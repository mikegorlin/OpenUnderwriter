---
phase: 37-stock-charts-price-history-drop-analysis
plan: 01
subsystem: extract
tags: [yfinance, stock-drops, sector-etf, spy-benchmark, recovery-time, market-wide-events]

# Dependency graph
requires:
  - phase: 04-market-analysis
    provides: "yfinance market data client, stock drop detection"
provides:
  - "Sector ETF history acquisition (1Y/5Y) via brain/sectors.json mapping"
  - "S&P 500 (SPY) benchmark history acquisition (1Y/5Y)"
  - "StockDropEvent enhanced with recovery_days, is_market_wide, trigger_source_url, cumulative_pct"
  - "Recovery time computation (trading days to pre-drop price level)"
  - "Consecutive drop grouping into multi-day events"
  - "Market-wide event tagging using SPY correlation"
affects: [37-02, 37-03, 37-04, render]

# Tech tracking
tech-stack:
  added: []
  patterns: ["sector ETF resolution via brain/sectors.json", "SPY benchmark comparison for market-wide tagging"]

key-files:
  created:
    - "src/do_uw/stages/extract/stock_drop_analysis.py"
  modified:
    - "src/do_uw/stages/acquire/clients/market_client.py"
    - "src/do_uw/models/market_events.py"
    - "src/do_uw/stages/extract/stock_drops.py"
    - "src/do_uw/stages/extract/stock_performance.py"

key-decisions:
  - "Split new analysis functions into stock_drop_analysis.py for 500-line compliance"
  - "Preserve original single-day drops for worst_single_day identification after grouping"
  - "Use 4-calendar-day gap threshold for consecutive drop grouping to handle weekends"
  - "Fall back to legacy sector_history key when sector_history_1y not present"

patterns-established:
  - "Sector ETF resolution: yfinance sector name -> brain/sectors.json code -> ETF ticker"
  - "Market-wide tagging: SPY return on same day <= -3% flags event as market-wide"

requirements-completed: []

# Metrics
duration: 15min
completed: 2026-02-21
---

# Phase 37 Plan 01: Sector ETF + SPY Data Acquisition and Enhanced Drop Analysis Summary

**Sector ETF/SPY benchmark acquisition via brain/sectors.json mapping, with recovery time, consecutive-drop grouping, and market-wide event tagging for stock drop analysis**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-21T17:54:10Z
- **Completed:** 2026-02-21T18:09:12Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Market client now acquires sector ETF (1Y/5Y) and S&P 500 (1Y/5Y) history alongside company data
- StockDropEvent model enhanced with 4 new fields: recovery_days, is_market_wide, trigger_source_url, cumulative_pct
- Three new analysis functions: compute_recovery_days, group_consecutive_drops, tag_market_wide_events
- Full pipeline wired: stock_performance.py orchestrates recovery, grouping, and market-wide tagging during extraction
- attribute_triggers() now populates trigger_source_url from 8-K accession numbers (SEC EDGAR URLs)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add sector ETF and SPY history acquisition to market_client.py** - `85746cf` (feat)
2. **Task 2: Enhance StockDropEvent model and add recovery/grouping/market-wide analysis** - `9ae2474` (feat)

## Files Created/Modified
- `src/do_uw/stages/acquire/clients/market_client.py` - Added _resolve_sector_etf(), sector ETF + SPY 1Y/5Y history acquisition (322 lines)
- `src/do_uw/models/market_events.py` - Added recovery_days, is_market_wide, trigger_source_url, cumulative_pct to StockDropEvent (470 lines)
- `src/do_uw/stages/extract/stock_drops.py` - Updated _get_8k_dates to return accession numbers, attribute_triggers to populate trigger_source_url (376 lines)
- `src/do_uw/stages/extract/stock_drop_analysis.py` - NEW: compute_recovery_days, group_consecutive_drops, tag_market_wide_events (220 lines)
- `src/do_uw/stages/extract/stock_performance.py` - Wired recovery, grouping, market-wide tagging into extraction pipeline (480 lines)

## Decisions Made
- **500-line split**: New analysis functions (recovery, grouping, market-wide) placed in new `stock_drop_analysis.py` rather than extending stock_drops.py beyond 500 lines
- **Preserve worst_single_day**: After grouping consecutive drops into multi-day events, the original ungrouped single-day drops are preserved for worst_single_day identification so existing behavior is maintained
- **4-day calendar gap**: Used 4-calendar-day gap threshold for consecutive drop grouping to properly handle weekends (2 consecutive trading days separated by a weekend = 4 calendar days)
- **Backwards-compatible sector key**: stock_performance.py falls back to legacy `sector_history` key when `sector_history_1y` isn't present

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test failure from grouping converting all single-day drops to multi-day**
- **Found during:** Task 2 (wiring into stock_performance.py)
- **Issue:** group_consecutive_drops() converted all consecutive single-day drops to MULTI_DAY, causing worst_single_day to become None in existing test
- **Fix:** Preserved `original_single_drops` before grouping for worst_single_day identification
- **Files modified:** src/do_uw/stages/extract/stock_performance.py
- **Verification:** All 22 stock performance tests pass, 61/61 stock-related tests pass
- **Committed in:** 9ae2474 (Task 2 commit)

**2. [Rule 3 - Blocking] stock_drops.py exceeded 500-line limit**
- **Found during:** Task 2 (after adding new functions)
- **Issue:** stock_drops.py grew to 563 lines with new functions, violating CLAUDE.md anti-context-rot rule
- **Fix:** Extracted compute_recovery_days, group_consecutive_drops, _merge_group, tag_market_wide_events into new stock_drop_analysis.py (220 lines)
- **Files modified:** src/do_uw/stages/extract/stock_drops.py, src/do_uw/stages/extract/stock_drop_analysis.py, src/do_uw/stages/extract/stock_performance.py
- **Verification:** All files under 500 lines, all imports and tests pass
- **Committed in:** 9ae2474 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug fix, 1 blocking)
**Impact on plan:** Both necessary for correctness and code standards. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Sector ETF and SPY benchmark data now available for chart rendering (plans 02-04)
- Enhanced drop events (recovery time, cumulative %, market-wide tags) ready for detailed drop tables
- All existing tests pass (pre-existing brain_schema failure unrelated)

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 37-stock-charts-price-history-drop-analysis*
*Completed: 2026-02-21*
