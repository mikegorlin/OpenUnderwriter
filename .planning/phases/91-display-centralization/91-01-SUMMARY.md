---
phase: 91-display-centralization
plan: 01
subsystem: rendering
tags: [yaml-thresholds, jinja2, context-builders, signal-yaml, chart-evaluation]

# Dependency graph
requires:
  - phase: 88-stock-analysis-engine
    provides: Chart metrics extraction (beta_ratio, volatility, drawdown, etc.)
  - phase: 82-brain-schema-v3
    provides: BrainLoader additive schema fields support
provides:
  - chart_thresholds.py context builder extracting signal YAML thresholds
  - Signal YAML evaluation blocks with numeric chart thresholds
  - Template-ready threshold variables (thresholds.X.red/yellow)
  - Fallback threshold dict for resilient rendering
affects: [91-02-chart-registry, 91-03-ci-lint, rendering, templates]

# Tech tracking
tech-stack:
  added: []
  patterns: [signal-yaml-threshold-ownership, context-builder-threshold-injection]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/chart_thresholds.py
    - tests/test_chart_thresholds.py
  modified:
    - src/do_uw/brain/signals/stock/price.yaml
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2
    - src/do_uw/templates/html/sections/market/stock_performance.html.j2
    - src/do_uw/stages/render/charts/stock_chart_overlays.py
    - src/do_uw/stages/render/context_builders/__init__.py

key-decisions:
  - "Thresholds owned by signal YAML display.chart_thresholds and evaluation.thresholds blocks"
  - "Context builder provides _FALLBACK_THRESHOLDS dict so rendering never breaks even if YAML loading fails"
  - "Overlay thresholds documented as signal-sourced but not parameterized (future Plan 91-03 CI lint ensures sync)"
  - "Templates use dict.get() with inline fallback dicts for graceful degradation"

patterns-established:
  - "Signal YAML threshold ownership: chart evaluation thresholds live on signal YAML, not in templates"
  - "Context builder threshold injection: extract_chart_thresholds reads YAML and injects flat dict into template context"
  - "Template threshold variables: templates reference thresholds.X.red/yellow instead of numeric literals"

requirements-completed: [DISP-01, DISP-02]

# Metrics
duration: 9min
completed: 2026-03-09
---

# Phase 91 Plan 01: Chart Threshold Centralization Summary

**Chart evaluation thresholds moved from 15+ hardcoded template literals to signal YAML ownership via chart_thresholds.py context builder with fallback resilience**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-09T16:32:06Z
- **Completed:** 2026-03-09T16:41:00Z
- **Tasks:** 2 (Task 1 TDD, Task 2 auto)
- **Files modified:** 8

## Accomplishments

- Created chart_thresholds.py context builder that extracts 15 threshold metrics from signal YAML
- Added numeric evaluation.thresholds and display.chart_thresholds blocks to 7 stock price signals
- Replaced all hardcoded numeric thresholds in stock_charts.html.j2 and stock_performance.html.j2
- Templates now reference thresholds.X.red/yellow variables; changing a threshold requires only YAML edit
- 5 unit tests validate threshold extraction, numeric types, expected values, and fallback behavior

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `ac9d517` (test)
2. **Task 1 GREEN: Signal YAML thresholds + chart_thresholds.py** - `70bf42a` (feat)
3. **Task 2: Wire injection + replace template literals** - `d9506eb` (feat)

_Note: Task 1 was TDD with RED/GREEN phases._

## Files Created/Modified

- `src/do_uw/stages/render/context_builders/chart_thresholds.py` - Extracts chart thresholds from signal YAML into template-ready dict
- `tests/test_chart_thresholds.py` - 5 unit tests for threshold extraction
- `src/do_uw/brain/signals/stock/price.yaml` - Added evaluation.thresholds and display.chart_thresholds to 7 signals
- `src/do_uw/stages/render/html_renderer.py` - Wired extract_chart_thresholds into build_html_context
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` - Replaced all hardcoded thresholds with threshold variables
- `src/do_uw/templates/html/sections/market/stock_performance.html.j2` - Replaced off-high and beta thresholds
- `src/do_uw/stages/render/charts/stock_chart_overlays.py` - Documented overlay thresholds as signal-sourced
- `src/do_uw/stages/render/context_builders/__init__.py` - Exported extract_chart_thresholds

## Decisions Made

- Thresholds stored in signal YAML `display.chart_thresholds` for derived metrics (mdd_ratio, vol_ratio, etc.) and `evaluation.thresholds` for direct signal metrics
- _FALLBACK_THRESHOLDS provides resilient defaults matching previous hardcoded values
- Overlay thresholds (volume spike, divergence, drop severity, beta ratio) documented as signal-sourced but not parameterized -- will be enforced by CI lint in Plan 91-03
- Templates use dict.get() with inline fallback dicts to handle missing threshold context gracefully

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing test failure in tests/brain/test_brain_contract.py (sca_settlement_data not in valid sources set) unrelated to this plan's changes. Logged to deferred-items.md.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Threshold injection infrastructure ready for Plans 91-02 (chart registry) and 91-03 (CI lint)
- Templates are threshold-free, ready for CI lint rule to prevent future threshold drift

## Self-Check: PASSED

All files verified present, all commit hashes confirmed in git log.

---
*Phase: 91-display-centralization*
*Completed: 2026-03-09*
