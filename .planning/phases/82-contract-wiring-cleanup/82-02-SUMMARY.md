---
phase: 82-contract-wiring-cleanup
plan: 02
subsystem: brain
tags: [yaml, migration, ruamel, signal-architecture, v3, schema-version]

requires:
  - phase: 82-01
    provides: "BrainSignalEntry v3 fields (group, depends_on, field_path, signal_class) + contract test stubs"
provides:
  - "All 476 signal YAML files migrated to v3 schema (schema_version=3)"
  - "brain_migrate_v3.py migration script with --dry-run support"
  - "group field: 100% coverage using section YAML + prefix inference"
  - "signal_class: 26 foundational, 422 evaluative, 28 inference"
  - "field_path: 337/476 populated from data_strategy.field_key"
  - "depends_on: 55/476 traced through field registry"
  - "Old type/facet fields removed from all signal YAML"
  - "Provenance expanded with data_source, threshold_provenance, render_target"
affects: [82-03, 82-04, 83, 84]

tech-stack:
  added: []
  patterns:
    - "ruamel.yaml round-trip editing for comment-preserving YAML migration"
    - "Group remap table bridges section YAML short names to manifest prefixed names"
    - "Longest-prefix-match for signal-to-group inference (341 signals)"

key-files:
  created:
    - "src/do_uw/brain/brain_migrate_v3.py"
  modified:
    - "src/do_uw/brain/signals/**/*.yaml (all 36 files)"
    - "tests/brain/test_brain_contract.py"
    - "tests/brain/test_foundational_coverage.py"
    - "tests/brain/test_v2_migration.py"
    - "tests/brain/test_v2_schema.py"
    - "tests/test_signal_forensic_wiring.py"

key-decisions:
  - "Group assignment: 135 explicit from section YAML, 341 from prefix-based inference, 0 unresolved"
  - "Group remap table bridges 11 section YAML short names to manifest prefixed equivalents"
  - "Inference class: 28 signals (21 work_type=infer + 7 composite patterns)"
  - "field_path uses registry keys (not direct paths) to minimize risk per CONTEXT.md"
  - "BASE.* signals classified as foundational by ID prefix for idempotent re-runs"

patterns-established:
  - "_PREFIX_GROUP_MAP: longest-match dictionary for signal-to-group assignment"
  - "_GROUP_REMAP: bridges section YAML and manifest group ID naming conventions"
  - "Idempotent migration: detects already-migrated signals via signal_class field"

requirements-completed: [SCHEMA-06]

duration: 26min
completed: 2026-03-08
---

# Phase 82 Plan 02: V3 Migration Summary

**Migrated all 476 signal YAML files to v3 schema: group, signal_class, field_path, depends_on, expanded provenance -- with ruamel.yaml comment preservation and 752 brain tests passing**

## Performance

- **Duration:** 26 min
- **Started:** 2026-03-08T05:41:05Z
- **Completed:** 2026-03-08T06:07:32Z
- **Tasks:** 2
- **Files modified:** 52

## Accomplishments
- All 476 signal YAML files migrated to schema_version 3 with v3 fields populated
- Old `type` and `facet` fields removed, replaced by `signal_class` and `group`
- Migration script (brain_migrate_v3.py) is idempotent with --dry-run/--stats/--verbose modes
- Contract tests un-skipped: all 19 pass; 752 total brain tests pass
- 5 consumer test files updated for type->signal_class and facet->group renames

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain_migrate_v3.py migration script** - `0d0976e` (feat)
2. **Task 2: Execute migration and validate all 476 signals** - `84d945c` (feat)

## Files Created/Modified
- `src/do_uw/brain/brain_migrate_v3.py` - V3 migration script with lookup builders, group inference, class inference, ruamel.yaml round-trip editing
- `src/do_uw/brain/signals/**/*.yaml` (36 files) - All signals updated with v3 fields, old fields removed
- `tests/brain/test_brain_contract.py` - Skip markers removed, manifest test fixed (groups->facets key)
- `tests/brain/test_foundational_coverage.py` - type->signal_class check, required fields updated
- `tests/brain/test_v2_migration.py` - V2 fixture filter, source types, foundational signal handling
- `tests/brain/test_v2_schema.py` - schema_version validation expanded to include v3
- `tests/test_signal_forensic_wiring.py` - facet->group field check

## Decisions Made
- Group assignment uses 3-tier resolution: explicit section YAML mapping (135), prefix inference (341), facet fallback (0)
- 11 group IDs require remapping between section YAML short names and manifest prefixed names (e.g., `prior_litigation` -> `executive_prior_litigation`)
- Inference class assigned to 28 signals: 21 with work_type=infer plus 7 composite patterns (fis_composite, dechow_f_score, etc.)
- field_path populated using registry keys per CONTEXT.md discretion (minimize risk approach)
- BASE.* signals detected as foundational by ID prefix to ensure idempotent re-runs after type field removal

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Group ID mismatch between section YAML and manifest**
- **Found during:** Task 2 (contract test validation)
- **Issue:** Section YAMLs use short group IDs (e.g., `prior_litigation`) but manifest uses prefixed IDs (e.g., `executive_prior_litigation`). 11 group IDs affected.
- **Fix:** Added _GROUP_REMAP translation table in migration script, applied during group resolution
- **Files modified:** src/do_uw/brain/brain_migrate_v3.py
- **Committed in:** 84d945c

**2. [Rule 1 - Bug] Three BASE.MARKET signals had empty facet field**
- **Found during:** Task 2 (migration execution)
- **Issue:** BASE.MARKET.stock_price, BASE.MARKET.institutional, BASE.MARKET.insider_trading had no facet value, causing unresolved group assignment
- **Fix:** Added explicit prefix mappings for BASE.MARKET.* signals in _PREFIX_GROUP_MAP
- **Files modified:** src/do_uw/brain/brain_migrate_v3.py
- **Committed in:** 84d945c

**3. [Rule 3 - Blocking] Consumer test updates for type/facet removal**
- **Found during:** Task 2 (brain test suite validation)
- **Issue:** 5 test files referenced removed `type` and `facet` fields, causing test failures
- **Fix:** Updated all references: type->signal_class, facet->group, schema_version checks, source type lists
- **Files modified:** test_brain_contract.py, test_foundational_coverage.py, test_v2_migration.py, test_v2_schema.py, test_signal_forensic_wiring.py
- **Committed in:** 84d945c

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered
- Migration script exceeded 500-line target (769 lines) due to comprehensive prefix-to-group mapping table. This is acceptable for a one-shot migration tool with 180+ mapping entries.
- Idempotency required special handling: after first run removes `type` field, second run must detect foundational signals by ID prefix (BASE.*) rather than type field value.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 476 signals have v3 fields populated -- ready for Plan 82-03 (consumer updates)
- Contract tests enforce v3 field presence -- any regression will be caught
- Group remap table documents the section YAML vs manifest naming discrepancy for Phase 84 elimination work

---
*Phase: 82-contract-wiring-cleanup*
*Completed: 2026-03-08*
