---
phase: 34-living-knowledge-continuous-learning
plan: 03
subsystem: feedback
tags: [duckdb, typer, cli, feedback, proposals, incubating]

# Dependency graph
requires:
  - phase: 34-living-knowledge-continuous-learning
    plan: 01
    provides: "brain_feedback and brain_proposals tables, FeedbackEntry/ProposalRecord/FeedbackSummary Pydantic models"
provides:
  - "record_feedback() inserts into brain_feedback with auto-proposal for MISSING_COVERAGE"
  - "get_feedback_summary() returns dashboard-ready counts by type/status"
  - "get_feedback_for_check() retrieves feedback for a specific check_id"
  - "mark_feedback_applied() marks feedback as APPLIED after calibration"
  - "do-uw feedback add/summary/list CLI commands"
  - "Auto-proposed INCUBATING checks from MISSING_COVERAGE feedback"
affects: [34-04, 34-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [NoCloseConn wrapper for DuckDB test isolation, public row_to_feedback_entry for cross-module use]

key-files:
  created:
    - src/do_uw/knowledge/feedback.py
    - src/do_uw/cli_feedback.py
    - tests/knowledge/test_feedback.py
  modified:
    - src/do_uw/cli.py

key-decisions:
  - "CLI uses explicit 'add' subcommand instead of callback pattern (Typer limitation: positional args + subcommands conflict in callback)"
  - "row_to_feedback_entry made public for cross-module use by cli_feedback.py"
  - "BrainWriter connection reuse via writer._conn = conn for auto-proposal (avoids opening second DB connection)"
  - "cast(dict[str, Any]) for json.loads return type in _parse_json_field (pyright strict compliance)"

patterns-established:
  - "NoCloseConn wrapper in tests: prevents CLI conn.close() from killing test connection (DuckDB close is read-only)"
  - "Auto-proposal pattern: MISSING_COVERAGE feedback -> INCUBATING check + brain_proposals row"

requirements-completed: [SECT7-06, SECT7-07, SECT7-11]

# Metrics
duration: 8min
completed: 2026-02-21
---

# Phase 34 Plan 03: Underwriter Feedback System Summary

**CLI feedback commands (add/summary/list) with auto-proposal generation for missing coverage gaps, named reviewer tracking, and run_id traceability**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-21T05:12:59Z
- **Completed:** 2026-02-21T05:21:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Built feedback recording module with record, query, summary, and auto-proposal functions (425 lines)
- Created CLI with 3 subcommands: add (record), summary (dashboard), list (filtered display)
- MISSING_COVERAGE feedback auto-generates INCUBATING check proposals invisible to pipeline
- All 11 tests pass covering accuracy/threshold/missing_coverage feedback, summary counts, mark_applied, and CLI integration
- Pyright strict clean on all new modules

## Task Commits

Each task was committed atomically:

1. **Task 1: Build feedback recording and querying module** - `615fdc8` (feat)
2. **Task 2: Build CLI feedback commands and tests** - `4b96e3e` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/feedback.py` - Feedback recording, querying, auto-proposal generation (425 lines)
- `src/do_uw/cli_feedback.py` - CLI sub-app with add/summary/list commands (310 lines)
- `src/do_uw/cli.py` - Registered feedback_app alongside existing sub-apps
- `tests/knowledge/test_feedback.py` - 11 tests for feedback module and CLI

## Decisions Made
- Used explicit `add` subcommand instead of Typer callback pattern -- Typer's `invoke_without_command=True` callback with positional arguments creates conflicts when subcommands exist (AAPL treated as subcommand name, --note treated as unrecognized command)
- Made `row_to_feedback_entry` public (was `_row_to_feedback_entry`) for cross-module use by CLI list command
- BrainWriter connection reused via `writer._conn = conn` in auto-proposal to avoid opening a second DuckDB connection to the same in-memory DB
- `cast(dict[str, Any])` for json.loads and isinstance dict narrowing under pyright strict

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Typer callback pattern incompatible with positional args + subcommands**
- **Found during:** Task 2 (CLI feedback commands)
- **Issue:** Plan specified `@feedback_app.callback(invoke_without_command=True)` with ticker as positional argument, but Typer treats the ticker as a subcommand name when `summary`/`list` subcommands exist
- **Fix:** Restructured to use explicit `add` subcommand: `do-uw feedback add AAPL --note ...` instead of `do-uw feedback AAPL --note ...`
- **Files modified:** src/do_uw/cli_feedback.py
- **Verification:** CLI invocation works correctly, all 11 tests pass
- **Committed in:** 4b96e3e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor CLI invocation change (add subcommand vs callback default). All functionality preserved.

## Issues Encountered
- DuckDB connection `close` attribute is read-only, preventing simple monkey-patching in tests. Solved with `_NoCloseConn` wrapper class that delegates all methods except close.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Feedback recording pipeline complete for Plans 04-05 (calibration and batch processing)
- mark_feedback_applied() ready for calibration workflow to mark feedback as addressed
- Auto-proposal path establishes INCUBATING check creation for promotion workflow

---
*Phase: 34-living-knowledge-continuous-learning*
*Completed: 2026-02-21*
