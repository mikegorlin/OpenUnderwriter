#!/usr/bin/env python3
"""Generate Card Tracker — checklist for every card showing status of redesign, data verification, QA."""

import json
import re
from pathlib import Path

# Card definitions from the catalog
CARDS = [
    # (id, section_num, section_name, card_title, template_file, sub_elements_count, data_sources)
    ("00", 0, "Overview", "Decision Dashboard", "page0_dashboard.html.j2", 7,
     ["XBRL", "yfinance", "Computed", "LLM", "Web", "SEC", "Supabase"]),
    ("01", 1, "Exec Brief", "Recommendation & Red Flags", "exec_brief.html.j2", 3,
     ["Computed", "LLM"]),
    ("02", 1, "Exec Brief", "Risk Thesis & Commentary", "exec_brief.html.j2", 2,
     ["LLM"]),
    ("03", 2, "Company", "Business Description & Revenue Model", "company.html.j2", 5,
     ["SEC", "LLM", "Computed"]),
    ("04", 2, "Company", "Revenue Deep Dive", "company.html.j2", 5,
     ["XBRL", "LLM"]),
    ("05", 2, "Company", "Concentration Risk", "company.html.j2", 4,
     ["LLM", "XBRL"]),
    ("06", 2, "Company", "Risk Factors & D&O Exposure", "company.html.j2", 4,
     ["SEC", "LLM", "Computed"]),
    ("07", 2, "Company", "10-K YoY & Peer SCA", "company.html.j2", 3,
     ["SEC", "LLM", "Supabase"]),
    ("08", 2, "Company", "Sector Risk, Regulatory & News", "company.html.j2", 3,
     ["Web", "LLM", "SEC"]),
    ("09", 3, "Stock & Market", "Stock Performance & Drop Investigation", "stock_market.html.j2", 4,
     ["yfinance", "Web", "Computed"]),
    ("10", 3, "Stock & Market", "Insider Trading & Scienter Risk", "stock_market.html.j2", 5,
     ["yfinance", "Computed"]),
    ("11", 3, "Stock & Market", "Technical Analysis Charts", "stock_market.html.j2", 5,
     ["yfinance", "Computed"]),
    ("12", 3, "Stock & Market", "Earnings & Guidance", "stock_market.html.j2", 5,
     ["yfinance", "LLM", "Computed"]),
    ("13", 3, "Stock & Market", "Analyst Coverage & Estimates", "stock_market.html.j2", 3,
     ["yfinance"]),
    ("14", 3, "Stock & Market", "Capital Returns, Sentiment & 8-K", "stock_market.html.j2", 4,
     ["yfinance", "SEC", "LLM", "Computed"]),
    ("15", 4, "Financial", "Annual Financial Comparison", "financial.html.j2", 1,
     ["XBRL"]),
    ("16", 4, "Financial", "Key Metrics & Quarterly Trends", "financial.html.j2", 4,
     ["XBRL", "yfinance", "Computed"]),
    ("17", 4, "Financial", "Distress & Forensic Models", "financial.html.j2", 5,
     ["XBRL", "Computed"]),
    ("18", 4, "Financial", "Audit & Tax Profile", "financial.html.j2", 4,
     ["XBRL", "SEC"]),
    ("19", 4, "Financial", "Debt, Liquidity & Balance Sheet Risk", "financial.html.j2", 7,
     ["XBRL", "LLM", "Computed"]),
    ("20", 4, "Financial", "Peer Benchmarking", "financial.html.j2", 3,
     ["yfinance", "XBRL", "Computed"]),
    ("21", 4, "Financial", "MD&A & Filing Analysis", "financial.html.j2", 3,
     ["SEC", "LLM"]),
    ("22", 5, "Governance", "Board Composition & Skills", "governance.html.j2", 6,
     ["SEC", "Computed"]),
    ("23", 5, "Governance", "Board Forensic Profiles", "governance.html.j2", 1,
     ["SEC", "Web", "LLM"]),
    ("24", 5, "Governance", "Officer Investigation & People Risk", "governance.html.j2", 4,
     ["Web", "SEC", "LLM"]),
    ("25", 5, "Governance", "Compensation & Ownership", "governance.html.j2", 5,
     ["SEC", "yfinance", "Web"]),
    ("26", 5, "Governance", "Prior Litigation & Governance Structure", "governance.html.j2", 4,
     ["Web", "SEC", "LLM"]),
    ("27", 6, "Litigation", "Active Litigation & Defense", "litigation.html.j2", 6,
     ["Supabase", "SEC", "Web", "LLM"]),
    ("28", 6, "Litigation", "Exposure Windows & SOL", "litigation.html.j2", 2,
     ["Computed", "SEC"]),
    ("29", 6, "Litigation", "SEC & Regulatory Enforcement", "litigation.html.j2", 2,
     ["SEC", "Web"]),
    ("30", 6, "Litigation", "Historical Litigation & Timeline", "litigation.html.j2", 3,
     ["SEC", "XBRL", "Web"]),
    ("31", 6, "Litigation", "Other Matters & Whistleblower", "litigation.html.j2", 2,
     ["SEC", "LLM", "Web"]),
    ("32", 7, "Industry", "Competitive & Strategic Position", "sector_industry.html.j2", 4,
     ["Computed", "LLM", "Supabase"]),
    ("33", 7, "Industry", "AI Risk & Biotech Module", "sector_industry.html.j2", 2,
     ["LLM", "SEC"]),
    ("34", 8, "Scoring", "Tier & Factor Scoring", "scoring.html.j2", 5,
     ["Computed"]),
    ("35", 8, "Scoring", "Loss Analysis & Scenarios", "scoring.html.j2", 3,
     ["Computed"]),
    ("36", 8, "Scoring", "Peril Assessment & Mapping", "scoring.html.j2", 3,
     ["Computed"]),
    ("37", 8, "Scoring", "Investigative Depth", "scoring.html.j2", 5,
     ["Computed"]),
    ("38", 8, "Scoring", "UW Posture & Calibration", "scoring.html.j2", 4,
     ["Computed", "LLM"]),
    ("39", 8, "Scoring", "Altman Z-Score & Distress Models", "scoring.html.j2", 3,
     ["XBRL", "Computed"]),
    ("40", 8, "Scoring", "Beneish M-Score (Manipulation)", "scoring.html.j2", 8,
     ["XBRL", "Computed"]),
    ("41", 8, "Scoring", "Piotroski F-Score (Health)", "scoring.html.j2", 3,
     ["XBRL", "Computed"]),
    ("42", 8, "Scoring", "Hazard Profile (H1-H7)", "scoring.html.j2", 8,
     ["Computed"]),
    ("43", 8, "Scoring", "AI Risk Scoring", "scoring.html.j2", 5,
     ["LLM", "Computed"]),
    ("44", 8, "Scoring", "Frequency & Severity Modeling", "scoring.html.j2", 6,
     ["Computed", "Supabase"]),
    ("45", 8, "Scoring", "7-Lens Peril Mapping", "scoring.html.j2", 7,
     ["Computed"]),
    ("46", 8, "Scoring", "Pattern Detection & Red Flags", "scoring.html.j2", 4,
     ["Computed", "LLM"]),
    ("47", 9, "UW Framework", "Underwriting Decision Questions", "uw_questions.html.j2", 2,
     ["Computed", "LLM"]),
    ("48", 10, "Meeting Prep", "Meeting Preparation Questions", "meeting_prep.html.j2", 1,
     ["Computed", "LLM"]),
    ("49", 11, "Audit Trail", "Signal Disposition Audit", "audit_trail.html.j2", 2,
     ["Computed"]),
    ("50", 11, "Audit Trail", "Data Coverage & Gaps", "audit_trail.html.j2", 4,
     ["Computed", "Web"]),
    ("51", 11, "Audit Trail", "Decision Record & Provenance", "audit_trail.html.j2", 5,
     ["Computed"]),
]

SECTION_COLORS = {
    0: ("#0F172A", "Overview"),
    1: ("#6D28D9", "Exec Brief"),
    2: ("#0369A1", "Company"),
    3: ("#EA580C", "Stock & Market"),
    4: ("#059669", "Financial"),
    5: ("#D97706", "Governance"),
    6: ("#DC2626", "Litigation"),
    7: ("#7C3AED", "Industry"),
    8: ("#0891B2", "Scoring"),
    9: ("#4338CA", "UW Framework"),
    10: ("#BE185D", "Meeting Prep"),
    11: ("#64748B", "Audit Trail"),
}

# ── STATUS TRACKING ──
# Pipeline per card: Designed → Data Hooked & Verified → LLM Synthesis → QA/Tested
# Update this dict as work progresses on each card.
#
# Fields:
#   designed: bool — visual design matches catalog spec (card frame, header, sub-blocks, colors)
#   data_verified: bool — all data sources hooked up, values match state.json, no N/A where data exists
#   llm_synthesis: bool — LLM-generated narrative/synthesis present and quality-checked (story of the card)
#   qa_tested: bool — visual QA passed across 3+ tickers, no data loss, no formatting issues
#   notes: str — current status notes
#
CARD_STATUS = {
    "00": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame + Overview rename done. Internal elements not restyled yet."},
    "01": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame done. Old header removed."},
    "02": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame done."},
}
# Everything else defaults to all False


def get_status(card_id):
    return CARD_STATUS.get(card_id, {
        "designed": False, "data_verified": False,
        "llm_synthesis": False, "qa_tested": False, "notes": ""
    })


def check_icon(val):
    if val is True: return "✅"
    if val is False: return "⬜"
    return "⬜"


# Sub-elements per card (expandable detail)
SUB_ELEMENTS: dict[str, list[tuple[str, str, str]]] = {
    "00": [("A","5Y Stock Strip","CHART"),("B","6 Financial Mini-Cards","CARDS"),("C","Litigation Status Bar","ALERT"),("D","2Y Drop Investigation Chart","CHART+LEGEND"),("E","Key Risk Findings","ALERT"),("F","UW Priority Metrics","4 CARDS"),("G","Plaintiff Exposure Matrix","TABLE")],
    "01": [("A","Recommendation Box","VERDICT"),("B","Critical Red Flags","ALERT"),("C","Key Negatives & Positives","TABLE")],
    "02": [("A","Risk Thesis","NARRATIVE"),("B","Dual-Voice Commentary","NARRATIVE")],
    "03": [("A","Company Profile (LLM 4-section)","NARRATIVE"),("B","Summary Cards (6)","CARDS"),("C","Business Description","NARRATIVE"),("D","Classification","KV"),("E","Revenue Model","KV")],
    "04": [("A","Revenue Segments","TABLE"),("B","Unit Economics","TABLE"),("C","Revenue Waterfall","TABLE"),("D","ASC 606","KV"),("E","Revenue Mix Bar","CHART")],
    "05": [("A","Customer Concentration","TABLE"),("B","Supplier Concentration","TABLE"),("C","Concentration Assessment","TABLE"),("D","Geographic Footprint","TABLE")],
    "06": [("A","Risk Factors (D&O-Relevant)","TABLE"),("B","D&O Exposure Factors","BADGES"),("C","Emerging Risk Radar","TABLE"),("D","Risk Classification","VERDICT")],
    "07": [("A","10-K YoY Analysis","TABLE"),("B","Risk Factor Review","TABLE"),("C","Peer SCA Contagion","TABLE")],
    "08": [("A","Sector-Specific D&O Concerns","NARRATIVE"),("B","Regulatory Environment","NARRATIVE"),("C","Key Events & News","TIMELINE")],
    "09": [("A","Market Summary Cards (6)","CARDS"),("B","Stock Charts (1Y+5Y)","2 CHARTS"),("C","Price Performance","TABLE"),("D","Drop Investigation Chart+Legend","CHART+LEGEND")],
    "10": [("A","Insider Trading Timeline","TIMELINE"),("B","Scienter Risk Strip (4 cards)","CARDS"),("C","Cluster Selling Alert","ALERT"),("D","Pre-Event Trading Suspects","ALERT"),("E","Insider Trading Table","TABLE")],
    "11": [("A","Drawdown (1Y+5Y)","2 CHARTS"),("B","Volatility & Beta (1Y+5Y)","2 CHARTS"),("C","Relative Performance (1Y+5Y)","2 CHARTS"),("D","Drop vs Sector Scatter (1Y+5Y)","2 CHARTS"),("E","Stock Performance Stats","TABLE")],
    "12": [("A","Quarterly Earnings Table","TABLE"),("B","Beat/Miss History","TABLE"),("C","Guidance Track Record","TABLE"),("D","Earnings Reaction Analysis","TABLE"),("E","Earnings Miss Scenario","NARRATIVE")],
    "13": [("A","Forward Estimates","TABLE"),("B","Analyst Revision Trends","TABLE"),("C","Recent Analyst Actions","TABLE")],
    "14": [("A","Capital Returns","TABLE"),("B","NLP & Sentiment Dashboard","TABLE"),("C","Return Correlation","TABLE"),("D","8-K Event Classification","TABLE")],
    "15": [("A","Annual Comparison (FY vs FY-1)","TABLE")],
    "16": [("A","8 Metric Cards","CARDS"),("B","Key Financial Metrics","TABLE"),("C","Quarterly Trends (8Q)","TABLE"),("D","Quarterly Updates","TABLE")],
    "17": [("A","Distress Models","TABLE"),("B","Forensic Dashboard","TABLE"),("C","Earnings Quality","TABLE"),("D","Bankruptcy Risk","TABLE"),("E","Margin+Forensic 2-Column","2-COL")],
    "18": [("A","Audit Profile","KV"),("B","Tax Risk Profile","KV"),("C","Audit Disclosure Alerts","ALERT"),("D","Tax Jurisdiction Breakdown","TABLE")],
    "19": [("A","Debt Structure","TABLE"),("B","Debt Maturity Schedule","CHART"),("C","Liquidity & Solvency","TABLE"),("D","Goodwill & Intangibles","TABLE"),("E","Capital Allocation","TABLE"),("F","Cash Flow Adequacy","TABLE"),("G","Refinancing Risk","TABLE")],
    "20": [("A","Peer Group","TABLE"),("B","Comparison Matrix","TABLE"),("C","Peer Benchmarking (SEC)","TABLE")],
    "21": [("A","MD&A Analysis","NARRATIVE"),("B","Risk Factor Analysis","TABLE"),("C","Filing Patterns & Whistleblower","TABLE")],
    "22": [("A","Board Summary Cards (7)","CARDS"),("B","Board Composition","TABLE"),("C","Skills Matrix","TABLE"),("D","Committee Membership","TABLE"),("E","Tenure Distribution","TABLE"),("F","3 Governance SVGs","3 VISUALS")],
    "23": [("A","Board Forensic Profiles","TABLE")],
    "24": [("A","Officer Background Investigation","TABLE"),("B","People Risk","TABLE"),("C","Executive Risk Profiles","TABLE"),("D","Tenure & Stability","TABLE")],
    "25": [("A","Compensation Analysis","TABLE"),("B","Ownership Structure","TABLE"),("C","Insider Trading Detail","TABLE"),("D","Activist Risk","TABLE"),("E","ISS QualityScore (5)","CARDS")],
    "26": [("A","Prior Litigation Exposure","TABLE"),("B","Structural Governance","TABLE"),("C","Shareholder Rights","TABLE"),("D","Transparency & Disclosure","TABLE")],
    "27": [("A","Header Badges","BADGES"),("B","Summary Cards (6)","CARDS"),("C","Case Status Circles","VISUAL"),("D","SCA Case Cards","CASE CARDS"),("E","Derivative Suits","LIST"),("F","Defense Strength","TABLE")],
    "28": [("A","SOL Active Windows","TABLE"),("B","Theoretical Exposure Windows","TABLE")],
    "29": [("A","SEC Enforcement Pipeline","TABLE"),("B","Regulatory Proceedings","TABLE")],
    "30": [("A","Deal/M&A Litigation","TABLE"),("B","Litigation Timeline","CHART"),("C","Contingent Liabilities","KV")],
    "31": [("A","Whistleblower Indicators","TABLE"),("B","Workforce/Product/Environmental","TABLE")],
    "32": [("A","Competitive Position","NARRATIVE"),("B","Strategic Assessment","NARRATIVE"),("C","Sector Claim Profile (3)","CARDS"),("D","D&O Tier Distribution","CHART")],
    "33": [("A","AI Risk Dimensions","TABLE"),("B","Biotech Module","NARRATIVE")],
    "34": [("A","Tier Classification","VERDICT"),("B","Factor Score Table","TABLE"),("C","Per-Factor Detail","TABLE"),("D","Critical Risk Flags","ALERT"),("E","Radar Chart","CHART")],
    "35": [("A","Claim Probability","TABLE"),("B","Severity Scenarios","TABLE"),("C","Tower Recommendation","KV")],
    "36": [("A","Peril Assessment","TABLE"),("B","Peril Map","TABLE"),("C","Allegation Theory Mapping","TABLE")],
    "37": [("A","Hazard Profile (IES)","TABLE"),("B","Forensic Composites","TABLE"),("C","Temporal Signals","TABLE"),("D","Pattern Detection","TABLE"),("E","Executive Risk Profile","TABLE")],
    "38": [("A","UW Posture","NARRATIVE"),("B","Calibration Notes","NARRATIVE"),("C","Zero Verification","TABLE"),("D","Dual-Voice Commentary","NARRATIVE")],
    "39": [("A","Altman Z (Original)","TABLE"),("B","Altman Z'' Double-Prime","TABLE"),("C","Ohlson O-Score","TABLE")],
    "40": [("A","DSRI","KV"),("B","GMI","KV"),("C","AQI","KV"),("D","SGI","KV"),("E","DEPI","KV"),("F","SGAI","KV"),("G","LVGI","KV"),("H","TATA","KV")],
    "41": [("A","Profitability Signals (4)","TABLE"),("B","Leverage/Liquidity (3)","TABLE"),("C","Efficiency (2)","TABLE")],
    "42": [("A","H1-Business","TABLE"),("B","H2-People","TABLE"),("C","H3-Financial","TABLE"),("D","H4-Governance","TABLE"),("E","H5-Maturity","TABLE"),("F","H6-Environment","TABLE"),("G","H7-Emerging","TABLE"),("H","Interactions","TABLE")],
    "43": [("A","Revenue Displacement","KV"),("B","Workforce Automation","KV"),("C","Cost Vulnerability","KV"),("D","Moat Erosion","KV"),("E","Regulatory/IP","KV")],
    "44": [("A","Frequency Model","TABLE"),("B","Severity Percentiles","TABLE"),("C","Settlement Regression","TABLE"),("D","Bear Case","NARRATIVE"),("E","Precedent Match","TABLE"),("F","Peer Outlier","TABLE")],
    "45": [("A","Shareholders","TABLE"),("B","Regulators","TABLE"),("C","Employees","TABLE"),("D","Customers/Suppliers","TABLE"),("E","Business Partners","TABLE"),("F","Investors","TABLE"),("G","General Public","TABLE")],
    "46": [("A","Pattern Detection","TABLE"),("B","Red Flag Gates","ALERT"),("C","Conjunction Scanning","TABLE"),("D","Adversarial Critique","NARRATIVE")],
    "47": [("A","Domain Question Groups","Q&A"),("B","Per-Question Detail","Q&A")],
    "48": [("A","Prioritized Questions","LIST")],
    "49": [("A","QA Audit Trail","TABLE"),("B","14 Category Breakdowns","TABLES")],
    "50": [("A","Market Data Full Detail","TABLE"),("B","Per-Section Coverage","TABLE"),("C","Data Gaps","TABLE"),("D","Blind Spot Discovery","TABLE")],
    "51": [("A","Decision Record","KV"),("B","Sources & Provenance","TABLE"),("C","Epistemological Trace","TABLE"),("D","Pipeline Status","TABLE"),("E","Render Audit","TABLE")],
}


def dsrc_pill(src):
    colors = {
        "XBRL": ("#DCFCE7", "#166534"),
        "yfinance": ("#FEF3C7", "#92400E"),
        "LLM": ("#F3E8FF", "#7C3AED"),
        "Web": ("#DBEAFE", "#1D4ED8"),
        "Computed": ("#F1F5F9", "#475569"),
        "SEC": ("#FFE4E6", "#9F1239"),
        "Supabase": ("#E0F2FE", "#075985"),
    }
    bg, fg = colors.get(src, ("#F1F5F9", "#475569"))
    return f'<span style="font-size:7px;font-weight:600;padding:1px 5px;border-radius:3px;background:{bg};color:{fg}">{src}</span>'


def build_tracker():
    html = []
    html.append('''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>D&O Worksheet — Card Tracker</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#F8FAFC;color:#1E293B;padding:0}
.hero{text-align:center;padding:32px 24px 24px;background:white;border-bottom:1px solid #E2E8F0}
.hero h1{font-size:24px;font-weight:900;color:#0F172A}
.hero .sub{font-size:12px;color:#64748B;margin-top:4px}
.progress{display:flex;justify-content:center;gap:24px;margin-top:16px}
.prog{text-align:center}
.prog-num{font-size:28px;font-weight:900}
.prog-label{font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px;font-weight:600}
.prog-bar{width:200px;height:8px;background:#E5E7EB;border-radius:4px;margin:12px auto 0;overflow:hidden}
.prog-fill{height:8px;border-radius:4px;background:#16A34A}

.nav{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.97);backdrop-filter:blur(12px);border-bottom:1px solid #E2E8F0;padding:8px 16px;display:flex;flex-wrap:wrap;justify-content:center;gap:4px}
.nav a{font-size:10px;font-weight:600;padding:4px 10px;border-radius:5px;text-decoration:none;color:white}

.section{max-width:1200px;margin:0 auto;padding:24px 16px 8px}
.sec-hdr{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.sec-num{font-size:28px;font-weight:900;line-height:1;font-family:'JetBrains Mono',monospace;opacity:0.2}
.sec-title{font-size:16px;font-weight:800}
.sec-line{flex:1;height:2px;border-radius:1px;opacity:0.15}
.sec-stats{font-size:9px;color:#64748B;font-weight:600}

.card-row{display:grid;grid-template-columns:40px 1fr 140px 50px 50px 50px 50px;gap:8px;padding:8px 12px;border-bottom:1px solid #F1F5F9;align-items:center;font-size:10px;background:white;border-left:3px solid transparent}
.card-row:hover{background:#FAFBFC}
.card-row-hdr{background:#F9FAFB;font-weight:700;color:#64748B;font-size:8px;text-transform:uppercase;letter-spacing:0.5px;border-left-color:transparent !important}
.card-id{font-family:'JetBrains Mono',monospace;font-weight:800;font-size:12px}
.card-title-col{font-weight:700;color:#1E293B}
.card-title-col .sub-count{font-size:8px;color:#94A3B8;font-weight:400;margin-left:4px}
.card-sources{display:flex;flex-wrap:wrap;gap:2px}
.card-status{font-size:9px;font-weight:600;padding:2px 6px;border-radius:3px;text-align:center}
.st-not_started{background:#F1F5F9;color:#64748B}
.st-css_only{background:#DBEAFE;color:#1D4ED8}
.st-template_rewrite{background:#FEF3C7;color:#92400E}
.st-data_verified{background:#DCFCE7;color:#166534}
.st-qa_passed{background:#D1FAE5;color:#065F46}
.check{font-size:14px;text-align:center}
.notes{font-size:8px;color:#94A3B8;grid-column:2/-1;padding:0 0 4px}

.legend{max-width:1200px;margin:16px auto;padding:0 16px;display:flex;gap:12px;flex-wrap:wrap;font-size:9px;color:#64748B}
.legend-item{display:flex;align-items:center;gap:4px}

details>summary{list-style:none}
details>summary::marker{display:none}
details[open]>summary{color:#64748B !important}
details[open]>summary::before{content:""}
.footer{text-align:center;padding:32px 24px;color:#94A3B8;font-size:10px;border-top:1px solid #E2E8F0;margin-top:24px;background:white}
</style></head><body>
''')

    # Progress stats
    total = len(CARDS)
    designed = sum(1 for c in CARDS if get_status(c[0])["designed"])
    data_ok = sum(1 for c in CARDS if get_status(c[0])["data_verified"])
    llm_ok = sum(1 for c in CARDS if get_status(c[0])["llm_synthesis"])
    qa_done = sum(1 for c in CARDS if get_status(c[0])["qa_tested"])
    pct = int(qa_done / total * 100) if total else 0

    html.append(f'''<div class="hero">
<h1>Card Tracker — D&O Worksheet Redesign</h1>
<div class="sub">52 cards across 12 sections. Pipeline: Designed → Data Verified → LLM Synthesis → QA Tested</div>
<div class="progress">
<div class="prog"><div class="prog-num">{total}</div><div class="prog-label">Total Cards</div></div>
<div class="prog"><div class="prog-num" style="color:#1D4ED8">{designed}</div><div class="prog-label">Designed</div></div>
<div class="prog"><div class="prog-num" style="color:#D97706">{data_ok}</div><div class="prog-label">Data Verified</div></div>
<div class="prog"><div class="prog-num" style="color:#7C3AED">{llm_ok}</div><div class="prog-label">LLM Synthesis</div></div>
<div class="prog"><div class="prog-num" style="color:#16A34A">{qa_done}</div><div class="prog-label">QA Tested</div></div>
</div>
<div class="prog-bar"><div class="prog-fill" style="width:{pct}%;background:#16A34A"></div></div>
</div>''')

    # Nav
    html.append('<div class="nav">')
    for sec_num, (color, name) in SECTION_COLORS.items():
        count = sum(1 for c in CARDS if c[1] == sec_num)
        html.append(f'<a href="#sec-{sec_num}" style="background:{color}">{sec_num} {name} ({count})</a>')
    html.append('</div>')

    # Legend
    html.append('''<div class="legend">
<div class="legend-item"><b>Pipeline:</b></div>
<div class="legend-item">✅ Designed — card frame, header, sub-blocks, colors match catalog spec</div>
<div class="legend-item">✅ Data — all sources hooked up, values verified against state.json</div>
<div class="legend-item">✅ LLM — narrative synthesis done, story quality checked</div>
<div class="legend-item">✅ QA — visual QA across 3+ tickers, no data loss, no formatting issues</div>
<div class="legend-item">⬜ = Not done yet</div>
</div>''')

    # Cards by section
    current_section = -1
    for card_id, sec_num, sec_name, title, template, sub_count, sources in CARDS:
        if sec_num != current_section:
            if current_section >= 0:
                html.append('</div>')  # close prev section
            color, name = SECTION_COLORS[sec_num]
            sec_cards = [c for c in CARDS if c[1] == sec_num]
            sec_designed = sum(1 for c in sec_cards if get_status(c[0])["designed"])
            html.append(f'<div class="section" id="sec-{sec_num}">')
            html.append(f'<div class="sec-hdr"><div class="sec-num" style="color:{color}">{sec_num:02d}</div><div class="sec-title">{name}</div><div class="sec-line" style="background:{color}"></div><div class="sec-stats">{sec_designed}/{len(sec_cards)} designed</div></div>')
            # Header row
            html.append(f'<div class="card-row card-row-hdr"><div>ID</div><div>Card Title</div><div>Data Sources</div><div>Designed</div><div>Data</div><div>LLM</div><div>QA</div></div>')
            current_section = sec_num

        st = get_status(card_id)
        color = SECTION_COLORS[sec_num][0]
        sources_html = ' '.join(dsrc_pill(s) for s in sources)

        html.append(f'<div class="card-row" style="border-left-color:{color}">')
        html.append(f'<div class="card-id" style="color:{color}">{card_id}</div>')
        html.append(f'<div class="card-title-col">{title}<span class="sub-count">{sub_count} elements</span></div>')
        html.append(f'<div class="card-sources">{sources_html}</div>')
        html.append(f'<div class="check">{check_icon(st["designed"])}</div>')
        html.append(f'<div class="check">{check_icon(st["data_verified"])}</div>')
        html.append(f'<div class="check">{check_icon(st["llm_synthesis"])}</div>')
        html.append(f'<div class="check">{check_icon(st["qa_tested"])}</div>')
        html.append('</div>')

        # Expandable sub-elements
        subs = SUB_ELEMENTS.get(card_id, [])
        if subs:
            html.append(f'<details style="border-left:3px solid {color};background:white;border-bottom:1px solid #F1F5F9">')
            html.append(f'<summary style="padding:4px 12px 4px 52px;font-size:9px;color:#94A3B8;cursor:pointer;list-style:none">▸ {len(subs)} sub-elements</summary>')
            html.append(f'<div style="padding:2px 12px 8px 52px">')
            for letter, name, typ in subs:
                type_colors = {"CHART":"#DBEAFE;color:#1D4ED8","TABLE":"#FEF3C7;color:#92400E","NARRATIVE":"#F3E8FF;color:#7C3AED","CARDS":"#DCFCE7;color:#166534","ALERT":"#FEF2F2;color:#991B1B","VERDICT":"#FEF2F2;color:#991B1B","KV":"#E0F2FE;color:#075985","VISUAL":"#EDE9FE;color:#6D28D9","TIMELINE":"#FFF7ED;color:#9A3412","BADGES":"#FEF2F2;color:#991B1B","LIST":"#F1F5F9;color:#475569","Q&A":"#F0F9FF;color:#0C4A6E"}
                tc = type_colors.get(typ, type_colors.get(typ.split("+")[0].split(" ")[-1], "#F1F5F9;color:#475569"))
                html.append(f'<div style="display:flex;align-items:center;gap:6px;padding:2px 0">')
                html.append(f'<span style="width:16px;height:16px;border-radius:3px;background:{color};color:white;font-size:7px;font-weight:800;display:flex;align-items:center;justify-content:center">{letter}</span>')
                html.append(f'<span style="font-size:9px;font-weight:600;color:#1E293B;flex:1">{name}</span>')
                html.append(f'<span style="font-size:7px;font-weight:700;padding:1px 5px;border-radius:2px;background:{tc}">{typ}</span>')
                html.append(f'</div>')
            html.append('</div></details>')

        if st["notes"]:
            html.append(f'<div style="border-left:3px solid {color};padding:2px 12px 4px 52px;background:white;border-bottom:1px solid #F1F5F9;font-size:8px;color:#94A3B8">{st["notes"]}</div>')

    html.append('</div>')  # close last section

    html.append(f'''<div class="footer">
<p><strong>Card Tracker</strong> — {total} cards · {designed} designed · {data_ok} data verified · {llm_ok} LLM synthesis · {qa_done} QA tested</p>
<p style="margin-top:4px;color:#CBD5E1">Update CARD_STATUS in build_card_tracker.py as work progresses</p>
</div></body></html>''')

    return '\n'.join(html)


if __name__ == "__main__":
    html = build_tracker()
    out = Path("output/CARD_TRACKER.html")
    out.write_text(html)
    total = len(CARDS)
    designed = sum(1 for c in CARDS if get_status(c[0])["designed"])
    print(f"Generated tracker: {total} cards, {designed} designed, {total - designed} remaining")
