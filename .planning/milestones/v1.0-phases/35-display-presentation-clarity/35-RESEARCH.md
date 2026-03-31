# Phase 35: Display & Presentation Clarity - Research

**Researched:** 2026-02-21
**Domain:** Document rendering, HTML-to-PDF pipelines, LLM narrative generation, density-driven template architecture
**Confidence:** MEDIUM-HIGH (toolchain verified with official docs; LLM narrative architecture is design-level guidance)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Section Density Levels**: Three tiers: CLEAN, ELEVATED, CRITICAL — per-section and per-subsection. CLEAN keeps full depth (same tables, narratives, structure — just green signals). ELEVATED adds amber indicators + "why this matters for D&O" context. CRITICAL gets expanded forensic detail, Deep Dive sub-sections, cross-references, visual urgency cues.
- **Check-Type Display Mapping**: MANAGEMENT_DISPLAY -> structured data tables + one-line context note. EVALUATIVE_CHECK -> traffic light badge + brief D&O explanation when TRIGGERED/ELEVATED. INFERENCE_PATTERN -> written narrative + bulleted evidence. SKIPPED -> grey "Not evaluated" badge + reason.
- **Narrative Generation**: All narratives LLM-generated (Claude), not rule-based. Tiered executive summary (CLEAN: 3-4 sentences, ELEVATED/CRITICAL: 6-8 sentences). Every section gets a narrative. Meeting prep questions tied to specific findings. Narratives pre-computed in BENCHMARK stage.
- **Gap & Coverage Visibility**: Per-subsection gap notices with "Data not available" explanation. Data coverage appendix (% checks evaluated). Only LOW confidence gets visible markers. Blind spot discoveries as distinct "Discovery" callout boxes.
- **Visual Quality & Document Output**: Bloomberg/S&P target quality. Dual output: Word (editable, basic formatting) + PDF from rich HTML (presentation version). Mixed layout (full-width narratives, multi-column data). Full analytical charts (stock with events, trend comparisons, peer scatter, risk radar). HTML-to-PDF: research cutting edge, no paid services. Word: functional/clean, not Bloomberg-grade.

### Claude's Discretion
- Exact color palette and typography choices for HTML/PDF (should feel like Bloomberg/S&P)
- Chart library choice (matplotlib, plotly, or alternatives) for embedded visuals
- HTML template architecture (single template vs component-based)
- Formatting of "Not evaluated" badges and discovery callout boxes
- Multi-column layout implementation in HTML report

### Deferred Ideas (OUT OF SCOPE)
- None specified in CONTEXT.md
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OUT-01 | Primary output format is Word (.docx) via python-docx | Existing word_renderer.py + section renderers already produce Word docs. Phase 35 keeps this as "functional/clean" editable version. No Bloomberg-grade upgrade needed for Word. |
| OUT-02 | PDF output | **Major upgrade**: Current WeasyPrint pipeline replaced with Playwright headless Chromium for Bloomberg-quality HTML-to-PDF. Jinja2 + Tailwind CSS templates rendered by Chromium produce pixel-perfect PDFs. |
| OUT-03 | Every section begins with summary paragraph | Narrative generation moved to BENCHMARK stage as LLM-generated text. RENDER just inserts pre-computed narratives. |
| OUT-04 | Source citation on every data point | Already implemented via SourcedValue model. Phase 35 ensures citations render consistently across density tiers. |
| VIS-01 | Stock price charts with event overlays | Existing matplotlib charts in charts/stock_charts.py. For HTML PDF, generate as PNG via matplotlib, embed as base64. Plotly optional for interactive HTML preview. |
| VIS-02 | Ownership breakdown chart | Existing charts/ownership_chart.py. Same embed strategy. |
| VIS-03 | Litigation timeline visualization | Existing charts/timeline_chart.py. Same embed strategy. |
| VIS-04 | Financial tables with conditional formatting | HTML/CSS tables with risk-class styling (already in styles.css). Extend with multi-column dashboard grid for PDF. |
| VIS-05 | Complete visual design system | **Core deliverable**: Bloomberg-inspired design system — dark navy headers, gold accents, dense data tables, professional typography, multi-column grid layouts, risk heat spectrum badges. |
| SECT1-01 | Company snapshot as structured header block | Already built by summary_builder.py. Phase 35 upgrades its visual presentation in the HTML PDF template. |
| CORE-04 | 7-stage pipeline maintained | Narrative generation added to BENCHMARK stage. No new stages. RENDER becomes pure formatter. Pipeline stays at 7 stages. |
</phase_requirements>

## Summary

Phase 35 requires five interconnected workstreams: (1) upgrading the section density model from boolean clean/not-clean to three-tier CLEAN/ELEVATED/CRITICAL with per-subsection granularity, (2) moving all narrative generation to the BENCHMARK stage using LLM (Claude) calls with caching, (3) implementing check-type-driven display formatting based on the knowledge model's MANAGEMENT_DISPLAY / EVALUATIVE_CHECK / INFERENCE_PATTERN types, (4) building a Bloomberg-quality HTML template system with Jinja2 + Tailwind CSS rendered to PDF via Playwright headless Chromium, and (5) elevating gap/coverage visibility throughout the document.

The current codebase is well-positioned for this work. The ANALYZE stage already computes boolean section assessments (`governance_clean`, `litigation_clean`, etc.) in `section_assessments.py`. The BENCHMARK stage already pre-computes thesis, risk, and claim narratives. The RENDER stage already has three parallel pipelines (Word, Markdown, PDF). The content_type field already exists on all checks in the knowledge store. The main gaps are: extending booleans to three-tier density, replacing rule-based narratives with LLM-generated ones, and building the entirely new HTML/PDF template system.

**Primary recommendation:** Use Playwright headless Chromium for HTML-to-PDF (not WeasyPrint) because Chromium fully supports CSS Grid, Flexbox, and Tailwind CSS utility classes — essential for Bloomberg-quality multi-column layouts. WeasyPrint has known limitations with Grid and Flexbox. Keep matplotlib for chart generation (PNG embedded as base64 in HTML), since it produces publication-quality static images ideal for PDF. Use Jinja2 macros as the component system for HTML templates.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| playwright | >=1.45 | HTML-to-PDF via headless Chromium | Full CSS Grid/Flexbox/Tailwind support. Pixel-perfect rendering. Already an MCP dependency. |
| jinja2 | >=3.1 (existing) | HTML template rendering | Already used for Markdown/PDF templates. Macros provide component system. |
| matplotlib | >=3.9 (existing) | Chart generation (PNG) | Already produces all current charts. Publication-quality static output ideal for PDF embed. |
| anthropic | >=0.79 (existing) | LLM narrative generation | Already a dependency for LLM extraction in EXTRACT stage. |
| instructor | >=1.14 (existing) | Structured LLM output | Already used for structured extraction. Enables typed narrative responses. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| plotly | >=6.5 (existing) | Interactive charts for HTML preview | Optional: stock chart with hover, peer scatter. Only for web dashboard, not PDF. |
| tailwindcss | CDN v4 | Utility-first CSS for HTML PDF template | Loaded via CDN `<script>` tag in HTML template, rendered by Chromium before PDF export. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright (PDF) | WeasyPrint (current) | WeasyPrint has incomplete CSS Grid/Flexbox support; cannot render multi-column dashboard layouts. Playwright uses real Chromium engine. |
| Playwright (PDF) | wkhtmltopdf | Unmaintained since 2022, based on old WebKit fork. Poor modern CSS support. |
| Playwright (PDF) | pagedjs | Polyfill approach; requires Node.js runtime. Less mature than Playwright. |
| Tailwind CDN | Hand-written CSS | Tailwind utility classes dramatically reduce CSS authoring for dense financial layouts. CDN avoids build step. |
| matplotlib (charts) | plotly (static) | Plotly requires Kaleido for static export (being deprecated). matplotlib is simpler for PNG generation. |

**Installation:**
```bash
uv add playwright
playwright install chromium
```
Note: `playwright install chromium` downloads the headless Chromium browser binary (~150MB). This is a one-time setup.

## Architecture Patterns

### Current Render Architecture (What Exists)
```
src/do_uw/stages/render/
├── __init__.py              # RenderStage orchestrator (3 formats)
├── word_renderer.py         # Word doc assembly (283 lines)
├── md_renderer.py           # Markdown via Jinja2 (301 lines)
├── pdf_renderer.py          # PDF via WeasyPrint (173 lines) → TO BE REPLACED
├── design_system.py         # DesignSystem frozen dataclass (188 lines)
├── chart_helpers.py         # matplotlib fig creation/embed (193 lines)
├── formatters.py            # format_currency/format_percentage
├── md_narrative.py          # Rule-based narratives (368 lines) → TO BE REPLACED
├── md_narrative_helpers.py  # Financial sub-narratives
├── md_narrative_sections.py # Gov/lit/scoring narratives (494 lines)
├── md_renderer_helpers.py   # State extraction for templates (497 lines)
├── md_renderer_helpers_ext.py
├── md_renderer_helpers_scoring.py
├── md_renderer_helpers_calibration.py
├── peer_context.py
├── tier_helpers.py
├── docx_helpers.py
├── charts/                  # stock, radar, ownership, timeline
└── sections/                # 30+ section renderer files
```

### Target Architecture (Phase 35)
```
src/do_uw/stages/render/
├── __init__.py              # RenderStage (Word + HTML-PDF + Markdown)
├── word_renderer.py         # UNCHANGED (functional Word output)
├── md_renderer.py           # UNCHANGED (Markdown output)
├── html_renderer.py         # NEW: Playwright-based HTML-to-PDF
├── design_system.py         # Extended with HTML color palette
├── chart_helpers.py         # Extended with base64 PNG helper
├── formatters.py            # Extended with HTML-specific formatters
├── sections/                # UNCHANGED (Word section renderers)
└── ... (existing files unchanged)

src/do_uw/templates/
├── html/                    # NEW: Bloomberg-quality HTML templates
│   ├── base.html.j2         # Base layout with Tailwind CDN
│   ├── components/          # Jinja2 macro components
│   │   ├── badges.html.j2   # Traffic light, density, confidence badges
│   │   ├── tables.html.j2   # Data tables, KV tables, multi-column grids
│   │   ├── charts.html.j2   # Chart embed containers
│   │   ├── callouts.html.j2 # Discovery, warning, D&O context boxes
│   │   └── narratives.html.j2 # Section narrative blocks
│   ├── sections/            # Per-section templates
│   │   ├── executive.html.j2
│   │   ├── company.html.j2
│   │   ├── financial.html.j2
│   │   ├── market.html.j2
│   │   ├── governance.html.j2
│   │   ├── litigation.html.j2
│   │   ├── scoring.html.j2
│   │   └── ai_risk.html.j2
│   ├── appendices/
│   │   ├── meeting_prep.html.j2
│   │   ├── coverage.html.j2
│   │   └── calibration.html.j2
│   └── styles.css           # Tailwind overrides + custom styles
├── markdown/                # UNCHANGED
│   └── worksheet.md.j2
└── pdf/                     # DEPRECATED (replaced by html/)
    └── ...
```

### Pattern 1: Three-Tier Density Assessment
**What:** Extend boolean `*_clean` fields to three-tier `DensityLevel` enum (CLEAN/ELEVATED/CRITICAL).
**When to use:** ANALYZE stage computes per-section density. BENCHMARK stage may override per-subsection. RENDER reads density, never computes it.
**Example:**
```python
# In models/common.py or models/state.py
class DensityLevel(StrEnum):
    CLEAN = "CLEAN"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"

class SectionDensity(BaseModel):
    """Density assessment for a worksheet section."""
    level: DensityLevel = DensityLevel.CLEAN
    subsection_overrides: dict[str, DensityLevel] = Field(default_factory=dict)
    # e.g., {"4.1_people_risk": "CRITICAL", "4.2_structural_governance": "CLEAN"}

# On AnalysisResults (state.analysis)
section_densities: dict[str, SectionDensity] = Field(default_factory=dict)
# Keyed by section ID: "company", "financial", "market", "governance", "litigation", "scoring"
```

### Pattern 2: Check-Type Display Dispatch
**What:** Template components select display format based on content_type from check metadata.
**When to use:** Rendering check results in section detail views and coverage appendix.
**Example (Jinja2 macro):**
```html
{% macro render_check(check) %}
  {% if check.content_type == "MANAGEMENT_DISPLAY" %}
    {{ render_data_table(check) }}
  {% elif check.content_type == "EVALUATIVE_CHECK" %}
    {{ render_traffic_light(check) }}
  {% elif check.content_type == "INFERENCE_PATTERN" %}
    {{ render_inference_narrative(check) }}
  {% else %}
    {{ render_skipped_badge(check) }}
  {% endif %}
{% endmacro %}
```

### Pattern 3: LLM Narrative Generation in BENCHMARK
**What:** Generate section narratives via Claude API calls during BENCHMARK, cache results in state.
**When to use:** After all scoring/benchmark data is available but before RENDER.
**Example:**
```python
# In stages/benchmark/narrative_generator.py
def generate_section_narrative(
    section_id: str,
    section_data: dict[str, Any],
    density: DensityLevel,
    company_name: str,
) -> str:
    """Generate LLM narrative for a section based on its density level."""
    # Build prompt from section data and density tier
    prompt = _build_narrative_prompt(section_id, section_data, density)

    # Check cache first
    cache_key = _compute_cache_key(section_id, section_data, density)
    cached = _get_cached_narrative(cache_key)
    if cached is not None:
        return cached

    # Generate via Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500 if density == DensityLevel.CLEAN else 1000,
        messages=[{"role": "user", "content": prompt}],
    )
    narrative = response.content[0].text

    # Cache and return
    _cache_narrative(cache_key, narrative)
    return narrative
```

### Pattern 4: Playwright PDF Generation
**What:** Render Jinja2 HTML template, load in headless Chromium, export as PDF.
**When to use:** PDF output format in RENDER stage.
**Example:**
```python
# In stages/render/html_renderer.py
from playwright.sync_api import sync_playwright

def render_html_pdf(
    state: AnalysisState,
    output_path: Path,
    chart_dir: Path | None = None,
) -> Path:
    """Render Bloomberg-quality PDF via Playwright headless Chromium."""
    # 1. Build template context (reuse existing build_template_context)
    context = build_html_context(state, chart_dir)

    # 2. Render HTML via Jinja2
    html_content = _render_html_template(context)

    # 3. Write to temp file (Chromium needs a file: URL for local resources)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        f.write(html_content.encode('utf-8'))
        html_path = f.name

    # 4. Generate PDF via Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'file://{html_path}')
        page.pdf(
            path=str(output_path),
            format='Letter',
            margin={'top': '0.75in', 'bottom': '0.75in',
                    'left': '0.65in', 'right': '0.65in'},
            print_background=True,
        )
        browser.close()

    Path(html_path).unlink()  # Cleanup
    return output_path
```

### Pattern 5: Jinja2 Macro Component System
**What:** Reusable HTML components as Jinja2 macros imported into section templates.
**When to use:** Any repeated UI pattern (badges, tables, callouts, charts).
**Example:**
```html
{# components/badges.html.j2 #}
{% macro traffic_light(status, label="") %}
  {% if status == "TRIGGERED" %}
    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-700 text-white">{{ label or "TRIGGERED" }}</span>
  {% elif status == "CLEAR" %}
    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-600 text-white">{{ label or "CLEAR" }}</span>
  {% elif status == "SKIPPED" %}
    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-gray-400 text-white">{{ label or "Not evaluated" }}</span>
  {% else %}
    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blue-600 text-white">{{ label or status }}</span>
  {% endif %}
{% endmacro %}

{% macro density_indicator(level) %}
  {% if level == "CRITICAL" %}
    <div class="border-l-4 border-red-700 bg-red-50 px-3 py-1 text-xs text-red-800 font-semibold uppercase tracking-wider">Critical Risk</div>
  {% elif level == "ELEVATED" %}
    <div class="border-l-4 border-amber-500 bg-amber-50 px-3 py-1 text-xs text-amber-800 font-semibold uppercase tracking-wider">Elevated Concern</div>
  {% endif %}
{% endmacro %}
```

### Anti-Patterns to Avoid
- **Analytical logic in RENDER**: No threshold comparisons, score evaluations, or data classification in any render file. RENDER reads pre-computed density, narratives, and display metadata. If you need an `if score > X` in render, it belongs upstream in ANALYZE or BENCHMARK.
- **Monolithic HTML template**: Do NOT put all sections in one 1000+ line template. Use Jinja2 `{% include %}` and macros to keep each section template under 300 lines.
- **Duplicating display logic for Word and HTML**: The Word renderer and HTML renderer serve different purposes (editable vs presentation). Do NOT try to share rendering logic between them. Share only the data extraction layer (`build_template_context`).
- **Running LLM calls in RENDER**: All LLM narrative generation happens in BENCHMARK. RENDER is synchronous, deterministic, and fast.
- **Inlining Tailwind CDN in PDF**: Tailwind CDN `<script>` tag generates CSS at runtime in the browser. For PDF, this works because Playwright runs real Chromium which executes the script. Do NOT try to pre-compile Tailwind — CDN is sufficient for this use case.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML-to-PDF rendering | Custom PDF generator | Playwright `page.pdf()` | Chromium's print engine handles all CSS, page breaks, headers/footers. Handles everything WeasyPrint can't. |
| CSS framework | Custom CSS from scratch | Tailwind CSS v4 CDN | Utility classes produce Bloomberg-dense layouts with 10x less custom CSS. No build step needed. |
| Component system | Custom template inheritance | Jinja2 macros + includes | Jinja2 macros are the standard Pythonic component pattern. No JavaScript framework needed. |
| Chart embedding | Custom SVG generation | matplotlib PNG -> base64 | `save_chart_to_bytes()` already exists in chart_helpers.py. Base64 embed works in both WeasyPrint and Chromium. |
| LLM structured output | Custom JSON parsing | instructor library | Already a dependency. Ensures typed responses from Claude for narrative generation. |
| Cache key computation | Custom hashing | hashlib.sha256 on serialized input | Standard Python. Cache by section_id + data hash + density level. |

**Key insight:** Playwright headless Chromium IS a browser engine. Anything that renders correctly in Chrome renders correctly in the PDF. This eliminates the entire category of "CSS compatibility" issues that plague WeasyPrint, wkhtmltopdf, and other non-browser PDF generators.

## Common Pitfalls

### Pitfall 1: Playwright Browser Installation
**What goes wrong:** `playwright install chromium` not run, or run in wrong environment. PDF generation silently fails.
**Why it happens:** Playwright requires a separate binary download step beyond `pip install`.
**How to avoid:** Add `playwright install chromium` to setup instructions. In code, catch `BrowserType.launch()` errors and fall back gracefully (same pattern as current WeasyPrint `ImportError` handling).
**Warning signs:** `Error: Executable doesn't exist` at runtime.

### Pitfall 2: Tailwind CDN in Print Context
**What goes wrong:** Tailwind CDN `<script>` tag needs JavaScript execution. If the page is rendered without JS, no styles apply.
**Why it happens:** Playwright executes JS by default, but `page.goto()` with `wait_until='domcontentloaded'` may fire before Tailwind processes classes.
**How to avoid:** Use `page.goto(url, wait_until='networkidle')` to ensure Tailwind CDN script has fully loaded and applied styles before PDF generation. Alternatively, use `page.wait_for_timeout(500)` as a safety margin.
**Warning signs:** PDF output has no styling, raw HTML visible.

### Pitfall 3: LLM Cost Explosion in Narrative Generation
**What goes wrong:** Every pipeline run generates 10+ LLM calls for narratives, costing $0.50-2.00 per run on top of existing extraction costs.
**Why it happens:** No caching, no cost budgeting, narratives regenerated even when input data hasn't changed.
**How to avoid:** (1) Cache narratives keyed by hash of input data — same data = same narrative. (2) Use claude-sonnet (not opus) for narrative generation — sufficient quality at ~10x lower cost. (3) Budget: allocate $0.50 max for narrative generation per run. (4) Fallback: if budget exceeded or LLM unavailable, fall back to existing rule-based narratives.
**Warning signs:** `CostTracker.budget_usd` consistently exceeded.

### Pitfall 4: State Model Bloat
**What goes wrong:** Adding 8+ narrative fields, density assessments, and display metadata balloons AnalysisState JSON from ~2MB to ~5MB+.
**Why it happens:** Pre-computing everything for RENDER means storing more intermediate results.
**How to avoid:** Keep narratives as plain strings (not nested models). Keep density as simple enums. Consider a separate `RenderContext` transient model that isn't serialized to disk — only needed between BENCHMARK and RENDER in the same pipeline run.
**Warning signs:** state.json exceeds 3MB, serialization takes >1s.

### Pitfall 5: Template Size Explosion
**What goes wrong:** Single monolithic HTML template exceeds 2000 lines, becomes unmaintainable.
**Why it happens:** Bloomberg-quality reports have many sections, each with density-conditional content, charts, tables.
**How to avoid:** Strict component architecture: base template + section includes + macro components. No section template over 300 lines. No component macro file over 200 lines.
**Warning signs:** Any `.html.j2` file approaching 500 lines.

### Pitfall 6: Check content_type Not Available at Render Time
**What goes wrong:** check_results in state.analysis don't carry content_type metadata, so template can't dispatch by type.
**Why it happens:** check_engine.py stores results as dicts with status/evidence/threshold but doesn't carry forward content_type from the check definition.
**How to avoid:** Ensure check_engine.py propagates content_type into each check_result dict. Or: maintain a lookup from check_id to content_type that RENDER can reference.
**Warning signs:** All checks render with same generic format regardless of type.

## Code Examples

### Playwright PDF Generation
```python
# Source: https://playwright.dev/python/docs/api/class-page#page-pdf
from playwright.sync_api import sync_playwright

def generate_pdf(html_path: str, output_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'file://{html_path}', wait_until='networkidle')
        page.pdf(
            path=output_path,
            format='Letter',
            margin={'top': '0.75in', 'bottom': '0.75in',
                    'left': '0.65in', 'right': '0.65in'},
            print_background=True,
            display_header_footer=True,
            header_template='<div style="font-size:7pt;color:#999;width:100%;text-align:center;"><span class="title"></span></div>',
            footer_template='<div style="font-size:7pt;color:#999;width:100%;text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
        )
        browser.close()
```

### Jinja2 Macro Component Import Pattern
```html
{# base.html.j2 #}
{% from "components/badges.html.j2" import traffic_light, density_indicator, confidence_marker %}
{% from "components/tables.html.j2" import data_table, kv_table, multi_column_grid %}
{% from "components/callouts.html.j2" import discovery_box, warning_box, do_context %}
{% from "components/charts.html.j2" import embed_chart %}
```

### Density-Conditional Section Rendering
```html
{# sections/financial.html.j2 #}
{% set density = densities.get('financial', {}).get('level', 'CLEAN') %}

<section id="financial" class="page-break">
  {{ density_indicator(density) }}
  <h2>Section 3: Financial Health</h2>

  {# Narrative — always present, length varies by density #}
  <div class="narrative">{{ narratives.financial }}</div>

  {# Core tables — always present regardless of density #}
  {{ render_financial_tables(financials) }}

  {% if density == "CRITICAL" %}
    {# Deep Dive: expanded forensic analysis #}
    <div class="deep-dive border-l-4 border-red-700 pl-4 mt-4">
      <h3>Deep Dive: Financial Distress Indicators</h3>
      {{ render_distress_deep_dive(financials) }}
      <p class="text-sm text-gray-600 mt-2">
        <strong>Cross-reference:</strong> See Section 6 (Litigation) for related going-concern implications
        and Section 7 (Scoring) for factor impact.
      </p>
    </div>
  {% elif density == "ELEVATED" %}
    {# Brief concern notes alongside amber indicators #}
    {% for concern in financials.concerns %}
      {{ warning_box(concern.description, concern.do_context) }}
    {% endfor %}
  {% endif %}
</section>
```

### LLM Narrative with Caching
```python
import hashlib, json
from anthropic import Anthropic

_narrative_cache: dict[str, str] = {}

def _cache_key(section_id: str, data: dict, density: str) -> str:
    """Deterministic cache key from section data."""
    raw = json.dumps({"section": section_id, "density": density, "data": data},
                     sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def generate_narrative(
    section_id: str,
    section_data: dict,
    density: str,
    company_name: str,
    client: Anthropic,
) -> str:
    key = _cache_key(section_id, section_data, density)
    if key in _narrative_cache:
        return _narrative_cache[key]

    length_guide = {
        "CLEAN": "2-3 concise sentences",
        "ELEVATED": "4-5 sentences covering concerns and D&O implications",
        "CRITICAL": "6-8 sentences with forensic detail and cross-references",
    }

    prompt = f"""Write a professional D&O underwriting narrative for the {section_id} section of {company_name}.
Density level: {density} — write {length_guide.get(density, '3-4 sentences')}.
Tone: Bloomberg analyst report — factual, specific, professional.
Data: {json.dumps(section_data, default=str)[:3000]}
Rules: Cite specific numbers. Explain D&O relevance. No hedging language. No generic statements."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400 if density == "CLEAN" else 800,
        messages=[{"role": "user", "content": prompt}],
    )
    narrative = response.content[0].text
    _narrative_cache[key] = narrative
    return narrative
```

## Current Codebase Analysis

### Analytical Logic Currently in RENDER (Must Move Upstream)

The following functions in `render/` contain threshold comparisons or analytical logic that Phase 35 must move to ANALYZE or BENCHMARK:

1. **`sect7_scoring.py:_score_to_risk_level()`** — Maps quality score to risk level string via thresholds (86/71/51/26). Already partially pre-computed in BENCHMARK (`_precompute_narratives` stores `state.benchmark.risk_level`), but the function is still called directly in render.

2. **`sect8_ai_risk.py:_score_to_threat_label()` and `_dim_score_threat()`** — Maps AI risk scores to threat labels (70/40 thresholds). Should be pre-computed during ANALYZE.

3. **`sect3_financial.py:_is_financial_clean()` local fallback** — Lines 218-221 show the render-time fallback when `state.analysis.financial_clean` is None. Phase 35 eliminates this by making section density always pre-computed.

4. **`sect2_company_details.py:_is_high_risk_jurisdiction()`** — Classifies jurisdictions as high-risk. This is display logic (which color to show) but the classification itself should come from ANALYZE.

5. **`md_narrative.py` and `md_narrative_sections.py`** — All ~800 lines of rule-based narrative generation. Phase 35 replaces with LLM narratives pre-computed in BENCHMARK.

6. **`sect1_helpers.py`** — `build_thesis_narrative()`, `build_risk_narrative()`, `build_claim_narrative()`. Already called from BENCHMARK's `_precompute_narratives()` but the functions live in render/. Phase 35 should move these to benchmark/.

### Current Section Assessment Model

Current state model uses four boolean fields on `AnalysisResults`:
- `governance_clean: bool | None`
- `litigation_clean: bool | None`
- `financial_clean: bool | None`
- `market_clean: bool | None`

Phase 35 replaces these with `section_densities: dict[str, SectionDensity]` providing three-tier assessment with per-subsection overrides.

### Current Narrative Architecture

Narratives are currently generated in two places:
1. **Rule-based** (in render/): `md_narrative.py`, `md_narrative_sections.py`, `md_narrative_helpers.py` — ~1,200 lines of hand-coded narrative generation with if/elif chains.
2. **Template-based** (in benchmark/): `thesis_templates.py` — 392 lines of risk-type-specific thesis templates.

Phase 35 replaces both with LLM-generated narratives pre-computed in BENCHMARK, falling back to existing rule-based when LLM is unavailable.

### Check Content Type Distribution

The knowledge store tracks three content types on all checks:
- **EVALUATIVE_CHECK** (~267): Has TRIGGERED/CLEAR/SKIPPED threshold evaluation
- **MANAGEMENT_DISPLAY** (~98): Data presence verification, INFO-only
- **INFERENCE_PATTERN** (~19): Multi-signal detection via inference_evaluator

The check_engine.py already dispatches differently based on content_type (line 108-112). Phase 35 needs the content_type to flow through to check_results so RENDER can display each type differently.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WeasyPrint for PDF | Playwright headless Chromium | 2024-2025 | Full CSS Grid/Flexbox support, pixel-perfect rendering |
| Hand-written CSS | Tailwind CSS utility classes | 2023-2024 | 10x faster styling, consistent spacing, dark theme support |
| Rule-based narratives | LLM-generated narratives | 2024-2025 | Natural language, company-specific, professional tone |
| Boolean clean/not-clean | Multi-tier density (CLEAN/ELEVATED/CRITICAL) | Phase 35 | Granular display control, proportional detail depth |
| Separate chart libraries per format | matplotlib PNG + base64 embed | Stable | Single chart source, works in all formats |

**Deprecated/outdated:**
- **WeasyPrint**: Still works for simple layouts but cannot handle CSS Grid or complex Flexbox. Will be replaced by Playwright for the "presentation" PDF. Remains as optional fallback.
- **Plotly Orca/engine**: Deprecated in Plotly 6.2.0, removed after Sep 2025. Kaleido is the current static export engine, but adds complexity. matplotlib remains simpler for static charts.

## Bloomberg/S&P Design Recommendations (Claude's Discretion)

### Color Palette
- **Primary Navy**: #0B1D3A (deeper than current #1A1446 for more Bloomberg feel)
- **Accent Gold**: #D4A843 (muted gold, less saturated than current #FFD000)
- **Risk Red**: #B91C1C (Tailwind red-700)
- **Caution Amber**: #D97706 (Tailwind amber-600)
- **Positive Blue**: #1D4ED8 (Tailwind blue-700, NOT green)
- **Neutral Gray**: #6B7280 (Tailwind gray-500)
- **Background**: #FFFFFF body, #F8FAFC (Tailwind slate-50) for alternating rows
- **Text**: #111827 (Tailwind gray-900) for body, #6B7280 for secondary

### Typography
- **Headings**: Inter or system sans-serif (Tailwind default) — clean, professional
- **Body**: Georgia or system serif — traditional financial report feel
- **Data/Tables**: Tabular numerals via `font-variant-numeric: tabular-nums` — columns align perfectly
- **Citations**: JetBrains Mono or system monospace at 7pt

### Chart Library Recommendation
**Use matplotlib for all chart generation.** Rationale:
- Already produces all current charts (stock, radar, ownership, timeline)
- Publication-quality PNG output embeds perfectly as base64 in HTML
- No additional dependency (plotly already a dependency but not needed for static charts)
- For the HTML PDF version, add enhanced charts: financial trend comparison (bar+line combo), peer scatter plot (market cap vs quality score), risk heat map (10 factors as colored grid)
- If interactive charts are later desired for the web dashboard, plotly can be added as an enhancement — but the PDF uses static PNG.

### Template Architecture Recommendation
**Component-based Jinja2 macros.** Rationale:
- Base template handles page setup, Tailwind CDN, print styles
- Component macros handle badges, tables, callouts, charts (reusable across sections)
- Section templates handle content organization (one per worksheet section)
- This maps to ~15-20 template files, each under 300 lines
- Much cleaner than a single monolithic template (current `worksheet.html.j2` is already 417 lines)

### Multi-Column Layout
- **Executive Summary**: Full-width for thesis narrative; 2-column grid for company snapshot + inherent risk side-by-side
- **Data Sections** (financial, governance): 2-column CSS Grid for KV tables side-by-side; full-width for narrative and deep-dive sections
- **Charts**: Full-width for stock charts and timelines; 2-up grid for radar + ownership chart
- **Scoring**: Full-width factor table; 3-column grid for severity/probability/tower recommendation

Implementation: CSS Grid via Tailwind (`grid grid-cols-2 gap-4`) with `@media print` overrides for page-break control.

## Open Questions

1. **Playwright Chromium binary distribution**
   - What we know: `playwright install chromium` downloads a browser binary. Works on macOS/Linux.
   - What's unclear: Does this work in CI/CD environments without display? (Answer: Yes, headless mode doesn't need a display.)
   - Recommendation: Document the install step. Add a `try/except` around Playwright import matching current WeasyPrint pattern.

2. **Narrative caching persistence**
   - What we know: In-memory dict cache works per-run. The existing DuckDB brain database could store narratives.
   - What's unclear: Should narrative cache persist across runs? If data changes, cache is invalidated by hash. But LLM outputs are non-deterministic — same input may produce slightly different narratives.
   - Recommendation: In-memory cache per run for now. Cache key = hash of input data + density. If same data reappears in next run, regenerate (narratives are cheap at sonnet tier). Persistent caching is a Phase 36+ optimization.

3. **Word renderer changes**
   - What we know: User decision says Word stays "functional and clean, not Bloomberg-grade."
   - What's unclear: Does the Word renderer need any changes for density-aware rendering, or does it stay exactly as-is?
   - Recommendation: Minimal Word changes — add density-tier indicators (simple colored text) and pre-computed narratives. Do NOT port the Bloomberg HTML design to Word. Word is the "edit this" version; PDF is the "present this" version.

4. **Fallback when Playwright is not available**
   - What we know: WeasyPrint is currently an optional dependency (`pdf = ["weasyprint>=60.0"]`).
   - What's unclear: Should Playwright also be optional? If so, what's the fallback?
   - Recommendation: Make Playwright optional (like WeasyPrint). Fallback chain: Playwright -> WeasyPrint -> skip PDF. Log warning at each fallback level.

## Sources

### Primary (HIGH confidence)
- Playwright Python docs: https://playwright.dev/python/docs/api/class-page#page-pdf — `page.pdf()` API reference
- Playwright PDF generation guide: https://www.checklyhq.com/docs/learn/playwright/generating-pdfs/
- WeasyPrint Flexbox issue #324: https://github.com/Kozea/WeasyPrint/issues/324 — Confirms incomplete Flexbox support
- WeasyPrint CSS Grid issue #543: https://github.com/Kozea/WeasyPrint/issues/543 — Confirms incomplete Grid support
- Plotly static export docs: https://plotly.com/python/static-image-export/ — Kaleido-based static export
- Jinja2 macros as components: https://fluix.one/blog/jinja-macros/

### Secondary (MEDIUM confidence)
- HTML-to-PDF library comparison 2025: https://pdfbolt.com/blog/python-html-to-pdf-library
- Top 5 open source PDF generators 2025: https://wkhtmltopdf.com/top-5-open-source-pdf-generators-compared-2025/
- Matplotlib vs Plotly comparison: https://www.fabi.ai/blog/plotly-vs-matplotlib-a-quick-comparison-with-visual-guides
- LLM cost optimization: https://futureagi.com/blogs/llm-cost-optimization-2025

### Codebase (HIGH confidence)
- Current render architecture: 50+ files in `src/do_uw/stages/render/`
- Section assessments: `src/do_uw/stages/analyze/section_assessments.py` (187 lines, boolean clean/not-clean)
- Benchmark stage: `src/do_uw/stages/benchmark/__init__.py` (499 lines, already pre-computes thesis/risk/claim narratives)
- Check engine dispatch: `src/do_uw/stages/analyze/check_engine.py` lines 108-112 (content_type dispatch)
- Check definition model: `src/do_uw/knowledge/check_definition.py` (ContentType enum)
- Design system: `src/do_uw/stages/render/design_system.py` (188 lines, Angry Dolphin branding)
- Existing HTML template: `src/do_uw/templates/pdf/worksheet.html.j2` (417 lines)
- Existing CSS: `src/do_uw/templates/pdf/styles.css` (353 lines)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Playwright, Jinja2, matplotlib are well-documented, verified via official sources
- Architecture: MEDIUM-HIGH — Density tiers and check-type display are codebase-specific design; patterns are sound but untested at this scale
- Pitfalls: HIGH — Identified from real WeasyPrint/Playwright issues and existing codebase patterns
- LLM narratives: MEDIUM — Cost control and caching patterns are standard but narrative quality depends on prompt engineering during implementation
- Bloomberg design: MEDIUM — Typography and color recommendations based on professional financial report conventions, not verified against specific Bloomberg source

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (30 days — Playwright and Tailwind are stable, LLM pricing may shift)
