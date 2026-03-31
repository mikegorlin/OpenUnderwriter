"""Scenario generator and risk cluster context builder.

Generates company-specific score-impact scenarios and groups factors
into risk clusters. Display-only logic -- no new scores are created.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier config loading
# ---------------------------------------------------------------------------

_SCORING_CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent / "brain" / "config" / "scoring.json"
)


def _load_tier_config() -> list[dict[str, Any]]:
    """Load tier boundaries from scoring.json."""
    try:
        with open(_SCORING_CONFIG_PATH) as f:
            config = json.load(f)
        tiers = config.get("tiers", [])
        if tiers and isinstance(tiers, list) and "min_score" in tiers[0]:
            return tiers
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load scoring.json tier config: %s", e)
    return _FALLBACK_TIERS


_FALLBACK_TIERS: list[dict[str, Any]] = [
    {"tier": "WIN", "min_score": 86, "max_score": 100},
    {"tier": "WANT", "min_score": 71, "max_score": 85},
    {"tier": "WRITE", "min_score": 51, "max_score": 70},
    {"tier": "WATCH", "min_score": 31, "max_score": 50},
    {"tier": "WALK", "min_score": 11, "max_score": 30},
    {"tier": "NO_TOUCH", "min_score": 0, "max_score": 10},
]


def _classify_tier_simple(
    quality_score: float,
    tier_config: list[dict[str, Any]],
) -> str:
    """Classify quality score into a tier name string.

    Uses the same logic as tier_classification.classify_tier()
    but returns a plain string to avoid import coupling.
    """
    for entry in tier_config:
        mn = int(entry.get("min_score", 0))
        mx = int(entry.get("max_score", 100))
        if mn <= quality_score <= mx:
            return str(entry.get("tier", "NO_TOUCH"))
    return "NO_TOUCH"


# ---------------------------------------------------------------------------
# Scenario templates
# ---------------------------------------------------------------------------

_SCENARIO_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "SCA_FILED",
        "name": "Securities Class Action Filed",
        "description": "New SCA complaint filed alleging securities fraud",
        "condition": "no_active_sca",
        "factor_deltas": {"F1": 20},
        "probability_impact": "HIGH",
    },
    {
        "id": "SCA_ESCALATION",
        "name": "SCA Escalation (Class Certified)",
        "description": "Existing SCA survives motion to dismiss, class certified",
        "condition": "has_active_sca",
        "factor_deltas": {"F1": 20, "F9": 4},
        "probability_impact": "VERY_HIGH",
    },
    {
        "id": "EARNINGS_MISS_DROP",
        "name": "Earnings Miss + 30% Stock Drop",
        "description": "Company misses earnings guidance, stock drops 30%+ in a week",
        "condition": "always",
        "factor_deltas": {"F2": 12, "F5": 8},
        "probability_impact": "ELEVATED",
    },
    {
        "id": "RESTATEMENT",
        "name": "Financial Restatement",
        "description": "Material restatement of prior financials",
        "condition": "always",
        "factor_deltas": {"F3": 15, "F1": 10},
        "probability_impact": "VERY_HIGH",
    },
    {
        "id": "INSIDER_DUMP",
        "name": "Insider Selling Accelerates",
        "description": "C-suite insiders sell >$10M in stock within 30 days",
        "condition": "has_insider_selling",
        "factor_deltas": {"F6": 8, "F2": 5},
        "probability_impact": "MODERATE",
    },
    {
        "id": "REGULATORY_ACTION",
        "name": "SEC Investigation Announced",
        "description": "SEC opens formal investigation into company disclosures",
        "condition": "always",
        "factor_deltas": {"F1": 15, "F9": 6},
        "probability_impact": "HIGH",
    },
    {
        "id": "GOVERNANCE_CRISIS",
        "name": "CEO Departure + Board Turnover",
        "description": "CEO exits abruptly, 2+ board members resign within 90 days",
        "condition": "always",
        "factor_deltas": {"F10": 8, "F9": 8},
        "probability_impact": "ELEVATED",
    },
    {
        "id": "POSITIVE_RESOLUTION",
        "name": "Litigation Resolved Favorably",
        "description": "Active SCA dismissed or settled below reserves",
        "condition": "has_active_sca",
        "factor_deltas": {"F1": -15},
        "probability_impact": "LOW",
    },
]


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------


def _evaluate_condition(
    condition: str,
    factor_map: dict[str, float],
) -> bool:
    """Evaluate a scenario condition against current factor scores."""
    if condition == "always":
        return True
    if condition == "no_active_sca":
        return factor_map.get("F1", 0.0) < 15.0
    if condition == "has_active_sca":
        return factor_map.get("F1", 0.0) >= 15.0
    if condition == "has_insider_selling":
        return factor_map.get("F6", 0.0) > 0.0
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_scenarios(
    state: Any,
) -> list[dict[str, Any]]:
    """Generate company-specific score-impact scenarios.

    For each applicable scenario template, applies factor deltas to
    current scores, computes the new quality score, and re-classifies
    the tier.

    Args:
        state: AnalysisState with scoring.factor_scores populated.

    Returns:
        List of 5-7 scenario dicts, each with:
        - id, name, description
        - current_score, scenario_score, score_delta
        - current_tier, scenario_tier
        - factor_deltas (list of per-factor changes)
        - probability_impact
    """
    scoring = getattr(state, "scoring", None)
    if scoring is None:
        return []

    factor_scores = getattr(scoring, "factor_scores", None)
    if not factor_scores:
        return []

    quality_score = safe_float(getattr(scoring, "quality_score", 100.0))

    # Build factor map: {factor_id: (points_deducted, max_points)}
    factor_map: dict[str, tuple[float, int]] = {}
    for fs in factor_scores:
        fid = getattr(fs, "factor_id", "")
        pts = safe_float(getattr(fs, "points_deducted", 0.0))
        mx = int(safe_float(getattr(fs, "max_points", 0.0)))
        factor_map[fid] = (pts, mx)

    pts_map = {fid: pts for fid, (pts, _) in factor_map.items()}

    # Load tier config
    tier_config = _load_tier_config()
    current_tier = _classify_tier_simple(quality_score, tier_config)

    # Evaluate scenarios
    scenarios: list[dict[str, Any]] = []
    for template in _SCENARIO_TEMPLATES:
        if not _evaluate_condition(template["condition"], pts_map):
            continue

        # Apply deltas
        deltas = template["factor_deltas"]
        new_pts_map: dict[str, float] = {}
        factor_delta_details: list[dict[str, Any]] = []

        for fid, (current_pts, max_pts) in factor_map.items():
            delta = deltas.get(fid, 0)
            # For delta scenarios, the delta represents the TARGET deduction
            # not an additive change. If delta is specified, set deduction to
            # min(max(current + adjustment, 0), max_points).
            if fid in deltas:
                delta_val = deltas[fid]
                if delta_val < 0:
                    # Negative = improvement (reduce deduction)
                    new_pts = max(current_pts + delta_val, 0.0)
                else:
                    # Positive = worsening (set to delta if higher)
                    new_pts = min(max(current_pts, delta_val), float(max_pts))
            else:
                new_pts = current_pts
            new_pts_map[fid] = new_pts

            if fid in deltas:
                factor_delta_details.append({
                    "factor_id": fid,
                    "factor_name": fid,
                    "current_points": round(current_pts, 1),
                    "scenario_points": round(new_pts, 1),
                    "max_points": max_pts,
                })

        # Compute scenario score
        total_deductions = sum(new_pts_map.values())
        scenario_score = max(0.0, min(100.0, 100.0 - total_deductions))
        scenario_score = round(scenario_score, 1)
        score_delta = round(scenario_score - quality_score, 1)

        scenario_tier = _classify_tier_simple(scenario_score, tier_config)

        scenarios.append({
            "id": template["id"],
            "name": template["name"],
            "description": template["description"],
            "factor_deltas": factor_delta_details,
            "current_score": round(quality_score, 1),
            "scenario_score": scenario_score,
            "current_tier": current_tier,
            "scenario_tier": scenario_tier,
            "score_delta": score_delta,
            "probability_impact": template["probability_impact"],
        })

    # Sort by absolute impact (most impactful first)
    scenarios.sort(key=lambda s: abs(s["score_delta"]), reverse=True)

    # Trim to 7 max
    if len(scenarios) > 7:
        scenarios = scenarios[:7]

    return scenarios


# ---------------------------------------------------------------------------
# Risk cluster computation
# ---------------------------------------------------------------------------

_CLUSTER_DEFINITIONS: list[tuple[str, list[str]]] = [
    ("Litigation & History", ["F1"]),
    ("Stock & Market", ["F2", "F5", "F6", "F7"]),
    ("Financial Integrity", ["F3"]),
    ("Corporate Actions", ["F4", "F8"]),
    ("Governance & Leadership", ["F9", "F10"]),
]


def compute_risk_clusters(
    factor_scores: list[Any],
) -> list[dict[str, Any]]:
    """Group factors into role-based risk clusters.

    Identifies where risk concentrates across the 10-factor model
    by grouping factors into 5 role dimensions and computing each
    cluster's share of total deductions.

    Args:
        factor_scores: List of FactorScore objects (or mocks with
            factor_id, points_deducted attributes).

    Returns:
        List of cluster dicts sorted by pct_of_total descending:
        - name: str
        - factor_ids: list[str]
        - total_points: float
        - pct_of_total: float (0.0-1.0)
        - is_dominant: bool (True if pct_of_total > 0.50)
    """
    if not factor_scores:
        return []

    # Build factor lookup
    factor_pts: dict[str, float] = {}
    for fs in factor_scores:
        fid = getattr(fs, "factor_id", "")
        pts = safe_float(getattr(fs, "points_deducted", 0.0))
        factor_pts[fid] = pts

    total_deductions = sum(factor_pts.values())
    if total_deductions == 0:
        total_deductions = 1.0  # Avoid division by zero

    clusters: list[dict[str, Any]] = []
    for name, factor_ids in _CLUSTER_DEFINITIONS:
        cluster_pts = sum(factor_pts.get(fid, 0.0) for fid in factor_ids)
        pct = cluster_pts / total_deductions
        clusters.append({
            "name": name,
            "factor_ids": factor_ids,
            "total_points": round(cluster_pts, 2),
            "pct_of_total": round(pct, 4),
            "is_dominant": pct > 0.50,
        })

    # Sort by pct_of_total descending
    clusters.sort(key=lambda c: c["pct_of_total"], reverse=True)

    return clusters


__all__ = ["compute_risk_clusters", "generate_scenarios"]
