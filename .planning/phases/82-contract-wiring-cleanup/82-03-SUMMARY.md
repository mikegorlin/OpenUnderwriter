---
phase: 82-contract-wiring-cleanup
plan: 03
subsystem: brain
tags: [signal-architecture, v3, consumer-migration, contract-enforcement]

requires:
  - phase: 82-02
    provides: "All 476 signal YAML files migrated to v3 schema with signal_class/group"
provides:
  - "All production code consumers read signal_class instead of type"
  - "All production code consumers read group instead of facet"
  - "Old type and facet fields removed from BrainSignalEntry Pydantic schema"
  - "All test files use v3 fields exclusively (no dual-mode)"
  - "CI contract test enforces v3 fields on all ACTIVE signals"
  - "754 brain tests + 782 total signal tests passing"
affects: [82-04, 83, 84]

tech-stack:
  added: []
  patterns:
    - "signal_class replaces type for foundational/evaluative/inference classification"
    - "group replaces facet for signal-to-section organization"

key-files:
  created: []
  modified:
    - "src/do_uw/stages/analyze/signal_engine.py"
    - "src/do_uw/stages/analyze/signal_disposition.py"
    - "src/do_uw/brain/chain_validator.py"
    - "src/do_uw/brain/brain_signal_schema.py"
    - "src/do_uw/brain/brain_unified_loader.py"
    - "src/do_uw/cli_brain_trace.py"
    - "tests/brain/test_brain_contract.py"
    - "tests/brain/test_chain_validator.py"
    - "tests/brain/test_signal_disposition.py"
    - "tests/knowledge/test_enriched_roundtrip.py"

key-decisions:
  - "Removed type and facet from BrainSignalEntry schema (not just deprecated -- fully removed)"
  - "brain_unified_loader inference no longer checks type field (v3 migration complete, all signals have signal_class)"
  - "TestFacetIntegrity removed entirely (section YAML elimination in Phase 84 makes it obsolete)"
  - "TestSignalFacetOrGroupAssignment merged into TestSignalDisplaySpec (group check in V3 TestSignalGroupAssignment)"

patterns-established:
  - "signal_class is the sole field for foundational/evaluative/inference classification"
  - "group is the sole field for signal-to-manifest organization"

requirements-completed: [SCHEMA-05, SCHEMA-07]

duration: 14min
completed: 2026-03-08
---

# Phase 82 Plan 03: Consumer Wiring Cleanup Summary

**Updated all production and test consumers from deprecated type/facet fields to v3 signal_class/group fields, removed old fields from schema, 782 tests passing with zero stale references**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-08T06:10:38Z
- **Completed:** 2026-03-08T06:24:43Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- All 6 production files updated: signal_engine, signal_disposition, chain_validator, brain_signal_schema, brain_unified_loader, cli_brain_trace
- Old `type` and `facet` field definitions removed from BrainSignalEntry Pydantic schema
- 6 test files updated to v3 fields exclusively, TestFacetIntegrity removed
- 782 signal-related tests pass, 754 brain tests pass, zero stale references

## Task Commits

Each task was committed atomically:

1. **Task 1: Update all production code consumers** - `a0934b5` (feat)
2. **Task 2: Update all test files and enforce v3 contract** - `0f0d2cc` (test)

## Files Created/Modified
- `src/do_uw/stages/analyze/signal_engine.py` - foundational skip uses signal_class
- `src/do_uw/stages/analyze/signal_disposition.py` - foundational gap check uses signal_class
- `src/do_uw/brain/chain_validator.py` - all signal.type changed to signal.signal_class
- `src/do_uw/brain/brain_signal_schema.py` - type and facet field definitions removed
- `src/do_uw/brain/brain_unified_loader.py` - removed type-based inference
- `src/do_uw/cli_brain_trace.py` - all facet display changed to group
- `tests/brain/test_brain_contract.py` - removed dual-mode, removed TestFacetIntegrity
- `tests/brain/test_chain_validator.py` - fixture uses signal_class/group
- `tests/brain/test_signal_disposition.py` - fixture uses signal_class
- `tests/knowledge/test_enriched_roundtrip.py` - foundational check uses signal_class

## Decisions Made
- Fully removed `type` and `facet` from BrainSignalEntry schema rather than deprecating. Since migration is complete and extra="allow" means stray YAML fields won't crash, removing is cleaner.
- Removed TestFacetIntegrity class since section YAML is scheduled for elimination in Phase 84. The manifest-based TestSignalGroupAssignment replaces it.
- brain_unified_loader's type->signal_class inference removed since all 476 YAMLs now have explicit signal_class.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] test_signal_disposition.py needed signal_class update**
- **Found during:** Task 1 verification
- **Issue:** test_signal_disposition.py fixture used `"type": signal_type` but production code now checks `signal_class`
- **Fix:** Updated fixture to use `signal_class` parameter and dict key
- **Files modified:** tests/brain/test_signal_disposition.py
- **Committed in:** 0f0d2cc (Task 2 commit)

**2. [Rule 1 - Bug] chain_validator integration test expected "evaluate" not "evaluative"**
- **Found during:** Task 2 verification
- **Issue:** test_single_chain_real_signal asserted `signal_type == "evaluate"` but v3 uses "evaluative"
- **Fix:** Updated assertion to match v3 signal_class value
- **Files modified:** tests/brain/test_chain_validator.py
- **Committed in:** 0f0d2cc (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for test correctness with new v3 field names. No scope creep.

## Issues Encountered
- Pre-existing uncommitted changes in brain_audit.py and cli_brain_health.py from another session. Ignored (not staged).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All consumers use v3 fields exclusively -- ready for Phase 82-04 (validation strategy)
- Phase 84 (section YAML elimination) can now safely remove section YAML files since no production code references `facet` field
- Chain validator uses signal_class for foundational classification

---
*Phase: 82-contract-wiring-cleanup*
*Completed: 2026-03-08*
