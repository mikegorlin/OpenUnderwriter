# Phase 54: Signal Contract V2 - Research

**Researched:** 2026-03-01
**Domain:** Pydantic schema extension, YAML signal contract, declarative field registry
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **V2 YAML Structure**: Parallel threshold fields: Keep `threshold.red/yellow/clear` as English text (human-readable). Add `evaluation.thresholds` as structured list `[{op, value, label}]`. Both coexist on V2 signals. Flat source list for acquisition. Presentation extends, doesn't replace. snake_case naming throughout.
- **Field Registry Design**: Coexist with FIELD_FOR_CHECK. Named function dispatch for COMPUTED fields: `{type: COMPUTED, function: compute_activist_count, args: [extracted.governance.activists]}`. Dual roots supported (`extracted.*` and `company.*`). Single file: `brain/field_registry.yaml`.
- **Signal Selection**: 2-3 from each prefix (FIN, GOV, LIT, STOCK, BIZ). Stick to 5 listed prefixes. Edit signals in-place. Strict Pydantic validation for V2 sections (`extra='forbid'`).
- **Schema Version Dispatch**: Dispatch stub only in `signal_engine.py`. V1 -> existing path. V2 -> stub that falls through to legacy path. Both automated and manual verification. Update CLI for V2 visibility.

### Claude's Discretion
- Exact V2 Pydantic model field names and defaults
- Which specific signals from each prefix to migrate (within the breadth criteria)
- Internal structure of the dispatch stub
- Test fixture design

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCHEMA-01 | BrainSignalEntry extended with optional `acquisition` section | Architecture Patterns (V2 Pydantic models), Code Examples (AcquisitionSpec), current BrainSignalEntry analysis |
| SCHEMA-02 | BrainSignalEntry extended with optional `evaluation` section | Architecture Patterns (V2 Pydantic models), Code Examples (EvaluationSpec), threshold type analysis |
| SCHEMA-03 | BrainSignalEntry extended with optional `presentation` section | Architecture Patterns (V2 Pydantic models), Code Examples (PresentationSpec), existing DisplaySpec analysis |
| SCHEMA-04 | `schema_version` field + dispatch stub | Architecture Patterns (dispatch pattern), signal_engine.py dispatch analysis, Code Examples |
| SCHEMA-05 | Field registry YAML | Architecture Patterns (field registry design), FIELD_FOR_CHECK overlap analysis, COMPUTED field inventory |
| SCHEMA-06 | 10-15 signals migrated to V2 | Signal candidate analysis by prefix, numeric threshold inventory, migration examples |
</phase_requirements>

## Summary

Phase 54 extends the existing BrainSignalEntry Pydantic model with three optional V2 sections (`acquisition`, `evaluation`, `presentation`) plus a `schema_version` field and a `brain/field_registry.yaml`. The existing system is well-positioned for this: BrainSignalEntry already has `extra='allow'` (accepts unknown fields), the YAML loader already enriches+validates, and the signal engine already dispatches by content_type (adding schema_version dispatch is a natural extension).

The key risk is breaking the 400 existing signals. Mitigation is strong: V2 fields are all Optional with defaults, `extra='allow'` on BrainSignalEntry means unknown fields already pass through, and the V2 sub-models use `extra='forbid'` to catch typos on new fields only. The field registry coexists with FIELD_FOR_CHECK (zero deletion in this phase).

**Primary recommendation:** Build V2 Pydantic models as standalone classes imported into BrainSignalEntry, add `schema_version: int = 1` as a top-level field, add dispatch stub at the top of `execute_signals()` before the existing content_type dispatch, and create `brain/field_registry.yaml` as a flat mapping. Migrate 12-15 signals with the clearest numeric thresholds (e.g., FIN.LIQ.position, GOV.BOARD.independence, LIT.DEFENSE.contingent_liabilities, STOCK.PRICE.recent_drop_alert, BIZ.DEPEND.customer_conc).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | v2 (already installed) | V2 sub-model definitions (AcquisitionSpec, EvaluationSpec, PresentationSpec) | Already the validation framework; `extra='forbid'` catches YAML typos |
| PyYAML | CSafeLoader (already installed) | Reading field_registry.yaml and signal YAML at runtime | Already used by BrainLoader; CSafeLoader confirmed at 65ms for 400 signals |
| ruamel.yaml | (already installed) | In-place YAML editing for migrating signals to V2 | Already used for write-back in Phase 51; preserves comments and formatting |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (already installed) | Regression tests for backward compatibility | All V2 schema changes + field registry + dispatch stub |
| Rich | (already installed) | CLI output for `brain stats` V2 visibility | Already used in cli_brain.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML CSafeLoader for registry | ruamel.yaml | ruamel.yaml preserves comments but is 10x slower for read-only; CSafeLoader is correct since registry is read-only at runtime |
| Single field_registry.yaml | Multiple per-domain registry files | Single file is ~800 lines -- manageable. Splitting adds complexity without benefit at this scale |

**Installation:** No new dependencies needed. All libraries already in `pyproject.toml`.

## Architecture Patterns

### Existing Code Structure (Integration Points)

```
src/do_uw/brain/
  brain_signal_schema.py    (157 lines) — BrainSignalEntry, DisplaySpec, BrainSignalThreshold
  brain_unified_loader.py   (430 lines) — _load_and_validate_signals(), enrich_signal()
  brain_enrichment.py       (93 lines)  — enrichment maps for backward-compat
  brain_build_signals.py    (238 lines) — brain build validate+export

src/do_uw/stages/analyze/
  signal_engine.py          (404 lines) — execute_signals() + evaluate_signal() dispatcher
  signal_field_routing.py   (371 lines) — FIELD_FOR_CHECK dict (371 entries) + narrow_result()
  signal_evaluators.py      (315 lines) — evaluate_tiered, evaluate_boolean, etc.
  signal_mappers.py         (505 lines) — map_signal_data() prefix router
  signal_helpers.py         (216 lines) — try_numeric_compare (English threshold parser)
```

### Pattern 1: V2 Pydantic Sub-Models (SCHEMA-01, 02, 03)

**What:** Define AcquisitionSpec, EvaluationSpec, PresentationSpec as standalone Pydantic v2 models with `extra='forbid'`. Add them as Optional fields on BrainSignalEntry.

**Why `extra='forbid'` on sub-models but `extra='allow'` on BrainSignalEntry:** The main model must accept unknown fields to not block future additions. But V2 sub-models are new and controlled -- typos should fail immediately (e.g., `fallback_ot` instead of `fallback_to`).

**Existing precedent:** DisplaySpec and BrainSignalThreshold are already sub-models on BrainSignalEntry (see brain_signal_schema.py lines 27-81).

**Example:**
```python
# brain_signal_schema.py additions

class AcquisitionSource(BaseModel):
    """A single data source in the acquisition chain."""
    model_config = ConfigDict(extra="forbid")

    type: str  # "SEC_10K", "MARKET_PRICE", "SCAC_SEARCH", etc.
    fields: list[str] = Field(default_factory=list)  # dotted paths: ["extracted.financials.liquidity"]
    fallback_to: str | None = None  # next source type in chain

class AcquisitionSpec(BaseModel):
    """V2 acquisition section: sources and their field paths."""
    model_config = ConfigDict(extra="forbid")

    sources: list[AcquisitionSource] = Field(default_factory=list)

class EvaluationThreshold(BaseModel):
    """A single structured threshold entry."""
    model_config = ConfigDict(extra="forbid")

    op: str  # "<", ">", "<=", ">=", "==", "!=", "between", "contains"
    value: float | str | list[float]  # numeric or string comparison
    label: str  # "RED", "YELLOW", "CLEAR"

class EvaluationSpec(BaseModel):
    """V2 evaluation section: formula and structured thresholds."""
    model_config = ConfigDict(extra="forbid")

    formula: str | None = None  # field reference or expression
    thresholds: list[EvaluationThreshold] = Field(default_factory=list)
    window_years: int | None = None  # lookback period

class PresentationDetailLevel(BaseModel):
    """Content at a specific detail level."""
    model_config = ConfigDict(extra="forbid")

    level: str  # "glance", "standard", "deep"
    template: str = ""  # Jinja2-compatible template string
    fields: list[str] = Field(default_factory=list)  # fields to include

class PresentationSpec(BaseModel):
    """V2 presentation section: rendering hints beyond DisplaySpec."""
    model_config = ConfigDict(extra="forbid")

    detail_levels: list[PresentationDetailLevel] = Field(default_factory=list)
    context_templates: dict[str, str] = Field(default_factory=dict)  # keyed by status

# On BrainSignalEntry:
class BrainSignalEntry(BaseModel):
    # ... existing fields ...
    schema_version: int = Field(default=1, description="1=legacy, 2=V2 declarative")
    acquisition: AcquisitionSpec | None = None
    evaluation: EvaluationSpec | None = None
    presentation: PresentationSpec | None = None
```

### Pattern 2: Schema Version Dispatch (SCHEMA-04)

**What:** Add `schema_version` check at the top of signal evaluation, before content_type dispatch.

**Current dispatch flow in signal_engine.py:**
```
execute_signals()
  for each signal:
    1. _signal_sector_applicable()         — sector filter
    2. map_signal_data()                   — prefix-based data routing
    3. content_type dispatch:
       MANAGEMENT_DISPLAY -> evaluate_management_display()
       INFERENCE_PATTERN  -> evaluate_inference_pattern()
       EVALUATIVE_CHECK   -> evaluate_signal()
         -> threshold.type dispatch (tiered/boolean/numeric/temporal/info)
```

**V2 dispatch addition (stub only in Phase 54):**
```
execute_signals()
  for each signal:
    1. _signal_sector_applicable()
    2. map_signal_data()
    3. NEW: schema_version dispatch:
       schema_version == 2 -> _evaluate_v2_stub(sig, data)
                              -> falls through to legacy evaluate
       schema_version == 1 (default) -> existing content_type dispatch
```

**Why before content_type dispatch:** The V2 evaluator in Phase 55 will handle its own content_type awareness. Intercepting earlier avoids modifying the content_type dispatch chain.

**Stub implementation:**
```python
def _evaluate_v2_stub(sig: dict[str, Any], data: dict[str, Any]) -> SignalResult | None:
    """Phase 54 stub: V2 signals fall through to legacy evaluation.

    Phase 55 will replace this with the declarative evaluator.
    Returns None to signal "use legacy path".
    """
    logger.debug(
        "V2 signal %s dispatched to legacy path (stub)",
        sig.get("id", "UNKNOWN"),
    )
    return None  # None = fall through to legacy
```

### Pattern 3: Field Registry YAML (SCHEMA-05)

**What:** Single `brain/field_registry.yaml` mapping logical field names to data paths.

**Current state analysis:**
- FIELD_FOR_CHECK dict: 371 entries mapping signal_id -> field_key
- data_strategy.field_key: 270 signals have this
- Overlap: 263 signals have BOTH, 7 only have data_strategy, 0 only have FIELD_FOR_CHECK
- 130 signals have neither (routed by prefix mappers without narrowing)

**Key insight:** FIELD_FOR_CHECK maps signal_id -> field_key (e.g., `"FIN.LIQ.position"` -> `"current_ratio"`). The field_registry maps field_key -> dotted_path (e.g., `"current_ratio"` -> `"extracted.financials.liquidity.current_ratio"`). These are DIFFERENT abstractions. FIELD_FOR_CHECK says "which field does this signal evaluate?" The registry says "where does this field live in the state model?"

**Registry structure:**
```yaml
# brain/field_registry.yaml
fields:
  # DIRECT_LOOKUP: simple dotted path traversal
  current_ratio:
    type: DIRECT_LOOKUP
    path: extracted.financials.liquidity
    key: current_ratio  # key within the SourcedValue dict at that path

  board_size:
    type: DIRECT_LOOKUP
    path: extracted.governance.board_composition.size

  active_sca_count:
    type: COMPUTED
    function: count_active_scas
    args:
      - extracted.litigation.securities_class_actions

  ceo_cfo_selling_pct:
    type: COMPUTED
    function: compute_ceo_cfo_selling_pct
    args:
      - extracted.market.insider_analysis.transactions
```

**COMPUTED fields (~30% of entries):** These cannot be resolved by simple path traversal. They require len(), filtering, fallback logic, or custom computation. The registry declares the function name and arguments; the actual function lives in signal_mappers*.py and is referenced by name.

### Pattern 4: In-Place Signal Migration (SCHEMA-06)

**What:** Add V2 fields directly to existing YAML entries. Set `schema_version: 2`.

**Example migration (FIN.LIQ.position in balance.yaml):**
```yaml
- id: FIN.LIQ.position
  name: Liquidity Position
  # ... all existing V1 fields unchanged ...
  threshold:
    type: tiered
    red: <1.0 current ratio (inadequate liquidity)
    yellow: <1.5 current ratio (tight liquidity)
    clear: Current ratio at or above 1.5
  # V2 additions:
  schema_version: 2
  acquisition:
    sources:
      - type: SEC_10Q
        fields:
          - extracted.financials.liquidity
        fallback_to: SEC_10K
      - type: SEC_10K
        fields:
          - extracted.financials.liquidity
  evaluation:
    formula: current_ratio
    thresholds:
      - op: "<"
        value: 1.0
        label: RED
      - op: "<"
        value: 1.5
        label: YELLOW
    window_years: 1
  presentation:
    detail_levels:
      - level: glance
        template: "Current ratio: {value}"
      - level: standard
        template: "Liquidity ({current_ratio}x) — {status_label}"
      - level: deep
        fields:
          - current_ratio
          - quick_ratio
          - cash_ratio
    context_templates:
      TRIGGERED: "Liquidity concern: current ratio {value} is below {threshold}"
      CLEAR: "Adequate liquidity with current ratio of {value}"
```

### Anti-Patterns to Avoid

- **Modifying existing V1 field semantics:** All V2 additions are NEW optional fields. Never change the meaning or type of existing fields (threshold.red stays a string, not converted to structured).
- **Consuming V2 fields in the pipeline this phase:** V2 fields are stored but NOT consumed. The dispatch stub must fall through to legacy. If any V2 evaluation path is active, it breaks the "identical results" invariant.
- **Replacing FIELD_FOR_CHECK in this phase:** The field registry coexists. FIELD_FOR_CHECK stays untouched. Phase 55 migrates signals off it one prefix at a time.
- **Loading field_registry.yaml eagerly in the hot path:** Registry should be loaded lazily (like signals) and cached. Don't add import-time loading.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML validation | Custom dict-walking validator | Pydantic v2 `model_validate()` with `extra='forbid'` | Catches typos, type errors, missing fields automatically |
| Threshold operator parsing | Regex-based custom parser | Direct `op`/`value` fields in YAML | The whole point of structured thresholds is eliminating English parsing |
| Field path resolution | New path traversal at this phase | Existing signal_field_routing.narrow_result() | Phase 55 will add the declarative path resolver; don't build it now |
| Signal count tracking | Manual counting in brain_build | BrainSignalEntry.schema_version field + count query on load | Pydantic validates the field; counting is trivial |

**Key insight:** Phase 54 is a SCHEMA phase. It defines the contract. It does NOT implement the runtime behavior changes -- that's Phase 55. The temptation to "wire it up while we're here" must be resisted.

## Common Pitfalls

### Pitfall 1: Breaking the 400-Signal Load
**What goes wrong:** Adding a required field to BrainSignalEntry causes all 400 signals to fail validation (they don't have the V2 fields).
**Why it happens:** Forgetting `= None` or `= Field(default=1)` on new fields.
**How to avoid:** All V2 fields on BrainSignalEntry are Optional with defaults. V2 sub-models are only validated when present (Optional[AcquisitionSpec]). Run `test_load_signals_returns_400_signals` immediately after schema changes.
**Warning signs:** Test count drops below 400 or BrainLoader raises ValidationError on startup.

### Pitfall 2: V2 Sub-Model extra='allow' Leak
**What goes wrong:** YAML typos in V2 sections pass silently because sub-models also use `extra='allow'`.
**Why it happens:** Copying the BrainSignalEntry config to sub-models out of habit.
**How to avoid:** V2 sub-models (AcquisitionSpec, EvaluationSpec, PresentationSpec) MUST use `extra='forbid'`. BrainSignalEntry stays `extra='allow'`.
**Warning signs:** YAML with `falback_to` (typo) loads without error.

### Pitfall 3: Registry Path/Field Key Confusion
**What goes wrong:** The field_registry maps field_key -> dotted_path, but someone confuses it with signal_id -> field_key (which is FIELD_FOR_CHECK's job).
**Why it happens:** Two different mappings exist at different abstraction levels.
**How to avoid:** Document clearly: signal_id -> field_key (FIELD_FOR_CHECK or data_strategy.field_key), field_key -> dotted_path (field_registry). The registry resolves field_keys, not signal_ids.
**Warning signs:** Registry entries keyed by "FIN.LIQ.position" instead of "current_ratio".

### Pitfall 4: Accidental V2 Evaluation
**What goes wrong:** The dispatch stub accidentally evaluates V2 signals differently, changing pipeline output.
**Why it happens:** Stub returns a result instead of None (fallthrough).
**How to avoid:** Stub MUST return None to trigger legacy fallback. Add assertion test: run same signals through V1 and V2 paths, compare results.
**Warning signs:** Signal counts or statuses change between before/after migration.

### Pitfall 5: YAML Edit Corruption
**What goes wrong:** In-place YAML editing with ruamel.yaml corrupts existing fields or loses comments.
**Why it happens:** Rewriting the full file instead of targeted insertions; CSafeLoader strips comments.
**How to avoid:** Use ruamel.yaml's CommentedMap for in-place edits that preserve formatting. Test by comparing git diff -- only V2 fields should be added.
**Warning signs:** Git diff shows reformatting of existing V1 fields.

### Pitfall 6: File Size Explosion
**What goes wrong:** 400 signals x 3 V2 sections = massive YAML files.
**Why it happens:** V2 sections add 15-25 lines per signal.
**How to avoid:** Only 10-15 signals get V2 fields in this phase. At 15 signals x 20 lines = 300 lines of additions across 36 files. Manageable.
**Warning signs:** Any single YAML file exceeding 1000 lines.

## Code Examples

### Current BrainSignalEntry (what we extend)
```python
# Source: /src/do_uw/brain/brain_signal_schema.py (lines 97-157)
class BrainSignalEntry(BaseModel):
    model_config = {"extra": "allow"}  # accept unknown fields
    id: str
    name: str
    work_type: str
    tier: int
    depth: int
    threshold: BrainSignalThreshold
    provenance: BrainSignalProvenance
    layer: str | None = None
    factors: list[str] = Field(default_factory=list)
    # ... 20+ optional fields ...
    facet: str = ""
    display: DisplaySpec | None = None
```

### Current YAML Loader (where validation happens)
```python
# Source: /src/do_uw/brain/brain_unified_loader.py (lines 76-113)
def _load_and_validate_signals(signals_dir=None):
    all_raw = []
    for yaml_file in sorted(signals_dir.glob("**/*.yaml")):
        data = yaml.load(yaml_file.read_text(), Loader=yaml.CSafeLoader)
        # ... collect raw dicts ...
    validated = []
    for raw in all_raw:
        enriched = enrich_signal(raw)
        try:
            BrainSignalEntry.model_validate(enriched)  # V2 fields validated here
            validated.append(enriched)
        except ValidationError:
            skipped += 1
    return validated, skipped
```

### Current Dispatch (where version check goes)
```python
# Source: /src/do_uw/stages/analyze/signal_engine.py (lines 82-125)
for sig in chunk:
    data = map_signal_data(signal_id, sig, extracted, company)
    content_type = sig.get("content_type", "EVALUATIVE_CHECK")
    if content_type == "MANAGEMENT_DISPLAY":
        result = evaluate_management_display(sig, data)
    elif content_type == "INFERENCE_PATTERN":
        result = evaluate_inference_pattern(sig, data)
    else:
        result = evaluate_signal(sig, data)
```

### Current narrow_result() (field registry replaces the lookup, not the function)
```python
# Source: /src/do_uw/stages/analyze/signal_field_routing.py (lines 19-47)
def narrow_result(signal_id, data, signal_def=None):
    # Priority 1: data_strategy.field_key
    if signal_def is not None:
        ds = signal_def.get("data_strategy")
        if isinstance(ds, dict):
            fk = ds.get("field_key")
            if fk is not None:
                return {fk: data[fk]} if fk in data else {}
    # Priority 2: FIELD_FOR_CHECK
    field = FIELD_FOR_CHECK.get(signal_id)
    if field is not None:
        return {field: data[field]} if field in data else {}
    return data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 4 competing loaders | Single BrainLoader (YAML) | Phase 53 (2026-03-01) | No DuckDB for signal defs |
| DuckDB signal table at runtime | YAML read directly via CSafeLoader | Phase 53 (2026-03-01) | 65ms load, no DuckDB dep for signals |
| English-only thresholds | English + structured (V2) | Phase 54 (this phase) | Machine-readable evaluation |
| FIELD_FOR_CHECK dict only | FIELD_FOR_CHECK + field_registry.yaml | Phase 54 (this phase) | Declarative field resolution |
| Implicit data paths in mappers | Explicit paths in acquisition YAML | Phase 54 (this phase) | Signals declare their own data needs |

## Detailed Data Analysis

### Signal Distribution by Prefix
| Prefix | Count | Numeric Thresholds | Best V2 Candidates |
|--------|-------|--------------------|---------------------|
| FIN | 58 | 33 | FIN.LIQ.position, FIN.DEBT.coverage, FIN.ACCT.restatement |
| GOV | 85 | 47 | GOV.BOARD.independence, GOV.PAY.say_on_pay, GOV.ACTIVIST.13d_filings |
| LIT | 65 | 32 | LIT.SCA.active, LIT.DEFENSE.contingent_liabilities, LIT.OTHER.product |
| STOCK | 35 | 22 | STOCK.PRICE.recent_drop_alert, STOCK.SHORT.position, STOCK.VALUATION.pe_ratio |
| BIZ | 43 | 14 | BIZ.DEPEND.customer_conc, BIZ.STRUCT.subsidiary_count, BIZ.SIZE.market_cap |

### Threshold Type Distribution (400 signals)
| Type | Count | V2 Structured? | Notes |
|------|-------|-----------------|-------|
| tiered | 236 | Yes (most benefit) | English text parsed via regex -- most error-prone |
| display | 83 | No (info-only) | No threshold evaluation |
| boolean | 21 | Yes | Simple true/false, easy conversion |
| info | 13 | No (info-only) | No threshold evaluation |
| temporal | 10 | Deferred | Complex multi-period logic |
| value | 9 | Yes | Numeric comparison |
| count | 9 | Yes | Numeric comparison |
| percentage | 8 | Yes | Numeric comparison |
| pattern | 6 | Deferred | Multi-signal inference |
| classification | 4 | Deferred | Categorical (not numeric) |
| multi_period | 1 | Deferred | Complex temporal |

### FIELD_FOR_CHECK vs data_strategy Overlap
| Category | Count | Meaning |
|----------|-------|---------|
| Both data_strategy.field_key AND FIELD_FOR_CHECK | 263 | Redundant -- registry replaces both eventually |
| Only data_strategy.field_key | 7 | Field key in YAML, no dict entry needed |
| Only FIELD_FOR_CHECK | 0 | Every FIELD_FOR_CHECK signal also has data_strategy |
| Neither | 130 | Routed by prefix mappers without field narrowing |

### Recommended V2 Migration Candidates (12-15 signals)

**FIN prefix (3 signals):**
1. `FIN.LIQ.position` -- tiered, `<1.0` / `<1.5`, field_key=current_ratio, DIRECT_LOOKUP
2. `FIN.DEBT.coverage` -- tiered, `<1.5x` / `<2.5x`, field_key=interest_coverage, DIRECT_LOOKUP
3. `FIN.ACCT.restatement` -- tiered, `>1 restatements`, field_key=restatements, COMPUTED (len)

**GOV prefix (3 signals):**
4. `GOV.BOARD.independence` -- percentage, `<50%` / `<67%`, field_key=board_independence, DIRECT_LOOKUP
5. `GOV.PAY.say_on_pay` -- percentage, `<70%` / `<80%`, field_key=say_on_pay_pct, DIRECT_LOOKUP
6. `GOV.ACTIVIST.13d_filings` -- tiered, `>0`, field_key=filing_13d_count, COMPUTED (count)

**LIT prefix (3 signals):**
7. `LIT.SCA.active` -- boolean, active_sca_count > 0, field_key=active_sca_count, COMPUTED (filter+count)
8. `LIT.DEFENSE.contingent_liabilities` -- value, `>$100M`, field_key=contingent_liabilities_total, DIRECT_LOOKUP
9. `LIT.OTHER.product` -- tiered, `>5 active`, field_key=product_liability_count, COMPUTED (count)

**STOCK prefix (2-3 signals):**
10. `STOCK.PRICE.recent_drop_alert` -- tiered, `>10%` / `>5%`, field_key=decline_from_high, DIRECT_LOOKUP
11. `STOCK.SHORT.position` -- tiered, `>15%` / `>10%`, field_key=short_interest_pct, DIRECT_LOOKUP
12. `STOCK.VALUATION.pe_ratio` -- tiered, `>50x`, field_key=pe_ratio, DIRECT_LOOKUP

**BIZ prefix (2-3 signals):**
13. `BIZ.DEPEND.customer_conc` -- percentage, `>25%`, field_key=customer_concentration, COMPUTED
14. `BIZ.STRUCT.subsidiary_count` -- value, `>100`, field_key=subsidiary_count, DIRECT_LOOKUP
15. `BIZ.SIZE.market_cap` -- tiered (info), field_key=market_cap, DIRECT_LOOKUP

This gives 15 signals across all 5 prefixes with a mix of DIRECT_LOOKUP (9) and COMPUTED (6), covering tiered (7), boolean (1), percentage (2), value (3), and info (2) threshold types.

## Open Questions

1. **Threshold operator ordering**
   - What we know: English thresholds check red first, then yellow. Structured thresholds should maintain the same ordering.
   - What's unclear: Should `evaluation.thresholds` be ordered (check first match) or labeled (check all, return highest severity)?
   - Recommendation: First-match ordered list (red thresholds first). This matches the current `try_numeric_compare()` which checks red before yellow. Document ordering convention.

2. **COMPUTED function registration**
   - What we know: ~30% of FIELD_FOR_CHECK entries use computed values (len(), filter, fallback logic). Named function dispatch is the decision.
   - What's unclear: Where does the function registry live? A dict in field_registry.py? Or discovered via a decorator?
   - Recommendation: Simple dict in a new `brain/field_registry_functions.py` mapping function_name -> callable. Keep it explicit (no magic discovery). Can hold 30-40 entries easily.

3. **SourcedValue unwrapping in paths**
   - What we know: Many dotted paths traverse through SourcedValue wrappers. `_safe_sourced()` handles this in mappers.
   - What's unclear: Should the field_registry declare which path segments are SourcedValue-wrapped?
   - Recommendation: Phase 55 concern. The registry in Phase 54 declares paths but doesn't resolve them. The resolver (Phase 55) will need SourcedValue-awareness. For now, just document the paths accurately.

4. **Enrichment of V2 fields**
   - What we know: `enrich_signal()` in brain_enrichment.py adds backward-compat fields. V2 signals may need enrichment too.
   - What's unclear: Do V2 fields need any enrichment before validation?
   - Recommendation: No enrichment for V2 fields. They are explicit in YAML and validated directly by Pydantic. Enrichment is a V1 backward-compat mechanism. V2 signals should be self-describing.

## Sources

### Primary (HIGH confidence)
- `/src/do_uw/brain/brain_signal_schema.py` -- current BrainSignalEntry model (157 lines, verified)
- `/src/do_uw/brain/brain_unified_loader.py` -- YAML loading and validation pipeline (430 lines, verified)
- `/src/do_uw/stages/analyze/signal_engine.py` -- execution dispatch (404 lines, verified)
- `/src/do_uw/stages/analyze/signal_field_routing.py` -- FIELD_FOR_CHECK dict (371 entries, verified)
- `/src/do_uw/stages/analyze/signal_evaluators.py` -- threshold evaluators (315 lines, verified)
- `/src/do_uw/stages/analyze/signal_helpers.py` -- try_numeric_compare English parser (216 lines, verified)
- `/src/do_uw/brain/signals/fin/balance.yaml` -- sample signal YAML (12 signals, verified)
- `tests/brain/test_brain_unified_loader.py` -- 47 tests passing (verified)

### Secondary (MEDIUM confidence)
- `.planning/research/brain-redundancy-audit.md` -- DuckDB/YAML architecture analysis
- `.planning/research/signal-composition-model.md` -- 400-signal to 10-factor pipeline analysis
- `.planning/phases/54-signal-contract-v2/54-CONTEXT.md` -- user decisions

### Analysis (HIGH confidence -- derived from code)
- Signal prefix distribution: BIZ(43), EXEC(20), FIN(58), FWRD(79), GOV(85), LIT(65), NLP(15), STOCK(35) = 400
- FIELD_FOR_CHECK overlap: 263 both, 7 data_strategy only, 0 FFC only, 130 neither
- Numeric threshold candidates: FIN(33), GOV(47), LIT(32), STOCK(22), BIZ(14) = 148 total
- data_strategy.field_key coverage: 270/400 signals (67.5%)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use
- Architecture: HIGH -- all integration points verified in actual source code
- Pitfalls: HIGH -- derived from known patterns in the codebase (predecessor failures documented)
- Signal candidates: HIGH -- selected from actual signal analysis with verified field_key mappings

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable internal architecture, no external dependencies)
