---
phase: 131-scoring-depth-and-visualizations
plan: 02
subsystem: scoring
tags: [probability-decomposition, scenario-generator, risk-clusters, context-builders]

requires:
  - phase: 131-01
    provides: scoring visualization Pydantic models (ProbabilityComponent, ScoreScenario, RiskCluster)
provides:
  - build_probability_decomposition() - 7+ additive probability components from multiplicative model
  - generate_scenarios() - 5-7 company-specific score-impact scenarios with tier re-classification
  - compute_risk_clusters() - factor grouping into 5 role dimensions with dominant cluster detection
affects: [131-03-templates, 132-page0-dashboard]

tech-stack:
  added: []
  patterns: [multiplicative-to-additive decomposition, condition-based scenario filtering, role-based factor clustering]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/probability_decomposition.py
    - src/do_uw/stages/render/context_builders/scenario_generator.py
    - tests/render/test_probability_decomposition.py
    - tests/render/test_scenario_generator.py
    - tests/render/test_risk_cluster.py
  modified: []

key-decisions:
  - "Multiplicative-to-additive conversion uses marginal impact on running total per component"
  - "Residual Model Interaction component reconciles multiplicative interaction effects"
  - "Scenario deltas use target-deduction approach (set to delta if higher than current) not additive"
  - "_classify_tier_simple avoids import coupling with tier_classification module"

patterns-established:
  - "Probability components: each multiplicative factor decomposed via running_total * ratio * weight"
  - "Scenario condition evaluation: string-based conditions matched against factor score thresholds"
  - "Risk clusters: static factor-to-role mapping with percentage-based dominance detection"

requirements-completed: [PROB-01, PROB-02, PROB-03, SCEN-01, SCEN-02, SCORE-04]

duration: 6min
completed: 2026-03-23
---

# Phase 131 Plan 02: Probability Decomposition, Scenario Generator, and Risk Clusters Summary

**Probability decomposition into 7+ calibrated/uncalibrated components, 8 company-specific scenario templates with tier re-classification, and 5-cluster risk concentration analysis**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T21:15:12Z
- **Completed:** 2026-03-23T21:21:41Z
- **Tasks:** 2
- **Files created:** 5

## Accomplishments
- Probability decomposition transforms multiplicative EnhancedFrequency (base * hazard * signal) into 7+ additive display components with calibration labels (NERA/Cornerstone/SCAC citations for calibrated; UNCALIBRATED badges for estimated)
- Scenario generator produces 5-7 company-specific scenarios from 8 templates, with condition-based filtering (SCA filed vs escalation), score deltas respecting max_points caps, and tier re-classification via scoring.json
- Risk cluster computation groups 10 factors into 5 role dimensions (Litigation, Stock & Market, Financial Integrity, Corporate Actions, Governance) with dominant cluster detection at >50% threshold
- All functions use safe_float() for robust handling of non-numeric state data, graceful empty-list returns when scoring data is None

## Task Commits

Each task was committed atomically:

1. **Task 1: Probability decomposition context builder** - `db4f549c` (feat)
2. **Task 2: Scenario generator + risk cluster computation** - `a62cf855` (feat)

_Note: TDD tasks -- tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/probability_decomposition.py` - 7+ component decomposition from multiplicative frequency model
- `src/do_uw/stages/render/context_builders/scenario_generator.py` - Scenario generation (8 templates) and risk cluster computation (5 role dimensions)
- `tests/render/test_probability_decomposition.py` - 9 tests for probability decomposition
- `tests/render/test_scenario_generator.py` - 9 tests for scenario generator
- `tests/render/test_risk_cluster.py` - 6 tests for risk cluster computation

## Decisions Made
- Multiplicative-to-additive conversion computes each component's marginal impact on the running total (running_total * factor_ratio * weight), with a "Model Interaction" residual to reconcile interaction effects within 0.1% tolerance
- Scenario delta approach: positive deltas set deduction to max(current, delta) capped at max_points; negative deltas reduce deduction -- this prevents double-counting and respects factor caps
- Tier re-classification uses a local _classify_tier_simple() returning plain strings to avoid import coupling with tier_classification.py while maintaining identical logic
- scoring.json tier config loaded directly from brain/config path with fallback tiers

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functions fully implemented with real computation logic.

## Next Phase Readiness
- Context builders ready for Plan 03 template integration (waterfall chart, scenario table, probability decomposition display, tornado chart, risk cluster visualization)
- Functions return plain dicts compatible with Jinja2 template consumption
- All 24 tests passing, modules under 350 lines each

## Self-Check: PASSED

- All 5 created files exist on disk
- Both task commits (db4f549c, a62cf855) found in git log
- All 24 tests passing

---
*Phase: 131-scoring-depth-and-visualizations*
*Completed: 2026-03-23*
