"""Drawdown analysis chart for D&O underwriting worksheets.

Creates a professional drawdown chart showing:
- Company running drawdown (red area fill)
- Sector ETF running drawdown (dashed gold line) for comparison
- Maximum drawdown annotated with horizontal arrow showing duration
- Stats header: Max DD, Avg DD, Current DD, Recovery Days, DD Duration
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
from do_uw.stages.render.charts.chart_computations import compute_drawdown_series
from do_uw.stages.render.charts.stock_chart_data import extract_chart_data
from do_uw.stages.render.chart_style_registry import resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _get_mdd_context(
    state: AnalysisState,
    period: str,
) -> dict[str, float | None]:
    """Extract MDD ratio and sector MDD from state for the drawdown header."""
    ctx: dict[str, float | None] = {
        "mdd_ratio": None,
        "sector_mdd": None,
    }
    if not state.extracted or not state.extracted.market:
        return ctx
    stock = state.extracted.market.stock
    if period == "1Y":
        mdd_sv = stock.mdd_ratio_1y
        smdd_sv = stock.sector_mdd_1y
    else:
        mdd_sv = stock.mdd_ratio_5y
        smdd_sv = stock.sector_mdd_5y
    ctx["mdd_ratio"] = mdd_sv.value if mdd_sv is not None else None
    ctx["sector_mdd"] = smdd_sv.value if smdd_sv is not None else None
    return ctx


@null_safe_chart
def create_drawdown_chart(
    state: AnalysisState,
    period: str = "1Y",
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a drawdown analysis chart.

    Shows the running drawdown from peak for the company and sector ETF,
    with maximum drawdown annotated.

    Args:
        state: Complete analysis state with market data.
        period: Chart period ("1Y" or "5Y").
        ds: Design system for styling (reserved).
        colors: Optional color palette dict.
        format: Output format -- "png" returns BytesIO, "svg" returns str.

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    # Resolve colors from chart style registry.
    if format == "svg":
        c = resolve_colors("drawdown", "svg")
    else:
        c = colors if colors is not None else resolve_colors("drawdown", format)

    data = extract_chart_data(state, period)
    if data is None:
        return None

    # Compute drawdown series.
    company_dd = compute_drawdown_series(data.prices)
    if not company_dd or len(company_dd) < 5:
        return None

    # Align drawdown series length to dates.
    min_len = min(len(data.dates), len(company_dd))
    chart_dates = data.dates[:min_len]
    company_dd = company_dd[:min_len]

    etf_dd: list[float] | None = None
    if data.etf_prices and len(data.etf_prices) >= 5:
        etf_dd = compute_drawdown_series(data.etf_prices)

    # Compute stats.
    stats = _compute_dd_stats(company_dd, chart_dates)

    # Enrich stats with MDD ratio and sector MDD from state.
    mdd_ctx = _get_mdd_context(state, period)
    stats["mdd_ratio"] = mdd_ctx["mdd_ratio"]
    stats["sector_mdd"] = mdd_ctx["sector_mdd"]

    matplotlib.use("Agg")
    plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 4), dpi=200, facecolor=c["bg"],
    )

    try:
        # Stats header (top 12%).
        ax_header: Any = fig.add_axes([0.05, 0.86, 0.9, 0.12])
        _render_dd_header(ax_header, stats, data.ticker, period, c)

        # Main drawdown chart.
        ax: Any = fig.add_axes([0.08, 0.12, 0.86, 0.70])
        ax.set_facecolor(c["bg"])

        # Company drawdown area fill (red gradient).
        ax.fill_between(
            chart_dates, company_dd, 0,
            color=c.get("price_down", "#B91C1C"),
            alpha=0.25,
            label=data.ticker,
        )
        ax.plot(
            chart_dates, company_dd,
            color=c.get("price_down", "#B91C1C"),
            linewidth=1.2,
            label="_nolegend_",
        )

        # Sector ETF drawdown (dashed gold).
        if etf_dd and data.etf_dates:
            etf_len = min(len(data.etf_dates), len(etf_dd))
            ax.fill_between(
                data.etf_dates[:etf_len], etf_dd[:etf_len], 0,
                color=c.get("grid", "#E5E7EB"),
                alpha=0.15,
                label="_nolegend_",
            )
            ax.plot(
                data.etf_dates[:etf_len], etf_dd[:etf_len],
                linestyle="--",
                color=c.get("etf_line", "#D4A843"),
                linewidth=1.0,
                label=data.etf_ticker or "Sector ETF",
            )

        # Annotate maximum drawdown.
        _annotate_max_dd(ax, chart_dates, company_dd, c)

        # Zero line.
        ax.axhline(y=0, color=c.get("text_muted", "#6B7280"), linewidth=0.5, linestyle="-")

        # Styling.
        _apply_dd_style(ax, period, c)

        # Legend.
        ax.legend(
            loc="lower left", fontsize=7,
            framealpha=0.8, facecolor=c["bg"],
            edgecolor=c.get("grid", "#E5E7EB"),
            labelcolor=c.get("text", "#1F2937"),
        )

        _ = ds  # Reserved for future extensions.
        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


# ---------------------------------------------------------------------------
# Stats header
# ---------------------------------------------------------------------------


def _compute_dd_stats(
    dd_series: list[float],
    dates: list[datetime],
) -> dict[str, Any]:
    """Compute drawdown statistics for the header."""
    stats: dict[str, Any] = {}

    if not dd_series:
        return stats

    stats["max_dd"] = min(dd_series)
    stats["avg_dd"] = sum(dd_series) / len(dd_series)
    stats["current_dd"] = dd_series[-1]

    # Find max drawdown location and duration.
    max_dd_idx = dd_series.index(stats["max_dd"])
    stats["max_dd_date"] = dates[max_dd_idx] if max_dd_idx < len(dates) else None

    # Count days in drawdown (any dd < -1%).
    dd_days = sum(1 for d in dd_series if d < -1.0)
    stats["dd_days"] = dd_days

    # Recovery days: from max DD to next 0% (or end of series).
    recovery_days = 0
    if max_dd_idx < len(dd_series) - 1:
        for i in range(max_dd_idx + 1, len(dd_series)):
            recovery_days += 1
            if dd_series[i] >= -0.5:  # Close enough to recovered.
                break
    stats["recovery_days"] = recovery_days

    # Duration of max DD episode: find start of the DD that leads to max.
    dd_start_idx = max_dd_idx
    for i in range(max_dd_idx - 1, -1, -1):
        if dd_series[i] >= -0.5:
            dd_start_idx = i + 1
            break
    stats["dd_duration"] = max_dd_idx - dd_start_idx

    return stats


def _render_dd_header(
    ax_header: Any,
    stats: dict[str, Any],
    ticker: str,
    period: str,
    c: dict[str, str],
) -> None:
    """Render drawdown stats in a header bar."""
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")
    # Draw filled rectangle as background (set_facecolor unreliable with overlapping axes).
    from matplotlib.patches import Rectangle
    bg_rect = Rectangle((0, 0), 1, 1, transform=ax_header.transAxes,
                         facecolor=c.get("header_bg", "#0B1D3A"), edgecolor="none",
                         zorder=0, clip_on=False)
    ax_header.add_patch(bg_rect)

    # Title.
    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax_header.text(
        0.02, 0.5, f"{ticker} Peak-to-Trough Drawdown ({period_label})",
        fontsize=9, fontweight="bold",
        color=c.get("header_text", "#FFFFFF"),
        va="center",
    )

    # Stat items.
    items: list[tuple[str, str, str]] = []
    white = c.get("header_text", "#FFFFFF")
    red = c.get("price_down", "#B91C1C")

    max_dd = stats.get("max_dd")
    if isinstance(max_dd, (int, float)):
        items.append(("Max DD", f"{max_dd:.1f}%", red))
    else:
        items.append(("Max DD", "N/A", white))

    avg_dd = stats.get("avg_dd")
    if isinstance(avg_dd, (int, float)):
        items.append(("Avg DD", f"{avg_dd:.1f}%", white))
    else:
        items.append(("Avg DD", "N/A", white))

    current_dd = stats.get("current_dd")
    if isinstance(current_dd, (int, float)):
        clr = red if current_dd < -5.0 else white
        items.append(("Current", f"{current_dd:.1f}%", clr))
    else:
        items.append(("Current", "N/A", white))

    recovery = stats.get("recovery_days")
    if isinstance(recovery, int):
        items.append(("Recovery", f"{recovery}d", white))
    else:
        items.append(("Recovery", "N/A", white))

    dd_days = stats.get("dd_days")
    if isinstance(dd_days, int):
        items.append(("DD Days", str(dd_days), white))
    else:
        items.append(("DD Days", "N/A", white))

    # Sector MDD for context.
    sector_mdd = stats.get("sector_mdd")
    if isinstance(sector_mdd, (int, float)):
        items.append(("Sector DD", f"{sector_mdd:.1f}%", white))

    # MDD ratio: company MDD / sector MDD.
    mdd_ratio = stats.get("mdd_ratio")
    if isinstance(mdd_ratio, (int, float)):
        ratio_color = red if mdd_ratio > 1.5 else white
        items.append(("MDD Ratio", f"{mdd_ratio:.1f}x", ratio_color))

    x_start = 0.30
    x_step = 0.10

    for i, (label, value, color) in enumerate(items):
        x = x_start + i * x_step
        ax_header.text(
            x, 0.72, label,
            fontsize=6, color=c.get("text_muted", "#6B7280"),
            va="center",
        )
        ax_header.text(
            x, 0.28, value,
            fontsize=9, fontweight="bold", color=color,
            va="center",
        )


# ---------------------------------------------------------------------------
# Max drawdown annotation
# ---------------------------------------------------------------------------


def _annotate_max_dd(
    ax: Any,
    dates: list[datetime],
    dd_series: list[float],
    c: dict[str, str],
) -> None:
    """Annotate the maximum drawdown point with an arrow and label."""
    if not dd_series:
        return

    max_dd = min(dd_series)
    if max_dd >= -0.5:
        return  # No meaningful drawdown to annotate.

    max_dd_idx = dd_series.index(max_dd)
    if max_dd_idx >= len(dates):
        return

    # Find start of this drawdown episode (last time near 0).
    dd_start_idx = max_dd_idx
    for i in range(max_dd_idx - 1, -1, -1):
        if dd_series[i] >= -0.5:
            dd_start_idx = i
            break

    max_dd_date = dates[max_dd_idx]
    dd_start_date = dates[dd_start_idx]

    red = c.get("price_down", "#B91C1C")

    # Horizontal arrow from start to trough.
    if dd_start_idx != max_dd_idx:
        ax.annotate(
            "",
            xy=(max_dd_date, max_dd),
            xytext=(dd_start_date, max_dd),
            arrowprops={
                "arrowstyle": "->",
                "color": red,
                "linewidth": 1.5,
                "linestyle": "--",
            },
        )

    # Label at the trough.
    ax.annotate(
        f"Max: {max_dd:.1f}%",
        xy=(max_dd_date, max_dd),
        xytext=(8, -12),
        textcoords="offset points",
        fontsize=7, fontweight="bold",
        color=red,
        ha="left",
    )


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------


def _apply_dd_style(
    ax: Any, period: str, c: dict[str, str],
) -> None:
    """Apply professional styling to the drawdown chart."""
    ax.tick_params(colors=c.get("text", "#1F2937"), labelsize=7)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(c.get("grid", "#E5E7EB"))
        ax.spines[spine].set_linewidth(0.5)

    ax.grid(
        visible=True, alpha=0.3,
        color=c.get("grid", "#E5E7EB"), linewidth=0.5,
    )

    ax.set_ylabel(
        "Drawdown %", color=c.get("text", "#1F2937"), fontsize=9,
    )

    # Date formatting.
    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.tick_params(axis="x", rotation=0)


__all__ = ["create_drawdown_chart"]
