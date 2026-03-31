"""Volume bars, earnings markers, and beta stats for stock charts.

Split from stock_charts.py to keep both files under 500 lines.
These functions render optional overlays that depend on ChartData
fields added by the enhanced data layer (volumes, earnings_events,
company_beta, sector_beta).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from do_uw.stages.render.charts.stock_chart_data import ChartData, index_to_base


# ---------------------------------------------------------------------------
# Volume subplot
# ---------------------------------------------------------------------------


def render_volume_bars(
    ax_vol: Any,
    data: ChartData,
    c: dict[str, str],
) -> None:
    """Render volume bars on the dedicated volume subplot.

    Gray bars by default; RED bars when volume > 2x its 20-day moving average.
    Gracefully skips if ChartData has no volumes field or it is empty.
    """
    volumes: list[float] | None = getattr(data, "volumes", None)
    if not volumes or len(volumes) < 2:
        # No volume data -- hide the axes entirely.
        ax_vol.set_visible(False)
        return

    dates = data.dates
    min_len = min(len(dates), len(volumes))
    dates_v = dates[:min_len]
    vols = volumes[:min_len]

    # Compute 20-day simple moving average for spike detection.
    window = 20
    ma: list[float] = []
    for i in range(min_len):
        start = max(0, i - window + 1)
        chunk = vols[start : i + 1]
        ma.append(sum(chunk) / len(chunk))

    # Classify bars: spike if > 2x 20-day average.
    # Threshold sourced from STOCK.PRICE.chart_comparison display.chart_thresholds volume_spike.red=2.0
    normal_color = c.get("volume_normal", "#555555")
    spike_color = c.get("volume_spike", "#FF1744")

    colors: list[str] = []
    alphas: list[float] = []
    for i, v in enumerate(vols):
        if ma[i] > 0 and v > 2.0 * ma[i]:
            colors.append(spike_color)
            alphas.append(0.9)
        else:
            colors.append(normal_color)
            alphas.append(0.6)

    # Scale to millions for display.
    vols_m = [v / 1_000_000.0 for v in vols]

    # Matplotlib bar() doesn't support per-bar alpha, so draw in two passes.
    normal_dates = [d for d, a in zip(dates_v, alphas) if a < 0.8]
    normal_vols = [v for v, a in zip(vols_m, alphas) if a < 0.8]
    spike_dates = [d for d, a in zip(dates_v, alphas) if a >= 0.8]
    spike_vols = [v for v, a in zip(vols_m, alphas) if a >= 0.8]

    bar_width = 1.0 if data.period == "1Y" else 5.0

    if normal_dates:
        ax_vol.bar(
            normal_dates, normal_vols,
            width=bar_width, color=normal_color, alpha=0.6,
            linewidth=0, label="_nolegend_",
        )
    if spike_dates:
        ax_vol.bar(
            spike_dates, spike_vols,
            width=bar_width, color=spike_color, alpha=0.9,
            linewidth=0, label="_nolegend_",
        )

    # Style the volume subplot.
    ax_vol.set_ylabel("Vol (M)", color=c.get("text_muted", "#888"), fontsize=6)
    ax_vol.tick_params(labelsize=6, colors=c.get("text", "#ccc"))
    ax_vol.set_xlim(ax_vol.get_xlim())  # Sync with main chart x range.

    # Minimal gridlines (2-3).
    max_vol = max(vols_m) if vols_m else 1.0
    ax_vol.set_ylim(0, max_vol * 1.15)
    ax_vol.yaxis.set_major_locator(
        _MaxNLocator(nbins=3, integer=False)
    )
    ax_vol.grid(visible=True, alpha=0.15, color=c.get("grid", "#333"), linewidth=0.5)

    # Spines.
    for spine in ax_vol.spines.values():
        spine.set_color(c.get("grid", "#333"))
        spine.set_linewidth(0.5)

    ax_vol.set_facecolor(c.get("bg", "#1B1B1D"))


def _MaxNLocator(nbins: int = 3, integer: bool = False) -> Any:
    """Lazy import MaxNLocator to avoid top-level matplotlib import."""
    from matplotlib.ticker import MaxNLocator
    return MaxNLocator(nbins=nbins, integer=integer)


# ---------------------------------------------------------------------------
# Earnings date markers
# ---------------------------------------------------------------------------


def render_earnings_markers(
    ax: Any,
    data: ChartData,
    c: dict[str, str],
) -> None:
    """Draw vertical dashed lines at earnings dates on the main chart.

    Each line has a small ``E`` label at the top colored by surprise direction.
    Gracefully skips if ChartData has no earnings_events field or it is empty.
    """
    events: list[dict[str, Any]] | None = getattr(data, "earnings_events", None)
    if not events:
        return

    if not data.dates:
        return

    chart_start = data.dates[0]
    chart_end = data.dates[-1]
    y_min, y_max = ax.get_ylim()

    line_color = c.get("earnings_line", "#666666")
    pos_color = c.get("earnings_text_pos", "#00C853")
    neg_color = c.get("earnings_text_neg", "#FF1744")
    neutral_color = c.get("earnings_text_neutral", "#888888")

    for event in events:
        date_val = event.get("date")
        if date_val is None:
            continue

        # Parse date if string.
        if isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val[:10])
            except (ValueError, TypeError):
                continue
        elif isinstance(date_val, datetime):
            dt = date_val
        else:
            continue

        # Skip if outside chart range.
        if dt < chart_start or dt > chart_end:
            continue

        # Draw the vertical dashed line.
        ax.axvline(
            x=dt, color=line_color, linestyle="--",
            linewidth=0.5, alpha=0.6, zorder=1,
        )

        # Determine 'E' label color based on earnings surprise.
        surprise = event.get("surprise_pct")
        if isinstance(surprise, (int, float)):
            if surprise > 0:
                text_color = pos_color
            elif surprise < 0:
                text_color = neg_color
            else:
                text_color = neutral_color
        else:
            text_color = neutral_color

        # Place 'E' at the top of the chart area.
        ax.text(
            dt, y_max * 0.98, "E",
            fontsize=8, fontweight="bold", color=text_color,
            ha="center", va="top", zorder=6,
        )


# ---------------------------------------------------------------------------
# Litigation filing date markers
# ---------------------------------------------------------------------------


def render_litigation_markers(
    ax: Any,
    data: ChartData,
    c: dict[str, str],
) -> None:
    """Draw vertical dash-dot lines at litigation filing dates.

    Each line has a small 'L' label at the top and an abbreviated case name
    below it. Uses orange color to distinguish from earnings (gray dashed)
    and drop markers (red/yellow dots).

    Gracefully skips if ChartData has no litigation_events or it is empty.
    """
    events: list[dict[str, Any]] | None = getattr(data, "litigation_events", None)
    if not events:
        return

    if not data.dates:
        return

    chart_start = data.dates[0]
    chart_end = data.dates[-1]
    y_min, y_max = ax.get_ylim()

    line_color = c.get("litigation_line", "#FF6D00")
    text_color = c.get("litigation_text", "#FF6D00")

    for event in events:
        date_val = event.get("date")
        if date_val is None:
            continue

        # Parse date if string.
        if isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val[:10])
            except (ValueError, TypeError):
                continue
        elif isinstance(date_val, datetime):
            dt = date_val
        else:
            continue

        # Skip if outside chart range.
        if dt < chart_start or dt > chart_end:
            continue

        # Draw the vertical dash-dot line.
        ax.axvline(
            x=dt, color=line_color, linestyle="-.",
            linewidth=0.7, alpha=0.7, zorder=1,
        )

        # Place 'L' at the top of the chart area.
        ax.text(
            dt, y_max * 0.98, "L",
            fontsize=7, fontweight="bold", color=text_color,
            ha="center", va="top", zorder=6,
        )

        # Abbreviated case name below "L".
        case_name = event.get("case_name", "")
        if case_name:
            label = case_name[:12] + "..." if len(case_name) > 12 else case_name
            ax.text(
                dt, y_max * 0.93, label,
                fontsize=5.5, color=text_color,
                ha="center", va="top", zorder=6,
                alpha=0.85,
            )


# ---------------------------------------------------------------------------
# Beta ratio stat for header
# ---------------------------------------------------------------------------


def compute_beta_ratio(data: ChartData) -> tuple[float | None, str]:
    """Compute company_beta / sector_beta ratio.

    Returns:
        (ratio_value, color_key) where color_key is one of:
        "header_text" (normal), "price_down" (red, >1.5), "drop_yellow" (amber, >1.2)
    """
    company_beta: float | None = getattr(data, "company_beta", None)
    sector_beta: float | None = getattr(data, "sector_beta", None)

    if company_beta is None or sector_beta is None:
        return None, "header_text"
    if sector_beta == 0:
        return None, "header_text"

    # Thresholds sourced from STOCK.PRICE.beta_ratio_elevated evaluation.thresholds
    # red=1.5 (overlay severity), yellow=1.2 (overlay caution)
    ratio = company_beta / sector_beta
    if ratio > 1.5:
        return round(ratio, 2), "price_down"
    if ratio > 1.2:
        return round(ratio, 2), "drop_yellow"
    return round(ratio, 2), "header_text"


# ---------------------------------------------------------------------------
# Divergence bands (moved from stock_charts.py)
# ---------------------------------------------------------------------------

# Divergence band threshold in indexed points.
# Threshold sourced from STOCK.PRICE.chart_comparison evaluation.thresholds yellow=10.0
_DIVERGENCE_THRESHOLD = 10.0


def render_divergence_bands(ax2: Any, data: ChartData, c: dict[str, str]) -> None:
    """Shade the gap between company and sector when >10% divergence."""
    if not data.etf_dates or not data.etf_prices:
        return

    # Index both series to 100 for comparison on the right axis.
    company_indexed = index_to_base(data.prices, 100.0)
    etf_indexed = index_to_base(data.etf_prices, 100.0)

    # Build aligned series using company dates (most common axis).
    min_len = min(len(company_indexed), len(etf_indexed))
    if min_len < 2:
        return

    c_idx = company_indexed[:min_len]
    e_idx = etf_indexed[:min_len]
    dates_aligned = data.dates[:min_len]

    divergence = [abs(cv - ev) for cv, ev in zip(c_idx, e_idx)]
    where_div = [d > _DIVERGENCE_THRESHOLD for d in divergence]

    if any(where_div):
        ax2.fill_between(
            dates_aligned, c_idx, e_idx,
            where=where_div,
            color=c["divergence_alpha"],
            alpha=0.08, label="_nolegend_",
            zorder=1,
        )


# ---------------------------------------------------------------------------
# Drop markers (moved from stock_charts.py)
# ---------------------------------------------------------------------------


def render_drop_markers(ax: Any, data: ChartData, c: dict[str, str]) -> None:
    """Plot drop markers with trigger context and company-specific distinction.

    - Company-specific drops: filled circles (prominent)
    - Market-wide drops: hollow diamonds (de-emphasized)
    - Labels include trigger context (8-K, earnings) when available
    """
    for drop in data.drops:
        if not drop.date or not drop.drop_pct:
            continue

        pct = drop.drop_pct.value
        drop_date = _parse_overlay_date(drop.date.value)
        if drop_date is None:
            continue

        # Find y-position on the company price line.
        y_pos = _find_y_at_date(data.dates, data.prices, drop_date)
        if y_pos is None:
            continue

        is_market = drop.is_market_wide
        is_specific = drop.is_company_specific

        # Severity determines color and size.
        # Threshold sourced from STOCK.PRICE.chart_comparison display.chart_thresholds drop_severity.red=-10.0
        if pct <= -10.0:
            color = c["drop_red"]
            size = 8 if is_specific else 6
        else:
            color = c["drop_yellow"]
            size = 6 if is_specific else 5

        # Company-specific: filled circle. Market-wide: hollow diamond.
        if is_market:
            ax.plot(
                drop_date, y_pos,
                "D", color=color, markersize=size,
                markerfacecolor="none", markeredgewidth=1.2,
                zorder=5,
            )
        else:
            ax.plot(
                drop_date, y_pos,
                "o", color=color, markersize=size, zorder=5,
            )

        # Build annotation label with trigger context.
        label = f"{pct:+.1f}%"
        trigger_tag = _short_trigger_tag(drop)
        if trigger_tag:
            label = f"{label}\n{trigger_tag}"

        ax.annotate(
            label,
            (drop_date, y_pos),
            textcoords="offset points",
            xytext=(0, -14),
            fontsize=5.0, color=color,
            ha="center", va="top", zorder=5,
            linespacing=0.85,
        )


def _short_trigger_tag(drop: Any) -> str:
    """Return a short trigger tag for drop marker annotations.

    Maps raw trigger_event values to concise display labels.
    """
    if not drop.trigger_event:
        if drop.is_market_wide:
            return "mkt"
        return ""
    raw = str(drop.trigger_event.value).lower()
    if "8-k" in raw or "8k" in raw:
        return "8-K"
    if "earning" in raw:
        return "earn"
    if "guidance" in raw:
        return "guid"
    if "restate" in raw:
        return "restate"
    if "sec" in raw or "enforce" in raw:
        return "SEC"
    if drop.is_market_wide:
        return "mkt"
    # Generic non-empty trigger — abbreviate
    return raw[:6] if len(raw) > 6 else raw


def _parse_overlay_date(date_str: str) -> datetime | None:
    """Parse a single date string to datetime."""
    try:
        return datetime.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _find_y_at_date(
    dates: list[datetime],
    prices: list[float],
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

    return prices[best_idx] if best_idx < len(prices) else None


# ---------------------------------------------------------------------------
# Class period shading
# ---------------------------------------------------------------------------


def render_class_period_shading(
    ax: Any,
    data: ChartData,
    c: dict[str, str],
) -> None:
    """Shade SCA class period ranges on the stock chart.

    Draws a translucent red vertical band for each active SCA class period,
    making it immediately obvious where the litigation exposure window falls
    relative to stock price movements. This is the single most important
    visual cue for a D&O underwriter reviewing the chart.

    Gracefully skips if ChartData has no class_periods or it is empty.
    """
    periods: list[dict[str, Any]] | None = getattr(data, "class_periods", None)
    if not periods:
        return

    if not data.dates:
        return

    shade_color = c.get("class_period_shade", "#FF1744")
    label_color = c.get("class_period_label", "#991B1B")
    y_min, y_max = ax.get_ylim()

    for i, period in enumerate(periods):
        start = period.get("start")
        end = period.get("end")
        case_name = period.get("case_name", "SCA")
        if not start or not end:
            continue

        # Translucent red band — prominent but doesn't obscure price data.
        ax.axvspan(
            start, end,
            color=shade_color, alpha=0.08,
            zorder=0,
            label="_nolegend_" if i > 0 else "Class Period",
        )

        # Dashed boundary lines at period start and end.
        for dt in (start, end):
            ax.axvline(
                x=dt, color=shade_color, linestyle=":",
                linewidth=0.6, alpha=0.5, zorder=1,
            )

        # Label at top of shading region.
        mid = start + (end - start) / 2
        ax.text(
            mid, y_max * 0.99,
            f"CLASS PERIOD",
            fontsize=5.5, fontweight="bold", color=label_color,
            ha="center", va="top", zorder=6,
            alpha=0.8,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.7, edgecolor="none"),
        )


__all__ = [
    "compute_beta_ratio",
    "render_class_period_shading",
    "render_divergence_bands",
    "render_drop_markers",
    "render_earnings_markers",
    "render_litigation_markers",
    "render_volume_bars",
]
