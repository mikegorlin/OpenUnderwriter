---
phase: 84-manifest-section-elimination
plan: 01
subsystem: brain
tags: [manifest, pydantic, yaml, signal-groups, v3-architecture]

requires:
  - phase: 82-signal-schema-v3
    provides: "signal_class/group fields on all 476 signals"
provides:
  - "ManifestGroup model (5 fields: id, name, template, render_as, requires)"
  - "collect_signals_by_group() helper for signal self-selection"
  - "Evolved output_manifest.yaml using groups (not facets)"
  - "Backward-compat facets->groups auto-population in ManifestSection"
affects: [84-02, 84-03, 84-04, render-pipeline, brain-audit, chain-validation]

tech-stack:
  added: []
  patterns: ["expand-and-contract migration: groups primary, facets backward-compat"]

key-files:
  created:
    - tests/brain/test_signal_group_resolution.py
  modified:
    - src/do_uw/brain/manifest_schema.py
    - src/do_uw/brain/output_manifest.yaml
    - src/do_uw/brain/chain_validator.py
    - src/do_uw/brain/contract_validator.py
    - src/do_uw/brain/brain_audit.py
    - tests/brain/test_manifest_schema.py
    - tests/brain/test_brain_contract.py
    - tests/brain/test_contract_enforcement.py

key-decisions:
  - "Backward-compat detection uses has_facet_signals (not has_groups) to distinguish legacy test manifests from v3"
  - "Auto-populate groups from facets only when groups empty (one-way: facets->groups, not reverse)"
  - "get_facet_order returns group IDs when groups present, maintaining API compatibility"

patterns-established:
  - "groups-or-facets pattern: all consumers check section.groups first, fall back to section.facets"
  - "Signal self-selection: collect_signals_by_group reads signal.group field, not manifest signal lists"

requirements-completed: [MANIF-01, MANIF-02]

duration: 21min
completed: 2026-03-08
---

# Phase 84 Plan 01: Manifest Schema Evolution Summary

**ManifestGroup model with 5 fields replaces ManifestFacet as primary grouping unit; output_manifest.yaml evolved to groups with signal self-selection; all 5 consumers updated**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-08T07:25:14Z
- **Completed:** 2026-03-08T07:46:22Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- ManifestGroup model (id, name, template, render_as, requires) with extra="forbid" validation
- ManifestSection.groups as primary field with backward-compat facets->groups auto-population
- output_manifest.yaml transformed: 100 facets -> 100 groups, data_type and signals removed
- collect_signals_by_group() correctly maps 476 signals across 54 groups
- All 5 manifest consumers updated (chain_validator, contract_validator, brain_audit, tests)
- 43 manifest+signal tests pass; 795 brain tests pass; 574 render tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ManifestGroup model and evolve ManifestSection** - `9b262ab` (feat, TDD)
2. **Task 2: Evolve manifest YAML and add signal self-selection tests** - `00034c0` (feat)

## Files Created/Modified
- `src/do_uw/brain/manifest_schema.py` - ManifestGroup model, collect_signals_by_group, backward-compat validator
- `src/do_uw/brain/output_manifest.yaml` - 100 groups (was facets), no data_type/signals fields
- `src/do_uw/brain/chain_validator.py` - _build_facet_signal_map uses collect_signals_by_group for v3
- `src/do_uw/brain/contract_validator.py` - Template agreement, signal refs, requires all use groups
- `src/do_uw/brain/brain_audit.py` - Signal-to-section mapping via group membership
- `tests/brain/test_manifest_schema.py` - 14 new tests for ManifestGroup, backward-compat, collect
- `tests/brain/test_signal_group_resolution.py` - 6 tests for signal self-selection into groups
- `tests/brain/test_brain_contract.py` - Read groups key from YAML (was facets)
- `tests/brain/test_contract_enforcement.py` - Updated orphaned signals, template, requires tests

## Decisions Made
- Backward-compat detection uses `has_facet_signals` (checking if any facet has signal lists) rather than `has_groups` to correctly handle test manifests that auto-populate groups from facets
- Auto-populate is one-directional: facets->groups when groups empty, never groups->facets
- get_facet_order returns group IDs when groups present, maintaining API compatibility for callers

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed chain_validator reading empty facets**
- **Found during:** Task 2 (manifest YAML evolution)
- **Issue:** _build_facet_signal_map read section.facets which were now empty, causing all chains to appear broken
- **Fix:** Updated to use collect_signals_by_group for v3 manifests, with has_facet_signals detection for legacy
- **Files modified:** src/do_uw/brain/chain_validator.py
- **Verification:** 14 chain_validator tests pass
- **Committed in:** 00034c0

**2. [Rule 3 - Blocking] Fixed contract_validator template/signal/requires checks**
- **Found during:** Task 2 (manifest YAML evolution)
- **Issue:** validate_facet_template_agreement, validate_signal_references, validate_requires_populated all iterated empty section.facets
- **Fix:** Updated all three functions to use section.groups (preferred) or section.facets (legacy)
- **Files modified:** src/do_uw/brain/contract_validator.py
- **Verification:** All contract enforcement tests pass
- **Committed in:** 00034c0

**3. [Rule 3 - Blocking] Fixed brain_audit signal-to-section mapping**
- **Found during:** Task 2 (manifest YAML evolution)
- **Issue:** Audit report built facet_signal_ids from empty section.facets, making all signals appear orphaned
- **Fix:** Updated to use collect_signals_by_group and group membership for section mapping
- **Files modified:** src/do_uw/brain/brain_audit.py
- **Verification:** Brain audit tests pass
- **Committed in:** 00034c0

**4. [Rule 3 - Blocking] Fixed test_brain_contract YAML reading**
- **Found during:** Task 2 (manifest YAML evolution)
- **Issue:** Test read raw YAML looking for 'facets' key which was now 'groups'
- **Fix:** Updated to read both 'groups' and 'facets' keys
- **Files modified:** tests/brain/test_brain_contract.py
- **Verification:** Contract test passes
- **Committed in:** 00034c0

**5. [Rule 3 - Blocking] Fixed test_contract_enforcement manifest consumers**
- **Found during:** Task 2 (manifest YAML evolution)
- **Issue:** Tests iterated section.facets for orphaned signals, template checks, requires validation
- **Fix:** Updated to use section.groups and collect_signals_by_group
- **Files modified:** tests/brain/test_contract_enforcement.py
- **Verification:** All 795 brain tests pass
- **Committed in:** 00034c0

---

**Total deviations:** 5 auto-fixed (all Rule 3 - blocking)
**Impact on plan:** All auto-fixes necessary for consumers to work with the evolved manifest. The plan identified manifest_schema.py and output_manifest.yaml as files_modified but underestimated the consumer surface area. No scope creep -- all fixes are minimal backward-compat updates.

## Issues Encountered
None beyond the deviation fixes above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ManifestGroup is the primary grouping unit across the manifest
- All existing consumers work with both groups (v3) and facets (legacy)
- Ready for Plan 02 (consumer migration to use groups directly)
- Key API: `section.groups` for iteration, `collect_signals_by_group()` for signal resolution

---
*Phase: 84-manifest-section-elimination*
*Completed: 2026-03-08*
