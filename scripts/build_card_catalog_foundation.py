#!/usr/bin/env python3
"""Generate the D&O Worksheet Card Catalog HTML from structured card definitions."""

import json
from textwrap import dedent

# ── Card definitions ──
# Each card: (id, section, title, description, sub_elements, data_sources, colors)
# sub_elements: list of (letter, name, type, note)
# data_sources: list of (css_class, label)
# colors: list of (hex, label)

SECTIONS = [
    ("sec-0", "0", "Decision Dashboard", "#0F172A", "c-dash"),
    ("sec-1", "1", "Executive Summary", "#6D28D9", "c-brief"),
    ("sec-2", "2", "Company & Operations", "#0369A1", "c-company"),
    ("sec-3", "3", "Stock & Market", "#EA580C", "c-market"),
    ("sec-4", "4", "Financial Analysis", "#059669", "c-financial"),
    ("sec-5", "5", "People & Governance", "#D97706", "c-governance"),
    ("sec-6", "6", "Legal & Litigation", "#DC2626", "c-litigation"),
    ("sec-7", "7", "Sector & Industry", "#7C3AED", "c-industry"),
    ("sec-8", "8", "Scoring & Underwriting", "#0891B2", "c-scoring"),
    ("sec-9", "9", "UW Decision Framework", "#4338CA", "c-uw"),
    ("sec-10", "10", "Meeting Preparation", "#BE185D", "c-meeting"),
    ("sec-11", "11", "Audit Trail", "#64748B", "c-audit"),
]

CARDS = [
    # ── Section 0: Decision Dashboard ──
    {
        "id": "00", "section": 0, "title": "Decision Dashboard (Page-0)",
        "desc": "One continuous card — the entire first page. 5Y stock strip → 6 financial mini-cards → litigation status bar → 2Y investigative drop chart → key risk findings → UW priority metrics → plaintiff exposure matrix.",
        "subs": [
            ("A", "5-Year Stock Performance Strip", "CHART", "Full-width dark navy (#1A1A2E), weekly data, gold label"),
            ("B", "6 Mini-Cards (Financial Snapshot)", "6 CARDS", "MCap & Valuation (purple) | Stock Price & Range (orange) | Revenue & Growth (green) | Profitability & Cash Flow (red) | Balance Sheet (green, densest) | Valuation Multiples (blue)"),
            ("C", "Litigation & Regulatory Status Bar", "ALERT", "Red/green bg conditional. SCA/Derivative/Other badges. Case names. Regulatory agency status. D&O lit history tier (CRITICAL/WATCH/MONITOR/CLEAR) with narrative."),
            ("D", "2-Year Combo Stock Chart (Drop Investigation)", "CHART+LEGEND", "Price line (orange glow) + sector ETF overlay + numbered drop markers + cluster spans + event markers. Legend table: # | Date | Drop% | Duration | Catalyst | Category. DDL per event."),
            ("E", "Key Risk Findings", "ALERT", "Red header. Severity circles + headline + score badge + evidence bullets (jargon-stripped). Score/findings reconciliation note."),
            ("F", "Underwriter Priority Metrics", "4 CARDS", "EPS Beat Streak | Forward Estimate Spread (wider=higher miss risk) | Analyst Trend (90d) | Key Dates Calendar"),
            ("G", "Plaintiff Exposure Matrix", "TABLE", "Per exposure type: 5-block severity bar + probability + severity. Securities Fraud, Derivative, Employment, Regulatory, etc."),
        ],
        "sources": [
            ("dsrc-xbrl", "XBRL: revenue, assets, equity, liabilities, debt, cash, goodwill, ratios"),
            ("dsrc-yfinance", "yfinance: price, 52W range, P/E, EPS, beta, shares, employees, earnings dates, analyst data"),
            ("dsrc-computed", "Computed: D/E, current ratio, interest coverage, ND/EBITDA, DDL, drop detection"),
            ("dsrc-llm", "LLM: D&O context insights, drop catalyst synthesis, key risk findings"),
            ("dsrc-web", "Web Search: drop investigation catalysts, news events"),
            ("dsrc-sec", "SEC/EDGAR: 8-K events, filing dates, litigation data"),
            ("dsrc-supabase", "Supabase SCA DB: active SCA count, case names"),
        ],
        "colors": [("#0F172A", "header"), ("#1A1A2E", "chart bg"), ("#D4A843", "gold label"), ("#F5F3FF", "purple card"), ("#FFF7ED", "orange card"), ("#F0FDF4", "green card"), ("#FEF2F2", "red card"), ("#EFF6FF", "blue card")],
    },
    # ── Section 1: Executive Summary ──
    {
        "id": "01", "section": 1, "title": "Recommendation & Red Flags",
        "desc": "Tier verdict, critical red flags with evidence, key negatives vs positives with point scores.",
        "subs": [
            ("A", "Recommendation Box", "VERDICT", "Dark blue header: tier name + action + probability band + claim band"),
            ("B", "Critical Red Flags", "ALERT", "Bullet list with evidence. Only renders if flags exist."),
            ("C", "Key Negatives & Positives (2-column)", "TABLE", "Left: negatives (red points). Right: positives (green points)."),
        ],
        "sources": [("dsrc-computed", "Scoring: tier, quality score, probability band, factor scores"), ("dsrc-llm", "LLM: red flag synthesis")],
        "colors": [("#6D28D9", "header"), ("#DC2626", "red flags"), ("#16A34A", "positives")],
    },
    {
        "id": "02", "section": 1, "title": "Risk Thesis & Commentary",
        "desc": "Structured risk thesis with factors/mitigations/conditions, plus dual-voice commentary.",
        "subs": [
            ("A", "Risk Thesis", "NARRATIVE", "Risk Factors (red bullets) → Mitigating Factors (green) → Recommended Conditions (orange numbered) → Recommendation"),
            ("B", "Dual-Voice Commentary", "NARRATIVE", "'What Was Said' (factual) + 'Underwriting Commentary' (analytical)"),
        ],
        "sources": [("dsrc-llm", "LLM: thesis generation, dual-voice commentary")],
        "colors": [("#6D28D9", "header")],
    },
    # ── Section 2: Company ──
    {
        "id": "03", "section": 2, "title": "Business Description & Revenue Model",
        "desc": "Who they are and how they make money. LLM-synthesized 4-part profile + classification cards.",
        "subs": [
            ("A", "Company Profile (LLM 4-section)", "NARRATIVE", "Overview → Risk Landscape → Structural/Concentration Risk → D&O Implications (red callout)"),
            ("B", "Summary Cards (6)", "CARDS", "Filer Category | Exchange | Years Public | Revenue Model | Disruption Risk | Key Person Risk"),
            ("C", "How [Company] Makes Money", "NARRATIVE", "Business model narrative"),
            ("D", "What the Company Does", "KV", "Classification: SIC, GICS, NAICS, State, FYE, MCap decile"),
            ("E", "Revenue Model Card", "KV", "Revenue model type, description"),
        ],
        "sources": [("dsrc-sec", "SEC: 10-K Item 1, SIC/NAICS, filer category"), ("dsrc-llm", "LLM: company profile, business model extraction"), ("dsrc-computed", "Computed: risk classification, years public")],
        "colors": [("#0369A1", "header")],
    },
    {
        "id": "04", "section": 2, "title": "Revenue Deep Dive",
        "desc": "Revenue segments, unit economics, growth decomposition, revenue recognition policy.",
        "subs": [
            ("A", "Revenue Segments", "TABLE", "Segment name, revenue, % of total, growth"),
            ("B", "Unit Economics", "TABLE", "Key unit metrics"),
            ("C", "Revenue Waterfall (Growth Decomposition)", "TABLE", "Organic vs inorganic, volume vs price"),
            ("D", "Revenue Recognition (ASC 606)", "KV", "How aggressive is the accounting?"),
            ("E", "Revenue Mix Bar", "CHART", "Horizontal stacked bar — segment proportions"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: revenue segments, geographic data"), ("dsrc-llm", "LLM: unit economics, revenue model extraction")],
        "colors": [("#0369A1", "header")],
    },
    {
        "id": "05", "section": 2, "title": "Concentration Risk",
        "desc": "Customer, supplier, and geographic concentration — key D&O exposure indicators.",
        "subs": [
            ("A", "Customer Concentration", "TABLE", "Top customers, % revenue"),
            ("B", "Supplier Concentration", "TABLE", "Key suppliers, dependency"),
            ("C", "Concentration Assessment", "TABLE", "Overall concentration risk verdict"),
            ("D", "Geographic Footprint", "TABLE", "Region | Detail — 2-column layout"),
        ],
        "sources": [("dsrc-llm", "LLM: concentration extraction from 10-K"), ("dsrc-xbrl", "XBRL: geographic segment data")],
        "colors": [("#0369A1", "header")],
    },
    {
        "id": "06", "section": 2, "title": "Risk Factors & D&O Exposure",
        "desc": "10-K risk factors categorized by D&O relevance, exposure factor badges, emerging risks.",
        "subs": [
            ("A", "Risk Factors (D&O-Relevant)", "TABLE", "Category-grouped with severity ratings. NEW badges for latest filing."),
            ("B", "D&O Exposure Factors", "BADGES", "Badge row with tooltips: complexity, geography, M&A, insider ownership"),
            ("C", "Emerging Risk Radar", "TABLE", "AI disruption, ESG, cyber, climate, regulatory"),
            ("D", "Risk Classification Verdict", "VERDICT", "BINARY_EVENT / GROWTH_DARLING / GUIDANCE_DEPENDENT / CYCLICAL etc."),
        ],
        "sources": [("dsrc-sec", "SEC: 10-K Item 1A risk factors"), ("dsrc-llm", "LLM: risk factor extraction, classification, emerging risk synthesis"), ("dsrc-computed", "Computed: risk classification type")],
        "colors": [("#0369A1", "header"), ("#DC2626", "red severity"), ("#F59E0B", "amber")],
    },
    {
        "id": "07", "section": 2, "title": "10-K YoY Analysis & Peer SCA",
        "desc": "Year-over-year 10-K changes, risk factor review, peer group SCA contagion.",
        "subs": [
            ("A", "10-K Year-over-Year Analysis", "TABLE", "New/removed/changed risk factors between FY and FY-1"),
            ("B", "Risk Factor Review", "TABLE", "Detailed review of changed factors"),
            ("C", "Peer SCA Contagion", "TABLE", "Peer group lawsuit exposure from Supabase SCA DB"),
        ],
        "sources": [("dsrc-sec", "SEC: 10-K (current + prior year)"), ("dsrc-llm", "LLM: YoY diff extraction"), ("dsrc-supabase", "Supabase: peer SCA filings")],
        "colors": [("#0369A1", "header")],
    },
    {
        "id": "08", "section": 2, "title": "Sector Risk, Regulatory & News",
        "desc": "Industry-specific D&O concerns, regulatory environment, recent key events.",
        "subs": [
            ("A", "Sector-Specific D&O Concerns", "NARRATIVE", "Industry-specific: biotech 4-pillar, industrials env/product/cyclical, etc."),
            ("B", "Regulatory Environment", "NARRATIVE", "Applicable regulators, enforcement trends, compliance posture"),
            ("C", "Key Events & News", "TIMELINE", "Recent significant events, chronological"),
        ],
        "sources": [("dsrc-web", "Web Search: news, regulatory actions"), ("dsrc-llm", "LLM: sector-specific analysis, regulatory synthesis"), ("dsrc-sec", "SEC: industry classification")],
        "colors": [("#0369A1", "header")],
    },
    # ── Section 3: Stock & Market ──
    {
        "id": "09", "section": 3, "title": "Stock Performance & Drop Investigation",
        "desc": "Price performance stats and the full stock drop investigation with catalysts.",
        "subs": [
            ("A", "Market Summary Cards (6)", "CARDS", "Price (drawdown badge) | 52W Range | Beta | Short Interest | Max Drawdown | Analyst Consensus"),
            ("B", "Stock Charts (1Y + 5Y)", "2 CHARTS", "Price vs sector & market overlay"),
            ("C", "Price Performance", "TABLE", "1M/3M/6M/YTD/1Y/3Y/5Y returns vs S&P 500"),
            ("D", "Stock Drop Investigation", "CHART+LEGEND", "2Y combo chart + numbered drops + catalyst legend table"),
        ],
        "sources": [("dsrc-yfinance", "yfinance: price history, beta, short interest, analyst consensus"), ("dsrc-web", "Web: drop catalyst investigation"), ("dsrc-computed", "Computed: drawdown, drop detection, DDL")],
        "colors": [("#EA580C", "header"), ("#1A1A2E", "chart bg"), ("#E8903A", "price line")],
    },
    {
        "id": "10", "section": 3, "title": "Insider Trading & Scienter Risk",
        "desc": "Full insider analysis with scienter risk assessment, cluster selling alerts, trading table.",
        "subs": [
            ("A", "Insider Trading Timeline", "TIMELINE", "Buys/sells near stock chart context"),
            ("B", "Scienter Risk Strip (4 cards)", "CARDS", "Net Posture (SELLER/BUYER/NEUTRAL) | 10b5-1 Coverage | Cluster Events | Timing/Exercise-Sell"),
            ("C", "Cluster Selling Alert", "ALERT", "Red-bordered, conditional on cluster detection"),
            ("D", "Pre-Event Trading Suspects", "ALERT", "Orange-bordered, conditional on event correlation"),
            ("E", "Insider Trading Table", "TABLE", "Date | Name | Role | Type | Shares | Value | % Holding | 10b5-1. Highlighted EX-SELL + C-Suite."),
        ],
        "sources": [("dsrc-yfinance", "yfinance: insider transactions, Form 4 data"), ("dsrc-computed", "Computed: scienter risk scoring, cluster detection, pre-event correlation")],
        "colors": [("#EA580C", "header"), ("#DC2626", "sell/cluster alerts"), ("#16A34A", "buy")],
    },
    {
        "id": "11", "section": 3, "title": "Technical Analysis Charts",
        "desc": "Drawdown, volatility/beta, relative performance, drop vs sector scatter — 1Y and 5Y each.",
        "subs": [
            ("A", "Drawdown Analysis (1Y + 5Y)", "2 CHARTS", "Peak-to-trough drawdown"),
            ("B", "Volatility & Beta (1Y + 5Y)", "2 CHARTS", "Rolling volatility and beta"),
            ("C", "Relative Performance (1Y + 5Y)", "2 CHARTS", "Indexed to 100 vs sector & market"),
            ("D", "Drop vs Sector Scatter (1Y + 5Y)", "2 CHARTS", "Company drops vs sector drops"),
            ("E", "Stock Performance", "TABLE", "Detailed performance stats"),
        ],
        "sources": [("dsrc-yfinance", "yfinance: price history, sector ETF data"), ("dsrc-computed", "Computed: drawdown, rolling vol/beta, relative return, drop correlation")],
        "colors": [("#EA580C", "header")],
    },
    {
        "id": "12", "section": 3, "title": "Earnings & Guidance",
        "desc": "Quarterly earnings table, beat/miss history, guidance track record, earnings reaction analysis.",
        "subs": [
            ("A", "Quarterly Earnings Table", "TABLE", "Quarter | Revenue | YoY% | Margins | EPS | Est EPS | Beat/Miss. Green/red rows."),
            ("B", "Earnings Beat/Miss History", "TABLE", "8-quarter beat/miss pattern"),
            ("C", "Earnings Guidance Track Record", "TABLE", "Management guidance vs actual results"),
            ("D", "Earnings Reaction Analysis", "TABLE", "Post-earnings stock moves"),
            ("E", "Earnings Miss Scenario", "NARRATIVE", "What happens if they miss? Investigative analysis."),
        ],
        "sources": [("dsrc-yfinance", "yfinance: quarterly earnings, EPS estimates"), ("dsrc-llm", "LLM: guidance extraction, earnings miss scenario"), ("dsrc-computed", "Computed: beat/miss patterns, reaction analysis")],
        "colors": [("#EA580C", "header"), ("#16A34A", "beat"), ("#DC2626", "miss")],
    },
    {
        "id": "13", "section": 3, "title": "Analyst Coverage & Estimates",
        "desc": "Forward estimates, revision trends, recent analyst actions.",
        "subs": [
            ("A", "Forward Estimates", "TABLE", "Consensus revenue/EPS estimates"),
            ("B", "Analyst Revision Trends", "TABLE", "Estimate revisions over time"),
            ("C", "Recent Analyst Actions", "TABLE", "Upgrades, downgrades, initiations"),
        ],
        "sources": [("dsrc-yfinance", "yfinance: analyst estimates, recommendations, revisions")],
        "colors": [("#EA580C", "header")],
    },
    {
        "id": "14", "section": 3, "title": "Capital Returns, Sentiment & 8-K Events",
        "desc": "Dividends/buybacks, NLP sentiment on 10-K, return correlations, 8-K event classification.",
        "subs": [
            ("A", "Capital Returns", "TABLE", "Dividends, buybacks, shareholder return policy"),
            ("B", "NLP & Sentiment Dashboard", "TABLE", "Loughran-McDonald sentiment on 10-K text. Tone shifts, readability."),
            ("C", "Return Correlation Analysis", "TABLE", "Correlation with sector, market, peers"),
            ("D", "8-K Event Classification", "TABLE", "All 8-K filings classified by type"),
        ],
        "sources": [("dsrc-yfinance", "yfinance: dividends, buybacks"), ("dsrc-sec", "SEC: 8-K filings"), ("dsrc-llm", "LLM: NLP sentiment analysis (Loughran-McDonald)"), ("dsrc-computed", "Computed: return correlation")],
        "colors": [("#EA580C", "header")],
    },
    # ── Section 4: Financial ──
    {
        "id": "15", "section": 4, "title": "Annual Financial Comparison",
        "desc": "FY vs FY-1 income statement, balance sheet, cash flow with YoY changes and direction arrows.",
        "subs": [
            ("A", "Annual Financial Comparison (FY vs FY-1)", "TABLE", "Revenue, GP, OpInc, EBITDA, NI with YoY changes + balance sheet + cash flow"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: income statement, balance sheet, cash flow (audited)")],
        "colors": [("#059669", "header")],
    },
    {
        "id": "16", "section": 4, "title": "Key Metrics & Quarterly Trends",
        "desc": "Financial metric cards, profitability/solvency/liquidity ratios, 8-quarter trends.",
        "subs": [
            ("A", "8 Metric Cards", "CARDS", "Revenue | EBITDA | Net Income | Op Cash Flow | FCF | Cash | Debt (red) | Current Ratio (orange)"),
            ("B", "Key Financial Metrics", "TABLE", "Profitability (Gross/Op/Net/EBITDA margin, ROE, ROA, ROIC) | Solvency | Liquidity"),
            ("C", "Quarterly Financial Trends (8Q)", "TABLE", "Revenue, margins, EPS with direction arrows"),
            ("D", "Quarterly Updates (2 Quarters)", "TABLE", "Recent quarter detail"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: financial statements"), ("dsrc-yfinance", "yfinance: quarterly data, margins"), ("dsrc-computed", "Computed: ratios, margins, growth rates")],
        "colors": [("#059669", "header")],
    },
    {
        "id": "17", "section": 4, "title": "Distress & Forensic Models",
        "desc": "Altman Z-Score, Beneish M-Score, Piotroski F-Score, Ohlson O-Score, earnings quality, bankruptcy risk.",
        "subs": [
            ("A", "Distress Model Indicators", "TABLE", "Altman Z (Safe/Grey/Distress) + Piotroski F (0-9) + Ohlson O (probability)"),
            ("B", "Forensic Analysis Dashboard", "TABLE", "Beneish M-Score: 8 components (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA)"),
            ("C", "Earnings Quality", "TABLE", "Accruals quality, cash conversion"),
            ("D", "Bankruptcy Risk Assessment", "TABLE", "Composite bankruptcy risk"),
            ("E", "Margin Profile + Forensic Scores (2-column)", "2-COL", "Left: margins. Right: all 4 distress scores with zone badges."),
        ],
        "sources": [("dsrc-xbrl", "XBRL: financial data for all model inputs"), ("dsrc-computed", "Computed: Altman Z, Beneish M, Piotroski F, Ohlson O formulas")],
        "colors": [("#059669", "header"), ("#16A34A", "safe zone"), ("#F59E0B", "grey zone"), ("#DC2626", "distress zone")],
    },
    {
        "id": "18", "section": 4, "title": "Audit & Tax Profile",
        "desc": "Auditor details, opinions, changes, tax jurisdiction, UTB, disclosure alerts.",
        "subs": [
            ("A", "Audit Profile", "KV", "Auditor name, tenure, opinions, changes (change = red flag)"),
            ("B", "Tax Risk Profile", "KV", "Effective rate, volatility, valuation allowances, uncertain tax positions"),
            ("C", "Audit Disclosure Alerts", "ALERT", "Red box with severity-colored bullets"),
            ("D", "Tax Jurisdiction Breakdown", "TABLE", "Federal/State/Foreign %"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: audit opinions, tax data, UTB"), ("dsrc-sec", "SEC: auditor changes, NT filings")],
        "colors": [("#059669", "header")],
    },
    {
        "id": "19", "section": 4, "title": "Debt, Liquidity & Balance Sheet Risk",
        "desc": "Debt structure and maturity, solvency ratios, goodwill, capital allocation, refinancing risk.",
        "subs": [
            ("A", "Debt Structure", "TABLE", "Instruments, maturity, rates"),
            ("B", "Debt Maturity Schedule", "CHART", "Bar chart: near-term red, future blue"),
            ("C", "Liquidity & Solvency", "TABLE", "Current/Quick/Cash ratios, debt service"),
            ("D", "Goodwill & Intangible Concentration", "TABLE", "GW amount, GW/Equity%, impairment risk"),
            ("E", "Capital Allocation", "TABLE", "CapEx, R&D, acquisitions, buybacks mix"),
            ("F", "Cash Flow Adequacy", "TABLE", "FCF coverage, burn rate if applicable"),
            ("G", "Refinancing Risk", "TABLE", "Near-term maturities, rate exposure"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: debt schedule, balance sheet, cash flow"), ("dsrc-llm", "LLM: debt structure extraction from 10-K"), ("dsrc-computed", "Computed: debt service coverage, refinancing risk")],
        "colors": [("#059669", "header"), ("#DC2626", "near-term debt")],
    },
    {
        "id": "20", "section": 4, "title": "Peer Benchmarking",
        "desc": "Peer group identification, comparison matrix, percentile rankings across key metrics.",
        "subs": [
            ("A", "Peer Group", "TABLE", "Identified peer companies by SIC/industry"),
            ("B", "Peer Comparison Matrix", "TABLE", "Company vs peers on revenue, margins, leverage, returns"),
            ("C", "Peer Benchmarking (SEC Filers)", "TABLE", "Percentile rankings from SEC data"),
        ],
        "sources": [("dsrc-yfinance", "yfinance: peer financial data"), ("dsrc-xbrl", "XBRL: peer SEC filings"), ("dsrc-computed", "Computed: percentile rankings, SIC matching")],
        "colors": [("#059669", "header")],
    },
    {
        "id": "21", "section": 4, "title": "MD&A & Filing Analysis",
        "desc": "Management discussion analysis, risk factor quantitative review, filing patterns, whistleblower.",
        "subs": [
            ("A", "MD&A Analysis", "NARRATIVE", "What management says about the business"),
            ("B", "Risk Factor Analysis", "TABLE", "Quantitative analysis of risk factor changes"),
            ("C", "Filing Patterns & Whistleblower", "TABLE", "SEC filing frequency, late filings, NT filings"),
        ],
        "sources": [("dsrc-sec", "SEC: 10-K MD&A, filing history"), ("dsrc-llm", "LLM: MD&A extraction and analysis")],
        "colors": [("#059669", "header")],
    },
    # ── Section 5: Governance ──
    {
        "id": "22", "section": 5, "title": "Board Composition & Skills",
        "desc": "Board member table, skills matrix, committee assignments, tenure distribution, 3 SVG visualizations.",
        "subs": [
            ("A", "Board Summary Cards (7)", "CARDS", "Board Size | Independence % | Avg Tenure | CEO/Chair Duality | Classified Board | Insider Own % | Institutional Own %"),
            ("B", "Board Composition", "TABLE", "Name | Title | Tenure | Independence | Committees"),
            ("C", "Board Skills Matrix", "TABLE", "Skills coverage: finance, legal, industry, tech, risk, ESG"),
            ("D", "Committee Membership", "TABLE", "Audit, Comp, Nom/Gov, Risk assignments"),
            ("E", "Board Tenure Distribution", "TABLE", "Service duration per director"),
            ("F", "3 Governance Visualizations (SVG)", "3 VISUALS", "Independence Donut | Tenure Bars | CEO Pay Ratio Gauge"),
        ],
        "sources": [("dsrc-sec", "SEC: proxy (DEF 14A), board members, committees"), ("dsrc-computed", "Computed: independence %, tenure distribution")],
        "colors": [("#D97706", "header")],
    },
    {
        "id": "23", "section": 5, "title": "Board Forensic Profiles",
        "desc": "Deep profile per director: prior lawsuits, character issues, experience/qualifications. NON-NEGOTIABLE.",
        "subs": [
            ("A", "Board Member Forensic Profiles", "TABLE", "Per director: background, red flags, qualifications"),
        ],
        "sources": [("dsrc-sec", "SEC: proxy biographical details"), ("dsrc-web", "Web: director background search, prior lawsuits"), ("dsrc-llm", "LLM: profile synthesis")],
        "colors": [("#D97706", "header")],
    },
    {
        "id": "24", "section": 5, "title": "Officer Investigation & People Risk",
        "desc": "CEO/CFO/key officer background investigation, people risk, executive risk profiles, turnover.",
        "subs": [
            ("A", "Officer Background Investigation", "TABLE", "Web-search-backed: prior companies, lawsuits, public incidents"),
            ("B", "People Risk", "TABLE", "Key person dependencies"),
            ("C", "Executive Risk Profiles", "TABLE", "Per-executive risk assessment"),
            ("D", "Tenure & Stability", "TABLE", "C-suite turnover, 8-K officer changes"),
        ],
        "sources": [("dsrc-web", "Web: officer name + litigation search"), ("dsrc-sec", "SEC: 8-K officer changes"), ("dsrc-llm", "LLM: officer profile synthesis")],
        "colors": [("#D97706", "header")],
    },
    {
        "id": "25", "section": 5, "title": "Compensation & Ownership",
        "desc": "Executive compensation, say-on-pay, ownership structure, insider trading detail, activist risk.",
        "subs": [
            ("A", "Compensation Analysis", "TABLE", "CEO comp, say-on-pay vote, pay ratio, equity/cash mix"),
            ("B", "Ownership Structure", "TABLE", "Insiders | Institutional | Mutual Funds distribution"),
            ("C", "Insider Trading Activity Detail", "TABLE", "Detailed transaction history"),
            ("D", "Activist Investor Risk", "TABLE", "Historical activist involvement, current holders, proposals"),
            ("E", "ISS QualityScore Risk Cards (5)", "CARDS", "Overall | Board | Compensation | Audit | Shareholder Rights"),
        ],
        "sources": [("dsrc-sec", "SEC: proxy compensation tables, say-on-pay"), ("dsrc-yfinance", "yfinance: insider transactions, institutional holders"), ("dsrc-web", "Web: activist investor research")],
        "colors": [("#D97706", "header")],
    },
    {
        "id": "26", "section": 5, "title": "Prior Litigation & Governance Structure",
        "desc": "Officers' litigation history, shareholder rights, transparency, structural governance.",
        "subs": [
            ("A", "Prior Litigation Exposure", "TABLE", "Lawsuits naming current officers/directors"),
            ("B", "Structural Governance", "TABLE", "Anti-takeover provisions, classified board"),
            ("C", "Shareholder Rights Inventory", "TABLE", "Poison pill, staggered board, supermajority requirements"),
            ("D", "Transparency & Disclosure", "TABLE", "Disclosure quality assessment"),
        ],
        "sources": [("dsrc-web", "Web: officer litigation history"), ("dsrc-sec", "SEC: proxy governance provisions"), ("dsrc-llm", "LLM: governance assessment")],
        "colors": [("#D97706", "header")],
    },
    # ── Section 6: Litigation ──
    {
        "id": "27", "section": 6, "title": "Active Litigation & Defense",
        "desc": "Securities class actions with full case detail cards, derivative suits, defense strength.",
        "subs": [
            ("A", "Header Badges", "BADGES", "Active count (red/green) | Historical count | Industry Sweep"),
            ("B", "Summary Cards (6)", "CARDS", "Total Cases | Active | Settled | Dismissed | Open SOL | Total Reserve"),
            ("C", "Case Status Circles", "VISUAL", "Active 🔴 | Appeal 🟠 | Settled 🟠 | Dismissed 🟢 | Other ⚪"),
            ("D", "Securities Class Action Cards", "CASE CARDS", "Per SCA: name + docket + settlement + status + metadata pills + legal theories + defendants + allegations + damages"),
            ("E", "Derivative Suits", "LIST", "Case name | Filing date | Status badge"),
            ("F", "Defense Strength Assessment", "TABLE", "Prior outcomes, counsel quality, coverage adequacy"),
        ],
        "sources": [("dsrc-supabase", "Supabase SCA DB: case details, allegations, settlements"), ("dsrc-sec", "SEC: 10-K Item 3"), ("dsrc-web", "Web: Stanford SCAC, CourtListener"), ("dsrc-llm", "LLM: legal theory classification")],
        "colors": [("#DC2626", "header/active"), ("#F59E0B", "settled"), ("#16A34A", "dismissed")],
    },
    {
        "id": "28", "section": 6, "title": "Exposure Windows & SOL",
        "desc": "Statute of limitations windows, theoretical future exposure, Section 11/10b-5 timelines.",
        "subs": [
            ("A", "Statute of Limitations — Active Windows", "TABLE", "Open liability windows per offering/event"),
            ("B", "Theoretical Exposure Windows", "TABLE", "Potential future claims from current risk signals"),
        ],
        "sources": [("dsrc-computed", "Computed: SOL calculations, exposure window analysis"), ("dsrc-sec", "SEC: offering dates, filing dates")],
        "colors": [("#DC2626", "header")],
    },
    {
        "id": "29", "section": 6, "title": "SEC & Regulatory Enforcement",
        "desc": "SEC investigations, enforcement actions, regulatory proceedings from other agencies.",
        "subs": [
            ("A", "SEC Enforcement Pipeline", "TABLE", "Investigations, actions, settlements"),
            ("B", "Regulatory Proceedings", "TABLE", "Non-SEC: EPA, DOJ, FTC, state AGs"),
        ],
        "sources": [("dsrc-sec", "SEC: litigation releases, AAERs"), ("dsrc-web", "Web: regulatory action search")],
        "colors": [("#DC2626", "header")],
    },
    {
        "id": "30", "section": 6, "title": "Historical Litigation & Timeline",
        "desc": "Settlement history, M&A litigation, visual timeline, contingent liabilities.",
        "subs": [
            ("A", "Deal / M&A Litigation", "TABLE", "Appraisal rights, breach of fiduciary duty"),
            ("B", "Litigation Timeline", "CHART", "Visual timeline, color-coded by type/status"),
            ("C", "Contingent Liabilities (ASC 450)", "KV", "Disclosed contingent liabilities from financials"),
        ],
        "sources": [("dsrc-sec", "SEC: 10-K legal disclosures"), ("dsrc-xbrl", "XBRL: contingent liabilities"), ("dsrc-web", "Web: settlement records")],
        "colors": [("#DC2626", "header")],
    },
    {
        "id": "31", "section": 6, "title": "Other Matters & Whistleblower",
        "desc": "Whistleblower indicators, workforce/product/environmental litigation.",
        "subs": [
            ("A", "Whistleblower Indicators", "TABLE", "SEC complaints, internal reports"),
            ("B", "Workforce, Product & Environmental", "TABLE", "Employment, product liability, environmental claims"),
        ],
        "sources": [("dsrc-sec", "SEC: whistleblower filings"), ("dsrc-llm", "LLM: extraction from 10-K disclosures"), ("dsrc-web", "Web: employment/product/env litigation search")],
        "colors": [("#DC2626", "header")],
    },
    # ── Section 7: Industry ──
    {
        "id": "32", "section": 7, "title": "Competitive & Strategic Position",
        "desc": "Market position, competitive advantages, strategic assessment, regulatory environment.",
        "subs": [
            ("A", "Competitive Position", "NARRATIVE", "Market share, advantages, threat assessment"),
            ("B", "Strategic Assessment", "NARRATIVE", "Growth trajectory, industry trends"),
            ("C", "Sector Claim Profile Cards (3)", "CARDS", "SCA Filing Rate | MTD Dismissal Rate | Median Settlement"),
            ("D", "Industry D&O Tier Distribution", "CHART", "Stacked bar: PREFERRED/STANDARD/ELEVATED/HIGH_RISK/PROHIBITED %"),
        ],
        "sources": [("dsrc-computed", "Computed: sector claim statistics, tier distribution"), ("dsrc-llm", "LLM: competitive/strategic analysis"), ("dsrc-supabase", "Supabase: sector SCA data")],
        "colors": [("#7C3AED", "header")],
    },
    {
        "id": "33", "section": 7, "title": "AI Risk & Biotech Module",
        "desc": "AI exposure assessment (all companies) + biotech four-pillar framework (conditional).",
        "subs": [
            ("A", "AI Risk Dimension Breakdown", "TABLE", "AI Exposure | Governance | Liability | Competitive | Regulatory"),
            ("B", "Biotech Module (conditional)", "NARRATIVE", "Four-pillar: Pipeline Risk, Regulatory Risk, IP/Patent Risk, Capital Risk"),
        ],
        "sources": [("dsrc-llm", "LLM: AI risk assessment, biotech analysis"), ("dsrc-sec", "SEC: 10-K technology/pipeline disclosures")],
        "colors": [("#7C3AED", "header")],
    },
    # ── Section 8: Scoring ──
    {
        "id": "34", "section": 8, "title": "Tier & Factor Scoring",
        "desc": "Quality score, tier classification, 10-factor scoring table with SVG progress bars, per-factor detail.",
        "subs": [
            ("A", "Tier Classification", "VERDICT", "Quality Score /100 + Composite Score + Tier badge (WIN/PREFERRED/WRITE/WATCH/WALK/NO_TOUCH)"),
            ("B", "Factor Score Table", "TABLE", "Factor | Name | Points (X/Y) | SVG bar | Signals (X/Y) | Evidence. Total row → Tier."),
            ("C", "Per-Factor Detail", "TABLE", "Drill-down: which signals drove each score"),
            ("D", "Critical Risk Flags", "ALERT", "Red box. Per flag: name + max tier ceiling badge + evidence. Single flag can cap tier."),
            ("E", "Radar Chart", "CHART", "10-factor risk profile visualization"),
        ],
        "sources": [("dsrc-computed", "Computed: 10-factor scoring engine, quality score, tier classification, signal aggregation")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "35", "section": 8, "title": "Loss Analysis & Scenarios",
        "desc": "Claim probability, severity scenarios (10th/50th/90th percentile), tower position recommendation.",
        "subs": [
            ("A", "Claim Probability", "TABLE", "Annual frequency estimate, marginal probability decomposition (waterfall/tornado)"),
            ("B", "Severity Scenarios", "TABLE", "10th/50th/90th percentile settlement range"),
            ("C", "Tower Position Recommendation", "KV", "Primary/excess/umbrella. Retention guidance. Capacity guidance."),
        ],
        "sources": [("dsrc-computed", "Computed: actuarial models, severity calibration, tower positioning")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "36", "section": 8, "title": "Peril Assessment & Mapping",
        "desc": "D&O claim perils, peril map, allegation theory mapping — which theories of liability are active.",
        "subs": [
            ("A", "D&O Claim Peril Assessment", "TABLE", "Per peril: risk level, active chains, evidence, severity range"),
            ("B", "Peril Map", "TABLE", "Perils mapped to company-specific exposure"),
            ("C", "Allegation Theory Mapping", "TABLE", "Litigation allegations mapped to D&O perils"),
        ],
        "sources": [("dsrc-computed", "Computed: peril scoring from signals + litigation data")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "37", "section": 8, "title": "Investigative Depth",
        "desc": "Hazard profile (47 dimensions), forensic composites, temporal signals, pattern detection, executive risk.",
        "subs": [
            ("A", "Hazard Profile (Inherent Exposure Score)", "TABLE", "47-dimension IES across H1-H7"),
            ("B", "Forensic Composite Scores", "TABLE", "Altman + Beneish + Piotroski + Ohlson in scoring context"),
            ("C", "Temporal Signals", "TABLE", "12M lookback trends, acceleration/deceleration"),
            ("D", "Composite Pattern Detection", "TABLE", "Recurring risk patterns, frequency, severity"),
            ("E", "Executive Risk Profile", "TABLE", "Per-executive risk in scoring context"),
        ],
        "sources": [("dsrc-computed", "Computed: hazard engine (7 dimensions), temporal analysis, pattern engine, forensic composites")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "38", "section": 8, "title": "Underwriting Posture & Calibration",
        "desc": "Recommended action, watch items, calibration notes, zero-score verification.",
        "subs": [
            ("A", "Suggested Underwriting Posture", "NARRATIVE", "Recommended action with rationale"),
            ("B", "Calibration Notes", "NARRATIVE", "Context-specific scoring adjustments and limitations"),
            ("C", "ZER-001 Verifications", "TABLE", "Factors at zero — verified justified, not missing data"),
            ("D", "Dual-Voice Commentary", "NARRATIVE", "'What Was Said' + 'Underwriting Commentary'"),
        ],
        "sources": [("dsrc-computed", "Computed: posture recommendation logic"), ("dsrc-llm", "LLM: commentary, calibration notes")],
        "colors": [("#0891B2", "header")],
    },
    # ── Section 8 continued: Individual Scoring Frameworks ──
    {
        "id": "39", "section": 8, "title": "Altman Z-Score & Distress Models",
        "desc": "Altman Z-Score (original + Z'' variant), Ohlson O-Score bankruptcy probability. Zone-based classification.",
        "subs": [
            ("A", "Altman Z-Score (Original)", "TABLE", "5 components: Working Capital/TA, Retained Earnings/TA, EBIT/TA, Market Cap/TL, Sales/TA. Zones: DISTRESS <1.81 | GREY 1.81-2.99 | SAFE >2.99"),
            ("B", "Altman Z'' Double-Prime", "TABLE", "Adjusted for private/non-manufacturing. Zones: DISTRESS <1.1 | GREY 1.1-2.6 | SAFE >2.6"),
            ("C", "Ohlson O-Score", "TABLE", "9-variable logit bankruptcy probability. Zones: DISTRESS >0.5 | GREY 0.25-0.5 | SAFE <0.25"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: all financial statement inputs"), ("dsrc-computed", "Computed: distress model formulas")],
        "colors": [("#0891B2", "header"), ("#16A34A", "safe"), ("#F59E0B", "grey"), ("#DC2626", "distress")],
    },
    {
        "id": "40", "section": 8, "title": "Beneish M-Score (Earnings Manipulation)",
        "desc": "8-component earnings manipulation detection. M > -1.78 = manipulation likely.",
        "subs": [
            ("A", "DSRI (Days Sales in Receivables Index)", "KV", "Rising receivables relative to sales"),
            ("B", "GMI (Gross Margin Index)", "KV", "Declining gross margins"),
            ("C", "AQI (Asset Quality Index)", "KV", "Increasing intangibles/soft assets"),
            ("D", "SGI (Sales Growth Index)", "KV", "High growth companies more likely to manipulate"),
            ("E", "DEPI (Depreciation Index)", "KV", "Slowing depreciation to boost earnings"),
            ("F", "SGAI (SG&A Index)", "KV", "Rising SG&A costs"),
            ("G", "LVGI (Leverage Index)", "KV", "Increasing leverage"),
            ("H", "TATA (Total Accruals to Total Assets)", "KV", "High accruals = potential manipulation"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: all income statement and balance sheet inputs"), ("dsrc-computed", "Computed: 8-component Beneish formula")],
        "colors": [("#0891B2", "header"), ("#DC2626", "manipulation likely"), ("#16A34A", "unlikely")],
    },
    {
        "id": "41", "section": 8, "title": "Piotroski F-Score (Financial Health)",
        "desc": "9-point binary scoring for financial health. 0-3 = weak, 4-7 = average, 8-9 = strong.",
        "subs": [
            ("A", "Profitability Signals (4)", "TABLE", "Positive ROA, Positive CFO, Improving ROA, CFO > NI (accruals quality)"),
            ("B", "Leverage/Liquidity Signals (3)", "TABLE", "Declining leverage, Improving current ratio, No equity dilution"),
            ("C", "Efficiency Signals (2)", "TABLE", "Improving gross margin, Improving asset turnover"),
        ],
        "sources": [("dsrc-xbrl", "XBRL: financial statements for all 9 criteria"), ("dsrc-computed", "Computed: binary scoring per criterion")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "42", "section": 8, "title": "Hazard Profile (7 Dimensions, 47 Sub-dimensions)",
        "desc": "Inherent Exposure Score — pre-behavioral risk layer. H1-H7 with interdependence effects.",
        "subs": [
            ("A", "H1-Business", "TABLE", "Business model, competitive position, strategy execution"),
            ("B", "H2-People", "TABLE", "Board quality, management, key person dependencies"),
            ("C", "H3-Financial", "TABLE", "Earnings quality, leverage, liquidity stress"),
            ("D", "H4-Governance", "TABLE", "Board independence, oversight, shareholder rights"),
            ("E", "H5-Maturity", "TABLE", "Company lifecycle stage, operational sophistication"),
            ("F", "H6-Environment", "TABLE", "Macro, supply chain, regulatory exposure"),
            ("G", "H7-Emerging", "TABLE", "AI, digital transformation, novel risks"),
            ("H", "Interaction Effects", "TABLE", "Cross-dimension amplification/dampening"),
        ],
        "sources": [("dsrc-computed", "Computed: hazard engine across 47 sub-dimensions with normalized inputs")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "43", "section": 8, "title": "AI Risk Scoring (5 Sub-dimensions)",
        "desc": "Industry-weighted AI risk assessment. Revenue displacement, workforce, cost, moat, regulatory.",
        "subs": [
            ("A", "Revenue Displacement Risk", "KV", "How much revenue is at risk from AI disruption"),
            ("B", "Workforce Automation Risk", "KV", "Exposure to labor automation"),
            ("C", "Cost Structure Vulnerability", "KV", "AI-driven cost compression in industry"),
            ("D", "Competitive Moat Erosion", "KV", "AI reducing barriers to entry"),
            ("E", "Regulatory/IP Challenge Risk", "KV", "AI regulation and IP exposure"),
        ],
        "sources": [("dsrc-llm", "LLM: AI risk assessment per dimension"), ("dsrc-computed", "Computed: industry-weighted composite from ai_risk_weights.json")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "44", "section": 8, "title": "Frequency & Severity Modeling",
        "desc": "Actuarial claim frequency by plaintiff type, severity percentiles, settlement regression, bear case.",
        "subs": [
            ("A", "Frequency Model", "TABLE", "Annual claim rates by plaintiff type and peril"),
            ("B", "Severity Percentiles", "TABLE", "25th/50th/75th/95th percentile estimated settlement"),
            ("C", "Settlement Regression (DDL-based)", "TABLE", "Dollar-day-loss driven severity prediction"),
            ("D", "Bear Case Builder", "NARRATIVE", "Adversarial worst-case scenario narrative"),
            ("E", "Precedent Match", "TABLE", "Historical case similarity scoring"),
            ("F", "Peer Outlier Detection", "TABLE", "Statistical positioning vs comparable companies"),
        ],
        "sources": [("dsrc-computed", "Computed: actuarial models, DDL regression, precedent matching"), ("dsrc-supabase", "Supabase: historical settlement data")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "45", "section": 8, "title": "7-Lens Peril Mapping",
        "desc": "D&O claim perils assessed from 7 plaintiff perspectives. Probability × severity per lens.",
        "subs": [
            ("A", "Shareholders Lens", "TABLE", "Securities fraud, proxy, derivative exposure"),
            ("B", "Regulators Lens", "TABLE", "SEC, DOJ, state AG exposure"),
            ("C", "Employees Lens", "TABLE", "EPL, ERISA, whistleblower exposure"),
            ("D", "Customers/Suppliers Lens", "TABLE", "Antitrust, contract, product exposure"),
            ("E", "Business Partners Lens", "TABLE", "JV, M&A, IP exposure"),
            ("F", "Investors Lens", "TABLE", "Offering liability, prospectus claims"),
            ("G", "General Public Lens", "TABLE", "Environmental, safety, privacy exposure"),
        ],
        "sources": [("dsrc-computed", "Computed: peril mapping engine from signals + litigation data")],
        "colors": [("#0891B2", "header")],
    },
    {
        "id": "46", "section": 8, "title": "Pattern Detection & Red Flag Gates",
        "desc": "Multi-signal conjunction scanning, red flag trigger logic, adversarial critique.",
        "subs": [
            ("A", "Pattern Detection", "TABLE", "Recurring risk patterns across signals, frequency/severity"),
            ("B", "Red Flag Gates", "ALERT", "Trigger thresholds that cap tier regardless of score"),
            ("C", "Conjunction Scanning", "TABLE", "Multi-factor red flags (when A+B+C fire together)"),
            ("D", "Adversarial Critique", "NARRATIVE", "Devil's advocate challenge to scoring conclusions"),
        ],
        "sources": [("dsrc-computed", "Computed: pattern engine, red flag gates, conjunction logic"), ("dsrc-llm", "LLM: adversarial critique generation")],
        "colors": [("#0891B2", "header"), ("#DC2626", "red flag triggers")],
    },
    # ── Section 9: UW Framework ──
    {
        "id": "47", "section": 9, "title": "Underwriting Decision Questions",
        "desc": "Question-driven underwriting. System asks experienced-underwriter questions, answers from data.",
        "subs": [
            ("A", "Domain Question Groups", "Q&A", "Per domain (Financial, Governance, Litigation, Market, Operations): verdict badge + answered count + completeness bar"),
            ("B", "Per-Question Detail", "Q&A", "Verdict circle (+/-/=/?) + question + SCA source badge + answer paragraph + evidence"),
        ],
        "sources": [("dsrc-computed", "Computed: question generation from scoring + analysis"), ("dsrc-llm", "LLM: answer synthesis from state data")],
        "colors": [("#4338CA", "header"), ("#16A34A", "upgrade"), ("#DC2626", "downgrade"), ("#6B7280", "neutral")],
    },
    # ── Section 10: Meeting Prep ──
    {
        "id": "48", "section": 10, "title": "Meeting Preparation Questions",
        "desc": "What to ask the CFO/broker. Prioritized by HIGH/MEDIUM/LOW, tagged by topic.",
        "subs": [
            ("A", "Prioritized Questions", "LIST", "Color-coded number (dark blue HIGH, indigo MEDIUM, grey LOW) + priority badge + topic badge + question text"),
        ],
        "sources": [("dsrc-computed", "Computed: question generation from data gaps + risk signals"), ("dsrc-llm", "LLM: question formulation")],
        "colors": [("#BE185D", "header"), ("#1E3A8A", "HIGH"), ("#4338CA", "MEDIUM"), ("#6B7280", "LOW")],
    },
    # ── Section 11: Audit Trail ──
    {
        "id": "49", "section": 11, "title": "Signal Disposition Audit",
        "desc": "Per-signal results across 14 categories: Biz, Fin, Sect, Disc, Envr, Exec, Fwrd, Gov, Lit, Nlp, Stock, Abs, Conj, Ctx.",
        "subs": [
            ("A", "QA / Audit Trail", "TABLE", "Per-section signal counts, coverage %, triggered vs executed"),
            ("B", "14 Category Breakdowns", "TABLES", "Signal Name | Category | Confidence | Evidence | Disposition"),
        ],
        "sources": [("dsrc-computed", "Computed: signal evaluation engine results")],
        "colors": [("#64748B", "header")],
    },
    {
        "id": "50", "section": 11, "title": "Data Coverage & Gaps",
        "desc": "Per-section data coverage, missing data, blind spot discovery results.",
        "subs": [
            ("A", "Market Data — Full Detail", "TABLE", "Raw market data dump for reference"),
            ("B", "Per-Section Coverage", "TABLE", "% of expected data present per section"),
            ("C", "Data Gaps", "TABLE", "What's missing and why"),
            ("D", "Blind Spot Discovery", "TABLE", "What web search found that structured sources missed"),
        ],
        "sources": [("dsrc-computed", "Computed: pipeline status, coverage metrics"), ("dsrc-web", "Web: blind spot discovery searches")],
        "colors": [("#64748B", "header")],
    },
    {
        "id": "51", "section": 11, "title": "Decision Record & Provenance",
        "desc": "Final decision record, epistemological trace, sources, render audit.",
        "subs": [
            ("A", "Underwriting Decision Record", "KV", "Final tier + posture + industry D&O tier distribution reference"),
            ("B", "Sources & Provenance", "TABLE", "Filing URLs, data source references"),
            ("C", "Epistemological Trace", "TABLE", "Every signal traced to data source, filing, confidence"),
            ("D", "Pipeline Execution Status", "TABLE", "Stage timing, pass/fail"),
            ("E", "Render Audit", "TABLE", "Template rendering diagnostics"),
        ],
        "sources": [("dsrc-computed", "Computed: pipeline telemetry, provenance tracking")],
        "colors": [("#64748B", "header")],
    },
]


def build_html():
    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>D&O Worksheet — Card Catalog v4</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#F8FAFC;color:#1E293B}
.hero{text-align:center;padding:48px 24px 32px;background:white;border-bottom:1px solid #E2E8F0}
.hero h1{font-size:28px;font-weight:900;color:#0F172A;letter-spacing:-0.5px}
.hero .sub{font-size:13px;color:#64748B;margin-top:6px;max-width:700px;margin-inline:auto;line-height:1.5}
.hero .stats{display:flex;justify-content:center;gap:32px;margin-top:20px}
.stat{text-align:center}
.stat-num{font-size:32px;font-weight:900;color:#0F172A}
.stat-label{font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;font-weight:600}
.nav{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.97);backdrop-filter:blur(12px);border-bottom:1px solid #E2E8F0;padding:10px 16px;display:flex;flex-wrap:wrap;justify-content:center;gap:6px}
.nav a{font-size:11px;font-weight:600;padding:5px 12px;border-radius:6px;text-decoration:none;color:white;transition:opacity .15s}
.nav a:hover{opacity:.85}
.section{max-width:1100px;margin:0 auto;padding:40px 24px 16px}
.sec-hdr{display:flex;align-items:center;gap:14px;margin-bottom:6px}
.sec-num{font-size:42px;font-weight:900;line-height:1}
.sec-title{font-size:20px;font-weight:800}
.sec-desc{font-size:12px;color:#64748B;margin-bottom:20px;line-height:1.5;max-width:800px}

/* Card */
.card{background:white;border:2px solid #CBD5E1;border-radius:12px;margin-bottom:16px;overflow:hidden}
.card-hdr{padding:12px 16px;display:flex;align-items:center;gap:12px}
.card-num{font-size:22px;font-weight:900;color:rgba(255,255,255,0.35);font-family:'JetBrains Mono',monospace;width:36px;text-align:center}
.card-icon{width:32px;height:32px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0;color:white}
.card-title{font-size:14px;font-weight:800;color:white;flex:1}
.card-desc{font-size:10.5px;color:#64748B;padding:0 16px 10px;line-height:1.5;border-bottom:1px solid #F1F5F9}

/* Data Sources */
.dsrc-panel{padding:8px 16px;background:#FAFBFC;border-bottom:1px solid #F1F5F9}
.dsrc-title{font-size:7.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#94A3B8;margin-bottom:4px}
.dsrc-grid{display:flex;flex-wrap:wrap;gap:3px}
.dsrc{display:inline-flex;align-items:center;gap:3px;font-size:8px;padding:2px 7px;border-radius:3px;font-weight:600}
.dsrc-dot{width:5px;height:5px;border-radius:3px;flex-shrink:0}
.dsrc-xbrl{background:#DCFCE7;color:#166534}
.dsrc-yfinance{background:#FEF3C7;color:#92400E}
.dsrc-llm{background:#F3E8FF;color:#7C3AED}
.dsrc-web{background:#DBEAFE;color:#1D4ED8}
.dsrc-computed{background:#F1F5F9;color:#475569}
.dsrc-sec{background:#FFE4E6;color:#9F1239}
.dsrc-supabase{background:#E0F2FE;color:#075985}

/* Colors */
.colors{display:flex;flex-wrap:wrap;gap:5px;padding:6px 16px;border-bottom:1px solid #F1F5F9}
.swatch{display:inline-flex;align-items:center;gap:3px;font-size:7.5px;font-family:'JetBrains Mono',monospace;color:#64748B}
.swatch span{width:12px;height:12px;border-radius:2px;border:1px solid rgba(0,0,0,.1);display:inline-block}

/* Sub-element */
.sub{border-bottom:1px solid #F1F5F9}
.sub:last-child{border-bottom:none}
.sub-head{padding:8px 16px;display:flex;align-items:center;gap:8px;cursor:pointer}
.sub-head:hover{background:#FAFBFC}
.sub-letter{width:20px;height:20px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;flex-shrink:0;color:white}
.sub-name{font-size:11px;font-weight:700;flex:1;color:#1E293B}
.sub-type{font-size:7.5px;font-weight:700;padding:2px 6px;border-radius:3px;text-transform:uppercase;letter-spacing:.3px;background:#F1F5F9;color:#475569}
.sub-arrow{font-size:9px;color:#94A3B8;transition:transform .15s}
.sub[open]>.sub-head .sub-arrow{transform:rotate(90deg)}
.sub-body{padding:4px 16px 8px 44px;font-size:10px;color:#64748B;line-height:1.5}

.type-CHART,.type-2.CHARTS,.type-CHART\\+LEGEND{background:#DBEAFE;color:#1D4ED8}
.type-TABLE,.type-TABLES,.type-2-COL,.type-LIST,.type-CASE.CARDS{background:#FEF3C7;color:#92400E}
.type-NARRATIVE,.type-NARRATIVES{background:#F3E8FF;color:#7C3AED}
.type-CARDS,.type-2.CARDS,.type-3.CARDS,.type-4.CARDS,.type-5.CARDS,.type-6.CARDS,.type-7.CARDS{background:#DCFCE7;color:#166534}
.type-ALERT,.type-VERDICT,.type-BADGES{background:#FEF2F2;color:#991B1B}
.type-VISUAL,.type-3.VISUALS{background:#EDE9FE;color:#6D28D9}
.type-KV{background:#E0F2FE;color:#075985}
.type-TIMELINE{background:#FFF7ED;color:#9A3412}
.type-Q\\&A{background:#F0F9FF;color:#0C4A6E}

.footer{text-align:center;padding:40px 24px;color:#94A3B8;font-size:11px;border-top:1px solid #E2E8F0;margin-top:40px;background:white}
@media print{.nav{display:none}.card{break-inside:avoid}}
</style></head><body>
<div class="hero">
<h1>D&O Worksheet Card Catalog</h1>
<div class="sub">Every card in the worksheet with its sub-elements, data sources, and colors. Click sub-elements to expand. 46 cards across 12 sections.</div>
<div class="stats">
<div class="stat"><div class="stat-num">12</div><div class="stat-label">Sections</div></div>
<div class="stat"><div class="stat-num">""" + str(len(CARDS)) + """</div><div class="stat-label">Cards</div></div>
<div class="stat"><div class="stat-num">173</div><div class="stat-label">Tables</div></div>
<div class="stat"><div class="stat-num">53</div><div class="stat-label">Charts</div></div>
</div></div>
""")

    # Nav
    parts.append('<div class="nav">')
    for sid, num, name, color, _ in SECTIONS:
        parts.append(f'<a href="#{sid}" style="background:{color}">{num} {name}</a>')
    parts.append('</div>')

    # Render sections and cards
    current_section = -1
    for card in CARDS:
        sec_idx = card["section"]
        if sec_idx != current_section:
            if current_section >= 0:
                parts.append('</div>')  # close prev section
            sid, num, name, color, css = SECTIONS[sec_idx]
            parts.append(f'<div class="section" id="{sid}">')
            parts.append(f'<div class="sec-hdr"><div class="sec-num" style="color:{color}">{num}</div><div class="sec-title">{name}</div></div>')
            current_section = sec_idx

        sec_color = SECTIONS[sec_idx][3]
        sec_css = SECTIONS[sec_idx][4]

        # Card
        parts.append(f'<div class="card" style="border-color:{sec_color}40">')
        parts.append(f'<div class="card-hdr" style="background:{sec_color}">')
        parts.append(f'<div class="card-num">{card["id"]}</div>')
        parts.append(f'<div class="card-icon" style="background:rgba(255,255,255,0.15)">{card["id"]}</div>')
        parts.append(f'<div class="card-title">{card["title"]}</div>')
        parts.append('</div>')

        # Description
        parts.append(f'<div class="card-desc">{card["desc"]}</div>')

        # Data Sources
        parts.append('<div class="dsrc-panel"><div class="dsrc-title">Data Sources</div><div class="dsrc-grid">')
        dsrc_dots = {"dsrc-xbrl": "#16A34A", "dsrc-yfinance": "#D97706", "dsrc-llm": "#7C3AED", "dsrc-web": "#1D4ED8", "dsrc-computed": "#64748B", "dsrc-sec": "#E11D48", "dsrc-supabase": "#0284C7"}
        for cls, label in card["sources"]:
            dot = dsrc_dots.get(cls, "#64748B")
            parts.append(f'<div class="dsrc {cls}"><div class="dsrc-dot" style="background:{dot}"></div>{label}</div>')
        parts.append('</div></div>')

        # Colors
        if card["colors"]:
            parts.append('<div class="colors">')
            for hex_c, label in card["colors"]:
                parts.append(f'<div class="swatch"><span style="background:{hex_c}"></span>{hex_c} {label}</div>')
            parts.append('</div>')

        # Sub-elements
        for letter, name, typ, note in card["subs"]:
            parts.append(f'<details class="sub">')
            parts.append(f'<summary class="sub-head">')
            parts.append(f'<div class="sub-letter" style="background:{sec_color}">{letter}</div>')
            parts.append(f'<div class="sub-name">{name}</div>')
            parts.append(f'<div class="sub-type">{typ}</div>')
            parts.append(f'<div class="sub-arrow">▸</div>')
            parts.append(f'</summary>')
            parts.append(f'<div class="sub-body">{note}</div>')
            parts.append(f'</details>')

        parts.append('</div>')  # close card

    parts.append('</div>')  # close last section

    parts.append(f"""
<div class="footer">
<p><strong>D&O Worksheet Card Catalog v4</strong> — 2026-03-29 · Built from actual template code</p>
<p>{len(CARDS)} cards · 12 sections · Click sub-elements to expand details</p>
</div></body></html>""")

    return '\n'.join(parts)


if __name__ == "__main__":
    html = build_html()
    with open("output/CARD_CATALOG_v4.html", "w") as f:
        f.write(html)
    print(f"Generated {len(CARDS)} cards")
