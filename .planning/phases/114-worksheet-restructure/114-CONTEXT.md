# Phase 114: Worksheet Restructure + Epistemological Trace - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the HTML worksheet into a polished, self-contained recommendation report with three structural layers: risk scorecard + executive brief, domain sections with integrated narrative assessment, and epistemological trace appendix. Multi-audience support via information architecture (not separate exports). Screen/print divergence. Decision documentation as a separate page. Updated golden baselines.

**Critical framing:** The worksheet is the DELIVERABLE — a fully finished document that gets attached to emails, filed as the official record. It is NOT a web app or dashboard. Think CIQ/S&P research report quality, not SaaS UI. 100+ pages is fine. Completeness and polish are non-negotiable.

</domain>

<decisions>
## Implementation Decisions

### Report Structure
- Page 1: **Risk Scorecard** — tier badge, H/A/E radar chart, 10-factor scores table, top concern signals, key financial metrics strip. Dense, visual, single-page
- Page 2: **Executive Brief** — structured narrative summary covering company profile, key risks, notable findings. Standalone for secondary readers
- Pages 3+: **Domain sections** (Company, Financials, Market, Governance, Litigation, Scoring, Analysis) — current section order preserved
- H/A/E threading: each section annotated with which H/A/E dimension it contributes to; H/A/E radar on page 1 links to relevant sections
- Narrative assessment is INTEGRATED per section (not a standalone chapter) — each section has evaluative narrative paragraphs alongside data/charts
- Appendix: **Epistemological Trace** — full signal provenance table

### Navigation & Interactivity (Screen HTML)
- Sticky TOC sidebar — persistent left sidebar with section links, highlights current section on scroll, collapses on narrow screens
- Collapsible sections with chevrons (existing pattern, keep)
- Signal drill-down: in-page expansion (click signal reference → inline detail panel showing raw data, source, threshold, evaluation)
- CRF alert bar: persistent banner at report top (below scorecard) listing all critical risk factors with severity

### Charts & Visualization
- Hybrid rendering: SVG for screen HTML, PNG for email/PDF export
- Signal heatmap: color-coded grid grouped by H/A/E dimension and signal category (green/yellow/red/gray cells, each cell = one signal, hover/click for details)
- P×S matrix: individual signal dots on scatter plot, colored by H/A/E dimension. Hover for signal details
- Sparklines: grouped trends panel in risk overview PLUS inline sparklines next to key metrics throughout sections
- Existing chart components: radar_chart.py, sparklines.py, pxs_matrix_chart.py available for reuse

### Narrative Content
- LLM-generated content shows confidence badges (HIGH/MEDIUM/LOW) based on underlying source data quality (audited/unaudited/estimated)
- One report for all audiences — no separate export profiles. Executive summary designed to stand alone but everyone gets the full document

### Epistemological Trace Appendix
- Purpose: compliance audit trail + trust calibration (dual use)
- Scope: ALL signals — triggered, clean, AND skipped. Full transparency. Clean signals prove "we looked and found no issue." Skipped signals show data gaps
- Organization: grouped by H/A/E dimension (Host, Agent, Environment), sorted by severity/contribution within each group
- Columns: Signal ID | Status | Raw Data | Source (filing+date+page) | Threshold Applied | Confidence Level | Source Type (audited/unaudited/web/derived) | Evaluation Result | Score Contribution

### Decision Documentation
- Separate Decision Record page at end of report (not embedded in analysis sections)
- Captures: posture (bind/decline/refer/terms) + free-text rationale
- Soft guidance: shows comparable account tier distribution ("60% bound, 25% referred, 15% declined at this tier") — informative, not prescriptive
- No system recommendation — avoids anchoring bias, UW forms own view from evidence

### Claude's Discretion
- **Research and propose best presentation patterns** from CIQ, Bloomberg, Moody's, S&P research reports. Challenge the current design. Bring ideas for making this the most polished, informative financial document possible. Don't just execute — be creative and ambitious
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

</decisions>

<specifics>
## Specific Ideas

- "The most amazing, fully produced worksheet document" — user explicitly prioritizes report quality over interactive dashboard features
- "I don't care if it's 100 pages, but I care more about [the report] right now" — completeness > conciseness
- "Like a full recommendation report" — self-contained, attachable to email, official record
- CIQ/Bloomberg/S&P visual density as the quality bar (established in Phase 59 VIS requirements and project memory)
- "Challenge yourself to be better at this" — user wants the research phase to autonomously explore world-class financial report design patterns and bring real proposals, not just implement what was discussed

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `radar_chart.py`, `sparklines.py`, `pxs_matrix_chart.py` — existing chart generators (SVG output)
- `design_system.py` — centralized design tokens and style definitions
- `section_renderer.py` — section rendering infrastructure
- `facet_renderer.py` — facet-based rendering
- `chart_registry.py`, `chart_style_registry.py` — chart type registration
- `_signal_consumer.py`, `_signal_fallback.py` — typed signal result extraction (Phase 104/113)
- `hae_context.py` — H/A/E radar chart context builder (Phase 113)
- `html_footnotes.py` — footnote rendering system

### Established Patterns
- Context builders provide typed dicts consumed by Jinja2 templates (Phase 113 pattern)
- Signal-backed evaluative content in `*_evaluative.py` companion modules
- Collapsible sections with chevrons already implemented
- Section files organized as `sect{N}_{name}.py` (12+ section renderers)
- `md_renderer.py` (411 lines) builds template context, `html_renderer.py` (697 lines) renders HTML

### Integration Points
- `html_renderer.py::build_html_context()` — main entry point for HTML context assembly
- `md_renderer.py::build_template_context()` — shared context builder (HTML delegates to this)
- Template system: Jinja2 templates (need to locate/create — no `.html` templates found in render dir)
- `output_manifest.yaml` — defines section ordering and grouping
- Golden baselines in `tests/test_visual_regression.py`

</code_context>

<deferred>
## Deferred Ideas

- Supabase as centralized data store for run history and feedback (infrastructure milestone)
- Multiple export profiles per audience (premature — one great report first)
- Interactive form fields for decision capture (future enhancement)
- System recommendation engine with ML-based posture suggestion (future milestone)

</deferred>

---

*Phase: 114-worksheet-restructure*
*Context gathered: 2026-03-17*
