---
phase: 33-brain-driven-worksheet-architecture
plan: 02
subsystem: analyze
tags: [check-engine, field-routing, thresholds, false-triggers, regression-tests]

# Dependency graph
requires:
  - phase: 32-knowledge-driven-acquisition-analysis-pipeline
    provides: "check enrichment, try_numeric_compare rewrite, QUESTION-AUDIT findings"
provides:
  - "5 false triggers eliminated from check evaluation"
  - "17 regression tests preventing false trigger recurrence"
  - "Calibrated thresholds for liquidity, pay ratio, CEO duality checks"
affects: [33-brain-driven-worksheet-architecture, scoring, rendering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Boolean threshold type for binary governance checks (CEO chair duality)"
    - "Threshold values must match data unit semantics (pay ratio vs percentile, current ratio vs months)"
    - "FIELD_FOR_CHECK legacy entries must be consistent with data_strategy.field_key"

key-files:
  created:
    - tests/stages/analyze/test_false_triggers.py
  modified:
    - src/do_uw/brain/checks.json
    - src/do_uw/stages/analyze/check_field_routing.py

key-decisions:
  - "BIZ.DEPEND.labor routed to labor_risk_flag_count (SKIPPED until extraction provides this data)"
  - "BIZ.DEPEND.key_person routed to customer_concentration to match check name"
  - "GOV.BOARD.ceo_chair changed from tiered to boolean threshold type"
  - "GOV.PAY.peer_comparison calibrated to CEO pay ratio units (>500 red, >200 yellow)"
  - "FIN.LIQ.position calibrated to current ratio scale (<1.0 red, <1.5 yellow)"

patterns-established:
  - "False trigger regression tests: verify both routing AND threshold semantics"
  - "Threshold calibration: red/yellow values must be in same units as routed field data"

requirements-completed:
  - SC4-false-trigger-elimination

# Metrics
duration: 10min
completed: 2026-02-20
---

# Phase 33 Plan 02: False Trigger Elimination Summary

**Fixed 5 known false triggers in check evaluation: corrected field routing for labor/key_person checks, changed CEO chair to boolean threshold, calibrated liquidity and pay ratio thresholds to match data units**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-20T21:40:32Z
- **Completed:** 2026-02-20T21:50:06Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- All 5 false triggers identified in QUESTION-AUDIT eliminated
- 17 regression tests prevent recurrence across field routing, threshold type, and threshold calibration
- No test regressions (135 analyze tests pass, 162 brain tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix all 5 known false triggers** - `d668276` (fix -- field routing + threshold changes were included in Plan 33-01 docs commit which bundled pre-existing working tree changes)
2. **Task 2: Add regression tests** - `0b818c5` (test)

**Plan metadata:** (included in final commit)

## Files Created/Modified
- `tests/stages/analyze/test_false_triggers.py` - 17 regression tests covering all 5 false triggers (280 lines)
- `src/do_uw/brain/checks.json` - Fixed thresholds for FIN.LIQ.position, GOV.BOARD.ceo_chair, GOV.PAY.peer_comparison
- `src/do_uw/stages/analyze/check_field_routing.py` - Fixed FIELD_FOR_CHECK entries for BIZ.DEPEND.labor and BIZ.DEPEND.key_person

## Decisions Made

1. **BIZ.DEPEND.labor routed to non-existent field** -- `labor_risk_flag_count` does not exist in extracted data yet, so the check goes SKIPPED/DATA_UNAVAILABLE. This is intentional: the check should not evaluate until proper labor risk flag extraction exists. Far better than false RED at employee_count=150,000.

2. **GOV.BOARD.ceo_chair changed to boolean** -- The check name is "CEO Chair Separation" and evaluates a True/False duality field. Boolean threshold type is semantically correct. The old tiered threshold had `<50% board independence` in the red text, causing `_extract_comparison` to extract `<50.0`, which matched against boolean True=1.0 and always triggered RED.

3. **GOV.PAY.peer_comparison thresholds calibrated to pay ratio** -- CEO pay ratio data is in raw ratio units (e.g., 533:1 for AAPL). The old threshold text `>75th percentile` extracted as `>75`, causing any company with a pay ratio above 75 to trigger RED. New thresholds: >500 RED (top-quartile excess), >200 YELLOW (elevated but common). These align with S&P 500 CEO pay ratio distributions.

4. **FIN.LIQ.position thresholds calibrated to current ratio** -- The data is current_ratio (assets/liabilities). The old threshold `<6 months runway` extracted as `<6.0`, flagging nearly every company as RED. New thresholds: <1.0 RED (inadequate liquidity), <1.5 YELLOW (tight liquidity). These match standard financial analysis benchmarks.

## Deviations from Plan

### Pre-existing Changes Bundled

The Task 1 code changes (field routing fixes, threshold calibrations, try_numeric_compare rewrite) were already present as uncommitted working tree changes from the Phase 32 post-phase audit. They were committed as part of Plan 33-01's docs commit (`d668276`). This plan verified these changes are correct and added regression tests to lock them in.

Additional field routing fixes beyond the 5 false triggers were included in the same commit:
- BIZ.DEPEND.* checks: `_count` suffix routing to numeric text signal counts
- STOCK.VALUATION.* checks: routing to specific ratio fields instead of current_price
- LIT.REG.* and LIT.OTHER.* checks: routing to specific count fields instead of generic regulatory_count
- GOV.BOARD/PAY/RIGHTS/EFFECT/INSIDER checks: routing to specific fields instead of generic governance_score

These are all [Rule 1 - Bug] fixes (wrong field routing causing incorrect evaluation), applied during the prior Phase 32 audit work.

---

**Total deviations:** 0 new (all code changes pre-existed, plan verified and tested them)
**Impact on plan:** Plan executed as specified. Task 1 was already done; Task 2 added the missing regression tests.

## Issues Encountered
None - all changes verified cleanly against existing test suite.

## Next Phase Readiness
- False triggers eliminated, check evaluation is more trustworthy
- 17 regression tests guard against recurrence
- Ready for Plan 03 (check mapper work) and Plan 04+ (v6 section mapping)

---
*Phase: 33-brain-driven-worksheet-architecture*
*Completed: 2026-02-20*
