# Phase 35: Display & Presentation Clarity - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete separation of analysis and display. RENDER becomes a pure formatter receiving pre-computed narratives, density assessments, and display-ready data from upstream stages. The knowledge model types (MANAGEMENT_DISPLAY, EVALUATIVE_CHECK, INFERENCE_PATTERN) drive how each piece of information is presented. Additionally, the document output quality is elevated to Bloomberg/S&P professional report standards with a beautiful HTML-to-PDF pipeline alongside the editable Word doc.

</domain>

<decisions>
## Implementation Decisions

### Section Density Levels
- Three density tiers: CLEAN, ELEVATED, CRITICAL — computed per-section and per-subsection
- Section-level density sets the baseline; individual subsections can override (e.g., section is ELEVATED but one subsection is CRITICAL and gets deep-dive treatment)
- **CLEAN sections keep full depth** — same data tables, same narratives, same structure as other densities. Indicators show green/clear signals. Nothing is abbreviated or removed
- **ELEVATED sections** add amber-colored indicators where concerns exist, plus brief "why this matters for D&O" context notes alongside each concern
- **CRITICAL sections** get the full treatment: expanded forensic detail with evidence chains, additional "Deep Dive" sub-sections with cross-references to related risks in other sections, and visual urgency cues (red/amber styling, alert icons, severity badges)

### Check-Type Display Mapping
- **MANAGEMENT_DISPLAY** (pure data — board size, revenue segments, officer list): Structured data tables with headers, values, and source citations, plus a one-line contextual note per table (e.g., "Board has 9 members, 7 independent — above median for sector")
- **EVALUATIVE_CHECK** (has TRIGGERED/CLEAR/SKIPPED result): Traffic light badge (red/amber/green) plus a brief "what this means for D&O" explanation when TRIGGERED or ELEVATED. CLEAR items show green badge only
- **INFERENCE_PATTERN** (combines multiple signals into a conclusion): Written narrative explanation of the inference followed by a bulleted list of the specific data points that support it. Reads like an analyst's note
- **SKIPPED checks**: Appear in output with a grey "Not evaluated" badge and brief reason why it was skipped (e.g., "No DEF 14A filing available"). Underwriter sees what wasn't checked

### Narrative Generation
- All narratives LLM-generated (Claude), not rule-based templates — natural language, readable, professional tone
- **Executive summary thesis** is tiered: CLEAN companies get concise verdict (3-4 sentences), ELEVATED/CRITICAL companies get detailed analysis brief (6-8 sentences covering risk profile, concerns, mitigating factors, sector comparison)
- **Every section** gets a narrative paragraph — even CLEAN sections get "No material concerns identified in [area]" with supporting context
- **Meeting prep questions** are fully specific to company findings — every question tied to a specific TRIGGERED check, detected pattern, or data gap. No generic industry questions that didn't earn their place from the analysis
- Narratives pre-computed in BENCHMARK stage, stored in state — RENDER just formats them

### Gap & Coverage Visibility
- **Per-subsection gap notices**: When a subsection has no data, the subsection header still appears with a prominent "Data not available" notice and explanation of what was attempted
- **Data coverage appendix**: Full data coverage breakdown as a back-of-document appendix (% of checks evaluated, data sources available/unavailable)
- **LOW confidence flagging**: HIGH and MEDIUM confidence data renders normally. Only LOW confidence items get a visible marker (asterisk, footnote, or lighter styling)
- **Blind spot discoveries**: Unverified web search findings appear as distinct "Discovery" callout boxes with the finding, source URL, and explicit "unverified — requires confirmation" disclaimer. Visually distinct from verified data

### Visual Quality & Document Output
- **Target quality**: Bloomberg / S&P professional reports — dense information, minimal white space, clear graphics, professional polish
- **Dual output format**: Word doc for editability (basic formatting), PDF from rich HTML for the beautiful "presentation" version
- **Layout approach**: Mixed — executive summary and risk narrative sections full-width for readability; data sections (financials, governance, peer comparison) in multi-column or dashboard-style grid layouts
- **Charts and graphics**: Full analytical charts — stock price with event overlays, financial trend comparisons, peer scatter plots, risk radar charts. Larger embedded visuals with rich insight, not just sparklines
- **HTML-to-PDF toolchain**: Research the cutting edge (MCP tools, plugins, new approaches) during planning. No paid services. If the best free approach is Jinja2 + Tailwind CSS rendered via headless browser, go with that
- **Word doc**: Remains the editable version but doesn't need to match the PDF's visual quality. Functional and clean, not Bloomberg-grade

### Claude's Discretion
- Exact color palette and typography choices for the HTML/PDF report (should feel like Bloomberg/S&P)
- Specific chart library choice (matplotlib, plotly, or alternatives) for embedded visuals
- How to structure the HTML template architecture (single template vs component-based)
- Exact formatting of "Not evaluated" badges and discovery callout boxes
- How to implement multi-column layouts in the HTML report

</decisions>

<specifics>
## Specific Ideas

- "I want this to look like professional S&P / Bloomberg reports" — the gold standard for financial analysis presentation
- Dense information with little white space — every element earns its page space
- "Clear graphics and amazing visuals" — charts should be analytically meaningful, not decorative
- Explore cutting-edge free tools (MCP plugins, modern libraries) for the best possible output quality
- The PDF is the "wow" document; the Word doc is the "work with it" document

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 35-display-presentation-clarity*
*Context gathered: 2026-02-21*
