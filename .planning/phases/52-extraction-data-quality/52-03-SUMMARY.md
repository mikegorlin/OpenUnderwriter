---
phase: 52-extraction-data-quality
plan: 03
subsystem: extract
tags: [litigation, llm, filtering, validation, boilerplate, 10-K]

# Dependency graph
requires:
  - phase: 52-01
    provides: "Board extraction improvements (qualification tags, age)"
provides:
  - "Tightened 10-K LLM prompt requiring named parties, court, and filing date for legal proceedings"
  - "_meets_minimum_evidence() post-extraction filter dropping hollow CaseDetail records"
  - "_is_generic_label() catching 12 boilerplate case name patterns"
  - "Borderline evidence handling: named-parties-only cases kept at LOW confidence"
  - "SNA regression test verifying 0 false SCAs from boilerplate language"
affects: [score, analyze, render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Defense-in-depth extraction validation: prompt tightening + post-extraction filter"
    - "Borderline evidence confidence downgrade via parameterized confidence in converter"

key-files:
  created: []
  modified:
    - src/do_uw/stages/extract/llm/prompts.py
    - src/do_uw/stages/extract/llm_litigation.py
    - tests/test_llm_litigation_converter.py

key-decisions:
  - "Borderline cases (named parties but no court/date) kept at LOW confidence, not dropped"
  - "Check _is_borderline_evidence before _meets_minimum_evidence to ensure borderline cases survive filtering"
  - "Confidence parameter threaded through _convert_one_proceeding for all SourcedValue fields"

patterns-established:
  - "Post-extraction validation pattern: filter hollow LLM output before domain model conversion"
  - "Generic label set for boilerplate detection (12 patterns, case-insensitive)"

requirements-completed: [DQ-03]

# Metrics
duration: 6min
completed: 2026-02-28
---

# Phase 52 Plan 03: Litigation False Positive Filtering Summary

**Defense-in-depth filtering for 10-K litigation extraction: tightened LLM prompt + _meets_minimum_evidence post-extraction filter + 12-pattern generic label set, with borderline cases preserved at LOW confidence**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-28T18:04:59Z
- **Completed:** 2026-02-28T18:10:35Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Tightened 10-K system prompt to require named plaintiff/agency, court/jurisdiction, and filing date for legal proceedings extraction
- Added _meets_minimum_evidence() and _is_generic_label() post-extraction filters to drop hollow CaseDetail records
- Implemented borderline evidence handling: cases with named parties but no court/date are kept at LOW confidence (not dropped)
- Added 17 new tests including SNA regression test verifying 0 false SCAs from boilerplate language
- All 55 litigation converter tests pass (38 existing + 17 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Tighten 10-K prompt and add minimum evidence filter** - `14bbf1f` (feat)
2. **Task 2: Add litigation filter tests and SNA regression coverage** - `da69a00` (test)

## Files Created/Modified
- `src/do_uw/stages/extract/llm/prompts.py` - Tightened Item 3 extraction instruction requiring specificity
- `src/do_uw/stages/extract/llm_litigation.py` - Added _meets_minimum_evidence(), _is_generic_label(), _is_borderline_evidence(), updated convert_legal_proceedings() flow, parameterized confidence in _convert_one_proceeding()
- `tests/test_llm_litigation_converter.py` - 17 new tests: TestMeetsMinimumEvidence (7), TestIsGenericLabel (4), TestIsBorderlineEvidence (3), TestConvertLegalProceedingsFiltering (3 including SNA regression)

## Decisions Made
- Borderline cases (named parties but no court/date) kept at LOW confidence per user decision -- not dropped
- Check _is_borderline_evidence before _meets_minimum_evidence to avoid premature filtering of borderline cases
- Confidence parameter threaded through all SourcedValue construction in _convert_one_proceeding (not just a post-hoc override)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed borderline evidence ordering in convert_legal_proceedings**
- **Found during:** Task 2 (test writing revealed logic bug)
- **Issue:** _meets_minimum_evidence() returned False for borderline cases (named parties only), causing them to be dropped before _is_borderline_evidence() check
- **Fix:** Reordered checks: _is_borderline_evidence first (keeps at LOW), then _meets_minimum_evidence (drops hollow)
- **Files modified:** src/do_uw/stages/extract/llm_litigation.py
- **Verification:** test_borderline_kept_at_low_confidence passes
- **Committed in:** da69a00 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential fix for correctness of borderline evidence handling. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 Phase 52 plans complete (52-01 board extraction, 52-02 earnings guidance, 52-03 litigation filtering, 52-04 volume spikes)
- Litigation extraction now has defense-in-depth filtering preventing false SCAs from boilerplate 10-K language
- Phase 52 data quality improvements ready for validation against real pipeline runs

## Self-Check: PASSED

All files found, all commits verified.

---
*Phase: 52-extraction-data-quality*
*Completed: 2026-02-28*
