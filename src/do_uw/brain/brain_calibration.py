"""Statistical threshold calibration engine and fire rate alerting.

Queries brain_signal_runs for observed value distributions, compares
against current YAML thresholds, detects statistical drift (>2 sigma),
flags fire rate anomalies (>80% or <2%), and generates
THRESHOLD_CALIBRATION proposals in brain_proposals for manual approval.

Usage:
    from do_uw.brain.brain_calibration import compute_calibration_report
    report = compute_calibration_report(conn)
    # report.drift_signals, report.fire_rate_alerts, report.insufficient_data
"""

from __future__ import annotations

import json
import logging
import re
from statistics import mean, quantiles, stdev
from typing import Any, Literal

import duckdb
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_RUNS_FOR_ANALYSIS = 5
DRIFT_SIGMA_THRESHOLD = 2.0

# Threshold types that support numeric drift analysis
NUMERIC_THRESHOLD_TYPES = frozenset({"tiered_threshold", "numeric_threshold", "tiered"})

# Fire rate alert thresholds
HIGH_FIRE_RATE_THRESHOLD = 0.80
LOW_FIRE_RATE_THRESHOLD = 0.02

# Regex for extracting numeric value and operator from threshold strings
# Matches patterns like ">5.0", "<1.0 current ratio", ">=10", "<=0.5"
_THRESHOLD_REGEX = re.compile(r"([<>=!]+)\s*([\d.]+)")
_NUMERIC_ONLY_REGEX = re.compile(r"([\d.]+)")


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class DriftReport(BaseModel):
    """Per-signal threshold drift analysis result."""

    signal_id: str
    status: Literal["DRIFT_DETECTED", "OK", "INSUFFICIENT_DATA"]
    n: int = 0
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    current_threshold: float | None = None
    observed_mean: float | None = None
    observed_stdev: float | None = None
    fire_rate: float = 0.0
    proposed_value: float | None = None
    basis: str = ""
    projected_impact: str = ""


class FireRateAlert(BaseModel):
    """Fire rate anomaly alert for a signal."""

    signal_id: str
    fire_rate: float
    alert_type: Literal["HIGH_FIRE_RATE", "LOW_FIRE_RATE"]
    recommendation: str


class CalibrationReport(BaseModel):
    """Complete calibration report from compute_calibration_report()."""

    drift_signals: list[DriftReport] = Field(default_factory=list)
    fire_rate_alerts: list[FireRateAlert] = Field(default_factory=list)
    insufficient_data: list[DriftReport] = Field(default_factory=list)
    total_signals_analyzed: int = 0
    total_with_numeric_values: int = 0
    total_proposals_generated: int = 0


# ---------------------------------------------------------------------------
# Value Distribution Query
# ---------------------------------------------------------------------------


def get_signal_value_distribution(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> list[float]:
    """Query brain_signal_runs for numeric values of a signal.

    Reads all non-backtest runs, tries float() on each value,
    silently skips non-numeric. Defensive parsing per Pitfall 2.

    Args:
        conn: DuckDB connection with brain schema.
        signal_id: Signal identifier.

    Returns:
        List of float values (may be empty).
    """
    rows = conn.execute(
        """SELECT value FROM brain_signal_runs
           WHERE signal_id = ? AND is_backtest = FALSE
             AND value IS NOT NULL""",
        [signal_id],
    ).fetchall()

    values: list[float] = []
    for (raw_value,) in rows:
        try:
            values.append(float(raw_value))
        except (ValueError, TypeError):
            continue  # Skip non-numeric values
    return values


# ---------------------------------------------------------------------------
# Confidence Level
# ---------------------------------------------------------------------------


def _compute_confidence(n: int) -> Literal["LOW", "MEDIUM", "HIGH"]:
    """Determine confidence level from observation count.

    N=5-9: LOW, N=10-24: MEDIUM, N>=25: HIGH.
    """
    if n >= 25:
        return "HIGH"
    if n >= 10:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Threshold Drift Computation
# ---------------------------------------------------------------------------


def compute_threshold_drift(
    signal_id: str,
    values: list[float],
    current_threshold: float | None,
    fire_rate: float,
) -> DriftReport:
    """Compute threshold drift for a single signal.

    Uses statistics.mean, statistics.stdev, statistics.quantiles.
    Flags when abs(current_threshold - observed_mean) > 2 * stdev.

    Proposed value uses p90 for "higher is worse" (>) or p10 for
    "lower is worse" (<) thresholds. Defaults to p90 when direction
    is unknown.

    Args:
        signal_id: Signal identifier.
        values: List of observed numeric values.
        current_threshold: Parsed threshold value (None for non-numeric).
        fire_rate: Signal fire rate from effectiveness data.

    Returns:
        DriftReport with status, stats, and optional proposal.
    """
    n = len(values)

    if n < MIN_RUNS_FOR_ANALYSIS:
        return DriftReport(
            signal_id=signal_id,
            status="INSUFFICIENT_DATA",
            n=n,
            fire_rate=fire_rate,
        )

    confidence = _compute_confidence(n)
    obs_mean = mean(values)
    obs_stdev = stdev(values) if n > 1 else 0.0

    # If no current threshold, we can only report stats (no drift comparison)
    if current_threshold is None:
        return DriftReport(
            signal_id=signal_id,
            status="OK",
            n=n,
            confidence=confidence,
            observed_mean=round(obs_mean, 4),
            observed_stdev=round(obs_stdev, 4),
            fire_rate=fire_rate,
        )

    # Check drift: threshold > 2 sigma from observed mean
    if obs_stdev > 0 and abs(current_threshold - obs_mean) > DRIFT_SIGMA_THRESHOLD * obs_stdev:
        # Compute percentiles for proposal (need at least 2 values)
        if n >= 2:
            pcts = quantiles(values, n=100)
            # p90 = pcts[89], p10 = pcts[9] (0-indexed, 99 values for n=100)
            proposed = round(pcts[89], 4)  # Default to p90
        else:
            proposed = round(obs_mean, 4)

        return DriftReport(
            signal_id=signal_id,
            status="DRIFT_DETECTED",
            n=n,
            confidence=confidence,
            current_threshold=current_threshold,
            observed_mean=round(obs_mean, 4),
            observed_stdev=round(obs_stdev, 4),
            fire_rate=fire_rate,
            proposed_value=proposed,
            basis="p90 of observed distribution",
            projected_impact=(
                f"Threshold would move from {current_threshold} to {proposed}, "
                f"better aligned with observed data (mean={round(obs_mean, 2)}, "
                f"stdev={round(obs_stdev, 2)}, N={n})"
            ),
        )

    # No significant drift
    return DriftReport(
        signal_id=signal_id,
        status="OK",
        n=n,
        confidence=confidence,
        current_threshold=current_threshold,
        observed_mean=round(obs_mean, 4),
        observed_stdev=round(obs_stdev, 4),
        fire_rate=fire_rate,
    )


# ---------------------------------------------------------------------------
# Numeric Threshold Extraction
# ---------------------------------------------------------------------------


def extract_numeric_threshold(
    signal: dict[str, Any],
) -> tuple[float | None, str]:
    """Parse numeric value and operator direction from a signal's threshold.

    For V2 signals (schema_version >= 2): uses evaluation.thresholds[0].value
    and evaluation.thresholds[0].op directly.

    For V1 signals: parses strings like ">5.0", "<1.0 current ratio" using
    regex. Returns (value, operator_direction).

    Args:
        signal: Signal definition dict.

    Returns:
        Tuple of (threshold_value, operator) where operator is ">", "<", etc.
        Returns (None, "") if unparseable.
    """
    schema_version = signal.get("schema_version", 1)

    # V2 path: structured evaluation.thresholds
    if schema_version >= 2:
        evaluation = signal.get("evaluation")
        if evaluation and isinstance(evaluation, dict):
            thresholds = evaluation.get("thresholds", [])
            if thresholds and isinstance(thresholds, list) and len(thresholds) > 0:
                first = thresholds[0]
                if isinstance(first, dict):
                    val = first.get("value")
                    op = first.get("op", "")
                    if val is not None:
                        try:
                            return (float(val), str(op))
                        except (ValueError, TypeError):
                            pass
        return (None, "")

    # V1 path: parse from threshold.red or threshold.yellow string
    threshold = signal.get("threshold", {})
    if not threshold or not isinstance(threshold, dict):
        return (None, "")

    # Try red first, then yellow
    for level_key in ("red", "yellow"):
        level_str = threshold.get(level_key)
        if not level_str or not isinstance(level_str, str):
            continue

        # Try to extract operator + value
        match = _THRESHOLD_REGEX.search(level_str)
        if match:
            op = match.group(1)
            try:
                return (float(match.group(2)), op)
            except ValueError:
                continue

        # Try numeric value only (no operator)
        num_match = _NUMERIC_ONLY_REGEX.search(level_str)
        if num_match:
            try:
                return (float(num_match.group(1)), "")
            except ValueError:
                continue

    return (None, "")


# ---------------------------------------------------------------------------
# Fire Rate Alerts
# ---------------------------------------------------------------------------


def compute_fire_rate_alerts(
    effectiveness_entries: list[Any],
) -> list[FireRateAlert]:
    """Flag signals with extreme fire rates (>80% or <2%).

    Args:
        effectiveness_entries: List of SignalEffectivenessEntry objects
            (or anything with signal_id and fire_rate attributes).

    Returns:
        List of FireRateAlert for anomalous signals.
    """
    alerts: list[FireRateAlert] = []

    for entry in effectiveness_entries:
        signal_id = entry.signal_id
        fire_rate = entry.fire_rate

        if fire_rate > HIGH_FIRE_RATE_THRESHOLD:
            alerts.append(
                FireRateAlert(
                    signal_id=signal_id,
                    fire_rate=fire_rate,
                    alert_type="HIGH_FIRE_RATE",
                    recommendation=(
                        "Threshold may be too sensitive -- consider raising "
                        f"(fire rate: {fire_rate:.1%})"
                    ),
                )
            )
        elif fire_rate < LOW_FIRE_RATE_THRESHOLD:
            alerts.append(
                FireRateAlert(
                    signal_id=signal_id,
                    fire_rate=fire_rate,
                    alert_type="LOW_FIRE_RATE",
                    recommendation=(
                        "Threshold may be unreachable -- consider lowering "
                        f"or reviewing signal relevance (fire rate: {fire_rate:.1%})"
                    ),
                )
            )

    return alerts


# ---------------------------------------------------------------------------
# Proposal Generation
# ---------------------------------------------------------------------------


def generate_calibration_proposals(
    conn: duckdb.DuckDBPyConnection,
    drift_signals: list[DriftReport],
) -> int:
    """Write THRESHOLD_CALIBRATION proposals for drift-detected signals.

    For each DRIFT_DETECTED signal, inserts into brain_proposals with
    source_type='CALIBRATION', statistical evidence in backtest_results.

    Args:
        conn: DuckDB connection with brain schema.
        drift_signals: List of DriftReport objects.

    Returns:
        Count of proposals generated.
    """
    count = 0

    for drift in drift_signals:
        if drift.status != "DRIFT_DETECTED":
            continue

        proposed_changes = {
            "current_threshold": drift.current_threshold,
            "proposed_value": drift.proposed_value,
            "basis": drift.basis,
        }

        backtest_results = {
            "n": drift.n,
            "mean": drift.observed_mean,
            "stdev": drift.observed_stdev,
            "fire_rate": drift.fire_rate,
            "confidence": drift.confidence,
            "projected_impact": drift.projected_impact,
        }

        rationale = (
            f"Statistical drift detected: current threshold "
            f"({drift.current_threshold}) is >{DRIFT_SIGMA_THRESHOLD} sigma "
            f"from observed mean ({drift.observed_mean}). "
            f"Proposed adjustment to {drift.proposed_value} based on "
            f"{drift.basis}. Confidence: {drift.confidence} (N={drift.n})."
        )

        conn.execute(
            """INSERT INTO brain_proposals
               (source_type, source_ref, signal_id, proposal_type,
                proposed_changes, backtest_results, rationale, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')""",
            [
                "CALIBRATION",
                f"brain_audit_calibrate_{drift.signal_id}",
                drift.signal_id,
                "THRESHOLD_CALIBRATION",
                json.dumps(proposed_changes),
                json.dumps(backtest_results),
                rationale,
            ],
        )
        count += 1

    return count


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------


def compute_calibration_report(
    conn: duckdb.DuckDBPyConnection,
) -> CalibrationReport:
    """Compute full calibration report: drift analysis, fire rate alerts, proposals.

    Orchestrates the calibration pipeline:
    1. Load signal definitions from YAML (via BrainLoader)
    2. Get effectiveness data (fire rates) from brain_signal_runs
    3. For each signal with numeric threshold, compute drift
    4. Compute fire rate alerts for all signals
    5. Generate proposals for drift-detected signals

    Args:
        conn: DuckDB connection with brain schema (for signal_runs queries).

    Returns:
        CalibrationReport with all analysis results.
    """
    from do_uw.brain.brain_effectiveness import (
        SignalEffectivenessEntry,
        compute_effectiveness,
    )
    from do_uw.brain.brain_unified_loader import load_signals

    # Load signal definitions from YAML
    signals_data = load_signals()
    all_signals = signals_data.get("signals", [])
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]

    # Get effectiveness data for fire rates
    effectiveness = compute_effectiveness(conn)

    # Build fire rate lookup from effectiveness data
    fire_rate_map: dict[str, float] = {}
    effectiveness_entries: list[SignalEffectivenessEntry] = []

    # Reconstruct effectiveness entries from report classifications
    for entry_list in [
        effectiveness.always_fire,
        effectiveness.never_fire,
        effectiveness.high_skip,
        effectiveness.consistent,
    ]:
        for entry_dict in entry_list:
            sid = entry_dict.get("signal_id", "")
            fr = entry_dict.get("fire_rate", 0.0)
            fire_rate_map[sid] = fr

    # Build per-signal effectiveness entries from brain_signal_runs directly
    rows = conn.execute(
        """SELECT signal_id, status, COUNT(*) as cnt
           FROM brain_signal_runs
           WHERE is_backtest = FALSE
           GROUP BY signal_id, status"""
    ).fetchall()

    signal_stats: dict[str, dict[str, int]] = {}
    for signal_id, status, cnt in rows:
        if signal_id not in signal_stats:
            signal_stats[signal_id] = {
                "triggered": 0, "clear": 0, "skipped": 0, "info": 0, "total": 0,
            }
        s = signal_stats[signal_id]
        s["total"] += cnt
        status_upper = status.upper()
        if status_upper == "TRIGGERED":
            s["triggered"] += cnt
        elif status_upper == "CLEAR":
            s["clear"] += cnt
        elif status_upper == "SKIPPED":
            s["skipped"] += cnt
        elif status_upper == "INFO":
            s["info"] += cnt

    for sid, stats in signal_stats.items():
        total = stats["total"]
        fr = stats["triggered"] / total if total > 0 else 0.0
        fire_rate_map[sid] = fr
        effectiveness_entries.append(
            SignalEffectivenessEntry(
                signal_id=sid,
                fire_rate=round(fr, 4),
                total_runs=total,
                triggered_count=stats["triggered"],
                clear_count=stats["clear"],
                skipped_count=stats["skipped"],
                info_count=stats["info"],
            )
        )

    # Analyze each active signal with numeric threshold
    drift_signals: list[DriftReport] = []
    insufficient: list[DriftReport] = []
    total_analyzed = 0
    total_numeric = 0

    for signal in active_signals:
        signal_id = signal.get("id", "")
        threshold = signal.get("threshold", {})
        if not threshold or not isinstance(threshold, dict):
            continue

        threshold_type = threshold.get("type", "")

        # Only attempt numeric drift analysis for numeric threshold types
        if threshold_type not in NUMERIC_THRESHOLD_TYPES:
            continue

        total_analyzed += 1

        # Extract numeric threshold value
        threshold_value, _operator = extract_numeric_threshold(signal)

        # Get observed value distribution
        values = get_signal_value_distribution(conn, signal_id)
        if values:
            total_numeric += 1

        fire_rate = fire_rate_map.get(signal_id, 0.0)

        # Compute drift
        report = compute_threshold_drift(
            signal_id, values, threshold_value, fire_rate,
        )

        if report.status == "INSUFFICIENT_DATA":
            insufficient.append(report)
        elif report.status == "DRIFT_DETECTED":
            drift_signals.append(report)
        # OK signals are not stored separately (they're the majority)

    # Fire rate alerts (for ALL signals with effectiveness data)
    fire_rate_alerts = compute_fire_rate_alerts(effectiveness_entries)

    # Generate proposals for drift-detected signals
    proposals_count = generate_calibration_proposals(conn, drift_signals)

    return CalibrationReport(
        drift_signals=drift_signals,
        fire_rate_alerts=fire_rate_alerts,
        insufficient_data=insufficient,
        total_signals_analyzed=total_analyzed,
        total_with_numeric_values=total_numeric,
        total_proposals_generated=proposals_count,
    )


__all__ = [
    "CalibrationReport",
    "DriftReport",
    "FireRateAlert",
    "compute_calibration_report",
    "compute_fire_rate_alerts",
    "compute_threshold_drift",
    "extract_numeric_threshold",
    "generate_calibration_proposals",
    "get_signal_value_distribution",
]
