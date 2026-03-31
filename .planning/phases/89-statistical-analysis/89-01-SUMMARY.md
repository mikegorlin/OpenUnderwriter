---
phase: 89-statistical-analysis
plan: 01
subsystem: analysis
tags: [ddl, abnormal-return, ewma, volatility-regime, event-study, pure-python]

# Dependency graph
requires:
  - phase: 88-data-foundation
    provides: "chart_computations.py infrastructure, return decomposition, MDD ratio"
provides:
  - "compute_ddl_exposure: DDL/MDL dollar exposure from market cap and worst drop"
  - "compute_abnormal_return: market model AR with t-stat significance testing"
  - "compute_ewma_volatility: EWMA vol series (lambda=0.94, annualized)"
  - "classify_vol_regime: percentile-based regime classification with duration"
  - "Model fields on StockPerformance (3), StockDropEvent (5), StockDropAnalysis (3)"
affects: [89-02, rendering, extraction, scoring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "EWMA exponential decay (lambda=0.94 RiskMetrics standard)"
    - "Market model event study (Brown & Warner 1985)"
    - "Percentile-based regime classification on company's own history"

key-files:
  created:
    - tests/stages/render/charts/test_chart_computations.py
    - tests/models/test_market_fields.py
  modified:
    - src/do_uw/stages/render/charts/chart_computations.py
    - src/do_uw/models/market.py
    - src/do_uw/models/market_events.py

key-decisions:
  - "DDL uses abs(worst_drop_pct) so both positive and negative inputs work"
  - "EWMA seeds with first return squared, then decays with lambda=0.94"
  - "Regime thresholds are percentile-based (25/75/90) on company's own EWMA history"
  - "Abnormal return requires minimum 60 observations in estimation window"
  - "classify_vol_regime skips zero-valued entries when computing percentiles"

patterns-established:
  - "Event study pattern: estimation window with gap before event day"
  - "Regime classification with duration counting from series end"

requirements-completed: [STOCK-02, STOCK-04, STOCK-05]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 89 Plan 01: Statistical Analysis Computations Summary

**Four pure-Python statistical functions (DDL exposure, abnormal return event study, EWMA volatility, regime classification) with 11 new model fields and 43 tests**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T12:27:09Z
- **Completed:** 2026-03-09T12:30:40Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- DDL/MDL exposure computation with configurable settlement ratio (default 1.8%)
- Market model abnormal return with t-statistic significance testing (120-day estimation, 5-day gap)
- EWMA volatility series (lambda=0.94) producing annualized vol percentages
- Percentile-based regime classifier (LOW/NORMAL/ELEVATED/CRISIS) with consecutive-day duration
- 11 new model fields across StockPerformance, StockDropEvent, StockDropAnalysis -- all backward-compatible

## Task Commits

Each task was committed atomically:

1. **Task 1: Add model fields for DDL exposure, abnormal returns, and EWMA volatility** - `24ad925` (feat)
2. **Task 2: Implement DDL, abnormal return, EWMA, and regime computation functions with tests** - `04268da` (feat)

_Both tasks followed TDD: RED (failing tests) then GREEN (implementation)._

## Files Created/Modified
- `src/do_uw/stages/render/charts/chart_computations.py` - Added 4 new computation functions
- `src/do_uw/models/market.py` - Added ewma_vol_current, vol_regime, vol_regime_duration_days to StockPerformance
- `src/do_uw/models/market_events.py` - Added AR fields to StockDropEvent, DDL fields to StockDropAnalysis
- `tests/stages/render/charts/test_chart_computations.py` - 29 tests for new computation functions
- `tests/models/test_market_fields.py` - 14 tests for new model field defaults and backward compat

## Decisions Made
- DDL uses abs(worst_drop_pct) to handle both positive and negative percentage inputs uniformly
- EWMA seeds with first return squared then applies exponential decay (not windowed average)
- Regime thresholds are relative to company's own EWMA vol history (not fixed absolute thresholds)
- Abnormal return computation returns None (not zero) when data is insufficient for reliable estimates
- Zero-value EWMA entries are excluded from percentile computation to avoid skewing regime boundaries

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four computation functions ready for integration in Plan 02
- Model fields ready to receive computed values during extraction
- Plan 02 will wire computations into stock_performance.py extraction and chart rendering

---
*Phase: 89-statistical-analysis*
*Completed: 2026-03-09*
