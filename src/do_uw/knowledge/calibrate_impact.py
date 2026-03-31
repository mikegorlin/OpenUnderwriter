"""Calibration impact simulation, git audit trail, and internal helpers.

Split from calibrate.py for file length compliance (<500 lines).
Contains impact simulation logic, git commit handling, and shared
helper functions used by the calibrate module's public API.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import duckdb

from do_uw.knowledge.feedback_models import ProposalRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Impact simulation
# ---------------------------------------------------------------------------


def compute_changes(
    conn: duckdb.DuckDBPyConnection,
    proposals: list[ProposalRecord],
) -> list[dict[str, Any]]:
    """Compute field-level diffs for each proposal.

    For THRESHOLD_CHANGE: compare proposed_changes fields vs current check.
    For NEW_CHECK: show all fields as new.
    For DEACTIVATION: show lifecycle_state change.

    Returns list of change dicts with proposal_id, description, field,
    old_value, new_value.
    """
    changes: list[dict[str, Any]] = []

    for proposal in proposals:
        pid = proposal.proposal_id or 0
        signal_id = proposal.signal_id or ""

        if proposal.proposal_type == "THRESHOLD_CHANGE":
            if not proposal.proposed_changes:
                continue

            # Get current check values for comparison
            current = get_current_check_fields(conn, signal_id)

            for field, new_value in proposal.proposed_changes.items():
                old_value = current.get(field, "N/A")
                changes.append({
                    "proposal_id": pid,
                    "description": f"Change {field} on {signal_id}",
                    "field": field,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                })

        elif proposal.proposal_type == "NEW_CHECK":
            changes.append({
                "proposal_id": pid,
                "description": f"Add new check {signal_id}",
                "field": "lifecycle_state",
                "old_value": "INCUBATING",
                "new_value": "ACTIVE",
            })

        elif proposal.proposal_type == "DEACTIVATION":
            changes.append({
                "proposal_id": pid,
                "description": f"Deactivate check {signal_id}",
                "field": "lifecycle_state",
                "old_value": "ACTIVE",
                "new_value": "INACTIVE",
            })

    return changes


def run_impact_simulation(
    conn: duckdb.DuckDBPyConnection,
    proposals: list[ProposalRecord],
    output_dir: Path,
) -> tuple[list[dict[str, str]], int]:
    """Run impact simulation against cached state files.

    Loads each state.json, runs execute_signals with current checks,
    applies proposals in-memory to get modified checks, runs again,
    and diffs the results.

    Returns (impact_list, state_files_tested).
    """
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.models.state import AnalysisState
    from do_uw.stages.analyze.signal_engine import execute_signals

    # Find all state files
    state_files = list(output_dir.glob("*/state.json"))
    if not state_files:
        logger.info("No state files found in %s for impact simulation", output_dir)
        return [], 0

    # Load current checks once
    checks_data = load_signals()

    current_checks: list[dict[str, Any]] = checks_data.get("signals", [])

    # Build modified checks by applying proposals in-memory
    modified_checks = apply_proposals_to_checks(current_checks, proposals)

    impact: list[dict[str, str]] = []
    tested = 0

    for state_path in state_files:
        try:
            with open(state_path, encoding="utf-8") as f:
                data = json.load(f)

            state = AnalysisState.model_validate(data)
            if state.extracted is None:
                continue

            ticker = state.ticker

            # Run with current checks
            current_results = execute_signals(
                current_checks, state.extracted, state.company,
            )

            # Run with modified checks
            proposed_results = execute_signals(
                modified_checks, state.extracted, state.company,
            )

            # Diff results
            current_by_id = {r.signal_id: r.status.value for r in current_results}
            proposed_by_id = {r.signal_id: r.status.value for r in proposed_results}

            # Find changed statuses
            all_ids = set(current_by_id.keys()) | set(proposed_by_id.keys())
            for signal_id in all_ids:
                curr = current_by_id.get(signal_id, "N/A")
                prop = proposed_by_id.get(signal_id, "N/A")
                if curr != prop:
                    impact.append({
                        "ticker": ticker,
                        "signal_id": signal_id,
                        "current_status": curr,
                        "proposed_status": prop,
                    })

            tested += 1

        except Exception:
            logger.exception(
                "Impact simulation failed for %s", state_path,
            )

    return impact, tested


def apply_proposals_to_checks(
    checks: list[dict[str, Any]],
    proposals: list[ProposalRecord],
) -> list[dict[str, Any]]:
    """Apply proposals in-memory to a copy of the checks list.

    Modifies thresholds, adds new checks, removes deactivated checks.
    Returns a new list (does not modify the original).
    """
    import copy

    modified = copy.deepcopy(checks)
    check_by_id = {c.get("id", ""): c for c in modified}

    for proposal in proposals:
        signal_id = proposal.signal_id or ""

        if proposal.proposal_type == "THRESHOLD_CHANGE":
            if signal_id in check_by_id and proposal.proposed_changes:
                check = check_by_id[signal_id]
                # Apply threshold changes to the check dict
                for field, value in proposal.proposed_changes.items():
                    if field.startswith("threshold_"):
                        # Map threshold_red -> check["threshold"]["red"]
                        threshold_key = field.replace("threshold_", "")
                        threshold = check.get("threshold", {})
                        if isinstance(threshold, dict):
                            threshold[threshold_key] = value
                            check["threshold"] = threshold
                    else:
                        check[field] = value

        elif proposal.proposal_type == "NEW_CHECK":
            # Add the proposed check to the list
            if proposal.proposed_check and signal_id not in check_by_id:
                new_check = dict(proposal.proposed_check)
                new_check["id"] = signal_id
                new_check.setdefault("execution_mode", "AUTO")
                modified.append(new_check)
                check_by_id[signal_id] = new_check

        elif proposal.proposal_type == "DEACTIVATION":
            # Remove the check from the list (deactivated)
            modified = [c for c in modified if c.get("id") != signal_id]
            check_by_id.pop(signal_id, None)

    return modified


# ---------------------------------------------------------------------------
# Git audit trail
# ---------------------------------------------------------------------------


def verify_clean_brain_tree() -> None:
    """Check that brain/ directory has no uncommitted changes.

    Raises RuntimeError if there are dirty files in the brain/ directory
    that are not related to the current calibration.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", "src/do_uw/brain/signals/"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            dirty_files = result.stdout.strip()
            msg = (
                f"brain/ directory has uncommitted changes:\n{dirty_files}\n"
                "Please commit or stash these changes before running calibration."
            )
            raise RuntimeError(msg)
    except FileNotFoundError:
        # git not available -- skip check
        logger.warning("git not available, skipping dirty tree check")
    except subprocess.CalledProcessError:
        # Not a git repo -- skip check
        logger.warning("Not in a git repository, skipping dirty tree check")


def git_commit_calibration(
    files_changed: list[str],
    summary: str,
    details: str,
) -> str | None:
    """Create a git commit for calibration changes.

    Stages specific files (never git add -A) and commits with a
    structured calibration message.

    Args:
        files_changed: List of file paths to stage.
        summary: One-line commit summary.
        details: Multi-line details for commit body.

    Returns:
        Commit hash string, or None if commit failed.
    """
    try:
        # Stage specific files only
        for filepath in files_changed:
            subprocess.run(
                ["git", "add", filepath],
                check=True,
                capture_output=True,
                text=True,
            )

        # Build commit message
        commit_msg = f"calibrate: {summary}\n\n{details}"

        # Create commit
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
            text=True,
        )

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        commit_hash = result.stdout.strip()

        logger.info("Calibration committed: %s", commit_hash)
        return commit_hash

    except FileNotFoundError:
        logger.warning("git not available, skipping commit")
        return None
    except subprocess.CalledProcessError as exc:
        logger.warning("Git commit failed: %s", exc.stderr or exc.stdout)
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def get_current_check_fields(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
) -> dict[str, Any]:
    """Get current check field values for diff comparison."""
    row = conn.execute(
        """SELECT threshold_type, threshold_red, threshold_yellow,
                  threshold_clear, lifecycle_state, name
           FROM brain_signals_current
           WHERE signal_id = ?""",
        [signal_id],
    ).fetchone()

    if row is None:
        return {}

    return {
        "threshold_type": row[0],
        "threshold_red": row[1],
        "threshold_yellow": row[2],
        "threshold_clear": row[3],
        "lifecycle_state": row[4],
        "name": row[5],
    }


def get_proposals_by_ids(
    conn: duckdb.DuckDBPyConnection,
    proposal_ids: list[int],
) -> list[ProposalRecord]:
    """Get specific proposals by ID."""
    if not proposal_ids:
        return []

    placeholders = ",".join(["?"] * len(proposal_ids))
    rows = conn.execute(
        f"""SELECT proposal_id, source_type, source_ref, signal_id,
                  proposal_type, proposed_check, proposed_changes,
                  backtest_results, rationale, status, reviewed_by,
                  created_at
           FROM brain_proposals
           WHERE proposal_id IN ({placeholders})""",
        proposal_ids,
    ).fetchall()

    results: list[ProposalRecord] = []
    for row in rows:
        proposed_check = parse_json_field(row[5])
        proposed_changes = parse_json_field(row[6])
        backtest_results = parse_json_field(row[7])

        results.append(
            ProposalRecord(
                proposal_id=row[0],
                source_type=row[1],
                source_ref=row[2],
                signal_id=row[3],
                proposal_type=row[4],
                proposed_check=proposed_check,
                proposed_changes=proposed_changes,
                backtest_results=backtest_results,
                rationale=row[8],
                status=row[9],
                reviewed_by=row[10],
                created_at=row[11],
            )
        )

    return results


def resolve_related_feedback(
    conn: duckdb.DuckDBPyConnection,
    proposals: list[ProposalRecord],
) -> int:
    """Mark feedback entries related to applied proposals as APPLIED.

    Looks up source_ref on proposals that match 'feedback_N' pattern,
    and marks those feedback entries as applied.

    Returns count of feedback entries resolved.
    """
    from do_uw.knowledge.feedback import mark_feedback_applied

    resolved = 0
    for proposal in proposals:
        source_ref = proposal.source_ref or ""
        if source_ref.startswith("feedback_"):
            try:
                feedback_id = int(source_ref.replace("feedback_", ""))
                # Use proposal_id as change_id reference
                mark_feedback_applied(
                    conn, feedback_id, change_id=proposal.proposal_id or 0,
                )
                resolved += 1
            except (ValueError, Exception):
                logger.warning(
                    "Could not resolve feedback for source_ref %s",
                    source_ref,
                )

    return resolved


def parse_json_field(value: Any) -> dict[str, Any] | None:
    """Parse a JSON field that may be a string, dict, or None."""
    if value is None:
        return None
    if isinstance(value, dict):
        from typing import cast
        return cast(dict[str, Any], value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                from typing import cast
                return cast(dict[str, Any], parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return None
