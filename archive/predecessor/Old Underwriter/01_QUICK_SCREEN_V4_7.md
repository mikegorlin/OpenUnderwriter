# D&O QUICK SCREEN MODULE
## Version 4.7 - Sector-Calibrated Thresholds + Enhanced Stock Monitoring
## 43 Red Flag Triage Checks + NEG Protocol + SEC Calibration + STK Module

**Purpose**: Rapid triage to identify serious risk conditions BEFORE deep-dive analysis.
**Time Budget**: 20-25 minutes (includes sector calibration + stock analysis)
**Decision Rule**: 3+ red flags = ELEVATED REVIEW REQUIRED (management approval needed to proceed)

---

## â­ v4.7 CHANGES

1. **SEC-001 through SEC-009**: Sector calibration protocol with dynamic thresholds
2. **STK-001 through STK-010**: Stock performance module replacing QS-023, QS-029, QS-032
3. **Clean Rule Numbering**: All rules use sequential 3-digit format (no letter suffixes)
4. **Attribution Integration**: Company vs. Sector vs. Market built into stock checks
5. **Recency Weighting**: Recent events weighted higher than older events

---

## â­ CRITICAL: EXECUTION ORDER

```
TRI-001 (Triage) â†’ SEC-001 (Sector ID) â†’ NEG-001 (Negative Sweep) â†’ QS-001 to QS-043
```

**All gates must pass in order. Do not skip sector identification.**

---

## PHASE 0A: NEGATIVE NEWS SWEEP (NEG-001 through NEG-009)

### NEG-001: Negative Sweep Protocol (Master)
Execute ALL 8 searches (NEG-002 through NEG-009) before proceeding to Quick Screen checks.

| Rule ID | Search Query | Purpose |
|---------|-------------|---------|
| **NEG-002** | "[Company] securities class action lawsuit sued" | Find active/recent litigation |
| **NEG-003** | "[Company] CFO CEO resigned departure left fired" | Find executive turnover |
| **NEG-004** | "[Company] restatement accounting problems SEC" | Find financial reporting issues |
| **NEG-005** | "[Company] investigation subpoena Wells Notice DOJ" | Find regulatory matters |
| **NEG-006** | "[Company] stock drop decline crash plunge" | Find significant price events |
| **NEG-007** | "[Company] guidance cut miss warning disappoints" | Find earnings/guidance issues |
| **NEG-008** | "[Company] short seller Hindenburg Citron fraud" | Find activist short attacks |
| **NEG-009** | "[Company] layoffs restructuring problems troubles" | Find operational distress |

### NEG Checkpoint (REQUIRED)

```
## NEG NEGATIVE NEWS SWEEP - [COMPANY NAME] ([TICKER])
Date Executed: [DATE]

| Rule ID | Query Used | Results Found | Follow-Up Required |
|---------|-----------|---------------|-------------------|
| NEG-002 | "[Company] securities class action" | [Describe or "None found"] | [Yes/No] |
| NEG-003 | "[Company] CFO CEO departure" | [Describe or "None found"] | [Yes/No] |
| NEG-004 | "[Company] restatement accounting" | [Describe or "None found"] | [Yes/No] |
| NEG-005 | "[Company] investigation subpoena" | [Describe or "None found"] | [Yes/No] |
| NEG-006 | "[Company] stock drop decline" | [Describe or "None found"] | [Yes/No] |
| NEG-007 | "[Company] guidance miss warning" | [Describe or "None found"] | [Yes/No] |
| NEG-008 | "[Company] short seller fraud" | [Describe or "None found"] | [Yes/No] |
| NEG-009 | "[Company] layoffs restructuring" | [Describe or "None found"] | [Yes/No] |

### NEG SUMMARY
- **SWEEP COMPLETE**: [YES/NO]
- **ISSUES IDENTIFIED**: [Count]
- **KEY FINDINGS**: [List most significant items]
- **FOLLOW-UP ITEMS FOR QUICK SCREEN**: [List specific checks to scrutinize]
```

**â›” GATE: Do not proceed to Quick Screen until NEG checkpoint is complete.**

---

## â­ PHASE 0B: SECTOR IDENTIFICATION (SEC-001 through SEC-009)

### SEC-001: Sector Identification

**Purpose**: Identify company's sector to apply appropriate thresholds throughout Quick Screen.

#### Step 1: Determine Primary Sector

| Sector Code | Sector Name | Identifying Characteristics | ETF Benchmark |
|-------------|-------------|---------------------------|---------------|
| **UTIL** | Utilities | Regulated power/gas/water, rate base | XLU |
| **STPL** | Consumer Staples | Food, beverage, household products | XLP |
| **FINS** | Financials | Banks, insurance, asset managers | XLF |
| **INDU** | Industrials | Manufacturing, aerospace, construction | XLI |
| **TECH** | Technology | Software, hardware, semiconductors | XLK |
| **HLTH** | Healthcare (Non-Biotech) | Pharma, devices, services | XLV |
| **BIOT** | Biotech | Pre-revenue drug development | XBI |
| **CDIS** | Consumer Discretionary | Retail, auto, leisure | XLY |
| **ENGY** | Energy | Oil & gas, pipelines, services | XLE |
| **REIT** | REITs/Real Estate | Property ownership, mREITs | XLRE |
| **COMM** | Communications/Media | Telecom, media, entertainment | XLC |
| **MATL** | Materials | Chemicals, mining, packaging | XLB |
| **SPEC** | Speculative | Cannabis, crypto, SPACs | N/A |

#### Step 2: Document Sector Selection

```
SEC-001 SECTOR IDENTIFICATION
Company: [Name]
Ticker: [TICKER]
Primary Sector: [CODE] - [Name]
Sector ETF: [Ticker]
Rationale: [1-2 sentences why this classification]
Industry Module to Load: [filename.md]
```

#### Step 3: Load Calibration Tables

Once sector identified, the following checks use SECTOR-CALIBRATED thresholds:

| Check | Calibration Rule |
|-------|------------------|
| QS-013: Negative EBITDA | SEC-002 |
| QS-014: Debt/EBITDA | SEC-003 |
| QS-015: Cash Runway | SEC-004 |
| QS-017: Margin Compression | SEC-005 |
| QS-018: Current Ratio | SEC-006 |
| QS-020: Interest Coverage | SEC-007 |
| QS-030: Short Interest | SEC-008 |
| STK-001: Stock Performance | SEC-009 |

---

## â­ SEC-002 through SEC-007: FINANCIAL CALIBRATION TABLES

### SEC-002: Negative EBITDA Threshold

| Sector | RED Threshold | YELLOW Threshold | Notes |
|--------|---------------|------------------|-------|
| UTIL | 1 quarter negative | 1 quarter declining | Should never be negative |
| STPL | 2 quarters negative | 1 quarter negative | Rare for established |
| FINS | N/A (use net income) | N/A | Different metric |
| INDU | 3 quarters negative | 2 quarters negative | Cyclical allowance |
| TECH | 4 quarters + cash <18mo | 4 quarters negative | Growth companies may burn |
| HLTH | 3 quarters negative | 2 quarters negative | Depends on stage |
| BIOT | N/A | N/A | Expected to be negative |
| CDIS | 3 quarters negative | 2 quarters negative | Standard |
| ENGY | 4 quarters + declining | 3 quarters negative | Commodity cyclicality |
| REIT | N/A (use FFO/AFFO) | N/A | Different metric |
| COMM | 3 quarters negative | 2 quarters negative | Standard |
| MATL | 4 quarters negative | 3 quarters negative | Cyclical |
| SPEC | N/A | N/A | Expected to be negative |

### SEC-003: Debt/EBITDA Threshold

| Sector | RED Threshold | YELLOW Threshold | Normal Range |
|--------|---------------|------------------|--------------|
| UTIL | >8.0x | 6.0-8.0x | 4-6x |
| STPL | >5.0x | 3.5-5.0x | 2-3x |
| FINS | N/A (use Debt/Equity) | >15x D/E | 10-15x D/E |
| INDU | >5.0x | 3.5-5.0x | 2-3x |
| TECH | >4.0x | 2.5-4.0x | 0-2x |
| HLTH | >5.0x | 3.5-5.0x | 1-3x |
| BIOT | N/A (use cash runway) | N/A | Pre-revenue |
| CDIS | >5.0x | 3.5-5.0x | 2-3x |
| ENGY | >5.0x | 3.5-5.0x | 2-3x |
| REIT | >9.0x | 7.0-9.0x | 5-7x |
| COMM | >6.0x | 4.0-6.0x | 3-4x |
| MATL | >5.0x | 3.5-5.0x | 2-3x |
| SPEC | N/A | N/A | Varies widely |

### SEC-004: Cash Runway Threshold

| Sector | RED Threshold | YELLOW Threshold | Applies? |
|--------|---------------|------------------|----------|
| TECH (pre-profit) | <12 months | 12-18 months | âœ… |
| BIOT | <18 months | 18-24 months | âœ… |
| SPEC | <12 months | 12-18 months | âœ… |
| All Others | N/A | N/A | âŒ Use profitability instead |

### SEC-005: Margin Compression Threshold

| Sector | RED Threshold | YELLOW Threshold | Typical Margin |
|--------|---------------|------------------|----------------|
| UTIL | >200bps | 100-200bps | 15-25% operating |
| STPL | >300bps | 150-300bps | 15-20% operating |
| FINS | >300bps | 150-300bps | 25-35% efficiency |
| INDU | >400bps | 200-400bps | 10-15% operating |
| TECH (SaaS) | >800bps | 400-800bps | 60-80% gross |
| TECH (HW) | >500bps | 250-500bps | 30-50% gross |
| HLTH | >400bps | 200-400bps | 20-30% operating |
| BIOT | N/A | N/A | No meaningful margin |
| CDIS | >400bps | 200-400bps | 8-15% operating |
| ENGY | >500bps | 250-500bps | Highly variable |
| REIT | >300bps | 150-300bps | 60-70% NOI |
| COMM | >400bps | 200-400bps | 20-30% operating |
| MATL | >500bps | 250-500bps | 10-20% operating |

### SEC-006: Current Ratio Threshold

| Sector | RED Threshold | YELLOW Threshold | Notes |
|--------|---------------|------------------|-------|
| UTIL | <0.7 | 0.7-0.9 | Lower OK due to stable cash |
| STPL | <0.8 | 0.8-1.0 | Standard |
| FINS | N/A | N/A | Different liquidity metrics |
| INDU | <0.9 | 0.9-1.1 | Standard |
| TECH | <1.0 | 1.0-1.2 | Need higher buffer |
| HLTH | <0.9 | 0.9-1.1 | Standard |
| BIOT | N/A (use cash runway) | N/A | Cash-focused |
| CDIS (Retail) | <0.6 | 0.6-0.8 | Negative WC normal |
| CDIS (Other) | <0.8 | 0.8-1.0 | Standard |
| ENGY | <0.8 | 0.8-1.0 | Standard |
| REIT | <0.5 | 0.5-0.7 | REITs run lower |
| COMM | <0.8 | 0.8-1.0 | Standard |
| MATL | <0.9 | 0.9-1.1 | Standard |

### SEC-007: Interest Coverage Threshold

| Sector | RED Threshold | YELLOW Threshold | Normal Range |
|--------|---------------|------------------|--------------|
| UTIL | <1.2x | 1.2-1.5x | 2-3x |
| STPL | <2.0x | 2.0-2.5x | 4-8x |
| FINS | N/A | N/A | Different metric |
| INDU | <2.0x | 2.0-2.5x | 4-8x |
| TECH | <2.5x | 2.5-3.0x | 5-10x+ |
| HLTH | <2.0x | 2.0-2.5x | 4-8x |
| BIOT | N/A | N/A | Pre-revenue |
| CDIS | <2.0x | 2.0-2.5x | 3-6x |
| ENGY | <1.5x | 1.5-2.0x | 3-6x |
| REIT | <1.2x | 1.2-1.5x | 2-3x |
| COMM | <1.8x | 1.8-2.2x | 3-5x |
| MATL | <2.0x | 2.0-2.5x | 4-8x |

---

## â­ SEC-008: SHORT INTEREST CALIBRATION

| Sector | RED Threshold | YELLOW Threshold | Typical Range |
|--------|---------------|------------------|---------------|
| UTIL | >8% | 5-8% | 2-3% |
| STPL | >10% | 6-10% | 2-4% |
| FINS | >10% | 6-10% | 2-4% |
| INDU | >10% | 6-10% | 2-4% |
| TECH | >15% | 10-15% | 3-5% |
| HLTH | >12% | 8-12% | 3-5% |
| BIOT | >25% | 15-25% | 5-10% |
| CDIS | >15% | 10-15% | 4-7% |
| ENGY | >15% | 10-15% | 3-6% |
| REIT | >12% | 8-12% | 3-5% |
| COMM | >12% | 8-12% | 3-5% |
| MATL | >12% | 8-12% | 3-5% |
| SPEC | >30% | 20-30% | 10-20% |

---

## â­ SEC-009: STOCK DECLINE CALIBRATION

See STK-001 through STK-007 for sector-specific thresholds by time horizon.

---

## â­ STK-001 through STK-010: STOCK PERFORMANCE MODULE

**Replaces**: QS-023 (Stock Decline), QS-029 (Multiple Drops), QS-032 (Stock <$5)

### STK-001: Stock Performance Module (Master)

Comprehensive stock analysis across multiple time horizons with sector calibration, attribution, and recency weighting.

#### Step 1: Gather Stock Data

```
STOCK DATA COLLECTION
Company: [Name] ([TICKER])
Data Date: [DATE]
Source: [Yahoo Finance / Bloomberg / etc.]

Current Price: $[X.XX]
52-Week High: $[X.XX] (Date: [X])
52-Week Low: $[X.XX] (Date: [X])
Sector ETF: [TICKER]
```

#### Step 2: Calculate All Horizons (STK-002 through STK-007)

| Rule ID | Horizon | Period | Calculation |
|---------|---------|--------|-------------|
| STK-002 | 1-Day | Single Day | (Yesterday - Today) / Yesterday Ã— 100 |
| STK-003 | 5-Day | 5 Trading Days | (5 days ago - Today) / 5 days ago Ã— 100 |
| STK-004 | 20-Day | ~1 Month | (20 days ago - Today) / 20 days ago Ã— 100 |
| STK-005 | 60-Day | ~3 Months | (60 days ago - Today) / 60 days ago Ã— 100 |
| STK-006 | 90-Day | ~1 Quarter | (90 days ago - Today) / 90 days ago Ã— 100 |
| STK-007 | 52-Week | From High | (52W High - Today) / 52W High Ã— 100 |

---

### STK-002: Single-Day Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >7% | 5-7% | <5% |
| STPL | >8% | 6-8% | <6% |
| FINS | >10% | 7-10% | <7% |
| INDU | >10% | 7-10% | <7% |
| TECH | >12% | 8-12% | <8% |
| HLTH | >10% | 7-10% | <7% |
| BIOT | >18% | 12-18% | <12% |
| CDIS | >12% | 8-12% | <8% |
| ENGY | >12% | 8-12% | <8% |
| REIT | >10% | 7-10% | <7% |
| COMM | >10% | 7-10% | <7% |
| MATL | >10% | 7-10% | <7% |
| SPEC | >20% | 15-20% | <15% |

---

### STK-003: 5-Day Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >10% | 7-10% | <7% |
| STPL | >12% | 8-12% | <8% |
| FINS | >15% | 10-15% | <10% |
| INDU | >15% | 10-15% | <10% |
| TECH | >18% | 12-18% | <12% |
| HLTH | >15% | 10-15% | <10% |
| BIOT | >25% | 18-25% | <18% |
| CDIS | >18% | 12-18% | <12% |
| ENGY | >18% | 12-18% | <12% |
| REIT | >15% | 10-15% | <10% |
| COMM | >15% | 10-15% | <10% |
| MATL | >15% | 10-15% | <10% |
| SPEC | >30% | 20-30% | <20% |

---

### STK-004: 20-Day Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >15% | 10-15% | <10% |
| STPL | >18% | 12-18% | <12% |
| FINS | >25% | 18-25% | <18% |
| INDU | >25% | 18-25% | <18% |
| TECH | >30% | 20-30% | <20% |
| HLTH | >25% | 18-25% | <18% |
| BIOT | >40% | 30-40% | <30% |
| CDIS | >30% | 20-30% | <20% |
| ENGY | >30% | 20-30% | <20% |
| REIT | >25% | 18-25% | <18% |
| COMM | >25% | 18-25% | <18% |
| MATL | >25% | 18-25% | <18% |
| SPEC | >45% | 35-45% | <35% |

---

### STK-005: 60-Day Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >20% | 15-20% | <15% |
| STPL | >25% | 18-25% | <18% |
| FINS | >35% | 25-35% | <25% |
| INDU | >35% | 25-35% | <25% |
| TECH | >40% | 30-40% | <30% |
| HLTH | >35% | 25-35% | <25% |
| BIOT | >50% | 40-50% | <40% |
| CDIS | >40% | 30-40% | <30% |
| ENGY | >40% | 30-40% | <30% |
| REIT | >35% | 25-35% | <25% |
| COMM | >35% | 25-35% | <25% |
| MATL | >35% | 25-35% | <25% |
| SPEC | >55% | 45-55% | <45% |

---

### STK-006: 90-Day Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >25% | 18-25% | <18% |
| STPL | >30% | 22-30% | <22% |
| FINS | >40% | 30-40% | <30% |
| INDU | >40% | 30-40% | <30% |
| TECH | >45% | 35-45% | <35% |
| HLTH | >40% | 30-40% | <30% |
| BIOT | >55% | 45-55% | <45% |
| CDIS | >45% | 35-45% | <35% |
| ENGY | >45% | 35-45% | <35% |
| REIT | >40% | 30-40% | <30% |
| COMM | >40% | 30-40% | <30% |
| MATL | >40% | 30-40% | <30% |
| SPEC | >60% | 50-60% | <50% |

---

### STK-007: 52-Week Horizon Thresholds

| Sector | ðŸ”´ RED | ðŸŸ¡ YELLOW | ðŸŸ¢ PASS |
|--------|--------|----------|---------|
| UTIL | >30% | 20-30% | <20% |
| STPL | >35% | 25-35% | <25% |
| FINS | >45% | 35-45% | <35% |
| INDU | >45% | 35-45% | <35% |
| TECH | >55% | 40-55% | <40% |
| HLTH | >50% | 35-50% | <35% |
| BIOT | >65% | 50-65% | <50% |
| CDIS | >55% | 40-55% | <40% |
| ENGY | >55% | 40-55% | <40% |
| REIT | >50% | 35-50% | <35% |
| COMM | >50% | 35-50% | <35% |
| MATL | >45% | 35-45% | <35% |
| SPEC | >70% | 55-70% | <55% |

---

### STK-008: Attribution Analysis

**Required for ANY timeframe with decline >10%**

#### Attribution Types

| Classification | Condition | Severity Impact |
|----------------|-----------|-----------------|
| **COMPANY-SPECIFIC** | Company underperformed sector by >10 ppts | Full severity |
| **SECTOR-WIDE** | Company within Â±5 ppts of sector | Reduce 1 tier |
| **MARKET-WIDE** | Company within Â±5 ppts of S&P 500 | Reduce 1 tier |
| **OUTPERFORMER** | Company declined less than sector | Note positive |

#### Attribution Calculation

```
Company-Specific Component = Company Return - Sector ETF Return
Sector Component = Sector ETF Return - S&P 500 Return
Market Component = S&P 500 Return
```

---

### STK-009: Recency Weighting

For single-day drop events in past 12 months:

| Event Timing | Recency Weight | Effect |
|--------------|----------------|--------|
| Last 30 days | 1.5x | Amplifies severity |
| 31-90 days | 1.0x | Standard weight |
| 91-180 days | 0.75x | Reduced weight |
| 181-365 days | 0.5x | Minimal weight |

**Application**: Weighted Impact = Actual Drop % Ã— Recency Weight

---

### STK-010: Pattern Detection

| Pattern | Definition | Severity Impact |
|---------|------------|-----------------|
| **ACCELERATION** | STK-004 decline % > STK-005 decline % | +1 tier (ðŸŸ¡â†’ðŸ”´) |
| **STABILIZATION** | STK-003 flat or up after prior decline | -1 tier (ðŸ”´â†’ðŸŸ¡) |
| **CASCADE** | STK-003 > STK-002 (selling continues) | +1 tier, ESCALATE |
| **RECOVERY** | Current up >10% from 20-day low | Note as mitigating |
| **BREAKDOWN** | 3+ horizons simultaneously RED | ESCALATE |

---

### STK-001 Output Checkpoint

```
## STK-001 STOCK PERFORMANCE ANALYSIS - [COMPANY] ([TICKER])
Analysis Date: [DATE]
Sector: [CODE] - [Name]

### PRICE DATA
| Metric | Value | Date |
|--------|-------|------|
| Current Price | $[X.XX] | [Today] |
| 52-Week High | $[X.XX] | [Date] |
| 52-Week Low | $[X.XX] | [Date] |

### DECLINE BY TIMEFRAME
| Rule | Horizon | Decline | Sector | Attribution | Raw | Adjusted |
|------|---------|---------|--------|-------------|-----|----------|
| STK-002 | 1-Day | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
| STK-003 | 5-Day | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
| STK-004 | 20-Day | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
| STK-005 | 60-Day | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
| STK-006 | 90-Day | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
| STK-007 | 52-Week | [X]% | [X]% | [Type] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |

### PATTERN DETECTION (STK-010)
- [ ] ACCELERATION: [Y/N - details]
- [ ] CASCADE: [Y/N - details]
- [ ] STABILIZATION: [Y/N - details]
- [ ] RECOVERY: [Y/N - details]
- [ ] BREAKDOWN: [Y/N]

### LOW-PRICE RISK
- Current price vs $5 threshold: [Above/Below]
- Sector-appropriate: [Y/N]
- Severity: ðŸŸ¢/ðŸŸ¡/ðŸ”´

### STK-001 SUMMARY
- **Highest Severity Horizon**: [STK-00X] at ðŸ”´/ðŸŸ¡/ðŸŸ¢
- **Company-Specific Flags**: [Count]
- **Pattern Flags**: [List]
- **OVERALL STOCK RISK**: ðŸŸ¢ PASS / ðŸŸ¡ CAUTION / ðŸ”´ RED FLAG / ðŸ”´ ESCALATE
```

---

## CATEGORY QS-A: LITIGATION & ENFORCEMENT (QS-001 to QS-012) â­ NUCLEAR TRIGGERS

**These checks are NOT sector-calibrated - nuclear triggers are universal.**

### QS-001: Active Securities Class Action â­ NUCLEAR
**What**: Pending securities fraud class action
**Source**: Stanford SCAC (securities.stanford.edu), 10-K Item 3
**Threshold**:
- ðŸ”´ **RED FLAG**: Active securities class action pending â†’ NUCLEAR TRIGGER
- ðŸŸ¡ **CAUTION**: Settled <2 years
- ðŸŸ¢ **PASS**: None or settled >2 years

**Action if RED FLAG**: ðŸ”´ ESCALATE to management OR load Section G for prospective-only analysis

---

### QS-002: SEC Wells Notice â­ NUCLEAR
**What**: SEC has notified company of intent to bring enforcement action
**Source**: 10-K/10-Q Risk Factors, 8-K Item 8.01
**Threshold**:
- ðŸ”´ **RED FLAG**: Wells Notice disclosed â†’ NUCLEAR TRIGGER
- ðŸŸ¢ **PASS**: No Wells Notice

**Action if RED FLAG**: ðŸ”´ ESCALATE - requires senior underwriter approval

---

### QS-003: SPAC Status â­ NUCLEAR
**What**: De-SPAC companies have ~60% litigation rate in first 3 years
**Source**: 8-K merger completion, S-4, company history
**Threshold**:
- ðŸ”´ **RED FLAG**: SPAC <18 months AND stock <$5 â†’ NUCLEAR TRIGGER
- ðŸ”´ **RED FLAG**: SPAC <18 months AND stock down >50%
- ðŸŸ¡ **CAUTION**: SPAC 18-36 months
- ðŸŸ¢ **PASS**: Not a SPAC OR SPAC >36 months with stable stock

**Action if RED FLAG**: ðŸ”´ ESCALATE - requires extreme pricing or senior approval

---

### QS-004: Recent Restatement â­ NUCLEAR
**What**: Financial restatements have 70-80% correlation with litigation
**Source**: 8-K Item 4.02 (Non-Reliance), 10-K/A amendments
**Threshold**:
- ðŸ”´ **RED FLAG**: Restatement <12 months â†’ NUCLEAR TRIGGER
- ðŸ”´ **RED FLAG**: Restatement 12-24 months
- ðŸŸ¡ **CAUTION**: Restatement 2-5 years ago
- ðŸŸ¢ **PASS**: None or >5 years

**Action if RED FLAG**: ðŸ”´ ESCALATE - requires senior underwriter approval

---

### QS-005: Auditor Resignation/Dismissal â­ NUCLEAR
**What**: Auditor changes with disagreements signal serious problems
**Source**: 8-K Item 4.01
**Threshold**:
- ðŸ”´ **RED FLAG**: Auditor resigned with disagreements <24 months â†’ NUCLEAR TRIGGER
- ðŸŸ¡ **CAUTION**: Routine rotation
- ðŸŸ¢ **PASS**: Same auditor >3 years

**Action if RED FLAG**: ðŸ”´ ESCALATE, load Section A and B for deep-dive

---

### QS-006: Going Concern Opinion â­ NUCLEAR
**What**: Auditor questions company's ability to continue operating
**Source**: 10-K auditor's report
**Threshold**:
- ðŸ”´ **RED FLAG**: Going concern opinion issued â†’ NUCLEAR TRIGGER
- ðŸŸ¡ **CAUTION**: Substantial doubt language in MD&A
- ðŸŸ¢ **PASS**: Clean opinion

**Action if RED FLAG**: ðŸ”´ ESCALATE - requires senior underwriter approval

---

### QS-007: Material Weakness (SOX 404) â­ NUCLEAR (if unremediated)
**What**: Internal control deficiencies
**Source**: 10-K Item 9A
**Threshold**:
- ðŸ”´ **RED FLAG**: Material weakness disclosed, not remediated â†’ NUCLEAR
- ðŸŸ¡ **CAUTION**: Material weakness, remediation in progress
- ðŸŸ¢ **PASS**: Effective controls

**Action if RED FLAG**: ðŸ”´ ESCALATE, load Section A and B

---

### QS-008: DOJ Investigation â­ NUCLEAR
**What**: Department of Justice criminal investigation
**Source**: 10-K/10-Q Risk Factors, news
**Threshold**:
- ðŸ”´ **RED FLAG**: Active DOJ investigation â†’ NUCLEAR TRIGGER
- ðŸŸ¡ **CAUTION**: DOJ investigation closed without charges
- ðŸŸ¢ **PASS**: No DOJ matters

**Action if RED FLAG**: ðŸ”´ ESCALATE - requires senior underwriter approval

---

### QS-009: SEC Investigation (Non-Wells)
**What**: SEC inquiry or investigation not yet at Wells stage
**Source**: 10-K/10-Q Risk Factors, 8-K
**Threshold**:
- ðŸ”´ **RED FLAG**: Active SEC investigation disclosed
- ðŸŸ¡ **CAUTION**: SEC inquiry (informal)
- ðŸŸ¢ **PASS**: No SEC matters

---

### QS-010: FTC/Antitrust Investigation
**What**: Competition-related investigations
**Source**: 10-K Risk Factors, news
**Threshold**:
- ðŸ”´ **RED FLAG**: Active FTC/DOJ antitrust investigation
- ðŸŸ¡ **CAUTION**: Hart-Scott-Rodino second request pending
- ðŸŸ¢ **PASS**: No antitrust matters

---

### QS-011: Bankruptcy/Default Risk â­ NUCLEAR
**What**: Credit events indicating distress
**Source**: Credit ratings, debt covenants in 10-K
**Threshold**:
- ðŸ”´ **RED FLAG**: Debt in default or bankruptcy filed â†’ NUCLEAR TRIGGER
- ðŸ”´ **RED FLAG**: Credit rating CCC or below
- ðŸŸ¡ **CAUTION**: Covenant waiver in past 12 months
- ðŸŸ¢ **PASS**: Investment grade or stable non-IG

**Action if RED FLAG**: ðŸ”´ ESCALATE - likely decline

---

### QS-012: Short Seller Report â­ NUCLEAR
**What**: Activist short reports from known firms
**Source**: News search, Hindenburg, Citron, Muddy Waters, etc.
**Threshold**:
- ðŸ”´ **RED FLAG**: Short seller report <6 months â†’ NUCLEAR TRIGGER
- ðŸŸ¡ **CAUTION**: Short seller report 6-24 months
- ðŸŸ¢ **PASS**: No short seller reports

**Action if RED FLAG**: ðŸ”´ ESCALATE - elevated review required, load Section F

---

## CATEGORY QS-B: FINANCIAL DISTRESS (QS-013 to QS-022) â­ SECTOR-CALIBRATED

**Apply SEC-002 through SEC-007 thresholds based on sector identified in SEC-001**

### QS-013: Negative EBITDA
**Threshold**: Use SEC-002 table for sector
**Source**: 10-K/10-Q financial statements

### QS-014: Debt/EBITDA
**Threshold**: Use SEC-003 table for sector
**Source**: 10-K balance sheet, calculate

### QS-015: Cash Runway
**Threshold**: Use SEC-004 table for sector
**Source**: 10-K/10-Q cash flow, calculate

### QS-016: Revenue Decline >20% YoY
**Threshold**: >20% = ðŸ”´ RED, 10-20% = ðŸŸ¡ YELLOW (universal)
**Source**: 10-K/10-Q vs prior year

### QS-017: Margin Compression
**Threshold**: Use SEC-005 table for sector
**Source**: 10-K/10-Q vs prior year

### QS-018: Working Capital Deficit
**Threshold**: Use SEC-006 table for sector
**Source**: 10-K/10-Q balance sheet

### QS-019: Debt Maturity Wall (<24 months)
**Threshold**: >30% maturing + distress indicators = ðŸ”´ RED (universal)
**Source**: 10-K debt footnote

### QS-020: Interest Coverage
**Threshold**: Use SEC-007 table for sector
**Source**: Calculate EBIT / Interest Expense

### QS-021: Goodwill >50% of Total Assets
**Threshold**: >50% + recent acquisition = ðŸ”´ RED (universal)
**Source**: 10-K balance sheet

### QS-022: Negative Operating Cash Flow (TTM)
**Threshold**: Negative + declining = ðŸ”´ RED (universal, with sector context)
**Source**: 10-K/10-Q cash flow statement

---

## CATEGORY QS-C: STOCK PERFORMANCE (QS-023 to QS-032)

### QS-023, QS-029, QS-032: REPLACED BY STK-001
**See STK-001 through STK-010 above**

### QS-024: Delisting Notice â­ NUCLEAR
**Threshold**: ðŸ”´ RED FLAG if received â†’ NUCLEAR TRIGGER
**Source**: 8-K Item 3.01, exchange notices

### QS-025: IPO <24 Months
**Threshold**: ðŸ”´ RED if <12 months + stock down >30%, ðŸŸ¡ YELLOW if <24 months
**Source**: S-1, company history

### QS-026: Secondary Offering <12 Months
**Threshold**: ðŸŸ¡ CAUTION if <12 months
**Source**: S-3, 8-K

### QS-027: Lock-Up Expiration <90 Days
**Threshold**: ðŸŸ¡ CAUTION if <90 days
**Source**: S-1, calculate from IPO

### QS-028: Analyst Downgrade Cluster
**Threshold**: 3+ downgrades in 30 days = ðŸ”´ RED
**Source**: News, analyst reports

### QS-030: Short Interest
**Threshold**: Use SEC-008 table for sector
**Source**: Yahoo Finance, FINRA

### QS-031: ATM (At-the-Market) Program Active
**Threshold**: ðŸŸ¡ CAUTION if active
**Source**: S-3, prospectus supplements

---

## CATEGORY QS-D: GOVERNANCE (QS-033 to QS-038)

### QS-033: CEO/CFO Tenure <6 Months â­ CRITICAL
**Threshold**: ðŸ”´ RED if both <6 months, ðŸŸ¡ YELLOW if either <6 months
**Source**: 8-K Item 5.02, DEF 14A

### QS-034: Board Independence <50%
**Threshold**: ðŸ”´ RED if <50%, ðŸŸ¡ YELLOW if 50-66%
**Source**: DEF 14A director table

### QS-035: Insider Selling >$25M Net (6mo)
**Threshold**: ðŸ”´ RED if >$25M, ðŸŸ¡ YELLOW if $10-25M
**Source**: Form 4 filings

### QS-036: Executive Background Issues
**Threshold**: ðŸ”´ RED if CEO/CFO named defendant in prior securities fraud
**Source**: News search, SEC database

### QS-037: Related Party Transactions >5% Revenue
**Threshold**: ðŸ”´ RED if >5%, ðŸŸ¡ YELLOW if 2-5%
**Source**: 10-K Related Party footnote, DEF 14A

### QS-038: Active Proxy Contest
**Threshold**: ðŸ”´ RED if active proxy fight
**Source**: DEF 14A, 13D filings, news

---

## CATEGORY QS-E: INDUSTRY-SPECIFIC (QS-039 to QS-043)

### QS-039: Opioid Exposure
**Applies to**: Pharma, Distributors, Retailers with pharmacy

### QS-040: PFAS/Environmental Contamination
**Applies to**: Chemicals, Manufacturing, Consumer Products

### QS-041: Crypto/Digital Asset Exposure

### QS-042: Cannabis Operations

### QS-043: China VIE Structure
**Applies to**: Companies with China operations

---

## CHECKPOINT OUTPUT FORMAT (v4.7)

```
## QUICK SCREEN RESULTS - [COMPANY NAME] ([TICKER])
Analysis Date: [DATE]

### SEC-001 SECTOR IDENTIFICATION
- Sector: [CODE] - [Name]
- Sector ETF: [Ticker]
- Industry Module: [filename.md]

### NEG-001 NEGATIVE SWEEP SUMMARY
- Sweep Complete: [YES/NO]
- Issues Identified: [COUNT] (via NEG-002 through NEG-009)
- Key Findings: [LIST]

### STK-001 STOCK PERFORMANCE SUMMARY
- Highest Severity Horizon: [STK-00X] at [ðŸ”´/ðŸŸ¡/ðŸŸ¢]
- Company-Specific Decline: [Y/N - X%]
- Patterns Detected (STK-010): [ACCELERATION / CASCADE / None]
- Overall Stock Risk: [ðŸ”´/ðŸŸ¡/ðŸŸ¢]

### NUCLEAR TRIGGERS (QS-001 to QS-012)
| Check | Finding | Severity | Action |
|-------|---------|----------|--------|
| QS-001 | [Result] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [If ðŸ”´: ESCALATE] |
...
| QS-012 | [Result] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | |

### SECTOR-CALIBRATED CHECKS (QS-013 to QS-022)
| Check | Value | Sector Threshold (SEC-00X) | Severity |
|-------|-------|---------------------------|----------|
| QS-013 | [Value] | [Per SEC-002] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ |
...

### SUMMARY
- **NUCLEAR TRIGGERS HIT**: [Count and list]
- **TOTAL RED FLAGS**: X/43
- **TOTAL YELLOW FLAGS**: X/43

### DECISION
- [ ] NUCLEAR TRIGGER HIT â†’ ESCALATE
- [ ] 3+ RED FLAGS â†’ ESCALATE FOR ELEVATED REVIEW
- [ ] <3 RED FLAGS â†’ PROCEED TO SCORING
```

---

## RULE SUMMARY (v4.7)

| Category | Rule IDs | Count |
|----------|----------|-------|
| Sector Calibration | SEC-001 to SEC-009 | 9 |
| Stock Performance | STK-001 to STK-010 | 10 |
| Negative Sweep | NEG-001 to NEG-009 | 9 |
| Quick Screen | QS-001 to QS-043 (less 3 retired) | 40 |
| **Module Total** | | **68** |

---

**END OF QUICK SCREEN MODULE v4.7**
