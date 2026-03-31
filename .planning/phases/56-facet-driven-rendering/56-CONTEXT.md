# Phase 56: Facet-Driven Rendering - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Facets control what appears in each document section. Facet YAML files gain subsection specs with layout hints that drive template dispatch. At least one facet (Financial Health) fully migrated with facet-driven rendering orchestrating existing section renderers. Legacy fallback preserved for unmigrated facets. HTML output only — Word/Markdown renderers untouched.

</domain>

<decisions>
## Implementation Decisions

### Subsection Schema Design
- Extend existing `content` pattern from market_activity.yaml — rename `content` → `subsections`, add `id`, `name`, `columns` fields to each entry
- Each subsection entry has explicit `signals` list (not auto-grouped by prefix) — clear, no magic
- `render_as` field per subsection controls template dispatch (already exists in market_activity `content`)

### Facet-to-Template Dispatch
- Thin orchestrator pattern: `facet_renderer.py` calls existing section functions (sect3_financial.py, etc.), but facet YAML controls WHICH subsections appear and in WHAT order
- Section .py functions still do the heavy lifting — facet renderer is a glue/dispatch layer
- HTML rendering only for Phase 56 — Word/Markdown renderers remain completely untouched

### Migration Strategy
- Financial Health is the first facet to fully migrate (58 signals, heaviest, matches RENDER-03 suggestion)
- "No hardcoded renderer involvement" = facet orchestrates, section functions stay — facet dispatch replaces hardcoded template includes, but existing rendering functions are still invoked by the dispatcher
- Verification: HTML diff on a real ticker (e.g., SNA) before/after migration — visual output must match

### Legacy Fallback
- Dispatch mechanism: presence of `subsections` key in facet YAML — if present, use facet renderer; if absent, fall through to legacy hardcoded section template
- Per-section mixed mode: a single document can have BOTH facet-rendered and legacy-rendered sections side by side (essential for incremental migration)

### Claude's Discretion
- Exact `render_as` type taxonomy (whether to use RENDER-01's kv_table/scorecard/narrative/chart, market_activity's existing types, or a superset)
- `columns` field semantics (table column definitions vs layout columns vs both with separate fields)
- Data flow approach (direct state access vs pre-resolve via field registry)
- Unknown render_as type handling (skip with warning vs generic fallback table)
- Subsection render failure handling (skip subsection vs fall back to legacy for entire facet)
- Whether to keep legacy `signals` list alongside new `subsections` during migration
- Financial Health signal grouping into subsections (by prefix vs by existing section structure)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The key constraint is that facets orchestrate existing renderers (12K+ lines across 30+ section files), not replace them.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain/facets/*.yaml` (9 facets): Currently have `id`, `name`, `display_type`, `signals` list, `display_config`. market_activity.yaml already has `content` list with `render_as` hints — closest to target format
- `stages/render/sections/sect3_*.py` (4 files, ~1,900 lines): Financial section renderers — these become the functions invoked by facet dispatch for the Financial Health migration
- `stages/render/html_renderer.py` (445 lines): Main HTML orchestrator, builds Jinja2 context and renders — entry point for facet dispatch integration
- `templates/html/sections/financial*.html.j2`: Existing Jinja2 templates for financial sections

### Established Patterns
- Section renderers build context dicts passed to Jinja2 templates — facet renderer follows same pattern
- AnalysisState passed directly to section functions — existing data access pattern
- Phase 55 field registry available for declarative data resolution if needed

### Integration Points
- `html_renderer.py` is where facet dispatch hooks in — currently includes sections via hardcoded template references
- `brain/facets/*.yaml` get the new `subsections` field — Pydantic schema must validate at load time
- `BrainLoader` (from Phase 53) loads facets — needs to handle new subsection schema

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 56-facet-driven-rendering*
*Context gathered: 2026-03-01*
