---
phase: 103-schema-foundation
plan: 01
subsystem: brain
tags: [pydantic, yaml, schema-validation, rap-taxonomy, epistemology]

# Dependency graph
requires:
  - phase: 102-foundation-research
    provides: RAP taxonomy (H/A/E categories), decision framework, SCAC validation
provides:
  - BrainSignalEntry extended with rap_class, rap_subcategory, epistemology fields
  - EvaluationSpec extended with mechanism field (EvaluationMechanism Literal type)
  - Epistemology Pydantic model for rule origin + threshold basis traceability
  - PatternDefinition schema for multi-signal risk patterns
  - ChartTemplate schema matching chart_registry.yaml structure
  - SeverityAmplifier schema for severity model multipliers
  - 42 validation tests covering all 4 YAML schema types
affects: [103-03, 103-04, 104, 105, 108, 109]

# Tech tracking
tech-stack:
  added: []
  patterns: [pydantic-extra-forbid-for-new-schemas, optional-none-defaults-for-backward-compat]

key-files:
  created:
    - tests/brain/test_yaml_schemas.py
  modified:
    - src/do_uw/brain/brain_signal_schema.py
    - src/do_uw/brain/brain_schema.py

key-decisions:
  - "All new BrainSignalEntry fields use default=None for backward compat with 514 existing signals"
  - "New schemas (PatternDefinition, ChartTemplate, SeverityAmplifier) use extra=forbid for strict validation"
  - "Epistemology is required on SeverityAmplifier but optional on BrainSignalEntry and PatternDefinition"
  - "EvaluationMechanism is a 6-value Literal type: threshold, peer_comparison, trend, conjunction, absence, contextual"

patterns-established:
  - "V4 RAP taxonomy fields: rap_class (Literal H/A/E | None), rap_subcategory (str | None), epistemology (Epistemology | None)"
  - "Schema extension pattern: add optional fields to BrainSignalEntry, use extra=forbid for new standalone models"

requirements-completed: [SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 103 Plan 01: Schema Foundation Summary

**Pydantic schemas for all 4 brain YAML types: signal (extended with RAP/epistemology), pattern definitions, chart templates, severity amplifiers -- with 42 validation tests and full backward compatibility**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T03:19:40Z
- **Completed:** 2026-03-15T03:24:22Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended BrainSignalEntry with rap_class, rap_subcategory, epistemology (all optional/None) and EvaluationSpec with mechanism field
- Created Epistemology model with strict validation (extra=forbid, required rule_origin + threshold_basis)
- Created 3 new schema classes: PatternDefinition, ChartTemplate, SeverityAmplifier in brain_schema.py
- Validated all 15 chart_registry.yaml entries against ChartTemplate schema
- All 514 existing signals load unchanged (zero regressions across 886 brain tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend BrainSignalEntry + create schemas** - `dd9eb42` (feat)
2. **Task 2: Schema validation tests for all 4 YAML types** - `06c38da` (test)

## Files Created/Modified
- `src/do_uw/brain/brain_signal_schema.py` - Added Epistemology model, EvaluationMechanism type, mechanism field on EvaluationSpec, rap_class/rap_subcategory/epistemology fields on BrainSignalEntry
- `src/do_uw/brain/brain_schema.py` - Added PatternDefinition, ChartTemplate, SeverityAmplifier Pydantic models (alongside existing DuckDB DDL)
- `tests/brain/test_yaml_schemas.py` - 42 tests: signal (18), pattern (7), chart (7), amplifier (7), regression (3)

## Decisions Made
- All new BrainSignalEntry fields default to None so 514 existing signals load unchanged -- Phase 103-04 will populate these fields across all signals
- EvaluationMechanism uses 6 values (threshold, peer_comparison, trend, conjunction, absence, contextual) covering all evaluation patterns discovered in Phase 102
- Epistemology is required on SeverityAmplifier (amplifiers must justify their multiplier) but optional on signals (populated later in Phase 103-04)
- New schemas placed in existing brain_schema.py alongside DuckDB DDL rather than creating a new file -- keeps imports clean since brain_unified_loader already imports from brain_schema

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 YAML schema types have Pydantic enforcement ready
- Phase 103-03 can now add rap_class/epistemology to signal YAML files
- Phase 103-04 can populate mechanism field across all 514 signals
- Phase 108 has SeverityAmplifier schema ready
- Phase 109 has PatternDefinition schema ready

## Self-Check: PASSED

All files and commits verified:
- `src/do_uw/brain/brain_signal_schema.py` -- FOUND
- `src/do_uw/brain/brain_schema.py` -- FOUND
- `tests/brain/test_yaml_schemas.py` -- FOUND
- `dd9eb42` (Task 1 commit) -- FOUND
- `06c38da` (Task 2 commit) -- FOUND

---
*Phase: 103-schema-foundation*
*Completed: 2026-03-15*
