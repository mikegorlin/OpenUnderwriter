---
phase: 09-knowledge-store-domain-intelligence
plan: 05
subsystem: pipeline-integration
tags: [knowledge-store, backward-compat, ingestion, cli, stage-wiring, zero-regression]

# Dependency graph
requires:
  - phase: 09-knowledge-store-domain-intelligence
    plan: 02
    provides: BackwardCompatLoader, KnowledgeStore, migration infrastructure
  - phase: 09-knowledge-store-domain-intelligence
    plan: 03
    provides: Provenance tracking, get_migration_stats
  - phase: 09-knowledge-store-domain-intelligence
    plan: 04
    provides: cli_knowledge.py sub-app with narratives and learning-summary commands
provides:
  - All 3 brain-consuming stages (ANALYZE, SCORE, BENCHMARK) wired to knowledge store
  - Document ingestion pipeline for external knowledge documents
  - CLI knowledge commands for migrate, stats, ingest, search
  - Zero functional regression across all existing tests
affects: [09-06 (if exists), Phase 10+ (all future work uses knowledge store)]

# Tech tracking
tech-stack:
  added: []
  patterns: [auto-migrate default constructor, rule-based text extraction, StrEnum document types]

key-files:
  created:
    - src/do_uw/knowledge/ingestion.py
    - tests/knowledge/test_ingestion.py
    - tests/knowledge/test_integration.py
  modified:
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/knowledge/compat_loader.py
    - src/do_uw/knowledge/__init__.py
    - src/do_uw/cli_knowledge.py
    - tests/test_pipeline.py
    - tests/test_cli.py
    - tests/test_benchmark_stage.py
    - tests/test_analyze_stage.py
    - tests/test_score_stage.py
    - tests/test_executive_summary.py

key-decisions:
  - "BackwardCompatLoader default constructor auto-migrates brain/ JSON to in-memory store for zero-regression"
  - "Rule-based extraction for v1 with pluggable extraction_fn hook for future LLM-based extraction (Phase 13)"
  - "Incubating checks use section=0, pillar=INGESTED, origin=AI_GENERATED for clear differentiation"
  - "6 document types as StrEnum: SHORT_SELLER_REPORT, CLAIMS_STUDY, UNDERWRITER_NOTES, INDUSTRY_ANALYSIS, REGULATORY_GUIDANCE, GENERAL"
  - "4 extraction patterns: RISK:/CHECK: prefixes, NOTE:/OBSERVATION: prefixes, header bullets, numbered lists"

patterns-established:
  - "auto-migrate pattern: BackwardCompatLoader() with no args creates in-memory store + auto-migrates brain/ JSON"
  - "pluggable extraction: extraction_fn parameter enables custom extraction strategies without modifying ingestion.py"
  - "ingestion result pattern: IngestionResult dataclass with counts and error list for CLI feedback"

# Metrics
duration: 8min
completed: 2026-02-09
---

# Phase 9 Plan 5: Stage Wiring, Document Ingestion, and CLI Commands Summary

**All 3 brain-consuming stages wired to BackwardCompatLoader, document ingestion pipeline with 6 document types, 4 new CLI commands, zero functional regression across 1347 tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-09T06:44:21Z
- **Completed:** 2026-02-09T06:52:11Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 12

## Accomplishments
- Replaced ConfigLoader with BackwardCompatLoader in ANALYZE, SCORE, and BENCHMARK stages (surgical 2-line change per file)
- BackwardCompatLoader default constructor auto-creates in-memory store with brain/ JSON migration for zero-regression
- Document ingestion pipeline extracts knowledge items from .txt and .md files using rule-based patterns
- 6 document types (SHORT_SELLER_REPORT, CLAIMS_STUDY, UNDERWRITER_NOTES, INDUSTRY_ANALYSIS, REGULATORY_GUIDANCE, GENERAL)
- 4 extraction patterns: RISK:/CHECK: prefixes -> check ideas, NOTE:/OBSERVATION: prefixes -> notes, bullet points under headers, numbered lists
- Pluggable extraction_fn parameter for future LLM-based extraction (Phase 13 hook)
- 4 new CLI commands: `do-uw knowledge migrate|stats|ingest|search`
- 29 new tests (7 integration + 22 ingestion), all passing alongside 1318 existing tests (1347 total)
- Updated 8 test files to mock BackwardCompatLoader instead of ConfigLoader
- Zero functional regression: all existing tests pass with identical behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire stages to knowledge store and validate zero regression** - `b529679` (feat)
2. **Task 2: Create document ingestion pipeline and CLI knowledge commands** - `3cc39e1` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/ingestion.py` (351 lines) - Document ingestion pipeline with rule-based extraction
- `src/do_uw/knowledge/compat_loader.py` (191 lines) - Added default constructor with auto-migration
- `src/do_uw/knowledge/__init__.py` (97 lines) - Exported DocumentType, IngestionResult, ingest_document, ingest_text
- `src/do_uw/cli_knowledge.py` (370 lines) - Added migrate, stats, ingest, search commands
- `src/do_uw/stages/analyze/__init__.py` - BackwardCompatLoader instead of ConfigLoader
- `src/do_uw/stages/score/__init__.py` - BackwardCompatLoader instead of ConfigLoader
- `src/do_uw/stages/benchmark/__init__.py` - BackwardCompatLoader instead of ConfigLoader
- `tests/knowledge/test_integration.py` - 7 integration tests validating full data path
- `tests/knowledge/test_ingestion.py` - 22 tests for extraction, ingestion, error handling
- `tests/test_pipeline.py` - Updated mock paths to BackwardCompatLoader
- `tests/test_benchmark_stage.py` - Updated mock paths to BackwardCompatLoader
- `tests/test_analyze_stage.py` - Updated mock paths to BackwardCompatLoader
- `tests/test_score_stage.py` - Updated comment for BackwardCompatLoader
- `tests/test_executive_summary.py` - Updated mock paths to BackwardCompatLoader
- `tests/test_cli.py` - No changes needed (doesn't mock ConfigLoader directly)

## Decisions Made
- **Auto-migrate default constructor**: BackwardCompatLoader() with no args creates in-memory KnowledgeStore and runs migrate_from_json(brain_dir). This ensures tests that previously used real ConfigLoader (loading brain/ JSON directly) continue to work identically through BackwardCompatLoader -> KnowledgeStore path. No test behavior changes needed.
- **Rule-based extraction v1**: Initial extraction uses pattern matching (RISK:/CHECK:/NOTE:/OBSERVATION: prefixes, header bullets, numbered lists). Pluggable extraction_fn parameter enables future LLM-based extraction without modifying ingestion.py.
- **Incubating check conventions**: section=0, pillar=INGESTED, origin=AI_GENERATED, status=INCUBATING, execution_mode=MANUAL. These conventions make ingested checks clearly distinguishable from migrated brain/ checks.
- **4 extraction patterns**: Chosen to handle common structured document formats (reports with risk callouts, findings sections, numbered checklists).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] BackwardCompatLoader default constructor for zero-regression**
- **Found during:** Task 1 (stage wiring)
- **Issue:** BackwardCompatLoader requires a KnowledgeStore, but stages previously called ConfigLoader() with no args. Integration tests (test_score_stage.py) use real brain files via ConfigLoader -- replacing with BackwardCompatLoader(KnowledgeStore()) would produce empty data since the store has no data without migration.
- **Fix:** Added optional store parameter to BackwardCompatLoader.__init__. When None, auto-creates in-memory store and migrates brain/ JSON files. This makes `BackwardCompatLoader()` functionally identical to `ConfigLoader()`.
- **Files modified:** src/do_uw/knowledge/compat_loader.py
- **Commit:** b529679

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Essential for zero-regression requirement. No scope creep.

## Issues Encountered
None beyond the auto-fixed item above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 brain-consuming stages now read from knowledge store via BackwardCompatLoader
- ConfigLoader remains available as legacy/fallback in do_uw.config.loader
- Document ingestion pipeline ready for external knowledge documents
- CLI knowledge commands operational (migrate, stats, ingest, search, narratives, learning-summary)
- 1347 tests passing, zero functional regression
- Ready for 09-06 (if exists) or Phase 10

---
*Phase: 09-knowledge-store-domain-intelligence*
*Completed: 2026-02-09*
