---
phase: 143-stock-charts
plan: 01
subsystem: render
tags: [matplotlib, stock-charts, litigation, overlays, chart-data]

# Dependency graph
requires:
  - phase: 91-chart-registry
    provides: chart style registry YAML and resolve_colors infrastructure
provides:
  - litigation_events field on ChartData dataclass
  - render_litigation_markers overlay function
  - orange dash-dot litigation markers on stock charts
affects: [stock-charts, chart-overlays, chart-data]

# Tech tracking
tech-stack:
  added: []
  patterns: ["litigation event extraction from AnalysisState following earnings_events pattern"]

key-files:
  created:
    - tests/stages/render/test_stock_chart_events.py
  modified:
    - src/do_uw/stages/render/charts/stock_chart_data.py
    - src/do_uw/stages/render/charts/stock_chart_overlays.py
    - src/do_uw/stages/render/charts/stock_charts.py
    - src/do_uw/brain/config/chart_styles.yaml

key-decisions:
  - "Combined securities_class_actions and derivative_suits as litigation event sources"
  - "Orange (#FF6D00 dark, #E65100 light) dash-dot lines distinguish from earnings gray dashes and drop red/yellow dots"

patterns-established:
  - "Litigation event extraction pattern: read CaseDetail.filing_date SourcedValues, filter by chart date range, convert to event dicts"

requirements-completed: [CHART-04]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 143 Plan 01: Litigation Filing Date Annotations on Stock Charts Summary

**Litigation filing dates render as orange dash-dot vertical lines with abbreviated case names on both 1Y and 5Y stock charts**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T04:54:50Z
- **Completed:** 2026-03-28T05:00:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- ChartData.litigation_events field extracts filing dates from securities_class_actions and derivative_suits
- render_litigation_markers draws orange dash-dot vertical lines with "L" label and abbreviated case name
- Litigation colors added to dark/light themes and stock chart overlay configuration
- 9 TDD tests covering extraction, filtering, rendering, and integration
- Zero regressions: all 21 existing stock chart tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add litigation_events to ChartData and extract from state** - `884848bb` (feat)
2. **Task 2: Render litigation markers on charts and wire into create_stock_chart** - `ddfef7b4` (feat)

## Files Created/Modified
- `tests/stages/render/test_stock_chart_events.py` - 9 tests for litigation event extraction and rendering
- `src/do_uw/stages/render/charts/stock_chart_data.py` - Added litigation_events field and _extract_litigation_events()
- `src/do_uw/stages/render/charts/stock_chart_overlays.py` - Added render_litigation_markers() with orange dash-dot style
- `src/do_uw/stages/render/charts/stock_charts.py` - Wired render_litigation_markers into create_stock_chart
- `src/do_uw/brain/config/chart_styles.yaml` - Added litigation_line/litigation_text to both themes and stock overlays

## Decisions Made
- Combined securities_class_actions and derivative_suits as event sources (both are CaseDetail with filing_date)
- Used coverage_type SourcedValue for case_type extraction (matches CaseDetail model)
- Orange #FF6D00 (dark) / #E65100 (light) chosen for visibility against dark navy and white backgrounds

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SourcedValue requires as_of field in tests**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Test helper created SourcedValue without required as_of field
- **Fix:** Added as_of="2025-01-01" to test helper _sv() function
- **Files modified:** tests/stages/render/test_stock_chart_events.py
- **Verification:** All 5 tests pass
- **Committed in:** 884848bb (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test-only fix, no impact on scope.

## Issues Encountered
None.

## Known Stubs
None - all data paths are fully wired to state.extracted.litigation.

## Next Phase Readiness
- Litigation markers ready for visual verification on real ticker output
- Plan 02 (if any) can build on this overlay infrastructure

---
*Phase: 143-stock-charts*
*Completed: 2026-03-28*
