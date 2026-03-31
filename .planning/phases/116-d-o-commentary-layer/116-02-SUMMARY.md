---
phase: 116-d-o-commentary-layer
plan: 02
subsystem: render
tags: [do_context, brain-yaml, signal-consumer, jinja2, docx-renderer]

# Dependency graph
requires:
  - phase: 116-01
    provides: "563 brain signals populated with do_context templates"
  - phase: 115
    provides: "safe_get_result consumer pattern and SignalResultView.do_context field"
provides:
  - "5 hardcoded Python D&O commentary functions deleted from render sections"
  - "1 Jinja2 template migrated to do_context pass-through variables"
  - "All rendered D&O commentary now originates from brain YAML do_context"
  - "Golden parity tests confirming equivalent D&O intelligence"
affects: [116-03, 116-04, 116-05, 120]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Signal do_context consumption in section renderers via safe_get_result(signal_results, SIGNAL_ID).do_context"
    - "Per-section _get_signal_results() helper extracting from context['_state'].analysis.signal_results"
    - "Graceful fallback: when signal unavailable, renderers use generic text or skip"

key-files:
  created:
    - tests/render/test_do_context_migration.py
  modified:
    - src/do_uw/stages/render/sections/sect3_audit.py
    - src/do_uw/stages/render/sections/sect4_market_events.py
    - src/do_uw/stages/render/sections/sect5_governance.py
    - src/do_uw/stages/render/sections/sect6_litigation.py
    - src/do_uw/stages/render/sections/sect7_scoring_detail.py
    - src/do_uw/templates/html/sections/financial/distress_indicators.html.j2

key-decisions:
  - "Signal fallback: when do_context unavailable, render generic text rather than crash or show empty"
  - "Per-row departure D&O context uses signal do_context for UNPLANNED, simplified text for PLANNED"
  - "SCA do_context: active/settlement/counsel each mapped to distinct LIT.SCA.* signals"
  - "Pattern do_context: iterates trigger signal IDs to find first with do_context, falls back to generic"

patterns-established:
  - "Section renderer signal consumption: _get_signal_results(context) -> safe_get_result(results, ID).do_context"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-03-19
---

# Phase 116 Plan 02: D&O Commentary Migration Summary

**Deleted 5 hardcoded Python D&O commentary functions and 4 Jinja2 inline conditionals, replacing all with brain signal do_context consumption via safe_get_result pattern**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-19T04:58:05Z
- **Completed:** 2026-03-19T05:06:27Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Deleted _add_audit_do_context(), _departure_do_context(), _add_leadership_do_context(), _add_sca_do_context(), _add_pattern_do_context() from 5 section renderers
- Replaced 4 inline Jinja2 D&O conditionals in distress_indicators.html.j2 with {{ fin.*_do_context }} pass-through variables
- Created 20 golden parity tests validating signal do_context covers equivalent D&O intelligence
- All 63 render tests pass, CI gate (5 tests) passes

## Task Commits

Each task was committed atomically:

1. **Task 1: Create golden parity snapshots and migrate sect3-5 Python functions** - `978fca0a` (feat)
2. **Task 2: Migrate sect6-7 Python functions and Jinja2 template** - `3c1d2f4f` (feat)

## Files Created/Modified
- `tests/render/test_do_context_migration.py` - 20 golden parity tests for all 5 migration targets + template validation
- `src/do_uw/stages/render/sections/sect3_audit.py` - Replaced _add_audit_do_context with signal do_context from FIN.ACCT.* signals
- `src/do_uw/stages/render/sections/sect4_market_events.py` - Replaced _departure_do_context with EXEC.DEPARTURE.* signal do_context
- `src/do_uw/stages/render/sections/sect5_governance.py` - Replaced _add_leadership_do_context with EXEC.PRIOR_LIT/GOV.BOARD signal do_context
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Replaced _add_sca_do_context with LIT.SCA.* signal do_context
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` - Replaced _add_pattern_do_context with trigger signal do_context lookups
- `src/do_uw/templates/html/sections/financial/distress_indicators.html.j2` - Replaced 4 inline conditionals with do_context variables

## Decisions Made
- Signal fallback strategy: when do_context is unavailable (signal missing or SKIPPED), renderers provide generic fallback text rather than crashing or rendering empty
- Per-row departure context: UNPLANNED departures use signal do_context, PLANNED uses simplified signal text -- departure signals are aggregate-level, not per-person
- SCA migration maps to 3 distinct signals (LIT.SCA.active, LIT.SCA.prior_settle, LIT.SCA.exposure) covering the 3 aspects of the old monolithic function
- Pattern do_context iterates the pattern's triggers_matched list to find the first signal with do_context, providing pattern-specific commentary

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 Python D&O commentary functions deleted -- zero hardcoded D&O text remains in section renderers
- Brain YAML do_context is now the sole source of D&O commentary for all migrated sections
- Ready for Plan 03 (remaining HTML template migrations) and Plan 05 (CI gate promotion)

---
*Phase: 116-d-o-commentary-layer*
*Completed: 2026-03-19*
