"""Signal-backed evaluative content for market context builders.

Extracts volatility regime, short interest assessment, insider trading
verdict, guidance track record, and return/beta interpretation from
brain signal results with graceful fallback to direct state reads.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
    safe_get_value,
)
from do_uw.stages.render.formatters import format_percentage


def _extract_volatility_signals(
    signal_results: dict[str, Any] | None,
    stock: Any,
) -> dict[str, Any]:
    """Extract volatility regime from STOCK.PRICE signals with state fallback."""
    result: dict[str, Any] = {}

    idio_vol = safe_get_result(signal_results, "STOCK.PRICE.idiosyncratic_vol")
    if idio_vol and idio_vol.value is not None:
        result["volatility_signal_level"] = signal_to_display_level(
            idio_vol.status, idio_vol.threshold_level,
        )
        result["volatility_signal_evidence"] = idio_vol.evidence

    # D&O context for volatility
    result["volatility_do_context"] = idio_vol.do_context if idio_vol and idio_vol.do_context else ""

    # Display data with signal enrichment
    if stock.volatility_90d:
        result["volatility_90d"] = format_percentage(stock.volatility_90d.value)
    if stock.ewma_vol_current:
        result["ewma_vol"] = format_percentage(stock.ewma_vol_current.value)
    if stock.vol_regime:
        vol_signal = safe_get_value(signal_results, "STOCK.PRICE.idiosyncratic_vol")
        result["vol_regime"] = stock.vol_regime.value
        if vol_signal is not None:
            result["vol_regime_source"] = "signal"
    if stock.vol_regime_duration_days is not None:
        result["vol_regime_duration"] = str(stock.vol_regime_duration_days)

    return result


def _extract_short_interest_signals(
    signal_results: dict[str, Any] | None,
    si: Any,
) -> dict[str, Any]:
    """Extract short interest assessment from STOCK.SHORT signals."""
    result: dict[str, Any] = {}

    short_position = safe_get_result(signal_results, "STOCK.SHORT.position")
    short_trend = safe_get_result(signal_results, "STOCK.SHORT.trend")

    if short_position and short_position.value is not None:
        result["short_signal_level"] = signal_to_display_level(
            short_position.status, short_position.threshold_level,
        )
        result["short_signal_evidence"] = short_position.evidence

    # D&O context for short interest
    result["short_do_context"] = short_position.do_context if short_position and short_position.do_context else ""

    if short_trend and short_trend.status == "TRIGGERED":
        result["short_trend_signal"] = short_trend.evidence or "Increasing"

    # Absolute counts (display data, always from state)
    if si.shares_short:
        result["shares_short"] = f"{si.shares_short.value:,}"
    if si.shares_short_prior:
        result["shares_short_prior"] = f"{si.shares_short_prior.value:,}"
    if si.short_pct_shares_out:
        result["short_pct_shares_out"] = format_percentage(si.short_pct_shares_out.value)

    # Short interest trend from state
    if si.trend_6m and si.trend_6m.value:
        result["short_trend_6m"] = str(si.trend_6m.value)

    return result


def _extract_insider_signals(
    signal_results: dict[str, Any] | None,
    mkt: Any,
) -> dict[str, Any]:
    """Extract insider trading verdict from STOCK.INSIDER signals."""
    result: dict[str, Any] = {}

    insider_summary = safe_get_result(signal_results, "STOCK.INSIDER.summary")
    cluster_timing = safe_get_result(signal_results, "STOCK.INSIDER.cluster_timing")
    notable = safe_get_result(signal_results, "STOCK.INSIDER.notable_activity")

    if insider_summary and insider_summary.value is not None:
        result["insider_signal_level"] = signal_to_display_level(
            insider_summary.status, insider_summary.threshold_level,
        )
        result["insider_signal_evidence"] = insider_summary.evidence

    # D&O context for insider trading
    result["insider_do_context"] = insider_summary.do_context if insider_summary and insider_summary.do_context else ""
    result["cluster_timing_do_context"] = cluster_timing.do_context if cluster_timing and cluster_timing.do_context else ""

    if cluster_timing and cluster_timing.status == "TRIGGERED":
        result["cluster_timing_alert"] = cluster_timing.evidence or "Suspicious timing"

    if notable and notable.status == "TRIGGERED":
        result["notable_insider_activity"] = notable.evidence or "Notable activity detected"

    return result


def _extract_guidance_signals(
    signal_results: dict[str, Any] | None,
    mkt: Any,
) -> dict[str, Any]:
    """Extract guidance track record from FIN.GUIDE signals."""
    result: dict[str, Any] = {}

    track_record = safe_get_result(signal_results, "FIN.GUIDE.track_record")
    philosophy = safe_get_result(signal_results, "FIN.GUIDE.philosophy")
    earnings_reaction = safe_get_result(signal_results, "FIN.GUIDE.earnings_reaction")
    revision_pattern = safe_get_result(
        signal_results, "FIN.GUIDE.estimate_revision_pattern",
    )

    if track_record and track_record.value is not None:
        result["guidance_signal_level"] = signal_to_display_level(
            track_record.status, track_record.threshold_level,
        )
        result["guidance_signal_evidence"] = track_record.evidence

    # D&O context for guidance
    result["guidance_do_context"] = track_record.do_context if track_record and track_record.do_context else ""

    if earnings_reaction and earnings_reaction.status == "TRIGGERED":
        result["earnings_reaction_alert"] = (
            earnings_reaction.evidence or "Adverse market reaction"
        )

    if revision_pattern and revision_pattern.status == "TRIGGERED":
        result["revision_pattern_alert"] = (
            revision_pattern.evidence or "Downward revision trend"
        )

    # Aggregate guidance signals for summary
    guidance_signals = safe_get_signals_by_prefix(signal_results, "FIN.GUIDE.")
    triggered = [s for s in guidance_signals if s.status == "TRIGGERED"]
    if triggered:
        result["guidance_alert_count"] = len(triggered)

    return result


def _extract_return_signals(
    signal_results: dict[str, Any] | None,
    stock: Any,
) -> dict[str, Any]:
    """Extract beta/return assessment from STOCK.PRICE signals."""
    result: dict[str, Any] = {}

    beta_signal = safe_get_result(signal_results, "STOCK.PRICE.beta_ratio_elevated")
    returns_signal = safe_get_result(
        signal_results, "STOCK.PRICE.returns_multi_horizon",
    )

    # D&O context for return/beta signals
    result["beta_do_context"] = beta_signal.do_context if beta_signal and beta_signal.do_context else ""
    result["returns_do_context"] = returns_signal.do_context if returns_signal and returns_signal.do_context else ""

    if beta_signal and beta_signal.value is not None:
        result["beta_signal_level"] = signal_to_display_level(
            beta_signal.status, beta_signal.threshold_level,
        )
        result["beta_signal_evidence"] = beta_signal.evidence

    if returns_signal and returns_signal.value is not None:
        result["returns_signal_level"] = signal_to_display_level(
            returns_signal.status, returns_signal.threshold_level,
        )
        result["returns_signal_evidence"] = returns_signal.evidence

    # Display data always from state
    if stock.returns_1y:
        result["return_1y"] = format_percentage(stock.returns_1y.value)
    if stock.max_drawdown_1y:
        result["max_drawdown_1y"] = format_percentage(stock.max_drawdown_1y.value)
    if stock.beta:
        result["beta"] = f"{stock.beta.value:.2f}"

    return result


__all__ = [
    "_extract_guidance_signals",
    "_extract_insider_signals",
    "_extract_return_signals",
    "_extract_short_interest_signals",
    "_extract_volatility_signals",
]
