---
phase: 129-bug-fixes-and-data-integrity
plan: 03
subsystem: render
tags: [meeting-prep, company-specific, sca-counter, question-generation]

# Dependency graph
requires:
  - phase: 129-01
    provides: Canonical SCA counter (sca_counter.py)
provides:
  - Company-specific meeting prep question generators
  - sca_counter wired into meeting_prep.py and meeting_questions.py
  - _company_name() helper for extracting company name from state
  - 10 specificity tests enforcing no generic templates
affects: [render, benchmark]

# Tech tracking
tech-stack:
  added: []
  patterns: [company-name-injection-via-helper]

key-files:
  created:
    - tests/render/test_meeting_prep_specificity.py
  modified:
    - src/do_uw/stages/render/sections/meeting_questions.py
    - src/do_uw/stages/render/sections/meeting_questions_analysis.py
    - src/do_uw/stages/render/sections/meeting_questions_gap.py
    - src/do_uw/stages/render/sections/meeting_prep.py

key-decisions:
  - "_company_name() helper centralized in meeting_questions.py, imported by sibling modules"
  - "Fallback to state.ticker when legal_name unavailable"

patterns-established:
  - "_company_name(state) pattern: all meeting question generators inject actual company name via shared helper"

requirements-completed: [FIX-03]

# Metrics
duration: 8min
completed: 2026-03-23
---

# Phase 129 Plan 03: Meeting Prep Specificity Summary

**Eliminated generic "the company" templates from all meeting prep question generators, replacing with actual company names via _company_name() helper and wiring canonical SCA counter**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-23T00:12:40Z
- **Completed:** 2026-03-23T00:21:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments
- Replaced all generic "the company" phrases across 4 meeting question generator files with actual company name from state
- Added _company_name() helper that extracts legal_name with ticker fallback
- Wired sca_counter imports into meeting_questions.py and meeting_prep.py for canonical SCA counts
- Created 10 specificity tests verifying company-specific data in every question type

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing specificity tests** - `f6585a94` (test)
2. **Task 1 (GREEN): Company-specific question generation** - `ea198b5b` (feat)

## Files Created/Modified
- `tests/render/test_meeting_prep_specificity.py` - 10 tests enforcing company-specific data in meeting prep questions
- `src/do_uw/stages/render/sections/meeting_questions.py` - Added _company_name() helper, sca_counter import, replaced 3 "the company" occurrences
- `src/do_uw/stages/render/sections/meeting_questions_analysis.py` - Replaced "the company" in bear case and peril map questions
- `src/do_uw/stages/render/sections/meeting_questions_gap.py` - Replaced "the company" in 4 gap/credibility question generators
- `src/do_uw/stages/render/sections/meeting_prep.py` - Added sca_counter import for canonical SCA counting

## Decisions Made
- Centralized _company_name() in meeting_questions.py since it's already the base module imported by analysis and gap modules
- Used legal_name with ticker fallback rather than always using ticker (matches narrative_generator.py pattern)
- Added sca_counter to meeting_prep.py (Word renderer) even though it wasn't directly generating SCA questions yet -- ensures consistency when SCA-specific questions are added later

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- SourcedValue requires `as_of` field -- test helper _sv() created to handle this
- CompanyIdentity.ticker is a plain string, not SourcedValue -- corrected in test fixture
- TierClassification requires score_range_low/high -- added to test fixture
- Pre-existing test failures in test_peril_scoring_html.py (SimpleNamespace missing ceiling_details) -- unrelated to this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All meeting prep question generators now inject company-specific data
- Ready for any future work that adds more question types or SCA-specific questions
- Pre-existing test_peril_scoring_html.py failures should be addressed in a separate fix

---
*Phase: 129-bug-fixes-and-data-integrity*
*Completed: 2026-03-23*
