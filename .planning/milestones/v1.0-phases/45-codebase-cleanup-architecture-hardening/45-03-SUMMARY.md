---
phase: 45-codebase-cleanup-architecture-hardening
plan: "03"
subsystem: brain
tags: [duckdb, brain, migration, legacy, refactor]

# Dependency graph
requires:
  - phase: 45-02
    provides: BrainKnowledgeLoader rename and caller updates
provides:
  - brain/legacy/ subpackage with 3 deprecated migration files
  - hard-fail guard in brain_loader._get_conn() after migration
  - zero non-legacy imports of deprecated migration paths
affects: [brain, cli_brain, cli_brain_ext, brain_loader]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "brain/legacy/ subpackage for emergency-only deprecated code"
    - "Hard-fail RuntimeError guard after DuckDB migration to enforce non-empty invariant"

key-files:
  created:
    - src/do_uw/brain/legacy/__init__.py
    - src/do_uw/brain/legacy/brain_migrate_framework.py
    - src/do_uw/brain/legacy/brain_migrate_config.py
    - src/do_uw/brain/legacy/brain_migrate_scoring.py
  modified:
    - src/do_uw/brain/brain_loader.py
    - src/do_uw/cli_brain.py
    - src/do_uw/cli_brain_ext.py
    - tests/brain/test_brain_framework.py

key-decisions:
  - "Created brain/legacy/ subpackage to make emergency-only nature of deprecated migration files structurally obvious"
  - "Added hard-fail RuntimeError guard in brain_loader._get_conn() after migration: raises if brain_checks is empty post-migration"
  - "_BRAIN_DIR and _CONFIG_DIR/_KNOWLEDGE_DB paths adjusted in legacy files to account for extra directory level"

patterns-established:
  - "Emergency/deprecated code goes in brain/legacy/ — structural location communicates purpose"
  - "Migration invariants enforced at runtime with explicit RuntimeError messages, not silent failure"

requirements-completed:
  - ARCH-04

# Metrics
duration: 7min
completed: 2026-02-25
---

# Phase 45 Plan 03: Brain Legacy Migration Isolation Summary

**Moved 3 deprecated brain migration files into brain/legacy/ subpackage, updated all callers to use legacy paths, and added hard-fail guard in BrainDBLoader to enforce non-empty DuckDB invariant after migration.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-25T16:07:32Z
- **Completed:** 2026-02-25T16:14:51Z
- **Tasks:** 4 (3 code tasks + 1 verification pipeline run)
- **Files modified:** 8

## Accomplishments
- Created `brain/legacy/` subpackage with `__init__.py` explaining emergency-only purpose
- Moved `brain_migrate_framework.py`, `brain_migrate_config.py`, `brain_migrate_scoring.py` from `brain/` root to `brain/legacy/`
- Updated all callers (brain_loader.py, cli_brain.py, cli_brain_ext.py) and test file to use `brain.legacy.*` paths
- Added hard-fail RuntimeError guard in `brain_loader._get_conn()` after migration block — raises if `brain_checks` is empty post-migration
- 3,409 tests pass with 0 regressions; AAPL pipeline completes end-to-end

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain/legacy/ subpackage and relocate 3 migration files** - `7642d8d` (feat)
2. **Task 2: Update callers in brain_loader.py, cli_brain.py, cli_brain_ext.py** - `03e6074` (feat)
3. **Task 3: Run full test suite + fix test_brain_framework.py import** - `0a08811` (fix)
4. **Task 4: AAPL pipeline — verification only, no code changes** — no commit

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/do_uw/brain/legacy/__init__.py` - Subpackage marker with emergency-only docstring
- `src/do_uw/brain/legacy/brain_migrate_framework.py` - Moved from brain root; `_framework_dir()` now uses `Path(__file__).parent.parent / "framework"` to maintain correct relative path
- `src/do_uw/brain/legacy/brain_migrate_config.py` - Moved from brain root; `_CONFIG_DIR` and `_KNOWLEDGE_DB` updated to use `parent.parent.parent` for correct project-relative paths
- `src/do_uw/brain/legacy/brain_migrate_scoring.py` - Moved from brain root; `_BRAIN_DIR` updated to `parent.parent` (brain/ directory)
- `src/do_uw/brain/brain_loader.py` - Import paths updated to `brain.legacy.*`; hard-fail guard added after migration block
- `src/do_uw/cli_brain.py` - Import path updated to `brain.legacy.brain_migrate_framework`
- `src/do_uw/cli_brain_ext.py` - Import paths updated to `brain.legacy.brain_migrate_config` and `brain.legacy.brain_migrate_scoring`
- `tests/brain/test_brain_framework.py` - Import path updated to `brain.legacy.brain_migrate_framework`

## Decisions Made
- Adjusted relative paths inside legacy files during move: `_BRAIN_DIR`, `_CONFIG_DIR`, `_KNOWLEDGE_DB`, `_framework_dir()` all needed one extra `.parent` level since files moved one directory deeper
- Hard-fail guard checks `brain_checks` table (not `brain_checks_active`) to catch the case where migration ran but left the table empty

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test file import path in test_brain_framework.py**
- **Found during:** Task 3 (Run full test suite)
- **Issue:** `tests/brain/test_brain_framework.py` imported from `do_uw.brain.brain_migrate_framework` (old path), causing `ModuleNotFoundError` on test collection
- **Fix:** Changed import to `do_uw.brain.legacy.brain_migrate_framework`
- **Files modified:** `tests/brain/test_brain_framework.py`
- **Verification:** All 3,409 tests pass after fix
- **Committed in:** `0a08811` (Task 3 fix commit)

**2. [Rule 1 - Bug] Adjusted relative path variables in legacy files**
- **Found during:** Task 1 (anticipatory during file creation)
- **Issue:** `_BRAIN_DIR`, `_CONFIG_DIR`, `_KNOWLEDGE_DB`, `_framework_dir()` were defined relative to `__file__` in original files; moving one directory deeper would resolve to wrong paths
- **Fix:** Updated each path to add an extra `.parent` to account for new directory depth
- **Files modified:** `legacy/brain_migrate_framework.py`, `legacy/brain_migrate_config.py`, `legacy/brain_migrate_scoring.py`
- **Verification:** All legacy imports verified working; AAPL pipeline completes
- **Committed in:** `7642d8d` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs: broken imports from path change)
**Impact on plan:** Both essential for correctness after file relocation. No scope creep.

## Issues Encountered
- Pre-existing test failure: `test_html_coverage_exceeds_90_percent` (89.1% vs 90% threshold) — confirmed pre-existing before our changes, unrelated to brain/legacy migration

## Next Phase Readiness
- brain/legacy/ structure established as canonical location for emergency-only deprecated code
- All callers updated; zero non-legacy imports of deprecated migration paths remain
- brain_loader hard-fail guard protects against silent empty-brain scenarios
- Ready to continue Phase 45 cleanup plans

---
*Phase: 45-codebase-cleanup-architecture-hardening*
*Completed: 2026-02-25*
