# D&O Underwriting Hazard Dimensions: Comprehensive Taxonomy

**Date:** 2026-02-11
**Purpose:** Define the full landscape of D&O liability *hazard* dimensions -- the inherent conditions and characteristics that make a company more or less likely to generate D&O claims, independent of whether anything has actually gone wrong yet.
**Audience:** Experienced D&O underwriter; system architects building an automated hazard profiling engine.

---

## Executive Summary

Traditional D&O underwriting evaluates two conceptually distinct layers of risk:

1. **Hazards** (this document): The inherent exposure conditions -- business model, people, structure, environment -- that create the baseline probability and severity of a D&O claim. These exist even when all behavioral signals are clean.
2. **Signals** (covered elsewhere): Evidence that something IS going wrong -- financial distress indicators, governance failures, insider selling patterns, M-Score anomalies, etc.

The distinction matters because a clean company can still be highly exposed. A pre-revenue biotech with a first-time public company CEO in the middle of a bull market has enormous inherent exposure -- even if every signal today reads green. The hazard profile tells the underwriter: "This is the starting point. Everything else adjusts from here."

This research identifies **7 major hazard categories** containing **47 specific hazard dimensions**, proposes a weighted scoring framework, and maps each dimension to its data source for automated extraction.

---

## 1. The Hazard vs. Signal Distinction

### Definition

| Concept | Definition | D&O Example | Temporal Nature |
|---------|-----------|-------------|-----------------|
| **Hazard** | A condition or characteristic that increases the likelihood or severity of a loss. Exists independently of any actual loss event. | "This is a fast-growing biotech with a first-time public company CEO and operations in 6 countries." | Persistent structural condition. Changes slowly. |
| **Signal** | An observable indicator that a loss may be imminent or in progress. Evidence of a developing problem. | "The Beneish M-Score is above -1.78, insiders sold $50M in stock last quarter, and the auditor issued a going-concern opinion." | Transient event-driven. Changes rapidly. |
| **Peril** | The actual cause of loss -- the lawsuit itself. | "Securities class action filed alleging Section 10(b) violations related to clinical trial disclosures." | Discrete event. |

### Why This Distinction Matters for Underwriting

The traditional insurance framework defines:
- **Physical hazard**: A tangible condition increasing loss probability (P&C: wooden building near forest)
- **Moral hazard**: Intentional actions that increase loss probability (P&C: arson for insurance)
- **Morale hazard**: Carelessness induced by having insurance (P&C: not locking doors because insured)

In D&O liability, these translate to:
- **Structural hazard** (analog of physical hazard): Business model complexity, industry regulation density, geographic footprint, financial structure -- conditions that inherently create more surfaces for claims
- **Behavioral hazard** (analog of moral hazard): Tone at the top, corporate culture, management self-dealing tendencies -- characteristics of the people that increase loss probability
- **Governance hazard** (analog of morale hazard): Weak oversight structures that allow problems to develop unchecked -- board independence, committee quality, accountability mechanisms

### The Clean Company Problem

Consider two companies with identical, clean signal profiles (no red flags triggered):

| Characteristic | Company A | Company B |
|---------------|-----------|-----------|
| Industry | Electric utility, single state | Pre-revenue biotech |
| Revenue model | Regulated rate base | None (R&D stage) |
| CEO experience | 25 years in industry, 10 as CEO of public utility | First-time CEO, promoted from VP of R&D |
| Board | 10 independent directors, 4 committee chairs with 15+ years public company experience | 5 directors, 2 are investors, board formed 18 months ago |
| Geography | Single state | US + 3 international clinical trial sites |
| Regulatory intensity | 1 primary regulator (PUC) | FDA, EMA, SEC, potentially CFPB |
| Growth trajectory | 2% annual | 40% headcount growth, burning $200M/year |
| IPO age | Listed since 1952 | IPO 14 months ago |
| Capital structure | Investment grade, 40% debt/cap | No debt, $800M cash, 18-month runway |

**Every behavioral signal could be identical and green.** Yet Company B's inherent exposure is 10-20x Company A's. The hazard profile captures this gap.

**Academic support**: Kim & Skinner (2012) in "Measuring Securities Litigation Risk" (Journal of Accounting and Economics) demonstrated that firm characteristics -- industry membership, size, growth, stock volatility -- predict litigation risk more effectively than governance quality metrics or behavioral indicators. Their model using only structural characteristics achieves strong predictive power, and adding governance/behavioral variables contributes "relatively little" additional explanatory value.

Source: Kim, I. & Skinner, D.J. (2012). "Measuring Securities Litigation Risk." *Journal of Accounting and Economics*, 53(1), 290-310.

---

## 2. Hazard Category Taxonomy

### Overview of 7 Hazard Categories

| # | Category | Dimensions | Weight (Proposed) | Core Question |
|---|----------|-----------|-------------------|---------------|
| H1 | Business & Operating Model | 13 | 25% | What about this business makes it inherently exposed? |
| H2 | People & Management | 8 | 15% | What about these people creates inherent exposure? |
| H3 | Financial Structure | 8 | 15% | What about the financial structure creates exposure? |
| H4 | Governance Structure | 8 | 15% | What about the governance creates exposure? |
| H5 | Public Company Maturity | 5 | 10% | How seasoned is this company in the public markets? |
| H6 | External Environment | 7 | 10% | What external conditions amplify exposure? |
| H7 | Emerging / Modern Hazards | 6 | 10% | What new-era exposures exist? |
| | **Total** | **55** | **100%** | |

*Note: Some dimensions overlap with the existing Inherent Risk Baseline (INHERENT_RISK_BASELINE_RESEARCH.md) which covers actuarial frequency/severity drivers (market cap, industry, IPO age). This taxonomy is broader -- it captures ALL hazard dimensions including those that affect claim type, defense costs, and settlement dynamics, not just filing probability.*

---

## 3. H1: Business & Operating Model Hazards

These are characteristics of the business itself -- what it does, how it makes money, where it operates -- that create inherent D&O exposure surfaces.

### H1-01: Industry Sector Risk Tier

**What it measures:** The inherent litigation rate associated with the company's primary industry.

**Why it matters:** Industry sector is the second-most-important predictor of securities litigation frequency after market cap (Kim & Skinner 2012). Certain industries face structurally higher claim rates due to the nature of their operations, regulatory environment, and investor expectations.

**Risk tiers by industry:**

| Risk Tier | Industries | Approximate Annual SCA Filing Rate | Key Claim Drivers |
|-----------|-----------|-----------------------------------|-------------------|
| EXTREME | Biotech/Pharma (pre-revenue), Cannabis, SPAC vehicles | 8-10%+ | Clinical trial binary outcomes, regulatory approval/rejection, revenue legitimacy |
| VERY HIGH | Technology, Cryptocurrency/Digital assets | 6-8% | Revenue recognition complexity, hypergrowth metrics inflation, rapid valuation shifts |
| HIGH | Financial services (banking, insurance), Healthcare services | 4-6% | Regulatory density, reserve adequacy, lending practices, billing fraud |
| MODERATE | Consumer goods, Telecommunications, Media/Entertainment | 3-4% | Consumer-facing claims, subscriber metrics, content valuation |
| LOW | Industrial, Energy (mature), Materials, Transportation | 2-3% | Cyclical but predictable, established disclosure frameworks |
| VERY LOW | Utilities, REITs (core), Basic materials | 1-2% | Regulated rate base, stable cash flows, limited growth expectations |

**Data sources:**
- SIC/NAICS code from SEC EDGAR CIK lookup
- Stanford Securities Class Action Clearinghouse industry filing data
- Cornerstone Research annual filings report (2024: 225 total filings; tech + biotech = 37%)

**Scoring:** 0-10 scale based on industry filing rate relative to market average of ~3.9%

Sources: Cornerstone Research, "Securities Class Action Filings -- 2024 Year in Review" (2025); NERA Economic Consulting, "Recent Trends in Securities Class Action Litigation: 2024 Full-Year Review" (2025); Stanford Securities Class Action Clearinghouse.

---

### H1-02: Business Model Complexity

**What it measures:** How difficult the business is to understand, explain, and evaluate from the outside.

**Why it matters:** Complex business models create information asymmetry between management and investors. When something goes wrong, plaintiffs argue "management knew the business was more complex than they disclosed." Complexity also increases the probability of honest mistakes that look like fraud after the fact.

**Complexity indicators:**

| Indicator | LOW Complexity | MODERATE Complexity | HIGH Complexity |
|-----------|---------------|-------------------|----------------|
| Number of operating segments | 1 | 2-3 | 4+ |
| Revenue recognition methods | Single standard method | 2-3 methods (e.g., product + subscription) | Multiple methods with significant estimates (percentage of completion, long-term contracts, variable consideration) |
| Business model novelty | Well-established (retail, banking) | Evolving (SaaS, marketplace) | Novel/unproven (platform with network effects, token economics, two-sided marketplace with multiple monetization) |
| Analyst ability to model | Consensus estimates within tight band | Moderate estimate dispersion | Wide estimate dispersion, frequent model revisions |
| Related-party complexity | None | Minority JV interests | VIEs, unconsolidated entities, related-party revenue |
| Segment profitability variance | All segments profitable | Mix of profitable/breakeven | Cross-subsidized segments, loss leaders funding growth |

**Data sources:**
- Number of operating segments: 10-K segment reporting (ASC 280)
- Revenue recognition methods: 10-K Note on Revenue Recognition policies
- Analyst estimate dispersion: yfinance analyst data, earnings surprise history
- VIE/off-balance-sheet disclosures: 10-K notes

**Scoring:** 0-5 scale. Each HIGH indicator adds +1. Novel/unproven business model is +2.

---

### H1-03: Regulatory Intensity

**What it measures:** The number and power of regulatory bodies overseeing the company's operations, and the severity of non-compliance consequences.

**Why it matters:** Every regulator is a potential enforcement source. A banking CEO may answer to the OCC, FDIC, Fed, SEC, CFPB, and state regulators -- each with independent authority to investigate, fine, and refer for prosecution. More regulators = more potential claim vectors. D&O claims frequently follow regulatory enforcement actions (Allianz 2026: regulatory enforcement is a top claim driver for private D&O).

**Regulatory density spectrum:**

| Level | Description | Example Industries | Approx. # Primary Regulators |
|-------|------------|-------------------|-------------------------------|
| EXTREME | Multiple overlapping federal + state + international regulators with criminal referral authority | Banking, Securities firms, Pharma/Biotech | 5-8+ |
| HIGH | Multiple specialized federal regulators + state AGs active | Healthcare services, Energy (nuclear), Insurance, Defense contractors | 3-5 |
| MODERATE | Primary federal regulator + SEC + state consumer protection | Telecom, Food/Bev, Transportation, Tech (data privacy) | 2-3 |
| LOW | SEC + industry SRO + minimal specialized oversight | General manufacturing, Retail, SaaS (non-health/finance) | 1-2 |
| MINIMAL | Primarily SEC only | Pure software, Consulting, Services | 1 |

**Data sources:**
- SIC/NAICS → regulatory mapping (config-driven lookup)
- 10-K Item 1 "Regulation" section (length and complexity as proxy)
- 10-K Item 1A risk factor disclosures mentioning specific regulators
- FCPA-relevant jurisdiction count from geographic revenue breakdown

**Scoring:** 0-5 scale based on regulatory density level.

---

### H1-04: Geographic Complexity

**What it measures:** The number and risk level of jurisdictions where the company operates, with special attention to FCPA-risk countries and multi-jurisdictional regulatory exposure.

**Why it matters:** Geographic complexity multiplies regulatory surface area. Companies with operations in FCPA-high-risk countries face corruption prosecution risk. Multi-jurisdiction operations create disclosure complexity (transfer pricing, currency, tax) that can become the basis for securities claims. Chubb's multinational D&O analysis emphasizes that cross-border regulatory cooperation has increased, exposing directors to actions in multiple countries simultaneously.

**Geographic risk factors:**

| Factor | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| Countries of operation | 1-3 (developed) | 4-10 or any developing | 10+ or high-risk developing |
| FCPA-risk countries | None | 1-3 CPI < 50 countries | 4+ CPI < 50 countries |
| Revenue from outside home country | < 20% | 20-50% | > 50% |
| Local D&O policies required | 0 | 1-3 | 4+ |
| Sanctions-adjacent operations | None | Monitoring required | Active compliance program required |

**Data sources:**
- 10-K geographic revenue breakdowns
- Entity list from SEC EDGAR (subsidiary listing in Exhibit 21)
- Transparency International Corruption Perceptions Index for operating countries
- tax_havens.json config for tax structure complexity

**Scoring:** 0-5 scale. Each HIGH factor adds +1. FCPA-risk operations are +2.

Source: Chubb, "Global Risk Spotlight: Why Multinationals Must Carefully Consider Local D&O" (2020); FCPAméricas, "D&O and FCPA: What Underwriters Should Know" (2024).

---

### H1-05: Revenue Model Manipulation Surface

**What it measures:** How susceptible the company's revenue recognition model is to manipulation or aggressive accounting.

**Why it matters:** Revenue recognition is "the most important issue in D&O underwriting" according to The D&O Diary's analysis of what underwriters examine. Different revenue models create different manipulation surfaces -- long-term contracts with percentage-of-completion create more judgment calls than cash-register retail sales.

**Revenue model risk ranking:**

| Revenue Model | Manipulation Surface | Common Claim Theories | Risk Level |
|--------------|---------------------|----------------------|------------|
| Long-term contracts (% completion) | Estimated completion, cost-to-complete | Premature recognition, understated costs | VERY HIGH |
| Channel partner/distributor model | Channel stuffing, return reserves | Stuffing channels at quarter-end, manipulated sell-through | VERY HIGH |
| Subscription/SaaS (ARR-focused) | Metrics inflation (ARR, NRR, churn) | Inflated subscriber counts, backdated bookings | HIGH |
| License + services bundled | Allocation between elements | Premature license recognition, understated service obligations | HIGH |
| Advertising/platform (user metrics) | User/engagement metrics inflation | Inflated DAU/MAU, bot traffic misrepresentation | HIGH |
| Product sales (physical goods) | Bill-and-hold, cutoff manipulation | Quarter-end shipment timing, consignment misclassification | MODERATE |
| Government contracts (cost-plus) | Cost allocation, False Claims Act | Overbilling, mischarging, bid rigging | MODERATE |
| Subscription (traditional) | Deferred revenue timing | Early recognition of deferred revenue | LOW-MOD |
| Regulated rate base | Rate case filings | Rate case fraud, cost misallocation (rare) | LOW |
| Commodity sales (spot market) | Hedging complexity | Mark-to-market manipulation (Enron-era) | MODERATE |

**Data sources:**
- 10-K Revenue Recognition policy notes
- Revenue model type classification from business description
- ASC 606 disclosure analysis (performance obligations, contract assets/liabilities)
- Percentage of revenue from long-term contracts vs. spot

**Scoring:** 0-5 scale based on revenue model risk tier.

---

### H1-06: Customer & Supplier Concentration

**What it measures:** Revenue and supply chain dependency on a small number of counterparties.

**Why it matters:** High customer concentration creates "binary event" risk -- loss of a major customer can trigger a stock decline and securities litigation. High supplier concentration creates disclosure obligation risk (failure to disclose dependency). Government customer concentration adds False Claims Act exposure.

**Concentration thresholds:**

| Metric | LOW Risk | MODERATE Risk | HIGH Risk |
|--------|----------|---------------|-----------|
| Top customer as % of revenue | < 10% | 10-25% | > 25% |
| Top 5 customers as % of revenue | < 30% | 30-60% | > 60% |
| Single-source supplier dependency | None material | 1-2 identified | 3+ or critical component single-sourced |
| Government as % of revenue | < 10% | 10-30% | > 30% (False Claims Act exposure) |

**Data sources:**
- 10-K customer concentration disclosures (required for >10% customers)
- 10-K supply chain risk factor disclosures
- Government contract revenue from segment reporting
- FPDS (Federal Procurement Data System) for defense/government contractors

**Scoring:** 0-3 scale. Government dependency >30% adds +1 for FCA exposure.

---

### H1-07: Capital Intensity and CapEx Cycles

**What it measures:** The degree to which the business requires large, lumpy capital investments with long payback periods.

**Why it matters:** Capital-intensive businesses face disclosure risk around project cost overruns, delays, and impairments. Large CapEx programs create significant estimate-dependent accounting (capitalization vs. expense, useful life assumptions, impairment testing). The gap between spending and returns creates investor expectations that, if disappointed, drive litigation.

**Capital intensity indicators:**

| Metric | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| CapEx / Revenue | < 5% | 5-15% | > 15% |
| PP&E / Total assets | < 20% | 20-50% | > 50% |
| Major project risk | None | 1-2 multi-year projects | Bet-the-company projects |
| Construction/commissioning risk | Minimal | Standard expansion | Mega-projects (LNG, fab, pipeline) |

**Data sources:**
- 10-K financial statements (CapEx from cash flow statement, PP&E from balance sheet)
- MD&A discussion of capital programs
- yfinance financial data

**Scoring:** 0-3 scale.

---

### H1-08: M&A Activity and Integration Complexity

**What it measures:** The level and nature of acquisition activity, including deal frequency, size relative to the acquirer, and integration execution risk.

**Why it matters:** M&A activity is one of the top D&O claim generators. Financing activities and M&A activity are "the kinds of events that often generate claims" (Ames & Gough underwriting analysis). Serial acquirers face goodwill impairment risk; large transformative deals face integration disclosure risk; cross-border deals face regulatory and FCPA risk.

**M&A risk factors:**

| Factor | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| Deal frequency (3 years) | 0-1 | 2-4 | 5+ (serial acquirer) |
| Largest deal as % of market cap | < 10% | 10-30% | > 30% (transformative) |
| Goodwill as % of total assets | < 10% | 10-30% | > 30% (acquisition-driven growth) |
| Cross-border deals | 0 | 1-2 | 3+ |
| Earn-out structures | None | Standard | Complex multi-year earn-outs |
| Integration track record | History of successful integration | Mixed | History of write-downs |

**Data sources:**
- 10-K business combination disclosures (Note on Acquisitions)
- Goodwill and intangible assets from balance sheet
- Goodwill impairment history from income statement
- MD&A discussion of acquisitions and integration

**Scoring:** 0-5 scale. Goodwill > 30% of assets is +2.

---

### H1-09: Speed of Growth

**What it measures:** The rate at which the company is growing revenue, headcount, and operational footprint.

**Why it matters:** Hypergrowth companies make more errors because systems, controls, and personnel cannot keep pace with business expansion. Growth creates disclosure pressure (management wants to report impressive numbers), accounting complexity (new revenue streams, geographic expansion), and operational strain (control environment gaps). Companies growing >30% annually face materially elevated litigation risk.

**Growth rate risk tiers:**

| Revenue Growth Rate (3yr CAGR) | Risk Level | Rationale |
|-------------------------------|------------|-----------|
| Negative or <5% | LOW (but other risks -- distress, restructuring) | Stable but may signal other problems |
| 5-15% | LOW | Manageable growth within existing controls |
| 15-30% | MODERATE | Straining systems, hiring rapidly |
| 30-50% | HIGH | Controls likely lagging growth |
| >50% | VERY HIGH | "Move fast and break things" -- errors almost certain |
| Pre-revenue with cash burn | EXTREME (for biotech/startup) | Binary outcome risk |

**Data sources:**
- yfinance revenue growth data (3-year CAGR)
- Employee headcount growth from 10-K
- Operating segment growth rates from segment reporting
- Cash burn rate for pre-revenue companies

**Scoring:** 0-5 scale based on growth tier.

---

### H1-10: Dual-Class Share Structure

**What it measures:** Whether the company has a multi-class share structure that separates economic ownership from voting control.

**Why it matters:** Dual-class structures create misalignment between voting power and economic interest, enabling controller self-dealing. The EZCORP case illustrated the extreme -- management controlled 100% of voting power with 5.5% of economic interest. Dual-class companies face elevated derivative suit risk (+20-30% estimated), though the effect on securities class action frequency is ambiguous.

**Risk factors:**

| Factor | Risk Level |
|--------|------------|
| Single class, one-share-one-vote | NONE |
| Dual class with sunset provision (7-10 years) | MODERATE |
| Dual class without sunset, controller < 50% economic | HIGH |
| Dual class without sunset, controller < 20% economic | VERY HIGH |
| Multi-class with 3+ share classes | VERY HIGH |

**Data sources:**
- Proxy statement (DEF 14A) share structure disclosure
- SEC EDGAR filing type analysis (multi-class identified in registration statements)
- ISS governance data

**Scoring:** 0-3 scale. Dual class with economic/voting spread > 3x is +2.

Sources: Harvard Law School Forum on Corporate Governance (August 2024); SEC Investor Advisory Committee; Committee on Capital Markets Regulation, "The Rise of Dual Class Shares" (2020).

---

### H1-11: Reliance on Non-GAAP Metrics

**What it measures:** The extent to which the company emphasizes non-GAAP financial measures in its investor communications.

**Why it matters:** Heavy reliance on non-GAAP metrics (adjusted EBITDA, adjusted EPS, non-GAAP revenue, "community-adjusted EBITDA") creates disclosure litigation risk. Plaintiffs argue that non-GAAP emphasis is designed to obscure GAAP reality. The SEC has increased enforcement around non-GAAP metric abuse. Companies with large GAAP-to-non-GAAP divergence are more likely to face accounting-related claims.

**Risk indicators:**

| Indicator | LOW | MODERATE | HIGH |
|-----------|-----|----------|------|
| Non-GAAP metrics highlighted in earnings releases | 1-2 standard adjustments | 3-5 adjustments | 6+ adjustments or novel metrics |
| GAAP vs. non-GAAP divergence (net income) | < 20% | 20-50% | > 50% or different sign |
| Non-GAAP metric novelty | Industry-standard (adjusted EBITDA) | Company-specific but defensible | Company-invented metric with no peer comparison |
| SEC comment letter history on non-GAAP | None | 1 comment resolved | Repeat comments or unresolved |

**Data sources:**
- Earnings releases (8-K) -- non-GAAP reconciliation tables
- SEC EDGAR EDGAR Full-Text Search for non-GAAP comment letters
- Comparison of non-GAAP EPS to GAAP EPS over time

**Scoring:** 0-3 scale.

---

### H1-12: Technology Platform Dependency

**What it measures:** The degree to which the company depends on third-party technology platforms for distribution, revenue, or core operations.

**Why it matters:** Platform dependency creates "deplatforming" risk (Apple App Store policy changes, Google algorithm updates, Amazon marketplace rules) that can materially impact revenue. Failure to disclose this dependency, or changes in platform terms, can trigger securities claims.

**Risk factors:**

| Factor | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| Revenue from single platform | < 10% | 10-30% | > 30% |
| API dependency for core product | None critical | 1-2 APIs important | Core product breaks without 3rd-party API |
| Platform regulatory risk | Platform unregulated | Platform facing regulation | Platform under active antitrust action |

**Data sources:**
- 10-K risk factor disclosures mentioning platform dependencies
- Revenue concentration disclosures
- Business description analysis

**Scoring:** 0-2 scale.

---

### H1-13: Intellectual Property Dependency

**What it measures:** The degree to which company value depends on IP that could be challenged, expired, or circumvented.

**Why it matters:** Patent cliff risk (pharma), trade secret litigation (tech), and copyright challenges (media) create material disclosure obligations. Failure to adequately disclose IP risks -- especially upcoming patent expirations or pending IP litigation -- is a common securities claim theory.

**Risk factors:**

| Factor | LOW | HIGH |
|--------|-----|------|
| Patent cliff (revenue at risk from expiration) | None in 3 years | >20% revenue at risk within 3 years |
| Pending IP litigation as defendant | None material | Material litigation disclosed |
| Trade secret dependency for competitive moat | Low | High (key employee departures = risk) |

**Data sources:**
- 10-K IP disclosures
- Patent database searches
- Item 3 legal proceedings

**Scoring:** 0-2 scale.

---

## 4. H2: People & Management Hazards

These are characteristics of the management team and board that create inherent exposure through inexperience, mismatched capabilities, or structural dependencies on key individuals.

### H2-01: Management Team Public Company Experience

**What it measures:** The depth of experience the CEO, CFO, and other C-suite officers have in running publicly traded companies.

**Why it matters:** First-time public company executives are statistically more likely to make disclosure errors, mishandle earnings guidance, misjudge materiality thresholds, and struggle with the SEC reporting cadence. The transition from private-to-public is one of the highest-risk periods in a company's life. IPO companies with first-time management teams face compounded risk (IPO hazard + management hazard).

**Experience levels:**

| Role | LOW Risk | MODERATE Risk | HIGH Risk |
|------|----------|---------------|-----------|
| CEO | 10+ years public company C-suite experience | 3-10 years, or first CEO role at public company | First time at any public company |
| CFO | 10+ years public company CFO/controller experience | 3-10 years, or first CFO role | First time at public company, no Big 4 background |
| GC/CLO | Experienced securities lawyer, prior public company role | Some public company experience | First public company role, or no GC in place |
| Board overall | Majority have 10+ years public company board experience | Mixed experience levels | Majority are first-time public company directors |

**Data sources:**
- Proxy statement (DEF 14A) executive biographies
- LinkedIn profiles (via web search)
- SEC EDGAR filing history (search for prior roles in other company filings)
- Officer tenure data from proxy

**Scoring:** 0-5 scale. First-time public company CEO + first-time CFO = +4.

---

### H2-02: Industry Expertise Match

**What it measures:** Whether the CEO and CFO have deep experience in the company's specific industry.

**Why it matters:** A CEO brought in from a different industry must learn new regulatory frameworks, competitive dynamics, and industry-specific disclosure requirements. During this learning period, the risk of inadequate disclosure or misjudged materiality increases. The semiconductor industry has different disclosure norms than retail banking, and a new CEO from outside may not appreciate the nuances (e.g., book-to-bill ratios, inventory write-down triggers, export control compliance).

**Risk levels:**

| Situation | Risk Level |
|-----------|------------|
| CEO has 15+ years in same industry | LOW |
| CEO has 5-15 years in same industry | LOW-MODERATE |
| CEO from adjacent industry (e.g., pharma to biotech) | MODERATE |
| CEO from entirely different industry (e.g., consumer goods CEO at semiconductor company) | HIGH |
| CEO from PE/consulting with no operating experience in the industry | HIGH |

**Data sources:**
- Proxy statement executive biographies
- Prior company SIC codes vs. current company SIC code
- Web search for career history

**Scoring:** 0-3 scale.

---

### H2-03: Scale Experience Mismatch

**What it measures:** Whether the management team has experience operating at the current company's scale.

**Why it matters:** Managing a $500M revenue company is fundamentally different from managing a $15B revenue company. The control environment, reporting complexity, stakeholder management, and regulatory exposure scale non-linearly with company size. A CEO who was excellent at a small-cap may be overwhelmed at a large-cap.

**Risk indicators:**

| Metric | LOW Risk | HIGH Risk |
|--------|----------|-----------|
| CEO's prior company revenue vs. current | Within 2x | 5x+ difference |
| CEO's prior company market cap vs. current | Within 3x | 10x+ difference |
| CEO's prior company employees vs. current | Within 3x | 10x+ difference |
| Rapid scaling while in role | Revenue doubled in 3 years | Revenue 5x+ in 3 years |

**Data sources:**
- Proxy biography + prior company financials
- Current company growth trajectory
- Web search for prior role details

**Scoring:** 0-3 scale.

---

### H2-04: Board Governance Experience & Quality

**What it measures:** The collective experience, diversity of expertise, and oversight capability of the board.

**Why it matters:** An experienced, independent board is the primary defense against D&O claims. Boards with deep governance experience are more likely to catch problems early, push back on management, and establish effective compliance systems. The Boeing 737 MAX derivative settlement ($237.5M) was driven in part by allegations that the board lacked aviation safety expertise.

**Board quality indicators:**

| Indicator | STRONG | MODERATE | WEAK |
|-----------|--------|----------|------|
| Average board tenure (years) | 5-10 | 3-5 or 10-15 | < 3 (too new) or > 15 (entrenchment) |
| Directors with prior public company board experience | > 75% | 50-75% | < 50% |
| Directors with industry-specific expertise | > 50% | 25-50% | < 25% |
| Audit committee financial expert(s) | 2+ | 1 | None or questionable qualification |
| Overboarded directors (4+ boards) | None | 1-2 | 3+ |
| Board diversity (gender, background) | Multi-dimensional diversity | Some diversity | Homogeneous |
| Recent board refreshment (new directors in 3 years) | 2-3 | 1 | 0 (stale board) or 4+ (complete turnover) |

**Data sources:**
- Proxy statement (DEF 14A) director biographies, committee assignments
- ISS/Glass Lewis governance scores
- governance_weights.json thresholds

**Scoring:** 0-5 scale based on composite board quality assessment.

---

### H2-05: Founder-Led vs. Professional Management

**What it measures:** Whether the company is led by its founder(s) or by professional management hired post-founding.

**Why it matters:** Founder-led companies have a distinctive risk profile. Founders bring passion and vision but may resist board oversight, make decisions based on personal vision rather than shareholder value, and create key-person dependency. The "imperial CEO" dynamic is more common with founders. Conversely, founders often have deep domain expertise and long-term orientation that reduces short-term gaming.

**Risk profile:**

| Situation | Risk Profile |
|-----------|-------------|
| Founder CEO with professional CFO, strong board | MODERATE (vision risk offset by controls) |
| Founder CEO/Chair combined, board packed with loyalists | HIGH (concentrated power) |
| Non-founder professional CEO with founder on board | MODERATE (potential for founder interference) |
| Professional management, founders departed | LOW (standard corporate governance) |
| Founder CEO with dual-class control | VERY HIGH (no accountability mechanism) |

**Data sources:**
- Proxy statement
- Company history / founding information
- Share ownership structure

**Scoring:** 0-3 scale. Founder + combined CEO/Chair + dual-class = maximum.

---

### H2-06: Key Person Dependency

**What it measures:** The degree to which company value, customer relationships, or regulatory approvals depend on specific individuals.

**Why it matters:** Key person risk creates D&O exposure through: (1) succession planning failures that are disclosed late, (2) departure announcements that trigger stock declines and securities claims, (3) disability/death creating operational disruption. Companies must disclose material key-person risks, and failure to do so is itself a D&O hazard.

**Risk indicators:**

| Indicator | LOW | HIGH |
|-----------|-----|------|
| Named in 10-K as key person risk | Not mentioned | Specific individuals named |
| Revenue tied to individual relationships | < 10% | > 25% |
| Regulatory licenses in individual's name | None | Critical licenses individually held |
| Succession plan disclosed | Yes, named successor | No plan disclosed |
| Key person insurance in place | Yes | No or not disclosed |

**Data sources:**
- 10-K risk factor disclosures
- Proxy statement executive compensation (relative compensation as proxy)
- Key person insurance disclosures

**Scoring:** 0-3 scale.

---

### H2-07: Management Turnover and Stability

**What it measures:** Recent turnover in the C-suite and reasons for departures.

**Why it matters:** Rapid executive turnover is both a signal and a hazard. As a hazard, it indicates that the company's operating environment is challenging enough to drive away talent, and new executives face a learning curve during which errors are more likely. CFO departures within 2 years of appointment are particularly concerning.

**Turnover risk levels:**

| Metric | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| CEO tenure | > 5 years | 2-5 years | < 2 years or interim |
| CFO tenure | > 3 years | 1-3 years | < 1 year |
| C-suite departures in past 2 years | 0-1 | 2-3 | 4+ |
| Reason for departures | Retirement, planned succession | "Pursue other opportunities" | "Immediate resignation," "mutual agreement" |

**Data sources:**
- 8-K filings (Item 5.02 -- departure/appointment of officers)
- Proxy statement
- News search for departure circumstances

**Scoring:** 0-3 scale.

---

### H2-08: Tone at the Top / Corporate Culture Indicators

**What it measures:** Observable indicators of the corporate culture and management's attitude toward compliance, transparency, and accountability.

**Why it matters:** "Tone at the top" is a qualitative assessment that experienced underwriters make instinctively. Companies with promotional, aggressive cultures generate more claims because management pushes boundaries. Companies with conservative, compliance-focused cultures generate fewer. While difficult to quantify precisely, several observable indicators serve as proxies.

**Culture risk indicators:**

| Indicator | LOW Risk (Conservative) | HIGH Risk (Aggressive) |
|-----------|------------------------|----------------------|
| Earnings guidance specificity | Range or no guidance | Precise point estimates, frequently raised |
| Executive compensation structure | Balanced (salary + long-term equity) | Heavily revenue/growth-incentivized, cliff vesting |
| Insider trading patterns | Regular 10b5-1 plans | Irregular, large discretionary sales |
| PR/IR tone | Measured, caveated | Hyperbolic ("revolutionary," "game-changing") |
| SEC comment letter responsiveness | Prompt, thorough responses | Delayed or argumentative responses |
| Whistleblower reports | Robust reporting program | No program or history of retaliation |
| CEO public persona | Low-profile, operational focus | Celebrity CEO, frequent media, social media statements |

**Data sources:**
- Earnings call transcripts (tone analysis)
- Executive compensation from proxy (incentive structure analysis)
- SEC EDGAR comment letters
- Glassdoor/employee review sentiment
- News search for CEO public statements

**Scoring:** 0-3 scale. Qualitative, requires judgment.

---

## 5. H3: Financial Structure Hazards

These are characteristics of the company's financial structure that create inherent exposure surfaces for D&O claims, independent of current financial performance.

### H3-01: Leverage and Capital Structure Complexity

**What it measures:** The level of debt relative to equity, and the complexity of the debt structure.

**Why it matters:** Highly leveraged companies face covenant compliance risk, refinancing risk, and insolvency risk -- all of which generate D&O claims. Complex capital structures (convertible debt, mezzanine financing, PIK notes, warrant structures) create additional disclosure obligations and valuation complexity. Allianz 2026 reports that global insolvencies are projected at +24% above pre-pandemic averages, and underwriting scrutiny of balance sheet health has intensified.

**Risk indicators:**

| Metric | LOW | MODERATE | HIGH |
|--------|-----|----------|------|
| Debt/Equity ratio | < 0.5 | 0.5-1.5 | > 1.5 |
| Net Debt / EBITDA | < 2x | 2-4x | > 4x |
| Debt maturity concentration | Laddered over 5+ years | Some concentration within 2 years | > 40% maturing within 18 months |
| Covenant headroom (disclosed) | Comfortable (>25% buffer) | Moderate (10-25%) | Tight (< 10%) or not disclosed |
| Capital structure complexity | Senior secured only | Mix of secured, unsecured, converts | Multiple tranches, PIK, warrants, preferred |

**Data sources:**
- 10-K financial statements (debt schedule, covenant disclosures)
- Debt maturity profile from 10-K notes
- yfinance balance sheet data
- Rating agency reports (Moody's/S&P credit ratings)

**Scoring:** 0-5 scale.

Source: Allianz Commercial, "D&O Insurance Insights 2026" (2026).

---

### H3-02: Off-Balance Sheet Arrangements

**What it measures:** The extent of off-balance-sheet items including VIEs, operating leases (pre-ASC 842), unconsolidated JVs, and special-purpose entities.

**Why it matters:** Off-balance-sheet arrangements are the classic source of accounting-related securities claims (Enron). While ASC 842 brought many leases on-balance-sheet, VIEs, unconsolidated joint ventures, and guarantee arrangements still create disclosure risk. The complexity of determining consolidation creates room for both honest errors and manipulation.

**Risk indicators:**

| Indicator | LOW | HIGH |
|-----------|-----|------|
| Variable interest entities | None | VIEs identified, consolidation analysis required |
| Unconsolidated joint ventures | None or immaterial | Material JVs with complex profit-sharing |
| Guarantee obligations | None | Material guarantees of third-party debt |
| Contractual obligations not on B/S | Standard (operating leases, purchase commitments) | Complex or large relative to on-B/S |
| SPE / securitization structures | None | Active securitization program |

**Data sources:**
- 10-K Note on Variable Interest Entities
- 10-K Note on Commitments and Contingencies
- Off-balance-sheet arrangements disclosure (10-K Item 7A)

**Scoring:** 0-3 scale.

---

### H3-03: Goodwill-Heavy Balance Sheet

**What it measures:** The proportion of total assets represented by goodwill and acquired intangible assets.

**Why it matters:** High goodwill signals acquisition-driven growth where organic value creation may be insufficient to justify purchase prices. Goodwill impairment is inherently subjective -- determining fair value requires estimates of future cash flows and discount rates. PwC guidance notes that "navigating the goodwill impairment model can be complex, judgmental and often time intensive." Impairment announcements frequently trigger securities claims alleging management knew acquired businesses were worth less than carrying value.

**Risk tiers:**

| Goodwill / Total Assets | Risk Level | Rationale |
|-------------------------|------------|-----------|
| < 10% | LOW | Organic business, minimal impairment risk |
| 10-25% | MODERATE | Some acquisition activity, manageable |
| 25-40% | HIGH | Acquisition-dependent growth model |
| > 40% | VERY HIGH | Balance sheet dominated by purchase price allocation |

**Additional risk factor:** Goodwill already impaired in recent years is a signal (not hazard), but a pattern of acquisitions followed by impairments is a hazard -- it indicates the company's M&A process reliably overpays.

**Data sources:**
- Balance sheet: Goodwill, Intangible Assets
- Historical goodwill impairment charges from income statement
- M&A history from business combination notes

**Scoring:** 0-3 scale based on goodwill concentration.

---

### H3-04: Earnings Quality Characteristics

**What it measures:** The structural characteristics of the company's earnings that make them inherently more or less susceptible to manipulation, independent of whether manipulation is occurring.

**Why it matters:** Companies with earnings that rely heavily on estimates, accruals, and management judgment have more "moving parts" that can be adjusted to manage reported results. This is not about detecting manipulation (that is a signal) -- it is about recognizing that some earnings structures inherently have more surfaces for manipulation.

**Earnings quality hazard indicators:**

| Indicator | HIGHER Quality (Lower Hazard) | LOWER Quality (Higher Hazard) |
|-----------|------------------------------|------------------------------|
| Cash flow vs. earnings alignment | Operating cash flow closely tracks net income | Persistent gap (earnings >> cash flow) |
| Accruals intensity | Low accruals / revenue | High accruals / revenue |
| Estimate-dependent items | Few material estimates | Many material estimates (reserves, warranty, AROs, pension) |
| Revenue timing | Cash received near recognition | Long lag between recognition and cash collection |
| Extraordinary/unusual items | Rare | Frequent "one-time" adjustments |
| Tax rate consistency | Consistent effective tax rate | Volatile tax rate, frequent discrete items |
| Pension/OPEB obligations | None or frozen | Active defined benefit plan with significant assumptions |

**Data sources:**
- Financial statement comparison (net income vs. operating cash flow, 5-year trend)
- Accruals ratio computation
- 10-K critical accounting estimates section
- Revenue recognition policy complexity

**Scoring:** 0-5 scale based on composite earnings quality assessment.

---

### H3-05: Cash Flow vs. Earnings Divergence Pattern

**What it measures:** Specifically, the structural tendency for cash flows to diverge from reported earnings over time.

**Why it matters:** A company where operating cash flows chronically lag reported earnings has a structural earnings quality problem. This hazard dimension captures the baseline tendency, not a specific anomaly in a given quarter (which would be a signal). Industries like construction (percentage of completion), defense contracting (cost-plus with estimated costs), and software (multi-element arrangements with upfront recognition) structurally produce divergence.

**Risk levels:**

| Pattern | Risk Level |
|---------|------------|
| OCF / Net Income > 1.0 consistently (cash-generative) | LOW |
| OCF / Net Income ~0.8-1.0 (typical industrials) | LOW-MODERATE |
| OCF / Net Income ~0.5-0.8 (growth companies investing) | MODERATE |
| OCF / Net Income < 0.5 or negative OCF with positive earnings | HIGH |
| OCF negative, earnings negative but OCF worse by >50% | VERY HIGH |

**Data sources:**
- 5-year trend of OCF vs. net income from financial statements
- Industry comparison for expected OCF/NI ratio

**Scoring:** 0-3 scale.

---

### H3-06: Pre-Revenue / Cash Burn Profile

**What it measures:** Whether the company is pre-revenue or early-revenue with significant ongoing cash burn.

**Why it matters:** Pre-revenue companies (biotech, clinical-stage pharma, pre-production EV, pre-commercialization tech) face unique hazards: (1) valuation is entirely based on forward-looking statements and projections, (2) investor expectations are binary (drug approval, product launch), (3) running out of cash is existential. The inherent exposure is extreme because every forward-looking statement is a potential securities claim allegation.

**Risk levels:**

| Stage | Risk Level | Key Hazard |
|-------|------------|-----------|
| Profitable, positive free cash flow | LOW | Standard disclosure obligations |
| Revenue-generating but cash flow negative | MODERATE | Growth-vs-profitability narrative risk |
| Revenue < $50M, burning > $100M/year | HIGH | Cash runway creates existential risk |
| Pre-revenue, clinical/development stage | VERY HIGH | Entire valuation is forward-looking |
| Pre-revenue with < 18 months cash runway | EXTREME | Imminent dilution or failure |

**Data sources:**
- Financial statements (revenue, operating cash flow, cash balance)
- Cash runway calculation (cash + short-term investments / quarterly burn rate)
- Pipeline/product development stage disclosures

**Scoring:** 0-5 scale.

---

### H3-07: Related Party Transaction Complexity

**What it measures:** The volume and nature of transactions between the company and its officers, directors, or their affiliates.

**Why it matters:** Related-party transactions create inherent conflict-of-interest exposure. Even when properly disclosed and board-approved, they provide ammunition for derivative suit claims alleging self-dealing. Complex related-party structures (management company arrangements, shared services with founder's other companies, real estate leases from director-owned entities) increase the probability of claims.

**Risk indicators:**

| Indicator | LOW | HIGH |
|-----------|-----|------|
| Related-party transactions disclosed | None or immaterial | Material transactions, multiple parties |
| Transaction types | Standard (officer loans, indemnification) | Real estate, consulting, procurement, IP licensing |
| Controller/founder involved | No controlling shareholder | Controlling shareholder with active business interests |
| Approval process | Independent committee with independent counsel | Board approval without independent review |

**Data sources:**
- Proxy statement Item 404 (Related Party Transactions)
- 10-K related-party transaction notes

**Scoring:** 0-3 scale.

---

### H3-08: Pending Securities Offering / Capital Markets Activity

**What it measures:** Whether the company is currently in registration, recently completed, or is planning a significant securities offering.

**Why it matters:** Securities offerings (IPO, secondary, convertible, SPAC de-SPAC) carry heightened D&O exposure because Section 11 of the Securities Act provides strict liability for material misstatements in registration statements. The window surrounding a capital raise is one of the highest-risk periods for D&O claims. Woodruff Sawyer's analysis notes that 16% of all 2024 filings were against companies that went public in the prior three years.

**Risk levels:**

| Situation | Risk Level |
|-----------|------------|
| No recent or planned offerings | LOW |
| Secondary offering in past 12 months | MODERATE |
| IPO in past 36 months | HIGH |
| De-SPAC transaction in past 36 months | VERY HIGH |
| Currently in registration / offering pending | VERY HIGH |

**Data sources:**
- SEC EDGAR filing history (S-1, S-3, F-1 registrations)
- 8-K filings for offering announcements
- IPO date from company profile

**Scoring:** 0-4 scale.

---

## 6. H4: Governance Structure Hazards

These are structural characteristics of corporate governance that increase inherent D&O exposure by reducing accountability, entrenching management, or limiting shareholder remedies.

### H4-01: Combined CEO / Board Chair

**What it measures:** Whether the CEO also serves as Chairman of the Board.

**Why it matters:** A combined CEO/Chair role concentrates power and reduces the board's ability to independently oversee management. This is one of the most studied governance risk factors. While some argue it provides clear leadership, the D&O underwriting perspective views it as an accountability hazard -- there is no independent check on the CEO at the board level.

**Risk levels:**

| Structure | Risk Level |
|-----------|------------|
| Independent Board Chair | LOW |
| Lead Independent Director with independent Chair | LOW |
| Lead Independent Director with CEO/Chair combined | MODERATE |
| Combined CEO/Chair with no Lead Independent Director | HIGH |
| Founder CEO/Chair with dual-class control | VERY HIGH |

**Data sources:**
- Proxy statement (DEF 14A)
- governance_weights.json configuration

**Scoring:** 0-3 scale.

---

### H4-02: Board Independence Level

**What it measures:** The percentage of independent directors on the board and key committees.

**Why it matters:** Low board independence is a structural hazard because it reduces the board's ability to challenge management, investigate wrongdoing, and protect minority shareholders. Courts evaluating derivative claims assess board independence in determining whether the board's business judgment is entitled to deference.

**Risk levels:**

| Metric | STRONG | ADEQUATE | WEAK |
|--------|--------|----------|------|
| Board independence % | > 80% | 67-80% | < 67% |
| Audit committee independence | 100% | 100% (required) | Any non-independent = regulatory violation |
| Compensation committee independence | 100% | All independent | Any non-independent |
| Nominating committee independence | 100% | All independent | Non-independent or no committee |

**Data sources:**
- Proxy statement committee composition
- ISS independence classification

**Scoring:** 0-3 scale based on governance_weights.json thresholds.

---

### H4-03: Anti-Takeover Provisions

**What it measures:** The accumulation of anti-takeover defenses that entrench management and reduce shareholder ability to effect change.

**Why it matters:** Anti-takeover provisions collectively reduce board accountability to shareholders. The more provisions in place, the harder it is for shareholders to replace underperforming directors, creating a structural hazard for ongoing governance failures. The entrenchment effect is well-documented in academic literature.

**Key provisions and risk weighting:**

| Provision | Presence = Risk |
|-----------|----------------|
| Classified/staggered board | +2 (takes 2 election cycles to change board majority) |
| Poison pill (shareholder rights plan) | +1 (blocks hostile takeover) |
| Supermajority voting requirement for charter changes | +1 |
| No shareholder right to call special meeting | +1 |
| No shareholder right to act by written consent | +1 |
| Blank check preferred stock | +0.5 |
| Plurality (not majority) voting for directors | +0.5 |
| Forum selection clause (Delaware only) | Neutral (reduces multi-forum litigation but limits plaintiff choice) |
| Federal forum provision (SCA in federal court only) | Neutral (consolidates but does not reduce claims) |

**Data sources:**
- Proxy statement governance disclosures
- Corporate charter and bylaws (SEC EDGAR)
- ISS Governance QualityScore
- Entrenchment Index calculation

**Scoring:** Cumulative 0-5 based on provision count and severity.

---

### H4-04: Audit Committee Quality

**What it measures:** The expertise, activity level, and effectiveness of the audit committee.

**Why it matters:** The audit committee is the board's front line for detecting financial reporting problems. A weak audit committee -- lacking financial expertise, meeting infrequently, or failing to challenge management -- is a structural hazard because problems are more likely to go undetected and grow larger before discovery. The Sarbanes-Oxley Act mandated audit committee financial experts for this reason.

**Quality indicators:**

| Indicator | STRONG | ADEQUATE | WEAK |
|-----------|--------|----------|------|
| Financial experts | 2+ designated financial experts | 1 financial expert | No designated expert |
| Meeting frequency | 8+ meetings per year | 4-7 meetings | < 4 meetings |
| Auditor tenure | Changed within 10 years | 10-20 years | > 20 years same auditor (familiarity risk) |
| Non-audit fees ratio | Non-audit < 25% of total fees | 25-50% | > 50% non-audit fees |
| Auditor quality | Big 4 firm | Mid-tier national firm | Small regional firm for large-cap company |

**Data sources:**
- Proxy statement audit committee report
- 10-K audit fee disclosures (audit vs. non-audit fees)
- Proxy statement meeting frequency disclosures
- PCAOB inspection reports for the company's auditor

**Scoring:** 0-4 scale.

---

### H4-05: Shareholder Rights and Engagement

**What it measures:** The degree to which shareholders have practical mechanisms to hold management accountable.

**Why it matters:** Strong shareholder rights provide a pressure-relief valve -- shareholders can express displeasure through proxy voting, shareholder proposals, and board elections before resorting to litigation. Weak shareholder rights (no proxy access, no majority voting, no right to call special meetings) force shareholders toward litigation as their only recourse, increasing D&O claim frequency.

**Key indicators:**

| Right | STRONG | WEAK |
|-------|--------|------|
| Voting standard for directors | Majority voting | Plurality voting |
| Proxy access | Adopted (3%/3-year/25% threshold) | Not adopted |
| Shareholder ability to call special meeting | Yes, reasonable threshold (10-25%) | No, or threshold >50% |
| Say-on-pay recent results | >90% approval | <70% approval |
| Shareholder proposal responsiveness | Board engages, implements when appropriate | Board ignores, recommends against all |

**Data sources:**
- Proxy statement governance provisions
- Say-on-pay vote results
- Shareholder proposal history

**Scoring:** 0-3 scale.

---

### H4-06: Executive Compensation Structure

**What it measures:** How executive compensation is structured, and whether it creates incentives that increase D&O risk.

**Why it matters:** Compensation structure is a hazard (not just a signal) because it creates the incentive environment that management operates within. Heavily incentivized compensation tied to short-term stock price performance creates structural pressure to manage earnings, inflate metrics, or take excessive risks. Options-heavy compensation with cliff vesting creates windfall incentives that can motivate insider selling (itself a claim trigger).

**Risk indicators:**

| Factor | LOW Risk | HIGH Risk |
|--------|----------|-----------|
| Equity mix | Balanced (RSU + performance shares, 3-year vesting) | Options-heavy with cliff vesting |
| Performance metrics | Multi-factor (revenue + margin + relative TSR) | Single metric (revenue only, or EPS only) |
| Time horizon | 3+ year performance period | 1-year performance period |
| CEO compensation vs. peers | Within 1-2 standard deviations | Top decile without corresponding performance |
| Severance/golden parachute | Standard 2x | Excessive (>3x with tax gross-up) |
| Clawback policy | Robust, beyond SOX minimum | Bare minimum compliance only |

**Data sources:**
- Proxy statement CD&A (Compensation Discussion & Analysis)
- Executive compensation tables
- Peer comparison from proxy

**Scoring:** 0-3 scale.

---

### H4-07: Whistleblower and Compliance Infrastructure

**What it measures:** The visible presence and quality of the company's compliance and reporting infrastructure.

**Why it matters:** A company without a robust compliance infrastructure is structurally more likely to have problems develop unchecked. The absence of a compliance committee, a whistleblower hotline, or a Code of Conduct is a hazard because it means the detection-and-correction cycle is impaired. Courts in Caremark claims specifically examine whether the company had compliance reporting systems in place.

**Infrastructure indicators:**

| Element | Present = Lower Hazard | Absent = Higher Hazard |
|---------|----------------------|----------------------|
| Anonymous whistleblower hotline | Essential | Major gap |
| Board-level compliance committee | Best practice | Compliance buried in audit committee |
| Chief Compliance Officer | Best practice for regulated industries | No dedicated CCO |
| Code of Conduct publicly available | Standard | Not found |
| Anti-corruption/FCPA program | Essential for international operations | Not evident |
| SOX 404 material weakness history | Clean (no material weaknesses in 5 years) | Recent material weakness |

**Data sources:**
- Proxy statement governance disclosures
- Company website (Code of Conduct, compliance resources)
- 10-K internal controls disclosures (Item 9A)
- SEC EDGAR search for material weakness disclosures

**Scoring:** 0-3 scale.

---

### H4-08: State of Incorporation and Legal Regime

**What it measures:** The legal framework governing the company based on its state of incorporation.

**Why it matters:** Delaware's Court of Chancery provides well-developed case law and sophisticated judges for corporate governance disputes, but also a more accessible forum for derivative plaintiffs. Recent trends include companies reincorporating from Delaware to Nevada or Texas (which have less developed corporate law), and Delaware's 2025 narrowing of Section 220 books-and-records demands. The choice of incorporation state affects the legal hazard landscape.

**Risk considerations:**

| State | D&O Risk Profile |
|-------|-----------------|
| Delaware | Moderate-High for derivatives (accessible Chancery Court, well-developed fiduciary duty law); standard for SCAs (federal) |
| Nevada | Lower for derivatives (higher burden on plaintiffs, less developed case law) |
| Texas | Lower for derivatives (2025 business courts, minimum ownership requirements) |
| Other | Varies; less predictable case law |
| Foreign (FPI) | Different legal regime; generally lower US litigation exposure due to Morrison limitations |

**Data sources:**
- SEC EDGAR: State of incorporation from company filing header
- Company charter documents
- Forum selection clause analysis

**Scoring:** 0-2 scale.

---

## 7. H5: Public Company Maturity Hazards

These dimensions capture where the company sits in its lifecycle as a public entity, which affects baseline D&O exposure independently of all other factors.

### H5-01: IPO Recency

**What it measures:** How recently the company completed its initial public offering.

**Why it matters:** This is one of the most powerful hazard dimensions. Stanford Securities Litigation Analytics data shows 14-21% of IPOs face securities litigation within 3 years (vs. ~3.9% annual base rate for all listed companies). 74% of IPO lawsuits occur within five quarters of the offering. Recently public companies face elevated risk because: (1) the registration statement provides a strict-liability basis under Section 11, (2) the company and management are adjusting to public company disclosure requirements, (3) initial investor expectations are often unrealistic.

**Risk tiers:**

| Time Since IPO | Hazard Multiplier | Basis |
|----------------|-------------------|-------|
| 0-18 months | 3-5x base rate | Stanford SLA: 74% of IPO suits within 5 quarters |
| 18-36 months | 2-3x base rate | Still within 3-year statute of limitations |
| 36-60 months | 1.5x base rate | Elevated but declining |
| 5-10 years | 1.0x base rate | At market average |
| 10+ years | 0.8x base rate | Seasoned company, established track record |

**Data sources:**
- SEC EDGAR: Initial filing date / IPO date
- Company profile data
- INHERENT_RISK_BASELINE_RESEARCH.md actuarial data

**Scoring:** 0-5 scale based on multiplier tier.

Source: Stanford Securities Litigation Analytics; Cornerstone Research 2024 Year in Review.

---

### H5-02: Method of Going Public

**What it measures:** How the company became publicly traded.

**Why it matters:** The method of going public has a significant impact on D&O exposure. De-SPAC transactions face approximately 5-6x the base litigation rate (17-24% filing rate per transaction). Direct listings have an uncertain risk profile (less underwriter due diligence). Spin-offs carry unique disclosure risks about the separated entities.

**Risk by method:**

| Method | Hazard Level | Filing Rate (Estimated) |
|--------|-------------|------------------------|
| Traditional IPO (underwritten) | HIGH (first 3 years) | 14-21% cumulative 3-year |
| De-SPAC transaction | VERY HIGH (first 3 years) | 17-24% cumulative 3-year |
| Direct listing | HIGH (uncertain) | Limited data; Coinbase and others sued |
| Reverse merger (into shell) | VERY HIGH | Historical fraud concentration |
| Spin-off from public parent | MODERATE | Inherited some parent's governance |
| Registration of existing shares (already trading OTC) | LOW-MODERATE | Lower profile |

**Data sources:**
- SEC EDGAR: Filing type analysis (S-1, S-4 for SPAC, S-11 for REIT)
- Company history / press releases
- INHERENT_RISK_BASELINE_RESEARCH.md

**Scoring:** 0-4 scale.

Source: American Bar Association, "SPAC Litigation by the Numbers" (2023); Woodruff Sawyer, SPAC D&O Guide (2025).

---

### H5-03: Stock Exchange and Index Membership

**What it measures:** Which exchange the company is listed on and whether it belongs to major indices.

**Why it matters:** Exchange listing determines regulatory requirements (NYSE vs. NASDAQ vs. OTC have different governance mandates), and index membership drives institutional ownership (index funds must hold index constituents). Higher institutional ownership means more sophisticated plaintiff attorneys and higher claim probability. S&P 500 companies face a 6.1% annual filing rate vs. ~3.9% overall (2024).

**Risk by listing:**

| Listing | Risk Enhancement |
|---------|-----------------|
| S&P 500 member | +50% vs. base (6.1% vs. 3.9%) |
| Russell 2000 member | ~0.8x base (smaller damages pool) |
| NYSE / NASDAQ listed | Base rate (governance requirements comparable) |
| OTC listed | Low SCA risk but high fraud association |
| Foreign exchange + ADR | ~0.65x base (Morrison limitations) |

**Data sources:**
- Company profile (exchange, index membership)
- yfinance for current index membership

**Scoring:** 0-3 scale.

Source: Cornerstone Research, 2024 Year in Review.

---

### H5-04: ADR / Foreign Private Issuer Status

**What it measures:** Whether the company is a foreign private issuer listed via ADR.

**Why it matters:** FPIs face approximately 0.65x the domestic filing rate due to jurisdictional complexity (Morrison v. National Australia Bank limits), lower US institutional ownership, and higher dismissal rates. However, FPIs from certain jurisdictions (China-based, reverse mergers) face elevated risk.

**Data sources:**
- SEC EDGAR: Foreign private issuer indicator from filing headers (Form 20-F vs. 10-K)
- ADR type (Level I, II, III) determines US listing requirements

**Scoring:** 0-2 scale. FPI generally reduces hazard, but China-based FPI increases it.

Source: NERA, 2024 Full-Year Review.

---

### H5-05: Seasoning and Track Record

**What it measures:** The company's track record of navigating public company reporting, surviving market downturns, and managing investor expectations.

**Why it matters:** A company that has been public for 20 years and successfully navigated the 2008 financial crisis, COVID, and multiple market corrections has demonstrated that its disclosure practices and governance can withstand stress. This track record itself is a hazard reducer -- not because past performance predicts future results, but because it evidences functional systems.

**Track record indicators:**

| Indicator | Positive (Lower Hazard) | Negative (Higher Hazard) |
|-----------|------------------------|-------------------------|
| Years without restatement | 10+ years | Any restatement in past 5 years |
| Survived major downturn without lawsuit | Yes (e.g., no 2020 COVID suit) | Sued during last downturn |
| Consistent earnings guidance accuracy | Generally met or beat | Pattern of missed guidance |
| Auditor relationship | Long-term, no audit opinion issues | Recent auditor change, especially if initiated by auditor |
| SEC comment letter history | Resolved promptly, no material issues | Material comments or unresolved issues |

**Data sources:**
- SEC EDGAR filing history
- Stanford SCAC historical filing search
- Audit fee and opinion analysis from proxy
- SEC EDGAR Full-Text Search for comment letters

**Scoring:** 0-3 scale.

---

## 8. H6: External Environment Hazards

These dimensions capture conditions in the broader market, regulatory, and political environment that amplify or suppress D&O exposure for all companies, but differentially affect companies based on their characteristics.

### H6-01: Market Cycle Position

**What it measures:** Where the broader equity market sits in its cycle, and the implications for subsequent D&O claims.

**Why it matters:** Securities class actions are procyclical in filing with a lag. Claims spike after market downturns because: (1) stock drops create the damages necessary for viable claims, (2) companies that made aggressive disclosures during bull markets face scrutiny when reality disappoints, (3) plaintiff attorneys file more aggressively when damages pools are large. Late-stage bull markets are the highest-hazard environment because they precede the corrections that generate claims.

**Market cycle risk levels:**

| Cycle Phase | Hazard Level | Mechanism |
|-------------|-------------|-----------|
| Late bull market (valuations stretched, IPO boom) | VERY HIGH | Claims accumulating; will materialize on correction |
| Early correction / bear market | HIGH | Filing wave begins, damages already sufficient |
| Deep bear market | HIGH | Maximum filing activity, but may moderate as damages compress for micro/small-cap |
| Early recovery | MODERATE | Tail-end filings from prior decline; new cycle beginning |
| Mid-cycle expansion | LOW | Moderate filing rates, investor satisfaction |

**Data sources:**
- S&P 500 trailing P/E ratio vs. historical average
- VIX level as volatility proxy
- Shiller CAPE ratio
- IPO issuance volume (high = late cycle indicator)

**Scoring:** 0-3 scale based on cycle assessment. This is a systemic factor applied to all companies.

---

### H6-02: Industry Regulatory Spotlight

**What it measures:** Whether the company's industry is currently under heightened regulatory scrutiny.

**Why it matters:** Regulatory enforcement tends to come in waves. When the SEC, DOJ, CFPB, FTC, or state AGs focus on a particular industry, all companies in that industry face elevated exposure -- even those that are compliant. The investigation wave creates disclosure obligations (must disclose material investigations), employee anxiety (whistleblower activity increases), and plaintiff attorney attention.

**Current heightened-scrutiny industries (as of early 2026):**

| Industry | Regulatory Focus | Key Regulators |
|----------|-----------------|----------------|
| AI / Technology | AI governance, algorithmic bias, data privacy, "AI washing" | SEC, FTC, EU AI Act enforcement |
| Cryptocurrency / Digital assets | Securities classification, custody, exchange operations | SEC, CFTC, state regulators |
| Healthcare (pharmacy, PBM) | Drug pricing, PBM practices, opioid liability | DOJ, HHS, state AGs |
| Financial services | Consumer lending, BSA/AML, crypto exposure | CFPB, OCC, state AGs |
| Energy (ESG) | Climate disclosures, greenwashing | SEC (climate rules), state AGs |
| Social media / platforms | Child safety, antitrust, data privacy | FTC, state AGs, Congress |
| Private credit / PE | Fund valuation, conflicts, fee disclosure | SEC, DOJ |

**Data sources:**
- News search for industry + "SEC enforcement" or "DOJ investigation"
- SEC enforcement actions by industry
- Brave Search for recent regulatory developments by sector
- Political environment analysis (new administration priorities)

**Scoring:** 0-3 scale based on current regulatory intensity for the company's industry.

---

### H6-03: Industry Litigation Wave

**What it measures:** Whether the company's industry is currently experiencing a wave of D&O-related litigation.

**Why it matters:** Litigation waves create "copycat" filing risk. When plaintiff attorneys succeed against one company in an industry, they look for similar fact patterns at peer companies. Waves in biotech (clinical trial failures), crypto (securities classification), SPAC (de-SPAC disclosure), and opioids (distribution liability) demonstrate this phenomenon. Allianz 2026 notes that securities class action filings increased 15% in 2024 with concentration in technology and biotech.

**Current active litigation waves (early 2026):**

| Wave | Industry | Claim Theory | Status |
|------|----------|-------------|--------|
| AI washing | Technology, diversified | Overstating AI capabilities | Doubling annually (7→15→~30 filings) |
| Clinical trial disclosure | Biotech | Failure to disclose adverse trial results | Persistent (~67 filings in 2024) |
| Cyber governance | Cross-industry | Board failure to oversee cyber risk | Growing |
| ESG/Greenwashing | Energy, consumer | Misleading sustainability claims | Growing globally |
| Insolvency-related | Consumer, auto, construction, retail | Breach of fiduciary duty near insolvency | Rising with insolvency wave |

**Data sources:**
- Stanford SCAC filing data by industry
- Cornerstone Research annual filings report
- D&O Diary, Woodruff Sawyer market updates

**Scoring:** 0-3 scale.

Source: Cornerstone Research, 2024 Year in Review; Allianz Commercial, D&O Insurance Insights 2026.

---

### H6-04: Political and Policy Environment

**What it measures:** The current political environment's impact on regulatory enforcement priorities and litigation trends.

**Why it matters:** Changes in administration priorities directly affect enforcement intensity. A new SEC chair with an enforcement focus (Gensler era) produces different claim patterns than a deregulatory posture. State AG activism fills gaps when federal enforcement retreats. Tariff policies create supply chain disclosure obligations. Immigration policies affect workforce-dependent industries.

**Current considerations (early 2026):**
- SEC enforcement recovered $8.2 billion in fiscal 2024 -- highest ever
- Shifting DEI/ESG enforcement priorities under new administration
- Tariff policies creating supply chain and cost disclosure obligations
- State AG activism filling federal enforcement gaps
- Whistleblower program expansion continuing

**Data sources:**
- News analysis of current administration priorities
- SEC enforcement statistics
- State AG enforcement patterns

**Scoring:** 0-2 scale (systemic factor, company-specific impact varies by industry exposure).

---

### H6-05: Interest Rate and Credit Environment

**What it measures:** The prevailing interest rate environment and its impact on leverage-sensitive companies.

**Why it matters:** Rising interest rates increase refinancing risk, covenant compliance pressure, and the cost of maintaining leveraged capital structures. Companies that thrived in zero-rate environments face new hazards when rates normalize. The insolvency wave that Allianz projects (+24% above pre-pandemic by 2026) is directly linked to the rate environment.

**Impact by company type:**

| Company Type | Rising Rate Hazard |
|-------------|-------------------|
| High-leverage (>4x debt/EBITDA) | HIGH -- refinancing risk, covenant pressure |
| Pre-revenue / cash-burning | HIGH -- dilution required to fund operations |
| Real estate / REITs | HIGH -- asset values, refinancing |
| Investment-grade with laddered maturities | LOW -- manageable impact |
| Cash-rich technology | LOW -- benefits from higher interest income |

**Data sources:**
- Federal funds rate, 10-year Treasury yield
- Company debt profile from financial statements
- Credit spreads (high-yield vs. investment-grade)

**Scoring:** 0-2 scale (interaction with H3-01 leverage).

---

### H6-06: Plaintiff Attorney Activity Level

**What it measures:** The current level of plaintiff attorney activity, resources, and aggressiveness in securities litigation.

**Why it matters:** The plaintiff bar's capacity and incentives directly affect claim frequency. Well-resourced lead plaintiff firms file more aggressively when they have capital, technology, and successful precedents. The "litigation funding" industry (third-party funding of securities suits) has expanded dramatically, reducing the financial barriers to filing.

**Current indicators (early 2026):**
- Third-party litigation funding has grown to an estimated $15+ billion global industry
- Plaintiff firms have invested in event-driven analytics to identify filing opportunities faster
- Dismissal rates increased 74% year-over-year (Woodruff Sawyer 2026), which could moderate filing incentives
- But settlement values remain high (median $14M in 2024)

**Data sources:**
- Cornerstone Research settlement data
- Stanford SCAC filing rates
- Litigation funding industry reports

**Scoring:** 0-1 scale (systemic factor applied uniformly).

---

### H6-07: Geopolitical Risk Environment

**What it measures:** Geopolitical tensions, sanctions regimes, and cross-border risks affecting the company's operating environment.

**Why it matters:** Geopolitical events (wars, sanctions, trade restrictions) create disclosure obligations, supply chain disruptions, and asset impairment risks. Companies with operations in conflict zones, sanctioned countries, or countries with deteriorating relations face elevated D&O exposure. Allianz 2026 identifies geopolitical uncertainty as a major D&O risk driver.

**Risk factors:**

| Factor | Risk Level |
|--------|------------|
| Operations in sanctioned countries | HIGH |
| Revenue from geopolitically unstable regions (>10%) | MODERATE |
| Supply chain through conflict-affected areas | MODERATE |
| Export-controlled technology | MODERATE |
| No material international exposure | LOW |

**Data sources:**
- 10-K geographic disclosures
- OFAC sanctions lists
- Export control classifications
- Current geopolitical risk assessments

**Scoring:** 0-2 scale.

---

## 9. H7: Emerging / Modern Hazards

These dimensions capture new-era exposure sources that traditional D&O underwriting frameworks may not fully address.

### H7-01: AI Adoption and Governance Exposure

**What it measures:** The degree to which the company uses, develops, or deploys AI systems, and the maturity of its AI governance framework.

**Why it matters:** AI-related securities filings more than doubled from 7 in 2023 to 15 in 2024. "AI washing" (exaggerating AI capabilities to inflate stock price) is a rapidly growing claim theory. Companies deploying AI in high-stakes applications (healthcare, lending, hiring) face regulatory exposure under emerging frameworks (EU AI Act, state laws). The SEC has signaled that AI-related disclosures will receive heightened scrutiny.

**Risk dimensions:**

| Factor | LOW | HIGH |
|--------|-----|------|
| AI in investor narrative | Minor/no mention | AI is central to valuation thesis |
| AI in regulated applications | No AI in regulated decisions | AI used in lending, healthcare, hiring |
| AI governance framework | Formal policy, board oversight, ethics committee | No visible governance framework |
| AI data privacy exposure | Limited data use | Large-scale personal data processing via AI |
| AI capability claims | Modest, substantiated | Bold claims difficult to verify ("our AI is revolutionary") |

**Data sources:**
- 10-K AI-related risk factor disclosures
- Earnings call transcript analysis for AI mention frequency
- Company website AI governance disclosures
- ai_risk_weights.json configuration

**Scoring:** 0-4 scale.

Source: Cornerstone Research, 2024; Woodruff Sawyer 2026 D&O Looking Ahead.

---

### H7-02: Cybersecurity Governance Exposure

**What it measures:** The company's cyber risk profile and board-level cyber governance maturity.

**Why it matters:** The SEC's 2023 cybersecurity disclosure rules require public companies to disclose material cybersecurity incidents within four business days and describe their cyber governance. Board-level cyber oversight is now a D&O liability surface. Companies with data-intensive business models, consumer PII, healthcare data, or financial data face the highest exposure. Allianz 2026 notes "cyber liability risks for directors and officers have risen sharply."

**Risk dimensions:**

| Factor | LOW | HIGH |
|--------|-----|------|
| Data sensitivity | B2B, limited PII | Consumer PII, health data, financial data |
| Industry cyber attack frequency | Below average | Above average (healthcare, financial, retail) |
| Board cyber expertise | Dedicated cyber committee, expert director | No visible cyber expertise on board |
| Prior incident history | None | Prior breach(es), even if resolved |
| SEC cybersecurity compliance | Early, robust disclosure | Minimal compliance, late disclosure |

**Data sources:**
- 10-K cybersecurity disclosures (Item 1C, new SEC requirement)
- Proxy statement for board cyber expertise
- News search for prior cyber incidents
- Industry cyber attack frequency data

**Scoring:** 0-3 scale.

---

### H7-03: ESG / Climate Disclosure Exposure

**What it measures:** The company's exposure to ESG-related litigation based on its industry, disclosures, and commitments.

**Why it matters:** ESG-related D&O claims are growing from both directions: (1) companies that make strong ESG commitments face "greenwashing" litigation when they fail to deliver, (2) companies that ignore ESG face regulatory and stakeholder pressure claims. The SEC's climate disclosure rules (even with litigation challenges) have raised the disclosure standard. State AG enforcement on ESG claims continues to expand.

**Risk dimensions:**

| Factor | LOW | HIGH |
|--------|-----|------|
| Carbon-intensive industry | No / minimal | High emitter (energy, mining, transportation, manufacturing) |
| ESG commitments made | Measured, achievable | Ambitious targets (net-zero by 2030) difficult to verify |
| ESG reporting maturity | No ESG report (low profile) or SASB-aligned | Bold claims without SASB/TCFD alignment |
| Greenwashing litigation risk | Low-profile industry | Consumer-facing, environmental claims in marketing |
| Regulatory exposure | Minimal ESG regulation | Subject to SEC climate rules, EU CSRD, or state laws |

**Data sources:**
- 10-K environmental disclosures
- Sustainability/ESG reports
- Industry carbon intensity data
- SEC climate rule applicability analysis

**Scoring:** 0-3 scale.

---

### H7-04: Cryptocurrency / Digital Asset Exposure

**What it measures:** The company's exposure to cryptocurrency and digital asset risks.

**Why it matters:** Companies with material crypto holdings, crypto-related revenue, or crypto-adjacent business models face heightened D&O exposure due to securities classification uncertainty, regulatory enforcement (SEC actions against crypto companies have been significant), and extreme asset volatility. Even companies with indirect crypto exposure (accepting Bitcoin payments, holding crypto on balance sheet) face disclosure risk.

**Risk levels:**

| Exposure | Risk Level |
|----------|------------|
| No crypto exposure | NONE |
| Crypto accepted as payment (immaterial) | LOW |
| Material crypto holdings on balance sheet | MODERATE |
| Revenue from crypto-related services | HIGH |
| Crypto exchange, DeFi, or token issuer | VERY HIGH |

**Data sources:**
- 10-K disclosures of digital asset holdings
- Revenue breakdown for crypto-related segments
- Business description analysis

**Scoring:** 0-3 scale.

---

### H7-05: Social Media and Public Persona Risk

**What it measures:** The company's (and its CEO's) social media profile and the risk of market-moving public statements outside traditional disclosure channels.

**Why it matters:** The "Elon Musk tweet" phenomenon -- material information disclosed via social media rather than through proper channels -- creates D&O exposure. CEOs with large social media followings who make statements about company performance, products, or strategy create disclosure liability risk. The SEC has pursued enforcement actions for social media disclosure violations.

**Risk indicators:**

| Indicator | LOW | HIGH |
|-----------|-----|------|
| CEO social media following | Low-profile, limited activity | 100K+ followers, frequent posts about company |
| History of market-moving social media | None | Stock moved >5% on social media statement |
| Social media policy for executives | Formal policy in place | No visible policy |
| Meme stock status | No | Active meme stock community / retail investor base |

**Data sources:**
- Social media analysis (Twitter/X follower counts, post frequency)
- News search for social media-related controversies
- SEC enforcement search for social media violations

**Scoring:** 0-2 scale.

---

### H7-06: Workforce and Labor Model Exposure

**What it measures:** The company's workforce structure and its exposure to employment-related D&O claims.

**Why it matters:** Employment practices liability (EPL) is a significant D&O claim category. Companies with large workforces, contractor-heavy models (gig economy), recent layoffs, or operations in high-employment-litigation jurisdictions face elevated exposure. The shift to remote work has created new wage-and-hour compliance challenges across jurisdictions.

**Risk indicators:**

| Factor | LOW | HIGH |
|--------|-----|------|
| Employee count | < 1,000 | > 50,000 |
| Contractor/gig worker ratio | Low | High (>25% of workforce) |
| Recent layoffs (12 months) | None | >10% reduction in force |
| Geographic distribution | Single jurisdiction | Multi-state / international |
| Unionization | Non-unionized | Active unionization efforts or disputes |
| DEI litigation exposure | Low-profile on DEI | Public DEI commitments now under scrutiny |

**Data sources:**
- 10-K employee count and workforce disclosures
- 8-K filings for layoff announcements
- News search for labor disputes
- Glassdoor employee sentiment

**Scoring:** 0-3 scale.

---

## 10. Hazard Interaction Effects

### Dangerous Combinations

Hazards do not operate in isolation. Certain combinations create multiplicative rather than additive risk. The following interaction effects represent the most dangerous hazard combinations in D&O underwriting.

### Tier 1: Critical Combinations (Multiplicative Risk)

| Combination | Components | Risk Multiplier | Example |
|-------------|-----------|-----------------|---------|
| **The Rookie Rocket** | High growth (H1-09) + Inexperienced management (H2-01) + Recent IPO (H5-01) | 3-5x | Pre-revenue biotech IPO with first-time CEO: EXTREME litigation probability |
| **The Black Box** | Complex business model (H1-02) + Weak earnings quality (H3-04) + Heavy non-GAAP reliance (H1-11) | 2-4x | Multi-segment company with multiple revenue recognition methods, emphasizing "adjusted" metrics |
| **The Imperial Founder** | Founder-led (H2-05) + Combined CEO/Chair (H4-01) + Dual-class control (H1-10) + Anti-takeover provisions (H4-03) | 2-3x (derivatives) | Founder with 80% voting control, combined CEO/Chair, classified board. No accountability mechanism exists |
| **The Acquisition Machine** | Serial acquirer (H1-08) + Goodwill-heavy (H3-03) + Aggressive compensation (H4-06) | 2-3x | CEO compensation tied to revenue growth, achieved through acquisitions that create massive goodwill; eventual impairment inevitable |

### Tier 2: High-Risk Combinations (Additive + Amplification)

| Combination | Components | Risk Enhancement | Example |
|-------------|-----------|-----------------|---------|
| **The Regulatory Pressure Cooker** | High regulatory intensity (H1-03) + Industry in regulatory spotlight (H6-02) + Weak compliance infrastructure (H4-07) | 2x | Financial services company during CFPB enforcement wave with no dedicated CCO |
| **The Geographic Minefield** | Multi-jurisdiction operations (H1-04) + FCPA-risk countries + Rapid international expansion (H1-09) | 2x | Company rapidly expanding into emerging markets without scaled compliance |
| **The Complexity Trap** | Off-balance sheet arrangements (H3-02) + Related party transactions (H3-07) + Capital structure complexity (H3-01) | 2x | Company with VIEs, management company arrangements, and layered debt |
| **The Governance Vacuum** | Low board independence (H4-02) + No compliance infrastructure (H4-07) + Weak audit committee (H4-04) | 1.5-2x | Small-cap company with board dominated by insiders and a weak audit committee |

### Tier 3: Elevated Combinations (Notable but Not Critical)

| Combination | Components | Risk Enhancement |
|-------------|-----------|-----------------|
| **Tech Disruption** | AI central to narrative (H7-01) + Pre-revenue (H3-06) + Celebrity CEO (H7-05) | 1.5x |
| **Leverage at the Top** | High debt (H3-01) + Rising rates (H6-05) + Cash burn (H3-06) | 1.5x |
| **Customer Cliff** | Customer concentration (H1-06) + Government dependency + Political environment shift (H6-04) | 1.5x |

### Implementation: Interaction Detection

For automated scoring, interaction effects should be detected by checking pairwise and three-way combinations:

```
IF H1-09 (growth) >= HIGH AND H2-01 (experience) >= HIGH AND H5-01 (IPO recency) >= HIGH:
    apply_multiplier("rookie_rocket", 3.0)

IF H1-02 (complexity) >= HIGH AND H3-04 (earnings quality) >= HIGH AND H1-11 (non-GAAP) >= HIGH:
    apply_multiplier("black_box", 2.5)

IF H2-05 (founder-led) == TRUE AND H4-01 (CEO/Chair) == TRUE AND H1-10 (dual-class) == TRUE:
    apply_multiplier("imperial_founder", 2.0)
```

---

## 11. Proposed Hazard Profile Scoring Framework

### The "Inherent Exposure Score" (IES)

The Inherent Exposure Score provides a single number (0-100) that captures the company's baseline D&O hazard profile BEFORE examining any behavioral signals.

**Interpretation:**

| IES Range | Classification | Meaning |
|-----------|---------------|---------|
| 0-20 | MINIMAL | Very low inherent exposure (regulated utility, veteran management, mature public company) |
| 21-35 | LOW | Below-average inherent exposure |
| 36-50 | MODERATE | Average inherent exposure for a public company |
| 51-65 | ELEVATED | Above-average inherent exposure |
| 66-80 | HIGH | Significantly elevated inherent exposure |
| 81-100 | EXTREME | Maximum inherent exposure (pre-revenue biotech IPO with first-time management and complex structure) |

### Scoring Weights by Category

| Category | Weight | Max Raw Points | Scoring Method |
|----------|--------|---------------|----------------|
| H1: Business & Operating Model | 25% | 25 | Sum of H1-01 through H1-13, capped at 25 |
| H2: People & Management | 15% | 15 | Sum of H2-01 through H2-08, capped at 15 |
| H3: Financial Structure | 15% | 15 | Sum of H3-01 through H3-08, capped at 15 |
| H4: Governance Structure | 15% | 15 | Sum of H4-01 through H4-08, capped at 15 |
| H5: Public Company Maturity | 10% | 10 | Sum of H5-01 through H5-05, capped at 10 |
| H6: External Environment | 10% | 10 | Sum of H6-01 through H6-07, capped at 10 |
| H7: Emerging / Modern Hazards | 10% | 10 | Sum of H7-01 through H7-06, capped at 10 |
| **Base Total** | 100% | 100 | |
| **Interaction Multiplier** | Applied after | x1.0 to x3.0 | Highest applicable multiplier from Section 10 |

**Final IES = min(100, Base Total x Interaction Multiplier)**

### Example Profiles

**Example 1: Company A -- Established Utility**

| Category | Score | Key Factors |
|----------|-------|-------------|
| H1: Business | 4/25 | LOW industry risk, simple business model, single jurisdiction, regulated rate base |
| H2: People | 1/15 | Veteran CEO (20 years), experienced board, industry experts |
| H3: Financial | 3/15 | Moderate leverage (regulated), stable earnings quality |
| H4: Governance | 2/15 | Independent board, standard anti-takeover |
| H5: Maturity | 0/10 | Public since 1952, long track record |
| H6: External | 2/10 | Climate regulation exposure, but manageable |
| H7: Emerging | 1/10 | Minimal AI/cyber/ESG exposure |
| **Base Total** | **13** | |
| Interactions | None | |
| **Final IES** | **13 (MINIMAL)** | |

**Example 2: Company B -- Pre-Revenue Biotech IPO**

| Category | Score | Key Factors |
|----------|-------|-------------|
| H1: Business | 18/25 | EXTREME industry risk (biotech), novel business model, multiple clinical trial sites internationally, FDA + EMA regulated |
| H2: People | 10/15 | First-time public company CEO and CFO, limited board experience, key-person dependency on CSO |
| H3: Financial | 10/15 | Pre-revenue, 18-month cash runway, will need dilutive financing |
| H4: Governance | 5/15 | New board, limited committee experience, founder CEO/Chair |
| H5: Maturity | 8/10 | IPO 14 months ago, no track record, traditional IPO |
| H6: External | 4/10 | Late bull market, biotech litigation wave active |
| H7: Emerging | 2/10 | AI in drug discovery narrative |
| **Base Total** | **57** | |
| Interactions | "Rookie Rocket" (3x ceiling, applied as 1.5x because base already elevated) | |
| **Final IES** | **86 (EXTREME)** | |

**Example 3: Company C -- Mature Technology Company**

| Category | Score | Key Factors |
|----------|-------|-------------|
| H1: Business | 12/25 | HIGH industry risk (tech), moderate complexity, global operations, subscription revenue model |
| H2: People | 3/15 | Experienced CEO (8 years), some board experience gaps, recent CFO change |
| H3: Financial | 4/15 | Modest leverage, good cash generation, some goodwill from acquisitions |
| H4: Governance | 4/15 | Combined CEO/Chair, otherwise adequate governance |
| H5: Maturity | 2/10 | Public for 15 years, S&P 500 member |
| H6: External | 5/10 | AI washing litigation wave, tech in regulatory spotlight |
| H7: Emerging | 5/10 | AI central to narrative, high cyber exposure, customer data |
| **Base Total** | **35** | |
| Interactions | None at critical level | |
| **Final IES** | **35 (LOW-MODERATE)** | |

---

## 12. Data Source Summary by Hazard Dimension

### Automated Data Sources (Available in Current System)

| Source | Hazard Dimensions Served | Acquisition Method |
|--------|-------------------------|-------------------|
| SEC EDGAR (10-K) | H1-01 through H1-13, H3-01 through H3-08, H4-07, H5-01 through H5-05 | EdgarTools MCP / SEC REST API |
| SEC EDGAR (DEF 14A Proxy) | H2-01 through H2-08, H4-01 through H4-08 | EdgarTools MCP / SEC REST API |
| SEC EDGAR (8-K) | H2-07, H3-08 | EdgarTools MCP |
| yfinance | H1-01, H1-09, H3-01, H3-04, H3-05, H5-03, H6-01, H6-05 | yfinance Python library |
| Stanford SCAC | H1-01, H6-03 | Playwright MCP scraping |
| Brave Search / WebSearch | H2-01, H2-02, H2-08, H6-02, H6-04, H7-05 | Brave Search MCP |
| Company profile data | H1-04, H5-01, H5-02 | SEC EDGAR submissions API |

### Semi-Automated Sources (Require LLM Extraction)

| Source | Hazard Dimensions Served | Extraction Method |
|--------|-------------------------|-------------------|
| 10-K Item 1 (Business description) | H1-02, H1-03, H1-06, H1-07, H1-12, H1-13 | LLM extraction from filing text |
| 10-K Item 1A (Risk Factors) | H1-03, H1-04, H1-06, H1-12, H2-06, H7-01 through H7-06 | LLM extraction with structured prompts |
| 10-K Revenue Recognition notes | H1-05, H3-04 | LLM extraction |
| 10-K financial statement notes | H3-02, H3-03, H3-07 | LLM extraction |
| Proxy Statement CD&A | H4-06, H2-01, H2-02, H2-04, H2-05 | LLM extraction |
| Proxy Statement governance section | H4-01 through H4-05 | LLM extraction |
| Earnings call transcripts | H2-08 (tone), H1-11 (non-GAAP emphasis) | LLM tone analysis |

### Manual / Judgment-Dependent Sources

| Dimension | Manual Assessment Required |
|-----------|---------------------------|
| H2-03 (Scale experience mismatch) | Requires comparing prior company size to current |
| H2-08 (Tone at the top) | Qualitative, multi-source assessment |
| H6-01 (Market cycle position) | Macro assessment, updated periodically |
| H6-04 (Political environment) | Current events analysis |
| H7-05 (Social media risk) | Social media monitoring |

---

## 13. Relationship to Existing System Components

### How the Hazard Profile Complements the Current 10-Factor Scoring

The current system's 10-factor scoring (F1-F10) primarily captures **signals** -- evidence of problems:

| Existing Factor | Type | What It Measures |
|----------------|------|-----------------|
| F1: Prior Litigation | Signal | Has the company been sued? |
| F2: Stock Decline | Signal | Has the stock dropped significantly? |
| F3: Restatement/Audit | Signal | Has there been a restatement or audit issue? |
| F4: IPO/SPAC/M&A | **Hazard + Signal** | Is the company recently public? (hazard) Did a specific deal go wrong? (signal) |
| F5: Guidance Misses | Signal | Has management missed guidance? |
| F6: Short Interest | Signal | Are shorts betting against the company? |
| F7: Volatility | Signal | Is the stock abnormally volatile? |
| F8: Financial Distress | Signal | Is the company in financial distress? |
| F9: Governance | **Hazard** | Governance structure quality |
| F10: Officer Stability | **Hazard + Signal** | Management turnover patterns |

**Key observation:** Only F4 (partially), F9, and F10 (partially) capture hazard dimensions. The remaining factors are reactive -- they fire only when something has already gone wrong. The Hazard Profile Score fills the gap by providing the proactive baseline assessment.

### Proposed Integration Architecture

```
Hazard Profile Score (IES: 0-100)
    = H1 Business + H2 People + H3 Financial + H4 Governance
      + H5 Maturity + H6 Environment + H7 Emerging
      x Interaction Multiplier

Signal Score (Current 10-Factor: 0-100)
    = F1 + F2 + F3 + F4 + F5 + F6 + F7 + F8 + F9 + F10

Combined Underwriting Assessment
    = Hazard Profile establishes BASELINE
    + Signal Score identifies CURRENT PROBLEMS
    + Pattern Detection finds COMPOUND RISK STORIES
    → Tier Classification: WIN / WANT / WRITE / WATCH / WALK / NO TOUCH
```

The Hazard Profile should influence:
1. **The inherent risk baseline** (already computed in `inherent_risk.py`) -- should incorporate hazard dimensions beyond just industry and market cap
2. **The tier boundary assessment** -- a company with IES=80 and clean signals should still be WATCH tier, not WIN
3. **The narrative framing** in the worksheet -- "This company's inherent exposure profile is [X] because [hazard summary]"
4. **The pricing model** -- hazard-driven base rate before signal-driven adjustments

### How This Differs from INHERENT_RISK_BASELINE_RESEARCH.md

The existing Inherent Risk Baseline document focuses on **actuarial frequency and severity** -- what the claim rate is for a company with these characteristics. This Hazard Dimensions research is broader:

| Dimension | Inherent Risk Baseline | Hazard Profile |
|-----------|----------------------|----------------|
| Market cap | Primary frequency driver | Included (via industry + maturity factors) |
| Industry sector | Second frequency driver | Included (H1-01) plus deeper industry analysis |
| IPO recency | Frequency multiplier | Included (H5-01) plus method and maturity |
| Management quality | Not covered | Core dimension (H2 category) |
| Governance structure | Not covered | Core dimension (H4 category) |
| Business model complexity | Not covered | Core dimension (H1-02 through H1-13) |
| Financial structure | Not covered | Core dimension (H3 category) |
| External environment | Not covered | Core dimension (H6 category) |
| Emerging risks | Not covered | Core dimension (H7 category) |
| Interaction effects | Not covered | Multiplicative combinations (Section 10) |

The Hazard Profile subsumes the Inherent Risk Baseline and extends it into the qualitative dimensions that experienced underwriters evaluate intuitively but that the current system does not formalize.

---

## 14. D&O Underwriting Application Questions Mapped to Hazard Dimensions

Standard D&O underwriting applications capture hazard information through specific questions. The following maps common application questions to hazard dimensions, confirming that the taxonomy aligns with industry practice.

### Business & Operations Questions

| Application Question | Hazard Dimension |
|---------------------|-----------------|
| "Describe the nature of your business and primary products/services." | H1-01, H1-02 |
| "What percentage of revenue is derived from international operations?" | H1-04 |
| "Do you have operations in countries with a CPI score below 50?" | H1-04 |
| "What percentage of revenue is derived from government contracts?" | H1-06 |
| "Have you completed any M&A transactions in the past 3 years?" | H1-08 |
| "What is your revenue growth rate over the past 3 years?" | H1-09 |
| "Do you have multiple classes of stock?" | H1-10 |
| "What are your primary regulatory bodies?" | H1-03 |

### Management & Board Questions

| Application Question | Hazard Dimension |
|---------------------|-----------------|
| "Provide biographies for all directors and officers." | H2-01, H2-02, H2-04 |
| "Have any current officers or directors previously served as an officer or director of a company that was subject to bankruptcy, SEC investigation, or securities litigation?" | H2-01 (track record) |
| "Have there been any changes in the CEO, CFO, or General Counsel in the past 2 years?" | H2-07 |
| "Is the CEO also the Board Chair?" | H4-01 |
| "What percentage of directors are independent?" | H4-02 |

### Financial Structure Questions

| Application Question | Hazard Dimension |
|---------------------|-----------------|
| "Provide 3 years of audited financial statements." | H3-01, H3-04 |
| "Have there been any restatements or material weaknesses in the past 5 years?" | H3-04 (quality), H4-07 (controls) |
| "What is the company's debt-to-equity ratio?" | H3-01 |
| "Does the company have any off-balance-sheet arrangements?" | H3-02 |
| "Are there any pending or planned securities offerings?" | H3-08 |

### Governance Questions

| Application Question | Hazard Dimension |
|---------------------|-----------------|
| "Does the company have a Code of Conduct?" | H4-07 |
| "Does the company have a whistleblower hotline?" | H4-07 |
| "Does the board have an audit committee composed entirely of independent directors?" | H4-04 |
| "Does the company have a clawback policy?" | H4-06 |
| "Does the company have a shareholder rights plan (poison pill)?" | H4-03 |

Sources: Founder Shield, "Quick Tips for D&O Applications" (2025); Ames & Gough, "Underwriting Considerations for D&O Insurance" (2024); Vouch Insurance, "D&O Underwriting" (2025); Reuters Westlaw D&O Checklist (2024).

---

## 15. Academic and Actuarial Foundation

### Key Academic Studies Supporting the Hazard Framework

| Study | Finding | Hazard Dimensions Validated |
|-------|---------|---------------------------|
| Kim & Skinner (2012), "Measuring Securities Litigation Risk" | Industry + size + growth + volatility explain most litigation risk; governance adds little | H1-01, H1-09, H5-01 (structural > behavioral) |
| Cornerstone Research (2024), "Securities Class Action Filings" | 225 filings; tech+biotech = 37%; AI filings doubled | H1-01, H6-03, H7-01 |
| Stanford SLA, "IPO Litigation Risk" | 14-21% of IPOs sued within 3 years; 74% within 5 quarters | H5-01, H5-02 |
| Allianz Commercial (2026), "D&O Insurance Insights" | Global insolvencies +24% above pre-pandemic; regulatory enforcement top claim driver | H3-01, H6-02, H6-05 |
| ABA (2023), "SPAC Litigation by the Numbers" | De-SPAC filing rate 17-24% per transaction | H5-02 |
| Weterings (2013), "D&O Insurance and Moral Hazard" | D&O insurance design affects director behavior; exclusions reduce moral hazard | H4-07 (controls matter) |
| Woodruff Sawyer (2026), "D&O Looking Ahead" | AI disclosure risks, reincorporation trends, dismissals up 74% | H7-01, H4-08, H6-06 |
| NERA (2024), "Full-Year Review" | FPI filing rate ~2.7% vs. 4.19% overall; large-cap targeting increase | H5-04, H5-03 |

### Actuarial Classification Principles

The Casualty Actuarial Society's Risk Classification Statement of Principles (2005) establishes that risk classification variables must be:

1. **Accurate**: The variable must predict the loss measure it is intended to predict.
2. **Homogeneous**: Risks within a class should have similar expected loss experience.
3. **Credible**: Sufficient data must exist to evaluate the variable's predictive power.
4. **Separable**: Variables should not be redundant with other variables in the model.

Applied to the hazard framework:
- **Accuracy**: Industry sector, market cap, IPO age are proven predictors (Kim & Skinner). Management experience and governance are supported by underwriter practice but lack the same statistical rigor.
- **Homogeneity**: The proposed tiers (EXTREME through MINIMAL) should produce meaningfully different claim rates within each tier.
- **Credibility**: Some dimensions (industry, market cap) have high credibility from large datasets. Others (management experience, business model complexity) have lower credibility and require Bayesian approaches with informative priors.
- **Separability**: Some dimensions overlap (market cap correlates with board quality, industry correlates with regulatory intensity). The scoring framework should address this through weight calibration to avoid double-counting.

Source: Casualty Actuarial Society, "Risk Classification Statement of Principles" (2005); American Academy of Actuaries, "Risk Classification Statement of Principles" (2025).

---

## 16. Implementation Recommendations

### Phase 1: Core Hazard Scoring (Immediately Implementable)

These dimensions can be scored automatically from data already acquired by the system:

| Dimension | Data Already Available | Implementation |
|-----------|----------------------|----------------|
| H1-01: Industry sector risk | SIC/NAICS from company profile | Config lookup |
| H1-09: Speed of growth | Revenue data from yfinance | Calculation |
| H1-10: Dual-class structure | Proxy data (if extracted) | Check extraction |
| H3-01: Leverage | Financial statements | Calculation |
| H3-03: Goodwill-heavy | Financial statements | Calculation |
| H3-06: Pre-revenue / cash burn | Financial statements | Calculation |
| H4-01: Combined CEO/Chair | Proxy data | Lookup |
| H4-02: Board independence | Governance extraction | Existing check |
| H5-01: IPO recency | Company profile | Date calculation |
| H5-03: Index membership | yfinance | Lookup |
| H6-01: Market cycle | Market data | VIX / P/E calculation |

### Phase 2: LLM-Extracted Hazard Dimensions

These require LLM extraction from filing text (already part of the EXTRACT pipeline, but may need new extraction prompts):

| Dimension | Extraction Source | New Extraction Required |
|-----------|------------------|------------------------|
| H1-02: Business model complexity | 10-K business description, segment data | Yes -- structured complexity assessment |
| H1-03: Regulatory intensity | 10-K Item 1 "Regulation" section | Yes -- regulator count extraction |
| H1-05: Revenue model type | 10-K revenue recognition notes | Yes -- revenue model classification |
| H1-06: Customer concentration | 10-K concentration disclosures | Partial -- may already exist |
| H2-01: Management experience | Proxy biographies | Yes -- experience assessment |
| H2-06: Key person dependency | 10-K risk factors | Yes -- key person extraction |
| H4-03: Anti-takeover provisions | Proxy governance section | Yes -- provision enumeration |
| H4-04: Audit committee quality | Proxy audit committee report | Partial |

### Phase 3: Web-Enriched Hazard Dimensions

These require web search and external data:

| Dimension | External Source | Acquisition Method |
|-----------|----------------|-------------------|
| H2-02: Industry expertise match | Prior company data | Web search |
| H2-08: Tone at the top | News, Glassdoor, earnings calls | Brave Search, sentiment analysis |
| H6-02: Industry regulatory spotlight | Current news | Brave Search |
| H6-03: Industry litigation wave | Stanford SCAC | Playwright scraping |
| H7-01: AI exposure | Company AI disclosures, news | Multi-source |
| H7-05: Social media risk | Social media analysis | Web search |

### Configuration Approach

Following the project's pattern of config-driven architecture, the hazard scoring should be implemented as:

1. **`hazard_dimensions.json`** -- dimension definitions, weights, thresholds, scoring rules
2. **`hazard_interactions.json`** -- interaction effect definitions and multipliers
3. **Hazard scoring module** in `stages/score/` -- analogous to `factor_scoring.py`
4. **Hazard data extraction** in `stages/extract/` -- new extraction prompts for hazard-specific data
5. **Hazard profile section** in `stages/render/` -- new worksheet section presenting the hazard profile

---

## 17. Summary: Complete Hazard Dimension Inventory

| ID | Dimension | Category | Max Score | Primary Data Source | Auto-Scorable? |
|----|-----------|----------|-----------|-------------------|----------------|
| H1-01 | Industry Sector Risk Tier | Business | 10 | SIC/NAICS | YES |
| H1-02 | Business Model Complexity | Business | 5 | 10-K business description | LLM |
| H1-03 | Regulatory Intensity | Business | 5 | 10-K Item 1 | LLM |
| H1-04 | Geographic Complexity | Business | 5 | 10-K geographic data | LLM |
| H1-05 | Revenue Model Manipulation Surface | Business | 5 | 10-K rev rec notes | LLM |
| H1-06 | Customer/Supplier Concentration | Business | 3 | 10-K disclosures | LLM |
| H1-07 | Capital Intensity | Business | 3 | Financial statements | YES |
| H1-08 | M&A Activity & Integration | Business | 5 | 10-K business combos | LLM |
| H1-09 | Speed of Growth | Business | 5 | yfinance / financials | YES |
| H1-10 | Dual-Class Structure | Business | 3 | Proxy / profile | YES |
| H1-11 | Non-GAAP Reliance | Business | 3 | Earnings releases | LLM |
| H1-12 | Technology Platform Dependency | Business | 2 | 10-K risk factors | LLM |
| H1-13 | IP Dependency | Business | 2 | 10-K disclosures | LLM |
| H2-01 | Management Public Company Experience | People | 5 | Proxy biographies | LLM |
| H2-02 | Industry Expertise Match | People | 3 | Proxy + web search | LLM + Web |
| H2-03 | Scale Experience Mismatch | People | 3 | Proxy + prior companies | LLM + Web |
| H2-04 | Board Governance Experience | People | 5 | Proxy | LLM |
| H2-05 | Founder-Led vs. Professional | People | 3 | Proxy / history | LLM |
| H2-06 | Key Person Dependency | People | 3 | 10-K risk factors | LLM |
| H2-07 | Management Turnover | People | 3 | 8-K filings | YES |
| H2-08 | Tone at the Top | People | 3 | Multi-source | LLM + Web |
| H3-01 | Leverage / Capital Structure | Financial | 5 | Financial statements | YES |
| H3-02 | Off-Balance Sheet Arrangements | Financial | 3 | 10-K notes | LLM |
| H3-03 | Goodwill-Heavy Balance Sheet | Financial | 3 | Balance sheet | YES |
| H3-04 | Earnings Quality Characteristics | Financial | 5 | Financial statements | Partial |
| H3-05 | Cash Flow vs. Earnings Divergence | Financial | 3 | Financial statements | YES |
| H3-06 | Pre-Revenue / Cash Burn | Financial | 5 | Financial statements | YES |
| H3-07 | Related Party Transaction Complexity | Financial | 3 | Proxy Item 404 | LLM |
| H3-08 | Pending Securities Offering | Financial | 4 | SEC EDGAR filings | YES |
| H4-01 | Combined CEO / Board Chair | Governance | 3 | Proxy | YES |
| H4-02 | Board Independence Level | Governance | 3 | Proxy | YES |
| H4-03 | Anti-Takeover Provisions | Governance | 5 | Proxy / charter | LLM |
| H4-04 | Audit Committee Quality | Governance | 4 | Proxy | LLM |
| H4-05 | Shareholder Rights & Engagement | Governance | 3 | Proxy / vote results | Partial |
| H4-06 | Executive Compensation Structure | Governance | 3 | Proxy CD&A | LLM |
| H4-07 | Compliance Infrastructure | Governance | 3 | Proxy / 10-K / website | LLM |
| H4-08 | State of Incorporation | Governance | 2 | SEC EDGAR | YES |
| H5-01 | IPO Recency | Maturity | 5 | Company profile | YES |
| H5-02 | Method of Going Public | Maturity | 4 | SEC EDGAR filing history | YES |
| H5-03 | Exchange / Index Membership | Maturity | 3 | yfinance / profile | YES |
| H5-04 | ADR / Foreign Private Issuer | Maturity | 2 | SEC EDGAR | YES |
| H5-05 | Seasoning and Track Record | Maturity | 3 | SEC EDGAR / SCAC | Partial |
| H6-01 | Market Cycle Position | Environment | 3 | Market data | YES |
| H6-02 | Industry Regulatory Spotlight | Environment | 3 | News / web search | Web |
| H6-03 | Industry Litigation Wave | Environment | 3 | Stanford SCAC | Web |
| H6-04 | Political / Policy Environment | Environment | 2 | News analysis | Web |
| H6-05 | Interest Rate / Credit Environment | Environment | 2 | Market data | YES |
| H6-06 | Plaintiff Attorney Activity | Environment | 1 | Cornerstone data | Periodic |
| H6-07 | Geopolitical Risk | Environment | 2 | 10-K / news | LLM + Web |
| H7-01 | AI Adoption & Governance | Emerging | 4 | 10-K / earnings calls | LLM |
| H7-02 | Cybersecurity Governance | Emerging | 3 | 10-K Item 1C / proxy | LLM |
| H7-03 | ESG / Climate Disclosure | Emerging | 3 | 10-K / ESG reports | LLM |
| H7-04 | Crypto / Digital Asset Exposure | Emerging | 3 | 10-K / revenue data | LLM |
| H7-05 | Social Media / Public Persona Risk | Emerging | 2 | Web / social media | Web |
| H7-06 | Workforce / Labor Model | Emerging | 3 | 10-K / news | LLM |

**Total dimensions: 55**
**Auto-scorable: 19 (35%)**
**LLM-extractable: 26 (47%)**
**Web-dependent: 10 (18%)**

---

## References

### Industry Reports and Market Analysis
- Allianz Commercial. "D&O Insurance Insights 2026." (2026). https://commercial.allianz.com/news-and-insights/news/directors-and-officers-insurance-insights-2026.html
- Cornerstone Research. "Securities Class Action Filings -- 2024 Year in Review." (2025). https://www.cornerstone.com/insights/reports/securities-class-action-filings/
- Cornerstone Research. "Securities Class Action Settlements -- 2024 Review and Analysis." (2025). https://www.cornerstone.com/insights/reports/securities-class-action-settlements/
- NERA Economic Consulting. "Recent Trends in Securities Class Action Litigation: 2024 Full-Year Review." (2025).
- Woodruff Sawyer. "2026 D&O Looking Ahead: What Boards Need to Know About Emerging Risks and Insurance Trends." (2025). https://woodruffsawyer.com/insights/do-looking-ahead-guide
- Aon. "Management Liability Insurance Market in 2025: Stability Amid Evolving Risks." (2025). https://www.aon.com/en/insights/articles/financial-services-group/management-liability-insurance-market-in-2025-stability-amid-evolving-risks

### Underwriting Practice Guides
- Ames & Gough. "Underwriting Considerations for D&O Insurance." (2024). https://amesgough.com/underwriting-consideration-for-do-insurance/
- Alliant. "Understanding Five D&O Risk Factors." https://alliant.com/news-resources/article-understanding-five-do-risk-factors/
- The D&O Diary. "What Do D&O Insurers Look For?" (2008). https://www.dandodiary.com/2008/05/articles/d-o-insurance/what-do-do-insurers-look-for/
- Vouch Insurance. "Directors & Officers Insurance Underwriting." (2025). https://www.vouch.us/insurance101/directors-and-officers-insurance-underwriting
- Founder Shield. "Quick Tips for D&O Applications." (2025). https://foundershield.com/blog/quick-tips-completing-directors-and-officers-insurance-application/
- MPR Underwriting. "How to Choose a D&O Liability Limit." https://www.mprunderwriting.com/how-to-choose-a-do-liability-limit/
- Chubb. "Global Risk Spotlight: Why Multinationals Must Carefully Consider Local D&O." (2020). https://www.chubb.com/content/dam/chubb-sites/external/us/en/businesses/campaign/_assets/multinational/chubb_multinational_directorsofficers_082820-1.pdf

### Academic Research
- Kim, I. & Skinner, D.J. (2012). "Measuring Securities Litigation Risk." *Journal of Accounting and Economics*, 53(1), 290-310. https://www.sciencedirect.com/science/article/abs/pii/S0165410111000681
- Weterings, W. (2013). "Directors' & Officers' Liability, D&O Insurance and Moral Hazard." SSRN. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2153129
- Stanford Securities Litigation Analytics. https://sla.law.stanford.edu/
- Stanford Securities Class Action Clearinghouse. https://securities.stanford.edu/

### Legal and Regulatory Sources
- SEC. "SPACs, IPOs and Liability Risk under the Securities Laws." (2021). https://www.sec.gov/newsroom/speeches-statements/spacs-ipos-liability-risk-under-securities-laws
- American Bar Association. "SPAC Litigation by the Numbers." (2023).
- FCPAméricas. "D&O and FCPA: What Underwriters Should Know About Assessing Corruption Risk." (2024). https://fcpamericas.com/english/enforcement/do-and-fcpa-what-underwriters-should-know-about-assessing-corruption-risk/
- Harvard Law School Forum on Corporate Governance. Various publications on dual-class shares, derivative suits, and governance. https://corpgov.law.harvard.edu/

### Actuarial Standards
- Casualty Actuarial Society. "Risk Classification Statement of Principles." (2005). https://www.casact.org/sites/default/files/old/forum_88fforum_88ff509.pdf
- American Academy of Actuaries. "Risk Classification Statement of Principles." (2025). https://actuary.org/wp-content/uploads/2025/05/risk.pdf

---

*Research compiled: 2026-02-11*
*Phase: 24-check-calibration-knowledge-enrichment*
*Purpose: Foundation for Hazard Profile Score implementation in the D&O underwriting worksheet system*
