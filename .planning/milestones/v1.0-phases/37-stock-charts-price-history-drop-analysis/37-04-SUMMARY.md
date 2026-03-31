---
phase: 37-stock-charts-price-history-drop-analysis
plan: 04
subsystem: testing
tags: [pytest, sector-etf, stock-drops, recovery-time, market-wide-events, chart-generation, png, matplotlib]

# Dependency graph
requires:
  - phase: 37-01
    provides: "Sector ETF resolution, enhanced StockDropEvent model"
  - phase: 37-02
    provides: "Bloomberg dark theme chart renderer, stock_chart_data.py extraction layer"
  - phase: 37-03
    provides: "Chart pipeline to disk, drop detail tables"
provides:
  - "13 ETF resolution tests covering all 11 yfinance sectors + unknown + empty edge cases"
  - "12 enhanced drop analysis tests: recovery time, consecutive grouping, market-wide tagging"
  - "18 chart generation tests: data extraction, PNG output, 5Y weekly, stats, backward compat, template embedding"
affects: [render, extract, acquire]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Synthetic price history generator for chart tests", "Project root detection via pyproject.toml for template path resolution"]

key-files:
  created:
    - "tests/stages/acquire/test_market_client_etf.py"
    - "tests/stages/extract/test_stock_drops_enhanced.py"
    - "tests/stages/render/test_stock_charts.py"
  modified: []

key-decisions:
  - "Used project root detection via pyproject.toml traversal for template path resolution"
  - "Covered all 11 yfinance sector mappings (not just 5) for comprehensive ETF resolution testing"
  - "Added boundary test for SPY -3% threshold (exact boundary is_market_wide = True)"

patterns-established:
  - "Synthetic price history helper: _make_price_history(n_days, start_price, daily_return) generates column-oriented dicts"
  - "Project root detection: traverse parents looking for pyproject.toml"

requirements-completed: []

# Metrics
duration: 6min
completed: 2026-02-21
---

# Phase 37 Plan 04: Phase 37 Test Suite Summary

**43 new tests across 3 test files covering sector ETF resolution, enhanced drop analysis (recovery/grouping/market-wide), and Bloomberg chart generation pipeline (PNG output, data keys, weekly aggregation, stats, template embedding)**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-21T18:27:46Z
- **Completed:** 2026-02-21T18:33:48Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- 13 sector ETF resolution tests verifying all 11 yfinance sector-to-ETF mappings plus unknown/empty edge cases
- 12 enhanced drop analysis tests covering recovery time (normal, never-recovered, single-day, immediate, OOB), consecutive drop grouping (merge, separate, empty), and market-wide SPY correlation tagging (threshold boundary, no data)
- 18 chart generation pipeline tests covering correct key usage (history_1y not price_history), PNG signature verification, 5Y weekly aggregation, stats computation, backward-compatible exports, and template chart embedding across MD, HTML, and PDF templates

## Task Commits

Each task was committed atomically:

1. **Task 1: Add tests for sector ETF resolution and enhanced drop analysis** - `6a1d8de` (test)
2. **Task 2: Add tests for chart generation pipeline and end-to-end integration** - `995d1d2` (test)

## Files Created/Modified
- `tests/stages/acquire/test_market_client_etf.py` - NEW: 13 ETF resolution tests (68 lines)
- `tests/stages/extract/test_stock_drops_enhanced.py` - NEW: 12 recovery/grouping/market-wide tests (197 lines)
- `tests/stages/render/test_stock_charts.py` - NEW: 18 chart pipeline tests with synthetic data helpers (451 lines)

## Decisions Made
- **Project root detection**: Used pyproject.toml traversal for template path resolution instead of relative parent counting, which broke when test file depth changed
- **Comprehensive sector coverage**: Tested all 11 yfinance sector-to-ETF mappings (Technology through Communication Services), not just the 5 examples in the plan
- **Boundary value testing**: Added SPY exactly -3.0% test to verify the `<=` threshold boundary for market-wide event tagging

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed template path resolution in chart embedding tests**
- **Found during:** Task 2 (template embedding tests)
- **Issue:** Path resolution using `Path(__file__).resolve().parent.parent.parent / "src"` navigated to `tests/` directory instead of project root, because the test file is 4 levels deep (tests/stages/render/test_stock_charts.py)
- **Fix:** Replaced with `_project_root()` helper that traverses parents looking for `pyproject.toml`
- **Files modified:** tests/stages/render/test_stock_charts.py
- **Verification:** All 3 template embedding tests pass
- **Committed in:** 995d1d2 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary for correct path resolution. No scope creep.

## Issues Encountered
- Pre-existing test failures in brain/checks.json-related tests (test_brain_enrich, test_loader, test_check_classification, test_phase26_integration) due to unstaged checks.json modifications. Not caused by this plan's changes. Documented in 37-03-SUMMARY as well.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 37 is now fully complete: 4 plans covering acquisition, rendering, pipeline, and tests
- 43 new tests provide coverage for all Phase 37 functionality
- All pre-existing render tests (test_render_sections_3_4.py) continue to pass

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 37-stock-charts-price-history-drop-analysis*
*Completed: 2026-02-21*
