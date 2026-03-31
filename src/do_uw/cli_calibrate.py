# ruff: noqa: B008
"""CLI sub-app for check calibration and knowledge enrichment.

Provides the ``angry-dolphin calibrate`` command group with sub-commands:
run, report, enrich, preview, apply, show. The preview/apply/show commands
implement the human-in-the-loop calibration workflow with impact simulation
and git audit trail.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from do_uw.calibration.config import get_calibration_tickers
from do_uw.calibration.runner import CalibrationReport, CalibrationRunner

calibrate_app = typer.Typer(
    name="calibrate",
    help="Check calibration and knowledge enrichment",
)
console = Console()


@calibrate_app.command("run")
def run(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
    fresh: bool = typer.Option(
        True,
        "--fresh/--no-fresh",
        help="Clear cache before each ticker (default: fresh)",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Disable LLM extraction (regex-only mode)",
    ),
    top_n: int = typer.Option(
        20,
        "--top-n",
        help="Number of top-impact checks for ground truth",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Filter tickers by category (e.g., known_outcome)",
    ),
) -> None:
    """Run calibration across the 12 calibration tickers."""
    tickers = get_calibration_tickers(category)

    if not tickers:
        console.print("[bold red]No calibration tickers found.[/bold red]")
        raise typer.Exit(code=1)

    console.print(
        f"\n[bold]Angry Dolphin Calibration Run "
        f"-- {len(tickers)} tickers[/bold]"
    )
    console.print()
    for t in tickers:
        tier = t["expected_tier"]
        console.print(f"  [dim]{t['ticker']}[/dim]  {tier}")
    console.print()

    runner = CalibrationRunner(
        tickers=tickers,
        output_dir=output,
        fresh=fresh,
        use_llm=not no_llm,
        top_n=top_n,
    )
    report = runner.run()

    # Display summary table.
    _print_summary(report)

    # Save report JSON.
    report_dir = output / "calibration"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "calibration_report.json"
    report_path.write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    console.print(f"\n[dim]Report saved to {report_path}[/dim]")


@calibrate_app.command("report")
def report(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory containing calibration results",
    ),
    anomalies_only: bool = typer.Option(
        False,
        "--anomalies-only/--all",
        help="Show only anomalies (tier mismatches, 0/100%% fire rate)",
    ),
) -> None:
    """Generate calibration report from existing results."""
    _ = anomalies_only
    report_path = output / "calibration" / "calibration_report.json"
    if not report_path.exists():
        console.print(
            "[bold red]No calibration report found.[/bold red] "
            f"Expected at: {report_path}"
        )
        console.print("[dim]Run 'angry-dolphin calibrate run' first.[/dim]")
        raise typer.Exit(code=1)

    console.print(
        "Report generation not yet implemented. "
        "Run 24-03 plan."
    )


@calibrate_app.command("enrich")
def enrich(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory containing calibration results",
    ),
    auto_promote: bool = typer.Option(
        False,
        "--auto-promote",
        help="Auto-promote patterns confirmed across N tickers",
    ),
) -> None:
    """Enrich knowledge store from calibration findings."""
    _ = (output, auto_promote)
    console.print(
        "Enrichment not yet implemented. "
        "Run 24-04 plan."
    )


def _print_summary(report: CalibrationReport) -> None:
    """Display calibration summary as a Rich table.

    Args:
        report: Completed calibration report.
    """
    table = Table(
        title="Calibration Results",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Ticker", min_width=6)
    table.add_column("Expected", min_width=12)
    table.add_column("Actual", min_width=10)
    table.add_column("Score", width=6, justify="right")
    table.add_column("Checks", width=6, justify="right")
    table.add_column("Time", width=8, justify="right")
    table.add_column("Match", width=5, justify="center")

    for ticker_sym, result in report.tickers.items():
        if result.error is not None:
            table.add_row(
                ticker_sym,
                result.expected_tier,
                "[red]ERROR[/red]",
                "--",
                "--",
                f"{result.duration_seconds:.0f}s",
                "[red]X[/red]",
            )
            continue

        actual = result.actual_tier or "N/A"
        score = (
            f"{result.quality_score:.0f}"
            if result.quality_score is not None
            else "N/A"
        )
        checks = str(len(result.signal_results))
        time_str = f"{result.duration_seconds:.0f}s"

        # Check if actual tier is within expected range.
        expected_tiers = result.expected_tier.split("/")
        match = actual in expected_tiers
        match_str = "[green]Y[/green]" if match else "[red]N[/red]"

        table.add_row(
            ticker_sym, result.expected_tier, actual, score,
            checks, time_str, match_str,
        )

    console.print(table)

    # Summary line.
    total = len(report.tickers)
    errors = len(report.errors)
    successes = total - errors
    console.print(
        f"\n[dim]{successes}/{total} completed, "
        f"{errors} errors, "
        f"{report.total_duration:.0f}s total[/dim]"
    )

    # Load report for JSON serialization check.
    if report.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for err in report.errors:
            console.print(f"  [red]{err}[/red]")


# ---------------------------------------------------------------------------
# Preview: show pending proposals with impact simulation
# ---------------------------------------------------------------------------


@calibrate_app.command("preview")
def preview(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Directory containing state files for impact simulation",
    ),
) -> None:
    """Preview pending calibration proposals with impact simulation."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.calibrate import preview_calibration

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        result = preview_calibration(conn, output)

        if not result.proposals:
            console.print(
                "[dim]No pending proposals. Use `do-uw ingest` or "
                "`do-uw feedback` to create proposals.[/dim]"
            )
            return

        # Pending Proposals table
        proposals_table = Table(
            title="Pending Proposals",
            show_header=True,
            header_style="bold",
        )
        proposals_table.add_column("ID", width=5, justify="right")
        proposals_table.add_column("Source", width=12)
        proposals_table.add_column("Type", width=18)
        proposals_table.add_column("Check", min_width=20)
        proposals_table.add_column("Rationale", min_width=30)

        for p in result.proposals:
            rationale_display = (
                (p.rationale[:50] + "...") if len(p.rationale) > 50
                else p.rationale
            )
            proposals_table.add_row(
                str(p.proposal_id or ""),
                p.source_type,
                p.proposal_type,
                p.signal_id or "",
                rationale_display,
            )

        console.print(proposals_table)

        # Proposed Changes table
        if result.changes:
            console.print()
            changes_table = Table(
                title="Proposed Changes",
                show_header=True,
                header_style="bold",
            )
            changes_table.add_column("Proposal", width=8, justify="right")
            changes_table.add_column("Field", min_width=15)
            changes_table.add_column("Old Value", min_width=15)
            changes_table.add_column("New Value", min_width=15)

            for c in result.changes:
                changes_table.add_row(
                    str(c.get("proposal_id", "")),
                    str(c.get("field", "")),
                    str(c.get("old_value", "")),
                    str(c.get("new_value", "")),
                )

            console.print(changes_table)

        # Impact Simulation table
        if result.impact:
            console.print()
            impact_table = Table(
                title="Impact Simulation",
                show_header=True,
                header_style="bold",
            )
            impact_table.add_column("Ticker", width=8)
            impact_table.add_column("Check", min_width=20)
            impact_table.add_column("Current", width=12)
            impact_table.add_column("Proposed", width=12)
            impact_table.add_column("Changed?", width=8, justify="center")

            for i in result.impact:
                impact_table.add_row(
                    i.get("ticker", ""),
                    i.get("signal_id", ""),
                    i.get("current_status", ""),
                    i.get("proposed_status", ""),
                    "[yellow]YES[/yellow]",
                )

            console.print(impact_table)

        # Summary line
        n_proposals = len(result.proposals)
        n_changes = len(result.impact)
        n_companies = len({i.get("ticker", "") for i in result.impact})
        console.print(
            f"\n[dim]{n_proposals} proposals, "
            f"{n_changes} checks would change across "
            f"{n_companies} companies "
            f"({result.state_files_tested} state files tested)[/dim]"
        )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Apply: commit approved proposals with git audit trail
# ---------------------------------------------------------------------------


@calibrate_app.command("apply")
def apply(
    proposal: list[int] | None = typer.Option(
        None,
        "--proposal",
        "-p",
        help="Specific proposal IDs to apply (default: all pending)",
    ),
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Directory containing state files for preview",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Apply calibration proposals with git audit trail."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.calibrate import apply_calibration, preview_calibration

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        # Show preview first
        preview_result = preview_calibration(conn, output)

        if not preview_result.proposals:
            console.print(
                "[dim]No pending proposals to apply. Use `do-uw ingest` or "
                "`do-uw feedback` to create proposals.[/dim]"
            )
            return

        # Display preview summary
        n_proposals = len(preview_result.proposals)
        console.print(
            f"\n[bold]{n_proposals} pending proposal(s) to apply:[/bold]"
        )
        for p in preview_result.proposals:
            console.print(
                f"  [{p.proposal_type}] {p.signal_id}: {p.rationale[:80]}"
            )

        if preview_result.impact:
            console.print(
                f"\n[yellow]{len(preview_result.impact)} check(s) would change "
                f"across {len({i.get('ticker', '') for i in preview_result.impact})} "
                f"companies[/yellow]"
            )

        # Confirmation
        if not yes:
            typer.confirm(
                f"Apply {n_proposals} proposals?",
                default=False,
                abort=True,
            )

        # Apply
        result = apply_calibration(conn, proposal)

        console.print(
            f"\n[green]Applied {result.proposals_applied} proposals, "
            f"modified {len(result.checks_modified)} checks[/green]"
        )

        if result.commit_hash:
            console.print(f"[green]Git commit: {result.commit_hash}[/green]")
        else:
            console.print(
                "[yellow]Git commit failed "
                "(changes applied but not committed)[/yellow]"
            )

        if result.feedback_resolved > 0:
            console.print(
                f"[dim]Resolved {result.feedback_resolved} feedback entries[/dim]"
            )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Show: calibration history via git log
# ---------------------------------------------------------------------------


@calibrate_app.command("show")
def show(
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Number of recent entries to show",
    ),
) -> None:
    """Show calibration history from git log."""
    try:
        result = subprocess.run(
            [
                "git", "log", "--oneline", f"-{limit}",
                "--", "src/do_uw/brain/signals.json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if not lines:
            console.print("[dim]No calibration history found.[/dim]")
            return

        table = Table(
            title="Calibration History",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Hash", width=10)
        table.add_column("Message", min_width=40)

        for line in lines:
            parts = line.split(" ", 1)
            commit_hash = parts[0] if parts else ""
            message = parts[1] if len(parts) > 1 else ""
            table.add_row(commit_hash, message)

        console.print(table)

    except FileNotFoundError:
        console.print("[red]git not available[/red]")
    except subprocess.CalledProcessError:
        console.print("[red]Failed to read git log[/red]")
