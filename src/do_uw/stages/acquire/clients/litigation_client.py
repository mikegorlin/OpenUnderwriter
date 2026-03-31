"""Litigation data acquisition client.

Per user decision: web search fires FIRST for broad discovery, then
SEC filing references for structured data. This inverts the typical
structured-first approach because web search casts a wider net for
lawsuits, enforcement actions, and settlements that may not appear
in SEC filings.

Litigation lookback: 10 years per user decision.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence
from do_uw.models.state import AnalysisState
from do_uw.stages.acquire.clients.web_search import WebSearchClient
from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)

# Cache TTL: 7 days (litigation data changes frequently).
LITIGATION_TTL = 7 * 24 * 3600

# Litigation lookback: 10 years.
LITIGATION_LOOKBACK_YEARS = 10

# Web search query templates for litigation discovery.
# Covers active + historical (settled/dismissed) cases with specific queries
# for outcome data that underwriters need.
LITIGATION_SEARCH_TEMPLATES: list[str] = [
    '"{company}" securities class action',
    '"{company}" securities class action settlement amount',
    '"{company}" securities class action dismissed outcome',
    '"{company}" SEC investigation enforcement action',
    '"{company}" derivative lawsuit shareholder',
    '"{company}" securities litigation history settlements',
    '"{company}" ERISA class action',
    '"{company}" securities fraud allegations class period',
]

# EFTS search URL for SEC filing legal proceedings.
SEC_EFTS_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q={query}&forms={forms}&dateRange=custom"
    "&startdt={start}&enddt={end}"
)


class LitigationClient:
    """Litigation data acquisition client.

    Leads with web search for broad discovery, then collects SEC
    filing references for legal proceedings disclosures.
    """

    def __init__(
        self,
        web_search: WebSearchClient | None = None,
    ) -> None:
        """Initialize with optional web search client.

        Args:
            web_search: WebSearchClient instance for web queries.
                Defaults to a new instance with default (no-op) search.
        """
        self._web_search = web_search or WebSearchClient()

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "litigation"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire litigation data via web search + SEC references.

        Per user decision: web search fires FIRST.

        Args:
            state: Analysis state with resolved company identity.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with: web_results, sec_references, search_terms_used.
        """
        company_name = _get_company_name(state)
        cache_key = f"litigation:{state.ticker}"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for litigation: %s", cache_key)
                return dict(cached)

        logger.info(
            "Acquiring litigation data for %s (%s)",
            state.ticker,
            company_name,
        )

        # Step 1: Web search (fires FIRST per user decision).
        web_results, search_terms = _run_web_searches(
            self._web_search, company_name, cache
        )

        # Step 2: SEC filing references for legal proceedings.
        sec_references = _fetch_sec_litigation_refs(
            state.ticker, company_name
        )

        # Step 3: Supabase claims database (supplementary).
        supabase_cases: list[dict[str, Any]] = []
        try:
            from do_uw.stages.acquire.clients.supabase_litigation import (
                query_sca_filings,
            )
            supabase_cases = query_sca_filings(state.ticker, company_name)
        except Exception:
            logger.debug("Supabase SCA lookup unavailable", exc_info=True)

        # Step 4: Supabase risk card (scenario benchmarks, screening questions,
        # repeat filer detail, company risk profile).
        risk_card: dict[str, Any] = {}
        try:
            from do_uw.stages.acquire.clients.supabase_litigation import (
                query_risk_card,
            )
            risk_card = query_risk_card(state.ticker)
        except Exception:
            logger.debug("Supabase risk card unavailable", exc_info=True)

        # Tag sources and confidence.
        result: dict[str, Any] = {
            "web_results": [
                {**r, "source": "web_search", "confidence": Confidence.LOW}
                for r in web_results
            ],
            "sec_references": [
                {**r, "source": "sec_efts", "confidence": Confidence.HIGH}
                for r in sec_references
            ],
            "supabase_cases": [
                {**c, "source": "supabase_sca_filings", "confidence": Confidence.MEDIUM}
                for c in supabase_cases
            ],
            "risk_card": risk_card,
            "search_terms_used": search_terms,
        }

        # Cache results.
        if cache is not None:
            cache.set(
                cache_key,
                result,
                source="litigation_client",
                ttl=LITIGATION_TTL,
            )

        return result


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state, falling back to ticker."""
    if (
        state.company is not None
        and state.company.identity.legal_name is not None
    ):
        return state.company.identity.legal_name.value
    return state.ticker


def _run_web_searches(
    web_search: WebSearchClient,
    company_name: str,
    cache: AnalysisCache | None,
) -> tuple[list[dict[str, str]], list[str]]:
    """Run litigation-specific web searches.

    Returns:
        Tuple of (all_results, search_terms_used).
    """
    all_results: list[dict[str, str]] = []
    terms_used: list[str] = []

    for template in LITIGATION_SEARCH_TEMPLATES:
        query = template.replace("{company}", company_name)
        terms_used.append(query)
        results = web_search.search(query, cache=cache)
        all_results.extend(results)

    logger.info(
        "Litigation web search: %d results from %d queries",
        len(all_results),
        len(terms_used),
    )
    return all_results, terms_used


def _fetch_sec_litigation_refs(
    ticker: str,
    company_name: str,
) -> list[dict[str, str]]:
    """Search EFTS for SEC filing litigation references.

    Looks for Item 3 Legal Proceedings mentions in 10-K filings.
    """
    cutoff = datetime.now(tz=UTC) - timedelta(
        days=LITIGATION_LOOKBACK_YEARS * 365
    )
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

    url = SEC_EFTS_SEARCH_URL.format(
        query=f'"{company_name}" "legal proceedings"',
        forms="10-K,20-F",
        start=cutoff.strftime("%Y-%m-%d"),
        end=today,
    )

    try:
        data = sec_get(url)
    except Exception as exc:
        logger.warning("EFTS litigation search failed: %s", exc)
        return []

    hits = data.get("hits", {}).get("hits", [])
    references: list[dict[str, str]] = []

    for hit in hits[:20]:
        source = hit.get("_source", {})
        references.append({
            "filing_type": source.get("form_type", ""),
            "filing_date": source.get("file_date", ""),
            "file_url": source.get("file_url", ""),
            "company_name": source.get("display_names", [""])[0]
            if source.get("display_names")
            else "",
        })

    logger.info(
        "SEC litigation refs: %d filings found for %s",
        len(references),
        ticker,
    )
    return references
