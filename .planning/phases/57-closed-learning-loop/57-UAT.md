---
status: testing
phase: 57-closed-learning-loop
source: [57-01-SUMMARY.md, 57-02-SUMMARY.md, 57-03-SUMMARY.md]
started: 2026-03-02T15:50:00Z
updated: 2026-03-02T15:50:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: brain audit --calibrate runs without error
expected: |
  Run `do-uw brain audit --calibrate`. Should display the standard structural audit (staleness, coverage, thresholds, orphans) PLUS a new "Threshold Drift Analysis" section showing any signals with drift detected, a "Fire Rate Alerts" section, and a calibration summary with counts (signals analyzed, numeric values found, drift detected, proposals generated).
awaiting: user response

## Tests

### 1. brain audit --calibrate runs without error
expected: Run `do-uw brain audit --calibrate`. Displays standard audit output plus calibration sections: "Threshold Drift Analysis" table, "Fire Rate Alerts" table, and calibration summary panel.
result: [pending]

### 2. brain audit --lifecycle runs without error
expected: Run `do-uw brain audit --lifecycle`. Displays standard audit output plus "Signal Lifecycle Analysis" showing current state distribution (how many ACTIVE, INCUBATING, etc.) and any proposed transitions.
result: [pending]

### 3. brain audit without new flags unchanged
expected: Run `do-uw brain audit` (no --calibrate or --lifecycle). Output should look identical to before Phase 57 — standard structural audit only, no calibration or lifecycle sections.
result: [pending]

### 4. Calibration proposals written to brain_proposals
expected: After running `brain audit --calibrate`, run `do-uw brain list-proposals` or check brain_proposals table. Any THRESHOLD_CALIBRATION proposals should appear with statistical evidence (observed mean, stdev, fire rate, proposed value).
result: [pending]

### 5. Co-occurrence analysis displayed under --calibrate
expected: Under `brain audit --calibrate`, after the drift analysis section, there should be a "Co-occurrence Analysis" section showing any correlated signal pairs (signal_a, signal_b, co_fire_rate, type) and any "Redundancy Clusters" if 3+ same-prefix signals co-fire >70%.
result: [pending]

### 6. Lifecycle proposals written to brain_proposals
expected: After running `brain audit --lifecycle`, any lifecycle transition proposals (e.g., INCUBATING->ACTIVE for signals with 5+ runs) should appear in brain_proposals with type LIFECYCLE_TRANSITION.
result: [pending]

### 7. Phase 57 test suite passes
expected: Run `python -m pytest tests/brain/test_brain_calibration.py tests/brain/test_brain_correlation.py tests/brain/test_brain_lifecycle_v2.py -v`. All 53 tests (16 calibration + 16 correlation + 21 lifecycle) pass.
result: [pending]

### 8. Full test suite has no new regressions
expected: Run `python -m pytest tests/ -x --timeout=120 -q`. Any failures should be pre-existing (documented in SUMMARY.md files), not caused by Phase 57 changes.
result: [pending]

## Summary

total: 8
passed: 0
issues: 0
pending: 8
skipped: 0

## Gaps

[none yet]
