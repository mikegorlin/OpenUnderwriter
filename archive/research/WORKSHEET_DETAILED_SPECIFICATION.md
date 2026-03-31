# D&O Underwriting Worksheet: Detailed Data Point Specification

**Version:** 1.0
**Date:** February 6, 2026
**Purpose:** Define every data point, analysis, and data source for each section of the D&O underwriting worksheet at the implementation level. Each data point specifies what is measured, where the data comes from, peer-relative methodology, signal interpretation (red/neutral/positive), and the forward-looking component.

**Design Principle:** Forward-looking elements are distributed INTO each section. Each section tells its complete story -- past, present, and what is coming. There is no siloed "Forward Look" section.

---

# SECTION 1: EXECUTIVE SUMMARY

This section is a synthesis layer. It consumes outputs from Sections 2-6 and produces the underwriter's decision framework. No primary data is gathered here -- everything is derived.

---

## 1.1 Verdict & Tier Classification

| Attribute | Detail |
|-----------|--------|
| **What is measured** | Overall risk tier assignment: WIN / WANT / WRITE / WATCH / WALK / NO TOUCH |
| **How it is derived** | Composite quality score (Section 7) mapped to tier: WIN (90-100), WANT (75-89), WRITE (60-74), WATCH (40-59), WALK (20-39), NO TOUCH (0-19 or any Critical Red Flag ceiling triggered) |
| **Data source** | Derived from Section 7 scoring output |
| **Peer-relative** | Yes -- tier is contextualized against the distribution of scores for companies in the same market cap band and industry |
| **Red flag** | WALK or NO TOUCH tier |
| **Neutral** | WRITE or WATCH tier |
| **Positive** | WIN or WANT tier |
| **Forward-looking** | Tier includes a directional indicator: STABLE / IMPROVING / DETERIORATING based on trailing 12-month trend in underlying factors |

---

## 1.2 Key Concerns (Top 5)

| Attribute | Detail |
|-----------|--------|
| **What is measured** | The 5 highest-impact risk factors from across all sections, ranked by severity |
| **How it is derived** | Each concern includes: (a) category label (e.g., "Active Securities Litigation"), (b) 2-4 sentence evidence narrative with specific numbers, dates, and filing citations, (c) the section and check ID it originates from, (d) scoring impact (how many risk points it contributes), (e) allegation theory mapping (which of the 5 complaint theories it enables: A=Disclosure, B=Guidance, C=Product/Ops, D=Governance, E=M&A) |
| **Data source** | Derived from flagged items across Sections 2-6 |
| **Peer-relative** | Each concern notes whether the issue is unique to this company or common in its peer group |
| **Signal interpretation** | All items here are negative signals by definition; severity is graded as CRITICAL / HIGH / MODERATE |

---

## 1.3 Key Positives (Top 5)

| Attribute | Detail |
|-----------|--------|
| **What is measured** | The 5 strongest mitigating factors, ranked by underwriting comfort |
| **How it is derived** | Same structure as concerns: category, evidence narrative, section origin, scoring credit, and defense theory mapping (what makes this company harder to sue or more likely to win dismissal) |
| **Data source** | Derived from positive findings across Sections 2-6 |
| **Peer-relative** | Each positive notes how the company compares to peers on this dimension |

---

## 1.4 Inherent Risk Baseline

| Attribute | Detail |
|-----------|--------|
| **What is measured** | Expected annual securities class action filing probability and expected settlement severity range, based purely on objective company characteristics BEFORE examining behavior |
| **How it is derived** | Lookup in the Industry x Market Cap matrix (see INHERENT_RISK_BASELINE_RESEARCH.md, Part 3, Section 3). Inputs: market cap tier, industry sector, years public, IPO/SPAC status, FPI status, index membership. Output: frequency band (e.g., "6-10% annual filing probability, Elevated tier") and severity range (e.g., "Median $35-100M if sued") |
| **Data source** | Market cap: SEC EDGAR XBRL `us-gaap:CommonStockSharesOutstanding` x current stock price (Yahoo Finance API or equivalent). Industry: SEC EDGAR SIC code from company filings header. Years public: SEC EDGAR first filing date. Index membership: S&P 500 / Russell 2000 constituent lists (free, updated quarterly) |
| **Peer-relative** | The baseline IS the peer-relative anchor -- it represents the expected risk for a company with these characteristics |
| **Red flag** | Inherent risk in "High" (10-15%) or "Very High" (>15%) frequency band |
| **Neutral** | "Moderate" (3.5-6%) or "Elevated" (6-10%) |
| **Positive** | "Low" (<3.5%) or "Very Low" (<1.5%) |
| **Forward-looking** | Note any pending changes that would shift the baseline: imminent IPO anniversary (exiting elevated window), pending index inclusion/exclusion, market cap migration across tier boundaries |

---

## 1.5 D&O Risk Type Classification

| Attribute | Detail |
|-----------|--------|
| **What is measured** | Primary archetype assignment from 7 categories: BINARY_EVENT, GROWTH_DARLING, GUIDANCE_DEPENDENT, REGULATORY_SENSITIVE, TRANSFORMATION, STABLE_MATURE, DISTRESSED. Plus optional secondary overlay |
| **How it is derived** | Rule-based classification using: revenue growth rate (>25% = Growth Darling candidate), guidance philosophy (specific numerical = Guidance Dependent candidate), pending FDA/regulatory decisions (Binary Event), active M&A/restructuring (Transformation), Altman Z-Score <1.81 (Distressed), beta <0.8 with >10yr public (Stable Mature), regulatory action count (Regulatory Sensitive). Each archetype has defined entry criteria |
| **Data source** | SEC EDGAR 10-K (revenue growth), 8-K (guidance), FDA databases (pending decisions), 10-K Item 1A (regulatory exposure), financial ratios derived from XBRL |
| **Peer-relative** | Classification is absolute, not peer-relative |
| **Why it matters** | The archetype determines how downstream checks are weighted. A GROWTH_DARLING gets heavier weight on guidance track record and valuation; a DISTRESSED company gets heavier weight on liquidity and going concern |
| **Forward-looking** | Identify if the company is transitioning between archetypes (e.g., GROWTH_DARLING showing DISTRESSED signals = highest risk trajectory) |

---

## 1.6 Overall Quality Score & Factor Breakdown Summary

| Attribute | Detail |
|-----------|--------|
| **What is measured** | Composite quality score (0-100) with individual factor scores displayed as a summary table |
| **How it is derived** | 10-factor model (detailed in Section 7), with each factor's score/max/weight shown. Plus 17 composite pattern detection results shown as detected/not-detected with confidence levels |
| **Data source** | Derived from Section 7 |
| **Display format** | Summary table: Factor name | Score | Max | Weight | Weighted contribution. Plus pattern summary: Pattern name | Detected? | Confidence | Impact |

---

# SECTION 2: COMPANY PROFILE & INDUSTRY CONTEXT

This section establishes WHO the company is, WHAT industry dynamics drive D&O risk, and WHO the peers are. It sets the context for everything that follows.

---

## 2.1 Company Identification Fields

### 2.1.1 Core Identity

| Data Point | Source | Free? | Update Frequency | Notes |
|------------|--------|-------|-------------------|-------|
| **Company legal name** | SEC EDGAR company search API (`https://efts.sec.gov/LATEST/search-index?q=TICKER&dateRange=custom&startdt=...`) | Yes | Static | Use the registrant name from most recent 10-K cover page |
| **Ticker symbol** | SEC EDGAR or Yahoo Finance | Yes | Static | Primary exchange listing |
| **CIK number** | SEC EDGAR Company Tickers JSON (`https://www.sec.gov/files/company_tickers.json`) | Yes | Daily | Central Index Key for all EDGAR lookups |
| **Primary exchange** | SEC EDGAR filing header or Yahoo Finance API | Yes | Static | NYSE / NASDAQ / OTC |
| **SIC code** | SEC EDGAR filing header (browse-edgar `?action=getcompany&CIK=...&type=10-K`) | Yes | Static | 4-digit Standard Industrial Classification |
| **NAICS code** | Census Bureau crosswalk from SIC, or 10-K Item 1 | Yes | Static | 6-digit, more granular than SIC |
| **State of incorporation** | SEC EDGAR 10-K cover page, or DEF 14A | Yes | Annual | Critical for derivative suit exposure analysis |
| **Headquarters location** | SEC EDGAR 10-K cover page | Yes | Annual | State and country |
| **Fiscal year end** | SEC EDGAR filing header | Yes | Static | Month/day |
| **Market capitalization** | Shares outstanding (XBRL: `us-gaap:CommonStockSharesOutstanding` or `dei:EntityCommonStockSharesOutstanding`) x current price (Yahoo Finance) | Yes | Real-time (price) / Quarterly (shares) | Use most recent 10-Q for shares; multiply by current price |
| **Revenue (TTM)** | SEC EDGAR XBRL Company Facts API: `us-gaap:Revenues` or `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` | Yes | Quarterly | Sum of last 4 quarters |
| **Total employees** | SEC EDGAR XBRL: `dei:EntityNumberOfEmployees` (from 10-K) | Yes | Annual | From most recent 10-K |
| **Date first public** | SEC EDGAR first filing date, or IPO date from S-1 effectiveness | Yes | Static | Used for years-public calculation and IPO window risk |
| **Accelerated filer status** | SEC EDGAR 10-K cover page (`dei:EntityFilerCategory`) | Yes | Annual | Large Accelerated / Accelerated / Non-Accelerated / SRC / EGC |

### 2.1.2 Signal Interpretation for Identity Fields

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Years public | <3 years (IPO window) | 3-10 years | >10 years |
| Filer category | Non-accelerated (smaller, less oversight) | Accelerated | Large Accelerated (most SEC scrutiny, but also most established) |
| State of incorporation | Nevada (weaker fiduciary duties), non-Delaware non-standard | Delaware (well-developed case law, plaintiff-friendly Chancery) | Delaware WITH federal forum selection provision |

### 2.1.3 Forward-Looking Component
- **Pending reincorporation**: Check most recent DEF 14A and 8-K for any reincorporation proposals (Delaware to Nevada/Texas trend)
- **IPO window expiration**: If <3 years public, note when the 3-year Section 11 statute of limitations expires
- **Market cap migration**: If market cap is near a tier boundary (e.g., $9B approaching $10B large-cap threshold), note the potential shift in inherent risk baseline

---

## 2.2 Industry Classification & D&O Risk Profile

### 2.2.1 Industry Risk Assessment

| Data Point | Source | What Is Measured | Peer-Relative |
|------------|--------|-----------------|---------------|
| **Industry SCA filing rate** | Stanford SCAC database (filtered by SIC sector), Cornerstone Research annual filings report | Annual securities class action filing rate for this industry sector | Yes -- expressed as multiple of overall base rate (e.g., "Technology: 2.1x base rate") |
| **Industry settlement severity** | Cornerstone Research settlement reports, NERA trend reports | Median and average settlement for this industry | Yes -- expressed as severity multiplier (e.g., "Tech: 1.5-2.5x median") |
| **Industry-specific claim theories** | Cornerstone Research, Woodruff Sawyer D&O Looking Ahead | Which allegation types dominate in this industry (e.g., biotech = FDA/clinical trial misrepresentation; tech = revenue recognition / AI washing; financial = regulatory compliance) | Industry-specific |
| **Industry D&O market share** | Woodruff Sawyer, Aon market reports | What percentage of D&O premium volume this industry represents | Context only |
| **Emerging industry trends** | Cornerstone Research, NERA, D&O Diary, Allianz annual report | New or accelerating claim types (e.g., AI-related filings doubled 2023-2024; tariff-related claims emerging 2025-2026) | Industry-level |

### 2.2.2 Signal Interpretation

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Industry filing rate | >2x base rate (tech, biotech) | 0.8-2x base rate | <0.8x base rate |
| Emerging trends | Company is in the crosshairs of an accelerating claim trend (e.g., AI company during AI-washing surge) | Industry trends stable | Industry trends declining |

### 2.2.3 Forward-Looking Component
- **Regulatory pipeline**: Pending regulations that could change industry risk profile (e.g., SEC climate disclosure rules, AI regulation, FDA pathway changes)
- **Industry litigation trajectory**: Is the industry filing rate trending up, stable, or down over the last 3 years?

---

## 2.3 Peer Group Construction

| Attribute | Detail |
|-----------|--------|
| **What is measured** | Definition of the specific peer group used for all comparative analyses throughout the worksheet |
| **Methodology** | Three-tier peer construction: (1) **Primary peers** (5-8 companies): Same 4-digit SIC code AND within 0.5-2x market cap range. If <5 companies qualify, widen to 3-digit SIC. (2) **Sector benchmark**: Sector ETF (e.g., XLK for technology, XLV for healthcare) for broad market comparison. (3) **Market cap cohort**: All companies in the same market cap tier regardless of industry, for financial ratio percentile ranking |
| **Data source for peer identification** | SEC EDGAR full-text search by SIC code, filtered by market cap. Yahoo Finance screener. Free. Updated quarterly |
| **Data source for sector ETF** | Standard sector ETFs (XLK, XLV, XLF, XLY, XLP, XLE, XLI, XLB, XLU, XLRE, XLC). Free via Yahoo Finance API |
| **Output** | Named list of primary peers with ticker, market cap, and SIC code. Sector ETF identified. Market cap cohort defined |
| **Quality gate** | Minimum 5 primary peers required. If not achievable at 4-digit SIC within 0.5-2x market cap, document the widening steps taken |

### 2.3.1 Forward-Looking Component
- **Peer group stability**: Note if any named peer has a pending M&A that would remove it from the peer set
- **Sector convergence/divergence**: Note if the company is moving into a new competitive space that may warrant different peers in the future

---

## 2.4 Company Event Timeline

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **IPO / SPAC de-merger date** | SEC EDGAR S-1/S-4 effectiveness date | When the company became public and via what mechanism |
| **M&A activity (completed)** | SEC EDGAR 8-K Item 2.01 (completion of acquisition/disposition), 10-K MD&A | Every acquisition and divestiture >5% of market cap in the last 5 years, with date, target, deal value, and current integration status |
| **M&A activity (pending)** | SEC EDGAR 8-K Item 1.01 (entry into material definitive agreement), S-4, SC 14D-9, SC TO | Any announced but unclosed deal, with expected close date, regulatory approval status, and shareholder vote date |
| **Capital raises** | SEC EDGAR S-3, 424B (prospectus supplements), 8-K Item 8.01 | Every equity/debt offering in the last 3 years, with date, type (IPO, SPO, ATM, debt, convertible), amount, and Section 11 exposure window |
| **Restructuring events** | SEC EDGAR 8-K Item 2.05 (costs associated with exit activities), 10-K restructuring footnote | Every restructuring program in the last 3 years, with date announced, charges taken, headcount impact, and completion status |
| **Leadership changes** | SEC EDGAR 8-K Item 5.02 (departure/appointment of D&Os) | Every C-suite and board change in the last 24 months, with date, name, role, and whether departure was voluntary/involuntary |
| **Regulatory milestones** | SEC EDGAR 8-K Item 8.01, FDA databases, DOJ press releases | Significant regulatory events (FDA approvals/rejections, consent decrees, enforcement actions) in the last 3 years |
| **Stock split / reverse split** | SEC EDGAR 8-K Item 8.01, XBRL | Any stock split events (reverse splits can signal distress) |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Event density | >5 material events in 12 months (chaotic) | 1-4 events per year | Stable, predictable cadence |
| M&A track record | Multiple acquisitions with subsequent goodwill impairments | Normal acquisition cadence for industry | Clean integration history |
| Leadership stability | CFO + another C-suite departure within 6 months | Normal turnover (1-2 departures per year) | Stable leadership team >3 years |

### 2.4.1 Forward-Looking Component
- **Upcoming catalysts calendar**: List every known future event with date: next earnings release, annual meeting/proxy vote, debt maturity, M&A close deadline, regulatory decision expected date, lock-up expiration, Section 11 statute expiration
- **Event clustering risk**: Flag if multiple catalysts are concentrated in a short window

---

## 2.5 International & Jurisdictional Exposure

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Geographic revenue breakdown** | SEC EDGAR XBRL: `us-gaap:RevenueFromExternalCustomersByGeographicAreasTableTextBlock` (10-K segment footnote) | Revenue by country/region as % of total |
| **Subsidiary footprint** | SEC EDGAR Exhibit 21 (list of subsidiaries, filed with 10-K) | Number and jurisdiction of subsidiaries, including tax haven jurisdictions |
| **FCPA high-risk exposure** | Exhibit 21 jurisdictions cross-referenced against Transparency International Corruption Perceptions Index (free, annual) | Operations in countries with CPI score <40 (high corruption risk) |
| **Sanctions exposure** | Exhibit 21 jurisdictions cross-referenced against OFAC SDN list and country sanctions programs (free, updated regularly at treasury.gov) | Any operations in or near sanctioned jurisdictions |
| **Non-US listing/ADR status** | SEC EDGAR filing type (20-F for FPI vs. 10-K for domestic) | Whether the company is a Foreign Private Issuer, which affects filing requirements and litigation rates |
| **Cross-border regulatory exposure** | 10-K Item 1A risk factors (keyword search: "GDPR", "Bribery Act", "CSRD", "Pillar Two") | Disclosed exposure to non-US regulatory regimes |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| FCPA exposure | >25% revenue from CPI <40 countries with no disclosed anti-corruption program | Some international exposure with compliance program mentioned | Primarily domestic, or international with robust compliance disclosure |
| Subsidiary complexity | >100 subsidiaries across >30 jurisdictions, including tax havens | Moderate subsidiary count appropriate for business size | Simple corporate structure |

### 2.5.1 Forward-Looking Component
- **Regulatory pipeline by jurisdiction**: Pending regulations (EU CSRD phase-in, SEC climate rules, Pillar Two global minimum tax)
- **Geopolitical risk**: Trade policy changes (tariffs), sanctions program changes, or political instability in material operating jurisdictions

---

## 2.6 Customer & Supplier Concentration

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Customer concentration** | SEC EDGAR 10-K segment footnote: ASC 280 requires disclosure of any customer >10% of revenue. XBRL: `us-gaap:ConcentrationRiskPercentage1` | Identity and revenue percentage of each >10% customer |
| **Supplier concentration** | SEC EDGAR 10-K Item 1 (Business) and Item 1A (Risk Factors) -- keyword search for "sole source", "single supplier", "key vendor" | Disclosed single-source or critical supplier dependencies |
| **Product/service concentration** | SEC EDGAR XBRL segment reporting: `us-gaap:RevenueFromExternalCustomersByProductsAndServicesTableTextBlock` | Revenue breakdown by product/service line. Flag if any single product >50% of revenue |
| **Geographic concentration** | See 2.5 above | Revenue by geography |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Customer concentration | Single customer >25% of revenue, or top 3 customers >50% | Moderate concentration (largest customer 10-20%) | Highly diversified (no customer >5%) |
| Supplier concentration | Single-source dependency for critical input with no disclosed mitigation | Some concentration with backup suppliers identified | Diversified supply base |
| Product concentration | Single product >70% of revenue | Moderate diversification (2-3 major product lines) | Well-diversified across 4+ product lines |

### 2.6.1 Forward-Looking Component
- **Contract renewal dates**: If disclosed, when major customer/supplier contracts expire
- **Known customer/supplier changes**: Any 8-K disclosures of material contract gains or losses
- **Industry disruption risk**: Whether the company's customer or supplier base is at risk from technology disruption, regulation, or competition

---

## 2.7 Corporate Structure Complexity

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Total subsidiary count** | SEC EDGAR Exhibit 21 | Number of entities in the corporate structure |
| **VIE (Variable Interest Entity) exposure** | SEC EDGAR 10-K VIE footnote (XBRL: `us-gaap:VariableInterestEntityTextBlock`) | Off-balance-sheet entities that may require consolidation |
| **Dual-class share structure** | SEC EDGAR DEF 14A, Articles of Incorporation | Whether multiple share classes exist with differential voting rights |
| **Controlled company status** | SEC EDGAR DEF 14A (voting power concentration) | Whether a single shareholder/group holds >50% voting control |
| **SPE/off-balance-sheet entities** | SEC EDGAR 10-K notes (unconsolidated entities, guarantees) | Material off-balance-sheet exposures |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Dual-class | Yes, with >10:1 voting differential | Dual-class with sunset provision | Single-class, one-share-one-vote |
| Controlled company | Yes, with exemptions from exchange governance rules being used | Controlled but complying voluntarily with all governance rules | No controlling shareholder |
| VIE exposure | Material VIEs with consolidation risk | Immaterial VIEs | No VIE structures |

---

# SECTION 3: FINANCIAL HEALTH (Peer-Relative)

Every financial metric in this section is presented BOTH in absolute terms and relative to the peer group defined in Section 2.3. The peer-relative comparison is mandatory, not optional.

---

## 3.1 Income Statement Metrics

| Data Point | XBRL Tag / Source | Frequency | Peer-Relative Method |
|------------|-------------------|-----------|---------------------|
| **Revenue (TTM)** | `us-gaap:Revenues` or `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` | Quarterly (10-Q/10-K) | Percentile rank among primary peers |
| **Revenue growth (YoY)** | Calculated: (Current TTM / Prior TTM) - 1 | Quarterly | vs. peer median and sector ETF growth |
| **Revenue growth (QoQ sequential)** | Calculated from quarterly revenue | Quarterly | vs. peer median |
| **Gross profit margin** | `us-gaap:GrossProfit` / Revenue | Quarterly | Percentile rank among primary peers; flag if >2 standard deviations below peer median |
| **Gross margin trend (4-quarter)** | Calculated: trailing 4 quarters | Quarterly | Direction vs. peers (expanding/contracting relative to peer group) |
| **Operating income (EBIT)** | `us-gaap:OperatingIncomeLoss` | Quarterly | vs. peer median operating margin |
| **Operating margin** | EBIT / Revenue | Quarterly | Percentile rank |
| **Net income** | `us-gaap:NetIncomeLoss` | Quarterly | vs. peers |
| **Net margin** | Net income / Revenue | Quarterly | Percentile rank |
| **EPS (diluted)** | `us-gaap:EarningsPerShareDiluted` | Quarterly | vs. analyst consensus (see 4.8) |
| **EPS growth (YoY)** | Calculated | Quarterly | vs. peer median EPS growth |
| **Revenue by segment** | `us-gaap:RevenueFromExternalCustomersByProductsAndServicesTableTextBlock` | Quarterly | Segment-level trend analysis |
| **Non-GAAP adjustments** | 8-K earnings release reconciliation tables | Quarterly | Size of GAAP-to-non-GAAP delta as % of GAAP net income. Flag if adjustments >50% of GAAP income |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Revenue growth | Declining or negative when peers are growing | In line with peer median (+/- 1 SD) | Above peer 75th percentile |
| Margin trend | Contracting margins for 3+ consecutive quarters while peers stable/expanding | Stable | Expanding margins above peers |
| Non-GAAP gap | Non-GAAP income >2x GAAP income | Modest adjustments (<25% of GAAP) | Minimal adjustments; non-GAAP closely tracks GAAP |

---

## 3.2 Balance Sheet Metrics

| Data Point | XBRL Tag / Source | Peer-Relative |
|------------|-------------------|---------------|
| **Total cash & equivalents** | `us-gaap:CashAndCashEquivalentsAtCarryingValue` | Cash/market cap ratio vs. peers |
| **Short-term investments** | `us-gaap:ShortTermInvestments` | Combined liquidity |
| **Total assets** | `us-gaap:Assets` | Context for ratios |
| **Total debt (short + long term)** | `us-gaap:ShortTermBorrowings` + `us-gaap:LongTermDebtNoncurrent` + `us-gaap:LongTermDebtCurrent` | Debt/equity vs. peer median |
| **Net debt** | Total debt minus cash | Net debt/EBITDA vs. peers |
| **Total stockholders' equity** | `us-gaap:StockholdersEquity` | Book value trend |
| **Goodwill** | `us-gaap:Goodwill` | Goodwill/total assets %. Flag if >40% |
| **Goodwill as % of equity** | Calculated | If goodwill > equity, impairment could wipe out book value |
| **Working capital** | Current assets - current liabilities | Trend over 4 quarters |
| **Current ratio** | Current assets / current liabilities | vs. peer median |
| **Quick ratio** | (Cash + ST investments + receivables) / current liabilities | vs. peer median |
| **Debt-to-equity ratio** | Total debt / equity | vs. peer median. Flag if >2x peer median |
| **Debt-to-EBITDA** | Total debt / TTM EBITDA | vs. peer median |
| **Interest coverage ratio** | EBIT / `us-gaap:InterestExpense` | vs. peer median. Flag if <2x |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Net debt/EBITDA | >4x (highly leveraged) | 1-3x | <1x or net cash position |
| Goodwill/equity | >100% (impairment could eliminate book value) | 25-75% | <25% |
| Interest coverage | <2x | 3-6x | >6x |
| Working capital trend | Declining for 3+ quarters | Stable | Improving |

---

## 3.3 Cash Flow Metrics

| Data Point | XBRL Tag / Source | Peer-Relative |
|------------|-------------------|---------------|
| **Operating cash flow (TTM)** | `us-gaap:NetCashProvidedByUsedInOperatingActivities` | OCF margin vs. peer median |
| **Capital expenditures** | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` | Capex/revenue vs. peers |
| **Free cash flow** | OCF minus capex | FCF margin vs. peers |
| **FCF yield** | FCF / market cap | vs. peer median |
| **OCF vs. net income** | Ratio: OCF / net income | If consistently <0.8, earnings quality concern |
| **Cash flow from financing** | `us-gaap:NetCashProvidedByUsedInFinancingActivities` | Direction and composition (debt vs. equity) |
| **Share repurchases** | `us-gaap:PaymentsForRepurchaseOfCommonStock` | Buyback yield vs. peers |
| **Dividends paid** | `us-gaap:PaymentsOfDividends` | Payout ratio and sustainability |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| OCF/NI ratio | <0.5 (earnings significantly exceed cash generation -- accruals concern) | 0.8-1.2 | >1.0 consistently |
| FCF | Negative for 2+ consecutive years (non-growth company) | Positive but below peers | Positive and above peer median |
| Cash flow divergence | Net income growing while OCF declining (classic pre-fraud pattern) | Trends aligned | OCF growing faster than net income |

---

## 3.4 Earnings Quality Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Sloan Accrual Ratio** | Calculated: (Net income - OCF) / average total assets | Accruals intensity. Higher accruals = lower earnings quality. Flag if >10% |
| **CFRA-style earnings quality score** | Calculated from: OCF/NI ratio, accruals ratio, DSO trend, inventory trend, deferred revenue trend | Composite earnings quality grade (A through F or 0-100 score) |
| **Days Sales Outstanding (DSO) trend** | `us-gaap:AccountsReceivableNetCurrent` / (Revenue/365), trailing 4 quarters | Rising DSO faster than revenue growth = potential channel stuffing |
| **Days Inventory Outstanding (DIO) trend** | `us-gaap:InventoryNet` / (COGS/365), trailing 4 quarters | Rising DIO = potential inventory obsolescence or over-production |
| **Revenue recognition complexity** | 10-K Critical Accounting Estimates + Note 2 (revenue recognition policy). Manual review or NLP keyword extraction: "variable consideration", "performance obligations", "contract modifications", "percentage-of-completion" | Subjective assessment: LOW / MODERATE / HIGH complexity |
| **Non-GAAP adjustment quality** | 8-K earnings release. Measure: (non-GAAP EPS - GAAP EPS) / |GAAP EPS| | Persistent large adjustments suggest management prefers to highlight a metric disconnected from GAAP reality |
| **Cookie jar reserve risk** | Sudden large reserve releases or reversals (10-K/10-Q notes). `us-gaap:LossContingencyAccrualAtCarryingValue` trend | Management smoothing earnings using reserves |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Accrual ratio | >15% | 5-10% | <5% |
| DSO trend | Rising >20% YoY while revenue flat or declining | Stable | Declining or stable with growing revenue |
| Revenue recognition | HIGH complexity (multiple judgment-intensive methods) | MODERATE | LOW (straightforward product sales) |
| Non-GAAP gap | Adjustments >100% of GAAP income for 4+ quarters | 25-50% | <25% |

---

## 3.5 Distress Indicators

| Data Point | Calculation | Source | Thresholds |
|------------|-------------|--------|------------|
| **Altman Z-Score** | 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(Mkt Cap/TL) + 1.0*(Rev/TA) | Calculated from XBRL financial data | **Red:** <1.81 (distress zone). **Neutral:** 1.81-2.99 (gray zone). **Green:** >2.99 (safe zone) |
| **Beneish M-Score** | 8-variable model: DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA | Calculated from XBRL financial data (requires 2 years of data) | **Red:** >-1.78 (likely manipulator). **Neutral:** -1.78 to -2.22. **Green:** <-2.22 |
| **Ohlson O-Score** | Bankruptcy prediction model using 9 accounting variables | Calculated from XBRL data | **Red:** >0.5 (high bankruptcy probability). **Green:** <0.5 |
| **Piotroski F-Score** | 9-point scoring: profitability (4), leverage/liquidity (3), operating efficiency (2) | Calculated from XBRL data | **Red:** 0-3. **Neutral:** 4-6. **Green:** 7-9 |

**Peer-relative**: All scores are computed for each peer company and the subject company is ranked in percentile terms.

### 3.5.1 Forward-Looking Component
- **Score trajectory**: Calculate the Z-Score and M-Score for the last 4 quarters. Is the company moving toward or away from danger zones?
- **Peer divergence**: Is this company's score deteriorating while peers improve?

---

## 3.6 Audit Risk Indicators

| Data Point | Source | Free? | Update Frequency |
|------------|--------|-------|------------------|
| **Auditor identity** | SEC EDGAR 10-K auditor report (XBRL: `dei:AuditorName`) | Yes | Annual |
| **Big 4 status** | Derived from auditor name | Yes | Annual |
| **Auditor tenure** | Count years of consecutive 10-K filings with same auditor | Yes | Annual |
| **Auditor changes** | SEC EDGAR 8-K Item 4.01 (`currentReportItemNumber=4.01`) | Yes | Event-driven |
| **Disagreements on change** | 8-K Item 4.01 checkbox and narrative disclosure | Yes | Event-driven |
| **Audit opinion type** | 10-K auditor report: Unqualified / Qualified / Adverse / Disclaimer | Yes | Annual |
| **Going concern opinion** | 10-K auditor report: presence of "substantial doubt about ability to continue as a going concern" | Yes | Annual |
| **Material weaknesses** | 10-K management assessment of ICFR (XBRL: `us-gaap:InternalControlOverFinancialReportingMaterialWeaknessRemediated` and related tags), or auditor adverse opinion on ICFR | Yes | Annual |
| **Restatements (last 5 years)** | SEC EDGAR filings search for 10-K/A and 10-Q/A form types, or 8-K Item 4.02 (non-reliance on financial statements) | Yes | Event-driven |
| **Late filings (NT forms)** | SEC EDGAR filings search for form types "NT 10-K" and "NT 10-Q" (Form 12b-25) | Yes | Event-driven |
| **SEC comment letters** | SEC EDGAR CORRESP filings (search by CIK) | Yes (with 60-day delay) | Event-driven |
| **Critical Audit Matters (CAMs)** | 10-K auditor report: CAM descriptions and management response | Yes | Annual |
| **PCAOB inspection results for auditor** | PCAOB website (pcaobus.org) -- inspection reports by firm | Yes | Annual |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Auditor | Non-Big 4 for large cap; recent switch from Big 4 to non-Big 4; mid-year switch | Big 4, stable tenure 5-15 years | Big 4, long tenure, clean opinion |
| Going concern | Present | N/A | Absent |
| Material weakness | Disclosed and unremediated | Disclosed and remediated | None |
| Restatement | Within last 2 years | 3-5 years ago, remediated | None in 5 years |
| Late filings | Any NT 10-K/10-Q in last 3 years | None | Clean filing history |
| SEC comment letters | Aggressive or escalating comments; amendments required | Routine comments resolved quickly | No recent comments |

### 3.6.1 Forward-Looking Component
- **Open SEC comment letters**: Any comment letters without visible response (correspondence still pending)
- **Upcoming auditor rotation**: If auditor tenure >20 years, potential mandatory rotation pressure
- **Pending remediation**: If material weakness disclosed, expected remediation timeline

---

## 3.7 Tax Aggressiveness Indicators

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Effective tax rate (ETR)** | `us-gaap:IncomeTaxExpenseBenefit` / `us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | Statutory vs. effective rate gap |
| **Cash effective tax rate** | `us-gaap:IncomeTaxesPaid` / pre-tax income | Cash taxes actually paid vs. book tax expense |
| **Unrecognized Tax Benefits (UTB)** | `us-gaap:UnrecognizedTaxBenefits` (from tax footnote) | Size and trend of UTB balance. Academic research directly links UTB growth to D&O premium increases |
| **Tax haven subsidiary count** | Exhibit 21 cross-referenced against tax haven lists (Cayman Islands, Bermuda, Ireland, Netherlands, Luxembourg, Singapore, Switzerland, Hong Kong) | Number and significance of tax haven entities |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| ETR gap | >15 percentage points below statutory rate for 3+ years | Within 5pp of statutory | At or above statutory (conservative) |
| Cash ETR | Cash ETR < 50% of book ETR (aggressive tax planning) | Reasonably aligned | Cash ETR close to book ETR |
| UTB growth | Growing >25% YoY for 2+ years | Stable | Declining (resolving uncertain positions) |

---

## 3.8 Credit & Liquidity Profile

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Credit rating** | 8-K disclosures, rating agency websites (Moody's, S&P, Fitch). Not always free but often disclosed in 10-K | Current rating and outlook (positive/stable/negative) |
| **Debt maturity schedule** | 10-K debt footnote: `us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths` and related tags for years 2-5 | Near-term maturities that could trigger liquidity pressure |
| **Revolving credit facility** | 10-K or 8-K (credit agreement filed as exhibit). Available capacity, drawn amount, maturity date | Available liquidity buffer |
| **Covenant compliance** | 10-K/10-Q MD&A or credit agreement exhibit | Proximity to financial covenant violations |
| **Cash runway** | Current cash / monthly cash burn (for cash-burning companies) | Months of operation without additional financing |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Credit rating | Below investment grade (BB+ or lower) or recent downgrade | BBB/BBB+ stable | A- or above |
| Debt maturity wall | >30% of total debt maturing in next 12 months with insufficient cash/revolver | Balanced maturity profile | No near-term maturities |
| Covenant headroom | <10% headroom on key covenants | >25% headroom | >50% headroom or no financial covenants |

### 3.8.1 Forward-Looking Component
- **Debt maturity wall**: Next 12-month and 24-month maturity obligations
- **Refinancing risk**: Current credit spreads for the company's rating tier vs. existing coupon rates
- **Guidance vs. actual track record**: See Section 4.8 for full detail -- summarized here as trailing 12-quarter beat/miss rate
- **Analyst revenue/earnings estimates**: Next quarter and full-year consensus estimates, providing forward expectation context

---

# SECTION 4: MARKET & TRADING SIGNALS

This section focuses on what the market -- stock price, insiders, short sellers, analysts -- is telling us about D&O risk.

---

## 4.1 Stock Price Performance

| Data Point | Source | Peer-Relative |
|------------|--------|---------------|
| **Current price** | Yahoo Finance API (free) or equivalent | N/A |
| **52-week high** | Yahoo Finance API | N/A |
| **52-week low** | Yahoo Finance API | N/A |
| **Decline from 52-week high** | Calculated: (Current - 52wk high) / 52wk high | vs. sector ETF decline from high |
| **1-year total return** | Yahoo Finance API historical prices | vs. sector ETF, vs. S&P 500, vs. primary peers (median) |
| **3-year total return** | Yahoo Finance API | Same comparisons |
| **5-year total return** | Yahoo Finance API | Same comparisons |
| **YTD return** | Calculated | vs. sector ETF |
| **Beta (5-year monthly)** | Yahoo Finance API or calculated from price history | Absolute level and vs. peer median |
| **Annualized volatility (1yr)** | Calculated: standard deviation of daily returns x sqrt(252) | vs. sector ETF volatility |
| **Maximum drawdown (1yr)** | Calculated: largest peak-to-trough decline in 1-year window | vs. peer median max drawdown |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| 1yr return vs. sector | Underperforming sector by >20% | Within +/- 10% of sector | Outperforming sector by >10% |
| Decline from high | >40% from 52-week high | 10-25% | <10% |
| Beta | >1.5 (high volatility amplifies DDL) | 0.8-1.2 | <0.8 |
| Max drawdown vs. peers | Worst in peer group by >10pp | In line with peers | Best in peer group |

### 4.1.1 Forward-Looking Component
- **Upcoming earnings date**: Next scheduled earnings release (from Yahoo Finance or company IR calendar)
- **Known catalysts**: Events that could cause material stock price movement (FDA decisions, trial verdicts, regulatory rulings, M&A closes)
- **Implied volatility**: If available, options-implied 30-day volatility vs. realized volatility (high IV = market expecting big move)

---

## 4.2 Stock Drop Analysis (>5% Single-Day Declines)

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Every single-day decline >5% in last 12 months** | Yahoo Finance API daily price history. Calculated: (close - prior close) / prior close | Date, magnitude, and sector ETF return on same day |
| **Triggering event for each drop** | 8-K filings on or near the date, earnings releases, news articles (via news API or manual review) | What caused the drop: earnings miss, guidance cut, regulatory action, analyst downgrade, executive departure, product issue, market-wide event |
| **Company-specific vs. market attribution** | Company return minus sector ETF return on the same day | A drop of -8% when the sector dropped -7% is noise; a drop of -8% when the sector was flat is a signal |
| **Corrective disclosure identification** | For each company-specific drop: does it correspond to a new disclosure that contradicts prior positive statements? | If yes, this is a potential "corrective disclosure" for SCA complaint drafting |
| **DDL estimate for each drop** | Market cap on day prior x |abnormal return| | Approximate Disclosure Dollar Loss for each event |

### 4.2.1 Multi-Day Decline Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Cumulative 2-day declines >10%** | Calculated from daily prices | Captures earnings drops that span after-hours + next day |
| **Cumulative 5-day declines >15%** | Calculated | Captures cascading bad news sequences |
| **Cumulative 20-day declines >25%** | Calculated | Captures slow-motion corrections |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Company-specific drops >10% | 2+ in 12 months | 0-1 | None |
| Corrective disclosures identified | Any identified | None | N/A |
| DDL concentration | Single event DDL >$1B | <$500M aggregate | Minimal |

---

## 4.3 Insider Trading Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **All Form 4 filings (last 12 months)** | SEC EDGAR Form 4 filings by CIK (`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=...&type=4&dateb=&owner=include&count=40`) | Every insider transaction: name, title, date, buy/sell, shares, price, value |
| **Net insider buying/selling ($ value)** | Aggregated from Form 4 data | Net purchase or net sale in last 12 months |
| **10b5-1 plan status** | Form 4 footnotes (check for "10b5-1" or "Rule 10b5-1" text) | Whether each transaction was under a pre-established plan |
| **Discretionary vs. plan transactions** | Derived from 10b5-1 status | Discretionary sales are more informative (and more concerning) |
| **Cluster selling patterns** | Time series analysis of Form 4 dates | Multiple insiders selling in the same window = elevated concern |
| **Timing relative to announcements** | Cross-reference Form 4 dates with 8-K dates and earnings dates | Sales clustered before bad news = scienter indicator |
| **10b5-1 plan adoptions/terminations/modifications** | Form 4 footnotes and 8-K Item 5.02(a) (new SEC rules effective 2023 require 8-K disclosure) | New plan adoptions close to material events are a red flag |
| **Insider ownership level** | Proxy statement (DEF 14A) beneficial ownership table | Total insider ownership as % of shares outstanding |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Net selling | >$10M net selling by C-suite in 12 months outside 10b5-1 plans | Modest selling under 10b5-1 plans | Net buying by multiple insiders |
| Cluster selling | 3+ insiders selling in same 30-day window | Single insider, routine | Multiple insiders buying |
| Timing | Sales within 30 days before a >10% stock decline | No suspicious timing | Purchases before positive events |
| 10b5-1 manipulation | Plan adopted <90 days before material event (new SEC rules address this) | Plans in place >6 months | Long-standing plans with consistent execution |

### 4.3.1 Forward-Looking Component
- **Upcoming lockup expirations**: For IPO/SPAC companies, when insider lockup expires (Form 144 filings may signal intent)
- **10b5-1 plan schedules**: If plan details are disclosed, when future sales are expected
- **Insider ownership changes**: Whether insider ownership is trending up or down

---

## 4.4 Short Interest Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Current short interest (shares)** | Yahoo Finance API (`shortPercentOfFloat`) or FINRA bi-monthly reports | Shares sold short |
| **Short interest as % of float** | Short shares / float shares | Magnitude of bearish bets |
| **Short interest trend (6 months)** | Time series from FINRA bi-monthly reports | Whether shorts are increasing or decreasing |
| **Days to cover** | Short shares / average daily volume | How many days of normal trading needed to cover shorts |
| **Short interest vs. peers** | Same data computed for each peer company | Percentile rank of short interest within peer group |
| **Short interest vs. sector median** | Sector-level aggregation | Above or below sector norm |
| **Short seller reports** | Manual search: Hindenburg Research, Muddy Waters, Citron Research, Spruce Point, etc. | Whether any activist short seller has published a thesis on this company |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Short % of float | >10% | 2-5% | <2% |
| Trend | Increasing >50% in 6 months | Stable | Declining |
| Days to cover | >10 days | 2-5 days | <2 days |
| vs. peers | >75th percentile | 25th-75th | <25th percentile |
| Short seller report | Published within 12 months | None | N/A |

---

## 4.5 Earnings Guidance Track Record

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **12-quarter guidance history** | Company 8-K filings (earnings guidance), cross-referenced with actual results from subsequent 10-Q/10-K | For each of the last 12 quarters: what was guided (revenue and/or EPS range), what was delivered, beat/meet/miss classification, magnitude of miss as % of guided midpoint |
| **Beat rate** | Calculated: quarters where actual >= guided midpoint / 12 | Percentage of quarters meeting or exceeding guidance |
| **Miss magnitude distribution** | For misses: average miss as % of guidance | Size of misses when they occur |
| **Consecutive misses** | Calculated | Longest streak of consecutive guidance misses |
| **Guidance philosophy** | Derived from pattern: CONSERVATIVE (usually beats by meaningful amount), NEUTRAL (usually meets), AGGRESSIVE (frequently misses) | Management's tendency |
| **Guidance withdrawals** | 8-K filings: any quarter where guidance was withdrawn or suspended | Significant event -- often precedes bad news |
| **Stock price reaction to misses** | Daily returns on earnings dates crossed with miss data | For each miss: what happened to the stock? |
| **Guidance specificity** | Type of guidance: specific number, range, qualitative, none | Specific guidance = higher expectations = higher miss risk |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Beat rate | <50% (frequent misser) | 50-75% | >75% (conservative guide) |
| Consecutive misses | 3+ | 0-1 | None in 12 quarters |
| Guidance withdrawal | Any in last 8 quarters | None | N/A |
| Miss + stock drop | Multiple misses causing >5% drops | Misses with minimal market reaction | Beats consistently rewarded |

---

## 4.6 Analyst Sentiment

| Data Point | Source | Free? | What Is Measured |
|------------|--------|-------|-----------------|
| **Number of covering analysts** | Yahoo Finance API (`recommendationMean`, `numberOfAnalystOpinions`) | Yes | Breadth of coverage (thin coverage = higher information asymmetry) |
| **Consensus recommendation** | Yahoo Finance API | Yes | Mean recommendation (1=Strong Buy to 5=Sell) |
| **Mean/median price target** | Yahoo Finance API (`targetMeanPrice`, `targetMedianPrice`) | Yes | Implied upside/downside from current price |
| **Price target range** | Yahoo Finance API (`targetLowPrice`, `targetHighPrice`) | Yes | Dispersion of analyst views (wide range = high uncertainty) |
| **Recent upgrades/downgrades (90 days)** | Yahoo Finance or financial news APIs | Yes (partial) | Direction of analyst sentiment change |
| **Earnings estimate revisions (90 days)** | Yahoo Finance API (earnings estimate trends) | Yes | Whether next-quarter and next-year estimates are being revised up or down |
| **Estimate dispersion** | Calculated: (High estimate - Low estimate) / Mean estimate | Yes | High dispersion = high uncertainty about future results |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Consensus | >3.5 (underperform/sell territory) | 2.0-3.0 | <2.0 (strong buy consensus) |
| Price target upside | <-10% (trading above consensus target) | 0-20% upside | >20% upside |
| Estimate revisions | Downward revisions by >5% in 90 days | Stable | Upward revisions |
| Coverage count | <5 analysts (thin -- high information asymmetry) | 5-15 | >15 (heavily covered) |

---

## 4.7 Capital Markets Activity & Section 11 Exposure

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Active shelf registrations** | SEC EDGAR search for effective S-3 filings | Whether the company has an active shelf registration enabling quick securities offerings |
| **Recent equity offerings (3 years)** | SEC EDGAR 424B filings (prospectus supplements), S-1 (IPO), S-3 (shelf) | Every equity offering with date, type, amount, underwriters |
| **Recent debt offerings (3 years)** | SEC EDGAR 424B filings, 8-K Item 8.01 | Every debt issuance with date, amount, coupon, maturity |
| **ATM (at-the-market) programs** | SEC EDGAR prospectus supplements for ATM offerings | Active ATM program: total authorized amount, amount remaining |
| **Section 11 exposure window** | Calculated: date of most recent offering + 3 years (statute of limitations) | Whether the company is currently within the Section 11 litigation window for any offering |
| **Convertible securities outstanding** | 10-K/10-Q balance sheet notes | Outstanding convertibles that could dilute equity and create complex securities claims |
| **PIPE transactions** | 8-K Item 3.02 (unregistered sales of equity securities) | Private placements that may indicate difficulty accessing public markets |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Section 11 window | Currently within 3 years of an IPO or major equity offering | More than 3 years since last offering | No recent offerings |
| Capital market activity | Frequent offerings (3+ in 24 months) suggesting cash burn | Occasional offerings appropriate for business needs | No need to access markets (self-funding) |
| ATM program | Active ATM with heavy utilization | Shelf registration on file but unused | No ATM or shelf |

---

## 4.8 Adverse Corporate Event Scoring (SAR-Style)

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Event count (12 months)** | Aggregated from: stock drops >5%, 8-K filings (material events), SEC comment letters, insider selling clusters, analyst downgrades, short seller reports | Total count of adverse events in the last 12 months |
| **Event severity weighting** | Each event type assigned a severity weight: stock drop >10% (HIGH), restatement (CRITICAL), SEC investigation (CRITICAL), executive departure (MODERATE), analyst downgrade (LOW), short seller report (HIGH) | Weighted adverse event score |
| **Peer comparison** | Same event scoring computed for each peer | Percentile rank of adverse event score within peer group |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| vs. peers | >75th percentile (more adverse events than 75% of peers) | 25th-75th percentile | <25th percentile |
| Absolute count | >5 adverse events in 12 months | 1-3 | 0 |

### 4.8.1 Forward-Looking Component for All of Section 4
- **Upcoming earnings date**: Exact date with consensus estimates
- **Guidance expectations**: Whether the market expects guidance raise, maintenance, or cut
- **Known catalysts calendar**: Every known future event with date that could move the stock (FDA decision dates, trial verdict dates, regulatory ruling dates, M&A close deadlines, debt maturities, lockup expirations)
- **Analyst estimate trajectory**: Are forward estimates trending up or down?
- **Short interest trajectory**: Is the short trade building or unwinding?

---

# SECTION 5: GOVERNANCE & LEADERSHIP

---

## 5.1 Board Composition

| Data Point | Source | Peer-Relative |
|------------|--------|---------------|
| **Total directors** | DEF 14A proxy statement (SEC EDGAR) | vs. peer median |
| **Independent directors** | DEF 14A (independence designation per exchange rules) | Count and percentage vs. peers |
| **Independence ratio** | Independent / total | Flag if <2/3 for non-controlled companies |
| **Board diversity** | DEF 14A board matrix (required by Nasdaq since 2023) or individual bios | Gender, racial/ethnic diversity counts |
| **Average board tenure** | Calculated from DEF 14A director biographies (year first elected) | Flag if average >12 years (potential entrenchment) or <2 years (instability) |
| **New directors (last 24 months)** | DEF 14A, 8-K Item 5.02 | Count and context (refreshment vs. crisis response) |
| **CEO/Chair duality** | DEF 14A | Whether CEO also serves as Board Chair |
| **Lead independent director** | DEF 14A | Whether a lead independent director exists (especially important when CEO=Chair) |
| **Board meeting frequency** | DEF 14A (reported annually) | Number of full board meetings. Flag if <6 per year |
| **Director overboarding** | DEF 14A bios cross-referenced for each director's other board seats | Count directors serving on >3 public company boards (ISS considers this overboarded) |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Independence | <2/3 independent (non-controlled) | 2/3 to 75% | >80% independent |
| CEO=Chair | Yes, with no lead independent director | CEO=Chair with strong lead independent | Separate CEO and Chair |
| Average tenure | >15 years (entrenchment) or <2 years (instability) | 5-12 years | 6-10 year balanced refreshment |
| Overboarding | >2 directors overboarded | 1 director overboarded | None overboarded |

---

## 5.2 Committee Structure

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Audit committee composition** | DEF 14A | Size, all independent (required), financial expert designated (required by SOX) |
| **Audit committee financial expert** | DEF 14A (required disclosure) | Name and qualifications of designated financial expert |
| **Compensation committee composition** | DEF 14A | Size, independence, outside advisors used |
| **Nominating/governance committee** | DEF 14A | Existence, independence, director nomination process |
| **Risk committee** | DEF 14A | Whether a separate risk committee exists (common in financial services, less so elsewhere) |
| **Cybersecurity oversight** | 10-K Item 1C (required since December 2023) + DEF 14A | Which committee/board has cybersecurity oversight, and what is the reporting cadence |

---

## 5.3 Individual D&O Risk Profiles

**For EACH named executive officer and director (typically 12-20 individuals):**

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Name and current role** | DEF 14A, 10-K cover page | Identity |
| **Tenure in current role** | DEF 14A bios, 8-K Item 5.02 history | Years in position. Short tenure for CFO (<2 years) can be a concern |
| **Career history** | DEF 14A biographical information | Prior companies and roles |
| **Personal litigation history** | Stanford SCAC (search by individual name as defendant). Free. Also PACER (federal court) if deeper search needed ($0.10/page) | Whether this person has been named as a defendant in a securities class action or derivative suit at any company |
| **SEC enforcement actions** | SEC AAER (Accounting and Auditing Enforcement Releases) database (`sec.gov/litigation/admin.shtml`). Free | Whether this person has been subject to SEC enforcement |
| **Prior company associations** | DEF 14A bio cross-referenced against Stanford SCAC, SEC enforcement, and bankruptcy records | Whether any prior employer experienced a bankruptcy, restatement, or enforcement action during this person's tenure |
| **Other current board seats** | DEF 14A | Other public company boards served on, with risk assessment of each (are any currently under SEC investigation or in litigation?) |
| **Board interlock contagion** | Cross-reference other board seats against Stanford SCAC active case list | Whether any other company where this person serves as director is currently in D&O litigation |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Personal litigation | Named defendant in prior SCA or SEC action | No history found | N/A |
| Prior company issues | Prior employer had restatement/enforcement during their tenure | No problematic associations | Long track record at well-regarded companies |
| Board interlocks | Serving on board of a company currently in litigation | Serving on stable company boards | Limited outside commitments |

### 5.3.1 Forward-Looking Component
- **Upcoming departures**: Any announced retirements, contract expirations, or transition plans for executives
- **Board election cycle**: When each director's term expires and whether they are standing for re-election
- **Succession planning**: Whether the company has disclosed succession planning for CEO/CFO

---

## 5.4 Executive Compensation Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **CEO total compensation** | DEF 14A Summary Compensation Table | Total comp: salary + bonus + stock + options + other |
| **CEO pay ratio** | DEF 14A (required disclosure) | CEO compensation / median employee compensation |
| **CEO pay vs. peer median** | DEF 14A compensation benchmarking + peer analysis | Percentile rank of CEO pay among disclosed peer group |
| **Compensation mix** | DEF 14A | % base salary, % annual cash incentive, % long-term equity, % other. High equity proportion = high sensitivity to stock price = potential incentive misalignment |
| **Performance metrics used** | DEF 14A CD&A (Compensation Discussion & Analysis) | What metrics trigger incentive payouts: revenue, EPS, TSR, ROIC, etc. |
| **Say-on-pay vote results** | DEF 14A (most recent annual meeting results). XBRL: `dei:EntityRegistrantName` search for Form 8-K voting results | Percentage of votes "FOR" say-on-pay resolution |
| **Clawback policy** | DEF 14A or clawback policy filed as exhibit (required by SEC since 2023) | Existence, scope (mandatory vs. voluntary), breadth (beyond SEC minimum) |
| **Related party transactions** | DEF 14A "Certain Relationships and Related Party Transactions" section | Any transactions between the company and D&Os or their affiliates, including dollar amounts, terms, and board approval process |
| **Perquisites** | DEF 14A Summary Compensation Table "All Other Compensation" column and footnotes | Unusual or excessive perks |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Say-on-pay | <70% support (ISS/Glass Lewis threshold for concern) | 70-90% | >90% |
| Pay vs. performance | High pay + poor stock performance (pay-performance disconnect) | Pay aligned with performance | Pay closely tied to demonstrated results |
| Related party transactions | Material RPTs with CEO/controlling shareholder at non-market terms | Modest RPTs with proper board approval | None or immaterial |
| Clawback | Minimum compliance only | Meets SEC requirements | Exceeds SEC requirements (broader scope, longer lookback) |

---

## 5.5 Officer & Director Turnover

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **All C-suite departures (24 months)** | SEC EDGAR 8-K Item 5.02 | Name, role, departure date, whether voluntary/involuntary, reason if disclosed |
| **All board departures (24 months)** | 8-K Item 5.02 and DEF 14A | Same detail. Flag any mid-term resignations (vs. end-of-term non-renewal) |
| **CFO turnover** | 8-K Item 5.02 | CFO departures are the single strongest leading indicator among executive changes |
| **CAO/Controller turnover** | 8-K Item 5.02 | Chief Accounting Officer departures signal potential accounting issues |
| **General Counsel turnover** | 8-K Item 5.02 | Legal leadership change can signal litigation/regulatory concerns |
| **Simultaneous departures** | Cross-reference departure dates | Multiple C-suite departures within 3 months = extreme red flag |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| CFO departure | Unexpected/sudden within last 12 months | Planned transition with successor named | Stable CFO tenure >3 years |
| Multiple departures | 3+ C-suite departures in 12 months | 1 departure with clear succession | Stable team |
| Mid-term board resignation | Director resignation between annual meetings with no clear reason | End-of-term departure | Full board standing for re-election |

---

## 5.6 Anti-Takeover Provisions & Charter Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Classified/staggered board** | DEF 14A | Whether directors serve 1-year or 3-year terms |
| **Poison pill (shareholder rights plan)** | DEF 14A, 8-K, 8-A filings | Whether a poison pill is in effect, its terms, and whether board-adopted or shareholder-approved |
| **Supermajority voting requirements** | Articles of Incorporation (filed on EDGAR) | Voting thresholds for mergers, charter amendments, etc. |
| **Blank-check preferred stock** | Articles of Incorporation | Board authority to issue preferred stock without shareholder approval |
| **Special meeting calling rights** | Bylaws (filed on EDGAR) | Minimum ownership threshold to call a special meeting |
| **Written consent rights** | Bylaws | Whether shareholders can act by written consent (vs. requiring a meeting) |
| **Forum selection bylaws** | Bylaws | Exclusive forum provisions for internal corporate claims (Delaware Chancery) and Securities Act claims (federal court) |
| **Fee-shifting provisions** | Bylaws (rare for stock corporations post-2015 Delaware legislation) | Provisions shifting litigation costs to losing plaintiffs |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Anti-takeover concentration | Staggered board + poison pill + supermajority requirements (entrenchment risk) | Some provisions, standard for industry | Annual elections, no poison pill, majority voting |
| Forum selection | No forum selection provision (multi-forum litigation risk) | Forum selection for fiduciary claims only | Both Delaware forum + federal forum provisions (comprehensive litigation cost control) |

### 5.6.1 Forward-Looking Component
- **Upcoming shareholder proposals**: Any governance reform proposals on the next proxy (declassification, poison pill repeal, etc.)
- **Expiring provisions**: When sunset provisions on dual-class or poison pill expire
- **Board election outcomes**: Upcoming director elections and whether any contested

---

## 5.7 Ownership Structure

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Institutional ownership %** | SEC EDGAR 13F filings (quarterly, free). Or Yahoo Finance API (`institutionsPercentHeld`) | Total shares held by institutional investors |
| **Top 10 institutional holders** | 13F filings or Yahoo Finance | Names, share counts, % of total. Identify any activist funds |
| **Insider ownership %** | DEF 14A beneficial ownership table | Total shares held by D&Os |
| **Dual-class voting control** | DEF 14A | Voting power vs. economic ownership (if dual-class) |
| **13D filings (last 24 months)** | SEC EDGAR search for SC 13D filings by company | Any investor crossing 5% with activist intent |
| **13G to 13D conversions** | SEC EDGAR | A conversion from passive (13G) to active (13D) filing signals activist shift |
| **Proxy contest history (3 years)** | DEF 14A, DEFC14A (dissident proxy) filings | Any proxy fights or settlement agreements with activists |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Activist presence | Active 13D filing from known activist fund | 13G passive filings only | No >5% activist holders |
| Institutional concentration | Top 5 holders own >50% (high litigation lead plaintiff risk) | Normal institutional ownership (60-80% for large cap) | Well-diversified shareholder base |
| Insider ownership | <1% (misalignment) or >50% voting control (entrenchment) | 3-15% (alignment without entrenchment) | 5-20% with balanced voting structure |

### 5.7.1 Forward-Looking Component
- **Activist campaign risk assessment**: Company characteristics that make it an activist target (underperformance vs. peers, governance deficiencies, excess cash, conglomerate structure)
- **Upcoming proxy season items**: Shareholder proposals scheduled for next annual meeting
- **13D filing monitoring**: Any recent 13D amendments suggesting increased position or new demands

---

# SECTION 6: LITIGATION & REGULATORY EXPOSURE

---

## 6.1 Securities Class Action History

| Data Point | Source | Free? | What Is Measured |
|------------|--------|-------|-----------------|
| **Active securities class actions** | Stanford SCAC (`securities.stanford.edu`) search by company name/ticker | Yes | Case name, case number, court, filing date, class period, allegations, lead plaintiff, lead counsel, current status |
| **Historical SCAs (10 years)** | Stanford SCAC | Yes | All filed cases: outcome (dismissed, settled, ongoing), settlement amount if settled |
| **Settlements (5 years)** | Stanford SCAC and Cornerstone Research settlement database | Yes | Settlement amounts, terms, date of settlement |
| **Lead counsel identity** | Stanford SCAC case details | Yes | Whether lead plaintiff counsel is a top-tier firm (Bernstein Litowitz, Robbins Geller, Pomerantz, Scott+Scott). Top-tier counsel correlates with more aggressive prosecution and higher settlements |
| **Lead plaintiff identity** | Stanford SCAC case details | Yes | Whether lead plaintiff is a public pension fund (3.5x median settlement multiplier) or institutional investor |
| **Current procedural status** | Stanford SCAC, PACER | Yes (SCAC) / $0.10/page (PACER) | Motion to dismiss pending/granted/denied, discovery stage, class certification, settlement negotiations, trial date |
| **Class period dates** | Stanford SCAC | Yes | Start and end dates. Longer class periods = larger potential damages |
| **Allegation types** | Stanford SCAC case details | Yes | Which statutory provisions: Rule 10b-5 (fraud), Section 11 (registration statement), Section 14(a) (proxy), Rule 14a-9 (proxy fraud) |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Active SCA | Any active case (CRITICAL RED FLAG -- triggers score ceiling) | No active cases | Clean 10-year history |
| Settlement history | Multiple settlements in 5 years | Single settlement >5 years ago | No settlement history |
| Lead counsel | Top-tier firm representing plaintiff | Mid-tier firm | Case dismissed at pleading stage |

---

## 6.2 SEC Enforcement

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **SEC enforcement actions** | SEC Enforcement Actions database (sec.gov/litigation/litreleases.htm), SEC AAER database (sec.gov/litigation/admin.shtml) | Any SEC actions against the company or its officers: cease-and-desist, civil injunctions, administrative proceedings |
| **Wells notices** | 10-K/10-Q risk factors or legal proceedings (companies sometimes disclose receipt of Wells notices) | Pending SEC investigation (80% of Wells notice recipients face charges) |
| **SEC penalties and disgorgement** | SEC enforcement database | Dollar amounts of fines and disgorgement |
| **Officer bars** | SEC AAER database | Whether any current or former officer was barred from serving as a D&O |
| **Consent decree terms** | SEC enforcement database | Requirements imposed on the company (enhanced reporting, independent monitor, etc.) |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| Active enforcement | Any pending SEC action (CRITICAL RED FLAG) | No active actions | Clean SEC history |
| Wells notice | Disclosed in recent filing | None disclosed | N/A |
| Officer bar | Any current or recent officer barred | No bars | N/A |

---

## 6.3 Derivative Suits

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Delaware Chancery Court filings** | Delaware Courts e-Filing system (courts.delaware.gov) or PACER | Active derivative suits against directors |
| **Other state court derivative suits** | PACER, state court records | Derivative suits in courts of other states |
| **Demand refusal letters** | 10-K Item 3 (Legal Proceedings) or 8-K | Whether the company has received and refused shareholder litigation demands |
| **Books and records demands (220)** | Delaware Chancery records | Section 220 demands often precede derivative suits |
| **Caremark/oversight claims** | Case-specific analysis | Breach of duty of oversight claims (rising success rate: ~30%) |

---

## 6.4 Regulatory Proceedings (Non-SEC)

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **DOJ investigations/actions** | DOJ press releases (justice.gov), 10-K Item 3 | Criminal or civil investigations by Department of Justice |
| **FCPA actions** | Stanford FCPA Clearinghouse (fcpa.stanford.edu), DOJ/SEC databases | Foreign Corrupt Practices Act investigations and resolutions |
| **FTC antitrust** | FTC enforcement database | Antitrust investigations or consent orders |
| **Industry-specific regulators** | FDA (fda.gov), EPA ECHO (echo.epa.gov), CFPB, OCC, state AGs | Regulatory actions from industry-specific agencies |
| **State AG actions** | State AG office websites (manual search) | Multi-state or single-state enforcement |
| **EEOC charges** | EEOC litigation database (eeoc.gov) | Employment discrimination enforcement actions |

---

## 6.5 M&A & Deal-Related Litigation

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Merger objection suits** | PACER, Stanford SCAC (M&A filter) | Suits challenging pending or completed mergers (historically filed in >80% of deals >$100M) |
| **Appraisal actions** | Delaware Chancery records | Shareholder petitions for fair value determination |
| **Disclosure-only settlements** | PACER, case records | Whether any prior M&A litigation settled for supplemental disclosures only (post-Trulia scrutiny) |
| **Deal litigation rate vs. peers** | Stanford SCAC filtered by peer companies | Whether this company faces more or less M&A litigation than peers |

---

## 6.6 Workforce & Employment Litigation

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **EEOC complaints and charges** | EEOC litigation database, 10-K Item 3 | Volume and type of discrimination charges |
| **Wage/hour class actions** | PACER, 10-K Item 3 | Pending or historical wage/hour class actions |
| **Whistleblower activity** | 10-K risk factors (keyword: "whistleblower"), SEC whistleblower reports (aggregate only -- individual tips are confidential) | Indicators of internal complaints |
| **WARN Act compliance** | State WARN Act notice databases (varies by state) | Recent layoff notifications |
| **Human capital disclosures** | 10-K Item 1 (mandated since 2020) | Quality and completeness of human capital disclosures (turnover, diversity, safety) |

---

## 6.7 Environmental & Product Liability

| Data Point | Source | Free? | What Is Measured |
|------------|--------|-------|-----------------|
| **EPA enforcement** | EPA ECHO database (echo.epa.gov) | Yes | Active enforcement actions, penalties, compliance status |
| **Superfund site involvement** | EPA CERCLIS database | Yes | Listed as a Potentially Responsible Party |
| **Product recalls** | CPSC (cpsc.gov), FDA (fda.gov/safety/recalls), NHTSA (nhtsa.gov) | Yes | Active product recalls |
| **Mass tort exposure** | 10-K Item 3, PACER | Mixed | Pending mass tort litigation (opioids, PFAS, talc, etc.) |
| **Cybersecurity incidents** | 8-K Item 1.05 (required since December 2023), state breach notification databases | Yes | Material cybersecurity incidents disclosed |
| **Climate litigation exposure** | Grantham Research Institute climate litigation database | Yes | Climate-related lawsuits or regulatory actions |

---

## 6.8 Peer Litigation Comparison

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Peer group SCA count (5 years)** | Stanford SCAC, searched for each peer company | Number of SCAs filed against each peer in the last 5 years |
| **Company SCA count vs. peer average** | Calculated | Whether this company has more, fewer, or average litigation vs. its peers |
| **Peer allegation type distribution** | Stanford SCAC | What types of claims dominate in the peer group (disclosure, guidance, product, governance, M&A) |
| **Industry litigation frequency rate** | Cornerstone Research annual filings data | This industry's filing rate vs. overall market rate |
| **Peer settlement amounts** | Cornerstone Research, Stanford SCAC | Settlement range for peer companies that were sued |

| Signal | Red Flag | Neutral | Positive |
|--------|----------|---------|----------|
| vs. peers | More litigation than peer average | In line with peers | Less litigation than peers |
| Industry trend | Industry filing rate increasing | Stable | Decreasing |

---

## 6.9 Allegation Theory Mapping

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **For each finding across all sections** | Derived from Sections 2-5 flagged items | Which of the 5 complaint theories each finding could support: **A** (Disclosure: material misstatement/omission), **B** (Guidance: earnings guidance miss or withdrawal), **C** (Product/Operations: operational failure causing stock drop), **D** (Governance: fiduciary breach, self-dealing, oversight failure), **E** (M&A: deal-related claims) |
| **Allegation theory distribution** | Aggregated counts | How many findings support each theory. A company with 12 Disclosure findings and 0 Governance findings has a different risk profile than one with 3 of each |
| **Primary exposure type** | Derived | The dominant allegation theory -- this tells the underwriter what kind of complaint is most likely |

---

## 6.10 Known Matters

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Pending litigation disclosed in 10-K/10-Q** | 10-K Item 3 (Legal Proceedings), 10-Q contingencies footnote | Specific pending matters that must be noted on the policy or excluded |
| **Contingent liabilities** | 10-K/10-Q financial statement footnotes: `us-gaap:LossContingencyAccrualAtCarryingValue` | Reserved amounts for pending litigation |
| **Insurance coverage for known matters** | Claims on existing Liberty policy (internal data -- not from public sources) | Whether any pending matter is already a claim on the D&O policy |

### 6.10.1 Forward-Looking Component for All of Section 6
- **Pending investigations**: SEC comment letters awaiting response, known DOJ/AG investigations not yet resolved
- **Regulatory pipeline**: Pending regulatory actions that could generate new liability (FDA decisions, antitrust reviews, environmental rulings)
- **Statute of limitations analysis**: For each potential claim theory, when the applicable statute expires
- **Emerging claim trends**: Whether the company's industry is experiencing new types of claims (AI washing, ESG, climate, DEI)
- **Trial dates and legal milestones**: Key upcoming court dates for any pending litigation

---

# SECTION 7: RISK SCORING & TOWER ANALYSIS

---

## 7.1 10-Factor Composite Score

Each factor is scored individually with defined maximum points, and the weighted total produces the quality score (100 minus total risk points).

### Factor F.1: Prior Litigation History (Max: 20 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Active SCA | 15 | Stanford SCAC | Any active securities class action |
| Active SEC action | 15 | SEC enforcement database | Any active SEC enforcement |
| Active DOJ investigation | 10 | DOJ press releases, 10-K | Any active criminal investigation |
| Prior SCA settled (5 years) | 5 per settlement (max 10) | Stanford SCAC | Number of settlements |
| Prior SEC enforcement (5 years) | 5 | SEC AAER | Any resolved enforcement action |
| Prior derivative suits (5 years) | 3 | PACER, Delaware Chancery | Any resolved derivative suits |
| Claims on existing D&O policy | 5 | Internal (Liberty) | Open claims on current policy |
| **Maximum for this factor** | **20** | | Capped at 20 regardless of accumulated sub-checks |

### Factor F.2: Stock Decline Severity (Max: 15 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Single-day drop >10% (company-specific) | 5 per event (max 10) | Yahoo Finance daily prices + sector ETF | Stock drop >10% with sector return >-3% on same day |
| Cumulative 5-day drop >20% | 5 | Calculated | |
| Trading below IPO price | 5 | IPO price from S-1 | If within 3 years of IPO |
| >50% decline from 52-week high | 5 | Yahoo Finance | |
| Peer underperformance >20% (1yr) | 3 | Calculated vs. sector ETF | |
| **Maximum for this factor** | **15** | | |

### Factor F.3: Restatement & Audit Issues (Max: 12 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Restatement in last 2 years | 10 | EDGAR 10-K/A, 10-Q/A, 8-K Item 4.02 | |
| Material weakness (unremediated) | 8 | 10-K ICFR assessment | |
| Material weakness (remediated) | 3 | 10-K ICFR assessment | |
| Auditor change (mid-year) | 5 | 8-K Item 4.01 | |
| Auditor change (year-end, Big4 to non-Big4) | 4 | 8-K Item 4.01 | |
| Going concern opinion | 10 | 10-K auditor report | |
| Late filing (NT form) | 6 | EDGAR NT 10-K/10-Q | |
| SEC comment letter (aggressive/unresolved) | 3 | EDGAR CORRESP | |
| **Maximum for this factor** | **12** | | |

### Factor F.4: Capital Markets & M&A Activity (Max: 10 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| IPO within 3 years | 5 | EDGAR S-1 effectiveness date | Section 11 window open |
| SPAC de-merger within 3 years | 8 | EDGAR S-4/proxy | |
| Major equity offering within 1 year | 3 | EDGAR 424B filings | Creates Section 11 exposure |
| Pending M&A (acquirer) | 3 | EDGAR 8-K Item 1.01 | Integration risk |
| Pending M&A (target) | 4 | EDGAR SC 14D-9, DEFM14A | Merger objection suit risk |
| Prior acquisition with goodwill impairment | 4 | 10-K goodwill footnote | |
| **Maximum for this factor** | **10** | | |

### Factor F.5: Guidance & Earnings Misses (Max: 10 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| 3+ guidance misses in 12 quarters | 5 | 8-K guidance vs. actual | |
| Guidance miss causing >10% stock drop | 5 | Cross-reference guidance misses with stock data | |
| Guidance withdrawal | 5 | 8-K | |
| Beat rate <50% | 3 | Calculated from 12-quarter history | |
| Aggressive guidance philosophy | 2 | Derived | Consistently guides high |
| **Maximum for this factor** | **10** | | |

### Factor F.6: Short Interest & Activist Short (Max: 8 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Short interest >10% of float | 3 | FINRA / Yahoo Finance | |
| Short interest >20% of float | 5 | Same | |
| Short interest trend up >50% in 6 months | 3 | FINRA historical | |
| Active short seller report published | 5 | Manual search | |
| **Maximum for this factor** | **8** | | |

### Factor F.7: Stock Volatility & Market Signals (Max: 9 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Beta >1.5 | 2 | Yahoo Finance | |
| Annualized volatility >50% | 3 | Calculated from daily returns | |
| Max drawdown >40% (1yr) | 3 | Calculated | |
| Analyst consensus >3.5 (sell territory) | 2 | Yahoo Finance | |
| Analyst estimate revisions negative >10% | 2 | Yahoo Finance | |
| **Maximum for this factor** | **9** | | |

### Factor F.8: Financial Distress (Max: 8 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Altman Z-Score <1.81 | 5 | Calculated from XBRL | |
| Beneish M-Score >-1.78 | 4 | Calculated from XBRL | |
| Net debt/EBITDA >5x | 3 | Calculated | |
| Interest coverage <2x | 3 | Calculated | |
| Negative FCF for 2+ years (non-growth) | 3 | Calculated | |
| OCF/NI ratio <0.5 | 3 | Calculated | |
| Credit rating below investment grade | 2 | 8-K, 10-K | |
| Debt maturity wall (>30% in 12 months) | 3 | 10-K debt footnote | |
| **Maximum for this factor** | **8** | | |

### Factor F.9: Governance Issues (Max: 6 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| Say-on-pay <70% support | 3 | DEF 14A, 8-K voting results | |
| Material related party transactions | 2 | DEF 14A | |
| Independence ratio <2/3 | 2 | DEF 14A | |
| Active activist campaign (13D) | 3 | EDGAR SC 13D | |
| Dual-class with >10:1 voting differential | 2 | DEF 14A, Articles | |
| CEO=Chair with no lead independent | 1 | DEF 14A | |
| No financial expert on audit committee | 2 | DEF 14A | |
| **Maximum for this factor** | **6** | | |

### Factor F.10: Officer Stability (Max: 2 points)

| Sub-check | Points | Data Source | Criteria |
|-----------|--------|-------------|----------|
| CFO departure in last 12 months | 2 | 8-K Item 5.02 | |
| CEO departure in last 12 months | 1 | 8-K Item 5.02 | |
| 3+ C-suite departures in 12 months | 2 | 8-K Item 5.02 | |
| CAO/Controller departure | 2 | 8-K Item 5.02 | |
| **Maximum for this factor** | **2** | | |

### Quality Score Calculation

```
Base Risk Points = SUM(F.1 through F.10), each capped at its max
Pattern Adjustments = +/- points from composite pattern detection (Section 7.2)
Final Risk Points = Base + Pattern Adjustments
Quality Score = 100 - Final Risk Points (floor of 0)
```

---

## 7.2 Composite Pattern Detection (17 Patterns)

Each pattern tests for a COMBINATION of factors that historically precede D&O claims. A pattern is more than the sum of its parts.

| Pattern ID | Pattern Name | What It Detects | Input Checks | Detection Criteria | Impact |
|------------|-------------|-----------------|--------------|-------------------|--------|
| P.01 | **EVENT_COLLAPSE** | Single catastrophic event | Stock drops >10%, triggering event identified | Single-day company-specific decline >10% with identifiable corporate disclosure trigger | +3 to +5 risk points |
| P.02 | **CASCADE** | Multi-week accelerating decline | 5-day, 20-day, 60-day returns all negative with acceleration | Each successive period shows worse performance | +3 to +5 |
| P.03 | **PEER_DIVERGENCE** | Company falling behind sector | 1yr return vs. sector ETF | Underperforming sector by >20% over 12 months | +2 to +4 |
| P.04 | **DEATH_SPIRAL** | Multiple distress signals converging | Z-Score, going concern, cash burn, stock decline, insider selling | 3+ distress indicators simultaneously flagged | +5 to +8 |
| P.05 | **SHORT_ATTACK** | Coordinated short campaign | Short interest spike, short seller report, stock decline | Short report published + >50% short interest increase + stock decline >20% | +4 to +6 |
| P.06 | **INFORMED_TRADING** | Insiders trading on MNPI | Insider sales, timing vs. announcements, 10b5-1 manipulation | Insider selling clusters within 30 days before major drop | +3 to +5 |
| P.07 | **SUSTAINABILITY_RISK** | Business model under threat | Revenue declining, margins contracting, competitive position weakening | 3+ consecutive quarters of revenue decline + margin contraction + peer outperformance | +2 to +4 |
| P.08 | **CONCENTRATION_COMPOSITE** | Multiple concentration risks | Customer, supplier, product, geographic concentration | 2+ concentration types flagged simultaneously | +2 to +3 |
| P.09 | **AI_WASHING_RISK** | Overstated AI capabilities | Revenue claims, product descriptions, keyword frequency in filings vs. actual AI revenue | Heavy AI marketing language + no disclosed AI-specific revenue segment + tech company classification | +2 to +4 |
| P.10 | **DISCLOSURE_QUALITY_RISK** | Below-standard disclosure | Non-GAAP gap, risk factor boilerplate, MD&A quality | Non-GAAP adjustments >100% of GAAP + vague risk factors + minimal forward-looking specificity | +2 to +3 |
| P.11 | **NARRATIVE_COHERENCE_RISK** | Management story contradicts actions | Strategy statements vs. financial results, insider transactions vs. public optimism | Publicly bullish guidance + insider selling + deteriorating fundamentals | +3 to +5 |
| P.12 | **CATALYST_RISK** | Near-term binary event pending | Upcoming FDA decision, trial verdict, regulatory ruling, M&A close | Binary event within 90 days with >25% potential stock impact | +2 to +4 |
| P.13 | **GUIDANCE_EROSION** | Deteriorating guidance reliability | Guidance track record, withdrawal history | 3+ misses in 8 quarters OR guidance withdrawal | +2 to +3 |
| P.14 | **LIQUIDITY_STRESS** | Cash/funding pressure | Cash burn, debt maturity, covenant proximity | <12 months cash runway OR covenant headroom <10% | +3 to +5 |
| P.15 | **EARNINGS_QUALITY_DETERIORATION** | Accounting quality declining | Accrual ratio trend, DSO trend, OCF/NI divergence | Accrual ratio increasing + DSO increasing + OCF/NI diverging, all for 2+ quarters | +3 to +5 |
| P.16 | **TURNOVER_STRESS** | Leadership instability | Officer departures, board changes | 3+ departures in 12 months OR CFO + 1 other C-suite within 6 months | +2 to +4 |
| P.17 | **PROXY_ADVISOR_RISK** | Governance deficiency flagged | Say-on-pay results, ISS/GL concerns | Say-on-pay <70% OR multiple adverse ISS/GL recommendations | +1 to +3 |

---

## 7.3 Critical Red Flag System (11 Absolute Gates)

If ANY Critical Red Flag is triggered, a hard score ceiling is imposed regardless of other factor scores. These are non-negotiable escalation triggers.

| CRF ID | Critical Red Flag | Ceiling Imposed | Data Source |
|--------|-------------------|-----------------|-------------|
| CRF-01 | Active Securities Class Action | Score ceiling: 30 (WALK minimum) | Stanford SCAC |
| CRF-02 | Active Wells Notice | Score ceiling: 25 | 10-K/10-Q disclosure |
| CRF-03 | Active DOJ Criminal Investigation | Score ceiling: 20 | DOJ press releases, 10-K |
| CRF-04 | Going Concern Opinion | Score ceiling: 20 | 10-K auditor report |
| CRF-05 | Restatement (last 12 months) | Score ceiling: 25 | EDGAR 10-K/A, 8-K Item 4.02 |
| CRF-06 | Material Weakness (unremediated) | Score ceiling: 35 | 10-K ICFR |
| CRF-07 | Auditor Resignation (vs. mutual termination) | Score ceiling: 30 | 8-K Item 4.01 |
| CRF-08 | Active Short Seller Report (prominent firm) | Score ceiling: 35 | Manual search |
| CRF-09 | Debt Default or Covenant Violation | Score ceiling: 20 | 8-K Item 2.04, 10-K |
| CRF-10 | Stock >70% Below IPO Price (within 3 years) | Score ceiling: 25 | EDGAR S-1 + Yahoo Finance |
| CRF-11 | Disclosed SEC/DOJ Subpoena | Score ceiling: 30 | 10-K/10-Q, 8-K |

---

## 7.4 Tier Classification

| Tier | Score Range | Meaning | Underwriting Action |
|------|-----------|---------|---------------------|
| **WIN** | 90-100 | Excellent risk. Pursue aggressively | Quote at or below market rates. Primary and low excess acceptable |
| **WANT** | 75-89 | Strong risk with minor concerns | Quote at market. Any layer position acceptable |
| **WRITE** | 60-74 | Acceptable risk with notable concerns | Quote at market to 1.3x. Prefer excess over primary |
| **WATCH** | 40-59 | Marginal risk requiring monitoring | Quote at 1.3-1.5x market. High excess only ($50M+ attachment) |
| **WALK** | 20-39 | Poor risk, consider declining | Quote at 2x+ market if at all. Ultra-high excess only |
| **NO TOUCH** | 0-19 or CRF ceiling < 20 | Unacceptable risk | Decline |

---

## 7.5 Tower Positioning & Severity Analysis

| Data Point | Source | What Is Measured |
|------------|--------|-----------------|
| **Expected settlement range (if sued)** | Inherent risk baseline (market cap x industry matrix from Section 1.4) adjusted by company-specific factors | 25th percentile, median, 75th percentile, and 95th percentile settlement estimates |
| **DDL scenario modeling** | Stock volatility x market cap | Estimated DDL for a hypothetical 10%, 20%, 30% stock drop |
| **Settlement as % of DDL** | Cornerstone Research empirical data: 7.3% median overall; 28.2% for DDL <$25M; declining percentage for larger DDL | Applied to DDL scenarios |
| **Attachment point analysis** | Settlement scenarios mapped against typical tower structures for this market cap tier | Which layers are "at risk" under median and adverse scenarios |
| **Defense cost estimate** | $5-15M for SCA through MTD, $15-30M through discovery, $30M+ through trial | Layer erosion from defense costs even in ultimately dismissed cases |
| **Typical program limit for market cap** | Industry benchmarking data | Expected total D&O program size |

### Tower Vulnerability Summary

| Scenario | Estimated Loss (Settlement + Defense) | Layers Affected |
|----------|--------------------------------------|-----------------|
| Favorable (25th pctl) | $X | Primary only |
| Median | $Y | Through Nth excess |
| Adverse (75th pctl) | $Z | Through Nth excess |
| Tail (95th pctl) | $W | Potential tower exhaustion |

---

## 7.6 Red Flag Summary

| Attribute | Detail |
|-----------|--------|
| **What is produced** | Consolidated list of EVERY flagged item across all sections, organized by severity (CRITICAL > HIGH > MODERATE > LOW), with: the finding, the data source citation, the scoring impact, the allegation theory mapping, and the recommended underwriting response |
| **Severity levels** | CRITICAL (score ceiling triggered or >5 risk points from single item), HIGH (3-5 risk points), MODERATE (1-2 risk points), LOW (watch item, 0 risk points but noted for monitoring) |
| **Evidence requirement** | Every red flag must cite a specific data source with date and filing reference. No unsourced flags permitted |
| **Forward-looking integration** | Each flag includes a "trajectory" indicator: WORSENING / STABLE / IMPROVING based on trend data |

---

# DATA SOURCE MASTER REFERENCE

## Free Public Sources

| Source | URL | Data Available | Update Cadence | API Available? |
|--------|-----|---------------|----------------|----------------|
| **SEC EDGAR** | sec.gov/cgi-bin/browse-edgar | All public filings (10-K, 10-Q, 8-K, DEF 14A, S-1, Form 4, etc.) | Real-time (filings posted within hours) | Yes: EDGAR full-text search API, XBRL Company Facts API, Filing History API |
| **SEC EDGAR XBRL Company Facts** | data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json | All XBRL-tagged financial data points | Quarterly | Yes: REST API, free, rate-limited to 10 req/sec |
| **SEC EDGAR Full-Text Search** | efts.sec.gov/LATEST/search-index | Search across all filing text | Real-time | Yes: REST API |
| **Stanford SCAC** | securities.stanford.edu | Securities class action filings, status, settlements | Monthly | No (web scraping or manual) |
| **Yahoo Finance** | finance.yahoo.com (various API endpoints) | Stock prices, fundamentals, analyst data, insider transactions, short interest | Real-time (prices), Daily (fundamentals) | Yes: unofficial API via Python libraries (yfinance) |
| **FINRA Short Interest** | finra.org/finra-data/browse-catalog/short-interest | Short interest by security | Bi-monthly | No (download) |
| **SEC Enforcement** | sec.gov/litigation | Enforcement actions, AAERs | As actions filed | No (scraping) |
| **PCAOB** | pcaobus.org | Audit firm inspection reports | Annual | No |
| **EPA ECHO** | echo.epa.gov | Environmental compliance/enforcement | Weekly | Yes: REST API |
| **FDA** | fda.gov | Drug approvals, recalls, warning letters | Real-time | Yes: openFDA API |
| **DOJ Press Releases** | justice.gov/news | Criminal/civil enforcement | Real-time | No |
| **OFAC SDN List** | treasury.gov/ofac | Sanctioned entities | Updated regularly | Yes: download |
| **Transparency International CPI** | transparency.org | Country corruption scores | Annual | Yes: download |
| **Cornerstone Research Reports** | cornerstone.com/insights | Annual filings/settlement reports | Annual/semi-annual | No (PDF download) |
| **NERA Reports** | nera.com/insights | Annual/semi-annual litigation trends | Semi-annual | No (PDF download) |

## Commercial / Paid Sources (NOT required but enhance analysis)

| Source | Data Available | Used For |
|--------|---------------|----------|
| **Audit Analytics** | Restatements, MW, auditor changes, comment letters | Enhanced audit risk indicators |
| **ISS / Glass Lewis** | Governance scores, proxy recommendations | Governance risk scoring |
| **Bloomberg / Refinitiv** | Financial data, estimates, transactions | Enhanced financial and analyst data |
| **PACER** | Federal court dockets | Litigation deep-dive ($0.10/page) |
| **BoardEx** | Director interlocks, career histories | Individual D&O risk profiles |
| **SharkRepellent / FactSet** | Governance provisions, activism | Anti-takeover and activism analysis |
| **Advisen** | Insurance claims data | Loss severity benchmarking |
| **WTW D&O Quantified** | Interactive risk benchmarking | Peer comparison and pricing |

---

# DATA FRESHNESS & CONFIDENCE INDICATORS

For every data point in the worksheet, the output must include:

| Attribute | Description |
|-----------|-------------|
| **As-of date** | The date of the most recent data underlying this data point (e.g., "10-K filed 2025-11-15 for FY ending 2025-09-30") |
| **Staleness flag** | CURRENT (<90 days old), AGING (90-180 days), STALE (>180 days). Stale data must be flagged with a warning |
| **Confidence level** | HIGH (audited financial data, court records), MEDIUM (unaudited 10-Q data, analyst estimates), LOW (derived calculations, estimated peer comparisons, news-based signals) |
| **Source citation** | Specific filing type, date, and URL/CIK reference |

---

# CROSS-SECTION INTERCONNECTION PATTERNS

The following cross-section combinations are specifically tested as interconnection risk:

| Pattern | Sections Involved | What It Signals | Historical Precedent |
|---------|------------------|-----------------|---------------------|
| Aggressive accounting + insider selling + auditor change | 3 (Financial) + 4 (Market) + 3 (Audit) | Very high restatement risk | Enron, WorldCom pattern |
| Revenue deceleration + guidance miss + stock drop + SCA filing | 3 + 4 + 4 + 6 | Active or imminent securities litigation | Most common SCA fact pattern |
| Executive departure + Wells notice + SEC comment letter escalation | 5 + 6 + 3 | Enforcement action approaching | Typical SEC enforcement timeline |
| M&A announcement + stock drop + merger objection suit | 2 + 4 + 6 | Deal-related litigation (near-certain for large deals) | >80% of deals >$100M attract litigation |
| Customer concentration + revenue miss + stock drop | 2 + 3 + 4 | Undisclosed customer loss | Classic Section 10(b) fact pattern |
| Activist 13D + proxy contest + executive turnover | 5 + 5 + 5 | Governance instability | Common activist campaign evolution |
| Goodwill impairment + acquisition history + margin decline | 3 + 2 + 3 | Failed acquisition thesis | "Buyer's remorse" SCA pattern |
| IPO <3yr + stock below IPO price + insider lockup expiring | 2 + 4 + 4 | High-probability Section 11 claim | IPO litigation window |

---

*Specification completed February 6, 2026*
*This document defines 200+ individual data points across 7 sections with specific sources, signal interpretation, and forward-looking components for each.*
