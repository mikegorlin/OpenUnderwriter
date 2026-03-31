---
phase: 57-closed-learning-loop
plan: 03
subsystem: brain
tags: [lifecycle, state-machine, duckdb, pydantic, cli, rich, strnum]

# Dependency graph
requires:
  - phase: 57-closed-learning-loop
    provides: Calibration engine (Plan 01) and correlation mining (Plan 02)
  - phase: 54-signal-contract-v2
    provides: BrainSignalEntry Pydantic schema with V2 fields
provides:
  - 5-state lifecycle state machine (brain_lifecycle_v2.py)
  - LIFECYCLE_TRANSITION proposal generation to brain_proposals
  - Extended apply-proposal pipeline for all Phase 57 proposal types
  - brain audit --lifecycle CLI flag with Rich table output
  - brain audit --calibrate now includes co-occurrence analysis display
  - Updated brain_signals_active view (includes MONITORING, excludes DEPRECATED/ARCHIVED)
affects: [brain-audit, feedback-approve, brain-apply-proposal]

# Tech tracking
tech-stack:
  added: []
  patterns: [5-state-lifecycle-machine, multi-factor-transition-evaluation, display-helper-extraction]

key-files:
  created:
    - src/do_uw/brain/brain_lifecycle_v2.py
    - tests/brain/test_brain_lifecycle_v2.py
    - src/do_uw/cli_brain_audit_display.py
  modified:
    - src/do_uw/knowledge/calibrate_apply.py
    - src/do_uw/cli_brain_health.py
    - src/do_uw/brain/brain_schema.py
    - src/do_uw/knowledge/feedback_models.py

key-decisions:
  - "Display helpers extracted to cli_brain_audit_display.py for 500-line compliance (cli_brain_health.py was 740+ lines)"
  - "ProposalRecord.proposal_type Literal extended with THRESHOLD_CALIBRATION, CORRELATION_ANNOTATION, LIFECYCLE_TRANSITION"
  - "brain_signals_active view excludes DEPRECATED and ARCHIVED but keeps MONITORING visible in pipeline"
  - "evaluate_transition uses _to_aware_dt helper for defensive datetime conversion from DuckDB"

patterns-established:
  - "Lifecycle evaluation pattern: per-state private evaluators dispatched by main evaluate_transition()"
  - "signal_overrides dict in compute_lifecycle_proposals for testing without BrainLoader"
  - "Display helper extraction: CLI command files stay under 500 lines by splitting display formatting"

requirements-completed: [LEARN-04]

# Metrics
duration: 21min
completed: 2026-03-02
---

# Phase 57 Plan 03: Signal Lifecycle & Apply-Proposal Integration Summary

**5-state lifecycle state machine (INCUBATING->ACTIVE->MONITORING->DEPRECATED->ARCHIVED) with multi-factor transition proposals, unified apply-proposal pipeline for all Phase 57 types, and brain audit --lifecycle CLI**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-02T15:21:45Z
- **Completed:** 2026-03-02T15:42:50Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- brain_lifecycle_v2.py (474 lines) implementing 5-state machine with VALID_TRANSITIONS dict, legacy state mapping, multi-factor evaluate_transition() dispatcher
- 21 TDD tests covering all transition paths, state normalization, proposal generation, and report structure
- calibrate_apply.py extended to handle THRESHOLD_CALIBRATION, CORRELATION_ANNOTATION, LIFECYCLE_TRANSITION proposal types with provenance logging
- brain audit CLI with --lifecycle flag showing state distribution and transition proposals; --calibrate now includes co-occurrence analysis
- brain_signals_active view updated to properly handle new lifecycle states

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain_lifecycle_v2.py with 5-state machine and transition proposal logic**
   - `411ab3c` (test: TDD RED - failing tests for lifecycle machine)
   - `72795a2` (feat: TDD GREEN - implement lifecycle machine)
2. **Task 2: Extend apply-proposal pipeline and brain audit CLI** - `bfc753a` (feat: pipeline + CLI + schema)

_TDD flow: RED tests committed first, then GREEN implementation._

## Files Created/Modified
- `src/do_uw/brain/brain_lifecycle_v2.py` - 5-state lifecycle state machine: LifecycleState enum, VALID_TRANSITIONS, evaluate_transition dispatcher, proposal generation
- `tests/brain/test_brain_lifecycle_v2.py` - 21 test cases with in-memory DuckDB fixtures
- `src/do_uw/cli_brain_audit_display.py` - Extracted display helpers for calibration, correlation, and lifecycle reports
- `src/do_uw/knowledge/calibrate_apply.py` - Extended _compute_yaml_changes for 3 new proposal types + provenance logging
- `src/do_uw/cli_brain_health.py` - Added --lifecycle flag and correlation display in --calibrate section
- `src/do_uw/brain/brain_schema.py` - Updated brain_signals_active view to exclude DEPRECATED and ARCHIVED
- `src/do_uw/knowledge/feedback_models.py` - Extended ProposalRecord.proposal_type Literal with 3 new types

## Decisions Made
- Display helpers extracted to `cli_brain_audit_display.py` because `cli_brain_health.py` was 740+ lines pre-change (over 500-line project limit) and adding more display code would worsen it. After extraction, cli_brain_health.py is 634 lines (still over but better than 903)
- ProposalRecord.proposal_type needed Literal extension to accept new Phase 57 proposal types when reading from DuckDB
- brain_signals_active view keeps MONITORING signals visible in pipeline (they are under observation but still active). DEPRECATED signals are excluded as "clearly broken"
- Used `_to_aware_dt()` helper to consolidate repeated datetime timezone handling in DuckDB query results

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extended ProposalRecord.proposal_type Literal**
- **Found during:** Task 2 (testing _compute_yaml_changes)
- **Issue:** ProposalRecord Pydantic model had Literal["NEW_CHECK", "THRESHOLD_CHANGE", "DEACTIVATION"] -- new proposal types failed validation
- **Fix:** Extended Literal to include THRESHOLD_CALIBRATION, CORRELATION_ANNOTATION, LIFECYCLE_TRANSITION
- **Files modified:** src/do_uw/knowledge/feedback_models.py
- **Verification:** All 3 new proposal types validate correctly
- **Committed in:** bfc753a (part of Task 2 commit)

**2. [Rule 2 - Missing Critical] Extracted display helpers for file length compliance**
- **Found during:** Task 2 (adding display helpers to cli_brain_health.py)
- **Issue:** cli_brain_health.py was 740 lines pre-change, adding calibration/correlation/lifecycle display helpers pushed it to 903 lines (well over 500-line limit)
- **Fix:** Created cli_brain_audit_display.py with all 3 display helper functions, reducing cli_brain_health.py from 903 to 634 lines
- **Files modified:** src/do_uw/cli_brain_health.py, src/do_uw/cli_brain_audit_display.py (new)
- **Verification:** CLI import works, all tests pass
- **Committed in:** bfc753a (part of Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes necessary for correctness. Literal extension required for proposal pipeline; display extraction for project code quality rules. No scope creep.

## Issues Encountered
- Pre-existing test failures (21 total) in enrichment, migration, render coverage, and classification tests -- confirmed pre-existing via comparison with Plan 02 summary (same failures). Not caused by this plan.
- Pre-existing test_brain_framework.py import failure due to `do_uw.brain.legacy` moved to archive/ -- not caused by this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 57 is now COMPLETE (3/3 plans done)
- All LEARN requirements implemented: LEARN-01 (calibration), LEARN-02 (correlation), LEARN-03 (fire rate alerts), LEARN-04 (lifecycle)
- v2.0 Brain-Driven Architecture milestone is complete
- Full learning loop available: brain audit --calibrate shows drift+correlation, brain audit --lifecycle shows transitions, brain apply-proposal handles all types

## Self-Check: PASSED

- [x] src/do_uw/brain/brain_lifecycle_v2.py exists (474 lines)
- [x] tests/brain/test_brain_lifecycle_v2.py exists (21 tests, all pass)
- [x] src/do_uw/cli_brain_audit_display.py exists (258 lines)
- [x] Commit 411ab3c: test(57-03) failing tests
- [x] Commit 72795a2: feat(57-03) lifecycle implementation
- [x] Commit bfc753a: feat(57-03) pipeline + CLI + schema
- [x] 53 Phase 57 tests pass (calibration + correlation + lifecycle)
- [x] 4288 total tests pass (21 pre-existing failures excluded)

---
*Phase: 57-closed-learning-loop*
*Completed: 2026-03-02*
