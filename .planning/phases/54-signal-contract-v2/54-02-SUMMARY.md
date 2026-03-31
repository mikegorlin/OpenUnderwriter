---
phase: 54-signal-contract-v2
plan: 02
subsystem: brain
tags: [yaml, pydantic, field-registry, declarative-mapping, v2-signals]

# Dependency graph
requires:
  - phase: 53-data-store-simplification
    provides: YAML-first BrainLoader, brain/ directory structure
provides:
  - brain/field_registry.yaml with 15 field mappings (7 DIRECT_LOOKUP, 8 COMPUTED)
  - field_registry.py Pydantic-validated loader with lazy caching
  - 22 comprehensive tests for registry loading and validation
affects: [54-03 V2 signal migration, 55 declarative evaluation, field-registry-functions]

# Tech tracking
tech-stack:
  added: []
  patterns: [field-registry-yaml, direct-lookup-vs-computed, dual-root-paths, lazy-cached-loader]

key-files:
  created:
    - src/do_uw/brain/field_registry.yaml
    - src/do_uw/brain/field_registry.py
    - tests/brain/test_field_registry.py
  modified: []

key-decisions:
  - "Paths verified against actual Pydantic model attributes (not research estimates)"
  - "8 of 15 fields classified COMPUTED (board_independence needs *100 conversion, say_on_pay_pct has fallback chain, counts need len())"
  - "Added 'key' field to FieldRegistryEntry for dict-valued SourcedValue sub-extraction (e.g., liquidity dict -> current_ratio key)"

patterns-established:
  - "DIRECT_LOOKUP vs COMPUTED classification: simple SourcedValue traversal vs Python function dispatch"
  - "Dual root convention: extracted.* for ExtractedData, company.* for CompanyProfile"
  - "Dict-valued SourcedValue pattern: path points to SourcedValue[dict], key extracts specific entry"
  - "Lazy-cached YAML loader with _reset_cache() for testing"

requirements-completed: [SCHEMA-05]

# Metrics
duration: 17min
completed: 2026-03-01
---

# Phase 54 Plan 02: Field Registry YAML Summary

**Pydantic-validated field registry mapping 15 logical field names to ExtractedData/CompanyProfile dotted paths with DIRECT_LOOKUP/COMPUTED classification**

## Performance

- **Duration:** 17 min
- **Started:** 2026-03-01T15:37:38Z
- **Completed:** 2026-03-01T15:54:35Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments
- Created brain/field_registry.yaml with 15 field mappings covering all 5 signal prefixes (FIN, GOV, LIT, STOCK, BIZ) needed by Plan 54-03 V2 migration
- All dotted paths verified against actual Pydantic model attribute names (corrected multiple paths from research estimates: e.g., `extracted.market.stock_analysis.decline_from_high` -> `extracted.market.stock.decline_from_high_pct`)
- Pydantic loader with `extra='forbid'` catches YAML typos immediately, model_validator enforces type-specific required fields
- 22 tests covering loading, validation, caching, error cases, and custom YAML paths

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain/field_registry.yaml with initial field mappings** - `5dd0ab5` (feat)
2. **Task 2: Create field_registry.py loader module** - `7d5974a` (feat)
3. **Task 3: Write field registry tests** - `4ce519e` (test)

## Files Created/Modified
- `src/do_uw/brain/field_registry.yaml` - 15 field mappings (7 DIRECT_LOOKUP, 8 COMPUTED) with descriptions and verified paths
- `src/do_uw/brain/field_registry.py` - Pydantic-validated loader (131 lines) with lazy caching, get_field_entry() convenience, _reset_cache() for testing
- `tests/brain/test_field_registry.py` - 22 tests across 5 test classes (loading, get_field_entry, cache, validation, custom YAML)

## Decisions Made
- **Path corrections from research**: Research proposed paths like `extracted.financials.liquidity.current_ratio` but the actual model uses a SourcedValue[dict] at `extracted.financials.liquidity` with key `current_ratio`. Added `key` field to FieldRegistryEntry to handle this pattern.
- **More COMPUTED than expected**: 8 of 15 fields (53%) are COMPUTED, not the ~30% estimated by research. `board_independence` needs *100 conversion, `say_on_pay_pct` has a dual-source fallback chain, and all list counts need len(). This confirms the research finding that simple path traversal is insufficient for many fields.
- **Reused `count_items` function name**: Two COMPUTED fields (`filing_13d_count`, `product_liability_count`) can share the same generic `count_items` function (both just need len()). This avoids proliferating trivial one-off functions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected YAML paths to match actual Pydantic models**
- **Found during:** Task 1 (field_registry.yaml creation)
- **Issue:** Plan's example paths (from research) did not match actual model attribute names. Examples: `extracted.financials.coverage.interest_coverage` -> correct path is `extracted.financials.leverage` (SourcedValue[dict] with key `interest_coverage`); `extracted.market.stock_analysis.decline_from_high` -> correct is `extracted.market.stock.decline_from_high_pct`; `extracted.governance.board_composition.independence_ratio` -> correct is `extracted.governance.board.independence_ratio`
- **Fix:** Read all 5 model files (state.py, financials.py, market.py, governance.py, litigation.py, company.py) and verified every path against actual Pydantic field names
- **Files modified:** src/do_uw/brain/field_registry.yaml
- **Verification:** All paths correspond to actual model attributes confirmed via source code review

**2. [Rule 2 - Missing Critical] Added `key` field to FieldRegistryEntry for dict-valued SourcedValues**
- **Found during:** Task 1 (field_registry.yaml creation)
- **Issue:** Plan's FieldRegistryEntry schema only had `path` for DIRECT_LOOKUP, but financial fields like `current_ratio` live inside SourcedValue[dict] at `extracted.financials.liquidity` -- need both path AND key
- **Fix:** Added optional `key: str | None` field to FieldRegistryEntry for sub-extraction from dict-valued SourcedValues
- **Files modified:** src/do_uw/brain/field_registry.py, src/do_uw/brain/field_registry.yaml
- **Verification:** Pydantic validation passes, tests confirm key field loaded correctly

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both auto-fixes necessary for correctness. Path corrections prevent runtime errors in Phase 55. The `key` field addition is essential for the dict-valued SourcedValue pattern used by financial fields.

## Issues Encountered
- Pre-existing test failures (test_brain_enrich.py, test_enriched_roundtrip.py, test_enrichment.py) related to MANAGEMENT_DISPLAY report_section count (expects 99, gets 98). Not caused by this plan's changes -- logged as out-of-scope.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Field registry is ready for Plan 54-03 (V2 signal migration) -- all 15 field_keys referenced by the migration candidates have registry entries
- Phase 55 will need to implement the actual path resolver and COMPUTED function dispatcher using this registry
- FIELD_FOR_CHECK remains untouched per locked decision -- zero legacy code changes

## Self-Check: PASSED

All files verified present, all commits verified in git log.

---
*Phase: 54-signal-contract-v2*
*Plan: 02*
*Completed: 2026-03-01*
