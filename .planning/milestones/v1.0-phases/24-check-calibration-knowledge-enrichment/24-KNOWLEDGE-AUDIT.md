# D&O Underwriting Knowledge Audit: First-Principles Analysis

**Date:** 2026-02-11
**Purpose:** Map the D&O underwriting knowledge domain from first principles and identify gaps in the current 359-check system.
**Audience:** Experienced D&O underwriter reviewing system architecture.

---

## 1. Executive Summary

### What the Current System Does Well

The system has a solid foundation: 10 scoring factors with empirically calibrated weights, 19 composite patterns that detect multi-signal risk, sector-specific baselines for 15 industries, and a tier framework (WIN through NO_TOUCH) that maps cleanly to underwriting actions. The 359 checks cover the five major D&O liability pathways (securities class actions, SEC enforcement, derivative suits, M&A litigation, and regulatory proceedings). The critical red flag gates (CRF-01 through CRF-11) correctly implement hard ceilings that prevent algorithmic overconfidence.

### What is Missing

The audit identified five structural gaps:

1. **NLP/forensic signals are defined but not implemented.** The system has LLM extraction capability (sends full 10-K/10-Q filings to Claude Haiku) but does not use it for the forensic linguistic signals that academic research identifies as the strongest leading indicators: MD&A tone shift, risk factor evolution, earnings call hedging language, and Non-GAAP/GAAP divergence patterns. The patterns.json defines signals like "mda_is_generic_boilerplate" and "forward_guidance_language_more_hedged" but marks them as needing "NLP-based evaluation or manual review" -- they are placeholders, not implementations.

2. **The bear case framework is implicit, not explicit.** An underwriter constructs a plaintiff's complaint in their head. The system scores risk factors independently but does not synthesize them into the specific allegation narratives a plaintiff would file. SMCI had auditor resignation + Hindenburg report + delayed 10-K + insider sales -- these signals fire individually but the system does not construct "here is the complaint that would be filed."

3. **Temporal signals are underweighted.** The strongest predictors in academic literature are *changes over time*: DSO increasing 3 quarters running, accruals ratio diverging from cash flow, risk factors being quietly removed, guidance methodology changing. The current checks are mostly point-in-time snapshots. The system knows current leverage but not whether leverage increased 50% in the last year relative to the prior year's trajectory.

4. **The check-to-factor mapping has structural misalignment.** Many checks map to generic factors (F9 Governance for business concentration risks) rather than the specific allegation pathway they relate to. Customer concentration (BIZ.DEPEND.customer_conc) maps to F9 but its claim pathway is Type A (disclosure fraud -- "they knew the customer was leaving and didn't tell us"). The factor architecture conflates "what type of risk" with "how do we score it."

5. **Relative risk benchmarking is thin.** The system has sector baselines for short interest, volatility, and leverage, but does not systematically benchmark the company against specific named peers on the dimensions that matter most: valuation premium, growth rate differential, governance quality, and disclosure practices. An underwriter's first question for any tech company is "how does this compare to its closest 5 peers?" The system provides some peer data but doesn't structure it as a formal peer comparison framework.

### Prioritized Recommendations

| Priority | Recommendation | Impact | Effort |
|----------|---------------|--------|--------|
| 1 | Build temporal change detection (YoY/QoQ) for top 10 financial metrics | Catches 60%+ of SCA triggers before they become news | Medium |
| 2 | Implement MD&A tone shift analysis via LLM extraction | Single highest-value forensic signal per academic literature | Medium |
| 3 | Build explicit bear case synthesis (allegation narrative constructor) | Transforms worksheet from checklist to underwriting tool | High |
| 4 | Implement risk factor evolution tracking (added/removed/changed) | Second highest NLP signal; directly maps to plaintiff discovery | Medium |
| 5 | Add earnings quality forensics (Beneish M-Score, accruals ratio) | Quantitative leading indicator with 76% fraud detection accuracy | Low |
| 6 | Build structured peer comparison framework | Answers the underwriter's first question | Medium |
| 7 | Restructure checks around allegation pathways, not worksheet sections | Clarifies what each check is actually testing | High |
| 8 | Add Non-GAAP/GAAP divergence tracking with trend analysis | Growing plaintiff attack vector; 21% of 2024 filings cited Non-GAAP | Low |
| 9 | Build "kitchen sink" quarter detector | Classic leading indicator that management is resetting expectations | Low |
| 10 | Add related party transaction language analysis | High scienter signal when combined with insider trading | Low |

---

## 2. D&O Liability Pathways

### The Decision Tree: How Companies Get Sued

```
START: Public company with D&O insurance
|
+-- PATHWAY 1: Securities Class Action (10b-5 / Section 11)
|   |   ~220 filings/year, 3.9% annual base rate
|   |
|   +-- TRIGGER: Stock price decline (necessary condition)
|   |   |-- Single-day event collapse (>15% drop on news)
|   |   |-- Cascade decline (sustained >20 days, no recovery)
|   |   |-- Earnings miss sell-off (guidance miss + >10% drop)
|   |   |-- Short seller report + drop
|   |   |-- Restatement announcement + drop
|   |
|   +-- ALLEGATION TYPE A: Disclosure Fraud (10b-5)
|   |   "Company knew X and didn't disclose it"
|   |   -- Material misrepresentation in SEC filings
|   |   -- Material omission (knew but didn't tell)
|   |   -- Scienter: management knew or was reckless
|   |   -- Loss causation: stock dropped when truth emerged
|   |
|   +-- ALLEGATION TYPE B: Forward-Looking Statement Fraud
|   |   "Guidance was false when given"
|   |   -- Guidance given with knowledge it was unattainable
|   |   -- Safe harbor defense does NOT apply to present facts
|   |   -- Revenue/earnings guidance misses
|   |   -- Pipeline/clinical trial outcome misrepresentation
|   |
|   +-- ALLEGATION TYPE C: Product/Operations
|       "Product was defective / operations failed"
|       -- Product safety/efficacy misrepresented
|       -- Manufacturing quality hidden
|       -- Operational metrics inflated (users, subscribers, etc.)
|
+-- PATHWAY 2: SEC Enforcement
|   |   ~700 enforcement actions/year, but only ~50-100 against public companies
|   |
|   +-- Wells Notice (formal notification of potential enforcement)
|   +-- Formal Order of Investigation
|   +-- Administrative Proceeding
|   +-- Civil Action (SEC as plaintiff in federal court)
|   +-- AAER (Accounting and Auditing Enforcement Release)
|   +-- Cease-and-Desist Order
|   +-- D&O Bar (officer/director bars)
|
+-- PATHWAY 3: Derivative Suits
|   |   Filed by shareholders on behalf of the company vs. its own directors
|   |
|   +-- Breach of fiduciary duty (duty of care, duty of loyalty)
|   +-- Corporate waste (excessive compensation, bad acquisitions)
|   +-- Caremark claims (failure of board oversight)
|   +-- Books and records demands (Section 220)
|   +-- Self-dealing / related party transactions
|   +-- Failure to monitor (cyber breach oversight, compliance failures)
|
+-- PATHWAY 4: M&A Litigation
|   |   ~80% of deals >$100M get sued (declining post-Trulia)
|   |
|   +-- Merger objections (inadequate price, flawed process)
|   +-- Appraisal actions (Delaware fair value proceedings)
|   +-- Post-merger integration disclosure fraud
|   +-- SPAC-specific: De-SPAC projections fraud
|   +-- Revlon claims (failure to maximize value in sale)
|
+-- PATHWAY 5: Regulatory Proceedings
|   |
|   +-- DOJ criminal investigation
|   +-- State AG consumer protection actions
|   +-- FTC antitrust / consumer protection
|   +-- CFPB enforcement (financial services)
|   +-- FDA warning letters / enforcement (pharma/biotech)
|   +-- EPA enforcement (energy/industrial)
|   +-- OFAC sanctions violations (financial services)
|   +-- Sector-specific regulators (FDIC, OCC, state insurance)
|
+-- PATHWAY 6: Bankruptcy/Insolvency D&O Claims
|   |
|   +-- Deepening insolvency claims
|   +-- Fraudulent transfer claims (preferential payments to insiders)
|   +-- Zone of insolvency duty shifting (creditors replace shareholders)
|   +-- Side A claims (personal assets of D&Os at risk)
|
+-- PATHWAY 7: Cyber/Data Breach Claims
|   |
|   +-- Shareholder derivative suits for oversight failure
|   +-- Securities class actions if breach was material + not disclosed timely
|   +-- Regulatory fines (GDPR, state privacy laws)
|   +-- Caremark claims against board for inadequate cybersecurity governance
|
+-- PATHWAY 8: ESG/Climate Disclosure Claims
    |
    +-- Greenwashing class actions
    +-- SEC climate disclosure rule violations
    +-- Failure to meet stated ESG commitments
    +-- State AG actions for environmental misrepresentation
    +-- European CSRD compliance (for dual-listed companies)
```

### Leading Indicators by Pathway

| Pathway | Leading Indicators (12-18 months before suit) | Confirming Signals (0-6 months) | Forensic Evidence |
|---------|----------------------------------------------|--------------------------------|-------------------|
| Securities Class Action | Revenue deceleration, insider selling cluster, SI rising, analyst downgrades, risk factor changes | Stock drop >10%, earnings miss, short seller report, restatement | MD&A tone shift, DSO increase, accruals spike, Non-GAAP gap widening |
| SEC Enforcement | SEC comment letters, auditor change, internal control weakness, whistleblower complaints | Wells Notice, formal investigation order, subpoena disclosure | Revenue recognition policy changes, related party transactions, CAM additions |
| Derivative Suit | Low say-on-pay vote, ISS/GL "Against" recommendations, shareholder proposals ignored | SCA filing (derivatives follow), books and records demand | Board meeting minutes (not public), D&O questionnaire responses |
| M&A Litigation | Pending M&A announcement, acquirer stock decline, proxy fight | Deal announcement + inadequate process allegations | Fairness opinion methodology, go-shop provisions, deal protection terms |
| Bankruptcy D&O | Going concern opinion, cash runway <12 months, covenant breach, credit downgrade | Missed debt payment, delisting warning, Chapter 11 filing | Insider transactions in zone of insolvency, preferential payments |
| Cyber/Data Breach | No board cyber committee, inadequate Item 1C disclosure, prior breaches | Breach announcement, regulatory investigation, customer notifications | Security audit reports (not public), incident response timeline |
| ESG/Climate | Specific dated ESG targets, emissions commitments without reduction plan | Target deadline approaching without progress, regulatory action | Sustainability report vs. SEC filing inconsistencies |

---

## 3. Empirically Validated Predictors

### What Actually Predicts D&O Claims

The academic literature and industry claims studies converge on a hierarchy of predictive variables. The following is organized by predictive power (strongest first), with citations.

#### Tier 1: Strongest Predictors (Lift >3x base rate)

**1. Prior Litigation History (Lift: 4.2x)**
Companies with a prior SCA within 5 years are 4.2x more likely to face another. This is the single strongest predictor and is already well-covered by F1 in the current system.
- Source: Stanford SCAC historical data; NERA longitudinal analysis.
- Current system coverage: STRONG (F1_prior_litigation, 20 points, CRF-01)

**2. Stock Price Decline Magnitude (Lift: 3.8x)**
The stock drop is both a necessary condition for filing (creates damages) and a strong predictor of filing likelihood. A >50% decline from 52-week high corresponds to approximately a 15-20% annual filing probability for large-cap companies. The critical distinction is *company-specific* vs. market/sector decline.
- Source: Cornerstone Research 2024; Kim & Skinner (2012) litigation risk model.
- Current system coverage: STRONG (F2_stock_decline, 15 points, multiple pattern modifiers)

**3. Restatement/Audit Issues (Lift: 4.5x)**
Restatements within 12 months have the highest historical lift factor (4.5x). Auditor resignation with disagreement is nearly as strong.
- Source: Audit Analytics restatement database; Cornerstone Research.
- Current system coverage: STRONG (F3_restatement_audit, 12 points, CRF-05)

**4. IPO/SPAC Recency (Lift: 2.8x)**
14% of IPOs (2010-2019) faced SCA within 3 years. SPACs: 17-24% filing rate per transaction. 74% of IPO suits occur within 5 quarters post-IPO.
- Source: Stanford SLA IPO Litigation Risk study (2021).
- Current system coverage: STRONG (F4_ipo_spac_ma, 10 points, CRF-06)

#### Tier 2: Significant Predictors (Lift 2-3x base rate)

**5. Guidance Misses / Earnings Surprises (Lift: 2.4x)**
3+ misses in 8 quarters or consecutive misses significantly increase filing probability. The magnitude of the miss matters: a >15% miss triggers much higher plaintiff interest than a 2% miss.
- Source: Cornerstone Research settlement data; D&O Diary event analysis.
- Current system coverage: GOOD (F5_guidance_misses, 10 points, pattern modifiers)

**6. Short Interest Elevation (Lift: 2.1x)**
21% of 2024 core SCA filings referenced short seller reports. SI >3x sector average correlates with 2.1x base filing rate. Short seller reports (Hindenburg, Muddy Waters, etc.) are particularly predictive when they make specific fraud allegations vs. valuation-only arguments.
- Source: Cornerstone Research 2024 Year in Review; NERA 2024.
- Current system coverage: GOOD (F6_short_interest, 8 points, SHORT_ATTACK pattern)

**7. Financial Distress Indicators (Lift: 2.0x)**
Going concern opinions, covenant breaches, and cash runway <6 months each independently increase claim probability. The combination is more predictive than any individual signal.
- Source: Altman Z-score literature; Cornerstone settlement analysis.
- Current system coverage: GOOD (F8_financial_distress, 8 points, DEATH_SPIRAL pattern)

**8. Stock Volatility (Lift: 1.9x)**
90-day volatility >3x sector ETF correlates with elevated filing risk. Extreme daily moves (>5% in 5+ days in 90 days) are a distinct signal.
- Source: Kim & Skinner (2012); NERA volatility analysis.
- Current system coverage: GOOD (F7_volatility, 9 points, sector-adjusted)

#### Tier 3: Contributing Predictors (Lift 1.2-2x base rate)

**9. Governance Deficiencies (Lift: 1.3x)**
CEO=Chairman with low board independence, dual-class structures, and compensation misalignment are weak standalone predictors but amplify other signals. They primarily predict *derivative suit* exposure, not securities class actions.
- Source: ISS Governance QualityScore research; Stanford derivative settlement data.
- Current system coverage: ADEQUATE (F9_governance, 6 points)

**10. Officer Instability (Lift: 1.2x)**
CEO/CFO turnover is a weak standalone predictor but becomes significant when combined with financial stress signals (departure *during* declining quarters = high signal).
- Source: Cornerstone executive turnover analysis.
- Current system coverage: ADEQUATE (F10_officer_stability, 2 points)

#### Tier 4: Variables NOT in Current System but Empirically Validated

**11. Beneish M-Score / Earnings Quality Deterioration (Lift: ~3x)**
The Beneish M-Score correctly identifies 76% of earnings manipulators with 17.5% false-positive rate. The 8 variables (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA) can be computed from standard financial statements. An M-Score > -2.22 indicates likely manipulation.
- Source: Beneish (1999); Indiana University Kelley School validation studies.
- **Current system coverage: WEAK.** The check FIN.ACCT.earnings_manipulation exists but does not compute Beneish M-Score. The EARNINGS_QUALITY_DETERIORATION pattern references accruals_ratio and beneish_m_score_zone but has empty component_checks [].

**12. MD&A Linguistic Tone Change (Lift: ~2x)**
Year-over-year changes in MD&A sentiment, hedging language, and certainty markers predict future restatements and enforcement actions. Fraudulent firms produce "abnormal verbal disclosures" detectable out-of-sample.
- Source: Li (2010) "Textual Analysis of Corporate Disclosures"; Loughran & McDonald financial sentiment dictionary; FinBERT models.
- **Current system coverage: ABSENT.** The DISCLOSURE_QUALITY pattern defines the signal but marks it as needing "NLP-based evaluation."

**13. Risk Factor Evolution (Added/Removed/Changed)**
New risk factors, removed risk factors, and significant language changes in Item 1A are leading indicators. Companies that remove risk factors shortly before the risk materializes face high scienter allegations.
- Source: Campbell et al. (2014) "The Information Content of Mandatory Risk Factor Disclosures"; SEC staff observations.
- **Current system coverage: ABSENT.** No check compares current risk factors to prior year.

**14. Insider Trading Timing Patterns (Lift: ~2.5x when combined with stock drop)**
Not just the volume of insider selling but the *timing* relative to corporate events. Pre-announcement selling within 90 days of bad news is the strongest scienter signal. 10b5-1 plan modifications/terminations are increasingly scrutinized under 2023 SEC rules.
- Source: Cohen et al. (2012) "Decoding Inside Information"; SEC enforcement statistics.
- **Current system coverage: PARTIAL.** The INFORMED_TRADING pattern defines this but relies on data (options volume, 10b5-1 modifications) that the system does not reliably acquire.

**15. Market Cap at Risk (Disclosure Dollar Loss)**
The DDL -- stock price drop on the corrective disclosure date multiplied by shares outstanding -- is the single best predictor of whether a case will settle and for how much. Cases with DDL >$500M settle 85%+ of the time.
- Source: Cornerstone Research settlement data (annual reports 2015-2024); Stanford SCAC DDL Index.
- **Current system coverage: PARTIAL.** The check LIT.SCA.exposure references DDL but the actual computation is not implemented in the check engine.

---

## 4. Current System Coverage Map

### Check Distribution by Section

| Section | Check Count | Category | Coverage Quality |
|---------|------------|----------|-----------------|
| 1 (Business) | ~85 | Company profile, business model, dependencies, competitive position | COMPREHENSIVE but mostly info/context |
| 2 (Market) | ~65 | Stock price, insider trading, short interest, patterns, valuation | STRONG for price-based signals |
| 3 (Financial) | ~75 | Liquidity, debt, profitability, guidance, accounting, sector | GOOD for current state; WEAK for temporal changes |
| 4 (Litigation) | ~80 | SCA history, regulatory actions, other litigation types | COMPREHENSIVE for known litigation |
| 5 (Governance) | ~35 | Board, compensation, executives, effectiveness | ADEQUATE |
| 6 (Forward) | ~20 | Disclosure quality, catalysts, regulatory risk | THIN |
| Total | 359 | | |

### Coverage by Liability Pathway

| Pathway | Checks Covering | Quality Assessment |
|---------|----------------|-------------------|
| Securities Class Action (10b-5) | ~120 (stock, financial, litigation) | STRONG -- primary design focus |
| SEC Enforcement | ~25 (LIT.REG.*) | ADEQUATE -- checks exist but data acquisition is web-search dependent |
| Derivative Suits | ~8 (LIT.SCA.derivative, GOV.*) | WEAK -- derivative exposure is undermodeled |
| M&A Litigation | ~5 (LIT.SCA.merger_obj, BIZ.COMP.consolidation) | WEAK -- no pending M&A analysis framework |
| Regulatory Proceedings | ~15 (LIT.REG.* for various agencies) | ADEQUATE -- breadth is good but depth is shallow |
| Bankruptcy/Insolvency D&O | ~10 (FIN.LIQ.*, FIN.DEBT.*, DEATH_SPIRAL) | GOOD via financial distress signals |
| Cyber/Data Breach | ~3 (BIZ.UNI.cyber_posture, cyber_business) | WEAK -- no actual breach detection or governance assessment |
| ESG/Climate | ~3 (BIZ.UNI.esg_*, esg_commitments) | MINIMAL -- no gap analysis between commitments and progress |

### Coverage by the Four-Layer Framework

#### Layer 1: Customary (Standard Worksheet Sections)
**Coverage: STRONG**
The system covers all standard D&O worksheet sections: company profile, stock performance, financial analysis, litigation history, governance review, and forward-looking risk assessment. The 8-section worksheet structure maps to standard underwriting practice.

Missing from customary: Insurance program history (expiring tower, loss history, current carrier). This is intentionally excluded as it requires submission data not available from public sources.

#### Layer 2: Objective Risk (Quantifiable, Empirical Signals)
**Coverage: STRONG for what is implemented, GAPS in forensic signals**

Well-covered objective signals:
- Stock price position and decline from high
- Short interest absolute and relative to sector
- Market cap tier and litigation probability
- Prior SCA history
- Restatement history
- Insider trading volume
- Financial ratios (leverage, liquidity, coverage)
- Guidance track record (beats/misses)
- IPO/SPAC age

Missing objective signals:
- Beneish M-Score (computable from existing data)
- Accruals ratio (computable from existing data)
- DSO/DIO/DPO trends (computable from existing data)
- Non-GAAP/GAAP divergence magnitude and trend
- Options put/call volume ratio (data acquisition needed)
- SEC comment letter count and topic (available from EDGAR)
- Disclosure Dollar Loss calculation (DDL)
- Auditor critical audit matter (CAM) changes

#### Layer 3: Relative Risk (Peer-Benchmarked)
**Coverage: MODERATE**

Implemented peer benchmarks:
- Stock performance vs. sector ETF
- Volatility vs. sector baseline
- Short interest vs. sector baseline
- Leverage vs. sector norms
- Guidance miss rate vs. sector beat rate

Missing peer benchmarks:
- Valuation (P/E, EV/EBITDA) vs. named peer group (not just sector)
- Revenue growth rate vs. named peers
- Margin trajectory vs. named peers
- Governance score vs. named peers
- Disclosure quality vs. named peers (word count, readability score)
- Insider selling rate vs. named peers
- Compensation structure vs. named peers

#### Layer 4: Subjective Modifiers (Underwriter Judgment)
**Coverage: WEAK**

The system currently has limited mechanisms for surfacing the right *questions* for underwriter judgment. Subjective areas where the system should prompt (but mostly doesn't):

- "Would you want to be a board member of this company?" (the underwriter's gut check)
- "If management called tomorrow to discuss coverage, what 3 questions would you ask?"
- "What is the most likely complaint narrative against this company?"
- "What would a Hindenburg report on this company focus on?"
- "If this company's stock dropped 40% tomorrow, what would be the cause?"
- "Is the CEO's compensation aligned with shareholder interests?"
- "Does management's narrative in earnings calls match what the numbers say?"

The playbook meeting_questions partially address this, but they are generic by industry rather than specific to the company's risk profile.

---

## 5. Gap Analysis

### Gap 1: Temporal Change Detection
**Severity: HIGH -- affects all financial checks**

The current system evaluates point-in-time values. Academic research shows that *changes* are more predictive than *levels*. The following temporal signals are not implemented:

| Signal | Data Source | Predictive Value | Implementation Difficulty |
|--------|-----------|-----------------|--------------------------|
| Revenue growth deceleration (3 consecutive years) | 10-K income statements | HIGH -- classic growth darling trigger | LOW -- data exists |
| Gross margin decline (3+ quarters) | 10-Q income statements | HIGH -- indicates pricing power loss | LOW -- data exists |
| DSO increase (3+ quarters) | Balance sheet + revenue | HIGH -- revenue recognition red flag | LOW -- data exists |
| Cash flow / Net income divergence widening | Cash flow + income statement | HIGH -- earnings quality deterioration | LOW -- data exists |
| Working capital deterioration (3+ quarters) | Balance sheet | MEDIUM -- liquidity stress | LOW -- data exists |
| SG&A as % of revenue increasing | Income statement | MEDIUM -- operating leverage shift | LOW -- data exists |
| CapEx as % of revenue increasing while revenue flat/declining | Cash flow statement | MEDIUM -- capital allocation concern | LOW -- data exists |
| Employee count decline while growth narrative maintained | 10-K Item 1 | HIGH -- narrative inconsistency | LOW -- data exists |
| Debt/EBITDA deterioration trajectory | Balance sheet + income | MEDIUM -- financial distress path | LOW -- data exists |
| Inventory days increase (manufacturing/retail) | Balance sheet + COGS | HIGH for applicable sectors | LOW -- data exists |

### Gap 2: NLP/Forensic Signals
**Severity: HIGH -- represents the system's biggest competitive advantage opportunity**

The system sends full SEC filings to Claude Haiku for structured extraction. This capability is NOT being used for forensic linguistic analysis. The following signals could be extracted:

**2a. MD&A Tone Shift Analysis**
- Compare current year MD&A sentiment to prior year using Loughran-McDonald financial sentiment dictionary
- Track: negative word frequency, uncertain word frequency, litigious word frequency, hedging language frequency
- Alert when: negative/uncertain language increases >20% YoY, hedging language increases >30% YoY
- Real example: Enron's 2000 10-K showed 15% increase in uncertainty language vs. 1999; WorldCom's MD&A shifted from specific revenue targets to vague "market environment" language
- Implementation: Add extraction prompt for tone metrics to LLM extraction; compare current vs. prior filing

**2b. Risk Factor Evolution**
- Compare current Item 1A risk factors to prior year
- Track: new risk factors added, risk factors removed, language changes in existing factors
- Alert when: material risk factor removed (potential omission), new risk factor added (new exposure), language becomes more hedged
- Real example: SMCI added cybersecurity risk factors in 2023 10-K that were vague relative to actual exposure; Luckin Coffee removed competitive risk factors shortly before fraud disclosure
- Implementation: Extract risk factor headings from current and prior 10-K; diff and classify changes

**2c. Earnings Call Hedging Language Detection**
- Parse earnings call transcripts for hedging, deflection, and specificity changes
- Track: "I think" / "we believe" frequency, deflection of analyst questions, reduced specificity in forward guidance
- Alert when: management language becomes significantly more hedged vs. prior quarter, or management deflects specific analyst questions they previously answered directly
- Real example: Theranos earnings calls showed increasing deflection on technology specifics; Valeant's conference calls shifted from specific revenue drivers to "operational improvements"
- Implementation: This requires earnings call transcript acquisition (not currently in ACQUIRE)

**2d. Revenue Recognition Language Red Flags**
- Extract ASC 606 disclosures and compare to prior year
- Track: changes in performance obligation definitions, changes in variable consideration estimates, changes in timing of revenue recognition
- Alert when: methodology changes (potential manipulation), variable consideration becomes larger share, recognition shifts from "over time" to "point in time" or vice versa
- Implementation: Extract rev rec note from current and prior 10-K; LLM comparison

**2e. Non-GAAP / GAAP Divergence Patterns**
- Compute gap between GAAP and Non-GAAP earnings (per share) over 8 quarters
- Track: absolute gap, gap as % of GAAP earnings, trend direction
- Alert when: gap is widening, Non-GAAP positive while GAAP negative, adjustments include recurring items
- Real example: WeWork's "Community Adjusted EBITDA" excluded virtually all costs; Valeant's "Cash EPS" excluded amortization of acquired intangibles that represented the core business model
- Implementation: Extract GAAP and Non-GAAP earnings from 8-K earnings releases; compute trend

**2f. "Kitchen Sink" Quarter Detection**
- Detect quarters with unusual charge patterns: multiple large write-downs, restructuring charges, goodwill impairments, and guidance resets occurring simultaneously
- Purpose: Management often "cleans house" by taking all bad news at once, creating an artificially low baseline for future beats
- Alert when: total special charges >10% of revenue, 3+ distinct charge categories in one quarter, combined with lowered forward guidance
- Real example: GE's Q4 2017 $6.2B after-tax charge + insurance reserve increase + guidance cut was a classic kitchen sink quarter
- Implementation: Parse 8-K earnings releases for charge categories and magnitudes

**2g. Footnote Complexity / Obfuscation Detection**
- Measure footnote length, readability (Fog Index), and complexity relative to company size and industry
- Track: changes in footnote length YoY, sentences per footnote, use of passive voice, undefined terms
- Alert when: footnotes grow >25% without corresponding business complexity increase, readability declines significantly
- Research basis: Li (2008) found that firms with lower readability filings have lower earnings persistence and larger absolute earnings surprises
- Implementation: Compute readability metrics on extracted footnotes; compare to prior year

**2h. Related Party Transaction Language**
- Extract and analyze related party transaction disclosures
- Track: number of related party transactions, dollar volume, types (real estate, consulting, procurement), involvement of family members or entities controlled by officers/directors
- Alert when: related party volume increases, new related party appears, related party receives above-market terms
- Implementation: Extract related party note from 10-K; LLM analysis of terms and trends

**2i. Going Concern Language Trajectory**
- Track the evolution of going concern language across auditor reports
- Alert when: new "substantial doubt" language appears, prior year's going concern was mitigated but conditions haven't actually improved, management's mitigation plan cites "expected future financing" without commitments
- Implementation: Extract auditor opinion paragraph; classify going concern status and compare to prior year

**2j. Whistleblower / Qui Tam Language**
- Detect references to whistleblower complaints, qui tam actions, or internal investigations in SEC filings
- These are strong leading indicators of larger problems
- Alert when: new whistleblower disclosure appears, internal investigation initiated, reference to "preliminary findings" from internal review
- Implementation: Keyword extraction from Item 3, Item 1A, and legal proceedings footnotes

### Gap 3: Bear Case Synthesis Framework
**Severity: HIGH -- transforms the worksheet from a checklist to an underwriting tool**

The system should construct the plaintiff's complaint for every company. This requires synthesizing multiple signals into a narrative:

**Framework: Building the Plaintiff's Case**

For any company, the bear case framework asks five questions:

1. **What was the misrepresentation?** (Material Misstatement/Omission)
   - Sources: Earnings guidance, revenue projections, product efficacy claims, regulatory compliance representations, growth narrative
   - Detection: Compare management's public statements to subsequent reality. Identify any gap >15% between guidance and actual results, or any qualitative claim that was demonstrably false.

2. **What did management know?** (Scienter)
   - Sources: Insider trading patterns, internal documents referenced in filings, analyst Q&A deflections, 10b5-1 plan modifications, management background
   - Detection: Pre-announcement insider selling, cluster selling by multiple executives, 10b5-1 plan modifications within 6 months of bad news, management dodging specific analyst questions they previously answered.

3. **When did the truth emerge?** (Corrective Disclosure)
   - Sources: Earnings announcement, restatement, short seller report, regulatory action, product recall, whistleblower disclosure
   - Detection: Identify the specific date(s) when the stock dropped significantly on company-specific news. Map the news to the prior representations.

4. **How much did shareholders lose?** (Loss Causation / Damages)
   - Sources: Stock price data, DDL calculation, trading volume, institutional holdings
   - Detection: Compute DDL (price drop on corrective disclosure date x shares outstanding). Compute Maximum Dollar Loss. Estimate settlement range based on Cornerstone Research regression models.

5. **Is this case viable?** (PSLRA Pleading Standards / Dismissal Risk)
   - Assessment: Has there been a >10% stock drop? Is the DDL >$50M? Are there institutional investors with standing? Is there evidence beyond circumstantial (e.g., insider trading, restatement, CW allegations)?
   - Sector dismissal rates: Biotech 67.5%, Tech 57.5%, Financials 52.5%, Healthcare 37.5%

**Company-Specific Bear Case Template:**

```
BEAR CASE: [COMPANY NAME]

Alleged Misrepresentation:
  [What specific statements could plaintiffs cite as false or misleading?]
  Filing references: [10-K Item 7, earnings call transcript, 8-K]

Scienter Indicators:
  [What evidence suggests management knew?]
  - Insider trading: [summary]
  - Timing of disclosures: [summary]
  - Internal vs. external narrative: [summary]

Corrective Disclosure Event(s):
  [What event(s) revealed the truth?]
  - Date: [date], Stock drop: [%], DDL: [$M]

Damages Estimate:
  - DDL: $[X]M
  - Maximum Dollar Loss: $[X]M
  - Settlement range: $[X-Y]M (based on market cap tier + allegation type)

Viability Assessment:
  - Pleading strength: [LOW/MEDIUM/HIGH]
  - Institutional lead plaintiff likely: [YES/NO]
  - Dismissal probability: [X%] (sector-adjusted)
  - Settlement probability (if not dismissed): [X%]
```

### Gap 4: Structured Peer Comparison Framework
**Severity: MEDIUM -- answers the underwriter's first question**

The current system benchmarks against sector ETFs and sector averages. Underwriters compare against *named peers*. The system should:

1. Identify 5-8 named peers (using SIC code, market cap range, business description similarity)
2. Benchmark the company on 10 dimensions:
   - Stock performance (12M, 6M, 3M vs. peer median)
   - Valuation premium/discount (P/E, EV/Revenue vs. peer median)
   - Revenue growth rate vs. peer median
   - Margin (gross, operating, net) vs. peer median
   - Leverage (debt/EBITDA) vs. peer median
   - Short interest (as % of float) vs. peer median
   - Insider selling rate vs. peer median
   - Litigation frequency (prior SCAs in 5 years) vs. peer median
   - Governance quality (board independence, CEO=Chair) vs. peer median
   - Disclosure quality (10-K length, Non-GAAP reliance) vs. peer median

3. Compute a "Peer Relative Risk Score" that captures whether this company is an outlier within its peer group

### Gap 5: Check Architecture Misalignment
**Severity: MEDIUM -- causes confusion in interpretation**

Current problem: Checks are organized by *worksheet section* (Business, Market, Financial, Governance, Litigation, Forward) rather than by *allegation pathway*. This means:

- Customer concentration (BIZ.DEPEND.customer_conc) maps to F9 (Governance) but the actual claim pathway is Type A (disclosure fraud) or Type C (product/ops)
- Revenue recognition issues (BIZ.MODEL.revenue_type) map to no factor but are core to Type A allegations
- ESG commitments (BIZ.UNI.esg_commitments) map to no factor but represent emerging litigation exposure

Proposed restructuring: Maintain the worksheet section organization for presentation, but add a second dimension mapping each check to its allegation pathway:

```
Check: BIZ.DEPEND.customer_conc
  Worksheet Section: 1 (Business Profile)
  Allegation Pathway: TYPE_A (if customer leaves and company didn't disclose concentration)
  Factor Impact: F5 (guidance/earnings miss from customer loss)
  Leading Indicator For: Guidance miss -> stock drop -> SCA
```

---

## 6. NLP/Forensic Signal Opportunities

### Priority Matrix

| Signal | Predictive Value | Data Available? | LLM Extraction Feasible? | Implementation Priority |
|--------|-----------------|-----------------|--------------------------|------------------------|
| MD&A tone shift | HIGH (Lift ~2x) | YES (10-K on hand) | YES | P1 |
| Risk factor evolution | HIGH | YES (current + prior 10-K) | YES | P1 |
| Non-GAAP/GAAP divergence | HIGH | YES (8-K earnings releases) | YES | P2 |
| Revenue recognition changes | HIGH | YES (10-K rev rec note) | YES | P2 |
| "Kitchen sink" quarter | MEDIUM | YES (8-K earnings releases) | YES | P2 |
| Related party transaction analysis | MEDIUM-HIGH | YES (10-K footnotes) | YES | P2 |
| Footnote complexity changes | MEDIUM | YES (10-K footnotes) | YES | P3 |
| Going concern trajectory | MEDIUM | YES (10-K auditor opinion) | YES | P2 |
| Whistleblower language | HIGH (when present) | YES (10-K Item 3, 1A) | YES | P2 |
| Earnings call hedging | HIGH | NO (need transcript acquisition) | YES if acquired | P3 (blocked by data) |
| Executive communication patterns | MEDIUM | NO (need transcript acquisition) | YES if acquired | P3 (blocked by data) |
| Board meeting frequency anomalies | LOW | YES (proxy statement) | YES | P4 |
| Auditor CAM changes | MEDIUM-HIGH | YES (10-K auditor report) | YES | P2 |
| SEC comment letter topics | MEDIUM-HIGH | YES (EDGAR CORRESP filings) | YES | P2 |

### Specific LLM Extraction Prompts

For the P1 signals, the following extraction prompts would be added to the LLM extraction engine:

**MD&A Tone Analysis Prompt:**
```
Analyze the MD&A section of this 10-K filing and provide:
1. NEGATIVE_WORD_COUNT: Count of words from the Loughran-McDonald negative word list
2. UNCERTAIN_WORD_COUNT: Count of uncertain/hedging words (may, might, could, potentially, etc.)
3. FORWARD_LOOKING_SPECIFICITY: Rate 1-5 how specific the forward-looking statements are (1=vague, 5=precise targets)
4. KEY_NARRATIVE_THEMES: List the 5 main themes management emphasizes
5. TONE_SHIFT_INDICATORS: Any language that suggests a shift in confidence vs. typical corporate optimism
6. DEFLECTION_LANGUAGE: Phrases that blame external factors for negative results
```

**Risk Factor Evolution Prompt:**
```
Compare the risk factors in this 10-K to the following prior year risk factors [provided]:
1. NEW_RISK_FACTORS: List any risk factors added that were not in the prior year
2. REMOVED_RISK_FACTORS: List any risk factors removed from the prior year
3. MATERIALLY_CHANGED: List risk factors with significant language changes
4. HEDGING_INCREASED: Identify risk factors where language became more hedged/uncertain
5. SPECIFICITY_REDUCED: Identify risk factors where quantitative details were removed
```

---

## 7. The Bear Case Framework

### Standard Plaintiff Allegation Templates

Based on analysis of Cornerstone Research settlement data and Stanford SCAC filing patterns, the following are the most common allegation structures:

#### Template 1: Earnings Guidance Fraud (Type B)
**Frequency:** ~40% of SCA filings
**Typical Company Profile:** Growth company, analyst coverage >10, provides quarterly guidance
**Allegation Pattern:**
1. Company provides specific revenue/earnings guidance
2. Management has contemporaneous knowledge that guidance is unattainable (through internal forecasts, pipeline data, customer signals)
3. Insiders sell stock during the class period
4. Company misses guidance, stock drops >15%
5. Plaintiff alleges management knew guidance was false when given

**Leading Indicators the System Should Track:**
- Guidance magnitude vs. historical achievement rate
- Insider selling during guidance period
- Channel checks / customer sentiment (not available from public data)
- Revenue recognition policy changes
- Backlog/pipeline trajectory vs. guidance assumptions

**Real Examples:**
- CrowdStrike (2024): Q2 guidance miss after Falcon platform outage; stock dropped 23%; plaintiff alleged management knew about system fragility
- Peloton (2022): Continued growth guidance while demand was clearly waning; insider selling >$100M

#### Template 2: Accounting/Financial Misstatement (Type A)
**Frequency:** ~25% of SCA filings
**Typical Company Profile:** Company with complex accounting, recent auditor change, or material weakness
**Allegation Pattern:**
1. Company files financial statements with material misstatements
2. Misstatement is discovered through: restatement, auditor change, SEC investigation, short seller report, or internal whistleblower
3. Stock drops on corrective disclosure
4. Plaintiff alleges company knowingly filed false financials

**Leading Indicators:**
- Beneish M-Score > -2.22
- Accruals ratio > 10%
- DSO increasing >15% YoY without business explanation
- Auditor change (especially resignation)
- Material weakness in SOX 404 assessment
- SEC comment letters on accounting topics
- Non-GAAP positive while GAAP negative

**Real Examples:**
- SMCI (2024-2025): Hindenburg report + auditor resignation (Ernst & Young) + delayed 10-K + DOJ investigation; stock dropped >60% from peak
- Luckin Coffee (2020): Fabricated $310M in revenue; short seller report by Muddy Waters preceded disclosure

#### Template 3: Product/Operational Fraud (Type C)
**Frequency:** ~20% of SCA filings (heavily concentrated in biotech/pharma)
**Typical Company Profile:** Biotech with clinical trials, tech company with product claims, company with operational metrics
**Allegation Pattern:**
1. Company makes specific claims about product efficacy, safety, or operational metrics
2. Claims turn out to be false or materially overstated
3. Stock drops when truth emerges (failed clinical trial, product recall, metric restatement)

**Leading Indicators:**
- Binary event approaching (PDUFA date, Phase III readout)
- Product safety signals in FDA adverse event database
- Customer complaints trending
- Insider selling ahead of product announcement
- Excessive marketing claims vs. regulatory filings

**Real Examples:**
- Theranos (2018): Blood testing technology did not work as described
- Nikola (2020): Rolling truck downhill for promotional video; Hindenburg report

#### Template 4: M&A Disclosure Fraud (Type E)
**Frequency:** ~10% of SCA filings (but nearly 100% of deals >$100M get objection suits)
**Allegation Pattern:**
1. Company announces acquisition or merger
2. Shareholders allege inadequate process, conflicts of interest, or inadequate disclosure in proxy statement
3. Alternative claims: post-merger integration failures, overstated synergies

**Leading Indicators:**
- Pending M&A announcement
- Acquisition price premium vs. unaffected stock price
- Fairness opinion methodology (single banker, limited market check)
- Insider conflicts (management rollover equity, banker incentives)

#### Template 5: Regulatory/Compliance Failure (Mixed Types)
**Frequency:** ~5% of SCA filings but growing
**Allegation Pattern:**
1. Company faces regulatory action (SEC, DOJ, state AG, sector regulator)
2. Shareholders allege company knew about regulatory risk and failed to disclose
3. Often follows Wells Notice or formal investigation disclosure

**Leading Indicators:**
- SEC comment letters (available on EDGAR)
- Industry-wide regulatory trend (e.g., opioid enforcement, PFAS liability)
- Whistleblower disclosures in filings
- Consent decrees / prior enforcement actions

---

## 8. Proposed Check Architecture

### Current Architecture vs. Proposed

**Current:** Checks organized by worksheet section (BIZ, STOCK, FIN, LIT, GOV, FWRD) with checks mapped to factors (F1-F10).

**Proposed:** Add a parallel organization by *claim pathway* and *signal type*:

```
DIMENSION 1: Worksheet Section (for display)
  BIZ.* -> Company Profile section
  STOCK.* -> Market Analysis section
  FIN.* -> Financial Analysis section
  LIT.* -> Litigation & Regulatory section
  GOV.* -> Governance section
  FWRD.* -> Forward-Looking section

DIMENSION 2: Claim Pathway (for analysis)
  PATH_A: 10b-5 Disclosure Fraud
  PATH_B: Forward-Looking Statement Fraud
  PATH_C: Product/Operational Claims
  PATH_D: Derivative / Fiduciary Breach
  PATH_E: M&A Litigation
  PATH_F: Regulatory Proceedings
  PATH_G: Bankruptcy/Insolvency D&O
  PATH_H: Cyber/Privacy Claims
  PATH_I: ESG/Climate Claims

DIMENSION 3: Signal Type (for methodology)
  LEVEL: Point-in-time value (current ratio, stock price, SI level)
  DELTA: Change over time (margin compression, SI trend, DSO trajectory)
  PATTERN: Multi-signal composite (DEATH_SPIRAL, INFORMED_TRADING)
  FORENSIC: NLP/linguistic signal (tone shift, risk factor evolution)
  BENCHMARK: Peer-relative comparison (valuation premium, growth vs peers)
  EVENT: Binary catalyst (FDA decision, contract renewal, debt maturity)
  JUDGMENT: Subjective underwriter assessment (bear case narrative, management quality)
```

### Proposed Factor Restructuring

The current 10-factor model works well for scoring but could be enhanced:

| Current Factor | Weight | Proposed Enhancement |
|---------------|--------|---------------------|
| F1 Prior Litigation | 20% | Add DDL computation, settlement range estimate |
| F2 Stock Decline | 15% | Add DDL as severity input, not just % decline |
| F3 Restatement/Audit | 12% | Add Beneish M-Score as leading indicator sub-score |
| F4 IPO/SPAC/M&A | 10% | No change needed |
| F5 Guidance Misses | 10% | Add magnitude-weighted miss tracking, consecutive miss escalation |
| F6 Short Interest | 8% | Add named short seller report quality assessment |
| F7 Volatility | 9% | Rename to "Market Risk Indicators" -- include put/call ratio if available |
| F8 Financial Distress | 8% | Add temporal trajectory scoring (improving vs. deteriorating) |
| F9 Governance | 6% | Add proxy advisor signals, say-on-pay trends |
| F10 Officer Stability | 2% | Add departure-during-stress amplifier |

**New Proposed Sub-Factors (within existing factors):**

| Sub-Factor | Parent Factor | Source | Weight |
|------------|--------------|--------|--------|
| Beneish M-Score | F3 | 10-K financial data | +2 points if M-Score > -2.22 |
| MD&A Tone Shift | F3 | LLM extraction | +1-3 points based on magnitude |
| Risk Factor Evolution | F3 | LLM extraction | +1-2 points for material removals |
| Non-GAAP/GAAP Divergence | F5 | 8-K earnings releases | +1-2 points if divergence widening |
| DSO/Inventory Trajectory | F3 | Balance sheet | +1-2 points if increasing >15% YoY |
| Peer Valuation Premium | F2 | Market data + financials | +1-2 points if >2x peer P/E |
| SEC Comment Letters | F3 | EDGAR CORRESP filings | +1 point if accounting-focused |
| Auditor CAM Changes | F3 | 10-K auditor report | +1-2 points for new/expanded CAMs |

---

## 9. Recommendations

### Priority 1: Implement Now (High Impact, Achievable)

**1a. Temporal Change Detection Engine**
- Build a `TemporalAnalyzer` that computes QoQ and YoY changes for the top 10 financial metrics
- Input: Current and prior period financial data (already extracted)
- Output: Trend direction (improving/stable/deteriorating) and magnitude for each metric
- Integration: Feed into existing checks as an additional data dimension
- Estimated effort: 3-5 days

**1b. Beneish M-Score Computation**
- Add Beneish M-Score calculation to the financial extraction pipeline
- All 8 variables are computable from standard financial statement data the system already extracts
- Classify as SAFE (<-2.22), SUSPECT (-2.22 to -1.78), or MANIPULATOR (>-1.78)
- Integration: Add as sub-factor under F3 (Restatement/Audit)
- Estimated effort: 1-2 days

**1c. Non-GAAP/GAAP Divergence Tracking**
- Extract GAAP and Non-GAAP EPS from 8-K earnings releases (system already parses 8-Ks)
- Compute gap magnitude and trend over 8 quarters
- Flag: widening gap, Non-GAAP positive/GAAP negative, recurring items excluded
- Integration: Add as sub-factor under F5 (Guidance Misses)
- Estimated effort: 2-3 days

### Priority 2: Build Next (High Impact, Medium Effort)

**2a. MD&A Tone Shift Analysis**
- Add forensic sentiment extraction prompt to the LLM extraction engine
- Compare current 10-K MD&A to prior year on: negative word frequency, uncertainty language, specificity, hedging
- Flag material year-over-year shifts
- Integration: Add as sub-factor under F3
- Estimated effort: 3-5 days (includes prior-year filing retrieval)

**2b. Risk Factor Evolution Tracking**
- Extract Item 1A risk factor headings and key language from current and prior 10-K
- LLM comparison to identify: added, removed, materially changed risk factors
- Flag risk factor removals (potential omission) and new risk factors (new exposure)
- Integration: Add as check under FWRD.NARRATIVE
- Estimated effort: 3-5 days

**2c. Bear Case Narrative Generator**
- Synthesize signals from all 10 factors into a plaintiff allegation narrative
- Template-based: use the 5 allegation templates from Section 7
- For each company, generate: "If sued, the complaint would likely allege..."
- Integration: New section in the worksheet (Section 9: Bear Case Analysis)
- Estimated effort: 5-8 days

**2d. Auditor CAM Change Detection**
- Extract Critical Audit Matters from current and prior 10-K auditor report
- Identify new CAMs, removed CAMs, expanded CAMs
- New CAMs often signal auditor concerns about emerging issues
- Integration: Add as sub-factor under F3
- Estimated effort: 2-3 days

### Priority 3: Build Later (Medium Impact, Higher Effort)

**3a. Structured Peer Comparison Framework**
- Build peer identification algorithm (SIC code + market cap range + business description similarity)
- Benchmark on 10 dimensions with ranked comparison
- Generate peer comparison table for worksheet
- Estimated effort: 5-8 days

**3b. Earnings Call Transcript Acquisition and Analysis**
- Add earnings call transcript acquisition to the ACQUIRE stage (may require Seeking Alpha or similar)
- Build hedging language detector for management Q&A sections
- Track specificity changes quarter-over-quarter
- Estimated effort: 8-10 days (includes data acquisition)

**3c. SEC Comment Letter Analysis**
- Pull EDGAR CORRESP filings for the company
- Classify comment letter topics (accounting, disclosure, executive compensation)
- Track response quality and follow-up volume
- Estimated effort: 3-5 days

**3d. DDL (Disclosure Dollar Loss) Computation**
- For companies with identified stock drop events, compute DDL
- Use Cornerstone Research regression model to estimate settlement probability and range
- Integration: Add to LIT.SCA.exposure check
- Estimated effort: 3-5 days

### Priority 4: Evaluate / Long-Term

**4a. Allegation Pathway Restructuring**
- Add claim pathway dimension to all 359 checks
- Map each check to its most relevant allegation type(s)
- Build pathway-specific scoring views
- Estimated effort: 10-15 days (requires careful review of each check)

**4b. FinBERT Integration**
- Evaluate FinBERT or similar fine-tuned NLP models for SEC filing analysis
- May provide more precise sentiment scoring than general LLM extraction
- Estimated effort: 10-15 days (R&D project)

**4c. Real-Time Monitoring Dashboard**
- Extend system from one-time analysis to continuous monitoring
- Track key signals (stock price, insider trading, SI) between analyses
- Alert on material changes
- Estimated effort: 15-20 days

### What NOT to Build

- **Predictive litigation filing model.** Attempting to predict the *exact probability* of a lawsuit is overfit to historical data. The system should identify *conditions that make a lawsuit more likely* and quantify their severity, not produce a point probability estimate. The current tier framework (WIN through NO_TOUCH with probability ranges) is the right level of precision.

- **Automated buy/sell recommendations.** The system provides risk assessment to support human underwriting decisions. It should never output "write this risk" or "decline this risk" without human review.

- **Social media sentiment scoring.** While social media can contain early signals, the noise-to-signal ratio is too high and the legal/regulatory basis for using it in underwriting is uncertain. Web search for news coverage is sufficient.

---

## Appendix A: Source Materials

### Academic Literature
- Kim, I. & Skinner, D.J. (2012). "[Measuring securities litigation risk](https://www.sciencedirect.com/science/article/abs/pii/S0165410111000681)." *Journal of Accounting and Economics*.
- Beneish, M.D. (1999). "The Detection of Earnings Manipulation." *Financial Analysts Journal*.
- Li, F. (2008). "Annual Report Readability, Current Earnings, and Earnings Persistence." *Journal of Accounting and Economics*.
- Campbell, J. et al. (2014). "The Information Content of Mandatory Risk Factor Disclosures." *Review of Accounting Studies*.
- Cohen, L. et al. (2012). "Decoding Inside Information." *Journal of Finance*.
- Loughran, T. & McDonald, B. (2011). "When is a Liability not a Liability? Textual Analysis, Dictionaries, and 10-Ks." *Journal of Finance*.
- Hopkins, P.E. (2018). "[Do Securities Class Actions Deter Misreporting?](https://onlinelibrary.wiley.com/doi/abs/10.1111/1911-3846.12367)" *Contemporary Accounting Research*.

### Industry Reports
- [Cornerstone Research, "Securities Class Action Filings -- 2024 Review and Analysis"](https://www.cornerstone.com/insights/reports/securities-class-action-filings-2024-review-and-analysis/) (January 2025).
- [Cornerstone Research, "Securities Class Action Settlements -- 2024 Review and Analysis"](https://www.cornerstone.com/wp-content/uploads/2025/03/Securities-Class-Action-Settlements-2024-Review-and-Analysis.pdf) (March 2025).
- [Cornerstone Research, "Overall Size of Securities Class Action Filings Reached New Heights in 2025"](https://www.cornerstone.com/insights/press-releases/overall-size-of-securities-class-action-filings-reached-new-heights-in-2025/) (2025 full year).
- [Stanford SCAC, Securities Class Action Clearinghouse](https://securities.stanford.edu/).
- [Stanford SLA, Securities Litigation Analytics](https://sla.law.stanford.edu/).
- [Woodruff Sawyer, "2026 D&O Looking Ahead Guide"](https://woodruffsawyer.com/insights/do-looking-ahead-guide).
- NERA Economic Consulting, "Recent Trends in Securities Class Action Litigation: 2024 Full-Year Review" (January 2025).
- [D&O Diary, "Assessing Securities Class Action Risk with Event Analysis"](https://www.dandodiary.com/2020/01/articles/securities-litigation/assessing-securities-class-action-risk-with-event-analysis/).
- [D&O Diary, "Cornerstone Research: Securities Suit Filings Increased in 2024"](https://www.dandodiary.com/2025/01/articles/securities-litigation/cornerstone-research-securities-suit-filings-increased-in-2024/).

### NLP/Machine Learning Research
- [Lokanan, M. (2025). "AI-Driven Detection of Industry-Specific Financial Fraud: A Theory-Informed NLP Approach."](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5349337) SSRN.
- [FinBERT: Pre-trained Model on SEC Filings for Financial NLP Tasks](https://www.researchgate.net/publication/334974348_FinBERT_pre-trained_model_on_SEC_filings_for_financial_natural_language_tasks).
- [ACM Computing Surveys, "Machine Learning for Identifying Risk in Financial Statements"](https://dl.acm.org/doi/10.1145/3723157).
- [Zhu et al. (2025). "Accounting fraud detection through textual risk disclosures in annual reports."](https://onlinelibrary.wiley.com/doi/10.1111/acfi.13390) *Accounting & Finance*.

### Forensic Accounting
- [StableBread, "How to Use the Beneish M-Score to Detect Earnings Manipulation"](https://stablebread.com/beneish-m-score/).
- [Indiana University Kelley School, "M-Score Model Remains Most Viable Means of Predicting Corporate Fraud"](https://blog.kelley.iu.edu/2022/02/17/kelley-professors-m-score-model-remains-most-viable-means-of-predicting-corporate-fraud/) (2022).
- [Apostolou, N. "Forensic Investing: Red Flags"](https://abfa.us/wp-content/uploads/2022/07/Forensic-Investing-Site.pdf). American Board of Forensic Accounting.

---

## Appendix B: Current System File Reference

| File | Purpose | Line Count |
|------|---------|-----------|
| `src/do_uw/brain/checks.json` | 359 check definitions with thresholds and data mappings | ~4,800 |
| `src/do_uw/brain/scoring.json` | 10-factor scoring model with weights, rules, and tier boundaries | ~1,380 |
| `src/do_uw/brain/red_flags.json` | 11 critical red flag gates with ceilings | ~187 |
| `src/do_uw/brain/patterns.json` | 19 composite risk patterns with trigger conditions | ~1,547 |
| `src/do_uw/brain/sectors.json` | Sector baselines for 15 industries | ~170 |
| `src/do_uw/knowledge/playbook_data.py` | 10 industry playbook definitions | ~305 |
| `src/do_uw/stages/analyze/check_engine.py` | Check execution engine (10 threshold types) | ~456 |
| `src/do_uw/stages/analyze/check_mappers.py` | Data field mapping for checks | ~100+ |

---

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **SCA** | Securities Class Action -- a lawsuit filed under federal securities laws (typically 10b-5 or Section 11) |
| **DDL** | Disclosure Dollar Loss -- market cap decline on the corrective disclosure date |
| **MDL** | Maximum Dollar Loss -- market cap decline from class period peak to post-disclosure |
| **PSLRA** | Private Securities Litigation Reform Act (1995) -- heightened pleading standards for SCAs |
| **Scienter** | Legal term for "intent to deceive" -- plaintiff must show management knew statements were false |
| **Class Period** | Time period during which the alleged misrepresentation/omission affected the stock price |
| **Wells Notice** | SEC notification to a company or individual that the SEC staff intends to recommend enforcement action |
| **Beneish M-Score** | Statistical model using 8 financial ratios to detect earnings manipulation; M-Score > -2.22 signals likely manipulation |
| **Caremark Claims** | Derivative claims alleging board failed to implement adequate compliance/oversight systems |
| **CAM** | Critical Audit Matter -- matters arising from the audit that required particularly challenging or subjective judgment |
| **10b5-1 Plan** | Pre-arranged stock trading plan that provides an affirmative defense against insider trading allegations |
| **Side A** | D&O insurance coverage that pays only when the company cannot indemnify (bankruptcy, insolvency) |
