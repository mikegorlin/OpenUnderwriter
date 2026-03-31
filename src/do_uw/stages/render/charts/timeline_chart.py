"""VIS-03: Litigation timeline visualization.

Creates a horizontal timeline chart showing chronological legal events
overlaid with corporate events for pattern recognition. Color-codes
events by type using the risk spectrum.
"""

from __future__ import annotations

import io
from datetime import date, timedelta
from typing import Any

import matplotlib
import matplotlib.dates as mdates  # pyright: ignore[reportUnknownMemberType]
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.figure import Figure
from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem

# Event type to display category mapping
_EVENT_CATEGORIES: dict[str, str] = {
    "case_filing": "SCA / Filing",
    "settlement": "Settlement",
    "enforcement_action": "SEC Enforcement",
    "regulatory": "Regulatory",
    "stock_drop": "Corporate",
    "executive_change": "Corporate",
    "derivative": "Derivative",
}

# Event type to color mapping from chart style registry.
_tl_colors = get_chart_style("timeline").colors
_EVENT_COLORS: dict[str, str] = {
    "case_filing": str(_tl_colors.get("case_filing", "#CC0000")),
    "settlement": str(_tl_colors.get("settlement", "#E67300")),
    "enforcement_action": str(_tl_colors.get("enforcement_action", "#CC0000")),
    "regulatory": str(_tl_colors.get("regulatory", "#FFB800")),
    "stock_drop": str(_tl_colors.get("stock_drop", "#4A90D9")),
    "executive_change": str(_tl_colors.get("executive_change", "#4A90D9")),
    "derivative": str(_tl_colors.get("derivative", "#E67300")),
}

# Y-position for each category (bottom to top)
_CATEGORY_Y: dict[str, float] = {
    "SCA / Filing": 5.0,
    "SEC Enforcement": 4.0,
    "Derivative": 3.0,
    "Regulatory": 2.0,
    "Settlement": 1.0,
    "Corporate": 0.0,
}

# Marker shapes per event category
_CATEGORY_MARKERS: dict[str, str] = {
    "SCA / Filing": "D",
    "SEC Enforcement": "s",
    "Derivative": "^",
    "Regulatory": "p",
    "Settlement": "o",
    "Corporate": "v",
}


def _collect_events(
    state: AnalysisState,
) -> list[dict[str, Any]]:
    """Collect all timeline events from state.

    Gathers litigation timeline events plus corporate overlay events
    from market and governance data.
    """
    events: list[dict[str, Any]] = []

    # Litigation timeline events
    lit = state.extracted.litigation if state.extracted else None
    if lit is not None:
        for evt in lit.litigation_timeline_events:
            if evt.event_date is None:
                continue
            evt_type = ""
            if evt.event_type is not None:
                evt_type = evt.event_type.value
            desc = ""
            if evt.description is not None:
                desc = str(evt.description.value)[:50]
            severity = "MODERATE"
            if evt.severity is not None:
                severity = evt.severity.value
            events.append({
                "date": evt.event_date,
                "type": evt_type,
                "description": desc,
                "severity": severity,
            })

    return events


@null_safe_chart
def create_litigation_timeline(
    state: AnalysisState,
    ds: DesignSystem,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a horizontal timeline chart (VIS-03).

    Shows chronological legal and corporate events color-coded by type
    for pattern recognition.

    Args:
        state: Full analysis state with litigation timeline events.
        ds: Design system for colors and styling.
        colors: Optional color dict for theming. Uses default light
            colors when None. Pass CREDIT_REPORT_LIGHT for PDF output.
        format: Output format -- "png" returns BytesIO, "svg" returns str.

    Returns:
        BytesIO with PNG image data, SVG string, or None if no timeline events.
    """
    events = _collect_events(state)
    if not events:
        return None

    # Skip full chart for sparse timelines — the HTML inline timeline
    # handles <=2 events more compactly without wasting a full page.
    if len(events) <= 2:
        return None

    # Resolve theme colors from chart style registry.
    tl_style = get_chart_style("timeline")
    c = resolve_colors("timeline", format)
    text_color = c.get("text", "#333333")
    grid_color = c.get("grid", "#E0E0E0")
    bg_color = c.get("bg", "#FFFFFF")
    spine_color = c.get("grid", "#CCCCCC")

    matplotlib.use("Agg")
    fig: Figure = plt.figure(figsize=tuple(tl_style.figure_size), dpi=200)  # pyright: ignore[reportUnknownMemberType]
    fig.patch.set_facecolor(bg_color)
    ax: Any = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    # Sort events by date
    events.sort(key=lambda e: e["date"])

    # Plot each event
    legend_handles: dict[str, Any] = {}
    for evt in events:
        evt_date: date = evt["date"]
        evt_type: str = evt["type"]
        category = _EVENT_CATEGORIES.get(evt_type, "Corporate")
        color = _EVENT_COLORS.get(evt_type, c.get("text_muted", "#999999"))
        y_pos = _CATEGORY_Y.get(category, 0.0)
        marker = _CATEGORY_MARKERS.get(category, "o")

        handle: Any = ax.scatter(
            [evt_date], [y_pos],
            c=color, s=60, marker=marker, zorder=5,
            edgecolors="white", linewidths=0.5,
        )

        # Track for legend (one per category)
        if category not in legend_handles:
            legend_handles[category] = handle

        # Label high-severity events
        if evt.get("severity") in ("HIGH", "CRITICAL") and evt.get("description"):
            ax.annotate(
                evt["description"][:30],
                xy=(evt_date, y_pos),
                xytext=(0, 8), textcoords="offset points",
                fontsize=5.5, color=text_color,
                ha="center", va="bottom",
                arrowprops={"arrowstyle": "-", "color": spine_color, "lw": 0.5},
            )

    # Configure x-axis as dates — use MonthLocator to prevent duplicate labels
    # that AutoDateLocator produces when the date range is narrow.
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    if events:
        min_date = min(e["date"] for e in events) - timedelta(days=30)
        max_date = max(e["date"] for e in events) + timedelta(days=30)
        date_span_days = (max_date - min_date).days
        if date_span_days <= 180:
            # Narrow range: one tick per month
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        elif date_span_days <= 730:
            # Medium range: quarterly ticks
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        else:
            # Wide range: semi-annual ticks
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.set_xlim(min_date, max_date)

    # Configure y-axis with category labels
    categories_used = sorted(
        {_EVENT_CATEGORIES.get(e["type"], "Corporate") for e in events},
        key=lambda cat: _CATEGORY_Y.get(cat, 0.0),
    )
    y_positions = [_CATEGORY_Y[cat] for cat in categories_used]
    ax.set_yticks(y_positions)
    ax.set_yticklabels(categories_used, fontsize=8, color=text_color)
    ax.set_ylim(-0.5, 5.5)

    # Grid and styling
    ax.grid(visible=True, axis="x", alpha=0.3, color=grid_color, linewidth=0.5)
    ax.axhline(y=-0.5, color=spine_color, linewidth=0.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(spine_color)
        ax.spines[spine].set_linewidth(0.5)

    # Rotate date labels
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=7)  # pyright: ignore[reportUnknownMemberType]

    # Legend
    if legend_handles:
        ax.legend(
            legend_handles.values(), legend_handles.keys(),
            loc="upper left", fontsize=7, frameon=True,
            facecolor=bg_color, edgecolor=spine_color,
        )

    title_color = str(get_chart_style("ownership").colors.get("institutional", "#1A1446"))
    ax.set_title(
        "Litigation & Regulatory Timeline", color=title_color,
        fontweight="bold", fontsize=11, pad=10,
    )

    fig.tight_layout()
    _ = ds  # reserved for future use
    if format == "svg":
        return save_chart_to_svg(fig)
    return save_chart_to_bytes(fig, dpi=200)


__all__ = ["create_litigation_timeline"]
