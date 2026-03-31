#!/usr/bin/env python3
"""Generate 10 visual style variations of the Basic D&O Chart 1 combo chart.

All 10 charts have identical data and overlays — only colors, fonts, and
backgrounds change.  Output: single HTML gallery at output/{ticker}/chart_styles_mpl.html.

Usage:
    python scripts/generate_chart_styles_mpl.py [path/to/state.json]
"""

import base64
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import numpy as np  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
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


def parse_dates(date_strs):
    dates = []
    for d in date_strs:
        if d is None:
            continue
        try:
            for fmt in ["%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(d.split("-04:00")[0].split("-05:00")[0], fmt.replace("%z", ""))
                    dates.append(dt)
                    break
                except ValueError:
                    continue
            else:
                dates.append(datetime.strptime(d[:10], "%Y-%m-%d"))
        except Exception:
            continue
    return dates


def load_history(md, key):
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
    n = min(len(dates), len(closes), len(volumes))
    return dates[:n], opens[:n], highs[:n], lows[:n], closes[:n], volumes[:n]


def fmt_billions(v):
    v = safe_float(v)
    if abs(v) >= 1e9:
        return f"${v/1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def fig_to_base64(fig, bg_color="white"):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# 10 Style definitions
# ---------------------------------------------------------------------------

STYLES = [
    {
        "name": "Navy Professional",
        "desc": "White background with navy accents. The default institutional look.",
        "bg": "#FFFFFF",
        "panel_bg": "#FFFFFF",
        "ddl_panel_bg": "#FFFBFB",
        "stock_line": "#1E3A5F",
        "stock_line_drop": "#DC2626",
        "fill_up": "#16A34A",
        "fill_down": "#DC2626",
        "benchmark_spy": "#9CA3AF",
        "benchmark_sector": "#60A5FA",
        "grid": "#F3F4F6",
        "grid_lw": 0.4,
        "text": "#374151",
        "text_muted": "#9CA3AF",
        "axis_edge": "#D1D5DB",
        "earnings_beat": "#059669",
        "earnings_miss": "#DC2626",
        "insider_sale": "#DC2626",
        "insider_buy": "#059669",
        "insider_gift": "#9CA3AF",
        "ddl_fill": "#FCA5A5",
        "ddl_line": "#DC2626",
        "vol_up": "#059669",
        "vol_down": "#DC2626",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#1E3A5F",
        "pill_spy": "#9CA3AF",
        "pill_sector": "#60A5FA",
        "pill_si": "#7C3AED",
        "pill_peak": "#16A34A",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#111827",
        "ylabel_color": "#374151",
        "tick_color": "#374151",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Arial", "DejaVu Sans"],
    },
    {
        "name": "Dark Terminal",
        "desc": "Deep dark background with cyan highlights. Terminal / hacker aesthetic.",
        "bg": "#0F172A",
        "panel_bg": "#0F172A",
        "ddl_panel_bg": "#131B2E",
        "stock_line": "#22D3EE",
        "stock_line_drop": "#F87171",
        "fill_up": "#4ADE80",
        "fill_down": "#F87171",
        "benchmark_spy": "#64748B",
        "benchmark_sector": "#818CF8",
        "grid": "#1E293B",
        "grid_lw": 0.3,
        "text": "#CBD5E1",
        "text_muted": "#475569",
        "axis_edge": "#334155",
        "earnings_beat": "#4ADE80",
        "earnings_miss": "#F87171",
        "insider_sale": "#F87171",
        "insider_buy": "#4ADE80",
        "insider_gift": "#475569",
        "ddl_fill": "#7F1D1D",
        "ddl_line": "#F87171",
        "vol_up": "#4ADE80",
        "vol_down": "#F87171",
        "vol_insider": "#FBBF24",
        "pill_ticker": "#0E7490",
        "pill_spy": "#475569",
        "pill_sector": "#6366F1",
        "pill_si": "#A78BFA",
        "pill_peak": "#16A34A",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#E2E8F0",
        "ylabel_color": "#94A3B8",
        "tick_color": "#94A3B8",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"],
    },
    {
        "name": "Bloomberg Orange",
        "desc": "Dark background with signature orange/amber. Financial terminal style.",
        "bg": "#1A1A2E",
        "panel_bg": "#1A1A2E",
        "ddl_panel_bg": "#1E1A2E",
        "stock_line": "#F59E0B",
        "stock_line_drop": "#EF4444",
        "fill_up": "#D97706",
        "fill_down": "#EF4444",
        "benchmark_spy": "#6B7280",
        "benchmark_sector": "#F97316",
        "grid": "#27274A",
        "grid_lw": 0.3,
        "text": "#D1D5DB",
        "text_muted": "#6B7280",
        "axis_edge": "#374151",
        "earnings_beat": "#10B981",
        "earnings_miss": "#EF4444",
        "insider_sale": "#EF4444",
        "insider_buy": "#10B981",
        "insider_gift": "#6B7280",
        "ddl_fill": "#7F1D1D",
        "ddl_line": "#EF4444",
        "vol_up": "#10B981",
        "vol_down": "#EF4444",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#B45309",
        "pill_spy": "#4B5563",
        "pill_sector": "#EA580C",
        "pill_si": "#8B5CF6",
        "pill_peak": "#059669",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#F3F4F6",
        "ylabel_color": "#9CA3AF",
        "tick_color": "#9CA3AF",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    },
    {
        "name": "Clean White",
        "desc": "Pure white background, black line. Maximum clarity with minimal chrome.",
        "bg": "#FFFFFF",
        "panel_bg": "#FFFFFF",
        "ddl_panel_bg": "#FEFEFE",
        "stock_line": "#111827",
        "stock_line_drop": "#DC2626",
        "fill_up": "#D1FAE5",
        "fill_down": "#FEE2E2",
        "benchmark_spy": "#D1D5DB",
        "benchmark_sector": "#93C5FD",
        "grid": "#F9FAFB",
        "grid_lw": 0.2,
        "text": "#1F2937",
        "text_muted": "#9CA3AF",
        "axis_edge": "#E5E7EB",
        "earnings_beat": "#059669",
        "earnings_miss": "#DC2626",
        "insider_sale": "#DC2626",
        "insider_buy": "#059669",
        "insider_gift": "#D1D5DB",
        "ddl_fill": "#FEE2E2",
        "ddl_line": "#EF4444",
        "vol_up": "#059669",
        "vol_down": "#DC2626",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#111827",
        "pill_spy": "#D1D5DB",
        "pill_sector": "#93C5FD",
        "pill_si": "#8B5CF6",
        "pill_peak": "#059669",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#111827",
        "ylabel_color": "#6B7280",
        "tick_color": "#6B7280",
        "line_lw": 1.8,
        "drop_lw": 2.0,
        "max_drop_lw": 2.5,
        "font": ["SF Pro Display", "Helvetica Neue", "Arial", "DejaVu Sans"],
    },
    {
        "name": "Warm Earth",
        "desc": "Cream background with brown/amber tones. Warm, organic palette.",
        "bg": "#FFFBF5",
        "panel_bg": "#FFFBF5",
        "ddl_panel_bg": "#FFF8F0",
        "stock_line": "#78350F",
        "stock_line_drop": "#B91C1C",
        "fill_up": "#A16207",
        "fill_down": "#B91C1C",
        "benchmark_spy": "#A8A29E",
        "benchmark_sector": "#D97706",
        "grid": "#F5F0E8",
        "grid_lw": 0.4,
        "text": "#44403C",
        "text_muted": "#A8A29E",
        "axis_edge": "#D6D3D1",
        "earnings_beat": "#15803D",
        "earnings_miss": "#B91C1C",
        "insider_sale": "#B91C1C",
        "insider_buy": "#15803D",
        "insider_gift": "#A8A29E",
        "ddl_fill": "#FECACA",
        "ddl_line": "#B91C1C",
        "vol_up": "#15803D",
        "vol_down": "#B91C1C",
        "vol_insider": "#D97706",
        "pill_ticker": "#78350F",
        "pill_spy": "#78716C",
        "pill_sector": "#B45309",
        "pill_si": "#7E22CE",
        "pill_peak": "#15803D",
        "pill_trough": "#B91C1C",
        "pill_drop": "#B91C1C",
        "pill_text": "white",
        "title_color": "#292524",
        "ylabel_color": "#57534E",
        "tick_color": "#57534E",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Georgia", "Palatino", "Times New Roman", "DejaVu Serif"],
    },
    {
        "name": "Ice Blue",
        "desc": "Light blue background with deep blue line. Cool, clinical palette.",
        "bg": "#F0F9FF",
        "panel_bg": "#F0F9FF",
        "ddl_panel_bg": "#FFF1F2",
        "stock_line": "#1E40AF",
        "stock_line_drop": "#DC2626",
        "fill_up": "#1D4ED8",
        "fill_down": "#DC2626",
        "benchmark_spy": "#94A3B8",
        "benchmark_sector": "#38BDF8",
        "grid": "#E0F2FE",
        "grid_lw": 0.4,
        "text": "#1E3A5F",
        "text_muted": "#94A3B8",
        "axis_edge": "#BAE6FD",
        "earnings_beat": "#059669",
        "earnings_miss": "#DC2626",
        "insider_sale": "#DC2626",
        "insider_buy": "#059669",
        "insider_gift": "#94A3B8",
        "ddl_fill": "#FCA5A5",
        "ddl_line": "#DC2626",
        "vol_up": "#059669",
        "vol_down": "#DC2626",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#1E40AF",
        "pill_spy": "#64748B",
        "pill_sector": "#0284C7",
        "pill_si": "#7C3AED",
        "pill_peak": "#059669",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#0F172A",
        "ylabel_color": "#334155",
        "tick_color": "#334155",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Avenir", "Segoe UI", "Arial", "DejaVu Sans"],
    },
    {
        "name": "High Contrast",
        "desc": "White background, heavy black line, bold colors. Optimised for printing.",
        "bg": "#FFFFFF",
        "panel_bg": "#FFFFFF",
        "ddl_panel_bg": "#FFF5F5",
        "stock_line": "#000000",
        "stock_line_drop": "#CC0000",
        "fill_up": "#008800",
        "fill_down": "#CC0000",
        "benchmark_spy": "#888888",
        "benchmark_sector": "#4488DD",
        "grid": "#E8E8E8",
        "grid_lw": 0.6,
        "text": "#000000",
        "text_muted": "#666666",
        "axis_edge": "#999999",
        "earnings_beat": "#008800",
        "earnings_miss": "#CC0000",
        "insider_sale": "#CC0000",
        "insider_buy": "#008800",
        "insider_gift": "#888888",
        "ddl_fill": "#FFAAAA",
        "ddl_line": "#CC0000",
        "vol_up": "#008800",
        "vol_down": "#CC0000",
        "vol_insider": "#CC8800",
        "pill_ticker": "#000000",
        "pill_spy": "#666666",
        "pill_sector": "#2266BB",
        "pill_si": "#6622AA",
        "pill_peak": "#006600",
        "pill_trough": "#CC0000",
        "pill_drop": "#CC0000",
        "pill_text": "white",
        "title_color": "#000000",
        "ylabel_color": "#333333",
        "tick_color": "#333333",
        "line_lw": 3.0,
        "drop_lw": 3.5,
        "max_drop_lw": 4.0,
        "font": ["Arial Black", "Helvetica Neue", "Arial", "DejaVu Sans"],
    },
    {
        "name": "Sage Green",
        "desc": "Light green background with dark green line. Nature-inspired calm palette.",
        "bg": "#F0FDF4",
        "panel_bg": "#F0FDF4",
        "ddl_panel_bg": "#FFF1F2",
        "stock_line": "#14532D",
        "stock_line_drop": "#DC2626",
        "fill_up": "#166534",
        "fill_down": "#DC2626",
        "benchmark_spy": "#9CA3AF",
        "benchmark_sector": "#34D399",
        "grid": "#DCFCE7",
        "grid_lw": 0.4,
        "text": "#14532D",
        "text_muted": "#6B7280",
        "axis_edge": "#BBF7D0",
        "earnings_beat": "#059669",
        "earnings_miss": "#DC2626",
        "insider_sale": "#DC2626",
        "insider_buy": "#059669",
        "insider_gift": "#9CA3AF",
        "ddl_fill": "#FCA5A5",
        "ddl_line": "#DC2626",
        "vol_up": "#059669",
        "vol_down": "#DC2626",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#14532D",
        "pill_spy": "#6B7280",
        "pill_sector": "#059669",
        "pill_si": "#7C3AED",
        "pill_peak": "#059669",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#052E16",
        "ylabel_color": "#166534",
        "tick_color": "#166534",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Gill Sans", "Optima", "Arial", "DejaVu Sans"],
    },
    {
        "name": "Slate Modern",
        "desc": "Neutral slate grays with cool undertones. Modern, professional SaaS feel.",
        "bg": "#F8FAFC",
        "panel_bg": "#F8FAFC",
        "ddl_panel_bg": "#FEF2F2",
        "stock_line": "#334155",
        "stock_line_drop": "#E11D48",
        "fill_up": "#475569",
        "fill_down": "#E11D48",
        "benchmark_spy": "#CBD5E1",
        "benchmark_sector": "#7DD3FC",
        "grid": "#F1F5F9",
        "grid_lw": 0.3,
        "text": "#334155",
        "text_muted": "#94A3B8",
        "axis_edge": "#E2E8F0",
        "earnings_beat": "#10B981",
        "earnings_miss": "#E11D48",
        "insider_sale": "#E11D48",
        "insider_buy": "#10B981",
        "insider_gift": "#94A3B8",
        "ddl_fill": "#FECDD3",
        "ddl_line": "#E11D48",
        "vol_up": "#10B981",
        "vol_down": "#E11D48",
        "vol_insider": "#F59E0B",
        "pill_ticker": "#334155",
        "pill_spy": "#94A3B8",
        "pill_sector": "#38BDF8",
        "pill_si": "#8B5CF6",
        "pill_peak": "#10B981",
        "pill_trough": "#E11D48",
        "pill_drop": "#E11D48",
        "pill_text": "white",
        "title_color": "#0F172A",
        "ylabel_color": "#475569",
        "tick_color": "#475569",
        "line_lw": 1.8,
        "drop_lw": 2.2,
        "max_drop_lw": 2.8,
        "font": ["Inter", "Segoe UI", "Roboto", "Arial", "DejaVu Sans"],
    },
    {
        "name": "Midnight Gold",
        "desc": "Near-black background with gold accents. Luxury / premium feel.",
        "bg": "#0C0A09",
        "panel_bg": "#0C0A09",
        "ddl_panel_bg": "#1C1210",
        "stock_line": "#D4A843",
        "stock_line_drop": "#EF4444",
        "fill_up": "#A16207",
        "fill_down": "#EF4444",
        "benchmark_spy": "#57534E",
        "benchmark_sector": "#CA8A04",
        "grid": "#292524",
        "grid_lw": 0.3,
        "text": "#D6D3D1",
        "text_muted": "#78716C",
        "axis_edge": "#44403C",
        "earnings_beat": "#4ADE80",
        "earnings_miss": "#EF4444",
        "insider_sale": "#EF4444",
        "insider_buy": "#4ADE80",
        "insider_gift": "#57534E",
        "ddl_fill": "#7F1D1D",
        "ddl_line": "#EF4444",
        "vol_up": "#4ADE80",
        "vol_down": "#EF4444",
        "vol_insider": "#D4A843",
        "pill_ticker": "#92400E",
        "pill_spy": "#44403C",
        "pill_sector": "#854D0E",
        "pill_si": "#7E22CE",
        "pill_peak": "#15803D",
        "pill_trough": "#DC2626",
        "pill_drop": "#DC2626",
        "pill_text": "white",
        "title_color": "#FAFAF9",
        "ylabel_color": "#A8A29E",
        "tick_color": "#A8A29E",
        "line_lw": 2.0,
        "drop_lw": 2.5,
        "max_drop_lw": 3.0,
        "font": ["Didot", "Bodoni MT", "Georgia", "DejaVu Serif"],
    },
]


# ---------------------------------------------------------------------------
# Chart builder — parameterised by style dict
# ---------------------------------------------------------------------------

def chart_1_styled(state, md, ticker, style):
    """Build the 3-panel combo chart with the given visual style."""

    # ── Configure matplotlib for this style ──
    plt.rcParams.update({
        "figure.facecolor": style["bg"],
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "font.family": "sans-serif" if "Mono" not in style["font"][0] and "mono" not in style["font"][0].lower() else "monospace",
        "font.sans-serif": style["font"],
        "font.monospace": style["font"],
        "font.serif": style["font"],
        "font.size": 9,
        "text.antialiased": True,
        "lines.antialiased": True,
        "axes.facecolor": style["panel_bg"],
        "axes.edgecolor": style["axis_edge"],
        "axes.linewidth": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": style["grid"],
        "grid.linewidth": style["grid_lw"],
        "xtick.color": style["tick_color"],
        "ytick.color": style["tick_color"],
        "axes.labelcolor": style["ylabel_color"],
    })

    dates, opens, _highs, _lows, closes, volumes = load_history(md, "history_2y")
    if not dates:
        return None

    closes_arr = np.array(closes)
    dates_arr = np.array(dates)
    volumes_arr = np.array(volumes)
    info = md.get("info", {})
    shares_out = safe_float(info.get("sharesOutstanding", 0))

    # ── Rolling 60-day peak + drawdown ──
    window = 60
    rolling_peak_60 = np.copy(closes_arr)
    for i in range(len(closes_arr)):
        start = max(0, i - window)
        rolling_peak_60[i] = np.max(closes_arr[start:i + 1])
    drawdown_from_peak = (closes_arr - rolling_peak_60) / rolling_peak_60
    drop_mask = drawdown_from_peak < -0.08

    # ── Parse insider transactions ──
    ins = md.get("insider_transactions", {})
    ins_dates, ins_names, ins_values, ins_types = [], [], [], []
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
                if dates[0] <= dt <= dates[-1]:
                    ins_dates.append(dt)
                    ins_names.append(name)
                    if val == 0 and sh > 0:
                        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                        val = sh * closes[idx]
                    ins_values.append(val)
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

    # ── Parse earnings dates ──
    ed = md.get("earnings_dates", {})
    ed_dates_raw = ed.get("Earnings Date", [])
    ed_surprise = ed.get("Surprise(%)", [])
    ed_reported = ed.get("Reported EPS", [])
    earn_dates, earn_surprises = [], []
    for i, d_str in enumerate(ed_dates_raw):
        if d_str and i < len(ed_reported) and ed_reported[i] is not None:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                if dates[0] <= dt <= dates[-1]:
                    earn_dates.append(dt)
                    s_pct = safe_float(ed_surprise[i] if i < len(ed_surprise) else 0)
                    earn_surprises.append(s_pct)
            except Exception:
                pass

    # ── Compute DDL exposure ──
    ddl_exposure = np.zeros(len(closes_arr))
    for i in range(len(closes_arr)):
        drop = rolling_peak_60[i] - closes_arr[i]
        if drop > 0 and shares_out > 0:
            ddl_exposure[i] = drop * shares_out

    # ═══════════════════════════════════════════
    # Build figure
    # ═══════════════════════════════════════════
    fig = plt.figure(figsize=(16, 8))
    fig.set_facecolor(style["bg"])
    gs = fig.add_gridspec(3, 1, height_ratios=[60, 20, 20], hspace=0.08)

    # ── Panel 1: Price ──
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(style["panel_bg"])

    # Google Finance green/red fill under entire stock line
    overall_up = closes[-1] >= closes[0]
    fill_color = style["fill_up"] if overall_up else style["fill_down"]
    ax1.fill_between(dates, closes, min(closes) * 0.97, color=fill_color, alpha=0.07, zorder=0)

    # Red fill for drops >= 15%
    drop_15_mask = drawdown_from_peak < -0.15
    ax1.fill_between(dates, closes, min(closes) * 0.97,
                     where=drop_15_mask[:len(dates)],
                     color=style["fill_down"], alpha=0.25, interpolate=True, zorder=1)

    # Plot segments: normal line + red during drops
    in_drop = False
    drop_start = 0
    seg_start = 0
    drop_zones = []
    for i in range(len(drop_mask)):
        if drop_mask[i] and not in_drop:
            if seg_start < i:
                ax1.plot(dates[seg_start:i + 1], closes[seg_start:i + 1],
                         color=style["stock_line"], linewidth=style["line_lw"], zorder=3)
            drop_start = i
            in_drop = True
        elif not drop_mask[i] and in_drop:
            ax1.plot(dates[drop_start:i + 1], closes[drop_start:i + 1],
                     color=style["stock_line_drop"], linewidth=style["drop_lw"], zorder=4, alpha=0.8)
            zone = closes_arr[drop_start:i]
            trough_idx = drop_start + np.argmin(zone)
            pre_peak_idx = max(0, drop_start - window)
            peak_val = np.max(closes_arr[pre_peak_idx:drop_start + 1])
            peak_pos = pre_peak_idx + np.argmax(closes_arr[pre_peak_idx:drop_start + 1])
            trough_val = closes_arr[trough_idx]
            ddl_val = (peak_val - trough_val) * shares_out
            drop_zones.append((drop_start, i, peak_pos, trough_idx, peak_val, trough_val, ddl_val))
            seg_start = i
            in_drop = False
    if not in_drop and seg_start < len(dates):
        ax1.plot(dates[seg_start:], closes[seg_start:],
                 color=style["stock_line"], linewidth=style["line_lw"], zorder=3)
    if in_drop:
        zone = closes_arr[drop_start:]
        trough_idx = drop_start + np.argmin(zone)
        pre_peak_idx = max(0, drop_start - window)
        peak_val = np.max(closes_arr[pre_peak_idx:drop_start + 1])
        peak_pos = pre_peak_idx + np.argmax(closes_arr[pre_peak_idx:drop_start + 1])
        trough_val = closes_arr[trough_idx]
        ddl_val = (peak_val - trough_val) * shares_out
        drop_zones.append((drop_start, len(dates) - 1, peak_pos, trough_idx, peak_val, trough_val, ddl_val))
        ax1.plot(dates[drop_start:], closes[drop_start:],
                 color=style["stock_line_drop"], linewidth=style["max_drop_lw"], zorder=4, alpha=0.85)

    # Label drops
    if drop_zones:
        max_drop = max(drop_zones, key=lambda x: x[6])
        mds, mdi = max_drop[0], max_drop[1]
        ax1.plot(dates[mds:mdi + 1], closes[mds:mdi + 1],
                 color=style["stock_line_drop"], linewidth=style["max_drop_lw"], zorder=4, alpha=0.9)
        merged_drops = []
        for dz in sorted(drop_zones, key=lambda x: x[0]):
            ds, di, pp, ti, pv, tv, dv = dz
            if merged_drops and ds - merged_drops[-1][1] < 10:
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
            zone_start_price = closes[ds]
            drop_pct = (tv - zone_start_price) / zone_start_price * 100
            if dz is max_drop or (max_drop and dv == max_drop[6]):
                pass  # Max DDL labels go on DDL panel
            elif drop_pct <= -15:
                mid_date = dates[ds] + (dates[min(ti, len(dates) - 1)] - dates[ds]) / 2
                ax1.annotate(f"{drop_pct:.0f}%", xy=(mid_date, 0.05), xycoords=("data", "axes fraction"),
                             fontsize=6, color=style["pill_text"], fontweight="700", ha="center", va="center",
                             bbox=dict(boxstyle="round,pad=0.25", fc=style["pill_drop"], ec="none", alpha=0.75),
                             zorder=12)

    # Insider trade circles
    for i, (dt, name, val, itype) in enumerate(zip(ins_dates, ins_names, ins_values, ins_types)):
        idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
        price = closes[idx]
        size = max(15, min(100, val / 2e5))
        color_map = {"sale": style["insider_sale"], "buy": style["insider_buy"], "gift": style["insider_gift"]}
        c = color_map.get(itype, style["insider_gift"])
        s = size if itype != "gift" else size * 0.5
        ax1.scatter(dt, price, marker="o", c=c, s=s, zorder=5, edgecolors="white", linewidths=0.3)

    # Label top 3 largest insider trades
    if ins_values:
        sorted_idx = np.argsort(ins_values)[::-1][:3]
        for idx in sorted_idx:
            if ins_values[idx] > 0:
                dt = ins_dates[idx]
                p_idx = np.argmin(np.abs(np.array([(d - dt).total_seconds() for d in dates])))
                price = closes[p_idx]
                label = f"{ins_names[idx].split()[0]} {fmt_billions(ins_values[idx])}"
                ax1.annotate(label, xy=(dt, price), fontsize=5.5, color=style["text"],
                             xytext=(5, 8), textcoords="offset points",
                             arrowprops=dict(arrowstyle="-", color=style["text_muted"], lw=0.5), zorder=6)

    # Earnings markers
    for dt, surprise in zip(earn_dates, earn_surprises):
        color = style["earnings_beat"] if surprise >= 0 else style["earnings_miss"]
        ax1.axvline(x=dt, color=color, linewidth=0.6, linestyle=":", alpha=0.35, zorder=1)
        arrow = "E^" if surprise >= 0 else "Ev"
        ax1.annotate(arrow, xy=(dt, 0.97), xycoords=("data", "axes fraction"),
                     fontsize=6, color=color, fontweight="700", ha="center", va="top",
                     alpha=0.7, annotation_clip=False, zorder=11)

    # Benchmark overlays: S&P 500 + Sector ETF
    spy_closes = [safe_float(c) for c in md.get("spy_history_2y", {}).get("Close", [])][:len(dates)]
    sect_closes = [safe_float(c) for c in md.get("sector_history_2y", {}).get("Close", [])][:len(dates)]
    sector_etf_name = str(md.get("sector_etf", "Sector"))
    if spy_closes and len(spy_closes) > 10 and spy_closes[0] > 0:
        spy_scaled = [c / spy_closes[0] * closes[0] for c in spy_closes]
        ax1.plot(dates[:len(spy_scaled)], spy_scaled, color=style["benchmark_spy"], linewidth=1.3, alpha=0.6, zorder=1)
        lbl_idx = int(len(spy_scaled) * 0.25)
        ax1.annotate("S&P 500", xy=(dates[lbl_idx], spy_scaled[lbl_idx]),
                     fontsize=5.5, color=style["pill_text"], fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc=style["pill_spy"], ec="none", alpha=0.8),
                     xytext=(0, -10), textcoords="offset points", zorder=11)
    if sect_closes and len(sect_closes) > 10 and sect_closes[0] > 0:
        sect_scaled = [c / sect_closes[0] * closes[0] for c in sect_closes]
        ax1.plot(dates[:len(sect_scaled)], sect_scaled, color=style["benchmark_sector"], linewidth=1.3, alpha=0.6, zorder=1)
        lbl_idx = int(len(sect_scaled) * 0.15)
        ax1.annotate(sector_etf_name, xy=(dates[lbl_idx], sect_scaled[lbl_idx]),
                     fontsize=5.5, color=style["pill_text"], fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc=style["pill_sector"], ec="none", alpha=0.8),
                     xytext=(0, 10), textcoords="offset points", zorder=11)

    # Ticker pill
    lbl_idx_tk = int(len(dates) * 0.85)
    ax1.annotate(ticker, xy=(dates[lbl_idx_tk], closes[lbl_idx_tk]),
                 fontsize=5.5, color=style["pill_text"], fontweight="700", ha="center",
                 bbox=dict(boxstyle="round,pad=0.2", fc=style["pill_ticker"], ec="none", alpha=0.85),
                 xytext=(0, 10), textcoords="offset points", zorder=11)

    # SI badge on price panel (small)
    si_pct = safe_float(info.get("shortPercentOfFloat"), 0)
    if si_pct > 0:
        si_bg = style["panel_bg"] if style["panel_bg"] != "#FFFFFF" else "white"
        ax1.annotate(f"SI: {si_pct * 100:.1f}%", xy=(0.99, 0.03), xycoords="axes fraction",
                     fontsize=6, color=style["text_muted"], fontweight="600", ha="right", va="bottom",
                     bbox=dict(boxstyle="round,pad=0.2", fc=si_bg, ec=style["axis_edge"], linewidth=0.3),
                     zorder=12)

    ax1.set_ylabel("Price ($)", fontsize=8, color=style["ylabel_color"])
    ax1.set_title(f"{ticker} — Stock Price with Drops, DDL Exposure, Insider Trades & Earnings",
                  fontsize=11, fontweight="bold", pad=8, color=style["title_color"])
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax1.tick_params(labelbottom=False)

    # ── Panel 2: DDL Exposure ──
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.set_facecolor(style["ddl_panel_bg"])
    ax2.fill_between(dates, ddl_exposure / 1e9, color=style["ddl_fill"], alpha=0.6, zorder=2)
    ax2.plot(dates, ddl_exposure / 1e9, color=style["ddl_line"], linewidth=0.8, zorder=3)
    ax2.set_ylabel("DDL ($B)", fontsize=8, color=style["ylabel_color"])
    ax2.tick_params(labelbottom=False)

    # Max DDL annotations
    if drop_zones:
        max_drop = max(drop_zones, key=lambda x: x[6])
        _, _, pp, ti, pv, tv, dv = max_drop
        max_ddl_bn = dv / 1e9 if dv > 1e9 else dv / 1e6
        max_ddl_unit = "B" if dv > 1e9 else "M"
        peak_ddl_idx = np.argmax(ddl_exposure)
        ax2.annotate(f"Peak: ${pv:,.0f}", xy=(dates[pp], ddl_exposure[pp] / 1e9),
                     fontsize=6, color=style["pill_text"], fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.2", fc=style["pill_peak"], ec="none", alpha=0.85),
                     xytext=(0, 10), textcoords="offset points", zorder=12)
        ax2.annotate(f"Trough: ${tv:,.0f}  |  Max DDL: ${max_ddl_bn:.1f}{max_ddl_unit}",
                     xy=(dates[peak_ddl_idx], ddl_exposure[peak_ddl_idx] / 1e9),
                     fontsize=6.5, color=style["pill_text"], fontweight="700", ha="center",
                     bbox=dict(boxstyle="round,pad=0.3", fc=style["pill_trough"], ec="none", alpha=0.9),
                     xytext=(0, -12), textcoords="offset points", zorder=12)

    # ── Panel 3: Volume ──
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.set_facecolor(style["panel_bg"])
    ins_date_set = set()
    for dt in ins_dates:
        ins_date_set.add(dt.strftime("%Y-%m-%d"))
    for i in range(len(dates)):
        c = closes[i]
        o = opens[i] if i < len(opens) else c
        color = style["vol_up"] if c >= o else style["vol_down"]
        if dates[i].strftime("%Y-%m-%d") in ins_date_set:
            color = style["vol_insider"]
        ax3.bar(dates[i], volumes[i] / 1e6, color=color, alpha=0.5, width=1.0)

    ax3.set_ylabel("Vol (M)", fontsize=8, color=style["ylabel_color"])
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    # SI pill on volume panel
    si_pct_val = safe_float(info.get("shortPercentOfFloat"), 0) * 100
    si_prior = safe_float(info.get("sharesShortPriorMonth"), 0)
    si_current = safe_float(info.get("sharesShort"), 0)
    if si_pct_val > 0:
        direction = "^" if si_current > si_prior else "v"
        change_pct = ((si_current - si_prior) / si_prior * 100) if si_prior > 0 else 0
        si_label = f"SI: {si_pct_val:.1f}% {direction} ({change_pct:+.0f}% MoM)"
        ax3.annotate(si_label, xy=(0.99, 0.92), xycoords="axes fraction",
                     fontsize=6, color=style["pill_text"], fontweight="700", ha="right", va="top",
                     bbox=dict(boxstyle="round,pad=0.25", fc=style["pill_si"], ec="none", alpha=0.8),
                     zorder=12)

    fig.align_ylabels([ax1, ax2, ax3])
    return fig


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def build_html(charts, company_name, ticker):
    toc_items = []
    cards = []
    for i, (style, b64) in enumerate(charts):
        sid = f"style-{i}"
        toc_items.append(f'<a href="#{sid}" class="toc-link">{i + 1}. {style["name"]}</a>')
        cards.append(f"""
        <div class="card" id="{sid}">
            <div class="card-header">
                <span class="style-num">{i + 1}</span>
                <div>
                    <h2>{style["name"]}</h2>
                    <p class="style-desc">{style["desc"]}</p>
                </div>
            </div>
            <img src="data:image/png;base64,{b64}" alt="{style['name']}" style="border-radius:12px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 4px 12px rgba(0,0,0,0.2);" />
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} — D&O Chart 1 Style Gallery</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #111827;
        color: #E5E7EB;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        padding: 20px;
    }}
    .header {{
        text-align: center;
        padding: 30px 0 20px;
    }}
    .header h1 {{
        font-size: 28px;
        font-weight: 700;
        color: #F9FAFB;
        margin-bottom: 6px;
    }}
    .header p {{
        color: #9CA3AF;
        font-size: 14px;
    }}
    .toc {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        max-width: 1000px;
        margin: 0 auto 30px;
    }}
    .toc-link {{
        display: inline-block;
        padding: 6px 14px;
        background: #1F2937;
        border: 1px solid #374151;
        border-radius: 6px;
        color: #D1D5DB;
        text-decoration: none;
        font-size: 13px;
        transition: all 0.15s;
    }}
    .toc-link:hover {{
        background: #374151;
        color: #F9FAFB;
        border-color: #4B5563;
    }}
    .card {{
        max-width: 1200px;
        margin: 0 auto 40px;
        background: #1F2937;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #374151;
    }}
    .card-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px 24px;
        border-bottom: 1px solid #374151;
    }}
    .style-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: #4F46E5;
        color: white;
        font-weight: 700;
        font-size: 16px;
        border-radius: 8px;
        flex-shrink: 0;
    }}
    .card-header h2 {{
        font-size: 18px;
        font-weight: 600;
        color: #F9FAFB;
    }}
    .style-desc {{
        font-size: 13px;
        color: #9CA3AF;
        margin-top: 2px;
    }}
    .card img {{
        width: 100%;
        display: block;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>{ticker} — D&amp;O Chart 1: Style Gallery</h1>
        <p>{company_name} — 10 visual styles, identical data &amp; overlays</p>
    </div>
    <nav class="toc">
        {"".join(toc_items)}
    </nav>
    {"".join(cards)}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    state_path = STATE_PATH.resolve()
    if not state_path.exists():
        print(f"ERROR: State file not found: {state_path}")
        sys.exit(1)

    print(f"Loading state from {state_path} ...")
    with open(state_path) as f:
        state = json.load(f)

    md = state.get("acquired_data", {}).get("market_data", {})
    info = md.get("info", {})
    company_name = info.get("longName", info.get("shortName", "Company"))
    ticker = state.get("ticker", info.get("symbol", "???"))

    charts = []
    for i, style in enumerate(STYLES):
        print(f"  [{i + 1}/10] {style['name']} ...")
        try:
            fig = chart_1_styled(state, md, ticker, style)
            if fig:
                b64 = fig_to_base64(fig, style["bg"])
                charts.append((style, b64))
            else:
                print(f"    SKIP: no data")
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()

    html = build_html(charts, company_name, ticker)

    out_dir = state_path.parent
    # Derive output dir from state path: output/{ticker}/
    # state_path is like output/AAPL/2026-03-22/state.json -> go up to AAPL level
    ticker_dir = state_path.parent.parent
    out_path = ticker_dir / "chart_styles_mpl.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)

    print(f"\nDone! {len(charts)}/10 styles generated.")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
