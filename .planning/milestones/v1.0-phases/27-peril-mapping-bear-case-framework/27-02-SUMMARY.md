---
phase: 27-peril-mapping-bear-case-framework
plan: 02
subsystem: scoring
tags: [peril-mapping, plaintiff-assessment, pydantic, severity-bands, plaintiff-firms]

requires:
  - phase: 26-check-reorganization
    provides: "Faceted check classification with PlaintiffLens, CheckCategory, and check_classification.json"
  - phase: 27-01
    provides: "DataStatus three-state enum on CheckResult (EVALUATED, DATA_UNAVAILABLE, NOT_APPLICABLE)"
provides:
  - "PerilMap, PlaintiffAssessment, BearCase, EvidenceItem, PlaintiffFirmMatch Pydantic models"
  - "7-lens plaintiff assessment engine (build_peril_map)"
  - "plaintiff_firms.json config with 3-tier severity multipliers"
  - "settlement_calibration.json config with DDL-based multiplier parameters"
  - "AnalysisResults.peril_map and settlement_prediction dict fields"
affects: [27-03-settlement-prediction, 27-04-bear-case-construction, 27-05-score-stage-integration]

tech-stack:
  added: []
  patterns:
    - "Peril probability bands (VERY_LOW through HIGH) separate from scoring ProbabilityBand"
    - "FULL vs PROPORTIONAL modeling depth per plaintiff lens"
    - "Config-driven plaintiff firm tier matching with severity multipliers"

key-files:
  created:
    - src/do_uw/models/peril.py
    - src/do_uw/stages/score/peril_mapping.py
    - src/do_uw/config/plaintiff_firms.json
    - src/do_uw/config/settlement_calibration.json
    - tests/models/test_peril_models.py
    - tests/stages/score/test_peril_mapping.py
  modified:
    - src/do_uw/models/state.py

key-decisions:
  - "PerilProbabilityBand (VERY_LOW..HIGH) separate from scoring ProbabilityBand (LOW..VERY_HIGH) to avoid namespace collision"
  - "SHAREHOLDERS and REGULATORS get FULL modeling; other 5 lenses get PROPORTIONAL count-based estimation"
  - "Tier 3 firms are default (no match) -- only tier 1 and 2 produce PlaintiffFirmMatch entries"
  - "Bear cases left empty in PerilMap (populated by Plan 04 bear case construction)"
  - "peril_map and settlement_prediction stored as dict[str, Any] on AnalysisResults (following Phase 26 engine output pattern)"

patterns-established:
  - "Peril models as separate module from scoring_output.py to avoid coupling"
  - "assess_lens() with FULL/PROPORTIONAL depth flag for per-lens assessment strategy"
  - "Coverage gap collection from DATA_UNAVAILABLE data_status for three-state reporting"

duration: 8min
completed: 2026-02-12
---

# Phase 27 Plan 02: Peril Mapping Models and 7-Lens Assessment Engine Summary

**7-lens plaintiff assessment engine with PerilProbabilityBand/SeverityBand mapping, config-driven plaintiff firm matching, and settlement calibration parameters**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-12T20:53:50Z
- **Completed:** 2026-02-12T21:02:10Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created 7 Pydantic models for peril mapping (PerilMap, PlaintiffAssessment, BearCase, EvidenceItem, PlaintiffFirmMatch, PerilProbabilityBand, PerilSeverityBand)
- Built 7-lens plaintiff assessment engine producing exactly 7 assessments per company with FULL/PROPORTIONAL modeling depth
- Created plaintiff_firms.json (3-tier severity multipliers) and settlement_calibration.json (DDL-based calibration with 10 multipliers)
- Extended AnalysisResults with peril_map and settlement_prediction dict fields
- 45 total tests (13 model + 32 engine) all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create peril Pydantic models, config files, and extend AnalysisResults** - `b4ad95e` (feat)
2. **Task 2: Implement 7-lens plaintiff assessment engine** - `036c01d` (feat)

**Plan metadata:** (see final commit)

## Files Created/Modified
- `src/do_uw/models/peril.py` - PerilMap, PlaintiffAssessment, BearCase, EvidenceItem, PlaintiffFirmMatch Pydantic models
- `src/do_uw/stages/score/peril_mapping.py` - 7-lens assessment engine: build_peril_map, assess_lens, match_plaintiff_firms (417 lines)
- `src/do_uw/config/plaintiff_firms.json` - 3-tier plaintiff firm config with severity multipliers (2.0x/1.5x/1.0x)
- `src/do_uw/config/settlement_calibration.json` - DDL-based settlement calibration with 10 multipliers
- `src/do_uw/models/state.py` - Added peril_map and settlement_prediction dict fields to AnalysisResults
- `tests/models/test_peril_models.py` - 13 tests for peril model construction, serialization, round-trip
- `tests/stages/score/test_peril_mapping.py` - 32 tests for assessment engine, probability/severity bands, firm matching

## Decisions Made
- Created PerilProbabilityBand (VERY_LOW, LOW, MODERATE, ELEVATED, HIGH) separate from scoring_output.ProbabilityBand to avoid enum collision -- peril uses different scale boundaries
- SHAREHOLDERS and REGULATORS receive FULL probabilistic modeling (claim probability + severity scenarios); other 5 lenses use PROPORTIONAL count-based thresholds
- Plaintiff firm matching returns None for unrecognized firms (tier 3 is the default, not a "match") -- only tier 1/2 firms create PlaintiffFirmMatch entries
- Coverage gaps collected from DATA_UNAVAILABLE checks flow through to PerilMap.coverage_gaps for worksheet reporting

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan 27-01 DataStatus prerequisite was uncommitted**
- **Found during:** Task 1 (staging files for commit)
- **Issue:** Plan 27-01 DataStatus changes (check_results.py, check_engine.py, test_data_status.py) were in the working tree but uncommitted
- **Fix:** Included in Task 1 commit since peril_mapping.py imports DataStatus
- **Files modified:** (already in working tree, just staged)
- **Verification:** 22 DataStatus tests pass
- **Committed in:** b4ad95e (combined with Task 1)

---

**Total deviations:** 1 auto-fixed (1 blocking prerequisite)
**Impact on plan:** Prerequisite dependency was already coded, just needed committing. No scope creep.

## Issues Encountered
- Initial peril_mapping.py was 613 lines (over 500-line CLAUDE.md limit). Compacted docstrings and consolidated helpers to reach 417 lines without removing any functionality.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Peril models and assessment engine ready for Plan 03 (settlement prediction) and Plan 04 (bear case construction)
- PerilMap.bear_cases intentionally left empty -- populated by Plan 04
- settlement_calibration.json parameters ready for Plan 03's DDL-based settlement model
- All tests passing, no regressions

## Self-Check: PASSED

All 6 created files verified on disk. Both commit hashes (b4ad95e, 036c01d) verified in git log. 67 tests passing (13 model + 32 engine + 22 DataStatus).

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
