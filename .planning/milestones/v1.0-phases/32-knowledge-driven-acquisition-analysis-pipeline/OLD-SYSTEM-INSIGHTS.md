# Old System Insights: Gap Analysis vs Current System

## Purpose
Comprehensive analysis of the "Old System" (~547 checks across 6 modules + Quick Screen) vs the current system (388 checks in `brain/checks.json`). Identifies checks, data sources, thresholds, and real-world insights that the old system has but the current system does NOT.

## Methodology
- Read 20 Old System documents covering frameworks, module deep dives, real case analysis, and industry-specific patterns
- Extracted all 388 current check IDs and searched for old system topic coverage
- Categorized gaps by severity and implementation priority

---

## SECTION 1: HIGH-PRIORITY GAPS (Missing Entire Check Categories)

### 1.1 SPAC/De-SPAC Analysis (OLD: A.1.3, QS-43 | CURRENT: None)
**What's missing**: The old system has dedicated SPAC checks including:
- De-SPAC date and age (<24mo = high risk)
- Projections vs actuals comparison (missed >50% = CRITICAL)
- Stock performance post-merger
- SPAC-related litigation filed
- **Threshold**: De-SPAC <24mo + projections missed >50% + stock down >60% = CRITICAL

**Why it matters**: SPAC litigation was the #1 source of new securities class actions in 2022-2024. The current system has no SPAC detection or assessment.

**Data sources needed**: 8-K merger filings, original SPAC projections, post-merger actuals

---

### 1.2 Going Concern Warnings (OLD: A.6.2 | CURRENT: None explicitly)
**What's missing**: Dedicated check for auditor going concern opinion with cash runway assessment.
- Going concern + cash runway <6mo + no financing = CRITICAL
- Going concern + cash runway 6-12mo = HIGH
- Current system has `FIN.LIQ.cash_burn` but no explicit going concern flag

**Why it matters**: Going concern is one of the strongest predictors of D&O claims. The auditor has already flagged existential risk.

**Data source**: 10-K auditor's report, financial statements

---

### 1.3 Revenue Recognition Fraud Patterns (OLD: A.4.4, Module 2 Checks 1.1.1-1.1.8 | CURRENT: Partial)
**What's missing**: The old system has 8 specific revenue manipulation pattern checks:
1. **Bill-and-Hold arrangements** (1.1.3) - Revenue recognized before delivery
2. **Channel Stuffing** (1.1.4) - Forcing excess inventory on distributors
3. **Side Letter Agreements** (1.1.5) - Secret agreements modifying stated terms
4. **Round-tripping** (1.1.6) - Circular transactions creating false revenue
5. **Percentage of Completion manipulation** (1.1.2) - Overstating project completion
6. **Cookie jar reserves** - Saving earnings for future periods
7. **Big bath charges** - Taking all bad news at once
8. **Q4 revenue concentration** - Disproportionate year-end revenue

**Current coverage**: `FIN.QUALITY.q4_revenue_concentration` exists, but the specific fraud pattern taxonomy is absent.

**Why it matters**: Revenue recognition fraud is the #1 type of financial statement fraud. The old system explicitly names the patterns; the current system doesn't check for them by type.

---

### 1.4 Altman Z-Score (OLD: Module 2 | CURRENT: None)
**What's missing**: The Altman Z-Score distress prediction model.
- Z < 1.81 = Distress zone (HIGH risk)
- Z between 1.81-2.99 = Grey zone (MODERATE)
- Z > 2.99 = Safe zone (LOW)

**Current coverage**: Has Beneish M-Score (via Dechow F-Score), Montier C-Score, Enhanced Sloan, but no Altman Z-Score.

**Why it matters**: Altman Z-Score is the most widely used bankruptcy prediction model. Missing it is a significant analytical gap.

---

### 1.5 AGR Score / Accounting Governance Risk (OLD: Module 2 Check 5.1.1 | CURRENT: None)
**What's missing**: The Accounting Governance Risk score from MSCI/RiskMetrics.
- AGR <50 = 2.5x more likely to face securities litigation
- AGR <25 = 4x more likely

**Why it matters**: Direct correlation between AGR score and litigation probability, quantified by research.

---

### 1.6 Derivative Lawsuit Risk Factors (OLD: Module 1, derivative_lawsuit_patterns.md | CURRENT: Basic only)
**What's missing**: The old system has a detailed 5-category derivative suit risk assessment:
1. **Board-Level Conflicts of Interest** - Related-party M&A, director ownership in targets (Tesla/SolarCity: $60M)
2. **M&A Diligence Failures** - Problems discovered during sale process (Yahoo: $29M, Freeport: $138M)
3. **Egregious Behavior / Consumers / Employees** - Fake accounts, #MeToo, data breaches (Wells Fargo: $240M)
4. **Health & Human Safety (Caremark Claims)** - Product safety, opioid distribution (McKesson: $175M, PG&E: $90M)
5. **Massive Fraud** - Intentional deception (American Realty: $287M)

**Current coverage**: Has `LIT.SCA.derivative` and `LIT.SCA.demand` but these just track whether derivative suits exist, not whether derivative-suit-risk-factors are present.

**Key insight**: 2/3 of securities class actions have related derivative suits. The old system assesses which of the 5 categories the company's risk profile falls into. The current system only checks if derivatives already exist.

---

### 1.7 Scientific Community Monitoring (OLD: Module 6, Section 6 | CURRENT: None)
**What's missing**: 10+ checks covering scientific/academic community signals:
1. **PubPeer comments** on company-sponsored research
2. **Retraction Watch** for paper retractions
3. **Journal quality** assessment (predatory journals?)
4. **Key Opinion Leader (KOL) sentiment** at conferences
5. **Conference reception** for presentations
6. **Clinical trial endpoint changes** (moving goalposts)
7. **Publication of negative results** (or absence thereof)
8. **Citizen petitions to FDA**
9. **Data integrity allegations** from independent researchers
10. **Reproducibility concerns** raised by peers

**Case study proof**: In the SAVA (Cassava Sciences) analysis, PubPeer comments and scientific community skepticism predicted the stock collapse 3+ years before the SEC action. Short sellers used these signals. The current system would completely miss this.

**Why it matters**: For life sciences companies, scientific community signals are the earliest and most reliable predictors of fraud. They appear months to years before regulatory action.

---

### 1.8 Compensation Manipulation Patterns (OLD: Module 4 Checks 5.1-5.3 | CURRENT: Partial)
**What's missing**:
- **Spring-loading** - Granting options right before positive news
- **Backdating** - Retroactively dating options to lower strike price
- **Excise tax gross-ups** - Company pays executives' tax penalties (GOV.PAY has some comp checks but not these specific patterns)
- **Change-in-control triggers** - Single vs double trigger analysis
- **Share pledging** by insiders (using company stock as loan collateral)
- **Anti-hedging/pledging policy** existence check

**Current coverage**: `GOV.PAY.hedging` exists but focuses on hedging policy, not specific manipulation patterns. No pledge check, no spring-loading, no backdating detection.

---

### 1.9 ESG/Greenwashing Risk (OLD: Module 5, energy_sector_litigation_patterns.md | CURRENT: Minimal)
**What's missing**:
- **Greenwashing claims** - Gap between ESG marketing and actual practices
- **Internal climate reports** not publicly disclosed (Exxon precedent)
- **ESG marketing without substance** as litigation trigger
- **Board-level ESG oversight** existence
- **Climate risk disclosure** adequacy
- **Participation in climate denial** or lobbying

**Current coverage**: `FWRD.MACRO.climate_transition_risk` exists as a macro risk, but no specific greenwashing or ESG misrepresentation checks.

**Why it matters**: ESG litigation is one of the fastest-growing areas. The Exxon case established that internal climate assessments create disclosure obligations.

---

### 1.10 Dark Web / Emerging Threat Monitoring (OLD: Module 6 Check 10.1 | CURRENT: None)
**What's missing**:
- Dark web mentions of company data/credentials
- CVE vulnerabilities in company products
- Stolen data listings
- Pre-breach intelligence

**Why it matters**: Dark web signals can predict data breaches weeks to months before public disclosure.

---

## SECTION 2: MEDIUM-PRIORITY GAPS (Partially Covered but Missing Detail)

### 2.1 Stock Performance Attribution Analysis (OLD: B.5.1, Module 2 Checks 7.1-7.20 | CURRENT: Partial)
**What's missing**: The old system has 20 detailed stock analysis checks. Current system covers some but misses:
- **Death cross detection** (50-day MA crosses below 200-day MA)
- **Gap down analysis** (single-day gaps >5%)
- **Block trade analysis** (institutional selling patterns)
- **Options activity** (unusual put buying as predictor)
- **Days to cover** calculation from short interest
- **Short squeeze risk** assessment
- **Valuation vs peers** multiples comparison

**Current coverage**: Has `STOCK.PATTERN.*` (6 patterns), `STOCK.SHORT.*` (3 checks), `STOCK.VALUATION.*` (4 checks), but missing the specific technical indicators listed above.

---

### 2.2 Industry-Specific Operating Metrics (OLD: B.7.1-B.7.4, Module 2 Checks 8.1-8.4 | CURRENT: Very Partial)
**What's missing by industry**:

**SaaS/Software**:
- Rule of 40 (revenue growth + profit margin > 40%)
- Net Revenue Retention (NRR) with thresholds (<90% = CRITICAL)
- CAC Payback Period (>36mo = CRITICAL)
- LTV/CAC ratio (<1.0 = CRITICAL)
- Magic number (sales efficiency)
- Gross churn rate

**Life Sciences/Biotech**:
- Cash runway with clinical stage context
- Pipeline progression rates by phase
- FDA interaction history (CRLs, warning letters)
- ClinicalTrials.gov status monitoring
- Partnership/licensing deal assessment

**Retail**:
- Same-store sales / comparable sales trends
- Store count trends (expansion vs closure)
- Sales per square foot
- E-commerce penetration rate
- Inventory turnover with retail-specific thresholds

**Financial Services**:
- Net interest margin (NIM)
- Efficiency ratio
- Non-performing loan (NPL) ratio
- Loan loss reserve adequacy
- Regulatory capital ratios (CET1, Tier 1)

**Energy**:
- Reserve replacement ratio
- Finding & development costs
- Production costs vs commodity prices
- Hedging program assessment
- Reserve life in years
- Proved Undeveloped Reserves (PUD) on balance sheet

**Current coverage**: `FIN.SECTOR.energy` and `FIN.SECTOR.retail` exist but are single checks. The old system has 4-8 metrics per industry with specific thresholds.

---

### 2.3 Employee/Workplace Alternative Data (OLD: Module 6 Section 3 | CURRENT: Partial)
**What's missing beyond basic Glassdoor**:
- **Glassdoor fraud keywords** search ("cooking books", "pressure to meet numbers", "ethics violations")
- **CEO approval rating** trend (drop >20% = red flag)
- **"Recommend to friend"** percentage (<40% = concern)
- **Blind app** specific category monitoring (compensation complaints, layoff rumors)
- **Indeed reviews** for operational roles
- **Review surge detection** (sudden increase in negative reviews)
- **LinkedIn employee departures** by department (accounting/legal departures = red flag)
- **Job posting patterns** anomalies (mass hiring of lawyers, forensic accountants)

**Current coverage**: `FWRD.WARN.glassdoor_sentiment`, `FWRD.WARN.blind_posts`, `FWRD.WARN.indeed_reviews`, `FWRD.WARN.linkedin_departures`, `FWRD.WARN.job_posting_patterns`, `FWRD.WARN.compliance_hiring`, `FWRD.WARN.legal_hiring` exist. But the specific keyword-based fraud detection within reviews and surge detection patterns are not captured.

---

### 2.4 Customer/Consumer Complaint Databases (OLD: Module 6 Section 4 | CURRENT: Partial)
**What's missing**:
- **NHTSA complaints** for auto companies (already have `FWRD.WARN.nhtsa_complaints`)
- **FDA MedWatch / FAERS** adverse event reports (already have `FWRD.WARN.fda_medwatch`)
- **App Store rating trends** and review text analysis (already have `FWRD.WARN.app_ratings`)
- **BBB complaints** - Better Business Bureau patterns
- **Customer churn signals on social media** (already have `FWRD.WARN.customer_churn_signals`)
- **SimilarWeb/Sensor Tower** web traffic and app download trends (MISSING)
- **YouTube/TikTok** product failure viral videos (MISSING)

**Gap**: Web traffic/app download data and social media video sentiment are missing data sources.

---

### 2.5 Regulatory Database Deep Checks (OLD: Module 6 Section 5 | CURRENT: Partial)
**What's missing**:
- **FDA Form 483 observations** (inspection findings, not just warning letters)
- **FDA import alerts** (products barred from import)
- **EPA consent decrees** active status
- **OSHA fatality reports** (not just citations)
- **State AG investigation patterns** (multi-state = serious)
- **Congressional inquiries** (letters from Congress = escalation)
- **DOL ERISA audits** (401k plan issues)

**Current coverage**: Has `LIT.REG.epa_action`, `LIT.REG.osha_citation`, `LIT.REG.fda_warning`, `LIT.REG.state_ag`, `LIT.REG.dol_audit`, `LIT.REG.cfpb_action`. But these are litigation-stage checks looking at what already happened. The old system's Module 6 versions are forward-looking warning indicators that catch issues before they become formal actions.

---

### 2.6 Patent/IP Risk Assessment (OLD: Module 6 Section 7 | CURRENT: Minimal)
**What's missing**:
- **PTAB challenges** (Patent Trial and Appeal Board inter partes review)
- **NPE litigation** (Non-Practicing Entity / patent troll exposure)
- **Patent portfolio quality** assessment
- **Trade secret theft** vulnerability
- **IP concentration** (single patent = existential risk)
- **Patent cliff** analysis (pharmaceutical)

**Current coverage**: `LIT.OTHER.ip` and `LIT.OTHER.trade_secret` exist but track existing litigation, not IP risk exposure.

---

### 2.7 Insider Trading Pattern Analysis (OLD: Module 4 Checks 5.1-5.6, D.3 | CURRENT: Partial)
**What's missing**:
- **10b5-1 plan adoption timing** relative to material events (adopted right before bad news = suspect)
- **Share pledging** by insiders (stock as loan collateral - forced selling risk)
- **Hedging transactions** by executives (collar/put options on own stock)
- **Anti-hedging/pledging policy** existence and enforcement
- **Cluster selling** with specific timing thresholds

**Current coverage**: Has `GOV.INSIDER.10b5_plans`, `GOV.INSIDER.plan_adoption`, `GOV.INSIDER.cluster_sales`, `GOV.INSIDER.unusual_timing`, `EXEC.INSIDER.*`. But the specific 10b5-1 adoption timing analysis, share pledging, and hedging transaction checks are missing.

---

### 2.8 Shareholder Rights / Governance Provisions (OLD: Module 4 Checks 6.1-6.5 | CURRENT: Partial)
**What's missing**:
- **Dual-class sunset provisions** (do they expire? when?)
- **Written consent rights** (can shareholders act by written consent?)
- **Special meeting thresholds** (what % needed to call special meeting?)
- **Fee-shifting bylaws** (loser pays in litigation)
- **Forum selection** impact on derivative suits
- **Supermajority requirements** for specific actions

**Current coverage**: Has `GOV.RIGHTS.*` (10 checks) including dual_class, voting_rights, bylaws, takeover, proxy_access, forum_select, supermajority, action_consent, special_mtg, classified. The framework exists but some of the specific risk assessments (sunset provisions, fee-shifting bylaws) may need threshold refinement.

---

## SECTION 3: LOWER-PRIORITY GAPS (Nice to Have)

### 3.1 Litigation Funding Activity (OLD: Module 6 Check 10.6 | CURRENT: None)
Third-party litigation funding targeting the company. Presence of litigation funders increases probability and severity of suits.

### 3.2 Expert Witness Reports (OLD: Module 6 Check 10.7 | CURRENT: None)
Expert witnesses being retained against the company. Early indicator of litigation preparation.

### 3.3 Activist/Advocacy Campaign Monitoring (OLD: Module 6 Check 10.5 | CURRENT: Partial)
Current system has `GOV.ACTIVIST.*` but this covers investor activists. Missing: non-investor advocacy campaigns (environmental groups, consumer groups, labor organizations) that can escalate into litigation or regulatory action.

### 3.4 Unusual Accounting Firm Activity (OLD: Module 6 Check 10.8 | CURRENT: None)
Forensic accounting firms being engaged, unusual audit team changes, Big 4 partner rotation concerns.

### 3.5 Undisclosed Related Party Discovery (OLD: Module 6 Check 10.9 | CURRENT: Partial)
`FWRD.DISC.related_party_completeness` exists but doesn't cover proactive discovery of undisclosed related parties through web research.

### 3.6 Union Organizing Activity (OLD: Module 6 Check 10.5 | CURRENT: None)
Union campaigns, NLRB filings, collective bargaining disputes.

### 3.7 Competitive Intelligence Signals (OLD: Module 6 Section 9 | CURRENT: None)
- Competitive pricing actions
- Market share data from third parties
- Win/loss analysis from sales channels
- Competitor patent filings in company's space

---

## SECTION 4: UNIQUE THRESHOLDS AND CRITERIA

### 4.1 Quick Screen Auto-Decline Triggers (OLD: 40-43 checks | CURRENT: None as a category)

The old system has a dedicated "Quick Screen" of 40-43 binary checks that, if 3+ are RED, trigger immediate decline. Key thresholds:

| Check | Threshold | Current System |
|-------|-----------|----------------|
| QS-2.5 | Stock down >70% from peak | STOCK.PRICE has equivalent |
| QS-5.4 | Short interest >30% | STOCK.SHORT.position partial |
| QS-41 | AI Regulatory Violation | None |
| QS-42 | Cryptocurrency Regulatory Action | None |
| QS-43 | SPAC Merger Litigation | None |
| QS-1.7 | Multiple restatements + SEC investigation | FIN.ACCT.restatement_pattern partial |
| QS-3.5 | Board <50% independent | GOV.BOARD.independence covers |
| QS-4.3 | CEO + CFO departed same quarter | EXEC.DEPARTURE partial |

**Key gap**: The current system doesn't have an aggregated "auto-decline" fast-screen layer.

### 4.2 Decision Matrix Thresholds (OLD: Master Summary | CURRENT: None)

The old system defines underwriting decisions based on RED/YELLOW percentages:

| Decision | Criteria |
|----------|----------|
| **CLEAR DECLINE** | RED% > 20% OR any CRITICAL in Quick Screen |
| **DECLINE** | RED% 15-20% OR 3+ Quick Screen RED |
| **YELLOW-A** (write with restrictions) | RED% 10-15%, YELLOW% < 30% |
| **YELLOW-B** (refer to senior) | RED% 10-15%, YELLOW% > 30% |
| **GREEN** (standard write) | RED% < 5%, YELLOW% < 15% |

**Current system**: Has scoring (SCORE stage) but the explicit percentage-based decision matrix is different.

### 4.3 Non-Audit Fee Ratio (OLD: B.6.1 | CURRENT: Missing specific threshold)
- Non-audit fees >50% of audit fees = HIGH risk
- This is a well-established auditor independence red flag not explicitly checked.

### 4.4 Severity Criteria with Dollar Thresholds (OLD: Instructions Section | CURRENT: Different approach)
The old system uses specific dollar thresholds for severity:
- CRITICAL: Settlement >$50M OR >10% market cap
- HIGH: Settlement $10-50M
- MODERATE: Settlement <$10M

These concrete thresholds enable consistent classification. The current system may use different calibration.

---

## SECTION 5: DATA SOURCES THE OLD SYSTEM USES THAT WE MAY NOT ACQUIRE

### 5.1 Currently Not Acquired
| Source | Old System Use | Priority |
|--------|---------------|----------|
| **PubPeer** | Scientific integrity for life sciences | HIGH for biotech |
| **Retraction Watch** | Paper retractions for life sciences | HIGH for biotech |
| **ClinicalTrials.gov** | Clinical trial status monitoring | HIGH for biotech |
| **SimilarWeb / Sensor Tower** | Web traffic, app downloads | MEDIUM |
| **ISS / Glass Lewis** | Governance ratings (ISS QualityScore) | MEDIUM |
| **Dark web monitoring** | Pre-breach intelligence | LOW (hard to access) |
| **PTAB / USPTO** | Patent challenges | MEDIUM for tech/pharma |
| **NLRB** | Union organizing filings | LOW |
| **Congressional records** | Committee inquiries, hearing transcripts | LOW |
| **Litigation funding databases** | Third-party funder involvement | LOW |
| **CourtListener** | Court filings beyond PACER | MEDIUM |
| **YouTube/TikTok** | Product failure videos, viral complaints | LOW |

### 5.2 Currently Acquired but Underutilized
| Source | Old System Use | Current Gap |
|--------|---------------|-------------|
| **Glassdoor** | Fraud keyword search, CEO approval, "recommend" % | Have basic sentiment, missing keyword analysis |
| **LinkedIn** | Department-level departure tracking | Have headcount/departures, missing department breakdown |
| **SEC EDGAR** | Comment letters deep analysis | Have `LIT.REG.comment_letters` but old system does deeper content analysis |
| **Form 4** | 10b5-1 adoption timing analysis | Have filing tracking but not adoption-to-event timing |
| **DEF 14A** | Compensation manipulation patterns | Have basic comp checks, missing pattern detection |

---

## SECTION 6: REAL-WORLD CASE INSIGHTS

### 6.1 Cassava Sciences (SAVA) - Scientific Community Predicted Collapse
**Timeline of signals**:
1. **2020-2021**: PubPeer comments raised data integrity concerns about published research
2. **2021**: Citizen petition filed with FDA questioning trial data
3. **2021**: Short seller reports referenced scientific community concerns
4. **2022**: SEC investigation opened
5. **2023**: FDA rejection / clinical trial failures
6. **2024-2025**: Securities class actions, settlements

**What the current system would catch**: Stock decline, short seller reports, SEC investigation (all AFTER the fact)
**What the current system would MISS**: PubPeer comments, citizen petitions, scientific community skepticism (3+ YEARS earlier)

**Lesson**: For life sciences companies, scientific community monitoring is the earliest and most valuable signal. The current system has zero coverage here.

### 6.2 CoreWeave - AI Infrastructure Bubble Warning Signs
**Key signals from old system's AI 4-Lens Framework**:
1. **Circular deals** - Microsoft is both customer (67% revenue) and investor
2. **Operating margin (4%) < interest rate (8-10%)** - Structurally unprofitable
3. **Single customer concentration** (67%) - Existential dependency
4. **CEO credibility gaps** - Contradictory statements on earnings calls
5. **Failed merger** (Woven Intelligence) - Deal collapsed during due diligence
6. **Default insurance soaring** (7.9%) - Market pricing in default risk

**What the current system would catch**: Customer concentration, operating margins, debt levels, stock decline
**What the current system would MISS**: The circular deal detection, operating margin vs interest rate comparison as a structural check, CEO credibility analysis from earnings call language, default insurance (CDS) spread monitoring

### 6.3 Oracle - Debt-Fueled AI Capex Bubble
**Key signals**:
1. **Capex/OCF ratio 571%** (Q2 FY2026) - Spending 5.7x operating cash flow on capex
2. **$248B in new lease commitments** - Off-balance sheet obligations dwarfing revenue
3. **500% debt-to-equity ratio** - Far exceeding all cloud peers
4. **Dependency on single partnership** (OpenAI) for AI strategy justification

**What the current system would catch**: Debt levels, leverage ratios, stock decline
**What the current system would MISS**: The capex/OCF ratio as a specific check, lease commitment analysis (off-balance sheet), the single-partnership dependency risk

### 6.4 Wells Fargo - Derivative Suit for Culture Failure ($240M)
**Key signals the old system flags**:
1. Aggressive sales culture with commission-based compensation
2. Employee complaints about sales pressure (would show on Glassdoor)
3. Increasing customer complaints to CFPB
4. High turnover in branch operations

**Lesson**: The largest derivative settlement ($240M) came from a culture/conduct issue, not a financial fraud. The old system's alternative data checks (employee reviews, customer complaints, sales culture assessment) would catch early signals.

### 6.5 Derivative Lawsuit Settlement Patterns
From `derivative_lawsuit_patterns.md`:
- **Board conflicts of interest**: $50-60M typical (Tesla/SolarCity: $60M)
- **M&A diligence failures**: $30-140M (Freeport-McMoRan: $138M)
- **Egregious behavior**: $30-240M (Wells Fargo: $240M)
- **Caremark/safety**: $90-175M (McKesson: $175M)
- **Massive fraud**: $200M+ (American Realty: $287M)

**Insight**: The current system tracks derivative suits after filing but doesn't assess which of these 5 risk categories the company falls into BEFORE a suit is filed.

### 6.6 Energy Sector - Event-Driven Litigation ($18M avg settlement)
From `energy_sector_litigation_patterns.md`:
- 60% of energy cases end in defendant victory (better than most sectors)
- Average settlement $18M (below market average)
- 4+ year median time to settlement
- Key triggers: environmental events, regulatory shifts, project setbacks, reserve misstatements, ESG/greenwashing

**Insight**: Energy companies have strong legal defenses (pure omissions not actionable, forward-looking safe harbor, puffery defense). The current system could incorporate industry-specific settlement probability adjustments.

---

## SECTION 7: AI-SPECIFIC LITIGATION PATTERNS (Missing from Current System)

From `ai_technology_litigation_patterns.md`, 7 hazard categories the old system checks that the current system mostly lacks:

### 7.1 AI Washing (BIZ.UNI.ai_claims covers partially)
- Companies marketing traditional software as "AI-powered"
- No actual machine learning in products
- Example: Innodata claimed AI capabilities but used manual human labor

### 7.2 Misleading AI Revenue Claims (MISSING)
- Attributing revenue growth to AI when it's from acquisitions or other sources
- Inflating AI revenue mix to command higher multiples
- Example: Oddity Tech overstated AI role in revenue growth

### 7.3 Concealment of AI Limitations (MISSING)
- Known failure rates not disclosed
- Bias in AI systems not disclosed
- Example: Evolv Technologies concealed weapon detection failure rates

### 7.4 False Third-Party Validation (MISSING)
- Misrepresenting analyst reports
- Fabricating customer endorsements
- Overstating clinical trial results for AI diagnostics

### 7.5 Concealment of AI Costs (MISSING)
- GPU/compute costs growing faster than revenue
- Dependency on single infrastructure provider
- Unsustainable unit economics hidden by non-GAAP adjustments

### 7.6 Failure to Disclose AI Risks (MISSING)
- Regulatory risks specific to AI (EU AI Act, state laws)
- IP risks from training data
- Liability risks from AI-generated outputs

### 7.7 Misleading AI R&D Claims (MISSING)
- Overstating AI research capabilities
- Claiming AI patents that don't exist
- Misrepresenting AI talent/team

**Filing trend**: 7 cases (2023) -> 14 cases (2024) -> 12 cases (first 9 months 2025). This is an accelerating trend.

**Current coverage**: `BIZ.UNI.ai_claims` and `BIZ.UNI.cyber_posture` exist but don't cover the specific fraud pattern taxonomy above.

---

## SECTION 8: GENERAL SECURITIES FRAUD TAXONOMY (Reference Framework)

From `general_securities_fraud_types.md`, the old system has a comprehensive taxonomy of fraud types that serves as a reference framework for what to look for:

### Misstatement Types (8 categories)
1. Guarantees of returns
2. False representations of safety
3. Mischaracterization of assets
4. Exaggeration of performance history
5. Revenue recognition fraud
6. Earnings manipulation
7. Asset valuation fraud
8. Liability concealment

### Omission Types (5 categories)
1. Conflicts of interest
2. Known risks
3. Financial health issues
4. Management issues
5. Operational problems

### Half-Truth Framework
Technically true statements that mislead through omitted context. Supreme Court recognizes these as actionable.

**How this helps**: This taxonomy could be used to classify allegation types in the current system's litigation analysis. Currently, `LIT.SCA.allegations` captures allegations but doesn't categorize them against a standard fraud taxonomy.

---

## SECTION 9: PROCESS/METHODOLOGY INSIGHTS

### 9.1 Verification Standards
The old system enforces:
- **Hard data** (financial, regulatory): 1 authoritative source required
- **Soft signals** (social media, reviews, news): 2+ independent sources required
- **Critical/High findings**: Must verify with primary sources before flagging

The current system has this in CLAUDE.md but it's worth verifying the implementation enforces it.

### 9.2 Stock Decline Attribution (REQUIRED)
The old system makes stock attribution analysis mandatory for any decline >10%:
1. Identify trigger event with specific date
2. Document stock reaction magnitude
3. Compare to peer/sector performance
4. Attribute cause (company-specific vs. sector-wide vs. macro)

The current system has `STOCK.PRICE.attribution` but should verify this is enforced as rigorously.

### 9.3 Industry-Specific Module Priorities
The old system recommends different module emphasis by industry:
- **Life Sciences**: Modules 1, 2, 6 (litigation, financial, alternative data)
- **Technology**: Modules 2, 4, 6 (financial, governance, alternative data)
- **Financial Services**: Modules 1, 2, 4 (litigation, financial, governance)
- **Energy**: Modules 1, 3, 5 (litigation, operations, market dynamics)
- **Retail**: Modules 2, 3, 6 (financial, operations, alternative data)

### 9.4 Color Coding System
The old system uses a 4-color + 1 system:
- GREEN = Pass
- YELLOW = Caution
- RED = Fail
- PURPLE = Unknown / Needs Research

The PURPLE category is particularly important - it prevents false "all clear" signals when data is simply unavailable.

---

## SECTION 10: PRIORITIZED IMPLEMENTATION RECOMMENDATIONS

### Tier 1: Critical Gaps (Should be in Phase 32)
1. **SPAC/De-SPAC detection and analysis** - Entire check category missing
2. **Going concern explicit flag** - Direct bankruptcy/claims predictor
3. **Scientific community monitoring for life sciences** - Earliest fraud predictor (PubPeer, Retraction Watch)
4. **Revenue fraud pattern taxonomy** - #1 fraud type, patterns not named
5. **Derivative suit risk factor assessment** - 5-category pre-filing risk model
6. **AI-specific hazard categories** (7 types) - Fastest-growing litigation area
7. **Altman Z-Score** - Standard distress prediction missing

### Tier 2: Important Gaps (Phase 33 or later)
8. **Industry-specific operating metric suites** - SaaS, Biotech, Retail, FinServ, Energy
9. **Compensation manipulation patterns** - Spring-loading, backdating, pledging
10. **ESG/Greenwashing specific checks** - Growing litigation area
11. **Quick Screen / Auto-Decline layer** - Fast pre-screening before deep analysis
12. **CDS spread / default probability monitoring** - Credit market signals
13. **Share pledging by insiders** - Forced selling risk
14. **Capex/OCF ratio check** - Oracle case showed importance
15. **Off-balance sheet lease commitment analysis** - Oracle $248B example

### Tier 3: Enhancement Gaps (Future phases)
16. **Dark web monitoring** - Pre-breach intelligence
17. **Patent/IP risk assessment** - PTAB, NPE, patent cliff
18. **Litigation funding activity** - Third-party funder involvement
19. **Expert witness engagement** - Early litigation preparation signal
20. **Web traffic/app download monitoring** - SimilarWeb/Sensor Tower integration
21. **Union organizing / NLRB filings** - Labor risk
22. **Unusual accounting firm activity** - Forensic accountant engagement
23. **Congressional inquiry tracking** - Legislative escalation signal

---

## APPENDIX A: Check ID Mapping (Old System -> Current System Coverage)

### Fully Covered by Current System
- Oracle debt levels -> `FIN.DEBT.*`
- Stock decline detection -> `STOCK.PRICE.*`
- Short interest -> `STOCK.SHORT.*`
- Board independence -> `GOV.BOARD.independence`
- CEO/CFO profiles -> `GOV.EXEC.*`
- Insider trading -> `GOV.INSIDER.*`
- SEC enforcement -> `LIT.REG.*`
- Auditor quality -> `FIN.ACCT.*`
- Forensic accounting -> `FIN.FORENSIC.*`
- Earnings quality -> `FIN.PROFIT.earnings`, `FIN.QUALITY.*`
- Customer concentration -> `BIZ.DEPEND.*`
- M&A assessment -> `FWRD.EVENT.ma_closing`, `FWRD.EVENT.synergy`
- Activist investors -> `GOV.ACTIVIST.*`
- NLP/disclosure analysis -> `NLP.*`, `FWRD.DISC.*`
- Forward-looking events -> `FWRD.EVENT.*`

### Partially Covered (Have check but missing depth)
- Revenue recognition patterns -> `FIN.QUALITY.*` (missing specific fraud pattern names)
- Stock attribution -> `STOCK.PRICE.attribution` (missing technical indicators)
- Employee data -> `FWRD.WARN.glassdoor_sentiment` etc. (missing keyword search, surge detection)
- Derivative suits -> `LIT.SCA.derivative` (tracks existence, not risk factors)
- Compensation -> `GOV.PAY.*` (missing manipulation patterns)
- Shareholder rights -> `GOV.RIGHTS.*` (has structure, may need threshold refinement)
- Industry metrics -> `FIN.SECTOR.*` (only energy and retail, no SaaS/biotech/finserv)
- Regulatory databases -> `LIT.REG.*` (backward-looking, not forward-looking monitoring)

### Not Covered at All
- SPAC analysis
- Going concern explicit flag
- Scientific community monitoring (PubPeer, Retraction Watch, KOL sentiment)
- Altman Z-Score
- AGR Score
- Revenue fraud pattern taxonomy
- Derivative suit risk factor assessment (5 categories)
- AI-specific hazard categories (7 types)
- Compensation manipulation patterns (spring-loading, backdating)
- Share pledging
- ESG/Greenwashing specific checks
- Quick Screen / Auto-Decline aggregation
- CDS spread monitoring
- Off-balance sheet lease analysis
- Dark web monitoring
- Patent risk (PTAB, NPE, patent cliff)
- Litigation funding detection
- Expert witness engagement tracking
- Web traffic/app download trends
- Union organizing / NLRB
- Congressional inquiry tracking
- Forensic accounting firm engagement detection
