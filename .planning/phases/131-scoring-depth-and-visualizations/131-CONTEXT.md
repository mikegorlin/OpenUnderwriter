# Phase 131: Scoring Depth and Visualizations - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the scoring section from a single number into a fully decomposed visual risk narrative. Waterfall chart shows factor-by-factor score buildup. Radar chart shows risk concentration. Probability is decomposed into 7+ named components with calibration labels. Company-specific scenarios show score impact and tier changes. Tornado chart ranks scenario impact.

</domain>

<decisions>
## Implementation Decisions

### Chart Technology
- **D-01:** Mix approach: pure SVG for waterfall and tornado charts (bar charts are simple geometry, crisp, print-friendly). Matplotlib for radar chart (polar coordinates are hard in raw SVG). Follows existing codebase pattern — factor_bars.py and sparklines.py use pure SVG, radar_chart.py uses matplotlib.

### Visual Density
- **D-02:** Dashboard density — charts sit side-by-side where possible (waterfall + radar on one row), factor cards are compact grids, scenarios in a tight table. Maximum information per screen, like the CR report style.

### Probability Decomposition
- **D-03:** Show ALL components with calibration labels. Calibrated components get source citations (NERA, Cornerstone, SCAC data). Uncalibrated components get clear "ESTIMATED" or "UNCALIBRATED" badges. Transparency over false precision.
- **D-04:** 7+ named components: sector base rate, IPO uplift, market cap tier, volatility adjustment, insider selling signal, litigation history, governance quality. Each shows its contribution (additive/subtractive) to the final probability.

### Scenario Analysis
- **D-05:** Company-specific scenarios generated from actual risk profile. If active SCA → "SCA Escalation" scenario, if earnings volatile → "Earnings Miss + Drop", if high insider selling → "Insider Selling Accelerates". 5-7 scenarios per company.
- **D-06:** Each scenario shows: current score, scenario score, tier change (e.g., "70 WRITE → 85 WALK"), and the score delta.

### Voice & Presentation (from Phase 130)
- **D-07:** Formal research report voice. No factor codes (F1-F10) in prose — only in chart labels and tables where they serve as cross-references. No system internals in narrative text.
- **D-08:** Factor cards use the dual-voice pattern: factual data + bulleted D&O commentary per factor.

### Claude's Discretion
- SVG dimensions, color palette, print CSS for charts
- Exact probability component calculations and default values for uncalibrated items
- How to derive scenario score impacts (which factors change, by how much)
- Whether to use existing severity_scenarios.html.j2 or create new template
- Tornado chart orientation (horizontal bars ranked by magnitude)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Chart Infrastructure
- `src/do_uw/stages/render/charts/radar_chart.py` — Existing matplotlib radar chart (reuse/enhance)
- `src/do_uw/stages/render/charts/factor_bars.py` — Pure SVG bar pattern (follow for waterfall/tornado)
- `src/do_uw/stages/render/charts/sparklines.py` — Pure SVG inline chart pattern
- `src/do_uw/stages/render/chart_registry.py` — Chart registration and dispatch
- `src/do_uw/stages/render/chart_helpers.py` — save_chart_to_bytes, save_chart_to_svg utilities

### Scoring Templates (enhance, don't replace)
- `src/do_uw/templates/html/sections/scoring/ten_factor_scoring.html.j2` — Current factor display
- `src/do_uw/templates/html/sections/scoring/factor_detail.html.j2` — Factor detail cards
- `src/do_uw/templates/html/sections/scoring/claim_probability.html.j2` — Current probability display
- `src/do_uw/templates/html/sections/scoring/severity_scenarios.html.j2` — Current scenario display
- `src/do_uw/templates/html/sections/scoring/tier_classification.html.j2` — Tier display

### Scoring Models
- `src/do_uw/models/scoring.py` — FactorScore, TierClassification, ClaimProbability models
- `src/do_uw/stages/render/context_builders/scoring.py` — Scoring context builder (extract_scoring)
- `src/do_uw/stages/render/context_builders/scorecard_context.py` — Scorecard context

### Design Reference
- `memory/reference-page0-cr-report.md` — CR report first page design (Phase 132 target, but scoring section should be compatible)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `radar_chart.py`: matplotlib-based, already generates 10-factor radar — enhance with threshold rings
- `factor_bars.py`: pure SVG horizontal bars — pattern for waterfall and tornado
- `sparklines.py`: pure SVG inline charts — pattern for small probability component bars
- `claim_probability.html.j2`: shows band/range — extend with component decomposition
- `severity_scenarios.html.j2`: shows scenarios — extend with score impact and tier change
- `factor_detail.html.j2`: shows per-factor detail — extend with "Why this score" commentary

### Established Patterns
- Charts return base64 PNG or inline SVG strings via chart_helpers
- Context builders provide chart data to templates via assembly_registry
- Scoring context already provides factor_scores, tier, claim_probability
- Commentary engine (Phase 130) can generate per-factor narratives

### Integration Points
- `scorecard_context.py` — add waterfall data, scenario calculations
- `scoring.html.j2` — add waterfall + radar row, probability decomposition, scenario table + tornado
- New files: `waterfall_chart.py`, `tornado_chart.py`, `probability_decomposition.py`

</code_context>

<specifics>
## Specific Ideas

- Waterfall chart: horizontal bars, each factor's contribution, tier threshold lines as horizontal dashed lines
- Radar chart: existing radar enhanced with optional threshold rings showing tier boundaries
- Dashboard layout: waterfall and radar side-by-side on one row, factor cards below, then probability, then scenarios + tornado
- Tornado chart: horizontal bars sorted by absolute impact magnitude, current score line in center
- Each probability component should be a row: name, value, direction (↑/↓), calibration badge, source

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 131-scoring-depth-and-visualizations*
*Context gathered: 2026-03-23*
