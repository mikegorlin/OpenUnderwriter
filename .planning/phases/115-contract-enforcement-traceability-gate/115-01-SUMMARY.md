---
phase: 115-contract-enforcement-traceability-gate
plan: 01
subsystem: analyze
tags: [do_context, brain-yaml, template-engine, signal-results, cli]

# Dependency graph
requires: []
provides:
  - PresentationSpec.do_context field (brain YAML schema)
  - SignalResult.do_context field (populated in ANALYZE)
  - do_context_engine.py module (render, apply, validate)
  - Pipeline integration (all 8 signal eval paths)
  - brain health/audit do_context validation
affects: [115-02, rendering, context-builders]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SafeFormatDict for crash-safe template variable substitution
    - Compound key fallback chain (TRIGGERED_RED -> TRIGGERED -> DEFAULT)
    - YAML-driven D&O commentary (brain signals declare, engine renders)

key-files:
  created:
    - src/do_uw/stages/analyze/do_context_engine.py
    - tests/stages/analyze/test_do_context_engine.py
    - tests/brain/test_do_context_health.py
  modified:
    - src/do_uw/brain/brain_signal_schema.py
    - src/do_uw/stages/analyze/signal_results.py
    - src/do_uw/stages/analyze/signal_engine.py
    - src/do_uw/cli_brain_health.py
    - tests/brain/test_brain_schema.py

key-decisions:
  - "apply_do_context added at each call site rather than wrapper function -- safer for existing code"
  - "SafeFormatDict returns empty string for missing variables -- no crash on incomplete data"
  - "SKIPPED signals always get empty do_context -- no commentary for unevaluated signals"

patterns-established:
  - "do_context templates in brain YAML: presentation.do_context with status-keyed templates"
  - "Template variables: {value}, {score}, {zone}, {threshold}, {evidence}, {source}, {company}, {ticker}, {details_*}"

requirements-completed: [INFRA-01, INFRA-02]

# Metrics
duration: 12min
completed: 2026-03-18
---

# Phase 115 Plan 01: do_context Infrastructure Summary

**Brain-YAML-driven D&O commentary engine with template evaluation, pipeline integration, and health/audit validation**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-18T23:31:14Z
- **Completed:** 2026-03-18T23:43:07Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- PresentationSpec.do_context and SignalResult.do_context fields with backward-compatible defaults
- do_context_engine.py: render_do_context, apply_do_context, _select_template, validate_do_context_template
- Pipeline wired at all 8 signal evaluation paths in signal_engine.py
- brain health reports do_context coverage; brain audit validates template syntax
- 50 total new tests (30 engine + 7 health/audit + 2 schema + 11 pre-existing schema)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add do_context fields and create do_context_engine.py** - `61dd8bed` (feat, TDD)
2. **Task 2: Wire apply_do_context into signal_engine.py** - `f8927408` (feat)
3. **Task 3: Add do_context validation to brain health/audit** - `f12ab61e` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/do_context_engine.py` - Template evaluation engine (render, apply, select, validate)
- `src/do_uw/brain/brain_signal_schema.py` - Added PresentationSpec.do_context field
- `src/do_uw/stages/analyze/signal_results.py` - Added SignalResult.do_context field
- `src/do_uw/stages/analyze/signal_engine.py` - Wired apply_do_context at 8 eval paths
- `src/do_uw/cli_brain_health.py` - do_context coverage in health, template validation in audit
- `tests/stages/analyze/test_do_context_engine.py` - 30 unit tests for engine
- `tests/brain/test_do_context_health.py` - 7 health/audit validation tests
- `tests/brain/test_brain_schema.py` - 2 PresentationSpec do_context tests

## Decisions Made
- Added apply_do_context at each individual call site rather than using a wrapper function, to minimize risk to existing code paths
- SafeFormatDict returns empty string for missing template variables rather than raising errors -- brain YAML authors can safely reference optional fields
- SKIPPED signals always produce empty do_context since there is no meaningful commentary for unevaluated signals

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failures in brain tests (orphaned templates, template purity) unrelated to this plan's changes
- Pre-existing test failure in test_inference_evaluator (evidence string mismatch) unrelated to changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- do_context infrastructure complete, ready for 115-02 (pilot YAML signals with do_context templates)
- Any brain signal YAML can now carry presentation.do_context and get commentary rendered during ANALYZE
- brain health and audit validate template syntax for new do_context entries

---
*Phase: 115-contract-enforcement-traceability-gate*
*Completed: 2026-03-18*
