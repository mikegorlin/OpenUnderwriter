"""Brain health metrics: unified system health computation.

Signal definitions are read from YAML (source of truth).
Historical run data (fire rates, run history) from DuckDB (only place it lives).
Feedback queue from DuckDB. Data freshness from DuckDB.

YAML = signal definitions (source of truth).
DuckDB = runtime/historical data (run results, effectiveness, feedback).
"""

from __future__ import annotations

from typing import Any

import duckdb
from pydantic import BaseModel, Field

from do_uw.brain.brain_effectiveness import compute_effectiveness

# ---------------------------------------------------------------------------
# Fire rate distribution buckets
# ---------------------------------------------------------------------------

_FIRE_RATE_BUCKETS: list[tuple[str, float, float]] = [
    ("0%", 0.0, 0.0),
    ("1-10%", 0.0001, 0.10),
    ("10-30%", 0.1001, 0.30),
    ("30-50%", 0.3001, 0.50),
    ("50-80%", 0.5001, 0.80),
    ("80-100%", 0.8001, 1.0),
]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BrainHealthReport(BaseModel):
    """Unified brain system health report."""

    total_active_signals: int = 0
    total_all_signals: int = 0  # including INACTIVE, DEPRECATED
    facet_coverage_pct: float = 0.0  # signals in facets / total active * 100
    signals_in_facets: int = 0
    signals_not_in_facets: int = 0

    # Fire rate distribution (bucket -> count)
    fire_rate_distribution: dict[str, int] = Field(default_factory=dict)

    # Top problematic signals
    top_always_fire: list[dict[str, Any]] = Field(default_factory=list)
    top_never_fire: list[dict[str, Any]] = Field(default_factory=list)
    top_high_skip: list[dict[str, Any]] = Field(default_factory=list)

    # System metadata
    data_freshness: str = "N/A"  # last_build_at from brain_meta
    total_pipeline_runs: int = 0
    total_backtest_runs: int = 0
    feedback_queue_size: int = 0

    # Run history
    tickers_analyzed: list[str] = Field(default_factory=list)
    runs_by_ticker: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------


def _bucket_fire_rate(rate: float) -> str:
    """Assign a fire rate to a distribution bucket."""
    if rate == 0.0:
        return "0%"
    for label, low, high in _FIRE_RATE_BUCKETS:
        if label == "0%":
            continue
        if low <= rate <= high:
            return label
    return "80-100%"


def compute_brain_health(conn: duckdb.DuckDBPyConnection) -> BrainHealthReport:
    """Compute unified brain health metrics from existing DuckDB data.

    Reads from brain_signals_active, brain_signal_runs, brain_effectiveness,
    brain_feedback, and brain_meta. Does not create new tables.

    Args:
        conn: DuckDB connection with brain schema.

    Returns:
        BrainHealthReport with all health metrics.
    """
    # Load signal definitions from YAML (source of truth)
    from do_uw.brain.brain_unified_loader import load_signals as _load_yaml_signals
    signals_data = _load_yaml_signals()
    all_signals = signals_data.get("signals", [])

    # Partition by lifecycle state
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]
    total_active = len(active_signals)
    total_all = len(all_signals)
    active_ids = {s["id"] for s in active_signals}

    # Facet/group coverage -- signals with valid group assignment
    signals_in_facets = sum(1 for s in active_signals if s.get("group", ""))
    signals_not_in_facets = max(0, total_active - signals_in_facets)
    facet_coverage_pct = (
        round(signals_in_facets / total_active * 100, 1)
        if total_active > 0
        else 0.0
    )

    # Fire rate distribution from effectiveness report
    eff_report = compute_effectiveness(conn)

    # Build fire rate distribution by bucketing per-signal fire rates
    # We need per-signal fire rates from brain_signal_runs
    distribution: dict[str, int] = {label: 0 for label, _, _ in _FIRE_RATE_BUCKETS}

    # Get per-signal fire rates from brain_signal_runs directly
    signal_stats = conn.execute(
        "SELECT signal_id, "
        "SUM(CASE WHEN status = 'TRIGGERED' THEN 1 ELSE 0 END) as triggered, "
        "COUNT(*) as total "
        "FROM brain_signal_runs "
        "WHERE is_backtest = FALSE "
        "GROUP BY signal_id"
    ).fetchall()

    for _signal_id, triggered, total in signal_stats:
        rate = triggered / total if total > 0 else 0.0
        bucket = _bucket_fire_rate(rate)
        distribution[bucket] = distribution.get(bucket, 0) + 1

    # Top problematic signals (first 10 from each category)
    top_always_fire = eff_report.always_fire[:10]
    top_never_fire = eff_report.never_fire[:10]
    top_high_skip = eff_report.high_skip[:10]

    # Data freshness from brain_meta
    freshness_row = conn.execute(
        "SELECT meta_value FROM brain_meta WHERE meta_key = 'last_build_at'"
    ).fetchone()
    data_freshness = freshness_row[0] if freshness_row else "N/A"

    # Pipeline and backtest run counts
    pipeline_runs_row = conn.execute(
        "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
        "WHERE is_backtest = FALSE"
    ).fetchone()
    total_pipeline_runs = pipeline_runs_row[0] if pipeline_runs_row else 0

    backtest_runs_row = conn.execute(
        "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
        "WHERE is_backtest = TRUE"
    ).fetchone()
    total_backtest_runs = backtest_runs_row[0] if backtest_runs_row else 0

    # Feedback queue
    fb_row = conn.execute(
        "SELECT COUNT(*) FROM brain_feedback WHERE status = 'PENDING'"
    ).fetchone()
    feedback_queue_size = fb_row[0] if fb_row else 0

    # Tickers analyzed
    ticker_rows = conn.execute(
        "SELECT DISTINCT ticker FROM brain_signal_runs "
        "WHERE is_backtest = FALSE ORDER BY ticker"
    ).fetchall()
    tickers_analyzed = [r[0] for r in ticker_rows]

    # Runs by ticker
    runs_by_ticker_rows = conn.execute(
        "SELECT ticker, COUNT(DISTINCT run_id) "
        "FROM brain_signal_runs "
        "WHERE is_backtest = FALSE "
        "GROUP BY ticker ORDER BY ticker"
    ).fetchall()
    runs_by_ticker = {r[0]: r[1] for r in runs_by_ticker_rows}

    return BrainHealthReport(
        total_active_signals=total_active,
        total_all_signals=total_all,
        facet_coverage_pct=facet_coverage_pct,
        signals_in_facets=signals_in_facets,
        signals_not_in_facets=signals_not_in_facets,
        fire_rate_distribution=distribution,
        top_always_fire=top_always_fire,
        top_never_fire=top_never_fire,
        top_high_skip=top_high_skip,
        data_freshness=data_freshness,
        total_pipeline_runs=total_pipeline_runs,
        total_backtest_runs=total_backtest_runs,
        feedback_queue_size=feedback_queue_size,
        tickers_analyzed=tickers_analyzed,
        runs_by_ticker=runs_by_ticker,
    )


__all__ = [
    "BrainHealthReport",
    "compute_brain_health",
]
