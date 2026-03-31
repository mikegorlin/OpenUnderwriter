---
phase: 23-end-to-end-output-quality
plan: 01
subsystem: resolve
tags: [sic-mapping, sector-classification, COMM, sectors.json]

# Dependency graph
requires:
  - phase: 02-company-resolution-data-acquisition
    provides: sec_identity.py SIC-to-sector mapping
provides:
  - COMM sector classification for entertainment/media SIC codes (78xx, 79xx)
  - COMM baselines in all sectors.json sector-specific tables
  - Regression tests covering SIC 70-89 services range
affects: [scoring, benchmarking, rendering, ground-truth-validation]

# Tech tracking
tech-stack:
  added: []
  patterns: [finer-grained SIC range splitting for sector accuracy]

key-files:
  created: []
  modified:
    - src/do_uw/stages/resolve/sec_identity.py
    - src/do_uw/brain/sectors.json
    - tests/test_resolve.py

key-decisions:
  - "Split SIC (74,79)->INDU into (74,76)->INDU and (78,79)->COMM for entertainment/media granularity"
  - "COMM sector baselines modeled between TECH and CONS (moderate short interest, volatility, leverage)"

patterns-established:
  - "SIC range splitting: when coarse ranges conflate distinct industries, split into finer sub-ranges"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 23 Plan 01: SIC-to-Sector Mapping Refinement Summary

**Split SIC 78xx/79xx from INDU to COMM so NFLX and DIS classify as Communication Services with sector-specific baselines**

## Performance

- **Duration:** 2m 38s
- **Started:** 2026-02-11T22:34:19Z
- **Completed:** 2026-02-11T22:36:57Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- NFLX (SIC 7841) and DIS (SIC 7990) now correctly classify as COMM instead of INDU
- COMM sector baselines added to all 7 relevant tables in sectors.json (short_interest, volatility_90d, leverage_debt_ebitda, guidance_miss_sector_adjustments, insider_trading_sector_context, dismissal_rates, claim_base_rates)
- 17 parametrized regression tests covering SIC 70-89 services range with zero regressions in 38 total resolve tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Refine SIC-to-sector mapping and add COMM sector** - `10fe39c` (feat)
2. **Task 2: Add sector classification regression tests** - `1c0a13e` (test)

## Files Created/Modified
- `src/do_uw/stages/resolve/sec_identity.py` - Split (74,79)->INDU into (74,76)->INDU and (78,79)->COMM in _SIC_SECTOR_MAP
- `src/do_uw/brain/sectors.json` - Added COMM entries to 7 sector-specific baseline tables
- `tests/test_resolve.py` - Added test_sic_to_sector_refined_services with 17 parametrized cases

## Decisions Made
- Split SIC range (74,79) at 76/78 boundary because SIC 77xx is an unused range in the standard SIC system, making a clean split
- COMM baselines modeled as moderate: between TECH (high growth/volatility) and CONS (consumer), reflecting entertainment sector characteristics
- COMM insider trading context mirrors TECH (insiders rarely buy in media/entertainment)
- COMM dismissal rate set at 52.5% (between TECH 57.5% and FINS 52.5%)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Sector classification fix cascades to scoring, benchmarking, and display for NFLX and DIS
- Downstream plans in Phase 23 can now reference COMM sector baselines
- Ground truth validation tests for DIS may need updating (previously expected INDU, now should expect COMM per 21-06 decision note)

## Self-Check: PASSED

- All 3 modified files exist on disk
- Both task commits (10fe39c, 1c0a13e) found in git log
- SUMMARY.md created at expected path

---
*Phase: 23-end-to-end-output-quality*
*Completed: 2026-02-11*
