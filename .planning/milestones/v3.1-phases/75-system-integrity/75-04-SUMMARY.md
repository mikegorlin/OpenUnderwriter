---
phase: 75-system-integrity
plan: 04
subsystem: brain
tags: [calibration, lifecycle, learning-loop, post-pipeline, fire-rate]

requires:
  - phase: 75-01
    provides: "Tier 1 manifest, foundational signals, signal author guide"
provides:
  - "Post-pipeline learning hook (auto-propose calibration + lifecycle changes)"
  - "Fire-rate alert logging after every pipeline run"
  - "7 tests covering proposal generation, exception safety, fire-rate logging"
affects: [brain-cli, pipeline]

tech-stack:
  added: []
  patterns: ["lazy-import safety pattern for optional brain modules in pipeline"]

key-files:
  created:
    - src/do_uw/brain/post_pipeline.py
    - tests/brain/test_post_pipeline.py
    - tests/brain/test_auto_calibration.py
  modified:
    - src/do_uw/pipeline.py

key-decisions:
  - "Lazy import of post_pipeline in pipeline.py to avoid import-time dependency on brain modules"
  - "Fire-rate alerts logged at WARNING level; drift/lifecycle proposals are silent (stored in brain_proposals)"
  - "total_proposals counts only actionable proposals (drift + lifecycle), not fire-rate alerts"

patterns-established:
  - "Post-pipeline hook pattern: try/except with lazy import, debug-level skip logging, never crashes pipeline"

requirements-completed: [SYS-08, SYS-09, SYS-10]

duration: 4min
completed: 2026-03-07
---

# Phase 75 Plan 04: Learning Loop Summary

**Post-pipeline auto-propose hook wiring calibration drift, fire-rate alerts, and lifecycle transitions into every pipeline run**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T05:43:01Z
- **Completed:** 2026-03-07T05:46:37Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created post_pipeline.py module that runs calibration + lifecycle analysis after every pipeline completion
- Wired into pipeline.py with lazy import and full exception safety (learning failures never crash the pipeline)
- Fire-rate alerts logged at WARNING level with signal ID, rate, and recommended action
- All proposals stored in brain_proposals table with PENDING status for CLI review -- never auto-applied
- 7 tests verifying: dict structure, exception safety, fire-rate logging, no-auto-apply, drift proposals, no-consensus-no-proposal, lifecycle deprecation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create post-pipeline learning module + wire into pipeline** - `d083017` (feat)
2. **Task 2: Create tests for post-pipeline learning and auto-calibration** - `40926fb` (test)

## Files Created/Modified
- `src/do_uw/brain/post_pipeline.py` - Post-pipeline learning hook (92 lines)
- `src/do_uw/pipeline.py` - Added lazy import call to post_pipeline after stage completion
- `tests/brain/test_post_pipeline.py` - 4 tests: dict structure, exception safety, fire-rate logging, no-auto-apply
- `tests/brain/test_auto_calibration.py` - 3 tests: drift consensus, no-proposal-without-consensus, lifecycle deprecation

## Decisions Made
- Lazy import of post_pipeline in pipeline.py avoids import-time dependency on brain modules (duckdb, brain_calibration, etc.)
- Fire-rate alerts logged at WARNING (actionable), while skip/failure uses debug level (non-critical)
- total_proposals counts drift + lifecycle only (fire-rate alerts are informational logs, not stored proposals)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mock patch targets in tests**
- **Found during:** Task 2 (test creation)
- **Issue:** post_pipeline.py uses lazy imports inside the function body, so `do_uw.brain.post_pipeline.get_brain_db_path` does not exist as a module attribute
- **Fix:** Changed patch targets to source modules (`do_uw.brain.brain_schema.get_brain_db_path`, `do_uw.brain.brain_calibration.compute_calibration_report`, etc.)
- **Files modified:** tests/brain/test_post_pipeline.py
- **Verification:** All 7 tests pass
- **Committed in:** 40926fb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary fix for test correctness when patching lazy-imported functions.

## Issues Encountered
None beyond the mock patch target fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Learning loop now runs automatically after every pipeline completion
- Proposals accumulate in brain_proposals table for `brain apply-proposal` CLI review
- Ready for Phase 75-05 (final plan in system integrity phase)

---
*Phase: 75-system-integrity*
*Completed: 2026-03-07*
