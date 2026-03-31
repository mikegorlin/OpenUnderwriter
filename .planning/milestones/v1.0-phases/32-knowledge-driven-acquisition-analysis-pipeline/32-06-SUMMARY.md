---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 06
subsystem: knowledge, brain, analysis
tags: [pydantic, duckdb, gap-detection, effectiveness-tracking, requirements-analysis]

# Dependency graph
requires:
  - phase: 32-04
    provides: "v6 taxonomy remap — all 388 checks use X.Y subsection IDs"
  - phase: 32-05
    provides: "BrainDBLoader wired as primary check source, content-type dispatch"
provides:
  - "AcquisitionManifest model and build_manifest() from check declarations"
  - "PipelineGapDetector with 3-level gap analysis (source/field/mapper)"
  - "EffectivenessTracker with fire_rate/skip_rate computation from brain_check_runs"
  - "brain_effectiveness table population with flags (always_fires, never_fires, high_skip)"
  - "record_check_run() and record_check_runs_batch() for pipeline integration"
affects: [32-07-brain-cli-backtest, phase-33-living-knowledge]

# Tech tracking
tech-stack:
  added: []
  patterns: [requirements-manifest-from-declarations, 3-level-gap-analysis, effectiveness-classification]

key-files:
  created:
    - src/do_uw/knowledge/requirements.py
    - src/do_uw/knowledge/gap_detector.py
    - src/do_uw/brain/brain_effectiveness.py
    - tests/knowledge/test_requirements.py
    - tests/knowledge/test_gap_detector.py
    - tests/brain/test_brain_effectiveness.py
  modified: []

key-decisions:
  - "High-skip classification takes priority over never-fire in elif chain (data gap > calibration concern)"
  - "Confidence thresholds: LOW (N<5), MEDIUM (5-20), HIGH (20+) — N=5 is boundary for MEDIUM"
  - "KnowledgeStore CheckRun and brain_check_runs coexist — convergence deferred to future plan"
  - "Phase 26+ dedicated mapper checks (EXEC/NLP/FIN.TEMPORAL/FORENSIC/QUALITY/FWRD) treated as having field routing coverage (not gaps)"

patterns-established:
  - "Requirements manifest pattern: parse check declarations to derive pipeline requirements without modifying acquisition"
  - "3-level gap analysis: SOURCE (CRITICAL) > FIELD (WARNING) > MAPPER (INFO) severity ordering"
  - "Effectiveness classification priority: always-fire > high-skip > never-fire to prevent data-gap masking"

requirements-completed: [SC-3, SC-6]

# Metrics
duration: 12min
completed: 2026-02-20
---

# Phase 32 Plan 06: Gap Detection and Effectiveness Tracking Summary

**RequirementsAnalyzer derives AcquisitionManifest from 381 AUTO checks (10 sources, 144 section pairs), PipelineGapDetector validates 3-level pipeline coverage (0 CRITICAL gaps), EffectivenessTracker computes fire_rate/skip_rate with N-based confidence from brain_check_runs**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-20T16:16:21Z
- **Completed:** 2026-02-20T16:28:59Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- RequirementsAnalyzer reads all 381 AUTO checks and produces AcquisitionManifest with required_sources (10), required_sections (144 pairs), source_to_checks mapping, and depth/content_type distributions
- PipelineGapDetector compares manifest to pipeline capabilities across 3 levels: source (CRITICAL), field routing (WARNING), and mapper handler (INFO) — confirms 0 CRITICAL gaps in current pipeline
- EffectivenessTracker computes per-check fire_rate, skip_rate, clear_rate from brain_check_runs with always-fire/never-fire/high-skip classification and N-based confidence (LOW/MEDIUM/HIGH)
- brain_effectiveness table populated via update_effectiveness_table() with discrimination_power and 4 flags
- Batch recording function (record_check_runs_batch) ready for pipeline post-ANALYZE integration
- 54 new tests (27 requirements/gap + 27 effectiveness) all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Build RequirementsAnalyzer and PipelineGapDetector** - `8bd4c07` (feat)
2. **Task 2: Build effectiveness tracking from brain_check_runs** - `1a071b5` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/requirements.py` - AcquisitionManifest model and build_manifest() from check declarations
- `src/do_uw/knowledge/gap_detector.py` - PipelineGapDetector with detect_gaps() producing GapReport at 3 severity levels
- `src/do_uw/brain/brain_effectiveness.py` - EffectivenessTracker: compute_effectiveness(), update_effectiveness_table(), record_check_run/batch()
- `tests/knowledge/test_requirements.py` - 12 tests: real checks.json manifest validation + synthetic edge cases
- `tests/knowledge/test_gap_detector.py` - 15 tests: real gap report + synthetic gap scenarios (source/field/mapper)
- `tests/brain/test_brain_effectiveness.py` - 27 tests: compute/classify/update/record with seeded synthetic data

## Decisions Made
- **High-skip priority over never-fire:** A check that's mostly skipped is primarily a data gap (skip_rate > 0.5), not a calibration issue (fire_rate == 0.0). The elif classification chain checks high_skip before never_fire to prevent masking the root cause.
- **Confidence boundaries at N=5 and N=20:** Matches the plan's specification. 5 runs is the minimum for MEDIUM confidence, 20+ for HIGH. Below 5, statistics are unreliable.
- **KnowledgeStore/brain_check_runs coexistence:** Both systems record check results. KnowledgeStore (SQLite) serves the existing knowledge CLI. brain_check_runs (DuckDB) serves brain effectiveness analysis. Pipeline should record to both until convergence.
- **Phase 26+ mapper = field routing coverage:** Checks handled by dedicated mappers (EXEC, NLP, FIN.TEMPORAL/FORENSIC/QUALITY, FWRD) are NOT field routing gaps, even though they lack data_strategy.field_key and FIELD_FOR_CHECK entries.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed effectiveness classification priority**
- **Found during:** Task 2 (effectiveness tracker implementation)
- **Issue:** elif chain checked never-fire before high-skip, causing CHECK_HIGH_SKIP (4/5 skipped, 1 CLEAR) to be classified as never-fire instead of high-skip
- **Fix:** Reordered elif chain: always-fire > high-skip > never-fire
- **Files modified:** src/do_uw/brain/brain_effectiveness.py
- **Verification:** test_high_skip_detection passes correctly
- **Committed in:** 1a071b5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Classification logic corrected. No scope creep.

## Issues Encountered
- Pre-existing test failures in test_ground_truth_coverage.py (TSLA material weakness), test_ground_truth_validation.py (TSLA sector), test_llm_litigation_integration.py, and test_render_outputs.py -- all unrelated to this plan's changes. Documented as out-of-scope per deviation rules.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RequirementsAnalyzer and GapReport models are ready for CLI display in Plan 07 (Brain CLI + backtesting)
- EffectivenessReport is ready for `do-uw knowledge effectiveness` CLI command
- record_check_runs_batch() is ready to wire into pipeline post-ANALYZE step
- All models are Pydantic v2, ready for JSON serialization and Rich table rendering

## Self-Check: PASSED

All 7 files verified on disk. Both task commits (8bd4c07, 1a071b5) found in git log.

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
