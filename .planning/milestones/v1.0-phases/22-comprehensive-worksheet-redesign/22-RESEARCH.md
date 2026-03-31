# Phase 22: Comprehensive Worksheet Redesign - Research

**Researched:** 2026-02-11
**Domain:** Document rendering, narrative generation, professional report design, multi-format output
**Confidence:** HIGH (all technology is in-codebase; this is a redesign of existing architecture, not new technology)

## Summary

Phase 22 is a ground-up redesign of the RENDER stage that transforms the worksheet from a v1 "graceful degradation" design (built for sparse regex data) into a production-quality document designed for complete LLM-extracted data. The current system has 30 rendering files totaling ~7,100 lines across Word (8 section renderers + meeting prep + helpers), Markdown (Jinja2 template + helpers), PDF (WeasyPrint HTML/CSS), and dashboard (FastAPI + htmx + Plotly).

The primary technical challenge is NOT the rendering technology (python-docx, Jinja2, and WeasyPrint are well-understood and already in use) -- it is the data-to-presentation mapping. The v1 renderers read AnalysisState fields with `if field is not None` / `N/A` fallback patterns. The v2 renderers must assume data IS present and build rich presentations: multi-column comparison tables, LLM-quality narratives citing specific filing passages, conditional formatting that highlights what matters, and source traceability linking every claim to a specific filing section.

**Primary recommendation:** Rebuild each section renderer from scratch (not patch), starting with the highest-impact sections (Executive Summary, Financial, Litigation). Use LLM-generated narratives from the EXTRACT stage (already in state.json) as the narrative backbone, supplemented by rule-based interpretive text in md_narrative.py. Keep the existing rendering architecture (importlib dispatch, section renderer pattern, DesignSystem, docx_helpers) but rewrite the content logic within each renderer.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | 1.2.0 | Word document generation | Already in use, only viable Python option for .docx |
| Jinja2 | 3.x | Markdown and PDF template rendering | Already in use, standard Python templating |
| WeasyPrint | 62.x | HTML-to-PDF conversion | Already in use, optional dependency |
| matplotlib | 3.9.x | Static chart generation for Word/PDF | Already in use for radar, stock, timeline, ownership charts |
| Plotly.js | CDN | Interactive dashboard charts | Already in use via CDN (no build step) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| docx OxmlElement | built-in | Low-level XML manipulation for cells, borders, shading | Custom formatting beyond python-docx's API surface |
| io.BytesIO | stdlib | Chart image pipeline (matplotlib -> BytesIO -> docx picture) | Embedding all charts in Word documents |
| base64 | stdlib | Chart embedding in PDF HTML templates | PDF chart rendering |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-docx | python-docx-template (docxtpl) | Template-based approach using Word templates as base; would require creating .docx template files; higher design flexibility but more complexity. Not worth switching. |
| matplotlib (static) | Plotly (static export) | Could use plotly.io.write_image for static chart export; requires kaleido dependency; charts would look identical across Word/dashboard. Not needed -- matplotlib charts are adequate for static docs. |
| WeasyPrint | Playwright PDF | Could use the existing Playwright MCP for PDF generation from HTML; slower, more complex. WeasyPrint is simpler. |

**Installation:** No new dependencies needed. Everything is already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/stages/render/
  __init__.py              # RenderStage orchestrator (existing)
  word_renderer.py         # Word assembly orchestrator (existing, modify)
  md_renderer.py           # Markdown renderer (existing, modify)
  pdf_renderer.py          # PDF renderer (existing, modify)
  design_system.py         # Visual constants (existing, enhance)
  docx_helpers.py          # Word XML helpers (existing, enhance)
  formatters.py            # Number/citation formatters (existing, enhance)
  chart_helpers.py         # Chart creation utilities (existing)
  md_narrative.py          # Interpretive narrative generator (existing, REWRITE)
  md_renderer_helpers.py   # Markdown template context (existing, REWRITE)
  md_renderer_helpers_ext.py  # Extended helpers (existing, REWRITE)
  sections/
    sect1_executive.py     # REWRITE: rich thesis, snapshot, tower recommendation
    sect2_company.py       # REWRITE: revenue segments, geo footprint, D&O exposure
    sect3_financial.py     # REWRITE: full financial tables, distress, debt, audit
    sect3_tables.py        # REWRITE: multi-period financial statement tables
    sect4_market.py        # REWRITE: stock drops, insider trading, earnings guidance
    sect5_governance.py    # REWRITE: board, compensation, ownership, sentiment
    sect6_litigation.py    # REWRITE: SCAs, enforcement, defense, contingencies
    sect6_timeline.py      # REWRITE: derivative suits, regulatory, SOL, patterns
    sect7_scoring.py       # REWRITE: factor detail, patterns, allegation mapping
    sect8_ai_risk.py       # REWRITE: company-specific AI scoring, peer comparison
    meeting_prep.py        # REWRITE: data-driven questions from complete extraction
    meeting_questions.py   # REWRITE: richer question generation
    meeting_questions_gap.py  # REWRITE: gap analysis from actual data
  charts/
    stock_charts.py        # Enhance: event overlay, sector comparison line
    radar_chart.py         # Enhance: labeled data points, threshold rings
    ownership_chart.py     # Enhance: named holders, insider detail
    timeline_chart.py      # Enhance: event categorization, severity coloring
  templates/
    markdown/worksheet.md.j2     # REWRITE: full markdown redesign
    pdf/worksheet.html.j2        # REWRITE: full PDF template redesign
    pdf/styles.css               # REWRITE: professional CSS styling
```

### Pattern 1: Rich Data Presentation (Replace N/A Fallback)
**What:** v1 renderers check `if field is not None` and show "N/A" or skip. v2 renderers assume data is present and build rich multi-column tables.
**When to use:** Every section renderer.
**Example:**
```python
# v1 pattern (AVOID):
rows.append(["CEO Total Comp",
    format_currency(comp.ceo_total_comp.value if comp.ceo_total_comp else None)])

# v2 pattern (USE):
def _render_compensation_table(doc: Any, comp: CompensationAnalysis, ds: DesignSystem) -> None:
    """Render detailed NEO compensation table with all components."""
    headers = ["Executive", "Salary", "Bonus", "Equity", "Other", "Total", "Pay Ratio"]
    rows: list[list[str]] = []
    # Build row per NEO from complete LLM extraction data
    for neo in comp.named_executive_officers:
        rows.append([
            neo.name, format_currency(neo.salary, compact=True),
            format_currency(neo.bonus, compact=True),
            format_currency(neo.equity_awards, compact=True),
            format_currency(neo.other_comp, compact=True),
            format_currency(neo.total_comp, compact=True),
            f"{neo.pay_ratio:.0f}:1" if neo.pay_ratio else "N/A",
        ])
    add_styled_table(doc, headers, rows, ds)
```

### Pattern 2: Source Attribution on Every Data Point
**What:** Every rendered data point links to its source filing, section, and passage.
**When to use:** All tables and narrative text.
**Example:**
```python
# Citation format: [filing_type, date, confidence]
# Already exists as format_citation(sv) -> "[SEC 10-K, 2024-12-31, HIGH]"
# v2 enhancement: add_sourced_paragraph with passage reference
def _render_sourced_finding(doc: Any, text: str, sv: SourcedValue, ds: DesignSystem) -> None:
    """Render text with inline source citation and passage reference."""
    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(text)
    run.font.name = ds.font_body
    # Citation with specific passage ref
    citation = format_citation(sv)
    cite_run: Any = para.add_run(f"  {citation}")
    cite_run.font.name = ds.font_mono
    cite_run.font.size = ds.size_small
    cite_run.font.color.rgb = ds.color_text_light
```

### Pattern 3: Interpretive Narratives (Not Template Fill)
**What:** Section narratives combine LLM-extracted data with rule-based interpretation. Not "Revenue: $X" but "Revenue declined 2.9% year-over-year to $X, driven by softening demand in the automotive segment. This margin compression, combined with elevated leverage, increases the company's vulnerability to securities litigation following earnings disappointments."
**When to use:** Every section summary paragraph.
**Example:**
```python
# In md_narrative.py, rewrite financial_narrative() to use complete data:
def financial_narrative(fin: dict[str, Any]) -> str:
    """Generate analyst-quality financial narrative from complete data."""
    parts: list[str] = []

    # Revenue trajectory with segment detail (NEW in v2)
    segments = fin.get("revenue_segments", [])
    if segments and len(segments) > 1:
        top_segment = max(segments, key=lambda s: s.get("revenue", 0))
        parts.append(
            f"Revenue concentration is notable: {top_segment['name']} "
            f"accounts for {top_segment['percentage']:.0f}% of total revenue, "
            f"creating single-segment exposure risk."
        )

    # Critical accounting estimates (NEW from LLM extraction)
    estimates = fin.get("critical_accounting_estimates", [])
    if estimates:
        parts.append(
            f"Management identifies {len(estimates)} critical accounting "
            f"estimate(s), including {', '.join(e['description'][:50] for e in estimates[:3])}. "
            f"Each represents potential restatement surface area."
        )

    return " ".join(parts)
```

### Pattern 4: Conditional Formatting for Actionable Insights
**What:** Visual formatting (cell shading, risk indicators, bold) applied based on data values to guide the underwriter's eye to what matters.
**When to use:** All data tables with numeric/risk values.
**Example:**
```python
# Existing pattern (keep): set_cell_shading(cell, color_hex)
# v2 enhancement: apply_risk_cell_shading helper
def _apply_risk_cell_shading(cell: Any, value: float, thresholds: dict[str, float]) -> None:
    """Apply background shading based on risk thresholds."""
    if value >= thresholds.get("critical", float("inf")):
        set_cell_shading(cell, "FCE8E6")  # Light red
    elif value >= thresholds.get("elevated", float("inf")):
        set_cell_shading(cell, "FFF3CD")  # Light amber
    elif value >= thresholds.get("moderate", float("inf")):
        set_cell_shading(cell, "DCEEF8")  # Light blue
```

### Pattern 5: File Size Compliance (500-Line Rule)
**What:** Every file must stay under 500 lines. Complex sections split into logical sub-files.
**When to use:** Any section renderer approaching 400 lines.
**Example:** `sect3_financial.py` + `sect3_tables.py` (existing split). New splits will follow the same pattern: `sect5_governance.py` + `sect5_governance_comp.py`, `sect6_litigation.py` + `sect6_litigation_defense.py`.

### Anti-Patterns to Avoid
- **"N/A" as primary design:** v1 renderers treat missing data as normal. v2 renderers should NOT have `N/A` as a first-class presentation element. If data is truly missing (rare with LLM extraction), display a specific explanation: "Auditor opinion not disclosed in most recent 10-K (unusual -- verify)" instead of "N/A".
- **Template-only narrative:** The Markdown narrative (`md_narrative.py`) currently uses string-parsing of summary dicts. Rewrite to use actual typed data from state, not re-parsed summary strings.
- **Duplicate data extraction:** The Markdown renderer has `md_renderer_helpers.py` (390 lines) + `md_renderer_helpers_ext.py` (284 lines) that re-extract data from state into flat dicts. This is a parallel extraction path that diverges from Word renderer. Unify into shared context builders.
- **Generic D&O context:** Current D&O context paragraphs are boilerplate ("D&O Context: CEO/Chair duality reduces board independence..."). v2 should cite company-specific facts.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cell shading | Custom XML builder | Existing `set_cell_shading()` in docx_helpers.py | Already handles OxmlElement creation correctly |
| Table creation | Raw XML tables | Existing `add_styled_table()` / `add_data_table()` | Already handles header styling, alternating rows |
| Chart embedding | Direct image insertion | Existing `embed_chart()` / `save_chart_to_bytes()` pipeline | Handles BytesIO lifecycle, figure cleanup |
| Risk level coloring | Hardcoded RGB values | Existing `get_risk_color()` + `_RISK_COLORS` mapping | Centralized color definitions |
| Number formatting | f-strings with %.2f | Existing `format_currency()` / `format_percentage()` / `format_compact()` | Handles None, negatives, compact notation |
| Source citations | Manual string building | Existing `format_citation(sv)` -> `"[SEC 10-K, 2024-12-31, HIGH]"` | Consistent format across all renderers |
| Page numbers | Manual field code | Existing `add_page_number()` | Handles complex fldChar XML |
| TOC | Manual field code | Existing `add_toc_field()` | Handles TOC instruction text |
| Section dividers | Custom border code | Existing `add_section_divider()` | Gold accent line per brand |

**Key insight:** The rendering infrastructure (docx_helpers, formatters, chart_helpers, design_system) is solid and well-tested. The problem is in the section renderers and template context builders, not the utility layer.

## Common Pitfalls

### Pitfall 1: Rewriting Utility Layer When Section Logic Is the Problem
**What goes wrong:** Developer rewrites docx_helpers.py or design_system.py thinking the visual problems are there.
**Why it happens:** The output looks sparse, so it seems like a styling problem. But the styling is fine -- the problem is that section renderers aren't accessing rich data.
**How to avoid:** Audit data flow first. Print what data exists in state.json for a real ticker (TSLA has 28 LLM extractions, 8 SCAs, 9 directors, 5 key findings). Then design the presentation for that data.
**Warning signs:** Modifying docx_helpers.py or design_system.py before any section renderer changes.

### Pitfall 2: Breaking Existing Tests Before Rewriting
**What goes wrong:** Existing 2,526 tests depend on current renderer interfaces. Rewriting renderers without maintaining function signatures breaks everything.
**Why it happens:** Temptation to start fresh and change interfaces.
**How to avoid:** Keep `render_section_N(doc, state, ds) -> None` signature for all Word section renderers. Keep `build_template_context(state, chart_dir) -> dict` signature for Markdown/PDF. Internal refactoring is free; interface changes require test updates.
**Warning signs:** Import errors in test files after renderer changes.

### Pitfall 3: Exceeding 500-Line Limit During Section Rewrites
**What goes wrong:** Rich presentation logic for a section pushes a file past 500 lines.
**Why it happens:** Complete data requires more rendering code. Current sect5_governance.py is 420 lines with SPARSE data. Rich data will need more.
**How to avoid:** Plan file splits proactively. Each section should have a primary renderer + helper file. E.g., sect5_governance.py (main entry, board, ownership) + sect5_governance_comp.py (compensation, sentiment, coherence).
**Warning signs:** Any file approaching 400 lines during development.

### Pitfall 4: Markdown/PDF Diverging from Word Content
**What goes wrong:** Word renderer gets rich content updates but Markdown template and PDF template lag behind, producing sparse output.
**Why it happens:** The three formats use different code paths. Word uses section renderers. Markdown uses Jinja2 template + md_renderer_helpers.py. PDF reuses Markdown context.
**How to avoid:** After each section redesign, immediately update the Markdown template and helpers. Test all three formats.
**Warning signs:** Current state: TSLA Markdown output shows "data not available" for Sections 3-8 while the Word doc has content. This is the existing bug that v2 must fix.

### Pitfall 5: LLM Narrative in RENDER Stage Violates MCP Boundary
**What goes wrong:** Developer adds Claude API calls in the RENDER stage to generate better narratives.
**Why it happens:** The success criteria says "narratives that read like an analyst wrote them" and the temptation is to call Claude at render time.
**How to avoid:** CLAUDE.md is explicit: "MCP tools are used ONLY in ACQUIRE stage" and "EXTRACT and later stages operate on local data only." All narrative quality must come from: (1) LLM extractions already in state.json (from EXTRACT), (2) rule-based interpretive text in md_narrative.py, (3) existing narrative fields on state models (thesis, summaries). No API calls in RENDER.
**Warning signs:** Any `import anthropic` or `import instructor` in stages/render/.

### Pitfall 6: Ignoring the Dashboard Format
**What goes wrong:** Word and Markdown get redesigned but the dashboard (FastAPI + htmx) still shows v1 sparse data.
**Why it happens:** Dashboard is in a separate `dashboard/` directory with its own `state_api.py` that extracts data differently.
**How to avoid:** Phase 22 scope explicitly includes "All formats updated: Word (primary), PDF, Markdown, and dashboard." Dashboard state_api.py reads from the same AnalysisState and needs its own update pass.
**Warning signs:** Dashboard showing "N/A" or empty sections after Word/Markdown redesign.

### Pitfall 7: Not Handling the Markdown/PDF Disconnect
**What goes wrong:** The Markdown renderer's template context builders (`md_renderer_helpers.py` + `md_renderer_helpers_ext.py`) are a parallel data extraction path from state, separate from Word renderers. They extract data into flat dicts that lose structure.
**Why it happens:** Originally designed for simplicity with sparse data. Rich data requires structured context.
**How to avoid:** Redesign template context to pass richer data structures to Jinja2 templates. The Markdown template should iterate over actual typed data, not flattened strings.
**Warning signs:** Having to duplicate business logic between Word renderers and md_renderer_helpers.

## Code Examples

Verified patterns from the existing codebase:

### Creating a Rich Comparison Table (Word)
```python
# Source: existing docx_helpers.py + sect3_tables.py pattern
def _render_comparison_table(
    doc: Any,
    headers: list[str],
    rows: list[list[str]],
    ds: DesignSystem,
    highlight_cols: dict[int, dict[str, str]],  # col_idx -> {value_pattern: color_hex}
) -> None:
    """Create table with per-cell conditional shading."""
    table = add_styled_table(doc, headers, rows, ds)

    # Apply conditional shading on data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, highlights in highlight_cols.items():
            if col_idx < len(row_data):
                cell_text = row_data[col_idx]
                for pattern, color in highlights.items():
                    if pattern in cell_text:
                        cell = table.rows[row_idx + 1].cells[col_idx]
                        set_cell_shading(cell, color)
```

### Extracting Rich Template Context (Markdown)
```python
# Source: existing md_renderer.py build_template_context pattern
# Enhanced for v2 to pass structured data not flat dicts
def extract_litigation_v2(state: AnalysisState) -> dict[str, Any]:
    """Extract rich litigation context for Markdown templates."""
    lit = state.extracted.litigation if state.extracted else None
    if lit is None:
        return {"has_data": False}

    # Pass actual case objects, not flattened strings
    cases = []
    for sca in lit.securities_class_actions:
        cases.append({
            "name": _sv_val(sca.case_name),
            "filing_date": _sv_val(sca.filing_date),
            "status": _sv_val(sca.status),
            "court": _sv_val(sca.court),
            "class_period_start": _sv_val(sca.class_period_start),
            "class_period_end": _sv_val(sca.class_period_end),
            "allegations": [_sv_val(a) for a in sca.allegations],
            "lead_counsel": _sv_val(sca.lead_counsel),
            "settlement": format_currency(
                sca.settlement_amount.value if sca.settlement_amount else None,
                compact=True,
            ),
            "source": format_citation(sca.case_name) if sca.case_name else "",
        })

    return {
        "has_data": True,
        "active_count": lit.active_matter_count.value if lit.active_matter_count else 0,
        "historical_count": lit.historical_matter_count.value if lit.historical_matter_count else 0,
        "cases": cases,
        "enforcement_stage": _get_enforcement_stage(lit.sec_enforcement),
        "narrative": str(lit.litigation_summary.value) if lit.litigation_summary else "",
    }
```

### Per-Cell Shading for Distress Zones (Already Implemented)
```python
# Source: sect3_financial.py _color_zone_cells
# This pattern is correct and should be replicated for other tables
def _zone_to_color(zone: str) -> str | None:
    zone_colors: dict[str, str] = {
        "SAFE": "DCEEF8",      # Blue (NOT green)
        "GREY": "FFF3CD",      # Amber
        "DISTRESS": "FCE8E6",  # Red
    }
    return zone_colors.get(zone)
```

### Chart Embedding Pipeline (Already Implemented)
```python
# Source: chart_helpers.py + sect5_governance.py
chart_buf = create_ownership_chart(ownership, ds)
if chart_buf is not None:
    embed_chart(doc, chart_buf)
    caption: Any = doc.add_paragraph(style="DOCaption")
    caption.add_run("Figure: Ownership breakdown")
```

## State of the Art

| Old Approach (v1) | Current Approach (v2 target) | Impact |
|-------------------|------------------------------|--------|
| Regex extraction -> sparse data -> N/A fallbacks | LLM extraction -> 28+ filings -> complete structured data | Every section has rich data to render |
| Template narratives ("Revenue: $X") | Interpretive narratives with D&O context and filing citations | Reads like an analyst wrote it |
| Generic D&O context boilerplate | Company-specific context citing actual findings | Actionable for underwriters |
| Flat dict template context | Structured typed context preserving SourcedValue chain | Source traceability maintained |
| Word-only complete rendering | Consistent rich rendering across Word/Markdown/PDF/Dashboard | All formats equally useful |

**What's NOT changing:**
- python-docx as the Word generation library (no alternatives in Python)
- Jinja2 for Markdown/PDF templates (standard, works well)
- WeasyPrint for PDF (optional, adequate)
- matplotlib for static charts (adequate for Word/PDF)
- Plotly.js for dashboard charts (CDN, no build step)
- DesignSystem frozen dataclass pattern (clean, tested)
- importlib section renderer dispatch (clean extensibility)
- Angry Dolphin branding (brand is established)
- NO green in risk spectrum (underwriting principle)

## Open Questions

Things that couldn't be fully resolved:

1. **LLM narrative quality at render time without API calls**
   - What we know: State.json already contains LLM-generated summaries (thesis narrative, governance summary, litigation summary, financial health narrative). md_narrative.py generates rule-based interpretive text.
   - What's unclear: Whether the existing narratives are sufficient quality for "reads like an experienced D&O analyst wrote them" or whether the rule-based narratives need a major quality upgrade.
   - Recommendation: Start by wiring the existing LLM narratives (from EXTRACT stage) into all renderers. Then assess quality. If insufficient, enhance md_narrative.py rule-based logic with richer interpretation -- still no API calls in RENDER.

2. **Dashboard update scope**
   - What we know: Dashboard has 6 files (~1,460 lines) with its own state_api.py. It reads from the same AnalysisState.
   - What's unclear: How much of the dashboard needs redesign vs. just wiring up existing data. The dashboard's chart endpoints and htmx partials may need significant updates.
   - Recommendation: Dashboard updates should be a separate wave in the phase plan, after Word/Markdown/PDF are complete. Dashboard state_api.py needs the same data extraction improvements as md_renderer_helpers.py.

3. **File count after 500-line splits**
   - What we know: Current render section files are 258-442 lines. Rich rendering will push many past 500.
   - What's unclear: Exactly which files will need splits and how many new files will be created.
   - Recommendation: Budget for at least 6-8 new split files. Plan splits proactively at 400 lines.

4. **Test strategy for "analyst quality" narratives**
   - What we know: Current tests verify renderers don't crash and produce non-empty output. 2,526 tests passing.
   - What's unclear: How to test that narratives "read like an experienced D&O analyst." This is inherently subjective.
   - Recommendation: Test that narratives contain specific data citations (company name, dollar amounts, filing references). Test that key risk signals are mentioned. Manual review checkpoint for final quality assessment.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All 30 render files read and analyzed
- State.json analysis: TSLA state.json (7.4MB) examined for available data structure
- Validation report: 25/26 tickers passing, 277/277 ground truth tests
- ROADMAP.md and STATE.md: Phase 22 scope and success criteria confirmed

### Secondary (MEDIUM confidence)
- [python-docx 1.2.0 documentation](https://python-docx.readthedocs.io/en/latest/) -- Current version, API reference
- [python-docx table API](https://python-docx.readthedocs.io/en/latest/api/table.html) -- Table formatting capabilities
- [python-docx style system](https://python-docx.readthedocs.io/en/latest/user/styles-using.html) -- Style creation and usage

### Tertiary (LOW confidence)
- Web search on LLM narrative generation for financial reports -- confirms rule-based + LLM approach, governance-first
- Web search on python-docx advanced formatting -- confirms cell shading via XML, merged cells supported, cross-references NOT natively supported

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- existing patterns are well-established, redesign is content not infrastructure
- Pitfalls: HIGH -- identified from actual codebase analysis (e.g., Markdown disconnection is a real observed bug)

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (stable -- no moving technology targets)
