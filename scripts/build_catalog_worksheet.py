#!/usr/bin/env python3
"""Generate a D&O worksheet using the Card Catalog design language, from real state.json data."""

import json
import sys
from pathlib import Path

def sv(val):
    """Extract value from SourcedValue or plain value."""
    if isinstance(val, dict):
        return val.get("value", val.get("v"))
    return val

def fmt_money(val):
    if val is None: return "N/A"
    v = float(val)
    if abs(v) >= 1e12: return f"${v/1e12:.1f}T"
    if abs(v) >= 1e9: return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6: return f"${v/1e6:.0f}M"
    if abs(v) >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:,.0f}"

def fmt_pct(val):
    if val is None: return "N/A"
    return f"{float(val):.1f}%"

def fmt_num(val, decimals=1):
    if val is None: return "N/A"
    v = float(val)
    if abs(v) >= 1e6: return f"{v/1e6:.1f}M"
    if abs(v) >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:,.{decimals}f}"

def fmt_ratio(val):
    if val is None: return "N/A"
    return f"{float(val):.2f}x"

def safe_get(obj, *keys, default=None):
    """Nested safe get."""
    for k in keys:
        if obj is None: return default
        if isinstance(obj, dict):
            obj = obj.get(k)
        else:
            obj = getattr(obj, k, None)
    if obj is None: return default
    return sv(obj) if isinstance(obj, dict) and "value" in obj else obj


def build_worksheet(state_path: str, output_path: str):
    with open(state_path) as f:
        state = json.load(f)

    ticker = state.get("ticker", "???")
    company = state.get("company", {}) or {}
    scoring = state.get("scoring", {}) or {}
    extracted = state.get("extracted", {}) or {}
    analysis = state.get("analysis", {}) or {}
    acquired = state.get("acquired_data", {}) or {}
    hazard = state.get("hazard_profile", {}) or {}
    exec_summary = state.get("executive_summary", {}) or {}
    classification = state.get("classification", {}) or {}

    # Identity
    ident = company.get("identity", {}) or {}
    legal_name = sv(ident.get("legal_name", "")) or ticker
    short_name = legal_name.split(",")[0].split(" Inc")[0].split(" Corp")[0].split("/")[0].strip()
    sic = sv(ident.get("sic_code")) or ""
    exchange = sv(ident.get("exchange")) or ""
    state_inc = sv(ident.get("state_of_incorporation")) or ""
    cik = sv(ident.get("cik")) or ""
    fye = sv(ident.get("fiscal_year_end")) or ""

    # Financials
    mcap = sv(company.get("market_cap")) or 0
    employees = sv(company.get("employee_count")) or 0

    # Scoring
    quality_score = scoring.get("quality_score", 0)
    tier_info = scoring.get("tier", {}) or {}
    tier_name = tier_info.get("tier", "N/A") if isinstance(tier_info, dict) else str(tier_info)
    tier_action = tier_info.get("action", "") if isinstance(tier_info, dict) else ""
    prob_range = tier_info.get("probability_range", "") if isinstance(tier_info, dict) else ""
    factor_scores = scoring.get("factor_scores", []) or []
    red_flags = scoring.get("red_flags", []) or []
    claim_prob = scoring.get("claim_probability", {}) or {}
    severity = scoring.get("severity_scenarios", {}) or {}
    tower = scoring.get("tower_recommendation", {}) or {}
    calibration = scoring.get("calibration_notes", []) or []

    # Extracted financials
    fin = extracted.get("financials", {}) or {}
    xbrl = extracted.get("xbrl_data", {}) or {}
    governance = extracted.get("governance", {}) or {}
    litigation = extracted.get("litigation", {}) or {}

    # Revenue from XBRL or extracted
    revenue = None
    if xbrl and isinstance(xbrl, dict):
        for key in ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"]:
            if key in xbrl:
                vals = xbrl[key]
                if isinstance(vals, list) and vals:
                    revenue = vals[0].get("value") if isinstance(vals[0], dict) else vals[0]
                    break
                elif isinstance(vals, (int, float)):
                    revenue = vals
                    break

    # Stock data
    stock = acquired.get("stock_data", {}) or {}
    price = None
    if isinstance(stock, dict):
        price = stock.get("current_price") or stock.get("price")

    # Color scheme from catalog
    COLORS = {
        "bg": "#F8FAFC", "card_bg": "#FFFFFF", "border": "#E2E8F0",
        "text": "#1E293B", "muted": "#64748B", "faint": "#94A3B8",
        "dash": "#0F172A", "brief": "#6D28D9", "company": "#0369A1",
        "market": "#EA580C", "financial": "#059669", "governance": "#D97706",
        "litigation": "#DC2626", "industry": "#7C3AED", "scoring": "#0891B2",
        "uw": "#4338CA", "meeting": "#BE185D", "audit": "#64748B",
        "red": "#DC2626", "amber": "#F59E0B", "green": "#16A34A", "blue": "#1D4ED8",
    }

    # Build HTML
    html = []

    def card_start(num, title, color, desc=""):
        html.append(f'<div class="card" style="border-color:{color}40">')
        html.append(f'<div class="card-hdr" style="background:{color}">')
        html.append(f'<div class="card-num">{num:02d}</div>')
        html.append(f'<div class="card-title">{title}</div>')
        html.append(f'</div>')
        if desc:
            html.append(f'<div class="card-desc">{desc}</div>')

    def card_end():
        html.append('</div>')

    def sub_block(letter, name, content_html, typ=""):
        html.append(f'<div class="sub-block">')
        html.append(f'<div class="sub-hdr"><span class="sub-ltr">{letter}</span><span class="sub-nm">{name}</span>')
        if typ:
            html.append(f'<span class="sub-tp">{typ}</span>')
        html.append(f'</div>')
        html.append(f'<div class="sub-content">{content_html}</div>')
        html.append(f'</div>')

    def kv_row(label, value, color=""):
        style = f' style="color:{color}"' if color else ""
        return f'<div class="kv"><span class="kv-l">{label}</span><span class="kv-v"{style}>{value}</span></div>'

    def metric_card(title, value, subtitle="", color="#0F172A", bg="#F8FAFC", border="#E2E8F0"):
        return f'''<div class="mini" style="background:{bg};border-color:{border}">
<div class="mini-t" style="color:{color}">{title}</div>
<div class="mini-v">{value}</div>
{f'<div class="mini-s">{subtitle}</div>' if subtitle else ''}
</div>'''

    def section_start(sid, num, title, color):
        html.append(f'<div class="section" id="{sid}">')
        html.append(f'<div class="sec-hdr"><div class="sec-num" style="color:{color}">{num}</div><div class="sec-title">{title}</div></div>')

    def section_end():
        html.append('</div>')

    # ── Page structure ──
    html.append(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{ticker} — D&O Underwriting Worksheet</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,-apple-system,sans-serif;background:{COLORS["bg"]};color:{COLORS["text"]}}}

/* Header */
.header{{background:{COLORS["dash"]};color:white;padding:16px 24px;display:flex;align-items:center;gap:16px}}
.header-logo{{width:44px;height:44px;border-radius:10px;background:rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;color:white}}
.header-info{{flex:1}}
.header-name{{font-size:18px;font-weight:800}}
.header-meta{{font-size:10px;color:rgba(255,255,255,0.6);margin-top:2px}}
.header-score{{text-align:right}}
.header-score-num{{font-size:28px;font-weight:900}}
.header-score-tier{{font-size:11px;font-weight:700;padding:2px 10px;border-radius:6px;display:inline-block;margin-top:3px}}

/* Nav */
.nav{{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.97);backdrop-filter:blur(12px);border-bottom:1px solid #E2E8F0;padding:8px 16px;display:flex;flex-wrap:wrap;justify-content:center;gap:5px}}
.nav a{{font-size:10px;font-weight:600;padding:4px 10px;border-radius:5px;text-decoration:none;color:white}}

/* Section */
.section{{max-width:1100px;margin:0 auto;padding:32px 24px 12px}}
.sec-hdr{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
.sec-num{{font-size:36px;font-weight:900;line-height:1}}
.sec-title{{font-size:18px;font-weight:800}}

/* Card */
.card{{background:white;border:2px solid #CBD5E1;border-radius:12px;margin-bottom:14px;overflow:hidden}}
.card-hdr{{padding:10px 14px;display:flex;align-items:center;gap:10px}}
.card-num{{font-size:18px;font-weight:900;color:rgba(255,255,255,0.3);font-family:'JetBrains Mono',monospace;width:30px}}
.card-title{{font-size:13px;font-weight:800;color:white;flex:1}}
.card-desc{{font-size:10px;color:#64748B;padding:6px 14px;border-bottom:1px solid #F1F5F9;line-height:1.4}}

/* Sub-block */
.sub-block{{border-bottom:1px solid #F1F5F9;padding:8px 14px}}
.sub-block:last-child{{border-bottom:none}}
.sub-hdr{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.sub-ltr{{width:18px;height:18px;border-radius:4px;background:#E2E8F0;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:800;color:#475569}}
.sub-nm{{font-size:11px;font-weight:700;flex:1}}
.sub-tp{{font-size:7px;font-weight:700;padding:2px 6px;border-radius:3px;background:#F1F5F9;color:#475569;text-transform:uppercase}}
.sub-content{{font-size:10px;line-height:1.5;color:#334155}}

/* KV rows */
.kv{{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #FAFAFA}}
.kv:last-child{{border-bottom:none}}
.kv-l{{color:#64748B}}
.kv-v{{font-weight:600;font-variant-numeric:tabular-nums}}

/* Mini metric cards */
.mini-row{{display:grid;gap:4px;margin:4px 0}}
.mini-row-6{{grid-template-columns:repeat(6,1fr)}}
.mini-row-4{{grid-template-columns:repeat(4,1fr)}}
.mini-row-3{{grid-template-columns:repeat(3,1fr)}}
.mini-row-2{{grid-template-columns:repeat(2,1fr)}}
.mini{{border-radius:5px;padding:6px 8px;border:1px solid #E2E8F0;font-size:9px}}
.mini-t{{font-size:7px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px}}
.mini-v{{font-size:13px;font-weight:800;line-height:1}}
.mini-s{{font-size:7.5px;color:#6B7280;margin-top:2px}}

/* Table */
.tbl{{width:100%;border-collapse:collapse;font-size:9.5px;margin:4px 0}}
.tbl th{{background:#F9FAFB;padding:4px 8px;text-align:left;font-weight:700;color:#374151;border-bottom:1px solid #E5E7EB;font-size:8.5px}}
.tbl td{{padding:3px 8px;border-bottom:1px solid #F3F4F6;color:#4B5563}}
.tbl tr:hover{{background:#FAFBFC}}

/* Alert bar */
.alert{{border-radius:5px;padding:8px 12px;margin:4px 0;font-size:10px}}
.alert-red{{background:#FEF2F2;border:1px solid #FECACA;color:#991B1B}}
.alert-green{{background:#F0FDF4;border:1px solid #BBF7D0;color:#065F46}}
.alert-amber{{background:#FFFBEB;border:1px solid #FDE68A;color:#92400E}}
.pill{{display:inline-block;font-size:8px;font-weight:700;padding:2px 8px;border-radius:10px}}
.pill-red{{background:#DC2626;color:white}}
.pill-green{{background:#D1FAE5;color:#065F46}}
.pill-amber{{background:#F59E0B;color:white}}

/* Badge */
.badge{{display:inline-block;font-size:8px;font-weight:700;padding:1px 6px;border-radius:3px}}

/* Narrative */
.narrative{{font-size:10.5px;line-height:1.6;color:#334155;padding:6px 0}}

/* Factor bar */
.factor-bar{{height:8px;border-radius:4px;background:#E5E7EB}}
.factor-fill{{height:8px;border-radius:4px}}

.footer{{text-align:center;padding:40px 24px;color:#94A3B8;font-size:11px;border-top:1px solid #E2E8F0;margin-top:40px;background:white}}
@media print{{.nav{{display:none}}.card{{break-inside:avoid}}}}
</style></head><body>
''')

    # ── Header ──
    tier_bg = {"WIN": "#16A34A", "WANT": "#059669", "WRITE": "#D97706", "WATCH": "#EA580C", "WALK": "#DC2626", "NO_TOUCH": "#991B1B"}.get(tier_name, "#64748B")
    html.append(f'''<div class="header">
<div class="header-logo">{ticker[:2]}</div>
<div class="header-info">
<div class="header-name">{legal_name}</div>
<div class="header-meta">{ticker} · SIC {sic} · {exchange} · {state_inc} · CIK {cik}</div>
</div>
<div class="header-score">
<div class="header-score-num" style="color:{tier_bg}">{quality_score:.0f}</div>
<div class="header-score-tier" style="background:{tier_bg};color:white">{tier_name}</div>
</div>
</div>''')

    # ── Nav ──
    nav_items = [
        ("sec-0", "0 Dashboard", COLORS["dash"]),
        ("sec-1", "1 Exec Brief", COLORS["brief"]),
        ("sec-2", "2 Company", COLORS["company"]),
        ("sec-4", "4 Financial", COLORS["financial"]),
        ("sec-5", "5 Governance", COLORS["governance"]),
        ("sec-6", "6 Litigation", COLORS["litigation"]),
        ("sec-8", "8 Scoring", COLORS["scoring"]),
    ]
    html.append('<div class="nav">')
    for sid, label, color in nav_items:
        html.append(f'<a href="#{sid}" style="background:{color}">{label}</a>')
    html.append('</div>')

    # ════════════════════════════════════════════
    # SECTION 0: DECISION DASHBOARD
    # ════════════════════════════════════════════
    section_start("sec-0", "0", "Decision Dashboard", COLORS["dash"])

    card_start(0, "Decision Dashboard", COLORS["dash"],
               "One-page executive overview — financial snapshot, litigation status, key risk findings.")

    # Mini cards
    mcap_label = "Large Cap" if mcap and mcap > 10e9 else "Mid Cap" if mcap and mcap > 2e9 else "Small Cap"
    cards_html = '<div class="mini-row mini-row-6">'
    cards_html += metric_card("Market Cap", fmt_money(mcap), mcap_label, "#7C3AED", "#F5F3FF", "#DDD6FE")
    cards_html += metric_card("Stock Price", f"${price:.2f}" if price else "N/A", "", "#C2410C", "#FFF7ED", "#FED7AA")
    cards_html += metric_card("Revenue", fmt_money(revenue), "Annual (XBRL)", "#16A34A", "#F0FDF4", "#BBF7D0")
    cards_html += metric_card("Employees", f"{employees:,}" if employees else "N/A", "", "#DC2626", "#FEF2F2", "#FECACA")

    # Balance sheet from XBRL
    total_assets = None
    if xbrl:
        for k in ["Assets"]:
            v = xbrl.get(k)
            if isinstance(v, list) and v:
                total_assets = v[0].get("value") if isinstance(v[0], dict) else v[0]
    cards_html += metric_card("Total Assets", fmt_money(total_assets), "", "#16A34A", "#F0FDF4", "#BBF7D0")
    cards_html += metric_card("Quality Score", f"{quality_score:.0f}/100", tier_name, "#1D4ED8", "#EFF6FF", "#BFDBFE")
    cards_html += '</div>'
    sub_block("B", "Financial Snapshot (6 Mini-Cards)", cards_html, "CARDS")

    # Litigation status
    lit_cases = litigation.get("cases", []) or []
    active_count = sum(1 for c in lit_cases if isinstance(c, dict) and c.get("status", "").lower() in ("active", "pending", "open"))
    if active_count > 0:
        lit_html = f'<div class="alert alert-red"><span class="pill pill-red">{active_count} Active Cases</span>'
        for c in lit_cases[:3]:
            if isinstance(c, dict):
                name = c.get("case_name", c.get("name", "Unknown"))
                lit_html += f'<div style="margin-top:4px">🔴 <b>{name}</b></div>'
        lit_html += '</div>'
    else:
        lit_html = '<div class="alert alert-green"><span class="pill pill-green">No Active Litigation</span> Clean litigation profile.</div>'
    sub_block("C", "Litigation & Regulatory Status", lit_html, "ALERT")

    # Key Risk Findings
    rfs = red_flags or []
    if rfs:
        findings_html = '<div style="background:#FEF2F2;padding:4px 8px;border-radius:4px 4px 0 0"><span style="font-size:9px;font-weight:700;color:#DC2626">Key Risk Findings</span> <span class="pill pill-red" style="font-size:7px">' + str(len(rfs)) + ' flags</span></div>'
        findings_html += '<div style="background:white;border:1px solid #FECACA;border-top:none;border-radius:0 0 4px 4px;padding:6px 8px">'
        for i, rf in enumerate(rfs[:8], 1):
            if isinstance(rf, dict):
                name = rf.get("name", rf.get("flag", "Unknown"))
                desc = rf.get("description", rf.get("evidence", ""))
                findings_html += f'<div style="display:flex;gap:6px;padding:4px 0;border-bottom:1px solid #F3F4F6">'
                findings_html += f'<div style="width:16px;height:16px;border-radius:8px;background:#DC2626;color:white;font-size:7px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{i}</div>'
                findings_html += f'<div><strong>{name}</strong>'
                if desc:
                    findings_html += f'<div style="font-size:9px;color:#6B7280;margin-top:1px">{str(desc)[:200]}</div>'
                findings_html += '</div></div>'
            elif isinstance(rf, str):
                findings_html += f'<div style="padding:3px 0">🔴 {rf}</div>'
        findings_html += '</div>'
    else:
        findings_html = '<div class="alert alert-green">No critical risk flags identified — clean risk profile.</div>'
    sub_block("E", "Key Risk Findings", findings_html, "ALERT")

    # UW Priority metrics
    uw_html = '<div class="mini-row mini-row-4">'
    uw_html += metric_card("Quality Score", f"{quality_score:.0f}", f"{tier_name} tier", tier_bg, "white", "#E5E7EB")
    uw_html += metric_card("Claim Probability", claim_prob.get("range_high_pct", "N/A") if isinstance(claim_prob, dict) else "N/A",
                           claim_prob.get("band", "") if isinstance(claim_prob, dict) else "", "#D97706", "white", "#E5E7EB")
    prob_low = claim_prob.get("range_low_pct", "?") if isinstance(claim_prob, dict) else "?"
    prob_high = claim_prob.get("range_high_pct", "?") if isinstance(claim_prob, dict) else "?"
    uw_html += metric_card("Probability Range", f"{prob_low}%-{prob_high}%", "", "#4338CA", "white", "#E5E7EB")
    uw_html += metric_card("Red Flags", str(len(rfs)), "critical flags" if rfs else "none", "#DC2626" if rfs else "#16A34A", "white", "#E5E7EB")
    uw_html += '</div>'
    sub_block("F", "Underwriting Priority Metrics", uw_html, "CARDS")

    card_end()
    section_end()

    # ════════════════════════════════════════════
    # SECTION 1: EXECUTIVE BRIEF
    # ════════════════════════════════════════════
    section_start("sec-1", "1", "Executive Summary & Recommendation", COLORS["brief"])

    card_start(1, "Recommendation & Red Flags", COLORS["brief"])
    # Recommendation box
    rec_html = f'''<div style="background:{COLORS["dash"]};color:white;padding:8px 12px;border-radius:5px;display:flex;justify-content:space-between;align-items:center">
<div><span style="font-size:14px;font-weight:900">{tier_name}</span> <span style="font-size:10px;opacity:0.7">— {tier_action}</span></div>
<div><span style="font-size:10px;opacity:0.7">Probability:</span> <span style="font-weight:700">{prob_range}</span></div>
</div>'''
    sub_block("A", "Recommendation", rec_html, "VERDICT")

    # Red flags
    if rfs:
        rf_html = '<div class="alert alert-red">'
        for rf in rfs[:5]:
            if isinstance(rf, dict):
                rf_html += f'<div style="margin:3px 0">🔴 <strong>{rf.get("name", rf.get("flag", ""))}</strong></div>'
            elif isinstance(rf, str):
                rf_html += f'<div style="margin:3px 0">🔴 {rf}</div>'
        rf_html += '</div>'
        sub_block("B", "Critical Red Flags", rf_html, "ALERT")
    card_end()

    # Thesis card
    card_start(2, "Risk Thesis & Commentary", COLORS["brief"])
    thesis = exec_summary.get("thesis", "") or exec_summary.get("narrative", "") or ""
    if isinstance(thesis, dict):
        thesis = thesis.get("value", str(thesis))
    if thesis:
        sub_block("A", "Risk Thesis", f'<div class="narrative">{str(thesis)[:1500]}</div>', "NARRATIVE")
    else:
        sub_block("A", "Risk Thesis", '<div class="narrative" style="color:#94A3B8">Executive summary not yet generated. Run pipeline with LLM synthesis enabled.</div>', "NARRATIVE")
    card_end()
    section_end()

    # ════════════════════════════════════════════
    # SECTION 2: COMPANY
    # ════════════════════════════════════════════
    section_start("sec-2", "2", "Company Operations & Profile", COLORS["company"])

    card_start(3, "Business Description & Revenue Model", COLORS["company"])
    bus_desc = sv(company.get("business_description")) or sv(company.get("business_model_description")) or ""
    if bus_desc:
        sub_block("A", "Business Description", f'<div class="narrative">{str(bus_desc)[:1000]}</div>', "NARRATIVE")

    # Classification KV
    kv_html = kv_row("Ticker", ticker)
    kv_html += kv_row("Exchange", exchange)
    kv_html += kv_row("SIC Code", sic)
    kv_html += kv_row("State of Incorporation", state_inc)
    kv_html += kv_row("Filer Category", sv(company.get("filer_category")) or "N/A")
    kv_html += kv_row("Years Public", str(sv(company.get("years_public")) or "N/A"))
    kv_html += kv_row("GICS Code", sv(company.get("gics_code")) or "N/A")
    sub_block("B", "Classification", kv_html, "KV")
    card_end()

    # Concentration
    card_start(5, "Concentration Risk", COLORS["company"])
    cust = company.get("customer_concentration", {}) or {}
    supp = company.get("supplier_concentration", {}) or {}
    conc_html = kv_row("Customer Concentration", sv(cust) if isinstance(cust, (str, dict)) and not isinstance(cust, dict) else "See detail" if cust else "Not disclosed")
    conc_html += kv_row("Supplier Concentration", sv(supp) if isinstance(supp, (str, dict)) and not isinstance(supp, dict) else "See detail" if supp else "Not disclosed")
    sub_block("A", "Concentration Assessment", conc_html, "KV")

    geo = company.get("geographic_footprint", {}) or {}
    if geo and isinstance(geo, dict):
        geo_html = ""
        for region, detail in list(geo.items())[:6]:
            if isinstance(detail, dict):
                detail = sv(detail) or str(detail)
            geo_html += kv_row(str(region), str(detail)[:80])
        if geo_html:
            sub_block("B", "Geographic Footprint", geo_html, "TABLE")
    card_end()

    section_end()

    # ════════════════════════════════════════════
    # SECTION 4: FINANCIAL
    # ════════════════════════════════════════════
    section_start("sec-4", "4", "Financial Analysis", COLORS["financial"])

    card_start(15, "Key Financial Metrics", COLORS["financial"])
    # XBRL metrics
    xbrl_metrics = {}
    if xbrl and isinstance(xbrl, dict):
        for concept, display in [
            ("Revenues", "Revenue"), ("NetIncomeLoss", "Net Income"),
            ("Assets", "Total Assets"), ("Liabilities", "Total Liabilities"),
            ("StockholdersEquity", "Equity"), ("CashAndCashEquivalentsAtCarryingValue", "Cash"),
            ("LongTermDebt", "Long-Term Debt"), ("OperatingIncomeLoss", "Operating Income"),
        ]:
            v = xbrl.get(concept)
            if isinstance(v, list) and v:
                val = v[0].get("value") if isinstance(v[0], dict) else v[0]
                if val is not None:
                    xbrl_metrics[display] = val

    if xbrl_metrics:
        fin_html = ""
        for label, val in xbrl_metrics.items():
            color = "#DC2626" if "Debt" in label or "Liabilities" in label else ""
            fin_html += kv_row(label, fmt_money(val), color)
        sub_block("A", "XBRL Financial Data (Audited)", fin_html, "TABLE")
    card_end()

    # Distress models
    card_start(17, "Distress & Forensic Models", COLORS["financial"])
    forensic = analysis.get("forensic_scores", {}) or {}
    if forensic:
        fhtml = ""
        for model in ["altman_z", "beneish_m", "piotroski_f", "ohlson_o"]:
            data = forensic.get(model, {})
            if isinstance(data, dict):
                score = data.get("score", data.get("value"))
                zone = data.get("zone", data.get("classification", ""))
                if score is not None:
                    zone_color = {"SAFE": "#16A34A", "GREY": "#D97706", "DISTRESS": "#DC2626"}.get(str(zone).upper(), "#64748B")
                    fhtml += kv_row(model.replace("_", " ").title(), f'{score:.2f} <span class="badge" style="background:{zone_color};color:white">{zone}</span>')
        if fhtml:
            sub_block("A", "Distress Model Scores", fhtml, "TABLE")
    else:
        sub_block("A", "Distress Model Scores", '<span style="color:#94A3B8">Not yet computed</span>', "TABLE")
    card_end()

    section_end()

    # ════════════════════════════════════════════
    # SECTION 5: GOVERNANCE
    # ════════════════════════════════════════════
    section_start("sec-5", "5", "People & Governance", COLORS["governance"])

    card_start(22, "Board Composition", COLORS["governance"])
    board = governance.get("board_members", []) or []
    if board:
        tbl_html = '<table class="tbl"><tr><th>Name</th><th>Title</th><th>Independent</th></tr>'
        for member in board[:15]:
            if isinstance(member, dict):
                name = member.get("name", sv(member.get("name", "")))
                title = member.get("title", sv(member.get("title", "")))
                ind = member.get("is_independent", member.get("independent", ""))
                tbl_html += f'<tr><td><strong>{name}</strong></td><td>{title}</td><td>{ind}</td></tr>'
        tbl_html += '</table>'
        sub_block("A", "Board of Directors", tbl_html, "TABLE")
    else:
        sub_block("A", "Board of Directors", '<span style="color:#94A3B8">Board data not yet extracted</span>', "TABLE")
    card_end()
    section_end()

    # ════════════════════════════════════════════
    # SECTION 6: LITIGATION
    # ════════════════════════════════════════════
    section_start("sec-6", "6", "Legal & Litigation", COLORS["litigation"])

    card_start(27, "Active Litigation & Defense", COLORS["litigation"])
    if lit_cases:
        cases_html = f'<div style="margin-bottom:6px"><span class="pill {"pill-red" if active_count > 0 else "pill-green"}">{len(lit_cases)} Total Cases</span> <span class="pill {"pill-red" if active_count > 0 else "pill-green"}">{active_count} Active</span></div>'
        cases_html += '<table class="tbl"><tr><th>Case</th><th>Status</th><th>Type</th></tr>'
        for c in lit_cases[:10]:
            if isinstance(c, dict):
                name = c.get("case_name", c.get("name", "Unknown"))
                status = c.get("status", "Unknown")
                ctype = c.get("case_type", c.get("type", ""))
                status_color = "#DC2626" if status.lower() in ("active", "pending") else "#F59E0B" if status.lower() == "settled" else "#16A34A"
                cases_html += f'<tr><td><strong>{name}</strong></td><td><span class="badge" style="background:{status_color};color:white">{status}</span></td><td>{ctype}</td></tr>'
        cases_html += '</table>'
        sub_block("A", "Case Summary", cases_html, "TABLE")
    else:
        sub_block("A", "Case Summary", '<div class="alert alert-green">No litigation matters identified.</div>', "ALERT")
    card_end()
    section_end()

    # ════════════════════════════════════════════
    # SECTION 8: SCORING
    # ════════════════════════════════════════════
    section_start("sec-8", "8", "Scoring & Underwriting", COLORS["scoring"])

    # Factor Scoring
    card_start(34, "Tier & Factor Scoring", COLORS["scoring"])
    tier_html = f'''<div style="display:flex;gap:12px;align-items:center;padding:8px 0">
<div style="font-size:36px;font-weight:900;color:{tier_bg}">{quality_score:.0f}</div>
<div><div style="font-size:14px;font-weight:800">{tier_name}</div>
<div style="font-size:10px;color:#64748B">{tier_action}</div>
<div style="font-size:10px;color:#64748B">Probability: {prob_range}</div></div></div>'''
    sub_block("A", "Tier Classification", tier_html, "VERDICT")

    if factor_scores:
        ftbl = '<table class="tbl"><tr><th>Factor</th><th>Name</th><th>Points</th><th>Bar</th></tr>'
        for f in factor_scores:
            if isinstance(f, dict):
                fid = f.get("factor_id", f.get("id", ""))
                fname = f.get("name", fid)
                points = f.get("points") or f.get("score", 0) or 0
                max_pts = f.get("max_points") or f.get("max", 10) or 10
                pct = min(100, (float(points) / float(max_pts) * 100)) if max_pts else 0
                bar_color = "#16A34A" if pct < 30 else "#D97706" if pct < 60 else "#DC2626"
                ftbl += f'<tr><td><strong>{fid}</strong></td><td>{fname}</td><td>{points}/{max_pts}</td>'
                ftbl += f'<td><div class="factor-bar" style="width:80px"><div class="factor-fill" style="width:{pct}%;background:{bar_color}"></div></div></td></tr>'
        total_risk = scoring.get("total_risk_points", 0)
        ftbl += f'<tr style="font-weight:700;border-top:2px solid #E5E7EB"><td colspan="2">Total Risk Points</td><td colspan="2">{total_risk}</td></tr>'
        ftbl += '</table>'
        sub_block("B", "10-Factor Scoring", ftbl, "TABLE")
    card_end()

    # Loss Analysis
    card_start(35, "Loss Analysis & Scenarios", COLORS["scoring"])
    if isinstance(severity, dict) and severity:
        sev_html = ""
        for scenario_key in ["best_case", "base_case", "worst_case", "10th", "25th", "50th", "75th", "90th", "95th"]:
            s = severity.get(scenario_key)
            if isinstance(s, dict):
                label = scenario_key.replace("_", " ").title()
                est = s.get("estimated_loss") or s.get("settlement") or s.get("value")
                sev_html += kv_row(label, fmt_money(est) if est else "N/A")
        if sev_html:
            sub_block("A", "Severity Scenarios", sev_html, "TABLE")
    elif isinstance(severity, list) and severity:
        sev_html = ""
        for s in severity[:5]:
            if isinstance(s, dict):
                label = s.get("scenario", s.get("name", ""))
                est = s.get("estimated_loss") or s.get("settlement") or s.get("value")
                sev_html += kv_row(label, fmt_money(est) if est else "N/A")
        if sev_html:
            sub_block("A", "Severity Scenarios", sev_html, "TABLE")

    if isinstance(tower, dict) and tower:
        tw_html = ""
        for k, v in tower.items():
            if isinstance(v, (str, int, float)):
                tw_html += kv_row(k.replace("_", " ").title(), str(v))
        if tw_html:
            sub_block("B", "Tower Recommendation", tw_html, "KV")
    card_end()

    # Calibration
    card_start(38, "Underwriting Posture & Calibration", COLORS["scoring"])
    if calibration:
        cal_html = '<ul style="padding-left:16px;font-size:10px;color:#4B5563">'
        for note in calibration[:10]:
            if isinstance(note, str):
                cal_html += f'<li style="margin:2px 0">{note}</li>'
            elif isinstance(note, dict):
                cal_html += f'<li style="margin:2px 0">{note.get("note", note.get("text", str(note)))}</li>'
        cal_html += '</ul>'
        sub_block("A", "Calibration Notes", cal_html, "NARRATIVE")
    card_end()

    section_end()

    # Footer
    html.append(f'''<div class="footer">
<p><strong>{ticker} — D&O Underwriting Worksheet</strong> · Card Catalog Design Language v4</p>
<p>Generated from state.json · {len(CARDS)} card definitions available</p>
</div></body></html>''')

    # Write
    output = Path(output_path)
    output.write_text('\n'.join(html))
    print(f"Written {output} ({len(html)} lines)")


# Card count reference
CARDS = list(range(52))

if __name__ == "__main__":
    state_path = sys.argv[1] if len(sys.argv) > 1 else "output/RPM/state.json"
    ticker = Path(state_path).parent.name
    output_path = f"output/{ticker}/{ticker}_catalog_worksheet.html"
    build_worksheet(state_path, output_path)
