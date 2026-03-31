#!/usr/bin/env python3
"""Generate 20 experimental stock chart visualizations for D&O underwriting.

Usage: python scripts/generate_chart_experiments.py
Reads: output/AAPL/2026-03-22/state.json
Writes: output/AAPL/chart_experiments.html
"""

import base64
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(val: Any, default: float = 0.0) -> float:
    """Convert value to float safely, handling None, strings, percentages."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace(",", "").replace("%", "").replace("$", "")
        if not val or val.lower() in ("n/a", "none", "nan", "-", "—"):
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def parse_dates(date_strings: list[str]) -> list[datetime]:
    """Parse date strings into datetime objects."""
    dates = []
    for ds in date_strings:
        if ds is None:
            continue
        try:
            # Handle timezone-aware strings
            clean = ds.split("+")[0].split("-04:00")[0].split("-05:00")[0].strip()
            # Try multiple formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dates.append(datetime.strptime(clean, fmt))
                    break
                except ValueError:
                    continue
            else:
                # Last resort: just take first 10 chars
                dates.append(datetime.strptime(ds[:10], "%Y-%m-%d"))
        except (ValueError, TypeError):
            dates.append(datetime(2020, 1, 1))  # fallback
    return dates


def fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def placeholder_chart(title: str, reason: str) -> str:
    """Generate a gray placeholder chart when data is unavailable."""
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.set_facecolor("#F3F4F6")
    ax.text(0.5, 0.5, f"{title}\n\n{reason}",
            ha="center", va="center", fontsize=14, color="#6B7280",
            transform=ax.transAxes, fontfamily="sans-serif")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig_to_base64(fig)


# Colors
GREEN = "#16A34A"
RED = "#DC2626"
BLUE = "#2563EB"
GRAY = "#9CA3AF"
ORANGE = "#F97316"
DARK_GRAY = "#374151"
LIGHT_GREEN = "#DCFCE7"
LIGHT_RED = "#FEE2E2"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
})


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

STATE_PATH = Path("output/AAPL/2026-03-22/state.json")
with open(STATE_PATH) as f:
    state = json.load(f)

md = state["acquired_data"]["market_data"]
info = md["info"]
ticker = state["ticker"]

# Pre-parse common datasets
h2y_dates = parse_dates(md["history_2y"]["Date"])
h2y_close = [safe_float(v) for v in md["history_2y"]["Close"]]
h2y_volume = [safe_float(v) for v in md["history_2y"]["Volume"]]
h2y_high = [safe_float(v) for v in md["history_2y"]["High"]]
h2y_low = [safe_float(v) for v in md["history_2y"]["Low"]]

h5y_dates = parse_dates(md["history_5y"]["Date"])
h5y_close = [safe_float(v) for v in md["history_5y"]["Close"]]
h5y_high = [safe_float(v) for v in md["history_5y"]["High"]]
h5y_low = [safe_float(v) for v in md["history_5y"]["Low"]]
h5y_volume = [safe_float(v) for v in md["history_5y"]["Volume"]]

sec2y_dates = parse_dates(md["sector_history_2y"]["Date"])
sec2y_close = [safe_float(v) for v in md["sector_history_2y"]["Close"]]

spy2y_dates = parse_dates(md["spy_history_2y"]["Date"])
spy2y_close = [safe_float(v) for v in md["spy_history_2y"]["Close"]]

sec5y_dates = parse_dates(md["sector_history_5y"]["Date"])
sec5y_close = [safe_float(v) for v in md["sector_history_5y"]["Close"]]

spy5y_dates = parse_dates(md["spy_history_5y"]["Date"])
spy5y_close = [safe_float(v) for v in md["spy_history_5y"]["Close"]]

sector_etf = md.get("sector_etf", "XLK")

# Earnings dates with reported data
ed = md["earnings_dates"]
ed_dates_raw = ed["Earnings Date"]
ed_est = ed["EPS Estimate"]
ed_act = ed["Reported EPS"]
ed_surp = ed["Surprise(%)"]

# Earnings history (last 4 quarters)
eh = md["earnings_history"]

# Insider transactions
it = md["insider_transactions"]

# Income statement
inc = md["income_stmt"]
qinc = md["quarterly_income_stmt"]

# Balance sheet
bs = md["balance_sheet"]


# ---------------------------------------------------------------------------
# Chart generators
# ---------------------------------------------------------------------------

def chart_01_relative_performance() -> str:
    """Relative Performance (% Return) — AAPL vs sector vs S&P 500, 2-year."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Calculate % returns from start
    base_aapl = h2y_close[0]
    base_sec = sec2y_close[0]
    base_spy = spy2y_close[0]

    aapl_ret = [(c / base_aapl - 1) * 100 for c in h2y_close]
    sec_ret = [(c / base_sec - 1) * 100 for c in sec2y_close]
    spy_ret = [(c / base_spy - 1) * 100 for c in spy2y_close]

    # Fill under AAPL line: green when positive, red when negative
    ax.fill_between(h2y_dates, aapl_ret, 0,
                     where=[r >= 0 for r in aapl_ret],
                     color=GREEN, alpha=0.08, interpolate=True)
    ax.fill_between(h2y_dates, aapl_ret, 0,
                     where=[r < 0 for r in aapl_ret],
                     color=RED, alpha=0.08, interpolate=True)

    ax.plot(h2y_dates, aapl_ret, color=BLUE, linewidth=2, label=f"{ticker}", zorder=5)
    ax.plot(sec2y_dates, sec_ret, color=ORANGE, linewidth=1.2, label=f"{sector_etf}", alpha=0.8)
    ax.plot(spy2y_dates, spy_ret, color=GRAY, linewidth=1.2, label="SPY", alpha=0.8)
    ax.axhline(0, color="#1F2937", linewidth=0.5, linestyle="-")

    # Overlay earnings dates with reported data as diamonds
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None or ed_est[i] is None:
            continue
        edate = parse_dates([ed_dates_raw[i]])[0]
        if edate < h2y_dates[0] or edate > h2y_dates[-1]:
            continue
        # Find closest trading date
        closest_idx = min(range(len(h2y_dates)), key=lambda j: abs((h2y_dates[j] - edate).days))
        surprise = safe_float(ed_surp[i])
        color = GREEN if surprise >= 0 else RED
        ax.plot(h2y_dates[closest_idx], aapl_ret[closest_idx], marker="D",
                color=color, markersize=8, zorder=10)
        if abs(surprise) > 2:
            ax.annotate(f"{'+' if surprise > 0 else ''}{surprise:.1f}%",
                        (h2y_dates[closest_idx], aapl_ret[closest_idx]),
                        textcoords="offset points", xytext=(0, 12),
                        fontsize=7, color=color, ha="center", fontweight="bold")

    ax.set_title(f"{ticker} vs {sector_etf} vs S&P 500 — 2-Year Relative Performance (%)", fontweight="bold")
    ax.set_ylabel("Return (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_02_price_sma() -> str:
    """5-Year Absolute Price with 50/200 SMA and cross signals."""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(h5y_dates, h5y_close, color=BLUE, linewidth=1.5, label=f"{ticker} Price", alpha=0.9)

    # 50-day SMA
    close_arr = np.array(h5y_close)
    sma50 = np.convolve(close_arr, np.ones(50)/50, mode="valid")
    sma200 = np.convolve(close_arr, np.ones(200)/200, mode="valid")

    sma50_dates = h5y_dates[49:]
    sma200_dates = h5y_dates[199:]

    ax.plot(sma50_dates, sma50, color=ORANGE, linewidth=1.2, label="50-Day SMA", alpha=0.8)
    ax.plot(sma200_dates, sma200, color=RED, linewidth=1.2, label="200-Day SMA", alpha=0.8)

    # Find golden cross / death cross
    # Align sma50 and sma200 to same date range
    offset = 200 - 50  # sma200 starts 150 days later
    sma50_aligned = sma50[offset:]
    min_len = min(len(sma50_aligned), len(sma200))
    sma50_aligned = sma50_aligned[:min_len]
    sma200_trimmed = sma200[:min_len]
    cross_dates = sma200_dates[:min_len]

    for i in range(1, min_len):
        if sma50_aligned[i-1] <= sma200_trimmed[i-1] and sma50_aligned[i] > sma200_trimmed[i]:
            ax.axvline(cross_dates[i], color=GREEN, alpha=0.3, linewidth=1.5, linestyle="--")
            ax.annotate("Golden\nCross", (cross_dates[i], sma50_aligned[i]),
                        textcoords="offset points", xytext=(10, 15),
                        fontsize=8, color=GREEN, fontweight="bold")
        elif sma50_aligned[i-1] >= sma200_trimmed[i-1] and sma50_aligned[i] < sma200_trimmed[i]:
            ax.axvline(cross_dates[i], color=RED, alpha=0.3, linewidth=1.5, linestyle="--")
            ax.annotate("Death\nCross", (cross_dates[i], sma50_aligned[i]),
                        textcoords="offset points", xytext=(10, -20),
                        fontsize=8, color=RED, fontweight="bold")

    ax.set_title(f"{ticker} — 5-Year Price with 50/200 Day Moving Averages", fontweight="bold")
    ax.set_ylabel("Price ($)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_03_drawdown() -> str:
    """Drawdown from peak — shows depth and duration of pullbacks."""
    fig, ax = plt.subplots(figsize=(14, 5))

    close_arr = np.array(h5y_close)
    running_max = np.maximum.accumulate(close_arr)
    drawdown = (close_arr - running_max) / running_max * 100

    ax.fill_between(h5y_dates, drawdown, 0, color=RED, alpha=0.3)
    ax.plot(h5y_dates, drawdown, color=RED, linewidth=0.8)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.5)

    # Annotate worst drawdowns
    min_dd = np.min(drawdown)
    min_idx = int(np.argmin(drawdown))
    ax.annotate(f"Max: {min_dd:.1f}%\n{h5y_dates[min_idx].strftime('%b %d, %Y')}",
                (h5y_dates[min_idx], drawdown[min_idx]),
                textcoords="offset points", xytext=(40, -10),
                fontsize=9, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))

    ax.set_title(f"{ticker} — Drawdown From All-Time High (5-Year)", fontweight="bold")
    ax.set_ylabel("Drawdown (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylim(min_dd * 1.2, 5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_04_normalized_100() -> str:
    """Normalized to 100 comparison — AAPL vs sector vs S&P 500, 5-year."""
    fig, ax = plt.subplots(figsize=(14, 6))

    aapl_norm = [c / h5y_close[0] * 100 for c in h5y_close]
    sec_norm = [c / sec5y_close[0] * 100 for c in sec5y_close]
    spy_norm = [c / spy5y_close[0] * 100 for c in spy5y_close]

    ax.plot(h5y_dates, aapl_norm, color=BLUE, linewidth=2, label=ticker)
    ax.plot(sec5y_dates, sec_norm, color=ORANGE, linewidth=1.2, label=sector_etf, alpha=0.8)
    ax.plot(spy5y_dates, spy_norm, color=GRAY, linewidth=1.2, label="SPY", alpha=0.8)
    ax.axhline(100, color=DARK_GRAY, linewidth=0.5, linestyle="--")

    # End labels
    for series, dates, color, name in [
        (aapl_norm, h5y_dates, BLUE, ticker),
        (sec_norm, sec5y_dates, ORANGE, sector_etf),
        (spy_norm, spy5y_dates, GRAY, "SPY"),
    ]:
        ax.annotate(f"{name}: {series[-1]:.0f}",
                    (dates[-1], series[-1]),
                    textcoords="offset points", xytext=(5, 0),
                    fontsize=9, color=color, fontweight="bold")

    ax.set_title(f"{ticker} vs {sector_etf} vs S&P 500 — 5-Year Normalized to 100", fontweight="bold")
    ax.set_ylabel("Index (Start = 100)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_05_volume_spikes() -> str:
    """Volume with spike detection — highlights >2x 20-day average."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), height_ratios=[2, 1],
                                     sharex=True, gridspec_kw={"hspace": 0.05})

    # Price
    ax1.plot(h2y_dates, h2y_close, color=BLUE, linewidth=1.5)
    ax1.set_ylabel("Price ($)")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax1.set_title(f"{ticker} — Volume Spike Detection (2-Year)", fontweight="bold")

    # Volume
    vol_arr = np.array(h2y_volume)
    sma20_vol = np.convolve(vol_arr, np.ones(20)/20, mode="same")
    # Fix edges
    for i in range(10):
        sma20_vol[i] = np.mean(vol_arr[:i+10])
    for i in range(len(vol_arr)-10, len(vol_arr)):
        sma20_vol[i] = np.mean(vol_arr[i-10:])

    is_spike = vol_arr > (2 * sma20_vol)
    colors = [ORANGE if s else GRAY for s in is_spike]

    ax2.bar(h2y_dates, vol_arr, color=colors, width=1.5, alpha=0.7)
    ax2.plot(h2y_dates, sma20_vol, color=DARK_GRAY, linewidth=0.8, linestyle="--",
             label="20-Day Avg", alpha=0.6)

    # Label top spikes
    spike_indices = np.where(is_spike)[0]
    if len(spike_indices) > 0:
        # Get top 5 spikes
        top_spikes = sorted(spike_indices, key=lambda i: vol_arr[i], reverse=True)[:5]
        for idx in top_spikes:
            ax2.annotate(f"{h2y_dates[idx].strftime('%b %d')}",
                        (h2y_dates[idx], vol_arr[idx]),
                        textcoords="offset points", xytext=(0, 8),
                        fontsize=7, color=ORANGE, ha="center", fontweight="bold",
                        rotation=45)

    ax2.set_ylabel("Volume")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
    ax2.legend(loc="upper right", fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_06_insider_scatter() -> str:
    """Insider Transaction Scatter — price line with trade markers."""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(h2y_dates, h2y_close, color=BLUE, linewidth=1.5, alpha=0.7, label="Price")

    # Plot insider transactions
    dates_raw = it["Start Date"]
    shares = it["Shares"]
    values = it["Value"]
    insiders = it["Insider"]
    texts = it["Text"]

    trade_dates = []
    trade_prices = []
    trade_sizes = []
    trade_labels = []
    trade_types = []  # sale or gift

    for i in range(len(dates_raw)):
        if dates_raw[i] is None:
            continue
        try:
            tdate = datetime.strptime(dates_raw[i][:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        if tdate < h2y_dates[0] or tdate > h2y_dates[-1]:
            continue

        # Find closest price
        closest_idx = min(range(len(h2y_dates)), key=lambda j: abs((h2y_dates[j] - tdate).days))

        val = safe_float(values[i])
        shr = safe_float(shares[i])
        text = texts[i] if texts[i] else ""
        is_gift = "Gift" in text
        is_sale = "Sale" in text or (val > 0 and not is_gift)

        trade_dates.append(h2y_dates[closest_idx])
        trade_prices.append(h2y_close[closest_idx])
        trade_sizes.append(max(val, shr * h2y_close[closest_idx]) if val == 0 else val)
        trade_labels.append(insiders[i] if insiders[i] else "Unknown")
        trade_types.append("gift" if is_gift else "sale")

    if trade_dates:
        max_val = max(trade_sizes) if trade_sizes else 1
        for j in range(len(trade_dates)):
            size = max(20, min(300, trade_sizes[j] / max_val * 300))
            color = GRAY if trade_types[j] == "gift" else RED
            ax.scatter(trade_dates[j], trade_prices[j], s=size, color=color,
                       alpha=0.5, edgecolors=color, linewidths=1.5, zorder=5)

        # Label top 5 by value
        sorted_idx = sorted(range(len(trade_sizes)), key=lambda i: trade_sizes[i], reverse=True)[:5]
        for j in sorted_idx:
            val_str = f"${trade_sizes[j]/1e6:.1f}M" if trade_sizes[j] >= 1e6 else f"${trade_sizes[j]/1e3:.0f}K"
            name_short = trade_labels[j].split()[-1].title() if trade_labels[j] else ""
            ax.annotate(f"{name_short}\n{val_str}",
                        (trade_dates[j], trade_prices[j]),
                        textcoords="offset points", xytext=(10, 10),
                        fontsize=7, color=RED, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color=RED, alpha=0.5, lw=0.8))

    ax.scatter([], [], s=60, color=RED, alpha=0.5, label="Sale")
    ax.scatter([], [], s=60, color=GRAY, alpha=0.5, label="Gift/Grant")

    ax.set_title(f"{ticker} — Insider Transactions on Price (2-Year)", fontweight="bold")
    ax.set_ylabel("Price ($)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_07_cumulative_insider() -> str:
    """Net Insider Activity Cumulative — running sum of insider shares."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), height_ratios=[2, 1],
                                     sharex=True, gridspec_kw={"hspace": 0.05})

    ax1.plot(h2y_dates, h2y_close, color=BLUE, linewidth=1.5)
    ax1.set_ylabel("Price ($)")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax1.set_title(f"{ticker} — Cumulative Net Insider Activity (2-Year)", fontweight="bold")

    # Build daily insider net shares
    insider_by_date: dict[str, float] = {}
    for i in range(len(it["Start Date"])):
        d = it["Start Date"][i]
        if d is None:
            continue
        text = it["Text"][i] if it["Text"][i] else ""
        shr = safe_float(it["Shares"][i])
        if "Sale" in text:
            shr = -shr  # Sales are negative
        elif "Gift" in text:
            shr = -shr  # Gifts reduce holding
        # else: grants/buys are positive (but yfinance shows all as sales for AAPL)
        # For AAPL, most transactions without text are grants (no value)
        val = safe_float(it["Value"][i])
        if not text and val == 0:
            # Likely a grant (vesting), keep positive
            pass
        elif not text:
            shr = -shr  # Has value but no text = likely sale

        insider_by_date[d[:10]] = insider_by_date.get(d[:10], 0) + shr

    # Create cumulative series aligned to 2y dates
    cum_shares = 0.0
    cum_series = []
    sorted_insider_dates = sorted(insider_by_date.keys())
    insider_idx = 0

    for dt in h2y_dates:
        dt_str = dt.strftime("%Y-%m-%d")
        while insider_idx < len(sorted_insider_dates) and sorted_insider_dates[insider_idx] <= dt_str:
            cum_shares += insider_by_date[sorted_insider_dates[insider_idx]]
            insider_idx += 1
        cum_series.append(cum_shares)

    cum_arr = np.array(cum_series)
    ax2.fill_between(h2y_dates, cum_arr, 0,
                      where=cum_arr >= 0, color=GREEN, alpha=0.3)
    ax2.fill_between(h2y_dates, cum_arr, 0,
                      where=cum_arr < 0, color=RED, alpha=0.3)
    ax2.plot(h2y_dates, cum_arr, color=DARK_GRAY, linewidth=1)
    ax2.axhline(0, color=DARK_GRAY, linewidth=0.5)
    ax2.set_ylabel("Net Shares")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K"))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_08_earnings_waterfall() -> str:
    """Earnings Reaction Waterfall — EPS surprise vs 1-day price reaction."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Get earnings dates with actual data (skip future)
    quarters = []
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None or ed_est[i] is None:
            continue
        surprise = safe_float(ed_surp[i])
        edate = parse_dates([ed_dates_raw[i]])[0]
        if edate < h2y_dates[0]:
            continue

        # Find price reaction: close on earnings day vs next trading day
        closest_idx = min(range(len(h2y_dates)), key=lambda j: abs((h2y_dates[j] - edate).days))
        if closest_idx + 1 < len(h2y_close):
            price_before = h2y_close[closest_idx]
            price_after = h2y_close[min(closest_idx + 1, len(h2y_close) - 1)]
            price_reaction = (price_after / price_before - 1) * 100
        else:
            price_reaction = 0

        q_label = edate.strftime("%b '%y")
        quarters.append((q_label, surprise, price_reaction, safe_float(ed_act[i]), safe_float(ed_est[i])))

    quarters.reverse()  # Chronological order

    if not quarters:
        return placeholder_chart("Earnings Reaction Waterfall", "No earnings data in range")

    y_pos = np.arange(len(quarters))
    labels = [q[0] for q in quarters]
    surprises = [q[1] for q in quarters]
    reactions = [q[2] for q in quarters]

    bar_width = 0.35

    # EPS Surprise bars (left side)
    colors_s = [GREEN if s >= 0 else RED for s in surprises]
    ax.barh(y_pos + bar_width/2, surprises, bar_width, color=colors_s, alpha=0.7,
            label="EPS Surprise (%)", edgecolor="white", linewidth=0.5)

    # Price Reaction bars
    colors_r = [GREEN if r >= 0 else RED for r in reactions]
    ax.barh(y_pos - bar_width/2, reactions, bar_width, color=colors_r, alpha=0.4,
            label="1-Day Price Reaction (%)", edgecolor="white", linewidth=0.5,
            hatch="///")

    # Labels on bars
    for i, (s, r) in enumerate(zip(surprises, reactions)):
        ax.text(s + (0.3 if s >= 0 else -0.3), i + bar_width/2,
                f"+{s:.1f}%" if s >= 0 else f"{s:.1f}%",
                va="center", ha="left" if s >= 0 else "right",
                fontsize=8, color=DARK_GRAY, fontweight="bold")
        ax.text(r + (0.3 if r >= 0 else -0.3), i - bar_width/2,
                f"+{r:.1f}%" if r >= 0 else f"{r:.1f}%",
                va="center", ha="left" if r >= 0 else "right",
                fontsize=8, color=DARK_GRAY)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.axvline(0, color=DARK_GRAY, linewidth=0.5)
    ax.set_xlabel("Percentage (%)")
    ax.set_title(f"{ticker} — Earnings Surprise vs Market Reaction", fontweight="bold")
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_09_guidance_vs_actual() -> str:
    """Guidance vs Actual — grouped bars showing EPS estimate vs actual."""
    fig, ax = plt.subplots(figsize=(14, 5))

    quarters = []
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None or ed_est[i] is None:
            continue
        edate = parse_dates([ed_dates_raw[i]])[0]
        q_label = edate.strftime("Q%m/%y").replace("Q01", "Q1-FY").replace("Q04", "Q2-FY").replace("Q07", "Q3-FY").replace("Q10", "Q4-FY")
        # Simple quarter label
        month = edate.month
        q_num = {1: "FQ1", 2: "FQ1", 4: "FQ2", 5: "FQ2", 7: "FQ3", 8: "FQ3", 10: "FQ4", 11: "FQ4"}
        q_label = f"{q_num.get(month, 'Q?')} {edate.strftime('%y')}"
        quarters.append((q_label, safe_float(ed_est[i]), safe_float(ed_act[i])))

    quarters.reverse()  # Chronological
    # Limit to last 12
    quarters = quarters[-12:]

    x = np.arange(len(quarters))
    width = 0.35

    estimates = [q[1] for q in quarters]
    actuals = [q[2] for q in quarters]

    ax.bar(x - width/2, estimates, width, label="Estimate", color=GRAY, alpha=0.7, edgecolor="white")
    ax.bar(x + width/2, actuals, width, label="Actual", color=BLUE, alpha=0.7, edgecolor="white")

    # Beat/miss indicators
    for i in range(len(quarters)):
        diff = actuals[i] - estimates[i]
        color = GREEN if diff >= 0 else RED
        symbol = "+" if diff >= 0 else ""
        ax.text(x[i] + width/2, actuals[i] + 0.02, f"{symbol}{diff:.2f}",
                ha="center", va="bottom", fontsize=7, color=color, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([q[0] for q in quarters], rotation=45, ha="right")
    ax.set_ylabel("EPS ($)")
    ax.set_title(f"{ticker} — EPS Estimate vs Actual (Last {len(quarters)} Quarters)", fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
    fig.tight_layout()
    return fig_to_base64(fig)


def chart_10_event_timeline() -> str:
    """Event Timeline — price with earnings, insider trades, large drops."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), height_ratios=[3, 1],
                                     sharex=True, gridspec_kw={"hspace": 0.08})

    ax1.plot(h2y_dates, h2y_close, color=BLUE, linewidth=1.5)
    ax1.set_ylabel("Price ($)")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax1.set_title(f"{ticker} — Event Timeline (2-Year)", fontweight="bold")

    # Earnings dates on price chart
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None:
            continue
        edate = parse_dates([ed_dates_raw[i]])[0]
        if edate < h2y_dates[0] or edate > h2y_dates[-1]:
            continue
        closest_idx = min(range(len(h2y_dates)), key=lambda j: abs((h2y_dates[j] - edate).days))
        ax1.plot(h2y_dates[closest_idx], h2y_close[closest_idx], marker="D",
                 color=GREEN, markersize=8, zorder=10)

    # Large drops (>3% single day)
    for i in range(1, len(h2y_close)):
        ret = (h2y_close[i] / h2y_close[i-1] - 1) * 100
        if ret < -3:
            ax1.plot(h2y_dates[i], h2y_close[i], marker="v",
                     color=RED, markersize=10, zorder=10)
            ax1.annotate(f"{ret:.1f}%", (h2y_dates[i], h2y_close[i]),
                         textcoords="offset points", xytext=(0, -15),
                         fontsize=7, color=RED, ha="center")

    # Timeline strip below
    ax2.set_ylim(0, 3)
    ax2.set_yticks([0.5, 1.5, 2.5])
    ax2.set_yticklabels(["Drops", "Insider", "Earnings"], fontsize=9)
    ax2.set_xlim(h2y_dates[0], h2y_dates[-1])

    # Earnings on timeline
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None:
            continue
        edate = parse_dates([ed_dates_raw[i]])[0]
        if edate < h2y_dates[0] or edate > h2y_dates[-1]:
            continue
        ax2.plot(edate, 2.5, marker="D", color=GREEN, markersize=8)

    # Insider trades on timeline
    for i in range(len(it["Start Date"])):
        d = it["Start Date"][i]
        if d is None:
            continue
        try:
            tdate = datetime.strptime(d[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        if tdate < h2y_dates[0] or tdate > h2y_dates[-1]:
            continue
        val = safe_float(it["Value"][i])
        size = max(20, min(200, val / 1e6 * 50)) if val > 0 else 20
        ax2.scatter(tdate, 1.5, s=size, color=RED, alpha=0.5, edgecolors=RED, linewidths=0.5)

    # Large drops on timeline
    for i in range(1, len(h2y_close)):
        ret = (h2y_close[i] / h2y_close[i-1] - 1) * 100
        if ret < -3:
            ax2.plot(h2y_dates[i], 0.5, marker="v", color=RED, markersize=8)

    for spine in ax2.spines.values():
        spine.set_alpha(0.3)
    ax2.grid(axis="y", alpha=0.2)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_11_ddl_exposure() -> str:
    """DDL Exposure Area — max damages at each point."""
    fig, ax = plt.subplots(figsize=(14, 5))

    close_arr = np.array(h2y_close)
    high_arr = np.array(h2y_high)
    shares_out = safe_float(info.get("sharesOutstanding", 0))

    # DDL = (running high - current price) * shares outstanding
    running_high = np.maximum.accumulate(high_arr)
    price_drop = running_high - close_arr
    ddl_exposure = price_drop * shares_out

    ax.fill_between(h2y_dates, ddl_exposure / 1e9, 0, color=RED, alpha=0.3)
    ax.plot(h2y_dates, ddl_exposure / 1e9, color=RED, linewidth=1)

    # Annotate max exposure
    max_idx = int(np.argmax(ddl_exposure))
    max_val = ddl_exposure[max_idx] / 1e9
    ax.annotate(f"Max: ${max_val:.1f}B\n{h2y_dates[max_idx].strftime('%b %d, %Y')}\nDrop: ${price_drop[max_idx]:.2f}/share",
                (h2y_dates[max_idx], max_val),
                textcoords="offset points", xytext=(-60, -30),
                fontsize=9, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))

    # Current exposure
    current_exp = ddl_exposure[-1] / 1e9
    ax.annotate(f"Current: ${current_exp:.1f}B",
                (h2y_dates[-1], current_exp),
                textcoords="offset points", xytext=(-80, 10),
                fontsize=9, color=DARK_GRAY, fontweight="bold")

    ax.set_title(f"{ticker} — Securities Class Action DDL Exposure (2-Year)", fontweight="bold")
    ax.set_ylabel("Max Damages Exposure ($B)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0fB"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_12_volatility_cone() -> str:
    """Volatility Cone — expected price ranges at future horizons."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Plot last 6 months of price
    lookback = min(126, len(h2y_dates))
    recent_dates = h2y_dates[-lookback:]
    recent_close = h2y_close[-lookback:]
    ax.plot(recent_dates, recent_close, color=BLUE, linewidth=2, label="Price")

    # Calculate historical volatility (annualized)
    returns = np.diff(np.log(np.array(h2y_close[-252:])))  # last year
    daily_vol = np.std(returns)
    annual_vol = daily_vol * np.sqrt(252)

    current_price = h2y_close[-1]
    last_date = h2y_dates[-1]

    horizons = [30, 60, 90, 180]
    future_dates = [last_date + __import__("datetime").timedelta(days=d * 365/252) for d in horizons]

    # Build cone
    cone_dates = [last_date] + future_dates
    upper_1s = [current_price]
    lower_1s = [current_price]
    upper_2s = [current_price]
    lower_2s = [current_price]

    for h in horizons:
        vol_h = daily_vol * np.sqrt(h)
        upper_1s.append(current_price * np.exp(vol_h))
        lower_1s.append(current_price * np.exp(-vol_h))
        upper_2s.append(current_price * np.exp(2 * vol_h))
        lower_2s.append(current_price * np.exp(-2 * vol_h))

    ax.fill_between(cone_dates, lower_2s, upper_2s, color=RED, alpha=0.08, label="2-sigma range")
    ax.fill_between(cone_dates, lower_1s, upper_1s, color=ORANGE, alpha=0.15, label="1-sigma range")
    ax.plot(cone_dates, upper_1s, color=ORANGE, linewidth=1, linestyle="--", alpha=0.6)
    ax.plot(cone_dates, lower_1s, color=ORANGE, linewidth=1, linestyle="--", alpha=0.6)
    ax.plot(cone_dates, upper_2s, color=RED, linewidth=1, linestyle=":", alpha=0.4)
    ax.plot(cone_dates, lower_2s, color=RED, linewidth=1, linestyle=":", alpha=0.4)

    # Annotate endpoints
    for label, vals, color in [("1-sigma", upper_1s, ORANGE), ("2-sigma", upper_2s, RED)]:
        ax.annotate(f"${vals[-1]:.0f}", (cone_dates[-1], vals[-1]),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=8, color=color)
        ax.annotate(f"${[lower_1s, lower_2s][["1-sigma", "2-sigma"].index(label)][-1]:.0f}",
                    (cone_dates[-1], [lower_1s, lower_2s][["1-sigma", "2-sigma"].index(label)][-1]),
                    textcoords="offset points", xytext=(5, -10),
                    fontsize=8, color=color)

    # Horizon labels
    for i, (h, fd) in enumerate(zip(horizons, future_dates)):
        ax.axvline(fd, color=GRAY, linewidth=0.5, linestyle=":", alpha=0.5)
        ax.text(fd, ax.get_ylim()[1], f"{h}d", ha="center", va="bottom",
                fontsize=8, color=DARK_GRAY)

    ax.set_title(f"{ticker} — Volatility Cone (Ann. Vol: {annual_vol*100:.1f}%)", fontweight="bold")
    ax.set_ylabel("Price ($)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_13_rolling_beta() -> str:
    """Rolling Beta — 60-day rolling beta vs S&P 500."""
    fig, ax = plt.subplots(figsize=(14, 5))

    # Align dates
    min_len = min(len(h2y_close), len(spy2y_close))
    aapl_arr = np.array(h2y_close[:min_len])
    spy_arr = np.array(spy2y_close[:min_len])
    dates_arr = h2y_dates[:min_len]

    aapl_ret = np.diff(np.log(aapl_arr))
    spy_ret = np.diff(np.log(spy_arr))

    window = 60
    rolling_beta = []
    beta_dates = []

    for i in range(window, len(aapl_ret)):
        a = aapl_ret[i-window:i]
        s = spy_ret[i-window:i]
        cov = np.cov(a, s)
        beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 1.0
        rolling_beta.append(beta)
        beta_dates.append(dates_arr[i+1])

    ax.plot(beta_dates, rolling_beta, color=BLUE, linewidth=1.5)
    ax.axhline(1.0, color=DARK_GRAY, linewidth=1, linestyle="--", label="Beta = 1.0")
    ax.fill_between(beta_dates, rolling_beta, 1.0,
                     where=[b > 1 for b in rolling_beta],
                     color=RED, alpha=0.1, interpolate=True)
    ax.fill_between(beta_dates, rolling_beta, 1.0,
                     where=[b <= 1 for b in rolling_beta],
                     color=GREEN, alpha=0.1, interpolate=True)

    # Current beta from info
    current_beta = safe_float(info.get("beta", 1.0))
    ax.annotate(f"Current: {current_beta:.2f} (reported)\nRolling: {rolling_beta[-1]:.2f}",
                (beta_dates[-1], rolling_beta[-1]),
                textcoords="offset points", xytext=(-100, 20),
                fontsize=9, color=BLUE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))

    ax.set_title(f"{ticker} — 60-Day Rolling Beta vs S&P 500 (2-Year)", fontweight="bold")
    ax.set_ylabel("Beta")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_14_short_interest() -> str:
    """Short Interest — current level overlaid on price."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 5), height_ratios=[2, 1],
                                     sharex=True, gridspec_kw={"hspace": 0.05})

    ax1.plot(h2y_dates, h2y_close, color=BLUE, linewidth=1.5)
    ax1.set_ylabel("Price ($)")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax1.set_title(f"{ticker} — Short Interest Context (2-Year)", fontweight="bold")

    si_pct = safe_float(info.get("shortPercentOfFloat", 0)) * 100
    si_shares = safe_float(info.get("sharesShort", 0))
    si_ratio = safe_float(info.get("shortRatio", 0))

    # Draw as horizontal line (single data point)
    ax2.axhline(si_pct, color=ORANGE, linewidth=2, label=f"Short % of Float: {si_pct:.2f}%")
    ax2.fill_between(h2y_dates, si_pct, 0, color=ORANGE, alpha=0.15)

    ax2.set_ylabel("Short %")
    ax2.set_ylim(0, max(si_pct * 3, 2))

    # Add text annotation
    ax2.text(h2y_dates[len(h2y_dates)//2], si_pct * 1.5,
             f"Short Shares: {si_shares/1e6:.1f}M | Days to Cover: {si_ratio:.1f} | Short %: {si_pct:.2f}%",
             ha="center", va="bottom", fontsize=10, color=ORANGE, fontweight="bold")

    ax2.legend(loc="upper right", fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_15_excess_return() -> str:
    """Excess Return vs Sector — cumulated daily alpha."""
    fig, ax = plt.subplots(figsize=(14, 5))

    min_len = min(len(h2y_close), len(sec2y_close))
    aapl_arr = np.array(h2y_close[:min_len])
    sec_arr = np.array(sec2y_close[:min_len])

    aapl_ret = np.diff(aapl_arr) / aapl_arr[:-1] * 100
    sec_ret = np.diff(sec_arr) / sec_arr[:-1] * 100
    excess = aapl_ret - sec_ret
    cum_excess = np.cumsum(excess)

    dates = h2y_dates[1:min_len]

    ax.fill_between(dates, cum_excess, 0,
                     where=cum_excess >= 0, color=GREEN, alpha=0.2, interpolate=True)
    ax.fill_between(dates, cum_excess, 0,
                     where=cum_excess < 0, color=RED, alpha=0.2, interpolate=True)
    ax.plot(dates, cum_excess, color=BLUE, linewidth=1.5)
    ax.axhline(0, color=DARK_GRAY, linewidth=0.5)

    # Annotate largest drops (potential corrective disclosure events)
    # Find steepest 5-day declines
    for window in [5]:
        for i in range(window, len(cum_excess)):
            drop = cum_excess[i] - cum_excess[i - window]
            if drop < -5:  # >5pp drop in 5 days
                ax.annotate(f"{drop:.1f}pp",
                            (dates[i], cum_excess[i]),
                            textcoords="offset points", xytext=(0, -15),
                            fontsize=7, color=RED, ha="center")

    ax.set_title(f"{ticker} — Cumulative Excess Return vs {sector_etf} (2-Year)", fontweight="bold")
    ax.set_ylabel("Cumulative Excess Return (pp)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f pp"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_16_market_cap_journey() -> str:
    """Market Cap Journey — area chart of market cap over time."""
    fig, ax = plt.subplots(figsize=(14, 5))

    shares_out = safe_float(info.get("sharesOutstanding", 0))
    mcap = np.array(h5y_close) * shares_out

    ax.fill_between(h5y_dates, mcap / 1e12, color=BLUE, alpha=0.15)
    ax.plot(h5y_dates, mcap / 1e12, color=BLUE, linewidth=1.5)

    # Annotate milestones
    max_idx = int(np.argmax(mcap))
    min_idx = int(np.argmin(mcap))

    ax.annotate(f"Peak: ${mcap[max_idx]/1e12:.2f}T\n{h5y_dates[max_idx].strftime('%b %Y')}",
                (h5y_dates[max_idx], mcap[max_idx]/1e12),
                textcoords="offset points", xytext=(-60, 10),
                fontsize=9, color=BLUE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))

    ax.annotate(f"Trough: ${mcap[min_idx]/1e12:.2f}T\n{h5y_dates[min_idx].strftime('%b %Y')}",
                (h5y_dates[min_idx], mcap[min_idx]/1e12),
                textcoords="offset points", xytext=(20, -10),
                fontsize=9, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))

    # Current
    current_mcap = mcap[-1] / 1e12
    ax.annotate(f"Current: ${current_mcap:.2f}T",
                (h5y_dates[-1], current_mcap),
                textcoords="offset points", xytext=(-80, 10),
                fontsize=9, color=DARK_GRAY, fontweight="bold")

    ax.set_title(f"{ticker} — Market Capitalization Journey (5-Year)", fontweight="bold")
    ax.set_ylabel("Market Cap ($T)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.1fT"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_17_52w_range_position() -> str:
    """52-Week Range Position — monthly heatmap strip."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 5), height_ratios=[3, 1],
                                     sharex=True, gridspec_kw={"hspace": 0.08})

    ax1.plot(h5y_dates, h5y_close, color=BLUE, linewidth=1.5)
    ax1.set_ylabel("Price ($)")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax1.set_title(f"{ticker} — 52-Week Range Position (5-Year)", fontweight="bold")

    # Calculate trailing 52W range position for each day
    close_arr = np.array(h5y_close)
    high_arr = np.array(h5y_high)
    low_arr = np.array(h5y_low)
    positions = []
    pos_dates = []

    for i in range(252, len(close_arr)):
        trailing_high = np.max(high_arr[i-252:i+1])
        trailing_low = np.min(low_arr[i-252:i+1])
        rng = trailing_high - trailing_low
        if rng > 0:
            pos = (close_arr[i] - trailing_low) / rng * 100
        else:
            pos = 50
        positions.append(pos)
        pos_dates.append(h5y_dates[i])

    # Create heatmap strip using scatter
    colors_map = plt.cm.RdYlGn  # Red at bottom, Green at top
    norm = plt.Normalize(0, 100)
    ax2.scatter(pos_dates, [0.5] * len(pos_dates), c=positions,
                cmap=colors_map, norm=norm, s=8, marker="s")

    # Also plot as line
    ax2.plot(pos_dates, [p/100 for p in positions], color=DARK_GRAY, linewidth=0.5, alpha=0.5)

    ax2.set_ylabel("52W %")
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_yticks([0, 0.5, 1.0])
    ax2.set_yticklabels(["Low", "Mid", "High"])

    # Current position
    if positions:
        current_pos = positions[-1]
        ax2.text(pos_dates[-1], 0.9, f"Current: {current_pos:.0f}%",
                 ha="right", va="top", fontsize=9, color=DARK_GRAY, fontweight="bold")

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate()
    return fig_to_base64(fig)


def chart_18_earnings_quality_lollipop() -> str:
    """Earnings Quality Strip — lollipop chart of EPS actual vs estimate."""
    fig, ax = plt.subplots(figsize=(14, 5))

    quarters = []
    for i in range(len(ed_dates_raw)):
        if ed_act[i] is None or ed_est[i] is None:
            continue
        edate = parse_dates([ed_dates_raw[i]])[0]
        quarters.append((edate.strftime("%b '%y"), safe_float(ed_est[i]),
                        safe_float(ed_act[i]), safe_float(ed_surp[i])))

    quarters.reverse()
    quarters = quarters[-12:]  # Last 12 quarters

    x = np.arange(len(quarters))
    estimates = [q[1] for q in quarters]
    actuals = [q[2] for q in quarters]

    # Estimate line
    ax.plot(x, estimates, color=GRAY, linewidth=2, linestyle="--", label="Estimate", zorder=3)
    ax.scatter(x, estimates, color=GRAY, s=40, zorder=4)

    # Lollipops from estimate to actual
    for i in range(len(quarters)):
        color = GREEN if actuals[i] >= estimates[i] else RED
        ax.plot([i, i], [estimates[i], actuals[i]], color=color, linewidth=2, zorder=5)
        ax.scatter(i, actuals[i], color=color, s=80, zorder=6, edgecolors="white", linewidths=1)
        diff = actuals[i] - estimates[i]
        ax.text(i, actuals[i] + (0.03 if diff >= 0 else -0.05),
                f"{'+'if diff>=0 else ''}{diff:.2f}",
                ha="center", va="bottom" if diff >= 0 else "top",
                fontsize=8, color=color, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([q[0] for q in quarters], rotation=45, ha="right")
    ax.set_ylabel("EPS ($)")
    ax.set_title(f"{ticker} — Earnings Quality: Estimate vs Actual (Lollipop)", fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))

    # Beat streak annotation
    beats = sum(1 for q in quarters if q[2] >= q[1])
    ax.text(0.98, 0.02, f"Beat {beats}/{len(quarters)} quarters",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=11, color=GREEN if beats > len(quarters)//2 else RED,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=GRAY, alpha=0.8))

    fig.tight_layout()
    return fig_to_base64(fig)


def chart_19_revenue_margin() -> str:
    """Revenue + Margin Trend — dual-axis quarterly view."""
    fig, ax1 = plt.subplots(figsize=(14, 5))

    periods = qinc["periods"]
    line_items = qinc["line_items"]

    rev_raw = line_items.get("Total Revenue", [])
    ebitda_raw = line_items.get("EBITDA", [])

    if not rev_raw or not ebitda_raw:
        return placeholder_chart("Revenue + Margin", "Quarterly income data not available")

    revenues = [safe_float(v) for v in rev_raw]
    ebitdas = [safe_float(v) for v in ebitda_raw]

    # Parse period dates
    period_dates = []
    for p in periods:
        try:
            period_dates.append(datetime.strptime(p, "%Y-%m-%d"))
        except (ValueError, TypeError):
            period_dates.append(datetime(2020, 1, 1))

    # Reverse for chronological order
    period_dates_r = list(reversed(period_dates))
    revenues_r = list(reversed(revenues))
    ebitdas_r = list(reversed(ebitdas))

    x = np.arange(len(period_dates_r))
    labels = [d.strftime("%b '%y") for d in period_dates_r]

    # Revenue bars
    ax1.bar(x, [r/1e9 for r in revenues_r], color=BLUE, alpha=0.6, label="Revenue ($B)")
    ax1.set_ylabel("Revenue ($B)", color=BLUE)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0fB"))
    ax1.tick_params(axis="y", labelcolor=BLUE)

    # EBITDA Margin line on secondary axis
    ax2 = ax1.twinx()
    margins = [e/r*100 if r != 0 else 0 for e, r in zip(ebitdas_r, revenues_r)]
    ax2.plot(x, margins, color=ORANGE, linewidth=2.5, marker="o", markersize=6, label="EBITDA Margin (%)")
    ax2.set_ylabel("EBITDA Margin (%)", color=ORANGE)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.tick_params(axis="y", labelcolor=ORANGE)

    # Margin labels
    for i, m in enumerate(margins):
        ax2.text(i, m + 0.5, f"{m:.1f}%", ha="center", va="bottom",
                 fontsize=8, color=ORANGE, fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.set_title(f"{ticker} — Quarterly Revenue & EBITDA Margin", fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", framealpha=0.9)

    fig.tight_layout()
    return fig_to_base64(fig)


def chart_20_composite_risk_strip() -> str:
    """Composite Risk Strip — 5 stacked sparklines for one-glance dashboard."""
    fig, axes = plt.subplots(5, 1, figsize=(14, 8), sharex=True,
                              gridspec_kw={"hspace": 0.15})

    min_len = min(len(h2y_dates), len(h2y_close), len(h2y_volume))
    dates = h2y_dates[:min_len]
    close = np.array(h2y_close[:min_len])
    volume = np.array(h2y_volume[:min_len])

    # 1. Price
    ax = axes[0]
    ax.plot(dates, close, color=BLUE, linewidth=1.2)
    ax.fill_between(dates, close, close.min(), alpha=0.1, color=BLUE)
    ax.set_ylabel("Price", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
    ax.set_title(f"{ticker} — Composite Risk Dashboard (2-Year)", fontweight="bold", fontsize=13)

    # 2. Volume (normalized)
    ax = axes[1]
    vol_norm = volume / np.mean(volume)
    colors = [ORANGE if v > 2 else GRAY for v in vol_norm]
    ax.bar(dates, vol_norm, color=colors, width=1.5, alpha=0.7)
    ax.axhline(2, color=RED, linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_ylabel("Vol/Avg", fontsize=9)

    # 3. Insider Net (cumulative)
    ax = axes[2]
    insider_by_date: dict[str, float] = {}
    for i in range(len(it["Start Date"])):
        d = it["Start Date"][i]
        if d is None:
            continue
        text = it["Text"][i] if it["Text"][i] else ""
        shr = safe_float(it["Shares"][i])
        val = safe_float(it["Value"][i])
        if "Sale" in text or (val > 0 and "Gift" not in text):
            shr = -shr
        elif "Gift" in text:
            shr = -shr
        insider_by_date[d[:10]] = insider_by_date.get(d[:10], 0) + shr

    cum = 0.0
    cum_series = []
    sorted_dates = sorted(insider_by_date.keys())
    idx = 0
    for dt in dates:
        ds = dt.strftime("%Y-%m-%d")
        while idx < len(sorted_dates) and sorted_dates[idx] <= ds:
            cum += insider_by_date[sorted_dates[idx]]
            idx += 1
        cum_series.append(cum)

    cum_arr = np.array(cum_series)
    ax.fill_between(dates, cum_arr, 0,
                     where=cum_arr >= 0, color=GREEN, alpha=0.3)
    ax.fill_between(dates, cum_arr, 0,
                     where=cum_arr < 0, color=RED, alpha=0.3)
    ax.plot(dates, cum_arr, color=DARK_GRAY, linewidth=0.8)
    ax.set_ylabel("Insider\nNet", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K"))

    # 4. Short Interest (flat line with current value)
    ax = axes[3]
    si_pct = safe_float(info.get("shortPercentOfFloat", 0)) * 100
    ax.axhline(si_pct, color=ORANGE, linewidth=1.5)
    ax.fill_between(dates, si_pct, 0, color=ORANGE, alpha=0.1)
    ax.set_ylabel("Short %", fontsize=9)
    ax.set_ylim(0, max(si_pct * 3, 2))
    ax.text(dates[-1], si_pct, f" {si_pct:.2f}%", va="center", fontsize=8, color=ORANGE, fontweight="bold")

    # 5. Rolling Volatility (20-day)
    ax = axes[4]
    returns = np.diff(np.log(close))
    roll_vol = []
    for i in range(len(returns)):
        start = max(0, i - 19)
        rv = np.std(returns[start:i+1]) * np.sqrt(252) * 100
        roll_vol.append(rv)

    vol_dates = dates[1:]
    roll_vol_arr = np.array(roll_vol)
    ax.plot(vol_dates, roll_vol_arr, color=RED, linewidth=1)
    ax.fill_between(vol_dates, roll_vol_arr, 0,
                     where=roll_vol_arr > np.mean(roll_vol_arr),
                     color=RED, alpha=0.2, interpolate=True)
    ax.fill_between(vol_dates, roll_vol_arr, 0,
                     where=roll_vol_arr <= np.mean(roll_vol_arr),
                     color=GREEN, alpha=0.1, interpolate=True)
    ax.axhline(np.mean(roll_vol_arr), color=DARK_GRAY, linewidth=0.5, linestyle="--")
    ax.set_ylabel("Vol %", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Chart metadata
# ---------------------------------------------------------------------------

CHARTS = [
    {
        "id": "chart-01",
        "num": 1,
        "title": "Relative Performance (% Return)",
        "category": "Multi-Line Performance",
        "description": "AAPL vs sector ETF (XLK) vs S&P 500, indexed to 0% from 2 years ago. Earnings dates shown as diamonds with surprise percentage labels. Google Finance-style green/red fill under the company line.",
        "why": "Shows whether the stock has diverged from its sector and the broad market -- a key factor in Securities Class Action (SCA) loss causation analysis. Large divergences often precede corrective disclosure events. Earnings surprises overlaid show whether the market was repeatedly caught off-guard.",
        "generator": chart_01_relative_performance,
    },
    {
        "id": "chart-02",
        "num": 2,
        "title": "5-Year Price + 50/200 SMA",
        "category": "Multi-Line Performance",
        "description": "Absolute price with 50-day and 200-day simple moving averages over 5 years. Golden cross (bullish) and death cross (bearish) crossover points are highlighted.",
        "why": "Moving average crossovers mark regime changes in investor sentiment. A death cross during a class period strengthens plaintiff arguments about deteriorating conditions. SMA trends also affect D&O pricing models since they influence market-adjusted damages calculations.",
        "generator": chart_02_price_sma,
    },
    {
        "id": "chart-03",
        "num": 3,
        "title": "Drawdown From Peak",
        "category": "Multi-Line Performance",
        "description": "Percentage decline from the running all-time high at every point over 5 years. Shows depth and duration of each pullback.",
        "why": "Drawdown depth directly maps to potential SCA damages -- deeper drawdowns mean larger maximum dollar-loss exposure. Duration reveals whether declines were sudden (corrective disclosure) or gradual (market-wide). The worst drawdown sets the ceiling for DDL claims.",
        "generator": chart_03_drawdown,
    },
    {
        "id": "chart-04",
        "num": 4,
        "title": "Normalized to 100 Comparison",
        "category": "Multi-Line Performance",
        "description": "AAPL, sector (XLK), and S&P 500 all rebased to 100 at the 5-year start date. Shows long-term divergence between the company and its benchmarks.",
        "why": "Normalization strips out price-level differences and reveals true relative outperformance/underperformance. A company trading well above its sector may be more vulnerable to a corrective event -- the higher they climb, the further they fall. Persistent underperformance may indicate ongoing undisclosed issues.",
        "generator": chart_04_normalized_100,
    },
    {
        "id": "chart-05",
        "num": 5,
        "title": "Volume with Spike Detection",
        "category": "Volume & Trading",
        "description": "Volume bars colored orange when exceeding 2x the 20-day average. Price shown in upper panel for context. Top 5 volume spikes labeled by date.",
        "why": "Abnormal volume often accompanies material information events -- earnings, analyst downgrades, news breaks, or pre-announcement trading. Volume spikes that precede price drops can indicate information asymmetry, a key element in insider trading and Section 10b-5 claims.",
        "generator": chart_05_volume_spikes,
    },
    {
        "id": "chart-06",
        "num": 6,
        "title": "Insider Transaction Scatter",
        "category": "Volume & Trading",
        "description": "Price line with circles at insider trade dates. Circle size is proportional to dollar value. Red = sale, gray = gift/grant. The 5 largest transactions are labeled by name and value.",
        "why": "Insider selling patterns are the single strongest predictor of D&O claims. Sales clustered before a stock drop create the appearance of trading on material non-public information (MNPI). Courts look at timing, magnitude, and whether sales deviated from historical patterns.",
        "generator": chart_06_insider_scatter,
    },
    {
        "id": "chart-07",
        "num": 7,
        "title": "Net Insider Activity (Cumulative)",
        "category": "Volume & Trading",
        "description": "Running cumulative sum of insider shares traded over 2 years. Sales shown as negative (red area), buys/grants as positive (green). Plotted below price for correlation.",
        "why": "A steadily declining cumulative line means insiders are consistently reducing exposure -- a bearish signal that plaintiff attorneys cite as evidence of management lacking confidence. Sudden acceleration of sales before bad news is even more damning.",
        "generator": chart_07_cumulative_insider,
    },
    {
        "id": "chart-08",
        "num": 8,
        "title": "Earnings Reaction Waterfall",
        "category": "Earnings & Events",
        "description": "Horizontal bars for each earnings quarter: EPS surprise percentage (solid) vs 1-day price reaction (hatched). Green = beat/positive, red = miss/negative.",
        "why": "The disconnect between earnings surprise and market reaction reveals how much the market trusts management guidance. Consistent beats with negative reactions suggest investors see earnings quality issues. Large negative reactions to small misses indicate stretched valuations vulnerable to SCA triggers.",
        "generator": chart_08_earnings_waterfall,
    },
    {
        "id": "chart-09",
        "num": 9,
        "title": "Guidance vs Actual (EPS Strip)",
        "category": "Earnings & Events",
        "description": "Grouped bars showing analyst consensus EPS estimate vs actual reported EPS for each quarter. Beat magnitude shown above each bar pair.",
        "why": "Consistent narrow beats suggest earnings management -- hitting consensus by just enough. Wide beats suggest sandbagged guidance. Any miss after a long streak of beats is a common SCA trigger because the market expected the pattern to continue.",
        "generator": chart_09_guidance_vs_actual,
    },
    {
        "id": "chart-10",
        "num": 10,
        "title": "Event Timeline",
        "category": "Earnings & Events",
        "description": "Price chart with a dense timeline strip below showing three event lanes: earnings dates (green diamonds), insider trades (red circles sized by dollar value), and significant daily drops >3% (red triangles).",
        "why": "Temporal clustering of events is a forensic red flag. Insider sales followed by large drops, or earnings beats followed by unusual volume, create the narrative scaffolding for SCA complaints. This view compresses multiple data dimensions into one scannable strip.",
        "generator": chart_10_event_timeline,
    },
    {
        "id": "chart-11",
        "num": 11,
        "title": "DDL Exposure Area",
        "category": "Risk & Exposure",
        "description": "Dollar-loss damages (DDL) exposure at each point: (running high price - current price) x shares outstanding. Shows the maximum theoretical SCA damages envelope over 2 years.",
        "why": "DDL is the primary metric insurers and plaintiff attorneys use to size potential securities class action settlements. This chart shows when the company was most vulnerable -- peaks correspond to periods where the stock had fallen furthest from its high while having the most shares outstanding.",
        "generator": chart_11_ddl_exposure,
    },
    {
        "id": "chart-12",
        "num": 12,
        "title": "Volatility Cone",
        "category": "Risk & Exposure",
        "description": "From the current price, an expanding cone shows +/- 1-sigma and 2-sigma expected price ranges at 30, 60, 90, and 180-day horizons, based on trailing 1-year historical volatility.",
        "why": "The volatility cone quantifies severity windows for underwriters. A wide cone means the stock could easily move enough to trigger an SCA within the policy period. Underwriters can compare the 2-sigma downside against policy limits to assess whether the D&O tower is adequately sized.",
        "generator": chart_12_volatility_cone,
    },
    {
        "id": "chart-13",
        "num": 13,
        "title": "Rolling Beta",
        "category": "Risk & Exposure",
        "description": "60-day rolling beta vs S&P 500 over 2 years. Red fill when beta > 1 (amplifies market moves), green fill when < 1 (dampens them). Reference line at beta = 1.",
        "why": "Beta affects loss causation defense in SCA litigation. A high-beta stock's decline can be partially attributed to market-wide moves, reducing plaintiff damages. Regime changes in beta (e.g., from 0.8 to 1.5) may indicate increased systematic risk or a company-specific event that changed its correlation structure.",
        "generator": chart_13_rolling_beta,
    },
    {
        "id": "chart-14",
        "num": 14,
        "title": "Short Interest Context",
        "category": "Risk & Exposure",
        "description": "Price chart with short interest data below. Since only current short interest is available (not historical), it is displayed as a constant reference level with key metrics: short shares, days to cover, and short % of float.",
        "why": "Elevated short interest signals that sophisticated investors are betting against the stock -- a leading indicator of potential corrective events. High short ratios (days to cover) mean short sellers are committed to their thesis. Rising SI before bad news suggests information leakage.",
        "generator": chart_14_short_interest,
    },
    {
        "id": "chart-15",
        "num": 15,
        "title": "Excess Return vs Sector",
        "category": "Comparative",
        "description": "Daily AAPL return minus sector (XLK) return, cumulated over 2 years. Positive values (green fill) = outperforming sector. Rapid drops annotated as potential corrective disclosure events.",
        "why": "Excess return stripping out sector moves isolates company-specific alpha/alpha-decay. Sudden drops in cumulative excess return are strong candidates for corrective disclosure events -- the stock fell more than its peers, suggesting company-specific bad news rather than market-wide turbulence.",
        "generator": chart_15_excess_return,
    },
    {
        "id": "chart-16",
        "num": 16,
        "title": "Market Cap Journey",
        "category": "Comparative",
        "description": "Area chart of market capitalization (price x shares outstanding) over 5 years, with peak, trough, and current values annotated.",
        "why": "Market cap determines the stakes of D&O litigation -- larger companies attract more plaintiff attorney attention, face larger settlements, and need higher D&O limits. The journey from peak to trough represents the maximum aggregate investor loss, which drives settlement demand sizing.",
        "generator": chart_16_market_cap_journey,
    },
    {
        "id": "chart-17",
        "num": 17,
        "title": "52-Week Range Position",
        "category": "Comparative",
        "description": "For each trading day, shows where the stock sits within its trailing 52-week high-low range (0% = at 52W low, 100% = at 52W high). Displayed as a color-coded heatmap strip below the price chart.",
        "why": "Stocks trading near their 52-week low are in the 'danger zone' for D&O claims -- any further decline amplifies DDL. Stocks consistently near highs have further to fall. The transition from green (near highs) to red (near lows) often marks the onset of a class period.",
        "generator": chart_17_52w_range_position,
    },
    {
        "id": "chart-18",
        "num": 18,
        "title": "Earnings Quality (Lollipop)",
        "category": "Forensic",
        "description": "Lollipop chart showing EPS actual vs estimate for the last 12 quarters. Green dots above the estimate line = beat, red below = miss. Beat magnitude labeled on each stick.",
        "why": "This is the forensic earnings view. Patterns in beat magnitude reveal earnings management: consistently tiny beats suggest 'just enough' management. A long beat streak followed by a miss is the classic SCA complaint narrative. The lollipop format makes the pattern immediately visible.",
        "generator": chart_18_earnings_quality_lollipop,
    },
    {
        "id": "chart-19",
        "num": 19,
        "title": "Revenue + EBITDA Margin Trend",
        "category": "Forensic",
        "description": "Dual-axis chart with quarterly revenue bars and EBITDA margin percentage line. Shows whether revenue growth is sustainable or coming at the expense of profitability.",
        "why": "Revenue growth with declining margins is a D&O red flag -- it may indicate the company is buying growth through unsustainable spending, channel stuffing, or aggressive revenue recognition. Margin compression often precedes earnings misses, which trigger SCA filings.",
        "generator": chart_19_revenue_margin,
    },
    {
        "id": "chart-20",
        "num": 20,
        "title": "Composite Risk Dashboard",
        "category": "Forensic",
        "description": "Five stacked sparkline strips showing Price, Volume (normalized to average), Cumulative Insider Net, Short Interest %, and Rolling Volatility. All aligned on the same 2-year time axis for cross-correlation analysis.",
        "why": "This is the one-glance risk dashboard. When multiple strips turn red simultaneously -- volume spikes, insider selling accelerates, volatility rises -- it signals a convergence of risk factors that often precedes a D&O claim. The composite view reveals temporal correlations invisible in individual charts.",
        "generator": chart_20_composite_risk_strip,
    },
]


# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------

def generate_html() -> str:
    """Generate the complete HTML page with all 20 charts."""
    chart_sections = []
    toc_items = []

    categories = {}
    for chart in CHARTS:
        cat = chart["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(chart)

    for chart in CHARTS:
        print(f"  Generating chart {chart['num']}: {chart['title']}...")
        try:
            img_b64 = chart["generator"]()
        except Exception as e:
            print(f"    ERROR: {e}")
            img_b64 = placeholder_chart(chart["title"], f"Error: {e}")

        toc_items.append(f'<li><a href="#{chart["id"]}">{chart["num"]}. {chart["title"]}</a> <span class="cat">{chart["category"]}</span></li>')

        chart_sections.append(f'''
        <div class="chart-section" id="{chart["id"]}">
            <div class="chart-header">
                <span class="chart-num">{chart["num"]}</span>
                <div>
                    <h3>{chart["title"]}</h3>
                    <span class="chart-category">{chart["category"]}</span>
                </div>
            </div>
            <p class="chart-desc">{chart["description"]}</p>
            <p class="chart-why"><strong>D&amp;O Underwriting Relevance:</strong> {chart["why"]}</p>
            <div class="chart-img">
                <img src="data:image/png;base64,{img_b64}" alt="{chart["title"]}" />
            </div>
            <div class="comment-box">
                <div class="comment-label">Notes / What Could Be Improved</div>
                <div contenteditable="true" class="comment-area" placeholder="Add your notes here..."></div>
            </div>
        </div>
        ''')

    # Current price info
    current_price = safe_float(info.get("currentPrice", 0))
    market_cap = safe_float(info.get("marketCap", 0))
    high_52w = safe_float(info.get("fiftyTwoWeekHigh", 0))
    low_52w = safe_float(info.get("fiftyTwoWeekLow", 0))
    beta = safe_float(info.get("beta", 0))

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} — D&O Underwriting Chart Lab (20 Visualizations)</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: Arial, 'DejaVu Sans', sans-serif; background: #F9FAFB; color: #1F2937; line-height: 1.6; }}

    .header {{
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white; padding: 32px 40px;
    }}
    .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
    .header .subtitle {{ color: #94A3B8; font-size: 14px; }}
    .header .stats {{
        display: flex; gap: 32px; margin-top: 16px; flex-wrap: wrap;
    }}
    .header .stat {{
        background: rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 16px;
    }}
    .header .stat .label {{ font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }}
    .header .stat .value {{ font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }}

    .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 40px; }}

    .toc {{
        background: white; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 24px 32px; margin-bottom: 32px;
    }}
    .toc h2 {{ font-size: 18px; margin-bottom: 12px; color: #374151; }}
    .toc ol {{ columns: 2; column-gap: 32px; padding-left: 20px; }}
    .toc li {{ margin-bottom: 6px; font-size: 14px; break-inside: avoid; }}
    .toc a {{ color: {BLUE}; text-decoration: none; }}
    .toc a:hover {{ text-decoration: underline; }}
    .toc .cat {{ color: #9CA3AF; font-size: 12px; margin-left: 4px; }}

    .chart-section {{
        background: white; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 28px 32px; margin-bottom: 24px;
        scroll-margin-top: 20px;
    }}
    .chart-header {{
        display: flex; align-items: center; gap: 16px; margin-bottom: 12px;
    }}
    .chart-num {{
        background: {BLUE}; color: white; width: 36px; height: 36px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 14px; flex-shrink: 0;
    }}
    .chart-header h3 {{ font-size: 18px; font-weight: 700; color: #1F2937; margin: 0; }}
    .chart-category {{
        font-size: 12px; color: #6B7280; background: #F3F4F6;
        padding: 2px 10px; border-radius: 12px; display: inline-block;
    }}
    .chart-desc {{ color: #4B5563; font-size: 14px; margin-bottom: 8px; }}
    .chart-why {{
        color: #374151; font-size: 13px; margin-bottom: 16px;
        background: #F0FDF4; border-left: 3px solid {GREEN};
        padding: 10px 14px; border-radius: 0 8px 8px 0;
    }}
    .chart-img {{ margin-bottom: 16px; }}
    .chart-img img {{ width: 100%; height: auto; border-radius: 8px; border: 1px solid #E5E7EB; }}

    .comment-box {{
        border: 1px dashed #D1D5DB; border-radius: 8px; padding: 12px 16px;
        background: #FAFAFA;
    }}
    .comment-label {{
        font-size: 12px; color: #9CA3AF; text-transform: uppercase;
        letter-spacing: 0.5px; margin-bottom: 6px;
    }}
    .comment-area {{
        min-height: 40px; font-size: 14px; color: #374151;
        outline: none; padding: 4px;
    }}
    .comment-area:empty:before {{
        content: attr(placeholder); color: #D1D5DB;
    }}

    .footer {{
        text-align: center; color: #9CA3AF; font-size: 12px;
        padding: 32px 0; border-top: 1px solid #E5E7EB; margin-top: 32px;
    }}

    @media (max-width: 900px) {{
        .toc ol {{ columns: 1; }}
        .container {{ padding: 16px; }}
        .header {{ padding: 24px 16px; }}
        .header .stats {{ gap: 12px; }}
    }}
</style>
</head>
<body>

<div class="header">
    <h1>{ticker} — D&O Underwriting Chart Lab</h1>
    <div class="subtitle">20 experimental stock chart visualizations for D&O risk assessment | Data from {STATE_PATH}</div>
    <div class="stats">
        <div class="stat">
            <div class="label">Current Price</div>
            <div class="value">${current_price:,.2f}</div>
        </div>
        <div class="stat">
            <div class="label">Market Cap</div>
            <div class="value">${market_cap/1e12:.2f}T</div>
        </div>
        <div class="stat">
            <div class="label">52W Range</div>
            <div class="value">${low_52w:,.2f} - ${high_52w:,.2f}</div>
        </div>
        <div class="stat">
            <div class="label">Beta</div>
            <div class="value">{beta:.3f}</div>
        </div>
        <div class="stat">
            <div class="label">Charts</div>
            <div class="value">20</div>
        </div>
    </div>
</div>

<div class="container">
    <div class="toc">
        <h2>Table of Contents</h2>
        <ol>
            {"".join(toc_items)}
        </ol>
    </div>

    {"".join(chart_sections)}

    <div class="footer">
        Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} | {ticker} D&O Underwriting Chart Lab | Data: state.json ({STATE_PATH})
    </div>
</div>

</body>
</html>'''
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Generating 20 chart experiments for {ticker}...")
    output_path = Path("output/AAPL/chart_experiments.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = generate_html()
    output_path.write_text(html)
    print(f"\nDone! Written to {output_path} ({len(html)/1024:.0f} KB)")
