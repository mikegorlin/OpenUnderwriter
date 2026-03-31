# D&O UNDERWRITING CHECKLIST v1.1 (FINAL)

**Version**: 1.1 Final - Consolidated & Hierarchical  
**Last Updated**: October 29, 2025  
**Total Checks**: ~200 (44 Quick Screen + ~160 Comprehensive)  
**Optimized for**: Token efficiency & clarity

---

## 📋 FRAMEWORK OVERVIEW

### Purpose
Systematic D&O risk assessment for public company underwriting. Each check represents one risk area/hazard with multiple related factors assessed together.

### Hierarchical Numbering System
- **QS-A.1** = Quick Screen, Category A (Litigation), Check 1
- **A.1.1** = Section A (Litigation & Regulatory), Subcategory 1 (Company Classification), Check 1
- **B.3.2** = Section B (Financial Health), Subcategory 3 (Balance Sheet), Check 2

### Structure
- **PART 1: QUICK SCREEN** (43 checks) - Auto-decline triage
- **PART 2: COMPREHENSIVE ANALYSIS** (~160 checks) - Full assessment
  - Section A: Litigation & Regulatory Risk (~25 checks)
  - Section B: Financial Health & Quantitative (~35 checks)
  - Section C: Business Model & Operations (~20 checks)
  - Section D: Leadership & Governance (~25 checks)
  - Section E: Market Dynamics & External Risks (~20 checks)
  - Section F: Alternative Data & Blind Spots (~30 checks)

### Decision Rules
1. **Quick Screen**: 3+ red flags → DECLINE immediately
2. **Section Stop Conditions**: Specific triggers → DECLINE, skip remaining sections
3. **Overall**: >50 red flags (>25% fail rate) → DECLINE

### Color Coding
- 🟢 GREEN = Pass / Low Risk
- 🟡 YELLOW = Caution / Moderate Risk
- 🔴 RED = Fail / High Risk / Critical
- 🟣 PURPLE = Unknown / Requires Research

---

## PART 1: QUICK SCREEN (43 Checks)

**Purpose**: 5-10 minute triage for immediate auto-decline triggers  
**Decision Rule**: 3+ red flags = DECLINE immediately, do not proceed to comprehensive analysis

---

### QS-A: LITIGATION & REGULATORY HAZARDS (8 checks)

**QS-A.1: Securities Class Action Litigation**
- **Hazard**: Active securities fraud lawsuit creating known loss
- **Sources**: Stanford Clearinghouse, 8-K, 10-K/10-Q Legal Proceedings
- **Assess**: Active lawsuit filed <24 months, class period, allegations, estimated settlement
- **Criteria**: 🔴 Active lawsuit + settlement >$50M or >10% market cap | ✅ None

**QS-A.2: SEC Enforcement Action**
- **Hazard**: SEC civil enforcement indicating accounting/disclosure violations
- **Sources**: SEC.gov Litigation Releases, 8-K
- **Assess**: Active enforcement, settlement <12 months, penalties, officer bars
- **Criteria**: 🔴 Active action or settlement <12mo + penalties >$25M or officer bars | ✅ None

**QS-A.3: DOJ Criminal Investigation**
- **Hazard**: Criminal charges against company or executives
- **Sources**: DOJ press releases, 8-K, news
- **Assess**: Criminal investigation disclosed, charges filed, target letters
- **Criteria**: 🔴 Criminal charges filed or target letter disclosed | ✅ None

**QS-A.4: Derivative Lawsuit Cascade**
- **Hazard**: Multiple derivative suits indicating governance failure
- **Sources**: Delaware Chancery, PACER, company disclosures
- **Assess**: Number of active derivative suits, Caremark claims, parallel securities action
- **Criteria**: 🔴 2+ derivative suits + Caremark claims + parallel securities action | ✅ <2 suits

**QS-A.5: Financial Restatement with Investigation**
- **Hazard**: Accounting failure triggering regulatory scrutiny
- **Sources**: 8-K Item 4.02, SEC comment letters
- **Assess**: Restatement announced, SEC investigation, magnitude of restatement
- **Criteria**: 🔴 Restatement + SEC investigation + >5% revenue or >10% net income | ✅ None

**QS-A.6: Auditor Resignation**
- **Hazard**: Auditor fled due to fraud concerns or disagreement
- **Sources**: 8-K Item 4.01
- **Assess**: Auditor resigned (not dismissed) <12 months, cited reasons
- **Criteria**: 🔴 Resigned + cited disagreement or fraud concerns | ✅ None or dismissed by company

**QS-A.7: Bankruptcy Filing**
- **Hazard**: Insolvency triggering automatic D&O claims
- **Sources**: 8-K, PACER bankruptcy records
- **Assess**: Chapter 11 or Chapter 7 filing
- **Criteria**: 🔴 Any bankruptcy filing | ✅ None

**QS-A.8: FCPA Criminal Charges**
- **Hazard**: Foreign corruption prosecution
- **Sources**: DOJ FCPA database, 8-K
- **Assess**: Criminal charges filed, penalty amount
- **Criteria**: 🔴 Criminal charges or penalty >$100M | ✅ None

---

### QS-B: FINANCIAL DISTRESS HAZARDS (8 checks)

**QS-B.1: Going Concern Warning**
- **Hazard**: Auditor doubts company can continue operations
- **Sources**: 10-K auditor's report
- **Assess**: Going concern warning, cash runway
- **Criteria**: 🔴 Going concern + cash runway <6 months | ✅ No warning

**QS-B.2: Negative Cash Position**
- **Hazard**: Out of cash with negative cash flow
- **Sources**: 10-Q/10-K balance sheet, cash flow statement
- **Assess**: Cash & equivalents, operating cash flow
- **Criteria**: 🔴 Negative cash + negative OCF | ✅ Positive cash

**QS-B.3: Debt Covenant Breach**
- **Hazard**: Debt default triggering acceleration
- **Sources**: 10-Q/10-K debt footnote, 8-K Item 1.03
- **Assess**: Covenant breach, waiver status, default status
- **Criteria**: 🔴 Breach + no waiver + debt in default | ✅ Compliant

**QS-B.4: Delisting Notice**
- **Hazard**: Exchange delisting due to non-compliance
- **Sources**: 8-K Item 3.01, exchange notices
- **Assess**: Delisting notice, stock price <$1, compliance plan
- **Criteria**: 🔴 Delisting notice + stock <$1 for >30 days | ✅ Compliant

**QS-B.5: Mass Layoffs**
- **Hazard**: Severe cost-cutting indicating distress
- **Sources**: 8-K Item 5.02, WARN Act notices, news
- **Assess**: Layoffs as % workforce, timing, financial condition
- **Criteria**: 🔴 Layoffs >30% <6 months + (going concern or negative cash) | ✅ <30%

**QS-B.6: Revenue Collapse**
- **Hazard**: Business model failure
- **Sources**: 10-Q income statement
- **Assess**: Revenue decline YoY, gross margin
- **Criteria**: 🔴 Revenue down >50% YoY + negative gross margin | ✅ <50% decline

**QS-B.7: Asset Impairment**
- **Hazard**: Major asset write-downs indicating overpayment or failure
- **Sources**: 10-Q/10-K impairment disclosures
- **Assess**: Impairment as % total assets, goodwill impairment
- **Criteria**: 🔴 Impairment >25% total assets <12mo + goodwill impairment >50% | ✅ <25%

**QS-B.8: Pre-Revenue Biotech Cash Burn**
- **Hazard**: Clinical-stage biotech running out of cash
- **Sources**: 10-Q cash burn, clinical trial results
- **Assess**: Cash runway, revenue status, Phase 3 results, financing/partnership
- **Criteria**: 🔴 Pre-revenue + <12mo cash + Phase 3 failure + no financing | ✅ >12mo cash

---

### QS-C: BUSINESS MODEL COLLAPSE HAZARDS (6 checks)

**QS-C.1: FDA Complete Response Letter (CRL)**
- **Hazard**: FDA drug rejection destroying business model
- **Sources**: 8-K, FDA.gov, ClinicalTrials.gov
- **Assess**: CRL for lead product, product % projected revenue
- **Criteria**: 🔴 CRL for lead product + product >60% projected revenue | ✅ No CRL

**QS-C.2: Product Recall**
- **Hazard**: Safety recall destroying revenue
- **Sources**: FDA.gov recalls, 8-K
- **Assess**: Recall class, recalled products % revenue
- **Criteria**: 🔴 Class I recall <12mo + recall >50% revenue products | ✅ No Class I recall

**QS-C.3: Loss of Major Customer**
- **Hazard**: Customer concentration risk realized
- **Sources**: 10-Q/10-K customer disclosures, 8-K Item 1.02
- **Assess**: Lost customer % revenue, replacement identified
- **Criteria**: 🔴 Lost customer >25% revenue + no replacement | ✅ <25% or replacement

**QS-C.4: Failed M&A Integration**
- **Hazard**: Acquisition destroyed value
- **Sources**: 10-Q/10-K M&A disclosures, impairment charges
- **Assess**: Acquisition timing, goodwill impairment, synergies achieved
- **Criteria**: 🔴 Acquisition <24mo + goodwill impairment >50% + synergies not achieved | ✅ Successful

**QS-C.5: Patent Expiration**
- **Hazard**: Loss of IP protection enabling generic competition
- **Sources**: 10-K patent disclosures, FDA Orange Book
- **Assess**: Key patent expiration, generic competition, pipeline, patent % revenue
- **Criteria**: 🔴 Key patent expired + generics + no pipeline + patent >50% revenue | ✅ Protected

**QS-C.6: Technology Obsolescence**
- **Hazard**: Core technology disrupted
- **Sources**: 10-K risk factors, industry analysis
- **Assess**: Technology obsolescence, next-gen product, revenue trend
- **Criteria**: 🔴 Core tech obsolete + no next-gen + revenue down >30% YoY | ✅ Current tech

---

### QS-D: GOVERNANCE CRISIS HAZARDS (6 checks)

**QS-D.1: CEO/CFO Simultaneous Departure**
- **Hazard**: Leadership crisis indicating hidden problems
- **Sources**: 8-K Item 5.02, press releases
- **Assess**: CEO/CFO departure timing, planned vs. unplanned
- **Criteria**: 🔴 Both departed within 90 days + not disclosed as planned | ✅ Planned succession

**QS-D.2: Whistleblower Allegations**
- **Hazard**: Internal fraud allegations going public
- **Sources**: News, 8-K, SEC filings
- **Assess**: Public whistleblower allegations, investigation opened
- **Criteria**: 🔴 Public whistleblower fraud allegations + SEC/DOJ investigation | ✅ None

**QS-D.3: Board Mass Resignation**
- **Hazard**: Board exodus indicating governance failure
- **Sources**: 8-K Item 5.02, DEF 14A
- **Assess**: Board resignations % total board, cited reasons
- **Criteria**: 🔴 >30% board resigned <6mo + cited disagreement | ✅ <30% or planned

**QS-D.4: Founder/CEO Fraud Charges**
- **Hazard**: Top executive charged with fraud
- **Sources**: DOJ/SEC press releases, news
- **Assess**: Fraud charges (civil or criminal) against CEO/founder
- **Criteria**: 🔴 Fraud charges filed | ✅ None

**QS-D.5: Internal Controls Material Weakness**
- **Hazard**: Control failure enabling fraud or error
- **Sources**: 10-K Item 9A
- **Assess**: Material weakness disclosed, remediation status, fraud risk area
- **Criteria**: 🔴 Material weakness + not remediated + related to revenue/fraud | ✅ Effective controls

**QS-D.6: Related Party Transactions**
- **Hazard**: Self-dealing by insiders
- **Sources**: 10-K related party disclosures, proxy
- **Assess**: Related party transactions % revenue/assets, arm's length
- **Criteria**: 🔴 Related party >10% revenue/assets + not arm's length | ✅ <10% or arm's length

---

### QS-E: MARKET COLLAPSE HAZARDS (7 checks)

**QS-E.1: Stock Price Collapse**
- **Hazard**: >80% stock decline indicating catastrophic failure
- **Sources**: Yahoo Finance, 8-K event analysis
- **Assess**: Stock decline from 52-week high, trigger event
- **Criteria**: 🔴 Stock down >80% + driven by fraud allegations or regulatory action | ✅ <80%

**QS-E.2: Short Seller Fraud Report**
- **Hazard**: Credible fraud allegations by short sellers
- **Sources**: Hindenburg, Muddy Waters, Citron, company response
- **Assess**: Short seller report, fraud allegations, stock reaction, company rebuttal
- **Criteria**: 🔴 Short seller fraud report + stock down >40% + no effective rebuttal | ✅ No report

**QS-E.3: Trading Halt**
- **Hazard**: Exchange-initiated halt for regulatory concerns
- **Sources**: Exchange notices, 8-K
- **Assess**: Trading halt, who initiated, reason
- **Criteria**: 🔴 Exchange-initiated halt (not company-requested) + regulatory concern | ✅ No halt

**QS-E.4: Insider Selling Cascade**
- **Hazard**: Insiders fleeing before bad news
- **Sources**: Form 4, insider transaction databases
- **Assess**: Insider selling % holdings, 10b5-1 plans, stock performance
- **Criteria**: 🔴 Insiders sold >50% <6mo + no 10b5-1 + stock down >30% | ✅ <50% or planned

**QS-E.5: Failed Financing**
- **Hazard**: Cannot raise capital when needed
- **Sources**: 8-K, press releases
- **Assess**: Announced financing, outcome, liquidity concerns
- **Criteria**: 🔴 Announced financing failed or downsized + liquidity concerns | ✅ Successful

**QS-E.6: Analyst Consensus Sell**
- **Hazard**: All analysts recommend selling
- **Sources**: Bloomberg, Yahoo Finance
- **Assess**: Analyst ratings distribution, price targets vs. current
- **Criteria**: 🔴 Majority "Sell" + avg price target >50% below current | ✅ Hold/Buy ratings

**QS-E.7: Stock Decline Attribution Analysis**
- **Hazard**: Stock declines indicating undisclosed problems or material events
- **Sources**: Yahoo Finance, 8-K, news, peer/sector comparison
- **Assess**: Any decline >10% in past 12 months - identify trigger event, date, magnitude, peer comparison, attribution (company-specific vs. sector-wide)
- **Criteria**: 
  - 🔴 Decline >20% + company-specific trigger (fraud allegations, regulatory action, earnings miss >20%, product failure) + underperformed peers/sector >30%
  - ⚠️ Decline 10-20% + company-specific trigger OR underperformed peers 15-30%
  - ✅ Decline <10% OR sector-wide decline (company performance in line with peers)
- **Required for ANY decline >10%**: Document trigger event with date, stock reaction magnitude, peer/sector performance same period, attribution analysis

---

### QS-F: ALTERNATIVE DATA CRISIS HAZARDS (6 checks)

**QS-F.1: Glassdoor Fraud Allegations**
- **Hazard**: Employees publicly alleging fraud/ethics violations
- **Sources**: Glassdoor, Form 4 cross-reference
- **Assess**: Glassdoor rating, reviews mentioning fraud/ethics, exec departures
- **Criteria**: 🔴 Rating <2.5 + >50 reviews mentioning "fraud"/"ethics" + exec departures | ✅ >2.5

**QS-F.2: Customer Review Collapse**
- **Hazard**: Product safety or fraud issues in customer feedback
- **Sources**: Amazon, App Store, Google Play, Trustpilot
- **Assess**: Rating trend, reviews citing safety/fraud
- **Criteria**: 🔴 Rating declined >4.0 to <2.0 <6mo + reviews cite safety/fraud | ✅ Stable >3.0

**QS-F.3: Regulatory Database Red Flags**
- **Hazard**: Pattern of regulatory violations
- **Sources**: FDA.gov, EPA.gov enforcement databases
- **Assess**: FDA warnings, EPA violations, consent decree, criminal referral
- **Criteria**: 🔴 >10 FDA warnings or >5 EPA violations <24mo + consent decree/criminal | ✅ <10/5

**QS-F.4: Viral Social Media Fraud Allegations**
- **Hazard**: Fraud allegations going viral on social media
- **Sources**: Twitter/X, Reddit, news aggregators
- **Assess**: Fraud allegations, social media engagement, mainstream media pickup, rebuttal
- **Criteria**: 🔴 Viral (>100K engagements) + mainstream pickup + no effective rebuttal | ✅ None

**QS-F.5: Investigative Journalism Exposé**
- **Hazard**: Major media fraud investigation
- **Sources**: WSJ, NYT, Bloomberg, Reuters
- **Assess**: Investigative exposé, fraud allegations, company response
- **Criteria**: 🔴 Major exposé alleging fraud + weak response or confirmed allegations | ✅ No exposé

**QS-F.6: CFPB Complaints Spike**
- **Hazard**: Consumer fraud pattern (financial services)
- **Sources**: CFPB Consumer Complaint Database
- **Assess**: Complaint trend YoY, fraud allegations
- **Criteria**: 🔴 Complaints up >300% YoY + allege fraud or systemic issues | ✅ <300%

---

### QS-G: EMERGING RISK HAZARDS (3 checks)

**QS-G.1: AI Regulatory Violation**
- **Hazard**: AI safety incident causing bodily injury
- **Sources**: State regulatory filings, news, litigation
- **Assess**: AI safety incident, bodily injury, litigation filed
- **Criteria**: 🔴 AI safety violation + bodily injury + litigation filed | ✅ Compliant

**QS-G.2: Cryptocurrency Regulatory Action**
- **Hazard**: Crypto enforcement by SEC/DOJ
- **Sources**: SEC.gov, DOJ press releases, 8-K
- **Assess**: SEC/DOJ enforcement re: crypto, criminal charges, penalty
- **Criteria**: 🔴 Enforcement + criminal charges or penalty >$100M | ✅ No action

**QS-G.3: SPAC Merger Litigation**
- **Hazard**: SPAC merger disclosure fraud
- **Sources**: Stanford Clearinghouse, 8-K, stock data
- **Assess**: SPAC merger, securities litigation, stock performance, settlement
- **Criteria**: 🔴 SPAC merger + litigation re: disclosures + stock down >60% + settlement >$50M | ✅ None

---

### QUICK SCREEN DECISION MATRIX

**Red Flag Count**:
- **0-1 red flags**: ✅ Proceed to Comprehensive Analysis
- **2 red flags**: ⚠️ Proceed with caution, document thoroughly
- **3+ red flags**: 🔴 **DECLINE** - Stop analysis immediately, document findings

---

