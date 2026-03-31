# Phase 43: HTML Presentation Quality — CapIQ Layout — Research

**Researched:** 2026-02-24
**Domain:** Jinja2 HTML templates, CSS layout architecture, data tracing infrastructure
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Layout density & structure:**
- Target density: CapIQ-grade — multi-column tables, minimal whitespace, 3-4 data points per row. Looks like a Bloomberg terminal printout.
- Page layout: Two-column — fixed left sidebar with section TOC, right side is dense data content.
- Sticky top bar: Company name, ticker, sector, market cap/size. Score does NOT go in the top bar — it lives in the body. No red flags in the top bar.
- Data tables: 3-column grid — Label | Value | Context/Benchmark. Every data point shows what it is, the value, and how it compares to peers or thresholds.

**Document section order:**
1. Company identity header block (company name, ticker, sector, size, description, run date)
2. Executive Summary
3. Red Flags (immediately after exec summary — risk-first flow)
4. Scoring (overall score + peril breakdown)
5. Financial
6. Market
7. Governance
8. Litigation
9. Appendix / Sources

No collapsible sections — always fully expanded. This is a document, not an app. Works correctly for print/PDF.

**Risk signal presentation:**
- Red Flags section: Priority-sorted table — Severity | Check name | Finding | Source. Worst issues first.
- Score & peril visualization: Claude's discretion — maximize BOTH visual impact AND data granularity.
- Check results within sections: Show only TRIGGERED/ELEVATED checks inline + a summary count line.
- Color palette: CapIQ-style — deep red / amber / green on white background.

**Data sourcing & traceability:**
- Sourcing method: Footnote numbers with a Sources appendix at end of document. Inline superscript numbers (¹ ² ³) on data points.
- Confidence display: Show confidence level ONLY when MEDIUM or LOW. High confidence is the default and shown silently.
- Missing data: Em dash (—) with a footnote explaining why.
- Sources appendix: End of document, numbered list: `¹ 10-K FY2024 (SEC EDGAR), filed 2024-02-23`

**Document navigation:**
- Sidebar TOC: Sticky — stays fixed as user scrolls. Active section highlighted. Click any section to jump.
- Sections: Always fully expanded — no toggles, no collapsing.

### Claude's Discretion
- Exact peril score visualization design (tile grid + table is the direction, specifics are open)
- Typography choices, exact spacing, font sizes
- Sidebar width and styling
- Exact footnote rendering implementation
- Chart/sparkline choices within sections (if any)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope

</user_constraints>

---

## Summary

Phase 43 is a **presentation-only overhaul** of the existing HTML output. The data pipeline, models, and scoring logic are frozen — this phase changes only what the user sees. The primary deliverable is a transformed `worksheet.html.j2` and its supporting templates/CSS that achieve S&P Capital IQ presentation density.

The current output is a single-column sequential document with a sticky top bar, section h2 headings, and alternating-row tables. It is readable but not institutionally credible — too much whitespace, no two-column layout, no sticky sidebar TOC, and no inline source footnotes. The gap between current output and CapIQ quality is primarily a **CSS architecture gap** (no two-column layout, no fixed sidebar) and a **template gap** (section ordering, footnote system, 3-col data grid, Red Flags section as dedicated block).

**Primary recommendation:** The work is pure HTML/CSS/Jinja2 — no new Python logic, no new models. Implement in six focused waves: (1) two-column layout + sticky sidebar, (2) section reordering + identity block, (3) 3-col data grid macro + section migration, (4) Red Flags dedicated section, (5) footnote/Sources infrastructure, (6) visual polish pass. Each wave is independently testable via HTML inspection.

---

## Standard Stack

### Core (already installed, no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.x (via project) | HTML templating | Already used for all HTML templates |
| Tailwind CSS v4 | compiled | Utility CSS | Already compiled into `compiled.css` via `build-css.sh` |
| Plain CSS | N/A | Custom styles | `styles.css` already handles custom CapIQ/Bloomberg classes |
| Python Intersection Observer API (JS) | browser-native | Sidebar active-section tracking | No new dependency needed — vanilla JS |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Vanilla JS (inline `<script>`) | browser-native | Sidebar IntersectionObserver for active highlighting | Required for scroll-based sidebar active state |
| CSS `position: sticky` | browser-native | Fixed sidebar that scrolls with page | No JS required for layout, just CSS |
| CSS `grid` / `flexbox` | browser-native | Two-column layout | Already used extensively in templates |

### No New Installs Needed
This phase requires zero new Python packages. All tooling is already in place:
- Tailwind CSS compilation: `bash scripts/build-css.sh --embed`
- Template rendering: existing `html_renderer.py` + `_render_html_template()`
- Test runner: `uv run pytest tests/stages/render/ -x`

---

## Architecture Patterns

### Current HTML Architecture (What Exists Today)

**Entry point:** `src/do_uw/templates/html/worksheet.html.j2`
```
{% extends "base.html.j2" %}
{% block content %}
  cover.html.j2       ← compact header bar (navy bg, company+ticker+tier+score)
  executive.html.j2   ← Section 1: Executive Summary
  company.html.j2     ← Section 2: Company Profile
  financial.html.j2   ← Section 3: Financial Health
  market.html.j2      ← Section 4: Market & Trading
  governance.html.j2  ← Section 5: Governance
  litigation.html.j2  ← Section 6: Litigation
  scoring.html.j2     ← Section 7: Scoring & Risk (contains red flags, peril, etc.)
  ai_risk.html.j2     ← Section 8: AI Risk
  appendices/meeting_prep.html.j2
  appendices/coverage.html.j2
{% endblock %}
```

**Base layout:** `base.html.j2` renders:
1. Sticky top nav (`.sticky-topbar`) — currently: name + ticker + tier badge + quality/composite scores + tier action + sector + market cap + date
2. Header (`.bg-navy`, printed) — currently duplicates name + date
3. `<main class="px-8 max-w-none">` — single-column, full width
4. Footer

**Current sticky top bar** shows too much: tier badge, quality score, composite score, tier action. Per decision: strip to identity-only (name, ticker, sector, size).

**Current section order** is: cover → executive → company → financial → market → governance → litigation → scoring. Required order is: identity → exec summary → red flags → scoring → financial → market → governance → litigation → appendix.

**Sections missing as standalone blocks:** Red Flags. Currently buried inside `scoring.html.j2` as a subsection (`<h3>Critical Red Flags</h3>`). Needs to become its own `sections/red_flags.html.j2` included right after exec summary.

### New Layout Architecture (What Phase 43 Builds)

**Two-column layout with fixed sidebar:**
```html
<div class="worksheet-layout">
  <!-- Left sidebar: sticky TOC (fixed, never scrolls away) -->
  <nav class="sidebar-toc" id="sidebar-toc">
    <ul>
      <li><a href="#identity" class="active">Identity</a></li>
      <li><a href="#executive-summary">Exec Summary</a></li>
      <li><a href="#red-flags">Red Flags</a></li>
      <li><a href="#scoring">Scoring</a></li>
      <li><a href="#financial-health">Financial</a></li>
      <li><a href="#market">Market</a></li>
      <li><a href="#governance">Governance</a></li>
      <li><a href="#litigation">Litigation</a></li>
      <li><a href="#sources">Sources</a></li>
    </ul>
  </nav>
  <!-- Right main content -->
  <main class="worksheet-main">
    {% block content %}{% endblock %}
  </main>
</div>
```

CSS:
```css
.worksheet-layout {
  display: grid;
  grid-template-columns: 180px 1fr;   /* sidebar + content */
  gap: 0;
  align-items: start;
}
.sidebar-toc {
  position: sticky;
  top: 0;              /* sticks at top when layout scrolls */
  height: 100vh;
  overflow-y: auto;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  padding: 1rem 0;
}
.worksheet-main {
  min-width: 0;        /* prevents grid blowout */
  padding: 0 1.5rem;
}
```

**Print/PDF handling:** Sidebar must be hidden in print (`display: none` in `@media print`). PDF generated via Playwright sees only the main content column, letter-page layout.

### 3-Column Data Grid Pattern

The 3-col `Label | Value | Context/Benchmark` grid is the key density improvement. This replaces the current 2-col `kv_table` macro for all data points that have benchmark context available.

New macro in `components/tables.html.j2`:
```jinja2
{# 3-column data grid: Label | Value | Context/Benchmark.
   label: metric name
   value: formatted value (or em dash if missing)
   context: peer benchmark, threshold, or status context
   footnote_num: optional superscript reference number
   confidence: if MEDIUM or LOW, show "(est.)" or "(web)" marker
#}
{% macro data_row(label, value, context="", footnote_num=none, confidence="HIGH") %}
<tr>
  <td class="dr-label">{{ label }}</td>
  <td class="dr-value">
    {{ value if value else "—" }}
    {% if footnote_num %}<sup class="fn-ref">{{ footnote_num }}</sup>{% endif %}
    {% if confidence == "MEDIUM" %}<span class="conf-marker">(est.)</span>{% endif %}
    {% if confidence == "LOW" %}<span class="conf-marker">(web)</span>{% endif %}
  </td>
  <td class="dr-context">{{ context }}</td>
</tr>
{% endmacro %}
```

CSS classes:
```css
.dr-label { width: 35%; font-weight: 600; font-size: 10pt; color: var(--do-navy); }
.dr-value { width: 30%; font-variant-numeric: tabular-nums; font-size: 10pt; }
.dr-context { width: 35%; font-size: 9pt; color: var(--do-text-secondary); }
.conf-marker { font-size: 8pt; font-style: italic; color: #9ca3af; margin-left: 3px; }
```

### Footnote/Sources System

No footnote infrastructure exists today. The render context has no footnote collector. Two implementation approaches:

**Option A: Build-time footnote collector in Jinja2 (RECOMMENDED)**
Use a Jinja2 namespace object passed through context to accumulate footnotes as templates render. Each `data_row` call can register a source and receive a footnote number.

Implementation in `html_renderer.py` `build_html_context()`:
```python
# FootnoteCollector tracks sources and assigns numbers
class FootnoteCollector:
    def __init__(self):
        self._sources: list[str] = []
        self._index: dict[str, int] = {}

    def add(self, source_text: str) -> int:
        """Register a source, return its footnote number (1-based)."""
        if source_text in self._index:
            return self._index[source_text]
        self._sources.append(source_text)
        num = len(self._sources)
        self._index[source_text] = num
        return num

    @property
    def sources(self) -> list[tuple[int, str]]:
        return list(enumerate(self._sources, 1))

context["footnotes"] = FootnoteCollector()
```

In Jinja2 templates, calling `{% set fn = footnotes.add("10-K FY2024, filed 2024-02-23") %}` won't work because Jinja2 doesn't support Python object mutation through template calls in autoescape mode.

**Practical constraint:** Jinja2 templates cannot easily call Python methods that mutate shared state during rendering (the template is rendered in a single pass). The workaround is to **pre-collect all source citations in `build_html_context()`** and assign footnote numbers before rendering.

**Option B: Pre-collected footnotes in Python (CLEANER)**
In `build_html_context()`, iterate over all data points in the state that have `.source` fields and build a `footnotes` list pre-render. Each template then uses a footnote lookup filter:

```python
# In build_html_context():
footnote_registry = _build_footnote_registry(state)
context["footnote_registry"] = footnote_registry
# Dict: source_string -> int (footnote number)
context["all_sources"] = list(enumerate(sorted(footnote_registry, key=footnote_registry.get), 1))
```

Template usage:
```jinja2
{{ value }}<sup>{{ footnote_registry.get(source_key, '') }}</sup>
```

**Recommendation:** Use Option B. Pre-collect in Python where logic is clean and testable. The Sources appendix template then simply iterates `all_sources`.

**What source data exists in AnalysisState:**
- `SourcedValue[T]` model: `value`, `source` (filing type + date + URL), `confidence` (HIGH/MEDIUM/LOW), `as_of`, `retrieved_at`
- Check results in `state.analysis.check_results` have `trace_data_source` (already parsed by `_format_filing_ref()` in html_renderer.py)
- Financial data: `state.extracted.financials` — uses `SourcedValue` wrappers
- Market data: `state.extracted.market` — uses `SourcedValue` wrappers
- Check results: `filing_ref` already computed in `_group_checks_by_section()`

**Missing data as em dash:** Currently `format_na` filter returns `"N/A"` for None values. Phase 43 changes this to `"—"` (em dash) for display, while the footnote system can add a footnote explaining why (not applicable vs. acquisition failed vs. not disclosed).

### Red Flags as Dedicated Section

Currently `red_flags` lives inside `scoring.html.j2`. The required section order puts Red Flags immediately after Executive Summary. Two implementation strategies:

**Strategy A: Extract to `sections/red_flags.html.j2`**
- Create `src/do_uw/templates/html/sections/red_flags.html.j2`
- Pull the red_flags rendering block out of `scoring.html.j2`
- Include in `worksheet.html.j2` between `executive.html.j2` and `scoring.html.j2`
- The scoring section retains a brief "see Red Flags section above" reference

**Strategy B: Reorder sections and keep red_flags in scoring**
- Move `scoring.html.j2` to appear right after `executive.html.j2`
- The Red Flags `<h3>` inside scoring becomes prominently visible at top of scoring section

**Recommendation:** Strategy A. The user decision says Red Flags is a distinct section — giving it its own `<section id="red-flags">` enables proper sidebar TOC linking, scroll tracking, and print page control.

The Red Flags section renders from `sc.get('red_flags', [])` which is already available in the template context. The table format: Severity | Check name | Finding | Source — maps cleanly to current `RedFlagResult` model fields:
- Severity: `flag.get('ceiling')` or derived from flag triggered state
- Check name: `flag.name`
- Finding: `flag.description`
- Source: `flag.evidence` (list — can concatenate first 2)

### Sticky Top Bar Modification

Current `base.html.j2` sticky top bar shows: name, ticker, tier badge, quality score, composite score, tier action, sector, market cap, employees, date.

Required: Strip to identity-only — name, ticker, sector, size. No score, no tier, no action.

Change in `base.html.j2`, lines 38-75:
```html
<nav class="sticky-topbar no-print" id="sticky-topbar">
  <div class="sticky-topbar-inner">
    <span class="sticky-topbar-company">{{ company_name }}</span>
    {% if ticker %}<span class="sticky-topbar-ticker">({{ ticker }})</span>{% endif %}
    {% if sector %}<span class="sticky-topbar-sep">|</span><span class="sticky-topbar-meta">{{ sector }}</span>{% endif %}
    {% if snap.get('market_cap') %}<span class="sticky-topbar-sep">|</span><span class="sticky-topbar-meta">{{ snap.market_cap }}</span>{% endif %}
    <span class="sticky-topbar-date">{{ generation_date }}</span>
  </div>
</nav>
```

The header block (`<header class="bg-navy...">`) can be removed (it duplicates info that now lives in the identity block and sidebar).

### Company Identity Block

Per decision, section order starts with "Company identity header block (company name, ticker, sector, size, description, run date)." This replaces the current `cover.html.j2` compact header bar, which shows company name and tier badge (not the right content).

New `sections/identity.html.j2` replaces `sections/cover.html.j2`:
```html
<section id="identity">
  <div class="identity-block">
    <h1>{{ company_name }}</h1>
    <p class="identity-meta">{{ ticker }} — {{ exchange }} | {{ sector }} | {{ sic_code }}</p>
    <p class="identity-desc">{{ business_description }}</p>
    <p class="identity-run">Analysis run: {{ generation_date }}</p>
  </div>
  <!-- 3-col summary metrics -->
  <div class="identity-metrics">
    {{ data_row("Market Cap", snap.market_cap, context=market_cap_tier) }}
    {{ data_row("Revenue", snap.revenue, context=revenue_vs_peers) }}
    {{ data_row("Employees", snap.employees, context=employee_tier) }}
    {{ data_row("Years Public", classification.years_public, context="") }}
  </div>
</section>
```

### Section Ordering Change in worksheet.html.j2

Current order:
```
cover → executive → company → financial → market → governance → litigation → scoring → ai_risk → meeting_prep → coverage
```

Required order:
```
identity → executive → red_flags → scoring → financial → market → governance → litigation → [ai_risk] → [meeting_prep] → sources_appendix → [coverage]
```

Changes:
1. Replace `cover.html.j2` with `sections/identity.html.j2`
2. Add `sections/red_flags.html.j2` after `sections/executive.html.j2`
3. Move `sections/scoring.html.j2` before `sections/financial.html.j2`
4. Rename `sections/company.html.j2` — per the section order, there is no longer a standalone "Company" section header. The company identity content becomes the opening identity block, and the detailed company profile subsections (business description, peer group, etc.) can either remain as a section or merge into the identity block. **DECISION NEEDED:** The user's section order has no "Company" section — it goes directly to Financial after Scoring. Clarify whether detailed company profile content (business description, subsidiaries, peer group, etc.) merges into identity block or gets a separate "Company" section between Identity and Exec Summary.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sidebar active-section tracking | Custom scroll event listener | `IntersectionObserver` API | Browser-native, efficient, works with any scroll speed |
| CSS sticky sidebar | Manual JS offset calculation | `position: sticky` + CSS Grid | Zero JS, works in Playwright PDF context |
| Two-column layout | Table-based layout | CSS Grid (`grid-template-columns: 180px 1fr`) | Print-safe, responsive, no table semantic issues |
| Footnote numbering | Template-level counters | Python pre-collection in `build_html_context()` | Jinja2 can't mutate shared state reliably during render |
| Print hiding sidebar | JS detection | `@media print { .sidebar-toc { display: none } }` | Pure CSS, reliable in Playwright |

---

## Common Pitfalls

### Pitfall 1: Two-Column Layout Breaks Playwright PDF
**What goes wrong:** CSS Grid sidebar layout renders correctly in browser but Playwright PDF renders only one column or clips content.
**Why it happens:** Playwright's PDF mode is closer to `@media print` than browser screen mode. `position: sticky` and `height: 100vh` behave differently.
**How to avoid:** The sidebar must be hidden in `@media print`. Use `display: none !important` on `.sidebar-toc`. The `<main>` content should then be full-width in print. Test by running `render_html_pdf()` and inspecting the PDF, not just the browser HTML.
**Warning signs:** PDF missing content on the right, or the sidebar appearing as a blank column in PDF output.

### Pitfall 2: Jinja2 Autoescape Breaks HTML in Macro Arguments
**What goes wrong:** When passing HTML strings (e.g., badge HTML) as macro arguments in autoescape mode, the HTML gets escaped and shows as literal tags.
**Why it happens:** Jinja2 autoescape is `True` in the current env setup.
**How to avoid:** Use `| safe` filter when passing pre-rendered HTML into macros, or use `Markup` in Python-side pre-rendering. Alternatively, use Jinja2 `{% call %}` blocks instead of passing HTML as arguments.

### Pitfall 3: IntersectionObserver Fires Before DOM is Ready
**What goes wrong:** Sidebar active state doesn't update correctly — all items highlighted or none highlighted.
**Why it happens:** IntersectionObserver registered before sections have proper bounding boxes.
**How to avoid:** Register observer on `DOMContentLoaded`. Use threshold `[0, 0.1]` and `rootMargin: '-10% 0px -80% 0px'` to trigger when section header enters the viewport top zone.

### Pitfall 4: CSS Conflicts Between Tailwind and Custom Sidebar CSS
**What goes wrong:** Tailwind utility classes applied to sidebar elements override custom sidebar CSS, causing layout breaks.
**Why it happens:** Tailwind v4 has high specificity on utilities; sidebar styles in `styles.css` may lose.
**How to avoid:** Add sidebar CSS to `styles.css` (which is loaded AFTER compiled.css and uses CSS custom properties). Use `!important` only where necessary to override. Run `uv run tailwindcss -i input.css -o compiled.css --minify` after adding new class names to templates.

### Pitfall 5: Section Reordering Breaks Template Context Dependencies
**What goes wrong:** `red_flags.html.j2` references `scoring` context variable, but scoring template is now AFTER red flags in the include order.
**Why it happens:** The `scoring` variable is populated in `build_html_context()` before rendering, so order of includes doesn't matter for context. But if any section writes to a shared Jinja2 namespace variable, order matters.
**How to avoid:** All context variables are built in Python before any template renders (`build_html_context()` returns a complete dict). The include order in `worksheet.html.j2` is safe to change without worrying about context dependencies.

### Pitfall 6: Compiled CSS Missing New Classes
**What goes wrong:** New CSS utility classes added to templates (e.g., `sidebar-active`) don't appear in the rendered HTML because they weren't compiled into `compiled.css`.
**Why it happens:** Tailwind v4 scans `@source "../../../do_uw/templates/html"` to find used classes. New custom classes in `styles.css` don't need recompilation. But new Tailwind utility classes do.
**How to avoid:** After adding new Tailwind utility class names to templates, run `bash scripts/build-css.sh --embed` to recompile `compiled.css`. For sidebar-specific styles, add to `styles.css` instead (custom CSS, no recompile needed).

### Pitfall 7: `format_na` Returns "N/A" Instead of Em Dash
**What goes wrong:** Missing data shows "N/A" when the design requires em dash (—).
**Why it happens:** `format_na` filter in `formatters.py` returns "N/A" for None values.
**How to avoid:** Either (a) add a new `format_em` filter that returns "—" for None, or (b) modify `format_na` to return "—". Check call sites — `format_na` is used in hundreds of template locations, so a modification would affect all of them. Safest: add `format_em` filter and use it in new 3-col grid macros; leave `format_na` for backward compatibility.

---

## Code Examples

### Pattern 1: IntersectionObserver for Sidebar Active State
Verified pattern from MDN + Intersection Observer browser standard:
```javascript
// Add to base.html.j2 before </body>
// Marks sidebar links as 'active' as sections scroll into view.
(function() {
  const tocLinks = document.querySelectorAll('.sidebar-toc a[href^="#"]');
  const sections = document.querySelectorAll('section[id]');
  if (!sections.length || !tocLinks.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        tocLinks.forEach(a => a.classList.remove('active'));
        const active = document.querySelector(`.sidebar-toc a[href="#${id}"]`);
        if (active) active.classList.add('active');
      }
    });
  }, {
    rootMargin: '-10% 0px -80% 0px',
    threshold: [0, 0.1]
  });

  sections.forEach(s => observer.observe(s));
})();
```

### Pattern 2: CSS Grid Two-Column Layout
```css
/* Add to styles.css */
.worksheet-layout {
  display: grid;
  grid-template-columns: 180px 1fr;
  align-items: start;
}

.sidebar-toc {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  padding: 0.75rem 0;
  font-size: 11px;
}

.sidebar-toc a {
  display: block;
  padding: 4px 12px;
  color: var(--do-text-secondary);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.1s;
}

.sidebar-toc a:hover,
.sidebar-toc a.active {
  color: var(--do-navy);
  border-left-color: var(--do-navy);
  background: white;
  font-weight: 600;
}

.worksheet-main {
  min-width: 0;
  padding: 0 1.5rem;
}

@media print {
  .worksheet-layout {
    display: block;  /* Single column in print */
  }
  .sidebar-toc {
    display: none !important;
  }
  .worksheet-main {
    padding: 0;
  }
}
```

### Pattern 3: Pre-collecting Footnotes in build_html_context()
```python
# In html_renderer.py

class FootnoteRegistry:
    """Pre-collected source citations for footnote rendering."""
    def __init__(self) -> None:
        self._sources: list[str] = []
        self._index: dict[str, int] = {}

    def register(self, source_text: str) -> int:
        """Register source, return footnote number (1-based). Idempotent."""
        if not source_text:
            return 0
        if source_text in self._index:
            return self._index[source_text]
        self._sources.append(source_text)
        num = len(self._sources)
        self._index[source_text] = num
        return num

    def get(self, source_text: str) -> int:
        """Get footnote number for existing source, 0 if not registered."""
        return self._index.get(source_text, 0)

    @property
    def all_sources(self) -> list[tuple[int, str]]:
        """Return list of (number, source_text) for Sources appendix."""
        return list(enumerate(self._sources, 1))


def _build_footnote_registry(state: AnalysisState) -> FootnoteRegistry:
    """Pre-collect all data sources from AnalysisState into registry."""
    reg = FootnoteRegistry()
    # Register check results sources
    if state.analysis and state.analysis.check_results:
        for check_id, result in state.analysis.check_results.items():
            if isinstance(result, dict) and result.get("trace_data_source"):
                src = _format_filing_ref(result["trace_data_source"])
                if src:
                    reg.register(src)
    # Register filing sources
    if state.acquired_data and state.acquired_data.filing_documents:
        for form_type, docs in state.acquired_data.filing_documents.items():
            for doc in docs:
                date = doc.get("filing_date", "")
                src = f"{form_type} {date} (SEC EDGAR)"
                if date:
                    reg.register(src)
    return reg
```

### Pattern 4: 3-Column Data Grid Macro
New macro to add to `components/tables.html.j2`:
```jinja2
{# 3-column data grid row: Label | Value | Context/Benchmark.
   For CapIQ-density rendering of individual data points.
   context_text: peer benchmark, threshold, or status context.
                 Empty string if no context available.
   footnote_num: integer (1-99) or 0/none for no footnote.
   confidence: HIGH (default, silent), MEDIUM -> (est.), LOW -> (web) #}
{% macro data_row(label, value, context_text="", footnote_num=0, confidence="HIGH") %}
<tr class="dr-row">
  <td class="dr-label">{{ label }}</td>
  <td class="dr-value tabular-nums">
    {%- if value -%}
      {{ value }}
    {%- else -%}
      <span class="dr-missing">&mdash;</span>
    {%- endif -%}
    {%- if footnote_num %}<sup class="fn-ref"><a href="#fn-{{ footnote_num }}">{{ footnote_num }}</a></sup>{% endif -%}
    {%- if confidence == "MEDIUM" %}<span class="conf-marker"> (est.)</span>{% endif -%}
    {%- if confidence == "LOW" %}<span class="conf-marker"> (web)</span>{% endif -%}
  </td>
  <td class="dr-context">{{ context_text }}</td>
</tr>
{% endmacro %}

{# 3-column data grid wrapper table.
   Wraps a series of data_row macros with minimal header overhead. #}
{% macro data_grid(title="") %}
<table class="w-full border-collapse text-sm data-grid-table">
  {% if title %}
  <thead>
    <tr><th colspan="3" class="data-grid-title">{{ title }}</th></tr>
  </thead>
  {% endif %}
  <tbody>
    {{ caller() }}
  </tbody>
</table>
{% endmacro %}
```

CSS additions:
```css
/* 3-column data grid */
.data-grid-table { margin: 0.5rem 0; }
.data-grid-title {
  background: var(--do-navy); color: white;
  font-family: Calibri, sans-serif; font-size: 9pt; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 3px 6px;
}
.dr-row:nth-child(odd) { background: var(--do-bg-alt); }
.dr-label {
  width: 35%; padding: 2px 6px;
  font-weight: 600; font-size: 10pt; color: var(--do-navy);
}
.dr-value {
  width: 30%; padding: 2px 6px;
  font-variant-numeric: tabular-nums;
}
.dr-context {
  width: 35%; padding: 2px 6px;
  font-size: 9pt; color: var(--do-text-secondary);
}
.dr-missing { color: var(--do-neutral-gray); }
.fn-ref { font-size: 8pt; vertical-align: super; line-height: 0; }
.fn-ref a { color: var(--do-navy); text-decoration: none; }
.conf-marker { font-size: 8pt; font-style: italic; color: #9ca3af; }
```

### Pattern 5: Red Flags Dedicated Section Template
```jinja2
{# Red Flags dedicated section — Priority-sorted table.
   Severity | Check name | Finding | Source
   Pulled from scoring context (already populated by SCORE stage) #}
{% set sc = scoring or {} %}
{% set red_flags = sc.get('red_flags', []) %}
{% set triggered_flags = red_flags | selectattr('triggered', 'defined') | selectattr('triggered') | list
                         if red_flags and red_flags[0] is mapping and 'triggered' in red_flags[0]
                         else red_flags %}

<section id="red-flags" class="page-break">
  <h2>Red Flags</h2>
  {% if triggered_flags %}
  <p class="text-sm text-gray-600 mb-2">
    {{ triggered_flags|length }} critical risk signal{{ 's' if triggered_flags|length != 1 }} identified.
    Reviewed in severity order — worst issues first.
  </p>
  <table class="w-full border-collapse text-sm my-3">
    <thead>
      <tr class="bg-navy text-white">
        <th class="...">Severity</th>
        <th class="...">Flag</th>
        <th class="...">Finding</th>
        <th class="...">Source</th>
      </tr>
    </thead>
    <tbody>
      {% for flag in triggered_flags %}
      <tr class="bg-red-50">
        <td>{{ traffic_light("TRIGGERED", "CRITICAL") }}</td>
        <td class="font-semibold">{{ flag.name }}</td>
        <td class="text-xs">{{ flag.description }}</td>
        <td class="text-xs text-gray-500">{{ flag.evidence[0] if flag.evidence else '—' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="text-sm text-gray-500">No critical red flags triggered.</p>
  {% endif %}
</section>
```

---

## Current Output vs. CapIQ: Specific Gaps

| Dimension | Current Output | CapIQ Target | Gap Size |
|-----------|---------------|--------------|----------|
| Layout | Single-column, full-width | Two-column: 180px sidebar + content | Large — CSS architecture change |
| Section order | cover→exec→company→fin→market→gov→lit→scoring | identity→exec→red_flags→scoring→fin→market→gov→lit | Medium — template reordering |
| Top bar | Name+tier badge+scores+action | Name+ticker+sector+size only | Small — template trim |
| Data density | 2-col kv_table (Label | Value) | 3-col grid (Label | Value | Context) | Medium — new macro + migration |
| Red flags | Buried in Section 7 scoring | Dedicated section after exec summary | Medium — extract + reorder |
| Source tracing | Per-check `Source: 10-K Item 3` text inline | Superscript numbers + Sources appendix | Large — new infrastructure |
| Missing data | "N/A" string | Em dash (—) + footnote | Small — filter change |
| Confidence display | Current: `(low conf.)` marker | MEDIUM: "(est.)", LOW: "(web)" only | Small — marker text change |
| Color palette | Navy/gold/risk-red/risk-amber | CapIQ red/amber/green — matches current | None — already correct |
| Typography | Calibri, 10pt body | Calibri, 10pt body | None — already matches |
| Print sidebar | N/A (no sidebar today) | Hidden in @media print | None yet — add with sidebar |

---

## Data Availability for 3-Column Grid

**What benchmark/context data exists in render context:**

From `BenchmarkResult` (available as `state.benchmark`):
- `peer_group_tickers`: list of peer tickers
- `peer_rankings`: `dict[metric_name, percentile_rank]`
- `metric_details`: `dict[metric_name, MetricBenchmark]` with `percentile_rank`, `peer_count`, `baseline_value`, `higher_is_better`
- `sector_average_score`: sector-level quality score
- `relative_position`: BEST_IN_CLASS / ABOVE_AVERAGE / etc.

From `peer_context.py`:
- `format_metric_with_context()` already formats "X (72nd percentile vs. 15 peers; median $8.1B)"

The 3-col context column can use:
- For financial metrics: `"72nd pct (peer median: $8.1B)"`
- For scoring factors: `"Max: 20 pts | Current: 12 pts"`
- For market metrics: `"vs. S&P 500 YTD: +12%"`
- For governance scores: `"Peer avg: 71"`
- When no benchmark available: `""` (empty — context column is blank, not "N/A")

**SourcedValue fields accessible for footnotes:**

Most extracted data uses `SourcedValue[T]` with `.source` (filing + date + URL) and `.confidence` (HIGH/MEDIUM/LOW). Specifically:
- `state.company.identity.*` — all `SourcedValue` fields
- `state.extracted.financials.*` — uses `SourcedValue`
- `state.extracted.market.*` — uses `SourcedValue`
- Check results: `trace_data_source` (already formatted by `_format_filing_ref()`)
- Filing documents: `form_type`, `filing_date` available

The footnote registry can be built from these sources pre-render.

---

## File Inventory: Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `src/do_uw/templates/html/sections/identity.html.j2` | Company identity block (replaces cover.html.j2) |
| `src/do_uw/templates/html/sections/red_flags.html.j2` | Dedicated Red Flags section |
| `src/do_uw/templates/html/appendices/sources.html.j2` | Numbered Sources appendix |
| `tests/stages/render/test_html_layout.py` | Layout structure tests |

### Modified Files
| File | Change Summary |
|------|---------------|
| `src/do_uw/templates/html/base.html.j2` | Add two-column grid wrapper, strip scores from sticky topbar, add sidebar TOC, add JS IntersectionObserver |
| `src/do_uw/templates/html/worksheet.html.j2` | Reorder includes per new section order |
| `src/do_uw/templates/html/styles.css` | Add sidebar CSS, 3-col grid CSS, footnote CSS |
| `src/do_uw/templates/html/components/tables.html.j2` | Add `data_row` macro, `data_grid` macro |
| `src/do_uw/templates/html/sections/scoring.html.j2` | Remove red_flags block (moved to red_flags.html.j2) |
| `src/do_uw/stages/render/html_renderer.py` | Add `FootnoteRegistry` class, `_build_footnote_registry()`, add `format_em` filter |
| `src/do_uw/stages/render/formatters.py` | Add `format_em_dash()` function |

### Sections to Migrate to 3-col Data Grid (High Value)
These sections have the highest concentration of data points that benefit from context column:
1. `sections/executive.html.j2` — company profile block, size metrics
2. `sections/financial.html.j2` — key financial metrics block
3. `sections/scoring.html.j2` — tier classification block, claim probability
4. `sections/market.html.j2` — stock performance metrics

---

## Open Questions

1. **Company section fate in new section order**
   - What we know: User's section order is identity → exec → red flags → scoring → financial → market → governance → litigation → appendix. There is no "Company" section listed.
   - What's unclear: Does detailed company content (business description, peer group, SIC/industry analysis, subsidiary count, event timeline) get folded into the identity block? Or kept as a section that comes before financial?
   - Recommendation: Treat the detailed company profile as part of the identity section (expanded), or keep `sections/company.html.j2` but rename it "Company Profile" in the sidebar TOC and place it between identity and exec summary.

2. **Sidebar width and content depth**
   - What we know: Sidebar is sticky, always expanded, shows section names.
   - What's unclear: Should subsections appear as indented items? (e.g., Financial → Balance Sheet, Income Statement, Distress Indicators)
   - Recommendation: Keep TOC to top-level sections only for Phase 43. Subsection links are a Phase 44+ enhancement.

3. **Coverage of `format_na` → em dash migration scope**
   - What we know: `format_na` is used in ~100+ template locations via `{{ value | format_na }}`.
   - What's unclear: Should ALL `format_na` calls switch to em dash, or only new 3-col grid calls?
   - Recommendation: Add `format_em` as a new filter (`—` for None, value otherwise). Use it in new `data_row` macro. Leave `format_na` ("N/A") unchanged for existing 2-col tables to avoid broad regression risk.

4. **Jinja2 `{% call %}` block for data_grid macro**
   - What we know: The `data_grid` macro wraps `{{ caller() }}` — this requires `{% call %}` syntax which is supported in Jinja2 but not currently used in the templates.
   - What's unclear: Whether the autoescape mode causes issues with `caller()` output.
   - Recommendation: Test `{% call %}` in a minimal template before committing to the pattern. Fallback: pass rows as a list parameter instead.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/stages/render/ -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |
| Estimated runtime | ~8s (render tests) / ~60s (full suite) |

### Phase Requirements → Test Map
| Behavior | Test Type | Command |
|----------|-----------|---------|
| Two-column layout CSS classes present in rendered HTML | unit | `pytest tests/stages/render/test_html_layout.py::test_two_column_layout -x` |
| Sidebar TOC contains all required section IDs | unit | `pytest tests/stages/render/test_html_layout.py::test_sidebar_toc_links -x` |
| Sticky topbar has no score/tier in new format | unit | `pytest tests/stages/render/test_html_layout.py::test_topbar_identity_only -x` |
| Section order matches decision: exec→red_flags→scoring→financial | unit | `pytest tests/stages/render/test_html_layout.py::test_section_order -x` |
| Red Flags section renders as standalone section | unit | `pytest tests/stages/render/test_html_layout.py::test_red_flags_section -x` |
| 3-col `data_row` macro renders label/value/context | unit | `pytest tests/stages/render/test_html_components.py::test_data_row_macro -x` |
| `FootnoteRegistry` assigns sequential numbers, deduplicates | unit | `pytest tests/stages/render/test_html_layout.py::test_footnote_registry -x` |
| Sources appendix renders numbered list | unit | `pytest tests/stages/render/test_html_layout.py::test_sources_appendix -x` |
| Em dash for missing values (None → —) | unit | `pytest tests/stages/render/test_formatters.py::test_format_em_dash -x` |
| Existing HTML renderer tests still pass | regression | `pytest tests/stages/render/test_html_renderer.py -x` |
| Existing HTML components tests still pass | regression | `pytest tests/stages/render/test_html_components.py -x` |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every template change → run: `uv run pytest tests/stages/render/ -x -q`
- **Full suite trigger:** Before marking any wave as complete
- **Phase-complete gate:** Full suite green + manual HTML inspection of AAPL output
- **Estimated feedback latency per task:** ~8 seconds

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/stages/render/test_html_layout.py` — new test file covering layout structure, sidebar, section order, footnote registry
- [ ] `FootnoteRegistry` unit test coverage in new test file

---

## Sources

### Primary (HIGH confidence)
- Codebase inspection (direct file reads) — `html_renderer.py`, `base.html.j2`, `worksheet.html.j2`, `styles.css`, all section templates, `tables.html.j2`, `badges.html.j2`, `callouts.html.j2`, `narratives.html.j2`
- `models/common.py` — `SourcedValue[T]` and `Confidence` enum
- `models/scoring.py` — `MetricBenchmark`, `BenchmarkResult` fields
- `stages/render/peer_context.py` — existing benchmark formatting functions
- `stages/render/html_renderer.py` — `build_html_context()`, `_format_filing_ref()`, `_group_checks_by_section()`
- `pyproject.toml` — pytest configuration, confirmed framework version
- Existing passing tests — `test_html_renderer.py` (21 tests pass), `test_html_components.py`

### Secondary (MEDIUM confidence)
- IntersectionObserver pattern — standard browser API, widely documented; MDN-verified behavior
- CSS Grid sticky sidebar pattern — standard CSS, widely used for documentation sites

### Tertiary (LOW confidence)
- None — all findings are grounded in direct codebase inspection

---

## Metadata

**Confidence breakdown:**
- Current architecture: HIGH — direct code inspection
- Required changes: HIGH — clear diff between current and target
- Implementation patterns: HIGH — CSS Grid and IntersectionObserver are established browser standards
- Footnote system: MEDIUM — Python pre-collection approach is sound but needs validation that Jinja2 call blocks work in autoescape mode
- Section order migration: HIGH — all required data is already in the render context; reordering is purely template includes

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (30 days — stable codebase)
