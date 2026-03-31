# Phase 147: Golden Manifest Wiring - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning
**Source:** Auto-mode (recommended defaults selected)

<domain>
## Phase Boundary

Audit all manifest templates in `output_manifest.yaml` and ensure every one either renders meaningful content from pipeline data or is suppressed with zero DOM output. The "27 recently-added templates" in the roadmap refers to templates added during Phase 132 (Page-0 dashboard work) — the actual manifest has 166 groups across 14 sections, but the focus is on templates that currently render empty or with placeholder content.

</domain>

<decisions>
## Implementation Decisions

### Wiring Strategy
- **D-01:** [auto] Three-tier classification: "renders" (has data, shows content), "wired" (has data path but may be empty for some tickers), "suppressed" (no data path, hidden via `{% if %}` guard). Every template gets exactly one classification.
- **D-02:** [auto] Suppressed templates produce ZERO DOM elements — not hidden divs, not empty cards, not whitespace. Use `{% if data %}...{% endif %}` at the template root level, not CSS display:none.
- **D-03:** [auto] Wiring audit is automated — a test reads the manifest, renders each template with a real state.json, and classifies output as renders/wired/suppressed.

### Data Flow Approach
- **D-04:** [auto] Wire data through existing context builders in `assembly_registry.py` — no new builder files. Add keys to existing builder functions where data already exists in state.
- **D-05:** [auto] For templates where pipeline data doesn't exist yet (adverse events, tariff risk, ESG), add suppression guards now. Don't fake data or create placeholder text. These templates activate when future pipeline stages produce the data.
- **D-06:** [auto] Templates that render analytical content from signals (display_only=true in manifest) should check if any signals fired for their group. If zero signals → suppress entirely.

### Audit & Testing
- **D-07:** [auto] Create `test_manifest_wiring_completeness.py` that loads real state.json, renders each manifest group template, and asserts: (a) renders produce non-empty content, (b) suppressed produce empty string, (c) no template crashes with TypeError/AttributeError.
- **D-08:** [auto] Audit log written to render context as `manifest_audit` dict — available in audit trail section.

### Claude's Discretion
- Order of template wiring within each section
- Whether to merge small related templates into parent sections
- Specific Jinja2 guard expressions for each template
- Whether display-only templates with zero fired signals should show "No concerns identified" vs suppress entirely (recommend: suppress)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Manifest Definition
- `src/do_uw/brain/output_manifest.yaml` — All 166 manifest groups with sections, templates, render_as types, requires clauses
- `src/do_uw/stages/render/section_renderer.py` — How manifest sections connect to builders and templates

### Context Builders
- `src/do_uw/stages/render/context_builders/assembly_registry.py` — Builder registration and dispatch
- `src/do_uw/stages/render/context_builders/assembly_html_extras.py` — Densities, narratives, identity
- `src/do_uw/stages/render/context_builders/assembly_signals.py` — Signal results and audit context
- `src/do_uw/stages/render/context_builders/assembly_dossier.py` — Forward risk, credibility, monitoring

### Templates
- `src/do_uw/templates/html/sections/report/` — All report section templates (the active render path)
- `src/do_uw/templates/html/sections/` — Legacy section templates (some still included)

### Existing Tests
- `tests/stages/render/test_manifest_rendering.py` — Manifest ordering and structure tests
- `tests/brain/test_contract_enforcement.py` — Template-manifest agreement checks

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `assembly_registry.py` `@register_builder` decorator — add new context keys without new files
- `section_renderer.py` `collect_signals_by_group()` — already maps signals to manifest groups
- `test_manifest_rendering.py` — existing test framework for manifest validation

### Established Patterns
- Templates use `{% if data %}` guards at top level for suppression
- Context builders mutate shared `context` dict — keys match template variable names
- Stage failure banners inject after all builders complete
- `null_safe_chart` decorator catches 5 exception types

### Integration Points
- `build_html_context()` in `assembly_registry.py` — add new context keys here
- `output_manifest.yaml` — add/modify `requires:` clauses
- Report templates in `sections/report/` — add suppression guards

</code_context>

<specifics>
## Specific Ideas

- The roadmap mentions "27 recently-added manifest templates" but scout found 166 total groups. Focus on templates added in Phase 132 and any that currently render empty.
- 5 extremely small templates (<200B) are high-risk for empty rendering: subsidiary_structure, workforce_distribution, operational_resilience, statement_tables, ownership_chart
- 103 display-only templates (62%) — these should suppress when zero signals fire for their group
- Scoring section has 82% display-only load — biggest cleanup target

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 147-golden-manifest-wiring*
*Context gathered: 2026-03-28 via auto-mode*
