---
phase: 18-llm-extraction-engine
plan: 01
subsystem: extract
tags: [instructor, anthropic, claude-haiku, pydantic, sqlite, llm-extraction, caching, cost-tracking]

# Dependency graph
requires:
  - phase: 17-system-assessment
    provides: "Stable codebase with 2015 tests, ground truth validation framework"
provides:
  - "LLMExtractor class with extract() method accepting any Pydantic schema"
  - "ExtractionCache SQLite table keyed by (accession, form_type, schema_version)"
  - "strip_boilerplate function for XBRL/exhibit/signature/certification removal"
  - "CostTracker with $1.00/company budget enforcement"
  - "schema_hash function for automatic cache invalidation on schema changes"
affects: [18-02-extraction-schemas, 18-03-integration, 19-regex-deprecation]

# Tech tracking
tech-stack:
  added: [anthropic>=0.79.0, instructor>=1.14.0]
  patterns: [instructor-from-provider, schema-hash-versioning, graceful-none-return, try-import-guard]

key-files:
  created:
    - src/do_uw/stages/extract/llm/__init__.py
    - src/do_uw/stages/extract/llm/extractor.py
    - src/do_uw/stages/extract/llm/cache.py
    - src/do_uw/stages/extract/llm/boilerplate.py
    - src/do_uw/stages/extract/llm/cost_tracker.py
    - tests/test_llm_extractor.py
    - tests/test_extraction_cache.py
    - tests/test_boilerplate.py
    - tests/test_cost_tracker.py
  modified:
    - pyproject.toml

key-decisions:
  - "anthropic and instructor added as main dependencies, not optional extras"
  - "Schema versioning uses SHA-256 hash of model_json_schema() for automatic cache invalidation"
  - "Token estimation uses len(text)//4 heuristic for pre-flight checks (not API counting)"
  - "All LLMExtractor error paths return None (never raise), enabling regex fallback at caller"

patterns-established:
  - "try-import guard pattern: import anthropic/instructor with None fallback for graceful degradation"
  - "Schema hash versioning: schema_hash(model) returns 12-char hex, used as cache key component"
  - "Budget enforcement: CostTracker checks before each extraction, refuses when over $1.00/company"
  - "instructor.from_provider() with cast(T, ...) for pyright strict compatibility"

# Metrics
duration: 6min
completed: 2026-02-10
---

# Phase 18 Plan 01: LLM Extraction Engine Foundation Summary

**LLMExtractor class with instructor+Anthropic wrapping, SQLite extraction cache, boilerplate stripping, and $1.00/company cost budget enforcement**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-10T18:16:46Z
- **Completed:** 2026-02-10T18:22:35Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- LLMExtractor.extract() accepts any Pydantic BaseModel subclass as schema, returns validated instance or None on failure
- ExtractionCache stores/retrieves by composite key (accession_number, form_type, schema_version) with token/cost metadata
- strip_boilerplate removes XBRL inline tags, exhibit indexes, signature pages, SEC headers, officer certifications, and HTML comments
- CostTracker enforces per-company budget with per-extraction recording and summary rollup
- 44 new tests covering all modules with mocked API calls (no real Anthropic calls)
- Full test suite: 2059 passed (up from 2015), 0 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies and create LLM extraction infrastructure** - `dcd57b7` (feat)
2. **Task 2: Implement LLMExtractor core class with tests** - `d5b30a5` (feat)

## Files Created/Modified
- `pyproject.toml` - Added anthropic>=0.79.0 and instructor>=1.14.0 dependencies
- `src/do_uw/stages/extract/llm/__init__.py` - Package init with re-exports of all public symbols
- `src/do_uw/stages/extract/llm/extractor.py` - LLMExtractor class with extract(), schema_hash(), import guards
- `src/do_uw/stages/extract/llm/cache.py` - ExtractionCache with SQLite table, composite PK, cost aggregation
- `src/do_uw/stages/extract/llm/boilerplate.py` - strip_boilerplate() and estimate_tokens() functions
- `src/do_uw/stages/extract/llm/cost_tracker.py` - CostTracker with budget enforcement and summary stats
- `tests/test_llm_extractor.py` - 14 tests for LLMExtractor (guards, cache, API mock, errors)
- `tests/test_extraction_cache.py` - 9 tests for ExtractionCache (CRUD, aggregation, stats)
- `tests/test_boilerplate.py` - 13 tests for strip_boilerplate and estimate_tokens
- `tests/test_cost_tracker.py` - 8 tests for CostTracker (accumulation, budget, summary)

## Decisions Made
- Added anthropic and instructor as main (not optional) dependencies since LLM extraction is core pipeline functionality
- Used character-based token estimation (len//4) instead of Anthropic's count_tokens API for pre-flight checks -- avoids extra API call and rate limit consumption; exact counting deferred to future optimization
- All error paths in LLMExtractor return None rather than raising, matching the "LLM primary, regex fallback" pattern from CONTEXT.md

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. ANTHROPIC_API_KEY environment variable is checked at runtime and extraction gracefully returns None if absent.

## Next Phase Readiness
- LLMExtractor ready to accept filing-type-specific Pydantic schemas (Plan 02)
- Cache and cost tracker ready for integration into ExtractStage pipeline (Plan 03)
- All infrastructure modules pass ruff + pyright strict with 0 errors

---
*Phase: 18-llm-extraction-engine*
*Completed: 2026-02-10*
