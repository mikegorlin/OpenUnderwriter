"""SEC EDGAR company identity resolution.

Given a CIK, fetches full company identity from SEC submissions API
and maps SIC codes to sector codes for downstream scoring.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any, cast

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity
from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)

# SEC submissions endpoint. CIK must be zero-padded to 10 digits.
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"

# Cache TTL: 30 days in seconds.
_IDENTITY_CACHE_TTL = 30 * 24 * 60 * 60

# Source citation for all SEC-sourced fields.
_SEC_SOURCE = "SEC EDGAR submissions"


def _pad_cik(cik: int) -> str:
    """Zero-pad CIK to 10 digits as required by SEC APIs."""
    return str(cik).zfill(10)


def _sourced(value: str, source: str = _SEC_SOURCE) -> SourcedValue[str]:
    """Wrap a string value as HIGH-confidence SourcedValue from SEC."""
    return SourcedValue[str](
        value=value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


# SIC code to sector code mapping.
# 4-digit map checked first for ambiguous 2-digit ranges (e.g. SIC 28xx),
# then 2-digit division ranges as fallback.
_SIC_4DIGIT_SECTOR_MAP: dict[tuple[int, int], str] = {
    # SIC 28xx: Industrial chemicals vs pharma vs specialty chemicals
    (2800, 2829): "INDU",  # Industrial chemicals, plastics, paints/coatings
    (2830, 2836): "HLTH",  # Pharma, biologicals, diagnostics
    (2840, 2844): "CONS",  # Soap, cleaners, toiletries -> Consumer
    (2850, 2899): "INDU",  # Specialty chemicals, coatings, adhesives
    # SIC 35xx: Not all are tech
    (3500, 3549): "INDU",  # Metalworking, special industry machinery
    (3550, 3559): "INDU",  # Industrial machinery
    (3560, 3569): "INDU",  # General industrial machinery
    (3570, 3579): "TECH",  # Computer & office equipment
    (3580, 3589): "INDU",  # Refrigeration, service industry machinery
    (3590, 3599): "INDU",  # Misc industrial machinery
    # SIC 36xx: Not all are tech
    (3600, 3612): "INDU",  # Electrical distribution equipment
    (3613, 3629): "INDU",  # Electrical industrial apparatus
    (3630, 3639): "CONS",  # Household appliances
    (3640, 3649): "INDU",  # Lighting equipment
    (3650, 3659): "CONS",  # Audio/video equipment -> Consumer electronics
    (3660, 3679): "TECH",  # Communications equipment, semiconductors
    (3690, 3699): "INDU",  # Misc electrical equipment
}

_SIC_2DIGIT_SECTOR_MAP: dict[tuple[int, int], str] = {
    # Mining (10-14) -> Energy
    (10, 14): "ENGY",
    # Construction (15-17) -> Industrials
    (15, 17): "INDU",
    # Manufacturing: varies by sub-range
    (20, 27): "INDU",  # Food, tobacco, textiles, lumber, furniture, paper
    # 28 handled by 4-digit map above; fallback to INDU for unmapped codes
    (28, 28): "INDU",
    (29, 29): "ENGY",  # Petroleum refining -> Energy
    (30, 34): "INDU",  # Rubber, stone, metals, fabricated metals
    (35, 36): "TECH",  # Fallback for unmapped 35xx/36xx -> Tech
    (37, 37): "CONS",  # Motor vehicles / auto -> Consumer Discretionary
    (38, 39): "INDU",  # Instruments, misc manufacturing
    # Transportation (40-47) -> Industrials
    (40, 47): "INDU",
    # Utilities (48-49)
    (48, 49): "UTIL",
    # Wholesale trade (50-51) -> Consumer
    (50, 51): "CONS",
    # Retail trade (52-59) -> Consumer
    (52, 59): "CONS",
    # Finance/Insurance (60-64) -> Financials
    (60, 64): "FINS",
    # Real Estate (65-67) -> REIT
    (65, 67): "REIT",
    # Services: varies by sub-range
    (70, 72): "CONS",   # Hotels, personal services
    (73, 73): "TECH",   # Computer/data services -> Tech
    (74, 76): "INDU",   # Management, engineering, R&D services
    (78, 79): "COMM",   # Motion picture, amusement/recreation
    (80, 80): "HLTH",   # Health services -> Healthcare
    (81, 86): "INDU",   # Legal, educational, social services
    (87, 87): "TECH",   # Engineering/R&D/management services -> Tech
    (88, 89): "INDU",   # Misc services
}


def sic_to_sector(sic_code: str) -> str:
    """Map a SIC code to a sector code.

    Checks 4-digit SIC first for ambiguous ranges (e.g. 28xx chemicals
    vs pharma), then falls back to 2-digit division mapping.
    Returns 'DEFAULT' if no mapping found.
    """
    try:
        sic_full = int(sic_code[:4].ljust(4, "0"))
    except (ValueError, IndexError):
        return "DEFAULT"

    # Try 4-digit map first (more specific)
    for (low, high), sector in _SIC_4DIGIT_SECTOR_MAP.items():
        if low <= sic_full <= high:
            return sector

    # Fall back to 2-digit division
    sic_2 = sic_full // 100
    for (low, high), sector in _SIC_2DIGIT_SECTOR_MAP.items():
        if low <= sic_2 <= high:
            return sector

    return "DEFAULT"


def _detect_fpi(submissions: dict[str, Any]) -> bool:
    """Detect if company is a foreign private issuer.

    Checks entityType field and filing history for 20-F filings.
    """
    entity_type = str(submissions.get("entityType", ""))
    if "foreign-private-issuer" in entity_type.lower():
        return True

    # Check recent filings for 20-F (FPI annual report).
    filings = submissions.get("filings", {})
    recent = filings.get("recent", {})
    forms = recent.get("form", [])
    if isinstance(forms, list) and "20-F" in forms:
        return True

    return False


def _format_fiscal_year_end(fye_raw: str) -> str:
    """Convert SEC fiscal year end format (MMDD) to MM-DD."""
    if len(fye_raw) == 4:
        return f"{fye_raw[:2]}-{fye_raw[2:]}"
    return fye_raw


def resolve_company_identity(
    cik: int,
    ticker: str,
    cache: AnalysisCache | None = None,
) -> CompanyIdentity:
    """Resolve a CIK to full company identity via SEC submissions API.

    Primary path: SEC EDGAR REST API (direct httpx).
    EdgarTools MCP integration deferred to when MCP invocation pattern
    is established.

    Args:
        cik: SEC Central Index Key.
        ticker: Stock ticker symbol (for result and cache key).
        cache: Optional cache for SEC data.

    Returns:
        CompanyIdentity with all available fields wrapped in SourcedValue.

    Raises:
        httpx.HTTPStatusError: If SEC API returns an error.
    """
    today = date.today().isoformat()
    cache_key = f"sec:{ticker.upper()}:identity:{today}"

    # Check cache first.
    submissions: dict[str, Any] | None = None
    if cache is not None:
        cached = cache.get(cache_key)
        if cached is not None:
            submissions = cached
            logger.debug("Cache hit for %s identity", ticker)

    # Fetch from SEC if not cached.
    if submissions is None:
        padded = _pad_cik(cik)
        url = _SUBMISSIONS_URL.format(cik_padded=padded)
        submissions = sec_get(url)
        if cache is not None:
            cache.set(
                cache_key,
                submissions,
                source=_SEC_SOURCE,
                ttl=_IDENTITY_CACHE_TTL,
            )

    return _parse_submissions(submissions, cik, ticker)


def _parse_submissions(
    data: dict[str, Any],
    cik: int,
    ticker: str,
) -> CompanyIdentity:
    """Parse SEC submissions JSON into CompanyIdentity."""
    name = str(data.get("name", ""))
    sic = str(data.get("sic", ""))
    sic_desc = str(data.get("sicDescription", ""))
    state = str(data.get("stateOfIncorporation", ""))
    fye = str(data.get("fiscalYearEnd", ""))
    entity_type_raw = str(data.get("entityType", ""))

    # Tickers and exchanges from submissions.
    raw_tickers = data.get("tickers", [])
    tickers_list: list[str] = (
        [str(t) for t in cast(list[Any], raw_tickers)]
        if isinstance(raw_tickers, list)
        else []
    )
    raw_exchanges = data.get("exchanges", [])
    exchanges_list: list[str] = (
        [str(e) for e in cast(list[Any], raw_exchanges)]
        if isinstance(raw_exchanges, list)
        else []
    )
    primary_exchange = exchanges_list[0] if exchanges_list else ""

    # Build all_tickers set, including our ticker if not already present.
    ticker_set: set[str] = {t.upper() for t in tickers_list}
    ticker_set.add(ticker.upper())
    all_tickers = sorted(ticker_set)

    # Map SIC to sector.
    sector = sic_to_sector(sic) if sic else "DEFAULT"

    # Detect FPI.
    is_fpi = _detect_fpi(data)

    # Format fiscal year end.
    formatted_fye = _format_fiscal_year_end(fye) if fye else ""

    identity = CompanyIdentity(
        ticker=ticker.upper(),
        legal_name=_sourced(name) if name else None,
        cik=_sourced(str(cik)),
        sic_code=_sourced(sic) if sic else None,
        sic_description=_sourced(sic_desc) if sic_desc else None,
        exchange=_sourced(primary_exchange) if primary_exchange else None,
        sector=_sourced(sector),
        state_of_incorporation=_sourced(state) if state else None,
        fiscal_year_end=_sourced(formatted_fye) if formatted_fye else None,
        entity_type=_sourced(entity_type_raw) if entity_type_raw else None,
        is_fpi=is_fpi,
        all_tickers=all_tickers,
    )

    logger.info(
        "Resolved CIK %d: %s (SIC=%s, sector=%s, FPI=%s)",
        cik,
        name,
        sic,
        sector,
        is_fpi,
    )
    return identity
