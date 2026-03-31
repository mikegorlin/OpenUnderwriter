# Phase 76: Output Manifest - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish a single declared output manifest that controls what every worksheet contains, in what order, with manifest-driven rendering replacing hardcoded template includes. The manifest becomes the authority for output structure across all formats (HTML, Word, PDF).

</domain>

<decisions>
## Implementation Decisions

### Manifest structure
- Single manifest YAML with full control over both section order AND facet order within each section
- Existing 12 `brain/sections/*.yaml` files may be composed into or replaced by the manifest — Claude's discretion on approach, as long as it's flexible enough to grow
- Manifest must be versioned (`manifest_version: 1.0`) for schema tracking
- Manifest declares structure (what appears, where); data field requirements live on facets themselves (Phase 79 `requires` blocks)

### Rendering dispatch
- Replace hardcoded `{% include %}` list in `worksheet.html.j2` with a manifest-driven loop — sections rendered dynamically from manifest
- Adding a section = adding to manifest; template auto-renders
- Manifest-driven rendering applies to ALL formats: HTML, Word, and PDF — not just HTML
- Hybrid conditional rendering: sections marked `required` (always render) or `optional` (skip if no data)

### Manifest authority
- Manifest declares both layers: parent section templates (structural wrappers) AND facet sub-templates (content)
- Templates not in manifest are flagged (orphan detection)
- Facets referencing non-existent templates are errors
- Currently: 19 templates not referenced by facets (9 parent wrappers, legacy scoring, cover/identity), 4 facets referencing non-existent templates (executive_risk/)

### Facet typing and data taxonomy
- Facets carry a `data_type` tag matching the data complexity spectrum:
  1. `extract_display` — Pull data, show it (revenue, board size)
  2. `extract_compute` — Pull inputs, apply formula (Altman Z, ratios)
  3. `extract_infer` — Pattern recognition across data points
  4. `hunt_analyze` — Broad search, aggregate, deduplicate, then analyze (litigation)
- This type tag serves: manifest organization, audit trail categorization, and issue diagnosis (know where in the pipeline a gap originated)
- Data display facets always render in main output
- Finding facets render only when signals trigger
- ALL facets appear in the audit trail regardless — confirming they were checked

### Clean data rendering
- Core data always renders in the main output (financials, governance, company profile) even when clean
- If everything is clean, audit trail confirms "checked, no issues"
- Underwriter gets both the information AND the assurance

### Claude's Discretion
- Whether manifest is a new single file composing section YAMLs, or restructures existing files — whichever is most flexible and maintainable
- Manifest = structure only (section+facet presence and order); data field requirements belong on facets (Phase 79)
- Technical approach to manifest-driven rendering loop across HTML/Word/PDF

</decisions>

<specifics>
## Specific Ideas

- User emphasized: "something is displayed because manifest explicitly says that it should be"
- Data complexity spectrum (4 types) should be visible in manifest so debugging is traceable
- Foundational (BASE.*) signals that drive bulk data acquisition must be part of the traceability chain — every data pull traces to a signal declaration
- User wants the manifest to be "flexible enough to change and grow over time"
- Manifest versioning for schema tracking

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain/sections/*.yaml` (12 files): Already declare facets per section with ordering — manifest can compose or extend these
- `brain_section_schema.py`: SectionSpec/FacetSpec Pydantic models, `load_all_sections()` — solid foundation for manifest loading
- `section_renderer.py`: `build_section_context()` already loops over sections and builds facet data — adapt for manifest-driven rendering

### Established Patterns
- Section YAML → Pydantic validation → render context dict — this pattern should extend to manifest
- Jinja2 `{% include %}` for section templates — will be replaced by manifest loop
- `context_builders/` shared functions feed both HTML and Word — manifest dispatch should use these

### Integration Points
- `worksheet.html.j2` lines 8-16: 9 hardcoded includes — primary replacement target
- Word renderer: 28 sections via shared context_builders — needs manifest-driven equivalent
- PDF renderer: Playwright from HTML — inherits HTML changes automatically

### Current Gaps (found during scout)
- 19 templates NOT referenced by any facet (9 parent wrappers, cover, identity, legacy scoring)
- 4 facets referencing NON-EXISTENT templates (executive_risk/ directory)
- 100 facets total, 54 with empty signal lists (Phase 80 scope, not this phase)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 76-output-manifest*
*Context gathered: 2026-03-07*
