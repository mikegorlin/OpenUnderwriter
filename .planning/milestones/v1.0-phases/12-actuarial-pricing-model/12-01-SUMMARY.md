---
phase: 12-actuarial-pricing-model
plan: 01
subsystem: scoring
tags: [actuarial, expected-loss, frequency-severity, pydantic, config]

# Dependency graph
requires:
  - phase: 06-scoring-engine
    provides: "ScoringResult, SeverityScenarios, severity_model.py"
  - phase: 07-benchmark-executive-summary
    provides: "InherentRiskBaseline with filing probability"
provides:
  - "actuarial.json config with all pricing model parameters"
  - "ActuarialPricing + ExpectedLoss + 4 supporting Pydantic models"
  - "compute_expected_loss() pure function for frequency-severity computation"
affects: [12-02-layer-pricing, 12-03-pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Config-driven actuarial parameters (no hardcoding)", "Pure function actuarial computation"]

key-files:
  created:
    - "src/do_uw/config/actuarial.json"
    - "src/do_uw/stages/score/actuarial_model.py"
    - "tests/test_actuarial_model.py"
  modified:
    - "src/do_uw/models/scoring_output.py"
    - "src/do_uw/models/scoring.py"

key-decisions:
  - "All actuarial parameters in actuarial.json, none hardcoded"
  - "Pure function compute_expected_loss for testability"
  - "Defense cost lookup by case type with fallback to default"

patterns-established:
  - "Actuarial config pattern: all pricing parameters in JSON, loaded at call site"
  - "Expected loss = probability * severity + defense costs at each percentile"

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 12 Plan 01: Actuarial Expected Loss Computation Summary

**Frequency-severity expected loss model with config-driven defense costs, 4-percentile scenario losses, and 6 new Pydantic pricing models**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T05:35:39Z
- **Completed:** 2026-02-10T05:39:42Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created actuarial.json config with defense_cost_factors, ilf_parameters, loss_ratio_targets, expense_loads, credibility, default_tower, and model_label
- Added 6 Pydantic models (ScenarioLoss, ExpectedLoss, LayerSpec, LayerPricing, CalibratedPricing, ActuarialPricing) to scoring_output.py
- Implemented compute_expected_loss() pure function: prob * severity + defense costs with 4-percentile scenario losses
- Added actuarial_pricing field to ScoringResult with full re-exports
- 8 TDD tests covering basic computation, edge cases (no data, empty, zero probability), defense cost lookup, and complex case types

## Task Commits

Each task was committed atomically:

1. **Task 1: Create actuarial.json config and ActuarialPricing Pydantic models** - `4af2a31` (feat)
2. **Task 2 RED: Failing tests for compute_expected_loss** - `5721621` (test)
3. **Task 2 GREEN: Implement compute_expected_loss** - `c3a93dd` (feat)

## Files Created/Modified
- `src/do_uw/config/actuarial.json` - All actuarial model parameters (defense costs, ILF, loss ratios, tower structure)
- `src/do_uw/stages/score/actuarial_model.py` - compute_expected_loss() pure function (223L)
- `tests/test_actuarial_model.py` - 8 TDD tests for expected loss computation (235L)
- `src/do_uw/models/scoring_output.py` - 6 new Pydantic models (ScenarioLoss, ExpectedLoss, LayerSpec, LayerPricing, CalibratedPricing, ActuarialPricing) (473L)
- `src/do_uw/models/scoring.py` - actuarial_pricing field on ScoringResult + re-exports (364L)

## Decisions Made
- All actuarial parameters stored in actuarial.json config file (defense costs, ILF curves, loss ratio targets, expense loads, credibility, tower structure)
- compute_expected_loss is a pure function taking explicit inputs (no side effects, no state mutation) for maximum testability
- Defense cost lookup by case_type with fallback to 'default' key (0.20)
- Scenario losses computed at all 4 percentiles (25th/50th/75th/95th) using same probability and defense cost
- LayerSpec, LayerPricing, CalibratedPricing models added now for Plan 02 (layer pricing) consumption

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness
- compute_expected_loss() ready for Plan 02 (layer pricing) to build upon
- ActuarialPricing model ready for Plan 03 (pipeline integration) to populate
- actuarial.json config has all parameters Plan 02 needs (ilf_parameters, loss_ratio_targets, expense_loads)
- 1666 tests passing, 0 lint/type errors, all files under 500 lines

---
*Phase: 12-actuarial-pricing-model*
*Completed: 2026-02-10*
