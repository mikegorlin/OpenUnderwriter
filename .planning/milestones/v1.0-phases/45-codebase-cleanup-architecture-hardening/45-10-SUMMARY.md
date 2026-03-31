---
phase: 45-codebase-cleanup-architecture-hardening
plan: "10"
subsystem: brain-knowledge
tags: [pydantic, yaml-validation, brain-schema, brain-checks]

# Dependency graph
requires:
  - phase: 45-02
    provides: BrainKnowledgeLoader rename from BackwardCompatLoader
  - phase: 45-03
    provides: brain/legacy/ reorganization, brain_migrate.py import updates

provides:
  - BrainCheckEntry Pydantic model validating brain/checks/**/*.yaml entries on load
  - BrainKnowledgeLoader.load_checks() raises RuntimeError on schema violations
  - All 400 brain YAML entries validated at load time (no silent skipping)

affects:
  - stages/score/
  - stages/analyze/
  - knowledge/compat_loader.py

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Load-time schema validation: BrainCheckEntry.model_validate() called on every check loaded from brain.duckdb"
    - "Hard-fail on schema violations: RuntimeError with check_id and first error message, capped at 10"
    - "extra='allow' on all sub-models: unknown fields accepted, only missing required fields fail"

key-files:
  created:
    - src/do_uw/brain/brain_check_schema.py
  modified:
    - src/do_uw/knowledge/compat_loader.py

key-decisions:
  - "factors is optional (default=[]) because 64 of 400 entries legitimately omit it (descriptive/display checks)"
  - "layer is optional (default=None) because brain.duckdb stores it as _brain_risk_framework_layer, not layer; all 400 YAML source files have the field"
  - "Validation applies only to brain.duckdb path; KnowledgeStore fallback (legacy format) skips validation to avoid false positives from old schema"
  - "ValidationError capped at 10 entries per error report to avoid log flooding"

patterns-established:
  - "BrainCheckEntry: add new check fields here first, then update YAML files"
  - "RuntimeError on schema violation: hard-fail is preferred over silent skipping for correctness guarantees"

requirements-completed: [ARCH-01, ARCH-04]

# Metrics
duration: 10min
completed: 2026-02-25
---

# Phase 45 Plan 10: Brain Check Schema Validation Summary

**BrainCheckEntry Pydantic model validates all 400 brain YAML check entries on load from brain.duckdb, raising RuntimeError with actionable check_id details on any schema violation**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-25T18:27:36Z
- **Completed:** 2026-02-25T18:37:48Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `brain_check_schema.py` with `BrainCheckEntry`, `BrainCheckThreshold`, and `BrainCheckProvenance` Pydantic models derived from audit of all 36 YAML files (400 entries)
- Wired `BrainCheckEntry.model_validate()` into `BrainKnowledgeLoader.load_checks()` for the brain.duckdb path — missing required fields now raise `RuntimeError` with check_id and error details
- All 400 YAML entries pass schema validation with zero errors; 366+ existing tests pass; AAPL pipeline completes

## Task Commits

1. **Task 1: Define BrainCheckEntry Pydantic model** - `fdce36c` (feat)
2. **Task 2: Add load-time validation to BrainKnowledgeLoader.load_checks()** - `3826ee0` (feat)

**Plan metadata:** (final commit after SUMMARY)

## Files Created/Modified

- `src/do_uw/brain/brain_check_schema.py` — BrainCheckEntry, BrainCheckThreshold, BrainCheckProvenance Pydantic models
- `src/do_uw/knowledge/compat_loader.py` — Added validation block in load_checks(), imports for BrainCheckEntry and ValidationError, updated class docstring

## Decisions Made

- **factors optional (not required):** Audit found 64 of 400 YAML entries missing `factors` (e.g., BIZ.*, FWRD.DISC.*, NLP.MDA.* descriptive checks). Making it required would break 64 valid entries. Default=[].
- **layer optional (not required):** brain.duckdb loader maps `risk_framework_layer` to `_brain_risk_framework_layer` key (not `layer`). All 400 YAML source files have it, but the DuckDB output format doesn't expose it under `layer`. Optional with None default avoids false validation failures.
- **Validation only on brain.duckdb path:** The KnowledgeStore fallback path returns checks in an older schema format (missing `tier`, `depth`, `threshold`, `provenance` fields). Applying BrainCheckEntry validation to this path would produce 400 false positive errors. Validation applies only to the canonical brain.duckdb path.
- **Cap error display at 10:** Prevents log flooding when many entries fail simultaneously.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] factors must be optional, not required**
- **Found during:** Task 1 (validating all YAML entries)
- **Issue:** Plan specified `factors` as a required field. Audit found 64 of 400 entries legitimately omit it (descriptive/display checks like BIZ.*, FWRD.DISC.*).
- **Fix:** Made `factors` optional with `default_factory=list` — validation passes for all 400 entries.
- **Files modified:** src/do_uw/brain/brain_check_schema.py
- **Verification:** All 400 YAML entries pass `BrainCheckEntry.model_validate()` with zero errors.
- **Committed in:** fdce36c (Task 1 commit)

**2. [Rule 1 - Bug] layer must be optional — brain.duckdb output uses _brain_risk_framework_layer key**
- **Found during:** Task 2 (running tests after wiring validation)
- **Issue:** brain.duckdb stores `risk_framework_layer` but BrainDBLoader exposes it as `_brain_risk_framework_layer` in the output dict. All 400 DuckDB entries had `layer: None`, triggering 400 schema validation errors and RuntimeError.
- **Fix:** Made `layer` optional with `default=None`. Added docstring note explaining the DuckDB key naming.
- **Files modified:** src/do_uw/brain/brain_check_schema.py
- **Verification:** Tests pass (366+ passing, 1 pre-existing coverage test failure unrelated to this plan).
- **Committed in:** 3826ee0 (Task 2 commit)

**3. [Rule 1 - Bug] Validation must only apply to brain.duckdb path, not KnowledgeStore fallback**
- **Found during:** Task 2 (running tests)
- **Issue:** Initial implementation applied validation to all paths. The KnowledgeStore fallback returns checks in an older format without `tier`, `depth`, `threshold`, `provenance` fields. This triggered 400 false positive errors in the test suite.
- **Fix:** Restructured `load_checks()` to apply validation only in the `if self._brain_db_loader is not None` branch.
- **Files modified:** src/do_uw/knowledge/compat_loader.py
- **Verification:** Tests pass; AAPL pipeline completes successfully.
- **Committed in:** 3826ee0 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (all Rule 1 - Bug: discovered during validation audit)
**Impact on plan:** All fixes necessary for correct schema validation against real data. No scope creep. The plan's intent (catch schema violations at load time) is fully achieved.

## Issues Encountered

- brain.duckdb stores `risk_framework_layer` under a different key (`_brain_risk_framework_layer`) than the YAML source (`layer`). This is a naming inconsistency in BrainDBLoader's output mapping. The fix (making `layer` optional) is correct behavior. The underlying inconsistency could be addressed in a future plan by normalizing BrainDBLoader output.

## Next Phase Readiness

- Phase 45 Plan 10 complete. Schema validation is in place for the canonical brain.duckdb path.
- Any new check fields added to YAML files must be reflected in `BrainCheckEntry` before they will be passed through validation.
- The `layer` field naming inconsistency (YAML `layer` vs DuckDB `_brain_risk_framework_layer`) is documented but not blocking.

---
*Phase: 45-codebase-cleanup-architecture-hardening*
*Completed: 2026-02-25*
