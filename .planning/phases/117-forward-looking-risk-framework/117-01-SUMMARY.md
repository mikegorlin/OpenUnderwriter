---
phase: 117-forward-looking-risk-framework
plan: 01
subsystem: models
tags: [pydantic, yaml, forward-looking, nuclear-triggers, posture, credibility, llm-extraction]

# Dependency graph
requires:
  - phase: 115-do-context-infrastructure
    provides: do_context engine and signal consumer pattern
  - phase: 116-do-commentary-wiring
    provides: brain YAML config patterns and signal-driven architecture
provides:
  - ForwardLookingData Pydantic model with 14 sub-models on AnalysisState
  - Underwriting posture decision matrix in brain YAML
  - 6 monitoring trigger definitions (MON-01 to MON-06)
  - 5 nuclear trigger definitions (NUC-01 to NUC-05)
  - LLM extraction schema for forward-looking statements from 10-K/8-K
affects: [117-02, 117-03, 117-04, 117-05, 117-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Forward-looking models as top-level AnalysisState field (spans extract through benchmark)"
    - "Brain YAML configs for underwriting posture matrix and trigger definitions"
    - "CurrencyFloat annotated type with BeforeValidator for LLM output resilience"

key-files:
  created:
    - src/do_uw/models/forward_looking.py
    - src/do_uw/brain/config/underwriting_posture.yaml
    - src/do_uw/brain/config/monitoring_triggers.yaml
    - src/do_uw/brain/config/nuclear_triggers.yaml
    - src/do_uw/stages/extract/llm/schemas/forward_looking.py
    - tests/models/test_forward_looking.py
    - tests/stages/extract/test_forward_looking_schema.py
  modified:
    - src/do_uw/models/state.py

key-decisions:
  - "ForwardLookingData placed as top-level field on AnalysisState (not nested in ExtractedData) because data spans extraction through benchmark"
  - "Factor overrides in posture YAML reference scoring factor IDs (F.1, F.3, F.7, F.9) for deterministic override logic"
  - "Nuclear triggers use check_type field (list_not_empty, boolean_true, departure_under_pressure) for runtime dispatch"

patterns-established:
  - "Brain YAML config for decision matrices: tier-to-posture mapping with factor overrides"
  - "Nuclear trigger definition pattern: id, state_path, check_type, evidence templates"

requirements-completed: [FORWARD-01, FORWARD-02, FORWARD-04, SCORE-03, TRIGGER-03]

# Metrics
duration: 13min
completed: 2026-03-19
---

# Phase 117 Plan 01: Data Models & Brain Config Summary

**14 Pydantic v2 models for forward-looking risk framework, 3 brain YAML configs (posture matrix + monitoring + nuclear triggers), and LLM extraction schema with currency coercion**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-19T19:33:38Z
- **Completed:** 2026-03-19T19:47:05Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- 14 Pydantic v2 models covering forward statements, credibility scoring, monitoring triggers, underwriting posture, nuclear triggers, quick screen, and container
- ForwardLookingData integrated on AnalysisState as top-level field for cross-stage access
- 3 brain YAML configs: 6-tier posture matrix with 4 factor overrides, 6 monitoring triggers, 5 nuclear triggers
- LLM extraction schema with CurrencyFloat coercion for resilient parsing
- 49 tests across both test files, all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models + state integration** - `20138a7e` (feat)
2. **Task 2: Brain YAML configs + LLM extraction schema** - `09f787f6` (feat)

## Files Created/Modified
- `src/do_uw/models/forward_looking.py` - 14 Pydantic models (218 lines, under 500 limit)
- `src/do_uw/models/state.py` - Added ForwardLookingData import and field on AnalysisState
- `src/do_uw/brain/config/underwriting_posture.yaml` - Tier-to-posture decision matrix + factor overrides + nuclear escalation
- `src/do_uw/brain/config/monitoring_triggers.yaml` - 6 company-specific monitoring triggers (MON-01 to MON-06)
- `src/do_uw/brain/config/nuclear_triggers.yaml` - 5 nuclear trigger definitions (NUC-01 to NUC-05)
- `src/do_uw/stages/extract/llm/schemas/forward_looking.py` - LLM extraction schema with BeforeValidator coercions
- `tests/models/test_forward_looking.py` - 33 tests for all 14 model classes
- `tests/stages/extract/test_forward_looking_schema.py` - 16 tests for extraction schema

## Decisions Made
- ForwardLookingData placed as top-level field on AnalysisState rather than nested in ExtractedData, because forward-looking data spans extraction through benchmark stages
- Factor overrides in posture YAML reference scoring factor IDs (F.1, F.3, F.7, F.9) for deterministic override logic at runtime
- Nuclear triggers use a `check_type` field (list_not_empty, boolean_true, departure_under_pressure) to enable runtime dispatch without hardcoding logic

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in `tests/brain/test_brain_contract.py::TestSignalAuditTrail::test_threshold_provenance_categorized` (ohlson_o_score signal uses 'academic' instead of 'academic_research'). Unrelated to this plan's changes -- verified by running the test on the prior commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 14 Pydantic models ready for import by plans 02-06
- Brain YAML configs ready for runtime loading by posture engine (plan 03) and quick screen builder (plan 05)
- LLM extraction schema ready for EXTRACT stage integration (plan 02)
- AnalysisState has ForwardLookingData field ready for population across pipeline stages

## Self-Check: PASSED

All 7 created files verified present. Both task commits (20138a7e, 09f787f6) verified in git log.

---
*Phase: 117-forward-looking-risk-framework*
*Completed: 2026-03-19*
