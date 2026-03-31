---
phase: "45"
plan: "08"
subsystem: brain
tags: [data-integrity, hard-fail, silent-fallback, sync-check]
dependency_graph:
  requires: [45-03]
  provides: [brain-hard-fail-on-empty, yaml-json-sync-check]
  affects: [brain_loader, brain_build_checks]
tech_stack:
  added: []
  patterns: [hard-fail-on-empty, sync-check-before-write]
key_files:
  modified:
    - src/do_uw/brain/brain_loader.py
    - src/do_uw/brain/brain_build_checks.py
    - tests/brain/test_brain_loader.py
  created: []
decisions:
  - "Replace all 8 ConfigLoader silent fallbacks in BrainDBLoader with RuntimeError; brain.duckdb is the single source of truth"
  - "Implement sync check (option b) rather than integrating brain_migrate_yaml into brain build (option a); preserves canonical YAML direction without introducing direction-reversal confusion"
  - "Expand fully_migrated_conn test fixture to populate all brain tables (checks + scoring + patterns + sectors + red_flags); migrated_conn retained for tests that only need brain_checks"
metrics:
  duration: "12m 44s"
  completed: "2026-02-25"
  tasks_completed: 4
  files_modified: 3
---

# Phase 45 Plan 08: Brain Hard-Fail Guards and YAML-JSON Sync Check Summary

Replaced 8 ConfigLoader silent fallbacks with RuntimeError in BrainDBLoader and added a YAML-vs-DuckDB sync check to brain build, eliminating both silent data integrity failure paths.

## Objective

Two CONCERNS.md data-integrity items:

1. `BrainDBLoader` load_* methods silently fell back to JSON files via ConfigLoader when DuckDB tables were empty — the pipeline could run on stale data with no warning.
2. `brain_migrate_yaml.py` is a standalone script not called by `brain build` — YAML files could silently diverge from `checks.json`, producing incorrect DuckDB state with no error.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace ConfigLoader silent fallback with hard error in BrainDBLoader | 7ea7fd7 | src/do_uw/brain/brain_loader.py |
| 2 | Add YAML-vs-DuckDB sync check to brain_build_checks.py | fca3018 | src/do_uw/brain/brain_build_checks.py |
| 3 | Run full test suite and document deferred items | 0e135ba | tests/brain/test_brain_loader.py |
| 4 | Run AAPL pipeline to confirm hard-fail guards do not block valid runs | (verification only) | — |

## Changes Made

### Task 1: BrainDBLoader Hard-Fail

Replaced all 8 occurrences of the ConfigLoader silent fallback pattern in `brain_loader.py`:

- `load_scoring()` CatalogException handler: now raises RuntimeError with message "brain_scoring_factors table"
- `_load_scoring_from_db()` empty rows: now raises RuntimeError with message "brain_scoring table is empty"
- `load_patterns()` CatalogException handler: now raises RuntimeError
- `_load_patterns_from_db()` empty rows: now raises RuntimeError with message "brain_patterns table is empty"
- `load_red_flags()` CatalogException handler: now raises RuntimeError
- `_load_red_flags_from_db()` empty rows: now raises RuntimeError with message "brain_red_flags table is empty"
- `load_sectors()` CatalogException handler: now raises RuntimeError
- `_load_sectors_from_db()` empty rows: now raises RuntimeError with message "brain_sectors table is empty"

All RuntimeError messages include the actionable fix: "Run: angry-dolphin brain build".

The `from do_uw.config.loader import BrainConfig` import on line 14 was retained — it is still used by `load_all()`.

Verified: `grep -c "ConfigLoader" brain_loader.py` returns 0.

### Task 2: YAML-JSON Sync Check

Added `_validate_yaml_json_sync(brain_dir: Path)` to `brain_build_checks.py`:

- Reads check IDs from `checks.json` (handles both list and `{"checks": [...]}` formats)
- Reads check IDs from all `brain/checks/**/*.yaml` files (handles both `{"checks": [...]}` and list formats)
- Compares the two sets; raises RuntimeError with actionable message if they diverge
- Skips gracefully when `checks.json` does not exist (YAML-only mode)
- Skips gracefully when no YAML files have been generated yet (first-time setup)
- Called at the start of `build_checks_from_yaml()` before any DuckDB writes
- Added explanatory comment above the call site

File size: 305 lines (well under 500-line limit).

Design decision: Implemented as sync check (option b) rather than integrating `brain_migrate_yaml.py` into `brain build` (option a). Integrating would create a direction-reversal (JSON → YAML → DuckDB) that conflicts with the canonical YAML direction. The sync check catches divergence without changing data flow.

### Task 3: Test Fixes

`TestOtherLoaders` in `test_brain_loader.py` previously worked because `load_scoring()`, `load_patterns()`, etc. fell back to ConfigLoader when their DuckDB tables were empty. After removing that fallback, these tests would fail with RuntimeError.

Fix: Added `fully_migrated_conn` fixture that calls `migrate_all_scoring(conn)` and `migrate_configs(conn)` in addition to `migrate_checks_to_brain(conn)`. Updated `loader` fixture to use `fully_migrated_conn`.

Result: 3971 tests pass; 2 pre-existing render coverage failures unchanged (not regressions).

### Task 4: AAPL Pipeline Verification

`uv run do-uw analyze AAPL` completed without errors. Output files generated at `output/AAPL/`. No RuntimeError from BrainDBLoader — confirms the hard-fail guards only trigger when DuckDB is unpopulated, not during normal operation with a populated brain.duckdb.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Expanded test fixture for fully populated brain**

- **Found during:** Task 3
- **Issue:** `TestOtherLoaders` tests (test_load_scoring, test_load_patterns, test_load_sectors, test_load_red_flags) used `loader` fixture backed by `migrated_conn` which only called `migrate_checks_to_brain()`. After removing ConfigLoader fallback, these tests hit empty tables and raised RuntimeError.
- **Fix:** Added `fully_migrated_conn` fixture calling all three migration functions; updated `loader` fixture to use it. `migrated_conn` retained for `TestLifecycleFiltering` tests that only need brain_checks.
- **Files modified:** tests/brain/test_brain_loader.py
- **Commit:** 0e135ba

## Success Criteria Verification

- [x] BrainDBLoader raises RuntimeError (not silent fallback) when DuckDB load_* methods return empty
- [x] No remaining ConfigLoader imports in brain_loader.py (count: 0)
- [x] brain_build_checks.py calls _validate_yaml_json_sync() before DuckDB writes
- [x] Divergent YAML/JSON check IDs produce a clear RuntimeError with actionable fix instructions
- [x] All tests pass (3971 pass, 2 pre-existing failures unchanged)
- [x] AAPL pipeline completes without errors and output file is generated

## Self-Check: PASSED
