"""SEC enforcement data acquisition client.

Fetches SEC enforcement actions, litigation releases, AAERs (Accounting and
Auditing Enforcement Releases), and consent decrees for a company.

4-tier fallback chain:
  1. SEC Litigation Releases (LR) API - HIGH confidence, official source
  2. AAER (Accounting and Auditing Enforcement Releases) - HIGH confidence
  3. 10-K Item 3/1A extraction (from already acquired filings) - MEDIUM confidence
  4. Web search for "SEC enforcement [company]" - LOW confidence

Per CLAUDE.md: "Broad web search is a FIRST-CLASS acquisition method,
not a fallback." Web search is tier 4 but treated as legitimate acquisition.

Returns dict with keys:
  - enforcement_history: list of enforcement actions with dates, types, outcomes
  - penalties: monetary penalties assessed
  - consent_decrees: consent agreements and injunctions
  - enforcement_actions: summary counts by year
  - source_tier: which tier succeeded (for metadata)
  - confidence: HIGH, MEDIUM, LOW
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence
from do_uw.models.state import AnalysisState
from do_uw.stages.acquire.fallback import (
    DataAcquisitionError,
    FallbackChain,
    FallbackTier,
)

logger = logging.getLogger(__name__)

# Cache TTL: 14 months (same as 10-K) for enforcement data.
ENFORCEMENT_TTL = 14 * 30 * 24 * 3600


class SECEnforcementClient:
    """SEC enforcement data acquisition client."""

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "sec_enforcement"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire SEC enforcement data for the given company.

        Args:
            state: Analysis state with resolved company identity.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with enforcement data to store in AcquiredData.regulatory_data.
        """
        if state.company is None or state.company.identity.cik is None:
            msg = "Company CIK must be resolved before SEC enforcement acquisition"
            raise ValueError(msg)

        cik = state.company.identity.cik.value
        company_name = (
            state.company.identity.legal_name.value
            if state.company.identity.legal_name
            else state.ticker
        )
        ticker = state.ticker

        logger.info("Acquiring SEC enforcement data for %s (CIK %s)", company_name, cik)

        cache_key = f"sec_enforcement:{ticker}:{cik}"
        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for SEC enforcement: %s", cache_key)
                return dict(cached)

        # Build 4-tier fallback chain.
        chain = self._build_enforcement_chain(cik, company_name, ticker, state)
        try:
            result, confidence, tier_name = chain.execute()
            logger.info(
                "Retrieved SEC enforcement data via %s (confidence: %s)",
                tier_name,
                confidence,
            )
            # Add metadata
            result["source_tier"] = tier_name
            result["confidence"] = confidence.value
        except DataAcquisitionError as exc:
            logger.warning("All SEC enforcement acquisition tiers failed: %s", exc)
            # Return empty structure but mark as failed.
            result = {
                "enforcement_history": [],
                "penalties": [],
                "consent_decrees": [],
                "enforcement_actions": {},
                "source_tier": "none",
                "confidence": "LOW",
                "error": str(exc),
            }

        # Cache the result.
        if cache is not None:
            cache.set(
                cache_key,
                result,
                source=f"sec_enforcement:{result.get('source_tier', 'none')}",
                ttl=ENFORCEMENT_TTL,
            )

        return result

    def _build_enforcement_chain(
        self, cik: str, company_name: str, ticker: str, state: AnalysisState
    ) -> FallbackChain:
        """Build 4-tier fallback chain for SEC enforcement data."""
        # Create wrapper functions that capture arguments and accept **kwargs
        def make_closure(fn, *captured_args):
            def wrapper(**kwargs):
                return fn(*captured_args)
            return wrapper
        
        tiers = [
            # Tier 1: SEC Litigation Releases API (HIGH confidence)
            FallbackTier(
                name="sec_litigation_releases",
                confidence=Confidence.HIGH,
                acquire_fn=make_closure(self._acquire_litigation_releases, cik, company_name),
            ),
            # Tier 2: AAER (Accounting and Auditing Enforcement Releases) - HIGH confidence
            FallbackTier(
                name="sec_aaer",
                confidence=Confidence.HIGH,
                acquire_fn=make_closure(self._acquire_aaer, cik, company_name),
            ),
            # Tier 3: 10‑K Item 3/1A extraction (MEDIUM confidence)
            FallbackTier(
                name="tenk_extraction",
                confidence=Confidence.MEDIUM,
                acquire_fn=make_closure(self._acquire_from_tenk, state),
            ),
            # Tier 4: Web search (LOW confidence)
            FallbackTier(
                name="web_search",
                confidence=Confidence.LOW,
                acquire_fn=make_closure(self._acquire_via_web_search, company_name, ticker),
            ),
        ]
        
        return FallbackChain(source_name="sec_enforcement", tiers=tiers)


    def _acquire_litigation_releases(self, cik: str, company_name: str) -> dict[str, Any]:
        """Fetch SEC Litigation Releases for a CIK.

        TODO: Implement using SEC API or web scraping.
        Currently returns empty dict to trigger fallback.
        """
        logger.debug("Tier 1: SEC Litigation Releases not implemented, falling back")
        raise DataAcquisitionError(
            source_name="sec_litigation_releases",
            errors=["SEC Litigation Releases API not yet implemented"],
        )

    def _acquire_aaer(self, cik: str, company_name: str) -> dict[str, Any]:
        """Fetch AAER (Accounting and Auditing Enforcement Releases) for a CIK.

        TODO: Implement using SEC API or web scraping.
        Currently returns empty dict to trigger fallback.
        """
        logger.debug("Tier 2: AAER not implemented, falling back")
        raise DataAcquisitionError(
            source_name="sec_aaer",
            errors=["AAER API not yet implemented"],
        )

    def _acquire_from_tenk(self, state: AnalysisState) -> dict[str, Any]:
        """Extract enforcement history from 10-K Item 3/1A.

        Uses existing sec_enforcement.py extractor.
        """
        try:
            from do_uw.stages.extract.sec_enforcement import extract_sec_enforcement
        except ImportError:
            logger.warning("SEC enforcement extractor not available")
            raise DataAcquisitionError(
                source_name="tenk_extraction",
                errors=["SEC enforcement extractor import failed"],
            )

        # Extract from already acquired filings (state.acquired_data).
        try:
            pipeline, report = extract_sec_enforcement(state)
            # Convert pipeline to expected dict format for regulatory_data
            enforcement_history = []
            for signal in pipeline.pipeline_signals:
                enforcement_history.append(
                    {
                        "type": "pipeline_signal",
                        "evidence": signal.value,
                        "source": signal.source,
                        "confidence": signal.confidence.value,
                    }
                )

            # Extract actions if present
            enforcement_actions = []
            for action_sourced in pipeline.actions:
                action = action_sourced.value
                enforcement_actions.append(
                    {
                        "type": action.get("type", "unknown"),
                        "date": action.get("date", ""),
                        "description": action.get("description", ""),
                        "release_number": action.get("release_number", ""),
                    }
                )

            result = {
                "enforcement_history": enforcement_history,
                "penalties": [],  # Not extracted from 10-K
                "consent_decrees": [],  # Not extracted from 10-K
                "enforcement_actions": enforcement_actions,
                "source_tier": "tenk_extraction",  # Overridden by chain with confidence
                "confidence": "MEDIUM",
            }
            logger.info(
                "Extracted SEC enforcement pipeline: %s signals, %s actions",
                len(enforcement_history),
                len(enforcement_actions),
            )
            return result
        except Exception as exc:
            logger.warning("10-K extraction failed: %s", exc)
            raise DataAcquisitionError(
                source_name="tenk_extraction",
                errors=[f"10-K extraction failed: {exc}"],
            )

    def _acquire_via_web_search(self, company_name: str, ticker: str) -> dict[str, Any]:
        """Search web for SEC enforcement news.

        TODO: Integrate with WebSearchClient.
        Currently returns empty dict to trigger failure.
        """
        logger.debug("Tier 4: Web search not implemented, falling back")
        raise DataAcquisitionError(
            source_name="web_search",
            errors=["Web search not yet integrated"],
        )
