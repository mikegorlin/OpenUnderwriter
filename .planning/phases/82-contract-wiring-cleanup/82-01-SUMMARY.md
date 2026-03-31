---
phase: 82-contract-wiring-cleanup
plan: 01
subsystem: brain
tags: [pydantic, schema, signal-architecture, v3, contract-tests]

requires:
  - phase: none
    provides: "Existing BrainSignalEntry v2 schema with 476 signals"
provides:
  - "BrainSignalEntry with v3 fields: group, depends_on, field_path, signal_class"
  - "BrainSignalProvenance with audit trail: formula, threshold_provenance, render_target, data_source"
  - "SignalDependency and ThresholdProvenance models"
  - "BrainLoader v3 field inference (signal_class from type/work_type)"
  - "Contract test stubs defining v3 migration target (6 skip-marked, 4 immediate)"
affects: [82-02, 82-03, 82-04, 83, 84]

tech-stack:
  added: []
  patterns:
    - "V3 expand-and-contract: new fields coexist with v2, dual-mode helpers (_is_foundational)"
    - "Auto-inference at load time: signal_class derived from v2 type/work_type"
    - "Contract test stubs with skip markers as migration targets"

key-files:
  created: []
  modified:
    - "src/do_uw/brain/brain_signal_schema.py"
    - "src/do_uw/brain/brain_unified_loader.py"
    - "tests/brain/test_brain_contract.py"

key-decisions:
  - "signal_class default is 'evaluative' (not 'evaluate') to distinguish from v2 type field"
  - "ThresholdProvenance uses extra=allow for forward compatibility"
  - "SignalDependency uses extra=forbid to catch YAML typos"
  - "Auto-inference uses regex for COMP.* and FIN.FORENSIC.*composite patterns"

patterns-established:
  - "Dual-mode foundational check: _is_foundational() checks both type=='foundational' and signal_class=='foundational'"
  - "_active_signals_validated() loads through BrainLoader for v3 inference in tests"

requirements-completed: [SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04, SCHEMA-05, SCHEMA-08]

duration: 4min
completed: 2026-03-08
---

# Phase 82 Plan 01: Schema Extension Summary

**Extended BrainSignalEntry with 4 v3 fields (group, depends_on, field_path, signal_class) + 4 provenance audit fields, with auto-inference from v2 type and contract test stubs defining migration target**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T05:35:01Z
- **Completed:** 2026-03-08T05:39:02Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- BrainSignalEntry extended with signal_class (foundational/evaluative/inference), group, depends_on, field_path
- BrainSignalProvenance extended with formula, threshold_provenance, render_target, data_source
- BrainLoader auto-infers signal_class: 26 foundational, 23 inference from v2 fields
- All 476 signals load without error through extended schema
- 5 contract test classes (10 tests: 4 pass now, 6 skip-marked for migration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend BrainSignalEntry with v3 fields and expanded provenance** - `024e64e` (feat)
2. **Task 2: Update BrainLoader to warn on missing v3 fields and infer defaults** - `022a975` (feat)
3. **Task 3: Create v3 contract test stubs in test_brain_contract.py** - `804cf0d` (test)

## Files Created/Modified
- `src/do_uw/brain/brain_signal_schema.py` - Added SignalDependency, ThresholdProvenance models; v3 fields on BrainSignalEntry; audit trail fields on BrainSignalProvenance
- `src/do_uw/brain/brain_unified_loader.py` - Added _warn_v3_fields() with signal_class auto-inference and v3 coverage logging
- `tests/brain/test_brain_contract.py` - Added 5 v3 test classes, dual-mode helpers, renamed TestSignalFacetAssignment

## Decisions Made
- signal_class uses "evaluative" (not "evaluate") to avoid confusion with v2 type field values
- Auto-inference maps type=="foundational" to signal_class=="foundational" and work_type=="infer" or COMP.*/FIN.FORENSIC.*composite to "inference"
- ThresholdProvenance allows extra fields for forward compatibility; SignalDependency forbids extra to catch typos

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in test_v2_migration.py (FIN.PEER.revenue_bottom_quartile missing acquisition) -- confirmed pre-existing, not caused by this plan's changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Schema foundation ready for Plan 82-02 (v3 migration of signal YAML files)
- Contract test stubs define exact success criteria for migration
- BrainLoader inference ensures backward compatibility during incremental migration

---
*Phase: 82-contract-wiring-cleanup*
*Completed: 2026-03-08*
