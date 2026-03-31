"""Hazard engine: computes IES from dimension scores with interactions.

Main entry point: compute_hazard_profile() takes extracted data, company
profile, classification, and config; returns a complete HazardProfile.

Steps:
1. Score all 55 dimensions via dimension_scoring.score_all_dimensions()
2. Aggregate dimension scores by category (weighted average)
3. Compute raw IES (0-100) from weighted category scores
4. Detect named + dynamic interaction effects
5. Apply interaction multiplier (capped at 2.0x)
6. Convert adjusted IES to filing rate multiplier via piecewise linear
7. Compute data coverage and confidence assessment
8. Collect underwriter flags from MEETING_PREP evidence notes

IES=50 is neutral (1.0x filing rate multiplier). Higher IES means
higher inherent exposure.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.classification import ClassificationResult
from do_uw.models.company import CompanyProfile
from do_uw.models.hazard_profile import (
    CategoryScore,
    HazardCategory,
    HazardDimensionScore,
    HazardProfile,
    InteractionEffect,
)
from do_uw.models.state import ExtractedData
from do_uw.stages.analyze.layers.hazard.dimension_scoring import (
    DimensionScoreDict,
    score_all_dimensions,
)
from do_uw.stages.analyze.layers.hazard.interaction_effects import (
    detect_dynamic_interactions,
    detect_named_interactions,
)

logger = logging.getLogger(__name__)

# Maximum combined interaction multiplier to prevent IES explosion.
_MAX_INTERACTION_MULTIPLIER = 2.0

# Prefix for underwriter attention flags in evidence notes.
_MEETING_PREP_PREFIX = "MEETING_PREP:"


def load_hazard_config() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load hazard_weights.json and hazard_interactions.json from config/.

    Returns
    -------
    tuple[dict, dict]
        (weights_config, interactions_config)
    """
    weights = load_config("hazard_weights")
    interactions = load_config("hazard_interactions")

    return weights, interactions


def _convert_to_dimension_score(
    score_dict: DimensionScoreDict,
) -> HazardDimensionScore:
    """Convert a plain dict score to a Pydantic HazardDimensionScore.

    The dimension_scoring module returns plain dicts to avoid dependency
    issues. This function converts them to the proper Pydantic model.
    """
    category_str = str(score_dict.get("category", "H1"))
    try:
        category = HazardCategory(category_str)
    except ValueError:
        category = HazardCategory.BUSINESS

    return HazardDimensionScore(
        dimension_id=str(score_dict.get("dimension_id", "")),
        dimension_name=str(score_dict.get("dimension_name", "")),
        category=category,
        raw_score=float(score_dict.get("raw_score", 0)),
        max_score=float(score_dict.get("max_score", 5)),
        normalized_score=float(score_dict.get("normalized_score", 50)),
        data_available=bool(score_dict.get("data_available", False)),
        data_sources=list(score_dict.get("data_sources", [])),
        evidence=list(score_dict.get("evidence", [])),
    )


def aggregate_by_category(
    dimension_scores: list[DimensionScoreDict],
    weights_config: dict[str, Any],
) -> dict[str, CategoryScore]:
    """Group dimension scores by category and compute weighted aggregates.

    For each category:
    - raw_score = weighted average of normalized scores within category
    - weighted_score = raw_score * category_weight_pct / 100
    - data_coverage_pct = (dimensions with data) / total in category

    Parameters
    ----------
    dimension_scores : list[dict]
        Score dicts from score_all_dimensions().
    weights_config : dict
        Full hazard_weights.json config with categories and dimensions.

    Returns
    -------
    dict[str, CategoryScore]
        Category scores keyed by category ID (H1-H7).
    """
    categories_config: dict[str, dict[str, Any]] = weights_config.get("categories", {})

    # Group dimensions by category
    by_category: dict[str, list[DimensionScoreDict]] = {}
    for d in dimension_scores:
        cat = str(d.get("category", ""))
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(d)

    result: dict[str, CategoryScore] = {}

    for cat_id, cat_config in categories_config.items():
        cat_dims = by_category.get(cat_id, [])
        weight_pct = float(cat_config.get("weight_pct", 0))
        cat_name = str(cat_config.get("name", cat_id))

        if not cat_dims:
            result[cat_id] = CategoryScore(
                category=HazardCategory(cat_id),
                category_name=cat_name,
                weight_pct=weight_pct,
                raw_score=0.0,
                weighted_score=0.0,
                dimensions_scored=0,
                dimensions_total=0,
                data_coverage_pct=0.0,
            )
            continue

        # Compute weighted average of normalized scores
        total_weight = 0.0
        weighted_sum = 0.0
        dims_with_data = 0

        for d in cat_dims:
            dim_weight = float(d.get("weight", 1.0))
            normalized = float(d.get("normalized_score", 50))
            weighted_sum += normalized * dim_weight
            total_weight += dim_weight
            if d.get("data_available", False):
                dims_with_data += 1

        raw_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        weighted_score = raw_score * weight_pct / 100.0
        coverage = (dims_with_data / len(cat_dims) * 100.0) if cat_dims else 0.0

        try:
            hazard_cat = HazardCategory(cat_id)
        except ValueError:
            hazard_cat = HazardCategory.BUSINESS

        result[cat_id] = CategoryScore(
            category=hazard_cat,
            category_name=cat_name,
            weight_pct=weight_pct,
            raw_score=round(raw_score, 2),
            weighted_score=round(weighted_score, 2),
            dimensions_scored=dims_with_data,
            dimensions_total=len(cat_dims),
            data_coverage_pct=round(coverage, 1),
        )

    return result


def compute_interaction_multiplier(
    named: list[InteractionEffect],
    dynamic: list[InteractionEffect],
) -> float:
    """Combine named and dynamic interaction multipliers.

    Total multiplier = product of all individual multipliers,
    capped at _MAX_INTERACTION_MULTIPLIER to prevent explosion.

    Parameters
    ----------
    named : list[InteractionEffect]
        Named interactions that triggered.
    dynamic : list[InteractionEffect]
        Dynamic interactions detected.

    Returns
    -------
    float
        Combined multiplier (1.0 if no interactions, capped at 2.0).
    """
    total = 1.0
    for effect in named:
        total *= effect.multiplier
    for effect in dynamic:
        total *= effect.multiplier

    return min(total, _MAX_INTERACTION_MULTIPLIER)


def _ies_to_filing_multiplier(
    ies: float,
    breakpoints: list[list[float]],
) -> float:
    """Convert IES to filing rate multiplier via piecewise linear interpolation.

    Breakpoints from classification.json ies_multiplier_breakpoints:
    [[0, 0.5], [20, 0.7], [35, 0.85], [50, 1.0], [65, 1.3],
     [80, 2.0], [90, 2.5], [100, 3.5]]

    IES=50 -> 1.0x (neutral). IES=0 -> 0.5x. IES=100 -> 3.5x.

    Parameters
    ----------
    ies : float
        Adjusted IES (0-100).
    breakpoints : list[list[float]]
        Pairs of [ies_value, multiplier] defining the piecewise function.

    Returns
    -------
    float
        Filing rate multiplier.
    """
    if not breakpoints:
        return 1.0

    # Sort by IES value
    bp = sorted(breakpoints, key=lambda x: x[0])

    # Below lowest breakpoint
    if ies <= bp[0][0]:
        return bp[0][1]

    # Above highest breakpoint
    if ies >= bp[-1][0]:
        return bp[-1][1]

    # Find surrounding breakpoints and interpolate
    for i in range(len(bp) - 1):
        ies_low, mult_low = bp[i]
        ies_high, mult_high = bp[i + 1]

        if ies_low <= ies <= ies_high:
            span = ies_high - ies_low
            if span == 0:
                return mult_low
            fraction = (ies - ies_low) / span
            return mult_low + fraction * (mult_high - mult_low)

    return 1.0


def _collect_underwriter_flags(
    dimension_scores: list[DimensionScoreDict],
) -> list[str]:
    """Extract underwriter attention flags from MEETING_PREP evidence.

    Scans all dimension evidence notes for items prefixed with
    "MEETING_PREP:" and returns them as underwriter flags.
    """
    flags: list[str] = []
    for d in dimension_scores:
        for note in d.get("evidence", []):
            note_str = str(note)
            if note_str.startswith(_MEETING_PREP_PREFIX):
                flag_text = note_str[len(_MEETING_PREP_PREFIX) :].strip()
                if flag_text:
                    flags.append(flag_text)
    return flags


def compute_hazard_profile(
    extracted: ExtractedData | None,
    company: CompanyProfile | None,
    classification: ClassificationResult,
    weights_config: dict[str, Any],
    interactions_config: dict[str, Any],
) -> HazardProfile:
    """Compute the full hazard profile (Layer 2) from extracted data.

    Main entry point for IES computation. Orchestrates:
    1. Dimension scoring (55 dimensions)
    2. Category aggregation (7 categories)
    3. Raw IES computation
    4. Interaction effect detection
    5. IES adjustment (capped multiplier)
    6. Filing rate multiplier conversion
    7. Data coverage and confidence assessment
    8. Underwriter flag collection

    Parameters
    ----------
    extracted : ExtractedData | None
        Structured data from EXTRACT stage. None = minimal scoring.
    company : CompanyProfile | None
        Company identity and profile. None = minimal scoring.
    classification : ClassificationResult
        Layer 1 classification result.
    weights_config : dict
        Full hazard_weights.json config.
    interactions_config : dict
        Full hazard_interactions.json config.

    Returns
    -------
    HazardProfile
        Complete hazard profile with IES, dimension scores,
        category scores, interactions, and metadata.
    """
    from do_uw.models.state import ExtractedData as ExtractedDataModel

    # Handle None inputs with defaults
    if extracted is None:
        extracted = ExtractedDataModel()
    if company is None:
        from do_uw.models.company import CompanyIdentity
        from do_uw.models.company import CompanyProfile as CompanyProfileModel
        company = CompanyProfileModel(identity=CompanyIdentity(ticker="UNKNOWN"))

    # Step 1: Score all dimensions
    dim_score_dicts = score_all_dimensions(extracted, company, weights_config)

    # Step 2: Aggregate by category
    category_scores = aggregate_by_category(dim_score_dicts, weights_config)

    # Step 3: Compute raw IES (sum of weighted category scores)
    raw_ies = sum(cs.weighted_score for cs in category_scores.values())
    raw_ies = max(0.0, min(100.0, raw_ies))

    # Step 4: Detect interaction effects
    named_interactions = detect_named_interactions(
        dim_score_dicts, interactions_config
    )
    dynamic_interactions = detect_dynamic_interactions(
        dim_score_dicts, interactions_config
    )

    # Step 5: Compute interaction multiplier and adjusted IES
    interaction_mult = compute_interaction_multiplier(
        named_interactions, dynamic_interactions
    )
    adjusted_ies = min(100.0, raw_ies * interaction_mult)

    # Step 6: Convert IES to filing rate multiplier
    # Load breakpoints from classification config (stored alongside IES config)
    # The breakpoints come from classification.json but we access them through
    # hazard engine since that's where they're consumed
    breakpoints: list[list[float]] = weights_config.get(
        "ies_multiplier_breakpoints", []
    )
    if not breakpoints:
        # Fallback: load from classification.json
        try:
            class_config = load_config("classification")
            breakpoints = class_config.get("ies_multiplier_breakpoints", [])
        except Exception:
            breakpoints = [[0, 0.5], [50, 1.0], [100, 3.5]]

    ies_multiplier = _ies_to_filing_multiplier(adjusted_ies, breakpoints)

    # Step 7: Data coverage and confidence
    total_dims = len(dim_score_dicts)
    dims_with_data = sum(1 for d in dim_score_dicts if d.get("data_available", False))
    data_coverage = (dims_with_data / total_dims * 100.0) if total_dims > 0 else 0.0

    missing_data = weights_config.get("missing_data_handling", {})
    low_threshold = float(missing_data.get("low_coverage_threshold_pct", 60))
    confidence_note = ""
    if data_coverage < low_threshold:
        confidence_note = str(
            missing_data.get(
                "low_coverage_note",
                "IES based on limited data coverage",
            )
        )
        confidence_note += f" ({data_coverage:.0f}% of dimensions have data)"

    # Step 8: Collect underwriter flags
    underwriter_flags = _collect_underwriter_flags(dim_score_dicts)

    # Convert dimension score dicts to Pydantic models
    dimension_models = [_convert_to_dimension_score(d) for d in dim_score_dicts]

    logger.info(
        "Hazard profile: raw_IES=%.1f adjusted_IES=%.1f multiplier=%.2fx "
        "coverage=%.0f%% interactions=%d named + %d dynamic",
        raw_ies,
        adjusted_ies,
        ies_multiplier,
        data_coverage,
        len(named_interactions),
        len(dynamic_interactions),
    )

    return HazardProfile(
        ies_score=round(adjusted_ies, 1),
        raw_ies_score=round(raw_ies, 1),
        ies_multiplier=round(ies_multiplier, 3),
        dimension_scores=dimension_models,
        category_scores=category_scores,
        named_interactions=named_interactions,
        dynamic_interactions=dynamic_interactions,
        interaction_multiplier=round(interaction_mult, 3),
        data_coverage_pct=round(data_coverage, 1),
        confidence_note=confidence_note,
        underwriter_flags=underwriter_flags,
    )


__all__ = [
    "aggregate_by_category",
    "compute_hazard_profile",
    "compute_interaction_multiplier",
    "load_hazard_config",
]
