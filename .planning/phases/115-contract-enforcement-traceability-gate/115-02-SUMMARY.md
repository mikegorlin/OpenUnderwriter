---
phase: 115-contract-enforcement-traceability-gate
plan: 02
subsystem: brain
tags: [do_context, yaml, ci-gate, signal-results, distress-models]

requires:
  - phase: 115-01
    provides: do_context engine (render_do_context, apply_do_context, _select_template)
provides:
  - do_context YAML templates on 4 distress signals (Altman, Beneish, Piotroski + composite)
  - SignalResultView.do_context field for consumer-side access
  - get_signal_do_context accessor in _signal_consumer
  - CI gate preventing hardcoded D&O commentary regression
  - Golden parity tests proving YAML output matches original Python functions
affects: [116-distress-templates-remaining, render-context-builders]

tech-stack:
  added: []
  patterns:
    - "do_context consumer pattern: safe_get_result -> .do_context field"
    - "AST-based Python string literal scanning for CI gates"
    - "Baseline-tracked regression prevention (template/file counts)"

key-files:
  created:
    - tests/test_do_context_golden.py
    - tests/brain/test_do_context_ci_gate.py
  modified:
    - src/do_uw/brain/signals/fin/accounting.yaml
    - src/do_uw/brain/signals/fin/forensic.yaml
    - src/do_uw/brain/signals/fin/forensic_xbrl.yaml
    - src/do_uw/stages/render/context_builders/_distress_do_context.py
    - src/do_uw/stages/render/context_builders/_signal_consumer.py
    - src/do_uw/stages/render/context_builders/financials_evaluative.py
    - src/do_uw/stages/analyze/do_context_engine.py

key-decisions:
  - "Ohlson retained as Python fallback -- no brain signal exists for Ohlson O-Score"
  - "Piotroski int formatting: render_do_context strips .0 from whole-number floats for template parity"
  - "CI gate uses baseline counts for templates (34) and context builders (20) rather than exhaustive allow-lists"
  - "AST-based scanning for Python files, regex for Jinja2 templates"

patterns-established:
  - "do_context consumer: safe_get_result(signal_results, SIGNAL_ID).do_context"
  - "Beneish fallback chain: m_score_composite -> earnings_manipulation"
  - "CI gate two-tier: FAIL on migrated scope, WARN on future targets"

requirements-completed: [INFRA-03, INFRA-04, INFRA-05]

duration: 22min
completed: 2026-03-18
---

# Phase 115 Plan 02: Distress D&O Commentary Migration Summary

**3 distress commentary functions migrated from Python to brain YAML do_context with golden parity tests and CI regression gate**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-18T23:45:23Z
- **Completed:** 2026-03-19T00:07:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Migrated Altman Z-Score, Beneish M-Score, and Piotroski F-Score D&O commentary from hardcoded Python functions to brain YAML do_context templates
- Added do_context field to SignalResultView dataclass and wired context builders to consume it
- Created 19 golden parity tests proving YAML templates produce identical output to original Python functions
- Created CI gate with 5 tests: FAIL on Phase 115 scope, WARN on Phase 116 targets (Python + Jinja2), baseline-tracked regression prevention

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED):** Golden parity tests - `94b00184` (test)
2. **Task 1 (GREEN):** YAML templates + consumer wiring + function deletion - `f45a764a` (feat)
3. **Task 2:** CI gate test - `1eeee3ff` (feat)

## Files Created/Modified
- `src/do_uw/brain/signals/fin/accounting.yaml` - Added do_context blocks for quality_indicators (Altman) and earnings_manipulation (Beneish)
- `src/do_uw/brain/signals/fin/forensic.yaml` - Added do_context block for dechow_f_score (Piotroski)
- `src/do_uw/brain/signals/fin/forensic_xbrl.yaml` - Added do_context block for m_score_composite (Beneish active)
- `src/do_uw/stages/render/context_builders/_distress_do_context.py` - Deleted altman_do_context, beneish_do_context, piotroski_do_context; kept ohlson_do_context fallback
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` - Added do_context field to SignalResultView, get_signal_do_context accessor
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` - Wired to consume do_context from signal results instead of Python functions
- `src/do_uw/stages/analyze/do_context_engine.py` - Fixed whole-number float formatting (8.0 -> 8) for Piotroski template parity
- `tests/test_do_context_golden.py` - 19 golden parity tests covering all 3 migrated signals + Ohlson fallback + SignalResultView
- `tests/brain/test_do_context_ci_gate.py` - 5 CI gate tests with AST scanning, Jinja2 scanning, baseline tracking

## Decisions Made
- Ohlson O-Score retained as Python fallback because no brain signal exists for it. Phase 116 will create the signal and migrate.
- Used `int()` stripping for whole-number floats in render_do_context to achieve parity with Python's `int(score)` formatting in Piotroski templates.
- CI gate uses baseline file/template counts (20 Python files, 34 Jinja2 templates) rather than exhaustive allow-lists, making the gate sensitive to NEW violations while tolerating known pre-existing ones.
- Beneish do_context added to BOTH earnings_manipulation (DEFERRED) and m_score_composite (active) signals, with consumer fallback chain trying composite first.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed whole-number float rendering in do_context_engine**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Pydantic coerces int value=8 to float 8.0, causing template {value} to render "8.0/9" instead of "8/9"
- **Fix:** Added int() stripping for whole-number floats in render_do_context
- **Files modified:** src/do_uw/stages/analyze/do_context_engine.py
- **Committed in:** f45a764a

**2. [Rule 1 - Bug] Fixed CI gate ohlson filtering to use AST function boundaries**
- **Found during:** Task 2
- **Issue:** Initial text-based ohlson filter missed "D&O risk profile" string inside ohlson_do_context function
- **Fix:** Added _is_in_ohlson_function() using AST to detect function boundaries
- **Files modified:** tests/brain/test_do_context_ci_gate.py
- **Committed in:** 1eeee3ff

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- financials_evaluative.py hit 304-line limit (max 300) after initial migration. Tightened comments and consolidated Beneish signal lookup to bring it to 297 lines.
- CI gate "no new" tests required baseline tracking due to extensive pre-existing D&O evaluative language across 20 context builder files and 34 Jinja2 templates.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- do_context infrastructure fully proven end-to-end: engine (Plan 01) + YAML templates + consumer wiring + CI gate (Plan 02)
- Phase 116 can follow the same migration pattern for remaining commentary functions in sect3-7 render sections
- CI gate will catch regressions immediately if new hardcoded D&O commentary is added

## Self-Check: PASSED

All 9 files found. All 3 commits verified. All 10 acceptance criteria met.

---
*Phase: 115-contract-enforcement-traceability-gate*
*Completed: 2026-03-18*
