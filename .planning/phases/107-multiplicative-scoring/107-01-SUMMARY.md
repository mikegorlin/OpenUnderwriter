---
phase: 107-multiplicative-scoring
plan: 01
subsystem: scoring
tags: [multiplicative-scoring, hae-model, electre-discordance, crf-veto, tier-classification, liberty-calibration, pydantic, protocol]

# Dependency graph
requires:
  - phase: 106-model-research
    provides: "scoring_model_design.yaml, decision_framework.yaml, rap_signal_mapping.yaml"
  - phase: 104-signal-consumer
    provides: "SignalResultView, signal_results dict contract"
  - phase: 103-schema-foundation
    provides: "514 signals with rap_class, rap_subcategory, evaluation.mechanism"
  - phase: 102-rap-taxonomy
    provides: "H/A/E taxonomy with 20 subcategories"
provides:
  - "ScoringLens Protocol -- pluggable scoring lens contract"
  - "HAETier 5-value enum with comparison operators"
  - "ScoringLensResult and CRFVetoResult Pydantic models"
  - "HAEScoringLens -- H/A/E composite computation + multiplicative P = H x A x E"
  - "evaluate_crf_discordance() -- CRF ELECTRE discordance with time/claim awareness"
  - "Liberty calibration by attachment tier and product type"
  - "ScoringResult.hae_result field for scoring pipeline integration"
affects: [108-severity-patterns, 109-pattern-engines, 110-score-integration, 112-worksheet-restructure]

# Tech tracking
tech-stack:
  added: [pyyaml]
  patterns: [scoring-lens-protocol, multiplicative-model, electre-discordance, dual-path-tier-assignment, module-level-cache-singleton]

key-files:
  created:
    - src/do_uw/stages/score/scoring_lens.py
    - src/do_uw/stages/score/hae_scoring.py
    - src/do_uw/stages/score/hae_crf.py
    - tests/stages/score/test_hae_scoring.py
  modified:
    - src/do_uw/models/scoring.py

key-decisions:
  - "TYPE_CHECKING guard + model_rebuild() to break circular import between models/scoring.py and stages/score/scoring_lens.py"
  - "5-tier P thresholds adapted from 6-tier design doc: PREFERRED [0,0.01), STANDARD [0.01,0.08), ELEVATED [0.08,0.25), HIGH_RISK [0.25,0.50), PROHIBITED [0.50,1.0]"
  - "CRF-RESTATEMENT veto target set to HIGH_RISK (not ELEVATED) per CONTEXT.md override"
  - "CRF-MULTI and CRF-MATERIAL-WEAKNESS veto targets remapped from ADVERSE->HIGH_RISK and CAUTIOUS->ELEVATED"
  - "Time decay: 1-tier reduction for aging+NO_CLAIM, 2-tier for expired+NO_CLAIM, STANDARD floor"

patterns-established:
  - "ScoringLens Protocol: all scoring models implement evaluate() returning ScoringLensResult"
  - "Module-level YAML cache singletons with monkeypatch-friendly module attributes for testing"
  - "Dual-path tier assignment: max(composite_tier, individual_tier) ensures single-dimension spikes are caught"
  - "CRF discordance: non-compensatory veto override applied externally to lens evaluation"

requirements-completed: [SCORE-01, SCORE-02, SCORE-03, SCORE-04]

# Metrics
duration: 9min
completed: 2026-03-15
---

# Phase 107 Plan 01: Multiplicative Scoring Model Summary

**H/A/E multiplicative scoring lens with P = H x A x E product, CRF ELECTRE discordance, dual-path 5-tier assignment, and Liberty calibration -- 58 passing tests**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-15T23:25:06Z
- **Completed:** 2026-03-15T23:34:02Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- ScoringLens Protocol defines pluggable lens contract for all future scoring models
- HAEScoringLens computes H/A/E composites from classified signal results using empirically-weighted subcategories from scoring_model_design.yaml
- P = H x A x E product with 0.05 floor captures interaction effects (high+high+low differs from medium+medium+medium)
- CRF ELECTRE discordance is time-aware (recent/aging/expired) and claim-status-aware (NO_CLAIM/CLAIM_FILED/CLAIM_RESOLVED)
- Dual-path tier assignment: both P score ranges and individual dimension criteria, most restrictive wins
- Liberty calibration adjusts weights for excess-only position (attachment tier) and product type (ABC vs Side A)
- 58 tests covering composites, multiplication, CRF vetoes, tiers, Liberty calibration, and full lens evaluation

## Task Commits

Each task was committed atomically (TDD: RED -> GREEN for each):

1. **Task 1: Scoring lens protocol + Pydantic models** - `611e964` (test)
2. **Task 2: H/A/E composite computation + multiplicative model + tier assignment** - `fc0030c` (feat)
3. **Task 3: CRF ELECTRE discordance with time/claim-status awareness** - `41b2da7` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/scoring_lens.py` (158 lines) - HAETier enum, ScoringLens Protocol, ScoringLensResult + CRFVetoResult models
- `src/do_uw/stages/score/hae_scoring.py` (480 lines) - H/A/E composite computation, multiplicative product, tier classification, Liberty calibration, HAEScoringLens class
- `src/do_uw/stages/score/hae_crf.py` (328 lines) - CRF ELECTRE discordance evaluation with time/claim-status awareness
- `src/do_uw/models/scoring.py` (modified) - Added hae_result field to ScoringResult with TYPE_CHECKING + model_rebuild
- `tests/stages/score/test_hae_scoring.py` (933 lines) - 58 tests across 16 test classes

## Decisions Made
- **Circular import resolution:** Used `TYPE_CHECKING` guard + `_rebuild_scoring_models()` function to break circular dependency between models/scoring.py (which imports ScoringLensResult) and stages/score/__init__.py (which imports from models/scoring.py). Pydantic v2 requires `model_rebuild()` since `from __future__ import annotations` makes annotations strings but Pydantic resolves them at model creation time.
- **5-tier threshold adaptation:** Merged CAUTIOUS into ELEVATED and ADVERSE into HIGH_RISK per CONTEXT.md. P thresholds adjusted to maintain similar risk discrimination with 5 bins instead of 6.
- **CRF-RESTATEMENT at HIGH_RISK:** Per CONTEXT.md: "Material restatement should map to HIGH_RISK, not just ELEVATED." Overrides the design doc's ELEVATED veto target.
- **Time decay initial parameters:** Implemented the structure per CONTEXT.md acknowledgment that "Decay curves need more thought." Aging reduces by 1 tier, expired by 2 tiers, STANDARD floor. Calibration-required flag set.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Resolved circular import between models/scoring.py and stages/score/scoring_lens.py**
- **Found during:** Task 1 (Pydantic model extension)
- **Issue:** Direct import of ScoringLensResult in models/scoring.py caused circular import through stages/score/__init__.py
- **Fix:** Used TYPE_CHECKING conditional import + model_rebuild() pattern
- **Files modified:** src/do_uw/models/scoring.py
- **Verification:** All 172 existing + new tests pass
- **Committed in:** 611e964 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary architectural adaptation for Pydantic v2 forward reference resolution. No scope creep.

## Issues Encountered
None beyond the circular import resolved above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ScoringLens Protocol ready for additional lens implementations (legacy 10-factor adapter)
- HAEScoringLens ready for integration into score stage pipeline (Phase 110)
- CRF discordance ready for score pipeline integration
- Shadow calibration comparison (Plan 107-02/03) can proceed against this scoring engine
- All source files under 500-line limit

## Self-Check: PASSED

All 5 created files exist. All 3 task commits verified in git log.

---
*Phase: 107-multiplicative-scoring*
*Completed: 2026-03-15*
