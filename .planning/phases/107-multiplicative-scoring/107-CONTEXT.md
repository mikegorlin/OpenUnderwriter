# Phase 107: Multiplicative Scoring - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the H/A/E multiplicative scoring model that captures interaction effects between Host, Agent, and Environment risk dimensions. Produces tier recommendations, CRF discordance overrides, and shadow calibration comparison. Consumes signal results from Phase 104 infrastructure and design from Phase 106 research.

</domain>

<decisions>
## Implementation Decisions

### Scoring Lens Architecture
- Scoring models are **pluggable lenses**, not a monolithic score. Same architecture as Phase 109 pattern engines.
- H/A/E multiplicative model is the first new lens. Legacy 10-factor additive is wrapped as a second lens.
- All lenses consume the same signal_results dict and produce a tier recommendation.
- Future lenses can be added without rearchitecting.
- **Consensus view** shown in worksheet: "Based on N models, this risk profiles as [TIER]" with individual lens breakdowns below.
- Infrastructure: shared input/output contract for scoring lenses.

### Model Transition
- **New H/A/E model drives the worksheet immediately** -- not shadow-only.
- Legacy 10-factor runs alongside as a comparison lens, never drives output.
- Legacy kept permanently for ongoing comparison (not deleted after calibration).
- When model is wrong: flag disagreement for weight tuning AND rely on UW override for immediate accuracy. Model improves iteratively, UW is never blocked.

### Worksheet Display
- **Tier badge + 3 composites** (H:0.35 A:0.62 E:0.28) in the recommendation header. No radar chart in Phase 107.
- All 6 recommendation outputs **always visible** (pricing, layer comfort, terms, monitoring, referral, communication) -- not collapsed.
- Consensus view at top, individual lens details below.
- Legacy score visible as a secondary lens, clearly labeled.

### Calibration Approach
- **30-40 tickers** selected by Claude for full sector diversity.
- Both eras: recent active cases (2023-2025) AND historical landmarks with known outcomes.
- Full sector diversity (not just Liberty-heavy sectors).
- **Interactive HTML calibration report** where:
  1. System shows ticker + model recommendation
  2. UW provides their tier assessment with rationale
  3. System asks follow-up questions (e.g., "Is that because of insider selling or thin tower?")
  4. Rationale stored for weight adjustment
- This is a calibration session, not a static report.

### Tier Thresholds
- **Start with design doc thresholds**, adjust from calibration feedback.
- **Fixed thresholds** -- not market-cycle adjusted. A company at P=0.12 is ELEVATED regardless of hard/soft market.
- Expected distribution is **right-skewed** -- most public companies are PREFERRED or STANDARD.
- Multiplicative floor (0.05) to be **calibrated empirically** -- start with 0.05, adjust based on distribution.

### CRF Veto Behavior
- CRF vetoes are **time-aware and claim-status-aware**, not binary.
  - Event just happened (restatement, enforcement, material news) -> HIGH_RISK or PROHIBITED
  - Claim already filed -> exposure is quantifiable, risk changes character
  - Event old + DDL passed -> veto decays
- Add explicit **claim_status** derived field with full claims-made context:
  - NO_CLAIM / CLAIM_FILED / CLAIM_RESOLVED
  - Class period defined (start/end dates)
  - Whether current policy period overlaps class period
  - Whether prior acts coverage applies
- **Decay curves need more thought** -- implement the CRF structure with time/claim-status inputs in Phase 107, but exact decay parameters are calibration work.
- Material restatement (recent) should map to HIGH_RISK, not just ELEVATED.
- 5-tier model: PREFERRED / STANDARD / ELEVATED / HIGH_RISK / PROHIBITED (updated from 6-tier).
- All outputs are **recommendations, not decisions** -- UW has final authority.

### Claude's Discretion
- Code organization within stages/score/ (new files, function decomposition)
- Exact Pydantic model extensions for ScoringResult
- Shadow comparison table column layout
- How to wrap legacy 10-factor as a lens (adapter pattern, etc.)
- Calibration ticker selection criteria within the "diverse set" guidance

</decisions>

<specifics>
## Specific Ideas

- "Why not keep [legacy] as legacy 10 point or something and display maybe?" -- Multiple scoring models as parallel lenses, like pattern engines. Consensus view synthesizes.
- CRF decay is fundamentally about DDL, claims-made policy mechanics, and whether the claim is already in. A restatement from 5 years ago with DDL expired is not the same as one from last quarter.
- Calibration should be conversational: system proposes, UW responds with rationale, system asks follow-ups, rationale feeds back into weight adjustment.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `stages/score/__init__.py` (481 lines): 17-step pipeline orchestrator -- new H/A/E scoring inserts as additional step
- `stages/score/tier_classification.py` (253 lines): Existing tier mapping -- extend with `classify_tier_from_hae()`
- `stages/score/red_flag_gates.py` (529 lines): CRF evaluation -- extend with time-aware, claim-status-aware logic
- `stages/render/context_builders/_signal_consumer.py` (193 lines): SignalResultView with rap_class, rap_subcategory -- primary data source for H/A/E computation
- `stages/render/context_builders/_signal_fallback.py` (105 lines): Graceful degradation for missing signals
- `models/scoring.py`: ScoringResult Pydantic model -- extend with host_composite, agent_composite, environment_composite, hae_product, hae_tier

### Established Patterns
- Score stage produces ScoringResult -> stored on state.scoring -> consumed by context builders
- Signal results dict[signal_id] -> dict[status, value, ...] -> SignalResultView extraction
- All score/ modules < 530 lines, clean separation of concerns
- Brain signal cache: module-level lazy singleton for RAP/mechanism lookup
- SKIPPED signals excluded from computation (null, not 0)

### Integration Points
- `stages/score/__init__.py` ScoreStage.run(): Insert new step after tier classification
- `state.analysis.signal_results`: Input data source (all signal evaluations)
- `brain/framework/scoring_model_design.yaml`: Subcategory weights, tier mapping, CRF catalog
- `brain/framework/decision_framework.yaml`: 5-tier recommendation outputs
- `brain/framework/rap_signal_mapping.yaml`: 514 signals mapped to H/A/E subcategories

</code_context>

<deferred>
## Deferred Ideas

- Market-cycle adjusted thresholds -- revisit if fixed thresholds prove too harsh/lenient in different market conditions
- CRF decay curves (exact parameters) -- implement structure now, calibrate parameters over time
- Additional scoring lenses beyond H/A/E and legacy -- future phases
- Radar chart visualization of H/A/E composites -- Phase 112 (Worksheet Restructure)

</deferred>

---

*Phase: 107-multiplicative-scoring*
*Context gathered: 2026-03-15*
