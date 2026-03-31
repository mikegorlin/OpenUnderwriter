---
phase: 67-xbrl-first
plan: 03
subsystem: extract
tags: [xbrl, derived-metrics, financial-ratios, margins, computation]

# Dependency graph
requires:
  - "67-01: 113 XBRL concept mappings with expected_sign + 25 derived concept stubs"
provides:
  - "24 derived concept computations (margins, ratios, per-share, balance sheet)"
  - "compute_derived_concepts() single-period API"
  - "compute_multi_period_derived() cross-period API with revenue_growth_yoy"
  - "Derived line items integrated into FinancialStatement objects with DERIVED provenance"
affects: [68, 69, 70, 73]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DerivedDef registry pattern for formula definitions with safe arithmetic"
    - "DERIVED provenance in SourcedValue source field (DERIVED:{inputs} CIK{cik})"
    - "Intermediate derived concepts (statement=derived) excluded from statement line items"

key-files:
  created:
    - src/do_uw/stages/extract/xbrl_derived.py
    - tests/test_xbrl_derived.py
  modified:
    - src/do_uw/stages/extract/financial_statements.py

key-decisions:
  - "DerivedDef dataclass registry pattern for all 24 formulas with safe arithmetic helpers"
  - "Intermediate concepts (working_capital, ebitda with statement=derived) not added to statement line items"
  - "DERIVED provenance format: DERIVED:{input_concepts} CIK{cik} for full traceability"

patterns-established:
  - "DerivedDef registry: name, inputs, compute function, statement, description"
  - "Safe arithmetic: _safe_div, _safe_sub, _safe_add -- None/zero-safe, never raise"
  - "_collect_primitives_by_period + _add_derived_line_items integration pattern"

requirements-completed: [XBRL-03]

# Metrics
duration: 8min
completed: 2026-03-06
---

# Phase 67 Plan 03: Derived Concept Computation Summary

**24 derived financial metrics (margins, ratios, per-share) computed from XBRL primitives with zero LLM, integrated into extraction pipeline as FinancialLineItem entries with DERIVED provenance**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-06T06:22:01Z
- **Completed:** 2026-03-06T06:30:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Built xbrl_derived.py with 24 derived concepts: 7 income (margins, tax rate, coverage), 11 balance sheet (ratios, book value, ROA/ROE), 6 cash flow (FCF, capex, payout)
- All computations None-safe, zero-division-safe, exception-free via safe arithmetic helpers
- Integrated into extraction pipeline: derived line items appear in FinancialStatement objects with DERIVED:{inputs} provenance
- 36 unit tests covering all concepts + edge cases + multi-period revenue growth

## Task Commits

Each task was committed atomically:

1. **Task 1: Derived concept computation module (TDD)**
   - `05d144f` (test: failing tests for derived concept computation)
   - `738292f` (feat: implement derived concept computation module)
2. **Task 2: Integrate derived computation into extraction pipeline**
   - `4644153` (feat: integrate derived computation into extraction pipeline)

_TDD flow: RED (failing tests) then GREEN (implementation) for Task 1_

## Files Created/Modified
- `src/do_uw/stages/extract/xbrl_derived.py` - 24 derived concept definitions with DerivedDef registry, safe arithmetic helpers, single-period and multi-period computation APIs
- `tests/test_xbrl_derived.py` - 36 tests: margins, ratios, balance sheet, cash flow, edge cases (None, zero, partial), multi-period with revenue_growth_yoy
- `src/do_uw/stages/extract/financial_statements.py` - Added _collect_primitives_by_period(), _add_derived_line_items(), integration call after Tier 2 fallback

## Decisions Made
- DerivedDef dataclass registry pattern (name, inputs, compute, statement, description) for clean extensibility
- Intermediate concepts (working_capital, ebitda with statement="derived") excluded from statement line items -- they are used by other derived concepts but are not displayable financial statement rows
- DERIVED provenance format includes input concept names for full traceability (e.g., "DERIVED:revenue+cost_of_revenue CIK320193")
- revenue_growth_yoy computed only in multi-period context (requires consecutive periods)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Linter auto-removed xbrl_derived import**
- **Found during:** Task 2 (integration)
- **Issue:** ruff auto-formatter removed the `from do_uw.stages.extract.xbrl_derived import ...` line due to import ordering
- **Fix:** Placed import between validation and xbrl_mapping imports (alphabetical order) to satisfy ruff
- **Files modified:** src/do_uw/stages/extract/financial_statements.py
- **Verification:** Import persists after linter runs, all 54 tests pass
- **Committed in:** 4644153 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Import ordering fix only. No scope creep.

## Issues Encountered
- 4 pre-existing test failures unrelated to this plan: test_enriched_roundtrip.py (Pydantic validation), test_xbrl_coverage.py (module not yet created), test_enrichment.py (content type counts), test_migrate.py (section check counts)
- edgartools IdentityNotSetException in test runs from Tier 2 fallback (expected -- no SEC access in test context, properly caught by exception handler)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 24 derived concepts available for signal wiring (Phase 70)
- Derived line items render in existing financial statement templates
- Multi-period revenue_growth_yoy ready for trend analysis (Phase 68)
- Phase 67 complete: all 3 plans delivered (concept expansion, sign normalization, derived computation)

---
*Phase: 67-xbrl-first*
*Completed: 2026-03-06*
