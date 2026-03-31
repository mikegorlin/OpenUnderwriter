# Phase 73: Rendering & Bug Fixes - Research

**Researched:** 2026-03-06
**Domain:** Jinja2 HTML/PDF template rendering, CSS-only data visualization, false SCA classification bug
**Confidence:** HIGH

## Summary

Phase 73 adds three new rendering components (8-quarter trend table, forensic dashboard, peer percentile display), enhances existing templates (insider trading, Beneish), fixes two bugs (false SCA classification, PDF header overlap), and adds company logo embedding. The project has a mature, well-structured rendering pipeline built during v3.0 (Phases 58-66) with clear patterns for adding new templates.

The rendering system uses Jinja2 templates with inline CSS (Tailwind + custom), facet-driven section dispatch via brain YAML configs, and Playwright for PDF generation. Sparklines are pure SVG (no matplotlib), all charts are CSS-only or server-rendered SVG. The false SCA bug has multiple filtering layers already in place but needs strengthening at the extraction prompt level. The PDF header overlap is a CSS `position:fixed` issue with first-page content spacing.

**Primary recommendation:** Follow existing facet patterns exactly -- new templates are facet additions to `financial_health.yaml` and `market_activity.yaml` with corresponding `.html.j2` files. Bug fixes are surgical: tighten LLM prompt + add scoring filters for false SCA; adjust CSS margins for PDF header overlap.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RENDER-01 | 8-quarter trend table with tabs and sparklines | Existing `quarterly_trend.html.j2` provides base pattern; CSS tab pattern from `financial_statements.html.j2`; sparklines via `render_sparkline()` in `charts/sparklines.py` |
| RENDER-02 | Forensic dashboard with hazard cards | Existing hazard card CSS in `components.css`; color-coded severity pattern from distress indicators facet |
| RENDER-03 | Peer percentile display (CSS-only horizontal bars) | Existing `.percentile-bar` + `.percentile-fill` CSS classes in `components.css` already implement this pattern |
| RENDER-04 | Enhanced insider trading table | Existing `insider_trading.html.j2` facet in `market_activity.yaml`; needs ownership concentration column from Phase 71 data |
| RENDER-05 | Beneish component breakdown | Existing `distress_indicators.html.j2` facet; Beneish data from `financial_models.py` `_compute_beneish_m_score()` |
| RENDER-06 | BUG FIX: False SCA from boilerplate 10-K | `_is_boilerplate_litigation()` in `signal_mappers_ext.py`; `_is_regulatory_not_sca()` in `red_flag_gates.py`; LLM extraction prompt in `prompts.py` |
| RENDER-07 | BUG FIX: PDF header overlap | CSS `position:fixed` header at `top: -0.55in` in `styles.css` @media print; Playwright margin `top: 0.75in`; cover-header div has negative top margin |
| RENDER-08 | Company logo in HTML header | Already partially implemented: `_fetch_company_logo()` in `orchestrator.py`, `company_logo_b64` context var, display in `identity.html.j2` and `base.html.j2` topbar |
| RENDER-09 | All templates work in HTML and PDF | PDF via Playwright; `pdf_mode` context flag; `@media print` CSS; `<details>` auto-expansion |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.x | HTML template rendering | Already used for all templates |
| Playwright | 1.x | PDF generation from HTML | Already used for PDF rendering |
| Pure SVG | N/A | Sparklines and inline charts | Established pattern in `charts/sparklines.py` |
| CSS-only | N/A | Tabs, percentile bars, hazard cards | No JS dependencies per project convention |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tailwind CSS | v4 | Utility classes | Pre-compiled, all utilities available |
| Custom CSS | N/A | components.css, styles.css, charts.css | Component-level styling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SVG sparklines | matplotlib sparklines | matplotlib is overkill for inline trends; SVG is lighter |
| CSS-only tabs | JavaScript tabs | No JS in charts/viz per project convention (CHART-06 decision) |
| CSS percentile bars | SVG bars | Existing CSS pattern already in components.css; simpler |

## Architecture Patterns

### Template Structure (Existing -- Follow Exactly)
```
src/do_uw/
  templates/html/
    base.html.j2          # Layout + CSS includes + macros
    worksheet.html.j2     # Section ordering
    sections/
      financial.html.j2   # Parent section template (includes facets)
      financial/
        annual_comparison.html.j2   # Facet template
        quarterly_trend.html.j2     # Facet template (EXTEND for RENDER-01)
        distress_indicators.html.j2 # Facet template (EXTEND for RENDER-05)
      market/
        insider_trading.html.j2     # Facet template (EXTEND for RENDER-04)
    components/
      sparkline.html.j2   # Reusable macro
      badges.html.j2      # tier_badge, verdict_badge, etc.
      tables.html.j2      # kv_table, data_grid, financial_row
  brain/sections/
    financial_health.yaml  # Facet definitions (ADD new facets)
    market_activity.yaml   # Facet definitions
  stages/render/
    html_renderer.py       # build_html_context() entry point
    section_renderer.py    # Facet dispatch
    charts/sparklines.py   # SVG sparkline generator
    context_builders/
      financials.py        # extract_financials() context builder
      market.py            # extract_market() context builder
```

### Pattern 1: Adding a New Facet Template
**What:** Each visual block is a "facet" defined in brain section YAML, rendered by a Jinja2 template.
**When to use:** Any new rendering component within an existing section.
**Steps:**
1. Add facet entry to section YAML (e.g., `financial_health.yaml`)
2. Create template file at the path specified in facet `template` field
3. Add data to context builder (e.g., `extract_financials()` in `financials.py`)
4. Template uses context variables + component macros from `base.html.j2`

**Example facet YAML entry:**
```yaml
- id: forensic_dashboard
  name: "Forensic Analysis Dashboard"
  render_as: scorecard
  signals: []
  template: sections/financial/forensic_dashboard.html.j2
```

### Pattern 2: CSS-Only Tab Switching
**What:** Tabs using hidden radio inputs + CSS `:checked` selector.
**When to use:** RENDER-01 tabbed views (Income | Balance | Cash Flow).
**Existing pattern:** Already used in `financial_statements.html.j2` (Phase 63).
```html
<input type="radio" name="trend-tabs" id="trend-income" checked class="hidden">
<input type="radio" name="trend-tabs" id="trend-balance" class="hidden">
<label for="trend-income" class="fin-tab-label">Income</label>
<label for="trend-balance" class="fin-tab-label">Balance Sheet</label>
<div class="fin-tab-panel" id="panel-income">...</div>
<div class="fin-tab-panel" id="panel-balance">...</div>
```
CSS in `charts.css` handles `:checked ~ .fin-tab-panel` visibility.

### Pattern 3: Sparkline Integration
**What:** Call `render_sparkline(values)` in context builder, pass SVG string to template.
**When to use:** RENDER-01 sparklines per metric row.
**Example:**
```python
# In context builder
from do_uw.stages.render.charts.sparklines import render_sparkline
sparkline_svg = render_sparkline(quarterly_values, width=60, height=16)
metric["sparkline"] = sparkline_svg

# In template
<td>{{ metric.sparkline | safe }}</td>
```

### Pattern 4: Color-Coded Severity Cards (Hazard Cards)
**What:** Existing CSS for hazard cards with severity indicators.
**When to use:** RENDER-02 forensic dashboard.
**Existing CSS classes:** `.hazard-card`, `.hazard-cat-code`, `.hazard-cat-name`, `.hazard-cat-score`
**Color mapping:** Use `risk-critical` (red), `risk-elevated` (amber), `risk-positive` (blue) CSS classes.

### Pattern 5: Percentile Bar (CSS-only)
**What:** Horizontal bar with fill width proportional to percentile.
**When to use:** RENDER-03 peer percentile display.
**Existing CSS in components.css:**
```css
.percentile-bar { position: relative; height: 20px; background: #f0f0f0; border-radius: 3px; }
.percentile-fill { position: absolute; top: 0; left: 0; height: 100%; border-radius: 3px; }
```
**Template pattern:**
```html
<div class="percentile-bar">
  <div class="percentile-fill" style="width:{{ pct }}%;background:{{ color }}"></div>
  <span>{{ pct }}th</span>
</div>
```

### Anti-Patterns to Avoid
- **JavaScript for visualization:** All charts/tabs/bars must be CSS-only or SVG. No JS charting libraries.
- **New CSS files:** Add to `components.css` (component-level) or `charts.css` (chart-level). Do not create new CSS files.
- **Hardcoded colors:** Use CSS variables (`var(--do-navy)`, `var(--do-risk-red)`) or `CHART_COLORS` dict. Never raw hex in templates.
- **Template over 100 lines:** Split into sub-templates or use macros.
- **Context builder over 500 lines:** Split into sub-module (existing pattern: `financials_balance.py` alongside `financials.py`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sparklines | Custom SVG generation | `render_sparkline()` from `charts/sparklines.py` | Handles edge cases, colors, auto-direction |
| Tab switching | JavaScript tabs | CSS-only radio pattern from `charts.css` | No JS policy, works in PDF |
| Percentile bars | Custom bar component | `.percentile-bar` + `.percentile-fill` CSS | Already styled, tested |
| Hazard cards | Custom card layout | `.hazard-card` CSS pattern in `components.css` | Already has expand/collapse |
| KV tables | Custom table markup | `kv_table()` macro from `components/tables.html.j2` | Consistent styling |
| Badge pills | Inline styles | `badge-pill`, `badge-tier` CSS classes | Consistent, hover states |
| Color-coded values | Manual class selection | `risk-critical`, `risk-elevated`, `risk-positive` classes | Matches design system |

## Common Pitfalls

### Pitfall 1: PDF Print Mismatch
**What goes wrong:** Templates look fine in browser but break in PDF.
**Why it happens:** `@media print` CSS overrides not considered; `position:sticky` becomes `position:static`; `<details>` are collapsed.
**How to avoid:** Test with `pdf_mode=True`; ensure `@media print` rules exist for new components; `<details>` auto-expanded by Playwright `evaluate()`.
**Warning signs:** Component uses `position:sticky`, relies on hover states, or uses `<details>` without `open` attribute in PDF mode.

### Pitfall 2: Jinja2 None Handling
**What goes wrong:** `{{ value | default('N/A') }}` does NOT catch Python `None` (only Jinja2 undefined).
**Why it happens:** Jinja2 `default` filter only applies to undefined variables, not None values.
**How to avoid:** Use `{{ value if value else 'N/A' }}` or `{{ value | format_na }}` filter (custom filter registered).
**Warning signs:** Template shows "None" literally in output.

### Pitfall 3: False SCA Classification (RENDER-06 Bug)
**What goes wrong:** Boilerplate 10-K language ("various legal proceedings in the normal course of business") gets extracted as active SCAs, triggering CRF-1 red flag.
**Why it happens:** Multi-layer problem: (1) LLM extraction prompt asks for Item 3 legal proceedings, and despite instructions to skip boilerplate, LLM sometimes includes generic language as a "case"; (2) downstream filters (`_is_boilerplate_litigation()`, `_is_regulatory_not_sca()`) check case names but may miss variants.
**How to avoid:** Three-layer fix: (1) Strengthen LLM prompt with explicit examples of what to reject, (2) Add more boilerplate patterns to `_BOILERPLATE_PATTERNS`, (3) Add a `case_specificity_score` check -- if case lacks named plaintiff, court, and filing date, it's boilerplate.
**Current filter locations:**
- `signal_mappers.py:45` -- `_is_boilerplate_litigation()` called during signal mapping
- `red_flag_gates.py:247` -- `_is_boilerplate_litigation()` called during CRF-1 gate
- `red_flag_gates.py:224-257` -- `_is_regulatory_not_sca()` checks securities theories
- `prompts.py:45-51` -- LLM extraction prompt attempts to filter

### Pitfall 4: PDF Header Overlap (RENDER-07 Bug)
**What goes wrong:** CSS `position:fixed` running header overlaps with first-page content.
**Why it happens:** The `.pdf-running-header` uses `position:fixed; top:-0.55in` in `@media print`, which places it in the margin area. But on page 1, the cover-header has `margin: -0.5rem 0 1rem 0` (negative top margin), and the identity block follows immediately. If content is tall enough, it runs into the fixed header space.
**How to avoid:** Add `padding-top` to `.worksheet-main` in print mode to account for fixed header height; or add `margin-top` on first child of `.worksheet-main` in `@media print`.
**Root cause:** The Playwright margin `top: 0.75in` and CSS header `top: -0.55in` with `height: 0.35in` should place the header entirely in the margin, but content with negative margins or insufficient padding can overlap.

### Pitfall 5: Context Builder Data Not Available
**What goes wrong:** Template references data from Phases 68/69/72 that doesn't exist yet.
**Why it happens:** Phase 73 depends on prior phases for quarterly data, forensics, and peer benchmarks.
**How to avoid:** Every template MUST gracefully handle missing data with `{% if ... %}` guards. Use `{{ data | default({}) }}` pattern. Templates should render "Data not available" rather than crash when upstream phases haven't run.

### Pitfall 6: CSS File Size
**What goes wrong:** Adding too much CSS to one file pushes it over 500 lines.
**Why it happens:** Anti-context-rot rule: no source file over 500 lines.
**How to avoid:** `styles.css` is 535 lines (already at limit). New component CSS goes in `components.css` (currently ~500 lines). If needed, split into a new `forensic.css` and add `{% include "forensic.css" %}` in `base.html.j2`.

## Code Examples

### Example 1: Context Builder for Quarterly Trends (RENDER-01)
```python
# In context_builders/financials.py (or new financials_quarterly.py)
def _build_quarterly_trend_context(state: AnalysisState) -> dict[str, Any]:
    """Build 8-quarter trend table context from XBRL quarterly data."""
    result: dict[str, Any] = {"has_data": False}

    if not (state.extracted and state.extracted.financials
            and hasattr(state.extracted.financials, "quarterly_xbrl")
            and state.extracted.financials.quarterly_xbrl):
        return result

    qxbrl = state.extracted.financials.quarterly_xbrl
    result["has_data"] = True
    result["periods"] = [q.period_label for q in qxbrl.quarters]

    # Build metric rows with sparklines
    metrics = []
    for concept_name, label in TREND_METRICS:
        values = []
        cells = []
        for q in qxbrl.quarters:
            stmt = getattr(q, "income", {})  # or balance, cash_flow
            sv = stmt.get(concept_name)
            val = sv.value if sv else None
            values.append(val or 0)
            cells.append(format_currency(val) if val else "N/A")

        metrics.append({
            "label": label,
            "cells": cells,
            "sparkline": render_sparkline(values),
        })

    result["metrics"] = metrics
    return result
```

### Example 2: Forensic Dashboard Hazard Card Template (RENDER-02)
```html
{# Forensic Analysis Dashboard — grid of hazard cards #}
{% set forensics = fin.get('forensics', {}) %}
{% if forensics.get('has_data') %}
<h3>Forensic Analysis Dashboard</h3>
<div class="grid grid-cols-2 gap-3 my-3">
  {% for card in forensics.cards %}
  <div class="border rounded p-3 page-break-inside-avoid"
       style="border-left: 3px solid {{ card.color }}">
    <div class="flex justify-between items-start">
      <span class="text-xs font-semibold uppercase tracking-wider"
            style="color:{{ card.color }}">{{ card.label }}</span>
      <span class="text-lg font-bold tabular-nums">{{ card.value }}</span>
    </div>
    <div class="text-xs text-gray-500 mt-1">{{ card.explanation }}</div>
    {% if card.trend_svg %}
    <span class="sparkline-inline">{{ card.trend_svg | safe }}</span>
    {% endif %}
  </div>
  {% endfor %}
</div>
{% else %}
{{ gap_notice("Forensic Analysis", "Forensic analysis data not available") }}
{% endif %}
```

### Example 3: Peer Percentile Bar Template (RENDER-03)
```html
{# Peer Percentile Display — CSS-only horizontal bars #}
{% set peers = fin.get('peer_percentiles', {}) %}
{% if peers.get('has_data') %}
<h3>Peer Benchmarking (SEC Filers)</h3>
<table class="w-full border-collapse my-3 text-sm">
  <thead>
    <tr class="bg-navy text-white">
      <th class="text-left px-3 py-2 border-b-2 border-gold text-xs font-semibold uppercase">Metric</th>
      <th class="text-center px-3 py-2 border-b-2 border-gold text-xs font-semibold uppercase">Percentile</th>
      <th class="px-3 py-2 border-b-2 border-gold text-xs font-semibold uppercase" style="min-width:200px">Position</th>
    </tr>
  </thead>
  <tbody>
    {% for m in peers.metrics %}
    <tr class="{{ 'bg-bg-alt' if loop.index is odd }}">
      <td class="px-3 py-2 border-b border-gray-200 font-semibold">{{ m.label }}</td>
      <td class="px-3 py-2 border-b border-gray-200 text-center tabular-nums">{{ m.overall }}th</td>
      <td class="px-3 py-2 border-b border-gray-200">
        <div class="percentile-bar">
          <div class="percentile-fill" style="width:{{ m.overall }}%;background:var(--do-navy)"></div>
          {% if m.sector %}
          <div class="percentile-fill" style="width:{{ m.sector }}%;background:var(--do-gold);opacity:0.5"></div>
          {% endif %}
        </div>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endif %}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance quarterly data | XBRL quarterly data (Phase 68) | v3.1 | Template consumes both; XBRL preferred when available |
| Ratio-to-baseline proxy | Frames API true percentile (Phase 72) | v3.1 | Template shows real position among 8000+ filers |
| No forensic display | Forensic dashboard cards (Phase 69) | v3.1 | New template with hazard card grid |
| Boilerplate SCA leaks through | Multi-layer filtering + prompt fix | Phase 73 | Eliminates false CRF-1 triggers |

## Bug Fix Analysis

### False SCA Classification (RENDER-06)

**Root cause chain:**
1. **LLM extraction** (`prompts.py:45-51`): Prompt says to skip boilerplate but LLM sometimes includes "various legal proceedings" as a named case
2. **Signal mapping** (`signal_mappers.py:45`): `_is_boilerplate_litigation()` checks 6 patterns against case name, but variants slip through (e.g., "Company is party to legal matters arising in the ordinary course")
3. **Red flag gates** (`red_flag_gates.py:224-257`): `_is_regulatory_not_sca()` checks for securities theories and boilerplate, but non-securities cases without explicit theory labels may pass through
4. **Scoring** (`red_flag_gates.py:220`): Any SCA that passes filters triggers CRF-1 (Active SCA red flag)

**Fix strategy (three layers):**
1. **Prompt hardening** (prompts.py): Add explicit rejection examples -- "Do NOT extract 'Company is subject to various legal proceedings arising in the ordinary course of business' or similar generic disclosures"
2. **Pattern expansion** (signal_mappers_ext.py): Add more boilerplate patterns:
   - "PARTY TO LEGAL MATTERS"
   - "LEGAL MATTERS ARISING"
   - "INVOLVED IN LITIGATION"
   - "SUBJECT TO CLAIMS"
   - "LEGAL PROCEEDINGS AND CLAIMS"
3. **Case specificity filter** (red_flag_gates.py): If SCA entry lacks ALL of: named plaintiff, court/jurisdiction, specific filing date -- treat as boilerplate regardless of name

### PDF Header Overlap (RENDER-07)

**Root cause:** The `.pdf-running-header` uses `position:fixed; top:-0.55in; height:0.35in` in `@media print`. Playwright sets page margin `top: 0.75in`. This should place the header entirely in the 0.75in margin. However:
- The cover-header div has `margin: -0.5rem 0 1rem 0` (negative top margin pulling content up)
- The identity block immediately follows with no explicit top padding
- On page 1, content starts at the very top of the content area and can visually collide with the fixed header

**Fix:** Add `padding-top` to the first content element in print mode:
```css
@media print {
  .worksheet-main > *:first-child {
    padding-top: 0.4in; /* Clear the fixed header */
  }
  /* Only first page needs extra space; subsequent pages have natural page-break spacing */
}
```

Alternative: Use Playwright's `header_template` for first-page blank header (but this changes all pages).

### Company Logo (RENDER-08)

**Status: Already partially implemented.** Logo acquisition (`_fetch_company_logo()`) works. Logo displays in:
- Browser topbar (`base.html.j2:69-70`): favicon with brightness inversion
- Identity block (`identity.html.j2:11-12`): small image beside company name

**Remaining work:** Ensure logo displays properly in cover-header for PDF, handle SVG favicons (some companies serve SVG), and ensure logo renders in both HTML and PDF modes. The acquisition side is solid (Google Favicons API -> favicon.ico -> OG tag fallback chain).

## Open Questions

1. **Quarterly data availability at render time**
   - What we know: RENDER-01 depends on Phase 68 data (`quarterly_xbrl` on `ExtractedFinancials`)
   - What's unclear: Will templates be developed before Phase 68 is complete?
   - Recommendation: Build templates with graceful fallback to existing `yfinance_quarterly` data. The existing `quarterly_trend.html.j2` already renders yfinance quarterly data. New template should try XBRL first, fall back to yfinance.

2. **Forensic data model shape**
   - What we know: Phase 69 creates `state.analyzed.forensics` namespace with Pydantic models
   - What's unclear: Exact field names for forensic results (depends on Phase 69 implementation)
   - Recommendation: Define template interface contract (expected context dict keys) now. Phase 69 context builder adapts to actual model shape.

3. **Peer percentile data shape**
   - What we know: Phase 72 creates Frames API percentile data
   - What's unclear: Whether sector percentile is available (requires CIK-to-SIC cross-reference)
   - Recommendation: Template supports both overall-only and overall+sector display modes.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `html_renderer.py`, `section_renderer.py`, `base.html.j2`, `worksheet.html.j2`
- Template patterns: `quarterly_trend.html.j2`, `annual_comparison.html.j2`, `insider_trading.html.j2`, `distress_indicators.html.j2`
- CSS: `styles.css` (535 lines), `components.css` (500 lines), `charts.css`
- Sparklines: `charts/sparklines.py` (119 lines, pure SVG)
- Section YAML: `financial_health.yaml`, `market_activity.yaml`
- Bug analysis: `signal_mappers.py`, `signal_mappers_ext.py`, `red_flag_gates.py`, `prompts.py`
- Logo: `orchestrator.py:531-604`, `identity.html.j2`, `base.html.j2`

### Secondary (MEDIUM confidence)
- PDF rendering: `html_renderer.py:407-511` (Playwright config)
- Architecture research: `.planning/research/ARCHITECTURE.md` (v3.1 rendering section)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools/patterns already exist in codebase
- Architecture: HIGH - mature template system with clear patterns from v3.0
- Pitfalls: HIGH - bugs are identified with specific file locations and root causes
- New template data: MEDIUM - depends on Phase 68/69/72 model shapes (not yet implemented)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable rendering infrastructure, unlikely to change)
