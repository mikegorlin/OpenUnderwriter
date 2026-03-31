# SCORING MODULE
## 10-Factor Empirically-Calibrated Risk Scoring

---

## EMPIRICAL FOUNDATION

### Base Litigation Rates (2024 Data)

| Metric | Value | Source |
|--------|-------|--------|
| Annual litigation rate (all public) | 4.19% | NERA 2024 |
| S&P 500 litigation rate | 6.1% | Cornerstone 2024 |
| **18-month litigation rate** | **~6%** | NERA annualized |
| IPO <3 years litigation rate | ~16% of filings | Cornerstone H1 2024 |
| Motion to dismiss granted | 61% | NERA 2024 |
| Cases reaching settlement | ~45% of filed | Cornerstone |
| Median settlement (2024) | $14M | Cornerstone 2024 |
| Average settlement (2024) | $42.4M | Cornerstone 2024 |

**Key Insight**: The question isn't "will they be sued?" but "are they MORE likely than average to be sued?"

---

## FACTOR WEIGHTS (Total 100 pts)

| Factor | Max Pts | Weight % | Rationale |
|--------|---------|----------|-----------|
| F.1 Prior Litigation | **20** | 20% | HIGHEST - prior defendants 3-5x more likely |
| F.2 Stock Decline | **15** | 15% | HIGH - primary trigger for securities suits |
| F.3 Restatement/Audit | **12** | 12% | HIGH - 70-80% litigation correlation |
| F.4 IPO/SPAC/M&A | **10** | 10% | Elevated windows for litigation |
| F.5 Guidance Misses | **8** | 8% | Creates corrective disclosure scenarios |
| F.6 Short Interest | **8** | 8% | Indicates market skepticism |
| F.7 Insider Trading | **8** | 8% | Heavy selling before drops is red flag |
| F.8 Volatility | **7** | 7% | Higher vol = higher drop probability |
| F.9 Financial Distress | **6** | 6% | Lower direct correlation |
| F.10 Governance | **3** | 3% | LOWEST - doesn't directly cause suits |
| **TOTAL** | **100** | 100% | |

---

## RISK TIERS

| Rule ID | Score | Tier | 18-Mo Probability | Base Rate Multiple | Underwriting Posture |
|---------|-------|------|-------------------|-------------------|---------------------|
| TR-001 | 70-100 | ðŸ”´ðŸ”´ðŸ”´ **EXTREME** | >20% (1 in 5) | >3x | Decline or 2-3x rate |
| TR-002 | 50-69 | ðŸ”´ðŸ”´ **HIGH** | 10-20% (1 in 5-10) | 2-3x | 1.5-2x rate, higher retention |
| TR-003 | 30-49 | âš ï¸ **AVERAGE** | 5-10% (1 in 10-20) | ~1-2x | Market rate |
| TR-004 | 15-29 | âœ… **BELOW AVG** | 2-5% (1 in 20-50) | <1x | Discount available |
| TR-005 | 0-14 | âœ…âœ… **MINIMAL** | <2% (1 in 50+) | Well below | Best rates |

**TR-006**: Never claim >25% probability. Even extreme cases rarely exceed 20-25%.

---

## NUCLEAR TRIGGERS

Check BEFORE calculating factor scores. If triggered, score cannot fall below minimum:

| Rule ID | Trigger | Min Tier | Min Score | Source Check |
|---------|---------|----------|-----------|--------------|
| NT-001 | Active securities class action | EXTREME | 70 | Stanford SCAC |
| NT-002 | Wells Notice disclosed | EXTREME | 70 | 10-K, 8-K |
| NT-003 | DOJ criminal investigation | EXTREME | 70 | DOJ.gov, 10-K |
| NT-004 | Going concern opinion | HIGH | 50 | 10-K auditor report |
| NT-005 | Restatement <12 months | HIGH | 50 | 8-K Item 4.02 |
| NT-006 | SPAC <18mo + stock <$5 | HIGH | 50 | Filing dates, price |
| NT-007 | Short seller report <6 months | HIGH | 50 | Activist short websites |
| NT-008 | Stock decline >60% company-specific | HIGH | 50 | Yahoo Finance + attribution |

---

## F.1: PRIOR LITIGATION SCORE (0-20 pts) â­ HIGHEST WEIGHT

### Scoring Table

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F1-001 | Active securities class action | 20 + **NT-001** |
| F1-002 | Securities suit settled <3 years | 18 |
| F1-003 | Securities suit settled 3-5 years | 15 |
| F1-004 | Securities suit settled 5-10 years | 10 |
| F1-005 | SEC enforcement action <5 years | 12 |
| F1-006 | Derivative suit <5 years | 6 |
| F1-007 | No prior litigation | 0 |

### Calculation Rules
- Use **highest applicable** single condition
- If multiple conditions, take highest (do NOT add)
- Active litigation = automatic NUCLEAR trigger

### Source Verification
1. Stanford SCAC: Search ticker AND company name
2. SEC.gov Litigation Releases: Search company name
3. 10-K Legal Proceedings section
4. PACER federal court search

### Calculation Example
```
Company: XYZ Corp
Stanford SCAC search: 1 case found
- Case: In re XYZ Corp Securities Litigation
- Class Period: May 2020 - Aug 2021
- Settlement: $12.5M (March 2023)
- Time since: 2 years 8 months â†’ <3 years bracket

SEC.gov search: No enforcement actions found

F.1 Score = 18/20 points (settled <3 years)
```

---

## F.2: STOCK DECLINE SCORE (0-15 pts) â­ HIGH WEIGHT

### Base Score Table

| Rule ID | Decline from 52-Week High | Base Points |
|---------|---------------------------|-------------|
| F2-001 | >60% | 15 |
| F2-002 | 50-60% | 12 |
| F2-003 | 40-50% | 9 |
| F2-004 | 30-40% | 6 |
| F2-005 | 20-30% | 3 |
| F2-006 | <20% | 0 |

### Bonuses
| Rule ID | Condition | Points |
|---------|-----------|--------|
| F2-007 | Company underperformed sector by >20 ppts | +3 (max 15 total) |
| F2-008 | Event-window >20% sector-adjusted (10-day) | +2, flag for review |

### Calculation Steps

**Step 1: Calculate Decline**
```
Decline = (52-week high - Current price) / 52-week high Ã— 100
```

**Step 2: Attribution (if decline >10%)**
```
Company-specific = Company return - Sector ETF return
```

**Step 3: Apply Scoring**
```
Base points (from table) + Company-specific bonus (if applicable)
Cap at 15 points maximum
```

### Sector ETF Reference

| Industry | Primary ETF |
|----------|-------------|
| Technology | XLK |
| Healthcare | XLV |
| Financials | XLF |
| Industrials | XLI |
| Energy | XLE |
| Consumer Discretionary | XLY |
| Consumer Staples | XLP |
| Materials | XLB |
| Utilities | XLU |
| Real Estate | XLRE |
| Communications | XLC |
| BDCs | BIZD |
| Biotech | XBI |

### Calculation Example
```
Company: ABC Inc (Technology)
Current price: $45.00
52-week high: $95.00
Decline: ($95 - $45) / $95 = 52.6% â†’ Base: 12 pts

Attribution:
- ABC 12-month return: -48%
- XLK 12-month return: +18%
- Company-specific: -48% - (+18%) = -66 percentage points
- Exceeds 20% threshold â†’ +3 bonus

F.2 Score = 12 + 3 = 15/15 points (capped)
```

### â›” MANDATORY DATA VALIDATION (F.2)

**Before calculating F.2, verify:**

| Check | Rule | Action if Fails |
|-------|------|-----------------|
| High â‰¥ Current | 52-week high must be â‰¥ current price | Re-fetch from Yahoo Finance |
| Current â‰¥ Low | Current price must be â‰¥ 52-week low | Re-fetch from Yahoo Finance |
| Decline â‰¤ 100% | Calculated decline cannot exceed 100% | Math error - recalculate |
| Decline â‰¥ 0% | Calculated decline cannot be negative | High/Current swapped - fix |
| Same Source | High, Low, Current all from same source | Use single Yahoo Finance pull |
| Fresh Data | Data pulled within last 24 hours | Note date in citation |

**Validation Template (include in output):**
```
F.2 Data Validation:
- 52-week high: $X [Source: Yahoo Finance, DATE]
- 52-week low: $X
- Current price: $X
- Validation: High ($X) â‰¥ Current ($X) â‰¥ Low ($X)? âœ“/âœ—
- Decline calculation: ($X - $X) / $X = X% âœ“/âœ—
```

**Common Errors to Catch:**
1. **Stale data**: Yahoo Finance showing yesterday's close vs. real-time
2. **Wrong ticker**: Similar tickers (e.g., META vs MELI)
3. **Split-adjusted**: 52-week high not adjusted for recent split
4. **Currency**: ADR prices vs. local market prices

---

## F.3: RESTATEMENT & AUDIT SCORE (0-12 pts) â­ HIGH WEIGHT

### Scoring Table

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F3-001 | Restatement <12 months | 12 + **NT-005** |
| F3-002 | Restatement 12-24 months | 10 |
| F3-003 | Restatement 2-5 years | 6 |
| F3-004 | Auditor fired/resigned with disagreement | 10 |
| F3-005 | Material weakness (SOX 404) | 5 |
| F3-006 | Auditor change (routine rotation) | 2 |
| F3-007 | Clean | 0 |

### Calculation Rules
- Use **highest applicable** single condition
- Restatement <12mo triggers NUCLEAR (min HIGH tier)
- "Fired with disagreement" = 8-K Item 4.01 discloses disagreements

### Source Verification
1. 8-K Item 4.02: Non-reliance on prior financials (restatement)
2. 8-K Item 4.01: Auditor changes
3. 10-K Item 9A: Internal controls/material weaknesses
4. 10-K Auditor report: Opinion type

### Calculation Example
```
Company: DEF Corp
8-K Item 4.01 filed June 2024: Auditor change
- Old auditor: BDO (resigned)
- New auditor: Grant Thornton
- Disagreements: No

10-K Item 9A: Effective internal controls (no material weakness)

No restatements found

F.3 Score = 2/12 points (routine auditor change)
```

---

## F.4: IPO/SPAC/M&A SCORE (0-10 pts)

### Scoring Table

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F4-001 | SPAC merger <18 months | 10 |
| F4-002 | SPAC merger 18-36 months | 7 |
| F4-003 | IPO <18 months | 8 |
| F4-004 | IPO 18-36 months | 5 |
| F4-005 | Major M&A (>25% market cap) <2 years | 6 |
| F4-006 | IPO/SPAC >36 months or N/A | 0 |

### Calculation Rules
- Use **highest applicable** single condition
- SPAC <18mo + stock <$5 triggers NUCLEAR
- Major M&A = acquisition >25% of acquirer's market cap

### Source Verification
1. S-1: IPO registration
2. 8-K: IPO completion, SPAC merger completion
3. For SPAC: 8-K merger announcement date + close date

### Calculation Example
```
Company: GHI Holdings
IPO Date: March 2022 (via S-1)
Analysis Date: November 2025
Time since IPO: 44 months â†’ >36 months

No SPAC, no major M&A

F.4 Score = 0/10 points
```

---

## F.5: GUIDANCE MISS SCORE (0-8 pts)

### Scoring Table

| Rule ID | Misses in Past 8 Quarters | Base Points |
|---------|---------------------------|-------------|
| F5-001 | 4+ misses | 8 |
| F5-002 | 3 misses | 6 |
| F5-003 | 2 misses | 4 |
| F5-004 | 1 miss | 2 |
| F5-005 | 0 misses | 0 |

### Bonus
| Rule ID | Condition | Points |
|---------|-----------|--------|
| F5-006 | Any single miss >15% vs guidance | +2 (max 8 total) |

### What Counts as a "Miss"
- Revenue below prior guidance range
- EPS below prior guidance range
- Guidance withdrawn without meeting

### Source Verification
1. Review past 8 quarters of 8-K earnings releases
2. Compare actual results to prior quarter's guidance
3. Document: Quarter, guidance, actual, miss %, stock impact

### Calculation Example
```
Company: JKL Corp
Quarter Analysis (past 8):
- Q1 2024: Guided $500M rev, Actual $485M = -3% miss âœ—
- Q2 2024: Guided $520M rev, Actual $490M = -6% miss âœ—
- Q3 2024: Guided $510M rev, Actual $525M = +3% beat âœ“
- Q4 2024: Guided $550M rev, Actual $530M = -4% miss âœ—
- Q1 2025: Guided $560M rev, Actual $540M = -4% miss âœ—
- Q2 2025: Guided $580M rev, Actual $595M = +3% beat âœ“
- Q3 2025: Guided $600M rev, Actual $590M = -2% miss âœ—
- Q4 2025: Not yet reported

Misses: 5/7 reported quarters â†’ 4+ misses = 8 pts base
Largest miss: 6% (no miss >15%) â†’ No magnitude bonus

F.5 Score = 8/8 points
```

---

## F.6: SHORT INTEREST SCORE (0-8 pts) â€” CONTEXTUAL

**Principle**: Short interest significance depends on sector norms, company size, and trend direction.

### Step 1: Sector Baseline Reference

| Sector | Typical SI | Elevated Threshold | ETF |
|--------|-----------|-------------------|-----|
| Technology | 3-5% | >8% | XLK |
| Healthcare/Biotech | 5-10% | >15% | XLV/XBI |
| Financials | 2-4% | >6% | XLF |
| Consumer Discretionary | 4-7% | >10% | XLY |
| Industrials | 2-4% | >6% | XLI |
| Energy | 3-6% | >10% | XLE |
| REITs | 3-5% | >8% | XLRE |
| Utilities | 2-3% | >5% | XLU |
| Consumer Staples | 2-4% | >6% | XLP |

### Step 2: Relative Score (Company SI vs Sector Average)

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F6-R01 | >3x sector average | 4 |
| F6-R02 | 2-3x sector average | 3 |
| F6-R03 | 1.5-2x sector average | 2 |
| F6-R04 | 1-1.5x sector average | 1 |
| F6-R05 | <1x sector average | 0 |

### Step 3: Market Cap Modifier

| Rule ID | Market Cap | Modifier | Rationale |
|---------|------------|----------|-----------|
| F6-M01 | <$1B | +2 pts | Thin float, harder to cover |
| F6-M02 | $1-5B | +1 pt | Mid-cap sensitivity |
| F6-M03 | >$5B | +0 pts | Deep liquidity |

### Step 4: Trend Modifier (vs 3 months prior)

| Rule ID | Trend | Modifier |
|---------|-------|----------|
| F6-D01 | SI increased >50% | +2 pts |
| F6-D02 | SI increased 25-50% | +1 pt |
| F6-D03 | SI stable (Â±25%) | +0 pts |
| F6-D04 | SI decreased >25% | -1 pt |

### Step 5: Short Seller Report Override

| Rule ID | Condition | Action |
|---------|-----------|--------|
| F6-X01 | Named report <6 months | Minimum 6 pts + **NT-007** |
| F6-X02 | Named report 6-12 months | Minimum 4 pts |

### Calculation Formula
```
F.6 = Relative Score + Market Cap Modifier + Trend Modifier
Maximum: 8 points | Minimum: 0 points
Short report overrides set floor
```

### Source Verification
1. Yahoo Finance: Statistics â†’ Short % of Float
2. FINRA: Bi-monthly short interest (for trend)
3. Activist short sites: Hindenburg, Citron, Muddy Waters, Spruce Point, Kerrisdale

### Calculation Example
```
Company: Small-cap biotech ($800M market cap)
Current SI: 12% [Source: Yahoo Finance, Dec 15, 2025]
Sector (XBI) avg: 7%
3 months ago SI: 8%

Step 2 - Relative: 12% / 7% = 1.71x â†’ F6-R03 = 2 pts
Step 3 - Market cap: $800M < $1B â†’ F6-M01 = +2 pts
Step 4 - Trend: 8% â†’ 12% = +50% â†’ F6-D01 = +2 pts
Step 5 - Report: None found

F.6 Score = 2 + 2 + 2 = 6/8 points

Compare OLD method: 12% = 2 pts (would have missed red flag)
```

---

## F.7: INSIDER TRADING SCORE (0-8 pts) â€” CONTEXTUAL

**Principle**: Insider selling significance depends on % of holdings, % of market cap, plan status, and timing relative to stock drops.

### Step 1: Holdings Sold Score (CEO/CFO only, past 6 months)

| Rule ID | CEO or CFO % Holdings Sold | Points |
|---------|---------------------------|--------|
| F7-H01 | >50% of holdings | 5 |
| F7-H02 | 25-50% of holdings | 3 |
| F7-H03 | 10-25% of holdings | 1 |
| F7-H04 | <10% of holdings | 0 |

### Step 2: Market Cap Impact Score (all insiders)

| Rule ID | Total Selling as % of Market Cap | Points |
|---------|----------------------------------|--------|
| F7-C01 | >1% of market cap | 3 |
| F7-C02 | 0.5-1% of market cap | 2 |
| F7-C03 | 0.1-0.5% of market cap | 1 |
| F7-C04 | <0.1% of market cap | 0 |

### Step 3: 10b5-1 Plan Modifier

| Rule ID | Condition | Modifier |
|---------|-----------|----------|
| F7-P01 | >50% of $ sold outside 10b5-1 plans | +2 pts |
| F7-P02 | New 10b5-1 adopted <90 days before sale | +1 pt |
| F7-P03 | All sales via 10b5-1 established >6mo prior | -1 pt |

### Step 4: Timing Red Flags

| Rule ID | Condition | Modifier |
|---------|-----------|----------|
| F7-T01 | Heavy selling within 90 days before stock drop >15% | +2 pts (scienter) |
| F7-T02 | Sales volume accelerated >2x vs prior 12mo pattern | +1 pt |
| F7-T03 | Consistent quarterly pattern via 10b5-1 | -1 pt |

### Step 5: Net Buying Override

| Rule ID | Condition | Action |
|---------|-----------|--------|
| F7-B01 | Net buying by CEO or CFO (6mo) | Cap total at 2 pts max |
| F7-B02 | Significant open market buys by multiple insiders | Cap total at 1 pt max |

### Calculation Formula
```
F.7 = MAX(Holdings Score, Market Cap Score) + Plan Modifier + Timing Modifier
Maximum: 8 points | Minimum: 0 points
Net buying caps override
```

### Source Verification
1. SEC EDGAR: Form 4 filings (cite accession numbers)
2. DEF 14A: Beneficial ownership table (for total holdings baseline)
3. OpenInsider.com: Aggregated insider activity

### Calculation Example
```
Company: Mid-cap tech ($2.5B market cap)
CEO sold $4M (was 35% of his holdings) [Form 4: 0001234-25-001]
CFO sold $1M (was 8% of her holdings) [Form 4: 0001234-25-002]
Director sold $500K [Form 4: 0001234-25-003]
Total insider selling: $5.5M
All via 10b5-1 plans established 9 months ago
Stock dropped 22% six weeks after CEO's largest sale

Step 1 - Holdings: CEO sold 35% â†’ F7-H02 = 3 pts
Step 2 - Market cap: $5.5M / $2.5B = 0.22% â†’ F7-C03 = 1 pt
Step 3 - Plan: All via established 10b5-1 â†’ F7-P03 = -1 pt
Step 4 - Timing: Heavy sale before 22% drop â†’ F7-T01 = +2 pts

F.7 Score = MAX(3, 1) + (-1) + 2 = 4/8 points

Compare OLD method: $5.5M = 2 pts (missed CEO % holdings + timing)
```

---

## F.8: VOLATILITY SCORE (0-7 pts) â€” CONTEXTUAL

**Principle**: Volatility must be compared to sector norms. Biotech at 6% is normal; utility at 6% is extreme.

### Step 1: Sector Volatility Baselines (90-day std dev)

| Sector | Typical Vol | Elevated | High | ETF |
|--------|-------------|----------|------|-----|
| Biotech | 4-6% | >8% | >12% | XBI |
| Technology | 2-3% | >4% | >6% | XLK |
| Financials | 1.5-2.5% | >3% | >5% | XLF |
| Consumer Disc | 2-3% | >4% | >6% | XLY |
| Industrials | 2-3% | >4% | >6% | XLI |
| Energy | 2.5-4% | >5% | >8% | XLE |
| Healthcare | 1.5-2.5% | >3% | >5% | XLV |
| Utilities | 1-1.5% | >2% | >3% | XLU |
| Consumer Staples | 1-1.5% | >2% | >3% | XLP |
| REITs | 2-3% | >4% | >6% | XLRE |

### Step 2: Relative Score (Company Vol / Sector ETF Vol)

| Rule ID | Volatility Ratio | Points |
|---------|-----------------|--------|
| F8-R01 | >3x sector ETF | 4 |
| F8-R02 | 2-3x sector ETF | 3 |
| F8-R03 | 1.5-2x sector ETF | 2 |
| F8-R04 | 1-1.5x sector ETF | 1 |
| F8-R05 | <1x sector ETF | 0 |

### Step 3: Trend Modifier (vs 6 months ago)

| Rule ID | Volatility Change | Modifier |
|---------|------------------|----------|
| F8-D01 | Vol increased >100% | +2 pts |
| F8-D02 | Vol increased 50-100% | +1 pt |
| F8-D03 | Vol stable (Â±50%) | +0 pts |
| F8-D04 | Vol decreased >50% | -1 pt |

### Step 4: Extreme Event Frequency (past 90 days)

| Rule ID | Days with >5% single-day move | Modifier |
|---------|------------------------------|----------|
| F8-E01 | 5+ occurrences | +2 pts |
| F8-E02 | 3-4 occurrences | +1 pt |
| F8-E03 | 0-2 occurrences | +0 pts |

### Calculation Formula
```
F.8 = Relative Score + Trend Modifier + Event Frequency Modifier
Maximum: 7 points | Minimum: 0 points
```

### Calculation Method
1. Download 90 trading days of closing prices (company AND sector ETF)
2. Calculate daily return: (Today - Yesterday) / Yesterday
3. STDEV of 90 daily returns for both
4. Ratio = Company STDEV / Sector ETF STDEV

### Source Verification
1. Yahoo Finance: Historical prices for company and sector ETF
2. Calculate STDEV manually or via spreadsheet

### Calculation Example
```
Company: Biotech ($1.2B market cap)
Company 90-day vol: 7.8% [Calculated from Yahoo Finance historical]
Sector (XBI) 90-day vol: 5.4% [Same method]
Company vol 6 months ago: 4.5%
Single-day moves >5%: 4 occurrences

Step 2 - Relative: 7.8% / 5.4% = 1.44x â†’ F8-R04 = 1 pt
Step 3 - Trend: 4.5% â†’ 7.8% = +73% â†’ F8-D02 = +1 pt
Step 4 - Events: 4 occurrences â†’ F8-E02 = +1 pt

F.8 Score = 1 + 1 + 1 = 3/7 points

Compare OLD method: 7.8% > 6% = 5 pts (false alarm - biotech is volatile)
```

---

## F.9: FINANCIAL DISTRESS SCORE (0-6 pts) â€” CONTEXTUAL

**Principle**: Leverage thresholds vary by sector. REITs at 6x Debt/EBITDA is normal; tech at 6x is critical.

### Step 1: Sector Leverage Baselines (Debt/EBITDA)

| Sector | Normal | Elevated | Critical |
|--------|--------|----------|----------|
| Utilities | 4-6x | 6-8x | >8x |
| REITs | 5-7x | 7-9x | >9x |
| Telecom | 3-4x | 4-6x | >6x |
| Industrials | 2-3x | 3-5x | >5x |
| Technology | 0-2x | 2-4x | >4x |
| Healthcare | 1-3x | 3-5x | >5x |
| Consumer | 2-3x | 3-5x | >5x |
| Financials | N/A | Use Debt/Equity | >15x D/E |
| Energy | 2-3x | 3-5x | >5x |

### Step 2: Leverage Score (Sector-Relative)

| Rule ID | Leverage vs Sector Threshold | Points |
|---------|------------------------------|--------|
| F9-L01 | >Critical threshold | 3 |
| F9-L02 | Elevated to Critical | 2 |
| F9-L03 | Normal to Elevated | 1 |
| F9-L04 | Below Normal | 0 |

### Step 3: Cash Position Score (Burn-Rate Adjusted)

| Rule ID | Cash Runway | Points |
|---------|-------------|--------|
| F9-C01 | <6 months | 4 |
| F9-C02 | 6-12 months | 2 |
| F9-C03 | 12-18 months | 1 |
| F9-C04 | >18 months or cash flow positive | 0 |

**Cash Runway Calculation:**
```
Runway = (Cash + Undrawn Credit) / Monthly Cash Burn
Monthly Burn = Avg Quarterly OCF (if negative) / 3
```

### Step 4: Trend Deterioration Modifiers

| Rule ID | Condition | Modifier |
|---------|-----------|----------|
| F9-T01 | Leverage increased >50% YoY | +1 pt |
| F9-T02 | Cash declined >40% QoQ (non-seasonal) | +1 pt |
| F9-T03 | EBITDA margin declined >500bps YoY | +1 pt |
| F9-T04 | Metrics improving (leverage down, cash up) | -1 pt |

### Step 5: Hard Triggers (Override)

| Rule ID | Condition | Action |
|---------|-----------|--------|
| F9-X01 | Going concern opinion | 6 pts + **NT-004** |
| F9-X02 | Covenant breach or waiver | Minimum 4 pts |
| F9-X03 | Missed debt payment | 6 pts, consider **NT-001** review |
| F9-X04 | Credit rating downgrade to junk (<BBB-) in past 12mo | +2 pts |

### Calculation Formula
```
F.9 = MAX(Leverage Score, Cash Score) + Trend Modifiers
Hard triggers set minimums/overrides
Maximum: 6 points | Minimum: 0 points
```

### Source Verification
1. 10-Q/10-K: Balance sheet (cash, debt), Cash flow statement (OCF)
2. Debt footnotes: Covenant status, maturity schedule, available credit
3. 10-K Auditor report: Going concern language
4. 8-K: Covenant waivers, credit rating changes

### Calculation Example
```
Company: Utility
Debt/EBITDA: 7.5x [10-K: Debt $3B, EBITDA $400M]
Sector baseline: Normal 4-6x, Elevated 6-8x, Critical >8x
Cash runway: Not applicable (OCF positive)
YoY: Leverage up 25% (was 6.0x), EBITDA margin down 300bps
No going concern, covenants compliant

Step 2 - Leverage: 7.5x = "Elevated" â†’ F9-L02 = 2 pts
Step 3 - Cash: OCF positive â†’ F9-C04 = 0 pts
Step 4 - Trend: Leverage up 25% (<50%) = 0, Margin down 300bps (<500) = 0
Step 5 - Hard triggers: None

F.9 Score = MAX(2, 0) + 0 = 2/6 points

Compare OLD method: Debt/EBITDA 7.5x > 6x = 3 pts (overstated for utility)
```

---

## F.10: GOVERNANCE WEAKNESS SCORE (0-3 pts)

### Scoring Table (Cumulative)

| Rule ID | Condition | Points |
|---------|-----------|--------|
| F10-001 | CEO = Chairman + Board independence <50% | 3 |
| F10-002 | CEO = Chairman alone | 2 |
| F10-002 | Board independence <66% alone | 2 |
| F10-003 | CEO tenure <6 months | 1 |
| F10-004 | CFO tenure <6 months | 1 |
| F10-005 | Strong governance | 0 |

### Calculation Rules
- Cumulative scoring up to max 3 points
- Source: DEF 14A proxy statement

### Calculation Example
```
Company: YZA Inc
DEF 14A Analysis:

CEO: John Smith, tenure 5 years (>6 months) = 0 pts
CFO: Jane Doe, tenure 8 months (>6 months) = 0 pts
CEO = Chairman: Yes = 2 pts
Board: 7 directors, 5 independent = 71% (>66%) = 0 pts

Combined: 2 + 0 + 0 + 0 = 2 pts

F.10 Score = 2/3 points
```

---

## COMPOSITE SCORE CALCULATION

### Step-by-Step Process

**Step 1: Check Nuclear Triggers**
```
â–¡ Active securities class action? â†’ If yes, MIN score = 70
â–¡ Wells Notice? â†’ If yes, MIN score = 70
â–¡ Going concern? â†’ If yes, MIN score = 50
â–¡ Restatement <12mo? â†’ If yes, MIN score = 50
â–¡ SPAC <18mo + stock <$5? â†’ If yes, MIN score = 50
â–¡ Short seller report <6mo? â†’ If yes, MIN score = 50
â–¡ Stock decline >60% company-specific? â†’ If yes, MIN score = 50
â–¡ DOJ investigation? â†’ If yes, MIN score = 70
```

**Step 2: Calculate Individual Factors**
```
F.1 Prior Litigation:    ___/20
F.2 Stock Decline:       ___/15
F.3 Restatement/Audit:   ___/12
F.4 IPO/SPAC/M&A:        ___/10
F.5 Guidance Misses:     ___/8
F.6 Short Interest:      ___/8
F.7 Insider Trading:     ___/8
F.8 Volatility:          ___/7
F.9 Financial Distress:  ___/6
F.10 Governance:         ___/3
                         -------
SUBTOTAL:                ___/100
```

**Step 3: Apply Nuclear Floor**
```
IF Nuclear trigger present:
  FINAL SCORE = MAX(Subtotal, Nuclear minimum)
ELSE:
  FINAL SCORE = Subtotal
```

**Step 4: Determine Tier**
```
70-100 â†’ EXTREME (ðŸ”´ðŸ”´ðŸ”´)
50-69  â†’ HIGH (ðŸ”´ðŸ”´)
30-49  â†’ AVERAGE (âš ï¸)
15-29  â†’ BELOW AVERAGE (âœ…)
0-14   â†’ MINIMAL (âœ…âœ…)
```

---

## SEVERITY CALCULATION (Separate from Likelihood)

### Step 1: Market Cap Base Range

| Market Cap | Base Settlement Range |
|------------|----------------------|
| >$50B | $25M - $150M |
| $10-50B | $15M - $75M |
| $2-10B | $8M - $40M |
| $500M-2B | $4M - $20M |
| <$500M | $2M - $10M |

### Step 2: Apply Tier Multiplier

| Risk Tier | Multiplier |
|-----------|------------|
| EXTREME | 1.5-2.0x |
| HIGH | 1.2-1.5x |
| AVERAGE | 1.0x |
| BELOW AVERAGE | 0.7-0.9x |
| MINIMAL | 0.5-0.7x |

### Step 3: Calculate Expected Severity
```
Expected Settlement = Base Range Ã— Tier Multiplier
```

### Example
```
Market Cap: $8B â†’ Base: $8M - $40M
Risk Tier: HIGH (score 55) â†’ Multiplier: 1.3x

Expected Severity: $10.4M - $52M
```

---

## FINAL SCORING SUMMARY TEMPLATE

```
FINAL SCORING SUMMARY
=====================
Company: [Name]
Analysis Date: [Date]

NUCLEAR TRIGGER CHECK:
â–¡ Active SCA: [Y/N]
â–¡ Wells Notice: [Y/N]
â–¡ Going Concern: [Y/N]
â–¡ Restatement <12mo: [Y/N]
â–¡ SPAC <18mo + <$5: [Y/N]
â–¡ Short Report <6mo: [Y/N]
â–¡ >60% Company-Specific Decline: [Y/N]
â–¡ DOJ Investigation: [Y/N]

â†’ Nuclear Floor Applied: [None / Score X]

FACTOR SCORES:
| Factor | Score | Max | Calculation Summary |
|--------|-------|-----|---------------------|
| F.1 Prior Litigation | | 20 | |
| F.2 Stock Decline | | 15 | |
| F.3 Restatement/Audit | | 12 | |
| F.4 IPO/SPAC/M&A | | 10 | |
| F.5 Guidance Misses | | 8 | |
| F.6 Short Interest | | 8 | |
| F.7 Insider Trading | | 8 | |
| F.8 Volatility | | 7 | |
| F.9 Financial Distress | | 6 | |
| F.10 Governance | | 3 | |
| **TOTAL** | **X** | **100** | |

RISK TIER: [EXTREME / HIGH / AVERAGE / BELOW AVG / MINIMAL]

PROBABILITY ASSESSMENT:
- 18-Month Litigation Probability: [X]%
- Base Rate Comparison: [X]x the ~6% base rate
- Confidence: [HIGH / MODERATE / LOW]

SEVERITY ASSESSMENT:
- Market Cap: $[X]B
- Base Settlement Range: $[X]M - $[Y]M
- Tier Multiplier: [X]x
- Expected Severity: $[X]M - $[Y]M

TOP RISK DRIVERS:
1. [Factor]: [X] pts - [Brief explanation]
2. [Factor]: [X] pts - [Brief explanation]
3. [Factor]: [X] pts - [Brief explanation]

PROTECTIVE FACTORS:
- [Factor scoring low with explanation]
- [Factor scoring low with explanation]
```

---

## â›” SCORING VALIDATION CHECKPOINT (MANDATORY)

**Complete before finalizing any analysis:**

### Data Integrity Checks
```
â–¡ F.2 Stock Data:
  - 52-week high ($___) â‰¥ current ($___) â‰¥ 52-week low ($___)? [PASS/FAIL]
  - Decline math: ($___ - $___) / $___ = ___% [VERIFIED]
  - Data source date: [DATE] - within 24 hours? [YES/NO]

â–¡ F.5 Guidance Data:
  - Quarters analyzed: Q___ through Q___ (8 quarters)? [YES/NO]
  - Each miss has 8-K source cited? [YES/NO]

â–¡ F.6 Short Interest:
  - Source date: [DATE] - within 14 days? [YES/NO]
  - % of float is reasonable (typically 1-30%)? [YES/NO]

â–¡ F.7 Insider Trading:
  - All Form 4s have accession numbers? [YES/NO]
  - Net calculation: Sells $___M - Buys $___M = $___M [VERIFIED]

â–¡ F.8 Volatility:
  - Calculation method documented? [YES/NO]
  - Date range specified? [YES/NO]
```

### Calculation Integrity Checks
```
â–¡ Each factor score â‰¤ maximum allowed:
  - F.1 â‰¤ 20? [___/20] âœ“/âœ—
  - F.2 â‰¤ 15? [___/15] âœ“/âœ—
  - F.3 â‰¤ 12? [___/12] âœ“/âœ—
  - F.4 â‰¤ 10? [___/10] âœ“/âœ—
  - F.5 â‰¤ 8?  [___/8]  âœ“/âœ—
  - F.6 â‰¤ 8?  [___/8]  âœ“/âœ—
  - F.7 â‰¤ 8?  [___/8]  âœ“/âœ—
  - F.8 â‰¤ 7?  [___/7]  âœ“/âœ—
  - F.9 â‰¤ 6?  [___/6]  âœ“/âœ—
  - F.10 â‰¤ 3? [___/3]  âœ“/âœ—

â–¡ Total = Sum of factors:
  ___ + ___ + ___ + ___ + ___ + ___ + ___ + ___ + ___ + ___ = ___ [VERIFIED]

â–¡ Tier matches score range:
  - Score: ___
  - Tier assigned: ___________
  - Correct range: [70-100=EXTREME / 50-69=HIGH / 30-49=AVG / 15-29=BELOW / 0-14=MINIMAL]
  - Match? [YES/NO]

â–¡ Nuclear trigger floor applied correctly:
  - Any nuclear triggers present? [YES/NO]
  - If YES, score â‰¥ minimum floor? [YES/NO]
```

### Logic Checks
```
â–¡ Probability claim â‰¤ 25%? [YES/NO]
â–¡ Probability matches tier? (EXTREME=15-25%, HIGH=10-20%, etc.) [YES/NO]
â–¡ Severity range reasonable for market cap? [YES/NO]
```

### VALIDATION RESULT
```
All checks passed: [YES/NO]
If NO, list failures and corrections made:
1. _______________________________________________
2. _______________________________________________
```

**â›” DO NOT GENERATE FINAL OUTPUT UNTIL ALL VALIDATION CHECKS PASS**

---

**END OF SCORING MODULE**
