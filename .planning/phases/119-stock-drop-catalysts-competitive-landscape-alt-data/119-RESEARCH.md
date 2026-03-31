# Phase 119: Stock Drop Catalysts + Competitive Landscape + Alt Data - Research

**Researched:** 2026-03-20
**Domain:** Stock analytics enhancement, competitive intelligence extraction, alternative risk data
**Confidence:** HIGH

## Summary

Phase 119 addresses three distinct but complementary areas: (1) enriching existing stock drop analysis with catalyst identification, D&O assessment columns, price/volume context, and multi-horizon performance summary; (2) implementing the deferred DOSSIER-07 competitive landscape and moat assessment section; and (3) adding four alternative data risk assessments (ESG/greenwashing, AI-washing, tariff/trade, competitor SCA contagion).

The critical finding is that **nearly all required data is already acquired** by existing infrastructure. Stock drops already have trigger attribution, 8-K enrichment, web search enrichment, and decomposition -- Phase 119 needs to add a "Catalyst & D&O Assessment" column, From/To price columns, volume data, and a narrative wrapper. Analyst data is already acquired via yfinance (recommendations, price targets, upgrades/downgrades, earnings estimates) but rendered minimally -- this phase expands the rendering. Competitive landscape requires a new LLM extraction from 10-K Item 1 following the Phase 118 dossier extraction pattern. Alternative data signals map to existing environment assessment infrastructure (ENVR.* signals) and brain signal YAML patterns.

**Primary recommendation:** Structure as 6 plans following the Phase 118 pattern: (1) Pydantic models for competitive landscape + alt data, (2) stock drop catalyst enrichment + multi-horizon returns, (3) competitive landscape LLM extraction + moat assessment, (4) alt data extraction + peer SCA check, (5) context builders + Jinja2 templates, (6) pipeline wiring + manifest updates.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STOCK-01 | Every stock drop >5% has "Catalyst & D&O Assessment" column | Existing trigger_category, trigger_description, trigger_8k_items on StockDropEvent provide catalyst data; need to add D&O assessment column via do_context pattern |
| STOCK-02 | Stock drops table includes From price, To price, Volume | StockDropEvent has close_price; need from_price (price at period start) and volume fields; yfinance history_2y has Volume data |
| STOCK-03 | "D&O Underwriting Implication" narrative after drop table | New narrative field generated in BENCHMARK via LLM or algorithmic pattern analysis of drop characteristics |
| STOCK-04 | Multi-horizon returns (1D, 5D, 1M, 3M, 6M, 52W) + analyst consensus + narrative | yfinance history_1y has all price data for computation; analyst data already acquired (recommendations, price targets, upgrades_downgrades) |
| STOCK-05 | Pattern Detection section | Existing infrastructure: grouping, decay weighting, market-wide tagging; need new pattern classification (post-IPO arc, clusters, support levels) |
| STOCK-06 | Analyst consensus table with interpretive narrative | AnalystSentimentProfile already has coverage_count, consensus, target prices, upgrades/downgrades; need expanded rendering + LLM narrative |
| DOSSIER-07 | Competitive Landscape + Moat Assessment | Deferred placeholder exists in manifest; needs LLM extraction from 10-K Item 1, Pydantic models, context builder, template |
| ALTDATA-01 | ESG/Greenwashing Risk assessment | Existing ENVR.esg signal + esg_gap_score extraction; need structured table rendering with D&O Relevance |
| ALTDATA-02 | AI-Washing Risk assessment | Existing AI risk module (models/ai_risk.py, stages/score/ai_risk_scoring.py); need restructured rendering as alt data table |
| ALTDATA-03 | Tariff/Trade Exposure assessment | Existing ENVR.geopolitical signal + geographic operations data; need structured table + D&O Relevance |
| ALTDATA-04 | Competitor SCA Check | New: query Stanford SCAC or litigation data for SCA filings against companies in same SIC/sector |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Purpose | Why Standard |
|---------|---------|--------------|
| Pydantic v2 | Models for CompetitiveLandscape, AltDataAssessment, StockPerformanceSummary | Project standard; ConfigDict(frozen=False) pattern from Phase 118 |
| yfinance | All stock data already acquired: history, recommendations, price targets, upgrades | Existing acquire client; no new acquisition needed |
| Jinja2 | Template rendering for new sections | Existing template infrastructure |
| httpx | Any new HTTP calls (Stanford SCAC for ALTDATA-04) | Project standard HTTP client |

### No New Dependencies Required
This phase uses only existing project dependencies. No new packages needed.

## Architecture Patterns

### Recommended Project Structure (New Files)
```
src/do_uw/
  models/
    competitive_landscape.py    # CompetitiveLandscape, MoatDimension, PeerRow
    alt_data.py                 # AltDataAssessments, ESGRisk, AIWashingRisk, TariffExposure, PeerSCACheck
  stages/
    extract/
      competitive_extraction.py # LLM extraction from 10-K Item 1
      alt_data_extraction.py    # Alt data signal extraction
      stock_catalyst.py         # D&O assessment generation for drop catalysts
    benchmark/
      competitive_enrichment.py # Moat assessment D&O enrichment
      alt_data_enrichment.py    # Alt data D&O relevance generation
      stock_drop_narrative.py   # Drop pattern narrative + multi-horizon summary
    render/
      context_builders/
        dossier_competitive.py  # Context builder for competitive landscape
        alt_data_context.py     # Context builders for alt data tables
        stock_catalyst_context.py # Enhanced drop events + performance summary
  templates/html/
    sections/
      dossier/competitive_landscape.html.j2  # Replaces deferred placeholder
      market/stock_performance_summary.html.j2 # Multi-horizon + analyst
      market/stock_drop_catalyst.html.j2     # Enhanced drop table with catalyst + D&O
      alt_data/esg_risk.html.j2
      alt_data/ai_washing.html.j2
      alt_data/tariff_exposure.html.j2
      alt_data/peer_sca.html.j2
```

### Pattern 1: StockDropEvent Enhancement (Additive Fields)
**What:** Add `from_price`, `volume`, `do_assessment` fields to existing StockDropEvent model
**When to use:** STOCK-01, STOCK-02 requirements
**Example:**
```python
# Add to StockDropEvent in models/market_events.py (additive, no removal)
from_price: float | None = Field(
    default=None, description="Price at start of drop period"
)
volume: int | None = Field(
    default=None, description="Trading volume on drop date"
)
do_assessment: str = Field(
    default="", description="D&O litigation risk assessment for this catalyst"
)
```

### Pattern 2: LLM Extraction for Competitive Landscape (Phase 118 Pattern)
**What:** Focused LLM extraction from 10-K Item 1 targeting competitive landscape data
**When to use:** DOSSIER-07
**Example:**
```python
# Follow dossier_extraction.py pattern: focused prompts with QUAL-03 context
_COMPETITIVE_PROMPT = """Extract competitive landscape from this 10-K filing.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
Scoring Context: {scoring_summary}

From Item 1 (Business Description), extract:
1. Named competitors (4+ companies)
2. Competitive dimensions: market share, revenue, margin, growth rate, R&D spend, patents, etc.
3. Moat characteristics: data advantage, switching costs, scale, brand, network effects, regulatory barrier, distribution lock
"""
```

### Pattern 3: Context Builder for Alt Data (Phase 118 Dossier Pattern)
**What:** Pure data formatting context builders consuming state data, zero evaluative logic
**When to use:** ALTDATA-01 through ALTDATA-04
**Example:**
```python
# Follow dossier_what_company_does.py pattern
def build_alt_data_esg(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ESG/Greenwashing risk context for template."""
    # Consume ENVR.esg signal do_context + environment assessment data
    result: dict[str, Any] = {}
    # ... pure formatting, no business logic
    return result
```

### Pattern 4: Multi-Horizon Return Computation
**What:** Compute 1D, 5D, 1M, 3M, 6M, 52W returns from existing price history
**When to use:** STOCK-04
**Example:**
```python
# Use existing get_close_prices() from stock_drops.py
def compute_multi_horizon_returns(history: dict[str, Any]) -> dict[str, float | None]:
    prices = get_close_prices(history)
    if len(prices) < 2:
        return {}
    current = prices[-1]
    horizons = {"1D": 1, "5D": 5, "1M": 21, "3M": 63, "6M": 126, "52W": 252}
    returns = {}
    for label, days in horizons.items():
        if len(prices) > days:
            prior = prices[-(days + 1)]
            returns[label] = round((current - prior) / prior * 100, 2)
    return returns
```

### Anti-Patterns to Avoid
- **Do NOT create new acquisition clients** -- all data is already acquired via yfinance, web search, and SEC filings. Only exception: ALTDATA-04 peer SCA check may need to query acquired litigation data or Stanford SCAC data already in state.
- **Do NOT put D&O assessment logic in templates or context builders** -- all D&O commentary must come from brain YAML do_context or be generated in BENCHMARK stage
- **Do NOT modify existing drop table rendering destructively** -- add new columns additively; existing columns (Date, Drop, Recency, AR, Type, Trigger, Market/Sector/Company, Recovery, Disclosure) must remain
- **Do NOT create monolithic files** -- split competitive landscape extraction, alt data extraction, and stock catalyst enrichment into separate files per 500-line rule

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| D&O catalyst assessment text | Custom Python if/elif chains | Brain YAML do_context templates on stock drop signals | Brain portability principle; renderers are dumb consumers |
| Multi-horizon return math | Custom numpy/scipy | Simple arithmetic on existing get_close_prices() output | Already computed as percentages; no libraries needed |
| Competitive landscape parsing | Custom 10-K regex parser | LLM extraction with focused prompt (Phase 118 pattern) | 10-K text too varied for regex; LLM handles ambiguity |
| ESG/AI-wash scoring | New scoring framework | Existing ENVR.* signal infrastructure + do_context | Environment assessment already extracts esg_gap_score, geopolitical_risk_score |
| Peer SCA lookup | New web scraping pipeline | Query existing Stanford SCAC data from state.acquired_data or brain/framework/rap_scac_validation.yaml | SCAC data already acquired in litigation stage |

## Common Pitfalls

### Pitfall 1: Overcomplicating Stock Drop Enhancement
**What goes wrong:** Trying to rebuild the drop table from scratch instead of adding columns to existing infrastructure.
**Why it happens:** The existing StockDropEvent + build_drop_events() + stock_drops.html.j2 is complex (15+ columns already). Tempting to rewrite.
**How to avoid:** Add `from_price`, `volume`, `do_assessment` fields to StockDropEvent. Add columns to build_drop_events() context builder. Add `<th>` columns to stock_drops.html.j2. Preserve ALL existing columns.
**Warning signs:** Removing existing fields from StockDropEvent, changing build_drop_events() return structure, deleting rows from the template.

### Pitfall 2: Competitive Landscape Data Quality
**What goes wrong:** LLM extraction returns vague or hallucinated competitor data (wrong revenues, made-up market shares).
**Why it happens:** 10-K Item 1 often names competitors without specific metrics. LLM fills in blanks.
**How to avoid:** Mark LLM-extracted competitive data as MEDIUM confidence. Use "Not Disclosed" for metrics not in 10-K. Cross-reference with yfinance data for named competitors if possible. Do NOT present LLM-generated market share numbers as fact.
**Warning signs:** Precise market share percentages for all competitors (likely hallucinated).

### Pitfall 3: Alt Data Scope Creep
**What goes wrong:** Each alt data signal becomes a mini-project with custom acquisition, custom scoring, custom rendering.
**Why it happens:** ESG, AI-washing, tariffs, peer SCA are each deep domains.
**How to avoid:** Keep each alt data assessment to a structured table with 3-5 indicator rows and a D&O Relevance column. Leverage existing data (10-K text, environment assessment, brain signals). LLM generates the assessment narrative from existing data, not new acquisition.
**Warning signs:** Adding new MCP tool calls, new data sources, or complex scoring algorithms.

### Pitfall 4: Missing safe_float() on New Render Code
**What goes wrong:** New template code uses bare float() on state values that contain "N/A" or None.
**Why it happens:** Every new rendering path risks this. Critical project lesson.
**How to avoid:** Import and use safe_float() from stages/render/formatters.py for ALL numeric formatting in new context builders. Use format_currency(), format_percentage(), na_if_none() helpers.
**Warning signs:** Any bare `float()` or `int()` call on state data in new code.

### Pitfall 5: Manifest Deferred Group Not Updated
**What goes wrong:** The deferred/dossier_competitive_landscape.html.j2 placeholder stays in manifest after implementing the real template.
**Why it happens:** Manifest entry already exists with render_as: deferred. Easy to forget to update.
**How to avoid:** Change manifest entry from `template: deferred/dossier_competitive_landscape.html.j2` / `render_as: deferred` to the actual template path and `render_as: data_table`.

## Code Examples

### Existing Drop Event Context (build_drop_events in _market_display.py)
```python
# Current fields in drop_events dict:
# date, drop_pct, type, days, trigger, trigger_description, trigger_category,
# sector, company_specific, recovery, abnormal_return, t_stat, significant,
# decay_weight, decay_weighted_severity, market_pct, sector_pct, company_pct,
# market_driven, disclosure_badge
#
# STOCK-01 adds: do_assessment (from brain do_context or BENCHMARK)
# STOCK-02 adds: from_price, to_price, volume
```

### Existing Analyst Data Available (market_client.py acquires all of these)
```python
# Already acquired and available in state.acquired_data.market_data:
# - recommendations: DataFrame with firm, toGrade, fromGrade, action
# - analyst_price_targets: mean, high, low, current, number
# - upgrades_downgrades: DataFrame with recent changes
# - earnings_estimate: current/next quarter EPS estimates
# - revenue_estimate: revenue estimates
# - growth_estimates: growth rate estimates
#
# AnalystSentimentProfile already has:
# coverage_count, consensus, recommendation_mean, target_price_mean/high/low,
# recent_upgrades, recent_downgrades
#
# STOCK-06 enriches rendering: expanded table + LLM narrative
```

### Manifest Update for Competitive Landscape
```yaml
# Change from:
  - id: dossier_competitive_landscape
    name: Competitive Landscape & Moat Assessment
    template: deferred/dossier_competitive_landscape.html.j2
    render_as: deferred
    display_only: true
# To:
  - id: dossier_competitive_landscape
    name: Competitive Landscape & Moat Assessment
    template: sections/dossier/competitive_landscape.html.j2
    render_as: data_table
    display_only: true
```

### Brain YAML do_context for Drop Catalyst (New Signal or Signal Update)
```yaml
# In brain/signals/stock/price.yaml, update stock drop signals with:
presentation:
  do_context:
    TRIGGERED_RED: >-
      {company} stock dropped {value}% on {date} — catalyst: {trigger_category}.
      D&O Assessment: {do_assessment}. This company-specific drop exceeds sector
      decline and creates corrective disclosure window for Section 10(b) claims.
    TRIGGERED_YELLOW: >-
      {company} stock dropped {value}% on {date} — catalyst: {trigger_category}.
      D&O Assessment: {do_assessment}. Drop partially market-driven but
      company-specific residual warrants monitoring.
    CLEAR: >-
      No significant stock drops exceeding 5% threshold in analysis period.
      Clean stock performance reduces SCA filing probability.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Drop table has trigger but no D&O assessment | Add "Catalyst & D&O Assessment" column | Phase 119 | Underwriters see WHY a drop matters for D&O, not just what happened |
| Analyst consensus as 3-field KV table | Expanded analyst table with rating distribution + targets + narrative | Phase 119 | Matches gold standard PDF format |
| No competitive landscape | LLM-extracted peer table + moat assessment from 10-K | Phase 119 | Fills DOSSIER-07 gap, completes intelligence dossier |
| Environment signals exist but no structured alt data tables | ESG/AI/Tariff/Peer SCA as separate assessable tables | Phase 119 | Surfaces emerging D&O risk vectors with D&O Relevance |

## Open Questions

1. **Peer SCA data source for ALTDATA-04**
   - What we know: Stanford SCAC data is acquired via Playwright in ACQUIRE stage for the target company. SIC codes and sector classification are available.
   - What's unclear: Whether peer company SCAs are systematically acquired. May need to query acquired web search results or add a targeted search for "[sector] securities class action 2025 2026".
   - Recommendation: First check existing web_search_results for sector SCA mentions. If insufficient, add one Brave Search query in ACQUIRE with sector + "securities class action" terms. Mark as MEDIUM confidence.

2. **Multi-horizon return labels for recent IPOs**
   - What we know: StockPerformance.trading_days_available tracks actual days. IPO companies may have < 252 days.
   - What's unclear: How to label returns when company has been public < 52 weeks.
   - Recommendation: Use "Since IPO (Xmo)" for any horizon exceeding available history. This pattern already exists in stock_performance.py for 1Y/5Y distinction.

3. **Competitive landscape data completeness**
   - What we know: 10-K Item 1 names competitors but rarely provides their financial metrics.
   - What's unclear: Whether yfinance data for named competitors should be fetched in ACQUIRE or if LLM-extracted qualitative assessment suffices.
   - Recommendation: Do NOT add new acquisition for competitor tickers in Phase 119. Extract qualitative competitive dimensions from 10-K only. Mark as "Enhancement opportunity" for v9.0 when peer data acquisition is added.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/ -x --timeout=30 -q` |
| Full suite command | `uv run pytest tests/ --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STOCK-01 | Drop events have do_assessment field | unit | `uv run pytest tests/stages/extract/test_stock_catalyst.py -x` | Wave 0 |
| STOCK-02 | Drop events have from_price, to_price, volume | unit | `uv run pytest tests/stages/extract/test_stock_drops_enhanced.py -x` | Wave 0 |
| STOCK-03 | D&O Underwriting Implication narrative generated | unit | `uv run pytest tests/stages/benchmark/test_stock_drop_narrative.py -x` | Wave 0 |
| STOCK-04 | Multi-horizon returns computed | unit | `uv run pytest tests/stages/extract/test_multi_horizon_returns.py -x` | Wave 0 |
| STOCK-05 | Pattern detection identifies clusters/arcs | unit | `uv run pytest tests/stages/extract/test_stock_pattern_detection.py -x` | Wave 0 |
| STOCK-06 | Analyst consensus expanded rendering | unit | `uv run pytest tests/stages/render/test_analyst_context.py -x` | Wave 0 |
| DOSSIER-07 | Competitive landscape extracted + rendered | unit+integration | `uv run pytest tests/stages/extract/test_competitive_extraction.py -x` | Wave 0 |
| ALTDATA-01 | ESG risk assessment renders | unit | `uv run pytest tests/stages/render/test_alt_data_context.py::test_esg -x` | Wave 0 |
| ALTDATA-02 | AI-Washing risk assessment renders | unit | `uv run pytest tests/stages/render/test_alt_data_context.py::test_ai_washing -x` | Wave 0 |
| ALTDATA-03 | Tariff/Trade exposure renders | unit | `uv run pytest tests/stages/render/test_alt_data_context.py::test_tariff -x` | Wave 0 |
| ALTDATA-04 | Competitor SCA check renders | unit | `uv run pytest tests/stages/render/test_alt_data_context.py::test_peer_sca -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x --timeout=30 -q -k "stock_catalyst or competitive or alt_data or multi_horizon or pattern_detect"`
- **Per wave merge:** `uv run pytest tests/ --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/extract/test_stock_catalyst.py` -- covers STOCK-01
- [ ] `tests/stages/extract/test_multi_horizon_returns.py` -- covers STOCK-04
- [ ] `tests/stages/extract/test_stock_pattern_detection.py` -- covers STOCK-05
- [ ] `tests/stages/extract/test_competitive_extraction.py` -- covers DOSSIER-07
- [ ] `tests/stages/render/test_alt_data_context.py` -- covers ALTDATA-01 through ALTDATA-04
- [ ] `tests/stages/render/test_stock_catalyst_context.py` -- covers STOCK-02, STOCK-03
- [ ] `tests/stages/render/test_analyst_context.py` -- covers STOCK-06
- [ ] `tests/stages/benchmark/test_stock_drop_narrative.py` -- covers STOCK-03

## Sources

### Primary (HIGH confidence)
- Source code analysis: `src/do_uw/stages/extract/stock_drops.py`, `stock_drop_enrichment.py`, `stock_performance.py` -- existing drop detection, trigger attribution, enrichment pipeline
- Source code analysis: `src/do_uw/models/market_events.py` -- StockDropEvent model (40+ fields), AnalystSentimentProfile, StockDropAnalysis
- Source code analysis: `src/do_uw/models/market.py` -- StockPerformance model (50+ fields), all yfinance-sourced data
- Source code analysis: `src/do_uw/models/dossier.py` -- DossierData with explicit "5.7 deferred to Phase 119" comment
- Source code analysis: `src/do_uw/stages/acquire/clients/market_client.py` -- full yfinance acquisition (recommendations, price targets, upgrades_downgrades, growth_estimates, etc.)
- Source code analysis: `src/do_uw/stages/extract/environment_assessment.py` -- existing ENVR.* signal extraction (esg, geopolitical, cyber, macro)
- Source code analysis: `src/do_uw/brain/output_manifest.yaml` -- deferred dossier_competitive_landscape entry at line 201
- Source code analysis: `src/do_uw/templates/html/sections/market/stock_drops.html.j2` -- current 15-column drop table template
- Source code analysis: Phase 118 dossier extraction/enrichment/context builder/template/wiring pattern

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` -- STOCK-01 through STOCK-06, DOSSIER-07, ALTDATA-01 through ALTDATA-04 requirement definitions
- `.planning/ROADMAP.md` -- Phase 119 success criteria and dependency on Phase 118

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project, no new dependencies
- Architecture: HIGH - follows established Phase 117/118 patterns exactly
- Stock drop enhancement: HIGH - existing infrastructure is comprehensive; additive changes only
- Competitive landscape: MEDIUM - LLM extraction quality depends on 10-K content; peer metrics may be sparse
- Alt data: MEDIUM - leverages existing ENVR.* signals but rendering is new; scope management critical
- Pitfalls: HIGH - documented from extensive codebase analysis

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable internal project patterns)
