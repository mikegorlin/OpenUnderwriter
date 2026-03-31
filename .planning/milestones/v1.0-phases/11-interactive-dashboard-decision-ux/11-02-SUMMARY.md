---
phase: 11-interactive-dashboard-decision-ux
plan: 02
subsystem: dashboard
tags: [plotly, charts, fastapi, jinja2, interactive-visualization]

# Dependency graph
requires:
  - phase: 11-01
    provides: "FastAPI app factory, state API, index template, dashboard.js loadChart()"
  - phase: 06
    provides: "ScoringResult with 10 factor scores, red flags, tier classification"
  - phase: 03
    provides: "ExtractedFinancials with DistressIndicators (Z/O/M/F scores)"
provides:
  - "Plotly chart builder functions for risk radar, heatmap, factor bars, gauges"
  - "Financial chart builders for distress gauges, peer comparison, red flags"
  - "7 chart API endpoints returning Plotly JSON for client-side rendering"
  - "Reusable chart container Jinja2 macro with data-chart-url pattern"
  - "Index page with interactive chart sections (risk, factor, financial, red flags)"
affects: [11-03, future-phases-needing-dashboard-charts]

# Tech tracking
tech-stack:
  added: [plotly]
  patterns: ["Chart API endpoint pattern: fig.to_dict() -> JSONResponse", "empty_figure() fallback for missing data", "Chart macro with data-chart-url for JS discovery"]

key-files:
  created:
    - src/do_uw/dashboard/charts.py
    - src/do_uw/dashboard/charts_financial.py
    - src/do_uw/templates/dashboard/partials/_chart_container.html
    - tests/test_dashboard_charts.py
  modified:
    - src/do_uw/dashboard/app.py
    - src/do_uw/templates/dashboard/index.html

key-decisions:
  - "empty_figure() made public for cross-module use (app.py distress endpoint needs it for unknown model fallback)"
  - "Plotly figures typed as Any throughout for pyright strict (plotly is untyped)"
  - "Risk fraction scale (0-1) for radar and heatmap, not raw point deductions"
  - "Distress gauges use model-specific axis ranges (Z: 0-5, O: 0-1, M: -3.5-0, F: 0-9)"
  - "Red flag chart uses ceiling_applied as bar value (impact severity visualization)"

patterns-established:
  - "Chart builder pattern: accept AnalysisState, return Any (Plotly Figure), handle None with empty_figure()"
  - "Chart API pattern: GET /api/chart/{name} -> JSONResponse(fig.to_dict())"
  - "Chart template macro: {{ chart(id, url, title, height) }} with data-chart-url attribute"
  - "_get_state() helper in app.py for hot-reload check before chart generation"

# Metrics
duration: 6min
completed: 2026-02-10
---

# Phase 11 Plan 02: Interactive Charts Summary

**Plotly risk radar, heatmap, distress gauges, factor bars, and red flag charts with 7 JSON API endpoints and reusable Jinja2 chart macro**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-10T02:46:09Z
- **Completed:** 2026-02-10T02:51:56Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- 5 core chart builders: risk radar (spider), risk heatmap, factor bar chart, score gauge, tier gauge
- 3 financial chart builders: distress gauges (4 models), peer comparison bars, red flag summary
- 7 API endpoints serving Plotly JSON for client-side interactive rendering
- 20 new tests (11 direct chart builder + 9 API endpoint tests), 1623 total passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Plotly chart builder modules** - `09c2663` (feat)
2. **Task 2: Chart API endpoints, template, tests** - `0fe2138` (feat)

## Files Created/Modified
- `src/do_uw/dashboard/charts.py` (335L) - Risk radar, heatmap, factor bars, score/tier gauges
- `src/do_uw/dashboard/charts_financial.py` (312L) - Distress gauges, peer comparison, red flags
- `src/do_uw/dashboard/app.py` (222L) - Added 7 chart API endpoints and chart imports
- `src/do_uw/templates/dashboard/partials/_chart_container.html` - Reusable chart div macro
- `src/do_uw/templates/dashboard/index.html` - Chart sections: risk overview, factor analysis, financial health, red flags
- `tests/test_dashboard_charts.py` (264L) - 20 tests for chart builders and API endpoints

## Decisions Made
- `empty_figure()` made public (not private `_empty_figure`) because app.py needs it for unknown distress model fallback
- Risk fraction (0-1) scale for radar/heatmap instead of raw deductions -- makes factors comparable regardless of max_points
- Distress gauge axis ranges tailored per model (Z-Score 0-5, O-Score 0-1, M-Score -3.5-0, F-Score 0-9)
- Red flag summary uses ceiling_applied as bar value to visualize impact severity
- Brand colors from design.py used consistently (navy #1A1446, gold #FFD000, risk spectrum without green)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed f-string without placeholders**
- **Found during:** Task 1 (charts.py fillcolor)
- **Issue:** `f"rgba(26, 20, 70, 0.15)"` had no interpolation
- **Fix:** Removed `f` prefix
- **Files modified:** src/do_uw/dashboard/charts.py
- **Verification:** ruff check passes
- **Committed in:** 0fe2138 (part of Task 2 commit after fix)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor lint fix. No scope creep.

## Issues Encountered
None - plan executed as specified.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All chart types are live and testable via the dashboard
- Chart container macro pattern ready for reuse in Plan 03 section drill-downs
- Index page has full interactive visualization suite
- Ready for Plan 03: Section detail panels with htmx drill-down

---
*Phase: 11-interactive-dashboard-decision-ux*
*Completed: 2026-02-10*
