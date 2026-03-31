---
phase: 55-declarative-mapping-structured-evaluation
plan: 01
subsystem: analyze
tags: [declarative-mapper, structured-evaluator, field-registry, sourced-value, v2-signals]

# Dependency graph
requires:
  - phase: 54-signal-contract-v2
    provides: "V2 signal schema (EvaluationSpec, EvaluationThreshold), field registry (15 entries), V2 dispatch stub"
provides:
  - "declarative_mapper.py: resolve_field(), resolve_path(), map_v2_signal() for V2 signal data resolution"
  - "structured_evaluator.py: evaluate_v2() with 8 operators and clear_conditions"
  - "field_registry_functions.py: COMPUTED_FUNCTIONS dict with 8 pure function implementations"
  - "field_registry.yaml expanded to 17 entries (added cash_ratio, cash_burn_months)"
affects: [55-02-shadow-evaluation, 55-03-fin-liq-migration, signal-engine-v2-dispatch]

# Tech tracking
tech-stack:
  added: []
  patterns: ["SourcedValue duck-type detection via hasattr (not isinstance)", "COMPUTED function dispatch with pre-resolved args", "Structured {op, value, label} threshold evaluation replacing regex parsing"]

key-files:
  created:
    - src/do_uw/stages/analyze/declarative_mapper.py
    - src/do_uw/stages/analyze/structured_evaluator.py
    - src/do_uw/brain/field_registry_functions.py
    - tests/stages/analyze/test_declarative_mapper_v2.py
    - tests/stages/analyze/test_structured_evaluator.py
  modified:
    - src/do_uw/brain/field_registry.py
    - src/do_uw/brain/field_registry.yaml
    - tests/brain/test_field_registry.py

key-decisions:
  - "SourcedValue detected by duck-typing (hasattr for value/source/confidence) -- isinstance fails with Pydantic generics at runtime"
  - "COMPUTED_FUNCTIONS in dedicated field_registry_functions.py (not field_registry.py) -- keeps loader under 150 lines"
  - "contains operator evaluated on raw string value before numeric conversion -- string ops don't require float()"
  - "clear_conditions handled as evaluation_spec extension (not EvaluationSpec Pydantic change) -- avoids Phase 54 schema modification"

patterns-established:
  - "resolve_path() traversal: root dispatch -> segment-by-segment getattr -> SourcedValue unwrap at each step"
  - "evaluate_v2() flow: missing check -> clear_conditions -> string ops -> numeric conversion -> threshold iteration"
  - "COMPUTED functions receive pre-resolved values, not paths -- pure functions with no state access"

requirements-completed: [MAP-01, MAP-02, EVAL-01, EVAL-02, EVAL-03]

# Metrics
duration: 50min
completed: 2026-03-01
---

# Phase 55 Plan 01: Declarative Mapper + Structured Evaluator Summary

**Declarative field resolution via dotted-path traversal with SourcedValue auto-unwrap, and operator-based threshold evaluation replacing legacy regex parsing**

## Performance

- **Duration:** 50 min
- **Started:** 2026-03-01T17:37:53Z
- **Completed:** 2026-03-01T18:27:53Z
- **Tasks:** 2 (both TDD)
- **Files created:** 5
- **Files modified:** 3

## Accomplishments

- Built `declarative_mapper.py` with SourcedValue-aware dotted-path traversal that resolves DIRECT_LOOKUP and COMPUTED fields from the field registry
- Built `structured_evaluator.py` with all 8 comparison operators ({op, value, label} thresholds), clear_conditions for qualitative values, and proper edge case handling
- Created `field_registry_functions.py` with 8 COMPUTED function implementations (count_items, count_active_scas, compute_board_independence_pct, compute_cash_burn_months, etc.)
- Expanded field_registry.yaml from 15 to 17 entries (added cash_ratio and cash_burn_months for FIN.LIQ migration)
- 70 new tests passing (14 mapper + 28 evaluator + 6 registry + 22 existing registry), zero regressions

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Build declarative_mapper.py** - `4763085` (test), `11031f4` (feat)
   - RED: 14 failing tests for resolve_field, resolve_path, map_v2_signal
   - GREEN: declarative_mapper.py, field_registry_functions.py, field_registry.py updates, field_registry.yaml additions

2. **Task 2: Build structured_evaluator.py** - `a40ae2c` (test), `4973219` (feat)
   - RED: 28 failing tests for operators, thresholds, edge cases, qualitative clear
   - GREEN: structured_evaluator.py with evaluate_v2(), _compare(), clear_conditions

## Files Created/Modified

- `src/do_uw/stages/analyze/declarative_mapper.py` (188 lines) -- resolve_field(), resolve_path(), map_v2_signal() for V2 signal data resolution
- `src/do_uw/stages/analyze/structured_evaluator.py` (225 lines) -- evaluate_v2() with 8 operators and clear_conditions support
- `src/do_uw/brain/field_registry_functions.py` (166 lines) -- COMPUTED_FUNCTIONS dict with 8 pure function implementations
- `src/do_uw/brain/field_registry.py` (145 lines) -- Added get_computed_function() helper
- `src/do_uw/brain/field_registry.yaml` (125 lines) -- Added cash_ratio and cash_burn_months entries (17 total)
- `tests/stages/analyze/test_declarative_mapper_v2.py` (342 lines) -- 14 tests for V2 mapper
- `tests/stages/analyze/test_structured_evaluator.py` (485 lines) -- 28 tests for V2 evaluator
- `tests/brain/test_field_registry.py` (320 lines) -- Added 6 Phase 55 tests for new entries and COMPUTED_FUNCTIONS

## Decisions Made

1. **SourcedValue duck-type detection** -- Used `hasattr(obj, "value") and hasattr(obj, "source") and hasattr(obj, "confidence")` instead of `isinstance(obj, SourcedValue)`. Pydantic generics fail isinstance at runtime. This matches the established `_safe_sourced()` pattern in signal_mappers.py.

2. **COMPUTED_FUNCTIONS in dedicated file** -- Created `field_registry_functions.py` (~166 lines) to keep `field_registry.py` focused on the registry loader (now 145 lines). Functions are pure -- receive pre-resolved arg values, no state access.

3. **String contains operator handling** -- The `contains` operator evaluates on raw string values before numeric conversion. This required a `_compare_string()` path separate from the numeric `_compare()` path, with `has_string_ops` detection before the numeric conversion gate.

4. **clear_conditions as evaluation_spec extension** -- Rather than modifying the Phase 54 `EvaluationSpec` Pydantic schema, `clear_conditions` is handled as an optional dict key in the evaluation_spec. This avoids a schema migration while enabling the cash_burn "Profitable" qualitative clear pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] String contains operator was SKIPPED instead of TRIGGERED**
- **Found during:** Task 2 (structured evaluator GREEN phase)
- **Issue:** The `contains` operator test passed "text with keyword inside" but got SKIPPED because the string value failed `float()` conversion and was treated as non-numeric
- **Fix:** Added `has_string_ops` detection that checks if any threshold uses `contains` operator. For `contains` ops, uses `_compare_string()` on raw value before numeric conversion gate. Non-numeric values are only SKIPPED if no string-based operators exist.
- **Files modified:** `src/do_uw/stages/analyze/structured_evaluator.py`
- **Verification:** All 28 evaluator tests pass including `test_contains`
- **Committed in:** `4973219` (part of Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correctness of the `contains` operator. No scope creep.

## Issues Encountered

- 2 pre-existing test failures in full suite (test_brain_enrich.py count mismatch 99 vs 98, test_regression_baseline.py missing baseline file). Both confirmed pre-existing by running on unmodified code. Logged to `deferred-items.md`. Zero failures caused by Phase 55 changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- declarative_mapper.py and structured_evaluator.py are ready for wiring into signal_engine.py (Plan 55-02: shadow evaluation)
- field_registry.yaml has all entries needed for FIN.LIQ prefix migration (Plan 55-03)
- COMPUTED_FUNCTIONS dict is extensible -- add new functions by adding entries to the dict
- All exports are clean: `resolve_field`, `map_v2_signal`, `evaluate_v2`

## Self-Check: PASSED

- All 9 files verified present on disk
- All 4 task commits verified in git log (4763085, 11031f4, a40ae2c, 4973219)
- 70 plan-specific tests passing
- Zero regressions in analyze+brain test suite (711 passed, 2 pre-existing failures excluded)

---
*Phase: 55-declarative-mapping-structured-evaluation*
*Completed: 2026-03-01*
