"""Dimension scoring dispatcher: routes each dimension to its category scorer.

Loads dimension definitions from config, maps data via data_mapping, and
dispatches to the appropriate category scorer (H1-H7). Returns a list of
HazardDimensionScore objects (one per dimension) for aggregation by the
hazard engine (Plan 03).

When the HazardDimensionScore model is not yet available (parallel build),
returns raw tuples that can be converted later.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData
from do_uw.stages.analyze.layers.hazard.data_mapping import map_dimension_data

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default neutral score percentage when no data is available.
# 35% maps to MODERATE (not ELEVATED) in analysis.py thresholds,
# which is the appropriate baseline when we have no data.
_DEFAULT_NEUTRAL_PCT = 35.0

# ---------------------------------------------------------------------------
# Category scorer type: (dim_id, dim_config, data) -> (raw, sources, evidence)
# ---------------------------------------------------------------------------

_ScorerResult = tuple[float, list[str], list[str]]


def _get_category_scorer(
    category: str,
) -> Any:
    """Lazily import and return the scorer function for a category.

    Uses lazy imports to avoid circular dependencies and to allow
    category files to be created independently.
    """
    if category == "H1":
        from do_uw.stages.analyze.layers.hazard.dimension_h1_business import score_h1_dimension

        return score_h1_dimension
    if category == "H2":
        from do_uw.stages.analyze.layers.hazard.dimension_h2_people import score_h2_dimension

        return score_h2_dimension
    if category == "H3":
        from do_uw.stages.analyze.layers.hazard.dimension_h3_financial import score_h3_dimension

        return score_h3_dimension
    if category == "H4":
        from do_uw.stages.analyze.layers.hazard.dimension_h4_governance import score_h4_dimension

        return score_h4_dimension
    if category == "H5":
        from do_uw.stages.analyze.layers.hazard.dimension_h5_maturity import score_h5_dimension

        return score_h5_dimension
    if category == "H6":
        from do_uw.stages.analyze.layers.hazard.dimension_h6_environment import (
            score_h6_dimension,
        )

        return score_h6_dimension
    if category == "H7":
        from do_uw.stages.analyze.layers.hazard.dimension_h7_emerging import score_h7_dimension

        return score_h7_dimension
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Dimension score as a dict (model-independent representation)
DimensionScoreDict = dict[str, Any]


def score_single_dimension(
    dim_id: str,
    dim_config: dict[str, Any],
    data: dict[str, Any],
) -> DimensionScoreDict:
    """Score a single dimension and return a dict representation.

    Parameters
    ----------
    dim_id : str
        Dimension identifier (e.g., "H1-01").
    dim_config : dict
        Dimension configuration from hazard_weights.json. Expected keys:
        ``name``, ``max_score``, ``weight``, ``category``.
    data : dict
        Mapped data from ``map_dimension_data()``. Empty dict means
        no data available.

    Returns
    -------
    DimensionScoreDict
        Dict with keys matching HazardDimensionScore fields.
    """
    max_score = float(dim_config.get("max_score", 5))
    default_score_pct = float(dim_config.get("default_score_pct", _DEFAULT_NEUTRAL_PCT))
    category = dim_id.split("-")[0]  # "H1", "H2", etc.

    # No data -> neutral default
    if not data:
        neutral_raw = max_score * (default_score_pct / 100.0)
        return {
            "dimension_id": dim_id,
            "dimension_name": dim_config.get("name", dim_id),
            "category": category,
            "raw_score": round(neutral_raw, 2),
            "max_score": max_score,
            "normalized_score": round(default_score_pct, 1),
            "weight": float(dim_config.get("weight", 1.0)),
            "data_available": False,
            "data_tier": "unavailable",
            "data_sources": [],
            "evidence": ["No data available — scored at baseline (MODERATE)"],
        }

    # Dispatch to category scorer
    scorer = _get_category_scorer(category)
    if scorer is None:
        logger.warning("No scorer for category %s (dim %s)", category, dim_id)
        neutral_raw = max_score * (default_score_pct / 100.0)
        return {
            "dimension_id": dim_id,
            "dimension_name": dim_config.get("name", dim_id),
            "category": category,
            "raw_score": round(neutral_raw, 2),
            "max_score": max_score,
            "normalized_score": round(default_score_pct, 1),
            "weight": float(dim_config.get("weight", 1.0)),
            "data_available": False,
            "data_tier": "unavailable",
            "data_sources": [],
            "evidence": [f"No scorer implemented for category {category}."],
        }

    raw_score, data_sources, evidence = scorer(dim_id, dim_config, data)

    # Clamp to [0, max_score]
    raw_score = max(0.0, min(float(raw_score), max_score))
    normalized = (raw_score / max_score * 100.0) if max_score > 0 else 0.0

    data_tier = data.get("_data_tier", "primary")

    # Proxy-scored dimensions are data_available=True with evidence note
    if data_tier == "proxy":
        evidence.append("Estimated from related indicators.")

    return {
        "dimension_id": dim_id,
        "dimension_name": dim_config.get("name", dim_id),
        "category": category,
        "raw_score": round(raw_score, 2),
        "max_score": max_score,
        "normalized_score": round(normalized, 1),
        "weight": float(dim_config.get("weight", 1.0)),
        "data_available": True,
        "data_tier": data_tier,
        "data_sources": data_sources,
        "evidence": evidence,
    }


def score_all_dimensions(
    extracted: ExtractedData,
    company: CompanyProfile,
    config: dict[str, Any],
) -> list[DimensionScoreDict]:
    """Score all dimensions defined in config and return score dicts.

    Parameters
    ----------
    extracted : ExtractedData
        Structured data from EXTRACT stage.
    company : CompanyProfile
        Company identity and profile from RESOLVE/EXTRACT.
    config : dict
        Full hazard weights config. Expected structure::

            {
                "dimensions": {
                    "H1-01": {"name": "...", "max_score": 10, ...},
                    ...
                }
            }

    Returns
    -------
    list[DimensionScoreDict]
        One score dict per dimension, ordered by dimension ID.
    """
    dimensions: dict[str, dict[str, Any]] = config.get("dimensions", {})
    results: list[DimensionScoreDict] = []

    for dim_id in sorted(dimensions.keys()):
        dim_cfg = dimensions[dim_id]
        data = map_dimension_data(dim_id, extracted, company, config)
        score_dict = score_single_dimension(dim_id, dim_cfg, data)
        results.append(score_dict)

    logger.info(
        "Scored %d dimensions: %d with data, %d neutral defaults",
        len(results),
        sum(1 for r in results if r["data_available"]),
        sum(1 for r in results if not r["data_available"]),
    )

    return results
