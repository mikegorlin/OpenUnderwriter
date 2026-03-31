"""CourtListener federal case search client.

Searches the CourtListener free API (v4) for federal litigation involving
a company. Fills a gap not covered by Stanford SCAC (which only tracks
securities class actions): employment, regulatory, environmental, and
other federal cases.

Results are LOW confidence and supplementary -- they require cross-validation
from other sources before being treated as confirmed findings.

Per CLAUDE.md: all data acquisition must live in stages/acquire/.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence

logger = logging.getLogger(__name__)

# CourtListener REST API v4 base URL.
CL_API_BASE = "https://www.courtlistener.com/api/rest/v4"

# Cache TTL: 7 days (matches litigation_client).
CL_CACHE_TTL = 7 * 24 * 3600

# Litigation lookback: 10 years (matches litigation_client).
CL_LOOKBACK_YEARS = 10

# Request timeout in seconds.
CL_REQUEST_TIMEOUT = 10.0

# Maximum results to return per search.
CL_MAX_RESULTS = 30

# Suit nature keyword -> litigation type mapping for classification.
_SUIT_NATURE_MAP: dict[str, str] = {
    "employment": "employment",
    "labor": "employment",
    "wage": "employment",
    "discrimination": "employment",
    "wrongful termination": "employment",
    "environmental": "environmental",
    "epa": "environmental",
    "pollution": "environmental",
    "securities": "securities",
    "fraud": "securities",
    "sec": "securities",
    "regulatory": "regulatory",
    "antitrust": "regulatory",
    "ftc": "regulatory",
    "patent": "intellectual_property",
    "trademark": "intellectual_property",
    "copyright": "intellectual_property",
    "product liability": "product_liability",
    "personal injury": "product_liability",
    "contract": "contract",
    "breach": "contract",
}


class CourtListenerClient:
    """Federal case search via CourtListener free API.

    No API key required for basic search (free tier).
    Results are supplementary to Stanford SCAC and existing litigation client.
    """

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "courtlistener"

    def search_cases(
        self,
        company_name: str,
        ticker: str,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Search CourtListener for federal cases involving the company.

        Args:
            company_name: Legal name of the company.
            ticker: Stock ticker symbol (used for cache key).
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with 'cases' list, each containing case_name, date_filed,
            court, docket_number, litigation_type, source, confidence.
            Returns empty dict on any failure (graceful degradation).
        """
        cache_key = f"courtlistener:{ticker}"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for CourtListener: %s", cache_key)
                return dict(cached)

        logger.info(
            "Searching CourtListener for federal cases: %s (%s)",
            company_name,
            ticker,
        )

        try:
            raw_results = _fetch_cases(company_name)
        except Exception as exc:
            logger.warning(
                "CourtListener search failed (graceful degradation): %s", exc
            )
            return {}

        if not raw_results:
            return {"cases": [], "source": "CourtListener", "query": company_name}

        # Parse into structured results.
        cases = _parse_results(raw_results)

        result: dict[str, Any] = {
            "cases": cases,
            "source": "CourtListener",
            "query": company_name,
        }

        # Cache results.
        if cache is not None:
            cache.set(
                cache_key,
                result,
                source="courtlistener",
                ttl=CL_CACHE_TTL,
            )

        logger.info(
            "CourtListener returned %d cases for %s",
            len(cases),
            ticker,
        )
        return result


def _fetch_cases(company_name: str) -> list[dict[str, Any]]:
    """Fetch cases from CourtListener REST API v4.

    Uses the docket search endpoint with company name query.
    Filters to cases filed within the lookback period.

    Returns:
        List of raw case dicts from API response.
    """
    cutoff = datetime.now(tz=UTC) - timedelta(days=CL_LOOKBACK_YEARS * 365)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    url = f"{CL_API_BASE}/search/"
    params: dict[str, str] = {
        "q": f'"{company_name}"',
        "type": "r",  # RECAP dockets
        "filed_after": cutoff_str,
        "order_by": "dateFiled desc",
        "page_size": str(CL_MAX_RESULTS),
    }

    with httpx.Client(timeout=CL_REQUEST_TIMEOUT) as client:
        response = client.get(
            url,
            params=params,
            headers={"User-Agent": "do-uw/1.0 (D&O underwriting research)"},
        )
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])
    if isinstance(results, list):
        return results
    return []


def _parse_results(raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse CourtListener API results into structured case records.

    Each record includes source='CourtListener' and confidence=LOW
    per data integrity requirements.
    """
    cases: list[dict[str, Any]] = []

    for raw in raw_results:
        case_name = raw.get("caseName", raw.get("case_name", ""))
        date_filed = raw.get("dateFiled", raw.get("date_filed", ""))
        court = raw.get("court", "")
        docket_number = raw.get("docketNumber", raw.get("docket_number", ""))
        suit_nature = raw.get("suitNature", raw.get("suit_nature", ""))

        # Classify litigation type from suit nature.
        litigation_type = _classify_litigation_type(suit_nature, case_name)

        cases.append({
            "case_name": case_name,
            "date_filed": date_filed,
            "court": court,
            "docket_number": docket_number,
            "litigation_type": litigation_type,
            "suit_nature_raw": suit_nature,
            "source": "CourtListener",
            "confidence": Confidence.LOW,
        })

    return cases


def _classify_litigation_type(suit_nature: str, case_name: str) -> str:
    """Attempt to classify the litigation type from suit nature and case name.

    Uses keyword matching against known litigation categories.
    Returns 'other' if no match found.
    """
    combined = f"{suit_nature} {case_name}".lower()

    for keyword, lit_type in _SUIT_NATURE_MAP.items():
        if keyword in combined:
            return lit_type

    return "other"
