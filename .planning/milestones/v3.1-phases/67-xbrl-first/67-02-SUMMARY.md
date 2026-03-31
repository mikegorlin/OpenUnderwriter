---
phase: 67-xbrl-first
plan: 02
subsystem: extract
tags: [xbrl, sign-normalization, coverage-validation, data-quality]

# Dependency graph
requires:
  - phase: 67-01
    provides: "113 XBRL concept mappings with expected_sign field"
provides:
  - "normalize_sign() function correcting wrong-sign XBRL values"
  - "Sign normalization integrated into financial statement extraction pipeline"
  - "CoverageReport with per-concept, per-statement resolution tracking"
  - "discover_tags() utility for tag research on Company Facts data"
  - "Alerts when statement coverage drops below 60%"
affects: [67-03, 68, 69, 70, 73]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sign normalization as post-extraction step in _make_sourced_value()"
    - "CoverageReport dataclass for structured validation output"
    - "Informational coverage call (non-blocking) at end of extraction"

key-files:
  created:
    - src/do_uw/stages/extract/xbrl_coverage.py
    - tests/test_sign_normalization.py
    - tests/test_xbrl_coverage.py
  modified:
    - src/do_uw/stages/extract/xbrl_mapping.py
    - src/do_uw/stages/extract/financial_statements.py

key-decisions:
  - "_make_sourced_value() returns tuple[SourcedValue, bool] for normalization tracking (backward-compatible via expected_sign='any' default)"
  - "Coverage validation is informational only -- never blocks extraction"
  - "Derived concepts excluded from coverage calculations (they have no XBRL tags)"

patterns-established:
  - "normalize_sign() standalone function reusable outside extraction pipeline"
  - "ConceptResolution dataclass for per-concept tag audit trail"
  - "Coverage alerts at 60% threshold per statement type"

requirements-completed: [XBRL-02, XBRL-04, XBRL-05]

# Metrics
duration: 5min
completed: 2026-03-06
---

# Phase 67 Plan 02: Sign Normalization + Coverage Validation Summary

**Sign normalization layer correcting wrong-sign XBRL values with audit logging, plus coverage validator tracking per-concept tag resolution rates with 60% alert threshold**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-06T06:21:50Z
- **Completed:** 2026-03-06T06:27:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Built normalize_sign() handling positive/negative/any conventions per DQC 0015
- Integrated sign normalization into _make_sourced_value() with backward-compatible signature
- Created CoverageReport with per-concept ConceptResolution tracking and per-statement breakdown
- Built discover_tags() utility for tag research when adding new XBRL concepts
- 27 new tests (12 sign normalization + 15 coverage validation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Sign normalization layer + integration**
   - `9924448` (test: failing tests for sign normalization)
   - `97f01b1` (feat: implement sign normalization + integration)
2. **Task 2: Coverage validator + tag discovery utility**
   - `aee3128` (test: failing tests for coverage validator)
   - `905ec98` (feat: implement coverage validator + tag discovery)

_TDD flow: RED (failing tests) then GREEN (implementation) for both tasks_

## Files Created/Modified
- `src/do_uw/stages/extract/xbrl_mapping.py` - Added normalize_sign() function
- `src/do_uw/stages/extract/financial_statements.py` - Integrated normalize_sign into _make_sourced_value(), added coverage call
- `src/do_uw/stages/extract/xbrl_coverage.py` - New: CoverageReport, validate_coverage(), discover_tags()
- `tests/test_sign_normalization.py` - 12 tests (unit + integration)
- `tests/test_xbrl_coverage.py` - 15 tests (coverage + discovery)

## Decisions Made
- _make_sourced_value() now returns tuple[SourcedValue, bool] instead of plain SourcedValue; backward compatibility via expected_sign="any" default
- Coverage validation is informational (non-blocking) -- logged via try/except at end of extraction
- Derived concepts excluded from coverage (they are computed, not extracted from XBRL)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing dirty working tree had xbrl_derived imports leaking into financial_statements.py (from Plan 67-03 work); restored to clean committed state each time linter re-added them.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Sign normalization ready for use by derived computation module (67-03)
- Coverage validator ready for pipeline integration
- 45 total tests pass (18 existing + 12 sign normalization + 15 coverage)
- All Plan 67-01 + 67-02 infrastructure ready for 67-03 (derived formulas)

---
*Phase: 67-xbrl-first*
*Completed: 2026-03-06*
