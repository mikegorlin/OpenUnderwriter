---
phase: 49-pipeline-integrity-facets-ci-guardrails
plan: 05
subsystem: testing
tags: [ci, contract-tests, nomenclature-lint, pytest, brain, signals, facets]

# Dependency graph
requires:
  - phase: 49-01
    provides: "check->signal rename, brain/signals/ directory"
  - phase: 49-02
    provides: "Facet assignments on all 400 signals, 9 facet YAML files"
  - phase: 49-03
    provides: "20 GOV signals marked INACTIVE, lifecycle_state field in YAML"
provides:
  - "CI contract tests validating data routes, thresholds, v6_subsection_ids, scoring linkage, facet assignment, display specs for all ACTIVE signals"
  - "CI facet integrity tests (valid signal IDs, no duplicates, full coverage)"
  - "CI SKIPPED count threshold gate (max 45)"
  - "CI nomenclature lint guard preventing drift back to 'check' terminology (17 forbidden patterns)"
affects: [all-future-phases, ci-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "YAML-based contract tests: load signal YAML directly (not DuckDB) for speed and CI simplicity"
    - "Parametrized nomenclature tests: each forbidden pattern reports individually for targeted fixes"
    - "File-based allowlist for legitimate backward-compat references"

key-files:
  created:
    - "tests/brain/test_brain_contract.py"
    - "tests/brain/test_signal_nomenclature.py"
  modified:
    - "src/do_uw/cli_brain_trace.py"

key-decisions:
  - "SKIPPED threshold set conservatively at 45 (down from ~68 pre-Phase 49); tighten as signals are fixed"
  - "cli_brain_trace.py allowlisted for backward-compat check_results key (reads old state files)"
  - "Used __file__-relative paths in tests for robust CWD handling"

patterns-established:
  - "Brain contract tests: validate signal YAML completeness in CI to prevent regression"
  - "Nomenclature lint: parametrized forbidden-pattern tests with file-based allowlist"

requirements-completed: [QA-03]

# Metrics
duration: 13min
completed: 2026-02-26
---

# Phase 49 Plan 05: CI Guardrails Summary

**10 brain contract tests + 37 nomenclature lint tests enforcing signal completeness and terminology standards in CI**

## Performance

- **Duration:** 13 min
- **Started:** 2026-02-26T20:35:06Z
- **Completed:** 2026-02-26T20:48:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- 10 contract tests validate every ACTIVE signal has data route, threshold, v6_subsection_ids, scoring linkage, facet, and display spec
- 3 facet integrity tests ensure all facet signal IDs are valid, no duplicates, every active signal in exactly one facet
- 37 nomenclature lint tests (17 forbidden patterns x 2 directories + 3 file/directory existence checks) prevent check-terminology drift
- SKIPPED count threshold gate prevents backsliding on signal completeness

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_brain_contract.py** - `336912f` (test)
2. **Task 2: Create test_signal_nomenclature.py** - `d4be89c` (test)
3. **Deviation fix: remove check_results fallbacks** - `fb447e3` (fix)
4. **Deviation fix: allowlist backward-compat** - `3cceb48` (fix)

## Files Created/Modified
- `tests/brain/test_brain_contract.py` - 10 contract tests validating signal YAML completeness (data routes, thresholds, sections, scoring, facets, display, SKIPPED count)
- `tests/brain/test_signal_nomenclature.py` - 37 parametrized lint tests preventing check-terminology drift with file-based allowlist
- `src/do_uw/cli_brain_trace.py` - Backward-compat pattern maintained by project linter; allowlisted in nomenclature tests

## Decisions Made
- Set MAX_SKIPPED_THRESHOLD to 45 (conservative; actual SKIPPED count is well below). Can tighten as confidence grows.
- Used `__file__`-relative paths (`Path(__file__).parent.parent.parent`) instead of `Path("src/...")` for robust CWD handling in all test contexts.
- Allowlisted `cli_brain_trace.py` in nomenclature tests rather than removing its backward-compat `check_results` dict key fallback, since the project linter actively maintains that pattern for reading old cached state files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] cli_brain_trace.py backward-compat fallback for check_results**
- **Found during:** Task 2 (nomenclature lint guard)
- **Issue:** `cli_brain_trace.py` contains `check_results` as a dict key fallback for reading old state files. The project linter actively maintains this backward-compat pattern.
- **Fix:** Added `cli_brain_trace.py` to the nomenclature test allowlist since this is a legitimate backward-compat use, not a signal-related identifier.
- **Files modified:** tests/brain/test_signal_nomenclature.py, src/do_uw/cli_brain_trace.py
- **Verification:** All 47 tests pass green
- **Committed in:** 3cceb48

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Necessary to handle legitimate backward-compat pattern. No scope creep.

## Issues Encountered
- Pre-existing test failure in `tests/knowledge/test_ingestion.py::test_check_prefix_creates_signal_ideas` -- unrelated to this plan's changes (knowledge ingestion feature). Logged as out-of-scope.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 49 is now complete (all 5 plans executed)
- CI guardrails protect against: incomplete signals, terminology drift, facet integrity violations, SKIPPED count backsliding
- Ready for Phase 50 (or next milestone phase)

---
*Phase: 49-pipeline-integrity-facets-ci-guardrails*
*Completed: 2026-02-26*
