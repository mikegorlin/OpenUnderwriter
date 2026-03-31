---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 04
subsystem: brain
tags: [duckdb, brain, taxonomy, v6, remap, enrichment, risk-questions]

# Dependency graph
requires:
  - phase: 32-01
    provides: brain_schema.py and brain_migrate.py (DuckDB schema + initial migration)
  - phase: 32-02
    provides: enrichment_data.py with Q1-Q25 mappings, brain_enrich.py enrichment applier
  - phase: 32-03
    provides: QUESTIONS-FINAL.md with v6 5-section taxonomy (45 subsections, 231 questions)
provides:
  - enrichment_data.py with v6 subsection IDs (1.1-5.9) replacing Q1-Q25
  - PREFIX_TO_REPORT_SECTION with 5 v6 sections (company, market, financial, governance, litigation)
  - brain_taxonomy with 45 v6 subsection entities replacing 25 Q-IDs
  - remap_to_v6() function for idempotent taxonomy migration
  - brain_loader.py section_map aligned to v6 section names
  - Full migration pipeline (v1 -> enrich -> remap) producing v6-ready checks
affects: [32-05, 32-06, 32-07]

# Tech tracking
tech-stack:
  added: []
  patterns: [v6-taxonomy-subsection-granularity, idempotent-remap, enrichment-with-test-isolation]

key-files:
  created:
    - tests/brain/test_brain_remap.py
  modified:
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/brain/brain_enrich.py
    - src/do_uw/brain/brain_migrate.py
    - src/do_uw/brain/brain_loader.py
    - tests/brain/test_brain_enrich.py
    - tests/brain/test_brain_migrate.py
    - tests/brain/test_brain_loader.py

key-decisions:
  - "Enrichment already applies v6 IDs directly (enrichment_data.py is v6-native), so remap_to_v6() is idempotent no-op for fresh migrations but provides safety net for existing databases"
  - "37 unique v6 subsections referenced by checks (out of 45 total) -- 8 subsections have no current checks mapped (1.4, 1.5, 1.9, 1.10, 4.4, 4.9, 5.3, 5.7) which is correct since those are gap areas"
  - "NLP prefix mapped to governance section (disclosure merged into Section 4 in v6)"
  - "FWRD prefix mapped to company section (forward-looking maps to risk calendar 1.11 in v6)"
  - "Added run_enrichment parameter to migrate_checks_to_brain() for test isolation of migration vs enrichment"

patterns-established:
  - "v6 taxonomy granularity: subsection-level X.Y format (45 entities), not individual question X.Y.Z (231 entities)"
  - "Idempotent remap: remap_to_v6() checks current format before creating new versions"
  - "Test isolation: run_enrichment=False allows testing migration separately from enrichment"

requirements-completed: [SC-1, SC-3]

# Metrics
duration: 17min
completed: 2026-02-20
---

# Phase 32 Plan 04: v6 Taxonomy Remap Summary

**All 388 checks remapped from Q1-Q25 to v6 subsection IDs (X.Y format, 45 entities), with 45 taxonomy subsections, 5 report sections, and idempotent migration pipeline**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-20T15:56:08Z
- **Completed:** 2026-02-20T16:13:14Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Remapped all enrichment mappings from Q1-Q25 to v6 subsection IDs: 53 subdomain defaults and 84 explicit overrides now use X.Y format
- Updated PREFIX_TO_REPORT_SECTION from 7 old sections to 5 v6 sections (financial not financials, NLP -> governance, FWRD -> company)
- Replaced 25 Q-ID taxonomy entities with 45 v6 subsections from QUESTIONS-FINAL.md (11+8+8+9+9 per section)
- Updated 7 report section taxonomy entities to 5 matching v6 (company, market, financial, governance, litigation)
- Added remap_to_v6() function providing idempotent Q-old to v6 transition for existing databases
- Updated brain_loader.py section_map to match v6 section names
- Updated backlog items to use v6 subsection IDs
- 135 brain tests passing (18 new remap tests), 1960 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Remap enrichment_data.py to v6 taxonomy and update brain_loader section_map** - `efa95aa` (feat)
2. **Task 2: Apply v6 remap to brain.duckdb and update taxonomy** - `434042c` (feat)

## Files Created/Modified
- `src/do_uw/brain/enrichment_data.py` - All Q1-Q25 replaced with v6 X.Y subsection IDs in SUBDOMAIN_TO_RISK_QUESTIONS (53), CHECK_TO_RISK_QUESTIONS (84), PREFIX_TO_REPORT_SECTION (5 sections)
- `src/do_uw/brain/brain_enrich.py` - Added remap_to_v6() function, _has_old_q_ids(), _is_v6_format() helpers
- `src/do_uw/brain/brain_migrate.py` - v6 prefix mapping, 45 subsection taxonomy, 5 section entities, v6 backlog IDs, run_enrichment parameter
- `src/do_uw/brain/brain_loader.py` - section_map updated to v6 names (5 entries, no disclosure/forward)
- `tests/brain/test_brain_remap.py` - 18 new tests: v6 format validation, taxonomy counts, changelog, idempotency, backlog
- `tests/brain/test_brain_enrich.py` - Updated all spot-checks to v6 IDs, added v6 format validation tests, NLP/insider mapping tests
- `tests/brain/test_brain_migrate.py` - Updated counts: 45 questions, 5 sections, 75 total taxonomy
- `tests/brain/test_brain_loader.py` - Updated taxonomy counts to v6

## Decisions Made
- Enrichment already applies v6 IDs directly since enrichment_data.py was updated first (Task 1 before Task 2), making remap_to_v6() a safety net / validation function rather than active remapper for fresh migrations
- 37 of 45 subsections are currently referenced by check mappings -- 8 subsections (1.4 Corporate Structure, 1.5 Geographic, 1.9 Employee Signals, 1.10 Customer Signals, 4.4 Shareholder Rights, 4.9 Media, 5.3 Derivative, 5.7 Defense Posture) have no current checks mapped, which correctly identifies gap areas for future backlog work
- Added run_enrichment parameter to migrate_checks_to_brain() to allow test_brain_enrich.py to test enrichment independently from migration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_brain_loader.py taxonomy counts**
- **Found during:** Task 2 (running brain test suite)
- **Issue:** test_brain_loader.py::test_load_taxonomy_counts expected old counts (25 questions, 7 sections)
- **Fix:** Updated assertions to v6 counts (45 questions, 5 sections)
- **Files modified:** tests/brain/test_brain_loader.py
- **Committed in:** 434042c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test assertion update was necessary consequence of taxonomy change. No scope creep.

## Issues Encountered
- Pre-existing test failure `test_item9a_material_weakness[TSLA]` unrelated to our changes (documented in 32-01-SUMMARY.md)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All brain knowledge uses v6 taxonomy subsection identifiers (X.Y format: 1.1 through 5.9, 45 entities)
- No references to old Q1-Q25 remain in enrichment data, DuckDB, or tests
- Fresh migrations produce fully v6-ready checks in a single pipeline (v1 -> enrich -> remap)
- Ready for Plan 05 (Pipeline Integration) to wire brain reads into ACQUIRE/EXTRACT stages
- Ready for Plan 06 (Gap Detection) to identify unmapped subsections for coverage analysis
- 8 unmapped subsections identified as natural gap analysis targets

## Self-Check: PASSED

- All 8 created/modified files verified present on disk
- Both task commits (efa95aa, 434042c) verified in git log
- 135 brain tests passing, 1960 total tests passing (1 pre-existing failure unrelated)

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
