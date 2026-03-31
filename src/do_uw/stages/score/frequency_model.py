"""Enhanced frequency model: classification x hazard x signal adjustments.

Computes filing probability from three orthogonal components:
1. Classification base rate (from Layer 1 classification engine)
2. Hazard multiplier (from Layer 2 IES profile)
3. Signal adjustments (from CRF triggers, pattern detection, elevated factors)

Formula: adjusted_probability = base_rate * hazard_mult * signal_mult

This replaces the ad-hoc tier-based probability + IES adjustment approach
with an explicit, traceable three-factor formula.

Phase 27 gap closure -- verification gap #2.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.scoring import FactorScore, PatternMatch, RedFlagResult
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signal configuration -- all multipliers in one place, not inline
# ---------------------------------------------------------------------------

_SIGNAL_CONFIG: dict[str, dict[str, float]] = {
    # CRF trigger count -> multiplier
    "crf": {
        "0": 1.0,
        "1": 1.15,
        "2": 1.30,
        "3+": 1.50,
    },
    # Active detected pattern count -> multiplier
    "pattern": {
        "0": 1.0,
        "1-2": 1.10,
        "3+": 1.25,
    },
    # Elevated factor ratio thresholds
    "factor": {
        "threshold_50": 1.15,  # >50% of factors elevated
        "threshold_75": 1.30,  # >75% of factors elevated
        "default": 1.0,
    },
    # Caps
    "caps": {
        "signal_max": 2.0,
        "probability_max": 50.0,
    },
}


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------


class EnhancedFrequency(BaseModel):
    """Result of the enhanced frequency model computation.

    Captures all three components and their product for full
    transparency and downstream audit trail.
    """

    model_config = ConfigDict(frozen=False)

    base_rate_pct: float = Field(
        description="Classification base filing rate (%)",
    )
    hazard_multiplier: float = Field(
        description="IES multiplier from hazard profile",
    )
    signal_multiplier: float = Field(
        description="Combined signal multiplier (CRF * pattern * factor)",
    )
    crf_signal: float = Field(
        description="CRF trigger contribution to signal",
    )
    pattern_signal: float = Field(
        description="Pattern detection contribution to signal",
    )
    factor_signal: float = Field(
        description="Factor elevation contribution to signal",
    )
    adjusted_probability_pct: float = Field(
        description="Final filing probability (%), capped at 50%",
    )
    methodology: str = Field(
        description=(
            "'classification x hazard x signal' or 'tier-based fallback'"
        ),
    )
    components: dict[str, float] = Field(
        default_factory=dict,
        description="Full breakdown for transparency",
    )


# ---------------------------------------------------------------------------
# Signal computation helpers
# ---------------------------------------------------------------------------


def _compute_crf_signal(red_flag_results: list[RedFlagResult]) -> float:
    """Compute CRF trigger signal multiplier.

    0 triggers = 1.0x, 1 = 1.15x, 2 = 1.30x, 3+ = 1.50x.
    """
    trigger_count = sum(1 for r in red_flag_results if r.triggered)
    crf_cfg = _SIGNAL_CONFIG["crf"]

    if trigger_count == 0:
        return crf_cfg["0"]
    if trigger_count == 1:
        return crf_cfg["1"]
    if trigger_count == 2:
        return crf_cfg["2"]
    return crf_cfg["3+"]


def _compute_pattern_signal(patterns: list[PatternMatch]) -> float:
    """Compute detected pattern signal multiplier.

    Filters to detected patterns only.
    0 detected = 1.0x, 1-2 = 1.10x, 3+ = 1.25x.
    """
    detected_count = sum(1 for p in patterns if p.detected)
    pattern_cfg = _SIGNAL_CONFIG["pattern"]

    if detected_count == 0:
        return pattern_cfg["0"]
    if detected_count <= 2:
        return pattern_cfg["1-2"]
    return pattern_cfg["3+"]


def _compute_factor_signal(factor_scores: list[FactorScore]) -> float:
    """Compute elevated factor ratio signal multiplier.

    A factor is 'elevated' when points_deducted > 50% of max_points.
    If >75% of factors are elevated -> 1.30x.
    If >50% of factors are elevated -> 1.15x.
    Otherwise -> 1.0x.
    """
    if not factor_scores:
        return _SIGNAL_CONFIG["factor"]["default"]

    elevated_count = sum(
        1
        for fs in factor_scores
        if fs.max_points > 0 and fs.points_deducted > 0.5 * fs.max_points
    )
    total = len(factor_scores)
    ratio = elevated_count / total

    factor_cfg = _SIGNAL_CONFIG["factor"]
    if ratio > 0.75:
        return factor_cfg["threshold_75"]
    if ratio > 0.50:
        return factor_cfg["threshold_50"]
    return factor_cfg["default"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_enhanced_frequency(
    state: AnalysisState,
    red_flag_results: list[RedFlagResult],
    patterns: list[PatternMatch],
    factor_scores: list[FactorScore],
) -> EnhancedFrequency:
    """Compute enhanced filing probability: classification x hazard x signal.

    Args:
        state: Full analysis state (reads classification and hazard_profile).
        red_flag_results: CRF gate evaluation results.
        patterns: All pattern matches (detected filtering done internally).
        factor_scores: All 10-factor scores.

    Returns:
        EnhancedFrequency with the adjusted probability and full breakdown.
    """
    caps = _SIGNAL_CONFIG["caps"]

    # --- Component 1: Base rate from classification ---
    methodology = "classification x hazard x signal"
    if (
        state.classification is not None
        and state.classification.base_filing_rate_pct > 0
    ):
        base_rate = state.classification.base_filing_rate_pct
    elif (
        state.scoring is not None
        and state.scoring.claim_probability is not None
    ):
        # Fallback: use existing tier-based claim probability
        base_rate = state.scoring.claim_probability.range_high_pct
        methodology = "tier-based fallback"
    else:
        # Last resort: industry average ~4%
        base_rate = 4.0
        methodology = "tier-based fallback"

    # --- Component 2: Hazard multiplier from IES ---
    if state.hazard_profile is not None:
        hazard_mult = state.hazard_profile.ies_multiplier
    else:
        hazard_mult = 1.0

    # --- Component 3: Signal adjustments ---
    crf_signal = _compute_crf_signal(red_flag_results)
    pattern_signal = _compute_pattern_signal(patterns)
    factor_signal = _compute_factor_signal(factor_scores)

    signal_mult = crf_signal * pattern_signal * factor_signal
    signal_mult = min(signal_mult, caps["signal_max"])

    # --- Final computation ---
    raw_probability = base_rate * hazard_mult * signal_mult
    adjusted_probability = min(raw_probability, caps["probability_max"])

    logger.info(
        "Enhanced frequency: %.2f%% base x %.2f hazard x %.2f signal "
        "= %.2f%% (%s)",
        base_rate,
        hazard_mult,
        signal_mult,
        adjusted_probability,
        methodology,
    )

    return EnhancedFrequency(
        base_rate_pct=round(base_rate, 4),
        hazard_multiplier=round(hazard_mult, 4),
        signal_multiplier=round(signal_mult, 4),
        crf_signal=round(crf_signal, 4),
        pattern_signal=round(pattern_signal, 4),
        factor_signal=round(factor_signal, 4),
        adjusted_probability_pct=round(adjusted_probability, 2),
        methodology=methodology,
        components={
            "base_rate_pct": round(base_rate, 4),
            "hazard_multiplier": round(hazard_mult, 4),
            "signal_multiplier": round(signal_mult, 4),
            "crf_signal": round(crf_signal, 4),
            "pattern_signal": round(pattern_signal, 4),
            "factor_signal": round(factor_signal, 4),
            "raw_probability_pct": round(raw_probability, 4),
            "capped_probability_pct": round(adjusted_probability, 2),
        },
    )


__all__ = ["EnhancedFrequency", "compute_enhanced_frequency"]
