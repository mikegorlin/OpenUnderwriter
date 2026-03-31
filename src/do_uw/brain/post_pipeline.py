"""Post-pipeline learning hook: auto-propose calibration and lifecycle changes.

After each pipeline run, generates proposals for threshold drift, fire-rate
anomalies, and lifecycle transitions. Proposals are written to brain_proposals
for CLI review -- never auto-applied.

Usage:
    from do_uw.brain.post_pipeline import run_post_pipeline_learning
    result = run_post_pipeline_learning("AAPL")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_post_pipeline_learning(ticker: str) -> dict[str, Any]:
    """Generate calibration and lifecycle proposals after pipeline completion.

    Connects to the brain DuckDB, runs calibration (threshold drift + fire-rate
    alerts) and lifecycle analysis, logs results. Proposals are stored in
    brain_proposals table for manual review via ``brain apply-proposal``.

    This function NEVER raises -- all exceptions are caught and logged so that
    learning-loop failures cannot crash the pipeline.

    Args:
        ticker: Company ticker that was just analyzed.

    Returns:
        Dict with counts: drift_proposals, fire_rate_alerts, lifecycle_proposals,
        total_proposals. Empty dict on failure.
    """
    conn = None
    try:
        from do_uw.brain.brain_calibration import compute_calibration_report
        from do_uw.brain.brain_lifecycle_v2 import compute_lifecycle_proposals
        from do_uw.brain.brain_schema import get_brain_db_path

        import duckdb

        db_path = get_brain_db_path()
        conn = duckdb.connect(str(db_path))

        # 1. Calibration: threshold drift + fire-rate alerts
        cal_report = compute_calibration_report(conn)
        drift_count = cal_report.total_proposals_generated

        # Log fire-rate alerts at WARNING level
        for alert in cal_report.fire_rate_alerts:
            logger.warning(
                "Fire-rate alert [%s]: %s (fire_rate=%.1f%%, action=%s)",
                alert.signal_id,
                alert.alert_type,
                alert.fire_rate * 100,
                alert.recommendation,
            )

        # 2. Lifecycle: state transition proposals
        lifecycle_report = compute_lifecycle_proposals(conn)
        lifecycle_count = len(lifecycle_report.proposals)

        fire_alert_count = len(cal_report.fire_rate_alerts)
        total = drift_count + lifecycle_count

        logger.info(
            "Post-pipeline learning [%s]: %d drift proposals, "
            "%d fire-rate alerts, %d lifecycle proposals",
            ticker,
            drift_count,
            fire_alert_count,
            lifecycle_count,
        )

        return {
            "drift_proposals": drift_count,
            "fire_rate_alerts": fire_alert_count,
            "lifecycle_proposals": lifecycle_count,
            "total_proposals": total,
        }

    except Exception:
        logger.debug(
            "Post-pipeline learning failed for %s", ticker, exc_info=True
        )
        return {}

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


__all__ = ["run_post_pipeline_learning"]
