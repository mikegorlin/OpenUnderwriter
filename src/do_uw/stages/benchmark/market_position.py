"""Market position pipeline integration for BENCHMARK stage.

Queries the pricing knowledge store for market intelligence data,
computes mispricing alerts when current ROL deviates significantly
from peer segment median, and returns a MarketIntelligence model
ready for attachment to AnalysisState.

Non-breaking: returns has_data=False when no pricing data exists
or when the pricing module is unavailable.
"""

from __future__ import annotations

import logging

from do_uw.models.executive_summary import MarketIntelligence

logger = logging.getLogger(__name__)

_MISPRICING_THRESHOLD_PCT = 15.0
"""Deviation threshold (%) for mispricing alert."""


def check_mispricing(
    current_premium: float,
    current_limit: float,
    median_rate_on_line: float,
    peer_count: int,
    ci_low: float | None,
    ci_high: float | None,
) -> str | None:
    """Check if current pricing diverges significantly from market.

    Returns an alert string if |deviation| > 15%, None otherwise.

    Args:
        current_premium: Current program premium in USD.
        current_limit: Current program limit in USD.
        median_rate_on_line: Market median ROL for peer segment.
        peer_count: Number of comparable quotes.
        ci_low: 95% CI lower bound (for context in alert).
        ci_high: 95% CI upper bound (for context in alert).

    Returns:
        Alert string like "OVERPRICED vs market: current ROL 0.0450
        is 28.6% above median 0.0350 (n=12, CI: 0.0310-0.0390)"
        or None if within threshold.
    """
    if current_limit <= 0 or median_rate_on_line <= 0:
        return None

    current_rol = current_premium / current_limit
    deviation_pct = (current_rol - median_rate_on_line) / median_rate_on_line * 100.0

    if abs(deviation_pct) <= _MISPRICING_THRESHOLD_PCT:
        return None

    direction = "OVERPRICED" if deviation_pct > 0 else "UNDERPRICED"
    above_below = "above" if deviation_pct > 0 else "below"

    ci_str = ""
    if ci_low is not None and ci_high is not None:
        ci_str = f", CI: {ci_low:.4f}-{ci_high:.4f}"

    return (
        f"{direction} vs market: current ROL {current_rol:.4f} is "
        f"{abs(deviation_pct):.1f}% {above_below} median "
        f"{median_rate_on_line:.4f} (n={peer_count}{ci_str})"
    )


_MODEL_VS_MARKET_THRESHOLD_PCT = 20.0
"""Deviation threshold (%) for model-vs-market mispricing alert."""


def check_model_vs_market_mispricing(
    model_indicated_rol: float,
    market_median_rol: float,
    peer_count: int,
    ci_low: float | None,
    ci_high: float | None,
) -> str | None:
    """Check if actuarial model pricing diverges from market pricing.

    Compares the risk-assessment-indicated rate on line to the market
    median ROL. Flags when divergence exceeds 20%.

    Args:
        model_indicated_rol: Actuarial model indicated rate on line.
        market_median_rol: Market median ROL for peer segment.
        peer_count: Number of comparable quotes.
        ci_low: 95% CI lower bound (for context in alert).
        ci_high: 95% CI upper bound (for context in alert).

    Returns:
        Alert string like "MODEL SUGGESTS UNDERPRICED BY MARKET: model
        indicated ROL 0.0550 is 37.1% above market median 0.0401 ..."
        or None if within threshold.
    """
    if model_indicated_rol <= 0 or market_median_rol <= 0:
        return None

    deviation_pct = (
        (model_indicated_rol - market_median_rol)
        / market_median_rol
        * 100.0
    )

    if abs(deviation_pct) <= _MODEL_VS_MARKET_THRESHOLD_PCT:
        return None

    ci_str = ""
    if ci_low is not None and ci_high is not None:
        ci_str = f", CI: {ci_low:.4f}-{ci_high:.4f}"

    if deviation_pct > 0:
        return (
            f"MODEL SUGGESTS UNDERPRICED BY MARKET: model indicated ROL "
            f"{model_indicated_rol:.4f} is {abs(deviation_pct):.1f}% above "
            f"market median {market_median_rol:.4f} (n={peer_count}{ci_str}). "
            f"Risk assessment indicates higher loss potential than current "
            f"market pricing reflects."
        )
    return (
        f"MODEL SUGGESTS OVERPRICED BY MARKET: model indicated ROL "
        f"{model_indicated_rol:.4f} is {abs(deviation_pct):.1f}% below "
        f"market median {market_median_rol:.4f} (n={peer_count}{ci_str}). "
        f"Market pricing exceeds model-indicated risk."
    )


def _build_segment_label(
    market_cap_tier: str, sector: str | None
) -> str:
    """Build a human-readable segment label from tier and sector."""
    parts: list[str] = []
    if market_cap_tier:
        parts.append(market_cap_tier.upper())
    if sector:
        parts.append(sector.upper())
    return " / ".join(parts) if parts else "ALL SEGMENTS"


def get_market_intelligence(
    ticker: str,
    quality_score: float,
    market_cap_tier: str,
    sector: str | None,
    current_premium: float | None = None,
    current_limit: float | None = None,
) -> MarketIntelligence:
    """Query pricing store and compute market intelligence for a company.

    Non-breaking: returns MarketIntelligence(has_data=False) when
    pricing data is unavailable or the pricing module cannot be imported.

    Args:
        ticker: Company stock ticker.
        quality_score: Company quality score from SCORE stage.
        market_cap_tier: Market cap tier (MEGA, LARGE, MID, SMALL, MICRO).
        sector: Sector code (TECH, FINS, etc.) or None.
        current_premium: Current program premium (optional, for mispricing).
        current_limit: Current program limit (optional, for mispricing).

    Returns:
        MarketIntelligence model populated from pricing store data.
    """
    try:
        from do_uw.knowledge.pricing_analytics import MarketPositionEngine
        from do_uw.knowledge.pricing_store import PricingStore
    except ImportError:
        logger.debug("Pricing module not available, skipping market intelligence")
        return MarketIntelligence(has_data=False)

    try:
        store = PricingStore()
        engine = MarketPositionEngine(store)
        position = engine.get_position_for_analysis(
            ticker=ticker,
            quality_score=quality_score,
            market_cap_tier=market_cap_tier,
            sector=sector,
        )
    except Exception:
        logger.warning(
            "Failed to query pricing store for %s", ticker, exc_info=True
        )
        return MarketIntelligence(has_data=False)

    if position.confidence_level == "INSUFFICIENT":
        return MarketIntelligence(
            has_data=False,
            peer_count=position.peer_count,
            segment_label=_build_segment_label(market_cap_tier, sector),
        )

    # Build populated intelligence
    segment_label = _build_segment_label(market_cap_tier, sector)

    # Check mispricing if current pricing is provided
    mispricing_alert: str | None = None
    if (
        current_premium is not None
        and current_limit is not None
        and position.median_rate_on_line is not None
    ):
        mispricing_alert = check_mispricing(
            current_premium=current_premium,
            current_limit=current_limit,
            median_rate_on_line=position.median_rate_on_line,
            peer_count=position.peer_count,
            ci_low=position.ci_low,
            ci_high=position.ci_high,
        )

    return MarketIntelligence(
        has_data=True,
        peer_count=position.peer_count,
        confidence_level=position.confidence_level,
        median_rate_on_line=position.median_rate_on_line,
        ci_low=position.ci_low,
        ci_high=position.ci_high,
        trend_direction=position.trend_direction,
        trend_magnitude_pct=position.trend_magnitude_pct,
        mispricing_alert=mispricing_alert,
        data_window=position.data_window,
        segment_label=segment_label,
    )


__all__ = [
    "check_mispricing",
    "check_model_vs_market_mispricing",
    "get_market_intelligence",
]
