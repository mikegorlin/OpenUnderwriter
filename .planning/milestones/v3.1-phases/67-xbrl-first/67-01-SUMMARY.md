---
phase: 67-xbrl-first
plan: 01
subsystem: extract
tags: [xbrl, financial-data, concepts, total-liabilities, sign-convention]

# Dependency graph
requires: []
provides:
  - "113 XBRL concept mappings with expected_sign field (was 50)"
  - "XBRLConcept TypedDict with expected_sign field"
  - "derive_total_liabilities() 4-step cascade function"
  - "23 derived concept stubs for ratios/margins"
  - "Validation test suite for concept config integrity"
affects: [67-02, 67-03, 68, 69, 70, 73]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "expected_sign convention for XBRL sign normalization"
    - "derive_total_liabilities() cascade pattern for multi-source derivation"
    - "Derived concepts in xbrl_concepts.json with statement=derived and empty tags"

key-files:
  created:
    - tests/test_xbrl_concepts.py
    - tests/test_financial_models_tl.py
  modified:
    - src/do_uw/brain/config/xbrl_concepts.json
    - src/do_uw/stages/extract/xbrl_mapping.py
    - src/do_uw/stages/analyze/financial_models.py

key-decisions:
  - "Corrected working_capital and ebitda statement type from income/balance_sheet to derived (semantic fix, they have empty xbrl_tags)"
  - "derive_total_liabilities() extracted as standalone public function for reuse"
  - "expected_sign defaults to 'any' for backward compatibility when field missing from config"

patterns-established:
  - "expected_sign field on every XBRL concept: positive, negative, or any"
  - "Derived concepts use statement=derived with empty xbrl_tags"
  - "Total liabilities derivation via 4-step priority cascade"

requirements-completed: [XBRL-01, XBRL-06]

# Metrics
duration: 7min
completed: 2026-03-06
---

# Phase 67 Plan 01: XBRL Concept Expansion Summary

**Expanded XBRL concept coverage from 50 to 113 concepts with expected_sign field, plus hardened total liabilities derivation with 4-step cascade handling minority interest and L&SE fallback**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-06T06:11:21Z
- **Completed:** 2026-03-06T06:18:40Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Expanded xbrl_concepts.json from 50 to 113 concepts (8 income, 17 balance sheet, 15 cash flow, 23 derived)
- Added expected_sign field to all 113 concepts per DQC 0015 sign conventions
- Built derive_total_liabilities() with 4-step cascade: direct tag, TA-SE, minority interest, L&SE fallback
- Created 23 test cases (10 config integrity + 13 derivation edge cases)

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand xbrl_concepts.json + update XBRLConcept TypedDict**
   - `c8c792e` (test: failing tests for config integrity)
   - `70d70b4` (feat: expand from 50 to 113 concepts with expected_sign)
2. **Task 2: Harden total liabilities derivation cascade**
   - `c0c94b8` (test: failing tests for TL derivation)
   - `4d0866f` (feat: 4-step cascade with minority interest + L&SE)

_TDD flow: RED (failing tests) then GREEN (implementation) for both tasks_

## Files Created/Modified
- `src/do_uw/brain/config/xbrl_concepts.json` - Expanded from 50 to 113 concepts, added expected_sign to all
- `src/do_uw/stages/extract/xbrl_mapping.py` - Added expected_sign to XBRLConcept TypedDict and load_xbrl_mapping()
- `src/do_uw/stages/analyze/financial_models.py` - Extracted derive_total_liabilities(), updated _collect_all_inputs()
- `tests/test_xbrl_concepts.py` - 10 config integrity validation tests
- `tests/test_financial_models_tl.py` - 13 edge case tests for TL derivation cascade

## Decisions Made
- Corrected working_capital and ebitda statement type to "derived" (they had empty xbrl_tags but were labeled as income/balance_sheet)
- derive_total_liabilities() made a public function (not private) for reuse by other modules
- expected_sign defaults to "any" in load_xbrl_mapping() for backward compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed legacy derived concept statement types**
- **Found during:** Task 1 (concept expansion)
- **Issue:** working_capital and ebitda had statement=balance_sheet/income but xbrl_tags=[] (they are derived concepts)
- **Fix:** Changed statement to "derived" for both
- **Files modified:** src/do_uw/brain/config/xbrl_concepts.json
- **Verification:** All 10 config integrity tests pass
- **Committed in:** 70d70b4 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Semantic correction only. No scope creep.

## Issues Encountered
- Pre-existing test failure in tests/knowledge/test_enriched_roundtrip.py (SignalDefinition Pydantic validation errors) -- unrelated to this plan's changes, confirmed by running test on pre-change codebase.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 113 concepts with expected_sign ready for sign normalization (67-02)
- derive_total_liabilities() ready for use in derived computation module (67-03)
- 23 derived concept stubs ready for formula implementation (67-03)
- All 41 plan tests + 594 suite tests pass (1 pre-existing failure excluded)

---
*Phase: 67-xbrl-first*
*Completed: 2026-03-06*
