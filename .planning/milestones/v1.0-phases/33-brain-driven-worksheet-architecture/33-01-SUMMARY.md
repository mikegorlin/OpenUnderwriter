---
phase: 33-brain-driven-worksheet-architecture
plan: 01
subsystem: brain
tags: [v6-subsections, checks-json, enrichment, duckdb, coverage-mapping]

# Dependency graph
requires:
  - phase: 32-knowledge-driven-acquisition-analysis-pipeline
    provides: "384 checks in checks.json with enrichment_data.py mappings (CHECK_TO_RISK_QUESTIONS, SUBDOMAIN_TO_RISK_QUESTIONS)"
provides:
  - "v6_subsection_ids field on all 384 checks in checks.json"
  - "Cross-reference mappings for 1.5 (Geographic), 1.9 (Customer/Employee), 1.10 (Company-Specific), 5.3 (Derivative)"
  - "Coverage validation test suite (11 tests)"
affects: [33-02, 33-03, 33-04, 33-05, 33-06]

# Tech tracking
tech-stack:
  added: []
  patterns: ["v6_subsection_ids as static field in checks.json derived from enrichment_data.py"]

key-files:
  created:
    - tests/brain/test_enrichment_coverage.py
  modified:
    - src/do_uw/brain/checks.json
    - src/do_uw/brain/enrichment_data.py

key-decisions:
  - "Added cross-reference subsection mappings for 3 non-Plan-03 gaps (1.5, 1.9, 1.10) plus 5.3 Derivative Litigation"
  - "v6_subsection_ids computed from enrichment_data.py at build time, not maintained independently -- single source of truth"
  - "4 remaining uncovered subsections (1.4, 4.9, 5.7, 5.9) deferred to Plan 03 as designed"

patterns-established:
  - "v6_subsection_ids field: static list of X.Y strings on each check, derived from enrichment_data.py"
  - "Coverage test validates checks.json v6_subsection_ids match enrichment_data.py resolution"

requirements-completed: [SC1-question-specs, SC3-acquisition-audit]

# Metrics
duration: 5m 30s
completed: 2026-02-20
---

# Phase 33 Plan 01: v6 Subsection IDs Summary

**Added v6_subsection_ids to all 384 checks in checks.json with 41/45 subsection coverage via enrichment_data.py cross-reference mappings**

## Performance

- **Duration:** 5m 30s
- **Started:** 2026-02-20T21:40:12Z
- **Completed:** 2026-02-20T21:45:42Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Every check in checks.json now has a non-empty v6_subsection_ids list linking it to v6 subsections
- 37 unique subsection IDs covered (41 of 45 subsections have at least one check); only 4 Plan 03 gaps remain
- Added 18 explicit cross-reference mappings in enrichment_data.py for subsections 1.5, 1.9, 1.10, 5.3
- 11-test coverage suite validates completeness, format validity, enrichment consistency

## Task Commits

Each task was committed atomically:

1. **Task 1: Add v6_subsection_ids to all 384 checks** - `556e5cb` (feat)
2. **Task 2: Coverage test and enrichment verification** - `a40a42a` (test)

## Files Created/Modified
- `src/do_uw/brain/checks.json` - Added v6_subsection_ids field to all 384 checks
- `src/do_uw/brain/enrichment_data.py` - Added 18 explicit cross-reference mappings for geographic, customer/employee, company-specific, and derivative subsections
- `tests/brain/test_enrichment_coverage.py` - 11 tests validating v6 subsection ID coverage, format, and enrichment consistency

## Decisions Made
- Added cross-reference mappings for BIZ.MODEL.revenue_geo -> 1.5, BIZ.SIZE.employees -> 1.9, BIZ.DEPEND.customer_conc/labor -> 1.9, BIZ.UNI.* -> 1.10, LIT.SCA.derivative/demand/merger_obj -> 5.3, plus FWRD.EVENT/WARN/MACRO crossovers. These are natural multi-subsection mappings (a check can answer questions in multiple subsections).
- Subsection 5.8 (Litigation Risk Patterns) was originally zero-coverage but BIZ.COMP.peer_litigation already maps to ["1.7", "5.8"], so only 4 of the original 5 zero-coverage subsections remain for Plan 03.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added cross-reference mappings for 3 uncovered subsections**
- **Found during:** Task 1 (v6_subsection_ids assignment)
- **Issue:** Subsections 1.5, 1.9, 1.10, and 5.3 had no check coverage because existing checks only mapped to their primary subsection. Plan must_have requires all 45 subsections covered except 5 Plan 03 ones.
- **Fix:** Added 18 explicit entries in CHECK_TO_RISK_QUESTIONS for checks that naturally answer questions in multiple subsections (e.g., BIZ.MODEL.revenue_geo answers both 1.2 Business Model and 1.5 Geographic Footprint)
- **Files modified:** src/do_uw/brain/enrichment_data.py
- **Verification:** 41/45 subsections covered; only 4 Plan 03 gaps remain (1.4, 4.9, 5.7, 5.9)
- **Committed in:** 556e5cb (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical mapping)
**Impact on plan:** Essential for meeting must_have coverage requirement. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- v6_subsection_ids are now available for Plan 02 (section artifact builders) to query "what checks belong to subsection X.Y?"
- Plan 03 (zero-coverage closure) has clear list of 4 remaining subsections to create checks for
- All 173 brain tests pass with zero regressions

## Self-Check: PASSED
- All 3 created/modified files exist on disk
- Both task commits (556e5cb, a40a42a) found in git log
