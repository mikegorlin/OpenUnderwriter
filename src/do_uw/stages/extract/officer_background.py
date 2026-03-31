"""Officer background extraction with serial defendant detection.

Provides:
- extract_prior_companies_from_bio: Regex extraction of prior companies from DEF 14A bios
- date_ranges_overlap: Date range overlap check for officer tenure vs SCA class period
- query_officer_prior_sca: Batch Supabase query for SCA filings at officer prior companies
- detect_serial_defendants: Cross-reference officers against SCA database
- assess_suitability: Data completeness indicator (HIGH/MEDIUM/LOW)
- aggregate_per_insider: Per-insider transaction aggregation with 10b5-1 status

Phase 135 GOV-01, GOV-02, GOV-05.
"""

from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from datetime import date
from typing import Any

from do_uw.models.governance_intelligence import (
    OfficerBackground,
    OfficerSCAExposure,
    PerInsiderActivity,
    PriorCompany,
)
from do_uw.models.market_events import InsiderTransaction

logger = logging.getLogger(__name__)

# Transaction codes to exclude from per-insider sell aggregation
# A = award/grant, F = tax withhold on vesting, G = gift, W = estate
_COMPENSATION_CODES: set[str] = {"A", "F"}
_EXCLUDED_CODES: set[str] = {"G", "W"}

# ---------------------------------------------------------------------------
# GOV-01: Prior company extraction from bio text
# ---------------------------------------------------------------------------

# Patterns for "served as ROLE of/at COMPANY from YEAR to YEAR"
_SERVED_PATTERN = re.compile(
    r"served\s+as\s+"
    r"(?P<role>[A-Z][A-Za-z\s.&/,-]+?)\s+"
    r"(?:of|at)\s+"
    r"(?P<company>[A-Z][A-Za-z0-9\s.&,'-]+?)\s+"
    r"from\s+(?P<start>\d{4})\s+to\s+(?P<end>\d{4})",
    re.IGNORECASE,
)

# Pattern for "was ROLE at COMPANY (YEAR-YEAR)"
_WAS_PATTERN = re.compile(
    r"was\s+"
    r"(?P<role>[A-Z][A-Za-z\s.&/,-]+?)\s+"
    r"(?:of|at)\s+"
    r"(?P<company>[A-Z][A-Za-z0-9\s.&,'-]+?)\s*"
    r"\((?P<start>\d{4})\s*[-\u2013]\s*(?P<end>\d{4})\)",
    re.IGNORECASE,
)


def extract_prior_companies_from_bio(bio_text: str) -> list[PriorCompany]:
    """Extract prior company names, roles, and dates from officer bio text.

    Uses regex pattern matching for common bio formats found in DEF 14A
    filings. For complex bios, future versions may use LLM extraction.

    Args:
        bio_text: Full biographical text from proxy statement.

    Returns:
        List of PriorCompany records. Empty list if no patterns match.
    """
    if not bio_text or len(bio_text.strip()) < 10:
        return []

    results: list[PriorCompany] = []
    seen: set[tuple[str, int | None, int | None]] = set()

    for pattern in (_SERVED_PATTERN, _WAS_PATTERN):
        for match in pattern.finditer(bio_text):
            role = match.group("role").strip().rstrip(",")
            company = match.group("company").strip().rstrip(",")
            start_year = int(match.group("start"))
            end_year = int(match.group("end"))

            # Deduplicate by (company, start, end)
            key = (company.lower(), start_year, end_year)
            if key in seen:
                continue
            seen.add(key)

            results.append(
                PriorCompany(
                    company_name=company,
                    role=role,
                    years=f"{start_year}-{end_year}",
                    start_year=start_year,
                    end_year=end_year,
                )
            )

    return results


# ---------------------------------------------------------------------------
# GOV-02: Date range overlap for serial defendant detection
# ---------------------------------------------------------------------------


def date_ranges_overlap(
    officer_start_year: int,
    officer_end_year: int,
    class_period_start: str,
    class_period_end: str,
) -> bool:
    """Check if officer tenure overlaps with SCA class period.

    Converts officer years to full date ranges (start_year-01-01 to
    end_year-12-31) per research recommendation. Parses class period
    dates as YYYY-MM-DD.

    Args:
        officer_start_year: Year officer started at company.
        officer_end_year: Year officer left company.
        class_period_start: SCA class period start (YYYY-MM-DD).
        class_period_end: SCA class period end (YYYY-MM-DD).

    Returns:
        True if any overlap exists. False if dates are invalid or empty.
    """
    if not class_period_start or not class_period_end:
        return False

    try:
        officer_start = date(officer_start_year, 1, 1)
        officer_end = date(officer_end_year, 12, 31)
        cp_start = date.fromisoformat(class_period_start[:10])
        cp_end = date.fromisoformat(class_period_end[:10])
    except (ValueError, TypeError):
        return False

    # Two ranges overlap if one starts before the other ends
    return officer_start <= cp_end and cp_start <= officer_end


# ---------------------------------------------------------------------------
# GOV-02: Supabase batch query for officer prior company SCAs
# ---------------------------------------------------------------------------

_SUPABASE_URL = "https://jfqenpobwadlhuvseiax.supabase.co"
_TABLE = "sca_filings"


def query_officer_prior_sca(
    company_names: list[str],
) -> list[dict[str, Any]]:
    """Batch query Supabase for SCA filings at officer prior companies.

    Uses company_name ilike matching (same pattern as query_sca_filings).
    Splits into batches of 20 to avoid URL length limits.

    Args:
        company_names: List of prior company names from officer bios.

    Returns:
        Raw Supabase results with class_period_start/end for date overlap.
        Empty list if no API key, no names, or query fails.
    """
    if not company_names:
        return []

    api_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not api_key:
        logger.debug("No SUPABASE_KEY -- skipping officer prior SCA lookup")
        return []

    try:
        import httpx
    except ImportError:
        logger.debug("httpx not available -- skipping officer prior SCA query")
        return []

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Deduplicate and clean company names
    unique_names: list[str] = []
    seen_lower: set[str] = set()
    for name in company_names:
        clean = name.replace("'", "''").split(",")[0].split(" Inc")[0].strip()
        if clean and len(clean) > 3 and clean.lower() not in seen_lower:
            unique_names.append(clean)
            seen_lower.add(clean.lower())

    all_results: list[dict[str, Any]] = []
    select_fields = (
        "company_name,ticker,filing_date,case_status,"
        "settlement_amount_m,class_period_start,class_period_end,"
        "case_summary,docket_number"
    )

    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(unique_names), batch_size):
        batch = unique_names[i : i + batch_size]

        # Build OR filter: or=(company_name.ilike.*Name1*,company_name.ilike.*Name2*)
        or_clauses = ",".join(
            f"company_name.ilike.*{name}*" for name in batch
        )
        url = (
            f"{_SUPABASE_URL}/rest/v1/{_TABLE}"
            f"?or=({or_clauses})"
            f"&select={select_fields}"
            f"&order=filing_date.desc"
            f"&limit=50"
        )

        try:
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    all_results.extend(data)
            else:
                logger.warning(
                    "Supabase officer SCA query returned %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
        except Exception:
            logger.warning("Supabase officer prior SCA query failed", exc_info=True)

    return all_results


# ---------------------------------------------------------------------------
# GOV-02: Serial defendant detection
# ---------------------------------------------------------------------------


def _company_name_matches(prior_name: str, sca_name: str) -> bool:
    """Fuzzy match officer's prior company name against SCA company name.

    Uses case-insensitive substring matching to handle variations like
    "Acme Corp" vs "Acme Corporation" or "ACME, Inc."
    """
    prior_lower = prior_name.lower().strip()
    sca_lower = sca_name.lower().strip()

    # Direct substring match
    if prior_lower in sca_lower or sca_lower in prior_lower:
        return True

    # Extract core name (first 2+ words before Inc/Corp/Ltd etc.)
    stop_words = {"inc", "corp", "corporation", "ltd", "llc", "co", "company", "group", "holdings"}
    prior_words = [w for w in re.split(r"[\s,.]+", prior_lower) if w and w not in stop_words]
    sca_words = [w for w in re.split(r"[\s,.]+", sca_lower) if w and w not in stop_words]

    if prior_words and sca_words:
        # Check if core words match
        prior_core = " ".join(prior_words[:3])
        sca_core = " ".join(sca_words[:3])
        if prior_core == sca_core or prior_core in sca_core or sca_core in prior_core:
            return True

    return False


def detect_serial_defendants(
    officers: list[OfficerBackground],
    sca_results: list[dict[str, Any]],
) -> list[OfficerBackground]:
    """Cross-reference officers against SCA results for serial defendant detection.

    For each officer's prior_companies, checks if any SCA result matches
    the company name AND the date range overlaps with officer tenure.

    Args:
        officers: List of OfficerBackground with prior_companies populated.
        sca_results: Raw Supabase SCA filing results.

    Returns:
        Updated officers with is_serial_defendant and sca_exposures populated.
    """
    if not officers:
        return []

    for officer in officers:
        exposures: list[OfficerSCAExposure] = []

        for pc in officer.prior_companies:
            if pc.start_year is None or pc.end_year is None:
                continue

            for sca in sca_results:
                sca_company = sca.get("company_name", "")
                if not sca_company:
                    continue

                if not _company_name_matches(pc.company_name, sca_company):
                    continue

                cp_start = sca.get("class_period_start", "")
                cp_end = sca.get("class_period_end", "")

                if date_ranges_overlap(pc.start_year, pc.end_year, cp_start, cp_end):
                    exposures.append(
                        OfficerSCAExposure(
                            company_name=sca_company,
                            case_caption=sca.get("case_summary", "") or sca.get("docket_number", ""),
                            filing_date=sca.get("filing_date", ""),
                            class_period_start=cp_start,
                            class_period_end=cp_end,
                            officer_role_at_time=pc.role,
                            settlement_amount_m=sca.get("settlement_amount_m"),
                        )
                    )

        if exposures:
            officer.is_serial_defendant = True
            officer.sca_exposures = exposures

    return officers


# ---------------------------------------------------------------------------
# GOV-01: Suitability assessment (data completeness indicator)
# ---------------------------------------------------------------------------


def assess_suitability(
    officer: OfficerBackground,
    has_full_bio: bool,
    has_litigation_search: bool,
) -> tuple[str, str]:
    """Assess data completeness for an officer background investigation.

    This is a DATA COMPLETENESS indicator, not a judgment on the person.
    HIGH = full bio + litigation search done + cross-validated.
    MEDIUM = partial data (bio but no litigation search, or vice versa).
    LOW = minimal bio, no cross-validation.

    Args:
        officer: OfficerBackground record.
        has_full_bio: Whether a full biographical text was available.
        has_litigation_search: Whether litigation search was performed.

    Returns:
        Tuple of (level, reason) where level is HIGH/MEDIUM/LOW.
    """
    if has_full_bio and has_litigation_search:
        return (
            "HIGH",
            "Full bio available and litigation search completed",
        )
    elif has_full_bio or has_litigation_search:
        parts: list[str] = []
        if has_full_bio:
            parts.append("bio available")
        else:
            parts.append("limited bio")
        if has_litigation_search:
            parts.append("litigation search done")
        else:
            parts.append("no litigation search")
        return ("MEDIUM", "; ".join(parts))
    else:
        return ("LOW", "Minimal bio, no cross-validation performed")


# ---------------------------------------------------------------------------
# GOV-05: Per-insider activity aggregation
# ---------------------------------------------------------------------------


def aggregate_per_insider(
    transactions: list[InsiderTransaction],
    shares_outstanding: float | None = None,
) -> list[PerInsiderActivity]:
    """Aggregate insider transactions by insider name for GOV-05 display.

    Groups SELL transactions by insider_name, sums total_value, counts
    transactions, detects 10b5-1 status, finds date range. Excludes
    compensation codes (A=award, F=tax withhold) and gift/estate (G, W).
    Only includes insiders with SELL transactions.

    Args:
        transactions: List of InsiderTransaction records from Form 4 extraction.
        shares_outstanding: Total shares outstanding for %O/S calculation.

    Returns:
        List of PerInsiderActivity sorted by total_sold_usd descending.
    """
    if not transactions:
        return []

    # Group sell transactions by insider name
    by_insider: dict[str, list[InsiderTransaction]] = defaultdict(list)

    for tx in transactions:
        if not tx.insider_name or not tx.insider_name.value:
            continue

        code = tx.transaction_code
        if code in _COMPENSATION_CODES or code in _EXCLUDED_CODES:
            continue

        if tx.transaction_type != "SELL":
            continue

        by_insider[tx.insider_name.value].append(tx)

    results: list[PerInsiderActivity] = []

    for name, sells in by_insider.items():
        if not sells:
            continue

        total_sold = 0.0
        total_shares = 0.0
        has_10b5_1 = False
        dates: list[str] = []
        position = ""

        for tx in sells:
            if tx.total_value and tx.total_value.value:
                total_sold += float(tx.total_value.value)
            if tx.shares and tx.shares.value:
                total_shares += float(tx.shares.value)
            if tx.is_10b5_1 and tx.is_10b5_1.value is True:
                has_10b5_1 = True
            if tx.transaction_date and tx.transaction_date.value:
                dates.append(tx.transaction_date.value)
            if not position and tx.title and tx.title.value:
                position = tx.title.value

        # Calculate %O/S if shares outstanding available
        pct_os: float | None = None
        if shares_outstanding and shares_outstanding > 0 and total_shares > 0:
            pct_os = (total_shares / shares_outstanding) * 100.0

        sorted_dates = sorted(dates) if dates else []

        results.append(
            PerInsiderActivity(
                name=name,
                position=position,
                total_sold_usd=total_sold,
                total_sold_pct_os=pct_os,
                tx_count=len(sells),
                has_10b5_1=has_10b5_1,
                activity_period_start=sorted_dates[0] if sorted_dates else "",
                activity_period_end=sorted_dates[-1] if sorted_dates else "",
            )
        )

    # Sort by total sold descending
    results.sort(key=lambda x: x.total_sold_usd, reverse=True)
    return results
