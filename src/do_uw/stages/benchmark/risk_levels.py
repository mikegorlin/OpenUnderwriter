"""Score-to-risk-level and threat label functions.

Relocated from render/ to benchmark/ to establish proper stage boundaries:
analytical logic belongs in benchmark/, not render/.

Public API:
- score_to_risk_level: Quality score -> risk level (LOW/MODERATE/ELEVATED/HIGH/CRITICAL)
- score_to_threat_label: AI risk composite score -> threat label (MODERATE/ELEVATED/HIGH)
- dim_score_threat: AI risk sub-dimension score -> threat level (MODERATE/ELEVATED/HIGH)
"""

from __future__ import annotations


def score_to_risk_level(score: float) -> str:
    """Map quality score to risk level for display.

    Thresholds:
    - 86+: LOW
    - 71-85: MODERATE
    - 51-70: ELEVATED
    - 26-50: HIGH
    - 0-25: CRITICAL
    """
    if score >= 86:
        return "LOW"
    if score >= 71:
        return "MODERATE"
    if score >= 51:
        return "ELEVATED"
    if score >= 26:
        return "HIGH"
    return "CRITICAL"


def score_to_threat_label(score: float) -> str:
    """Map 0-100 AI risk composite score to threat level.

    Thresholds:
    - 70+: HIGH
    - 40-69: ELEVATED
    - 0-39: MODERATE
    """
    if score >= 70.0:
        return "HIGH"
    if score >= 40.0:
        return "ELEVATED"
    return "MODERATE"


def dim_score_threat(score: float) -> str:
    """Map 0-10 AI risk sub-dimension score to threat level.

    Thresholds:
    - 7+: HIGH
    - 4-6: ELEVATED
    - 0-3: MODERATE
    """
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "ELEVATED"
    return "MODERATE"


__all__ = [
    "dim_score_threat",
    "score_to_risk_level",
    "score_to_threat_label",
]
