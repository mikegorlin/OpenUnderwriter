# Phase 70: Signal Integration & Validation - Research

**Researched:** 2026-03-06 (updated with Two-Tier architecture)
**Domain:** Brain signal system -- YAML signal definitions, field_key routing, evaluation engine, shadow evaluation, Two-Tier data acquisition model, cross-ticker validation
**Confidence:** HIGH

## Summary

Phase 70 wires all new XBRL and forensic data (from Phases 67-69) into the brain signal system, AND implements the Two-Tier data acquisition model decided in STATE.md. This involves four categories of work:

1. **Tier 1 Foundational Signals (NEW):** Create `brain/signals/base/` directory with foundational signal YAML files that declare the complete data acquisition manifest. These use `type: foundational` (a new signal type with `acquisition` blocks but NO `evaluation` blocks). They replace the implicit acquisition manifest currently hardcoded in `orchestrator.py`.

2. **New forensic evaluative signals (SIG-01, SIG-06):** 20-30 new signals in `fin/forensic_xbrl.yaml` covering all forensic module outputs from Phase 69, plus 12 new opportunity signals.

3. **Upgrade/enhance existing signals (SIG-02, SIG-03):** 45 signals upgraded from LLM-sourced to XBRL-sourced field_keys, 28 enhanced with dual data sources.

4. **Reactivation + web search + validation (SIG-04, SIG-05, SIG-07, SIG-08):** Reactivate 15+ broken signals, wire 35 web-search signals, shadow evaluation for all changes, cross-ticker validation.

The Two-Tier model is the architectural cornerstone. Every piece of data becomes traceable to either "it's on the Tier 1 manifest" (a foundational signal declared it) or "signal X requested it" (an evaluative signal's acquisition block). This eliminates orphaned computation and makes the acquisition stage fully brain-declared.

**Primary recommendation:** Work in three sequential waves: (1) Tier 1 foundational signals + new forensic evaluative signals (additive, establishes the manifest), (2) upgrade/enhance existing signals with shadow evaluation (highest regression risk), (3) reactivate broken signals + web search wiring + cross-ticker validation.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIG-01 | 20-30 new forensic signals in `fin/forensic_xbrl.yaml` with field_key mappings | New YAML file, field_key paths to `state.analysis.xbrl_forensics.*`, ForensicMetric model has value/zone/trend/confidence |
| SIG-02 | Upgrade 45 XBRL-replaceable signals to XBRL-sourced field_keys | Update `data_strategy.field_key` in existing YAML files, mappers route to `extracted.financials.statements` |
| SIG-03 | Enhance 28 XBRL-enhanceable signals with dual data sources | XBRL for numeric threshold + LLM for narrative context, update mappers |
| SIG-04 | Shadow evaluation for all signal changes | Extend existing `_log_shadow_evaluation()` pattern, add XBRL vs LLM comparison columns |
| SIG-05 | Reactivate 15+ broken/skipped signals | Wire to newly available XBRL data or web search data |
| SIG-06 | 12 new signal opportunities from audit | Revenue recognition risk, level 3 fair value, pension, operating lease, goodwill, SBC, related party, insider patterns, peer gaps |
| SIG-07 | Cross-ticker validation on 5 tickers with baseline updates | Re-run AAPL, RPM, SNA, V, WWD; use `scripts/qa_compare.py` + custom signal delta report |
| SIG-08 | Web search tier 2 wiring for 35 qualitative signals | Wire to Brave Search + Exa acquisition; FWRD.WARN.* signals |
</phase_requirements>

## Standard Stack

### Core (All Existing -- No New Dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | installed | Signal YAML loading | Already used by BrainLoader |
| Pydantic v2 | installed | State models, forensic result models | Project standard for all models |
| DuckDB | installed | Shadow evaluation logging, brain DB | Already used for brain_shadow_evaluations table |
| pytest | installed | Cross-ticker validation, regression tests | Project test framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | installed | Lint/format YAML-adjacent Python | All new code |
| httpx | installed | Web search acquisition (SIG-08) | Brave Search / Exa API calls |

**No new dependencies needed.** All tools are already installed and proven in the codebase.

## Architecture Patterns

### Two-Tier Data Acquisition Model (NEW -- Key Decision from STATE.md)

```
Tier 1 -- Foundational Signals (brain/signals/base/)
  |  type: foundational
  |  Has acquisition blocks, NO evaluation blocks
  |  Declares what data to pull for EVERY company
  |
  v
AcquisitionOrchestrator reads foundational signals at startup
  |  Builds manifest from foundational signal acquisition blocks
  |  Replaces hardcoded acquisition flow
  |
  v
Tier 2 -- Evaluative Signals (brain/signals/{domain}/)
  |  type: evaluate (existing 400+ signals)
  |  References Tier 1 data via field_key
  |  If needs ADDITIONAL data, declares in own acquisition block
  |
  v
Signal Engine evaluates Tier 2 only (foundational signals skipped)
```

### Signal System Architecture (Existing -- Follow)

```
brain/signals/base/*.yaml              -- NEW: Foundational signals (Tier 1)
brain/signals/{domain}/{file}.yaml     -- Evaluative signals (Tier 2, 400 total)
       |
brain/field_registry.yaml              -- V2 field_key -> state path mapping
       |
signal_engine.py                       -- execute_signals(): main loop
  |-- signal_mappers.py                -- Prefix routing (BIZ/FIN/GOV/LIT/STOCK)
  |-- signal_mappers_analytical.py     -- FIN.TEMPORAL/FORENSIC/QUALITY, EXEC, NLP
  |-- signal_mappers_sections.py       -- GOV, LIT section mappers
  |-- signal_mappers_forward.py        -- FWRD mappers
  |-- signal_field_routing.py          -- FIELD_FOR_CHECK dict + narrow_result()
  |-- signal_evaluators.py            -- Threshold evaluation functions
  |-- declarative_mapper.py            -- V2 resolve_path/resolve_field
  |-- structured_evaluator.py          -- V2 evaluate_v2()
  |-- signal_helpers.py                -- Shared utilities
```

### Data Routing Resolution Order (CRITICAL)
1. `data_strategy.field_key` from signal YAML definition (highest priority)
2. V2 `evaluation.formula` -> `field_registry.yaml` lookup (V2 signals)
3. `FIELD_FOR_CHECK` dict in `signal_field_routing.py` (legacy fallback)
4. Full mapper dict returned as-is (last resort)

### Pattern 1: Foundational Signal YAML (NEW)
**What:** A signal with `type: foundational` that declares data acquisition needs without evaluation
**When:** Tier 1 manifest -- data we always pull for every company
**Example:**
```yaml
# brain/signals/base/xbrl.yaml
- id: BASE.XBRL.balance_sheet
  name: XBRL Balance Sheet Extraction
  type: foundational
  work_type: acquire
  tier: 0
  depth: 1
  threshold:
    type: info
  acquisition:
    sources:
      - type: SEC_10K
        fields:
          - extracted.financials.statements.balance_sheet
      - type: SEC_10Q
        fields:
          - extracted.financials.quarterly_xbrl
    coverage: required
  provenance:
    origin: v3.1_tier1_manifest
    confidence: HIGH
    source_author: system
    added_by: Phase70
  display:
    value_format: text
    source_type: SEC_10K

- id: BASE.XBRL.income_statement
  name: XBRL Income Statement Extraction
  type: foundational
  work_type: acquire
  tier: 0
  depth: 1
  threshold:
    type: info
  acquisition:
    sources:
      - type: SEC_10K
        fields:
          - extracted.financials.statements.income_statement
      - type: SEC_10Q
        fields:
          - extracted.financials.quarterly_xbrl
    coverage: required
  provenance:
    origin: v3.1_tier1_manifest
    confidence: HIGH
    source_author: system
    added_by: Phase70
  display:
    value_format: text
    source_type: SEC_10K
```

### Pattern 2: Forensic Evaluative Signal YAML
**What:** A Tier 2 signal that evaluates forensic results computed from Tier 1 data
**When:** SIG-01, SIG-06 -- new forensic signals referencing Phase 69 outputs
**Example:**
```yaml
# brain/signals/fin/forensic_xbrl.yaml
- id: FIN.FORENSIC.goodwill_impairment_risk
  name: Goodwill Impairment Risk
  work_type: evaluate
  layer: signal
  factors: [F3]
  peril_ids: [P1_SCA]
  chain_roles:
    restatement_to_sca: evidence
  threshold:
    type: tiered
    red: '> 0.50'
    yellow: '> 0.35'
    clear: '<= 0.35'
  tier: 1
  depth: 3
  plaintiff_lenses: [SHAREHOLDERS, REGULATORS]
  data_strategy:
    field_key: forensic_goodwill_to_assets
    primary_source: SEC_10K
  facet: financial_health
  display:
    value_format: percentage
    source_type: SEC_10K
    threshold_context: 'Goodwill as % of total assets; >50% high risk'
  provenance:
    origin: v3.1_xbrl_forensic
    confidence: HIGH
    last_validated: '2026-03-06'
    added_by: Phase70
```

### Pattern 3: Upgrading Existing Signal field_key
**What:** Change an existing signal's `data_strategy.field_key` to point to XBRL-sourced data
**When:** SIG-02 -- replacing 45 LLM-sourced signals
**Example:**
```yaml
# BEFORE (LLM-sourced via financial_health_narrative):
data_strategy:
  field_key: financial_health_narrative
  primary_source: SEC_10Q

# AFTER (XBRL-sourced via extracted.financials.statements):
data_strategy:
  field_key: xbrl_revenue_growth_yoy
  primary_source: SEC_10K
```

### Pattern 4: Shadow Evaluation for Data Source Migration
**What:** Run both old and new field_key mappings, compare results, log to DuckDB
**When:** SIG-04 -- validating every signal change
**Example:** The existing `_evaluate_v2_signal()` in `signal_engine.py` already implements shadow evaluation for V2 signals. For XBRL migration, extend the same pattern:
```python
# In signal_mappers_analytical.py, _map_forensic_check():
def _map_forensic_check(signal_id, extracted):
    result = {}
    # NEW: XBRL-sourced value (primary)
    xbrl_forensics = _get_xbrl_forensics(extracted)
    if xbrl_forensics:
        result["xbrl_value"] = xbrl_forensics.get("balance_sheet", {}).get("goodwill_to_assets", {}).get("value")

    # LEGACY: LLM-sourced value (shadow comparison)
    fin = extracted.financials
    if fin and fin.earnings_quality is not None:
        result["llm_value"] = fin.earnings_quality.value.get("accruals_ratio")

    # Primary value for evaluation
    result["value"] = result.get("xbrl_value") or result.get("llm_value")
    return result
```

### Anti-Patterns to Avoid

- **Changing thresholds preemptively:** Do NOT adjust signal thresholds before shadow evaluation proves they need changing. Run shadow eval, identify actual divergences, then adjust case by case with evidence.
- **Editing mapper code without FIELD_FOR_CHECK or field_key:** Every new signal field_key must be routable. Either add to `signal_field_routing.py` FIELD_FOR_CHECK dict, or use `data_strategy.field_key` in YAML (preferred).
- **Creating new mapper functions for each forensic module:** Extend `_map_forensic_check()` in `signal_mappers_analytical.py`, do not create new mapper files.
- **Modifying signal_engine.py core loop:** The engine is stable. Changes go in mappers and YAML, not the engine loop. Exception: adding foundational signal filtering (skip evaluation for `type: foundational`).
- **Making foundational signals act like evaluative signals:** Foundational signals declare data needs. They do NOT produce TRIGGERED/CLEAR/SKIPPED results. The signal engine must skip them during evaluation.

## Two-Tier Implementation Details

### Complete Tier 1 Manifest

The foundational signals must cover everything currently hardcoded in `orchestrator.py`. Based on analysis of the acquisition flow:

| Foundational Signal ID | Data Category | What It Declares | Maps to Orchestrator Code |
|----------------------|---------------|------------------|---------------------------|
| BASE.XBRL.balance_sheet | XBRL | 10-K/10-Q balance sheet extraction | `_acquire_structured_data` -> SEC client |
| BASE.XBRL.income_statement | XBRL | 10-K/10-Q income statement extraction | SEC client |
| BASE.XBRL.cash_flow | XBRL | 10-K/10-Q cash flow extraction | SEC client |
| BASE.XBRL.quarterly | XBRL | 8 quarters of 10-Q data | Phase 68 quarterly extraction |
| BASE.XBRL.derived | XBRL | Derived ratios (margins, D/E, etc.) | Phase 67 xbrl_derived.py |
| BASE.FILING.10K | Filing | Full 10-K text (Item 1A, 7, 8) | SEC client filing download |
| BASE.FILING.10Q | Filing | Recent 10-Q text | SEC client |
| BASE.FILING.DEF14A | Filing | Proxy statement text | SEC client |
| BASE.FILING.8K | Filing | Recent 8-K events | SEC client |
| BASE.MARKET.stock_price | Market | 1Y and 5Y price/volume history | MarketDataClient |
| BASE.MARKET.institutional | Market | Institutional ownership data | MarketDataClient |
| BASE.MARKET.insider_trading | Market | Form 4 insider transactions | MarketDataClient / SEC |
| BASE.LIT.scac | Litigation | Stanford SCAC database search | LitigationClient |
| BASE.LIT.10k_item3 | Litigation | 10-K Item 3 legal proceedings | LitigationClient |
| BASE.LIT.courtlistener | Litigation | CourtListener federal case search | CourtListenerClient |
| BASE.NEWS.blind_spot_pre | News | Pre-acquisition blind spot sweep | WebSearchClient |
| BASE.NEWS.blind_spot_post | News | Post-acquisition blind spot sweep | WebSearchClient |
| BASE.NEWS.company_news | News | Company news and sentiment | NewsClient |
| BASE.FORENSIC.balance_sheet | Forensic | Balance sheet forensic analysis | Phase 69 forensic modules |
| BASE.FORENSIC.revenue | Forensic | Revenue quality analysis | Phase 69 |
| BASE.FORENSIC.capital_alloc | Forensic | Capital allocation analysis | Phase 69 |
| BASE.FORENSIC.debt_tax | Forensic | Debt/tax analysis | Phase 69 |
| BASE.FORENSIC.beneish | Forensic | Beneish M-Score decomposition | Phase 69 |
| BASE.FORENSIC.earnings | Forensic | Earnings quality dashboard | Phase 69 |
| BASE.FORENSIC.ma | Forensic | M&A forensics | Phase 69 |

**Total: ~25 foundational signals** covering all current acquisition targets.

### How BrainLoader Handles Foundational Signals

The BrainLoader (`brain_unified_loader.py`) uses `signals_dir.glob("**/*.yaml")` to load all YAML files recursively from `brain/signals/`. Adding `brain/signals/base/*.yaml` means foundational signals will be auto-discovered. No change to loader scan logic.

**Required changes:**
1. **BrainSignalEntry schema:** Add `type` field (default `"evaluate"` for backward compat). Values: `"evaluate"` (existing), `"foundational"` (new).
2. **Signal engine filtering:** In `execute_signals()`, skip any signal with `type == "foundational"`. They are loaded but never evaluated.
3. **Manifest builder:** `build_manifest()` in `knowledge/requirements.py` should also read foundational signal acquisition blocks to build the Tier 1 manifest.

### How Evaluative Signals Reference Tier 1 Data

Evaluative signals reference Tier 1 data through the existing data routing system:
- `data_strategy.field_key` points to a state path (e.g., `forensic_goodwill_to_assets`)
- The mapper function (`_map_forensic_check`) resolves that field_key by reading `state.analysis.xbrl_forensics`
- No direct reference to foundational signals; the indirection happens through shared state

The key insight: **forensic computations are Tier 1 data** (declared by BASE.FORENSIC.* foundational signals), not triggered by evaluative signals. The forensic orchestrator runs during ANALYZE regardless of which evaluative signals exist. Evaluative signals simply consume the results.

### Forensic Data Access Path

Phase 69 stores forensic results as `state.analysis.xbrl_forensics` (a `dict[str, Any]` serialized from `XBRLForensics` Pydantic model). The mapper reads this:

```python
def _get_xbrl_forensics(extracted: ExtractedData) -> dict[str, Any] | None:
    """Get XBRL forensic results from analysis state.

    Note: forensic results are on state.analysis, not extracted.
    The signal engine passes state to mappers, so access via
    the analysis attribute.
    """
    # xbrl_forensics is stored as dict on AnalysisResults
    # Access depends on how signal_engine passes state to mappers
    ...
```

**CRITICAL PATH ISSUE:** The current `_map_forensic_check` receives `extracted: ExtractedData`, but forensic results live on `state.analysis.xbrl_forensics` (AnalysisResults), not on ExtractedData. The mapper must receive access to `state.analysis` to read forensic results.

**Resolution options (in order of preference):**
1. **Pass AnalysisResults to mappers** -- the `map_phase26_check` signature already accepts optional `company` param. Add optional `analysis` param.
2. **Store forensic results on ExtractedData** -- violates stage boundaries (ANALYZE results should not be on EXTRACT model).
3. **Use a side-channel** -- global/thread-local state access (least clean).

**Recommendation:** Option 1. Extend `map_phase26_check` signature to accept optional `analysis: AnalysisResults | None`. The signal engine already has access to state and can pass `state.analysis` when calling mappers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Shadow evaluation logging | Custom file-based logging | Existing `brain_shadow_evaluations` DuckDB table | Already has schema, fire-and-forget error handling |
| Signal loading | Custom YAML parser | Existing `BrainLoader` | Handles all YAML files, caching, validation |
| Field routing | New routing system | Existing `narrow_result()` + `data_strategy.field_key` | Proven two-tier resolution system |
| Cross-ticker validation | Manual comparison | Existing `scripts/qa_compare.py` pattern | Already profiles outputs, catches regressions |
| Threshold evaluation | New evaluator functions | Existing `evaluate_tiered()`, `evaluate_boolean()`, etc. | Cover all threshold types used by forensic signals |
| Acquisition manifest | Hardcoded list | Foundational signals in `brain/signals/base/` | Makes manifest brain-declared and auditable |

## Common Pitfalls

### Pitfall 1: Mapper Returns Wrong Field Structure
**What goes wrong:** Signal evaluator expects `{field_key: value}` dict but mapper returns `{value: X}` or nested structure.
**Why it happens:** `narrow_result()` looks for the exact field_key string in the mapper return dict. If the key doesn't match, the signal gets SKIPPED.
**How to avoid:** When adding a new `data_strategy.field_key` to YAML (e.g., `forensic_goodwill_to_assets`), the mapper must return `{"forensic_goodwill_to_assets": <value>}`. Either: (a) set the key in the mapper return dict to match the field_key, or (b) add the field_key to FIELD_FOR_CHECK dict pointing to the mapper's actual key.
**Warning signs:** New signals all showing SKIPPED/DATA_UNAVAILABLE despite data being present.

### Pitfall 2: Forensic Results on Wrong State Path
**What goes wrong:** Mapper tries to read forensic results from `extracted.financials` but they live on `state.analysis.xbrl_forensics`.
**Why it happens:** Phase 69 stores forensic results as `state.analysis.xbrl_forensics = forensics.model_dump()` -- a dict on AnalysisResults, not ExtractedData. Existing mappers only receive ExtractedData.
**How to avoid:** Extend mapper signatures to accept optional `analysis` parameter. Signal engine passes `state.analysis` when calling mappers.
**Warning signs:** All forensic signals returning SKIPPED despite forensic analysis completing successfully.

### Pitfall 3: Shadow Evaluation Not Capturing Value Changes
**What goes wrong:** Shadow eval compares status (TRIGGERED/CLEAR/SKIPPED) but misses VALUE changes. A signal might stay TRIGGERED but with different numeric values that affect composite scores.
**Why it happens:** Existing shadow eval only logs status + threshold_level match. Value drift within the same threshold band is invisible.
**How to avoid:** Log both old_value and new_value in shadow evaluation. Add a value_delta column. Flag any value change >10% even if status is unchanged.
**Warning signs:** Composite scores shifting despite "zero unexpected flips" in shadow eval.

### Pitfall 4: YAML File Grows Past 500 Lines
**What goes wrong:** Adding 20-30 new signals to `fin/forensic.yaml` (currently 592 lines) pushes it further past the project's 500-line anti-context-rot rule.
**Why it happens:** Each signal definition is ~40-50 lines of YAML.
**How to avoid:** Create a new file `fin/forensic_xbrl.yaml` for the new forensic signals. Keep existing `fin/forensic.yaml` untouched. Note: `fin/forensic.yaml` (592) and `fin/accounting.yaml` (701) and `fin/balance.yaml` (812) are ALREADY over 500 lines -- splitting these is a separate concern.
**Warning signs:** YAML file line count growing without bound.

### Pitfall 5: field_key Collision with Existing Keys
**What goes wrong:** New forensic signal uses `field_key: goodwill_to_assets` which collides with an existing key.
**Why it happens:** The flat namespace of field_keys in FIELD_FOR_CHECK has 200+ entries.
**How to avoid:** Prefix new forensic field_keys with `forensic_` (e.g., `forensic_goodwill_to_assets`, `forensic_channel_stuffing`). This matches the signal ID prefix pattern.
**Warning signs:** Signal evaluation producing wrong values because it matched a different mapper's field.

### Pitfall 6: Foundational Signal Evaluation Crash
**What goes wrong:** Signal engine tries to evaluate a foundational signal, fails because it has no threshold levels.
**Why it happens:** Foundational signals have `threshold: { type: info }` with no red/yellow/clear. The evaluator expects at least one level.
**How to avoid:** Signal engine must filter out `type: foundational` signals BEFORE the evaluation loop. Use: `if signal.get("type") == "foundational": continue`.
**Warning signs:** 25+ new "evaluation failed" errors in signal engine logs.

### Pitfall 7: Cross-Ticker Baselines Recalibrated Too Early
**What goes wrong:** Updating baselines before shadow evaluation is complete means regressions can't be detected.
**Why it happens:** Natural temptation to "clean up" baselines as each signal is wired.
**How to avoid:** Baselines are the LAST step, after all signal changes are complete and shadow evaluation shows zero unexpected flips.
**Warning signs:** Cross-ticker validation passing trivially because baselines were updated to match new behavior.

### Pitfall 8: ForensicMetric Zone vs Signal Threshold Mismatch
**What goes wrong:** ForensicMetric has `zone: "warning"` but signal threshold evaluates the raw `value` field, producing a different severity.
**Why it happens:** Two independent severity assessments: ForensicMetric zone (set during Phase 69 computation) and signal threshold (set during Phase 70 evaluation). They can disagree.
**How to avoid:** Signal thresholds should evaluate the ForensicMetric `.value` field (the raw number), not the `.zone` string. The zone is for display; the threshold is for signal evaluation. Document this clearly in signal YAML `threshold_context`.
**Warning signs:** Forensic card shows "warning" but signal shows "CLEAR" (or vice versa).

## Code Examples

### ForensicMetric Access Pattern
```python
# Source: models/xbrl_forensics.py ForensicMetric schema
# Every forensic result is a ForensicMetric with: value, zone, trend, confidence
#
# When serialized to state.analysis.xbrl_forensics (via model_dump()),
# it becomes a nested dict:
# {
#   "balance_sheet": {
#     "goodwill_to_assets": {
#       "value": 0.42,
#       "zone": "warning",
#       "trend": "deteriorating",
#       "confidence": "HIGH"
#     },
#     ...
#   },
#   ...
# }
#
# Mapper reads the .value field for threshold evaluation:
def _extract_forensic_value(
    xbrl_forensics: dict[str, Any],
    module: str,
    metric: str,
) -> float | None:
    """Extract a ForensicMetric value from serialized xbrl_forensics."""
    mod = xbrl_forensics.get(module)
    if not isinstance(mod, dict):
        return None
    met = mod.get(metric)
    if not isinstance(met, dict):
        return None
    return met.get("value")
```

### Foundational Signal Schema Extension
```python
# In brain_signal_schema.py BrainSignalEntry:
# Add 'type' field with backward-compatible default
class BrainSignalEntry(BaseModel):
    # ... existing fields ...

    type: str = Field(
        default="evaluate",
        description="Signal type: 'evaluate' (Tier 2, existing), 'foundational' (Tier 1, data acquisition manifest)",
    )
```

### Signal Engine Foundational Filtering
```python
# In signal_engine.py execute_signals():
for signal in signals:
    # Skip foundational signals -- they declare data needs, not evaluations
    if signal.get("type") == "foundational":
        continue
    # ... existing evaluation logic ...
```

### Mapper Extension for Forensic Data
```python
# In signal_mappers_analytical.py:
def _map_forensic_check(
    signal_id: str,
    extracted: ExtractedData,
    analysis: AnalysisResults | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    suffix = signal_id.replace("FIN.FORENSIC.", "")

    # Phase 70: read XBRL forensic results from analysis
    xbrl_forensics = None
    if analysis is not None:
        xbrl_forensics = getattr(analysis, "xbrl_forensics", None)

    if xbrl_forensics is not None:
        # Balance sheet forensics
        if suffix == "goodwill_impairment_risk":
            result["forensic_goodwill_to_assets"] = _extract_forensic_value(
                xbrl_forensics, "balance_sheet", "goodwill_to_assets"
            )
        elif suffix == "intangible_concentration":
            result["forensic_intangible_concentration"] = _extract_forensic_value(
                xbrl_forensics, "balance_sheet", "intangible_concentration"
            )
        # ... more mappings for all ForensicMetric fields

    # Legacy fallback preserved for shadow evaluation
    fin = extracted.financials
    if fin is not None:
        if suffix == "fis_composite":
            if fin.distress.beneish_m_score is not None:
                result["value"] = fin.distress.beneish_m_score.score
                if xbrl_forensics:
                    result["_shadow_xbrl"] = _extract_forensic_value(
                        xbrl_forensics, "beneish", "composite_score"
                    )

    return result
```

### Shadow Evaluation Extension
```python
# Source: signal_engine.py _log_shadow_evaluation() pattern
# Extended for XBRL migration tracking
def _log_xbrl_shadow(
    run_id: str,
    signal_id: str,
    ticker: str,
    old_source: str,     # "LLM" or "XBRL"
    old_value: Any,
    new_source: str,
    new_value: Any,
    status_match: bool,
) -> None:
    try:
        conn = connect_brain_db()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brain_xbrl_shadow (
                    run_id VARCHAR NOT NULL,
                    signal_id VARCHAR NOT NULL,
                    ticker VARCHAR NOT NULL,
                    old_source VARCHAR NOT NULL,
                    old_value VARCHAR,
                    new_source VARCHAR NOT NULL,
                    new_value VARCHAR,
                    value_delta FLOAT,
                    status_match BOOLEAN NOT NULL,
                    evaluated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
                    PRIMARY KEY (run_id, signal_id)
                )
            """)
            delta = None
            if old_value is not None and new_value is not None:
                try:
                    delta = float(new_value) - float(old_value)
                except (ValueError, TypeError):
                    pass
            conn.execute("""
                INSERT INTO brain_xbrl_shadow
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)
            """, [run_id, signal_id, ticker, old_source,
                  str(old_value), new_source, str(new_value),
                  delta, status_match])
        finally:
            conn.close()
    except Exception:
        logger.warning("Failed to log XBRL shadow for %s", signal_id, exc_info=True)
```

## Key Implementation Details

### File Inventory

**New files:**
| File | Location | Est. Lines | Purpose |
|------|----------|-----------|---------|
| `xbrl.yaml` | `brain/signals/base/` | ~250 | Foundational signals for XBRL data (5 signals) |
| `filings.yaml` | `brain/signals/base/` | ~200 | Foundational signals for filing text (4 signals) |
| `market.yaml` | `brain/signals/base/` | ~150 | Foundational signals for market/insider data (3 signals) |
| `litigation.yaml` | `brain/signals/base/` | ~150 | Foundational signals for litigation sources (3 signals) |
| `news.yaml` | `brain/signals/base/` | ~150 | Foundational signals for news/blind spot (3 signals) |
| `forensics.yaml` | `brain/signals/base/` | ~350 | Foundational signals for forensic analysis (7 signals) |
| `forensic_xbrl.yaml` | `brain/signals/fin/` | ~500 | 20-30 new forensic evaluative signals |
| `forensic_opportunities.yaml` | `brain/signals/fin/` | ~250 | 12 new opportunity signals (SIG-06) |

**Modified files:**
| File | Location | Change |
|------|----------|--------|
| `brain_signal_schema.py` | `brain/` | Add `type` field to BrainSignalEntry (default="evaluate") |
| `signal_engine.py` | `stages/analyze/` | Filter out foundational signals before evaluation loop |
| `signal_mappers_analytical.py` | `stages/analyze/` | Extend `_map_forensic_check()` for xbrl_forensics paths (~80 lines), add `analysis` param |
| `signal_field_routing.py` | `stages/analyze/` | Add new field_key entries for forensic signals (~30 entries) |
| `field_registry.yaml` | `brain/` | Add forensic field entries (~30 entries) |
| `brain_requirements.py` | `stages/acquire/` | Read foundational signals to build Tier 1 manifest |
| `requirements.py` | `knowledge/` | `build_manifest()` handles foundational signal acquisition blocks |
| `fin/balance.yaml` | `brain/signals/` | Update data_strategy.field_key to XBRL paths |
| `fin/income.yaml` | `brain/signals/` | Update data_strategy.field_key to XBRL paths |
| `fin/temporal.yaml` | `brain/signals/` | Update data_strategy.field_key to quarterly XBRL paths |
| `fin/forensic.yaml` | `brain/signals/` | Update data_strategy.field_key to XBRL paths |
| `fin/accounting.yaml` | `brain/signals/` | Update data_strategy.field_key to XBRL paths |
| `biz/core.yaml` | `brain/signals/` | Update market_cap, revenue field_keys |
| `fwrd/warn_sentiment.yaml` | `brain/signals/` | Wire web search data_strategy |
| `fwrd/warn_ops.yaml` | `brain/signals/` | Wire web search data_strategy |
| `gov/effect.yaml` | `brain/signals/` | Reactivate late_filing, nt_filing |
| `gov/insider.yaml` | `brain/signals/` | Reactivate plan_adoption, unusual_timing |

### Signal Count Breakdown

| Category | Count | Source |
|----------|-------|--------|
| Total signals (current) | ~400 | 36 YAML files across 8 directories |
| New foundational signals (Tier 1) | ~25 | 6 new YAML files in base/ |
| New forensic evaluative signals (SIG-01) | 20-30 | New forensic_xbrl.yaml |
| New opportunity signals (SIG-06) | 12 | New forensic_opportunities.yaml |
| XBRL-replaceable upgrades (SIG-02) | 45 | Across existing YAML files |
| XBRL-enhanceable (SIG-03) | 28 | Across existing YAML files |
| Broken to reactivate (SIG-05) | 15+ | Across gov/effect, gov/insider, fin/forensic, fin/quality |
| Web search candidates (SIG-08) | 35 | fwrd/warn_sentiment, fwrd/warn_ops, gov/board |

### Forensic-to-Signal Mapping (SIG-01 Detail)

| Forensic Module (Phase 69) | State Path (in xbrl_forensics dict) | Signal Count | Example Signal IDs |
|---------------------------|--------------------------------------|-------------|-------------------|
| BalanceSheetForensics | `balance_sheet.*` | 5 | goodwill_impairment_risk, intangible_concentration, off_balance_sheet, cash_conversion_cycle, working_capital_volatility |
| CapitalAllocationForensics | `capital_allocation.*` | 4 | roic_decline, acquisition_effectiveness, buyback_timing, dividend_sustainability |
| DebtTaxForensics | `debt_tax.*` | 5 | interest_coverage_decline, debt_maturity_concentration, etr_anomaly, deferred_tax_growth, pension_underfunding |
| RevenueForensics | `revenue.*` | 4 | revenue_recognition_flag, channel_stuffing, margin_compression, ocf_revenue_trend |
| BeneishDecomposition | `beneish.*` | 4 | dsri_elevated, aqi_elevated, tata_elevated, m_score_composite |
| EarningsQualityDashboard | `earnings_quality.*` | 4 | sloan_accruals, cash_flow_manipulation, sbc_dilution, non_gaap_gap |
| MAForensics | `ma_forensics.*` | 3 | serial_acquirer, goodwill_growth_rate, acquisition_to_revenue |

**Total: ~29 new forensic signals** covering all ForensicMetric fields.

### XBRL-Replaceable Signal Categories (SIG-02 Detail)

From signal-xbrl-audit.md Bucket A:

| Category | Signals | Current field_key | New XBRL field_key |
|----------|---------|-------------------|-------------------|
| Liquidity | FIN.LIQ.position, FIN.LIQ.working_capital | current_ratio, liquidity | XBRL-derived current_ratio |
| Debt | FIN.DEBT.structure/coverage/maturity | debt_to_ebitda, interest_coverage | XBRL-derived ratios |
| Profitability | FIN.PROFIT.revenue/margins | financial_health_narrative | XBRL revenue/margin data |
| Temporal | FIN.TEMPORAL.* (8 signals) | temporal metric markers | Quarterly XBRL trends |
| Forensic | FIN.FORENSIC.* (6 signals) | distress model proxies | xbrl_forensics direct results |
| Quality | FIN.QUALITY.* (5 signals) | earnings quality dict | xbrl_forensics.revenue/earnings_quality |
| Business | BIZ.SIZE.market_cap, BIZ.MODEL.revenue_* | market_cap, revenue segments | XBRL-sourced |

### Broken Signal Reactivation Candidates (SIG-05 Detail)

| Signal ID | Current Status | Why Broken | Reactivation Data Source |
|-----------|---------------|------------|------------------------|
| GOV.EFFECT.late_filing | SKIPPED | No SEC filing metadata | SEC EDGAR filing dates (available in ACQUIRE) |
| GOV.EFFECT.nt_filing | SKIPPED | No NT filing detection | SEC EDGAR filing type filter |
| GOV.INSIDER.plan_adoption | SKIPPED | No 10b5-1 adoption timing | Form 4 XML enhancement (Phase 71) |
| GOV.INSIDER.unusual_timing | SKIPPED | No insider timing analysis | Form 4 filing dates vs 8-K dates (Phase 71) |
| FIN.QUALITY.q4_revenue_concentration | SKIPPED | Requires quarterly data | Quarterly XBRL (Phase 68) |
| FIN.QUALITY.deferred_revenue_trend | SKIPPED | Requires multi-period data | XBRL multi-period extraction (Phase 67-68) |
| FWRD.WARN.cfpb_complaints | SKIPPED | No CFPB data | Web search (Brave Search) |
| FWRD.WARN.fda_medwatch | SKIPPED | No FDA data | Web search (Brave Search) |
| LIT.DEFENSE.forum_selection | SKIPPED | No forum selection detection | 10-K text extraction (existing) |
| LIT.DEFENSE.contingent_liabilities | SKIPPED | Missing contingent data | XBRL contingent liability concepts |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded acquisition in orchestrator.py | Brain-declared Tier 1 foundational signals | v3.1 Phase 70 | Full traceability, auditable manifest |
| LLM extracts all financial data (MEDIUM confidence) | XBRL for numbers, LLM for narratives (HIGH confidence for numerics) | v3.1 Phase 67-69 | 45 signals upgrade from MEDIUM to HIGH confidence |
| Single Beneish M-Score (aggregate only) | 8 individual Beneish components exposed | Phase 69 (FRNSC-05) | Richer forensic signals, contextualized M-Score |
| No quarterly trend signals | 8-quarter QoQ/YoY trend computation | Phase 68 (QTRLY-04/05) | Enables temporal pattern signals (4+ quarter compression) |
| Implicit data acquisition decisions | Explicit Tier 1/Tier 2 traceability | Phase 70 | Every data point traceable to a signal |

## Open Questions

1. **Mapper access to AnalysisResults**
   - What we know: Forensic results live on `state.analysis.xbrl_forensics` (dict). Current mappers receive `ExtractedData` only.
   - What's unclear: The cleanest way to plumb `analysis` through to `_map_forensic_check` without disrupting 10+ other mapper functions.
   - Recommendation: Add optional `analysis` param to `map_phase26_check()` and `_map_forensic_check()`. Signal engine passes `state.analysis` when available. Low-risk since it's additive and defaults to None.

2. **V2 vs legacy signal approach for new signals**
   - What we know: Only 1 signal (FIN.LIQ.position) currently uses V2 schema with `evaluation` section. All 400 others use legacy.
   - What's unclear: Should new forensic signals use V2 schema or legacy?
   - Recommendation: Use legacy pattern (data_strategy.field_key + tiered threshold) for Phase 70. V2 migration is a separate concern. Consistency with existing signals reduces risk.

3. **Foundational signal impact on AcquisitionOrchestrator**
   - What we know: The orchestrator currently hardcodes its acquisition flow (SEC, market, litigation, news in fixed order).
   - What's unclear: Whether Phase 70 should also refactor orchestrator to read foundational signals, or just create the signals as documentation.
   - Recommendation: Phase 70 creates the foundational YAML files and updates `build_manifest()` to read them. The orchestrator itself continues its current flow but logs Tier 1 coverage validation against the foundational manifest. Full orchestrator refactoring to be driven by foundational signals is a future concern -- too risky to combine with signal wiring.

4. **Web search acquisition budget for SIG-08**
   - What we know: Brave Search has 2,000 free/month, Exa has 5-query budget per run.
   - What's unclear: Whether 35 web-search signals can be served within these budgets.
   - Recommendation: Group web search queries by topic (e.g., one "whistleblower + company" search serves 3 signals), prioritize by D&O relevance. Most FWRD.WARN signals share common searches.

5. **ForensicMetric zone vs signal threshold alignment**
   - What we know: ForensicMetric has its own zone classification (safe/warning/danger). Signal thresholds produce RED/YELLOW/CLEAR.
   - What's unclear: Should signal thresholds mirror zone boundaries, or be independently calibrated?
   - Recommendation: Start with thresholds mirroring zone boundaries (same cutoff values). Shadow evaluation will reveal if they need adjustment. Document the correspondence in each signal's `threshold_context`.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `signal_engine.py`, `signal_mappers_analytical.py` (462 lines), `signal_field_routing.py` (366 lines), `brain_signal_schema.py` (320 lines), `brain_unified_loader.py` (160 lines), `forensic_orchestrator.py` (154 lines), `xbrl_forensics.py` (307 lines)
- Brain signals: 36 YAML files across 8 directories, 400 total signals, file sizes verified (forensic.yaml: 592, accounting.yaml: 701, balance.yaml: 812)
- State model: `state.py` line 220: `xbrl_forensics: dict[str, Any] | None`
- Acquisition: `orchestrator.py` (acquisition flow), `brain_requirements.py` (manifest builder)

### Secondary (MEDIUM confidence)
- `.planning/research/signal-xbrl-audit.md` -- Signal XBRL audit with bucket classifications
- `.planning/research/ARCHITECTURE.md` -- Component boundaries and data flow
- `.planning/STATE.md` -- Two-Tier Data Acquisition Model decision

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all existing tools, no new dependencies
- Architecture: HIGH - signal system deeply analyzed, all code paths traced, Two-Tier model documented in STATE.md
- Pitfalls: HIGH - based on codebase analysis + prior migration experience (V2 shadow eval) + forensic model inspection

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable architecture, 30-day validity)
