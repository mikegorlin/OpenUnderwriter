---
phase: 46-brain-driven-gap-search
plan: "04"
subsystem: analyze
tags: [analyze, gap-search, re-evaluator, check-results, qa-audit, state-model]

# Dependency graph
requires:
  - phase: 46-03
    provides: AcquiredData.brain_targeted_search populated by Phase E (gap_searcher.py)
  - phase: 46-02
    provides: AcquiredData.brain_targeted_search field + CheckResult.confidence field
provides:
  - gap_revaluator.py module with apply_gap_search_results() pure function
  - AnalyzeStage wired to call re-evaluator post-execute_checks() with state.acquired_data
  - AnalysisResults.gap_search_summary field on state model
  - QA audit template summary paragraph showing gap search re-evaluation activity
affects:
  - "46-05+ (downstream score/render stages benefit from promoted TRIGGERED/CLEAR checks)"
  - "Score stage now sees TRIGGERED/CLEAR instead of SKIPPED for gap-search-resolved checks"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Re-evaluator as pure function (acquired_data, analysis_results) -> summary dict; no side effects beyond mutating check_results in-place"
    - "Guard: only update SKIPPED checks — non-SKIPPED checks are never overwritten"
    - "Lazy import of gap_revaluator inside try block in AnalyzeStage — same non-blocking pattern as classification/hazard"
    - "Recompute aggregate counts in-place after mutation (direct dict scan instead of re-running aggregate_results)"
    - "gap_search_summary always stored on state.analysis even when updated=0 (template uses .get('updated', 0) guard)"

key-files:
  created:
    - src/do_uw/stages/analyze/gap_revaluator.py
  modified:
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/models/state.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/appendices/qa_audit.html.j2

key-decisions:
  - "Re-evaluator mutates check_results dict in-place (dicts are mutable in Python); the dict was just constructed from model_dump() in AnalyzeStage.run() — safe to mutate"
  - "gap_search_summary stored on state.analysis (not as top-level state field) — same pattern as forensic_composites/executive_risk/nlp_signals"
  - "Aggregate counts recomputed by direct status scan (not re-running aggregate_results()) — avoids double-pass over results list and ensures counts are consistent with mutated state"

requirements-completed: [GAP-05]

# Metrics
duration: 287s
completed: 2026-02-25
---

# Phase 46 Plan 04: Gap Re-evaluator and QA Audit Summary

**SKIPPED checks promoted to TRIGGERED/CLEAR via gap_revaluator.py pure function — closes feedback loop between brain_targeted_search (ACQUIRE) and check_results (ANALYZE) with QA audit summary**

## Performance

- **Duration:** 287s (~5 min)
- **Started:** 2026-02-25T23:25:41Z
- **Completed:** 2026-02-25T23:30:08Z
- **Tasks:** 2
- **Files created/modified:** 5

## Accomplishments

- Built `gap_revaluator.py` (76 lines): pure function `apply_gap_search_results()` reads `acquired.brain_targeted_search`, promotes eligible SKIPPED checks to TRIGGERED or CLEAR with confidence=LOW and source="WEB (gap): {domain}", returns `{updated, triggered, clear}` summary
- Wired re-evaluation into `AnalyzeStage.run()` before `_run_analytical_engines()` so temporal/forensic engines see the updated statuses; recomputes `checks_failed/passed/skipped` aggregate counts after mutation
- Added `gap_search_summary: dict[str, Any]` field to `AnalysisResults` in `state.py` (default={})
- Passed `gap_search_summary` from `state.analysis` through `build_html_context()` to QA audit Jinja2 template
- QA audit template (`qa_audit.html.j2`) now shows gap search summary paragraph when checks were re-evaluated: "Gap search: N checks re-evaluated (J TRIGGERED, L CLEAR)"
- All 3383 tests pass (1 pre-existing test_word_coverage failure, confirmed unrelated)

## Task Commits

1. **Task 1: Build gap_revaluator.py** - `b1ba9f2` (feat)
2. **Task 2: Wire re-evaluation into AnalyzeStage + state + render + QA audit** - `cf8195f` (feat)

## Files Created/Modified

- `src/do_uw/stages/analyze/gap_revaluator.py` (new, 76 lines) — Pure function `apply_gap_search_results()`: reads `brain_targeted_search`, guards non-SKIPPED, sets status/confidence/source/data_status/evidence fields
- `src/do_uw/stages/analyze/__init__.py` — Phase 46 gap re-evaluation block added after logger.info("Analyze: ...") and before `_run_analytical_engines(state)`; aggregate count recomputation; gap_summary stored on state.analysis
- `src/do_uw/models/state.py` — `gap_search_summary: dict[str, Any]` field added to `AnalysisResults` after `checks_skipped`, default={}
- `src/do_uw/stages/render/html_renderer.py` — `gap_search_summary` extracted from `state.analysis` and injected into template context after `blind_spot_status`
- `src/do_uw/templates/html/appendices/qa_audit.html.j2` — Gap search summary paragraph added after "Total checks:" footer, gated on `gap_search_summary.get('updated', 0) > 0`

## Decisions Made

- **Re-evaluator as pure function with in-place mutation**: `check_results` is a `dict[str, Any]` built from `model_dump()` in `AnalyzeStage.run()`. Since it's a plain dict (not the CheckResult Pydantic object), mutating it directly is safe. The dict reference in `state.analysis.check_results` is updated immediately.
- **Aggregate counts recomputed by direct scan**: After re-evaluation, we scan `check_results.values()` directly to count statuses rather than calling `aggregate_results()` again (which would require reconstructing CheckResult objects). Simpler and correct.
- **gap_search_summary always stored**: Even when `updated=0`, the summary is stored so the state captures that gap search ran but had nothing to update. This enables future diagnostics.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- GAP-05 satisfied: SKIPPED checks with gap search evidence are promoted to TRIGGERED or CLEAR
- Score stage will now see fewer SKIPPED checks when gap search has evidence
- QA audit table shows gap search activity for auditors
- Ready for Phase 47 (check routing completeness) or Phase 48 (output quality)

---
*Phase: 46-brain-driven-gap-search*
*Completed: 2026-02-25*
