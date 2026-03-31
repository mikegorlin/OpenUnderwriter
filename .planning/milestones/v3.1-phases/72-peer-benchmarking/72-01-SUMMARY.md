---
phase: 72-peer-benchmarking
plan: 01
subsystem: acquire
tags: [sec-edgar, frames-api, xbrl, peer-benchmarking, sic-mapping]

requires:
  - phase: 67-xbrl-foundation
    provides: XBRL concept mapping and extraction infrastructure
provides:
  - SEC Frames API acquisition client (acquire_frames)
  - CIK-to-SIC incremental mapping (acquire_sic_mapping)
  - Cross-filer XBRL data for 10 benchmarking concepts
  - Frames data integration in ACQUIRE orchestrator
affects: [72-peer-benchmarking, benchmark-stage]

tech-stack:
  added: []
  patterns: [system-level-caching, incremental-batch-fetch, non-blocking-supplemental]

key-files:
  created:
    - src/do_uw/stages/acquire/clients/sec_client_frames.py
    - tests/test_sec_client_frames.py
  modified:
    - src/do_uw/stages/acquire/orchestrator.py

key-decisions:
  - "FramesMetricDef dataclass with frozen=True for immutable metric registry"
  - "10 XBRL tags: 8 direct metrics + 2 component-only for derived ratios (Plan 02)"
  - "SIC batch limit 500 CIKs per run with incremental caching (90-day TTL)"
  - "Frames data stored on acquired.filings['frames'] alongside existing filing data"

patterns-established:
  - "System-level Frames cache: 180d completed periods, 1d current period"
  - "Incremental SIC mapping: cache-check-first, batch-fetch uncached, 500-CIK limit"
  - "Non-blocking orchestrator phase: try/except wraps entire Frames step"

requirements-completed: [PEER-01, PEER-03]

duration: 22min
completed: 2026-03-07
---

# Phase 72 Plan 01: SEC Frames API Acquisition Summary

**SEC Frames API client fetching cross-filer XBRL data for 10 benchmarking concepts with incremental CIK-to-SIC mapping and system-level caching**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-07T01:27:02Z
- **Completed:** 2026-03-07T01:49:06Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created sec_client_frames.py with acquire_frames() and acquire_sic_mapping() functions
- FRAMES_METRICS registry covers 10 XBRL tags (Revenues, NetIncomeLoss, Assets, StockholdersEquity, Liabilities, OperatingIncomeLoss, NetCashProvidedByOperatingActivities, ResearchAndDevelopmentExpense, AssetsCurrent, LiabilitiesCurrent)
- Integrated Frames acquisition into orchestrator as non-blocking Phase B step
- 22 unit tests with full mock coverage (no real API calls)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for Frames client** - `31ad45f` (test)
2. **Task 1 (GREEN): Implement Frames client** - `49fdd4d` (feat)
3. **Task 2: Wire into orchestrator** - `c99be46` (feat)

_TDD pattern: Task 1 has RED + GREEN commits_

## Files Created/Modified
- `src/do_uw/stages/acquire/clients/sec_client_frames.py` - Frames API client with metric registry, acquire_frames(), acquire_sic_mapping()
- `tests/test_sec_client_frames.py` - 22 unit tests covering period strings, registry, cache behavior, error handling
- `src/do_uw/stages/acquire/orchestrator.py` - Added _acquire_frames_data() and _extract_10k_year() helper

## Decisions Made
- Used FramesMetricDef frozen dataclass for immutable metric definitions (consistent with project Pydantic patterns)
- Lazy import of sec_client_frames inside orchestrator method (avoids import-time overhead when Frames not needed)
- Store only data list from Frames response (not full response) per research pitfall 3 (memory optimization)
- _extract_10k_year checks both 10-K and 20-F for FPI company support

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failures in tests/knowledge/ (test_enriched_roundtrip.py, test_enrichment.py, test_migrate.py) and tests/render/test_peril_scoring_html.py -- all unrelated to this plan's changes, verified by running against pre-change codebase
- orchestrator.py was already at 677 lines pre-change (over 500-line limit); our addition brings it to 793 -- logged as pre-existing violation, not in scope for this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Frames data available at acquired.filings["frames"] for Plan 02 to consume
- SIC mapping available at acquired.filings["sic_mapping"] for sector filtering
- Plan 02 will build percentile computation and signal wiring on top of this data

---
*Phase: 72-peer-benchmarking*
*Completed: 2026-03-07*
