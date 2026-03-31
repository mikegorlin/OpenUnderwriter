---
phase: 133-stock-and-market-intelligence
plan: 01
subsystem: extract, render
tags: [earnings-reactions, correlation, r-squared, chart-computations, pydantic, stock]

# Dependency graph
requires: []
provides:
  - "EarningsQuarterRecord with next_day_return_pct and week_return_pct fields"
  - "compute_earnings_reactions() for multi-window return computation"
  - "compute_correlation() and compute_r_squared() in chart_computations.py"
affects: [133-02-stock-and-market-intelligence]

# Tech tracking
tech-stack:
  added: []
  patterns: ["yfinance dict-of-dicts extraction pattern reused from volume_spikes.py"]

key-files:
  created:
    - src/do_uw/stages/extract/earnings_reactions.py
    - tests/stages/extract/test_earnings_reactions.py
    - tests/stages/render/test_chart_computations_correlation.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/stages/render/charts/chart_computations.py

key-decisions:
  - "Reused existing compute_daily_returns() for correlation instead of adding duplicate"
  - "Returns measured from pre-earnings close (T-1) not earnings-day open for full reaction capture"
  - "30-observation minimum for correlation matches existing idiosyncratic_vol threshold"

patterns-established:
  - "Multi-window return computation: day-of, next-day, week relative to pre-event close"

requirements-completed: [STOCK-04, STOCK-08]

# Metrics
duration: 4min
completed: 2026-03-27
---

# Phase 133 Plan 01: Backend Computation Layer Summary

**Multi-window earnings reaction returns and Pearson correlation/R-squared computations for stock intelligence**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-27T04:10:30Z
- **Completed:** 2026-03-27T04:14:25Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Extended EarningsQuarterRecord with next_day_return_pct and week_return_pct fields (backward compatible)
- Created compute_earnings_reactions() computing day-of, next-day, and 1-week returns for each earnings date
- Added compute_correlation() and compute_r_squared() to chart_computations.py for return correlation metrics
- 19 new tests, 48 total tests passing with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend EarningsQuarterRecord + create earnings_reactions.py**
   - `21eb3980` (test: failing tests for earnings reactions)
   - `d2231628` (feat: earnings reaction computation with multi-window returns)
2. **Task 2: Add compute_correlation() and compute_r_squared()**
   - `bc579176` (test: failing tests for correlation and R-squared)
   - `65a7a7a3` (feat: correlation and R-squared computations)

## Files Created/Modified
- `src/do_uw/models/market_events.py` - Added next_day_return_pct and week_return_pct to EarningsQuarterRecord
- `src/do_uw/stages/extract/earnings_reactions.py` - New module: multi-window earnings return computation
- `src/do_uw/stages/render/charts/chart_computations.py` - Added compute_correlation() and compute_r_squared()
- `tests/stages/extract/test_earnings_reactions.py` - 11 tests for earnings reactions
- `tests/stages/render/test_chart_computations_correlation.py` - 8 tests for correlation/R-squared

## Decisions Made
- Reused existing compute_daily_returns() in chart_computations.py instead of creating a duplicate function as the plan template suggested
- All returns are computed relative to pre-earnings close (T-1) to capture the full market reaction including after-hours moves
- 30-observation minimum for correlation computation matches the existing threshold in compute_idiosyncratic_vol()

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed inverse correlation test expectation**
- **Found during:** Task 2 (correlation tests)
- **Issue:** Plan's additive price moves don't create perfectly inverse returns in return space
- **Fix:** Changed test to use multiplicative returns for proper inverse correlation
- **Files modified:** tests/stages/render/test_chart_computations_correlation.py
- **Verification:** Test now correctly validates correlation < -0.9

**2. [Rule 1 - Bug] Fixed SourcedValue constructor in tests**
- **Found during:** Task 1 (model field tests)
- **Issue:** SourcedValue requires as_of datetime field not shown in plan's interface spec
- **Fix:** Added as_of parameter to SourcedValue construction in tests
- **Files modified:** tests/stages/extract/test_earnings_reactions.py
- **Verification:** All model tests pass

---

**Total deviations:** 2 auto-fixed (2 bug fixes in tests)
**Impact on plan:** Minor test adjustments for correctness. No scope creep.

## Issues Encountered
None - implementation straightforward.

## Known Stubs
None - all functions fully implemented with real computation logic.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 can now use compute_earnings_reactions() for context builders
- Plan 02 can use compute_correlation() and compute_r_squared() for metrics cards
- All model fields backward compatible (default=None)

## Self-Check: PASSED

All 5 files verified present. All 4 commits verified in git log. All 5 content patterns confirmed.

---
*Phase: 133-stock-and-market-intelligence*
*Completed: 2026-03-27*
