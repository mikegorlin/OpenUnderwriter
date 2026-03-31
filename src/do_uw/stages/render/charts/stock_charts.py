"""Bloomberg dark theme stock performance charts (VIS-01).

Creates dual-axis area charts with Bloomberg Terminal GP-inspired styling:
- Left Y-axis: company dollar price with green/red conditional area fill
- Right Y-axis: sector ETF (dashed gold) and S&P 500 (dotted blue) indexed to 100
- Stats header: current price, 52W H/L, total return, vs sector, alpha, beta ratio
- Drop markers: yellow dots for 5-10%, red dots for 10%+
- Divergence bands: shaded gap when company vs sector diverge >10%
- Volume subplot: gray/red bars beneath the main chart
- Earnings markers: dashed vertical lines with colored 'E' labels
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]

from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.charts.stock_chart_data import (
    ChartData,
    compute_chart_stats,
    extract_chart_data,
    index_to_base,
)
from do_uw.stages.render.charts.stock_chart_overlays import (
    compute_beta_ratio,
    render_class_period_shading,
    render_divergence_bands,
    render_drop_markers,
    render_earnings_markers,
    render_litigation_markers,
    render_volume_bars,
)
from do_uw.stages.render.chart_style_registry import resolve_colors
from do_uw.stages.render.design_system import DesignSystem

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_stock_chart(
    state: AnalysisState,
    period: str = "1Y",
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a stock performance chart for the given period.

    Uses BLOOMBERG_DARK colors by default (dark background). Pass
    CREDIT_REPORT_LIGHT for light-themed PDF output on white background.

    Args:
        state: Complete analysis state with market data.
        period: Chart period ("1Y" or "5Y").
        ds: Design system for styling.
        colors: Optional color palette dict.
        format: Output format -- "png" returns BytesIO, "svg" returns str.

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    # Resolve colors from chart style registry.
    # SVG always gets light theme; PNG/PDF get dark theme (stock's default).
    if format == "svg":
        c = resolve_colors("stock", "svg")
    else:
        c = colors if colors is not None else resolve_colors("stock", format)
    data = extract_chart_data(state, period)
    if data is None:
        return None

    stats = compute_chart_stats(data, state=state)

    matplotlib.use("Agg")
    # Only use dark_background style for dark theme
    if c.get("bg") == resolve_colors("stock", "png").get("bg"):
        plt.style.use("dark_background")  # pyright: ignore[reportUnknownMemberType]
    else:
        plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 6.5), dpi=200, facecolor=c["bg"]
    )

    # Stats header (top 10% of figure).
    ax_header: Any = fig.add_axes([0.05, 0.88, 0.9, 0.10])
    _render_stats_header(ax_header, stats, data.ticker, period, c, data)

    # Main chart area (shrunk to make room for volume subplot).
    ax: Any = fig.add_axes([0.08, 0.25, 0.82, 0.58])
    ax.set_facecolor(c["bg"])

    # Company price area on left axis.
    _render_price_area(ax, data.dates, data.prices, data.ticker, c)

    # Right axis for indexed overlays.
    ax2: Any = ax.twinx()
    _render_overlays(ax2, data, c)
    render_divergence_bands(ax2, data, c)

    # Drop markers on left axis (company price scale).
    render_drop_markers(ax, data, c)

    # Earnings date markers on the main chart.
    render_earnings_markers(ax, data, c)

    # Litigation filing date markers on the main chart.
    render_litigation_markers(ax, data, c)

    # SCA class period shading — the most important visual for D&O underwriters.
    render_class_period_shading(ax, data, c)

    # Legend combining both axes.
    _render_legend(ax, ax2, data.ticker, data.etf_ticker, c)

    # Styling.
    _apply_bloomberg_style(ax, ax2, period, c)

    # Volume subplot beneath the main chart (shared x-axis).
    ax_vol: Any = fig.add_axes([0.08, 0.10, 0.82, 0.13], sharex=ax)
    render_volume_bars(ax_vol, data, c)

    # Hide x-axis labels on main chart (volume subplot shows them).
    if ax_vol.get_visible():
        ax.tick_params(axis="x", labelbottom=False)
        # Apply date formatting to volume subplot x-axis instead.
        _apply_volume_xaxis_style(ax_vol, period, c)

    _ = ds  # Reserved for future extensions.
    if format == "svg":
        return save_chart_to_svg(fig)
    return save_chart_to_bytes(fig, dpi=200)


@null_safe_chart
def create_stock_performance_chart(
    state: AnalysisState,
    period: str = "1Y",
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Backward-compatible alias for create_stock_chart."""
    return create_stock_chart(state, period=period, ds=ds, colors=colors, format=format)


@null_safe_chart
def create_stock_performance_chart_5y(
    state: AnalysisState,
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a 5-year stock performance chart (backward-compatible)."""
    return create_stock_chart(state, period="5Y", ds=ds, colors=colors, format=format)


# ---------------------------------------------------------------------------
# Stats header
# ---------------------------------------------------------------------------


def _render_stats_header(
    ax_header: Any, stats: dict[str, Any], ticker: str, period: str,
    c: dict[str, str], data: ChartData | None = None,
) -> None:
    """Render key metrics in a header bar above the chart."""
    ax_header.set_facecolor(c["header_bg"])
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")

    # Ticker name on far left.
    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax_header.text(
        0.02, 0.5, f"{ticker} Price vs Sector & Market ({period_label})",
        fontsize=9, fontweight="bold",
        color=c["header_text"],
        va="center",
    )

    # Stat items.
    items = _build_stat_items(stats, c, data)
    x_start = 0.22
    x_step = 0.16 if len(items) <= 5 else 0.13

    for i, (label, value, color) in enumerate(items):
        x = x_start + i * x_step
        ax_header.text(
            x, 0.72, label,
            fontsize=6, color=c["text_muted"],
            va="center",
        )
        ax_header.text(
            x, 0.28, value,
            fontsize=9, fontweight="bold", color=color,
            va="center",
        )


def _build_stat_items(
    stats: dict[str, Any],
    c: dict[str, str],
    data: ChartData | None = None,
) -> list[tuple[str, str, str]]:
    """Build (label, value_str, color) tuples for the stats header."""
    items: list[tuple[str, str, str]] = []
    white = c["header_text"]
    green = c["price_up"]
    red = c["price_down"]

    # Current price.
    cp = stats.get("current_price")
    if isinstance(cp, (int, float)):
        items.append(("Price", f"${cp:,.2f}", white))
    else:
        items.append(("Price", "N/A", white))

    # 52W H/L.
    h = stats.get("high_52w")
    lo = stats.get("low_52w")
    if isinstance(h, (int, float)) and isinstance(lo, (int, float)):
        items.append(("52W H/L", f"${h:,.2f} / ${lo:,.2f}", white))
    else:
        items.append(("52W H/L", "N/A", white))

    # Total return.
    tr = stats.get("total_return_pct")
    if isinstance(tr, (int, float)):
        clr = green if tr >= 0 else red
        items.append(("Return", f"{tr:+.1f}%", clr))
    else:
        items.append(("Return", "N/A", white))

    # Sector return.
    sr = stats.get("sector_return_pct")
    if isinstance(sr, (int, float)):
        clr = green if sr >= 0 else red
        items.append(("Sector", f"{sr:+.1f}%", clr))
    else:
        items.append(("Sector", "N/A", white))

    # Alpha.
    alpha = stats.get("alpha_pct")
    if isinstance(alpha, (int, float)):
        clr = green if alpha >= 0 else red
        items.append(("Alpha", f"{alpha:+.1f}%", clr))
    else:
        items.append(("Alpha", "N/A", white))

    # Beta Ratio (company_beta / sector_beta).
    if data is not None:
        ratio, color_key = compute_beta_ratio(data)
        if ratio is not None:
            amber = c.get("drop_yellow", "#FFEB3B")
            if color_key == "price_down":
                clr = red
            elif color_key == "drop_yellow":
                clr = amber
            else:
                clr = white
            items.append(("\u03B2 Ratio", f"{ratio:.2f}x", clr))

    return items


# ---------------------------------------------------------------------------
# Company price area
# ---------------------------------------------------------------------------


def _render_price_area(
    ax: Any,
    dates: list[datetime],
    prices: list[float],
    ticker: str,
    c: dict[str, str],
) -> None:
    """Plot company price with green/red conditional area fill."""
    if not prices:
        return

    base_price = prices[0]

    # Main price line.
    ax.plot(
        dates, prices,
        color=c["price_up"],
        linewidth=1.5, label=ticker, zorder=3,
    )

    # Green fill where price >= starting price.
    ax.fill_between(
        dates, prices, base_price,
        where=[p >= base_price for p in prices],
        color=c["fill_up_alpha"],
        alpha=0.2, interpolate=True, label="_nolegend_",
    )

    # Red fill where price < starting price.
    ax.fill_between(
        dates, prices, base_price,
        where=[p < base_price for p in prices],
        color=c["fill_down_alpha"],
        alpha=0.2, interpolate=True, label="_nolegend_",
    )

    ax.set_ylabel(
        f"$ {ticker}", color=c["text"], fontsize=9,
    )


# ---------------------------------------------------------------------------
# Overlays (ETF + SPY on right axis)
# ---------------------------------------------------------------------------


def _render_overlays(ax2: Any, data: ChartData, c: dict[str, str]) -> None:
    """Render sector ETF and SPY as indexed lines on the right axis."""
    has_overlay = False

    if data.etf_dates and data.etf_prices:
        etf_indexed = index_to_base(data.etf_prices, 100.0)
        ax2.plot(
            data.etf_dates, etf_indexed,
            linestyle="--", color=c["etf_line"],
            linewidth=1.0, label=data.etf_ticker or "Sector ETF",
            zorder=2,
        )
        has_overlay = True

    if data.spy_dates and data.spy_prices:
        spy_indexed = index_to_base(data.spy_prices, 100.0)
        ax2.plot(
            data.spy_dates, spy_indexed,
            linestyle=":", color=c["spy_line"],
            linewidth=1.0, label="S&P 500",
            zorder=2,
        )
        has_overlay = True

    if has_overlay:
        ax2.set_ylabel(
            "Indexed (100 = start)",
            color=c["text"], fontsize=9,
        )
    else:
        ax2.set_yticks([])


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------


def _render_legend(
    ax: Any, ax2: Any, ticker: str, etf_ticker: str,
    c: dict[str, str],
) -> None:
    """Combine legends from both axes into one small legend."""
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    all_handles = handles1 + handles2
    all_labels = labels1 + labels2

    if not all_handles:
        return

    ax.legend(
        all_handles, all_labels,
        loc="upper left", fontsize=7,
        framealpha=0.6, facecolor=c["bg"],
        edgecolor=c["grid"],
        labelcolor=c["text"],
    )
    _ = (ticker, etf_ticker)


# ---------------------------------------------------------------------------
# Bloomberg chart styling
# ---------------------------------------------------------------------------


def _apply_bloomberg_style(
    ax: Any, ax2: Any, period: str, c: dict[str, str],
) -> None:
    """Apply chart styling to axes (dark or light theme)."""
    for a in (ax, ax2):
        a.tick_params(colors=c["text"], labelsize=7)
        for spine in a.spines.values():
            spine.set_color(c["grid"])
            spine.set_linewidth(0.5)

    ax.grid(
        visible=True, alpha=0.3,
        color=c["grid"], linewidth=0.5,
    )
    ax2.grid(False)

    # Date formatting.
    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.tick_params(axis="x", rotation=0)


def _apply_volume_xaxis_style(
    ax_vol: Any, period: str, c: dict[str, str],
) -> None:
    """Apply date formatting to the volume subplot x-axis."""
    if period == "1Y":
        ax_vol.xaxis.set_major_locator(mdates.MonthLocator())
        ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax_vol.xaxis.set_major_locator(mdates.YearLocator())
        ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax_vol.tick_params(axis="x", rotation=0, labelsize=6, colors=c.get("text", "#ccc"))


__all__ = [
    "create_stock_chart",
    "create_stock_performance_chart",
    "create_stock_performance_chart_5y",
]
