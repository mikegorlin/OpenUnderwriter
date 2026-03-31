# Phase 53: Data Store Simplification - Context

**Gathered:** 2026-02-28
**Updated:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Unify the brain's data layer so YAML signal files and JSON config files are the single runtime source of truth. DuckDB retains only run history and analytics. Four loaders merge into one. Config directory consolidates. Pipeline works zero-setup without `brain build`.

</domain>

<decisions>
## Implementation Decisions

### Config consolidation
- brain/config/ is the single canonical location for ALL JSON config
- config/ directory gets deleted entirely — all files (sic_naics_mapping.json, signal_classification.json, loader.py, etc.) move to brain/config/
- brain/ root JSON files (patterns.json, red_flags.json, scoring.json, sectors.json, signals.json) also move to brain/config/ — brain/ root is for Python code only
- Config loading switches from DuckDB-first-with-JSON-fallback to direct JSON file reads from brain/config/
- 18+ sites currently calling `load_brain_config()` need updating to use the new unified loader

### brain build behavior
- `brain build` becomes validate + export only — no more YAML→DuckDB sync, no more config→DuckDB sync
- Validation: schema checks on all 400 YAML signals, cross-reference integrity, coverage matrix
- Export: signals.json preserved for portability — generated only on explicit `brain build`, NOT on every pipeline run
- Pipeline works zero-setup — no `brain build` prerequisite for first run. Clone and run just works.
- Pipeline does lazy validation on first YAML load — invalid signals logged as warnings and skipped, pipeline continues
- `brain build` is optional: run it for thorough validation/export, but pipeline doesn't depend on it

### brain CLI commands
- `brain stats`, `brain health`, `brain audit`, `brain trace` updated to read from YAML/JSON directly (not DuckDB definition tables)
- Scope: update commands that break when definition tables aren't populated. Commands that only read history tables are fine.
- `feedback` CLI continues writing to DuckDB (brain_feedback, brain_effectiveness) — this is run-history data

### Loader unification
- Four loaders (BrainDBLoader, BrainKnowledgeLoader, BackwardCompatLoader, ConfigLoader) replaced by single BrainLoader
- All ~30 import sites updated to use new BrainLoader — no shims, no re-exports, clean break
- compat_loader.py in knowledge/ also killed — calibrate_impact.py and backtest.py call BrainLoader directly
- Module-level singleton caching: load YAML/JSON once on first call, serve from memory for duration of run. No plumbing through pipeline signatures.
- Callers updated to match new key names where needed

### DuckDB table scoping
- Definition tables (~25 tables including brain_signals, brain_checks, brain_config, brain_taxonomy, brain_patterns, brain_red_flags, brain_sectors, brain_scoring_factors, brain_coverage_matrix, brain_risk_framework, brain_perils, brain_meta, brain_causal_chains, brain_industry, and all *_current/*_active views) — stop being read at pipeline runtime
- History/analytics tables stay completely untouched: brain_signal_runs (20K), brain_check_runs (384K), brain_changelog (1.2K), brain_signal_effectiveness, brain_check_effectiveness, brain_effectiveness, brain_feedback, brain_backlog, brain_proposals
- History write paths remain exactly as-is — no changes to how pipeline writes run data
- brain.duckdb continues to exist but becomes purely a history/analytics store

### Claude's Discretion
- Whether to drop definition tables from schema entirely or keep them as read-only archives
- Which brain CLI commands need updating vs which only read history tables
- Exact BrainLoader class API (methods, constructor signature, typed vs dict config access)
- Migration ordering within the phase (loaders first vs config first)
- brain build DuckDB access (whether to show history stats or go pure YAML/JSON)
- brain_changelog logging from brain build (keep or drop)

</decisions>

<specifics>
## Specific Ideas

- The PAUSE.md from the previous session captures the vision: "The brain YAML signals should be self-contained contracts that drive everything — acquisition, evaluation, and rendering. The system should learn from every run."
- PyYAML CSafeLoader benchmarked at 65ms for all 400 signals — 4x faster than DuckDB intermediary
- Pipeline output must be identical before/after (HTML diff on SNA as verification)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain_signal_schema.py` (BrainSignalEntry Pydantic model): Already validates YAML signals, can be the contract for BrainLoader output
- `brain_loader_rows.py` (_parse_json, row_to_signal_dict): JSON parsing helpers, may be reusable for YAML→dict conversion
- `brain_build_signals.py`: Contains YAML reading logic that can be adapted for runtime loading
- `brain_schema.py` (422 lines): DDL definitions — informs which tables are definition vs history

### Established Patterns
- Lazy imports throughout stages (e.g., `from do_uw.brain.brain_loader import BrainDBLoader` inside function bodies) — ~30 sites all follow this pattern
- brain_config_loader uses DuckDB→JSON fallback chain — replace with direct JSON
- BrainDBLoader.load_all_checks() returns list of dicts — new loader returns BrainSignalEntry objects (Pydantic)
- config/loader.py wraps json.load with typed BrainConfig dataclass — pattern worth keeping in BrainLoader

### Integration Points
- Pipeline stages that import loaders: acquire (brain_requirements), extract (profile_helpers, xbrl_mapping, tax_indicators, sol_mapper, ownership_structure, extraction_manifest), analyze (__init__), benchmark (__init__, benchmark_enrichments), render (scoring_peril_data), score (via compat_loader)
- CLI commands: cli_brain.py, cli_brain_ext.py, cli_knowledge_traceability.py
- Knowledge system: calibrate_impact.py, backtest.py, gap_detector.py, compat_loader.py (compat_loader to be killed)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 53-data-store-simplification*
*Context gathered: 2026-02-28*
*Updated: 2026-02-28*
