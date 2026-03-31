---
phase: 06-scoring-patterns-risk-synthesis
plan: 01
subsystem: analyze
tags: [check-engine, threshold-evaluation, data-mappers, pydantic, analyze-stage]

# Dependency graph
requires:
  - phase: 05-litigation-regulatory-analysis
    provides: LitigationLandscape model and litigation extractors
  - phase: 04-market-trading-governance-analysis
    provides: MarketSignals and GovernanceData models
  - phase: 03-financial-data-extraction
    provides: ExtractedFinancials model and financial extractors
  - phase: 02-company-resolution-data-acquisition
    provides: CompanyProfile model and SEC data acquisition
provides:
  - AnalyzeStage that loads 359 checks from brain/checks.json
  - Check execution engine with 10 threshold type evaluators
  - Data mappers for all 6 sections (company, financial, market, governance, litigation)
  - CheckResult model with provenance (check_id, status, evidence, factors, section)
  - aggregate_results helper for summary counts
affects:
  - 06-02 (SCORE stage core): consumes state.analysis.check_results
  - 06-03 (pattern detection): may query check_results for pattern triggers
  - 06-04 (scoring calibration): needs_calibration flag on CheckResult

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Section-routed data mapping (check section -> domain mapper)"
    - "SourcedValue[T] safe unwrapping via generic _safe_sourced[T]() helper"
    - "Threshold direction detection from text (< vs > in threshold strings)"
    - "Chunked batch execution with progress logging"

key-files:
  created:
    - "src/do_uw/stages/analyze/check_results.py"
    - "src/do_uw/stages/analyze/check_engine.py"
    - "src/do_uw/stages/analyze/check_mappers.py"
    - "tests/test_analyze_stage.py"
  modified:
    - "src/do_uw/stages/analyze/__init__.py"
    - "tests/test_pipeline.py"

key-decisions:
  - "Qualitative tiered checks (non-numeric thresholds) report as INFO rather than attempting string matching"
  - "percentage/count/value threshold types share a common numeric evaluator to reduce duplication"
  - "Data mappers return all available fields for a section rather than per-check-id mapping"
  - "check_engine refactored to 455 lines via shared helpers (_first_data_value, _coerce_value, _make_skipped)"

patterns-established:
  - "CheckResult provenance pattern: every check produces exactly one result with check_id, status, evidence, factors"
  - "Section-routed mapping: map_check_data dispatches by section (1-2, 3, 4, 5, 6)"
  - "SourcedValue safe unwrapping: _safe_sourced[T]() generic helper for None-safe extraction"
  - "ConfigLoader mock pattern: patch 'do_uw.stages.analyze.ConfigLoader' for AnalyzeStage tests"

# Metrics
duration: 11min
completed: 2026-02-08
---

# Phase 6 Plan 1: ANALYZE Stage Summary

**Check execution engine with 10 threshold types, section-routed data mappers for 5 domains, and AnalyzeStage orchestrator populating state.analysis**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-08T19:11:43Z
- **Completed:** 2026-02-08T19:22:43Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Built complete ANALYZE pipeline stage replacing Phase 1 stub
- Check engine handles all 10 threshold types from checks.json (tiered, info, percentage, boolean, count, value, pattern, search, multi_period, classification)
- Data mappers safely traverse ExtractedData model tree across all 5 data domains (company, financial, market, governance, litigation)
- Missing data always produces SKIPPED status, never false CLEARs
- 37 tests covering engine, mappers, and orchestrator. 814 total tests passing.

## Task Commits

Each task was committed atomically:

1. **Task 1: CheckResult model and check execution engine** - `af0e8ed` (feat)
2. **Task 2: Data mappers and AnalyzeStage orchestrator** - `06d1d42` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/check_results.py` - CheckStatus enum, CheckResult model, aggregate_results helper (107 lines)
- `src/do_uw/stages/analyze/check_engine.py` - Check execution engine with 10 threshold evaluators, chunked batch processing (455 lines)
- `src/do_uw/stages/analyze/check_mappers.py` - Section-routed data mappers for company, financial, market, governance, litigation (493 lines)
- `src/do_uw/stages/analyze/__init__.py` - AnalyzeStage orchestrator loading brain config, executing checks, populating state.analysis (110 lines)
- `tests/test_analyze_stage.py` - 37 tests for check engine, mappers, and orchestrator
- `tests/test_pipeline.py` - Updated pipeline resume test for non-stub AnalyzeStage

## Decisions Made
- Qualitative tiered checks (non-numeric thresholds like "Prior SCA within 3 years") report as INFO since automated string comparison would be unreliable. The SCORE stage will handle these.
- percentage, count, and value threshold types share a common `_evaluate_numeric_threshold()` to eliminate code duplication (saved ~150 lines)
- Data mappers return ALL available fields for a section (not per-check-id specific), since checks share common data within a section domain
- Threshold direction detection parses "<" and ">" from threshold strings to determine if lower or higher values are worse

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed check_engine.py exceeding 500-line limit**
- **Found during:** Task 2 (pre-verification)
- **Issue:** Initial check_engine.py was 616 lines, exceeding the 500-line anti-context-rot limit
- **Fix:** Extracted common helpers (_first_data_value, _coerce_value, _make_skipped) and unified percentage/count/value evaluators into _evaluate_numeric_threshold
- **Files modified:** src/do_uw/stages/analyze/check_engine.py
- **Verification:** wc -l shows 455 lines
- **Committed in:** 06d1d42 (Task 2 commit)

**2. [Rule 3 - Blocking] Fixed pipeline resume test for non-stub AnalyzeStage**
- **Found during:** Task 2 (full test suite verification)
- **Issue:** test_resume_skips_completed_stages expected stub AnalyzeStage behavior; real stage requires state.extracted and ConfigLoader
- **Fix:** Added state.extracted = ExtractedData() and mocked ConfigLoader in test
- **Files modified:** tests/test_pipeline.py
- **Verification:** Full test suite passes (814 tests)
- **Committed in:** 06d1d42 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pyright strict mode required cast() for dict values from dict[str, Any].get() calls, which return Any type that pyright can't narrow through isinstance checks alone
- Python 3.12 type parameter syntax (PEP 695) required for ruff UP047 compliance: `def _safe_sourced[T](...)` instead of `TypeVar("T")`

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- state.analysis is now populated with CheckResult objects for all 351 AUTO checks
- SCORE stage (06-02) can consume state.analysis.check_results to compute factor scores
- Pattern detection (06-03) can query check_results by factor mapping
- Scoring calibration (06-04) can identify calibratable checks via needs_calibration flag
- No blockers for parallel execution with 06-02

---
*Phase: 06-scoring-patterns-risk-synthesis*
*Completed: 2026-02-08*
