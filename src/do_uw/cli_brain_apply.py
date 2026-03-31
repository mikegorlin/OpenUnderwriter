"""CLI sub-command: brain apply-proposal.

Applies a single calibration proposal by modifying brain YAML,
running brain build to validate, and creating a git commit.
Split from cli_brain.py for file length compliance (<500 lines).
"""

from __future__ import annotations

import typer
from rich.console import Console

from do_uw.cli_brain import brain_app

console = Console()


# ---------------------------------------------------------------------------
# brain apply-proposal
# ---------------------------------------------------------------------------


@brain_app.command("apply-proposal")
def apply_proposal(
    proposal_id: int = typer.Argument(help="Proposal ID to apply"),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Apply a calibration proposal by modifying brain YAML.

    Locates the signal's YAML file, modifies it with comment-preserving
    round-trip editing, shows the diff for review, runs brain build to
    validate, and creates a git commit.

    One proposal at a time. Each gets its own validation and commit.
    """
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.calibrate_apply import apply_single_proposal

    # Verify clean git tree first
    from do_uw.knowledge.calibrate_impact import verify_clean_brain_tree

    try:
        verify_clean_brain_tree()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        result = apply_single_proposal(conn, proposal_id, skip_confirm=yes)

        if result.proposals_applied == 0:
            console.print("[dim]No proposals were applied.[/dim]")
            raise typer.Exit(code=1)

    finally:
        conn.close()
