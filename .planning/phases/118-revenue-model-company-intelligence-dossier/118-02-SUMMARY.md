---
phase: 118-revenue-model-company-intelligence-dossier
plan: 02
subsystem: extract
tags: [llm-extraction, pydantic, dossier, asc-606, revenue-model, unit-economics]

# Dependency graph
requires:
  - phase: 118-01
    provides: DossierData Pydantic models on AnalysisState
provides:
  - 4 focused LLM extraction schemas for dossier fields
  - Dossier extraction orchestration module with QUAL-03 prompts
  - Revenue flow diagram text generation from structured nodes/edges
  - Revenue model card construction with heuristic risk levels
affects: [118-03, 118-04, 118-05, 118-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Split-prompt extraction: 4 focused schemas targeting specific 10-K sections"
    - "Revenue flow as structured nodes/edges converted to text"
    - "Revenue model card with heuristic risk levels from extraction attributes"
    - "Segment enrichment: consume existing revenue_segments, enrich with LLM"

key-files:
  created:
    - src/do_uw/stages/extract/llm/schemas/dossier.py
    - src/do_uw/stages/extract/dossier_extraction.py
  modified:
    - tests/stages/extract/test_dossier_extraction.py

key-decisions:
  - "4 focused extraction schemas (not one mega-schema) targeting specific 10-K sections to avoid context bloat"
  - "Revenue segments consumed from state.company.revenue_segments as authoritative, enriched by LLM"
  - "Each sub-extraction is try/except wrapped -- failure in one does not block others"
  - "Revenue flow represented as nodes/edges dict lists for structured LLM extraction"

patterns-established:
  - "Dossier extraction pattern: focused prompts with QUAL-03 analytical context"
  - "Revenue card construction from extraction attributes with heuristic risk levels"

requirements-completed: [DOSSIER-01, DOSSIER-02, DOSSIER-03, DOSSIER-04, DOSSIER-05, DOSSIER-06, DOSSIER-08, DOSSIER-09]

# Metrics
duration: 6min
completed: 2026-03-20
---

# Phase 118 Plan 02: Dossier Extraction Summary

**4 focused LLM extraction schemas + orchestration module populating DossierData from 10-K with QUAL-03 analytical context in all prompts**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T13:31:07Z
- **Completed:** 2026-03-20T13:37:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- 4 LLM extraction schemas targeting specific 10-K sections: RevenueModelExtraction (Items 1+7), ASC606Extraction (Note 2), EmergingRiskExtraction (Item 1A+MD&A), UnitEconomicsExtraction (MD&A+Items 1/7)
- Extraction orchestration module with 4 independent sub-extractions, each fault-tolerant
- Revenue model card construction with heuristic D&O risk levels
- Revenue flow diagram generation from structured nodes/edges
- Segment enrichment pattern: consume existing state.company.revenue_segments, enrich with LLM growth_rate/rev_rec_method/do_exposure
- 17 comprehensive tests (8 schema validation + 9 orchestration/integration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create LLM extraction schemas for dossier fields** - `7808ed9b` (test: TDD schemas + 8 tests)
2. **Task 2: Create dossier extraction orchestration module** - `30f01daa` (feat: orchestration + 9 integration tests)

_Note: Task 1 used TDD (test first, then implementation)_

## Files Created/Modified
- `src/do_uw/stages/extract/llm/schemas/dossier.py` - 4 Pydantic extraction schemas with sub-models
- `src/do_uw/stages/extract/dossier_extraction.py` - Extraction orchestration with 4 focused LLM prompts
- `tests/stages/extract/test_dossier_extraction.py` - 17 tests covering schemas and orchestration

## Decisions Made
- Used 4 focused schemas (not one mega-schema) to avoid context window bloat and improve extraction quality per filing section
- Revenue segments consumed from state.company.revenue_segments as authoritative per research Pitfall 2 -- LLM only enriches, never replaces
- Each sub-extraction is independently try/except wrapped so one failure does not block others
- Revenue flow represented as typed dict lists (nodes/edges) for structured LLM output, converted to text for display
- Extraction confidence set algorithmically: 3+ sections = HIGH, 1+ = MEDIUM, 0 = LOW

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- AnalysisState requires `ticker` field -- fixed test helper to pass ticker to constructor

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Extraction schemas and orchestration ready for pipeline wiring (118-03 or later)
- Schemas can be imported from `do_uw.stages.extract.llm.schemas.dossier`
- Extraction can be called via `extract_dossier(state)` once wired into EXTRACT stage
- Revenue model card, segment dossiers, ASC 606 elements ready for rendering in 118-04/05

---
*Phase: 118-revenue-model-company-intelligence-dossier*
*Completed: 2026-03-20*
