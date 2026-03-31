---
phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning
plan: "03"
subsystem: brain
tags: [yaml, duckdb, brain, migration, backward-compat, brain-build]

# Dependency graph
requires:
  - phase: 44-02
    provides: "36 domain YAML files under src/do_uw/brain/checks/ with 400 checks in unified 3-axis schema"
  - phase: 44-01
    provides: "SCHEMA.md — authoritative spec for unified 3-axis YAML check model"
provides:
  - "brain_schema.py — ADD COLUMN IF NOT EXISTS for 8 new YAML columns in DuckDB"
  - "brain_build_checks.py — build_checks_from_yaml() rebuilds brain_checks from YAML glob"
  - "brain_migrate.py — load_checks_from_yaml() reads checks/**/*.yaml into flat list"
  - "brain_loader.py — _row_to_check_dict() returns both old and new field names"
  - "brain build CLI — rebuilds checks + framework from YAML in one command"
affects:
  - "44-04-PLAN.md — patterns/red_flags absorption builds on this YAML pipeline"
  - "44-05-PLAN.md — brain add CLI uses brain_build_checks.py as build target"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "YAML glob loader: load_checks_from_yaml(checks_dir / '**' / '*.yaml') returns flat list from all domain files"
    - "Backward compat reverse maps: work_type→content_type, layer→hazard_or_signal, tier→category in brain_build_checks.py"
    - "Empty string fallback for deprecated required-str fields: pillar='', signal_type='' preserves CheckDefinition validation"
    - "Column migrations in _COLUMN_MIGRATIONS (brain_schema.py) for idempotent ADD COLUMN IF NOT EXISTS"

key-files:
  created:
    - "src/do_uw/brain/brain_build_checks.py"
  modified:
    - "src/do_uw/brain/brain_schema.py"
    - "src/do_uw/brain/brain_loader.py"
    - "src/do_uw/brain/brain_migrate.py"
    - "src/do_uw/cli_brain.py"
    - "tests/knowledge/test_compat_loader.py"

key-decisions:
  - "brain_build_checks.py as new module (not inline in brain_migrate.py): brain_migrate.py was 463 lines; adding full build function would exceed 500-line limit. New module under 240 lines."
  - "Empty string for pillar/signal_type deprecated fields: CheckDefinition.pillar is a required str (not Optional) — storing None caused Pydantic validation errors. Store '' to preserve backward compat without data loss."
  - "test_compat_loader.py pillar assertion replaced with tier: pillar was intentionally removed from YAML in plan 44-02; the assertion is pre-existing and now irrelevant for deprecated fields."

patterns-established:
  - "Backward compat reverse maps in build step: work_type→content_type, layer→hazard_or_signal, tier→category so old callers never change"
  - "brain build = checks rebuild + framework rebuild in sequence: checks first (full table rebuild), framework second (tags checks)"
  - "Deprecated required fields get empty string defaults (not None) to preserve downstream Pydantic model compat"

requirements-completed: [ARCH-09]

# Metrics
duration: 28min
completed: "2026-02-25"
---

# Phase 44 Plan 03: Brain Build Pipeline — YAML to DuckDB Summary

**brain build now reads checks/**/*.yaml glob, rebuilds brain_checks with 8 new columns + backward compat shims, and preserves all runtime data tables (brain_check_runs, effectiveness, feedback)**

## Performance

- **Duration:** 28 min
- **Started:** 2026-02-25T06:02:44Z
- **Completed:** 2026-02-25T06:31:02Z
- **Tasks:** 2 of 2
- **Files modified:** 6 (4 brain modules + 1 new module + 1 test fix)

## Accomplishments

- Added 8 new YAML columns to `brain_schema.py` `_COLUMN_MIGRATIONS`: work_type, acquisition_tier, worksheet_section, display_when, chain_roles, unlinked, provenance, peril_ids
- Created `brain_build_checks.py` (238 lines) with `build_checks_from_yaml()` that reads checks/**/*.yaml, applies backward compat reverse maps, and rebuilds brain_checks without touching runtime tables
- Added `load_checks_from_yaml()` to `brain_migrate.py` for reusable YAML glob loading
- Updated `brain_loader.py` to return both new fields (work_type, acquisition_tier, etc.) and legacy fields (content_type, hazard_or_signal, category) from DuckDB — callers work without changes
- Updated `brain build` CLI to print: "Loaded 400 checks (283 unlinked) from 36 YAML files"
- Full test suite: 3974 passed, 0 new failures (one pre-existing `test_html_coverage_exceeds_90_percent` excluded)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add new columns to brain_schema.py** - `01c4012` (feat)
2. **Task 2: YAML pipeline + backward compat** - `37dba36` (feat)
3. **Fix: backward compat pillar/signal_type empty string** - `886cf94` (fix)

**Plan metadata:** (docs commit added at end of state updates)

## Files Created/Modified

- `src/do_uw/brain/brain_schema.py` — Added 8 ADD COLUMN IF NOT EXISTS to _COLUMN_MIGRATIONS; compacted _VIEWS_DDL to stay under 500 lines (499 lines)
- `src/do_uw/brain/brain_build_checks.py` — New module: build_checks_from_yaml() with full field mapping and backward compat reverse maps
- `src/do_uw/brain/brain_migrate.py` — Added load_checks_from_yaml() + glob/yaml imports (478 lines)
- `src/do_uw/brain/brain_loader.py` — Updated load_checks() SELECT to include 8 new columns; _row_to_check_dict() returns all new + legacy fields; _SECTION_MAP extended with worksheet_section strings (500 lines)
- `src/do_uw/cli_brain.py` — brain build command updated to call build_checks_from_yaml() + build_framework()
- `tests/knowledge/test_compat_loader.py` — Replace deprecated pillar assertion with tier assertion

## Decisions Made

- **brain_build_checks.py as new module:** brain_migrate.py was already 463 lines. Adding `build_checks_from_yaml()` inline would push it to ~560 lines, violating the 500-line rule. Created `brain_build_checks.py` (238 lines) for the build logic.
- **Empty string for pillar/signal_type:** `CheckDefinition.pillar: str` is required (non-Optional). Storing `None` from the YAML build (which lacks `pillar`) caused Pydantic validation errors in `test_enriched_roundtrip`. Store `""` to preserve backward compat without requiring model changes.
- **test_compat_loader.py pillar replacement:** The test asserted `pillar` equality between ConfigLoader (reads JSON with pillar values) and BackwardCompatLoader (reads DuckDB after YAML build, which has no pillar). Since `pillar` was intentionally deprecated in plan 44-02, the assertion is replaced with `tier` (which is populated from YAML).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created brain_build_checks.py instead of adding to brain_migrate.py**
- **Found during:** Task 2 (updating brain_migrate.py)
- **Issue:** brain_migrate.py was already 463 lines. Adding the full `build_checks_from_yaml()` with INSERT logic (~100 lines) would push it to ~560 lines, violating CLAUDE.md 500-line rule.
- **Fix:** Created new module `brain_build_checks.py` (238 lines) for the YAML→DuckDB pipeline. Added only `load_checks_from_yaml()` (lightweight glob loader, 11 lines) to `brain_migrate.py`.
- **Files modified:** `src/do_uw/brain/brain_build_checks.py` (created), `src/do_uw/brain/brain_migrate.py` (minimal)
- **Committed in:** `37dba36` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed pillar/signal_type None causing Pydantic validation failures**
- **Found during:** Task 2 (full test suite run)
- **Issue:** `CheckDefinition.pillar: str` is a required non-Optional field. YAML build stored `None` for deprecated fields, causing `test_enriched_check_validates_against_definition` to fail across 400 checks.
- **Fix:** Changed `None` to `""` for `pillar` and `signal_type` in `brain_build_checks.py`.
- **Files modified:** `src/do_uw/brain/brain_build_checks.py`
- **Committed in:** `886cf94`

**3. [Rule 1 - Bug] Updated test_compat_loader.py pillar assertion**
- **Found during:** Task 2 (full test suite run with stash check)
- **Issue:** `test_check_fields_preserved` asserted `pillar` equality between ConfigLoader (JSON: `'P1_WHAT_WRONG'`) and BackwardCompatLoader (DuckDB: `''` or `None`). The test was valid pre-plan-44 but became invalid once YAML migration (plan 44-02) dropped the `pillar` field.
- **Fix:** Replaced `pillar` assertion with `tier` assertion (non-deprecated, populated from YAML).
- **Files modified:** `tests/knowledge/test_compat_loader.py`
- **Committed in:** `37dba36` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 bugs)
**Impact on plan:** All auto-fixes necessary for correctness and code quality compliance. No scope creep.

## Issues Encountered

- `test_html_coverage_exceeds_90_percent` is a pre-existing failure (89.1% vs 90% threshold) unrelated to brain pipeline changes.
- `test_enriched_check_validates_against_definition` appeared as a flaky failure in full-suite runs due to test ordering/DuckDB state sharing. Root cause was `pillar=None` (fixed by deviation 2 above).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- brain build now reads 36 YAML files → populates 400 checks in DuckDB with 8 new columns + backward compat shims
- All 400 checks have work_type, acquisition_tier, worksheet_section, display_when, chain_roles, unlinked, provenance, peril_ids in DuckDB
- brain_check_runs (10,382 rows) and all runtime tables preserved — not wiped during brain build
- Full test suite green (3974 passed, 0 new failures)
- Ready for 44-04: patterns/red_flags YAML absorption

## Self-Check

- FOUND: `src/do_uw/brain/brain_schema.py` (499 lines, under 500) with 8 new ADD COLUMN IF NOT EXISTS
- FOUND: `src/do_uw/brain/brain_build_checks.py` (238 lines) with build_checks_from_yaml()
- FOUND: `src/do_uw/brain/brain_loader.py` (500 lines) with new + legacy fields in _row_to_check_dict()
- FOUND: commit `01c4012` (Task 1 — brain_schema.py new columns)
- FOUND: commit `37dba36` (Task 2 — YAML pipeline + loader update)
- FOUND: commit `886cf94` (Fix — backward compat pillar/signal_type)
- VERIFIED: brain build prints "Loaded 400 checks (283 unlinked) from 36 YAML files"
- VERIFIED: brain_check_runs = 10,382 rows (not wiped)
- VERIFIED: load_checks() returns both 'work_type' and 'content_type' in same dict
- VERIFIED: 3974 tests passed, 0 new failures

## Self-Check: PASSED

---
*Phase: 44-brain-unification-yaml-knowledge-model-self-describing-checks-live-learning*
*Completed: 2026-02-25*
