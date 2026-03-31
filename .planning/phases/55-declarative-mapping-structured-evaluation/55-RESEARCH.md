# Phase 55: Declarative Mapping & Structured Evaluation - Research

**Researched:** 2026-03-01
**Domain:** Declarative data resolution, operator-based threshold evaluation, shadow evaluation parity testing
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Prefix migration target**: FIN.LIQ (5 signals) is the first full end-to-end migration -- simplest prefix, already has V2 YAML (FIN.LIQ.position), mostly DIRECT_LOOKUP from financials.liquidity. Populate V2 YAML broadly across many signals (scripted), but only flip schema_version: 2 on signals that pass shadow evaluation.
- **Shadow evaluation design**: Compare status AND threshold level (TRIGGERED/CLEAR/SKIPPED + RED/YELLOW/CLEAR). Value differences acceptable if status+level match. Any 3 tickers with zero discrepancy validates. Discrepancies logged to console AND DuckDB (brain_shadow_evaluations table). Shadow evaluation runs permanently -- never auto-disabled.
- **COMPUTED function design**: Central `COMPUTED_FUNCTIONS` dict in `field_registry.py` maps YAML function names to Python callables. Functions receive pre-resolved arguments. Complex composites (Altman Z, Beneish M) stay as named evaluator dispatch.
- **Legacy cleanup strategy**: FIELD_FOR_CHECK entries removed immediately when a prefix is fully migrated. Rollback: flip `schema_version` back to 1. Migration visibility in `brain status` command.
- **Field registry expansion scope**: Scriptable migration of FIELD_FOR_CHECK entries is acceptable; at Claude's discretion.

### Claude's Discretion
- Whether to migrate additional prefixes beyond FIN.LIQ (based on implementation velocity)
- Field registry expansion scope -- full 371-entry migration vs. on-demand
- Where COMPUTED function implementations live (dedicated file vs. field_registry.py)
- Exact DuckDB shadow evaluation table schema

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MAP-01 | Declarative mapper resolves signal data from field registry paths -- DIRECT_LOOKUP via dotted paths, COMPUTED via named function dispatch | Architecture Patterns (declarative_mapper.py), Code Examples (resolve_field), SourcedValue traversal analysis, COMPUTED_FUNCTIONS dict design |
| MAP-02 | SourcedValue-aware path resolver -- auto-unwrap SourcedValue at each step, propagate source/confidence, dual roots (extracted.*, company.*) | Architecture Patterns (SourcedValue traversal), Code Examples (resolve_path), SourcedValue model analysis (value/source/confidence/as_of) |
| MAP-03 | Legacy fallback preserved -- signals without V2 acquisition paths use existing mapper chain | Architecture Patterns (dispatch integration), signal_engine.py dispatch analysis showing V2 stub fallthrough |
| MAP-04 | At least one full prefix migrated -- FIN.LIQ.* uses declarative mapping exclusively, FIELD_FOR_CHECK entries removed | FIN.LIQ signal inventory (5 signals), field registry gap analysis (2 missing: cash_ratio, cash_burn_months), FIELD_FOR_CHECK removal plan |
| EVAL-01 | Structured evaluator handles operator-based thresholds -- {op, value} with operators >, <, >=, <=, ==, !=, between, contains | Architecture Patterns (structured_evaluator.py), Code Examples (evaluate_structured), legacy try_numeric_compare behavior analysis |
| EVAL-02 | Formula evaluation for single-field and multi-field signals | Architecture Patterns (formula resolution), field registry formula -> field_key mapping, composite dispatch design |
| EVAL-03 | Edge cases handled -- None->SKIPPED, empty list->0, "N/A"->missing | Common Pitfalls (edge case catalog), legacy make_skipped behavior analysis |
| EVAL-04 | Legacy fallback preserved -- signals without V2 evaluation use existing check_evaluators.py | Architecture Patterns (dispatch integration), _evaluate_v2_stub replacement design |
| EVAL-05 | Shadow evaluation mode -- both paths run, discrepancies logged, switch at zero discrepancy across 3 tickers | Architecture Patterns (shadow evaluation), DuckDB table schema, brain status integration |
</phase_requirements>

## Summary

Phase 55 replaces the `_evaluate_v2_stub()` in `signal_engine.py` with a real declarative mapper and structured evaluator. The existing infrastructure is well-prepared: Phase 54 created the V2 schema models (AcquisitionSpec, EvaluationSpec, PresentationSpec), the field registry (15 entries in `brain/field_registry.yaml`), the dispatch hook (`signal_engine.py:107-118`), and 15 V2 signals across 5 prefixes. Phase 55 builds the two new modules that make V2 signals actually evaluate declaratively rather than falling through to legacy.

The scope is three interconnected deliverables: (1) `declarative_mapper.py` that resolves data from field registry paths with SourcedValue-aware traversal, (2) `structured_evaluator.py` that evaluates using `{op, value}` operators instead of parsing English threshold text, and (3) shadow evaluation that runs both paths permanently and logs discrepancies. The FIN.LIQ prefix (5 signals) is the end-to-end migration target.

Key technical challenges: SourcedValue unwrapping at each traversal step (the `liquidity` field is `SourcedValue[dict[str, float | None]]` -- must unwrap the SourcedValue then extract the dict key), COMPUTED function dispatch with pre-resolved arguments, and ensuring the structured evaluator produces identical status+level to the legacy `try_numeric_compare` for every signal.

**Primary recommendation:** Build `declarative_mapper.py` and `structured_evaluator.py` as new files in `stages/analyze/`. Wire the mapper into the V2 dispatch path before `map_signal_data()`. Wire the evaluator into `_evaluate_v2_stub()` replacement. Add shadow evaluation logging inline in the dispatch path. Migrate FIN.LIQ.* fully, then expand field registry and V2 YAML broadly via script.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | (already installed) | FieldRegistryEntry model, signal schema validation | Already the system's validation framework |
| PyYAML CSafeLoader | (already installed) | Reading field_registry.yaml at runtime | Already used; 65ms for 400 signals |
| DuckDB | (already installed) | Shadow evaluation results table (brain_shadow_evaluations) | Already used for all brain history tables |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (already installed) | Unit tests for mapper, evaluator, shadow eval, regression | All phase deliverables |
| Rich | (already installed) | CLI output for migration stats in `brain status` | Already used in cli_brain.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom path resolver | attrs-based traversal | Pydantic models already support `getattr()` traversal; no need for external library |
| Expression parser for formulas | simpleeval / asteval | Locked decision: simple formulas resolve via field registry, composites stay procedural. No expression parser needed |
| Separate shadow eval service | Inline in dispatch | Inline is simpler, lower overhead, and matches the existing dispatch pattern. Shadow eval adds ~1ms per signal |

**Installation:** No new dependencies needed.

## Architecture Patterns

### Recommended New File Structure

```
src/do_uw/stages/analyze/
  declarative_mapper.py     # NEW: resolve_field(), resolve_path(), COMPUTED dispatch
  structured_evaluator.py   # NEW: evaluate_v2(), operator comparison logic
  signal_engine.py          # MODIFY: replace _evaluate_v2_stub with real dispatch + shadow eval
  signal_field_routing.py   # MODIFY: remove FIN.LIQ.* entries from FIELD_FOR_CHECK

src/do_uw/brain/
  field_registry.py         # MODIFY: add COMPUTED_FUNCTIONS dict
  field_registry.yaml       # MODIFY: add cash_ratio, cash_burn_months entries
  brain_schema.py           # MODIFY: add brain_shadow_evaluations DDL

src/do_uw/brain/signals/fin/
  balance.yaml              # MODIFY: add V2 sections to 4 remaining FIN.LIQ signals

tests/stages/analyze/
  test_declarative_mapper.py    # EXISTING + EXPAND: add V2 resolution tests
  test_structured_evaluator.py  # NEW: operator evaluation tests
  test_shadow_evaluation.py     # NEW: parity + logging tests

tests/brain/
  test_v2_migration.py          # EXISTING + EXPAND: add FIN.LIQ migration regression
  test_field_registry.py        # EXISTING + EXPAND: add new field entries
```

### Pattern 1: Declarative Path Resolution (MAP-01, MAP-02)

**What:** `resolve_field()` takes a field_key, looks it up in the field registry, and resolves the value from either ExtractedData or CompanyProfile. For DIRECT_LOOKUP fields, it traverses the dotted path. For COMPUTED fields, it resolves all argument paths first, then calls the named function.

**When to use:** Every V2 signal's data mapping step (replaces the section-specific mapper functions for V2 signals).

**Why this design:**
- The existing mapper functions (`_map_financial_fields`, `_map_market_fields`, etc.) each build a large dict of ~30 fields, then `narrow_result()` picks one. This is wasteful -- V2 needs only the specific field(s) referenced in `evaluation.formula`.
- The field registry already maps field_key -> dotted path. The mapper just needs to traverse that path.

**Integration point:** `signal_engine.py:103` -- before calling `map_signal_data()`, check if the signal has V2 acquisition/evaluation. If so, call `resolve_field()` instead, producing a single-entry dict `{field_key: resolved_value}`.

**Example:**
```python
# declarative_mapper.py

def resolve_field(
    field_key: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> tuple[Any, str, str]:
    """Resolve a field_key to its value, source, and confidence.

    Returns:
        (value, source, confidence) tuple.
        value is None if field not found or data missing.
    """
    entry = get_field_entry(field_key)
    if entry is None:
        return None, "", ""

    if entry.type == "DIRECT_LOOKUP":
        return _resolve_direct_lookup(entry, extracted, company)
    elif entry.type == "COMPUTED":
        return _resolve_computed(entry, extracted, company)
    return None, "", ""


def _resolve_direct_lookup(
    entry: FieldRegistryEntry,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> tuple[Any, str, str]:
    """Traverse dotted path, unwrapping SourcedValue at each step."""
    path = entry.path  # e.g., "extracted.financials.liquidity"
    root_name, *segments = path.split(".")

    # Select root object
    if root_name == "extracted":
        obj = extracted
    elif root_name == "company":
        obj = company
    else:
        return None, "", ""

    source = ""
    confidence = ""

    # Traverse each segment
    for segment in segments:
        if obj is None:
            return None, "", ""
        # Check if current obj is a SourcedValue -- unwrap
        if hasattr(obj, "value") and hasattr(obj, "source") and hasattr(obj, "confidence"):
            source = obj.source
            confidence = str(obj.confidence)
            obj = obj.value
        obj = getattr(obj, segment, None)

    # Final unwrap if terminal is SourcedValue
    if obj is not None and hasattr(obj, "value") and hasattr(obj, "source"):
        source = obj.source
        confidence = str(obj.confidence)
        obj = obj.value

    # Extract sub-key from dict if specified
    if entry.key and isinstance(obj, dict):
        obj = obj.get(entry.key)

    return obj, source, confidence
```

**Critical detail -- SourcedValue detection:** Cannot use `isinstance(obj, SourcedValue)` because `SourcedValue` is generic and Pydantic models don't support `isinstance` checks with generics well at runtime. Instead, use duck-typing: check for `value`, `source`, and `confidence` attributes. This matches the existing `_safe_sourced()` pattern in `signal_mappers.py:27`.

### Pattern 2: COMPUTED Function Dispatch (MAP-01)

**What:** COMPUTED fields map function names to Python callables. The mapper resolves all arg paths first, then passes resolved values to the function.

**Design (locked):** Central `COMPUTED_FUNCTIONS` dict in `field_registry.py`.

```python
# field_registry.py additions

from typing import Any, Callable

COMPUTED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "count_items": lambda items: len(items) if items else 0,
    "count_restatements": lambda restatements: len(restatements) if restatements else 0,
    "count_active_scas": _count_active_scas,
    "sum_contingent_liabilities": _sum_contingent_liabilities,
    "compute_board_independence_pct": _compute_board_independence,
    "resolve_say_on_pay_pct": _resolve_say_on_pay,
    "compute_customer_concentration": _compute_customer_conc,
}
```

**Where implementations live:** Recommend a dedicated `field_registry_functions.py` (~200 lines) to keep `field_registry.py` focused on the registry loader. The dict lives in `field_registry.py` and imports from `field_registry_functions.py`. This keeps `field_registry.py` under 200 lines (currently 132).

**Argument resolution:** Each arg path in the YAML is resolved using `_resolve_direct_lookup()` (same path traversal, but without the `key` extraction step -- the function receives the raw resolved value).

```python
def _resolve_computed(
    entry: FieldRegistryEntry,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> tuple[Any, str, str]:
    """Resolve COMPUTED field by calling named function with resolved args."""
    func = COMPUTED_FUNCTIONS.get(entry.function)
    if func is None:
        logger.warning("Unknown computed function: %s", entry.function)
        return None, "", ""

    resolved_args = []
    source = ""
    confidence = ""
    for arg_path in entry.args:
        val, src, conf = resolve_path(arg_path, extracted, company)
        resolved_args.append(val)
        if src:
            source = src  # Last non-empty source wins
        if conf:
            confidence = conf

    try:
        result = func(*resolved_args)
    except Exception:
        logger.exception("Computed function %s failed", entry.function)
        return None, "", ""

    return result, source, confidence
```

### Pattern 3: Structured Threshold Evaluation (EVAL-01, EVAL-02)

**What:** `evaluate_v2()` takes a resolved value and the signal's `evaluation.thresholds` list, applies operator comparisons in order (RED first), and returns status + threshold_level.

**Key behavior to match:** The legacy `try_numeric_compare()` in `signal_helpers.py` parses English text like `"<1.0 current ratio (inadequate liquidity)"` using regex to extract `<` and `1.0`, then compares. The V2 evaluator uses the same logic but with structured `{op: "<", value: 1.0, label: "RED"}` -- no regex needed.

**Threshold ordering convention (from Phase 54):** RED before YELLOW in `evaluation.thresholds`. The evaluator checks thresholds in order and returns the first match.

```python
# structured_evaluator.py

def evaluate_v2(
    value: Any,
    thresholds: list[dict[str, Any]],
    signal_id: str,
    signal_name: str,
    sig: dict[str, Any],
) -> SignalResult:
    """Evaluate a V2 signal using structured thresholds.

    Checks thresholds in order (RED first). Returns first match.
    If no threshold matches, returns CLEAR.
    """
    if value is None:
        return make_skipped(sig, {})

    try:
        numeric_val = float(value)
    except (ValueError, TypeError):
        # Non-numeric value -- cannot compare with structured thresholds
        return _handle_qualitative(value, sig)

    for threshold in thresholds:
        op = threshold["op"]
        thresh_val = threshold["value"]
        label = threshold["label"]

        if _compare(numeric_val, op, thresh_val):
            status = SignalStatus.TRIGGERED
            level = label.lower()  # "RED" -> "red"
            evidence = f"Value {numeric_val} {op} {thresh_val} ({label})"
            return SignalResult(
                signal_id=signal_id,
                signal_name=signal_name,
                status=status,
                value=coerce_value(value),
                threshold_level=level,
                evidence=evidence,
                factors=extract_factors(sig),
                section=sig.get("section", 0),
            )

    # No threshold matched -> CLEAR
    return SignalResult(
        signal_id=signal_id,
        signal_name=signal_name,
        status=SignalStatus.CLEAR,
        value=coerce_value(value),
        threshold_level="clear",
        evidence=f"Value {numeric_val} within thresholds",
        factors=extract_factors(sig),
        section=sig.get("section", 0),
    )


def _compare(value: float, op: str, threshold: float | list[float]) -> bool:
    """Apply comparison operator."""
    if op == "<":
        return value < threshold
    elif op == ">":
        return value > threshold
    elif op == "<=":
        return value <= threshold
    elif op == ">=":
        return value >= threshold
    elif op == "==":
        return value == threshold
    elif op == "!=":
        return value != threshold
    elif op == "between":
        # threshold is [low, high]
        return threshold[0] <= value <= threshold[1]
    elif op == "contains":
        return str(threshold) in str(value)
    return False
```

### Pattern 4: Shadow Evaluation (EVAL-05)

**What:** In the V2 dispatch path, run BOTH the V2 evaluator AND the legacy evaluator. Compare results. Log discrepancies. The V2 result is used only when shadow evaluation has shown zero discrepancies.

**Integration point:** Replace `_evaluate_v2_stub()` with a function that:
1. Runs the V2 declarative mapper + structured evaluator
2. Runs the legacy mapper + evaluator
3. Compares status + threshold_level
4. Logs discrepancy if mismatch
5. Returns the legacy result (until shadow eval is clean for the signal)

**When to return V2 vs legacy:** Per the locked decision, shadow evaluation runs permanently. However, the "active" result should be:
- Legacy result by default
- V2 result ONLY for signals in fully-migrated prefixes (schema_version=2 AND V2 sections populated AND FIELD_FOR_CHECK entries removed)
- The switch is implicit: once FIELD_FOR_CHECK entries are removed for a prefix, the legacy path produces different (worse) results, so V2 must be the primary

**DuckDB table schema:**
```sql
CREATE TABLE IF NOT EXISTS brain_shadow_evaluations (
    run_id VARCHAR NOT NULL,
    signal_id VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    v1_status VARCHAR NOT NULL,
    v1_threshold_level VARCHAR,
    v1_value VARCHAR,
    v2_status VARCHAR NOT NULL,
    v2_threshold_level VARCHAR,
    v2_value VARCHAR,
    is_match BOOLEAN NOT NULL,
    discrepancy_detail TEXT,
    evaluated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (run_id, signal_id)
);
CREATE INDEX IF NOT EXISTS idx_shadow_signal ON brain_shadow_evaluations(signal_id);
CREATE INDEX IF NOT EXISTS idx_shadow_match ON brain_shadow_evaluations(is_match);
```

### Pattern 5: V2 Dispatch Flow (end-to-end)

**Current flow (Phase 54):**
```
signal_engine.execute_signals()
  -> for each signal:
    -> map_signal_data(signal_id, sig, extracted, company)  [legacy mapper]
    -> if schema_version >= 2:
      -> _evaluate_v2_stub(sig, data) -> None  [always falls through]
    -> evaluate_signal(sig, data)  [legacy evaluator]
```

**Phase 55 flow:**
```
signal_engine.execute_signals()
  -> for each signal:
    -> if schema_version >= 2 AND evaluation section present:
      -> v2_data = declarative_mapper.map_v2_signal(sig, extracted, company)
      -> v2_result = structured_evaluator.evaluate_v2(v2_data, sig)
      -> legacy_data = map_signal_data(signal_id, sig, extracted, company)
      -> legacy_result = evaluate_signal(sig, legacy_data)
      -> shadow_compare(v2_result, legacy_result, signal_id)  [log to DuckDB]
      -> return v2_result  (for migrated prefixes where FIELD_FOR_CHECK removed)
      -> return legacy_result  (for signals still in shadow mode)
    -> else:  [V1 signals]
      -> map_signal_data(signal_id, sig, extracted, company)
      -> evaluate_signal(sig, data)
```

### Anti-Patterns to Avoid
- **Building a general expression parser:** Locked decision says simple formulas resolve via field registry, composites stay procedural. Do not build `eval()` or expression tree parsing.
- **Modifying legacy mapper functions:** The existing `_map_financial_fields()`, `_map_market_fields()` etc. must remain unchanged. V2 mapper is a parallel path, not a modification.
- **Auto-disabling shadow evaluation:** Locked decision: shadow eval runs permanently. No code to detect "clean" runs and disable it.
- **Bulk FIELD_FOR_CHECK deletion before shadow validation:** Only remove entries for a prefix AFTER shadow evaluation confirms zero discrepancies across 3 ticker runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path traversal | Custom string splitting + dict walking | `getattr()` chain on Pydantic models | Pydantic models support attribute access; dict-style access is fragile |
| SourcedValue detection | `isinstance(obj, SourcedValue[T])` | Duck-typing: `hasattr(obj, "value") and hasattr(obj, "source")` | Generic isinstance fails at runtime with Pydantic generics |
| Threshold comparison | Regex parsing of structured thresholds | Direct operator dispatch (`_compare()` function) | V2 thresholds are already structured -- regex would be going backward |
| Shadow eval storage | File-based logging | DuckDB `brain_shadow_evaluations` table | Existing brain history infrastructure uses DuckDB; consistent query interface |
| Complex formula eval | Custom expression parser (eval/ast) | Named function dispatch via `COMPUTED_FUNCTIONS` dict | Locked decision: composites stay procedural |

**Key insight:** Phase 55's value comes from REPLACING parsing with structure. The legacy path parses English text with regex (`try_numeric_compare`). The V2 path uses structured data directly. Any design that introduces new parsing is going in the wrong direction.

## Common Pitfalls

### Pitfall 1: SourcedValue Wrapping Inconsistency
**What goes wrong:** Some fields are `SourcedValue[dict[str, float]]` (liquidity, leverage), some are `SourcedValue[float]` (decline_from_high), some are plain `float` (pe_ratio via `getattr`), and some are `None` at runtime despite being typed as non-optional.
**Why it happens:** The Pydantic model types and the actual runtime values diverge when data is missing or partially extracted.
**How to avoid:** The path resolver must handle ALL of: SourcedValue wrapping a dict (unwrap SV then get key), SourcedValue wrapping a scalar (unwrap SV), plain scalar (no unwrap needed), None at any traversal step (return None immediately).
**Warning signs:** Tests pass with mock data but fail on real pipeline output. Always test with at least one real `state.json` from a previous run.

### Pitfall 2: Threshold Level Case Mismatch
**What goes wrong:** V2 structured thresholds use `label: "RED"` (uppercase). Legacy SignalResult uses `threshold_level: "red"` (lowercase). Shadow evaluation reports false discrepancies.
**Why it happens:** Phase 54 defined `label: Literal["RED", "YELLOW", "CLEAR"]` (uppercase). Legacy uses lowercase.
**How to avoid:** Normalize in the structured evaluator: `level = label.lower()`. Normalize in shadow comparison: compare `v2_level.lower() == legacy_level.lower()`.
**Warning signs:** Shadow eval shows 100% discrepancy rate on threshold_level while status matches.

### Pitfall 3: FIN.LIQ.cash_burn Qualitative Value
**What goes wrong:** `cash_burn_months` returns `"Profitable (OCF positive)"` (a string) for profitable companies, not a numeric value. Structured evaluator tries `float()` and fails.
**Why it happens:** The legacy mapper in `_map_financial_fields()` (line 354) explicitly sets this string when OCF is positive. The signal's English threshold says "Runway <12 months" -- a numeric check that only applies to cash-burning companies.
**How to avoid:** The structured evaluator must handle the "qualitative clear" case: if `float()` conversion fails on a non-None value, check for clear_condition patterns. For cash_burn, the string value itself means CLEAR. Alternatively, mark FIN.LIQ.cash_burn as COMPUTED with a function that returns numeric months or None.
**Warning signs:** FIN.LIQ.cash_burn SKIPS for profitable companies (which should be CLEAR or INFO).

### Pitfall 4: Shadow Evaluation Double-Mapping Overhead
**What goes wrong:** Running both V2 mapper AND legacy mapper for every V2 signal doubles the data resolution work per signal.
**Why it happens:** Shadow evaluation requires both paths to produce results for comparison.
**How to avoid:** Accept the overhead -- it's ~1ms per signal, negligible vs. the 2-3 minute pipeline runtime. The legacy mapper builds a full dict (~30 fields) but `narrow_result()` picks one. The V2 mapper resolves exactly one field. Combined overhead is minimal.
**Warning signs:** None expected. This pitfall is more about premature optimization anxiety than actual performance issues.

### Pitfall 5: FIELD_FOR_CHECK Removal Before Shadow Validation
**What goes wrong:** Removing FIELD_FOR_CHECK entries for FIN.LIQ.* before shadow eval confirms parity causes the legacy path to produce wrong results (falls back to full dict, `first_data_value()` grabs wrong field).
**Why it happens:** Eager cleanup breaks the safety net.
**How to avoid:** Strict ordering: (1) build V2 mapper+evaluator, (2) run shadow eval on 3 tickers, (3) confirm zero discrepancies, (4) THEN remove FIELD_FOR_CHECK entries. Remove in a separate commit so rollback is easy.
**Warning signs:** Shadow eval shows discrepancies because legacy path is using wrong field after premature FIELD_FOR_CHECK removal.

### Pitfall 6: Missing `_apply_classification_metadata` and `_apply_traceability` on V2 Results
**What goes wrong:** V2 evaluator returns a SignalResult that is missing classification metadata (category, signal_type, hazard_or_signal, plaintiff_lenses) and traceability chain (trace_data_source, trace_extraction, etc.). Downstream rendering breaks or shows empty fields.
**Why it happens:** The legacy path calls `_apply_classification_metadata()` and `_apply_traceability()` in `evaluate_signal()`. The V2 path must do the same.
**How to avoid:** After V2 evaluation produces a SignalResult, call the same `_apply_classification_metadata()` and `_apply_traceability()` functions on it. These functions are already importable from `signal_engine.py`.
**Warning signs:** V2 results have empty `trace_*` fields, empty `plaintiff_lenses`, empty `category`.

## Code Examples

### Example 1: Complete FIN.LIQ.position V2 Resolution

```python
# Input: FIN.LIQ.position signal with evaluation.formula = "current_ratio"

# Step 1: Look up "current_ratio" in field registry
# -> FieldRegistryEntry(type=DIRECT_LOOKUP, path="extracted.financials.liquidity", key="current_ratio")

# Step 2: Resolve path "extracted.financials.liquidity"
# extracted.financials -> ExtractedFinancials instance
# ExtractedFinancials.liquidity -> SourcedValue[dict[str, float | None]]
#   value = {"current_ratio": 1.48, "quick_ratio": 0.95, "cash_ratio": 0.32}
#   source = "SEC-10Q-2025-11-04:CIK0000091142"
#   confidence = "HIGH"

# Step 3: Unwrap SourcedValue -> dict
# Extract key "current_ratio" from dict -> 1.48

# Step 4: Evaluate 1.48 against thresholds:
#   - op="<", value=1.0, label="RED" -> 1.48 < 1.0? No
#   - op="<", value=1.5, label="YELLOW" -> 1.48 < 1.5? Yes -> TRIGGERED, yellow

# Result: SignalResult(
#   signal_id="FIN.LIQ.position",
#   status=TRIGGERED,
#   threshold_level="yellow",
#   value=1.48,
#   evidence="Value 1.48 < 1.5 (YELLOW)",
#   source="SEC-10Q-2025-11-04:CIK0000091142",
#   confidence="HIGH",
# )
```

### Example 2: Shadow Evaluation Comparison

```python
# In signal_engine.py, replacing _evaluate_v2_stub:

def _evaluate_v2_signal(
    sig: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
    legacy_data: dict[str, Any],
    run_id: str,
    ticker: str,
) -> SignalResult:
    """Evaluate V2 signal with shadow comparison against legacy."""
    from do_uw.stages.analyze.declarative_mapper import map_v2_signal
    from do_uw.stages.analyze.structured_evaluator import evaluate_v2

    signal_id = sig.get("id", "UNKNOWN")
    evaluation = sig.get("evaluation", {})

    # V2 path
    v2_value, v2_source, v2_confidence = map_v2_signal(sig, extracted, company)
    v2_result = evaluate_v2(v2_value, evaluation, signal_id, sig)

    # Legacy path
    legacy_result = evaluate_signal(sig, legacy_data)

    # Shadow comparison
    is_match = (
        v2_result.status == legacy_result.status
        and v2_result.threshold_level.lower() == legacy_result.threshold_level.lower()
    )

    if not is_match:
        logger.warning(
            "Shadow eval mismatch for %s: V2=%s/%s Legacy=%s/%s",
            signal_id,
            v2_result.status.value, v2_result.threshold_level,
            legacy_result.status.value, legacy_result.threshold_level,
        )

    # Log to DuckDB (async-safe, fire-and-forget)
    _log_shadow_evaluation(
        run_id, signal_id, ticker,
        legacy_result, v2_result, is_match,
    )

    # Return V2 result for fully-migrated prefixes, legacy otherwise
    return v2_result  # or legacy_result during shadow phase
```

### Example 3: FIN.LIQ.cash_burn V2 YAML Addition

```yaml
# V2 additions for FIN.LIQ.cash_burn:
schema_version: 2
acquisition:
  sources:
    - type: SEC_10Q
      fields:
        - extracted.financials.earnings_quality
      fallback_to: SEC_10K
    - type: SEC_10K
      fields:
        - extracted.financials.earnings_quality
evaluation:
  formula: cash_burn_months
  thresholds:
    - op: "<"
      value: 12
      label: RED
    - op: "<"
      value: 18
      label: YELLOW
  clear_conditions:
    - type: qualitative_value
      pattern: "Profitable"
      result: CLEAR
  window_years: 1
presentation:
  detail_levels:
    - level: glance
      template: "Cash runway: {value}"
    - level: standard
      template: "Cash burn ({cash_burn_months} months) — {status_label}"
  context_templates:
    TRIGGERED: "Cash runway concern: {value} months remaining"
    CLEAR: "Company is cash flow positive"
```

Note: The `clear_conditions` pattern is needed for qualitative-clear signals (EVAL-03). When the mapper returns a string like "Profitable (OCF positive)" instead of a number, the evaluator checks `clear_conditions` before attempting numeric comparison.

### Example 4: Field Registry Expansion for FIN.LIQ

```yaml
# Additions to brain/field_registry.yaml for FIN.LIQ migration:

  cash_ratio:
    type: DIRECT_LOOKUP
    path: extracted.financials.liquidity
    key: cash_ratio
    description: Cash / current liabilities ratio (from SourcedValue dict)

  cash_burn_months:
    type: COMPUTED
    function: compute_cash_burn_months
    args:
      - extracted.financials.earnings_quality
    description: Cash runway in months (None if OCF positive, numeric if burning)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| English threshold text + regex parsing | Structured `{op, value}` operators | Phase 55 (V2 signals) | Eliminates regex parsing errors, enables machine reasoning about thresholds |
| Section-specific mapper functions (500+ lines) | Field registry dotted-path resolution | Phase 55 (V2 signals) | Single field resolved instead of 30-field dict; declarative instead of procedural |
| 371-entry FIELD_FOR_CHECK Python dict | Field registry YAML (Phase 54: 15 entries) | Phase 54/55 migration | YAML is editable without code changes; self-documenting with descriptions |
| Implicit threshold logic in Python code | Explicit threshold definitions in signal YAML | Phase 54/55 | Underwriters can see and reason about thresholds without reading Python |

## Open Questions

1. **clear_conditions schema for qualitative-clear signals**
   - What we know: FIN.LIQ.cash_burn returns "Profitable (OCF positive)" which is a qualitative CLEAR, not a threshold breach. The legacy evaluator handles this in `_check_clear_signal()`.
   - What's unclear: Should `clear_conditions` be a formal part of EvaluationSpec? Or handled as a special case in the structured evaluator?
   - Recommendation: Add `clear_conditions` as an optional field on EvaluationSpec (list of dicts with `type`, `pattern`, `result`). This keeps the signal YAML self-describing. But since this needs a Pydantic schema change on EvaluationSpec (Phase 54 model), evaluate whether it's simpler to just handle it in the evaluator code with the existing `_check_clear_signal()` patterns. **Claude's discretion per CONTEXT.md.**

2. **Field registry expansion scope**
   - What we know: Currently 15 entries. FIN.LIQ needs 2 more (cash_ratio, cash_burn_months). Full FIELD_FOR_CHECK is 263 entries.
   - What's unclear: How many to migrate in this phase vs. leave for future phases?
   - Recommendation: Migrate the fields needed for FIN.LIQ (2 entries). Optionally script-migrate 20-30 additional DIRECT_LOOKUP fields that have simple `extracted.*` paths. Leave COMPUTED fields for on-demand migration. **Claude's discretion per CONTEXT.md.**

3. **Shadow evaluation during pipeline run vs. separate command**
   - What we know: Locked decision says shadow eval runs permanently inline in the dispatch path.
   - What's unclear: Should shadow eval results be aggregated per-run and summarized at the end of `brain status`? Or just logged individually?
   - Recommendation: Log individually per signal to DuckDB. Add a summary query to `brain status` that shows: total shadow evals, match rate, top discrepant signals. This keeps logging simple and analysis flexible.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already installed) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/stages/analyze/test_declarative_mapper.py tests/stages/analyze/test_structured_evaluator.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | Declarative mapper resolves DIRECT_LOOKUP and COMPUTED fields | unit | `uv run pytest tests/stages/analyze/test_declarative_mapper.py -x` | Partial (exists for narrow_result, needs expansion for V2 resolution) |
| MAP-02 | SourcedValue-aware path resolver with confidence propagation | unit | `uv run pytest tests/stages/analyze/test_declarative_mapper.py::TestSourcedValueTraversal -x` | Wave 0 |
| MAP-03 | Legacy fallback preserved for V1 signals | integration | `uv run pytest tests/brain/test_v2_dispatch.py -x` | Exists (Phase 54 tests) |
| MAP-04 | FIN.LIQ prefix fully migrated with identical results | integration | `uv run pytest tests/brain/test_v2_migration.py -x` | Partial (needs FIN.LIQ migration tests) |
| EVAL-01 | Structured evaluator with operator-based thresholds | unit | `uv run pytest tests/stages/analyze/test_structured_evaluator.py -x` | Wave 0 |
| EVAL-02 | Formula evaluation (field reference, COMPUTED dispatch) | unit | `uv run pytest tests/stages/analyze/test_structured_evaluator.py::TestFormulaEvaluation -x` | Wave 0 |
| EVAL-03 | Edge cases: None->SKIPPED, empty list->0, N/A->missing | unit | `uv run pytest tests/stages/analyze/test_structured_evaluator.py::TestEdgeCases -x` | Wave 0 |
| EVAL-04 | Legacy fallback preserved for V1 signals | integration | `uv run pytest tests/brain/test_v2_dispatch.py -x` | Exists (Phase 54 tests) |
| EVAL-05 | Shadow evaluation with DuckDB logging | integration | `uv run pytest tests/stages/analyze/test_shadow_evaluation.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/analyze/test_declarative_mapper.py tests/stages/analyze/test_structured_evaluator.py tests/stages/analyze/test_shadow_evaluation.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/analyze/test_structured_evaluator.py` -- covers EVAL-01, EVAL-02, EVAL-03
- [ ] `tests/stages/analyze/test_shadow_evaluation.py` -- covers EVAL-05
- [ ] Expand `tests/stages/analyze/test_declarative_mapper.py` -- covers MAP-01, MAP-02 (SourcedValue traversal)
- [ ] Expand `tests/brain/test_v2_migration.py` -- covers MAP-04 (FIN.LIQ regression)
- [ ] Expand `tests/brain/test_field_registry.py` -- covers new field entries

## Detailed Technical Inventory

### FIN.LIQ Signal Migration Inventory

| Signal ID | field_key | In Registry? | V2 Status | Threshold Type | Clear Condition |
|-----------|-----------|-------------|-----------|----------------|-----------------|
| FIN.LIQ.position | current_ratio | Yes | schema_version=2 | `<1.0` RED, `<1.5` YELLOW | numeric >= 1.5 |
| FIN.LIQ.working_capital | current_ratio | Yes | V1 (needs V2) | `<1.0` RED, `<1.5` YELLOW | numeric >= 1.5 |
| FIN.LIQ.efficiency | cash_ratio | **No** (needs add) | V1 (needs V2) | `<0.2` RED, `<0.5` YELLOW | numeric >= 0.5 |
| FIN.LIQ.trend | current_ratio | Yes | V1 (needs V2) | DETERIORATING pattern | qualitative |
| FIN.LIQ.cash_burn | cash_burn_months | **No** (needs add) | V1 (needs V2) | `<12` RED, `<18` YELLOW | "Profitable" string |

**Migration work per signal:**
1. **FIN.LIQ.position** -- Already V2. Just needs declarative mapper + evaluator to pick it up. No YAML changes needed.
2. **FIN.LIQ.working_capital** -- Same field_key (current_ratio) as position. Add V2 sections to YAML. Uses same thresholds.
3. **FIN.LIQ.efficiency** -- Add `cash_ratio` to field registry as DIRECT_LOOKUP (path=extracted.financials.liquidity, key=cash_ratio). Add V2 sections.
4. **FIN.LIQ.trend** -- Uses current_ratio (already in registry). Threshold is qualitative ("DETERIORATING: 3+ quarters declining"). May need INFO-only treatment in V2 or a clear_condition.
5. **FIN.LIQ.cash_burn** -- Add `cash_burn_months` to field registry as COMPUTED (needs a function that checks OCF, returns months or "Profitable" string). Add V2 sections with clear_condition for profitable companies.

### FIELD_FOR_CHECK Entries to Remove (post-validation)

```python
# These 5 entries are removed from FIELD_FOR_CHECK after shadow eval confirms parity:
"FIN.LIQ.position": "current_ratio",
"FIN.LIQ.working_capital": "current_ratio",
"FIN.LIQ.efficiency": "cash_ratio",
"FIN.LIQ.trend": "current_ratio",
"FIN.LIQ.cash_burn": "cash_burn_months",
```

### Existing Reusable Functions

| Function | Location | Reusable For |
|----------|----------|-------------|
| `_safe_sourced(sv)` | signal_mappers.py:27 | Pattern for SourcedValue unwrap (but mapper needs path-based traversal, not field-by-field) |
| `coerce_value(data_value)` | signal_helpers.py:84 | V2 evaluator needs same coercion for SignalResult.value |
| `extract_factors(check)` | signal_helpers.py:26 | V2 evaluator uses same factor extraction |
| `make_skipped(check, data)` | signal_helpers.py:100 | V2 evaluator uses same SKIPPED result builder |
| `first_data_value(data)` | signal_helpers.py:72 | NOT used by V2 (V2 resolves specific field, not first-non-None) |
| `try_numeric_compare()` | signal_helpers.py:150 | NOT used by V2 (replaced by structured comparison) |
| `_check_clear_signal()` | signal_evaluators.py:90 | V2 may reuse for qualitative clear detection |
| `_apply_classification_metadata()` | signal_engine.py:235 | V2 results must go through this |
| `_apply_traceability()` | signal_engine.py:248 | V2 results must go through this |

## Sources

### Primary (HIGH confidence)
- Codebase analysis of all referenced files (signal_engine.py, signal_field_routing.py, signal_mappers.py, signal_evaluators.py, signal_helpers.py, field_registry.py, field_registry.yaml, brain_signal_schema.py, brain_schema.py, cli_brain.py)
- Phase 54 RESEARCH.md, CONTEXT.md, and implementation artifacts (15 V2 signals, dispatch stub, field registry)
- REQUIREMENTS.md (MAP-01 through MAP-04, EVAL-01 through EVAL-05)
- STATE.md (Phase 54 decisions and context)
- MEMORY.md (project conventions, user preferences)

### Secondary (MEDIUM confidence)
- Live runtime verification of FIN.LIQ signal inventory (5 signals confirmed via `load_signals()`)
- Live runtime verification of field registry (15 entries, 2 gaps identified for FIN.LIQ)
- Live runtime verification of FIELD_FOR_CHECK (263 total, 5 for FIN.LIQ)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all libraries already in use
- Architecture: HIGH -- all integration points verified in codebase, patterns follow existing conventions
- Pitfalls: HIGH -- identified from actual code analysis (SourcedValue wrapping, cash_burn qualitative, threshold case mismatch)
- Migration inventory: HIGH -- verified against live runtime data

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable internal architecture, no external dependency concerns)
