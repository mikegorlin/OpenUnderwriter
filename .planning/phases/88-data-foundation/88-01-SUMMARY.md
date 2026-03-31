---
phase: 88-data-foundation
plan: 01
subsystem: extract
tags: [yfinance, return-decomposition, mdd-ratio, stock-analysis, market-data]

# Dependency graph
requires: []
provides:
  - 2-year daily price history acquisition (company, sector ETF, SPY)
  - 3-component return decomposition (market, sector, company-specific)
  - MDD ratio computation (company drawdown vs sector drawdown)
  - 11 new StockPerformance model fields
affects: [89-stock-analysis, 90-display-centralization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Return decomposition: total = market (SPY) + sector (ETF - SPY) + residual (company - ETF)"
    - "MDD ratio with sector near-zero guard (>= -0.5% returns None)"
    - "2Y fallback pattern: prefer history_2y, fall back to history_1y"

key-files:
  created:
    - tests/stages/acquire/test_market_client_2y.py
    - tests/stages/extract/test_return_decomposition.py
    - tests/stages/extract/test_mdd_ratio.py
  modified:
    - src/do_uw/stages/acquire/clients/market_client.py
    - src/do_uw/models/market.py
    - src/do_uw/stages/render/charts/chart_computations.py
    - src/do_uw/stages/extract/stock_performance.py

key-decisions:
  - "compute_return_decomposition and compute_mdd_ratio placed in chart_computations.py for reuse by both extraction and chart rendering"
  - "_compute_performance_metrics takes optional market_data param for backward compatibility"

patterns-established:
  - "2Y fallback: prefer 2Y data, degrade to 1Y when unavailable"
  - "Sector MDD near-zero guard: -0.5% threshold prevents division by tiny denominators"

requirements-completed: [STOCK-07, STOCK-01, STOCK-03]

# Metrics
duration: 7min
completed: 2026-03-09
---

# Phase 88 Plan 01: Data Foundation Summary

**2-year daily data acquisition with 3-component return decomposition and peer-relative MDD ratio for stock analysis**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-09T05:10:27Z
- **Completed:** 2026-03-09T05:17:01Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended market_client to acquire 2-year daily price history for company, sector ETF, and SPY
- Added 11 new fields to StockPerformance model (6 decomposition, 5 MDD-related)
- Implemented compute_return_decomposition (market + sector + company = total, by construction)
- Implemented compute_mdd_ratio with sector near-zero drawdown guard
- Wired decomposition and MDD into extraction pipeline via _compute_performance_metrics
- Switched drop detection from 1Y to 2Y lookback window with 1Y fallback
- 18 new tests all passing, 1944 existing tests unaffected

## Task Commits

Each task was committed atomically:

1. **Task 1: Add 2Y acquisition + model fields + computation functions (RED)** - `729c796` (test)
2. **Task 1: Add 2Y acquisition + model fields + computation functions (GREEN)** - `b8b7715` (feat)
3. **Task 2: Wire decomposition + MDD ratio into extraction and switch drops to 2Y** - `657ff47` (feat)

## Files Created/Modified
- `src/do_uw/stages/acquire/clients/market_client.py` - Added history_2y, sector_history_2y, spy_history_2y acquisition
- `src/do_uw/models/market.py` - 11 new SourcedValue fields on StockPerformance
- `src/do_uw/stages/render/charts/chart_computations.py` - compute_return_decomposition and compute_mdd_ratio functions
- `src/do_uw/stages/extract/stock_performance.py` - Wired decomposition/MDD into extraction, 2Y drop detection
- `tests/stages/acquire/test_market_client_2y.py` - 3 tests for 2Y acquisition keys
- `tests/stages/extract/test_return_decomposition.py` - 7 tests for decomposition math
- `tests/stages/extract/test_mdd_ratio.py` - 8 tests for MDD ratio computation

## Decisions Made
- Placed compute_return_decomposition and compute_mdd_ratio in chart_computations.py rather than stock_performance.py so chart rendering can import them directly without circular dependency
- Made market_data parameter optional on _compute_performance_metrics for backward compatibility with any callers that pass positional args
- Used -0.5% as the sector MDD near-zero threshold (sector with less than 0.5% drawdown is not meaningful for ratio comparison)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Two pre-existing test failures found (test_brain_contract.py threshold_provenance, test_5layer_narrative.py market template) -- both confirmed pre-existing, unrelated to this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All new model fields populated during extraction when market data available
- Return decomposition and MDD ratio ready for display in stock analysis charts and tables
- Drop detection now uses 2Y lookback for better coverage of decline patterns

---
*Phase: 88-data-foundation*
*Completed: 2026-03-09*
