"""H/A/E multiplicative scoring lens.

Computes Host, Agent, Environment composite scores from classified signal
results, combines them multiplicatively (P = H x A x E), and maps to
5-tier decision recommendations. Liberty calibration adjusts weights by
attachment tier and product type.

This is the first ScoringLens implementation for v7.0. The legacy
10-factor additive model is wrapped as a separate lens.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from do_uw.stages.score.scoring_lens import (
    HAETier,
    ScoringLensResult,
)

__all__ = [
    "HAEScoringLens",
    "apply_liberty_calibration",
    "classify_tier_from_individual",
    "classify_tier_from_p",
    "compute_category_composite",
    "compute_multiplicative_product",
    "compute_subcategory_score",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Module-level caches (lazy singletons)
# ---------------------------------------------------------------

_FRAMEWORK_DIR = Path(__file__).resolve().parent.parent.parent / "brain" / "framework"

_scoring_model_cache: dict[str, Any] | None = None
_decision_framework_cache: dict[str, Any] | None = None
_rap_mapping_cache: dict[str, tuple[str, str]] | None = None
_brain_signals_cache: dict[str, dict[str, Any]] | None = None


def _load_scoring_model() -> dict[str, Any]:
    """Load scoring_model_design.yaml. Cached as module-level singleton."""
    global _scoring_model_cache
    if _scoring_model_cache is not None:
        return _scoring_model_cache
    path = _FRAMEWORK_DIR / "scoring_model_design.yaml"
    with open(path) as f:
        _scoring_model_cache = yaml.safe_load(f)
    return _scoring_model_cache  # type: ignore[return-value]


def _load_decision_framework() -> dict[str, Any]:
    """Load decision_framework.yaml. Cached as module-level singleton."""
    global _decision_framework_cache
    if _decision_framework_cache is not None:
        return _decision_framework_cache
    path = _FRAMEWORK_DIR / "decision_framework.yaml"
    with open(path) as f:
        _decision_framework_cache = yaml.safe_load(f)
    return _decision_framework_cache  # type: ignore[return-value]


def _load_rap_mapping() -> dict[str, tuple[str, str]]:
    """Load rap_signal_mapping.yaml -> {signal_id: (rap_class, rap_subcategory)}.

    Cached as module-level singleton.
    """
    global _rap_mapping_cache
    if _rap_mapping_cache is not None:
        return _rap_mapping_cache
    path = _FRAMEWORK_DIR / "rap_signal_mapping.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    mapping: dict[str, tuple[str, str]] = {}
    for entry in data.get("mappings", []):
        sid = entry.get("signal_id", "")
        rap_class = entry.get("rap_class", "")
        rap_sub = entry.get("rap_subcategory", "")
        if sid:
            mapping[sid] = (rap_class, rap_sub)
    _rap_mapping_cache = mapping
    return _rap_mapping_cache


def _load_brain_signals() -> dict[str, dict[str, Any]]:
    """Load brain signals for CRF flag lookup. Cached."""
    global _brain_signals_cache
    if _brain_signals_cache is not None:
        return _brain_signals_cache
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        data = load_signals()
        _brain_signals_cache = {
            s["id"]: s for s in data.get("signals", []) if "id" in s
        }
    except Exception:
        logger.warning("Could not load brain signals for HAE scoring")
        _brain_signals_cache = {}
    return _brain_signals_cache


# ---------------------------------------------------------------
# Signal score mapping
# ---------------------------------------------------------------


def _signal_score(status: str, threshold_level: str) -> float | None:
    """Map signal evaluation to numeric score.

    Per scoring_model_design.yaml signal_evaluation_mapping:
    - TRIGGERED + red = 1.0
    - TRIGGERED + yellow = 0.5
    - CLEAR = 0.0
    - SKIPPED / INFO = None (excluded from computation)
    """
    if status == "TRIGGERED":
        if threshold_level == "red":
            return 1.0
        return 0.5  # yellow or unspecified threshold
    if status == "CLEAR":
        return 0.0
    # SKIPPED, INFO, or unknown -> excluded
    return None


# ---------------------------------------------------------------
# Subcategory and category composite computation
# ---------------------------------------------------------------


def compute_subcategory_score(
    signal_results: dict[str, Any],
    subcategory: str,
    rap_mapping: dict[str, tuple[str, str]],
    brain_signals: dict[str, dict[str, Any]],
) -> float | None:
    """Compute weighted average score for signals in a subcategory.

    Excludes SKIPPED signals. CRF signals get 3x weight.
    Returns None if all signals are SKIPPED or missing.
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for sid, (_, sub) in rap_mapping.items():
        if sub != subcategory:
            continue
        raw = signal_results.get(sid)
        if raw is None or not isinstance(raw, dict):
            continue

        status = raw.get("status", "")
        threshold_level = raw.get("threshold_level", "")
        score = _signal_score(status, threshold_level)

        if score is None:
            continue

        # Determine weight
        weight = 1.0
        brain_sig = brain_signals.get(sid, {})
        if brain_sig.get("critical_red_flag"):
            weight *= 3.0

        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0.0:
        return None

    return weighted_sum / total_weight


def compute_category_composite(
    subcategory_scores: dict[str, float | None],
    weights: dict[str, dict[str, Any]],
) -> float:
    """Compute weighted average of non-null subcategory scores.

    Args:
        subcategory_scores: {subcategory_name: score_or_None}
        weights: {subcategory_name: {"weight": float, ...}}

    Returns:
        Composite score in [0, 1]. Returns 0.0 if all null.
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for sub_name, score in subcategory_scores.items():
        if score is None:
            continue
        weight_entry = weights.get(sub_name, {})
        w = weight_entry.get("weight", 0.0)
        weighted_sum += score * w
        total_weight += w

    if total_weight == 0.0:
        return 0.0

    return weighted_sum / total_weight


# ---------------------------------------------------------------
# Liberty calibration
# ---------------------------------------------------------------


def _get_attachment_tier(attachment: float) -> str:
    """Classify attachment into tier for Liberty calibration."""
    if attachment >= 50.0:
        return "high_attachment"
    if attachment >= 10.0:
        return "mid_attachment"
    return "low_attachment"


def apply_liberty_calibration(
    h: float,
    a: float,
    e: float,
    attachment: float | None,
    product: str | None,
) -> tuple[float, float, float]:
    """Apply Liberty calibration to composites.

    Adjusts weights by attachment tier and product type,
    clamping each result to [0, 1].
    """
    config = _load_scoring_model()
    liberty_cal = config.get("liberty_calibration", {})

    # Attachment multipliers
    h_att = a_att = e_att = 1.0
    if attachment is not None:
        tier = _get_attachment_tier(attachment)
        att_adj = liberty_cal.get("attachment_weight_adjustments", {}).get(tier, {})
        h_att = att_adj.get("host_weight_multiplier", 1.0)
        a_att = att_adj.get("agent_weight_multiplier", 1.0)
        e_att = att_adj.get("environment_weight_multiplier", 1.0)

    # Product multipliers
    h_prod = a_prod = e_prod = 1.0
    if product is not None:
        prod_adj = liberty_cal.get("product_weight_adjustments", {}).get(product, {})
        h_prod = prod_adj.get("host_weight_multiplier", 1.0)
        a_prod = prod_adj.get("agent_weight_multiplier", 1.0)
        e_prod = prod_adj.get("environment_weight_multiplier", 1.0)

    # Apply combined multipliers, clamp to [0, 1]
    adjusted_h = min(h * h_att * h_prod, 1.0)
    adjusted_a = min(a * a_att * a_prod, 1.0)
    adjusted_e = min(e * e_att * e_prod, 1.0)

    return adjusted_h, adjusted_a, adjusted_e


# ---------------------------------------------------------------
# Multiplicative product
# ---------------------------------------------------------------


def compute_multiplicative_product(
    h: float, a: float, e: float, floor: float = 0.05
) -> float:
    """Compute P = max(H, floor) x max(A, floor) x max(E, floor)."""
    return max(h, floor) * max(a, floor) * max(e, floor)


# ---------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------

# 5-tier thresholds (adapted from 6-tier design doc per CONTEXT.md):
# CAUTIOUS merged into ELEVATED, ADVERSE merged into HIGH_RISK.
_P_TIER_THRESHOLDS: list[tuple[float, float, HAETier]] = [
    (0.0, 0.01, HAETier.PREFERRED),
    (0.01, 0.08, HAETier.STANDARD),
    (0.08, 0.25, HAETier.ELEVATED),
    (0.25, 0.50, HAETier.HIGH_RISK),
    (0.50, 1.01, HAETier.PROHIBITED),  # 1.01 to include 1.0
]


def classify_tier_from_p(p: float) -> HAETier:
    """Map composite P score to 5-tier classification.

    Thresholds: PREFERRED [0, 0.01), STANDARD [0.01, 0.08),
    ELEVATED [0.08, 0.25), HIGH_RISK [0.25, 0.50), PROHIBITED [0.50, 1.0].
    """
    for low, high, tier in _P_TIER_THRESHOLDS:
        if low <= p < high:
            return tier
    return HAETier.PROHIBITED


def classify_tier_from_individual(
    h: float, a: float, e: float
) -> HAETier:
    """Classify tier from individual dimension criteria.

    Checks from most restrictive to least. Returns the most
    restrictive tier that any individual dimension triggers.
    """
    # HIGH_RISK: any composite above 0.70
    if h > 0.70 or a > 0.70 or e > 0.70:
        return HAETier.HIGH_RISK

    # ELEVATED: any composite above 0.50
    if h > 0.50 or a > 0.50 or e > 0.50:
        return HAETier.ELEVATED

    # STANDARD: within moderate bounds
    if h <= 0.45 and a <= 0.40 and e <= 0.50:
        if h <= 0.25 and a <= 0.20 and e <= 0.30:
            return HAETier.PREFERRED
        return HAETier.STANDARD

    # Between STANDARD max and ELEVATED threshold
    return HAETier.ELEVATED


# ---------------------------------------------------------------
# Recommendations lookup
# ---------------------------------------------------------------


def _get_recommendations(
    tier: HAETier, framework: dict[str, Any]
) -> dict[str, str]:
    """Look up 6 recommendation outputs for the given tier."""
    outputs = framework.get("recommendation_outputs", {})
    recs: dict[str, str] = {}
    for dim_key, dim_data in outputs.items():
        by_tier = dim_data.get("by_tier", {})
        value = by_tier.get(tier.value, "")
        # Handle list values (monitoring_triggers for ELEVATED/HIGH_RISK)
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        recs[dim_key] = value
    return recs


# ---------------------------------------------------------------
# HAEScoringLens implementation
# ---------------------------------------------------------------


class HAEScoringLens:
    """H/A/E multiplicative scoring lens.

    Implements the ScoringLens Protocol. Computes H/A/E composites
    from signal results, multiplies them, and assigns tiers.
    CRF discordance is applied externally (hae_crf.py).
    """

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
    ) -> ScoringLensResult:
        """Evaluate signal results through the H/A/E multiplicative model.

        Steps:
        1. Load configs (scoring model, decision framework, rap mapping)
        2. Compute subcategory scores for all 20 subcategories
        3. Compute H, A, E composites from subcategory scores + weights
        4. Apply Liberty calibration if attachment/product provided
        5. Compute P = H x A x E with floor
        6. Classify tier from P (composite path)
        7. Classify tier from individual criteria
        8. Take max(composite_tier, individual_tier) as pre-CRF tier
        9. Build recommendations from tier
        10. Return ScoringLensResult
        """
        scoring_model = _load_scoring_model()
        decision_fw = _load_decision_framework()
        rap_mapping = _load_rap_mapping()
        brain_signals = _load_brain_signals()

        composites_config = scoring_model.get("composites", {})
        floor = (
            scoring_model.get("interaction_model", {})
            .get("floor_adjustment", {})
            .get("floor_value", 0.05)
        )

        # Compute subcategory scores for each category
        host_weights = composites_config.get("host_subcategory_weights", {}).get("weights", {})
        agent_weights = composites_config.get("agent_subcategory_weights", {}).get("weights", {})
        env_weights = (
            composites_config.get("environment_subcategory_weights", {})
            .get("weights", {})
        )

        host_sub_scores: dict[str, float | None] = {}
        for sub_name in host_weights:
            host_sub_scores[sub_name] = compute_subcategory_score(
                signal_results, sub_name, rap_mapping, brain_signals
            )

        agent_sub_scores: dict[str, float | None] = {}
        for sub_name in agent_weights:
            agent_sub_scores[sub_name] = compute_subcategory_score(
                signal_results, sub_name, rap_mapping, brain_signals
            )

        env_sub_scores: dict[str, float | None] = {}
        for sub_name in env_weights:
            env_sub_scores[sub_name] = compute_subcategory_score(
                signal_results, sub_name, rap_mapping, brain_signals
            )

        # Compute category composites
        h = compute_category_composite(host_sub_scores, host_weights)
        a = compute_category_composite(agent_sub_scores, agent_weights)
        e = compute_category_composite(env_sub_scores, env_weights)

        # Apply Liberty calibration if provided
        if liberty_attachment is not None or liberty_product is not None:
            h, a, e = apply_liberty_calibration(
                h, a, e, liberty_attachment, liberty_product
            )

        # Compute multiplicative product
        p = compute_multiplicative_product(h, a, e, floor=floor)

        # Dual-path tier assignment
        composite_tier = classify_tier_from_p(p)
        individual_tier = classify_tier_from_individual(h, a, e)
        pre_crf_tier = max(composite_tier, individual_tier)

        # Determine tier source
        if individual_tier > composite_tier:
            tier_source = "individual"
        else:
            tier_source = "composite"

        # Build recommendations
        recommendations = _get_recommendations(pre_crf_tier, decision_fw)

        # Determine confidence based on signal coverage
        total_signals = len(rap_mapping)
        evaluated = sum(
            1 for sid in rap_mapping
            if sid in signal_results
            and isinstance(signal_results[sid], dict)
            and signal_results[sid].get("status") not in ("SKIPPED", None)
        )
        if total_signals > 0 and evaluated / total_signals >= 0.7:
            confidence = "HIGH"
        elif total_signals > 0 and evaluated / total_signals >= 0.4:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return ScoringLensResult(
            lens_name="hae_multiplicative",
            tier=pre_crf_tier,
            composites={"host": h, "agent": a, "environment": e},
            product_score=p,
            confidence=confidence,
            recommendations=recommendations,
            crf_vetoes=[],  # CRF applied externally
            tier_source=tier_source,
            individual_tier=individual_tier,
            composite_tier=composite_tier,
        )
