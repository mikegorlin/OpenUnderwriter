"""Bloomberg Terminal + Purple + Neon chart variations."""
from __future__ import annotations
import sys
sys.path.insert(0, "src")
from dotenv import load_dotenv
load_dotenv()

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.stock_chart_data import ChartData, extract_chart_data, index_to_base
from do_uw.stages.render.charts.unified_drop_chart import _sort_drops, _deduplicate_drops, _cluster_drops, _parse_date, _find_y
from do_uw.stages.render.chart_helpers import save_chart_to_svg

_PAL = ["#FF2D55","#BF5AF2","#5E5CE6","#30D158","#FFD60A",
        "#FF375F","#AC8EFF","#64D2FF","#FF453A","#DA5BF6",
        "#32D74B","#FF9F0A"]

STYLES = [
    {"name": "Bloomberg Purple Neon",
     "desc": "Black bg, neon purple price line, green terminal text, amber grid",
     "bg": "#000000", "grid": "#1A0A2E", "ga": 0.3,
     "line": "#BF5AF2", "lw": 2.2, "glow": True,
     "etf": "#30D158", "txt": "#30D158", "me": "#BF5AF2", "dl": "#FF2D55"},

    {"name": "Bloomberg Purple + Gold",
     "desc": "Black bg, vivid purple line, gold/amber accents like classic terminal",
     "bg": "#000000", "grid": "#1A0A2E", "ga": 0.25,
     "line": "#AC8EFF", "lw": 2.0, "glow": True,
     "etf": "#FFD60A", "txt": "#FFD60A", "me": "white", "dl": "#FF453A"},

    {"name": "Deep Purple Terminal",
     "desc": "Very dark purple bg, bright violet line, neon green grid ticks",
     "bg": "#0D0020", "grid": "#1A0040", "ga": 0.3,
     "line": "#DA5BF6", "lw": 2.5, "glow": True,
     "etf": "#30D158", "txt": "#AC8EFF", "me": "white", "dl": "#FF2D55"},

    {"name": "Neon Violet on Black",
     "desc": "Pure black, intense violet with heavy glow, maximum neon",
     "bg": "#000000", "grid": "#120025", "ga": 0.2,
     "line": "#E040FB", "lw": 2.5, "glow_heavy": True,
     "etf": "#00E5FF", "txt": "#E040FB", "me": "#E040FB", "dl": "#FF1744"},

    {"name": "Purple Haze",
     "desc": "Dark purple-black, softer lavender line, teal sector overlay",
     "bg": "#080015", "grid": "#150030", "ga": 0.25,
     "line": "#C4B5FD", "lw": 2.0, "glow": True,
     "etf": "#5EEAD4", "txt": "#C4B5FD", "me": "white", "dl": "#FB7185"},

    {"name": "Cyberpunk Purple",
     "desc": "Near-black with purple grid lines, hot pink price line, cyan accents",
     "bg": "#050010", "grid": "#200045", "ga": 0.35,
     "line": "#FF2D93", "lw": 2.2, "glow": True,
     "etf": "#00FFC6", "txt": "#FF2D93", "me": "#00FFC6", "dl": "#FFD60A"},

    {"name": "Bloomberg Classic + Purple Wash",
     "desc": "Standard Bloomberg black/amber but with purple-tinted grid zones",
     "bg": "#000000", "grid": "#110022", "ga": 0.3,
     "line": "#FFB300", "lw": 1.8, "glow": False,
     "etf": "#BF5AF2", "txt": "#00E676", "me": "#FFB300", "dl": "#FF5252",
     "cluster_color": "#BF5AF2"},

    {"name": "Royal Purple + Neon Orange",
     "desc": "Deep royal purple bg, neon orange price line, vivid contrast",
     "bg": "#0A0020", "grid": "#180040", "ga": 0.25,
     "line": "#FF9500", "lw": 2.5, "glow": True,
     "etf": "#AC8EFF", "txt": "#AC8EFF", "me": "white", "dl": "#FF2D55"},

    {"name": "Electric Purple Wide Glow",
     "desc": "Black bg, electric purple line with MASSIVE glow halo, drops POP",
     "bg": "#000000", "grid": "#0D001A", "ga": 0.15,
     "line": "#A855F7", "lw": 2.0, "glow_heavy": True,
     "etf": "#64748B", "txt": "#A855F7", "me": "white", "dl": "#FF0050",
     "marker_scale": 1.3},

    {"name": "Matrix Purple",
     "desc": "Black bg, neon green-tinged purple line, terminal aesthetic",
     "bg": "#000000", "grid": "#001A0D", "ga": 0.25,
     "line": "#9F7AEA", "lw": 2.0, "glow": True,
     "etf": "#48BB78", "txt": "#48BB78", "me": "#48BB78", "dl": "#FC8181"},
]


def render_chart(data, drops, clusters, s):
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(14, 3.5), dpi=150, facecolor=s["bg"])
    ax = fig.add_axes([0.05, 0.12, 0.89, 0.84])
    ax.set_facecolor(s["bg"])

    # Heavy glow (3 layers)
    if s.get("glow_heavy"):
        ax.plot(data.dates, data.prices, color=s["line"], linewidth=12.0, alpha=0.06, zorder=1)
        ax.plot(data.dates, data.prices, color=s["line"], linewidth=7.0, alpha=0.12, zorder=2)
        ax.plot(data.dates, data.prices, color=s["line"], linewidth=4.0, alpha=0.20, zorder=2)
    elif s.get("glow"):
        ax.plot(data.dates, data.prices, color=s["line"], linewidth=6.0, alpha=0.12, zorder=2)

    ax.plot(data.dates, data.prices, color=s["line"], linewidth=s["lw"], alpha=0.95,
            label=data.ticker, zorder=3)

    # Fill under with very subtle version of line color
    ax.fill_between(data.dates, data.prices, alpha=0.04, color=s["line"], zorder=1)

    ax2 = ax.twinx()
    if data.etf_dates and data.etf_prices and len(data.etf_prices) >= 2:
        indexed = index_to_base(data.etf_prices, 100.0)
        ax2.plot(data.etf_dates, indexed, color=s["etf"], linewidth=0.8, alpha=0.5,
                 linestyle="--", label=data.etf_ticker, zorder=2)
        ax2.tick_params(axis="y", colors=s["etf"], labelsize=5, length=2)
        for sp in ax2.spines.values():
            sp.set_visible(False)

    # Cluster spans with custom color
    cluster_col = s.get("cluster_color", "#DC2626")
    csizes = {}
    if clusters:
        for i, cl in enumerate(clusters):
            csizes[i] = len(cl)
            if len(cl) < 2: continue
            f = _parse_date(cl[0].date.value) if cl[0].date else None
            l = _parse_date(cl[-1].date.value) if cl[-1].date else None
            if f and l:
                ax.axvspan(f, l, facecolor=cluster_col, alpha=0.08, zorder=1)

    ms_scale = s.get("marker_scale", 1.0)
    for i, drop in enumerate(drops, 1):
        if not drop.drop_pct or not drop.date: continue
        dd = _parse_date(drop.date.value)
        if not dd: continue
        y = _find_y(data.dates, data.prices, dd)
        if y is None: continue
        pct = drop.drop_pct.value
        base_ms = 14 if pct <= -15 else 11 if pct <= -10 else 8
        ms = base_ms * ms_scale
        mk = "s" if csizes.get(i-1, 1) > 1 else "o"
        mc = _PAL[(i-1) % len(_PAL)]
        ax.plot(dd, y, mk, color=mc, markersize=ms, markeredgecolor=s["me"],
                markeredgewidth=0.8, alpha=0.95, zorder=6)
        ax.annotate(str(i), (dd, y), fontsize=5.5 if i < 10 else 4.5,
                     fontweight="bold", color="white", ha="center", va="center", zorder=7)
        ax.annotate(f"{pct:+.0f}%", (dd, y), textcoords="offset points",
                     xytext=(0, -(ms + 5)), fontsize=6.5, fontweight="bold",
                     color=s["dl"], ha="center", va="top", zorder=6)

    ax.set_ylabel("Price ($)", color=s["txt"], fontsize=7)
    ax.tick_params(colors=s["txt"], labelsize=6, length=3)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("bottom", "left"):
        ax.spines[sp].set_color(s["grid"])
        ax.spines[sp].set_linewidth(0.5)
    ax.grid(visible=True, alpha=s["ga"], color=s["grid"], linewidth=0.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    if h1 or h2:
        ax.legend(h1+h2, l1+l2, loc="upper left", fontsize=6, framealpha=0.7,
                  edgecolor="none", facecolor=s["bg"], labelcolor=s["txt"])
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

    print(f"Generating {len(STYLES)} neon purple charts...")
    parts = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Bloomberg Purple Neon Gallery</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
body{font-family:Inter,sans-serif;background:#000000;color:#E2E8F0;padding:30px;margin:0}
h1{text-align:center;font-size:22pt;font-weight:900;color:#BF5AF2;margin-bottom:4px}
.sub{text-align:center;font-size:10pt;color:#64748B;margin-bottom:30px}
.grid{display:grid;grid-template-columns:1fr;gap:20px;max-width:1200px;margin:0 auto}
.card{border-radius:10px;overflow:hidden;border:1px solid #1A0A2E}
.hdr{padding:10px 16px;background:#0A0020;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1A0A2E}
.nm{font-size:12pt;font-weight:800;color:#BF5AF2}
.ds{font-size:8pt;color:#64748B;margin-top:2px}
.num{font-size:28pt;font-weight:900;color:#1A0A2E}
svg{width:100%;height:auto;display:block}
</style></head><body>
<h1>Bloomberg Terminal + Purple Neon</h1>
<div class="sub">VKTX · 10 variations — black bg, purple/neon lines, terminal aesthetic</div>
<div class="grid">"""]

    for i, s in enumerate(STYLES, 1):
        print(f"  [{i:2d}/{len(STYLES)}] {s['name']}")
        svg = render_chart(data, chart_drops, clusters, s)
        parts.append(f"""<div class="card" style="background:{s['bg']}">
<div class="hdr"><div><div class="nm">{i}. {s['name']}</div>
<div class="ds">{s['desc']}</div></div>
<div class="num">{i:02d}</div></div>
<div>{svg}</div></div>""")

    parts.append("</div></body></html>")
    out = "output/VKTX/chart_neon_purple_gallery.html"
    with open(out, "w") as f:
        f.write("\n".join(parts))
    print(f"\nGallery: {out}")

if __name__ == "__main__":
    main()
