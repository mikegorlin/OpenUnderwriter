---
phase: 50-automated-qa-anomaly-detection
plan: 01
subsystem: validation
tags: [pydantic, rich, anomaly-detection, signal-health, qa]

# Dependency graph
requires:
  - phase: 49-pipeline-integrity
    provides: "Signal nomenclature (check->signal rename), brain.duckdb signal runs, facet system"
provides:
  - "SignalResult.details field for composites to read structured evaluation data"
  - "Post-pipeline health summary with anomaly detection (CLI output)"
  - "Signal enrichment pattern (stock drops, insider trading, litigation, financial distress)"
affects: [50-02, 50-03, 50-04]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Post-evaluation details enrichment via signal_details.py", "Heuristic anomaly detection with module-level threshold constants"]

key-files:
  created:
    - src/do_uw/stages/analyze/signal_details.py
    - src/do_uw/validation/health_summary.py
  modified:
    - src/do_uw/stages/analyze/signal_results.py
    - src/do_uw/stages/analyze/signal_engine.py
    - src/do_uw/cli.py
    - tests/brain/test_signal_nomenclature.py

key-decisions:
  - "Details enrichment in separate module (signal_details.py) rather than inline in evaluators -- keeps evaluators generic"
  - "Post-evaluation enrichment pattern: evaluators produce results, then signal_details enriches from ExtractedData"
  - "Anomaly thresholds as module-level constants (MAX_SKIPPED_THRESHOLD=45) consistent with test_brain_contract.py"
  - "Health summary reads both signal_results and legacy check_results keys for backward compat"

patterns-established:
  - "signal_details.py enrichment pattern: domain-specific functions keyed by signal_id prefix"
  - "health_summary.py anomaly rule pattern: each rule returns AnomalyWarning | None"

requirements-completed: [QA-01]

# Metrics
duration: 28min
completed: 2026-02-26
---

# Phase 50 Plan 01: Signal Details + Health Summary

**SignalResult gains details dict for composite analysis, with Rich-formatted post-pipeline health summary showing signal counts, section breakdown, and heuristic anomaly warnings**

## Performance

- **Duration:** 28 min
- **Started:** 2026-02-27T02:42:33Z
- **Completed:** 2026-02-27T03:10:14Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added `details: dict[str, Any]` field to SignalResult enabling composites to read structured evaluation data
- Created signal_details.py enriching 4 signal domains (stock drops, insider trading, litigation, financial distress)
- Implemented validation/health_summary.py with compute_health_summary() + print_health_summary()
- Added 3 heuristic anomaly rules: zero-triggered-with-litigation, high-skipped (>45), all-section-skipped
- Wired health summary into cli.py post-pipeline hook alongside existing QA report
- Verified with real AAPL state data: 403 signals, correct section breakdown, anomaly detection working

## Task Commits

Each task was committed atomically:

1. **Task 1: Add details field to SignalResult and enrich evaluators** - `be76044` (feat)
2. **Task 2: Implement post-pipeline health summary with anomaly detection** - `4583e2e` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/signal_results.py` - Added `details: dict[str, Any]` field to SignalResult model
- `src/do_uw/stages/analyze/signal_details.py` - NEW: Post-evaluation enrichment for 4 signal domains
- `src/do_uw/stages/analyze/signal_engine.py` - Wired enrichment into execute_signals() post-evaluation
- `src/do_uw/validation/health_summary.py` - NEW: HealthSummary + AnomalyWarning models, compute + print functions
- `src/do_uw/cli.py` - Added health summary call after QA report in post-pipeline hook
- `tests/brain/test_signal_nomenclature.py` - Added health_summary.py to allowlist for backward-compat key access

## Decisions Made
- **Enrichment architecture:** Created separate signal_details.py module rather than modifying evaluators. Evaluators remain generic threshold evaluators; enrichment happens post-evaluation with access to full ExtractedData. This keeps the evaluators clean and the enrichment testable independently.
- **Anomaly thresholds:** Defined as module-level constants (MAX_SKIPPED_THRESHOLD=45) rather than config JSON. Consistent with the existing test_brain_contract.py threshold. Can be moved to config later if adjustment needed.
- **Backward compatibility:** health_summary.py checks both `signal_results` and `check_results` keys using the same pattern as cli_brain_trace.py, supporting both Pydantic AnalysisState and dict-based state from JSON.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Nomenclature test allowlist update**
- **Found during:** Task 2 (health summary implementation)
- **Issue:** test_signal_nomenclature.py flagged `check_results` string in health_summary.py as forbidden term
- **Fix:** Added `health_summary.py` to the ALLOWLIST_FILES (same pattern as cli_brain_trace.py which is also allowlisted)
- **Files modified:** tests/brain/test_signal_nomenclature.py
- **Verification:** All 37 nomenclature tests pass
- **Committed in:** 4583e2e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for backward compatibility with old state files. No scope creep.

## Issues Encountered
- 3 pre-existing test failures found in tests/knowledge/ (test_compat_loader, test_ingestion, test_integration). All verified as pre-existing by running tests without Plan 50-01 changes. Not related to this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- SignalResult.details field is ready for Plan 04 (Signal Composites) to consume
- Health summary prints after every `do-uw analyze` run
- Anomaly detection operational with 3 heuristic rules
- Pattern established for adding more enrichment domains in signal_details.py

## Self-Check: PASSED

All files exist, all commits verified:
- be76044: feat(50-01): add details field to SignalResult and post-evaluation enrichment
- 4583e2e: feat(50-01): implement post-pipeline health summary with anomaly detection

---
*Phase: 50-automated-qa-anomaly-detection*
*Completed: 2026-02-26*
