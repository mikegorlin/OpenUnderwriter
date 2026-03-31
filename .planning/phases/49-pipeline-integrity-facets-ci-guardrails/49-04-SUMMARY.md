---
phase: 49-pipeline-integrity-facets-ci-guardrails
plan: 04
subsystem: cli
tags: [trace, render-audit, facets, signals, diagnostics, rich-console]

# Dependency graph
requires:
  - phase: 49-01
    provides: "check->signal rename, brain/signals/ YAML directory"
  - phase: 49-02
    provides: "facet field on all 400 signals, 9 facet definition YAMLs"
  - phase: 49-03
    provides: "20 GOV signals INACTIVE, lifecycle_state field in YAML"
provides:
  - "brain trace CLI command with blueprint + live modes (5-stage pipeline journey)"
  - "brain render-audit CLI command (declared vs rendered signals per facet)"
  - "facet-aware metadata in HTML signal grouping (_PREFIX_TO_FACET, _lookup_facet_metadata)"
  - "_group_signals_by_section includes facet_id and facet_name on every signal"
affects: [49-05, rendering-templates, future-facet-migration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Signal trace diagnostic: 5-stage vertical flow (YAML -> Extraction -> Mapping -> Evaluation -> Rendering)"
    - "Facet metadata as parallel classification (additive, not replacement for prefix-based grouping)"
    - "Backward-compat state reading: for key in (signal_results, check_results) loop pattern"

key-files:
  created:
    - "src/do_uw/cli_brain_trace.py"
  modified:
    - "src/do_uw/cli_brain.py"
    - "src/do_uw/stages/render/html_signals.py"

key-decisions:
  - "Created new cli_brain_trace.py rather than adding to cli_brain.py or cli_brain_ext.py (both near 500-line limit)"
  - "render-audit placed in cli_brain_trace.py (thematically related diagnostic commands)"
  - "Facet metadata additive in _group_signals_by_section -- facet_id and facet_name added without changing section assignment"
  - "_PREFIX_TO_FACET bridges existing prefix-based rendering with new facet system"
  - "Backward-compat for state.json: explicit for-loop over key candidates instead of or-chain (linter-safe)"

patterns-established:
  - "Signal diagnostics in cli_brain_trace.py (trace, render-audit)"
  - "_lookup_facet_metadata() for resolving signal -> facet membership"

requirements-completed: [INT-02, INT-03, FACET-03]

# Metrics
duration: 15min
completed: 2026-02-26
---

# Phase 49 Plan 04: Trace & Render-Audit Commands Summary

**brain trace shows 5-stage pipeline journey per signal (blueprint + live), render-audit reports declared vs rendered coverage per facet, HTML grouping now carries facet metadata**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-26T20:36:13Z
- **Completed:** 2026-02-26T20:51:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `brain trace <SIGNAL_ID>` shows full pipeline journey: YAML Definition, Extraction, Mapping, Evaluation, Rendering stages
- Blueprint mode (--blueprint) shows theoretical routes from YAML only, no run needed
- Live mode loads state.json and shows actual values, status markers, evidence at each stage
- `brain render-audit <TICKER>` shows per-facet declared vs rendered signals (AAPL: 325/400 = 81%)
- HTML signal grouping now includes facet_id and facet_name on every signal (parallel metadata, not replacement)
- _PREFIX_TO_FACET mapping and _lookup_facet_metadata() function bridge prefix-based and facet-based systems

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement brain trace CLI command** - `637066c` (feat)
2. **Task 2: Implement render-audit and facet-aware HTML grouping** - `9f4e160` (feat)

## Files Created/Modified
- `src/do_uw/cli_brain_trace.py` (NEW) - trace and render-audit commands (494 lines)
- `src/do_uw/cli_brain.py` - Added import registration for cli_brain_trace module
- `src/do_uw/stages/render/html_signals.py` - _PREFIX_TO_FACET, _lookup_facet_metadata(), facet metadata in grouped signal dicts

## Decisions Made
- **New file for diagnostic commands:** Created cli_brain_trace.py rather than adding to existing cli_brain.py (420 lines) or cli_brain_ext.py (491 lines) -- both near the 500-line limit.
- **render-audit in same file:** Placed render-audit in cli_brain_trace.py since it's thematically related (signal diagnostics). File at 494 lines, under limit.
- **Facet metadata is additive:** _group_signals_by_section now includes facet_id and facet_name but does NOT change section assignment. Existing prefix-based rendering is completely unchanged.
- **Linter-safe backward compat:** Used explicit for-loop over key candidates ("signal_results", "check_results") instead of `or` chain, which linters were stripping.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Backward-compat for state.json check_results key**
- **Found during:** Task 1 (live mode testing)
- **Issue:** state.json files use `check_results` key (pre-rename), but code only checked `signal_results`
- **Fix:** Added explicit for-loop fallback to try both key names
- **Files modified:** src/do_uw/cli_brain_trace.py (both _print_live and brain_render_audit)
- **Verification:** AAPL render-audit shows 325/400 rendered (was 0/400 without fix)
- **Committed in:** 9f4e160 (Task 2 commit, combined with facet changes)

**2. [Rule 1 - Bug] html_signals.py changes lost during stash pop conflict**
- **Found during:** Task 2 (post-test verification)
- **Issue:** git stash/pop failed on brain.duckdb conflict, silently reverting html_signals.py edits
- **Fix:** Re-applied all _PREFIX_TO_FACET, _lookup_facet_metadata, and facet metadata changes
- **Files modified:** src/do_uw/stages/render/html_signals.py
- **Verification:** Import test confirms facet_id/facet_name present in grouped signals
- **Committed in:** 9f4e160

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- **Pre-existing test failure:** tests/test_render_coverage.py has two failing tests (Word coverage 89.1% < 90% threshold, HTML coverage similar). Confirmed pre-existing and unrelated to Plan 04 changes.
- **DuckDB WAL lock:** Transient DuckDB lock errors during testing when multiple processes accessed brain.duckdb concurrently. Resolved by cleaning up .wal file.
- **Linter modifying backward compat:** Linter automatically removed `or analysis.get("check_results", {})` pattern, treating it as redundant. Switched to explicit for-loop pattern which linter accepts.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- trace and render-audit commands ready for CI guardrails (Plan 05) to validate
- Facet metadata in HTML grouping enables future template migration from prefix-based to facet-based rendering
- 478 rendering tests pass (excluding 2 pre-existing coverage threshold failures)

## Self-Check: PASSED

All claims verified:
- All 3 modified/created files exist on disk
- Both task commits found (637066c, 9f4e160)
- _PREFIX_TO_FACET mapping present in html_signals.py
- render-audit and brain_trace commands present in cli_brain_trace.py
- Import registration present in cli_brain.py

---
*Phase: 49-pipeline-integrity-facets-ci-guardrails*
*Completed: 2026-02-26*
