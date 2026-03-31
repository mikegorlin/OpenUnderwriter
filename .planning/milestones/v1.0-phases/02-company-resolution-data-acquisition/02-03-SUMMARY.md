---
phase: 02-company-resolution-data-acquisition
plan: 03
subsystem: acquire-orchestration
tags: [acquire, orchestrator, gates, cli, pipeline-config, search-budget]
dependency-graph:
  requires: [02-01, 02-02]
  provides: [acquire-stage, acquisition-orchestrator, pipeline-config]
  affects: [03-01]
tech-stack:
  added: []
  patterns: [orchestrator-pattern, gate-retry, blind-spot-sweep, pipeline-config-passthrough]
key-files:
  created:
    - src/do_uw/stages/acquire/orchestrator.py
    - tests/test_acquire.py
  modified:
    - src/do_uw/stages/acquire/__init__.py
    - src/do_uw/models/state.py
    - src/do_uw/cli.py
    - src/do_uw/pipeline.py
    - tests/test_pipeline.py
    - tests/test_cli.py
decisions:
  - id: LAMBDA_DEFAULT_FACTORY
    decision: "Used lambda factory for gate_results field in AcquiredData"
    rationale: "Pyright strict mode infers bare `list` as `list[Unknown]`; lambda: [] is typed as list[dict[str, Any]]"
  - id: ORCHESTRATOR_METHOD_INJECTION
    decision: "Orchestrator creates client instances internally, testable via class-level mocking"
    rationale: "Simpler than constructor DI for 4 clients; mocked at class level in tests"
metrics:
  duration: 13m 45s
  completed: 2026-02-07
---

# Phase 2 Plan 3: ACQUIRE Stage Orchestrator Summary

Acquisition orchestrator coordinating 5 data clients (SEC, market, litigation, news, web search) in 4 phases (blind spot pre -> structured -> blind spot post -> gates), with HARD gate retry, SOFT gate warnings, CLI --search-budget flag, and pipeline config passthrough.

## What Was Built

### AcquisitionOrchestrator (`src/do_uw/stages/acquire/orchestrator.py`, 307 lines)
- 4-phase acquisition flow: Phase A (pre-acquisition blind spot sweep) -> Phase B (structured data from 4 clients) -> Phase C (post-acquisition blind spot sweep) -> Phase D (gate checking)
- Each client wrapped in try/except with metadata recording (timestamp, duration, success/error)
- Gate checking: evaluates all 6 gates (4 HARD, 2 SOFT) after acquisition
- HARD gate retry: on failure, sleeps 2 seconds, retries the specific client once, re-checks gates
- If HARD gate still fails after retry: raises DataAcquisitionError with descriptive message
- SOFT gate failures logged as warnings, pipeline continues
- WebSearchClient with pluggable search_fn (no-op by default, real MCP function injectable)
- Clear logging when search returns empty due to no search function vs no results found

### AcquiredData Metadata Fields (`src/do_uw/models/state.py`)
- `acquisition_metadata: dict[str, Any]` -- per-source timestamps, confidence, tier, errors
- `gate_results: list[dict[str, Any]]` -- gate pass/fail results
- `search_budget_used: int` -- Brave Search budget consumed
- `blind_spot_results: dict[str, Any]` -- pre/post structured discovery results
- `regulatory_data: dict[str, Any]` -- regulatory data placeholder

### AcquireStage (`src/do_uw/stages/acquire/__init__.py`, 77 lines)
- Replaces stub with real orchestrator delegation
- `validate_input`: checks resolve COMPLETED, company not None, CIK not None
- `run`: creates AnalysisCache, creates AcquisitionOrchestrator, calls orchestrator.run(), assigns state.acquired_data
- Proper error handling: marks stage failed on exception, always closes cache

### Pipeline Config Passthrough (`src/do_uw/pipeline.py`)
- `Pipeline.__init__` accepts `pipeline_config: dict[str, Any] | None`
- `_build_default_stages(config)` reads `config.get("search_budget", 50)` and passes to AcquireStage

### CLI --search-budget (`src/do_uw/cli.py`)
- `--search-budget INTEGER` option on `analyze` command (default 50)
- Passed through to Pipeline via `pipeline_config={"search_budget": search_budget}`

## Tests Written

9 new tests in `tests/test_acquire.py`:

| Test Class | Count | Coverage |
|---|---|---|
| TestAcquireStageValidation | 4 | No company, no CIK, resolve not complete, valid state |
| TestAcquireStageRun | 1 | Full run with mocked clients populates state |
| TestGateFailure | 2 | HARD gate retry then fail (assert 2 calls), retry succeeds |
| TestSoftGateWarning | 1 | Missing litigation+news SOFT gates, no exception |
| TestCacheReuse | 1 | Second run uses cache (mock_cache.get called) |

All tests use `unittest.mock.patch` -- zero real network calls.

**Updated existing tests:**
- `tests/test_pipeline.py`: Added AcquisitionOrchestrator.run mock and AnalysisCache mock to 4 pipeline tests that run full pipeline
- `tests/test_cli.py`: Added same mocks to _patch_network() (6 context managers instead of 4)

**Total tests: 105 (96 existing + 9 new)**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pipeline/CLI tests making real network calls through acquire stage**
- **Found during:** Task 2 verification
- **Issue:** After replacing AcquireStage stub with real implementation, pipeline tests (test_pipeline_runs_all_stages, test_pipeline_callbacks_fire, test_resume_skips_completed_stages, test_state_saved_after_each_stage) and CLI tests (all 4) started making real SEC API and yfinance calls through the acquire stage, causing 10x slowdown (10s vs 1s) and test flakiness.
- **Fix:** Added `@patch("do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run")` and `@patch("do_uw.stages.acquire.AnalysisCache")` mocks to all affected tests. Created `_mock_orchestrator_run()` helper that returns AcquiredData passing all gates.
- **Files modified:** tests/test_pipeline.py, tests/test_cli.py
- **Commit:** 0569cea

**2. [Rule 3 - Blocking] Pyright strict mode rejects bare `list` default_factory**
- **Found during:** Task 1 verification
- **Issue:** `gate_results: list[dict[str, Any]] = Field(default_factory=list)` inferred as `list[Unknown]` by pyright strict.
- **Fix:** Changed to `default_factory=lambda: []` which infers correctly.
- **Files modified:** src/do_uw/models/state.py
- **Commit:** 36feddf

## Decisions Made

| ID | Decision | Rationale |
|---|---|---|
| LAMBDA_DEFAULT_FACTORY | lambda: [] for gate_results | Pyright strict infers bare list as list[Unknown] |
| ORCHESTRATOR_METHOD_INJECTION | Orchestrator creates clients internally | Simpler than constructor DI; testable via class-level mock |

## Next Phase Readiness

### Phase 2 Complete
All 3 plans executed:
- 02-01: Ticker resolution + SEC identity (RESOLVE stage)
- 02-02: Data acquisition clients (SEC, market, litigation, news, web search)
- 02-03: Acquisition orchestrator + ACQUIRE stage wiring

### Ready for Phase 3 (Data Extraction)
- `state.acquired_data.filings` populated with raw filing metadata
- `state.acquired_data.market_data` populated with yfinance data
- `state.acquired_data.litigation_data` populated with web + SEC references
- `state.acquired_data.web_search_results` populated with news data
- `state.acquired_data.blind_spot_results` populated with pre/post discovery
- All data is RAW -- Phase 3 EXTRACT stage will parse and structure it

### No Blockers for Phase 3
- 105 tests passing
- All lint and type checks clean
- No file exceeds 500 lines
