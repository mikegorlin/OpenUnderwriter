"""Matplotlib-based stock performance chart for the UW Analysis.

Renders company vs sector ETF vs S&P 500 as % return, with earnings
diamonds, 52W labels, DDL callout, and volume bars.
"""

from __future__ import annotations

import base64
import io
import logging
from datetime import datetime
from typing import Any

from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)


def render_stock_chart_png(
    hist: dict[str, Any],
    info: dict[str, Any],
    ed: dict[str, Any],
    sector_hist: dict[str, Any],
    spy_hist: dict[str, Any],
    sector_etf: str,
    insider_txns: dict[str, Any],
    ticker: str,
) -> str:
    """Render the stock chart and return an <img> tag with base64 PNG."""
    import matplotlib
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    matplotlib.use("Agg")
    # Professional quality settings
    plt.rcParams.update({
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Arial", "SF Pro Text", "sans-serif"],
        "text.antialiased": True,
        "lines.antialiased": True,
        "axes.linewidth": 0.5,
        "axes.edgecolor": "#E5E7EB",
    })

    closes_raw, dates_raw = hist.get("Close", []), hist.get("Date", [])
    volumes_raw = hist.get("Volume", [])
    if not closes_raw or len(closes_raw) < 10:
        return ""
    closes, vdates = _parse_prices(closes_raw, dates_raw)
    volumes = _parse_volumes(volumes_raw, dates_raw, vdates)
    if len(closes) < 10:
        return ""

    dt_dates = _parse_date_strings(vdates)
    if len(dt_dates) < 10:
        return ""

    start_price = closes[0]
    pct_returns = [(c / start_price - 1) * 100 for c in closes]
    sector_pcts = _compute_benchmark_returns(sector_hist, dt_dates)
    spy_pcts = _compute_benchmark_returns(spy_hist, dt_dates)

    h52 = safe_float(info.get("fiftyTwoWeekHigh"), 0)
    l52 = safe_float(info.get("fiftyTwoWeekLow"), 0)
    cur_price = safe_float(info.get("currentPrice"), closes[-1])
    market_cap = safe_float(info.get("marketCap"), 0)

    fig, (ax_main, ax_vol) = plt.subplots(
        2, 1, figsize=(14, 4.5), dpi=200,
        gridspec_kw={"height_ratios": [4, 1], "hspace": 0.05},
    )
    fig.patch.set_facecolor("white")
    ax_main.set_facecolor("white")

    # Main company line with Google Finance style red/green fill
    # Green fill where return >= 0, red fill where return < 0
    import numpy as np
    pct_arr = np.array(pct_returns)
    dt_arr = np.array(dt_dates)
    ax_main.fill_between(dt_arr, pct_arr, 0,
                         where=pct_arr >= 0, color="#16A34A", alpha=0.08,
                         interpolate=True, zorder=2)
    ax_main.fill_between(dt_arr, pct_arr, 0,
                         where=pct_arr < 0, color="#DC2626", alpha=0.08,
                         interpolate=True, zorder=2)
    # Company line — green when up, red when down from baseline
    final_return = pct_returns[-1]
    line_color = "#16A34A" if final_return >= 0 else "#DC2626"
    ax_main.plot(dt_dates, pct_returns, color=line_color, linewidth=2,
                 label=ticker, zorder=5)
    # Zero line
    ax_main.axhline(y=0, color="#9CA3AF", linewidth=0.5, linestyle="--",
                    alpha=0.5, zorder=1)
    # Benchmark lines
    if spy_pcts:
        ax_main.plot(dt_dates, spy_pcts, color="#9CA3AF", linewidth=1,
                     label="S&P 500", zorder=3)
    if sector_pcts:
        ax_main.plot(dt_dates, sector_pcts, color="#2563EB", linewidth=1.5,
                     label=str(sector_etf), zorder=4)

    # Grid + formatting
    ax_main.grid(True, axis="y", color="#F3F4F6", linewidth=0.5, zorder=0)
    ax_main.grid(True, axis="x", color="#F3F4F6", linewidth=0.3, zorder=0)
    ax_main.set_axisbelow(True)
    ax_main.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x:+.0f}%" if x != 0 else "0%"))
    ax_main.tick_params(axis="y", labelsize=7, colors="#6B7280")
    ax_main.tick_params(axis="x", labelbottom=False, length=0)
    for spine in ax_main.spines.values():
        spine.set_visible(False)

    leg = ax_main.legend(loc="upper left", fontsize=6.5, frameon=True,
                         framealpha=0.9, edgecolor="#E5E7EB", fancybox=True)
    leg.get_frame().set_linewidth(0.5)

    # Overlays
    _plot_earnings_diamonds(ax_main, ed, dt_dates, pct_returns, closes, start_price)
    _plot_price_labels(ax_main, dt_dates, closes, pct_returns, h52, l52,
                       cur_price, start_price)
    _plot_return_labels(ax_main, dt_dates, pct_returns, spy_pcts,
                        sector_pcts, ticker, sector_etf)
    _plot_ddl_callout(ax_main, h52, l52, market_cap)

    # Volume
    _plot_volume_bars(ax_vol, dt_dates, volumes, insider_txns)
    ax_vol.set_facecolor("white")
    for spine in ax_vol.spines.values():
        spine.set_visible(False)
    ax_vol.tick_params(axis="y", labelsize=5.5, colors="#9CA3AF")
    ax_vol.tick_params(axis="x", labelsize=6.5, colors="#9CA3AF")
    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax_vol.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_vol.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x / 1e6:.0f}M" if x >= 1e6 else f"{x / 1e3:.0f}K"))
    ax_vol.grid(True, axis="y", color="#F3F4F6", linewidth=0.3)
    ax_vol.set_axisbelow(True)

    # Bottom legend
    ax_vol.text(0.0, -0.45, "VOLUME", transform=ax_vol.transAxes,
                fontsize=5.5, color="#6B7280", fontweight="bold")
    ax_vol.text(0.065, -0.45, "\u25cf = insider sale", transform=ax_vol.transAxes,
                fontsize=5.5, color="#F59E0B")
    ax_vol.text(0.175, -0.45, "\u25cf = insider buy", transform=ax_vol.transAxes,
                fontsize=5.5, color="#2563EB")
    ax_vol.text(0.275, -0.45, "\u25c6 = earnings", transform=ax_vol.transAxes,
                fontsize=5.5, color="#16A34A")

    fig.subplots_adjust(left=0.06, right=0.92, top=0.97, bottom=0.08)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="width:100%;max-width:1200px" alt="Stock Performance Chart">'
    )


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _parse_prices(closes_raw: list[Any], dates_raw: list[Any]) -> tuple[list[float], list[str]]:
    closes: list[float] = []
    vdates: list[str] = []
    for i, c in enumerate(closes_raw):
        v = safe_float(c, -1.0)
        if v > 0:
            closes.append(v)
            vdates.append(str(dates_raw[i]) if i < len(dates_raw) else "")
    return closes, vdates


def _parse_volumes(volumes_raw: list[Any], dates_raw: list[Any],
                   valid_dates: list[str]) -> list[float]:
    date_to_vol: dict[str, float] = {}
    for i, d in enumerate(dates_raw):
        if i < len(volumes_raw):
            date_to_vol[str(d)] = safe_float(volumes_raw[i], 0.0)
    return [date_to_vol.get(d, 0.0) for d in valid_dates]


def _parse_date_strings(vdates: list[str]) -> list[datetime]:
    result: list[datetime] = []
    for d in vdates:
        dt = _str_to_dt(d)
        if dt:
            result.append(dt)
    return result


def _str_to_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(s[:19].replace("T", " "), fmt)
            except ValueError:
                continue
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _compute_benchmark_returns(
    bench_hist: dict[str, Any], target_dates: list[datetime],
) -> list[float] | None:
    if not bench_hist:
        return None
    b_closes = bench_hist.get("Close", [])
    b_dates = bench_hist.get("Date", [])
    if not b_closes or len(b_closes) < 10:
        return None
    date_to_price: dict[str, float] = {}
    for i, d in enumerate(b_dates):
        if i < len(b_closes):
            p = safe_float(b_closes[i], -1.0)
            if p > 0:
                date_to_price[str(d)[:10]] = p
    if not date_to_price:
        return None
    sorted_dates = sorted(date_to_price.keys())
    start_p = date_to_price[sorted_dates[0]]
    result: list[float] = []
    last_p = start_p
    for dt in target_dates:
        ds = dt.strftime("%Y-%m-%d")
        if ds in date_to_price:
            last_p = date_to_price[ds]
        result.append((last_p / start_p - 1) * 100)
    return result


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def _find_nearest_date_idx(target: str, date_idx: dict[str, int]) -> int | None:
    try:
        t = datetime.strptime(target, "%Y-%m-%d")
    except ValueError:
        return None
    best_idx, best_diff = None, float("inf")
    for ds, idx in date_idx.items():
        try:
            diff = abs((datetime.strptime(ds, "%Y-%m-%d") - t).days)
            if diff < best_diff:
                best_diff, best_idx = diff, idx
        except ValueError:
            continue
    return best_idx if best_diff <= 5 else None


def _plot_earnings_diamonds(
    ax: Any, ed: dict[str, Any], dt_dates: list[datetime],
    pct_returns: list[float], closes: list[float], start_price: float,
) -> None:
    edates = ed.get("Earnings Date", []) if isinstance(ed, dict) else []
    esurps = ed.get("Surprise(%)", []) if isinstance(ed, dict) else []
    if not edates:
        return
    date_idx: dict[str, int] = {dt.strftime("%Y-%m-%d"): i for i, dt in enumerate(dt_dates)}
    for ei, ev in enumerate(edates):
        surp = esurps[ei] if ei < len(esurps) else None
        if surp is None:
            continue
        surp_val = safe_float(surp, 0.0)
        es = ev[:10] if isinstance(ev, str) else (
            ev.strftime("%Y-%m-%d") if hasattr(ev, "strftime") else "")
        if not es:
            continue
        idx = date_idx.get(es) or _find_nearest_date_idx(es, date_idx)
        if idx is None or idx >= len(dt_dates):
            continue
        color = "#16A34A" if surp_val >= 0 else "#DC2626"
        ax.plot(dt_dates[idx], pct_returns[idx], marker="D", markersize=6,
                color=color, zorder=10, markeredgecolor="white", markeredgewidth=0.5)
        label = f"Beat +{surp_val:.0f}%" if surp_val >= 0 else f"Miss {surp_val:.0f}%"
        ax.annotate(label, (dt_dates[idx], pct_returns[idx]),
                    textcoords="offset points", xytext=(0, 10),
                    fontsize=5, color=color, fontweight="bold",
                    ha="center", va="bottom", zorder=11)


def _plot_price_labels(
    ax: Any, dt_dates: list[datetime], closes: list[float],
    pct_returns: list[float], h52: float, l52: float,
    cur_price: float, start_price: float,
) -> None:
    if not closes or not dt_dates:
        return
    max_idx = closes.index(max(closes))
    min_idx = closes.index(min(closes))
    if h52 > 0:
        ax.annotate(
            f"${h52:,.2f}", (dt_dates[max_idx], pct_returns[max_idx]),
            textcoords="offset points", xytext=(0, 12),
            fontsize=5.5, color="white", fontweight="bold",
            ha="center", va="bottom", zorder=12,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#16A34A",
                      "edgecolor": "none", "alpha": 0.9})
    if l52 > 0:
        ax.annotate(
            f"${l52:,.2f}", (dt_dates[min_idx], pct_returns[min_idx]),
            textcoords="offset points", xytext=(0, -14),
            fontsize=5.5, color="white", fontweight="bold",
            ha="center", va="top", zorder=12,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#DC2626",
                      "edgecolor": "none", "alpha": 0.9})
    ax.annotate(
        f"${cur_price:,.2f}", (dt_dates[-1], pct_returns[-1]),
        textcoords="offset points", xytext=(8, 0),
        fontsize=5.5, color="white", fontweight="bold",
        ha="left", va="center", zorder=12,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#374151",
                  "edgecolor": "none", "alpha": 0.9})


def _plot_return_labels(
    ax: Any, dt_dates: list[datetime], pct_returns: list[float],
    spy_pcts: list[float] | None, sector_pcts: list[float] | None,
    ticker: str, sector_etf: str,
) -> None:
    if not dt_dates or not pct_returns:
        return
    right_x = dt_dates[-1]
    labels: list[tuple[float, str, str]] = []
    labels.append((pct_returns[-1], f"{pct_returns[-1]:+.0f}%", "#111827"))
    if sector_pcts:
        labels.append((sector_pcts[-1], f"{sector_pcts[-1]:+.0f}%", "#2563EB"))
    if spy_pcts:
        labels.append((spy_pcts[-1], f"{spy_pcts[-1]:+.0f}%", "#9CA3AF"))
    for val, label, color in labels:
        ax.annotate(
            label, (right_x, val),
            textcoords="offset points", xytext=(35, 0),
            fontsize=6, color=color, fontweight="bold",
            ha="left", va="center", zorder=12, annotation_clip=False)


def _plot_ddl_callout(
    ax: Any, h52: float, l52: float, market_cap: float,
) -> None:
    if h52 <= 0 or l52 <= 0:
        return
    drop_pct = (l52 - h52) / h52 * 100
    if drop_pct >= -10:
        return
    if market_cap > 0:
        dollar_loss = market_cap * abs(drop_pct) / 100
        if dollar_loss >= 1e9:
            loss_str = f"${dollar_loss / 1e9:.1f}B"
        else:
            loss_str = f"${dollar_loss / 1e6:.0f}M"
        ddl_text = f"DDL {drop_pct:+.0f}% \u00b7 ${h52:,.0f}\u2192${l52:,.0f} ({loss_str})"
    else:
        ddl_text = f"DDL {drop_pct:+.0f}% \u00b7 ${h52:,.0f}\u2192${l52:,.0f}"
    ax.text(0.98, 0.04, ddl_text, transform=ax.transAxes, fontsize=6.5,
            color="white", fontweight="bold", ha="right", va="bottom", zorder=15,
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "#DC2626",
                      "edgecolor": "none", "alpha": 0.95})


def _plot_volume_bars(
    ax: Any, dt_dates: list[datetime], volumes: list[float],
    insider_txns: dict[str, Any],
) -> None:
    if not dt_dates or not volumes:
        return
    insider_dates: dict[str, str] = {}
    if isinstance(insider_txns, dict):
        for i, d in enumerate(insider_txns.get("Start Date", [])):
            ds = str(d)[:10]
            txn_texts = insider_txns.get("Text", [])
            txt = str(txn_texts[i]).lower() if i < len(txn_texts) else ""
            if "sale" in txt:
                insider_dates[ds] = "sale"
            elif "purchase" in txt or "buy" in txt:
                insider_dates[ds] = "buy"
            elif ds not in insider_dates:
                insider_dates[ds] = "sale"
    colors = []
    for dt in dt_dates:
        ds = dt.strftime("%Y-%m-%d")
        if ds in insider_dates:
            colors.append("#2563EB" if insider_dates[ds] == "buy" else "#F59E0B")
        else:
            colors.append("#CBD5E1")
    ax.bar(dt_dates, volumes, width=1.5, color=colors, zorder=2, linewidth=0)


def render_stock_chart_5y_png(
    hist: dict[str, Any],
    sector_hist: dict[str, Any],
    spy_hist: dict[str, Any],
    sector_etf: str,
    ticker: str,
) -> str:
    """Render compact 5-year stock chart — lower detail, same width."""
    import matplotlib
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Arial", "SF Pro Text", "sans-serif"],
        "text.antialiased": True, "lines.antialiased": True,
        "axes.linewidth": 0.5, "axes.edgecolor": "#E5E7EB",
    })

    closes_raw, dates_raw = hist.get("Close", []), hist.get("Date", [])
    if not closes_raw or len(closes_raw) < 20:
        return ""
    closes, vdates = _parse_prices(closes_raw, dates_raw)
    if len(closes) < 20:
        return ""

    dt_dates = _parse_date_strings(vdates)
    if len(dt_dates) < 20:
        return ""

    start_price = closes[0]
    pct_returns = [(c / start_price - 1) * 100 for c in closes]
    sector_pcts = _compute_benchmark_returns(sector_hist, dt_dates)
    spy_pcts = _compute_benchmark_returns(spy_hist, dt_dates)

    fig, ax = plt.subplots(1, 1, figsize=(14, 1.5), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Google Finance style red/green fill
    import numpy as np
    pct_arr = np.array(pct_returns)
    dt_arr = np.array(dt_dates)
    ax.fill_between(dt_arr, pct_arr, 0,
                    where=pct_arr >= 0, color="#16A34A", alpha=0.06,
                    interpolate=True, zorder=2)
    ax.fill_between(dt_arr, pct_arr, 0,
                    where=pct_arr < 0, color="#DC2626", alpha=0.06,
                    interpolate=True, zorder=2)
    final_ret = pct_returns[-1]
    line_color = "#16A34A" if final_ret >= 0 else "#DC2626"
    ax.plot(dt_dates, pct_returns, color=line_color, linewidth=1.5,
            label=ticker, zorder=5)
    ax.axhline(y=0, color="#9CA3AF", linewidth=0.4, linestyle="--",
               alpha=0.4, zorder=1)
    if sector_pcts:
        ax.plot(dt_dates[:len(sector_pcts)], sector_pcts,
                color="#2563EB", linewidth=0.8, label=sector_etf or "Sector", zorder=4)
    if spy_pcts:
        ax.plot(dt_dates[:len(spy_pcts)], spy_pcts,
                color="#9CA3AF", linewidth=0.6, label="S&P 500", zorder=3)

    # Subtle grid
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.grid(True, alpha=0.15, linewidth=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    # Return label on right
    ax.annotate(f"{final_ret:+.0f}%", xy=(dt_dates[-1], final_ret),
                fontsize=7, fontweight="bold", color=line_color,
                xytext=(5, 0), textcoords="offset points", va="center")

    ax.legend(fontsize=6, loc="upper left", framealpha=0.8)
    ax.tick_params(labelsize=6)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return f'<img src="data:image/png;base64,{b64}" style="width:100%;height:auto;display:block;" alt="{ticker} 5-year performance"/>'
