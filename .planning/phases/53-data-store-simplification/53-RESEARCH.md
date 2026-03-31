# Phase 53: Data Store Simplification - Research

**Researched:** 2026-02-28
**Domain:** Data layer unification (YAML/JSON runtime loading, loader consolidation, DuckDB scoping)
**Confidence:** HIGH

## Summary

Phase 53 replaces the DuckDB-intermediary pattern for brain signal definitions with direct YAML/JSON file reads at runtime. The current architecture has 4 competing loaders (`BrainDBLoader`, `BrainKnowledgeLoader`/`BackwardCompatLoader`, `ConfigLoader`, `brain_config_loader`) and 2 overlapping config directories (`config/` and `brain/config/`) with all 21 shared JSON files diverged. The new architecture consolidates to a single `BrainLoader` that reads YAML signals and JSON configs directly from disk, with module-level singleton caching.

The performance case is proven: PyYAML CSafeLoader loads all 400 signals from 36 YAML files in 66ms -- well under the 1-second target. DuckDB (brain.duckdb) retains its role for history/analytics tables only (brain_signal_runs, brain_effectiveness, brain_feedback, brain_changelog, brain_proposals). The `brain build` command becomes validate + export only.

Key risk: 21 config files have diverged between `config/` and `brain/config/` -- every single shared file has differences. A per-file merge review is required to select the canonical version before `config/` can be deleted. Additionally, approximately 30 import sites for `load_brain_config()` and 20+ for `BrainDBLoader`/`BrainKnowledgeLoader` need updating, though the function signatures can remain compatible.

**Primary recommendation:** Sequence work as (1) config consolidation, (2) YAML signal loader, (3) loader unification, (4) DuckDB scoping, (5) brain build simplification, (6) SNA output diff verification.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- brain/config/ is the single canonical location for ALL JSON config
- config/ directory gets deleted entirely -- all files (sic_naics_mapping.json, signal_classification.json, loader.py, etc.) move to brain/config/
- brain/ root JSON files (patterns.json, red_flags.json, scoring.json, sectors.json, signals.json) also move to brain/config/ -- brain/ root is for Python code only
- Config loading switches from DuckDB-first-with-JSON-fallback to direct JSON file reads from brain/config/
- 18+ sites currently calling `load_brain_config()` need updating to use the new unified loader
- `brain build` becomes validate + export only -- no more YAML->DuckDB sync, no more config->DuckDB sync
- Pipeline works zero-setup -- no `brain build` prerequisite for first run. Clone and run just works
- Pipeline does lazy validation on first YAML load -- invalid signals logged as warnings and skipped, pipeline continues
- Four loaders (BrainDBLoader, BrainKnowledgeLoader, BackwardCompatLoader, ConfigLoader) replaced by single BrainLoader
- All ~30 import sites updated to use new BrainLoader -- no shims, no re-exports, clean break
- compat_loader.py in knowledge/ also killed -- calibrate_impact.py and backtest.py call BrainLoader directly
- Module-level singleton caching: load YAML/JSON once on first call, serve from memory for duration of run
- Definition tables (~25 tables) stop being read at pipeline runtime
- History/analytics tables stay completely untouched
- History write paths remain exactly as-is -- no changes to how pipeline writes run data
- brain.duckdb continues to exist but becomes purely a history/analytics store

### Claude's Discretion
- Whether to drop definition tables from schema entirely or keep them as read-only archives
- Which brain CLI commands need updating vs which only read history tables
- Exact BrainLoader class API (methods, constructor signature, typed vs dict config access)
- Migration ordering within the phase (loaders first vs config first)
- brain build DuckDB access (whether to show history stats or go pure YAML/JSON)
- brain_changelog logging from brain build (keep or drop)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STORE-01 | Signals load from YAML at runtime -- BrainYAMLLoader reads 400 signals from brain/signals/ directly, no DuckDB intermediary. Load time < 1 second. | Benchmarked: CSafeLoader loads 400 signals in 66ms (36 YAML files). `load_signals_from_yaml()` in brain_migrate.py already implements the YAML glob+parse pattern. BrainSignalEntry Pydantic model validates each entry. |
| STORE-02 | Config directory consolidated -- 21 overlapping config files merged into single brain/config/ directory. config/ directory deleted. Import paths updated. | All 21 shared config files have diverged (diff analysis complete). 2 files only in config/ (sic_naics_mapping.json, signal_classification.json), 1 only in brain/config/ (check_classification.json). signal_classification.json and check_classification.json are the same file pre/post Phase 49 rename. Per-file merge review needed. 24 call sites for load_brain_config() identified. |
| STORE-03 | Single loader replaces 4 -- BrainDBLoader, BrainKnowledgeLoader, BackwardCompatLoader, ConfigLoader replaced by one BrainLoader. | Full import site audit: BrainDBLoader (10 src/ sites), BrainKnowledgeLoader (5 src/ sites + BackwardCompatLoader alias), load_brain_config (24 src/ sites), ConfigLoader (2 src/ sites via config/__init__.py). BrainConfig Pydantic model (from config/loader.py) is the return type -- must be preserved in new loader. |
| STORE-04 | DuckDB scoped to history only -- definition tables no longer read at pipeline runtime. | Identified all DuckDB definition table reads: brain_signals/views (BrainDBLoader, cli_brain status/export-docs/stats/export-all), brain_taxonomy (cli_brain status, BrainDBLoader.load_taxonomy), brain_config (brain_config_loader, cli_brain_ext export-all), brain_scoring_factors/meta/patterns/red_flags/sectors (BrainDBLoader.load_*), brain_coverage_matrix (brain_audit.py), brain_perils/causal_chains (BrainDBLoader, scoring_peril_data). History tables (brain_signal_runs, brain_effectiveness, brain_feedback, brain_changelog, brain_proposals, brain_meta, brain_backlog) stay unchanged. |
| STORE-05 | brain build simplified -- no longer migrates YAML->DuckDB for signal definitions. Only validates schema and exports signals.json. | Current brain build: build_checks_from_yaml() truncates + re-inserts brain_signals, build_framework() populates perils/chains. New behavior: YAML schema validation via BrainSignalEntry, cross-reference integrity checks, signals.json export. brain_changelog logging is at Claude's discretion (recommend keeping). |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.3 (installed) | YAML signal file parsing | CSafeLoader (C extension) gives 66ms load time for 400 signals. Already a dependency. |
| Pydantic v2 | installed | Signal/config schema validation | BrainSignalEntry already validates all 400 signals. BrainConfig is the aggregate return type. |
| DuckDB | 1.4.4+ (installed) | History/analytics store (write path unchanged) | Still needed for brain_signal_runs, brain_effectiveness, brain_feedback. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruamel.yaml | 0.19.1+ (installed) | YAML round-trip editing (brain apply/feedback) | Write-back only -- NOT for runtime reads (10x slower than CSafeLoader) |
| json (stdlib) | N/A | Config JSON file reads | Direct reads from brain/config/ |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML CSafeLoader | ruamel.yaml | ruamel.yaml preserves comments but is 10x slower (607ms vs 66ms). Use CSafeLoader for read-only runtime loading. |
| Module-level singleton | functools.lru_cache | Singleton pattern is simpler and matches existing lazy-import style across ~30 sites. lru_cache adds unnecessary complexity for a single-call-per-run pattern. |

## Architecture Patterns

### Recommended Project Structure (Post-Phase 53)
```
src/do_uw/brain/
  brain_loader.py        # NEW: unified BrainLoader (replaces 4 loaders)
  brain_signal_schema.py # EXISTING: BrainSignalEntry Pydantic model
  brain_schema.py        # EXISTING: DuckDB DDL (definition tables kept as read-only archive)
  brain_build_signals.py # MODIFIED: validate + export only (no DuckDB insert)
  brain_writer.py        # EXISTING: history/feedback writes (unchanged)
  brain_health.py        # EXISTING: already reads from YAML
  brain_audit.py         # EXISTING: already reads from YAML
  config/                # CANONICAL: all 23+ JSON config files
    actuarial.json
    activist_investors.json
    ...
    sic_naics_mapping.json    # moved from config/
    signal_classification.json # moved from config/ (merged with check_classification.json)
  signals/               # EXISTING: 36 YAML files, 400 signals
    fin/*.yaml
    gov/*.yaml
    lit/*.yaml
    stock/*.yaml
    biz/*.yaml
    exec/*.yaml
    fwrd/*.yaml
    nlp/*.yaml

src/do_uw/config/        # DELETED (all contents moved to brain/config/)
```

### Pattern 1: Singleton YAML/JSON Loader with Lazy Init
**What:** Module-level dict that loads once on first access, serves from memory thereafter.
**When to use:** All runtime signal/config reads.
**Example:**
```python
# brain_loader.py
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any
import yaml

logger = logging.getLogger(__name__)
_BRAIN_DIR = Path(__file__).parent

# Module-level cache -- populated on first call, serves for duration of run
_signals_cache: list[dict[str, Any]] | None = None
_config_cache: dict[str, dict[str, Any]] = {}

def load_signals() -> list[dict[str, Any]]:
    """Load all signals from YAML, cached for duration of process."""
    global _signals_cache
    if _signals_cache is not None:
        return _signals_cache

    signals_dir = _BRAIN_DIR / "signals"
    all_signals: list[dict[str, Any]] = []
    for yaml_file in sorted(signals_dir.glob("**/*.yaml")):
        data = yaml.load(yaml_file.read_text(), Loader=yaml.CSafeLoader)
        if isinstance(data, list):
            all_signals.extend(data)
        elif isinstance(data, dict) and "signals" in data:
            all_signals.extend(data["signals"])

    # Lazy validation: warn and skip invalid entries
    validated = _validate_signals(all_signals)
    _signals_cache = validated
    return validated

def load_config(key: str) -> dict[str, Any]:
    """Load a config JSON by key, cached for duration of process."""
    if key in _config_cache:
        return _config_cache[key]

    config_dir = _BRAIN_DIR / "config"
    json_path = config_dir / f"{key}.json"
    if not json_path.exists():
        logger.warning("Config '%s' not found at %s", key, json_path)
        return {}

    with open(json_path, encoding="utf-8") as f:
        result = json.load(f)
    _config_cache[key] = result
    return result
```

### Pattern 2: BrainConfig Aggregate Return Type (Preserved)
**What:** BrainConfig Pydantic model wraps all 5 data domains.
**When to use:** `BrainLoader.load_all()` -- same interface as current `BrainDBLoader.load_all()` and `BrainKnowledgeLoader.load_all()`.
**Example:**
```python
class BrainLoader:
    """Unified brain data loader: YAML signals + JSON configs."""

    def load_signals(self) -> dict[str, Any]:
        """Load signals as dict with 'signals' list."""
        signals = load_signals()  # module-level singleton
        return {"signals": signals, "total_signals": len(signals)}

    def load_scoring(self) -> dict[str, Any]:
        return load_config("scoring")  # or read brain/config/scoring.json

    def load_patterns(self) -> dict[str, Any]:
        return load_config("patterns")

    def load_red_flags(self) -> dict[str, Any]:
        return load_config("red_flags")

    def load_sectors(self) -> dict[str, Any]:
        return load_config("sectors")

    def load_all(self) -> BrainConfig:
        return BrainConfig(
            checks=self.load_signals(),
            scoring=self.load_scoring(),
            patterns=self.load_patterns(),
            sectors=self.load_sectors(),
            red_flags=self.load_red_flags(),
        )
```

### Pattern 3: Config File Merge Strategy
**What:** Per-file comparison to select canonical version for brain/config/.
**When to use:** Before deleting config/ directory.
**Decision matrix:**
- Files with minor whitespace/formatting diffs only: use brain/config/ version (newer timestamps)
- Files with substantive content diffs: brain/config/ is canonical (it was the target of `brain build` exports, which is the most recent sync point)
- Files only in config/: move to brain/config/ as-is
- check_classification.json (brain/config/) vs signal_classification.json (config/): merge -- they differ only in key name (`deprecated_check_ids` vs `deprecated_signal_ids`). Use `deprecated_signal_ids` (post-Phase 49 naming).

### Anti-Patterns to Avoid
- **Re-exporting old loader names from new module:** CONTEXT.md explicitly says "no shims, no re-exports, clean break." Update all import sites directly.
- **Loading YAML on every function call:** Module-level singleton ensures YAML is parsed exactly once per process. No per-call overhead.
- **Dropping DuckDB definition DDL:** Keep table definitions in brain_schema.py as read-only archive. Dropping them would break existing brain.duckdb files that have data in those tables.
- **Changing history write paths:** brain_signal_runs, brain_effectiveness, brain_feedback writes must remain exactly as-is. The only change is that definition tables are no longer *read* at pipeline runtime.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML loading | Custom parser | `yaml.load(text, Loader=yaml.CSafeLoader)` | C extension, 66ms for 400 signals, battle-tested |
| Signal validation | Custom validation | `BrainSignalEntry.model_validate(dict)` | Already exists, validates all 400 entries, catches schema drift |
| Config file merging | Automated merge tool | Manual per-file review | 21 diverged files need human judgment on which version is canonical |
| Backward-compat column mapping | New mapping logic | Existing `_WORK_TYPE_TO_CONTENT_TYPE`, `_LAYER_TO_HAZARD_OR_SIGNAL` dicts | Already in brain_build_signals.py, reuse for signal dict enrichment |

**Key insight:** The existing `load_signals_from_yaml()` function in `brain_migrate.py` already does 90% of what the new loader needs. The main addition is Pydantic validation and backward-compat field enrichment (content_type, category, hazard_or_signal) that currently happens in `brain_build_signals.py` during DuckDB insert.

## Common Pitfalls

### Pitfall 1: Backward-Compat Field Enrichment Gap
**What goes wrong:** Current `BrainDBLoader.load_signals()` returns dicts with backward-compat fields (`content_type`, `category`, `hazard_or_signal`, `section`, `_brain_*` metadata) that are populated during `brain build` DuckDB insert. Direct YAML loading misses these fields.
**Why it happens:** YAML files contain the new schema (`work_type`, `layer`, `tier`). The reverse-mapping to legacy fields happens in `brain_build_signals.py:build_checks_from_yaml()` which inserts into DuckDB. The loader then reads the enriched rows.
**How to avoid:** The new `BrainLoader.load_signals()` must apply the same backward-compat enrichment that `brain_build_signals.py` does -- specifically the `_WORK_TYPE_TO_CONTENT_TYPE`, `_LAYER_TO_HAZARD_OR_SIGNAL`, `_WORKSHEET_TO_REPORT_SECTION`, and `_derive_category()` mappings. Copy these as pure functions into the new loader or import from brain_build_signals.
**Warning signs:** Analyze stage crashes on missing `content_type` key, or `section` key returns wrong number.

### Pitfall 2: Config File Divergence Causes Silent Behavior Changes
**What goes wrong:** brain/config/ versions of config files have different thresholds, weights, or classifications than config/ versions. Switching to brain/config/ silently changes pipeline scoring behavior.
**Why it happens:** brain/config/ was populated by `brain build`/`brain export-all` which may have transformed data during round-trip through DuckDB. config/ was edited directly.
**How to avoid:** For each of the 21 diverged files, run a structural diff. For files where brain/config/ version is a superset or equivalent, use brain/config/. For files where config/ has newer data (e.g., sic_gics_mapping.json with 664 diff lines), carefully evaluate which version produces correct pipeline output. The SNA HTML diff is the ultimate arbiter.
**Warning signs:** Score differences in SNA output after config consolidation.

### Pitfall 3: CLI Commands Break When Definition Tables Are Empty
**What goes wrong:** `brain status`, `brain stats`, `brain export-docs`, `brain export-all` query definition tables (brain_signals, brain_taxonomy, brain_config, etc.) that may be empty after the transition.
**Why it happens:** These commands were written when DuckDB was the source of truth. They directly query brain_signals_active, brain_taxonomy_current, etc.
**How to avoid:** Update affected commands to read from YAML/JSON directly (same pattern as brain_health.py and brain_audit.py which already do this). `brain stats` can still show DuckDB table counts for history tables but should read signal counts from YAML.
**Warning signs:** `brain status` shows "0 signals" or crashes after Phase 53.

### Pitfall 4: Perils and Causal Chains Have No JSON/YAML Equivalent
**What goes wrong:** `BrainDBLoader.load_perils()` and `load_causal_chains()` read from DuckDB tables that are populated by `brain_build_signals.py:build_framework()`. There is no standalone JSON/YAML file for perils and chains outside of `brain/framework/` YAML files.
**Why it happens:** Framework data (perils, causal chains) was designed for DuckDB only. The YAML files exist in brain/framework/ but are only read during `brain build`.
**How to avoid:** Add perils and causal chains to the new BrainLoader. Either: (a) read from brain/framework/ YAML files directly at runtime (same pattern as signals), or (b) export to JSON in brain/config/ and load from there. Option (a) is more consistent with the YAML-first approach.
**Warning signs:** Render stage's `_get_scoring_peril_data()` returns empty dict, losing peril map in output.

### Pitfall 5: Test Fixtures Mock the Old Loaders
**What goes wrong:** Tests in tests/brain/test_brain_loader.py, tests/knowledge/test_compat_loader.py, tests/config/test_loader.py mock or instantiate the old loader classes. After removal, these tests fail or become meaningless.
**Why it happens:** Tests are tightly coupled to implementation classes.
**How to avoid:** Update tests to use BrainLoader. For tests that verify DuckDB interaction, keep them as integration tests for history table writes. For tests that verify signal loading behavior, rewrite to test BrainLoader against YAML fixtures.
**Warning signs:** Test count drops below 4,495 without replacement tests covering the same behaviors.

## Code Examples

### Loading Signals with Backward-Compat Enrichment
```python
# Source: brain_build_signals.py reverse maps + brain_loader_rows.py section map
# These must be applied to raw YAML dicts before returning to callers

_WORK_TYPE_TO_CONTENT_TYPE = {
    "extract": "MANAGEMENT_DISPLAY",
    "evaluate": "EVALUATIVE_CHECK",
    "infer": "INFERENCE_PATTERN",
}

_LAYER_TO_HAZARD_OR_SIGNAL = {
    "hazard": "HAZARD",
    "signal": "SIGNAL",
    "peril_confirming": "PERIL_CONFIRMING",
}

_WORKSHEET_TO_REPORT_SECTION = {
    "company_profile": "company",
    "financial": "financial",
    "governance": "governance",
    "litigation": "litigation",
    "stock_activity": "market",
    "management": "governance",
}

SECTION_MAP = {
    "company": 1, "market": 2, "financial": 3,
    "financials": 3, "governance": 4, "litigation": 5,
    "disclosure": 4, "forward": 1,
    "company_profile": 1, "stock_activity": 2, "management": 4,
}

def _enrich_signal(raw: dict) -> dict:
    """Apply backward-compat fields to raw YAML signal dict."""
    work_type = raw.get("work_type")
    layer = raw.get("layer")
    tier = raw.get("tier")
    worksheet_section = raw.get("worksheet_section")

    raw["content_type"] = _WORK_TYPE_TO_CONTENT_TYPE.get(work_type or "", "EVALUATIVE_CHECK")
    raw["hazard_or_signal"] = _LAYER_TO_HAZARD_OR_SIGNAL.get(layer or "", "SIGNAL")
    raw["category"] = "CONTEXT_DISPLAY" if tier == 1 and work_type == "extract" else "DECISION_DRIVING"

    report_section = _WORKSHEET_TO_REPORT_SECTION.get(worksheet_section or "", "company")
    raw["section"] = SECTION_MAP.get(worksheet_section or "", SECTION_MAP.get(report_section, 0))

    # data_strategy field_key extraction
    ds = raw.get("data_strategy")
    if ds and "field_key" in ds:
        raw.setdefault("data_strategy", ds)

    return raw
```

### Config Loading with brain/config/ as Single Source
```python
# Source: brain_config_loader.py simplified (no DuckDB lookup)
def load_brain_config(key: str) -> dict[str, Any]:
    """Load config JSON from brain/config/{key}.json."""
    if key in _config_cache:
        return _config_cache[key]

    config_dir = Path(__file__).parent / "config"
    json_path = config_dir / f"{key}.json"

    if not json_path.exists():
        logger.warning("Config '%s' not found at %s", key, json_path)
        return {}

    with open(json_path, encoding="utf-8") as f:
        result = json.load(f)

    _config_cache[key] = result
    logger.debug("Loaded config '%s' from %s", key, json_path)
    return result
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DuckDB as source of truth | YAML as source of truth (DuckDB = cache) | Phase 41 (conceptual), Phase 49-52 (partial) | brain_health.py and brain_audit.py already read YAML directly |
| ConfigLoader reads from brain/*.json | BrainDBLoader reads from DuckDB | Phase 41 | ConfigLoader deprecated but still used by 2 src/ sites |
| brain_config_loader: DuckDB-first with JSON fallback | Direct JSON reads | Phase 53 target | 24 call sites, signature stays compatible |
| KnowledgeStore (SQLite) as fallback | BrainKnowledgeLoader wraps BrainDBLoader | Phase 45 | KnowledgeStore is legacy, compat_loader wraps it |

**Already partially migrated (leverage this):**
- `brain_health.py`: Reads YAML directly via `load_signals_from_yaml()` (line 101)
- `brain_audit.py`: Reads YAML directly via `load_signals_from_yaml()` (line 24)
- `brain_build_signals.py`: Contains YAML->dict conversion with backward-compat enrichment
- `brain_migrate.py`: Contains `load_signals_from_yaml()` function

## Open Questions

1. **Config file canonical version selection**
   - What we know: All 21 shared config files have diverged. brain/config/ files have newer timestamps (2026-02-28) from `brain build` export. config/ files are the versions actively loaded by `load_brain_config()` as JSON fallback.
   - What's unclear: Whether brain/config/ versions are strictly better or if some config/ versions have manually applied corrections not reflected in brain/config/.
   - Recommendation: Run SNA pipeline with each directory as the config source. If output is identical, use brain/config/ (newer). If different, review diffs for the files that affect scoring (actuarial, hazard_weights, classification, settlement_calibration).

2. **Framework data (perils, causal chains) loading**
   - What we know: `brain/framework/` has YAML files for perils and causal chains. `BrainDBLoader.load_perils()` and `load_causal_chains()` read from DuckDB. `scoring_peril_data.py` calls these methods.
   - What's unclear: Whether framework YAML files follow the same format as DuckDB rows, or if `build_framework()` transforms them.
   - Recommendation: Add `load_perils()` and `load_causal_chains()` to new BrainLoader reading from framework/ YAML. The render stage fallback (returns empty dict on failure) provides safety during migration.

3. **BrainConfig model location after config/ deletion**
   - What we know: `BrainConfig` Pydantic model lives in `config/loader.py`. It is imported by `brain_loader.py`, `compat_loader.py`, and 5 test files.
   - What's unclear: Where to relocate it when config/ is deleted.
   - Recommendation: Move `BrainConfig` to `brain/brain_loader.py` (the new unified loader). Update all imports. The config/__init__.py re-export can be replaced with direct imports.

4. **Definition tables: drop DDL or keep as archive?**
   - What we know: Definition tables have 400 signals, taxonomy entries, scoring factors, etc. from last `brain build`. They are historical snapshots.
   - What's unclear: Whether any external tooling or analytics queries reference them.
   - Recommendation: Keep DDL in brain_schema.py but do not recreate/populate. Existing data stays readable. No runtime reads from pipeline. This is lowest risk.

## Import Site Audit

### BrainDBLoader (10 src/ sites -- all need updating)
| File | Line | Context |
|------|------|---------|
| `stages/acquire/brain_requirements.py` | 31 | Lazy import inside function |
| `stages/extract/extraction_manifest.py` | 269 | Lazy import inside function |
| `stages/render/scoring_peril_data.py` | 194 | Lazy import inside function |
| `cli_brain.py` | 62, 191 | `brain status`, `brain gaps` |
| `cli_brain_ext.py` | 82, 137, 367 | `brain backlog`, `brain export-docs`, `brain export-all` |
| `knowledge/compat_loader.py` | 70 | Inside `_try_brain_db_loader()` |
| `knowledge/calibrate_impact.py` | 98 | Lazy import |
| `knowledge/backtest.py` | 106 | Lazy import |

### BrainKnowledgeLoader (5 src/ sites -- all need updating)
| File | Line | Context |
|------|------|---------|
| `stages/analyze/__init__.py` | 19 | Top-level import |
| `stages/score/__init__.py` | 20 | Top-level import |
| `stages/benchmark/__init__.py` | 15 | Top-level import |
| `stages/render/sections/sect7_coverage_gaps.py` | 54 | Lazy import |
| `cli_knowledge_traceability.py` | 174 | Lazy import |

### load_brain_config (24 src/ call sites -- function signature stays compatible)
| File | Key(s) Used |
|------|-------------|
| `stages/extract/board_governance.py` | governance_weights |
| `stages/extract/sca_extractor.py` | lead_counsel_tiers |
| `stages/extract/tax_indicators.py` | tax_havens |
| `stages/extract/ownership_structure.py` | activist_investors |
| `stages/extract/xbrl_mapping.py` | xbrl_concepts |
| `stages/extract/profile_helpers.py` | tax_havens |
| `stages/extract/sol_mapper.py` | claim_types |
| `stages/analyze/temporal_engine.py` | temporal_thresholds |
| `stages/analyze/executive_forensics.py` | executive_scoring |
| `stages/analyze/executive_data.py` | executive_scoring |
| `stages/analyze/adverse_events.py` | adverse_events |
| `stages/analyze/pipeline_audit.py` | signal_classification |
| `stages/analyze/industry_claims.py` | industry_theories |
| `stages/analyze/forensic_composites.py` | forensic_models |
| `stages/analyze/layers/hazard/hazard_engine.py` | hazard_weights, hazard_interactions, classification |
| `stages/analyze/layers/classify/classification_engine.py` | classification |
| `stages/score/case_characteristics.py` | lead_counsel_tiers |
| `stages/score/settlement_prediction.py` | settlement_calibration |
| `stages/score/peril_mapping.py` | signal_classification, plaintiff_firms |
| `stages/score/ai_risk_scoring.py` | ai_risk_weights |
| `stages/score/__init__.py` | settlement_calibration, actuarial |
| `stages/benchmark/benchmark_enrichments.py` | actuarial |

### ConfigLoader (minimal -- 2 active src/ sites)
| File | Line | Context |
|------|------|---------|
| `config/__init__.py` | 3 | Re-export (will be deleted with config/) |
| `config/loader.py` | N/A | Definition site (BrainConfig model must be relocated) |

### Test Files (need updating but not urgent)
- `tests/brain/test_brain_loader.py` -- BrainDBLoader, ConfigLoader
- `tests/config/test_loader.py` -- ConfigLoader
- `tests/knowledge/test_compat_loader.py` -- BrainKnowledgeLoader, BrainConfig, ConfigLoader
- `tests/knowledge/test_persistent_store.py` -- BrainKnowledgeLoader, BrainConfig
- `tests/knowledge/test_integration.py` -- BrainKnowledgeLoader, BrainConfig
- `tests/knowledge/test_playbooks.py` -- BrainKnowledgeLoader
- `tests/knowledge/test_enriched_roundtrip.py` -- BrainKnowledgeLoader
- `tests/test_pattern_detection.py` -- ConfigLoader

## CLI Commands Requiring Updates

| Command | Current Data Source | Needs Update? | Reason |
|---------|-------------------|---------------|--------|
| `brain status` | DuckDB brain_signals, brain_taxonomy | YES | Reads definition tables for signal/taxonomy counts |
| `brain gaps` | BrainDBLoader.load_signals() | YES | Uses BrainDBLoader |
| `brain effectiveness` | DuckDB brain_signal_runs only | NO | Only reads history tables |
| `brain build` | YAML -> DuckDB | YES | Core behavior change: validate + export only |
| `brain changelog` | brain_changelog (DuckDB) | NO | History table only |
| `brain backlog` | BrainDBLoader.load_backlog() | YES | Uses BrainDBLoader (brain_backlog is history-ish) |
| `brain export-docs` | DuckDB brain_signals_active | YES | Reads definition table |
| `brain backtest` | BrainKnowledgeLoader via backtest.py | YES | Uses old loader |
| `brain stats` | DuckDB all tables (row counts) | PARTIAL | Can show history table counts; signal counts from YAML |
| `brain export-all` | BrainDBLoader (all methods) | YES | Major rewrite to read YAML/JSON |
| `brain import-json` | JSON -> DuckDB | DECIDE | May become obsolete if DuckDB definitions are no longer needed |
| `brain health` | YAML + DuckDB history | NO | Already reads YAML for definitions |
| `brain audit` | YAML + DuckDB coverage_matrix | PARTIAL | Already reads YAML; coverage_matrix view references definition tables |
| `brain validate` | YAML directly | NO | Already reads YAML |
| `brain unlinked` | YAML directly | NO | Already reads YAML |
| `brain trace` | Facets + state.json | NO | Does not read DuckDB definition tables |

## Sources

### Primary (HIGH confidence)
- Codebase analysis of all 4 loader implementations (brain_loader.py, brain_config_loader.py, compat_loader.py, config/loader.py)
- Codebase analysis of all import sites via grep (comprehensive audit above)
- PyYAML CSafeLoader benchmark: 66ms for 400 signals from 36 files (run in-process)
- Config file divergence analysis: all 21 shared files confirmed diverged via diff
- brain_schema.py DDL: 19 tables, 11 views -- definition vs history classification confirmed

### Secondary (MEDIUM confidence)
- brain_health.py and brain_audit.py already demonstrate the YAML-direct-read pattern (validates approach)
- `brain_build_signals.py` backward-compat enrichment logic confirmed complete and reusable

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- PyYAML/Pydantic already in use, benchmark confirms performance
- Architecture: HIGH -- Pattern proven by brain_health.py and brain_audit.py
- Pitfalls: HIGH -- Identified from direct code analysis of all loader paths and backward-compat mappings
- Config divergence: MEDIUM -- File diffs quantified but canonical version selection requires per-file review

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (stable internal codebase, no external dependency changes)
