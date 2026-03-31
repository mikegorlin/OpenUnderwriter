#!/usr/bin/env python3
"""Generate ALL D&O underwriting charts using matplotlib. Output: single HTML with base64 PNGs."""

import base64
import io
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Global chart quality
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.facecolor": "white", "figure.dpi": 300, "savefig.dpi": 300,
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9, "text.antialiased": True, "lines.antialiased": True,
    "axes.facecolor": "white", "axes.edgecolor": "#D1D5DB", "axes.linewidth": 0.3,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.axisbelow": True,
    "grid.color": "#F3F4F6", "grid.linewidth": 0.4,
})

# ---------------------------------------------------------------------------
# Paths — accept state.json path as argument
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) > 1:
    STATE_PATH = Path(sys.argv[1])
else:
    STATE_PATH = PROJECT_ROOT / "output" / "AAPL" / "2026-03-22" / "state.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(v, default=0.0):
    """Safely convert any value to float."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        return safe_float(v.get("value"), default)
    if isinstance(v, str):
        v = v.strip().replace(",", "").replace("%", "").replace("$", "").replace("B", "").replace("M", "")
        try:
            return float(v)
        except (ValueError, TypeError):
            return default
    return default


def sourced_val(v, default=None):
    """Extract value from SourcedValue dict or plain value."""
    if v is None:
        return default
    if isinstance(v, dict) and "value" in v:
        return v["value"] if v["value"] is not None else default
    return v


def parse_dates(date_strs):
    """Parse date strings from yfinance into datetime objects."""
    dates = []
    for d in date_strs:
        if d is None:
            continue
        try:
            # Try multiple formats
            for fmt in ["%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(d.split("-04:00")[0].split("-05:00")[0], fmt.replace("%z", ""))
                    dates.append(dt)
                    break
                except ValueError:
                    continue
            else:
                # Last resort: just take date part
                dates.append(datetime.strptime(d[:10], "%Y-%m-%d"))
        except Exception:
            continue
    return dates


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def fmt_billions(v):
    """Format dollar value in billions."""
    v = safe_float(v)
    if abs(v) >= 1e9:
        return f"${v/1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def load_history(md, key):
    """Load price history from market_data dict into parallel lists."""
    h = md.get(key, {})
    if not h:
        return [], [], [], [], [], []
    raw_dates = h.get("Date", [])
    dates = parse_dates(raw_dates)
    opens = [safe_float(x) for x in h.get("Open", [])]
    highs = [safe_float(x) for x in h.get("High", [])]
    lows = [safe_float(x) for x in h.get("Low", [])]
    closes = [safe_float(x) for x in h.get("Close", [])]
    volumes = [safe_float(x) for x in h.get("Volume", [])]
    # Trim to shortest
    n = min(len(dates), len(closes), len(volumes))
    return dates[:n], opens[:n], highs[:n], lows[:n], closes[:n], volumes[:n]


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def chart_1_combo(state, md):
    """COMBINATION: Drops + Insider Trades + DDL -- 3-panel stacked."""
    dates, opens, highs, lows, closes, volumes = load_history(md, "history_2y")
    if not dates:
        return None, "No 2-year price history available"

    closes_arr = np.array(closes)
    dates_arr = np.array(dates)
    volumes_arr = np.array(volumes)

    info = md.get("info", {})
    shares_out = safe_float(info.get("sharesOutstanding", 0))

    # Compute rolling 60-day peak
    rolling_peak = np.maximum.accumulate(closes_arr)
    # For a proper 60-day rolling peak:
    window = 60
    rolling_peak_60 = np.copy(closes_arr)
    for i in range(len(closes_arr)):
        start = max(0, i - window)
        rolling_peak_60[i] = np.max(closes_arr[start:i+1])

    drawdown_from_peak = (closes_arr - rolling_peak_60) / rolling_peak_60

    # Find drop zones (>8% from rolling 60-day peak)
    drop_mask = drawdown_from_peak < -0.08

    # Get multi-day drops from extracted data
    extracted_drops = state.get("extracted", {}).get("market", {}).get("stock_drops", {}).get("multi_day_drops", [])

    # Parse insider transactions
    ins = md.get("insider_transactions", {})
    ins_dates, ins_names, ins_shares, ins_values, ins_types = [], [], [], [], []
    n_ins = len(ins.get("index", []))
    for i in range(n_ins):
        d_str = ins.get("Start Date", [None] * n_ins)[i]
        name = ins.get("Insider", [""] * n_ins)[i]
        sh = safe_float(ins.get("Shares", [0] * n_ins)[i])
        val = safe_float(ins.get("Value", [0] * n_ins)[i])
        text = str(ins.get("Text", [""] * n_ins)[i]).lower()
        ownership = str(ins.get("Ownership", [""] * n_ins)[i])

        if d_str:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dt >= dates[0] and dt <= dates[-1]:
                    ins_dates.append(dt)
                    ins_names.append(name)
                    ins_shares.append(sh)
                    # Estimate value if not available
                    if val == 0 and sh > 0:
                        # Find closest price
                        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                        val = sh * closes[idx]
                    ins_values.append(val)
                    # Determine buy vs sell
                    is_sale = "sale" in text or "sold" in text or ownership == "D"
                    is_buy = "purchase" in text or "buy" in text or "bought" in text
                    if is_buy:
                        ins_types.append("buy")
                    elif "gift" in text:
                        ins_types.append("gift")
                    else:
                        ins_types.append("sale")
            except Exception:
                pass

    # Parse earnings dates
    ed = md.get("earnings_dates", {})
    ed_dates_raw = ed.get("Earnings Date", [])
    ed_surprise = ed.get("Surprise(%)", [])
    ed_reported = ed.get("Reported EPS", [])
    earn_dates, earn_surprises = [], []
    for i, d_str in enumerate(ed_dates_raw):
        if d_str and i < len(ed_reported) and ed_reported[i] is not None:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dt >= dates[0] and dt <= dates[-1]:
                    earn_dates.append(dt)
                    s_pct = safe_float(ed_surprise[i] if i < len(ed_surprise) else 0)
                    earn_surprises.append(s_pct)
            except Exception:
                pass

    # Compute running DDL exposure
    ddl_exposure = np.zeros(len(closes_arr))
    for i in range(len(closes_arr)):
        peak = rolling_peak_60[i]
        drop = peak - closes_arr[i]
        if drop > 0 and shares_out > 0:
            ddl_exposure[i] = drop * shares_out
        else:
            ddl_exposure[i] = 0

    # --- Build figure ---
    fig = plt.figure(figsize=(16, 8))
    gs = fig.add_gridspec(3, 1, height_ratios=[60, 20, 20], hspace=0.08)

    # Panel 1: Price — Google Finance style green fill under entire line, red shading for 15%+ drops
    ax1 = fig.add_subplot(gs[0])

    # Green area fill under entire stock line (Google Finance style)
    overall_up = closes[-1] >= closes[0]
    fill_color = "#16A34A" if overall_up else "#DC2626"
    ax1.fill_between(dates, closes, min(closes) * 0.97, color=fill_color, alpha=0.07, zorder=0)

    # Red fill UNDER the stock line (not full vertical) for drops >= 15%
    drop_15_mask = drawdown_from_peak < -0.15
    ax1.fill_between(dates, closes, min(closes) * 0.97,
                     where=drop_15_mask[:len(dates)],
                     color="#DC2626", alpha=0.25, interpolate=True, zorder=1)

    # Plot segments: navy normal, fat red during drops
    in_drop = False
    drop_start = 0
    seg_start = 0
    drop_zones = []
    for i in range(len(drop_mask)):
        if drop_mask[i] and not in_drop:
            # End normal segment, start drop
            if seg_start < i:
                ax1.plot(dates[seg_start:i+1], closes[seg_start:i+1], color="#1E3A5F", linewidth=2.0, zorder=3)
            drop_start = i
            in_drop = True
        elif not drop_mask[i] and in_drop:
            # Draw red segment for the drop (will upgrade to fat+shaded for max DDL later)
            ax1.plot(dates[drop_start:i+1], closes[drop_start:i+1], color="#DC2626", linewidth=2.0, zorder=4, alpha=0.8)
            # Track this drop for max DDL calculation
            zone = closes_arr[drop_start:i]
            trough_idx = drop_start + np.argmin(zone)
            pre_peak_idx = max(0, drop_start - window)
            peak_val = np.max(closes_arr[pre_peak_idx:drop_start+1])
            peak_pos = pre_peak_idx + np.argmax(closes_arr[pre_peak_idx:drop_start+1])
            trough_val = closes_arr[trough_idx]
            ddl_val = (peak_val - trough_val) * shares_out
            drop_zones.append((drop_start, i, peak_pos, trough_idx, peak_val, trough_val, ddl_val))
            seg_start = i
            in_drop = False
    # Draw remaining normal segment
    if not in_drop and seg_start < len(dates):
        ax1.plot(dates[seg_start:], closes[seg_start:], color="#1E3A5F", linewidth=2.0, zorder=3)
    # Handle case where drop extends to end
    if in_drop:
        zone = closes_arr[drop_start:]
        trough_idx = drop_start + np.argmin(zone)
        pre_peak_idx = max(0, drop_start - window)
        peak_val = np.max(closes_arr[pre_peak_idx:drop_start+1])
        peak_pos = pre_peak_idx + np.argmax(closes_arr[pre_peak_idx:drop_start+1])
        trough_val = closes_arr[trough_idx]
        ddl_val = (peak_val - trough_val) * shares_out
        drop_zones.append((drop_start, len(dates)-1, peak_pos, trough_idx, peak_val, trough_val, ddl_val))
        ax1.plot(dates[drop_start:], closes[drop_start:], color="#DC2626", linewidth=2.5, zorder=4, alpha=0.85)

    # Label drops: max DDL gets full treatment + shading, others get small pill at bottom
    if drop_zones:
        max_drop = max(drop_zones, key=lambda x: x[6])  # highest DDL value
        # Re-draw max DDL segment extra fat (shading handled by 15% threshold above)
        mds, mdi = max_drop[0], max_drop[1]
        ax1.plot(dates[mds:mdi+1], closes[mds:mdi+1],
                 color="#DC2626", linewidth=3.0, zorder=4, alpha=0.9)
        # Merge nearby drop zones (within 10 days) to avoid overlapping labels
        merged_drops = []
        for dz in sorted(drop_zones, key=lambda x: x[0]):
            ds, di, pp, ti, pv, tv, dv = dz
            if merged_drops and ds - merged_drops[-1][1] < 10:
                # Merge: extend previous zone, keep the deeper trough
                prev = merged_drops[-1]
                new_ti = ti if tv < prev[5] else prev[3]
                new_tv = min(tv, prev[5])
                new_pv = max(pv, prev[4])
                new_pp = pp if pv >= prev[4] else prev[2]
                new_dv = max(dv, prev[6])
                merged_drops[-1] = (prev[0], di, new_pp, new_ti, new_pv, new_tv, new_dv)
            else:
                merged_drops.append(dz)

        for dz in merged_drops:
            ds, di, pp, ti, pv, tv, dv = dz
            # Simple: % from the price at zone start to the trough
            zone_start_price = closes[ds]
            drop_pct = (tv - zone_start_price) / zone_start_price * 100
            if dz is max_drop or (max_drop and dv == max_drop[6]):
                # Max DDL labels go on the DDL panel (panel 2), not here
                pass
            elif drop_pct <= -15:
                # Only label drops >= 15% with a pill at bottom
                mid_date = dates[ds] + (dates[min(ti, len(dates)-1)] - dates[ds]) / 2
                ax1.annotate(f"{drop_pct:.0f}%", xy=(mid_date, 0.05), xycoords=("data", "axes fraction"),
                            fontsize=6, color="white", fontweight="700", ha="center", va="center",
                            bbox=dict(boxstyle="round,pad=0.25", fc="#DC2626", ec="none", alpha=0.75),
                            zorder=12)

    # Insider trade circles
    for i, (dt, name, val, itype) in enumerate(zip(ins_dates, ins_names, ins_values, ins_types)):
        # Find price at date
        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
        price = closes[idx]
        size = max(15, min(100, val / 2e5))  # Smaller circles
        if itype == "sale":
            ax1.scatter(dt, price, marker="o", c="#DC2626", s=size, zorder=5, edgecolors="white", linewidths=0.3)
        elif itype == "buy":
            ax1.scatter(dt, price, marker="o", c="#059669", s=size, zorder=5, edgecolors="white", linewidths=0.3)
        else:
            ax1.scatter(dt, price, marker="o", c="#9CA3AF", s=size * 0.5, zorder=5, edgecolors="white", linewidths=0.3)

    # Label top 5 largest insider trades
    if ins_values:
        sorted_idx = np.argsort(ins_values)[::-1][:3]
        for idx in sorted_idx:
            if ins_values[idx] > 0:
                dt = ins_dates[idx]
                p_idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                price = closes[p_idx]
                label = f"{ins_names[idx].split()[0]} {fmt_billions(ins_values[idx])}"
                ax1.annotate(label, xy=(dt, price), fontsize=5.5, color="#374151",
                           xytext=(5, 8), textcoords="offset points",
                           arrowprops=dict(arrowstyle="-", color="#9CA3AF", lw=0.5), zorder=6)

    # Earnings: dotted vertical line (green beat / red miss), "E↑" or "E↓" at top
    for dt, surprise in zip(earn_dates, earn_surprises):
        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
        color = "#059669" if surprise >= 0 else "#DC2626"
        ax1.axvline(x=dt, color=color, linewidth=0.6, linestyle=":", alpha=0.35, zorder=1)
        arrow = "E^" if surprise >= 0 else "Ev"
        ax1.annotate(arrow, xy=(dt, 0.97), xycoords=("data", "axes fraction"),
                     fontsize=6, color=color, fontweight="700", ha="center", va="top",
                     alpha=0.7, annotation_clip=False, zorder=11)

    # ── OVERLAY: Sector ETF + S&P 500 (very subtle, behind everything) ──
    spy_closes = [safe_float(c) for c in md.get("spy_history_2y", {}).get("Close", [])][:len(dates)]
    sect_closes = [safe_float(c) for c in md.get("sector_history_2y", {}).get("Close", [])][:len(dates)]
    sector_etf_name = str(md.get("sector_etf", "Sector"))
    if spy_closes and len(spy_closes) > 10 and spy_closes[0] > 0:
        spy_scaled = [c / spy_closes[0] * closes[0] for c in spy_closes]
        ax1.plot(dates[:len(spy_scaled)], spy_scaled, color="#9CA3AF", linewidth=1.3,
                 alpha=0.6, zorder=1)
        # Label as pill on chart where there's room (25% from right)
        lbl_idx = int(len(spy_scaled) * 0.25)
        ax1.annotate("S&P 500", xy=(dates[lbl_idx], spy_scaled[lbl_idx]),
                     fontsize=5.5, color="white", fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc="#9CA3AF", ec="none", alpha=0.8),
                     xytext=(0, -10), textcoords="offset points", zorder=11)
    if sect_closes and len(sect_closes) > 10 and sect_closes[0] > 0:
        sect_scaled = [c / sect_closes[0] * closes[0] for c in sect_closes]
        ax1.plot(dates[:len(sect_scaled)], sect_scaled, color="#60A5FA", linewidth=1.3,
                 alpha=0.6, zorder=1)
        # Label as pill on chart
        lbl_idx = int(len(sect_scaled) * 0.15)
        ax1.annotate(sector_etf_name, xy=(dates[lbl_idx], sect_scaled[lbl_idx]),
                     fontsize=5.5, color="white", fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc="#60A5FA", ec="none", alpha=0.8),
                     xytext=(0, 10), textcoords="offset points", zorder=11)

    # AAPL pill label on the stock line (near the end)
    lbl_idx_aapl = int(len(dates) * 0.85)
    ax1.annotate(ticker, xy=(dates[lbl_idx_aapl], closes[lbl_idx_aapl]),
                 fontsize=5.5, color="white", fontweight="700", ha="center",
                 bbox=dict(boxstyle="round,pad=0.2", fc="#1E3A5F", ec="none", alpha=0.85),
                 xytext=(0, 10), textcoords="offset points", zorder=11)

    # ── Short interest badge ──
    si_pct = safe_float(info.get("shortPercentOfFloat"), 0)
    if si_pct > 0:
        ax1.annotate(f"SI: {si_pct*100:.1f}%", xy=(0.99, 0.03), xycoords="axes fraction",
                    fontsize=6, color="#6B7280", fontweight="600", ha="right", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#E5E7EB", linewidth=0.3),
                    zorder=12)

    ax1.set_ylabel("Price ($)", fontsize=8)
    ax1.set_title("Stock Price with Drops, DDL Exposure, Insider Trades & Earnings", fontsize=11, fontweight="bold", pad=8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax1.tick_params(labelbottom=False)
    # No legend box — lines labeled as pills directly on chart

    # Panel 2: Running DDL exposure area
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.fill_between(dates, ddl_exposure / 1e9, color="#FCA5A5", alpha=0.6, zorder=2)
    ax2.plot(dates, ddl_exposure / 1e9, color="#DC2626", linewidth=0.8, zorder=3)
    ax2.set_ylabel("DDL ($B)", fontsize=8)
    ax2.tick_params(labelbottom=False)

    # Max DDL annotations on THIS panel
    if drop_zones:
        max_drop = max(drop_zones, key=lambda x: x[6])
        _, _, pp, ti, pv, tv, dv = max_drop
        max_ddl_bn = dv / 1e9 if dv > 1e9 else dv / 1e6
        max_ddl_unit = "B" if dv > 1e9 else "M"
        peak_ddl_idx = np.argmax(ddl_exposure)
        # Green pill: peak price
        ax2.annotate(f"Peak: ${pv:,.0f}", xy=(dates[pp], ddl_exposure[pp] / 1e9),
                    fontsize=6, color="white", fontweight="700", ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#16A34A", ec="none", alpha=0.85),
                    xytext=(0, 10), textcoords="offset points", zorder=12)
        # Red pill: trough price + max DDL amount
        ax2.annotate(f"Trough: ${tv:,.0f}  |  Max DDL: ${max_ddl_bn:.1f}{max_ddl_unit}",
                    xy=(dates[peak_ddl_idx], ddl_exposure[peak_ddl_idx] / 1e9),
                    fontsize=6.5, color="white", fontweight="700", ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#DC2626", ec="none", alpha=0.9),
                    xytext=(0, -12), textcoords="offset points", zorder=12)

    # Panel 3: Volume bars
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    for i in range(len(dates)):
        c = closes[i]
        o = opens[i] if i < len(opens) else c
        color = "#059669" if c >= o else "#DC2626"
        # Check if insider trade date
        is_insider_date = any(abs((dt - dates[i]).total_seconds()) < 86400 for dt in ins_dates)
        if is_insider_date:
            color = "#F59E0B"
        ax3.bar(dates[i], volumes[i] / 1e6, color=color, alpha=0.5, width=1.0)

    ax3.set_ylabel("Vol (M)", fontsize=8)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    # Short interest as pill badge on volume panel (we only have current snapshot, not history)
    si_pct = safe_float(info.get("shortPercentOfFloat"), 0) * 100
    si_prior = safe_float(info.get("sharesShortPriorMonth"), 0)
    si_current = safe_float(info.get("sharesShort"), 0)
    if si_pct > 0:
        direction = "^" if si_current > si_prior else "v"
        change_pct = ((si_current - si_prior) / si_prior * 100) if si_prior > 0 else 0
        si_label = f"SI: {si_pct:.1f}% {direction} ({change_pct:+.0f}% MoM)"
        ax3.annotate(si_label, xy=(0.99, 0.92), xycoords="axes fraction",
                    fontsize=6, color="white", fontweight="700", ha="right", va="top",
                    bbox=dict(boxstyle="round,pad=0.25", fc="#7C3AED", ec="none", alpha=0.8),
                    zorder=12)

    fig.align_ylabels([ax1, ax2, ax3])
    return fig, None


def chart_2_perf_2y(state, md):
    """2-Year Performance vs Benchmarks."""
    dates, _, _, _, closes, volumes = load_history(md, "history_2y")
    if not dates or len(closes) < 2:
        return None, "No 2-year history"

    closes_arr = np.array(closes)
    base = closes_arr[0]
    returns_pct = (closes_arr / base - 1) * 100

    info = md.get("info", {})
    extracted_stock = state.get("extracted", {}).get("market", {}).get("stock", {})

    # Real benchmark data from yfinance
    n = len(dates)
    spy_closes = [safe_float(c) for c in md.get("spy_history_2y", {}).get("Close", [])][:n]
    sect_closes = [safe_float(c) for c in md.get("sector_history_2y", {}).get("Close", [])][:n]
    if spy_closes and spy_closes[0] > 0:
        market_return = np.array([(c / spy_closes[0] - 1) * 100 for c in spy_closes])
    else:
        market_return = np.zeros(n)
    if sect_closes and sect_closes[0] > 0:
        sector_return = np.array([(c / sect_closes[0] - 1) * 100 for c in sect_closes])
    else:
        sector_return = np.zeros(n)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 5.5), height_ratios=[75, 25],
                                    gridspec_kw={"hspace": 0.08})

    # Main price chart as % return
    ax1.plot(dates, returns_pct, color="#1E3A5F", linewidth=1.2, label=ticker, zorder=3)
    ax1.plot(dates, market_return, color="#6B7280", linewidth=0.8, linestyle="--", label="S&P 500", zorder=2)
    ax1.plot(dates, sector_return, color="#9333EA", linewidth=0.8, linestyle="--", label="Sector ETF", zorder=2)

    # Green/red fill
    ax1.fill_between(dates, returns_pct, 0, where=returns_pct >= 0, color="#D1FAE5", alpha=0.4, zorder=1)
    ax1.fill_between(dates, returns_pct, 0, where=returns_pct < 0, color="#FEE2E2", alpha=0.4, zorder=1)

    # 52W annotations
    hi52 = safe_float(info.get("fiftyTwoWeekHigh", 0))
    lo52 = safe_float(info.get("fiftyTwoWeekLow", 0))
    curr = safe_float(info.get("currentPrice", 0))
    if hi52:
        hi_ret = (hi52 / base - 1) * 100
        lo_ret = (lo52 / base - 1) * 100
        curr_ret = (curr / base - 1) * 100
        # Find dates closest to these prices
        hi_idx = np.argmin(np.abs(closes_arr - hi52))
        lo_idx = np.argmin(np.abs(closes_arr - lo52))
        ax1.scatter(dates[hi_idx], hi_ret, s=120, c="#059669", zorder=6, edgecolors="white", linewidths=1.5)
        ax1.annotate(f"52W Hi ${hi52:.0f}", xy=(dates[hi_idx], hi_ret), fontsize=7, color="#059669",
                   fontweight="bold", xytext=(8, 8), textcoords="offset points")
        ax1.scatter(dates[lo_idx], lo_ret, s=120, c="#DC2626", zorder=6, edgecolors="white", linewidths=1.5)
        ax1.annotate(f"52W Lo ${lo52:.0f}", xy=(dates[lo_idx], lo_ret), fontsize=7, color="#DC2626",
                   fontweight="bold", xytext=(8, -12), textcoords="offset points")

    # DDL dashed line from peak to trough
    peak_idx = np.argmax(closes_arr)
    trough_idx_after = peak_idx + np.argmin(closes_arr[peak_idx:])
    if trough_idx_after > peak_idx:
        ax1.plot([dates[peak_idx], dates[trough_idx_after]],
                [returns_pct[peak_idx], returns_pct[trough_idx_after]],
                color="#DC2626", linewidth=1.5, linestyle="--", zorder=4)

    # Return labels on right edge
    final_ret = returns_pct[-1]
    ax1.annotate(f"AAPL: {final_ret:+.1f}%", xy=(1.01, final_ret),
               xycoords=("axes fraction", "data"), fontsize=8, fontweight="bold",
               color="#1E3A5F", va="center")
    ax1.annotate(f"S&P: {market_return[-1]:+.1f}%", xy=(1.01, market_return[-1]),
               xycoords=("axes fraction", "data"), fontsize=7, color="#6B7280", va="center")

    # Risk stat badges top-right
    si_pct = safe_float(info.get("shortPercentOfFloat", 0)) * 100
    vol_90 = safe_float(sourced_val(extracted_stock.get("volatility_90d")), 0)
    max_dd = safe_float(sourced_val(extracted_stock.get("max_drawdown_1y")), 0)
    badge_text = f"SI: {si_pct:.1f}%  |  Vol: {vol_90:.1f}%  |  Max Drop: {max_dd:.1f}%"
    ax1.text(0.98, 0.95, badge_text, transform=ax1.transAxes, fontsize=7,
            ha="right", va="top", bbox=dict(boxstyle="round,pad=0.3", facecolor="#F3F4F6",
            edgecolor="#D1D5DB", linewidth=0.5))

    ax1.set_ylabel("Return (%)", fontsize=8)
    ax1.set_title("2-Year Performance vs Benchmarks", fontsize=11, fontweight="bold", pad=8)
    ax1.legend(loc="upper left", fontsize=7, framealpha=0.8)
    ax1.tick_params(labelbottom=False)
    ax1.axhline(y=0, color="#9CA3AF", linewidth=0.5, zorder=1)

    # Earnings diamonds on price chart
    ed = md.get("earnings_dates", {})
    ed_dates_raw = ed.get("Earnings Date", [])
    ed_reported = ed.get("Reported EPS", [])
    for i, d_str in enumerate(ed_dates_raw):
        if d_str and i < len(ed_reported) and ed_reported[i] is not None:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dt >= dates[0] and dt <= dates[-1]:
                    idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                    surp_val = safe_float(ed["Surprise(%)"][i]) if i < len(ed.get("Surprise(%)", [])) else 0
                    color_e = "#059669" if surp_val >= 0 else "#DC2626"
                    ax1.axvline(dt, color=color_e, linewidth=1.2, linestyle=":", alpha=0.5, zorder=1)
                    arrow_e = "E ^" if surp_val >= 0 else "E v"
                    ax1.annotate(arrow_e, xy=(dt, 0.97), xycoords=("data", "axes fraction"),
                                fontsize=7, color=color_e, fontweight="800", ha="center", va="top",
                                annotation_clip=False, zorder=12)
            except Exception:
                pass

    # Volume bars
    opens_arr = np.array([safe_float(x) for x in md.get("history_2y", {}).get("Open", [])][:len(dates)])
    for i in range(len(dates)):
        c = closes[i]
        o = opens_arr[i] if i < len(opens_arr) else c
        color = "#059669" if c >= o else "#DC2626"
        ax2.bar(dates[i], volumes[i] / 1e6, color=color, alpha=0.4, width=1.0)

    ax2.set_ylabel("Vol (M)", fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    return fig, None


def chart_3_perf_5y(state, md):
    """5-Year Weekly Performance."""
    dates, _, _, _, closes, volumes = load_history(md, "history_5y")
    if not dates or len(closes) < 10:
        return None, "No 5-year history"

    # Resample to weekly
    weekly_dates, weekly_closes, weekly_volumes = [], [], []
    week_closes, week_vols = [], []
    current_week = dates[0].isocalendar()[1]
    current_year = dates[0].year

    for i in range(len(dates)):
        w = dates[i].isocalendar()[1]
        y = dates[i].year
        if w != current_week or y != current_year:
            if week_closes:
                weekly_dates.append(dates[i-1])
                weekly_closes.append(week_closes[-1])
                weekly_volumes.append(sum(week_vols))
            week_closes, week_vols = [], []
            current_week, current_year = w, y
        week_closes.append(closes[i])
        week_vols.append(volumes[i])
    if week_closes:
        weekly_dates.append(dates[-1])
        weekly_closes.append(week_closes[-1])
        weekly_volumes.append(sum(week_vols))

    wc = np.array(weekly_closes)
    base = wc[0]
    returns_pct = (wc / base - 1) * 100

    # Real 5-year benchmark data, resampled to weekly
    n = len(weekly_dates)
    spy_5y = [safe_float(c) for c in md.get("spy_history_5y", {}).get("Close", [])]
    sect_5y = [safe_float(c) for c in md.get("sector_history_5y", {}).get("Close", [])]
    # Resample to weekly (take every 5th point to approximate)
    spy_weekly = spy_5y[::5][:n] if spy_5y else []
    sect_weekly = sect_5y[::5][:n] if sect_5y else []
    if spy_weekly and spy_weekly[0] > 0:
        market_line = np.array([(c / spy_weekly[0] - 1) * 100 for c in spy_weekly])
    else:
        market_line = np.zeros(n)
    if sect_weekly and sect_weekly[0] > 0:
        sector_line = np.array([(c / sect_weekly[0] - 1) * 100 for c in sect_weekly])
    else:
        sector_line = np.zeros(n)

    # Compact strip — 1/3 height, Bloomberg Orange style (dark bg, orange/amber)
    fig, ax = plt.subplots(figsize=(16, 2.7))
    fig.patch.set_facecolor("#1A1A2E")
    ax.set_facecolor("#1A1A2E")

    # Fill
    overall_up = weekly_closes[-1] >= weekly_closes[0]
    line_color = "#D97706" if overall_up else "#EF4444"
    rp = np.array(returns_pct)
    wd = np.array(weekly_dates)
    ax.fill_between(wd, rp, 0, where=rp >= 0, color="#D97706", alpha=0.08, interpolate=True)
    ax.fill_between(wd, rp, 0, where=rp < 0, color="#EF4444", alpha=0.12, interpolate=True)

    # Stock line — orange
    ax.plot(weekly_dates, returns_pct, color="#F59E0B", linewidth=1.5, zorder=5)

    # Benchmarks
    m_len = min(len(weekly_dates), len(market_line))
    s_len = min(len(weekly_dates), len(sector_line))
    sector_etf_name = str(md.get("sector_etf", "Sector"))
    if m_len > 10:
        ax.plot(weekly_dates[:m_len], market_line[:m_len], color="#6B7280", linewidth=1.0, alpha=0.6, zorder=1)
        lbl_i = int(m_len * 0.3)
        ax.annotate("S&P 500", xy=(weekly_dates[lbl_i], market_line[lbl_i]),
                     fontsize=6.5, color="white", fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.25", fc="#4B5563", ec="none", alpha=0.8),
                     xytext=(0, -8), textcoords="offset points", zorder=11)
    if s_len > 10:
        ax.plot(weekly_dates[:s_len], sector_line[:s_len], color="#F97316", linewidth=1.0, alpha=0.6, zorder=1)
        lbl_i = int(s_len * 0.15)
        ax.annotate(sector_etf_name, xy=(weekly_dates[lbl_i], sector_line[lbl_i]),
                     fontsize=6.5, color="white", fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.25", fc="#EA580C", ec="none", alpha=0.8),
                     xytext=(0, 8), textcoords="offset points", zorder=11)

    ax.axhline(0, color="#374151", linewidth=0.5, zorder=1)

    # Ticker pill
    lbl_i = int(len(weekly_dates) * 0.85)
    ax.annotate(ticker, xy=(weekly_dates[lbl_i], returns_pct[lbl_i]),
                fontsize=7.5, color="white", fontweight="700", ha="center",
                bbox=dict(boxstyle="round,pad=0.35", fc="#B45309", ec="none", alpha=0.85),
                xytext=(0, 10), textcoords="offset points", zorder=11)

    # Style axes for dark theme
    ax.tick_params(colors="#9CA3AF")
    ax.grid(True, color="#27274A", linewidth=0.3)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Return label at right edge
    final_ret = returns_pct[-1]
    ax.annotate(f"{final_ret:+.0f}%", xy=(weekly_dates[-1], final_ret),
                fontsize=8, color=line_color, fontweight="700",
                xytext=(8, 0), textcoords="offset points", ha="left", va="center",
                annotation_clip=False, zorder=12)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+.0f}%" if x != 0 else "0%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.set_title("5-Year Performance (Weekly)", fontsize=10, fontweight="700", loc="left", pad=6)

    fig.subplots_adjust(left=0.04, right=0.93, top=0.88, bottom=0.15)
    return fig, None


def chart_4_drawdown(state, md):
    """Drawdown From Peak (2-Year)."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates:
        return None, "No history"

    closes_arr = np.array(closes)
    running_max = np.maximum.accumulate(closes_arr)
    drawdown = (closes_arr - running_max) / running_max * 100

    fig, ax = plt.subplots(figsize=(16, 3))
    ax.fill_between(dates, drawdown, 0, color="#FCA5A5", alpha=0.5)
    ax.plot(dates, drawdown, color="#DC2626", linewidth=0.8)
    ax.axhline(y=-10, color="#F59E0B", linewidth=0.8, linestyle="--", alpha=0.7, label="-10% threshold")
    ax.axhline(y=-20, color="#DC2626", linewidth=0.8, linestyle="--", alpha=0.7, label="-20% threshold")

    # Max drawdown label
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]
    ax.scatter(dates[max_dd_idx], max_dd, s=100, c="#DC2626", zorder=5, edgecolors="white", linewidths=1.5)
    ax.annotate(f"Max DD: {max_dd:.1f}%", xy=(dates[max_dd_idx], max_dd),
               fontsize=8, fontweight="bold", color="#DC2626",
               xytext=(10, -5), textcoords="offset points",
               bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#DC2626", linewidth=0.5))

    ax.set_ylabel("Drawdown (%)", fontsize=8)
    ax.set_title("Drawdown From All-Time High (2-Year)", fontsize=11, fontweight="bold", pad=8)
    ax.legend(loc="lower left", fontsize=7, framealpha=0.8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    return fig, None


def chart_5_earnings_surprise(state, md):
    """Earnings Surprise History (8 Quarters)."""
    ed = md.get("earnings_dates", {})
    ed_dates_raw = ed.get("Earnings Date", [])
    ed_estimate = ed.get("EPS Estimate", [])
    ed_reported = ed.get("Reported EPS", [])
    ed_surprise = ed.get("Surprise(%)", [])

    quarters, surprises, estimates, actuals, labels = [], [], [], [], []
    for i in range(len(ed_dates_raw)):
        if i < len(ed_reported) and ed_reported[i] is not None and i < len(ed_surprise) and ed_surprise[i] is not None:
            try:
                dt = datetime.strptime(ed_dates_raw[i][:10], "%Y-%m-%d")
                q_label = f"Q{(dt.month-1)//3+1} '{dt.strftime('%y')}"
                quarters.append(q_label)
                surprises.append(safe_float(ed_surprise[i]))
                estimates.append(safe_float(ed_estimate[i] if i < len(ed_estimate) else 0))
                actuals.append(safe_float(ed_reported[i]))
                labels.append(f"${actuals[-1]:.2f} vs ${estimates[-1]:.2f}")
            except Exception:
                pass
        if len(quarters) >= 8:
            break

    if not quarters:
        return None, "No earnings data"

    # Reverse to chronological order
    quarters, surprises, estimates, actuals, labels = (
        list(reversed(quarters)), list(reversed(surprises)),
        list(reversed(estimates)), list(reversed(actuals)), list(reversed(labels))
    )

    fig, ax = plt.subplots(figsize=(14, 3))
    x = np.arange(len(quarters))
    colors = ["#059669" if s >= 0 else "#DC2626" for s in surprises]
    bars = ax.bar(x, surprises, color=colors, alpha=0.8, width=0.6, edgecolor="white", linewidth=0.5)

    for i, (bar, lbl) in enumerate(zip(bars, labels)):
        ax.text(bar.get_x() + bar.get_width()/2, -0.5, lbl,
                ha="center", va="top", fontsize=6.5, color="#6B7280", rotation=0)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f"+{surprises[i]:.1f}%" if surprises[i] >= 0 else f"{surprises[i]:.1f}%",
                ha="center", va="bottom", fontsize=7, fontweight="bold", color=colors[i])

    ax.set_xticks(x)
    ax.set_xticklabels(quarters, fontsize=8)
    ax.axhline(y=0, color="#9CA3AF", linewidth=0.5)
    ax.set_ylabel("Surprise (%)", fontsize=8)
    ax.set_title("Earnings Surprise History (Last 8 Quarters)", fontsize=11, fontweight="bold", pad=8)

    return fig, None


def chart_6_insider_detail(state, md):
    """Insider Trading Detail."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates:
        return None, "No history"

    ins = md.get("insider_transactions", {})
    n_ins = len(ins.get("index", []))

    trades = []
    for i in range(n_ins):
        d_str = ins.get("Start Date", [None]*n_ins)[i]
        name = ins.get("Insider", [""]*n_ins)[i]
        sh = safe_float(ins.get("Shares", [0]*n_ins)[i])
        val = safe_float(ins.get("Value", [0]*n_ins)[i])
        text = str(ins.get("Text", [""]*n_ins)[i]).lower()
        ownership = str(ins.get("Ownership", [""]*n_ins)[i])

        if d_str:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dt >= dates[0] and dt <= dates[-1]:
                    idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                    price = closes[idx]
                    if val == 0 and sh > 0:
                        val = sh * price
                    is_buy = "purchase" in text or "buy" in text
                    is_gift = "gift" in text
                    ttype = "buy" if is_buy else ("gift" if is_gift else "sale")
                    trades.append({"date": dt, "name": name, "shares": sh, "value": val,
                                  "price": price, "type": ttype})
            except Exception:
                pass

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 5), height_ratios=[70, 30],
                                    gridspec_kw={"hspace": 0.12})

    # Price line
    ax1.plot(dates, closes, color="#D1D5DB", linewidth=0.8, zorder=2)

    # Trade circles
    for t in trades:
        color = "#DC2626" if t["type"] == "sale" else ("#059669" if t["type"] == "buy" else "#9CA3AF")
        size = max(30, min(300, t["value"] / 5e4))
        ax1.scatter(t["date"], t["price"], s=size, c=color, alpha=0.7, zorder=4,
                   edgecolors="white", linewidths=0.5)

    # Label top 10
    trades_sorted = sorted(trades, key=lambda x: x["value"], reverse=True)[:10]
    for t in trades_sorted:
        if t["value"] > 0:
            parts = t["name"].split()
            short_name = parts[0] if parts else "?"
            label = f"{short_name} {fmt_billions(t['value'])}"
            color = "#DC2626" if t["type"] == "sale" else "#059669"
            ax1.annotate(label, xy=(t["date"], t["price"]), fontsize=6, color=color,
                       xytext=(5, 8), textcoords="offset points",
                       arrowprops=dict(arrowstyle="-", color="#9CA3AF", lw=0.4), zorder=5)

    ax1.set_ylabel("Price ($)", fontsize=8)
    ax1.set_title("Insider Trading Detail", fontsize=11, fontweight="bold", pad=8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax1.tick_params(labelbottom=False)

    # Cumulative net insider position
    # Sort trades by date
    trades_by_date = sorted(trades, key=lambda x: x["date"])
    cum_net = 0
    cum_dates, cum_vals = [], []
    for t in trades_by_date:
        if t["type"] == "buy":
            cum_net += t["value"]
        elif t["type"] == "sale":
            cum_net -= t["value"]
        cum_dates.append(t["date"])
        cum_vals.append(cum_net)

    if cum_dates:
        color = "#059669" if cum_net >= 0 else "#DC2626"
        ax2.fill_between(cum_dates, cum_vals, 0, color=color, alpha=0.3, step="post")
        ax2.step(cum_dates, cum_vals, color=color, linewidth=1.0, where="post")
        ax2.axhline(y=0, color="#9CA3AF", linewidth=0.5)

    ax2.set_ylabel("Cum Net ($)", fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: fmt_billions(x)))

    return fig, None


def chart_7_drops_analysis(state, md):
    """Significant Drops Analysis."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates:
        return None, "No history"

    extracted_drops = state.get("extracted", {}).get("market", {}).get("stock_drops", {}).get("multi_day_drops", [])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 4), height_ratios=[60, 40],
                                    gridspec_kw={"hspace": 0.15})

    ax1.plot(dates, closes, color="#1E3A5F", linewidth=1.0, zorder=3)

    drop_labels = []
    for drop in extracted_drops:
        drop_date_str = sourced_val(drop.get("date"), "")
        drop_pct = safe_float(sourced_val(drop.get("drop_pct")))
        sector_pct = safe_float(sourced_val(drop.get("sector_return_pct")))
        is_company_specific = drop.get("is_company_specific", False)
        period_days = safe_float(drop.get("period_days", 1))
        from_price = safe_float(drop.get("from_price", 0))
        close_price = safe_float(drop.get("close_price", 0))

        if not drop_date_str:
            continue
        try:
            dt = datetime.strptime(str(drop_date_str)[:10], "%Y-%m-%d")
        except Exception:
            continue

        if dt < dates[0] or dt > dates[-1]:
            continue

        # Shade the drop zone
        start_dt = dt - timedelta(days=max(1, int(period_days)))
        ax1.axvspan(start_dt, dt, color="#FEE2E2", alpha=0.5, zorder=1)

        label = "Company-Specific" if is_company_specific else "Market-Wide"
        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
        ax1.annotate(label, xy=(dt, closes[idx]), fontsize=6, color="#DC2626",
                   fontweight="bold", xytext=(5, -15), textcoords="offset points",
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#FCA5A5", linewidth=0.5))

        drop_labels.append({
            "date": dt, "company_drop": drop_pct, "sector_drop": sector_pct,
            "label": f"{dt.strftime('%b %d')}"
        })

    ax1.set_ylabel("Price ($)", fontsize=8)
    ax1.set_title("Significant Drops Analysis", fontsize=11, fontweight="bold", pad=8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax1.tick_params(labelbottom=False)

    # Bar chart: company vs sector drop
    if drop_labels:
        x = np.arange(len(drop_labels))
        w = 0.35
        company_drops = [d["company_drop"] for d in drop_labels]
        sector_drops = [d["sector_drop"] for d in drop_labels]
        bar_labels = [d["label"] for d in drop_labels]

        ax2.bar(x - w/2, company_drops, w, color="#DC2626", alpha=0.8, label="AAPL Drop")
        ax2.bar(x + w/2, sector_drops, w, color="#6B7280", alpha=0.6, label="Sector Drop")

        for i in range(len(x)):
            ax2.text(x[i] - w/2, company_drops[i] - 0.5, f"{company_drops[i]:.1f}%",
                    ha="center", va="top", fontsize=6.5, color="white", fontweight="bold")
            ax2.text(x[i] + w/2, sector_drops[i] - 0.5, f"{sector_drops[i]:.1f}%",
                    ha="center", va="top", fontsize=6.5, color="white", fontweight="bold")

        ax2.set_xticks(x)
        ax2.set_xticklabels(bar_labels, fontsize=7)
        ax2.axhline(y=0, color="#9CA3AF", linewidth=0.5)
        ax2.legend(fontsize=7, loc="lower left")
    ax2.set_ylabel("Drop (%)", fontsize=8)

    return fig, None


def chart_8_rolling_vol(state, md):
    """Rolling Volatility vs Sector (30-day)."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates or len(closes) < 31:
        return None, "Not enough data"

    closes_arr = np.array(closes)
    # Daily returns
    returns = np.diff(np.log(closes_arr))

    # 30-day rolling volatility (annualized)
    window = 30
    vol_30 = np.array([np.std(returns[max(0, i-window):i]) * np.sqrt(252) * 100
                       for i in range(1, len(returns)+1)])

    # Real sector volatility from actual sector ETF price data
    sect_closes_raw = [safe_float(c) for c in md.get("sector_history_2y", {}).get("Close", [])]
    sect_closes_arr = np.array(sect_closes_raw[:len(closes)])
    if len(sect_closes_arr) > 31 and sect_closes_arr[0] > 0:
        sect_returns = np.diff(np.log(sect_closes_arr))
        sector_vol = np.array([np.std(sect_returns[max(0, i-window):i]) * np.sqrt(252) * 100
                               for i in range(1, len(sect_returns)+1)])
    else:
        sector_vol = np.zeros(len(vol_30))

    vol_dates = dates[1:]  # One less due to diff

    fig, ax = plt.subplots(figsize=(16, 3))

    ax.plot(vol_dates, vol_30, color="#1E3A5F", linewidth=1.0, label="AAPL 30d Vol")
    ax.plot(vol_dates, sector_vol, color="#9333EA", linewidth=0.8, linestyle="--", label="Sector 30d Vol")

    avg_vol = np.mean(vol_30)
    avg_sector = np.mean(sector_vol)
    ax.axhline(y=avg_vol, color="#1E3A5F", linewidth=0.5, linestyle=":", alpha=0.5)
    ax.axhline(y=avg_sector, color="#9333EA", linewidth=0.5, linestyle=":", alpha=0.5)

    # Spike labels where vol > 2x average
    spike_threshold = avg_vol * 2
    for i in range(len(vol_30)):
        if vol_30[i] > spike_threshold:
            # Only label if it's a local max
            if i > 0 and i < len(vol_30)-1:
                if vol_30[i] >= vol_30[i-1] and vol_30[i] >= vol_30[i+1]:
                    ax.annotate(f"{vol_30[i]:.0f}%", xy=(vol_dates[i], vol_30[i]),
                              fontsize=6, color="#DC2626", fontweight="bold",
                              xytext=(0, 8), textcoords="offset points", ha="center")

    ax.set_ylabel("Annualized Vol (%)", fontsize=8)
    ax.set_title("Rolling 30-Day Volatility vs Sector", fontsize=11, fontweight="bold", pad=8)
    ax.legend(loc="upper left", fontsize=7, framealpha=0.8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    return fig, None


def chart_9_earnings_reaction(state, md):
    """Earnings Reaction Chart."""
    ed = md.get("earnings_dates", {})
    dates_h, _, _, _, closes_h, _ = load_history(md, "history_2y")
    if not dates_h:
        return None, "No history"

    ed_dates_raw = ed.get("Earnings Date", [])
    ed_surprise = ed.get("Surprise(%)", [])
    ed_reported = ed.get("Reported EPS", [])
    closes_arr = np.array(closes_h)

    quarters, eps_surprises, day1_reactions, day5_reactions = [], [], [], []
    for i in range(len(ed_dates_raw)):
        if i < len(ed_reported) and ed_reported[i] is not None and i < len(ed_surprise) and ed_surprise[i] is not None:
            try:
                dt = datetime.strptime(ed_dates_raw[i][:10], "%Y-%m-%d")
                if dt < dates_h[0] or dt > dates_h[-1]:
                    continue
                q_label = f"Q{(dt.month-1)//3+1} '{dt.strftime('%y')}"

                # Find index in price data
                idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates_h])))

                # 1-day reaction
                if idx + 1 < len(closes_arr) and idx > 0:
                    day1 = (closes_arr[idx+1] / closes_arr[idx] - 1) * 100
                else:
                    day1 = 0

                # 5-day reaction
                if idx + 5 < len(closes_arr) and idx > 0:
                    day5 = (closes_arr[min(idx+5, len(closes_arr)-1)] / closes_arr[idx] - 1) * 100
                else:
                    day5 = 0

                quarters.append(q_label)
                eps_surprises.append(safe_float(ed_surprise[i]))
                day1_reactions.append(day1)
                day5_reactions.append(day5)
            except Exception:
                pass
        if len(quarters) >= 8:
            break

    if not quarters:
        return None, "No earnings reaction data"

    # Reverse to chronological
    quarters, eps_surprises, day1_reactions, day5_reactions = (
        list(reversed(quarters)), list(reversed(eps_surprises)),
        list(reversed(day1_reactions)), list(reversed(day5_reactions))
    )

    fig, ax = plt.subplots(figsize=(14, 3.5))
    x = np.arange(len(quarters))
    w = 0.25

    ax.bar(x - w, eps_surprises, w, color="#3B82F6", alpha=0.8, label="EPS Surprise %")
    ax.bar(x, day1_reactions, w, color="#F59E0B", alpha=0.8, label="1-Day Reaction %")
    ax.bar(x + w, day5_reactions, w, color="#8B5CF6", alpha=0.8, label="5-Day Reaction %")

    # Value labels
    for i in range(len(x)):
        for offset, val, color in [(-w, eps_surprises[i], "#3B82F6"),
                                    (0, day1_reactions[i], "#F59E0B"),
                                    (w, day5_reactions[i], "#8B5CF6")]:
            y_pos = val + 0.2 if val >= 0 else val - 0.2
            va = "bottom" if val >= 0 else "top"
            ax.text(x[i] + offset, y_pos, f"{val:+.1f}%", ha="center", va=va,
                   fontsize=5.5, color=color, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(quarters, fontsize=8)
    ax.axhline(y=0, color="#9CA3AF", linewidth=0.5)
    ax.set_ylabel("Percentage (%)", fontsize=8)
    ax.set_title("Earnings Reaction: Surprise vs Market Response", fontsize=11, fontweight="bold", pad=8)
    ax.legend(loc="upper left", fontsize=7, framealpha=0.8)

    return fig, None


def chart_10_financial_sparklines(state, md):
    """Financial Health Sparklines (6 metrics)."""
    inc = md.get("income_stmt", {})
    bs = md.get("balance_sheet", {})
    cf = md.get("cashflow", {})

    periods = inc.get("periods", [])[:4]  # Latest 4 years
    period_labels = [p[:4] for p in periods]  # Just year

    def get_vals(source, key):
        items = source.get("line_items", {})
        vals = items.get(key, [])
        return [safe_float(v) for v in vals[:4]]

    metrics = [
        ("Revenue", get_vals(inc, "Total Revenue"), "$"),
        ("Net Income", get_vals(inc, "Net Income"), "$"),
        ("Gross Margin", [], "%"),
        ("EBITDA Margin", [], "%"),
        ("Debt/Equity", [], "x"),
        ("Free Cash Flow", get_vals(cf, "Free Cash Flow"), "$"),
    ]

    # Compute margins
    rev = get_vals(inc, "Total Revenue")
    gp = get_vals(inc, "Gross Profit")
    ebitda = get_vals(inc, "EBITDA")
    debt = get_vals(bs, "Total Debt")
    equity = get_vals(bs, "Common Stock Equity")

    gm = [(g / r * 100 if r else 0) for g, r in zip(gp, rev)]
    em = [(e / r * 100 if r else 0) for e, r in zip(ebitda, rev)]
    de = [(d / e if e else 0) for d, e in zip(debt, equity)]

    metrics[2] = ("Gross Margin", gm, "%")
    metrics[3] = ("EBITDA Margin", em, "%")
    metrics[4] = ("Debt/Equity", de, "x")

    fig, axes = plt.subplots(2, 3, figsize=(14, 4))
    axes = axes.flatten()

    for i, (title, vals, unit) in enumerate(metrics):
        ax = axes[i]
        if not vals or all(v == 0 for v in vals):
            ax.text(0.5, 0.5, "N/A", transform=ax.transAxes, ha="center", va="center",
                   fontsize=12, color="#D1D5DB")
            ax.set_title(title, fontsize=9, fontweight="bold")
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        x = list(range(len(vals)))
        # Reverse for chronological (periods are newest-first)
        vals_rev = list(reversed(vals))
        labels_rev = list(reversed(period_labels[:len(vals)]))

        # Trend color
        trend_up = vals_rev[-1] >= vals_rev[0] if len(vals_rev) >= 2 else True
        # For Debt/Equity, down is good
        if "Debt" in title:
            trend_up = not trend_up
        color = "#059669" if trend_up else "#DC2626"

        ax.plot(x, vals_rev, color=color, linewidth=2.0, marker="o", markersize=4, zorder=3)
        ax.fill_between(x, vals_rev, min(vals_rev) * 0.95, color=color, alpha=0.1)

        # Format current value
        curr = vals_rev[-1]
        if unit == "$":
            val_label = fmt_billions(curr)
        elif unit == "%":
            val_label = f"{curr:.1f}%"
        else:
            val_label = f"{curr:.2f}x"

        ax.text(0.98, 0.95, val_label, transform=ax.transAxes, ha="right", va="top",
               fontsize=10, fontweight="bold", color=color)

        ax.set_xticks(x)
        ax.set_xticklabels(labels_rev, fontsize=7)
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.tick_params(axis="y", labelsize=6)

        # Minimal y formatting
        if unit == "$":
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_billions(v)))

    fig.suptitle("Financial Health Sparklines", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig, None


def chart_11_ddl_scenarios(state, md):
    """DDL Exposure Scenarios."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates:
        return None, "No history"

    info = md.get("info", {})
    shares_out = safe_float(info.get("sharesOutstanding", 0))
    closes_arr = np.array(closes)
    rolling_peak = np.maximum.accumulate(closes_arr)

    # Current DDL
    ddl = np.maximum(0, (rolling_peak - closes_arr) * shares_out) / 1e9

    # Scenario DDLs: if stock drops another 10%, 20%, 30% from current
    curr_price = closes_arr[-1]
    scenarios = [
        ("Current", ddl, "#DC2626", "-"),
        ("If -10%", np.maximum(0, (rolling_peak - closes_arr * 0.90) * shares_out) / 1e9, "#F59E0B", "--"),
        ("If -20%", np.maximum(0, (rolling_peak - closes_arr * 0.80) * shares_out) / 1e9, "#9333EA", "--"),
        ("If -30%", np.maximum(0, (rolling_peak - closes_arr * 0.70) * shares_out) / 1e9, "#1E3A5F", "--"),
    ]

    fig, ax = plt.subplots(figsize=(16, 3.5))

    for label, data, color, ls in scenarios:
        ax.plot(dates, data, color=color, linewidth=1.0 if ls == "-" else 0.8, linestyle=ls, label=label, zorder=3)
        if ls == "-":
            ax.fill_between(dates, data, color=color, alpha=0.15, zorder=1)

    # Dollar labels at current date
    for label, data, color, ls in scenarios:
        val = data[-1]
        ax.annotate(f"{label}: ${val:.1f}B", xy=(dates[-1], val),
                   fontsize=7, color=color, fontweight="bold",
                   xytext=(10, 0), textcoords="offset points", va="center")

    ax.set_ylabel("DDL Exposure ($B)", fontsize=8)
    ax.set_title("DDL Exposure Scenarios", fontsize=11, fontweight="bold", pad=8)
    ax.legend(loc="upper left", fontsize=7, framealpha=0.8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x:.0f}B"))

    return fig, None


def chart_12_suspicious_windows(state, md):
    """Suspicious Trading Windows."""
    dates, _, _, _, closes, _ = load_history(md, "history_2y")
    if not dates:
        return None, "No history"

    closes_arr = np.array(closes)

    # Find major drops (>10% from rolling peak)
    rolling_peak = np.maximum.accumulate(closes_arr)
    drawdown = (closes_arr - rolling_peak) / rolling_peak

    # Find drop start points
    drop_starts = []
    in_drop = False
    for i in range(len(drawdown)):
        if drawdown[i] < -0.10 and not in_drop:
            drop_starts.append(i)
            in_drop = True
        elif drawdown[i] >= -0.05:
            in_drop = False

    # Parse insider transactions
    ins = md.get("insider_transactions", {})
    n_ins = len(ins.get("index", []))
    trades = []
    for i in range(n_ins):
        d_str = ins.get("Start Date", [None]*n_ins)[i]
        name = ins.get("Insider", [""]*n_ins)[i]
        sh = safe_float(ins.get("Shares", [0]*n_ins)[i])
        val = safe_float(ins.get("Value", [0]*n_ins)[i])
        text = str(ins.get("Text", [""]*n_ins)[i]).lower()
        if d_str:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dt >= dates[0] and dt <= dates[-1]:
                    idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                    price = closes[idx]
                    if val == 0 and sh > 0:
                        val = sh * price
                    is_buy = "purchase" in text or "buy" in text
                    trades.append({"date": dt, "idx": idx, "name": name, "value": val,
                                  "price": price, "type": "buy" if is_buy else "sale"})
            except Exception:
                pass

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(dates, closes, color="#1E3A5F", linewidth=1.0, zorder=3)

    # 30-day windows before each major drop = yellow
    suspicious_window_indices = set()
    for ds in drop_starts:
        window_start = max(0, ds - 30)
        ax.axvspan(dates[window_start], dates[ds], color="#FEF3C7", alpha=0.6, zorder=1)
        for j in range(window_start, ds):
            suspicious_window_indices.add(j)

    # Plot trades
    for t in trades:
        in_window = t["idx"] in suspicious_window_indices
        if in_window and t["type"] == "sale":
            # Red star - scienter indicator
            ax.scatter(t["date"], t["price"], marker="*", c="#DC2626", s=200, zorder=6,
                      edgecolors="white", linewidths=0.5)
            parts = t["name"].split()
            short_name = parts[0] if parts else "?"
            ax.annotate(f"{short_name} {fmt_billions(t['value'])}", xy=(t["date"], t["price"]),
                       fontsize=6, color="#DC2626", fontweight="bold",
                       xytext=(8, 10), textcoords="offset points",
                       arrowprops=dict(arrowstyle="-", color="#DC2626", lw=0.5), zorder=7)
        else:
            # Small gray dot
            ax.scatter(t["date"], t["price"], marker="o", c="#D1D5DB", s=15, zorder=4,
                      edgecolors="white", linewidths=0.3)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#DC2626", markersize=12, label="Sale in pre-drop window (scienter risk)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#D1D5DB", markersize=6, label="Trade outside window"),
        plt.Rectangle((0, 0), 1, 1, facecolor="#FEF3C7", edgecolor="none", alpha=0.6, label="30-day pre-drop window"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=7, framealpha=0.9)

    ax.set_ylabel("Price ($)", fontsize=8)
    ax.set_title("Suspicious Trading Windows: Insider Sales Before Major Drops", fontsize=11, fontweight="bold", pad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    return fig, None


# ---------------------------------------------------------------------------
# HTML Assembly
# ---------------------------------------------------------------------------

CHART_DEFS = [
    {
        "id": "combo",
        "title": "1. Drops + Insider Trades + DDL (Combination Chart)",
        "desc": "The most critical D&O chart: maps stock price drops against insider trading activity and Dollar-Day-Loss exposure. Red zones show >8% drops from rolling 60-day peaks. Insider trades sized by dollar value reveal potential scienter. DDL area shows cumulative damages exposure at each point in time.",
        "func": chart_1_combo,
    },
    {
        "id": "perf-2y",
        "title": "2. 2-Year Performance vs Benchmarks",
        "desc": "Company-specific vs market performance reveals whether stock decline is idiosyncratic (higher D&O risk) or market-wide (lower risk). DDL exposure line from peak to trough quantifies potential securities class action damages.",
        "func": chart_2_perf_2y,
    },
    {
        "id": "perf-5y",
        "title": "3. 5-Year Weekly Performance",
        "desc": "Longer-term view shows structural trends and whether current performance represents a reversal from historical pattern. Weekly resampling smooths noise while preserving major movements.",
        "func": chart_3_perf_5y,
    },
    {
        "id": "drawdown",
        "title": "4. Drawdown From Peak",
        "desc": "Running drawdown from all-time high shows severity and duration of declines. Drops exceeding -20% historically correlate with securities litigation filing probability above 8%.",
        "func": chart_4_drawdown,
    },
    {
        "id": "earnings",
        "title": "5. Earnings Surprise History",
        "desc": "Consistent beats suggest strong disclosure practices (lower D&O risk). Misses, especially after management guidance, create corrective disclosure events that trigger securities class actions.",
        "func": chart_5_earnings_surprise,
    },
    {
        "id": "insider",
        "title": "6. Insider Trading Detail",
        "desc": "Executive trading patterns are the #1 scienter indicator in securities litigation. Large sales before drops establish 'knowledge and intent' in 10b-5 claims. Cumulative net position shows insider confidence trend.",
        "func": chart_6_insider_detail,
    },
    {
        "id": "drops",
        "title": "7. Significant Drops Analysis",
        "desc": "Distinguishes company-specific drops (high D&O risk, actionable) from market-wide selloffs (lower risk, less likely to support securities claims). Company-specific drops with >10% abnormal return are strong SCA indicators.",
        "func": chart_7_drops_analysis,
    },
    {
        "id": "volatility",
        "title": "8. Rolling Volatility vs Sector",
        "desc": "Elevated volatility relative to sector peers indicates company-specific risk factors. Volatility spikes above 2x average often coincide with material events that may generate claims.",
        "func": chart_8_rolling_vol,
    },
    {
        "id": "reaction",
        "title": "9. Earnings Reaction Analysis",
        "desc": "Compares EPS surprise magnitude to actual stock reaction. Disproportionate negative reactions to small misses suggest market distrust of management credibility -- a D&O risk amplifier.",
        "func": chart_9_earnings_reaction,
    },
    {
        "id": "sparklines",
        "title": "10. Financial Health Sparklines",
        "desc": "Six key financial metrics at a glance. Deteriorating trends in margins, rising leverage, or declining free cash flow increase probability of restatement risk and securities claims.",
        "func": chart_10_financial_sparklines,
    },
    {
        "id": "ddl-scenarios",
        "title": "11. DDL Exposure Scenarios",
        "desc": "Projects Dollar-Day-Loss exposure under stress scenarios. Shows how additional 10-30% stock declines would increase potential securities class action damages beyond current levels.",
        "func": chart_11_ddl_scenarios,
    },
    {
        "id": "suspicious",
        "title": "12. Suspicious Trading Windows",
        "desc": "Maps insider sales against 30-day pre-drop windows. Sales within these windows are 'smoking gun' evidence in securities litigation, establishing that insiders traded on material non-public information.",
        "func": chart_12_suspicious_windows,
    },
]


def build_html(charts, company_name, score, tier):
    """Build the final HTML page."""
    toc = []
    cards = []
    for c in charts:
        toc.append(f'<li><a href="#{c["id"]}">{c["title"]}</a></li>')
        if c.get("error"):
            img_html = f'<p style="color:#DC2626;padding:20px;">{c["error"]}</p>'
        else:
            img_html = f'<img src="data:image/png;base64,{c["b64"]}" style="width:100%;" alt="{c["title"]}">'
        cards.append(f"""
        <div id="{c['id']}" style="background:white;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);
            margin-bottom:24px;overflow:hidden;">
            <div style="padding:16px 20px 8px;">
                <h3 style="margin:0 0 4px;font-size:16px;color:#1E3A5F;">{c['title']}</h3>
                <p style="margin:0 0 8px;font-size:12px;color:#6B7280;line-height:1.4;">{c['desc']}</p>
            </div>
            <div style="padding:0 12px 12px;">
                {img_html}
            </div>
        </div>
        """)

    tier_colors = {
        "WIN": "#059669", "WRITE": "#3B82F6", "WATCH": "#F59E0B",
        "WALK": "#F97316", "WITHDRAW": "#DC2626",
    }
    tier_color = tier_colors.get(tier, "#6B7280")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} - D&amp;O Underwriting Charts</title>
<style>
    body {{ font-family: Arial, 'DejaVu Sans', sans-serif; background: #FAFAFA; margin: 0; padding: 0; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .header {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
               padding: 20px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .header h1 {{ margin: 0; font-size: 22px; color: #1E3A5F; }}
    .header .meta {{ text-align: right; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold;
              font-size: 13px; color: white; background: {tier_color}; }}
    .score {{ font-size: 28px; font-weight: bold; color: #1E3A5F; margin-right: 8px; }}
    .toc {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            padding: 16px 24px; margin-bottom: 24px; }}
    .toc h2 {{ margin: 0 0 8px; font-size: 14px; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; }}
    .toc ol {{ margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; }}
    .toc li {{ font-size: 13px; margin-bottom: 4px; }}
    .toc a {{ color: #1E3A5F; text-decoration: none; }}
    .toc a:hover {{ text-decoration: underline; }}
    img {{ display: block; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1>{company_name} -- D&amp;O Underwriting Charts</h1>
            <p style="margin:4px 0 0;font-size:12px;color:#6B7280;">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | All data from pipeline state</p>
        </div>
        <div class="meta">
            <span class="score">{score:.1f}</span>
            <span class="badge">{tier}</span>
        </div>
    </div>
    <div class="toc">
        <h2>Table of Contents</h2>
        <ol>{''.join(toc)}</ol>
    </div>
    {''.join(cards)}
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    state_path = STATE_PATH
    if not state_path.exists():
        print(f"ERROR: {state_path} not found")
        sys.exit(1)

    print(f"Loading state from {state_path}...")
    with open(state_path) as f:
        state = json.load(f)

    md = state.get("acquired_data", {}).get("market_data", {})
    info = md.get("info", {})
    company_name = info.get("longName", info.get("shortName", "Company"))
    global ticker
    ticker = state.get("ticker", info.get("symbol", "???"))
    score = safe_float(state.get("scoring", {}).get("composite_score"), 0)
    tier_data = state.get("scoring", {}).get("tier", {})
    tier = tier_data.get("tier", "N/A") if isinstance(tier_data, dict) else str(tier_data)

    charts = []
    for cdef in CHART_DEFS:
        print(f"  Generating: {cdef['title']}...")
        try:
            fig, error = cdef["func"](state, md)
            if fig:
                b64 = fig_to_base64(fig)
                charts.append({"id": cdef["id"], "title": cdef["title"], "desc": cdef["desc"], "b64": b64})
            else:
                charts.append({"id": cdef["id"], "title": cdef["title"], "desc": cdef["desc"], "error": error or "No data available"})
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            charts.append({"id": cdef["id"], "title": cdef["title"], "desc": cdef["desc"], "error": str(e)})

    # Build HTML
    html = build_html(charts, company_name, score, tier)

    # Write output
    out_dir = STATE_PATH.parent.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "all_charts.html"
    with open(out_path, "w") as f:
        f.write(html)

    print(f"\nDone! Output: {out_path}")
    print(f"  Charts generated: {sum(1 for c in charts if 'b64' in c)}/{len(charts)}")
    print(f"  Charts failed: {sum(1 for c in charts if 'error' in c)}/{len(charts)}")


if __name__ == "__main__":
    main()
