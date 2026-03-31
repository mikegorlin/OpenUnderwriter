---
phase: 23-end-to-end-output-quality
plan: 02
subsystem: extraction
tags: [llm, pydantic, validation, employee-count, cross-validation]

# Dependency graph
requires:
  - phase: 18-llm-extraction-engine
    provides: LLM extraction schemas and TenKExtraction model
  - phase: 03
    provides: Company profile extraction pipeline and SourcedValue system
provides:
  - Explicit LLM extraction prompt for employee headcount (prevents truncation)
  - Post-extraction validation catching implausibly low employee counts
  - Cross-validation of LLM employee count against yfinance data
affects: [23-end-to-end-output-quality, ground-truth-validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Post-extraction numeric validation with cross-source sanity checks"
    - "Revenue-based heuristic for employee count plausibility"

key-files:
  created: []
  modified:
    - src/do_uw/stages/extract/llm/schemas/ten_k.py
    - src/do_uw/stages/extract/company_profile.py
    - tests/test_company_profile.py

key-decisions:
  - "Market cap used as revenue proxy for employee count plausibility (both indicate company size)"
  - "1% ratio threshold for yfinance cross-validation (catches 100x truncation errors)"
  - "1000x multiplier heuristic for large companies with sub-100 employee counts"
  - "Corrected values get MEDIUM confidence (not HIGH) to flag uncertainty"

patterns-established:
  - "Post-extraction validation: pure function validates LLM output against independent sources"
  - "Cross-source sanity check: ratio-based comparison between LLM and yfinance data"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 23 Plan 02: Employee Count Extraction Fix Summary

**Explicit LLM prompt for full integer headcount plus post-extraction validation catching truncated employee counts via yfinance cross-check and revenue heuristic**

## Performance

- **Duration:** 2m 54s
- **Started:** 2026-02-11T22:34:33Z
- **Completed:** 2026-02-11T22:37:27Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Updated 10-K extraction schema to explicitly instruct LLM to return full integer employee count, not abbreviated thousands
- Added _validate_employee_count() function that catches truncated numbers (e.g., 62 instead of 62000 from "approximately 62 thousand")
- Cross-validates LLM count against yfinance data with <1% ratio detection
- Revenue/market-cap heuristic catches implausibly low counts for large companies
- 7 new unit tests covering all validation edge cases, 90 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Improve LLM extraction prompts for numeric fields** - `f24bdfe` (feat)
2. **Task 2: Add post-extraction employee count validation** - `60b205e` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/llm/schemas/ten_k.py` - Updated employee_count field description with explicit full-integer instructions
- `src/do_uw/stages/extract/company_profile.py` - Added _validate_employee_count() and wired into _enrich_from_llm flow
- `tests/test_company_profile.py` - Added TestValidateEmployeeCount class with 7 test cases

## Decisions Made
- Market cap used as company size proxy (revenue not always available at extraction time, but market cap is from yfinance)
- Ratio threshold of 1% catches the XOM scenario (62 vs 62000 = 0.1%) while allowing normal variance
- 1000x multiplier applied when employee count <100 and company >$10B (covers "thousands" truncation pattern)
- Corrected values tagged with MEDIUM confidence and "10-K (LLM, corrected)" source for audit trail

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Employee count extraction now robust against LLM truncation errors
- Validation pattern can be extended to other numeric fields if similar issues found
- Ready for next plan in phase 23

---
*Phase: 23-end-to-end-output-quality*
*Completed: 2026-02-11*
