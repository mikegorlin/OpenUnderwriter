# Phase 56: Facet-Driven Rendering - Research

**Researched:** 2026-03-01
**Domain:** Template dispatch, facet schema extension, HTML rendering orchestration
**Confidence:** HIGH

## Summary

Phase 56 adds a structural orchestration layer between facet YAML definitions and existing HTML section templates. The core pattern is: facet YAML files gain a `subsections` list that declares WHAT renders and in what order; a thin `facet_renderer.py` dispatches each subsection's `render_as` type to existing Jinja2 templates/macros. This is NOT a rewrite of 4,000+ lines of rendering logic -- it is a dispatch wrapper that replaces the hardcoded `{% include "sections/financial.html.j2" %}` in `worksheet.html.j2` with a facet-driven equivalent for migrated facets.

The existing codebase has strong foundations for this: `market_activity.yaml` already has a `content` list with `render_as` hints (Phase 50), `FacetSpec` Pydantic schema already validates facet YAML with `content: list[FacetContentRef]`, and all HTML section templates use composable Jinja2 macros (`kv_table`, `data_grid`, `data_table`, `check_summary`, `financial_row`, etc.) from `components/*.html.j2`. The existing pattern of `build_html_context()` building a flat dict consumed by Jinja2 templates is preserved -- the facet renderer just adds a routing layer on top.

Financial Health is the migration target (58 signals, 9 sub-prefixes, 449-line template). The existing template naturally decomposes into ~10 subsections matching `<h3>` headings: Annual Financial Comparison, Key Financial Metrics, Financial Statements, Quarterly Updates, Distress Model Indicators, Tax Risk, Earnings Quality, Audit Profile, Peer Group, and Financial Checks. Each maps to a `render_as` type and an existing template fragment or macro invocation.

**Primary recommendation:** Build a thin facet renderer that dispatches subsections to template fragments, keeping all existing context-building and macro logic untouched. The dispatch mechanism is presence of `subsections` key in facet YAML (per CONTEXT.md decision). Use `{% include %}` with dynamic template selection in Jinja2 to route each subsection.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Extend existing `content` pattern from market_activity.yaml -- rename `content` to `subsections`, add `id`, `name`, `columns` fields to each entry
- Each subsection entry has explicit `signals` list (not auto-grouped by prefix) -- clear, no magic
- `render_as` field per subsection controls template dispatch (already exists in market_activity `content`)
- Thin orchestrator pattern: `facet_renderer.py` calls existing section functions (sect3_financial.py, etc.), but facet YAML controls WHICH subsections appear and in WHAT order
- Section .py functions still do the heavy lifting -- facet renderer is a glue/dispatch layer
- HTML rendering only for Phase 56 -- Word/Markdown renderers remain completely untouched
- Financial Health is the first facet to fully migrate (58 signals, heaviest, matches RENDER-03 suggestion)
- "No hardcoded renderer involvement" = facet orchestrates, section functions stay -- facet dispatch replaces hardcoded template includes, but existing rendering functions are still invoked by the dispatcher
- Verification: HTML diff on a real ticker (e.g., SNA) before/after migration -- visual output must match
- Dispatch mechanism: presence of `subsections` key in facet YAML -- if present, use facet renderer; if absent, fall through to legacy hardcoded section template
- Per-section mixed mode: a single document can have BOTH facet-rendered and legacy-rendered sections side by side (essential for incremental migration)

### Claude's Discretion
- Exact `render_as` type taxonomy (whether to use RENDER-01's kv_table/scorecard/narrative/chart, market_activity's existing types, or a superset)
- `columns` field semantics (table column definitions vs layout columns vs both with separate fields)
- Data flow approach (direct state access vs pre-resolve via field registry)
- Unknown render_as type handling (skip with warning vs generic fallback table)
- Subsection render failure handling (skip subsection vs fall back to legacy for entire facet)
- Whether to keep legacy `signals` list alongside new `subsections` during migration
- Financial Health signal grouping into subsections (by prefix vs by existing section structure)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RENDER-01 | Facets define subsections with layout specs -- each facet YAML gains `subsections` list with `id`, `name`, `render_as` (kv_table/scorecard/narrative/chart), `signals`, `columns` | FacetSpec schema extension pattern, SubsectionSpec Pydantic model, financial_health.yaml subsection mapping |
| RENDER-02 | Facet renderer orchestrates existing templates -- `render_facet_section()` dispatches to existing Jinja2 section templates based on `render_as` type | facet_renderer.py architecture, dispatch pattern using Jinja2 `{% include %}`, existing macro reuse |
| RENDER-03 | At least one facet fully migrated -- Financial Health renders entirely from facet YAML subsections | Financial Health decomposition into 10 subsections, template fragment extraction, zero-regression verification |
| RENDER-04 | Legacy fallback preserved -- facets without `subsections` use existing hardcoded section renderers | Dispatch mechanism in worksheet.html.j2, conditional facet-vs-legacy routing |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | SubsectionSpec schema validation at load time | Already used for FacetSpec, BrainSignalEntry; project standard |
| Jinja2 | 3.x | Template dispatch via `{% include %}` with variable path | Already the template engine; supports dynamic includes |
| PyYAML | 6.x | Facet YAML loading (CSafeLoader for speed) | Already used via `yaml.safe_load` in brain_facet_schema.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test facet schema validation, dispatch routing, regression | Existing test infrastructure with 3,967+ tests |
| difflib | stdlib | HTML diff for zero-regression verification | Side-by-side comparison of legacy vs facet-rendered output |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 dynamic include | Python-side template selection + render | Keeps logic in Python but loses Jinja2 macro context; existing macros need Jinja2 environment |
| New subsection templates | Inline Jinja2 blocks in facet_section.html.j2 | Cleaner separation vs single-file complexity; templates preferred for subsections > 20 lines |

**Installation:** No new dependencies. All libraries already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
├── brain/
│   ├── facets/
│   │   ├── financial_health.yaml       # Extended with subsections
│   │   ├── market_activity.yaml        # content -> subsections rename (future)
│   │   └── *.yaml                      # Other facets (no subsections yet)
│   └── brain_facet_schema.py           # Extended with SubsectionSpec
├── stages/render/
│   ├── facet_renderer.py               # NEW: thin dispatch orchestrator (~150 lines)
│   ├── html_renderer.py                # Modified: passes facets to context
│   └── sections/
│       └── sect3_*.py                  # UNCHANGED: existing section renderers
├── templates/html/
│   ├── worksheet.html.j2              # Modified: conditional facet-vs-legacy routing
│   ├── sections/
│   │   ├── financial.html.j2           # Split into subsection fragments
│   │   └── financial/                  # NEW directory for subsection fragments
│   │       ├── annual_comparison.html.j2
│   │       ├── key_metrics.html.j2
│   │       ├── financial_statements.html.j2  # Move from sections/
│   │       ├── quarterly_updates.html.j2
│   │       ├── distress_indicators.html.j2
│   │       ├── tax_risk.html.j2
│   │       ├── earnings_quality.html.j2
│   │       ├── audit_profile.html.j2
│   │       ├── peer_group.html.j2
│   │       └── financial_checks.html.j2
│   └── facet_section.html.j2          # NEW: facet dispatch wrapper template
```

### Pattern 1: Facet Subsection Schema Extension
**What:** Extend FacetSpec with optional `subsections` field containing SubsectionSpec models.
**When to use:** Every facet YAML that participates in facet-driven rendering.

```python
# Source: brain_facet_schema.py extension
class SubsectionSpec(BaseModel):
    """Schema for a subsection within a facet."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique subsection ID within facet (e.g., 'annual_comparison')")
    name: str = Field(description="Display name for subsection heading (e.g., 'Annual Financial Comparison')")
    render_as: str = Field(description="Template dispatch type: financial_table, kv_table, scorecard, narrative, data_grid, check_summary")
    signals: list[str] = Field(default_factory=list, description="Signal IDs this subsection displays")
    columns: list[str] = Field(default_factory=list, description="Column definitions for table render types")
    template: str = Field(default="", description="Override template path (optional; default derived from render_as)")


class FacetSpec(BaseModel):
    # ... existing fields ...
    subsections: list[SubsectionSpec] = Field(
        default_factory=list,
        description="Ordered subsection specs for facet-driven rendering. If empty, legacy rendering used."
    )
```

**Confidence:** HIGH -- follows existing FacetContentRef pattern, validated by Pydantic at load time.

### Pattern 2: Dispatch in worksheet.html.j2
**What:** Conditional routing between facet-rendered and legacy-rendered sections.
**When to use:** The master template decides per-section whether to use facet or legacy rendering.

```jinja2
{# In worksheet.html.j2-- replace hardcoded include with conditional dispatch #}
{% if facets.financial_health and facets.financial_health.subsections %}
  {% include "facet_section.html.j2" with context %}
{% else %}
  {% include "sections/financial.html.j2" %}
{% endif %}
```

However, this approach has a complexity problem: each section would need its own if/else, and `facet_section.html.j2` needs to know WHICH facet to render. A cleaner approach:

```jinja2
{# Cleaner: use a macro that checks each facet #}
{% for section in render_sections %}
  {% if section.facet_driven %}
    {% include section.template %}
  {% else %}
    {% include section.legacy_template %}
  {% endif %}
{% endfor %}
```

**Recommended approach:** Keep the explicit section includes in worksheet.html.j2 but wrap the financial section specifically with a facet check. This preserves the simple, readable template structure while enabling per-section migration.

```jinja2
{# worksheet.html.j2 -- minimal change for Phase 56 #}
{% if facet_sections and 'financial_health' in facet_sections %}
  {% include "facet_section.html.j2" %}
{% else %}
  {% include "sections/financial.html.j2" %}
{% endif %}
```

**Confidence:** HIGH -- Jinja2 `{% include %}` with context is well-understood and already used throughout.

### Pattern 3: Facet Renderer Python Module
**What:** `facet_renderer.py` builds the facet dispatch context for Jinja2.
**When to use:** Called from `build_html_context()` in html_renderer.py.

```python
# Source: facet_renderer.py (new file, ~150 lines)
from do_uw.brain.brain_facet_schema import FacetSpec, load_all_facets

def build_facet_context(state: AnalysisState) -> dict[str, Any]:
    """Build facet dispatch context for HTML rendering.

    Returns dict with:
    - facet_sections: dict of facet_id -> {subsections: [...], context: {...}}
      Only includes facets that have subsections defined.
    """
    facets = load_all_facets(BRAIN_FACETS_DIR)
    facet_sections = {}

    for facet_id, facet in facets.items():
        if not facet.subsections:
            continue  # Legacy rendering -- skip

        subsection_data = []
        for sub in facet.subsections:
            template = sub.template or f"sections/financial/{sub.id}.html.j2"
            subsection_data.append({
                "id": sub.id,
                "name": sub.name,
                "render_as": sub.render_as,
                "signals": sub.signals,
                "columns": sub.columns,
                "template": template,
            })

        facet_sections[facet_id] = {
            "facet": facet,
            "subsections": subsection_data,
        }

    return {"facet_sections": facet_sections}
```

**Confidence:** HIGH -- follows existing pattern of `build_html_context()` adding context dicts.

### Pattern 4: Subsection Template Fragments
**What:** Extract each `<h3>` block from financial.html.j2 into standalone template fragments.
**When to use:** Each subsection becomes a separate `.html.j2` file that can be included by the facet dispatcher.

The existing financial.html.j2 (449 lines) naturally decomposes into fragments at `<h3>` boundaries:

| Current Block | Lines | Fragment File | render_as |
|---------------|-------|---------------|-----------|
| Section heading + narrative | 1-17 | (section wrapper in facet_section.html.j2) | section_header |
| Annual Financial Comparison | 18-57 | annual_comparison.html.j2 | financial_table |
| Key Financial Metrics | 59-93 | key_metrics.html.j2 | data_grid |
| Financial Statements | 95-96 (include) | financial_statements.html.j2 (already exists) | statement_tables |
| Quarterly Updates | 98-290 | quarterly_updates.html.j2 | financial_table |
| Distress Model Indicators | 292-342 | distress_indicators.html.j2 | scorecard |
| Tax Risk Profile | 344-360 | tax_risk.html.j2 | kv_table |
| Earnings Quality | 362-375 | earnings_quality.html.j2 | kv_table |
| Audit Profile | 377-401 | audit_profile.html.j2 | kv_table |
| Peer Group | 403-415 | peer_group.html.j2 | data_table |
| Financial Checks | 417-422 | financial_checks.html.j2 | check_summary |
| Density deep dive | 424-448 | density_alerts.html.j2 | conditional_alert |

Each fragment must work with the same template context that financial.html.j2 currently receives (the `fin` dict, `density`, `narratives`, `signal_results_by_section`, `footnote_registry`). No context changes needed -- fragments just get narrower scope from the same context.

**Confidence:** HIGH -- mechanical extraction of existing template blocks.

### Pattern 5: facet_section.html.j2 Dispatch Template
**What:** A Jinja2 template that iterates over a facet's subsections and includes each fragment.

```jinja2
{# facet_section.html.j2 -- iterates facet subsections, dispatches to templates #}
{% set facet_data = facet_sections[current_facet_id] %}
{% set facet = facet_data.facet %}

<section id="{{ facet.id }}" class="page-break">
  {{ density_indicator(level) }}
  <h2>Section 3: {{ facet.name }}</h2>

  {# Section narrative #}
  {% set narr = narratives.financial if narratives else none %}
  {{ section_narrative(narr, ai_generated=true) }}

  {# Dispatch each subsection to its template #}
  {% for sub in facet_data.subsections %}
    {% include sub.template ignore missing %}
  {% endfor %}
</section>
```

**Confidence:** HIGH -- Jinja2 `{% include variable_name %}` is supported and `ignore missing` provides graceful degradation.

### Anti-Patterns to Avoid
- **Rebuilding context inside facet renderer:** Do NOT re-extract financial data in facet_renderer.py. The existing `extract_financials(state)` and `build_html_context()` already provide everything. The facet renderer only adds dispatch metadata.
- **Replacing existing macros with new ones:** Do NOT create new table/chart macros. Subsection fragments use the same `kv_table`, `data_grid`, `financial_row`, `check_summary` macros already imported in base.html.j2.
- **Dynamic template path construction without validation:** Always validate that `render_as` maps to a known template path. Log warnings for unknown types rather than crashing.
- **Modifying Word/Markdown renderers:** Phase 56 is HTML-only. The sect3_financial.py Word renderer is completely untouched.
- **All-or-nothing facet migration:** The dispatch mechanism is per-section, not per-document. A single document can have Financial Health from facets and all other sections from legacy templates.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template context building | New financial data extraction | Existing `extract_financials(state)` in md_renderer_helpers | 200+ lines of battle-tested financial data extraction |
| Table rendering | Custom HTML table generation in Python | Existing Jinja2 macros (kv_table, data_table, data_grid) | 219 lines of macros with consistent Bloomberg styling |
| Signal grouping | New signal-to-section mapping | Existing `_group_signals_by_section()` in html_signals.py | Already uses facet definitions for grouping |
| Conditional formatting | New risk coloring logic | Existing `traffic_light`, `conditional_cell` macros | Consistent with design system, handles all edge cases |
| YAML schema validation | Manual dict parsing | Pydantic SubsectionSpec model | Type-safe, validates at load time, clear error messages |

**Key insight:** The facet renderer is 95% routing and 5% new logic. All heavy lifting is done by existing templates, macros, and context builders.

## Common Pitfalls

### Pitfall 1: Template Context Scope Mismatch
**What goes wrong:** Subsection template fragments reference variables that exist in the parent financial.html.j2 scope (e.g., `fin`, `density`, `level`) but are not available when included from facet_section.html.j2.
**Why it happens:** Jinja2 `{% include %}` shares the calling template's context, but variables set with `{% set %}` at the top of financial.html.j2 (lines 5-7) need to be replicated.
**How to avoid:** The facet_section.html.j2 wrapper must set the same context variables before dispatching subsections:
```jinja2
{% set density = densities.get('financial', {}) %}
{% set level = density.level|default('CLEAN') if density else 'CLEAN' %}
{% set fin = financials or {} %}
```
**Warning signs:** Template errors mentioning undefined variables when rendering via facet dispatch.

### Pitfall 2: Visual Regression from Whitespace/CSS Changes
**What goes wrong:** Splitting a monolithic template into fragments introduces subtle whitespace differences that affect CSS layout (extra blank lines between sections, missing `page-break` classes).
**Why it happens:** Jinja2 whitespace handling varies between `{% include %}` and inline blocks. Fragment boundaries introduce newlines.
**How to avoid:** Run side-by-side HTML diff on SNA output before and after migration. Use `difflib.HtmlDiff` or similar to catch even minor differences. Test print/PDF layout.
**Warning signs:** Extra vertical spacing, missing horizontal rules, broken table alignment.

### Pitfall 3: Existing financial_statements.html.j2 Include Chain
**What goes wrong:** financial.html.j2 line 96 already includes `sections/financial_statements.html.j2`. When extracting subsection fragments, this include must be preserved in the correct subsection fragment, not duplicated.
**Why it happens:** The financial statements template is already split from the main template (Plan 43-03).
**How to avoid:** Map the existing include to a specific subsection (e.g., `statement_tables`) and ensure the fragment either re-includes it or becomes a wrapper around it.
**Warning signs:** Duplicate financial statement tables appearing in output.

### Pitfall 4: FacetContentRef vs SubsectionSpec Confusion
**What goes wrong:** market_activity.yaml already has `content: list[FacetContentRef]` (from Phase 50). The new `subsections` field has a different purpose and schema. Developers may confuse the two.
**Why it happens:** CONTEXT.md says "rename content to subsections" but the existing `content` field references composites (COMP.xxx), while `subsections` controls template dispatch.
**How to avoid:** SubsectionSpec is a distinct Pydantic model from FacetContentRef. The `content` field on FacetSpec is kept for backward compatibility. `subsections` is a new field with its own schema. market_activity.yaml is NOT migrated in Phase 56.
**Warning signs:** Attempting to use FacetContentRef.ref as a template path, or losing composite rendering.

### Pitfall 5: Density/Deep-Dive Conditional Blocks
**What goes wrong:** The financial template has ELEVATED and CRITICAL conditional blocks at the end (lines 424-448) that render additional warnings and deep-dive sections. These are density-driven, not signal-driven, and must be preserved.
**Why it happens:** These blocks don't map to a simple `render_as` type -- they are conditional on the density level computed in the ANALYZE stage.
**How to avoid:** Include density-driven blocks as a special subsection type (e.g., `render_as: conditional_alert`) or include them in the facet_section.html.j2 wrapper after the subsection loop.
**Warning signs:** Missing financial distress deep-dive warnings in output for distressed companies.

### Pitfall 6: Backward-Compatible Legacy Facets
**What goes wrong:** Adding `subsections` field to FacetSpec breaks existing code that only expects `signals` and `content` fields.
**Why it happens:** `FacetSpec` has `model_config = ConfigDict(extra="allow")`, so unknown YAML fields are accepted but not validated. If `subsections` is added to the Pydantic model without default, loading old YAML fails.
**How to avoid:** `subsections: list[SubsectionSpec] = Field(default_factory=list)` -- default to empty list. Only facets with non-empty `subsections` use facet-driven rendering. All 8 other facets continue using legacy rendering unchanged.
**Warning signs:** Pydantic validation errors on startup when loading facets without subsections.

## Code Examples

### Financial Health Facet YAML with Subsections

```yaml
# brain/facets/financial_health.yaml -- extended with subsections
id: financial_health
name: Financial Health
display_type: metric_table
subsections:
  - id: annual_comparison
    name: "Annual Financial Comparison"
    render_as: financial_table
    signals: [FIN.PROFIT.revenue, FIN.PROFIT.earnings, FIN.PROFIT.margins]
    template: sections/financial/annual_comparison.html.j2

  - id: key_metrics
    name: "Key Financial Metrics"
    render_as: data_grid
    signals: [FIN.PROFIT.segment, FIN.LIQ.position, FIN.LIQ.working_capital]
    template: sections/financial/key_metrics.html.j2

  - id: statement_tables
    name: "Financial Statements"
    render_as: statement_tables
    signals: []
    template: sections/financial/financial_statements.html.j2

  - id: quarterly_updates
    name: "Quarterly Updates"
    render_as: financial_table
    signals: []
    template: sections/financial/quarterly_updates.html.j2

  - id: distress_indicators
    name: "Distress Model Indicators"
    render_as: scorecard
    signals: [FIN.FORENSIC.beneish_dechow_convergence, FIN.FORENSIC.dechow_f_score,
              FIN.FORENSIC.fis_composite, FIN.FORENSIC.montier_c_score]
    template: sections/financial/distress_indicators.html.j2

  - id: tax_risk
    name: "Tax Risk Profile"
    render_as: kv_table
    signals: []
    template: sections/financial/tax_risk.html.j2

  - id: earnings_quality
    name: "Earnings Quality"
    render_as: kv_table
    signals: [FIN.QUALITY.cash_flow_quality, FIN.QUALITY.quality_of_earnings,
              FIN.QUALITY.revenue_quality_score]
    template: sections/financial/earnings_quality.html.j2

  - id: audit_profile
    name: "Audit Profile"
    render_as: kv_table
    signals: [FIN.ACCT.auditor, FIN.ACCT.material_weakness, FIN.ACCT.restatement]
    template: sections/financial/audit_profile.html.j2

  - id: peer_group
    name: "Peer Group"
    render_as: data_table
    signals: []
    template: sections/financial/peer_group.html.j2

  - id: financial_checks
    name: "Financial Checks"
    render_as: check_summary
    signals: []
    template: sections/financial/financial_checks.html.j2

  - id: density_alerts
    name: "Density Alerts"
    render_as: conditional_alert
    signals: []
    template: sections/financial/density_alerts.html.j2

# Legacy signals list kept for backward compatibility
signals:
  - FIN.ACCT.auditor
  # ... (all 58 signals)
display_config:
  col_signal: Financial Metric
  col_value: Value
```

### Facet Dispatch in worksheet.html.j2

```jinja2
{# Financial Health: facet-driven or legacy #}
{% if facet_sections and 'financial_health' in facet_sections %}
  {% set current_facet_id = 'financial_health' %}
  {% include "facet_section.html.j2" %}
{% else %}
  {% include "sections/financial.html.j2" %}
{% endif %}
```

### SubsectionSpec Pydantic Model

```python
class SubsectionSpec(BaseModel):
    """Schema for a subsection within a facet YAML."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique subsection ID (e.g., 'annual_comparison')")
    name: str = Field(..., description="Display heading (e.g., 'Annual Financial Comparison')")
    render_as: str = Field(
        ...,
        description="Template dispatch type: financial_table, kv_table, scorecard, "
                    "narrative, data_grid, data_table, check_summary, "
                    "statement_tables, conditional_alert"
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Signal IDs rendered in this subsection (informational, not filtered)"
    )
    columns: list[str] = Field(
        default_factory=list,
        description="Column names for table-type render_as types"
    )
    template: str = Field(
        default="",
        description="Explicit template path override. If empty, derived from render_as + facet_id."
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic section templates | Template fragments per subsection | Phase 56 (this phase) | Facets control section composition |
| Hardcoded section order in worksheet.html.j2 | Facet YAML `subsections` list controls order | Phase 56 | Reordering sections requires YAML edit, not template edit |
| All sections rendered via fixed includes | Mixed mode: facet-driven + legacy | Phase 56 | Incremental migration without regression risk |
| FacetSpec with signals list only | FacetSpec with optional subsections | Phase 56 | Schema stays backward compatible |

**Deprecated/outdated:**
- `content: list[FacetContentRef]` on FacetSpec: Phase 50 approach for composite rendering. Kept for backward compat but not extended. `subsections` is the new declarative rendering path.

## Open Questions

1. **Signal list on subsections: informational or functional?**
   - What we know: CONTEXT.md says "explicit signals list per subsection." The existing financial template does NOT use signal data to render its content -- it uses the `fin` context dict from `extract_financials()`. The `signal_results_by_section` is only used in the Financial Checks subsection.
   - What's unclear: Should the signals list on each subsection actually filter/gate rendering, or is it purely metadata for provenance tracking?
   - Recommendation: Treat signals as informational metadata in Phase 56. The template fragments render from the existing context dict. Signal-driven rendering (where subsection content is dynamically built from signal results) is a Phase 57+ concern.

2. **`columns` field usage for Financial Health**
   - What we know: Financial tables have fixed column structures (Metric/Value/YoY, Model/Score/Assessment, etc.) baked into the existing templates.
   - What's unclear: Should `columns` drive actual table rendering, or is it metadata describing what the existing template renders?
   - Recommendation: Metadata only in Phase 56. Column values describe the existing template structure for documentation. Dynamic column rendering is a future concern for fully declarative facets.

3. **Renaming `content` to `subsections` on market_activity.yaml**
   - What we know: CONTEXT.md says "rename content to subsections." But market_activity.yaml's `content` references composites (COMP.xxx), not template fragments. The schema is different.
   - What's unclear: Should market_activity also be migrated in Phase 56, or just financial_health?
   - Recommendation: Only migrate financial_health in Phase 56. Keep market_activity's `content` field as-is. The `content -> subsections` rename for other facets is future work (REND-01, deferred).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_render_sections_3_4.py tests/stages/render/test_html_renderer.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=30` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RENDER-01 | SubsectionSpec validates at load time; rejects invalid render_as | unit | `pytest tests/test_facet_schema.py::test_subsection_validation -x` | Wave 0 |
| RENDER-01 | financial_health.yaml loads with subsections, Pydantic validates | unit | `pytest tests/test_facet_schema.py::test_financial_health_subsections -x` | Wave 0 |
| RENDER-02 | facet_renderer dispatches to correct template for each render_as type | unit | `pytest tests/test_facet_renderer.py::test_dispatch_render_as -x` | Wave 0 |
| RENDER-02 | facet_renderer gracefully handles unknown render_as | unit | `pytest tests/test_facet_renderer.py::test_unknown_render_as -x` | Wave 0 |
| RENDER-03 | Financial Health renders identically via facet dispatch vs legacy | integration | `pytest tests/test_facet_renderer.py::test_financial_health_regression -x` | Wave 0 |
| RENDER-04 | Facets without subsections use legacy rendering | unit | `pytest tests/test_facet_renderer.py::test_legacy_fallback -x` | Wave 0 |
| RENDER-04 | Mixed mode: facet + legacy sections in same document | integration | `pytest tests/test_facet_renderer.py::test_mixed_mode -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_facet_schema.py tests/test_facet_renderer.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=30`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_facet_schema.py` -- covers RENDER-01 (SubsectionSpec validation)
- [ ] `tests/test_facet_renderer.py` -- covers RENDER-02, RENDER-03, RENDER-04 (dispatch, regression, fallback)
- Framework install: None needed -- pytest already configured

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of 15+ source files across brain/, stages/render/, templates/html/
- `brain_facet_schema.py` (106 lines) -- current FacetSpec/FacetContentRef schema
- `html_renderer.py` (445 lines) -- build_html_context() and render pipeline
- `templates/html/sections/financial.html.j2` (449 lines) -- full financial template structure
- `templates/html/components/tables.html.j2` (219 lines) -- reusable macros
- `brain/facets/financial_health.yaml` -- 58 signals in 9 sub-prefix groups
- `brain/facets/market_activity.yaml` -- existing `content` list with `render_as` hints

### Secondary (MEDIUM confidence)
- Phase 55 RESEARCH.md and completion patterns for migration approach
- CONTEXT.md user decisions for locked architecture choices

### Tertiary (LOW confidence)
- None -- all findings from direct codebase investigation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all libraries already in use
- Architecture: HIGH -- direct codebase analysis, existing patterns provide clear blueprint
- Pitfalls: HIGH -- identified from actual template structure and Jinja2 behavior

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable domain, no external dependency changes expected)
