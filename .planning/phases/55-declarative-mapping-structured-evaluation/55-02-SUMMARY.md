---
phase: 55-declarative-mapping-structured-evaluation
plan: 02
subsystem: analyze
tags: [shadow-evaluation, v2-dispatch, duckdb-logging, signal-engine, declarative-mapper, structured-evaluator]

# Dependency graph
requires:
  - phase: 55-declarative-mapping-structured-evaluation
    plan: 01
    provides: "declarative_mapper.py (map_v2_signal), structured_evaluator.py (evaluate_v2), field_registry_functions.py"
provides:
  - "_evaluate_v2_signal(): V2 dispatch with declarative mapper + structured evaluator + shadow comparison"
  - "_log_shadow_evaluation(): Fire-and-forget DuckDB logging of shadow evaluation results"
  - "brain_shadow_evaluations DDL: DuckDB table for shadow comparison records"
  - "execute_signals() run_id/ticker params for shadow evaluation context"
affects: [55-03-fin-liq-migration, signal-engine-v2-primary-switch, shadow-evaluation-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Shadow evaluation: both V2 and legacy paths run, discrepancies logged, legacy result returned during migration", "Fire-and-forget DuckDB writes with exception catching for pipeline safety", "Case-insensitive threshold_level comparison for cross-evaluator normalization"]

key-files:
  created:
    - tests/stages/analyze/test_shadow_evaluation.py
  modified:
    - src/do_uw/stages/analyze/signal_engine.py
    - src/do_uw/brain/brain_schema.py
    - tests/brain/test_v2_dispatch.py
    - tests/brain/test_brain_schema.py

key-decisions:
  - "Shadow phase returns LEGACY result (not V2) -- V2 is computed for comparison only, Plan 03 switches to V2 for fully-migrated prefixes"
  - "Case-insensitive threshold_level comparison via .lower() normalization (legacy returns lowercase, V2 could return uppercase)"
  - "Fire-and-forget DuckDB logging: entire _log_shadow_evaluation wrapped in try/except, DB errors never crash pipeline"
  - "execute_signals() gains optional run_id/ticker params with empty-string defaults for backward compatibility"

patterns-established:
  - "Shadow evaluation pattern: V2 path runs map_v2_signal+evaluate_v2, legacy path runs evaluate_signal, compare status+level, log to DuckDB, return legacy"
  - "_log_shadow_evaluation uses connect_brain_db() with short-lived connection (open, insert, close)"
  - "discrepancy_detail populated only on mismatch (is_match=False) with V2 and legacy status/level strings"

requirements-completed: [MAP-03, EVAL-04, EVAL-05]

# Metrics
duration: 54min
completed: 2026-03-01
---

# Phase 55 Plan 02: Shadow Evaluation + V2 Signal Engine Wiring Summary

**V2 signals now run declarative mapper + structured evaluator with shadow comparison against legacy path, logging results to DuckDB brain_shadow_evaluations table**

## Performance

- **Duration:** 54 min
- **Started:** 2026-03-01T18:33:51Z
- **Completed:** 2026-03-01T19:27:51Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files created:** 1
- **Files modified:** 4

## Accomplishments

- Replaced Phase 54 `_evaluate_v2_stub` with real `_evaluate_v2_signal` that wires declarative mapper + structured evaluator into the signal engine V2 dispatch path
- Added shadow evaluation that runs both V2 and legacy paths for every V2 signal with an evaluation section, comparing status + threshold_level
- Created `brain_shadow_evaluations` DuckDB table with run_id/signal_id/ticker tracking, is_match flag, and discrepancy_detail
- Fire-and-forget DuckDB logging ensures pipeline never crashes on DB write errors
- 21 new plan-specific tests passing (11 shadow evaluation + 10 V2 dispatch), 1226 suite tests green, zero regressions

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Replace _evaluate_v2_stub with real V2 dispatch + shadow evaluation** - `f15cbaa` (test), `bc92131` (feat)
   - RED: 21 failing tests for shadow comparison, V2 dispatch integration, DuckDB logging, classification metadata
   - GREEN: signal_engine.py V2 dispatch, brain_schema.py shadow DDL, test fixes for kwargs assertions and schema table count

## Files Created/Modified

- `src/do_uw/stages/analyze/signal_engine.py` (579 lines) -- _evaluate_v2_signal(), _log_shadow_evaluation(), updated execute_signals() with run_id/ticker params
- `src/do_uw/brain/brain_schema.py` (520 lines) -- brain_shadow_evaluations DDL + 2 indexes
- `tests/stages/analyze/test_shadow_evaluation.py` (370 lines) -- 11 tests: shadow comparison (4), V2 dispatch integration (3), DuckDB logging (3), classification metadata (1)
- `tests/brain/test_v2_dispatch.py` (175 lines) -- Updated from stub tests to _evaluate_v2_signal tests, added V1 skip + V2 without eval section tests
- `tests/brain/test_brain_schema.py` (233 lines) -- Updated expected table count from 19 to 20

## Decisions Made

1. **Shadow phase returns LEGACY result** -- During the initial shadow phase, `_evaluate_v2_signal` returns the legacy result (not V2). The V2 result is computed for comparison only. Plan 03 will switch to V2 as primary for fully-migrated prefixes once shadow evaluation confirms zero discrepancy.

2. **Case-insensitive threshold_level comparison** -- `v2_level.lower() == legacy_level.lower()` ensures "RED" from legacy matches "red" from V2. This addresses Pitfall 2 from research about case normalization between evaluators.

3. **Fire-and-forget DuckDB logging** -- `_log_shadow_evaluation()` wraps its entire body in try/except. Pipeline stability is paramount; shadow logging is best-effort. Connection uses short-lived pattern (open, insert, close).

4. **Optional run_id/ticker on execute_signals()** -- Added with empty-string defaults so all existing callers work without modification. Backward compatible.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated brain_schema test for 20-table count**
- **Found during:** Task 1 (GREEN phase, full suite verification)
- **Issue:** `test_brain_schema.py::test_all_tables_exist` expected 19 tables but brain_shadow_evaluations made it 20. The idempotency test also checked for count 19.
- **Fix:** Updated expected table list to include `brain_shadow_evaluations` and changed count assertion from 19 to 20.
- **Files modified:** `tests/brain/test_brain_schema.py`
- **Verification:** `uv run pytest tests/brain/test_brain_schema.py -v` -- all 11 tests pass
- **Committed in:** `bc92131` (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix -- schema test needed updating for the new table. No scope creep.

## Issues Encountered

- Test assertions initially used positional args to check `_log_shadow_evaluation` mock calls, but the function uses keyword arguments. Fixed by accessing `call_args[1]` (kwargs dict) instead of `call_args[0]` (positional tuple).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Shadow evaluation infrastructure is ready for FIN.LIQ prefix migration (Plan 55-03)
- `_evaluate_v2_signal` will shadow-compare V2 vs legacy for all migrated signals automatically
- `brain_shadow_evaluations` table will accumulate comparison data for migration confidence tracking
- Signal engine at 579 lines (over 500-line limit); consider splitting shadow eval into separate module in future refactor
- deferred-items.md updated with pre-existing test failures and file size concern

## Self-Check: PASSED

- All 5 files verified present on disk
- Both task commits verified in git log (f15cbaa, bc92131)
- 21 plan-specific tests passing
- 1226 suite tests passing (3 pre-existing failures excluded, 0 regressions from Phase 55-02)

---
*Phase: 55-declarative-mapping-structured-evaluation*
*Completed: 2026-03-01*
