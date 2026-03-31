"""Conjunction Scan engine -- detects cross-domain co-firing CLEAR signals.

Implements the PatternEngine Protocol. Detects 3+ individually CLEAR
signals co-occurring across 2+ RAP categories (host, agent, environment)
as elevated risk invisible to single-signal evaluation.

Algorithm from pattern_engine_design.yaml:
1. Collect evaluated signals with status and rap_class
2. Identify CLEAR signals with known co-fire correlations
3. Build cross-domain conjunction groups
4. Evaluate conjunction significance
5. Flag elevated conjunctions

Phase 109: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from do_uw.stages.score.pattern_engine import EngineResult

logger = logging.getLogger(__name__)

__all__ = [
    "ConjunctionScanEngine",
    "_load_seed_correlations",
]

# Default seed YAML path
_SEED_PATH = (
    Path(__file__).parent.parent.parent
    / "brain"
    / "framework"
    / "seed_correlations.yaml"
)


def _normalize_pair(a: str, b: str) -> tuple[str, str]:
    """Normalize a signal pair to sorted tuple for consistent lookup."""
    return (min(a, b), max(a, b))


def _load_seed_correlations(
    seed_path: Path | None = None,
) -> dict[tuple[str, str], float]:
    """Load seed correlations from YAML file.

    Returns dict mapping (signal_a, signal_b) -> co_fire_rate.
    Pair keys are normalized (alphabetically sorted) for consistent lookup.
    """
    path = seed_path or _SEED_PATH
    if not path.exists():
        logger.warning("Seed correlations file not found: %s", path)
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)

    if not data or "seed_correlations" not in data:
        return {}

    correlations: dict[tuple[str, str], float] = {}
    for entry in data["seed_correlations"]:
        sig_a = entry.get("signal_a", "")
        sig_b = entry.get("signal_b", "")
        rate = entry.get("co_fire_rate", 0.0)
        if sig_a and sig_b and isinstance(rate, (int, float)):
            pair = _normalize_pair(sig_a, sig_b)
            correlations[pair] = float(rate)

    return correlations


def _load_correlations(
    seed_path: Path | None = None,
) -> dict[tuple[str, str], float]:
    """Load seed correlations from YAML, supplement with DuckDB if available.

    Empirical DuckDB correlations override seed rates when both exist.
    """
    correlations = _load_seed_correlations(seed_path)

    # Try to supplement with empirical data from brain_correlations table
    try:
        from do_uw.brain.brain_schema import connect_brain_db

        conn = connect_brain_db()
        rows = conn.execute(
            "SELECT signal_a, signal_b, co_fire_rate FROM brain_correlations"
            " WHERE above_threshold = TRUE"
        ).fetchall()
        for row in rows:
            pair = _normalize_pair(row[0], row[1])
            correlations[pair] = float(row[2])  # Empirical overrides seed
        conn.close()
    except Exception:
        pass  # Seed data is sufficient; DuckDB may not exist yet

    return correlations


class ConjunctionScanEngine:
    """Detects cross-domain co-firing CLEAR signals as elevated risk.

    Implements the PatternEngine Protocol. Looks for 3+ CLEAR signals
    from 2+ RAP categories that have known co-fire correlations above
    the minimum threshold.
    """

    def __init__(
        self,
        *,
        correlations_override: dict[tuple[str, str], float] | None = None,
        co_fire_rate_minimum: float = 0.15,
        minimum_signals: int = 3,
        confidence_minimum: float = 0.5,
    ) -> None:
        self._co_fire_rate_minimum = co_fire_rate_minimum
        self._minimum_signals = minimum_signals
        self._confidence_minimum = confidence_minimum

        if correlations_override is not None:
            self._correlations = correlations_override
        else:
            self._correlations = _load_correlations()

    @property
    def engine_id(self) -> str:
        return "conjunction_scan"

    @property
    def engine_name(self) -> str:
        return "Conjunction Scan"

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        state: Any | None = None,
    ) -> EngineResult:
        """Run conjunction scan on signal results.

        Steps:
        1. Collect CLEAR signals with rap_class
        2. Find co-firing pairs above threshold
        3. Check cross-domain requirement (2+ RAP categories)
        4. Compute confidence
        5. Return result
        """
        # Check correlations availability
        if not self._correlations:
            return EngineResult(
                engine_id=self.engine_id,
                engine_name=self.engine_name,
                fired=False,
                confidence=0.0,
                headline="Insufficient correlation data",
            )

        # Step 1: Collect evaluated signals
        clear_signals: dict[str, str] = {}  # signal_id -> rap_class
        for sig_id, raw in signal_results.items():
            if not isinstance(raw, dict):
                continue
            status = raw.get("status", "")
            if status == "CLEAR":
                rap_class = raw.get("rap_class", "")
                if rap_class:
                    clear_signals[sig_id] = rap_class

        if not clear_signals:
            return EngineResult(
                engine_id=self.engine_id,
                engine_name=self.engine_name,
                fired=False,
                confidence=0.0,
                headline="No CLEAR signals to scan",
            )

        # Step 2: Find co-firing pairs above threshold
        co_firing_pairs: list[tuple[str, str, float]] = []
        clear_ids = list(clear_signals.keys())

        for i, sig_a in enumerate(clear_ids):
            for sig_b in clear_ids[i + 1 :]:
                pair = _normalize_pair(sig_a, sig_b)
                rate = self._correlations.get(pair)
                if rate is not None and rate > self._co_fire_rate_minimum:
                    co_firing_pairs.append((sig_a, sig_b, rate))

        if not co_firing_pairs:
            return EngineResult(
                engine_id=self.engine_id,
                engine_name=self.engine_name,
                fired=False,
                confidence=0.0,
                headline="No co-firing signal pairs found",
            )

        # Step 3: Build cross-domain conjunction groups
        # Collect all signals participating in co-firing pairs
        participating_signals: set[str] = set()
        for sig_a, sig_b, _ in co_firing_pairs:
            participating_signals.add(sig_a)
            participating_signals.add(sig_b)

        # Check RAP category diversity
        rap_categories = {
            clear_signals[s] for s in participating_signals if s in clear_signals
        }

        if len(rap_categories) < 2:
            return EngineResult(
                engine_id=self.engine_id,
                engine_name=self.engine_name,
                fired=False,
                confidence=0.0,
                headline="Co-firing signals are single-domain only",
                metadata={"rap_categories": list(rap_categories)},
            )

        # Step 4: Evaluate conjunction significance
        # Only count signals in cross-domain pairs
        cross_domain_signals: set[str] = set()
        cross_domain_rates: list[float] = []
        for sig_a, sig_b, rate in co_firing_pairs:
            rap_a = clear_signals.get(sig_a, "")
            rap_b = clear_signals.get(sig_b, "")
            if rap_a != rap_b:
                cross_domain_signals.add(sig_a)
                cross_domain_signals.add(sig_b)
                cross_domain_rates.append(rate)

        count = len(cross_domain_signals)
        if count < self._minimum_signals:
            return EngineResult(
                engine_id=self.engine_id,
                engine_name=self.engine_name,
                fired=False,
                confidence=0.0,
                headline=f"Only {count} cross-domain co-firing signals (need {self._minimum_signals})",
            )

        # Confidence = mean(co_fire_rate) * count / expected_count
        # For practical purposes: expected_count is the minimum threshold
        mean_rate = sum(cross_domain_rates) / len(cross_domain_rates)
        confidence = min(1.0, mean_rate * count / self._minimum_signals)

        # Step 5: Flag if above confidence threshold
        fired = confidence > self._confidence_minimum and count >= self._minimum_signals

        # Build findings
        findings: list[dict[str, Any]] = []
        for sig_id in sorted(cross_domain_signals):
            findings.append(
                {
                    "signal_id": sig_id,
                    "rap_class": clear_signals.get(sig_id, ""),
                    "status": "CLEAR",
                }
            )

        # Build headline
        if fired:
            headline = (
                f"{count} CLEAR signals co-firing across "
                f"{len(rap_categories)} RAP categories "
                f"(confidence: {confidence:.2f})"
            )
        else:
            headline = (
                f"Conjunction below threshold "
                f"(confidence: {confidence:.2f}, need > {self._confidence_minimum})"
            )

        return EngineResult(
            engine_id=self.engine_id,
            engine_name=self.engine_name,
            fired=fired,
            confidence=confidence,
            headline=headline,
            findings=findings,
            metadata={
                "rap_categories": sorted(rap_categories),
                "cross_domain_signal_count": count,
                "co_firing_pairs": len(co_firing_pairs),
                "cross_domain_pairs": len(cross_domain_rates),
                "mean_co_fire_rate": round(mean_rate, 4),
            },
        )
