"""Relative performance chart for D&O underwriting worksheets.

Creates a clean indexed performance comparison chart:
- Company, sector ETF, and S&P 500 all indexed to 100
- Green/red fill where company outperforms/underperforms sector
- Earnings dates as vertical dashed lines
- Drop events as red triangles
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
from do_uw.stages.render.charts.stock_chart_data import (
    extract_chart_data,
    index_to_base,
)
from do_uw.stages.render.chart_style_registry import resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_relative_performance_chart(
    state: AnalysisState,
    period: str = "1Y",
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a relative performance chart with all series indexed to 100.

    Shows company vs sector vs S&P 500 on a single scale, with
    green/red fill for over/underperformance and earnings markers.

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
        c = resolve_colors("relative_performance", "svg")
    else:
        c = colors if colors is not None else resolve_colors("relative_performance", format)

    data = extract_chart_data(state, period)
    if data is None:
        return None

    # Index all series to 100.
    company_idx = index_to_base(data.prices, 100.0)
    if not company_idx or len(company_idx) < 5:
        return None

    etf_idx: list[float] | None = None
    if data.etf_prices and len(data.etf_prices) >= 5:
        etf_idx = index_to_base(data.etf_prices, 100.0)

    spy_idx: list[float] | None = None
    if data.spy_prices and len(data.spy_prices) >= 5:
        spy_idx = index_to_base(data.spy_prices, 100.0)

    # Compute stats for header.
    stats = _compute_rel_stats(data, company_idx, etf_idx)

    matplotlib.use("Agg")
    plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 5), dpi=200, facecolor=c["bg"],
    )

    try:
        # Stats header (top 10%).
        ax_header: Any = fig.add_axes([0.05, 0.88, 0.9, 0.10])
        _render_rel_header(ax_header, stats, data.ticker, period, c)

        # Main chart.
        ax: Any = fig.add_axes([0.08, 0.10, 0.86, 0.74])
        ax.set_facecolor(c["bg"])

        navy = c.get("header_bg", "#0B1D3A")
        gold = c.get("etf_line", "#D4A843")
        gray = c.get("text_muted", "#6B7280")
        green = c.get("price_up", "#16A34A")
        red = c.get("price_down", "#B91C1C")

        # Green/red fill between company and sector.
        if etf_idx and data.etf_dates:
            min_len = min(len(data.dates), len(company_idx), len(data.etf_dates), len(etf_idx))
            fill_dates = data.dates[:min_len]
            fill_company = company_idx[:min_len]
            fill_etf = etf_idx[:min_len]

            where_above = [fill_company[i] >= fill_etf[i] for i in range(min_len)]
            where_below = [fill_company[i] < fill_etf[i] for i in range(min_len)]

            ax.fill_between(
                fill_dates, fill_company, fill_etf,
                where=where_above,
                color=green, alpha=0.10,
                interpolate=True,
                label="_nolegend_",
            )
            ax.fill_between(
                fill_dates, fill_company, fill_etf,
                where=where_below,
                color=red, alpha=0.10,
                interpolate=True,
                label="_nolegend_",
            )

        # Company line (solid navy, 2px).
        min_len_c = min(len(data.dates), len(company_idx))
        ax.plot(
            data.dates[:min_len_c], company_idx[:min_len_c],
            color=navy, linewidth=2.0,
            label=data.ticker, zorder=3,
        )

        # Sector ETF line (dashed gold, 1.5px).
        if etf_idx and data.etf_dates:
            etf_len = min(len(data.etf_dates), len(etf_idx))
            ax.plot(
                data.etf_dates[:etf_len], etf_idx[:etf_len],
                linestyle="--", color=gold, linewidth=1.5,
                label=data.etf_ticker or "Sector ETF", zorder=2,
            )

        # S&P 500 line (dotted gray, 1px).
        if spy_idx and data.spy_dates:
            spy_len = min(len(data.spy_dates), len(spy_idx))
            ax.plot(
                data.spy_dates[:spy_len], spy_idx[:spy_len],
                linestyle=":", color=gray, linewidth=1.0,
                label="S&P 500", zorder=2,
            )

        # Base 100 reference line.
        ax.axhline(y=100, color=gray, linewidth=0.5, linestyle="-", alpha=0.5)

        # Earnings dates as vertical dashed lines.
        for earning in data.earnings_events:
            e_date = earning.get("date")
            if isinstance(e_date, datetime):
                ax.axvline(
                    x=e_date, color=gray, linewidth=0.5,
                    linestyle="--", alpha=0.4, zorder=1,
                )
                # Small "E" label at top.
                ax.text(
                    e_date, ax.get_ylim()[1] * 0.98, "E",
                    fontsize=5, color=gray, ha="center", va="top",
                    alpha=0.6,
                )

        # Drop events as red triangles.
        for drop in data.drops:
            if not drop.date or not drop.drop_pct:
                continue
            drop_date = _parse_single_date(drop.date.value)
            if drop_date is None:
                continue
            # Find indexed price at drop date.
            y_pos = _find_y_at_date(data.dates, company_idx, drop_date)
            if y_pos is None:
                continue
            ax.plot(
                drop_date, y_pos,
                "v", color=red, markersize=6, zorder=5,
            )

        # Styling.
        ax.set_ylabel(
            "Indexed Performance (100 = Start)",
            color=c.get("text", "#1F2937"), fontsize=9,
        )

        ax.legend(
            loc="upper left", fontsize=7,
            framealpha=0.8, facecolor=c["bg"],
            edgecolor=c.get("grid", "#E5E7EB"),
            labelcolor=c.get("text", "#1F2937"),
        )

        _apply_rel_style(ax, period, c)

        _ = ds
        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def _compute_rel_stats(
    data: Any,
    company_idx: list[float],
    etf_idx: list[float] | None,
) -> dict[str, Any]:
    """Compute relative performance stats for the header."""
    stats: dict[str, Any] = {}

    # Company return.
    if company_idx and len(company_idx) >= 2:
        stats["company_return"] = company_idx[-1] - 100.0
    else:
        stats["company_return"] = None

    # Sector return.
    if etf_idx and len(etf_idx) >= 2:
        stats["sector_return"] = etf_idx[-1] - 100.0
    else:
        stats["sector_return"] = None

    # Alpha = company - sector.
    cr = stats.get("company_return")
    sr = stats.get("sector_return")
    if isinstance(cr, (int, float)) and isinstance(sr, (int, float)):
        stats["alpha"] = cr - sr
    else:
        stats["alpha"] = None

    # Beta ratio (company beta / sector beta).
    cb = data.company_beta
    sb = data.sector_beta
    if isinstance(cb, (int, float)) and isinstance(sb, (int, float)) and sb > 0:
        stats["beta_ratio"] = cb / sb
    else:
        stats["beta_ratio"] = None

    # Vol ratio.
    cv = data.company_vol_90d
    sv = data.sector_vol_90d
    if isinstance(cv, (int, float)) and isinstance(sv, (int, float)) and sv > 0:
        stats["vol_ratio"] = cv / sv
    else:
        stats["vol_ratio"] = None

    return stats


def _render_rel_header(
    ax_header: Any,
    stats: dict[str, Any],
    ticker: str,
    period: str,
    c: dict[str, str],
) -> None:
    """Render relative performance stats in a header bar."""
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")
    from matplotlib.patches import Rectangle
    bg_rect = Rectangle((0, 0), 1, 1, transform=ax_header.transAxes,
                         facecolor=c.get("header_bg", "#0B1D3A"), edgecolor="none",
                         zorder=0, clip_on=False)
    ax_header.add_patch(bg_rect)

    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax_header.text(
        0.02, 0.5, f"{ticker} Relative Performance ({period_label})",
        fontsize=9, fontweight="bold",
        color=c.get("header_text", "#FFFFFF"),
        va="center",
    )

    items: list[tuple[str, str, str]] = []
    white = c.get("header_text", "#FFFFFF")
    green = c.get("price_up", "#16A34A")
    red = c.get("price_down", "#B91C1C")

    cr = stats.get("company_return")
    if isinstance(cr, (int, float)):
        clr = green if cr >= 0 else red
        items.append(("Return", f"{cr:+.1f}%", clr))
    else:
        items.append(("Return", "N/A", white))

    sr = stats.get("sector_return")
    if isinstance(sr, (int, float)):
        clr = green if sr >= 0 else red
        items.append(("Sector", f"{sr:+.1f}%", clr))
    else:
        items.append(("Sector", "N/A", white))

    alpha = stats.get("alpha")
    if isinstance(alpha, (int, float)):
        clr = green if alpha >= 0 else red
        items.append(("Alpha", f"{alpha:+.1f}%", clr))
    else:
        items.append(("Alpha", "N/A", white))

    br = stats.get("beta_ratio")
    if isinstance(br, (int, float)):
        clr = red if br > 1.5 else white
        items.append(("Beta Ratio", f"{br:.2f}x", clr))
    else:
        items.append(("Beta Ratio", "N/A", white))

    vr = stats.get("vol_ratio")
    if isinstance(vr, (int, float)):
        clr = red if vr > 1.5 else white
        items.append(("Vol Ratio", f"{vr:.2f}x", clr))
    else:
        items.append(("Vol Ratio", "N/A", white))

    x_start = 0.28
    x_step = 0.14

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
# Styling
# ---------------------------------------------------------------------------


def _apply_rel_style(
    ax: Any, period: str, c: dict[str, str],
) -> None:
    """Apply professional styling to the relative performance chart."""
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

    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.tick_params(axis="x", rotation=0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_single_date(date_str: str) -> datetime | None:
    """Parse a single date string to datetime."""
    try:
        return datetime.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _find_y_at_date(
    dates: list[datetime],
    values: list[float],
    target: datetime,
) -> float | None:
    """Find the y-value at or nearest to a given date."""
    if not dates:
        return None

    best_idx = 0
    best_diff = abs((dates[0] - target).total_seconds())
    for i, d in enumerate(dates[1:], 1):
        diff = abs((d - target).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_idx = i

    return values[best_idx] if best_idx < len(values) else None


__all__ = ["create_relative_performance_chart"]
