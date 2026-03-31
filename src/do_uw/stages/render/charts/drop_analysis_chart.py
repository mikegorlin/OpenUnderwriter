"""Drop analysis chart for D&O underwriting worksheets.

Creates a dedicated chart set for stock drop events:
- Drop event timeline with magnitude bars and trigger annotations
- Company vs sector scatter showing which drops are company-specific
- Recovery analysis showing days to recover for each drop

Drop events are the #1 trigger for securities class actions.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.patches import Rectangle

from do_uw.models.market_events import StockDropEvent
from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.charts.stock_chart_data import extract_chart_data
from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart

# Trigger category to display color mapping from chart style registry.
_da_colors = get_chart_style("drop_analysis").colors
_CATEGORY_COLORS: dict[str, str] = {
    "earnings_miss": str(_da_colors.get("earnings_miss", "#B91C1C")),
    "guidance_cut": str(_da_colors.get("guidance_cut", "#D97706")),
    "restatement": str(_da_colors.get("restatement", "#7C3AED")),
    "management_departure": str(_da_colors.get("management_departure", "#2563EB")),
    "litigation": str(_da_colors.get("litigation", "#DC2626")),
    "regulatory": str(_da_colors.get("regulatory", "#9333EA")),
    "analyst_downgrade": str(_da_colors.get("analyst_downgrade", "#EA580C")),
    "acquisition": str(_da_colors.get("acquisition", "#0891B2")),
    "market_wide": str(_da_colors.get("market_wide", "#6B7280")),
    "unknown": str(_da_colors.get("unknown", "#374151")),
    "other_event": str(_da_colors.get("other_event", "#4B5563")),
    "": str(_da_colors.get("unknown", "#374151")),
}

# Trigger category to short display label.
_CATEGORY_LABELS: dict[str, str] = {
    "earnings_miss": "Earnings",
    "guidance_cut": "Guidance",
    "restatement": "Restatement",
    "management_departure": "Exec Change",
    "litigation": "Litigation",
    "regulatory": "Regulatory",
    "analyst_downgrade": "Downgrade",
    "acquisition": "Deal",
    "market_wide": "Market",
    "unknown": "Unexplained",
    "other_event": "Other",
    "agreement": "Agreement",
    "restructuring": "Restructuring",
    "material_impairment": "Impairment",
    "delisting": "Delisting",
    "": "Unexplained",  # Empty/unset trigger_category
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_drop_analysis_chart(
    state: AnalysisState,
    period: str = "1Y",
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a drop analysis chart showing all significant drops.

    Renders a two-panel chart:
    - Top: Price line with drop events annotated (trigger + magnitude)
    - Bottom: Drop waterfall showing magnitude bars colored by category

    Args:
        state: Complete analysis state with market and drop data.
        period: Chart period ("1Y" or "5Y").
        format: "png" or "svg".

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    c = resolve_colors("drop_analysis", format)
    data = extract_chart_data(state, period)
    if data is None or not data.drops:
        return None

    # Sort drops by date.
    drops = _sort_drops(data.drops)
    if not drops:
        return None

    matplotlib.use("Agg")
    plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 6), dpi=200, facecolor=c["bg"],
    )

    try:
        # Header (top 10%).
        ax_header: Any = fig.add_axes([0.05, 0.90, 0.9, 0.08])
        _render_header(ax_header, drops, data.ticker, period, c)

        # Top panel: Price with annotated drops (55% height).
        ax_price: Any = fig.add_axes([0.08, 0.40, 0.86, 0.48])
        _render_price_with_drops(ax_price, data.dates, data.prices, drops, data.ticker, period, c)

        # Bottom panel: Drop waterfall (30% height).
        ax_waterfall: Any = fig.add_axes([0.08, 0.06, 0.86, 0.30])
        _render_drop_waterfall(ax_waterfall, drops, c)

        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


@null_safe_chart
def create_drop_scatter_chart(
    state: AnalysisState,
    period: str = "1Y",
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create drop vs sector scatter chart.

    Each drop plotted as company drop % (x) vs sector drop % (y).
    Points below the diagonal are company-specific.

    Args:
        state: Analysis state with drop data.
        period: Chart period.
        format: Output format.

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    c = resolve_colors("drop_analysis", format)
    data = extract_chart_data(state, period)
    if data is None or not data.drops:
        return None

    drops = [d for d in data.drops if d.sector_return_pct is not None]
    if not drops:
        return None

    matplotlib.use("Agg")
    plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 5), dpi=200, facecolor=c["bg"],
    )

    try:
        # Header.
        ax_header: Any = fig.add_axes([0.05, 0.88, 0.9, 0.10])
        _render_scatter_header(ax_header, data.ticker, period, drops, c)

        # Main scatter.
        ax: Any = fig.add_axes([0.10, 0.10, 0.84, 0.75])
        _render_scatter(ax, drops, c)

        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


# ---------------------------------------------------------------------------
# Header rendering
# ---------------------------------------------------------------------------


def _render_header(
    ax: Any, drops: list[StockDropEvent],
    ticker: str, period: str, c: dict[str, str],
) -> None:
    """Render stats header for drop analysis chart."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    bg_rect = Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=c.get("header_bg", "#0B1D3A"),
        edgecolor="none", zorder=0, clip_on=False,
    )
    ax.add_patch(bg_rect)

    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax.text(
        0.02, 0.5, f"{ticker} Drop Event Analysis ({period_label})",
        fontsize=9, fontweight="bold",
        color=c.get("header_text", "#FFFFFF"), va="center",
    )

    white = c.get("header_text", "#FFFFFF")
    red = c.get("price_down", "#B91C1C")

    # Stats.
    total = len(drops)
    company_specific = sum(1 for d in drops if d.is_company_specific)
    unexplained = sum(1 for d in drops if d.trigger_category in ("unknown", ""))
    worst_pct = min(
        (d.drop_pct.value for d in drops if d.drop_pct), default=0.0,
    )

    items = [
        ("Events", str(total), white),
        ("Company-Specific", str(company_specific), red if company_specific > 0 else white),
        ("Unexplained", str(unexplained), red if unexplained > 0 else white),
        ("Worst Drop", f"{worst_pct:.1f}%", red),
    ]

    x_start = 0.38
    x_step = 0.16
    for i, (label, value, color) in enumerate(items):
        x = x_start + i * x_step
        ax.text(x, 0.72, label, fontsize=6, color=c.get("text_muted", "#6B7280"), va="center")
        ax.text(x, 0.28, value, fontsize=9, fontweight="bold", color=color, va="center")


# ---------------------------------------------------------------------------
# Price with drops panel
# ---------------------------------------------------------------------------


def _render_price_with_drops(
    ax: Any,
    dates: list[datetime],
    prices: list[float],
    drops: list[StockDropEvent],
    ticker: str,
    period: str,
    c: dict[str, str],
) -> None:
    """Render price line with drop events prominently annotated."""
    ax.set_facecolor(c["bg"])

    # Price line.
    ax.plot(dates, prices, color=c["price_up"], linewidth=1.2, alpha=0.7, label=ticker)

    # Shade drop zones.
    for drop in drops:
        if not drop.date or not drop.drop_pct:
            continue

        drop_date = _parse_date(drop.date.value)
        if drop_date is None:
            continue

        y_pos = _find_y(dates, prices, drop_date)
        if y_pos is None:
            continue

        pct = drop.drop_pct.value
        cat = drop.trigger_category or "unknown"
        color = _CATEGORY_COLORS.get(cat, "#374151")

        # Marker size by severity.
        if pct <= -15.0:
            size = 12
        elif pct <= -10.0:
            size = 9
        else:
            size = 7

        # Shape: circle for company-specific, diamond for market-wide.
        if drop.is_market_wide and not drop.is_company_specific:
            marker = "D"
            alpha = 0.6
        else:
            marker = "o"
            alpha = 0.9

        ax.plot(
            drop_date, y_pos, marker,
            color=color, markersize=size, alpha=alpha, zorder=5,
        )

        # Build rich annotation.
        label_parts = [f"{pct:+.1f}%"]
        cat_label = _CATEGORY_LABELS.get(cat, cat)
        if cat_label and cat_label != "Unknown":
            label_parts.append(cat_label)

        # Add trigger description snippet (first 40 chars) — skip yfinance boilerplate.
        if drop.trigger_description:
            _td = drop.trigger_description
            _is_garbage = any(p in _td for p in (
                "Find the latest", "stock quote", "vital information",
                "make the best investing", "finance.yahoo.com",
            ))
            if not _is_garbage:
                desc = _td[:40]
                if len(_td) > 40:
                    desc += "..."
                label_parts.append(desc)

        label = "\n".join(label_parts)

        # Alternate annotation position to avoid overlaps.
        ax.annotate(
            label,
            (drop_date, y_pos),
            textcoords="offset points",
            xytext=(6, -16),
            fontsize=5.0, color=color,
            ha="left", va="top", zorder=6,
            linespacing=0.85,
            bbox=dict(
                boxstyle="round,pad=0.15",
                facecolor="white", edgecolor=color,
                alpha=0.8, linewidth=0.5,
            ),
        )

    # Style.
    ax.tick_params(colors=c["text"], labelsize=7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(c["grid"])
        ax.spines[spine].set_linewidth(0.5)
    ax.grid(visible=True, alpha=0.3, color=c["grid"], linewidth=0.5)
    ax.set_ylabel("Price ($)", color=c["text"], fontsize=8)

    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


# ---------------------------------------------------------------------------
# Drop waterfall panel
# ---------------------------------------------------------------------------


def _render_drop_waterfall(
    ax: Any,
    drops: list[StockDropEvent],
    c: dict[str, str],
) -> None:
    """Render horizontal bar chart of drop magnitudes with category colors."""
    ax.set_facecolor(c["bg"])

    # Build bar data.
    labels: list[str] = []
    values: list[float] = []
    colors: list[str] = []
    edge_colors: list[str] = []

    for i, drop in enumerate(drops):
        if not drop.drop_pct or not drop.date:
            continue

        pct = drop.drop_pct.value
        date_str = drop.date.value[:10]
        cat = drop.trigger_category or "unknown"
        cat_label = _CATEGORY_LABELS.get(cat, cat)

        # Label: date + category.
        labels.append(f"{date_str}\n{cat_label}")
        values.append(pct)
        bar_color = _CATEGORY_COLORS.get(cat, "#374151")
        colors.append(bar_color)

        # Thicker edge for company-specific.
        if drop.is_company_specific:
            edge_colors.append(bar_color)
        else:
            edge_colors.append("#D1D5DB")

    if not values:
        ax.set_visible(False)
        return

    y_pos = list(range(len(values)))

    bars = ax.barh(
        y_pos, values, color=colors, edgecolor=edge_colors,
        linewidth=1.0, height=0.6, zorder=3,
    )

    # Add percentage labels on bars.
    for i, (bar, val) in enumerate(zip(bars, values)):
        text_x = val - 0.5 if val < -5 else val + 0.3
        ha = "right" if val < -5 else "left"
        ax.text(
            text_x, i, f"{val:+.1f}%",
            va="center", ha=ha, fontsize=6, fontweight="bold",
            color="white" if val < -5 else colors[i],
            zorder=4,
        )

        # Add recovery days if available.
        drop = drops[i]
        if drop.recovery_days is not None:
            rec_text = f"{drop.recovery_days}d" if drop.recovery_days > 0 else "N/R"
            ax.text(
                0.2, i, f"Recovery: {rec_text}",
                va="center", ha="left", fontsize=5,
                color=c["text_muted"], zorder=4,
            )

    # Style.
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6, color=c["text"])
    ax.invert_yaxis()  # Chronological order top to bottom.
    ax.set_xlabel("Drop %", fontsize=7, color=c["text"])

    ax.tick_params(colors=c["text"], labelsize=6)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(c["grid"])
        ax.spines[spine].set_linewidth(0.5)

    ax.axvline(x=0, color=c["grid"], linewidth=0.5)
    ax.axvline(x=-10, color=c["drop_red"], linewidth=0.5, linestyle="--", alpha=0.4)
    ax.grid(visible=True, axis="x", alpha=0.2, color=c["grid"], linewidth=0.5)


# ---------------------------------------------------------------------------
# Scatter chart
# ---------------------------------------------------------------------------


def _render_scatter_header(
    ax: Any, ticker: str, period: str,
    drops: list[StockDropEvent], c: dict[str, str],
) -> None:
    """Render header for scatter chart."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    bg_rect = Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=c.get("header_bg", "#0B1D3A"),
        edgecolor="none", zorder=0, clip_on=False,
    )
    ax.add_patch(bg_rect)

    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax.text(
        0.02, 0.5,
        f"{ticker} Drop Events: Company vs Sector ({period_label})",
        fontsize=9, fontweight="bold",
        color=c.get("header_text", "#FFFFFF"), va="center",
    )

    company_specific = sum(1 for d in drops if d.is_company_specific)
    white = c.get("header_text", "#FFFFFF")
    ax.text(
        0.65, 0.5,
        f"Company-Specific: {company_specific}/{len(drops)} events",
        fontsize=8, color=white, va="center",
    )


def _render_scatter(
    ax: Any, drops: list[StockDropEvent], c: dict[str, str],
) -> None:
    """Render scatter plot: company drop vs sector drop."""
    ax.set_facecolor(c["bg"])

    for drop in drops:
        if not drop.drop_pct or not drop.sector_return_pct:
            continue

        company_pct = drop.drop_pct.value
        sector_pct = drop.sector_return_pct.value
        cat = drop.trigger_category or "unknown"
        color = _CATEGORY_COLORS.get(cat, "#374151")

        size = 60 if drop.is_company_specific else 40
        marker = "o" if not drop.is_market_wide else "D"
        alpha = 0.9 if drop.is_company_specific else 0.5

        ax.scatter(
            company_pct, sector_pct,
            c=color, s=size, marker=marker, alpha=alpha, zorder=3,
            edgecolors=color, linewidths=0.8,
        )

        # Label with date.
        date_label = drop.date.value[:10] if drop.date else ""
        ax.annotate(
            date_label,
            (company_pct, sector_pct),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=5, color=c["text_muted"],
            zorder=4,
        )

    # Diagonal line (equal decline = sector-driven).
    lims = ax.get_xlim()
    diag_range = [min(lims[0], -30), 0]
    ax.plot(diag_range, diag_range, "--", color=c["grid"], linewidth=0.8, alpha=0.5, zorder=1)

    # Zone labels.
    ax.text(
        -20, -5, "Company-Specific\n(stock fell more than sector)",
        fontsize=6, color=c["drop_red"], alpha=0.6, ha="center",
    )
    ax.text(
        -5, -20, "Sector-Driven\n(sector also declined)",
        fontsize=6, color=c["text_muted"], alpha=0.6, ha="center",
    )

    # Style.
    ax.set_xlabel("Company Drop %", fontsize=8, color=c["text"])
    ax.set_ylabel("Sector Return %", fontsize=8, color=c["text"])
    ax.tick_params(colors=c["text"], labelsize=7)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(c["grid"])
        ax.spines[spine].set_linewidth(0.5)

    ax.grid(visible=True, alpha=0.2, color=c["grid"], linewidth=0.5)
    ax.axhline(y=0, color=c["grid"], linewidth=0.5)
    ax.axvline(x=0, color=c["grid"], linewidth=0.5)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sort_drops(drops: list[StockDropEvent]) -> list[StockDropEvent]:
    """Sort drops chronologically."""
    def _date_key(d: StockDropEvent) -> str:
        return d.date.value[:10] if d.date else ""
    return sorted(drops, key=_date_key)


def _parse_date(date_str: str) -> datetime | None:
    """Parse a single date string."""
    try:
        return datetime.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _find_y(
    dates: list[datetime], prices: list[float], target: datetime,
) -> float | None:
    """Find y-value at nearest date."""
    if not dates:
        return None
    best_idx = 0
    best_diff = abs((dates[0] - target).total_seconds())
    for i, d in enumerate(dates[1:], 1):
        diff = abs((d - target).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_idx = i
    return prices[best_idx] if best_idx < len(prices) else None


__all__ = [
    "create_drop_analysis_chart",
    "create_drop_scatter_chart",
]
