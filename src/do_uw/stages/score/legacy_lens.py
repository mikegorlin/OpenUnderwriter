"""Legacy 10-factor scoring wrapped as a ScoringLens adapter.

Adapts the existing 10-factor additive scoring output (ScoringResult)
into a ScoringLensResult for side-by-side comparison with the H/A/E
multiplicative model.

This is a POST-HOC adapter: it takes an already-computed ScoringResult
(via constructor) and wraps it. It does NOT re-run the 10-factor
scoring. This means it does not match the ScoringLens Protocol
signature exactly (which expects signal_results as input). The
Protocol defines the common interface for NEW scoring lenses; this
adapter wraps legacy output for comparison purposes only.

Legacy 10-factor is NEVER the primary scoring model -- H/A/E drives
the worksheet. Legacy is retained permanently for ongoing calibration.
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
    "LEGACY_TIER_MAP",
    "LegacyScoringLens",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Legacy tier to HAETier mapping
# ---------------------------------------------------------------

LEGACY_TIER_MAP: dict[str, str] = {
    "WIN": "PREFERRED",
    "WANT": "STANDARD",
    "WRITE": "STANDARD",
    "WATCH": "ELEVATED",
    "WALK": "HIGH_RISK",
    "NO_TOUCH": "PROHIBITED",
}
"""Maps legacy W-series tier names to 5-tier HAETier values.

WIN -> PREFERRED: Best risk, actively pursue.
WANT/WRITE -> STANDARD: Good accounts, quotable.
WATCH -> ELEVATED: Multiple flags, caution warranted.
WALK -> HIGH_RISK: Significant risk, Side A or high premium.
NO_TOUCH -> PROHIBITED: Cannot write.
"""

# ---------------------------------------------------------------
# Decision framework cache
# ---------------------------------------------------------------

_FRAMEWORK_DIR = Path(__file__).resolve().parent.parent.parent / "brain" / "framework"
_decision_framework_cache: dict[str, Any] | None = None


def _load_decision_framework() -> dict[str, Any]:
    """Load decision_framework.yaml. Cached as module-level singleton."""
    global _decision_framework_cache
    if _decision_framework_cache is not None:
        return _decision_framework_cache
    path = _FRAMEWORK_DIR / "decision_framework.yaml"
    with open(path) as f:
        _decision_framework_cache = yaml.safe_load(f)
    return _decision_framework_cache  # type: ignore[return-value]


def _get_recommendations(tier: HAETier) -> dict[str, str]:
    """Look up 6 recommendation outputs for the given tier."""
    framework = _load_decision_framework()
    outputs = framework.get("recommendation_outputs", {})
    recs: dict[str, str] = {}
    for dim_key, dim_data in outputs.items():
        by_tier = dim_data.get("by_tier", {})
        value = by_tier.get(tier.value, "")
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        recs[dim_key] = value
    return recs


# ---------------------------------------------------------------
# LegacyScoringLens implementation
# ---------------------------------------------------------------


class LegacyScoringLens:
    """Legacy 10-factor scoring wrapped as a ScoringLens adapter.

    This is a post-hoc adapter: pass an already-computed ScoringResult
    to the constructor, then call evaluate() to get a ScoringLensResult.

    The evaluate() signature accepts signal_results for Protocol
    compatibility, but the actual scoring comes from the ScoringResult
    passed at construction time.
    """

    def __init__(self, scoring_result: Any) -> None:
        """Store the legacy ScoringResult for wrapping.

        Args:
            scoring_result: A ScoringResult from the legacy 10-factor
                pipeline (imported as Any to avoid circular import).
        """
        self._scoring_result = scoring_result

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
    ) -> ScoringLensResult:
        """Wrap legacy scoring output as ScoringLensResult.

        Maps the legacy tier to HAETier, normalizes quality_score to
        [0, 1] product_score, and builds recommendations from the
        decision framework.
        """
        sr = self._scoring_result

        # Map legacy tier to HAETier
        hae_tier = HAETier.STANDARD  # default if tier missing
        if sr.tier is not None:
            tier_name = sr.tier.tier.value if hasattr(sr.tier.tier, "value") else str(sr.tier.tier)
            mapped = LEGACY_TIER_MAP.get(tier_name, "STANDARD")
            hae_tier = HAETier(mapped)

        # Normalize quality_score to [0, 1]
        # Legacy quality_score is 0-100; product_score is 0-1
        product_score = sr.quality_score / 100.0

        # Build recommendations from decision framework
        try:
            recommendations = _get_recommendations(hae_tier)
        except Exception:
            logger.warning("Could not load decision framework for legacy lens")
            recommendations = {}

        return ScoringLensResult(
            lens_name="legacy_10_factor",
            tier=hae_tier,
            composites={"host": 0, "agent": 0, "environment": 0},
            product_score=product_score,
            confidence="HIGH",  # Legacy model always has data
            recommendations=recommendations,
            crf_vetoes=[],
            tier_source="legacy_adapter",
            individual_tier=None,
            composite_tier=None,
        )
