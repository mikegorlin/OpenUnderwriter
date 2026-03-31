"""Acquisition orchestrator coordinating clients, gates, fallbacks, and caching.

Orchestrates the full ACQUIRE stage flow:
  Phase A: Pre-acquisition blind spot sweep (~20% budget)
  Phase B: Structured data acquisition (SEC, market, litigation, news)
  Phase C: Post-acquisition blind spot sweep (remaining budget)
  Phase D: Gate checking with retry on HARD failure

Per CLAUDE.md: MCP tools are NOT available inside Python pipeline code.
WebSearchClient uses a pluggable search_fn (no-op by default).
"""

from __future__ import annotations

import base64
import concurrent.futures
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlparse

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.knowledge.requirements import AcquisitionManifest
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.acquire.brain_requirements import (
    log_section_requirements,
    validate_acquisition_coverage,
)
from do_uw.stages.acquire.clients.courtlistener_client import CourtListenerClient
from do_uw.stages.acquire.clients.litigation_client import LitigationClient
from do_uw.stages.acquire.clients.market_client import MarketDataClient
from do_uw.stages.acquire.clients.news_client import NewsClient
from do_uw.stages.acquire.clients.patent_client import fetch_ai_patents
from do_uw.stages.acquire.clients.sec_client import SECFilingClient
from do_uw.stages.acquire.clients.web_search import WebSearchClient
from do_uw.stages.acquire.fallback import DataAcquisitionError
from do_uw.stages.acquire.inventory import AcquisitionInventory, check_inventory
from do_uw.stages.acquire.gates import (
    GateType,
    check_gates,
)

logger = logging.getLogger(__name__)

# Budget allocation for blind spot sweep phases.
PRE_SWEEP_BUDGET_FRACTION = 0.20  # 20% of total for pre-acquisition sweep.

# Retry delay for HARD gate failures (seconds).
GATE_RETRY_DELAY_SECONDS = 2


class AcquisitionOrchestrator:
    """Coordinates all data acquisition clients in the correct order.

    Flow: blind spot pre -> structured -> blind spot post -> gates.
    """

    def __init__(
        self,
        cache: AnalysisCache | None = None,
        search_budget: int = 50,
        search_fn: Callable[[str], list[dict[str, str]]] | None = None,
        brain_manifest: AcquisitionManifest | None = None,
    ) -> None:
        """Initialize orchestrator with cache and search configuration.

        Args:
            cache: Optional analysis cache for storing/retrieving results.
            search_budget: Maximum web searches per analysis run.
            search_fn: Optional search function to inject into
                WebSearchClient. Defaults to no-op.
            brain_manifest: Optional manifest of brain-derived acquisition
                requirements. If provided, orchestrator logs brain-driven
                requirements at start and validates coverage at end.
        """
        self._cache = cache
        self._search_budget = search_budget
        self._search_fn = search_fn
        self._brain_manifest = brain_manifest

        # Create the shared WebSearchClient.
        self._web_search = WebSearchClient(
            search_fn=search_fn,
            search_budget=search_budget,
        )

        # Create all data clients.
        self._sec_client = SECFilingClient()
        self._market_client = MarketDataClient()
        self._litigation_client = LitigationClient(
            web_search=self._web_search,
        )
        self._news_client = NewsClient(web_search=self._web_search)

        # Supplemental client (Phase B++++).
        self._courtlistener_client = CourtListenerClient()

    def run(self, state: AnalysisState) -> AcquiredData:
        """Orchestrate the full acquisition flow.

        Args:
            state: Analysis state with resolved company identity.

        Returns:
            Populated AcquiredData with all acquisition results.

        Raises:
            DataAcquisitionError: If a HARD gate fails after retry.
        """
        acquired = AcquiredData()
        company_name = _get_company_name(state)

        # Incremental acquisition: check what we already have.
        inv = check_inventory(state.acquired_data)
        _log_inventory(inv)

        # Copy existing data for sources that don't need re-fetching.
        if state.acquired_data is not None:
            _copy_complete_sources(inv, state.acquired_data, acquired)

        # Brain-driven requirements logging (before any acquisition).
        if self._brain_manifest:
            log_section_requirements(self._brain_manifest)
            logger.info(
                "Brain-driven acquisition: %d sources required by %d signals",
                len(self._brain_manifest.required_sources),
                self._brain_manifest.total_signals,
            )

        # Phase A: Pre-acquisition blind spot sweep.
        if inv.needs_blind_spot:
            logger.info("Phase A: Pre-acquisition blind spot sweep")
            pre_results = self._run_blind_spot_sweep(company_name, state.ticker)
            acquired.blind_spot_results["pre_structured"] = pre_results
        else:
            logger.info("SKIP Phase A: %s", inv.skip_reasons.get("blind_spot", "already acquired"))

        # Phase B: Structured data acquisition.
        if (
            inv.needs_sec_filings
            or inv.needs_market_data
            or inv.needs_litigation
            or inv.needs_news
        ):
            logger.info("Phase B: Structured data acquisition")
            self._acquire_structured_data(state, acquired, inv)
        else:
            logger.info("SKIP Phase B: all structured data already acquired")

        # Phase B (Frames): SEC Frames API cross-filer data (non-blocking).
        if inv.needs_frames:
            self._acquire_frames_data(state, acquired)
        else:
            logger.info(
                "SKIP Phase B (Frames): %s", inv.skip_reasons.get("frames", "already acquired")
            )

        # Phase B+: Non-blocking supplemental acquisitions.
        logger.info("Phase B+: SKIPPED — USPTO patent fetch disabled for performance")
        acquired.patent_data = []

        # Phase B++: Company logo acquisition (non-blocking).
        if inv.needs_logo:
            _fetch_company_logo(state, acquired)
        else:
            logger.info("SKIP Phase B++: %s", inv.skip_reasons.get("logo", "already acquired"))

        # Phase B+++: Volume spike event correlation (non-blocking).
        try:
            from do_uw.stages.acquire.spike_correlator import (
                correlate_volume_spikes,
            )
            from do_uw.stages.extract.volume_spikes import (
                detect_volume_spikes,
            )

            history_1y = acquired.market_data.get("history_1y", {})
            if history_1y and isinstance(history_1y, dict):
                spike_events = detect_volume_spikes(history_1y)
                if spike_events and self._web_search.is_search_configured:
                    company = _get_company_name(state)
                    correlate_volume_spikes(
                        spike_events=spike_events,
                        company_name=company,
                        ticker=state.ticker,
                        search_fn=lambda q: self._web_search.search(q, cache=None),
                    )
                    # Store correlated spikes for EXTRACT to pick up.
                    acquired.market_data["volume_spike_events"] = spike_events
                    logger.info(
                        "Phase B+++: Correlated %d volume spikes with catalysts",
                        len(spike_events),
                    )
        except Exception:
            logger.warning(
                "Phase B+++: Volume spike correlation failed (non-blocking)",
                exc_info=True,
            )

        # Phase B++++: CourtListener federal case search (non-blocking).
        if inv.needs_courtlistener:
            try:
                cl_results = self._courtlistener_client.search_cases(
                    company_name, state.ticker, cache=self._cache
                )
                if cl_results:
                    acquired.litigation_data["courtlistener"] = cl_results
                    logger.info(
                        "Phase B++++: CourtListener returned %d cases",
                        len(cl_results.get("cases", [])),
                    )
            except Exception:
                logger.warning(
                    "Phase B++++: CourtListener search failed (non-blocking)",
                    exc_info=True,
                )
        else:
            logger.info(
                "SKIP Phase B++++: %s", inv.skip_reasons.get("courtlistener", "already acquired")
            )

        # Phase C: Post-acquisition blind spot sweep.
        logger.info("Phase C: Post-acquisition blind spot sweep")
        post_results = self._run_blind_spot_sweep(company_name, state.ticker)
        acquired.blind_spot_results["post_structured"] = post_results

        # Phase D: Gate checking with retry on HARD failure.
        logger.info("Phase D: Gate checking")
        self._check_and_retry_gates(state, acquired)

        # Post-acquisition brain validation.
        if self._brain_manifest:
            acquired_sources = _determine_acquired_sources(acquired)
            coverage = validate_acquisition_coverage(self._brain_manifest, acquired_sources)
            acquired.acquisition_metadata["brain_coverage"] = coverage

        # Record search budget usage and configuration status.
        acquired.search_budget_used = self._web_search.searches_used
        acquired.blind_spot_results["search_configured"] = self._web_search.is_search_configured
        acquired.blind_spot_results["search_budget_used"] = self._web_search.searches_used

        # Automatic discovery — feed high-relevance blind spot results
        # through LLM ingestion for proposal generation.
        # Non-blocking: failures here never break the acquisition pipeline.
        # DISABLED for debugging web search hang
        # _run_discovery_hook(acquired.blind_spot_results, state.ticker)

        # Phase E: Brain-driven gap search
        # Non-blocking: failures here DO NOT break the acquisition pipeline.
        # DISABLED for debugging web search hang
        logger.info(
            "Phase E: Brain-driven gap search SKIPPED",
        )
        # try:
        #     from do_uw.stages.acquire.gap_searcher import run_gap_search
        #     run_gap_search(state, acquired, self._web_search, self._cache)
        # except Exception:
        #     logger.warning(
        #         "Phase E: Gap search failed (non-blocking)",
        #         exc_info=True,
        #     )

        return acquired

    def _run_blind_spot_sweep(
        self, company_name: str, ticker: str
    ) -> dict[str, list[dict[str, str]]]:
        """Run blind spot sweep if budget allows."""
        if self._web_search.budget_remaining <= 0:
            logger.info("No search budget remaining for blind spot sweep")
            return {}

        results = self._web_search.blind_spot_sweep(company_name, ticker, cache=None)

        total_hits = sum(len(v) for v in results.values())
        if total_hits > 0:
            logger.info(
                "Blind spot sweep found %d results across %d categories",
                total_hits,
                len(results),
            )
        elif self._search_fn is None:
            logger.info("Blind spot sweep returned empty results (no search function configured)")
        else:
            logger.info("Blind spot sweep returned no results")

        return results

    def _acquire_structured_data(
        self,
        state: AnalysisState,
        acquired: AcquiredData,
        inv: AcquisitionInventory | None = None,
    ) -> None:
        """Run structured data clients, skipping those already complete.

        Args:
            state: Analysis state with resolved company identity.
            acquired: AcquiredData to populate.
            inv: Optional inventory; if provided, skip complete sources.
        """
        clients_and_targets: list[tuple[str, Any, str, bool]] = [
            ("sec_filings", self._sec_client, "filings", inv.needs_sec_filings if inv else True),
            (
                "market_data",
                self._market_client,
                "market_data",
                inv.needs_market_data if inv else True,
            ),
            (
                "litigation",
                self._litigation_client,
                "litigation_data",
                inv.needs_litigation if inv else True,
            ),
            (
                "news_sentiment",
                self._news_client,
                "web_search_results",
                inv.needs_news if inv else True,
            ),
        ]

        for client_name, client, target_field, needed in clients_and_targets:
            if not needed:
                logger.info("SKIP %s: already acquired", client_name)
                continue
            self._run_client(client_name, client, target_field, state, acquired)

    def _acquire_frames_data(self, state: AnalysisState, acquired: AcquiredData) -> None:
        """Acquire SEC Frames cross-filer data and SIC mapping.

        Non-blocking: failures here do not break the pipeline. The
        pipeline works without Frames data (falls back to existing
        proxy benchmarking).

        SKIPPED for performance: we only need target company filings, not peer benchmarking data.
        """
        logger.info(
            "Phase B (Frames): SKIPPED — focusing on target company filings only (peer benchmarking disabled)"
        )
        # Store empty frames data to satisfy downstream consumers
        acquired.filings["frames"] = {}
        acquired.filings["sic_mapping"] = {}

    def _run_client(
        self,
        client_name: str,
        client: Any,
        target_field: str,
        state: AnalysisState,
        acquired: AcquiredData,
    ) -> None:
        """Execute a single client with error handling and metadata."""
        start = datetime.now(tz=UTC)
        try:
            data = client.acquire(state, self._cache)
            elapsed = (datetime.now(tz=UTC) - start).total_seconds()

            # For SEC filings, extract filing_documents to the dedicated
            # Pydantic field so extractors find them at
            # acquired.filing_documents (not nested in filings dict).
            if target_field == "filings" and isinstance(data, dict):
                _promote_filing_fields(cast(dict[str, Any], data), acquired)

            setattr(acquired, target_field, data)

            acquired.acquisition_metadata[client_name] = {
                "timestamp": start.isoformat(),
                "duration_seconds": elapsed,
                "success": True,
                "error": None,
            }
            logger.info(
                "Client '%s' completed in %.2fs",
                client_name,
                elapsed,
            )

        except Exception as exc:
            elapsed = (datetime.now(tz=UTC) - start).total_seconds()
            acquired.acquisition_metadata[client_name] = {
                "timestamp": start.isoformat(),
                "duration_seconds": elapsed,
                "success": False,
                "error": str(exc),
            }
            logger.warning(
                "Client '%s' failed after %.2fs: %s",
                client_name,
                elapsed,
                exc,
            )

    def _check_and_retry_gates(self, state: AnalysisState, acquired: AcquiredData) -> None:
        """Check gates, retry HARD failures once, then enforce.

        Raises:
            DataAcquisitionError: If HARD gate still fails after retry.
        """
        gate_results = check_gates(acquired)
        hard_failures = [r for r in gate_results if not r.passed and r.gate_type == GateType.HARD]
        soft_failures = [r for r in gate_results if not r.passed and r.gate_type == GateType.SOFT]

        # Log soft failures as warnings.
        for sf in soft_failures:
            logger.warning("SOFT gate failed: %s", sf.message)

        # Retry HARD failures.
        if hard_failures:
            logger.info(
                "Retrying %d HARD gate failures after %ds delay",
                len(hard_failures),
                GATE_RETRY_DELAY_SECONDS,
            )
            time.sleep(GATE_RETRY_DELAY_SECONDS)
            self._retry_hard_gates(hard_failures, state, acquired)

            # Re-check gates after retry.
            gate_results = check_gates(acquired)
            still_failed = [
                r for r in gate_results if not r.passed and r.gate_type == GateType.HARD
            ]
            if still_failed:
                failed_names = [r.gate_name for r in still_failed]
                messages = [r.message for r in still_failed]
                raise DataAcquisitionError(
                    source_name=f"gates:{','.join(failed_names)}",
                    errors=messages,
                )

        # Store gate results.
        acquired.gate_results = [
            {
                "gate_name": r.gate_name,
                "gate_type": str(r.gate_type),
                "passed": r.passed,
                "message": r.message,
            }
            for r in gate_results
        ]

    def _retry_hard_gates(
        self,
        failures: list[Any],
        state: AnalysisState,
        acquired: AcquiredData,
    ) -> None:
        """Retry the specific client for each failed HARD gate."""
        gate_to_client: dict[str, tuple[Any, str]] = {
            "annual_report": (self._sec_client, "filings"),
            "quarterly_report": (self._sec_client, "filings"),
            "proxy_statement": (self._sec_client, "filings"),
            "market_data": (self._market_client, "market_data"),
        }

        retried: set[str] = set()
        for failure in failures:
            client_info = gate_to_client.get(failure.gate_name)
            if client_info is None:
                continue

            client, target_field = client_info
            client_name = client.name

            # Only retry each client once even if multiple gates fail.
            if client_name in retried:
                continue
            retried.add(client_name)

            logger.info("Retrying client '%s' for gate '%s'", client_name, failure.gate_name)
            self._run_client(client_name, client, target_field, state, acquired)


def _log_inventory(inv: AcquisitionInventory) -> None:
    """Log inventory check results for observability."""
    skip_count = len(inv.skip_reasons)
    if skip_count == 0:
        logger.info("Inventory check: all sources need fetching (fresh run)")
        return

    logger.info(
        "Inventory check: %d source(s) can be skipped (incremental run)",
        skip_count,
    )
    for source, reason in inv.skip_reasons.items():
        logger.info("SKIP %s: %s", source, reason)


def _copy_complete_sources(
    inv: AcquisitionInventory,
    existing: AcquiredData,
    acquired: AcquiredData,
) -> None:
    """Copy data from existing state for sources that don't need re-fetching.

    This avoids re-running expensive API calls and LLM extractions
    for data that already exists from a prior pipeline run.
    """
    if not inv.needs_sec_filings:
        acquired.filing_documents = existing.filing_documents
        acquired.filings = existing.filings
        acquired.llm_extractions = existing.llm_extractions
    if not inv.needs_market_data:
        acquired.market_data = existing.market_data
    if not inv.needs_litigation:
        acquired.litigation_data = existing.litigation_data
    if not inv.needs_news:
        acquired.web_search_results = existing.web_search_results
    if not inv.needs_blind_spot:
        acquired.blind_spot_results = existing.blind_spot_results
    if not inv.needs_patents:
        acquired.patent_data = existing.patent_data
    if not inv.needs_logo:
        acquired.company_logo_b64 = existing.company_logo_b64


def _promote_filing_fields(data: dict[str, Any], acquired: AcquiredData) -> None:
    """Extract filing_documents from SEC result to dedicated field.

    The SEC client returns filing_documents nested in the filings dict.
    Extractors expect them at ``acquired.filing_documents`` (the dedicated
    Pydantic field). This function pops the data to the correct location
    so it is not double-stored in both filings and filing_documents.

    Also pops filing_texts (legacy Phase 3 data) from the filings dict
    since it is redundant with filing_documents.
    """
    # Promote filing_documents to dedicated field.
    filing_docs = data.pop("filing_documents", None)
    if filing_docs and isinstance(filing_docs, dict):
        fd = cast(dict[str, list[dict[str, str]]], filing_docs)
        acquired.filing_documents = fd
        logger.info(
            "Promoted filing_documents to dedicated field: %d form types",
            len(fd),
        )

    # Remove legacy filing_texts (superseded by filing_documents).
    data.pop("filing_texts", None)


def _extract_10k_year(filings: dict[str, Any]) -> int | None:
    """Extract the fiscal year from the most recent 10-K filing.

    Scans 10-K filing metadata for the most recent filing date and
    extracts the year. Falls back to 20-F (FPI equivalent) if no 10-K.

    Args:
        filings: Acquired filings dict keyed by form type.

    Returns:
        Fiscal year of the most recent 10-K/20-F, or None if unknown.
    """
    for form_type in ("10-K", "20-F"):
        filing_list = filings.get(form_type, [])
        if not filing_list or not isinstance(filing_list, list):
            continue
        # Find the most recent filing by date.
        latest_date = ""
        for filing in filing_list:
            if isinstance(filing, dict):
                date = filing.get("filing_date", "")
                if date > latest_date:
                    latest_date = date
        if latest_date and len(latest_date) >= 4:
            try:
                return int(latest_date[:4])
            except ValueError:
                pass
    return None


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state, falling back to ticker."""
    if state.company is not None and state.company.identity.legal_name is not None:
        return state.company.identity.legal_name.value
    return state.ticker


# Mapping from SEC form types (as stored in acquired.filings keys)
# to the source type names used in check data_strategy declarations.
_SEC_FORM_TO_SOURCE: dict[str, str] = {
    "10-K": "SEC_10K",
    "20-F": "SEC_10K",  # FPI equivalent
    "10-Q": "SEC_10Q",
    "6-K": "SEC_10Q",  # FPI equivalent
    "DEF 14A": "SEC_DEF14A",
    "8-K": "SEC_8K",
    "4": "SEC_FORM4",
    "frames": "SEC_FRAMES",
    "SC 13D": "SEC_13DG",
    "SC 13D/A": "SEC_13DG",
    "SC 13G": "SEC_13DG",
    "SC 13G/A": "SEC_13DG",
    "S-1": "SEC_S1",
    "S-1/A": "SEC_S1",
    "S-3": "SEC_S3",
    "S-3/A": "SEC_S3",
    "424B": "SEC_424B",
    "424B/A": "SEC_424B",
}


def _determine_acquired_sources(acquired: AcquiredData) -> set[str]:
    """Map AcquiredData fields to source type names.

    Uses the same source names as gap_detector.ACQUIRED_SOURCES so
    brain coverage validation compares apples to apples.

    Args:
        acquired: Populated AcquiredData from orchestrator.

    Returns:
        Set of source type names that were successfully acquired.
    """
    sources: set[str] = set()

    # SEC filings: map form types to source names.
    if acquired.filings:
        for form_type, data in acquired.filings.items():
            if data:  # Non-empty filing data
                source_name = _SEC_FORM_TO_SOURCE.get(form_type)
                if source_name:
                    sources.add(source_name)

    # Also check filing_documents (promoted from filings by orchestrator).
    if acquired.filing_documents:
        for form_type, docs in acquired.filing_documents.items():
            if docs:
                source_name = _SEC_FORM_TO_SOURCE.get(form_type)
                if source_name:
                    sources.add(source_name)

    # Market data.
    if acquired.market_data:
        sources.add("MARKET_PRICE")
        # Check for short interest data specifically.
        if acquired.market_data.get("short_interest"):
            sources.add("MARKET_SHORT")

    # Litigation data.
    if acquired.litigation_data:
        sources.add("SCAC_SEARCH")

    # Insider trading data (from Form 4 or yfinance).
    if acquired.market_data and acquired.market_data.get("insider_transactions"):
        sources.add("INSIDER_TRADES")
    # Also check Form 4 filings as insider trade source.
    if "SEC_FORM4" in sources:
        sources.add("INSIDER_TRADES")

    # Web search results (blind spot sweep, news, etc.).
    if acquired.web_search_results:
        sources.add("WEB_SEARCH")

    # SEC enforcement (may be in regulatory_data or acquisition_metadata).
    if acquired.regulatory_data:
        sources.add("SEC_ENFORCEMENT")

    # SEC enforcement also detected from filing extraction metadata.
    if acquired.acquisition_metadata and acquired.acquisition_metadata.get("sec_enforcement"):
        sources.add("SEC_ENFORCEMENT")

    return sources


def _fetch_company_logo(state: AnalysisState, acquired: AcquiredData) -> None:
    """Fetch company favicon for HTML topbar display (non-blocking).

    Tries:
      1. {domain}/favicon.ico
      2. Open Graph / link[rel=icon] from homepage HTML

    On any failure, logs and returns silently — logo is purely cosmetic.
    """
    try:
        import httpx
    except ImportError:
        logger.debug("httpx not available; skipping company logo fetch")
        return

    website = acquired.market_data.get("info", {}).get("website", "")
    if not website:
        logger.info("Company logo unavailable (non-blocking): no website in market data")
        return

    parsed = urlparse(website)
    if not parsed.scheme or not parsed.netloc:
        logger.info("Company logo unavailable (non-blocking): unparseable website URL")
        return

    domain_base = f"{parsed.scheme}://{parsed.netloc}"
    ticker = state.ticker

    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            # Attempt 1: Google favicon service (most reliable)
            google_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64"
            resp = client.get(google_url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and resp.content and len(resp.content) > 100:
                acquired.company_logo_b64 = base64.b64encode(resp.content).decode("ascii")
                logger.info("Company logo acquired for %s (google favicons)", ticker)
                return

            # Attempt 2: favicon.ico direct
            favicon_url = f"{domain_base}/favicon.ico"
            resp = client.get(favicon_url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and resp.content and len(resp.content) > 100:
                acquired.company_logo_b64 = base64.b64encode(resp.content).decode("ascii")
                logger.info("Company logo acquired for %s (favicon.ico)", ticker)
                return

            # Attempt 3: Open Graph / link[rel=icon] from homepage
            home_resp = client.get(domain_base, headers={"User-Agent": "Mozilla/5.0"})
            if home_resp.status_code == 200:
                html_text = home_resp.text
                icon_url = _extract_icon_url(html_text, domain_base)
                if icon_url:
                    icon_resp = client.get(icon_url, headers={"User-Agent": "Mozilla/5.0"})
                    if icon_resp.status_code == 200 and icon_resp.content:
                        acquired.company_logo_b64 = base64.b64encode(icon_resp.content).decode(
                            "ascii"
                        )
                        logger.info("Company logo acquired for %s (og/link icon)", ticker)
                        return

        logger.info("Company logo unavailable (non-blocking): no icon found for %s", ticker)

    except Exception as exc:
        logger.info("Company logo unavailable (non-blocking): %s", exc)


def _extract_icon_url(html: str, domain_base: str) -> str:
    """Extract best icon URL from homepage HTML.

    Checks (in order): og:image meta tag, link[rel~=icon] tag.
    Returns absolute URL or empty string if none found.
    """
    import re

    # Try Open Graph image
    og_match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if og_match:
        url = og_match.group(1).strip()
        if url.startswith("http"):
            return url

    # Try link rel=icon
    icon_match = re.search(
        r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if icon_match:
        url = icon_match.group(1).strip()
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return f"{domain_base}{url}"

    return ""


def _run_discovery_hook(
    blind_spot_results: dict[str, Any],
    ticker: str,
) -> None:
    """Run automatic discovery on blind spot results (non-blocking).

    Feeds high-relevance blind spot results through the LLM ingestion
    pipeline to generate proposals. Only runs when there are actual
    search results to process.

    All failures are caught and logged — never breaks the pipeline.
    """
    # Only run if blind spot results have actual search data
    has_results = False
    for key in ("pre_structured", "post_structured"):
        val = blind_spot_results.get(key)
        if isinstance(val, dict) and val:
            has_results = True
            break

    if not has_results:
        return

    try:
        from do_uw.knowledge.discovery import (
            get_discovery_summary,
            process_blind_spot_discoveries,
        )

        discoveries = process_blind_spot_discoveries(blind_spot_results, ticker)
        summary = get_discovery_summary(discoveries)

        if summary:
            blind_spot_results["discovery_findings"] = summary
            logger.info("Discovery hook: %s", summary)
        if discoveries:
            blind_spot_results["discovery_details"] = discoveries
    except Exception as exc:
        logger.warning("Discovery hook failed (non-blocking): %s", exc)
        # Non-blocking: blind spot search results remain intact
