---
phase: 37-stock-charts-price-history-drop-analysis
plan: 02
subsystem: render
tags: [matplotlib, bloomberg-dark-theme, stock-charts, dual-axis, area-charts, drop-markers]

# Dependency graph
requires:
  - phase: 37-01
    provides: "Sector ETF + SPY data acquisition, enhanced StockDropEvent with recovery_days/is_market_wide"
provides:
  - "Bloomberg dark theme stock chart renderer with dual-axis area fills"
  - "stock_chart_data.py data extraction layer reading correct market_data keys"
  - "Stats header with price, 52W H/L, returns, alpha"
  - "Drop markers (yellow 5-10%, red 10%+) and divergence bands"
  - "BLOOMBERG_DARK color palette in design_system.py"
affects: [37-03, 37-04, render]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Bloomberg Terminal dark theme chart styling", "dual-axis area chart with green/red conditional fills", "chart data extraction separated from rendering"]

key-files:
  created:
    - "src/do_uw/stages/render/charts/stock_chart_data.py"
  modified:
    - "src/do_uw/stages/render/charts/stock_charts.py"
    - "src/do_uw/stages/render/design_system.py"
    - "tests/test_render_sections_3_4.py"

key-decisions:
  - "Split data extraction into stock_chart_data.py (316 lines) and rendering into stock_charts.py (463 lines) for 500-line compliance"
  - "Use fill_between with where clause and interpolate=True for green/red conditional area fills"
  - "Divergence bands compare company vs ETF on indexed scale, shade when >10 points apart"
  - "5Y charts filter drops to >10% single-day or >15% cumulative only"

patterns-established:
  - "Bloomberg dark theme: plt.style.use('dark_background') then override with BLOOMBERG_DARK colors"
  - "Dual-axis charts: company dollar price on left (ax), indexed overlays on right (ax2 via twinx)"
  - "Stats header via fig.add_axes() at top 10% of figure, separate from main chart axes"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 37 Plan 02: Bloomberg Dark Theme Stock Chart Renderer Summary

**Bloomberg Terminal-inspired dual-axis area charts with green/red conditional fills, sector ETF + S&P 500 overlays, stats header, drop markers, and divergence bands**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T18:11:52Z
- **Completed:** 2026-02-21T18:17:15Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- New stock_chart_data.py separates data extraction from rendering, reading correct keys (history_1y/5y, sector_history_1y/5y, spy_history_1y/5y) -- fixes the fundamental key mismatch that made all charts return None
- Complete rewrite of stock_charts.py with Bloomberg dark theme: dual-axis area charts, green/red conditional fills, stats header, drop markers, divergence bands
- BLOOMBERG_DARK color palette (15 colors) added to design_system.py as single source of truth for chart colors
- Backward-compatible: create_stock_performance_chart and create_stock_performance_chart_5y still exported and delegate to new create_stock_chart

## Task Commits

Each task was committed atomically:

1. **Task 1: Create stock_chart_data.py and Bloomberg colors** - `c7fdbc9` (feat)
2. **Task 2: Rewrite stock_charts.py with Bloomberg dark theme** - `03c14ba` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/charts/stock_chart_data.py` - NEW: ChartData dataclass, extract_chart_data(), compute_chart_stats(), index_to_base(), aggregate_weekly() (316 lines)
- `src/do_uw/stages/render/charts/stock_charts.py` - REWRITTEN: Bloomberg dark theme with 8 sub-systems (463 lines)
- `src/do_uw/stages/render/design_system.py` - Added BLOOMBERG_DARK color dict and __all__ export (220 lines)
- `tests/test_render_sections_3_4.py` - Updated test data to column-oriented format with correct keys

## Decisions Made
- **Data/rendering split**: stock_chart_data.py (316 lines) handles all data extraction and stats computation; stock_charts.py (463 lines) handles all matplotlib rendering. Neither exceeds 500 lines.
- **Conditional fill approach**: Using fill_between with where clause and interpolate=True for smooth green/red transitions at the starting price level.
- **Divergence bands on indexed scale**: Both company and ETF indexed to 100 on the right axis for fair comparison, bands shade when gap exceeds 10 indexed points.
- **5Y drop filtering**: 5Y charts only show drops >10% single-day or >15% cumulative to avoid clutter with weekly aggregation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test data format for stock chart tests**
- **Found during:** Task 2 (verification step)
- **Issue:** Existing tests used old data format (price_history key with {date, close} dicts) but new code reads history_1y with column-oriented {Date: [...], Close: [...]} format
- **Fix:** Updated _make_rich_state() test helper to use correct column-oriented format with history_1y, sector_history_1y, spy_history_1y keys and sufficient data points (13 entries)
- **Files modified:** tests/test_render_sections_3_4.py
- **Verification:** All 4 stock chart tests pass
- **Committed in:** 03c14ba (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking -- test data format mismatch)
**Impact on plan:** Necessary for tests to pass with new data key format. No scope creep.

## Issues Encountered
None beyond the auto-fixed test data update.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Bloomberg dark theme charts now render with all 8 visual features (theme, area fill, stats header, ETF overlay, SPY overlay, drop markers, divergence bands, backward compat)
- Chart generation reads correct data keys from Phase 37-01 acquisition
- Ready for Plan 03 (chart-to-disk pipeline) and Plan 04 (drop detail tables)

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 37-stock-charts-price-history-drop-analysis*
*Completed: 2026-02-21*
