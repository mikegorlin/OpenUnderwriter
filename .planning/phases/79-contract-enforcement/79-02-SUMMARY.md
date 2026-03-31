---
phase: 79-contract-enforcement
plan: 02
subsystem: brain
tags: [manifest, contract-validation, requires, data-dependencies, pydantic]

requires:
  - phase: 79-contract-enforcement/01
    provides: "Contract validator with ContractViolation/ContractReport models"
provides:
  - "ManifestFacet.requires field for declaring data dependencies"
  - "validate_requires_populated function for pre-render data gap diagnostics"
  - "DataWarning model for non-fatal missing-data warnings"
  - "11 representative facets with requires annotations as pattern for Phase 80"
affects: [80-gap-remediation]

tech-stack:
  added: []
  patterns: ["dot-notation path resolution for nested dict traversal", "warning vs violation distinction for soft vs hard contract checks"]

key-files:
  created: []
  modified:
    - src/do_uw/brain/manifest_schema.py
    - src/do_uw/brain/contract_validator.py
    - src/do_uw/brain/output_manifest.yaml
    - tests/brain/test_contract_enforcement.py

key-decisions:
  - "DataWarning is separate from ContractViolation -- missing data is a warning not a contract break"
  - "requires uses dot-notation paths resolved against render context dict"
  - "None, empty list, empty dict, missing key all count as not populated"

patterns-established:
  - "requires block pattern: facets declare data dependencies as dot-notation paths"
  - "validate_requires_populated as pre-render diagnostic (not gating)"

requirements-completed: [ENF-02]

duration: 3min
completed: 2026-03-07
---

# Phase 79 Plan 02: Requires Validation Summary

**ManifestFacet requires field with dot-notation path validation and 11 representative facets annotated**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-07T22:45:43Z
- **Completed:** 2026-03-07T22:48:43Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added optional `requires: list[str]` field to ManifestFacet schema (backwards compatible)
- Implemented `validate_requires_populated` with dot-notation path resolution against render context
- Created `DataWarning` model for non-fatal missing-data diagnostics
- Annotated 11 representative facets across financial, governance, litigation, market, and scoring sections
- 28 tests passing including 3 integration tests against real manifest

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for requires field** - `847e9d9` (test)
2. **Task 1 (GREEN): ManifestFacet.requires + validate_requires_populated** - `7b6b506` (feat)
3. **Task 2: requires blocks on 11 facets + integration tests** - `1e90d35` (feat)

_TDD task had separate RED/GREEN commits._

## Files Created/Modified
- `src/do_uw/brain/manifest_schema.py` - Added requires field to ManifestFacet
- `src/do_uw/brain/contract_validator.py` - Added DataWarning model, validate_requires_populated function, path resolution helpers
- `src/do_uw/brain/output_manifest.yaml` - Added requires blocks to 11 representative facets
- `tests/brain/test_contract_enforcement.py` - 13 new tests (8 unit + 2 facet field + 3 integration)

## Decisions Made
- DataWarning is separate from ContractViolation -- missing data is informational, not a contract break
- Dot-notation path resolution splits on '.' and traverses nested dicts
- None, empty list, empty dict, empty string, and missing keys all count as "not populated"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- requires pattern established; Phase 80 gap remediation can complete remaining facets
- validate_requires_populated is callable from the render pipeline for pre-render diagnostics
- All existing manifest consumers unaffected (backwards compatible default)

---
*Phase: 79-contract-enforcement*
*Completed: 2026-03-07*
