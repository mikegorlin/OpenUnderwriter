#!/usr/bin/env python3
"""Chart Style Gallery — 40+ dramatically different chart & infographic styles rendered side-by-side."""

from pathlib import Path


def svg_line(points, color, width=1.5, dash=""):
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    attrs = f'fill="none" stroke="{color}" stroke-width="{width}"'
    if dash:
        attrs += f' stroke-dasharray="{dash}"'
    return f'<path d="{d}" {attrs}/>'


def svg_area(points, color, opacity=0.12):
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    last_x = points[-1][0]
    first_x = points[0][0]
    d += f" L{last_x},80 L{first_x},80Z"
    return f'<path d="{d}" fill="{color}" opacity="{opacity}"/>'


# Sample price data (normalized 0-80 Y axis, 0-300 X axis)
PRICE_UP = [(0,55),(30,50),(60,45),(90,40),(120,35),(150,38),(180,32),(210,28),(240,22),(270,18),(300,12)]
PRICE_DOWN = [(0,15),(30,18),(60,22),(90,28),(120,35),(150,40),(180,48),(210,55),(240,60),(270,65),(300,70)]
PRICE_VOLATILE = [(0,40),(30,25),(60,45),(90,20),(120,50),(150,30),(180,55),(210,35),(240,15),(270,40),(300,25)]
SECTOR = [(0,50),(30,48),(60,46),(90,44),(120,42),(150,41),(180,39),(210,37),(240,35),(270,33),(300,30)]

def chart_card(name, desc, bg, content_svg, w=300, h=80):
    return f'''<div style="background:#111;border-radius:8px;overflow:hidden;border:1px solid #333">
<div style="padding:6px 10px;display:flex;justify-content:space-between;align-items:center">
  <div><div style="font-size:10px;font-weight:800;color:white">{name}</div><div style="font-size:7px;color:#6B7280">{desc}</div></div>
</div>
<div style="background:{bg};padding:8px 10px;margin:0 4px 4px;border-radius:4px">
<svg width="100%" height="{h}" viewBox="0 0 {w} {h}">{content_svg}</svg>
</div></div>'''


def build():
    cards = []

    # ═══════════════════════════════════════
    # LINE CHART STYLES (15 variations)
    # ═══════════════════════════════════════

    # 1. Bloomberg Dark Gold
    s = svg_area(PRICE_UP, "#D4A843", 0.15) + svg_line(PRICE_UP, "#D4A843", 2)
    s += svg_line(SECTOR, "#6B7280", 1, "4,3")
    cards.append(("line", chart_card("Bloomberg Dark Gold", "Classic terminal look — gold line on navy", "#0B1D3A", s)))

    # 2. Slate Modern
    s = svg_line(PRICE_UP, "#38BDF8", 2) + svg_area(PRICE_UP, "#38BDF8", 0.08)
    s += svg_line(SECTOR, "#475569", 1, "4,3")
    cards.append(("line", chart_card("Slate Modern", "Sky blue on deep slate", "#1A1A2E", s)))

    # 3. Liberty Warm
    s = svg_line(PRICE_UP, "#E8903A", 2.5)
    s += f'<path d="M0,55 L30,50 L60,45 L90,40 L120,35 L150,38 L180,32 L210,28 L240,22 L270,18 L300,12" fill="none" stroke="#E8903A" stroke-width="5" opacity="0.12"/>'
    s += svg_line(SECTOR, "#6B7280", 1, "4,3")
    cards.append(("line", chart_card("Liberty Warm", "Orange glow effect on navy", "#0F172A", s)))

    # 4. Neon Purple
    s = svg_line(PRICE_UP, "#A855F7", 2) + svg_area(PRICE_UP, "#A855F7", 0.1)
    s += svg_line(SECTOR, "#4B5563", 1, "3,3")
    cards.append(("line", chart_card("Neon Purple", "Electric purple on charcoal", "#18181B", s)))

    # 5. WSJ Classic
    s = svg_line(PRICE_UP, "#0F172A", 1.8) + svg_area(PRICE_UP, "#0F172A", 0.04)
    s += svg_line(SECTOR, "#D97706", 1.2, "6,2")
    for y in [20,40,60]:
        s += f'<line x1="0" y1="{y}" x2="300" y2="{y}" stroke="#E2E8F0" stroke-width="0.5"/>'
    cards.append(("line", chart_card("WSJ Classic", "Black line on white, amber sector", "#FFFFFF", s)))

    # 6. Economist Red
    s = svg_line(PRICE_DOWN, "#DC2626", 2) + svg_area(PRICE_DOWN, "#DC2626", 0.08)
    for y in [20,40,60]:
        s += f'<line x1="0" y1="{y}" x2="300" y2="{y}" stroke="#F1F5F9" stroke-width="0.5"/>'
    cards.append(("line", chart_card("Economist Red", "Red decline on cream", "#FFF8F0", s)))

    # 7. FT Salmon
    s = svg_line(PRICE_UP, "#0F172A", 1.8)
    s += svg_line(SECTOR, "#0891B2", 1.2, "5,3")
    for y in [20,40,60]:
        s += f'<line x1="0" y1="{y}" x2="300" y2="{y}" stroke="#E2D8CC" stroke-width="0.5"/>'
    cards.append(("line", chart_card("FT Salmon", "Dark line on salmon-pink", "#FFF1E6", s)))

    # 8. Mint Clean
    s = svg_line(PRICE_UP, "#059669", 2) + svg_area(PRICE_UP, "#059669", 0.06)
    for y in [20,40,60]:
        s += f'<line x1="0" y1="{y}" x2="300" y2="{y}" stroke="#E2E8F0" stroke-width="0.3"/>'
    cards.append(("line", chart_card("Mint Clean", "Green on white, minimal grid", "#FFFFFF", s)))

    # 9. Ice Blue
    s = svg_line(PRICE_UP, "#0369A1", 2) + svg_area(PRICE_UP, "#0369A1", 0.06)
    cards.append(("line", chart_card("Ice Blue", "Deep blue on ice", "#F0F9FF", s)))

    # 10. Dual Tone (up/down colored)
    split = 150
    s = f'<path d="M0,55 L30,50 L60,45 L90,40 L120,35 L{split},38" fill="none" stroke="#16A34A" stroke-width="2"/>'
    s += f'<path d="M{split},38 L180,32 L210,28 L240,22 L270,18 L300,12" fill="none" stroke="#16A34A" stroke-width="2"/>'
    s += svg_line(SECTOR, "#94A3B8", 1, "4,3")
    s += f'<line x1="0" y1="38" x2="300" y2="38" stroke="#E2E8F0" stroke-width="0.5" stroke-dasharray="2,2"/>'
    cards.append(("line", chart_card("Dual Tone", "Green above baseline, red below", "#FAFAFA", s)))

    # 11. Midnight Teal
    s = svg_line(PRICE_UP, "#14B8A6", 2) + svg_area(PRICE_UP, "#14B8A6", 0.12)
    cards.append(("line", chart_card("Midnight Teal", "Teal glow on near-black", "#0C0F14", s)))

    # 12. Warm Sand
    s = svg_line(PRICE_UP, "#92400E", 2) + svg_area(PRICE_UP, "#92400E", 0.08)
    for y in [20,40,60]:
        s += f'<line x1="0" y1="{y}" x2="300" y2="{y}" stroke="#D6CFC4" stroke-width="0.4"/>'
    cards.append(("line", chart_card("Warm Sand", "Brown on warm beige", "#F5F0E8", s)))

    # 13. High Contrast
    s = svg_line(PRICE_VOLATILE, "#FFFFFF", 2)
    for i, (x, y) in enumerate(PRICE_VOLATILE):
        col = "#16A34A" if i > 0 and y < PRICE_VOLATILE[i-1][1] else "#DC2626"
        s += f'<circle cx="{x}" cy="{y}" r="3" fill="{col}"/>'
    cards.append(("line", chart_card("High Contrast", "White line on black, colored dots", "#000000", s)))

    # 14. Gradient Fill
    s = f'<defs><linearGradient id="gf1" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3B82F6" stop-opacity="0.3"/><stop offset="100%" stop-color="#3B82F6" stop-opacity="0.02"/></linearGradient></defs>'
    d = "M" + " L".join(f"{x},{y}" for x, y in PRICE_UP) + " L300,80 L0,80Z"
    s += f'<path d="{d}" fill="url(#gf1)"/>'
    s += svg_line(PRICE_UP, "#3B82F6", 2)
    cards.append(("line", chart_card("Gradient Fill", "Blue gradient fade on white", "#FFFFFF", s)))

    # 15. Step Line
    step_pts = []
    for i, (x, y) in enumerate(PRICE_UP):
        if i > 0:
            step_pts.append((x, PRICE_UP[i-1][1]))
        step_pts.append((x, y))
    s = svg_line(step_pts, "#7C3AED", 1.5)
    cards.append(("line", chart_card("Step Line", "Purple step function — discrete changes", "#FAFAFA", s)))

    # ═══════════════════════════════════════
    # BAR CHART STYLES (10 variations)
    # ═══════════════════════════════════════

    # 16. Debt Maturity Dark
    bars = ""
    vals = [(15,50,"#DC2626"),(45,38,"#DC2626"),(75,28,"#3B82F6"),(105,22,"#3B82F6"),(135,18,"#3B82F6"),(165,12,"#3B82F6")]
    for x, h, c in vals:
        bars += f'<rect x="{x}" y="{80-h}" width="22" height="{h}" rx="2" fill="{c}"/>'
    cards.append(("bar", chart_card("Debt Maturity Dark", "Red near-term, blue future — dark bg", "#0F172A",
        bars + '<text x="26" y="78" font-size="5" fill="#6B7280">2025</text><text x="56" y="78" font-size="5" fill="#6B7280">2026</text><text x="86" y="78" font-size="5" fill="#6B7280">2027</text>')))

    # 17. Revenue Bars Light
    bars = ""
    vals = [(10,45),(50,52),(90,48),(130,58),(170,62),(210,55)]
    for i, (x, h) in enumerate(vals):
        bars += f'<rect x="{x}" y="{80-h}" width="30" height="{h}" rx="3" fill="#0369A1" opacity="{0.4 + i*0.12}"/>'
    cards.append(("bar", chart_card("Revenue Bars Light", "Progressive opacity — most recent darkest", "#FFFFFF", bars)))

    # 18. Grouped Comparison
    bars = ""
    for i, x in enumerate([10, 80, 150, 220]):
        h1, h2 = [40,55,48,60][i], [35,50,52,45][i]
        bars += f'<rect x="{x}" y="{80-h1}" width="14" height="{h1}" rx="2" fill="#0369A1"/>'
        bars += f'<rect x="{x+16}" y="{80-h2}" width="14" height="{h2}" rx="2" fill="#D97706"/>'
    cards.append(("bar", chart_card("Grouped Compare", "Blue=company, amber=peer side-by-side", "#FAFAFA", bars)))

    # 19. Horizontal Lollipop
    bars = ""
    items = [("Litigation",85,"#DC2626"),("Financial",60,"#D97706"),("Governance",30,"#16A34A"),("Stock",45,"#D97706"),("Insider",10,"#16A34A")]
    for i, (label, pct, col) in enumerate(items):
        y = 8 + i * 14
        bars += f'<line x1="70" y1="{y}" x2="{70+pct*2}" y2="{y}" stroke="{col}" stroke-width="2"/>'
        bars += f'<circle cx="{70+pct*2}" cy="{y}" r="4" fill="{col}"/>'
        bars += f'<text x="65" y="{y+3}" text-anchor="end" font-size="6" fill="#64748B">{label}</text>'
        bars += f'<text x="{75+pct*2}" y="{y+3}" font-size="6" fill="{col}" font-weight="700">{pct}%</text>'
    cards.append(("bar", chart_card("Lollipop Horizontal", "Clean horizontal with endpoint dots", "#FFFFFF", bars)))

    # 20. Stacked 100%
    segs = [(0,"#0369A1",38),(38,"#0891B2",28),(66,"#7C3AED",20),(86,"#D97706",14)]
    bars = ""
    for start, col, w in segs:
        bars += f'<rect x="{start*2.8}" y="20" width="{w*2.8}" height="30" fill="{col}"/>'
        if w > 12:
            bars += f'<text x="{start*2.8 + w*1.4}" y="38" text-anchor="middle" font-size="6" fill="white" font-weight="700">{w}%</text>'
    cards.append(("bar", chart_card("Stacked 100%", "Segment composition — full width", "#FFFFFF", bars, h=60)))

    # 21. Waterfall Score
    bars = '<rect x="5" y="5" width="25" height="70" rx="3" fill="#16A34A"/><text x="17" y="18" text-anchor="middle" font-size="7" fill="white" font-weight="800">100</text>'
    deductions = [(35,5,10,"#DC2626","F1"),(65,15,15,"#DC2626","F2"),(95,30,5,"#D97706","F3"),(125,35,0,"#E5E7EB","F4"),(155,35,8,"#DC2626","F5"),(185,43,3,"#D97706","F6")]
    for x, y, h, col, label in deductions:
        if h > 0:
            bars += f'<rect x="{x}" y="{y}" width="22" height="{h}" rx="2" fill="{col}"/>'
        bars += f'<text x="{x+11}" y="78" text-anchor="middle" font-size="4.5" fill="#6B7280">{label}</text>'
    bars += '<rect x="220" y="5" width="35" height="41" rx="3" fill="#16A34A"/><text x="237" y="22" text-anchor="middle" font-size="9" fill="white" font-weight="800">88</text><text x="237" y="32" text-anchor="middle" font-size="5" fill="white" opacity="0.7">WIN</text>'
    cards.append(("bar", chart_card("Waterfall Score", "Factor deductions from 100 → final score", "#FAFAFA", bars, w=270)))

    # 22. Tornado Sensitivity
    bars = ""
    items = [("Revenue",-35,55),("Margin",-50,20),("Stock Drop",-65,12),("Governance",-15,40),("Litigation",-60,8)]
    for i, (label, neg, pos) in enumerate(items):
        y = 5 + i * 14
        bars += f'<text x="90" y="{y+8}" text-anchor="end" font-size="6" fill="#64748B">{label}</text>'
        bars += f'<rect x="{95+neg}" y="{y}" width="{abs(neg)}" height="10" rx="2" fill="#DC2626" opacity="0.7"/>'
        bars += f'<line x1="95" y1="{y-2}" x2="95" y2="{y+12}" stroke="#374151" stroke-width="0.8"/>'
        bars += f'<rect x="95" y="{y}" width="{pos}" height="10" rx="2" fill="#16A34A" opacity="0.7"/>'
    cards.append(("bar", chart_card("Tornado Sensitivity", "Downside (red) vs upside (green)", "#FFFFFF", bars, w=250)))

    # 23. Candlestick-style
    bars = ""
    candles = [(15,20,45,15,50),(45,25,40,22,42),(75,30,55,28,58),(105,22,38,18,42),(135,35,50,32,52),(165,28,42,25,45),(195,15,35,12,38),(225,20,30,18,32)]
    for x, o, c, l, h in candles:
        col = "#16A34A" if c < o else "#DC2626"
        bars += f'<line x1="{x+8}" y1="{l}" x2="{x+8}" y2="{h}" stroke="{col}" stroke-width="1"/>'
        bars += f'<rect x="{x}" y="{min(o,c)}" width="16" height="{abs(c-o)}" fill="{col}"/>'
    cards.append(("bar", chart_card("Candlestick", "OHLC quarterly — green up, red down", "#0F172A", bars, w=250)))

    # ═══════════════════════════════════════
    # SPECIAL / INFOGRAPHIC (15 variations)
    # ═══════════════════════════════════════

    # 24. Radar Dark
    def radar(fill, stroke, bg, opacity=0.2):
        pts = "100,25 155,50 170,110 145,160 55,160 30,110 45,50"
        grid1 = "100,20 165,48 182,115 150,168 50,168 18,115 35,48"
        grid2 = "100,50 140,65 152,105 135,140 65,140 48,105 60,65"
        s = f'<polygon points="{grid1}" fill="none" stroke="{"#334155" if "1A" in bg else "#E2E8F0"}" stroke-width="0.5"/>'
        s += f'<polygon points="{grid2}" fill="none" stroke="{"#334155" if "1A" in bg else "#E2E8F0"}" stroke-width="0.5"/>'
        s += f'<polygon points="{pts}" fill="{fill}" opacity="{opacity}" stroke="{stroke}" stroke-width="1.5"/>'
        for x, y in [(100,25),(155,50),(170,110),(145,160),(55,160),(30,110),(45,50)]:
            s += f'<circle cx="{x}" cy="{y}" r="3" fill="{stroke}"/>'
        return s

    cards.append(("special", chart_card("Radar Dark Gold", "Navy fill, gold outline on dark", "#1A1A2E", radar("#0F172A","#D4A843","#1A1A2E"), w=200, h=180)))
    cards.append(("special", chart_card("Radar Light Blue", "Blue fill on white", "#FFFFFF", radar("#0369A1","#0369A1","#FFFFFF",0.1), w=200, h=180)))
    cards.append(("special", chart_card("Radar Green Minimal", "Green with no fill", "#FAFAFA", radar("#16A34A","#16A34A","#FAFAFA",0.05), w=200, h=180)))

    # 27. Donut variations
    def donut(pcts, colors, center_text, center_sub, bg="#FFFFFF"):
        s = ""
        offset = 0
        total = 220  # circumference of r=35
        for pct, col in zip(pcts, colors):
            dash = pct / 100 * total
            s += f'<circle cx="60" cy="60" r="35" fill="none" stroke="{col}" stroke-width="14" stroke-dasharray="{dash} {total-dash}" stroke-dashoffset="{-offset}" transform="rotate(-90 60 60)"/>'
            offset += dash
        s += f'<text x="60" y="56" text-anchor="middle" font-size="14" font-weight="900" fill="#1E293B">{center_text}</text>'
        s += f'<text x="60" y="68" text-anchor="middle" font-size="5" fill="#94A3B8">{center_sub}</text>'
        return s

    cards.append(("special", chart_card("Donut — Ownership", "Institutional/Insider/Retail", "#FFFFFF", donut([70,20,10],["#0F172A","#D4A843","#94A3B8"],"70%","Institutional"), w=120, h=120)))
    cards.append(("special", chart_card("Donut — Independence", "Board independence ratio", "#FFFFFF", donut([80,20],["#16A34A","#E5E7EB"],"80%","Independent"), w=120, h=120)))
    cards.append(("special", chart_card("Donut — Debt/Cash", "Leverage composition", "#FFFFFF", donut([86,14],["#DC2626","#16A34A"],"86%","Debt"), w=120, h=120)))

    # 30. Gauge variations
    def gauge(score, label, color, bg="#FFFFFF"):
        s = f'<path d="M15,65 A35,35 0 0,1 105,65" fill="none" stroke="#E5E7EB" stroke-width="8" stroke-linecap="round"/>'
        pct = min(score, 100) / 100
        # Approximate arc length
        s += f'<path d="M15,65 A35,35 0 0,1 105,65" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="{pct * 140} 140"/>'
        s += f'<text x="60" y="58" text-anchor="middle" font-size="18" font-weight="900" fill="{color}">{score}</text>'
        s += f'<text x="60" y="72" text-anchor="middle" font-size="6" fill="#94A3B8">{label}</text>'
        return s

    cards.append(("special", chart_card("Gauge — Score (Green)", "Quality score 91/100", "#FFFFFF", gauge(91, "WIN", "#16A34A"), w=120, h=80)))
    cards.append(("special", chart_card("Gauge — Score (Amber)", "Quality score 55/100", "#FFFFFF", gauge(55, "WATCH", "#D97706"), w=120, h=80)))
    cards.append(("special", chart_card("Gauge — Score (Red)", "Quality score 28/100", "#FFFFFF", gauge(28, "WALK", "#DC2626"), w=120, h=80)))
    cards.append(("special", chart_card("Gauge — Dark Theme", "Score on dark background", "#0F172A", gauge(91, "WIN", "#D4A843", "#0F172A"), w=120, h=80)))

    # 34. Heat map
    hm = ""
    data = [(8,3,-12,5,2,6,0,4), (5,4,-3,2,3,7,1,5)]
    labels = ["EPS","Rev"]
    quarters = ["Q1'24","Q2'24","Q3'24","Q4'24","Q1'25","Q2'25","Q3'25","Q4'25"]
    for row, (label, vals) in enumerate(zip(labels, data)):
        y = 18 + row * 18
        hm += f'<text x="24" y="{y+8}" text-anchor="end" font-size="5" fill="#64748B" font-weight="600">{label}</text>'
        for col, val in enumerate(vals):
            x = 28 + col * 28
            if val > 0:
                bg, fg = "#D1FAE5", "#065F46"
            elif val < 0:
                bg, fg = "#FEE2E2", "#991B1B"
            else:
                bg, fg = "#FEF3C7", "#92400E"
            hm += f'<rect x="{x}" y="{y}" width="26" height="16" rx="2" fill="{bg}"/>'
            hm += f'<text x="{x+13}" y="{y+11}" text-anchor="middle" font-size="5" fill="{fg}" font-weight="700">{val:+d}%</text>'
    for i, q in enumerate(quarters):
        hm += f'<text x="{41+i*28}" y="14" text-anchor="middle" font-size="4" fill="#94A3B8">{q}</text>'
    cards.append(("special", chart_card("Heat Map — Earnings", "Color-coded quarterly beat/miss grid", "#FFFFFF", hm, w=260, h=56)))

    # 35. P×S Matrix
    pxs = ""
    # 4 zone backgrounds
    pxs += '<rect x="40" y="0" width="110" height="40" rx="0" fill="#D1FAE5"/>'  # low-low
    pxs += '<rect x="150" y="0" width="110" height="40" rx="0" fill="#FEF3C7"/>'  # low-high
    pxs += '<rect x="40" y="40" width="110" height="40" rx="0" fill="#FEF3C7"/>'  # high-low
    pxs += '<rect x="150" y="40" width="110" height="40" rx="0" fill="#FEE2E2"/>'  # high-high
    pxs += '<text x="95" y="25" text-anchor="middle" font-size="5" fill="#065F46">Low Risk</text>'
    pxs += '<text x="205" y="25" text-anchor="middle" font-size="5" fill="#92400E">Moderate</text>'
    pxs += '<text x="95" y="65" text-anchor="middle" font-size="5" fill="#92400E">Elevated</text>'
    pxs += '<text x="205" y="65" text-anchor="middle" font-size="5" fill="#991B1B">Critical</text>'
    # Position dot
    pxs += '<circle cx="160" cy="35" r="8" fill="#D97706" stroke="white" stroke-width="2"/>'
    pxs += '<text x="160" y="38" text-anchor="middle" font-size="5" fill="white" font-weight="700">◆</text>'
    pxs += '<text x="36" y="44" text-anchor="end" font-size="4" fill="#94A3B8" transform="rotate(-90 36 44)">Severity →</text>'
    pxs += '<text x="150" y="78" text-anchor="middle" font-size="4" fill="#94A3B8">Probability →</text>'
    cards.append(("special", chart_card("P×S Risk Matrix", "Probability × Severity with position marker", "#FFFFFF", pxs, w=270)))

    # 36-40. More infographic elements
    # Score bar
    sb = '<rect x="0" y="10" width="280" height="12" rx="6" fill="#E5E7EB"/>'
    zones = [(0,42,"#991B1B"),(42,42,"#DC2626"),(84,42,"#EA580C"),(126,56,"#D97706"),(182,56,"#059669"),(238,42,"#16A34A")]
    for x, w, c in zones:
        sb += f'<rect x="{x}" y="10" width="{w}" height="12" fill="{c}"/>'
    sb += '<circle cx="252" cy="16" r="8" fill="white" stroke="#0F172A" stroke-width="2"/>'
    sb += '<text x="252" y="19" text-anchor="middle" font-size="6" fill="#0F172A" font-weight="800">91</text>'
    cards.append(("special", chart_card("Score Position Bar", "Linear score with tier zone colors", "#FAFAFA", sb, w=290, h=34)))

    # Severity blocks
    blocks = ""
    items = [("Securities Fraud",3,"#DC2626"),("Derivative",2,"#D97706"),("Employment",1,"#16A34A"),("Regulatory",2,"#D97706"),("Product",0,"#E5E7EB")]
    for i, (label, level, col) in enumerate(items):
        y = 4 + i * 14
        blocks += f'<text x="88" y="{y+8}" text-anchor="end" font-size="6" fill="#64748B">{label}</text>'
        for j in range(5):
            fill = col if j < level else "#E5E7EB"
            blocks += f'<rect x="{92+j*16}" y="{y}" width="14" height="10" rx="2" fill="{fill}"/>'
    cards.append(("special", chart_card("Severity Blocks", "Plaintiff exposure per claim type", "#FFFFFF", blocks, w=180, h=74)))

    # Bullet chart
    bc = ""
    items = [("ROE",18,15,25,"#0369A1"),("D/E",187,100,200,"#DC2626"),("Coverage",4.2,3,8,"#16A34A")]
    for i, (label, val, low, high, col) in enumerate(items):
        y = 8 + i * 22
        pct = min((val - low) / (high - low), 1) * 200
        bc += f'<text x="48" y="{y+10}" text-anchor="end" font-size="6" fill="#64748B">{label}</text>'
        bc += f'<rect x="52" y="{y+2}" width="200" height="12" rx="2" fill="#F1F5F9"/>'
        bc += f'<rect x="52" y="{y+2}" width="{pct}" height="12" rx="2" fill="{col}" opacity="0.6"/>'
        bc += f'<line x1="{52+pct}" y1="{y}" x2="{52+pct}" y2="{y+16}" stroke="#0F172A" stroke-width="2"/>'
        bc += f'<text x="258" y="{y+10}" font-size="6" fill="{col}" font-weight="700">{val}</text>'
    cards.append(("special", chart_card("Bullet Chart", "Value vs range with target marker", "#FFFFFF", bc, w=280, h=72)))

    # Slope chart
    sl = ""
    items = [("Revenue", 35, 28, "#16A34A"), ("EBITDA", 45, 52, "#DC2626"), ("Net Inc", 50, 42, "#16A34A")]
    sl += '<text x="40" y="8" text-anchor="middle" font-size="5" fill="#94A3B8" font-weight="600">FY2024</text>'
    sl += '<text x="160" y="8" text-anchor="middle" font-size="5" fill="#94A3B8" font-weight="600">FY2025</text>'
    sl += '<line x1="40" y1="12" x2="40" y2="75" stroke="#E2E8F0" stroke-width="0.5"/>'
    sl += '<line x1="160" y1="12" x2="160" y2="75" stroke="#E2E8F0" stroke-width="0.5"/>'
    for label, y1, y2, col in items:
        sl += f'<line x1="40" y1="{y1}" x2="160" y2="{y2}" stroke="{col}" stroke-width="1.5"/>'
        sl += f'<circle cx="40" cy="{y1}" r="3" fill="{col}"/><circle cx="160" cy="{y2}" r="3" fill="{col}"/>'
        sl += f'<text x="165" y="{y2+3}" font-size="5" fill="{col}" font-weight="600">{label}</text>'
    cards.append(("special", chart_card("Slope Chart", "Year-over-year directional change", "#FFFFFF", sl, w=200)))

    # Waffle chart
    wf = ""
    filled = 73  # 73%
    for row in range(10):
        for col in range(10):
            idx = row * 10 + col
            color = "#0369A1" if idx < filled else "#E5E7EB"
            wf += f'<rect x="{col*12+2}" y="{row*12+2}" width="10" height="10" rx="1.5" fill="{color}"/>'
    wf += f'<text x="62" y="135" text-anchor="middle" font-size="8" fill="#0369A1" font-weight="800">73% Institutional</text>'
    cards.append(("special", chart_card("Waffle Chart", "100-square grid showing proportions", "#FFFFFF", wf, w=124, h=140)))

    # ═══════════════════════════════════════
    # BUILD HTML
    # ═══════════════════════════════════════
    groups = {"line": "Line Charts", "bar": "Bar Charts", "special": "Special & Infographic"}
    group_colors = {"line": "#0F172A", "bar": "#DC2626", "special": "#7C3AED"}

    html = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Chart Style Gallery</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#0A0A0A;color:#E2E8F0;padding:16px}
h1{font-size:22px;font-weight:900;text-align:center;margin-bottom:4px}
.sub{font-size:11px;color:#6B7280;text-align:center;margin-bottom:20px}
.gh{display:flex;align-items:center;gap:10px;margin:24px 0 10px}
.gn{font-size:24px;font-weight:900;opacity:0.3}
.gt{font-size:15px;font-weight:800;color:white}
.gl{flex:1;height:1px;opacity:0.2;background:white}
.gc{font-size:9px;color:#6B7280}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.footer{text-align:center;margin-top:24px;font-size:9px;color:#4B5563}
</style></head><body>
<h1>Chart & Infographic Style Gallery</h1>
<div class="sub">''' + str(len(cards)) + ''' styles — pick favorites, mix elements, name what you like</div>
'''

    current_group = None
    for group, card_html in cards:
        if group != current_group:
            if current_group is not None:
                html += '</div>'  # close grid
            color = group_colors.get(group, "#6B7280")
            name = groups.get(group, group)
            count = sum(1 for g, _ in cards if g == group)
            html += f'<div class="gh"><div class="gn" style="color:{color}">{name[0]}</div><div class="gt">{name}</div><div class="gl"></div><div class="gc">{count} styles</div></div>'
            html += '<div class="grid">'
            current_group = group
        html += card_html

    html += '</div>'  # close last grid
    html += '<div class="footer">Review each style — tell me which ones to use for which cards</div></body></html>'

    return html


if __name__ == "__main__":
    html = build()
    Path("output/CHART_GALLERY.html").write_text(html)
    print(f"Generated: output/CHART_GALLERY.html")
