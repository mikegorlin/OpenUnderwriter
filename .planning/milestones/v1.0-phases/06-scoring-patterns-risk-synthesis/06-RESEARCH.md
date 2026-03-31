# Phase 6: Scoring, Patterns & Risk Synthesis - Research

**Researched:** 2026-02-08
**Domain:** Rule-based scoring engine, pattern detection, risk classification (pure computation over structured data)
**Confidence:** HIGH

## Summary

Phase 6 implements the ANALYZE and SCORE pipeline stages -- the computation layers that transform 5 phases of extracted structured facts into a quantified risk assessment. This is a pure rule-based engine with no external data access, no LLM calls, and no network I/O. All inputs come from `state.extracted` (financials, market, governance, litigation); all outputs go to `state.analysis` and `state.scoring`.

The domain is well-constrained: every scoring rule, pattern trigger, red flag ceiling, and tier boundary is already defined in the brain/ JSON config files (scoring.json, patterns.json, red_flags.json, sectors.json, checks.json). The implementation is a mechanical translation of these rules into Python code that reads Pydantic models, evaluates conditions, and writes results back to Pydantic models. The main engineering challenges are: (1) mapping 359 checks to specific fields on the ExtractedData model tree, (2) handling missing/partial data gracefully without false negatives, (3) keeping files under 500 lines with a clean split between ANALYZE (check execution) and SCORE (factor scoring, patterns, CRF, tier, claim probability, severity), and (4) ensuring every output is traceable to the config rule ID that produced it.

**Primary recommendation:** Build this as a 3-plan phase following the existing sub-orchestrator pattern: Plan 1 creates the ANALYZE stage (check engine + data mappers), Plan 2 creates the SCORE stage (10-factor scoring + CRF + tier), Plan 3 adds patterns, allegation mapping, claim probability, severity modeling, tower positioning, and wires everything into the pipeline.

## Standard Stack

### Core

No new external libraries are needed for Phase 6. This is pure computation over existing Pydantic models.

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| pydantic v2 | existing | State models for input/output | Already in project, all data is Pydantic |
| ConfigLoader | existing | Load brain/ JSON files | Already loads all 5 config files |
| StrEnum | stdlib | Status/classification enums | Python 3.12+ pattern used everywhere |
| dataclass | stdlib | ExtractionReport-style light structs | Established pattern from EXTRACT stage |
| json (stdlib) | existing | Config file parsing | Already used by ConfigLoader |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| math (stdlib) | Rounding, min/max, percentage math | Factor score capping, ceiling logic |
| logging (stdlib) | Stage execution logging | Check skip/fail logging |
| datetime (stdlib) | Recency calculations | Time-based check conditions (e.g., "within 12 months") |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom rule engine | Rules engine library (e.g., business-rules, durable-rules) | Overkill -- checks.json IS the rule registry; the evaluation logic is simple field comparisons. Custom code is more maintainable for 359 checks with known structure. |
| pandas for data manipulation | Direct Pydantic field access | Pydantic models are already typed; adding pandas creates an unnecessary data format conversion layer |
| scipy for severity distributions | Manual percentile math | Settlement prediction uses simple multiplier tables from scoring.json, not statistical distributions in v1 |

## Architecture Patterns

### Recommended Project Structure

```
src/do_uw/
  stages/
    analyze/
      __init__.py              # AnalyzeStage orchestrator (~200 lines)
      check_engine.py          # Check execution engine: load, match, evaluate (~400 lines)
      check_mappers.py         # Map check IDs to ExtractedData fields (~450 lines)
      check_results.py         # CheckResult model + aggregation (~200 lines)
    score/
      __init__.py              # ScoreStage orchestrator (~250 lines)
      factor_scoring.py        # 10-factor scoring with sub-components (~450 lines)
      pattern_detection.py     # 17 composite pattern evaluator (~450 lines)
      red_flag_gates.py        # 11 CRF ceilings + recency triggers (~250 lines)
      tier_classification.py   # Tier assignment + claim probability (~300 lines)
      allegation_mapping.py    # 5-theory mapping + risk type (~300 lines)
      severity_model.py        # Loss severity + tower positioning (~350 lines)
  models/
    scoring.py                 # Extended with new output models (~400 lines)
```

**Line count estimates:** 10 new files, ~3,400 total lines. All under 500 per file.

### Pattern 1: Check-to-Data Mapper (Core Architectural Decision)

**What:** Each of the 359 checks specifies `required_data` and `data_locations` pointing to data source types (SEC_10K, MARKET_PRICE, etc.), but the actual data lives in typed Pydantic models (ExtractedFinancials, MarketSignals, GovernanceData, LitigationLandscape). The mapper translates check data references to actual state model field paths.

**When to use:** Every check evaluation.

**Approach:** Group checks by the section/domain they target. Create mapper functions per domain (financial_mapper, market_mapper, governance_mapper, litigation_mapper) that return a dict[str, Any] of field values the check needs. This avoids a single monolithic mapping table.

```python
# check_mappers.py
from do_uw.models.state import ExtractedData

def map_check_data(
    check_id: str,
    check_config: dict[str, Any],
    extracted: ExtractedData,
) -> dict[str, Any]:
    """Map check data requirements to actual extracted values.

    Returns a dict of field_name -> value pairs the check evaluator
    needs. Missing data returns None values (not KeyError).
    """
    section = check_config.get("section", 0)
    if section in (1, 2):
        return _map_company_fields(check_id, extracted)
    elif section == 3:
        return _map_financial_fields(check_id, extracted)
    elif section == 4:
        return _map_market_fields(check_id, extracted)
    elif section == 5:
        return _map_governance_fields(check_id, extracted)
    elif section == 6:
        return _map_litigation_fields(check_id, extracted)
    return {}
```

### Pattern 2: Check Evaluator with Threshold Types

**What:** checks.json has 7 threshold types (tiered, percentage, boolean, classification, count, multi_period, info, search, value, pattern). Each needs a different evaluation strategy.

**Approach:** Use a dispatcher pattern based on threshold type:

```python
# check_engine.py
def evaluate_check(
    check: dict[str, Any],
    data: dict[str, Any],
) -> CheckResult:
    """Evaluate a single check against its data."""
    threshold = check.get("threshold", {})
    threshold_type = threshold.get("type", "info")

    if threshold_type == "tiered":
        return _eval_tiered(check, data, threshold)
    elif threshold_type == "percentage":
        return _eval_percentage(check, data, threshold)
    elif threshold_type == "boolean":
        return _eval_boolean(check, data, threshold)
    elif threshold_type == "info":
        return _eval_info(check, data)
    # ... etc
```

**Key insight:** The 309 "tiered" checks all use a red/yellow/clear structure. The evaluator needs to determine which tier the data falls into, but many tiered checks have qualitative thresholds (e.g., "Leadership claimed without support") that cannot be fully automated. For these, return a "DATA_AVAILABLE" status with the raw data value and let downstream scoring apply the rule.

### Pattern 3: Factor Score Aggregation (Scoring Pipeline)

**What:** The SCORE stage consumes check results + patterns to compute 10 factor scores.

**Approach:** Two-pass scoring:
1. **Base scoring pass:** For each factor F1-F10, evaluate the scoring rules from scoring.json against the extracted data. Each factor uses its own rules (not check results directly -- the checks provide evidence/context, but factor scoring uses the scoring.json rules).
2. **Pattern modifier pass:** After base scores, apply pattern modifiers (from patterns.json score_impact fields) to adjust factor scores.
3. **Cap pass:** Apply factor max_points caps.

```python
# factor_scoring.py
def score_factor(
    factor_config: dict[str, Any],
    extracted: ExtractedData,
    check_results: dict[str, CheckResult],
    sector_code: str,
    sectors: dict[str, Any],
) -> FactorScore:
    """Score a single factor using its rules from scoring.json."""
    factor_id = factor_config["factor_id"]
    max_pts = factor_config["max_points"]

    # Evaluate each rule, take the maximum triggered
    base_points = _evaluate_factor_rules(factor_config, extracted, sector_code, sectors)

    # Apply bonuses (additive, but don't exceed max)
    bonus_points = _evaluate_bonuses(factor_config, extracted)

    # Apply multipliers (e.g., insider amplifier for F2)
    multiplied = _apply_multipliers(factor_config, extracted, base_points)

    # Cap at max_points
    final = min(multiplied + bonus_points, max_pts)

    return FactorScore(
        factor_id=factor_id,
        factor_name=factor_config["name"],
        max_points=max_pts,
        points_deducted=final,
        sub_components={"base": base_points, "bonus": bonus_points, ...},
    )
```

### Pattern 4: Red Flag Ceiling Application (Critical)

**What:** CRF gates impose hard ceilings AFTER factor scoring.

**Processing order (from red_flags.json processing_rules):**
1. Check ALL CRF triggers BEFORE factor scoring
2. Compute factor scores normally
3. Compute composite_score = 100 - total_risk_points
4. Apply ceiling: quality_score = MIN(composite_score, lowest_triggered_ceiling)
5. Determine tier from quality_score (not composite_score)

```python
# red_flag_gates.py
def apply_red_flag_ceilings(
    composite_score: float,
    triggers: list[RedFlagResult],
) -> tuple[float, str | None]:
    """Apply CRF ceilings and return (quality_score, binding_ceiling_id)."""
    lowest_ceiling = 100.0
    binding_id = None
    for trigger in triggers:
        if trigger.triggered and trigger.ceiling_applied is not None:
            if trigger.ceiling_applied < lowest_ceiling:
                lowest_ceiling = trigger.ceiling_applied
                binding_id = trigger.flag_id
    quality_score = min(composite_score, lowest_ceiling)
    return quality_score, binding_id
```

### Anti-Patterns to Avoid

- **Mixing ANALYZE and SCORE logic:** ANALYZE executes checks and detects patterns. SCORE computes factor scores, applies CRF, assigns tier. These are separate pipeline stages with separate inputs/outputs. Do NOT blend them.
- **Scoring logic outside stages/score/:** Per CLAUDE.md, all scoring logic MUST live in stages/score/. Pattern detection lives in stages/score/ too (it feeds scoring).
- **Hardcoded thresholds:** Every threshold, weight, ceiling, and boundary comes from brain/ JSON. No magic numbers in Python code.
- **LLM calls in ANALYZE/SCORE:** Per project decision, these stages are rule-based. No AI calls.
- **Imputation of missing data:** If a check's required data is missing, the check is SKIPPED (not evaluated as "pass"). AnalysisResults tracks checks_skipped.
- **Single-file factor scoring:** With 10 factors each having complex sub-rules, a single scoring file would exceed 500 lines. Split factor evaluation into dedicated files or use a dispatcher.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config loading | Custom JSON parser | ConfigLoader.load_all() | Already validates all 5 brain/ files |
| Pydantic model serialization | Custom serializers | model_dump_json / model_validate | Built into Pydantic v2 |
| Check registry parsing | Parse checks.json manually each time | Load once via ConfigLoader, pass through | Validated on load |
| Tier boundary lookup | Manual if/elif chain | Table-driven lookup from scoring.json tiers[] | Config-driven, NEEDS CALIBRATION |

**Key insight:** The brain/ JSON files ARE the specification. The Python code is a mechanical executor. Don't re-specify rules in Python -- read them from config and apply them.

## Common Pitfalls

### Pitfall 1: Checks vs Factor Scoring Confusion

**What goes wrong:** Treating the 359 checks and the 10-factor scoring model as the same thing. They are related but distinct.
**Why it happens:** Both reference factors (F1-F10). Checks map to factors, but factor scoring uses its own rules from scoring.json, not check results directly.
**How to avoid:** Checks produce CheckResult objects with status/evidence/source. Factor scoring reads extracted data directly using scoring.json rules. Check results provide EVIDENCE for the scoring narrative but do not directly compute factor scores. Pattern detection bridges the two -- patterns reference component_checks AND produce score_impact.
**Warning signs:** If you're iterating over check results to compute F1 points, you're doing it wrong. Scoring.json has explicit rules for F1.

### Pitfall 2: Missing Data = False Negative

**What goes wrong:** A check evaluates to "PASS" because the required data field is None, when in reality the data simply wasn't available.
**Why it happens:** Optional fields in Pydantic default to None. `if not value` treats None as false/zero.
**How to avoid:** Three-state check result: TRIGGERED (issue found), CLEAR (data present, no issue), SKIPPED (data unavailable). Track checks_skipped separately from checks_passed.
**Warning signs:** If checks_passed + checks_failed == 359 and checks_skipped == 0, something is wrong -- not all data will be available for every company.

### Pitfall 3: Pattern-Factor Score Double Counting

**What goes wrong:** A finding adds points to a factor directly AND triggers a pattern that also adds points to the same factor, resulting in double-counting.
**Why it happens:** scoring.json rules and patterns.json score_impact both reference the same factors.
**How to avoid:** Clear separation: scoring.json rules compute BASE factor points. patterns.json score_impact computes MODIFIER points. Both are additive but capped at factor max_points. The cap prevents runaway scoring.
**Warning signs:** If a company can score >100 total risk points (before capping), the math is wrong.

### Pitfall 4: Qualitative Check Evaluation

**What goes wrong:** Attempting to fully automate checks with qualitative thresholds like "MD&A is generic/boilerplate" or "management dodges analyst questions."
**Why it happens:** 6 pattern trigger conditions and some checks require NLP/manual evaluation (noted as pending todo from Phase 1).
**How to avoid:** For qualitative checks, use the data that IS available as a proxy. The sentiment_analysis and narrative_coherence extractors from Phase 4 already produce quantified signals (hedging_language_score, tone_trajectory, etc.). Map these proxy signals to the qualitative conditions. Where no proxy exists, mark the check as MANUAL_REVIEW_NEEDED.
**Warning signs:** If you're writing NLP code in the ANALYZE stage, you've crossed the stage boundary. NLP belongs in EXTRACT.

### Pitfall 5: ScoringResult Model Expansion

**What goes wrong:** The existing ScoringResult model in models/scoring.py has the basic structure but lacks fields for allegation theory mapping, claim probability, loss severity, tower position, risk type classification, and red flag summary. Adding all these to scoring.py would exceed 500 lines.
**How to avoid:** Split into scoring.py (factor scores, patterns, CRF, tier -- existing) + scoring_output.py (claim probability, severity, tower, allegation mapping, risk type, red flag summary). Or expand scoring.py carefully and use a second file only if needed. The existing scoring.py is 220 lines, so there's room.
**Warning signs:** If scoring.py is approaching 400 lines during model expansion, split proactively.

### Pitfall 6: CRF ID Mismatch Between scoring.json and red_flags.json

**What goes wrong:** scoring.json uses CRF-001 through CRF-011. red_flags.json uses CRF-01 through CRF-11 (no leading zero). Different ID formats.
**How to avoid:** Normalize IDs on load (strip leading zeros from the numeric portion) or map between both formats. Use red_flags.json as canonical (it has richer metadata).
**Warning signs:** If CRF lookups return "not found," check ID format normalization.

### Pitfall 7: Sector Code Availability

**What goes wrong:** Scoring rules reference sector baselines (sectors.json) using sector codes like "TECH", "BIOT", "FINS". The company's sector code comes from state.company.identity.sector, which may not match these codes exactly.
**How to avoid:** The RESOLVE stage's sic_to_sector() function produces sector codes. Verify these match sectors.json keys. Use the "DEFAULT" fallback from sectors.json when no sector match.
**Warning signs:** KeyError when looking up sector baselines.

## Code Examples

### Check Result Data Model

```python
# check_results.py
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field

class CheckStatus(StrEnum):
    TRIGGERED = "TRIGGERED"    # Issue found
    CLEAR = "CLEAR"            # Data present, no issue
    SKIPPED = "SKIPPED"        # Required data unavailable
    INFO = "INFO"              # Informational only (no pass/fail)

class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=False)

    check_id: str = Field(description="Check ID from checks.json")
    check_name: str = Field(default="", description="Human-readable name")
    status: CheckStatus = Field(description="Evaluation result")
    value: str | float | None = Field(
        default=None, description="The actual data value evaluated"
    )
    threshold_level: str = Field(
        default="", description="Which threshold was hit: red/yellow/clear"
    )
    evidence: str = Field(
        default="", description="Evidence narrative for this check"
    )
    source: str = Field(
        default="", description="Data source citation"
    )
    factors: list[str] = Field(
        default_factory=lambda: [],
        description="Factor IDs this check maps to (F1-F10)"
    )
    section: int = Field(default=0, description="Worksheet section 1-6")
    needs_calibration: bool = Field(
        default=False, description="NEEDS CALIBRATION marker per SECT7-11"
    )
```

### Chunked Check Execution

```python
# check_engine.py
CHUNK_SIZE = 50  # Process checks in batches for progress reporting

def execute_checks(
    checks: list[dict[str, Any]],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> list[CheckResult]:
    """Execute all checks in chunked batches."""
    results: list[CheckResult] = []
    auto_checks = [c for c in checks if c.get("execution_mode") == "AUTO"]

    for i in range(0, len(auto_checks), CHUNK_SIZE):
        chunk = auto_checks[i:i + CHUNK_SIZE]
        for check in chunk:
            data = map_check_data(check["id"], check, extracted)
            result = evaluate_check(check, data)
            results.append(result)
        logger.info("Processed checks %d-%d of %d",
                     i + 1, min(i + CHUNK_SIZE, len(auto_checks)),
                     len(auto_checks))

    return results
```

### Tier Classification from Quality Score

```python
# tier_classification.py
from do_uw.models.scoring import Tier, TierClassification

def classify_tier(
    quality_score: float,
    tier_config: list[dict[str, Any]],
) -> TierClassification:
    """Assign tier based on quality score using scoring.json boundaries."""
    for tier_def in tier_config:
        if tier_def["min_score"] <= quality_score <= tier_def["max_score"]:
            return TierClassification(
                tier=Tier(tier_def["tier"]),
                score_range_low=tier_def["min_score"],
                score_range_high=tier_def["max_score"],
                probability_range=tier_def.get("probability_range", ""),
                pricing_multiplier=tier_def.get("pricing_multiplier", ""),
                action=tier_def.get("action", ""),
            )
    # Fallback for score exactly 0
    return TierClassification(
        tier=Tier.NO_TOUCH, score_range_low=0, score_range_high=10,
    )
```

### Pattern Detection

```python
# pattern_detection.py
def detect_pattern(
    pattern_config: dict[str, Any],
    extracted: ExtractedData,
    check_results: dict[str, CheckResult],
) -> PatternMatch:
    """Evaluate a single composite pattern against available data."""
    pattern_id = pattern_config["id"]
    triggers = pattern_config["trigger_conditions"]
    matched_triggers: list[str] = []

    for trigger in triggers:
        if "any_of" in trigger:
            # OR logic: any sub-condition matches
            for sub in trigger["any_of"]:
                if _evaluate_trigger_condition(sub, extracted):
                    matched_triggers.append(sub.get("description", ""))
                    break
        elif "field" in trigger:
            # Simple field comparison
            if _evaluate_trigger_condition(trigger, extracted):
                matched_triggers.append(trigger.get("description", ""))

    # Check if enough triggers matched
    min_triggers = _get_min_trigger_count(triggers)
    detected = len(matched_triggers) >= min_triggers

    severity = _compute_severity(pattern_config, matched_triggers, extracted)
    score_impact = _compute_score_impact(pattern_config, severity) if detected else {}

    return PatternMatch(
        pattern_id=pattern_id,
        pattern_name=pattern_config.get("name", ""),
        detected=detected,
        severity=severity,
        triggers_matched=matched_triggers,
        score_impact=score_impact,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic scoring in one function (predecessor: 9,445-line file) | Config-driven scoring with factors loaded from JSON | Phase 1 knowledge migration | All weights/thresholds in brain/scoring.json |
| 4 competing scoring definitions (predecessor) | Single authoritative scoring.json | Phase 1 consolidation | One definition, one location |
| Hardcoded thresholds in code | Sector-aware baselines from sectors.json | Phase 1 | Sector-contextual scoring |

**What's established:**
- brain/scoring.json: 10 factors, rules, multipliers, tier boundaries -- COMPLETE
- brain/patterns.json: 17 patterns with trigger conditions -- COMPLETE
- brain/red_flags.json: 11 CRF gates with ceilings -- COMPLETE
- brain/sectors.json: Sector baselines for SI, volatility, leverage, guidance -- COMPLETE
- brain/checks.json: 359 checks with data locations and threshold types -- COMPLETE
- models/scoring.py: Pydantic output models (FactorScore, PatternMatch, RedFlagResult, ScoringResult, TierClassification, Tier) -- COMPLETE
- ConfigLoader: Loads and validates all 5 brain files -- COMPLETE

**What needs building:**
- stages/analyze/: Check engine, data mappers, check execution
- stages/score/: Factor scoring, pattern detection, CRF application, tier classification, allegation mapping, claim probability, severity model, tower positioning

## Data Flow Architecture

### Input Data Map (what ANALYZE/SCORE reads from state.extracted)

| Domain | State Path | Key Fields Used by Scoring |
|--------|-----------|---------------------------|
| **Financial** | `extracted.financials` | statements, distress (z-score, m-score), earnings_quality, liquidity, leverage, debt_structure, audit (going_concern, restatements, MW, opinion) |
| **Market** | `extracted.market` | stock (decline_from_high, volatility_90d, single_day_events), insider_trading (cluster, ceo_cfo_pct_sold), short_interest (vs_sector_ratio, reports), earnings_guidance (misses, consecutive), capital_markets (IPO/SPAC/MA), adverse_events |
| **Governance** | `extracted.governance` | executives (tenure, interim), board (independence, duality), compensation (say_on_pay), ownership (activists, dual_class), sentiment (tone), coherence |
| **Litigation** | `extracted.litigation` | active_scas, sec_enforcement_pipeline, derivative_suits, regulatory_proceedings, defense_assessment, industry_patterns, sol_windows, contingent_liabilities |
| **Company** | `state.company` | identity (sector, market_cap, sic_code, years_since_ipo) |

### Output Data Map (what ANALYZE/SCORE writes to state)

| Stage | State Path | What's Written |
|-------|-----------|----------------|
| ANALYZE | `state.analysis` | checks_executed, checks_passed, checks_failed, checks_skipped, check_results (dict by ID), patterns_detected (list of IDs) |
| SCORE | `state.scoring` | composite_score, quality_score, total_risk_points, factor_scores (10), red_flags (11), tier, patterns_detected (with full PatternMatch), allegation_mapping, claim_probability, severity_scenarios, tower_recommendation, risk_type, red_flag_summary |

### Processing Pipeline (execution order within phases)

```
ANALYZE Stage:
  1. Load brain config (ConfigLoader.load_all())
  2. Validate extracted data exists
  3. Execute checks in chunks (359 AUTO + skip MANUAL_ONLY/SECTOR_CONDITIONAL)
     - For each check: map data -> evaluate threshold -> produce CheckResult
  4. Store results in state.analysis

SCORE Stage:
  1. Load brain config
  2. Evaluate 11 CRF gates -> RedFlagResult[] (check FIRST, per processing_rules)
  3. Score 10 factors (scoring.json rules against extracted data)
  4. Detect 17 patterns -> PatternMatch[] (patterns.json triggers)
  5. Apply pattern modifiers to factor scores
  6. Cap each factor at max_points
  7. Compute composite_score = 100 - sum(factor_points)
  8. Apply CRF ceilings -> quality_score = MIN(composite, lowest_ceiling)
  9. Classify tier from quality_score
  10. Classify risk type (SECT7-04)
  11. Map allegations to 5 theories (SECT7-05)
  12. Compute claim probability band (SECT7-07)
  13. Model loss severity scenarios (SECT7-08)
  14. Recommend tower position (SECT7-09)
  15. Compile red flag summary (SECT7-10)
  16. Store everything in state.scoring
```

## Requirement-to-Implementation Mapping

| Requirement | Implementation Location | Key Decisions |
|-------------|------------------------|---------------|
| SECT7-01: 10-Factor Score | `score/factor_scoring.py` | Rules from scoring.json factors{}. Each factor has dedicated evaluator function. |
| SECT7-02: 17 Patterns | `score/pattern_detection.py` | Trigger conditions from patterns.json. Pattern names map (see mapping below). |
| SECT7-03: 11 CRF Gates | `score/red_flag_gates.py` | From red_flags.json + scoring.json critical_red_flag_ceilings. Normalize CRF IDs. |
| SECT7-04: Risk Type | `score/allegation_mapping.py` | 7 archetypes from checks.json BIZ.CLASS.primary threshold values. |
| SECT7-05: Allegation Mapping | `score/allegation_mapping.py` | 5 theories (A-E) from patterns.json allegation_types. Map all findings. |
| SECT7-06: Claims Correlation | `score/factor_scoring.py` | historical_lift values from scoring.json factors. Integrated into factor weights. |
| SECT7-07: Claim Probability | `score/tier_classification.py` | Tier probability_range from scoring.json tiers[]. Base rate from sectors.json. |
| SECT7-08: Loss Severity | `score/severity_model.py` | DDL from market cap + decline. Settlement ratios from scoring.json severity_ranges. |
| SECT7-09: Tower Position | `score/severity_model.py` | Tower positions from scoring.json tower_positions. Side A from financial distress. |
| SECT7-10: Red Flag Summary | `score/red_flag_gates.py` or ScoreStage | Consolidate all flagged items by severity tier. |
| SECT7-11: NEEDS CALIBRATION | All scoring files | Mark every configurable parameter. CheckResult.needs_calibration field. |

### Pattern Name Mapping (SECT7-02 names to patterns.json IDs)

| SECT7-02 Name | patterns.json ID | Notes |
|---------------|------------------|-------|
| EVENT_COLLAPSE | PATTERN.STOCK.EVENT_COLLAPSE | Direct match |
| CASCADE | PATTERN.STOCK.CASCADE | Direct match |
| PEER_DIVERGENCE | PATTERN.STOCK.PEER_DIVERGENCE | Direct match |
| DEATH_SPIRAL | PATTERN.STOCK.DEATH_SPIRAL | Direct match |
| SHORT_ATTACK | PATTERN.STOCK.SHORT_ATTACK | Direct match |
| INFORMED_TRADING | PATTERN.STOCK.INFORMED_TRADING | Direct match |
| SUSTAINABILITY_RISK | PATTERN.BIZ.SUSTAINABILITY_RISK | Direct match |
| CONCENTRATION_COMPOSITE | PATTERN.BIZ.CONCENTRATION | Name differs, same pattern |
| AI_WASHING_RISK | *Not in patterns.json* | Req'd by SECT7-02 but no config. Needs definition. |
| DISCLOSURE_QUALITY_RISK | PATTERN.FWRD.DISCLOSURE_QUALITY | Name differs, same pattern |
| NARRATIVE_COHERENCE_RISK | PATTERN.FWRD.NARRATIVE_COHERENCE | Name differs, same pattern |
| CATALYST_RISK | PATTERN.FWRD.CATALYST_RISK | Direct match |
| GUIDANCE_EROSION | PATTERN.FIN.GUIDANCE_TRACK_RECORD | Name differs, same concept |
| LIQUIDITY_STRESS | PATTERN.FIN.LIQUIDITY_STRESS | Direct match |
| EARNINGS_QUALITY_DETERIORATION | *No exact match* | Could map to PATTERN.GOV.CREDIBILITY_RISK or needs new config |
| TURNOVER_STRESS | PATTERN.GOV.TURNOVER_STRESS | Direct match |
| PROXY_ADVISOR_RISK | PATTERN.GOV.PROXY_ADVISOR_RISK | Direct match |

**Note on missing patterns:** AI_WASHING_RISK and EARNINGS_QUALITY_DETERIORATION are listed in SECT7-02 requirements but have no definitions in patterns.json. Two options: (1) add them to patterns.json in Phase 6 Plan 1 with trigger conditions, or (2) defer to a later phase and document as "pattern stub." Recommend option 1 -- define minimal trigger conditions based on available extracted data. GROWTH_TRAJECTORY (PATTERN.BIZ.GROWTH_TRAJECTORY) is in patterns.json but not in the SECT7-02 list -- include it anyway since it's defined.

## Model Expansion Needs

The existing `ScoringResult` model (models/scoring.py, 220 lines) needs expansion for SECT7-04 through SECT7-09. Fields to add:

```python
# Additional fields for ScoringResult
risk_type: RiskTypeClassification | None    # SECT7-04
allegation_mapping: AllegationMapping | None # SECT7-05
claim_probability: ClaimProbability | None   # SECT7-07
severity_scenarios: SeverityScenarios | None # SECT7-08
tower_recommendation: TowerRecommendation | None  # SECT7-09
red_flag_summary: RedFlagSummary | None      # SECT7-10
calibration_notes: list[str]                 # SECT7-11
```

These sub-models should be defined in models/scoring.py if the file stays under 500 lines. If not, split to models/scoring_output.py. Current scoring.py is 220 lines; adding ~6 new models at ~30 lines each = ~400 lines total. Should fit.

## Check Execution Strategy

### Execution Modes

| Mode | Count | Handling |
|------|-------|----------|
| AUTO | 351 | Execute automatically with available data |
| SECTOR_CONDITIONAL | 2 | Execute only if company matches the sector condition |
| MANUAL_ONLY | 3 | Skip in automated pipeline, mark as MANUAL_REVIEW_NEEDED |
| FALLBACK_ONLY | 3 | Execute only when primary data source failed |

### Data Availability Handling

For each check:
1. Identify required_data sources
2. Check if the corresponding extracted data exists in state
3. If ALL required data is present: evaluate the check
4. If ANY required data is missing: mark SKIPPED with reason
5. Never evaluate a check with partial data as CLEAR

### Threshold Evaluation by Type

| Type | Count | Evaluation Strategy |
|------|-------|-------------------|
| tiered | 309 | Compare value against red/yellow/clear thresholds. Many are qualitative -- use extracted proxy data. |
| info | 19 | Informational only -- report value, no pass/fail |
| percentage | 10 | Numeric comparison with percentage thresholds |
| pattern | 6 | Defer to pattern detection in SCORE stage |
| classification | 5 | Assign to one of defined categories |
| value | 4 | Simple value comparison |
| count | 2 | Count-based threshold |
| boolean | 2 | True/false evaluation |
| search | 1 | Search result presence check |
| multi_period | 1 | Multi-quarter trend evaluation |

## Open Questions

1. **AI_WASHING_RISK pattern definition**
   - What we know: SECT7-02 requires it, but patterns.json has no definition
   - What's unclear: What trigger conditions should be used? The company profile extractor may have relevant data about AI claims
   - Recommendation: Define a minimal pattern in patterns.json during Plan 1 or defer and document as stub. Use available data from company profile (business description mentions of "AI" + revenue not from AI products). LOW confidence in any trigger conditions we define.

2. **EARNINGS_QUALITY_DETERIORATION pattern definition**
   - What we know: SECT7-02 requires it, no exact match in patterns.json
   - What's unclear: Whether CREDIBILITY_RISK covers this or it's truly distinct
   - Recommendation: Create a new pattern entry using earnings_quality extractor data (accruals_ratio, ocf_to_ni divergence, DSO trends). The data is available from Phase 3.

3. **Qualitative check evaluation (6 conditions from Phase 1 todo)**
   - What we know: 6 pattern trigger conditions need NLP/manual evaluation (noted in STATE.md pending todos)
   - What's unclear: Which 6 exactly, and whether Phase 4 extractors (sentiment, coherence) provide sufficient proxy data
   - Recommendation: Use extracted proxy signals where available. Mark remaining as MANUAL_REVIEW_NEEDED. Do not build NLP in ANALYZE/SCORE stages.

4. **Check-to-extracted-data mapping completeness**
   - What we know: 359 checks reference data by source type (SEC_10K, MARKET_PRICE, etc.) but the actual field paths in the Pydantic model tree are different
   - What's unclear: How many checks will have unmappable data (extracted data doesn't cover what the check needs)
   - Recommendation: Build the mapper incrementally. Start with the highest-impact checks (those mapping to factors F1-F3 with max points 20/15/12). Log unmappable checks as SKIPPED. Expect 50-70% check execution coverage in v1 -- the remaining checks need data that may not be available from current extractors.

5. **SECT7-06 Claims Correlation implementation**
   - What we know: The requirement says "methodology to be determined -- may integrate directly into factor scoring weights"
   - What's unclear: Whether this is a separate scoring layer or just the historical_lift values in scoring.json
   - Recommendation: The historical_lift values in scoring.json factors ARE the claims correlation weights. SECT7-06 is already implemented by the factor weight structure. Document this and mark as "integrated into factor scoring."

## Plan Decomposition Recommendation

### Plan 06-01: ANALYZE Stage -- Check Engine and Data Mappers
**Scope:** AnalyzeStage implementation, CheckResult model, check execution engine, data mappers, chunked processing
**Wave:** 1 (foundation)
**Files:** ~4 new files in stages/analyze/ + test file
**Complexity:** HIGH (359 checks to map)
**Key risk:** Data mapper coverage -- not all checks will have mappable data

### Plan 06-02: SCORE Stage -- Factor Scoring, CRF, and Tier
**Scope:** ScoreStage implementation, 10-factor scoring, 11 CRF gates, tier classification, model expansion
**Wave:** 2 (depends on ANALYZE completion for check results)
**Files:** ~4 new files in stages/score/ + model expansion + test file
**Complexity:** HIGH (complex scoring rules with multipliers, caps, and ceilings)
**Key risk:** Scoring rule interpretation -- some rules are ambiguous

### Plan 06-03: Patterns, Allegation Mapping, Severity, Tower
**Scope:** 17 pattern detectors, allegation mapping, risk type, claim probability, severity model, tower recommendation, red flag summary, pipeline wiring, integration tests
**Wave:** 3 (depends on SCORE factor infrastructure)
**Files:** ~4 new files in stages/score/ + pipeline test updates
**Complexity:** MEDIUM-HIGH (patterns are well-defined in JSON, severity/tower are config-driven)
**Key risk:** Pattern-to-data mapping for 17 patterns with different trigger structures

## Sources

### Primary (HIGH confidence)
- `/Users/gorlin/projects/research/src/do_uw/brain/scoring.json` -- 10-factor scoring model with all rules, weights, thresholds, tiers, multipliers, and severity ranges
- `/Users/gorlin/projects/research/src/do_uw/brain/patterns.json` -- 17 composite patterns with trigger conditions, severity levels, and score impacts
- `/Users/gorlin/projects/research/src/do_uw/brain/red_flags.json` -- 11 CRF gates with ceiling values, escalation triggers, and processing rules
- `/Users/gorlin/projects/research/src/do_uw/brain/checks.json` -- 359 checks with data locations, threshold types, factor mappings, and execution modes (9,215 lines)
- `/Users/gorlin/projects/research/src/do_uw/brain/sectors.json` -- Sector baselines for SI, volatility, leverage, guidance, insider trading
- `/Users/gorlin/projects/research/src/do_uw/models/scoring.py` -- Existing Pydantic output models (FactorScore, PatternMatch, RedFlagResult, ScoringResult, TierClassification)
- `/Users/gorlin/projects/research/src/do_uw/models/state.py` -- AnalysisState with AnalysisResults placeholder and ExtractedData
- `/Users/gorlin/projects/research/src/do_uw/config/loader.py` -- ConfigLoader with load_all() and validation
- `/Users/gorlin/projects/research/.planning/REQUIREMENTS.md` -- SECT7-01 through SECT7-11 requirements
- `/Users/gorlin/projects/research/.planning/ROADMAP.md` -- Phase 6 success criteria and plan stubs

### Secondary (MEDIUM confidence)
- Existing extractor patterns from stages/extract/ (sub-orchestrator pattern, ExtractionReport)
- Pipeline orchestrator pattern from pipeline.py (StageCallbacks, config passthrough)

### Tertiary (LOW confidence)
- Check-to-data mapper coverage estimates (50-70% coverage based on manual review of check IDs vs extracted model fields)
- Line count estimates for new files (based on complexity analysis)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed, all infrastructure exists
- Architecture: HIGH -- config-driven scoring is well-defined by brain/ JSON files
- Data flow: HIGH -- input/output models exist, processing order documented in brain/ files
- Check mapping: MEDIUM -- 359 checks need individual data mappings, coverage unknown until built
- Pitfalls: HIGH -- based on direct analysis of config file structures and Pydantic model trees

**Research date:** 2026-02-08
**Valid until:** No expiration (internal codebase research, not external library)
