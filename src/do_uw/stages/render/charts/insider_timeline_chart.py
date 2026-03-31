"""Insider trading timeline chart for D&O scienter analysis.

Creates a timeline visualization showing:
- Insider sale transactions plotted over the stock price
- Cluster events highlighted with shaded windows
- 10b5-1 vs discretionary sales distinguished visually
- Suspicious timing (pre-event) sales called out

This chart answers the key D&O underwriting question:
"Did insiders sell before bad news hit?"
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.patches import Rectangle

from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.charts.stock_chart_data import extract_chart_data
from do_uw.stages.render.chart_style_registry import resolve_colors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_insider_timeline_chart(
    state: AnalysisState,
    period: str = "1Y",
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create insider trading timeline overlaid on stock price.

    Shows when insiders sold relative to stock movements — the visual
    that tells an underwriter whether scienter risk exists.

    Args:
        state: Complete analysis state with insider and market data.
        period: "1Y" or "5Y".
        format: "png" or "svg".

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    c = resolve_colors("stock", format)
    data = extract_chart_data(state, period)
    if data is None:
        return None

    # Get insider transactions
    insider_txns = _extract_insider_transactions(state)
    if not insider_txns:
        return None

    # Get cluster events
    cluster_events = _extract_cluster_events(state)

    matplotlib.use("Agg")
    if c.get("bg", "").startswith("#0"):
        plt.style.use("dark_background")  # pyright: ignore[reportUnknownMemberType]
    else:
        plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(12, 5), dpi=200, facecolor=c["bg"],
    )

    try:
        # Header
        ax_header: Any = fig.add_axes([0.04, 0.90, 0.92, 0.08])
        _render_header(ax_header, state, insider_txns, c, period)

        # Main chart: price + insider markers
        ax: Any = fig.add_axes([0.07, 0.12, 0.87, 0.74])
        _render_insider_timeline(ax, data, insider_txns, cluster_events, c)

        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


def build_insider_timeline_data(state: AnalysisState) -> list[dict[str, Any]]:
    """Build structured data for the HTML insider analysis detail table.

    Returns transaction data enriched with context for template rendering.
    """
    txns = _extract_insider_transactions(state)
    result: list[dict[str, Any]] = []

    for t in txns:
        is_sell = t.get("type", "").upper() in ("SELL", "SALE", "S")
        result.append({
            "date": t.get("date", ""),
            "name": t.get("name", "Unknown"),
            "title": t.get("title", ""),
            "type": "SELL" if is_sell else t.get("type", ""),
            "shares": t.get("shares", 0),
            "value": t.get("value", 0),
            "value_fmt": _fmt_value(t.get("value", 0)),
            "is_10b5_1": t.get("is_10b5_1", False),
            "is_sell": is_sell,
            "is_c_suite": _is_c_suite(t.get("title", "")),
        })

    return result


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def _render_header(
    ax: Any, state: AnalysisState,
    txns: list[dict[str, Any]], c: dict[str, str],
    period: str,
) -> None:
    """Render stats header for insider timeline."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    bg = Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=c.get("header_bg", "#0B1D3A"),
        edgecolor="none", zorder=0, clip_on=False,
    )
    ax.add_patch(bg)

    ticker = state.ticker or (
        state.company.identity.ticker
        if state.company and state.company.identity
        else "?"
    )
    period_label = "12 Months" if period == "1Y" else "5 Years"
    white = c.get("header_text", "#FFFFFF")
    red = c.get("price_down", "#EF4444")
    green = "#22C55E"
    muted = c.get("text_muted", "#9CA3AF")

    ax.text(
        0.02, 0.5,
        f"{ticker} — Insider Trading Timeline ({period_label})",
        fontsize=9, fontweight="bold", color=white, va="center",
    )

    # Stats
    sells = [t for t in txns if t.get("type", "").upper() in ("SELL", "SALE", "S")]
    buys = [t for t in txns if t.get("type", "").upper() in ("BUY", "PURCHASE", "P")]
    sell_val = sum(float(t.get("value", 0) or 0) for t in sells)
    buy_val = sum(float(t.get("value", 0) or 0) for t in buys)
    c_suite_sells = sum(1 for t in sells if _is_c_suite(t.get("title", "")))

    items = [
        ("Sales", str(len(sells)), red if sells else white),
        ("Purchases", str(len(buys)), green if buys else white),
        ("Net Sold", _fmt_value(sell_val - buy_val), red if sell_val > buy_val else green),
        ("C-Suite Sales", str(c_suite_sells), red if c_suite_sells else white),
    ]

    x = 0.50
    for label, val, col in items:
        ax.text(x, 0.72, label, fontsize=5.5, color=muted, va="center")
        ax.text(x, 0.28, val, fontsize=8, fontweight="bold", color=col, va="center")
        x += 0.13


# ---------------------------------------------------------------------------
# Main timeline
# ---------------------------------------------------------------------------


def _render_insider_timeline(
    ax: Any, data: Any, txns: list[dict[str, Any]],
    clusters: list[dict[str, Any]], c: dict[str, str],
) -> None:
    """Render stock price with insider transaction markers."""
    ax.set_facecolor(c["bg"])

    # Price line (subtle, as context)
    ax.plot(
        data.dates, data.prices,
        color=c.get("price_up", "#22C55E"), linewidth=1.2, alpha=0.4,
        label="Price", zorder=2,
    )
    ax.fill_between(data.dates, data.prices, alpha=0.05,
                     color=c.get("price_up", "#22C55E"), zorder=1)

    # Cluster event shading
    for cl in clusters:
        start = _parse_date(cl.get("start", ""))
        end = _parse_date(cl.get("end", ""))
        if start and end:
            ax.axvspan(
                start, end,
                facecolor="#DC2626", alpha=0.08, zorder=1,
                label="Cluster Window" if cl == clusters[0] else None,
            )

    # Plot transactions on the price line
    for t in txns:
        t_date = _parse_date(t.get("date", ""))
        if t_date is None:
            continue

        y_pos = _find_y(data.dates, data.prices, t_date)
        if y_pos is None:
            continue

        is_sell = t.get("type", "").upper() in ("SELL", "SALE", "S")
        is_buy = t.get("type", "").upper() in ("BUY", "PURCHASE", "P")
        is_10b5_1 = t.get("is_10b5_1", False)
        is_csuite = _is_c_suite(t.get("title", ""))
        val = float(t.get("value", 0) or 0)

        # Marker styling
        if is_sell:
            color = "#DC2626" if not is_10b5_1 else "#F59E0B"
            marker = "v"  # Down triangle for sales
            size = 8 if val > 1_000_000 else 6 if val > 100_000 else 4
            if is_csuite:
                size += 3  # C-suite sales larger
        elif is_buy:
            color = "#22C55E"
            marker = "^"  # Up triangle for purchases
            size = 7
        else:
            color = "#6B7280"
            marker = "o"
            size = 4

        ax.plot(
            t_date, y_pos, marker,
            color=color, markersize=size,
            markeredgecolor="white", markeredgewidth=0.5,
            alpha=0.85, zorder=5,
        )

        # Name label for large or C-suite transactions
        if is_csuite or val > 5_000_000:
            name = t.get("name", "")
            short_name = name.split(",")[0].split(" ")[-1] if name else ""
            ax.annotate(
                f"{short_name}\n{_fmt_value(val)}",
                (t_date, y_pos),
                textcoords="offset points",
                xytext=(5, -12 if is_sell else 12),
                fontsize=4.5, color=color,
                ha="left", va="top" if is_sell else "bottom",
                zorder=6,
            )

    # Styling
    ax.set_ylabel("Price ($)", color=c.get("text", "#E5E7EB"), fontsize=7)
    ax.tick_params(colors=c.get("text", "#E5E7EB"), labelsize=6, length=3)

    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("bottom", "left"):
        ax.spines[sp].set_color(c.get("grid", "#374151"))
        ax.spines[sp].set_linewidth(0.5)

    ax.grid(visible=True, alpha=0.15, color=c.get("grid", "#374151"), linewidth=0.5)

    period = data.period
    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Legend
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], marker="v", color="w", markerfacecolor="#DC2626",
               markersize=6, label="Discretionary Sale", linestyle="None"),
        Line2D([0], [0], marker="v", color="w", markerfacecolor="#F59E0B",
               markersize=6, label="10b5-1 Plan Sale", linestyle="None"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#22C55E",
               markersize=6, label="Purchase", linestyle="None"),
    ]
    ax.legend(
        handles=legend_items, loc="upper right", fontsize=5.5,
        framealpha=0.7, edgecolor="none",
        facecolor=c.get("bg", "#111827"),
        labelcolor=c.get("text", "#E5E7EB"),
    )


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------


def _extract_insider_transactions(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract insider transactions from state."""
    # Try extracted insider analysis first
    if state.extracted and state.extracted.market:
        analysis = state.extracted.market.insider_analysis
        if analysis and hasattr(analysis, "transactions"):
            txns_raw = analysis.transactions or []
            result: list[dict[str, Any]] = []
            for t in txns_raw:
                name = t.insider_name.value if t.insider_name else "Unknown"
                title = t.title.value if t.title else ""
                date = t.transaction_date.value if t.transaction_date else ""
                ttype = t.transaction_type or ""
                shares = t.shares.value if t.shares else 0
                value = t.total_value.value if t.total_value else 0
                is_10b5 = t.is_10b5_1 if t.is_10b5_1 is not None else False

                result.append({
                    "date": str(date)[:10],
                    "name": str(name),
                    "title": str(title),
                    "type": str(ttype),
                    "shares": shares,
                    "value": float(value) if value else 0,
                    "is_10b5_1": bool(is_10b5),
                })
            return result

    # Fallback to raw market data
    if state.acquired_data and state.acquired_data.market_data:
        raw = state.acquired_data.market_data.get("insider_transactions", {})
        if isinstance(raw, dict) and "Insider" in raw:
            indices = raw.get("index", [])
            result_raw: list[dict[str, Any]] = []
            for idx in indices:
                result_raw.append({
                    "date": str(raw.get("Start Date", {}).get(str(idx), ""))[:10],
                    "name": str(raw.get("Insider", {}).get(str(idx), "Unknown")),
                    "title": str(raw.get("Position", {}).get(str(idx), "")),
                    "type": str(raw.get("Transaction", {}).get(str(idx), "")),
                    "shares": raw.get("Shares", {}).get(str(idx), 0),
                    "value": float(raw.get("Value", {}).get(str(idx), 0) or 0),
                    "is_10b5_1": False,
                })
            return result_raw

    return []


def _extract_cluster_events(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract cluster selling events from state."""
    if state.extracted and state.extracted.market:
        analysis = state.extracted.market.insider_analysis
        if analysis and hasattr(analysis, "cluster_events"):
            clusters = analysis.cluster_events or []
            result: list[dict[str, Any]] = []
            for cl in clusters:
                result.append({
                    "start": str(cl.start_date) if cl.start_date else "",
                    "end": str(cl.end_date) if cl.end_date else "",
                    "count": cl.insider_count if cl.insider_count else 0,
                    "insiders": cl.insiders or [],
                    "total_value": cl.total_value or 0,
                })
            return result
    return []


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _parse_date(date_str: str) -> datetime | None:
    """Parse date string."""
    if not date_str:
        return None
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


def _fmt_value(val: float) -> str:
    """Format dollar value."""
    if not val or val == 0:
        return "$0"
    if abs(val) >= 1_000_000_000:
        return f"${val / 1_000_000_000:.1f}B"
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def _is_c_suite(title: str) -> bool:
    """Check if title indicates C-suite executive."""
    if not title:
        return False
    t = title.upper()
    return any(x in t for x in (
        "CEO", "CFO", "COO", "CTO", "CHIEF", "PRESIDENT",
        "EXECUTIVE VICE", "EVP", "GENERAL COUNSEL",
    ))


__all__ = [
    "create_insider_timeline_chart",
    "build_insider_timeline_data",
]
