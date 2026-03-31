# Old System (594 checks) vs Our Question Framework (222 Qs): Gap Analysis

**Purpose:** Systematic comparison of the predecessor system's ~594 new-business checks against our 222-question framework. Identifies questions we're missing, old system orphans, and things we should NOT import.

**Source documents:**
- `OLD-UNDERWRITER-ANALYSIS.md` — 594 checks across 10 modules + 287 scoring rules
- `OLD-SYSTEM-INSIGHTS.md` — Gap analysis with case studies
- `QUESTIONS-REVIEW.md` — Our 222-question framework (current v2)

---

## SECTION 1: GAPS — Old System Questions We're NOT Asking

### Priority 1: Critical Missing Questions

#### GAP-01: Scientific/Academic Community Monitoring
**Old system:** Module 08, F.4 (10 checks) — PubPeer, Retraction Watch, KOL sentiment, clinical trial integrity, conference reception, peer review concerns, ORI findings
**Our framework:** ZERO coverage
**Why it matters:** In SAVA (Cassava Sciences), PubPeer and academic skepticism predicted the stock collapse 3+ YEARS before SEC action. This is the earliest and most reliable fraud predictor for life sciences companies.
**Proposed addition:** Add to FORWARD Area 3 (Customer & Product Signals) or create new conditional area:
- `[NEW-OLD]` What does scientific community monitoring reveal? (PubPeer, Retraction Watch, KOL sentiment, clinical data integrity — life sciences conditional)

#### GAP-02: Revenue Fraud Pattern Taxonomy
**Old system:** Module 03, A.4.4 + Module 04 checks — 8 specific fraud patterns: bill-and-hold, channel stuffing, side letters, round-tripping, percentage of completion manipulation, cookie jar reserves, big bath charges, Q4 concentration
**Our framework:** Q56 asks about DSO/Q4 concentration/deferred revenue, but we don't name the specific fraud patterns
**Why it matters:** Revenue recognition fraud is the #1 type of financial statement fraud. Naming the patterns enables targeted detection
**Proposed addition:** Enhance FINANCIAL Area 4 Q56:
- `[NEW-OLD]` Are there specific revenue manipulation patterns (channel stuffing, bill-and-hold, round-tripping, side letter indicators)?

#### GAP-03: Derivative Suit Risk Factor Assessment
**Old system:** Module 03 + derivative_lawsuit_patterns.md — 5-category pre-filing risk model: (1) board conflicts of interest, (2) M&A diligence failures, (3) egregious behavior/employees, (4) health/safety Caremark claims, (5) massive fraud
**Our framework:** Q121 asks about existing derivative suits, not risk factors that predict future filing
**Why it matters:** 2/3 of SCAs have related derivative suits. The old system assesses WHICH of the 5 risk categories applies BEFORE suit is filed. Current system only checks if suits already exist.
**Proposed addition:** Add to LITIGATION Area 3:
- `[NEW-OLD]` What derivative suit risk factors are present? (board conflicts, M&A diligence failures, Caremark health/safety, conduct/culture issues)

#### GAP-04: Runoff/Tail Policy Analysis
**Old system:** Module 09, G.6 (12 checks) — Transaction structure, R&W survival periods, indemnification caps, escrow/holdback, R&W insurance, MAC definition, post-close discovery risk, appraisal rights, tail policy requirements
**Our framework:** Q27 asks about pending M&A and Q198 about closings, but ZERO analysis of the M&A transaction's D&O tail implications
**Why it matters:** Runoff/tail is a common D&O policy type. The old system has a complete framework for evaluating the transaction's risk to D&O policies
**Proposed addition:** Could be a conditional section or LITIGATION sub-area:
- `[NEW-OLD]` If M&A is pending/closing, what are the R&W survival periods, indemnification terms, and tail policy requirements?
- `[NEW-OLD]` What post-close discovery risks exist (hidden liabilities, financial misstatement, compliance gaps)?

#### GAP-05: ESG/Greenwashing Risk
**Old system:** Module 05 + energy_sector_litigation_patterns.md — Greenwashing claims, internal climate reports, ESG marketing vs substance, board ESG oversight
**Our framework:** Nothing specific. FWRD.MACRO.climate_transition_risk in checks but not in questions
**Why it matters:** ESG litigation is one of fastest-growing areas. Exxon case established internal climate assessments = disclosure obligation
**Proposed addition:** Add to COMPANY Area 3 or DISCLOSURE:
- `[NEW-OLD]` Is there ESG/greenwashing risk (gap between ESG marketing claims and actual practices)?

#### GAP-06: AI-Specific Hazard Categories
**Old system:** ai_technology_litigation_patterns.md — 7 types: (1) AI washing, (2) misleading AI revenue claims, (3) concealment of AI limitations, (4) false third-party validation, (5) concealment of AI costs, (6) failure to disclose AI risks, (7) misleading AI R&D claims
**Our framework:** Q17 asks about technology dependencies. BIZ.UNI.ai_claims in checks but no specific fraud taxonomy
**Why it matters:** Filing trend accelerating: 7 cases (2023) → 14 (2024) → 12 (first 9mo 2025). AI litigation is a distinct and growing category
**Proposed addition:** Add to COMPANY Area 2 or conditional:
- `[NEW-OLD]` For companies with AI claims: is there AI-specific misrepresentation risk (AI washing, concealed limitations, inflated AI revenue attribution)?

#### GAP-07: Nuclear Trigger / Auto-Decline Aggregation
**Old system:** Module 01, QS-001 to QS-012 + Escalation Rules (ESC-001 to ESC-007) — 12 nuclear triggers, with escalation rule: 3+ RED = elevated review, any CRITICAL = management escalation
**Our framework:** We have individual check severity but no aggregation layer question
**Why it matters:** The concept that combinations of findings trigger different underwriting responses is fundamental. Not just "what's RED" but "how many REDs and in what combination"
**Proposed addition:** Not a section question per se — this is a SCORE stage aggregation pattern. But worth noting:
- The old system's decision matrix (RED% thresholds → CLEAR DECLINE / DECLINE / YELLOW-A / YELLOW-B / GREEN) should influence our SCORE stage design

### Priority 2: Important Missing Questions

#### GAP-08: Compensation Manipulation Patterns
**Old system:** Module 06, D.4 + D.1.11 — Spring-loading options, backdating, excise tax gross-ups, change-in-control triggers (single vs double), share pledging, anti-hedging/pledging policy
**Our framework:** Q91-96 cover structure and alignment. Share pledging noted in OLD-SYSTEM-INSIGHTS but not in our questions
**Proposed additions:**
- `[NEW-OLD]` Are there compensation manipulation indicators (option timing vs news, excessive perquisites, share pledging by insiders)?
- `[NEW-OLD]` Do executives pledge company shares as loan collateral? (Forced selling risk in decline)

#### GAP-09: Sector-Specific Hazard Exposures
**Old system:** Module 01, QS-039 to QS-043 — Opioid exposure, PFAS/environmental contamination, crypto/digital asset exposure, cannabis operations, China VIE structure
**Our framework:** China VIE is in company structure (Q21). Others not explicitly asked
**Why it matters:** These are binary exposure flags. If present, they trigger whole categories of regulatory/litigation risk
**Proposed addition:** Add to COMPANY Area 3:
- `[NEW-OLD]` Does the company have sector-specific hazard exposure? (Opioid, PFAS/environmental contamination, crypto, cannabis, China VIE, social media/Section 230)

#### GAP-10: Section 16 Late Filings & Gift Transactions
**Old system:** Module 09, G.5.7 + G.5.9 — Pattern of late Form 4 filings = compliance breakdown. Large gift transactions before decline = tax-motivated selling disguised as philanthropy
**Our framework:** Q99-103 cover insider trading but not these specific compliance signals
**Proposed addition:** Enhance GOVERNANCE Area 4:
- `[NEW-OLD]` Are there Form 4 compliance issues (late filings, gift transactions timed before declines)?

#### GAP-11: Employee Hotline & Internal Investigation
**Old system:** Module 03, A.5.3 + A.5.2 — Employee hotline activity (material increase disclosed?), board-level internal investigations
**Our framework:** Q188-189 cover whistleblower/investigation LANGUAGE in filings, but not the underlying activity
**Proposed addition:** Could enhance DISCLOSURE Area 5:
- `[NEW-OLD]` Are there signals of internal problems beyond disclosure language (hotline activity increases, board-directed investigations)?

#### GAP-12: Detailed Event-Window Attribution
**Old system:** Module 09, G.1.4a-c — For each material event: 0/1/5/10-day sector-adjusted returns, cumulative market cap loss, recovery analysis
**Our framework:** Q150-153 ask about drops and triggers, but not structured event-window methodology
**Why it matters:** Structured event-window analysis directly maps to damages calculation in securities litigation. The methodology matters as much as the question
**Note:** This is more about analysis methodology than a missing question. Our questions cover it; the implementation should follow the old system's structured approach.

#### GAP-13: CDS Spread / Default Probability
**Old system:** CoreWeave case study — Default insurance (CDS) at 7.9% signals market pricing in serious default risk
**Our framework:** Not asked. Credit rating trajectory (Q46) is the closest
**Proposed addition:** Could enhance FINANCIAL Area 6:
- `[NEW-OLD]` What do credit market signals show (CDS spreads, default probability if available)?

#### GAP-14: Vendor Payment / Payables Stretch
**Old system:** Module 08, F.7.7 — Stretched payables, slow pay to vendors as liquidity stress signal
**Our framework:** Not explicitly asked. Cash flow quality (Q51) is closest
**Note:** This is a good signal but hard to acquire systematically. Could be a sub-point under cash flow or liquidity questions rather than a standalone question.

### Priority 3: Nice-to-Have (Lower Priority)

#### GAP-15: Litigation Funding Activity
**Old system:** Module 06, Check 10.6 — Third-party litigation funders targeting the company
**Note:** Interesting signal but hard to detect. Presence increases litigation probability and severity. LOW priority.

#### GAP-16: Expert Witness Engagement
**Old system:** Module 06, Check 10.7 — Expert witnesses being retained against the company
**Note:** Very early litigation signal but extremely hard to acquire. LOW priority.

#### GAP-17: Congressional Inquiry Tracking
**Old system:** Module 08, F.3 — Letters from Congress, committee hearings
**Our framework:** Q135 [NEW] covers congressional investigations. Already proposed.

#### GAP-18: Union Organizing / NLRB
**Old system:** Module 06, D.5.18 + F.7 — Union campaigns, NLRB filings, collective bargaining
**Our framework:** Q16 covers workforce profile/labor risk. Could be more specific.
**Note:** Labor organizing is growing (Starbucks, Amazon). But current question about workforce risk captures the essence.

#### GAP-19: Forensic Accounting Firm Engagement
**Old system:** Module 06, Check 10.8 — Forensic accountants being engaged, unusual audit team changes
**Note:** Very hard to detect. If discoverable, it's a powerful signal. LOW priority due to acquisition difficulty.

#### GAP-20: Cybersecurity Posture Scoring
**Old system:** Module 08, F.8.9 — SecurityScorecard, BitSight ratings
**Our framework:** Q19 [NEW] covers data/privacy risk profile but not external security scoring
**Note:** Systematic data source exists. Relevant for cyber-D&O crossover. Could be a sub-point under Q19.

---

## SECTION 2: Old System ORPHANS — Checks That Don't Fit

These old system checks exist but don't clearly answer an underwriting question, or answer a question poorly:

### 2.1 Process/Workflow Checks (Not Analysis)
| Old Check | Why Orphan |
|-----------|-----------|
| TRI-001 to TRI-005 (Triage) | Workflow routing, not analysis |
| STR-001 to STR-005 (Streamlined) | Phase completion gates |
| EX-001 to EX-010 (Execution) | Execution order rules |
| VER-001, ZER-001 | Quality assurance protocols |
| DDR-001 to DDR-003 | Deep-dive recommendation routing |
| IND-001 to IND-004 | Module loading instructions |

**Count:** 29 rules that are execution logic, not underwriting analysis. We implement these as pipeline stage ordering, not as questions.

### 2.2 Duplicate/Overlapping Checks
| Old Check | What It Duplicates |
|-----------|-------------------|
| B.5.1-B.5.12 (Stock performance in Financial) | E.1-E.4 (Stock in Market Dynamics) — same analysis in two modules |
| G.1.1-G.1.16 (Stock drops in Prior Acts) | E.1.1-E.1.18 (Stock drops in Market) — third copy |
| G.5.1-G.5.12 (Insider trading in Prior Acts) | D.3.1-D.3.14 (Insider in Governance) — second copy |
| G.4.1-G.4.12 (Disclosure gaps in Prior Acts) | Equivalent to DISCLOSURE section questions |
| A.4.1-A.4.6 (Financial reporting in Litigation) | B.6.1-B.6.12 (Accounting quality in Financial) |
| E.3.5, E.3.6, E.3.7 (Ownership) | D.3.1-D.3.2 (Governance ownership) |

**Count:** ~60 checks that appear in multiple modules. Our section-boundary design eliminates this — each question lives in ONE section. This is a major improvement over the old system.

### 2.3 Granularity Orphans (Too Specific to be Questions)
| Old Check | Why Too Granular |
|-----------|-----------------|
| F.8.5 Domain authority (Moz, Ahrefs) | SEO metric, not D&O signal |
| F.8.6 Email marketing indicators | Marketing operations, not D&O |
| F.8.7 Conversion rate indicators | Sales funnel metric, not D&O |
| F.5.3 Documentary/podcast coverage | Lagging indicator (if Netflix makes a doc, it's already over) |
| D.5.13 Cumulative voting | Exists in few states, almost never D&O relevant |
| D.5.16 NOL poison pill | Tax strategy, not governance risk |
| F.1.14 H-1B sponsorship decline | Very indirect signal |
| C.1.7 Asset light vs heavy | Business school taxonomy, not risk signal |
| C.3.8 Barriers to entry | MBA Porter's analysis, not D&O prediction |
| C.3.10 Supplier/buyer power | Porter's framework, indirect to D&O |
| F.7.2 Port/logistics data | Supply chain intelligence, not D&O |
| F.7.5 Shipping/freight rates | Cost analysis, not D&O |

**Count:** ~12 checks that are interesting business intelligence but don't predict D&O claims.

---

## SECTION 3: Old System Checks We Should NOT Import

### 3.1 Impractical Data Sources
| Item | Why Skip |
|------|---------|
| Dark web monitoring (F.4 area) | Can't systematically acquire. Would require expensive specialized feeds |
| YouTube/TikTok viral video analysis | Too noisy, no systematic acquisition |
| SimilarWeb/Sensor Tower (web traffic) | Paid services, limited free access |
| Bloomberg terminal data (block trades, dark pool) | Enterprise-only, $25K+/year |
| S3 Partners (lending utilization, squeeze probability) | Expensive institutional data |
| Interactive Brokers borrow fee data | Requires brokerage account |
| ISS/Glass Lewis governance ratings | Institutional subscription only |
| MSCI AGR Score | Enterprise subscription only |

**Principle:** Don't build questions around data we can't acquire. If we add the data source later, we add the question then.

### 3.2 Trading Microstructure (Too Granular for Underwriting)
| Item | Why Skip |
|------|---------|
| E.2.5 Cost to borrow | Institutional trading metric |
| E.2.6 Fail-to-deliver volume | SEC mechanical data, noisy |
| E.2.7 Dark pool activity | Requires specialized feeds |
| E.2.9 Options volume vs open interest | Derivatives analysis beyond scope |
| E.2.10 Implied volatility skew | Options pricing analysis |
| E.2.15 Relative volume sustained | Overly granular trading signal |
| E.2.16 Pre/after-hours activity | Marginal signal |
| E.2.17 Exchange short sale volume | Redundant with short interest |
| E.2.18 Securities lending utilization | Institutional data |
| E.2.19 Short squeeze probability | Trading strategy, not D&O |
| E.2.20 Synthetic short position | Deep options analysis |

**Principle:** We're underwriters, not quantitative traders. Short interest level, direction, and named reports are sufficient.

### 3.3 Business Strategy Analysis (Not D&O Predictive)
| Item | Why Skip |
|------|---------|
| C.1.4 Unit economics (LTV, CAC, LTV/CAC) | Covered by sector KPIs where relevant |
| C.1.5 Scalability / operating leverage | Academic metric |
| C.1.8 Platform vs linear model | Business model taxonomy, not risk |
| C.3.5 Pricing power | Downstream effect captured by margin metrics |
| C.3.6 Customer switching costs | Strategic moat analysis |
| C.3.8 Barriers to entry | Porter's framework |
| C.3.10 Supplier/buyer power | Porter's framework |
| C.5.6 Commodity cycle position | Market timing, not D&O |
| C.6.5 Capacity utilization | Operational efficiency metric |
| C.6.10 Business continuity/DR | IT resilience, very indirect |
| C.7.1-C.7.8 Growth strategy (8 checks) | Forward business strategy, not risk assessment |

**Principle:** We assess risk signals, not business strategy. If a strategy fails, the financial metrics and stock price will reflect it.

### 3.4 Redundant with Better Questions We Already Ask
| Old Check | Covered By |
|-----------|-----------|
| B.1.6 Cash concentration risk (offshore) | Liquidity questions capture total cash |
| B.1.7 Restricted cash / total cash | Subsumed by liquidity analysis |
| B.2.8 Floating rate exposure | Subsumed by interest coverage |
| B.2.15-B.2.18 Secured/sub/cross-default/COC | Debt structure detail, covered by leverage questions |
| B.3.7 Revenue volatility (12Q std dev) | Covered by revenue trend and growth questions |
| D.1.5-D.1.8 GC/COO/CTO/division leaders | We focus on CEO/CFO — the ones with litigation exposure |
| D.1.13 Non-compete enforceability | Employment law, very indirect |
| D.1.14 Recent promotions | Positive indicator but not risk-relevant |
| D.3.12 Tax gross-ups | Minor executive comp detail |
| D.3.13 Perquisites analysis | Q95 covers excessive perquisites |

---

## SECTION 4: Module-by-Module Coverage Score

How well does our 222-question framework cover each old system module?

| Old Module | Checks | Our Coverage | Notes |
|-----------|--------|-------------|-------|
| 01 Quick Screen (QS/NEG/SEC/STK) | 68 | **85%** | Missing: SPAC detection, sector-specific hazards (opioid/PFAS/crypto/cannabis), ATM program. Have: all nuclear triggers, financial distress, governance, stock |
| 02 Trigger Matrix | Routing | **N/A** | Process logic, not analysis |
| 03 Litigation/Regulatory | 37 | **90%** | Missing: employee hotline activity, restructuring as standalone. Have: all litigation types, enforcement, whistleblower |
| 04 Financial Health | 112 | **80%** | Missing: covenant trajectory detail, EBITDA addback analysis, commodity analysis, revenue fraud patterns. Have: liquidity, leverage, profitability, cash flow, guidance, forensics. Old system has 112 checks for what we cover in ~39 questions — right level of abstraction |
| 05 Business Model | 74 | **70%** | Missing: commodity exposure analysis, operational execution track record, specific competitive intelligence. Have: business model, concentration, M&A, industry position. Many old checks are business strategy (not D&O risk) |
| 06 Governance | 78 | **85%** | Missing: share pledging, compensation manipulation patterns, Section 16 late filings. Have: board, executives, compensation, insider trading, rights, activism |
| 07 Market Dynamics | 68 | **75%** | Missing: structured event-window methodology, options activity, pre-announcements, PE/VC exit risk. Have: price, drops, volatility, shorts, ownership, analysts, valuation. Old system has excessive trading microstructure |
| 08 Alternative Data | 97 | **65%** | Missing: scientific community (10), regulatory database depth (some), media depth (some), competitive intelligence granularity, digital signals, supply chain signals. Have: employee signals, customer signals, macro, basic media. BIGGEST GAP IS HERE |
| 09 Prior Acts/Prospective | 85 | **80%** | Missing: runoff analysis (12), gift transactions, some drop attribution detail. But ~60 checks are duplicates of Modules 04/06/07 |
| 10 Scoring | 287 rules | **85%** | Our F1-F10 framework covers the same factors. Missing: nuclear trigger aggregation, decision matrix (DECLINE/YELLOW/GREEN) |

**Overall: Our 222 questions cover approximately 78% of the old system's analytical substance.** The 22% gap breaks down:
- ~8% genuinely missing questions (Gaps 01-14 above)
- ~8% intentionally excluded (trading microstructure, impractical data, business strategy)
- ~6% covered by the old system as duplicates across modules (eliminated by our section boundaries)

---

## SECTION 5: Recommended Additions to QUESTIONS-REVIEW.md

Based on this analysis, the following should be added to our question framework:

### Must Add (Priority 1)
1. **Scientific community monitoring** → FORWARD Area 3 or new conditional area (1 question, life sciences)
2. **Revenue fraud pattern taxonomy** → FINANCIAL Area 4 (enhance Q56, 1 question)
3. **Derivative suit risk factors** → LITIGATION Area 3 (1 question)
4. **Runoff/tail analysis** → Conditional section for M&A (2-3 questions)
5. **ESG/greenwashing risk** → COMPANY Area 3 or FORWARD (1 question)
6. **AI-specific hazard categories** → COMPANY Area 2 or conditional (1 question)

### Should Add (Priority 2)
7. **Share pledging by insiders** → GOVERNANCE Area 4 (1 question)
8. **Compensation manipulation patterns** → GOVERNANCE Area 3 (enhance existing)
9. **Sector-specific hazard flags** → COMPANY Area 3 (1 question)
10. **Form 4 compliance / gift transactions** → GOVERNANCE Area 4 (enhance existing)
11. **CDS/credit market signals** → FINANCIAL Area 6 (1 question)
12. **Internal investigation/hotline signals** → DISCLOSURE Area 5 (enhance existing)

### Consider But Lower Priority
13. **Vendor payment stretch** → signal embedded in cash flow questions
14. **Cybersecurity posture scoring** → sub-point of data/privacy question
15. **PE/VC exit risk** → sub-point of ownership question
16. **Litigation funding** → too hard to acquire
17. **Congressional inquiry** → already proposed as [NEW]

**Net impact: +10-12 questions to the framework → ~232-234 total**

---

## SECTION 6: Key Process Insights from Old System

### 6.1 Verification Standards
The old system enforces:
- **Hard data** (financial, regulatory): 1 authoritative source
- **Soft signals** (social media, reviews, news): 2+ independent sources
- **Critical/High findings**: Primary source verification before flagging
→ We have this in CLAUDE.md. Implementation should enforce it.

### 6.2 PURPLE Status (Unknown/Needs Research)
The old system uses a 4-color system: GREEN/YELLOW/RED/PURPLE. PURPLE = data unavailable or unresearchable.
→ Critical concept: prevents false "all clear" when data is simply missing. Our system should distinguish "checked and clear" from "not checked."

### 6.3 Sector-Calibrated Thresholds
The old system has 13 sectors with per-metric calibration tables (different RED/YELLOW thresholds per sector for leverage, short interest, volatility, etc.)
→ Our sector-conditional KPI framework (FINANCIAL Area 8) should include calibrated thresholds, not just metrics.

### 6.4 Event-Window Attribution Methodology
For significant drops, the old system requires structured analysis:
1. Identify trigger event with specific date
2. Calculate 0/1/5/10-day returns
3. Compare to sector ETF same window
4. Attribute: company-specific vs sector vs macro
5. Calculate cumulative market cap loss
→ Our MARKET Area 2 questions should ensure this methodology is followed.

### 6.5 Scoring Tier Mapping to Underwriting Decision
Old system: Score → Tier → Decision → Posture
- EXTREME (70-100): >20% claim probability → Decline or 2-3x rate
- HIGH (50-69): 10-20% → 1.5-2x rate
- AVERAGE (30-49): 5-10% → Market rate
- BELOW AVG (15-29): 2-5% → Discount
- MINIMAL (0-14): <2% → Best rates
→ Our SCORE stage should map to explicit underwriting decisions.

---

## Summary

| Category | Count |
|----------|-------|
| Old system checks (new business) | 594 |
| Old system scoring rules | 287 |
| Our current questions | 222 |
| Genuinely missing questions identified | 12-15 |
| Intentionally excluded (impractical/irrelevant) | ~50 checks |
| Old system duplicates eliminated by our boundaries | ~60 checks |
| Old system process/workflow rules (not analysis) | ~29 rules |
| Recommended additions to our framework | 10-12 questions |
| **Revised question total after additions** | **~232-234** |

The old system is wider but shallower in many areas (lots of checks that are really business intelligence, not D&O risk assessment). Our framework is narrower but more focused on what actually predicts D&O claims. The main gaps are in **alternative data / early warning signals** (Module 08) where the old system's breadth genuinely adds value, and in **runoff/tail analysis** which is a legitimate use case we haven't addressed.
