---
phase: 112-signal-driven-scoring
plan: 01
subsystem: scoring
tags: [signal-aggregation, factor-scoring, traceability, pydantic, yaml]

# Dependency graph
requires:
  - phase: 111-signal-wiring-closure
    provides: Signal evaluation results in state.analysis.signal_results
provides:
  - Signal-to-factor aggregation engine (factor_data_signals.py)
  - Extended FactorScore with signal attribution fields
  - ScoringSpec/ScoringContribution on BrainSignalEntry schema
  - Signal-driven scoring primary path with rule-based fallback
affects: [112-02, rendering, calibration]

# Tech tracking
tech-stack:
  added: []
  patterns: [signal-driven-scoring-with-fallback, coverage-threshold-gating, weighted-severity-normalization]

key-files:
  created:
    - src/do_uw/stages/score/factor_data_signals.py
    - tests/stages/score/test_factor_data_signals.py
    - tests/stages/score/test_signal_scoring_influence.py
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/brain/brain_signal_schema.py
    - src/do_uw/stages/score/factor_scoring.py
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/score/__init__.py

key-decisions:
  - "Signal-driven path replaces rule-based BASE score only; modifiers (F2 insider/mktcap/decay, F9 dual_class) apply on top of both paths"
  - "Coverage threshold 50% gates signal path usage; below threshold falls back to rule-based"
  - "Inference signals (conjunction/absence/contextual) included at 0.5 weight per research recommendation"
  - "DEFERRED and SKIPPED signals excluded from coverage denominator entirely"

patterns-established:
  - "Signal-driven scoring with fallback: try signal path first, gate on coverage, fall back to rule-based"
  - "Weighted severity normalization: sum(severity_i * weight_i) / total_weight * max_points"

requirements-completed: [FSCORE-01, FSCORE-02]

# Metrics
duration: 22min
completed: 2026-03-16
---

# Phase 112 Plan 01: Signal-Driven Scoring Summary

**Signal-to-factor aggregation engine with weighted severity normalization, 50% coverage threshold, and full backward compatibility across 1803 tests**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-17T00:13:40Z
- **Completed:** 2026-03-17T00:35:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created factor_data_signals.py aggregation engine: weighted severity normalization, factor canonical mapping, inference signal half-weighting
- Extended FactorScore with signal_contributions, signal_coverage, scoring_method fields for full traceability
- Added ScoringSpec/ScoringContribution to BrainSignalEntry for per-signal and per-factor weight overrides
- Wired signal_results through ScoreStage -> score_all_factors -> _score_factor with seamless fallback
- 20 new tests (unit + integration) proving FSCORE-02 score differentiation
- Zero regressions across 1803 score/render/knowledge tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Schema extensions + signal aggregation engine** - `d35f849` (test) + `a057346` (feat) - TDD RED then GREEN
2. **Task 2: Wire signal path into scoring pipeline** - `5d37b4c` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/factor_data_signals.py` - Signal-to-factor aggregation engine (195 lines)
- `src/do_uw/models/scoring.py` - Extended FactorScore with signal attribution fields
- `src/do_uw/brain/brain_signal_schema.py` - ScoringSpec/ScoringContribution models + optional scoring field on BrainSignalEntry
- `src/do_uw/stages/score/factor_scoring.py` - Signal-driven primary path in _score_factor with fallback
- `src/do_uw/stages/score/factor_data.py` - API compatibility (signal_results parameter)
- `src/do_uw/stages/score/__init__.py` - ScoreStage passes signal_results to score_all_factors
- `tests/stages/score/test_factor_data_signals.py` - 18 unit tests for aggregation
- `tests/stages/score/test_signal_scoring_influence.py` - 2 integration tests for FSCORE-02

## Decisions Made
- Signal-driven path replaces rule-based BASE score only -- modifiers (F2 insider amplifier, market cap multiplier, drop contribution, F9 dual_class override) apply on top of signal-driven base
- Coverage threshold set at 50% -- below this, fall back to rule-based to avoid scoring on insufficient signal data
- Inference signals (conjunction/absence/contextual) included at 0.5 weight per Phase 112 research recommendation
- DEFERRED and SKIPPED signals excluded from coverage denominator entirely (they don't penalize coverage)
- ScoringSpec is optional on BrainSignalEntry -- no YAML changes required for existing signals

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Signal-driven scoring path is functional and tested
- Plan 112-02 can now add signal-based factor data enrichment and calibration
- Real pipeline runs will show signal_driven vs rule_based scoring_method per factor based on actual signal coverage

---
*Phase: 112-signal-driven-scoring*
*Completed: 2026-03-16*
