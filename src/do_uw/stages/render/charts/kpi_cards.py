"""KPI summary card builder (INFO-06).

Builds context dicts for compact KPI card layouts at the top of major
sections. Each card shows: metric value, label, optional trend arrow,
optional sub-label. The actual rendering is CSS grid in the template.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.charts.trend_arrows import render_trend_arrow, trend_direction


def build_kpi_card(
    label: str,
    value: str,
    *,
    sub_label: str = "",
    current: float | None = None,
    previous: float | None = None,
    inverted: bool = False,
    severity: str = "",
) -> dict[str, Any]:
    """Build a single KPI card context dict.

    Args:
        label: Metric label (e.g., "Revenue").
        value: Formatted display value (e.g., "$42.3B").
        sub_label: Optional secondary text (e.g., "FY 2025").
        current: Current numeric value for trend detection.
        previous: Previous numeric value for trend detection.
        inverted: If True, decrease is positive (e.g., expenses).
        severity: Risk severity class: "critical", "elevated", "watch", "positive", "".

    Returns:
        Dict ready for template rendering.
    """
    # Compute trend arrow SVG if we have comparison data
    trend_svg = ""
    direction = "flat"
    if current is not None and previous is not None:
        direction = trend_direction(current, previous)
        trend_svg = render_trend_arrow(direction, inverted=inverted)

    return {
        "label": label,
        "value": value,
        "sub_label": sub_label,
        "trend_svg": trend_svg,
        "direction": direction,
        "severity": severity,
    }


def build_kpi_strip(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a KPI strip context with multiple cards.

    Args:
        cards: List of card dicts (from build_kpi_card).

    Returns:
        Dict with 'cards' list and 'count' for template grid sizing.
    """
    return {
        "cards": cards,
        "count": len(cards),
    }


__all__ = ["build_kpi_card", "build_kpi_strip"]
