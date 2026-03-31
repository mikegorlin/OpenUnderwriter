# Phase 55: Declarative Mapping & Structured Evaluation - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the procedural mapper/evaluator pipeline with declarative alternatives for V2 signals. Build `declarative_mapper.py` and `structured_evaluator.py`. Shadow evaluation proves parity between legacy and V2 paths. At least one full prefix (FIN.LIQ) migrated end-to-end with FIELD_FOR_CHECK entries removed.

</domain>

<decisions>
## Implementation Decisions

### Prefix migration target
- FIN.LIQ (5 signals) is the first full end-to-end migration — simplest prefix, already has V2 YAML (FIN.LIQ.position), mostly DIRECT_LOOKUP from financials.liquidity
- Additional prefixes at Claude's discretion based on how FIN.LIQ goes
- Populate V2 YAML fields broadly across many signals (scripted), but only flip schema_version: 2 on signals that pass shadow evaluation
- Field registry expansion scope at Claude's discretion — scriptable migration of FIELD_FOR_CHECK entries is acceptable

### Shadow evaluation design
- Compare **status AND threshold level** (TRIGGERED/CLEAR/SKIPPED + RED/YELLOW/CLEAR) — both must match between legacy and V2 paths
- Value differences (e.g., 1.48 vs 1.49) are acceptable if status+level match
- Any 3 tickers with zero discrepancy validates migration — no specific tickers required
- Discrepancies logged to **console AND DuckDB** (brain_shadow_evaluations table) for historical tracking
- Shadow evaluation runs **permanently** — never auto-disabled. Both paths always execute. Ongoing regression detection at negligible performance cost

### COMPUTED function design
- Central `COMPUTED_FUNCTIONS` dict in `field_registry.py` maps YAML function names to Python callables
- Functions receive **pre-resolved arguments** — the mapper resolves each arg path from YAML, then passes resolved values to the function. Functions are pure (e.g., `count_items(items_list) -> int`)
- Complex composite formulas (Altman Z-Score, Beneish M-Score) stay as **named evaluator dispatch** — procedural Python functions dispatched by name, not expression-parsed
- Simple formulas (single field reference like `current_ratio`) resolve via field registry

### Legacy cleanup strategy
- FIELD_FOR_CHECK entries **removed immediately** when a prefix is fully migrated — shadow evaluation catches regressions
- Legacy mapper functions: Claude decides per-function based on whether any schema_version: 1 signals still call them
- Rollback mechanism: flip `schema_version` back to 1 in the signal YAML file — V2 stub returns None, legacy takes over. Zero code changes needed
- Migration visibility: V1/V2 migration stats integrated into existing `brain status` command (X signals V1, Y signals V2, Z shadow discrepancies)

### Claude's Discretion
- Whether to migrate additional prefixes beyond FIN.LIQ (based on implementation velocity)
- Field registry expansion scope — full 371-entry migration vs. on-demand
- Where COMPUTED function implementations live (dedicated file vs. field_registry.py)
- Exact DuckDB shadow evaluation table schema

</decisions>

<specifics>
## Specific Ideas

- V2 dispatch hook already wired at `signal_engine.py:107` — `_evaluate_v2_stub()` returns None for fall-through to legacy. Phase 55 replaces this stub.
- 15 V2 signals already exist across FIN, GOV, LIT, STOCK, BIZ from Phase 54
- Shadow evaluation should be invisible to the pipeline consumer — same SignalResult output regardless of which path produced it
- The "populate broadly, activate narrowly" strategy means scripted V2 YAML enrichment is a distinct task from the mapper/evaluator implementation

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_evaluate_v2_stub()` in `signal_engine.py:156` — Phase 55 replaces this with real declarative evaluator dispatch
- `field_registry.py` (56 lines) + `field_registry.yaml` (115 lines) — already exist from Phase 54, need expansion
- `signal_evaluators.py` — existing evaluators (tiered, boolean, numeric_threshold, temporal) as reference for V2 structured evaluator behavior
- `signal_helpers.py` — `coerce_value()`, `first_data_value()`, `make_skipped()`, `try_numeric_compare()` reusable for V2

### Established Patterns
- Signal engine chunked execution loop (`signal_engine.py:75-148`) — V2 dispatch integrates at line 107-118
- `narrow_result()` in `signal_field_routing.py` — resolution order: data_strategy.field_key → FIELD_FOR_CHECK → full dict. V2 replaces FIELD_FOR_CHECK path
- SourcedValue unwrap pattern: `_safe_sourced()` in `signal_mappers.py:27` — need SourcedValue-aware traversal in declarative mapper
- Existing `brain.duckdb` tables for run history — shadow evaluation table follows same patterns

### Integration Points
- `signal_engine.py:107-118` — V2 dispatch decision point (schema_version >= 2)
- `signal_field_routing.py:42` — FIELD_FOR_CHECK dict consumed by `narrow_result()`
- `cli_brain.py` — `brain status` command where migration stats will be added
- `brain_schema.py` — DDL for new shadow evaluation DuckDB table

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 55-declarative-mapping-structured-evaluation*
*Context gathered: 2026-03-01*
