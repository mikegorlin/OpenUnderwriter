# Phase 90: Drop Enhancements - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance stock drop analysis with three capabilities: (1) time-decay weighting so recent drops score higher than old ones, (2) per-drop return decomposition showing market/sector/company attribution for each individual drop, and (3) corrective disclosure reverse lookup that searches for 8-K filings and news after unexplained drops. All three affect both display and F2 scoring.

Requirements: STOCK-06, STOCK-08, STOCK-09

</domain>

<decisions>
## Implementation Decisions

### Time-decay curve
- Exponential decay with 6-month half-life: `weight = exp(-ln(2)/180 * days_ago)`
- At 6mo: ~50%, 12mo: ~25%, 18mo: ~12%, 24mo: ~6%
- Show decay weight as a visible column in the drops table (e.g., "0.87" or "87%")
- Drops table re-sorted by decay-weighted severity (magnitude x decay_weight), not raw magnitude
- Decay weight affects F2 (Stock Decline) factor score — each drop's contribution multiplied by its decay weight

### Per-drop return decomposition
- Three inline columns added to drops table: Market, Sector, Company-Specific (consistent with Phase 88 period decomposition display)
- Full period decomposition for multi-day drops (first day open to last day close, not per-day breakdown)
- Drops where market contribution exceeds 50% get a "Market-Driven" badge/flag
- Company-specific percentage weights the drop's contribution to F2 scoring — market-driven drops count less for D&O risk
- Reuse existing `compute_return_decomposition()` from chart_computations.py applied to price windows around each drop

### Corrective disclosure search
- Search window: +1 to +14 days after drop for 8-K filings (existing ±3 day forward lookup stays, this adds the reverse/delayed lookup)
- Web search fallback: Yes — if no 8-K found, search Brave for company + drop date + keywords. Results marked LOW confidence
- Display: Linked badge with lag days (e.g., "8-K +3d" or "News +7d") next to trigger column
- Drops with confirmed corrective disclosure get a 1.5x scoring uplift in F2 — drop + disclosure = stronger SCA trigger signal

### Claude's Discretion
- Exact exponential decay lambda constant (should yield 6-month half-life)
- Web search query templates for corrective disclosure fallback
- Threshold for "Market-Driven" badge (50% market contribution suggested, Claude can adjust)
- How to handle drops where decomposition data is unavailable (missing sector ETF data)
- Disclosure uplift multiplier calibration (1.5x suggested, Claude can adjust based on literature)

</decisions>

<specifics>
## Specific Ideas

- The three scoring adjustments (time-decay, company-specific weighting, disclosure uplift) all modify how drops contribute to F2. They compound: a recent (high decay weight), company-specific (high company %), disclosure-linked (1.5x boost) drop has maximum scoring impact
- Sorting by decay-weighted severity means the "worst drop" from the underwriter's perspective reflects actual current risk, not just historical magnitude

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `chart_computations.compute_return_decomposition()` (lines 260-306): Already decomposes returns into market/sector/company. Reusable per-drop by passing price windows
- `stock_drop_enrichment.enrich_drops_from_8k()` (lines 60-124): Existing forward-looking 8-K search. Extend with reverse lookup function
- `stock_drop_enrichment._find_8k_near_date()` (lines 137-150): Date matching logic, reusable with expanded window

### Established Patterns
- All drop fields are on `StockDropEvent` in `models/market_events.py` — add new fields there
- Context builder `context_builders/market.py` (lines 323-375) formats drops for template — extend for new columns
- SourcedValue pattern used for all drop data with source/confidence tracking

### Integration Points
- `stock_performance.py` line 842-850: Where enrichment is called — add per-drop decomposition + reverse lookup here
- `stages/score/` F2 factor calculation: Where decay weighting + company-specific weighting + disclosure uplift modify drop contributions
- `stock_drops.html.j2`: Template adds decomposition columns, recency column, disclosure badge
- stock_performance.py is already 925 lines — may need splitting (pre-existing 500-line violation)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 90-drop-enhancements*
*Context gathered: 2026-03-09*
