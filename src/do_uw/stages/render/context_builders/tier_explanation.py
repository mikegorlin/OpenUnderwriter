"""Algorithmic tier explanation generator.

Produces a 'Why TIER, not ADJACENT_TIER' narrative from ScoringResult data.
Purely algorithmic (no LLM). Analyzes factor contributions, computes
counterfactuals, and identifies proximity to tier boundaries.

Extracted from scoring_evaluative.py (Phase 116-05) for 300-line compliance.
"""

from __future__ import annotations

from typing import Any

# Ordered tier list for adjacency lookups (lowest to highest)
_TIER_ORDER = ["NO_TOUCH", "WALK", "WATCH", "WRITE", "WANT", "WIN"]

_TIER_BOUNDARIES: dict[str, tuple[int, int]] = {
    "WIN": (86, 100),
    "WANT": (71, 85),
    "WRITE": (51, 70),
    "WATCH": (31, 50),
    "WALK": (11, 30),
    "NO_TOUCH": (0, 10),
}


def generate_tier_explanation(scoring_result: Any) -> str:
    """Generate algorithmic 'Why TIER, not ADJACENT_TIER' narrative.

    Purely algorithmic (no LLM). Analyzes factor contributions, computes
    counterfactuals (what if factor X were clean?), and identifies
    proximity to tier boundaries.

    Args:
        scoring_result: ScoringResult with quality_score, tier, and factor_scores.

    Returns:
        Multi-sentence narrative explaining tier placement.
    """
    score = scoring_result.quality_score
    tier_obj = scoring_result.tier
    if tier_obj is None:
        return f"Quality score of {score:.1f}. Tier classification not available."

    tier_name = tier_obj.tier.value if hasattr(tier_obj.tier, "value") else str(tier_obj.tier)
    tier_low = tier_obj.score_range_low
    tier_high = tier_obj.score_range_high

    parts: list[str] = []

    # Opening: score and tier placement
    parts.append(
        f"Quality score of {score:.1f} places this risk in {tier_name} "
        f"tier ({tier_low}-{tier_high})."
    )

    # Factor analysis
    factors = scoring_result.factor_scores or []
    active = sorted(
        [f for f in factors if f.points_deducted > 0],
        key=lambda f: f.points_deducted,
        reverse=True,
    )

    if not active:
        parts.append("No risk deductions recorded -- clean across all factors.")
        return " ".join(parts)

    total_deducted = sum(f.points_deducted for f in active)

    # Top drag factor
    top = active[0]
    pct = (top.points_deducted / total_deducted * 100) if total_deducted > 0 else 0
    parts.append(
        f"Heaviest drag: {top.factor_id} {top.factor_name} "
        f"({top.points_deducted:.0f}/{top.max_points}), accounting for "
        f"{pct:.0f}% of total deductions."
    )

    # Find tier above
    tier_idx = _TIER_ORDER.index(tier_name) if tier_name in _TIER_ORDER else -1
    above_tier = _TIER_ORDER[tier_idx + 1] if 0 <= tier_idx < len(_TIER_ORDER) - 1 else None

    if above_tier:
        above_min = _TIER_BOUNDARIES[above_tier][0]
        gap = above_min - score
        parts.append(f"To reach {above_tier}, score would need +{gap:.1f} points.")

        # Counterfactual: if each factor were clean, would we reach above?
        for f in active:
            hypothetical = score + f.points_deducted
            if hypothetical >= above_min:
                parts.append(
                    f"If {f.factor_id} {f.factor_name} were clean "
                    f"(0/{f.max_points}), score would be {hypothetical:.1f} "
                    f"-- {above_tier} tier."
                )
                break  # Only show first counterfactual that reaches above

    # Find tier below -- proximity warning
    below_tier = _TIER_ORDER[tier_idx - 1] if tier_idx > 0 else None
    if below_tier:
        below_max = _TIER_BOUNDARIES[below_tier][1]
        gap_below = score - below_max
        if 0 < gap_below < 5:
            parts.append(
                f"Warning: Only {gap_below:.1f} points above "
                f"{below_tier} boundary."
            )

    return " ".join(parts)


__all__ = ["generate_tier_explanation"]
