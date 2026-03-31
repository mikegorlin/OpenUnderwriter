---
phase: 91-display-centralization
plan: 03
subsystem: render
tags: [jinja2, yaml, callout-templates, chart-thresholds, ci-lint, d&o-signals]

# Dependency graph
requires:
  - phase: 91-01
    provides: chart threshold extraction from signal YAML, thresholds context var
provides:
  - evaluate_chart_callouts() generates pre-built flag/positive lists from signal callout_templates
  - callout_templates on 7 stock/price signals with D&O-specific severity-tiered text
  - CI lint test preventing numeric threshold drift back into templates
  - chart_flags/chart_positives context variables for template consumption
affects: [render, stock-charts, signal-yaml]

# Tech tracking
tech-stack:
  added: []
  patterns: [callout-template-pattern, signal-driven-display-text]

key-files:
  created:
    - tests/test_chart_callouts.py
    - tests/test_threshold_lint.py
  modified:
    - src/do_uw/brain/signals/stock/price.yaml
    - src/do_uw/stages/render/context_builders/chart_thresholds.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2

key-decisions:
  - "Callout templates stored in display.callout_templates on each signal YAML — co-located with thresholds"
  - "_FALLBACK_CALLOUTS dict in chart_thresholds.py ensures rendering never breaks if YAML unavailable"
  - "Metric evaluation logic centralized in Python (evaluate_chart_callouts) instead of Jinja2 conditionals"

patterns-established:
  - "callout-template-pattern: Signal YAML carries severity-tiered text templates with {value}/{threshold} placeholders; Python evaluates and interpolates"
  - "ci-lint-for-templates: test_threshold_lint.py scans Jinja2 conditionals for numeric literals to prevent threshold drift"

requirements-completed: [DISP-04]

# Metrics
duration: 6min
completed: 2026-03-09
---

# Phase 91 Plan 03: Chart Callout Templates Summary

**Signal-driven D&O callout text for stock chart risk flags/positives with CI lint enforcement against threshold drift**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-09T16:45:13Z
- **Completed:** 2026-03-09T16:51:33Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added callout_templates to 7 stock/price signal YAMLs with D&O-specific severity-tiered text containing {value}/{threshold} placeholders
- Built evaluate_chart_callouts() that reads templates from signal YAML, evaluates metrics against thresholds, interpolates values, returns categorized flags/positives
- Replaced ~60 lines of inline Jinja2 threshold evaluation with simple loops over pre-built context lists
- Created CI lint test that scans templates for hardcoded numeric thresholds in conditionals

## Task Commits

Each task was committed atomically:

1. **Task 1: Add callout_templates to signal YAMLs and build callout aggregation** - `d682aea` (feat)
2. **Task 2: Replace inline flag/positive logic + CI lint test** - `2a43ed9` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/stock/price.yaml` - Added callout_templates to 7 signals
- `src/do_uw/stages/render/context_builders/chart_thresholds.py` - evaluate_chart_callouts(), _FALLBACK_CALLOUTS, callout template loading
- `src/do_uw/stages/render/html_renderer.py` - Wired chart_flags/chart_positives into build_html_context
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` - Replaced inline evaluation with simple loops
- `tests/test_chart_callouts.py` - 8 tests for callout generation (TDD)
- `tests/test_threshold_lint.py` - 3 CI lint tests for threshold drift prevention

## Decisions Made
- Callout templates co-located with thresholds on signal YAML display blocks (single source of truth)
- _FALLBACK_CALLOUTS dict ensures graceful degradation when YAML loading fails
- Kept cm variable definition for standalone unexplained-drops callout (separate from flags/positives system)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Restored cm variable definition for unexplained drops section**
- **Found during:** Task 2 (template simplification)
- **Issue:** Removing the inline evaluation block also removed the `{% set cm = chart_metrics %}` definition needed by the standalone unexplained drops callout on line 93
- **Fix:** Added `{% set cm = chart_metrics if chart_metrics is defined else {} %}` before the unexplained drops section
- **Files modified:** stock_charts.html.j2
- **Committed in:** 2a43ed9 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix to preserve existing unexplained drops feature. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All chart display text now driven from signal YAML callout_templates
- CI lint test active to prevent threshold drift
- Phase 91 complete (all 3 plans done)

---
*Phase: 91-display-centralization*
*Completed: 2026-03-09*
