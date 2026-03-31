"""Adverse event scoring (SECT4-09).

Computes a composite adverse event score by aggregating all SECT4
extraction results and weighting them by severity. This extractor
MUST run after all other SECT4 extractors have populated the market
signals on state.extracted.market.

Severity weights are loaded from config/adverse_events.json so
underwriters can tune them without code changes.

Usage:
    score, report = compute_adverse_event_score(state)
    state.extracted.market.adverse_events = score
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence
from do_uw.models.market_events import (
    AdverseEventScore,
    EarningsResult,
    SeverityLevel,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import sourced_float
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Source attribution.
_SOURCE = "SECT4 composite analysis"

# Expected fields for extraction report.
EXPECTED_FIELDS: list[str] = [
    "total_score",
    "event_count",
    "severity_breakdown",
]

# Severity classification thresholds.
_SEVERITY_THRESHOLDS: list[tuple[float, str]] = [
    (3.0, SeverityLevel.CRITICAL),
    (2.0, SeverityLevel.HIGH),
    (1.0, SeverityLevel.MEDIUM),
    (0.0, SeverityLevel.LOW),
]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_severity_weights(
    path: Path | None = None,
) -> dict[str, float]:
    """Load severity weights from config JSON.

    Args:
        path: Optional override path to adverse_events.json.

    Returns:
        Dict of event_type -> severity_weight.
    """
    if path is not None:
        import json
        if not path.exists():
            logger.warning(
                "Adverse events config not found: %s", path
            )
            return {}
        with path.open(encoding="utf-8") as f:
            data_raw: dict[str, Any] = json.load(f)
        raw_weights = data_raw.get("severity_weights", {})
        if not isinstance(raw_weights, dict):
            logger.warning("severity_weights is not a dict in config")
            return {}
        return cast(dict[str, float], raw_weights)

    data = load_config("adverse_events")
    raw_weights = data.get("severity_weights", {})
    if not isinstance(raw_weights, dict):
        logger.warning("severity_weights is not a dict in config")
        return {}

    return cast(dict[str, float], raw_weights)


# ---------------------------------------------------------------------------
# Event counting from market signals
# ---------------------------------------------------------------------------


def _classify_severity(weight: float) -> str:
    """Map a severity weight to a severity level string."""
    for threshold, level in _SEVERITY_THRESHOLDS:
        if weight >= threshold:
            return level
    return SeverityLevel.LOW


def _count_stock_drop_events(
    state: AnalysisState,
    weights: dict[str, float],
) -> list[tuple[str, int, float]]:
    """Count stock drop events and compute weighted scores.

    Returns list of (event_type, count, weighted_score).
    """
    events: list[tuple[str, int, float]] = []
    market = _get_market(state)
    if market is None:
        return events

    drops = market.stock_drops

    # Single-day drops by magnitude.
    for drop in drops.single_day_drops:
        drop_pct = abs(drop.drop_pct.value) if drop.drop_pct else 0.0
        if drop_pct >= 20.0:
            events.append((
                "single_day_drop_20pct",
                1,
                weights.get("single_day_drop_20pct", 4.0),
            ))
        elif drop_pct >= 10.0:
            events.append((
                "single_day_drop_10pct",
                1,
                weights.get("single_day_drop_10pct", 2.0),
            ))
        elif drop_pct >= 5.0:
            events.append((
                "single_day_drop_5pct",
                1,
                weights.get("single_day_drop_5pct", 1.0),
            ))

    # Multi-day declines.
    for drop in drops.multi_day_drops:
        drop_pct = abs(drop.drop_pct.value) if drop.drop_pct else 0.0
        if drop_pct >= 25.0:
            events.append((
                "multi_day_decline_25pct",
                1,
                weights.get("multi_day_decline_25pct", 3.0),
            ))
        elif drop_pct >= 10.0:
            events.append((
                "multi_day_decline_10pct",
                1,
                weights.get("multi_day_decline_10pct", 1.5),
            ))

    return events


def _count_insider_events(
    state: AnalysisState,
    weights: dict[str, float],
) -> list[tuple[str, int, float]]:
    """Count insider trading adverse events."""
    events: list[tuple[str, int, float]] = []
    market = _get_market(state)
    if market is None:
        return events

    insider = market.insider_analysis

    # Cluster selling events.
    cluster_count = len(insider.cluster_events)
    if cluster_count > 0:
        events.append((
            "insider_cluster_selling",
            cluster_count,
            weights.get("insider_cluster_selling", 2.0) * cluster_count,
        ))

    return events


def _count_earnings_events(
    state: AnalysisState,
    weights: dict[str, float],
) -> list[tuple[str, int, float]]:
    """Count earnings-related adverse events."""
    events: list[tuple[str, int, float]] = []
    market = _get_market(state)
    if market is None:
        return events

    guidance = market.earnings_guidance

    # Individual misses.
    miss_count = sum(
        1
        for q in guidance.quarters
        if q.result == EarningsResult.MISS
    )
    if miss_count > 0:
        events.append((
            "earnings_miss",
            miss_count,
            weights.get("earnings_miss", 1.0) * miss_count,
        ))

    # Consecutive misses bonus (3+).
    if guidance.consecutive_miss_count >= 3:
        events.append((
            "consecutive_earnings_misses_3plus",
            1,
            weights.get("consecutive_earnings_misses_3plus", 3.0),
        ))

    # Guidance withdrawals.
    if guidance.guidance_withdrawals > 0:
        events.append((
            "guidance_withdrawal",
            guidance.guidance_withdrawals,
            weights.get("guidance_withdrawal", 2.0)
            * guidance.guidance_withdrawals,
        ))

    return events


def _count_analyst_events(
    state: AnalysisState,
    weights: dict[str, float],
) -> list[tuple[str, int, float]]:
    """Count analyst-related adverse events."""
    events: list[tuple[str, int, float]] = []
    market = _get_market(state)
    if market is None:
        return events

    analyst = market.analyst
    if analyst.recent_downgrades > 0:
        events.append((
            "analyst_downgrade",
            analyst.recent_downgrades,
            weights.get("analyst_downgrade", 0.5)
            * analyst.recent_downgrades,
        ))

    return events


def _count_capital_markets_events(
    state: AnalysisState,
    weights: dict[str, float],
) -> list[tuple[str, int, float]]:
    """Count capital markets adverse events."""
    events: list[tuple[str, int, float]] = []
    market = _get_market(state)
    if market is None:
        return events

    cm = market.capital_markets
    if cm.active_section_11_windows > 0:
        events.append((
            "recent_offering_section_11",
            cm.active_section_11_windows,
            weights.get("recent_offering_section_11", 2.0)
            * cm.active_section_11_windows,
        ))

    return events


def _get_market(state: AnalysisState) -> Any:
    """Get market signals from state, or None."""
    if state.extracted is None:
        return None
    return state.extracted.market


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------


def compute_adverse_event_score(
    state: AnalysisState,
    config_path: Path | None = None,
) -> tuple[AdverseEventScore, ExtractionReport]:
    """Compute composite adverse event score (SECT4-09).

    Aggregates events from all SECT4 extractors, weights them by
    severity from config, and produces a single composite score.

    MUST run after all other SECT4 extractors.

    Args:
        state: Analysis state with SECT4 extractions complete.
        config_path: Optional override for config file path.

    Returns:
        Tuple of (AdverseEventScore, ExtractionReport).
    """
    weights = load_severity_weights(config_path)
    found_fields: list[str] = []
    warnings: list[str] = []

    score = AdverseEventScore()

    if _get_market(state) is None:
        warnings.append("No market signals available for scoring")
        report = create_report(
            extractor_name="adverse_events",
            expected=EXPECTED_FIELDS,
            found=found_fields,
            source_filing=_SOURCE,
            warnings=warnings,
        )
        log_report(report)
        return score, report

    # Collect all events.
    all_events: list[tuple[str, int, float]] = []
    all_events.extend(_count_stock_drop_events(state, weights))
    all_events.extend(_count_insider_events(state, weights))
    all_events.extend(_count_earnings_events(state, weights))
    all_events.extend(_count_analyst_events(state, weights))
    all_events.extend(_count_capital_markets_events(state, weights))

    # Aggregate.
    total_weighted = sum(w for _, _, w in all_events)
    total_count = sum(c for _, c, _ in all_events)

    # Build severity breakdown.
    breakdown: dict[str, int] = {}
    for _event_type, count, weighted in all_events:
        # Classify by per-unit weight.
        per_unit = weighted / count if count > 0 else 0.0
        severity = _classify_severity(per_unit)
        breakdown[severity] = breakdown.get(severity, 0) + count

    score.total_score = sourced_float(
        round(total_weighted, 2), _SOURCE, Confidence.LOW
    )
    found_fields.append("total_score")

    score.event_count = total_count
    found_fields.append("event_count")

    score.severity_breakdown = breakdown
    found_fields.append("severity_breakdown")

    report = create_report(
        extractor_name="adverse_events",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=_SOURCE,
        warnings=warnings,
    )
    log_report(report)
    return score, report
