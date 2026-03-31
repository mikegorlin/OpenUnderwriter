---
phase: 54-signal-contract-v2
plan: "01"
subsystem: brain
tags: [pydantic, schema, v2-contract, signal-engine, dispatch]

# Dependency graph
requires:
  - phase: 53-data-store-simplification
    provides: BrainLoader YAML runtime loading, BrainSignalEntry Pydantic schema
provides:
  - V2 Pydantic sub-models (AcquisitionSpec, EvaluationSpec, PresentationSpec)
  - schema_version field on BrainSignalEntry (default=1)
  - V2 dispatch stub in signal_engine.py (_evaluate_v2_stub)
  - 51 new tests covering V2 schema and dispatch
affects: [54-02, 54-03, 55-declarative-mapping-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "extra='forbid' on V2 sub-models for YAML typo detection"
    - "Literal types for constrained string fields (op, label, level)"
    - "schema_version dispatch before content_type dispatch in signal engine"

key-files:
  created:
    - tests/brain/test_v2_schema.py
    - tests/brain/test_v2_dispatch.py
  modified:
    - src/do_uw/brain/brain_signal_schema.py
    - src/do_uw/stages/analyze/signal_engine.py

key-decisions:
  - "Used Literal types for constrained enums (op, label, level) instead of plain str — catches invalid values at validation time"
  - "V2 dispatch stub returns None for legacy fallthrough — ensures zero pipeline behavior change in Phase 54"

patterns-established:
  - "V2 sub-models use ConfigDict(extra='forbid') while BrainSignalEntry stays extra='allow'"
  - "schema_version >= 2 check in execute_signals() before content_type dispatch"
  - "Stub returns None to signal 'use legacy path' — Phase 55 replaces with real evaluator"

requirements-completed: [SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04]

# Metrics
duration: 20min
completed: 2026-03-01
---

# Phase 54 Plan 01: V2 Pydantic Models + Schema Version Dispatch Summary

**Extended BrainSignalEntry with 3 Optional V2 sub-model sections (acquisition, evaluation, presentation) + schema_version field, plus dispatch stub in signal_engine.py that falls through to legacy evaluation -- 400 existing signals load unchanged, 623 tests pass**

## Performance

- **Duration:** 20 min
- **Started:** 2026-03-01T15:37:35Z
- **Completed:** 2026-03-01T15:58:06Z
- **Tasks:** 3
- **Files modified:** 4 (2 source, 2 test)

## Accomplishments
- 6 new Pydantic V2 sub-models with extra='forbid' for YAML typo catching: AcquisitionSource, AcquisitionSpec, EvaluationThreshold, EvaluationSpec, PresentationDetailLevel, PresentationSpec
- 4 new Optional fields on BrainSignalEntry: schema_version (default=1), acquisition, evaluation, presentation -- all 400 existing signals load unchanged
- Dispatch stub in signal_engine.py: schema_version >= 2 signals go through _evaluate_v2_stub() which returns None (falls through to legacy evaluation)
- 51 new tests: 42 for V2 schema validation (all operators, value types, extra='forbid' rejection, integration), 9 for dispatch (stub return, V1/V2 identical results)

## Task Commits

Each task was committed atomically:

1. **Task 1: Define V2 Pydantic sub-models on BrainSignalEntry** - `bd7a2a3` (feat)
2. **Task 2: Add schema_version dispatch stub in signal_engine.py** - `1f54eeb` (feat)
3. **Task 3: Write V2 schema and dispatch tests** - `8ab5d95` (test)

## Files Created/Modified
- `src/do_uw/brain/brain_signal_schema.py` - Extended with 6 V2 sub-models + 4 new fields on BrainSignalEntry (286 lines, under 500 limit)
- `src/do_uw/stages/analyze/signal_engine.py` - Added _evaluate_v2_stub() and schema_version dispatch in execute_signals()
- `tests/brain/test_v2_schema.py` - 42 tests covering all V2 sub-model validation
- `tests/brain/test_v2_dispatch.py` - 9 tests covering V2 dispatch stub and legacy fallthrough

## Decisions Made
- Used Literal types for EvaluationThreshold.op (8 operators), EvaluationThreshold.label (RED/YELLOW/CLEAR), and PresentationDetailLevel.level (glance/standard/deep) instead of plain str -- catches invalid values at Pydantic validation time rather than runtime
- V2 dispatch stub placed before content_type dispatch in execute_signals() (not in evaluate_signal()) per plan specification -- allows Phase 55 to intercept before any legacy logic runs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 4 pre-existing test failures found (test_brain_enrich, test_regression_baseline, test_enriched_roundtrip, test_content_type_distribution) -- all verified pre-existing by running on clean commit before changes. Not caused by this plan's changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- V2 schema is ready for Plan 54-02 (field_registry.yaml) and Plan 54-03 (signal migration)
- Dispatch stub is ready for Phase 55 to replace with real V2 evaluator
- All 400 signals load unchanged -- safe to add V2 fields to individual signals

---
*Phase: 54-signal-contract-v2*
*Completed: 2026-03-01*
