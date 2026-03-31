"""Interaction effect detection for hazard profile.

Detects named interaction patterns (branded risk combinations like
'Rookie Rocket') and dynamic co-occurrence effects when multiple
dimensions are simultaneously elevated.

Named interactions are defined in hazard_interactions.json. Each
requires ALL specified dimensions to exceed their threshold. When
triggered, the multiplier is interpolated within the defined range
based on how far dimensions exceed their thresholds.

Dynamic interactions are detected algorithmically:
- Elevated co-occurrence: 5+ dimensions above 60% threshold
- Category concentration: 3+ elevated dimensions in one category
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.hazard_profile import InteractionEffect

logger = logging.getLogger(__name__)

# Type alias for dimension score dicts from dimension_scoring.py
_DimScore = dict[str, Any]


def detect_named_interactions(
    dimension_scores: list[_DimScore],
    config: dict[str, Any],
) -> list[InteractionEffect]:
    """Detect named interaction patterns from config.

    For each named interaction in config, check if ALL required
    dimensions meet their min_score_pct threshold. When triggered,
    interpolate multiplier within multiplier_range based on average
    excess above threshold.

    Parameters
    ----------
    dimension_scores : list[dict]
        Scored dimensions from score_all_dimensions(). Each dict
        has keys: dimension_id, normalized_score, etc.
    config : dict
        Full hazard_interactions.json config.

    Returns
    -------
    list[InteractionEffect]
        Named interactions that triggered, each with is_named=True.
    """
    named_configs: list[dict[str, Any]] = config.get("named_interactions", [])
    score_lookup = {d["dimension_id"]: d for d in dimension_scores}
    effects: list[InteractionEffect] = []

    for interaction in named_configs:
        interaction_id = str(interaction.get("id", "UNKNOWN"))
        name = str(interaction.get("name", interaction_id))
        description = str(interaction.get("description", ""))
        required: dict[str, dict[str, Any]] = interaction.get(
            "required_dimensions", {}
        )
        mult_range: list[float] = interaction.get("multiplier_range", [1.0, 1.0])

        if len(mult_range) < 2:
            continue

        # Check if ALL required dimensions meet their threshold
        triggered_dims: list[str] = []
        excess_total = 0.0
        all_met = True

        for dim_id, req in required.items():
            min_pct = float(req.get("min_score_pct", 50))
            dim_score = score_lookup.get(dim_id)
            if dim_score is None:
                all_met = False
                break

            normalized = float(dim_score.get("normalized_score", 0))
            if normalized < min_pct:
                all_met = False
                break

            triggered_dims.append(dim_id)
            excess_total += normalized - min_pct

        if not all_met or not triggered_dims:
            continue

        # Interpolate multiplier based on average excess above threshold
        avg_excess = excess_total / len(triggered_dims) if triggered_dims else 0.0
        # Max reasonable excess is ~40 percentage points (from 60% threshold to 100%)
        max_excess = 40.0
        fraction = min(avg_excess / max_excess, 1.0)
        multiplier = mult_range[0] + fraction * (mult_range[1] - mult_range[0])

        effects.append(
            InteractionEffect(
                interaction_id=interaction_id,
                name=name,
                description=description,
                triggered_dimensions=triggered_dims,
                multiplier=round(multiplier, 3),
                is_named=True,
            )
        )

        logger.info(
            "Named interaction triggered: %s (multiplier=%.3f, dims=%s)",
            name,
            multiplier,
            triggered_dims,
        )

    return effects


def detect_dynamic_interactions(
    dimension_scores: list[_DimScore],
    config: dict[str, Any],
) -> list[InteractionEffect]:
    """Detect dynamic interaction effects from elevated dimension clustering.

    Two types of dynamic detection:
    1. Elevated co-occurrence: When 5+ dimensions score above 60%
    2. Category concentration: When 3+ dimensions in one category
       are elevated

    Parameters
    ----------
    dimension_scores : list[dict]
        Scored dimensions from score_all_dimensions().
    config : dict
        Full hazard_interactions.json config.

    Returns
    -------
    list[InteractionEffect]
        Dynamic interactions detected, each with is_named=False.
    """
    dynamic_cfg: dict[str, Any] = config.get("dynamic_detection", {})
    min_elevated = int(dynamic_cfg.get("min_elevated_dimensions", 5))
    threshold_pct = float(dynamic_cfg.get("elevated_threshold_pct", 60))
    co_mult_range: list[float] = dynamic_cfg.get(
        "co_occurrence_multiplier", [1.05, 1.15]
    )
    cat_conc_min = int(dynamic_cfg.get("category_concentration_min", 3))
    cat_conc_mult = float(dynamic_cfg.get("category_concentration_multiplier", 1.05))

    effects: list[InteractionEffect] = []

    # Find all elevated dimensions
    elevated: list[_DimScore] = [
        d
        for d in dimension_scores
        if float(d.get("normalized_score", 0)) >= threshold_pct
    ]

    # 1. Elevated co-occurrence
    if len(elevated) >= min_elevated and len(co_mult_range) >= 2:
        # Interpolate multiplier based on count above threshold
        # At min_elevated: low end. At min_elevated + 5: high end.
        excess_count = len(elevated) - min_elevated
        max_additional = 5.0
        fraction = min(excess_count / max_additional, 1.0)
        multiplier = co_mult_range[0] + fraction * (co_mult_range[1] - co_mult_range[0])

        elevated_ids = [str(d.get("dimension_id", "")) for d in elevated]

        effects.append(
            InteractionEffect(
                interaction_id="ELEVATED_CO_OCCURRENCE",
                name="Elevated Co-occurrence",
                description=(
                    f"{len(elevated)} dimensions scoring above "
                    f"{threshold_pct:.0f}% threshold"
                ),
                triggered_dimensions=elevated_ids,
                multiplier=round(multiplier, 3),
                is_named=False,
            )
        )

        logger.info(
            "Dynamic co-occurrence: %d elevated dimensions (multiplier=%.3f)",
            len(elevated),
            multiplier,
        )

    # 2. Category concentration
    category_counts: dict[str, list[str]] = {}
    for d in elevated:
        cat = str(d.get("category", ""))
        dim_id = str(d.get("dimension_id", ""))
        if cat not in category_counts:
            category_counts[cat] = []
        category_counts[cat].append(dim_id)

    for cat, dim_ids in category_counts.items():
        if len(dim_ids) >= cat_conc_min:
            effects.append(
                InteractionEffect(
                    interaction_id=f"CATEGORY_CONCENTRATION_{cat}",
                    name=f"Category Concentration ({cat})",
                    description=(
                        f"{len(dim_ids)} elevated dimensions in "
                        f"category {cat}"
                    ),
                    triggered_dimensions=dim_ids,
                    multiplier=cat_conc_mult,
                    is_named=False,
                )
            )

            logger.info(
                "Category concentration in %s: %d dimensions (multiplier=%.3f)",
                cat,
                len(dim_ids),
                cat_conc_mult,
            )

    return effects


__all__ = [
    "detect_dynamic_interactions",
    "detect_named_interactions",
]
