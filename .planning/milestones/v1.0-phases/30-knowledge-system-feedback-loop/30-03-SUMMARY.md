---
phase: 30-knowledge-system-feedback-loop
plan: 03
subsystem: analyze
tags: [traceability, check-results, audit, cli, pydantic, rich]

# Dependency graph
requires:
  - phase: 30-01
    provides: "Persistent-first knowledge store with idempotent migration"
provides:
  - "5-link traceability chain on every CheckResult (data_source, extraction, evaluation, output, scoring)"
  - "Automatic trace population from check definitions in the check engine"
  - "CLI traceability audit command (knowledge trace audit)"
  - "traceability_complete and traceability_gaps helper properties"
affects: [30-04, score-stage, render-stage, knowledge-cli]

# Tech tracking
tech-stack:
  added: []
  patterns: [traceability-chain, trace-population-at-evaluation, separate-cli-subapp]

key-files:
  created:
    - src/do_uw/cli_knowledge_traceability.py
    - tests/knowledge/test_traceability.py
  modified:
    - src/do_uw/stages/analyze/check_results.py
    - src/do_uw/stages/analyze/check_engine.py
    - src/do_uw/cli_knowledge.py

key-decisions:
  - "Trace fields populated centrally in _apply_traceability() called from evaluate_check(), not at each CheckResult construction site"
  - "trace_data_source and trace_extraction derived from check definition metadata (required_data, data_locations) rather than runtime resolution"
  - "CLI traceability command extracted to cli_knowledge_traceability.py as sub-app (cli_knowledge.py was already 503 lines)"
  - "Handles both dict and list data_locations for industry playbook compatibility"

patterns-established:
  - "Traceability chain: every CheckResult carries 5 provenance links for full pipeline audit"
  - "Central trace population: single function reads check definition fields, not scattered across evaluators"

# Metrics
duration: 10min
completed: 2026-02-15
---

# Phase 30 Plan 03: Traceability Chain Summary

**5-link traceability chain on CheckResult with central engine population and CLI audit command**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-15T17:24:06Z
- **Completed:** 2026-02-15T17:34:39Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Every CheckResult now carries 5 trace fields: trace_data_source, trace_extraction, trace_evaluation, trace_output, trace_scoring
- Check engine automatically populates all 5 links from check definition metadata (section, pillar, factors, required_data, data_locations, threshold type)
- CLI `knowledge trace audit` command provides completeness summary with gap breakdown (works with state.json files or brain definitions)
- 13 new tests covering field properties, engine population, backward compatibility, and list data_locations handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Traceability fields and engine/mapper population** - `dc9a867` (feat)
2. **Task 2: Traceability audit CLI and tests** - `14eea93` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/check_results.py` - Added 5 trace_ fields, traceability_complete property, traceability_gaps helper
- `src/do_uw/stages/analyze/check_engine.py` - Added _apply_traceability() function, called from evaluate_check() and execute_checks()
- `src/do_uw/cli_knowledge_traceability.py` - New file: traceability audit sub-app with Rich output
- `src/do_uw/cli_knowledge.py` - Registered traceability sub-app, updated docstring
- `tests/knowledge/test_traceability.py` - 13 tests: field properties, engine population, backward compat

## Decisions Made
- Centralized trace population in `_apply_traceability()` rather than modifying each evaluator function -- this avoids touching 6+ CheckResult construction sites and keeps the engine under control
- Derived trace_data_source/trace_extraction from check definition metadata (required_data, data_locations) rather than tracking runtime resolution -- simpler, no mapper signature changes needed
- Extracted CLI command to separate file since cli_knowledge.py was already at 503 lines (well over the 420-line budget)
- Used sub-app pattern (`knowledge trace audit`) matching existing `knowledge govern` convention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed list data_locations crash for industry playbook checks**
- **Found during:** Task 1 (engine trace population)
- **Issue:** Industry playbook checks (TECH.REV.*, TECH.COMP.*, etc.) have `data_locations` as a list (e.g., `["extracted.financials"]`), not a dict. The `_apply_traceability` function called `.items()` on it, causing `'list' object has no attribute 'items'`
- **Fix:** Added `isinstance(data_locs, dict)` check before `.items()`, with separate handling for list-type data_locations
- **Files modified:** src/do_uw/stages/analyze/check_engine.py
- **Verification:** Pipeline tests pass, added test_list_data_locations_handled test
- **Committed in:** dc9a867 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for correctness with industry playbook checks. No scope creep.

## Issues Encountered
- Pre-existing test failures: TSLA material weakness ground truth test and TestAnalyzeCommand integration tests -- both documented in prior summaries as known issues, unrelated to this work

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Traceability chain ready for Plan 30-04 (learning infrastructure)
- trace fields will be populated for all checks during pipeline runs
- CLI audit command available for inspecting trace completeness on any analysis output
- Pre-existing test failures unchanged (TSLA ground truth, analyze command integration)

## Self-Check: PASSED

- All 5 files verified present on disk
- Both task commits (dc9a867, 14eea93) verified in git log
- All must_have artifacts confirmed (trace_data_source, trace_evaluation, traceability-audit)

---
*Phase: 30-knowledge-system-feedback-loop*
*Completed: 2026-02-15*
