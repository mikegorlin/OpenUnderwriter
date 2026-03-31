---
phase: 103-schema-foundation
plan: 04
subsystem: brain
tags: [yaml, pydantic, rap-taxonomy, evaluation-mechanism, ci-gate, schema-validation]

# Dependency graph
requires:
  - phase: 103-01
    provides: "BrainSignalEntry schema with rap_class, epistemology, evaluation.mechanism fields (Optional)"
  - phase: 103-03
    provides: "Epistemology blocks on all 514 signals"
  - phase: 102-01
    provides: "rap_signal_mapping.yaml with H/A/E classification for all 514 signals"
provides:
  - "All 514 signals annotated with rap_class, rap_subcategory, evaluation.mechanism"
  - "CI gate test validating schema compliance on every signal"
  - "v7.0 fields (rap_class, rap_subcategory, epistemology, evaluation.mechanism) are REQUIRED in BrainSignalEntry"
affects: [104-signal-wiring, 105-render-signal-binding, 110-advanced-evaluation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CI gate tests for schema enforcement (pytest mark: ci)"
    - "Required Pydantic fields for v7.0 taxonomy (no Optional on rap_class, epistemology, evaluation.mechanism)"

key-files:
  created:
    - "tests/brain/test_schema_validation_ci.py"
  modified:
    - "src/do_uw/brain/brain_signal_schema.py"
    - "src/do_uw/brain/signals/**/*.yaml (52 files)"
    - "tests/brain/test_yaml_schemas.py"
    - "tests/brain/test_chain_validator.py"
    - "tests/brain/test_brain_unified_loader.py"
    - "tests/brain/test_brain_correlation.py"
    - "pyproject.toml"

key-decisions:
  - "Tightened v7.0 fields to required (not Optional) in Pydantic schema -- future signals fail at load time if missing"
  - "Mechanism classification: threshold (default ~80%), peer_comparison (peer_xbrl + stock comparisons), trend (temporal/yoy/warn)"
  - "No conjunction/absence/contextual mechanisms assigned -- reserved for Phase 110"
  - "Registered 'ci' pytest marker for CI gate tests"

patterns-established:
  - "CI gate pattern: module-scoped fixtures for signal loading, @pytest.mark.ci for CI-only tests"
  - "Schema enforcement pattern: v7.0 fields required at Pydantic level, not just CI test level"

requirements-completed: [SCHEMA-07, SCHEMA-08]

# Metrics
duration: 8min
completed: 2026-03-15
---

# Phase 103 Plan 04: RAP Class + Evaluation Mechanism + CI Gate Summary

**All 514 signals annotated with rap_class (H/A/E from mapping), evaluation.mechanism (threshold/peer_comparison/trend), and CI gate test enforcing complete v7.0 schema compliance with required Pydantic fields**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-15T04:21:03Z
- **Completed:** 2026-03-15T04:29:00Z
- **Tasks:** 2
- **Files modified:** 59

## Accomplishments
- Injected rap_class + rap_subcategory from rap_signal_mapping.yaml into all 514 signals across 52 YAML files
- Added evaluation.mechanism to all 514 signals (threshold: ~80%, peer_comparison: peer_xbrl/stock, trend: temporal/yoy/warn)
- Created CI gate test (8 tests) validating rap_class, rap_subcategory, epistemology, evaluation.mechanism, Pydantic compliance, signal count, and distribution
- Tightened BrainSignalEntry schema: rap_class, rap_subcategory, epistemology now REQUIRED (not Optional)
- Tightened EvaluationSpec schema: mechanism now REQUIRED (not Optional)
- Updated 4 test files with required v7.0 fields in test fixtures
- All 896 brain tests pass, all 8 CI gate tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add rap_class + evaluation.mechanism to all 514 signals** - `4e39cd5` (feat)
2. **Task 2: CI gate test + tighten v7.0 schema fields** - `e0d00f3` (feat)

## Files Created/Modified
- `tests/brain/test_schema_validation_ci.py` - 8 CI gate tests validating all v7.0 fields on all signals
- `src/do_uw/brain/brain_signal_schema.py` - Tightened rap_class, rap_subcategory, epistemology to required; mechanism to required
- `src/do_uw/brain/signals/**/*.yaml` (52 files) - Added rap_class, rap_subcategory, evaluation.mechanism
- `tests/brain/test_yaml_schemas.py` - Updated _minimal_signal with v7.0 required fields
- `tests/brain/test_chain_validator.py` - Updated _make_signal with v7.0 required fields
- `tests/brain/test_brain_unified_loader.py` - Updated test signal dicts with v7.0 required fields
- `tests/brain/test_brain_correlation.py` - Updated test signal construction with v7.0 required fields
- `pyproject.toml` - Registered 'ci' pytest marker

## Decisions Made
- Tightened v7.0 fields to required (not Optional) in Pydantic schema. Any new signal added without rap_class, rap_subcategory, epistemology, or evaluation.mechanism will fail at YAML load time, not just CI test time. This is the strongest enforcement level.
- Classified evaluation mechanisms conservatively: threshold for most signals (~80%), peer_comparison for peer benchmarking signals, trend for temporal/YOY/warning signals. No conjunction/absence/contextual (reserved for Phase 110).
- Used Python automation script for bulk YAML injection (deleted after run). yaml.dump with sort_keys=False to preserve key order.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated 4 test files with now-required v7.0 fields**
- **Found during:** Task 2 (schema tightening)
- **Issue:** Existing tests in test_yaml_schemas.py, test_chain_validator.py, test_brain_unified_loader.py, and test_brain_correlation.py created BrainSignalEntry objects without the now-required rap_class, rap_subcategory, and epistemology fields
- **Fix:** Updated _minimal_signal helpers and individual test signal dicts to include all v7.0 required fields. Changed backward-compat tests to now test that missing fields FAIL validation.
- **Files modified:** tests/brain/test_yaml_schemas.py, tests/brain/test_chain_validator.py, tests/brain/test_brain_unified_loader.py, tests/brain/test_brain_correlation.py
- **Verification:** All 896 brain tests pass
- **Committed in:** e0d00f3 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix for test compatibility)
**Impact on plan:** Necessary fix for schema tightening. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 103 (Schema Foundation) is now COMPLETE. All 3 plans executed.
- All 514 signals have: epistemology, rap_class, rap_subcategory, evaluation.mechanism
- Schema enforced at Pydantic level (required fields) + CI gate (8 tests)
- Ready for Phase 104 (Signal Wiring), 105 (Render-Signal Binding), and 106 (Research) to proceed in parallel

## Self-Check: PASSED

- tests/brain/test_schema_validation_ci.py: FOUND (207 lines, above 50 minimum)
- src/do_uw/brain/brain_signal_schema.py: FOUND
- 103-04-SUMMARY.md: FOUND
- Commit 4e39cd5: FOUND
- Commit e0d00f3: FOUND

---
*Phase: 103-schema-foundation*
*Completed: 2026-03-15*
