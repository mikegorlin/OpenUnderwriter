# Brain Redundancy Audit

**Date**: 2026-02-28
**Principle**: YAML is the brain. Everything else is a cache, a view, or should be eliminated.

---

## 1. Data Store Map

### Where Data Lives (7 locations for signal definitions alone)

| Store | Technology | Signal Count | Purpose | Canonical? |
|-------|-----------|-------------|---------|-----------|
| `brain/signals/**/*.yaml` (36 files) | YAML | **400** | Source of truth for signal definitions | **YES** |
| `brain/signals.json` | JSON | 380 | Legacy import/export format | NO (20 signals behind YAML) |
| `brain.duckdb` → `brain_signals` | DuckDB | 400 | Runtime query cache | NO (rebuilt from YAML via `brain build`) |
| `brain.duckdb` → `brain_checks` | DuckDB | 803 (403 distinct, 2 versions) | **LEGACY DUPLICATE** — old table name | NO (orphaned) |
| `knowledge.db` | SQLite | 0 (93MB file, empty signals) | **DEAD** — KnowledgeStore has 0 signals | NO (deprecated) |
| `brain.duckdb` → `brain_check_runs` | DuckDB | 384,549 | **LEGACY** run history (old table name) | Partially (historical data) |
| `brain.duckdb` → `brain_signal_runs` | DuckDB | 20,448 | Current run history | YES for run history |

### Redundant DuckDB Tables (legacy "check" naming coexists with "signal" naming)

| Legacy Table | Rows | Current Equivalent | Rows | Status |
|-------------|------|-------------------|------|--------|
| `brain_checks` | 803 | `brain_signals` | 400 | **REDUNDANT** — same schema, old data |
| `brain_check_runs` | 384,549 | `brain_signal_runs` | 20,448 | **REDUNDANT** — old run history |
| `brain_check_effectiveness` | 419 | `brain_effectiveness` | 0 | **REDUNDANT** — old effectiveness data |
| `brain_checks_active` (view) | — | `brain_signals_active` (view) | — | **REDUNDANT** view |
| `brain_checks_current` (view) | — | `brain_signals_current` (view) | — | **REDUNDANT** view |

### DuckDB Tables That Should Remain (run history / feedback — NOT signal definitions)

| Table | Rows | Role | Keep? |
|-------|------|------|-------|
| `brain_signal_runs` | 20,448 | Per-ticker evaluation history | YES |
| `brain_changelog` | 1,202 | Signal version audit trail | YES |
| `brain_feedback` | 0 | User feedback on signals | YES |
| `brain_proposals` | 3 | Auto-generated improvement proposals | YES |
| `brain_effectiveness` | 0 | Computed signal quality metrics | YES |
| `brain_meta` | 8 | Build metadata (timestamps, versions) | YES |

### DuckDB Tables That Are Caches of YAML/JSON (rebuilt by `brain build`)

| Table | Rows | Source | Action |
|-------|------|--------|--------|
| `brain_signals` | 400 | `brain/signals/**/*.yaml` | Keep as cache, read YAML directly in v2.0 |
| `brain_scoring_factors` | 10 | `brain/scoring.json` | Migrate to YAML, then cache |
| `brain_scoring_meta` | 8 | `brain/scoring.json` | Migrate to YAML, then cache |
| `brain_patterns` | 19 | `brain/patterns.json` | Migrate to YAML, then cache |
| `brain_red_flags` | 17 | `brain/red_flags.json` | Migrate to YAML, then cache |
| `brain_sectors` | 95 | `brain/sectors.json` | Migrate to YAML, then cache |
| `brain_taxonomy` | 75 | Derived during migration | Migrate to YAML |
| `brain_config` | 22 | `config/*.json` files | See Config Redundancy below |
| `brain_backlog` | 7 | Seeded by migration script | Migrate to YAML |
| `brain_perils` | 8 | Defined in migration code | Migrate to YAML |
| `brain_causal_chains` | 16 | Defined in migration code | Migrate to YAML |
| `brain_industry` | 0 | Never populated | DROP |
| `brain_risk_framework` | 19 | Defined in migration code | Migrate to YAML |

---

## 2. Config Redundancy Table

### Dual-Location Configs: `config/` vs `brain/config/` (ALL 21 are DIFFERENT)

| File | config/ size | brain/config/ size | Identical? | Which is canonical? |
|------|-------------|-------------------|-----------|-------------------|
| `activist_investors.json` | 620B | 687B | DIFFERENT | brain/config/ (more complete) |
| `actuarial.json` | 1,591B | 1,784B | DIFFERENT | brain/config/ (more complete) |
| `adverse_events.json` | 624B | 623B | DIFFERENT | Unclear (1B diff) |
| `ai_risk_weights.json` | 1,173B | 1,158B | DIFFERENT | Unclear |
| `claim_types.json` | 2,177B | 2,176B | DIFFERENT | Unclear (1B diff) |
| `classification.json` | 1,457B | 1,840B | DIFFERENT | brain/config/ (383B larger) |
| `executive_scoring.json` | 1,007B | 1,006B | DIFFERENT | Unclear (1B diff) |
| `forensic_models.json` | 1,956B | 2,307B | DIFFERENT | brain/config/ (351B larger) |
| `governance_weights.json` | 585B | 581B | DIFFERENT | Unclear (4B diff) |
| `hazard_interactions.json` | 2,354B | 2,771B | DIFFERENT | brain/config/ (417B larger) |
| `hazard_weights.json` | 19,822B | 20,797B | DIFFERENT | brain/config/ (975B larger) |
| `industry_theories.json` | 7,319B | 9,118B | DIFFERENT | brain/config/ (1,799B larger) |
| `lead_counsel_tiers.json` | 531B | 530B | DIFFERENT | Unclear (1B diff) |
| `plaintiff_firms.json` | 843B | 842B | DIFFERENT | Unclear (1B diff) |
| `rate_decay.json` | 457B | 453B | DIFFERENT | Unclear (4B diff) |
| `render_thresholds.json` | 530B | 491B | DIFFERENT | config/ (39B larger) |
| `settlement_calibration.json` | 1,384B | 1,401B | DIFFERENT | brain/config/ |
| `sic_gics_mapping.json` | 10,200B | 12,053B | DIFFERENT | brain/config/ (1,853B larger, more SIC codes) |
| `tax_havens.json` | 2,455B | 3,222B | DIFFERENT | brain/config/ (767B larger) |
| `temporal_thresholds.json` | 1,775B | 1,774B | DIFFERENT | Unclear (1B diff) |
| `xbrl_concepts.json` | 17,333B | 17,332B | DIFFERENT | Unclear (1B diff) |

### Files in Only One Location

| File | Location | Notes |
|------|----------|-------|
| `sic_naics_mapping.json` | config/ only | Not in brain/config/ |
| `signal_classification.json` | config/ only | Not in brain/config/ |
| `check_classification.json` | brain/config/ only | Not in config/ |

### Config Loading Path (Triple Indirection)

1. `load_brain_config("key")` checks DuckDB `brain_config_current` FIRST
2. Falls back to `config/{key}.json` on disk
3. brain/config/ files are NEVER directly read at runtime (only imported into DuckDB by `brain_migrate_config.py`)
4. Result: `config/` files are the JSON fallback, `brain/config/` files are the DuckDB source, and they have **diverged in ALL 21 cases**

### Config Consumers (23 call sites for `load_brain_config`)

All in EXTRACT, ANALYZE, SCORE, BENCHMARK stages:
- `board_governance.py` → governance_weights
- `sca_extractor.py` → lead_counsel_tiers
- `tax_indicators.py` → tax_havens
- `ownership_structure.py` → activist_investors
- `xbrl_mapping.py` → xbrl_concepts
- `profile_helpers.py` → tax_havens
- `sol_mapper.py` → claim_types
- `temporal_engine.py` → temporal_thresholds
- `executive_forensics.py` → executive_scoring
- `pipeline_audit.py` → signal_classification
- `industry_claims.py` → industry_theories
- `adverse_events.py` → adverse_events
- `hazard_engine.py` → hazard_weights, hazard_interactions, classification
- `classification_engine.py` → classification
- `forensic_composites.py` → forensic_models
- `executive_data.py` → executive_scoring
- `ai_risk_scoring.py` → ai_risk_weights
- `case_characteristics.py` → lead_counsel_tiers
- `score/__init__.py` → settlement_calibration, actuarial
- `settlement_prediction.py` → settlement_calibration
- `peril_mapping.py` → signal_classification, plaintiff_firms
- `benchmark_enrichments.py` → actuarial

---

## 3. Loader Dependency Graph

### Current Loaders (4 loaders for brain data)

```
                    +-----------------------+
                    |    ConfigLoader        |  config/loader.py
                    |  (JSON file reader)    |  DEPRECATED but still imported by tests
                    |  Reads: brain/*.json   |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |   BrainDBLoader       |  brain/brain_loader.py
                    |  (DuckDB reader)      |  PRIMARY for signals/scoring/patterns/
                    |  Reads: brain.duckdb  |  red_flags/sectors
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    | BrainKnowledgeLoader  |  knowledge/compat_loader.py
                    |  (Wrapper/validator)   |  Delegates to BrainDBLoader, falls back
                    |  Falls back to:       |  to KnowledgeStore (SQLite)
                    |  KnowledgeStore       |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    | load_brain_config()   |  brain/brain_config_loader.py
                    | (KV config reader)    |  DuckDB first, JSON fallback
                    | For: actuarial, etc.  |  Used by 23 call sites
                    +-----------------------+
```

### Consumer Map

| Consumer | Loader Used | Data Loaded |
|----------|------------|-------------|
| `AnalyzeStage.run()` | `BrainKnowledgeLoader` | signals, scoring, patterns, red_flags, sectors |
| `ScoreStage.run()` | `BrainKnowledgeLoader` | scoring, patterns, red_flags, sectors |
| `BenchmarkStage.run()` | `BrainKnowledgeLoader` | sectors, actuarial |
| `brain stats` CLI | `BrainDBLoader` (direct) | signals, taxonomy, backlog |
| `brain trace` CLI | `BrainDBLoader` (direct) | signals |
| `brain export-all` CLI | `BrainDBLoader` (direct) | all |
| 23 extract/analyze/score modules | `load_brain_config()` | individual config files |
| `tests/` | `ConfigLoader` | JSON files directly |
| `knowledge/learning.py` | `KnowledgeStore` | notes, outcomes |
| `knowledge/narrative.py` | `KnowledgeStore` | check metadata |
| `knowledge/provenance.py` | `KnowledgeStore` | provenance records |
| `knowledge/playbooks.py` | `KnowledgeStore` | industry playbooks |

### Proposed: ONE Path Per Data Type

| Data Type | v2.0 Loader | Source |
|-----------|------------|--------|
| Signal definitions | `YAMLSignalLoader` (new) | `brain/signals/**/*.yaml` directly |
| Scoring factors | `YAMLSignalLoader` | `brain/framework/scoring.yaml` (new) |
| Patterns | `YAMLSignalLoader` | `brain/framework/patterns.yaml` (new) |
| Red flags | `YAMLSignalLoader` | `brain/framework/red_flags.yaml` (new) |
| Sector baselines | `YAMLSignalLoader` | `brain/framework/sectors.yaml` (new) |
| Config KV (actuarial, etc.) | `load_brain_config()` | `brain/config/*.yaml` (migrated from JSON) |
| Run history | DuckDB direct | `brain.duckdb` (keep for history) |
| Feedback/proposals | DuckDB direct | `brain.duckdb` (keep for writes) |

---

## 4. Signal Overlaps

### YAML vs JSON vs DuckDB Signal Count Mismatch

| Store | Count | Notes |
|-------|-------|-------|
| YAML | **400** | Canonical, includes 20 INACTIVE signals |
| signals.json | 380 | 20 signals behind YAML (INACTIVE ones not in JSON) |
| brain_signals (DuckDB) | 400 | Matches YAML (rebuilt via `brain build`) |
| brain_checks (DuckDB) | 803 (403 distinct) | **LEGACY** — 3 extra IDs: DOC.QA.001, GOV.DOC.ARCHIVE, GOV.DOC_INTEGRITY |

### FIELD_FOR_CHECK vs YAML data_strategy.field_key

| Metric | Count |
|--------|-------|
| FIELD_FOR_CHECK entries (Python dict) | 263 |
| YAML data_strategy.field_key entries | 270 |
| Exact matches (same signal_id + same value) | **263** (100%) |
| YAML-only (7 signals with field_key not in dict) | 7 |
| Mismatches | **0** |

**Conclusion**: FIELD_FOR_CHECK is 100% redundant with YAML. The 263 entries in the Python dict are exactly duplicated in YAML. The 7 extra YAML entries are newer signals. The Python dict can be eliminated entirely once `narrow_result()` uses YAML field_key exclusively (already priority 1 in resolution order).

---

## 5. Hardcoded Logic That Should Be YAML

### signal_field_routing.py — FIELD_FOR_CHECK (263 entries, 371 lines)
- **100% replaceable by YAML `data_strategy.field_key`**
- `narrow_result()` already checks `data_strategy.field_key` FIRST (line 32-39)
- FIELD_FOR_CHECK is only hit when signal_def lacks data_strategy
- **Action**: Add field_key to remaining 130 YAML signals that lack data_strategy, then delete FIELD_FOR_CHECK

### signal_mappers.py family (5 files, 2,357 lines total)
- `signal_mappers.py` — 505 lines, prefix routing + company/financial/market mappers
- `signal_mappers_sections.py` — 477 lines, governance + litigation mappers
- `signal_mappers_analytical.py` — 462 lines, Phase 26 analytical mappers
- `signal_mappers_forward.py` — 377 lines, forward-looking signal mappers
- `signal_mappers_ext.py` — 165 lines, text signal helpers
- **These contain COMPUTED data extraction logic** — not simple lookups. They unwrap SourcedValues, count lists, derive ratios, filter boilerplate. Cannot be replaced by YAML config alone.
- **However**: The prefix-based routing (BIZ/STOCK/FIN/LIT/GOV) could be driven by YAML `worksheet_section` field instead of hardcoded prefix parsing

### brain_build_signals.py — Backward Compat Reverse Maps (lines 28-51)
- `_WORK_TYPE_TO_CONTENT_TYPE` — maps new YAML fields to legacy DuckDB columns
- `_LAYER_TO_HAZARD_OR_SIGNAL` — same
- `_WORKSHEET_TO_REPORT_SECTION` — same
- **Action**: Once all consumers use new field names, delete these maps

### brain_loader.py — _FACTOR_KEY_MAP (lines 25-36)
- Maps DuckDB `factor_id` (F.1-F.10) to Python dict keys (F1_prior_litigation, etc.)
- **Action**: Move to YAML scoring definition, eliminate hardcoded map

### signal_engine.py — _SOURCE_TO_EXTRACTOR (lines 236-247)
- Maps required_data sources to extractor module names
- **Action**: Move to signal YAML `data_strategy.sources` field

---

## 6. Knowledge System Status

### knowledge.db (SQLite via KnowledgeStore) — ASSESSMENT: MOSTLY DEAD

| Metric | Value |
|--------|-------|
| File size | 93MB |
| Signal count | **0** (empty) |
| Still imported by | 15+ modules in `src/do_uw/knowledge/` |
| Active consumers | `learning.py`, `narrative.py`, `provenance.py`, `playbooks.py` |
| Dead consumers | Signal loading (0 signals), scoring rules, patterns, sectors, red flags |

**Remaining live uses of KnowledgeStore**:
1. **Playbooks** (`playbooks.py`) — industry-specific signal supplements. Could move to YAML.
2. **Learning/outcomes** (`learning.py`) — analysis outcome tracking. Could move to DuckDB brain tables.
3. **Narrative generation** (`narrative.py`) — check-to-narrative mapping. Reads from KnowledgeStore metadata.
4. **Provenance** (`provenance.py`) — data lineage tracking. ORM-based writes.
5. **Notes** (`store.py`) — free-text underwriting notes with FTS5 search.

**Recommendation**: Migrate playbooks to YAML, learning/feedback to DuckDB brain tables, and deprecate KnowledgeStore entirely. The 93MB file with 0 signals is dead weight.

---

## 7. Proposed Clean Architecture

```
YAML (Source of Truth)                    DuckDB (History Only)
========================                  ========================
brain/signals/**/*.yaml (400)    --->     brain_signal_runs (history)
brain/framework/scoring.yaml     --->     brain_changelog (audit)
brain/framework/patterns.yaml    --->     brain_feedback (user input)
brain/framework/red_flags.yaml   --->     brain_proposals (auto)
brain/framework/sectors.yaml     --->     brain_effectiveness (computed)
brain/framework/taxonomy.yaml    --->     brain_meta (build info)
brain/framework/perils.yaml
brain/framework/chains.yaml
brain/config/*.yaml (21 files)

         |                                         |
         v                                         v
  YAMLBrainLoader (NEW)               DuckDB direct queries
  - PyYAML CSafeLoader (~65ms)         - Run history analytics
  - Validates via BrainSignalEntry     - Effectiveness computation
  - Returns BrainConfig                - Feedback loop reads
  - NO DuckDB dependency               - Proposal management
         |
         v
   Pipeline Stages
   (ACQUIRE -> EXTRACT -> ANALYZE -> SCORE -> BENCHMARK -> RENDER)
         |
         v
   DuckDB (writes run results back to history tables)
```

### What Gets Eliminated

| Component | Lines | Action |
|-----------|-------|--------|
| `ConfigLoader` (config/loader.py) | 326 | Delete class, keep `BrainConfig` model |
| `BrainDBLoader` (brain/brain_loader.py) | 442 | Replace with `YAMLBrainLoader` |
| `BrainKnowledgeLoader` (knowledge/compat_loader.py) | 357 | Delete entirely |
| `KnowledgeStore` (knowledge/store.py + 5 helpers) | ~1,500 | Delete after migrating playbooks/notes |
| `FIELD_FOR_CHECK` dict (signal_field_routing.py) | 263 entries | Delete (YAML field_key covers 100%) |
| `brain/signals.json` | 364KB | Delete (YAML is canonical, 20 signals ahead) |
| `brain/scoring.json` | 13KB | Migrate to YAML, then delete |
| `brain/patterns.json` | 18KB | Migrate to YAML, then delete |
| `brain/red_flags.json` | 9KB | Migrate to YAML, then delete |
| `brain/sectors.json` | 21KB | Migrate to YAML, then delete |
| `brain_checks` table | 803 rows | DROP (legacy duplicate of brain_signals) |
| `brain_check_runs` table | 384,549 rows | Merge into brain_signal_runs, then DROP |
| `brain_check_effectiveness` table | 419 rows | Merge into brain_effectiveness, then DROP |
| `config/*.json` (21 files) | ~73KB | Keep as fallback during migration, then delete |
| `brain/config/*.json` (22 files) | ~77KB | Migrate to `brain/config/*.yaml`, then delete |
| `knowledge.db` | 93MB | Delete (0 signals, remaining uses migrated) |
| Backward compat maps in `brain_build_signals.py` | ~25 lines | Delete once consumers use new fields |

**Total elimination**: ~3,000 lines of loader code, ~600KB of duplicate data files, 93MB dead database.

---

## 8. Deprecation Plan

### Phase 1: Eliminate Dead Weight (Safe, No Behavior Change)
1. DROP `brain_checks`, `brain_checks_active`, `brain_checks_current` tables
2. Merge `brain_check_runs` data into `brain_signal_runs` (384K historical rows), then DROP
3. Merge `brain_check_effectiveness` into `brain_effectiveness`, then DROP
4. DROP `brain_industry` table (0 rows, never populated)
5. Delete `knowledge.db` (0 signals, 93MB)
6. **Safety**: Run full pipeline before/after, compare output

### Phase 2: YAML Direct Loading (Phase 53 Target)
1. Build `YAMLBrainLoader` — reads YAML directly via PyYAML CSafeLoader
2. Add `field_key` to remaining 130 YAML signals that lack `data_strategy`
3. Shadow-test: run both old (DuckDB) and new (YAML) loaders, assert identical output
4. Switch pipeline to `YAMLBrainLoader`
5. Delete `FIELD_FOR_CHECK` dict entirely (now 100% covered by YAML)
6. Delete `BrainDBLoader` (no longer needed for signal loading)
7. Delete `BrainKnowledgeLoader` and `BackwardCompatLoader` alias
8. Delete `ConfigLoader` class (keep `BrainConfig` model)
9. **Safety**: Shadow evaluation with zero discrepancy threshold

### Phase 3: Config Consolidation
1. Diff all 21 config file pairs, determine canonical version for each
2. Migrate canonical versions to `brain/config/*.yaml`
3. Update `load_brain_config()` to read YAML directly (no DuckDB)
4. Delete `brain_config` DuckDB table
5. Delete `config/*.json` files (21 files)
6. Delete `brain/config/*.json` files (22 files)
7. **Safety**: Config value comparison before/after

### Phase 4: JSON Export Elimination
1. Delete `brain/signals.json` (YAML is 20 signals ahead already)
2. Delete `brain/scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json`
3. Migrate scoring/patterns/red_flags/sectors to `brain/framework/*.yaml`
4. Remove `_validate_yaml_json_sync()` check from `brain_build_signals.py`
5. **Safety**: Verify `brain build` works without JSON files

### Phase 5: KnowledgeStore Deprecation
1. Migrate playbooks to YAML (`brain/playbooks/*.yaml`)
2. Migrate learning/outcomes to DuckDB brain tables
3. Migrate notes to DuckDB (or drop if unused)
4. Delete `knowledge/store.py`, `store_bulk.py`, `store_converters.py`, `store_search.py`
5. Delete `knowledge/migrate.py`
6. Delete `knowledge/models.py` (SQLAlchemy ORM models)
7. **Safety**: Verify all `knowledge/` consumers are rewired
