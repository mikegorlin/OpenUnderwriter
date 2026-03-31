---
phase: 34-living-knowledge-continuous-learning
plan: 02
subsystem: knowledge
tags: [llm, anthropic, instructor, ingestion, cli, typer, httpx]

# Dependency graph
requires:
  - phase: 34-living-knowledge-continuous-learning
    provides: "brain_feedback + brain_proposals tables, INCUBATING lifecycle, Pydantic ingestion models"
provides:
  - "LLM-powered document intelligence extraction via instructor + anthropic"
  - "`do-uw ingest file` and `do-uw ingest url` CLI commands"
  - "URL content fetching with HTML-to-text conversion"
  - "Impact report generation with Rich formatting"
  - "Proposal storage in brain_proposals with INCUBATING check creation"
  - "llm_extraction_fn wired into existing ingestion.py extraction hook"
affects: [34-03, 34-04, 34-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [lazy import for LLM deps inside functions, patch at source module for lazy-import testing]

key-files:
  created:
    - src/do_uw/knowledge/ingestion_llm.py
    - src/do_uw/cli_ingest.py
    - tests/knowledge/test_ingestion_llm.py
  modified:
    - src/do_uw/knowledge/ingestion.py
    - src/do_uw/cli.py

key-decisions:
  - "Lazy import anthropic + instructor inside extract_document_intelligence (matching existing LLMExtractor pattern)"
  - "Patch at source module (do_uw.knowledge.ingestion_llm.extract_document_intelligence) for lazy-import CLI testing"
  - "Proposals with sufficient detail (check_id + question + threshold) also inserted as INCUBATING checks"
  - "llm_extraction_fn falls back to empty list (rule-based extraction then takes over) when LLM unavailable"
  - "50,000 char truncation for both URL fetch and LLM input to stay within token budget"

patterns-established:
  - "CLI ingest sub-app pattern: Typer sub-app with file/url sub-commands, Rich impact report display"
  - "Lazy import + source module patching pattern for testing LLM-dependent CLI commands"

requirements-completed: [ARCH-10]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 34 Plan 02: LLM Document Ingestion Pipeline & CLI Summary

**LLM-powered `do-uw ingest` CLI with file/URL support, instructor + anthropic extraction, brain proposal storage, and Rich impact reports**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T05:13:03Z
- **Completed:** 2026-02-21T05:18:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created LLM document intelligence extraction module (ingestion_llm.py, 269 lines) with 4 public functions
- Built CLI `ingest file` and `ingest url` commands with Rich-formatted impact reports showing implications, affected checks, gaps, and proposals
- Wired llm_extraction_fn into existing ingestion.py extraction hook (fills the Phase 13 TODO)
- 19 new tests covering LLM extraction, URL fetching, impact reports, proposal storage, CLI commands, and extraction function wiring
- All tests pass with mocked Anthropic calls, pyright strict clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Build LLM document extraction and ingestion pipeline** - `615fdc8` (feat)
2. **Task 2: Build CLI ingest command and tests** - `d20d06b` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/ingestion_llm.py` - LLM extraction (extract_document_intelligence, fetch_url_content, generate_impact_report, store_proposals)
- `src/do_uw/cli_ingest.py` - CLI ingest sub-app with file and url commands, Rich impact report display
- `tests/knowledge/test_ingestion_llm.py` - 19 tests with mocked Anthropic/instructor calls
- `src/do_uw/knowledge/ingestion.py` - Added llm_extraction_fn, wired as default when anthropic available
- `src/do_uw/cli.py` - Registered ingest_app as Typer sub-app

## Decisions Made
- Lazy import anthropic + instructor inside function bodies (matching existing LLMExtractor pattern) for graceful degradation when not installed
- Proposals with sufficient detail (check_id + question + at least one threshold) are inserted as both brain_proposals AND INCUBATING checks; insufficient detail proposals only go to brain_proposals
- 50,000 character truncation for both URL fetch and LLM input to stay within token budget
- Patch at source module (`do_uw.knowledge.ingestion_llm.extract_document_intelligence`) for testing lazy-import CLI commands
- llm_extraction_fn returns empty list on failure/unavailability, causing fallback to rule-based extraction

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Initial test mock paths targeted the consuming module (cli_ingest, ingestion) instead of the source module (ingestion_llm) -- corrected to patch at source module for lazy-import compatibility

## User Setup Required
None - no external service configuration required. ANTHROPIC_API_KEY needed at runtime for actual LLM extraction (graceful fallback when absent).

## Next Phase Readiness
- Ingestion pipeline complete, ready for feedback loop (Plan 03) and calibration (Plan 04)
- `do-uw ingest` commands available for manual document analysis
- INCUBATING lifecycle path exercised end-to-end: LLM proposes -> brain_proposals + INCUBATING check -> human review for promotion

---
*Phase: 34-living-knowledge-continuous-learning*
*Completed: 2026-02-21*
