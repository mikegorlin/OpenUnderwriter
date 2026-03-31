---
phase: 18-llm-extraction-engine
plan: 02
subsystem: extract
tags: [pydantic, schemas, llm, sec-filings, 10-K, DEF-14A, 8-K, 10-Q, SC-13D, extraction]

# Dependency graph
requires:
  - phase: 18-llm-extraction-engine (plan 01)
    provides: LLMExtractor class and cache infrastructure in stages/extract/llm/
provides:
  - Pydantic extraction schemas for all 11 SEC filing types (10-K, 20-F, DEF 14A, 10-Q, 6-K, 8-K, SC 13D, SC 13G, S-3, S-1, 424B)
  - Schema registry mapping form_type strings to (schema, prompt_key, max_tokens) tuples
  - D&O-specific system prompts with anti-hallucination instructions for each filing type
  - Common sub-models shared across schemas (ExtractedPerson, ExtractedRiskFactor, etc.)
affects: [18-llm-extraction-engine plan 03, 19-extraction-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One flat Pydantic schema per filing type (max 2-3 levels nesting)"
    - "Schema registry NamedTuple mapping form_type to SchemaEntry(schema, prompt_key, max_tokens)"
    - "Shared common sub-models for cross-schema reuse"
    - "System prompts with _PREAMBLE constant + filing-specific focus areas"

key-files:
  created:
    - src/do_uw/stages/extract/llm/schemas/__init__.py
    - src/do_uw/stages/extract/llm/schemas/common.py
    - src/do_uw/stages/extract/llm/schemas/ten_k.py
    - src/do_uw/stages/extract/llm/schemas/def14a.py
    - src/do_uw/stages/extract/llm/schemas/eight_k.py
    - src/do_uw/stages/extract/llm/schemas/ten_q.py
    - src/do_uw/stages/extract/llm/schemas/ownership_filing.py
    - src/do_uw/stages/extract/llm/schemas/capital_filing.py
    - src/do_uw/stages/extract/llm/prompts.py
    - tests/test_llm_schemas.py
  modified: []

key-decisions:
  - "Form 4 excluded from registry -- XML-parsed, not LLM-extracted per RESEARCH.md"
  - "FPI forms use domestic equivalents: 20-F uses TenKExtraction, 6-K uses TenQExtraction"
  - "All schema fields optional with defaults to handle incomplete LLM extraction"
  - "lambda: [] for list default_factory (pyright strict compliance)"
  - "Common _PREAMBLE string for system prompts ensures consistent anti-hallucination rules"

patterns-established:
  - "SchemaEntry NamedTuple: (schema class, prompt_key, max_tokens) for registry entries"
  - "get_schema_for_filing() returns None for unsupported types (Form 4)"
  - "get_prompt() raises KeyError for unknown prompt keys"

# Metrics
duration: 7min
completed: 2026-02-10
---

# Phase 18 Plan 02: Extraction Schemas Summary

**Pydantic extraction schemas for all 11 SEC filing types with D&O-focused system prompts, shared sub-models, and schema registry**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-10T18:18:43Z
- **Completed:** 2026-02-10T18:25:13Z
- **Tasks:** 2
- **Files created:** 10

## Accomplishments
- Created comprehensive extraction schemas for every SEC filing type the system acquires (10-K, DEF 14A, 10-Q, 8-K, SC 13D/13G, S-3/S-1/424B, plus FPI equivalents 20-F/6-K)
- Schema registry maps all 11 form types to their extraction configuration in a single lookup
- 6 filing-type-specific system prompts with D&O underwriting context and anti-hallucination instructions
- 74 tests covering schema instantiation, JSON schema generation, nesting depth, registry completeness, and prompt validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create common sub-models and primary filing schemas** - `ad6341d` (feat)
2. **Task 2: Create remaining filing schemas, system prompts, and tests** - `0093fc1` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/llm/schemas/__init__.py` - Schema registry with SCHEMA_REGISTRY dict and get_schema_for_filing()
- `src/do_uw/stages/extract/llm/schemas/common.py` - Shared sub-models: ExtractedPerson, MoneyAmount, ExtractedLegalProceeding, ExtractedRiskFactor, ExtractedDirector, ExtractedCompensation
- `src/do_uw/stages/extract/llm/schemas/ten_k.py` - TenKExtraction: Items 1, 1A, 3, 5, 7, 7A, 8, 9A, 10-14 (288 lines)
- `src/do_uw/stages/extract/llm/schemas/def14a.py` - DEF14AExtraction: board, compensation, governance, ownership (196 lines)
- `src/do_uw/stages/extract/llm/schemas/eight_k.py` - EightKExtraction: Items 1.01, 2.01, 2.02, 4.02, 5.02, 8.01 (153 lines)
- `src/do_uw/stages/extract/llm/schemas/ten_q.py` - TenQExtraction: quarterly changes and new developments (123 lines)
- `src/do_uw/stages/extract/llm/schemas/ownership_filing.py` - SC13DExtraction (activist) and SC13GExtraction (passive)
- `src/do_uw/stages/extract/llm/schemas/capital_filing.py` - CapitalFilingExtraction for S-3, S-1, 424B offerings
- `src/do_uw/stages/extract/llm/prompts.py` - System prompts with D&O context per filing type
- `tests/test_llm_schemas.py` - 74 tests covering all schemas, registry, and prompts

## Decisions Made
- Form 4 deliberately excluded from the schema registry (XML-parsed, not LLM-extracted per RESEARCH.md decision)
- FPI forms reuse domestic schema equivalents (20-F -> TenKExtraction, 6-K -> TenQExtraction) since the content is structurally equivalent
- All schema fields are optional with defaults -- the LLM returns whatever it can find, missing data stays null
- Shared _PREAMBLE constant ensures all 6 prompts have identical anti-hallucination rules
- max_tokens tuned per filing complexity: 10-K=16384, DEF 14A=12288, 10-Q=8192, 8-K/ownership/capital=4096

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All extraction schemas ready for LLMExtractor (Plan 01) to consume via SCHEMA_REGISTRY
- Plan 03 (integration pipeline) can wire LLMExtractor + schemas into EXTRACT stage
- get_schema_for_filing() provides clean lookup API for the extraction pipeline

---
*Phase: 18-llm-extraction-engine*
*Completed: 2026-02-10*
