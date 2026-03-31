---
phase: 27-peril-mapping-bear-case-framework
plan: 03
subsystem: scoring
tags: [settlement-prediction, ddl, severity-model, tower-positioning, ilf, actuarial]

# Dependency graph
requires:
  - phase: 12
    provides: "Severity model (model_severity), actuarial pricing chain"
  - phase: 26
    provides: "CRF gates, analytical engines, check_results on state"
provides:
  - "DDL-based settlement prediction model (predict_settlement)"
  - "Case characteristic detection from analysis state"
  - "Tower risk characterization by ILF expected loss share per layer"
  - "settlement_calibration.json config for DDL model parameters"
affects: [render, actuarial-pricing, peril-map, bear-case]

# Tech tracking
tech-stack:
  added: []
  patterns: ["DDL computation from stock drops", "case characteristic multipliers", "ILF-based layer risk distribution"]

key-files:
  created:
    - src/do_uw/stages/score/settlement_prediction.py
    - src/do_uw/stages/score/case_characteristics.py
    - tests/stages/score/__init__.py
    - tests/stages/score/test_settlement_prediction.py
  modified:
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/score/severity_model.py

key-decisions:
  - "predict_settlement returns None (not fallback result) when no stock drops, letting ScoreStage explicitly choose fallback path"
  - "Case characteristic detection split into separate module (case_characteristics.py) for 500-line compliance"
  - "Tower risk characterization uses ILF alpha power curve to compute per-layer expected loss share percentages"
  - "Settlement prediction stored on state.analysis.settlement_prediction as dict (matching Phase 26 serialization pattern)"

patterns-established:
  - "DDL-based severity: market_cap * max_drop -> base_settlement_pct -> multipliers -> spread scenarios"
  - "Analytical tower positioning: per-layer % of expected loss, not prescriptive attachment points"

# Metrics
duration: 9min
completed: 2026-02-12
---

# Phase 27 Plan 03: DDL-Based Settlement Prediction Summary

**DDL-based settlement prediction from stock drops with case characteristic multipliers replacing tier-based severity lookup, plus ILF-based tower risk characterization by layer**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-12T20:54:19Z
- **Completed:** 2026-02-12T21:03:24Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- DDL computation from actual stock drops (market_cap * max_drop_magnitude) replaces market-cap-tier lookup tables
- 5-step settlement prediction pipeline: DDL -> base % -> case characteristic multipliers -> scenario spread -> defense costs
- Case characteristic detection inspects 10 signals from analysis state (CRF triggers, insider selling, going concern, etc.)
- Tower risk characterization computes per-layer expected loss share using ILF power curve
- ScoreStage Step 11 uses DDL model first, falls back to tier-based model when no stock drops
- 31 new tests covering DDL, prediction, characteristics, tower risk, actuarial compatibility
- Full test suite: 2826 passed, 0 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement DDL-based settlement prediction model** - `c022a92` (feat)
2. **Task 2: Wire settlement prediction into ScoreStage, refactor severity_model.py** - `96bd25e` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/settlement_prediction.py` - DDL computation, predict_settlement, characterize_tower_risk (377 lines)
- `src/do_uw/stages/score/case_characteristics.py` - detect_case_characteristics with 10 signal checks (278 lines)
- `src/do_uw/stages/score/__init__.py` - Step 11 updated to try DDL model first, fall back to tier; Step 12 passes tower_risk_data
- `src/do_uw/stages/score/severity_model.py` - model_severity marked as FALLBACK; recommend_tower accepts tower_risk_data; _build_layer_assessments enriched with ILF share
- `tests/stages/score/test_settlement_prediction.py` - 31 tests across DDL, prediction, characteristics, tower risk, actuarial compat
- `tests/stages/score/__init__.py` - Test package init

## Decisions Made
- predict_settlement() returns None when no stock drops (explicit fallback signal) rather than computing a degraded estimate
- Split case_characteristics.py (278 lines) from settlement_prediction.py (377 lines) to comply with 500-line rule
- Tower risk characterization uses analytical ILF distribution ("Primary carries 48% of expected loss") instead of prescriptive attachment points
- Settlement prediction stored as dict on state.analysis.settlement_prediction, consistent with Phase 26 serialization pattern for analytical engine outputs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- settlement_calibration.json already existed from a prior plan execution (Plan 02 dependency); used the existing config without modification.
- Initial settlement_prediction.py was 630 lines; split case_characteristics.py to comply with 500-line anti-context-rot rule.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Settlement prediction integrated into scoring pipeline; actuarial pricing chain works unchanged
- Tower risk characterization data available for peril map and render stages
- Bear case construction (Plan 04/05) can use DDL and case characteristic data for evidence-based narratives

## Self-Check: PASSED

- All 6 key files: FOUND
- Commit c022a92 (Task 1): FOUND
- Commit 96bd25e (Task 2): FOUND
- Test suite: 2826 passed, 0 regressions

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
