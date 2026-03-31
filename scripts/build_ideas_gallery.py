#!/usr/bin/env python3
"""Ideas Gallery — new visualization concepts for existing cards, heavy on stock charts."""
from pathlib import Path

# Price data curves
UP = "M0,65 C30,60 60,52 90,45 C120,38 150,42 180,35 C210,28 240,20 270,15 C285,12 300,10"
DOWN = "M0,12 C30,18 60,25 90,35 C120,42 150,48 180,55 C210,60 240,65 270,68 C285,70 300,72"
VOLATILE = "M0,40 C20,30 40,50 60,25 C80,45 100,20 120,55 C140,30 160,50 180,22 C200,45 220,35 240,18 C260,40 280,28 300,15"
SECTOR = "M0,58 C40,55 80,52 120,48 C160,45 200,42 240,38 C270,36 300,33"
SPY = "M0,55 C40,53 80,50 120,47 C160,44 200,41 240,38 C270,36 300,34"

def card(ref, name, desc, bg, svg_content, w=420, h=120, full=False):
    fw = 'style="grid-column:1/-1"' if full else ''
    return f'''<div {fw}>
<div style="background:#111;border:1px solid #333;border-radius:8px;overflow:hidden">
<div style="padding:8px 12px;display:flex;align-items:center;gap:8px">
  <span style="font-size:14px;font-weight:900;color:#D4A843;font-family:'JetBrains Mono',monospace">{ref}</span>
  <span style="font-size:11px;font-weight:800;color:white">{name}</span>
  <span style="font-size:8px;color:#6B7280;flex:1">{desc}</span>
</div>
<div style="background:{bg};padding:10px 12px;margin:0 4px 4px;border-radius:5px">
<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{svg_content}</svg>
</div></div></div>'''

def build():
    items = []

    # ═══════════════════════════════════════
    # STOCK CHART VARIATIONS (30+)
    # ═══════════════════════════════════════

    # S-01: Classic with sector overlay
    s = f'''<text x="4" y="10" font-size="7" fill="#D4A843" font-weight="700">RPM — 2Y WEEKLY</text>
<path d="{UP}" fill="none" stroke="#D4A843" stroke-width="2.5"/>
<path d="{UP}" fill="none" stroke="#D4A843" stroke-width="5" opacity="0.12"/>
<path d="{SECTOR}" fill="none" stroke="#6B7280" stroke-width="1" stroke-dasharray="4,3"/>
<text x="305" y="12" font-size="5" fill="#D4A843">Company</text>
<text x="305" y="35" font-size="5" fill="#6B7280">Sector ETF</text>'''
    items.append(card("S-01", "Classic Gold + Sector", "Dark bg, gold glow, dashed sector overlay", "#0B1D3A", s, full=True))

    # S-02: With class period shading
    s = f'''<text x="4" y="10" font-size="7" fill="#38BDF8" font-weight="700">META — WITH CLASS PERIOD</text>
<rect x="90" y="0" width="120" height="80" fill="#DC2626" opacity="0.08"/>
<line x1="90" y1="0" x2="90" y2="80" stroke="#DC2626" stroke-width="1" stroke-dasharray="3,2"/>
<line x1="210" y1="0" x2="210" y2="80" stroke="#DC2626" stroke-width="1" stroke-dasharray="3,2"/>
<text x="150" y="78" text-anchor="middle" font-size="5" fill="#DC2626" opacity="0.7">CLASS PERIOD</text>
<path d="{DOWN}" fill="none" stroke="#38BDF8" stroke-width="2"/>
<circle cx="90" cy="35" r="5" fill="#DC2626" opacity="0.8"/><text x="90" y="37" text-anchor="middle" font-size="4" fill="white" font-weight="700">▼</text>
<text x="78" y="30" text-anchor="end" font-size="5" fill="#DC2626">SCA Filed</text>'''
    items.append(card("S-02", "Class Period Overlay", "Red shading shows active class period — critical for D&O", "#0F172A", s, full=True))

    # S-03: With insider trading markers
    s = f'''<text x="4" y="10" font-size="7" fill="#E8903A" font-weight="700">INSIDER TRADING OVERLAY</text>
<path d="{VOLATILE}" fill="none" stroke="#E8903A" stroke-width="2"/>
<circle cx="60" cy="25" r="4" fill="#DC2626"/><text x="60" y="22" text-anchor="middle" font-size="4" fill="#DC2626">SELL</text>
<circle cx="100" cy="20" r="4" fill="#DC2626"/><text x="100" y="17" text-anchor="middle" font-size="4" fill="#DC2626">SELL</text>
<circle cx="140" cy="30" r="3" fill="#DC2626"/>
<circle cx="200" cy="45" r="4" fill="#16A34A"/><text x="200" y="42" text-anchor="middle" font-size="4" fill="#16A34A">BUY</text>
<rect x="50" y="18" width="100" height="20" fill="#DC2626" opacity="0.06" rx="2"/>
<text x="100" y="42" text-anchor="middle" font-size="4" fill="#DC2626" opacity="0.5">CLUSTER SELL WINDOW</text>'''
    items.append(card("S-03", "Insider Trading Overlay", "Buy/sell markers on price + cluster windows = scienter evidence", "#0F172A", s, full=True))

    # S-04: Earnings reaction bars
    s = f'''<text x="4" y="10" font-size="7" fill="#38BDF8" font-weight="700">EARNINGS REACTION</text>
<path d="{UP}" fill="none" stroke="#475569" stroke-width="1.5"/>
<rect x="55" y="42" width="6" height="15" fill="#16A34A" rx="1"/><text x="58" y="40" text-anchor="middle" font-size="4" fill="#16A34A">+4.2%</text>
<rect x="115" y="35" width="6" height="8" fill="#16A34A" rx="1"/>
<rect x="175" y="28" width="6" height="20" fill="#DC2626" rx="1"/><text x="178" y="25" text-anchor="middle" font-size="4" fill="#DC2626">-8.1%</text>
<rect x="235" y="18" width="6" height="5" fill="#16A34A" rx="1"/>
<text x="55" y="63" font-size="4" fill="#6B7280">Q1</text><text x="115" y="50" font-size="4" fill="#6B7280">Q2</text><text x="175" y="55" font-size="4" fill="#6B7280">Q3</text><text x="235" y="28" font-size="4" fill="#6B7280">Q4</text>'''
    items.append(card("S-04", "Earnings Reaction Bars", "Post-earnings stock moves as bars on price chart — miss = red = claim catalyst", "#0F172A", s))

    # S-05: With analyst price target range
    s = f'''<text x="4" y="10" font-size="7" fill="#14B8A6" font-weight="700">ANALYST CONSENSUS + RANGE</text>
<rect x="0" y="20" width="420" height="25" fill="#14B8A6" opacity="0.04" rx="2"/>
<line x1="0" y1="20" x2="420" y2="20" stroke="#14B8A6" stroke-width="0.5" stroke-dasharray="3,3"/>
<line x1="0" y1="45" x2="420" y2="45" stroke="#14B8A6" stroke-width="0.5" stroke-dasharray="3,3"/>
<line x1="0" y1="32" x2="420" y2="32" stroke="#14B8A6" stroke-width="0.8" stroke-dasharray="6,3"/>
<text x="422" y="23" font-size="4" fill="#14B8A6">High $165</text>
<text x="422" y="35" font-size="4" fill="#14B8A6">Consensus $142</text>
<text x="422" y="48" font-size="4" fill="#14B8A6">Low $118</text>
<path d="M0,55 C40,50 80,45 120,38 C160,42 200,48 240,40 C280,35 320,30 360,28 C380,25 420,22" fill="none" stroke="white" stroke-width="1.8"/>'''
    items.append(card("S-05", "Analyst Price Target Range", "Consensus + high/low target band — stock above/below consensus", "#0F172A", s, w=460))

    # S-06: Multi-indexed performance
    s = f'''<text x="4" y="10" font-size="7" fill="white" font-weight="700">RELATIVE PERFORMANCE — INDEXED TO 100</text>
<line x1="0" y1="40" x2="420" y2="40" stroke="#334155" stroke-width="0.5" stroke-dasharray="2,2"/><text x="422" y="42" font-size="4" fill="#6B7280">100</text>
<rect x="0" y="10" width="420" height="30" fill="#16A34A" opacity="0.03"/>
<rect x="0" y="40" width="420" height="35" fill="#DC2626" opacity="0.03"/>
<path d="M0,40 C40,36 80,28 120,22 C160,18 200,16 240,12 C280,10 320,8 360,6 C400,5 420,4" fill="none" stroke="#38BDF8" stroke-width="2"/>
<path d="M0,40 C40,38 80,35 120,32 C160,30 200,28 240,25 C280,23 320,22 360,20 C400,19 420,18" fill="none" stroke="#D4A843" stroke-width="1.2" stroke-dasharray="5,2"/>
<path d="M0,40 C40,39 80,37 120,35 C160,33 200,32 240,30 C280,29 320,28 360,27 C400,26 420,25" fill="none" stroke="#6B7280" stroke-width="1" stroke-dasharray="2,2"/>
<text x="422" y="6" font-size="5" fill="#38BDF8" font-weight="600">RPM +156%</text>
<text x="422" y="20" font-size="5" fill="#D4A843">Sector +85%</text>
<text x="422" y="27" font-size="5" fill="#6B7280">S&P +62%</text>
<text x="4" y="75" font-size="4" fill="#16A34A">▲ OUTPERFORMING</text>
<text x="4" y="46" font-size="4" fill="#DC2626" opacity="0.4">▼ UNDERPERFORMING</text>'''
    items.append(card("S-06", "Multi-Index Relative (Full Width)", "Company vs sector vs S&P indexed to 100 — green/red shading for over/under", "#0F172A", s, w=460, h=80, full=True))

    # S-07: Short interest overlay
    s = f'''<text x="4" y="10" font-size="7" fill="#A855F7" font-weight="700">PRICE + SHORT INTEREST</text>
<path d="{UP}" fill="none" stroke="#A855F7" stroke-width="2"/>
<path d="M0,75 C30,73 60,70 90,68 C120,72 150,74 180,70 C210,65 240,58 270,50 C285,48 300,55" fill="#DC2626" opacity="0.15" stroke="#DC2626" stroke-width="1"/>
<text x="305" y="12" font-size="5" fill="#A855F7">Price</text>
<text x="305" y="57" font-size="5" fill="#DC2626">Short Interest ↑</text>
<text x="240" y="46" font-size="4" fill="#DC2626" font-weight="700">25.1%</text>'''
    items.append(card("S-07", "Short Interest Dual-Axis", "Rising short interest as price climbs = contrarian signal", "#0F172A", s))

    # S-08: Drawdown with recovery annotation
    s = f'''<text x="4" y="10" font-size="7" fill="#DC2626" font-weight="700">DRAWDOWN WITH RECOVERY TIME</text>
<path d="M0,5 C20,5 40,8 60,15 C80,28 100,42 120,50 C140,55 160,52 180,45 C200,35 220,25 240,18 C260,12 280,8 300,5" fill="#DC2626" opacity="0.12" stroke="#DC2626" stroke-width="1.5"/>
<line x1="100" y1="42" x2="100" y2="55" stroke="#DC2626" stroke-width="0.5" stroke-dasharray="2,2"/>
<line x1="260" y1="12" x2="260" y2="55" stroke="#16A34A" stroke-width="0.5" stroke-dasharray="2,2"/>
<line x1="100" y1="55" x2="260" y2="55" stroke="#D97706" stroke-width="1.5"/>
<text x="180" y="62" text-anchor="middle" font-size="5" fill="#D97706" font-weight="700">Recovery: 187 days</text>
<text x="120" y="52" font-size="5" fill="#DC2626" font-weight="700">Max: -38.2%</text>
<text x="262" y="10" font-size="4" fill="#16A34A">Recovered</text>'''
    items.append(card("S-08", "Drawdown + Recovery Time", "Annotated max drawdown with recovery duration — tells the full story", "#0F172A", s))

    # S-09: Small multiples (6 timeframes)
    mini_charts = ""
    timeframes = [("1M",10,"#6B7280"), ("3M",20,"#6B7280"), ("6M",35,"#16A34A"), ("1Y",55,"#16A34A"), ("3Y",70,"#16A34A"), ("5Y",80,"#16A34A")]
    for i, (label, gain_h, col) in enumerate(timeframes):
        x = i * 70
        mini_charts += f'<rect x="{x}" y="0" width="65" height="75" rx="3" fill="#1A1A2E" stroke="#334155" stroke-width="0.5"/>'
        mini_charts += f'<text x="{x+32}" y="10" text-anchor="middle" font-size="5" fill="#94A3B8" font-weight="700">{label}</text>'
        if gain_h > 30:
            mini_charts += f'<path d="M{x+5},60 C{x+15},{60-gain_h*0.4} {x+35},{60-gain_h*0.6} {x+60},{60-gain_h*0.8}" fill="none" stroke="{col}" stroke-width="1.5"/>'
        else:
            mini_charts += f'<path d="M{x+5},{30} C{x+15},{30+gain_h*0.3} {x+35},{30-gain_h*0.2} {x+60},{30+gain_h*0.5}" fill="none" stroke="{col}" stroke-width="1.5"/>'
        pct = f"+{gain_h//2}%" if gain_h > 20 else f"-{30-gain_h}%"
        mini_charts += f'<text x="{x+32}" y="70" text-anchor="middle" font-size="6" fill="{col}" font-weight="800">{pct}</text>'
    items.append(card("S-09", "Small Multiples (6 Timeframes)", "1M/3M/6M/1Y/3Y/5Y — instant visual of performance profile", "#0A0A0A", mini_charts, w=420, h=80, full=True))

    # S-10: IPO reference price
    s = f'''<text x="4" y="10" font-size="7" fill="#D4A843" font-weight="700">IPO / OFFERING REFERENCE</text>
<line x1="0" y1="50" x2="420" y2="50" stroke="#7C3AED" stroke-width="1" stroke-dasharray="6,3"/>
<text x="422" y="52" font-size="4" fill="#7C3AED">IPO Price $24</text>
<line x1="60" y1="0" x2="60" y2="80" stroke="#7C3AED" stroke-width="0.8" stroke-dasharray="3,2"/>
<text x="62" y="78" font-size="4" fill="#7C3AED">IPO Date</text>
<line x1="180" y1="0" x2="180" y2="80" stroke="#D97706" stroke-width="0.8" stroke-dasharray="3,2"/>
<text x="182" y="78" font-size="4" fill="#D97706">Lockup Expiry</text>
<path d="M60,50 C80,45 100,35 120,28 C140,22 160,18 180,25 C200,30 220,28 240,22 C260,18 280,15 300,12 C340,8 380,10 420,8" fill="none" stroke="#D4A843" stroke-width="2"/>'''
    items.append(card("S-10", "IPO Price + Lockup Lines", "IPO price as horizontal ref, lockup expiry as vertical — Section 11 window", "#0F172A", s, w=460, full=True))

    # S-11: Volume profile (horizontal)
    s = f'''<text x="4" y="10" font-size="7" fill="#38BDF8" font-weight="700">VOLUME PROFILE</text>
<path d="{UP}" fill="none" stroke="#38BDF8" stroke-width="2"/>'''
    for y in range(12, 70, 5):
        vol_w = max(5, 40 - abs(y - 40)) + (15 if 35 <= y <= 50 else 0)
        s += f'<rect x="0" y="{y}" width="{vol_w}" height="4" fill="#38BDF8" opacity="0.08" rx="1"/>'
    s += '<text x="2" y="44" font-size="4" fill="#38BDF8" opacity="0.5">High volume node</text>'
    items.append(card("S-11", "Volume Profile (Horizontal)", "Shows where most trading happened — support/resistance levels", "#0F172A", s))

    # S-12: Bollinger / volatility envelope
    s = f'''<text x="4" y="10" font-size="7" fill="#14B8A6" font-weight="700">VOLATILITY ENVELOPE</text>
<path d="M0,55 C40,48 80,38 120,30 C160,35 200,40 240,32 C280,25 300,20" fill="none" stroke="#14B8A6" stroke-width="0.5" stroke-dasharray="3,2"/>
<path d="M0,68 C40,62 80,55 120,48 C160,50 200,52 240,45 C280,40 300,35" fill="none" stroke="#14B8A6" stroke-width="0.5" stroke-dasharray="3,2"/>
<path d="M0,55 C40,48 80,38 120,30 C160,35 200,40 240,32 C280,25 300,20 L300,35 C280,40 240,45 200,52 160,50 120,48 80,55 40,62 0,68Z" fill="#14B8A6" opacity="0.06"/>
<path d="M0,62 C40,55 80,46 120,38 C160,42 200,46 240,38 C280,32 300,28" fill="none" stroke="white" stroke-width="1.8"/>
<circle cx="160" cy="42" r="4" fill="#DC2626"/><text x="166" y="40" font-size="4" fill="#DC2626">Touch upper band</text>'''
    items.append(card("S-12", "Volatility Envelope", "2-sigma bands — price touching boundaries = volatility signal", "#0F172A", s))

    # ═══════════════════════════════════════
    # CARD-LEVEL INNOVATIONS
    # ═══════════════════════════════════════

    # I-01: Distress gauge cluster
    gauges = ""
    models = [("Altman Z","3.42","SAFE","#16A34A",85), ("Beneish M","-2.81","OK","#16A34A",70), ("Piotroski","7/9","STRONG","#16A34A",78), ("Ohlson O","0.12","SAFE","#16A34A",88)]
    for i, (name, val, zone, col, pct) in enumerate(models):
        cx = 55 + i * 105
        gauges += f'<path d="M{cx-30},55 A30,30 0 0,1 {cx+30},55" fill="none" stroke="#334155" stroke-width="6" stroke-linecap="round"/>'
        dash = pct / 100 * 94
        gauges += f'<path d="M{cx-30},55 A30,30 0 0,1 {cx+30},55" fill="none" stroke="{col}" stroke-width="6" stroke-linecap="round" stroke-dasharray="{dash} 94"/>'
        gauges += f'<text x="{cx}" y="50" text-anchor="middle" font-size="10" font-weight="900" fill="{col}">{val}</text>'
        gauges += f'<text x="{cx}" y="62" text-anchor="middle" font-size="5" fill="#94A3B8">{name}</text>'
        gauges += f'<text x="{cx}" y="70" text-anchor="middle" font-size="4" fill="{col}" font-weight="700">{zone}</text>'
    items.append(card("I-01", "Distress Gauge Cluster", "Card 21 — all 4 distress models as semicircle gauges, instant read", "#111827", gauges, w=460, h=75, full=True))

    # I-02: Beneish 8-component radar
    pts = "210,35 245,65 250,120 230,165 170,165 150,120 155,65"  # 7 spokes
    s = f'''<text x="4" y="12" font-size="7" fill="white" font-weight="700">BENEISH M-SCORE COMPONENT MAP</text>
<polygon points="210,20 260,55 265,130 235,180 185,180 155,130 160,55" fill="none" stroke="#334155" stroke-width="0.5"/>
<polygon points="210,50 240,70 245,120 230,155 190,155 175,120 180,70" fill="none" stroke="#334155" stroke-width="0.5"/>
<polygon points="{pts}" fill="#7C3AED" opacity="0.15" stroke="#7C3AED" stroke-width="1.5"/>
<text x="210" y="16" text-anchor="middle" font-size="5" fill="#94A3B8">DSRI</text>
<text x="268" y="55" font-size="5" fill="#94A3B8">GMI</text>
<text x="272" y="125" font-size="5" fill="#94A3B8">AQI</text>
<text x="240" y="188" font-size="5" fill="#94A3B8">SGI</text>
<text x="178" y="188" font-size="5" fill="#94A3B8">DEPI</text>
<text x="148" y="125" font-size="5" fill="#DC2626" font-weight="700">SGAI ⚠</text>
<text x="152" y="55" font-size="5" fill="#94A3B8">LVGI</text>
<text x="50" y="50" font-size="8" font-weight="800" fill="#16A34A">M = -2.81</text>
<text x="50" y="62" font-size="5" fill="#16A34A">Below -1.78 threshold</text>
<text x="50" y="74" font-size="5" fill="#6B7280">No manipulation indicated</text>
<rect x="40" y="85" width="80" height="14" rx="3" fill="#DC2626" opacity="0.1"/>
<text x="45" y="94" font-size="5" fill="#DC2626">⚠ SGAI elevated (1.24)</text>
<text x="45" y="106" font-size="4" fill="#6B7280">SG&A growing faster than revenue</text>'''
    items.append(card("I-02", "Beneish Component Radar", "Card 50 — radar showing which M-Score components are elevated vs threshold", "#0F172A", s, w=300, h=195))

    # I-03: Ownership flow (who entered/exited)
    s = f'''<text x="4" y="12" font-size="7" fill="white" font-weight="700">INSTITUTIONAL HOLDER CHANGES (90 DAYS)</text>
<text x="4" y="28" font-size="5" fill="#16A34A" font-weight="700">▲ NEW / INCREASED</text>'''
    enters = [("Vanguard Group","+2.1%","12.4%"),("BlackRock","+0.8%","9.2%"),("State Street","+0.3%","5.8%")]
    for i, (name, change, total) in enumerate(enters):
        y = 35 + i * 14
        s += f'<text x="10" y="{y}" font-size="6" fill="#D1FAE5">{name}</text>'
        s += f'<text x="180" y="{y}" font-size="6" fill="#16A34A" font-weight="700">{change}</text>'
        s += f'<rect x="210" y="{y-7}" width="{float(total.rstrip("%"))*4}" height="8" rx="2" fill="#16A34A" opacity="0.3"/>'
        s += f'<text x="{215+float(total.rstrip("%"))*4}" y="{y}" font-size="5" fill="#6B7280">{total}</text>'

    s += f'<line x1="0" y1="80" x2="300" y2="80" stroke="#334155" stroke-width="0.5"/>'
    s += f'<text x="4" y="92" font-size="5" fill="#DC2626" font-weight="700">▼ DECREASED / EXITED</text>'
    exits = [("Citadel Advisors","-100%","EXITED"),("Renaissance Tech","-45%","1.2%")]
    for i, (name, change, total) in enumerate(exits):
        y = 100 + i * 14
        s += f'<text x="10" y="{y}" font-size="6" fill="#FEE2E2">{name}</text>'
        s += f'<text x="180" y="{y}" font-size="6" fill="#DC2626" font-weight="700">{change}</text>'
        s += f'<text x="230" y="{y}" font-size="5" fill="#DC2626">{total}</text>'

    items.append(card("I-03", "Institutional Holder Flow", "Card 14 — who entered, who exited, position size bars. Exits = bearish signal.", "#0F172A", s, w=320, h=125))

    # I-04: Board skills heatmap
    s = f'<text x="4" y="12" font-size="7" fill="white" font-weight="700">BOARD SKILLS COVERAGE</text>'
    skills = ["Finance","Legal","Industry","Tech","Risk","ESG","M&A","Gov't"]
    directors = ["Smith","Jones","Lee","Chen","Davis"]
    for i, skill in enumerate(skills):
        s += f'<text x="{42+i*35}" y="26" text-anchor="middle" font-size="4" fill="#94A3B8" transform="rotate(-45 {42+i*35} 26)">{skill}</text>'
    for j, director in enumerate(directors):
        y = 38 + j * 16
        s += f'<text x="14" y="{y+8}" font-size="5" fill="#CBD5E1">{director}</text>'
        import random; random.seed(j*8+42)
        for i in range(8):
            has = random.random() > 0.4
            col = "#16A34A" if has else "#1E293B"
            s += f'<rect x="{28+i*35}" y="{y}" width="28" height="13" rx="2" fill="{col}" opacity="{0.6 if has else 0.3}"/>'
            if has:
                s += f'<text x="{42+i*35}" y="{y+9}" text-anchor="middle" font-size="5" fill="white">✓</text>'
    # Gap indicator
    s += f'<rect x="28" y="120" width="28" height="10" rx="2" fill="#DC2626" opacity="0.2"/><text x="62" y="128" font-size="4" fill="#DC2626">Gap: No Cybersecurity expertise on board</text>'
    items.append(card("I-04", "Board Skills Heatmap", "Card 22 — director × skill matrix. Green = has skill. Gaps highlighted red.", "#0F172A", s, w=320, h=135))

    # I-05: Exposed market cap concept
    s = f'''<text x="4" y="12" font-size="7" fill="white" font-weight="700">EXPOSED vs TOTAL MARKET CAP</text>
<rect x="20" y="25" width="280" height="30" rx="4" fill="#334155"/>
<rect x="20" y="25" width="275" height="30" rx="4" fill="#0369A1" opacity="0.7"/>
<text x="155" y="44" text-anchor="middle" font-size="8" fill="white" font-weight="800">Total: $12.5B</text>
<rect x="20" y="62" width="280" height="30" rx="4" fill="#334155"/>
<rect x="20" y="62" width="270" height="30" rx="4" fill="#D97706" opacity="0.7"/>
<text x="152" y="81" text-anchor="middle" font-size="8" fill="white" font-weight="800">Float (Exposed): $12.3B (98.6%)</text>
<text x="310" y="44" font-size="5" fill="#6B7280">Insider: 1.3%</text>
<text x="310" y="54" font-size="5" fill="#6B7280">Institutional: 83.7%</text>
<text x="310" y="81" font-size="5" fill="#D97706" font-weight="600">→ This is what plaintiffs claim on</text>
<text x="20" y="105" font-size="5" fill="#94A3B8">For small caps: $500M total with 60% insider = only $200M exposed = below plaintiff filing threshold</text>'''
    items.append(card("I-05", "Exposed Market Cap Bar", "Card 00/14 — total vs float-adjusted cap. Critical for small/mid caps.", "#0F172A", s, w=420, h=115, full=True))

    # I-06: Earnings surprise chart
    s = f'<text x="4" y="12" font-size="7" fill="white" font-weight="700">EARNINGS SURPRISE HISTORY</text>'
    quarters = [("Q1'24",0.05,3), ("Q2'24",0.08,4.2), ("Q3'24",-0.12,-8.1), ("Q4'24",0.03,1.5), ("Q1'25",0.06,2.8), ("Q2'25",0.02,0.8), ("Q3'25",-0.01,-0.3), ("Q4'25",0.04,2.1)]
    for i, (q, surprise, reaction) in enumerate(quarters):
        x = 20 + i * 50
        bar_h = abs(surprise) * 300
        col = "#16A34A" if surprise >= 0 else "#DC2626"
        y_base = 55
        y_top = y_base - bar_h if surprise >= 0 else y_base
        s += f'<rect x="{x}" y="{min(y_top, y_base)}" width="35" height="{max(bar_h, 2)}" rx="2" fill="{col}" opacity="0.7"/>'
        s += f'<text x="{x+17}" y="{y_base + (12 if surprise >= 0 else -bar_h-3)}" text-anchor="middle" font-size="5" fill="{col}" font-weight="700">{surprise:+.0%}</text>'
        # Reaction dot
        react_y = 75 - reaction * 3
        react_col = "#16A34A" if reaction >= 0 else "#DC2626"
        s += f'<circle cx="{x+17}" cy="{react_y}" r="3" fill="{react_col}"/>'
        s += f'<text x="{x+17}" y="95" text-anchor="middle" font-size="4" fill="#6B7280">{q}</text>'
    s += f'<line x1="15" y1="55" x2="420" y2="55" stroke="#334155" stroke-width="0.5"/>'
    s += f'<text x="422" y="45" font-size="4" fill="#16A34A">Surprise</text>'
    s += f'<text x="422" y="78" font-size="4" fill="#6B7280">Reaction</text>'
    items.append(card("I-06", "Earnings Surprise + Reaction", "Card 16 — bar = EPS surprise, dot = stock reaction. Miss+drop = SCA trigger.", "#0F172A", s, w=460, h=100, full=True))

    # I-07: Litigation case severity timeline
    s = f'''<text x="4" y="12" font-size="7" fill="white" font-weight="700">LITIGATION TIMELINE — SEVERITY WEIGHTED</text>
<line x1="30" y1="40" x2="390" y2="40" stroke="#334155" stroke-width="1"/>'''
    cases = [(50,"2018","Settled $4.2M","#F59E0B",8), (120,"2019","Dismissed","#16A34A",6), (190,"2021","Settled $12.8M","#DC2626",14), (260,"2023","SEC Action","#7C3AED",10), (330,"2025","Active SCA","#DC2626",16)]
    for x, year, label, col, size in cases:
        s += f'<circle cx="{x}" cy="40" r="{size/2+2}" fill="{col}" opacity="0.2"/>'
        s += f'<circle cx="{x}" cy="40" r="{size/3+1}" fill="{col}"/>'
        s += f'<text x="{x}" y="58" text-anchor="middle" font-size="4" fill="#94A3B8">{year}</text>'
        s += f'<text x="{x}" y="66" text-anchor="middle" font-size="4" fill="{col}">{label}</text>'
    s += '<text x="30" y="80" font-size="4" fill="#6B7280">Circle size = settlement/exposure magnitude. Chronic filer pattern visible.</text>'
    items.append(card("I-07", "Litigation Severity Timeline", "Card 35 — cases as bubbles sized by settlement. Pattern = chronic filer.", "#0F172A", s, w=420, h=85, full=True))

    # Build HTML
    html = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Ideas Gallery — New Visualizations for Cards</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,sans-serif;background:#0A0A0A;color:#E2E8F0;padding:16px}
h1{font-size:22px;font-weight:900;text-align:center;color:white}
.sub{font-size:11px;color:#6B7280;text-align:center;margin:4px 0 20px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.sep{grid-column:1/-1;padding:16px 0 4px;display:flex;align-items:center;gap:10px}
.sep-n{font-size:20px;font-weight:900;opacity:0.2;color:#D4A843}
.sep-t{font-size:14px;font-weight:800;color:white}
.sep-l{flex:1;height:1px;background:#D4A843;opacity:0.15}
.sep-c{font-size:8px;color:#6B7280}
.footer{text-align:center;margin-top:20px;font-size:9px;color:#4B5563}
</style></head><body>
<h1>New Visualization Ideas</h1>
<div class="sub">Stock chart variations + card-level innovations — all rendered, reference by ID</div>
<div class="grid">

<div class="sep"><div class="sep-n">S</div><div class="sep-t">Stock Chart Variations</div><div class="sep-l"></div><div class="sep-c">12 options</div></div>
'''

    for item in items[:12]:
        html += item

    html += '''
<div class="sep"><div class="sep-n">I</div><div class="sep-t">Card-Level Innovations</div><div class="sep-l"></div><div class="sep-c">7 concepts</div></div>
'''

    for item in items[12:]:
        html += item

    html += '''
</div>
<div class="footer">19 new visualization concepts — S-01 through S-12 (stock charts) + I-01 through I-07 (card innovations)</div>
</body></html>'''

    return html


if __name__ == "__main__":
    html = build()
    Path("output/IDEAS_GALLERY.html").write_text(html)
    print(f"Generated: output/IDEAS_GALLERY.html ({len(html):,} chars)")
