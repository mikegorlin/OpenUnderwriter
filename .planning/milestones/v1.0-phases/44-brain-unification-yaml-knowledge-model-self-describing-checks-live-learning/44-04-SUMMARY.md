---
phase: 44
plan: "04"
subsystem: brain-cli
tags: [brain, yaml, validation, deprecation, cli]
dependency_graph:
  requires: [44-03]
  provides: [brain validate CLI, brain unlinked CLI, deprecation markers]
  affects: [cli_brain.py, cli_brain_yaml.py, brain_migrate_*.py, checks.json]
tech_stack:
  added: []
  patterns: [cli-extension-module, comment-deprecation-headers, json-metadata-key]
key_files:
  created:
    - src/do_uw/brain/cli_brain_yaml.py
  modified:
    - src/do_uw/cli_brain.py
    - src/do_uw/brain/brain_migrate_config.py
    - src/do_uw/brain/brain_migrate_framework.py
    - src/do_uw/brain/brain_migrate_scoring.py
    - src/do_uw/brain/checks.json
    - tests/brain/test_brain_loader.py
decisions:
  - "Commands added to new cli_brain_yaml.py module (not brain_writer.py) — brain_writer.py was already at 496/500 lines; cli_brain_ext.py extension pattern reused"
  - "VALIDATION PASSED with 0 warnings — all 400 YAML checks already comply with unified schema from prior phase 44-03 migration"
  - "deprecated key added as first JSON key in checks.json with status/date/message/replacement fields"
  - "test_data_sources_key_preserved updated to exclude deprecated from BrainDBLoader propagation check — metadata annotation intentionally not passed through DuckDB loader"
metrics:
  duration: "12m 20s"
  completed: "2026-02-25"
  tasks: 2
  files: 7
---

# Phase 44 Plan 04: Brain Validate and Deprecation Summary

**One-liner:** Added `brain validate` (schema compliance checker for 400 YAML checks) and `brain unlinked` (lists 283 unlinked checks), plus deprecation markers on 3 Python migration files and checks.json.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | brain validate and brain unlinked CLI commands | f0fade6 | cli_brain_yaml.py (new), cli_brain.py |
| 2 | Deprecation headers + checks.json notice | bd323a6 | brain_migrate_config.py, brain_migrate_framework.py, brain_migrate_scoring.py, checks.json, tests/brain/test_brain_loader.py |

## What Was Built

### Task 1: brain validate and brain unlinked

Created `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli_brain_yaml.py` following the `cli_brain_ext.py` extension pattern (registered via module import in `cli_brain.py`).

**brain validate:**
- Globs all `checks/**/*.yaml` files (400 checks across 36 files)
- Checks required fields: `id, name, work_type, layer, acquisition_tier, required_data, worksheet_section, display_when, provenance`
- Validates enum values: `work_type in {extract, evaluate, infer}`, `layer in {hazard, signal, peril_confirming}`, `acquisition_tier in {L1, L2, L3, L4}`
- Warns on deprecated fields: `pillar, category, signal_type, hazard_or_signal, content_type`
- Result: VALIDATION PASSED: 400 checks valid, 0 warnings

**brain unlinked:**
- Globs all `checks/**/*.yaml` files
- Lists checks with `unlinked: true` (no causal chain assignment)
- Supports `--domain` filter (e.g. `--domain BIZ` returns 28 of 283)
- Result: 283 unlinked checks displayed

### Task 2: Deprecation markers

**Python files** (`brain_migrate_config.py`, `brain_migrate_framework.py`, `brain_migrate_scoring.py`): Added standard 4-line `# DEPRECATED: 2026-02-25` comment block after each module docstring, before imports. Files not deleted, imports not removed.

**checks.json**: Added top-level `deprecated` object as first key with `status`, `date`, `message`, and `replacement` fields. The `deprecated` key is read safely by all existing consumers (they use `data.get("checks")`, not top-level list assumption).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_data_sources_key_preserved test broken by new deprecated key**
- **Found during:** Task 2
- **Issue:** The test checked that all top-level keys from `checks.json` (via `ConfigLoader`) are present in `BrainDBLoader.load_checks()` result. Adding `deprecated` to `checks.json` caused the test to expect `deprecated` in the DuckDB loader output, which it doesn't produce.
- **Fix:** Added `deprecated` to the `_metadata_only_keys` exclusion set in `test_data_sources_key_preserved`. Added docstring explaining the design decision.
- **Files modified:** `tests/brain/test_brain_loader.py`
- **Commit:** bd323a6

**2. [Rule 3 - Blocking] Commands placed in new module instead of brain_writer.py**
- **Found during:** Task 1 planning
- **Issue:** `brain_writer.py` was already at 496 lines. Adding 80+ lines of commands would violate the 500-line rule. Additionally, brain CLI commands live in `cli_brain.py` / `cli_brain_ext.py`, not in `brain_writer.py`.
- **Fix:** Created `cli_brain_yaml.py` following the established `cli_brain_ext.py` extension pattern. Registered via `import do_uw.cli_brain_yaml` in `cli_brain.py`.
- **Files created:** `src/do_uw/cli_brain_yaml.py`
- **Note:** `brain_writer.py` stays at 496 lines (unchanged). The plan referenced `brain_writer.py` as the target but the actual CLI architecture requires `cli_brain_*.py` modules.

## Pre-existing Failures (Deferred)

`tests/test_render_coverage.py::TestMultiFormatCoverage::test_html_coverage_exceeds_90_percent` was failing before this plan (HTML coverage 89.1% < 90% threshold, 5 uncovered fields). Not related to this plan's changes.

## Self-Check: PASSED

Files created/modified:
- FOUND: src/do_uw/cli_brain_yaml.py
- FOUND: src/do_uw/cli_brain.py (modified)
- FOUND: src/do_uw/brain/brain_migrate_config.py (deprecated header present)
- FOUND: src/do_uw/brain/brain_migrate_framework.py (deprecated header present)
- FOUND: src/do_uw/brain/brain_migrate_scoring.py (deprecated header present)
- FOUND: src/do_uw/brain/checks.json (deprecated key present)
- FOUND: tests/brain/test_brain_loader.py (test updated)

Commits:
- f0fade6: feat(44-04): add brain validate and brain unlinked CLI commands
- bd323a6: chore(44-04): mark deprecated source files and add deprecation notice to checks.json

CLI verification:
- brain validate: VALIDATION PASSED: 400 checks valid, 0 warnings
- brain unlinked: Unlinked checks: 283
- Test suite: 269 brain tests pass (0 failures introduced)
