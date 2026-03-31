# Phase 43: HTML Presentation Quality — CapIQ Layout — Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the existing HTML worksheet into a professional, institutionally-credible underwriting document that matches S&P Capital IQ-grade presentation quality. This phase covers layout architecture, information density, risk signal visualization, data traceability, and document navigation. The underlying data pipeline and data model are NOT changing — this is purely a presentation layer overhaul.

The document is a single HTML file (no page concept, no "cover page"). PDF is generated later by printing/converting the HTML — the HTML itself is the primary deliverable.

</domain>

<decisions>
## Implementation Decisions

### Layout density & structure
- **Target density:** CapIQ-grade — multi-column tables, minimal whitespace, 3-4 data points per row. Looks like a Bloomberg terminal printout.
- **Page layout:** Two-column — fixed left sidebar with section TOC, right side is dense data content.
- **Sticky top bar:** Company name, ticker, sector, market cap/size. Score does NOT go in the top bar — it lives in the body. No red flags in the top bar.
- **Data tables:** 3-column grid — Label | Value | Context/Benchmark. Every data point shows what it is, the value, and how it compares to peers or thresholds.

### Document section order
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

### Risk signal presentation
- **Red Flags section:** Priority-sorted table — Severity | Check name | Finding | Source. Worst issues first. Underwriter scans top-to-bottom to see severity.
- **Score & peril visualization:** Claude's discretion — maximize BOTH visual impact AND data granularity. No sacrificing one for the other. Likely: peril tile scorecard grid (for visual pattern recognition) + detailed breakdown table underneath (for full data).
- **Check results within sections:** Show only TRIGGERED/ELEVATED checks inline + a summary count line ("47 checks: 3 TRIGGERED, 2 ELEVATED, 42 PASSING"). Do NOT show all 47 checks.
- **Color palette:** CapIQ-style — deep red / amber / green on white background. Standard institutional severity colors.

### Data sourcing & traceability
- **Sourcing method:** Footnote numbers with a Sources appendix at end of document. Inline superscript numbers (¹ ² ³) on data points.
- **Confidence display:** Show confidence level ONLY when MEDIUM or LOW. High confidence is the default and shown silently. Reduced confidence flagged as e.g., "¹ (est.)" or "¹ (web)".
- **Missing data:** Em dash (—) with a footnote explaining why (not applicable vs. acquisition failed vs. not disclosed).
- **Sources appendix:** End of document, numbered list format: `¹ 10-K FY2024 (SEC EDGAR), filed 2024-02-23`

### Document navigation
- **Sidebar TOC:** Sticky — stays fixed as user scrolls. Active section highlighted as you scroll through the document. Click any section to jump.
- **Sections:** Always fully expanded — no toggles, no collapsing. Document-first, not app-first.

### Claude's Discretion
- Exact peril score visualization design (tile grid + table is the direction, specifics are open)
- Typography choices, exact spacing, font sizes
- Sidebar width and styling
- Exact footnote rendering implementation
- Chart/sparkline choices within sections (if any)

</decisions>

<specifics>
## Specific Ideas

- Reference product: S&P Capital IQ worksheet layout — dense, professional, institutional
- "Whatever looks great WITHOUT sacrificing any data granularity" — this is the governing design constraint for the scoring/peril section
- Red flags appear immediately after Executive Summary (not buried at end, not in top bar)
- The sticky top bar is identity-only (name, ticker, sector, size) — NOT a dashboard with scores/flags
- No "Cover page" concept — HTML has a company identity block at top, then flows straight into analysis

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 43-html-presentation-quality-capiq-layout-data-tracing*
*Context gathered: 2026-02-24*
