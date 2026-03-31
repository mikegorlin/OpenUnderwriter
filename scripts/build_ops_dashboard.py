#!/usr/bin/env python3
"""Operating Dashboard — Card Tracker + Data Sources + Brain Signals + Pipeline Health.
Multi-tab dashboard for the entire D&O worksheet system."""

from pathlib import Path
import json
import re

# ══════════════════════════════════════════════════════════════
# CARD DEFINITIONS — EXPANDED TO ~68 CARDS
# Covers: actual rendered output + Liberty template gaps + brain audit
# ══════════════════════════════════════════════════════════════

SECTION_COLORS = {
    0: ("#0F172A", "Overview"),
    1: ("#6D28D9", "Exec Brief"),
    2: ("#0369A1", "Company"),
    3: ("#EA580C", "Stock & Market"),
    4: ("#059669", "Financial"),
    5: ("#D97706", "Governance"),
    6: ("#DC2626", "Litigation"),
    7: ("#0D9488", "Forward-Looking"),
    8: ("#7C3AED", "Industry"),
    9: ("#0891B2", "Scoring"),
    10: ("#4338CA", "UW Framework"),
    11: ("#BE185D", "Meeting Prep"),
    12: ("#64748B", "Audit Trail"),
}

# (id, section, title, sub_count, sources, sub_elements)
CARDS = [
    # ── Section 0: Overview (1 card) ──
    ("00", 0, "Overview (Decision Dashboard)", 7,
     ["XBRL","yfinance","Computed","LLM","Web","SEC","Supabase"],
     [("A","5Y Stock Strip","CHART"),("B","6 Financial Mini-Cards","CARDS"),("C","Litigation Status Bar","ALERT"),("D","2Y Drop Investigation Chart","CHART+LEGEND"),("E","Key Risk Findings","ALERT"),("F","UW Priority Metrics","4 CARDS"),("G","Plaintiff Exposure Matrix","TABLE")]),

    # ── Section 1: Exec Brief (2 cards) ──
    ("01", 1, "Recommendation & Red Flags", 3,
     ["Computed","LLM"],
     [("A","Recommendation Box (tier+action+probability)","VERDICT"),("B","Critical Red Flags","ALERT"),("C","Key Negatives & Positives (2-col)","TABLE")]),
    ("02", 1, "Risk Thesis & Commentary", 2,
     ["LLM"],
     [("A","Risk Thesis (factors/mitigations/conditions)","NARRATIVE"),("B","Dual-Voice Commentary","NARRATIVE")]),

    # ── Section 2: Company (11 cards — expanded) ──
    ("03", 2, "Business Description & Revenue Model", 5,
     ["SEC","LLM","Computed"],
     [("A","Company Profile (LLM 4-section)","NARRATIVE"),("B","Summary Cards (6)","CARDS"),("C","Business Description","NARRATIVE"),("D","Classification (SIC/GICS/NAICS)","KV"),("E","Revenue Model","KV")]),
    ("04", 2, "Revenue Deep Dive", 6,
     ["XBRL","LLM"],
     [("A","Revenue Segments","TABLE"),("B","Unit Economics","TABLE"),("C","Revenue Waterfall (Growth Decomposition)","TABLE"),("D","Revenue Recognition (ASC 606)","KV"),("E","Revenue Mix Bar","CHART"),("F","Money Flows (reverse waterfall)","CHART")]),
    ("05", 2, "Concentration Risk", 4,
     ["LLM","XBRL"],
     [("A","Customer Concentration","TABLE"),("B","Supplier Concentration","TABLE"),("C","Concentration Assessment","TABLE"),("D","Geographic Footprint","TABLE")]),
    ("06", 2, "Risk Factors & D&O Exposure", 4,
     ["SEC","LLM","Computed"],
     [("A","Risk Factors (D&O-Relevant)","TABLE"),("B","D&O Exposure Factors","BADGES"),("C","Emerging Risk Radar","TABLE"),("D","Risk Classification Verdict","VERDICT")]),
    ("07", 2, "10-K YoY Analysis & Peer SCA", 3,
     ["SEC","LLM","Supabase"],
     [("A","10-K YoY Analysis","TABLE"),("B","Risk Factor Review","TABLE"),("C","Peer SCA Contagion","TABLE")]),
    ("08", 2, "Sector Risk, Regulatory & News", 3,
     ["Web","LLM","SEC"],
     [("A","Sector-Specific D&O Concerns","NARRATIVE"),("B","Regulatory Environment","NARRATIVE"),("C","Key Events & News","TIMELINE")]),
    ("09", 2, "M&A Profile & Transaction History", 4,
     ["SEC","LLM","Web"],
     [("A","Acquisition History","TABLE"),("B","Goodwill Concentration from M&A","TABLE"),("C","Deal/M&A Litigation Risk","ALERT"),("D","Integration Risk Assessment","NARRATIVE")]),
    ("10", 2, "Corporate Events & IPO/Offerings", 5,
     ["SEC","LLM","Computed"],
     [("A","Event Status (IPO/SPAC/M&A/capital raises)","KV"),("B","IPO/Offering Details (S-1/S-3/424B)","TABLE"),("C","Section 11 Exposure Windows","TABLE"),("D","Lockup Terms & Expiry","TABLE"),("E","Event Timeline","TIMELINE")]),
    ("11", 2, "Operational Complexity & Supply Chain", 5,
     ["SEC","LLM"],
     [("A","Subsidiary Structure","TABLE"),("B","VIE/SPE Structures","TABLE"),("C","Supply Chain Dependencies","TABLE"),("D","Workforce Distribution","TABLE"),("E","Technology Dependence","NARRATIVE")]),
    ("12", 2, "Competitive Moat & Industry Position", 3,
     ["LLM","Web"],
     [("A","Competitive Landscape (moat assessment)","NARRATIVE"),("B","Market Share & Trends","TABLE"),("C","Industry Headwinds/Tailwinds","NARRATIVE")]),

    # ── Section 3: Stock & Market (6 cards) ──
    ("13", 3, "Stock Performance & Drop Investigation", 4,
     ["yfinance","Web","Computed"],
     [("A","Market Summary Cards (6)","CARDS"),("B","Stock Charts (1Y+5Y)","2 CHARTS"),("C","Price Performance (1M-5Y vs S&P)","TABLE"),("D","Drop Investigation Chart+Legend","CHART+LEGEND")]),
    ("14", 3, "Ownership, Insider Trading & Scienter Risk", 9,
     ["yfinance","Computed"],
     [("A","Exposed Market Cap (float × price)","METRIC"),("B","Ownership Breakdown (institutional/insider/float)","CARDS"),("C","Institutional Holder Changes (buying/dumping)","TABLE"),("D","Concentrated Holder Risk (top 5 %)","ALERT"),("E","Short Interest Trend (current vs prior month)","METRIC"),("F","Insider Trading Timeline","TIMELINE"),("G","Scienter Risk Strip (4 cards)","CARDS"),("H","Cluster Selling / Pre-Event Alerts","ALERT"),("I","Insider Trading Table","TABLE")]),
    ("15", 3, "Technical Analysis Charts", 5,
     ["yfinance","Computed"],
     [("A","Drawdown (1Y+5Y)","2 CHARTS"),("B","Volatility & Beta (1Y+5Y)","2 CHARTS"),("C","Relative Performance (1Y+5Y)","2 CHARTS"),("D","Drop vs Sector Scatter (1Y+5Y)","2 CHARTS"),("E","Stock Performance Stats","TABLE")]),
    ("16", 3, "Earnings & Guidance", 5,
     ["yfinance","LLM","Computed"],
     [("A","Quarterly Earnings Table","TABLE"),("B","Beat/Miss History","TABLE"),("C","Guidance Track Record (miss magnitude+impact)","TABLE"),("D","Earnings Reaction Analysis","TABLE"),("E","Earnings Miss Scenario","NARRATIVE")]),
    ("17", 3, "Analyst Coverage & Estimates", 3,
     ["yfinance"],
     [("A","Forward Estimates","TABLE"),("B","Analyst Revision Trends","TABLE"),("C","Recent Analyst Actions","TABLE")]),
    ("18", 3, "Capital Returns, Sentiment & 8-K", 4,
     ["yfinance","SEC","LLM","Computed"],
     [("A","Capital Returns","TABLE"),("B","NLP & Sentiment Dashboard","TABLE"),("C","Return Correlation Analysis","TABLE"),("D","8-K Event Classification","TABLE")]),

    # ── Section 4: Financial (7 cards) ──
    ("19", 4, "Annual Financial Comparison", 1,
     ["XBRL"],
     [("A","Annual Comparison (FY vs FY-1)","TABLE")]),
    ("20", 4, "Key Metrics & Quarterly Trends", 4,
     ["XBRL","yfinance","Computed"],
     [("A","8 Metric Cards","CARDS"),("B","Key Financial Metrics (profitability/solvency/liquidity)","TABLE"),("C","Quarterly Trends (8Q)","TABLE"),("D","Quarterly Updates","TABLE")]),
    ("21", 4, "Distress & Forensic Models", 5,
     ["XBRL","Computed"],
     [("A","Distress Models (Altman/Piotroski/Ohlson)","TABLE"),("B","Forensic Dashboard (Beneish 8-component)","TABLE"),("C","Earnings Quality","TABLE"),("D","Bankruptcy Risk","TABLE"),("E","Margin+Forensic 2-Column","2-COL")]),
    ("22", 4, "Audit & Tax Profile", 4,
     ["XBRL","SEC"],
     [("A","Audit Profile (auditor/tenure/opinions/changes)","KV"),("B","Tax Risk Profile","KV"),("C","Audit Disclosure Alerts","ALERT"),("D","Tax Jurisdiction Breakdown","TABLE")]),
    ("23", 4, "Debt, Liquidity & Balance Sheet Risk", 7,
     ["XBRL","LLM","Computed"],
     [("A","Debt Structure","TABLE"),("B","Debt Maturity Schedule","CHART"),("C","Liquidity & Solvency","TABLE"),("D","Goodwill & Intangibles","TABLE"),("E","Capital Allocation","TABLE"),("F","Cash Flow Adequacy","TABLE"),("G","Refinancing Risk","TABLE")]),
    ("24", 4, "Peer Benchmarking", 3,
     ["yfinance","XBRL","Computed"],
     [("A","Peer Group","TABLE"),("B","Comparison Matrix","TABLE"),("C","Peer Benchmarking (SEC)","TABLE")]),
    ("25", 4, "MD&A & Filing Analysis", 3,
     ["SEC","LLM"],
     [("A","MD&A Analysis","NARRATIVE"),("B","Risk Factor Analysis","TABLE"),("C","Filing Patterns & Whistleblower","TABLE")]),

    # ── Section 5: Governance (6 cards — expanded) ──
    ("26", 5, "Board Composition & Skills", 6,
     ["SEC","Computed"],
     [("A","Board Summary Cards (7)","CARDS"),("B","Board Composition","TABLE"),("C","Skills Matrix","TABLE"),("D","Committee Membership","TABLE"),("E","Tenure Distribution","TABLE"),("F","3 Governance SVGs (donut/bars/gauge)","3 VISUALS")]),
    ("27", 5, "Board & Officer Forensic Profiles", 3,
     ["SEC","Web","LLM"],
     [("A","Board Member Forensic Profiles","TABLE"),("B","Officer Background Investigation","TABLE"),("C","Prior Litigation Exposure","TABLE")]),
    ("28", 5, "People Risk & Executive Profiles", 4,
     ["Web","SEC","LLM"],
     [("A","People Risk (key person dependencies)","TABLE"),("B","Executive Risk Profiles","TABLE"),("C","Tenure & Stability (C-suite turnover)","TABLE"),("D","Recent Changes (departures/appointments 12M)","TABLE")]),
    ("29", 5, "Compensation & Ownership", 5,
     ["SEC","yfinance","Web"],
     [("A","Compensation Analysis (CEO comp/say-on-pay/ratio)","TABLE"),("B","Ownership Structure (insiders/institutional/funds)","TABLE"),("C","Per-Insider Activity Detail","TABLE"),("D","Activist Investor Risk","TABLE"),("E","ISS QualityScore (5 dimensions)","CARDS")]),
    ("30", 5, "Structural Governance & Rights", 4,
     ["SEC","LLM"],
     [("A","Structural Governance (anti-takeover/classified)","TABLE"),("B","Shareholder Rights Inventory","TABLE"),("C","Transparency & Disclosure Quality","TABLE"),("D","Dual-Class / Controlled Company Analysis","TABLE")]),
    ("31", 5, "Compensation & Conflicts (Liberty)", 3,
     ["SEC","LLM"],
     [("A","Short-term Stock Incentives","TABLE"),("B","Related Party Transactions","TABLE"),("C","Say-on-Pay <70% Analysis","ALERT")]),

    # ── Section 6: Litigation (5 cards) ──
    ("32", 6, "Active Litigation & Defense", 6,
     ["Supabase","SEC","Web","LLM"],
     [("A","Header Badges","BADGES"),("B","Summary Cards (6)","CARDS"),("C","Case Status Circles","VISUAL"),("D","SCA Case Cards","CASE CARDS"),("E","Derivative Suits","LIST"),("F","Defense Strength","TABLE")]),
    ("33", 6, "Exposure Windows & SOL", 2,
     ["Computed","SEC"],
     [("A","SOL Active Windows","TABLE"),("B","Theoretical Exposure Windows","TABLE")]),
    ("34", 6, "SEC & Regulatory Enforcement", 2,
     ["SEC","Web"],
     [("A","SEC Enforcement Pipeline","TABLE"),("B","Regulatory Proceedings","TABLE")]),
    ("35", 6, "Historical Litigation & Timeline", 3,
     ["SEC","XBRL","Web"],
     [("A","Deal/M&A Litigation","TABLE"),("B","Litigation Timeline","CHART"),("C","Contingent Liabilities (ASC 450)","KV")]),
    ("36", 6, "Other Matters, Internal Issues & Whistleblower", 4,
     ["SEC","LLM","Web"],
     [("A","Whistleblower Indicators","TABLE"),("B","Workforce/Product/Environmental","TABLE"),("C","Internal Issues (investigations/SEC comments)","TABLE"),("D","Accounting Issues (restatements/material weakness)","ALERT")]),

    # ── Section 7: Forward-Looking (5 cards — NEW SECTION, was empty!) ──
    ("37", 7, "Catalyst Events & Key Dates", 3,
     ["yfinance","SEC","LLM"],
     [("A","Upcoming Catalyst Calendar","TIMELINE"),("B","Earnings/FDA/Trial Dates","TABLE"),("C","Event-Driven Risk Assessment","NARRATIVE")]),
    ("38", 7, "Scenario Analysis (Bull/Base/Bear)", 3,
     ["LLM","Computed"],
     [("A","Bull Case","NARRATIVE"),("B","Base Case","NARRATIVE"),("C","Bear Case","NARRATIVE")]),
    ("39", 7, "Short Seller & Alternative Signals", 4,
     ["Web","LLM"],
     [("A","Short Seller Monitoring","TABLE"),("B","Glassdoor/Employee Signals","TABLE"),("C","Social Media Sentiment","TABLE"),("D","Alternative Data Signals","TABLE")]),
    ("40", 7, "Analyst Credibility & Disclosure Quality", 3,
     ["yfinance","LLM"],
     [("A","Analyst Credibility Assessment","TABLE"),("B","Disclosure Quality Score","TABLE"),("C","Narrative Coherence (MD&A vs reality)","NARRATIVE")]),
    ("41", 7, "Macro, Geopolitical & Emerging Risk", 4,
     ["Web","LLM"],
     [("A","Macro Exposure (rates/currency/commodities)","TABLE"),("B","Geopolitical Risk","NARRATIVE"),("C","Monitoring Triggers & Early Warning","TABLE"),("D","Restructuring Activity","TABLE")]),

    # ── Section 8: Industry (2 cards) ──
    ("42", 8, "Competitive & Strategic Position", 4,
     ["Computed","LLM","Supabase"],
     [("A","Competitive Position","NARRATIVE"),("B","Strategic Assessment","NARRATIVE"),("C","Sector Claim Profile (3 cards)","CARDS"),("D","D&O Tier Distribution","CHART")]),
    ("43", 8, "AI Risk & Biotech Module", 2,
     ["LLM","SEC"],
     [("A","AI Risk Dimensions (5)","TABLE"),("B","Biotech Four-Pillar (conditional)","NARRATIVE")]),

    # ── Section 9: Scoring (13 cards) ──
    ("44", 9, "Tier & Factor Scoring", 5,
     ["Computed"],
     [("A","Tier Classification","VERDICT"),("B","Factor Score Table (SVG bars)","TABLE"),("C","Per-Factor Detail","TABLE"),("D","Critical Risk Flags","ALERT"),("E","Radar Chart","CHART")]),
    ("45", 9, "Loss Analysis & Scenarios", 3,
     ["Computed"],
     [("A","Claim Probability","TABLE"),("B","Severity Scenarios","TABLE"),("C","Tower Recommendation","KV")]),
    ("46", 9, "Peril Assessment & Mapping", 3,
     ["Computed"],
     [("A","Peril Assessment","TABLE"),("B","Peril Map","TABLE"),("C","Allegation Theory Mapping","TABLE")]),
    ("47", 9, "Investigative Depth", 5,
     ["Computed"],
     [("A","Hazard Profile (IES H1-H7)","TABLE"),("B","Forensic Composites","TABLE"),("C","Temporal Signals","TABLE"),("D","Pattern Detection","TABLE"),("E","Executive Risk Profile","TABLE")]),
    ("48", 9, "UW Posture & Calibration", 4,
     ["Computed","LLM"],
     [("A","UW Posture","NARRATIVE"),("B","Calibration Notes","NARRATIVE"),("C","Zero Verification","TABLE"),("D","Dual-Voice Commentary","NARRATIVE")]),
    ("49", 9, "Altman Z-Score & Distress Models", 3,
     ["XBRL","Computed"],
     [("A","Altman Z (Original)","TABLE"),("B","Altman Z'' Double-Prime","TABLE"),("C","Ohlson O-Score","TABLE")]),
    ("50", 9, "Beneish M-Score (Manipulation)", 8,
     ["XBRL","Computed"],
     [("A","DSRI","KV"),("B","GMI","KV"),("C","AQI","KV"),("D","SGI","KV"),("E","DEPI","KV"),("F","SGAI","KV"),("G","LVGI","KV"),("H","TATA","KV")]),
    ("51", 9, "Piotroski F-Score (Health)", 3,
     ["XBRL","Computed"],
     [("A","Profitability (4)","TABLE"),("B","Leverage/Liquidity (3)","TABLE"),("C","Efficiency (2)","TABLE")]),
    ("52", 9, "Hazard Profile (H1-H7, 47 dims)", 8,
     ["Computed"],
     [("A","H1-Business","TABLE"),("B","H2-People","TABLE"),("C","H3-Financial","TABLE"),("D","H4-Governance","TABLE"),("E","H5-Maturity","TABLE"),("F","H6-Environment","TABLE"),("G","H7-Emerging","TABLE"),("H","Interactions","TABLE")]),
    ("53", 9, "AI Risk Scoring (5 dims)", 5,
     ["LLM","Computed"],
     [("A","Revenue Displacement","KV"),("B","Workforce Automation","KV"),("C","Cost Vulnerability","KV"),("D","Moat Erosion","KV"),("E","Regulatory/IP","KV")]),
    ("54", 9, "Frequency & Severity Modeling", 6,
     ["Computed","Supabase"],
     [("A","Frequency Model","TABLE"),("B","Severity Percentiles","TABLE"),("C","Settlement Regression (DDL)","TABLE"),("D","Bear Case","NARRATIVE"),("E","Precedent Match","TABLE"),("F","Peer Outlier","TABLE")]),
    ("55", 9, "7-Lens Peril Mapping", 7,
     ["Computed"],
     [("A","Shareholders","TABLE"),("B","Regulators","TABLE"),("C","Employees","TABLE"),("D","Customers/Suppliers","TABLE"),("E","Business Partners","TABLE"),("F","Investors","TABLE"),("G","General Public","TABLE")]),
    ("56", 9, "Pattern Detection & Red Flags", 4,
     ["Computed","LLM"],
     [("A","Pattern Detection","TABLE"),("B","Red Flag Gates","ALERT"),("C","Conjunction Scanning","TABLE"),("D","Adversarial Critique","NARRATIVE")]),

    # ── Section 10: UW Framework (1 card) ──
    ("57", 10, "Underwriting Decision Questions", 2,
     ["Computed","LLM"],
     [("A","Domain Question Groups","Q&A"),("B","Per-Question Detail","Q&A")]),

    # ── Section 11: Meeting Prep (1 card) ──
    ("58", 11, "Meeting Preparation Questions", 1,
     ["Computed","LLM"],
     [("A","Prioritized Questions","LIST")]),

    # ── Section 12: Audit Trail (3 cards) ──
    ("59", 12, "Signal Disposition Audit", 2,
     ["Computed"],
     [("A","QA Audit Trail","TABLE"),("B","14 Category Breakdowns","TABLES")]),
    ("60", 12, "Data Coverage & Gaps", 4,
     ["Computed","Web"],
     [("A","Market Data Full Detail","TABLE"),("B","Per-Section Coverage","TABLE"),("C","Data Gaps","TABLE"),("D","Blind Spot Discovery","TABLE")]),
    ("61", 12, "Decision Record & Provenance", 5,
     ["Computed"],
     [("A","Decision Record","KV"),("B","Sources & Provenance","TABLE"),("C","Epistemological Trace","TABLE"),("D","Pipeline Status","TABLE"),("E","Render Audit","TABLE")]),
]

# ── STATUS TRACKING ──
CARD_STATUS: dict[str, dict] = {
    "00": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame done, renamed Overview"},
    "01": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame done"},
    "02": {"designed": True, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": "Card frame done"},
}

def get_status(card_id):
    return CARD_STATUS.get(card_id, {"designed": False, "data_verified": False, "llm_synthesis": False, "qa_tested": False, "notes": ""})

# ── DATA SOURCES ──
DATA_SOURCES = [
    ("XBRL", "#DCFCE7", "#166534", "SEC XBRL filings", "HIGH", "179 concepts mapped"),
    ("yfinance", "#FEF3C7", "#92400E", "Yahoo Finance market data", "MEDIUM", "Price, earnings, insider, analyst"),
    ("SEC", "#FFE4E6", "#9F1239", "SEC EDGAR filings + enforcement", "HIGH", "10-K, 10-Q, 8-K, proxy, S-1"),
    ("LLM", "#F3E8FF", "#7C3AED", "Claude extraction + synthesis", "MEDIUM", "Haiku 4.5 default, Sonnet for synthesis"),
    ("Web", "#DBEAFE", "#1D4ED8", "Brave Search + web scraping", "LOW", "2,000 free searches/month"),
    ("Computed", "#F1F5F9", "#475569", "Derived/calculated metrics", "HIGH", "Ratios, scores, models"),
    ("Supabase", "#E0F2FE", "#075985", "GorlinBase D&O claims DB", "MEDIUM", "6,980 SCA filings"),
]

# ── BRAIN SIGNAL CATEGORIES ──
BRAIN_CATEGORIES = [
    ("biz", "Business", 75, 8),
    ("fin", "Financial", 82, 12),
    ("stock", "Stock/Market", 45, 6),
    ("gov", "Governance", 58, 5),
    ("lit", "Litigation", 42, 3),
    ("exec", "Executive", 38, 4),
    ("fwrd", "Forward", 35, 5),
    ("nlp", "NLP/Sentiment", 28, 2),
    ("disc", "Disclosure", 32, 3),
    ("envr", "Environment", 25, 4),
    ("sect", "Sector", 22, 3),
    ("abs", "Absence", 20, 8),
    ("conj", "Conjunction", 8, 0),
    ("ctx", "Contextual", 20, 0),
]

# ── PIPELINE STAGES ──
PIPELINE_STAGES = [
    ("RESOLVE", "Ticker → company identity", "#16A34A"),
    ("ACQUIRE", "Data acquisition (SEC, stock, lit, web)", "#0369A1"),
    ("EXTRACT", "Parse filings, extract structured data", "#7C3AED"),
    ("ANALYZE", "Run checks, detect patterns", "#D97706"),
    ("SCORE", "10-factor scoring, red flags", "#DC2626"),
    ("BENCHMARK", "Peer-relative comparisons", "#0891B2"),
    ("RENDER", "Word/PDF/HTML generation", "#0F172A"),
]


def dsrc_pill(src):
    colors = {"XBRL":("#DCFCE7","#166534"),"yfinance":("#FEF3C7","#92400E"),"LLM":("#F3E8FF","#7C3AED"),
              "Web":("#DBEAFE","#1D4ED8"),"Computed":("#F1F5F9","#475569"),"SEC":("#FFE4E6","#9F1239"),
              "Supabase":("#E0F2FE","#075985")}
    bg, fg = colors.get(src, ("#F1F5F9","#475569"))
    return f'<span style="font-size:7px;font-weight:600;padding:1px 5px;border-radius:3px;background:{bg};color:{fg}">{src}</span>'

def check_icon(val):
    return "✅" if val else "⬜"


def build_html():
    total = len(CARDS)
    designed = sum(1 for c in CARDS if get_status(c[0])["designed"])
    data_ok = sum(1 for c in CARDS if get_status(c[0])["data_verified"])
    llm_ok = sum(1 for c in CARDS if get_status(c[0])["llm_synthesis"])
    qa_done = sum(1 for c in CARDS if get_status(c[0])["qa_tested"])

    total_signals = sum(c[2] for c in BRAIN_CATEGORIES)
    skipped_signals = sum(c[3] for c in BRAIN_CATEGORIES)

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>D&O Worksheet — Operating Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,-apple-system,sans-serif;background:#F8FAFC;color:#1E293B}}
.hero{{text-align:center;padding:32px 24px 16px;background:white;border-bottom:1px solid #E2E8F0}}
.hero h1{{font-size:24px;font-weight:900;color:#0F172A}}
.hero .sub{{font-size:12px;color:#64748B;margin-top:4px}}
.stats{{display:flex;justify-content:center;gap:20px;margin-top:16px;flex-wrap:wrap}}
.stat{{text-align:center;min-width:70px}}
.stat-num{{font-size:24px;font-weight:900}}
.stat-label{{font-size:8px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.5px;font-weight:600}}

/* Tabs */
.tabs{{position:sticky;top:0;z-index:100;background:white;border-bottom:2px solid #E2E8F0;padding:0 16px;display:flex;gap:0}}
.tab{{padding:10px 20px;font-size:12px;font-weight:700;color:#64748B;cursor:pointer;border-bottom:3px solid transparent;transition:all .15s}}
.tab:hover{{color:#1E293B}}
.tab.active{{color:#0F172A;border-bottom-color:#0F172A}}
.tab-count{{font-size:9px;font-weight:600;background:#F1F5F9;color:#64748B;padding:1px 5px;border-radius:8px;margin-left:4px}}
.tab-panel{{display:none;max-width:1200px;margin:0 auto;padding:16px}}
.tab-panel.active{{display:block}}

/* Cards tab */
.sec-hdr{{display:flex;align-items:center;gap:10px;margin:20px 0 8px}}
.sec-num{{font-size:24px;font-weight:900;opacity:0.15;font-family:'JetBrains Mono',monospace}}
.sec-title{{font-size:14px;font-weight:800}}
.sec-line{{flex:1;height:2px;opacity:0.12;border-radius:1px}}
.sec-stats{{font-size:9px;color:#64748B}}

.card-row{{display:grid;grid-template-columns:36px 1fr 140px 40px 40px 40px 40px;gap:6px;padding:7px 10px;border-bottom:1px solid #F1F5F9;align-items:center;font-size:10px;background:white;border-left:3px solid transparent}}
.card-row:hover{{background:#FAFBFC}}
.card-row-hdr{{background:#F9FAFB;font-weight:700;color:#64748B;font-size:8px;text-transform:uppercase;letter-spacing:.3px}}
.card-id{{font-family:'JetBrains Mono',monospace;font-weight:800;font-size:11px}}
.card-title-col{{font-weight:700;color:#1E293B}}
.card-title-col .sub-count{{font-size:8px;color:#94A3B8;font-weight:400;margin-left:4px}}
.card-sources{{display:flex;flex-wrap:wrap;gap:2px}}
.check{{font-size:13px;text-align:center}}

/* Expandable sub-elements */
details>summary{{list-style:none;cursor:pointer}}
details>summary::-webkit-details-marker{{display:none}}
.sub-el{{display:flex;align-items:center;gap:6px;padding:2px 0}}
.sub-ltr{{width:16px;height:16px;border-radius:3px;color:white;font-size:7px;font-weight:800;display:flex;align-items:center;justify-content:center}}
.sub-nm{{font-size:9px;font-weight:600;color:#1E293B;flex:1}}
.sub-tp{{font-size:7px;font-weight:700;padding:1px 5px;border-radius:2px}}

/* Data Sources tab */
.ds-card{{background:white;border:1px solid #E2E8F0;border-radius:8px;padding:12px 16px;margin-bottom:8px}}
.ds-name{{font-size:13px;font-weight:800}}
.ds-desc{{font-size:10px;color:#64748B;margin-top:2px}}
.ds-meta{{display:flex;gap:12px;margin-top:6px;font-size:9px}}
.ds-badge{{padding:2px 8px;border-radius:4px;font-weight:700;font-size:8px}}

/* Brain tab */
.brain-row{{display:grid;grid-template-columns:60px 1fr 60px 60px 80px;gap:8px;padding:6px 10px;border-bottom:1px solid #F1F5F9;font-size:10px;align-items:center}}
.brain-bar{{height:6px;border-radius:3px;background:#E5E7EB}}
.brain-fill{{height:6px;border-radius:3px}}

/* Pipeline tab */
.pipe-stage{{display:flex;align-items:center;gap:12px;padding:12px 16px;background:white;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:6px}}
.pipe-num{{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:white}}
.pipe-arrow{{font-size:18px;color:#CBD5E1;text-align:center;margin:0 0 6px 18px}}

.footer{{text-align:center;padding:24px;color:#94A3B8;font-size:10px;border-top:1px solid #E2E8F0;margin-top:24px;background:white}}
</style></head><body>

<div class="hero">
<h1>D&O Worksheet — Operating Dashboard</h1>
<div class="sub">System health, card tracker, data sources, brain signals, pipeline status</div>
<div class="stats">
<div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Cards</div></div>
<div class="stat"><div class="stat-num" style="color:#1D4ED8">{designed}</div><div class="stat-label">Designed</div></div>
<div class="stat"><div class="stat-num" style="color:#D97706">{data_ok}</div><div class="stat-label">Data OK</div></div>
<div class="stat"><div class="stat-num" style="color:#7C3AED">{llm_ok}</div><div class="stat-label">LLM</div></div>
<div class="stat"><div class="stat-num" style="color:#16A34A">{qa_done}</div><div class="stat-label">QA</div></div>
<div class="stat"><div class="stat-num" style="color:#64748B">{total_signals}</div><div class="stat-label">Signals</div></div>
<div class="stat"><div class="stat-num" style="color:#64748B">7</div><div class="stat-label">Pipeline</div></div>
</div>
</div>

<div class="tabs">
<div class="tab active" onclick="switchTab('cards')">Cards<span class="tab-count">{total}</span></div>
<div class="tab" onclick="switchTab('sources')">Data Sources<span class="tab-count">{len(DATA_SOURCES)}</span></div>
<div class="tab" onclick="switchTab('brain')">Brain Signals<span class="tab-count">{total_signals}</span></div>
<div class="tab" onclick="switchTab('pipeline')">Pipeline<span class="tab-count">7</span></div>
<div class="tab" onclick="switchTab('elements')">Design Elements<span class="tab-count">83</span></div>
<div class="tab" onclick="switchTab('chartlib')">Chart Library</div>
<div class="tab" onclick="switchTab('complib')">Components</div>
</div>
'''

    # ═══ TAB 1: CARDS ═══
    html += '<div class="tab-panel active" id="panel-cards">'
    current_section = -1
    for card_id, sec_num, title, sub_count, sources, subs in CARDS:
        if sec_num != current_section:
            if current_section >= 0:
                html += '</div>'
            color, name = SECTION_COLORS[sec_num]
            sec_cards = [c for c in CARDS if c[1] == sec_num]
            sec_designed = sum(1 for c in sec_cards if get_status(c[0])["designed"])
            html += f'<div id="sec-{sec_num}">'
            html += f'<div class="sec-hdr"><div class="sec-num" style="color:{color}">{sec_num:02d}</div><div class="sec-title">{name}</div><div class="sec-line" style="background:{color}"></div><div class="sec-stats">{sec_designed}/{len(sec_cards)} designed</div></div>'
            html += '<div class="card-row card-row-hdr"><div>ID</div><div>Card</div><div>Sources</div><div>Des</div><div>Data</div><div>LLM</div><div>QA</div></div>'
            current_section = sec_num

        st = get_status(card_id)
        color = SECTION_COLORS[sec_num][0]
        srcs = ' '.join(dsrc_pill(s) for s in sources)

        html += f'<div class="card-row" style="border-left-color:{color}">'
        html += f'<div class="card-id" style="color:{color}">{card_id}</div>'
        html += f'<div class="card-title-col">{title}<span class="sub-count">{sub_count} el</span></div>'
        html += f'<div class="card-sources">{srcs}</div>'
        html += f'<div class="check">{check_icon(st["designed"])}</div>'
        html += f'<div class="check">{check_icon(st["data_verified"])}</div>'
        html += f'<div class="check">{check_icon(st["llm_synthesis"])}</div>'
        html += f'<div class="check">{check_icon(st["qa_tested"])}</div>'
        html += '</div>'

        # Sub-elements dropdown
        if subs:
            type_colors = {"CHART":"#DBEAFE;color:#1D4ED8","TABLE":"#FEF3C7;color:#92400E","NARRATIVE":"#F3E8FF;color:#7C3AED","CARDS":"#DCFCE7;color:#166534","ALERT":"#FEF2F2;color:#991B1B","VERDICT":"#FEF2F2;color:#991B1B","KV":"#E0F2FE;color:#075985","VISUAL":"#EDE9FE;color:#6D28D9","TIMELINE":"#FFF7ED;color:#9A3412","BADGES":"#FEF2F2;color:#991B1B","LIST":"#F1F5F9;color:#475569","Q&A":"#F0F9FF;color:#0C4A6E","CHART+LEGEND":"#DBEAFE;color:#1D4ED8","2 CHARTS":"#DBEAFE;color:#1D4ED8","2-COL":"#FEF3C7;color:#92400E","3 VISUALS":"#EDE9FE;color:#6D28D9","4 CARDS":"#DCFCE7;color:#166534","CASE CARDS":"#FEF3C7;color:#92400E","TABLES":"#FEF3C7;color:#92400E"}
            html += f'<details style="border-left:3px solid {color};background:white;border-bottom:1px solid #F1F5F9">'
            html += f'<summary style="padding:3px 10px 3px 46px;font-size:8px;color:#94A3B8;cursor:pointer">▸ {len(subs)} elements</summary>'
            html += f'<div style="padding:2px 10px 6px 46px">'
            for letter, name, typ in subs:
                tc = type_colors.get(typ, "#F1F5F9;color:#475569")
                html += f'<div class="sub-el"><span class="sub-ltr" style="background:{color}">{letter}</span><span class="sub-nm">{name}</span><span class="sub-tp" style="background:{tc}">{typ}</span></div>'
            html += '</div></details>'

        if st["notes"]:
            html += f'<div style="border-left:3px solid {color};padding:2px 10px 3px 46px;background:white;border-bottom:1px solid #F1F5F9;font-size:8px;color:#94A3B8">{st["notes"]}</div>'

    html += '</div></div>'  # close last section + panel

    # ═══ TAB 2: DATA SOURCES ═══
    html += '<div class="tab-panel" id="panel-sources">'
    for name, bg, fg, desc, confidence, detail in DATA_SOURCES:
        conf_color = {"HIGH":"#16A34A","MEDIUM":"#D97706","LOW":"#DC2626"}.get(confidence, "#64748B")
        # Count cards using this source
        usage = sum(1 for c in CARDS if name in c[4])
        html += f'''<div class="ds-card" style="border-left:4px solid {fg}">
<div style="display:flex;align-items:center;gap:8px">
<span style="font-size:7px;font-weight:700;padding:2px 6px;border-radius:3px;background:{bg};color:{fg}">{name}</span>
<span class="ds-name">{desc}</span>
</div>
<div class="ds-meta">
<span>Confidence: <span class="ds-badge" style="background:{conf_color};color:white">{confidence}</span></span>
<span>Used by: <b>{usage}</b> cards</span>
<span>{detail}</span>
</div></div>'''
    html += '</div>'

    # ═══ TAB 3: BRAIN SIGNALS ═══
    html += '<div class="tab-panel" id="panel-brain">'
    html += '<div class="brain-row" style="font-weight:700;color:#64748B;font-size:8px;text-transform:uppercase">'\
            '<div>Category</div><div>Name</div><div>Signals</div><div>Skipped</div><div>Coverage</div></div>'
    for cat, name, count, skipped in BRAIN_CATEGORIES:
        active = count - skipped
        pct = active / count * 100 if count else 0
        bar_color = "#16A34A" if pct > 80 else "#D97706" if pct > 60 else "#DC2626"
        html += f'''<div class="brain-row">
<div style="font-weight:700;font-family:'JetBrains Mono',monospace;color:#64748B">{cat}</div>
<div style="font-weight:600">{name}</div>
<div style="text-align:center">{count}</div>
<div style="text-align:center;color:#DC2626">{skipped}</div>
<div><div class="brain-bar"><div class="brain-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div><div style="font-size:8px;color:#94A3B8;text-align:center">{pct:.0f}%</div></div>
</div>'''
    html += f'<div style="padding:12px;font-size:11px;color:#64748B;font-weight:600">Total: {total_signals} signals · {skipped_signals} skipped · {total_signals-skipped_signals} active ({(total_signals-skipped_signals)/total_signals*100:.0f}%)</div>'
    html += '</div>'

    # ═══ TAB 4: PIPELINE ═══
    html += '<div class="tab-panel" id="panel-pipeline">'
    for i, (stage, desc, color) in enumerate(PIPELINE_STAGES):
        html += f'''<div class="pipe-stage">
<div class="pipe-num" style="background:{color}">{i+1}</div>
<div style="flex:1"><div style="font-size:13px;font-weight:800">{stage}</div><div style="font-size:10px;color:#64748B">{desc}</div></div>
</div>'''
        if i < len(PIPELINE_STAGES) - 1:
            html += '<div class="pipe-arrow">↓</div>'
    html += '</div>'

    # ═══ TAB 5: DESIGN ELEMENTS ═══
    ELEMENT_GROUPS = [
        ("Cards", "#0F172A", [
            ("MetricCard", "Large bold number + label + trend + colored bg", "6 variants (Green/Amber/Red/Blue/Purple/Default)", "Bloomberg KPI tiles"),
            ("RiskCard", "Title + severity badge + evidence bullets + colored left border", "3 severity levels", "Economist risk boxes"),
            ("KeyValueCard", "Compact labeled pairs, 1-2 column grid", "1Col, 2Col", "Capital IQ fact tables"),
            ("AlertCard", "Prominent notification + pills + colored border", "Red/Amber/Green/Blue", "WSJ breaking alerts"),
            ("ComparisonCard", "Side-by-side metric comparison, auto-colored", "", "Economist comparisons"),
            ("TimelineCard", "Vertical timeline + colored dots + connecting line", "", "NYT event timelines"),
            ("DataTableCard", "Compact table + navy header + row count badge", "", "Bloomberg data grids"),
            ("NarrativeCard", "Text block + left accent border + title bar", "Blue/Navy/Green/Amber/Red", "Economist analysis boxes"),
            ("MetricStrip", "Horizontal grid of metric cards (1-6 cols)", "", "Bloomberg header strip"),
        ]),
        ("Badges & Pills", "#7C3AED", [
            ("StatusBadge", "Colored pill for check results", "TRIGGERED/CLEAR/ELEVATED/SKIPPED/INFO", ""),
            ("TierBadge", "Underwriting recommendation pill", "WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH", ""),
            ("VerdictBadge", "Section verdict pill", "FAVORABLE/NEUTRAL/CONCERNING/CRITICAL", ""),
            ("PillBadgeRow", "Flex-wrapped row of classification pills", "", ""),
            ("DimensionBadge", "Tiny H/A/E risk dimension pills", "H(blue)/A(red)/E(green)", ""),
            ("ConfidenceMarker", "Small italic gray data quality note", "", ""),
            ("FactorTag", "Small pill showing factor codes", "", ""),
        ]),
        ("Callouts & Containers", "#D97706", [
            ("DiscoveryBox", "Gold left border callout for blind spot findings", "", "NYT 'What We Found'"),
            ("WarningBox", "Amber left border for elevated findings", "", ""),
            ("GapNotice", "Gray data unavailability notice", "", ""),
            ("ContextNote", "Small italic D&O relevance explanation", "", ""),
            ("SCRBlock", "Situation-Complication-Resolution framework", "", "McKinsey pyramid"),
            ("ImplicationsBox", "Navy left border + D&O implications bullets", "", ""),
            ("InsightBox", "Navy left border + 'UNDERWRITING INSIGHT' label", "", ""),
        ]),
        ("Inline Charts & Infographics", "#1D4ED8", [
            ("Sparkline", "Lightweight inline trend (60x16px), auto-colored", "Up/Down/Flat", "Tufte sparklines"),
            ("TrendArrow", "Tiny directional triangle (12x12px)", "Up/Down/Flat", ""),
            ("FactorBar", "Horizontal bar showing points/max with color intensity", "", "Economist progress bars"),
            ("ScoreGauge", "Semi-circular 180° arc, 0-100 with needle", "", "Dashboard gauges"),
            ("DecileDots", "10 rounded squares showing distribution position", "", "NYT dot distributions"),
            ("RangeSlider", "Position indicator between low/high", "", "Bloomberg range bars"),
            ("CompositionBar", "Stacked horizontal cash/debt bar", "", "Economist stacked bars"),
            ("EarningsCircles", "8px colored circles for beat/miss history", "", "NYT win/loss"),
            ("SeverityBlocks", "5-block severity bar (filled vs empty)", "", ""),
            ("EquityLiabilityBar", "Two-color mini equity/liability split", "", ""),
            ("SpectrumBar", "Market cap tier position indicator", "", ""),
            ("DataSourcePill", "Colored provenance pill (XBRL/yfinance/LLM/etc)", "", ""),
        ]),
        ("Full Charts (Matplotlib)", "#DC2626", [
            ("StockPerformanceChart", "Price + sector overlay + drops + volume", "1Y/5Y/2Y unified", "Bloomberg equity"),
            ("RelativePerformanceChart", "Indexed to 100, company vs sector vs S&P", "", "WSJ performance"),
            ("VolatilityChart", "Rolling vol + beta with zone backgrounds", "", "Risk analytics"),
            ("DrawdownChart", "Running drawdown with max annotation", "", "Hedge fund analysis"),
            ("RadarChart", "10-spoke polar factor risk profile", "", "Economist radars"),
            ("WaterfallChart", "Factor deductions stacking from 100 (SVG)", "", "McKinsey waterfall"),
            ("TornadoChart", "Horizontal sensitivity bars (SVG)", "", "Actuarial sensitivity"),
            ("LitigationTimeline", "Horizontal timeline with category markers", "", "NYT timelines"),
            ("OwnershipDonut", "Institutional/insider/retail donut", "", "Capital IQ ownership"),
            ("PxSMatrix", "Probability × severity 2D zones", "", "Risk management"),
            ("DropAnalysisChart", "Price + drop events + catalyst attribution", "", "Investigative journalism"),
            ("InsiderTimeline", "Stock price + insider trade overlays", "", ""),
            ("DebtMaturityChart", "Near-term (red) vs future (blue) bars", "", "Moody's maturity"),
        ]),
        ("Tables", "#059669", [
            ("DataTable", "Full-width, navy header, alternating rows, tabular-nums", "", "Bloomberg grids"),
            ("KeyValueTable", "2-column facts with light header", "", "Capital IQ panels"),
            ("PairedKVTable", "4 cols/row for CIQ-density (Label|Value|Label|Value)", "", "S&P Capital IQ"),
            ("FinancialRow", "Label|Current|Prior|YoY with color arrows", "", "Earnings releases"),
            ("CheckSummaryTable", "Signal results with severity-colored rows", "", ""),
            ("EvidenceTable", "Indicator|Value|Source with severity coloring", "", ""),
        ]),
        ("Narrative Frameworks", "#6D28D9", [
            ("Narrative5Layer", "Verdict → thesis → evidence → context → implications", "", "McKinsey structure"),
            ("BullBearFraming", "Two-column positive/negative analysis", "", "Sell-side research"),
            ("EvidenceChain", "Bulleted evidence with source citations", "", ""),
            ("DualVoice", "'What Was Said' + 'Underwriting Commentary'", "", "Audit dual-perspective"),
        ]),
    ]

    html += '<div class="tab-panel" id="panel-elements">'
    for group_name, group_color, elements in ELEMENT_GROUPS:
        html += f'<div class="sec-hdr"><div class="sec-num" style="color:{group_color}">●</div><div class="sec-title">{group_name}</div><div class="sec-line" style="background:{group_color}"></div><div class="sec-stats">{len(elements)} elements</div></div>'
        for name, desc, variants, inspiration in elements:
            html += f'<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid #F1F5F9;background:white;border-left:3px solid {group_color}">'
            html += f'<div style="font-size:11px;font-weight:800;color:{group_color};min-width:160px;font-family:\'JetBrains Mono\',monospace">{name}</div>'
            html += f'<div style="font-size:10px;color:#334155;flex:1">{desc}</div>'
            if variants:
                html += f'<div style="font-size:8px;color:#64748B;min-width:120px">{variants}</div>'
            if inspiration:
                html += f'<div style="font-size:7px;color:#94A3B8;font-style:italic;min-width:100px">{inspiration}</div>'
            html += '</div>'
    html += '</div>'

    # ═══ TAB 6: CHART LIBRARY ═══
    # Organized by DATA INTENT — what are you trying to show?
    CHART_LIB = [
        ("Trend Over Time", "#0F172A", [
            ("L-01","Line-Dark-Gold","Price on dark navy, gold line, area fill","Bloomberg terminal","Full / 2-up"),
            ("L-02","Line-Dark-Blue","Sky blue on deep slate","Slate Modern","Full / 2-up"),
            ("L-03","Line-Dark-Glow","Orange with glow effect on navy","Liberty warm","Full / 2-up"),
            ("L-04","Line-Dark-Teal","Teal glow on near-black","Midnight","Full / 2-up"),
            ("L-05","Line-Dark-Purple","Electric purple on charcoal","Neon","Full / 2-up"),
            ("L-06","Line-Light-WSJ","Black on white, minimal grid","WSJ Classic","Full / 2-up"),
            ("L-07","Line-Light-Economist","Red decline on cream background","Economist","Full / 2-up"),
            ("L-08","Line-Light-FT","Dark line on salmon-pink","FT Salmon","Full / 2-up"),
            ("L-09","Line-Light-Mint","Green on white, clean grid","Minimal","Full / 2-up"),
            ("L-10","Line-Light-Ice","Deep blue on ice-blue bg","Cool tone","Full / 2-up"),
            ("L-11","Line-Light-Sand","Brown on warm beige","Warm tone","Full / 2-up"),
            ("L-12","Line-GradientFill","Blue gradient fade area fill","Modern","Full / 2-up"),
            ("L-13","Line-MultiIndex","3+ series indexed to 100, over/under shading","WSJ comparison","Full-width only"),
            ("L-14","Line-StepFunction","Discrete step changes (ratings, tiers)","Academic","Full / 2-up"),
            ("L-15","Line-HighContrast","White on black with colored data points","Terminal","Full / 2-up"),
            ("L-16","Area-Stacked","Multiple series stacked areas","NYT","Full-width"),
            ("L-17","Area-StreamGraph","Flowing stacked areas (sentiment over time)","NYT","Full-width"),
            ("L-18","Horizon-Chart","Compressed multi-series (rolling vol bands)","Bloomberg","Strip"),
            ("L-19","Small-Multiples","Grid of mini-charts (one per metric)","Tufte","Grid"),
            ("L-20","Sparkline-Area-Up","Micro trend, green area fill","Inline","60x16px"),
            ("L-21","Sparkline-Area-Down","Micro trend, red area fill","Inline","60x16px"),
            ("L-22","Sparkline-Bar","Micro quarterly bars (beat/miss)","Inline","80x20px"),
            ("L-23","Sparkline-DotStrip","Colored dots per period","Inline","80x20px"),
            ("L-24","Sparkline-WinLoss","Square blocks up/down","Inline","80x20px"),
            ("L-25","Sparkline-Bullet","Value vs range with target","Inline","80x20px"),
            ("L-26","Candlestick","OHLC candles (quarterly/monthly)","Trading","Full / 2-up"),
        ]),
        ("Comparison", "#DC2626", [
            ("C-01","Bar-Vertical-Simple","Single metric across categories","Standard","Full / 2-up"),
            ("C-02","Bar-Vertical-Grouped","Side-by-side (company vs peer, FY vs FY-1)","Economist","Full / 2-up"),
            ("C-03","Bar-Vertical-Progressive","Same metric, progressive opacity (time)","Modern","Full / 2-up"),
            ("C-04","Bar-Horizontal-Labeled","Labeled bars with values (factor scores)","McKinsey","Full / 2-up"),
            ("C-05","Bar-Horizontal-Lollipop","Thin line + endpoint dot","Clean","Full / 2-up"),
            ("C-06","Bar-Horizontal-Dumbbell","Two dots connected (before/after)","Economist","Full / 2-up"),
            ("C-07","Slope-Chart","Two-point comparison (FY24 → FY25)","Tufte","2-up / Card"),
            ("C-08","Dot-Plot","Dots on axis showing position vs peers","Bloomberg","Full / Card"),
            ("C-09","Bullet-Chart","Value vs qualitative ranges + target","Dashboard","Card / Strip"),
            ("C-10","Parallel-Coordinates","Multi-axis comparison of peers","Academic","Full-width"),
            ("C-11","Side-by-Side-Metric","Two big numbers compared","Economist","Card"),
            ("C-12","Diverging-Bar","Positive/negative from center (tornado)","Sensitivity","Full / 2-up"),
        ]),
        ("Composition (Part-to-Whole)", "#7C3AED", [
            ("P-01","Stacked-Bar-100","Full-width segment breakdown (revenue mix)","Economist","Full / Strip"),
            ("P-02","Stacked-Bar-Abs","Absolute values stacked","Standard","Full / 2-up"),
            ("P-03","Donut-Simple","Single metric with center text","Capital IQ","Card"),
            ("P-04","Donut-Multi","Multiple rings (nested breakdown)","Bloomberg","Card"),
            ("P-05","Waffle-Chart","100-square grid showing proportion","NYT","Card"),
            ("P-06","Treemap","Nested rectangles by size","Bloomberg","Full / Card"),
            ("P-07","Marimekko","Variable-width stacked bars","Economist","Full"),
            ("P-08","Composition-Bar","Horizontal thin bar (cash vs debt)","Inline","Strip"),
            ("P-09","Equity-Liability-Split","Two colored boxes side by side","Inline","Mini-card"),
            ("P-10","Tier-Distribution","Colored zones (WIN/WANT/WRITE/etc)","Custom","Strip"),
        ]),
        ("Distribution & Ranking", "#059669", [
            ("D-01","Histogram","Frequency distribution bins","Standard","Full / 2-up"),
            ("D-02","Box-Plot","Quartiles + outliers","Academic","Full / 2-up"),
            ("D-03","Strip-Plot","Individual data points on axis","Tufte","Card"),
            ("D-04","Beeswarm","Clustered dots avoiding overlap","NYT","Card"),
            ("D-05","Ridgeline","Overlapping density curves","Academic","Full"),
            ("D-06","Violin","Box plot + density combined","Academic","2-up"),
            ("D-07","Decile-Dots","10 blocks showing position","Custom","Inline"),
            ("D-08","Range-Slider","Position between min/max","Custom","Inline"),
            ("D-09","Percentile-Bar","Position in peer distribution","Bloomberg","Strip"),
            ("D-10","Rank-Table","Colored by rank (1st green → last red)","Economist","Table"),
        ]),
        ("Risk Assessment", "#D97706", [
            ("R-01","Heat-Map-PxS","Probability × Severity matrix","Risk mgmt","Full / Card"),
            ("R-02","Heat-Map-Quarterly","Color-coded quarterly grid","NYT Calendar","Full / Card"),
            ("R-03","Heat-Map-Correlation","Pairwise correlation matrix","Bloomberg","Full"),
            ("R-04","Radar-Dark","10-spoke spider on dark bg","Economist","Card"),
            ("R-05","Radar-Light","Spider on white with data points","Minimal","Card"),
            ("R-06","Gauge-Semicircle","180° arc score (quality score)","Dashboard","Card"),
            ("R-07","Gauge-LinearBar","Horizontal bar with tier zones","Custom","Strip"),
            ("R-08","Traffic-Light-Grid","Red/amber/green signal grid","Audit","Table"),
            ("R-09","Severity-Blocks","5-block filled/empty bars","Custom","Inline"),
            ("R-10","Piotroski-Grid","9-cell check/cross grid","Custom","Card"),
            ("R-11","Zone-Scale","Distress/Grey/Safe with marker","Custom","Card"),
            ("R-12","Risk-Dots","Colored dots per category","Custom","Inline"),
        ]),
        ("Flow & Process", "#0891B2", [
            ("F-01","Waterfall-Score","100 → deductions → final score","McKinsey","Full"),
            ("F-02","Waterfall-Financial","Bridge from revenue to net income","Standard","Full"),
            ("F-03","Tornado-Sensitivity","Left/right bars from center","Actuarial","Full / 2-up"),
            ("F-04","Sankey","Flow diagram (revenue sources → uses)","D3","Full"),
            ("F-05","Funnel","Narrowing stages","Standard","Card"),
            ("F-06","Timeline-Horizontal","Events on time axis","NYT","Full / Strip"),
            ("F-07","Timeline-Vertical","Events stacked vertically","Standard","Card"),
            ("F-08","Gantt-Bars","Duration bars (debt maturity)","Standard","Full"),
        ]),
        ("Layout Formats", "#64748B", [
            ("FMT-01","Full-Width-Strip","40px tall, stretches full width","Bloomberg","Strip header"),
            ("FMT-02","Full-Width-Standard","Standard height, full width","Standard","Chart"),
            ("FMT-03","Two-Up-Side-by-Side","Two charts same height, 50/50","Comparison","1Y vs 5Y"),
            ("FMT-04","Two-Up-Unequal","60/40 split (chart + detail)","Dashboard","Chart + KV"),
            ("FMT-05","Card-Framed","Chart inside card with header","Catalog","Any"),
            ("FMT-06","Grid-Small-Multiples","2x3 or 3x3 mini-charts","Tufte","Metrics grid"),
            ("FMT-07","Inline-Sparkline","Inside table cell or KV pair","Tufte","60x16px"),
            ("FMT-08","Dashboard-Tile","Mini-card with chart inside","Bloomberg","Mini-card"),
        ]),
    ]

    html += '<div class="tab-panel" id="panel-chartlib">'
    html += '<div style="font-size:10px;color:#64748B;margin-bottom:12px">Reference any chart by its ID (e.g., L-07, C-03, R-01). Organized by what you\'re trying to show.</div>'
    for group_name, group_color, items in CHART_LIB:
        html += f'<div class="sec-hdr"><div class="sec-num" style="color:{group_color}">●</div><div class="sec-title">{group_name}</div><div class="sec-line" style="background:{group_color}"></div><div class="sec-stats">{len(items)} options</div></div>'
        for ref_id, name, desc, inspiration, size in items:
            html += f'<div style="display:grid;grid-template-columns:50px 140px 1fr 80px 80px;gap:6px;padding:5px 10px;border-bottom:1px solid #F1F5F9;background:white;border-left:3px solid {group_color};font-size:9px;align-items:center">'
            html += f'<div style="font-family:\'JetBrains Mono\',monospace;font-weight:800;color:{group_color};font-size:10px">{ref_id}</div>'
            html += f'<div style="font-weight:700;color:#1E293B">{name}</div>'
            html += f'<div style="color:#64748B">{desc}</div>'
            html += f'<div style="font-size:7px;color:#94A3B8;font-style:italic">{inspiration}</div>'
            html += f'<div style="font-size:7px;color:#64748B;font-weight:600">{size}</div>'
            html += '</div>'
    total_charts = sum(len(items) for _, _, items in CHART_LIB)
    html += f'<div style="padding:12px;font-size:10px;color:#64748B"><b>{total_charts}</b> chart options across {len(CHART_LIB)} categories. Visual examples: <code>python3 scripts/build_chart_gallery.py && open output/CHART_GALLERY.html</code></div>'
    html += '</div>'

    # ═══ TAB 7: COMPONENT LIBRARY ═══
    COMP_LIB = [
        ("Cards", "#0F172A", [
            ("CARD-01","MetricCard","Large bold value + label + trend, 6 color variants"),
            ("CARD-02","RiskCard","Title + severity badge + evidence bullets + colored border"),
            ("CARD-03","KeyValueCard","Compact labeled pairs, 1-2 columns"),
            ("CARD-04","AlertCard","Prominent notification + pills + colored border"),
            ("CARD-05","ComparisonCard","Side-by-side metric comparison"),
            ("CARD-06","TimelineCard","Vertical timeline + colored dots + connecting line"),
            ("CARD-07","DataTableCard","Compact table + header + row count badge"),
            ("CARD-08","NarrativeCard","Text block + left accent border + title bar"),
            ("CARD-09","MetricStrip","Horizontal grid of metric cards (1-6 cols)"),
            ("CARD-10","CompositionCard","Chart + ratios + context in one card (balance sheet style)"),
        ]),
        ("Badges & Pills", "#7C3AED", [
            ("BADGE-01","StatusBadge","TRIGGERED/CLEAR/ELEVATED/SKIPPED/INFO pills"),
            ("BADGE-02","TierBadge","WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH"),
            ("BADGE-03","VerdictBadge","FAVORABLE/NEUTRAL/CONCERNING/CRITICAL"),
            ("BADGE-04","PillBadgeRow","Classification attributes (Delaware, NYSE, Large Cap)"),
            ("BADGE-05","DataSourcePill","XBRL/yfinance/LLM/Web/SEC/Computed/Supabase"),
            ("BADGE-06","DimensionBadge","H/A/E risk dimension tiny pills"),
            ("BADGE-07","FactorTag","Factor code reference pills"),
            ("BADGE-08","ConfidenceMarker","Small italic data quality note"),
            ("BADGE-09","SeverityDot","8px colored circle (red/amber/green)"),
            ("BADGE-10","CountBadge","Number in circle (finding count, case count)"),
        ]),
        ("Callouts & Containers", "#D97706", [
            ("CALL-01","DiscoveryBox","Gold border — blind spot finding"),
            ("CALL-02","WarningBox","Amber border — elevated concern"),
            ("CALL-03","InsightBox","Navy border — underwriting insight"),
            ("CALL-04","GapNotice","Gray — data unavailability"),
            ("CALL-05","SCRBlock","Situation-Complication-Resolution framework"),
            ("CALL-06","DualVoice","What Was Said + Underwriting Commentary"),
            ("CALL-07","ImplicationsBox","D&O implications bullet list"),
            ("CALL-08","ContextNote","Small italic D&O relevance note"),
            ("CALL-09","DensityIndicator","Red/amber risk level flag"),
            ("CALL-10","BullBearFraming","Two-column positive vs negative"),
        ]),
        ("Inline Infographics", "#1D4ED8", [
            ("INF-01","Sparkline","60x16px inline trend line (6 variants: area/bar/dot/winloss/bullet)"),
            ("INF-02","TrendArrow","12x12px directional triangle"),
            ("INF-03","FactorBar","Horizontal points/max with color intensity"),
            ("INF-04","DecileDots","10 rounded squares showing distribution position"),
            ("INF-05","RangeSlider","Position between low/high (52W range)"),
            ("INF-06","CompositionBar","Stacked cash/debt bar"),
            ("INF-07","EarningsCircles","8px circles for beat/miss history"),
            ("INF-08","SeverityBlocks","5-block filled/empty severity bar"),
            ("INF-09","EquityLiabilityBar","Two-color mini equity/liability split"),
            ("INF-10","ScorePositionBar","Linear 0-100 bar with tier zones"),
            ("INF-11","SpectrumBar","Market cap tier position indicator"),
            ("INF-12","ProgressRing","Circular percentage indicator"),
        ]),
        ("Tables", "#059669", [
            ("TBL-01","DataTable","Full-width, navy header, alternating rows"),
            ("TBL-02","KeyValueTable","2-column facts table"),
            ("TBL-03","PairedKVTable","4 cols/row CIQ-density"),
            ("TBL-04","FinancialRow","Label|Current|Prior|YoY with arrows"),
            ("TBL-05","CheckSummaryTable","Signal results with severity rows"),
            ("TBL-06","EvidenceTable","Indicator|Value|Source with severity"),
            ("TBL-07","CompactTable","Borderless, ultra-tight spacing"),
            ("TBL-08","HeatTable","Color-coded cell backgrounds by value"),
        ]),
        ("Narrative Frameworks", "#6D28D9", [
            ("NARR-01","Narrative5Layer","Verdict → thesis → evidence → context → implications"),
            ("NARR-02","BullBearFraming","Two-column positive/negative"),
            ("NARR-03","EvidenceChain","Bulleted evidence with citations"),
            ("NARR-04","DualVoice","Factual + analytical commentary pair"),
            ("NARR-05","SCRBlock","Situation → Complication → Resolution"),
            ("NARR-06","ExecSummary","Tier + key concerns/positives + recommendation"),
        ]),
    ]

    html += '<div class="tab-panel" id="panel-complib">'
    html += '<div style="font-size:10px;color:#64748B;margin-bottom:12px">Reference any component by its ID (e.g., CARD-03, BADGE-02, INF-07). Visual examples: <code>open output/DESIGN_GALLERY_v2.html</code></div>'
    for group_name, group_color, items in COMP_LIB:
        html += f'<div class="sec-hdr"><div class="sec-num" style="color:{group_color}">●</div><div class="sec-title">{group_name}</div><div class="sec-line" style="background:{group_color}"></div><div class="sec-stats">{len(items)}</div></div>'
        for ref_id, name, desc in items:
            html += f'<div style="display:grid;grid-template-columns:60px 140px 1fr;gap:6px;padding:5px 10px;border-bottom:1px solid #F1F5F9;background:white;border-left:3px solid {group_color};font-size:9px;align-items:center">'
            html += f'<div style="font-family:\'JetBrains Mono\',monospace;font-weight:800;color:{group_color};font-size:10px">{ref_id}</div>'
            html += f'<div style="font-weight:700;color:#1E293B">{name}</div>'
            html += f'<div style="color:#64748B">{desc}</div>'
            html += '</div>'
    total_comps = sum(len(items) for _, _, items in COMP_LIB)
    html += f'<div style="padding:12px;font-size:10px;color:#64748B"><b>{total_comps}</b> components across {len(COMP_LIB)} categories</div>'
    html += '</div>'

    # Tab switching JS
    html += '''
<script>
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector('.tab-panel#panel-' + name).classList.add('active');
  event.target.classList.add('active');
}
</script>
'''

    html += f'''<div class="footer">
<p><strong>Operating Dashboard</strong> — {total} cards · {len(DATA_SOURCES)} data sources · {total_signals} brain signals · 7 pipeline stages</p>
</div></body></html>'''

    return html


if __name__ == "__main__":
    html = build_html()
    out = Path("output/OPS_DASHBOARD.html")
    out.write_text(html)
    print(f"Generated: {len(CARDS)} cards, {len(DATA_SOURCES)} sources, {sum(c[2] for c in BRAIN_CATEGORIES)} signals")
