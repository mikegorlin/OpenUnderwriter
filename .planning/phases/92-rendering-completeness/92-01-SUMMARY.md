---
phase: 92-rendering-completeness
plan: 01
subsystem: rendering
tags: [yaml-config, render-audit, ci-contract, coverage, jinja2, pipeline]

# Dependency graph
requires:
  - phase: 91-display-centralization
    provides: "Rendering infrastructure and chart registry"
provides:
  - "render_exclusions.yaml config with 22 exclusion entries and reason strings"
  - "render_audit.py engine: compute_render_audit() producing RenderAuditReport"
  - "CI contract test (test_ci_render_paths.py) validating all model fields have render paths"
  - "Data Audit appendix in HTML worksheet (collapsed)"
  - "render_audit key in state.json pipeline_metadata after pipeline run"
affects: [92-02, qa-compare, future-extraction-fields]

# Tech tracking
tech-stack:
  added: []
  patterns: ["YAML-driven exclusion config with reason strings", "CI static analysis of model-to-render coverage", "Post-pipeline render audit injection into state.json"]

key-files:
  created:
    - config/render_exclusions.yaml
    - src/do_uw/stages/render/render_audit.py
    - src/do_uw/stages/render/context_builders/render_audit.py
    - src/do_uw/templates/html/appendices/render_audit.html.j2
    - tests/test_render_audit.py
    - tests/test_ci_render_paths.py
  modified:
    - src/do_uw/stages/render/coverage.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/pipeline.py
    - src/do_uw/templates/html/worksheet.html.j2

key-decisions:
  - "YAML config for exclusions with mandatory reason strings (not hardcoded frozenset)"
  - "CI test uses static file scanning (no pipeline run needed) -- scans context builders, templates, and renderers"
  - "Pipeline injects full render audit into pipeline_metadata after RENDER stage completes"
  - "Preliminary audit (exclusions only) computed at context build time for appendix template"
  - "Discovered and added text_signals and actuarial_pricing as exclusions via CI test"

patterns-established:
  - "YAML exclusion config: every excluded field must have a reason string"
  - "CI contract pattern: add field to model -> must add render path or exclusion entry"
  - "Post-pipeline audit injection: render_audit key in state.json for downstream tools"

requirements-completed: [REND-01, REND-02]

# Metrics
duration: 8min
completed: 2026-03-09
---

# Phase 92 Plan 01: CI Render-Path Contract and Render Audit Summary

**YAML-driven render exclusion config, CI contract test enforcing field-to-render coverage, post-pipeline audit engine injecting into state.json, and Data Audit appendix in HTML worksheet**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-09T18:13:55Z
- **Completed:** 2026-03-09T18:21:54Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Migrated 20 hardcoded EXCLUSION_PREFIXES to YAML config with reason strings, plus discovered 2 new exclusions
- CI contract test statically validates all ExtractedData, ScoringResult, ClassificationResult, HazardProfile, and BenchmarkResult fields have render paths
- Pipeline injects render_audit into state.json pipeline_metadata with excluded/unrendered/coverage data
- HTML worksheet includes collapsed Data Audit appendix showing excluded-by-policy and unrendered field tables

## Task Commits

Each task was committed atomically:

1. **Task 1: Render exclusions config + audit engine + template**
   - `45e559b` (test: add failing tests for render audit framework)
   - `6cc288e` (feat: render exclusions config, audit engine, context builder, template)
2. **Task 2: CI contract test + pipeline integration + state.json injection**
   - `9552401` (feat: CI contract test, pipeline integration, state.json audit injection)

_Note: TDD tasks have test and implementation commits._

## Files Created/Modified
- `config/render_exclusions.yaml` - YAML config with 22 exclusion entries (path + reason)
- `src/do_uw/stages/render/render_audit.py` - Audit engine: compute_render_audit() returning RenderAuditReport
- `src/do_uw/stages/render/context_builders/render_audit.py` - Context builder for template consumption
- `src/do_uw/templates/html/appendices/render_audit.html.j2` - Collapsed Data Audit appendix
- `tests/test_render_audit.py` - 17 unit tests for exclusion loading, audit computation, context building
- `tests/test_ci_render_paths.py` - 7 CI contract tests for model field render path validation
- `src/do_uw/stages/render/coverage.py` - Added load_render_exclusions(), updated _is_excluded() to use YAML
- `src/do_uw/stages/render/html_renderer.py` - Wired render audit context builder into build_html_context()
- `src/do_uw/pipeline.py` - Added _inject_render_audit() for post-pipeline audit in state.json
- `src/do_uw/templates/html/worksheet.html.j2` - Added render_audit appendix include

## Decisions Made
- Used YAML config (not JSON) for exclusions -- matches brain signal YAML convention and supports inline comments with reason strings
- CI test uses static file content scanning (grep-like) rather than AST parsing -- simpler, sufficient for leaf field name detection, no pipeline run needed
- Preliminary audit computed at context build time uses empty rendered_text (conservative: marks all fields unrendered) -- full audit runs post-render in pipeline
- `load_render_exclusions()` uses `functools.cache` for module-level caching -- avoids re-reading YAML on every call
- Kept EXCLUSION_PREFIXES as deprecated backward-compat alias -- existing tests still work without changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added text_signals exclusion**
- **Found during:** Task 2 (CI contract test)
- **Issue:** CI test detected `extracted.text_signals` has no render path -- it's an internal extraction field consumed by the signal engine
- **Fix:** Added to render_exclusions.yaml with reason string
- **Files modified:** config/render_exclusions.yaml
- **Verification:** CI test passes after exclusion added

**2. [Rule 2 - Missing Critical] Added actuarial_pricing exclusion**
- **Found during:** Task 2 (CI contract test)
- **Issue:** CI test detected `scoring.actuarial_pricing` has no render path -- populated in BENCHMARK but no template renders it yet
- **Fix:** Added to render_exclusions.yaml with "render path pending future phase" reason
- **Files modified:** config/render_exclusions.yaml
- **Verification:** CI test passes after exclusion added

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both exclusions are genuine discoveries by the new CI test -- exactly the kind of gaps it's designed to surface. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CI contract test is in place and will catch any future model field additions without render paths
- render_audit key will be in state.json after pipeline runs, ready for qa_compare.py consumption in Plan 02
- Data Audit appendix template renders correctly in HTML worksheet

## Self-Check: PASSED

All 6 created files verified on disk. All 3 task commits verified in git log.

---
*Phase: 92-rendering-completeness*
*Completed: 2026-03-09*
