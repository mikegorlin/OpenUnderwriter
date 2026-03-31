---
phase: 50-automated-qa-anomaly-detection
plan: 02
subsystem: brain-cli
tags: [duckdb, rich, typer, brain-health, brain-audit, cli]

# Dependency graph
requires:
  - phase: 49-pipeline-integrity
    provides: Facet system (load_all_facets), brain signal nomenclature, brain_signals_active view
provides:
  - "`do-uw brain health` unified system health command"
  - "`do-uw brain audit` structural health audit command"
  - "BrainHealthReport and BrainAuditReport Pydantic models"
affects: [phase-50-qa, phase-51-feedback, phase-52-knowledge]

# Tech tracking
tech-stack:
  added: []
  patterns: [brain-health-computation, brain-audit-findings, cli-registration-via-import]

key-files:
  created:
    - src/do_uw/brain/brain_health.py
    - src/do_uw/brain/brain_audit.py
  modified:
    - src/do_uw/cli_brain_health.py
    - src/do_uw/cli_brain.py

key-decisions:
  - "Facet coverage computed by intersecting facet signal IDs with active DB signals (avoids >100% when facets reference INACTIVE signals)"
  - "Threshold conflict detection limited to tiered/numeric types only (skips boolean, count, ratio, date)"
  - "Staleness reported as aggregate counts not per-signal (380 never-calibrated signals would be too noisy)"

patterns-established:
  - "Brain computation module + CLI module split: brain_health.py (computation) + cli_brain_health.py (CLI)"
  - "AuditFinding model with category/severity/message/detail for structured audit results"

requirements-completed: [QA-02, QA-05]

# Metrics
duration: 15min
completed: 2026-02-27
---

# Phase 50 Plan 02: Brain Health + Brain Audit Summary

**Two new CLI commands: `brain health` shows unified system health (coverage, fire rates, freshness, feedback queue) and `brain audit` reports structural issues (staleness, peril coverage gaps, threshold conflicts, orphaned signals)**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-27T02:42:49Z
- **Completed:** 2026-02-27T02:58:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `do-uw brain health` shows: 380 active signals (of 400 total), 100% facet coverage, fire rate distribution histogram (6 buckets), top always-fire/never-fire/high-skip signals, data freshness, pipeline run counts, feedback queue size, tickers analyzed
- `do-uw brain audit` shows: staleness report (380 never calibrated), peril coverage status (correctly reports "NOT AVAILABLE" since 0/380 signals have peril_id), threshold conflict detection (numeric types only), orphaned signal check (all assigned to facets)
- Both commands are read-only, create no new DuckDB tables, and handle missing brain.duckdb gracefully

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement brain health computation + CLI command** - `1809c3a` (feat)
2. **Task 2: Implement brain audit computation + CLI command** - `96bec5c` (feat)

## Files Created/Modified
- `src/do_uw/brain/brain_health.py` - BrainHealthReport model + compute_brain_health() (222 lines)
- `src/do_uw/brain/brain_audit.py` - AuditFinding/BrainAuditReport models + compute_brain_audit() with 4 check categories (461 lines)
- `src/do_uw/cli_brain_health.py` - CLI commands for `brain health` and `brain audit` with Rich tables/panels (398 lines)
- `src/do_uw/cli_brain.py` - Import registration for cli_brain_health module

## Decisions Made
- Facet coverage intersection: facet signal IDs are intersected with active DB signal IDs to avoid >100% coverage (facets reference some INACTIVE signals)
- Threshold conflict detection only for numeric types (tiered, numeric_threshold) -- boolean_presence, count_threshold, ratio_threshold, date_threshold do not have overlapping ranges to conflict
- Staleness is reported as aggregate counts (never calibrated: 380, >365 days: 0, etc.) rather than per-signal findings, because 380 individual findings would be too noisy

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed facet coverage >100% calculation**
- **Found during:** Task 1 (brain health computation)
- **Issue:** Facet coverage showed 105.3% because facet YAML files reference 400 signal IDs (including INACTIVE ones) but only 380 are active
- **Fix:** Intersect facet signal IDs with active signal IDs from brain_signals_active before computing coverage percentage
- **Files modified:** src/do_uw/brain/brain_health.py
- **Verification:** `do-uw brain health` now correctly shows 100.0% coverage (380/380)
- **Committed in:** 1809c3a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for data accuracy. No scope creep.

## Issues Encountered
None -- both commands implemented cleanly from existing infrastructure.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Brain health and audit commands are complete and registered
- Ready for 50-03 (brain delta cross-run comparison) and 50-04 (signal composites)
- Pre-existing test failures noted (test_compat_loader scoring table, test_signal_nomenclature check_results in health_summary.py from 50-01) -- these are unrelated to this plan

---
*Phase: 50-automated-qa-anomaly-detection*
*Completed: 2026-02-27*
