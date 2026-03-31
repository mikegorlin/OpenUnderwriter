---
phase: 14-knowledge-system-governance
plan: 03
subsystem: cli
tags: [typer, governance, lifecycle, provenance, drift, cli]
depends_on:
  requires: [09-02, 09-03, 09-04]
  provides: [governance-cli-commands]
  affects: [14-04]
tech_stack:
  added: []
  patterns: [typer-sub-app-nesting, lazy-import-cli, rich-table-output]
key_files:
  created:
    - src/do_uw/cli_knowledge_governance.py
    - tests/test_cli_knowledge_governance.py
  modified:
    - src/do_uw/cli_knowledge.py
    - ruff.toml
decisions:
  - id: "14-03-01"
    description: "Register governance_app on knowledge_app (not main app) for do-uw knowledge govern <cmd> hierarchy"
  - id: "14-03-02"
    description: "Import governance_app at top of cli_knowledge.py to avoid E402 lint error"
  - id: "14-03-03"
    description: "Drift command compares scoring.json factor max_points with store scoring rule max points per factor"
  - id: "14-03-04"
    description: "Patch at do_uw.knowledge.store.KnowledgeStore for tests (lazy imports in CLI functions)"
metrics:
  duration: 5m
  completed: 2026-02-10
---

# Phase 14 Plan 03: Governance CLI Commands Summary

CLI commands for knowledge governance: review, promote, history, drift, deprecation-log registered as `do-uw knowledge govern <command>`.

## What Was Done

### Task 1: Create governance CLI sub-app (c18cd8a)

Created `src/do_uw/cli_knowledge_governance.py` (367 lines) with 5 Typer commands:

1. **review** -- Lists checks filtered by lifecycle status (INCUBATING default) as Rich table with ID, Name, Origin, Section, Pillar columns
2. **promote** -- Transitions check lifecycle status with validation against state machine (INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED); requires `--reason` for deprecation
3. **history** -- Shows check modification history via provenance summary with header info and change table (version, field, old/new values, changed_by, date, reason)
4. **drift** -- Compares scoring.json factor config (max_points, weight_pct) with knowledge store scoring rules; flags mismatches as DRIFT
5. **deprecation-log** -- Lists all deprecated checks with deprecation date, actor, and reason

Registration: `governance_app` imported at top of `cli_knowledge.py`, registered via `knowledge_app.add_typer(governance_app, name="govern")`.

Added B008 ruff ignore for `cli_knowledge_governance.py` (Typer function call defaults).

### Task 2: Add tests for governance CLI commands (0ee2148)

Created `tests/test_cli_knowledge_governance.py` (311 lines) with 13 tests:

- **review**: 3 tests (show incubating checks, filter by status, empty state)
- **promote**: 4 tests (valid transition, invalid transition, deprecated requires reason, nonexistent check)
- **history**: 2 tests (show changes after transitions, check not found)
- **drift**: 2 tests (synced OK, mismatch detected)
- **deprecation-log**: 2 tests (shows deprecated with details, empty state)

Tests use in-memory KnowledgeStore for real lifecycle transitions and patch at source module (`do_uw.knowledge.store.KnowledgeStore`) for lazy-import CLI pattern.

## Decisions Made

1. **Governance sub-app nesting**: Registered on `knowledge_app` (not main app) for `do-uw knowledge govern <cmd>` command hierarchy, avoiding circular imports
2. **Top-level import**: Moved `governance_app` import to top of `cli_knowledge.py` (not after `knowledge_app` definition) to satisfy E402 lint rule; no circular import since `cli_knowledge_governance.py` doesn't import from `cli_knowledge.py`
3. **Drift detection**: Compares factor-level max_points from scoring.json config with max points across scoring rules per factor_id in the store
4. **Test patching**: Patch at `do_uw.knowledge.store.KnowledgeStore` (source module) rather than `do_uw.cli_knowledge_governance.KnowledgeStore` because CLI uses lazy imports inside functions

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- `uv run pyright src/do_uw/cli_knowledge_governance.py` -- 0 errors
- `uv run ruff check src/do_uw/cli_knowledge_governance.py` -- 0 errors
- `uv run pytest tests/test_cli_knowledge_governance.py -v` -- 13/13 passed
- `uv run pytest tests/ -x -q` -- 1764 passed (39 deselected from pre-existing playbook dirty-tree issue, not related to this plan)
- `wc -l src/do_uw/cli_knowledge_governance.py` -- 367 lines (under 500)
- `wc -l src/do_uw/cli_knowledge.py` -- 375 lines (under 500)

## Success Criteria

Phase 14 Success Criterion #3 met: CLI commands exist for knowledge governance -- review pending checks, promote/demote check lifecycle status, view calibration drift, and view check history.
