---
phase: 108-severity-model
plan: 01
subsystem: scoring
tags: [severity, damages, settlement, regression, amplifiers, layer-erosion, pydantic, log-normal]

# Dependency graph
requires:
  - phase: 107-multiplicative-scoring
    provides: "ScoringLens Protocol, HAEScoringLens, ScoringLensResult with P composite"
  - phase: 106-model-research
    provides: "severity_model_design.yaml with formulas, coefficients, amplifier catalog"
  - phase: 104-signal-consumer
    provides: "SignalResultView for amplifier trigger evaluation"
provides:
  - "SeverityLens Protocol mirroring ScoringLens for pluggable severity engines"
  - "SeverityResult Pydantic model on state.scoring.severity_result"
  - "Damages estimation: market_cap * class_period_return * turnover_rate"
  - "12-feature settlement regression with published Cornerstone/NERA coefficients"
  - "11 severity amplifiers loaded from YAML with signal-driven firing"
  - "Log-normal layer erosion P(settlement > attachment) per allegation type"
  - "Dual ABC/Side A severity with DIC probability from distress signals"
  - "Legacy DDL severity wrapped as comparison lens"
  - "ScoreStage Step 15.5 integration with graceful degradation"
affects: [108-02, 109, 110, 111, 112, 113]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SeverityLens Protocol: pluggable severity interface mirroring ScoringLens"
    - "Log-normal CDF via math.erfc (no scipy dependency)"
    - "Amplifier multiplicative combination with 3.0 cap"
    - "TYPE_CHECKING + model_rebuild() for severity_result forward ref"
    - "Post-hoc adapter pattern for legacy severity lens"

key-files:
  created:
    - src/do_uw/models/severity.py
    - src/do_uw/stages/score/severity_lens.py
    - src/do_uw/stages/score/damages_estimation.py
    - src/do_uw/stages/score/settlement_regression.py
    - src/do_uw/stages/score/severity_amplifiers.py
    - src/do_uw/stages/score/layer_erosion.py
    - src/do_uw/stages/score/legacy_severity_lens.py
    - src/do_uw/stages/score/_severity_runner.py
    - tests/stages/score/test_severity_lens.py
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/score/__init__.py

key-decisions:
  - "Regression intercept calibrated to ~$5M median settlement for typical case features (Cornerstone baseline)"
  - "Amplifier combination is multiplicative with 3.0 cap (prevents runaway from multiple small amplifiers)"
  - "Log-normal CDF computed via math.erfc -- no scipy dependency needed"
  - "Allegation-type-specific sigma: restatement 1.0, guidance_miss 0.6, default 0.8"
  - "DIC probability additive from distress signals, capped at 0.8"
  - "Legacy severity wrapped as post-hoc adapter (same pattern as LegacyScoringLens)"
  - "Severity runner extracted to _severity_runner.py to keep __init__.py manageable"
  - "Extra YAML fields stripped before SeverityAmplifier validation (calibration_required not in schema)"

patterns-established:
  - "SeverityLens Protocol: evaluate(signal_results, company, attachment, product, hae_result) -> SeverityLensResult"
  - "Module-level YAML caches for design doc coefficients and amplifier catalog"
  - "Amplifier signal checking reuses case_characteristics._check_triggered pattern"
  - "Scenario grid: worst_actual/sector_median/catastrophic drop levels"

requirements-completed: [SEV-01, SEV-02, SEV-03]

# Metrics
duration: 22min
completed: 2026-03-16
---

# Phase 108 Plan 01: Severity Model Summary

**Damages estimation, settlement regression, 11 signal-driven amplifiers, log-normal layer erosion, and dual ABC/Side A severity models with legacy DDL comparison lens**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-16T00:49:58Z
- **Completed:** 2026-03-16T01:12:13Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Full severity computation engine: damages formula, 12-feature settlement regression with published Cornerstone/NERA coefficients, and 3-scenario grid (worst/sector/catastrophic)
- 11 severity amplifiers auto-fire from signal results with multiplicative combination capped at 3.0x
- Log-normal layer erosion with allegation-type-specific dispersion, Side A excess of ABC tower structure awareness, and DIC probability from financial distress signals
- SeverityResult on state.scoring.severity_result with dual primary/legacy lens results and P x S expected loss
- 35 severity-specific tests + 240 total score tests + 1558 model/stage tests, zero regressions

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: SeverityLens protocol + Pydantic models + damages + regression**
   - `1ee5312` (test: failing tests for severity models, damages, regression)
   - `6a62c16` (feat: severity models, damages estimation, settlement regression)

2. **Task 2: Severity amplifiers + layer erosion + legacy lens + integration**
   - `cf965ee` (test: failing tests for amplifiers, erosion, legacy lens, integration)
   - `72da079` (feat: severity amplifiers, layer erosion, legacy lens, pipeline integration)

## Files Created/Modified

- `src/do_uw/models/severity.py` - SeverityZone, ScenarioSeverity, AmplifierResult, LayerErosionResult, SeverityLensResult, SeverityResult Pydantic models (245 lines)
- `src/do_uw/stages/score/severity_lens.py` - SeverityLens Protocol definition (39 lines)
- `src/do_uw/stages/score/damages_estimation.py` - Base damages formula, allegation modifiers, defense costs, scenario grid, turnover rate (242 lines)
- `src/do_uw/stages/score/settlement_regression.py` - 12-feature log-linear model with published coefficients, feature extraction, allegation type inference (376 lines)
- `src/do_uw/stages/score/severity_amplifiers.py` - YAML loading, signal evaluation, multiplicative combination with 3.0 cap (220 lines)
- `src/do_uw/stages/score/layer_erosion.py` - Log-normal CDF, ABC/Side A erosion, DIC probability (288 lines)
- `src/do_uw/stages/score/legacy_severity_lens.py` - Post-hoc adapter wrapping SeverityScenarios (154 lines)
- `src/do_uw/stages/score/_severity_runner.py` - Full pipeline orchestrator for ScoreStage (273 lines)
- `src/do_uw/models/scoring.py` - Added severity_result field to ScoringResult with TYPE_CHECKING + model_rebuild()
- `src/do_uw/stages/score/__init__.py` - Added Step 15.5 severity model integration with graceful degradation
- `tests/stages/score/test_severity_lens.py` - 35 tests covering all severity modules (535 lines)

## Decisions Made

- **Regression intercept = 2.56**: Calibrated so typical case ($1B market cap, 20% decline, guidance_miss, 365-day class period, 2 defendants) predicts ~$5M median settlement per Cornerstone baseline
- **Multiplicative amplifier combination with 3.0 cap**: Actuarially sound -- multiplicative captures compounding severity factors, cap prevents unrealistic extremes
- **Log-normal via math.erfc**: Standard normal CDF = 0.5 * erfc(-x / sqrt(2)), avoiding scipy dependency while maintaining mathematical precision
- **Allegation-type-specific sigma**: Restatement cases have higher settlement dispersion (sigma=1.0) than guidance-miss cases (sigma=0.6), reflecting Cornerstone empirical data
- **DIC probability additive, capped at 0.8**: Going concern (0.5) + Altman distress (0.3) + cash runway (0.2) + leverage (0.1), conservative cap since DIC is never certain
- **Extra YAML field stripping**: severity_model_design.yaml has `calibration_required` on death_spiral amplifier not in SeverityAmplifier schema -- stripped before validation rather than modifying schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Regression intercept too high producing $35B settlements**
- **Found during:** Task 1 (settlement regression implementation)
- **Issue:** Initial intercept of 5.50 produced unrealistically high predictions when combined with log10(market_cap) coefficient
- **Fix:** Recalibrated intercept to 2.56 based on Cornerstone median settlement target of ~$5M for typical case features
- **Files modified:** src/do_uw/stages/score/settlement_regression.py
- **Verification:** Regression now produces $1M-$500M for typical mid-cap restatement case

**2. [Rule 3 - Blocking] SeverityAmplifier schema rejects calibration_required field**
- **Found during:** Task 2 (amplifier loading)
- **Issue:** death_spiral amplifier in YAML has extra `calibration_required: true` field that SeverityAmplifier schema (extra="forbid") rejects
- **Fix:** Strip fields not in schema before validation, logging warning for unexpected fields
- **Files modified:** src/do_uw/stages/score/severity_amplifiers.py
- **Verification:** All 11 amplifiers load successfully

**3. [Rule 1 - Bug] ORANGE zone test used wrong thresholds**
- **Found during:** Task 1 (SeverityZone tests)
- **Issue:** Test used P=0.15, S=$30M which is YELLOW, not ORANGE per the zone criteria
- **Fix:** Updated test to use P=0.25, S=$10M (which satisfies P >= 0.25 AND S >= $5M)
- **Files modified:** tests/stages/score/test_severity_lens.py
- **Verification:** Zone classification tests now match design doc criteria exactly

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 3 blocking)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SeverityLensResult and SeverityResult available on state.scoring.severity_result
- Plan 108-02 can implement SeverityScoringLens orchestrator, P x S chart, severity context builder, and CLI --attachment
- Phase 109 (Pattern Engines) can proceed independently
- All existing scoring infrastructure preserved with zero regressions

---
*Phase: 108-severity-model*
*Completed: 2026-03-16*
