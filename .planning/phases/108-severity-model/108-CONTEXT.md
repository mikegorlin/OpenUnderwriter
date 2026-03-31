# Phase 108: Severity Model - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement damages estimation, settlement prediction, severity amplifiers, and P x S expected loss computation so the worksheet shows probability and severity independently. Produces per-layer severity estimates with Liberty-specific erosion probability, dual ABC/Side A models, and a dedicated severity section in the worksheet. Design blueprint is `severity_model_design.yaml` from Phase 106.

</domain>

<decisions>
## Implementation Decisions

### Legacy Model Relationship
- **Parallel lens pattern** (mirroring Phase 107 scoring): Define a `SeverityLens` protocol. New severity model is primary lens driving worksheet output. Legacy DDL model (`settlement_prediction.py`) wrapped as second lens for comparison.
- Legacy kept permanently alongside new model (not deleted after calibration), same as legacy 10-factor scoring.
- **New model drives output immediately** -- not shadow-only. Legacy DDL shown as comparison lens below primary.
- **Point estimate + amplifiers** (no percentile scenarios). Scenario dimensionality handled via drop-level x allegation-type grid instead.

### Settlement Regression
- **Published coefficients** from Cornerstone/NERA/Bajaj research (already in `severity_model_design.yaml`). No model fitting from training data in v7.0 -- the published research did the fitting on thousands of cases.
- **Always estimate** (prospective severity). Even with no active claim, compute "if a claim were filed today, what would it settle for?" This is the S in P x S.
- **Scenario-based severity**: Compute at multiple drop levels:
  - Worst actual drop (from stock analysis engine, Phases 89-90)
  - Sector median drop
  - Hypothetical catastrophic drop (~50%)
- **All plausible allegation types shown**: Settlement estimate computed for each allegation type consistent with active signals (e.g., "If restatement: $X. If guidance miss only: $Y"). Signal-inferred primary allegation type is highlighted as most-likely.
- P x S chart shows **primary dot + range bar** (most-likely scenario as dot, min-to-max across scenarios as range bar).

### P x S Display
- **Total market severity** on the chart (not Liberty-adjusted). Liberty attachment context shown elsewhere.
- **Single-account only** for Phase 108. Multi-account portfolio view deferred to Phase 112 (Worksheet Restructure).
- **Dedicated severity section** in the worksheet: damages breakdown, amplifier table, P x S chart, scenario table, expected loss, layer erosion.
- Zone backgrounds from design doc: GREEN/YELLOW/ORANGE/RED with calibration_required flag.

### Amplifier Trigger Logic
- **Auto-fire from signal results**: If ANY `signal_id` in the amplifier's list is TRIGGERED/STRONG/CRITICAL, the amplifier fires. Uses `SignalResultView` from Phase 104 consumer infrastructure.
- **Amplifier combination**: Claude's discretion -- multiplicative with cap, additive excess, or hybrid. Pick based on actuarial reasoning.
- **Skip silently** when trigger data unavailable: amplifier doesn't fire, multiplier = 1.0. No noise in main output.
- **Main section: fired amplifiers only** with explanations (the "answers"). **Appendix: full table** of all 11 amplifiers with fired/not-fired/not-evaluated status (the "show your work"). Worksheet is the decision record -- main body is answers + explanations, appendix shows all the work.

### Layer Erosion Math
- **Fitted log-normal distribution, conditional on allegation type**: P(settlement > attachment | allegation_type) with separate distribution parameters per allegation type. Restatement cases have very different severity distributions than guidance-miss cases.
- **Explicit display**: Layer penetration probability shown as a clear metric in the severity section ("Layer penetration: 32%"). One of the most decision-relevant numbers for an excess underwriter.
- **Attachment as CLI parameter** (--attachment): Always configurable, no dependency on uw_db. Useful for quoting new accounts not yet in the database.

### Side A vs ABC Severity
- **Full dual model**: Separate severity distributions for ABC and Side A with different amplifier weights, allegation type modifiers, and explicit DIC/bankruptcy scenario modeling.
- **Tower-aware severity**: Side A excess of ABC has fundamentally different exposure than Side A only.
  - ABC layer: erosion = P(settlement > ABC attachment)
  - Side A excess of ABC: erosion = P(settlement > total ABC tower + Side A attachment) -- essentially catastrophe-only
  - Side A only: DIC-scenario weighted, no entity coverage below
- **DIC probability is signal-driven**: Use financial distress signals (Altman Z-score, liquidity, debt maturity, going concern) to estimate probability of entity coverage being unavailable. If distress signals are HIGH, DIC scenario gets higher weight.
- **Per-layer severity**: Each Liberty layer gets its own severity estimate based on its position in the tower. ABC at $25M xs $25M has different severity than Side A at $10M xs $100M. The P x S chart could show each layer as a separate point.

### Calibration
- **Historical settlement validation** against ~50-100 cases from Cornerstone annual settlement summaries. Check if model estimates are in the right ballpark for known outcomes.
- **Persistent HTML calibration report** showing model estimate vs actual settlement for each case, with error metrics (median absolute error, R-squared, bias). Lives in output/ for ongoing reference. Can be re-run as model evolves.
- No interactive UW calibration for severity in v7.0 (unlike Phase 107 scoring calibration). Trust published coefficients, validate against outcomes.

### Defense Costs
- **Both shown**: Severity = indemnity-only for P x S matrix computation. Total loss (indemnity + defense costs) shown as a separate metric.
- **Hybrid estimation**: Case-characteristic-adjusted percentages when data is available (multi-defendant +5%, government investigation +5%, long class period +5%), falling back to fixed percentage tiers by market cap (15% large cap, 20% mid-cap, 25% small-cap/complex) when data is sparse.
- Defense costs are inherently imprecise -- model should be honest about uncertainty.

### Claude's Discretion
- Amplifier combination method (multiplicative with cap vs additive excess vs hybrid)
- Code organization within stages/score/ (new files, function decomposition)
- Exact Pydantic model extensions for severity results on AnalysisState
- Defense cost tier breakpoints and case-characteristic adjustment values
- Chart rendering details (matplotlib styles, axis formatting, annotation placement)
- Log-normal distribution parameter estimation methodology

</decisions>

<specifics>
## Specific Ideas

- "Think of the main worksheet as answers to the homework with explanations, and the appendix is where you show your work" -- amplifiers and all severity calculations should follow this principle
- Side A often builds on top of ABC tower (e.g., $100M ABC, Side A attaching excess of that). The severity model must be tower-structure-aware, not just product-aware.
- Layer penetration probability is one of the most decision-relevant metrics for excess underwriters -- make it prominent
- Defense costs actually erode the tower, so total loss (indemnity + defense) matters for layer erosion even though the P x S matrix uses indemnity-only severity
- Published coefficients from Cornerstone/NERA research have been fitted on thousands of cases -- more reliable than anything we could fit on available data

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `severity_model.py` (legacy): Tier-based loss severity at percentiles -- becomes legacy severity lens
- `settlement_prediction.py` (legacy): DDL-based model (market_cap x max_drop) with case characteristic multipliers -- significant overlap with new design, wrappable as legacy lens
- `case_characteristics.py`: Detects accounting fraud, insider selling, SEC investigation, etc. -- direct input to allegation type classification and amplifier trigger evaluation
- `SeverityAmplifier` Pydantic schema in `brain_schema.py`: Already defined (id, name, multiplier 1.0-5.0, signal_ids, rap_class, epistemology)
- `severity_model_design.yaml`: Complete design blueprint with 11 amplifiers, 12 regression features, P x S zones
- `scoring_lens.py` (Phase 107): ScoringLens Protocol pattern to mirror for SeverityLens
- `_signal_consumer.py` (Phase 104): SignalResultView with rap_class -- primary data source for amplifier trigger evaluation
- `hae_scoring.py` (Phase 107): P composite available on `ScoringResult.hae_result` -- input to P x S computation
- `chart_styles.yaml` (Phase 105): Chart style registry for consistent P x S chart rendering

### Established Patterns
- ScoringLens Protocol: pluggable lens contract with `compute()` returning typed result -- mirror for SeverityLens
- Signal results dict[signal_id] -> SignalResultView extraction via `_signal_consumer.py`
- Design YAML as implementation blueprint: `severity_model_design.yaml` specifies all formulas, features, amplifiers
- Legacy adapter pattern: `legacy_lens.py` wraps old scoring as a lens -- same pattern for wrapping old severity
- Score stage orchestrator: `stages/score/__init__.py` runs all scoring steps sequentially -- add severity step

### Integration Points
- `stages/score/__init__.py`: Add severity computation step after H/A/E scoring (P is available)
- `state.scoring`: Extend with severity result fields (SeverityResult Pydantic model)
- `brain/framework/severity_model_design.yaml`: Source of amplifier catalog, regression coefficients, zone definitions
- `brain/brain_schema.py`: SeverityAmplifier schema already defined
- `stages/render/context_builders/`: New severity context builder for dedicated worksheet section
- `templates/html/sections/`: New severity section template
- CLI: Add --attachment parameter for layer erosion computation

</code_context>

<deferred>
## Deferred Ideas

- Multi-account portfolio P x S view (plotting many accounts) -- Phase 112 (Worksheet Restructure)
- Liberty attachment auto-lookup from uw_db -- future integration
- Market-cycle severity adjustments (hard market vs soft market) -- future calibration
- CI test encoding of calibration thresholds (model must be within 2x of actual for >70% of cases) -- Phase 113
- Radar chart showing H/A/E composites alongside P x S -- Phase 112
- Interactive UW calibration for severity (like Phase 107 scoring) -- future milestone

</deferred>

---

*Phase: 108-severity-model*
*Context gathered: 2026-03-15*
