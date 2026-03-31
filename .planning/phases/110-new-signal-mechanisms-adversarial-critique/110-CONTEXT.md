# Phase 110: New Signal Mechanisms + Adversarial Critique - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the signal evaluation framework with four new mechanism types (conjunction, absence, contextual, conditional deep-dive) and add an adversarial second-pass that challenges conclusions without modifying scores. New mechanisms produce new YAML-defined signals evaluated in the pipeline. Adversarial critique runs after scoring as a new ScoreStage step, producing caveats displayed inline and in a dedicated Devil's Advocate worksheet section.

</domain>

<decisions>
## Implementation Decisions

### Conjunction Rules Design
- **Separate from Phase 109 Conjunction Scan.** Phase 109's engine detects statistical co-fire patterns post-evaluation. Phase 110 conjunction rules are curated YAML-defined rules for known dangerous D&O combinations. Both fire independently -- Phase 109 finds unexpected patterns, Phase 110 encodes domain wisdom.
- **New YAML signals with mechanism=conjunction.** Each conjunction rule is a distinct signal in brain/signals/ with `evaluation.mechanism: conjunction`. Produces its own SignalResult in signal_results dict. Clear audit trail, consistent with brain-as-source-of-truth architecture.
- **Start with 6-10 curated conjunction rules** covering the most dangerous D&O combinations:
  - Compensation + Performance: CEO/exec comp up + company performance down + no clawback
  - Governance + Events: Weak governance + adverse event (restatement, enforcement, exec departure)
  - Insider selling + material news gap
  - Related-party + audit issues
  - Rapid growth + margin compression + guidance history
  - Additional high-impact combinations as research identifies
- **Elevation floor (like archetypes).** Each conjunction rule has a `recommendation_floor`. If conjunction fires and floor > current tier, tier is raised. Consistent with Phase 109 archetype behavior and CRF veto logic -- raises only, never lowers.
- **Pipeline placement: Claude's discretion.** Evaluate during ANALYZE (as signals) or post-evaluation in SCORE (as a new step). Choose based on best architectural fit given that conjunction rules need other signal results as input.

### Absence Detection
- **Triple-source expectation model:**
  1. **Company-profile-driven rules**: Infer expected disclosures from company characteristics. E.g., known subsidiaries → expect related-party disclosure. Stock compensation → expect stock comp tables. >$1B revenue → expect segment reporting.
  2. **Peer-comparison-driven**: If 80%+ of sector peers disclose something and this company doesn't, flag absence. Works for industry-standard disclosures (ESG for large cap, cyber risk for tech).
  3. **Curated 'always expected' list**: Disclosures required for all public companies (risk factors, internal controls, going concern assessment).
- **Separate signals with mechanism=absence.** Each absence rule produces its own SignalResult (e.g., `absence.related_party_disclosure`). Not modifications to existing signals.
- **20-30 comprehensive absence rules** covering all major disclosure categories.

### Contextual Reframing
- **Full context matrix** for company classification:
  - Lifecycle stage: pre-revenue, post-IPO (<3yr), growth, mature, distressed
  - Sector: financial, tech, healthcare, industrial, etc.
  - Size: small-cap, mid-cap, large-cap, mega-cap
  - Product type: Side A vs ABC (from CLI --product parameter)
  - Tower position: primary vs high excess (from CLI --attachment parameter)
- **Separate signals with mechanism=contextual.** Each contextual reframing rule is a distinct signal that evaluates the same underlying data but through a company-type lens. E.g., `contextual.ceo_comp_lifecycle` evaluates CEO comp relative to lifecycle-appropriate benchmarks.
- **20-30 comprehensive contextual reframing rules** covering every signal category where interpretation varies meaningfully by company type. Start comprehensive, not minimal.

### Conditional Deep-Dive Triggers
- **8-12 comprehensive triggers** covering all major D&O peril categories. Every H/A/E dimension has at least 2 trigger conditions:
  - Governance weak + exec departure → full board composition deep-dive
  - Restatement + auditor change → financial controls investigation
  - Financial distress signals + insider selling → bankruptcy/DIC scenario analysis
  - Regulatory action + new material litigation → enforcement escalation check
  - Rapid M&A + integration red flags → acquisition risk deep-dive
  - Plus 3-7 additional combinations across H/A/E dimensions
- **Both: auto signals + UW investigation flag.** Trigger fires additional automated signals AND flags the UW for manual investigation. System does what it can automatically (board tenure, audit committee, proxy data), tells UW what it couldn't find.
- **Triggers CAN request additional acquisition.** When deep-dive triggers fire, the pipeline can loop back for targeted additional data. This makes some runs longer based on risk profile. Architecture: Claude's discretion on implementation (ANALYZE→ACQUIRE loop with max 1 iteration, or deferred queue, or hybrid).
- **Formalized in YAML** with trigger conditions, additional signals to evaluate, and UW investigation prompts.

### Adversarial Critique Engine
- **Rule-based detection + LLM narrative.** Deterministic rules identify false positive/false negative/contradiction/completeness issues. LLM generates human-readable explanations for each caveat. Rules catch it, LLM explains it.
- **Four check types (per MECH-05):**
  1. False positive check: signal fired, but context suggests innocent explanation
  2. False negative check: signal didn't fire, but company profile suggests exposure
  3. Contradictory signal check: conflicting signals suggest missing context
  4. Data completeness check: required data unavailable, conclusions unreliable
- **Runs after SCORE (new ScoreStage step).** Has access to full picture: signal results, tier, severity, pattern engine results. Can check for contradictions across all layers. New Step 17+ in ScoreStage.
- **Caveats never modify score.** Adversarial output is informational. Tier, severity, and pattern results are unchanged.
- **Both inline caveats + dedicated section:**
  - Inline caveat badges on specific signals/findings in the main worksheet body
  - Full "Devil's Advocate" section at same prominence level as scoring section
  - Devil's Advocate is a core part of the decision record -- UW should always read the counter-argument before deciding

### Claude's Discretion
- Conjunction rule pipeline placement (ANALYZE vs SCORE step)
- Deep-dive acquisition architecture (loop vs queue vs hybrid)
- Exact conjunction rule definitions beyond the listed 6-10 patterns
- Absence rule specifics (which disclosures map to which company attributes)
- Contextual reframing threshold adjustments per context matrix cell
- Adversarial critique rule catalog (specific false positive/negative patterns)
- LLM prompt design for adversarial narrative generation
- Code organization (new files, module structure within stages/analyze/ and stages/score/)
- How to integrate Tier 3 signals with the existing signal dependency graph

</decisions>

<specifics>
## Specific Ideas

- Conjunction rules encode the "underwriter's gut" -- the known dangerous combinations that 25 years of D&O experience recognizes instantly. Machine encodes the pattern, not replaces the judgment.
- Absence detection captures the "dog that didn't bark" -- in D&O, what a company DOESN'T disclose is often more telling than what it does. Missing related-party disclosures when Glassdoor reviews mention nepotism. Missing segment reporting when revenue concentration is obvious.
- Contextual reframing prevents false alarms from one-size-fits-all thresholds. A 40% CEO pay increase at a post-IPO company setting up their first comp package is completely different from the same increase at a mature F500.
- Devil's Advocate section at equal prominence to scoring forces the worksheet to be intellectually honest. The recommendation says ELEVATED, but here's why it might be wrong. This is what a good underwriter does mentally -- the system makes it explicit and systematic.
- Deep-dive triggers with acquisition loops mean the system adapts its depth to the risk profile. Low-risk companies get standard analysis. Companies that trigger deep-dives get the equivalent of a full manual investigation, automated.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain/brain_signal_schema.py`: `EvaluationMechanism` Literal already includes conjunction/absence/contextual. Schema is ready.
- `stages/analyze/signal_engine.py`: Main signal dispatcher (lines 362-398) -- needs mechanism-based dispatch layer added before threshold-type dispatch
- `stages/analyze/signal_evaluators.py`: Current evaluator functions (tiered, boolean, numeric, temporal) -- pattern for new evaluators
- `stages/analyze/signal_results.py`: SignalResult + SignalStatus -- new mechanisms produce same result type
- `stages/score/conjunction_scan.py` (Phase 109): Post-evaluation conjunction detection -- complements, doesn't replace
- `stages/score/_pattern_runner.py` (Phase 109): Runner pattern for orchestrating multiple engines
- `stages/render/context_builders/_signal_consumer.py`: SignalResultView already includes mechanism field
- `brain/framework/named_archetypes.yaml` (Phase 109): Pattern for defining curated YAML rules with recommendation_floor

### Established Patterns
- Signal evaluation: YAML definition → signal_engine dispatcher → evaluator function → SignalResult
- All definitions in YAML, Pydantic-validated, loaded at runtime
- Graceful degradation: evaluator failure → SKIPPED with warning, pipeline continues
- Pluggable Protocol pattern (ScoringLens, SeverityLens, PatternEngine) for adversarial critique
- ScoreStage sequential steps with per-step try/except

### Integration Points
- `stages/analyze/signal_engine.py`: Add mechanism-based dispatch for conjunction/absence/contextual
- `stages/score/__init__.py`: Add adversarial critique step (Step 17+) after pattern engines (Step 16)
- `brain/signals/`: New YAML files for conjunction/absence/contextual signals
- `brain/framework/`: Deep-dive trigger definitions, adversarial critique rules
- `stages/render/context_builders/`: New adversarial context builder for Devil's Advocate section
- `templates/html/sections/`: New adversarial section template

</code_context>

<deferred>
## Deferred Ideas

- Full LLM-powered adversarial critique without rule scaffolding (ADV-05, v8.0+)
- Sector base rate false positive/negative checks (ADV-05, v8.0+)
- Market-cycle-aware contextual reframing (adjusting thresholds for hard/soft market)
- Interactive calibration for conjunction/absence/contextual thresholds
- Peer-comparison absence detection from live SEC Frames data (requires additional acquisition step)

</deferred>

---

*Phase: 110-new-signal-mechanisms-adversarial-critique*
*Context gathered: 2026-03-16*
