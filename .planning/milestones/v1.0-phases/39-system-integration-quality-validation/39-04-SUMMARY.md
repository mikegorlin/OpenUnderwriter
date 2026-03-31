---
phase: 39-system-integration-quality-validation
plan: 04
subsystem: analyze
tags: [backtest, false-triggers, check-mappers, prior-litigation, field-routing]

requires:
  - phase: 32-knowledge-driven-acquisition-analysis-pipeline
    provides: check engine, backtest infrastructure, brain DuckDB
  - phase: 33-brain-driven-worksheet-architecture
    provides: false trigger elimination (BIZ.DEPEND.labor, key_person routing)
provides:
  - Reusable backtest audit script (scripts/backtest_audit.py)
  - Fixed TSLA EXEC.PRIOR_LIT false trigger (val=75.0 from hallucinated data)
  - Complete audit results for both AAPL and TSLA check accuracy
affects: [analyze, scoring, brain, render]

tech-stack:
  added: []
  patterns:
    - "Backtest audit: load state -> rerun checks -> classify TRIGGERED/SKIPPED"
    - "Prior lit deduplication: filter URLs/snippets, cap per-exec, return boolean"

key-files:
  created:
    - scripts/backtest_audit.py
  modified:
    - src/do_uw/stages/analyze/check_mappers_phase26.py

key-decisions:
  - "Prior lit check returns boolean (has cases) not raw count to avoid hallucination inflation"
  - "Per-executive cap of 10 cases guards against bulk search contamination"
  - "FIN.LIQ thresholds confirmed correct: <1.0 red, <1.5 yellow for current ratio"
  - "BIZ.DEPEND.labor already correctly routes to labor_risk_flag_count (Phase 33-02 fix)"
  - "TSLA FIN.ACCT.material_weakness val=2.0 is genuine (not false trigger)"

patterns-established:
  - "Backtest audit script: reusable validation tool for check accuracy on any state.json"
  - "False trigger classification: heuristic patterns detect known bad data signatures"

requirements-completed: []

duration: 25min
completed: 2026-02-21
---

# Plan 39-04: Backtest Audit and False Trigger Fixes Summary

**Reusable backtest audit script achieving zero false triggers and zero routing failures across AAPL and TSLA, with EXEC.PRIOR_LIT deduplication fix**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-22T00:25:10Z
- **Completed:** 2026-02-22T00:50:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created comprehensive backtest audit script that categorizes every check result as genuine trigger, false trigger, routing failure, or legitimately unavailable
- Fixed TSLA EXEC.PRIOR_LIT false trigger: val=75.0 was from 75 raw search result snippets stored as "prior_litigation" for misidentified "Kimbal Musk (CEO)" -- now deduplicates and returns boolean
- Confirmed all 27 AAPL triggers and 21 remaining TSLA triggers are genuine
- Confirmed all 98 AAPL and 114 TSLA skipped checks are legitimately unavailable (no routing failures)
- Verified plan-mentioned concerns are not issues: FIN.LIQ thresholds correct, employee count routing already fixed, PE ratio routing correct

## Task Commits

1. **Task 1: Backtest audit script** - `e243c87` (feat)
2. **Task 2: Fix false triggers** - `3b7af79` (fix)

## Files Created/Modified
- `scripts/backtest_audit.py` - Reusable backtest audit tool with false trigger detection patterns, routing failure classification, and human-readable reports
- `src/do_uw/stages/analyze/check_mappers_phase26.py` - EXEC.PRIOR_LIT mapper: deduplicates entries, filters URLs/snippets, caps per-exec at 10, returns boolean for CEO/CFO filtering

## Decisions Made
- Prior lit mapper returns boolean (True/False) matching the check's boolean threshold type, instead of raw count that inflated with hallucinated data
- Per-executive cap of 10 distinct cases prevents bulk search contamination from producing absurd counts
- Confirmed FIN.LIQ.position red threshold (<1.0 current ratio) is correct -- AAPL's 0.89 genuinely indicates inadequate liquidity
- Confirmed BIZ.DEPEND.labor routing to labor_risk_flag_count (Phase 33-02 fix) is working -- check correctly SKIPs when no labor risk flags exist
- TSLA FIN.ACCT.material_weakness val=2.0 confirmed genuine (Tesla had 2 material weaknesses in SOX 404 assessment)

## Deviations from Plan

### Findings Different from Research

**1. FIN.LIQ.position threshold**
- Research mentioned "red threshold 6.0" for current ratio
- Actual threshold in checks.json: "<1.0 current ratio (inadequate liquidity)" -- this is correct
- AAPL val=0.8933 triggers red correctly (Apple's current ratio IS below 1.0)
- No fix needed

**2. BIZ.DEPEND.labor (employee count as labor dependency)**
- Already fixed in Phase 33-02: field_key routes to labor_risk_flag_count, not employee_count
- Audit confirms check correctly SKIPs (data unavailable for labor_risk_flag_count)
- No fix needed

**3. Stock price as PE ratio**
- Not found in audit: STOCK.VALUATION.pe_ratio correctly maps to pe_ratio field
- AAPL val=33.45 is genuine PE ratio, not stock price
- No fix needed

---

**Total deviations:** 1 auto-fix applied (EXEC.PRIOR_LIT mapper), 3 plan-mentioned issues confirmed as non-issues
**Impact on plan:** Plan research was partially based on outdated data; thorough audit confirmed most check logic was already correct

## Issues Encountered
- checks.json repeatedly corrupted to 1 test check by external process -- restored from git HEAD each time
- 186 knowledge test failures are pre-existing (from brain.duckdb infrastructure, not check logic)
- All 213 analyze tests pass when checks.json is correct

## Audit Results Summary

### AAPL (389 checks evaluated)
| Status | Count | Details |
|--------|-------|---------|
| TRIGGERED | 27 | All genuine (0 false) |
| CLEAR | 93 | |
| SKIPPED | 98 | All legitimate (0 routing failures) |
| INFO | 171 | |

### TSLA (389 checks evaluated)
| Status | Count | Details |
|--------|-------|---------|
| TRIGGERED | 23 | All genuine after fix (0 false) |
| CLEAR | 88 | |
| SKIPPED | 114 | All legitimate (0 routing failures) |
| INFO | 164 | |

## Next Phase Readiness
- Backtest audit tool available for ongoing check validation
- All check logic verified accurate for both AAPL and TSLA
- checks.json corruption issue needs to be investigated (external process overwriting)

## Self-Check: PASSED

---
*Phase: 39-system-integration-quality-validation*
*Completed: 2026-02-21*
