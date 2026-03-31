---
phase: 03-company-profile-financial-extraction
plan: 03
subsystem: extract
tags: [xbrl, sec-filings, financial-statements, company-facts, income-statement, balance-sheet, cash-flow]

# Dependency graph
requires:
  - phase: 03-01
    provides: ExtractionReport, xbrl_mapping (resolve_concept, get_period_values), XBRL concepts config
provides:
  - Financial statement extraction from XBRL Company Facts API
  - Income statement, balance sheet, cash flow with up to 3 annual periods
  - YoY change calculations for each line item
  - Per-statement ExtractionReport with coverage tracking
  - Tier 2 edgartools fallback scaffold
affects: [03-04, 03-05, 03-06, 03-07, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-tier XBRL extraction: Company Facts API primary, edgartools fallback"
    - "Period labeling from fy field with end-date derivation fallback"
    - "Per-statement ExtractionReport with coverage-driven confidence"

key-files:
  created:
    - src/do_uw/stages/extract/financial_statements.py
    - tests/test_financial_statements.py
  modified: []

key-decisions:
  - "Public helper functions (fiscal_year_label, determine_periods, compute_yoy_change) for testability"
  - "cast() for JSON type narrowing from AcquiredData.filings dict (pyright strict compliance)"
  - "CIK accessed via state.company.identity.cik SourcedValue path (not state.company.cik)"

patterns-established:
  - "Financial extraction pattern: resolve concepts -> determine periods -> build line items -> compute YoY -> report"
  - "SourcedValue provenance: source includes form type, end date, CIK, accession number"

# Metrics
duration: 6min
completed: 2026-02-08
---

# Phase 3 Plan 3: Financial Statement Extraction Summary

**Three-statement XBRL extraction (income, balance sheet, cash flow) from Company Facts API with period labeling, YoY change, deduplication, and per-statement ExtractionReport coverage tracking**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-08T05:33:53Z
- **Completed:** 2026-02-08T05:39:43Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- Extract income statement (22 concepts), balance sheet (21 concepts), cash flow (7 concepts) from XBRL Company Facts
- YoY change calculation with zero-division protection and multi-period support
- Deduplication via resolve_concept (10-K preferred, latest filed wins)
- Per-statement ExtractionReport with coverage percentage and confidence thresholds
- Tier 2 edgartools fallback scaffold (triggers at <50% Tier 1 coverage)
- 18 comprehensive tests covering all extraction paths and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Create financial_statements.py** - `acfe81b` (feat)
2. **Task 2: Create test_financial_statements.py** - `5b232aa` (test)

## Files Created/Modified
- `src/do_uw/stages/extract/financial_statements.py` - Two-tier financial statement extraction from XBRL (485 lines)
- `tests/test_financial_statements.py` - 18 tests covering extraction, YoY, dedup, reports, edge cases (481 lines)

## Decisions Made
- Made helper functions public (no underscore) for direct testability: `fiscal_year_label`, `determine_periods`, `compute_yoy_change`
- Used `cast(dict[str, Any], raw)` for Company Facts type narrowing from `AcquiredData.filings` (pyright strict requires explicit cast on dict values from `dict[str, Any]`)
- CIK access path: `state.company.identity.cik.value` (SourcedValue wrapper on CompanyIdentity, not direct on CompanyProfile)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CIK access path incorrect in plan**
- **Found during:** Task 1 (financial_statements.py creation)
- **Issue:** Plan referenced `state.company.cik` but CompanyProfile has CIK at `state.company.identity.cik` (a SourcedValue[str])
- **Fix:** Used correct path `state.company.identity.cik.value` with None guards
- **Files modified:** src/do_uw/stages/extract/financial_statements.py
- **Verification:** pyright passes with 0 errors
- **Committed in:** acfe81b (Task 1 commit)

**2. [Rule 1 - Bug] Private helper functions not testable under pyright strict**
- **Found during:** Task 2 (test creation)
- **Issue:** pyright strict reportPrivateUsage prevents importing _underscore functions in tests
- **Fix:** Renamed `_fiscal_year_label`, `_determine_periods`, `_compute_yoy_change` to public equivalents
- **Files modified:** src/do_uw/stages/extract/financial_statements.py
- **Verification:** pyright 0 errors, all 18 tests pass
- **Committed in:** 5b232aa (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for type safety and testability. No scope creep.

## Issues Encountered
- Initial file was 512 lines (over 500-line limit); condensed docstrings to bring to 485 lines

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Financial statements extraction ready for integration into ExtractStage pipeline
- ExtractionReport coverage data available for downstream quality assessment
- FinancialStatements model populated with SourcedValue provenance for every data point
- Ready for distress indicator computation (Plan 03-04) which needs income/balance sheet data

---
*Phase: 03-company-profile-financial-extraction*
*Completed: 2026-02-08*
