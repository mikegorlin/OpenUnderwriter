---
phase: 45
plan: "07"
subsystem: brain-duckdb-consolidation
tags: [dual-write, knowledge-db, brain-duckdb, cli, architecture]
dependency_graph:
  requires: ["45-03", "45-06"]
  provides: ["single-write-brain-duckdb", "knowledge-cli-brain-duckdb"]
  affects: ["analyze-stage", "cli-knowledge", "cli-knowledge-governance", "cli-knowledge-checks"]
tech_stack:
  added: []
  patterns: ["single-write telemetry", "brain.duckdb-only check runs", "TODO stubs for unported CLI commands"]
key_files:
  created: []
  modified:
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/cli_knowledge.py
    - src/do_uw/cli_knowledge_governance.py
    - src/do_uw/cli_knowledge_checks.py
    - .gitignore
    - tests/test_cli_knowledge_governance.py
decisions:
  - "Removed dual-write block (knowledge.db) from _record_check_results() in analyze/__init__.py; brain.duckdb is the exclusive telemetry store"
  - "Ported check-stats and dead-checks CLI commands from KnowledgeStore to brain_check_runs in brain.duckdb"
  - "Ported governance review, history, drift, deprecation-log to brain_checks_current and brain_scoring_factors in brain.duckdb"
  - "Promote command replaced with stub directing users to brain YAML workflow"
  - "Commands with no brain.duckdb equivalent (migrate, ingest, narratives) return TODO stubs with informative messages"
  - "Updated governance CLI tests to use temporary file-based brain.duckdb instead of KnowledgeStore patching"
metrics:
  duration: 12m
  completed_date: 2026-02-25
  tasks: 3
  files: 6
---

# Phase 45 Plan 07: Eliminate Dual-Write to knowledge.db Summary

Removed the dual-write from brain.duckdb + knowledge.db to brain.duckdb only. Ported all knowledge CLI commands that read check run history to brain.duckdb. Added knowledge.db to .gitignore.

## What Was Built

**Dual-write elimination:** The `_record_check_results()` function in `analyze/__init__.py` previously wrote every check run to both brain.duckdb (primary) and knowledge.db (legacy SQLite). The knowledge.db write block was removed entirely. brain.duckdb is now the exclusive telemetry store. A comment `# Single write: brain.duckdb only. knowledge.db dual-write removed in Phase 45.` was added.

**CLI command porting:**

| Command | Old Source | New Source |
|---------|-----------|-----------|
| `check-stats` | KnowledgeStore.get_check_stats() → SQLite check_runs | brain_check_runs in brain.duckdb |
| `dead-checks` | KnowledgeStore.get_dead_checks() → SQLite check_runs | brain_check_runs in brain.duckdb |
| `govern review` | KnowledgeStore.query_checks() → SQLite checks | brain_checks_current in brain.duckdb |
| `govern history` | get_provenance_summary() → SQLite history | brain_changelog in brain.duckdb |
| `govern drift` | KnowledgeStore.get_scoring_rules() → SQLite rules | brain_scoring_factors_current in brain.duckdb |
| `govern deprecation-log` | get_deprecation_log() → SQLite deprecated | brain_checks_current RETIRED state |
| `learning-summary` | get_learning_summary() → Notes table | brain_check_runs in brain.duckdb |
| `stats` | get_migration_stats() → SQLite | brain_checks_active + brain_check_runs |
| `search` | store.search_checks() → SQLite FTS5 | brain_checks_active ILIKE |

**TODO stubs for unported commands:**
- `govern promote` → returns "not available via brain.duckdb" (lifecycle transitions require YAML workflow)
- `migrate` → redirects to `do-uw brain build`
- `ingest` → returns "not available" until brain ingestion workflow implemented
- `narratives` → returns "not available" until analysis outcomes stored in brain.duckdb

**Test update:** `tests/test_cli_knowledge_governance.py` rewritten to use temporary file-based brain.duckdb (via `_patch_brain_path` helper) instead of KnowledgeStore patching.

**.gitignore:** Added explicit `src/do_uw/knowledge/knowledge.db` entry (already covered by `*.db` rule but made explicit for clarity).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test suite failure after KnowledgeStore removal**
- **Found during:** Task 3
- **Issue:** `tests/test_cli_knowledge_governance.py` used KnowledgeStore patching; after port to brain.duckdb, all governance tests failed with "Connection already closed" errors (patched connection was being closed by the command implementation)
- **Fix:** Rewrote test file to use temporary file-based brain.duckdb seeded with test data; replaced `_patch_store(KnowledgeStore)` with `_patch_brain_path(db_path)` helper
- **Files modified:** tests/test_cli_knowledge_governance.py
- **Commit:** 5aace69

## Self-Check

### Files verified present
- src/do_uw/stages/analyze/__init__.py - FOUND
- src/do_uw/cli_knowledge.py - FOUND
- src/do_uw/cli_knowledge_governance.py - FOUND
- src/do_uw/cli_knowledge_checks.py - FOUND
- .gitignore (knowledge.db entry) - FOUND
- tests/test_cli_knowledge_governance.py - FOUND

### Commits verified
- 9ba053f: refactor(45-07): remove dual-write from analyze stage; port knowledge CLI to brain.duckdb
- 5aace69: fix(45-07): update governance CLI tests to use brain.duckdb instead of KnowledgeStore

### Test results
- 3934 passed, 382 skipped (excluding pre-existing test_word_coverage_exceeds_90_percent failure)
- AAPL pipeline completed successfully; brain.duckdb has 132,247 check run records

## Self-Check: PASSED
