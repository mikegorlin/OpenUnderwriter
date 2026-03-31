# Brain Section Questions — Final v6

**Based on:** v5.1 review draft, incorporating user review feedback (2026-02-20).
**Status:** APPROVED — canonical reference for all subsequent plans (enrichment remapping, check classification, gap detection, brain CLI).
**Audit basis:** Every question verified against 388 current checks + 594 old system checks + 287 scoring rules (1,097 total).

## Review Decisions

User reviewed all 5 sections of the v5.1 question framework on 2026-02-20. Key decisions:

1. **Automation feasibility filter** -- Removed 9 questions requiring internal/policy access (board protocols, ICFR workpapers, whistleblower hotline, D&O questionnaires, officer oversight, management review controls, manual journal entries, consent to counsel, Side A adequacy). Moved to DEFERRED table.
2. **Insider trading relocation** -- Moved 7 insider trading questions from Section 4 (GOVERNANCE) to Section 2 (MARKET) as subsection 2.8. Rationale: insider trading is market signal data, not governance structure.
3. **Governance reframing** -- Reframed governance questions to prioritize: experience > litigation history > turnover trends > negative publicity. Diversity as standalone metric removed; board qualification and oversight effectiveness emphasized.
4. **Stock drop thresholds** -- Lowered single-day threshold from 8% to 5%, multi-day from 15% to 10%. Extended window from 12 to 18 months for full policy period context.
5. **Trend analysis required** -- Short interest and institutional ownership questions require 6-12 month trend analysis, not just current snapshots.
6. **Runoff/tail deferred** -- Section 5.10 (runoff/tail coverage analysis) deferred to future version; valuable for M&A transactions but not needed for v1.
7. **Identity expansion** -- Questions 1.1.1-1.1.5 expanded to capture SIC, NAICS, GICS codes, state of incorporation, exchange listing, FPI status upfront.
8. **SCORING clarification** -- Base D&O exposure and size-adjusted risk explicitly marked as SCORING outputs (inherent risk), not COMPANY identity inputs.
9. **Data Feasibility principle** -- Added as cross-cutting principle: every question must be answerable from SEC filings + web search + MCP tools.
10. **Granularity Rule** -- Added as cross-cutting principle: bundling related metrics into one question preferred over over-splitting. One question = one analytical judgment call.
11. **Subsection renumbering** -- Sections 4-5 renumbered after insider trading relocation and removals (e.g., old 4.7 Disclosure -> 4.6, old 4.8 Narrative -> 4.7, etc.).

---

## Cross-Cutting Principles

**Peer Comparison** — Not a standalone section. Peer comparison is a METHOD applied within every section:
- COMPANY: peer competitive position, peer litigation frequency
- MARKET: peer-relative stock performance, peer valuation multiples, peer insider trading patterns
- FINANCIAL: peer-relative margins, leverage, sector-calibrated thresholds
- GOVERNANCE: peer-relative CEO pay, board structure, executive experience
- LITIGATION: peer lawsuit frequency, sector allegation patterns

**Data Feasibility** — Every question must be answerable from SEC filings + web search + MCP tools (EdgarTools, Brave/Google Search, Playwright, Fetch). If we can't programmatically acquire the data, the question is aspirational, not operational.

**Sector Calibration** — Every threshold-based check must use sector-calibrated values, not universal cutoffs. The knowledge database stores per-sector thresholds for RED/YELLOW/CLEAR status. "Is leverage high?" means nothing without "...for this sector."

**Granularity Rule** — One question = one analytical judgment call. If the underwriter would reach two independent conclusions, they're two questions. If metrics are always evaluated together, bundle them.

---

## Section Boundaries

| # | Section | Owns |
|---|---|---|
| 1 | **COMPANY** | Entity identity, business model, operations, structure, geography, M&A, competitive position, macro environment, employee signals, customer signals, risk calendar |
| 2 | **MARKET** | Stock price, volatility, trading patterns, short interest, ownership structure, analyst coverage, valuation, insider trading activity |
| 3 | **FINANCIAL** | Liquidity, leverage, profitability, earnings quality, forensic analysis, distress indicators, guidance credibility, audit/accounting integrity, sector-specific KPIs |
| 4 | **GOVERNANCE & DISCLOSURE** | Board, executives, compensation, shareholder rights, activist pressure, disclosure quality, narrative analysis, whistleblower signals, media/external narrative |
| 5 | **LITIGATION & REGULATORY** | Securities class actions, regulatory enforcement, derivative suits, non-securities litigation, defense posture, litigation patterns, sector-specific regulatory |

---

# 1. COMPANY

## 1.1 Identity
*What is this company?*

- 1.1.1 What industry is this company in? (SIC, NAICS, GICS codes and sector/industry classification)
- 1.1.2 What are the key company metrics? (Market cap, enterprise value, employee count, revenue, headquarters)
- 1.1.3 What lifecycle stage is this company in (IPO, growth, mature, distressed, SPAC)?
- 1.1.4 What is the state of incorporation and what legal regime applies?
- 1.1.5 What exchange is it listed on and is it a Foreign Private Issuer?

*Note: Base D&O exposure for sector and size-adjusted risk are SCORING outputs (inherent risk), not identity inputs.*

## 1.2 Business Model & Revenue
*How does this company make money?*

- 1.2.1 What is the company's primary business model and revenue type?
- 1.2.2 How is revenue broken down by segment?
- 1.2.3 What are the key products/services and how concentrated is the product portfolio?
- 1.2.4 What is the cost structure and operating leverage?
- 1.2.5 What is the recurring vs non-recurring revenue mix?
- 1.2.6 Is there an "Innovation/Investment Gap" — does the company's public AI/tech narrative diverge from actual R&D/CAPEX spend?

## 1.3 Operations & Dependencies
*What does this company depend on to operate?*

- 1.3.1 How concentrated is the customer base?
- 1.3.2 How dependent is the company on key suppliers or single-source inputs?
- 1.3.3 How complex and vulnerable is the supply chain?
- 1.3.4 What is the workforce profile and labor risk?
- 1.3.5 What technology, IP, or regulatory dependencies exist?
- 1.3.6 What is the government contract exposure?
- 1.3.7 What is the data/privacy risk profile? (PII, PHI, financial, children's data; CCPA, GDPR, HIPAA)
- 1.3.8 Does the company have sector-specific hazard exposure? (Binary flags: Opioid, PFAS, Crypto, Cannabis, China VIE, AI/ML, Nuclear/defense, Social media/content)
- 1.3.9 Is there ESG/greenwashing risk?

## 1.4 Corporate Structure & Complexity
*How is this company organized?*

- 1.4.1 How many subsidiaries and legal entities exist?
- 1.4.2 Are there VIEs, SPEs, or off-balance-sheet structures?
- 1.4.3 Are there related-party transactions or intercompany complexity?

## 1.5 Geographic Footprint
*Where does this company operate and what jurisdictional risks exist?*

- 1.5.1 Where does the company operate (countries/regions)?
- 1.5.2 What jurisdiction-specific risks apply (FCPA, GDPR, sanctions, export controls)?

## 1.6 M&A & Corporate Transactions
*What deal activity has there been and what's pending?*

- 1.6.1 Are there pending M&A transactions?
- 1.6.2 What is the 2-3 year acquisition history (deal sizes, rationale, integration)?
- 1.6.3 How much goodwill has accumulated and is there impairment risk?
- 1.6.4 What is the integration track record?
- 1.6.5 Has there been deal-related litigation?
- 1.6.6 Have there been divestitures, spin-offs, or capital markets transactions?

## 1.7 Competitive Position & Industry Dynamics
*How is this company positioned within its industry?*

- 1.7.1 What is the company's market position and competitive moat?
- 1.7.2 Who are the direct peers and how do they compare?
- 1.7.3 What is the peer litigation frequency (SCA contagion risk)?
- 1.7.4 What are the industry headwinds and tailwinds?

## 1.8 Macro & Industry Environment
*What external forces are creating risk?*

- 1.8.1 How is the sector performing overall and are peers experiencing similar issues?
- 1.8.2 Is the industry consolidating or facing disruptive technology threats?
- 1.8.3 What macro factors materially affect this company (rates, FX, commodities, trade, labor)?
- 1.8.4 Are there regulatory, legislative, or geopolitical changes creating sector risk?

## 1.9 Employee & Workforce Signals
*What are employees telling us about the company's health?*

- 1.9.1 What do employee review platforms indicate (Glassdoor, Indeed, Blind)?
- 1.9.2 Are there unusual hiring patterns (compliance/legal hiring surge)?
- 1.9.3 Are there LinkedIn headcount or departure trends?
- 1.9.4 Are there WARN Act or mass layoff signals?
- 1.9.5 What do department-level departures show? (Accounting/legal departures = stronger fraud signal)
- 1.9.6 What is the CEO approval rating trend? (Glassdoor CEO approval drop >20% = red flag)

## 1.10 Customer & Product Signals
*What are customers and the market experiencing?*

- 1.10.1 Are there customer complaint trends (CFPB, app ratings, Trustpilot)?
- 1.10.2 Are there product quality signals (FDA MedWatch, NHTSA complaints)?
- 1.10.3 Are there customer churn or partner instability signals?
- 1.10.4 Are there vendor payment or supply chain stress signals?
- 1.10.5 What do web traffic and app download trends show?
- 1.10.6 What does scientific/academic community monitoring reveal? (PubPeer, Retraction Watch, KOL sentiment — biotech/pharma)

## 1.11 Risk Calendar & Upcoming Catalysts
*What events are coming in the next policy year?*

- 1.11.1 When is the next earnings report and what's the miss risk?
- 1.11.2 Are there pending regulatory decisions (FDA, FCC, etc.)?
- 1.11.3 Are there M&A closings or shareholder votes?
- 1.11.4 Are there debt maturities or covenant tests in the next 12 months?
- 1.11.5 Are there lockup expirations or warrant expiry?
- 1.11.6 Are there contract renewals or customer retention milestones?
- 1.11.7 Are there litigation milestones (trial dates, settlement deadlines)?
- 1.11.8 Are there industry-specific catalysts (PDUFA dates, patent cliffs)?

---

# 2. MARKET

## 2.1 Stock Price Performance
*How has the stock performed?*

- 2.1.1 What's the stock's current position relative to its 52-week range?
- 2.1.2 What is the stock's volatility profile and how does it compare to sector/peers? (Beta, 90-day vol, calm vs wild characterization)
- 2.1.3 How does performance compare to the sector and peers?
- 2.1.4 Is there delisting risk?
- 2.1.5 Does the MD&A exhibit "Abnormal Positive Tone" relative to quantitative financial reality?

## 2.2 Stock Drop Events
*Have there been significant drops that could trigger litigation?*

- 2.2.1 Have there been single-day drops >=5% in the past 18 months?
- 2.2.2 Have there been multi-day decline events >=10%?
- 2.2.3 Were significant drops preceded by "Corrective Disclosures" (restatements, guidance withdrawals, auditor changes) that establish loss causation?
- 2.2.4 Has the stock recovered from significant drops, or is there a sustained unrecovered decline in the past 18 months?

## 2.3 Volatility & Trading Patterns
*What does trading behavior signal?*

- 2.3.1 What's the 90-day volatility and how does it compare to peers?
- 2.3.2 What's the beta?
- 2.3.3 Is there adequate trading liquidity?
- 2.3.4 Are there unusual volume or options patterns?

## 2.4 Short Interest & Bearish Signals
*Are sophisticated investors betting against this company?*

- 2.4.1 What's the short interest as % of float and what's the trend over the past 6-12 months?
- 2.4.2 Have there been activist short seller reports?

## 2.5 Ownership Structure
*Who owns the stock?*

- 2.5.1 What's the institutional vs insider vs retail ownership breakdown?
- 2.5.2 Who are the largest holders and what's the concentration?
- 2.5.3 What are the institutional ownership trends over the past 6-12 months?
- 2.5.4 Are there capital markets transactions creating liability windows? (Secondary offerings, ATM programs, convertible issuance)

## 2.6 Analyst Coverage & Sentiment
*What do professional analysts think?*

- 2.6.1 How many analysts cover this stock?
- 2.6.2 What's the consensus rating and recent changes?
- 2.6.3 What's the price target relative to current price?

## 2.7 Valuation Metrics
*Is the stock priced appropriately?*

- 2.7.1 What are the key valuation ratios (P/E, EV/EBITDA, PEG)?
- 2.7.2 How does valuation compare to peers?

## 2.8 Insider Trading Activity
*Are insiders buying or selling, and is the timing suspicious?*

- 2.8.1 What's the net insider trading direction?
- 2.8.2 Are CEO/CFO selling significant holdings?
- 2.8.3 What percentage of transactions use 10b5-1 plans?
- 2.8.4 Is there cluster selling (multiple insiders simultaneously)?
- 2.8.5 Is insider trading timing suspicious relative to material events?
- 2.8.6 Do executives pledge company shares as loan collateral?
- 2.8.7 Are there Form 4 compliance issues? (Late Section 16 filings, gift transactions timed before declines)

---

# 3. FINANCIAL

## 3.1 Liquidity & Solvency
*Can the company meet its near-term obligations? (Sector-calibrated thresholds apply)*

- 3.1.1 Does the company have adequate liquidity (current ratio, quick ratio, cash ratio)?
- 3.1.2 What is the cash runway — how many months before cash runs out?
- 3.1.3 Is there a going concern opinion from the auditor?
- 3.1.4 How has working capital trended over the past 3 years?

## 3.2 Leverage & Debt Structure
*How much debt does the company carry, and can they service it? (Sector-calibrated thresholds apply)*

- 3.2.1 How leveraged is the company relative to earnings capacity (D/E, Debt/EBITDA)?
- 3.2.2 Can the company service its debt (interest coverage)?
- 3.2.3 When does significant debt mature and is refinancing at risk?
- 3.2.4 Are there covenant compliance risks?
- 3.2.5 What is the credit rating and recent trajectory?
- 3.2.6 What off-balance-sheet obligations exist (operating leases, purchase commitments, guarantees)?

## 3.3 Profitability & Growth
*Is the business economically viable and growing?*

- 3.3.1 Is revenue growing or decelerating?
- 3.3.2 Are margins expanding, stable, or compressing?
- 3.3.3 Is the company profitable? What's the trajectory?
- 3.3.4 How does cash flow quality compare to reported earnings?
- 3.3.5 Are there segment-level divergences hiding overall trends?
- 3.3.6 What is the free cash flow generation and CapEx trend?

## 3.4 Earnings Quality & Forensic Analysis
*Are the financial statements trustworthy, or is there manipulation?*

- 3.4.1 Is there evidence of earnings manipulation (Beneish M-Score, Dechow F-Score)?
- 3.4.2 Are accruals abnormally high relative to cash flows?
- 3.4.3 Is revenue quality deteriorating (DSO expansion, Q4 concentration, deferred revenue)?
- 3.4.4 Is there a growing gap between GAAP and non-GAAP earnings?
- 3.4.5 What does the Financial Integrity Score composite indicate?
- 3.4.6 Are there specific revenue manipulation patterns? (Bill-and-hold, channel stuffing, side letters, round-tripping, POC manipulation, cookie jar reserves, big bath, Q4 concentration)
- 3.4.7 Is the Depreciation Index (DEPI) anomalous? (Depreciation rate slowing without disclosed asset mix change)

## 3.5 Accounting Integrity & Audit Risk
*Is the financial reporting reliable?*

- 3.5.1 Who is the auditor and what's their tenure and opinion?
- 3.5.2 Has there been a restatement, material weakness, or significant deficiency?
- 3.5.3 Has there been an auditor change, and why?
- 3.5.4 Are there SEC comment letters raising accounting questions?
- 3.5.5 What are the critical audit matters (CAMs)?
- 3.5.6 What is the non-audit fee ratio? (Non-audit > audit = independence compromised)
- 3.5.7 Are there PCAOB inspection findings for this auditor?

## 3.6 Financial Distress Indicators
*How close is this company to failure?*

- 3.6.1 What does the Altman Z-Score indicate? (Z < 1.8 in high-risk sector = SCORING gate trigger for Side A review)
- 3.6.2 What does the Ohlson O-Score (bankruptcy probability) show?
- 3.6.3 What does the Piotroski F-Score (fundamental quality) show?
- 3.6.4 Is the company in or approaching the "Zone of Insolvency"? (Triggers SCORING gate for Side A structure review)
- 3.6.5 What do credit market signals show? (CDS spreads, default probability, credit rating downgrades)
- 3.6.6 Is there active restructuring (debt renegotiation, operational restructuring, workforce reduction)?

## 3.7 Guidance & Market Expectations
*Is management credible in their forward communications?*

- 3.7.1 Does the company provide earnings guidance and what's the current outlook?
- 3.7.2 What's the guidance track record (beat/miss pattern)?
- 3.7.3 What's the guidance philosophy (conservative vs aggressive)?
- 3.7.4 How does analyst consensus align with company guidance?
- 3.7.5 How does the market react to earnings?

## 3.8 Sector-Specific Financial Metrics
*Which industry-specific financial metrics apply? (Sector-conditional — only applicable metrics evaluate)*

- 3.8.1 What are the applicable sector-specific KPIs and how do they compare to benchmarks?

| Sector | Key KPIs | Why They Matter for D&O |
|---|---|---|
| **SaaS/Cloud** | NRR, ARR growth, Rule of 40, logo churn, CAC payback, gross margin | Subscription economics reveal whether growth is durable or a guidance miss is coming |
| **Biotech/Pharma** | Pipeline stage mix, cash per remaining trial, probability-adjusted NPV, patent cliff | Binary outcomes create massive stock drops; cash runway is existential |
| **Banking** | NIM, NPL ratio, CET1 capital, loan-to-deposit, provision coverage, net charge-offs | Capital adequacy and loan quality are the core D&O signals |
| **Insurance** | Combined ratio, reserve development, investment yield, premium growth, loss ratio | Reserve deficiency is the #1 insurance D&O allegation |
| **REIT** | FFO/AFFO, NAV discount, occupancy rate, lease expiry profile, tenant quality | Occupancy decline = dividend cut = SCA |
| **Energy** | Reserve replacement ratio, finding costs, decline rate, breakeven price, ESG transition | Reserve write-downs create immediate stock impact |
| **Retail** | Same-store sales, inventory turns, e-commerce mix, store count trajectory, shrinkage | Same-store sales decline = core business deteriorating |
| **Mining/Materials** | Reserve grade, all-in sustaining cost, commodity price sensitivity, reclamation liability | Commodity cycle + reserve impairment + environmental liability |
| **Telecom/Media** | ARPU, subscriber churn, content spend efficiency, spectrum value, cord-cutting rate | Subscriber metrics are KPIs management guides on; misses trigger SCAs |
| **Automotive** | Vehicle deliveries, ASP trends, warranty reserves, EV transition metrics, recall frequency | Delivery guidance miss is the primary SCA trigger |
| **Fintech/Payments** | TPV growth, take rate, merchant churn, regulatory compliance spend, fraud rate | Rapid growth masking unit economics; regulatory risk |
| **Healthcare Services** | Revenue per admission, payor mix, reimbursement rate changes, occupancy, staffing ratios | CMS rate changes can crater margins overnight |
| **Construction/Engineering** | Backlog, book-to-bill, percentage-of-completion, change order rate, bonding capacity | POC revenue recognition is #1 construction fraud pattern |

**Sector-Calibrated Thresholds:**

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

- 4.1.1 How independent is the board?
- 4.1.2 Is the CEO also the board chair?
- 4.1.3 What's the board size and tenure distribution?
- 4.1.4 Do board members have relevant, demonstrated experience to oversee THIS company's industry and risks?
- 4.1.5 Is this a classified (staggered) board?
- 4.1.6 How engaged is the board (meeting frequency, attendance)?
- 4.1.7 What is the board committee structure? (Audit committee financial expert, comp committee independence, risk committee existence)
- 4.1.8 Is the Board Chair the immediate past CEO ("Successor Chair")?

## 4.2 Executive Team & Stability
*Are the right leaders in place, and is the team stable? (Priority: experience > litigation history > turnover > negative publicity)*

- 4.2.1 Do the CEO and key executives have relevant, demonstrated experience to run THIS company?
- 4.2.2 Have any executives or directors been sued, investigated, or subject to enforcement actions in prior roles at other companies?
- 4.2.3 Are there negative personal publicity signals for executives or directors? (Public scandals, reputational red flags)
- 4.2.4 What is the C-suite turnover trend and are there signs of management instability? (Rising departures, unplanned exits, short tenures, interim appointments)
- 4.2.5 Is there a succession plan for key roles?
- 4.2.6 Is there founder/key-person concentration risk?

*Note: These inputs feed a composite governance score in SCORING.*

## 4.3 Compensation & Alignment
*Is management incentivized to act in shareholders' interests?*

- 4.3.1 What's the CEO's total compensation and how does it compare to peers?
- 4.3.2 What's the compensation structure (salary vs bonus vs equity)?
- 4.3.3 What was the say-on-pay vote result?
- 4.3.4 Are performance metrics in incentive comp appropriate?
- 4.3.5 Are there clawback policies and what's their scope?
- 4.3.6 Are there related-party transactions or excessive perquisites?
- 4.3.7 What's the golden parachute/change-in-control exposure?
- 4.3.8 What are the executive stock ownership requirements?
- 4.3.9 What is the CEO pay ratio to median employee?
- 4.3.10 Are there compensation manipulation indicators? (Option spring-loading, backdating, excise tax gross-ups, single vs double triggers)

## 4.4 Shareholder Rights & Protections
*How well are shareholder rights protected?*

- 4.4.1 Does the company have a dual-class voting structure?
- 4.4.2 Are there anti-takeover provisions (poison pill, supermajority requirements)?
- 4.4.3 Is there proxy access for shareholder nominations?
- 4.4.4 What forum selection and fee-shifting provisions exist?
- 4.4.5 Have there been recent bylaw amendments?

## 4.5 Activist Pressure
*Is there activist investor activity creating governance instability?*

- 4.5.1 Are there Schedule 13D filings indicating activist intent?
- 4.5.2 Have there been proxy contests or board seat demands?
- 4.5.3 Are there shareholder proposals with significant support?
- 4.5.4 Is there a short activism campaign targeting governance?

## 4.6 Disclosure Quality & Filing Mechanics
*Is the company meeting its disclosure obligations?*

- 4.6.1 How have risk factors changed year-over-year?
- 4.6.2 Have new litigation-specific or regulatory risk factors appeared?
- 4.6.3 Have previously disclosed risks materialized?
- 4.6.4 Has the company filed on time (NT filings, date shifts)?
- 4.6.5 Is non-GAAP reconciliation adequate?
- 4.6.6 Is segment reporting consistent?
- 4.6.7 Is related-party disclosure complete?
- 4.6.8 Is the guidance methodology transparent?
- 4.6.9 Are 8-K event disclosures timely and complete? (Item 1.05 cyber, Item 4.01 auditor, Item 5.02 exec departure)

## 4.7 Narrative Analysis & Tone
*What does the language reveal about management's confidence?*

- 4.7.1 Has the MD&A readability changed (Fog Index)?
- 4.7.2 Has the negative tone shifted?
- 4.7.3 Is there increased hedging/qualifying language?
- 4.7.4 Are forward-looking statements decreasing?
- 4.7.5 Is the 10-K narrative consistent with earnings call messaging?
- 4.7.6 Is the investor-facing narrative consistent with SEC filings?
- 4.7.7 Is there analyst skepticism about management's story?
- 4.7.8 Are there short thesis narratives contradicting management?
- 4.7.9 What do auditor CAMs focus on, and has focus changed?
- 4.7.10 Are there red-flag phrases appearing for the first time in filings? ("Investigation", "subpoena", "material uncertainty")
- 4.7.11 Are risk factors boilerplate or company-specific?
- 4.7.12 What does earnings call Q&A analysis reveal? (Evasion patterns, deflection, "non-answers")
- 4.7.13 What does the full 10-K year-over-year diff show?
- 4.7.14 How does this company's disclosure compare to peer filings?
- 4.7.15 What is the management credibility score? (Forward statements vs actual outcomes)

## 4.8 Whistleblower & Investigation Signals
*Are there signals of internal problems?*

- 4.8.1 Is there whistleblower/qui tam language in filings?
- 4.8.2 Is there internal investigation language?
- 4.8.3 Are there signals of internal problems from public sources? (Special committee formation in 8-K/proxy, board-directed investigations, legal/compliance hiring spikes)

## 4.9 Media & External Narrative
*What are external observers seeing?*

- 4.9.1 What does social media sentiment indicate?
- 4.9.2 Is there investigative journalism activity?

---

# 5. LITIGATION & REGULATORY

## 5.1 Securities Class Actions (Active)
*Are there current SCAs, and how serious are they?*

- 5.1.1 Are there active securities class actions against this company?
- 5.1.2 What are the class periods, allegations, and case stage?
- 5.1.3 Who is lead counsel and what tier are they?
- 5.1.4 What is the estimated exposure (DDL and settlement range)?

## 5.2 Securities Class Action History
*What does the litigation track record tell us?*

- 5.2.1 How many prior SCAs has this company had?
- 5.2.2 What were the outcomes (dismissed, settled, amount)?
- 5.2.3 Is there a recidivist pattern (repeat filer)?
- 5.2.4 Are there pre-filing signals (law firm announcements, investigations)?

## 5.3 Derivative & Merger Litigation
*Are there non-SCA shareholder claims?*

- 5.3.1 Are there active derivative suits (Caremark, duty of loyalty)?
- 5.3.2 Are there merger objection lawsuits?
- 5.3.3 Has the company received any Section 220 (Books & Records) demands in the last 24 months?
- 5.3.4 Are there ERISA class actions (401k stock drop cases)?
- 5.3.5 Are there appraisal actions? (Delaware Section 262)
- 5.3.6 What derivative suit risk factors are present BEFORE a suit is filed?

## 5.4 SEC Enforcement
*Where is this company in the SEC enforcement pipeline?*

- 5.4.1 What stage is any SEC matter at (comment letters > inquiry > investigation > Wells > enforcement)?
- 5.4.2 Are there SEC comment letters, and what topics?
- 5.4.3 Has there been a Wells Notice?
- 5.4.4 What prior SEC enforcement actions exist?

## 5.5 Other Regulatory & Government
*What non-SEC enforcement exposure exists?*

- 5.5.1 Which government agencies regulate this company?
- 5.5.2 Are there active DOJ investigations?
- 5.5.3 Are there state AG investigations or multi-state actions?
- 5.5.4 Are there industry-specific enforcement actions (FDA, EPA, OSHA, FTC, CFPB)?
- 5.5.5 Are there foreign government enforcement matters (UK SFO, EU Commission)?
- 5.5.6 Are there congressional investigations or subpoenas?

## 5.6 Non-Securities Litigation
*What is the aggregate non-SCA litigation landscape?*

- 5.6.1 What is the aggregate active litigation count?
- 5.6.2 Are there significant product liability, employment, IP, or antitrust matters?
- 5.6.3 Are there whistleblower/qui tam actions?
- 5.6.4 Are there cyber breach or environmental litigation matters?

## 5.7 Defense Posture & Reserves
*How well positioned is the company to defend against claims?*

- 5.7.1 What defense provisions exist (federal forum, PSLRA safe harbor)?
- 5.7.2 What are the contingent liabilities and litigation reserves (ASC 450)?
- 5.7.3 What is the historical defense success rate?

## 5.8 Litigation Risk Patterns
*What systemic litigation patterns apply?*

- 5.8.1 What are the open statute of limitations windows?
- 5.8.2 What industry-specific allegation theories apply?
- 5.8.3 What is the contagion risk from peer lawsuits?
- 5.8.4 Do financial events temporally correlate with stock drops to create class period windows?

## 5.9 Sector-Specific Litigation & Regulatory Patterns
*What sector-specific patterns and regulatory databases apply? (Sector-conditional)*

- 5.9.1 What sector-specific litigation patterns apply to this company?

| Sector | Primary D&O Allegation Theories | Typical Triggers |
|---|---|---|
| **SaaS/Cloud** | Revenue recognition (ASC 606), customer metrics inflation, churn concealment | NRR decline, logo churn spike, deferred revenue changes |
| **Biotech/Pharma** | Clinical trial data manipulation, FDA submission failures, off-label promotion, "Overpromise & Underdeliver" | Failed trial, CRL, safety signal, PubPeer findings, binary event reliance |
| **Banking** | Loan quality misrepresentation, BSA/AML failures, consumer fraud (UDAAP), redlining | NPL spike, consent order, CFPB action, DOJ fair lending |
| **Insurance** | Reserve deficiency, investment portfolio losses, excess commission, claims handling | Reserve strengthening, combined ratio deterioration, AM Best downgrade |
| **Energy** | Reserve write-downs, environmental liability concealment, ESG/climate greenwashing | Commodity price crash, EPA action, climate litigation |
| **Retail** | Same-store sales manipulation, inventory valuation, e-commerce overpromise | Comp miss, inventory write-down, store closure wave |
| **Tech/Hardware** | Product defect concealment, IP theft, antitrust, supply chain disruption concealment | Product recall, import ban (ITC), EU DMA fine |
| **Healthcare** | False Claims Act/Anti-Kickback, Stark Law, opioid liability, patient safety | DOJ/OIG investigation, CMS exclusion, whistleblower qui tam |
| **Mining/Materials** | Environmental contamination (PFAS/Superfund), mine safety, reserve overstatement | EPA order, MSHA fatality, commodity crash + impairment |
| **Automotive** | Safety defect concealment, emissions fraud, delivery/production guidance miss | NHTSA investigation, recall, delivery miss |
| **Fintech/Payments** | Unlicensed money transmission, consumer harm, BSA/AML, data breach | State enforcement, CFPB action, federal indictment |
| **Construction** | Percentage-of-completion fraud, cost overrun concealment, safety violations | DOJ False Claims, OSHA fatality, project write-down |

- 5.9.2 What do sector-specific regulatory databases show?

| Sector | Regulatory Databases | What They Catch Early |
|---|---|---|
| **Pharma/Biotech/Devices** | FDA Warning Letters, 483 Observations, Import Alerts, Recalls, MAUDE, ClinicalTrials.gov | Manufacturing quality, safety signals, trial problems |
| **Banking/Financial** | OCC orders, FDIC orders, CFPB complaints, Fed enforcement, FinCEN, state regulators | Consumer harm, BSA/AML deficiencies, capital issues |
| **Energy/Chemicals** | EPA ECHO (SNC status, HPV violations), air/water permits, Superfund, TRI releases | Environmental violations before major enforcement |
| **Mining** | MSHA violations, fatalities, pattern of violations, S&S citations | Safety culture deterioration |
| **Automotive** | NHTSA complaints, investigations, recalls, early warning reports, TSBs | Safety defect patterns before recall |
| **Consumer Products** | CPSC recalls, complaints, import violations | Product safety before class action |
| **Healthcare** | CMS sanctions, OIG exclusions, state health department actions | Billing/quality issues before FCA |
| **All sectors** | OSHA violations, fatalities, EEOC charges, DOL wage/hour, state AG complaints | Workplace safety, employment, consumer protection |

---

# PROCESS INSIGHTS (Implementation Guidance — Not Questions)

1. **PURPLE status** — Distinguish "checked and clear" from "not checked." Prevents false "all clear" when data is unavailable.

2. **Event-window attribution methodology** — For drops: 0/1/5/10-day sector-adjusted returns, cumulative market cap loss, recovery analysis. Maps directly to damages calculation.

3. **Nuclear trigger aggregation** — 3+ nuclear findings = auto-escalate. Not just "what's RED" but "how many and in what combination."

4. **Score to underwriting decision** — EXTREME (70-100, >20% probability, decline) > HIGH (50-69, 10-20%, 1.5-2x rate) > AVERAGE (30-49, 5-10%, market) > BELOW (15-29, 2-5%, discount) > MINIMAL (0-14, <2%, best rates).

5. **Underwriting Decision Logic Gates** — Sequential screens before final scoring:
    - **Gate 1: Insolvency Check** — Z-Score < 1.8 or critical default probability. Decline or require collateralization.
    - **Gate 2: Scienter Screen** — High TATA or abnormal DEPI. Debit Side C; restrict limits; higher retention.
    - **Gate 3: Governance Screen** — Combined CEO/Chair or Successor Chair. Debit Side A; require Lead Independent Director.
    - **Gate 4: Emerging Screen** — AI/ESG hype without internal controls. Refer for review; AI Disclosure warranty.
    - *Note: Consent to Counsel and Side A structure recommendations are policy-level outputs from these gates, not analysis inputs.*

6. **Actuarial Anchor** — Pre-analysis baseline profiling:
    - Market Cap Stratification: Micro (<$1B, insolvency/severity) vs Large Cap (>$10B, frequency)
    - Circuit Court Leniency: HQ in "High Severity" Circuit (9th, 2nd)? ~7% lower dismissal probability
    - Lifecycle Stage: De-SPAC (<36 months) or IPO? High Section 11 strict liability exposure

---

# DEFERRED (Revisit in Future Versions)

| Item | Why Deferred |
|---|---|
| 5.10 Runoff / Tail Coverage Analysis | Valuable for M&A transactions; not needed for v1 |
| Officer oversight protocols (McDonald's Check) | Requires internal documentation; keep as SCORING context |
| Board mission-critical risk protocols | Requires board minutes access |
| Management Review Controls precision | Requires ICFR workpapers |
| Manual journal entry override controls | Requires internal audit detail |
| D&O questionnaire off-cycle updates | Insurer process, not analysis |
| Risk officer reporting lines | Requires internal org chart |
| Whistleblower hotline Audit Committee review | Requires internal process access |

---

# Structural Relocation Map (v4 -> v5 -> v6)

For traceability — where each v4 section moved through v5 to final v6:

| v4 Section | v5 Location | v6 Location | Notes |
|---|---|---|---|
| 1. COMPANY (1.1-1.7) | 1. COMPANY (1.1-1.7) | 1. COMPANY (1.1-1.7) | Same, minor renumbering |
| 2. FINANCIAL (2.1-2.8) | 3. FINANCIAL (3.1-3.8) | 3. FINANCIAL (3.1-3.8) | Renumbered from 2->3 |
| 3. GOVERNANCE (3.1-3.6) | 4. GOV & DISCLOSURE (4.1-4.6) | 4. GOV & DISCLOSURE (4.1-4.5) | Renumbered; insider trading moved to 2.8 |
| 4. LITIGATION (4.1-4.9) | 5. LIT & REGULATORY (5.1-5.10) | 5. LIT & REGULATORY (5.1-5.9) | Runoff/tail deferred |
| 5. MARKET (5.1-5.7) | 2. MARKET (2.1-2.7) | 2. MARKET (2.1-2.8) | Added 2.8 insider trading from GOV |
| 6. DISCLOSURE (6.1-6.6) | 4. GOV & DISCLOSURE (4.7-4.9) | 4. GOV & DISCLOSURE (4.6-4.9) | Renumbered within section 4 |
| 7.1 Catalyst Events | 1.11 Risk Calendar | 1.11 Risk Calendar | Moved to COMPANY |
| 7.2 Employee Signals | 1.9 Employee Signals | 1.9 Employee Signals | Moved to COMPANY |
| 7.3 Customer Signals | 1.10 Customer Signals | 1.10 Customer Signals | Moved to COMPANY |
| 7.4 Macro & Industry | 1.8 Macro & Industry | 1.8 Macro & Industry | Moved to COMPANY |
| 7.5 Media Signals | 4.10 Media & External | 4.9 Media & External | Renumbered in v6 |
| 7.6 Regulatory Databases | 5.9 Sector Litigation | 5.9 Sector Litigation | Moved to LITIGATION |
| 8.1 Sector KPIs | 3.8 Sector Financial | 3.8 Sector Financial | Embedded in FINANCIAL |
| 8.2 Sector Thresholds | 3.8 (threshold table) | 3.8 (threshold table) | Embedded as principle |
| 8.3 Sector Litigation | 5.9 Sector Litigation | 5.9 Sector Litigation | Embedded in LITIGATION |
| 8.4 Sector Regulatory | 5.9 Sector Litigation | 5.9 Sector Litigation | Embedded in LITIGATION |
| 8.5 Sector Risk Profiles | 1.3.8 (binary flags) | 1.3.8 (binary flags) | Embedded in COMPANY |

---

# Mapping Audit Results

| Source | Total | Covered | Excluded | Sector | Scoring | Orphan |
|---|---|---|---|---|---|---|
| Our 388 checks | 388 | 365 | 6 | 15 | -- | 1 |
| Old system modules 01-04 | 206 | 152 | 23 | 24 | -- | 1 |
| Old system modules 05-07 | 210 | 174 | 36 | 0 | -- | 0 |
| Old system modules 08-10 | 293 | 117 | 61 | 4 | 111 | 0 |
| **TOTAL** | **1,097** | **808 (73.7%)** | **126 (11.5%)** | **43 (3.9%)** | **111 (10.1%)** | **2 (0.2%)** |

- **808 COVERED** -- map to a specific question in this framework
- **126 EXCLUDED** -- documented in "Chose Not To" tables or redundant with better questions
- **43 SECTOR** -- sector-specific checks now embedded in sections 3.8 and 5.9
- **111 SCORING** -- point assignment rules belonging in SCORE stage, not analysis questions
- **2 ORPHAN** -- added as new questions (3.6.6 restructuring, 5.8.4 class period windows)
- **0 UNACCOUNTED** -- every check from both systems is mapped

---

# Summary

| Section | Subsections | Questions |
|---|---|---|
| **1. COMPANY** | 11 | 59 |
| **2. MARKET** | 8 | 31 |
| **3. FINANCIAL** | 8 | 42 |
| **4. GOVERNANCE & DISCLOSURE** | 9 | 62 |
| **5. LITIGATION & REGULATORY** | 9 | 37 |
| **TOTAL** | **45** | **231** |

**Changes from v5.1 (225) to v6 (231):**
- Removed 9 questions (automation infeasible -- require internal/policy access)
- Moved 7 insider trading questions from Section 4 to Section 2
- Merged short interest level + trend (2 questions -> 1)
- Deferred runoff/tail section (5.10)
- Added 1 new question (4.2.3 negative personal publicity)
- Reframed/strengthened 12 existing questions
- Renumbered subsections in Sections 4-5 after reorganization

**v6 net: 231 questions across 5 sections, 45 subsections** (tighter boundaries, more automatable framework)
