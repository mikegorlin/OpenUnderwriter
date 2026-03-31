"""Export/import feedback review files for offline editing.

Provides:
- export_review_file(): Generate a JSON review file with triggered signals
- import_review_file(): Validate and ingest reactions from an exported file
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from do_uw.knowledge.feedback_models import FeedbackReaction, ReactionType

logger = logging.getLogger(__name__)


def export_review_file(
    ticker: str,
    triggered_signals: dict[str, dict[str, Any]],
    output_path: Path,
    run_id: str | None = None,
) -> Path:
    """Export triggered signals as a structured JSON review file.

    The file includes signal details and blank reaction fields for
    the underwriter to fill in offline.

    Args:
        ticker: Stock ticker.
        triggered_signals: Dict of signal_id -> result dict from state.json.
        output_path: Path to write the review file.
        run_id: Optional run ID for traceability.

    Returns:
        Path to the written file.
    """
    review_data: dict[str, Any] = {
        "_metadata": {
            "ticker": ticker,
            "run_id": run_id,
            "signal_count": len(triggered_signals),
            "instructions": (
                "Fill in 'reaction' (AGREE/DISAGREE/ADJUST_SEVERITY), "
                "'rationale' (required), and optionally 'severity_target' "
                "(for ADJUST_SEVERITY only) for each signal you want to "
                "review. Leave 'reaction' as null to skip a signal."
            ),
        },
        "signals": [],
    }

    for sig_id, result in triggered_signals.items():
        review_data["signals"].append({
            "signal_id": sig_id,
            "signal_name": result.get("check_name", result.get("signal_name", "")),
            "value": result.get("value"),
            "threshold_level": result.get("threshold_level", ""),
            "evidence": result.get("evidence", ""),
            "factors": result.get("factors", []),
            # Fields for underwriter to fill:
            "reaction": None,  # AGREE, DISAGREE, or ADJUST_SEVERITY
            "severity_target": None,  # Only for ADJUST_SEVERITY
            "rationale": None,  # Required for any reaction
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(review_data, indent=2, default=str),
        encoding="utf-8",
    )

    logger.info("Exported review file for %s: %s", ticker, output_path)
    return output_path


def import_review_file(
    conn: duckdb.DuckDBPyConnection,
    file_path: Path,
    reviewer: str = "underwriter",
) -> tuple[int, list[str]]:
    """Import and validate reactions from an exported review file.

    Validates:
    - Each reaction type is one of AGREE/DISAGREE/ADJUST_SEVERITY
    - Rationale is non-empty for every reaction
    - Signal IDs exist in brain_signals_active (warns but does not block)

    Args:
        conn: DuckDB connection with brain schema.
        file_path: Path to the review JSON file.
        reviewer: Reviewer name for attribution.

    Returns:
        (count_imported, list_of_errors) tuple.
    """
    from do_uw.knowledge.feedback import record_reaction

    data = json.loads(file_path.read_text(encoding="utf-8"))
    metadata = data.get("_metadata", {})
    ticker = metadata.get("ticker", "UNKNOWN")
    run_id = metadata.get("run_id")
    signals = data.get("signals", [])

    errors: list[str] = []
    imported = 0
    valid_types = {t.value for t in ReactionType}

    # Build set of known signal IDs for validation
    try:
        known_ids = {
            row[0]
            for row in conn.execute(
                "SELECT signal_id FROM brain_signals_active"
            ).fetchall()
        }
    except Exception:
        known_ids = set()  # Table might not exist in test

    for i, entry in enumerate(signals):
        sig_id = entry.get("signal_id", "")
        reaction = entry.get("reaction")
        rationale = entry.get("rationale")
        severity_target = entry.get("severity_target")

        # Skip entries with no reaction
        if reaction is None:
            continue

        # Validate reaction type
        reaction_upper = str(reaction).upper()
        if reaction_upper not in valid_types:
            errors.append(
                f"Signal {i + 1} ({sig_id}): invalid reaction '{reaction}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )
            continue

        # Validate rationale
        if not rationale or not str(rationale).strip():
            errors.append(
                f"Signal {i + 1} ({sig_id}): rationale is required for every reaction"
            )
            continue

        # Warn on unknown signal ID (but still import)
        if known_ids and sig_id not in known_ids:
            errors.append(
                f"Signal {i + 1} ({sig_id}): [warning] signal_id not found in brain_signals_active"
            )

        # Record the reaction
        feedback_reaction = FeedbackReaction(
            ticker=ticker,
            signal_id=sig_id,
            run_id=run_id,
            reaction_type=ReactionType(reaction_upper),
            severity_target=severity_target,
            rationale=str(rationale).strip(),
            reviewer=reviewer,
        )

        try:
            record_reaction(conn, feedback_reaction)
            imported += 1
        except Exception as exc:
            errors.append(f"Signal {i + 1} ({sig_id}): import failed: {exc}")

    return imported, errors
