"""Peer percentile context builder for SEC Frames benchmarking display.

Transforms FramesPercentileResult data from the benchmark stage into
template-ready dicts with direction-aware risk coloring and dual bar
(overall vs sector) percentile positioning.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_currency, format_percentage


# Direction mapping: whether HIGH values are favorable, unfavorable, or neutral
_FAVORABLE_HIGH: set[str] = {
    "operating_margin",
    "net_margin",
    "roe",
    "current_ratio",
    "cash_from_operations",
    "operating_income",
}
_UNFAVORABLE_HIGH: set[str] = {
    "debt_to_equity",
    "total_liabilities",
}
# Everything else (revenue, net_income, total_assets, total_equity, rd_expense,
# current_assets, current_liabilities) is NEUTRAL (size metric, no risk color).


_DISPLAY_LABELS: dict[str, str] = {
    "revenue": "Revenue",
    "net_income": "Net Income",
    "total_assets": "Total Assets",
    "total_equity": "Stockholders' Equity",
    "total_liabilities": "Total Liabilities",
    "operating_income": "Operating Income",
    "cash_from_operations": "Cash from Operations",
    "rd_expense": "R&D Expense",
    "current_ratio": "Current Ratio",
    "debt_to_equity": "Debt-to-Equity",
    "operating_margin": "Operating Margin",
    "net_margin": "Net Margin",
    "roe": "Return on Equity",
    "current_assets": "Current Assets",
    "current_liabilities": "Current Liabilities",
}

# Ordered display sequence (10 direct + 5 derived = 15 max)
_DISPLAY_ORDER: list[str] = [
    "revenue",
    "net_income",
    "operating_income",
    "operating_margin",
    "net_margin",
    "roe",
    "total_assets",
    "total_equity",
    "total_liabilities",
    "debt_to_equity",
    "current_ratio",
    "cash_from_operations",
    "rd_expense",
    "current_assets",
    "current_liabilities",
]


def _format_value(value: float | None, metric_key: str) -> str:
    """Format a metric value based on its type."""
    if value is None:
        return "\u2014"
    key = metric_key.lower()
    # Ratio metrics
    if key in ("current_ratio", "debt_to_equity"):
        return f"{value:.2f}x"
    if key in ("operating_margin", "net_margin", "roe"):
        return format_percentage(value * 100 if abs(value) < 5 else value)
    # Currency metrics
    return format_currency(value, compact=True)


def _risk_color(
    percentile: float | None,
    metric_key: str,
) -> str:
    """Determine CSS color variable based on percentile and direction.

    For metrics where HIGH IS GOOD: bottom 25% = red, top 25% = green.
    For metrics where HIGH IS BAD: top 25% = red, bottom 25% = green.
    For NEUTRAL metrics: always navy.
    """
    if percentile is None:
        return "var(--do-navy)"

    if metric_key in _FAVORABLE_HIGH:
        # High is good: low percentile = risky (red)
        if percentile <= 25:
            return "var(--do-risk-red)"
        if percentile >= 75:
            return "var(--do-risk-green)"
        return "var(--do-navy)"

    if metric_key in _UNFAVORABLE_HIGH:
        # High is bad: high percentile = risky (red)
        if percentile >= 75:
            return "var(--do-risk-red)"
        if percentile <= 25:
            return "var(--do-risk-green)"
        return "var(--do-navy)"

    # Neutral (size metrics) - always navy
    return "var(--do-navy)"


def _favorable_direction(metric_key: str) -> str:
    """Return 'high', 'low', or 'neutral' for the metric."""
    if metric_key in _FAVORABLE_HIGH:
        return "high"
    if metric_key in _UNFAVORABLE_HIGH:
        return "low"
    return "neutral"


def build_peer_percentile_context(state: AnalysisState) -> dict[str, Any]:
    """Build peer percentile context for the template.

    Returns:
        Dict with keys: has_data, metrics (list), filer_count, sector_name.
        Each metric dict: label, overall, sector, company_value, risk_color,
        favorable_direction.
    """
    bm = state.benchmark
    if bm is None or not bm.frames_percentiles:
        return {"has_data": False, "metrics": [], "filer_count": 0, "sector_name": None}

    fp = bm.frames_percentiles
    metrics: list[dict[str, Any]] = []
    max_filer_count = 0
    sector_name: str | None = None

    for key in _DISPLAY_ORDER:
        if key not in fp:
            continue
        entry = fp[key]
        overall = entry.overall
        sector = entry.sector

        if overall is not None and entry.peer_count_overall > max_filer_count:
            max_filer_count = entry.peer_count_overall

        metrics.append({
            "label": _DISPLAY_LABELS.get(key, key.replace("_", " ").title()),
            "key": key,
            "overall": round(overall, 1) if overall is not None else None,
            "sector": round(sector, 1) if sector is not None else None,
            "company_value": _format_value(entry.company_value, key),
            "risk_color": _risk_color(overall, key),
            "favorable_direction": _favorable_direction(key),
            "filer_count": entry.peer_count_overall,
            "sector_filer_count": entry.peer_count_sector,
        })

    # Derive sector name from company SIC if available
    if state.company and state.company.identity.sic_code and state.company.identity.sic_code.value:
        from do_uw.stages.resolve.sec_identity import sic_to_sector
        sector_name = sic_to_sector(str(state.company.identity.sic_code.value))

    return {
        "has_data": len(metrics) > 0,
        "metrics": metrics,
        "filer_count": max_filer_count,
        "sector_name": sector_name,
    }


__all__ = ["build_peer_percentile_context"]
