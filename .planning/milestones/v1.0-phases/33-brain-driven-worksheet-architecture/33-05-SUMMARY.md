---
phase: 33-brain-driven-worksheet-architecture
plan: 05
subsystem: analyze
tags: [check-engine, field-routing, threshold-calibration, evaluators, mappers]

requires:
  - phase: 33-02
    provides: "False trigger elimination fixes"
  - phase: 33-03
    provides: "Zero-coverage subsection checks and field routing"
provides:
  - "Corrected field routing for 8+ checks (analyst, trade, guidance, valuation)"
  - "Clear signal recognition for SEC enforcement, Wells notice, customer concentration"
  - "FIN.TEMPORAL mapper returns computed metric values from temporal_metrics"
  - "Shared guidance computation helper (compute_guidance_fields)"
affects: [33-06, render, score, benchmark]

tech-stack:
  added: []
  patterns:
    - "_check_clear_signal pattern for qualitative clear/negative signal recognition in evaluators"
    - "compute_guidance_fields shared helper for cross-mapper guidance computation"

key-files:
  created:
    - tests/stages/analyze/test_wiring_fixes.py
  modified:
    - src/do_uw/stages/analyze/check_field_routing.py
    - src/do_uw/stages/analyze/check_mappers.py
    - src/do_uw/stages/analyze/check_mappers_ext.py
    - src/do_uw/stages/analyze/check_evaluators.py
    - src/do_uw/stages/analyze/check_mappers_phase26.py
    - src/do_uw/brain/checks.json

key-decisions:
  - "Updated both FIELD_FOR_CHECK and checks.json data_strategy.field_key for consistency (data_strategy takes priority)"
  - "Used coverage_count model field name (not analyst_count) since that is the actual Pydantic field on AnalystSentimentProfile"
  - "Valuation fields (pe_ratio, ev_ebitda, peg_ratio) use getattr fallback since model fields not yet added by Plan 04"
  - "Guidance fields computed from EarningsGuidanceAnalysis quarters/philosophy/beat_rate"
  - "_check_clear_signal pattern matches on data_key (not check_id) for reusability across evaluator types"
  - "FIN.TEMPORAL mapper uses extract_temporal_metrics for latest period values instead of 'present' markers"

patterns-established:
  - "clear_signal_recognition: _check_clear_signal function for known negative/absent values that indicate CLEAR"
  - "shared_guidance_computation: compute_guidance_fields in check_mappers_ext avoids duplication across financial and market mappers"

requirements-completed: [SC4-false-trigger-elimination, SC6-artifact-renderer-wiring, SC3-acquisition-audit]

duration: 15min
completed: 2026-02-21
---

# Phase 33 Plan 05: Wiring, Routing, and Calibration Fixes Summary

**Fixed 8 field routing errors, added clear-signal recognition for SEC/Wells/customer-concentration, and upgraded FIN.TEMPORAL to return computed metric values instead of placeholder markers**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-21T03:02:21Z
- **Completed:** 2026-02-21T03:17:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Fixed 8 field routing errors: STOCK.TRADE.liquidity, STOCK.ANALYST.coverage, STOCK.ANALYST.momentum, and 5 FIN.GUIDE checks all pointed to wrong fields
- Added _check_clear_signal() evaluator pattern that recognizes "NONE" SEC enforcement, False wells_notice, and "Not mentioned" customer concentration as CLEAR signals instead of INFO
- Upgraded FIN.TEMPORAL mapper to return computed metric values (revenue growth %, operating margin %, etc.) from temporal_metrics extraction instead of generic "present" markers
- Added guidance computation to both financial and market mappers via shared compute_guidance_fields helper
- Updated checks.json data_strategy.field_key entries to match FIELD_FOR_CHECK corrections (both must agree since data_strategy takes priority)
- Created 43 regression tests covering all routing fixes, threshold calibration, SEC enforcement, Wells notice, customer concentration, and clear signal helper

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix field routing for analyst, trade, guidance, and valuation checks** - `407c723` (feat)
2. **Task 2: Fix threshold calibration, SEC enforcement evaluation, and customer concentration logic** - `a000469` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/check_field_routing.py` - Fixed 8 FIELD_FOR_CHECK entries (analyst, trade, guidance)
- `src/do_uw/stages/analyze/check_mappers.py` - Added analyst_count, recommendation_mean, valuation, guidance fields to market/financial mappers
- `src/do_uw/stages/analyze/check_mappers_ext.py` - Added compute_guidance_fields shared helper
- `src/do_uw/stages/analyze/check_evaluators.py` - Added _check_clear_signal and integrated into evaluate_tiered and evaluate_numeric_threshold
- `src/do_uw/stages/analyze/check_mappers_phase26.py` - FIN.TEMPORAL mapper returns computed values from temporal_metrics
- `src/do_uw/brain/checks.json` - Updated 8 data_strategy.field_key entries to match routing corrections
- `tests/stages/analyze/test_wiring_fixes.py` - 43 regression tests for all fixes

## Decisions Made
- Updated both FIELD_FOR_CHECK dict AND checks.json data_strategy.field_key for each fix, since data_strategy takes priority (Phase 31 declarative routing)
- Used model field name `coverage_count` (AnalystSentimentProfile) rather than plan's suggested `analyst_count` for the market mapper, but mapped it as `analyst_count` in the result dict for check routing consistency
- Valuation fields (pe_ratio, ev_ebitda, peg_ratio) use getattr with None fallback since model fields will be added by Plan 04
- _check_clear_signal matches on data_key (the field name), not check_id, making it reusable across any evaluator that processes these fields
- FIN.LIQ.position thresholds verified already correct (<1.0 red, <1.5 yellow) -- the "6.0 miscalibration" mentioned in REVIEW-DECISIONS.md was likely already fixed in a prior phase

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Updated checks.json data_strategy.field_key alongside FIELD_FOR_CHECK**
- **Found during:** Task 1 (field routing fixes)
- **Issue:** Plan only mentioned updating FIELD_FOR_CHECK dict, but data_strategy.field_key in checks.json takes priority (Phase 31 declarative). Without updating both, fixes would have no effect.
- **Fix:** Updated 8 data_strategy.field_key entries in checks.json to match the corrected FIELD_FOR_CHECK routing
- **Files modified:** src/do_uw/brain/checks.json
- **Verification:** Tests verify narrow_result returns correct field for each check
- **Committed in:** 407c723

**2. [Rule 2 - Missing Critical] Extracted guidance computation to shared helper**
- **Found during:** Task 1 (adding guidance fields to mappers)
- **Issue:** Guidance fields needed in both financial mapper (FIN.GUIDE prefix) and market mapper (STOCK prefix). Duplicating computation would violate DRY and push check_mappers.py over 500 lines.
- **Fix:** Created compute_guidance_fields in check_mappers_ext.py, used by both mappers
- **Files modified:** src/do_uw/stages/analyze/check_mappers_ext.py, src/do_uw/stages/analyze/check_mappers.py
- **Verification:** check_mappers.py at 489 lines (under 500 limit), tests pass
- **Committed in:** 407c723

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both essential for correctness. checks.json fix was required for routing changes to take effect. Shared helper was required for 500-line compliance and DRY.

## Issues Encountered
- Pre-existing test failures (tests/config/test_loader.py, tests/knowledge/test_check_definition.py, etc.) expect 388 checks but 396 exist after Phase 33-03 additions. Not caused by this plan, logged as out-of-scope.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All known wiring and calibration issues fixed
- 43 regression tests prevent regressions
- Ready for Plan 06 (renderer wiring and final integration)

---
*Phase: 33-brain-driven-worksheet-architecture*
*Completed: 2026-02-21*
