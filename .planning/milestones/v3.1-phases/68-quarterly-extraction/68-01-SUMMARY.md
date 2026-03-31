---
phase: 68-quarterly-extraction
plan: 01
subsystem: extraction
tags: [xbrl, quarterly, company-facts, pydantic, ytd-disambiguation]

# Dependency graph
requires:
  - phase: 67-xbrl-foundation
    provides: "xbrl_mapping.py with resolve_concept(), load_xbrl_mapping(), normalize_sign()"
provides:
  - "QuarterlyPeriod and QuarterlyStatements Pydantic models on financials.py"
  - "extract_quarterly_xbrl() function in xbrl_quarterly.py"
  - "select_standalone_quarters() frame-based YTD filter"
  - "ExtractedFinancials.quarterly_xbrl field"
affects: [68-02 (trend computation), 68-03 (reconciler), 69 (forensic analysis), 70 (signal integration)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frame-based quarterly filtering: CY####Q# for duration, CY####Q#I for instant"
    - "Fiscal/calendar dual-labeling on QuarterlyPeriod"
    - "Duration fallback: 70-105 day span filter when frame absent"

key-files:
  created:
    - src/do_uw/stages/extract/xbrl_quarterly.py
    - tests/test_xbrl_quarterly.py
  modified:
    - src/do_uw/models/financials.py

key-decisions:
  - "Frame regex as primary YTD discriminator, duration fallback as secondary"
  - "Fiscal/calendar dual labels stored on every QuarterlyPeriod"
  - "Derived concepts skipped in quarterly extraction (annual-only for now)"

patterns-established:
  - "QUARTERLY_FRAME_RE (CY####Q#) and INSTANT_FRAME_RE (CY####Q#I) for quarterly selection"
  - "Dedup by frame value preferring most recently filed entry"
  - "XBRL:10-Q:{end}:CIK{cik}:accn:{accn} provenance format"

requirements-completed: [QTRLY-01, QTRLY-02, QTRLY-03, QTRLY-08]

# Metrics
duration: 5min
completed: 2026-03-06
---

# Phase 68 Plan 01: Quarterly Extraction Summary

**Frame-based XBRL quarterly extraction with fiscal/calendar dual-labeling and 22 passing tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-06T14:08:39Z
- **Completed:** 2026-03-06T14:14:00Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 3

## Accomplishments
- QuarterlyPeriod and QuarterlyStatements models with fiscal/calendar dual labels
- extract_quarterly_xbrl() using frame-based YTD disambiguation (no subtraction math)
- select_standalone_quarters() with frame regex primary + duration fallback
- Fiscal alignment verified for non-calendar FY companies (AAPL Sep FY)
- All SourcedValues carry XBRL:10-Q provenance at HIGH confidence

## Task Commits

Each task was committed atomically:

1. **Task 1: QuarterlyPeriod + QuarterlyStatements models (RED)** - `cbdff80` (feat)
2. **Task 1: Failing tests for extraction logic (RED)** - `ced064a` (test)
3. **Task 2: xbrl_quarterly.py implementation (GREEN)** - `ccbaebf` (feat)

_Note: TDD tasks have separate test and implementation commits_

## Files Created/Modified
- `src/do_uw/models/financials.py` - Added QuarterlyPeriod, QuarterlyStatements, quarterly_xbrl field on ExtractedFinancials
- `src/do_uw/stages/extract/xbrl_quarterly.py` - New module: frame-based quarterly XBRL extraction (~280 lines)
- `tests/test_xbrl_quarterly.py` - 22 tests covering models, frame filtering, fiscal alignment, provenance, edge cases

## Decisions Made
- Frame regex as primary YTD discriminator eliminates subtraction math for ~95% of entries
- Fiscal/calendar dual labels stored on every QuarterlyPeriod for dual-view display
- Derived concepts skipped in quarterly extraction (they depend on annual primitives)
- Dedup by frame value prefers most recently filed (handles amendments)
- Duration fallback uses 70-105 day span filter (not fp field alone, which appears on both YTD and standalone)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in tests/knowledge/test_enriched_roundtrip.py (unrelated to changes, SignalDefinition validation error)
- Pyright unnecessary isinstance warning fixed inline

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- QuarterlyStatements model ready for trend computation (68-02)
- extract_quarterly_xbrl() ready for pipeline integration
- Provenance format established for downstream consumers

---
*Phase: 68-quarterly-extraction*
*Completed: 2026-03-06*
