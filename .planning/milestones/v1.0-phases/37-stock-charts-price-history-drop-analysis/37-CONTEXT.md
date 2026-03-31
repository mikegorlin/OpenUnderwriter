# Phase 37: Stock Charts, Price History & Drop Analysis - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Stock performance charts (1Y and 5Y) render in all three output formats (MD, Word, PDF) with annotated 5%+ drop events, sector ETF + S&P 500 comparison overlays, and trigger explanations. Every significant stock drop is explained with source links. Fix the existing price history key mismatch so chart generation actually works. Acquire sector ETF and S&P 500 history for overlay comparison.

</domain>

<decisions>
## Implementation Decisions

### Chart Visual Style
- **Chart type:** Area chart with filled area under price line
- **Price axis:** Dual axis — company actual dollar price on left axis, sector ETF/S&P indexed on right axis
- **Color scheme:** Bloomberg Terminal dark theme — dark background, bright colored lines
- **Reference model:** Bloomberg Terminal GP (graph) function aesthetic
- **Area fill:** Green fill when price is above starting level, red fill when below — clear directional risk signal
- **Stats header:** Key metrics displayed in header bar above chart (current price, 52W H/L, total return, company vs sector return, alpha)
- **Drop annotations:** Red markers/dots on chart at drop dates, PLUS detailed drop table below each chart

### Drop Presentation
- **Full detail per drop event:** Date, drop %, recovery time (trading days to recover), trigger event, company-specific vs market-wide label, source link (8-K URL or news article)
- **Severity tiers:** 5-10% drops shown as yellow/notable, 10%+ drops shown as red/critical — different visual treatment in table and on chart markers
- **Unknown triggers:** Provide best-effort hypothesis using available context (macro events, sector moves, earnings calendar) BUT clearly mark as "Unconfirmed — Requires Investigation"
- **Market-wide events:** Tag drops that correlate with S&P 500/sector drops >3% on same day as "Market-Wide Event" — distinguish systemic from idiosyncratic risk
- **Recovery time:** Include column showing trading days until stock recovered to pre-drop level
- **Event grouping:** Group consecutive daily drops into single events with cumulative drop percentage — prevents table clutter
- **Summary line:** Brief overview before table: "X significant drops in past Y months (N company-specific, M market-wide)"
- **Source links:** Each trigger explanation includes link to source (8-K filing URL, news article) — underwriter can verify

### 5Y Chart Density
- **Condensed:** Weekly data aggregation for 5Y chart to reduce noise
- **Higher threshold:** Only show drops >10% or multi-day cumulative drops >15% on 5Y chart
- **1Y chart:** Full daily data, all 5%+ drops annotated

### Sector ETF Comparison
- **Two overlays:** Both sector ETF (dashed line) AND S&P 500 (dotted line) on same chart as company area fill
- **ETF selection:** Automatic mapping from company SIC/GICS sector to standard sector ETF (XLK for tech, XLF for financials, etc.)
- **Divergence bands:** Shade the gap between company and sector lines when company outperforms/underperforms sector by >10%
- **Performance stats:** Company return, sector return, and alpha (outperformance/underperformance) shown in chart header stats bar

### Output Format
- **Image format:** PNG for all three formats (MD, Word, PDF) — one format, consistent rendering
- **Chart size:** Full page width, ~400px tall — standard institutional report sizing
- **Placement:** Section 2: Market Data — alongside stock stats, short interest, analyst consensus
- **Caching:** Cache chart images keyed by hash of price data — skip regeneration if data unchanged

### Claude's Discretion
- Exact Bloomberg dark theme hex colors (as long as it looks professional and matches Bloomberg aesthetic)
- Chart library choice (matplotlib, plotly, etc.) — pick what generates best static PNG output
- Legend placement and typography within the chart
- How to handle companies where sector ETF doesn't exist (rare edge case)
- Exact divergence band opacity and styling
- Chart DPI/resolution for print quality

</decisions>

<specifics>
## Specific Ideas

- Bloomberg Terminal GP function is the visual reference — dark background, bright lines, professional data density
- Green/red area fill is a powerful visual signal for an underwriter — immediately shows whether the stock has been gaining or losing value
- Dual axis with company dollars on left and indexed comparison on right lets the underwriter see actual price AND relative performance in one view
- Drop grouping into events prevents the table from being a wall of daily entries during volatile periods
- The "Market-Wide Event" tag on drops is critical for D&O underwriting — a drop caused by COVID crash is very different risk than an earnings miss
- Source links on every drop trigger turn this from a summary into a verifiable reference document

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 37-stock-charts-price-history-drop-analysis*
*Context gathered: 2026-02-21*
