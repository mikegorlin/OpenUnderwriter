---
phase: 31-knowledge-model-redesign
plan: 01
subsystem: knowledge
tags: [pydantic, sqlalchemy, alembic, orm, check-definition, enums]

# Dependency graph
requires:
  - phase: 26-check-classification
    provides: "category, signal_type, hazard_or_signal, plaintiff_lenses fields on Check ORM"
  - phase: 30-knowledge-system
    provides: "check_runs table, feedback loop infrastructure"
provides:
  - "CheckDefinition Pydantic model with ContentType, DepthLevel, DataStrategy, EvaluationCriteria, PresentationHint"
  - "Check ORM with 6 new enrichment columns (content_type, depth, rationale, field_key, extraction_path, pattern_ref)"
  - "Alembic migration 006 for enrichment columns"
  - "store_converters round-trips new fields"
affects: [31-02-PLAN, 31-03-PLAN, 31-04-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["CheckDefinition as enriched superset of checks.json with extra='allow'", "DepthLevel IntEnum mapping Data Complexity Spectrum 1-4"]

key-files:
  created:
    - "src/do_uw/knowledge/check_definition.py"
    - "src/do_uw/knowledge/migrations/versions/006_knowledge_model_enrichment.py"
    - "tests/knowledge/test_check_definition.py"
  modified:
    - "src/do_uw/knowledge/models.py"
    - "src/do_uw/knowledge/store_converters.py"

key-decisions:
  - "ContentType enum has 3 values mapping to display/evaluate/infer check archetypes"
  - "DepthLevel IntEnum 1-4 maps directly to user's Data Complexity Spectrum"
  - "CheckDefinition uses extra='allow' to preserve edge-case fields (amplifier, sector_adjustments)"
  - "All 6 ORM columns nullable for backward compatibility with existing data"

patterns-established:
  - "CheckDefinition.from_check_dict / to_check_dict for round-trip serialization"
  - "Enrichment fields always optional with backward-compatible defaults"

# Metrics
duration: 4min
completed: 2026-02-15
---

# Phase 31 Plan 01: Enriched Check Schema Summary

**CheckDefinition Pydantic model with ContentType/DepthLevel enums, DataStrategy/EvaluationCriteria/PresentationHint sub-models, ORM enrichment columns, and Alembic migration 006**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-15T21:03:09Z
- **Completed:** 2026-02-15T21:07:34Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- CheckDefinition Pydantic model validates all 388 existing checks with backward-compatible defaults
- ContentType (3 values) and DepthLevel (1-4) enums map to the Data Complexity Spectrum
- DataStrategy, EvaluationCriteria, PresentationHint sub-models define structured enrichment metadata
- Check ORM gains 6 new nullable columns with Alembic migration 006
- store_converters round-trips all new fields
- 24 new tests + 438 total knowledge tests all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: CheckDefinition Pydantic model with content types and lifecycle metadata** - `84047bc` (feat)
2. **Task 2: Knowledge store ORM update, Alembic migration 006, and converter updates** - `15e41e0` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/check_definition.py` - CheckDefinition, ContentType, DepthLevel, DataStrategy, EvaluationCriteria, PresentationHint Pydantic models
- `src/do_uw/knowledge/migrations/versions/006_knowledge_model_enrichment.py` - Alembic migration adding 6 enrichment columns to checks table
- `tests/knowledge/test_check_definition.py` - 24 tests covering enums, sub-models, validation, round-trip, and all 388 checks
- `src/do_uw/knowledge/models.py` - Check ORM with 6 new nullable columns after Phase 26 classification fields
- `src/do_uw/knowledge/store_converters.py` - check_to_dict includes content_type, depth, rationale, field_key, extraction_path, pattern_ref

## Decisions Made
- ContentType enum has 3 values (MANAGEMENT_DISPLAY, EVALUATIVE_CHECK, INFERENCE_PATTERN) mapping to display/evaluate/infer check archetypes
- DepthLevel IntEnum 1-4 maps directly to user's Data Complexity Spectrum (DISPLAY/COMPUTE/INFER/HUNT)
- CheckDefinition uses ConfigDict(extra="allow") to preserve edge-case fields like amplifier and sector_adjustments that appear in only 1 of 388 checks
- All 6 new ORM columns are nullable for backward compatibility -- no existing data needs migration
- Default content_type is EVALUATIVE_CHECK (most checks are evaluative), default depth is COMPUTE (level 2)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- CheckDefinition model is the foundation for Plan 31-02 (enrichment of all 388 checks)
- ORM columns ready to persist enriched data via Plan 31-03 (knowledge store integration)
- Migration 006 ready to apply to existing knowledge.db instances

---
*Phase: 31-knowledge-model-redesign*
*Completed: 2026-02-15*
