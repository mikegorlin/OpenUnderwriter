---
phase: 51-feedback-loop
plan: 03
subsystem: knowledge
tags: [ruamel-yaml, calibration, yaml-writeback, feedback-loop, brain-build]

# Dependency graph
requires:
  - phase: 51-02
    provides: "Feedback processing pipeline and proposal generation"
provides:
  - "brain apply-proposal CLI command for YAML write-back"
  - "yaml_writer.py module for round-trip YAML editing with comment preservation"
  - "calibrate_apply.py with apply_single_proposal() for YAML-based calibration"
  - "Complete feedback loop: react -> aggregate -> propose -> apply -> rebuild"
affects: [brain-build, calibration, feedback]

# Tech tracking
tech-stack:
  added: [ruamel.yaml]
  patterns: [yaml-round-trip-editing, git-revert-on-failure, one-proposal-per-commit]

key-files:
  created:
    - src/do_uw/knowledge/yaml_writer.py
    - src/do_uw/knowledge/calibrate_apply.py
    - src/do_uw/cli_brain_apply.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/do_uw/cli_brain.py
    - src/do_uw/knowledge/calibrate.py
    - src/do_uw/knowledge/calibrate_impact.py

key-decisions:
  - "Split calibrate_apply.py from calibrate.py for 500-line compliance"
  - "YAML write-back is separate path from legacy DuckDB-only apply (backward compat preserved)"
  - "verify_clean_brain_tree checks signals/ dir specifically, not entire brain/ dir"

patterns-established:
  - "YAML write-back pattern: modify YAML -> brain build -> validate -> git commit -> mark APPLIED"
  - "Auto-revert on failure: if brain build fails after YAML edit, git checkout reverts the file"
  - "One proposal per invocation: each gets own validation and git commit"

requirements-completed: [FEED-01]

# Metrics
duration: 6min
completed: 2026-02-28
---

# Phase 51 Plan 03: Apply Proposal YAML Write-Back Summary

**brain apply-proposal command closing the feedback loop with ruamel.yaml round-trip YAML editing, brain build validation, auto-revert on failure, and structured git commits**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-28T03:26:28Z
- **Completed:** 2026-02-28T03:32:37Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added ruamel.yaml dependency for comment-preserving YAML round-trip editing
- Created yaml_writer.py with signal YAML index (400 signals across 36 files), modify_signal_in_yaml(), and revert_yaml_change()
- Implemented apply_single_proposal() that writes to YAML source of truth, runs brain build, validates signal count, and creates structured git commits
- Added `brain apply-proposal <id>` CLI command with --yes flag for scripted usage
- Complete feedback loop: record reaction -> aggregate -> generate proposal -> apply to YAML -> rebuild DuckDB -> commit

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ruamel.yaml dependency and create yaml_writer.py module** - `f4fbd5e` (feat)
2. **Task 2: Rewrite apply_calibration for YAML write-back and add brain apply-proposal CLI command** - `53f013f` (feat)

## Files Created/Modified
- `pyproject.toml` - Added ruamel.yaml dependency
- `uv.lock` - Updated lockfile with ruamel-yaml==0.19.1
- `src/do_uw/knowledge/yaml_writer.py` - Round-trip YAML editing module (build_signal_yaml_index, modify_signal_in_yaml, revert_yaml_change)
- `src/do_uw/knowledge/calibrate_apply.py` - YAML-based apply_single_proposal() with brain build validation and git commit
- `src/do_uw/knowledge/calibrate.py` - Re-exports apply_single_proposal for backward compat
- `src/do_uw/knowledge/calibrate_impact.py` - Updated verify_clean_brain_tree to check signals/ dir
- `src/do_uw/cli_brain_apply.py` - CLI command: brain apply-proposal <id> [--yes]
- `src/do_uw/cli_brain.py` - Registered cli_brain_apply import

## Decisions Made
- Split apply_single_proposal into calibrate_apply.py to keep calibrate.py under 500 lines (Anti-Context-Rot rule)
- Preserved existing apply_calibration() for backward compat -- the old DuckDB-only path still works via `calibrate apply`
- Updated verify_clean_brain_tree to check `src/do_uw/brain/signals/` specifically rather than entire brain/ dir (brain.duckdb can have uncommitted changes from pipeline runs)
- YAML header comment updated from "DO NOT EDIT" to "Brain signal definitions -- source of truth for brain build" on first calibration edit

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] File length compliance split**
- **Found during:** Task 2 (adding apply_single_proposal to calibrate.py)
- **Issue:** calibrate.py would reach 627 lines with the new function, exceeding the 500-line Anti-Context-Rot rule
- **Fix:** Created calibrate_apply.py (318 lines) with apply_single_proposal and helpers; re-exported from calibrate.py
- **Files modified:** src/do_uw/knowledge/calibrate.py, src/do_uw/knowledge/calibrate_apply.py
- **Verification:** Both files under 500 lines (336 + 318)
- **Committed in:** 53f013f (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** File split follows established pattern (cli_brain_ext.py, cli_feedback_process.py). No scope creep.

## Issues Encountered
- Plan verification script used approximate signal IDs (FIN.LIQ.current_ratio, LIT.SCA.securities_class_action) that don't match actual signal IDs (FIN.LIQ.position, LIT.SCA.active) -- verified index completeness with correct IDs instead (400 signals >= 380 required)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 51 feedback loop is complete: react -> aggregate -> propose -> apply -> rebuild
- FEED-01 requirement satisfied end-to-end
- All 26 existing calibrate + feedback tests pass
- Ready for Phase 52 or next milestone

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 51-feedback-loop*
*Completed: 2026-02-28*
