# Brain Section Questions — Review Draft v5.1

**Restructured:** 7+1 sections consolidated to 5 sections. FORWARD dissolved (content embedded by domain). DISCLOSURE merged into GOVERNANCE & DISCLOSURE. Sector Intelligence embedded into relevant sections. Peer comparison and sector calibration applied as cross-cutting principles.

**v5.1 updates:** Incorporated user research input from KPMG ICFR Handbook, OCC Corporate Governance Handbook, and 2025 Litigation Trends. New items marked 🔵 with source attribution. Refined items marked 🟠 with change rationale. Adds ~15 questions and refines ~6 existing ones. Also adds Underwriting Decision Logic gates and Policy Structure Assessment.

**Audit basis:** Every question verified against 388 current checks + 594 old system checks + 287 scoring rules (1,097 total). Check-by-check mapping tables in `/tmp/mapping_*.md`.

## Color Legend

| Color | Meaning |
|---|---|
| ⚪ | Keep as-is |
| 🔵 | ADD — proposed new question |
| 🟠 | CHANGE — consolidate or reword |
| 🔴 | REMOVE — low signal or wrong level |

Every 🔵/🟠/🔴 item includes a reason in *italics*. Items sourced from the old system's 594 checks note "Old system" in the rationale.

---

## Cross-Cutting Principles

**Peer Comparison** — Not a standalone section. Peer comparison is a METHOD applied within every section:
- COMPANY: peer competitive position, peer litigation frequency
- MARKET: peer-relative stock performance, peer valuation multiples
- FINANCIAL: peer-relative margins, leverage, sector-calibrated thresholds
- GOVERNANCE: peer-relative CEO pay, board structure
- LITIGATION: peer lawsuit frequency, sector allegation patterns

**Data Feasibility** — Every question must be answerable from SEC filings + web search + MCP tools (EdgarTools, Brave/Google Search, Playwright, Fetch). If we can't programmatically acquire the data, the question is aspirational, not operational. Flag questions where acquisition is uncertain.

**Sector Calibration** — Every threshold-based check must use sector-calibrated values, not universal cutoffs. The knowledge database stores per-sector thresholds for RED/YELLOW/CLEAR status. "Is leverage high?" means nothing without "...for this sector." See threshold tables in Section 3.8.

---

## Section Boundaries

| # | Section | Owns |
|---|---|---|
| 1 | **COMPANY** | Entity identity, business model, operations, structure, geography, M&A, competitive position, macro environment, employee signals, customer signals, risk calendar |
| 2 | **MARKET** | Stock price, volatility, trading patterns, short interest, ownership structure, analyst coverage, valuation |
| 3 | **FINANCIAL** | Liquidity, leverage, profitability, earnings quality, forensic analysis, distress indicators, guidance credibility, audit/accounting integrity, sector-specific KPIs |
| 4 | **GOVERNANCE & DISCLOSURE** | Board, executives, compensation, insider trading, shareholder rights, activist pressure, disclosure quality, narrative analysis, whistleblower signals, media/external narrative |
| 5 | **LITIGATION & REGULATORY** | Securities class actions, regulatory enforcement, derivative suits, non-securities litigation, defense posture, litigation patterns, sector-specific regulatory, runoff/tail coverage |

---

# 1. COMPANY

## 1.1 Identity
*What is this company?*

- 🟠 1.1.1 What industry is this company in? — *CHANGED: Capture SIC, NAICS, GICS codes and sector/industry classification. Base D&O exposure is computed in SCORING (inherent risk), not here — this question gathers the raw identity data.*
- 🟠 1.1.2 What are the key company metrics? — *CHANGED: Market cap, enterprise value, employee count, revenue, SIC/NAICS/GICS codes, sector, industry. Full identity profile upfront. Size-adjusted risk is a SCORING output.*
- ⚪ 1.1.3 What lifecycle stage is this company in (IPO, growth, mature, distressed, SPAC)?
- 🔵 1.1.4 What is the state of incorporation and what legal regime applies? — *Delaware vs Nevada vs other affects derivative suit standards, fiduciary duty scope.*
- 🔵 1.1.5 What exchange is it listed on and is it a Foreign Private Issuer? — *NYSE vs NASDAQ listing standards differ; FPI = no proxy statement, different disclosure regime.*

🔴 Removed: "Risk archetype" — *This is an output WE compute after analysis, not a question the underwriter asks. Move to SCORE stage output.*

## 1.2 Business Model & Revenue
*How does this company make money?*

- ⚪ 1.2.1 What is the company's primary business model and revenue type?
- ⚪ 1.2.2 How is revenue broken down by segment?
- ⚪ 1.2.3 What are the key products/services and how concentrated is the product portfolio?
- ⚪ 1.2.4 What is the cost structure and operating leverage?
- 🔵 1.2.5 What is the recurring vs non-recurring revenue mix? — *Recurring = predictable. Non-recurring = lumpier = harder to forecast = higher guidance miss risk.*
- 🟠 1.2.6 Is there an "Innovation/Investment Gap" — does the company's public AI/tech narrative diverge from actual R&D/CAPEX spend? — *CHANGED from generic "AI risk" to specific measurable signal. Compare frequency of "AI" mentions in 10-K/marketing vs capitalized software and R&D spend. High mismatch = "AI Washing" — primary driver of AI-related securities fraud in 2025. AI-related filings doubled in 2024, often driven by overstated capabilities. Old system tracked 7 AI hazard types. Source: 2025 Litigation Trends.*

🔴 Removed: "Pricing power" — *Interesting business analysis but doesn't predict D&O claims. Margin compression (FINANCIAL) captures the downstream effect.*

## 1.3 Operations & Dependencies
*What does this company depend on to operate?*

- ⚪ 1.3.1 How concentrated is the customer base?
- ⚪ 1.3.2 How dependent is the company on key suppliers or single-source inputs?
- ⚪ 1.3.3 How complex and vulnerable is the supply chain?
- ⚪ 1.3.4 What is the workforce profile and labor risk?
- ⚪ 1.3.5 What technology, IP, or regulatory dependencies exist?
- 🔵 1.3.6 What is the government contract exposure? — *>10% revenue from government = False Claims Act qui tam risk, procurement compliance requirements.*
- 🔵 1.3.7 What is the data/privacy risk profile? — *What kind of data: PII, PHI, financial, children's? Drives cyber-D&O crossover risk (13.6x SCA risk post-breach). What regulations: CCPA, GDPR, HIPAA?*
- 🔵 1.3.8 Does the company have sector-specific hazard exposure? — *Binary flags that trigger whole categories of risk. Each flag = entire risk profile activates:*
    - Opioid (pharma/distributors) — mass tort litigation category
    - PFAS/environmental contamination (chemicals/mfg) — next asbestos, multi-decade liability
    - Crypto/digital assets — regulatory status unresolved, SEC vs CFTC
    - Cannabis — federal illegality creates unique D&O gaps
    - China VIE structure — no actual equity ownership, PRC regulatory risk
    - AI/ML claims — EU AI Act, algorithmic bias, training data litigation
    - Nuclear/defense — Price-Anderson, ITAR, classified programs
    - Social media/content — Section 230 erosion, CSAM, teen mental health
- 🔵 1.3.9 Is there ESG/greenwashing risk? — *Gap between ESG marketing and actual practices. Internal climate reports not publicly disclosed (Exxon precedent). Board ESG oversight. One of fastest-growing litigation areas.*
- 🔴 ~~1.3.10 Risk officer reporting lines (CISO to Board vs General Counsel)~~ — *REMOVED: Requires internal org chart access. Sometimes partially discoverable from proxy (committee charters mention CISO reporting) but unreliable. ASPIRATIONAL.*

## 1.4 Corporate Structure & Complexity
*How is this company organized?*

- ⚪ 1.4.1 How many subsidiaries and legal entities exist?
- ⚪ 1.4.2 Are there VIEs, SPEs, or off-balance-sheet structures?
- ⚪ 1.4.3 Are there related-party transactions or intercompany complexity?

🔴 Removed: "Holding company / orphan entity risk" — *Very niche, rarely matters for D&O. Fold into 1.4.1 as sub-consideration.*

## 1.5 Geographic Footprint
*Where does this company operate and what jurisdictional risks exist?*

- ⚪ 1.5.1 Where does the company operate (countries/regions)?
- ⚪ 1.5.2 What jurisdiction-specific risks apply (FCPA, GDPR, sanctions, export controls)?

🔴 Removed: "Country risk profile" — *Too broad. 1.5.2 already covers actionable jurisdiction risks. CPI scores are nice-to-have, not D&O signals.*

## 1.6 M&A & Corporate Transactions
*What deal activity has there been and what's pending?*

- ⚪ 1.6.1 Are there pending M&A transactions?
- ⚪ 1.6.2 What is the 2-3 year acquisition history (deal sizes, rationale, integration)?
- ⚪ 1.6.3 How much goodwill has accumulated and is there impairment risk?
- ⚪ 1.6.4 What is the integration track record?
- ⚪ 1.6.5 Has there been deal-related litigation?
- 🔵 1.6.6 Have there been divestitures, spin-offs, or capital markets transactions? — *Secondary offerings and ATM programs create Section 11 liability windows. Spin-offs create stranded liability risk.*

## 1.7 Competitive Position & Industry Dynamics
*How is this company positioned within its industry? (Peer comparison applies here)*

- ⚪ 1.7.1 What is the company's market position and competitive moat?
- ⚪ 1.7.2 Who are the direct peers and how do they compare?
- ⚪ 1.7.3 What is the peer litigation frequency (SCA contagion risk)?
- ⚪ 1.7.4 What are the industry headwinds and tailwinds?

🔴 Removed: "Barriers to entry" — *MBA-level analysis. Moat (1.7.1) and headwinds (1.7.4) already cover this. Too indirect a D&O signal.*

## 1.8 Macro & Industry Environment
*What external forces are creating risk? (Was Section 7.4)*

- ⚪ 1.8.1 How is the sector performing overall and are peers experiencing similar issues?
- ⚪ 1.8.2 Is the industry consolidating or facing disruptive technology threats?
- ⚪ 1.8.3 What macro factors materially affect this company (rates, FX, commodities, trade, labor)?
- ⚪ 1.8.4 Are there regulatory, legislative, or geopolitical changes creating sector risk?

## 1.9 Employee & Workforce Signals
*What are employees telling us about the company's health? (Was Section 7.2)*

- ⚪ 1.9.1 What do employee review platforms indicate (Glassdoor, Indeed, Blind)?
- ⚪ 1.9.2 Are there unusual hiring patterns (compliance/legal hiring surge)?
- ⚪ 1.9.3 Are there LinkedIn headcount or departure trends?
- ⚪ 1.9.4 Are there WARN Act or mass layoff signals?
- 🔵 1.9.5 What do department-level departures show? — *Accounting/legal departures = much stronger fraud signal than sales/marketing attrition. HBS research validates.*
- 🔵 1.9.6 What is the CEO approval rating trend? — *Glassdoor CEO approval drop >20% = red flag. Distinct from overall company rating.*

## 1.10 Customer & Product Signals
*What are customers and the market experiencing? (Was Section 7.3)*

- ⚪ 1.10.1 Are there customer complaint trends (CFPB, app ratings, Trustpilot)?
- ⚪ 1.10.2 Are there product quality signals (FDA MedWatch, NHTSA complaints)?
- ⚪ 1.10.3 Are there customer churn or partner instability signals?
- ⚪ 1.10.4 Are there vendor payment or supply chain stress signals?
- 🔵 1.10.5 What do web traffic and app download trends show? — *For consumer-facing companies, declining engagement precedes revenue decline.*
- 🔵 1.10.6 What does scientific/academic community monitoring reveal? — *For life sciences: PubPeer, Retraction Watch, KOL sentiment, clinical data integrity, FDA citizen petitions. Old system: F.4 (10 checks). SAVA case: PubPeer predicted collapse 3+ YEARS before SEC action. Single most valuable early warning for biotech/pharma. We have ZERO coverage.*

## 1.11 Risk Calendar & Upcoming Catalysts
*What events are coming in the next policy year? (Was Section 7.1 — temporal cross-reference across all domains)*

- ⚪ 1.11.1 When is the next earnings report and what's the miss risk?
- ⚪ 1.11.2 Are there pending regulatory decisions (FDA, FCC, etc.)?
- ⚪ 1.11.3 Are there M&A closings or shareholder votes?
- ⚪ 1.11.4 Are there debt maturities or covenant tests in the next 12 months?
- ⚪ 1.11.5 Are there lockup expirations or warrant expiry?
- ⚪ 1.11.6 Are there contract renewals or customer retention milestones?
- ⚪ 1.11.7 Are there litigation milestones (trial dates, settlement deadlines)?
- ⚪ 1.11.8 Are there industry-specific catalysts (PDUFA dates, patent cliffs)?

---

# 2. MARKET

## 2.1 Stock Price Performance
*How has the stock performed? (Peer comparison applies here)*

- ⚪ 2.1.1 What's the stock's current position relative to its 52-week range?
- 🟠 2.1.2 What is the stock's volatility profile and how does it compare to sector/peers? — *CHANGED: Focus on overall volatility characterization — is this a calm or wild stock? Beta, 90-day vol, vol vs peers. Moved from 2.3 for better flow.*
- ⚪ 2.1.3 How does performance compare to the sector and peers?
- ⚪ 2.1.4 Is there delisting risk?
- 🔵 2.1.5 Does the MD&A exhibit "Abnormal Positive Tone" relative to quantitative financial reality? — *Divergence between management's narrative tone and the numbers is a statistically validated predictor of future litigation and stock drops. Research shows companies with D&O insurance engage in higher tone manipulation. Cross-reference: 4.8.2 (tone shift) covers the disclosure angle; this question covers the MARKET SIGNAL angle — tone mismatch as a leading indicator of corrective disclosure events. Source: 2025 Litigation Trends.*

## 2.2 Stock Drop Events
*Have there been significant drops that could trigger litigation?*

- 🟠 2.2.1 Have there been single-day drops ≥5% in the past 18 months? — *CHANGED: Lowered threshold from 8% to 5% for earlier signal detection. Extended window from 12 to 18 months to cover full policy period context.*
- 🟠 2.2.2 Have there been multi-day decline events ≥10%? — *CHANGED: Lowered threshold from 15% to 10%. A 10% multi-day drop is already a significant event for D&O.*
- 🟠 2.2.3 Were significant drops preceded by "Corrective Disclosures" (restatements, guidance withdrawals, auditor changes) that establish loss causation? — *CHANGED from generic "what triggered it" to specifically identify corrective disclosures. Plaintiffs must prove a corrective disclosure caused the loss ("Loss Causation"). Identifying specific disclosure-to-drop temporal correlations directly maps to damages calculation. Source: 2025 Litigation Trends.*
- 🟠 2.2.4 Has the stock recovered from significant drops, or is there a sustained unrecovered decline in the past 18 months? — *CHANGED: An unrecovered drop = ongoing class period exposure. Recovery pattern matters for damages calculation and whether claims window is still open.*

## 2.3 Volatility & Trading Patterns
*What does trading behavior signal? (Peer comparison: volatility vs sector)*

- ⚪ 2.3.1 What's the 90-day volatility and how does it compare to peers?
- ⚪ 2.3.2 What's the beta?
- ⚪ 2.3.3 Is there adequate trading liquidity?
- ⚪ 2.3.4 Are there unusual volume or options patterns?

## 2.4 Short Interest & Bearish Signals
*Are sophisticated investors betting against this company?*

- 🟠 2.4.1 What's the short interest as % of float and what's the trend over the past 6-12 months? — *CHANGED: Level alone is insufficient — the trajectory matters. Rising short interest = growing bearish conviction.*
- ⚪ 2.4.2 Have there been activist short seller reports?

## 2.5 Ownership Structure
*Who owns the stock?*

- ⚪ 2.5.1 What's the institutional vs insider vs retail ownership breakdown?
- ⚪ 2.5.2 Who are the largest holders and what's the concentration?
- 🟠 2.5.3 What are the institutional ownership trends over the past 6-12 months? — *CHANGED: Not just "is it declining" but the full trend. Are institutions accumulating or exiting? Pace of change matters as much as direction.*
- 🔵 2.5.4 Are there capital markets transactions creating liability windows? — *Secondary offerings, ATM programs, convertible issuance = Section 11 exposure. PE/VC overhang = selling pressure.*

## 2.6 Analyst Coverage & Sentiment
*What do professional analysts think? (Peer comparison: coverage level vs sector)*

- ⚪ 2.6.1 How many analysts cover this stock?
- ⚪ 2.6.2 What's the consensus rating and recent changes?
- ⚪ 2.6.3 What's the price target relative to current price?

## 2.7 Valuation Metrics
*Is the stock priced appropriately? (Peer comparison: valuation vs peers is the entire point)*

- ⚪ 2.7.1 What are the key valuation ratios (P/E, EV/EBITDA, PEG)?
- ⚪ 2.7.2 How does valuation compare to peers?

## 2.8 Insider Trading Activity *(moved from Section 4 — market signal data)*
*Are insiders buying or selling, and is the timing suspicious?*

- ⚪ 2.8.1 What's the net insider trading direction?
- ⚪ 2.8.2 Are CEO/CFO selling significant holdings?
- ⚪ 2.8.3 What percentage of transactions use 10b5-1 plans?
- ⚪ 2.8.4 Is there cluster selling (multiple insiders simultaneously)?
- ⚪ 2.8.5 Is insider trading timing suspicious relative to material events?
- 🔵 2.8.6 Do executives pledge company shares as loan collateral? — *Share pledging = forced selling risk if stock declines. CEO pledging >50% + margin call = catastrophic selling.*
- 🔵 2.8.7 Are there Form 4 compliance issues? — *Late Section 16 filings = compliance breakdown. Gift transactions timed before declines = tax-motivated selling disguised as philanthropy.*

---

# 3. FINANCIAL

## 3.1 Liquidity & Solvency
*Can the company meet its near-term obligations? (Sector-calibrated thresholds apply)*

- ⚪ 3.1.1 Does the company have adequate liquidity (current ratio, quick ratio, cash ratio)?
- ⚪ 3.1.2 What is the cash runway — how many months before cash runs out?
- ⚪ 3.1.3 Is there a going concern opinion from the auditor?
- ⚪ 3.1.4 How has working capital trended over the past 3 years?

## 3.2 Leverage & Debt Structure
*How much debt does the company carry, and can they service it? (Sector-calibrated thresholds apply)*

- ⚪ 3.2.1 How leveraged is the company relative to earnings capacity (D/E, Debt/EBITDA)?
- ⚪ 3.2.2 Can the company service its debt (interest coverage)?
- ⚪ 3.2.3 When does significant debt mature and is refinancing at risk?
- ⚪ 3.2.4 Are there covenant compliance risks?
- ⚪ 3.2.5 What is the credit rating and recent trajectory?
- 🔵 3.2.6 What off-balance-sheet obligations exist (operating leases, purchase commitments, guarantees)? — *Real leverage not on the balance sheet. Can be material — Enron's OBS entities were the whole story.*

## 3.3 Profitability & Growth
*Is the business economically viable and growing? (Peer comparison applies here)*

- ⚪ 3.3.1 Is revenue growing or decelerating?
- ⚪ 3.3.2 Are margins expanding, stable, or compressing?
- ⚪ 3.3.3 Is the company profitable? What's the trajectory?
- ⚪ 3.3.4 How does cash flow quality compare to reported earnings?
- ⚪ 3.3.5 Are there segment-level divergences hiding overall trends?
- 🔵 3.3.6 What is the free cash flow generation and CapEx trend? — *FCF is the real measure of earnings power. Oracle CapEx/OCF ratio of 571% was the old system's smoking gun.*

## 3.4 Earnings Quality & Forensic Analysis
*Are the financial statements trustworthy, or is there manipulation?*

- ⚪ 3.4.1 Is there evidence of earnings manipulation (Beneish M-Score, Dechow F-Score)?
- ⚪ 3.4.2 Are accruals abnormally high relative to cash flows?
- ⚪ 3.4.3 Is revenue quality deteriorating (DSO expansion, Q4 concentration, deferred revenue)?
- ⚪ 3.4.4 Is there a growing gap between GAAP and non-GAAP earnings?
- ⚪ 3.4.5 What does the Financial Integrity Score composite indicate?
- 🔵 3.4.6 Are there specific revenue manipulation patterns? — *Old system had 8 named patterns: bill-and-hold, channel stuffing, side letters, round-tripping, percentage-of-completion manipulation, cookie jar reserves, big bath charges, Q4 concentration. Revenue fraud is #1 type of financial statement fraud. Naming patterns enables targeted detection.*
- 🔵 3.4.7 Is the Depreciation Index (DEPI) anomalous — is the depreciation rate slowing materially without a disclosed change in asset mix? — *Classic earnings management technique to artificially boost short-term profit by extending useful life of assets. DEPI ratio > 1 means depreciation is slowing relative to gross PPE. Often cited in securities fraud complaints. Beneish M-Score includes DEPI as a component, but calling it out separately enables targeted detection of this specific manipulation technique. Source: KPMG ICFR Handbook.*

## 3.5 Accounting Integrity & Audit Risk
*Is the financial reporting reliable? (Peer comparison: auditor quality vs peers)*

- ⚪ 3.5.1 Who is the auditor and what's their tenure and opinion?
- ⚪ 3.5.2 Has there been a restatement, material weakness, or significant deficiency?
- ⚪ 3.5.3 Has there been an auditor change, and why?
- ⚪ 3.5.4 Are there SEC comment letters raising accounting questions?
- ⚪ 3.5.5 What are the critical audit matters (CAMs)?
- 🔵 3.5.6 What is the non-audit fee ratio? — *Non-audit fees > audit fees = auditor independence compromised. SEC has flagged this as a risk factor.*
- 🔵 3.5.7 Are there PCAOB inspection findings for this auditor? — *PCAOB deficiencies at the firm = lower audit quality across all clients.*
- 🔴 ~~3.5.8 Management Review Controls precision~~ — *REMOVED: Requires access to internal ICFR documentation and audit workpapers. Not discoverable from public filings. Material weakness disclosures (3.5.2) are the public signal of ICFR failures. ASPIRATIONAL — revisit if we get audit report access.*
- 🔴 ~~3.5.9 Management override of manual journal entries~~ — *REMOVED: Internal control detail not available from public data. If material, it surfaces as a material weakness (3.5.2) or restatement. ASPIRATIONAL.*

## 3.6 Financial Distress Indicators
*How close is this company to failure?*

- 🟠 3.6.1 What does the Altman Z-Score indicate — and if Z-Score < 1.8 in a high-risk sector (Retail, CRE), does this trigger mandatory Side A policy structure review? — *CHANGED from informational to "knock-out" variable. Insolvency strips away corporate indemnification, exposing the insurer to 100% of Side A losses. Mega bankruptcies surged in H1 2025. Z-Score < 1.8 should automatically trigger review of bankruptcy waiver, Side A adequacy, and priority of payments clause. Source: 2025 Litigation Trends.*
- ⚪ 3.6.2 What does the Ohlson O-Score (bankruptcy probability) show?
- ⚪ 3.6.3 What does the Piotroski F-Score (fundamental quality) show?
- 🟠 3.6.4 Is the company in or approaching the "Zone of Insolvency" — and if yes, are Side A limits "bankruptcy remote"? — *CHANGED to add policy structure consequence. In the zone of insolvency, fiduciary duties may shift to creditors (jurisdiction-dependent), and corporate indemnification vanishes. Must verify Side A structure: dedicated limits, non-rescindable policy, automatic stay waiver, priority of payments to individuals over entity. Source: 2025 Litigation Trends.*
- 🔵 3.6.5 What do credit market signals show? — *CDS spreads, default probability pricing. Old system's CoreWeave case: default insurance at 7.9% = market pricing serious risk before equity reacted. Also: credit rating downgrades to junk in past 12mo.*
- 🔵 3.6.6 Is there active restructuring (debt renegotiation, operational restructuring, workforce reduction)? — *Concrete, observable distress signal between quantitative models (Z/O/F scores) and zone of insolvency. Old system A.6.3: restructuring is the middle ground our framework jumped over.*

## 3.7 Guidance & Market Expectations
*Is management credible in their forward communications?*

- ⚪ 3.7.1 Does the company provide earnings guidance and what's the current outlook?
- ⚪ 3.7.2 What's the guidance track record (beat/miss pattern)?
- ⚪ 3.7.3 What's the guidance philosophy (conservative vs aggressive)?
- ⚪ 3.7.4 How does analyst consensus align with company guidance?
- ⚪ 3.7.5 How does the market react to earnings?

## 3.8 Sector-Specific Financial Metrics
*Which industry-specific financial metrics apply? (Was Sections 2.8 + 8.1 + 8.2)*

🔵 Single conditional question replacing two generic questions:

- 🔵 3.8.1 What are the applicable sector-specific KPIs and how do they compare to benchmarks?

| Sector | Key KPIs | Why They Matter for D&O |
|---|---|---|
| **SaaS/Cloud** | NRR, ARR growth, Rule of 40, logo churn, CAC payback, gross margin | Subscription economics reveal whether growth is durable or a guidance miss is coming |
| **Biotech/Pharma** | Pipeline stage mix, cash per remaining trial, probability-adjusted NPV, patent cliff | Binary outcomes (FDA approval/rejection) create massive stock drops; cash runway is existential |
| **Banking** | NIM, NPL ratio, CET1 capital, loan-to-deposit, provision coverage, net charge-offs | Banking failures cascade; capital adequacy and loan quality are the core D&O signals |
| **Insurance** | Combined ratio, reserve development, investment yield, premium growth, loss ratio | Reserve deficiency is the #1 insurance D&O allegation; combined ratio >100 = operating loss |
| **REIT** | FFO/AFFO, NAV discount, occupancy rate, lease expiry profile, tenant quality | REITs are valued on cash flow (FFO), not earnings; occupancy decline = dividend cut = SCA |
| **Energy** | Reserve replacement ratio, finding costs, decline rate, breakeven price, ESG transition | Reserve write-downs and breakeven changes create immediate stock impact |
| **Retail** | Same-store sales, inventory turns, e-commerce mix, store count trajectory, shrinkage | Same-store sales decline = core business deteriorating; inventory buildup = markdown risk |
| **Mining/Materials** | Reserve grade, all-in sustaining cost, commodity price sensitivity, reclamation liability | Commodity cycle + reserve impairment + environmental liability = compound D&O exposure |
| **Telecom/Media** | ARPU, subscriber churn, content spend efficiency, spectrum value, cord-cutting rate | Subscriber metrics are the KPIs management guides on; misses trigger SCAs |
| **Automotive** | Vehicle deliveries, ASP trends, warranty reserves, EV transition metrics, recall frequency | Delivery guidance miss is the primary SCA trigger; safety recalls create product liability |
| **Fintech/Payments** | TPV growth, take rate, merchant churn, regulatory compliance spend, fraud rate | Rapid growth masking unit economics; regulatory risk from state-by-state licensing |
| **Healthcare Services** | Revenue per admission, payor mix, reimbursement rate changes, occupancy, staffing ratios | CMS rate changes can crater margins overnight; staffing shortages drive Caremark claims |
| **Construction/Engineering** | Backlog, book-to-bill, percentage-of-completion, change order rate, bonding capacity | POC revenue recognition is the #1 construction fraud pattern; backlog quality matters |

*(Sector-conditional — only applicable metrics evaluate)*

**Sector-Calibrated Thresholds** — Every threshold-based check above should use sector-specific RED/YELLOW/CLEAR values, not universal cutoffs:

| Metric | Tech/SaaS | Banking | Energy | Retail | Biotech | REIT |
|---|---|---|---|---|---|---|
| Debt/EBITDA RED | >3x | >8x | >4x | >4x | N/A | >7x |
| Current Ratio RED | <1.0 | N/A | <1.0 | <0.8 | <1.0 | N/A |
| Interest Coverage RED | <3x | <1.5x | <2x | <2x | N/A | <1.5x |
| Short Interest RED | >15% | >10% | >12% | >15% | >20% | >10% |
| Stock Decline 6mo RED | >40% | >30% | >35% | >40% | >50% | >30% |
| Cash Runway RED | <18mo | N/A | <12mo | <12mo | <18mo | N/A |
| Margin Compression RED | >500bps | >50bps NIM | >1000bps | >300bps | N/A | N/A |

---

# 4. GOVERNANCE & DISCLOSURE

## 4.1 Board Composition & Quality
*Is the board structured to provide effective oversight?*

- ⚪ 4.1.1 How independent is the board?
- ⚪ 4.1.2 Is the CEO also the board chair?
- 🟠 4.1.3 What's the board size and tenure distribution? — *CHANGED: Removed diversity as standalone metric. Diversity matters only if it ties to operational/oversight risk. Experience and independence are the priority.*
- 🟠 4.1.4 Do board members have relevant, demonstrated experience to oversee THIS company's industry and risks? — *CHANGED from "overboarded" check. Core question: is this board qualified? Sector expertise, financial literacy, risk-relevant backgrounds. Overboarding is a sub-signal, not the main question.*
- ⚪ 4.1.5 Is this a classified (staggered) board?
- ⚪ 4.1.6 How engaged is the board (meeting frequency, attendance)?
- 🔵 4.1.7 What is the board committee structure? — *Audit committee financial expert, comp committee independence, risk committee existence. Caremark claims hinge on committee adequacy.*
- 🔵 4.1.8 Is the Board Chair the immediate past CEO ("Successor Chair")? — *Successor CEOs retain shadow influence, creating "murky leadership" and "camouflage effects" that compromise board independence and monitoring capacity. If yes, is there a robust Lead Independent Director to counterbalance? Companies with successor chairs often lack effective independent oversight, making it harder to defend Caremark claims. Source: OCC Corporate Governance Handbook.*
- 🔴 ~~4.1.9 Board documented protocol for "Mission Critical" risk compliance~~ — *REMOVED: Requires access to board minutes and internal compliance documentation. Not discoverable from public filings. Proxy statement committee descriptions give a partial signal (folded into 4.1.7 committee structure). ASPIRATIONAL.*

## 4.2 Executive Team & Stability
*Are the right leaders in place, and is the team stable?*

- 🟠 4.2.1 Do the CEO and key executives have relevant, demonstrated experience to run THIS company? — *CHANGED: Not just "who is the CEO" but do they have the right background for this industry, this scale, this risk profile? A tech CEO running a pharma company = governance risk.*
- 🟠 4.2.2 Have any executives or directors been sued, investigated, or subject to enforcement actions in prior roles at other companies? — *CHANGED: Expanded from just "current company" litigation to full personal litigation history across all prior capacities. Prior lawsuit history is a leading indicator.*
- 🔵 4.2.3 Are there negative personal publicity signals for executives or directors? — *NEW: Public scandals, high-profile personal issues, reputational red flags. These create governance instability and can trigger shareholder activism or board pressure.*
- 🟠 4.2.4 What is the C-suite turnover trend and are there signs of management instability? — *CHANGED: Not just "recent turnover" but the TREND. Rising departures = instability signal. Unplanned exits, short tenures, interim appointments.*
- ⚪ 4.2.5 Is there a succession plan for key roles?
- ⚪ 4.2.6 Is there founder/key-person concentration risk?
- 🔴 ~~4.2.7 Officer oversight protocols (McDonald's Check)~~ — *REMOVED: Requires access to internal officer reporting protocols. Not discoverable from public filings. The McDonald's ruling is important context for SCORING (Caremark risk amplifier when officer turnover is high), but we can't check internal documentation. ASPIRATIONAL.*

## 4.3 Compensation & Alignment
*Is management incentivized to act in shareholders' interests? (Peer comparison: pay vs peers)*

- ⚪ 4.3.1 What's the CEO's total compensation and how does it compare to peers?
- ⚪ 4.3.2 What's the compensation structure (salary vs bonus vs equity)?
- ⚪ 4.3.3 What was the say-on-pay vote result?
- ⚪ 4.3.4 Are performance metrics in incentive comp appropriate?
- ⚪ 4.3.5 Are there clawback policies and what's their scope?
- ⚪ 4.3.6 Are there related-party transactions or excessive perquisites?
- ⚪ 4.3.7 What's the golden parachute/change-in-control exposure?
- 🔵 4.3.8 What are the executive stock ownership requirements? — *No ownership requirement = no skin in the game. Holding periods = alignment signal.*
- 🔵 4.3.9 What is the CEO pay ratio to median employee? — *>500:1 = political/reputational risk.*
- 🔵 4.3.10 Are there compensation manipulation indicators? — *Old system tracked: option spring-loading (grants before positive news), backdating, excise tax gross-ups (company pays exec taxes), change-in-control single vs double triggers. Specific red flags beyond general comp structure.*

🟠 **4.4 Insider Trading Activity — MOVED to Section 2 (MARKET) as subsection 2.8.** *Insider trading is market signal data, not governance. Renumbered there.*

## 4.4 Shareholder Rights & Protections
*How well are shareholder rights protected?*

- ⚪ 4.5.1 Does the company have a dual-class voting structure?
- ⚪ 4.5.2 Are there anti-takeover provisions (poison pill, supermajority requirements)?
- ⚪ 4.5.3 Is there proxy access for shareholder nominations?
- ⚪ 4.5.4 What forum selection and fee-shifting provisions exist?
- 🔵 4.5.5 Have there been recent bylaw amendments? — *Companies quietly add anti-shareholder provisions. Charter/bylaw changes removing rights = derivative suit trigger.*

## 4.6 Activist Pressure
*Is there activist investor activity creating governance instability?*

- ⚪ 4.6.1 Are there Schedule 13D filings indicating activist intent?
- ⚪ 4.6.2 Have there been proxy contests or board seat demands?
- ⚪ 4.6.3 Are there shareholder proposals with significant support?
- ⚪ 4.6.4 Is there a short activism campaign targeting governance?

🟠 **Check consolidation note:** 14 GOV.ACTIVIST.* checks all map to `activist_present` boolean. Should consolidate to ~4-5 checks matching these questions.

## 4.7 Disclosure Quality & Filing Mechanics
*Is the company meeting its disclosure obligations? (Was Section 6.1 + 6.4)*

- ⚪ 4.7.1 How have risk factors changed year-over-year?
- ⚪ 4.7.2 Have new litigation-specific or regulatory risk factors appeared?
- ⚪ 4.7.3 Have previously disclosed risks materialized?
- ⚪ 4.7.4 Has the company filed on time (NT filings, date shifts)?
- ⚪ 4.7.5 Is non-GAAP reconciliation adequate?
- ⚪ 4.7.6 Is segment reporting consistent?
- ⚪ 4.7.7 Is related-party disclosure complete?
- ⚪ 4.7.8 Is the guidance methodology transparent?
- 🔵 4.7.9 Are 8-K event disclosures timely and complete? — *Item 1.05 cyber (4-day rule), Item 4.01 auditor change, Item 5.02 exec departure. Late/missing 8-K = disclosure failure.*
- 🔴 ~~4.7.10 D&O questionnaires updated off-cycle~~ — *REMOVED: Requires access to the insurer's own questionnaire process. Not discoverable from public data. This is an underwriting process recommendation, not an analysis question. ASPIRATIONAL.*

## 4.8 Narrative Analysis & Tone
*What does the language reveal about management's confidence? (Was Section 6.2 + 6.3 + 6.6)*

- ⚪ 4.8.1 Has the MD&A readability changed (Fog Index)?
- ⚪ 4.8.2 Has the negative tone shifted?
- ⚪ 4.8.3 Is there increased hedging/qualifying language?
- ⚪ 4.8.4 Are forward-looking statements decreasing?
- ⚪ 4.8.5 Is the 10-K narrative consistent with earnings call messaging?
- ⚪ 4.8.6 Is the investor-facing narrative consistent with SEC filings?
- ⚪ 4.8.7 Is there analyst skepticism about management's story?
- ⚪ 4.8.8 Are there short thesis narratives contradicting management?
- ⚪ 4.8.9 What do auditor CAMs focus on, and has focus changed?
- 🔵 4.8.10 Are there red-flag phrases appearing for the first time in filings? — *"Investigation", "subpoena", "material uncertainty", "management override of controls" — first-time appearance is a leading indicator.*
- 🔵 4.8.11 Are risk factors boilerplate or company-specific? — *Generic copy-paste = not thinking about risks. Company-specific = genuine disclosure. Detectable via peer comparison.*
- 🔵 4.8.12 What does earnings call Q&A analysis reveal? — *Evasion patterns, prepared vs spontaneous tone divergence, deflection on specific topics, "non-answers."*
- 🔵 4.8.13 What does the full 10-K year-over-year diff show? — *Not just risk factor count — what sections changed substantively, what was removed, what new language appeared.*
- 🔵 4.8.14 How does this company's disclosure compare to peer filings? — *If every peer discloses a risk but this one doesn't = disclosure gap.*
- 🔵 4.8.15 What is the management credibility score? — *Cross-reference what management SAID vs what HAPPENED. Promised milestones vs delivery. Forward statement fulfillment rate.*

## 4.9 Whistleblower & Investigation Signals
*Are there signals of internal problems? (Was Section 6.5)*

- ⚪ 4.9.1 Is there whistleblower/qui tam language in filings?
- ⚪ 4.9.2 Is there internal investigation language?
- 🟠 4.9.3 Are there signals of internal problems from public sources? — *CHANGED: Narrowed to automatable signals only. Special committee formation (8-K/proxy), board-directed investigations (disclosure language), unusual legal/compliance hiring spikes (LinkedIn). Internal hotline data is not public.*
- 🔴 ~~4.9.4 Audit Committee whistleblower hotline review~~ — *REMOVED: Requires access to internal Audit Committee processes. Not discoverable from public filings. Whistleblower/qui tam language in filings (4.9.1) is the automatable proxy. ASPIRATIONAL.*

## 4.10 Media & External Narrative
*What are external observers seeing? (Was Section 7.5)*

- ⚪ 4.10.1 What does social media sentiment indicate?
- ⚪ 4.10.2 Is there investigative journalism activity?

---

# 5. LITIGATION & REGULATORY

## 5.1 Securities Class Actions (Active)
*Are there current SCAs, and how serious are they?*

- ⚪ 5.1.1 Are there active securities class actions against this company?
- ⚪ 5.1.2 What are the class periods, allegations, and case stage?
- ⚪ 5.1.3 Who is lead counsel and what tier are they?
- ⚪ 5.1.4 What is the estimated exposure (DDL and settlement range)?

## 5.2 Securities Class Action History
*What does the litigation track record tell us?*

- ⚪ 5.2.1 How many prior SCAs has this company had?
- ⚪ 5.2.2 What were the outcomes (dismissed, settled, amount)?
- ⚪ 5.2.3 Is there a recidivist pattern (repeat filer)?
- ⚪ 5.2.4 Are there pre-filing signals (law firm announcements, investigations)?

## 5.3 Derivative & Merger Litigation
*Are there non-SCA shareholder claims?*

- ⚪ 5.3.1 Are there active derivative suits (Caremark, duty of loyalty)?
- ⚪ 5.3.2 Are there merger objection lawsuits?
- 🟠 5.3.3 Has the company received any Section 220 (Books & Records) demands in the last 24 months? — *CHANGED to add timeframe and elevate as pre-claim indicator. Section 220 demands are the single strongest leading indicator of a future derivative suit — they are the "smoke" before the fire. If 220 demands exist, the claim is already incubating. Source: 2025 Litigation Trends.*
- 🔵 5.3.4 Are there ERISA class actions (401k stock drop cases)? — *Different legal theory (fiduciary breach under ERISA), different plaintiffs (employees), often filed alongside SCAs but separate exposure.*
- 🔵 5.3.5 Are there appraisal actions? — *Delaware Section 262 appraisal petitions in M&A. Shareholders claim deal price was too low. Growing area.*
- 🔵 5.3.6 What derivative suit risk factors are present BEFORE a suit is filed? — *Old system 5-category pre-filing risk model: (1) board conflicts in M&A, (2) M&A diligence failures, (3) egregious behavior / employees / consumers, (4) health & safety Caremark failures, (5) massive fraud. 2/3 of SCAs have companion derivatives. Assessing category BEFORE filing = proactive. Settlements: Tesla/SolarCity $60M, Wells Fargo $240M, McKesson $175M.*

## 5.4 SEC Enforcement
*Where is this company in the SEC enforcement pipeline?*

- ⚪ 5.4.1 What stage is any SEC matter at (comment letters → inquiry → investigation → Wells → enforcement)?
- ⚪ 5.4.2 Are there SEC comment letters, and what topics?
- ⚪ 5.4.3 Has there been a Wells Notice?
- ⚪ 5.4.4 What prior SEC enforcement actions exist?

## 5.5 Other Regulatory & Government
*What non-SEC enforcement exposure exists?*

- ⚪ 5.5.1 Which government agencies regulate this company?
- ⚪ 5.5.2 Are there active DOJ investigations?
- ⚪ 5.5.3 Are there state AG investigations or multi-state actions?
- ⚪ 5.5.4 Are there industry-specific enforcement actions (FDA, EPA, OSHA, FTC, CFPB)?
- 🔵 5.5.5 Are there foreign government enforcement matters (UK SFO, EU Commission, foreign anti-bribery)? — *Multi-jurisdictional exposure compounds risk.*
- 🔵 5.5.6 Are there congressional investigations or subpoenas? — *Congressional scrutiny often precedes regulatory enforcement and amplifies media. Big Tech hearings, pharma pricing.*

## 5.6 Non-Securities Litigation
*What is the aggregate non-SCA litigation landscape?*

- ⚪ 5.6.1 What is the aggregate active litigation count?
- ⚪ 5.6.2 Are there significant product liability, employment, IP, or antitrust matters?
- ⚪ 5.6.3 Are there whistleblower/qui tam actions?
- ⚪ 5.6.4 Are there cyber breach or environmental litigation matters?

## 5.7 Defense Posture & Reserves
*How well positioned is the company to defend against claims?*

- ⚪ 5.7.1 What defense provisions exist (federal forum, PSLRA safe harbor)?
- ⚪ 5.7.2 What are the contingent liabilities and litigation reserves (ASC 450)?
- ⚪ 5.7.3 What is the historical defense success rate?
- 🔴 ~~5.7.4 "Consent to Counsel" provision~~ — *REMOVED: Requires access to the actual D&O policy being underwritten. This is a policy structure recommendation for the underwriter, not a company analysis question. Move to Underwriting Decision Logic (process insight #5).*
- 🔴 ~~5.7.5 Side A coverage adequacy~~ — *REMOVED: Same — requires the policy document itself. Side A structure recommendations belong in scoring/decision output, triggered by distress indicators (3.6.1, 3.6.4). Not an analysis input.*

## 5.8 Litigation Risk Patterns
*What systemic litigation patterns apply?*

- ⚪ 5.8.1 What are the open statute of limitations windows?
- ⚪ 5.8.2 What industry-specific allegation theories apply?
- ⚪ 5.8.3 What is the contagion risk from peer lawsuits?
- 🔵 5.8.4 Do financial events temporally correlate with stock drops to create class period windows? — *Restatement announced during stock decline = class period trigger. Material weakness disclosed + 15% drop = SCA filing pattern. The temporal overlap between financial events and market impact is the exact fact pattern plaintiffs use to define class periods.*

## 5.9 Sector-Specific Litigation & Regulatory Patterns
*What sector-specific patterns and regulatory databases apply? (Was Sections 7.6 + 8.3 + 8.4)*

- 🔵 5.9.1 What sector-specific litigation patterns apply to this company?

| Sector | Primary D&O Allegation Theories | Typical Triggers |
|---|---|---|
| **SaaS/Cloud** | Revenue recognition (ASC 606 allocation), customer metrics inflation, churn concealment | NRR decline, logo churn spike, deferred revenue changes |
| **Biotech/Pharma** | Clinical trial data manipulation, FDA submission failures, off-label promotion, product liability, **"Overpromise & Underdeliver"** (inflated efficacy claims vs actual trial data) | Failed trial, CRL, safety signal, PubPeer/Retraction Watch findings, **Binary event reliance** (single Phase 3 or FDA decision = existential stock impact) |
| **Banking** | Loan quality misrepresentation, BSA/AML failures, consumer fraud (UDAAP), redlining | NPL spike, consent order, CFPB action, DOJ fair lending |
| **Insurance** | Reserve deficiency, investment portfolio losses, excess commission, claims handling | Reserve strengthening, combined ratio deterioration, AM Best downgrade |
| **Energy** | Reserve write-downs, environmental liability concealment, ESG/climate greenwashing | Commodity price crash, EPA action, climate litigation |
| **Retail** | Same-store sales manipulation, inventory valuation, e-commerce overpromise | Comp miss, inventory write-down, store closure wave |
| **Tech/Hardware** | Product defect concealment, IP theft, antitrust, supply chain disruption concealment | Product recall, import ban (ITC), EU DMA fine |
| **Healthcare** | False Claims Act/Anti-Kickback, Stark Law, opioid liability, patient safety | DOJ/OIG investigation, CMS exclusion, whistleblower qui tam |
| **Mining/Materials** | Environmental contamination (PFAS/Superfund), mine safety, resource reserve overstatement | EPA order, MSHA fatality, commodity crash + impairment |
| **Automotive** | Safety defect concealment, emissions fraud, delivery/production guidance miss | NHTSA investigation, recall, delivery miss |
| **Fintech/Payments** | Unlicensed money transmission, consumer harm, BSA/AML, data breach | State enforcement, CFPB action, federal indictment |
| **Construction** | Percentage-of-completion fraud, cost overrun concealment, safety violations | DOJ False Claims, OSHA fatality, project write-down |

- 🔵 5.9.2 What do sector-specific regulatory databases show?

| Sector | Regulatory Databases | What They Catch Early |
|---|---|---|
| **Pharma/Biotech/Devices** | FDA Warning Letters, 483 Observations, Import Alerts, Recalls, MAUDE adverse events, ClinicalTrials.gov | Manufacturing quality, safety signals, trial problems before press release |
| **Banking/Financial** | OCC orders, FDIC orders, CFPB complaints, Fed enforcement, FinCEN, state banking regulators | Consumer harm patterns, BSA/AML deficiencies, capital issues |
| **Energy/Chemicals** | EPA ECHO (SNC status, HPV violations), air/water permits, Superfund, TRI releases | Environmental violations building before major enforcement |
| **Mining** | MSHA violations, fatalities, pattern of violations, significant & substantial citations | Safety culture deterioration before catastrophic event |
| **Automotive** | NHTSA complaints, investigations, recalls, early warning reports, TSBs | Safety defect patterns before recall announcement |
| **Consumer Products** | CPSC recalls, complaints, import violations | Product safety issues before class action |
| **Healthcare** | CMS sanctions, OIG exclusions, state health department actions | Billing/quality issues before False Claims Act |
| **All sectors** | OSHA violations, fatalities, EEOC charges, DOL wage/hour, state AG complaints | Workplace safety, employment, consumer protection |

🔴 **5.10 Runoff / Tail Coverage Analysis — DEFERRED.** *Valuable for M&A transactions but not needed for v1. Revisit when adding transaction-specific workflows.*

---

# WHAT WE COULD INCLUDE BUT CHOSE NOT TO (and why)

## Impractical Data Sources
*We can't systematically acquire this data, so don't build questions around it.*

| Old System Check | What It Is | Why Excluded |
|---|---|---|
| Dark web monitoring | Pre-breach intelligence from dark web | Expensive specialized feeds ($$$), can't automate |
| ISS QualityScore / Glass Lewis | Governance ratings | Institutional subscription ($$$) |
| MSCI AGR Score | Accounting governance risk score | Enterprise subscription ($$$), AGR <50 = 2.5x litigation |
| Bloomberg terminal data | Block trades, dark pool activity | $25K+/year, enterprise only |
| S3 Partners | Lending utilization, squeeze probability | Institutional subscription |
| Interactive Brokers borrow fee | Cost to borrow for short sellers | Requires brokerage account |
| SimilarWeb / Sensor Tower | Web traffic, app downloads | Paid tiers for useful data (noted in 1.10.5) |

## Trading Microstructure
*We're underwriters, not quantitative traders. Short interest level + direction + named reports is sufficient.*

| Old System Check | What It Is | Why Excluded |
|---|---|---|
| Cost to borrow (E.2.5) | Short seller borrowing cost | Institutional data feed |
| Fail-to-deliver volume (E.2.6) | SEC FTD data | Mechanical/noisy signal |
| Dark pool activity (E.2.7) | ATS trading percentage | Requires FINRA ATS data feed |
| Options IV skew (E.2.10) | Put option implied volatility | Derivatives analysis beyond scope |
| Synthetic short positions (E.2.20) | Options-based short exposure | Deep options analysis |
| Securities lending utilization (E.2.18) | How much stock is lent out | S3 Partners subscription |
| Short squeeze probability (E.2.19) | Likelihood of squeeze | Trading strategy, not D&O risk |
| Pre/after-hours activity (E.2.16) | Extended hours trading | Marginal signal for D&O |
| Exchange short sale volume (E.2.17) | % of volume that's short | Redundant with short interest |
| Block trade analysis (E.2.13) | Large institutional trades | Bloomberg-level data |

## Business Strategy Analysis
*If strategy fails, financial metrics and stock price will show it. We assess risk signals, not MBA strategy.*

| Old System Check | What It Is | Why Excluded |
|---|---|---|
| Barriers to entry (C.3.8) | Porter's Five Forces | MBA analysis, doesn't predict D&O |
| Buyer/supplier power (C.3.10) | Porter's Five Forces | Same — indirect at best |
| Pricing power (C.3.5) | Ability to maintain prices | Margin compression captures this |
| Customer switching costs (C.3.6) | Lock-in analysis | Competitive moat question covers this |
| Unit economics LTV/CAC (C.1.4) | Per-customer economics | Covered by sector KPIs where relevant |
| Scalability / operating leverage (C.1.5) | Revenue growth vs cost growth | Academic metric |
| Platform vs linear model (C.1.8) | Business model taxonomy | Not a risk signal |
| Asset light vs heavy (C.1.7) | Total assets / revenue | Not a risk signal |
| Capacity utilization (C.6.5) | % of capacity used | Operational efficiency metric |
| Business continuity / DR (C.6.10) | Disaster recovery | IT resilience, very indirect |
| Growth strategy (C.7.1-C.7.8) | 8 growth strategy checks | Forward business strategy, not risk |

## Redundant With Better Questions
*Already captured by questions we have, at a better level of abstraction.*

| Old System Check | What It Is | Covered By |
|---|---|---|
| Cash concentration risk / offshore (B.1.6) | % cash outside US | 3.1.1 total liquidity |
| Restricted cash (B.1.7) | Restricted / total cash | 3.1.1 liquidity |
| Floating rate exposure (B.2.8) | Floating % of debt | 3.2.2 interest coverage |
| Secured vs unsecured (B.2.15) | Debt seniority | 3.2.1 overall leverage |
| Cross-default provisions (B.2.17) | Covenant linkage | 3.2.4 covenant risks |
| Revenue volatility std dev (B.3.7) | 12-quarter growth std dev | 3.3.1 revenue trend |
| GC/COO/CTO profiles (D.1.5-D.1.8) | Non-CEO/CFO executives | 4.2.1-4.2.2 focus on CEO/CFO (litigation exposure) |
| Non-compete enforceability (D.1.13) | Employment law detail | Too indirect for D&O |
| Recent promotions (D.1.14) | Internal advancement | Positive indicator, not risk |
| Tax gross-ups (D.3.12) | Company pays exec taxes | Minor comp detail |
| Cumulative voting (D.5.13) | Director election method | Exists in few states, rarely relevant |
| NOL poison pill (D.5.16) | Tax asset protection | Tax strategy, not governance risk |

## Old System Structural Duplication
*Same analysis appearing in multiple modules. Our section boundaries eliminate this.*

| What | Where It Appeared | Our Fix |
|---|---|---|
| Stock performance analysis | Module 04 (Financial), Module 07 (Market), Module 09 (Prior Acts) — ~40 duplicate checks | Section 2 (MARKET) only |
| Insider trading analysis | Module 06 (Governance), Module 09 (Prior Acts) — ~12 duplicates | Section 4.4 only |
| Disclosure gap analysis | Module 03 (Litigation), Module 09 (Prior Acts) — ~12 duplicates | Section 4.7-4.8 only |
| Ownership structure | Module 06 (Governance), Module 07 (Market) — ~8 duplicates | Section 2.5 only |

---

# PROCESS INSIGHTS FROM OLD SYSTEM

Not questions, but important for implementation:

1. **🔵 PURPLE status** — Old system distinguishes "checked and clear" from "not checked." Prevents false "all clear" when data is unavailable. We should implement this.

2. **🔵 Event-window attribution methodology** — For drops: 0/1/5/10-day sector-adjusted returns, cumulative market cap loss, recovery analysis. Maps directly to damages calculation.

3. **🔵 Nuclear trigger aggregation** — 3+ nuclear findings = auto-escalate. Not just "what's RED" but "how many and in what combination." Scoring-stage issue.

4. **🔵 Score → underwriting decision** — EXTREME (70-100, >20% probability, decline) → HIGH (50-69, 10-20%, 1.5-2x rate) → AVERAGE (30-49, 5-10%, market) → BELOW (15-29, 2-5%, discount) → MINIMAL (0-14, <2%, best rates).

5. **🔵 Underwriting Decision Logic Gates** — First-principles sequential screens before final scoring (Source: 2025 Litigation Trends):
    - **Gate 1: "Kill Step" (Insolvency Check)** — If Z-Score < 1.8 or EDF-X is critical, the company likely cannot indemnify directors. This shifts 100% of risk to Side A. Decision: Decline or require full collateralization/specific insolvency exclusion.
    - **Gate 2: "Scienter Screen" (Forensic Accounting)** — High TATA or abnormal DEPI suggests management is manipulating earnings. Provides the "smoke" for securities fraud. Decision: Debit Side C (Entity) coverage; restrict limits; require higher retention.
    - **Gate 3: "Governance Screen" (Moral Hazard)** — Combined CEO/Chair or "Successor Chair" creates an environment where red flags are ignored, leading to Caremark claims. Decision: Debit Side A premium; require Lead Independent Director as binding condition.
    - **Gate 4: "Emerging Screen" (Disclosure Latency)** — If company hypes AI/ESG without internal controls to verify claims, they face strict liability for material misstatements ("AI Washing"). Decision: Refer for subject matter review; specific AI Disclosure warranty if marketing spend > R&D spend.

6. **🔵 Actuarial Anchor** — Pre-analysis profiling that sets the baseline:
    - Market Cap Stratification: Micro (<$1B, insolvency/severity risk) vs Large Cap (>$10B, frequency risk)
    - Circuit Court Leniency: HQ in "High Severity" Circuit (e.g., 9th or 2nd)? Lenient precedents reduce dismissal probability by ~7%
    - Lifecycle Stage: De-SPAC (<36 months) or IPO? High Section 11 strict liability exposure

---

# Structural Relocation Map (v4 → v5)

For traceability — where each v4 section moved:

| v4 Section | v5 Location | Notes |
|---|---|---|
| 1. COMPANY (1.1-1.7) | 1. COMPANY (1.1-1.7) | Same, minor renumbering |
| 2. FINANCIAL (2.1-2.8) | 3. FINANCIAL (3.1-3.8) | Renumbered from 2→3 |
| 3. GOVERNANCE (3.1-3.6) | 4. GOV & DISCLOSURE (4.1-4.6) | Renumbered from 3→4 |
| 4. LITIGATION (4.1-4.9) | 5. LIT & REGULATORY (5.1-5.10) | Renumbered from 4→5 |
| 5. MARKET (5.1-5.7) | 2. MARKET (2.1-2.7) | Renumbered from 5→2 |
| 6. DISCLOSURE (6.1-6.6) | 4. GOV & DISCLOSURE (4.7-4.9) | Merged into section 4 |
| 7.1 Catalyst Events | 1.11 Risk Calendar | Moved to COMPANY |
| 7.2 Employee Signals | 1.9 Employee Signals | Moved to COMPANY |
| 7.3 Customer Signals | 1.10 Customer Signals | Moved to COMPANY |
| 7.4 Macro & Industry | 1.8 Macro & Industry | Moved to COMPANY |
| 7.5 Media Signals | 4.10 Media & External | Moved to GOV & DISCLOSURE |
| 7.6 Regulatory Databases | 5.9 Sector Litigation | Moved to LITIGATION |
| 8.1 Sector KPIs | 3.8 Sector Financial | Embedded in FINANCIAL |
| 8.2 Sector Thresholds | 3.8 (threshold table) | Embedded as principle |
| 8.3 Sector Litigation | 5.9 Sector Litigation | Embedded in LITIGATION |
| 8.4 Sector Regulatory | 5.9 Sector Litigation | Embedded in LITIGATION |
| 8.5 Sector Risk Profiles | 1.3.8 (binary flags) | Embedded in COMPANY |

---

# Summary

| Section | Subsections | v5 Net | v5.1 🔵 Added | v5.1 🟠 Refined | v5.1 Net |
|---|---|---|---|---|---|
| **1. COMPANY** | 11 | 53 | +1 (1.3.10) | +1 (1.2.6) | **54** |
| **2. MARKET** | 7 | 24 | +1 (2.1.5) | +1 (2.2.3) | **25** |
| **3. FINANCIAL** | 8 | 38 | +3 (3.4.7, 3.5.8, 3.5.9) | +2 (3.6.1, 3.6.4) | **41** |
| **4. GOV & DISCLOSURE** | 10 | 57 | +5 (4.1.8, 4.1.9, 4.2.7, 4.7.10, 4.9.4) | 0 | **62** |
| **5. LIT & REGULATORY** | 10 | 40 | +3 (5.7.4, 5.7.5, 5.10.5) | +1 (5.3.3) | **43** |
| **TOTAL** | **46** | **212** | **+13 new questions** | **+5 refinements** | **~225** |

v5.1 changes from v5: +13 new questions (🔵), 5 existing questions refined (🟠) with stronger framing and specific mechanisms. Sources: KPMG ICFR Handbook [316–1030], OCC Corporate Governance Handbook [121–246], 2025 Litigation Trends [1–24]. Also adds 3 process insights (Decision Gates, Actuarial Anchor, Score→Decision).

Note: v4 had ~246 questions across 8 sections. v5 had ~212 across 5 sections. v5.1 has ~229 after incorporating research input. The original reduction came from: (a) 5 removals carried forward, (b) consolidation of 3 FORWARD subsections that had duplicate overlap with existing questions, (c) sector content embedded as tables rather than standalone questions.

## Mapping Audit Results

| Source | Total | Covered | Excluded | Sector | Scoring | Orphan |
|---|---|---|---|---|---|---|
| Our 388 checks | 388 | 365 | 6 | 15 | — | 1 |
| Old system modules 01-04 | 206 | 152 | 23 | 24 | — | 1 |
| Old system modules 05-07 | 210 | 174 | 36 | 0 | — | 0 |
| Old system modules 08-10 | 293 | 117 | 61 | 4 | 111 | 0 |
| **TOTAL** | **1,097** | **808 (73.7%)** | **126 (11.5%)** | **43 (3.9%)** | **111 (10.1%)** | **2 (0.2%)** |

- **808 COVERED** — map to a specific question in this framework
- **126 EXCLUDED** — documented in "Chose Not To" tables or redundant with better questions
- **43 SECTOR** — sector-specific checks now embedded in sections 3.8 and 5.9
- **111 SCORING** — point assignment rules belonging in SCORE stage, not analysis questions
- **2 ORPHAN** — added as new questions (3.6.6 restructuring, 5.8.4 class period windows)
- **0 UNACCOUNTED** — every check from both systems is mapped

*Note: Mapping files in `/tmp/mapping_*.md` reference v4 numbering. Cross-reference with the Structural Relocation Map above to translate to v5 numbering.*
