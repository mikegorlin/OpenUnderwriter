"""CLI sub-commands for underwriter feedback on check results.

Provides commands for recording and reviewing feedback:
- ``do-uw feedback add AAPL --check X --note Y`` -- record feedback
- ``do-uw feedback summary`` -- show pending proposals, threshold drift, coverage gaps
- ``do-uw feedback list`` -- list feedback entries with optional filters
- ``do-uw feedback capture AAPL`` -- interactive reaction capture on triggered signals
- ``do-uw feedback export AAPL`` -- export triggered signals for offline review
- ``do-uw feedback import <file>`` -- import reactions from exported review file

Registered as a Typer sub-app in cli.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

feedback_app = typer.Typer(
    name="feedback",
    help="Underwriter feedback: record, review, summarize",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Helper: load triggered signals from state.json
# ---------------------------------------------------------------------------


def _load_triggered_signals(
    ticker: str,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Load triggered signal results from the most recent state.json for a ticker.

    Scans output/ for directories matching {TICKER}-* pattern, picks the
    most recent by directory name (date-sorted), loads state.json, and
    filters analysis.signal_results to TRIGGERED status only.

    Returns (triggered_signals_dict, run_id) or ({}, None) if not found.
    """
    output_dir = Path("output")
    # Find most recent output directory for this ticker
    ticker_upper = ticker.upper()
    matches = sorted(
        output_dir.glob(f"{ticker_upper}-*"),
        reverse=True,  # Most recent first (date in dir name)
    )

    if not matches:
        # Try bare ticker directory
        bare = output_dir / ticker_upper
        if bare.exists():
            matches = [bare]

    for match_dir in matches:
        state_path = match_dir / "state.json"
        if state_path.exists():
            with open(state_path, encoding="utf-8") as f:
                data = json.load(f)

            analysis = data.get("analysis", {})
            signal_results = analysis.get("signal_results") or analysis.get("check_results") or {}
            run_id = analysis.get("run_id")

            # Filter to TRIGGERED only (status is RED or YELLOW in threshold_level,
            # or status field is "TRIGGERED")
            triggered: dict[str, dict[str, Any]] = {}
            for sig_id, result in signal_results.items():
                status = result.get("status", "")
                threshold_level = result.get("threshold_level", "")
                if status == "TRIGGERED" or threshold_level in ("red", "yellow"):
                    triggered[sig_id] = result

            return triggered, run_id

    return {}, None


# ---------------------------------------------------------------------------
# Subcommand: add (record feedback)
# ---------------------------------------------------------------------------


@feedback_app.command("add")
def feedback_add(
    ticker: str = typer.Argument(help="Stock ticker (e.g., AAPL)"),
    check: str | None = typer.Option(
        None,
        "--check",
        "-c",
        help="Check ID this feedback applies to",
    ),
    note: str = typer.Option(
        ...,
        "--note",
        "-n",
        help="Feedback text (required)",
    ),
    reviewer: str = typer.Option(
        "anonymous",
        "--reviewer",
        "-r",
        help="Named reviewer",
    ),
    feedback_type: str = typer.Option(
        "ACCURACY",
        "--type",
        "-t",
        help="Feedback type: ACCURACY, THRESHOLD, or MISSING_COVERAGE",
    ),
    direction: str | None = typer.Option(
        None,
        "--direction",
        "-d",
        help="Direction: FALSE_POSITIVE, FALSE_NEGATIVE, TOO_SENSITIVE, TOO_LOOSE",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Optional run ID for traceability",
    ),
) -> None:
    """Record feedback on a check result."""
    # Validate feedback_type
    valid_types = {"ACCURACY", "THRESHOLD", "MISSING_COVERAGE"}
    feedback_type_upper = feedback_type.upper()
    if feedback_type_upper not in valid_types:
        console.print(
            f"[red]Invalid feedback type '{feedback_type}'. "
            f"Must be one of: {', '.join(sorted(valid_types))}[/red]"
        )
        raise typer.Exit(code=1)

    # Validate direction (only valid for ACCURACY and THRESHOLD)
    valid_directions = {
        "FALSE_POSITIVE", "FALSE_NEGATIVE", "TOO_SENSITIVE", "TOO_LOOSE",
    }
    direction_upper: str | None = None
    if direction is not None:
        direction_upper = direction.upper()
        if direction_upper not in valid_directions:
            console.print(
                f"[red]Invalid direction '{direction}'. "
                f"Must be one of: {', '.join(sorted(valid_directions))}[/red]"
            )
            raise typer.Exit(code=1)
        if feedback_type_upper == "MISSING_COVERAGE":
            console.print(
                "[yellow]Direction is not applicable for MISSING_COVERAGE feedback. "
                "Ignoring.[/yellow]"
            )
            direction_upper = None

    # Connect to brain.duckdb and record
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback import record_feedback
    from do_uw.knowledge.feedback_models import FeedbackEntry

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)  # Ensure tables exist

    try:
        entry = FeedbackEntry(
            ticker=ticker.upper(),
            signal_id=check,
            run_id=run_id,
            feedback_type=feedback_type_upper,  # type: ignore[arg-type]
            direction=direction_upper,  # type: ignore[arg-type]
            note=note,
            reviewer=reviewer,
        )

        feedback_id = record_feedback(conn, entry)
        console.print(
            f"[green]Feedback recorded (ID: {feedback_id})[/green]"
        )

        # If MISSING_COVERAGE, show the auto-proposed check
        if feedback_type_upper == "MISSING_COVERAGE":
            # Query for the latest proposal linked to this feedback
            result = conn.execute(
                "SELECT signal_id FROM brain_proposals "
                "WHERE source_ref = ? ORDER BY created_at DESC LIMIT 1",
                [f"feedback_{feedback_id}"],
            ).fetchone()
            if result:
                console.print(
                    f"[green]Auto-proposed INCUBATING check: {result[0]}[/green]"
                )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subcommand: summary
# ---------------------------------------------------------------------------


@feedback_app.command("summary")
def feedback_summary(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show recent feedback and proposals as tables",
    ),
) -> None:
    """Show pending feedback summary: accuracy flags, threshold tuning, coverage gaps."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback import get_feedback_summary

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)  # Ensure tables exist

    try:
        summary = get_feedback_summary(conn)

        console.print("\n[bold]Pending Feedback Summary[/bold]")
        console.print("=" * 26)
        console.print(f"Accuracy flags:    {summary.pending_accuracy}")
        console.print(f"Threshold tuning:  {summary.pending_threshold}")
        console.print(f"Coverage gaps:     {summary.pending_coverage_gaps}")
        console.print(f"Pending proposals: {summary.pending_proposals}")

        if verbose and summary.recent_feedback:
            console.print()
            table = Table(title="Recent Feedback")
            table.add_column("ID", width=5, justify="right")
            table.add_column("Ticker", width=8)
            table.add_column("Check", min_width=15)
            table.add_column("Type", width=18)
            table.add_column("Direction", width=16)
            table.add_column("Reviewer", width=12)
            table.add_column("Note", min_width=20)

            for entry in summary.recent_feedback:
                table.add_row(
                    str(entry.feedback_id or ""),
                    entry.ticker or "",
                    entry.signal_id or "",
                    entry.feedback_type,
                    entry.direction or "",
                    entry.reviewer,
                    (entry.note[:60] + "...") if len(entry.note) > 60 else entry.note,
                )
            console.print(table)

        if verbose and summary.recent_proposals:
            console.print()
            table = Table(title="Recent Proposals")
            table.add_column("ID", width=5, justify="right")
            table.add_column("Source", width=12)
            table.add_column("Check", min_width=15)
            table.add_column("Type", width=18)
            table.add_column("Status", width=10)
            table.add_column("Rationale", min_width=20)

            for proposal in summary.recent_proposals:
                table.add_row(
                    str(proposal.proposal_id or ""),
                    proposal.source_type,
                    proposal.signal_id or "",
                    proposal.proposal_type,
                    proposal.status,
                    (proposal.rationale[:60] + "...")
                    if len(proposal.rationale) > 60
                    else proposal.rationale,
                )
            console.print(table)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subcommand: list
# ---------------------------------------------------------------------------


@feedback_app.command("list")
def feedback_list(
    check: str = typer.Option(
        None,
        "--check",
        "-c",
        help="Filter by check ID",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter by ticker",
    ),
) -> None:
    """List feedback entries with optional filters."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback import get_feedback_for_check

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)  # Ensure tables exist

    try:
        entries: list[Any] = []

        if check:
            entries = get_feedback_for_check(conn, check)
        else:
            # Query all, optionally filtered by ticker
            query = """SELECT feedback_id, ticker, signal_id, run_id,
                              feedback_type, direction, note, reviewer,
                              status, created_at
                       FROM brain_feedback"""
            params: list[str] = []
            if ticker:
                query += " WHERE ticker = ?"
                params.append(ticker.upper())
            query += " ORDER BY created_at DESC"

            from do_uw.knowledge.feedback import row_to_feedback_entry

            rows = conn.execute(query, params).fetchall()
            entries = [row_to_feedback_entry(row) for row in rows]

        if not entries:
            filter_desc = ""
            if check:
                filter_desc += f" for check '{check}'"
            if ticker:
                filter_desc += f" for ticker '{ticker}'"
            console.print(
                f"[dim]No feedback entries found{filter_desc}.[/dim]"
            )
            return

        table = Table(title=f"Feedback Entries ({len(entries)} found)")
        table.add_column("ID", width=5, justify="right")
        table.add_column("Ticker", width=8)
        table.add_column("Check", min_width=15)
        table.add_column("Type", width=18)
        table.add_column("Direction", width=16)
        table.add_column("Status", width=10)
        table.add_column("Reviewer", width=12)
        table.add_column("Note", min_width=20)

        for entry in entries:
            table.add_row(
                str(entry.feedback_id or ""),
                entry.ticker or "",
                entry.signal_id or "",
                entry.feedback_type,
                entry.direction or "",
                entry.status,
                entry.reviewer,
                (entry.note[:60] + "...") if len(entry.note) > 60 else entry.note,
            )

        console.print(table)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subcommand: capture (interactive reaction capture)
# ---------------------------------------------------------------------------


@feedback_app.command("capture")
def feedback_capture(
    ticker: str = typer.Argument(help="Stock ticker to review (e.g., AAPL, WWD)"),
    general: bool = typer.Option(
        False,
        "--general",
        help="Record systemic feedback not tied to a specific signal",
    ),
    reviewer: str = typer.Option(
        "underwriter",
        "--reviewer",
        "-r",
        help="Reviewer name for attribution",
    ),
    all_signals: bool = typer.Option(
        False,
        "--all",
        help="Show all evaluated signals, not just triggered",
    ),
) -> None:
    """Capture structured feedback on triggered signals for a ticker.

    Shows all triggered signals with full context (description, value,
    threshold, evidence). Select signals by number, then record your
    reaction (Agree/Disagree/Adjust Severity) with a required rationale.
    """
    from rich.panel import Panel

    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback import record_reaction
    from do_uw.knowledge.feedback_models import FeedbackReaction, ReactionType

    ticker_upper = ticker.upper()

    # Handle --general flag: systemic feedback not tied to signals
    if general:
        note = typer.prompt("Systemic observation (required)")
        if not note.strip():
            console.print("[red]Rationale cannot be empty.[/red]")
            raise typer.Exit(code=1)
        # Record as legacy feedback with ACCURACY type
        from do_uw.knowledge.feedback import record_feedback
        from do_uw.knowledge.feedback_models import FeedbackEntry

        db_path = get_brain_db_path()
        conn = connect_brain_db(db_path)
        create_schema(conn)
        try:
            entry = FeedbackEntry(
                ticker=ticker_upper,
                feedback_type="ACCURACY",
                note=note,
                reviewer=reviewer,
            )
            fid = record_feedback(conn, entry)
            console.print(f"[green]General feedback recorded (ID: {fid})[/green]")
        finally:
            conn.close()
        return

    # Load triggered signals
    triggered, run_id = _load_triggered_signals(ticker_upper)

    if not triggered:
        console.print(
            f"[yellow]No triggered signals found for {ticker_upper}. "
            f"Run the pipeline first: do-uw analyze {ticker_upper}[/yellow]"
        )
        raise typer.Exit(code=1)

    # Display triggered signals table
    table = Table(title=f"Triggered Signals for {ticker_upper} ({len(triggered)} found)")
    table.add_column("#", width=4, justify="right")
    table.add_column("Signal ID", min_width=25)
    table.add_column("Name", min_width=20)
    table.add_column("Value", width=12)
    table.add_column("Level", width=8)
    table.add_column("Evidence", min_width=30)

    sig_list = list(triggered.items())
    for i, (sig_id, result) in enumerate(sig_list, 1):
        level = result.get("threshold_level", "")
        level_styled = (
            f"[red]{level}[/red]" if level == "red"
            else f"[yellow]{level}[/yellow]" if level == "yellow"
            else level
        )
        table.add_row(
            str(i),
            sig_id,
            result.get("check_name", result.get("signal_name", "")),
            str(result.get("value", "N/A")),
            level_styled,
            (result.get("evidence", "") or "")[:60],
        )

    console.print(table)

    # Prompt for selection
    selection = typer.prompt(
        "\nSelect signal(s) to react to (e.g., 1,3,5 or 'all' or 'q' to quit)"
    )

    if selection.strip().lower() == "q":
        console.print("[dim]Cancelled.[/dim]")
        return

    # Parse selection
    if selection.strip().lower() == "all":
        selected_indices = list(range(len(sig_list)))
    else:
        try:
            selected_indices = [
                int(x.strip()) - 1
                for x in selection.split(",")
                if x.strip().isdigit()
            ]
            # Validate range
            selected_indices = [
                i for i in selected_indices
                if 0 <= i < len(sig_list)
            ]
        except ValueError:
            console.print("[red]Invalid selection. Use numbers separated by commas.[/red]")
            raise typer.Exit(code=1)

    if not selected_indices:
        console.print("[yellow]No valid signals selected.[/yellow]")
        return

    # Connect to DB for recording
    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        recorded = 0
        for idx in selected_indices:
            sig_id, result = sig_list[idx]

            # Show full detail panel
            detail_text = (
                f"[bold]{result.get('check_name', result.get('signal_name', sig_id))}[/bold]\n"
                f"Signal: {sig_id}\n"
                f"Value: {result.get('value', 'N/A')}\n"
                f"Threshold Level: {result.get('threshold_level', 'N/A')}\n"
                f"Evidence: {result.get('evidence', 'N/A')}\n"
                f"Factors: {', '.join(result.get('factors', []))}"
            )
            console.print(Panel(detail_text, title=f"Signal Detail ({idx + 1}/{len(sig_list)})"))

            # Prompt for reaction type
            reaction_input = typer.prompt(
                "[A]gree / [D]isagree / adjust [S]everity / [skip]",
                default="skip",
            ).strip().lower()

            if reaction_input in ("skip", ""):
                console.print("[dim]Skipped.[/dim]")
                continue

            # Map input to ReactionType
            reaction_map: dict[str, ReactionType] = {
                "a": ReactionType.AGREE, "agree": ReactionType.AGREE,
                "d": ReactionType.DISAGREE, "disagree": ReactionType.DISAGREE,
                "s": ReactionType.ADJUST_SEVERITY, "severity": ReactionType.ADJUST_SEVERITY,
                "adjust": ReactionType.ADJUST_SEVERITY,
            }
            reaction_type = reaction_map.get(reaction_input)
            if reaction_type is None:
                console.print(f"[yellow]Unknown reaction '{reaction_input}', skipping.[/yellow]")
                continue

            # Prompt for severity target if ADJUST_SEVERITY
            severity_target = None
            if reaction_type == ReactionType.ADJUST_SEVERITY:
                severity_target = typer.prompt(
                    "Target severity level (e.g., MEDIUM, LOW, HIGH)"
                ).strip().upper()

            # Prompt for rationale (REQUIRED)
            rationale = typer.prompt("Rationale (required)")
            if not rationale.strip():
                console.print("[red]Rationale cannot be empty. Skipping this signal.[/red]")
                continue

            # Record reaction
            reaction = FeedbackReaction(
                ticker=ticker_upper,
                signal_id=sig_id,
                run_id=run_id,
                reaction_type=reaction_type,
                severity_target=severity_target,
                rationale=rationale.strip(),
                reviewer=reviewer,
            )
            fid = record_reaction(conn, reaction)
            console.print(
                f"[green]  Recorded {reaction_type.value} reaction (ID: {fid})[/green]"
            )
            recorded += 1

        console.print(
            f"\n[bold green]{recorded} reaction(s) recorded for {ticker_upper}.[/bold green]"
        )
        if recorded > 0:
            console.print(
                "[dim]Run 'do-uw feedback process' to generate calibration proposals.[/dim]"
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subcommand: export (export review file for offline editing)
# ---------------------------------------------------------------------------


@feedback_app.command("export")
def feedback_export(
    ticker: str = typer.Argument(help="Stock ticker to export review for"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: output/{TICKER}_review.json)",
    ),
) -> None:
    """Export triggered signals as a review file for offline editing."""
    from do_uw.knowledge.feedback_export import export_review_file

    ticker_upper = ticker.upper()
    triggered, run_id = _load_triggered_signals(ticker_upper)

    if not triggered:
        console.print(
            f"[yellow]No triggered signals found for {ticker_upper}.[/yellow]"
        )
        raise typer.Exit(code=1)

    out_path = Path(output) if output else Path(f"output/{ticker_upper}_review.json")
    export_review_file(ticker_upper, triggered, out_path, run_id)
    console.print(
        f"[green]Exported {len(triggered)} triggered signals to {out_path}[/green]"
    )
    console.print("[dim]Edit the file, then import with: do-uw feedback import-file <file>[/dim]")


# ---------------------------------------------------------------------------
# Subcommand: import-file (import reactions from exported review file)
# ---------------------------------------------------------------------------


@feedback_app.command("import-file")
def feedback_import(
    file_path: str = typer.Argument(help="Path to the review JSON file"),
    reviewer: str = typer.Option(
        "underwriter",
        "--reviewer",
        "-r",
        help="Reviewer name for attribution",
    ),
) -> None:
    """Import reactions from an exported review file."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback_export import import_review_file

    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(code=1)

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        imported, errors = import_review_file(conn, path, reviewer)

        if errors:
            console.print(f"\n[yellow]{len(errors)} issue(s):[/yellow]")
            for err in errors:
                console.print(f"  [yellow]{err}[/yellow]")

        console.print(f"\n[green]{imported} reaction(s) imported from {path}[/green]")

        if imported > 0:
            console.print(
                "[dim]Run 'do-uw feedback process' to generate calibration proposals.[/dim]"
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Import extension module to register process/show commands on feedback_app
# ---------------------------------------------------------------------------

import do_uw.cli_feedback_process as _cli_feedback_process  # noqa: F401, E402
