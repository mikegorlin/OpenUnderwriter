---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 07
subsystem: cli, knowledge, brain
tags: [typer, rich, duckdb, backtesting, cli, brain]

# Dependency graph
requires:
  - phase: 32-04
    provides: "v6 taxonomy remap in brain.duckdb with brain_checks, brain_taxonomy, brain_backlog tables"
  - phase: 32-05
    provides: "Content-type-aware evaluation dispatch, BrainDBLoader/BrainWriter, brain_check_runs"
  - phase: 32-06
    provides: "RequirementsAnalyzer (AcquisitionManifest), PipelineGapDetector (GapReport), EffectivenessTracker (EffectivenessReport)"
provides:
  - "Brain CLI sub-app with 7 commands (status, gaps, effectiveness, changelog, backlog, export-docs, backtest)"
  - "BacktestRunner for historical state replay via check_engine.execute_checks()"
  - "BacktestComparison for A/B analysis of check results across runs"
  - "Operational brain management without writing code"
affects: [33-living-knowledge, 34-display-presentation, 35-pricing-calibration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CLI sub-app pattern: lazy imports in Typer command functions to avoid import overhead"
    - "Brain state file replay: load AnalysisState from JSON, run checks against ExtractedData"
    - "Patching pattern for lazy imports: patch at defining module, not at consuming module"

key-files:
  created:
    - src/do_uw/cli_brain.py
    - src/do_uw/knowledge/backtest.py
    - tests/test_cli_brain.py
    - tests/knowledge/test_backtest.py
  modified:
    - src/do_uw/cli.py

key-decisions:
  - "Brain CLI uses lazy imports (importing BrainDBLoader/BrainWriter inside function bodies) to avoid loading DuckDB at CLI startup time for unrelated commands"
  - "Backtest uses AnalysisState.model_validate(json.load()) for state deserialization instead of Pipeline.load_state() for clearer error handling on schema drift"
  - "Export-docs outputs to stdout by default (pipe-friendly) with optional --output file path"
  - "Backtest defaults to record=True (storing in brain_check_runs) since the primary use case is tracking effectiveness over time"

patterns-established:
  - "Brain CLI sub-app: 7 commands covering read (status, gaps, effectiveness, changelog, backlog), export (export-docs), and replay (backtest)"
  - "BacktestRunner pattern: load frozen state -> execute current checks -> compare results deterministically"

requirements-completed: [SC-3, SC-5, SC-6]

# Metrics
duration: 16min
completed: 2026-02-20
---

# Phase 32 Plan 07: Brain CLI + Backtesting Summary

**Brain CLI with 7 operational commands (status, gaps, effectiveness, changelog, backlog, export-docs, backtest) and BacktestRunner replaying 381 checks against historical state files**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-20T16:31:14Z
- **Completed:** 2026-02-20T16:47:48Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Brain CLI registered as `do-uw brain` sub-app with 7 Rich-formatted commands covering the complete brain operational surface
- BacktestRunner loads historical state.json files, replays all 381 AUTO checks via execute_checks(), and records results to brain_check_runs with is_backtest=TRUE
- BacktestComparison enables A/B diff of check results: identifies changed, new, and removed checks between runs
- Verified against real AAPL state file: 381 checks executed (6 triggered, 42 clear, 40 skipped, 293 info)
- 28 new tests (17 CLI + 11 backtest), 3,184+ total passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Brain CLI sub-app with 7 commands** - `f3613dd` (feat)
2. **Task 2: Build BacktestRunner for historical state replay** - `47c240d` (feat)

## Files Created/Modified

- `src/do_uw/cli_brain.py` - Typer sub-app with 7 commands: status, gaps, effectiveness, changelog, backlog, export-docs, backtest (633 lines)
- `src/do_uw/knowledge/backtest.py` - BacktestResult, BacktestComparison models, run_backtest(), compare_backtests() (252 lines)
- `src/do_uw/cli.py` - Added brain_app import and registration (2 lines)
- `tests/test_cli_brain.py` - 17 CLI tests with mocked dependencies (429 lines)
- `tests/knowledge/test_backtest.py` - 11 backtest tests including determinism and recording (315 lines)

## Decisions Made

1. **Lazy imports in CLI functions** -- BrainDBLoader, BrainWriter, brain_schema functions are imported inside command function bodies rather than at module level. This avoids loading DuckDB for every CLI invocation (e.g., `do-uw analyze` does not need DuckDB).

2. **State deserialization via AnalysisState.model_validate()** -- Instead of using Pipeline.load_state(), backtest uses direct JSON loading + Pydantic validation. This provides clearer error messages when state files have schema drift (ValidationError with field-level details).

3. **Export-docs stdout default** -- The export-docs command defaults to stdout (pipe-friendly for `do-uw brain export-docs > brain.md`) with an optional `--output` flag for direct file writing.

4. **Record default True** -- Backtest defaults to recording results because the primary use case is effectiveness tracking. Users who just want to inspect use `--no-record`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 32 is now COMPLETE (all 7 plans executed)
- Brain CLI provides complete operational management of the knowledge system
- Backtesting infrastructure is operational and verified against real state files
- All 6 Phase 32 success criteria are achievable:
  - SC-1: Acquisition driven by knowledge (Plans 04-06)
  - SC-2: Extraction guided by hints (Plan 05)
  - SC-3: Pipeline gap detection (Plan 06 + CLI in Plan 07)
  - SC-4: Content-type-aware evaluation (Plan 05)
  - SC-5: Backtesting infrastructure (Plan 07)
  - SC-6: Effectiveness measurement (Plans 06 + 07)

## Self-Check: PASSED

- All 4 created files verified present on disk
- Both commit hashes (f3613dd, 47c240d) verified in git log
- 17 CLI tests + 11 backtest tests = 28 new tests, all passing
- Full suite: 3,184+ passing (4 pre-existing failures in ground truth/integration tests, unrelated)

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
