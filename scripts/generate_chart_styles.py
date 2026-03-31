#!/usr/bin/env python3
"""Generate 10 different visual styles of the same AAPL stock chart.

All charts show identical data overlays (3 lines, earnings, insider trades,
DDL, volume, labels, badges). Only visual style differs.

Output: output/AAPL/chart_styles.html
"""

import base64
import json
import io
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def load_state():
    p = Path(__file__).resolve().parent.parent / "output" / "AAPL" / "2026-03-22" / "state.json"
    with open(p) as f:
        return json.load(f)


def parse_dates(date_strings):
    """Parse date strings to datetime objects."""
    out = []
    for d in date_strings:
        try:
            # Strip timezone info for matplotlib
            ds = d.split("+")[0].split("-04:00")[0].split("-05:00")[0].strip()
            out.append(datetime.strptime(ds, "%Y-%m-%d %H:%M:%S"))
        except Exception:
            try:
                out.append(datetime.strptime(d[:10], "%Y-%m-%d"))
            except Exception:
                out.append(datetime.now())
    return out


def compute_pct_return(closes):
    """Convert close prices to % return from first value."""
    base = safe_float(closes[0], 1.0)
    if base == 0:
        base = 1.0
    return [(safe_float(c, base) / base - 1) * 100 for c in closes]


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def extract_chart_data(state):
    md = state["acquired_data"]["market_data"]
    h2y = md["history_2y"]
    sh = md["sector_history_2y"]
    spy = md["spy_history_2y"]
    info = md.get("info", {})
    ed = md.get("earnings_dates", {})
    it = md.get("insider_transactions", {})

    # Main series
    dates = parse_dates(h2y["Date"])
    closes = [safe_float(c) for c in h2y["Close"]]
    volumes = [safe_float(v) for v in h2y["Volume"]]

    # % returns
    aapl_ret = compute_pct_return(closes)

    # Sector
    sector_dates = parse_dates(sh["Date"])
    sector_closes = [safe_float(c) for c in sh["Close"]]
    sector_ret = compute_pct_return(sector_closes)

    # SPY
    spy_dates = parse_dates(spy["Date"])
    spy_closes = [safe_float(c) for c in spy["Close"]]
    spy_ret = compute_pct_return(spy_closes)

    # DDL: peak to trough
    peak_idx = int(np.argmax(closes))
    # Find trough AFTER peak
    if peak_idx < len(closes) - 1:
        trough_idx = peak_idx + int(np.argmin(closes[peak_idx:]))
    else:
        trough_idx = peak_idx
    peak_price = closes[peak_idx]
    trough_price = closes[trough_idx]
    peak_date = dates[peak_idx]
    trough_date = dates[trough_idx]
    ddl_drop_pct = (trough_price - peak_price) / peak_price * 100 if peak_price else 0
    mkt_cap_at_peak = safe_float(info.get("marketCap", 0))
    # Rough loss estimate
    ddl_loss_b = abs(peak_price - trough_price) / peak_price * mkt_cap_at_peak / 1e9 if peak_price else 0

    # 52W high/low
    w52_high = safe_float(info.get("fiftyTwoWeekHigh", max(closes)))
    w52_low = safe_float(info.get("fiftyTwoWeekLow", min(closes)))
    current = safe_float(info.get("currentPrice", closes[-1]))

    # Earnings (only those within our date range and with reported data)
    earnings = []
    if ed.get("Earnings Date"):
        for i, edate_str in enumerate(ed["Earnings Date"]):
            reported = ed.get("Reported EPS", [None] * (i + 1))
            surprise = ed.get("Surprise(%)", [None] * (i + 1))
            rep_val = reported[i] if i < len(reported) else None
            surp_val = surprise[i] if i < len(surprise) else None
            if rep_val is None or surp_val is None:
                continue
            try:
                edt = parse_dates([edate_str])[0]
                if dates[0] <= edt <= dates[-1]:
                    # Find closest date index for return position
                    closest_idx = min(range(len(dates)), key=lambda j: abs((dates[j] - edt).total_seconds()))
                    earnings.append({
                        "date": edt,
                        "idx": closest_idx,
                        "surprise_pct": safe_float(surp_val),
                        "reported_eps": safe_float(rep_val),
                    })
            except Exception:
                pass

    # Insider transactions
    insiders = []
    if it.get("Start Date"):
        n = len(it["Start Date"])
        for i in range(n):
            try:
                idate = datetime.strptime(it["Start Date"][i][:10], "%Y-%m-%d")
                shares = safe_float(it["Shares"][i])
                text = it.get("Text", [""] * (i + 1))[i] or ""
                val = safe_float(it.get("Value", [0] * (i + 1))[i])
                # Determine buy vs sale
                is_sale = "Sale" in text or val > 0 and "Gift" not in text
                is_buy = "Purchase" in text or "Buy" in text
                if "Gift" in text or "Award" in text:
                    continue  # Skip gifts/awards
                if not is_sale and not is_buy:
                    # Default: if text mentions "Sale" or value > threshold
                    is_sale = True  # Most insider transactions are sales
                if dates[0] <= idate <= dates[-1]:
                    closest_idx = min(range(len(dates)), key=lambda j: abs((dates[j] - idate).total_seconds()))
                    insiders.append({
                        "date": idate,
                        "idx": closest_idx,
                        "shares": shares,
                        "is_sale": is_sale,
                        "insider": it.get("Insider", [""] * (i + 1))[i],
                    })
            except Exception:
                pass

    # Risk stats
    si_pct = safe_float(info.get("shortPercentOfFloat", 0)) * 100
    beta = safe_float(info.get("beta", 0))
    insider_pct = safe_float(info.get("heldPercentInsiders", 0)) * 100

    # Max drawdown
    running_max = 0
    max_dd = 0
    for c in closes:
        running_max = max(running_max, c)
        dd = (c - running_max) / running_max * 100 if running_max else 0
        max_dd = min(max_dd, dd)

    return {
        "dates": dates,
        "closes": closes,
        "volumes": volumes,
        "aapl_ret": aapl_ret,
        "sector_dates": sector_dates,
        "sector_ret": sector_ret,
        "spy_dates": spy_dates,
        "spy_ret": spy_ret,
        "peak_idx": peak_idx,
        "trough_idx": trough_idx,
        "peak_price": peak_price,
        "trough_price": trough_price,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "ddl_drop_pct": ddl_drop_pct,
        "ddl_loss_b": ddl_loss_b,
        "w52_high": w52_high,
        "w52_low": w52_low,
        "current": current,
        "earnings": earnings,
        "insiders": insiders,
        "si_pct": si_pct,
        "beta": beta,
        "insider_pct": insider_pct,
        "max_dd": max_dd,
        "sector": info.get("sector", "Technology"),
    }


# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------

STYLES = [
    {
        "name": "Bloomberg Terminal",
        "desc": "Dark background, green/cyan lines, monospace font, dense grid, terminal aesthetic",
        "bg": "#1B1B2F",
        "chart_bg": "#1B1B2F",
        "grid_color": "#2A2A4A",
        "grid_alpha": 0.6,
        "aapl_color": "#00FF88",
        "sector_color": "#00BFFF",
        "spy_color": "#FFD700",
        "fill_up": "#00FF8833",
        "fill_down": "#FF444433",
        "text_color": "#E0E0E0",
        "label_color": "#CCCCCC",
        "font": "monospace",
        "title_font": "monospace",
        "line_width": 1.5,
        "ddl_color": "#FF4444",
        "vol_color": "#3A3A5A",
        "vol_spike": "#FF8C00",
        "badge_bg": "#2A2A4A",
        "badge_border": "#00FF88",
        "badge_text": "#00FF88",
        "legend_bg": "#1B1B2F",
        "legend_border": "#3A3A5A",
        "earn_diamond": "#FFD700",
        "earn_text": "#FFD700",
        "axis_color": "#4A4A6A",
    },
    {
        "name": "Google Finance",
        "desc": "Clean white, green line when up, minimal chrome, subtle gray grid, modern sans-serif",
        "bg": "#FFFFFF",
        "chart_bg": "#FFFFFF",
        "grid_color": "#EEEEEE",
        "grid_alpha": 0.8,
        "aapl_color": "#0B8043",
        "sector_color": "#1A73E8",
        "spy_color": "#9334E6",
        "fill_up": "#0B804322",
        "fill_down": "#D9304722",
        "text_color": "#202124",
        "label_color": "#5F6368",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.0,
        "ddl_color": "#D93047",
        "vol_color": "#DADCE0",
        "vol_spike": "#F29900",
        "badge_bg": "#F1F3F4",
        "badge_border": "#DADCE0",
        "badge_text": "#202124",
        "legend_bg": "#FFFFFF",
        "legend_border": "#DADCE0",
        "earn_diamond": "#F29900",
        "earn_text": "#202124",
        "axis_color": "#DADCE0",
    },
    {
        "name": "TradingView",
        "desc": "Slightly warm white background, bold colored lines, semi-transparent fills, clean axes",
        "bg": "#FAFAFA",
        "chart_bg": "#FAFAFA",
        "grid_color": "#E8E8E8",
        "grid_alpha": 0.5,
        "aapl_color": "#2196F3",
        "sector_color": "#FF9800",
        "spy_color": "#9C27B0",
        "fill_up": "#4CAF5030",
        "fill_down": "#F4433630",
        "text_color": "#131722",
        "label_color": "#787B86",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.0,
        "ddl_color": "#F44336",
        "vol_color": "#D1D4DC",
        "vol_spike": "#FF9800",
        "badge_bg": "#F0F3FA",
        "badge_border": "#D1D4DC",
        "badge_text": "#131722",
        "legend_bg": "#FAFAFA",
        "legend_border": "#D1D4DC",
        "earn_diamond": "#FF9800",
        "earn_text": "#131722",
        "axis_color": "#D1D4DC",
    },
    {
        "name": "S&P Capital IQ",
        "desc": "Navy header strip, conservative palette, serif-like professionalism, dense data",
        "bg": "#F5F5F5",
        "chart_bg": "#FFFFFF",
        "grid_color": "#E0E0E0",
        "grid_alpha": 0.7,
        "aapl_color": "#1F3A5C",
        "sector_color": "#4A90D9",
        "spy_color": "#7B7B7B",
        "fill_up": "#1F3A5C18",
        "fill_down": "#C0392B18",
        "text_color": "#1F3A5C",
        "label_color": "#555555",
        "font": "serif",
        "title_font": "serif",
        "line_width": 1.8,
        "ddl_color": "#C0392B",
        "vol_color": "#CCCCCC",
        "vol_spike": "#E67E22",
        "badge_bg": "#EAEEF3",
        "badge_border": "#1F3A5C",
        "badge_text": "#1F3A5C",
        "legend_bg": "#FFFFFF",
        "legend_border": "#1F3A5C",
        "earn_diamond": "#E67E22",
        "earn_text": "#1F3A5C",
        "axis_color": "#CCCCCC",
    },
    {
        "name": "Koyfin",
        "desc": "Modern dark (#0F172A), vibrant accent colors, rounded corners aesthetic, clean typography",
        "bg": "#0F172A",
        "chart_bg": "#0F172A",
        "grid_color": "#1E293B",
        "grid_alpha": 0.6,
        "aapl_color": "#38BDF8",
        "sector_color": "#A78BFA",
        "spy_color": "#FB923C",
        "fill_up": "#22C55E25",
        "fill_down": "#EF444425",
        "text_color": "#E2E8F0",
        "label_color": "#94A3B8",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.0,
        "ddl_color": "#EF4444",
        "vol_color": "#1E293B",
        "vol_spike": "#FB923C",
        "badge_bg": "#1E293B",
        "badge_border": "#38BDF8",
        "badge_text": "#38BDF8",
        "legend_bg": "#0F172A",
        "legend_border": "#1E293B",
        "earn_diamond": "#FBBF24",
        "earn_text": "#FBBF24",
        "axis_color": "#334155",
    },
    {
        "name": "FT / WSJ",
        "desc": "Salmon/pink background, FT-style black lines, minimal decoration, journalistic",
        "bg": "#FFF1E6",
        "chart_bg": "#FFF1E6",
        "grid_color": "#E8D5C4",
        "grid_alpha": 0.5,
        "aapl_color": "#000000",
        "sector_color": "#990F3D",
        "spy_color": "#0D7680",
        "fill_up": "#00000010",
        "fill_down": "#990F3D15",
        "text_color": "#33302E",
        "label_color": "#66605C",
        "font": "serif",
        "title_font": "serif",
        "line_width": 2.0,
        "ddl_color": "#CC0000",
        "vol_color": "#DBC8B5",
        "vol_spike": "#FF8833",
        "badge_bg": "#F2DFCE",
        "badge_border": "#33302E",
        "badge_text": "#33302E",
        "legend_bg": "#FFF1E6",
        "legend_border": "#CCC1B7",
        "earn_diamond": "#FF8833",
        "earn_text": "#33302E",
        "axis_color": "#CCC1B7",
    },
    {
        "name": "Morningstar",
        "desc": "Clean with blue (#00A3E0) accent, structured grid, analytical feel",
        "bg": "#FFFFFF",
        "chart_bg": "#FFFFFF",
        "grid_color": "#E5E5E5",
        "grid_alpha": 0.7,
        "aapl_color": "#00A3E0",
        "sector_color": "#FF6600",
        "spy_color": "#666666",
        "fill_up": "#00A3E018",
        "fill_down": "#CC000018",
        "text_color": "#222222",
        "label_color": "#666666",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.0,
        "ddl_color": "#CC0000",
        "vol_color": "#D9D9D9",
        "vol_spike": "#FF6600",
        "badge_bg": "#E8F4FD",
        "badge_border": "#00A3E0",
        "badge_text": "#00648C",
        "legend_bg": "#FFFFFF",
        "legend_border": "#CCCCCC",
        "earn_diamond": "#FF6600",
        "earn_text": "#222222",
        "axis_color": "#CCCCCC",
    },
    {
        "name": "FactSet",
        "desc": "Professional gray palette, structured layout, institutional density",
        "bg": "#F0F0F0",
        "chart_bg": "#FAFAFA",
        "grid_color": "#DCDCDC",
        "grid_alpha": 0.8,
        "aapl_color": "#003366",
        "sector_color": "#CC6600",
        "spy_color": "#669999",
        "fill_up": "#00336612",
        "fill_down": "#99000012",
        "text_color": "#333333",
        "label_color": "#666666",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 1.8,
        "ddl_color": "#990000",
        "vol_color": "#D0D0D0",
        "vol_spike": "#CC6600",
        "badge_bg": "#E8ECF0",
        "badge_border": "#003366",
        "badge_text": "#003366",
        "legend_bg": "#FAFAFA",
        "legend_border": "#BBBBBB",
        "earn_diamond": "#CC6600",
        "earn_text": "#333333",
        "axis_color": "#BBBBBB",
    },
    {
        "name": "Refinitiv / Eikon",
        "desc": "Blue theme (#003366), clean modernist, gradient accents",
        "bg": "#002244",
        "chart_bg": "#002244",
        "grid_color": "#003366",
        "grid_alpha": 0.5,
        "aapl_color": "#4FC3F7",
        "sector_color": "#FFB74D",
        "spy_color": "#CE93D8",
        "fill_up": "#4FC3F720",
        "fill_down": "#EF535020",
        "text_color": "#E0E0E0",
        "label_color": "#90A4AE",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.0,
        "ddl_color": "#EF5350",
        "vol_color": "#1A3A5C",
        "vol_spike": "#FFB74D",
        "badge_bg": "#0A3A5C",
        "badge_border": "#4FC3F7",
        "badge_text": "#4FC3F7",
        "legend_bg": "#002244",
        "legend_border": "#003366",
        "earn_diamond": "#FFB74D",
        "earn_text": "#FFB74D",
        "axis_color": "#1A4466",
    },
    {
        "name": "Custom D&O Underwriting",
        "desc": "White background, navy (#1F3A5C) accents, gold (#D4A843) highlights, DDL prominence, insider emphasis",
        "bg": "#FFFFFF",
        "chart_bg": "#FFFFFF",
        "grid_color": "#EAEEF3",
        "grid_alpha": 0.6,
        "aapl_color": "#1F3A5C",
        "sector_color": "#7BA7CC",
        "spy_color": "#B0B0B0",
        "fill_up": "#1F3A5C15",
        "fill_down": "#C0392B20",
        "text_color": "#1F3A5C",
        "label_color": "#5A6F82",
        "font": "sans-serif",
        "title_font": "sans-serif",
        "line_width": 2.2,
        "ddl_color": "#C0392B",
        "vol_color": "#D6DDE5",
        "vol_spike": "#D4A843",
        "badge_bg": "#F5F0E5",
        "badge_border": "#D4A843",
        "badge_text": "#1F3A5C",
        "legend_bg": "#FFFFFF",
        "legend_border": "#1F3A5C",
        "earn_diamond": "#D4A843",
        "earn_text": "#1F3A5C",
        "axis_color": "#C5CDD6",
    },
]


# ---------------------------------------------------------------------------
# Chart rendering
# ---------------------------------------------------------------------------

def render_chart(data, style, idx):
    """Render a single chart with all overlays in the given style."""
    fig, (ax_main, ax_vol) = plt.subplots(
        2, 1, figsize=(16, 6), dpi=150,
        gridspec_kw={"height_ratios": [4, 1], "hspace": 0.05},
        facecolor=style["bg"],
    )
    ax_main.set_facecolor(style["chart_bg"])
    ax_vol.set_facecolor(style["chart_bg"])

    dates = data["dates"]
    aapl_ret = data["aapl_ret"]

    # --- Grid ---
    ax_main.grid(True, color=style["grid_color"], alpha=style["grid_alpha"], linewidth=0.5)
    ax_vol.grid(True, color=style["grid_color"], alpha=style["grid_alpha"], linewidth=0.5)

    # --- 3 return lines ---
    ax_main.plot(dates, aapl_ret, color=style["aapl_color"], linewidth=style["line_width"],
                 label="AAPL", zorder=5)
    ax_main.plot(data["sector_dates"], data["sector_ret"], color=style["sector_color"],
                 linewidth=1.2, label=f'{data["sector"]} ETF', zorder=4, alpha=0.8)
    ax_main.plot(data["spy_dates"], data["spy_ret"], color=style["spy_color"],
                 linewidth=1.2, label="S&P 500", zorder=4, alpha=0.8)

    # --- Green/red area fill under AAPL ---
    zero_line = [0] * len(aapl_ret)
    ax_main.fill_between(dates, aapl_ret, zero_line,
                         where=[r >= 0 for r in aapl_ret],
                         color=style["fill_up"], interpolate=True, zorder=2)
    ax_main.fill_between(dates, aapl_ret, zero_line,
                         where=[r < 0 for r in aapl_ret],
                         color=style["fill_down"], interpolate=True, zorder=2)

    # Zero line
    ax_main.axhline(y=0, color=style["axis_color"], linewidth=0.8, zorder=3)

    # --- DDL: peak-to-trough ---
    peak_ret = aapl_ret[data["peak_idx"]]
    trough_ret = aapl_ret[data["trough_idx"]]
    ax_main.plot([data["peak_date"], data["trough_date"]], [peak_ret, trough_ret],
                 color=style["ddl_color"], linewidth=2.0, linestyle="--", zorder=8)
    ddl_label = f'${data["peak_price"]:.0f}→${data["trough_price"]:.0f} (${data["ddl_loss_b"]:.0f}B)'
    mid_date = data["peak_date"] + (data["trough_date"] - data["peak_date"]) / 2
    mid_ret = (peak_ret + trough_ret) / 2
    ax_main.annotate(ddl_label,
                     xy=(mid_date, mid_ret), fontsize=7,
                     color=style["ddl_color"], fontweight="bold",
                     fontfamily=style["font"],
                     bbox=dict(boxstyle="round,pad=0.3", facecolor=style["chart_bg"],
                               edgecolor=style["ddl_color"], alpha=0.9),
                     ha="center", va="bottom", zorder=10)

    # --- 52W High / Low / Current bubbles ---
    # Find dates closest to 52W high and low
    w52h_idx = min(range(len(data["closes"])),
                   key=lambda j: abs(data["closes"][j] - data["w52_high"]))
    w52l_idx = min(range(len(data["closes"])),
                   key=lambda j: abs(data["closes"][j] - data["w52_low"]))

    for label_text, idx_pos, color_val in [
        (f'52W High ${data["w52_high"]:.0f}', w52h_idx, "#22C55E"),
        (f'52W Low ${data["w52_low"]:.0f}', w52l_idx, "#EF4444"),
        (f'Current ${data["current"]:.0f}', len(dates) - 1, "#333333" if style["bg"].startswith("#F") or style["bg"] == "#FFFFFF" else "#E0E0E0"),
    ]:
        ax_main.annotate(
            label_text,
            xy=(dates[idx_pos], aapl_ret[idx_pos]),
            xytext=(0, 14), textcoords="offset points",
            fontsize=7, fontweight="bold", color=color_val,
            fontfamily=style["font"],
            bbox=dict(boxstyle="round,pad=0.3", facecolor=style["chart_bg"],
                      edgecolor=color_val, alpha=0.85),
            ha="center", zorder=12,
            arrowprops=dict(arrowstyle="-", color=color_val, lw=0.8),
        )

    # --- Earnings diamonds ---
    for e in data["earnings"]:
        ret_val = aapl_ret[e["idx"]]
        ax_main.scatter([dates[e["idx"]]], [ret_val], marker="D",
                        color=style["earn_diamond"], s=60, zorder=11, edgecolors="white", linewidths=0.5)
        sign = "+" if e["surprise_pct"] >= 0 else ""
        ax_main.annotate(f'Beat {sign}{e["surprise_pct"]:.1f}%',
                         xy=(dates[e["idx"]], ret_val),
                         xytext=(0, -16), textcoords="offset points",
                         fontsize=7, color=style["earn_text"], fontweight="bold",
                         fontfamily=style["font"], ha="center", zorder=12)

    # --- Insider trade markers ---
    insider_dates_for_vol = set()
    max_shares = max((ins["shares"] for ins in data["insiders"]), default=1) or 1
    for ins in data["insiders"]:
        ret_val = aapl_ret[ins["idx"]]
        marker = "v" if ins["is_sale"] else "^"
        color = "#EF4444" if ins["is_sale"] else "#22C55E"
        size = max(30, min(200, ins["shares"] / max_shares * 200))
        ax_main.scatter([dates[ins["idx"]]], [ret_val], marker=marker,
                        color=color, s=size, zorder=11, edgecolors="white", linewidths=0.5, alpha=0.8)
        insider_dates_for_vol.add(ins["idx"])

    # --- Return labels on right edge ---
    final_aapl = aapl_ret[-1]
    final_sector = data["sector_ret"][-1] if data["sector_ret"] else 0
    final_spy = data["spy_ret"][-1] if data["spy_ret"] else 0

    for label, val, color in [
        ("AAPL", final_aapl, style["aapl_color"]),
        ("Sector", final_sector, style["sector_color"]),
        ("SPY", final_spy, style["spy_color"]),
    ]:
        sign = "+" if val >= 0 else ""
        ax_main.annotate(f'{label} {sign}{val:.1f}%',
                         xy=(dates[-1], val),
                         xytext=(10, 0), textcoords="offset points",
                         fontsize=8, fontweight="bold", color=color,
                         fontfamily=style["font"], ha="left", va="center", zorder=12,
                         bbox=dict(boxstyle="round,pad=0.2", facecolor=style["chart_bg"],
                                   edgecolor=color, alpha=0.9))

    # --- Volume bars ---
    avg_vol = np.mean(data["volumes"]) if data["volumes"] else 1
    vol_colors = []
    for i, v in enumerate(data["volumes"]):
        if i in insider_dates_for_vol:
            vol_colors.append(style["vol_spike"])
        elif v > 2 * avg_vol:
            vol_colors.append(style["vol_spike"])
        else:
            vol_colors.append(style["vol_color"])

    ax_vol.bar(dates, data["volumes"], color=vol_colors, width=1.5, zorder=3)

    # --- Risk stat badges ---
    badge_texts = [
        f'SI: {data["si_pct"]:.1f}%',
        f'Vol (β): {data["beta"]:.2f}',
        f'Max Drop: {data["max_dd"]:.1f}%',
        f'Insider: {data["insider_pct"]:.1f}%',
    ]
    for bi, bt in enumerate(badge_texts):
        ax_main.annotate(
            bt,
            xy=(0.01 + bi * 0.14, 0.97), xycoords="axes fraction",
            fontsize=7, fontweight="bold",
            color=style["badge_text"], fontfamily=style["font"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor=style["badge_bg"],
                      edgecolor=style["badge_border"], linewidth=1.2, alpha=0.95),
            ha="left", va="top", zorder=15,
        )

    # --- Legend ---
    legend_elements = [
        Line2D([0], [0], color=style["aapl_color"], linewidth=2, label="AAPL"),
        Line2D([0], [0], color=style["sector_color"], linewidth=1.5, label=f'{data["sector"]} ETF'),
        Line2D([0], [0], color=style["spy_color"], linewidth=1.5, label="S&P 500"),
        Line2D([0], [0], color=style["ddl_color"], linewidth=2, linestyle="--", label="DDL Drop"),
        Line2D([0], [0], marker="D", color=style["earn_diamond"], linestyle="None", markersize=6, label="Earnings"),
        Line2D([0], [0], marker="v", color="#EF4444", linestyle="None", markersize=6, label="Insider Sale"),
        Line2D([0], [0], marker="^", color="#22C55E", linestyle="None", markersize=6, label="Insider Buy"),
    ]
    leg = ax_main.legend(handles=legend_elements, loc="lower left", fontsize=7,
                         facecolor=style["legend_bg"], edgecolor=style["legend_border"],
                         framealpha=0.95, ncol=4)
    for text in leg.get_texts():
        text.set_color(style["text_color"])
        text.set_fontfamily(style["font"])

    # --- Axis formatting ---
    ax_main.set_ylabel("% Return", color=style["label_color"], fontsize=9, fontfamily=style["font"])
    ax_vol.set_ylabel("Volume", color=style["label_color"], fontsize=7, fontfamily=style["font"])

    ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax_main.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax_vol.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    for ax in [ax_main, ax_vol]:
        ax.tick_params(colors=style["label_color"], labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(style["axis_color"])
        ax.tick_params(axis='x', rotation=0)

    ax_main.set_xticklabels([])
    ax_main.yaxis.set_major_formatter(mticker.FormatStrFormatter('%+.0f%%'))

    # Volume y-axis in millions
    ax_vol.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1e6:.0f}M'))

    # Title
    ax_main.set_title(f'AAPL Stock Performance — {style["name"]} Style',
                      color=style["text_color"], fontsize=12, fontweight="bold",
                      fontfamily=style["title_font"], pad=10)

    plt.tight_layout()

    # Export to base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(),
                bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def build_html(chart_images):
    toc_items = []
    sections = []
    for i, (style, img_b64) in enumerate(chart_images):
        anchor = f"style-{i+1}"
        toc_items.append(f'<a href="#{anchor}" class="toc-link">{i+1}. {style["name"]}</a>')
        sections.append(f'''
        <div class="chart-section" id="{anchor}">
            <div class="chart-header">
                <span class="chart-number">{i+1:02d}</span>
                <div>
                    <h2>{style["name"]}</h2>
                    <p class="chart-desc">{style["desc"]}</p>
                </div>
            </div>
            <div class="chart-container">
                <img src="data:image/png;base64,{img_b64}" alt="{style['name']} chart" />
            </div>
        </div>
        ''')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AAPL Chart Style Comparison — D&O Underwriting</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #1A1A2E;
    color: #E0E0E0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 20px;
  }}
  .page-header {{
    text-align: center;
    padding: 40px 20px 30px;
  }}
  .page-header h1 {{
    font-size: 32px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 8px;
  }}
  .page-header .subtitle {{
    color: #8888AA;
    font-size: 16px;
  }}
  .toc {{
    max-width: 1200px;
    margin: 0 auto 40px;
    background: #16162A;
    border: 1px solid #2A2A4A;
    border-radius: 12px;
    padding: 24px 32px;
  }}
  .toc h3 {{
    color: #D4A843;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 16px;
  }}
  .toc-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 8px;
  }}
  .toc-link {{
    color: #8888CC;
    text-decoration: none;
    font-size: 14px;
    padding: 6px 12px;
    border-radius: 6px;
    transition: all 0.2s;
  }}
  .toc-link:hover {{
    background: #2A2A4A;
    color: #FFFFFF;
  }}
  .chart-section {{
    max-width: 1200px;
    margin: 0 auto 40px;
    background: #16162A;
    border: 1px solid #2A2A4A;
    border-radius: 12px;
    overflow: hidden;
  }}
  .chart-header {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    border-bottom: 1px solid #2A2A4A;
  }}
  .chart-number {{
    font-size: 28px;
    font-weight: 800;
    color: #D4A843;
    font-family: "SF Mono", "Fira Code", monospace;
    min-width: 48px;
  }}
  .chart-header h2 {{
    font-size: 20px;
    color: #FFFFFF;
    margin-bottom: 4px;
  }}
  .chart-desc {{
    color: #8888AA;
    font-size: 13px;
  }}
  .chart-container {{
    padding: 16px;
  }}
  .chart-container img {{
    width: 100%;
    border-radius: 8px;
    display: block;
  }}
</style>
</head>
<body>
  <div class="page-header">
    <h1>AAPL Chart Style Comparison</h1>
    <p class="subtitle">10 visual styles — same data, same overlays — D&O Underwriting Worksheet R&D</p>
  </div>

  <div class="toc">
    <h3>Table of Contents</h3>
    <div class="toc-grid">
      {"".join(toc_items)}
    </div>
  </div>

  {"".join(sections)}
</body>
</html>'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading state.json...")
    state = load_state()
    data = extract_chart_data(state)
    print(f"  {len(data['dates'])} trading days, {len(data['earnings'])} earnings events, {len(data['insiders'])} insider trades")

    chart_images = []
    for i, style in enumerate(STYLES):
        print(f"  [{i+1:2d}/10] Rendering {style['name']}...")
        img_b64 = render_chart(data, style, i)
        chart_images.append((style, img_b64))

    print("Building HTML...")
    html = build_html(chart_images)

    out_dir = Path(__file__).resolve().parent.parent / "output" / "AAPL"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "chart_styles.html"
    out_path.write_text(html)
    print(f"Done! Written to {out_path}")
    return str(out_path)


if __name__ == "__main__":
    result = main()
    print(result)
