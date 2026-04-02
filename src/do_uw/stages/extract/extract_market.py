"""Market extraction sub-orchestrator (SECT4).

Calls all SECT4 extractors in dependency order, collects
ExtractionReports, and assembles a populated MarketSignals model.

Adverse event scoring runs last because it reads other market
sub-models from state.extracted.market.
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence
from do_uw.models.market import (
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
    AdverseEventScore,
    AnalystSentimentProfile,
    CapitalMarketsActivity,
    EarningsGuidanceAnalysis,
    InsiderTradingAnalysis,
    StockDropAnalysis,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)


def run_market_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
    manifest: object | None = None,
) -> MarketSignals:
    """Run all SECT4 market extractors in dependency order.

    Each extractor is wrapped in try/except so a single failure
    does not abort the entire market extraction pass.  On failure
    the default (empty) sub-model is used and a warning is logged.

    Args:
        state: Pipeline state with acquired data.
        reports: Mutable report list -- each extractor appends its report.

    Returns:
        Populated MarketSignals instance.
    """
    signals = MarketSignals()

    # Log brain requirements for this domain if manifest provided
    if manifest is not None:
        from do_uw.stages.extract.extraction_manifest import ExtractionManifest

        if isinstance(manifest, ExtractionManifest):
            reqs = manifest.get_requirements_for_source("MARKET_PRICE")
            if reqs:
                logger.info(
                    "SECT4: Brain needs %d fields from MARKET_PRICE",
                    len(reqs),
                )

    # 1. Stock performance + drop analysis
    stock, drops = _run_stock_performance(state, reports)
    signals.stock = stock
    signals.stock_drops = drops

    # 2. Insider trading analysis
    signals.insider_analysis = _run_insider_trading(state, reports)

    # 3. Short interest profile (populates model-level field)
    signals.short_interest = _run_short_interest(state, reports)

    # 4. Earnings guidance
    signals.earnings_guidance = _run_earnings_guidance(state, reports)

    # 5. Analyst sentiment
    signals.analyst = _run_analyst_sentiment(state, reports)

    # 6. Capital markets activity
    signals.capital_markets = _run_capital_markets(state, reports)

    # 7. LLM 8-K event enrichment (multi-domain routing)
    _enrich_with_eight_k_events(state, signals)

    # 7b. 8-K item classification (deterministic regex + LLM merge)
    signals.eight_k_items = _run_eight_k_item_classifier(state, reports)

    # Write intermediate market signals to state so adverse event
    # scorer can read them from state.extracted.market.
    _ensure_extracted_market(state, signals)

    # 6b. MARKET_PRICE coverage validation
    _run_market_price_coverage(state, reports)

    # 8. Adverse event score (MUST be last -- reads other sub-models)
    signals.adverse_events = _run_adverse_events(state, reports)

    # 9. Forward statement extraction (Phase 117)
    _run_forward_statements(state, reports)

    return signals


# ------------------------------------------------------------------
# Individual extractor wrappers
# ------------------------------------------------------------------


def _run_stock_performance(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> tuple[StockPerformance, StockDropAnalysis]:
    """Extract stock performance metrics and drop events."""
    try:
        from do_uw.stages.extract.stock_performance import (
            extract_stock_performance,
        )

        perf, drops, report = extract_stock_performance(state)
        reports.append(report)
        logger.info("SECT4-02/03: Stock performance extracted")
        return perf, drops
    except Exception:
        logger.warning(
            "SECT4-02/03: Stock performance extraction failed",
            exc_info=True,
        )
        return StockPerformance(), StockDropAnalysis()


def _run_insider_trading(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> InsiderTradingAnalysis:
    """Extract insider trading analysis."""
    try:
        from do_uw.stages.extract.insider_trading import (
            extract_insider_trading,
        )

        analysis, report = extract_insider_trading(state)
        reports.append(report)
        logger.info("SECT4-04: Insider trading extracted")
        return analysis
    except Exception:
        logger.warning(
            "SECT4-04: Insider trading extraction failed",
            exc_info=True,
        )
        return InsiderTradingAnalysis()


def _run_short_interest(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> ShortInterestProfile:
    """Extract short interest profile."""
    try:
        from do_uw.stages.extract.short_interest import (
            extract_short_interest,
        )

        profile, report = extract_short_interest(state)
        reports.append(report)
        logger.info("SECT4-05: Short interest extracted")
        return profile
    except Exception:
        logger.warning(
            "SECT4-05: Short interest extraction failed",
            exc_info=True,
        )
        return ShortInterestProfile()


def _run_earnings_guidance(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> EarningsGuidanceAnalysis:
    """Extract earnings guidance analysis."""
    try:
        from do_uw.stages.extract.earnings_guidance import (
            extract_earnings_guidance,
        )
        from do_uw.stages.extract.llm_helpers import get_llm_ten_k

        # Get guidance language from 10-K LLM extraction (if available).
        llm_ten_k = get_llm_ten_k(state)
        guidance_text = llm_ten_k.guidance_language if llm_ten_k else None

        analysis, report = extract_earnings_guidance(state, guidance_text=guidance_text)
        reports.append(report)
        logger.info("SECT4-06: Earnings guidance extracted")
        return analysis
    except Exception:
        logger.warning(
            "SECT4-06: Earnings guidance extraction failed",
            exc_info=True,
        )
        return EarningsGuidanceAnalysis()


def _run_analyst_sentiment(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AnalystSentimentProfile:
    """Extract analyst sentiment profile."""
    try:
        from do_uw.stages.extract.earnings_guidance import (
            extract_analyst_sentiment,
        )

        profile, report = extract_analyst_sentiment(state)
        reports.append(report)
        logger.info("SECT4-07: Analyst sentiment extracted")
        return profile
    except Exception:
        logger.warning(
            "SECT4-07: Analyst sentiment extraction failed",
            exc_info=True,
        )
        return AnalystSentimentProfile()


def _run_capital_markets(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> CapitalMarketsActivity:
    """Extract capital markets activity."""
    try:
        from do_uw.stages.extract.capital_markets import (
            extract_capital_markets,
        )

        activity, report = extract_capital_markets(state)
        reports.append(report)
        logger.info("SECT4-08: Capital markets extracted")
        return activity
    except Exception:
        logger.warning(
            "SECT4-08: Capital markets extraction failed",
            exc_info=True,
        )
        return CapitalMarketsActivity()


def _run_market_price_coverage(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> None:
    """Validate MARKET_PRICE field coverage."""
    try:
        from do_uw.stages.extract.market_price_extractor import (
            extract_market_price_coverage,
        )

        coverage_dict, report = extract_market_price_coverage(state)
        reports.append(report)
        logger.info(
            "SECT4-06b: MARKET_PRICE coverage: %d/%d fields (%.1f%%)",
            coverage_dict["extracted_count"],
            coverage_dict["total_required"],
            coverage_dict["coverage_pct"],
        )
    except Exception:
        logger.warning(
            "SECT4-06b: MARKET_PRICE coverage validation failed",
            exc_info=True,
        )


def _run_adverse_events(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AdverseEventScore:
    """Compute adverse event score (must run after all other market extractors)."""
    try:
        from do_uw.stages.analyze.adverse_events import (
            compute_adverse_event_score,
        )

        score, report = compute_adverse_event_score(state)
        reports.append(report)
        logger.info("SECT4-09: Adverse event score computed")
        return score
    except Exception:
        logger.warning(
            "SECT4-09: Adverse event score computation failed",
            exc_info=True,
        )
        return AdverseEventScore()


def _run_forward_statements(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> None:
    """Extract forward-looking statements from 10-K/8-K filings (Phase 117).

    Stores results on state.forward_looking (ForwardLookingData).
    Runs after earnings guidance so credibility engine can use that data later.
    """
    try:
        from do_uw.stages.extract.forward_statements import (
            extract_forward_statements,
        )

        forward_stmts, catalysts, growth_estimates, report = extract_forward_statements(state)
        reports.append(report)

        # Store on state.forward_looking (initialized via default_factory)
        if state.forward_looking is None:
            from do_uw.models.forward_looking import ForwardLookingData

            state.forward_looking = ForwardLookingData()

        state.forward_looking.forward_statements = forward_stmts
        state.forward_looking.catalysts = catalysts
        state.forward_looking.growth_estimates = growth_estimates

        logger.info(
            "SECT4-10: Forward statements: %d statements, %d catalysts, %d estimates",
            len(forward_stmts),
            len(catalysts),
            len(growth_estimates),
        )
    except Exception:
        logger.warning(
            "SECT4-10: Forward statement extraction failed",
            exc_info=True,
        )


# ------------------------------------------------------------------
# LLM 8-K event enrichment
# ------------------------------------------------------------------


def _enrich_with_eight_k_events(
    state: AnalysisState,
    signals: MarketSignals,
) -> None:
    """Integrate LLM 8-K events into market signals and cross-domain state.

    Routes events: departures -> leadership stability, restatements -> audit
    risk flag, agreements/acquisitions/earnings -> business change context.
    Stores structured events on state.acquired_data.market_data for
    downstream stages (ANALYZE, SCORE, RENDER).
    """
    from do_uw.stages.extract.llm_helpers import get_llm_eight_k

    eight_k_list = get_llm_eight_k(state)
    if not eight_k_list:
        return

    from do_uw.stages.extract.eight_k_converter import (
        convert_acquisitions,
        convert_agreements,
        convert_auditor_changes,
        convert_bylaws_changes,
        convert_departures,
        convert_earnings_events,
        convert_ethics_changes,
        convert_impairments,
        convert_restatements,
        convert_restructurings,
        convert_terminations,
    )

    departures = convert_departures(eight_k_list)
    agreements = convert_agreements(eight_k_list)
    terminations = convert_terminations(eight_k_list)
    acquisitions = convert_acquisitions(eight_k_list)
    restatements = convert_restatements(eight_k_list)
    earnings = convert_earnings_events(eight_k_list)
    restructurings = convert_restructurings(eight_k_list)
    impairments = convert_impairments(eight_k_list)
    auditor_changes = convert_auditor_changes(eight_k_list)
    bylaws_changes = convert_bylaws_changes(eight_k_list)
    ethics_changes = convert_ethics_changes(eight_k_list)

    # Store structured events for downstream consumption
    events_summary: dict[str, object] = {
        "departure_count": len(departures),
        "agreement_count": len(agreements),
        "termination_count": len(terminations),
        "acquisition_count": len(acquisitions),
        "restatement_count": len(restatements),
        "earnings_event_count": len(earnings),
        "restructuring_count": len(restructurings),
        "impairment_count": len(impairments),
        "auditor_change_count": len(auditor_changes),
        "bylaws_change_count": len(bylaws_changes),
        "ethics_change_count": len(ethics_changes),
    }
    if state.acquired_data is not None:
        state.acquired_data.market_data["eight_k_events"] = events_summary

    # Flag restatements as critical audit risk signal
    if restatements and state.acquired_data is not None:
        state.acquired_data.market_data["has_restatement"] = True
        rst_details: list[dict[str, object]] = []
        for r in restatements:
            periods_raw = r.get("periods")
            periods_list: list[str] = []
            if isinstance(periods_raw, list):
                for p in periods_raw:
                    periods_list.append(p.value if hasattr(p, "value") else str(p))
            reason_raw = r.get("reason")
            reason_str: str | None = None
            if reason_raw is not None and hasattr(reason_raw, "value"):
                reason_str = str(reason_raw.value)  # type: ignore[union-attr]
            rst_details.append({"periods": periods_list, "reason": reason_str})
        state.acquired_data.market_data["restatement_details"] = rst_details

    # Flag auditor changes as critical audit risk signal
    if auditor_changes and state.acquired_data is not None:
        state.acquired_data.market_data["has_auditor_change"] = True

    # Flag impairments for financial deterioration tracking
    if impairments and state.acquired_data is not None:
        state.acquired_data.market_data["has_material_impairment"] = True

    if departures:
        logger.info("SECT4: Found %d executive departures from 8-K", len(departures))
    if agreements or terminations or acquisitions:
        logger.info(
            "SECT4: Found %d agreements, %d terminations, %d acquisitions from 8-K",
            len(agreements),
            len(terminations),
            len(acquisitions),
        )
    if restatements:
        logger.info("SECT4: Found %d restatements from 8-K", len(restatements))
    if auditor_changes:
        logger.warning("SECT4: Found %d auditor changes from 8-K", len(auditor_changes))
    if restructurings:
        logger.info("SECT4: Found %d restructurings from 8-K", len(restructurings))
    if impairments:
        logger.info("SECT4: Found %d material impairments from 8-K", len(impairments))
    if earnings:
        logger.info("SECT4: Found %d earnings events from 8-K", len(earnings))
    if bylaws_changes:
        logger.info("SECT4: Found %d bylaws amendments from 8-K", len(bylaws_changes))
    if ethics_changes:
        logger.warning("SECT4: Found %d ethics code changes from 8-K", len(ethics_changes))


# ------------------------------------------------------------------
# 8-K Item Classification (SECT4-10)
# ------------------------------------------------------------------


def _run_eight_k_item_classifier(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> EightKItemSummary:
    """Run deterministic 8-K item classification.

    Parses raw 8-K filing text for Item X.XX patterns, merges with
    LLM extraction items_covered, and produces a structured summary
    of all 8-K events with D&O-critical flagging.
    """
    from do_uw.models.market import EightKItemSummary

    try:
        from do_uw.stages.extract.eight_k_item_classifier import (
            classify_eight_k_filings,
        )

        result = classify_eight_k_filings(state)
        reports.append(
            ExtractionReport(
                extractor_name="eight_k_item_classifier",
                expected_fields=["eight_k_items"],
                found_fields=["eight_k_items"] if result else [],
                missing_fields=[] if result else ["eight_k_items"],
                unexpected_fields=[],
                coverage_pct=100.0 if result else 0.0,
                confidence=Confidence.HIGH if result else Confidence.LOW,
                source_filing="8-K filings",
            )
        )
        return result
    except Exception:
        logger.warning(
            "SECT4-10: 8-K item classification failed",
            exc_info=True,
        )
        reports.append(
            ExtractionReport(
                extractor_name="eight_k_item_classifier",
                expected_fields=["eight_k_items"],
                found_fields=[],
                missing_fields=["eight_k_items"],
                unexpected_fields=[],
                coverage_pct=0.0,
                confidence=Confidence.LOW,
                source_filing="8-K filings",
            )
        )
        return EightKItemSummary()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _ensure_extracted_market(state: AnalysisState, signals: MarketSignals) -> None:
    """Write intermediate market signals to state for adverse scorer."""
    from do_uw.models.state import ExtractedData

    if state.extracted is None:
        state.extracted = ExtractedData()
    state.extracted.market = signals
