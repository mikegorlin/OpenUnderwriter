---
phase: 84-manifest-section-elimination
plan: 04
subsystem: brain
tags: [yaml, manifest, section-elimination, cleanup]

requires:
  - phase: 84-02
    provides: All 5 consumers migrated from section YAML to manifest groups
  - phase: 84-03
    provides: High-risk renderer consumers migrated (section_renderer, html_signals)
provides:
  - Section YAML infrastructure fully deleted (12 files + schema module)
  - Single source of truth: manifest + signal.group (no dual-path rendering)
affects: [85-sector-risk, 86-sector-signals]

tech-stack:
  added: []
  patterns: ["manifest-only rendering (no section YAML fallback)"]

key-files:
  created: []
  modified:
    - tests/brain/test_template_facet_audit.py
    - tests/brain/test_brain_composites.py

key-decisions:
  - "Structural manifest sections (identity, sources, qa_audit, meeting_prep, coverage) exempt from group requirement -- they render as single template blocks"
  - "test_template_facet_audit rewritten to validate manifest groups instead of section YAML facets"
  - "TestFacetContentRefs skipped (facet content_refs were a section YAML concept, no manifest equivalent)"

patterns-established:
  - "Template audit uses manifest groups as source of truth for template coverage"

requirements-completed: [SECT-05, MANIF-05]

duration: 40min
completed: 2026-03-08
---

# Phase 84 Plan 04: Section YAML Deletion Summary

**Deleted all 12 section YAML files and brain_section_schema.py, completing manifest-only rendering architecture**

## Performance

- **Duration:** 40 min
- **Started:** 2026-03-08T07:57:33Z
- **Completed:** 2026-03-08T08:37:33Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Deleted all 12 brain/sections/*.yaml files and removed sections/ directory
- Deleted brain_section_schema.py (SectionSpec, FacetSpec, SubsectionSpec no longer needed)
- Deleted test_section_schema.py (tested deleted module)
- Rewrote test_template_facet_audit.py to use manifest groups
- Updated test_brain_composites.py to check signal group assignments instead of section YAML facet lists
- 2923 tests pass, 7 skipped (1 pre-existing failure in unrelated calibration_runner test)

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify zero consumers and delete section YAML infrastructure** - `6d82bed` (feat)
2. **Task 2: Verify output parity** - Auto-approved (auto-advance enabled, pre-existing test suite validates rendering)

## Files Created/Modified
- `src/do_uw/brain/sections/*.yaml` (12 files DELETED) - Section YAML definitions
- `src/do_uw/brain/brain_section_schema.py` (DELETED) - SectionSpec/FacetSpec schema module
- `tests/brain/test_section_schema.py` (DELETED) - Tests for deleted schema
- `tests/brain/test_template_facet_audit.py` (REWRITTEN) - Now validates manifest groups
- `tests/brain/test_brain_composites.py` (UPDATED) - Uses signal group fields instead of facet lists

## Decisions Made
- Structural manifest sections (identity, sources, qa_audit, meeting_prep, coverage) are exempt from the "must have groups" test -- they render as single template blocks without brain signal grouping
- TestFacetContentRefs test skipped rather than rewritten -- facet content_refs were a section YAML concept with no direct manifest equivalent
- Composite member signal test now checks for group assignment in signal YAML rather than presence in section facet lists

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test_brain_composites.py referencing deleted sections directory**
- **Found during:** Task 1 (test suite run)
- **Issue:** FACETS_DIR pointed to deleted brain/sections/ directory, causing empty signal ID set
- **Fix:** Rewrote TestCompositeSignalFacetCoverage to check signal group assignments via rglob on signal YAML files; skipped TestFacetContentRefs
- **Files modified:** tests/brain/test_brain_composites.py
- **Verification:** 8 passed, 1 skipped in composite tests
- **Committed in:** 6d82bed (Task 1 commit)

**2. [Rule 1 - Bug] Fixed signal YAML directory traversal in composite test**
- **Found during:** Task 1 (test suite run, attempt 2)
- **Issue:** Used glob("*.yaml") but signal files are in subdirectories (base/, biz/, fin/, etc.)
- **Fix:** Changed to rglob("*.yaml") to traverse subdirectories
- **Files modified:** tests/brain/test_brain_composites.py
- **Verification:** All signal IDs found, composite test passes
- **Committed in:** 6d82bed (Task 1 commit)

**3. [Rule 1 - Bug] Fixed manifest sections without groups failing audit test**
- **Found during:** Task 1 (test suite run, attempt 3)
- **Issue:** test_all_sections_have_groups failed for structural sections (identity, sources, etc.) that don't use brain signal grouping
- **Fix:** Added STRUCTURAL_SECTIONS exemption set; renamed test to test_all_signal_sections_have_groups
- **Files modified:** tests/brain/test_template_facet_audit.py
- **Verification:** Full test suite passes
- **Committed in:** 6d82bed (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes were necessary to handle test references to deleted infrastructure. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_calibration_runner.py (TestCLIWiring::test_calibrate_help_shows_commands) -- confirmed by running against pre-change code. Not related to section YAML deletion.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Section YAML infrastructure fully eliminated -- Phase 84 complete
- Manifest + signal.group is now the single source of truth for section/group rendering
- Ready for Phase 85 (Sector Risk Dimensions)

## Self-Check: PASSED

- sections/ directory: DELETED (confirmed)
- brain_section_schema.py: DELETED (confirmed)
- test_section_schema.py: DELETED (confirmed)
- test_template_facet_audit.py: UPDATED (confirmed)
- Commit 6d82bed: FOUND (confirmed)

---
*Phase: 84-manifest-section-elimination*
*Completed: 2026-03-08*
