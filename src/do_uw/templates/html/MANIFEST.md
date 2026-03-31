# HTML Worksheet Manifest

Canonical specification for the D&O underwriting worksheet HTML output.
Every render must be validated against this manifest.

## Document Structure

```
COVER        → Company identity, size metrics, classification
SECTION 1    → Executive Summary
SECTION 2    → Company Profile
SECTION 3    → Financial Health
SECTION 4    → Market & Trading
SECTION 5    → Governance & Leadership
SECTION 6    → Litigation & Regulatory
SECTION 7    → Scoring & Risk Assessment
SECTION 8    → AI Risk Assessment
APPENDIX A   → Meeting Preparation Questions
APPENDIX B   → Sources
APPENDIX C   → QA / Audit Trail
APPENDIX D   → Data Coverage & Quality
```

## Per-Section Requirements

### Cover
- Company name, ticker, exchange
- Sector | Industry | Analysis date
- Business description (1-paragraph)
- **Size Metrics** (with position-on-range bars): Market Cap, Revenue, Employees, Years Public
- **Classification table**: CIK, SIC Code, GICS, NAICS, State of Inc., FYE, FPI status
- Subsidiaries count

### Section 1: Executive Summary
- **At-a-Glance strip** (5 cards): Claim Probability, Recommendation, Severity Band, Active Matters, Red Flags
- **Risk Classification** card (tier badge, quality score, composite score)
- **Key Findings** bullet list with severity classes
- D&O Implications callout
- Data Quality Notice (if applicable)

### Section 2: Company Profile
- **Narrative layers**: verdict badge, evidence grid, deep context (collapsible)
- SCR block (Situation / Complication / Resolution)
- AI Assessment bullets
- D&O Implications callout
- **Collapsible details**:
  - Business Description
  - Risk Factors (D&O-Relevant) — grouped by category, with NEW badges, severity+D&O ratings
  - Exposure Factors
  - Revenue Segments (table + pie)
  - Geographic Footprint
  - Customer/Supplier Concentration
  - Inherent Risk Assessment

### Section 3: Financial Health
- Narrative layers + SCR + AI Assessment + D&O Implications
- **Collapsible details**:
  - Annual Financial Comparison (FY vs FY-1) with sparklines and YoY change
  - Key Financial Metrics (Profitability, Solvency, Liquidity tables)
  - Financial Statements (Income, Balance Sheet, Cash Flow — multi-year)
  - Distress Indicators (Altman Z, Piotroski F, Ohlson O)
  - Earnings Quality
  - Audit Profile
  - Tax Risk
  - Peer Group Comparison
  - Quarterly Updates

### Section 4: Market & Trading
- Narrative layers + SCR + AI Assessment + D&O Implications
- **Collapsible details**:
  - Stock Performance stats table
  - **CHART: stock_1y** — Figure 1: 12 Month Price vs Sector & Market
  - **CHART: stock_5y** — Figure 2: 5 Year Price vs Sector & Market
  - Drop Event tables (1Y + 5Y) with DDL exposure
  - **CHART: drop_analysis_1y** — Figure 9: 12 Month Drop Events
  - **CHART: drop_analysis_5y** — Figure 10: 5 Year Drop Events
  - **CHART: drop_scatter_1y** — Figure 11: 12 Month Company vs Sector Drops
  - **CHART: drop_scatter_5y** — Figure 12: 5 Year Company vs Sector Drops
  - **CHART: drawdown_1y** — Figure 3: 12 Month Peak-to-Trough Drawdown
  - **CHART: drawdown_5y** — Figure 4: 5 Year Drawdown History
  - **CHART: volatility_1y** — Figure 5: 12 Month Rolling Volatility & Beta
  - **CHART: volatility_5y** — Figure 6: 5 Year Rolling Volatility & Beta
  - **CHART: relative_1y** — Figure 7: 12 Month Performance Indexed to 100
  - **CHART: relative_5y** — Figure 8: 5 Year Performance Indexed to 100
  - Short Interest
  - Capital Markets (earnings, analyst consensus, guidance)

### Section 5: Governance & Leadership
- Narrative layers + SCR + AI Assessment + D&O Implications
- **Collapsible details**:
  - Board Composition table (name, role, tenure, independence, committees)
  - **CHART: ownership** — Figure 3: Ownership Distribution
  - Ownership Structure (institutional, insider, mutual fund)
  - Executive Risk Profiles
  - Insider Trading activity
  - Activist Risk assessment
  - People Risk
  - Board Forensics

### Section 6: Litigation & Regulatory
- Narrative layers + SCR + AI Assessment + D&O Implications
- **Collapsible details**:
  - Active Matters table (case, coverage type, status, class period, lead counsel, settlement)
  - **CHART: timeline** — Figure 5: Litigation & Regulatory Timeline
  - Settlement History
  - SEC Enforcement status
  - Contingent Liabilities
  - Industry Litigation Patterns
  - Defense Strength assessment
  - Whistleblower metrics
  - Workforce/Product/Environmental litigation

### Section 7: Scoring & Risk Assessment
- Narrative layers + SCR + AI Assessment + D&O Implications
- **Bull/Bear Grid** (data-driven, citing specific metrics)
- **Collapsible details**:
  - Tier Classification (3-card: Quality Score, Composite Score, Tier badge)
  - Tier detail table (risk points, range, action guidance, probability, binding ceiling)
  - 10-Factor Scoring breakdown table
  - D&O Claim Peril Assessment table (8 perils, risk level, active chains, evidence)
  - Allegation Mapping / Peril Map
  - Hazard Profile
  - Severity Scenarios
  - Tower Position Recommendation
  - **CHART: radar** — Figure 4: 10-Factor Risk Profile
  - Calibration Notes
  - Pattern Detection
  - Temporal Signals
  - NLP Dashboard

### Section 8: AI Risk Assessment
- Overall AI Risk Score
- Dimension breakdown
- Competitive Position
- Forward Assessment

### Appendices
- **A**: Meeting Prep Questions (generated from signals)
- **B**: Sources (filing dates, URLs, data provenance)
- **C**: QA/Audit Trail (per-section signal disposition tables)
- **D**: Data Coverage & Quality (signal coverage stats)

## Chart Inventory (15 total)

| Key | Section | Figure | Description | Size |
|-----|---------|--------|-------------|------|
| stock_1y | 4 | 1 | Price vs Sector & Market (12M) | full-width |
| stock_5y | 4 | 2 | Price vs Sector & Market (5Y) | full-width |
| drawdown_1y | 4 | 3 | Peak-to-Trough Drawdown (12M) | full-width |
| drawdown_5y | 4 | 4 | Drawdown History (5Y) | full-width |
| volatility_1y | 4 | 5 | Rolling Volatility & Beta (12M) | full-width |
| volatility_5y | 4 | 6 | Rolling Volatility & Beta (5Y) | full-width |
| relative_1y | 4 | 7 | Performance Indexed to 100 (12M) | full-width |
| relative_5y | 4 | 8 | Performance Indexed to 100 (5Y) | full-width |
| drop_analysis_1y | 4 | 9 | Drop Events (12M) | full-width |
| drop_analysis_5y | 4 | 10 | Drop Events (5Y) | full-width |
| drop_scatter_1y | 4 | 11 | Company vs Sector Drops (12M) | full-width |
| drop_scatter_5y | 4 | 12 | Company vs Sector Drops (5Y) | full-width |
| ownership | 5 | 3 | Ownership Distribution | half-width |
| timeline | 6 | 5 | Litigation Timeline | full-width |
| radar | 7 | 4 | 10-Factor Risk Profile | half-width |

## Visual Components

### Every Section Must Have
1. `<h2>` section header
2. Narrative layers block (verdict badge + evidence grid)
3. SCR block (Situation / Complication / Resolution) — complication reflects actual risk level
4. AI Assessment bullets (no title leakage, no generic text)
5. D&O Implications callout
6. Collapsible details with section-specific content

### Data Display Rules
- Dollar amounts: `$427,840` (comma-separated)
- Limits/large values: `$50M`, `$3.9T` (compact)
- Percentages: `32.0%` (one decimal)
- Scores: `96.6` (one decimal, matching LLM narrative)
- Missing data: visible placeholder (`--` or `N/A`), never silently omitted
- Sparklines: inline SVG in financial comparison rows
- Trend arrows in YoY change columns

### CSS Architecture
- Design system variables in `:root` (colors, fonts, spacing)
- Inter font (body) + JetBrains Mono (tabular data)
- Navy/gold/white primary palette
- SVGs: `max-width: 100%; height: auto;` (responsive)
- Print: `@media print` section with adjusted margins, forced colors
- Collapsible sections via `<details>` elements

## Validation Checklist (run after every render)

- [ ] All 15 charts present and visible (not zero-height, not overflowing)
- [ ] No LLM title artifacts in narrative bullets
- [ ] Score values consistent between cards and narrative text
- [ ] Probability range consistent between executive summary and scoring
- [ ] Bull/bear items cite specific metrics (not generic "clean risk profile")
- [ ] SCR complication reflects section risk level
- [ ] All financial tables have sparklines where applicable
- [ ] Risk factors have category grouping and D&O relevance ratings
- [ ] Active matters table populated with real case data
- [ ] Sources appendix has filing dates
- [ ] QA audit trail shows per-section signal dispositions
