"""Temporal change detection engine for the ANALYZE stage.

Identifies quarter-over-quarter and year-over-year changes in key
financial metrics -- the primary trigger for securities class actions.
Simple consecutive-period counting provides 80% of the value without
complex time-series models.

SCAs are triggered by CHANGES (revenue deceleration, margin compression),
not static levels. This engine fills that critical gap.

Provides:
- TemporalAnalyzer: Main class that classifies multi-period trends
  as IMPROVING/STABLE/DETERIORATING/CRITICAL based on consecutive
  adverse or favorable movements.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.temporal import (
    TemporalAnalysisResult,
    TemporalClassification,
    TemporalDataPoint,
    TemporalSignal,
)

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

def load_temporal_config(path: Path | None = None) -> dict:
    """Load temporal thresholds config from JSON file.

    Args:
        path: Override config file path. Defaults to config/temporal_thresholds.json.

    Returns:
        Parsed config dict with thresholds and magnitude cutoffs.
    """
    if path is not None:
        import json
        if path.exists():
            with open(path) as f:
                return json.load(f)
        logger.warning("Temporal config not found at %s, using defaults", path)
        return {}
    return load_config("temporal_thresholds")


class TemporalAnalyzer:
    """Classifies multi-period financial trends.

    Direction-aware consecutive-period counting:
    - CRITICAL: adverse >= consecutive_threshold + 1
    - DETERIORATING: adverse >= consecutive_threshold
    - IMPROVING: favorable >= consecutive_threshold
    - STABLE: default (no sustained directional change)

    Args:
        config: Temporal thresholds config dict. Loaded from
            config/temporal_thresholds.json if not provided.
    """

    def __init__(self, config: dict | None = None) -> None:
        self._config = config if config is not None else load_temporal_config()
        self._consecutive_threshold: int = self._config.get(
            "consecutive_adverse_threshold", 3
        )
        self._critical_threshold: int = self._config.get(
            "critical_consecutive_threshold", 4
        )
        self._magnitude_thresholds: dict = self._config.get(
            "magnitude_thresholds", {}
        )

    def classify_temporal_trend(
        self,
        values: list[float],
        direction: Literal["higher_is_worse", "lower_is_worse"],
        consecutive_threshold: int | None = None,
    ) -> TemporalClassification:
        """Classify a sequence of values into a temporal trend.

        Counts consecutive adverse and favorable period-over-period
        movements. Direction determines what constitutes "adverse":
        - higher_is_worse: increases are adverse (e.g., DSO, debt ratio)
        - lower_is_worse: decreases are adverse (e.g., revenue, margins)

        Args:
            values: Ordered numeric values from oldest to newest.
            direction: Which direction indicates worsening.
            consecutive_threshold: Override default consecutive threshold.

        Returns:
            TemporalClassification enum value.
        """
        if len(values) < 2:
            return TemporalClassification.STABLE

        threshold = consecutive_threshold or self._consecutive_threshold
        critical = threshold + 1

        # Count max consecutive adverse and favorable moves
        max_adverse = 0
        max_favorable = 0
        current_adverse = 0
        current_favorable = 0

        for i in range(1, len(values)):
            change = values[i] - values[i - 1]

            is_adverse = (
                change > 0 if direction == "higher_is_worse" else change < 0
            )
            is_favorable = (
                change < 0 if direction == "higher_is_worse" else change > 0
            )

            if is_adverse:
                current_adverse += 1
                current_favorable = 0
            elif is_favorable:
                current_favorable += 1
                current_adverse = 0
            else:
                # No change -- reset both streaks
                current_adverse = 0
                current_favorable = 0

            max_adverse = max(max_adverse, current_adverse)
            max_favorable = max(max_favorable, current_favorable)

        if max_adverse >= critical:
            return TemporalClassification.CRITICAL
        if max_adverse >= threshold:
            return TemporalClassification.DETERIORATING
        if max_favorable >= threshold:
            return TemporalClassification.IMPROVING
        return TemporalClassification.STABLE

    def _compute_total_change_pct(
        self, first: float, last: float
    ) -> float:
        """Compute total percentage change from first to last value.

        Handles zero division gracefully by returning 0.0.
        """
        if first == 0.0:
            return 0.0
        return (last - first) / abs(first) * 100.0

    def _build_evidence(
        self,
        metric_name: str,
        values: list[float],
        periods: list[str],
        classification: TemporalClassification,
        total_change_pct: float,
        consecutive_adverse: int,
    ) -> str:
        """Build human-readable evidence narrative.

        Example: "Revenue declined 3 consecutive quarters (-15.2% total:
        Q1'24 $100M -> Q4'24 $84.8M)"
        """
        display_name = metric_name.replace("_", " ").title()

        if classification == TemporalClassification.STABLE:
            return f"{display_name} stable across {len(periods)} periods"

        if classification in (
            TemporalClassification.DETERIORATING,
            TemporalClassification.CRITICAL,
        ):
            severity = "critically " if classification == TemporalClassification.CRITICAL else ""
            direction_word = "worsened"
            return (
                f"{display_name} {severity}{direction_word} "
                f"{consecutive_adverse} consecutive periods "
                f"({total_change_pct:+.1f}% total: "
                f"{periods[0]} {values[0]:,.1f} -> "
                f"{periods[-1]} {values[-1]:,.1f})"
            )

        # IMPROVING
        return (
            f"{display_name} improved over {len(periods)} periods "
            f"({total_change_pct:+.1f}% total: "
            f"{periods[0]} {values[0]:,.1f} -> "
            f"{periods[-1]} {values[-1]:,.1f})"
        )

    def _count_max_consecutive_adverse(
        self,
        values: list[float],
        direction: Literal["higher_is_worse", "lower_is_worse"],
    ) -> int:
        """Count maximum consecutive adverse moves in the series."""
        if len(values) < 2:
            return 0

        max_adverse = 0
        current = 0

        for i in range(1, len(values)):
            change = values[i] - values[i - 1]
            is_adverse = (
                change > 0 if direction == "higher_is_worse" else change < 0
            )
            if is_adverse:
                current += 1
                max_adverse = max(max_adverse, current)
            else:
                current = 0

        return max_adverse

    def analyze_metric(
        self,
        metric_name: str,
        values: list[float],
        periods: list[str],
        direction: Literal["higher_is_worse", "lower_is_worse"],
    ) -> TemporalSignal:
        """Analyze a single metric across multiple periods.

        Args:
            metric_name: Identifier for the metric (e.g., "revenue_growth").
            values: Ordered numeric values from oldest to newest.
            periods: Corresponding period labels (e.g., ["FY2022", "FY2023"]).
            direction: Which direction indicates worsening.

        Returns:
            TemporalSignal with classification, evidence, and data points.
        """
        if len(values) < 2 or len(periods) < 2:
            return TemporalSignal(
                metric_name=metric_name,
                classification=TemporalClassification.STABLE,
                evidence=f"Insufficient data for {metric_name} temporal analysis",
            )

        classification = self.classify_temporal_trend(values, direction)
        total_change_pct = self._compute_total_change_pct(values[0], values[-1])
        consecutive_adverse = self._count_max_consecutive_adverse(values, direction)

        data_points = [
            TemporalDataPoint(period=p, value=v, source="financial_statements")
            for p, v in zip(periods, values, strict=False)
        ]

        evidence = self._build_evidence(
            metric_name, values, periods, classification,
            total_change_pct, consecutive_adverse,
        )

        return TemporalSignal(
            metric_name=metric_name,
            periods=data_points,
            classification=classification,
            consecutive_adverse=consecutive_adverse,
            total_change_pct=round(total_change_pct, 2),
            evidence=evidence,
            source_periods=periods,
        )

    def analyze_all_temporal(
        self,
        extracted: ExtractedData,
        company: CompanyProfile | None = None,
    ) -> TemporalAnalysisResult:
        """Run temporal analysis across all available financial metrics.

        Uses temporal_metrics.py to extract multi-period values from
        ExtractedData, then analyzes each metric for temporal trends.

        Args:
            extracted: Structured data from the EXTRACT stage.
            company: Optional company profile for context.

        Returns:
            TemporalAnalysisResult with all signals and summary narrative.
        """
        from do_uw.stages.analyze.temporal_metrics import (
            METRIC_DIRECTIONS,
            extract_temporal_metrics,
        )

        metrics = extract_temporal_metrics(extracted)
        signals: list[TemporalSignal] = []

        for metric_name, data_points in metrics.items():
            if len(data_points) < 2:
                continue

            periods = [dp[0] for dp in data_points]
            values = [dp[1] for dp in data_points]
            direction = METRIC_DIRECTIONS.get(metric_name, "lower_is_worse")

            signal = self.analyze_metric(metric_name, values, periods, direction)
            signals.append(signal)

        summary = self._build_summary(signals, company)

        return TemporalAnalysisResult(
            signals=signals,
            summary=summary,
        )

    def _build_summary(
        self,
        signals: list[TemporalSignal],
        company: CompanyProfile | None = None,
    ) -> str:
        """Build overall temporal assessment summary narrative."""
        if not signals:
            return "No temporal data available for trend analysis."

        deteriorating = [
            s for s in signals
            if s.classification in (
                TemporalClassification.DETERIORATING,
                TemporalClassification.CRITICAL,
            )
        ]
        improving = [
            s for s in signals
            if s.classification == TemporalClassification.IMPROVING
        ]
        stable = [
            s for s in signals
            if s.classification == TemporalClassification.STABLE
        ]

        company_name = "Company"
        if company is not None and company.identity.legal_name is not None:
            company_name = company.identity.legal_name.value

        parts: list[str] = []
        parts.append(
            f"Temporal analysis of {len(signals)} metrics for {company_name}."
        )

        if deteriorating:
            critical = [
                s for s in deteriorating
                if s.classification == TemporalClassification.CRITICAL
            ]
            names = [s.metric_name.replace("_", " ") for s in deteriorating]
            parts.append(
                f"{len(deteriorating)} metric(s) deteriorating: "
                f"{', '.join(names)}."
            )
            if critical:
                crit_names = [s.metric_name.replace("_", " ") for s in critical]
                parts.append(
                    f"CRITICAL trends in: {', '.join(crit_names)}."
                )

        if improving:
            names = [s.metric_name.replace("_", " ") for s in improving]
            parts.append(
                f"{len(improving)} metric(s) improving: {', '.join(names)}."
            )

        if stable:
            parts.append(f"{len(stable)} metric(s) stable.")

        return " ".join(parts)


__all__ = ["TemporalAnalyzer", "load_temporal_config"]
