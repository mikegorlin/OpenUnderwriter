---
phase: 44
plan: "05"
subsystem: brain-cli
tags: [brain, yaml, live-learning, cli, provenance, schema]
dependency_graph:
  requires: [44-04]
  provides: [brain add CLI, brain provenance CLI, SCHEMA.md worked example]
  affects: [cli_brain_add.py, cli_brain.py, SCHEMA.md]
tech_stack:
  added: []
  patterns: [cli-extension-module, yaml-live-learning, editor-template-flow]
key_files:
  created:
    - src/do_uw/cli_brain_add.py
  modified:
    - src/do_uw/cli_brain.py
    - src/do_uw/brain/SCHEMA.md
decisions:
  - "Commands added to new cli_brain_add.py module (not brain_writer.py) — same pattern as 44-04 deviation; brain_writer.py is at 496/500 lines and handles DuckDB writes, not CLI"
  - "Domain routing for brain add: gov and fwrd use subdir routing based on check_id segment 2; biz/fin/lit/stock also route to subdirs; exec and nlp use single-file pattern"
  - "brain provenance uses Rich console.print for formatted output (consistent with other brain CLI commands)"
  - "SCHEMA.md Step 7 updated to use uv run do-uw brain build (not python -m do_uw.brain.brain_writer build)"
  - "SCHEMA.md Step 8 updated to use uv run do-uw brain validate (not python -m ...)"
metrics:
  duration: "10m"
  completed: "2026-02-25"
  tasks: 2
  files: 3
---

# Phase 44 Plan 05: Brain Add CLI and Live Learning Loop Summary

**One-liner:** Added `brain add` (interactive YAML check authoring from article sources with provenance) and `brain provenance` (check origin trace) CLI commands, plus a complete 8-step article decomposition worked example in SCHEMA.md Section 9.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | brain add and brain provenance CLI commands | 4b9a683 | cli_brain_add.py (new), cli_brain.py |
| 2 | Add worked example to SCHEMA.md Section 9 | ce69de6 | SCHEMA.md |

## What Was Built

### Task 1: brain add and brain provenance

Created `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli_brain_add.py` (391 lines) following the `cli_brain_yaml.py` / `cli_brain_ext.py` extension pattern. Registered via `import do_uw.cli_brain_add` in `cli_brain.py`.

**brain add:**
- Requires `--domain` (biz|fin|gov|exec|lit|stock|fwrd|nlp), `--source` (URL/citation), `--date` (ISO YYYY-MM-DD) — all required; rejects without them
- Validates domain against `_VALID_DOMAINS` set; validates date with `date_type.fromisoformat()`
- Opens `$EDITOR` with pre-populated YAML template (source and date injected into provenance block)
- After editor closes: validates required fields (`id`, `name`, `work_type`, `layer`, `acquisition_tier`, `required_data`, `worksheet_section`, `display_when`)
- Enforces `provenance.source_url` — exits 1 if missing
- Routes to correct domain subdirectory via `_resolve_domain_file()`: gov and fwrd use check_id segment 2 routing; biz/fin/lit/stock also subdir-route; exec → `activity.yaml`; nlp → `nlp.yaml`
- Checks for duplicate check ID in target file before appending
- Runs `uv run do-uw brain build` automatically after write

**brain provenance:**
- Takes `CHECK_ID` as positional argument
- Globs all `checks/**/*.yaml` files; finds the matching check
- Displays: Check ID, file location, name, full provenance block (origin, confidence, source_url, source_date, source_author, last_validated, added_by), risk position (work_type, layer, acquisition_tier, factors, peril_ids, chain_roles, unlinked)
- Uses Rich `console.print` for formatted output

**Verification results:**
- `uv run do-uw brain add --help`: shows --source, --date, --domain as required options
- `uv run do-uw brain provenance GOV.BOARD.independence`: shows origin: migrated_from_json, file: checks/gov/board.yaml, chain_roles populated
- 269 brain tests: all pass (0 failures introduced)

### Task 2: SCHEMA.md Worked Example

Added `### Worked Example: Article Decomposition End-to-End` subsection to Section 9, immediately after the 8-step outline. The worked example:

1. Uses real scenario: "Stanford SCAC data 2010-2023 shows boards with >40% insiders have 2.8x higher SCA rate"
2. Walks through all 8 steps with bash commands, decision reasoning, and complete YAML output
3. Shows `GOV.BOARD.insider_concentration` as the new check (full YAML with all fields)
4. Shows `brain add` CLI command with exact expected output (401 checks loaded)
5. Shows `brain validate` expected output
6. Shows `brain provenance` expected output with full provenance block
7. Explains confidence level rationale (medium = single source, upgrade to high if corroborated)
8. Documents chain linkage TODO pattern when no existing chain fits

Also corrected Steps 7 and 8 in the 8-step outline: changed `python -m do_uw.brain.brain_writer build/validate` to `uv run do-uw brain build/validate` (the actual CLI commands).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Commands placed in cli_brain_add.py instead of brain_writer.py**
- **Found during:** Task 1 planning
- **Issue:** `brain_writer.py` handles DuckDB write operations (496/500 lines). Brain CLI commands live in `cli_brain_*.py` modules, not in `brain_writer.py`. Same deviation pattern identified and documented in 44-04-SUMMARY.md.
- **Fix:** Created `cli_brain_add.py` following the established `cli_brain_ext.py` / `cli_brain_yaml.py` extension pattern. Registered via `import do_uw.cli_brain_add` in `cli_brain.py`.
- **Files created:** `src/do_uw/cli_brain_add.py`
- **Note:** `brain_writer.py` stays at 496 lines (unchanged).

**2. [Rule 1 - Bug] SCHEMA.md Steps 7-8 referenced wrong CLI invocation**
- **Found during:** Task 2
- **Issue:** Section 9 steps 7 and 8 used `uv run python -m do_uw.brain.brain_writer build/validate` — the old module invocation. The actual commands since Phase 44 are `uv run do-uw brain build` and `uv run do-uw brain validate`.
- **Fix:** Updated both commands in the 8-step outline to use the correct CLI invocations.
- **Files modified:** `src/do_uw/brain/SCHEMA.md`

## Self-Check: PASSED

Files created/modified:
- FOUND: src/do_uw/cli_brain_add.py (391 lines, brain add + brain provenance + _resolve_domain_file)
- FOUND: src/do_uw/cli_brain.py (import do_uw.cli_brain_add registered)
- FOUND: src/do_uw/brain/SCHEMA.md (Section 9 has Worked Example subsection at line 361)

Commits:
- 4b9a683: feat(44-05): add brain add and brain provenance CLI commands
- ce69de6: docs(44-05): add worked example to SCHEMA.md Section 9 article decomposition guide

CLI verification:
- brain add --help: shows --source, --date, --domain as required options
- brain provenance GOV.BOARD.independence: shows provenance block with origin: migrated_from_json
- brain add rejects invalid domain (exits 1 with error message)
- brain add rejects invalid date format (exits 1 with error message)
- brain validate: VALIDATION PASSED: 400 checks valid, 0 warnings (no regressions)
- 269 brain tests pass (0 failures introduced)
- SCHEMA.md Section 9 grep count for "Worked Example|brain add|insider_concentration": 14 occurrences
