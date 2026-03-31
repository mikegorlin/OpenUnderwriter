---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 09
subsystem: brain, extract
tags: [extraction-hints, brain-duckdb, extract-stage, coverage-validation, schema-migration]

# Dependency graph
requires:
  - phase: 32-01
    provides: "brain.duckdb schema with brain_checks table"
  - phase: 32-03
    provides: "BrainDBLoader with checks.json + DuckDB hybrid loading"
provides:
  - "extraction_hints field on 37 check definitions with field_patterns, expected_type, no_data_sentinel, validation_rule"
  - "brain_hints.py module in EXTRACT stage for loading and validating hints"
  - "ExtractStage brain integration: loads hints at startup, validates coverage at end"
  - "_collect_extracted_field_keys() maps state model fields to hint patterns"
affects: [extract-stage, brain-checks, check-engine, pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Brain-to-EXTRACT bridge via lazy-loaded extraction hints"
    - "Graceful degradation: empty hints dict when brain unavailable"
    - "Hint coverage validation as post-extraction quality signal"
    - "Version carry-forward for new brain_checks columns through enrichment/remap"

key-files:
  created:
    - src/do_uw/stages/extract/brain_hints.py
    - tests/stages/extract/test_brain_hints.py
    - tests/stages/extract/__init__.py
  modified:
    - src/do_uw/brain/checks.json
    - src/do_uw/brain/brain_schema.py
    - src/do_uw/brain/brain_loader.py
    - src/do_uw/brain/brain_migrate.py
    - src/do_uw/brain/brain_enrich.py
    - src/do_uw/stages/extract/__init__.py

key-decisions:
  - "37 checks selected across 5 categories (FIN:12, STOCK:7, GOV:6, LIT:6, BIZ:6) for highest extraction fragility impact"
  - "Hints use field_patterns as ANY-match (not ALL-match) for flexible coverage detection"
  - "extraction_hints carried forward through enrichment and v6 remap version rows to prevent loss on version bump"

patterns-established:
  - "Brain column additions require ALTER TABLE IF NOT EXISTS in migrate + carry-forward in enrich/remap"
  - "ExtractionHintsMap type alias for check_id -> ExtractionHint dict"
  - "_collect_extracted_field_keys() pattern for mapping state model to hint patterns"

requirements-completed: [SC-2]

# Metrics
duration: 16min
completed: 2026-02-20
---

# Phase 32 Plan 09: Brain Extraction Hints Summary

**extraction_hints on 37 brain checks with brain_hints module wired into ExtractStage for runtime hint loading and post-extraction coverage validation**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-20T18:28:30Z
- **Completed:** 2026-02-20T18:44:58Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added extraction_hints JSON column to brain_checks DuckDB schema with full migration support
- Populated 37 high-value checks with extraction_hints covering all 5 content categories (FIN, STOCK, GOV, LIT, BIZ)
- Created brain_hints.py module with load_extraction_hints(), get_hints_for_source(), and validate_extraction_against_hints()
- Wired ExtractStage to load hints at startup and validate coverage at completion
- All 182 tests pass (162 brain + 20 new extract tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add extraction_hints to check definitions and brain schema** - `5607115` (feat)
2. **Task 2: Create brain_hints module and wire into ExtractStage** - `8f01381` (feat)

## Files Created/Modified
- `src/do_uw/brain/brain_schema.py` - Added extraction_hints JSON column to brain_checks DDL
- `src/do_uw/brain/brain_loader.py` - SELECT, overlay (_brain_extraction_hints), and reconstruct extraction_hints
- `src/do_uw/brain/brain_migrate.py` - ALTER TABLE migration + extraction_hints in INSERT
- `src/do_uw/brain/brain_enrich.py` - Carry forward extraction_hints through enrichment and v6 remap versions
- `src/do_uw/brain/checks.json` - 37 checks enriched with extraction_hints
- `src/do_uw/stages/extract/brain_hints.py` - ExtractionHint TypedDict, load/filter/validate functions
- `src/do_uw/stages/extract/__init__.py` - ExtractStage brain integration + _collect_extracted_field_keys()
- `tests/stages/extract/__init__.py` - Package init
- `tests/stages/extract/test_brain_hints.py` - 20 tests for hints loading, filtering, validation

## Decisions Made
- Selected 37 checks (not all 388) focusing on highest-value checks where extraction guidance has the most impact -- checks that currently SKIP because extractors don't know what to look for
- Used ANY-match semantics for field_patterns (any one pattern matching satisfies the hint), since many XBRL fields have alternative tag names
- Carried forward extraction_hints through all version-bump operations (enrichment, v6 remap) to prevent data loss when new versions are created
- Used dict comprehension conversion to bridge TypedDict -> dict[str, Any] type mismatch between brain_hints module and ExtractStage

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] extraction_hints lost during version-bump enrichment**
- **Found during:** Task 1 (end-to-end test)
- **Issue:** brain_enrich.py creates version 2 rows with 34 columns but doesn't include extraction_hints. brain_checks_current picks the latest version, which has NULL extraction_hints. Same issue in remap_to_v6().
- **Fix:** Added extraction_hints to SELECT, INSERT, and row construction in both enrich_brain_checks() and remap_to_v6() in brain_enrich.py
- **Files modified:** src/do_uw/brain/brain_enrich.py
- **Verification:** End-to-end test: 37 checks with _brain_extraction_hints via BrainDBLoader after full migration
- **Committed in:** 5607115 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix -- without it, hints would be lost after enrichment. No scope creep.

## Issues Encountered
- Pre-existing pyright errors in brain_migrate.py (fetchone subscript) and extract/__init__.py (Unknown types in filing_texts handling) were present before changes -- 0 new type errors introduced

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- extraction_hints are now part of the brain schema and available to any pipeline component
- Individual extractors can call get_hints_for_source() to get relevant hints for their data source
- Post-extraction coverage reports identify which brain-expected fields were found vs. missing
- Brain failure never blocks extraction -- graceful degradation to empty hints

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
