"""Optional enrichment methods for BenchmarkStage.

Market intelligence and actuarial pricing enrichment extracted from
benchmark/__init__.py for 500-line compliance.

Both enrichments are non-breaking: failures are logged and silently
ignored. Their absence never blocks the pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.executive_summary import InherentRiskBaseline
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketPositionProxy:
    """Proxy for MarketIntelligence fields needed by calibrate_against_market.

    Provides the duck-typed interface that actuarial_layer_pricing expects
    (peer_count, confidence_level, median_rate_on_line) without importing
    pricing_analytics.MarketPosition directly.
    """

    peer_count: int
    confidence_level: str
    median_rate_on_line: float | None


def enrich_market_intelligence(
    state: AnalysisState,
    scoring: Any,
) -> None:
    """Optionally enrich state with market pricing intelligence.

    Non-breaking: failures are logged and silently ignored.
    Market intelligence is additive -- its absence never blocks
    the pipeline.
    """
    try:
        from do_uw.stages.benchmark.market_position import (
            get_market_intelligence,
        )

        quality_score = scoring.quality_score
        market_cap_tier = (
            state.benchmark.inherent_risk.market_cap_tier
            if state.benchmark and state.benchmark.inherent_risk
            else "MID"
        )
        sector: str | None = None
        if (
            state.company is not None
            and state.company.identity.sector is not None
        ):
            sector = str(state.company.identity.sector.value)

        mi = get_market_intelligence(
            ticker=state.ticker,
            quality_score=quality_score,
            market_cap_tier=market_cap_tier,
            sector=sector,
        )

        if mi.has_data and state.executive_summary is not None:
            state.executive_summary.deal_context.market_intelligence = mi
            logger.info(
                "Market intelligence: %s, median ROL=%.4f, "
                "confidence=%s, n=%d",
                mi.segment_label,
                mi.median_rate_on_line or 0.0,
                mi.confidence_level,
                mi.peer_count,
            )
        elif not mi.has_data:
            logger.info(
                "No market pricing data for %s (peer_count=%d)",
                state.ticker,
                mi.peer_count,
            )
    except Exception:
        logger.debug(
            "Market intelligence unavailable for %s",
            state.ticker,
            exc_info=True,
        )


def enrich_actuarial_pricing(
    state: AnalysisState,
    scoring: Any,
    inherent_risk: InherentRiskBaseline,
) -> None:
    """Optionally enrich state with actuarial layer pricing.

    Non-breaking: failures are logged and silently ignored.
    Actuarial pricing is additive -- its absence never blocks
    the pipeline.

    Requires:
    - Filing probability from inherent_risk.company_adjusted_rate_pct
    - Severity scenarios from scoring.severity_scenarios
    - actuarial.json config
    """
    try:
        from do_uw.stages.score.actuarial_pricing_builder import (
            build_actuarial_pricing,
        )

        # Guard: severity data required
        severity = getattr(scoring, "severity_scenarios", None)
        if severity is None:
            logger.info(
                "Actuarial pricing skipped for %s: no severity "
                "scenarios",
                state.ticker,
            )
            return

        # Filing probability from inherent risk baseline
        filing_probability_pct = inherent_risk.company_adjusted_rate_pct

        # Sector and market cap tier
        sector: str | None = None
        if (
            state.company is not None
            and state.company.identity.sector is not None
        ):
            sector = str(state.company.identity.sector.value)

        market_cap_tier = inherent_risk.market_cap_tier or "MID"

        # Build market position proxy from MarketIntelligence
        market_position: MarketPositionProxy | None = None
        if (
            state.executive_summary is not None
            and state.executive_summary.deal_context.market_intelligence
            is not None
        ):
            mi = (
                state.executive_summary.deal_context.market_intelligence
            )
            if mi.has_data:
                market_position = MarketPositionProxy(
                    peer_count=mi.peer_count,
                    confidence_level=mi.confidence_level,
                    median_rate_on_line=mi.median_rate_on_line,
                )

        # Load actuarial config
        actuarial_config: dict[str, Any] = load_config("actuarial")

        result = build_actuarial_pricing(
            filing_probability_pct=filing_probability_pct,
            severity_scenarios=severity,
            case_type="standard_sca",
            sector=sector,
            market_cap_tier=market_cap_tier,
            market_position=market_position,
            actuarial_config=actuarial_config,
        )

        scoring.actuarial_pricing = result

        # Model-vs-market mispricing check
        _check_mispricing(result, state)

        if result.has_data:
            logger.info(
                "Actuarial pricing: %d layers, total=$%.0f for %s",
                len(result.layer_pricing),
                result.total_indicated_premium,
                state.ticker,
            )
        else:
            logger.info(
                "Actuarial pricing: insufficient data for %s",
                state.ticker,
            )

    except Exception:
        logger.debug(
            "Actuarial pricing unavailable for %s",
            state.ticker,
            exc_info=True,
        )


def _check_mispricing(result: Any, state: AnalysisState) -> None:
    """Check for model-vs-market pricing mispricing."""
    if (
        not result.has_data
        or not result.layer_pricing
        or state.executive_summary is None
        or state.executive_summary.deal_context.market_intelligence
        is None
    ):
        return

    mi = state.executive_summary.deal_context.market_intelligence
    if not mi.has_data or mi.median_rate_on_line is None:
        return

    primary_pricing = result.layer_pricing[0]
    if primary_pricing.indicated_rol <= 0:
        return

    from do_uw.stages.benchmark.market_position import (
        check_model_vs_market_mispricing,
    )

    model_alert = check_model_vs_market_mispricing(
        model_indicated_rol=primary_pricing.indicated_rol,
        market_median_rol=mi.median_rate_on_line,
        peer_count=mi.peer_count,
        ci_low=mi.ci_low,
        ci_high=mi.ci_high,
    )
    if model_alert is not None:
        mi.model_vs_market_alert = model_alert
        logger.info("Model-vs-market mispricing: %s", model_alert)
