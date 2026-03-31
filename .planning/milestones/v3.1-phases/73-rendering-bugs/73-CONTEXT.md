# Phase 73: Rendering & Bug Fixes - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

New HTML templates for quarterly trends (8-quarter XBRL data), forensic dashboard (Phase 69 results), and peer percentile display (Phase 72 Frames data). Enhanced insider trading table. Beneish component breakdown. Bug fixes for false SCA classification and PDF header overlap. Company logo polish. HTML/PDF parity for all new templates.

</domain>

<decisions>
## Implementation Decisions

### Quarterly Trend Table (RENDER-01)
- Tabbed layout (Income | Balance Sheet | Cash Flow) using existing CSS radio tab pattern from `financial_statements.html.j2`
- Summary strip above tabs showing 4 cross-statement metrics: Revenue, Net Income, Free Cash Flow, Total Assets
- All 8 quarters displayed (no collapse/expand, full 2-year view)
- Each metric row has a sparkline (via `render_sparkline()`) plus a YoY % change column for the most recent quarter
- New facet in `financial_health.yaml` pointing to enhanced `quarterly_trend.html.j2`

### Forensic Dashboard (RENDER-02)
- Color-banded sections sorted worst-first: red Critical band at top, amber Warning in middle, green Normal at bottom; empty bands hidden
- Each card shows: module name, composite score, worst individual finding; expandable `<details>` to show all individual metrics
- Beneish M-Score gets a dedicated component table (all 8 components: DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA) with individual scores + thresholds + pass/fail. Separate from the hazard card grid.
- New facet in `financial_health.yaml` pointing to `sections/financial/forensic_dashboard.html.j2`
- All visual instructions via facet YAML definitions (brain-driven rendering pattern)

### Peer Percentile Display (RENDER-03)
- Lives in Financial Health section as a new facet in `financial_health.yaml`
- Dual horizontal bar per metric: navy bar for overall percentile (all SEC filers), gold bar for sector percentile (2-digit SIC peers)
- All 15 metrics displayed (10 direct XBRL + 5 derived ratios)
- Color-coded by risk quartile, direction-aware: high leverage = red, high margin = green; bottom quartile in risky direction gets red fill, top quartile in favorable direction gets green fill
- Uses existing `.percentile-bar` + `.percentile-fill` CSS classes in `components.css`

### False SCA Bug Fix (RENDER-06)
- Aggressive 3-layer extraction filter:
  1. Prompt hardening: explicit rejection examples in LLM extraction prompt for boilerplate 10-K language
  2. Pattern expansion: additional boilerplate patterns ("PARTY TO LEGAL MATTERS", "LEGAL MATTERS ARISING", "INVOLVED IN LITIGATION", "SUBJECT TO CLAIMS", etc.)
  3. Specificity gate: if SCA entry lacks ALL of named plaintiff, court/jurisdiction, and specific filing date -- treat as boilerplate
- NEW: Web search verification -- targeted search for `"{company name}" securities class action` to confirm/discover real SCAs. Acts as both verification of extracted findings AND fallback discovery for missed SCAs.
- Cross-validation: extracted SCAs checked against web search + SCAC + CourtListener results
- Unverified SCAs (extracted from filing but no web/SCAC/CourtListener corroboration) downgraded to LOW confidence
- CRF-1 red flag gate still triggers on LOW confidence SCAs but displays "unverified" caveat in the red flag description

### Claude's Discretion
- PDF header overlap fix (RENDER-07): CSS-level fix, Claude picks approach
- Company logo polish (RENDER-08): already partially implemented, Claude completes
- Insider trading table enhancement (RENDER-04): augment with Phase 71 ownership concentration data
- Beneish component table layout details
- Which metrics go in which tab of the quarterly trend table
- HTML/PDF parity testing approach (RENDER-09)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `render_sparkline()` in `charts/sparklines.py`: pure SVG sparkline generator, 119 lines
- CSS tab pattern in `charts.css`: radio input + `:checked` selector for tab switching
- `.percentile-bar` + `.percentile-fill` CSS in `components.css`: horizontal bar rendering
- `.hazard-card` CSS in `components.css`: card layout with expand/collapse
- `kv_table()` macro from `components/tables.html.j2`: consistent table styling
- `risk-critical`, `risk-elevated`, `risk-positive` CSS classes for severity colors
- `format_na` Jinja2 filter: handles Python None correctly (unlike `default`)
- `gap_notice()` macro: graceful "data not available" display

### Established Patterns
- Facet YAML in `brain/sections/financial_health.yaml` defines what renders and in what order
- Context builders in `stages/render/context_builders/` provide data to templates
- Component CSS goes in `components.css` (not `styles.css` which is at limit)
- `pdf_mode` context flag differentiates browser HTML from PDF HTML
- `<details>` auto-expanded in PDF via Playwright `evaluate()`
- No JavaScript in charts/visualization (CSS-only or SVG)

### Integration Points
- `extract_financials()` in `context_builders/financials.py` -- add quarterly XBRL trend data + forensic dashboard data + peer percentile data
- `financial_health.yaml` -- add 3 new facet entries (quarterly trend, forensic dashboard, peer percentiles)
- `section_renderer.py` -- existing dispatch handles new facets automatically
- `_is_boilerplate_litigation()` in `signal_mappers_ext.py` -- expand patterns
- `red_flag_gates.py` -- add specificity gate + unverified caveat
- LLM extraction prompt in `prompts.py` -- harden boilerplate rejection
- Litigation acquisition -- add targeted SCA web search verification step

</code_context>

<specifics>
## Specific Ideas

- Forensic dashboard should feel like a risk heat map -- worst problems visually prominent at top (red band), good results tucked at bottom (green band)
- Beneish M-Score table is the most referenced forensic tool by underwriters -- it deserves dedicated real estate, not just a card
- Peer percentile bars should immediately communicate "where does this company sit" -- dual navy/gold bars show overall vs sector context at a glance
- Web search verification for SCAs is the right approach because a real SCA is ALWAYS a public event with a discoverable footprint; absence of web corroboration is strong evidence of boilerplate
- Quarterly summary strip provides a "dashboard within a dashboard" -- the 4 key numbers before you dive into statement-level tabs

</specifics>

<deferred>
## Deferred Ideas

- Industry-specific forensic thresholds (e.g., different Beneish norms for financial vs industrial companies) -- future milestone
- Interactive percentile drill-down (click bar to see distribution) -- future phase
- Quarterly data comparison against analyst consensus estimates -- requires additional data source

</deferred>

---

*Phase: 73-rendering-bugs*
*Context gathered: 2026-03-07*
