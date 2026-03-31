# Phase 133: Stock and Market Intelligence - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Enrich every significant stock event with causation analysis, earnings reaction patterns, analyst consensus shifts, volume anomalies, and return correlation metrics. The underwriter should be able to assess loss causation defense strength from the stock/market section alone. This phase focuses on better extraction and presentation of EXISTING data sources (primarily yfinance) -- no new API dependencies.
</domain>

<decisions>
## Implementation Decisions

### Drop Attribution (STOCK-01, STOCK-02, STOCK-03)
- **D-01:** Full event card per >10% drop: date, magnitude, COMPANY/MARKET/SECTOR percentage split, catalyst (from 8-K/news), recovery days, and one-line D&O litigation theory mapping (e.g., "Pattern consistent with Section 10b-5 class period anchor")
- **D-02:** Multi-day consecutive drops consolidated into single events (e.g., -5% Mon + -8% Tue + -3% Wed = one event -15.2% over 3 days, with per-day breakdown available). Prevents clutter from "slow bleed" events.
- **D-03:** Existing infrastructure handles most of this: `stock_drop_decomposition.py` already splits market/sector/company, `StockDropEvent` model has sector_return_pct, is_company_specific, abnormal_return, trigger_category, recovery_days

### Earnings Reaction (STOCK-04, STOCK-05)
- **D-04:** Full reaction analysis table per quarter: date, EPS estimate vs actual, beat/miss flag, revenue estimate vs actual, day-of return, next-day return, 1-week return. Summary row with beat rate, avg reaction on miss
- **D-05:** Earnings trust assessment as pattern narrative after the table -- e.g., "Company beat 7 of 8 quarters but stock sold off on 3 of 4 beats, suggesting market distrust of earnings quality." Connects to D&O: markets ignoring beats = potential misrepresentation narrative
- **D-06:** Fix the todo "earnings guidance signals conflate analyst consensus with company-issued guidance" -- clearly separate analyst estimates from company-issued guidance in data model and display

### Analyst Consensus (STOCK-06)
- **D-07:** Revision trend table: rating breakdown (Buy/Hold/Sell count), price target range (low/mean/high), plus 30d and 90d EPS revision direction (up/flat/down). Shows whether "the Street" is getting more or less bullish. yfinance provides all of this.

### Volume Anomalies (STOCK-07)
- **D-08:** Full event cross-reference: days with volume >2x 20-day average, cross-referenced with 8-K filings (by date) and news articles. Show: date, volume multiple, catalyst if found, event type. Folds in the todo "volume spike detection and event correlation."
- **D-09:** Existing `volume_spikes.py` detects threshold crossings; this phase adds the event correlation layer and tabular display

### Return Correlation (STOCK-08)
- **D-10:** Dedicated metrics card: correlation vs sector ETF, vs SPY, R-squared, and idiosyncratic risk %. `compute_idiosyncratic_vol()` and `compute_return_decomposition()` already calculate this -- wire to display. Key for loss causation defense assessment.

### Data Source Strategy
- **D-11:** Optimize existing sources first (yfinance primary). No new API dependencies. Add new sources only if specific gaps found during implementation.
- **D-12:** Surface hidden state data that's collected but not displayed (e.g., recovery_days, abnormal_return_t_stat, market_model_beta are populated but may not be visible in worksheet)
- **D-13:** Also improve how currently-displayed market data is organized and presented -- not just adding new data, but making existing data more useful

### Claude's Discretion
- Exact layout/CSS for drop event cards, earnings table, analyst table, volume table, correlation card
- How to consolidate multi-day drops algorithmically (gap tolerance, minimum cumulative threshold)
- Which state fields are "hidden" vs already displayed (audit during implementation)
- Where to place new displays within the existing market section structure

### Folded Todos
- "Earnings guidance signals conflate analyst consensus with company-issued guidance" -- fix as part of D-06
- "Volume spike detection and event correlation" -- implement as part of D-08/D-09

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Models
- `src/do_uw/models/market_events.py` -- StockDropEvent (with decomposition fields), EarningsQuarterRecord, EarningsGuidanceAnalysis, AnalystSentimentProfile
- `src/do_uw/models/market.py` -- MarketSignals, volume_anomaly_days field

### Existing Analysis Code
- `src/do_uw/stages/extract/stock_drop_decomposition.py` -- decompose_drop() and decompose_drops() functions
- `src/do_uw/stages/extract/volume_spikes.py` -- volume spike detection (>2x threshold)
- `src/do_uw/stages/render/charts/chart_computations.py` -- compute_return_decomposition(), compute_idiosyncratic_vol()
- `src/do_uw/stages/extract/stock_performance.py` -- _compute_decomposition_and_mdd()

### Rendering Infrastructure
- `src/do_uw/stages/render/context_builders/market.py` -- main market context builder
- `src/do_uw/stages/render/context_builders/_market_display.py` -- drop events, earnings guidance, insider data builders
- `src/do_uw/stages/render/context_builders/market_evaluative.py` -- signal-derived market evaluations
- `src/do_uw/stages/render/context_builders/_market_acquired_data.py` -- earnings history, recommendations, upgrades/downgrades
- `src/do_uw/templates/html/sections/market/` -- all market sub-templates
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` -- stock charts with return decomposition
- `src/do_uw/stages/render/charts/stock_chart_overlays.py` -- volume spike overlays (red bars)
- `src/do_uw/stages/render/charts/drop_analysis_chart.py` -- drop analysis visualization

### Requirements
- `.planning/REQUIREMENTS.md` -- STOCK-01 through STOCK-08

### Prior Phase Context
- `.planning/phases/123-market-condensation/123-CONTEXT.md` -- market section condensed to top 10/5 with audit overflow

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StockDropEvent` model already has 20+ fields including decomposition, abnormal returns, trigger category, recovery days -- many may not be rendered
- `compute_return_decomposition()` returns market/sector/company split -- already called for 1Y and 5Y in stock charts template
- `compute_idiosyncratic_vol()` returns R-squared and idiosyncratic risk % -- exists but display status unclear
- `volume_spikes.py` detects >2x days -- overlays exist on stock chart but no tabular display
- `EarningsQuarterRecord` has stock_reaction_pct but only day-of -- need next-day and 1-week windows
- Card macro system from Phase 132 (20 Jinja2 macros, 12 chart types) available for new displays

### Established Patterns
- Context builders produce template-ready dicts consumed by both HTML and Word renderers
- Dual-voice pattern (Phase 130): factual summary + underwriting commentary per section
- Signal-derived evaluations flow through `market_evaluative.py`
- Phase 123 condensation: main body shows top N, overflow to audit trail

### Integration Points
- Market section template (`sections/market/`) for new displays
- Beta report mini-cards (Phase 132) may need stock intelligence data
- Scoring factors F2 (Stock Decline) and F3 (Earnings Volatility) already consume this data

</code_context>

<specifics>
## Specific Ideas

- User directive: "Ensure to optimize all info that is there" -- audit every state field in market models, surface anything collected but not displayed
- Both surface hidden data AND improve how visible data is organized
- Every drop event needs a D&O litigation theory connection (not just raw numbers)
- Earnings trust narrative should connect market reaction patterns to potential misrepresentation theories

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- "Executive Brief narrative boilerplate overhaul" (score: 0.5) -- render-area todo, not specific to stock/market intelligence. Belongs in a future rendering quality pass.

None other -- discussion stayed within phase scope.

</deferred>

---

*Phase: 133-stock-and-market-intelligence*
*Context gathered: 2026-03-26*
