# D&O UNDERWRITING FRAMEWORK - ISSUES INVENTORY
## Audit Date: January 7, 2026
## Framework Version: 4.6 â†’ 4.7

---

## EXECUTIVE SUMMARY

Comprehensive audit of all project knowledge files identified 9 issues across the framework. All critical and moderate issues have been addressed in v4.7 deliverables.

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 3 | âœ… RESOLVED |
| Moderate | 4 | âœ… RESOLVED |
| Minor | 2 | ðŸ“‹ DOCUMENTED |

---

## CRITICAL ISSUES (All Resolved in v4.7)

### ISSUE 1: Quick Screen Lacks Sector Calibration âœ… RESOLVED
**Severity**: CRITICAL
**Location**: 01_QUICK_SCREEN_V4_6.md (QS-013 through QS-032)

**Problem**: Quick Screen used absolute thresholds for financial/market checks when these metrics are inherently sector-relative. The Scoring module (10_SCORING.md) had contextual scoring for F.6, F.7, F.8, F.9, but QS ran BEFORE scoring with no sector adjustment.

**Affected Checks**:
| Check | Old Threshold | Problem |
|-------|---------------|---------|
| QS-013: Negative EBITDA | RED if negative 4Q (non-biotech) | Only carved out biotech |
| QS-014: Debt/EBITDA | >6.0x = RED | REITs normal at 5-7x |
| QS-017: Margin Compression | >500bps = RED | Sector-dependent |
| QS-018: Current Ratio | <0.8 = RED | Retail runs lower |
| QS-020: Interest Coverage | <2.0x = RED | Utilities/REITs run tighter |
| QS-023: Stock Decline | >60% = ESCALATE | Biotech swings 60%+ routinely |
| QS-030: Short Interest | >20% = RED | Sector norms vary widely |

**Resolution**: Created SEC-001 through SEC-009 sector calibration rules in 01_QUICK_SCREEN_V4_7.md with calibration tables for all 13 sector codes.

---

### ISSUE 2: Stock Monitoring Too Blunt âœ… RESOLVED
**Severity**: CRITICAL
**Location**: 01_QUICK_SCREEN_V4_6.md (QS-023, QS-029, QS-032)

**Problem**: Stock checks only measured:
- 52-week decline from high (too slow - missed recent deterioration)
- Count of 10%+ single-day drops (didn't distinguish recent vs. old)

**Missing Capabilities**:
- Multi-day sustained declines
- Recency weighting
- Acceleration detection
- Attribution within QS itself

**Resolution**: Created STK-001 through STK-010 Stock Performance Module with:
- 6 time horizons (1D, 5D, 20D, 60D, 90D, 52W)
- Sector-calibrated thresholds
- Attribution analysis (STK-008)
- Recency weighting (STK-009)
- Pattern detection (STK-010)
- Supporting reference document (14_STOCK_MONITORING_REFERENCE.md)

---

### ISSUE 3: Inconsistent Rule Numbering âœ… RESOLVED
**Severity**: CRITICAL
**Location**: Multiple files

**Problem**: Rules used inconsistent ID patterns:
- Letter suffixes: NEG-001a, NEG-001b
- Descriptive IDs: STK-1D, STK-5D
- Mixed hierarchical: TRI-001, TRI-001a, TRI-002

**Resolution**: Implemented clean sequential numbering throughout:
- All rules now use `[CATEGORY]-[3-digit number]` format
- No letter suffixes
- No descriptive IDs
- Created RULE_RENUMBERING_MAP.md for backward compatibility

---

## MODERATE ISSUES (All Resolved in v4.7)

### ISSUE 4: Trigger Matrix QS Reference Errors âœ… RESOLVED
**Severity**: MODERATE
**Location**: 02_TRIGGER_MATRIX.md

**Errors Found**:
| Line | Old Reference | Actual QS Check |
|------|---------------|-----------------|
| 57 | "QS-23: Stock >70% Down" | QS-023 is ">60% down" |
| 59 | "QS-25: Short Interest >25%" | QS-025 is IPO timing |
| 60 | "QS-26: Volatility >10%" | QS-026 is Secondary Offering |

**Resolution**: Created corrected 02_TRIGGER_MATRIX_V4_7.md with:
- All QS references verified and corrected
- STK module routing added
- SEC-001 sector-based triggers added

---

### ISSUE 5: F.2 Scoring Not Integrated with STK Module âœ… RESOLVED
**Severity**: MODERATE
**Location**: 10_SCORING.md

**Problem**: F.2 scoring section didn't reference new STK module outputs.

**Resolution**: Created 10_SCORING_F2_UPDATE.md patch with:
- F2-007 linked to STK-008 attribution
- F2-008 linked to STK-010 patterns
- Updated calculation steps referencing STK checkpoint

---

### ISSUE 6: Output Template Missing STK Section âœ… RESOLVED
**Severity**: MODERATE
**Location**: 11_OUTPUT_TEMPLATE_V1_1.md

**Problem**: Section 5 (Stock & Market) didn't capture multi-timeframe analysis.

**Resolution**: Created 11_OUTPUT_TEMPLATE_V1_2.md with:
- Multi-horizon STK table
- Attribution summary section
- Pattern flags section
- Sector comparison for short interest
- Section 10 Scoring Detail added

---

### ISSUE 7: Missing Cross-References âœ… RESOLVED
**Severity**: MODERATE
**Location**: Multiple files

**Problem**:
- QS didn't reference 13_SECTOR_BASELINES.md
- Industry modules didn't reference specific QS checks
- Output template didn't capture multi-timeframe stock analysis

**Resolution**: All v4.7 files include appropriate cross-references:
- QS references SEC calibration tables
- Trigger Matrix references STK module
- Output template references STK checkpoint

---

## MINOR ISSUES (Documented)

### ISSUE 8: Stale File Versions Present ðŸ“‹ DOCUMENTED
**Severity**: LOW
**Location**: /mnt/project/

**Files to Consider Archiving**:
- `01_QUICK_SCREEN_V4_4.md` - superseded by V4_7
- `RULE_INDEX_V4_4.md` - superseded by V4_7
- `RULE_INDEX_V4_5.md` - superseded by V4_7

**Recommendation**: Establish version control protocol. Consider:
1. Archive folder for superseded versions
2. Clear "CURRENT" designation in filenames
3. Version manifest document

---

### ISSUE 9: Industry Module Version Inconsistency ðŸ“‹ DOCUMENTED
**Severity**: LOW
**Location**: All industry module files

**Current State**:
| Module | Version | Consistent? |
|--------|---------|-------------|
| biotech | None stated | âŒ |
| technology | v1.0 | âœ… |
| financials | v3.0 | âœ… |
| healthcare | None stated | âŒ |
| energy | None stated | âŒ |
| industrials | None stated | âŒ |
| REITs | v2.1 | âœ… |
| cpg | None stated | âŒ |
| media | None stated | âŒ |
| transportation | None stated | âŒ |

**Recommendation**: Standardize all modules to consistent version format in headers.

---

## V4.7 DELIVERABLES SUMMARY

| File | Status | Description |
|------|--------|-------------|
| 01_QUICK_SCREEN_V4_7.md | âœ… NEW | Sector calibration + STK module |
| 02_TRIGGER_MATRIX_V4_7.md | âœ… NEW | Corrected references + STK routing |
| 10_SCORING_F2_UPDATE.md | âœ… NEW | F.2 integration with STK |
| 11_OUTPUT_TEMPLATE_V1_2.md | âœ… NEW | Enhanced stock section |
| 14_STOCK_MONITORING_REFERENCE.md | âœ… NEW | STK methodology reference |
| RULE_INDEX_V4_7.md | âœ… NEW | Clean numbering + new rules |
| RULE_RENUMBERING_MAP.md | âœ… NEW | Legacy ID mapping |
| PROJECT_ISSUES_INVENTORY.md | âœ… NEW | This document |

---

## RULE COUNT CHANGES

| Metric | v4.6 | v4.7 | Change |
|--------|------|------|--------|
| SEC rules | 0 | 9 | +9 |
| STK rules | 0 | 10 | +10 |
| NEG rules | 9 | 9 | 0 (renumbered) |
| TRI rules | 5 | 5 | 0 (renumbered) |
| EX rules | 8 | 10 | +2 |
| ESC rules | 5 | 7 | +2 |
| QS rules | 43 | 40 | -3 (retired to STK) |
| **Total Indexed** | 266 | 287 | **+21** |

---

## IMPLEMENTATION NOTES

### Files to Update in Project
When updating the project, replace/add these files:
1. Replace `01_QUICK_SCREEN_V4_6.md` with `01_QUICK_SCREEN_V4_7.md`
2. Replace `02_TRIGGER_MATRIX.md` with `02_TRIGGER_MATRIX_V4_7.md`
3. Replace `RULE_INDEX_V4_6.md` with `RULE_INDEX_V4_7.md`
4. Add `14_STOCK_MONITORING_REFERENCE.md`
5. Add `11_OUTPUT_TEMPLATE_V1_2.md`
6. Apply `10_SCORING_F2_UPDATE.md` patch to `10_SCORING.md`
7. Update Project Instructions to reference v4.7

### Training Notes
Key changes for underwriters:
1. **Always run SEC-001 first** - Sector ID is mandatory
2. **Use STK-001 checkpoint** - Multi-horizon analysis replaces single QS checks
3. **Check STK-010 patterns** - CASCADE and BREAKDOWN trigger escalation
4. **F.2 scoring uses STK output** - Reference STK-007, STK-008, STK-010

---

## VERIFICATION CHECKLIST

Before deploying v4.7:

```
â–¡ All 8 deliverable files created
â–¡ Rule numbering is sequential (no letter suffixes)
â–¡ Cross-references updated in all files
â–¡ STK thresholds match SEC-009 calibration
â–¡ Trigger Matrix QS references verified
â–¡ Output template includes STK checkpoint
â–¡ F.2 scoring references STK module
â–¡ Rule Index totals are accurate
â–¡ Renumbering map covers all changed IDs
```

---

**END OF ISSUES INVENTORY**
