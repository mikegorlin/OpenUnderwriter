---
phase: 73-rendering-bugs
plan: 03
subsystem: scoring, rendering
tags: [sca-filter, boilerplate, crf-1, pdf-header, company-logo, css-print]

requires:
  - phase: 73-rendering-bugs
    provides: "Phase 73 context and research on false SCA bug, PDF header overlap, logo implementation"
provides:
  - "3-layer false SCA classification filter (prompt + pattern + specificity gate)"
  - "PDF header overlap fix via @media print padding"
  - "Company logo fallback (CSS initial-letter) and PDF-mode sizing"
  - "Page-break-inside rules for forensic-band and beneish-table"
affects: [scoring, rendering, extract-litigation]

tech-stack:
  added: []
  patterns:
    - "Case specificity gate: _has_case_specificity() checks named plaintiff, court, case number, filing date"
    - "Boilerplate 14-pattern list in _BOILERPLATE_PATTERNS for false SCA filtering"
    - "CSS onerror fallback for company logo (inline initial-letter span)"

key-files:
  created:
    - tests/test_false_sca_filter.py
  modified:
    - src/do_uw/stages/extract/llm/prompts.py
    - src/do_uw/stages/analyze/signal_mappers_ext.py
    - src/do_uw/stages/score/red_flag_gates.py
    - src/do_uw/stages/score/red_flag_gates_enhanced.py
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/sections/identity.html.j2
    - src/do_uw/templates/html/base.html.j2

key-decisions:
  - "Moved stock drop, SPAC, short seller helpers from red_flag_gates.py to red_flag_gates_enhanced.py for 500-line compliance"
  - "Case specificity gate accepts partial specificity (any 1 of 4 fields) to avoid over-filtering real SCAs"
  - "Unverified SCAs still trigger CRF-1 (conservative) but evidence includes '(unverified)' caveat"
  - "CSS-only initial-letter fallback for company logo (no JavaScript required)"

patterns-established:
  - "3-layer filter pattern: LLM prompt hardening + pattern matching + specificity gate for data quality"
  - "Function delegation to _enhanced.py when main module exceeds 500 lines"

requirements-completed: [RENDER-06, RENDER-07, RENDER-08, RENDER-09]

duration: 8min
completed: 2026-03-07
---

# Phase 73 Plan 03: Bug Fixes Summary

**3-layer false SCA filter eliminating boilerplate CRF-1 triggers, PDF header overlap fix, company logo with CSS fallback**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-07T02:50:58Z
- **Completed:** 2026-03-07T02:59:21Z
- **Tasks:** 2 (Task 1 TDD, Task 2 auto)
- **Files modified:** 8

## Accomplishments
- Eliminated false SCA classification from boilerplate 10-K litigation language via 3-layer filter
- 17 new tests covering boilerplate patterns, specificity gate, and CRF-1 integration
- Fixed PDF header overlap on first page via @media print padding-top
- Added CSS-only company logo fallback (initial letter in styled circle) and PDF-mode larger sizing
- Moved stock drop/SPAC/short seller gate helpers to red_flag_gates_enhanced.py to keep red_flag_gates.py under 500 lines

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for false SCA filter** - `fc5c1aa` (test)
2. **Task 1 GREEN: 3-layer false SCA filter implementation** - `9d79029` (feat)
3. **Task 2: PDF header fix, logo polish, HTML/PDF parity** - `7555821` (fix)

## Files Created/Modified
- `tests/test_false_sca_filter.py` - 17 tests covering all 3 filter layers
- `src/do_uw/stages/extract/llm/prompts.py` - Hardened 10-K extraction prompt with explicit boilerplate rejection examples
- `src/do_uw/stages/analyze/signal_mappers_ext.py` - Expanded _BOILERPLATE_PATTERNS from 6 to 14 patterns
- `src/do_uw/stages/score/red_flag_gates.py` - Added _has_case_specificity() gate and unverified SCA caveat (496 lines)
- `src/do_uw/stages/score/red_flag_gates_enhanced.py` - Received stock drop, SPAC, short seller helpers (376 lines)
- `src/do_uw/templates/html/styles.css` - PDF header overlap fix, forensic component page-break rules (540 lines)
- `src/do_uw/templates/html/sections/identity.html.j2` - Logo with alt text, PDF sizing, CSS fallback
- `src/do_uw/templates/html/base.html.j2` - Topbar logo alt text and onerror fallback

## Decisions Made
- Moved 3 CRF gate functions (stock drops, SPAC, short seller) from red_flag_gates.py to red_flag_gates_enhanced.py to accommodate the specificity gate while staying under 500 lines
- Case specificity gate uses OR logic (any 1 of: named plaintiff, court, case number, filing date) to avoid over-filtering legitimate SCAs with partial information
- Unverified SCAs still trigger CRF-1 (conservative approach -- better to flag and note than miss) but evidence text includes "(unverified)" caveat
- Logo fallback uses CSS-only initial letter in navy circle (no JavaScript required, works in PDF)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] red_flag_gates.py exceeded 500-line limit**
- **Found during:** Task 1 (adding _has_case_specificity)
- **Issue:** File was already at 529 lines before changes; adding specificity gate pushed it to 577
- **Fix:** Moved _check_spac_under_5, _check_short_seller_report, _check_catastrophic_decline, and _check_recent_drop to red_flag_gates_enhanced.py as public functions with lazy import wrappers
- **Files modified:** red_flag_gates.py (496 lines), red_flag_gates_enhanced.py (376 lines)
- **Verification:** All 478 scoring tests pass
- **Committed in:** 9d79029 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary refactoring for 500-line compliance. No scope creep.

## Issues Encountered
- Multiple pre-existing test failures in working tree from uncommitted 73-01/73-02 plan changes (test_pdf_paged, test_html_layout, test_peril_scoring_html, test_llm_litigation_integration). These are NOT caused by 73-03 changes and are out of scope. Verified via git stash comparison.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- False SCA filter is production-ready for all tickers
- PDF header overlap fix applies automatically to all future renders
- Pre-existing test failures from 73-01/73-02 uncommitted changes need resolution before full test suite passes

---
*Phase: 73-rendering-bugs*
*Completed: 2026-03-07*
