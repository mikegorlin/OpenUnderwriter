# Phase 44: Brain Unification — YAML Knowledge Model, Self-Describing Checks, Live Learning Loop - Research

**Researched:** 2026-02-24
**Domain:** Internal knowledge architecture — YAML schema design, DuckDB cache pipeline, Python migration tooling
**Confidence:** HIGH (all findings from direct codebase inspection; no external library research needed)

---

## Summary

Phase 44 replaces the split brain (framework YAML + checks JSON + DuckDB as independent sources) with a single unified YAML knowledge model where every check is self-describing across three orthogonal axes. The design is fully specified in ROADMAP.md and .continue-here.md — no architectural decisions remain open. This research documents the exact current-state field inventory, the DuckDB schema delta needed, the loader impact, and migration risks.

The current system has 400 checks in checks.json with 24 fields each, 21 INFERENCE_PATTERN entries that are also in patterns.json (redundant), and 17 red_flags.json entries that are standalone escalation rules. DuckDB currently has ~80 columns in brain_checks — many are classification proxies for the same underlying dimension (content_type, category, signal_type, hazard_or_signal). The new schema collapses these into three canonical fields: work_type, acquisition_tier, and risk_position (layer + peril_ids + chain_roles + factors).

**Primary recommendation:** Migrate in strict sequence — schema first (YAML + brain/SCHEMA.md), then checks.json → 8 YAML files, then brain build pipeline, then absorb patterns/red_flags, then brain add CLI. Each plan should leave DuckDB fully functional after its wave.

---

<user_constraints>
## User Constraints (from .continue-here.md decisions)

### Locked Decisions
- Work type is the missing fundamental dimension: extract | evaluate | infer (not content_type/category/hazard_or_signal)
- 3 axes, orthogonal: work_type (what it does) + risk_position (where in framework) + acquisition_tier (how hard to get data)
- Presentation in checks = just 2 fields: worksheet_section + display_when. NOT layout/HTML/template details
- DuckDB = pure cache: rebuilt from YAML via brain build. Nothing enters DuckDB that isn't first declared in YAML
- Split checks by domain prefix: brain/checks/biz.yaml, fin.yaml, gov.yaml, exec.yaml, lit.yaml, stock.yaml, fwrd.yaml, nlp.yaml (8 files)
- 117 checks already cross-referenced in causal_chains.yaml: auto-populate chain_roles during migration
- 283 checks have no chain: correctly flagged as unlinked (human backlog), not silently wrong

### Deprecation Targets (after migration complete)
- checks.json, patterns.json, red_flags.json
- brain_migrate_config.py, brain_migrate_framework.py, brain_migrate_scoring.py (simplified)
- enrichment_data.py, enrichment_data_ext.py
- BackwardCompatLoader

### Claude's Discretion
- Exact YAML field names (within the 3-axis model)
- brain build error handling and validation UX
- brain add CLI interface details
- Test strategy for YAML-DuckDB round-trip validation
- Whether brain validate is a subcommand or part of brain build

### Deferred Ideas (OUT OF SCOPE)
- Retroactive scoring recalibration using new chain_roles
- UI for browsing the brain (that's a future phase)
- Automated article decomposition (AI-assisted) — only the manual workflow is in scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ARCH-09 | Unified YAML knowledge model: every check self-describing across work_type / risk_position / acquisition_tier axes. DuckDB = pure cache. brain build pipeline. Live learning loop. | Field mapping table (Section below), DuckDB delta columns, loader method impact, migration sequence |
</phase_requirements>

---

## Standard Stack

### Core (all already in project)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| PyYAML / ruamel.yaml | already in use (framework YAMLs) | Load/write YAML files | Check pyproject.toml for which one is available |
| duckdb | already in use | Brain cache database | No version change needed |
| Pydantic v2 | already in use | Check schema validation | Use for YAML → Python model before DuckDB write |
| Typer | already in use | brain add / brain build / brain validate CLI | brain_writer.py already uses Typer |

### No new dependencies needed
All tooling is already present. This phase is pure reorganization + pipeline work.

---

## Field Mapping: checks.json → Unified YAML

### Complete Field Inventory (24 fields in checks.json)

| checks.json Field | Status | Maps To in YAML | Notes |
|-------------------|--------|-----------------|-------|
| `id` | KEEP | `id` | Unchanged — domain prefix drives file assignment |
| `name` | KEEP | `name` | Unchanged |
| `section` | REPLACE | `worksheet_section` | Old int (1-7) → semantic string (e.g., "company_profile") |
| `pillar` | ELIMINATE | (removed) | Redundant with work_type + layer |
| `factors` | KEEP | `factors` (list) | F1-F10 scoring factor IDs |
| `required_data` | RENAME | `required_data` | Keep as-is, feeds acquisition_tier derivation |
| `data_locations` | KEEP | `data_locations` | Where in filing to find the data |
| `threshold` | KEEP | `threshold` | Unchanged structure |
| `execution_mode` | KEEP | `execution_mode` | AUTO / MANUAL |
| `claims_correlation` | KEEP | `claims_correlation` | Float 0-1 |
| `tier` | KEEP | `tier` | 1-3 (criticality) |
| `category` | ELIMINATE | (removed) | Was CONTEXT_DISPLAY / DECISION_DRIVING / etc — proxy for work_type |
| `signal_type` | ELIMINATE | (removed) | Was STRUCTURAL / PATTERN / etc — redundant after work_type |
| `hazard_or_signal` | ELIMINATE | (removed) | Was HAZARD / SIGNAL / PERIL_CONFIRMING — maps to layer in risk_position |
| `content_type` | REPLACE | `work_type` | MANAGEMENT_DISPLAY→extract, EVALUATIVE_CHECK→evaluate, INFERENCE_PATTERN→infer |
| `plaintiff_lenses` | KEEP | `plaintiff_lenses` | SHAREHOLDERS / BONDHOLDERS / etc |
| `depth` | KEEP | `depth` | 1-3 analysis depth |
| `pattern_ref` | KEEP (infer only) | `pattern_ref` | Only present on infer-type checks |
| `data_strategy` | KEEP | `data_strategy` | field_key + primary_source |
| `v6_subsection_ids` | KEEP | `v6_subsection_ids` | Links to taxonomy subsection |
| `amplifier` | KEEP (conditional) | `amplifier` | Only on checks with amplifier_bonus_points |
| `amplifier_bonus_points` | KEEP (conditional) | `amplifier_bonus_points` | Only on scoring amplifier checks |
| `sector_adjustments` | KEEP (conditional) | `sector_adjustments` | Industry-specific overrides |
| `extraction_hints` | KEEP (conditional) | `extraction_hints` | NLP/regex hints |

### New Fields Added in Unified YAML

| New YAML Field | Type | Purpose | Source During Migration |
|----------------|------|---------|------------------------|
| `work_type` | enum: extract/evaluate/infer | Replaces content_type | content_type→work_type map (below) |
| `layer` | enum: hazard/signal/peril_confirming | Risk framework position | hazard_or_signal field (rename) |
| `peril_ids` | list[str] | Which perils this check informs | From causal_chains.yaml lookup; empty list if unlinked |
| `chain_roles` | dict | Role per chain: trigger/amplifier/mitigator/evidence | Auto-populated for 117 checks; {} for unlinked 283 |
| `acquisition_tier` | enum: L1/L2/L3/L4 | How hard to acquire data | Derived from required_data values |
| `worksheet_section` | str | Semantic section name | Derived from section int + subsection |
| `display_when` | str | Filtering condition | New field; defaults to "always" or "has_data" |
| `provenance` | dict | Source article/doc + date + author | New; empty for migrated checks, filled by brain add |
| `unlinked` | bool | True if no chain_roles | Set True for 283 unlinked checks; False for 117 |

### content_type → work_type Mapping

| content_type (old) | Count | work_type (new) | Rationale |
|--------------------|-------|-----------------|-----------|
| `MANAGEMENT_DISPLAY` | 99 | `extract` | Pulls structured data from filings, no evaluation |
| `EVALUATIVE_CHECK` | 280 | `evaluate` | Applies threshold logic to extracted values |
| `INFERENCE_PATTERN` | 21 | `infer` | Combines multiple signals into higher-order finding |

### acquisition_tier Derivation Rules

| required_data value | acquisition_tier |
|---------------------|-----------------|
| SEC_10K, SEC_10Q, SEC_8K, XBRL_* | L1 (structured XBRL/filing) |
| Filing text items (item_1, item_7, etc.) | L2 (filing text) |
| MARKET_PRICE, NEWS, COURT_RECORDS, WEB_* | L3 (web/market) |
| Computed from other checks | L4 (derived) |

---

## Architecture Patterns

### Recommended File Layout After Phase 44

```
src/do_uw/brain/
├── checks/
│   ├── biz.yaml      # 43 checks: BIZ.* prefix
│   ├── fin.yaml      # 58 checks: FIN.* prefix
│   ├── gov.yaml      # 85 checks: GOV.* prefix
│   ├── exec.yaml     # 20 checks: EXEC.* prefix
│   ├── lit.yaml      # 65 checks: LIT.* prefix
│   ├── stock.yaml    # 35 checks: STOCK.* prefix
│   ├── fwrd.yaml     # 79 checks: FWRD.* prefix
│   └── nlp.yaml      # 15 checks: NLP.* prefix
├── framework/
│   ├── risk_model.yaml       (unchanged)
│   ├── perils.yaml           (unchanged)
│   ├── causal_chains.yaml    (unchanged)
│   └── taxonomy.yaml         (unchanged)
├── SCHEMA.md                 # Human-readable spec of unified check schema
├── brain_schema.py           (update: add new columns, remove deprecated)
├── brain_loader.py           (update: map new field names to runtime contract)
├── brain_migrate.py          (update: read 8 YAML files instead of checks.json)
├── brain_writer.py           (update: brain build, brain add, brain validate cmds)
├── brain.duckdb              (rebuilt; gitignored)
└── [DEPRECATED after phase]
    ├── checks.json
    ├── patterns.json
    ├── red_flags.json
    ├── brain_migrate_config.py
    ├── brain_migrate_framework.py
    └── brain_migrate_scoring.py
```

### Unified YAML Check Schema (per entry in checks/*.yaml)

```yaml
# Minimal required fields
id: GOV.BOARD.independence          # domain prefix drives file assignment
name: Board Independence Ratio
work_type: evaluate                  # extract | evaluate | infer
layer: signal                        # hazard | signal | peril_confirming

# Risk position
factors: [F9]
peril_ids: [P_GOV_FAIL]             # empty list [] if unlinked
chain_roles:                         # {} if unlinked
  CH_GOV_001: trigger

# Acquisition
acquisition_tier: L1                 # L1 | L2 | L3 | L4
required_data: [SEC_PROXY]
data_locations:
  SEC_PROXY: [board_composition]

# Evaluation
threshold:
  type: ratio
  red: "< 0.50"
  yellow: "0.50-0.75"
  clear: "> 0.75"
execution_mode: AUTO
claims_correlation: 0.62
tier: 2

# Presentation
worksheet_section: governance
display_when: always
v6_subsection_ids: ["4.1"]
plaintiff_lenses: [SHAREHOLDERS]

# Provenance (new; empty for migrated checks)
provenance: {}

# Optional fields (include only when applicable)
depth: 2
amplifier: null
pattern_ref: null          # only for work_type: infer
unlinked: false            # true for 283 checks with no chain_roles
```

### brain build Pipeline (YAML → DuckDB)

```
1. Read brain/SCHEMA.md validation rules
2. For each domain file in checks/:
   a. Parse YAML
   b. Validate each check against Pydantic CheckModel
   c. Collect validation errors (don't fail fast — report all)
3. Cross-validate: check peril_ids exist in perils.yaml
4. Cross-validate: check chain_roles keys exist in causal_chains.yaml
5. Report unlinked checks (unlinked: true) as INFO, not ERROR
6. Wipe and rebuild brain_checks table (all versions)
7. Re-run _VIEWS_DDL and _INDEXES_DDL
8. Write brain_meta: build_timestamp, yaml_check_count, unlinked_count
9. Print summary: N checks loaded, M unlinked, K errors
```

### patterns.json → YAML Mapping

The 21 INFERENCE_PATTERN checks in checks.json have `pattern_ref` pointing to patterns.json entries. The patterns.json `brain_patterns` table holds composite scoring logic.

**Strategy:** patterns.json entries become `brain_patterns` table source, loaded separately from checks YAML. The 21 infer-type checks in checks/*.yaml already reference them via `pattern_ref`. patterns.json is kept as-is for Plan 44-04 which absorbs it into YAML (possibly `framework/patterns.yaml`).

### red_flags.json → YAML Mapping

17 entries in `escalation_triggers` array. Each has: id, name, condition, max_tier, max_quality_score, source_check, action, auto_decline, new_business_context.

These are not checks — they are score ceiling rules. They reference `source_check` (e.g., "Stanford SCAC search") rather than a check ID. Plan 44-04 absorbs these into a `framework/red_flags.yaml` file and adds a `critical_red_flag: true` marker on the linked check (where source_check matches a check ID).

---

## DuckDB Schema Changes

### brain_checks: Columns to ADD

| New Column | Type | Purpose |
|------------|------|---------|
| `work_type` | VARCHAR | extract / evaluate / infer |
| `acquisition_tier` | VARCHAR | L1 / L2 / L3 / L4 |
| `worksheet_section` | VARCHAR | Semantic section name (replaces report_section int logic) |
| `display_when` | VARCHAR | Filtering condition string |
| `chain_roles` | JSON | Dict of chain_id → role for this check |
| `unlinked` | BOOLEAN | True if chain_roles is empty |
| `provenance` | JSON | Source article/doc metadata |

These are added via `_COLUMN_MIGRATIONS` block in brain_schema.py (uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` pattern already established).

### brain_checks: Columns to KEEP (runtime contract, don't remove yet)

These columns have downstream callers in brain_loader.py and analyze/score stages. Mark deprecated in SCHEMA.md but keep in DuckDB until all callers migrated:

- `content_type` — callers in brain_loader.py, test_brain_loader.py, analyze stage
- `category` — callers in render/template logic
- `signal_type` — callers unknown but likely score stage
- `hazard_or_signal` — callers in hazard_engine tests
- `report_section` — callers in brain_loader._SECTION_MAP

**Strategy:** Populate both old and new columns during migration. Loader reads new columns if present, falls back to old. Remove old columns in a follow-on cleanup phase.

### brain_checks: Columns Already Present (no change)

`peril_id` (singular) and `chain_ids` (array) were already added via `_COLUMN_MIGRATIONS`. Phase 44 renames semantics: `peril_ids` (plural array) replaces `peril_id` (singular). Add `peril_ids VARCHAR[]` as new column; keep `peril_id` for backward compat.

---

## brain_loader.py Impact

### Current Method Contract (must not break)

```python
BrainDBLoader.load_checks()  # Returns {"checks": [...]} — 400 checks
BrainDBLoader.load_patterns()
BrainDBLoader.load_red_flags()
BrainDBLoader.load_scoring_factors()
BrainDBLoader.load_taxonomy()
BrainDBLoader.load_perils()
BrainDBLoader.load_causal_chains()
```

`load_checks()` returns dicts with the OLD field names (content_type, category, signal_type, hazard_or_signal) because ConfigLoader and downstream code reference these keys.

### Minimal Change Strategy

1. `load_checks()` reads new columns (work_type, acquisition_tier, worksheet_section, etc.) from DuckDB
2. Adds new keys to each returned check dict alongside old keys
3. Old keys populated from new columns (backward compat shim):
   - `content_type` = reverse-map from work_type
   - `category` = derived from tier + work_type
   - `hazard_or_signal` = map from layer
4. `_SECTION_MAP` extended to handle both int sections and semantic worksheet_section strings
5. `BackwardCompatLoader` class removed after all callers updated

### Methods Needing Updates
- `_get_conn()` — auto-migrate logic still needed (call brain build if empty)
- `load_checks()` — add new field projection; backward compat shim
- `load_patterns()` — if patterns.json is deprecated, read from brain_patterns table (unchanged)
- No other methods need structural changes in Plans 44-01 through 44-03

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML validation | Custom schema checker | Pydantic model with strict=True | Edge cases in type coercion, union types |
| Cross-file ID validation | Manual set comparisons | Pydantic @model_validator with shared context | Cleaner error messages, testable |
| YAML file splitting | String manipulation | Python YAML load → filter by id prefix → dump | Preserves comments, handles edge cases |
| DuckDB schema migration | DROP and recreate | ALTER TABLE ADD COLUMN IF NOT EXISTS (existing pattern) | Preserves brain_check_runs, brain_effectiveness data |

---

## Common Pitfalls

### Pitfall 1: Wiping Runtime Data During brain build
**What goes wrong:** `brain build` drops and recreates `brain_checks` but also wipes `brain_check_runs` and `brain_effectiveness` (the learning tables).
**Why it happens:** Using `DROP TABLE` instead of targeted rebuild.
**How to avoid:** Only truncate/reload `brain_checks`, `brain_patterns`, `brain_red_flags`. Never touch `brain_check_runs`, `brain_effectiveness`, `brain_feedback`, `brain_proposals`, `brain_changelog`.
**Warning signs:** Test suite loses run history after build.

### Pitfall 2: Breaking the Backward Compat Contract Too Early
**What goes wrong:** Removing `content_type` from DuckDB before all callers updated causes runtime failures in score/analyze stages.
**Why it happens:** Eager cleanup during migration.
**How to avoid:** Populate both old and new columns during 44-02/44-03. Schedule old column removal as a named subtask at end of 44-03, only after test suite passes with new field names.
**Warning signs:** `test_brain_loader.py::TestRoundTripCompatibility::test_same_check_ids` fails.

### Pitfall 3: 283 Unlinked Checks Causing build Failure
**What goes wrong:** brain build treats missing chain_roles as an error and aborts.
**Why it happens:** Overly strict validation.
**How to avoid:** Unlinked checks are INFO-level, not ERROR. The `unlinked: true` flag is set during migration; brain build counts and reports them but does not fail on them.
**Warning signs:** build exits non-zero; 283 checks never make it to DuckDB.

### Pitfall 4: YAML File Size Exceeding 500-Line Limit
**What goes wrong:** gov.yaml (85 checks) or fwrd.yaml (79 checks) exceeds 500-line project limit.
**Why it happens:** Each check is ~20-30 lines of YAML.
**How to avoid:** gov.yaml at 85 checks × ~25 lines = ~2,125 lines. This WILL exceed the limit. Plan must split by sub-prefix (GOV.BOARD.*, GOV.AUDIT.*, etc.) into subdirectory: `checks/gov/board.yaml`, `checks/gov/audit.yaml`, etc. Same for fwrd.yaml (79 checks × ~25 lines = ~2,000 lines).
**Warning signs:** ruff pre-commit hook on YAML files? No — but CLAUDE.md anti-context-rot rule applies. Plan explicitly for subdirectory structure.

### Pitfall 5: brain add CLI Provenance Not Enforced
**What goes wrong:** `brain add` creates YAML entries without provenance metadata, defeating the live learning audit trail.
**Why it happens:** Provenance fields are optional in the schema.
**How to avoid:** `brain add` CLI must require `--source` (URL or citation) and `--date` flags. Validation rejects any new check written by `brain add` that lacks provenance.
**Warning signs:** Checks with `provenance: {}` accumulate from add CLI; no audit trail.

### Pitfall 6: 500-Line Limit on brain_migrate.py
**What goes wrong:** The migration script that reads 8 YAML files and writes DuckDB grows past 500 lines.
**Why it happens:** Each domain has its own transformation logic.
**How to avoid:** Split into `brain_migrate_yaml.py` (YAML parsing + validation) and keep `brain_migrate.py` as orchestrator. Existing `brain_migrate_config.py`, `brain_migrate_framework.py`, `brain_migrate_scoring.py` pattern shows this split already exists — follow it.

---

## Code Examples

### Existing Column Migration Pattern (from brain_schema.py)
```python
# Source: src/do_uw/brain/brain_schema.py lines 491-494
_COLUMN_MIGRATIONS = """
ALTER TABLE brain_checks ADD COLUMN IF NOT EXISTS peril_id VARCHAR;
ALTER TABLE brain_checks ADD COLUMN IF NOT EXISTS chain_ids VARCHAR[];
"""
```
Use this exact pattern for new columns (work_type, acquisition_tier, worksheet_section, display_when, chain_roles JSON, unlinked BOOLEAN, provenance JSON).

### Existing Lazy Migration Pattern (from brain_loader.py lines 60-80)
```python
def _get_conn(self) -> duckdb.DuckDBPyConnection:
    """Lazy-connect to brain.duckdb, auto-migrating if needed."""
    if self._conn is not None:
        return self._conn
    db_path = Path(self._db_path)
    needs_migration = not db_path.exists()
    self._conn = connect_brain_db(self._db_path)
    if not needs_migration:
        try:
            count = self._conn.execute("SELECT COUNT(*) FROM brain_checks").fetchone()[0]
            if count == 0:
                needs_migration = True
        except duckdb.CatalogException:
            needs_migration = True
    if needs_migration:
        # ... calls migrate pipeline
```
brain build replaces the auto-migrate trigger. After 44-03, `needs_migration` should also check for `work_type` column presence (schema version check).

### content_type → work_type mapping (for migration script)
```python
CONTENT_TYPE_TO_WORK_TYPE = {
    "MANAGEMENT_DISPLAY": "extract",
    "EVALUATIVE_CHECK": "evaluate",
    "INFERENCE_PATTERN": "infer",
}

HAZARD_OR_SIGNAL_TO_LAYER = {
    "HAZARD": "hazard",
    "SIGNAL": "signal",
    "PERIL_CONFIRMING": "peril_confirming",
}
```

### Backward Compat Shim (brain_loader.py)
```python
# Populate old field names from new for downstream compatibility
WORK_TYPE_TO_CONTENT_TYPE = {v: k for k, v in CONTENT_TYPE_TO_WORK_TYPE.items()}

def _add_compat_fields(check: dict) -> dict:
    """Add old field names derived from new canonical fields."""
    if "work_type" in check and "content_type" not in check:
        check["content_type"] = WORK_TYPE_TO_CONTENT_TYPE.get(check["work_type"], "EVALUATIVE_CHECK")
    if "layer" in check and "hazard_or_signal" not in check:
        check["hazard_or_signal"] = check["layer"].upper()
    return check
```

---

## Migration Risk and Rollback Strategy

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| YAML files exceed 500-line limit | CERTAIN (gov.yaml ~2100 lines) | HIGH | Use subdirectory structure: checks/gov/board.yaml etc |
| Backward compat break in score/analyze | MEDIUM | HIGH | Populate both old+new columns; run full test suite before removing old |
| brain build wipes learning tables | LOW (if plan is careful) | HIGH | Explicit table whitelist: only truncate brain_checks |
| 283 unlinked checks blocking build | MEDIUM | MEDIUM | Build validates but never fails on unlinked |
| Migration produces wrong check count | LOW | HIGH | test_brain_migrate.py must assert exactly 400 checks loaded |

### Rollback Strategy

Because DuckDB is a cache (not source of truth after Phase 44), rollback is trivial:
1. If YAML migration fails: `brain build` re-reads old checks.json (keep it as fallback until 44-04)
2. If DuckDB is corrupted: delete brain.duckdb, run `brain build` — rebuilt from YAML in seconds
3. If runtime breaks after loader changes: git revert the loader commit; DuckDB still has old columns

The key safety property: until checks.json is physically deleted (44-04), the old migration path remains available as a regression baseline.

---

## Existing Test Impact

### Tests That Need Updating

| Test File | Why It Needs Updating | Scope of Change |
|-----------|----------------------|-----------------|
| `tests/brain/test_brain_loader.py` | Asserts `content_type` field present; uses `migrate_checks_to_brain` which reads checks.json | Add assertions for new fields; keep old field assertions via compat shim |
| `tests/brain/test_brain_migrate.py` | Tests migration from checks.json; after 44-02/44-03, source is YAML files | New fixture: migrate from YAML; old test kept as regression until 44-04 |
| `tests/brain/test_brain_schema.py` | Schema assertions; new columns need tests | Add column existence tests for new fields |
| `tests/brain/test_brain_writer.py` | Tests brain CLI commands; brain build is new subcommand | Add test for `brain build` success + check count |
| `tests/test_check_classification.py` | References `content_type` field values | Update to use `work_type` or assert compat shim populates content_type |
| `tests/brain/test_brain_framework.py` | Tests causal chain loading; chain_roles population should be tested | Add test: checks with IDs in causal_chains.yaml have non-empty chain_roles |

### Tests That Should NOT Break (runtime behavior unchanged)

- `test_score_stage.py`, `test_analyze_stage.py`, `test_render_*.py` — these consume check data via brain_loader; as long as backward compat shim is in place, no changes needed
- `test_hazard_engine.py` — reads `hazard_or_signal` field; shim populates this from `layer`
- `test_pattern_detection.py` — reads patterns from brain_patterns table; table structure unchanged

### New Tests Required (Wave 0 Gaps)

| Test File | Covers |
|-----------|--------|
| `tests/brain/test_brain_yaml_loader.py` | YAML file parsing: 8 files load, all 400 checks present, no duplicates |
| `tests/brain/test_brain_build_pipeline.py` | brain build: YAML → DuckDB, count=400, work_type values valid, unlinked_count=283 |
| `tests/brain/test_check_field_mapping.py` | Every check has work_type, layer, acquisition_tier; backward compat fields populated |
| `tests/brain/test_brain_add_cli.py` | brain add: provenance required, YAML written to correct domain file, brain build picks it up |

---

## File Size Risk (CLAUDE.md Anti-Context-Rot Rule)

**500-line limit applies to all Python AND YAML files.**

| Domain File | Check Count | Est. Lines @ 25/check | Over Limit? |
|-------------|-------------|----------------------|-------------|
| biz.yaml | 43 | ~1,075 | YES — split by sub-prefix |
| fin.yaml | 58 | ~1,450 | YES — split by sub-prefix |
| gov.yaml | 85 | ~2,125 | YES — split by sub-prefix |
| exec.yaml | 20 | ~500 | AT LIMIT — monitor |
| lit.yaml | 65 | ~1,625 | YES — split by sub-prefix |
| stock.yaml | 35 | ~875 | YES — split by sub-prefix |
| fwrd.yaml | 79 | ~1,975 | YES — split by sub-prefix |
| nlp.yaml | 15 | ~375 | OK |

**All 7 larger domain files need subdirectory structure:**
```
checks/
├── biz/        # biz_class.yaml, biz_growth.yaml, etc.
├── fin/        # fin_income.yaml, fin_balance.yaml, etc.
├── gov/        # gov_board.yaml, gov_audit.yaml, gov_exec_comp.yaml, etc.
├── exec/       # exec_tenure.yaml (single file OK)
├── lit/        # lit_sca.yaml, lit_sec.yaml, lit_private.yaml, etc.
├── stock/      # stock_price.yaml, stock_short.yaml, etc.
├── fwrd/       # fwrd_guidance.yaml, fwrd_ipo.yaml, etc.
└── nlp/        # nlp_signals.yaml (single file OK)
```

The `brain build` pipeline reads `checks/**/*.yaml` (glob) so subdirectory structure is transparent.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already in use) |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/brain/ -x -q` |
| Full suite command | `uv run pytest tests/brain/ -v` |
| Estimated runtime | ~5-10 seconds (brain tests use in-memory DuckDB) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| ARCH-09 | 400 checks load from 8 YAML domain files | unit | `uv run pytest tests/brain/test_brain_yaml_loader.py -x` |
| ARCH-09 | brain build writes all checks to DuckDB | integration | `uv run pytest tests/brain/test_brain_build_pipeline.py -x` |
| ARCH-09 | work_type, layer, acquisition_tier present on all checks | unit | `uv run pytest tests/brain/test_check_field_mapping.py -x` |
| ARCH-09 | 117 checks have non-empty chain_roles; 283 have unlinked=True | unit | `uv run pytest tests/brain/test_brain_build_pipeline.py::test_chain_roles_count -x` |
| ARCH-09 | Backward compat: content_type populated via shim | unit | `uv run pytest tests/brain/test_brain_loader.py -x` |
| ARCH-09 | brain add writes valid YAML with provenance | integration | `uv run pytest tests/brain/test_brain_add_cli.py -x` |
| ARCH-09 | Full round-trip: YAML → DuckDB → loader returns same check IDs | integration | `uv run pytest tests/brain/test_brain_migrate.py -x` |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/brain/ -x -q`
- **Full suite trigger:** Before merging final task of any wave
- **Phase-complete gate:** Full suite green before /gsd:verify-work runs
- **Estimated feedback latency per task:** ~5-10 seconds

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/brain/test_brain_yaml_loader.py` — YAML file parsing tests
- [ ] `tests/brain/test_brain_build_pipeline.py` — brain build pipeline tests
- [ ] `tests/brain/test_check_field_mapping.py` — field presence + values tests
- [ ] `tests/brain/test_brain_add_cli.py` — brain add CLI tests

---

## Open Questions

1. **YAML format: ruamel.yaml vs PyYAML**
   - What we know: Framework YAML files (causal_chains.yaml, perils.yaml) are already in use. Unknown which library reads them.
   - What's unclear: Does the project use PyYAML or ruamel.yaml? ruamel.yaml preserves comments; PyYAML does not. brain add CLI needs comment preservation to maintain human-readable provenance.
   - Recommendation: Check pyproject.toml for the dependency. If PyYAML, add ruamel.yaml for brain add only (writes YAML). If ruamel.yaml is already present, use it throughout.

2. **brain build as CLI vs auto-trigger**
   - What we know: Current loader auto-migrates on first use (lazy migration in _get_conn).
   - What's unclear: Should brain build be explicit-only (`uv run brain build`) or should the loader auto-trigger it if YAML is newer than DuckDB mtime?
   - Recommendation: Explicit-only for Phase 44. Auto-trigger (mtime check) is a follow-on enhancement. Clearer mental model for users.

3. **section int → worksheet_section string mapping**
   - What we know: checks.json has `section: 1-7` (int). The new model uses `worksheet_section` (semantic string). `v6_subsection_ids` like "1.1", "4.2" encode both.
   - What's unclear: Is there a complete mapping table from section int + subsection to semantic string? The `_SECTION_MAP` in brain_loader.py is partial.
   - Recommendation: Plan 44-01 (schema design) must define the complete mapping before migration scripts are written.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)
- `src/do_uw/brain/brain_schema.py` — complete DuckDB schema: 19 tables, 11 views, all column names
- `src/do_uw/brain/checks.json` — 400 checks, 24 fields per check, exact field names and distributions
- `src/do_uw/brain/brain_loader.py` — runtime contract, backward compat shim locations
- `src/do_uw/brain/patterns.json` — 21 patterns, structure, allegation_types
- `src/do_uw/brain/red_flags.json` — 17 escalation triggers, field structure
- `.planning/phases/44-.../continue-here.md` — locked architectural decisions
- `tests/brain/test_brain_loader.py` — existing test contract that must not break

### Secondary (HIGH confidence — design documents)
- `.planning/ROADMAP.md Phase 44 entry` — full architecture spec including 3-axis model, deprecation targets, 5 planned plans

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tooling already present, no new dependencies
- Architecture: HIGH — fully specified in ROADMAP.md and .continue-here.md; no decisions open
- Field mapping: HIGH — derived from direct inspection of checks.json (400 checks, all 24 fields counted)
- DuckDB delta: HIGH — existing migration pattern well-established; column additions are additive
- File size risk: HIGH — 500-line limit will be violated by 7 of 8 domain files; subdirectory structure required
- Pitfalls: HIGH — all derived from current codebase structure

**Research date:** 2026-02-24
**Valid until:** This is internal architecture research; valid until the codebase changes significantly (no expiry concern)
