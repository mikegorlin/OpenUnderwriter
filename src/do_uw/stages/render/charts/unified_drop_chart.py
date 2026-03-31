"""Unified stock drop investigative chart.

Creates a single full-width chart combining:
- Price line with sector ETF overlay (context for market vs company moves)
- Numbered circles at each significant drop event
- Company-specific drops in RED, market-wide in GRAY
- Volume subplot beneath

The catalyst legend table is rendered in HTML template, NOT in matplotlib.
This chart generates the visual + returns structured drop data for the legend.

This is the PRIMARY stock drop view for D&O underwriters — tells the story
of what happened, when, and whether it was the company's fault.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.patches import FancyBboxPatch, Rectangle

from do_uw.models.market_events import StockDropEvent
from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.charts.stock_chart_data import (
    ChartData,
    extract_chart_data,
    index_to_base,
)
from do_uw.stages.render.charts.stock_chart_overlays import render_volume_bars
from do_uw.stages.render.chart_style_registry import resolve_colors

# Trigger category colors — shared with drop_analysis_chart.py
_CATEGORY_COLORS: dict[str, str] = {
    "earnings_miss": "#B91C1C",
    "guidance_cut": "#D97706",
    "restatement": "#7C3AED",
    "management_departure": "#2563EB",
    "litigation": "#DC2626",
    "regulatory": "#9333EA",
    "analyst_downgrade": "#EA580C",
    "acquisition": "#0891B2",
    "market_wide": "#6B7280",
    "unknown": "#374151",
    "other_event": "#4B5563",
    "agreement": "#0D9488",
    "restructuring": "#7C3AED",
    "material_impairment": "#DC2626",
    "": "#374151",
}

_CATEGORY_LABELS: dict[str, str] = {
    "earnings_miss": "Earnings",
    "guidance_cut": "Guidance",
    "restatement": "Restatement",
    "management_departure": "Exec Change",
    "litigation": "Litigation",
    "regulatory": "Regulatory",
    "analyst_downgrade": "Downgrade",
    "acquisition": "Deal",
    "market_wide": "Market-Wide",
    "unknown": "—",
    "other_event": "Filing",
    "agreement": "Agreement",
    "restructuring": "Restructuring",
    "material_impairment": "Impairment",
    "delisting": "Delisting",
    "": "—",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_unified_drop_chart(
    state: AnalysisState,
    period: str = "1Y",
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create unified stock drop chart with numbered events and sector overlay.

    This is the PRIMARY drop visualization for D&O underwriters.
    Full-width, tells the complete story.

    Args:
        state: Complete analysis state with market and drop data.
        period: "1Y" or "5Y".
        format: "png" or "svg".

    Returns:
        PNG BytesIO, SVG string, or None if insufficient data.
    """
    c = resolve_colors("stock", format)
    # Use 2Y data for drop charts — gives the full picture
    chart_period = "2Y" if period == "1Y" else period
    data = extract_chart_data(state, chart_period)
    if data is None:
        # Fallback to requested period if 2Y not available
        data = extract_chart_data(state, period)
    if data is None:
        return None

    # Filter drops to the chart's actual date range
    chart_start = data.dates[0] if data.dates else None
    chart_end = data.dates[-1] if data.dates else None
    filtered_drops = [
        d for d in data.drops
        if d.date and chart_start and chart_end
        and chart_start <= _parse_date(d.date.value[:10]) <= chart_end  # type: ignore[arg-type]
    ] if chart_start else data.drops

    # Use same clustering as legend table so numbers match
    deduped = _deduplicate_drops(_sort_drops(filtered_drops))
    # Gap proportional to chart period: 2Y=21d, 5Y=30d, 1Y=10d
    gap = {"1Y": 14, "2Y": 30, "5Y": 45}.get(data.period, 30)
    clusters = _cluster_drops(deduped, max_gap_days=gap)
    # For chart markers, use the worst drop from each cluster
    chart_drops = [min(cl, key=lambda d: d.drop_pct.value if d.drop_pct else 0)
                   for cl in clusters]

    matplotlib.use("Agg")
    if c.get("bg", "").startswith("#0"):
        plt.style.use("dark_background")  # pyright: ignore[reportUnknownMemberType]
    else:
        plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(14, 3.5), dpi=200, facecolor=c["bg"],
    )

    try:
        # No internal header — the card wrapper provides the header.
        # Full chart area with sector overlay + numbered drops.
        has_volume = bool(getattr(data, "volumes", None))
        main_bottom = 0.14 if has_volume else 0.06
        main_height = 0.82 if has_volume else 0.90
        ax: Any = fig.add_axes([0.06, main_bottom, 0.88, main_height])
        _render_main_chart(ax, data, chart_drops, c, clusters=clusters)

        # Volume subplot — compact (if data available).
        if has_volume:
            ax_vol: Any = fig.add_axes([0.06, 0.04, 0.88, 0.07], sharex=ax)
            render_volume_bars(ax_vol, data, c)
            ax.tick_params(axis="x", labelbottom=False)

        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


def build_drop_legend_data(
    state: AnalysisState,
    period: str = "1Y",
) -> list[dict[str, Any]]:
    """Build structured data for the HTML catalyst legend table.

    Steps:
    1. Deduplicate drops by date (keeps worst per date)
    2. Cluster consecutive drops within 5 calendar days into single events
    3. Generate intelligent context for unexplained drops
    4. Strip yfinance garbage from all text fields

    Returns a list of dicts, one per cluster/event.
    """
    # Use 2Y data when 1Y is requested — gives the full picture
    chart_period = "2Y" if period == "1Y" else period
    data = extract_chart_data(state, chart_period)
    if data is None:
        data = extract_chart_data(state, period)  # Fallback
    if data is None:
        return []

    # Filter drops to chart date range
    chart_start = data.dates[0] if data.dates else None
    chart_end = data.dates[-1] if data.dates else None
    all_drops = data.drops
    if chart_start and chart_end:
        all_drops = [
            d for d in all_drops
            if d.date and _parse_date(d.date.value[:10])
            and chart_start <= _parse_date(d.date.value[:10]) <= chart_end  # type: ignore[arg-type]
        ]

    drops = _sort_drops(all_drops)
    if not drops:
        return []

    # Step 1: Deduplicate same-date drops
    drops = _deduplicate_drops(drops)

    # Step 2: Cluster — gap proportional to chart period
    gap = {"1Y": 14, "2Y": 30, "5Y": 45}.get(data.period, 30)
    clusters = _cluster_drops(drops, max_gap_days=gap)

    # Step 2.5: Detect blanket descriptions — same text on ALL drops = not date-specific
    all_descs = [str(d.trigger_description or "")[:60] for d in drops if d.trigger_description]
    if all_descs:
        from collections import Counter
        desc_counts = Counter(all_descs)
        most_common_desc, most_common_count = desc_counts.most_common(1)[0]
        # If >70% of drops have the same description, it's a blanket — clear it
        if most_common_count > len(all_descs) * 0.7 and most_common_desc:
            for d in drops:
                if str(d.trigger_description or "")[:60] == most_common_desc:
                    d.trigger_description = None  # Force intelligent context generation

    # Step 2.7: Build event timeline for catalyst matching
    event_timeline = _build_event_timeline(state)

    # Step 3: Build legend entries from clusters
    ticker = state.ticker or "Company"
    legend: list[dict[str, Any]] = []
    for i, cluster in enumerate(clusters, 1):
        entry = _build_cluster_entry(i, cluster, ticker, event_timeline)
        legend.append(entry)

    # LLM synthesis for unexplained drops — fills in what pipeline missed
    try:
        from do_uw.stages.render.charts.drop_catalyst_synthesizer import (
            synthesize_drop_catalysts,
        )
        legend = synthesize_drop_catalysts(state, legend)
    except Exception:
        logger.debug("Drop catalyst synthesis skipped", exc_info=True)

    return legend


def _cluster_drops(
    drops: list[StockDropEvent],
    max_gap_days: int = 5,
    max_cluster_days: int = 60,
) -> list[list[StockDropEvent]]:
    """Group consecutive drops within max_gap_days into clusters.

    A cluster is a sequence of drops where each drop is within
    max_gap_days of the previous one AND the total cluster span
    doesn't exceed max_cluster_days.

    This prevents a stock in sustained decline from having its
    entire year-long slide merged into a single event.
    """
    if not drops:
        return []

    clusters: list[list[StockDropEvent]] = []
    current: list[StockDropEvent] = [drops[0]]

    for drop in drops[1:]:
        prev_date = _parse_date(current[-1].date.value) if current[-1].date else None
        curr_date = _parse_date(drop.date.value) if drop.date else None
        cluster_start = _parse_date(current[0].date.value) if current[0].date else None

        if prev_date and curr_date and cluster_start:
            gap = (curr_date - prev_date).days
            span = (curr_date - cluster_start).days
            if gap <= max_gap_days and span <= max_cluster_days:
                current.append(drop)
                continue

        # Gap too large or cluster too long — start new cluster
        clusters.append(current)
        current = [drop]

    clusters.append(current)
    return clusters


def _build_cluster_entry(
    number: int, cluster: list[StockDropEvent], ticker: str,
    event_timeline: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a single legend entry from a cluster of drops."""
    # Use the worst drop in the cluster for magnitude
    worst = min(cluster, key=lambda d: d.drop_pct.value if d.drop_pct else 0)

    # Date range
    first_date = cluster[0].date.value[:10] if cluster[0].date else "?"
    last_date = cluster[-1].date.value[:10] if cluster[-1].date else first_date
    is_multi = len(cluster) > 1

    if is_multi:
        date_display = f"{first_date} – {last_date}"
        # Calculate total cumulative decline
        total_pct = worst.drop_pct.value if worst.drop_pct else 0
        drop_display = f"{total_pct:+.1f}%"
        days = (_parse_date(last_date) - _parse_date(first_date)).days + 1 if _parse_date(first_date) and _parse_date(last_date) else len(cluster)
    else:
        date_display = first_date
        total_pct = worst.drop_pct.value if worst.drop_pct else 0
        drop_display = f"{total_pct:+.1f}%"
        days = 1

    # Category: use best attribution from any drop in the cluster
    cat = "unknown"
    best_trigger = ""
    for d in cluster:
        d_cat = d.trigger_category or "unknown"
        if d_cat != "unknown":
            cat = d_cat
            best_trigger = _clean_trigger(d)
            break

    # If still unexplained, try all drops for any trigger
    if cat == "unknown":
        for d in cluster:
            t = _clean_trigger(d)
            if t and t != "Unexplained":
                best_trigger = t
                break

    # If category still unknown, infer from trigger_event field
    if cat == "unknown":
        for d in cluster:
            if d.trigger_event:
                evt = str(d.trigger_event.value if hasattr(d.trigger_event, 'value') else d.trigger_event).lower()
                if "earnings" in evt:
                    cat = "earnings_miss"
                    if not best_trigger:
                        best_trigger = "Earnings Event"
                    break
                if "8-k" in evt or "8k" in evt:
                    cat = "other_event"
                    if not best_trigger:
                        best_trigger = "8-K Filing"
                    break

    # Always try event timeline for richer context (earnings surprise %, 8-K item detail)
    if event_timeline:
        matched = _match_cluster_to_events(cluster, event_timeline)
        if matched:
            best_trigger = matched["desc"]
            if cat == "unknown":
                if "earnings" in matched["type"].lower():
                    cat = "earnings_miss"  # Earnings event (beat or miss)
                elif "8-k" in matched["type"].lower():
                    cat = "other_event"

    cat_label = _CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())

    # Is company-specific? Use worst drop's classification
    is_company_specific = bool(worst.is_company_specific)

    # Per-event color palette for visual matching between chart and legend
    _EVENT_PALETTE = [
        "#F43F5E", "#8B5CF6", "#3B82F6", "#10B981", "#F59E0B",
        "#EC4899", "#6366F1", "#14B8A6", "#EF4444", "#A855F7",
        "#0EA5E9", "#22C55E", "#D97706", "#E11D48", "#7C3AED",
        "#06B6D4", "#84CC16", "#F97316",
    ]
    cat_color = _EVENT_PALETTE[(number - 1) % len(_EVENT_PALETTE)] if is_company_specific else "#6B7280"

    # Sector return — use worst drop's sector data
    sector_pct_raw = worst.sector_return_pct.value if worst.sector_return_pct else None
    sector_pct = f"{sector_pct_raw:+.1f}%" if sector_pct_raw is not None else "—"

    # Recovery
    recovery = "—"
    if worst.recovery_days is not None:
        recovery = f"{worst.recovery_days}d" if worst.recovery_days > 0 else "Not recovered"

    # Build intelligent context instead of useless "Unexplained"
    trigger = best_trigger or "Unexplained"
    context = _build_intelligent_context(
        cluster, trigger, cat, is_company_specific, sector_pct_raw,
        total_pct, days, ticker, is_multi,
    )

    return {
        "number": number,
        "date": date_display,
        "drop_pct": drop_display,
        "drop_pct_raw": total_pct,
        "category": cat,
        "category_label": cat_label,
        "category_color": cat_color,
        "is_company_specific": is_company_specific,
        "is_cluster": is_multi,
        "cluster_days": days,
        "cluster_count": len(cluster),
        "trigger": trigger if trigger != "Unexplained" else context,
        "recovery": recovery,
        "sector_pct": sector_pct,
        "abnormal_return": f"{worst.abnormal_return_pct:+.1f}%" if worst.abnormal_return_pct else "—",
        "do_assessment": "",  # Removed useless parrot text
    }


def _build_intelligent_context(
    cluster: list[StockDropEvent],
    trigger: str,
    cat: str,
    is_company_specific: bool,
    sector_pct: float | None,
    total_pct: float,
    days: int,
    ticker: str,
    is_multi: bool,
) -> str:
    """Generate useful context even when catalyst is unknown.

    Instead of "Unexplained", provide:
    - Whether it's company-specific or sector-driven (with sector comparison)
    - Magnitude context (how severe relative to norms)
    - Duration context for multi-day slides
    - Any partial attribution from the data
    """
    if trigger and trigger != "Unexplained":
        return trigger

    parts: list[str] = []

    # Multi-day slide context
    if is_multi and days > 1:
        parts.append(f"{days}-day sustained decline ({len(cluster)} trading sessions)")

    # Company vs sector context
    if sector_pct is not None:
        diff = total_pct - sector_pct  # both negative, diff shows excess
        if abs(sector_pct) > 3.0 and abs(diff) < 3.0:
            # Sector also fell significantly — mostly sector-driven
            parts.append(f"Broad sector sell-off (sector {sector_pct:+.1f}%)")
        elif abs(diff) > 5.0:
            parts.append(f"Company-specific decline ({total_pct - sector_pct:+.1f}% vs sector)")
        elif abs(sector_pct) > 1.0:
            parts.append(f"Mixed market/company move (sector {sector_pct:+.1f}%)")

    # Magnitude context
    if total_pct <= -20:
        parts.append("Severe decline — likely SCA trigger event")
    elif total_pct <= -10:
        parts.append("Material decline — elevated D&O exposure")
    elif total_pct <= -5:
        parts.append("Moderate decline")

    # Check for 8-K items even if not attributed
    for d in cluster:
        if d.trigger_8k_items:
            items = d.trigger_8k_items
            item_labels = _format_8k_items(items)
            if item_labels:
                parts.append(f"8-K filed: {item_labels}")
                break

    if parts:
        return ". ".join(parts)

    return "No catalyst identified in available data"


def _format_8k_items(items: list[str]) -> str:
    """Convert 8-K item numbers to readable labels."""
    _ITEM_MAP = {
        "1.01": "Material Agreement",
        "1.02": "Termination of Agreement",
        "2.01": "Asset Acquisition/Disposition",
        "2.02": "Financial Results",
        "2.04": "Mine Safety",
        "2.05": "Costs for Exit",
        "2.06": "Asset Impairment",
        "3.01": "Delisting/Transfer",
        "3.02": "Unregistered Sales",
        "3.03": "Bylaw Amendment",
        "4.01": "Auditor Change",
        "4.02": "Non-Reliance on Financials",
        "5.02": "Officer Departure/Appointment",
        "5.03": "Charter Amendment",
        "7.01": "Regulation FD Disclosure",
        "8.01": "Other Events",
        "9.01": "Financial Statements/Exhibits",
    }
    labels = []
    for item in items:
        label = _ITEM_MAP.get(item, f"Item {item}")
        if label not in ("Other Events", "Financial Statements/Exhibits"):
            labels.append(label)
    return ", ".join(labels) if labels else ""


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def _render_header(
    ax: Any, drops: list[StockDropEvent], ticker: str,
    period: str, c: dict[str, str], data: ChartData,
) -> None:
    """Stats header bar."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    bg = Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=c.get("header_bg", "#0B1D3A"),
        edgecolor="none", zorder=0, clip_on=False,
    )
    ax.add_patch(bg)

    _PERIOD_LABELS = {"1Y": "12 Months", "2Y": "2 Years", "5Y": "5 Years"}
    period_label = _PERIOD_LABELS.get(data.period, data.period)
    title = f"{ticker} — Stock Drop Events ({period_label})"
    if data.etf_ticker:
        title += f"  vs  {data.etf_ticker}"

    white = c.get("header_text", "#FFFFFF")
    red = c.get("price_down", "#EF4444")
    muted = c.get("text_muted", "#9CA3AF")

    ax.text(0.02, 0.5, title, fontsize=9, fontweight="bold", color=white, va="center")

    # Stats on right side
    total = len(drops)
    company_specific = sum(1 for d in drops if d.is_company_specific)
    worst = min((d.drop_pct.value for d in drops if d.drop_pct), default=0.0)

    items = [
        ("Events", str(total), white),
        ("Company-Specific", str(company_specific), red if company_specific else white),
        ("Worst", f"{worst:.1f}%", red),
    ]

    x = 0.58
    for label, val, col in items:
        ax.text(x, 0.72, label, fontsize=5.5, color=muted, va="center")
        ax.text(x, 0.28, val, fontsize=8, fontweight="bold", color=col, va="center")
        x += 0.14


# ---------------------------------------------------------------------------
# Main chart
# ---------------------------------------------------------------------------


def _render_main_chart(
    ax: Any, data: ChartData, drops: list[StockDropEvent],
    c: dict[str, str],
    clusters: list[list[StockDropEvent]] | None = None,
) -> None:
    """Price line with sector overlay, numbered drop markers, and cluster spans."""
    ax.set_facecolor(c["bg"])

    # Company price line — Slate Modern: sky blue
    price_color = "#38BDF8"  # Slate Modern sky blue
    ax.plot(
        data.dates, data.prices,
        color=price_color, linewidth=1.5, alpha=0.9,
        label=data.ticker, zorder=3,
    )

    # Fill under price line with subtle gradient
    ax.fill_between(
        data.dates, data.prices, alpha=0.06,
        color=price_color, zorder=2,
    )

    # Sector ETF overlay on RIGHT axis (indexed to 100)
    ax2: Any = ax.twinx()
    if data.etf_dates and data.etf_prices and len(data.etf_prices) >= 2:
        indexed_etf = index_to_base(data.etf_prices, 100.0)
        ax2.plot(
            data.etf_dates, indexed_etf,
            color="#F59E0B", linewidth=1.0, alpha=0.6,
            linestyle="--", label=data.etf_ticker, zorder=2,
        )
        ax2.set_ylabel(
            f"{data.etf_ticker} (indexed)", color="#F59E0B",
            fontsize=7, alpha=0.6,
        )
        ax2.tick_params(axis="y", colors="#F59E0B", labelsize=6, length=3)
        for sp in ax2.spines.values():
            sp.set_visible(False)

    # Draw cluster spans — shaded zones showing the decline period
    if clusters:
        for i, cluster in enumerate(clusters):
            if len(cluster) < 2:
                continue  # Single drops don't need span
            first_date = _parse_date(cluster[0].date.value) if cluster[0].date else None
            last_date = _parse_date(cluster[-1].date.value) if cluster[-1].date else None
            if first_date and last_date:
                ax.axvspan(
                    first_date, last_date,
                    facecolor="#DC2626", alpha=0.06, zorder=1,
                )

    # Build set of cluster sizes to determine marker shape
    _cluster_sizes: dict[int, int] = {}
    if clusters:
        for i, cl in enumerate(clusters):
            _cluster_sizes[i] = len(cl)

    # Drop event numbered markers
    for i, drop in enumerate(drops, 1):
        if not drop.drop_pct or not drop.date:
            continue

        drop_date = _parse_date(drop.date.value)
        if drop_date is None:
            continue

        y_pos = _find_y(data.dates, data.prices, drop_date)
        if y_pos is None:
            continue

        pct = drop.drop_pct.value
        cat = drop.trigger_category or "unknown"
        is_company = drop.is_company_specific
        is_cluster = _cluster_sizes.get(i - 1, 1) > 1

        # Color: distinct per event for visual matching to legend
        _EVENT_PALETTE = [
            "#F43F5E", "#8B5CF6", "#3B82F6", "#10B981", "#F59E0B",
            "#EC4899", "#6366F1", "#14B8A6", "#EF4444", "#A855F7",
            "#0EA5E9", "#22C55E", "#D97706", "#E11D48", "#7C3AED",
            "#06B6D4", "#84CC16", "#F97316",
        ]
        if is_company:
            marker_color = _EVENT_PALETTE[(i - 1) % len(_EVENT_PALETTE)]
        else:
            marker_color = "#6B7280"  # Gray for sector-wide

        # Size by severity
        if pct <= -15.0:
            marker_size = 14
        elif pct <= -10.0:
            marker_size = 11
        else:
            marker_size = 8

        # Shape: SQUARE for cluster (period) drops, CIRCLE for single-day
        marker_shape = "s" if is_cluster else "o"

        # Draw numbered marker
        ax.plot(
            drop_date, y_pos, marker_shape,
            color=marker_color, markersize=marker_size,
            markeredgecolor="white", markeredgewidth=0.8,
            alpha=0.9, zorder=6,
        )

        # Number label inside circle
        ax.annotate(
            str(i),
            (drop_date, y_pos),
            fontsize=5.5 if i < 10 else 4.5,
            fontweight="bold",
            color="white",
            ha="center", va="center",
            zorder=7,
        )

        # Drop % label below
        ax.annotate(
            f"{pct:+.1f}%",
            (drop_date, y_pos),
            textcoords="offset points",
            xytext=(0, -(marker_size + 4)),
            fontsize=5, fontweight="bold",
            color=marker_color,
            ha="center", va="top",
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

    # Date formatting
    period = data.period
    if period == "1Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    elif period == "2Y":
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Legend
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles1 or handles2:
        ax.legend(
            handles1 + handles2, labels1 + labels2,
            loc="upper left", fontsize=6,
            framealpha=0.7, edgecolor="none",
            facecolor=c.get("bg", "#111827"),
            labelcolor=c.get("text", "#E5E7EB"),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sort_drops(drops: list[StockDropEvent]) -> list[StockDropEvent]:
    """Sort drops chronologically."""
    def _date_key(d: StockDropEvent) -> str:
        return d.date.value[:10] if d.date else ""
    return sorted(drops, key=_date_key)


def _deduplicate_drops(drops: list[StockDropEvent]) -> list[StockDropEvent]:
    """Keep only the worst drop per date.

    When single-day and multi-day drops overlap on the same start date,
    the multi-day (larger magnitude) wins. This prevents showing
    e.g. -12% and -15% for the same Jan 27 event.
    """
    by_date: dict[str, StockDropEvent] = {}
    for d in drops:
        if not d.date or not d.drop_pct:
            continue
        key = d.date.value[:10]
        if key not in by_date:
            by_date[key] = d
        else:
            existing = by_date[key]
            # Keep the worse drop (more negative)
            if d.drop_pct.value < (existing.drop_pct.value if existing.drop_pct else 0):
                by_date[key] = d
    return sorted(by_date.values(), key=lambda d: d.date.value[:10] if d.date else "")


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string."""
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


def _clean_trigger(drop: StockDropEvent) -> str:
    """Extract clean trigger description, stripping yfinance garbage."""
    _GARBAGE_PATTERNS = (
        "Find the latest", "Get the latest", "stock quote",
        "vital information", "make the best investing",
        "finance.yahoo.com", "Yahoo Finance",
        "is a trending ticker", "stock news and he",
        "News From Dow Jones", "stock outperforms",
        "stock underperforms", "stock falls", "stock rises",
        "stock closes", "Dow Jones Newswires",
        "Barron's Online", "MarketWatch",
        "real-time stock price", "stock market data",
    )

    def _unwrap(val: Any) -> str:
        """Unwrap SourcedValue or any object to a clean string."""
        if val is None:
            return ""
        if hasattr(val, "value"):
            return str(val.value)
        return str(val)

    if drop.trigger_description:
        td = _unwrap(drop.trigger_description)
        if any(p.lower() in td.lower() for p in _GARBAGE_PATTERNS):
            # Garbage description — use event or category
            if drop.trigger_event:
                evt = _humanize_trigger(_unwrap(drop.trigger_event))
                if not any(p.lower() in evt.lower() for p in _GARBAGE_PATTERNS):
                    return evt
            cat = drop.trigger_category or "unknown"
            return _CATEGORY_LABELS.get(cat, "Unexplained")
        return td

    if drop.trigger_event:
        evt = _humanize_trigger(_unwrap(drop.trigger_event))
        if any(p.lower() in evt.lower() for p in _GARBAGE_PATTERNS):
            cat = drop.trigger_category or "unknown"
            return _CATEGORY_LABELS.get(cat, "Unexplained")
        return evt

    cat = drop.trigger_category or "unknown"
    return _CATEGORY_LABELS.get(cat, "Unexplained")


def _strip_garbage_from_text(text: str) -> str:
    """Strip yfinance boilerplate from any text field (D&O assessment, triggers)."""
    import re
    # Remove "News From Dow Jones" and everything after it in the same sentence
    text = re.sub(
        r"News From Dow Jones\s*;.*?(?:\.|$)", "", text, flags=re.IGNORECASE,
    ).strip()
    # Remove common yfinance boilerplate fragments
    for pattern in (
        r"Find the latest.*?(?:\.|$)",
        r"Get the latest.*?(?:\.|$)",
        r"stock quote.*?(?:\.|$)",
        r"stock news and.*?(?:\.|$)",
        r"stock outperforms.*?(?:\.|$)",
        r"stock underperforms.*?(?:\.|$)",
        r"vital information.*?(?:\.|$)",
        r"make the best investing.*?(?:\.|$)",
        r"finance\.yahoo\.com.*?(?:\.|$)",
        r"Yahoo Finance.*?(?:\.|$)",
        r"real-time stock.*?(?:\.|$)",
        r"at \d+:\d+ [ap]\.m\. ET\s*;?",
        r"MarketWatch.*?(?:\.|$)",
        r"Barron's Online.*?(?:\.|$)",
    ):
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    # Remove date-prefixed news headlines that leaked from yfinance
    # Pattern: "Mon. DD, YYYY text" that isn't the drop description itself
    text = re.sub(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.\s+\d{1,2},\s+20\d{2}\s+.*",
        "", text, flags=re.IGNORECASE,
    ).strip()
    # Remove "Veritone" and similar leaked company names from news
    text = re.sub(r"Veritone\s+.*", "", text, flags=re.IGNORECASE).strip()
    # Clean up multiple spaces/periods
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"^\s*[;,]\s*", "", text)
    return text.strip()


def _build_event_timeline(state: AnalysisState) -> list[dict[str, Any]]:
    """Build a timeline of known events (8-K filings, earnings dates) for catalyst matching."""
    events: list[dict[str, Any]] = []

    # 8-K filings — handles both Pydantic models and dicts
    if state.extracted and state.extracted.market:
        eight_k = state.extracted.market.eight_k_items
        if eight_k:
            item_map = {
                "1.01": "Material Agreement", "2.02": "Financial Results",
                "4.01": "Auditor Change", "4.02": "Non-Reliance on Financials",
                "5.02": "Officer Departure", "5.07": "Shareholder Vote",
                "7.01": "Reg FD Disclosure", "8.01": "Other Events",
            }
            filings = getattr(eight_k, "filings", None) or []
            if not filings and isinstance(eight_k, dict):
                filings = eight_k.get("filings", [])
            for f in filings:
                date = str(getattr(f, "filing_date", "") or (f.get("filing_date", "") if isinstance(f, dict) else ""))[:10]
                items = getattr(f, "items", None) or (f.get("items", []) if isinstance(f, dict) else [])
                desc = ", ".join(
                    item_map.get(i, f"Item {i}") for i in (items or [])
                    if i not in ("9.01",) and i in item_map
                )
                if date and desc:
                    events.append({"date": date, "type": "8-K", "desc": f"8-K: {desc}"})

    # Earnings dates with surprise %
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        ed = md.get("earnings_dates", {})
        if isinstance(ed, dict):
            dates = ed.get("Earnings Date", [])
            surprises = ed.get("Surprise(%)", [])
            reported = ed.get("Reported EPS", [])
            for i, d in enumerate(dates):
                s = surprises[i] if isinstance(surprises, list) and i < len(surprises) else None
                eps = reported[i] if isinstance(reported, list) and i < len(reported) else None
                parts = ["Earnings"]
                if s is not None:
                    try:
                        s_val = float(s)
                        parts.append(f"{'beat' if s_val > 0 else 'miss'} {s_val:+.1f}%")
                    except (ValueError, TypeError):
                        pass
                if eps is not None:
                    try:
                        parts.append(f"EPS ${float(eps):.2f}")
                    except (ValueError, TypeError):
                        pass
                events.append({
                    "date": str(d)[:10],
                    "type": "Earnings",
                    "desc": " ".join(parts),
                })

    events.sort(key=lambda e: e["date"])
    return events


def _match_cluster_to_events(
    cluster: list[StockDropEvent],
    events: list[dict[str, Any]],
    window_days: int = 7,
) -> dict[str, Any] | None:
    """Find the closest known event within window_days of a cluster's drops."""
    if not events:
        return None

    # Get cluster date range
    cluster_dates = [_parse_date(d.date.value) for d in cluster if d.date]
    cluster_dates = [d for d in cluster_dates if d is not None]
    if not cluster_dates:
        return None

    cluster_start = min(cluster_dates)
    cluster_end = max(cluster_dates)

    # Search for events within window of any cluster date
    best_match: dict[str, Any] | None = None
    best_gap = window_days + 1

    for event in events:
        event_date = _parse_date(event["date"])
        if event_date is None:
            continue

        # Check if event is within window of cluster range
        gap_start = abs((event_date - cluster_start).days)
        gap_end = abs((event_date - cluster_end).days)
        # Also check if event falls WITHIN the cluster range
        in_range = cluster_start <= event_date <= cluster_end
        gap = 0 if in_range else min(gap_start, gap_end)

        if gap <= window_days and gap < best_gap:
            best_gap = gap
            best_match = event

    return best_match


def _humanize_trigger(raw: str) -> str:
    """Clean up internal trigger event codes for display."""
    _TRIGGER_MAP: dict[str, str] = {
        "8-K_filing": "8-K Filing",
        "8-k_filing": "8-K Filing",
        "earnings_announcement": "Earnings Announcement",
        "guidance_update": "Guidance Update",
    }
    if raw in _TRIGGER_MAP:
        return _TRIGGER_MAP[raw]
    # Generic cleanup: underscores → spaces, title case
    return raw.replace("_", " ").title()


__all__ = [
    "create_unified_drop_chart",
    "build_drop_legend_data",
]
