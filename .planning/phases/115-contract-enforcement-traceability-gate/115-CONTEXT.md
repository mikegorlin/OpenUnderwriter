# Phase 115: do_context Infrastructure - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the brain signal YAML schema with a `presentation.do_context` field, build a do_context evaluation engine in ANALYZE, migrate the 4 hardcoded distress D&O commentary functions (Altman, Beneish, Piotroski, Ohlson) to brain YAML as proof-of-concept, wire context builders to consume rendered do_context strings from SignalResult, and add a CI gate preventing new hardcoded D&O commentary. The 5+ remaining hardcoded D&O functions in section renderers migrate in Phase 116.

</domain>

<decisions>
## Implementation Decisions

### Template Format & Variables
- **Per-status templates** — `presentation.do_context` is a dict keyed by signal outcome: `TRIGGERED_RED`, `TRIGGERED_YELLOW`, `CLEAR`, etc. Each value is a template string with placeholders
- **Separate field** — `do_context` lives alongside existing `context_templates` on `PresentationSpec`, not merged into it. Different purpose: `context_templates` = short status display strings, `do_context` = rich D&O risk interpretation paragraphs
- **Available variables** — Signal result fields: `{value}`, `{score}` (alias), `{zone}`, `{threshold}`, `{threshold_level}`, `{evidence}`, `{source}`, `{confidence}`, plus `{company}`, `{ticker}` from state, plus `{details.*}` for any key from the signal's details dict
- **Graceful missing variables** — Missing variables resolve to empty string. Log a warning for debugging. No runtime crashes on partial data

### Evaluation Timing & Engine
- **Evaluated in ANALYZE stage** — `do_context_engine.py` renders templates right after signal evaluation, stores the rendered string on `SignalResult.do_context`. Single evaluation point, deterministic, auditable in signal results JSON
- **Compound key lookup** — Engine tries `TRIGGERED_RED` first, falls back to `TRIGGERED`, then `DEFAULT`, then empty string. Signal authors choose their granularity — can write specific (RED/YELLOW/CLEAR) or coarse (TRIGGERED/CLEAR) templates
- **New field on SignalResult** — `do_context: str = ""` added to the existing `SignalResult` Pydantic model. Backward compatible (defaults to empty for existing signals). Shows up in state.json signal results dump

### Migration Boundary
- **Phase 115 migrates only the 4 distress functions** — `altman_do_context()`, `beneish_do_context()`, `piotroski_do_context()`, `ohlson_do_context()` from `_distress_do_context.py`. These are the proof-of-concept
- **Phase 116 migrates the remaining 5+** — `_add_audit_do_context()`, `_departure_do_context()`, `_add_leadership_do_context()`, `_add_sca_do_context()`, `_add_pattern_do_context()` plus all new D&O columns
- **Delete Python functions after migration** — Once YAML do_context produces identical output (verified by golden snapshot tests), delete the 4 Python commentary functions. No deprecated code left importable
- **Keep data builder functions** — `build_altman_trajectory()` and `build_piotroski_components()` are data extraction helpers, not D&O commentary. Keep them in the file (or move to better location)

### Signal Type Coverage
- **All signal types can carry do_context** — Schema doesn't restrict by content_type. MANAGEMENT_DISPLAY signals (e.g., board size, revenue breakdown) can have D&O context just like EVALUATIVE_CHECK signals. Phase 116 decides which ones actually get populated

### CI Gate Design
- **Pattern-based detection** — Scan `context_builders/` Python files and Jinja2 templates for D&O evaluative terms: `D&O\s+(risk|exposure|implication)`, `litigation\s+(risk|exposure|relevance)`, `SCA\s+(risk|relevance|probability)`, `underwriting\s+(concern|implication)`, `plaintiff`, `scienter`, `securities fraud` in hardcoded strings
- **Progressive enforcement** — FAIL on Phase 115 scope (4 distress functions), WARN on remaining known hardcoded D&O functions (Phase 116 targets). Warnings don't block CI
- **Regression prevention** — Scan ALL Python files in `context_builders/` and ALL Jinja2 templates broadly. Prevents anyone from adding new hardcoded D&O commentary outside brain YAML
- **Excluded from scan** — YAML files (brain source of truth), test files, comments/docstrings

### Output Verification
- **Golden snapshot tests** — Capture current Python function output for known inputs (multiple score/zone combinations per function, including None/None edge case). After migration, assert YAML engine produces identical strings

### Authoring Tooling
- **Basic validation in `brain health` and `brain audit`** — Validate template syntax, check referenced variables exist in signal's evaluation spec, report do_context coverage (X of Y signals). No interactive preview (Phase 116+)

### Claude's Discretion
- Exact implementation of the do_context engine module structure
- How to handle `details.*` variable resolution (dot-path parsing)
- Whether `_distress_do_context.py` gets renamed/restructured after deleting the 4 commentary functions
- CI gate test file location and naming
- Exact regex patterns for the CI gate (the ones listed above are starting points)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Brain Signal Schema
- `src/do_uw/brain/brain_signal_schema.py` — `PresentationSpec` class (lines 459-472) where `do_context` field will be added; `BrainSignalEntry` (line 474+) for full schema
- `src/do_uw/brain/signals/fin/forensic.yaml` — Contains the 4 distress signals (Altman, Beneish, Piotroski, Ohlson) that will get `do_context` blocks
- `src/do_uw/brain/signals/fin/balance.yaml` — Example of existing `presentation.context_templates` pattern

### Signal Evaluation
- `src/do_uw/stages/analyze/signal_engine.py` — Signal execution flow; `_apply_traceability()` is the pattern for `_apply_do_context()`
- `src/do_uw/stages/analyze/signal_results.py` — `SignalResult` model (lines 122-189) where `do_context` field will be added

### Signal Consumer
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` — `SignalResultView` dataclass, `get_signal_result()` and helpers; add `do_context` field and `get_signal_do_context()` getter

### Hardcoded D&O Functions (migration targets)
- `src/do_uw/stages/render/context_builders/_distress_do_context.py` — 4 commentary functions to migrate + 2 data builder functions to keep
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` — Consumer of distress functions (lines 12-18 imports, lines 50-77 calls)

### Phase 116 Migration Targets (warn, don't fail)
- `src/do_uw/stages/render/sections/sect3_audit.py` — `_add_audit_do_context()`
- `src/do_uw/stages/render/sections/sect4_market_events.py` — `_departure_do_context()`
- `src/do_uw/stages/render/sections/sect5_governance.py` — `_add_leadership_do_context()`
- `src/do_uw/stages/render/sections/sect6_litigation.py` — `_add_sca_do_context()`
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` — `_add_pattern_do_context()`

### Requirements
- `.planning/REQUIREMENTS.md` — INFRA-01 through INFRA-05 (Phase 115 requirements)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PresentationSpec` class already has `context_templates: dict[str, str]` — same pattern, different purpose
- `_apply_traceability()` in `signal_engine.py` — exact pattern for post-evaluation metadata population
- `SignalResultView` frozen dataclass in `_signal_consumer.py` — extend with `do_context` field
- `_brain_signal_cache` dict in `_signal_consumer.py` — lazy brain YAML loading already implemented

### Established Patterns
- Signal evaluation → metadata application → SignalResult storage → context builder consumption → template rendering
- Compound key lookup: `threshold_context` already uses status + level (similar fallback pattern)
- Golden snapshot testing: `test_brain_contract.py` already enforces signal schema contracts

### Integration Points
- `signal_engine.py` — new `_apply_do_context()` called after `_apply_traceability()`
- `SignalResult` model — new field, backward compatible
- `_signal_consumer.py` — new `get_signal_do_context()` accessor
- `financials_evaluative.py` — switch from Python function calls to signal result consumption
- `brain health` CLI — add do_context coverage/validation reporting

</code_context>

<specifics>
## Specific Ideas

- The 4 distress functions have clear zone-based branching (Distress/Gray/Safe for Altman, Likely Manipulator/Possible/Unlikely for Beneish, etc.) — these map directly to TRIGGERED_RED/TRIGGERED_YELLOW/CLEAR template keys
- Template variable resolution should use Python `str.format_map()` with a safe dict that returns empty string for missing keys (similar to `safe_float()` philosophy)
- The `details.*` dot-path notation allows accessing structured data from signal evaluation (e.g., `{details.components.profitability}` for Piotroski)

</specifics>

<deferred>
## Deferred Ideas

- Interactive `brain preview-do-context SIGNAL_ID` command — useful but not Phase 115 scope
- do_context coverage threshold in CI (e.g., "must be >50%") — Phase 120 integration gate
- Templating in do_context for cross-signal references (e.g., "combined with {ref:FIN.DISTRESS.ohlson}") — future enhancement

</deferred>

---

*Phase: 115-contract-enforcement-traceability-gate*
*Context gathered: 2026-03-18*
