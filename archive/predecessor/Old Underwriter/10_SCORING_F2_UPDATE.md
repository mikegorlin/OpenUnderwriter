# SCORING MODULE - F.2 UPDATE PATCH
## Version 4.7 Integration with STK-001 through STK-010
## Apply this update to 10_SCORING.md Section F.2

---

## F.2: STOCK DECLINE SCORE (0-15 pts) â­ HIGH WEIGHT

### v4.7 INTEGRATION NOTE

**F.2 now integrates with STK-001 through STK-010 from Quick Screen.**

The STK module provides:
- STK-007: 52-week decline percentage (base score input)
- STK-008: Attribution analysis (company vs sector vs market)
- STK-010: Pattern detection (CASCADE, ACCELERATION for bonus)

**Workflow**: Complete STK-001 checkpoint BEFORE calculating F.2.

---

### Base Score Table

| Rule ID | Decline from 52-Week High | Base Points | STK Reference |
|---------|---------------------------|-------------|---------------|
| F2-001 | >60% | 15 | STK-007 RED |
| F2-002 | 50-60% | 12 | STK-007 RED/YELLOW |
| F2-003 | 40-50% | 9 | STK-007 YELLOW |
| F2-004 | 30-40% | 6 | STK-007 YELLOW/PASS |
| F2-005 | 20-30% | 3 | STK-007 PASS |
| F2-006 | <20% | 0 | STK-007 PASS |

**Data Source**: Use STK-007 decline calculation from STK-001 checkpoint.

---

### Bonuses (Updated v4.7)

| Rule ID | Condition | Points | STK Reference |
|---------|-----------|--------|---------------|
| F2-007 | Company underperformed sector by >20 ppts | +3 (max 15 total) | STK-008 COMPANY-SPECIFIC |
| F2-008 | CASCADE or ACCELERATION pattern detected | +2, flag for review | STK-010 patterns |

**v4.7 Change**: F2-008 now triggered by STK-010 pattern detection instead of manual 10-day event-window calculation.

---

### Calculation Steps (Updated v4.7)

**Step 1: Import STK-007 Decline**
```
From STK-001 checkpoint:
- STK-007 Decline %: [X]%
- STK-007 Severity: [ðŸŸ¢/ðŸŸ¡/ðŸ”´]
```

**Step 2: Apply Base Score**
```
Use F2-001 through F2-006 table based on STK-007 decline %
```

**Step 3: Check STK-008 Attribution**
```
From STK-001 checkpoint:
- STK-008 Classification: [COMPANY-SPECIFIC / SECTOR-WIDE / MARKET-WIDE]
- If COMPANY-SPECIFIC and >20 ppts underperformance â†’ Apply F2-007 (+3 pts)
```

**Step 4: Check STK-010 Patterns**
```
From STK-001 checkpoint:
- ACCELERATION detected? [Y/N]
- CASCADE detected? [Y/N]
- If either YES â†’ Apply F2-008 (+2 pts)
```

**Step 5: Calculate Total**
```
F.2 Score = Base + F2-007 bonus + F2-008 bonus
Cap at 15 points maximum
```

---

### Sector ETF Reference

| Sector Code | ETF | Used For |
|-------------|-----|----------|
| UTIL | XLU | STK-008 attribution |
| STPL | XLP | STK-008 attribution |
| FINS | XLF | STK-008 attribution |
| INDU | XLI | STK-008 attribution |
| TECH | XLK | STK-008 attribution |
| HLTH | XLV | STK-008 attribution |
| BIOT | XBI | STK-008 attribution |
| CDIS | XLY | STK-008 attribution |
| ENGY | XLE | STK-008 attribution |
| REIT | XLRE | STK-008 attribution |
| COMM | XLC | STK-008 attribution |
| MATL | XLB | STK-008 attribution |

---

### Calculation Example (v4.7)

```
Company: RetailCo (CDIS sector)
STK-001 CHECKPOINT DATA:
- STK-007: 48% decline from 52-week high
- STK-008: COMPANY-SPECIFIC (company -48%, XLY -5%, difference = 43 ppts)
- STK-010: ACCELERATION detected (STK-004 > STK-005)

F.2 CALCULATION:
Step 1: STK-007 decline = 48%
Step 2: Base score = F2-003 (40-50%) = 9 pts
Step 3: STK-008 = COMPANY-SPECIFIC, 43 ppts > 20 ppts â†’ F2-007 = +3 pts
Step 4: STK-010 = ACCELERATION â†’ F2-008 = +2 pts
Step 5: Total = 9 + 3 + 2 = 14 pts (under 15 cap)

F.2 Score = 14/15 points
```

---

### â›” MANDATORY DATA VALIDATION (F.2)

**Validation now performed in STK-001 checkpoint.**

Before calculating F.2, verify STK-001 checkpoint is complete:

| Check | Rule | Action if Fails |
|-------|------|-----------------|
| STK-001 Complete | All 6 horizons calculated | Complete STK-001 first |
| STK-007 Validated | High â‰¥ Current â‰¥ Low verified | Re-fetch data |
| STK-008 Complete | Attribution calculated if decline >10% | Complete attribution |
| STK-010 Complete | Patterns checked | Complete pattern analysis |

**Validation Template (include in output):**
```
F.2 DATA SOURCE VERIFICATION
- STK-001 Checkpoint Complete: [YES/NO]
- STK-007 Decline: [X]% [Source: Yahoo Finance, accessed DATE]
- STK-008 Attribution: [Classification] - [X] ppts vs sector
- STK-010 Patterns: [List or "None"]
- Data Validation: High ($X) â‰¥ Current ($X) â‰¥ Low ($X) âœ“
```

---

### ZER-001 Requirements for F.2 = 0

**If scoring F.2 = 0, document per ZER-001:**

```
ZER-001 VERIFICATION - F.2 Stock Decline = 0

CLAIM: Stock decline from 52-week high is <20%
SOURCE: STK-001 checkpoint, Yahoo Finance accessed [DATE]
EVIDENCE: 
- 52-Week High: $[X.XX] (reached [DATE])
- Current Price: $[X.XX]
- Calculated Decline: [X]% (formula: (H-C)/H Ã— 100)
- STK-007 Severity: ðŸŸ¢ PASS
VERDICT: VERIFIED - Decline below 20% threshold
```

---

### Cross-Reference to STK Module

| F.2 Element | STK Rule | Location |
|-------------|----------|----------|
| Base decline % | STK-007 | 01_QUICK_SCREEN_V4_7.md |
| Attribution | STK-008 | 01_QUICK_SCREEN_V4_7.md |
| Pattern detection | STK-010 | 01_QUICK_SCREEN_V4_7.md |
| Calculation methodology | All | 14_STOCK_MONITORING_REFERENCE.md |
| Sector thresholds | SEC-009 | 01_QUICK_SCREEN_V4_7.md |

---

**END OF F.2 UPDATE PATCH**
