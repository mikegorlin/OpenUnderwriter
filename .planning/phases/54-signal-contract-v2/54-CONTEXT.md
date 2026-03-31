# Phase 54: Signal Contract V2 - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend signal YAML schema with machine-readable `acquisition`, `evaluation`, and `presentation` sections. Add `schema_version` for dual-path dispatch and `field_registry.yaml` for declarative field resolution. Schema is additive — old signals keep working unchanged. 10-15 signals migrated as proof of concept. V2 fields are stored but NOT consumed by the pipeline yet — evaluation results must be identical before/after.

</domain>

<decisions>
## Implementation Decisions

### V2 YAML Structure
- Parallel threshold fields: Keep `threshold.red/yellow/clear` as English text (human-readable). Add `evaluation.thresholds` as structured list `[{op, value, label}]`. Both coexist on V2 signals — English for display, structured for machine eval.
- Flat source list for acquisition: `acquisition.sources` is a list of `{type, fields: [dotted.paths], fallback_to: next_source}`. One level deep, no nested grouping.
- Presentation extends, doesn't replace: `presentation` adds `detail_levels` and `context_templates` alongside existing `display` (DisplaySpec) and `facet` fields. Existing fields stay as-is for backward compat. Presentation is additive.
- snake_case naming throughout: Match existing YAML conventions (`acquisition_tier`, `data_strategy`, `extraction_hints`). V2 fields follow same pattern: `evaluation.window_years`, `presentation.detail_levels`, `acquisition.fallback_to`.

### Field Registry Design
- Coexist with FIELD_FOR_CHECK: `field_registry.yaml` is the new source of truth for V2 signals. FIELD_FOR_CHECK dict (371 entries) stays for legacy signals. Phase 55 migrates signals off FIELD_FOR_CHECK. Zero risk of breaking 400 signals during schema phase.
- Named function dispatch for COMPUTED fields: COMPUTED fields reference a Python function by name: `{type: COMPUTED, function: compute_activist_count, args: [extracted.governance.activists]}`. Registry declares intent, code provides implementation.
- Dual roots supported now: Registry paths can start with `extracted.*` (ExtractedData) or `company.*` (CompanyProfile). Resolver knows which Pydantic model to traverse.
- Single file: One `brain/field_registry.yaml` with sections by domain. At ~371 entries (~800 lines YAML) it's manageable in one file.

### Signal Selection for V2 Migration
- Coverage breadth: Pick 2-3 from each prefix (FIN, GOV, LIT, STOCK, BIZ) to prove V2 works across all domains. Prioritize signals with clear numeric thresholds (easiest to convert to structured operators).
- Stick to 5 listed prefixes: FIN, GOV, LIT, STOCK, BIZ only. EXEC and NLP can wait for later phases.
- Edit in-place: Add V2 fields directly to existing signal entries in `brain/signals/fin/balance.yaml` etc. Set `schema_version: 2`. V1 fields stay alongside V2 fields. Single source of truth per signal.
- Strict Pydantic validation for V2 sections: V2 Pydantic models (`AcquisitionSpec`, `EvaluationSpec`, `PresentationSpec`) use `extra='forbid'`. Catches typos in YAML immediately. Main `BrainSignalEntry` stays `extra='allow'` for unknown top-level fields.

### Schema Version Dispatch
- Dispatch stub only: Add `schema_version` check in the signal engine entry point. V1 -> existing path (no change). V2 -> calls a stub that falls through to legacy path. Phase 55 fills in the real V2 evaluator/mapper. Proves the dispatch works without changing behavior.
- Dispatch in signal engine entry: In `signal_engine.py` execute_signals() path. The engine already dispatches by content_type — add `schema_version` as an earlier branch. Natural place since it's the single entry point for all signal evaluation.
- Both automated and manual verification: Automated regression tests that load V2 signals, run through legacy path, confirm identical results. Plus manual pipeline run on 1-2 tickers as final validation.
- Update CLI for V2 visibility: `brain stats` shows "V2 signals: 12/400 (3%)" and "Fields in registry: 45". `brain build` validates V2 Pydantic schemas. Makes migration progress visible.

### Claude's Discretion
- Exact V2 Pydantic model field names and defaults
- Which specific signals from each prefix to migrate (within the breadth criteria)
- Internal structure of the dispatch stub
- Test fixture design

</decisions>

<specifics>
## Specific Ideas

- V2 threshold example: `evaluation.thresholds: [{op: "<", value: 1.0, label: "RED"}, {op: "<", value: 1.5, label: "YELLOW"}]` alongside existing `threshold.red: "<1.0 current ratio (inadequate liquidity)"`
- Field registry example: `current_ratio: {path: extracted.financials.current_ratio, type: DIRECT_LOOKUP}` and `activist_count: {type: COMPUTED, function: compute_activist_count, args: [extracted.governance.activists]}`
- ~30% of FIELD_FOR_CHECK entries are COMPUTED (len(), filters, fallbacks) — the registry must handle this reality, not just simple paths

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BrainSignalEntry` (brain_signal_schema.py): Current Pydantic model with `extra='allow'` — V2 fields will extend this
- `BrainSignalThreshold` model: Current threshold structure (type, red, yellow, clear strings)
- `DisplaySpec` model: Current rendering spec (value_format, source_type, threshold_context)
- `BrainLoader` (brain_unified_loader.py): YAML loader with Pydantic validation loop — V2 validation plugs in here

### Established Patterns
- YAML -> Pydantic validation: `_load_and_validate_signals()` loads all YAML, enriches, validates with `BrainSignalEntry.model_validate()`
- Module-level singleton caching: Signals loaded once, served from memory for process duration
- `enrich_signal()`: Pre-processing step before validation — may need V2 enrichment additions
- `data_strategy.field_key` already takes priority over FIELD_FOR_CHECK in `narrow_result()`

### Integration Points
- `signal_engine.py`: Where `schema_version` dispatch stub will be added
- `signal_field_routing.py`: `narrow_result()` — current dispatch between `data_strategy.field_key` and `FIELD_FOR_CHECK`
- `brain/signals/**/*.yaml`: 36 files, 400 signals — 10-15 will get V2 fields added in-place
- `brain build` CLI command: Needs V2 schema validation and stats output

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 54-signal-contract-v2*
*Context gathered: 2026-03-01*
