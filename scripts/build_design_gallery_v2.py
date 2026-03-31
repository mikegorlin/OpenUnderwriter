#!/usr/bin/env python3
"""Design Gallery v2 — Massive visual library with chart styles, infographics, compositions."""

from pathlib import Path

def build():
    return '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>D&O Design Gallery v2</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#F8FAFC;color:#1E293B}
.hero{text-align:center;padding:28px 24px 18px;background:white;border-bottom:1px solid #E2E8F0}
.hero h1{font-size:22px;font-weight:900}
.hero .sub{font-size:11px;color:#64748B;margin-top:3px}
.nav{position:sticky;top:0;z-index:100;background:white;border-bottom:2px solid #E2E8F0;padding:6px 16px;display:flex;flex-wrap:wrap;gap:4px;justify-content:center}
.nav a{font-size:9px;font-weight:700;padding:4px 10px;border-radius:5px;text-decoration:none;color:white}
.g{max-width:1200px;margin:0 auto;padding:12px}
.gh{display:flex;align-items:center;gap:10px;margin:24px 0 10px}
.gn{font-size:24px;font-weight:900;opacity:0.12}
.gt{font-size:15px;font-weight:800}
.gl{flex:1;height:2px;opacity:0.12;border-radius:1px}
.gc{font-size:9px;color:#94A3B8}
.item{background:white;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:10px;overflow:hidden}
.ih{padding:8px 12px;border-bottom:1px solid #F1F5F9;display:flex;align-items:center;gap:6px}
.in{font-size:10px;font-weight:800;font-family:'JetBrains Mono',monospace;flex:1}
.id{font-size:8px;color:#64748B}
.ii{font-size:7px;color:#94A3B8;font-style:italic}
.demo{padding:12px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:flex-start}
.c2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.c3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.c4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px}
.c6{display:grid;grid-template-columns:repeat(6,1fr);gap:4px}
.full{width:100%}
.half{width:calc(50% - 3px)}
.label{font-size:7px;color:#94A3B8;margin-top:4px;text-align:center}
.sep{border-top:1px solid #F1F5F9;margin:6px 0}
.footer{text-align:center;padding:24px;color:#94A3B8;font-size:9px;border-top:1px solid #E2E8F0;margin-top:20px;background:white}
</style></head><body>

<div class="hero"><h1>Design Gallery v2</h1><div class="sub">Charts · Infographics · Compositions · Layout Options — pick what works</div></div>

<div class="nav">
<a href="#chart-lines" style="background:#0F172A">Line Charts</a>
<a href="#chart-bars" style="background:#DC2626">Bar Charts</a>
<a href="#chart-special" style="background:#7C3AED">Special Charts</a>
<a href="#chart-layouts" style="background:#EA580C">Chart Layouts</a>
<a href="#chart-themes" style="background:#059669">Color Themes</a>
<a href="#infographics" style="background:#1D4ED8">Infographics</a>
<a href="#gauges" style="background:#D97706">Gauges & Meters</a>
<a href="#heatmaps" style="background:#BE185D">Heat Maps</a>
<a href="#compositions" style="background:#0891B2">Card Compositions</a>
<a href="#strips" style="background:#64748B">Compact Strips</a>
</div>

<div class="g">

<!-- ═══════════════════════════════════════ -->
<!-- LINE CHARTS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="chart-lines"><div class="gn" style="color:#0F172A">01</div><div class="gt">Line Charts</div><div class="gl" style="background:#0F172A"></div><div class="gc">8 styles</div></div>

<div class="item"><div class="ih"><div class="in">Line-Dark-Glow</div><div class="id">Price chart with glow effect on dark bg</div><div class="ii">Bloomberg terminal</div></div>
<div class="demo">
<div class="c2">
<div style="background:#1A1A2E;border-radius:6px;padding:10px 12px;height:120px;position:relative">
  <div style="font-size:7px;font-weight:700;color:#D4A843;letter-spacing:0.5px">RPM — 2Y PERFORMANCE</div>
  <svg width="100%" height="80" viewBox="0 0 300 80" style="margin-top:4px">
    <path d="M0,60 C30,55 60,50 90,45 C120,40 150,50 180,55 C210,60 240,35 270,25 C280,22 290,20 300,18" fill="none" stroke="#E8903A" stroke-width="4" opacity="0.15"/>
    <path d="M0,60 C30,55 60,50 90,45 C120,40 150,50 180,55 C210,60 240,35 270,25 C280,22 290,20 300,18" fill="none" stroke="#E8903A" stroke-width="2"/>
    <path d="M0,65 C30,62 60,60 90,58 C120,56 150,57 180,58 C210,59 240,52 270,48 C290,45 300,43" fill="none" stroke="#6B7280" stroke-width="1" stroke-dasharray="4,3" opacity="0.5"/>
    <circle cx="180" cy="55" r="7" fill="#DC2626" opacity="0.9"/><text x="180" y="58" text-anchor="middle" fill="white" font-size="6" font-weight="700">1</text>
  </svg>
</div>
<div style="background:#1A1A2E;border-radius:6px;padding:10px 12px;height:120px">
  <div style="font-size:7px;font-weight:700;color:#38BDF8;letter-spacing:0.5px">AAPL — 5Y WEEKLY</div>
  <svg width="100%" height="80" viewBox="0 0 300 80" style="margin-top:4px">
    <path d="M0,70 C40,65 80,55 120,40 C160,30 200,25 240,15 C260,12 280,10 300,8" fill="none" stroke="#38BDF8" stroke-width="2"/>
    <path d="M0,70 C40,65 80,55 120,40 C160,30 200,25 240,15 C260,12 280,10 300,8 L300,80 L0,80Z" fill="#38BDF8" opacity="0.06"/>
  </svg>
</div>
</div>
<div class="label">Left: Orange glow + sector overlay + drop markers · Right: Slate blue area fill</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Line-Light-Clean</div><div class="id">Price chart on white/light bg</div><div class="ii">WSJ / Economist</div></div>
<div class="demo">
<div class="c2">
<div style="background:white;border:1px solid #E2E8F0;border-radius:6px;padding:10px 12px;height:120px">
  <div style="font-size:7px;font-weight:700;color:#1F3A5C;letter-spacing:0.3px">Stock Price — 1 Year</div>
  <svg width="100%" height="80" viewBox="0 0 300 80" style="margin-top:4px">
    <line x1="0" y1="80" x2="300" y2="80" stroke="#F1F5F9" stroke-width="1"/>
    <line x1="0" y1="60" x2="300" y2="60" stroke="#F1F5F9" stroke-width="0.5"/>
    <line x1="0" y1="40" x2="300" y2="40" stroke="#F1F5F9" stroke-width="0.5"/>
    <line x1="0" y1="20" x2="300" y2="20" stroke="#F1F5F9" stroke-width="0.5"/>
    <path d="M0,55 C40,50 80,45 120,35 C160,30 200,38 240,42 C260,40 280,35 300,30" fill="none" stroke="#0369A1" stroke-width="1.8"/>
    <path d="M0,55 C40,50 80,45 120,35 C160,30 200,38 240,42 C260,40 280,35 300,30 L300,80 L0,80Z" fill="#0369A1" opacity="0.05"/>
    <text x="4" y="58" font-size="5" fill="#94A3B8">$89</text>
    <text x="4" y="33" font-size="5" fill="#94A3B8">$142</text>
  </svg>
</div>
<div style="background:#FAFBFC;border:1px solid #E2E8F0;border-radius:6px;padding:10px 12px;height:120px">
  <div style="font-size:7px;font-weight:700;color:#374151;letter-spacing:0.3px">Revenue Trend — 5 Years ($B)</div>
  <svg width="100%" height="80" viewBox="0 0 300 80" style="margin-top:4px">
    <rect x="0" y="0" width="300" height="80" fill="#FAFBFC"/>
    <line x1="0" y1="80" x2="300" y2="80" stroke="#E2E8F0" stroke-width="1"/>
    <path d="M0,65 L60,55 L120,48 L180,40 L240,35 L300,28" fill="none" stroke="#16A34A" stroke-width="2"/>
    <circle cx="0" cy="65" r="3" fill="#16A34A"/><circle cx="60" cy="55" r="3" fill="#16A34A"/><circle cx="120" cy="48" r="3" fill="#16A34A"/><circle cx="180" cy="40" r="3" fill="#16A34A"/><circle cx="240" cy="35" r="3" fill="#16A34A"/><circle cx="300" cy="28" r="3" fill="#16A34A"/>
    <text x="0" y="75" font-size="5" fill="#94A3B8">2020</text><text x="60" y="75" font-size="5" fill="#94A3B8">2021</text><text x="120" y="75" font-size="5" fill="#94A3B8">2022</text><text x="180" y="75" font-size="5" fill="#94A3B8">2023</text><text x="240" y="75" font-size="5" fill="#94A3B8">2024</text><text x="290" y="75" font-size="5" fill="#94A3B8">2025</text>
  </svg>
</div>
</div>
<div class="label">Left: Blue line with subtle area fill · Right: Green with data points (Economist style)</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Line-Multi-Indexed</div><div class="id">Multiple series indexed to 100</div><div class="ii">WSJ performance comparison</div></div>
<div class="demo">
<div style="background:white;border:1px solid #E2E8F0;border-radius:6px;padding:10px 12px;height:130px">
  <div style="font-size:7px;font-weight:700;color:#374151">Relative Performance — Indexed to 100</div>
  <div style="display:flex;gap:12px;margin-top:3px;font-size:6px">
    <span><span style="display:inline-block;width:12px;height:2px;background:#0369A1;vertical-align:middle;margin-right:2px"></span> Company</span>
    <span><span style="display:inline-block;width:12px;height:2px;background:#D97706;vertical-align:middle;margin-right:2px;border-bottom:1px dashed #D97706"></span> Sector ETF</span>
    <span><span style="display:inline-block;width:12px;height:2px;background:#6B7280;vertical-align:middle;margin-right:2px;border-bottom:1px dotted #6B7280"></span> S&P 500</span>
  </div>
  <svg width="100%" height="85" viewBox="0 0 300 85" style="margin-top:4px">
    <line x1="0" y1="42" x2="300" y2="42" stroke="#E2E8F0" stroke-width="0.5" stroke-dasharray="2,2"/>
    <text x="302" y="44" font-size="5" fill="#94A3B8">100</text>
    <path d="M0,42 C40,38 80,30 120,22 C160,18 200,15 240,10 C270,8 300,5" fill="none" stroke="#0369A1" stroke-width="1.8"/>
    <path d="M0,42 C40,40 80,36 120,32 C160,30 200,28 240,24 C270,22 300,20" fill="none" stroke="#D97706" stroke-width="1.2" stroke-dasharray="4,2"/>
    <path d="M0,42 C40,41 80,38 120,35 C160,33 200,31 240,28 C270,26 300,25" fill="none" stroke="#6B7280" stroke-width="1" stroke-dasharray="2,2"/>
    <rect x="0" y="5" width="300" height="37" fill="#16A34A" opacity="0.03"/>
    <rect x="0" y="42" width="300" height="43" fill="#DC2626" opacity="0.03"/>
  </svg>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Sparkline-Variants</div><div class="id">Inline micro-charts in 6 styles</div><div class="ii">Tufte</div></div>
<div class="demo">
<div style="display:flex;flex-direction:column;gap:10px">
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Area (up)</span><svg width="80" height="20" viewBox="0 0 80 20"><path d="M0,18 L13,15 L26,12 L40,10 L53,7 L66,4 L80,2" fill="none" stroke="#16A34A" stroke-width="1.5"/><path d="M0,18 L13,15 L26,12 L40,10 L53,7 L66,4 L80,2 L80,20 L0,20Z" fill="#16A34A" opacity="0.12"/></svg><span style="font-size:9px;font-weight:700;color:#16A34A">+23.4%</span></div>
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Area (down)</span><svg width="80" height="20" viewBox="0 0 80 20"><path d="M0,4 L13,6 L26,8 L40,10 L53,13 L66,15 L80,17" fill="none" stroke="#DC2626" stroke-width="1.5"/><path d="M0,4 L13,6 L26,8 L40,10 L53,13 L66,15 L80,17 L80,20 L0,20Z" fill="#DC2626" opacity="0.12"/></svg><span style="font-size:9px;font-weight:700;color:#DC2626">-18.7%</span></div>
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Bar (quarterly)</span><svg width="80" height="20" viewBox="0 0 80 20"><rect x="2" y="8" width="8" height="12" rx="1" fill="#16A34A"/><rect x="12" y="5" width="8" height="15" rx="1" fill="#16A34A"/><rect x="22" y="10" width="8" height="10" rx="1" fill="#DC2626"/><rect x="32" y="3" width="8" height="17" rx="1" fill="#16A34A"/><rect x="42" y="6" width="8" height="14" rx="1" fill="#16A34A"/><rect x="52" y="4" width="8" height="16" rx="1" fill="#16A34A"/><rect x="62" y="12" width="8" height="8" rx="1" fill="#DC2626"/><rect x="72" y="2" width="8" height="18" rx="1" fill="#16A34A"/></svg><span style="font-size:9px;font-weight:700">6/8 beats</span></div>
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Dot strip</span><svg width="80" height="20" viewBox="0 0 80 20"><circle cx="5" cy="10" r="3" fill="#16A34A"/><circle cx="16" cy="10" r="3" fill="#16A34A"/><circle cx="27" cy="10" r="3" fill="#DC2626"/><circle cx="38" cy="10" r="3" fill="#16A34A"/><circle cx="49" cy="10" r="3" fill="#16A34A"/><circle cx="60" cy="10" r="3" fill="#16A34A"/><circle cx="71" cy="10" r="3" fill="#D97706"/><circle cx="80" cy="10" r="3" fill="#16A34A"/></svg></div>
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Win/loss</span><svg width="80" height="20" viewBox="0 0 80 20"><rect x="2" y="2" width="8" height="8" rx="1" fill="#16A34A"/><rect x="12" y="2" width="8" height="8" rx="1" fill="#16A34A"/><rect x="22" y="10" width="8" height="8" rx="1" fill="#DC2626"/><rect x="32" y="2" width="8" height="8" rx="1" fill="#16A34A"/><rect x="42" y="2" width="8" height="8" rx="1" fill="#16A34A"/><rect x="52" y="2" width="8" height="8" rx="1" fill="#16A34A"/><rect x="62" y="10" width="8" height="8" rx="1" fill="#DC2626"/><rect x="72" y="2" width="8" height="8" rx="1" fill="#16A34A"/></svg></div>
  <div style="display:flex;align-items:center;gap:8px"><span style="font-size:8px;color:#64748B;width:100px">Bullet range</span><svg width="80" height="20" viewBox="0 0 80 20"><rect x="0" y="6" width="80" height="8" rx="2" fill="#E5E7EB"/><rect x="0" y="6" width="55" height="8" rx="2" fill="#BFDBFE"/><rect x="0" y="8" width="42" height="4" rx="1" fill="#1D4ED8"/><line x1="60" y1="4" x2="60" y2="16" stroke="#0F172A" stroke-width="1.5"/></svg><span style="font-size:7px;color:#64748B">42 vs target 60</span></div>
</div>
</div></div>

<!-- ═══════════════════════════════════════ -->
<!-- BAR CHARTS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="chart-bars"><div class="gn" style="color:#DC2626">02</div><div class="gt">Bar Charts</div><div class="gl" style="background:#DC2626"></div><div class="gc">8 styles</div></div>

<div class="item"><div class="ih"><div class="in">Bar-Vertical-Grouped</div><div class="id">Side-by-side comparison bars</div><div class="ii">Economist</div></div>
<div class="demo"><div class="c2">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
  <div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Revenue by Segment ($M)</div>
  <svg width="100%" height="80" viewBox="0 0 200 80">
    <rect x="10" y="10" width="25" height="65" rx="2" fill="#0369A1"/><rect x="40" y="25" width="25" height="50" rx="2" fill="#0369A1" opacity="0.6"/>
    <rect x="80" y="20" width="25" height="55" rx="2" fill="#0369A1"/><rect x="110" y="30" width="25" height="45" rx="2" fill="#0369A1" opacity="0.6"/>
    <rect x="150" y="40" width="25" height="35" rx="2" fill="#0369A1"/><rect x="180" y="45" width="25" height="30" rx="2" fill="#0369A1" opacity="0.6"/>
    <text x="35" y="78" text-anchor="middle" font-size="5" fill="#94A3B8">Consumer</text>
    <text x="105" y="78" text-anchor="middle" font-size="5" fill="#94A3B8">Performance</text>
    <text x="175" y="78" text-anchor="middle" font-size="5" fill="#94A3B8">Specialty</text>
  </svg>
  <div style="font-size:6px;color:#94A3B8">Dark = FY2025, Light = FY2024</div>
</div>
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
  <div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Debt Maturity Schedule</div>
  <svg width="100%" height="80" viewBox="0 0 200 80">
    <rect x="5" y="15" width="22" height="60" rx="2" fill="#DC2626"/><text x="16" y="12" text-anchor="middle" font-size="5" fill="#DC2626" font-weight="700">$1.2B</text>
    <rect x="32" y="30" width="22" height="45" rx="2" fill="#DC2626" opacity="0.7"/>
    <rect x="59" y="45" width="22" height="30" rx="2" fill="#3B82F6"/>
    <rect x="86" y="50" width="22" height="25" rx="2" fill="#3B82F6"/>
    <rect x="113" y="55" width="22" height="20" rx="2" fill="#3B82F6"/>
    <rect x="140" y="60" width="22" height="15" rx="2" fill="#3B82F6"/>
    <rect x="167" y="65" width="22" height="10" rx="2" fill="#3B82F6"/>
    <text x="16" y="80" text-anchor="middle" font-size="4.5" fill="#94A3B8">2025</text><text x="43" y="80" text-anchor="middle" font-size="4.5" fill="#94A3B8">2026</text><text x="70" y="80" text-anchor="middle" font-size="4.5" fill="#94A3B8">2027</text><text x="97" y="80" text-anchor="middle" font-size="4.5" fill="#94A3B8">2028</text><text x="124" y="80" text-anchor="middle" font-size="4.5" fill="#94A3B8">2029</text>
  </svg>
  <div style="font-size:6px;color:#94A3B8"><span style="color:#DC2626">■</span> Near-term (<2yr) <span style="color:#3B82F6;margin-left:8px">■</span> Future</div>
</div>
</div></div></div>

<div class="item"><div class="ih"><div class="in">Bar-Horizontal-Labeled</div><div class="id">Factor bars, scoring, rankings</div><div class="ii">McKinsey</div></div>
<div class="demo">
<div class="c2">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
  <div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">10-Factor Scoring</div>
  <div style="display:flex;flex-direction:column;gap:3px">
    <div style="display:flex;align-items:center;gap:4px;font-size:8px"><span style="width:70px;color:#64748B">Litigation</span><div style="flex:1;height:8px;background:#E5E7EB;border-radius:4px"><div style="width:85%;height:8px;background:#DC2626;border-radius:4px"></div></div><span style="width:24px;font-weight:700;text-align:right;font-size:7px">13/15</span></div>
    <div style="display:flex;align-items:center;gap:4px;font-size:8px"><span style="width:70px;color:#64748B">Financial</span><div style="flex:1;height:8px;background:#E5E7EB;border-radius:4px"><div style="width:60%;height:8px;background:#D97706;border-radius:4px"></div></div><span style="width:24px;font-weight:700;text-align:right;font-size:7px">9/15</span></div>
    <div style="display:flex;align-items:center;gap:4px;font-size:8px"><span style="width:70px;color:#64748B">Governance</span><div style="flex:1;height:8px;background:#E5E7EB;border-radius:4px"><div style="width:30%;height:8px;background:#16A34A;border-radius:4px"></div></div><span style="width:24px;font-weight:700;text-align:right;font-size:7px">3/10</span></div>
    <div style="display:flex;align-items:center;gap:4px;font-size:8px"><span style="width:70px;color:#64748B">Stock</span><div style="flex:1;height:8px;background:#E5E7EB;border-radius:4px"><div style="width:45%;height:8px;background:#D97706;border-radius:4px"></div></div><span style="width:24px;font-weight:700;text-align:right;font-size:7px">7/15</span></div>
    <div style="display:flex;align-items:center;gap:4px;font-size:8px"><span style="width:70px;color:#64748B">Insider</span><div style="flex:1;height:8px;background:#E5E7EB;border-radius:4px"><div style="width:10%;height:8px;background:#16A34A;border-radius:4px"></div></div><span style="width:24px;font-weight:700;text-align:right;font-size:7px">1/10</span></div>
  </div>
</div>
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
  <div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Tornado — Sensitivity</div>
  <div style="display:flex;flex-direction:column;gap:3px">
    <div style="display:flex;align-items:center;gap:0;font-size:7px"><span style="width:60px;text-align:right;color:#64748B;padding-right:4px">Revenue</span><div style="width:30px;height:8px;background:#DC2626;border-radius:2px 0 0 2px;margin-left:auto"></div><div style="width:1px;background:#374151;height:14px"></div><div style="width:50px;height:8px;background:#16A34A;border-radius:0 2px 2px 0"></div><span style="width:40px"></span></div>
    <div style="display:flex;align-items:center;gap:0;font-size:7px"><span style="width:60px;text-align:right;color:#64748B;padding-right:4px">Margin</span><div style="width:45px;height:8px;background:#DC2626;border-radius:2px 0 0 2px;margin-left:auto"></div><div style="width:1px;background:#374151;height:14px"></div><div style="width:20px;height:8px;background:#16A34A;border-radius:0 2px 2px 0"></div><span style="width:40px"></span></div>
    <div style="display:flex;align-items:center;gap:0;font-size:7px"><span style="width:60px;text-align:right;color:#64748B;padding-right:4px">Stock Drop</span><div style="width:60px;height:8px;background:#DC2626;border-radius:2px 0 0 2px;margin-left:auto"></div><div style="width:1px;background:#374151;height:14px"></div><div style="width:10px;height:8px;background:#16A34A;border-radius:0 2px 2px 0"></div><span style="width:40px"></span></div>
    <div style="display:flex;align-items:center;gap:0;font-size:7px"><span style="width:60px;text-align:right;color:#64748B;padding-right:4px">Governance</span><div style="width:15px;height:8px;background:#DC2626;border-radius:2px 0 0 2px;margin-left:auto"></div><div style="width:1px;background:#374151;height:14px"></div><div style="width:35px;height:8px;background:#16A34A;border-radius:0 2px 2px 0"></div><span style="width:40px"></span></div>
  </div>
</div>
</div></div></div>

<div class="item"><div class="ih"><div class="in">Bar-Waterfall</div><div class="id">Stacking deductions from 100</div><div class="ii">McKinsey</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
<svg width="100%" height="100" viewBox="0 0 400 100">
  <rect x="10" y="5" width="35" height="85" rx="3" fill="#16A34A"/><text x="27" y="96" text-anchor="middle" font-size="5" fill="#64748B">100</text><text x="27" y="15" text-anchor="middle" font-size="5" fill="white" font-weight="700">Start</text>
  <rect x="55" y="5" width="35" height="12" rx="2" fill="#DC2626"/><text x="72" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F1 -3</text>
  <rect x="100" y="17" width="35" height="20" rx="2" fill="#DC2626"/><text x="117" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F2 -5</text>
  <rect x="145" y="37" width="35" height="4" rx="2" fill="#D97706"/><text x="162" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F3 -1</text>
  <rect x="190" y="41" width="35" height="0" rx="2" fill="#E5E7EB"/><text x="207" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F4 0</text>
  <rect x="235" y="41" width="35" height="8" rx="2" fill="#DC2626"/><text x="252" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F5 -2</text>
  <rect x="280" y="49" width="35" height="4" rx="2" fill="#D97706"/><text x="297" y="96" font-size="4.5" text-anchor="middle" fill="#64748B">F6 -1</text>
  <line x1="325" y1="0" x2="325" y2="90" stroke="#E2E8F0" stroke-width="0.5" stroke-dasharray="2,2"/>
  <rect x="335" y="5" width="50" height="48" rx="3" fill="#16A34A"/><text x="360" y="96" text-anchor="middle" font-size="5" fill="#64748B">Score</text><text x="360" y="25" text-anchor="middle" font-size="8" fill="white" font-weight="800">88</text><text x="360" y="35" text-anchor="middle" font-size="5" fill="white" opacity="0.7">WIN</text>
  <line x1="0" y1="38" x2="330" y2="38" stroke="#D97706" stroke-width="0.5" stroke-dasharray="3,3"/><text x="332" y="37" font-size="4" fill="#D97706">WRITE threshold</text>
</svg>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Bar-Stacked-Composition</div><div class="id">Segment/category breakdown</div><div class="ii">Economist stacked bars</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Revenue Mix by Segment</div>
<div style="display:flex;height:24px;border-radius:4px;overflow:hidden;margin-bottom:4px">
  <div style="width:38%;background:#0369A1;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">Consumer 38%</div>
  <div style="width:28%;background:#0891B2;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">Performance 28%</div>
  <div style="width:20%;background:#7C3AED;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">Specialty 20%</div>
  <div style="width:14%;background:#D97706;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">Other 14%</div>
</div>
<div style="font-size:7px;font-weight:700;color:#374151;margin:10px 0 6px">D&O Tier Distribution — Industrials</div>
<div style="display:flex;height:20px;border-radius:4px;overflow:hidden">
  <div style="width:15%;background:#16A34A;display:flex;align-items:center;justify-content:center;font-size:5px;color:white;font-weight:700">PREF 15%</div>
  <div style="width:35%;background:#059669;display:flex;align-items:center;justify-content:center;font-size:5px;color:white;font-weight:700">STANDARD 35%</div>
  <div style="width:25%;background:#D97706;display:flex;align-items:center;justify-content:center;font-size:5px;color:white;font-weight:700">ELEVATED 25%</div>
  <div style="width:18%;background:#DC2626;display:flex;align-items:center;justify-content:center;font-size:5px;color:white;font-weight:700">HIGH 18%</div>
  <div style="width:7%;background:#991B1B;display:flex;align-items:center;justify-content:center;font-size:5px;color:white;font-weight:700">X 7%</div>
</div>
</div>
</div></div>

<!-- ═══════════════════════════════════════ -->
<!-- SPECIAL CHARTS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="chart-special"><div class="gn" style="color:#7C3AED">03</div><div class="gt">Special Charts</div><div class="gl" style="background:#7C3AED"></div><div class="gc">6 styles</div></div>

<div class="item"><div class="ih"><div class="in">Radar-Spider</div><div class="id">Multi-axis risk profile</div><div class="ii">Economist radars</div></div>
<div class="demo"><div class="c2">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px;text-align:center">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:4px">Risk Profile — Dark Theme</div>
<svg width="180" height="180" viewBox="0 0 200 200">
  <polygon points="100,20 168,52 188,120 148,172 52,172 12,120 32,52" fill="none" stroke="#334155" stroke-width="0.5"/>
  <polygon points="100,45 150,65 165,115 138,152 62,152 35,115 50,65" fill="none" stroke="#334155" stroke-width="0.5"/>
  <polygon points="100,70 132,80 142,110 128,132 72,132 58,110 68,80" fill="none" stroke="#334155" stroke-width="0.5"/>
  <polygon points="100,30 155,56 172,115 142,165 58,165 28,115 45,56" fill="#0F172A" opacity="0.2" stroke="#D4A843" stroke-width="1.5"/>
  <text x="100" y="14" text-anchor="middle" font-size="6" fill="#64748B">Litigation</text>
  <text x="174" y="50" font-size="6" fill="#64748B">Stock</text>
  <text x="194" y="122" font-size="6" fill="#64748B">Financial</text>
  <text x="152" y="180" font-size="6" fill="#64748B">Governance</text>
  <text x="48" y="180" font-size="6" fill="#64748B">Regulatory</text>
  <text x="6" y="122" font-size="6" fill="#64748B">Insider</text>
  <text x="26" y="50" font-size="6" fill="#64748B">Volatility</text>
</svg>
</div>
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px;text-align:center">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:4px">Risk Profile — Light Theme</div>
<svg width="180" height="180" viewBox="0 0 200 200">
  <polygon points="100,20 168,52 188,120 148,172 52,172 12,120 32,52" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,45 150,65 165,115 138,152 62,152 35,115 50,65" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,70 132,80 142,110 128,132 72,132 58,110 68,80" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,35 148,58 168,118 140,162 60,162 32,118 52,58" fill="#0369A1" opacity="0.12" stroke="#0369A1" stroke-width="1.5"/>
  <circle cx="100" cy="35" r="3" fill="#0369A1"/><circle cx="148" cy="58" r="3" fill="#0369A1"/><circle cx="168" cy="118" r="3" fill="#0369A1"/><circle cx="140" cy="162" r="3" fill="#0369A1"/><circle cx="60" cy="162" r="3" fill="#0369A1"/><circle cx="32" cy="118" r="3" fill="#0369A1"/><circle cx="52" cy="58" r="3" fill="#0369A1"/>
</svg>
</div>
</div></div></div>

<div class="item"><div class="ih"><div class="in">Donut-Ring</div><div class="id">Ownership, composition breakdowns</div><div class="ii">Capital IQ</div></div>
<div class="demo"><div class="c3">
<div style="text-align:center;border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:4px">Ownership</div>
<svg width="80" height="80" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="35" fill="none" stroke="#E2E8F0" stroke-width="12"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#0F172A" stroke-width="12" stroke-dasharray="154 66" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#D4A843" stroke-width="12" stroke-dasharray="44 176" stroke-dashoffset="-154" transform="rotate(-90 50 50)"/>
  <text x="50" y="48" text-anchor="middle" font-size="12" font-weight="800" fill="#0F172A">70%</text>
  <text x="50" y="58" text-anchor="middle" font-size="5" fill="#94A3B8">Institutional</text>
</svg>
</div>
<div style="text-align:center;border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:4px">Board Independence</div>
<svg width="80" height="80" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="35" fill="none" stroke="#E2E8F0" stroke-width="10"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#16A34A" stroke-width="10" stroke-dasharray="176 44" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
  <text x="50" y="48" text-anchor="middle" font-size="14" font-weight="800" fill="#16A34A">80%</text>
  <text x="50" y="58" text-anchor="middle" font-size="5" fill="#94A3B8">Independent</text>
</svg>
</div>
<div style="text-align:center;border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:4px">Cash vs Debt</div>
<svg width="80" height="80" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="35" fill="none" stroke="#DC2626" stroke-width="12"/>
  <circle cx="50" cy="50" r="35" fill="none" stroke="#16A34A" stroke-width="12" stroke-dasharray="44 176" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
  <text x="50" y="48" text-anchor="middle" font-size="10" font-weight="800" fill="#DC2626">86%</text>
  <text x="50" y="58" text-anchor="middle" font-size="5" fill="#94A3B8">Debt</text>
</svg>
</div>
</div></div></div>

<!-- ═══════════════════════════════════════ -->
<!-- GAUGES & METERS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="gauges"><div class="gn" style="color:#D97706">04</div><div class="gt">Gauges, Meters & Scales</div><div class="gl" style="background:#D97706"></div><div class="gc">8 styles</div></div>

<div class="item"><div class="ih"><div class="in">Gauge-Semicircle + Scales</div><div class="id">Score gauges and graded scales</div></div>
<div class="demo"><div class="c4">
<div style="text-align:center;border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:6px;font-weight:700;color:#64748B;margin-bottom:2px">Quality Score</div>
<svg width="80" height="50" viewBox="0 0 100 55">
  <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="#E5E7EB" stroke-width="8" stroke-linecap="round"/>
  <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="url(#gauge-grad)" stroke-width="8" stroke-linecap="round" stroke-dasharray="126" stroke-dashoffset="12.6"/>
  <defs><linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#DC2626"/><stop offset="50%" stop-color="#D97706"/><stop offset="100%" stop-color="#16A34A"/></linearGradient></defs>
  <text x="50" y="45" text-anchor="middle" font-size="16" font-weight="900" fill="#16A34A">91</text>
  <text x="50" y="54" text-anchor="middle" font-size="5" fill="#94A3B8">WIN</text>
</svg>
</div>
<div style="text-align:center;border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:6px;font-weight:700;color:#64748B;margin-bottom:2px">CEO Pay Ratio</div>
<svg width="80" height="50" viewBox="0 0 100 55">
  <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="#E5E7EB" stroke-width="8" stroke-linecap="round"/>
  <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="#D97706" stroke-width="8" stroke-linecap="round" stroke-dasharray="126" stroke-dashoffset="50"/>
  <text x="50" y="42" text-anchor="middle" font-size="12" font-weight="900" fill="#D97706">187:1</text>
  <text x="50" y="54" text-anchor="middle" font-size="5" fill="#94A3B8">vs median 150:1</text>
</svg>
</div>
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:6px;font-weight:700;color:#64748B;margin-bottom:4px">Altman Z</div>
<div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin-bottom:2px">
  <div style="width:33%;background:#DC2626"></div>
  <div style="width:34%;background:#D97706"></div>
  <div style="width:33%;background:#16A34A"></div>
</div>
<div style="position:relative;height:8px"><div style="position:absolute;left:78%;top:0;width:2px;height:8px;background:#0F172A"></div></div>
<div style="display:flex;justify-content:space-between;font-size:5px;color:#94A3B8"><span>Distress</span><span>Grey</span><span>Safe</span></div>
<div style="text-align:center;font-size:9px;font-weight:800;color:#16A34A;margin-top:2px">3.42</div>
</div>
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:8px">
<div style="font-size:6px;font-weight:700;color:#64748B;margin-bottom:4px">Piotroski F</div>
<div style="display:flex;gap:2px">
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#DC2626;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✗</div>
  <div style="flex:1;height:18px;background:#16A34A;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✓</div>
  <div style="flex:1;height:18px;background:#DC2626;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">✗</div>
</div>
<div style="text-align:center;font-size:10px;font-weight:800;color:#16A34A;margin-top:3px">7/9</div>
</div>
</div></div></div>

<!-- ═══════════════════════════════════════ -->
<!-- HEATMAPS & MATRICES -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="heatmaps"><div class="gn" style="color:#BE185D">05</div><div class="gt">Heat Maps & Risk Matrices</div><div class="gl" style="background:#BE185D"></div><div class="gc">4 styles</div></div>

<div class="item"><div class="ih"><div class="in">HeatMap-PxS</div><div class="id">Probability × Severity risk matrix</div><div class="ii">Risk management</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Claim Probability × Severity</div>
<div style="display:grid;grid-template-columns:40px repeat(5,1fr);gap:1px;font-size:6px">
  <div></div><div style="text-align:center;color:#64748B;padding:2px">Very Low</div><div style="text-align:center;color:#64748B;padding:2px">Low</div><div style="text-align:center;color:#64748B;padding:2px">Medium</div><div style="text-align:center;color:#64748B;padding:2px">High</div><div style="text-align:center;color:#64748B;padding:2px">Extreme</div>
  <div style="color:#64748B;padding:4px 2px;text-align:right">High</div><div style="background:#FEF3C7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FED7AA;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FECACA;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FCA5A5;padding:4px;text-align:center;border-radius:2px;color:#991B1B;font-weight:700">★</div><div style="background:#DC2626;padding:4px;text-align:center;border-radius:2px;color:white;font-weight:700">★</div>
  <div style="color:#64748B;padding:4px 2px;text-align:right">Med</div><div style="background:#DCFCE7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FEF3C7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FED7AA;padding:4px;text-align:center;border-radius:2px;color:#92400E;font-weight:700;font-size:8px">◆</div><div style="background:#FECACA;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FCA5A5;padding:4px;text-align:center;border-radius:2px">●</div>
  <div style="color:#64748B;padding:4px 2px;text-align:right">Low</div><div style="background:#DCFCE7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#DCFCE7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FEF3C7;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FED7AA;padding:4px;text-align:center;border-radius:2px">●</div><div style="background:#FECACA;padding:4px;text-align:center;border-radius:2px">●</div>
</div>
<div style="font-size:6px;color:#94A3B8;margin-top:4px">◆ = Current position · ★ = Worst-case scenario</div>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">HeatMap-Quarterly</div><div class="id">Color-coded quarterly performance grid</div><div class="ii">NYT calendar heat maps</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:10px">
<div style="font-size:7px;font-weight:700;color:#374151;margin-bottom:6px">Quarterly Earnings — Beat/Miss Heat Map</div>
<div style="display:grid;grid-template-columns:40px repeat(8,1fr);gap:2px;font-size:6px">
  <div></div><div style="text-align:center;color:#94A3B8;font-weight:600">Q1'24</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q2'24</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q3'24</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q4'24</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q1'25</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q2'25</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q3'25</div><div style="text-align:center;color:#94A3B8;font-weight:600">Q4'25</div>
  <div style="color:#64748B;font-weight:600;padding:2px">EPS</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+8%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+3%</div>
  <div style="background:#FEE2E2;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#991B1B">-12%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+5%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+2%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+6%</div>
  <div style="background:#FEF3C7;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#92400E">0%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+4%</div>
  <div style="color:#64748B;font-weight:600;padding:2px">Rev</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+5%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+4%</div>
  <div style="background:#FEE2E2;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#991B1B">-3%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+2%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+3%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+7%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+1%</div>
  <div style="background:#D1FAE5;padding:4px;text-align:center;border-radius:2px;font-weight:700;color:#065F46">+5%</div>
</div>
</div>
</div></div>

<!-- ═══════════════════════════════════════ -->
<!-- CHART LAYOUTS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="chart-layouts"><div class="gn" style="color:#EA580C">06</div><div class="gt">Chart Layout Options</div><div class="gl" style="background:#EA580C"></div><div class="gc">3 layouts</div></div>

<div class="item"><div class="ih"><div class="in">Layout-FullWidth-Strip</div><div class="id">Thin chart stretching full width — maximum data density</div><div class="ii">Bloomberg header strips</div></div>
<div class="demo">
<div style="background:#1A1A2E;border-radius:4px;padding:4px 10px;height:40px;position:relative">
  <div style="font-size:6px;font-weight:700;color:#D4A843;letter-spacing:0.5px;position:absolute;left:10px;top:4px">RPM 5Y WEEKLY</div>
  <svg width="100%" height="28" viewBox="0 0 600 28" style="margin-top:10px">
    <path d="M0,22 L50,20 L100,18 L150,15 L200,16 L250,14 L300,12 L350,13 L400,10 L450,8 L500,6 L550,5 L600,4" fill="none" stroke="#E8903A" stroke-width="1.5"/>
  </svg>
</div>
<div class="label">Full-width strip — 40px tall, dark bg, used at top of dashboard</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Layout-2Up-SideBySide</div><div class="id">Two charts side by side — 1Y vs 5Y, company vs peer</div></div>
<div class="demo">
<div class="c2">
<div style="background:#1A1A2E;border-radius:4px;padding:6px 8px;height:80px">
  <div style="font-size:6px;font-weight:700;color:#D4A843">DRAWDOWN — 1Y</div>
  <svg width="100%" height="55" viewBox="0 0 200 55" style="margin-top:4px">
    <path d="M0,5 L20,5 L40,10 L60,20 L80,35 L100,45 L120,40 L140,30 L160,15 L180,8 L200,5" fill="#DC2626" opacity="0.15"/><path d="M0,5 L20,5 L40,10 L60,20 L80,35 L100,45 L120,40 L140,30 L160,15 L180,8 L200,5" fill="none" stroke="#DC2626" stroke-width="1.5"/>
  </svg>
</div>
<div style="background:#1A1A2E;border-radius:4px;padding:6px 8px;height:80px">
  <div style="font-size:6px;font-weight:700;color:#D4A843">DRAWDOWN — 5Y</div>
  <svg width="100%" height="55" viewBox="0 0 200 55" style="margin-top:4px">
    <path d="M0,5 L30,8 L60,25 L80,40 L100,50 L120,45 L140,20 L160,10 L180,15 L200,8" fill="#DC2626" opacity="0.15"/><path d="M0,5 L30,8 L60,25 L80,40 L100,50 L120,45 L140,20 L160,10 L180,15 L200,8" fill="none" stroke="#DC2626" stroke-width="1.5"/>
  </svg>
</div>
</div>
<div class="label">Side-by-side comparison — same chart type, different time periods</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Layout-Standard-Card</div><div class="id">Chart inside a card frame with title and legend</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:8px;overflow:hidden">
  <div style="background:#059669;padding:6px 12px;display:flex;align-items:center;gap:6px"><span style="font-size:10px;font-weight:900;color:rgba(255,255,255,0.3);font-family:'JetBrains Mono',monospace">15</span><span style="font-size:11px;font-weight:800;color:white">Debt Maturity Schedule</span></div>
  <div style="padding:10px;background:white">
    <svg width="100%" height="60" viewBox="0 0 400 60">
      <rect x="10" y="5" width="50" height="50" rx="3" fill="#DC2626"/><text x="35" y="60" text-anchor="middle" font-size="5" fill="#64748B">2025</text>
      <rect x="70" y="15" width="50" height="40" rx="3" fill="#DC2626" opacity="0.7"/><text x="95" y="60" text-anchor="middle" font-size="5" fill="#64748B">2026</text>
      <rect x="130" y="25" width="50" height="30" rx="3" fill="#3B82F6"/><text x="155" y="60" text-anchor="middle" font-size="5" fill="#64748B">2027</text>
      <rect x="190" y="30" width="50" height="25" rx="3" fill="#3B82F6"/><text x="215" y="60" text-anchor="middle" font-size="5" fill="#64748B">2028</text>
      <rect x="250" y="38" width="50" height="17" rx="3" fill="#3B82F6"/><text x="275" y="60" text-anchor="middle" font-size="5" fill="#64748B">2029</text>
      <rect x="310" y="42" width="50" height="13" rx="3" fill="#3B82F6"/><text x="335" y="60" text-anchor="middle" font-size="5" fill="#64748B">2030+</text>
    </svg>
    <div style="font-size:6px;color:#94A3B8;display:flex;gap:8px;margin-top:4px"><span><span style="color:#DC2626">■</span> Near-term (&lt;2yr)</span><span><span style="color:#3B82F6">■</span> Future</span></div>
  </div>
</div>
</div></div>

<!-- ═══════════════════════════════════════ -->
<!-- COMPACT STRIPS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="strips"><div class="gn" style="color:#64748B">07</div><div class="gt">Compact Strips & KPI Rows</div><div class="gl" style="background:#64748B"></div><div class="gc">4 styles</div></div>

<div class="item"><div class="ih"><div class="in">Strip-6Metric</div><div class="id">6 colored mini-cards in a row</div><div class="ii">Bloomberg header</div></div>
<div class="demo">
<div class="c6">
  <div style="background:#F5F3FF;border:1px solid #DDD6FE;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">$12.5B</div><div style="font-size:6px;color:#7C3AED;font-weight:700;text-transform:uppercase">Market Cap</div></div>
  <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">$112.30</div><div style="font-size:6px;color:#C2410C;font-weight:700;text-transform:uppercase">Price</div></div>
  <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">$7.3B</div><div style="font-size:6px;color:#16A34A;font-weight:700;text-transform:uppercase">Revenue</div></div>
  <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">$1.04B</div><div style="font-size:6px;color:#DC2626;font-weight:700;text-transform:uppercase">EBITDA</div></div>
  <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">17,800</div><div style="font-size:6px;color:#16A34A;font-weight:700;text-transform:uppercase">Employees</div></div>
  <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:4px;padding:4px 6px;text-align:center"><div style="font-size:12px;font-weight:800">14.2x</div><div style="font-size:6px;color:#1D4ED8;font-weight:700;text-transform:uppercase">P/E Ratio</div></div>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Strip-4Alert</div><div class="id">4 UW priority metrics</div></div>
<div class="demo">
<div class="c4">
  <div style="background:white;border:1px solid #E5E7EB;border-radius:4px;padding:6px 8px"><div style="font-size:6px;color:#64748B;font-weight:700;text-transform:uppercase">EPS Beat Streak</div><div style="font-size:16px;font-weight:800;color:#16A34A">8</div><div style="font-size:7px;color:#16A34A;font-weight:600">consecutive beats</div></div>
  <div style="background:white;border:1px solid #E5E7EB;border-radius:4px;padding:6px 8px"><div style="font-size:6px;color:#64748B;font-weight:700;text-transform:uppercase">Estimate Spread</div><div style="display:flex;gap:6px;margin-top:2px"><div style="text-align:center"><div style="font-size:12px;font-weight:800;color:#16A34A">4.2%</div><div style="font-size:5px;color:#6B7280">CQ</div></div><div style="text-align:center"><div style="font-size:12px;font-weight:800;color:#D97706">8.1%</div><div style="font-size:5px;color:#6B7280">NQ</div></div></div></div>
  <div style="background:white;border:1px solid #E5E7EB;border-radius:4px;padding:6px 8px"><div style="font-size:6px;color:#64748B;font-weight:700;text-transform:uppercase">Analyst Trend (90d)</div><div style="font-size:14px;font-weight:800;color:#16A34A">↑ Bullish</div><div style="font-size:7px;color:#6B7280">3 up, 0 down</div></div>
  <div style="background:white;border:1px solid #E5E7EB;border-radius:4px;padding:6px 8px"><div style="font-size:6px;color:#64748B;font-weight:700;text-transform:uppercase">Key Dates</div><div style="font-size:7px;margin-top:2px"><div style="display:flex;justify-content:space-between"><span style="color:#6B7280">Earnings</span><span style="font-weight:700;font-variant-numeric:tabular-nums">Apr 15</span></div><div style="display:flex;justify-content:space-between"><span style="color:#6B7280">10-K Due</span><span style="font-weight:700;font-variant-numeric:tabular-nums">Mar 01</span></div></div></div>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Strip-ScoreBar</div><div class="id">Linear score with tier zones</div></div>
<div class="demo">
<div style="border:1px solid #E2E8F0;border-radius:6px;padding:8px 12px">
<div style="display:flex;align-items:center;gap:10px">
  <div style="font-size:24px;font-weight:900;color:#16A34A">91</div>
  <div style="flex:1">
    <div style="display:flex;height:10px;border-radius:5px;overflow:hidden">
      <div style="width:15%;background:#991B1B" title="NO TOUCH"></div>
      <div style="width:15%;background:#DC2626" title="WALK"></div>
      <div style="width:15%;background:#EA580C" title="WATCH"></div>
      <div style="width:20%;background:#D97706" title="WRITE"></div>
      <div style="width:20%;background:#059669" title="WANT"></div>
      <div style="width:15%;background:#16A34A" title="WIN"></div>
    </div>
    <div style="position:relative;height:0"><div style="position:absolute;left:91%;top:-14px;font-size:14px">▼</div></div>
    <div style="display:flex;justify-content:space-between;font-size:5px;color:#94A3B8;margin-top:2px"><span>0</span><span>NO TOUCH</span><span>WALK</span><span>WATCH</span><span>WRITE</span><span>WANT</span><span>WIN</span><span>100</span></div>
  </div>
  <div style="font-size:11px;font-weight:700;padding:3px 10px;border-radius:5px;background:#16A34A;color:white;letter-spacing:1px">WIN</div>
</div>
</div>
</div></div>

<!-- ═══════════════════════════════════════ -->
<!-- COMPOSITIONS -->
<!-- ═══════════════════════════════════════ -->
<div class="gh" id="compositions"><div class="gn" style="color:#0891B2">08</div><div class="gt">Complex Card Compositions</div><div class="gl" style="background:#0891B2"></div><div class="gc">3 examples</div></div>

<div class="item"><div class="ih"><div class="in">Composition-BalanceSheet</div><div class="id">Mini-card with chart + ratios + context</div></div>
<div class="demo">
<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:5px;padding:6px 8px;max-width:200px">
  <div style="font-size:7px;color:#16A34A;text-transform:uppercase;font-weight:700;margin-bottom:3px">Balance Sheet</div>
  <div style="font-size:14px;font-weight:800">$8.4B</div>
  <div style="font-size:7px;color:#6B7280">Total assets</div>
  <div style="display:flex;gap:2px;margin-top:3px"><div style="flex:1;background:#D1FAE5;border-radius:2px;padding:2px;text-align:center"><div style="font-size:7px;font-weight:700;color:#065F46">$3.2B</div><div style="font-size:5px;color:#065F46">Equity</div></div><div style="flex:1;background:#FEE2E2;border-radius:2px;padding:2px;text-align:center"><div style="font-size:7px;font-weight:700;color:#991B1B">$5.2B</div><div style="font-size:5px;color:#991B1B">Liabilities</div></div></div>
  <div style="display:flex;height:8px;border-radius:3px;overflow:hidden;margin-top:3px"><div style="width:14%;background:#16A34A"></div><div style="width:86%;background:#DC2626"></div></div>
  <div style="margin-top:4px;padding-top:3px;border-top:1px solid #BBF7D0;font-size:7px">
    <div style="display:flex;justify-content:space-between"><span style="color:#6B7280">Cash</span><span style="font-weight:600;color:#16A34A">$705M</span></div>
    <div style="display:flex;justify-content:space-between"><span style="color:#6B7280">Total Debt</span><span style="font-weight:600;color:#DC2626">$4.2B</span></div>
    <div style="display:flex;justify-content:space-between"><span style="color:#6B7280">D/E</span><span style="font-weight:600;color:#D97706">187%</span></div>
    <div style="display:flex;justify-content:space-between"><span style="color:#6B7280">Int. Cov.</span><span style="font-weight:600">4.2x</span></div>
  </div>
  <div style="margin-top:3px;padding:2px 3px;background:#ECFDF5;border-left:2px solid #16A34A;border-radius:2px;font-size:5.5px;color:#065F46">Strong cash generation offsets leverage. Goodwill concentration at 48% requires monitoring for impairment triggers.</div>
</div>
</div></div>

<div class="item"><div class="ih"><div class="in">Composition-DropInvestigation</div><div class="id">Chart + numbered findings + legend table</div></div>
<div class="demo">
<div style="border:2px solid #0F172A30;border-radius:10px;overflow:hidden">
<div style="background:#0F172A;padding:8px 14px;display:flex;align-items:center;gap:8px"><span style="font-size:14px;font-weight:900;color:rgba(255,255,255,0.3);font-family:'JetBrains Mono',monospace">00</span><span style="font-size:11px;font-weight:800;color:white">Stock Drop Investigation</span></div>
<div style="background:#1A1A2E;padding:8px 12px">
  <svg width="100%" height="60" viewBox="0 0 400 60">
    <path d="M0,45 C50,42 100,38 150,30 C180,25 200,35 220,40 C250,42 280,30 320,20 C350,15 380,12 400,10" fill="none" stroke="#E8903A" stroke-width="3" opacity="0.15"/>
    <path d="M0,45 C50,42 100,38 150,30 C180,25 200,35 220,40 C250,42 280,30 320,20 C350,15 380,12 400,10" fill="none" stroke="#E8903A" stroke-width="1.8"/>
    <path d="M0,48 C60,46 120,44 180,42 C240,40 300,36 360,33 L400,31" fill="none" stroke="#6B7280" stroke-width="0.8" stroke-dasharray="4,3"/>
    <circle cx="220" cy="40" r="8" fill="#DC2626"/><text x="220" y="43" text-anchor="middle" fill="white" font-size="7" font-weight="700">1</text>
    <circle cx="320" cy="20" r="8" fill="#F59E0B"/><text x="320" y="23" text-anchor="middle" fill="white" font-size="7" font-weight="700">2</text>
  </svg>
</div>
<div style="padding:6px 12px;font-size:8px">
  <table style="width:100%;border-collapse:collapse"><tr style="border-bottom:1px solid #E5E7EB;font-size:7px;color:#64748B;font-weight:700"><td style="padding:2px 4px">#</td><td>Date</td><td>Drop</td><td>Duration</td><td>Catalyst</td><td>Type</td></tr>
  <tr style="border-bottom:1px solid #F3F4F6"><td style="padding:2px 4px"><span style="display:inline-block;width:12px;height:12px;border-radius:6px;background:#DC2626;color:white;font-size:6px;line-height:12px;text-align:center;font-weight:700">1</span></td><td>2025-08-15</td><td style="color:#DC2626;font-weight:700">-18.3%</td><td>12 days</td><td>Earnings miss, guidance cut to $7.8B</td><td style="font-size:7px;padding:1px 4px;background:#FEF2F2;color:#991B1B;border-radius:2px">earnings_miss</td></tr>
  <tr><td style="padding:2px 4px"><span style="display:inline-block;width:12px;height:12px;border-radius:6px;background:#F59E0B;color:white;font-size:6px;line-height:12px;text-align:center;font-weight:700">2</span></td><td>2025-11-02</td><td style="color:#D97706;font-weight:700">-9.7%</td><td>5 days</td><td>Sector selloff (ETF -7.2%)</td><td style="font-size:7px;padding:1px 4px;background:#F1F5F9;color:#475569;border-radius:2px">market</td></tr>
  </table>
</div>
</div>
</div></div>

</div><!-- /gallery -->

<div class="footer"><strong>Design Gallery v2</strong> — Charts, Infographics, Compositions, Layout Options · Review and select styles for each card</div>
</body></html>'''


if __name__ == "__main__":
    html = build()
    Path("output/DESIGN_GALLERY_v2.html").write_text(html)
    print("Generated: output/DESIGN_GALLERY_v2.html")
