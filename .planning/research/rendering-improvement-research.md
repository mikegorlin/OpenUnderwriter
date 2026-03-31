# Deep Research: Rendering Output, Schema & Requirements Improvement

**Date**: 2026-03-02
**Scope**: Comprehensive analysis of current state, industry standards, tooling, and narrative quality for the D&O underwriting worksheet.

---

## Part 1: Current State Assessment

### What We Have (Summary)

| Dimension | Current State | Maturity |
|-----------|--------------|----------|
| **Pipeline** | 7-stage (RESOLVE→RENDER), single AnalysisState | Production |
| **Signals** | 400 across 8 prefixes, 100% mapped to sections | Production |
| **Sections** | 12 rendered sections, 82 facets, 9 legacy-or-unrendered | Mixed |
| **Templates** | 90+ Jinja2 (.html.j2), 11 component macros, 20+ custom filters | Mature |
| **Styling** | Tailwind + custom CSS, Bloomberg-inspired navy/gold palette | Good |
| **Charts** | 5 matplotlib static PNGs (stock 1Y/5Y, radar, ownership, timeline) | Basic |
| **PDF** | Playwright Chromium → WeasyPrint fallback | Working |
| **Narrative** | Pre-computed in BENCHMARK, section-level summaries | Basic |
| **Tests** | 3,967+, 289 render+section tests | Strong |

### What's Rendered vs What's in State

| Data Category | In State | Rendered | Gap |
|---------------|----------|----------|-----|
| Financial statements | 5 years | 100% | None |
| Hazard dimensions | 55 scored | Top 10-15 | **75% hidden** |
| Peer benchmarking | 10 peers + metrics | Mentioned narratively | **No comparison table** |
| Compensation analysis | Extracted | Not rendered | **100% hidden** |
| Executive shade factors | Extracted per person | Not visualized | **100% hidden** |
| Sentiment/coherence | 5 NLP signals | Not rendered | **100% hidden** |
| Dynamic interactions | Risk multipliers | Not rendered | **100% hidden** |
| Allegation mapping | Structured per peril | Peril level only | **75% hidden** |
| Board forensic detail | 10-12 profiles | Names + flags only | **60% hidden** |
| Text signals (NLP) | 49 dimensions | Mentioned | **90% hidden** |
| Quarterly updates | Extracted (when available) | Empty table header | **Template exists, data sparse** |

### Sections Without Facet-Driven Rendering (4 sections, 194 signals)

| Section | Signals | Issue |
|---------|---------|-------|
| forward_looking | 79 | No facet dispatch — all-or-nothing rendering |
| executive_risk | 20 | No facet dispatch |
| filing_analysis | 15 | No facet dispatch |
| red_flags | 0 (special) | Triggered CRF display only |

---

## Part 2: Industry Standards for D&O Underwriting Worksheets

### Professional Report Structure (Inverted Pyramid)

```
LEVEL 1 — DECISION LAYER
  Risk Score + Tier + Recommendation + 2-sentence thesis

LEVEL 2 — KEY RISK DRIVERS
  Red Flags Summary | Scoring Breakdown | Peer Position

LEVEL 3 — CORE ANALYSIS
  Financial Health | Governance | Litigation | Market Activity

LEVEL 4 — SUPPORTING DETAIL
  Company Profile | Executive Compensation | Insider Trading
  Corporate Events | M&A | Forward-Looking Risks

LEVEL 5 — REFERENCE
  Data Sources | Methodology | Confidence Levels | Peer Group Definition
```

### D&O Diary's 11-Component Framework (Industry Standard)

| # | Category | What We Cover | Gap |
|---|----------|--------------|-----|
| 1 | Company Size & Industry | Full | None |
| 2 | Financial Position | Full | None |
| 3 | Accounting Practices | Full (audit, restatements, material weakness) | None |
| 4 | Corporate History & M&A | Partial (event timeline) | **M&A deal detail** |
| 5 | Continuity Events | Good (stock drops, earnings) | **Product recalls, regulatory setbacks detail** |
| 6 | Forward Vulnerabilities | Data exists (79 FWRD signals) | **Not rendered as section** |
| 7 | Stock Volatility | Full | None |
| 8 | Management & Compensation | Data exists | **Comp not rendered, shade factors hidden** |
| 9 | Insider Trading | Good | **Cluster events detail hidden** |
| 10 | Disclosure Practices | Data exists (NLP signals) | **Not rendered as section** |
| 11 | Corporate Governance | Good structure | **Peer comparison, sentiment missing** |

### Credit Rating Report Patterns (Moody's/S&P/Fitch)

Key patterns to adopt:
- **Scorecard + Narrative Override**: Quantitative factors scored mechanically, then qualitative narrative explains why final rating may differ
- **Cash Flow Centricity**: Narrative organized around cash generation stability
- **Forward-Looking Emphasis**: Explicit outlook with what would trigger change
- **Bull Case / Bear Case**: Both scenarios with equivalent rigor and quantified implications

### CIQ-Style Layout Density (User Priority)

Target patterns from S&P Capital IQ:
1. **Paired-column KV tables** (4 cols per row: Label|Value|Label|Value)
2. **Two-column section layout** (Market Data | Corporate Data side-by-side)
3. **Collapsible sections** with chevrons
4. **Forward estimates alongside historicals** in financial tables
5. **Compact financial tables** with consistent column widths
6. **Minimal chrome** — thin borders, tight padding, 10-11px font

---

## Part 3: Narrative Architecture

### Current Narrative State

- Pre-computed in BENCHMARK stage (AI-generated section summaries)
- One narrative per section (company, governance, litigation, scoring)
- Narrative renders as introductory paragraph, then data follows
- No progressive disclosure (glance/standard/deep)
- No bull/bear case framing
- No cross-section references
- No confidence-calibrated language system

### Target Narrative Architecture

#### The SCR Framework (McKinsey)

**Situation → Complication → Resolution** for every section:

> **Situation**: "RPM International operates in specialty coatings with $7.3B revenue and 17 consecutive years of dividend growth."
>
> **Complication**: "However, the company faces three converging risk factors: declining free cash flow (-23% YoY), an active securities class action from the 2019 period, and board governance below median independence ratio."
>
> **Resolution**: "These factors position the risk as WATCH-tier, warranting elevated attachment point and capacity limits on primary."

#### Five-Layer Narrative Structure

```
Layer 1 — VERDICT (1 sentence)
  Rating/recommendation with score badge
  "CAUTION (67.3) — Elevated litigation exposure with moderate governance concerns."

Layer 2 — THESIS (2-3 sentences)
  SCR framework connecting key factors
  "Despite strong financial fundamentals, RPM faces..."

Layer 3 — EVIDENCE GRID (structured bullets)
  Each claim backed by specific data + source
  "• Board independence: 45% [DEF 14A, 2025-10-15] — below NYSE 50% minimum"

Layer 4 — IMPLICATIONS ("So What?")
  Connection to D&O pricing/limits/structure
  "Below-minimum independence increases derivative suit probability by ~2.3x"

Layer 5 — DEEP CONTEXT (expandable)
  Historical trends, peer comparisons, methodology notes
  Available on demand via <details> elements
```

#### Confidence-Calibrated Language System

| Confidence | Data Basis | Verbs | Example |
|------------|-----------|-------|---------|
| HIGH | Audited/official | "confirms," "establishes" | "The 10-K confirms total debt of $2.3B" |
| MEDIUM | Unaudited/cross-validated | "indicates," "reflects" | "Available data indicates declining margins" |
| LOW | Single source/derived | "suggests," "may indicate" | "News reports suggest potential regulatory scrutiny" |
| INFERENCE | Multi-factor analysis | "is consistent with," "the pattern resembles" | "These factors are consistent with elevated SCA exposure" |

#### Bull Case / Bear Case for Every Account

```
FAVORABLE CASE:
  "Strong governance, declining litigation, improving financials suggest
  below-average D&O exposure. Expected loss ratio: 35-45%."

ADVERSE CASE:
  "Active SCA, declining margins, and board turnover suggest above-average
  exposure. Expected loss ratio: 65-80%."

WEIGHT OF EVIDENCE:
  "Current data more strongly supports [case] due to [specific factors]."
```

### LLM Narrative Generation Pipeline

1. **Data Assembly**: Gather all extracted/scored/benchmarked data for the section
2. **Chain-of-Analysis (CoT)**: LLM reasons step-by-step, identifying material factors + interactions
3. **Template-Anchored Draft**: Use exemplar narratives from prior reports as few-shot templates
4. **Self-Refine Critique**: Evaluate for factual accuracy, analytical depth, confidence calibration
5. **Refinement**: Revise with attention to "so what?" connections
6. **Evidence Grounding**: Verify every claim has an attributed source; flag unsupported assertions

---

## Part 4: MCP Servers & Tooling Recommendations

### Tier 1: Must-Have (Immediate High Impact)

| # | Tool | Why | Cost | Effort |
|---|------|-----|------|--------|
| 1 | **CourtListener MCP** | Semantic search across 9M+ court opinions. Replaces Playwright scraping with structured API. 5,000 req/hr free. | Free | Medium |
| 2 | **Financial Modeling Prep MCP** | 253 tools: financial statements, SEC filings, insider trades, 13F holdings, analyst estimates, Congressional trading. | Free (250/day) | Low |
| 3 | **Exa MCP** or **Perplexity MCP** | Semantic/deep search for blind spot detection. Dramatically better than keyword-only Brave for litigation, short seller reports, regulatory actions. | Paid API | Medium |
| 4 | **TradingView Lightweight Charts** | 35KB inline financial charts for HTML. Purpose-built for stock price visualization. | Free (Apache 2.0) | Low |
| 5 | **Sparklines.js** | Zero-dep SVG sparklines for inline table charts. CIQ-style density. | Free | Low |

### Tier 2: Should-Have (High Impact, More Effort)

| # | Tool | Why | Cost | Effort |
|---|------|-----|------|--------|
| 6 | **Plotly** (Python) | Interactive charts for HTML (candlestick, waterfall, radar, treemap). Static export via kaleido for PDF. Replaces matplotlib. | Free | Medium |
| 7 | **Paged.js** | CSS Paged Media polyfill — proper PDF headers, footers, page numbers, TOC with page refs. Works with existing Playwright pipeline. | Free | Medium |
| 8 | **Coresignal MCP** | 725M employee records for executive profiling, qualification verification, work history. Fills governance extraction gaps. | Paid | Medium |
| 9 | **Great Tables** (Python) | Publication-quality financial statement tables with built-in currency/pct formatting. | Free | Medium-High |

### Tier 3: Nice-to-Have (Future)

| # | Tool | Why | Cost |
|---|------|-----|------|
| 10 | **Kensho / S&P Global MCP** | Institutional-grade Capital IQ data (the gold standard). | Enterprise $$$ |
| 11 | **Octagon MCP** | 10 years SEC filings + earnings transcripts + private market data. | Paid |
| 12 | **Google News & Trends MCP** | Free real-time news monitoring with trend/breakout alerts. | Free |
| 13 | **docxtpl** | Jinja2 templates inside Word docs (replaces programmatic python-docx). | Free |
| 14 | **Typst** (PDF backend) | Modern typesetting in Rust, 100x faster than LaTeX, Python bindings. | Free |

### Not Recommended

| Tool | Reason |
|------|--------|
| Yahoo Finance MCP | Already have yfinance; MCP wrapper adds complexity without new capability |
| Alpha Vantage MCP | Overlaps with yfinance + FMP; low free tier (25/day) |
| Quarto | Migration cost from 90+ Jinja2 templates too high |
| React frameworks (Tremor) | Adds Node.js build chain to Python CLI |
| Highcharts | Commercial license required ($336+/yr) |
| D3.js raw | Too low-level when Plotly handles financial charts declaratively |

---

## Part 5: Interactive HTML Report Improvements

### Tier 1: Quick Wins (Low Effort, High Impact)

| Change | Impact | Effort | How |
|--------|--------|--------|-----|
| `tabular-nums` on financial tables | Visual alignment | Trivial | One CSS class |
| Collapsible sections with `<details>` | Usability | Very Low | Pure HTML5, zero JS |
| Sticky table headers | Usability | Low | ~10 lines CSS |
| Print CSS (`break-inside: avoid`) | PDF quality | Low | ~30 lines CSS |
| Active TOC highlighting | Navigation | Low-Medium | IntersectionObserver |

### Tier 2: Medium Effort, High Impact

| Change | Impact | Effort | How |
|--------|--------|--------|-----|
| Hover tooltips (source/confidence) | Data transparency | Medium | Tippy.js (8KB) or CSS title attrs |
| Tabbed financial statements | Space efficiency | Low | CSS-only tabs |
| Replace matplotlib → Plotly | Interactivity | Medium | Chart code is isolated |
| TradingView Lightweight Charts | Stock section quality | Low-Medium | 35KB, purpose-built |
| Paged.js for PDF headers/footers | PDF professionalism | Medium | CSS Paged Media rules |

### Tier 3: Strategic (Higher Effort)

| Change | Impact | Effort |
|--------|--------|--------|
| Progressive disclosure (glance/standard/deep) | Major UX improvement | High |
| Client-side search within report | Power user feature | Low |
| Dark mode toggle | Aesthetic | Medium |
| Typst PDF backend | Typographic quality | High |

---

## Part 6: Schema & Rendering Gap Analysis

### New Sections/Facets Needed

Based on industry standards vs current output:

#### 1. Executive Compensation Section (NEW — data exists, not rendered)
- Named executive officer pay table (salary, bonus, equity, total)
- CEO-to-median pay ratio
- Say-on-pay vote results with trend
- Equity burn rate
- Clawback provisions
- Performance adjustment basis
- **Source**: `extracted.governance.comp_analysis` (fully populated)

#### 2. Peer Comparison Matrix (NEW — data exists, not rendered)
- Peer group table: ticker, name, market cap, quality score, SCA history
- Percentile rankings by metric
- Subject vs peer median for key metrics
- Visual: small bar charts or sparklines showing relative position
- **Source**: `benchmark.peer_quality_scores`, `benchmark.peer_rankings`, `benchmark.metric_details`

#### 3. Forward-Looking Risk Section (NEEDS FACETS — 79 signals, no facets)
- Group by: WARN (32), EVENT (17), MACRO (15), DISC (9), NARRATIVE (6)
- Upcoming catalysts timeline (debt maturity, covenant tests, lockup expiry)
- Macro risk dashboard (rates, FX, commodity, geopolitical)
- Disclosure quality assessment
- **Source**: 79 FWRD.* signals already extracted

#### 4. Hazard Profile Detail (EXPAND — currently top 10-15 only)
- 7 category cards (H1-H7) with weighted scores and data coverage %
- Full 55-dimension matrix with drill-down by category
- Dynamic interaction cards showing risk multipliers
- **Source**: `hazard_profile.categories`, `hazard_profile.dynamic_interactions`

#### 5. Sentiment & Narrative Coherence (NEW — data exists, not rendered)
- L-M dictionary trend scores (negative, uncertainty, litigious)
- MD&A-to-financials alignment
- Tone-vs-financials assessment
- Strategy-vs-results consistency
- Year-over-year disclosure changes
- **Source**: `extracted.governance.sentiment`, `extracted.governance.narrative_coherence`

#### 6. Executive Forensic Detail (EXPAND — currently partial)
- Individual executive risk cards with:
  - Prior litigation details (not just counts)
  - Shade factors (character/conduct)
  - Departure context and succession risk
  - Bio summary with qualification assessment
- **Source**: `extracted.governance.leadership.executives`, `extracted.governance.board_forensics`

### Schema Additions Needed

#### For Narrative Architecture
```python
# Add to AnalysisResults or new NarrativeResults
class SectionNarrative(BaseModel):
    verdict: str                    # 1-sentence rating
    thesis: str                     # 2-3 sentence SCR
    evidence: list[EvidenceBullet]  # Sourced claims
    implications: str               # "So what?" paragraph
    bull_case: str                  # Favorable scenario
    bear_case: str                  # Adverse scenario
    weight_of_evidence: str         # Which case is stronger
    confidence: Confidence          # Overall narrative confidence

class EvidenceBullet(BaseModel):
    claim: str
    data_point: str
    source: str
    confidence: Confidence
```

#### For Progressive Disclosure
```python
class DetailLevel(str, Enum):
    GLANCE = "glance"      # 1-2 lines, always visible
    STANDARD = "standard"  # Default expanded, working level
    DEEP = "deep"          # Collapsed, expanded on click

# Each rendered element gets a detail_level tag
```

#### For Peer Comparison
```python
class PeerComparisonRow(BaseModel):
    ticker: str
    name: str
    market_cap: float | None
    quality_score: float | None
    sca_count_5y: int | None
    governance_score: float | None
    claim_probability: float | None
    relative_rank: int               # 1 = best in group
```

---

## Part 7: Prioritized Implementation Roadmap

### Wave 1: Visual Polish & Quick Wins (Low effort, immediate impact)

1. Add `tabular-nums` to all financial table cells
2. Wrap major sections in `<details>/<summary>` for collapse
3. Add sticky table headers via CSS
4. Add `break-inside: avoid` print CSS
5. Implement paired-column KV tables (4 cols/row) for CIQ density
6. Add sparklines SVG next to key metrics in KV tables

### Wave 2: Hidden Data Surfacing (Medium effort, high analytical value)

7. Render compensation analysis section
8. Render peer comparison matrix table
9. Render hazard category cards (H1-H7) with scores
10. Render sentiment/coherence summary card
11. Expand executive forensic profiles (shade factors, departure context)
12. Expand allegation mapping detail per peril
13. Facetize forward_looking section (group 79 signals into 5 facet groups)

### Wave 3: Narrative Depth (Medium-high effort, professional quality)

14. Implement 5-layer narrative structure (verdict/thesis/evidence/implications/deep)
15. Add bull case / bear case framing
16. Implement confidence-calibrated language system
17. Add cross-section references in narratives
18. Implement progressive disclosure (glance/standard/deep tiers)

### Wave 4: Interactive Charts & PDF Quality (Medium effort, visual excellence)

19. Replace matplotlib → Plotly for HTML (keep matplotlib for Word)
20. Add TradingView Lightweight Charts for stock section
21. Add Paged.js for CSS Paged Media (PDF headers, footers, page numbers)
22. Add hover tooltips with source/confidence on metrics
23. Add tabbed financial statements (Income | Balance | Cash Flow)

### Wave 5: MCP & Data Source Expansion (Ongoing)

24. Integrate CourtListener MCP for litigation acquisition
25. Integrate Financial Modeling Prep MCP for financial data
26. Integrate Exa or Perplexity MCP for semantic blind spot detection
27. Evaluate Coresignal MCP for executive profiling
28. Evaluate Kensho/S&P Global MCP for institutional-grade data

---

## Part 8: Key Architectural Principles

### Preserve What Works
- Jinja2 template system (90+ templates, mature)
- Facet-driven dispatch (Phase 56 architecture)
- Single AnalysisState model
- SourcedValue provenance on every field
- Brain YAML as source of truth

### Enhance, Don't Replace
- Add interactive charts alongside static (Plotly for HTML, matplotlib/kaleido for PDF/Word)
- Add progressive disclosure around existing content (wrap in `<details>`)
- Add narrative layers around existing data (verdict/thesis/evidence above current content)
- Add new sections for hidden data (compensation, peers, sentiment) using existing facet dispatch

### Every Data Point Must Earn Its Place
- Don't render data just because it exists — render it because an underwriter needs it
- Every new section must answer a specific underwriting question
- Compensation: "Is management aligned with shareholders?"
- Peers: "How does this account compare to similar risks?"
- Sentiment: "Are there early warning signs in how management communicates?"
- Forward-looking: "What could change this risk profile in the next 12 months?"

---

*Research compiled from 8 parallel research agents analyzing: rendering pipeline, data models/schema, actual output quality, D&O industry standards, brain signal coverage, MCP/plugin ecosystem, narrative generation techniques, and interactive HTML report technologies.*
