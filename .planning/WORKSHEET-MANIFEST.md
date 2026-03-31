# D&O Underwriting Worksheet — Content Manifest (GOLDEN)

**Purpose:** Definitive map of every piece of content in the worksheet. Numbered hierarchically. Nothing exists outside this manifest.

**Status legend:**
- `[LIVE]` — currently displayed in rendered worksheet
- `[HIDDEN]` — data exists in state.json but not displayed
- `[MISSING]` — should be extracted/computed but doesn't exist yet
- `[NEW]` — new section/subsection to build
- `[MANUAL INPUT]` — data comes from broker submission, not automated data
- `[PARTIALLY LIVE]` — some data displayed, gaps remain

---

## 0. SUBMISSION INPUT (broker-provided, pre-analysis) `[NEW SECTION]`

### 0.1 Expiring D&O Program
- 0.1.1 Total program limit `[MANUAL INPUT]`
- 0.1.2 Per-layer limits and retentions `[MANUAL INPUT]`
- 0.1.3 Carrier names by layer `[MANUAL INPUT]`
- 0.1.4 Side A / B / C coverage split `[MANUAL INPUT]`
- 0.1.5 Excess / DIC placement `[MANUAL INPUT]`

### 0.2 Prior Claims / Loss History
- 0.2.1 Claims by policy year `[MANUAL INPUT]`
- 0.2.2 Open claims (count, description, reserves) `[MANUAL INPUT]`
- 0.2.3 Paid losses (by year, cumulative) `[MANUAL INPUT]`

### 0.3 Expiring Premium & Terms
- 0.3.1 Expiring premium (per layer) `[MANUAL INPUT]`
- 0.3.2 Key terms and conditions `[MANUAL INPUT]`
- 0.3.3 Notable exclusions or endorsements `[MANUAL INPUT]`

### 0.4 Policy Period
- 0.4.1 Inception date `[MANUAL INPUT]`
- 0.4.2 Expiry date `[MANUAL INPUT]`
- 0.4.3 Retroactive date `[MANUAL INPUT]`
- 0.4.4 Extended reporting period (ERP) details `[MANUAL INPUT]`

### 0.5 Broker / Intermediary
- 0.5.1 Broker name and contact `[MANUAL INPUT]`
- 0.5.2 Producing office `[MANUAL INPUT]`

---

## 1. DECISION DASHBOARD (Page 0 — 30-second read)

### 1.1 Company Identity
- 1.1.1 Company logo `[LIVE]`
- 1.1.2 Company name + ticker `[LIVE]`
- 1.1.3 Industry + sector + sector ETF `[LIVE]`
- 1.1.4 D&O Underwriting Worksheet label `[LIVE]`

### 1.2 Key Metrics Strip
- 1.2.1 Market cap `[LIVE]`
- 1.2.2 Revenue (XBRL FY) `[LIVE]`
- 1.2.3 Stock price `[LIVE]`
- 1.2.4 Employees `[LIVE]`

### 1.3 Score Badge
- 1.3.1 Quality score (0-100) `[LIVE]`
- 1.3.2 Tier name (WIN/WRITE/WATCH/WALK/NO_TOUCH) `[LIVE]`
- 1.3.3 Score position bar (colored segments + dot) `[LIVE]`

### 1.4 5-Year Performance Strip
- 1.4.1 Weekly stock chart (Bloomberg Orange style) `[LIVE]`

### 1.5 Mini-Cards Row (6 cards)
- 1.5.1 Market Cap & Valuation (MCap, decile, EV, EV/Revenue, shares, rev/employee) `[LIVE]`
- 1.5.2 Stock Price & Range (price, 52W high/low, range slider, next earnings) `[LIVE]`
- 1.5.3 Revenue & Growth (revenue, sparkline, EV/Revenue, EBITDA margin) `[LIVE]`
- 1.5.4 Profitability & Cash Flow (EBITDA, sparkline, FCF sparkline, earnings beats) `[LIVE]`
- 1.5.5 Balance Sheet (total assets, cash/debt composition bar, cash, debt, net cash, current ratio, goodwill) `[LIVE]`
- 1.5.6 Valuation multiples card (P/E, Forward P/E, EV/EBITDA, PEG, P/B, P/S) `[HIDDEN→NEW]`

### 1.6 Active Litigation Bar
- 1.6.1 Active SCA count + case names `[LIVE]`
- 1.6.2 Regulatory agency status (clear/active badges) `[LIVE]`
- 1.6.3 D&O Litigation History one-liner `[LIVE]`

### 1.7 Combo Stock Chart
- 1.7.1 Navy Professional combo chart (price + DDL + volume + drop shading + insider trades) `[LIVE]`

### 1.8 Key Risk Findings
- 1.8.1 Top 5-7 findings with severity badges (red/yellow) `[LIVE]`
- 1.8.2 Red count + Yellow count summary `[LIVE]`

### 1.9 Executive Summary (condensed)
- 1.9.1 Recommendation (tier + action) `[LIVE]`
- 1.9.2 Probability range + claim band `[LIVE]`
- 1.9.3 Red flags with ceiling triggers `[LIVE]`
- 1.9.4 Key Negatives + Key Positives (side by side) `[LIVE]`
- 1.9.5 Narrative block `[LIVE]`
- 1.9.6 Dual-voice commentary `[LIVE]`

### 1.10 Quick Screen
- 1.10.1 Trigger matrix (signal pass/fail grid) `[LIVE]`

---

## 2. THE COMPANY (what they do, how they make money)

### 2.1 Business Overview
- 2.1.1 Business description `[LIVE]`
- 2.1.2 What the Company Does (narrative) `[LIVE]`
- 2.1.3 D&O Risk Signature (what makes this company unique) `[LIVE]`
- 2.1.4 Listing exchange (NYSE/Nasdaq) `[HIDDEN — in yfinance]`
- 2.1.5 State of incorporation `[MISSING]`
- 2.1.6 Foreign private issuer (FPI) status `[LIVE — drives 20-F vs 10-K]`
- 2.1.7 ADR / cross-listing status `[MISSING]`
- 2.1.8 Years public / IPO date `[LIVE — computed in RESOLVE]`
- 2.1.9 SPAC / de-SPAC history (if applicable) `[MISSING]`

### 2.2 Revenue Model
- 2.2.1 How Money Flows (diagram) `[LIVE]`
- 2.2.2 Revenue Model Card (type, recurring %, contract duration, etc.) `[LIVE]`
- 2.2.3 Revenue model type classification (Product/Service/Hybrid) `[HIDDEN]`

### 2.3 Revenue Analysis
- 2.3.1 Revenue Segments table `[LIVE]`
- 2.3.2 Revenue Segment Breakdown (detail) `[LIVE]`
- 2.3.3 Revenue Waterfall / Growth Decomposition `[LIVE]`
- 2.3.4 Unit Economics `[LIVE]`
- 2.3.5 Segment lifecycle stages (growth/mature/decline per segment) `[HIDDEN]`
- 2.3.6 Segment margins `[HIDDEN]`

### 2.4 Geographic & Concentration
- 2.4.1 Geographic Footprint (revenue by region) `[LIVE]`
- 2.4.2 Customer Concentration `[LIVE]`
- 2.4.3 Supplier Concentration `[LIVE]`
- 2.4.4 Supply chain critical dependencies `[MISSING]`
- 2.4.5 International operations footprint (countries of operation vs revenue) `[MISSING]`

### 2.5 Competitive Landscape
- 2.5.1 Peer Group (who are the peers, how selected) `[LIVE — from Financial]`
- 2.5.2 Competitive landscape narrative `[LIVE]`
- 2.5.3 Emerging Risk Radar `[LIVE]`
- 2.5.4 Disruption risk assessment `[HIDDEN]`

### 2.6 Regulatory Environment
- 2.6.1 Regulatory map (which agencies regulate this company) `[NEW]`
- 2.6.2 Regulatory risk factors from 10-K `[LIVE — in Risk Factors]`
- 2.6.3 Active regulatory proceedings/investigations `[PARTIALLY LIVE — in Litigation]`

### 2.7 Risk Profile
- 2.7.1 Risk Factors (D&O-Relevant) `[LIVE]`
- 2.7.2 10-K Year-over-Year Risk Factor Analysis (new/removed/escalated) `[LIVE]`
- 2.7.3 D&O Exposure Factors `[LIVE]`

### 2.8 Operations Detail
- 2.8.1 Subsidiary structure (count, jurisdictions, high/low-reg) `[HIDDEN]`
- 2.8.2 Workforce distribution (total, domestic, international) `[HIDDEN]`
- 2.8.3 Operational complexity (VIE, SPE, dual-class flags) `[HIDDEN]`
- 2.8.4 Operational resilience assessment `[HIDDEN]`
- 2.8.5 Key person risk assessment (founder-led, succession plan) `[HIDDEN]`
- 2.8.6 IP/patent portfolio summary `[MISSING]`
- 2.8.7 Cybersecurity posture `[HIDDEN]`
- 2.8.8 ESG risk level `[LIVE]`
- 2.8.9 Anti-corruption exposure (FCPA/UK Bribery Act, operations in high-CPI countries) `[MISSING]`
- 2.8.10 Antitrust exposure (market concentration, pending investigations) `[PARTIALLY LIVE — in litigation]`

### 2.9 Company Checks
- 2.9.1 Check Results summary `[LIVE]`

### 2.10 Corporate Transactions & Events `[NEW]`
- 2.10.1 M&A history (acquisitions, divestitures, with dates/values/status) `[HIDDEN — partial in XBRL]`
- 2.10.2 Goodwill from acquisitions `[LIVE — in XBRL balance sheet]`
- 2.10.3 Integration risk (earn-outs, contingent consideration) `[MISSING]`
- 2.10.4 Pending/announced transactions `[MISSING]`
- 2.10.5 Corporate event timeline (visual) `[HIDDEN]`
- 2.10.6 Divestitures / spinoffs `[MISSING]`

---

## 3. STOCK & MARKET (what the market is telling us)

### 3.1 Price Performance
- 3.1.1 Stock Performance summary (price, 52W, returns) `[LIVE]`
- 3.1.2 1-Year stock chart `[LIVE]`
- 3.1.3 5-Year stock chart `[LIVE]`
- 3.1.4 Drawdown Analysis chart `[LIVE]`
- 3.1.5 Relative Performance (indexed to 100 vs sector & SPY) `[LIVE]`

### 3.2 Volatility & Risk
- 3.2.1 Volatility & Beta charts `[LIVE]`
- 3.2.2 Return Attribution (market vs sector vs idiosyncratic) `[LIVE]`

### 3.3 Stock Drops
- 3.3.1 Stock Drop Analysis `[LIVE]`
- 3.3.2 Drop Scatter plot `[LIVE]`
- 3.3.3 Significant Stock Drops (with causation) `[LIVE]`
- 3.3.4 Corrective disclosure identification (what triggered each drop) `[MISSING]`
- 3.3.5 Per-drop market context (beta-adjusted, S&P on same day) `[MISSING]`

### 3.4 Short Interest
- 3.4.1 Short interest (% float, shares, days to cover, trend) `[LIVE]`

### 3.5 Earnings & Analyst
- 3.5.1 Earnings Guidance Track Record (beat rate, miss history) `[LIVE]`
- 3.5.2 Analyst Consensus (buy/hold/sell counts, price targets) `[LIVE]`
- 3.5.3 Individual quarterly EPS actual vs estimate (24 quarters) `[HIDDEN]`
- 3.5.4 Company guidance vs actual (management's own statements) `[MISSING]`
- 3.5.5 Earnings calendar (next earnings date) `[HIDDEN]`
- 3.5.6 Guidance change log (raised/lowered/withdrawn with dates) `[MISSING]`

### 3.6 Valuation
- 3.6.1 Valuation multiples table (P/E, Forward P/E, EV/EBITDA, PEG, P/B, P/S, EV/Rev) `[HIDDEN]`
- 3.6.2 Enterprise value `[HIDDEN]`
- 3.6.3 Growth metrics (revenue growth, earnings growth) `[HIDDEN]`
- 3.6.4 Profitability metrics (margins, ROE, ROA) `[HIDDEN]`

### 3.7 Insider Trading
- 3.7.1 Insider Trading Analysis (net direction, 10b5-1 %, clusters) `[LIVE]`
- 3.7.2 Individual insider transaction table (49 transactions) `[HIDDEN]`

### 3.8 Capital Markets Activity & Offerings
- 3.8.1 IPO Analysis (if applicable): IPO date, IPO price vs current, offering size, underwriters, lockup expiry, Section 11 window, S-1 risk factor comparison `[MISSING]`
- 3.8.2 Secondary/Follow-on Offerings: S-3 shelf capacity, follow-ons, ATM programs, timing vs material events `[PARTIALLY LIVE]`
- 3.8.3 Convertible Debt: notes, conversion price, dilution `[HIDDEN — XBRL concept]`
- 3.8.4 Shelf Registration Status `[LIVE — S-3 acquired]`
- 3.8.5 SPAC/De-SPAC Analysis (if applicable) `[MISSING]`
- 3.8.6 Dividend history & sustainability `[HIDDEN]`
- 3.8.7 Share repurchase history `[HIDDEN]`

### 3.9 Sentiment & Disclosure
- 3.9.1 Disclosure Quality `[LIVE]`
- 3.9.2 Narrative Coherence `[LIVE]`
- 3.9.3 NLP & Sentiment Dashboard `[LIVE]`

### 3.10 Ownership
- 3.10.1 Institutional ownership (top holders) `[LIVE — in Governance]`
- 3.10.2 Institutional ownership quarterly changes `[MISSING]`
- 3.10.3 Index membership (S&P 500, Nasdaq 100, etc.) `[MISSING]`

### 3.11 Market Checks
- 3.11.1 Market Checks `[LIVE]`
- 3.11.2 Market Risk Deep Dive `[LIVE]`

---

## 4. FINANCIALS (are the numbers real, is the company healthy)

### 4.1 Income Statement
- 4.1.1 Annual Financial Comparison (3-year P&L) `[LIVE]`
- 4.1.2 Key Financial Metrics — Profitability `[LIVE]`
- 4.1.3 Quarterly Financial Trends (8Q) `[LIVE]`
- 4.1.4 Post-Annual Quarterly Update `[LIVE]`

### 4.2 Balance Sheet
- 4.2.1 Key Financial Metrics — Balance Sheet `[LIVE]`
- 4.2.2 Balance Sheet composition (assets, liabilities, equity) `[LIVE — in statements]`
- 4.2.3 Working capital detail (receivables, inventory, payables) `[MISSING]`
- 4.2.4 Goodwill / intangible as % of equity `[MISSING]`

### 4.3 Cash Flow
- 4.3.1 Key Financial Metrics — Cash Flow `[LIVE]`
- 4.3.2 Free cash flow trend `[HIDDEN]`
- 4.3.3 Capital allocation view (FCF → dividends + buybacks + capex + debt paydown) `[MISSING]`
- 4.3.4 Cash flow adequacy (FCF vs debt service) `[MISSING]`

### 4.4 Debt & Capital Structure
- 4.4.1 Debt summary (total, short-term, long-term, net debt) `[LIVE — in leverage]`
- 4.4.2 Debt instruments detail (individual notes with rate, maturity, amount) `[HIDDEN]`
- 4.4.3 Debt maturity schedule (year-by-year amounts due) `[MISSING]`
- 4.4.4 Interest rate composition (fixed vs floating %) `[HIDDEN]`
- 4.4.5 Commercial paper outstanding `[HIDDEN]`
- 4.4.6 Credit facility (capacity, drawn, available) `[HIDDEN]`
- 4.4.7 Covenant compliance (ratios, headroom, status) `[HIDDEN]`
- 4.4.8 Credit ratings (Moody's/S&P/Fitch) `[MISSING]`
- 4.4.9 Refinancing risk assessment `[MISSING]`
- 4.4.10 Bankruptcy risk assessment (unified: Altman Z + cash runway + debt maturities + going concern) `[MISSING]`

### 4.5 Liquidity
- 4.5.1 Liquidity ratios (current, quick, cash) `[LIVE — in leverage]`
- 4.5.2 Working capital trend `[LIVE — partially]`
- 4.5.3 Days cash on hand `[HIDDEN]`

### 4.6 Forensic Analysis
- 4.6.1 Distress Model Indicators (Altman Z, Beneish M, Ohlson O, Piotroski F) `[LIVE]`
- 4.6.2 Forensic Analysis Dashboard (component detail) `[LIVE]`
- 4.6.3 Earnings Quality (accruals, OCF/NI, DSO delta) `[LIVE]`

### 4.7 Tax
- 4.7.1 Tax Risk Profile (ETR, deferred tax, havens, transfer pricing) `[LIVE]`
- 4.7.2 Tax jurisdiction breakdown (federal/state/foreign) `[HIDDEN — new XBRL]`
- 4.7.3 Unrecognized tax benefits (UTB) `[HIDDEN — new XBRL]`

### 4.8 Audit & Disclosure
- 4.8.1 Audit Profile (auditor, Big 4, tenure, opinion, going concern) `[LIVE]`
- 4.8.2 Revenue Recognition (ASC 606) `[LIVE]`
- 4.8.3 MD&A Analysis `[LIVE]`
- 4.8.4 Risk Factor Analysis `[LIVE]`
- 4.8.5 Filing Patterns & Whistleblower `[LIVE]`
- 4.8.6 SEC comment letter topics `[HIDDEN]`
- 4.8.7 Restatement history (type, magnitude, periods, Big R vs little r) `[MISSING]`
- 4.8.8 Auditor change history with reasons `[MISSING]`
- 4.8.9 Material weakness history (current + resolved) `[MISSING]`
- 4.8.10 Non-GAAP reconciliation quality (adjustment magnitude, consistency) `[MISSING]`
- 4.8.11 Quarter-end revenue loading (Q4 as % of annual) `[MISSING]`

### 4.9 Peer Benchmarks
- 4.9.1 Peer Benchmarking (SEC Filers / XBRL Frames) `[LIVE]`
- 4.9.2 Peer Comparison Matrix `[LIVE]`

### 4.10 Financial Checks
- 4.10.1 Financial Checks `[LIVE]`

---

## 5. PEOPLE & GOVERNANCE (who runs it, can you trust them)

### 5.1 Executive Officers
- 5.1.1 Executive Risk Profiles (name, title, tenure, bio, risk assessment) `[LIVE]`
- 5.1.2 People Risk overview (stability score, departures) `[LIVE]`
- 5.1.3 Tenure & Stability `[LIVE]`
- 5.1.4 Key person risk (founder-led, succession plan) `[HIDDEN]`

### 5.2 Board of Directors
- 5.2.1 Board Composition (size, independence, classified, CEO/chair duality) `[LIVE]`
- 5.2.2 Board Member Forensic Profiles (per-director detail) `[LIVE]`
- 5.2.3 Director qualification tags `[HIDDEN]`
- 5.2.4 Director age `[HIDDEN]`
- 5.2.5 Board skills matrix `[MISSING]`
- 5.2.6 Committee membership detail (Audit/Comp/Nom — who chairs each) `[MISSING]`
- 5.2.7 Audit committee financial expert designation `[MISSING]`
- 5.2.8 Per-director board meeting attendance `[MISSING]`
- 5.2.9 Director interlocks (shared boards with other portfolio companies) `[MISSING]`
- 5.2.10 Overboarded directors (4+ public boards) `[MISSING]`

### 5.3 Compensation
- 5.3.1 Compensation Analysis (CEO total comp, salary, bonus, equity) `[LIVE]`
- 5.3.2 CEO Pay Ratio `[LIVE]`
- 5.3.3 Say-on-Pay vote results `[LIVE]`
- 5.3.4 CEO comp actually paid (ECD XBRL: pay-for-performance) `[NEW — ECD parser]`
- 5.3.5 NEO average comp + actually paid `[NEW — ECD parser]`
- 5.3.6 Company TSR vs Peer Group TSR `[NEW — ECD parser]`
- 5.3.7 CEO pay vs peer median `[MISSING]`
- 5.3.8 Equity award vesting schedules `[MISSING]`
- 5.3.9 Change-of-control / golden parachute provisions `[MISSING]`
- 5.3.10 Director stock ownership requirements `[MISSING]`
- 5.3.11 Executive employment agreements `[MISSING]`

### 5.4 Insider Activity
- 5.4.1 Insider Trading Activity (net direction, 10b5-1 %, alerts) `[LIVE]`
- 5.4.2 Insider transaction detail table (49 transactions) `[HIDDEN]`
- 5.4.3 Ownership trajectories (12 insiders over time) `[HIDDEN]`
- 5.4.4 Exercise-sell events `[HIDDEN]`
- 5.4.5 Award timing MNPI consideration (ECD XBRL flag) `[NEW — ECD parser]`
- 5.4.6 Award timing predetermined (ECD XBRL flag) `[NEW — ECD parser]`
- 5.4.7 Insider trading policy adopted (ECD XBRL flag) `[NEW — ECD parser]`
- 5.4.8 Scienter correlation (insider trades × material event timing) `[MISSING]`

### 5.5 Ownership & Activism
- 5.5.1 Ownership Structure (institutional %, insider %, top holders) `[LIVE]`
- 5.5.2 Activist Investor Risk `[LIVE]`
- 5.5.3 Shareholder proposals & vote results `[HIDDEN — count only]`
- 5.5.4 D&O insurance program (limits, retentions, carriers) `[MISSING]`
- 5.5.5 Indemnification provisions (mandatory vs permissive, advance of expenses) `[MISSING]`
- 5.5.6 ERISA / employee benefit plan exposure `[MISSING]`

### 5.6 Governance Structure
- 5.6.1 Structural Governance (classified board, poison pill, bylaws) `[LIVE]`
- 5.6.2 Transparency & Disclosure `[LIVE]`
- 5.6.3 Prior Litigation Exposure (officers & directors) `[LIVE]`
- 5.6.4 Clawback policy scope `[HIDDEN]`
- 5.6.5 Related party transactions `[MISSING]`
- 5.6.6 Forum selection clause detail `[MISSING]`
- 5.6.7 Advance notice bylaw provisions `[MISSING]`
- 5.6.8 Special meeting threshold `[MISSING]`
- 5.6.9 Written consent rights `[MISSING]`

### 5.7 Governance Checks
- 5.7.1 Governance Checks `[LIVE]`

---

## 6. LITIGATION & REGULATORY (who's suing, who's investigating)

### 6.1 Active Securities Litigation
- 6.1.1 Active Matters (SCA list with detail) `[LIVE]`
- 6.1.2 Case numbers / docket numbers `[MISSING]`
- 6.1.3 Class period dates (start, end, duration) `[MISSING]`
- 6.1.4 Filing dates `[MISSING]`
- 6.1.5 Named defendants (individuals) `[MISSING]`
- 6.1.6 Lead counsel + tier `[MISSING]`
- 6.1.7 Lead plaintiff type (institutional vs individual) `[MISSING]`
- 6.1.8 Judge + track record `[MISSING]`
- 6.1.9 Procedural posture (MTD pending, certified, discovery) `[MISSING]`
- 6.1.10 Key rulings `[MISSING]`
- 6.1.11 Legal theories per case `[MISSING]`
- 6.1.12 Transaction-related litigation (M&A appraisal, Section 11, going-private) `[MISSING]`
- 6.1.13 Multi-jurisdictional litigation (Canada, Australia, Netherlands) `[MISSING]`

### 6.2 Derivative Suits
- 6.2.1 Derivative Suits list `[LIVE]`

### 6.3 Regulatory & Enforcement
- 6.3.1 SEC Enforcement Pipeline `[LIVE]`
- 6.3.2 SEC comment letter topics `[HIDDEN]`
- 6.3.3 Industry sweep detection `[HIDDEN]`
- 6.3.4 Regulatory agency-specific status `[NEW — from regulatory map]`

### 6.4 Settlement & Exposure
- 6.4.1 Settlement History `[LIVE]`
- 6.4.2 Settlement amounts (historical) `[MISSING]`
- 6.4.3 Contingent Liabilities (ASC 450) `[LIVE]`
- 6.4.4 Statute of Limitations — Exposure Windows `[LIVE]`
- 6.4.5 Insurance coverage analysis `[MISSING]`
- 6.4.6 Reserve adequacy assessment `[MISSING]`
- 6.4.7 Comparative settlement analysis (peer settlements) `[MISSING]`
- 6.4.8 Market cap at time of alleged fraud `[MISSING]`
- 6.4.9 Share turnover during class period `[MISSING]`
- 6.4.10 Damages model output (DDL estimate, proportional) `[HIDDEN — DDL in combo chart]`
- 6.4.11 Defense counsel roster / typical firms `[MISSING]`
- 6.4.12 Settlement timing benchmarks `[MISSING]`

### 6.5 Defense Assessment
- 6.5.1 Defense Strength Assessment `[LIVE]`
- 6.5.2 Allegation Theory Mapping `[LIVE]`
- 6.5.3 Industry Claim Patterns `[LIVE]`
- 6.5.4 Pending/prior litigation date (for claims-made trigger) `[MISSING]`

### 6.6 Other Matters
- 6.6.1 Workforce, Product & Environmental Matters `[LIVE]`
- 6.6.2 Whistleblower Indicators `[LIVE]`
- 6.6.3 Employee litigation (EEOC, NLRB) `[MISSING]`
- 6.6.4 Product recall history `[MISSING]`
- 6.6.5 Environmental liabilities `[MISSING]`
- 6.6.6 Cybersecurity incidents `[LIVE — 10 entries]`
- 6.6.7 Insured-vs-insured exposure (internal disputes) `[MISSING]`
- 6.6.8 Professional services exclusion applicability `[MISSING]`

### 6.7 Litigation Timeline
- 6.7.1 Litigation timeline events (visual) `[HIDDEN — 3 events]`

### 6.8 Litigation Checks
- 6.8.1 Litigation Checks `[LIVE]`
- 6.8.2 Litigation Risk Deep Dive `[LIVE]`

---

## 7. SECTOR & INDUSTRY ANALYSIS (sector-specific risk context) `[NEW SECTION]`

### 7.1 Sector Claim Profile
- 7.1.1 Sector SCA filing rate (per 1,000 companies) `[NEW]`
- 7.1.2 Sector dismissal rate at MTD `[NEW]`
- 7.1.3 Sector median settlement `[NEW]`
- 7.1.4 Sector-specific plaintiff theories `[NEW]`
- 7.1.5 Industry Reference — D&O Tier Distribution `[LIVE — from Decision Record]`

### 7.2 Competitive Position
- 7.2.1 Competitive Position assessment `[LIVE — from Pattern Detection]`
- 7.2.2 Strategic Assessment `[LIVE — from Pattern Detection]`
- 7.2.3 Dimension Breakdown (AI risk dimensions) `[LIVE — from Pattern Detection]`
- 7.2.4 Peer SCA contagion (peers with active SCAs) `[LIVE]`

### 7.3 Macro & External Risk
- 7.3.1 Macro Risk Factors `[LIVE — from Forward-Looking]`
- 7.3.2 Tariff exposure `[LIVE]`
- 7.3.3 Tariff manufacturing locations `[HIDDEN]`
- 7.3.4 Geopolitical risk assessment `[LIVE — in risk factors]`

### 7.4 Sector-Specific Module (conditional on GICS)

#### 7.4.A BIOTECH / LIFE SCIENCES (GICS 35201010/35201020)
- 7.4.A.1 Pipeline Risk Map (program × phase × indication × catalyst × stock impact × % of MCap) `[NEW]`
- 7.4.A.2 FDA Regulatory Calendar (PDUFA dates, AdCom, CRL history) `[NEW]`
- 7.4.A.3 Cash Runway vs Catalyst Timeline (visual) `[NEW]`
- 7.4.A.4 Clinical trial status (from ClinicalTrials.gov) `[NEW]`
- 7.4.A.5 FDA pathway designations (Breakthrough, Fast Track, Priority Review, Accelerated) `[NEW]`
- 7.4.A.6 FDA Warning Letter / Form 483 history `[NEW]`
- 7.4.A.7 Disclosure quality — FDA interaction characterization `[NEW]`
- 7.4.A.8 Section 11 offering exposure (frequency of capital raises vs catalysts) `[NEW]`
- 7.4.A.9 Competitor pipeline overlap `[NEW]`
- 7.4.A.10 Patent cliff analysis (product patent expiry dates) `[NEW]`
- 7.4.A.11 Pricing/reimbursement risk `[NEW]`
- 7.4.A.12 Development stage risk calibration (dismissal %, settlement range by stage) `[NEW]`

#### 7.4.B TECHNOLOGY (GICS 4510/4520)
- 7.4.B.1 Revenue recognition risk (ASC 606 complexity, deferred revenue trends) `[NEW]`
- 7.4.B.2 Subscription/SaaS metrics (ARR, churn, net retention, LTV/CAC) `[NEW]`
- 7.4.B.3 AI capability claims vs delivery `[LIVE — AI risk section]`
- 7.4.B.4 Cybersecurity incident history & disclosure `[LIVE]`
- 7.4.B.5 Open source / IP litigation exposure `[NEW]`
- 7.4.B.6 Platform risk (antitrust, app store, marketplace) `[NEW]`
- 7.4.B.7 Data privacy / GDPR / CCPA exposure `[NEW]`

#### 7.4.C FINANCIAL SERVICES / BANKING (GICS 4010/4020/4030)
- 7.4.C.1 Net interest margin (NIM) trend `[NEW]`
- 7.4.C.2 Loan loss reserves / provision for credit losses `[NEW]`
- 7.4.C.3 Non-performing loans / charge-offs `[NEW]`
- 7.4.C.4 CET1 / Tier 1 capital ratio `[NEW]`
- 7.4.C.5 BSA/AML compliance `[NEW]`
- 7.4.C.6 FDIC/OCC/Fed enforcement history `[NEW]`
- 7.4.C.7 Stress test results (DFAST/CCAR) `[NEW]`
- 7.4.C.8 Fiduciary litigation exposure `[NEW]`

#### 7.4.D ENERGY (GICS 1010)
- 7.4.D.1 Reserve estimation methodology & revisions `[NEW]`
- 7.4.D.2 Environmental liabilities & remediation `[NEW]`
- 7.4.D.3 Commodity hedging positions `[NEW]`
- 7.4.D.4 Regulatory permits & compliance `[NEW]`
- 7.4.D.5 Climate disclosure / transition risk `[NEW]`

#### 7.4.E CANNABIS (GICS TBD)
- 7.4.E.1 Federal/state regulatory conflict `[NEW]`
- 7.4.E.2 License portfolio & renewal risk `[NEW]`
- 7.4.E.3 Banking access / cash handling `[NEW]`

---

## 8. SCORING & UNDERWRITING (the math and the recommendation)

### 8.1 Tier & Classification
- 8.1.1 Tier Classification + Why This Tier `[LIVE]`
- 8.1.2 Risk Type Classification `[LIVE]`

### 8.2 Scoring Model
- 8.2.1 10-Factor Scoring (waterfall chart) `[LIVE]`
- 8.2.2 Per-Factor Detail `[LIVE]`
- 8.2.3 D&O Claim Peril Assessment `[LIVE]`
- 8.2.4 Hazard Profile (Inherent Exposure Score) `[LIVE]`

### 8.3 Probability & Severity
- 8.3.1 Claim Probability (decomposition) `[LIVE]`
- 8.3.2 Severity Scenarios (tornado chart) `[LIVE]`
- 8.3.3 Tower Position Recommendation `[LIVE]`

### 8.4 Pattern Detection
- 8.4.1 Pattern Detection Engines (4 engines) `[LIVE]`
- 8.4.2 Forensic Composite Scores `[LIVE]`
- 8.4.3 Temporal Signals `[LIVE]`
- 8.4.4 Peril Map `[LIVE]`
- 8.4.5 Calibration Notes `[LIVE]`
- 8.4.6 ZER-001 Verifications `[LIVE]`

### 8.5 Forward-Looking Risk
- 8.5.1 Forward Scenarios & Monitoring Triggers `[LIVE]`
- 8.5.2 Management Credibility `[LIVE]`
- 8.5.3 Growth Estimates `[LIVE]`
- 8.5.4 Alternative Forward-Looking Signals `[LIVE]`
- 8.5.5 Early Warning Signals `[LIVE]`
- 8.5.6 Event Catalysts `[LIVE]`

### 8.6 Underwriting Action
- 8.6.1 Suggested Underwriting Posture `[LIVE]`
- 8.6.2 Meeting Preparation Questions `[LIVE]`
- 8.6.3 Peer risk comparison (score vs peers) `[MISSING]`
- 8.6.4 Historical score trend (this company over time) `[MISSING]`
- 8.6.5 Loss ratio contribution estimate `[MISSING]`
- 8.6.6 Exposure base (revenue or assets) `[MISSING]`
- 8.6.7 Rate adequacy indicators (rate per million, rate-on-line) `[MISSING — needs submission data]`

### 8.7 Scoring Checks
- 8.7.1 Forward-Looking Checks `[LIVE]`
- 8.7.2 Scoring Checks `[LIVE]`

---

## 9. AUDIT TRAIL (collapsed — reference only)

### 9.1 Sources
- 9.1.1 Sources & Provenance `[LIVE]`

### 9.2 Quality Assurance
- 9.2.1 QA / Audit Trail `[LIVE]`
- 9.2.2 Market Data — Full Detail `[LIVE]`

### 9.3 Data Coverage
- 9.3.1 Per-Section Coverage `[LIVE]`
- 9.3.2 Data Gaps `[LIVE]`
- 9.3.3 Blind Spot Discovery `[LIVE]`

### 9.4 Decision Record
- 9.4.1 Underwriting Decision Record `[LIVE]`
- 9.4.2 Underwriting Posture `[LIVE]`

### 9.5 Signal Trace
- 9.5.1 Epistemological Trace — Signal Provenance `[LIVE]`
- 9.5.2 Signal Disposition Audit `[LIVE]`
- 9.5.3 Per-Section Breakdown `[LIVE]`

---

## MANIFEST STATISTICS

| Status | Count |
|--------|-------|
| `[LIVE]` — currently displayed | 173 |
| `[HIDDEN]` — data exists, not displayed | 48 |
| `[MISSING]` — needs extraction/computation | 83 |
| `[NEW]` — new sections to build | 46 (mostly sector-specific) |
| `[PARTIALLY LIVE]` — partial data displayed | 4 |
| `[MANUAL INPUT]` — broker submission data | 18 |
| **TOTAL** | **372** |

### Gap Closure Priority

**Tier 0 — Submission Input (enables pricing/terms analysis):**
- 0.1–0.5: Broker submission data (MANUAL INPUT — build intake form)
- 8.6.7: Rate adequacy indicators (depends on submission data)

**Tier 1 — Highest impact (underwriter asks for this immediately):**
- 6.1.2–6.1.13: Litigation case detail (all None today)
- 4.4.2–4.4.10: Debt & Capital Structure (data hidden or missing)
- 1.5.6: Valuation multiples card
- 5.3.4–5.3.6: ECD XBRL compensation data (parser built, needs pipeline run)
- 3.6.1–3.6.4: Valuation section (data exists, not displayed)
- 4.8.7–4.8.11: Audit red flags (restatements, auditor changes, material weaknesses)
- 2.10.1–2.10.6: Corporate transactions & events (M&A, divestitures)

**Tier 2 — Important:**
- 4.3.3–4.3.4: Capital allocation & cash flow adequacy
- 5.2.5–5.2.10: Board detail (skills matrix, committee, expert, interlocks, overboarding)
- 5.5.4–5.5.6: D&O insurance, indemnification, ERISA exposure
- 5.6.6–5.6.9: Governance structure detail (forum selection, advance notice, consent rights)
- 7.1.1–7.1.4: Sector claim profile data
- 3.3.4–3.3.5: Stock drop corrective disclosure & market context
- 3.5.4, 3.5.6: Company guidance tracking
- 3.8.1, 3.8.5: IPO & SPAC analysis
- 6.4.8–6.4.12: Settlement exposure detail (market cap, turnover, DDL, defense counsel)
- 6.6.7–6.6.8: Coverage-specific exposure (insured-vs-insured, professional services)
- 8.6.5–8.6.7: Pricing indicators

**Tier 3 — Differentiating:**
- 7.4.A.*: Biotech module (12 items)
- 7.4.B.*: Technology module (7 items)
- 3.10.2–3.10.3: Institutional ownership changes, index membership
- 8.6.3–8.6.4: Peer risk comparison, historical score trend
- 2.1.5, 2.1.7, 2.1.9: Incorporation state, ADR, SPAC status
- 2.4.5: International operations footprint
- 2.8.9: Anti-corruption exposure
- 5.3.11–5.3.12: Equity vesting, employment agreements
- 5.4.8: Scienter correlation
- 6.1.12–6.1.13: Transaction-related & multi-jurisdictional litigation
