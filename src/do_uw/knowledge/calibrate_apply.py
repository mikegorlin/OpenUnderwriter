"""YAML-based calibration apply: single proposal write-back to YAML.

Phase 51-03 implementation that closes the feedback loop by writing
calibration changes to YAML source of truth (not just DuckDB). Each
proposal gets its own validation and git commit.

Flow: load proposal -> locate YAML -> modify with ruamel.yaml ->
      brain build -> validate -> git commit -> mark APPLIED.
"""

from __future__ import annotations

import logging
from typing import Any

import duckdb

from do_uw.knowledge.calibrate_impact import (
    git_commit_calibration,
    get_proposals_by_ids,
    resolve_related_feedback,
)
from do_uw.knowledge.feedback_models import ProposalRecord

logger = logging.getLogger(__name__)


def apply_single_proposal(
    conn: duckdb.DuckDBPyConnection,
    proposal_id: int,
    skip_confirm: bool = False,
) -> "ApplyResult":
    """Apply a single calibration proposal by modifying brain YAML.

    This is the Phase 51 implementation that writes to YAML source of truth,
    rebuilds DuckDB via brain build, validates, and git commits.

    Flow:
    1. Load proposal from brain_proposals
    2. Locate signal's YAML file via build_signal_yaml_index()
    3. Compute YAML changes from proposal
    4. Modify YAML with ruamel.yaml (comment-preserving)
    5. Show diff, confirm (unless skip_confirm)
    6. Run brain build to rebuild DuckDB
    7. Validate signal count matches
    8. Git commit the modified YAML file
    9. Update proposal status to APPLIED

    If brain build fails, reverts YAML and leaves proposal PENDING.

    Args:
        conn: DuckDB connection (used for proposal queries, NOT for writing).
        proposal_id: Single proposal ID to apply.
        skip_confirm: Skip confirmation prompt (--yes flag).

    Returns:
        ApplyResult with commit hash, modified checks, etc.
    """
    import typer
    from rich.console import Console
    from rich.syntax import Syntax

    from do_uw.knowledge.calibrate import ApplyResult
    from do_uw.knowledge.yaml_writer import (
        build_signal_yaml_index,
        modify_signal_in_yaml,
        revert_yaml_change,
    )

    console = Console()

    # Step 1: Load proposal
    proposals = get_proposals_by_ids(conn, [proposal_id])
    if not proposals:
        console.print(f"[red]Proposal {proposal_id} not found.[/red]")
        return ApplyResult()

    proposal = proposals[0]
    signal_id = proposal.signal_id or ""

    if not signal_id:
        console.print(f"[red]Proposal {proposal_id} has no signal_id.[/red]")
        return ApplyResult()

    if proposal.status != "PENDING":
        console.print(
            f"[yellow]Proposal {proposal_id} status is '{proposal.status}', "
            f"not PENDING. Skipping.[/yellow]"
        )
        return ApplyResult()

    # Step 2: Locate YAML file
    yaml_index = build_signal_yaml_index()
    yaml_path = yaml_index.get(signal_id)

    if yaml_path is None:
        console.print(
            f"[red]Signal {signal_id} not found in any YAML file. "
            f"Cannot apply proposal.[/red]"
        )
        return ApplyResult()

    # Step 3: Compute YAML changes from proposal
    changes = _compute_yaml_changes(proposal)
    if not changes:
        console.print(
            f"[yellow]No concrete changes computed for proposal {proposal_id}. "
            f"Proposed changes: {proposal.proposed_changes}[/yellow]"
        )
        return ApplyResult()

    # Step 4: Modify YAML
    try:
        diff_str = modify_signal_in_yaml(yaml_path, signal_id, changes)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]YAML modification failed: {exc}[/red]")
        return ApplyResult()

    # Step 5: Show diff and confirm
    if diff_str:
        console.print(f"\n[bold]Changes to {yaml_path.name}:[/bold]")
        console.print(Syntax(diff_str, "diff", theme="monokai"))
    else:
        console.print(
            "[yellow]No visible changes in diff "
            "(fields may already match).[/yellow]"
        )

    if not skip_confirm:
        if not typer.confirm(
            f"Apply proposal {proposal_id} "
            f"({proposal.proposal_type} on {signal_id})?",
            default=False,
        ):
            # User cancelled -- revert
            revert_yaml_change(yaml_path)
            console.print("[dim]Cancelled. YAML reverted.[/dim]")
            return ApplyResult()

    # Step 6: Run brain build
    console.print("[dim]Running brain build...[/dim]")

    # Get pre-build signal count for validation
    try:
        pre_count_row = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_active"
        ).fetchone()
        pre_count = pre_count_row[0] if pre_count_row else 0
    except Exception:
        pre_count = 0

    try:
        from do_uw.brain.brain_build_signals import build_checks_from_yaml
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        db_path = get_brain_db_path()
        conn.close()
        build_conn = connect_brain_db(db_path)
        try:
            build_result = build_checks_from_yaml(build_conn)
        finally:
            build_conn.close()

        # Reopen connection for remaining operations
        conn = connect_brain_db(db_path)

        console.print(
            f"[green]Brain build complete: {build_result['signals']} signals "
            f"from {build_result['yaml_files']} YAML files[/green]"
        )

    except Exception as exc:
        # Build failed -- revert YAML
        console.print(f"[red]Brain build failed: {exc}[/red]")
        console.print("[yellow]Reverting YAML change...[/yellow]")
        revert_yaml_change(yaml_path)
        console.print("[yellow]YAML reverted. Proposal remains PENDING.[/yellow]")
        return ApplyResult()

    # Step 7: Validate signal count
    try:
        post_count_row = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_active"
        ).fetchone()
        post_count = post_count_row[0] if post_count_row else 0

        if proposal.proposal_type != "DEACTIVATION" and post_count < pre_count:
            console.print(
                f"[yellow]Warning: signal count dropped from {pre_count} "
                f"to {post_count} after build. "
                f"This may indicate an issue.[/yellow]"
            )
    except Exception:
        pass  # Non-fatal: validation is best-effort

    # Step 8: Git commit
    summary = _build_commit_summary(proposal)
    details = (
        f"Proposal {proposal_id}: {proposal.proposal_type}\n"
        f"Signal: {signal_id}\n"
        f"Changes: {changes}\n"
        f"Rationale: {proposal.rationale}"
    )

    commit_hash = git_commit_calibration(
        [str(yaml_path)],
        summary,
        details,
    )

    # Step 8b: Log provenance for Phase 57 proposal types
    if proposal.proposal_type in (
        "THRESHOLD_CALIBRATION", "LIFECYCLE_TRANSITION", "CORRELATION_ANNOTATION",
    ):
        try:
            from do_uw.brain.brain_writer_export import log_change

            log_change(
                conn, signal_id,
                old_version=None, new_version=1,
                change_type=proposal.proposal_type,
                description=proposal.rationale,
                changed_by="brain_audit",
                fields_changed=list(changes.keys()),
            )
        except Exception as exc:
            logger.warning("Failed to log changelog for %s: %s", signal_id, exc)

    # Step 9: Update proposal status
    conn.execute(
        "UPDATE brain_proposals SET status = 'APPLIED', "
        "reviewed_at = current_timestamp WHERE proposal_id = ?",
        [proposal_id],
    )

    # Mark related feedback as APPLIED
    feedback_resolved = resolve_related_feedback(conn, [proposal])

    console.print(
        f"\n[green]Proposal {proposal_id} applied successfully.[/green]"
    )
    if commit_hash:
        console.print(f"[green]Git commit: {commit_hash}[/green]")
    else:
        console.print(
            "[yellow]Git commit failed "
            "(YAML changes applied but not committed).[/yellow]"
        )

    return ApplyResult(
        commit_hash=commit_hash,
        proposals_applied=1,
        checks_modified=[signal_id],
        feedback_resolved=feedback_resolved,
    )


# ---------------------------------------------------------------------------
# YAML change computation helpers
# ---------------------------------------------------------------------------


def _compute_yaml_changes(proposal: ProposalRecord) -> dict[str, Any]:
    """Compute concrete YAML field changes from a proposal.

    Maps proposal_type and proposed_changes to actual YAML field modifications.
    """
    changes: dict[str, Any] = {}

    if proposal.proposal_type == "DEACTIVATION":
        changes["lifecycle_state"] = "INACTIVE"

    elif proposal.proposal_type == "THRESHOLD_CHANGE":
        if proposal.proposed_changes:
            for key, value in proposal.proposed_changes.items():
                # Skip internal meta keys
                if key.startswith("_"):
                    continue

                if key == "severity_target":
                    # Map severity target to threshold annotation
                    changes["calibration_notes"] = (
                        f"Severity adjustment to {value} "
                        f"based on underwriter feedback"
                    )
                    changes["threshold"] = {"_calibrated_target": value}
                elif key.startswith("threshold_"):
                    # Direct threshold field: threshold_red -> threshold.red
                    threshold_subkey = key.replace("threshold_", "")
                    changes.setdefault("threshold", {})[threshold_subkey] = value
                elif key == "lifecycle_state":
                    changes["lifecycle_state"] = value
                else:
                    changes[key] = value

    elif proposal.proposal_type == "NEW_CHECK":
        # NEW_CHECK proposals should have a full proposed_check dict
        if proposal.proposed_check:
            changes = dict(proposal.proposed_check)

    elif proposal.proposal_type == "THRESHOLD_CALIBRATION":
        # Phase 57 Plan 01: threshold adjustments from statistical calibration
        if proposal.proposed_changes:
            for key, value in proposal.proposed_changes.items():
                if key.startswith("threshold_"):
                    threshold_subkey = key.replace("threshold_", "")
                    changes.setdefault("threshold", {})[threshold_subkey] = value
                elif key == "calibration_notes":
                    changes["calibration_notes"] = value

    elif proposal.proposal_type == "CORRELATION_ANNOTATION":
        # Phase 57 Plan 02: write correlated_signals to YAML
        if proposal.proposed_changes and "correlated_signals" in proposal.proposed_changes:
            changes["correlated_signals"] = proposal.proposed_changes["correlated_signals"]

    elif proposal.proposal_type == "LIFECYCLE_TRANSITION":
        # Phase 57 Plan 03: change lifecycle_state
        if proposal.proposed_changes and "lifecycle_state" in proposal.proposed_changes:
            changes["lifecycle_state"] = proposal.proposed_changes["lifecycle_state"]

    return changes


def _build_commit_summary(proposal: ProposalRecord) -> str:
    """Build a structured git commit summary line.

    Format: brain(calibrate): <action> <signal_id> <details>
    """
    signal_id = proposal.signal_id or "unknown"
    # Convert dots to dashes for git message readability
    signal_short = signal_id.replace(".", "-")

    backtest = proposal.backtest_results or {}
    reaction_counts = backtest.get("reaction_counts", {})
    total = reaction_counts.get("total", 0)

    if proposal.proposal_type == "DEACTIVATION":
        return (
            f"brain(calibrate): deactivate {signal_short} "
            f"based on {total} feedback entries"
        )
    elif proposal.proposal_type == "THRESHOLD_CHANGE":
        pc = proposal.proposed_changes or {}
        if "severity_target" in pc:
            target = pc["severity_target"]
            return (
                f"brain(calibrate): adjust {signal_short} severity "
                f"to {target} based on {total} feedback entries"
            )
        else:
            return (
                f"brain(calibrate): adjust {signal_short} threshold "
                f"based on {total} feedback entries"
            )
    else:
        return f"brain(calibrate): apply proposal for {signal_short}"
