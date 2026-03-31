"""Forward-looking risk map context builder.

Extracts forward statement data, catalysts, growth estimates, and
alternative market signals from AnalysisState into template-ready dicts.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_percentage, na_if_none


_MISS_RISK_CSS: dict[str, str] = {
    "HIGH": "risk-high",
    "MEDIUM": "risk-medium",
    "LOW": "risk-low",
}

_LITIGATION_RISK_CSS: dict[str, str] = {
    "HIGH": "risk-high",
    "MEDIUM": "risk-medium",
    "LOW": "risk-low",
}

_TREND_ICONS: dict[str, str] = {
    "UP": "\u2191",     # up arrow
    "DOWN": "\u2193",   # down arrow
    "FLAT": "\u2192",   # right arrow
}


def _format_forward_statements(state: AnalysisState) -> dict[str, Any]:
    """Format forward statements into template-ready list."""
    fl = state.forward_looking
    statements: list[dict[str, Any]] = []
    has_quantitative = False

    for stmt in fl.forward_statements:
        if stmt.guidance_type == "QUANTITATIVE":
            has_quantitative = True
        statements.append({
            "metric_name": stmt.metric_name or "Unknown",
            "current_value": stmt.current_value or "N/A",
            "guidance_claim": stmt.guidance_claim or "N/A",
            "guidance_type": stmt.guidance_type or "UNKNOWN",
            "miss_risk": stmt.miss_risk or "UNKNOWN",
            "miss_risk_rationale": stmt.miss_risk_rationale or "",
            "sca_relevance": stmt.sca_relevance or "",
            "source": stmt.source_filing or "",
            "confidence": stmt.confidence or "MEDIUM",
            "row_class": _MISS_RISK_CSS.get(stmt.miss_risk, "risk-low"),
        })

    return {
        "forward_statements": statements,
        "forward_statement_count": len(statements),
        "has_forward_statements": len(statements) > 0,
        "has_quantitative_guidance": has_quantitative,
    }


def _format_catalysts(state: AnalysisState) -> dict[str, Any]:
    """Format catalyst events into template-ready list."""
    fl = state.forward_looking
    catalysts: list[dict[str, Any]] = []

    for cat in fl.catalysts:
        catalysts.append({
            "event": cat.event or "Unknown",
            "timing": cat.timing or "Unknown",
            "impact_if_negative": cat.impact_if_negative or "",
            "litigation_risk": cat.litigation_risk or "LOW",
            "row_class": _LITIGATION_RISK_CSS.get(cat.litigation_risk, "risk-low"),
        })

    return {
        "catalysts": catalysts,
        "catalyst_count": len(catalysts),
        "has_catalysts": len(catalysts) > 0,
    }


def _format_growth_estimates(state: AnalysisState) -> dict[str, Any]:
    """Format growth estimates into template-ready list."""
    fl = state.forward_looking
    estimates: list[dict[str, Any]] = []

    for ge in fl.growth_estimates:
        trend_key = (ge.trend or "").upper()
        estimates.append({
            "period": ge.period or "Unknown",
            "metric": ge.metric or "Unknown",
            "estimate": ge.estimate or "N/A",
            "trend": ge.trend or "FLAT",
            "trend_icon": _TREND_ICONS.get(trend_key, "\u2192"),
            "source": ge.source or "",
        })

    return {
        "growth_estimates": estimates,
        "has_growth_estimates": len(estimates) > 0,
    }


def _format_alt_signals(state: AnalysisState) -> dict[str, Any]:
    """Extract alternative market signals from state.extracted.market."""
    result: dict[str, Any] = {
        "short_interest": {},
        "analyst_sentiment": {},
        "buyback_support": {"has_buyback": False, "amount": "N/A"},
        "has_alt_signals": False,
    }

    if state.extracted is None or state.extracted.market is None:
        return result

    mkt = state.extracted.market

    # Short interest
    si = mkt.short_interest
    if si:
        si_data: dict[str, Any] = {}
        if si.shares_short and si.shares_short.value is not None:
            si_data["shares_short"] = f"{si.shares_short.value:,}"
        if si.days_to_cover and si.days_to_cover.value is not None:
            si_data["short_ratio"] = f"{si.days_to_cover.value:.1f}"
        if si.trend_6m and si.trend_6m.value:
            si_data["trend"] = str(si.trend_6m.value)
        if si_data:
            result["short_interest"] = si_data
            result["has_alt_signals"] = True

    # Analyst sentiment
    analyst = mkt.analyst
    if analyst:
        a_data: dict[str, Any] = {}
        if analyst.consensus and analyst.consensus.value:
            a_data["consensus"] = str(analyst.consensus.value)
        if analyst.target_price_mean and analyst.target_price_mean.value is not None:
            a_data["target_mean"] = f"${analyst.target_price_mean.value:,.2f}"
        if analyst.coverage_count and analyst.coverage_count.value is not None:
            a_data["coverage_count"] = analyst.coverage_count.value
        elif analyst.analyst_count and analyst.analyst_count.value is not None:
            a_data["coverage_count"] = analyst.analyst_count.value
        if a_data:
            result["analyst_sentiment"] = a_data
            result["has_alt_signals"] = True

    return result


def extract_forward_risk_map(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Extract forward-looking risk map data for template rendering.

    Reads from state.forward_looking for forward statements, catalysts,
    and growth estimates. Reads from state.extracted.market for alt signals.

    Returns dict with template-ready data including forward_statements,
    catalysts, growth_estimates, alt_signals, and availability flags.
    """
    result: dict[str, Any] = {}

    # Forward statements
    result.update(_format_forward_statements(state))

    # Catalysts
    result.update(_format_catalysts(state))

    # Growth estimates
    result.update(_format_growth_estimates(state))

    # Alternative signals
    result["alt_signals"] = _format_alt_signals(state)

    # Overall availability flag
    result["forward_available"] = (
        result["has_forward_statements"]
        or result["has_catalysts"]
        or result["has_growth_estimates"]
        or result["alt_signals"]["has_alt_signals"]
    )

    return result
