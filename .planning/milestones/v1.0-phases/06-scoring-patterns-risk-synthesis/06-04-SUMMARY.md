---
phase: 06-scoring-patterns-risk-synthesis
plan: 04
subsystem: scoring
tags: [severity-model, tower-positioning, red-flag-summary, score-stage, pipeline-integration]

# Dependency graph
requires:
  - phase: 06-02
    provides: "Partial ScoreStage orchestrator (CRF gates, factor scoring, tier classification)"
  - phase: 06-03
    provides: "Pattern detection engine, allegation mapping, risk type classification"
provides:
  - "Loss severity modeling at 4 percentile scenarios (25/50/75/95) with DDL"
  - "Tower position recommendation with Side A assessment"
  - "Red flag summary consolidation by severity tier"
  - "Complete 16-step ScoreStage orchestrator"
  - "Pattern modifier application to factor scores with max_points capping"
affects: [07-benchmark-peer-analysis, 08-render-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Severity scenario percentile modeling (base range * tier multiplier)"
    - "Tower position tier mapping with Side A distress assessment"
    - "Red flag consolidation from CRF + factors + patterns sorted by severity"
    - "Pattern modifier in-place application with re-capping"

key-files:
  created:
    - src/do_uw/stages/score/severity_model.py
    - tests/test_severity_tower.py
  modified:
    - src/do_uw/stages/score/__init__.py
    - tests/test_score_stage.py
    - tests/test_pipeline.py

key-decisions:
  - "_apply_pattern_modifiers as module-level function (not ScoreStage method) for testability"
  - "_get_market_cap helper extracts market cap from SourcedValue in company profile"
  - "ConfigLoader mock added to pipeline resume test alongside AnalyzeStage mock"

patterns-established:
  - "Severity scenario computation: base_range_m * tier_multiplier with defense cost percentages"
  - "Tower position recommendation: tier -> position map with Side A going_concern/altman_z/cash_runway assessment"
  - "Red flag summary: 3-source consolidation (CRF->CRITICAL, factors->by-%, patterns->severity-map) sorted by severity"

# Metrics
duration: 9min
completed: 2026-02-08
---

# Phase 6 Plan 4: Severity, Tower, Red Flags & Complete ScoreStage Summary

**Loss severity at 4 percentiles with DDL, tower positioning with Side A, red flag summary, and complete 16-step ScoreStage pipeline wiring all Phase 6 scoring components**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-08T20:07:39Z
- **Completed:** 2026-02-08T20:16:23Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Loss severity modeling producing 4-scenario output (favorable/median/adverse/catastrophic) with DDL decline scenarios and defense cost estimates
- Tower position recommendation mapping tiers to positions (PRIMARY through DECLINE) with Side A indemnification assessment (going concern, Altman Z, cash runway)
- Red flag summary consolidating CRF triggers (CRITICAL), factor scores (HIGH/MODERATE/LOW by %), and detected patterns (severity-mapped) into sorted list
- Complete 16-step ScoreStage orchestrator wiring all Phase 6 components: CRF -> factors -> patterns -> modifiers -> composite -> ceiling -> tier -> risk type -> allegations -> probability -> severity -> tower -> red flags
- Pattern modifier application adjusting factor scores in-place with max_points re-capping before composite calculation

## Task Commits

Each task was committed atomically:

1. **Task 1: Severity model, tower positioning, and red flag summary** - `773d540` (feat)
2. **Task 2: Complete ScoreStage orchestrator and pipeline integration** - `67046c0` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/severity_model.py` - Loss severity (4 percentiles), tower recommendation (tier->position), red flag summary (3-source consolidation), Side A assessment (380 lines)
- `tests/test_severity_tower.py` - 25 tests for severity model, tower recommendation, red flag summary, and line count validation
- `src/do_uw/stages/score/__init__.py` - Complete 16-step ScoreStage orchestrator with pattern modifier application (207 lines)
- `tests/test_score_stage.py` - 3 new tests: full pipeline fields, pattern modifiers applied/capped, no detected patterns (48 total)
- `tests/test_pipeline.py` - Updated resume test with ScoreStage ConfigLoader mocking

## Decisions Made
- `_apply_pattern_modifiers` as module-level function (not method) for independent testability and clarity
- `_get_market_cap` helper to extract float from SourcedValue company.market_cap field
- Pipeline resume test required ConfigLoader mock for ScoreStage (brain config files are on disk but test should be isolated)
- severity_model.py initially 535 lines, compacted to 380 by reducing docstring/comment verbosity while preserving all functionality

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] severity_model.py exceeded 500-line limit**
- **Found during:** Task 1 (severity model creation)
- **Issue:** Initial implementation was 535 lines, exceeding the 500-line project constraint
- **Fix:** Compacted docstrings, removed verbose comments, consolidated blank lines; reduced to 380 lines
- **Files modified:** src/do_uw/stages/score/severity_model.py
- **Verification:** `test_severity_model_under_500_lines` passes (380 < 500)
- **Committed in:** 773d540 (Task 1 commit)

**2. [Rule 3 - Blocking] Missing PatternMatch import in test_score_stage.py**
- **Found during:** Task 2 (new pattern modifier tests)
- **Issue:** New tests used PatternMatch but it wasn't in the import block
- **Fix:** Added PatternMatch to `from do_uw.models.scoring import` statement
- **Files modified:** tests/test_score_stage.py
- **Verification:** All 48 score stage tests pass
- **Committed in:** 67046c0 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None - plan executed as designed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 6 COMPLETE: All 4 plans executed (06-01 through 06-04)
- ANALYZE + SCORE stages work end-to-end in the pipeline
- 926 tests passing (up from 898 at phase start), 0 pyright errors, 0 ruff issues
- All score/ files under 500 lines (largest: factor_scoring.py at 497)
- Ready for Phase 7 (Benchmark & Peer Analysis) which will consume scoring output
- SECT7-11 calibration notes populated throughout - all scoring parameters flagged as needing historical calibration

---
*Phase: 06-scoring-patterns-risk-synthesis*
*Completed: 2026-02-08*
