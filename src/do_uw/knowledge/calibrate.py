"""Calibration workflow: preview, impact simulation, and apply with git audit.

Builds the human-in-the-loop control for knowledge evolution:
- Preview pending proposals with what-if impact simulation
- Apply approved proposals with structured git commits
- Backtest proposals against cached state files via execute_signals

The system proposes, the human disposes. Nothing auto-changes.
All calibration requires explicit human approval via CLI.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import duckdb
from pydantic import BaseModel, Field

from do_uw.knowledge.calibrate_impact import (
    compute_changes as _compute_changes,
)
from do_uw.knowledge.calibrate_impact import (
    get_proposals_by_ids as _get_proposals_by_ids,
)
from do_uw.knowledge.calibrate_impact import (
    git_commit_calibration as _git_commit_calibration,
)
from do_uw.knowledge.calibrate_impact import (
    parse_json_field as _parse_json_field,
)
from do_uw.knowledge.calibrate_impact import (
    resolve_related_feedback as _resolve_related_feedback,
)
from do_uw.knowledge.calibrate_impact import (
    run_impact_simulation as _run_impact_simulation,
)
from do_uw.knowledge.calibrate_impact import (
    verify_clean_brain_tree as _verify_clean_brain_tree,
)
from do_uw.knowledge.feedback_models import ProposalRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def _empty_proposal_list() -> list[ProposalRecord]:
    return []


def _empty_change_list() -> list[dict[str, Any]]:
    return []


def _empty_impact_list() -> list[dict[str, str]]:
    return []


def _empty_str_list() -> list[str]:
    return []


class CalibrationPreview(BaseModel):
    """Preview of pending calibration proposals with impact simulation."""

    proposals: list[ProposalRecord] = Field(
        default_factory=_empty_proposal_list,
    )
    changes: list[dict[str, Any]] = Field(
        default_factory=_empty_change_list,
    )
    """Per-proposal field-level diffs: [{proposal_id, description, field, old_value, new_value}]."""
    impact: list[dict[str, str]] = Field(
        default_factory=_empty_impact_list,
    )
    """Per-company check status changes: [{ticker, signal_id, current_status, proposed_status}]."""
    state_files_tested: int = 0


class ApplyResult(BaseModel):
    """Result of applying calibration proposals."""

    commit_hash: str | None = None
    proposals_applied: int = 0
    checks_modified: list[str] = Field(
        default_factory=_empty_str_list,
    )
    """Check IDs that were modified."""
    feedback_resolved: int = 0
    """Feedback entries marked APPLIED."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_pending_proposals(
    conn: duckdb.DuckDBPyConnection,
) -> list[ProposalRecord]:
    """Query pending proposals from brain_proposals table.

    Args:
        conn: DuckDB connection with brain schema.

    Returns:
        List of ProposalRecord with status='PENDING', ordered by created_at.
    """
    rows = conn.execute(
        """SELECT proposal_id, source_type, source_ref, signal_id,
                  proposal_type, proposed_check, proposed_changes,
                  backtest_results, rationale, status, reviewed_by,
                  created_at
           FROM brain_proposals
           WHERE status = 'PENDING'
           ORDER BY created_at"""
    ).fetchall()

    results: list[ProposalRecord] = []
    for row in rows:
        proposed_check = _parse_json_field(row[5])
        proposed_changes = _parse_json_field(row[6])
        backtest_results = _parse_json_field(row[7])

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


def preview_calibration(
    conn: duckdb.DuckDBPyConnection,
    output_dir: Path = Path("output"),
) -> CalibrationPreview:
    """Preview pending proposals with impact simulation.

    Loads all pending proposals, computes field-level diffs showing
    what would change, then runs impact simulation against cached
    state files by calling execute_signals directly (not run_backtest,
    which always loads signals from brain_signals_active with no
    override parameter).

    Args:
        conn: DuckDB connection with brain schema.
        output_dir: Directory containing ticker/state.json files.

    Returns:
        CalibrationPreview with proposals, changes, impact, and
        count of state files tested.
    """
    proposals = get_pending_proposals(conn)

    if not proposals:
        return CalibrationPreview()

    # Compute field-level diffs per proposal
    changes = _compute_changes(conn, proposals)

    # Run impact simulation against cached state files
    impact, state_count = _run_impact_simulation(conn, proposals, output_dir)

    return CalibrationPreview(
        proposals=proposals,
        changes=changes,
        impact=impact,
        state_files_tested=state_count,
    )


def apply_calibration(
    conn: duckdb.DuckDBPyConnection,
    proposal_ids: list[int] | None = None,
) -> ApplyResult:
    """Apply approved calibration proposals with git audit trail.

    For each proposal:
    - NEW_CHECK: promote INCUBATING check to ACTIVE via BrainWriter
    - THRESHOLD_CHANGE: update check via BrainWriter with proposed_changes
    - DEACTIVATION: set lifecycle_state='INACTIVE' via BrainWriter

    After all changes: export signals.json, update proposal status,
    mark related feedback as APPLIED, and create a git commit.

    Args:
        conn: DuckDB connection with brain schema.
        proposal_ids: Specific proposal IDs to apply. None = all pending.

    Returns:
        ApplyResult with commit hash, counts of applied proposals and
        modified checks, and feedback entries resolved.

    Raises:
        RuntimeError: If brain/ directory has uncommitted changes.
    """
    from do_uw.brain.brain_writer import BrainWriter

    # Verify git working tree is clean for brain/ directory
    _verify_clean_brain_tree()

    # Load proposals to apply
    if proposal_ids is not None:
        proposals = _get_proposals_by_ids(conn, proposal_ids)
    else:
        proposals = get_pending_proposals(conn)

    if not proposals:
        return ApplyResult()

    # Apply each proposal via BrainWriter (reuse conn)
    writer = BrainWriter(db_path=":memory:")
    writer._conn = conn  # pyright: ignore[reportPrivateUsage]

    checks_modified: list[str] = []

    for proposal in proposals:
        signal_id = proposal.signal_id or ""
        if not signal_id:
            logger.warning(
                "Proposal %d has no signal_id, skipping",
                proposal.proposal_id or 0,
            )
            continue

        try:
            if proposal.proposal_type == "NEW_CHECK":
                # Promote INCUBATING -> ACTIVE
                writer.promote_check(
                    signal_id,
                    new_lifecycle="ACTIVE",
                    reason=f"Approved via calibration (proposal {proposal.proposal_id})",
                    promoted_by="calibration",
                )
                checks_modified.append(signal_id)

            elif proposal.proposal_type == "THRESHOLD_CHANGE":
                if proposal.proposed_changes:
                    writer.update_check(
                        signal_id,
                        changes=proposal.proposed_changes,
                        reason=f"Threshold change via calibration (proposal {proposal.proposal_id})",
                        changed_by="calibration",
                    )
                    checks_modified.append(signal_id)

            elif proposal.proposal_type == "DEACTIVATION":
                writer.update_check(
                    signal_id,
                    changes={"lifecycle_state": "INACTIVE"},
                    reason=f"Deactivated via calibration (proposal {proposal.proposal_id})",
                    changed_by="calibration",
                )
                checks_modified.append(signal_id)

        except Exception:
            logger.exception(
                "Failed to apply proposal %d for check %s",
                proposal.proposal_id or 0,
                signal_id,
            )

    # NOTE: Do NOT export signals.json here. The authoritative check registry
    # is the hand-curated BRAIN_CHECKS_V7 file (396 checks, 16K+ lines).
    # writer.export_json() exports only ACTIVE-lifecycle signals from DuckDB,
    # which is a tiny subset, and overwrites the full registry — corrupting it.
    # DuckDB state is sufficient for calibration tracking; JSON export is only
    # needed for manual migration/snapshot via CLI command.

    # Update proposal status to APPLIED
    for proposal in proposals:
        pid = proposal.proposal_id
        if pid is not None:
            conn.execute(
                "UPDATE brain_proposals SET status = 'APPLIED', "
                "reviewed_at = current_timestamp WHERE proposal_id = ?",
                [pid],
            )

    # Mark related feedback as APPLIED
    feedback_resolved = _resolve_related_feedback(conn, proposals)

    # Build summary for git commit
    summary = f"apply {len(proposals)} proposals, modify {len(checks_modified)} checks"
    details_lines: list[str] = []
    for p in proposals:
        details_lines.append(
            f"- [{p.proposal_type}] {p.signal_id}: {p.rationale[:80]}"
        )
    details = "\n".join(details_lines)

    # Git commit
    files_changed = [
        str(Path(__file__).parent.parent / "brain" / "brain.duckdb"),
    ]
    commit_hash = _git_commit_calibration(files_changed, summary, details)

    return ApplyResult(
        commit_hash=commit_hash,
        proposals_applied=len(proposals),
        checks_modified=checks_modified,
        feedback_resolved=feedback_resolved,
    )


# ---------------------------------------------------------------------------
# YAML-based apply (Phase 51-03): re-exported from calibrate_apply.py
# ---------------------------------------------------------------------------
from do_uw.knowledge.calibrate_apply import apply_single_proposal  # noqa: E402, F401


__all__ = [
    "ApplyResult",
    "CalibrationPreview",
    "apply_calibration",
    "apply_single_proposal",
    "get_pending_proposals",
    "preview_calibration",
]
