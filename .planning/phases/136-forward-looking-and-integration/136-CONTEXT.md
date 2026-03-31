# Phase 136: Forward-Looking and Integration - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning
**Mode:** Auto-selected (all gray areas, recommended defaults)

<domain>
## Phase Boundary

The worksheet looks forward with company-specific scenarios, a key dates calendar, management credibility assessment, and short-seller awareness. Plus cross-ticker validation ensures all v10.0 features (Phases 128-135) work across the test portfolio (AAPL, RPM, V) without regressions.

Two distinct workstreams: (1) forward-looking analytical sections, (2) cross-ticker integration validation.

</domain>

<decisions>
## Implementation Decisions

### Forward Scenarios (FWD-01)
- **D-01:** Reuse existing `scenario_generator.py` which already generates company-specific score-impact scenarios. Extend to include probability, severity, and explicit catalyst linkage (not generic templates).
- **D-02:** Each scenario: Name | Probability (HIGH/MEDIUM/LOW) | Severity ($) | Score Impact (+/-) | Catalyst (company-specific event). Scenarios derived from scoring factors + signal results, not hardcoded.
- **D-03:** Display as cards with color-coded probability badges, not a flat table. Progressive disclosure — summary visible, detail expandable.

### Key Dates Calendar (FWD-02)
- **D-04:** Calendar data extracted from: yfinance calendar (next earnings), DEF 14A (annual meeting), SEC filings (IPO milestones if recent IPO), 10-K risk factors (regulatory deadlines, contract expirations). All already in acquired_data or extracted state.
- **D-05:** Display as a timeline/list sorted by date. Each entry: Date | Event | Source | D&O Relevance. Color code by urgency (within 30d = red, 30-90d = amber, >90d = gray).
- **D-06:** Include monitoring triggers — dates that should trigger re-underwriting (earnings, annual meeting, lockup expiry for IPOs).

### Management Credibility (FWD-03)
- **D-07:** Reuse earnings guidance data from Phase 133 (`build_earnings_trust()` already computes beat/miss patterns). Extend to show quarter-by-quarter table: Quarter | Guidance | Actual | Delta | Magnitude | Cumulative Pattern.
- **D-08:** Credibility assessment: "Consistent Beater" (>75% beat rate, small magnitude), "Sandbagging" (always beats by large margin), "Unreliable" (>25% miss rate), "Deteriorating" (recent misses after beats). Data-driven from existing earnings_guidance quarters.

### Short-Seller Monitoring (FWD-04, FWD-05)
- **D-09:** Check for short-seller reports from named firms: Citron Research, Hindenburg Research, Spruce Point Capital, Muddy Waters Research, Kerrisdale Capital. Use existing web search results from acquire stage (already searches for company + risk terms).
- **D-10:** Short interest trend from existing `state.extracted.market.stock` — already has shares_short, short_pct, short trend data. Extend display to show 6-month trend direction with "conviction" label: Rising = Bears gaining conviction, Stable = Established position, Declining = Bears losing conviction.
- **D-11:** Display: named firm reports (if any) as alert cards, short interest trend as a mini-chart or sparkline with conviction badge.

### Cross-Ticker Validation (Success Criterion 5)
- **D-12:** Run pipeline on AAPL, RPM, V. Compare output section-by-section against golden baselines (captured in Phase 128). No regressions = features render for all three without crashes or empty sections.
- **D-13:** Use existing `scripts/qa_compare.py` for cross-ticker QA. Extend if needed to cover new Phase 133-135 sections.
- **D-14:** Validation is a test/verification task, not a new feature — execute after all forward-looking features are implemented.

### Claude's Discretion
- Template layout for forward scenarios (cards vs table vs mixed)
- Key dates calendar visual format (timeline vs list)
- Short interest trend visualization approach
- Cross-ticker QA script enhancements

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Forward-Looking Infrastructure
- `src/do_uw/stages/render/context_builders/scenario_generator.py` — Existing scenario generator
- `src/do_uw/stages/render/context_builders/credibility_context.py` — Credibility context builder
- `src/do_uw/stages/render/context_builders/forward_risk_map.py` — Forward risk map

### Phase 133 Earnings Data (reuse for FWD-03)
- `src/do_uw/stages/render/context_builders/_market_acquired_data.py` — build_earnings_trust() with beat/miss patterns
- `src/do_uw/templates/html/sections/market/earnings_reaction.html.j2` — Earnings reaction template

### Market Data (reuse for FWD-04/05)
- `src/do_uw/stages/extract/insider_trading.py` — Short interest data paths
- `src/do_uw/templates/html/sections/market/short_interest.html.j2` — Existing short interest display

### Cross-Ticker QA
- `scripts/qa_compare.py` — Cross-ticker validation script
- `scripts/qa_beta_report.py` — QA checks on rendered output

### Templates
- `src/do_uw/templates/html/sections/beta_report.html.j2` — Active rendering path

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scenario_generator.py`: Already generates score-impact scenarios — extend, don't rebuild
- `credibility_context.py`: Existing credibility context builder
- `build_earnings_trust()`: Beat/miss patterns, consecutive miss count, beat sell-off detection
- `forward_risk_map.py`: Forward risk visualization
- Short interest data already in `state.extracted.market.stock` (shares_short, short_pct, short_trend_6m)
- yfinance calendar data in `state.acquired_data.market_data["calendar"]`

### Established Patterns
- Phase 134/135 pattern: models → extraction → context builder → template → beta_report wiring
- `safe_float()` for all numeric values
- `{% if data %}` guards on every template
- Beta report hardcoded includes

### Integration Points
- Forward-looking section goes after governance in beta_report.html.j2
- Key dates from multiple existing state paths (calendar, filings, earnings)
- Cross-ticker validation as final verification step

</code_context>

<specifics>
## Specific Ideas

- Forward scenarios answer "what could change the risk profile in the next 12 months?"
- Key dates calendar answers "when does the underwriter need to pay attention?"
- Management credibility answers "can we trust what management says?"
- Short-seller monitoring answers "are sophisticated bears betting against this company?"
- Cross-ticker validation proves the entire v10.0 milestone works end-to-end

</specifics>

<deferred>
## Deferred Ideas

- Phase 132 (Page-0 Decision Dashboard) still needs discuss/plan/execute — separate from this phase
- Real-time monitoring/alerting (would need a separate service, not pipeline)

</deferred>

---

*Phase: 136-forward-looking-and-integration*
*Context gathered: 2026-03-27 via auto mode*
