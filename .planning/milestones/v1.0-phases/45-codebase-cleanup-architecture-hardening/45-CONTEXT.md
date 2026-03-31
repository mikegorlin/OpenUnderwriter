# Phase 45: Codebase Cleanup & Architecture Hardening - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Eliminate accumulated tech debt: rename phase-numbered files, consolidate the BackwardCompatLoader, remove *_clean boolean fields from render logic, enforce the 500-line rule across all oversized files, unify the dual-write system (removing knowledge.db writes), and standardize the brain YAML schema with load-time validation. No new features — only cleanup, hardening, and structural consistency.

</domain>

<decisions>
## Implementation Decisions

### Backward Compatibility Cuts
- Hard cut — no re-export shims, ever. Old names are deleted.
- When a file is renamed, the old file is deleted entirely (not archived to legacy/).
- Before cutting, grep for old names across the entire codebase including test mocks — `patch('do_uw.stages.analyze.check_mappers_phase26.X')` style mocks must be updated too.
- `__init__.py` files and `__all__` exports must be updated alongside direct import statements. The full public API of each package must reflect new names.

### File Split Strategy
- Split criterion: functional domain. Each resulting file has a single clear responsibility (e.g., `_narrative`, `_tables`, `_financial`).
- After splitting, the original file is deleted. All callers are updated directly. No re-export shims, no thin wrappers.
- The 500-line rule is non-negotiable. If a post-split file is still over 500 lines, split it further in the same plan.
- After splitting, run a full line-count audit of the entire affected directory — not just the files in `files_modified`. Sibling files that are also over 500 lines should be caught and split in the same plan.

### Dual-Write Removal Scope
- Before removing knowledge.db write path: grep across the entire codebase for `knowledge.db`, `KnowledgeStore`, and any read/query of knowledge.db. Migrate or remove every reader found.
- After removal: add knowledge.db to .gitignore (if not already) and document a one-time cleanup step for developers (delete your local knowledge.db).
- CLI schema for migrated queries: Claude's Discretion — adapt `do-uw knowledge` CLI commands to query brain.duckdb using whatever schema is actually there. Don't force the old knowledge.db schema onto brain.duckdb.
- Verification: after removing knowledge.db writes, run a full AAPL analysis. Confirm brain.duckdb contains check run history and that knowledge CLI commands still return meaningful data.

### Verification Approach
- Each plan must pass: full AAPL pipeline run (`do-uw run AAPL`).
- Passing criterion: pipeline completes without errors and output file is generated. Not byte-for-byte match — minor non-determinism is acceptable.
- Pytest must also pass with 0 regressions before moving to the next plan.
- If verification fails: attempt auto-recovery once (e.g., revert a single change, fix an obvious import). If still failing, stop and report. Do not continue to the next plan.

### Brain as Single Source of Knowledge
- Architecture clarification: YAML files in `src/do_uw/brain/` are the source of truth for knowledge (checks, weights, scoring logic). They are git-tracked and human-readable. brain.duckdb is the runtime copy loaded from those YAMLs, plus check run history written during analysis runs.
- This phase must include a YAML schema standardization pass: audit all brain YAMLs for structural consistency, identify inconsistencies, and fix them. All knowledge entries should follow a uniform schema.
- BrainKnowledgeLoader must validate YAML structure on load using Pydantic. If an entry is missing required fields, raise a clear error — no silent skipping, no soft warnings. Prevents bad data from propagating silently.

### Claude's Discretion
- Exact Pydantic model fields for YAML validation — derive from what's actually in the brain YAMLs
- Precise DuckDB query rewrites for knowledge CLI commands migrated from knowledge.db
- Order of callers to update when renaming files (grep will find them all)

</decisions>

<specifics>
## Specific Ideas

- The user's mental model: YAMLs = source of truth, DuckDB = working copy. Any architecture decision must preserve this — brain.duckdb is derived from YAMLs, not the reverse.
- "Extensible" means: adding a new check or weight means editing one YAML in a predictable place. No hidden config spread across Python files.

</specifics>

<deferred>
## Deferred Ideas

- Brain versioning (when a check was added/changed, by whom) — future knowledge architecture phase
- brain.duckdb exportability to DataFrame / CSV for data science use — future phase

</deferred>

---

*Phase: 45-codebase-cleanup-architecture-hardening*
*Context gathered: 2026-02-25*
