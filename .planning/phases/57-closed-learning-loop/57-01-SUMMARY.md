---
phase: 57-closed-learning-loop
plan: 01
subsystem: brain
tags: [statistics, calibration, drift-detection, duckdb, pydantic, cli, rich]

# Dependency graph
requires:
  - phase: 54-signal-contract-v2
    provides: V2 signal schema with evaluation.thresholds
  - phase: 53-data-store-simplification
    provides: YAML-based signal definitions via BrainLoader
provides:
  - Statistical threshold drift detection engine (brain_calibration.py)
  - Fire rate anomaly alerting (>80% / <2%)
  - THRESHOLD_CALIBRATION proposal generation to brain_proposals
  - brain audit --calibrate CLI flag with Rich table output
affects: [57-02, 57-03, brain-audit, feedback-approve]

# Tech tracking
tech-stack:
  added: []
  patterns: [statistical-drift-detection, percentile-based-proposals, defensive-varchar-parsing]

key-files:
  created:
    - src/do_uw/brain/brain_calibration.py
    - tests/brain/test_brain_calibration.py
  modified:
    - src/do_uw/cli_brain_health.py

key-decisions:
  - "Used p90 of observed distribution as proposed threshold for drift-detected signals (percentile-based, not mean-based)"
  - "Confidence levels: LOW (N=5-9), MEDIUM (N=10-24), HIGH (N>=25) -- more conservative than effectiveness module"
  - "Fire rate alerts use >80% / <2% thresholds (per LEARN-03 requirement, not 100%/0% from effectiveness module)"
  - "Calibration section runs after audit section in same DuckDB connection (restructured conn lifecycle with try/finally)"

patterns-established:
  - "Defensive VARCHAR parsing: try float(), skip non-numeric, never crash on mixed-type brain_signal_runs.value"
  - "V1/V2 threshold extraction: regex for V1 strings, structured evaluation.thresholds for V2 signals"
  - "Proposal insertion pattern: source_type=CALIBRATION, statistical evidence in backtest_results JSON"

requirements-completed: [LEARN-01, LEARN-03]

# Metrics
duration: 13min
completed: 2026-03-02
---

# Phase 57 Plan 01: Calibration Engine Summary

**Statistical threshold calibration engine with 2-sigma drift detection, fire rate alerting (>80%/<2%), and THRESHOLD_CALIBRATION proposal generation wired into brain audit --calibrate CLI**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-02T14:41:34Z
- **Completed:** 2026-03-02T14:54:38Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- brain_calibration.py (~330 lines) with DriftReport, FireRateAlert, CalibrationReport Pydantic models and full calibration pipeline
- 16 TDD tests covering drift detection, value parsing, fire rate alerts, proposal generation, confidence levels, and report structure
- brain audit --calibrate CLI flag showing Rich tables for drift analysis, fire rate alerts, and calibration summary

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain_calibration.py with Pydantic models and calibration engine** - `2fe3357` (test: failing tests) -> `a3a307d` (feat: implementation)
2. **Task 2: Wire calibration into brain audit CLI with --calibrate flag** - `78551a0` (feat: CLI wiring)

_TDD flow: RED tests committed first, then GREEN implementation._

## Files Created/Modified
- `src/do_uw/brain/brain_calibration.py` - Statistical threshold calibration engine: drift detection, fire rate alerting, proposal generation
- `tests/brain/test_brain_calibration.py` - 16 test cases with in-memory DuckDB fixtures
- `src/do_uw/cli_brain_health.py` - Added --calibrate flag and _display_calibration_report() helper

## Decisions Made
- Used p90 of observed distribution as proposed threshold value (percentile-based is more robust than mean-based for skewed distributions)
- Confidence levels are more conservative than effectiveness module: LOW at N=5-9 (effectiveness uses N<5), reflecting that calibration proposals need higher confidence
- Fire rate alerting uses >80% / <2% thresholds per LEARN-03 requirement (extends effectiveness module's 100%/0% extremes)
- CLI restructured with try/finally encompassing both audit and calibration sections to keep DuckDB connection open

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_no_drift test data**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Test values [4.8, 5.0, 5.2, 4.9, 5.1] had stdev ~0.158, making 5.5 threshold (0.5 away) actually >2 sigma from mean -- test was incorrectly designed
- **Fix:** Changed test values to [3.5, 4.5, 5.5, 6.0, 5.5] with wider spread so 5.5 is genuinely within 2 sigma of mean
- **Files modified:** tests/brain/test_brain_calibration.py
- **Verification:** Test passes correctly with both DRIFT_DETECTED and OK statuses
- **Committed in:** a3a307d (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix in test data)
**Impact on plan:** Test data correction only, no scope change.

## Issues Encountered
- Pre-existing test failure in test_brain_enrich.py (98 vs 99 MANAGEMENT_DISPLAY count) -- not caused by our changes, documented as out-of-scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- brain_calibration.py provides CalibrationReport that Plans 02 and 03 can extend
- THRESHOLD_CALIBRATION proposals flow through existing brain apply-proposal workflow
- Fire rate alerts available for lifecycle state machine (Plan 03) to use as transition criteria
- Existing brain_proposals table accepts new proposal types without schema changes

## Self-Check: PASSED

- [x] src/do_uw/brain/brain_calibration.py exists (330 lines)
- [x] tests/brain/test_brain_calibration.py exists (16 tests, all pass)
- [x] src/do_uw/cli_brain_health.py modified with --calibrate flag
- [x] Commit 2fe3357: test(57-01) failing tests
- [x] Commit a3a307d: feat(57-01) implementation
- [x] Commit 78551a0: feat(57-01) CLI wiring
- [x] 505 brain tests pass (1 pre-existing failure excluded)

---
*Phase: 57-closed-learning-loop*
*Completed: 2026-03-02*
