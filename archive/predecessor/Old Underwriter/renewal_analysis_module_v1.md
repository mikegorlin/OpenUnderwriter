# D&O RENEWAL ANALYSIS MODULE
## Version 1.0 - Delta-Based Renewal Evaluation
## Effective: January 2026

---

## PURPOSE

This module provides a streamlined workflow for **clean renewals** - policies expiring without claims or reported circumstances. It focuses on **what changed** since the prior binding decision rather than full re-underwriting.

**Entry Point**: TRI-003 from Project Instructions (clean renewal routing)

**Exit Points**:
- REN-010: Renewal recommendation with pricing guidance
- COR-001: Corridor to full analysis (if material changes found)

---

## WHEN TO USE THIS MODULE

| Condition | Use This Module? |
|-----------|-----------------|
| Renewal + No claims + No circumstances | YES |
| Renewal + Claims exist | NO - Full analysis |
| Renewal + Circumstances reported | NO - Full analysis |
| New business | NO - Full analysis |

---

## SECTION 1: RENEWAL QUICK SCREEN (RQS-001 to RQS-020)

### Purpose
Identify policy-period events that require deeper review or corridor to full analysis.

### Execution
**Scan for events during the policy period (last 12 months):**

| Check ID | Event | Red Flag If | Source |
|----------|-------|-------------|--------|
| RQS-001 | Securities class action filed | Any filing | Stanford SCAC |
| RQS-002 | SEC enforcement action | Any action | SEC.gov |
| RQS-003 | DOJ investigation disclosed | Any disclosure | 8-K/10-K/News |
| RQS-004 | Restatement announced | Any restatement | 8-K Item 4.02 |
| RQS-005 | Going concern opinion | Opinion issued | 10-K audit report |
| RQS-006 | Wells Notice received | Any notice | 8-K/10-K |
| RQS-007 | Short seller report published | Any report less than 6mo | Web search |
| RQS-008 | Material weakness disclosed | New or unremediated | 10-K Item 9A |
| RQS-009 | CEO departure | Within policy period | 8-K Item 5.02 |
| RQS-010 | CFO departure | Within policy period | 8-K Item 5.02 |
| RQS-011 | Auditor change | Within policy period | 8-K Item 4.01 |
| RQS-012 | Stock decline greater than 50% | From policy inception | Stock data |
| RQS-013 | Guidance withdrawn | During policy period | 8-K/Earnings |
| RQS-014 | Major M&A announced | Greater than 25% market cap | 8-K |
| RQS-015 | Dividend suspended/cut | During policy period | 8-K/News |
| RQS-016 | Credit downgrade | During policy period | Rating agency |
| RQS-017 | Covenant violation | During policy period | 10-Q/10-K |
| RQS-018 | Mass layoffs (greater than 10%) | During policy period | 8-K/WARN/News |
| RQS-019 | Activist campaign launched | During policy period | 13D/News |
| RQS-020 | Regulatory action | Material action | Agency websites |

### Routing Logic

| Result | Action |
|--------|--------|
| 0 Red Flags | Continue to Section 2 |
| 1-2 Red Flags | Flag for elevated review, continue analysis |
| 3+ Red Flags | COR-001 Corridor to full analysis |
| Nuclear Event (RQS-001 to RQS-006) | COR-001 Corridor to full analysis |

---

## SECTION 2: STOCK PERFORMANCE DELTA (REN-002)

### Purpose
Evaluate stock performance changes from policy inception to current.

### Metrics to Capture

| Metric | At Binding (Prior) | Current | Delta | Direction |
|--------|-------------------|---------|-------|-----------|
| Stock Price | $X | $Y | +/-X% | Up/Down |
| 52-Week High | $X | $Y | +/-X% | Up/Down |
| 52-Week Low | $X | $Y | +/-X% | Up/Down |
| Market Cap | $XB | $YB | +/-X% | Up/Down |
| Decline from High | X% | Y% | +/- pts | Up/Down |
| Beta | X | Y | +/-X | Up/Down |

### Scoring Impact

| Delta | Impact |
|-------|--------|
| Stock +20% or more | Positive factor (potential credit) |
| Stock +/- 20% | Neutral |
| Stock -20% to -40% | Caution flag |
| Stock -40% to -60% | Material deterioration (flag) |
| Stock greater than -60% | COR-001 Corridor |

### Event-Window Analysis (if decline greater than 20%)
If stock declined more than 20% during policy period:
1. Identify date(s) of major drops (greater than 5% single day)
2. Identify catalyst for each drop
3. Calculate sector-adjusted decline
4. Assess scienter indicators (insider selling before drops)

---

## SECTION 3: FINANCIAL HEALTH DELTA (REN-003)

### Purpose
Compare key financial metrics YoY to identify improving or deteriorating trends.

### Metrics to Capture

| Metric | Prior FY | Current FY/TTM | Delta | Direction |
|--------|----------|----------------|-------|-----------|
| Revenue | $X | $Y | +/-X% | Up/Down |
| Gross Margin | X% | Y% | +/- pts | Up/Down |
| Operating Income | $X | $Y | +/-X% | Up/Down |
| Net Income | $X | $Y | +/-X% | Up/Down |
| EPS (GAAP) | $X | $Y | +/-X% | Up/Down |
| EPS (Adjusted) | $X | $Y | +/-X% | Up/Down |
| Operating Cash Flow | $X | $Y | +/-X% | Up/Down |
| Free Cash Flow | $X | $Y | +/-X% | Up/Down |
| Total Debt | $X | $Y | +/-X% | Up/Down |
| Cash and Equivalents | $X | $Y | +/-X% | Up/Down |
| Debt/EBITDA | Xx | Yx | +/-X | Up/Down |
| Interest Coverage | Xx | Yx | +/-X | Up/Down |

### Scoring Impact

| Category | Improved | Stable | Deteriorated |
|----------|----------|--------|--------------|
| Revenue | +5%+ | +/-5% | -5%+ |
| Profitability | +10%+ | +/-10% | -10%+ |
| Cash Flow | Positive growth | Stable | Negative trend |
| Leverage | Decreasing | Stable | Increasing greater than 25% |

---

## SECTION 4: LITIGATION AND REGULATORY STATUS (REN-004)

### Purpose
Verify no new litigation or regulatory matters since binding.

### Checks Required

| Check | Source | Finding |
|-------|--------|---------|
| Active securities class action | Stanford SCAC | Yes/No |
| SEC enforcement activity | SEC.gov/EDGAR | Yes/No |
| DOJ investigation | 8-K/10-K/News | Yes/No |
| State AG actions | News search | Yes/No |
| Derivative suits filed | PACER/News | Yes/No |
| Regulatory consent orders | Agency websites | Yes/No |
| Books and records demands | 8-K/News | Yes/No |

### Prior Litigation Review
If company had prior securities litigation at binding:
- Current status of that litigation
- Settlement amount (if resolved)
- Appeal status
- Insurance exhaustion status

---

## SECTION 4A: CLAIMS PROTOCOL (NEW)

### Purpose
Document claims confirmation process and handling of any disclosed matters.

### Pre-Claims Question Litigation Scan (TRI-001a/b)

**Before asking about claims, always run:**

| Search | Result | Source | Date |
|--------|--------|--------|------|
| Stanford SCAC search | Finding/None | Stanford SCAC | Date |
| Web search for securities lawsuit | Finding/None | Web | Date |

### Claims Confirmation Script

**Present findings, then ask:**
"I found [findings / no active securities litigation]. [Prior matter details if any].
Are there any claims or reported circumstances under the expiring policy I should know about?"

### Why Ask Even If Scan Is Clean

| Reason | Example |
|--------|---------|
| Derivative demands | Pre-suit demand letters not yet public |
| SEC subpoenas | Investigation not yet disclosed |
| Shareholder letters | 220 demands, investigation threats |
| Circumstances reported | Precautionary notices to carrier |
| Late notice situations | Claims reported after policy period |

### Response Handling

| User Response | Action |
|---------------|--------|
| No claims | Document confirmation, continue REN workflow |
| Claims disclosed | COR-001 Corridor to full analysis |
| Not sure | Clarify with broker, do not proceed without answer |

---

## SECTION 5: GOVERNANCE AND MANAGEMENT DELTA (REN-005)

### Purpose
Identify management changes and governance developments.

### Checks Required

| Position | At Binding | Current | Change? |
|----------|-----------|---------|---------|
| CEO | Name, tenure | Name, tenure | Yes/No |
| CFO | Name, tenure | Name, tenure | Yes/No |
| General Counsel | Name, tenure | Name, tenure | Yes/No |
| Board Chair | Name | Name | Yes/No |
| Audit Committee Chair | Name | Name | Yes/No |
| Lead Independent Director | Name | Name | Yes/No |

### Executive Departure Analysis (if changes found)

For each departure:
- Reason given (resignation, retirement, termination)
- Timing relative to any stock decline
- Severance arrangements
- Non-compete/cooperation provisions
- Public statements

### Scoring Impact

| Change | Impact |
|--------|--------|
| No changes | Neutral (stability positive) |
| Planned succession | Neutral to slight positive |
| Unexpected CEO departure | Material flag (+2-3 pts) |
| Unexpected CFO departure | Material flag (+2-3 pts) |
| Both CEO+CFO departed | COR-001 Corridor |

---

## SECTION 6: MARKET SIGNALS DELTA (REN-006)

### Purpose
Compare market risk indicators to prior binding.

### Metrics to Capture

| Metric | At Binding | Current | Delta | Flag? |
|--------|-----------|---------|-------|-------|
| Short Interest (% float) | X% | Y% | +/-X% | Yes/No |
| Days to Cover | X | Y | +/-X | Yes/No |
| Institutional Ownership | X% | Y% | +/-X% | Yes/No |
| Analyst Consensus | Rating | Rating | Change | Yes/No |
| Price Targets (median) | $X | $Y | +/-X% | Yes/No |

### Short Seller Report Check
- Any short seller report published during policy period?
- If yes: Report date, author, allegations, stock reaction
- Company response (if any)

### Scoring Impact

| Indicator | Improved | Neutral | Deteriorated |
|-----------|----------|---------|--------------|
| Short Interest | Down greater than 25% | +/-25% | Up greater than 50% |
| Institutional | Up or stable | Stable | Down greater than 10% |
| Analyst Consensus | Upgrades | Stable | Downgrades |

---

## SECTION 7: RISK INDICATOR DELTA (REN-007)

### Purpose
Capture any change in key risk flags monitored at binding.

### Indicators to Track

| Indicator | At Binding | Current | Change |
|-----------|-----------|---------|--------|
| Insider Selling (6mo net) | $XM | $YM | +/- |
| Form 4 Activity Pattern | Normal/Elevated | Normal/Elevated | Same/Changed |
| 10b5-1 Plan Status | Active/None | Active/None | Same/Changed |
| Guidance Practice | Provides/None | Provides/None | Same/Changed |
| Earnings Surprises | X of Y positive | X of Y positive | Better/Worse |
| Customer Concentration | X% top customer | Y% top customer | +/- |

### Insider Trading Deep Dive (if material selling)

If net insider selling greater than $5M or greater than 1% of market cap:
- Identify sellers (CEO, CFO, directors, 10% holders)
- Calculate as % of holdings sold
- Check timing relative to any announcements
- Verify 10b5-1 plan coverage

---

## SECTION 8: PROSPECTIVE TRIGGERS (REN-008)

### Purpose
Identify upcoming events that could generate claims in the next policy period.

### Forward-Looking Event Calendar

| Event | Expected Date | Litigation Risk | Notes |
|-------|---------------|-----------------|-------|
| Earnings release | Dates | Low/Med/High | Any guidance? |
| FDA decision | Date if applicable | Low/Med/High | Drug/Device |
| Major contract renewal | Date if known | Low/Med/High | Customer |
| Debt maturity | Date | Low/Med/High | Amount |
| Executive transition | Date if planned | Low/Med/High | Who |
| M&A closing | Date if announced | Low/Med/High | Deal |
| Regulatory decision | Date if pending | Low/Med/High | Matter |

### Binary Event Assessment (Biotech/Pharma)

If applicable:
- Clinical trial readouts scheduled
- FDA action dates (PDUFA, etc.)
- Patent expirations
- Competitive threats

---

## SECTION 9: DELTA SCORING SUMMARY (REN-009)

### Purpose
Aggregate delta findings into an overall risk trajectory assessment.

### Delta Score Matrix

| Category | Score (0-5) | Direction | Key Finding |
|----------|-------------|-----------|-------------|
| Stock Performance | X | Up/Down/Flat | Summary |
| Financial Health | X | Up/Down/Flat | Summary |
| Litigation Status | X | Up/Down/Flat | Summary |
| Governance | X | Up/Down/Flat | Summary |
| Market Signals | X | Up/Down/Flat | Summary |
| Risk Indicators | X | Up/Down/Flat | Summary |
| Prospective Triggers | X | Up/Down/Flat | Summary |
| Claims Protocol | X | Up/Down/Flat | Summary |
| **TOTAL DELTA** | **X/40** | **Direction** | |

### Delta Scoring Guide

| Score | Meaning |
|-------|---------|
| 0 | Improved or no concerns |
| 1-2 | Slight deterioration, monitor |
| 3-4 | Moderate deterioration, flag |
| 5 | Significant deterioration |

### Overall Trajectory Interpretation

| Total Delta | Trajectory | Pricing Implication |
|-------------|------------|---------------------|
| 0-5 | Stable/Improving | Flat to credit |
| 6-15 | Moderate Deterioration | Flat to +5-10% |
| 16-25 | Significant Deterioration | +10-25% |
| 26-35 | Severe Deterioration | +25%+ or COR-001 |
| 36-40 | Critical | COR-001 Full Analysis |

---

## SECTION 10: RENEWAL RECOMMENDATION (REN-010)

### Purpose
Provide bindability recommendation with pricing guidance.

### Recommendation Framework

| Trajectory | Risk Score | Recommendation | Pricing Guidance |
|------------|------------|----------------|------------------|
| Improving | 0-14 | RENEW | Flat to -5% credit |
| Stable | 0-14 | RENEW | Flat |
| Mod. Deterioration | 15-29 | RENEW W/CAUTION | +5-15% |
| Sig. Deterioration | 30-49 | ESCALATE | +15-25% or conditions |
| Severe | 50+ | ESCALATE | Re-underwrite or decline |

### Conditions to Consider

| Condition | When to Apply |
|-----------|---------------|
| Higher retention | Financial deterioration, leverage concerns |
| Co-insurance | Market signal deterioration |
| Prospective-only | Prior acts concerns |
| Sublimits | Specific exposure concerns |
| Exclusions | Identified risk concentrations |

### Output Format

**Summary Table:**
- Company: Name (NYSE: TICKER)
- Expiring Policy: Period
- Claims Status: Clean
- Delta Score: X/40
- Risk Tier: MINIMAL/BELOW AVG/AVERAGE/HIGH/EXTREME
- Trajectory: Improving/Stable/Deteriorating

**Recommendation:**
- ACTION: RENEW / RENEW WITH CONDITIONS / ESCALATE / DECLINE
- PRICING: Flat / +X% / -X% credit
- TERMS: As expiring / Modifications
- CONDITIONS (if any)

**Rationale:**
2-3 sentences explaining the recommendation based on delta findings

**Key Positives:**
- Positive 1
- Positive 2

**Watch Items:**
- Watch item 1
- Watch item 2

---

## COR-001: CORRIDOR TO FULL ANALYSIS

### Trigger Conditions

| Trigger | From Section |
|---------|--------------|
| Nuclear event during policy period | RQS-001 to RQS-006 |
| 3+ red flags in Renewal Quick Screen | RQS |
| Stock decline greater than 60% | REN-002 |
| Both CEO and CFO departed | REN-005 |
| Claims or circumstances disclosed | REN-004A |
| Delta score greater than 35 | REN-009 |
| Analyst judgment | Any section |

### Corridor Process

When COR-001 triggered:
1. Document the trigger condition
2. Note findings collected so far (do not discard)
3. Route to full analysis workflow (TRI-002)
4. Carry forward delta data as starting context

---

## RULE INDEX - RENEWAL MODULE

| Rule ID | Rule Name | Location | Description |
|---------|-----------|----------|-------------|
| REN-001 | Renewal Module Entry | renewal_analysis_module | Entry point from TRI-003 |
| RQS-001 | SCA During Policy | Section 1 | Securities class action filed |
| RQS-002 | SEC Action During Policy | Section 1 | SEC enforcement action |
| RQS-003 | DOJ Investigation | Section 1 | DOJ investigation disclosed |
| RQS-004 | Restatement | Section 1 | Restatement announced |
| RQS-005 | Going Concern | Section 1 | Going concern opinion issued |
| RQS-006 | Wells Notice | Section 1 | Wells Notice received |
| RQS-007 | Short Seller Report | Section 1 | Report published within 6mo |
| RQS-008 | Material Weakness | Section 1 | New or unremediated MW |
| RQS-009 | CEO Departure | Section 1 | CEO left during policy |
| RQS-010 | CFO Departure | Section 1 | CFO left during policy |
| RQS-011 | Auditor Change | Section 1 | Auditor changed during policy |
| RQS-012 | Stock Decline 50%+ | Section 1 | Major stock decline |
| RQS-013 | Guidance Withdrawn | Section 1 | Guidance pulled |
| RQS-014 | Major M&A | Section 1 | Deal greater than 25% mkt cap |
| RQS-015 | Dividend Cut | Section 1 | Dividend suspended/reduced |
| RQS-016 | Credit Downgrade | Section 1 | Rating agency downgrade |
| RQS-017 | Covenant Violation | Section 1 | Debt covenant breach |
| RQS-018 | Mass Layoffs | Section 1 | Workforce reduction 10%+ |
| RQS-019 | Activist Campaign | Section 1 | 13D filing or proxy fight |
| RQS-020 | Regulatory Action | Section 1 | Material regulatory action |
| REN-002 | Stock Delta | Section 2 | Stock performance comparison |
| REN-003 | Financial Delta | Section 3 | Financial metrics comparison |
| REN-004 | Litigation Status | Section 4 | Current litigation review |
| REN-004A | Claims Protocol | Section 4A | Claims confirmation process |
| REN-005 | Governance Delta | Section 5 | Management changes |
| REN-006 | Market Signals | Section 6 | Market indicator comparison |
| REN-007 | Risk Indicators | Section 7 | Risk flag tracking |
| REN-008 | Prospective Triggers | Section 8 | Forward-looking events |
| REN-009 | Delta Summary | Section 9 | Aggregate scoring |
| REN-010 | Recommendation | Section 10 | Final recommendation |
| COR-001 | Corridor Trigger | Corridor | Route to full analysis |

---

## TOTAL RENEWAL MODULE CHECKS: 67

| Section | Check Count |
|---------|-------------|
| Section 1: Renewal Quick Screen | 20 |
| Section 2: Stock Delta | 6 |
| Section 3: Financial Delta | 12 |
| Section 4: Litigation Status | 7 |
| Section 4A: Claims Protocol | 5 |
| Section 5: Governance Delta | 6 |
| Section 6: Market Signals | 5 |
| Section 7: Risk Indicators | 6 |
| Section 8: Prospective Triggers | 0 (variable) |
| Section 9: Delta Summary | 0 (aggregation) |
| Section 10: Recommendation | 0 (output) |
| **TOTAL** | **67** |

---

**END OF RENEWAL ANALYSIS MODULE v1.0**
