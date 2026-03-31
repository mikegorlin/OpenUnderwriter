---
phase: 139-contextual-signal-validation
plan: 01
subsystem: analyze
tags: [yaml, signal-validation, annotations, fnmatch, false-positives]

requires:
  - phase: 128-infrastructure-foundation
    provides: signal_results.py SignalResult model with frozen=False
provides:
  - YAML-driven contextual validation engine for TRIGGERED signals
  - annotations field on SignalResult for false-positive context
  - 4 validation rule classes (lifecycle_mismatch, contradicting_indicator, negation, temporal_staleness)
affects: [render, scoring, signal-results, brain-config]

tech-stack:
  added: []
  patterns: [yaml-driven-rule-engine, annotation-not-suppression, fnmatch-pattern-matching]

key-files:
  created:
    - src/do_uw/stages/analyze/contextual_validator.py
    - src/do_uw/brain/config/validation_rules.yaml
    - tests/stages/analyze/test_contextual_validator.py
  modified:
    - src/do_uw/stages/analyze/signal_results.py
    - src/do_uw/stages/analyze/__init__.py

key-decisions:
  - "Annotations are informational only -- never suppress or change signal status"
  - "Zero signal IDs hardcoded in Python; all patterns in YAML via fnmatch"
  - "Validator runs after gap re-evaluation and before composites in pipeline"
  - "SourcedValue auto-unwrap in state path resolver for clean dotted-path navigation"

patterns-established:
  - "YAML validation rules: add new rules without Python changes"
  - "Pipe-separated fnmatch patterns for flexible signal matching"

requirements-completed: [SIG-01, SIG-02, SIG-03, SIG-04, SIG-05, SIG-06, SIG-07]

duration: 5min
completed: 2026-03-28
---

# Phase 139 Plan 01: Contextual Signal Validation Summary

**YAML-driven validation engine that annotates TRIGGERED signals with false-positive context (IPO lifecycle, distress safe zone, negation language, departed executives) without ever changing signal status**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T00:22:55Z
- **Completed:** 2026-03-28T00:28:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added `annotations: list[str]` field to SignalResult model for post-ANALYZE contextual notes
- Created validation_rules.yaml with 4 rule classes covering IPO lifecycle mismatch, financial distress contradiction, evidence negation patterns, and departed executive staleness
- Built contextual_validator.py engine (245 lines) with YAML loading, fnmatch pattern matching, dotted-path state resolution with SourcedValue auto-unwrap, and 4 evaluator types
- Wired validate_signals() into ANALYZE pipeline between gap re-evaluation and composites with non-fatal try/except
- 15 passing tests covering all 7 SIG requirements

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add tests + annotations field + YAML rules** - `1a9f2be6` (test)
2. **Task 1 GREEN: Implement contextual_validator.py** - `a97e954b` (feat)
3. **Task 2: Wire into ANALYZE pipeline** - `5c3f8227` (feat)

## Files Created/Modified
- `src/do_uw/stages/analyze/contextual_validator.py` - YAML-driven validation engine with 4 evaluator types
- `src/do_uw/brain/config/validation_rules.yaml` - 4 declarative validation rules (lifecycle, distress, negation, temporal)
- `tests/stages/analyze/test_contextual_validator.py` - 15 test cases covering all SIG requirements
- `src/do_uw/stages/analyze/signal_results.py` - Added annotations field to SignalResult
- `src/do_uw/stages/analyze/__init__.py` - Pipeline wiring for contextual validation step

## Decisions Made
- Annotations are append-only informational context; status field is NEVER modified (SIG-01/SIG-07)
- All signal ID matching uses fnmatch patterns from YAML; zero signal ID literals in Python (SIG-02)
- SourcedValue objects auto-unwrapped during dotted-path state resolution for clean condition evaluation
- Validator placed after gap re-evaluation (signals have final status) and before composites (composites can inherit annotations)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MagicMock type assignment in tests**
- **Found during:** Task 1 GREEN (test execution)
- **Issue:** `type(mock).__class__ = type(MagicMock)` raises TypeError on Python 3.12
- **Fix:** Removed unnecessary type manipulation; MagicMock already triggers SourcedValue unwrap correctly
- **Files modified:** tests/stages/analyze/test_contextual_validator.py
- **Committed in:** a97e954b

**2. [Rule 1 - Bug] Fixed missing import in monkeypatched test**
- **Found during:** Task 1 GREEN (test execution)
- **Issue:** `test_missing_yaml_file_returns_empty` used `validate_signals` name without importing it in the test function scope
- **Fix:** Added explicit import as `vs` within the test function
- **Files modified:** tests/stages/analyze/test_contextual_validator.py
- **Committed in:** a97e954b

---

**Total deviations:** 2 auto-fixed (2 bugs in test fixtures)
**Impact on plan:** Minimal -- test fixture adjustments only, no design changes.

## Issues Encountered
- Pre-existing test failures in test_inference_evaluator.py (TestSingleValueFallback) and test_narrative_generation.py -- unrelated to this plan, not addressed. Logged as out-of-scope.

## Known Stubs
None -- all functionality is fully implemented and tested.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Contextual validation engine is ready for additional rules (just add YAML entries)
- Rendering layer can consume `annotations` field to display contextual notes to underwriters
- Future plans can add rule classes by extending the evaluator dispatch in contextual_validator.py

---
*Phase: 139-contextual-signal-validation*
*Completed: 2026-03-28*
