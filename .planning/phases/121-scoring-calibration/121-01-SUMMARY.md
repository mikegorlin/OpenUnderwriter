---
phase: 121-scoring-calibration
plan: 01
subsystem: scoring
tags: [crf-ceilings, weighted-compounding, size-severity-matrix, distress-graduation, ddl-consistency]

# Dependency graph
requires:
  - phase: 110-mechanism-signals
    provides: CRF-12 through CRF-17 gates, adversarial critique
provides:
  - Size-conditioned CRF ceiling resolution via scoring.json config
  - Weighted CRF compounding algorithm for multiple triggered CRFs
  - Distress-graduated CRF-13 ceiling (going concern / severe / distress / gray)
  - DDL narrative consistency reading from scoring stage settlement prediction
affects: [121-02 calibration baseline, render sections using DDL, scoring pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [size-severity-matrix config pattern, weighted-compounding algorithm, distress-graduation config pattern]

key-files:
  created:
    - tests/stages/score/test_crf_calibration.py
    - tests/stages/score/test_weighted_compounding.py
  modified:
    - src/do_uw/brain/config/scoring.json
    - src/do_uw/stages/score/red_flag_gates.py
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/render/sections/sect1_findings_data.py

key-decisions:
  - "CRF ceiling resolution order: distress_graduation > size_severity_matrix > flat max_quality_score"
  - "Compounding factor 0.5x per additional CRF, max reduction 80%, floor at 5"
  - "Default severity_weight 0.15 for CRFs not in scoring.json config"
  - "DDL reads scoring.severity_scenarios median first, analysis.settlement_prediction second, rough estimate last"

patterns-established:
  - "size_severity_matrix: config-driven ceiling lookup by market cap tier"
  - "distress_graduation: severity-graduated ceiling for financial distress CRF"
  - "Weighted CRF compounding: primary ceiling * (1 - sum(additional_weights * 0.5))"

requirements-completed: [SCORE-01, FIX-02]

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 121 Plan 01: Scoring Calibration Summary

**Size-conditioned CRF ceilings with weighted compounding: AAPL mega-cap ceiling 70 (WANT) vs ANGI micro-cap ceiling 25 (WALK), DDL narrative reads scoring stage**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-21T19:36:38Z
- **Completed:** 2026-03-21T19:42:38Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- CRF-001 (Active SCA) and CRF-008 (catastrophic decline) now use size_severity_matrix with 5 market cap tiers
- CRF-013 (Altman distress) uses distress_graduation with 4 severity levels (going concern=15, severe=20, distress=40, gray=55)
- apply_crf_ceilings() now supports weighted compounding: multiple CRFs compound downward from primary ceiling
- DDL narrative estimate reads from scoring stage settlement_prediction as authoritative source (FIX-02)
- Full backward compatibility maintained: old 2-arg call to apply_crf_ceilings still works
- 21 new tests, 470 total scoring tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for CRF calibration** - `452defd2` (test)
2. **Task 1 (GREEN): Size-conditioned CRF ceilings + weighted compounding** - `a7784843` (feat)
3. **Task 2: DDL narrative consistency FIX-02** - `b4dfb16a` (fix)

## Files Created/Modified
- `src/do_uw/brain/config/scoring.json` - Added size_severity_matrix (CRF-001, CRF-008), distress_graduation (CRF-013), severity_weight on all 12 CRFs
- `src/do_uw/stages/score/red_flag_gates.py` - Added _resolve_crf_ceiling(), rewrote apply_crf_ceilings() with weighted compounding
- `src/do_uw/stages/score/__init__.py` - Step 6 now passes scoring_config and market_cap
- `src/do_uw/models/scoring.py` - Added ceiling_details field to ScoringResult
- `src/do_uw/stages/render/sections/sect1_findings_data.py` - ddl_estimate() reads scoring stage DDL first
- `tests/stages/score/test_crf_calibration.py` - 16 tests: size conditioning, distress graduation, integration, DDL consistency
- `tests/stages/score/test_weighted_compounding.py` - 5 tests: compounding, floor, details

## Decisions Made
- CRF ceiling resolution priority: distress_graduation > size_severity_matrix > flat -- distress has unique severity semantics that override size
- Compounding factor set at 0.5x per additional CRF with 80% max reduction and floor at 5 -- prevents total annihilation while ensuring 17 CRFs produce meaningfully lower ceiling than 1 CRF
- Default severity_weight 0.15 for CRFs not explicitly configured -- conservative default for unlisted CRFs
- DDL authoritative source is scoring.severity_scenarios median scenario -- scorecard and narrative now agree

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Size-conditioned ceilings and weighted compounding are in place for 121-02 calibration baseline
- DDL consistency fixed, ready for render verification
- All scoring tests green, pipeline integration ready for multi-ticker validation

---
*Phase: 121-scoring-calibration*
*Completed: 2026-03-21*
