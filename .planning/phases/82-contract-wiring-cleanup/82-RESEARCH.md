# Phase 82: Signal Schema v3 - Research

**Researched:** 2026-03-07
**Domain:** Brain signal YAML schema evolution, Pydantic model extension, YAML migration tooling
**Confidence:** HIGH

## Summary

Phase 82 extends the brain signal schema from v2 to v3 by adding four new fields (`group`, `depends_on`, `field_path`, `signal_class`) to every signal, removing two old fields (`type`, `facet`), expanding the `provenance` block with audit trail metadata, and updating all consumers. The codebase is well-structured for this: `BrainSignalEntry` already uses `extra: "allow"`, the V2 migration (Phase 54) established the additive-field pattern, and `ruamel.yaml` is already a dependency with round-trip editing patterns in `knowledge/yaml_writer.py`.

The 476 signals are spread across 9 subdirectories under `src/do_uw/brain/signals/`. Current state: 26 foundational signals (type=foundational), 450 evaluative signals (type absent/defaulting), 10 unique facet values, 337 signals with `data_strategy.field_key`. The section YAML files (12 files under `brain/sections/`) contain 100+ group definitions that map to the new `group` field values. The output manifest (`output_manifest.yaml`, 1225 lines) contains the authoritative facet-to-group structure.

**Primary recommendation:** Execute as a three-wave migration: (1) extend schema + BrainLoader with backward-compatible defaults, (2) run migration script to populate v3 fields on all 476 signals using section YAML + field_registry as source data, (3) update all consumers from old fields to new fields and remove old fields. Commit before and after each wave.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Two-level grouping**: `group` is fine-grained (matches manifest group objects, e.g. `distress_indicators`, `key_metrics`). `facet` (coarse section-level) is being REMOVED -- replaced by section association derivable from manifest group membership
- **`field_path` hybrid resolution**: Can be either a direct dotted path (`extracted.financials.liquidity`) OR a registry key (`current_ratio`). Resolver tries direct path first, falls back to field_registry.yaml
- **`signal_class` three-tier**: `foundational | evaluative | inference`. Maps execution order, not rendering intent
- **`depends_on` with signal + field**: Each dependency declares both signal ID and specific field: `[{signal: BASE.XBRL.balance_sheet, field: total_assets}]`
- **`group` auto-populated** from existing `facet` field + section YAML mapping
- **`depends_on` auto-populated** for evaluative signals by tracing `data_strategy.field_key` through field_registry.yaml
- **`signal_class` inferred** from existing `type` field and ID patterns (COMP.*/FORENSIC.* -> inference)
- **In-place YAML modification with git safety**: ruamel.yaml preserving comments/formatting
- **Clean break on `type` and `facet`**: Remove old fields, replace with `signal_class` and `group`. All consumers updated
- **V3 fields have backward-compatible defaults**: `group: ''`, `depends_on: []`, `field_path: ''`, `signal_class: 'evaluative'`
- **BrainLoader warns on missing v3 fields**, enforcement deferred to Phase 84
- **CI contract test validates**: group exists in manifest, depends_on IDs exist, field_path resolves
- **Expanded `provenance` block**: formula, threshold_provenance, render_target, data_source
- **Threshold provenance requires source + rationale**
- **Auto-categorize unknown thresholds**: calibrated / standard / unattributed
- **`brain audit` produces HTML report**: institutional-quality, filterable, searchable

### Claude's Discretion
- `field_path` population strategy (registry key vs resolved direct path) -- pick approach that minimizes risk
- V3 field default computation logic (whether to auto-infer signal_class from type during loading)
- Exact ruamel.yaml formatting/comment preservation approach
- HTML audit report template design

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCHEMA-01 | Every signal declares `group` membership inline | Section YAML has 100 group definitions across 12 files; `facet` field on 450 signals provides coarse mapping; section YAML facets provide fine-grained group IDs |
| SCHEMA-02 | Every signal declares `depends_on` listing prerequisite signal IDs | `data_strategy.field_key` on 337 signals traces through `field_registry.yaml` (100+ entries) to identify source signals; foundational signals have empty depends_on |
| SCHEMA-03 | Every signal declares `field_path` for data resolution | `field_registry.yaml` maps logical names to dotted paths; `data_strategy.field_key` already references registry keys; hybrid approach minimizes risk |
| SCHEMA-04 | Every signal declares `signal_class` (foundational/evaluative/inference) | 26 signals have type=foundational; remaining 450 default to evaluative; work_type=infer (21 signals) and FIN.FORENSIC.* patterns (38 signals) candidates for inference |
| SCHEMA-05 | BrainLoader handles both v2 and v3 schemas with backward-compatible defaults | `brain_unified_loader.py` loads YAML, validates via `BrainSignalEntry` (extra=allow); V2 migration pattern established precedent |
| SCHEMA-06 | Migration tooling populates v3 fields on all 476 signals | `brain_migrate_yaml.py` (469 lines) + `yaml_writer.py` (ruamel.yaml round-trip) provide patterns; section YAML + field_registry are source data |
| SCHEMA-07 | CI contract test enforces v3 fields on ACTIVE signals | `test_brain_contract.py` exists (178 lines, 7 test classes); extend with v3 field validation |
| SCHEMA-08 | Every signal carries complete audit trail metadata | `BrainSignalProvenance` model exists (7 fields); expand with formula, threshold_provenance, render_target, data_source |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruamel.yaml | >=0.19.1 | Round-trip YAML editing preserving comments | Already in pyproject.toml; used by yaml_writer.py |
| PyYAML | (bundled) | Fast read-only YAML loading | Used by BrainLoader for signal loading |
| pydantic | v2 | Schema validation for BrainSignalEntry | Project standard; extra="allow" enables forward compat |
| Jinja2 | (bundled) | HTML audit report template rendering | Already used for all worksheet templates |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (bundled) | CI contract tests | test_brain_contract.py extension |
| pathlib | stdlib | File path handling | All YAML file operations |

### Alternatives Considered
None -- all libraries already in use. No new dependencies needed.

## Architecture Patterns

### Current Signal YAML Structure (v2)
```yaml
- id: FIN.ACCT.auditor
  name: Auditor
  work_type: evaluate          # stays
  type: foundational           # REMOVED -> signal_class
  facet: financial_health      # REMOVED -> group
  layer: signal                # stays
  tier: 2                      # stays
  depth: 3                     # stays
  threshold: {...}             # stays
  data_strategy:
    field_key: xbrl_auditor_opinion    # -> field_path (hybrid)
  provenance:
    origin: migrated_from_json
    confidence: inherited
  display: {...}               # stays
```

### Target Signal YAML Structure (v3)
```yaml
- id: FIN.ACCT.auditor
  name: Auditor
  work_type: evaluate
  signal_class: evaluative     # NEW (replaces type)
  group: earnings_quality      # NEW (replaces facet, fine-grained)
  depends_on:                  # NEW
    - signal: BASE.XBRL.income_statement
      field: operating_income
  field_path: xbrl_auditor_opinion   # NEW (registry key or dotted path)
  layer: signal
  tier: 2
  depth: 3
  threshold: {...}
  data_strategy:
    field_key: xbrl_auditor_opinion
  provenance:
    origin: migrated_from_json
    confidence: inherited
    formula: "threshold comparison on auditor opinion text"  # NEW
    threshold_provenance:            # NEW
      source: standard
      rationale: "Standard auditor opinion categories"
    render_target: "financial_health/earnings_quality"  # NEW
    data_source: SEC_10K             # NEW
  display: {...}
```

### Consumer Update Map (Critical Path)

Files that reference `type` field (must change to `signal_class`):
| File | Line | Current | New |
|------|------|---------|-----|
| `brain_signal_schema.py:303` | `type: Literal["evaluate", "foundational"]` | Remove field, add `signal_class` |
| `stages/analyze/signal_engine.py:96` | `sig.get("type") == "foundational"` | `sig.get("signal_class") == "foundational"` |
| `stages/analyze/signal_disposition.py:152` | `signal_type == "foundational"` | Same check on signal_class |
| `brain/chain_validator.py:176,334,338` | `signal.type == "foundational"` | `signal.signal_class == "foundational"` |
| `tests/brain/test_brain_contract.py` (6 refs) | `sig.get("type") == "foundational"` | `sig.get("signal_class") == "foundational"` |
| `tests/brain/test_foundational_coverage.py:47` | `signal.get("type") == "foundational"` | Same |
| `tests/knowledge/test_enriched_roundtrip.py:195` | `s.get("type") != "foundational"` | Same |

Files that reference `facet` field (must change to `group`):
| File | Line | Current | New |
|------|------|---------|-----|
| `brain_signal_schema.py:287` | `facet: str` | Remove field, add `group` |
| `cli_brain_trace.py:255,258,323,326,458` | `signal_def.get("facet")` | `signal_def.get("group")` |
| `brain/brain_health.py:112-126` | Section YAML facet coverage | Recompute from group field |
| `brain/brain_audit.py:347-379` | Orphaned signal check via sections | Recompute from group |
| `tests/brain/test_brain_contract.py:107` | `sig.get("facet")` | `sig.get("group")` |
| `tests/test_signal_forensic_wiring.py:329` | `"facet" in s` | `"group" in s` |
| `tests/brain/test_chain_validator.py:74` | `"facet": facet` | `"group": group` |

### Migration Data Flow
```
Section YAML (12 files)     field_registry.yaml (100+ entries)
       |                            |
       v                            v
  group assignment           field_path + depends_on
       |                            |
       +--------+-------------------+
                |
                v
    brain_migrate_v3.py (new script)
                |
                v
    476 YAML files modified in-place (ruamel.yaml)
```

### Group Assignment Strategy

The `group` field must be fine-grained, matching manifest group IDs. Current mapping path:

1. Signal has `facet` (coarse, 10 values: `financial_health`, `governance`, etc.)
2. Section YAMLs define fine-grained groups within each section (100 total groups)
3. Section YAMLs list which signal IDs belong to each group (135 signals explicitly mapped)
4. For the remaining ~341 signals not explicitly in section YAML groups: use facet + signal ID prefix to infer group

The 12 section YAML files contain these group counts:
- `financial_health`: 15 groups (annual_comparison, key_metrics, distress_indicators, etc.)
- `scoring`: 18 groups (tier_classification, peril_assessment, ten_factor_scoring, etc.)
- `litigation`: 12 groups (active_matters, sec_enforcement, settlement_history, etc.)
- `market_activity`: 11 groups (stock_performance, stock_drops, short_interest, etc.)
- `governance`: 10 groups (people_risk, board_composition, ownership_structure, etc.)
- `business_profile`: 9 groups
- `executive_summary`: 7 groups
- `ai_risk`: 5 groups
- `forward_looking`: 5 groups
- `executive_risk`: 4 groups
- `filing_analysis`: 3 groups
- `red_flags`: 1 group

Only 135 of 476 signals are explicitly listed in section YAML groups. The migration script must handle the remaining 341 signals by inferring group from:
1. Signal ID prefix pattern (e.g., `FIN.PROFIT.*` -> `key_metrics` or `annual_comparison`)
2. Signal `facet` field (coarse mapping to section, then infer best group within section)
3. Flagging truly ambiguous assignments for manual review

### `depends_on` Population Strategy

For evaluative signals with `data_strategy.field_key`:
1. Look up `field_key` in `field_registry.yaml`
2. The registry entry's `path` (e.g., `extracted.financials.liquidity`) maps to a foundational signal's acquisition output
3. Find the foundational signal whose `acquisition.sources[].fields[]` includes that path
4. Record as `{signal: BASE.XBRL.balance_sheet, field: current_ratio}`

For the 139 signals WITHOUT `data_strategy.field_key`: leave `depends_on: []` initially. These are mostly display/extract signals or signals using `data_locations` directly.

For inference signals (FIN.FORENSIC.*, work_type=infer): manual population needed since they depend on other evaluative signals.

### `field_path` Population (Claude's Discretion)

**Recommendation: Use registry keys for all signals that have `data_strategy.field_key`.** This minimizes risk -- 337 signals already reference these keys, and the resolver falls back to field_registry.yaml. Direct dotted paths can be gradually introduced later.

For the 139 signals without `field_key`: set `field_path: ''` (empty default). These signals use `data_locations` or narrative keys that don't map cleanly to a single path.

### `signal_class` Inference Rules

| Current State | New `signal_class` | Count | Rule |
|---|---|---|---|
| `type: foundational` | `foundational` | 26 | Direct mapping |
| `work_type: infer` | `inference` | 21 | Infer work_type maps to inference class |
| `FIN.FORENSIC.*` composites | `inference` | ~17 additional | ID pattern: composite forensic scores |
| Everything else | `evaluative` | ~412 | Default |

Note: The exact boundary between `evaluative` and `inference` for FIN.FORENSIC signals needs careful determination. Some FIN.FORENSIC signals are simple evaluative checks (e.g., `FIN.FORENSIC.accrual_intensity` just checks a ratio), while composites like `FIN.FORENSIC.fis_composite` aggregate multiple inputs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML round-trip editing | Custom string manipulation | ruamel.yaml `YAML(typ='rt')` | Comment preservation, formatting stability, proven in yaml_writer.py |
| Signal ID to YAML path index | Manual path scanning | `build_signal_yaml_index()` from yaml_writer.py | Already built, tested, handles both list and dict YAML formats |
| Schema validation | Manual field checks | Pydantic `BrainSignalEntry.model_validate()` | Already validates all signals on load; just add v3 fields |
| Group-to-manifest validation | Custom manifest parser | `load_manifest()` + `ManifestFacet.id` | manifest_schema.py already loads and validates manifest structure |

## Common Pitfalls

### Pitfall 1: YAML Comment Destruction
**What goes wrong:** Using PyYAML (`yaml.dump`) instead of ruamel.yaml destroys all comments in signal YAML files. The signal files have header comments (`# Generated by brain_migrate_yaml.py`) and inline documentation.
**Why it happens:** PyYAML's dumper strips comments by design.
**How to avoid:** Use `ruamel.yaml` with `YAML(typ='rt')` for ALL write operations. Pattern exists in `knowledge/yaml_writer.py:101`.
**Warning signs:** Diff shows removed comment lines after migration.

### Pitfall 2: Group Assignment Ambiguity (341 Unmapped Signals)
**What goes wrong:** Only 135 of 476 signals are explicitly listed in section YAML groups. Naive mapping leaves 341 signals with empty/wrong groups.
**Why it happens:** Section YAMLs list only "key" signals per group, not every signal that belongs there.
**How to avoid:** Build a multi-tier assignment strategy: (1) explicit section YAML mapping, (2) signal ID prefix heuristic, (3) facet field as section-level fallback. Flag ambiguous cases for manual review.
**Warning signs:** `brain audit` showing signals with empty `group` field.

### Pitfall 3: Circular depends_on (Inference Signals)
**What goes wrong:** Inference signals like FIN.FORENSIC.fis_composite may reference evaluative signals that in turn reference foundational signals. Getting the DAG wrong creates cycles.
**Why it happens:** Manual dependency population without validation.
**How to avoid:** The CI contract test MUST validate: every `depends_on` signal ID exists, no circular references (Phase 83 adds full DAG validation, but basic cycle detection should be in Phase 82 contract test).
**Warning signs:** `test_brain_contract.py` passing but `brain audit` showing broken depends_on references.

### Pitfall 4: Breaking Pipeline Output During Migration
**What goes wrong:** Renaming `type` to `signal_class` breaks signal_engine.py's foundational skip logic, causing 26 foundational signals to be evaluated (and fail).
**Why it happens:** Consumer updates happen in wrong order relative to YAML field changes.
**How to avoid:** Three-wave approach: (1) add new fields with defaults, keeping old fields, (2) update all consumers to read new fields, (3) remove old fields from YAML. Run full pipeline between waves.
**Warning signs:** Signal engine evaluating BASE.* signals; pipeline errors on foundational signals.

### Pitfall 5: Provenance Block Extra Fields Rejected
**What goes wrong:** `BrainSignalProvenance` model has `extra="allow"`, but if new provenance sub-fields use nested models with `extra="forbid"`, validation fails.
**Why it happens:** Inconsistent extra field policies across Pydantic models.
**How to avoid:** Use plain dict or `extra="allow"` for new provenance sub-models like `threshold_provenance`.
**Warning signs:** ValidationError on load after migration.

### Pitfall 6: Test Explosion from facet->group Rename
**What goes wrong:** Contract tests and forensic wiring tests hard-reference `facet` field. Changing YAML without updating tests causes mass test failures.
**Why it happens:** Tests check field names, not just field presence.
**How to avoid:** Update test assertions in the same commit/wave as the consumer code changes. The test files are: `test_brain_contract.py`, `test_signal_forensic_wiring.py`, `test_chain_validator.py`, `test_foundational_coverage.py`, `test_enriched_roundtrip.py`.

## Code Examples

### Pattern 1: Extending BrainSignalEntry with V3 Fields
```python
# Source: brain_signal_schema.py -- follows V2 additive pattern
class SignalDependency(BaseModel):
    """A single dependency declaration."""
    model_config = ConfigDict(extra="forbid")
    signal: str = Field(..., description="Prerequisite signal ID")
    field: str = Field(default="", description="Specific field needed from that signal")

class BrainSignalEntry(BaseModel):
    # ... existing fields ...

    # V3 fields (Phase 82) -- backward-compatible defaults
    group: str = Field(
        default="",
        description="Fine-grained group ID matching manifest group objects",
    )
    depends_on: list[SignalDependency] = Field(
        default_factory=list,
        description="Prerequisite signals this signal needs",
    )
    field_path: str = Field(
        default="",
        description="Data resolution path (registry key or dotted path)",
    )
    signal_class: Literal["foundational", "evaluative", "inference"] = Field(
        default="evaluative",
        description="Execution tier: foundational -> evaluative -> inference",
    )
```

### Pattern 2: ruamel.yaml Round-Trip Editing
```python
# Source: knowledge/yaml_writer.py pattern
from ruamel.yaml import YAML

def modify_signal_fields(yaml_path: Path, signal_id: str, updates: dict) -> None:
    rtyaml = YAML(typ='rt')
    rtyaml.preserve_quotes = True
    rtyaml.width = 120

    data = rtyaml.load(yaml_path.read_text(encoding='utf-8'))

    for entry in data:
        if isinstance(entry, dict) and entry.get('id') == signal_id:
            for key, value in updates.items():
                entry[key] = value
            break

    with open(yaml_path, 'w', encoding='utf-8') as f:
        rtyaml.dump(data, f)
```

### Pattern 3: Migration Script Group Assignment
```python
# Build group lookup from section YAML
def build_group_lookup(sections_dir: Path) -> dict[str, str]:
    """Map signal_id -> fine-grained group_id from section YAML facets."""
    import yaml
    lookup: dict[str, str] = {}
    for yaml_path in sorted(sections_dir.glob("*.yaml")):
        section = yaml.safe_load(yaml_path.read_text())
        for facet in section.get("facets", []):
            group_id = facet["id"]  # e.g., "distress_indicators"
            for sig_id in facet.get("signals", []):
                lookup[sig_id] = group_id
    return lookup
```

### Pattern 4: Consumer Update (signal_engine.py)
```python
# Before (v2):
if sig.get("type") == "foundational":
    continue

# After (v3):
if sig.get("signal_class") == "foundational":
    continue
```

### Pattern 5: Provenance Block Expansion
```python
class ThresholdProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: str = Field(default="unattributed", description="calibrated|standard|unattributed")
    rationale: str = Field(default="", description="Why this threshold value")

class BrainSignalProvenance(BaseModel):
    model_config = {"extra": "allow"}
    # Existing fields
    origin: str
    confidence: str | None = None
    last_validated: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    source_author: str | None = None
    added_by: str | None = None
    # V3 audit trail fields
    formula: str = Field(default="", description="Evaluation logic description")
    threshold_provenance: ThresholdProvenance | None = Field(default=None)
    render_target: str = Field(default="", description="Output location (section/group)")
    data_source: str = Field(default="", description="Primary data source type")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `type: evaluate/foundational` | `signal_class: foundational/evaluative/inference` | Phase 82 (v3) | Three-tier execution ordering |
| `facet: financial_health` (coarse) | `group: distress_indicators` (fine-grained) | Phase 82 (v3) | Signals self-select into manifest groups |
| Field registry lookup only | `field_path` on signal (hybrid) | Phase 82 (v3) | Inline data resolution, registry fallback |
| No dependency declaration | `depends_on` with signal+field | Phase 82 (v3) | Enables DAG execution in Phase 83 |
| Minimal provenance | Full audit trail in provenance | Phase 82 (v3) | Threshold attribution, formula, render target |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (pytest section) |
| Quick run command | `uv run pytest tests/brain/test_brain_contract.py -x` |
| Full suite command | `uv run pytest tests/brain/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCHEMA-01 | Every signal has non-empty `group` | unit | `uv run pytest tests/brain/test_brain_contract.py::TestSignalGroupAssignment -x` | Wave 0 |
| SCHEMA-02 | Every signal has `depends_on` (foundational: empty, others: populated or empty) | unit | `uv run pytest tests/brain/test_brain_contract.py::TestSignalDependencies -x` | Wave 0 |
| SCHEMA-03 | Every signal has `field_path` | unit | `uv run pytest tests/brain/test_brain_contract.py::TestSignalFieldPath -x` | Wave 0 |
| SCHEMA-04 | Every signal has valid `signal_class` | unit | `uv run pytest tests/brain/test_brain_contract.py::TestSignalClass -x` | Wave 0 |
| SCHEMA-05 | BrainLoader loads both v2 and v3 YAML | unit | `uv run pytest tests/brain/test_brain_loader.py -x` | Extend existing |
| SCHEMA-06 | Migration populates all 476 signals | integration | `uv run python src/do_uw/brain/brain_migrate_v3.py --dry-run` | Wave 0 |
| SCHEMA-07 | CI contract test fails on missing v3 fields | unit | `uv run pytest tests/brain/test_brain_contract.py -x` | Extend existing |
| SCHEMA-08 | Every signal has audit trail metadata | unit | `uv run pytest tests/brain/test_brain_contract.py::TestSignalAuditTrail -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/test_brain_contract.py -x`
- **Per wave merge:** `uv run pytest tests/brain/ -x && uv run pytest tests/test_signal_forensic_wiring.py -x`
- **Phase gate:** Full pipeline run on known ticker (e.g., `underwrite RPM --fresh`) + output comparison

### Wave 0 Gaps
- [ ] `tests/brain/test_brain_contract.py::TestSignalGroupAssignment` -- new test class for SCHEMA-01
- [ ] `tests/brain/test_brain_contract.py::TestSignalDependencies` -- new test class for SCHEMA-02
- [ ] `tests/brain/test_brain_contract.py::TestSignalFieldPath` -- new test class for SCHEMA-03
- [ ] `tests/brain/test_brain_contract.py::TestSignalClass` -- new test class for SCHEMA-04
- [ ] `tests/brain/test_brain_contract.py::TestSignalAuditTrail` -- new test class for SCHEMA-08
- [ ] `src/do_uw/brain/brain_migrate_v3.py` -- new migration script for SCHEMA-06

## Open Questions

1. **Inference signal boundary**
   - What we know: 21 signals have work_type=infer, 38 FIN.FORENSIC.* signals exist
   - What's unclear: Which FIN.FORENSIC signals are truly inference (compositing multiple evaluative results) vs simple evaluative checks on a single XBRL field
   - Recommendation: Default all FIN.FORENSIC.* to evaluative, manually promote composites (fis_composite, beneish_dechow_convergence, etc.) to inference. ~5-8 signals maximum.

2. **Group assignment for 341 unmapped signals**
   - What we know: 135 signals explicitly listed in section YAML groups; remaining 341 have facet but no fine-grained group
   - What's unclear: Best heuristic for prefix-to-group mapping
   - Recommendation: Build prefix map (e.g., FIN.PROFIT.* -> annual_comparison, FIN.LIQ.* -> key_metrics), validate against section YAML structure, flag remaining for manual review. Migration script should log all inferred assignments.

3. **HTML audit report scope**
   - What we know: User wants "institutional-quality, filterable, searchable" HTML
   - What's unclear: Whether this is a static HTML file or an interactive single-page app
   - Recommendation: Static HTML with Jinja2 template, CSS filters (checkbox toggles per section/class), browser search. No JavaScript framework. Matches existing worksheet output pattern.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/brain_signal_schema.py` -- current BrainSignalEntry with 326 lines, all field definitions
- `src/do_uw/brain/brain_unified_loader.py` -- BrainLoader implementation (431 lines)
- `src/do_uw/brain/signals/` -- 476 signals across 9 subdirectories
- `src/do_uw/brain/sections/` -- 12 section YAML files with 100 group definitions
- `src/do_uw/brain/output_manifest.yaml` -- 1225-line authoritative output structure
- `src/do_uw/brain/field_registry.yaml` -- 100+ field definitions
- `tests/brain/test_brain_contract.py` -- existing CI contract test (178 lines)
- `src/do_uw/brain/brain_audit.py` -- existing audit (492 lines)
- `src/do_uw/brain/brain_migrate_yaml.py` -- existing migration pattern (469 lines)
- `src/do_uw/knowledge/yaml_writer.py` -- ruamel.yaml round-trip pattern
- `src/do_uw/stages/analyze/signal_engine.py` -- primary consumer of type field

### Secondary (MEDIUM confidence)
- Signal population analysis (476 total, 26 foundational, 337 with field_key, 10 facet values) -- verified by loading actual YAML

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- all consumer files identified, migration data sources verified
- Pitfalls: HIGH -- based on actual codebase analysis (comment-preserving YAML, 341 unmapped signals, consumer update ordering)

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable internal architecture, no external dependencies)
