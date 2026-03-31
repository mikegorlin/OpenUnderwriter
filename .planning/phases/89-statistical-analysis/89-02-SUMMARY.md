---
phase: 89-statistical-analysis
plan: 02
subsystem: analysis
tags: [ddl, abnormal-return, ewma, volatility-regime, rendering, extraction-pipeline]

# Dependency graph
requires:
  - phase: 89-statistical-analysis
    plan: 01
    provides: "compute_ddl_exposure, compute_abnormal_return, compute_ewma_volatility, classify_vol_regime in chart_computations.py; model fields on StockPerformance, StockDropEvent, StockDropAnalysis"
provides:
  - "Extraction pipeline wiring: EWMA/regime, AR/t-stat, DDL/settlement populated during pipeline runs"
  - "Volatility chart: EWMA overlay with regime shading"
  - "Stock drops template: DDL card, AR columns, significance flags"
  - "Market context: exports EWMA, regime, DDL, settlement, AR fields for templates"
affects: [rendering, scoring, pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Decimal returns (chart_computations) vs percentage returns (stock_drops) distinction for market model"
    - "Regime shading via axvspan with percentile-based segment detection"
    - "Conditional AR columns in drop events table (only shown when data exists)"

key-files:
  created: []
  modified:
    - src/do_uw/stages/extract/stock_performance.py
    - src/do_uw/stages/render/charts/volatility_chart.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/templates/html/sections/market/stock_drops.html.j2
    - tests/stages/extract/test_stock_performance.py

key-decisions:
  - "Use chart_computations.compute_daily_returns (decimal) not stock_drops.compute_daily_returns (percentage) for AR market model"
  - "DDL exposure card placed in stock drops section (alongside worst drop context) rather than risk classification"
  - "AR/t-stat columns conditionally shown only when at least one drop has AR data"
  - "Regime shading drawn before volatility lines (zorder=0) so lines remain visible"
  - "Header stats layout compressed to 0.095 step width to accommodate regime item"

patterns-established:
  - "Return alignment: returns[i] corresponds to dates[offset + i + 1] when trimmed from end"
  - "Conditional template columns via Jinja2 selectattr filter on non-empty string"

requirements-completed: [STOCK-02, STOCK-04, STOCK-05]

# Metrics
duration: 9min
completed: 2026-03-09
---

# Phase 89 Plan 02: Statistical Analysis Integration Summary

**EWMA volatility overlay with regime shading on charts, DDL exposure card in stock drops section, and abnormal return significance flags per drop event -- all wired from computation functions into extraction pipeline and HTML rendering**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-09T12:33:39Z
- **Completed:** 2026-03-09T12:42:54Z
- **Tasks:** 2
- **Files modified:** 5 (+ 1 created)

## Accomplishments
- Extraction pipeline now populates ewma_vol_current, vol_regime, vol_regime_duration_days on StockPerformance during every run
- Abnormal return (AR), t-statistic, and significance flag computed per drop event using market model with decimal returns
- DDL/MDL exposure and 1.8% settlement estimate computed from worst observed drop and market cap
- Volatility chart shows EWMA vol (orange dashed) alongside rolling 30d vol with percentile-based regime background shading
- Stock drops HTML template displays DDL exposure card and AR/t-stat columns with significance markers
- 11 integration tests covering all extraction pipeline wiring paths

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire computations into extraction pipeline and add integration tests** - `55d3372` (feat)
2. **Task 2: Add EWMA line and regime shading to volatility chart, DDL display to pricing section, AR flags to drops** - `d4fd4de` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/stock_performance.py` - Added _compute_ewma_and_regime, _compute_abnormal_returns_for_drops, _compute_ddl_for_drops
- `src/do_uw/stages/render/charts/volatility_chart.py` - EWMA overlay, regime shading, regime in header stats
- `src/do_uw/stages/render/context_builders/market.py` - Exports DDL, settlement, AR, regime, EWMA fields
- `src/do_uw/templates/html/sections/market/stock_drops.html.j2` - DDL card, AR/t-stat columns, significance flags
- `tests/stages/extract/test_stock_performance.py` - 11 integration tests (EWMA, AR, DDL)

## Decisions Made
- Used decimal returns from chart_computations (not percentage returns from stock_drops) for market model AR computation -- the compute_abnormal_return function expects decimal scale
- Placed DDL exposure card in stock drops section rather than risk classification -- contextually belongs with worst drop data
- AR columns conditionally rendered only when at least one drop has AR data to avoid empty column noise
- Regime background shading uses same percentile thresholds as classify_vol_regime for consistency

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed decimal vs percentage return scale mismatch**
- **Found during:** Task 1 (abnormal return computation)
- **Issue:** stock_drops.compute_daily_returns returns percentage (x100), but compute_abnormal_return expects decimal returns
- **Fix:** Imported compute_daily_returns from chart_computations (decimal) as compute_decimal_returns
- **Files modified:** src/do_uw/stages/extract/stock_performance.py
- **Verification:** Integration tests pass with correct AR values
- **Committed in:** 55d3372

**2. [Rule 1 - Bug] Fixed return-to-date alignment offset**
- **Found during:** Task 1 (abnormal return date matching)
- **Issue:** returns[i] corresponds to the price transition from i to i+1, so date alignment needs offset+1
- **Fix:** Computed return_dates = dates[offset + 1 : offset + 1 + min_len] for correct date lookup
- **Files modified:** src/do_uw/stages/extract/stock_performance.py
- **Verification:** Test with known drop date correctly finds and computes AR
- **Committed in:** 55d3372

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes essential for correct AR computation. No scope creep.

## Issues Encountered
- Test initially used identical price patterns for company and SPY (same formula, different base), producing zero residuals and None AR. Fixed by using deterministic pseudo-random seeds for different return series.
- stock_performance.py is 915 lines (was 770 pre-changes). Pre-existing 500-line violation -- splitting is out of scope for this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 89 complete: all statistical analysis computations implemented and integrated
- Pipeline runs now populate all STOCK-02/04/05 fields
- Rendering shows all new data in charts and HTML templates
- Ready for Phase 90 (drop enhancements) or Phase 91 (display centralization)

---
*Phase: 89-statistical-analysis*
*Completed: 2026-03-09*
