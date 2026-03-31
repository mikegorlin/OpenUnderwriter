---
phase: 27-peril-mapping-bear-case-framework
plan: 01
subsystem: analyze
tags: [data-status, pipeline-audit, check-results, three-state, coverage-gaps]

# Dependency graph
requires:
  - phase: 26-check-reorganization
    provides: "CheckResult model with classification fields, check_classification.json"
provides:
  - "DataStatus enum (EVALUATED, DATA_UNAVAILABLE, NOT_APPLICABLE) on CheckResult"
  - "Pipeline audit tooling (audit_check_pipeline, audit_all_checks, format_audit_report)"
  - "data_status and data_status_reason fields on every CheckResult"
affects: [27-04-coverage-gaps, 27-02-peril-mapping, render]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Three-state data provenance on check results", "Pipeline audit pattern for identifying unwired checks"]

key-files:
  created:
    - src/do_uw/stages/analyze/pipeline_audit.py
    - tests/stages/analyze/test_data_status.py
    - tests/stages/analyze/test_pipeline_audit.py
  modified:
    - src/do_uw/stages/analyze/check_results.py
    - src/do_uw/stages/analyze/check_engine.py

key-decisions:
  - "DataStatus uses str type for CheckResult field (not enum) to ensure JSON serialization compat with dict[str, Any] storage"
  - "NOT_APPLICABLE detection via sector_filter field in check config as best-effort first pass"
  - "_determine_data_status called after evaluate_check for consistent status assignment"

patterns-established:
  - "Three-state data status: EVALUATED/DATA_UNAVAILABLE/NOT_APPLICABLE replaces ambiguous SKIPPED"
  - "Pipeline audit: programmatic check coverage assessment with category/section breakdowns"

# Metrics
duration: 6min
completed: 2026-02-12
---

# Phase 27 Plan 01: Data Status & Pipeline Audit Summary

**Three-state DataStatus enum (EVALUATED/DATA_UNAVAILABLE/NOT_APPLICABLE) on CheckResult with pipeline audit tooling to identify unwired checks**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-12T20:53:40Z
- **Completed:** 2026-02-12T20:59:47Z
- **Tasks:** 2
- **Files modified:** 5 (2 modified, 3 created)

## Accomplishments
- DataStatus enum with three values distinguishing checked-and-found from couldn't-check from doesn't-apply
- Backward-compatible data_status and data_status_reason fields on CheckResult (default "EVALUATED")
- Check engine automatically sets DATA_UNAVAILABLE on SKIPPED results and NOT_APPLICABLE for sector-filtered checks
- Pipeline audit module: audit_check_pipeline(), audit_all_checks(), format_audit_report() for programmatic coverage assessment
- 37 new tests (22 data_status + 15 pipeline audit), 0 regressions across 2794 total tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add DataStatus enum and data_status fields to CheckResult, update check engine** - `b4ad95e` (feat)
2. **Task 2: Build pipeline audit tooling to identify unwired checks** - `01b91e5` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/check_results.py` - Added DataStatus enum, data_status/data_status_reason fields on CheckResult
- `src/do_uw/stages/analyze/check_engine.py` - _make_skipped sets DATA_UNAVAILABLE, _determine_data_status helper, sector applicability check
- `src/do_uw/stages/analyze/pipeline_audit.py` - New: audit_check_pipeline, audit_all_checks, format_audit_report
- `tests/stages/analyze/test_data_status.py` - New: 22 tests for DataStatus, CheckResult fields, helpers
- `tests/stages/analyze/test_pipeline_audit.py` - New: 15 tests for pipeline audit module

## Decisions Made
- Used str type for data_status field (not DataStatus enum directly) to preserve JSON serialization compatibility with the existing dict[str, Any] storage pattern
- NOT_APPLICABLE detection via sector_filter field in check config -- best-effort first pass; most checks will be EVALUATED or DATA_UNAVAILABLE
- _determine_data_status is called after evaluate_check rather than inside it, keeping the evaluator functions unchanged

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DataStatus and pipeline audit are ready for Plan 04 (Coverage Gaps section) to consume
- Plan 02 (Peril Mapping) can proceed independently -- no dependency on data_status
- Pipeline audit can be run against real data to quantify check coverage gaps

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
