# Phase 25: Classification Engine & Hazard Profile - Research

**Researched:** 2026-02-11
**Domain:** D&O underwriting risk classification and hazard profiling engine
**Confidence:** HIGH -- this is internal domain logic with extensive prior research, working within an established codebase

## Summary

Phase 25 implements Layers 1-2 of the five-layer analysis architecture defined in the Phase 24 unified framework. Layer 1 (Classification) takes exactly 3 objective variables -- market cap tier, industry sector, and IPO age -- and produces a deterministic base filing rate with severity band. Layer 2 (Hazard Profile) evaluates 7 hazard categories containing 47 dimensions and produces an Inherent Exposure Score (IES, 0-100) with named interaction effects and a multiplicative filing rate adjustment.

The codebase already has an `InherentRiskBaseline` model and `compute_inherent_risk_baseline()` function in the BENCHMARK stage that computes `company_rate = sector_base_rate * cap_multiplier * score_multiplier`. This existing implementation uses sector + market cap but conflates classification with scoring (the `score_multiplier` comes from the 10-factor quality score). Phase 25 replaces this conflation with a clean separation: Classification produces the base rate from objective variables only, and the Hazard Profile produces the IES multiplier from 47 structural dimensions. The old inherent risk baseline is retained as a silent sanity check.

The pipeline position for the new engines is after EXTRACT and before ANALYZE, which means new stage logic or a new sub-stage. The data inputs (market cap, SIC/NAICS, IPO date, governance structure, financial structure) are all available from the RESOLVE and EXTRACT stages. The 47 hazard dimensions have been fully researched with data sources, scoring scales, and thresholds documented in `HAZARD_DIMENSIONS_RESEARCH.md`.

**Primary recommendation:** Build two new modules (`stages/classify/` and `stages/hazard/`) that run between EXTRACT and ANALYZE, producing `ClassificationResult` and `HazardProfile` Pydantic models stored on `AnalysisState`. Use JSON config files for all tiers, weights, multipliers, and interaction patterns. Keep the old `InherentRiskBaseline` as a silent sanity check. Wire IES into the SCORE stage as "Factor 0" (pre-factor baseline).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Exactly 3 classification variables**: market cap tier, industry sector (SIC/NAICS), IPO age (years since listing)
- Exchange/index membership dropped -- redundant with market cap + industry
- FPI status, dual-class, analyst coverage rejected for classification (may appear as hazard dimensions)
- **5 market cap tiers**: Mega (>$200B, 6-8%), Large ($10-200B, 4-6%), Mid ($2-10B, 3-4%), Small ($300M-2B, 2-3%), Micro (<$300M, 1-2%)
- **IPO age decay**: 3-year cliff model. Full 2.8x multiplier years 0-3, 1.5x years 3-5, 1.0x after 5 years
- **Output**: Single base filing rate + severity band (not a range with confidence interval)
- **Keep all 47 dimensions** from the research taxonomy -- do not trim
- **Rebalanced weights**: Business Model UP to 30-35% (from 25%), Governance DOWN to 5-10% (from 15%)
- Proposed weights: Business 30-35%, People 15%, Financial 15%, Governance 5-10%, Maturity 10%, Environment 10%, Emerging 10%
- **Non-automatable dimensions**: Use proxy signals for scoring AND flag for underwriter attention with meeting prep questions
- **Worksheet visibility**: IES score + hazard highlights in executive summary; full 47-dimension breakdown in appendix/drill-down
- **Named interaction effects in config + dynamic detection**: 4-6 hardcoded patterns (Rookie Rocket, Black Box, Imperial Founder, Acquisition Machine) in JSON config with multiplier ranges. ALSO detect novel combinations dynamically
- **IES-to-tier mapping**: Claude's discretion
- **Combination model**: Multiplicative. Filing rate = base_rate x IES_multiplier. IES=50 (neutral) = 1.0x
- **Transparency**: Full 47-dimension breakdown shown with individual scores, weights, and contribution to IES
- **Replaces old inherent risk baseline** but keeps old as silent validation
- **Pipeline position**: After EXTRACT, before ANALYZE
- **IES as Factor 0 (pre-factor)**: IES becomes the baseline BEFORE the 10-factor scoring adjustments
- **Caching**: Claude's discretion

### Claude's Discretion
- IES-to-tier band mapping (what IES score maps to which underwriting action)
- Caching strategy
- Exact multiplier values for IES-to-filing-rate conversion
- Dynamic interaction detection algorithm
- Hazard dimension data source mapping (which EXTRACT outputs feed which dimensions)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | >=2.0 | `ClassificationResult`, `HazardProfile`, `HazardDimensionScore` models | Already used for all models in the codebase |
| Python 3.12+ | 3.12+ | Type hints, match statements | Project standard |
| JSON config | N/A | `classification.json`, `hazard_weights.json`, `hazard_interactions.json` | Project standard: all thresholds in config/ not code |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | N/A | Multiplicative model computation, clamping | IES calculation, multiplier interpolation |
| logging (stdlib) | N/A | Stage logging | Consistent with all existing stages |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom multiplicative model | scikit-learn GLM | Overkill for 3-variable classification; config-driven is simpler and more transparent |
| JSON config | YAML config | Project uses JSON exclusively; no reason to introduce YAML |
| New CLASSIFY stage | Sub-step within EXTRACT | User specified "after EXTRACT, before ANALYZE" -- a new stage or sub-stage is cleaner |

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
├── stages/
│   ├── classify/                    # NEW - Layer 1 Classification Engine
│   │   ├── __init__.py              # ClassifyStage class
│   │   ├── classification_engine.py # 3-variable classification logic
│   │   └── severity_bands.py        # DDL/severity band computation
│   ├── hazard/                      # NEW - Layer 2 Hazard Profile Engine
│   │   ├── __init__.py              # HazardStage class
│   │   ├── hazard_engine.py         # Main engine: evaluate 7 categories, compute IES
│   │   ├── dimension_scoring.py     # Score individual dimensions from extracted data
│   │   ├── interaction_effects.py   # Named + dynamic interaction detection
│   │   └── data_mapping.py          # Map EXTRACT outputs to hazard dimensions
│   ├── score/                       # MODIFIED - consumes IES as Factor 0
│   │   └── __init__.py              # Modified to use IES as pre-factor baseline
│   └── benchmark/                   # MODIFIED - keeps old baseline as sanity check
│       └── inherent_risk.py         # Retained, runs silently for comparison
├── models/
│   ├── classification.py            # NEW - ClassificationResult, MarketCapTier
│   └── hazard_profile.py            # NEW - HazardProfile, HazardDimensionScore, InteractionEffect
├── config/
│   ├── classification.json          # NEW - market cap tiers, industry rates, IPO multipliers
│   ├── hazard_weights.json          # NEW - 7 category weights, 47 dimension configs
│   └── hazard_interactions.json     # NEW - named interaction patterns, multiplier ranges
└── brain/
    └── sectors.json                 # EXISTING - claim_base_rates remain as silent baseline
```

### Pattern 1: Classification Engine (Deterministic, Config-Driven)
**What:** Takes 3 objective variables and produces a single filing rate + severity band.
**When to use:** Every analysis, immediately after EXTRACT completes.
**Key design:** Pure function, no side effects, fully deterministic from inputs + config.

```python
# Source: Internal architecture based on existing inherent_risk.py pattern
from do_uw.models.classification import ClassificationResult, MarketCapTier

def classify_company(
    market_cap: float | None,
    sector_code: str,
    years_public: int | None,
    config: dict[str, Any],
) -> ClassificationResult:
    """Classify company into base filing rate and severity band.

    Uses ONLY 3 objective variables:
    1. Market cap -> tier (Mega/Large/Mid/Small/Micro)
    2. Industry sector (SIC/NAICS -> sector code) -> base rate
    3. IPO age (years since listing) -> age multiplier

    Formula: filing_rate = sector_base_rate * cap_multiplier * ipo_multiplier
    """
    cap_tier = _determine_cap_tier(market_cap, config["market_cap_tiers"])
    base_rate = _get_sector_rate(sector_code, config["sector_rates"])
    ipo_mult = _ipo_age_multiplier(years_public, config["ipo_age_decay"])

    filing_rate = base_rate * cap_tier.filing_multiplier * ipo_mult
    severity_band = _compute_severity_band(market_cap, config["severity_bands"])

    return ClassificationResult(
        market_cap_tier=cap_tier,
        sector_code=sector_code,
        years_public=years_public,
        base_filing_rate_pct=round(filing_rate, 2),
        severity_band_low_m=severity_band[0],
        severity_band_high_m=severity_band[1],
        ipo_multiplier=ipo_mult,
        methodology="classification_v1",
    )
```

### Pattern 2: Hazard Profile Engine (47 Dimensions -> IES 0-100)
**What:** Evaluates 7 categories of hazard dimensions, applies weights, detects interactions, produces IES.
**When to use:** After classification, before ANALYZE.
**Key design:** Each dimension is independently scored, then weighted and aggregated.

```python
# Source: Internal architecture based on factor_scoring.py pattern
from do_uw.models.hazard_profile import HazardProfile, HazardDimensionScore

def compute_hazard_profile(
    extracted: ExtractedData,
    company: CompanyProfile,
    classification: ClassificationResult,
    weights_config: dict[str, Any],
    interactions_config: dict[str, Any],
) -> HazardProfile:
    """Compute Inherent Exposure Score from 47 hazard dimensions.

    Steps:
    1. Score each of 47 dimensions (0-max_score)
    2. Normalize within category
    3. Apply category weights (Business 30-35%, etc.)
    4. Detect named interaction effects
    5. Detect dynamic co-occurrences
    6. Compute final IES (0-100)
    """
    dimension_scores = score_all_dimensions(extracted, company, weights_config)
    category_scores = aggregate_by_category(dimension_scores, weights_config)

    raw_ies = sum(
        cat.weighted_score for cat in category_scores.values()
    )

    named_interactions = detect_named_interactions(
        dimension_scores, interactions_config,
    )
    dynamic_interactions = detect_dynamic_interactions(
        dimension_scores, interactions_config,
    )

    # Apply interaction multipliers
    interaction_mult = compute_interaction_multiplier(
        named_interactions, dynamic_interactions,
    )
    adjusted_ies = min(100.0, raw_ies * interaction_mult)

    return HazardProfile(
        ies_score=round(adjusted_ies, 1),
        raw_ies_score=round(raw_ies, 1),
        dimension_scores=dimension_scores,
        category_scores=category_scores,
        named_interactions=named_interactions,
        dynamic_interactions=dynamic_interactions,
        interaction_multiplier=interaction_mult,
        ies_multiplier=_ies_to_filing_multiplier(adjusted_ies),
    )
```

### Pattern 3: IES-to-Filing-Rate Multiplicative Model
**What:** Converts IES score to a filing rate multiplier. IES=50 is neutral (1.0x).
**Key design:** Piecewise linear interpolation from config-defined breakpoints.

```python
# IES -> Filing Rate Multiplier (user decision: multiplicative model)
# filing_rate = base_rate (from classification) x IES_multiplier
#
# Recommended mapping (Claude's discretion):
# IES  0-20:  0.5-0.7x  (very low inherent exposure)
# IES 20-40:  0.7-0.9x  (below-average exposure)
# IES 40-60:  0.9-1.1x  (neutral zone)
# IES 60-75:  1.1-1.5x  (elevated exposure)
# IES 75-90:  1.5-2.5x  (high exposure)
# IES 90-100: 2.5-4.0x  (extreme exposure)
```

### Pattern 4: Named Interaction Effects
**What:** Branded, memorable patterns that amplify risk when multiple hazard dimensions co-occur.
**When to use:** After individual dimension scoring, before IES finalization.
**Key design:** Config-driven pattern definitions with required dimensions and multiplier ranges.

```python
# hazard_interactions.json structure:
{
  "named_interactions": [
    {
      "id": "ROOKIE_ROCKET",
      "name": "Rookie Rocket",
      "description": "High-growth company with inexperienced management and recent IPO",
      "required_dimensions": {
        "H1-09_speed_of_growth": {"min_score_pct": 60},
        "H2-01_management_experience": {"min_score_pct": 60},
        "H5-01_ipo_recency": {"min_score_pct": 50}
      },
      "multiplier_range": [1.3, 1.5],
      "category": "compounding_inexperience"
    },
    {
      "id": "BLACK_BOX",
      "name": "Black Box",
      "description": "Complex business model with weak earnings quality and heavy non-GAAP reliance",
      "required_dimensions": {
        "H1-02_business_complexity": {"min_score_pct": 60},
        "H3-04_earnings_quality": {"min_score_pct": 50},
        "H1-11_non_gaap_reliance": {"min_score_pct": 50}
      },
      "multiplier_range": [1.2, 1.4],
      "category": "opacity_risk"
    },
    {
      "id": "IMPERIAL_FOUNDER",
      "name": "Imperial Founder",
      "description": "Founder CEO with dual-class control and weak board oversight",
      "required_dimensions": {
        "H2-05_founder_led": {"min_score_pct": 70},
        "H1-10_dual_class": {"min_score_pct": 50},
        "H4-02_board_independence": {"min_score_pct": 50}
      },
      "multiplier_range": [1.2, 1.5],
      "category": "concentration_of_power"
    },
    {
      "id": "ACQUISITION_MACHINE",
      "name": "Acquisition Machine",
      "description": "Serial acquirer with goodwill-heavy balance sheet and integration risk",
      "required_dimensions": {
        "H1-08_ma_activity": {"min_score_pct": 60},
        "H3-03_goodwill_heavy": {"min_score_pct": 50}
      },
      "multiplier_range": [1.15, 1.35],
      "category": "acquisition_risk"
    }
  ],
  "dynamic_detection": {
    "min_elevated_dimensions": 5,
    "elevated_threshold_pct": 60,
    "co_occurrence_multiplier": [1.05, 1.15],
    "label": "Elevated Co-occurrence"
  }
}
```

### Pattern 5: Pipeline Integration
**What:** How the new engines integrate with the existing 7-stage pipeline.
**Key design:** Add CLASSIFY and HAZARD as sub-stages between EXTRACT and ANALYZE, or as a new pre-ANALYZE step.

```python
# Option A: New stages in pipeline (requires PIPELINE_STAGES change)
PIPELINE_STAGES = [
    "resolve", "acquire", "extract",
    "classify",   # NEW - Layer 1
    "hazard",     # NEW - Layer 2
    "analyze", "score", "benchmark", "render",
]

# Option B: Pre-ANALYZE step (less invasive, recommended)
# Run classification + hazard as part of ANALYZE stage entry
# but store results on AnalysisState separately
# This avoids changing the 7-stage pipeline structure

# Recommendation: Option B is less disruptive. The CLASSIFY and HAZARD
# logic runs at the start of ANALYZE, before checks execute.
# Models are stored on AnalysisState as:
#   state.classification: ClassificationResult | None
#   state.hazard_profile: HazardProfile | None
```

### Anti-Patterns to Avoid
- **Hardcoding thresholds in Python:** ALL tiers, weights, multipliers, dimension configs, interaction patterns go in JSON config files. Code reads config, never defines constants for domain values.
- **Mixing classification with hazard profile:** Classification is 3 variables, deterministic. Hazard profile is 47 dimensions, includes judgment. Keep them separate -- different modules, different models.
- **Duplicating data extraction:** The hazard engine reads FROM extracted data (ExtractedData, CompanyProfile). It does NOT re-extract data. Use `data_mapping.py` to bridge extracted fields to dimension inputs.
- **Monolithic scoring function:** Each of 47 dimensions has its own scoring function. Category aggregation is separate. IES computation is separate. Interaction detection is separate.
- **Ignoring missing data:** Many dimensions will have missing data for some companies. Score them as neutral (midpoint) and flag as "insufficient data" in the transparency output. Never penalize for missing data, never reward for it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Piecewise linear interpolation | Custom interpolation math | Simple `_interpolate()` helper with breakpoint list from config | Avoid off-by-one errors in tier boundaries |
| Dimension scoring dispatch | Giant if/elif chain | Dict-based dispatch keyed by dimension ID | 47 dimensions need clean dispatch |
| Config loading | Custom JSON reader | Existing `BackwardCompatLoader` pattern + `Path(__file__).parent.parent / "config"` pattern | Already proven in actuarial.json, ai_risk_weights.json |
| Multiplicative model | Custom math | `functools.reduce(operator.mul, multipliers, 1.0)` | Clean, readable, standard |

**Key insight:** The classification engine is ~100 lines of pure logic. The hazard profile engine is larger (~400-500 lines across files) but each dimension scoring function is 5-20 lines. The complexity is in breadth (47 dimensions), not depth.

## Common Pitfalls

### Pitfall 1: Double-Counting with Existing Factors
**What goes wrong:** Some hazard dimensions overlap with existing F1-F10 scoring factors. For example, H3 (Financial Structure) overlaps with F8 (Financial Distress). If both score the same signal, the company is penalized twice.
**Why it happens:** The hazard profile measures STRUCTURAL characteristics (the shape of the balance sheet), while F8 measures BEHAVIORAL signals (current distress indicators). But the data sources overlap.
**How to avoid:** Hazard dimensions score the STRUCTURAL CONDITION (e.g., "high-leverage capital structure"), not the CURRENT STATE (e.g., "covenant breach"). Document the boundary explicitly for each overlapping dimension. The IES becomes the baseline; F1-F10 adjust from there.
**Warning signs:** If a clean, well-run company with a complex capital structure gets heavily penalized in both IES and F8, the boundary is wrong.

### Pitfall 2: Excessive Sensitivity to Missing Data
**What goes wrong:** Many of the 47 dimensions require data that may not be available for all companies (e.g., H2-08 Tone at the Top, H4-04 Audit Committee Quality). If missing data defaults to HIGH risk, the IES is artificially inflated for data-sparse companies.
**Why it happens:** Conservative bias -- "we don't know, so assume the worst."
**How to avoid:** Missing data defaults to NEUTRAL (midpoint score). Track data coverage per company. If <60% of dimensions have data, flag the IES as "low confidence" and note which categories are under-represented.
**Warning signs:** Micro-cap companies with minimal public disclosure consistently score IES >80.

### Pitfall 3: Interaction Effect Explosion
**What goes wrong:** With 47 dimensions, there are 1,081 pairwise combinations. Detecting "interesting" combinations dynamically without overwhelming the output.
**Why it happens:** The desire for comprehensive interaction detection.
**How to avoid:** Named interactions (4-6 branded patterns) are explicit and config-driven. Dynamic detection uses a simple threshold: if 5+ dimensions are in the top 40% of their scoring range, flag as "elevated co-occurrence" with a modest multiplier (1.05-1.15x). Don't try to detect all possible interactions.
**Warning signs:** The interaction multiplier exceeds 2.0x for any company that isn't genuinely extreme (SMCI-level).

### Pitfall 4: Pipeline Stage Count Change Breaking Tests
**What goes wrong:** Adding new stages to `PIPELINE_STAGES` breaks test fixtures that assume exactly 7 stages.
**Why it happens:** Many tests create `AnalysisState` with hardcoded stage expectations.
**How to avoid:** Run classification + hazard as a pre-step within the existing pipeline flow (at the start of ANALYZE or as a separate callable before ANALYZE) rather than adding new formal pipeline stages. Store results on `AnalysisState` without changing `PIPELINE_STAGES`.
**Warning signs:** Test failures in `test_state.py`, `test_cli.py`, or any test that checks `state.stages` keys.

### Pitfall 5: Old vs. New Inherent Risk Baseline Confusion
**What goes wrong:** Both the old `InherentRiskBaseline` (in BENCHMARK) and new `ClassificationResult` produce filing rates, creating confusion about which is authoritative.
**Why it happens:** The old baseline is retained as a sanity check per user decision.
**How to avoid:** The new `ClassificationResult` is the authoritative source. The old `InherentRiskBaseline` computes silently and is compared. If they diverge by >2x, log a warning. The RENDER stage reads from the new model, not the old one.
**Warning signs:** Worksheet shows two different filing rates in different sections.

### Pitfall 6: File Size Explosion
**What goes wrong:** 47 dimensions with scoring functions, data mapping, and config could produce a single file exceeding the 500-line limit.
**Why it happens:** Trying to keep all dimension scoring in one file.
**How to avoid:** Split dimension scoring into category-based files if needed (e.g., `dimension_h1_business.py`, `dimension_h2_people.py`). The main `dimension_scoring.py` can use importlib dispatch to call into category modules.
**Warning signs:** Any file approaching 400 lines during development.

## Code Examples

### Pydantic Model: ClassificationResult
```python
# Source: Internal design based on existing InherentRiskBaseline pattern
from enum import StrEnum
from pydantic import BaseModel, Field

class MarketCapTier(StrEnum):
    MEGA = "MEGA"       # >$200B
    LARGE = "LARGE"     # $10-200B
    MID = "MID"         # $2-10B
    SMALL = "SMALL"     # $300M-2B
    MICRO = "MICRO"     # <$300M

class ClassificationResult(BaseModel):
    """Layer 1: Objective classification from 3 variables."""
    market_cap_tier: MarketCapTier
    sector_code: str
    sector_name: str = ""
    years_public: int | None = None
    base_filing_rate_pct: float = Field(
        description="Annual filing rate (%) from classification"
    )
    severity_band_low_m: float = Field(
        description="Low end of severity band (USD millions)"
    )
    severity_band_high_m: float = Field(
        description="High end of severity band (USD millions)"
    )
    ddl_exposure_base_m: float = Field(
        default=0.0,
        description="Prospective DDL at 15% stock drop (USD millions)"
    )
    ipo_multiplier: float = Field(
        default=1.0,
        description="IPO age multiplier applied (1.0 = seasoned)"
    )
    methodology: str = "classification_v1"
```

### Pydantic Model: HazardProfile
```python
# Source: Internal design based on ScoringResult pattern
class HazardCategory(StrEnum):
    BUSINESS = "H1"
    PEOPLE = "H2"
    FINANCIAL = "H3"
    GOVERNANCE = "H4"
    MATURITY = "H5"
    ENVIRONMENT = "H6"
    EMERGING = "H7"

class HazardDimensionScore(BaseModel):
    """Score for a single hazard dimension."""
    dimension_id: str       # e.g., "H1-01"
    dimension_name: str     # e.g., "Industry Sector Risk Tier"
    category: HazardCategory
    raw_score: float        # 0 to max_score
    max_score: float        # dimension-specific max
    normalized_score: float # 0-100 within dimension
    data_available: bool = True
    data_sources: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

class CategoryScore(BaseModel):
    """Aggregated score for a hazard category."""
    category: HazardCategory
    category_name: str
    weight_pct: float       # e.g., 32.5
    raw_score: float        # sum of normalized dimension scores
    weighted_score: float   # raw_score * weight_pct / 100
    dimensions_scored: int
    dimensions_total: int
    data_coverage_pct: float

class InteractionEffect(BaseModel):
    """Named or dynamic interaction effect."""
    interaction_id: str     # e.g., "ROOKIE_ROCKET"
    name: str               # e.g., "Rookie Rocket"
    description: str
    triggered_dimensions: list[str]  # dimension IDs that triggered
    multiplier: float       # applied multiplier
    is_named: bool = True   # False for dynamic detection

class HazardProfile(BaseModel):
    """Layer 2: Inherent Exposure Score from 47 hazard dimensions."""
    ies_score: float = Field(description="Adjusted IES 0-100")
    raw_ies_score: float = Field(description="Pre-interaction IES")
    ies_multiplier: float = Field(
        description="Filing rate multiplier from IES (1.0x at IES=50)"
    )
    dimension_scores: list[HazardDimensionScore] = Field(default_factory=list)
    category_scores: dict[str, CategoryScore] = Field(default_factory=dict)
    named_interactions: list[InteractionEffect] = Field(default_factory=list)
    dynamic_interactions: list[InteractionEffect] = Field(default_factory=list)
    interaction_multiplier: float = 1.0
    data_coverage_pct: float = Field(
        default=0.0,
        description="% of 47 dimensions with data available"
    )
    confidence_note: str = ""
    underwriter_flags: list[str] = Field(
        default_factory=list,
        description="Items flagged for underwriter attention / meeting prep"
    )
```

### AnalysisState Extension
```python
# Addition to state.py
class AnalysisState(BaseModel):
    # ... existing fields ...
    classification: ClassificationResult | None = Field(
        default=None, description="Layer 1: Objective classification"
    )
    hazard_profile: HazardProfile | None = Field(
        default=None, description="Layer 2: Hazard profile (IES)"
    )
```

### Config File: classification.json
```json
{
  "version": "1.0",
  "market_cap_tiers": [
    {"tier": "MEGA",  "min_cap": 200000000000, "filing_rate_range": [6, 8], "filing_multiplier": 1.8, "severity_band_m": [150, 500]},
    {"tier": "LARGE", "min_cap": 10000000000,  "filing_rate_range": [4, 6], "filing_multiplier": 1.3, "severity_band_m": [40, 150]},
    {"tier": "MID",   "min_cap": 2000000000,   "filing_rate_range": [3, 4], "filing_multiplier": 1.0, "severity_band_m": [15, 40]},
    {"tier": "SMALL", "min_cap": 300000000,    "filing_rate_range": [2, 3], "filing_multiplier": 0.7, "severity_band_m": [5, 15]},
    {"tier": "MICRO", "min_cap": 0,            "filing_rate_range": [1, 2], "filing_multiplier": 0.5, "severity_band_m": [2, 5]}
  ],
  "sector_rates": {
    "BIOT": 7.0, "TECH": 5.0, "HLTH": 4.0, "FINS": 4.0,
    "COMM": 3.5, "CONS": 3.5, "ENGY": 3.0, "INDU": 2.5,
    "STPL": 2.0, "UTIL": 1.5, "REIT": 3.0, "DEFAULT": 3.5
  },
  "ipo_age_decay": {
    "cliff_years": 3,
    "cliff_multiplier": 2.8,
    "transition_years": 5,
    "transition_multiplier": 1.5,
    "seasoned_multiplier": 1.0
  }
}
```

### Dimension Data Mapping Example
```python
# data_mapping.py: Bridge between ExtractedData/CompanyProfile and dimension inputs
def map_dimension_data(
    dim_id: str,
    extracted: ExtractedData,
    company: CompanyProfile,
) -> dict[str, Any]:
    """Map extracted data to dimension-specific inputs."""

    # Example mappings for H1 (Business Model) dimensions:
    if dim_id == "H1-01":  # Industry Sector Risk Tier
        sector = company.identity.sector
        return {"sector_code": sector.value if sector else "DEFAULT"}

    if dim_id == "H1-02":  # Business Model Complexity
        segments = company.revenue_segments
        return {
            "segment_count": len(segments),
            "has_vie": _check_operational_complexity(company, "vie"),
            "business_model_desc": (
                company.business_model_description.value
                if company.business_model_description else ""
            ),
        }

    if dim_id == "H2-01":  # Management Public Company Experience
        if extracted.governance and extracted.governance.leadership:
            execs = extracted.governance.leadership.executives
            return {
                "ceo_public_co_years": _get_ceo_experience(execs),
                "cfo_public_co_years": _get_cfo_experience(execs),
            }
        return {}  # No data available

    if dim_id == "H3-01":  # Leverage
        if extracted.financials and extracted.financials.statements:
            return {
                "debt_to_equity": _get_financial_ratio(
                    extracted.financials, "debt_to_equity"
                ),
                "net_debt_ebitda": _get_financial_ratio(
                    extracted.financials, "net_debt_ebitda"
                ),
            }
        return {}

    # ... 43 more dimension mappings ...
    return {}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `InherentRiskBaseline` = sector_rate * cap_mult * score_mult | Classification (3 vars) + Hazard Profile (47 dims) | Phase 25 | Separates objective classification from structural hazard assessment |
| Score multiplier comes from 10-factor quality score | IES multiplier comes from 47 hazard dimensions | Phase 25 | Breaks circular dependency: old system used signals to compute baseline |
| Flat inherent risk in BENCHMARK stage | Classification after EXTRACT, IES feeds into SCORE as Factor 0 | Phase 25 | Moves baseline computation earlier in pipeline |
| No interaction effects | Named patterns (Rookie Rocket, Black Box, etc.) + dynamic detection | Phase 25 | Captures non-linear risk combinations |

**Deprecated/outdated:**
- `InherentRiskBaseline.score_multiplier`: Will be computed but no longer authoritative. IES replaces this.
- `compute_inherent_risk_baseline()` as the primary risk computation: Retained as silent sanity check only.

## Critical Data Source Mapping

This is the most important section for the planner. Each of the 47 hazard dimensions needs data from specific EXTRACT outputs. Here is the complete mapping by category.

### H1: Business & Operating Model (13 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H1-01 Industry Sector | `company.identity.sic_code`, `company.identity.sector` | YES |
| H1-02 Business Complexity | `company.revenue_segments`, `company.operational_complexity` | YES |
| H1-03 Regulatory Intensity | SIC/NAICS -> config lookup | YES (config-driven) |
| H1-04 Geographic Complexity | `company.geographic_footprint`, subsidiary count | YES |
| H1-05 Revenue Model Risk | EXTRACT: revenue recognition notes (LLM extraction) | PARTIAL |
| H1-06 Customer/Supplier Concentration | `company.customer_concentration`, `company.supplier_concentration` | YES |
| H1-07 Capital Intensity | `extracted.financials.statements` (CapEx, PP&E) | YES |
| H1-08 M&A Activity | `company.business_changes`, goodwill from balance sheet | PARTIAL |
| H1-09 Speed of Growth | `extracted.financials` revenue YoY, headcount growth | YES |
| H1-10 Dual-Class Structure | `company.operational_complexity` | YES |
| H1-11 Non-GAAP Reliance | EXTRACT: earnings quality flags | PARTIAL |
| H1-12 Platform Dependency | 10-K risk factors (LLM extraction) | PARTIAL |
| H1-13 IP Dependency | 10-K risk factors, patent data | PARTIAL |

### H2: People & Management (8 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H2-01 Management Experience | `governance.leadership.executives` (bios) | YES |
| H2-02 Industry Expertise Match | Exec bios vs SIC code | PARTIAL |
| H2-03 Scale Experience Mismatch | Exec bios vs market cap | LOW |
| H2-04 Board Quality | `governance.board_forensic`, `governance.governance_quality` | YES |
| H2-05 Founder-Led | `governance.leadership`, proxy data | PARTIAL |
| H2-06 Key Person Dependency | 10-K risk factors | PARTIAL |
| H2-07 Management Turnover | `governance.leadership_stability` | YES |
| H2-08 Tone at the Top | `governance.sentiment`, `governance.narrative_coherence` | PARTIAL (proxy signals) |

### H3: Financial Structure (8 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H3-01 Leverage | `extracted.financials.distress` (ratios) | YES |
| H3-02 Off-Balance Sheet | 10-K notes (LLM extraction) | PARTIAL |
| H3-03 Goodwill-Heavy | `extracted.financials.statements` (balance sheet) | YES |
| H3-04 Earnings Quality | `extracted.financials.earnings_quality` | YES |
| H3-05 Cash Flow Divergence | `extracted.financials.statements` (OCF vs NI) | YES |
| H3-06 Pre-Revenue/Cash Burn | `extracted.financials` (revenue, cash runway) | YES |
| H3-07 Related Party Transactions | Proxy/10-K notes (LLM extraction) | PARTIAL |
| H3-08 Capital Markets Activity | SEC filing history, `company.business_changes` | PARTIAL |

### H4: Governance Structure (8 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H4-01 CEO/Chair Combined | `governance.board_forensic` or `governance.board` | YES |
| H4-02 Board Independence | `governance.governance_quality` or `governance.board` | YES |
| H4-03 Anti-Takeover Provisions | Proxy/charter analysis | PARTIAL |
| H4-04 Audit Committee Quality | `governance.governance_quality`, audit fees | PARTIAL |
| H4-05 Shareholder Rights | Proxy governance disclosures | PARTIAL |
| H4-06 Compensation Structure | `governance.compensation_analysis` | YES |
| H4-07 Compliance Infrastructure | 10-K internal controls, SOX 404 | PARTIAL |
| H4-08 State of Incorporation | `company.identity.state_of_incorporation` | YES |

### H5: Public Company Maturity (5 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H5-01 IPO Recency | `company.years_public` | YES |
| H5-02 Method of Going Public | SEC filing history analysis | PARTIAL |
| H5-03 Exchange/Index Membership | `company.identity.exchange` | YES |
| H5-04 FPI/ADR Status | `company.identity.is_fpi` | YES |
| H5-05 Seasoning/Track Record | Filing history, prior litigation | PARTIAL |

### H6: External Environment (7 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H6-01 Market Cycle Position | Market data (VIX, S&P P/E) | PARTIAL (systemic) |
| H6-02 Industry Regulatory Spotlight | Config-driven + news | PARTIAL |
| H6-03 Industry Litigation Wave | Config-driven + Stanford SCAC | PARTIAL |
| H6-04 Political/Policy Environment | Config-driven (systemic) | YES (config) |
| H6-05 Interest Rate Environment | Market data (systemic) | PARTIAL |
| H6-06 Plaintiff Attorney Activity | Config-driven (systemic) | YES (config) |
| H6-07 Geopolitical Risk | `company.geographic_footprint` + config | PARTIAL |

### H7: Emerging/Modern Hazards (6 dimensions)
| Dimension | Data Source | Available? |
|-----------|-----------|------------|
| H7-01 AI Adoption/Governance | `extracted.ai_risk` | YES |
| H7-02 Cybersecurity Governance | 10-K Item 1C disclosures | PARTIAL |
| H7-03 ESG/Climate Exposure | 10-K risk factors | PARTIAL |
| H7-04 Crypto/Digital Asset | 10-K, business description | PARTIAL |
| H7-05 Social Media/Public Persona | News search, web data | LOW |
| H7-06 Workforce/Labor Model | `extracted.governance.leadership` | PARTIAL |

**Summary:** Of 47 dimensions, approximately 20 have strong data availability (YES), 22 have partial data, and 5 have low data availability. Dimensions with PARTIAL or LOW data should score using available proxies and flag as "limited data" in the transparency output.

## IES-to-Tier Band Mapping (Claude's Discretion)

Recommended mapping for IES bands to underwriting action context:

| IES Range | Risk Label | Filing Multiplier | Underwriting Context |
|-----------|-----------|-------------------|---------------------|
| 0-20 | Very Low Exposure | 0.5-0.7x | Utility-like inherent risk. Structural conditions favorable. |
| 21-35 | Low Exposure | 0.7-0.85x | Below-average inherent exposure. Mature, stable profile. |
| 36-50 | Moderate Exposure | 0.85-1.0x | Average inherent exposure. Standard underwriting. |
| 51-65 | Elevated Exposure | 1.0-1.3x | Above-average inherent exposure. Enhanced scrutiny warranted. |
| 66-80 | High Exposure | 1.3-2.0x | Significant structural risk. Multiple hazard categories elevated. |
| 81-100 | Extreme Exposure | 2.0-3.5x | Pre-revenue biotech + IPO + inexperienced mgmt territory. |

**Validation targets:**
- AAPL: IES ~25-35 (low exposure -- mature, stable, massive scale)
- XOM: IES ~40-50 (moderate -- regulatory + environmental, but mature and stable)
- SMCI: IES ~70-85 (high-extreme -- accounting issues + growth + governance concerns)

## Caching Strategy (Claude's Discretion)

**Recommendation: Store in AnalysisState, no separate cache.**

Rationale:
1. Classification is pure function of 3 inputs -- recomputation is trivial (microseconds)
2. Hazard profile depends on extracted data which is already cached in state
3. The entire AnalysisState is serialized to JSON for resumption
4. No external dependencies that would benefit from caching
5. Adding DuckDB cache for classification/hazard adds complexity with no performance benefit

The classification and hazard profile results will be stored as fields on `AnalysisState`, which is already persisted. This is consistent with how all other stage outputs are stored.

## Dynamic Interaction Detection Algorithm (Claude's Discretion)

**Recommended algorithm:**

```python
def detect_dynamic_interactions(
    dimension_scores: list[HazardDimensionScore],
    config: dict[str, Any],
) -> list[InteractionEffect]:
    """Detect non-named co-occurrences of elevated dimensions.

    Algorithm:
    1. Count dimensions scoring above 60% of their max
    2. If count >= threshold (default: 5), flag as elevated co-occurrence
    3. Group elevated dimensions by category
    4. If any category has 3+ elevated dimensions, flag category concentration
    5. Apply modest multiplier (1.05-1.15x) based on count
    """
    threshold_pct = config.get("elevated_threshold_pct", 60)
    min_count = config.get("min_elevated_dimensions", 5)

    elevated = [
        ds for ds in dimension_scores
        if ds.data_available and ds.normalized_score >= threshold_pct
    ]

    effects: list[InteractionEffect] = []

    if len(elevated) >= min_count:
        # Overall co-occurrence
        mult_range = config.get("co_occurrence_multiplier", [1.05, 1.15])
        # Interpolate based on count above threshold
        excess = len(elevated) - min_count
        max_excess = 10  # cap interpolation at 15 elevated dimensions
        frac = min(excess / max_excess, 1.0)
        mult = mult_range[0] + frac * (mult_range[1] - mult_range[0])

        effects.append(InteractionEffect(
            interaction_id="DYNAMIC_COOCCURRENCE",
            name="Elevated Co-occurrence",
            description=f"{len(elevated)} dimensions elevated (>={threshold_pct}%)",
            triggered_dimensions=[ds.dimension_id for ds in elevated],
            multiplier=round(mult, 3),
            is_named=False,
        ))

    # Category concentration check
    from collections import Counter
    cat_counts = Counter(ds.category for ds in elevated)
    for cat, count in cat_counts.items():
        if count >= 3:
            effects.append(InteractionEffect(
                interaction_id=f"DYNAMIC_CATEGORY_{cat.value}",
                name=f"{cat.value} Category Concentration",
                description=f"{count} elevated dimensions in {cat.value}",
                triggered_dimensions=[
                    ds.dimension_id for ds in elevated if ds.category == cat
                ],
                multiplier=1.05,
                is_named=False,
            ))

    return effects
```

## Open Questions

1. **Pipeline position: new stages vs. pre-ANALYZE sub-step?**
   - What we know: User specified "after EXTRACT, before ANALYZE." The codebase has a rigid 7-stage pipeline with `PIPELINE_STAGES` list.
   - What's unclear: Whether to formally add stages (breaking change) or run as a sub-step of ANALYZE (less invasive).
   - Recommendation: Run as a callable before ANALYZE's main check execution. Store on AnalysisState without changing PIPELINE_STAGES. This minimizes test breakage. If the user prefers formal stages, that's a larger refactor.

2. **Score stage integration: how does IES become "Factor 0"?**
   - What we know: IES is the baseline BEFORE F1-F10 adjustments. The current 10-factor model starts at 100 and deducts.
   - What's unclear: Whether IES adjusts the starting score (e.g., start at IES-adjusted value instead of 100) or is a separate multiplier applied to the final filing rate.
   - Recommendation: IES adjusts the FILING RATE, not the quality score. The quality score (100 - deductions) remains the F1-F10 behavioral signal. The final probability = classification_rate * IES_multiplier * quality_score_multiplier. The quality_score_multiplier comes from the existing tier system.

3. **Validation against known companies: when and how?**
   - What we know: Success criteria require AAPL (low IES), SMCI (high IES), XOM (moderate IES) to produce sensible scores.
   - What's unclear: Whether we have existing state.json files for these companies to test against.
   - Recommendation: Use existing output/ directories (AAPL, SMCI, XOM all present) to load state and run classification + hazard against real data. Create validation tests that assert IES is within expected bands.

## Sources

### Primary (HIGH confidence)
- `24-UNIFIED-FRAMEWORK.md` -- Five-layer architecture definition, Layer 1-2 specifications
- `research/HAZARD_DIMENSIONS_RESEARCH.md` -- Full 47-dimension taxonomy, scoring scales, data sources
- `research/HAZARD_MODEL_VALIDATION.md` -- Industry validation, weight recommendations
- Existing codebase: `stages/score/__init__.py`, `stages/benchmark/inherent_risk.py`, `models/state.py`, `models/scoring.py`, `models/executive_summary.py`, `models/company.py`

### Secondary (MEDIUM confidence)
- Kim & Skinner (2012), "Measuring Securities Litigation Risk" -- validates structural variables as primary predictors
- Baker & Griffith (2007/2010) -- validates "deep governance" importance, limits of formal governance metrics
- Cornerstone Research 2024 Year in Review -- filing rates, settlement data
- CAS Forum D&O Reinsurance Pricing paper -- multiplicative model approach

### Tertiary (LOW confidence)
- IES-to-multiplier mapping values -- these are recommended starting points requiring calibration against actual outcomes
- Dynamic interaction detection thresholds -- require empirical validation
- Weight distribution between categories -- validated by research but untested empirically

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Pydantic v2, JSON config, pure Python; all patterns established in codebase
- Architecture: HIGH -- follows existing stage patterns, data mapping from known EXTRACT outputs
- Pitfalls: HIGH -- identified from deep examination of existing codebase integration points
- Domain model (47 dimensions): MEDIUM -- well-researched but novel taxonomy not validated empirically
- Multiplier values: LOW -- all numerical values (IES-to-multiplier mapping, interaction multipliers) need calibration

**Research date:** 2026-02-11
**Valid until:** 2026-04-11 (60 days -- internal architecture, not library-dependent)
