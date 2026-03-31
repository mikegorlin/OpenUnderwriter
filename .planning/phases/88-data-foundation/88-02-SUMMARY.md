---
phase: 88-data-foundation
plan: 02
subsystem: render
tags: [return-decomposition, mdd-ratio, stock-charts, html-template, drawdown]

# Dependency graph
requires:
  - phase: 88-01
    provides: "Return decomposition fields and MDD ratio on StockPerformance model"
provides:
  - Return attribution table in HTML stock analysis output (1Y + 5Y)
  - MDD ratio comparison cards with color-coded severity
  - Drawdown chart header enriched with sector MDD and MDD ratio
  - compute_chart_stats extended with decomposition/MDD from state
affects: [89-stock-analysis, 90-display-centralization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "State-to-chart-stats bridge: compute_chart_stats reads decomposition from state when provided"
    - "Color-coded MDD ratio cards: green (<1.0x), amber (1.0-1.5x), red (>1.5x)"

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/charts/stock_chart_data.py
    - src/do_uw/stages/render/charts/drawdown_chart.py
    - src/do_uw/stages/render/charts/stock_charts.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2

key-decisions:
  - "compute_chart_stats takes optional state param for backward compatibility — callers without state get original behavior"
  - "MDD ratio cards use three-tier color coding (green/amber/red) matching existing D&O risk flag patterns"
  - "Return attribution table placed between stock charts and drop event analysis for logical flow"

patterns-established:
  - "State-enriched chart stats: pass state to compute_chart_stats when available for decomposition data"
  - "Template-level conditional rendering: only show decomposition/MDD if data exists (graceful degradation)"

requirements-completed: [STOCK-07, STOCK-01, STOCK-03]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 88 Plan 02: Rendering Data Foundation Summary

**Return decomposition table and MDD ratio comparison cards added to HTML stock analysis output with color-coded severity and drawdown chart enrichment**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T05:18:56Z
- **Completed:** 2026-03-09T05:23:32Z
- **Tasks:** 2 (1 auto + 1 checkpoint auto-approved)
- **Files modified:** 5

## Accomplishments
- Extended compute_chart_stats() with return decomposition (market, sector, company-specific) and MDD ratio from state
- Added MDD ratio and sector MDD display to drawdown chart stats header with red highlighting for elevated ratios
- Added Return Attribution HTML table showing 1Y and 5Y three-component breakdown with color-coded company-specific returns
- Added MDD Ratio comparison cards near drawdown charts with green/amber/red severity tiers
- Added _extract_return_decomposition() context builder feeding 8 new template variables

## Task Commits

Each task was committed atomically:

1. **Task 1: Add decomposition + MDD ratio to chart stats and template** - `6fae940` (feat)
2. **Task 2: Verify data foundation output quality** - auto-approved checkpoint (no commit)

## Files Created/Modified
- `src/do_uw/stages/render/charts/stock_chart_data.py` - Extended compute_chart_stats with state param for decomposition/MDD data
- `src/do_uw/stages/render/charts/drawdown_chart.py` - Added _get_mdd_context() and MDD ratio/sector MDD to header stats
- `src/do_uw/stages/render/charts/stock_charts.py` - Updated compute_chart_stats caller to pass state
- `src/do_uw/stages/render/html_renderer.py` - Added _extract_return_decomposition() context builder
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` - Return Attribution table + MDD Ratio cards

## Decisions Made
- compute_chart_stats takes optional state param for backward compatibility
- MDD ratio cards use three-tier color coding matching existing risk flag patterns
- Return attribution table placed between stock charts and drop analysis for logical reading flow

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 3 pre-existing test failures in render suite (test_5layer_narrative, test_html_layout, test_html_renderer) related to 'cm' undefined Jinja2 variable in market template — not caused by this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Return decomposition and MDD ratio are now visible in HTML output
- Phase 89 (stock analysis engine) can build on this display foundation
- Phase 90 (display centralization) has render patterns to follow

---
*Phase: 88-data-foundation*
*Completed: 2026-03-09*
