---
phase: 33-brain-driven-worksheet-architecture
plan: 03
subsystem: analyze
tags: [checks, brain, field-routing, zero-coverage, litigation, corporate-structure]

# Dependency graph
requires:
  - phase: 33-01
    provides: "v6 subsection IDs on all 384 checks"
provides:
  - "12 new checks for 5 zero-coverage subsections (1.4, 4.9, 5.7, 5.8, 5.9)"
  - "check_mappers_ext.py module for text signal helpers"
  - "SOL window count, defense posture, and litigation pattern fields in mapper"
  - "59 tests validating zero-coverage check integrity"
affects: [33-04, 33-05, 33-06, render]

# Tech tracking
tech-stack:
  added: []
  patterns: ["check_mappers_ext.py split pattern for 500-line limit compliance"]

key-files:
  created:
    - src/do_uw/stages/analyze/check_mappers_ext.py
    - tests/brain/test_zero_coverage_checks.py
  modified:
    - src/do_uw/brain/checks.json
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/stages/analyze/check_field_routing.py
    - src/do_uw/stages/analyze/check_mappers.py
    - src/do_uw/stages/analyze/check_mappers_sections.py

key-decisions:
  - "Route BIZ.STRUCT checks through existing BIZ mapper (subsidiary_count already populated; vie_spe and related_party SKIP cleanly)"
  - "Route LIT.DEFENSE/PATTERN/SECTOR through existing LIT mapper, extending it with sol_open_count and defense fields"
  - "Move text signal helpers to check_mappers_ext.py (check_mappers.py 510->457 lines)"
  - "Use data_strategy.field_key (declarative routing) for all new checks rather than legacy FIELD_FOR_CHECK only"

patterns-established:
  - "check_mappers_ext.py: extension module pattern for keeping check_mappers.py under 500 lines"
  - "New check prefixes (BIZ.STRUCT, LIT.DEFENSE, LIT.PATTERN, LIT.SECTOR) route through existing prefix-based dispatch"

requirements-completed: [SC5-zero-coverage-closure]

# Metrics
duration: 10min
completed: 2026-02-20
---

# Phase 33 Plan 03: Zero-Coverage Subsection Checks Summary

**12 new checks + 2 updated checks close all 5 zero-coverage subsections (1.4, 4.9, 5.7, 5.8, 5.9) with full metadata, field routing, and enrichment mappings**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-20T21:53:40Z
- **Completed:** 2026-02-20T22:04:18Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created 12 new checks across 4 new prefixes: BIZ.STRUCT (3), LIT.DEFENSE (3), LIT.PATTERN (4), LIT.SECTOR (2)
- Updated 2 existing FWRD.WARN checks to include subsection 4.9 (Media & External Narrative)
- Total check count: 384 -> 396; all 5 previously zero-coverage subsections now have 2+ checks
- Split text signal helpers to check_mappers_ext.py, bringing check_mappers.py from 510 to 457 lines
- Added litigation mapper fields: sol_open_count, forum_selection_clause, pslra_safe_harbor, single_day_drops_count
- 59 new tests across 5 test classes; 232 brain tests and 135 analyze tests all pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create new checks for subsections 1.4, 4.9, 5.7, 5.8, 5.9** - `4d0c943` (feat)
2. **Task 2: Add field routing and data mappers for new checks** - `83c11a4` (feat)

## Files Created/Modified
- `src/do_uw/brain/checks.json` - 12 new checks added, 2 updated, total 396
- `src/do_uw/brain/enrichment_data.py` - New subdomain routing, risk questions, hazards, framework layers, characteristics
- `src/do_uw/stages/analyze/check_field_routing.py` - 12 new FIELD_FOR_CHECK entries
- `src/do_uw/stages/analyze/check_mappers.py` - Import from ext, removed local helpers (510->457 lines)
- `src/do_uw/stages/analyze/check_mappers_ext.py` - NEW: text signal helpers + BIZ_TEXT_SIG_FIELDS dict
- `src/do_uw/stages/analyze/check_mappers_sections.py` - Extended litigation mapper with defense/pattern fields
- `tests/brain/test_zero_coverage_checks.py` - NEW: 59 tests for new checks
- `tests/brain/test_brain_enrich.py` - Updated counts 384->396
- `tests/brain/test_brain_migrate.py` - Updated counts 384->396
- `tests/brain/test_brain_remap.py` - Updated counts 384->396
- `tests/brain/test_enrichment_coverage.py` - Updated counts 384->396

## Decisions Made
- Routed BIZ.STRUCT checks through existing BIZ prefix mapper -- subsidiary_count already extracted from CompanyProfile; vie_spe and related_party produce clean SKIPPED until extraction is added
- Routed all LIT.DEFENSE/PATTERN/SECTOR checks through existing LIT mapper, extending map_litigation_fields with new fields (sol_open_count from SOLWindow model, single_day_drops_count from market data)
- Used data_strategy.field_key (Phase 31 declarative routing) as primary routing for all new checks, with FIELD_FOR_CHECK as backup
- Moved text signal helpers to check_mappers_ext.py rather than creating per-prefix mapper modules, keeping the split minimal

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated 14 hardcoded test counts from 384 to 396**
- **Found during:** Task 2 (running brain tests)
- **Issue:** Existing brain tests in test_brain_enrich.py, test_brain_migrate.py, test_brain_remap.py, test_enrichment_coverage.py all hardcode 384 as expected check count
- **Fix:** Updated all instances of 384 to 396 (and MANAGEMENT_DISPLAY 98 to 99)
- **Files modified:** tests/brain/test_brain_enrich.py, test_brain_migrate.py, test_brain_remap.py, test_enrichment_coverage.py
- **Verification:** All 232 brain tests pass
- **Committed in:** 83c11a4 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Necessary count update for new checks. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 45 v6 subsections now have check coverage (previously 40/45 had coverage)
- check_mappers.py at 457 lines with headroom for future additions
- New prefix patterns (BIZ.STRUCT, LIT.DEFENSE, LIT.PATTERN, LIT.SECTOR) established for future check additions
- Ready for Plan 04 (section artifact generation)

---
*Phase: 33-brain-driven-worksheet-architecture*
*Completed: 2026-02-20*
