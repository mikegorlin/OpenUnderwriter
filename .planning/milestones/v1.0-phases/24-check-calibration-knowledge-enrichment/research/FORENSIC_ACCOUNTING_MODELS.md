# Forensic Accounting & Financial Fraud Detection Models

## Research Date: 2026-02-11
## Purpose: Identify quantitative frameworks beyond Altman Z, Piotroski F, Ohlson O, and Beneish M that can be computed from public SEC filing data for D&O underwriting.

---

## 1. Model Inventory

### 1.1 Beneish M-Score (8-Variable) -- ALREADY IMPLEMENTED

**What it detects:** Earnings manipulation. Identifies companies likely manipulating reported earnings through accounting tricks.

**Formula:**
```
M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
    + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
```

**Variables:**
| Variable | Full Name | Formula |
|----------|-----------|---------|
| DSRI | Days Sales in Receivables Index | (AR_t/Rev_t) / (AR_t-1/Rev_t-1) |
| GMI | Gross Margin Index | (GM_t-1/Rev_t-1) / (GM_t/Rev_t) |
| AQI | Asset Quality Index | (1-(CA_t+PPE_t)/TA_t) / (1-(CA_t-1+PPE_t-1)/TA_t-1) |
| SGI | Sales Growth Index | Rev_t / Rev_t-1 |
| DEPI | Depreciation Index | DepRate_t-1 / DepRate_t where DepRate = Dep/(Dep+PPE) |
| SGAI | SGA Expense Index | (SGA_t/Rev_t) / (SGA_t-1/Rev_t-1) |
| TATA | Total Accruals to Total Assets | (NI - OCF) / TA |
| LVGI | Leverage Index | (TL_t/TA_t) / (TL_t-1/TA_t-1) |

**Thresholds:**
- M > -1.78: Likely manipulator
- M between -2.22 and -1.78: Possible manipulator (grey zone)
- M < -2.22: Unlikely manipulator

**Accuracy:** 76% true positive rate, 17.5% false positive rate. In Beneish's 2020 follow-up paper, the method had the lowest false-to-true positive ratio of any non-ML method.

**Data requirement:** XBRL_DIRECT -- all variables computable from standard financial statements.

**Status in our system:** IMPLEMENTED in `distress_formulas.py` lines 94-221.

---

### 1.2 Dechow F-Score (Predicting Material Accounting Misstatements)

**What it detects:** Material accounting misstatements (broader than earnings manipulation). Based on analysis of 2,000+ SEC enforcement actions (AAERs). Specifically targets the probability that a firm has materially misstated its financial statements.

**Key difference from Beneish:** Beneish focuses on deliberate earnings manipulation using ratio indices. Dechow's F-Score uses a logistic regression framework that incorporates accrual quality measures, financial performance changes, and market incentive variables. The F-Score was trained on actual SEC enforcement data (AAERs), making it more directly relevant to regulatory risk.

**Formula (Model 1):**
```
Predicted Value = -7.893 + 0.790*RSST_ACC + 2.518*CH_REC + 1.191*CH_INV
                  + 1.979*SOFT_ASSETS + 0.171*CH_CS - 0.932*CH_ROA
                  + 1.029*ISSUE

F-Score = e^(Predicted Value) / (1 + e^(Predicted Value))
```

**Variables:**
| Variable | Definition | Formula |
|----------|-----------|---------|
| RSST_ACC | Richardson-Sloan-Soliman-Tuna accruals | Change in net operating assets / Average total assets. NOA = (TA - Cash - Investments) - (TL - Preferred Stock) |
| CH_REC | Change in receivables | (AR_t - AR_t-1) / Average TA |
| CH_INV | Change in inventory | (Inv_t - Inv_t-1) / Average TA |
| SOFT_ASSETS | Percentage of soft (non-hard) assets | (TA - PPE - Cash) / TA |
| CH_CS | Change in cash sales | % change in (Revenue - Change in AR) |
| CH_ROA | Change in return on assets | ROA_t - ROA_t-1, where ROA = NI/TA |
| ISSUE | Securities issuance | 1 if company issued debt or equity during year, else 0 |

**Three Model Variants:**
- Model 1: Accrual quality variables only (above)
- Model 2: Adds financial performance + nonfinancial variables (actual vs predicted issuance, abnormal employee headcount changes)
- Model 3: Adds market-based variables (market-adjusted returns, market cap changes)

**Thresholds:**
- F-Score < 1.00: Normal risk
- F-Score >= 1.00: Above-normal risk
- F-Score > 1.85: Extreme risk
- F-Score > 2.45: Very extreme risk

**Accuracy:** Based on SEC AAER data. Model 1 achieves conditional probability of misstatement ~3x unconditional probability when F-Score > 1.0. Models 2 and 3 improve further.

**Data requirement:** XBRL_DIRECT for Model 1. Model 2 needs XBRL_PLUS_TEXT (employee headcount from 10-K text). Model 3 needs EXTERNAL (market data).

**Implementation priority:** HIGH -- Model 1 is fully computable from existing XBRL data. Directly trained on SEC enforcement actions makes it the most relevant fraud model for D&O underwriting.

---

### 1.3 Sloan Accrual Ratio (Accrual Anomaly)

**What it detects:** Earnings quality deterioration. Companies with high accruals (earnings far exceeding cash flows) tend to have less persistent earnings and higher risk of future performance decline.

**Formulas (two approaches):**

Cash Flow Approach (preferred):
```
Sloan Ratio = (Net Income - CFO - CFI) / Average Total Assets
```

Balance Sheet Approach:
```
Sloan Ratio = (Net Income - CFO) / Total Assets
```

Simpler variant:
```
Sloan Ratio = (Net Income - Free Cash Flow) / Total Assets
```

**Thresholds:**
| Range | Interpretation |
|-------|---------------|
| -10% to +10% | Safe zone -- earnings backed by cash |
| +10% to +25% | Warning -- accrual buildup |
| > +25% | Danger -- earnings highly likely composed of accruals |
| < -25% | Also warning -- may indicate aggressive write-downs |

**Accuracy:** Over 40 years (1962-2001), buying lowest-accrual companies and shorting highest-accrual companies yielded 18% annualized vs. S&P 500's 7.4%. Note: Green, Hand & Soliman (2011) found the anomaly's predictive power for stock returns has diminished, but the *earnings quality signal* remains valid for fraud/risk assessment.

**Data requirement:** XBRL_DIRECT

**Implementation note:** Our system already computes `accruals_ratio = (NI - OCF) / TA` in `earnings_quality.py` line 109-120. However, we use a single threshold (0.10) rather than the graduated Sloan thresholds. Enhancement: adopt the -25%/-10%/+10%/+25% zone classification and compute the full Cash Flow approach variant.

**Status:** PARTIALLY IMPLEMENTED (basic version exists, needs enhancement to full Sloan classification).

---

### 1.4 Jones Model / Modified Jones Model (Discretionary Accruals)

**What it detects:** Discretionary (abnormal) accruals -- the portion of total accruals that management can manipulate, separated from nondiscretionary accruals that arise naturally from business operations.

**Original Jones Model (1991):**
```
Total Accruals / TA_t-1 = a1*(1/TA_t-1) + a2*(dREV/TA_t-1) + a3*(PPE/TA_t-1) + e

Where:
  dREV = change in revenue
  PPE = gross property, plant and equipment
  a1, a2, a3 = industry-year regression coefficients
  e = discretionary accruals (the residual)
```

**Modified Jones Model (Dechow, Sloan & Sweeney, 1995):**
```
Total Accruals / TA_t-1 = a1*(1/TA_t-1) + a2*((dREV - dREC)/TA_t-1)
                          + a3*(PPE/TA_t-1) + e

Where:
  dREC = change in net receivables
  Key insight: Revenue changes are adjusted for receivable changes,
  since revenue recognized in receivables may be manipulated.
```

**Computation challenge:** The Jones Model requires cross-sectional regression across industry peers to estimate normal accruals. This makes it computationally expensive -- you need a panel of comparable companies to estimate the regression coefficients, then compute the residual for the target company.

**Why it matters for D&O:** The Modified Jones Model is the most widely used academic method for detecting earnings management. High discretionary accruals are a proven predictor of SEC enforcement actions, restatements, and securities class actions.

**Data requirement:** XBRL_DIRECT for the target company, but EXTERNAL for the industry regression (need peer company data).

**Implementation feasibility:** MEDIUM. We could implement a simplified version using industry-average coefficients from academic literature rather than computing our own regressions. Or use the Dechow F-Score's RSST_ACC variable as a proxy (which captures similar information without requiring industry regression).

**Recommendation:** Do NOT implement the full Jones Model. Instead, implement Dechow F-Score (which incorporates similar accrual quality measures) and enhance the Sloan Ratio. The Jones Model is primarily an academic tool requiring panel data infrastructure that exceeds our scope.

---

### 1.5 Montier C-Score (Cooking the Books Score)

**What it detects:** Financial statement manipulation through 6 binary signals. Designed as a simple, practitioner-friendly alternative to the Beneish M-Score.

**Formula:** Sum of 6 binary indicators (0 = no, 1 = yes), yielding score 0-6.

**The Six Variables:**
| # | Signal | What to Check | Formula |
|---|--------|--------------|---------|
| 1 | NI > OCF divergence | Growing gap between net income and operating cash flow | 1 if (NI - OCF) is increasing YoY |
| 2 | Rising DSO | Days sales outstanding increasing | 1 if DSO_t > DSO_t-1 |
| 3 | Rising inventory days | Days sales of inventory increasing | 1 if DSI_t > DSI_t-1 where DSI = (Inventory/COGS)*365 |
| 4 | Rising other current assets | Other current assets growing faster than revenue | 1 if (OtherCA/Rev)_t > (OtherCA/Rev)_t-1 |
| 5 | Declining depreciation rate | Depreciation declining relative to gross PPE | 1 if (Dep/GrossPPE)_t < (Dep/GrossPPE)_t-1 |
| 6 | High total asset growth | Total assets growing rapidly (often via acquisitions) | 1 if TA growth > threshold (typically >10%) |

**Thresholds:**
- 0-2: Low manipulation risk ("best")
- 3: Moderate concern
- 4-6: High manipulation risk ("worst")

**Performance:**
- US stocks with C-Score 5-6 underperform by ~8% annually (1993-2007)
- European stocks with high C-Scores underperform by ~5% annually
- Combined with overvaluation, underperformance reaches 14-17% annually

**Data requirement:** XBRL_DIRECT -- all 6 signals computable from standard financials.

**Implementation priority:** HIGH -- extremely simple to implement (6 binary checks). Complements the Beneish M-Score by being more intuitive for underwriters. The binary nature makes it easy to explain *which* signals fired and why.

**D&O relevance:** Each signal corresponds to a specific manipulation technique that could lead to D&O claims. Signal 1 (NI vs OCF) maps to revenue inflation. Signal 2 (DSO) maps to channel stuffing. Signal 3 (inventory) maps to inventory fraud. Signal 5 (depreciation) maps to asset life manipulation.

---

### 1.6 Lev-Thiagarajan 12 Fundamental Signals

**What it detects:** Earnings quality through 12 fundamental signals identified from analyst publications and the financial press. Each signal predicts whether current earnings will persist into future periods.

**The 12 Signals:**
| # | Signal | What It Measures | Computation |
|---|--------|-----------------|-------------|
| 1 | Inventory | Inventory growth vs sales growth | % change inventory - % change sales. Positive = buildup |
| 2 | Accounts Receivable | AR growth vs sales growth | % change AR - % change sales. Positive = deterioration |
| 3 | Capital Expenditure | CapEx growth vs industry | CapEx growth vs industry median. Low = underinvestment |
| 4 | R&D | R&D spending trend | % change R&D vs revenue. Declining = cutting investment |
| 5 | Gross Margin | Gross margin change | GM_t - GM_t-1. Negative = deterioration |
| 6 | SGA Expense | SGA growth vs sales growth | % change SGA - % change sales. Positive = declining efficiency |
| 7 | Doubtful Receivables | Provision for doubtful debts | % change provision - % change AR. Positive = more conservative |
| 8 | Effective Tax Rate | ETR change | ETR_t - ETR_t-1. Declining may signal tax aggression or one-time items |
| 9 | Order Backlog | Backlog growth vs sales | % change backlog - % change sales. Negative = weakening demand |
| 10 | Labor Force | Employee productivity | % change sales - % change employees. Negative = declining productivity |
| 11 | LIFO Earnings | LIFO reserve impact | LIFO reserve change / NI. Large = significant income distortion |
| 12 | Audit Qualification | Auditor concerns | Binary: 1 if qualified/adverse opinion, else 0 |

**Scoring:** Each signal is coded as +1 (positive for future earnings), -1 (negative), or 0 (neutral). Aggregate score ranges from -12 to +12. Higher = better earnings quality outlook.

**Accuracy:** Lev & Thiagarajan found fundamental signals added ~70% to the explanatory power of earnings for stock returns.

**Data requirement:** Mixed:
- Signals 1-8: XBRL_DIRECT
- Signal 9 (order backlog): XBRL_PLUS_TEXT (often disclosed in MD&A, not always in XBRL)
- Signal 10 (labor force): XBRL_PLUS_TEXT (employee count from 10-K Part I)
- Signal 11 (LIFO): XBRL_PLUS_TEXT (LIFO reserve from inventory footnotes)
- Signal 12 (audit qualification): XBRL_PLUS_TEXT (auditor's report)

**Implementation priority:** MEDIUM-HIGH -- Signals 1-8 are trivially computable. Signals 9-12 require text extraction but add significant value. The framework is especially useful because each signal is independently interpretable and maps to specific underwriting concerns.

---

### 1.7 Benford's Law Analysis

**What it detects:** Digit distribution anomalies in financial statement data. If financial numbers are naturally generated, the first digit follows a predictable logarithmic distribution (digit 1 appears ~30.1% of the time, digit 2 ~17.6%, etc.). Deviations suggest manual adjustment or fabrication.

**Expected Distribution (First Digit Law):**
| Digit | Expected % |
|-------|-----------|
| 1 | 30.1% |
| 2 | 17.6% |
| 3 | 12.5% |
| 4 | 9.7% |
| 5 | 7.9% |
| 6 | 6.7% |
| 7 | 5.8% |
| 8 | 5.1% |
| 9 | 4.6% |

**Tests Applied:**
1. **First Digit Test:** Compare first-digit frequency distribution to Benford's expected
2. **First Two-Digit Test:** More granular -- 90 possible combinations
3. **Chi-Square Test:** Statistical significance of deviation
4. **Mean Absolute Deviation (MAD):** Average deviation from Benford's expected distribution
   - MAD < 0.006: Close conformity
   - MAD 0.006-0.012: Acceptable conformity
   - MAD 0.012-0.015: Marginally acceptable
   - MAD > 0.015: Nonconformity (red flag)

**Empirical validation:** Audit Analytics found companies with financial statements that do not conform to Benford's distribution have a greater chance of having adverse SOX 302/404 opinions, financial restatements, and late filings.

**Application to SEC filings:** Apply to all numerical values in financial statements -- line items on income statement, balance sheet, cash flow statement, and footnote disclosures. The more numbers available, the more reliable the test.

**Data requirement:** XBRL_DIRECT -- needs a large set of financial values from the statements.

**Implementation priority:** MEDIUM -- Conceptually elegant and statistically grounded. However, requires careful implementation:
- Need sufficient number of data points (minimum ~50-100 values) for statistical validity
- Some line items are inherently constrained (e.g., percentage fields) and should be excluded
- Works best as a screening tool -- flags companies for deeper investigation, not as a standalone fraud indicator
- False positive rate is higher than model-based approaches

**D&O relevance:** Companies failing Benford's Law analysis are more likely to have internal control weaknesses, which directly correlates with D&O claims related to SOX compliance failures.

---

### 1.8 Cash Flow Quality Score

**What it detects:** Whether reported earnings are backed by real cash generation. A composite measure combining multiple cash flow quality metrics.

**Components:**

**a) Quality of Earnings Ratio (QoE):**
```
QoE = CFO / Net Income
```
- QoE > 1.0: Higher quality (cash > reported earnings)
- QoE < 1.0: Lower quality (earnings inflated by accruals)
- QoE < 0.5: Red flag
- QoE negative while NI positive: Critical red flag

**b) Cash Conversion Efficiency:**
```
CCE = Free Cash Flow / EBITDA
```
- CCE > 0.5: Healthy
- CCE 0.2-0.5: Moderate
- CCE < 0.2: Poor conversion

**c) Accruals Intensity:**
```
AI = |Net Income - CFO| / Revenue
```
- AI < 0.05: Very low accrual intensity (good)
- AI 0.05-0.10: Normal
- AI > 0.10: High accrual intensity (concerning)

**d) Cash Flow Adequacy:**
```
CFA = CFO / (CapEx + Debt Payments + Dividends)
```
- CFA > 1.0: Self-funding
- CFA < 1.0: Requires external funding

**e) Multi-Period Divergence:**
```
Divergence = Count of quarters where (NI > 0 AND CFO < 0) over last 8 quarters
```
- 0-1 quarters: Normal
- 2-3 quarters: Concerning
- 4+ quarters: Critical red flag

**Composite Score Design:**
```
Cash Flow Quality Score = weighted average of component scores
  QoE weight: 30%
  CCE weight: 20%
  AI weight: 20%
  CFA weight: 15%
  Multi-Period Divergence weight: 15%
```

**Data requirement:** XBRL_DIRECT

**Implementation priority:** HIGH -- Our system already computes OCF/NI ratio and accruals ratio in `earnings_quality.py`. Enhancement would add CCE, AI, multi-period divergence, and the composite score.

**Status:** PARTIALLY IMPLEMENTED (OCF/NI and basic accruals in earnings_quality.py, but missing CCE, AI, multi-period divergence, and composite scoring).

---

### 1.9 Revenue Quality Score

**What it detects:** Revenue recognition manipulation, channel stuffing, and artificial revenue inflation.

**Components:**

**a) DSO Trend Analysis:**
```
DSO = (Accounts Receivable / Revenue) * 365
DSO Change = DSO_t - DSO_t-1
DSO Acceleration = DSO_Change_t - DSO_Change_t-1  (difference-in-differences)
```
- DSO increasing while revenue increasing: Possible channel stuffing
- DSO acceleration positive: Worsening trend

**b) Deferred Revenue Analysis (SaaS/subscription companies):**
```
Deferred Revenue Ratio = Deferred Revenue / Revenue
DR Change = DR_Ratio_t - DR_Ratio_t-1
```
- Declining DR ratio while revenue growing: May indicate pulling forward future revenue
- Increasing DR ratio: Generally positive (future revenue pipeline growing)

**c) Revenue-Receivable Divergence:**
```
RR Divergence = (% change AR) - (% change Revenue)
```
- Positive divergence: Revenue recognized but not collected -- possible manipulation
- Divergence > 10%: Red flag

**d) Allowance for Doubtful Accounts Ratio:**
```
ADA Ratio = Allowance for Doubtful Accounts / Gross Receivables
ADA Change = ADA_Ratio_t - ADA_Ratio_t-1
```
- Declining ADA ratio with rising receivables: Under-reserving

**e) Fourth Quarter Revenue Spike:**
```
Q4 Revenue Concentration = Q4 Revenue / Annual Revenue
```
- Normal: 20-30% depending on industry (some seasonality expected)
- > 35%: May indicate year-end push, channel stuffing, or "hockey stick" pattern
- Compare to prior year Q4 concentration for trend

**f) Revenue Quality Composite:**
```
Score 0-100:
  DSO trend component: 25%
  Revenue-receivable divergence: 25%
  Deferred revenue analysis: 20%
  ADA adequacy: 15%
  Q4 concentration: 15%
```

**Data requirement:** XBRL_DIRECT for most components. Quarterly data needed for Q4 analysis (available via 10-Q filings).

**Implementation priority:** MEDIUM-HIGH -- DSO is already tracked in `earnings_quality.py`. Adding the full revenue quality composite would significantly improve revenue manipulation detection.

---

### 1.10 Audit Risk Indicators

**What it detects:** Heightened audit risk correlating with financial reporting problems and D&O exposure.

**Components:**

**a) Auditor Change:**
- Auditor change within 2 years: 1 point
- Downgrade from Big 4 to non-Big 4: 2 points
- Multiple changes in 5 years: 3 points
- Change during regulatory investigation: 4 points

**b) Audit Fee Analysis:**
```
Audit Fee Ratio = Audit Fees / Total Assets (or Revenue)
Audit Fee Change = % change in audit fees YoY
Non-Audit Fee Ratio = Non-Audit Fees / Total Fees
```
- Unexpected increase in audit fees (>20% YoY without revenue growth): May signal complexity or problems found
- Non-audit fee ratio > 50%: Independence concern
- Declining audit fees despite growing complexity: May signal auditor shopping

**c) Material Weakness / Significant Deficiency:**
- Current year material weakness in ICFR: Critical (SOX 302/404)
- Prior year MW remediated: Moderate concern
- Significant deficiency: Moderate concern
- Track pattern over 3 years

**d) Critical Audit Matters (CAMs):**
- Number of CAMs vs. industry median
- CAMs related to revenue recognition: Higher risk
- CAMs related to valuation of assets: Moderate risk
- New CAMs appearing that were not in prior year

**e) Going Concern:**
- Going concern opinion: Critical risk
- Going concern removed (previously had one): Still elevated risk for 2 years
- "Substantial doubt" language without formal going concern

**f) Restatement History:**
- Restatement in last 3 years: Critical
- Big R restatement (material, requires amended filing): Very critical
- Little r restatement (immaterial, disclosed in current filing): Moderate
- Multiple restatements: Extreme risk

**g) Late Filing (NT 10-K / NT 10-Q):**
- Any late filing in last 3 years: Red flag
- Repeated late filings: Critical

**Audit Risk Composite Score:**
```
Score 0-100 (100 = highest risk):
  Material weakness: 25 points
  Going concern: 20 points
  Restatement: 20 points
  Auditor change: 15 points
  Audit fee anomaly: 10 points
  Late filing: 10 points
```

**Data requirement:** XBRL_PLUS_TEXT -- audit fees are in XBRL (proxy statement/10-K), but MW, CAMs, going concern require text extraction from auditor's report. Restatement history may require external data (Audit Analytics database).

**Implementation priority:** HIGH -- Many of these signals are already partially tracked in our governance/audit section. Formalizing them into a scored framework would add significant value.

---

## 2. Comparison Matrix

| Model | Detects | Variables | Accuracy | False Positives | Data Source | Compute Complexity | D&O Relevance |
|-------|---------|-----------|----------|-----------------|-------------|-------------------|--------------|
| **Beneish M-Score** | Earnings manipulation | 8 ratio indices | 76% TP | 17.5% | XBRL_DIRECT | Low | HIGH -- earnings fraud claims |
| **Dechow F-Score** | Material misstatements | 7 accrual/performance | ~3x lift | Moderate | XBRL_DIRECT (M1) | Low | VERY HIGH -- trained on AAERs |
| **Sloan Accrual Ratio** | Earnings quality | 1 ratio | High for quality | Low | XBRL_DIRECT | Very Low | MEDIUM -- quality deterioration |
| **Modified Jones** | Discretionary accruals | 3 + regression | Academic gold standard | Industry-dependent | EXTERNAL (peers) | High | HIGH but impractical |
| **Montier C-Score** | Book cooking | 6 binary | Performance validated | Moderate | XBRL_DIRECT | Very Low | HIGH -- intuitive signals |
| **Lev-Thiagarajan** | Earnings sustainability | 12 signals | 70% added power | Signal-dependent | XBRL + TEXT | Medium | MEDIUM-HIGH |
| **Benford's Law** | Data fabrication | Digit distribution | Screening tool | Higher | XBRL_DIRECT | Medium | MEDIUM -- screening only |
| **Cash Flow Quality** | Earnings-cash divergence | 5 components | Well-validated | Low | XBRL_DIRECT | Low | HIGH |
| **Revenue Quality** | Revenue manipulation | 6 components | Well-validated | Moderate | XBRL_DIRECT | Low-Medium | VERY HIGH -- common fraud |
| **Audit Risk** | Reporting problems | 7 components | Highly predictive | Low | XBRL + TEXT | Medium | VERY HIGH -- direct link |

---

## 3. What's Computable Now

### Tier 1: XBRL_DIRECT -- Can implement immediately from existing data
These models need only structured XBRL financial data that our system already extracts:

| Model | Status | Implementation Effort |
|-------|--------|----------------------|
| Beneish M-Score | DONE | Already in distress_formulas.py |
| Dechow F-Score (Model 1) | NOT IMPLEMENTED | 2-3 hours. Similar input structure to Beneish |
| Montier C-Score | NOT IMPLEMENTED | 1-2 hours. 6 simple binary checks |
| Enhanced Sloan Ratio | PARTIALLY DONE | 1 hour. Add graduated thresholds to existing code |
| Cash Flow Quality Score | PARTIALLY DONE | 2-3 hours. Enhance existing earnings_quality.py |
| Revenue Quality Score | PARTIALLY DONE | 3-4 hours. DSO exists, add remaining components |
| Benford's Law | NOT IMPLEMENTED | 3-4 hours. Statistical analysis of all XBRL values |

### Tier 2: XBRL_PLUS_TEXT -- Needs text extraction from filings
These need structured XBRL data plus NLP on specific 10-K/proxy sections:

| Model | Component Needing Text | Text Source |
|-------|----------------------|-------------|
| Lev-Thiagarajan (full) | Signals 9-12 | Order backlog (MD&A), employee count (Part I), LIFO reserve (notes), audit opinion |
| Audit Risk Score | MW, CAMs, going concern | Auditor's report, Item 9A |
| Revenue Quality (Q4 analysis) | Quarterly revenue breakdown | 10-Q filings |

### Tier 3: EXTERNAL -- Needs data beyond SEC filings

| Model | External Data Needed |
|-------|---------------------|
| Modified Jones | Industry peer regression panel |
| Dechow F-Score Model 2 | Employee headcount trends, predicted vs actual issuance |
| Dechow F-Score Model 3 | Market-adjusted stock returns, market cap changes |

---

## 4. Qualitative Red Flags -- Non-Quantitative Signals

### 4.1 Revenue Recognition Manipulation
- Revenue recognition policy changes disclosed in footnotes
- New or unusual revenue arrangements (bill-and-hold, consignment reclassified)
- Related-party revenue (especially if >10% of total)
- Revenue from non-recurring sources classified as operating
- "Round number" revenue figures near analyst consensus estimates

### 4.2 Expense and Cost Manipulation
- Capitalizing expenses that should be expensed (e.g., WorldCom capitalizing line costs)
- Changes in depreciation method or useful life assumptions
- Reclassifying operating expenses as non-recurring/restructuring
- Pension assumption changes (discount rate, expected return on assets)
  - Increasing expected return raises income without real cash
  - Lowering discount rate increases obligation but may be hidden in OCI
- OPEB assumption changes (healthcare cost trend rate)

### 4.3 Reserve and Accrual Manipulation
- **Cookie Jar Reserves:** Over-reserving in good years, releasing reserves to smooth earnings in bad years. Detection: reserve balance stability relative to underlying exposure volatility.
- **Big Bath:** Taking massive one-time charges (typically upon new CEO arrival) to depress baseline, making future comparisons easier. Detection: unusually large restructuring/impairment charges concentrated in a single quarter, especially coinciding with leadership change.
- **Warranty Reserve Manipulation:** Declining warranty reserve ratio while product returns/complaints stable or increasing.
- **Litigation Reserve Inadequacy:** Comparing disclosed contingent liabilities to known pending litigation.

### 4.4 Balance Sheet Manipulation
- Off-balance-sheet entity proliferation (VIEs, SPEs)
- Goodwill impairment delay -- goodwill growing relative to total assets without testing
- Inventory valuation method changes
- Investment classification changes (HTM vs AFS vs trading) to manage gains/losses
- Operating vs. finance lease classification choices

### 4.5 Cash Flow Manipulation
- Reclassifying operating cash outflows as investing (capitalizing expenses)
- Selling receivables (factoring) to inflate CFO
- Extending payables beyond normal terms to inflate CFO
- Non-recurring items in CFO not clearly disclosed
- Stock-based compensation addback distorting CFO quality

### 4.6 Disclosure and Governance Red Flags
- Unusual fourth quarter adjustments (>25% of annual adjustments in Q4)
- Frequent changes in accounting policies or estimates
- Related party transaction complexity and volume increasing
- Non-GAAP metrics diverging further from GAAP metrics over time
- Auditor resignation (vs. non-renewal/dismissal)
- Audit committee member turnover
- Internal audit function changes
- Whistleblower claims disclosed in risk factors

### 4.7 Management Behavior Signals
- Insider selling acceleration while making positive public statements
- CEO/CFO certification changes or restatement of prior certifications
- Departure of CFO or CAO without clear succession
- "Personal reasons" departure explanations for senior finance executives
- Board committee restructuring that reduces audit committee authority
- Declining to answer specific analyst questions about accounting policies

### 4.8 Tax-Related Signals
- Effective tax rate significantly below statutory rate without clear explanation
- Increasing tax benefit from stock-based compensation (may mask underlying tax issues)
- Significant deferred tax asset valuation allowance changes
- Transfer pricing arrangements with related entities in low-tax jurisdictions
- Unusual tax refunds or settlements

---

## 5. Organizing Framework for Financial Forensics in D&O Underwriting

### 5.1 By Manipulation Type

```
REVENUE INFLATION
  Signals: DSO trend, AR/Revenue divergence, Q4 concentration, deferred revenue
  Models: Beneish DSRI, Montier signal #2, Revenue Quality Score
  Check: "Is revenue growth real?"

EXPENSE DEFERRAL / CAPITALIZATION
  Signals: Asset quality delta, depreciation rate changes, CapEx vs peers
  Models: Beneish AQI/DEPI, Montier signal #5, Lev-Thiagarajan #3
  Check: "Are expenses being hidden in the balance sheet?"

COOKIE JAR / RESERVE MANIPULATION
  Signals: Reserve volatility, earnings smoothness, restructuring charge patterns
  Models: Sloan Ratio trends, Jones discretionary accruals
  Check: "Are reserves being used to manage earnings?"

CASH FLOW DISTORTION
  Signals: CFO/NI divergence, factoring activity, payables extension
  Models: QoE ratio, Cash Flow Quality Score, Montier signal #1
  Check: "Is cash flow matching reported earnings?"

FINANCIAL DISTRESS CONCEALMENT
  Signals: Altman Z trajectory, going concern language, debt covenant proximity
  Models: Altman Z-Score, Ohlson O-Score, Cash Flow Adequacy
  Check: "Is the company hiding financial stress?"

GOVERNANCE FAILURE
  Signals: Auditor changes, MW, restatements, insider selling, board turnover
  Models: Audit Risk Score, Lev-Thiagarajan #12, governance quality score
  Check: "Are the gatekeepers functioning?"
```

### 5.2 By Detection Method

```
RATIO ANALYSIS (quantitative, point-in-time)
  Beneish M-Score, Dechow F-Score, Montier C-Score, QoE Ratio

TREND ANALYSIS (quantitative, multi-period)
  Sloan Ratio trajectory, DSO trends, Altman Z trajectory, reserve patterns

CROSS-STATEMENT CONSISTENCY (quantitative, structural)
  Benford's Law, NI vs CFO reconciliation, balance sheet vs income statement checks

TEXT ANALYSIS (NLP on filings)
  MD&A sentiment, auditor's report language, risk factor changes, hedging language

BEHAVIORAL ANALYSIS (qualitative, requires judgment)
  Insider trading patterns, management tone, departure patterns, board dynamics
```

### 5.3 By Risk Level (Proven Predictive Power)

```
TIER 1 -- PROVEN PREDICTORS (high confidence, well-validated)
  Beneish M-Score, Dechow F-Score, QoE Ratio, DSO trend,
  Altman Z-Score, Piotroski F-Score, Ohlson O-Score,
  Material weakness, restatement history

TIER 2 -- STRONG DIRECTIONAL SIGNALS (moderate confidence)
  Montier C-Score, Sloan Ratio, Revenue Quality components,
  Audit fee anomalies, auditor changes, Lev-Thiagarajan signals,
  Cash Flow Adequacy, insider selling patterns

TIER 3 -- EXPLORATORY / SCREENING (lower confidence, supplement other signals)
  Benford's Law, NLP sentiment analysis, Benford's Law on footnotes,
  Social media sentiment, employee review sentiment,
  Q4 concentration analysis, related party transaction volume
```

### 5.4 By Data Source (Implementation Feasibility)

```
XBRL-COMPUTABLE (can automate fully)
  Beneish M-Score, Dechow F-Score M1, Montier C-Score,
  Sloan Ratio, Cash Flow Quality, Revenue Quality (partial),
  Benford's Law, Altman Z, Ohlson O, Piotroski F

REQUIRES NLP ON FILING TEXT (can automate with text extraction)
  Audit risk indicators, Lev-Thiagarajan signals 9-12,
  MD&A sentiment analysis, risk factor changes,
  going concern language, CAM analysis

REQUIRES EXTERNAL DATA (needs additional data sources)
  Jones Model (peer panel), market-based indicators,
  insider trading data, employee headcount trends,
  auditor history database, restatement database
```

---

## 6. Composite Score Design -- "Financial Integrity Score"

### 6.1 Concept

A single 0-100 score representing the overall financial statement integrity and earnings quality of a company, combining multiple validated models into a weighted composite. Higher score = higher integrity / lower manipulation risk.

### 6.2 Architecture

```
FINANCIAL INTEGRITY SCORE (0-100)
|
+-- Manipulation Detection Component (30%)
|     Beneish M-Score (normalized): 40%
|     Dechow F-Score (normalized):  35%
|     Montier C-Score (normalized): 25%
|
+-- Accrual Quality Component (20%)
|     Sloan Accrual Ratio: 50%
|     Accruals Intensity: 30%
|     Multi-period NI vs CFO divergence: 20%
|
+-- Revenue Quality Component (20%)
|     DSO trend: 30%
|     Revenue-Receivable divergence: 30%
|     Deferred revenue analysis: 20%
|     Q4 revenue concentration: 20%
|
+-- Cash Flow Quality Component (15%)
|     QoE Ratio (CFO/NI): 40%
|     Cash Conversion Efficiency: 30%
|     Cash Flow Adequacy: 30%
|
+-- Audit Risk Component (15%)
      Material weakness: 30%
      Auditor changes: 20%
      Restatement history: 25%
      Going concern: 25%
```

### 6.3 Normalization

Each sub-model score must be normalized to 0-100 before weighting:

**Beneish M-Score normalization:**
```python
# M-Score ranges roughly from -3.5 (very safe) to +1.0 (very risky)
# Map to 0-100 where 100 = safest
integrity = max(0, min(100, ((-1 * m_score + 3.5) / 4.5) * 100))
```

**Dechow F-Score normalization:**
```python
# F-Score ranges from ~0.5 (safe) to ~3.0+ (very risky)
# Map to 0-100 where 100 = safest
integrity = max(0, min(100, ((3.0 - f_score) / 2.5) * 100))
```

**Montier C-Score normalization:**
```python
# C-Score ranges 0 (safe) to 6 (risky)
# Map to 0-100 where 100 = safest
integrity = max(0, min(100, ((6 - c_score) / 6) * 100))
```

**Sloan Ratio normalization:**
```python
# Sloan ranges roughly from -0.30 to +0.30
# Near zero is best. Further from zero is worse.
integrity = max(0, min(100, (1 - abs(sloan) / 0.30) * 100))
```

### 6.4 Zone Classification

| Score Range | Zone | D&O Underwriting Implication |
|-------------|------|------------------------------|
| 80-100 | HIGH INTEGRITY | Standard pricing, no financial forensics concern |
| 60-79 | ADEQUATE | Monitor trends, note any declining trajectory |
| 40-59 | CONCERNING | Elevated financial reporting risk, investigate specific signals |
| 20-39 | WEAK | Material financial integrity concerns, higher pricing / exclusions |
| 0-19 | CRITICAL | Likely manipulation indicators, potential decline or restrictive terms |

### 6.5 How Forensic Accountants Combine Signals

Based on research into forensic accounting practice, the best practitioners use a "convergence of evidence" approach:

1. **No single model is definitive.** A Beneish M-Score above -1.78 alone does not prove fraud. But Beneish above threshold + Dechow F-Score above 1.0 + declining QoE ratio + rising DSO = very high probability of reporting problems.

2. **Weight SEC-trained models more heavily.** The Dechow F-Score was trained on actual SEC enforcement actions. The Beneish M-Score was validated against known manipulators. These deserve more weight than purely academic constructs.

3. **Track trajectory, not just point-in-time.** A company whose Financial Integrity Score has dropped from 85 to 55 over 3 years is more concerning than a company that has been stable at 55 for years (the latter may have legitimate industry characteristics causing the score).

4. **Use qualitative signals as multipliers.** If the quantitative score is borderline (40-60) AND qualitative red flags are present (auditor change + CFO departure + insider selling), treat as if in the lower zone.

5. **Industry adjustment is essential.** Asset-light tech companies will naturally have different accrual profiles than capital-intensive manufacturers. The composite score should be compared to sector peers, not absolute thresholds alone.

---

## 7. Implementation Priorities

### Phase 1: Quick Wins (1-2 days)
High value, low effort, fully computable from existing data.

| # | Model | Effort | Value | Why First |
|---|-------|--------|-------|-----------|
| 1 | Montier C-Score | 1-2 hrs | HIGH | 6 binary checks, trivial to implement, highly intuitive for underwriters |
| 2 | Enhanced Sloan Ratio | 1 hr | MEDIUM | Already have basic version, just add graduated thresholds |
| 3 | Cash Flow Quality Enhancement | 2-3 hrs | HIGH | Build on existing earnings_quality.py, add CCE + AI + multi-period |

### Phase 2: Core Additions (2-3 days)
Major model additions that significantly improve forensic capability.

| # | Model | Effort | Value | Why Second |
|---|-------|--------|-------|------------|
| 4 | Dechow F-Score (Model 1) | 2-3 hrs | VERY HIGH | Most directly relevant to D&O -- trained on SEC enforcement data |
| 5 | Revenue Quality Score | 3-4 hrs | HIGH | Revenue manipulation is the most common fraud type in D&O claims |
| 6 | Lev-Thiagarajan (signals 1-8) | 2-3 hrs | MEDIUM-HIGH | 8 interpretable signals from XBRL data |

### Phase 3: Composite Integration (1-2 days)
Combine individual models into Financial Integrity Score.

| # | Task | Effort | Value |
|---|------|--------|-------|
| 7 | Normalization framework | 2-3 hrs | Normalize all model outputs to 0-100 |
| 8 | Financial Integrity Score | 3-4 hrs | Weighted composite with zone classification |
| 9 | Trajectory tracking | 2-3 hrs | Multi-period FIS with trend detection |

### Phase 4: Text-Based Enhancements (3-5 days)
Requires NLP on filing text, longer implementation but high value.

| # | Enhancement | Effort | Value |
|---|-------------|--------|-------|
| 10 | Audit Risk Score | 4-6 hrs | Extract MW, going concern, CAMs from auditor's report |
| 11 | Lev-Thiagarajan (signals 9-12) | 3-4 hrs | Order backlog, employee count, LIFO, audit opinion |
| 12 | Benford's Law Analysis | 3-4 hrs | Statistical analysis of all financial values |

### Phase 5: Advanced / Future
Lower priority or requires infrastructure not yet available.

| # | Enhancement | Notes |
|---|-------------|-------|
| 13 | FinBERT MD&A analysis | Requires ML model deployment; would analyze management tone |
| 14 | Modified Jones Model | Requires peer panel data infrastructure |
| 15 | Graph-based related party analysis | Requires entity resolution across filings |

---

## 8. Sample Computations

### Hypothetical Company: AcmeCorp (Ticker: ACME)

**Financial Data (in millions):**
```
                          Current Year    Prior Year
Revenue                   $5,000          $4,200
COGS                      $3,250          $2,730
Gross Profit              $1,750          $1,470
SGA Expense               $800            $700
Net Income                $420            $380
Operating Cash Flow       $280            $410
Depreciation              $150            $140
Accounts Receivable       $850            $630
Inventory                 $620            $480
Current Assets            $2,100          $1,800
PP&E (net)                $1,500          $1,400
Total Assets              $6,200          $5,500
Current Liabilities       $1,200          $1,100
Long-Term Debt            $1,800          $1,600
Total Liabilities         $3,000          $2,700
Cash & Equivalents        $300            $350
Shares Outstanding        $100M           $95M
Capital Expenditures      $250            $200
Dividends Paid            $80             $75
```

---

#### 8.1 Beneish M-Score Computation

```
DSRI = (850/5000) / (630/4200) = 0.170 / 0.150 = 1.133
GMI  = (1470/4200) / (1750/5000) = 0.350 / 0.350 = 1.000
AQI  = (1-(2100+1500)/6200) / (1-(1800+1400)/5500)
     = (1-0.5806) / (1-0.5818) = 0.4194 / 0.4182 = 1.003
SGI  = 5000/4200 = 1.190
DEPI = (140/(140+1400)) / (150/(150+1500)) = 0.0909 / 0.0909 = 1.000
SGAI = (800/5000) / (700/4200) = 0.160 / 0.1667 = 0.960
TATA = (420-280) / 6200 = 0.0226
LVGI = (3000/6200) / (2700/5500) = 0.4839 / 0.4909 = 0.986

M-Score = -4.84 + 0.920(1.133) + 0.528(1.000) + 0.404(1.003)
          + 0.892(1.190) + 0.115(1.000) - 0.172(0.960)
          + 4.679(0.0226) - 0.327(0.986)
        = -4.84 + 1.042 + 0.528 + 0.405 + 1.061 + 0.115
          - 0.165 + 0.106 - 0.322
        = -2.070

RESULT: M-Score = -2.07 -- GREY ZONE (between -2.22 and -1.78)
The high DSRI (1.133) is the primary concern -- receivables growing faster
than revenue, a classic channel stuffing indicator.
```

---

#### 8.2 Dechow F-Score Computation

```
Average TA = (6200 + 5500) / 2 = 5850

RSST_ACC (simplified): Change in NOA / Average TA
  NOA_t = (6200 - 300) - (3000) = 2900
  NOA_t-1 = (5500 - 350) - (2700) = 2450
  RSST_ACC = (2900 - 2450) / 5850 = 0.0769

CH_REC = (850 - 630) / 5850 = 0.0376

CH_INV = (620 - 480) / 5850 = 0.0239

SOFT_ASSETS = (6200 - 1500 - 300) / 6200 = 0.7097

CH_CS: Cash Sales = Revenue - Change in AR
  Cash Sales_t = 5000 - (850-630) = 4780
  Cash Sales_t-1 = 4200 (assume stable AR prior)
  CH_CS = (4780 - 4200) / 4200 = 0.1381

CH_ROA:
  ROA_t = 420/6200 = 0.0677
  ROA_t-1 = 380/5500 = 0.0691
  CH_ROA = 0.0677 - 0.0691 = -0.0014

ISSUE: AcmeCorp issued new shares (100M vs 95M) = 1

Predicted Value = -7.893 + 0.790(0.0769) + 2.518(0.0376)
                  + 1.191(0.0239) + 1.979(0.7097) + 0.171(0.1381)
                  - 0.932(-0.0014) + 1.029(1)
                = -7.893 + 0.061 + 0.095 + 0.028 + 1.404 + 0.024
                  + 0.001 + 1.029
                = -5.251

F-Score = e^(-5.251) / (1 + e^(-5.251))
        = 0.00527 / 1.00527
        = 0.00524

Normalized F-Score = 0.00524 / 0.0037 (unconditional probability) = 1.42

RESULT: F-Score = 1.42 -- ABOVE NORMAL RISK
The high soft assets ratio (0.71) and securities issuance are the
primary drivers. The receivables change also contributes.
```

---

#### 8.3 Montier C-Score Computation

```
Signal 1: NI > OCF gap widening?
  Gap_t = 420 - 280 = 140
  Gap_t-1 = 380 - 410 = -30
  Gap widened from -30 to +140. YES = 1

Signal 2: DSO increasing?
  DSO_t = (850/5000)*365 = 62.1 days
  DSO_t-1 = (630/4200)*365 = 54.8 days
  DSO increased from 54.8 to 62.1. YES = 1

Signal 3: Inventory days increasing?
  DSI_t = (620/3250)*365 = 69.6 days
  DSI_t-1 = (480/2730)*365 = 64.2 days
  DSI increased from 64.2 to 69.6. YES = 1

Signal 4: Other current assets / revenue increasing?
  Other CA_t = 2100 - 850 - 620 - 300 = 330 (CA - AR - Inv - Cash)
  Other CA_t-1 = 1800 - 630 - 480 - 350 = 340
  Ratio_t = 330/5000 = 0.066
  Ratio_t-1 = 340/4200 = 0.081
  Ratio decreased. NO = 0

Signal 5: Depreciation rate declining?
  DepRate_t = 150/1500 = 0.100
  DepRate_t-1 = 140/1400 = 0.100
  Rate unchanged. NO = 0

Signal 6: High total asset growth?
  TA growth = (6200-5500)/5500 = 12.7%
  Growth > 10% threshold. YES = 1

C-SCORE = 0 + 1 + 1 + 1 + 0 + 0 + 1 = 4

RESULT: C-Score = 4/6 -- HIGH MANIPULATION RISK
Three of four triggered signals (NI>OCF divergence, rising DSO,
rising inventory days) are classic manipulation indicators.
The asset growth signal adds concern about acquisition-driven distortion.
```

---

#### 8.4 Sloan Accrual Ratio Computation

```
Cash Flow Approach:
  Sloan Ratio = (NI - CFO) / Average TA
  = (420 - 280) / 5850
  = 0.0239 = 2.39%

Balance Sheet Approach:
  Sloan Ratio = (NI - CFO - CFI) / Average TA
  Assume CFI = -250 (capex)
  = (420 - 280 - (-250)) / 5850
  = 390 / 5850
  = 0.0667 = 6.67%

RESULT (Cash Flow): Sloan Ratio = 2.39% -- SAFE ZONE (-10% to +10%)
RESULT (Balance Sheet): Sloan Ratio = 6.67% -- SAFE ZONE but approaching warning

Despite being in the "safe zone," the ratio is positive and notably higher
than typical for established companies, suggesting accrual buildup.
```

---

#### 8.5 Cash Flow Quality Score Computation

```
a) QoE Ratio = CFO / NI = 280 / 420 = 0.667
   Status: BELOW 1.0 -- Lower quality earnings
   Normalized (0-100): 44 (mapping: <0.5=0, 0.5=25, 1.0=75, >1.5=100)

b) Cash Conversion = FCF / EBITDA
   FCF = 280 - 250 = 30
   EBITDA = 420 + 150 + (interest, assume 90) = 660
   CCE = 30 / 660 = 0.045
   Status: POOR (<0.20)
   Normalized: 11

c) Accruals Intensity = |NI - CFO| / Revenue
   = |420 - 280| / 5000 = 0.028
   Status: NORMAL (0.028 < 0.05)
   Normalized: 85

d) Cash Flow Adequacy = CFO / (CapEx + Dividends)
   = 280 / (250 + 80) = 0.848
   Status: BELOW 1.0 -- Cannot self-fund
   Normalized: 56

e) Multi-Period Divergence: Need quarterly data (not available in this example)
   Assume 1 quarter of NI>0, CFO<0 = NORMAL
   Normalized: 75

COMPOSITE:
  = 0.30*44 + 0.20*11 + 0.20*85 + 0.15*56 + 0.15*75
  = 13.2 + 2.2 + 17.0 + 8.4 + 11.25
  = 52.1

RESULT: Cash Flow Quality Score = 52/100 -- CONCERNING ZONE
Primary concerns: Very poor cash conversion (CCE=4.5%) and
QoE ratio below 1.0. Net income of $420M is supported by only
$280M in operating cash flow.
```

---

#### 8.6 Revenue Quality Score Computation

```
a) DSO Trend:
   DSO_t = 62.1 days
   DSO_t-1 = 54.8 days
   DSO Change = +7.3 days (+13.3%)
   Status: DETERIORATING (>10% increase)
   Normalized: 30

b) Revenue-Receivable Divergence:
   AR change = (850-630)/630 = 34.9%
   Revenue change = (5000-4200)/4200 = 19.0%
   Divergence = 34.9% - 19.0% = 15.9%
   Status: RED FLAG (>10%)
   Normalized: 15

c) Deferred Revenue: Not available in this example
   Normalized: 50 (neutral)

d) ADA Ratio: Not available in this example
   Normalized: 50 (neutral)

e) Q4 Concentration: Not available in this example
   Normalized: 50 (neutral)

COMPOSITE:
  = 0.25*30 + 0.25*15 + 0.20*50 + 0.15*50 + 0.15*50
  = 7.5 + 3.75 + 10.0 + 7.5 + 7.5
  = 36.25

RESULT: Revenue Quality Score = 36/100 -- WEAK ZONE
Major concern: Receivables growing 35% while revenue grows only 19%.
This 15.9% divergence is a classic channel stuffing indicator.
Combined with rising DSO, this demands underwriting investigation.
```

---

#### 8.7 Financial Integrity Score -- Composite

```
Manipulation Detection (30%):
  Beneish normalized: ((-1*-2.07 + 3.5)/4.5)*100 = ((2.07+3.5)/4.5)*100 = 123.8 -> capped at 100
    Wait -- M=-2.07 means safe-ish. Recalc:
    integrity = max(0, min(100, ((-1 * (-2.07)) + 3.5) / 4.5 * 100))
    = max(0, min(100, (2.07 + 3.5) / 4.5 * 100))  -- this is wrong direction
    Correct: Higher M = more manipulation = lower integrity
    integrity = max(0, min(100, ((3.5 - (-1*(-2.07))) / 4.5) * 100))
    = max(0, min(100, ((3.5 - 2.07) / 4.5) * 100))
    = max(0, min(100, (1.43/4.5)*100))
    = 31.8  -- Actually: M-Score of -2.07 is grey zone, so should be moderate
    Better normalization: Safest M ~ -3.5, Riskiest M ~ +1.0
    integrity = max(0, min(100, (m_score * -1 + 1.0) / 4.5 * 100))
              = max(0, min(100, (2.07 + 1.0) / 4.5 * 100))
              = max(0, min(100, 68.2))
              = 68.2

  Dechow normalized: F-Score = 1.42
    integrity = max(0, min(100, ((3.0 - 1.42) / 2.5) * 100))
              = max(0, min(100, 63.2))
              = 63.2

  Montier normalized: C-Score = 4
    integrity = ((6-4)/6)*100 = 33.3

  Manipulation sub-score = 0.40*68.2 + 0.35*63.2 + 0.25*33.3
                         = 27.3 + 22.1 + 8.3 = 57.7

Accrual Quality (20%):
  Sloan normalized: abs ratio 2.39% -> (1 - 0.0239/0.30)*100 = 92.0
  Accruals Intensity normalized: 85 (from above)
  Multi-period: 75 (from above)
  Sub-score = 0.50*92 + 0.30*85 + 0.20*75 = 46 + 25.5 + 15 = 86.5

Revenue Quality (20%): 36.25 (computed above)

Cash Flow Quality (15%): 52.1 (computed above)

Audit Risk (15%): Assume no audit issues = 85

FINANCIAL INTEGRITY SCORE:
  = 0.30*57.7 + 0.20*86.5 + 0.20*36.25 + 0.15*52.1 + 0.15*85
  = 17.3 + 17.3 + 7.25 + 7.8 + 12.75
  = 62.4

RESULT: Financial Integrity Score = 62/100 -- ADEQUATE ZONE

UNDERWRITER INTERPRETATION:
"AcmeCorp shows adequate overall financial integrity (62/100) but
with specific areas of concern:
- Revenue quality is WEAK (36/100) due to receivables growing
  significantly faster than revenue (+35% vs +19%)
- Cash flow quality is CONCERNING (52/100) with poor cash conversion
  and QoE ratio below 1.0
- Manipulation detection models show mixed signals: Beneish grey zone,
  Dechow above-normal risk, and Montier C-Score at 4/6 (high)
- The strongest positive: accrual quality metrics are still reasonable
  (Sloan ratio in safe zone)

RECOMMENDATION: Investigate revenue recognition practices.
Request explanation for receivable buildup. Consider pricing
adjustment for elevated financial reporting risk."
```

---

## 9. Emerging / Advanced Models (For Future Reference)

### 9.1 Machine Learning Approaches

**Key features used in ML fraud detection (from literature review):**
- All features from Beneish, Dechow, and traditional models (baseline)
- Ratio changes over multiple periods (3-year trends, not just YoY)
- Industry-relative metrics (company ratio vs. industry median)
- Text features from MD&A (word counts, sentiment, readability)
- Interaction terms (e.g., high growth * high accruals)

**Best-performing ML models (2024-2025 research):**
- Ensemble methods (Random Forest, AdaBoost, XGBoost) consistently outperform logistic regression
- AdaBoost shows strongest overall predictive capability
- Key challenge: extreme class imbalance (fraudulent cases are <1% of observations)
- SMOTE and other oversampling techniques improve recall but may increase false positives

**Explainability:** SHAP and LIME are increasingly integrated to explain ML model predictions, which is critical for underwriting where decisions must be justifiable.

### 9.2 NLP / FinBERT Approaches

**FinBERT (Prosus AI):**
- BERT model fine-tuned on 4.9 billion tokens of financial text
- Pre-trained on: SEC filings (10-K, 10-Q), analyst reports, earnings call transcripts
- Significantly outperforms Loughran-McDonald dictionary for financial sentiment
- Can detect positive/negative sentiment in context where dictionary approaches fail

**Key NLP findings for fraud detection:**
- Fraudulent firms use MORE positive words (deliberately concealing)
- Use more "activation" language and imagery
- Lower lexical diversity (repetitive defensive language)
- Write more text overall (appearing credible while communicating less substance)
- SVM classifier on top 200 fraud-linked words can identify fraudulent MD&A sections

**Practical approach for D&O:**
- Use FinBERT to score MD&A sections for sentiment trends across quarters
- Compare CEO vs CFO language divergence
- Track hedging/uncertainty word frequency changes
- This aligns with our existing `SentimentProfile` model in governance_forensics.py

### 9.3 Graph-Based Anomaly Detection

**Concept:** Build networks of related parties, shared board members, and transaction flows. Anomalous patterns in the graph (circular transactions, complex multi-entity structures, unusual centrality) may indicate fraud.

**Application to D&O:**
- Map board interlocks and executive shared histories
- Identify related party transaction networks
- Detect shell company patterns in VIE/SPE structures
- Our system already tracks board interlocks and related party transactions in governance models

**Implementation feasibility:** LOW for near-term. Requires entity resolution across multiple filings and a graph database. Better as a Phase 5+ enhancement.

---

## 10. Key Sources

- Beneish, M.D. (1999). "The Detection of Earnings Manipulation." Financial Analysts Journal.
- Beneish, M.D., Lee, C.M., & Nichols, D.C. (2020). "The Cost of Fraud Prediction Errors."
- Dechow, P.M., Ge, W., Larson, C.R., & Sloan, R.G. (2011). "Predicting Material Accounting Misstatements." Contemporary Accounting Research.
- Sloan, R.G. (1996). "Do Stock Prices Fully Reflect Information in Accruals and Cash Flows about Future Earnings?" The Accounting Review.
- Jones, J.J. (1991). "Earnings Management During Import Relief Investigations." Journal of Accounting Research.
- Dechow, P.M., Sloan, R.G., & Sweeney, A.P. (1995). "Detecting Earnings Management." The Accounting Review.
- Montier, J. (2008). "Cooking the Books, or, More Sailing Under the Black Flag." Societe Generale Research.
- Lev, B. & Thiagarajan, S.R. (1993). "Fundamental Information Analysis." Journal of Accounting Research.
- Nigrini, M.J. (2012). "Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection." Wiley.
- Huang, A., Wang, H., & Yang, Y. (2023). "FinBERT: A Large Language Model for Extracting Information from Financial Text." Contemporary Accounting Research.

---

## 11. Relationship to Existing System

### Already Implemented
| Model | Location | Status |
|-------|----------|--------|
| Altman Z-Score (original + Z'') | `distress_models.py` + `distress_formulas.py` | Complete with trajectory |
| Beneish M-Score (8-var) | `distress_formulas.py` lines 94-221 | Complete |
| Ohlson O-Score | `distress_formulas.py` lines 229-322 | Complete |
| Piotroski F-Score (9 criteria) | `distress_formulas.py` lines 330-499 | Complete |
| Basic accruals ratio | `earnings_quality.py` line 109-120 | Basic version |
| OCF/NI ratio | `earnings_quality.py` line 123-134 | Basic version |
| DSO current + prior | `earnings_quality.py` line 137-144 | Basic version |
| Asset quality delta | `earnings_quality.py` line 147-174 | Basic version |
| Cash flow adequacy | `earnings_quality.py` line 177-192 | Basic version |
| Quality score aggregate | `earnings_quality.py` line 200-242 | Basic (0-3 flag count) |

### Gaps to Fill
| Priority | Model | Effort | Where to Add |
|----------|-------|--------|-------------|
| P1 | Montier C-Score | 1-2 hrs | New function in distress_formulas.py or new file |
| P1 | Cash Flow Quality (enhanced) | 2-3 hrs | Extend earnings_quality.py |
| P2 | Dechow F-Score | 2-3 hrs | New function in distress_formulas.py |
| P2 | Revenue Quality Score | 3-4 hrs | New file or extend earnings_quality.py |
| P2 | Lev-Thiagarajan (signals 1-8) | 2-3 hrs | New file (lev_thiagarajan.py) |
| P2 | Enhanced Sloan Ratio | 1 hr | Enhance in earnings_quality.py |
| P3 | Financial Integrity Score | 3-4 hrs | New composite in score/ stage |
| P3 | Benford's Law | 3-4 hrs | New file (benford_analysis.py) |
| P4 | Audit Risk Score | 4-6 hrs | Requires text extraction pipeline |
| P5 | FinBERT analysis | Days | Requires ML model infrastructure |
