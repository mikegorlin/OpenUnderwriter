# Phase 91: Display Centralization - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Move all chart evaluation thresholds and risk callout text from hardcoded template literals into signal YAML, create a chart type registry YAML, and wire the rendering pipeline to read presentation configuration from signal data. Templates become threshold-free; adding a new chart requires only a registry entry and a rendering function.

Requirements: DISP-01, DISP-02, DISP-03, DISP-04

</domain>

<decisions>
## Implementation Decisions

### Threshold ownership
- Thresholds live on signal YAML `display:` blocks — co-located with the signal that owns them
- Reuse existing `threshold:` block (red/yellow/clear) for chart evaluation thresholds — no new schema needed
- Context builders read signal thresholds and inject them into template context dicts (e.g., `thresholds.beta.yellow`)
- Templates use `{{ thresholds.beta.yellow }}` instead of hardcoded `1.5`
- All charted signals must have threshold blocks — add missing ones for STOCK.DECLINE_FROM_HIGH (30%/15%), STOCK.MDD_RATIO (1.5/1.0), STOCK.VOLATILITY (40%/1.3x), STOCK.IDIOSYNCRATIC_VOL (30%), STOCK.ALPHA (10%), and any others found in templates

### Callout generation
- Each signal carries `display.callout_templates` keyed by severity (red/yellow/clear) with `{value}` placeholders
- Severity-tiered templates — different D&O-specific text for amber vs red vs green
- Green/positive callouts included (not just risk flags) — complete centralization
- Context builder aggregates: iterates chart-relevant signals, evaluates each against thresholds, renders appropriate callout_template, groups into `flags[]` and `positives[]` lists
- Templates just loop over flags/positives — no threshold logic in Jinja2

### Chart registry
- YAML registry at `brain/config/chart_registry.yaml` declares all charts with metadata: id, name, module, function, params, signals, formats (html/pdf/word), data_requires
- Registry-driven rendering: renderer loops over registry entries filtered by format, calls each chart function dynamically via `import_chart_fn(chart)`
- Chart placement declared in registry (section/facet/position) — templates read registry to know which charts go where, matching facet-driven rendering pattern
- Standardized chart function signature: `(state: AnalysisState, **params) -> str` returning SVG string
- Overlays declared in registry as sub-components of parent charts with ordered list — renderer applies overlays in declared order

### Migration approach
- Single sweep: audit all templates for hardcoded thresholds, map to signals, add/update threshold blocks, update context builders, update templates — clean break, no mixed state
- Preserve existing `display:` fields (value_format, source_type, threshold_context) and extend with new fields (callout_templates) — additive, no migration of existing display blocks
- CI lint rule: test scans chart/market templates for numeric literals in conditional expressions, fails if found — prevents threshold drift back into templates

### Claude's Discretion
- Exact list of signals needing new threshold blocks (beyond the 5-6 identified)
- How to handle overlay thresholds (volume spike 20%, divergence band 10.0) — signal YAML or registry params
- Fallback behavior when a signal's callout_template is missing for a given severity
- Chart registry YAML schema details (additional metadata fields)
- How to handle charts that currently take non-state params (e.g., theme selection)

</decisions>

<specifics>
## Specific Ideas

- The pattern mirrors what Phase 56 did for section rendering (facet-driven dispatch from YAML) — this is the same principle applied to charts and thresholds
- Context builder becomes the single translation layer: reads signal YAML thresholds + callout templates, evaluates against state data, passes resolved values to templates
- The CI lint rule should catch patterns like `{% if value > 1.5 %}` but allow `{% if value > thresholds.beta.yellow %}` — regex on numeric literals in conditional expressions

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `display:` blocks already on signals (value_format, source_type, threshold_context) — extend with callout_templates
- `threshold:` blocks on many signals (red/yellow/clear with numeric values) — reuse for chart evaluation
- `BrainLoader` handles additive schema fields (Phase 82) — new display fields load without migration
- `embed_chart()` macro in `templates/html/components/charts.html.j2` — chart embedding already centralized
- `design_system.py` color palettes (BLOOMBERG_DARK, CREDIT_REPORT_LIGHT, CHART_COLORS) — reusable

### Established Patterns
- Context builders (`context_builders/*.py`) extract state data into template context dicts — threshold injection fits naturally
- Facet-driven dispatch from YAML (Phase 56) — chart registry follows same declarative pattern
- 10 chart modules in `stages/render/charts/` with varied signatures — need standardization to `(state, **params) -> str`

### Integration Points
- `context_builders/market.py` — primary location for threshold injection and callout aggregation
- `templates/html/sections/market/stock_charts.html.j2` — main template with ~15 hardcoded thresholds and callout conditionals
- `templates/html/sections/market/stock_performance.html.j2` — additional hardcoded thresholds (30%, 15%, 1.5)
- `stages/render/charts/stock_chart_overlays.py` — overlay thresholds (10%, 10.0, 2.0x, 1.5x)
- `stages/render/html_renderer.py` — where registry-driven chart rendering would be called

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 91-display-centralization*
*Context gathered: 2026-03-09*
