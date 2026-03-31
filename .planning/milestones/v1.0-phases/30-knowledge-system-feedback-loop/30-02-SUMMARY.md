---
phase: 30-knowledge-system-feedback-loop
plan: 02
subsystem: knowledge
tags: [sqlalchemy, sqlite, feedback-loop, check-stats, fire-rate, dead-checks]

# Dependency graph
requires:
  - phase: 30-01
    provides: "Persistent-first KnowledgeStore with idempotent migration"
provides:
  - "CheckRun ORM model for per-check pipeline result recording"
  - "Alembic migration 005 (check_runs table)"
  - "write_check_runs(), get_check_stats(), get_dead_checks() store methods"
  - "ANALYZE stage feedback recording (_record_check_results)"
  - "CLI check-stats and dead-checks commands"
affects: [30-03, 30-04, knowledge-cli, analyze-stage]

# Tech tracking
tech-stack:
  added: []
  patterns: [non-fatal-telemetry, feedback-loop-recording, fire-rate-aggregation]

key-files:
  created:
    - src/do_uw/knowledge/migrations/versions/005_check_runs.py
    - tests/knowledge/test_check_feedback.py
  modified:
    - src/do_uw/knowledge/models.py
    - src/do_uw/knowledge/store.py
    - src/do_uw/knowledge/__init__.py
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/cli_knowledge.py
    - tests/knowledge/test_models.py

key-decisions:
  - "No FK constraint on CheckRun.check_id -- dynamic industry checks may not exist in checks table"
  - "Non-fatal telemetry pattern: _record_check_results wrapped in try/except so feedback failure never breaks pipeline"
  - "Aggregation via GROUP BY check_id, status then Python dict rollup for fire_rate/skip_rate computation"

patterns-established:
  - "Non-fatal telemetry: feedback recording wrapped in try/except, failures logged as warnings"
  - "Batch INSERT for check runs (session.add_all), never upsert -- each run is a fresh snapshot"
  - "Dead check detection: fire_rate == 0.0 across min_runs threshold for deprecation candidates"

# Metrics
duration: 6min
completed: 2026-02-15
---

# Phase 30 Plan 02: Check Feedback Loop Summary

**Per-check feedback loop with CheckRun table, fire/skip rate stats, dead check detection, and ANALYZE integration**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-15T17:24:15Z
- **Completed:** 2026-02-15T17:30:50Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- CheckRun ORM model and Alembic migration 005 create the check_runs feedback table
- Every ANALYZE stage execution now records per-check results (non-fatal telemetry)
- CLI `check-stats` shows fire rates and skip rates per check with sorting and filtering
- CLI `dead-checks` identifies checks that never fire across N runs (deprecation candidates)
- 14 targeted tests covering write, stats aggregation, dead check detection, and multi-run scenarios
- Zero regression across 2890 tests (2 pre-existing failures excluded: TSLA material weakness, CLI network test)

## Task Commits

Each task was committed atomically:

1. **Task 1: CheckRun model, Alembic migration, and store methods** - `2a1d79b` (feat)
2. **Task 2: ANALYZE integration, CLI commands, and feedback tests** - `e772cd2` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/models.py` - Added CheckRun ORM model (no FK, string indexes)
- `src/do_uw/knowledge/store.py` - Added write_check_runs(), get_check_stats(), get_dead_checks()
- `src/do_uw/knowledge/__init__.py` - Exported CheckRun from knowledge package
- `src/do_uw/knowledge/migrations/versions/005_check_runs.py` - Alembic migration creating check_runs table
- `src/do_uw/stages/analyze/__init__.py` - Added _record_check_results() called after check execution
- `src/do_uw/cli_knowledge.py` - Added check-stats and dead-checks CLI commands
- `tests/knowledge/test_check_feedback.py` - 14 tests for feedback loop recording and stats
- `tests/knowledge/test_models.py` - Updated table count assertion (14 -> 15)

## Decisions Made
- No FK constraint on CheckRun.check_id because dynamic industry checks (from playbooks) may not exist in the checks table as persistent rows
- Non-fatal telemetry pattern: _record_check_results is wrapped in try/except so feedback recording failures never break the ANALYZE pipeline
- Aggregation uses GROUP BY then Python dict rollup rather than complex SQL window functions (simpler, SQLite-friendly)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed table count assertion in test_models**
- **Found during:** Task 1
- **Issue:** test_creates_all_model_tables expected 14 tables but CheckRun adds a 15th
- **Fix:** Updated assertion from 14 to 15 with updated comment
- **Files modified:** tests/knowledge/test_models.py
- **Verification:** All 387 knowledge tests pass
- **Committed in:** 2a1d79b (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary assertion update for new table. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Check feedback data will accumulate with each pipeline run
- Plans 03-04 can build on check_runs data for lifecycle management and learning infrastructure
- CLI commands ready for immediate use once pipeline runs generate data
- Pre-existing test failures (TSLA material weakness, CLI network test) are unrelated to this work

## Self-Check: PASSED

- All 8 files verified present on disk
- Both task commits (2a1d79b, e772cd2) verified in git log
- All must_have artifacts confirmed (CheckRun, write_check_runs, check-stats, dead-checks, _record_check_results)

---
*Phase: 30-knowledge-system-feedback-loop*
*Completed: 2026-02-15*
