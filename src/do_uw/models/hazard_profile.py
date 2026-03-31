"""Hazard profile models -- Layer 2 of the five-layer analysis architecture.

Captures the Inherent Exposure Score (IES) computed from 7 hazard
categories containing 47 dimensions. The IES provides a 0-100 score
indicating the company's structural D&O exposure, independent of
behavioral signals.

Models:
- HazardCategory: 7 top-level categories (H1-H7)
- HazardDimensionScore: Individual dimension score (47 total)
- CategoryScore: Aggregated category-level score
- InteractionEffect: Named or dynamic interaction pattern
- HazardProfile: Root container with IES and all sub-scores

Used by:
- HazardStage (Plan 02): Produces HazardProfile from extracted data
- AnalysisState: Stored as state.hazard_profile
- ScoreStage: IES multiplier feeds into filing rate computation
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def _default_str_list() -> list[str]:
    """Default factory for string lists."""
    return []


class HazardCategory(StrEnum):
    """Top-level hazard categories for D&O risk assessment.

    7 categories spanning business model, people, financial structure,
    governance, maturity, external environment, and emerging risks.
    """

    BUSINESS = "H1"       # Business & Operating Model
    PEOPLE = "H2"         # People & Management
    FINANCIAL = "H3"      # Financial Structure
    GOVERNANCE = "H4"     # Governance Structure
    MATURITY = "H5"       # Public Company Maturity
    ENVIRONMENT = "H6"    # External Environment
    EMERGING = "H7"       # Emerging / Modern Hazards


class HazardDimensionScore(BaseModel):
    """Score for a single hazard dimension.

    Each of the 47 dimensions is scored independently, then normalized
    to a 0-100 scale within the dimension's scoring range.

    When data is not available, data_available=False and the score
    defaults to the neutral midpoint (50% of max_score).
    """

    model_config = ConfigDict(frozen=False)

    dimension_id: str = Field(
        description="Dimension identifier (e.g., 'H1-01')",
    )
    dimension_name: str = Field(
        description="Human-readable name (e.g., 'Industry Sector Risk Tier')",
    )
    category: HazardCategory = Field(
        description="Parent hazard category (H1-H7)",
    )
    raw_score: float = Field(
        description="Raw score (0 to max_score for this dimension)",
    )
    max_score: float = Field(
        description="Maximum possible score for this dimension",
    )
    normalized_score: float = Field(
        description="Normalized score (0-100 within dimension range)",
    )
    data_available: bool = Field(
        default=True,
        description="Whether actual data was used (False = neutral default)",
    )
    data_sources: list[str] = Field(
        default_factory=_default_str_list,
        description="Data sources used for scoring",
    )
    evidence: list[str] = Field(
        default_factory=_default_str_list,
        description="Evidence notes supporting the score",
    )


class CategoryScore(BaseModel):
    """Aggregated score for a hazard category.

    Each of the 7 categories aggregates its constituent dimension
    scores and applies the category weight from hazard_weights.json.
    """

    model_config = ConfigDict(frozen=False)

    category: HazardCategory = Field(
        description="Hazard category (H1-H7)",
    )
    category_name: str = Field(
        description="Human-readable category name",
    )
    weight_pct: float = Field(
        description="Category weight as percentage (e.g., 32.5)",
    )
    raw_score: float = Field(
        description="Sum of normalized dimension scores within category",
    )
    weighted_score: float = Field(
        description="raw_score * weight_pct / 100",
    )
    dimensions_scored: int = Field(
        description="Number of dimensions with data available",
    )
    dimensions_total: int = Field(
        description="Total number of dimensions in this category",
    )
    data_coverage_pct: float = Field(
        description="Percentage of dimensions with data available",
    )


def _default_dimension_scores() -> list[HazardDimensionScore]:
    """Default factory for dimension scores list."""
    return []


def _default_category_scores() -> dict[str, CategoryScore]:
    """Default factory for category scores dict."""
    return {}


def _default_interaction_effects() -> list[InteractionEffect]:
    """Default factory for interaction effects list."""
    return []


class InteractionEffect(BaseModel):
    """Named or dynamic interaction effect.

    Named interactions are branded patterns (e.g., 'Rookie Rocket')
    defined in hazard_interactions.json. Dynamic interactions are
    detected algorithmically when multiple dimensions are elevated.
    """

    model_config = ConfigDict(frozen=False)

    interaction_id: str = Field(
        description="Interaction identifier (e.g., 'ROOKIE_ROCKET')",
    )
    name: str = Field(
        description="Human-readable name (e.g., 'Rookie Rocket')",
    )
    description: str = Field(
        description="Description of the interaction pattern",
    )
    triggered_dimensions: list[str] = Field(
        default_factory=_default_str_list,
        description="Dimension IDs that triggered this interaction",
    )
    multiplier: float = Field(
        description="Multiplier applied to IES (e.g., 1.3)",
    )
    is_named: bool = Field(
        default=True,
        description="True for named patterns, False for dynamic detection",
    )


class HazardProfile(BaseModel):
    """Layer 2: Inherent Exposure Score from 47 hazard dimensions.

    The IES (0-100) represents the company's structural D&O exposure.
    IES=50 is neutral (1.0x filing rate multiplier). Higher IES means
    higher inherent exposure and a higher filing rate multiplier.

    The profile includes:
    - Individual dimension scores (47 total)
    - Category-level aggregated scores (7 categories)
    - Named interaction effects (branded patterns)
    - Dynamic interaction effects (algorithmic detection)
    - Overall data coverage and confidence assessment
    - Underwriter attention flags for meeting prep
    """

    model_config = ConfigDict(frozen=False)

    ies_score: float = Field(
        description="Adjusted Inherent Exposure Score (0-100)",
    )
    raw_ies_score: float = Field(
        description="Pre-interaction IES before multiplier adjustment",
    )
    ies_multiplier: float = Field(
        description="Filing rate multiplier from IES (1.0x at IES=50)",
    )
    dimension_scores: list[HazardDimensionScore] = Field(
        default_factory=_default_dimension_scores,
        description="Individual dimension scores (up to 47)",
    )
    category_scores: dict[str, CategoryScore] = Field(
        default_factory=_default_category_scores,
        description="Category-level scores keyed by category ID (H1-H7)",
    )
    named_interactions: list[InteractionEffect] = Field(
        default_factory=_default_interaction_effects,
        description="Named interaction patterns that triggered",
    )
    dynamic_interactions: list[InteractionEffect] = Field(
        default_factory=_default_interaction_effects,
        description="Dynamic interaction patterns detected",
    )
    interaction_multiplier: float = Field(
        default=1.0,
        description="Combined interaction multiplier applied to raw IES",
    )
    data_coverage_pct: float = Field(
        default=0.0,
        description="Percentage of 47 dimensions with actual data",
    )
    confidence_note: str = Field(
        default="",
        description="Confidence assessment based on data coverage",
    )
    underwriter_flags: list[str] = Field(
        default_factory=_default_str_list,
        description="Items flagged for underwriter attention / meeting prep",
    )


__all__ = [
    "CategoryScore",
    "HazardCategory",
    "HazardDimensionScore",
    "HazardProfile",
    "InteractionEffect",
]
