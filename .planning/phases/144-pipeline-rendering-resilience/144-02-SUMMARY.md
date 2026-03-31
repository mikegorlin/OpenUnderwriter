---
phase: 144-pipeline-rendering-resilience
plan: 02
subsystem: render
tags: [charts, resilience, null-safety, decorators, banners]

# Dependency graph
requires:
  - phase: 144-pipeline-rendering-resilience
    provides: "Pipeline structure and rendering framework"
provides:
  - "null_safe_chart decorator for crash-proof chart builders"
  - "create_chart_placeholder for gray PNG fallback images"
  - "stage_failure_banners module for amber section banners"
  - "STAGE_SECTION_MAP linking pipeline stages to context sections"
affects: [render, charts, context-builders]

# Tech tracking
tech-stack:
  added: []
  patterns: ["@null_safe_chart decorator on all chart builders", "STAGE_SECTION_MAP for stage-to-section failure mapping"]

key-files:
  created:
    - src/do_uw/stages/render/charts/chart_guards.py
    - src/do_uw/stages/render/context_builders/stage_failure_banners.py
    - tests/stages/render/test_chart_null_safety.py
    - tests/stages/render/test_stage_failure_banners.py
    - tests/stages/render/test_risk_card_isolation.py
  modified:
    - src/do_uw/stages/render/charts/stock_charts.py
    - src/do_uw/stages/render/charts/drawdown_chart.py
    - src/do_uw/stages/render/charts/drop_analysis_chart.py
    - src/do_uw/stages/render/charts/volatility_chart.py
    - src/do_uw/stages/render/charts/relative_performance_chart.py
    - src/do_uw/stages/render/charts/ownership_chart.py
    - src/do_uw/stages/render/charts/radar_chart.py
    - src/do_uw/stages/render/charts/timeline_chart.py
    - src/do_uw/stages/render/charts/waterfall_chart.py
    - src/do_uw/stages/render/charts/tornado_chart.py
    - src/do_uw/stages/render/context_builders/assembly_registry.py

key-decisions:
  - "Decorator catches AttributeError, TypeError, KeyError, IndexError, ValueError -- covers all data-access failures without swallowing unrelated exceptions"
  - "Banner injection happens after builder loop but before boilerplate strip in assembly_registry"
  - "Risk card isolation verified through existing extract_litigation safe fallback (returns {} when extracted is None)"

patterns-established:
  - "@null_safe_chart: Apply to any chart builder function to make it crash-proof on missing data"
  - "STAGE_SECTION_MAP: Canonical mapping of pipeline stage names to affected context dict keys"

requirements-completed: [RES-02, RES-03, RES-04]

# Metrics
duration: 6min
completed: 2026-03-28
---

# Phase 144 Plan 02: Chart Null Safety + Stage Failure Banners Summary

**Null-safe decorator on all 15 chart builders with stage failure banner injection and risk card isolation verification**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T16:28:54Z
- **Completed:** 2026-03-28T16:35:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- All 15 chart builder functions decorated with @null_safe_chart -- None/missing data returns None instead of crashing the render pipeline
- Stage failure banners automatically injected into affected worksheet sections when upstream stages fail
- Risk card rendering verified independent of extraction pipeline -- acquired_data.litigation_data accessible even when EXTRACT fails
- 18 new tests covering decorator behavior, placeholder generation, banner injection, and risk card independence

## Task Commits

Each task was committed atomically:

1. **Task 1: Null-safe chart decorator and placeholder generator** - `5917016b` (feat)
2. **Task 2: Stage failure banners + risk card isolation verification** - `5add80b4` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/charts/chart_guards.py` - null_safe_chart decorator + create_chart_placeholder function
- `src/do_uw/stages/render/context_builders/stage_failure_banners.py` - STAGE_SECTION_MAP + inject_stage_failure_banners
- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Wired banner injection after builder loop
- `src/do_uw/stages/render/charts/stock_charts.py` - Added @null_safe_chart to 3 functions
- `src/do_uw/stages/render/charts/drawdown_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/drop_analysis_chart.py` - Added @null_safe_chart to 2 functions
- `src/do_uw/stages/render/charts/volatility_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/relative_performance_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/ownership_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/radar_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/timeline_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/waterfall_chart.py` - Added @null_safe_chart
- `src/do_uw/stages/render/charts/tornado_chart.py` - Added @null_safe_chart
- `tests/stages/render/test_chart_null_safety.py` - 10 tests for decorator and chart builders
- `tests/stages/render/test_stage_failure_banners.py` - 5 tests for banner injection
- `tests/stages/render/test_risk_card_isolation.py` - 3 tests for risk card independence

## Decisions Made
- Decorator catches 5 exception types (AttributeError, TypeError, KeyError, IndexError, ValueError) to cover all data-access failure modes without swallowing unrelated exceptions like RuntimeError
- Banner injection placed after builder loop but before boilerplate strip in assembly_registry to ensure banners survive post-processing
- Risk card isolation verified through existing extract_litigation safe fallback rather than creating a new _hydrate_risk_card function -- the current code already returns {} safely when extracted is None

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Chart builders are now crash-proof on missing data
- Stage failure banners ready for template integration (templates can check for `_stage_banner` key)
- Risk card data path verified independent of extraction

---
*Phase: 144-pipeline-rendering-resilience*
*Completed: 2026-03-28*
