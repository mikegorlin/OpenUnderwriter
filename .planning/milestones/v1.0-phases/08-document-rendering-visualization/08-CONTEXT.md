# Phase 8: Document Rendering & Visualization - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the complete AnalysisState (Sections 1-7) into polished output documents: Word (.docx) as primary, PDF and Markdown as secondary. Includes embedded charts/visualizations and a meeting prep companion appendix. The document should guide the underwriter's thought process — from understanding the risk to supporting a clear decision. Presentation quality is a first-class goal: premium consulting deliverable, not a data dump.

</domain>

<decisions>
## Implementation Decisions

### Visual Design Language
- **Color palette:** Liberty Mutual branding — Liberty Blue (#1A1446, deep navy) as primary, Liberty Yellow (#FFD000, gold) as accent
- **Risk heat spectrum:** Dark red → orange → yellow → blue for risk levels (NOT traffic light green — nothing is "safe" in underwriting)
- **Design tone:** Bloomberg/S&P data density combined with McKinsey visual polish and modern color-coded clarity. Use space well — not wasteful white space, but not cramped
- **Typography:** Claude's Discretion — optimize for readability of dense data tables while maintaining Liberty Mutual brand feel (serif headers likely, sans-serif body/tables)
- **Logo:** Liberty Mutual logo to be included (sourced from public brand assets)

### Data Presentation Strategy
- **Tier classification:** Prominent but contextual — shown on the executive summary page alongside composite score, key findings, and inherent risk. Part of the story, not isolated as a hero badge
- **10-factor scoring:** Radar/spider chart showing the risk profile shape across all 10 factors. Visual way to spot which factors are driving the score
- **Narrative-first approach:** Lead with the risk story ("Here's why this matters"), then show supporting data tables as evidence. Story-forward, not data-forward
- **Stock performance charts (Section 4 — Market/Trading):** Two charts required per company:
  - **1-year performance chart:** Company stock vs sector ETF, both indexed to 100. Overlaid with:
    - Red triangle markers for significant single-day drops (>=8%) with magnitude + date labels
    - Shaded orange/salmon vertical bands for multi-day drops (5d >=15%) with magnitude + date range labels
    - Legend showing marker thresholds AND total counts (e.g., "1-day >=8% drop (shown: 8; total >=5%: 31)")
    - Company line: solid navy. Sector ETF line: dashed gray. Y-axis: "Indexed to 100"
  - **5-year performance chart:** Same indexed-to-100 approach, same overlay mechanics, wider time scale
  - **Reference visual:** User-provided JACK vs XLY chart — this is the target quality and information density. Dense annotations are valued: every significant drop labeled with magnitude and date
  - **Key design principles from reference:** Annotations don't clutter because they use leader lines and offset labels; shaded bands provide visual weight for multi-day events without hiding the price line; the sector comparison immediately shows company-specific vs market-wide moves

### Document Structure & Flow
- **Page one:** Full executive summary (Section 1) — key findings, thesis, scoring snapshot, tier recommendation in context
- **Section ordering:** Standard worksheet order (Sections 2-7): Company Profile → Financial Health → Market/Trading → Governance/Leadership → Litigation/Regulatory → Scoring/Risk Synthesis
- **Navigation:** Table of contents with clickable links, continuous section flow (no forced page breaks between sections). Compact, readable
- **Decision section:** None — the worksheet informs the decision but approval happens in a separate process/system. This is the analytical foundation, not the approval form

### Meeting Prep Companion
- **Format:** Appendix to the main Word document (not a separate file). Clearly separated from the analysis sections
- **Question ordering:** Priority-ranked single list — most important questions first regardless of category. Category (CLARIFICATION, FORWARD_INDICATOR, GAP_FILLER, CREDIBILITY_TEST) shown as tags on each question
- **Question depth:** Each question includes: (1) the question to ask, (2) context on why it matters for D&O, (3) what a good/bad answer looks like
- **Red flag response guide:** Yes — if an answer is concerning, include follow-up questions, what to document, and escalation triggers

### Claude's Discretion
- Exact font choices (serif vs sans-serif balance for readability)

- Page layout details (margins, column widths, spacing)
- Chart rendering library choices (matplotlib vs alternatives)
- PDF rendering approach
- Loading/generation progress feedback
- Exact number of meeting prep questions to include

</decisions>

<specifics>
## Specific Ideas

- "We will likely have to do a lot of tweaking the final product" — expect an iterative design refinement cycle in Phase 8-05
- "Spectacular" means: easily understood thought process, very clear understanding of the risk, very clear way to demonstrate the decision-making process
- The document should read like a premium consulting deliverable — the kind of report you'd present to a C-suite or underwriting committee
- Liberty Mutual brand identity: fonts similar to Perpetua (serif), navy/gold palette, professional insurance industry feel
- Radar chart for 10-factor scoring is a specific visual request — not a bar chart or table
- **Stock chart reference (JACK vs XLY):** User provided a specific 1-year chart showing Jack in the Box vs Consumer Discretionary (XLY) indexed to 100. Key elements to replicate: solid navy company line, dashed gray sector line, red downward-triangle markers with red magnitude/date labels, orange shaded vertical bands for multi-day events with orange labels and leader lines, clean legend in top-right with threshold counts. This chart communicates "the stock dropped 50% while the sector gained 5%" instantly — that's the goal

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-document-rendering-visualization*
*Context gathered: 2026-02-08*
