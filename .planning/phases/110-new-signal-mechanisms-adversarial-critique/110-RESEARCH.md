# Phase 110: New Signal Mechanisms + Adversarial Critique - Research

**Researched:** 2026-03-16
**Domain:** Signal evaluation architecture, rule-based critique engines, YAML-driven evaluation dispatch
**Confidence:** HIGH

## Summary

Phase 110 extends the signal evaluation pipeline with four new mechanism types (conjunction, absence, contextual, conditional deep-dive) and adds an adversarial critique second-pass. This is entirely an internal architecture extension -- no new external libraries needed. The existing codebase provides all patterns: YAML-defined signals with `evaluation.mechanism` field (6-value Literal already includes conjunction/absence/contextual), Pydantic-validated schemas, pluggable Protocol-based engines (PatternEngine, ScoringLens, SeverityLens), and sequential ScoreStage steps with per-step try/except graceful degradation.

The key architectural insight is that the four new mechanism types operate at two different levels: (1) conjunction/absence/contextual are signal-level evaluators that fire during ANALYZE (adding new evaluator functions alongside existing tiered/boolean/numeric/temporal), and (2) conditional deep-dive triggers and adversarial critique are post-scoring operations that run in SCORE (as new Steps 17 and 18). This two-level split follows the existing pattern where signal evaluation happens in ANALYZE and compound pattern detection happens in SCORE.

**Primary recommendation:** Follow the established evaluator dispatch pattern in `signal_engine.py` for mechanisms 1-3 (dispatch on `evaluation.mechanism` before `threshold.type`), and follow the PatternEngine/runner pattern for deep-dive triggers and adversarial critique (new Steps 17-18 in ScoreStage).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Conjunction rules are separate from Phase 109 Conjunction Scan -- distinct YAML signals with `evaluation.mechanism: conjunction`
- Start with 6-10 curated conjunction rules covering known dangerous D&O combinations
- Elevation floor pattern (like archetypes) -- each conjunction rule has `recommendation_floor`
- Triple-source absence expectation model: company-profile-driven, peer-comparison-driven, curated always-expected list
- Separate signals with `mechanism=absence` (20-30 rules)
- Full context matrix for contextual reframing: lifecycle stage, sector, size, product type, tower position (20-30 rules)
- 8-12 comprehensive conditional deep-dive triggers covering all H/A/E dimensions
- Deep-dive triggers CAN request additional acquisition (pipeline loop)
- Adversarial critique: rule-based detection + LLM narrative generation
- Four adversarial check types: false positive, false negative, contradictory signal, data completeness
- Adversarial runs after SCORE (new ScoreStage step), has access to full picture
- Caveats NEVER modify score -- informational only
- Both inline caveat badges + dedicated Devil's Advocate section

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

### Deferred Ideas (OUT OF SCOPE)
- Full LLM-powered adversarial critique without rule scaffolding (ADV-05, v8.0+)
- Sector base rate false positive/negative checks (ADV-05, v8.0+)
- Market-cycle-aware contextual reframing
- Interactive calibration for conjunction/absence/contextual thresholds
- Peer-comparison absence detection from live SEC Frames data
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MECH-01 | Conjunction signal rules in YAML -- individually normal signals combined = elevated | Evaluator dispatch pattern, conjunction YAML schema, recommendation_floor from archetype pattern |
| MECH-02 | Absence detection rules -- expected disclosure missing = signal | Absence evaluator with triple-source expectation model, company profile access pattern |
| MECH-03 | Contextual reframing rules -- same data means different things by company type | Contextual evaluator with context matrix lookup, company profile + CLI params |
| MECH-04 | Conditional Tier 3 deep-dive triggers formalized | Framework YAML for triggers, post-scoring runner, acquisition loop architecture |
| MECH-05 | Adversarial Critique second-pass: false positive/false negative/contradictory/completeness | AdversarialCritiqueEngine Protocol, rule catalog, LLM narrative, ScoreStage Step 18 |
| MECH-06 | Adversarial caveats displayed alongside recommendation -- never modify score | Pydantic models for caveats, render context builder, template section |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | v2 (existing) | YAML signal schema validation, result models | Already enforced on all brain YAML; BrainSignalEntry validates at load |
| PyYAML | (existing) | YAML signal and framework file loading | Standard across all brain YAML loading |
| Python typing | 3.12+ | Literal types for mechanism dispatch, Protocol for engines | Pyright strict mode enforced project-wide |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | stdlib | Structured logging for new evaluators | All new evaluator/engine functions |
| math | stdlib | erfc for probability calculations in adversarial | If adversarial checks need statistical computations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom rule engine | Rete/Drools-like library | Massive overkill -- YAML + Python dispatch is simpler and the established pattern |
| LangChain for adversarial LLM | Direct Claude API | Project already uses direct Claude calls in subagents; LangChain adds unnecessary abstraction |

**Installation:**
No new dependencies needed. All work uses existing project libraries.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  stages/
    analyze/
      signal_engine.py          # Add mechanism dispatch before threshold dispatch
      signal_evaluators.py      # Existing evaluators (tiered, boolean, etc.)
      mechanism_evaluators.py   # NEW: conjunction, absence, contextual evaluators
    score/
      __init__.py               # Add Steps 17 (deep-dive) + 18 (adversarial)
      _deepdive_runner.py       # NEW: conditional deep-dive trigger runner
      _adversarial_runner.py    # NEW: adversarial critique orchestrator
      adversarial_engine.py     # NEW: AdversarialCritiqueEngine (Protocol pattern)
  brain/
    signals/                    # NEW conjunction/absence/contextual YAML files
      conjunction/              # NEW: 6-10 conjunction rule signals
      absence/                  # NEW: 20-30 absence detection signals
      contextual/               # NEW: 20-30 contextual reframing signals
    framework/
      deepdive_triggers.yaml    # NEW: 8-12 conditional deep-dive trigger definitions
      adversarial_rules.yaml    # NEW: false positive/negative/contradiction/completeness rules
      context_matrix.yaml       # NEW: lifecycle/sector/size/product/tower classification rules
  models/
    adversarial.py              # NEW: AdversarialResult, Caveat, DevilsAdvocate models
```

### Pattern 1: Mechanism-Based Dispatch in signal_engine.py

**What:** Before dispatching on `threshold.type`, check `evaluation.mechanism`. If mechanism is `conjunction`, `absence`, or `contextual`, route to mechanism-specific evaluators that replace the standard threshold logic.

**When to use:** All new mechanism types. This is the critical integration point.

**Example:**
```python
# In signal_engine.py evaluate_signal() or execute_signals()
# Add mechanism dispatch BEFORE threshold dispatch

def evaluate_signal(sig: dict[str, Any], data: dict[str, Any]) -> SignalResult:
    """Evaluate a single signal against its mapped data."""
    # NEW: Mechanism-based dispatch (Phase 110)
    evaluation = sig.get("evaluation", {})
    mechanism = evaluation.get("mechanism", "threshold") if isinstance(evaluation, dict) else "threshold"

    if mechanism == "conjunction":
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_conjunction
        result = evaluate_conjunction(sig, data, signal_results_ref)
        result = _apply_classification_metadata(result, sig)
        return _apply_traceability(result, sig, "conjunction")
    elif mechanism == "absence":
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_absence
        result = evaluate_absence(sig, data, company_ref)
        result = _apply_classification_metadata(result, sig)
        return _apply_traceability(result, sig, "absence")
    elif mechanism == "contextual":
        from do_uw.stages.analyze.mechanism_evaluators import evaluate_contextual
        result = evaluate_contextual(sig, data, company_ref, pipeline_config_ref)
        result = _apply_classification_metadata(result, sig)
        return _apply_traceability(result, sig, "contextual")

    # Existing threshold-based dispatch continues below...
    raw_threshold = sig.get("threshold")
    # ... existing code
```

**Critical design decision: Conjunction evaluators need access to OTHER signal results.** The conjunction mechanism evaluates whether a combination of signals fire together. This means the conjunction evaluator needs the signal_results dict as input. Two options:
- **Option A (Recommended): Run conjunction/absence/contextual signals in a second pass.** Execute standard signals first, then run mechanism signals with results available. This matches the `signal_class: inference` ordering that already exists via `order_signals_for_execution()`.
- **Option B:** Evaluate in SCORE as a separate step (like pattern engines). But this breaks the "signals produce SignalResults" contract and duplicates evaluation infrastructure.

**Recommendation: Option A.** Mark conjunction/absence/contextual signals as `signal_class: inference` so they naturally execute after standard signals. The dependency graph already supports this ordering.

### Pattern 2: Conjunction Signal YAML Schema

**What:** New YAML signals with `evaluation.mechanism: conjunction` and a `conjunction_rules` block.

**Example:**
```yaml
- id: CONJ.COMP_PERF.pay_up_perf_down
  name: "Compensation-Performance Divergence"
  work_type: evaluate
  tier: 2
  depth: 3
  signal_class: inference
  rap_class: agent
  rap_subcategory: agent.executive_conduct
  evaluation:
    mechanism: conjunction
    conjunction_rules:
      required_signals:
        - EXEC.COMP.ceo_total_increase     # CEO comp up
        - FIN.TEMPORAL.margin_compression   # Performance down
        - GOV.PAY.clawback                  # No clawback (CLEAR = missing)
      minimum_matches: 2
      signal_conditions:
        EXEC.COMP.ceo_total_increase: "TRIGGERED"     # Must be RED/YELLOW
        FIN.TEMPORAL.margin_compression: "TRIGGERED"   # Must be RED/YELLOW
        GOV.PAY.clawback: "CLEAR"                      # Absence of clawback
      recommendation_floor: ELEVATED
  threshold:
    type: conjunction
    red: "2+ of 3 component signals firing in combination"
    clear: "Component signals not co-occurring"
  epistemology:
    rule_origin: "D&O claims experience: 70%+ of executive compensation SCAs involve pay-performance divergence without recovery mechanisms"
    threshold_basis: "2-of-3 threshold based on SCAC filing patterns -- single compensation signal alone insufficient"
  # ... standard fields
```

### Pattern 3: Absence Detection YAML Schema

**What:** Signals with `evaluation.mechanism: absence` that fire when expected disclosures are MISSING.

**Example:**
```yaml
- id: ABS.DISC.related_party_missing
  name: "Missing Related-Party Disclosure"
  work_type: evaluate
  tier: 2
  depth: 3
  signal_class: inference
  rap_class: agent
  rap_subcategory: agent.disclosure
  evaluation:
    mechanism: absence
    absence_rules:
      expectation_type: company_profile   # or peer_comparison, always_expected
      condition: "company has known subsidiaries OR related-party transactions in prior filings"
      expected_signals:
        - "GOV.PAY.related_party"
      expected_status: "TRIGGERED"  # We expect this to fire if data exists
      absence_trigger: "SKIPPED"    # Fires when expected signal is SKIPPED (data missing)
  threshold:
    type: absence
    red: "Expected related-party disclosure absent despite company characteristics suggesting it should exist"
    clear: "Related-party disclosure present as expected"
  epistemology:
    rule_origin: "SEC Regulation S-K Item 404 requires related-party transaction disclosure; absence despite indicators suggests incomplete disclosure"
    threshold_basis: "Expectation based on company profile attributes (subsidiaries, insider ownership >5%)"
```

### Pattern 4: Contextual Reframing YAML Schema

**What:** Signals with `evaluation.mechanism: contextual` that re-evaluate existing signal data through a company-type lens.

**Example:**
```yaml
- id: CTX.COMP.ceo_pay_lifecycle
  name: "CEO Pay - Lifecycle Context"
  work_type: evaluate
  tier: 2
  depth: 3
  signal_class: inference
  rap_class: agent
  rap_subcategory: agent.executive_conduct
  evaluation:
    mechanism: contextual
    contextual_rules:
      source_signal: EXEC.COMP.ceo_total_increase
      context_dimensions:
        - lifecycle_stage
        - company_size
      context_matrix:
        post_ipo:
          threshold_adjustment: 2.0   # Double the threshold (40% -> 80% acceptable)
          rationale: "Post-IPO companies often set initial comp packages"
        mature:
          threshold_adjustment: 0.5   # Halve the threshold (40% -> 20% alarming)
          rationale: "Mature company pay increases should be modest"
        distressed:
          threshold_adjustment: 0.3   # Even more aggressive threshold
          rationale: "Pay increases during distress are highly alarming"
  threshold:
    type: contextual
    red: "CEO pay increase exceeds lifecycle-adjusted threshold"
    yellow: "CEO pay increase above lifecycle-adjusted caution level"
    clear: "CEO pay increase within lifecycle-appropriate range"
  epistemology:
    rule_origin: "ISS compensation guidelines: pay-for-performance evaluation adjusts for company lifecycle"
    threshold_basis: "Post-IPO 2x adjustment from ISS guidelines; mature 0.5x from Cornerstone settlement data"
```

### Pattern 5: Adversarial Critique Engine (Protocol Pattern)

**What:** New Protocol-based engine that produces caveats, following the ScoringLens/PatternEngine pattern.

**Example:**
```python
# adversarial_engine.py
from pydantic import BaseModel, Field
from typing import Any, Protocol, runtime_checkable

class Caveat(BaseModel):
    """A single adversarial critique finding."""
    caveat_type: Literal["false_positive", "false_negative", "contradiction", "data_completeness"]
    target_signal_id: str = ""       # Signal this caveat is about (empty for general)
    headline: str                    # One-sentence summary
    explanation: str                 # Detailed human-readable explanation (LLM-generated)
    confidence: float = 0.0          # 0.0-1.0
    evidence: list[str] = Field(default_factory=list)

class AdversarialResult(BaseModel):
    """Complete adversarial critique output."""
    caveats: list[Caveat] = Field(default_factory=list)
    false_positive_count: int = 0
    false_negative_count: int = 0
    contradiction_count: int = 0
    completeness_issues: int = 0
    overall_confidence_assessment: str = ""  # LLM narrative
    computed_at: datetime

@runtime_checkable
class AdversarialEngine(Protocol):
    """Protocol for adversarial critique engines."""
    def evaluate(
        self,
        signal_results: dict[str, Any],
        scoring_result: ScoringResult,
        *,
        state: AnalysisState | None = None,
    ) -> AdversarialResult: ...
```

### Pattern 6: ScoreStage Integration (Steps 17-18)

**What:** Add deep-dive triggers (Step 17) and adversarial critique (Step 18) to ScoreStage.run().

**Example:**
```python
# In ScoreStage.run(), after Step 16 (pattern engines):

# Step 17: Conditional deep-dive triggers (Phase 110)
try:
    from do_uw.stages.score._deepdive_runner import run_deepdive_triggers
    deepdive_result = run_deepdive_triggers(
        state=state,
        signal_results=signal_results,
        hae_result=hae_result,
    )
    if deepdive_result is not None:
        state.scoring.deepdive_result = deepdive_result
except Exception:
    logger.warning("Deep-dive triggers failed; continuing", exc_info=True)

# Step 18: Adversarial critique (Phase 110)
try:
    from do_uw.stages.score._adversarial_runner import run_adversarial_critique
    adversarial_result = run_adversarial_critique(
        state=state,
        signal_results=signal_results,
        scoring_result=state.scoring,
    )
    if adversarial_result is not None:
        state.scoring.adversarial_result = adversarial_result
except Exception:
    logger.warning("Adversarial critique failed; continuing", exc_info=True)
```

### Anti-Patterns to Avoid

- **Hardcoding conjunction/absence/contextual rules in Python.** All rules MUST be in YAML. Python code is dispatch/evaluation only.
- **Modifying scores in adversarial critique.** Caveats are informational. Never mutate `state.scoring` tier/quality_score/etc.
- **Evaluating conjunction signals before their component signals have results.** Must use `signal_class: inference` ordering or a two-pass approach.
- **Making contextual reframing thresholds independent of source signals.** Contextual signals MUST reference a source signal and its data -- they re-interpret, not re-acquire.
- **Building a general-purpose rule engine.** Keep evaluators simple -- each mechanism type has one evaluator function, not a configurable framework.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Signal execution ordering | Custom topological sort | Existing `order_signals_for_execution()` from `brain/dependency_graph.py` | Already handles `signal_class` ordering (foundational -> evaluative -> inference) |
| YAML loading + validation | Custom parser | Existing `BrainLoader.load_all()` + `BrainSignalEntry` Pydantic model | Schema validation catches typos at load time |
| Signal result creation | Ad-hoc dict construction | Existing `SignalResult` model with `_apply_classification_metadata` + `_apply_traceability` | Ensures traceability chain is always complete |
| Tier comparison/floor logic | Custom comparison | Existing `HAETier` enum with `__lt__`/`__gt__` operators | Already used by archetype tier floors in Phase 109 |
| Engine result model | New result type for each engine | Existing `EngineResult` Pydantic model | Consistent across all pattern-type engines |
| Graceful degradation | Custom error handling | Existing per-step try/except pattern in ScoreStage | Every new step should follow the same pattern |
| LLM text generation | Custom prompt chain | Existing subagent pattern (if used elsewhere in pipeline) | Consistent with MCP boundary rules (SCORE stage uses local data only, but LLM calls are allowed for narrative generation) |

**Key insight:** Phase 110 is an extension of existing patterns, not a new framework. Every mechanism can be implemented by following established signal evaluator, pattern engine, and ScoreStage step patterns.

## Common Pitfalls

### Pitfall 1: Circular Dependencies in Conjunction Evaluation
**What goes wrong:** Conjunction signal A depends on signals B and C. Signal B depends on A (circular).
**Why it happens:** When defining conjunction rules, it's tempting to create mutual dependencies.
**How to avoid:** Conjunction signals MUST have `signal_class: inference` and reference only `evaluative` or `foundational` signals. Never reference other `inference` signals.
**Warning signs:** `order_signals_for_execution()` raises an error or enters infinite loop.

### Pitfall 2: Absence Detection False Positives on Data Gaps
**What goes wrong:** Absence detection fires because data wasn't acquired (SKIPPED), not because disclosure is genuinely missing.
**Why it happens:** 60% of signal results are currently SKIPPED due to data coverage gaps. Absence detection must distinguish "didn't look" from "looked and didn't find."
**How to avoid:** Absence rules must check `data_status` not just `status`. Only fire when the acquisition pipeline successfully ran but the expected disclosure was not found. If `data_status == DATA_UNAVAILABLE`, that's a data gap, not an absence signal.
**Warning signs:** Absence signals fire for every company because underlying data was never acquired.

### Pitfall 3: Contextual Reframing Without Company Context
**What goes wrong:** Contextual evaluator can't determine lifecycle stage or sector, so it falls back to default thresholds, making contextual signals identical to their source signals.
**Why it happens:** CompanyProfile fields like years_public, SIC code, market_cap may be None.
**How to avoid:** Contextual evaluator must gracefully degrade to `signal_class: inference` with status=SKIPPED when company context is insufficient. Never silently fall through to default.
**Warning signs:** All contextual signals have identical results to their source signals.

### Pitfall 4: ScoreStage Exceeding 500 Lines
**What goes wrong:** Adding Steps 17-18 pushes `score/__init__.py` over the 500-line anti-context-rot limit.
**Why it happens:** ScoreStage.run() is already 611 lines. Adding more steps inline would exceed the limit.
**How to avoid:** Follow the `_pattern_runner.py` and `_severity_runner.py` pattern: each new step is a separate `_*_runner.py` file. ScoreStage.run() only imports and calls the runner function.
**Warning signs:** score/__init__.py growing beyond 650 lines.

### Pitfall 5: Adversarial LLM Calls Blocking Pipeline
**What goes wrong:** LLM narrative generation for adversarial caveats takes 30+ seconds, slowing the entire pipeline.
**Why it happens:** Generating human-readable explanations for each caveat requires LLM calls.
**How to avoid:** Keep rule detection fully deterministic (no LLM). Generate narratives in a batch call at the end, or defer LLM narrative to render time. Consider a budget: max 5 caveats get LLM explanations, rest use template-based narratives.
**Warning signs:** Pipeline time increases by >30 seconds when adversarial is enabled.

### Pitfall 6: BrainSignalEntry Schema Extension Breaking Existing Signals
**What goes wrong:** Adding required fields (conjunction_rules, absence_rules, contextual_rules) to EvaluationSpec breaks the 508 existing signals.
**Why it happens:** Pydantic `extra="forbid"` on EvaluationSpec rejects unknown fields.
**How to avoid:** New mechanism-specific fields MUST be Optional with defaults. Only `evaluation.mechanism` is already required. Add `conjunction_rules: ConjunctionRuleSpec | None = None`, `absence_rules: AbsenceRuleSpec | None = None`, `contextual_rules: ContextualRuleSpec | None = None` to EvaluationSpec.
**Warning signs:** CI gate test (8 tests from Phase 103) fails on existing signal YAML.

### Pitfall 7: Deep-Dive Acquisition Loop Creates Infinite Cycles
**What goes wrong:** Deep-dive trigger requests additional acquisition, which triggers extraction, which changes signal results, which triggers another deep-dive.
**Why it happens:** Uncapped pipeline loops.
**How to avoid:** Hard cap: max 1 deep-dive iteration per pipeline run. After deep-dive acquisition runs, re-evaluate only the triggered deep-dive signals, not the entire signal corpus. Use a `deepdive_iteration` counter in pipeline state.
**Warning signs:** Pipeline runs >2x expected time.

## Code Examples

### Conjunction Evaluator Function
```python
# mechanism_evaluators.py
def evaluate_conjunction(
    sig: dict[str, Any],
    data: dict[str, Any],
    signal_results: dict[str, Any],
) -> SignalResult:
    """Evaluate a conjunction mechanism signal.

    Checks whether required component signals fire in combination.
    Returns TRIGGERED if minimum_matches met, CLEAR otherwise.
    """
    evaluation = sig.get("evaluation", {})
    conj_rules = evaluation.get("conjunction_rules", {})
    required_signals = conj_rules.get("required_signals", [])
    minimum_matches = conj_rules.get("minimum_matches", 2)
    signal_conditions = conj_rules.get("signal_conditions", {})

    matched = 0
    matched_ids: list[str] = []
    for ref_signal_id in required_signals:
        ref_result = signal_results.get(ref_signal_id)
        if not isinstance(ref_result, dict):
            continue
        ref_status = ref_result.get("status", "")
        expected = signal_conditions.get(ref_signal_id, "TRIGGERED")
        if ref_status == expected or (expected == "TRIGGERED" and ref_status in ("RED", "YELLOW")):
            matched += 1
            matched_ids.append(ref_signal_id)

    fired = matched >= minimum_matches
    status = SignalStatus.TRIGGERED if fired else SignalStatus.CLEAR
    level = "red" if fired else "clear"

    return SignalResult(
        signal_id=sig.get("id", "UNKNOWN"),
        signal_name=sig.get("name", ""),
        status=status,
        value=f"{matched}/{len(required_signals)}",
        threshold_level=level,
        evidence=f"Conjunction: {matched} of {len(required_signals)} component signals fire ({', '.join(matched_ids)})",
        factors=extract_factors(sig),
        section=sig.get("section", 0),
        details={"matched_ids": matched_ids, "minimum_matches": minimum_matches},
    )
```

### Adversarial False Positive Check Rule
```python
# adversarial_engine.py (rule detection, deterministic)
def _check_false_positives(
    signal_results: dict[str, Any],
    rules: list[dict[str, Any]],
) -> list[Caveat]:
    """Check for signals that may be false positives based on context."""
    caveats = []
    for rule in rules:
        target_signal = rule.get("target_signal", "")
        mitigating_signals = rule.get("mitigating_signals", [])
        sig_data = signal_results.get(target_signal)
        if not isinstance(sig_data, dict) or sig_data.get("status") != "TRIGGERED":
            continue
        # Check if mitigating signals suggest false positive
        mitigating_count = sum(
            1 for ms in mitigating_signals
            if signal_results.get(ms, {}).get("status") == "CLEAR"
        )
        if mitigating_count >= rule.get("minimum_mitigating", 1):
            caveats.append(Caveat(
                caveat_type="false_positive",
                target_signal_id=target_signal,
                headline=rule.get("headline", f"{target_signal} may be false positive"),
                explanation="",  # LLM fills this later
                confidence=mitigating_count / len(mitigating_signals),
                evidence=[f"{ms}: CLEAR" for ms in mitigating_signals],
            ))
    return caveats
```

### Deep-Dive Trigger YAML
```yaml
# brain/framework/deepdive_triggers.yaml
triggers:
  - id: deepdive.governance_board
    name: "Full Board Composition Deep-Dive"
    description: "Governance weak + executive departure triggers exhaustive board investigation"
    trigger_conditions:
      all_of:
        - signal: GOV.BOARD.independence
          status: TRIGGERED
        - signal: GOV.EXEC.departure_context
          status: TRIGGERED
    additional_signals:
      - GOV.BOARD.tenure
      - GOV.BOARD.expertise
      - GOV.BOARD.attendance
      - GOV.BOARD.overboarding
    additional_acquisition:
      - type: SEC_DEF14A
        depth: full_proxy
        fields: ["board_attendance_record", "committee_membership", "related_transactions"]
    uw_investigation_prompt: >
      Board composition deep-dive triggered. System analyzed available proxy data.
      Recommend manual review of: (1) individual director qualifications,
      (2) attendance patterns, (3) committee composition changes in last 2 years.
    rap_dimensions: [host, agent]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-signal threshold evaluation only | Compound pattern detection (Phase 109) | v7.0 Phase 109 | Phase 110 extends this with YAML-declarative conjunction rules |
| Hardcoded risk context | YAML-driven evaluation with mechanism dispatch | v7.0 Phase 103 | EvaluationMechanism Literal already includes conjunction/absence/contextual |
| No second-guessing of results | Adversarial critique as standard practice | Phase 110 (new) | First systematic false positive/negative detection in D&O underwriting systems |

**Key state of the art points:**
- The `EvaluationMechanism` Literal in `brain_signal_schema.py` already includes all 6 values needed. Schema is ready.
- `signal_class: inference` ordering in `dependency_graph.py` already provides the second-pass execution needed for conjunction/absence/contextual signals.
- The Protocol pattern (ScoringLens, SeverityLens, PatternEngine) is the established extension mechanism and should be used for adversarial critique.

## Open Questions

1. **Deep-Dive Acquisition Loop Architecture**
   - What we know: Deep-dive triggers need to request additional data acquisition. Pipeline currently runs ACQUIRE -> EXTRACT -> ANALYZE -> SCORE linearly.
   - What's unclear: Whether to implement a true SCORE->ACQUIRE loop (architectural complexity) or a deferred queue that runs on next pipeline invocation.
   - Recommendation: Implement as a single-iteration loop within the SCORE step itself. Deep-dive runner calls targeted acquisition functions directly (bypassing full ACQUIRE stage), extracts minimal data, evaluates only the deep-dive signals. This avoids re-running the full pipeline. Cap at 1 iteration. Log what additional investigation is recommended for the UW.

2. **LLM Budget for Adversarial Narratives**
   - What we know: Rule detection is deterministic. LLM generates human-readable explanations.
   - What's unclear: How many caveats to generate narratives for, token budget, which model.
   - Recommendation: Cap at 8 caveats with LLM narratives. Use template-based explanations for overflow. Generate all narratives in a single batched prompt (send all caveat context, get all explanations back). This keeps LLM cost predictable.

3. **Conjunction Rule Recommendation Floor Integration with H/A/E Tier**
   - What we know: Archetypes already use `_apply_tier_floors` pattern from Phase 109.
   - What's unclear: Should conjunction rule floors apply to the H/A/E tier directly, or only to the legacy tier?
   - Recommendation: Apply to H/A/E tier using the same `_apply_tier_floors` pattern. Conjunction signals produce SignalResults that feed into the next scoring iteration conceptually, but the floor is applied post-scoring like archetypes.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/brain_signal_schema.py` - EvaluationMechanism Literal already defines conjunction/absence/contextual
- `src/do_uw/stages/analyze/signal_engine.py` - Current dispatch architecture (418 lines)
- `src/do_uw/stages/analyze/signal_evaluators.py` - Evaluator function patterns (344 lines)
- `src/do_uw/stages/score/__init__.py` - ScoreStage pipeline (611 lines)
- `src/do_uw/stages/score/_pattern_runner.py` - Runner pattern for engines (371 lines)
- `src/do_uw/stages/score/conjunction_scan.py` - Phase 109 conjunction scan (existing, complementary)
- `src/do_uw/stages/score/pattern_engine.py` - PatternEngine Protocol + EngineResult/ArchetypeResult
- `src/do_uw/stages/analyze/signal_results.py` - SignalResult model (317 lines)
- `src/do_uw/brain/framework/named_archetypes.yaml` - Archetype YAML pattern with recommendation_floor
- `src/do_uw/models/patterns.py` - PatternEngineResult model
- `src/do_uw/models/scoring.py` - ScoringResult model (shows where to add adversarial_result field)

### Secondary (MEDIUM confidence)
- `.planning/phases/110-new-signal-mechanisms-adversarial-critique/110-CONTEXT.md` - User decisions and constraints

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries needed, all patterns exist in codebase
- Architecture: HIGH - Every pattern follows established conventions (evaluator dispatch, Protocol engines, ScoreStage steps, YAML definitions)
- Pitfalls: HIGH - Based on direct code analysis of current data coverage (60% SKIPPED), file sizes (611-line ScoreStage), and established anti-patterns
- YAML schema: HIGH - EvaluationMechanism Literal already prepared in Phase 103; EvaluationSpec just needs Optional sub-model fields
- Adversarial engine: MEDIUM - New pattern (no existing adversarial engine to follow), but Protocol pattern is well-established

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable internal architecture, no external dependencies)
