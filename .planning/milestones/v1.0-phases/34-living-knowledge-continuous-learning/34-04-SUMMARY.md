---
phase: 34-living-knowledge-continuous-learning
plan: 04
subsystem: calibration
tags: [duckdb, typer, cli, calibration, git-audit, impact-simulation, backtest]

# Dependency graph
requires:
  - phase: 34-living-knowledge-continuous-learning
    plan: 02
    provides: "LLM ingestion pipeline with brain_proposals table, INCUBATING check insertion"
  - phase: 34-living-knowledge-continuous-learning
    plan: 03
    provides: "Feedback recording with mark_feedback_applied, auto-proposal generation"
provides:
  - "preview_calibration() shows pending proposals with field-level diffs and impact simulation"
  - "apply_calibration() commits approved proposals via BrainWriter with git audit trail"
  - "Impact simulation via execute_checks directly against cached state files"
  - "do-uw calibrate preview/apply/show CLI commands"
  - "Git audit trail with structured commit messages for all calibration changes"
  - "Dirty working tree detection prevents accidental brain/ changes"
affects: [34-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [subprocess git operations with structured commit messages, in-memory check modification for impact simulation]

key-files:
  created:
    - src/do_uw/knowledge/calibrate.py
    - tests/knowledge/test_calibrate.py
  modified:
    - src/do_uw/cli_calibrate.py

key-decisions:
  - "Impact simulation calls execute_checks directly (not run_backtest which has no check override parameter)"
  - "BrainWriter connection reuse via writer._conn = conn pattern (consistent with feedback.py)"
  - "_apply_proposals_to_checks operates on deep copy of checks list for safe in-memory modification"
  - "Git commit stages specific files only (never git add -A) -- brain/checks.json and brain/brain.duckdb"

patterns-established:
  - "Calibration workflow: preview (read-only) -> apply (with confirmation) -> git commit (with audit trail)"
  - "_NoCloseConn wrapper pattern reused from test_feedback.py for CLI tests with in-memory DuckDB"

requirements-completed: [ARCH-09, SECT7-06, SECT7-07, SECT7-11]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 34 Plan 04: Calibration Workflow Summary

**Human-in-the-loop calibration with preview/impact simulation, apply with git audit trail, and backtest against cached state files via execute_checks**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T05:23:42Z
- **Completed:** 2026-02-21T05:29:08Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Built calibration module (calibrate.py, 500 lines) with preview, apply, and impact simulation
- Extended CLI with 3 new commands (preview, apply, show) alongside existing run/report/enrich
- Impact simulation runs execute_checks directly against cached state files with current vs proposed checks
- All 15 tests pass covering proposals, preview, apply (new/threshold/deactivation), git audit, claims correlation, CLI

## Task Commits

Each task was committed atomically:

1. **Task 1: Build calibration impact simulation and git audit module** - `a193796` (feat)
2. **Task 2: Extend calibrate CLI and add tests** - `de78559` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/calibrate.py` - CalibrationPreview/ApplyResult models, preview_calibration, apply_calibration, impact simulation, git audit (500 lines)
- `src/do_uw/cli_calibrate.py` - Added preview, apply, show commands to calibrate_app (extended from 216 to 430 lines)
- `tests/knowledge/test_calibrate.py` - 15 tests for preview, apply, git, CLI (420 lines)

## Decisions Made
- Impact simulation calls execute_checks directly rather than run_backtest -- run_backtest always loads checks from brain_checks_active with no override parameter, so we load checks once, apply proposals in-memory, and run both current/proposed through execute_checks
- BrainWriter connection reuse via `writer._conn = conn` (same pattern as feedback.py) avoids opening a second DuckDB connection
- Deep copy of checks list for _apply_proposals_to_checks prevents mutation of the original checks during simulation
- Git commit stages only brain/checks.json and brain/brain.duckdb -- never uses `git add -A`
- _NoCloseConn wrapper pattern reused from test_feedback.py for CLI tests with in-memory DuckDB

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Calibration workflow complete for Plan 05 (batch processing and scheduled learning)
- Preview/apply/show commands ready for underwriter use
- Impact simulation infrastructure supports batch comparison against historical state files

## Self-Check: PASSED

All files exist, all commits verified:
- FOUND: src/do_uw/knowledge/calibrate.py
- FOUND: tests/knowledge/test_calibrate.py
- FOUND: src/do_uw/cli_calibrate.py
- FOUND: a193796 (Task 1)
- FOUND: de78559 (Task 2)

---
*Phase: 34-living-knowledge-continuous-learning*
*Completed: 2026-02-21*
