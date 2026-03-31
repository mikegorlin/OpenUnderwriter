---
phase: 140-litigation-classification-consolidation
plan: 01
subsystem: extract
tags: [litigation, classifier, dedup, coverage-type, legal-theory, boilerplate]

requires:
  - phase: 128-infrastructure-foundation
    provides: "Extraction pipeline orchestrator, CaseDetail model, LitigationLandscape"
provides:
  - "Unified post-extraction litigation classifier (classify_all_cases)"
  - "Universal cross-list deduplication (deduplicate_all_cases)"
  - "Year disambiguation on all case names (disambiguate_by_year)"
  - "Missing field flagging for ACQUIRE recovery (flag_missing_fields)"
  - "Boilerplate reserve separation (unclassified_reserves)"
  - "LitigationLandscape.unclassified_reserves and cases_needing_recovery fields"
affects: [140-02, rendering-litigation, scoring-litigation]

tech-stack:
  added: []
  patterns: [post-extraction-classifier-pipeline, confidence-preserving-overwrite, cross-list-dedup]

key-files:
  created:
    - src/do_uw/stages/extract/litigation_classifier.py
    - tests/stages/extract/test_litigation_classifier.py
  modified:
    - src/do_uw/stages/extract/extract_litigation.py
    - src/do_uw/models/litigation.py

key-decisions:
  - "DEDUP_THRESHOLD at 0.70 (lower than SCA-specific 0.80 to catch cross-type matches)"
  - "Confidence-preserving overwrite: existing HIGH confidence classifications not replaced by MEDIUM regex detection (Pitfall 3)"
  - "Boilerplate filter guards against false positives: cases with detail fields (court, date, settlement) kept even with generic names (Pitfall 5)"
  - "Regulatory proceedings and deal litigation skipped by classifier (different model types, per Research Open Questions 2 and 3)"

patterns-established:
  - "Post-extraction classifier pipeline: classify -> dedup -> disambiguate -> flag (order matters)"
  - "Confidence-aware field merging: highest confidence source wins per field during dedup"

requirements-completed: [LIT-01, LIT-02, LIT-03, LIT-04, LIT-05]

duration: 11min
completed: 2026-03-28
---

# Phase 140 Plan 01: Unified Litigation Classifier Summary

**Post-extraction litigation classifier with 4 public functions covering legal theory classification, cross-list deduplication, year disambiguation, missing field flagging, and boilerplate separation**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-28T01:33:24Z
- **Completed:** 2026-03-28T01:44:08Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created litigation_classifier.py with EXTENDED_THEORY_PATTERNS covering all 12 LegalTheory enum values
- Universal dedup engine merges cases across SCA + derivative lists with 70% word overlap threshold and filing year gap check
- Boilerplate filter separates generic reserves to unclassified_reserves while protecting cases with detail fields (Pitfall 5)
- 23 passing tests across 6 test classes covering all 5 LIT requirements + D-07 boilerplate filter
- Wired 4-pass classifier into extract_litigation.py between cross-validation and summary generation

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for classifier** - `0866c749` (test)
2. **Task 1 GREEN: Create classifier module + model fields** - `cb333d47` (feat)
3. **Task 2: Wire classifier into extract_litigation.py** - `1a497230` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/litigation_classifier.py` - Unified classifier with 4 public functions + extended theory patterns
- `tests/stages/extract/test_litigation_classifier.py` - 23 unit tests across 6 test classes
- `src/do_uw/stages/extract/extract_litigation.py` - 4-pass classifier wired after cross-validation
- `src/do_uw/models/litigation.py` - Added unclassified_reserves and cases_needing_recovery fields to LitigationLandscape

## Decisions Made
- DEDUP_THRESHOLD set to 0.70 (lower than SCA-specific 0.80 per RESEARCH.md recommendation, catches cross-type matches better for shorter derivative case names)
- Confidence-preserving overwrite: when unified classifier has MEDIUM confidence and existing has HIGH, keep existing (Pitfall 3 avoidance)
- Boilerplate Pitfall 5 guard: cases with court, filing_date, or settlement_amount fields preserved even with generic names
- Skipped regulatory_proceedings (SourcedValue[dict]) and deal_litigation (DealLitigation model) from classifier per Research Open Questions 2 and 3

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertion for 10b-5 without defendants**
- **Found during:** Task 1 GREEN (running tests)
- **Issue:** Test expected SCA_SIDE_A for 10b-5 without named defendants, but correct behavior per inference logic is SCA_SIDE_C (entity securities coverage when no individuals named)
- **Fix:** Added defendants to test case to correctly test SCA_SIDE_A
- **Files modified:** tests/stages/extract/test_litigation_classifier.py
- **Verification:** All 23 tests pass
- **Committed in:** cb333d47

---

**Total deviations:** 1 auto-fixed (1 bug in test)
**Impact on plan:** Minor test correction. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_narrative_generation.py (TestLitigationNarrative::test_litigation_prompt_is_section_specific) -- unrelated to classifier changes, existed before this plan

## Known Stubs
None -- all functions are fully implemented with real logic.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Classifier is wired and operational for all pipeline runs
- Plan 02 (rendering integration) can consume unclassified_reserves and cases_needing_recovery from LitigationLandscape
- Coverage type and legal theories are now uniformly set by the classifier, not per-extractor

---
*Phase: 140-litigation-classification-consolidation*
*Completed: 2026-03-28*
