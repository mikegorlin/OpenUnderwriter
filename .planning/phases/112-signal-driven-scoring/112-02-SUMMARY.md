---
phase: 112-signal-driven-scoring
plan: 02
subsystem: scoring
tags: [signal-attribution, factor-weights, calibration, shadow-comparison, context-builder]

# Dependency graph
requires:
  - phase: 112-signal-driven-scoring (plan 01)
    provides: FactorScore with signal_contributions, signal_coverage, scoring_method fields
provides:
  - Signal attribution data in scoring context builder (top-3 signals, confidence bar, factor weights)
  - Extended CalibrationRow with per-factor signal vs rule score comparison
  - Factor-level comparison section in calibration report HTML
affects: [114-worksheet-restructure, rendering, calibration-runs]

# Tech tracking
tech-stack:
  added: []
  patterns: [signal-attribution-context-enrichment, factor-level-calibration-comparison]

key-files:
  created:
    - tests/stages/score/test_factor_score_contributions.py
    - tests/stages/score/test_shadow_signal_calibration.py
  modified:
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/score/shadow_calibration.py
    - src/do_uw/stages/score/_calibration_report.py

key-decisions:
  - "Signal attribution only added to signal_driven factors; rule_based factors excluded (clean separation)"
  - "Factor weight percentage derived from max_points (each factor's max_points IS its weight in the 100-point budget)"
  - "Calibration factor comparison built into existing HTML report (not separate file)"

patterns-established:
  - "Signal attribution dict on factor context: top_3_signals, confidence_pct, evaluated_count, full_signal_count"
  - "Factor-level delta color coding: green <2pts, yellow 2-5pts, red >5pts"

requirements-completed: [FSCORE-03, FSCORE-04]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 112 Plan 02: Factor Contribution Display and Shadow Calibration Summary

**Signal attribution context with top-3 signals per factor, confidence bars, and factor-level calibration comparison table in shadow report**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T00:39:18Z
- **Completed:** 2026-03-17T00:45:40Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Scoring context builder enriched with signal_attribution per factor: top-3 signals sorted by contribution, confidence bar (coverage percentage), evaluated/total counts
- Factor weight percentage (max_points%) added to every factor in scoring context
- CalibrationRow extended with per-factor signal-driven vs rule-based score dicts, signal composite, average coverage, and scoring method tracking
- CalibrationMetrics extended with mean factor delta, average signal coverage, signal/rule factor counts
- Calibration report HTML includes new Factor-Level Comparison section with per-ticker per-factor breakdown
- Signal Coverage and Factor Delta metric badges added to calibration report header
- 26 new tests (10 + 16) covering all new functionality

## Task Commits

Each task was committed atomically:

1. **Task 1: Factor contribution display in scoring context builder** - `69f6a5b` (feat) - TDD RED/GREEN
2. **Task 2: Shadow calibration signal-driven vs rule-based comparison** - `0f9ece9` (feat)

## Files Created/Modified
- `tests/stages/score/test_factor_score_contributions.py` - 10 tests for signal attribution, factor weights, backward compat
- `tests/stages/score/test_shadow_signal_calibration.py` - 16 tests for CalibrationRow/Metrics extensions and report generation
- `src/do_uw/stages/render/context_builders/scoring.py` - Signal attribution dict and factor_weight_pct on factor context
- `src/do_uw/stages/score/shadow_calibration.py` - CalibrationRow/Metrics signal-driven fields, calibrate_from_pipeline capture
- `src/do_uw/stages/score/_calibration_report.py` - Factor comparison section, signal coverage badge, delta color coding

## Decisions Made
- Signal attribution only added to signal_driven factors -- rule_based factors have no signal_attribution key (clean separation, no noise)
- Factor weight percentage is max_points% (the 100-point budget makes max_points the natural weight)
- Factor-level comparison built into existing calibration report HTML rather than a separate file
- Synthetic stub rows default to empty signal data (new fields all zero/empty by default)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in `tests/render/test_peril_scoring_html.py::TestPerilScoringInExtractScoring::test_peril_scoring_key_present_with_brain_data` -- confirmed present before this plan's changes. Out of scope.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Signal attribution data is ready for Phase 114 (Worksheet Restructure) to render in the HTML template
- Shadow calibration can now capture signal vs rule comparisons on real pipeline runs
- Calibration storage to .cache/calibration/ is documented but actual JSON writing deferred to real pipeline runs (the infrastructure is in place via CalibrationRow.model_dump())

---
*Phase: 112-signal-driven-scoring*
*Completed: 2026-03-16*
