"""Split-tone chart variations — dark below / white above (and vice versa)."""
from __future__ import annotations
import sys, numpy as np
sys.path.insert(0, "src")
from dotenv import load_dotenv
load_dotenv()

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.stock_chart_data import (
    ChartData, extract_chart_data, index_to_base,
)
from do_uw.stages.render.charts.unified_drop_chart import (
    _sort_drops, _deduplicate_drops, _cluster_drops, _parse_date, _find_y,
)
from do_uw.stages.render.chart_helpers import save_chart_to_svg

_PAL = [
    "#F43F5E", "#8B5CF6", "#3B82F6", "#10B981", "#F59E0B",
    "#EC4899", "#6366F1", "#14B8A6", "#EF4444", "#A855F7",
    "#0EA5E9", "#22C55E",
]

STYLES = [
    # --- DARK BELOW, WHITE ABOVE ---
    {"name": "EV Split: Dark Below, White Above",
     "desc": "Electric Violet below the line, clean white above — price line is the horizon",
     "bg_above": "#FFFFFF", "bg_below": "#110B1E",
     "line": "#A855F7", "line_w": 2.5, "glow": True,
     "etf_above": "#C4B5FD", "etf_below": "#6B5B8D",
     "text_above": "#475569", "text_below": "#C4B5FD",
     "grid_above": "#F1F5F9", "grid_below": "#1E1535",
     "drop_label": "#DC2626", "marker_edge": "white"},

    {"name": "EV Split: Dark Below, Cream Above",
     "desc": "Electric Violet below, warm cream above — editorial + drama",
     "bg_above": "#FFF8F0", "bg_below": "#110B1E",
     "line": "#A855F7", "line_w": 2.5, "glow": True,
     "etf_above": "#A08060", "etf_below": "#6B5B8D",
     "text_above": "#5C3D1A", "text_below": "#C4B5FD",
     "grid_above": "#F5E6D3", "grid_below": "#1E1535",
     "drop_label": "#DC2626", "marker_edge": "white"},

    {"name": "EV Split: Dark Below, Ice Blue Above",
     "desc": "Electric Violet below, icy blue above — cold/hot contrast",
     "bg_above": "#EFF6FF", "bg_below": "#110B1E",
     "line": "#8B5CF6", "line_w": 2.5, "glow": True,
     "etf_above": "#93C5FD", "etf_below": "#6B5B8D",
     "text_above": "#1E3A8A", "text_below": "#C4B5FD",
     "grid_above": "#DBEAFE", "grid_below": "#1E1535",
     "drop_label": "#DC2626", "marker_edge": "white"},

    # --- WHITE BELOW, DARK ABOVE ---
    {"name": "EV Inverted: White Below, Dark Above",
     "desc": "White foundation below the line, Electric Violet sky above",
     "bg_above": "#110B1E", "bg_below": "#FFFFFF",
     "line": "#A855F7", "line_w": 2.5, "glow": True,
     "etf_above": "#6B5B8D", "etf_below": "#C4B5FD",
     "text_above": "#C4B5FD", "text_below": "#475569",
     "grid_above": "#1E1535", "grid_below": "#F1F5F9",
     "drop_label": "#F43F5E", "marker_edge": "white"},

    {"name": "EV Inverted: Lavender Below, Deep Purple Above",
     "desc": "Soft lavender below, deep void above — ethereal",
     "bg_above": "#0D0221", "bg_below": "#F5F3FF",
     "line": "#7C3AED", "line_w": 2.5, "glow": True,
     "etf_above": "#6C63FF", "etf_below": "#C4B5FD",
     "text_above": "#C4B5FD", "text_below": "#5B21B6",
     "grid_above": "#1A0A3A", "grid_below": "#EDE9FE",
     "drop_label": "#F43F5E", "marker_edge": "white"},

    # --- ORANGE LINE VARIANTS ---
    {"name": "Split Amber: Dark Below, White Above",
     "desc": "Dark earth below the orange line, clean white sky above",
     "bg_above": "#FFFFFF", "bg_below": "#1A1410",
     "line": "#E8903A", "line_w": 2.5, "glow": True,
     "etf_above": "#94A3B8", "etf_below": "#78716C",
     "text_above": "#475569", "text_below": "#D6D3D1",
     "grid_above": "#F1F5F9", "grid_below": "#2A2218",
     "drop_label": "#DC2626", "marker_edge": "white"},

    {"name": "Split Amber: Deep Purple Below, White Above",
     "desc": "Purple depths below the orange line, white clarity above",
     "bg_above": "#FFFFFF", "bg_below": "#16132B",
     "line": "#E8903A", "line_w": 2.8, "glow": True,
     "etf_above": "#94A3B8", "etf_below": "#64748B",
     "text_above": "#475569", "text_below": "#C4B5FD",
     "grid_above": "#F1F5F9", "grid_below": "#251F45",
     "drop_label": "#DC2626", "marker_edge": "white"},

    # --- HIGH CONTRAST DROP MARKERS ---
    {"name": "EV Split + Hot Drops",
     "desc": "Electric Violet split + oversized neon drop markers with thick white outlines",
     "bg_above": "#FFFFFF", "bg_below": "#110B1E",
     "line": "#A855F7", "line_w": 2.5, "glow": True,
     "etf_above": "#C4B5FD", "etf_below": "#6B5B8D",
     "text_above": "#475569", "text_below": "#C4B5FD",
     "grid_above": "#F1F5F9", "grid_below": "#1E1535",
     "drop_label": "#FF0050", "marker_edge": "white",
     "marker_scale": 1.5, "marker_edge_w": 1.5},

    {"name": "EV Split + Neon Drops",
     "desc": "Split tone + neon green/pink drop labels that POP against both zones",
     "bg_above": "#FFFFFF", "bg_below": "#110B1E",
     "line": "#A855F7", "line_w": 2.5, "glow": True,
     "etf_above": "#C4B5FD", "etf_below": "#6B5B8D",
     "text_above": "#475569", "text_below": "#C4B5FD",
     "grid_above": "#F1F5F9", "grid_below": "#1E1535",
     "drop_label": "#FF2D55", "marker_edge": "#00FFC6",
     "marker_scale": 1.3, "marker_edge_w": 1.2},

    {"name": "EV Split + Shadow Drops",
     "desc": "Split tone + dark drop markers with colored shadow halos",
     "bg_above": "#FAFAFA", "bg_below": "#110B1E",
     "line": "#8B5CF6", "line_w": 2.5, "glow": True,
     "etf_above": "#D4D4D8", "etf_below": "#6B5B8D",
     "text_above": "#3F3F46", "text_below": "#C4B5FD",
     "grid_above": "#E4E4E7", "grid_below": "#1E1535",
     "drop_label": "#DC2626", "marker_edge": "white",
     "marker_scale": 1.2, "drop_glow": True},
]


def render_split_chart(data, drops, clusters, s):
    plt.style.use("default")
    fig = plt.figure(figsize=(14, 3.5), dpi=150, facecolor=s["bg_above"])
    ax = fig.add_axes([0.05, 0.12, 0.89, 0.84])

    # The magic: fill BELOW the line with dark color, axes bg is light
    ax.set_facecolor(s["bg_above"])

    prices = np.array(data.prices)
    dates = data.dates

    # Set limits first, then fill below price line with dark color
    ax.set_ylim(min(prices) * 0.85, max(prices) * 1.08)
    ax.fill_between(dates, prices, y2=min(prices) * 0.85,
                     color=s["bg_below"], alpha=1.0, zorder=1)

    # Glow + main line
    if s.get("glow"):
        ax.plot(dates, prices, color=s["line"], linewidth=6.0, alpha=0.12, zorder=2)
    ax.plot(dates, prices, color=s["line"], linewidth=s["line_w"], alpha=0.95,
            label=data.ticker, zorder=3)

    # Sector ETF overlay
    ax2 = ax.twinx()
    if data.etf_dates and data.etf_prices and len(data.etf_prices) >= 2:
        indexed = index_to_base(data.etf_prices, 100.0)
        ax2.plot(data.etf_dates, indexed, color=s["etf_above"], linewidth=0.8,
                 alpha=0.4, linestyle="--", label=data.etf_ticker, zorder=2)
        ax2.tick_params(axis="y", colors=s["etf_above"], labelsize=5, length=2)
        for sp in ax2.spines.values():
            sp.set_visible(False)

    # Cluster spans
    if clusters:
        for cl in clusters:
            if len(cl) < 2: continue
            f = _parse_date(cl[0].date.value) if cl[0].date else None
            l = _parse_date(cl[-1].date.value) if cl[-1].date else None
            if f and l:
                ax.axvspan(f, l, facecolor="#DC2626", alpha=0.06, zorder=1)

    csizes = {i: len(cl) for i, cl in enumerate(clusters)} if clusters else {}
    marker_scale = s.get("marker_scale", 1.0)
    marker_edge_w = s.get("marker_edge_w", 0.8)

    for i, drop in enumerate(drops, 1):
        if not drop.drop_pct or not drop.date: continue
        dd = _parse_date(drop.date.value)
        if not dd: continue
        y = _find_y(dates, prices, dd)
        if y is None: continue
        pct = drop.drop_pct.value
        base_ms = 14 if pct <= -15 else 11 if pct <= -10 else 8
        ms = base_ms * marker_scale
        mk = "s" if csizes.get(i-1, 1) > 1 else "o"
        mc = _PAL[(i-1) % len(_PAL)]

        # Optional drop glow
        if s.get("drop_glow"):
            ax.plot(dd, y, mk, color=mc, markersize=ms*1.6, alpha=0.2,
                    markeredgecolor="none", zorder=5)

        ax.plot(dd, y, mk, color=mc, markersize=ms,
                markeredgecolor=s["marker_edge"], markeredgewidth=marker_edge_w,
                alpha=0.95, zorder=6)
        ax.annotate(str(i), (dd, y), fontsize=5.5 if i < 10 else 4.5,
                     fontweight="bold", color="white", ha="center", va="center", zorder=7)
        ax.annotate(f"{pct:+.0f}%", (dd, y), textcoords="offset points",
                     xytext=(0, -(ms + 5)), fontsize=6.5, fontweight="bold",
                     color=s["drop_label"], ha="center", va="top", zorder=6)

    # Grid — subtle in both zones
    ax.grid(visible=True, alpha=0.15, color=s["grid_above"], linewidth=0.5, zorder=0)

    ax.set_ylabel("Price ($)", color=s["text_above"], fontsize=7)
    ax.tick_params(colors=s["text_above"], labelsize=6, length=3)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("bottom", "left"):
        ax.spines[sp].set_color(s["grid_above"])
        ax.spines[sp].set_linewidth(0.5)

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    if h1 or h2:
        ax.legend(h1+h2, l1+l2, loc="upper left", fontsize=6, framealpha=0.8,
                  edgecolor="none", facecolor=s["bg_above"], labelcolor=s["text_above"])

    svg = save_chart_to_svg(fig)
    plt.close(fig)
    return svg


def main():
    state = AnalysisState.model_validate_json(open("output/VKTX/state.json").read())
    data = extract_chart_data(state, "2Y")
    if not data: print("No data"); return

    cs, ce = data.dates[0], data.dates[-1]
    filtered = [d for d in data.drops if d.date and cs <= _parse_date(d.date.value[:10]) <= ce]
    deduped = _deduplicate_drops(_sort_drops(filtered))
    clusters = _cluster_drops(deduped, max_gap_days=30)
    chart_drops = [min(cl, key=lambda d: d.drop_pct.value if d.drop_pct else 0) for cl in clusters]

    print(f"Generating {len(STYLES)} split-tone charts...")
    parts = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Split-Tone Chart Gallery — VKTX</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
body{font-family:Inter,sans-serif;background:#FFFFFF;color:#1E293B;padding:30px;margin:0}
h1{text-align:center;font-size:22pt;font-weight:900;margin-bottom:4px;color:#0F172A}
.sub{text-align:center;font-size:10pt;color:#64748B;margin-bottom:30px}
.grid{display:grid;grid-template-columns:1fr;gap:24px;max-width:1200px;margin:0 auto}
.card{border-radius:12px;overflow:hidden;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.hdr{padding:10px 16px;background:#F8FAFC;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #E2E8F0}
.nm{font-size:12pt;font-weight:800;color:#0F172A}
.ds{font-size:8pt;color:#64748B;margin-top:2px}
.num{font-size:28pt;font-weight:900;color:#E2E8F0}
svg{width:100%;height:auto;display:block}
</style></head><body>
<h1>Split-Tone Chart Gallery</h1>
<div class="sub">VKTX · The price line splits dark from light — 10 variations</div>
<div class="grid">"""]

    for i, s in enumerate(STYLES, 1):
        print(f"  [{i:2d}/{len(STYLES)}] {s['name']}")
        svg = render_split_chart(data, chart_drops, clusters, s)
        parts.append(f"""<div class="card">
<div class="hdr"><div><div class="nm">{i}. {s['name']}</div>
<div class="ds">{s['desc']}</div></div>
<div class="num">{i:02d}</div></div>
<div>{svg}</div></div>""")

    parts.append("</div></body></html>")
    out = "output/VKTX/chart_split_gallery.html"
    with open(out, "w") as f:
        f.write("\n".join(parts))
    print(f"\nGallery: {out}")

if __name__ == "__main__":
    main()
