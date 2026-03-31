# Phase 111: Signal Wiring Closure - Research

**Researched:** 2026-03-16
**Domain:** Signal-to-render traceability, YAML-driven data resolution, mechanism evaluators
**Confidence:** HIGH

## Summary

Phase 111 closes the wiring gaps identified by the traceability audit. The work divides into three clear streams: (1) assign render targets to 48 Phase 110 mechanism signals (absence/conjunction/contextual) that have empty `group` fields and mark 51 ungoverned manifest groups as `display_only: true`, (2) implement trend and peer_comparison evaluators in `mechanism_evaluators.py`, and (3) replace ~3,078 lines of hardcoded mapper code with a YAML-driven generic field resolver while closing the 64 SKIPPED signal data gaps.

The code investigation reveals the 48 empty-group signals are exactly the Phase 110 signals (20 absence, 8 conjunction, 20 contextual). All other 514 signals already have `group` fields. The trend mechanism affects 48 signals (not just 6 as the audit initially counted) -- 10 FIN.TEMPORAL, 32 FWRD.WARN, and 6 DISC.YOY -- though many of these already evaluate via threshold fallthrough because their mapper (`_map_disc_fields`, `_map_temporal_check`) provides data. The 9 peer_comparison signals need the SEC Frames percentile data already available at `state.benchmark.frames_percentiles`.

**Primary recommendation:** Execute in three sequential plans: (1) render target assignment (YAML-only, low risk), (2) trend + peer evaluators (new code in mechanism_evaluators.py, moderate risk), (3) generic field resolver replacing mappers + SKIPPED closure (highest risk, needs hydration verification).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Triage each of the 64 SKIPPED signals individually: wire signals where data exists at a different state path (path mismatch fix), mark signals DEFERRED where data genuinely doesn't exist yet (needs future extraction work)
- For the 25 "mapper not configured" signals: add mapper/resolver routing if data exists somewhere in state, otherwise DEFERRED with documented rationale
- For the 39 "data not available" signals: close cheap path mismatches, defer signals requiring new LLM extraction or new API calls
- DEFERRED signals show in worksheet check panels with a "Data pending" badge -- distinct from SKIPPED and CLEAR
- Hard CI gate: SKIPPED rate must be <5% or CI fails (enforced in Phase 115 as CI-04)
- Ungoverned manifest groups displaying COMPUTED data marked `display_only: true`
- Ungoverned manifest groups displaying RAW EXTRACTED data also marked `display_only: true`
- `display_only: true` field added directly in `output_manifest.yaml`
- 48 Phase 110 mechanism signals assigned to parent domain manifest group
- Replace ~3,000 lines of hardcoded mapper code with a YAML-driven generic field resolver
- Signal engine reads `acquisition.sources[].fields` from YAML and resolves directly against state
- YAML acquisition block gets richer declarations: `path`, `computed_from`, `fallback_paths`
- Fix all 102 YAML field declarations to point at correct actual state paths
- Hydration verification: every signal that evaluated before must still evaluate after migration
- QA gate: pipeline on at least one ticker pre and post migration, diff all signal results, zero regressions
- Trend evaluator compares current vs prior annual filing data
- Both evaluators produce standard CLEAR/TRIGGERED/SKIPPED result structure

### Claude's Discretion
- Specific peer comparison data source selection (SEC Frames percentiles vs MAD z-scores)
- Resolver architecture design (path traversal, computed fields, fallbacks)
- Individual signal-by-signal triage decisions for the 64 SKIPPED
- Assignment of 48 mechanism signals to specific manifest groups
- Categorization of 51 ungoverned manifest groups as display_only

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WIRE-01 | All 562 signals have non-empty `group` field mapping to a manifest group | 48 empty-group signals identified (all Phase 110 mechanism signals). Each needs `group` field matching a manifest group ID from the 115 available groups. |
| WIRE-02 | All ungoverned manifest groups have signal coverage or `display_only: true` | 51 ungoverned groups identified in audit. Most display computed/extracted data, not signal-evaluative content. `display_only: true` field added to manifest YAML. |
| WIRE-03 | `evaluate_trend()` and `evaluate_peer_comparison()` evaluators implemented | 48 trend signals (FIN.TEMPORAL, FWRD.WARN, DISC.YOY) and 9 peer_comparison signals. Existing data sources: TenKYoYComparison model, XBRL quarterly data, SEC Frames percentiles. |
| WIRE-04 | SKIPPED rate reduced from 13.5% to <5% | 64 SKIPPED signals: 39 "data not available" + 25 "mapper not configured". Root cause: path mismatches between YAML declarations and actual state paths, plus genuinely missing data needing DEFERRED classification. |
| WIRE-05 | Acquisition field declarations match actual state paths | 102 fields with no data, but root cause is YAML paths don't match state model. Generic resolver with correct paths fixes this. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.x | Signal YAML loading | Already used throughout brain/ |
| Pydantic v2 | 2.x | State model, signal schemas | Project standard per CLAUDE.md |
| Python 3.12+ | 3.12 | Async, type hints | Project requirement |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test infrastructure | 6,714 existing tests, 35 mechanism evaluator tests |
| ruff | latest | Linting/formatting | Project standard |

No new libraries needed. All work uses existing infrastructure.

## Architecture Patterns

### Existing Signal Engine Dispatch Pattern
The signal engine (`signal_engine.py`, 576 lines) processes signals in this order:
1. Filter to `execution_mode == "AUTO"` signals
2. Order by dependency graph
3. For each signal: check sector applicability, then dispatch by mechanism
4. Mechanism dispatch (lines 125-141): conjunction/absence/contextual go to `mechanism_evaluators.py`
5. All others fall through to `map_signal_data()` -> content-type dispatch -> threshold evaluation

**Trend and peer evaluators extend Step 4.** Add `trend` and `peer_comparison` to the mechanism dispatch block.

### Existing Mapper Architecture (TO BE REPLACED)
```
signal_engine.py
  -> map_signal_data() in signal_mappers.py (999 lines)
    -> signal_mappers_analytical.py (650 lines) -- FIN.TEMPORAL, FIN.FORENSIC, etc.
    -> signal_mappers_events.py (233 lines) -- BIZ.EVENT
    -> signal_mappers_ext.py (173 lines) -- helpers
    -> signal_mappers_forward.py (455 lines) -- FWRD.WARN
    -> signal_mappers_sections.py (568 lines) -- section-based routing
  -> signal_field_routing.py (446 lines) -- narrow_result()
TOTAL: ~3,524 lines of routing code
```

### Target: Generic YAML-Driven Resolver
```
signal_engine.py
  -> resolve_signal_data(sig, state) in signal_resolver.py (~200-300 lines)
    - Reads sig["acquisition"]["sources"][*]["fields"] or sig["field_path"] or sig["data_strategy"]["field_key"]
    - Resolves path against state object (e.g., "extracted.governance.board_composition.size")
    - Handles computed_from paths (e.g., "analysis.xbrl_forensics.beneish.composite_score")
    - Supports fallback_paths (try multiple paths in order)
    - Returns dict[str, Any] keyed by field name
```

### Signal YAML Field Resolution Paths (3 types)
```yaml
# Type 1: Direct state path
acquisition:
  sources:
    - fields:
        - path: extracted.governance.board_composition.size

# Type 2: Computed from analysis stage
acquisition:
  sources:
    - fields:
        - computed_from: analysis.xbrl_forensics.beneish.composite_score

# Type 3: Fallback chain
acquisition:
  sources:
    - fields:
        - path: extracted.financials.statements.revenue
          fallback_paths:
            - company.financials.revenue
            - extracted.market.fundamental_data.revenue
```

### Manifest Group Assignment Pattern for Mechanism Signals
```yaml
# Absence signals -> transparency_disclosure group
# (they detect missing disclosures, which is a transparency concern)
ABS.DISC.* -> transparency_disclosure

# Conjunction signals -> parent domain group based on primary domain
CONJ.ACCT.governance -> audit_profile
CONJ.COMP.perf_divergence -> compensation_analysis
CONJ.DISTRESS.insider -> distress_indicators
CONJ.FIN.growth_margin_guidance -> key_metrics
CONJ.GOV.governance_event -> structural_governance
CONJ.INSIDER.news_gap -> insider_trading
CONJ.REG.litigation -> active_matters
CONJ.RPT.audit -> audit_profile

# Contextual signals -> parent domain group
CTX.FIN.* -> the financial group matching the source signal
CTX.GOV.* -> governance group matching the source signal
CTX.MKT.* -> market group matching the source signal
CTX.RISK.* -> risk group matching the source signal
CTX.COMP.* -> competitive_position or company_checks
CTX.EXEC.* -> executive_tenure_stability
CTX.LIT.* -> active_matters
```

### Anti-Patterns to Avoid
- **Prefix-based Python routing**: The current mapper system routes by signal_id prefix (FIN.*, GOV.*, etc.) with hardcoded Python functions. This violates brain portability -- signals should declare their data paths, not rely on routing code.
- **Building narrow_result() for every signal**: The current `signal_field_routing.py` builds ALL fields for a prefix group, then narrows to the one field the signal needs. The generic resolver should only resolve the declared fields.
- **Parallel data paths**: Never have both the old mapper and new resolver active. Complete the migration atomically per plan, with hydration verification.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State path traversal | Custom path parser | Python `operator.attrgetter` + `getattr` chain | Standard library handles nested attribute access |
| YAML field validation | Custom field checker | Pydantic model for acquisition spec | Already have BrainSignalEntry Pydantic model |
| Signal result diffing | Custom diff tool | `deepdiff` or simple dict comparison | For hydration verification, dict equality suffices |
| Trend comparison | Complex time-series analysis | Simple current_value vs prior_value comparison | DISC.YOY already has YoY data extracted; FIN.TEMPORAL data comes from XBRL quarterly |

## Common Pitfalls

### Pitfall 1: Trend Signals Already Have Data (Most of Them)
**What goes wrong:** Implementing a trend evaluator that tries to fetch new data, when the existing mapper already provides it.
**Why it happens:** The audit said "no trend dispatch" but the signals still evaluate via threshold fallthrough.
**How to avoid:** The DISC.YOY signals get data from `_map_disc_fields` -> `extracted.ten_k_yoy`. FIN.TEMPORAL signals get data from `_map_temporal_check`. The trend evaluator should ENHANCE evaluation (e.g., delta calculation, prior-vs-current comparison evidence) rather than replace data acquisition.
**Warning signs:** Signals that previously returned CLEAR/TRIGGERED now returning SKIPPED after migration.

### Pitfall 2: Hydration Regression (Critical)
**What goes wrong:** Replacing the mapper with a generic resolver causes signals that previously evaluated to now SKIP because the new resolver can't find data at the declared YAML paths.
**Why it happens:** 102 YAML field declarations are aspirational -- they don't match actual state paths. The old mapper ignores YAML paths and uses hardcoded routing.
**How to avoid:** Before replacing ANY mapper: (1) run pipeline on test ticker, save all signal results, (2) implement resolver, (3) run again, (4) diff results. Zero regressions.
**Warning signs:** SKIPPED rate increases after migration.

### Pitfall 3: SourcedValue Unwrapping
**What goes wrong:** The generic resolver traverses state paths but hits SourcedValue wrappers instead of raw values.
**Why it happens:** Most CompanyProfile and ExtractedData fields are `SourcedValue[T]` (wrapper with `.value`, `.source`, `.confidence`). The old mappers call `_safe_sourced()` to unwrap.
**How to avoid:** The generic resolver must automatically unwrap SourcedValue -- check if result has `.value` attribute and unwrap.
**Warning signs:** Signal gets a SourcedValue object instead of the numeric/string value.

### Pitfall 4: DEFERRED vs SKIPPED Display
**What goes wrong:** Adding `execution_mode: DEFERRED` but the signal engine still tries to evaluate them (it filters on `execution_mode == "AUTO"`).
**Why it happens:** DEFERRED is a new execution_mode value -- need to verify the engine handles it correctly.
**How to avoid:** DEFERRED signals should NOT appear in `execute_signals()` output. They need a separate code path in the renderer to show "Data pending" badge.
**Warning signs:** DEFERRED signals appearing as SKIPPED in results.

### Pitfall 5: Manifest display_only Validation
**What goes wrong:** Adding `display_only: true` to manifest YAML but the manifest loader/validator rejects unknown fields.
**Why it happens:** The manifest may have Pydantic validation or strict schema.
**How to avoid:** Check manifest loading code for schema validation before adding new fields.
**Warning signs:** Manifest loading fails after adding display_only.

## Code Examples

### Trend Evaluator Implementation Pattern
```python
# Source: mechanism_evaluators.py extension
def evaluate_trend(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
) -> SignalResult:
    """Evaluate a trend signal: compare current vs prior period values.

    For DISC.YOY signals: data comes from extracted.ten_k_yoy
    For FIN.TEMPORAL: data comes from XBRL quarterly metrics
    """
    signal_id = sig.get("id", "UNKNOWN")
    field_key = sig.get("data_strategy", {}).get("field_key", "")

    # Get current value from mapped data
    current_value = data.get(field_key)
    if current_value is None:
        return _make_mechanism_skipped(signal_id, sig.get("name", ""), sig, "No trend data available")

    # Evaluate against threshold (reuse existing threshold logic)
    # The trend evaluator enriches evidence with delta/direction
    # but delegates threshold comparison to standard evaluators
```

### Peer Comparison Evaluator Pattern
```python
# Source: mechanism_evaluators.py extension
def evaluate_peer_comparison(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, dict[str, Any]],
    *,
    benchmarks: Any | None = None,
) -> SignalResult:
    """Evaluate signal against SEC Frames percentile data.

    Reads benchmarks.frames_percentiles for the metric,
    compares company value to sector/overall percentile.
    """
    # SEC Frames data at state.benchmark.frames_percentiles
    # Contains: {metric: {overall: pct, sector: pct, value: val}}
```

### Generic Field Resolver Pattern
```python
# Source: new signal_resolver.py
def resolve_signal_data(
    sig: dict[str, Any],
    state: AnalysisState,
) -> dict[str, Any]:
    """Resolve signal data requirements from YAML declarations against state.

    Resolution order:
    1. sig["field_path"] (direct field key)
    2. sig["data_strategy"]["field_key"] (legacy key)
    3. sig["acquisition"]["sources"][*]["fields"] (v7.0 YAML paths)
    """
    result: dict[str, Any] = {}

    # Try field_path first (most signals have this)
    field_path = sig.get("field_path")
    if field_path:
        value = _resolve_path(state, field_path)
        if value is not None:
            result[field_path] = _unwrap_sourced(value)
            return result

    # Try data_strategy.field_key
    ds = sig.get("data_strategy", {})
    field_key = ds.get("field_key")
    if field_key:
        value = _resolve_path(state, field_key)
        if value is not None:
            result[field_key] = _unwrap_sourced(value)
            return result

    return result


def _resolve_path(obj: Any, path: str) -> Any:
    """Traverse dotted path on object, unwrapping SourcedValues."""
    parts = path.split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        # Unwrap SourcedValue at each level
        if hasattr(current, "value") and hasattr(current, "source"):
            current = current.value
    return current
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prefix-based Python routing (signal_mappers*.py) | YAML-driven field resolution | Phase 111 | Eliminates ~3,000 lines of hardcoded routing; enables brain portability |
| Only 3 mechanism types dispatched | 5 mechanism types (+ trend, peer_comparison) | Phase 111 | Full coverage of declared evaluation mechanisms |
| SKIPPED = data gap (undifferentiated) | SKIPPED vs DEFERRED (explicit distinction) | Phase 111 | Underwriter sees "Data pending" vs "No data" |
| Ungoverned manifest groups | display_only annotation | Phase 111 | Explicit contract about what sections signals govern |

## Key Findings from Code Investigation

### Signal Count Correction
The traceability audit reported "6 DISC.YOY signals" needing trend evaluator. Actual count: **48 signals** with `mechanism: trend` (10 FIN.TEMPORAL + 32 FWRD.WARN + 6 DISC.YOY). ALL 48 already have `group` fields (not empty). The 48 empty-group signals are exclusively Phase 110 mechanism signals (absence/conjunction/contextual).

### DISC.YOY Data Already Mapped
The `_map_disc_fields()` function in `signal_mappers.py` (lines 974-996) already maps all 6 DISC.YOY signals to `extracted.ten_k_yoy` fields. These signals currently evaluate via threshold fallthrough (no trend dispatch). A proper trend evaluator would enrich the evaluation with delta/comparison evidence but the data pipeline already works.

### FIN.TEMPORAL Data Already Mapped
The `_map_temporal_check()` function in `signal_mappers_analytical.py` already maps 10 FIN.TEMPORAL signals to XBRL quarterly data. Same situation -- they evaluate as threshold signals currently.

### FWRD.WARN Signals Mostly SKIPPED
32 FWRD.WARN signals have `mechanism: trend` but most lack data because they reference external data sources (Glassdoor, Indeed, LinkedIn, CFPB, etc.) that are not yet acquired. These will be DEFERRED candidates.

### Peer Comparison Data Source
SEC Frames percentile data lives at `state.benchmark.frames_percentiles` (dict of `FramesPercentileResult`). The PeerOutlierEngine (Phase 109) already consumes this data for pattern detection. The peer_comparison evaluator should use the same data source. 6 of 9 peer signals are FIN.PEER with `data_strategy.field_key` pointing to `benchmarked.frames_percentiles.*` paths.

### Manifest Has 115 Groups
The output manifest has 115 sub-groups across 13 sections. 61 groups have signal coverage, 51 do not (though some IDs appear in both counts due to naming). The `display_only: true` field does not currently exist in the manifest schema -- need to verify the manifest loader accepts it.

### execution_mode Values
Currently only `AUTO` is filtered for in `signal_engine.py` (line 71). Other values seen: `MANUAL`, `FALLBACK`, `SECTOR`. `DEFERRED` is a new value that must be handled -- signals with this mode should be excluded from evaluation but included in results with a "Data pending" status for rendering.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/stages/analyze/ -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIRE-01 | All 562 signals have non-empty group | unit | `uv run pytest tests/brain/test_signal_groups.py -x` | Wave 0 |
| WIRE-02 | Ungoverned groups marked display_only | unit | `uv run pytest tests/brain/test_manifest_governance.py -x` | Wave 0 |
| WIRE-03 | Trend + peer evaluators dispatch | unit | `uv run pytest tests/stages/analyze/test_mechanism_evaluators.py -x` | Exists (35 tests) |
| WIRE-04 | SKIPPED rate <5% | integration | `uv run pytest tests/stages/analyze/test_skipped_rate.py -x` | Wave 0 |
| WIRE-05 | Acquisition field declarations match state paths | unit | `uv run pytest tests/brain/test_field_declarations.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/analyze/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/brain/test_signal_groups.py` -- verify all 562 signals have non-empty group mapping to a manifest group
- [ ] `tests/brain/test_manifest_governance.py` -- verify ungoverned groups have display_only: true
- [ ] `tests/stages/analyze/test_skipped_rate.py` -- verify SKIPPED rate on test data
- [ ] `tests/brain/test_field_declarations.py` -- verify YAML field paths resolve against state model
- [ ] Extend `tests/stages/analyze/test_mechanism_evaluators.py` with trend + peer tests

## Open Questions

1. **Manifest Schema Flexibility**
   - What we know: `output_manifest.yaml` is loaded by the render stage and drives section rendering
   - What's unclear: Whether the manifest loader validates strictly (rejecting unknown fields like `display_only`) or is permissive
   - Recommendation: Check manifest loading code before adding `display_only`. If strict, update the loader/schema first.

2. **DEFERRED Rendering**
   - What we know: DEFERRED signals should show "Data pending" badge in check panels
   - What's unclear: How the renderer currently handles non-AUTO signals (does it render them at all?)
   - Recommendation: The signal engine currently excludes non-AUTO signals entirely. DEFERRED signals need a separate rendering path -- either included in results with a special status, or tracked in a parallel list.

3. **Generic Resolver Migration Safety**
   - What we know: 3,078 lines of mapper code to replace; user demands zero regressions
   - What's unclear: Whether a phased migration (resolver handles what it can, falls back to old mapper) is safer than big-bang replacement
   - Recommendation: Plan 111-03 should use a phased approach: implement resolver, wire it as the primary path with mapper as fallback, verify on test ticker, then remove mapper fallback once verified.

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `signal_engine.py` (576 lines), `mechanism_evaluators.py` (509 lines), `signal_mappers*.py` (~3,078 lines)
- Direct YAML inspection of all 562 signals in `brain/signals/` directories
- `TRACEABILITY-AUDIT.md` -- baseline metrics and gap identification
- `output_manifest.yaml` -- 115 manifest groups across 13 sections
- `ten_k_comparison.py` -- TenKYoYComparison model with YoY fields

### Secondary (MEDIUM confidence)
- `CONTEXT.md` user decisions on architecture approach
- Existing test suite (35 mechanism evaluator tests, 6,714 total tests)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all existing infrastructure
- Architecture: HIGH -- extending established patterns (mechanism dispatch, signal YAML, manifest)
- Pitfalls: HIGH -- identified from direct code inspection of mapper routing, SourcedValue handling, and data availability

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable internal architecture, no external dependencies)
