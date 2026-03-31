"""Resolve stage: Ticker to company identity.

Maps any US-listed stock ticker or company name to a full company
identity (CIK, legal name, SIC, exchange, sector, state, FPI status)
via SEC EDGAR, with yfinance enrichment for market cap and employees.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.resolve.sec_identity import resolve_company_identity
from do_uw.stages.resolve.ticker_resolver import resolve_ticker

logger = logging.getLogger(__name__)


class ResolveStage:
    """Resolve a stock ticker to company identity.

    Pipeline stage 1 of 7. Performs:
    1. Ticker/name resolution to CIK via SEC company_tickers.json
    2. Full identity fetch from SEC submissions API
    3. Market cap and employee count from yfinance
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "resolve"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify ticker is present."""
        if not state.ticker or not state.ticker.strip():
            msg = "Ticker is required for resolve stage"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Resolve ticker to full company identity.

        Populates state.company with CompanyProfile containing:
        - identity: CompanyIdentity from SEC EDGAR
        - market_cap: From yfinance (MEDIUM confidence)
        - employee_count: From yfinance (MEDIUM confidence)
        """
        state.mark_stage_running(self.name)
        cache = AnalysisCache()

        try:
            # Step 1: Resolve ticker/name to CIK.
            resolved = resolve_ticker(state.ticker, cache)
            logger.info(
                "Resolved '%s' -> %s (CIK=%d, confidence=%.1f)",
                state.ticker,
                resolved.company_name,
                resolved.cik,
                resolved.confidence,
            )

            # Update state.ticker to the actual stock symbol.
            # When input is a company name (e.g. "Exponent"), state.ticker
            # starts as "EXPONENT" but the resolved ticker is "EXPO".
            # Downstream stages (yfinance, stock data) need the real ticker.
            if resolved.ticker and resolved.ticker != state.ticker:
                logger.info(
                    "Updating state.ticker: '%s' -> '%s'",
                    state.ticker,
                    resolved.ticker,
                )
                state.ticker = resolved.ticker

            # Step 2: Fetch full company identity from SEC.
            identity = resolve_company_identity(
                resolved.cik, resolved.ticker, cache
            )

            # Merge all_tickers from ticker resolver into identity.
            if resolved.all_tickers:
                identity.all_tickers = resolved.all_tickers

            # Step 3: Build CompanyProfile.
            profile = CompanyProfile(identity=identity)

            # Step 4: Enrich with yfinance data (non-critical).
            _enrich_from_yfinance(profile, resolved.ticker)

            state.company = profile

            # Step 5: Activate industry playbook (non-blocking).
            _activate_industry_playbook(state, identity)

            state.mark_stage_completed(self.name)

            logger.info(
                "RESOLVE complete: %s (CIK=%s, exchange=%s, FPI=%s, playbook=%s)",
                identity.legal_name.value if identity.legal_name else "?",
                identity.cik.value if identity.cik else "?",
                identity.exchange.value if identity.exchange else "?",
                identity.is_fpi,
                state.active_playbook_id or "none",
            )
        except Exception:
            state.mark_stage_failed(self.name, "Resolve stage failed")
            raise
        finally:
            cache.close()


def _activate_industry_playbook(
    state: AnalysisState,
    identity: CompanyIdentity,
) -> None:
    """Activate matching industry playbook based on SIC/NAICS codes.

    Non-blocking: catches all exceptions and logs warnings.
    Sets state.active_playbook_id if a match is found.
    """
    try:
        from do_uw.knowledge.playbooks import activate_playbook
        from do_uw.knowledge.store import KnowledgeStore

        sic_code = ""
        sic_sv = identity.sic_code
        if sic_sv is not None:
            sic_code = str(sic_sv.value)

        naics_code: str | None = None
        naics_sv = identity.naics_code
        if naics_sv is not None:
            naics_code = str(naics_sv.value)

        if not sic_code and not naics_code:
            logger.debug("No SIC/NAICS codes available for playbook activation")
            return

        store = KnowledgeStore(db_path=None)
        playbook = activate_playbook(sic_code, naics_code, store)

        if playbook is not None:
            pb_id = str(playbook["id"])
            state.active_playbook_id = pb_id
            logger.info(
                "Industry playbook activated: %s (%s)",
                pb_id,
                str(playbook.get("name", "")),
            )
        else:
            logger.debug(
                "No industry playbook matched SIC=%s NAICS=%s",
                sic_code,
                naics_code or "",
            )
    except Exception:
        logger.warning(
            "Industry playbook activation failed (non-critical)",
            exc_info=True,
        )


def _enrich_from_yfinance(profile: CompanyProfile, ticker: str) -> None:
    """Enrich CompanyProfile with market data from yfinance.

    Non-critical: logs warnings on failure but does not raise.
    """
    try:
        import yfinance as yf  # type: ignore[import-untyped]

        yf_ticker: Any = yf.Ticker(ticker)
        info: dict[str, object] = dict(
            cast(dict[str, Any], yf_ticker.info)
        )

        market_cap: object = info.get("marketCap")
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            profile.market_cap = SourcedValue[float](
                value=float(market_cap),
                source="yfinance",
                confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            )

        employees: object = info.get("fullTimeEmployees")
        if isinstance(employees, int) and employees > 0:
            profile.employee_count = SourcedValue[int](
                value=employees,
                source="yfinance",
                confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            )

        logger.info(
            "yfinance enrichment: market_cap=%s, employees=%s",
            profile.market_cap.value if profile.market_cap else "N/A",
            profile.employee_count.value if profile.employee_count else "N/A",
        )
    except Exception:
        logger.warning(
            "yfinance enrichment failed for %s (non-critical)", ticker
        )


__all__ = ["ResolveStage"]
