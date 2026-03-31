"""Volatility analysis chart for D&O underwriting worksheets.

Creates a two-subplot volatility chart:
- Top (60%): Rolling 30-day annualized volatility comparison with
  color-coded background zones (green <20%, amber 20-40%, red >40%)
- Bottom (40%): Rolling 60-day beta with sector beta comparison
"""

from __future__ import annotations

import io
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]

from do_uw.models.state import AnalysisState
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.charts.chart_computations import (
    classify_vol_regime,
    compute_beta,
    compute_ewma_volatility,
    compute_rolling_volatility,
)
from do_uw.stages.render.charts.stock_chart_data import extract_chart_data
from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem

# Volatility zone thresholds from chart style registry.
_vol_style = get_chart_style("volatility")
_VOL_LOW = _vol_style.zone_thresholds["low"] if _vol_style.zone_thresholds else 20.0
_VOL_HIGH = _vol_style.zone_thresholds["high"] if _vol_style.zone_thresholds else 40.0

# Rolling beta window.
_BETA_WINDOW = 60


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@null_safe_chart
def create_volatility_chart(
    state: AnalysisState,
    period: str = "1Y",
    ds: DesignSystem | None = None,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a volatility analysis chart with two stacked subplots.

    Top: Rolling 30-day annualized volatility (company, sector, SPY).
    Bottom: Rolling 60-day beta with sector beta reference.

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
        c = resolve_colors("volatility", "svg")
    else:
        c = colors if colors is not None else resolve_colors("volatility", format)

    data = extract_chart_data(state, period)
    if data is None:
        return None

    # Compute rolling volatilities.
    company_vol = compute_rolling_volatility(data.prices, window=30)
    if not company_vol or len(company_vol) < 30:
        return None

    etf_vol: list[float] | None = None
    if data.etf_prices and len(data.etf_prices) >= 31:
        etf_vol = compute_rolling_volatility(data.etf_prices, window=30)

    spy_vol: list[float] | None = None
    if data.spy_prices and len(data.spy_prices) >= 31:
        spy_vol = compute_rolling_volatility(data.spy_prices, window=30)

    # Compute EWMA volatility for overlay.
    ewma_vol = compute_ewma_volatility(data.prices)
    regime_label, regime_duration = classify_vol_regime(ewma_vol)

    # Compute rolling beta.
    rolling_beta = _compute_rolling_beta(data.prices, data.spy_prices, _BETA_WINDOW)

    # Compute stats for header.
    stats = _compute_vol_stats(data, company_vol, etf_vol)
    stats["regime"] = regime_label
    stats["regime_duration"] = regime_duration

    matplotlib.use("Agg")
    plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=(10, 7), dpi=200, facecolor=c["bg"],
    )

    try:
        # Top subplot: Rolling volatility (55% of remaining).
        ax_vol: Any = fig.add_axes([0.08, 0.42, 0.86, 0.46])
        ax_vol.set_facecolor(c["bg"])
        _render_vol_subplot(ax_vol, data, company_vol, etf_vol, spy_vol, c, ewma_vol)

        # Bottom subplot: Rolling beta (35% of remaining).
        ax_beta: Any = fig.add_axes([0.08, 0.06, 0.86, 0.30])
        ax_beta.set_facecolor(c["bg"])
        _render_beta_subplot(ax_beta, data, rolling_beta, c)

        # Stats header (top 8%) -- rendered AFTER subplots so it paints on top.
        ax_header: Any = fig.add_axes([0.05, 0.91, 0.9, 0.08])
        _render_vol_header(ax_header, stats, data.ticker, period, c)

        _ = ds
        if format == "svg":
            return save_chart_to_svg(fig)
        return save_chart_to_bytes(fig, dpi=200)
    except Exception:
        plt.close(fig)
        raise


# ---------------------------------------------------------------------------
# Volatility subplot
# ---------------------------------------------------------------------------


def _render_vol_subplot(
    ax: Any,
    data: Any,
    company_vol: list[float],
    etf_vol: list[float] | None,
    spy_vol: list[float] | None,
    c: dict[str, str],
    ewma_vol: list[float] | None = None,
) -> None:
    """Render the rolling volatility comparison subplot with EWMA overlay."""
    vol_colors = get_chart_style("volatility").colors
    navy = c.get("header_bg", "#0B1D3A")
    gold = c.get("etf_line", "#D4A843")
    gray = c.get("text_muted", "#6B7280")
    orange = str(vol_colors.get("ewma_line", "#E67E22"))
    regime_low_color = str(vol_colors.get("regime_low", "#16A34A"))
    regime_elevated_color = str(vol_colors.get("regime_elevated", "#D97706"))
    regime_crisis_color = str(vol_colors.get("regime_crisis", "#B91C1C"))

    # Regime background shading (EWMA-based, very subtle).
    if ewma_vol and data.dates and len(ewma_vol) >= 30:
        _render_regime_shading(ax, data.dates, ewma_vol)

    # Background volatility zones.
    if data.dates:
        ax.axhspan(0, _VOL_LOW, color=regime_low_color, alpha=0.04)
        ax.axhspan(_VOL_LOW, _VOL_HIGH, color=regime_elevated_color, alpha=0.04)
        ax.axhspan(_VOL_HIGH, 100, color=regime_crisis_color, alpha=0.04)

        # Zone boundary lines.
        ax.axhline(y=_VOL_LOW, color=regime_low_color, linewidth=0.5, alpha=0.4, linestyle=":")
        ax.axhline(y=_VOL_HIGH, color=regime_crisis_color, linewidth=0.5, alpha=0.4, linestyle=":")

    # Company volatility — skip warmup window (first 30 values are 0.0).
    warmup = 30
    min_len = min(len(data.dates), len(company_vol))
    start = min(warmup, min_len)
    ax.plot(
        data.dates[start:min_len], company_vol[start:min_len],
        color=navy, linewidth=1.5,
        label=f"{data.ticker} Rolling 30d",
    )

    # EWMA volatility overlay (orange dashed).
    if ewma_vol and len(ewma_vol) >= warmup:
        ewma_len = min(len(data.dates), len(ewma_vol))
        ewma_start = min(warmup, ewma_len)
        ax.plot(
            data.dates[ewma_start:ewma_len],
            ewma_vol[ewma_start:ewma_len],
            linestyle="--", color=orange, linewidth=1.2, alpha=0.85,
            label="EWMA Vol (lambda=0.94)",
        )

    # Sector ETF volatility — same warmup trim.
    if etf_vol and data.etf_dates:
        etf_len = min(len(data.etf_dates), len(etf_vol))
        etf_start = min(warmup, etf_len)
        ax.plot(
            data.etf_dates[etf_start:etf_len], etf_vol[etf_start:etf_len],
            linestyle="--", color=gold, linewidth=1.0,
            label=data.etf_ticker or "Sector ETF",
        )

    # SPY volatility — same warmup trim.
    if spy_vol and data.spy_dates:
        spy_len = min(len(data.spy_dates), len(spy_vol))
        spy_start = min(warmup, spy_len)
        ax.plot(
            data.spy_dates[spy_start:spy_len], spy_vol[spy_start:spy_len],
            linestyle=":", color=gray, linewidth=1.0,
            label="S&P 500",
        )

    # Styling.
    ax.set_ylabel("Annualized Vol %", color=c.get("text", "#1F2937"), fontsize=9)
    ax.legend(
        loc="upper left", fontsize=7,
        framealpha=0.8, facecolor=c["bg"],
        edgecolor=c.get("grid", "#E5E7EB"),
        labelcolor=c.get("text", "#1F2937"),
    )

    # Set reasonable y-limits (exclude warmup zeros).
    all_vols = [v for v in company_vol[warmup:] if v > 0]
    if ewma_vol:
        all_vols.extend(v for v in ewma_vol[warmup:] if v > 0)
    if all_vols:
        y_max = min(max(all_vols) * 1.2, 120.0)
        ax.set_ylim(0, y_max)

    _apply_axis_style(ax, data.period, c, show_xlabel=False)


def _render_regime_shading(
    ax: Any, dates: list[Any], ewma_vol: list[float],
) -> None:
    """Add subtle background shading for volatility regime periods.

    Uses classify_vol_regime's percentile thresholds to shade
    LOW (green), ELEVATED (amber), CRISIS (red) periods.
    NORMAL gets no shading.
    """
    valid = [v for v in ewma_vol if v > 0]
    if not valid:
        return

    sorted_vals = sorted(valid)
    n = len(sorted_vals)
    p25 = sorted_vals[int(n * 0.25)]
    p75 = sorted_vals[int(n * 0.75)]
    p90 = sorted_vals[min(int(n * 0.90), n - 1)]

    # Regime colors from chart style registry.
    _vol_colors = get_chart_style("volatility").colors
    _REGIME_COLORS = {
        "LOW": str(_vol_colors.get("regime_low", "#16A34A")),
        "ELEVATED": str(_vol_colors.get("regime_elevated", "#D97706")),
        "CRISIS": str(_vol_colors.get("regime_crisis", "#B91C1C")),
    }

    min_len = min(len(dates), len(ewma_vol))

    def _label(v: float) -> str:
        if v <= 0:
            return "NORMAL"
        if v <= p25:
            return "LOW"
        elif v <= p75:
            return "NORMAL"
        elif v <= p90:
            return "ELEVATED"
        else:
            return "CRISIS"

    # Scan for regime segments and shade them.
    i = 0
    while i < min_len:
        regime = _label(ewma_vol[i])
        if regime == "NORMAL":
            i += 1
            continue
        # Find end of this regime segment.
        j = i + 1
        while j < min_len and _label(ewma_vol[j]) == regime:
            j += 1
        color = _REGIME_COLORS.get(regime)
        if color and j - i >= 2:
            ax.axvspan(
                dates[i], dates[min(j, min_len) - 1],
                alpha=0.08, color=color, zorder=0,
            )
        i = j


# ---------------------------------------------------------------------------
# Beta subplot
# ---------------------------------------------------------------------------


def _render_beta_subplot(
    ax: Any,
    data: Any,
    rolling_beta: list[float | None],
    c: dict[str, str],
) -> None:
    """Render the rolling beta subplot."""
    navy = c.get("header_bg", "#0B1D3A")
    gold = c.get("etf_line", "#D4A843")
    gray = c.get("text_muted", "#6B7280")

    # Beta = 1.0 reference line.
    ax.axhline(y=1.0, color=gray, linewidth=0.8, linestyle="--", alpha=0.7, label="Beta = 1.0")

    # Sector beta reference.
    sector_beta = data.sector_beta
    if sector_beta is not None:
        ax.axhline(
            y=sector_beta, color=gold, linewidth=0.8,
            linestyle="--", alpha=0.7,
            label=f"Sector Beta ({sector_beta:.2f})",
        )

    # Rolling beta line.
    min_len = min(len(data.dates), len(rolling_beta))
    beta_dates = data.dates[:min_len]
    beta_vals = rolling_beta[:min_len]

    # Split into segments where beta is not None.
    seg_dates: list[Any] = []
    seg_vals: list[float] = []

    for dt, bv in zip(beta_dates, beta_vals):
        if bv is not None:
            seg_dates.append(dt)
            seg_vals.append(bv)
        else:
            if seg_dates:
                ax.plot(seg_dates, seg_vals, color=navy, linewidth=1.5, label="_nolegend_")
            seg_dates = []
            seg_vals = []

    if seg_dates:
        ax.plot(seg_dates, seg_vals, color=navy, linewidth=1.5, label=f"{data.ticker} Beta")

    # Shade between company beta and sector beta.
    if sector_beta is not None and seg_dates and seg_vals:
        sector_line = [sector_beta] * len(seg_vals)
        ax.fill_between(
            seg_dates, seg_vals, sector_line,
            alpha=0.08, color=navy,
            label="_nolegend_",
        )

    # Styling.
    ax.set_ylabel("Beta", color=c.get("text", "#1F2937"), fontsize=9)
    ax.legend(
        loc="upper left", fontsize=7,
        framealpha=0.8, facecolor=c["bg"],
        edgecolor=c.get("grid", "#E5E7EB"),
        labelcolor=c.get("text", "#1F2937"),
    )

    # Reasonable y-limits for beta.
    valid_betas = [b for b in beta_vals if b is not None]
    if valid_betas:
        y_min = max(min(valid_betas) - 0.3, -0.5)
        y_max = min(max(valid_betas) + 0.3, 4.0)
        ax.set_ylim(y_min, y_max)

    _apply_axis_style(ax, data.period, c, show_xlabel=True)


# ---------------------------------------------------------------------------
# Stats header
# ---------------------------------------------------------------------------


def _compute_vol_stats(
    data: Any,
    company_vol: list[float],
    etf_vol: list[float] | None,
) -> dict[str, Any]:
    """Compute volatility stats for the header."""
    stats: dict[str, Any] = {}

    # Current company vol (last non-zero value).
    recent_vols = [v for v in company_vol[-5:] if v > 0]
    stats["current_vol"] = recent_vols[-1] if recent_vols else None

    # Current sector vol.
    if etf_vol:
        recent_etf = [v for v in etf_vol[-5:] if v > 0]
        stats["sector_vol"] = recent_etf[-1] if recent_etf else None
    else:
        stats["sector_vol"] = None

    # Vol ratio.
    cv = stats.get("current_vol")
    sv = stats.get("sector_vol")
    if isinstance(cv, (int, float)) and isinstance(sv, (int, float)) and sv > 0:
        stats["vol_ratio"] = cv / sv
    else:
        stats["vol_ratio"] = None

    # Beta values from chart data.
    stats["beta"] = data.company_beta
    stats["sector_beta"] = data.sector_beta

    # Beta ratio.
    b = data.company_beta
    sb = data.sector_beta
    if isinstance(b, (int, float)) and isinstance(sb, (int, float)) and sb > 0:
        stats["beta_ratio"] = b / sb
    else:
        stats["beta_ratio"] = None

    return stats


def _render_vol_header(
    ax_header: Any,
    stats: dict[str, Any],
    ticker: str,
    period: str,
    c: dict[str, str],
) -> None:
    """Render volatility stats in a header bar."""
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")
    # Draw filled rectangle as background (set_facecolor unreliable with overlapping axes).
    from matplotlib.patches import Rectangle
    bg_rect = Rectangle((0, 0), 1, 1, transform=ax_header.transAxes,
                         facecolor=c.get("header_bg", "#0B1D3A"), edgecolor="none",
                         zorder=0, clip_on=False)
    ax_header.add_patch(bg_rect)

    period_label = "12 Months" if period == "1Y" else "5 Years"
    ax_header.text(
        0.02, 0.5, f"{ticker} Rolling Volatility & Beta ({period_label})",
        fontsize=9, fontweight="bold",
        color=c.get("header_text", "#FFFFFF"),
        va="center",
    )

    items: list[tuple[str, str, str]] = []
    white = c.get("header_text", "#FFFFFF")

    cv = stats.get("current_vol")
    if isinstance(cv, (int, float)):
        items.append(("Vol", f"{cv:.1f}%", white))
    else:
        items.append(("Vol", "N/A", white))

    sv = stats.get("sector_vol")
    if isinstance(sv, (int, float)):
        items.append(("Sector Vol", f"{sv:.1f}%", white))
    else:
        items.append(("Sector Vol", "N/A", white))

    vr = stats.get("vol_ratio")
    if isinstance(vr, (int, float)):
        clr = c.get("price_down", "#B91C1C") if vr > 1.5 else white
        items.append(("Vol Ratio", f"{vr:.2f}x", clr))
    else:
        items.append(("Vol Ratio", "N/A", white))

    b = stats.get("beta")
    if isinstance(b, (int, float)):
        items.append(("Beta", f"{b:.2f}", white))
    else:
        items.append(("Beta", "N/A", white))

    sb = stats.get("sector_beta")
    if isinstance(sb, (int, float)):
        items.append(("Sec Beta", f"{sb:.2f}", white))
    else:
        items.append(("Sec Beta", "N/A", white))

    br = stats.get("beta_ratio")
    if isinstance(br, (int, float)):
        clr = c.get("price_down", "#B91C1C") if br > 1.5 else white
        items.append(("Beta Ratio", f"{br:.2f}x", clr))
    else:
        items.append(("Beta Ratio", "N/A", white))

    # Regime label + duration.
    regime = stats.get("regime")
    regime_dur = stats.get("regime_duration")
    if regime:
        _hdr_vol_colors = get_chart_style("volatility").colors
        _regime_colors = {
            "LOW": str(_hdr_vol_colors.get("regime_low", "#16A34A")),
            "NORMAL": white,
            "ELEVATED": str(_hdr_vol_colors.get("regime_elevated", "#D97706")),
            "CRISIS": c.get("price_down", "#B91C1C"),
        }
        regime_clr = _regime_colors.get(regime, white)
        dur_str = f" ({regime_dur}d)" if regime_dur else ""
        items.append(("Regime", f"{regime}{dur_str}", regime_clr))

    x_start = 0.24
    x_step = 0.095

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
# Rolling beta computation
# ---------------------------------------------------------------------------


def _compute_rolling_beta(
    prices: list[float],
    spy_prices: list[float] | None,
    window: int = 60,
) -> list[float | None]:
    """Compute rolling beta from price series.

    Returns a list (same length as prices) with None for the
    initial window period where beta cannot be computed.
    """
    if not spy_prices or len(prices) < window or len(spy_prices) < window:
        return [None] * len(prices)

    # Compute daily returns.
    comp_returns: list[float] = [0.0]
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            comp_returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        else:
            comp_returns.append(0.0)

    mkt_returns: list[float] = [0.0]
    for i in range(1, len(spy_prices)):
        if spy_prices[i - 1] > 0:
            mkt_returns.append((spy_prices[i] - spy_prices[i - 1]) / spy_prices[i - 1])
        else:
            mkt_returns.append(0.0)

    result: list[float | None] = [None] * window
    min_len = min(len(comp_returns), len(mkt_returns))

    for i in range(window, min_len):
        cr_window = comp_returns[i - window + 1 : i + 1]
        mr_window = mkt_returns[i - window + 1 : i + 1]
        beta = compute_beta(cr_window, mr_window)
        result.append(beta)

    # Pad to match prices length if needed.
    while len(result) < len(prices):
        result.append(None)

    return result[:len(prices)]


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------


def _apply_axis_style(
    ax: Any, period: str, c: dict[str, str],
    show_xlabel: bool = True,
) -> None:
    """Apply professional styling to an axis."""
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

    if show_xlabel:
        if period == "1Y":
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        else:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", rotation=0)
    else:
        ax.set_xticklabels([])


__all__ = ["create_volatility_chart"]
