# Phase 40: Professional PDF & Visual Polish - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the existing HTML-to-PDF pipeline into a Bloomberg/S&P-quality professional document. The PDF output should look like a top-tier credit report. The HTML dashboard keeps its dark theme. The Word document is a functional format for editing, not a pixel-perfect replica of the PDF. Static CSS replaces the Tailwind CDN dependency.

</domain>

<decisions>
## Implementation Decisions

### Visual Reference & Tone
- **S&P / Moody's credit report** style: clean white background, blue/navy headers, professional typography
- **Light PDF, keep dark dashboard**: PDF gets white background with navy/gold accents; HTML dashboard stays dark navy (#0B1D3A)
- **Dense & compact** information density: maximize data per page, 9-10pt body, tight spacing, aim for 15-20 pages
- **Branded cover page**: full cover page with company name, ticker, date, risk tier badge, "Angry Dolphin Underwriting System" branding
- **Angry Dolphin full branding** throughout: company name, confidential notice in footer
- **Gold/amber accent** (#D4A843) on white background: ties to existing brand identity from dark theme
- **Word is functional, PDF is presentation**: Word uses clean formatting (readable, editable) but doesn't replicate PDF design

### Table & Number Formatting
- **Negative numbers**: red parentheses — $(1,234) in red, traditional accounting convention
- **Adaptive precision**: large numbers in millions/billions ($394.3B), ratios to 2 decimals (1.07x), percentages to 1 decimal (23.4%)
- **YoY changes**: inline colored arrows — triangle-up +12.3% in green, triangle-down -5.1% in red, right next to the value
- **Risk indicators**: colored badges/pills — TRIGGERED in red pill, ELEVATED in amber, CLEAR in green
- **All 10 scoring factors** always shown: every factor visible with score, max, and risk level
- **Navy background, white text** table headers: strong contrast, classic financial report look
- **Subtle zebra striping**: light gray every other row for scanning long tables
- **Missing data**: gray italic "N/A"

### Page Layout & Print Behavior
- **Every major section on new page**: Executive Summary, Company Profile, Financial, Market, Governance, Litigation, Scoring each start fresh
- **Full header + footer**: Header: "CONFIDENTIAL -- [Company] D&O Worksheet". Footer: "Angry Dolphin Underwriting System | Page X of Y | [Date]"
- **No table of contents**: with section-per-page layout, structure is self-evident
- **Letter portrait**: standard US Letter (8.5" x 11") portrait orientation

### Chart Rendering in PDF
- **All four charts essential**: stock price, risk radar, ownership pie, litigation timeline
- **Explore additional visualizations**: any data that benefits from a graphic (financial trend lines, sector comparison, distress indicator gauges)
- **Full page width, half page height**: charts span full column (~7"), roughly half a page tall
- **Numbered figure captions**: "Figure 1: AAPL Stock Performance (12M)" below each chart

### Claude's Discretion
- Typography choice (serif/sans pairing that works best at 9-10pt for dense financial documents)
- Chart color scheme (light vs dark themed to match PDF)
- Additional visualization opportunities beyond the four core charts
- Word document formatting level of detail
- Exact spacing, margins, and typographic scale

</decisions>

<specifics>
## Specific Ideas

- S&P credit reports and Moody's rating reports are the visual benchmark
- Gold/amber (#D4A843) as the brand accent color carried from the dark theme
- Cover page with risk tier badge prominently displayed
- Red parentheses for negatives is non-negotiable (accounting convention)
- Colored badges/pills for risk indicators (TRIGGERED/ELEVATED/CLEAR) throughout
- Explore chart opportunities: "anything else that can benefit from a graphic of some kind"

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 40-professional-pdf-visual-polish*
*Context gathered: 2026-02-22*
