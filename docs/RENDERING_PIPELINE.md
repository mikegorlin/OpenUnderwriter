# Rendering Pipeline — How the Worksheet Gets Built

## Overview

The RENDER stage is the final pipeline stage. It takes a fully-populated `AnalysisState` and produces three output formats simultaneously. The rendering system is roughly **22,900 lines** across ~70 Python files plus ~5,600 lines of Jinja2 templates and CSS.

```
AnalysisState
  │
  ├──→ Word (.docx)   — python-docx, primary output, always runs
  ├──→ HTML + PDF      — Jinja2 templates → Playwright Chromium → PDF
  └──→ Markdown (.md)  — Jinja2 templates, shared context with HTML
```

**Key design decision:** Word is the only non-optional output. HTML/PDF and Markdown are wrapped in error isolation — their failures never abort the pipeline.

---

## The Three Rendering Paths

### How They Share (and Don't Share) Data

This is the most important thing to understand about the rendering system:

```
                    AnalysisState
                         │
                         ▼
              build_template_context()     ← Markdown renderer builds this
                    (base context dict)
                         │
                ┌────────┼────────┐
                │        │        │
                ▼        ▼        ▼
           Markdown   HTML adds   Word reads
           templates  more fields state.* directly
                      on top
```

- **Markdown** and **HTML** share a base context dict (built by `build_template_context()` in `md_renderer.py`)
- **HTML** extends that context with HTML-specific fields (base64 charts, footnotes, section_context, etc.)
- **Word** does NOT use the context dict — it reads `state.*` directly through typed Pydantic access

This means **a new data field must be added in up to three places**: the extract function, the HTML/MD template, and the Word section renderer.

---

## Word Document Pipeline

### Orchestrator: `word_renderer.py` (413 lines)

`render_word_document()` builds the .docx:

1. Creates `Document()`, applies custom styles, sets margins (0.75in)
2. Adds header (company name + date) and footer (confidentiality + page number)
3. Adds title page with logo
4. Adds Table of Contents field
5. Iterates 10 sections, each wrapped with a gold divider

### Section Renderers

Each section is a separate module that reads from `state.*` directly:

| Section | Module | Lines | What it renders |
|---------|--------|-------|-----------------|
| 1. Executive Summary | `sect1_executive.py` | 240 | Risk snapshot, tier, key findings, underwriting thesis |
| 2. Company Profile | `sect2_company.py` | 383 | Business description, structure, geographic footprint |
| 3. Financial Health | `sect3_financial.py` | 467 | Statements, distress models, debt, audit, earnings quality |
| 4. Market & Trading | `sect4_market.py` | 446 | Stock charts, short interest, insider activity, options |
| 5. Governance | `sect5_governance.py` | 418 | Board, executives, compensation, ownership |
| 6. Litigation | `sect6_litigation.py` | 442 | SCAs, SEC enforcement, derivative suits, regulatory |
| 7. Scoring | `sect7_scoring.py` | 473 | 10-factor scorecard, patterns, allegations, tower |
| 8. AI Risk | `sect8_ai_risk.py` | 457 | AI transformation risk assessment |
| Calibration | `sect_calibration.py` | — | Data quality notes, signal coverage |
| Meeting Prep | `meeting_prep.py` | 304 | Underwriting meeting questions |

Each renderer follows the same pattern: one public `render_sectionN()` function calling a sequence of private `_render_*()` functions that add paragraphs, tables, and charts to the `Document` object.

### Shared Utilities: `docx_helpers.py` (331 lines)

All Word renderers use: `add_styled_table()`, `add_sourced_paragraph()`, `add_risk_indicator()`, `set_cell_shading()`, `add_section_divider()`.

### Design System: `design_system.py` (246 lines)

`DesignSystem` is a frozen dataclass — single source of truth for all visual constants:

- **Brand colors:** Navy `#1A1446`, Gold `#FFD000`
- **Risk spectrum** (no green — "nothing is safe in underwriting"): CRITICAL `#CC0000`, HIGH `#E67300`, ELEVATED `#FFB800`, MODERATE/LOW `#4A90D9` (blue)
- **Typography:** Georgia headings, Calibri body, Consolas citations
- **Two chart palettes:** `BLOOMBERG_DARK` (HTML dashboard), `CREDIT_REPORT_LIGHT` (PDF/Word)

---

## HTML/PDF Pipeline

### Context Building: `html_renderer.py` (451 lines)

**`build_html_context(state, chart_dir)`** is the data transformation hub. It calls `build_template_context()` (from MD renderer) as the base, then adds HTML-specific fields:

| Context field | Source | Purpose |
|---|---|---|
| `company`, `financials`, `market`, etc. | `build_template_context()` (base) | Core data for all sections |
| `section_context` | `build_section_context()` | Brain-driven facet dispatch |
| `chart_images` | `_load_chart_images()` | Base64-encoded PNGs |
| `signal_results_by_section` | `_group_signals_by_section()` | QA audit appendix |
| `coverage_stats` | `_compute_coverage_stats()` | Coverage appendix |
| `footnote_registry` | `build_footnote_registry()` | Source citation numbers |
| `densities` | `state.analysis.section_densities` | Section alert banners |
| `narratives` | `state.analysis.pre_computed_narratives` | LLM-generated prose |
| `sector` | Re-derived from SIC code at render time | Fixes stale state |
| `factor_breakdown`, `ceiling_line` | `sect1_executive_tables` | Executive summary tables |

**Pain point:** This function is 167 lines of sequential context assembly — every new field gets added here, making it grow without bound.

### Template Structure

**Base template:** `base.html.j2` (178 lines) provides:
- Inline pre-compiled Tailwind CSS + custom styles
- Sticky top bar with company name, ticker, sector, market cap
- Two-column layout: sticky sidebar TOC + main content area
- Print media styles
- IntersectionObserver JS for sidebar active-section tracking

**Worksheet:** `worksheet.html.j2` (22 lines) includes 13 sections in order:

```
sections/identity.html.j2
sections/executive.html.j2
sections/red_flags.html.j2
sections/financial.html.j2
sections/market.html.j2
sections/governance.html.j2
sections/litigation.html.j2
sections/ai_risk.html.j2
sections/scoring.html.j2
appendices/meeting_prep.html.j2
appendices/sources.html.j2
appendices/qa_audit.html.j2
appendices/coverage.html.j2
```

### Facet-Driven Section Dispatch (Phase 56)

Every major section template follows this pattern:

```jinja2
{% if section_context is defined and section_context.get('financial_health') %}
  {% for facet in section_context.financial_health.facets %}
    {% include facet.template %}
  {% endfor %}
{% else %}
  {# Legacy fallback — explicit fragment includes #}
  {% include "sections/financial/annual_comparison.html.j2" %}
  ...
{% endif %}
```

The brain's `sections/*.yaml` files define which facets appear in which order, and each facet has a `template` path. This means the brain controls what renders where.

### Fragment Templates (~82 total)

Each major section is decomposed into fragment templates:

| Section | Fragments | Directory |
|---------|-----------|-----------|
| Financial Health | 11 | `sections/financial/` |
| Governance | 9 | `sections/governance/` |
| Market | 9 | `sections/market/` |
| Company | 8 | `sections/company/` |
| Litigation | 11 | `sections/litigation/` |
| AI Risk | 5 | `sections/ai_risk/` |
| Executive Summary | 7 | `sections/executive/` |
| Scoring | 18 | `sections/scoring/` |

### Component Macros

Five reusable macro files in `templates/html/components/`:

- **`badges.html.j2`** (169 ln): `traffic_light()`, `density_indicator()`, `confidence_marker()`, `tier_badge()`, `check_summary()`
- **`tables.html.j2`** (219 ln): `data_table()`, `kv_table()`, `spectrum_bar()`, `data_row()`, `financial_row()`, `conditional_cell()`
- **`callouts.html.j2`** (58 ln): `discovery_box()`, `warning_box()`, `do_context()`, `gap_notice()`
- **`charts.html.j2`**: `embed_chart()`
- **`narratives.html.j2`** (67 ln): `section_narrative()`, `evidence_chain()`

### CSS Architecture

| File | Lines | Purpose |
|------|-------|---------|
| `input.css` | 81 | Tailwind v4 source with `@theme` design tokens |
| `compiled.css` | — | Pre-compiled Tailwind with base64-inlined fonts |
| `styles.css` | 568 | Bloomberg-inspired custom CSS (risk colors, data grids, KV tables, print styles) |
| `sidebar.css` | 130 | Two-column CapIQ layout |

Built via `bash scripts/build-css.sh --embed`. The compiled CSS has fonts inlined so HTML works from `file://` (no CDN).

### Custom Jinja2 Filters

15+ custom filters registered in `_render_html_template()`:

`format_currency`, `format_pct`, `na_if_none`, `risk_class`, `format_acct`, `format_adaptive`, `yoy_arrow`, `format_na`, `format_em`, `humanize`, `strip_md`, `humanize_theory`, `humanize_field`, `humanize_impact`, `humanize_evidence`, `strip_cyber`, `narratize`

### PDF Generation

`render_html_pdf()` renders HTML → saves `.html` → uses Playwright (headless Chromium) to print-to-PDF:
- Letter format, 0.75in/0.65in margins
- Running header/footer templates
- Falls back to WeasyPrint, then returns `None`

---

## Markdown Pipeline

### Orchestrator: `md_renderer.py` (412 lines)

Uses Jinja2 with `StrictUndefined` (missing variables fail loudly). Templates in `templates/markdown/`.

**`build_template_context()`** is the shared base context builder used by BOTH Markdown and HTML:

| Context key | Source function | Module |
|---|---|---|
| `company` | `extract_company()` | `md_renderer_helpers_narrative.py` |
| `executive_summary` | `extract_exec_summary()` | `md_renderer_helpers_narrative.py` |
| `financials` | `extract_financials()` | `md_renderer_helpers_financial_income.py` |
| `market` | `extract_market()` | `md_renderer_helpers_tables.py` |
| `governance` | `extract_governance()` | `md_renderer_helpers_governance.py` |
| `litigation` | `extract_litigation()` | `md_renderer_helpers_ext.py` |
| `scoring` | `extract_scoring()` | `md_renderer_helpers_scoring.py` |
| `ai_risk` | `extract_ai_risk()` | `md_renderer_helpers_scoring.py` |
| `classification` | `extract_classification()` | `md_renderer_helpers_analysis.py` |
| `hazard_profile` | `extract_hazard_profile()` | `md_renderer_helpers_analysis.py` |
| `forensic_composites` | `extract_forensic_composites()` | `md_renderer_helpers_analysis.py` |
| `executive_risk` | `extract_executive_risk()` | `md_renderer_helpers_analysis.py` |
| `peril_map` | `extract_peril_map()` | `md_renderer_helpers_analysis.py` |
| Narratives (6 sections) | `*_narrative()` | `md_narrative.py`, `md_narrative_sections.py` |
| `triggered_checks` | `_extract_check_findings()` | `md_renderer.py` |
| `calibration_notes` | `render_calibration_notes()` | `md_renderer_helpers_calibration.py` |

### Extraction Helpers (split for 500-line rule)

The extraction logic is spread across many files:

| File | Lines | What it extracts |
|------|-------|-----------------|
| `md_renderer_helpers_narrative.py` | 324 | Company profile, executive summary |
| `md_renderer_helpers_financial_income.py` | 419 | Financial statements and metrics |
| `md_renderer_helpers_tables.py` | 273 | Market data |
| `md_renderer_helpers_governance.py` | 374 | Governance data |
| `md_renderer_helpers_ext.py` | 495 | Litigation (approaching 500-line limit) |
| `md_renderer_helpers_scoring.py` | 411 | Scoring, AI risk, meeting questions |
| `md_renderer_helpers_analysis.py` | 477 | Classification, hazard, forensics, NLP, peril map |
| `md_renderer_helpers_calibration.py` | 218 | Calibration notes |
| `md_narrative.py` | 368 | Financial, market, insider narratives |
| `md_narrative_sections.py` | 494 | Company, governance, litigation, scoring narratives |
| `md_narrative_helpers.py` | 279 | Narrative helper utilities |

---

## Brain-Driven Section Configuration

### Section YAML Files

**Location:** `src/do_uw/brain/sections/` — 12 YAML files

Each defines a `SectionSpec` with ordered `FacetSpec` entries:

```yaml
# brain/sections/financial_health.yaml
id: financial_health
name: Financial Health
display_type: metric_table
signals: [FIN.ACCT.auditor, FIN.LIQ.current_ratio, ...]  # 58 signals
facets:
  - id: annual_comparison
    name: Annual Financial Comparison
    render_as: financial_table
    template: sections/financial/annual_comparison.html.j2
    signals: [...]
  - id: key_metrics
    name: Key Financial Metrics
    render_as: kv_table
    template: sections/financial/key_metrics.html.j2
    ...
```

### Section Renderer: `section_renderer.py` (75 lines)

`build_section_context()` loads all section YAMLs and builds a dispatch dict consumed by templates:

```python
{
  "financial_health": {
    "section": SectionSpec,
    "facets": [
      {"id": "annual_comparison", "name": "...", "template": "sections/financial/annual_comparison.html.j2", ...},
      ...
    ]
  },
  "governance": { ... },
  ...
}
```

### FacetSpec Fields

- `id` — unique within section
- `name` — display heading
- `render_as` — dispatch type hint (currently metadata-only; templates self-render)
- `signals` — which signals this facet displays
- `template` — Jinja2 template path

---

## Chart Generation

Four chart generators in `stages/render/charts/`, all output BytesIO PNG buffers:

| Chart | Module | What it shows |
|-------|--------|---------------|
| Stock 1Y/5Y | `stock_charts.py` (479 ln) | Stock vs SPY vs sector ETF with drop annotations |
| Radar | `radar_chart.py` | 10-factor risk spider chart |
| Ownership | `ownership_chart.py` (183 ln) | Institutional ownership donut |
| Timeline | `timeline_chart.py` (220 ln) | Litigation event timeline |

Charts are data-hash cached — regeneration is skipped if price data hasn't changed.

---

## Complete Data Flow

```
AnalysisState
│
├── state.company              → extract_company()         → company{}
├── state.executive_summary    → extract_exec_summary()    → executive_summary{}
├── state.extracted.financials → extract_financials()      → financials{}
├── state.extracted.market     → extract_market()          → market{}
├── state.extracted.governance → extract_governance()      → governance{}
├── state.extracted.litigation → extract_litigation()      → litigation{}
├── state.scoring              → extract_scoring()         → scoring{}
├── state.classification       → extract_classification()  → classification{}
├── state.analysis.signal_results
│                              → _extract_check_findings() → triggered_checks{}
│                              → _group_signals_by_section → signal_results_by_section{}
│
├── state.analysis.section_densities              → densities{}
├── state.analysis.pre_computed_narratives        → narratives{}
├── state.acquired_data.filing_documents          → footnote_registry, chart images
│
├── brain/sections/*.yaml      → build_section_context()   → section_context{}
│
└── All above → build_template_context() → build_html_context()
               → _render_html_template()
               → worksheet.html.j2
               → sections/{section}.html.j2
               → sections/{section}/{facet}.html.j2
```

---

## Where the Pain Points Are

### 1. Three Parallel Paths, Diverged

The biggest structural issue. Word, HTML, and Markdown each have their own rendering logic:

- **Word** reads `state.*` directly through Python objects
- **HTML/Markdown** transform `state.*` into context dicts, then feed to Jinja2

Adding a new field means touching:
1. The `extract_*()` function (for MD/HTML context)
2. The Jinja2 template (HTML) and/or Markdown template
3. The `sect*_*.py` Word renderer

There is no shared "section rendering interface" — each path does its own thing.

### 2. Context Building is a Growing Monolith

`build_html_context()` is 167 lines of sequential field assignment. `build_template_context()` is similar. Every new piece of data adds another line. There's no structured pattern for declaring "this section needs these fields."

The facet dispatch system (Phase 56) was designed to eventually solve this — each facet knows its signals, so it could theoretically declare its data needs. But today the templates still read from the flat context dict rather than from per-facet data.

### 3. Extract Functions Are At Their Limits

Several extract functions are at or near the 500-line limit:
- `extract_litigation()` — 490 lines, also builds HTML compatibility aliases
- `md_renderer_helpers_analysis.py` — 477 lines with 8 extract functions
- `md_narrative_sections.py` — 494 lines

These can't grow further without splitting again.

### 4. `render_as` Is Unused

`FacetSpec.render_as` (e.g., `financial_table`, `kv_table`, `scorecard`) is defined in YAML but templates ignore it — each fragment template does its own layout. This field could power a generic component dispatch system but today is just documentation.

### 5. Sector Re-Derivation in 4 Places

`sic_to_sector()` is called in `build_html_context()`, `extract_exec_summary()`, `extract_company()`, and `extract_classification()` to fix stale `state.company.sector`. Any new render path must remember to re-derive.

### 6. No Shared Section Abstraction

Each Word section renderer is 400-470 lines of custom code. The HTML fragments are 82 separate Jinja2 files. There's no shared abstraction like "render a KV table with these fields" that works across both Word and HTML. The `render_as` field on FacetSpec was meant to enable this but hasn't been wired up.

### 7. CSS Over Limit

`styles.css` is 568 lines (over the 500-line project rule). It was already split from `sidebar.css` but the main file is still too long.

### 8. Word/HTML Structural Divergence

Word sections are numbered 1-8 with specific heading strings. HTML uses `id` attributes and sidebar TOC. The section numbering, ordering, and naming aren't declared in one place — they're separately hardcoded in the Word renderer and the HTML template.

### 9. Template-Code Boundary Is Fuzzy

Some formatting logic lives in Python (`format_na()`, `format_currency()`), some in Jinja2 filters, some in Jinja2 macros, and some inline in templates. The `format_na` filter behaves differently from the `na_if_none` filter (one returns HTML spans, one returns plain text), and templates must use the right one.

### 10. Chart Image Loading Cross-Module Leak

`build_html_context` calls `_load_chart_images()` from `pdf_renderer.py` — a private function from another module. Chart loading belongs to the HTML context builder, not the PDF renderer.

---

## File Inventory

### Python (stages/render/)

| Category | Files | Total Lines |
|----------|-------|-------------|
| Orchestration | 4 (`__init__`, `html_renderer`, `md_renderer`, `word_renderer`) | ~1,645 |
| Word sections | 10 (`sect1` through `sect8` + calibration + meeting_prep) | ~3,870 |
| Word section helpers | 13 (`sect3_tables`, `sect7_scoring_perils`, etc.) | ~3,600 |
| MD extraction helpers | 11 (various `md_renderer_helpers_*`) | ~4,140 |
| MD narrative helpers | 3 (`md_narrative*`) | ~1,141 |
| Formatters | 3 (`formatters*`) | ~875 |
| HTML helpers | 3 (`html_signals`, `html_footnotes`, `html_renderer`) | ~879 |
| Charts | 5 (`stock_charts`, `radar`, `ownership`, `timeline`, `chart_helpers`) | ~1,075 |
| Section/facet renderer | 3 (`section_renderer`, `facet_renderer`, `design_system`) | ~404 |
| Other | 6 (calibration, docx_helpers, pdf_renderer, etc.) | ~1,200 |
| **Total** | **~61** | **~18,829** |

### Jinja2 Templates (templates/html/)

| Category | Files | Total Lines |
|----------|-------|-------------|
| Base + worksheet | 2 | ~200 |
| Section templates | 9 | ~700 |
| Fragment templates | 82 | ~3,500 |
| Component macros | 5 | ~512 |
| Appendix templates | 4 | ~300 |
| CSS | 4 | ~780 |
| **Total** | **~106** | **~5,992** |

### Brain Section YAMLs

| File | Facets |
|------|--------|
| `financial_health.yaml` | 11 |
| `governance.yaml` | 9 |
| `scoring.yaml` | 18 |
| `executive_summary.yaml` | 7 |
| `litigation.yaml` | 11 |
| `business_profile.yaml` | 8 |
| `market_activity.yaml` | 9 |
| `ai_risk.yaml` | 5 |
| `red_flags.yaml` | — |
| **Total** | **~82** |
