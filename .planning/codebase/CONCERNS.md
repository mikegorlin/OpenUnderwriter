# Codebase Concerns

**Analysis Date:** 2026-02-25

---

## Tech Debt

### Deprecated Migration Files Still Importable and Still Called

**Files with DEPRECATED headers that are still imported at runtime:**
- `src/do_uw/brain/brain_migrate_framework.py` — marked `# DEPRECATED: 2026-02-25`, but imported by `src/do_uw/cli_brain.py:367` (`brain build` command calls `build_framework`)
- `src/do_uw/brain/brain_migrate_scoring.py` — marked `# DEPRECATED: 2026-02-25`, but imported by `src/do_uw/brain/brain_loader.py:82` (used as fallback for scoring, patterns, red flags, sectors)
- `src/do_uw/brain/brain_migrate_config.py` — marked `# DEPRECATED: 2026-02-25`, but imported by `src/do_uw/brain/brain_loader.py:84` and `src/do_uw/cli_brain_ext.py:445`

**Impact:** The files self-describe as "emergency rollback only," but they execute on every cold-start and on `brain build`. Contradicts their own deprecation comments. Confuses future developers about whether they are active code.

**Fix approach:** Rename as `_legacy_` prefix or move to `brain/legacy/` subdirectory. Update callers in `brain_loader.py` to fail explicitly if DuckDB is unavailable rather than silently falling back to JSON migration code.

---

### Deprecated `config/loader.py` (ConfigLoader) Still Heavily Used

- Files: `src/do_uw/config/loader.py`, `src/do_uw/config/__init__.py`
- Marked `.. deprecated:: Phase 41` in docstring
- `BrainDBLoader.load_scoring()`, `load_patterns()`, `load_red_flags()`, `load_sectors()` all import `ConfigLoader` as fallback (8 separate `from do_uw.config.loader import ConfigLoader` calls in `src/do_uw/brain/brain_loader.py` alone)
- `src/do_uw/knowledge/compat_loader.py` also imports it

**Impact:** Two loader systems coexist. If DuckDB tables are empty, the pipeline silently falls back to JSON files without user-visible warning. Violates the "brain.duckdb is the single source of truth" invariant.

**Fix approach:** Add an explicit `assert` or hard error in `BrainDBLoader` when DuckDB is populated but queries return empty. Remove `ConfigLoader` as a fallback; make the fallback a hard failure with a clear message to run `brain build`.

---

### Deprecated Boolean `*_clean` Fields Still Driving Render Logic

- Location: `src/do_uw/models/state.py:223-260` — `governance_clean`, `litigation_clean`, `financial_clean`, `market_clean` all marked `DEPRECATED: Use section_densities[...].level instead`
- Active usage in render:
  - `src/do_uw/stages/render/sections/sect4_market.py:84-86` — reads `state.analysis.market_clean` and falls back to `_is_market_clean()`
  - `src/do_uw/stages/render/sections/sect5_governance.py:88-90` — reads `state.analysis.governance_clean` and falls back to `_is_governance_clean()`
  - `src/do_uw/stages/render/sections/sect3_financial.py:156-157` — reads `state.analysis.financial_clean`

**Impact:** Two parallel systems for the same decision. `section_densities` is the correct path (set by `compute_section_assessments` in ANALYZE). The boolean fallbacks in render sections recompute logic that was meant to be pre-computed upstream. Phase 29 Goal 3 was "render reads pre-computed values" — this partially remains unfixed.

**Fix approach:** Remove fallback functions `_is_market_clean()`, `_is_governance_clean()` from render sections. Force render to read only from `state.analysis.section_densities`. Then remove the deprecated boolean fields from `AnalysisState`.

---

### Dual Write to Both `brain.duckdb` and `knowledge.db` (SQLite)

- Location: `src/do_uw/stages/analyze/__init__.py:229-294`
- Comment explicitly calls it "legacy" — `# Write to knowledge.db (legacy, for knowledge CLI compatibility)`
- Every pipeline run writes check results to both stores

**Impact:** 24MB `knowledge.db` in `src/do_uw/knowledge/knowledge.db` (tracked in git tree) will grow unboundedly. Every analysis doubles write I/O. The knowledge CLI tools (`do-uw knowledge ...`) depend on `knowledge.db` which creates a forced coupling.

**Fix approach:** Port knowledge CLI tools (`src/do_uw/cli_knowledge.py`, `src/do_uw/cli_knowledge_governance.py`, `src/do_uw/cli_knowledge_traceability.py`) to read from `brain.duckdb`. Then remove the dual-write. Add `knowledge.db` to `.gitignore`.

---

### `brain_migrate_yaml.py` Is a Standalone Script, Not Called by Any Module

- File: `src/do_uw/brain/brain_migrate_yaml.py`
- Has usage comment: `uv run python src/do_uw/brain/brain_migrate_yaml.py`
- No `from do_uw.brain.brain_migrate_yaml import` exists in any source file
- This script converts `checks.json` → domain YAML files in `brain/checks/`

**Impact:** The migration tool is invisible to the standard build path. If someone runs `brain build` without first running this script, the YAML files may be stale relative to `checks.json`. There is no automated check that YAML and JSON are in sync.

**Fix approach:** Either (a) integrate YAML-to-DuckDB directly via `brain_build_checks.py` without the intermediate JSON, or (b) add a YAML/JSON sync check to `brain build` with a clear error if they diverge.

---

### `BackwardCompatLoader` Name Is Misleading — It's the Active Loader

- File: `src/do_uw/knowledge/compat_loader.py`
- Used in: `src/do_uw/stages/analyze/__init__.py:353`, `src/do_uw/stages/score/__init__.py:228`, `src/do_uw/stages/benchmark/__init__.py:135`, `src/do_uw/stages/render/sections/sect7_coverage_gaps.py:56`
- The name implies it will be removed, but it is the primary check loader for ANALYZE, SCORE, and BENCHMARK

**Impact:** Every Claude instance (and human developer) reading the code will assume this loader is temporary and may bypass it when adding new functionality, leading to fragmentation.

**Fix approach:** Rename to `BrainKnowledgeLoader` or `CheckLoader`. Update all callers. The "compat" name is historical — the class now cleanly delegates to `BrainDBLoader` with `KnowledgeStore` as fallback.

---

### Phase 26-Specific File Names Persist Indefinitely

- `src/do_uw/stages/analyze/check_mappers_phase26.py` — active code, imported by `check_mappers.py:115`
- `src/do_uw/stages/score/red_flag_gates_phase26.py` — active code, imported by `red_flag_gates.py:52`
- `src/do_uw/stages/analyze/check_mappers_fwrd.py` — docstring says "Split from check_mappers_phase26.py to stay under 500-line limit"

**Impact:** Phase-numbered file names create confusion about whether these files are permanent or transitional. Any developer sees "phase26" and assumes cleanup is pending. These are not cleanup targets — they are permanent logic files.

**Fix approach:** Rename:
- `check_mappers_phase26.py` → `check_mappers_analytical.py`
- `red_flag_gates_phase26.py` → `red_flag_gates_enhanced.py`
- `check_mappers_fwrd.py` → `check_mappers_forward.py`

---

## Files Violating 500-Line Rule

The following files exceed CLAUDE.md's 500-line limit. Each needs to be split:

| File | Lines | Split Strategy |
|------|-------|----------------|
| `src/do_uw/stages/render/md_renderer_helpers.py` | 590 | Extract narrative helpers and table helpers |
| `src/do_uw/stages/extract/company_profile.py` | 583 | Split item parsing from profile assembly |
| `src/do_uw/stages/extract/earnings_guidance.py` | 533 | Split extraction from classification |
| `src/do_uw/stages/render/md_renderer_helpers_financial.py` | 528 | Split balance sheet from income statement helpers |
| `src/do_uw/stages/extract/regulatory_extract.py` | 521 | Split by agency type (SEC vs other) |
| `src/do_uw/stages/score/factor_data.py` | 514 | Split by factor group |
| `src/do_uw/stages/acquire/clients/sec_client.py` | 511 | Split filing fetching from identity resolution |
| `src/do_uw/stages/analyze/financial_formulas.py` | 509 | Split distress models from other formulas |
| `src/do_uw/cli_knowledge.py` | 505 | Split by command group |
| `src/do_uw/validation/qa_report.py` | 503 | Split report generation from validation logic |

Files at exactly 500 lines (one addition away from violation):
- `src/do_uw/stages/extract/peer_group.py` (500)
- `src/do_uw/stages/analyze/check_mappers.py` (500)
- `src/do_uw/brain/brain_loader.py` (500)

---

## Known Bugs

### `ai_impact_models.py` Was "Deleted" in Phase 29 But Still Exists

- Phase 29 SUMMARY.md states: "Deleted `knowledge/ai_impact_models.py` (replaced by different implementation)"
- File still exists: `src/do_uw/knowledge/ai_impact_models.py`
- Still imported: `src/do_uw/stages/score/ai_risk_scoring.py:20` — `from do_uw.knowledge.ai_impact_models import get_ai_impact_model`
- `get_ai_impact_model` is called at `ai_risk_scoring.py:76`

**Impact:** Phase 29 claimed 1,188 lines of dead code deleted. This file (335 lines) was counted in that deletion but was replaced, not deleted. The function is live and called. No bug in functionality, but the Phase 29 audit report is incorrect.

**Fix approach:** No action needed on the code — it works. Update Phase 29 SUMMARY.md to reflect that `ai_impact_models.py` was replaced (not deleted) and is still active at a new location.

---

### `brain_sectors` in DuckDB Returns 95 Rows but `load_sectors()` Returns a Dict, Not a List

- `BrainDBLoader.load_sectors()` returns a `dict[str, Any]` with 10 top-level keys (short_interest, volatility_90d, etc.)
- `len(sectors.get("sectors", {}))` returns 0 because there is no "sectors" key — the top-level structure IS the sectors data
- Code in `src/do_uw/stages/score/factor_data.py:347` uses `sectors.get("volatility_90d", {})` — correct pattern
- But any code expecting `sectors["sectors"]` would silently get empty dict

**Impact:** If any caller uses the `{"sectors": {...}}` wrapper pattern (as `sectors.json` did), it silently gets no sector data. Low risk currently but fragile.

**Fix approach:** Audit all callers of `load_sectors()` for the `sectors["sectors"]` access pattern. Add a top-level `sectors` key to the returned dict for backward compatibility.

---

## Security Considerations

### `SERPER_API_KEY` Absence Disables Blind Spot Detection Without Hard Failure

- Location: `src/do_uw/cli.py:288-296`
- If `SERPER_API_KEY` is not set, a warning is logged and analysis continues
- CLAUDE.md states: "Broad web search is a FIRST-CLASS acquisition method, not a fallback" and "Missing them entirely is worse than flagging them"

**Risk:** Silently producing worksheets with no web-based blind spot discovery when the API key is absent. The worksheet gets a "Data Quality Notice" but the underwriter may not notice.

**Current mitigation:** Warning logged, notice in worksheet.

**Recommendations:** Add a CLI flag `--require-web-search` that hard-fails if no search provider is configured. At minimum, surface the Data Quality Notice more prominently in the worksheet executive summary.

---

## Performance Bottlenecks

### `knowledge.db` (SQLite) Is 24MB and Growing With Every Run

- Location: `src/do_uw/knowledge/knowledge.db`
- Size: 24MB (confirmed by `ls -la`)
- Every pipeline run appends check results to this file via `KnowledgeStore`
- The file appears to be committed in the git repository

**Impact:** Unbounded growth. After 100 analysis runs, this file could reach 2GB+. Git history bloat if committed. Slow CI imports.

**Fix:** Remove from git tracking immediately (add to `.gitignore`). Port knowledge CLI reads to `brain.duckdb`. Remove the dual-write from `src/do_uw/stages/analyze/__init__.py:272-294`.

---

### `BackwardCompatLoader` Creates a Full `KnowledgeStore` on Every Init

- Location: `src/do_uw/knowledge/compat_loader.py:41-51`
- `BackwardCompatLoader.__init__()` calls `_create_default_store()` which opens `knowledge.db` even when `brain.duckdb` is available
- The store is created unconditionally, then only used if `brain.duckdb` fails

**Impact:** Unnecessary SQLite connection on every ANALYZE, SCORE, and BENCHMARK stage init. Small overhead but wasteful.

**Fix:** Lazy-initialize `self._store` only when `_brain_db_loader` is `None`.

---

## Fragile Areas

### Word Renderer Falls Back to Placeholder for Unimplemented Sections

- Location: `src/do_uw/stages/render/word_renderer.py:324-398`
- `_add_placeholder_section()` renders `"{section_name} -- To be implemented"` for any section not in the implemented set
- Sections render silently as stubs if not wired

**Files:** `src/do_uw/stages/render/word_renderer.py`

**Why fragile:** Adding a new section to the HTML renderer without adding it to the Word renderer produces a silent gap. No test catches this because the Word renderer doesn't fail — it just renders a stub.

**Safe modification:** When adding a new section to `src/do_uw/stages/render/__init__.py`, always add a corresponding Word renderer call in `render_word_document()`. Add a test that asserts the set of HTML sections == the set of Word sections.

**Test coverage:** No test verifies Word section completeness.

---

### `DealContext` (SECT1-07) Is Always a Placeholder in Ticker-Only Mode

- Location: `src/do_uw/stages/benchmark/summary_builder.py:215-216`
- `deal_context = DealContext()` is always created empty; `is_placeholder=True` is the default
- `src/do_uw/models/executive_summary.py:257` — `is_placeholder: bool = True` as the default
- Render: `src/do_uw/stages/render/sections/sect1_market_context.py` gracefully handles the no-data case

**Impact:** The Deal Context section (layer structure, premium, carrier) in Section 1 is always blank in the primary use case (ticker-only analysis). This is by design but creates a permanent gap in the executive summary.

**Fix approach:** Either (a) add a CLI flag to pass deal context manually, or (b) clearly mark this section as "Not applicable in ticker-only mode" with instructions for populating it.

---

### Check Mapper Chain Has 5 Files With Lazy Imports — Hard to Trace

The check field routing goes:
1. `src/do_uw/stages/analyze/check_mappers.py` (main dispatcher, 500 lines)
2. → lazy import: `check_mappers_ext.py` (extended check types)
3. → lazy import: `check_mappers_phase26.py` (analytical engine checks)
4. → lazy import: `check_mappers_phase26.py` → lazy import `check_mappers_fwrd.py` (forward-looking)
5. → lazy import: `check_mappers_sections.py` (governance + litigation)

All imports are deferred `from X import Y` inside function bodies. While this avoids circular imports, it makes tracing a check's mapping path require reading 5 files.

**Why fragile:** Adding a new check prefix requires modifying `check_field_routing.py` and potentially one or more mapper files. The routing table in `src/do_uw/stages/analyze/check_field_routing.py` is the canonical entry point but it notes "handled by check_mappers_phase26.py and don't need entries."

**Safe modification:** Always update `check_field_routing.py` first to document which file handles a new prefix. Add a test for each new prefix to `tests/test_analyze_stage.py`.

---

## Scaling Limits

### Single-Tenant DuckDB (`brain.duckdb`) Cannot Handle Concurrent Analysis Runs

- `brain.duckdb` is opened with a persistent connection in `BrainDBLoader`
- DuckDB allows multiple readers but single writer
- If two `do-uw analyze` processes run simultaneously, the second will fail to acquire a write lock when auto-migrating

**Current capacity:** 1 concurrent analysis run safely.

**Limit:** 2+ concurrent runs → potential DuckDB lock contention on first connect.

**Scaling path:** Use read-only connections in `BrainDBLoader` (brain data is read-only during analysis). Reserve write-only for `brain build` operations.

---

## Dependencies at Risk

### `knowledge.db` SQLite File Is 24MB and Tracked in Git

- Risk: Will bloat git history. Each commit that runs a pipeline grows the file.
- Impact: Slow clones, large CI caches.
- Migration plan: Add to `.gitignore` immediately. Future: port knowledge CLI to `brain.duckdb`.

---

### `serper_client.py` Uses a Third-Party API (Serper.dev) With No Rate Limiting

- File: `src/do_uw/stages/acquire/clients/serper_client.py`
- Serper charges per-search, 2,000 free/month (per CLAUDE.md, for Brave Search — Serper has different limits)
- `WebSearchClient` has a search budget counter (`state.acquired_data.search_budget_used`) but `serper_client.py` does not enforce a hard cap

**Risk:** Runaway search costs if the budget tracking in `WebSearchClient` fails to propagate to the serper call path.

**Recommendation:** Add an explicit `max_searches` guard in `create_serper_search_fn()` that refuses to search if budget is exhausted.

---

## Missing Critical Features

### No Automated Check That YAML Source Files and `checks.json` Are in Sync

- `brain/checks/**/*.yaml` are the canonical check source
- `brain/checks.json` is a 407KB JSON file also present
- `brain_migrate_yaml.py` converts JSON → YAML (one-direction script)
- `brain_migrate.py` reads `checks.json` for DuckDB migration

**Problem:** Two sources of truth for check definitions. If someone edits a YAML file directly, `checks.json` becomes stale. If someone edits `checks.json`, the YAML files become stale.

**Fix:** Add a CI check or `brain build` validation step that compares check IDs between `checks.json` and the YAML files, failing if they diverge.

---

### SECT7-11 Calibration Is Marked `needs_calibration=True` on Every Check Output

- Files: `src/do_uw/stages/score/tier_classification.py:101`, `src/do_uw/stages/score/allegation_mapping.py:101`, `src/do_uw/stages/score/severity_model.py:95`
- Every probability, settlement prediction, and tier classification is flagged `needs_calibration=True`
- `src/do_uw/stages/benchmark/inherent_risk.py:14` — "All values marked NEEDS CALIBRATION per SECT7-11"

**Impact:** The calibration flag is ubiquitous and therefore meaningless. Underwriters cannot distinguish "this specific estimate is uncertain" from "the entire scoring system is uncalibrated." The flag was meant to be a signal, not a constant.

---

## Test Coverage Gaps

### No Test Verifies Brain YAML → DuckDB → Analysis Pipeline End-to-End

- What's not tested: The full path from YAML file edit → `brain build` → `brain.duckdb` populated → ANALYZE stage reads correct check
- Files: `src/do_uw/brain/checks/**/*.yaml`, `src/do_uw/brain/brain_build_checks.py`, `src/do_uw/stages/analyze/__init__.py`
- Risk: A YAML field rename could silently break check execution without test failure
- Priority: **High**

---

### No Test Verifies Word Renderer Section Completeness

- What's not tested: That every section rendered in HTML also has a corresponding Word implementation (vs. placeholder)
- Files: `src/do_uw/stages/render/word_renderer.py`, `src/do_uw/stages/render/__init__.py`
- Risk: New sections added to HTML silently appear as "To be implemented" stubs in Word output
- Priority: **Medium**

---

### No Test Covers the Deprecated `*_clean` Boolean Fallback Path

- What's not tested: The `_is_governance_clean()`, `_is_market_clean()` functions in render sections that fire when `section_densities` is not populated
- Files: `src/do_uw/stages/render/sections/sect4_market.py:98`, `src/do_uw/stages/render/sections/sect5_governance.py:128`
- Risk: If ANALYZE stage fails to populate `section_densities`, render silently falls back to less accurate boolean logic with no indication
- Priority: **Medium**

---

### `store_bulk.py` Has `raise NotImplementedError` in Production Code

- File: `src/do_uw/knowledge/store_bulk.py:48`
- `# pragma: no cover` comment acknowledges it is untested
- Risk: Low (marked no cover), but it is importable production code that would crash if called

---

*Concerns audit: 2026-02-25*
