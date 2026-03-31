# Phase 12: Actuarial Pricing Model - Research

**Researched:** 2026-02-09
**Domain:** Actuarial loss modeling, D&O insurance pricing, tower layer economics
**Confidence:** MEDIUM (domain knowledge verified against multiple sources; no novel libraries required)

## Summary

Phase 12 transforms the system's risk scoring output into an actuarial loss model that answers "what should this D&O coverage cost?" The core computation is: **Expected Loss = Filing Probability x Expected Severity + Defense Costs**, with layer-specific pricing derived via Increased Limits Factor (ILF) curves. This is not greenfield -- the system already has ~80% of the building blocks: inherent risk baseline (Phase 7, `inherent_risk.py`), severity scenarios (Phase 6, `severity_model.py`), claim probability bands (Phase 6, `scoring_output.py`), tower positioning (Phase 6/7), rate decay curves (Phase 10.1, `rate_decay.json`), and market position analytics (Phase 10, `pricing_analytics.py`). Phase 12 connects these into a coherent pricing model and calibrates against accumulated market data.

The standard actuarial approach for D&O pricing uses a **frequency-severity model**: the annual filing probability (frequency) is multiplied by the conditional expected settlement amount (severity) to produce a pure loss cost. Defense costs (ALAE) are added as a percentage of indemnity. Layer-specific pricing uses ILF curves -- power functions of the form `ILF(L) = (L/B)^alpha` where alpha typically ranges 0.3-0.5 for D&O -- to allocate total expected loss across tower layers. Premium is then derived from expected loss via a loss ratio target (typically 50-65% for D&O).

**Primary recommendation:** Build the actuarial model as pure computation functions in `stages/score/` (where severity_model.py already lives), with a new `ActuarialPricing` Pydantic model on `ScoringResult`. Use existing config infrastructure for all parameters. Calibrate against PricingStore market data when available. No new dependencies needed -- stdlib `math` and `statistics` suffice.

## Standard Stack

### Core

No new external libraries are needed. The actuarial model is pure arithmetic built on existing infrastructure.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `math` | stdlib | Power functions, logarithms for ILF curves | No dependency needed |
| `statistics` | stdlib | Median, mean, stdev for calibration | Already used in pricing_analytics.py |
| `pydantic` | >=2.10 | Output models | Already a dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sqlalchemy` | >=2.0 | Query PricingStore for calibration data | Already a dependency, used for market data calibration |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib math | scipy.stats (lognorm, pareto distributions) | scipy adds 50MB+ dependency for marginal improvement; lognormal/pareto fitting would be more actuarially rigorous but system has no loss triangle data to fit distributions against. If future phases need distribution fitting, add scipy then |
| Pure functions | GEMAct Python package | Full actuarial modeling package, massive overkill for this use case |
| Config JSON | Hardcoded parameters | Violates CLAUDE.md anti-hardcoding rule; all parameters must be in config |

**Installation:**
```bash
# No new packages needed
uv sync  # existing dependencies suffice
```

## Architecture Patterns

### Recommended Project Structure

```
src/do_uw/
  stages/score/
    severity_model.py          # EXISTING: severity scenarios (391L)
    actuarial_model.py         # NEW: expected loss computation (~300L)
    actuarial_layer_pricing.py # NEW: ILF curves, layer allocation (~300L)
  stages/benchmark/
    inherent_risk.py           # EXISTING: filing probability (267L)
    market_position.py         # EXISTING: market intelligence (172L)
  models/
    scoring_output.py          # EXTEND: add ActuarialPricing model (~50L addition)
  config/
    actuarial.json             # NEW: all model parameters
    rate_decay.json            # EXISTING: layer decay factors (already has ILF-like data)
  knowledge/
    pricing_analytics.py       # EXISTING: market position engine (395L)
```

### Pattern 1: Frequency-Severity Expected Loss Model

**What:** The standard actuarial decomposition: Expected Loss = E[Frequency] x E[Severity|claim] + E[ALAE]
**When to use:** Computing the total expected cost of a D&O claim for a given company
**How it maps to existing code:**

```python
# From inherent_risk.py: company_adjusted_rate_pct is our FREQUENCY
# e.g., TECH sector, LARGE cap, WRITE tier -> 7.68% annual filing probability

# From severity_model.py: scenarios give us SEVERITY at percentiles
# e.g., $15M (p25), $27M (p50), $52.5M (p75), $105M (p95)

# EXPECTED LOSS combines them:
expected_loss = filing_probability * conditional_severity + defense_costs
# e.g., 0.0768 * $27M * (1 + 0.20) = $2.49M expected annual loss

# PREMIUM derives from expected loss via loss ratio target:
indicated_premium = expected_loss / target_loss_ratio
# e.g., $2.49M / 0.55 = $4.53M indicated total premium
```

### Pattern 2: ILF Power Curve for Layer Pricing

**What:** Allocates total expected loss across tower layers using a power function
**When to use:** Computing rate-on-line for each layer (primary, 1st excess, 2nd excess, etc.)
**Formula:**

```python
# ILF(L) = (L / B)^alpha  where:
#   L = policy limit
#   B = basic limit (typically primary layer limit)
#   alpha = power parameter (0.3-0.5 for D&O, from config)
#
# Layer expected loss = [ILF(attachment + limit) - ILF(attachment)] / ILF(basic_limit)
#
# For a $10M xs $10M layer with alpha=0.40:
# ILF(20M) = (20/10)^0.40 = 1.320
# ILF(10M) = (10/10)^0.40 = 1.000
# Layer factor = (1.320 - 1.000) / 1.000 = 0.320
# Layer expected loss = primary_expected_loss * 0.320

def compute_ilf(limit: float, basic_limit: float, alpha: float) -> float:
    """Compute Increased Limits Factor via power curve."""
    if basic_limit <= 0 or limit <= 0:
        return 1.0
    return (limit / basic_limit) ** alpha

def compute_layer_loss(
    attachment: float,
    layer_limit: float,
    basic_limit: float,
    primary_expected_loss: float,
    alpha: float,
) -> float:
    """Compute expected loss for a specific tower layer."""
    ilf_top = compute_ilf(attachment + layer_limit, basic_limit, alpha)
    ilf_bottom = compute_ilf(attachment, basic_limit, alpha) if attachment > 0 else 1.0
    ilf_basic = compute_ilf(basic_limit, basic_limit, alpha)
    layer_factor = (ilf_top - ilf_bottom) / ilf_basic
    return primary_expected_loss * layer_factor
```

### Pattern 3: Calibration Against Market Data

**What:** Adjusts model parameters using accumulated PricingStore data
**When to use:** When the PricingStore has sufficient data (3+ quotes in the segment)
**How:**

```python
# Query MarketPositionEngine for peer segment rates
# Compare model-indicated ROL vs observed market ROL
# Compute calibration factor = observed_median_rol / model_indicated_rol
# Apply as a credibility-weighted blend:
#   credibility = min(1.0, sqrt(n / credibility_standard))
#   calibrated_rate = credibility * market_rate + (1 - credibility) * model_rate
# Where credibility_standard = 50 (from config)
```

### Pattern 4: Config-Driven Parameters

**What:** All model parameters in actuarial.json, not hardcoded
**When to use:** Every tunable parameter

```json
{
  "description": "Actuarial pricing model parameters. NEEDS CALIBRATION.",
  "defense_cost_factors": {
    "description": "Defense costs as % of indemnity by case type",
    "standard_sca": 0.20,
    "complex_sca": 0.25,
    "sec_enforcement": 0.30,
    "derivative": 0.15,
    "default": 0.20
  },
  "ilf_parameters": {
    "description": "ILF power curve alpha by market segment",
    "standard": 0.40,
    "large_cap": 0.38,
    "small_cap": 0.45,
    "biotech": 0.35,
    "financial_services": 0.42
  },
  "loss_ratio_targets": {
    "description": "Target loss ratio for premium derivation",
    "primary": 0.55,
    "low_excess": 0.50,
    "mid_excess": 0.45,
    "high_excess": 0.40,
    "side_a": 0.35
  },
  "expense_loads": {
    "acquisition_cost_pct": 0.15,
    "overhead_pct": 0.05,
    "profit_margin_pct": 0.05
  },
  "credibility": {
    "standard": 50,
    "minimum_quotes": 3
  },
  "model_label": "MODEL-INDICATED: Not prescriptive. Underwriter sets final price."
}
```

### Anti-Patterns to Avoid

- **Black-box pricing:** Every computation must show its inputs, formula, and assumptions. The model output includes a full audit trail of how the number was derived.
- **Precision theater:** D&O pricing data is sparse. Don't show 6 decimal places. Round to meaningful precision ($thousands for premium, basis points for ROL).
- **Claiming prescriptive authority:** Every output must be labeled "MODEL-INDICATED" not "RECOMMENDED PRICE". The underwriter decides.
- **Ignoring market data:** When PricingStore has data, use credibility-weighted calibration. Pure model output without market context is less useful.
- **Hardcoded parameters:** All alpha values, defense cost percentages, loss ratio targets must be in config JSON.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filing probability | New probability model | Existing `inherent_risk.py` `compute_inherent_risk_baseline()` | Already computes `company_adjusted_rate_pct` with sector, cap, and score adjustments |
| Severity distribution | Custom distribution fitting | Existing `severity_model.py` `model_severity()` | Already computes 25th/50th/75th/95th percentile scenarios with config-driven parameters |
| Market position stats | Custom statistics | Existing `pricing_analytics.py` `compute_market_position()` | Already computes median, CI, trends with t-distribution |
| Rate decay between layers | Custom decay calculation | Existing `pricing_inference.py` `infer_layer_rate()` | Already has config-driven decay factors for 10 excess layers + Side A |
| Confidence intervals | Manual CI computation | Existing `_t_value()` + `_classify_confidence()` in pricing_analytics.py | Already handles t-distribution lookup with interpolation |

**Key insight:** The system already has the individual building blocks. Phase 12's primary job is to compose them into a coherent pricing model with an ILF layer allocation mechanism, add calibration against market data, and produce transparent output. The actuarial model is ~60% existing code reuse and ~40% new composition logic.

## Common Pitfalls

### Pitfall 1: Overfitting to Sparse Data

**What goes wrong:** D&O claim data is inherently sparse (3.9% filing rate means most companies never have a claim). Models that try to fit precise distributions to small samples produce overconfident results.
**Why it happens:** Temptation to use sophisticated statistical methods (maximum likelihood, Bayesian inference) when the data doesn't support them.
**How to avoid:** Use simple parametric approaches (power curves with sector-level alpha) rather than per-company fitting. Clearly label confidence levels. Use credibility weighting when blending model vs market data.
**Warning signs:** Confidence intervals narrower than +/-30% for segments with <20 data points.

### Pitfall 2: Confusing Model Output with Market Price

**What goes wrong:** Model produces $X as "expected premium" and underwriter treats it as the price, ignoring market dynamics, relationship factors, capacity constraints.
**Why it happens:** Presentation doesn't clearly distinguish model indication from market reality.
**How to avoid:** Every output field is prefixed/suffixed with "MODEL-INDICATED". Include market comparison when available. Show the range, not a point estimate.
**Warning signs:** Single-value premium output without range or confidence interval.

### Pitfall 3: Double-Counting Existing Scoring Adjustments

**What goes wrong:** Severity model already applies tier multipliers. Filing probability already applies score multiplier. If the actuarial model applies another risk adjustment on top, it double-counts.
**Why it happens:** The model touches the same state data that upstream stages already processed.
**How to avoid:** Map exactly which adjustments happen where. The actuarial model should consume the OUTPUTS of existing stages, not re-derive them. Document the flow: `inherent_risk.company_adjusted_rate_pct` IS the frequency input, not a starting point for further adjustment.
**Warning signs:** Expected loss values that seem unreasonably high or low compared to market rates.

### Pitfall 4: Ignoring the 500-Line Rule

**What goes wrong:** Actuarial model logic is naturally complex with many interacting computations. Easy to end up with a monolithic file.
**Why it happens:** All the pricing logic "feels like one thing" so it goes in one file.
**How to avoid:** Split from the start: `actuarial_model.py` (expected loss computation, ~300L) + `actuarial_layer_pricing.py` (ILF curves, layer allocation, premium derivation, ~300L). Config in `actuarial.json`. Models in existing `scoring_output.py`.
**Warning signs:** Any file approaching 400 lines during development.

### Pitfall 5: Making ILF Alpha Too Precise

**What goes wrong:** Different alpha values for every sub-industry create an illusion of precision that the data can't support.
**Why it happens:** Actuarial literature discusses alpha variation by line of business.
**How to avoid:** Start with 3-5 alpha values (standard, large_cap, small_cap, biotech, financial_services) in config. Add more only if calibration data supports differentiation. Alpha for D&O typically falls in 0.35-0.45 range.
**Warning signs:** More than 10 alpha values in config without calibration evidence.

## Code Examples

### Expected Loss Computation (Core Formula)

```python
# Source: Standard actuarial frequency-severity model
# Adapted for D&O using existing system outputs

def compute_expected_loss(
    filing_probability_pct: float,
    severity_scenarios: SeverityScenarios,
    defense_cost_pct: float,
    actuarial_config: dict[str, Any],
) -> ExpectedLoss:
    """Compute expected annual loss for a D&O program.

    Uses existing severity scenarios from SCORE stage and filing
    probability from BENCHMARK stage inherent risk baseline.

    Args:
        filing_probability_pct: Annual filing probability (%).
        severity_scenarios: Percentile-based severity from severity_model.
        defense_cost_pct: Defense costs as fraction of indemnity.
        actuarial_config: Full actuarial.json config.

    Returns:
        ExpectedLoss with breakdown by component.
    """
    prob = filing_probability_pct / 100.0

    # Use median (50th percentile) as central severity estimate
    median_severity = _get_scenario_amount(severity_scenarios, 50)
    if median_severity is None:
        return ExpectedLoss(has_data=False)

    # Expected indemnity = probability * conditional severity
    expected_indemnity = prob * median_severity

    # Defense costs as percentage of indemnity
    expected_defense = expected_indemnity * defense_cost_pct

    # Total expected loss
    total_expected = expected_indemnity + expected_defense

    # Scenarios at each percentile
    scenario_losses = []
    for scenario in severity_scenarios.scenarios:
        s_indemnity = prob * scenario.settlement_estimate
        s_defense = s_indemnity * defense_cost_pct
        scenario_losses.append(ScenarioLoss(
            percentile=scenario.percentile,
            label=scenario.label,
            expected_indemnity=s_indemnity,
            expected_defense=s_defense,
            total_expected=s_indemnity + s_defense,
        ))

    return ExpectedLoss(
        has_data=True,
        filing_probability_pct=filing_probability_pct,
        median_severity=median_severity,
        defense_cost_pct=defense_cost_pct,
        expected_indemnity=expected_indemnity,
        expected_defense=expected_defense,
        total_expected_loss=total_expected,
        scenario_losses=scenario_losses,
        methodology_note=actuarial_config.get(
            "model_label",
            "MODEL-INDICATED: Not prescriptive.",
        ),
    )
```

### ILF Layer Pricing

```python
# Source: Actuarial ILF methodology (CAS study notes, Riebesell power curves)
# Applied to D&O tower structure

def price_tower_layers(
    expected_loss: ExpectedLoss,
    tower_structure: list[LayerSpec],
    alpha: float,
    loss_ratio_targets: dict[str, float],
    actuarial_config: dict[str, Any],
) -> list[LayerPricing]:
    """Compute indicated premium for each tower layer using ILF curves.

    Args:
        expected_loss: Total expected loss from compute_expected_loss.
        tower_structure: List of layer specifications (attachment, limit, type).
        alpha: ILF power curve parameter.
        loss_ratio_targets: Target loss ratios by layer type.
        actuarial_config: Full actuarial.json config.

    Returns:
        List of LayerPricing with indicated premium and ROL.
    """
    if not expected_loss.has_data or not tower_structure:
        return []

    basic_limit = tower_structure[0].limit  # Primary layer limit
    primary_loss = expected_loss.total_expected_loss
    results: list[LayerPricing] = []

    for layer in tower_structure:
        # ILF factor for this layer
        layer_factor = _compute_layer_factor(
            layer.attachment, layer.limit, basic_limit, alpha
        )
        layer_expected_loss = primary_loss * layer_factor

        # Premium from loss ratio target
        lr_key = _layer_type_key(layer.layer_type)
        target_lr = loss_ratio_targets.get(lr_key, 0.55)
        indicated_premium = layer_expected_loss / target_lr if target_lr > 0 else 0.0

        # Rate on line
        rol = indicated_premium / layer.limit if layer.limit > 0 else 0.0

        results.append(LayerPricing(
            layer_type=layer.layer_type,
            layer_number=layer.layer_number,
            attachment=layer.attachment,
            limit=layer.limit,
            ilf_factor=layer_factor,
            expected_loss=layer_expected_loss,
            target_loss_ratio=target_lr,
            indicated_premium=indicated_premium,
            indicated_rol=rol,
            confidence_note=_confidence_note(expected_loss),
        ))

    return results
```

### Market Calibration

```python
# Source: Actuarial credibility theory (Buhlmann)
# Simplified for D&O market data

def calibrate_against_market(
    model_premium: float,
    model_rol: float,
    market_position: MarketPosition,
    credibility_config: dict[str, Any],
) -> CalibratedPricing:
    """Blend model indication with market data using credibility weighting.

    Args:
        model_premium: Model-indicated premium.
        model_rol: Model-indicated rate-on-line.
        market_position: Market position from MarketPositionEngine.
        credibility_config: Credibility parameters from actuarial.json.

    Returns:
        CalibratedPricing with blended result and audit trail.
    """
    if market_position.confidence_level == "INSUFFICIENT":
        return CalibratedPricing(
            model_indicated_premium=model_premium,
            model_indicated_rol=model_rol,
            market_median_rol=None,
            credibility=0.0,
            calibrated_rol=model_rol,
            calibrated_premium=model_premium,
            calibration_source="MODEL_ONLY",
        )

    n = market_position.peer_count
    standard = credibility_config.get("standard", 50)
    z = min(1.0, sqrt(n / standard))  # Buhlmann credibility

    market_rol = market_position.median_rate_on_line or model_rol
    calibrated_rol = z * market_rol + (1 - z) * model_rol

    # Derive premium from calibrated ROL (assumes same limit)
    limit_ratio = model_premium / model_rol if model_rol > 0 else 0.0
    calibrated_premium = calibrated_rol * limit_ratio

    return CalibratedPricing(
        model_indicated_premium=model_premium,
        model_indicated_rol=model_rol,
        market_median_rol=market_rol,
        credibility=z,
        calibrated_rol=calibrated_rol,
        calibrated_premium=calibrated_premium,
        calibration_source=f"BLENDED (z={z:.2f}, n={n})",
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat per-unit rates | Frequency-severity models | Standard since 1990s | More granular risk differentiation |
| Single ILF table | Power curve with alpha by segment | Standard in London Market | Better excess layer pricing |
| Pure model output | Credibility-weighted blend with market | Always best practice | More accurate indications |
| Point estimates | Range with confidence intervals | Increasing adoption | More honest uncertainty communication |

**Deprecated/outdated:**
- Single loss ratio approach for D&O: Does not account for catastrophic tail risk in securities litigation
- Linear interpolation for excess layer rates: Power curves are more actuarially sound than the existing `rate_decay.json` linear factors

## Integration Points with Existing Code

### Inputs (all existing, no new acquisition needed)

| Input | Source | Field Path |
|-------|--------|------------|
| Filing probability | `inherent_risk.py` | `executive_summary.inherent_risk.company_adjusted_rate_pct` |
| Severity scenarios | `severity_model.py` | `scoring.severity_scenarios` |
| Tier classification | `tier_classification.py` | `scoring.tier` |
| Market cap | `company.py` | `company.market_cap.value` |
| Sector code | `company.py` | `company.identity.sector` |
| Quality score | `scoring.py` | `scoring.quality_score` |
| Market position | `pricing_analytics.py` | Via `MarketPositionEngine.get_position_for_analysis()` |
| Rate decay factors | `rate_decay.json` | Via `pricing_inference.load_rate_decay_config()` |
| Claim base rates | `sectors.json` | `claim_base_rates` |
| Severity ranges | `scoring.json` | `severity_ranges.by_market_cap` |

### Outputs (new fields on AnalysisState)

The actuarial pricing output should live on `ScoringResult` (not a new top-level state field) since it is derived from scoring outputs. Alternatively, it could be placed on `ExecutiveSummary.deal_context` since it relates to pricing. The better architectural choice is to add an `actuarial_pricing: ActuarialPricing | None` field to `ScoringResult` because:
1. It is computed from scoring outputs (severity, tier, probability)
2. It is consumed by RENDER and Dashboard alongside other scoring data
3. It follows the existing pattern where scoring_output.py holds derived SECT7 models

### Pipeline Integration

The actuarial model computation should happen in the SCORE stage (or BENCHMARK stage, since it needs inherent_risk which is computed in BENCHMARK). The cleanest approach:

1. **SCORE stage** computes severity scenarios and tier (existing)
2. **BENCHMARK stage** computes inherent risk baseline with filing probability (existing)
3. **BENCHMARK stage** also computes actuarial pricing using outputs from steps 1-2 (NEW)
4. Market calibration happens in BENCHMARK since it queries PricingStore (existing pattern from `market_position.py`)

This avoids adding a new pipeline stage and follows the existing pattern where BENCHMARK enriches the analysis with market-relative data.

## Open Questions

1. **Where to store actuarial output on state**
   - What we know: Could go on `ScoringResult.actuarial_pricing` or `ExecutiveSummary.deal_context.actuarial_pricing`
   - What's unclear: Whether the planner will want it on scoring (logically derived from scoring) or executive summary (consumed for deal decisions)
   - Recommendation: Put on `ScoringResult` for consistency with severity_scenarios and tower_recommendation. The render stage can access it from `state.scoring.actuarial_pricing`.

2. **ILF alpha calibration source**
   - What we know: Alpha 0.35-0.45 range for D&O, varies by segment
   - What's unclear: Whether the PricingStore data volume will ever be sufficient to empirically calibrate alpha (requires many observed tower structures)
   - Recommendation: Start with config-driven alpha values from actuarial literature. Add empirical calibration as a future enhancement when PricingStore has 50+ complete tower structures.

3. **Render integration scope**
   - What we know: Phase 12 should produce data. Rendering it in Word/PDF/Dashboard is work.
   - What's unclear: How much render integration to include in Phase 12 vs defer
   - Recommendation: Include basic rendering in the SECT7 section (scoring synthesis) where tower recommendation already lives. Dashboard integration can be a later plan if needed.

4. **Relationship to existing `rate_decay.json`**
   - What we know: rate_decay.json has linear decay factors (excess_1=0.50, excess_2=0.35, etc.)
   - What's unclear: Whether to replace these with ILF-derived factors or keep both systems
   - Recommendation: Keep rate_decay.json for the inference engine (Phase 10.1 feature that fills missing layers from partial data). The ILF model is a parallel pricing approach. They serve different purposes: inference fills gaps, ILF prices from first principles.

5. **Defense cost data quality**
   - What we know: Literature says 15-30% of total D&O loss is defense costs. System currently uses 15/20/25/30% at 25th/50th/75th/95th percentiles.
   - What's unclear: Whether to use a fixed percentage or model defense costs separately based on case type
   - Recommendation: Start with case-type-specific percentages in config (SCA: 20%, SEC enforcement: 30%, derivative: 15%). Add empirical calibration when claims data is available.

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `inherent_risk.py`, `severity_model.py`, `pricing_analytics.py`, `pricing_inference.py`, `scoring.json`, `sectors.json`, `rate_decay.json` -- verified by direct code reading
- CAS Study Notes: Palmer, "Increased Limits Ratemaking for Liability Insurance" (2006) -- standard actuarial reference for ILF methodology
- HandWiki/Wikipedia: ILF formula `ILF(L) = Expected_severity(L) / Expected_severity(B)` -- verified against CAS source

### Secondary (MEDIUM confidence)
- Cornerstone Research: Securities Class Action Settlements 2024 -- median settlement $14M, aggregate $3.7B-$4.75B (source variation by methodology), filing rates 3.9% all-company, 6.1% S&P 500
- NERA 2024 Full-Year Review -- filing counts, dismissal rates, settlement trends
- MatBlas/CARe 2009: Power curve alpha ~0.38 for casualty excess pricing
- D&O Diary, Woodruff Sawyer: 2024 market pricing trends (5.2% average premium decline, soft market)
- Milliman: Casualty actuarial language guide -- frequency x severity = pure premium

### Tertiary (LOW confidence)
- Web search for D&O-specific alpha values -- found range 0.3-0.5 mentioned but no authoritative D&O-specific source
- Defense cost percentages 15-30% -- widely cited but sourced from system's existing configuration (predecessor knowledge), not independently verified against 2024 settlement data
- Loss ratio targets 50-65% -- industry convention but varies significantly by market cycle and carrier

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, pure computation on existing infrastructure
- Architecture: HIGH - follows established patterns (pure functions, config-driven, Pydantic models), fits cleanly into existing BENCHMARK stage
- ILF methodology: MEDIUM - standard actuarial approach, but D&O-specific alpha values are literature-sourced not empirically calibrated
- Calibration approach: MEDIUM - credibility weighting is standard, but effectiveness depends on PricingStore data volume which varies
- Pitfalls: HIGH - well-documented in actuarial literature and learned from predecessor system failures

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable domain, 30-day validity)
