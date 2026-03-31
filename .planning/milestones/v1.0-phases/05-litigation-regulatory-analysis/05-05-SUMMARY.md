---
phase: 05-litigation-regulatory-analysis
plan: 05
subsystem: extract
tags: [litigation, sub-orchestrator, summary-narrative, timeline-events, matter-counting, integration, pipeline-tests]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Litigation models (LitigationLandscape, all SECT6 sub-models), filing section parser, config files"
  - phase: 05-02
    provides: "SCA extractor, SEC enforcement extractor, derivative suits extractor"
  - phase: 05-03
    provides: "Regulatory proceedings, deal litigation, workforce/product/environmental extractors"
  - phase: 05-04
    provides: "Defense assessment, industry claims, SOL mapper, contingent liability extractors"
provides:
  - "Litigation sub-orchestrator (run_litigation_extractors) calling all 10 SECT6 extractors"
  - "Rule-based litigation summary narrative (5 dimensions)"
  - "Chronological timeline events from all litigation data"
  - "Active and historical matter counting"
  - "ExtractStage Phase 12 integration with full test coverage"
affects: [phase-6-scoring, phase-7-render, phase-8-document]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Litigation sub-orchestrator follows market/governance pattern with 10 extractor wrappers"
    - "3-tuple unpacking for workforce_product and contingent_liabilities extractors"
    - "Intermediate state write before SOL mapper to provide active case trigger dates"
    - "cast(Any, proc_raw) pattern for Phase 3/5 type mismatch on regulatory_proceedings field"

key-files:
  created:
    - src/do_uw/stages/extract/extract_litigation.py
    - src/do_uw/stages/extract/litigation_narrative.py
    - tests/test_extract_litigation.py
  modified:
    - src/do_uw/stages/extract/__init__.py
    - tests/test_extract_stage.py
    - tests/test_pipeline.py
    - tests/test_cli.py

key-decisions:
  - "Split into extract_litigation.py (371L) + litigation_narrative.py (427L) for 500-line compliance"
  - "type: ignore[assignment] for regulatory_proceedings Phase 3/5 type mismatch"
  - "cast(Any, proc_raw) pattern to handle RegulatoryProceeding objects in Phase 3 typed field"
  - "Patch at do_uw.stages.extract.run_litigation_extractors (module namespace) for all integration tests"

patterns-established:
  - "3 sub-orchestrators (financial, market, governance, litigation) complete the extract stage"
  - "Rule-based litigation summary synthesizes 5 dimensions into SourcedValue[str] LOW confidence"
  - "Timeline events sorted date-descending from SCAs, enforcement, regulatory, and deal litigation"

# Metrics
duration: 11min
completed: 2026-02-08
---

# Phase 5 Plan 5: Litigation Sub-orchestrator & Integration Summary

**Litigation sub-orchestrator calling 10 SECT6 extractors with try/except isolation, rule-based summary narrative, chronological timeline, matter counting, and full pipeline/CLI test integration**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-08T18:11:00Z
- **Completed:** 2026-02-08T18:22:33Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 4

## Accomplishments
- Litigation sub-orchestrator (`run_litigation_extractors`) calls all 10 SECT6 extractors in dependency order with try/except isolation, returning default empty models on failure
- Summary narrative synthesizes 5 dimensions: active matters, historical patterns, regulatory pipeline position, defense posture, and emerging exposure
- Timeline events collected from SCAs, enforcement actions, regulatory proceedings, and deal litigation, sorted date-descending
- Active and historical matter counting across all litigation categories
- Intermediate state write before SOL mapper so it can access trigger dates from active cases
- ExtractStage updated with Phase 12 call to run_litigation_extractors
- All pipeline, CLI, and extract tests updated with litigation mock patches
- 752 tests passing, 0 lint/type errors, all files under 500 lines

## Task Commits

Each task was committed atomically:

1. **Task 1: Litigation sub-orchestrator + summary narrative + timeline events** - `7e2c7ed` (feat)
2. **Task 2: Wire into ExtractStage + update pipeline/CLI/extract tests** - `b2b9dd1` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/extract_litigation.py` - Sub-orchestrator with 10 extractor wrappers (371 lines)
- `src/do_uw/stages/extract/litigation_narrative.py` - Summary narrative, timeline events, matter counting (427 lines)
- `tests/test_extract_litigation.py` - 12 tests for orchestrator, failure isolation, summary, timeline, counting
- `src/do_uw/stages/extract/__init__.py` - Added Phase 12 call to run_litigation_extractors (388 lines)
- `tests/test_extract_stage.py` - Added litigation mock to all 9 decorator-based tests + 2 ExitStack tests + 2 new test classes
- `tests/test_pipeline.py` - Added litigation mock to all 4 full-pipeline test methods
- `tests/test_cli.py` - Added litigation mock to _apply_network_patches ExitStack helper

## Decisions Made
- Split orchestrator into two files for 500-line compliance: extract_litigation.py (orchestrator + wrappers) and litigation_narrative.py (summary + timeline + counting)
- Used `type: ignore[assignment]` for regulatory_proceedings field where Phase 5 extractor returns `list[RegulatoryProceeding]` but Phase 3 skeleton typed it as `list[SourcedValue[dict[str, str]]]`
- Used `cast(Any, proc_raw)` pattern in narrative/counting code to handle both RegulatoryProceeding and SourcedValue types at runtime
- Patched at `do_uw.stages.extract.run_litigation_extractors` (module namespace) for all integration tests, consistent with market/governance pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 500-line file limit exceeded**
- **Found during:** Task 1
- **Issue:** Initial extract_litigation.py was 781 lines (over 500 limit)
- **Fix:** Split into extract_litigation.py (371L) + litigation_narrative.py (427L). Orchestrator/wrappers in one file, narrative/timeline/counting in the other.
- **Files created:** src/do_uw/stages/extract/litigation_narrative.py
- **Committed in:** 7e2c7ed

**2. [Rule 1 - Bug] pyright reportUnnecessaryIsInstance for dict checks**
- **Found during:** Task 1
- **Issue:** `isinstance(proc.value, dict)` flagged as unnecessary because pyright sees the static type as `dict[str, str]` (always a dict)
- **Fix:** Used `cast(Any, proc_raw)` pattern and `hasattr(proc.value, "get")` instead of `isinstance`
- **Files modified:** src/do_uw/stages/extract/litigation_narrative.py
- **Committed in:** 7e2c7ed

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** File split necessary for 500-line compliance; cast pattern necessary for pyright strict. No scope creep.

## Issues Encountered
- Phase 3/5 type mismatch on `regulatory_proceedings` field requires careful dual-type handling in narrative and counting code
- Outermost `@patch` decorator = last method parameter ordering must be maintained across all test methods

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 (Litigation & Regulatory Analysis) is COMPLETE
- All 10 SECT6 extractors wired into pipeline via litigation sub-orchestrator
- ExtractStage now has 3 sub-orchestrators (market, governance, litigation) covering all SECT4/5/6 sections
- 752 tests passing with 0 lint/type errors
- Ready for Phase 6: Scoring, Patterns & Risk Synthesis

---
*Phase: 05-litigation-regulatory-analysis*
*Completed: 2026-02-08*
