#!/usr/bin/env python3
"""Design Gallery — live rendered examples of every visual element in the worksheet."""

from pathlib import Path


def build():
    html = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>D&O Worksheet — Design Gallery</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#F8FAFC;color:#1E293B}
.hero{text-align:center;padding:32px 24px 20px;background:white;border-bottom:1px solid #E2E8F0}
.hero h1{font-size:24px;font-weight:900}
.hero .sub{font-size:12px;color:#64748B;margin-top:4px}
.nav{position:sticky;top:0;z-index:100;background:white;border-bottom:2px solid #E2E8F0;padding:8px 16px;display:flex;flex-wrap:wrap;gap:4px;justify-content:center}
.nav a{font-size:10px;font-weight:600;padding:4px 12px;border-radius:5px;text-decoration:none;color:white}
.gallery{max-width:1100px;margin:0 auto;padding:16px}
.group{margin-bottom:32px}
.group-hdr{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.group-num{font-size:28px;font-weight:900;opacity:0.15}
.group-title{font-size:16px;font-weight:800}
.group-line{flex:1;height:2px;opacity:0.15;border-radius:1px}
.item{background:white;border:1px solid #E2E8F0;border-radius:10px;margin-bottom:14px;overflow:hidden}
.item-hdr{padding:10px 14px;border-bottom:1px solid #F1F5F9;display:flex;align-items:center;gap:8px}
.item-name{font-size:12px;font-weight:800;font-family:'JetBrains Mono',monospace;flex:1}
.item-desc{font-size:9px;color:#64748B}
.item-insp{font-size:8px;color:#94A3B8;font-style:italic}
.item-demo{padding:16px;background:#FAFBFC}
.item-variants{padding:8px 14px;background:#F8FAFC;border-top:1px solid #F1F5F9;font-size:8px;color:#94A3B8}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start}
.col-2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.col-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.col-6{display:grid;grid-template-columns:repeat(6,1fr);gap:4px}
.footer{text-align:center;padding:32px;color:#94A3B8;font-size:10px;border-top:1px solid #E2E8F0;margin-top:32px;background:white}
</style></head><body>

<div class="hero">
<h1>Design Gallery</h1>
<div class="sub">Live rendered examples of every visual element. Click through to review, approve, or modify designs.</div>
</div>

<div class="nav">
<a href="#cards" style="background:#0F172A">Cards</a>
<a href="#badges" style="background:#7C3AED">Badges</a>
<a href="#callouts" style="background:#D97706">Callouts</a>
<a href="#infographics" style="background:#1D4ED8">Infographics</a>
<a href="#charts" style="background:#DC2626">Charts</a>
<a href="#tables" style="background:#059669">Tables</a>
<a href="#narratives" style="background:#6D28D9">Narratives</a>
</div>

<div class="gallery">

<!-- ════════════════════════════════════════════ -->
<!-- CARDS -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="cards">
<div class="group-hdr"><div class="group-num" style="color:#0F172A">01</div><div class="group-title">Cards</div><div class="group-line" style="background:#0F172A"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">MetricCard</div><div class="item-desc">Large bold number + label + optional trend</div><div class="item-insp">Bloomberg KPI tiles</div></div>
<div class="item-demo">
<div class="col-6">
  <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">$7.32B</div>
    <div style="font-size:6.5pt;color:#16A34A;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">Revenue</div>
    <div style="font-size:5.5pt;color:#9CA3AF;margin-top:1px">FY2025 · XBRL · HIGH</div>
  </div>
  <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">$-359.6M</div>
    <div style="font-size:6.5pt;color:#DC2626;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">Net Income</div>
  </div>
  <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">$705.7M</div>
    <div style="font-size:6.5pt;color:#1D4ED8;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">Cash</div>
  </div>
  <div style="background:#F5F3FF;border:1px solid #DDD6FE;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">14.2x</div>
    <div style="font-size:6.5pt;color:#7C3AED;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">P/E Ratio</div>
  </div>
  <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">$137K</div>
    <div style="font-size:6.5pt;color:#C2410C;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">Debt</div>
  </div>
  <div style="background:#F1F5F9;border:1px solid #E2E8F0;border-radius:5px;padding:6px 8px;text-align:center">
    <div style="font-size:13pt;font-weight:800;color:#374151">9.33</div>
    <div style="font-size:6.5pt;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px">Current Ratio</div>
  </div>
</div>
</div>
<div class="item-variants">Variants: Green (positive), Red (negative/debt), Blue (neutral), Purple (valuation), Orange (warning), Default (gray)</div>
</div>

<div class="item">
<div class="item-hdr"><div class="item-name">RiskCard</div><div class="item-desc">Title + severity badge + evidence bullets + colored left border</div><div class="item-insp">Economist risk boxes</div></div>
<div class="item-demo">
<div style="border-left:3px solid #DC2626;background:#FEF2F2;padding:8px 12px;border-radius:0 5px 5px 0;margin-bottom:6px">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
    <span style="font-size:10px;font-weight:800;color:#991B1B">Refinancing Risk</span>
    <span style="font-size:7px;font-weight:700;padding:1px 6px;border-radius:8px;background:#DC2626;color:white">HIGH</span>
  </div>
  <div style="font-size:9px;color:#4B5563;line-height:1.5">
    • $2.1B in debt maturing within 18 months at 4.2% weighted average rate<br>
    • Current market rates 6.5-7.2% would increase annual interest by $42M<br>
    • Net Debt/EBITDA of 3.8x limits refinancing options
  </div>
</div>
<div style="border-left:3px solid #D97706;background:#FFFBEB;padding:8px 12px;border-radius:0 5px 5px 0">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
    <span style="font-size:10px;font-weight:800;color:#92400E">Customer Concentration</span>
    <span style="font-size:7px;font-weight:700;padding:1px 6px;border-radius:8px;background:#D97706;color:white">MEDIUM</span>
  </div>
  <div style="font-size:9px;color:#4B5563;line-height:1.5">
    • Top 3 customers represent 34% of revenue<br>
    • Loss of largest customer ($890M) would trigger covenant breach
  </div>
</div>
</div>
</div>

<div class="item">
<div class="item-hdr"><div class="item-name">KeyValueCard</div><div class="item-desc">Compact labeled pairs in bordered container</div><div class="item-insp">Capital IQ fact tables</div></div>
<div class="item-demo">
<div class="col-2">
  <div style="border:1px solid #E2E8F0;border-radius:5px;overflow:hidden">
    <div style="background:#F3F4F6;padding:4px 8px"><span style="font-size:9pt;font-weight:700;color:#1F3A5C">Company Profile</span></div>
    <div style="padding:4px 8px">
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">Ticker</span><span style="font-weight:600">VKTX</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">Exchange</span><span style="font-weight:600">NASDAQ</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">SIC Code</span><span style="font-weight:600">2834</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;font-size:9px"><span style="color:#64748B">Market Cap</span><span style="font-weight:600">$8.2B</span></div>
    </div>
  </div>
  <div style="border:1px solid #E2E8F0;border-radius:5px;overflow:hidden">
    <div style="background:#F3F4F6;padding:4px 8px"><span style="font-size:9pt;font-weight:700;color:#1F3A5C">Debt Profile</span></div>
    <div style="padding:4px 8px">
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">Total Debt</span><span style="font-weight:600;color:#DC2626">$4.2B</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">Net Debt</span><span style="font-weight:600;color:#DC2626">$3.5B</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #F3F4F6;font-size:9px"><span style="color:#64748B">D/E Ratio</span><span style="font-weight:600;color:#D97706">187%</span></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0;font-size:9px"><span style="color:#64748B">Int. Coverage</span><span style="font-weight:600">4.2x</span></div>
    </div>
  </div>
</div>
</div>
</div>

<div class="item">
<div class="item-hdr"><div class="item-name">AlertCard</div><div class="item-desc">Prominent notification with pills and colored border</div><div class="item-insp">WSJ breaking alerts</div></div>
<div class="item-demo">
<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:5px;padding:8px 12px;margin-bottom:6px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
    <span style="font-size:10px;font-weight:700;color:#991B1B">Litigation & Regulatory Status</span>
    <div style="display:flex;gap:4px">
      <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#DC2626;color:white">2 Active SCAs</span>
      <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#F59E0B;color:white">1 Derivative</span>
    </div>
  </div>
  <div style="font-size:9px;color:#374151">🔴 <b style="color:#DC2626">In re Meta Platforms Securities Litigation</b> — Filed 2024-11-15, S.D.N.Y.</div>
</div>
<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:5px;padding:8px 12px">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:10px;font-weight:700;color:#065F46">Litigation & Regulatory Status</span>
    <div style="display:flex;gap:4px">
      <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#D1FAE5;color:#065F46">No Active SCAs</span>
      <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#D1FAE5;color:#065F46">No Derivatives</span>
    </div>
  </div>
</div>
</div>
</div>

<div class="item">
<div class="item-hdr"><div class="item-name">ComparisonCard</div><div class="item-desc">Side-by-side metric comparison</div><div class="item-insp">Economist comparisons</div></div>
<div class="item-demo">
<div style="display:flex;border:1px solid #E2E8F0;border-radius:5px;overflow:hidden">
  <div style="flex:1;padding:8px 12px;text-align:center;border-right:1px solid #E2E8F0">
    <div style="font-size:7px;color:#64748B;text-transform:uppercase;font-weight:600">Company TSR</div>
    <div style="font-size:18px;font-weight:800;color:#16A34A">+233.9%</div>
  </div>
  <div style="flex:1;padding:8px 12px;text-align:center">
    <div style="font-size:7px;color:#64748B;text-transform:uppercase;font-weight:600">Peer Group TSR</div>
    <div style="font-size:18px;font-weight:800;color:#D97706">+279.5%</div>
  </div>
</div>
</div>
</div>

<div class="item">
<div class="item-hdr"><div class="item-name">TimelineCard</div><div class="item-desc">Vertical timeline with colored dots and connecting line</div><div class="item-insp">NYT event timelines</div></div>
<div class="item-demo">
<div style="padding:4px 0 4px 20px;border-left:2px solid #E2E8F0;margin-left:8px">
  <div style="position:relative;padding:6px 0 12px">
    <div style="position:absolute;left:-25px;top:8px;width:10px;height:10px;border-radius:5px;background:#DC2626"></div>
    <div style="font-size:8px;color:#94A3B8;font-variant-numeric:tabular-nums">2025-12-05</div>
    <div style="font-size:10px;font-weight:700">CFO Resignation</div>
    <div style="font-size:9px;color:#64748B">Sarah Chen resigned effective immediately, citing personal reasons</div>
  </div>
  <div style="position:relative;padding:6px 0 12px">
    <div style="position:absolute;left:-25px;top:8px;width:10px;height:10px;border-radius:5px;background:#F59E0B"></div>
    <div style="font-size:8px;color:#94A3B8;font-variant-numeric:tabular-nums">2025-10-22</div>
    <div style="font-size:10px;font-weight:700">Earnings Guidance Cut</div>
    <div style="font-size:9px;color:#64748B">FY2026 revenue guidance lowered from $8.5B to $7.8B (-8.2%)</div>
  </div>
  <div style="position:relative;padding:6px 0">
    <div style="position:absolute;left:-25px;top:8px;width:10px;height:10px;border-radius:5px;background:#16A34A"></div>
    <div style="font-size:8px;color:#94A3B8;font-variant-numeric:tabular-nums">2025-08-15</div>
    <div style="font-size:10px;font-weight:700">Acquisition Completed</div>
    <div style="font-size:9px;color:#64748B">Closed acquisition of DataSync Corp for $1.2B</div>
  </div>
</div>
</div>
</div>

</div><!-- /cards group -->

<!-- ════════════════════════════════════════════ -->
<!-- BADGES -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="badges">
<div class="group-hdr"><div class="group-num" style="color:#7C3AED">02</div><div class="group-title">Badges & Pills</div><div class="group-line" style="background:#7C3AED"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">StatusBadge</div><div class="item-desc">Check result indicators</div></div>
<div class="item-demo">
<div class="row">
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#DC2626;color:white">TRIGGERED</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#047857;color:white">CLEAR</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#D97706;color:white">ELEVATED</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#6B7280;color:white">SKIPPED</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#2563EB;color:white">INFO</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px;background:#D97706;color:white">DEFERRED</span>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">TierBadge</div><div class="item-desc">Underwriting recommendation tiers</div></div>
<div class="item-demo">
<div class="row">
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#16A34A;color:white;letter-spacing:1px">WIN</span>
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#059669;color:white;letter-spacing:1px">WANT</span>
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#D97706;color:white;letter-spacing:1px">WRITE</span>
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#EA580C;color:white;letter-spacing:1px">WATCH</span>
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#DC2626;color:white;letter-spacing:1px">WALK</span>
  <span style="font-size:9px;font-weight:700;padding:3px 12px;border-radius:6px;background:#991B1B;color:white;letter-spacing:1px">NO TOUCH</span>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">VerdictBadge</div><div class="item-desc">Section-level assessment</div></div>
<div class="item-demo">
<div class="row">
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:4px;background:#D1FAE5;color:#065F46">FAVORABLE</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:4px;background:#F1F5F9;color:#475569">NEUTRAL</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:4px;background:#FEF3C7;color:#92400E">CONCERNING</span>
  <span style="font-size:8px;font-weight:700;padding:2px 8px;border-radius:4px;background:#FEE2E2;color:#991B1B">CRITICAL</span>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">PillBadgeRow</div><div class="item-desc">Classification attributes</div></div>
<div class="item-demo">
<div class="row">
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#DBEAFE;color:#1D4ED8">Delaware</span>
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#F3E8FF;color:#7C3AED">NYSE</span>
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#DCFCE7;color:#166534">Large Cap</span>
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#FEF3C7;color:#92400E">S&P 500</span>
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#FFE4E6;color:#9F1239">Accelerated Filer</span>
  <span style="font-size:8px;font-weight:600;padding:2px 8px;border-radius:10px;background:#E0F2FE;color:#075985">18 Years Public</span>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">DataSourcePill</div><div class="item-desc">Data provenance indicators</div></div>
<div class="item-demo">
<div class="row">
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#DCFCE7;color:#166534">XBRL</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#FEF3C7;color:#92400E">yfinance</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#F3E8FF;color:#7C3AED">LLM</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#DBEAFE;color:#1D4ED8">Web</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#FFE4E6;color:#9F1239">SEC</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#F1F5F9;color:#475569">Computed</span>
  <span style="font-size:7px;font-weight:600;padding:2px 6px;border-radius:3px;background:#E0F2FE;color:#075985">Supabase</span>
</div>
</div></div>

</div><!-- /badges -->

<!-- ════════════════════════════════════════════ -->
<!-- CALLOUTS -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="callouts">
<div class="group-hdr"><div class="group-num" style="color:#D97706">03</div><div class="group-title">Callouts & Containers</div><div class="group-line" style="background:#D97706"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">DiscoveryBox</div><div class="item-desc">Blind spot / proactive finding</div><div class="item-insp">NYT "What We Found"</div></div>
<div class="item-demo">
<div style="border-left:4px solid #D4A843;background:#FFFBEB;padding:8px 12px;border-radius:0 5px 5px 0">
  <div style="font-size:7px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">Blind Spot Discovery</div>
  <div style="font-size:9.5px;color:#374151;line-height:1.5">Web search identified an unreported OSHA investigation at the Memphis facility opened December 2025. Three workplace safety incidents in 90 days triggered the investigation. This is not yet disclosed in SEC filings and could indicate operational risk not captured by structured data sources.</div>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">InsightBox</div><div class="item-desc">Underwriting-specific analytical insight</div></div>
<div class="item-demo">
<div style="border-left:4px solid #1F3A5C;background:#F0F4F8;padding:8px 12px;border-radius:0 5px 5px 0">
  <div style="font-size:7px;font-weight:700;color:#1F3A5C;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">Underwriting Insight</div>
  <div style="font-size:9.5px;color:#374151;line-height:1.5">The combination of 34% customer concentration, $2.1B near-term maturities, and a CFO departure creates a compounding risk scenario. If the largest customer reduces orders during the refinancing window, covenant breach becomes likely — and that's when plaintiffs file.</div>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">SCRBlock</div><div class="item-desc">Situation → Complication → Resolution</div><div class="item-insp">McKinsey pyramid</div></div>
<div class="item-demo">
<div style="border-top:2px solid #1F3A5C;background:#F8FAFC;padding:10px 12px;border-radius:0 0 5px 5px">
  <div style="margin-bottom:8px"><span style="font-size:7px;font-weight:700;color:#1F3A5C;text-transform:uppercase;background:#E2E8F0;padding:1px 6px;border-radius:2px">Situation</span><div style="font-size:9.5px;color:#374151;margin-top:3px;line-height:1.5">RPM International generates $7.3B in specialty coatings revenue across 5 operating segments, with 62% of revenue from North America.</div></div>
  <div style="margin-bottom:8px"><span style="font-size:7px;font-weight:700;color:#D97706;text-transform:uppercase;background:#FEF3C7;padding:1px 6px;border-radius:2px">Complication</span><div style="font-size:9.5px;color:#374151;margin-top:3px;line-height:1.5">Raw material costs increased 12% YoY while pricing power limited to 4-6% pass-through. EBITDA margin compressed 280bps to 14.2%, and the acquisition-heavy growth strategy has pushed goodwill to 48% of total assets.</div></div>
  <div><span style="font-size:7px;font-weight:700;color:#059669;text-transform:uppercase;background:#DCFCE7;padding:1px 6px;border-radius:2px">Resolution</span><div style="font-size:9.5px;color:#374151;margin-top:3px;line-height:1.5">Favorable D&O profile despite margin pressure: no active litigation, strong cash generation ($890M FCF), and seasoned management team. WIN tier at current pricing. Monitor goodwill impairment risk if organic growth stalls.</div></div>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">DualVoice</div><div class="item-desc">Factual + analytical commentary pair</div><div class="item-insp">Audit dual-perspective</div></div>
<div class="item-demo">
<div style="margin-bottom:6px">
  <div style="font-size:7px;font-weight:700;color:#1F3A5C;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">What Was Said</div>
  <div style="font-size:9.5px;color:#374151;line-height:1.5;padding:6px 10px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:4px">Management reported Q3 revenue of $1.92B, a 3.2% decline from the prior year quarter. Operating margin improved 40bps to 11.8% on cost reduction initiatives. The company maintained full-year guidance of $7.6-7.8B.</div>
</div>
<div>
  <div style="font-size:7px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px">Underwriting Commentary</div>
  <div style="font-size:9.5px;color:#374151;line-height:1.5;padding:6px 10px;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:4px;border-left:3px solid #2563EB">The revenue decline masks a more concerning trend: organic growth was -5.1%, with acquisitions providing the only positive contribution. Margin improvement came from headcount reductions, not operational efficiency. The narrow guidance range ($200M) in a $7.7B business suggests management is sandbagging — either they know something we don't, or they've lost visibility.</div>
</div>
</div></div>

</div><!-- /callouts -->

<!-- ════════════════════════════════════════════ -->
<!-- INFOGRAPHICS -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="infographics">
<div class="group-hdr"><div class="group-num" style="color:#1D4ED8">04</div><div class="group-title">Inline Charts & Infographics</div><div class="group-line" style="background:#1D4ED8"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">Sparkline</div><div class="item-desc">Inline trend line (60x16px)</div><div class="item-insp">Edward Tufte</div></div>
<div class="item-demo">
<div class="row" style="align-items:center;gap:24px">
  <div><span style="font-size:9px;color:#64748B;margin-right:6px">Revenue (up)</span><svg width="60" height="16" viewBox="0 0 60 16"><path d="M0,14 L10,12 L20,10 L30,9 L40,6 L50,4 L60,2" fill="none" stroke="#16A34A" stroke-width="1.5"/><path d="M0,14 L10,12 L20,10 L30,9 L40,6 L50,4 L60,2 L60,16 L0,16Z" fill="#16A34A" opacity="0.15"/></svg></div>
  <div><span style="font-size:9px;color:#64748B;margin-right:6px">EBITDA (down)</span><svg width="60" height="16" viewBox="0 0 60 16"><path d="M0,3 L10,4 L20,6 L30,8 L40,10 L50,12 L60,14" fill="none" stroke="#DC2626" stroke-width="1.5"/><path d="M0,3 L10,4 L20,6 L30,8 L40,10 L50,12 L60,14 L60,16 L0,16Z" fill="#DC2626" opacity="0.15"/></svg></div>
  <div><span style="font-size:9px;color:#64748B;margin-right:6px">FCF (flat)</span><svg width="60" height="16" viewBox="0 0 60 16"><path d="M0,8 L10,7 L20,9 L30,8 L40,7 L50,8 L60,8" fill="none" stroke="#6B7280" stroke-width="1.5"/></svg></div>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">DecileDots + RangeSlider + CompositionBar</div><div class="item-desc">Position indicators</div></div>
<div class="item-demo">
<div style="display:flex;flex-direction:column;gap:12px">
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">DecileDots — Market Cap Position (Decile 8 of 10)</div>
    <div style="display:flex;gap:2px">
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#7C3AED"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
      <div style="width:12px;height:8px;border-radius:2px;background:#DDD6FE"></div>
    </div>
  </div>
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">RangeSlider — 52-Week Range ($89.20 to $142.50, current $112.30)</div>
    <div style="position:relative;height:12px;background:#E5E7EB;border-radius:6px;width:200px">
      <div style="position:absolute;left:0;top:0;width:62%;height:12px;background:#BBF7D0;border-radius:6px"></div>
      <div style="position:absolute;left:60%;top:-2px;width:16px;height:16px;border-radius:8px;background:#16A34A;border:2px solid white"></div>
    </div>
    <div style="display:flex;justify-content:space-between;width:200px;font-size:7px;color:#94A3B8;margin-top:2px"><span>$89.20</span><span>$142.50</span></div>
  </div>
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">CompositionBar — Cash ($705M) vs Debt ($4.2B)</div>
    <div style="display:flex;height:14px;border-radius:4px;overflow:hidden;width:200px">
      <div style="width:14%;background:#16A34A;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">14%</div>
      <div style="width:86%;background:#DC2626;display:flex;align-items:center;justify-content:center;font-size:6px;color:white;font-weight:700">86%</div>
    </div>
    <div style="display:flex;justify-content:space-between;width:200px;font-size:7px;margin-top:2px"><span style="color:#16A34A;font-weight:600">Cash $705M</span><span style="color:#DC2626;font-weight:600">Debt $4.2B</span></div>
  </div>
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">SeverityBlocks — Plaintiff Exposure (3 of 5)</div>
    <div style="display:flex;gap:1px">
      <div style="width:14px;height:10px;border-radius:2px;background:#DC2626"></div>
      <div style="width:14px;height:10px;border-radius:2px;background:#DC2626"></div>
      <div style="width:14px;height:10px;border-radius:2px;background:#DC2626"></div>
      <div style="width:14px;height:10px;border-radius:2px;background:#E5E7EB"></div>
      <div style="width:14px;height:10px;border-radius:2px;background:#E5E7EB"></div>
    </div>
  </div>
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">EarningsCircles — Beat/Miss (6 of 8 beats)</div>
    <div style="display:flex;gap:3px;align-items:center">
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#DC2626"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#DC2626"></div>
      <div style="width:8px;height:8px;border-radius:4px;background:#16A34A"></div>
      <span style="font-size:8px;color:#9CA3AF;margin-left:4px">6/8 beats</span>
    </div>
  </div>
  <div>
    <div style="font-size:8px;color:#64748B;margin-bottom:3px">FactorBar — Market Risk Score (12/15 points deducted)</div>
    <div style="width:200px;height:10px;background:#E5E7EB;border-radius:5px;position:relative">
      <div style="width:80%;height:10px;background:#DC2626;border-radius:5px"></div>
      <span style="position:absolute;right:4px;top:0;font-size:7px;font-weight:700;color:white;line-height:10px">12/15</span>
    </div>
  </div>
</div>
</div></div>

</div><!-- /infographics -->

<!-- ════════════════════════════════════════════ -->
<!-- TABLES -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="tables">
<div class="group-hdr"><div class="group-num" style="color:#059669">05</div><div class="group-title">Tables</div><div class="group-line" style="background:#059669"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">FinancialRow</div><div class="item-desc">Label | Current | Prior | YoY Change</div><div class="item-insp">Earnings releases</div></div>
<div class="item-demo">
<table style="width:100%;border-collapse:collapse;font-size:9px">
<tr style="background:#F9FAFB;border-bottom:1px solid #E5E7EB"><th style="padding:4px 8px;text-align:left;font-size:7.5px;font-weight:700;color:#6B7280;text-transform:uppercase">Metric</th><th style="padding:4px 8px;text-align:right;font-size:7.5px;font-weight:700;color:#6B7280">FY2025</th><th style="padding:4px 8px;text-align:right;font-size:7.5px;font-weight:700;color:#6B7280">FY2024</th><th style="padding:4px 8px;text-align:right;font-size:7.5px;font-weight:700;color:#6B7280">YoY</th></tr>
<tr style="border-bottom:1px solid #F3F4F6"><td style="padding:4px 8px;font-weight:600">Revenue</td><td style="padding:4px 8px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums">$7.32B</td><td style="padding:4px 8px;text-align:right;color:#6B7280;font-variant-numeric:tabular-nums">$7.09B</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#16A34A">+3.2%</td></tr>
<tr style="border-bottom:1px solid #F3F4F6"><td style="padding:4px 8px;font-weight:600">EBITDA</td><td style="padding:4px 8px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums">$1.04B</td><td style="padding:4px 8px;text-align:right;color:#6B7280;font-variant-numeric:tabular-nums">$1.12B</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#DC2626">-7.1%</td></tr>
<tr style="border-bottom:1px solid #F3F4F6"><td style="padding:4px 8px;font-weight:600">Net Income</td><td style="padding:4px 8px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums">$482M</td><td style="padding:4px 8px;text-align:right;color:#6B7280;font-variant-numeric:tabular-nums">$521M</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#DC2626">-7.5%</td></tr>
<tr><td style="padding:4px 8px;font-weight:600">Free Cash Flow</td><td style="padding:4px 8px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums">$890M</td><td style="padding:4px 8px;text-align:right;color:#6B7280;font-variant-numeric:tabular-nums">$745M</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#16A34A">+19.5%</td></tr>
</table>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">PairedKVTable</div><div class="item-desc">4 columns — CIQ density</div><div class="item-insp">S&P Capital IQ</div></div>
<div class="item-demo">
<table style="width:100%;border-collapse:collapse;font-size:9px">
<tr style="border-bottom:1px solid #F3F4F6">
  <td style="padding:3px 6px;color:#64748B;width:18%">Gross Margin</td><td style="padding:3px 6px;font-weight:700;width:32%;font-variant-numeric:tabular-nums">42.3%</td>
  <td style="padding:3px 6px;color:#64748B;width:18%;border-left:1px solid #E2E8F0">Current Ratio</td><td style="padding:3px 6px;font-weight:700;width:32%;font-variant-numeric:tabular-nums">1.82x</td>
</tr>
<tr style="border-bottom:1px solid #F3F4F6">
  <td style="padding:3px 6px;color:#64748B">Op Margin</td><td style="padding:3px 6px;font-weight:700;font-variant-numeric:tabular-nums">14.2%</td>
  <td style="padding:3px 6px;color:#64748B;border-left:1px solid #E2E8F0">Quick Ratio</td><td style="padding:3px 6px;font-weight:700;font-variant-numeric:tabular-nums">1.14x</td>
</tr>
<tr style="border-bottom:1px solid #F3F4F6">
  <td style="padding:3px 6px;color:#64748B">Net Margin</td><td style="padding:3px 6px;font-weight:700;font-variant-numeric:tabular-nums">6.6%</td>
  <td style="padding:3px 6px;color:#64748B;border-left:1px solid #E2E8F0">D/E Ratio</td><td style="padding:3px 6px;font-weight:700;color:#D97706;font-variant-numeric:tabular-nums">187%</td>
</tr>
<tr>
  <td style="padding:3px 6px;color:#64748B">ROE</td><td style="padding:3px 6px;font-weight:700;font-variant-numeric:tabular-nums">18.4%</td>
  <td style="padding:3px 6px;color:#64748B;border-left:1px solid #E2E8F0">Int. Coverage</td><td style="padding:3px 6px;font-weight:700;font-variant-numeric:tabular-nums">4.2x</td>
</tr>
</table>
</div></div>

</div><!-- /tables -->

<!-- ════════════════════════════════════════════ -->
<!-- NARRATIVES -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="narratives">
<div class="group-hdr"><div class="group-num" style="color:#6D28D9">06</div><div class="group-title">Narrative Frameworks</div><div class="group-line" style="background:#6D28D9"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">BullBearFraming</div><div class="item-desc">Two-column positive/negative analysis</div><div class="item-insp">Sell-side equity research</div></div>
<div class="item-demo">
<div class="col-2">
  <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:5px;padding:8px 10px">
    <div style="font-size:8px;font-weight:700;color:#16A34A;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Bull Case</div>
    <div style="font-size:9px;color:#374151;line-height:1.5">
      <div style="padding:2px 0">✓ 8 consecutive earnings beats</div>
      <div style="padding:2px 0">✓ FCF up 19.5% YoY to $890M</div>
      <div style="padding:2px 0">✓ No active SCAs or derivatives</div>
      <div style="padding:2px 0">✓ Insider buying exceeds selling 3:1</div>
    </div>
  </div>
  <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:5px;padding:8px 10px">
    <div style="font-size:8px;font-weight:700;color:#DC2626;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Bear Case</div>
    <div style="font-size:9px;color:#374151;line-height:1.5">
      <div style="padding:2px 0">✗ Goodwill 48% of total assets — impairment risk</div>
      <div style="padding:2px 0">✗ EBITDA margin compressed 280bps</div>
      <div style="padding:2px 0">✗ $2.1B near-term debt maturities</div>
      <div style="padding:2px 0">✗ 3 peer companies sued for similar practices</div>
    </div>
  </div>
</div>
</div></div>

</div><!-- /narratives -->

<!-- ════════════════════════════════════════════ -->
<!-- CHARTS (placeholder — these are matplotlib) -->
<!-- ════════════════════════════════════════════ -->
<div class="group" id="charts">
<div class="group-hdr"><div class="group-num" style="color:#DC2626">07</div><div class="group-title">Full Charts (Matplotlib/SVG)</div><div class="group-line" style="background:#DC2626"></div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">StockPerformanceChart</div><div class="item-desc">Price + sector overlay + drops + volume</div><div class="item-insp">Bloomberg equity terminal</div></div>
<div class="item-demo">
<div style="background:#1A1A2E;border-radius:6px;padding:12px 16px;position:relative;height:100px">
  <div style="font-size:8px;font-weight:700;color:#D4A843;letter-spacing:0.5px">RPM — 2 YEAR PERFORMANCE</div>
  <div style="font-size:7px;color:#6B7280;margin-top:2px">Weekly · Sector ETF overlay · Numbered drop events</div>
  <svg width="100%" height="50" viewBox="0 0 400 50" style="margin-top:8px">
    <path d="M0,40 L40,38 L80,35 L120,30 L140,38 L160,42 L200,35 L240,28 L280,20 L320,15 L360,18 L400,12" fill="none" stroke="#E8903A" stroke-width="2.5" opacity="0.9"/>
    <path d="M0,40 L40,38 L80,35 L120,30 L140,38 L160,42 L200,35 L240,28 L280,20 L320,15 L360,18 L400,12 L400,50 L0,50Z" fill="#E8903A" opacity="0.08"/>
    <path d="M0,38 L40,37 L80,36 L120,34 L160,35 L200,33 L240,30 L280,28 L320,25 L360,24 L400,22" fill="none" stroke="#6B7280" stroke-width="1" stroke-dasharray="4,3" opacity="0.5"/>
    <circle cx="140" cy="38" r="8" fill="#DC2626" opacity="0.9"/><text x="140" y="41" text-anchor="middle" fill="white" font-size="7" font-weight="700">1</text>
    <circle cx="240" cy="28" r="8" fill="#F59E0B" opacity="0.9"/><text x="240" y="31" text-anchor="middle" fill="white" font-size="7" font-weight="700">2</text>
  </svg>
</div>
<div style="margin-top:4px;font-size:8px;color:#94A3B8">Drop legend table renders below with: # | Date | Drop% | Duration | Catalyst | Category</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">RadarChart</div><div class="item-desc">10-spoke factor risk profile</div><div class="item-insp">Economist radars</div></div>
<div class="item-demo">
<div style="text-align:center">
<svg width="200" height="200" viewBox="0 0 200 200">
  <polygon points="100,20 160,45 180,100 160,155 100,180 40,155 20,100 40,45" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,40 145,57 162,100 145,143 100,162 55,143 38,100 55,57" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,60 130,70 142,100 130,130 100,142 70,130 58,100 70,70" fill="none" stroke="#E2E8F0" stroke-width="0.5"/>
  <polygon points="100,35 148,56 165,100 148,144 100,165 52,144 35,100 52,56" fill="#0F172A" opacity="0.15" stroke="#D4A843" stroke-width="1.5"/>
  <text x="100" y="14" text-anchor="middle" font-size="6" fill="#64748B">Litigation</text>
  <text x="170" y="42" text-anchor="start" font-size="6" fill="#64748B">Stock</text>
  <text x="188" y="102" text-anchor="start" font-size="6" fill="#64748B">Financial</text>
  <text x="165" y="162" text-anchor="start" font-size="6" fill="#64748B">Governance</text>
  <text x="100" y="194" text-anchor="middle" font-size="6" fill="#64748B">Operational</text>
  <text x="30" y="162" text-anchor="end" font-size="6" fill="#64748B">Regulatory</text>
  <text x="12" y="102" text-anchor="end" font-size="6" fill="#64748B">IPO/M&A</text>
  <text x="30" y="42" text-anchor="end" font-size="6" fill="#64748B">Insider</text>
</svg>
</div>
</div></div>

<div class="item">
<div class="item-hdr"><div class="item-name">WaterfallChart</div><div class="item-desc">Factor deductions from 100</div><div class="item-insp">McKinsey waterfall</div></div>
<div class="item-demo">
<div style="display:flex;align-items:flex-end;gap:3px;height:80px;padding:0 4px">
  <div style="flex:1;text-align:center"><div style="background:#16A34A;height:80px;border-radius:3px 3px 0 0;display:flex;align-items:flex-end;justify-content:center;padding-bottom:2px"><span style="font-size:6px;color:white;font-weight:700">100</span></div><div style="font-size:5px;color:#64748B;margin-top:2px">Start</div></div>
  <div style="flex:1;text-align:center"><div style="background:#DC2626;height:12px;border-radius:3px 3px 0 0;margin-top:68px"></div><div style="font-size:5px;color:#64748B;margin-top:2px">F1 -3</div></div>
  <div style="flex:1;text-align:center"><div style="background:#DC2626;height:8px;border-radius:3px 3px 0 0;margin-top:72px"></div><div style="font-size:5px;color:#64748B;margin-top:2px">F2 -2</div></div>
  <div style="flex:1;text-align:center"><div style="background:#F59E0B;height:4px;border-radius:3px 3px 0 0;margin-top:76px"></div><div style="font-size:5px;color:#64748B;margin-top:2px">F3 -1</div></div>
  <div style="flex:1;text-align:center"><div style="background:#E5E7EB;height:0px;margin-top:80px"></div><div style="font-size:5px;color:#64748B;margin-top:2px">F4 0</div></div>
  <div style="flex:1;text-align:center"><div style="background:#DC2626;height:16px;border-radius:3px 3px 0 0;margin-top:64px"></div><div style="font-size:5px;color:#64748B;margin-top:2px">F5 -4</div></div>
  <div style="flex:1;text-align:center"><div style="background:#16A34A;height:60px;border-radius:3px 3px 0 0;margin-top:20px;display:flex;align-items:flex-end;justify-content:center;padding-bottom:2px"><span style="font-size:6px;color:white;font-weight:700">90</span></div><div style="font-size:5px;color:#64748B;margin-top:2px">Score</div></div>
</div>
</div></div>

</div><!-- /charts -->

</div><!-- /gallery -->

<div class="footer">
<p><strong>Design Gallery</strong> — Live rendered examples of all visual elements</p>
<p style="margin-top:4px">Review, approve, or modify. Each element has a standardized name for reference.</p>
</div>
</body></html>'''

    return html


if __name__ == "__main__":
    html = build()
    Path("output/DESIGN_GALLERY.html").write_text(html)
    print("Generated: output/DESIGN_GALLERY.html")
