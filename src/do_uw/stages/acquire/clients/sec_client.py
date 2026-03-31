"""SEC EDGAR filing acquisition client.

Fetches filing METADATA (accession number, date, form type, URL) for
a given CIK. Also fetches Company Facts XBRL data for financial
extraction in Phase 3, and filing TEXT content (10-K sections,
Exhibit 21) needed by EXTRACT stage extractors.

Handles FPI (foreign private issuer) filing type mapping:
- Domestic 10-K -> FPI 20-F
- Domestic 10-Q -> FPI 6-K
- DEF 14A and Form 4 are attempted for both domestic and FPI.

Filing fetch helpers (_fetch_from_submissions, _fetch_from_efts,
_filing_cutoff_date) are in sec_client_filing.py (split for
500-line compliance).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence
from do_uw.models.state import AnalysisState
from do_uw.stages.acquire.clients.sec_client_filing import (
    _fetch_from_efts,
    _fetch_from_submissions,
)
from do_uw.stages.acquire.fallback import (
    DataAcquisitionError,
    FallbackChain,
    FallbackTier,
)
from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)

# Cache TTLs in seconds per filing type (from user decisions).
CACHE_TTLS: dict[str, int] = {
    "10-K": 14 * 30 * 24 * 3600,   # 14 months
    "10-K/A": 14 * 30 * 24 * 3600, # 14 months (restatement amendments)
    "20-F": 14 * 30 * 24 * 3600,   # 14 months
    "10-Q": 5 * 30 * 24 * 3600,    # 5 months
    "10-Q/A": 5 * 30 * 24 * 3600,  # 5 months (quarterly amendments)
    "6-K": 5 * 30 * 24 * 3600,     # 5 months
    "DEF 14A": 14 * 30 * 24 * 3600,  # 14 months
    "8-K": 30 * 24 * 3600,         # 30 days
    "4": 7 * 24 * 3600,            # 7 days (Form 4)
    "S-3": 14 * 30 * 24 * 3600,    # 14 months
    "S-1": 14 * 30 * 24 * 3600,    # 14 months
    "424B": 14 * 30 * 24 * 3600,   # 14 months
    "SC 13D": 30 * 24 * 3600,      # 30 days
    "SC 13G": 30 * 24 * 3600,      # 30 days
}

# Filing types by company type.
DOMESTIC_FILING_TYPES: list[str] = [
    "10-K", "10-K/A", "10-Q", "10-Q/A", "DEF 14A", "8-K", "4",
    "S-3", "S-1", "424B", "SC 13D", "SC 13G",
]
FPI_FILING_TYPES: list[str] = ["20-F", "6-K", "DEF 14A", "4"]

# SEC EDGAR base URLs.
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}"
SEC_COMPANY_FACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
)


class SECFilingClient:
    """SEC EDGAR filing metadata acquisition client.

    Fetches filing metadata (accession numbers, dates, form types, URLs)
    using a fallback chain: SEC Submissions API -> EFTS full-text search.
    """

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "sec_filings"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire SEC filing metadata for the resolved company.

        Args:
            state: Analysis state with resolved company identity.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict keyed by filing type, each containing a list of
            filing metadata dicts with: accession_number, filing_date,
            form_type, primary_doc_url, filing_url.
        """
        if state.company is None or state.company.identity.cik is None:
            msg = "Company CIK must be resolved before SEC filing acquisition"
            raise ValueError(msg)

        cik = state.company.identity.cik.value
        padded_cik = cik.zfill(10)
        is_fpi = _check_is_fpi(state)
        filing_types = FPI_FILING_TYPES if is_fpi else DOMESTIC_FILING_TYPES

        logger.info(
            "Acquiring SEC filings for CIK %s (FPI=%s), types=%s",
            cik,
            is_fpi,
            filing_types,
        )

        result: dict[str, Any] = {}
        for form_type in filing_types:
            cache_key = f"sec:{state.ticker}:{form_type}"
            ttl = CACHE_TTLS.get(form_type, 30 * 24 * 3600)

            # Check cache first.
            if cache is not None:
                cached = cache.get(cache_key)
                if cached is not None:
                    logger.debug("Cache hit for %s", cache_key)
                    result[form_type] = cached
                    continue

            # Build fallback chain for this filing type.
            chain = _build_filing_chain(
                form_type, padded_cik, cik, state.ticker
            )

            try:
                filings, _confidence, tier_name = chain.execute()
                logger.info(
                    "Retrieved %d %s filings via %s",
                    len(filings.get("filings", [])),
                    form_type,
                    tier_name,
                )
                result[form_type] = filings.get("filings", [])

                # Cache the result.
                if cache is not None:
                    cache.set(
                        cache_key,
                        result[form_type],
                        source=f"sec_edgar:{tier_name}",
                        ttl=ttl,
                    )

            except DataAcquisitionError:
                logger.info(
                    "No %s filings found within lookback period",
                    form_type,
                )
                result[form_type] = []

        # Acquire Company Facts XBRL data (Phase 3 expansion).
        company_facts = self.acquire_company_facts(padded_cik, cache)
        if company_facts is not None:
            result["company_facts"] = company_facts

        # Fetch filing text content for EXTRACT stage (10-K sections,
        # Exhibit 21). Uses URLs from the metadata acquired above.
        # KEPT for backward compatibility with Phase 3 extractors.
        from do_uw.stages.acquire.clients.filing_text import (
            fetch_filing_content,
        )

        cik_raw = cik.lstrip("0") or "0"
        filing_texts, exhibit_21 = fetch_filing_content(
            result, cik_raw, cache
        )
        if filing_texts:
            result["filing_texts"] = filing_texts
        if exhibit_21:
            result["exhibit_21"] = exhibit_21

        # Phase 4: Fetch full documents for ALL filing types.
        # Each document is fetched once and cached by accession number.
        # EXTRACT stage parses sections from these full documents.
        from do_uw.stages.acquire.clients.filing_fetcher import (
            fetch_all_filing_documents,
        )

        filing_documents = fetch_all_filing_documents(
            result, cik_raw, cache
        )
        if filing_documents:
            result["filing_documents"] = filing_documents

        return result

    def acquire_company_facts(
        self,
        cik: str,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any] | None:
        """Fetch all XBRL facts for a company via Company Facts API.

        One API call returns ALL XBRL facts across all filings for
        the company. This is the primary data source for financial
        extraction in Phase 3.

        Args:
            cik: 10-digit zero-padded CIK.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Full Company Facts API response dict, or None if the
            company has no XBRL data (404).
        """
        cache_key = f"sec:company_facts:{cik}"
        # Cache for 14 months (same as 10-K).
        ttl = 14 * 30 * 24 * 3600

        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for company facts CIK %s", cik)
                cached_result: dict[str, Any] = cached
                return cached_result

        url = SEC_COMPANY_FACTS_URL.format(cik=cik)
        logger.info("Acquiring Company Facts XBRL data for CIK %s", cik)

        try:
            data = sec_get(url)
        except Exception:
            logger.warning(
                "Failed to acquire Company Facts for CIK %s "
                "(company may have no XBRL data)",
                cik,
            )
            return None

        if cache is not None:
            cache.set(
                cache_key,
                data,
                source="sec_edgar:company_facts_api",
                ttl=ttl,
            )

        logger.info(
            "Acquired Company Facts for CIK %s: %d taxonomies",
            cik,
            len(data.get("facts", {})),
        )
        return data


def _make_submissions_fn(
    padded_cik: str, form_type: str
) -> Callable[..., dict[str, Any] | None]:
    """Create a closure for submissions API tier."""
    def _fn(**_kwargs: Any) -> dict[str, Any] | None:
        return _fetch_from_submissions(padded_cik, form_type)
    return _fn


def _make_efts_fn(
    ticker: str, form_type: str, cik: str
) -> Callable[..., dict[str, Any] | None]:
    """Create a closure for EFTS search tier."""
    def _fn(**_kwargs: Any) -> dict[str, Any] | None:
        return _fetch_from_efts(ticker, form_type, cik)
    return _fn


def _build_filing_chain(
    form_type: str,
    padded_cik: str,
    cik: str,
    ticker: str,
) -> FallbackChain:
    """Build a fallback chain for a specific filing type."""
    return FallbackChain(
        source_name=f"sec:{form_type}",
        tiers=[
            FallbackTier(
                name="submissions_api",
                confidence=Confidence.HIGH,
                acquire_fn=_make_submissions_fn(padded_cik, form_type),
            ),
            FallbackTier(
                name="efts_search",
                confidence=Confidence.MEDIUM,
                acquire_fn=_make_efts_fn(ticker, form_type, cik),
            ),
        ],
    )


def _check_is_fpi(state: AnalysisState) -> bool:
    """Determine if company is a foreign private issuer.

    Checks for an is_fpi attribute on the identity. If not present,
    defaults to False (domestic).
    """
    if state.company is None:
        return False
    identity = state.company.identity
    # is_fpi may be added to CompanyIdentity in Phase 2 resolve stage.
    return bool(getattr(identity, "is_fpi", False))


