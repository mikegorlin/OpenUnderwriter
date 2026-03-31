---
phase: 51-feedback-loop
plan: 02
subsystem: knowledge
tags: [feedback, aggregation, proposals, duckdb, cli, calibration]

# Dependency graph
requires:
  - phase: 51-01
    provides: "feedback capture layer (record_reaction, get_pending_reactions, FeedbackReaction model, brain_feedback reaction columns)"
provides:
  - "feedback_process.py: aggregate_reactions(), generate_proposals(), compute_fire_rate_impact(), compute_score_impact(), process_pending_reactions()"
  - "CLI: feedback process (batch aggregate), feedback show (proposal detail)"
  - "Proposals inserted into brain_proposals with source_type=FEEDBACK, backtest_results with fire rate and score impact"
affects: [51-03-apply-proposal]

# Tech tracking
tech-stack:
  added: []
  patterns: ["consensus aggregation with 60% threshold", "fire rate impact from brain_signal_runs", "CLI extension via separate file import"]

key-files:
  created:
    - src/do_uw/knowledge/feedback_process.py
    - src/do_uw/cli_feedback_process.py
  modified:
    - src/do_uw/cli_feedback.py

key-decisions:
  - "Split CLI commands into cli_feedback_process.py to stay under 500-line limit (same pattern as cli_brain_ext.py)"
  - "CONFLICTED consensus proposals get status=CONFLICTED (not PENDING) for clear visual differentiation"
  - "Score impact reports affected ticker count rather than recalculating scores (pipeline re-run out of scope for impact projection)"

patterns-established:
  - "Consensus algorithm: >60% majority required, single reactions use direct mapping"
  - "Confidence scoring: LOW (1), MEDIUM (2-3), HIGH (4+) based on reaction count"
  - "AGREE consensus produces no proposal; only DISAGREE/ADJUST/CONFLICTED generate brain_proposals entries"

requirements-completed: [FEED-01]

# Metrics
duration: 4min
completed: 2026-02-28
---

# Phase 51 Plan 02: Feedback Processing Summary

**Reaction aggregation engine with consensus detection, confidence scoring, fire rate impact projections, and CLI process/show commands**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-28T03:19:52Z
- **Completed:** 2026-02-28T03:23:49Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Implemented aggregation algorithm that groups reactions by signal and determines consensus (AGREE/DISAGREE/ADJUST/CONFLICTED) with 60% threshold
- Confidence scoring (LOW/MEDIUM/HIGH) based on reaction volume, with DEACTIVATION proposals for HIGH-confidence DISAGREE (4+ reactions)
- Fire rate and score impact projections computed from brain_signal_runs historical data
- CLI `feedback process` command with summary table, proposals table, and verbose drill-down mode
- CLI `feedback show <id>` command for on-demand proposal detail viewing

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement proposal aggregation and impact projection logic** - `4ac38de` (feat)
2. **Task 2: Implement feedback process CLI command with summary table and drill-down** - `f3f3623` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/feedback_process.py` - Core aggregation engine: AggregationResult model, aggregate_reactions(), compute_fire_rate_impact(), compute_score_impact(), generate_proposals(), process_pending_reactions()
- `src/do_uw/cli_feedback_process.py` - CLI extension: feedback process and feedback show commands with Rich tables and panels
- `src/do_uw/cli_feedback.py` - Added import of cli_feedback_process extension module

## Decisions Made
- Split CLI commands into `cli_feedback_process.py` rather than adding to `cli_feedback.py` (already at 666 lines). Same extension pattern as `cli_brain.py`/`cli_brain_ext.py`.
- CONFLICTED proposals receive `status=CONFLICTED` distinct from `PENDING`, making them visually identifiable in both tables and queries.
- Score impact is computed as affected ticker count (not score recalculation) since full rescoring would require re-running the pipeline.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Proposals are now generated and stored in `brain_proposals` with full impact data
- Ready for Phase 51-03: `brain apply-proposal <id>` to write YAML changes, rebuild DuckDB, validate, and git commit
- The `feedback show` command provides the proposal detail view needed before applying

## Self-Check: PASSED

- All created files exist on disk
- All task commits found in git log (4ac38de, f3f3623)

---
*Phase: 51-feedback-loop*
*Completed: 2026-02-28*
