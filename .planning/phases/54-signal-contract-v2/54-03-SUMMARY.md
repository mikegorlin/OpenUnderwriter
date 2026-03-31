---
phase: 54-signal-contract-v2
plan: "03"
subsystem: brain
tags: [yaml, pydantic, signals, v2-migration, cli]

# Dependency graph
requires:
  - phase: 54-01
    provides: V2 Pydantic sub-models (AcquisitionSpec, EvaluationSpec, PresentationSpec) + schema_version dispatch stub
  - phase: 54-02
    provides: Field registry YAML with 15 field mappings (DIRECT_LOOKUP + COMPUTED)
provides:
  - 15 V2-migrated signals across 5 prefixes with structured acquisition/evaluation/presentation
  - CLI V2 visibility (brain status shows V2 count, brain build validates V2 sections)
  - V2 migration regression test suite (14 tests)
affects: [55-declarative-mapping, 56-facet-rendering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "V2 in-place YAML editing: Add V2 fields after existing V1 fields, preserving all original content"
    - "Structured threshold convention: RED before YELLOW in evaluation.thresholds list (first-match ordering)"
    - "V2 validation in brain build: check all 3 sections present for schema_version >= 2 signals"

key-files:
  created:
    - tests/brain/test_v2_migration.py
  modified:
    - src/do_uw/brain/signals/fin/balance.yaml
    - src/do_uw/brain/signals/fin/accounting.yaml
    - src/do_uw/brain/signals/gov/board.yaml
    - src/do_uw/brain/signals/gov/pay.yaml
    - src/do_uw/brain/signals/gov/activist.yaml
    - src/do_uw/brain/signals/lit/sca.yaml
    - src/do_uw/brain/signals/lit/defense.yaml
    - src/do_uw/brain/signals/lit/other.yaml
    - src/do_uw/brain/signals/stock/price.yaml
    - src/do_uw/brain/signals/stock/short.yaml
    - src/do_uw/brain/signals/stock/ownership.yaml
    - src/do_uw/brain/signals/biz/dependencies.yaml
    - src/do_uw/brain/signals/biz/core.yaml
    - src/do_uw/cli_brain.py
    - src/do_uw/brain/brain_build_signals.py
    - tests/brain/test_v2_schema.py

key-decisions:
  - "Used Edit tool for targeted YAML additions instead of ruamel.yaml (cleaner diffs, no reformatting risk)"
  - "BIZ.SIZE.market_cap thresholds: <$300M = RED (micro-cap), <$2B = YELLOW (small-cap) for D&O risk sizing"
  - "Updated test_v2_schema.py to accept V2 signals (was placeholder from Plan 54-01 assuming no V2 yet)"

patterns-established:
  - "V2 signal YAML structure: schema_version + acquisition + evaluation + presentation added after existing fields"
  - "Threshold ordering: RED thresholds first, YELLOW second (matches legacy try_numeric_compare behavior)"
  - "brain build V2 validation: checks 3 required sections, reports count in CLI output"

requirements-completed: [SCHEMA-06]

# Metrics
duration: 21min
completed: 2026-03-01
---

# Phase 54 Plan 03: V2 Signal Migration + CLI Updates + Verification Summary

**15 signals migrated to V2 format across all 5 prefixes (FIN/GOV/LIT/STOCK/BIZ) with structured thresholds, acquisition specs, and presentation levels; CLI updated for V2 visibility; 14 regression tests passing**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-01T16:07:22Z
- **Completed:** 2026-03-01T16:28:32Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments
- Migrated 15 signals to V2 format with all 3 V2 sections (acquisition, evaluation, presentation)
- All 5 required prefixes covered: FIN (3), GOV (3), LIT (3), STOCK (3), BIZ (3)
- CLI shows V2 progress: `brain status` reports "V2 signals: 15/400 (3%)" and field registry count; `brain build` validates V2 sections
- 14 V2 migration regression tests covering count, coverage, threshold ordering, field registry references, Pydantic validation, and threshold value consistency
- 400 total signals still load correctly -- zero breakage

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate 15 signals to V2 format** - `bc3ae47` (feat)
2. **Task 2: Update CLI for V2 visibility** - `971e3e4` (feat)
3. **Task 3: V2 migration regression tests** - `b78fc39` (test)

## Files Created/Modified
- `src/do_uw/brain/signals/fin/balance.yaml` - V2 fields on FIN.LIQ.position and FIN.DEBT.coverage
- `src/do_uw/brain/signals/fin/accounting.yaml` - V2 fields on FIN.ACCT.restatement
- `src/do_uw/brain/signals/gov/board.yaml` - V2 fields on GOV.BOARD.independence
- `src/do_uw/brain/signals/gov/pay.yaml` - V2 fields on GOV.PAY.say_on_pay
- `src/do_uw/brain/signals/gov/activist.yaml` - V2 fields on GOV.ACTIVIST.13d_filings
- `src/do_uw/brain/signals/lit/sca.yaml` - V2 fields on LIT.SCA.active
- `src/do_uw/brain/signals/lit/defense.yaml` - V2 fields on LIT.DEFENSE.contingent_liabilities
- `src/do_uw/brain/signals/lit/other.yaml` - V2 fields on LIT.OTHER.product
- `src/do_uw/brain/signals/stock/price.yaml` - V2 fields on STOCK.PRICE.recent_drop_alert
- `src/do_uw/brain/signals/stock/short.yaml` - V2 fields on STOCK.SHORT.position
- `src/do_uw/brain/signals/stock/ownership.yaml` - V2 fields on STOCK.VALUATION.pe_ratio
- `src/do_uw/brain/signals/biz/dependencies.yaml` - V2 fields on BIZ.DEPEND.customer_conc
- `src/do_uw/brain/signals/biz/core.yaml` - V2 fields on BIZ.STRUCT.subsidiary_count and BIZ.SIZE.market_cap
- `src/do_uw/cli_brain.py` - V2 signal count in brain status, V2 validation count in brain build
- `src/do_uw/brain/brain_build_signals.py` - V2 section validation step (step 5), v2_signals return key
- `tests/brain/test_v2_migration.py` - 14 regression tests for V2 migration
- `tests/brain/test_v2_schema.py` - Updated to allow V2 signals (was placeholder)

## Decisions Made
- Used Edit tool for targeted YAML insertions rather than ruamel.yaml, since manual targeted edits produce cleaner git diffs with zero risk of reformatting V1 fields
- BIZ.SIZE.market_cap thresholds set at <$300M RED and <$2B YELLOW to align with D&O underwriting size risk tiers
- Updated test_v2_schema.py to accept V2 signals (changed test_all_signals_have_schema_version_1_by_default to test_signals_have_valid_schema_version)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_v2_schema.py test that assumed no V2 signals**
- **Found during:** Task 3 (regression test run)
- **Issue:** `test_all_signals_have_schema_version_1_by_default` from Plan 54-01 asserted all signals have schema_version=1, but we just migrated 15 to V2
- **Fix:** Renamed to `test_signals_have_valid_schema_version`, now accepts 1 or 2 and asserts at least 12 V2 signals exist
- **Files modified:** tests/brain/test_v2_schema.py
- **Verification:** All brain tests pass (443 passed)
- **Committed in:** b78fc39 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Expected update -- the Plan 54-01 test was a placeholder for pre-migration state. No scope creep.

## Issues Encountered
- Pre-existing test failure in `test_brain_enrich.py::test_management_display_have_report_section` (expects 99, gets 98 MANAGEMENT_DISPLAY with report_section). This was pre-existing before V2 changes and is unrelated to this plan. Logged as out-of-scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 54 complete: V2 Pydantic models (54-01), field registry (54-02), and signal migration (54-03) all done
- 15 V2 signals with structured thresholds ready for Phase 55 declarative evaluation
- Schema version dispatch stub in signal_engine.py ready to be filled with V2 evaluator (Phase 55)
- Field registry has 15 field mappings for the 15 migrated signals
- Pre-existing enrichment test issue does not affect V2 functionality

## Self-Check: PASSED

All 18 files verified present. All 3 commits verified in git log.

---
*Phase: 54-signal-contract-v2*
*Completed: 2026-03-01*
