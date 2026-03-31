# Phase 114: Worksheet Restructure + Epistemological Trace - Research

**Researched:** 2026-03-17
**Domain:** HTML/CSS report restructure, information architecture, print optimization, data visualization
**Confidence:** HIGH

## Summary

Phase 114 transforms the existing HTML worksheet from a sequential section-by-section layout into a three-layer research report: (1) a dense risk scorecard page, (2) an executive brief + domain sections with integrated narrative, and (3) an epistemological trace appendix proving provenance. The primary challenge is architectural -- restructuring 142 existing Jinja2 templates and the base.html.j2 layout without breaking the existing rendering pipeline, while adding substantial new components (signal heatmap, CRF alert bar, decision record, H/A/E threading, signal drill-down panels).

The existing codebase is well-prepared for this: context builders already produce typed dicts, chart generators output SVG, the sidebar/sticky-nav/IntersectionObserver infrastructure exists, print CSS with @media print rules is established, and signal results are already grouped by section prefix. The work is primarily template restructuring + new context builder functions + new CSS, not deep pipeline changes.

**Primary recommendation:** Restructure base.html.j2 into a multi-page document template with distinct structural zones (scorecard, brief, sections, appendix), build 4-5 new context builders for the new components (scorecard, heatmap, CRF bar, decision record, epistemological trace), create corresponding Jinja2 templates, and update the sidebar TOC and print CSS to match the new structure.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Page 1: **Risk Scorecard** -- tier badge, H/A/E radar chart, 10-factor scores table, top concern signals, key financial metrics strip. Dense, visual, single-page
- Page 2: **Executive Brief** -- structured narrative summary covering company profile, key risks, notable findings. Standalone for secondary readers
- Pages 3+: **Domain sections** (Company, Financials, Market, Governance, Litigation, Scoring, Analysis) -- current section order preserved
- H/A/E threading: each section annotated with which H/A/E dimension it contributes to; H/A/E radar on page 1 links to relevant sections
- Narrative assessment is INTEGRATED per section (not a standalone chapter) -- each section has evaluative narrative paragraphs alongside data/charts
- Appendix: **Epistemological Trace** -- full signal provenance table
- Sticky TOC sidebar -- persistent left sidebar with section links, highlights current section on scroll, collapses on narrow screens
- Collapsible sections with chevrons (existing pattern, keep)
- Signal drill-down: in-page expansion (click signal reference -> inline detail panel showing raw data, source, threshold, evaluation)
- CRF alert bar: persistent banner at report top (below scorecard) listing all critical risk factors with severity
- Hybrid rendering: SVG for screen HTML, PNG for email/PDF export
- Signal heatmap: color-coded grid grouped by H/A/E dimension and signal category
- P x S matrix: individual signal dots on scatter plot, colored by H/A/E dimension
- Sparklines: grouped trends panel in risk overview PLUS inline sparklines next to key metrics throughout sections
- LLM-generated content shows confidence badges (HIGH/MEDIUM/LOW) based on underlying source data quality
- One report for all audiences -- no separate export profiles
- Epistemological Trace: ALL signals (triggered, clean, skipped), grouped by H/A/E, columns: Signal ID | Status | Raw Data | Source (filing+date+page) | Threshold Applied | Confidence Level | Source Type | Evaluation Result | Score Contribution
- Decision Record: separate page at end, captures posture + rationale, shows comparable tier distribution, no system recommendation

### Claude's Discretion
- Research and propose best presentation patterns from CIQ, Bloomberg, Moody's, S&P research reports
- Exact visual design of the scorecard page (layout, spacing, typography)
- Color palette and severity color mapping for heatmap/alerts
- Design of the H/A/E dimension annotation badges in section headers
- Sparkline chart style and size
- PDF page layout optimization (margins, headers, footers, page breaks)
- How collapsible sections behave when printing/exporting to PDF
- Sticky sidebar design and responsive breakpoints
- Signal heatmap cell sizing and grouping density
- Confidence badge visual design
- In-page expansion panel design for signal drill-down
- How the CRF banner links to relevant sections

### Deferred Ideas (OUT OF SCOPE)
- Supabase as centralized data store for run history and feedback
- Multiple export profiles per audience
- Interactive form fields for decision capture
- System recommendation engine with ML-based posture suggestion
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WS-01 | Part A: Programmatic Dashboard -- risk tier badge, H/A/E radar chart, signal heatmap, engine firing panel, P x S matrix, trend sparklines, CRF alert bar | Scorecard page template + 3 new context builders (scorecard_context, heatmap_context, crf_bar_context) + reuse existing hae_context, pattern_context, severity_context, sparklines.py |
| WS-02 | Part B: Narrative Assessment -- structured around H/A/E, LLM-generated | Integrated per-section evaluative narrative (existing _evaluative.py modules + 5-layer narrative architecture already in place) + H/A/E dimension badges |
| WS-03 | Part C: Epistemological Trace Appendix -- per-signal table with full provenance | New epistemological_trace_context builder consuming signal_results + brain signal YAML epistemology data via _signal_consumer |
| WS-04 | Updated golden baselines for visual regression | Test infrastructure exists (test_visual_regression.py, SECTION_IDS list, golden/ dir) -- update SECTION_IDS and regenerate baselines |
| WS-05 | Multi-audience info architecture | Scorecard + executive brief designed as standalone pages; sidebar TOC restructured with audience-oriented grouping |
| WS-06 | Screen vs. print UX divergence | Existing @media print rules, sidebar hidden in print, details expanded in pdf_mode. Extend with scorecard print optimization, heatmap print-color-adjust, CRF bar linearization |
| WS-07 | Decision documentation section | New decision_record template + context builder providing tier distribution stats from scoring model |
| WS-08 | Reading path design | Sidebar TOC restructured into audience groups; CRF banner links to relevant sections; H/A/E radar links to section anchors |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1+ | Template rendering | Already in use, 142 existing templates |
| Tailwind CSS | v4 | Utility-first styling | Already compiled (compiled.css), self-hosted fonts |
| matplotlib | 3.8+ | Chart generation (radar, P x S, stock charts) | Already in use for all chart types |
| Playwright | 1.40+ | HTML-to-PDF conversion | Already in use for PDF pipeline |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pure SVG (no library) | N/A | Sparklines, heatmap grid, inline charts | Already pattern: sparklines.py generates raw SVG strings |
| CSS Grid | N/A | Heatmap grid layout, scorecard layout | Native CSS, no library needed |
| IntersectionObserver | N/A | Sidebar scroll-spy, section tracking | Already implemented in base.html.j2 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure SVG heatmap | D3.js | D3 adds runtime JS dependency; pure SVG generated server-side is simpler and works in PDF |
| CSS Grid scorecard | Flexbox | CSS Grid better for 2D dense layouts (scorecard is a fixed grid) |
| Inline `<details>` drill-down | Modal/overlay | Details element already used throughout; consistent pattern, works in print |

## Architecture Patterns

### Recommended Template Structure
```
templates/html/
  base.html.j2              # Restructured: scorecard zone, brief zone, sections zone, appendix zone
  sections/
    scorecard.html.j2        # NEW: Page 1 risk scorecard
    executive_brief.html.j2  # NEW: Page 2 standalone brief (replaces cover.html.j2 + parts of executive.html.j2)
    crf_banner.html.j2       # NEW: Persistent CRF alert bar
    company.html.j2          # EXISTING: updated with H/A/E badges
    financial_statements.html.j2  # EXISTING: updated with H/A/E badges
    market.html.j2           # EXISTING: updated with H/A/E badges
    governance.html.j2       # EXISTING: updated with H/A/E badges
    litigation.html.j2       # EXISTING: updated with H/A/E badges
    scoring.html.j2          # EXISTING: updated with H/A/E badges
    decision_record.html.j2  # NEW: Decision documentation page
  appendices/
    epistemological_trace.html.j2  # NEW: Full signal provenance table
    meeting_prep.html.j2     # EXISTING
    coverage.html.j2         # EXISTING (may merge into trace)
    signal_audit.html.j2     # EXISTING (subsumed by trace)
  components/
    hae_badge.html.j2        # NEW: H/A/E dimension annotation macro
    signal_drilldown.html.j2 # NEW: Inline expansion panel for signal details
    confidence_badge.html.j2 # NEW: Confidence level indicator
    heatmap.html.j2          # NEW: Signal heatmap grid component
```

### Context Builder Structure
```
context_builders/
  scorecard_context.py       # NEW: Assembles scorecard page data (tier, scores, top concerns, metrics strip)
  heatmap_context.py         # NEW: Groups signals by H/A/E + category into grid data
  crf_bar_context.py         # NEW: Extracts CRF vetoes + critical signals for persistent banner
  decision_context.py        # NEW: Tier distribution stats, posture fields
  epistemological_trace.py   # NEW: Full signal provenance table data
  hae_context.py             # EXISTING: Already provides radar chart data
  pattern_context.py         # EXISTING: Already provides firing panel data
  severity_context.py        # EXISTING: Already provides P x S data
  scoring.py                 # EXISTING: Factor scores, red flags
```

### Pattern 1: Scorecard Page Layout (CSS Grid)
**What:** Dense single-page scorecard with tier badge, radar chart, 10-factor table, top concerns, metrics strip
**When to use:** Page 1 of the report -- must fit on one page when printed
**Example:**
```html
<!-- Scorecard uses CSS Grid for precise 2D layout -->
<div class="scorecard-grid">
  <div class="scorecard-tier"><!-- Tier badge + company identity --></div>
  <div class="scorecard-radar"><!-- H/A/E radar chart SVG --></div>
  <div class="scorecard-factors"><!-- 10-factor compact table --></div>
  <div class="scorecard-concerns"><!-- Top 5 triggered signals --></div>
  <div class="scorecard-metrics"><!-- Key financial metrics strip --></div>
  <div class="scorecard-heatmap"><!-- Signal heatmap mini --></div>
</div>
```
```css
.scorecard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 0.5rem;
  page-break-after: always;
}
@media print {
  .scorecard-grid { break-after: page; }
}
```

### Pattern 2: H/A/E Dimension Badge (Jinja2 Macro)
**What:** Small inline badge showing which H/A/E dimension(s) a section contributes to
**When to use:** Every domain section header
**Example:**
```html
{# Jinja2 macro in components/hae_badge.html.j2 #}
{% macro hae_badge(dimensions) %}
  {% for dim in dimensions %}
    <span class="hae-badge hae-{{ dim | lower }}">{{ dim[0] }}</span>
  {% endfor %}
{% endmacro %}

{# Usage in section header #}
<h2>Section 3: Financial Health {{ hae_badge(['Host']) }}</h2>
```
```css
.hae-badge {
  display: inline-block; padding: 0 0.3rem; border-radius: 2px;
  font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
  vertical-align: middle; margin-left: 0.3rem;
}
.hae-host { background: #1D4ED8; color: white; }
.hae-agent { background: #B91C1C; color: white; }
.hae-environment { background: #059669; color: white; }
```

### Pattern 3: Signal Drill-Down Panel (Details Element)
**What:** Click-to-expand inline panel showing signal provenance details
**When to use:** Any signal reference in the document can be clicked to reveal raw data, source, threshold, evaluation
**Example:**
```html
{# Inline signal drill-down using existing details pattern #}
<details class="signal-drilldown">
  <summary class="signal-ref">
    <span class="signal-id">{{ signal.signal_id }}</span>
    <span class="signal-status signal-{{ signal.status | lower }}">{{ signal.status }}</span>
  </summary>
  <div class="signal-detail-panel">
    <table class="signal-provenance">
      <tr><th>Raw Value</th><td>{{ signal.value }}</td></tr>
      <tr><th>Source</th><td>{{ signal.source }}</td></tr>
      <tr><th>Threshold</th><td>{{ signal.threshold_context }}</td></tr>
      <tr><th>Rule Origin</th><td>{{ signal.epistemology_rule_origin }}</td></tr>
      <tr><th>Confidence</th><td>{{ signal.confidence }}</td></tr>
      <tr><th>Score Contribution</th><td>{{ signal.factors | join(', ') }}</td></tr>
    </table>
  </div>
</details>
```

### Pattern 4: Pure SVG Heatmap (Server-Side Generation)
**What:** Color-coded grid of signal cells grouped by H/A/E dimension and category
**When to use:** Scorecard page heatmap component
**Rationale:** Server-side SVG (like existing sparklines.py) means no JS dependency, works in PDF, deterministic output
**Example:**
```python
# heatmap_context.py pattern
def build_heatmap_context(
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Group signals into H/A/E x category grid for heatmap rendering."""
    grid: dict[str, dict[str, list[dict]]] = {
        "host": {}, "agent": {}, "environment": {}
    }
    for sig_id, result in signal_results.items():
        view = get_signal_result(sig_id, signal_results)
        if not view:
            continue
        rap = view.rap_class.lower()
        cat = view.rap_subcategory or "general"
        grid.setdefault(rap, {}).setdefault(cat, []).append({
            "id": sig_id,
            "status": view.status,
            "level": view.threshold_level,
            "value": view.value,
        })
    return {"heatmap_grid": grid, "heatmap_available": True}
```

### Pattern 5: Epistemological Trace Table
**What:** Full provenance table for ALL signals -- the audit trail
**When to use:** Appendix section
**Approach:** Use SignalResultView's epistemology fields (already available via _signal_consumer.py) + brain signal YAML data
**Example:**
```python
def build_epistemological_trace(
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Build full signal provenance table grouped by H/A/E."""
    rows: list[dict[str, Any]] = []
    for sig_id, raw_result in signal_results.items():
        view = get_signal_result(sig_id, signal_results)
        if not view:
            continue
        rows.append({
            "signal_id": sig_id,
            "status": view.status,
            "raw_data": view.value,
            "source": view.source,
            "confidence": view.confidence,
            "source_type": _classify_source_type(view.source, view.confidence),
            "threshold": view.threshold_context,
            "rule_origin": view.epistemology_rule_origin,
            "evaluation": view.threshold_level,
            "score_contribution": ", ".join(view.factors),
            "rap_class": view.rap_class,
            "rap_subcategory": view.rap_subcategory,
        })
    # Group by H/A/E
    grouped = {"host": [], "agent": [], "environment": []}
    for row in sorted(rows, key=lambda r: (r["rap_class"], r["status"] != "TRIGGERED")):
        grouped.setdefault(row["rap_class"].lower(), []).append(row)
    return {"trace_rows": grouped, "trace_total": len(rows)}
```

### Anti-Patterns to Avoid
- **Monolithic template:** Do NOT put all scorecard HTML into base.html.j2. Use `{% include %}` for each structural zone, keeping files under 200 lines.
- **JavaScript-heavy interactivity:** The document must work as a static file (opened from disk, emailed). All interactive features (drill-down, collapsible) MUST use `<details>` or CSS-only patterns. The one exception is IntersectionObserver for scroll-spy (already exists, gracefully degrades).
- **Separate audience exports:** User explicitly deferred this. One document, info architecture handles audiences.
- **Breaking existing section templates:** Domain sections (company, financial, market, governance, litigation, scoring) keep their existing template structure. Add H/A/E badges and enhanced narrative, but do NOT rewrite these templates.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Radar chart | Custom SVG generator | Existing `radar_chart.py` | Already renders 10-factor and can be adapted for H/A/E 3-axis |
| Sparklines | Matplotlib sparklines | Existing `sparklines.py` (pure SVG) | Lightweight, no matplotlib overhead |
| P x S matrix | New chart component | Existing `pxs_matrix_chart.py` | Full implementation with zones, dots, labels |
| Pattern firing panel | New component | Existing `pattern_context.py` | Already builds 10-card firing panel data |
| Scroll-spy sidebar | New JS library | Existing IntersectionObserver in base.html.j2 | Already working, just needs TOC entries updated |
| Signal data extraction | Raw dict access | `_signal_consumer.py` (SignalResultView) | Typed, handles SKIPPED/unavailable gracefully |
| Print CSS | New stylesheet | Existing @media print in styles.css, sidebar.css, components.css, charts.css | Extend existing rules, don't create separate print.css |
| Collapsible sections | Custom accordion | Existing `<details>` pattern | Native HTML, works without JS, print CSS already handles it |

**Key insight:** The existing codebase has ~80% of the component infrastructure needed. The work is assembly and layout restructuring, not new technology.

## Common Pitfalls

### Pitfall 1: Scorecard Page Overflow on Print
**What goes wrong:** The scorecard CSS Grid layout fits on screen but overflows to 2 pages when printed.
**Why it happens:** Screen pixels and print points have different sizing; charts render larger in print.
**How to avoid:** Use `@media print` with explicit `max-height` on scorecard-grid, scale charts with `transform: scale(0.85)` for print. Test with `page-break-after: always` on scorecard container. Set chart SVG viewBox dimensions to fixed aspect ratios.
**Warning signs:** Scorecard content spills past first page in Playwright PDF.

### Pitfall 2: Heatmap Colors Lost in PDF
**What goes wrong:** CSS background colors don't render in Playwright PDF without explicit color-adjust.
**Why it happens:** Browsers strip background colors in print by default.
**How to avoid:** Add `-webkit-print-color-adjust: exact; print-color-adjust: exact;` to all heatmap cells, badge backgrounds, and CRF banner. Already pattern in existing codebase (peer_percentiles.html.j2 line 53).
**Warning signs:** Heatmap appears as all-white grid in PDF.

### Pitfall 3: Signal Drill-Down Panels Break PDF Layout
**What goes wrong:** All `<details>` elements expand in PDF mode (existing behavior), creating enormous pages.
**Why it happens:** pdf_mode JavaScript expands all details. Signal drill-downs (potentially 500+) would each expand.
**How to avoid:** Add a CSS class like `signal-drilldown` to drill-down panels and exclude them from pdf_mode expansion: `document.querySelectorAll('details:not(.signal-drilldown)').forEach(...)`. In print CSS, hide signal-drilldown entirely: `details.signal-drilldown { display: none; }`. The epistemological trace appendix serves as the print equivalent.
**Warning signs:** PDF grows to 300+ pages because every signal drill-down is expanded.

### Pitfall 4: Sidebar TOC Desync After Restructure
**What goes wrong:** Sidebar links point to old section IDs that no longer exist or new sections are missing from sidebar.
**Why it happens:** Sidebar TOC in base.html.j2 has hardcoded `<li>` elements with `href="#identity"` etc.
**How to avoid:** After restructuring, update ALL sidebar TOC entries to match new section IDs. Consider generating TOC from template context (list of sections with id + label) rather than hardcoding.
**Warning signs:** Clicking sidebar link scrolls to wrong section or nowhere.

### Pitfall 5: html_renderer.py Exceeds 500 Lines After Changes
**What goes wrong:** Adding scorecard, heatmap, CRF, decision record, and trace context builders to `build_html_context()` pushes it over 500 lines (currently 697).
**Why it happens:** All context assembly happens in one function.
**How to avoid:** html_renderer.py is already at 697 lines -- it needs to be split as part of this phase. Extract context assembly into a separate `html_context_assembly.py` module. `html_renderer.py` keeps only `render_html_pdf()` and `_render_html_template()`.
**Warning signs:** html_renderer.py crosses 800+ lines.

### Pitfall 6: Visual Regression Tests Fail After Restructure
**What goes wrong:** Every golden baseline becomes invalid because section IDs and layout changed.
**Why it happens:** Visual regression compares per-section screenshots by ID.
**How to avoid:** Plan golden baseline regeneration as an explicit step. Update SECTION_IDS list in test_visual_regression.py to include new sections (scorecard, crf-banner, decision-record, epistemological-trace). Remove old section IDs that were reorganized. Run `--update-golden` after restructure is complete.
**Warning signs:** All 13 visual regression tests fail on first run.

## Code Examples

### Example 1: Scorecard Context Builder
```python
# context_builders/scorecard_context.py
def build_scorecard_context(state: AnalysisState) -> dict[str, Any]:
    """Assemble dense scorecard data for Page 1."""
    sc = state.scoring
    if sc is None:
        return {"scorecard_available": False}

    # Top concern signals (TRIGGERED, sorted by severity)
    top_concerns = []
    if state.analysis and state.analysis.signal_results:
        for sig_id, res in state.analysis.signal_results.items():
            if res.get("status") == "TRIGGERED":
                top_concerns.append({
                    "id": sig_id,
                    "evidence": res.get("evidence", ""),
                    "level": res.get("threshold_level", ""),
                })
        top_concerns = sorted(top_concerns, key=lambda x: x["level"], reverse=True)[:8]

    # Key financial metrics strip
    metrics_strip = _build_metrics_strip(state)

    return {
        "scorecard_available": True,
        "tier": sc.tier_label,
        "quality_score": sc.quality_score,
        "composite_score": sc.composite_score,
        "factors_summary": [
            {"name": f.factor_name, "pct": round(f.points_deducted / f.max_points * 100)}
            for f in sc.factor_scores
        ],
        "top_concerns": top_concerns,
        "metrics_strip": metrics_strip,
    }
```

### Example 2: CRF Alert Bar Context
```python
# context_builders/crf_bar_context.py
def build_crf_bar_context(state: AnalysisState) -> dict[str, Any]:
    """Build persistent CRF alert banner data."""
    if state.scoring is None:
        return {"crf_alerts": [], "crf_count": 0}

    alerts = []
    # CRF vetoes from H/A/E scoring
    hae = getattr(state.scoring, "hae_result", None)
    if hae:
        for veto in getattr(hae, "crf_vetoes", []) or []:
            alerts.append({
                "id": str(veto),
                "severity": "CRITICAL",
                "section_link": _crf_to_section(str(veto)),
            })

    # Red flags from factor scoring
    for rf in state.scoring.red_flags:
        alerts.append({
            "id": rf.flag_id,
            "description": rf.description,
            "severity": "HIGH",
            "section_link": _flag_to_section(rf.flag_id),
        })

    return {"crf_alerts": alerts, "crf_count": len(alerts)}
```

### Example 3: Updated Sidebar TOC (Dynamic)
```html
{# Generate sidebar TOC from context instead of hardcoding #}
<nav class="sidebar-toc" id="sidebar-toc">
  <div class="sidebar-title">Report</div>
  <ul>
    <li class="sidebar-group-header">Overview</li>
    <li><a href="#scorecard">Risk Scorecard</a></li>
    <li><a href="#executive-brief">Executive Brief</a></li>
    {% if crf_count > 0 %}
    <li><a href="#crf-banner" class="sidebar-alert">CRF Alerts ({{ crf_count }})</a></li>
    {% endif %}
    <li class="sidebar-group-header">Analysis</li>
    <li><a href="#company">Company</a></li>
    <li><a href="#financial-health">Financial</a></li>
    <li><a href="#market">Market</a></li>
    <li><a href="#governance">Governance</a></li>
    <li><a href="#litigation">Litigation</a></li>
    <li><a href="#scoring">Scoring</a></li>
    <li class="sidebar-group-header">Appendix</li>
    <li class="sidebar-sub"><a href="#decision-record">Decision Record</a></li>
    <li class="sidebar-sub"><a href="#epistemological-trace">Signal Trace</a></li>
    <li class="sidebar-sub"><a href="#meeting-prep">Meeting Prep</a></li>
    <li class="sidebar-sub"><a href="#sources">Sources</a></li>
  </ul>
</nav>
```

## Design Recommendations (Claude's Discretion)

### Scorecard Page Visual Design
Inspired by Moody's Credit Opinion front page and S&P CIQ company overview:

**Layout:** 2-column CSS Grid. Left column (60%): company identity bar (logo, name, ticker, sector, market cap) at top, then 10-factor scores as compact horizontal bar chart (like CIQ factor scores). Right column (40%): tier badge (large, centered), H/A/E radar chart below, key metrics strip below that.

Below the two columns: full-width signal heatmap (compact, ~30px cells) and top concerns list (5-8 items).

**Typography:** Georgia 14pt for company name, Calibri 9pt for metrics. Tabular-nums for all numbers. Navy (#0B1D3A) headers, gold (#D4A843) accents on tier badge border.

**Color Palette for Heatmap/Alerts:**
| Status | Color | Hex | Usage |
|--------|-------|-----|-------|
| TRIGGERED | Red | #B91C1C | Heatmap cells, CRF badges |
| ELEVATED | Amber | #D97706 | Heatmap cells, warning badges |
| CLEAR | Blue-gray | #64748B | Heatmap cells (muted, not green) |
| SKIPPED | Light gray | #E5E7EB | Heatmap cells (data gap) |
| DEFERRED | Amber outline | #D97706 border | Heatmap cells (planned) |

Rationale: No green in underwriting (existing design principle from design_system.py). Blue-gray for "clear" signals -- underwriting views absence of risk as neutral, not positive.

### H/A/E Dimension Badges
Small pill badges in section headers. Single letter (H/A/E) with dimension color:
- **H** (Host/Structural): Blue (#1D4ED8) -- what the company IS
- **A** (Agent/Behavioral): Red (#B91C1C) -- what HAPPENED
- **E** (Environment/External): Green (#059669) -- what's AROUND it

Each section gets 1-2 badges. Example: "Financial Health [H]", "Litigation [A] [E]", "Governance [H] [A]".

### Confidence Badge Design
Inline micro-badges next to LLM-generated content:
- **HIGH** (audited/official): Solid navy background, white text
- **MEDIUM** (unaudited/estimates): Navy outline, navy text
- **LOW** (derived/web): Dashed amber outline, amber text

### CRF Alert Bar Design
Persistent banner below scorecard page, styled like Bloomberg terminal alert strip:
- Full-width bar, dark background (#0B1D3A navy)
- Gold left border (4px solid #D4A843)
- Each CRF listed as pill with severity icon + short description
- Each pill is a link to the relevant section (e.g., CRF-RESTATEMENT links to #financial-health)
- In print: renders as a boxed section with border, no sticky behavior

### PDF Page Layout Optimization
- **Scorecard:** `break-after: page` -- always its own page
- **Executive Brief:** `break-after: page` -- standalone page
- **CRF Banner:** Rendered inline at top of Page 3 (no separate page)
- **Domain sections:** Each gets `break-before: page` (existing pattern)
- **Decision Record:** `break-before: page`
- **Epistemological Trace:** `break-before: page`, table with `thead` repeated via CSS `display: table-header-group`
- **Running header:** Existing pattern in styles.css (CONFIDENTIAL + date)
- **Running footer:** Existing pattern (Angry Dolphin branding)
- **Collapsible sections in print:** Existing behavior: `<details>` content forced open, `<summary>` hidden
- **Signal drill-downs in print:** Hidden entirely (appendix serves this purpose)

### Signal Drill-Down Panel Design
Compact inline expansion using `<details>` pattern:
- Trigger: signal ID shown as monospace code-style link
- Expanded panel: gray background (#F8FAFC), 1px left border in dimension color
- Compact 2-column key-value layout for provenance data
- Close button not needed (`<details>` handles toggle natively)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded sidebar TOC | Dynamic from section list | Phase 114 | Sidebar stays in sync with actual sections |
| Section-sequential layout | Scorecard-first layout | Phase 114 | Key decisions visible on page 1 |
| Coverage appendix only | Full epistemological trace | Phase 114 | Provenance for every signal, not just counts |
| No audience differentiation | Brief stands alone | Phase 114 | Secondary readers get value without reading 100 pages |
| No decision record | Official decision page | Phase 114 | Worksheet becomes the underwriting record |

**Existing patterns preserved:**
- Collapsible `<details>` sections with chevrons
- IntersectionObserver scroll-spy
- @media print rules for PDF
- SVG chart generation (server-side)
- Context builder -> Jinja2 template pipeline
- Signal consumer typed extraction

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + Playwright (visual regression) |
| Config file | pytest.ini / pyproject.toml |
| Quick run command | `uv run pytest tests/stages/render/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WS-01 | Scorecard renders with tier, radar, heatmap, firing panel, P x S, sparklines, CRF bar | integration | `uv run pytest tests/stages/render/test_scorecard.py -x` | Wave 0 |
| WS-02 | Narrative assessment integrated per section with H/A/E badges | unit | `uv run pytest tests/stages/render/test_hae_badges.py -x` | Wave 0 |
| WS-03 | Epistemological trace has all signals with provenance columns | unit | `uv run pytest tests/stages/render/test_epistemological_trace.py -x` | Wave 0 |
| WS-04 | Golden baselines updated and passing | visual regression | `VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py -x` | Exists (update needed) |
| WS-05 | Executive brief standalone (no missing context when read alone) | unit | `uv run pytest tests/stages/render/test_executive_brief.py -x` | Wave 0 |
| WS-06 | Screen has sidebar/drilldown; print hides sidebar/drilldown, expands content | unit | `uv run pytest tests/stages/render/test_print_divergence.py -x` | Wave 0 |
| WS-07 | Decision record renders with posture fields and tier distribution | unit | `uv run pytest tests/stages/render/test_decision_record.py -x` | Wave 0 |
| WS-08 | Sidebar TOC has audience groups; CRF links to sections | unit | `uv run pytest tests/stages/render/test_reading_paths.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green + visual regression green before /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/stages/render/test_scorecard.py` -- covers WS-01
- [ ] `tests/stages/render/test_hae_badges.py` -- covers WS-02
- [ ] `tests/stages/render/test_epistemological_trace.py` -- covers WS-03
- [ ] `tests/stages/render/test_executive_brief.py` -- covers WS-05
- [ ] `tests/stages/render/test_print_divergence.py` -- covers WS-06
- [ ] `tests/stages/render/test_decision_record.py` -- covers WS-07
- [ ] `tests/stages/render/test_reading_paths.py` -- covers WS-08
- [ ] Update `SECTION_IDS` in `tests/test_visual_regression.py` for new sections

## Open Questions

1. **H/A/E Section Mapping**
   - What we know: Each section clearly maps to 1-2 H/A/E dimensions (Financial=Host, Litigation=Agent+Environment, etc.)
   - What's unclear: Exact mapping for edge cases (AI Risk section -- Host or Environment?)
   - Recommendation: Define mapping in a small YAML/dict config, not hardcoded per template. Planner should specify the mapping table.

2. **Tier Distribution Statistics for Decision Record**
   - What we know: Decision record should show "60% bound, 25% referred, 15% declined at this tier" as soft guidance.
   - What's unclear: Where does this data come from? No actual portfolio data exists.
   - Recommendation: Hardcode industry-standard D&O tier distributions from SCAC/Cornerstone data as static reference. Flag as "Industry Reference" not "Your Portfolio". Can be made dynamic when Supabase portfolio tracking is implemented (deferred).

3. **html_renderer.py Split Strategy**
   - What we know: Currently 697 lines, will grow. Anti-Context-Rot rule says 500 max.
   - What's unclear: Best split boundary.
   - Recommendation: Extract `build_html_context()` and all helper functions into `html_context_assembly.py` (~400 lines). Leave `render_html_pdf()` and `_render_html_template()` in html_renderer.py (~300 lines).

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/do_uw/stages/render/` -- 142 templates, 40+ Python modules, established patterns
- `src/do_uw/templates/html/base.html.j2` -- current layout structure (212 lines)
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- SignalResultView with epistemology fields
- `src/do_uw/stages/render/context_builders/hae_context.py` -- H/A/E radar data (52 lines)
- `src/do_uw/stages/render/charts/sparklines.py` -- pure SVG sparkline pattern
- `src/do_uw/stages/render/design_system.py` -- color palette, typography, brand constants
- `src/do_uw/templates/html/styles.css` (573 lines) -- existing @media print rules
- `src/do_uw/templates/html/sidebar.css` (139 lines) -- sidebar layout + print hiding

### Secondary (MEDIUM confidence)
- [CSS-Tricks: Sticky TOC with Scrolling Active States](https://css-tricks.com/sticky-table-of-contents-with-scrolling-active-states/) -- IntersectionObserver pattern (already implemented)
- [CSS-Tricks: How to Make Charts with SVG](https://css-tricks.com/how-to-make-charts-with-svg/) -- Pure SVG chart patterns
- [CSS print best practices](https://618media.com/en/blog/designing-for-print-with-css-tips/) -- Print CSS patterns for financial reports
- [Codelibrary: Heatmaps with CSS Grid](https://codelibrary.opendatasoft.com/widget-tricks/heatmaps-custom/) -- CSS Grid heatmap pattern

### Tertiary (LOW confidence)
- Moody's Credit Opinion structure (inferred from public PDF headers, not full template access)
- S&P CIQ layout density (from project memory references, not direct template access)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- extending existing patterns (context builders, Jinja2 templates, CSS)
- Pitfalls: HIGH -- identified from direct codebase analysis (697-line file, 142 templates, print CSS patterns)
- Design recommendations: MEDIUM -- based on general financial report conventions + existing design system, not direct CIQ/Bloomberg template access

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable -- no external dependency changes expected)
