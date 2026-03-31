---
phase: 18-llm-extraction-engine
plan: 03
subsystem: extract
tags: [llm, extraction, pipeline, cli, instructor, anthropic, caching]

# Dependency graph
requires:
  - phase: 18-01
    provides: LLMExtractor, ExtractionCache, CostTracker, strip_boilerplate
  - phase: 18-02
    provides: Extraction schemas for 11 filing types, SCHEMA_REGISTRY, system prompts
provides:
  - LLM extraction wired into ExtractStage as Phase 0 pre-step
  - --no-llm CLI flag for regex-only mode
  - llm_extractions field on AcquiredData for downstream consumers
  - Pipeline config propagation of no_llm flag
affects: [19-llm-result-consumption, 20-extraction-quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy import pattern for optional LLM dependencies in extract __init__.py"
    - "Pipeline config passthrough: no_llm flows CLI -> Pipeline -> ExtractStage"
    - "Serialized dict storage for LLM results (not typed models) since schema varies by filing"

key-files:
  created:
    - tests/test_extract_llm_integration.py
  modified:
    - src/do_uw/stages/extract/__init__.py
    - src/do_uw/models/state.py
    - src/do_uw/cli.py
    - src/do_uw/pipeline.py

key-decisions:
  - "Store llm_extractions as dict[str, Any] (serialized dicts) not typed models, since schema varies by filing type"
  - "Lazy import LLM deps inside _run_llm_extraction to avoid import-time failures"
  - "Entire LLM extraction wrapped in try/except for graceful degradation"
  - "Results keyed by 'form_type:accession' for deterministic lookup"

patterns-established:
  - "Phase 0 pre-step pattern: LLM extraction runs before regex, supplements not replaces"
  - "Mock at re-export namespace (do_uw.stages.extract.llm.LLMExtractor) for lazy import testing"

# Metrics
duration: 10min
completed: 2026-02-10
---

# Phase 18 Plan 03: Pipeline Integration Summary

**LLM extraction wired into ExtractStage as Phase 0 pre-step with --no-llm CLI flag, graceful degradation, and 13 integration tests**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-10T18:29:13Z
- **Completed:** 2026-02-10T18:39:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- LLM extraction runs as Phase 0 before all regex extractors in ExtractStage
- `--no-llm` CLI flag disables LLM extraction for regex-only mode
- Graceful degradation: no crash when API key missing, deps unavailable, or API fails
- Cost summary logged after extraction with tokens and USD
- Results stored in state.acquired_data.llm_extractions for downstream phases
- 13 new integration tests covering all paths, 2102 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire LLM extraction into ExtractStage and add CLI flag** - `1eab218` (feat)
2. **Task 2: Integration tests and pipeline test updates** - `7f677f6` (test)

## Files Created/Modified
- `src/do_uw/stages/extract/__init__.py` - Added _run_llm_extraction Phase 0 pre-step, use_llm param (498 lines)
- `src/do_uw/models/state.py` - Added llm_extractions field to AcquiredData
- `src/do_uw/cli.py` - Added --no-llm flag to analyze command
- `src/do_uw/pipeline.py` - Passes no_llm config through to ExtractStage
- `tests/test_extract_llm_integration.py` - 13 integration tests (382 lines)

## Decisions Made
- Store LLM extraction results as serialized dicts (model_dump()) not Pydantic models, since the specific schema type varies by filing type. Downstream consumers know which schema to deserialize with.
- Lazy import LLM dependencies inside the function body to prevent import-time failures when anthropic/instructor not installed.
- Key format 'form_type:accession' provides deterministic lookup without collision.
- Existing pipeline tests needed no modifications -- LLM extraction is a no-op when ANTHROPIC_API_KEY is unset.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Mock patch paths for lazy imports required patching at the re-export namespace (do_uw.stages.extract.llm.LLMExtractor) rather than the source module or the consumer module. This is because `from do_uw.stages.extract.llm import LLMExtractor` resolves through the `__init__.py` re-export.
- File line count (498 lines) was close to the 500-line limit but stayed under. If future changes push it over, the _run_llm_extraction function should be split into a separate llm_orchestrator.py module.

## User Setup Required

None - no external service configuration required. LLM extraction is enabled by default when ANTHROPIC_API_KEY is set in the environment and disabled automatically when absent.

## Next Phase Readiness
- Phase 18 complete: LLM extraction engine fully operational (foundation + schemas + pipeline integration)
- Ready for Phase 19: Wire LLM results into downstream extractors (governance, litigation, financial)
- The llm_extractions dict on AcquiredData is the handoff point for downstream consumption

---
*Phase: 18-llm-extraction-engine*
*Completed: 2026-02-10*
