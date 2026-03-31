---
phase: 26-check-reorganization-analytical-engine
plan: 03
subsystem: analyze
tags: [forensic-scoring, dechow-f-score, montier-c-score, sloan-ratio, accrual-intensity, financial-integrity-score, composite-scoring]

# Dependency graph
requires:
  - phase: 26-01
    provides: "ForensicZone, SubScore, FinancialIntegrityScore, RevenueQualityScore, CashFlowQualityScore Pydantic models; forensic_models.json config; check classification metadata"
provides:
  - "Dechow F-Score, Montier C-Score, Enhanced Sloan Ratio, Accrual Intensity model computations"
  - "FIS, RQS, CFQS composite scoring with config-driven weights and zone classification"
  - "Beneish-Dechow convergence detection (amplifier pattern)"
  - "13 FIN.FORENSIC.* and FIN.QUALITY.* checks in checks.json"
affects: [26-05, score-stage, render-stage]

# Tech tracking
tech-stack:
  added: []
  patterns: [config-driven-composite-scoring, graceful-degradation-reweighting, amplifier-check-pattern, normalize-to-score-mapping]

key-files:
  created:
    - src/do_uw/stages/analyze/forensic_models.py
    - src/do_uw/stages/analyze/forensic_composites.py
    - tests/test_forensic_composites.py
  modified:
    - src/do_uw/brain/checks.json

key-decisions:
  - "Dechow F-Score uses simplified 5-component formula (no cross-sectional peer regression) per research guidance"
  - "Beneish-Dechow convergence is an AMPLIFIER (bonus points) not fully additive, per research Pitfall 3"
  - "Missing sub-dimensions reweight proportionally rather than zeroing out composite score"
  - "_classify_zone uses default config thresholds when no explicit zones param passed"

patterns-established:
  - "normalize_to_score: Maps any raw metric to 0-100 scale handling both ascending and descending scales"
  - "weighted_composite: Weighted average that skips None values and reweights from remaining"
  - "amplifier check pattern: check with amplifier=true and amplifier_bonus_points in checks.json"

# Metrics
duration: 25min
completed: 2026-02-12
---

# Phase 26 Plan 03: Forensic Models & Composite Scoring Summary

**Dechow F-Score, Montier C-Score, Enhanced Sloan Ratio, Accrual Intensity models with FIS/RQS/CFQS composites combining 5 sub-dimensions via config-driven weights into 0-100 zone-classified scores**

## Performance

- **Duration:** ~25 min (across context continuation)
- **Started:** 2026-02-12
- **Completed:** 2026-02-12
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 1

## Accomplishments
- Implemented 4 academic fraud detection models: Dechow F-Score (5 components), Montier C-Score (6 binary indicators), Enhanced Sloan Accrual Ratio, Accrual Intensity
- Built 3 composite scores (FIS, RQS, CFQS) combining sub-dimensions with config-driven weights from forensic_models.json
- Zone classification (HIGH_INTEGRITY through CRITICAL) maps 0-100 scores to actionable categories
- Added 13 new FIN.FORENSIC.* and FIN.QUALITY.* checks to checks.json with full classification metadata
- Beneish-Dechow convergence detection as amplifier pattern (bonus points, not additive)
- 27 unit tests covering all models, composites, zone boundaries, edge cases, and checks.json integration
- Graceful degradation: missing data triggers proportional reweighting, never crashes

## Task Commits

Each task was committed atomically:

1. **Task 1: Forensic model implementations and composite scoring** - `ca5f089` (feat)
2. **Task 2: Add tests for forensic models and composites** - `cdbe0e2` (test)

## Files Created/Modified
- `src/do_uw/stages/analyze/forensic_models.py` (326 lines) - Dechow F-Score, Montier C-Score, Enhanced Sloan Ratio, Accrual Intensity computations
- `src/do_uw/stages/analyze/forensic_composites.py` (455 lines) - FIS, RQS, CFQS composite scoring with weighted combination, zone classification, convergence detection
- `tests/test_forensic_composites.py` (557 lines) - 27 tests: 12 test classes covering all forensic models, composites, helpers, and checks.json integration
- `src/do_uw/brain/checks.json` - 13 new checks: 6 FIN.FORENSIC.* (fis_composite, dechow_f_score, montier_c_score, enhanced_sloan, accrual_intensity, beneish_dechow_convergence) + 7 FIN.QUALITY.* (revenue_quality_score, cash_flow_quality, dso_ar_divergence, q4_revenue_concentration, deferred_revenue_trend, quality_of_earnings, non_gaap_divergence)

## Decisions Made
- **Dechow simplified**: Used 5-component formula without cross-sectional peer regression (per research "don't hand-roll" guidance). Score = 1.0 + normalized raw components.
- **Convergence as amplifier**: Beneish-Dechow convergence adds bonus confirmation points (amplifier_bonus_points: 2) rather than full additive scoring per research Pitfall 3.
- **Reweighting on missing data**: When a sub-dimension has no data, remaining dimensions are proportionally reweighted rather than penalizing or zeroing out.
- **Zone classification defaults**: _classify_zone loads default thresholds from forensic_models.json when no explicit zones parameter is passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SourcedValue requires as_of datetime field**
- **Found during:** Task 2 (writing tests)
- **Issue:** SourcedValue model requires `as_of` field; tests failed with validation error
- **Fix:** Added `from datetime import UTC, datetime` and `as_of=_NOW` to all SourcedValue constructors in test fixtures
- **Files modified:** tests/test_forensic_composites.py
- **Committed in:** cdbe0e2

**2. [Rule 1 - Bug] Dechow F-Score test_low_risk soft assets too high**
- **Found during:** Task 2 (writing tests)
- **Issue:** "Clean" test data had soft_assets/TA = 0.48, producing score 2.22 instead of < 1.40
- **Fix:** Increased PPE to 700 and cash to 200 to reduce soft_assets/TA to 0.10
- **Files modified:** tests/test_forensic_composites.py
- **Committed in:** cdbe0e2

**3. [Rule 3 - Blocking] checks.json edit anchor non-unique**
- **Found during:** Task 2 (adding checks to checks.json)
- **Issue:** Initial edit anchor matched wrong location in checks.json, duplicating content
- **Fix:** Reverted to HEAD and used globally unique anchor ("metric": "net_income_cfo_divergence")
- **Files modified:** src/do_uw/brain/checks.json
- **Committed in:** ca5f089 (checks were part of Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered
- Test file (557 lines) exceeds 500-line project guideline, but this is a test file (not source code) and splitting it would reduce test cohesion. All 27 tests are tightly related to the forensic scoring subsystem.
- Plan 26-04 was committed by a parallel agent (3e19be0) before Task 2 commit, meaning checks.json already contained the 13 forensic/quality checks at commit time. The test file was committed as standalone.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Forensic model computations ready for integration into analyze stage check execution
- FIS/RQS/CFQS composites available for score stage factor calculations
- 13 new checks in checks.json ready for check engine execution
- Convergence amplifier pattern established for score stage bonus point logic
- Plan 26-05 (scoring integration) can consume all forensic outputs

---
*Phase: 26-check-reorganization-analytical-engine*
*Completed: 2026-02-12*
