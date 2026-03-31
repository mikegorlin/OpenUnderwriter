---
phase: 90-drop-enhancements
plan: 01
subsystem: extract
tags: [time-decay, return-decomposition, corrective-disclosure, stock-drops, 8-K]

# Dependency graph
requires:
  - phase: 88-data-foundation
    provides: "compute_return_decomposition, 2Y daily price data"
  - phase: 89-statistical-analysis
    provides: "abnormal return fields on StockDropEvent"
provides:
  - "Time-decay weighting (compute_decay_weight, apply_decay_weights)"
  - "Per-drop return decomposition (decompose_drop, decompose_drops)"
  - "Corrective disclosure reverse 8-K lookup (enrich_drops_with_reverse_lookup)"
  - "9 new fields on StockDropEvent model"
affects: [90-02-pipeline-wiring, scoring, rendering]

# Tech tracking
tech-stack:
  added: []
  patterns: [exponential-decay-half-life, return-attribution-reuse, reverse-filing-lookup]

key-files:
  created:
    - src/do_uw/stages/extract/stock_drop_decay.py
    - src/do_uw/stages/extract/stock_drop_decomposition.py
    - tests/stages/extract/test_stock_drop_decay.py
    - tests/stages/extract/test_stock_drop_decomposition.py
    - tests/stages/extract/test_stock_drop_enrichment_reverse.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/stages/extract/stock_drop_enrichment.py

key-decisions:
  - "180-day half-life for decay weighting (balances recent relevance with historical context)"
  - "Reuse compute_return_decomposition from chart_computations for per-drop attribution"
  - "D&O-relevant 8-K items limited to 2.02, 4.02, 5.02, 2.06 (earnings, restatement, mgmt departure, impairment)"
  - "Market-driven threshold at >50% of absolute total drop"

patterns-established:
  - "2-point price window for per-drop decomposition (start/end only, not full series)"
  - "Reverse filing lookup: search for filings AFTER events, not just before"

requirements-completed: [STOCK-06, STOCK-08, STOCK-09]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 90 Plan 01: Drop Enhancements Computation Modules Summary

**Exponential time-decay weighting, per-drop 3-component return decomposition, and corrective disclosure reverse 8-K/web lookup for stock drop events**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T13:21:12Z
- **Completed:** 2026-03-09T13:26:28Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added 9 new fields to StockDropEvent with backward-compatible defaults (decay, decomposition, corrective disclosure)
- Created stock_drop_decay.py with 180-day half-life exponential decay and severity ranking
- Created stock_drop_decomposition.py reusing compute_return_decomposition for market/sector/company attribution
- Added corrective disclosure reverse lookup to stock_drop_enrichment.py with 8-K and web fallback
- 39 new tests covering all computation modules

## Task Commits

Each task was committed atomically:

1. **Task 1: Add model fields + create decay and decomposition modules with tests** - `1cac1ae` (feat)
2. **Task 2: Add corrective disclosure reverse lookup with tests** - `9f1bb2b` (feat)

## Files Created/Modified
- `src/do_uw/models/market_events.py` - 9 new Phase 90 fields on StockDropEvent
- `src/do_uw/stages/extract/stock_drop_decay.py` - Time-decay weighting (180-day half-life)
- `src/do_uw/stages/extract/stock_drop_decomposition.py` - Per-drop return decomposition
- `src/do_uw/stages/extract/stock_drop_enrichment.py` - Corrective disclosure reverse lookup
- `tests/stages/extract/test_stock_drop_decay.py` - 15 decay tests
- `tests/stages/extract/test_stock_drop_decomposition.py` - 9 decomposition tests
- `tests/stages/extract/test_stock_drop_enrichment_reverse.py` - 15 reverse lookup tests

## Decisions Made
- 180-day half-life chosen to balance recent relevance (litigation filing window) with historical context
- Reused existing compute_return_decomposition rather than duplicating decomposition logic
- D&O-relevant 8-K items restricted to 2.02 (earnings), 4.02 (restatement), 5.02 (mgmt departure), 2.06 (impairment)
- Market-driven flag at >50% market contribution threshold
- Reverse lookup window 1-14 days (excludes same-day to avoid double-counting existing enrichment)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SourcedValue requires as_of field**
- **Found during:** Task 1 (test execution)
- **Issue:** SourcedValue constructor requires mandatory `as_of` datetime parameter, not documented in plan interfaces
- **Fix:** Added `as_of=datetime(2026, 3, 9, tzinfo=UTC)` to all test SourcedValue constructions
- **Files modified:** test_stock_drop_decay.py, test_stock_drop_decomposition.py, test_stock_drop_enrichment_reverse.py
- **Verification:** All 39 tests pass
- **Committed in:** 1cac1ae, 9f1bb2b

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor test fixture fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three computation modules are standalone with tests
- Plan 02 can wire these into the extraction pipeline, F2 scoring, and HTML rendering
- Existing enrichment tests (141 total in extract/) continue to pass

---
*Phase: 90-drop-enhancements*
*Completed: 2026-03-09*
