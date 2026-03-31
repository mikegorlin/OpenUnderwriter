# Phase 131: Scoring Depth and Visualizations - Research

**Researched:** 2026-03-23
**Domain:** SVG chart generation, scoring decomposition, probability modeling, scenario analysis
**Confidence:** HIGH

## Summary

Phase 131 transforms the scoring section from a single composite number into a fully decomposed visual risk narrative. The existing codebase has strong foundations: a 10-factor scoring model with sub-components and signal attribution (FactorScore), a radar chart (matplotlib), factor bars (pure SVG), a gauge chart (pure SVG), and context builders that already extract scoring data for templates. The work is primarily additive -- new chart modules (waterfall, tornado), new context builder methods (probability decomposition, scenario generation), and enhanced templates.

The key technical challenge is not the charting (pure SVG for bar charts is straightforward), but the *data computation*: probability decomposition requires extracting 7+ named components from the existing frequency model, and scenario analysis requires simulating factor score changes and re-deriving tiers. Both computations already have partial foundations in `frequency_model.py` (EnhancedFrequency with base_rate, hazard_multiplier, signal_multiplier) and `severity_scenarios` (SeverityScenarios model), but need to be surfaced as individually addressable components.

**Primary recommendation:** Follow established patterns exactly -- pure SVG for waterfall/tornado (like factor_bars.py), matplotlib for radar enhancement (like radar_chart.py), new context builder methods in scorecard_context.py/scoring.py, and Jinja2 template updates. No new dependencies needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Mix approach: pure SVG for waterfall and tornado charts (bar charts are simple geometry, crisp, print-friendly). Matplotlib for radar chart (polar coordinates are hard in raw SVG). Follows existing codebase pattern.
- **D-02:** Dashboard density -- charts sit side-by-side where possible (waterfall + radar on one row), factor cards are compact grids, scenarios in a tight table. Maximum information per screen.
- **D-03:** Show ALL probability components with calibration labels. Calibrated components get source citations (NERA, Cornerstone, SCAC data). Uncalibrated components get clear "ESTIMATED" or "UNCALIBRATED" badges.
- **D-04:** 7+ named components: sector base rate, IPO uplift, market cap tier, volatility adjustment, insider selling signal, litigation history, governance quality. Each shows its contribution (additive/subtractive) to the final probability.
- **D-05:** Company-specific scenarios generated from actual risk profile. If active SCA -> "SCA Escalation" scenario, if earnings volatile -> "Earnings Miss + Drop", if high insider selling -> "Insider Selling Accelerates". 5-7 scenarios per company.
- **D-06:** Each scenario shows: current score, scenario score, tier change (e.g., "70 WRITE -> 85 WALK"), and the score delta.
- **D-07:** Formal research report voice. No factor codes (F1-F10) in prose -- only in chart labels and tables where they serve as cross-references. No system internals in narrative text.
- **D-08:** Factor cards use the dual-voice pattern: factual data + bulleted D&O commentary per factor.

### Claude's Discretion
- SVG dimensions, color palette, print CSS for charts
- Exact probability component calculations and default values for uncalibrated items
- How to derive scenario score impacts (which factors change, by how much)
- Whether to use existing severity_scenarios.html.j2 or create new template
- Tornado chart orientation (horizontal bars ranked by magnitude)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCORE-01 | Waterfall chart showing factor-by-factor score buildup with tier threshold lines | Pure SVG following factor_bars.py pattern; data from extract_scoring() factors list; tier thresholds from scoring.json |
| SCORE-02 | Risk radar/spider chart showing concentration vs distribution | Existing radar_chart.py enhanced with threshold rings; _compute_risk_fractions() already computes values |
| SCORE-03 | Factor detail cards with severity, score, narrative, bullet evidence | Existing factor_detail.html.j2 enhanced with dual-voice (Phase 130 pattern); build_factor_detail_context() provides data |
| SCORE-04 | Dominant risk cluster identification | Computed from factor_scores: group by role dimension, sum points, identify cluster >50% of total |
| SCORE-05 | Zero-scored factors show clean ZER-001 documentation | Existing zero_verification.html.j2 already implements this; verify integration |
| PROB-01 | Decompose probability into 7+ additive/subtractive components | Extract from EnhancedFrequency model components + new decomposition in context builder |
| PROB-02 | Each component has source citation or UNCALIBRATED label | Add calibration_source and is_calibrated fields per component |
| PROB-03 | Components individually auditable and adjustable by underwriter | Display as table with component name, value, direction, source -- adjustment is visual (future UI) |
| SCEN-01 | 5-7 named scenarios per company from actual risk profile | New scenario generator reads factor_scores, patterns, risk flags to select relevant scenarios |
| SCEN-02 | Each scenario shows score impact and tier change | Re-classify tier after applying scenario factor deltas; display current vs scenario |
| SCEN-03 | Tornado chart SVG showing score sensitivity per scenario | Pure SVG horizontal bars sorted by absolute magnitude, center line at current score |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **No bare float()** in render code -- use safe_float() from formatters.py
- **NEVER truncate analytical content** -- no `| truncate()` in templates on evidence, findings, narratives
- **No source file over 500 lines** -- split before it gets there
- **No scoring logic outside stages/score/** -- context builders extract, they don't compute scores
- **No data acquisition outside stages/acquire/** -- all data already in state
- **Pydantic v2** for all data models
- **Type hints on all functions** -- Pyright strict mode
- **ruff for formatting and linting**
- **safe_float() required** for any value from state, dicts, or LLM extraction
- **Brain YAML is source of truth** -- D&O commentary from brain signals, not Python templates
- **Every data point needs source and confidence** in Pydantic models

## Standard Stack

### Core (already in project -- no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | existing | Radar chart (polar coordinates) | Already used for radar_chart.py; complex polar math |
| Pure SVG (Python strings) | N/A | Waterfall chart, tornado chart, factor bars | Established pattern in factor_bars.py, sparklines.py, gauge.py -- crisp, print-friendly, zero dependencies |
| Jinja2 | existing | Template rendering with `| safe` for inline SVG | Already the template engine throughout |
| Pydantic v2 | existing | New models for probability components, scenarios | Project standard for all data models |

### Supporting (already available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| chart_style_registry | existing | Canonical colors, figure sizes | All new charts MUST use resolve_colors() |
| chart_registry.yaml | existing | Declarative chart catalog | Register new charts (waterfall, tornado) |
| chart_helpers.py | existing | save_chart_to_svg(), save_chart_to_bytes() | For radar chart SVG/PNG output |
| design_system.py | existing | Brand colors, risk spectrum | Color references for SVG generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure SVG waterfall | matplotlib bar chart | Heavier, slower, not print-friendly; SVG is better for simple horizontal bars |
| New probability model | Extend ClaimProbability | ClaimProbability is too simple (just band + range); need new ProbabilityDecomposition model |

## Architecture Patterns

### New File Structure
```
src/do_uw/
  stages/render/charts/
    waterfall_chart.py          # NEW: Pure SVG waterfall (score buildup)
    tornado_chart.py            # NEW: Pure SVG tornado (scenario sensitivity)
    radar_chart.py              # ENHANCE: Add threshold rings
  stages/render/context_builders/
    scoring.py                  # ENHANCE: Add waterfall data, probability decomposition
    scorecard_context.py        # ENHANCE: Add scenario analysis
    probability_decomposition.py # NEW: Extract 7+ probability components
    scenario_generator.py       # NEW: Generate company-specific scenarios
  models/
    scoring_output.py           # ENHANCE: Add ProbabilityComponent, ScoreScenario models
  templates/html/sections/scoring/
    waterfall_chart.html.j2     # NEW: Waterfall + radar side-by-side row
    probability_decomposition.html.j2  # NEW: Component table with calibration badges
    scenario_analysis.html.j2   # NEW: Scenario table + tornado chart
    factor_detail.html.j2       # ENHANCE: Dual-voice pattern (D-08)
```

### Pattern 1: Pure SVG Chart Generation (follow factor_bars.py)
**What:** Generate SVG markup as Python strings, return for inline embedding via `| safe`
**When to use:** Bar-based charts (waterfall, tornado) where geometry is simple rectangles + lines
**Example:**
```python
# Source: existing factor_bars.py pattern
def render_waterfall_chart(
    factors: list[dict[str, float]],  # [{name, points, max}]
    total_score: float,
    tier_thresholds: list[dict[str, float]],  # [{tier, score}]
    width: int = 600,
    height: int = 300,
) -> str:
    """Render score waterfall as inline SVG. Returns SVG string."""
    # Build cumulative bar positions
    # Each factor is a horizontal bar showing its contribution
    # Tier thresholds shown as horizontal dashed lines
    parts = [f'<svg viewBox="0 0 {width} {height}" ...>']
    # ... bar generation logic
    parts.append("</svg>")
    return "".join(parts)
```

### Pattern 2: Context Builder Decomposition
**What:** New context builder methods that extract/compute display data from state
**When to use:** When templates need computed values not directly in ScoringResult
**Key constraint:** Context builders EXTRACT and FORMAT -- they do NOT compute scores. Score computation lives in stages/score/. However, *decomposing* existing computed values into display components is a rendering concern.
```python
# In scoring.py or new probability_decomposition.py
def build_probability_decomposition(state: AnalysisState) -> dict[str, Any]:
    """Extract probability components for display."""
    # Reads from state.scoring.claim_probability and
    # state.scoring.hae_result / enhanced frequency data
    # Returns list of {name, value, direction, calibrated, source}
```

### Pattern 3: Scenario Simulation
**What:** Generate hypothetical factor score changes, re-derive composite + tier
**When to use:** SCEN-01/02/03 -- showing "what if" score impacts
**Key insight:** This is NOT new scoring logic. It takes existing factor scores, applies deltas, and re-sums. The deltas are defined by scenario templates (e.g., "SCA Filed" -> F1 = max_points). Tier re-classification uses the same tier_config from scoring.json.
```python
def generate_scenarios(state: AnalysisState) -> list[ScoreScenario]:
    """Generate company-specific scenarios from risk profile."""
    # 1. Read current factor_scores and total
    # 2. Select relevant scenarios based on current risk profile
    # 3. For each scenario: apply factor deltas, re-sum, re-classify tier
    # 4. Return list of ScoreScenario with current/scenario/delta/tier_change
```

### Anti-Patterns to Avoid
- **Computing new scores in context builders:** Context builders extract/format, they don't run scoring algorithms. Scenario "simulation" is just arithmetic on existing scores (apply delta, re-sum), not a new scoring run.
- **Hardcoding tier thresholds:** Always read from scoring.json via tier_config. Never `if score > 70`.
- **Matplotlib for simple bar charts:** Waterfall and tornado are horizontal rectangles -- pure SVG is cleaner, faster, and print-friendly. Reserve matplotlib for polar/complex charts only.
- **Storing scenario results in ScoringResult model:** Scenarios are ephemeral display data computed at render time, not persistent scoring output. Keep them in the context builder return dict, not the state model. (Exception: if scenarios need to persist for re-rendering, add a lightweight field.)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SVG generation | String templating | Pure Python string building (factor_bars.py pattern) | Already proven pattern, no template engine overhead for chart SVG |
| Color selection | Hardcoded hex values | chart_style_registry.resolve_colors() | Centralized, consistent, supports dark/light themes |
| Tier classification | Manual if/elif | tier_classification.classify_tier() | Already handles all edge cases, reads from config |
| Currency formatting | f-string formatting | formatters_numeric.format_currency(compact=True) | Handles None, compact notation, consistent across all templates |
| Factor bar rendering | New bar chart | render_factor_bar() from factor_bars.py | Already exists and handles all edge cases |

## Common Pitfalls

### Pitfall 1: SVG Viewbox vs Pixel Dimensions
**What goes wrong:** SVG looks wrong size in HTML or gets cut off in print
**Why it happens:** Mixing viewBox coordinates with style width/height, or not setting responsive width
**How to avoid:** Follow gauge.py pattern: `viewBox="0 0 W H"` for coordinate space, `style="width:Xpx"` for display size. For inline charts embedded in flex layouts, use `width="100%"` (see save_chart_to_svg).
**Warning signs:** Chart appears tiny or overflows container

### Pitfall 2: safe_float() Omission
**What goes wrong:** Pipeline crashes on None, "N/A", or string percentage values from state
**Why it happens:** Factor scores and probabilities can be None if scoring stage partially completed
**How to avoid:** Every `float()` in render code must be `safe_float()`. Every division must guard against zero divisor.
**Warning signs:** TypeError or ValueError in render stage

### Pitfall 3: Probability Components Don't Sum to Final
**What goes wrong:** Displayed components visually don't add up to the total probability shown elsewhere
**Why it happens:** EnhancedFrequency uses multiplicative formula (base * hazard * signal), not additive. But D-04 says "additive/subtractive" display.
**How to avoid:** Transform multiplicative model into additive display: show base rate, then each modifier as "+X%" or "-X%" (the difference it makes to the running total). Document this clearly. The underlying math is still multiplicative -- the display is the additive decomposition of the product.
**Warning signs:** Components listed as multipliers (1.15x) rather than percentage adjustments (+2.3%)

### Pitfall 4: Scenario Factor Deltas Exceed Max
**What goes wrong:** Scenario sets F1 to 25 points when max is 20
**Why it happens:** Scenario template says "add 15 points" without checking current + delta <= max
**How to avoid:** `min(current + delta, max_points)` for each factor in scenario. Tier re-classification from `classify_tier()` handles the rest.
**Warning signs:** Scenario score < 0 or > 100

### Pitfall 5: Template File Size
**What goes wrong:** scoring.html.j2 or a new template exceeds readability/maintainability
**Why it happens:** Adding waterfall + radar + decomposition + scenarios + tornado all in one file
**How to avoid:** Each visualization is its own template partial (waterfall_chart.html.j2, etc.), included from the parent scoring section. Follow existing pattern of `{% include "sections/scoring/factor_detail.html.j2" %}`.
**Warning signs:** Any template file over 100 lines

### Pitfall 6: Radar Chart Threshold Rings Obscure Data
**What goes wrong:** Adding tier boundary rings to radar makes chart unreadable
**Why it happens:** 6 tiers * ring = too many concentric circles
**How to avoid:** Show only 2-3 key threshold rings (e.g., WALK/WRITE boundary at 0.5 and WRITE/WANT boundary at 0.3 as fraction of max). Use light dashed lines. Label sparingly.
**Warning signs:** Chart looks like a spider web with no data visible

## Code Examples

### Waterfall Chart SVG Pattern
```python
# Source: derived from factor_bars.py + gauge.py patterns
def render_waterfall_chart(
    factors: list[dict[str, Any]],
    total_score: float,
    tier_thresholds: list[tuple[str, float]],
    width: int = 580,
    height: int = 320,
) -> str:
    """Render score buildup waterfall as inline SVG.

    Each factor shown as a horizontal bar segment. Bars stack left-to-right
    showing cumulative deductions from 100. Tier threshold lines overlay.

    Args:
        factors: List of {id, name, points_deducted, max_points} dicts.
        total_score: Final quality score (100 - sum of deductions).
        tier_thresholds: List of (tier_name, score_value) for threshold lines.
        width: SVG width.
        height: SVG height.

    Returns:
        SVG markup string.
    """
    bar_height = 24
    gap = 4
    left_margin = 100  # space for factor labels
    right_margin = 40
    top_margin = 30
    chart_width = width - left_margin - right_margin

    # Scale: 0-100 score maps to chart_width pixels
    def score_to_x(score: float) -> float:
        return left_margin + (score / 100.0) * chart_width

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'style="width:{width}px;height:{height}px" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]

    # Tier threshold lines (dashed vertical lines)
    for tier_name, threshold_score in tier_thresholds:
        x = score_to_x(threshold_score)
        parts.append(
            f'<line x1="{x}" y1="{top_margin - 10}" '
            f'x2="{x}" y2="{height - 10}" '
            f'stroke="#CBD5E1" stroke-width="1" stroke-dasharray="4,3"/>'
        )
        parts.append(
            f'<text x="{x}" y="{top_margin - 14}" text-anchor="middle" '
            f'font-size="8" fill="#94A3B8">{tier_name} {threshold_score}</text>'
        )

    # Factor bars (waterfall: each bar starts where previous ended)
    running_score = 100.0
    y = top_margin
    for f in factors:
        pts = safe_float(f.get("points_deducted", 0), 0.0)
        if pts <= 0:
            continue  # skip zero-scored factors in waterfall

        x_start = score_to_x(running_score)
        x_end = score_to_x(running_score - pts)
        bar_w = x_start - x_end

        # Color by severity
        pct = pts / safe_float(f.get("max_points", 1), 1.0)
        color = "#DC2626" if pct >= 0.6 else "#EA580C" if pct >= 0.3 else "#D4A843"

        # Factor label
        parts.append(
            f'<text x="{left_margin - 4}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="end" font-size="10" fill="#374151">'
            f'{f.get("id", "")} {f.get("name", "")}</text>'
        )

        # Deduction bar
        parts.append(
            f'<rect x="{x_end:.1f}" y="{y}" width="{bar_w:.1f}" '
            f'height="{bar_height}" rx="2" fill="{color}" opacity="0.85"/>'
        )

        # Points label inside bar
        parts.append(
            f'<text x="{(x_start + x_end) / 2:.1f}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="middle" font-size="9" fill="#FFF" font-weight="600">'
            f'-{pts:.0f}</text>'
        )

        running_score -= pts
        y += bar_height + gap

    # Final score bar (result)
    # ... similar pattern for the total

    parts.append("</svg>")
    return "".join(parts)
```

### Probability Decomposition Data Structure
```python
# New model in scoring_output.py or new file
class ProbabilityComponent(BaseModel):
    """Single component of filing probability decomposition."""
    name: str = Field(description="Component name (e.g., 'Sector Base Rate')")
    value_pct: float = Field(description="Component value as percentage points")
    direction: str = Field(description="'base', 'increase', or 'decrease'")
    is_calibrated: bool = Field(default=False, description="Has empirical calibration")
    source: str = Field(default="", description="Source citation if calibrated")
    running_total_pct: float = Field(
        default=0.0, description="Running total after this component"
    )
```

### Scenario Generation Logic
```python
# Scenario selection based on current risk profile
_SCENARIO_TEMPLATES = [
    {
        "id": "SCA_FILED",
        "name": "Securities Class Action Filed",
        "condition": lambda state: not _has_active_sca(state),  # Only if no current SCA
        "factor_deltas": {"F1": 20},  # F1 goes to max
        "probability_impact": "HIGH",
    },
    {
        "id": "EARNINGS_MISS_DROP",
        "name": "Earnings Miss + 30% Stock Drop",
        "condition": lambda state: True,  # Always relevant
        "factor_deltas": {"F2": 12, "F5": 8},  # Stock decline + guidance miss
        "probability_impact": "ELEVATED",
    },
    {
        "id": "RESTATEMENT",
        "name": "Financial Restatement",
        "condition": lambda state: True,
        "factor_deltas": {"F3": 15, "F1": 10},  # Audit + litigation
        "probability_impact": "VERY_HIGH",
    },
    # ... more scenario templates
]
```

### Tornado Chart SVG Pattern
```python
def render_tornado_chart(
    scenarios: list[dict[str, Any]],  # [{name, delta, direction}]
    current_score: float,
    width: int = 580,
    height: int = 280,
) -> str:
    """Render scenario sensitivity as horizontal tornado bars.

    Bars extend left (score decrease) or right (score increase) from
    a center line representing the current score. Sorted by absolute
    magnitude (largest impact at top).
    """
    # Sort by absolute impact
    sorted_scenarios = sorted(scenarios, key=lambda s: abs(s["delta"]), reverse=True)
    # Center line = current score position
    # Bars extend proportionally from center
    # Color: red for score decrease (worse), blue for score improvement
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single composite score display | 10-factor table with bars | Phase 6-12 | Factors visible but not visualized as buildup |
| Band-only probability | Band + range + industry base | Phase 12 | Still opaque -- no component decomposition |
| Percentile-based severity scenarios | Percentile scenarios in table | Phase 12 | Severity =/= score impact scenarios (different concept) |
| No zero-verification | ZER-001 table | Phase 117 | Zero factors documented but not emphasized in visual flow |

**Key insight:** Existing severity_scenarios (25th/50th/75th/95th percentile loss amounts) are a DIFFERENT concept from score-impact scenarios (D-05/D-06). Severity scenarios answer "how much would we pay?" Score scenarios answer "how would the risk score change?" Both should coexist -- don't replace one with the other.

## Open Questions

1. **Probability decomposition math**
   - What we know: EnhancedFrequency uses multiplicative formula: `adjusted_prob = base_rate * hazard_mult * signal_mult`. Components exist: base_rate_pct, hazard_multiplier, crf_signal, pattern_signal, factor_signal.
   - What's unclear: How to expand from 3 multiplicative components to 7+ additive display components (D-04 lists: sector base rate, IPO uplift, market cap tier, volatility adjustment, insider selling signal, litigation history, governance quality). Some of these may be sub-components of the existing multipliers.
   - Recommendation: Create additive display by computing each component's marginal impact: `component_impact = running_total * (multiplier - 1.0)`. For components not yet in EnhancedFrequency (IPO uplift, market cap tier, volatility), derive from factor scores (F4 for IPO, F7 for volatility, etc.) and map to probability adjustments. Mark these as UNCALIBRATED.

2. **Scenario factor delta calibration**
   - What we know: scoring.json defines factor rules with point values (e.g., F1-001 "Active SCA" = 20 points, F2-001 ">60% decline" = 15 points).
   - What's unclear: For compound scenarios ("Earnings Miss + 30% Drop"), how to combine factor impacts when multiple rules within a factor could apply.
   - Recommendation: Use the highest-applicable rule per factor (max, not sum), consistent with how actual scoring works. Document this in the scenario template definitions.

3. **Radar chart enhancement scope**
   - What we know: Existing radar shows risk fractions (points/max per factor). D-02 wants threshold rings showing tier boundaries.
   - What's unclear: Tier boundaries are score-level (e.g., 70 for WRITE), not factor-level. A factor doesn't have a "tier boundary."
   - Recommendation: Show 2-3 reference rings at fixed fractions (0.25, 0.50, 0.75) as they already exist. Add a "average" ring showing the mean fraction across factors to highlight concentration vs distribution. This addresses SCORE-02's "spiky vs round" question without conflating factor fractions with tier scores.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/render/ -x -q --timeout=30` |
| Full suite command | `uv run pytest -x -q --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCORE-01 | Waterfall SVG contains factor bars and tier lines | unit | `uv run pytest tests/render/test_waterfall_chart.py -x` | Wave 0 |
| SCORE-02 | Radar chart includes threshold rings | unit | `uv run pytest tests/render/test_radar_enhancement.py -x` | Wave 0 |
| SCORE-03 | Factor detail cards have dual-voice blocks | unit | `uv run pytest tests/render/test_factor_detail_cards.py -x` | Wave 0 |
| SCORE-04 | Dominant risk cluster computed correctly | unit | `uv run pytest tests/render/test_risk_cluster.py -x` | Wave 0 |
| SCORE-05 | Zero-scored factors display ZER-001 | integration | `uv run pytest tests/render/test_zero_verification.py -x` | Existing (verify) |
| PROB-01 | Probability decomposes into 7+ components | unit | `uv run pytest tests/render/test_probability_decomposition.py -x` | Wave 0 |
| PROB-02 | Components have calibration labels | unit | `uv run pytest tests/render/test_probability_decomposition.py::test_calibration_labels -x` | Wave 0 |
| PROB-03 | Components are individually displayed | integration | `uv run pytest tests/render/test_probability_decomposition.py::test_template_render -x` | Wave 0 |
| SCEN-01 | 5-7 scenarios generated from risk profile | unit | `uv run pytest tests/render/test_scenario_generator.py -x` | Wave 0 |
| SCEN-02 | Each scenario shows score delta and tier change | unit | `uv run pytest tests/render/test_scenario_generator.py::test_tier_change -x` | Wave 0 |
| SCEN-03 | Tornado SVG renders sorted bars | unit | `uv run pytest tests/render/test_tornado_chart.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/render/ -x -q --timeout=30`
- **Per wave merge:** `uv run pytest -x -q --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/render/test_waterfall_chart.py` -- covers SCORE-01
- [ ] `tests/render/test_tornado_chart.py` -- covers SCEN-03
- [ ] `tests/render/test_probability_decomposition.py` -- covers PROB-01, PROB-02, PROB-03
- [ ] `tests/render/test_scenario_generator.py` -- covers SCEN-01, SCEN-02
- [ ] `tests/render/test_risk_cluster.py` -- covers SCORE-04
- [ ] `tests/render/test_radar_enhancement.py` -- covers SCORE-02
- [ ] `tests/render/test_factor_detail_cards.py` -- covers SCORE-03

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/do_uw/stages/render/charts/factor_bars.py` -- established pure SVG pattern
- Codebase analysis: `src/do_uw/stages/render/charts/radar_chart.py` -- existing matplotlib radar
- Codebase analysis: `src/do_uw/models/scoring.py` -- FactorScore, ScoringResult models
- Codebase analysis: `src/do_uw/stages/render/context_builders/scoring.py` -- extract_scoring()
- Codebase analysis: `src/do_uw/stages/score/frequency_model.py` -- EnhancedFrequency model
- Codebase analysis: `src/do_uw/stages/score/tier_classification.py` -- classify_tier()
- Codebase analysis: `brain/config/scoring.json` -- tier boundaries, factor definitions

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions D-01 through D-08 -- user-validated design choices

### Tertiary (LOW confidence)
- Probability decomposition mapping (7+ components from 3 multiplicative factors) -- needs validation during implementation
- Scenario factor delta values -- calibrated from scoring.json rules but compound interactions untested

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - zero new dependencies, all patterns proven in codebase
- Architecture: HIGH - follows established chart/context builder/template patterns exactly
- Pitfalls: HIGH - based on actual codebase patterns and known issues (safe_float, SVG sizing)
- Probability decomposition: MEDIUM - mathematical transform from multiplicative to additive display needs validation
- Scenario generation: MEDIUM - scenario template design and factor delta calibration need iteration

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- internal codebase, no external dependency changes)
