# Phase 4 Plan 11: Phase 4 Sub-Orchestrator Test Coverage Summary

**One-liner:** Mock patches for run_market_extractors and run_governance_extractors across all integration tests, plus 7 new tests verifying sub-orchestrator wiring and failure handling

## Metadata

- **Phase:** 4
- **Plan:** 11
- **Duration:** 5m 31s
- **Completed:** 2026-02-08
- **Subsystem:** tests
- **Tags:** testing, mocks, sub-orchestrator, SECT4, SECT5, integration

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Update test_extract_stage.py with Phase 4 mocks | 83b6e64 | tests/test_extract_stage.py |
| 2 | Update test_pipeline.py and test_cli.py with Phase 4 mocks | ffdbdff | tests/test_pipeline.py, tests/test_cli.py |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Patch at `do_uw.stages.extract.run_market_extractors` (not `extract_market.run_market_extractors`) | `__init__.py` imports the function into its own namespace, so the patch target must match where the reference is used |
| Sub-orchestrator-level mocking for pipeline/CLI tests | Minimizes patches needed (2 instead of 13 individual extractors) while providing full isolation |
| ExitStack pattern for new failure tests | Consistent with established pattern from 03-07; cleaner than nesting 4+ context managers |
| Return default empty models from mocks (`MarketSignals()`, `GovernanceData()`) | Matches sub-orchestrator behavior on failure; avoids needing detailed mock data in integration tests |

## Implementation Details

### test_extract_stage.py (7 new tests, 7 existing updated)
- Added `@patch` decorators for `run_market_extractors` and `run_governance_extractors` to all 7 existing tests that call `stage.run()`
- 6 new test classes with 7 test methods:
  - `TestExtractStageCallsMarketSubOrchestrator` -- verifies state/reports args and result storage
  - `TestExtractStageCallsGovernanceSubOrchestrator` -- verifies state/reports args and result storage
  - `TestExtractStageHandlesSubOrchestratorFailure` -- 2 tests: market and governance failures propagate as FAILED
  - `TestMarketSubOrchestratorCallsAllExtractors` -- verifies all 7 market wrapper functions called
  - `TestGovernanceSubOrchestratorCallsAllExtractors` -- verifies all 6 governance wrapper functions called
  - `TestGovernanceNarrativeGenerated` -- verifies governance_summary is SourcedValue[str] with LOW confidence

### test_pipeline.py (4 tests updated)
- Added 2 `@patch` decorators to all 4 full-pipeline tests (`test_pipeline_runs_all_stages`, `test_pipeline_callbacks_fire`, `test_resume_skips_completed_stages`, `test_state_saved_after_each_stage`)
- Each test method receives 2 additional mock parameters

### test_cli.py (5 tests covered via helper update)
- Added 2 patches to `_apply_network_patches` ExitStack helper, automatically covering all 5 CLI tests
- Import additions: `GovernanceData`, `MarketSignals`

## Test Results

- **Total tests:** 476 (was 469, +7 new)
- **Passing:** 476/476
- **Lint errors:** 0
- **Regression:** None

## Deviations from Plan

None -- plan executed exactly as written.

## Files Modified

- `tests/test_extract_stage.py` (+436 lines)
- `tests/test_pipeline.py` (+60 lines)
- `tests/test_cli.py` (+15 lines)

## Verification

- `uv run python -m pytest tests/test_extract_stage.py -v` -- 17/17 passed
- `uv run python -m pytest tests/test_pipeline.py -v` -- 9/9 passed
- `uv run python -m pytest tests/test_cli.py -v` -- 5/5 passed
- `uv run python -m pytest tests/ -v` -- 476/476 passed
- `uv run ruff check tests/` -- All checks passed

## Next Phase Readiness

Phase 4 is now complete (11/11 plans). All market and governance extractors are implemented, wired into ExtractStage via sub-orchestrators, and thoroughly tested. Phase 5 (Litigation & Regulatory) can proceed.
