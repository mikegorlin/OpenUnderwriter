"""Impact ranker for automatic check prioritization.

Ranks all checks by impact score = weight x fire_rate x severity to identify
the top N highest-impact checks for ground truth validation. Uses factor
max_points from scoring.json as the weight for each check's primary factor.

The ranking is fully automatic per CONTEXT.md decision -- no manual check
selection. The system identifies the most important checks to validate.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from do_uw.calibration.analyzer import CheckMetrics

logger = logging.getLogger(__name__)

# Severity scores for threshold levels
_SEVERITY_MAP: dict[str, float] = {
    "red": 3.0,
    "yellow": 2.0,
    "clear": 0.0,
}


def _default_scoring_path() -> Path:
    """Return the default path to scoring.json."""
    return Path(__file__).parent.parent / "brain" / "config" / "scoring.json"


class RankedCheck(BaseModel):
    """A check ranked by impact score."""

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(description="Unique check identifier")
    signal_name: str = Field(description="Human-readable check name")
    impact_score: float = Field(description="weight * fire_rate * severity")
    weight: float = Field(description="Max points of the check's highest-weight factor")
    fire_rate: float = Field(description="Proportion of tickers where check fired")
    severity: float = Field(description="Average severity across triggered tickers")
    factors: list[str] = Field(default_factory=list, description="Factor IDs for this check")
    rank: int = Field(default=0, description="1-based rank position")


class ImpactRanker:
    """Ranks checks by impact score for ground truth prioritization.

    Algorithm (per CONTEXT.md):
    1. Load scoring.json factor max_points
    2. For each check: weight = max(factor_weights) for mapped factors
    3. fire_rate from CheckMetrics
    4. severity = average threshold level (red=3, yellow=2, clear=0)
    5. impact_score = weight * fire_rate * severity
    6. Sort descending, return top N
    """

    def __init__(self, scoring_config_path: Path | None = None) -> None:
        """Initialize with scoring config for factor weights.

        Args:
            scoring_config_path: Path to scoring.json. Defaults to
                brain/scoring.json relative to this package.
        """
        config_path = scoring_config_path or _default_scoring_path()
        self._factor_weights = self._load_factor_weights(config_path)

    @staticmethod
    def _load_factor_weights(config_path: Path) -> dict[str, float]:
        """Load factor_id -> max_points mapping from scoring.json.

        Handles both dotted (F.1) and undotted (F1) factor IDs by
        normalizing to the undotted form used in signals.json.

        Args:
            config_path: Path to scoring.json.

        Returns:
            Dict mapping factor ID (e.g. "F1") to max_points.
        """
        weights: dict[str, float] = {}
        try:
            with config_path.open(encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Could not load scoring config from %s", config_path)
            return weights

        factors = data.get("factors", {})
        if not isinstance(factors, dict):
            return weights

        factors_dict = cast(dict[str, Any], factors)
        for _key, factor_cfg_raw in factors_dict.items():
            if not isinstance(factor_cfg_raw, dict):
                continue
            factor_cfg = cast(dict[str, Any], factor_cfg_raw)
            factor_id_raw = str(factor_cfg.get("factor_id", ""))
            max_points = float(factor_cfg.get("max_points", 0))
            # Normalize F.1 -> F1 for matching with signals.json
            factor_id = factor_id_raw.replace(".", "")
            weights[factor_id] = max_points

        return weights

    def rank(
        self,
        metrics: list[CheckMetrics],
        top_n: int = 20,
    ) -> list[RankedCheck]:
        """Rank checks by impact score and return top N.

        Args:
            metrics: List of CheckMetrics from CheckAnalyzer.
            top_n: Number of top checks to return (default 20).

        Returns:
            Top N checks ranked by impact score (descending).
        """
        ranked: list[RankedCheck] = []

        for cm in metrics:
            weight = self._get_weight(cm.factors)
            severity = self._compute_severity(cm.threshold_levels)
            impact_score = weight * cm.fire_rate * severity

            ranked.append(
                RankedCheck(
                    signal_id=cm.signal_id,
                    signal_name=cm.signal_name,
                    impact_score=impact_score,
                    weight=weight,
                    fire_rate=cm.fire_rate,
                    severity=severity,
                    factors=cm.factors,
                )
            )

        # Sort by impact_score descending, then by signal_id for stability
        ranked.sort(key=lambda r: (-r.impact_score, r.signal_id))

        # Assign 1-based ranks
        for i, r in enumerate(ranked):
            r.rank = i + 1

        return ranked[:top_n]

    def get_unmapped_checks(self, metrics: list[CheckMetrics]) -> list[CheckMetrics]:
        """Return checks with no factor mapping (impact_score = 0).

        These checks have an empty factors list and therefore cannot
        contribute to scoring.

        Args:
            metrics: List of CheckMetrics from CheckAnalyzer.

        Returns:
            Checks with no factors assigned.
        """
        return [m for m in metrics if not m.factors]

    def get_factor_distribution(self, metrics: list[CheckMetrics]) -> dict[str, int]:
        """Count checks per factor to identify mapping imbalances.

        This reveals the F10=102 vs F8=2 anomaly documented in RESEARCH.md.

        Args:
            metrics: List of CheckMetrics from CheckAnalyzer.

        Returns:
            Dict mapping factor ID to count of checks mapped to it.
        """
        distribution: dict[str, int] = {}
        for m in metrics:
            for factor in m.factors:
                distribution[factor] = distribution.get(factor, 0) + 1
        return distribution

    def _get_weight(self, factors: list[str]) -> float:
        """Get the maximum factor weight for a check's factor list.

        Args:
            factors: List of factor IDs (e.g. ["F1", "F2"]).

        Returns:
            Max weight across all mapped factors, or 0 if none mapped.
        """
        if not factors:
            return 0.0
        weights = [self._factor_weights.get(f, 0.0) for f in factors]
        return max(weights) if weights else 0.0

    @staticmethod
    def _compute_severity(threshold_levels: dict[str, int]) -> float:
        """Compute average severity from threshold level distribution.

        Uses red=3.0, yellow=2.0, clear=0.0 mapping.

        Args:
            threshold_levels: Dict of level -> count (e.g. {"red": 2, "yellow": 1}).

        Returns:
            Average severity score, or 0.0 if no threshold data.
        """
        total_count = 0
        total_severity = 0.0

        for level, count in threshold_levels.items():
            severity = _SEVERITY_MAP.get(level.lower(), 0.0)
            total_severity += severity * count
            total_count += count

        if total_count == 0:
            return 0.0
        return total_severity / total_count


__all__ = ["ImpactRanker", "RankedCheck"]
