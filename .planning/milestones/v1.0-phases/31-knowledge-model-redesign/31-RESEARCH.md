# Phase 31: Knowledge Model Redesign & Check Architecture - Research

**Researched:** 2026-02-15
**Domain:** Check/knowledge model architecture, metadata enrichment, declarative routing
**Confidence:** HIGH

## Summary

Phase 31 redesigns the check/knowledge model so that every worksheet item is a self-describing knowledge unit carrying its full lifecycle: why it matters, where to get the data, how to extract it, how to evaluate it, and how to present it. The current system has 388 checks in `brain/checks.json` with 18 fields per check, but checks lack lifecycle metadata -- you cannot look at a check definition and understand the full pipeline from data source through extraction, evaluation, and rendering without reading 6+ Python files.

The system currently relies on a 3-layer mapping architecture: `check_engine.py` dispatches to `check_mappers.py` (prefix-based routing) which calls `check_field_routing.py` (per-check field narrowing). Phase 26 added `check_mappers_phase26.py` and Phase 27 added `check_mappers_fwrd.py`, creating 5 files totaling ~1,900 lines of imperative routing code. This routing knowledge is trapped in Python code rather than being declarative metadata on the check itself.

The phase introduces three content types (MANAGEMENT_DISPLAY, EVALUATIVE_CHECK, INFERENCE_PATTERN) that map directly to the user's Data Complexity Spectrum. The current `category` field (CONTEXT_DISPLAY/DECISION_DRIVING) is a two-way split that conflates "data to show" with "data to evaluate" -- the new three-way split separates "must show" (management guidelines say so), "evaluate against threshold" (analytical question), and "connect dots across signals" (pattern recognition). This aligns each content type with different metadata depth requirements.

**Primary recommendation:** Enrich `brain/checks.json` with lifecycle metadata fields, replace imperative routing code with declarative field mappings on each check, and type all 388 checks with the three content types + depth levels.

## Standard Stack

### Core (Already in Use -- No New Dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Check model validation, schema enforcement | Already the project standard per CLAUDE.md |
| SQLAlchemy 2.0 | 2.x | Knowledge store ORM (models.py) | Already backing `knowledge/models.py` |
| JSON Schema | built-in | checks.json validation | Already using `$schema` field in checks.json |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jsonschema | 4.x | Runtime validation of enriched checks.json | If strict schema enforcement is desired at load time |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON enrichment in checks.json | YAML for check definitions | YAML is more readable but would break existing loaders; JSON is already standard |
| Pydantic models for checks | Keep raw dicts | Pydantic catches schema violations at load time; raw dicts fail silently |
| SQLAlchemy migration | Direct ALTER TABLE | Alembic migrations already exist in knowledge/migrations/; use the pattern |

**Installation:** No new packages needed. All tools already in the project.

## Architecture Patterns

### Current Architecture (What Exists)

```
brain/checks.json (388 checks, 18 fields each)
       |
       v
compat_loader.py → BackwardCompatLoader.load_checks()
       |
       v
analyze/__init__.py → execute_checks()
       |
       v
check_engine.py → map_check_data() → evaluate_check()
       |                                    |
       v                                    v
check_mappers.py (prefix routing)    check_evaluators.py (threshold dispatch)
       |
       +-- check_mappers_phase26.py (FIN.TEMPORAL/FORENSIC/QUALITY, EXEC, NLP)
       +-- check_mappers_fwrd.py (FWRD.DISC/MACRO/EVENT/NARRATIVE/WARN)
       +-- check_field_routing.py (236 check → field mappings)
```

**Problems with current architecture:**
1. Routing knowledge is in 5 Python files (~1,900 lines), not on the check
2. Adding a new check requires editing Python code (mapper + field routing)
3. No way to know from the check definition what field it evaluates
4. No rationale for why a check exists or what underwriting question it answers
5. 241 checks have qualitative thresholds (text strings), making automated evaluation impossible
6. Coverage gaps section shows what was not checked but not what should have been checked

### Recommended Architecture

```
brain/checks.json (388 checks, enriched with lifecycle metadata)
       |
       v  (new) Pydantic CheckDefinition model validates at load time
       |
       v
check_engine.py → declarative_mapper() → evaluate_check()
       |                                       |
       v                                       v
(reads field_mapping from check def)    check_evaluators.py (unchanged)
       |
       v
ExtractedData.{path from check def}
```

### Enriched Check Schema

The check definition becomes self-describing:

```json
{
  "id": "FIN.LIQ.position",
  "name": "Liquidity Position Assessment",
  "content_type": "EVALUATIVE_CHECK",
  "depth": 2,

  "rationale": "Current ratio below 1.0 indicates potential inability to meet short-term obligations, increasing D&O risk from creditor lawsuits and going concern questions.",

  "data_strategy": {
    "primary_source": "SEC_10K",
    "extraction_path": "extracted.financials.liquidity.current_ratio",
    "fallback_sources": ["SEC_10Q"],
    "field_key": "current_ratio"
  },

  "evaluation_criteria": {
    "type": "tiered",
    "metric": "current_ratio",
    "direction": "lower_is_worse",
    "red": {"operator": "<", "value": 0.5, "label": "Severe liquidity crisis"},
    "yellow": {"operator": "<", "value": 1.0, "label": "Below minimum acceptable"},
    "clear": {"operator": ">=", "value": 1.0, "label": "Adequate liquidity"}
  },

  "presentation": {
    "display_format": "ratio",
    "worksheet_label": "Current Ratio",
    "section_placement": "Section 3: Financial Health"
  },

  "section": 3,
  "pillar": "P2_HOW_LIKELY",
  "factors": ["F3"],
  "category": "DECISION_DRIVING",
  "signal_type": "LEVEL",
  "hazard_or_signal": "SIGNAL",
  "plaintiff_lenses": ["CREDITORS", "SHAREHOLDERS"],
  "tier": 1,
  "threshold": {"type": "tiered", "red": "<0.5", "yellow": "<1.0", "clear": ">=1.0"},
  "required_data": ["SEC_10K"],
  "data_locations": {"SEC_10K": ["item_8_financials"]},
  "execution_mode": "AUTO"
}
```

### Three Content Types

| Type | Count (est.) | Metadata Depth | What It Does |
|------|-------------|----------------|--------------|
| `MANAGEMENT_DISPLAY` | ~64 | Light: source + display format | Data required by underwriting guidelines -- no analytical question |
| `EVALUATIVE_CHECK` | ~238+ | Full: rationale, thresholds, evaluation criteria | Analytical question with pass/fail thresholds |
| `INFERENCE_PATTERN` | ~19+ | Full + dependencies: constituent checks, trigger logic | Cross-signal pattern recognition |

**Mapping from current data:**
- `CONTEXT_DISPLAY` with no factors (64 checks) --> `MANAGEMENT_DISPLAY`
- `CONTEXT_DISPLAY` with factors (86 checks) --> some `EVALUATIVE_CHECK`, some `MANAGEMENT_DISPLAY` (needs per-check review)
- `DECISION_DRIVING` (238 checks) --> `EVALUATIVE_CHECK`
- `signal_type: PATTERN` (19 checks) --> `INFERENCE_PATTERN`

**Note:** Some CONTEXT_DISPLAY checks with factors are hybrid -- they display data AND contribute to scoring. These need individual classification during enrichment.

### Depth Levels

| Level | Description | What's Needed | Example |
|-------|-------------|---------------|---------|
| Level 1 | Extract & Display | Source path, display format | Market cap, SIC code |
| Level 2 | Extract & Compute | Source path, formula, thresholds | Altman Z-Score, current ratio |
| Level 3 | Extract & Infer | Multiple sources, pattern logic, combination rules | Restatement + auditor change + stock drop |
| Level 4 | Hunt & Analyze | Broad search, aggregation, dedup, then analysis | Litigation landscape, blind spot detection |

### Declarative Field Mapping (Replacing check_field_routing.py)

Currently `check_field_routing.py` has 236 hard-coded mappings:
```python
FIELD_FOR_CHECK: dict[str, str] = {
    "FIN.LIQ.position": "current_ratio",
    "FIN.LIQ.working_capital": "current_ratio",
    ...
}
```

The new approach puts this on the check definition:
```json
{
  "id": "FIN.LIQ.position",
  "data_strategy": {
    "extraction_path": "extracted.financials.liquidity.current_ratio",
    "field_key": "current_ratio"
  }
}
```

The mapper then becomes a generic function:
```python
def declarative_map(check_def: CheckDefinition, extracted: ExtractedData) -> dict[str, Any]:
    """Resolve field_key from extraction_path on the check definition."""
    path = check_def.data_strategy.extraction_path
    value = resolve_dotted_path(extracted, path)
    return {check_def.data_strategy.field_key: value}
```

**Critical constraint:** The existing prefix-based mappers (`check_mappers.py`, `check_mappers_phase26.py`, `check_mappers_fwrd.py`) do more than field routing -- they compute derived values (e.g., `_compute_ceo_cfo_selling_pct`, unwrap SourcedValues, aggregate lists). The declarative mapper cannot replace ALL mapper logic in Phase 31. The path is:

1. Phase 31: Add `data_strategy.field_key` to all checks (replaces `check_field_routing.py`)
2. Future: Migrate computation logic from mappers to EXTRACT stage where it belongs
3. Future: Phase out prefix-based mappers entirely

### Pattern 1: Backward-Compatible Enrichment

**What:** Add new fields to checks.json without breaking existing consumers
**When to use:** Throughout Phase 31 -- every change must be additive
**Example:**
```python
# Old consumers still work -- they just ignore new fields
check = checks_data["checks"][0]
check["id"]  # still works
check["threshold"]  # still works
# New consumers can read enriched metadata
check.get("content_type", "EVALUATIVE_CHECK")  # new field, defaulted
check.get("data_strategy", {}).get("field_key")  # new field, optional
```

### Pattern 2: Pydantic Validation at Load Time

**What:** Validate checks.json against a Pydantic model when loaded
**When to use:** After enrichment, to catch missing/invalid metadata
**Example:**
```python
class DataStrategy(BaseModel):
    """How to get data for this check."""
    primary_source: str
    extraction_path: str | None = None
    field_key: str | None = None
    fallback_sources: list[str] = Field(default_factory=list)

class CheckDefinition(BaseModel):
    """Enriched check definition with lifecycle metadata."""
    id: str
    name: str
    content_type: Literal["MANAGEMENT_DISPLAY", "EVALUATIVE_CHECK", "INFERENCE_PATTERN"]
    depth: int = Field(ge=1, le=4)
    rationale: str | None = None
    data_strategy: DataStrategy | None = None
    # ... existing fields preserved
```

### Anti-Patterns to Avoid

- **Breaking the existing pipeline:** All changes MUST be additive. The check engine must continue working with old-format checks during migration.
- **Duplicating routing in two places:** Don't keep `check_field_routing.py` AND `data_strategy.field_key` -- migrate fully, then remove old code.
- **Enriching all 388 checks manually in one shot:** Use scripted enrichment for mechanical fields (content_type, depth from category/factors), manual enrichment only for rationale and nuanced fields.
- **Over-engineering the schema:** Don't add fields "because we might need them." Every field must serve an identified consumer.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema validation | Custom validation logic | Pydantic model + `model_validate()` | Pydantic already handles nested validation, coercion, defaults |
| Database migrations | Manual ALTER TABLE | Alembic (already in `knowledge/migrations/`) | Migration versioning already established in the project |
| Content type classification | Manual per-check tagging | Scripted classification from existing `category` + `factors` fields | 85%+ can be auto-classified, only edge cases need manual review |
| Dotted path resolution | String splitting + getattr chains | `operator.attrgetter` or a small utility | Python stdlib handles this cleanly |

**Key insight:** The bulk of the work is not code -- it's data enrichment. The 388 checks need metadata added to their JSON definitions. The code changes are relatively small (Pydantic model, generic mapper, knowledge store schema update). The data enrichment can be partially automated (content_type from category+factors, field_key from check_field_routing.py, depth from signal_type) but rationale/presentation fields need manual or LLM-assisted writing.

## Common Pitfalls

### Pitfall 1: Breaking the Pipeline During Migration
**What goes wrong:** Changing checks.json format breaks existing loader/engine that expects current structure.
**Why it happens:** New fields or renamed fields cause KeyError or validation failures.
**How to avoid:** All new fields are OPTIONAL with defaults. Existing fields are preserved. The `BackwardCompatLoader` and `check_engine.py` continue to work unchanged during migration. Only new code reads new fields.
**Warning signs:** Tests fail after checks.json changes; pipeline crashes on load.

### Pitfall 2: check_field_routing.py / data_strategy.field_key Divergence
**What goes wrong:** Two sources of truth for field routing -- old Python dict and new JSON metadata.
**Why it happens:** Migration is partial; some checks have field_key in JSON, others still rely on FIELD_FOR_CHECK.
**How to avoid:** Phase 31 Plan 1 migrates ALL 236 entries from FIELD_FOR_CHECK to data_strategy.field_key. Plan 2 creates a new declarative mapper that reads field_key. Plan 3 removes check_field_routing.py. Never have both active simultaneously.
**Warning signs:** Check evaluation results differ between old and new routing paths.

### Pitfall 3: Content Type Misclassification
**What goes wrong:** A MANAGEMENT_DISPLAY check that actually drives scoring gets miscategorized, removing it from threshold evaluation.
**Why it happens:** 86 CONTEXT_DISPLAY checks have factors -- they contribute to scoring despite being "display." These are not pure management display items.
**How to avoid:** Only the 64 CONTEXT_DISPLAY checks with NO factors are definitely MANAGEMENT_DISPLAY. The 86 with factors need individual review against the question: "Is this check answering an analytical question, or just showing data that happens to map to a factor?"
**Warning signs:** Coverage gaps increase after reclassification; score changes for known-good tickers.

### Pitfall 4: Rationale Hallucination
**What goes wrong:** LLM-generated rationales contain plausible-sounding but incorrect D&O underwriting reasoning.
**Why it happens:** D&O underwriting is a specialized domain; general language models may confuse claims theories or misstate legal standards.
**How to avoid:** Write rationales from the existing `pillar` (P1_WHAT_WRONG, P2_HOW_LIKELY, P3_HOW_BAD, P4_WHAT_NEXT) and `plaintiff_lenses` fields. Validate against known D&O claims theories in patterns.json. Have rationales reviewed for accuracy.
**Warning signs:** Rationales reference incorrect legal theories or misstate what a metric measures.

### Pitfall 5: Extraction Path Mismatch
**What goes wrong:** `data_strategy.extraction_path` references a field that doesn't exist on ExtractedData or uses wrong nesting.
**Why it happens:** The Pydantic state model is complex (ExtractedData -> ExtractedFinancials -> AuditProfile -> going_concern, etc.). Wrong path = silent None, which produces SKIPPED.
**How to avoid:** Generate extraction_path from the ACTUAL mapper code. For each mapper function, trace what ExtractedData fields it reads. Automated: grep mapper functions, extract field access patterns, produce extraction_path. Verify with a test that resolves every path against a populated ExtractedData.
**Warning signs:** Skip rate increases after switching to declarative mapping.

### Pitfall 6: Knowledge Store Schema Drift
**What goes wrong:** `knowledge/models.py` Check table doesn't get updated with new fields; checks.json has richer data than the store can hold.
**Why it happens:** Two representations: JSON (brain/) and SQLite (knowledge/). They can drift.
**How to avoid:** Update the Check ORM model in `knowledge/models.py` with all new columns. Add an Alembic migration (006_knowledge_model_enrichment.py). Update `store_converters.py` to round-trip new fields.
**Warning signs:** Knowledge store queries return checks missing enriched metadata.

## Code Examples

### Example 1: Automated Content Type Classification

```python
def classify_content_type(check: dict) -> str:
    """Derive content_type from existing category and factors fields.

    Rules:
    - CONTEXT_DISPLAY + no factors = MANAGEMENT_DISPLAY
    - signal_type == PATTERN = INFERENCE_PATTERN
    - Everything else = EVALUATIVE_CHECK
    """
    category = check.get("category", "")
    factors = check.get("factors", [])
    signal_type = check.get("signal_type", "")

    if signal_type == "PATTERN":
        return "INFERENCE_PATTERN"
    if category == "CONTEXT_DISPLAY" and not factors:
        return "MANAGEMENT_DISPLAY"
    return "EVALUATIVE_CHECK"
```

### Example 2: Automated field_key Migration from check_field_routing.py

```python
# Script to merge FIELD_FOR_CHECK entries into checks.json
import json
from check_field_routing import FIELD_FOR_CHECK

with open("brain/checks.json") as f:
    data = json.load(f)

for check in data["checks"]:
    check_id = check["id"]
    field_key = FIELD_FOR_CHECK.get(check_id)
    if field_key:
        if "data_strategy" not in check:
            check["data_strategy"] = {}
        check["data_strategy"]["field_key"] = field_key

with open("brain/checks.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Example 3: Automated Depth Level Classification

```python
def classify_depth(check: dict) -> int:
    """Derive depth from signal_type, threshold, and required_data.

    Level 1: Extract & Display (info/display threshold, no factors)
    Level 2: Extract & Compute (numeric thresholds, single source)
    Level 3: Extract & Infer (pattern/forensic signal, multiple sources)
    Level 4: Hunt & Analyze (web search required, litigation)
    """
    signal_type = check.get("signal_type", "")
    threshold_type = check.get("threshold", {}).get("type", "info")
    required_data = check.get("required_data", [])

    if threshold_type in ("info", "display", "classification"):
        return 1
    if signal_type in ("PATTERN", "FORENSIC"):
        return 3
    if any(src in required_data for src in ("SCAC_SEARCH", "SEC_ENFORCEMENT")):
        return 4
    if threshold_type in ("percentage", "count", "value", "boolean"):
        return 2
    if threshold_type == "temporal":
        return 3
    return 2  # default for tiered
```

### Example 4: Generic Declarative Mapper

```python
def resolve_dotted_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like 'financials.liquidity.current_ratio' on an object."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            attr = getattr(current, part)
            # Unwrap SourcedValue
            if hasattr(attr, 'value') and hasattr(attr, 'source'):
                current = attr.value
            else:
                current = attr
        else:
            return None
    return current


def declarative_map_check(
    check_def: dict,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
) -> dict[str, Any]:
    """Map check data using declarative data_strategy metadata."""
    data_strategy = check_def.get("data_strategy", {})
    field_key = data_strategy.get("field_key")
    extraction_path = data_strategy.get("extraction_path")

    if not field_key or not extraction_path:
        return {}  # Fall back to existing prefix routing

    # Remove "extracted." prefix if present
    if extraction_path.startswith("extracted."):
        extraction_path = extraction_path[len("extracted."):]

    value = resolve_dotted_path(extracted, extraction_path)
    return {field_key: value}
```

### Example 5: Coverage Gap Visibility Enhancement

```python
class CoverageGapInfo(BaseModel):
    """What the underwriter needs to know about unchecked items."""
    check_id: str
    check_name: str
    content_type: str  # MANAGEMENT_DISPLAY, EVALUATIVE_CHECK, INFERENCE_PATTERN
    rationale: str  # WHY this matters (from enriched check def)
    data_status: str  # DATA_UNAVAILABLE, NOT_APPLICABLE
    data_status_reason: str
    mitigation: str  # What the underwriter should do about this gap
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw dict checks, prefix routing | Classified checks (Phase 26), field routing (Phase 28) | Phases 26-28 | Better routing accuracy |
| Two categories (DECISION_DRIVING/CONTEXT_DISPLAY) | Three content types with lifecycle metadata (Phase 31) | Phase 31 (planned) | Self-describing checks |
| Python-coded field routing (236 entries) | Declarative field_key on check definition | Phase 31 (planned) | No code changes to add checks |
| No check rationale | Rationale + underwriting context per check | Phase 31 (planned) | Coverage gaps show WHY items matter |
| Fire-and-forget check results | Feedback loop (Phase 30) + lifecycle metadata (Phase 31) | Phases 30-31 | Data-driven check curation |

## Implementation Strategy

### Critical Ordering Constraints

1. **Schema changes first** -- Define the Pydantic CheckDefinition model and the enriched checks.json schema BEFORE writing any migration scripts.
2. **Automated enrichment before manual** -- Script content_type, depth, and field_key from existing data. Only then do manual rationale writing.
3. **Backward compatibility throughout** -- At no point should the existing pipeline break. All new fields are optional with defaults.
4. **check_field_routing.py replacement last** -- Only remove the old routing code after ALL 236 checks have verified field_key values and the declarative mapper is confirmed equivalent.

### Estimated Work Distribution

| Work Item | Effort | Automatable? |
|-----------|--------|--------------|
| CheckDefinition Pydantic model | Small | No (design work) |
| Content type classification (388 checks) | Small | Yes (~85% scripted) |
| Depth classification (388 checks) | Small | Yes (fully scriptable) |
| field_key migration (236 checks) | Small | Yes (from FIELD_FOR_CHECK dict) |
| extraction_path derivation | Medium | Partially (from mapper code analysis) |
| Rationale writing (388 checks) | Large | Partially (template from pillar/lenses) |
| presentation_template (388 checks) | Medium | Partially (from render section analysis) |
| Knowledge store schema update | Small | No |
| Declarative mapper implementation | Medium | No |
| Coverage gap enhancement | Small | No |
| Testing + verification | Medium | No |

### What Can Be Deferred

- **Full extraction_path for all checks**: Start with the 236 checks that have field_key entries. The remaining 152 (mostly Phase 26+ checks) already use dedicated mappers that return single-field dicts.
- **Presentation templates**: Nice-to-have but not required for the core goal of self-describing checks.
- **Removing prefix-based mappers**: Declarative routing can coexist with prefix routing initially. The mappers handle SourcedValue unwrapping and computed fields that can't be expressed as simple paths.

## Open Questions

1. **86 CONTEXT_DISPLAY checks with factors -- what content_type?**
   - What we know: They have factors (F1-F10) mapped, meaning they influence scoring. But they're categorized as CONTEXT_DISPLAY, meaning they provide context rather than driving decisions.
   - What's unclear: Are these truly evaluative (answering an analytical question) or are they display items that happen to carry weight? Each needs individual review.
   - Recommendation: Default to EVALUATIVE_CHECK for any check with factors. Review manually during enrichment and reclassify to MANAGEMENT_DISPLAY only if the check truly asks no analytical question.

2. **SourcedValue unwrapping in declarative mapper**
   - What we know: The current mappers extensively use `_safe_sourced()` to unwrap SourcedValue wrappers. The extraction_path approach needs to handle this.
   - What's unclear: Should the declarative mapper automatically detect and unwrap SourcedValue, or should the extraction_path explicitly reference `.value`?
   - Recommendation: The generic mapper should auto-detect SourcedValue (check for `.value` attribute) and unwrap automatically. This matches the current behavior and avoids cluttering paths with `.value`.

3. **Computed values in mappers**
   - What we know: ~15 mapper functions compute derived values (e.g., `_compute_ceo_cfo_selling_pct`, counting active SCAs, aggregating departures). These can't be expressed as simple dotted paths.
   - What's unclear: Should these become EXTRACT-stage computations, or should the check definition reference a computation function?
   - Recommendation: Phase 31 should NOT try to eliminate computed mappers. Add a `data_strategy.computation` field that names a function for complex derivations. Migration of computation logic to EXTRACT is a future phase.

4. **patterns.json vs INFERENCE_PATTERN checks**
   - What we know: 19 checks have `signal_type: PATTERN` in checks.json. Separately, `patterns.json` defines 19 composite patterns with explicit trigger conditions. These are related but not identical.
   - What's unclear: Should INFERENCE_PATTERN checks reference their pattern definition from patterns.json, or should the pattern logic be folded into the check definition?
   - Recommendation: Add a `pattern_ref` field to INFERENCE_PATTERN checks that points to the corresponding pattern ID in patterns.json. Don't duplicate pattern logic -- keep patterns.json as the authoritative source for trigger conditions.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/checks.json` -- 388 check definitions, all 18 fields analyzed
- `src/do_uw/stages/analyze/check_engine.py` -- 308 lines, dispatch architecture
- `src/do_uw/stages/analyze/check_mappers.py` -- 478 lines, prefix routing
- `src/do_uw/stages/analyze/check_mappers_phase26.py` -- 403 lines, Phase 26+ routing
- `src/do_uw/stages/analyze/check_field_routing.py` -- 329 lines, 236 field mappings
- `src/do_uw/stages/analyze/check_evaluators.py` -- 227 lines, threshold evaluation
- `src/do_uw/stages/analyze/check_results.py` -- 284 lines, CheckResult model + enums
- `src/do_uw/stages/analyze/check_helpers.py` -- 190 lines, shared utilities
- `src/do_uw/knowledge/models.py` -- SQLAlchemy ORM schema
- `src/do_uw/knowledge/store.py` -- 366 lines, query API
- `src/do_uw/knowledge/store_bulk.py` -- 274 lines, write operations
- `src/do_uw/knowledge/lifecycle.py` -- Check lifecycle state machine
- `src/do_uw/knowledge/compat_loader.py` -- BackwardCompatLoader bridge
- `src/do_uw/stages/render/sections/sect7_coverage_gaps.py` -- Gap rendering

### Secondary (MEDIUM confidence)
- `src/do_uw/config/check_classification.json` -- Prefix-level classification defaults
- `src/do_uw/brain/patterns.json` -- 19 composite pattern definitions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No new dependencies, all tools already in project
- Architecture: HIGH -- Based on exhaustive analysis of current codebase (10+ files, all routing paths)
- Content type mapping: HIGH -- Derived from statistical analysis of all 388 checks (category, factors, signal_type distributions)
- Pitfalls: HIGH -- Identified from actual codebase analysis, not hypothetical
- Declarative routing: MEDIUM -- The approach is sound but SourcedValue unwrapping and computed mappers add complexity that needs careful handling
- Enrichment effort: MEDIUM -- Automated classification is straightforward; rationale quality depends on D&O domain expertise

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (stable domain -- no external dependency changes expected)
