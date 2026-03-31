# STOCK MONITORING REFERENCE
## Version 1.0 | January 2026
## Supporting Reference for STK-001 through STK-010

---

## PURPOSE

This document provides:
1. Calculation methodologies for STK-001 stock analysis
2. Sector-specific threshold rationale
3. Attribution calculation examples (STK-008)
4. Recency weighting methodology (STK-009)
5. Pattern detection algorithms (STK-010)
6. Integration with F.2 scoring

---

## SECTION 1: RULE QUICK REFERENCE

| Rule ID | Name | Description |
|---------|------|-------------|
| STK-001 | Stock Performance Module | Master module - comprehensive analysis |
| STK-002 | Single-Day Horizon | 1-day decline analysis |
| STK-003 | 5-Day Horizon | 5-day decline analysis |
| STK-004 | 20-Day Horizon | ~1 month decline analysis |
| STK-005 | 60-Day Horizon | ~3 month decline analysis |
| STK-006 | 90-Day Horizon | Quarterly decline analysis |
| STK-007 | 52-Week Horizon | Annual decline from high |
| STK-008 | Attribution Analysis | Company vs Sector vs Market |
| STK-009 | Recency Weighting | Time-based severity adjustment |
| STK-010 | Pattern Detection | Acceleration, cascade, recovery patterns |

---

## SECTION 2: DATA REQUIREMENTS

### 2.1 Minimum Data Points Required

| Data Point | Source | Required For |
|------------|--------|--------------|
| Current price | Yahoo Finance, Bloomberg | All horizons |
| 52-week high | Yahoo Finance | STK-007 |
| 52-week low | Yahoo Finance | Validation |
| 1-day prior close | Yahoo Finance | STK-002 |
| 5-day prior close | Yahoo Finance | STK-003 |
| 20-day prior close | Yahoo Finance | STK-004 |
| 60-day prior close | Yahoo Finance | STK-005 |
| 90-day prior close | Yahoo Finance | STK-006 |
| Sector ETF current | Yahoo Finance | STK-008 |
| Sector ETF historical | Yahoo Finance | STK-008 |
| S&P 500 historical | Yahoo Finance | STK-008 |

### 2.2 Date Calculations

**Trading Days vs Calendar Days**:
- STK-003: 5 trading days (approximately 1 week)
- STK-004: 20 trading days (approximately 1 month)
- STK-005: 60 trading days (approximately 3 months)
- STK-006: 90 trading days (approximately 1 quarter)

**Holiday Adjustment**: If a horizon date falls on a non-trading day, use the prior trading day's close.

---

## SECTION 3: CALCULATION METHODOLOGIES

### 3.1 Decline Percentage Calculation (STK-002 through STK-007)

**Formula**:
```
Decline % = (Reference Price - Current Price) / Reference Price Ã— 100
```

**Examples**:

| Rule | Reference Price | Current Price | Calculation | Result |
|------|----------------|---------------|-------------|--------|
| STK-002 | $50.00 (yesterday) | $47.00 | (50-47)/50Ã—100 | 6.0% |
| STK-007 | $80.00 (52W high) | $47.00 | (80-47)/80Ã—100 | 41.25% |

### 3.2 Attribution Calculation (STK-008)

**Purpose**: Determine if decline is company-specific, sector-wide, or market-wide.

**Step 1: Calculate Returns**
```
Company Return = (Current - Reference) / Reference Ã— 100
Sector Return = (Sector ETF Current - Sector ETF Reference) / Sector ETF Reference Ã— 100
Market Return = (S&P 500 Current - S&P 500 Reference) / S&P 500 Reference Ã— 100
```

**Step 2: Calculate Components**
```
Company-Specific Component = Company Return - Sector Return
Sector Component = Sector Return - Market Return
Market Component = Market Return
```

**Step 3: Classify**

| Classification | Condition | Severity Impact |
|----------------|-----------|-----------------|
| **COMPANY-SPECIFIC** | Company underperformed sector by >10 ppts | Full severity |
| **SECTOR-WIDE** | Company within Â±5 ppts of sector | Reduce 1 tier |
| **MARKET-WIDE** | Company within Â±5 ppts of S&P 500 | Reduce 1 tier |
| **OUTPERFORMER** | Company declined less than sector | Note positive |

**Example**:
```
Company: TechCorp
Horizon: STK-004 (20 trading days)

Company Return: -25%
Sector ETF (XLK) Return: -8%
S&P 500 Return: -5%

Company-Specific: -25% - (-8%) = -17% (underperformed sector by 17 ppts)
Sector: -8% - (-5%) = -3% (sector underperformed market by 3 ppts)
Market: -5%

Classification: COMPANY-SPECIFIC (>10 ppts underperformance)
Severity: Full (no reduction)
```

### 3.3 Recency Weighting (STK-009)

**Purpose**: Recent events matter more for near-term litigation risk.

**Weight Schedule**:

| Event Timing | Weight | Rationale |
|--------------|--------|-----------|
| Last 30 days | 1.5x | Immediate relevance, may be current class period |
| 31-90 days | 1.0x | Standard weight, within typical class period |
| 91-180 days | 0.75x | Reduced but still material |
| 181-365 days | 0.5x | Historical, less immediate concern |

**Application**:

For single-day drops, multiply the drop percentage by the recency weight:

```
Weighted Impact = Actual Drop % Ã— Recency Weight
```

**Example**:
- 15% drop 2 weeks ago: 15% Ã— 1.5 = 22.5% weighted
- 15% drop 4 months ago: 15% Ã— 0.75 = 11.25% weighted

---

## SECTION 4: PATTERN DETECTION ALGORITHMS (STK-010)

### 4.1 ACCELERATION Pattern

**Definition**: Decline is speeding up (recent decline steeper than longer-term)

**Detection Logic**:
```
IF STK-004 decline % > STK-005 decline %
   AND both are negative
THEN ACCELERATION = TRUE
```

**Example**:
- STK-005 (60-day): -20%
- STK-004 (20-day): -30%
- ACCELERATION detected (more decline in recent month than prior 2 months combined)

**Severity Impact**: +1 tier (ðŸŸ¡ â†’ ðŸ”´)

### 4.2 CASCADE Pattern

**Definition**: Selling continues after initial event (worse than initial drop)

**Detection Logic**:
```
IF STK-003 decline % > STK-002 decline %
   AND STK-002 was a discrete event (>5% single day)
THEN CASCADE = TRUE
```

**Example**:
- Day 1: 12% drop on earnings miss
- Day 2-5: Additional 10% decline
- STK-002: 12%, STK-003: 22%
- CASCADE detected

**Severity Impact**: +1 tier, ESCALATE

### 4.3 STABILIZATION Pattern

**Definition**: Stock has stabilized or recovered after decline

**Detection Logic**:
```
IF STK-003 is flat (Â±2%) or positive
   AND STK-004 or STK-005 showed prior decline
THEN STABILIZATION = TRUE
```

**Severity Impact**: -1 tier (ðŸ”´ â†’ ðŸŸ¡)

### 4.4 RECOVERY Pattern

**Definition**: Meaningful recovery from recent lows

**Detection Logic**:
```
IF Current price > 20-day low by more than 10%
   AND 52W decline still elevated
THEN RECOVERY = TRUE
```

**Severity Impact**: Note as mitigating (don't change tier, but document)

### 4.5 BREAKDOWN Pattern

**Definition**: Multiple timeframes simultaneously in RED zone

**Detection Logic**:
```
IF 3 or more horizons (STK-002 through STK-007) = RED
THEN BREAKDOWN = TRUE
```

**Severity Impact**: ESCALATE regardless of individual horizon severity

---

## SECTION 5: SECTOR THRESHOLD RATIONALE

### 5.1 Why Thresholds Vary by Sector

**Volatility Hierarchy** (lowest to highest):
1. Utilities (regulated, predictable cash flows)
2. Consumer Staples (defensive, stable demand)
3. Financials (regulated but rate-sensitive)
4. Healthcare (pharma/services - stable)
5. Industrials (cyclical but diversified)
6. Communications (mix of stable/growth)
7. REITs (rate-sensitive, leverage)
8. Materials (commodity-linked)
9. Consumer Discretionary (cyclical, competitive)
10. Technology (high growth, high expectations)
11. Energy (commodity volatility)
12. Biotech (binary outcomes)
13. Speculative (extreme uncertainty)

### 5.2 Threshold Development Methodology

Thresholds were developed using:
1. Historical 90th percentile daily/weekly moves by sector
2. Litigation filing correlation analysis
3. Sector ETF volatility benchmarks
4. Expert underwriter judgment

**Example**: Technology STK-002 threshold of 12%
- Historical data shows tech stocks regularly move 5-8% on earnings
- 10%+ single-day moves occur in ~15% of earnings releases
- Litigation filing analysis shows 12%+ drops have 3x higher lawsuit probability
- Therefore, 12% set as RED threshold (vs. 7-10% for lower-vol sectors)

### 5.3 Biotech Special Considerations

Biotech thresholds are significantly higher because:
- Binary clinical trial readouts cause 30-50%+ routine moves
- FDA decisions (CRLs) cause 40-80% declines routinely
- Courts provide substantial protection for scientific uncertainty
- Dismissal rates for biotech securities suits run 56-80%

**Key Principle**: A 50% biotech drop may be "business as usual" while a 50% utility drop is catastrophic.

---

## SECTION 6: INTEGRATION WITH F.2 SCORING

### 6.1 STK Module Informs F.2

The STK-001 module provides granular data for F.2 (Stock Decline) scoring:

| STK Output | F.2 Input |
|------------|-----------|
| STK-007 decline % | Base F.2 score (0-15 pts) |
| STK-008 attribution (company-specific %) | F2-007 bonus (+3 pts if >20% vs sector) |
| STK-010 pattern detection (CASCADE/ACCEL) | F2-008 event-window flag (+2 pts) |

### 6.2 STK Module Triggers F.2 Deep Analysis

| STK Finding | F.2 Action |
|-------------|------------|
| STK-001 PASS | Standard F.2 scoring |
| STK-001 CAUTION | Standard F.2 + document concerns |
| STK-001 RED | F.2 deep-dive, attribution required |
| STK-001 ESCALATE | F.2 + load 07_MARKET_DYNAMICS section |

### 6.3 Worked Example

```
Company: RetailCo
Sector: CDIS (Consumer Discretionary)

STK MODULE FINDINGS:
- STK-007: 48% decline (from $75 high to $39 current)
- STK-004: 22% decline
- STK-008: Company-specific (CDIS ETF only -5% same period)
- STK-010: ACCELERATION detected (STK-004 > STK-005)

F.2 SCORING:
- Base: 48% decline â†’ F2-003 = 9 pts (40-50% bracket)
- STK-008 Attribution: Company underperformed sector by 43 ppts â†’ F2-007 = +3 pts
- STK-010 Pattern: ACCELERATION pattern â†’ Flag but no additional points

F.2 Total: 12/15 points
```

---

## SECTION 7: DATA SOURCES & VERIFICATION

### 7.1 Primary Sources

| Source | URL | Data Available |
|--------|-----|----------------|
| Yahoo Finance | finance.yahoo.com | All price data, basic fundamentals |
| FINRA | finra.org/finra-data | Short interest (bi-monthly) |
| SEC EDGAR | sec.gov/edgar | Form 4 insider trades |
| Bloomberg | bloomberg.com | Professional data (if available) |

### 7.2 Data Validation Rules

**Before using ANY stock data, verify**:

| Check | Rule | If Fails |
|-------|------|----------|
| 52-Week Range | High â‰¥ Current â‰¥ Low | Re-fetch data |
| Current vs High | Current â‰¤ 52-week high | Check data staleness |
| Decline Math | Manual recalculation | Recalculate |
| Price Reasonableness | Within 5% of live quotes | Check date pulled |
| Split Adjustment | Prices adjusted for splits | Use adjusted close |

### 7.3 Citation Format

Always cite stock data with access date:

```
Stock Price: $47.23 [Source: Yahoo Finance, accessed Jan 7, 2026]
52-Week High: $75.18 (reached Aug 15, 2025) [Source: Yahoo Finance, accessed Jan 7, 2026]
```

---

## SECTION 8: COMMON SCENARIOS

### 8.1 Scenario: Biotech Clinical Trial Failure

**Facts**:
- Pre-announcement: $45
- Day 1 (Phase 3 miss): Dropped 55% to $20.25
- Day 2-5: Drifted to $18.50
- Sector (XBI): -2% same period

**STK Analysis**:
- STK-002: 55% â†’ BIOT threshold 18% â†’ ðŸ”´ RED
- STK-003: 59% â†’ BIOT threshold 25% â†’ ðŸ”´ RED
- STK-008: Company-specific (55% vs 2% sector)
- STK-010: CASCADE (STK-003 > STK-002)

**Result**: ESCALATE (multi-horizon RED + CASCADE per STK-010)

**Mitigation Factors**:
- BIOT sector has higher thresholds (55% is 3x threshold, not 5.5x)
- Judicial protection for clinical outcomes
- High dismissal rate expected

### 8.2 Scenario: Utility Rate Case Adverse Ruling

**Facts**:
- Pre-announcement: $65
- Day 1 (adverse ruling): Dropped 12% to $57.20
- Sector (XLU): Flat

**STK Analysis**:
- STK-002: 12% â†’ UTIL threshold 7% â†’ ðŸ”´ RED
- STK-008: 100% company-specific
- STK-010: No patterns

**Result**: ðŸ”´ RED FLAG (unusual for sector)

**Concern Level**: HIGH - utilities should not move 12% on any single event.

### 8.3 Scenario: Market-Wide Selloff

**Facts**:
- Company down 25% over 20 days
- Sector ETF down 22% same period
- S&P 500 down 18% same period

**STK Analysis**:
- STK-004: 25% â†’ threshold varies by sector
- STK-008: Company only 3 ppts worse than sector
- Classification: SECTOR-WIDE

**Result**: Reduce severity by 1 tier (ðŸ”´ â†’ ðŸŸ¡ or ðŸŸ¡ â†’ ðŸŸ¢)

---

## SECTION 9: CHECKLIST

Before completing STK-001, verify:

```
â–¡ All 6 horizons calculated (STK-002 through STK-007)
â–¡ Stock data validated (High â‰¥ Current â‰¥ Low)
â–¡ STK-008 attribution calculated for any horizon >10% decline
â–¡ Sector ETF identified and used
â–¡ STK-009 recency weights applied to discrete events
â–¡ STK-010 patterns checked (ACCELERATION, CASCADE, STABILIZATION, RECOVERY, BREAKDOWN)
â–¡ Low-price risk assessed (<$5 threshold)
â–¡ Sector-appropriate thresholds applied (per SEC-009)
â–¡ Sources cited with access dates
â–¡ Overall STK-001 verdict documented
```

---

**END OF STOCK MONITORING REFERENCE v1.0**
