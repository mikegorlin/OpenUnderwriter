---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 08
subsystem: acquire
tags: [brain, duckdb, acquisition, manifest, gap-closure, pipeline]

# Dependency graph
requires:
  - phase: 32-knowledge-driven-acquisition-analysis-pipeline (plans 01-07)
    provides: BrainDBLoader, AcquisitionManifest, build_manifest, gap_detector
provides:
  - Brain-aware ACQUIRE stage that reads check declarations at runtime
  - Post-acquisition coverage validation (brain_coverage in metadata)
  - _determine_acquired_sources mapping from AcquiredData to source type names
affects: [pipeline integration, gap detection, brain CLI diagnostics]

# Tech tracking
tech-stack:
  added: []
  patterns: [brain-derived requirements at acquisition startup, post-acquisition coverage validation]

key-files:
  created:
    - src/do_uw/stages/acquire/brain_requirements.py
    - tests/stages/acquire/test_brain_requirements.py
    - tests/stages/acquire/test_orchestrator_brain.py
    - tests/stages/acquire/__init__.py (test directory)
  modified:
    - src/do_uw/stages/acquire/orchestrator.py
    - src/do_uw/stages/acquire/__init__.py

key-decisions:
  - "Lazy BrainDBLoader import inside derive_brain_requirements() to avoid circular imports and hard DuckDB dependency"
  - "brain_manifest=None default on AcquisitionOrchestrator for full backward compatibility"
  - "_determine_acquired_sources uses same source names as gap_detector.ACQUIRED_SOURCES for consistent coverage comparison"
  - "FPI filing types (20-F, 6-K) mapped to domestic equivalents (SEC_10K, SEC_10Q) in source determination"

patterns-established:
  - "Brain-to-pipeline adapter pattern: thin adapter module reads brain at stage entry, passes manifest through stage"
  - "Graceful degradation: all brain calls wrapped in try/except, brain failure never blocks pipeline"

requirements-completed: [SC-1]

# Metrics
duration: 5min
completed: 2026-02-20
---

# Phase 32 Plan 08: Brain-Aware ACQUIRE Stage Summary

**ACQUIRE stage now reads check declarations from brain.duckdb at startup, derives required sources/sections via AcquisitionManifest, and validates post-acquisition coverage (SC-1 gap closure)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-20T18:28:28Z
- **Completed:** 2026-02-20T18:33:29Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created brain_requirements.py adapter: derive_brain_requirements(), validate_acquisition_coverage(), log_section_requirements()
- Wired brain manifest into AcquisitionOrchestrator with brain-driven logging at start and coverage validation at end
- Built _determine_acquired_sources() mapping AcquiredData fields to the 10 source type names used by gap_detector
- AcquireStage.run() now derives brain requirements before creating orchestrator, with full graceful fallback
- 27 new tests (11 brain_requirements + 16 orchestrator brain), all 79 acquire tests pass, zero type errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain_requirements module for ACQUIRE stage** - `8a69c78` (feat)
2. **Task 2: Wire brain requirements into AcquisitionOrchestrator** - `ec253b5` (feat)

## Files Created/Modified
- `src/do_uw/stages/acquire/brain_requirements.py` - Brain-to-acquisition adapter: derives manifest from BrainDBLoader checks
- `src/do_uw/stages/acquire/orchestrator.py` - Added brain_manifest parameter, pre-run logging, post-run coverage validation, _determine_acquired_sources helper
- `src/do_uw/stages/acquire/__init__.py` - AcquireStage.run() calls derive_brain_requirements() before orchestrator creation
- `tests/stages/acquire/test_brain_requirements.py` - 11 tests: validation, logging, graceful degradation
- `tests/stages/acquire/test_orchestrator_brain.py` - 16 tests: source mapping, orchestrator integration, coverage metadata

## Decisions Made
- Lazy BrainDBLoader import inside function body to avoid circular imports -- brain_requirements module has no top-level DuckDB dependency
- brain_manifest=None default ensures zero breaking changes to existing orchestrator callers
- FPI filing types (20-F, 6-K) mapped to domestic equivalents so coverage validation works regardless of whether company is domestic or foreign

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Initial test mocking approach used `patch("do_uw.stages.acquire.brain_requirements.BrainDBLoader")` which failed because BrainDBLoader is imported lazily (not at module level). Fixed by patching at source `do_uw.brain.brain_loader.BrainDBLoader` instead.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ACQUIRE stage is now brain-aware; future plans can enhance the manifest-driven acquisition (e.g., selective section fetching)
- brain_coverage metadata is available for pipeline diagnostics and gap detection reporting
- Ready for Plan 09 (if it exists) or phase completion

## Self-Check: PASSED

- All 5 created/modified files verified on disk
- Both task commits (8a69c78, ec253b5) verified in git log
- 79/79 acquire tests pass
- 0 pyright errors across src/do_uw/stages/acquire/

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
