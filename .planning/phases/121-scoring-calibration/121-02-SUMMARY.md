---
phase: 121-scoring-calibration
plan: 02
subsystem: scoring
tags: [calibration-baseline, multi-ticker, tier-distribution, crf-ceilings]

# Dependency graph
requires:
  - phase: 121-scoring-calibration
    provides: Size-conditioned CRF ceilings, weighted compounding, distress graduation
provides:
  - Multi-ticker calibration baseline script (scripts/calibration_baseline.py)
  - Before/after score snapshots for 5 tickers (output/calibration_baseline.json)
  - Integration tests encoding approved tier expectations
affects: [future scoring tuning, render sections, tier boundary adjustments]

# Tech tracking
tech-stack:
  added: []
  patterns: [calibration baseline comparison pattern, before/after scoring snapshot]

key-files:
  created:
    - scripts/calibration_baseline.py
  modified:
    - tests/stages/score/test_crf_calibration.py

key-decisions:
  - "Calibration approved as starting point -- further tuning expected in future work"
  - "No tier boundary adjustments needed at this stage -- 4 distinct tiers across 5 tickers is sufficient"
  - "Approved tier assignments: AAPL=WRITE, ANGI=WALK, RPM=WRITE, HNGE=WATCH, EXPO=WIN"

patterns-established:
  - "Calibration baseline pattern: load state.json, re-score with old vs new logic, compare tiers"

requirements-completed: [SCORE-02, SCORE-03, SCORE-04]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 121 Plan 02: Calibration Baseline Summary

**5-ticker before/after baseline: WALK compression eliminated (3 tiers before -> 4 after), AAPL WRITE vs ANGI WALK (2 tiers apart), approved as starting point**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T19:45:46Z
- **Completed:** 2026-03-21T19:52:00Z
- **Tasks:** 3 (Task 2 was human-verify checkpoint)
- **Files modified:** 2

## Accomplishments
- Calibration baseline script loads state.json from prior pipeline runs and re-scores with old (flat ceiling) vs new (size-conditioned + weighted compounding) logic
- 5 tickers successfully compared: AAPL, ANGI, RPM, HNGE, EXPO (V/Visa has no pipeline output)
- Before distribution was compressed: WALK=3, WATCH=1, WIN=1 (3 tiers)
- After distribution spread out: WALK=1, WATCH=1, WRITE=2, WIN=1 (4 tiers)
- AAPL jumped from WALK(30) to WRITE(70) via mega-cap CRF-1 ceiling
- ANGI dropped from WALK(25) to WALK(19.6) via micro-cap CRF-8 ceiling + compounding
- User approved calibration results: "not bad.. this will need a lot more work, but fine for now"
- 3 integration tests encode approved tier expectations for regression protection

## Task Commits

Each task was committed atomically:

1. **Task 1: Build calibration baseline script** - `19ed378f` (feat)
2. **Task 2: Human-verify checkpoint** - approved by user, no commit needed
3. **Task 3: Add integration tests** - `d3ad4ca3` (test)

## Files Created/Modified
- `scripts/calibration_baseline.py` - Multi-ticker calibration comparison: loads state.json, computes before/after scores, outputs table + JSON
- `tests/stages/score/test_crf_calibration.py` - Added 3 integration tests: AAPL/ANGI differentiation, tier distribution, baseline JSON structure
- `output/calibration_baseline.json` - Before/after snapshots for 5 tickers (generated artifact, not committed)

## Decisions Made
- Calibration approved as starting point -- further tuning expected in future work
- No tier boundary adjustments needed: 4 distinct tiers is sufficient for SCORE-04 (requires 3+)
- Approved tier assignments match new ceiling logic: AAPL=WRITE, ANGI=WALK, RPM=WRITE, HNGE=WATCH, EXPO=WIN

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Visa (V) has no pipeline output state.json -- skipped in calibration, 5/6 tickers sufficient
- EXPO ticker listed as "EXPONENT" in output directory naming, handled by prefix matching in script

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Scoring calibration complete (SCORE-01 through SCORE-04 all satisfied)
- Calibration baseline available for future comparison after any scoring changes
- Further tuning expected as more tickers are run and domain expert feedback accumulated

---
*Phase: 121-scoring-calibration*
*Completed: 2026-03-21*
