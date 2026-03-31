---
phase: 27-peril-mapping-bear-case-framework
plan: 06
subsystem: scoring
tags: [frequency-model, classification, hazard-profile, signal-adjustment, actuarial]

# Dependency graph
requires:
  - phase: 25
    provides: "Classification engine (base_filing_rate_pct) and hazard profile (ies_multiplier)"
  - phase: 27-04
    provides: "Peril mapping and bear case integration in ScoreStage"
provides:
  - "compute_enhanced_frequency() implementing classification x hazard x signal formula"
  - "EnhancedFrequency output model with full component breakdown"
  - "Unified frequency model replacing ad-hoc IES probability adjustment"
affects: [benchmark, render, actuarial-pricing]

# Tech tracking
tech-stack:
  added: []
  patterns: ["three-factor frequency decomposition: base_rate * hazard_mult * signal_mult"]

key-files:
  created:
    - "src/do_uw/stages/score/frequency_model.py"
    - "tests/stages/score/test_frequency_model.py"
  modified:
    - "src/do_uw/stages/score/__init__.py"

key-decisions:
  - "Enhanced frequency replaces Step 10.5 IES block to avoid double-application of hazard multiplier"
  - "Signal multiplier capped at 2.0x and final probability capped at 50% to prevent runaway values"
  - "Tier-based fallback preserved for backward compatibility when classification is unavailable"

patterns-established:
  - "Signal config dict at module level (_SIGNAL_CONFIG) for all multiplier thresholds"
  - "Three orthogonal signal sources (CRF, patterns, factors) multiply independently then cap"

# Metrics
duration: 4min
completed: 2026-02-12
---

# Phase 27 Plan 06: Enhanced Frequency Model Summary

**Filing probability from classification base rate x hazard IES multiplier x signal adjustments (CRF, patterns, elevated factors) with 2.0x signal cap and 50% probability ceiling**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-12T21:37:29Z
- **Completed:** 2026-02-12T21:41:20Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created `frequency_model.py` with explicit `adjusted_probability = base_rate * hazard_mult * signal_mult` formula
- Signal adjustments derived from 3 independent sources: CRF trigger count, detected pattern count, elevated factor ratio
- Replaced ad-hoc Step 10.5 IES multiplier block in ScoreStage with unified enhanced frequency call
- 16 tests covering clean companies, elevated signals, caps, and fallback scenarios
- Full test suite passes (2897 tests, 0 regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create enhanced frequency model** - `da3af8a` (feat)
2. **Task 2: Wire into ScoreStage** - `c759c6d` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/frequency_model.py` - Enhanced frequency model with classification x hazard x signal formula
- `tests/stages/score/test_frequency_model.py` - 16 tests covering all signal paths, caps, and fallbacks
- `src/do_uw/stages/score/__init__.py` - Replaced Step 10.5 IES block with compute_enhanced_frequency() call

## Decisions Made
- Enhanced frequency replaces Step 10.5 entirely (not added alongside) to avoid double-application of IES multiplier
- Signal multiplier capped at 2.0x to prevent runaway: max possible is CRF(1.50) * pattern(1.25) * factor(1.30) = 2.4375 -> capped to 2.0
- Final probability capped at 50% (no company has >50% annual filing probability)
- Tier-based fallback uses existing claim_prob.range_high_pct when classification is unavailable
- When neither classification nor scoring exists, falls back to 4.0% industry average

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Enhanced frequency model feeds directly into actuarial expected loss computation via claim_prob.range_high_pct
- Ready for Phase 27 Plan 07 (verification/integration testing)
- The formula is explicit and traceable: any future calibration can adjust _SIGNAL_CONFIG thresholds

## Self-Check: PASSED

- All 3 files exist on disk
- Both commit hashes (da3af8a, c759c6d) found in git log
- 16 frequency model tests pass
- 105 total score tests pass
- 2897 full suite tests pass, 0 regressions

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
