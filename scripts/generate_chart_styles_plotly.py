#!/usr/bin/env python3
"""Generate 10 different Plotly stock chart styles for AAPL.

Reads state.json and produces an interactive HTML file with 10 visual styles,
each containing the same overlays: 3-line % return, earnings markers, insider
trades, DDL exposure, 52W labels, volume, and risk badges.
"""

import json
import math
import re
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Load data ──────────────────────────────────────────────────────────────

STATE_PATH = Path("output/AAPL/2026-03-22/state.json")
OUTPUT_PATH = Path("output/AAPL/chart_styles_plotly.html")

with open(STATE_PATH) as f:
    state = json.load(f)

md = state["acquired_data"]["market_data"]
info = md["info"]

# ── Parse histories ────────────────────────────────────────────────────────

def parse_dates(date_strings: list[str]) -> list[str]:
    """Convert date strings to YYYY-MM-DD."""
    out = []
    for d in date_strings:
        # Handle timezone-aware strings
        clean = d.split(" ")[0] if " " in d else d[:10]
        out.append(clean)
    return out


hist = md["history_2y"]
dates = parse_dates(hist["Date"])
closes = hist["Close"]
highs = hist["High"]
lows = hist["Low"]
volumes = hist["Volume"]

sector_hist = md["sector_history_2y"]
sector_dates = parse_dates(sector_hist["Date"])
sector_closes = sector_hist["Close"]
sector_etf = md["sector_etf"]  # XLK

spy_hist = md["spy_history_2y"]
spy_dates = parse_dates(spy_hist["Date"])
spy_closes = spy_hist["Close"]

# ── Compute % returns ─────────────────────────────────────────────────────

def pct_return(prices: list[float]) -> list[float]:
    base = prices[0]
    return [(p / base - 1) * 100 for p in prices]


aapl_ret = pct_return(closes)
sector_ret = pct_return(sector_closes)
spy_ret = pct_return(spy_closes)

# ── Earnings dates ─────────────────────────────────────────────────────────

earnings = md["earnings_dates"]
earn_dates_raw = earnings["Earnings Date"]
earn_eps_est = earnings["EPS Estimate"]
earn_eps_rep = earnings["Reported EPS"]
earn_surprise = earnings["Surprise(%)"]

# Filter to only dates within our history range and with reported EPS
earn_entries = []
date_set = set(dates)
min_date, max_date = dates[0], dates[-1]

for i, ed_raw in enumerate(earn_dates_raw):
    ed = ed_raw.split(" ")[0] if " " in ed_raw else ed_raw[:10]
    if earn_eps_rep[i] is None:
        continue
    if ed < min_date or ed > max_date:
        continue
    # Find closest trading date
    closest = min(dates, key=lambda d: abs(datetime.strptime(d, "%Y-%m-%d").timestamp() - datetime.strptime(ed, "%Y-%m-%d").timestamp()))
    idx = dates.index(closest)
    surprise = earn_surprise[i] if earn_surprise[i] is not None else 0
    is_beat = surprise >= 0
    earn_entries.append({
        "date": closest,
        "idx": idx,
        "ret": aapl_ret[idx],
        "price": closes[idx],
        "surprise": surprise,
        "is_beat": is_beat,
        "eps_est": earn_eps_est[i],
        "eps_rep": earn_eps_rep[i],
    })

# ── Insider transactions ──────────────────────────────────────────────────

insiders_raw = md["insider_transactions"]
insider_entries = []

for i in range(len(insiders_raw["Shares"])):
    text = insiders_raw["Text"][i] or ""
    value = insiders_raw["Value"][i]
    shares = insiders_raw["Shares"][i]
    name = insiders_raw["Insider"][i] or ""
    sd = insiders_raw["Start Date"][i] or ""

    if not sd or sd < min_date or sd > max_date:
        continue

    is_sale = "Sale" in text
    is_buy = "Purchase" in text
    if not is_sale and not is_buy:
        continue

    # Parse price from text
    price_match = re.search(r"price\s+([\d.]+)", text)
    price_per = float(price_match.group(1)) if price_match else 0

    dollar_val = value if value and value > 0 else (shares * price_per if price_per > 0 else 0)

    # Find closest trading date
    closest = min(dates, key=lambda d: abs(
        datetime.strptime(d, "%Y-%m-%d").timestamp() - datetime.strptime(sd, "%Y-%m-%d").timestamp()
    ))
    idx = dates.index(closest)

    insider_entries.append({
        "date": closest,
        "idx": idx,
        "price": closes[idx],
        "ret": aapl_ret[idx],
        "name": name.title(),
        "shares": shares,
        "dollar_val": dollar_val,
        "is_sale": is_sale,
        "text": text,
    })

# ── DDL exposure ───────────────────────────────────────────────────────────

peak_idx = closes.index(max(closes))
peak_price = closes[peak_idx]
# Trough is lowest after peak
trough_slice = closes[peak_idx:]
trough_local_idx = trough_slice.index(min(trough_slice))
trough_idx = peak_idx + trough_local_idx
trough_price = closes[trough_idx]
ddl_pct = (trough_price / peak_price - 1) * 100
ddl_mktcap_loss = info["marketCap"] * abs(ddl_pct) / 100

# ── 52-week high/low ──────────────────────────────────────────────────────

w52_high = info["fiftyTwoWeekHigh"]
w52_low = info["fiftyTwoWeekLow"]

# Find actual dates of 52W high/low in history (last 252 trading days)
recent_closes = closes[-252:] if len(closes) >= 252 else closes
recent_dates = dates[-252:] if len(dates) >= 252 else dates
w52_high_idx_local = recent_closes.index(max(recent_closes))
w52_low_idx_local = recent_closes.index(min(recent_closes))
w52_high_date = recent_dates[w52_high_idx_local]
w52_low_date = recent_dates[w52_low_idx_local]
w52_high_price = recent_closes[w52_high_idx_local]
w52_low_price = recent_closes[w52_low_idx_local]

# ── Volume spikes ──────────────────────────────────────────────────────────

def moving_avg(vals: list[float], window: int = 20) -> list[float]:
    out = []
    for i in range(len(vals)):
        start = max(0, i - window + 1)
        out.append(sum(vals[start:i+1]) / (i - start + 1))
    return out


vol_ma20 = moving_avg(volumes, 20)
vol_spike = [v > 2 * ma for v, ma in zip(volumes, vol_ma20)]

# ── Risk badges ────────────────────────────────────────────────────────────

si_pct = (info.get("shortPercentOfFloat") or 0) * 100
beta = info.get("beta", 0)
max_drop = abs(ddl_pct)
# Insider ownership - approximate from major_holders if available
insider_pct = 0
mh = md.get("major_holders", {})
if mh:
    # major_holders has Value and Breakdown columns
    vals = mh.get("Value", [])
    labels = mh.get("Breakdown", [])
    for v, l in zip(vals, labels):
        if "insider" in (l or "").lower():
            try:
                insider_pct = float(str(v).replace("%", ""))
            except (ValueError, TypeError):
                pass

current_price = info["currentPrice"]

# ── Style definitions ─────────────────────────────────────────────────────

STYLES = [
    {
        "name": "Bloomberg Terminal",
        "desc": "Dense, monospace, dark background with green phosphor lines. The classic institutional terminal look.",
        "template": "plotly_dark",
        "bg": "#0A0A0A",
        "paper_bg": "#0A0A0A",
        "grid_color": "#1A1A2E",
        "primary_color": "#00FF41",
        "sector_color": "#FF6600",
        "spy_color": "#FFFF00",
        "up_fill": "rgba(0,255,65,0.15)",
        "down_fill": "rgba(255,50,50,0.15)",
        "vol_color": "#333333",
        "vol_spike_color": "#FF6600",
        "text_color": "#00FF41",
        "font_family": "'Courier New', monospace",
        "earn_beat": "#00FF41",
        "earn_miss": "#FF3333",
        "insider_buy": "#00FF41",
        "insider_sell": "#FF3333",
        "ddl_color": "#FF3333",
        "badge_bg": "rgba(0,0,0,0.8)",
        "badge_border": "#00FF41",
        "annotation_bg": "rgba(10,10,10,0.9)",
        "card_bg": "#0A0A0A",
        "card_text": "#00FF41",
    },
    {
        "name": "Google Finance",
        "desc": "Clean, minimal, lots of whitespace. Green when up, red when down. The approachable retail look.",
        "template": "plotly_white",
        "bg": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "grid_color": "#F0F0F0",
        "primary_color": "#16A34A",
        "sector_color": "#6366F1",
        "spy_color": "#F59E0B",
        "up_fill": "rgba(22,163,74,0.08)",
        "down_fill": "rgba(220,38,38,0.08)",
        "vol_color": "#E5E7EB",
        "vol_spike_color": "#F59E0B",
        "text_color": "#111827",
        "font_family": "'Google Sans', 'Roboto', sans-serif",
        "earn_beat": "#16A34A",
        "earn_miss": "#DC2626",
        "insider_buy": "#16A34A",
        "insider_sell": "#DC2626",
        "ddl_color": "#DC2626",
        "badge_bg": "rgba(255,255,255,0.95)",
        "badge_border": "#E5E7EB",
        "annotation_bg": "rgba(255,255,255,0.95)",
        "card_bg": "#FFFFFF",
        "card_text": "#111827",
    },
    {
        "name": "TradingView",
        "desc": "Bold colors, gradient fills, warm tones. The active trader's favorite charting platform.",
        "template": "plotly_white",
        "bg": "#131722",
        "paper_bg": "#131722",
        "grid_color": "#1E222D",
        "primary_color": "#2962FF",
        "sector_color": "#FF9800",
        "spy_color": "#AB47BC",
        "up_fill": "rgba(38,166,154,0.15)",
        "down_fill": "rgba(239,83,80,0.15)",
        "vol_color": "rgba(38,166,154,0.2)",
        "vol_spike_color": "#FF9800",
        "text_color": "#D1D4DC",
        "font_family": "'Trebuchet MS', sans-serif",
        "earn_beat": "#26A69A",
        "earn_miss": "#EF5350",
        "insider_buy": "#26A69A",
        "insider_sell": "#EF5350",
        "ddl_color": "#EF5350",
        "badge_bg": "rgba(19,23,34,0.9)",
        "badge_border": "#2962FF",
        "annotation_bg": "rgba(19,23,34,0.9)",
        "card_bg": "#131722",
        "card_text": "#D1D4DC",
    },
    {
        "name": "S&P Capital IQ",
        "desc": "Conservative navy accents, professional serif typography. The institutional research standard.",
        "template": "plotly_white",
        "bg": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "grid_color": "#E8ECF0",
        "primary_color": "#1F3A5C",
        "sector_color": "#7B8FA1",
        "spy_color": "#B8860B",
        "up_fill": "rgba(31,58,92,0.08)",
        "down_fill": "rgba(178,34,34,0.08)",
        "vol_color": "#D0D7DE",
        "vol_spike_color": "#B8860B",
        "text_color": "#1F3A5C",
        "font_family": "'Georgia', 'Times New Roman', serif",
        "earn_beat": "#2E7D32",
        "earn_miss": "#B22222",
        "insider_buy": "#2E7D32",
        "insider_sell": "#B22222",
        "ddl_color": "#B22222",
        "badge_bg": "rgba(255,255,255,0.95)",
        "badge_border": "#1F3A5C",
        "annotation_bg": "rgba(248,250,252,0.95)",
        "card_bg": "#FFFFFF",
        "card_text": "#1F3A5C",
    },
    {
        "name": "Koyfin",
        "desc": "Dark slate background with vibrant purple and cyan accents. Modern fintech aesthetic.",
        "template": "plotly_dark",
        "bg": "#0F172A",
        "paper_bg": "#0F172A",
        "grid_color": "#1E293B",
        "primary_color": "#8B5CF6",
        "sector_color": "#06B6D4",
        "spy_color": "#F59E0B",
        "up_fill": "rgba(139,92,246,0.12)",
        "down_fill": "rgba(239,68,68,0.12)",
        "vol_color": "#1E293B",
        "vol_spike_color": "#06B6D4",
        "text_color": "#E2E8F0",
        "font_family": "'Inter', 'SF Pro', sans-serif",
        "earn_beat": "#22C55E",
        "earn_miss": "#EF4444",
        "insider_buy": "#22C55E",
        "insider_sell": "#EF4444",
        "ddl_color": "#EF4444",
        "badge_bg": "rgba(15,23,42,0.9)",
        "badge_border": "#8B5CF6",
        "annotation_bg": "rgba(15,23,42,0.9)",
        "card_bg": "#0F172A",
        "card_text": "#E2E8F0",
    },
    {
        "name": "FT / WSJ",
        "desc": "Salmon background, black primary line, restrained palette. The financial journalism standard.",
        "template": "plotly_white",
        "bg": "#FFF1E6",
        "paper_bg": "#FFF1E6",
        "grid_color": "#F0DDD0",
        "primary_color": "#000000",
        "sector_color": "#6B7280",
        "spy_color": "#9F1239",
        "up_fill": "rgba(0,0,0,0.05)",
        "down_fill": "rgba(159,18,57,0.08)",
        "vol_color": "#E8D5C4",
        "vol_spike_color": "#9F1239",
        "text_color": "#1A1A1A",
        "font_family": "'Georgia', serif",
        "earn_beat": "#15803D",
        "earn_miss": "#9F1239",
        "insider_buy": "#15803D",
        "insider_sell": "#9F1239",
        "ddl_color": "#9F1239",
        "badge_bg": "rgba(255,241,230,0.95)",
        "badge_border": "#1A1A1A",
        "annotation_bg": "rgba(255,241,230,0.95)",
        "card_bg": "#FFF1E6",
        "card_text": "#1A1A1A",
    },
    {
        "name": "Morningstar",
        "desc": "Clean white with signature blue accent. Structured, data-dense, investor-education focused.",
        "template": "plotly_white",
        "bg": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "grid_color": "#E5E7EB",
        "primary_color": "#00A3E0",
        "sector_color": "#6B7280",
        "spy_color": "#D97706",
        "up_fill": "rgba(0,163,224,0.08)",
        "down_fill": "rgba(220,38,38,0.08)",
        "vol_color": "#E5E7EB",
        "vol_spike_color": "#D97706",
        "text_color": "#1F2937",
        "font_family": "'Helvetica Neue', 'Arial', sans-serif",
        "earn_beat": "#059669",
        "earn_miss": "#DC2626",
        "insider_buy": "#059669",
        "insider_sell": "#DC2626",
        "ddl_color": "#DC2626",
        "badge_bg": "rgba(255,255,255,0.95)",
        "badge_border": "#00A3E0",
        "annotation_bg": "rgba(255,255,255,0.95)",
        "card_bg": "#FFFFFF",
        "card_text": "#1F2937",
    },
    {
        "name": "FactSet",
        "desc": "Gray professional palette, institutional density. The portfolio manager's daily driver.",
        "template": "plotly_white",
        "bg": "#F8F9FA",
        "paper_bg": "#F8F9FA",
        "grid_color": "#DEE2E6",
        "primary_color": "#495057",
        "sector_color": "#0D6EFD",
        "spy_color": "#FD7E14",
        "up_fill": "rgba(25,135,84,0.08)",
        "down_fill": "rgba(220,53,69,0.08)",
        "vol_color": "#CED4DA",
        "vol_spike_color": "#FD7E14",
        "text_color": "#212529",
        "font_family": "'Segoe UI', 'Tahoma', sans-serif",
        "earn_beat": "#198754",
        "earn_miss": "#DC3545",
        "insider_buy": "#198754",
        "insider_sell": "#DC3545",
        "ddl_color": "#DC3545",
        "badge_bg": "rgba(248,249,250,0.95)",
        "badge_border": "#6C757D",
        "annotation_bg": "rgba(248,249,250,0.95)",
        "card_bg": "#F8F9FA",
        "card_text": "#212529",
    },
    {
        "name": "Refinitiv / Eikon",
        "desc": "Dark navy with modern gradient accents. The enterprise terminal successor to Reuters.",
        "template": "plotly_dark",
        "bg": "#002244",
        "paper_bg": "#002244",
        "grid_color": "#003366",
        "primary_color": "#4FC3F7",
        "sector_color": "#FFB74D",
        "spy_color": "#CE93D8",
        "up_fill": "rgba(79,195,247,0.12)",
        "down_fill": "rgba(239,83,80,0.12)",
        "vol_color": "#003366",
        "vol_spike_color": "#FFB74D",
        "text_color": "#B0C4DE",
        "font_family": "'Segoe UI', sans-serif",
        "earn_beat": "#66BB6A",
        "earn_miss": "#EF5350",
        "insider_buy": "#66BB6A",
        "insider_sell": "#EF5350",
        "ddl_color": "#EF5350",
        "badge_bg": "rgba(0,34,68,0.9)",
        "badge_border": "#4FC3F7",
        "annotation_bg": "rgba(0,34,68,0.9)",
        "card_bg": "#002244",
        "card_text": "#B0C4DE",
    },
    {
        "name": "D&O Underwriting",
        "desc": "White background, navy headers, gold highlights, DDL prominence. Purpose-built for underwriting meetings.",
        "template": "plotly_white",
        "bg": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "grid_color": "#E8ECF0",
        "primary_color": "#1F3A5C",
        "sector_color": "#6B8FA3",
        "spy_color": "#D4A843",
        "up_fill": "rgba(31,58,92,0.06)",
        "down_fill": "rgba(180,30,30,0.10)",
        "vol_color": "#D0D7DE",
        "vol_spike_color": "#D4A843",
        "text_color": "#1F3A5C",
        "font_family": "'Calibri', 'Helvetica Neue', sans-serif",
        "earn_beat": "#2E7D32",
        "earn_miss": "#B71C1C",
        "insider_buy": "#2E7D32",
        "insider_sell": "#B71C1C",
        "ddl_color": "#B71C1C",
        "badge_bg": "rgba(255,255,255,0.95)",
        "badge_border": "#D4A843",
        "annotation_bg": "rgba(255,255,255,0.95)",
        "card_bg": "#FFFFFF",
        "card_text": "#1F3A5C",
    },
]


def fmt_dollars(val: float) -> str:
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    if val >= 1e6:
        return f"${val/1e6:.1f}M"
    if val >= 1e3:
        return f"${val/1e3:.0f}K"
    return f"${val:.0f}"


def build_chart(style: dict, chart_idx: int) -> str:
    """Build a single Plotly chart with all overlays in the given style."""
    s = style

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    # ── 1. Three % return lines ────────────────────────────────────────

    # AAPL positive fill (green above 0)
    aapl_pos = [max(0, r) for r in aapl_ret]
    aapl_neg = [min(0, r) for r in aapl_ret]

    fig.add_trace(go.Scatter(
        x=dates, y=aapl_pos, fill='tozeroy',
        fillcolor=s["up_fill"], line=dict(width=0),
        showlegend=False, hoverinfo='skip',
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=aapl_neg, fill='tozeroy',
        fillcolor=s["down_fill"], line=dict(width=0),
        showlegend=False, hoverinfo='skip',
    ), row=1, col=1)

    # AAPL main line (thick)
    fig.add_trace(go.Scatter(
        x=dates, y=aapl_ret,
        name="AAPL",
        line=dict(color=s["primary_color"], width=2.5),
        hovertemplate="AAPL: %{y:.1f}%<extra></extra>",
    ), row=1, col=1)

    # Sector ETF
    fig.add_trace(go.Scatter(
        x=sector_dates, y=sector_ret,
        name=sector_etf,
        line=dict(color=s["sector_color"], width=1.2, dash="dash"),
        hovertemplate=f"{sector_etf}: %{{y:.1f}}%<extra></extra>",
    ), row=1, col=1)

    # S&P 500
    fig.add_trace(go.Scatter(
        x=spy_dates, y=spy_ret,
        name="SPY",
        line=dict(color=s["spy_color"], width=1.2, dash="dot"),
        hovertemplate="SPY: %{y:.1f}%<extra></extra>",
    ), row=1, col=1)

    # ── 3. Earnings markers ────────────────────────────────────────────

    earn_beat_dates = [e["date"] for e in earn_entries if e["is_beat"]]
    earn_beat_rets = [e["ret"] for e in earn_entries if e["is_beat"]]
    earn_miss_dates = [e["date"] for e in earn_entries if not e["is_beat"]]
    earn_miss_rets = [e["ret"] for e in earn_entries if not e["is_beat"]]

    earn_beat_texts = [f"Beat +{e['surprise']:.1f}%<br>EPS: {e['eps_rep']}" for e in earn_entries if e["is_beat"]]
    earn_miss_texts = [f"Miss {e['surprise']:.1f}%<br>EPS: {e['eps_rep']}" for e in earn_entries if not e["is_beat"]]

    if earn_beat_dates:
        fig.add_trace(go.Scatter(
            x=earn_beat_dates, y=earn_beat_rets,
            mode="markers+text",
            marker=dict(symbol="diamond", size=14, color=s["earn_beat"],
                        line=dict(width=2, color=s["earn_beat"])),
            text=["E"] * len(earn_beat_dates),
            textposition="middle center",
            textfont=dict(size=8, color="white", family=s["font_family"]),
            hovertext=earn_beat_texts,
            hoverinfo="text",
            name="Earnings Beat",
            showlegend=False,
        ), row=1, col=1)

    if earn_miss_dates:
        fig.add_trace(go.Scatter(
            x=earn_miss_dates, y=earn_miss_rets,
            mode="markers+text",
            marker=dict(symbol="diamond", size=14, color=s["earn_miss"],
                        line=dict(width=2, color=s["earn_miss"])),
            text=["E"] * len(earn_miss_dates),
            textposition="middle center",
            textfont=dict(size=8, color="white", family=s["font_family"]),
            hovertext=earn_miss_texts,
            hoverinfo="text",
            name="Earnings Miss",
            showlegend=False,
        ), row=1, col=1)

    # Earnings vertical dashed lines
    for e in earn_entries:
        fig.add_shape(
            type="line",
            x0=e["date"], x1=e["date"],
            y0=0, y1=e["ret"],
            line=dict(
                color=s["earn_beat"] if e["is_beat"] else s["earn_miss"],
                width=1, dash="dash",
            ),
            row=1, col=1,
        )

    # Earnings annotations
    for e in earn_entries:
        label = f"Beat +{e['surprise']:.1f}%" if e["is_beat"] else f"Miss {e['surprise']:.1f}%"
        fig.add_annotation(
            x=e["date"], y=e["ret"],
            text=label,
            showarrow=True,
            arrowhead=0, arrowcolor="rgba(0,0,0,0)",
            ax=40, ay=-25,
            font=dict(size=9, color=s["earn_beat"] if e["is_beat"] else s["earn_miss"],
                      family=s["font_family"]),
            bgcolor=s["annotation_bg"],
            borderpad=2,
            row=1, col=1,
        )

    # ── 4. Insider trades on PRICE line ────────────────────────────────

    if insider_entries:
        max_dollar = max(e["dollar_val"] for e in insider_entries if e["dollar_val"] > 0) or 1
        for ie in insider_entries:
            sz = max(6, min(30, 6 + 24 * (ie["dollar_val"] / max_dollar)))
            fig.add_trace(go.Scatter(
                x=[ie["date"]], y=[ie["ret"]],
                mode="markers",
                marker=dict(
                    size=sz,
                    color=s["insider_sell"] if ie["is_sale"] else s["insider_buy"],
                    opacity=0.7,
                    line=dict(width=1, color="white" if s["bg"] != "#FFFFFF" else "#333"),
                ),
                hovertext=f"{ie['name']}<br>{'Sale' if ie['is_sale'] else 'Buy'}: {ie['shares']:,} shares<br>{fmt_dollars(ie['dollar_val'])}",
                hoverinfo="text",
                showlegend=False,
            ), row=1, col=1)

    # ── 10. Volume bars ────────────────────────────────────────────────

    # Color volume bars
    vol_colors = []
    insider_sale_dates = {ie["date"] for ie in insider_entries if ie["is_sale"]}
    insider_buy_dates = {ie["date"] for ie in insider_entries if not ie["is_sale"]}

    for i, d in enumerate(dates):
        if d in insider_sale_dates:
            vol_colors.append("#FF6B35")  # orange for insider sale
        elif d in insider_buy_dates:
            vol_colors.append("#4169E1")  # blue for insider buy
        elif vol_spike[i]:
            vol_colors.append(s["vol_spike_color"])
        else:
            vol_colors.append(s["vol_color"])

    fig.add_trace(go.Bar(
        x=dates, y=volumes,
        marker_color=vol_colors,
        showlegend=False,
        hovertemplate="Vol: %{y:,.0f}<extra></extra>",
    ), row=2, col=1)

    # ── 6. DDL exposure line ───────────────────────────────────────────

    peak_ret = aapl_ret[peak_idx]
    trough_ret = aapl_ret[trough_idx]

    fig.add_shape(
        type="line",
        x0=dates[peak_idx], x1=dates[trough_idx],
        y0=peak_ret, y1=trough_ret,
        line=dict(color=s["ddl_color"], width=2.5, dash="dash"),
        row=1, col=1,
    )

    # DDL label
    ddl_label = f"DDL {ddl_pct:.1f}% | ${peak_price:.0f}\u2192${trough_price:.0f} ({fmt_dollars(ddl_mktcap_loss)})"
    mid_date_idx = (peak_idx + trough_idx) // 2
    mid_ret = (peak_ret + trough_ret) / 2
    fig.add_annotation(
        x=dates[mid_date_idx], y=mid_ret,
        text=ddl_label,
        showarrow=True, arrowhead=0,
        ax=0, ay=-30,
        font=dict(size=10, color=s["ddl_color"], family=s["font_family"]),
        bgcolor=s["annotation_bg"],
        bordercolor=s["ddl_color"],
        borderwidth=1, borderpad=4,
        row=1, col=1,
    )

    # Peak/trough markers
    fig.add_trace(go.Scatter(
        x=[dates[peak_idx]], y=[peak_ret],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color=s["ddl_color"]),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[dates[trough_idx]], y=[trough_ret],
        mode="markers",
        marker=dict(symbol="triangle-up", size=10, color=s["earn_beat"]),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    # ── 7. 52W high/low labels ─────────────────────────────────────────

    # Map 52W dates to return values
    if w52_high_date in dates:
        hi_idx = dates.index(w52_high_date)
        fig.add_annotation(
            x=w52_high_date, y=aapl_ret[hi_idx],
            text=f"52W High ${w52_high_price:.2f}",
            showarrow=True, arrowhead=2,
            ax=0, ay=-25,
            font=dict(size=9, color=s["earn_beat"], family=s["font_family"]),
            bgcolor=s["annotation_bg"],
            borderpad=3,
            row=1, col=1,
        )
    if w52_low_date in dates:
        lo_idx = dates.index(w52_low_date)
        fig.add_annotation(
            x=w52_low_date, y=aapl_ret[lo_idx],
            text=f"52W Low ${w52_low_price:.2f}",
            showarrow=True, arrowhead=2,
            ax=0, ay=25,
            font=dict(size=9, color=s["ddl_color"], family=s["font_family"]),
            bgcolor=s["annotation_bg"],
            borderpad=3,
            row=1, col=1,
        )

    # ── 8. Current price annotation ────────────────────────────────────

    fig.add_annotation(
        x=dates[-1], y=aapl_ret[-1],
        text=f"${current_price:.2f}",
        showarrow=True, arrowhead=2,
        ax=50, ay=0,
        font=dict(size=11, color=s["primary_color"], family=s["font_family"]),
        bgcolor=s["annotation_bg"],
        bordercolor=s["primary_color"],
        borderwidth=1, borderpad=4,
        row=1, col=1,
    )

    # ── 9. Return labels on right margin ───────────────────────────────

    final_aapl = aapl_ret[-1]
    final_sector = sector_ret[-1] if sector_ret else 0
    final_spy = spy_ret[-1] if spy_ret else 0

    for label, ret, color in [
        ("AAPL", final_aapl, s["primary_color"]),
        (sector_etf, final_sector, s["sector_color"]),
        ("SPY", final_spy, s["spy_color"]),
    ]:
        fig.add_annotation(
            x=dates[-1], y=ret,
            text=f"  {label} {ret:+.1f}%",
            showarrow=False,
            xanchor="left",
            font=dict(size=10, color=color, family=s["font_family"]),
            row=1, col=1,
        )

    # ── 11. Risk badges (top-right) ────────────────────────────────────

    badge_text = (
        f"SI: {si_pct:.1f}%  |  \u03b2: {beta:.2f}  |  "
        f"Max Drop: {max_drop:.1f}%  |  Insider: {insider_pct:.1f}%"
    )
    fig.add_annotation(
        x=1.0, y=1.02,
        xref="paper", yref="paper",
        text=badge_text,
        showarrow=False,
        font=dict(size=10, color=s["text_color"], family=s["font_family"]),
        bgcolor=s["badge_bg"],
        bordercolor=s["badge_border"],
        borderwidth=1, borderpad=6,
        xanchor="right", yanchor="bottom",
    )

    # ── Layout ─────────────────────────────────────────────────────────

    fig.update_layout(
        template=s["template"],
        title=dict(
            text=f"AAPL \u2014 2-Year Performance vs {sector_etf} & SPY",
            font=dict(size=16, color=s["text_color"], family=s["font_family"]),
            x=0.01, xanchor="left",
        ),
        plot_bgcolor=s["bg"],
        paper_bgcolor=s["paper_bg"],
        font=dict(family=s["font_family"], color=s["text_color"]),
        width=1200,
        height=520,
        margin=dict(l=60, r=100, t=60, b=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            font=dict(size=10, family=s["font_family"]),
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(
        gridcolor=s["grid_color"],
        showgrid=True,
        zeroline=False,
        row=1, col=1,
    )
    fig.update_yaxes(
        title_text="% Return",
        gridcolor=s["grid_color"],
        showgrid=True,
        zeroline=True,
        zerolinecolor=s["text_color"],
        zerolinewidth=0.5,
        row=1, col=1,
    )
    fig.update_xaxes(gridcolor=s["grid_color"], row=2, col=1)
    fig.update_yaxes(
        title_text="Volume",
        gridcolor=s["grid_color"],
        showgrid=False,
        row=2, col=1,
    )

    return fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        config={"displayModeBar": True, "scrollZoom": True, "responsive": True},
        div_id=f"chart-{chart_idx}",
    )


# ── Build HTML page ────────────────────────────────────────────────────────

def build_page() -> str:
    charts_html = []
    toc_items = []

    for i, style in enumerate(STYLES):
        anchor = f"style-{i}"
        toc_items.append(f'<a href="#{anchor}" class="toc-link">{i+1}. {style["name"]}</a>')
        chart_div = build_chart(style, i)

        is_dark = style["bg"] in ("#0A0A0A", "#131722", "#0F172A", "#002244")
        card_class = "card dark" if is_dark else "card light"

        charts_html.append(f"""
        <div id="{anchor}" class="{card_class}" style="background:{style['card_bg']}; color:{style['card_text']};">
            <div class="card-header">
                <span class="style-num">{i+1}</span>
                <h2>{style['name']}</h2>
            </div>
            <p class="desc">{style['desc']}</p>
            <div class="chart-container">
                {chart_div}
            </div>
        </div>
        """)

    toc_html = "\n".join(toc_items)
    charts_block = "\n".join(charts_html)

    comparison_rows = []
    categories = [
        ("Best for dark-room presentations", "Bloomberg Terminal, TradingView, Koyfin"),
        ("Best for printed reports", "S&P Capital IQ, FT/WSJ, FactSet"),
        ("Best for underwriting meetings", "D&O Underwriting, S&P Capital IQ"),
        ("Best for web embedding", "Google Finance, Morningstar"),
        ("Most data-dense", "Bloomberg Terminal, FactSet, Refinitiv"),
        ("Most modern aesthetic", "Koyfin, TradingView"),
        ("Best DDL visibility", "D&O Underwriting (purpose-built)"),
    ]
    for cat, picks in categories:
        comparison_rows.append(f"<tr><td>{cat}</td><td>{picks}</td></tr>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AAPL Stock Chart Styles - Plotly Interactive</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #111827;
    color: #E5E7EB;
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    padding: 0;
  }}
  .page-header {{
    background: linear-gradient(135deg, #1F3A5C 0%, #0F172A 100%);
    padding: 48px 40px 36px;
    border-bottom: 3px solid #D4A843;
  }}
  .page-header h1 {{
    font-size: 32px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 8px;
  }}
  .page-header .subtitle {{
    font-size: 16px;
    color: #94A3B8;
  }}
  .page-header .meta {{
    margin-top: 12px;
    font-size: 13px;
    color: #64748B;
  }}
  .toc {{
    background: #1E293B;
    padding: 20px 40px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    border-bottom: 1px solid #334155;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .toc-link {{
    color: #94A3B8;
    text-decoration: none;
    font-size: 13px;
    padding: 6px 14px;
    border-radius: 6px;
    background: #0F172A;
    border: 1px solid #334155;
    transition: all 0.2s;
  }}
  .toc-link:hover {{
    color: #FFFFFF;
    border-color: #D4A843;
    background: #1F3A5C;
  }}
  .content {{
    max-width: 1320px;
    margin: 0 auto;
    padding: 30px 20px;
  }}
  .card {{
    border-radius: 12px;
    margin-bottom: 40px;
    padding: 28px;
    border: 1px solid #334155;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  .card.light {{
    border-color: #E5E7EB;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
  }}
  .style-num {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #D4A843;
    color: #0F172A;
    font-weight: 700;
    font-size: 16px;
    flex-shrink: 0;
  }}
  .card-header h2 {{
    font-size: 22px;
    font-weight: 600;
  }}
  .desc {{
    font-size: 14px;
    opacity: 0.7;
    margin-bottom: 16px;
    line-height: 1.5;
  }}
  .chart-container {{
    border-radius: 8px;
    overflow: hidden;
  }}
  .comparison {{
    background: #1E293B;
    border-radius: 12px;
    padding: 28px;
    margin-top: 20px;
    border: 1px solid #334155;
  }}
  .comparison h2 {{
    font-size: 20px;
    margin-bottom: 16px;
    color: #D4A843;
  }}
  .comparison table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .comparison th, .comparison td {{
    padding: 10px 16px;
    text-align: left;
    border-bottom: 1px solid #334155;
    font-size: 14px;
  }}
  .comparison th {{
    color: #94A3B8;
    font-weight: 600;
  }}
  .comparison td:first-child {{
    color: #E5E7EB;
    font-weight: 500;
  }}
  .comparison td:last-child {{
    color: #D4A843;
  }}
</style>
</head>
<body>

<div class="page-header">
  <h1>AAPL Stock Chart Styles</h1>
  <div class="subtitle">10 interactive Plotly chart styles with full D&O underwriting overlays</div>
  <div class="meta">
    Current: ${current_price:.2f} | MCap: {fmt_dollars(info['marketCap'])} |
    52W: ${w52_low:.2f} - ${w52_high:.2f} |
    Beta: {beta:.2f} | SI: {si_pct:.1f}% |
    DDL: {ddl_pct:.1f}% (${peak_price:.0f} to ${trough_price:.0f})
  </div>
</div>

<nav class="toc">
  {toc_html}
  <a href="#comparison" class="toc-link" style="border-color:#D4A843; color:#D4A843;">Comparison</a>
</nav>

<div class="content">
  {charts_block}

  <div id="comparison" class="comparison">
    <h2>Style Comparison Guide</h2>
    <table>
      <thead><tr><th>Use Case</th><th>Recommended Styles</th></tr></thead>
      <tbody>
        {"".join(comparison_rows)}
      </tbody>
    </table>
  </div>
</div>

</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    html = build_page()
    OUTPUT_PATH.write_text(html)
    print(f"Written to {OUTPUT_PATH} ({len(html):,} bytes)")
    print(f"Charts: {len(STYLES)}")
    print(f"Data: {len(dates)} trading days, {len(earn_entries)} earnings, {len(insider_entries)} insider trades")
