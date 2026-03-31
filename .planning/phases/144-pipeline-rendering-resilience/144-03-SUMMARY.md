---
phase: 144-pipeline-rendering-resilience
plan: 03
subsystem: rendering
tags: [jinja2, templates, charts, matplotlib, resilience, audit]

requires:
  - phase: 144-pipeline-rendering-resilience (plans 01-02)
    provides: pipeline_status.py, stage_failure_banners.py, chart_guards.py (orphaned implementations)
provides:
  - Pipeline status table visible in audit trail section of HTML worksheet
  - Amber "Incomplete" banners visible in report section templates when stages fail
  - Gray placeholder PNGs written to disk when chart builders return None
affects: [rendering, html-output, chart-generation]

tech-stack:
  added: []
  patterns: [banner propagation from top-level to beta_report sub-dicts, placeholder PNG substitution]

key-files:
  created:
    - src/do_uw/templates/html/appendices/pipeline_status.html.j2
    - tests/stages/render/test_pipeline_status_wiring.py
    - tests/stages/render/test_stage_banner_template.py
    - tests/stages/render/test_chart_placeholder_wiring.py
  modified:
    - src/do_uw/stages/render/context_builders/assembly_registry.py
    - src/do_uw/stages/render/__init__.py
    - src/do_uw/templates/html/sections/report/audit_trail.html.j2
    - src/do_uw/templates/html/sections/report/financial.html.j2
    - src/do_uw/templates/html/sections/report/governance.html.j2
    - src/do_uw/templates/html/sections/report/litigation.html.j2
    - src/do_uw/templates/html/sections/report/stock_market.html.j2
    - src/do_uw/templates/html/sections/report/scoring.html.j2

key-decisions:
  - "Banner propagation reads state.stages directly when top-level context keys are None (handles empty extraction gracefully)"
  - "Placeholder PNGs written for all chart types (stock, radar, ownership, timeline, drawdown, volatility, relative, drop analysis)"

patterns-established:
  - "_propagate_banners_to_beta_report pattern: bridge between inject_stage_failure_banners (top-level keys) and beta_report template variables"

requirements-completed: [RES-02, RES-03, RES-06]

duration: 8min
completed: 2026-03-28
---

# Phase 144 Plan 03: Gap Closure Summary

**Wired 3 orphaned context builders to templates: pipeline status in audit trail, amber stage banners in 5 report sections, placeholder PNGs for all chart types**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28T17:06:30Z
- **Completed:** 2026-03-28T17:15:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Pipeline status table now appears in the audit trail section with per-stage status badges, duration, and error messages
- Amber "Incomplete" banners render in Financial, Governance, Litigation, Stock & Market, and Scoring sections when upstream stages fail
- Every chart slot writes either a real chart or a gray placeholder PNG -- no empty whitespace or broken images

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire pipeline status table into audit trail** - `2cf2b8e1` (feat)
2. **Task 2: Wire stage failure banners into report section templates** - `a6b2f441` (feat)
3. **Task 3: Wire chart placeholder PNG into chart generation pipeline** - `26e140d5` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/appendices/pipeline_status.html.j2` - Pipeline execution status table template
- `src/do_uw/templates/html/sections/report/audit_trail.html.j2` - Added pipeline status include
- `src/do_uw/stages/render/context_builders/assembly_registry.py` - Added build_pipeline_status_context call + _propagate_banners_to_beta_report
- `src/do_uw/templates/html/sections/report/financial.html.j2` - Added _stage_banner conditional
- `src/do_uw/templates/html/sections/report/governance.html.j2` - Added _stage_banner conditional
- `src/do_uw/templates/html/sections/report/litigation.html.j2` - Added _stage_banner conditional
- `src/do_uw/templates/html/sections/report/stock_market.html.j2` - Added _stage_banner conditional
- `src/do_uw/templates/html/sections/report/scoring.html.j2` - Added _stage_banner conditional
- `src/do_uw/stages/render/__init__.py` - Added create_chart_placeholder calls for all chart types
- `tests/stages/render/test_pipeline_status_wiring.py` - 4 wiring tests
- `tests/stages/render/test_stage_banner_template.py` - 3 propagation tests
- `tests/stages/render/test_chart_placeholder_wiring.py` - 3 placeholder tests

## Decisions Made
- Banner propagation uses a two-pass approach: first copies from top-level dict keys, then reads state.stages directly for the case where top-level context values are None (common when extraction fails and no data is available). This ensures banners appear even when the section has zero data.
- Placeholder PNGs are written for ALL chart types (11 chart slots), not just the 4 explicitly listed in the plan. This covers drawdown, volatility, relative performance, and drop analysis charts too.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Banner propagation handles None top-level context values**
- **Found during:** Task 2 (stage failure banners)
- **Issue:** inject_stage_failure_banners skips context keys that are None (not dicts), so when EXTRACT fails and context['financials'] is None, no banner gets injected into the top-level key, making propagation to beta_report impossible
- **Fix:** Added second pass in _propagate_banners_to_beta_report that reads state.stages directly and injects banners into beta_report sub-dicts even when top-level keys have no data
- **Files modified:** src/do_uw/stages/render/context_builders/assembly_registry.py
- **Verification:** All 3 banner propagation tests pass with EXTRACT/SCORE failure states
- **Committed in:** a6b2f441 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- without it, banners would never appear in real failure scenarios where context keys are None.

## Issues Encountered
None.

## Known Stubs
None -- all three features are fully wired end-to-end.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 VERIFICATION.md gaps are now closed
- Phase 144 is fully complete: 8/8 truths should verify on re-run
- 44 phase 144 tests pass (34 existing + 10 new)

---
*Phase: 144-pipeline-rendering-resilience*
*Completed: 2026-03-28*
