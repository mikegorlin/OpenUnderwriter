---
phase: 68-quarterly-extraction
plan: 02
subsystem: extract
tags: [xbrl, trends, qoq, yoy, acceleration, pattern-detection]

# Dependency graph
requires:
  - phase: 68-01
    provides: QuarterlyStatements + QuarterlyPeriod models with 8-quarter XBRL data
provides:
  - TrendResult dataclass with QoQ, YoY, acceleration, and sequential pattern metrics
  - compute_trends() for single-concept trend analysis
  - compute_all_trends() for full QuarterlyStatements trend sweep
  - detect_sequential_pattern() for margin compression, revenue deceleration, cash flow deterioration
affects: [68-03, 69-forensic-analysis, 70-signal-integration, 73-rendering]

# Tech tracking
tech-stack:
  added: []
  patterns: [dataclass-based TrendResult, endpoint-excluded QoQ convention, fiscal_quarter YoY matching]

key-files:
  created:
    - src/do_uw/stages/extract/xbrl_trends.py
    - tests/test_xbrl_trends.py
  modified: []

key-decisions:
  - "QoQ endpoints (most recent + oldest) return None -- interior quarters only get computed changes"
  - "YoY matches by fiscal_quarter field to eliminate seasonality (Q1-to-Q1, not position-based)"
  - "Sequential pattern detection skips None values without breaking streak"
  - "Pattern names derived from concept keywords: margin->compression, revenue/growth->deceleration, else->deterioration"

patterns-established:
  - "TrendResult dataclass: concept + qoq_changes + yoy_changes + acceleration + pattern for any XBRL concept"
  - "Statement attribute mapping via _STATEMENT_ATTRS dict for income/balance/cash_flow"

requirements-completed: [QTRLY-04, QTRLY-05]

# Metrics
duration: 5min
completed: 2026-03-06
---

# Phase 68 Plan 02: Trend Computation Summary

**QoQ/YoY/acceleration/sequential-pattern trend engine for 8-quarter XBRL data with 14 tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-06T14:16:05Z
- **Completed:** 2026-03-06T14:21:28Z
- **Tasks:** 1 (TDD: RED + GREEN + REFACTOR)
- **Files modified:** 2

## Accomplishments
- TrendResult dataclass captures all trend metrics per concept
- QoQ computation handles None, zero denominator, and normal values correctly
- YoY matches same fiscal quarter (Q1-to-Q1) eliminating seasonality bias
- Acceleration detection shows growth direction changes
- Sequential pattern detection flags 4+ consecutive declines as compression/deceleration/deterioration
- compute_all_trends sweeps all concepts across QuarterlyStatements
- 14 tests pass, 0 pyright errors

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `fc17a90` (test)
2. **Task 1 GREEN+REFACTOR: Implementation** - `82d4315` (feat)

_TDD task with RED/GREEN/REFACTOR cycle._

## Files Created/Modified
- `src/do_uw/stages/extract/xbrl_trends.py` (260 lines) - Trend computation module with TrendResult, compute_qoq, compute_yoy, compute_acceleration, detect_sequential_pattern, compute_trends, compute_all_trends
- `tests/test_xbrl_trends.py` (270 lines) - 14 tests covering all computation functions and edge cases

## Decisions Made
- QoQ endpoint convention: result[0] and result[-1] always None (only interior quarter transitions computed)
- YoY matches by fiscal_quarter field rather than positional index to handle non-standard fiscal years
- Sequential pattern detection skips None values without breaking the streak (common in quarterly data)
- Zero test adjusted from plan: tests zero denominator (prev=0) not zero numerator (curr=0)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected zero-prior test case**
- **Found during:** Task 1 (TDD RED phase)
- **Issue:** Plan test case had zero as current value (numerator) not prior value (denominator). Zero numerator is valid math (-100%), zero denominator is the actual division-by-zero edge case.
- **Fix:** Changed test input from [100, 0, 50] to [100, 50, 0] to test actual zero denominator
- **Files modified:** tests/test_xbrl_trends.py
- **Verification:** Test passes, confirms zero denominator returns None
- **Committed in:** fc17a90

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Corrected test case to match spec intent. No scope creep.

## Issues Encountered
- Pre-existing test failure in tests/knowledge/test_enriched_roundtrip.py (unrelated to this plan)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- TrendResult and compute_all_trends ready for integration in 68-03 (pipeline wiring)
- All exports (TrendResult, compute_trends, compute_all_trends) available for import

---
*Phase: 68-quarterly-extraction*
*Completed: 2026-03-06*
