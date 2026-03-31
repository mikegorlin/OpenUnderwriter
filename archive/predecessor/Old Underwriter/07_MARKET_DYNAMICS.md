# SECTION E: MARKET DYNAMICS
## Version 4.8 - 68 Checks
## Integrated with STK-001 Stock Performance Module

---

## OVERVIEW

This section covers market-related risk factors that indicate investor sentiment, trading dynamics, and market perception of risk. These factors often serve as leading indicators of securities litigation probability.

**When to Load**: Per 02_TRIGGER_MATRIX when:
- STK-008 shows COMPANY-SPECIFIC attribution
- STK-010 detects ACCELERATION, CASCADE, or BREAKDOWN patterns
- QS-012 (Short Seller Report) triggered
- QS-024 (Delisting Notice) triggered
- QS-027 (Lock-Up Expiration) triggered
- QS-028 (Analyst Downgrades) triggered
- QS-030 (Short Interest) elevated

---

## E.1: RECENT EVENTS & MOMENTUM ANALYSIS (Checks E.1.1 - E.1.18)

### E.1.1: Significant Stock Drop Events (Past 24 Months)
**Check ID**: E.1.1
**What**: Identify all single-day drops >10% and multi-day declines >20%
**Source**: Yahoo Finance Historical Data
**Data to Collect**:

| Date | Open | Close | Drop % | Volume vs Avg | Catalyst |
|------|------|-------|--------|---------------|----------|
| [Date] | $X | $X | -X% | Xx | [Event] |

**Thresholds**:
| Event Count | Severity | Scoring Impact |
|-------------|----------|----------------|
| 0 events | ðŸŸ¢ LOW | F.2: 0 pts bonus |
| 1-2 events | ðŸŸ¡ MODERATE | F.2: +1 pts |
| 3-4 events | ðŸ”´ HIGH | F.2: +2 pts |
| 5+ events | ðŸ”´ CRITICAL | F.2: +3 pts, escalate |

---

### E.1.2: Event Window Attribution Analysis
**Check ID**: E.1.2
**What**: For each significant drop, determine if company-specific or sector-driven
**Source**: Compare to sector ETF on same dates
**Calculate**:
```
Event Attribution = Company Drop - Sector ETF Drop
```

| Attribution | Classification | Scoring Impact |
|-------------|----------------|----------------|
| >10 ppts worse than sector | COMPANY-SPECIFIC | Full severity |
| Within Â±5 ppts of sector | SECTOR-WIDE | Reduce 1 tier |
| Within Â±5 ppts of S&P 500 | MARKET-WIDE | Reduce 1 tier |

---

### E.1.3: Momentum Direction
**Check ID**: E.1.3
**What**: Current price trend relative to moving averages
**Source**: Yahoo Finance, TradingView

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Price vs 50-day MA | [Above/Below] by X% | Short-term trend |
| Price vs 200-day MA | [Above/Below] by X% | Long-term trend |
| 50-day vs 200-day MA | [Golden Cross/Death Cross/Neutral] | Trend signal |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Price >50-day >200-day | ðŸŸ¢ BULLISH |
| Price <50-day but >200-day | ðŸŸ¡ WEAKENING |
| Death cross (50<200) recent | ðŸ”´ BEARISH |
| Price <50-day <200-day | ðŸ”´ DOWNTREND |

---

### E.1.4: Lock-Up Expiration Status
**Check ID**: E.1.4
**What**: For IPOs/SPACs, track lock-up expiration timing
**Source**: S-1, calculate from IPO date

| Status | Timing | Risk Level |
|--------|--------|------------|
| Expired | >180 days post-IPO | ðŸŸ¢ LOW (pressure passed) |
| Upcoming | <90 days to expiry | ðŸ”´ HIGH (selling pressure imminent) |
| Recent | 0-30 days post-expiry | ðŸŸ¡ MODERATE (may still be selling) |
| N/A | Not an IPO/SPAC | ðŸŸ¢ N/A |

---

### E.1.5: Secondary Offering Impact
**Check ID**: E.1.5
**What**: Stock performance following recent capital raises
**Source**: S-3, 424B prospectus supplements

| Offering Date | Price | Current Price | Change | Dilution % |
|---------------|-------|---------------|--------|------------|
| [Date] | $X | $X | +/-X% | X% |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Stock up from offering | ðŸŸ¢ LOW |
| Stock flat (Â±10%) | ðŸŸ¡ MODERATE |
| Stock down 10-30% | ðŸ”´ HIGH |
| Stock down >30% | ðŸ”´ CRITICAL - Section 11 risk |

---

### E.1.6: Earnings Reaction Pattern
**Check ID**: E.1.6
**What**: How stock reacts to earnings announcements
**Source**: 8-K, earnings transcripts, Yahoo Finance

| Quarter | EPS Beat/Miss | Revenue Beat/Miss | Next-Day Stock Move |
|---------|---------------|-------------------|---------------------|
| Q1 FY__ | [Beat/Miss] by $X | [Beat/Miss] by $XM | +/-X% |
| Q2 FY__ | | | |
| Q3 FY__ | | | |
| Q4 FY__ | | | |

**Thresholds**:
| Pattern | Severity |
|---------|----------|
| Consistent beats + positive reactions | ðŸŸ¢ LOW |
| Mixed results, muted reactions | ðŸŸ¡ MODERATE |
| Misses + significant drops | ðŸ”´ HIGH |
| Miss + >15% drop + guidance cut | ðŸ”´ CRITICAL |

---

### E.1.7-E.1.18: Additional Event Checks

| Check ID | Description | Source | Threshold |
|----------|-------------|--------|-----------|
| E.1.7 | Guidance Changes (8 quarters) | Earnings releases | 2+ cuts = ðŸ”´ |
| E.1.8 | Pre-Announcement Frequency | 8-K | Any pre-announcement = ðŸŸ¡ |
| E.1.9 | Analyst Day/Investor Day Events | IR calendar | Track date + stock reaction |
| E.1.10 | Conference Presentation Impact | Conference schedule | Large drop after = ðŸ”´ |
| E.1.11 | CEO Media Appearances | News search | Track statements vs outcomes |
| E.1.12 | Product Launch Events | 8-K, PR | Track announce vs reality |
| E.1.13 | Contract Win/Loss Announcements | 8-K | Material contract loss = ðŸ”´ |
| E.1.14 | FDA/Regulatory Decision Events | Agency, 8-K | Adverse decision + drop = ðŸ”´ |
| E.1.15 | M&A Announcement Reaction | 8-K | >10% drop on M&A = ðŸ”´ |
| E.1.16 | Dividend Change Events | 8-K | Cut/suspension = ðŸ”´ |
| E.1.17 | Share Repurchase Announcements | 8-K | Track vs actual buybacks |
| E.1.18 | Index Inclusion/Exclusion | S&P, Russell | Exclusion + drop = ðŸŸ¡ |

---

## E.2: SHORT INTEREST & TRADING DYNAMICS (Checks E.2.1 - E.2.20)

### E.2.1: Short Interest Level
**Check ID**: E.2.1
**What**: Percentage of float sold short
**Source**: FINRA, Yahoo Finance, Nasdaq

| Metric | Value |
|--------|-------|
| Shares Short | [X]M |
| Float | [X]M |
| Short % of Float | [X]% |
| Sector Average | [X]% (per SEC-008) |

**Thresholds** (apply sector calibration from SEC-008):
| Level vs Sector Norm | Severity |
|---------------------|----------|
| Below sector average | ðŸŸ¢ LOW |
| At sector average (Â±2 ppts) | ðŸŸ¢ NORMAL |
| 1.5x sector average | ðŸŸ¡ ELEVATED |
| 2x sector average | ðŸ”´ HIGH |
| >3x sector average | ðŸ”´ CRITICAL |

---

### E.2.2: Short Interest Trend
**Check ID**: E.2.2
**What**: Direction of short interest over time
**Source**: Historical short data (bi-weekly)

| Date | Short Interest | Change |
|------|----------------|--------|
| Current | [X]M | |
| 30 days ago | [X]M | +/-X% |
| 90 days ago | [X]M | +/-X% |

**Thresholds**:
| Trend | Severity |
|-------|----------|
| Decreasing >20% (90 days) | ðŸŸ¢ IMPROVING |
| Stable (Â±10%) | ðŸŸ¡ NEUTRAL |
| Increasing 20-50% | ðŸ”´ CONCERNING |
| Increasing >50% | ðŸ”´ CRITICAL |

---

### E.2.3: Days to Cover
**Check ID**: E.2.3
**What**: How many days of average volume to cover short position
**Source**: Calculate from short interest / avg volume

| Metric | Value |
|--------|-------|
| Shares Short | [X]M |
| Avg Daily Volume | [X]M |
| Days to Cover | [X] days |

**Thresholds**:
| Days to Cover | Severity |
|---------------|----------|
| <3 days | ðŸŸ¢ LOW (easy to cover) |
| 3-7 days | ðŸŸ¡ MODERATE |
| 7-15 days | ðŸ”´ HIGH (crowded short) |
| >15 days | ðŸ”´ CRITICAL (squeeze risk OR conviction short) |

---

### E.2.4: Named Short Seller Reports â­ NUCLEAR TRIGGER
**Check ID**: E.2.4
**What**: Published reports from activist short sellers
**Source**: Hindenburg, Citron, Muddy Waters, Spruce Point, etc.

| Date | Firm | Allegations | Stock Impact | Company Response |
|------|------|-------------|--------------|------------------|
| [Date] | [Firm] | [Summary] | -X% | [Response] |

**Thresholds**:
| Timing | Severity |
|--------|----------|
| Report <6 months | ðŸ”´ **NUCLEAR** - escalate immediately |
| Report 6-12 months | ðŸ”´ HIGH |
| Report 12-24 months | ðŸŸ¡ MODERATE |
| Report >24 months or None | ðŸŸ¢ LOW |

---

### E.2.5: Borrow Fee / Cost to Borrow
**Check ID**: E.2.5
**What**: Cost to borrow shares for shorting (indicates difficulty/conviction)
**Source**: Interactive Brokers, S3 Partners

**Thresholds**:
| Borrow Fee | Interpretation |
|------------|----------------|
| <1% | ðŸŸ¢ Easy to borrow, general availability |
| 1-5% | ðŸŸ¡ Moderate demand |
| 5-20% | ðŸ”´ High demand, hard to borrow |
| >20% | ðŸ”´ CRITICAL - either squeeze setup or strong conviction |

---

### E.2.6-E.2.20: Additional Short/Trading Checks

| Check ID | Description | Source | Threshold |
|----------|-------------|--------|-----------|
| E.2.6 | Fail-to-Deliver Volume | SEC FTD data | Elevated FTDs = ðŸŸ¡ |
| E.2.7 | Dark Pool Activity | FINRA ATS data | Unusual % = ðŸŸ¡ |
| E.2.8 | Options Put/Call Ratio | Options chain | High puts = ðŸŸ¡ |
| E.2.9 | Options Volume vs OI | Options chain | Unusual spikes = ðŸŸ¡ |
| E.2.10 | Implied Volatility Skew | Options chain | High put skew = ðŸ”´ |
| E.2.11 | Trading Volume Anomalies | Yahoo Finance | 3x avg volume = ðŸŸ¡ |
| E.2.12 | Bid-Ask Spread | Level 2 data | Wide spread = ðŸŸ¡ liquidity |
| E.2.13 | Block Trade Activity | Bloomberg | Large blocks = ðŸŸ¡ |
| E.2.14 | Average Daily Volume Trend | Historical | Declining = ðŸŸ¡ |
| E.2.15 | Relative Volume | Current vs avg | >2x sustained = ðŸŸ¡ |
| E.2.16 | Pre-Market/After-Hours Activity | Extended hours | Unusual = ðŸŸ¡ |
| E.2.17 | Exchange Short Sale Volume | Exchange data | % of volume | 
| E.2.18 | Securities Lending Utilization | S3 Partners | High util = ðŸ”´ |
| E.2.19 | Short Squeeze Probability | S3 Partners | High prob = ðŸŸ¡ |
| E.2.20 | Synthetic Short Position | Options analysis | Large synthetic = ðŸ”´ |

---

## E.3: OWNERSHIP STRUCTURE (Checks E.3.1 - E.3.15)

### E.3.1: Institutional Ownership Level
**Check ID**: E.3.1
**What**: Percentage held by institutional investors
**Source**: 13F filings, Yahoo Finance

| Metric | Value |
|--------|-------|
| Institutional Ownership | [X]% |
| Number of Institutions | [X] |
| Top 10 Holders % | [X]% |

**Thresholds**:
| Level | Interpretation |
|-------|----------------|
| >80% | High institutional = sophisticated holders, but crowded |
| 50-80% | Normal institutional mix |
| 20-50% | Lower institutional = more retail |
| <20% | Retail-dominated = higher volatility |

---

### E.3.2: Institutional Ownership Trend
**Check ID**: E.3.2
**What**: Net buying or selling by institutions
**Source**: 13F comparisons (quarterly)

| Quarter | Net Change | Notable Moves |
|---------|------------|---------------|
| Most Recent | +/-[X]% | [Top buyers/sellers] |
| Prior Quarter | +/-[X]% | |

**Thresholds**:
| Trend | Severity |
|-------|----------|
| Net accumulation >5% | ðŸŸ¢ POSITIVE |
| Stable (Â±2%) | ðŸŸ¡ NEUTRAL |
| Net reduction 5-15% | ðŸŸ¡ CONCERNING |
| Net reduction >15% | ðŸ”´ INSTITUTIONS EXITING |

---

### E.3.3: Top Holder Concentration
**Check ID**: E.3.3
**What**: Concentration among largest holders
**Source**: 13F filings

| Rank | Holder | % of Shares | Change | Type |
|------|--------|-------------|--------|------|
| 1 | [Name] | [X]% | +/-X% | [Index/Active/etc.] |
| 2 | | | | |
| ... | | | | |

**Risk Factors**:
- Single holder >20% = governance influence
- Top 5 holders >50% = concentrated, exit risk
- Index funds dominant = passive, won't challenge
- Hedge funds >15% = potential activists

---

### E.3.4: Insider Ownership Level
**Check ID**: E.3.4
**What**: Percentage held by officers and directors
**Source**: DEF 14A, Form 4

**Thresholds**:
| Ownership | Interpretation |
|-----------|----------------|
| >20% | High insider alignment |
| 5-20% | Moderate alignment |
| 1-5% | Low alignment |
| <1% | Minimal skin in game |

---

### E.3.5-E.3.15: Additional Ownership Checks

| Check ID | Description | Source | Threshold |
|----------|-------------|--------|-----------|
| E.3.5 | Dual-Class Structure | DEF 14A | Dual-class = ðŸŸ¡ governance |
| E.3.6 | Controlling Shareholder | 13D | >50% control = ðŸŸ¡ |
| E.3.7 | Founder Control | DEF 14A | Founder control = ðŸŸ¡ |
| E.3.8 | PE/VC Ownership | S-1, 13D | >30% PE/VC = ðŸŸ¡ exit risk |
| E.3.9 | Activist Presence | 13D | Activist = ðŸŸ¡ volatility |
| E.3.10 | Poison Pill Status | DEF 14A | Active pill = ðŸŸ¡ |
| E.3.11 | Staggered Board | DEF 14A | Staggered = ðŸŸ¡ entrenchment |
| E.3.12 | Supermajority Requirements | Charter | Supermajority = ðŸŸ¡ |
| E.3.13 | Shareholder Rights Plan | DEF 14A, 8-K | Recent adoption = ðŸŸ¡ |
| E.3.14 | Share Pledge by Insiders | DEF 14A | Pledged shares = ðŸ”´ |
| E.3.15 | Margin Loan Risk | Proxy | Insider margin = ðŸ”´ forced selling |

---

## E.4: ANALYST SENTIMENT (Checks E.4.1 - E.4.15)

### E.4.1: Analyst Coverage Level
**Check ID**: E.4.1
**What**: Number of analysts covering the stock
**Source**: Yahoo Finance, Bloomberg

**Thresholds**:
| Coverage | Interpretation |
|----------|----------------|
| >15 analysts | Well covered, consensus meaningful |
| 5-15 analysts | Adequate coverage |
| 2-5 analysts | Light coverage |
| 0-1 analysts | No coverage = ðŸ”´ information asymmetry |

---

### E.4.2: Consensus Rating
**Check ID**: E.4.2
**What**: Average analyst recommendation
**Source**: Yahoo Finance, TipRanks

| Rating | Interpretation |
|--------|----------------|
| Strong Buy (4.5-5.0) | Very bullish |
| Buy (3.5-4.5) | Bullish |
| Hold (2.5-3.5) | Neutral |
| Sell (1.5-2.5) | Bearish |
| Strong Sell (1.0-1.5) | Very bearish |

---

### E.4.3: Rating Changes (90 Days)
**Check ID**: E.4.3
**What**: Recent upgrades and downgrades
**Source**: News, analyst reports

| Date | Analyst | Firm | Action | Old | New |
|------|---------|------|--------|-----|-----|
| [Date] | [Name] | [Firm] | [Up/Down] | [Rating] | [Rating] |

**Thresholds**:
| Pattern | Severity |
|---------|----------|
| Net upgrades | ðŸŸ¢ POSITIVE |
| Stable | ðŸŸ¡ NEUTRAL |
| 1-2 downgrades | ðŸŸ¡ MONITOR |
| 3+ downgrades in 30 days | ðŸ”´ CRITICAL - cluster downgrade |

---

### E.4.4: Price Target Analysis
**Check ID**: E.4.4
**What**: Compare current price to analyst targets
**Source**: TipRanks, Yahoo Finance

| Metric | Value |
|--------|-------|
| Current Price | $[X] |
| Average Price Target | $[X] |
| High Target | $[X] |
| Low Target | $[X] |
| Implied Upside/Downside | +/-[X]% |

**Thresholds**:
| Implied Move | Interpretation |
|--------------|----------------|
| >30% upside | Analysts bullish (or stale targets) |
| 0-30% upside | Normal |
| 0-20% downside | Concerning |
| >20% downside | ðŸ”´ Analysts bearish |

---

### E.4.5: Estimate Revisions (90 Days)
**Check ID**: E.4.5
**What**: Direction of EPS and revenue estimate changes
**Source**: Yahoo Finance, Bloomberg

| Timeframe | EPS Revisions | Revenue Revisions |
|-----------|---------------|-------------------|
| 7 Days | [X] up / [X] down | [X] up / [X] down |
| 30 Days | [X] up / [X] down | [X] up / [X] down |
| 90 Days | [X] up / [X] down | [X] up / [X] down |

**Thresholds**:
| Pattern | Severity |
|---------|----------|
| Net upward revisions | ðŸŸ¢ POSITIVE |
| Stable | ðŸŸ¡ NEUTRAL |
| Net downward revisions | ðŸ”´ CONCERNING |
| Unanimous downward | ðŸ”´ CRITICAL |

---

### E.4.6-E.4.15: Additional Analyst Checks

| Check ID | Description | Source | Threshold |
|----------|-------------|--------|-----------|
| E.4.6 | Earnings Surprise History | Earnings data | Pattern of misses = ðŸ”´ |
| E.4.7 | Revenue Surprise History | Earnings data | Pattern of misses = ðŸ”´ |
| E.4.8 | Guidance vs Consensus | Earnings releases | Below consensus = ðŸ”´ |
| E.4.9 | Management Credibility | Track record | Broken promises = ðŸ”´ |
| E.4.10 | Conference Call Tone | NLP/transcript | Negative tone shift = ðŸŸ¡ |
| E.4.11 | Q&A Evasiveness | Transcript | Dodging questions = ðŸŸ¡ |
| E.4.12 | Peer Comparison | Peer analysis | Underperforming peers = ðŸŸ¡ |
| E.4.13 | Sector Analyst Views | Sector reports | Sector headwinds = ðŸŸ¡ |
| E.4.14 | Initiation/Termination | Coverage changes | Coverage dropped = ðŸ”´ |
| E.4.15 | Target Price Changes | Analyst reports | Cuts >20% = ðŸ”´ |

---

## SCORING INTEGRATION

### F.6: Short Interest Score (0-10 pts)
Uses E.2.1, E.2.2, E.2.3 with sector calibration from SEC-008.

### F.8: Volatility Score (0-10 pts)
Uses E.1.1, E.1.2, E.1.3 with sector calibration.

### F.2 Bonus Points
Uses E.1.1 (event count) and STK-010 patterns for +2 pts bonus.

---

## CROSS-REFERENCES

| This Section | Related File | Purpose |
|--------------|--------------|---------|
| E.1 | 01_QUICK_SCREEN (STK-001) | Multi-horizon stock analysis |
| E.2 | 13_SECTOR_BASELINES | Short interest baselines |
| E.3 | 06_GOVERNANCE | Insider trading, ownership |
| E.4 | 10_SCORING F.5 | Guidance track record |

---

## CHECKPOINT OUTPUT FORMAT

```
## MARKET DYNAMICS CHECKPOINT - [COMPANY] ([TICKER])
Analysis Date: [DATE]

### E.1 RECENT EVENTS SUMMARY
- Significant Drops (24mo): [X] events
- Worst Event: [Date] -[X]% on [Catalyst]
- Attribution: [COMPANY-SPECIFIC / SECTOR-WIDE / MARKET-WIDE]
- Momentum: [POSITIVE / NEUTRAL / NEGATIVE]
- Lock-Up Status: [N/A / Expired / Upcoming on DATE]

### E.2 SHORT INTEREST SUMMARY
- Current SI: [X]% of float (vs [X]% sector norm)
- Trend: [Increasing / Stable / Decreasing]
- Short Reports: [None / FIRM on DATE]
- Days to Cover: [X]

### E.3 OWNERSHIP SUMMARY
- Institutional: [X]% ([Trend])
- Insider: [X]%
- Control Issues: [None / Dual-class / Activist / etc.]

### E.4 ANALYST SUMMARY
- Coverage: [X] analysts
- Consensus: [Rating]
- Price Target: $[X] ([+/-X]% from current)
- Recent Changes: [X] upgrades / [X] downgrades (90 days)

### OVERALL MARKET DYNAMICS ASSESSMENT
Severity: [ðŸŸ¢ LOW / ðŸŸ¡ MODERATE / ðŸ”´ HIGH / ðŸ”´ CRITICAL]
Key Flags: [List]
Scoring Inputs: F.6=[X], F.8=[X], F.2 bonus=[X]
```

---

## RULE SUMMARY

| Category | Check Range | Count |
|----------|-------------|-------|
| E.1 Recent Events | E.1.1 - E.1.18 | 18 |
| E.2 Short Interest | E.2.1 - E.2.20 | 20 |
| E.3 Ownership | E.3.1 - E.3.15 | 15 |
| E.4 Analyst | E.4.1 - E.4.15 | 15 |
| **Section Total** | | **68** |

---

**END OF MARKET DYNAMICS SECTION v4.8**
