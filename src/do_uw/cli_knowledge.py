"""CLI sub-commands for knowledge store operations.

Provides commands for knowledge store management including:
- `do-uw knowledge narratives <ticker>` -- risk narratives
- `do-uw knowledge learning-summary` -- analysis learning
- `do-uw knowledge migrate` -- JSON-to-store migration
- `do-uw knowledge stats` -- store statistics
- `do-uw knowledge ingest <filepath>` -- document ingestion
- `do-uw knowledge search <query>` -- full-text search
- `do-uw knowledge check-stats` -- per-check fire/skip rates (in cli_knowledge_signals.py)
- `do-uw knowledge dead-checks` -- never-fire check detection (in cli_knowledge_signals.py)
- `do-uw knowledge trace audit` -- traceability chain audit

Registered as a Typer sub-app in cli.py.
Check analytics commands are in cli_knowledge_signals.py (split for 500-line compliance).

KnowledgeStore reads removed in Phase 45 — commands now read from brain.duckdb
where equivalent data exists, or return empty with TODO where no equivalent exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from do_uw.cli_knowledge_governance import governance_app
from do_uw.cli_knowledge_signals import check_stats, dead_checks
from do_uw.cli_knowledge_traceability import traceability_app

knowledge_app = typer.Typer(
    name="knowledge",
    help="Knowledge store queries and analysis",
    no_args_is_help=True,
)
console = Console()

# Register sub-apps
knowledge_app.add_typer(governance_app, name="govern")
knowledge_app.add_typer(traceability_app, name="trace")

# Register check analytics commands from cli_knowledge_signals.py
knowledge_app.command("check-stats")(check_stats)
knowledge_app.command("dead-checks")(dead_checks)


@knowledge_app.command("narratives")
def narratives(
    ticker: str = typer.Argument(
        help="Ticker to compose narratives for"
    ),
) -> None:
    """Compose risk narratives for a ticker from latest analysis run.

    Loads the latest analysis run for the given ticker from
    brain.duckdb, extracts fired check IDs, and composes
    narrative risk stories.
    """
    # TODO(45): narrative composition reads analysis_run notes from knowledge.db
    # (Notes table). That data is not stored in brain.duckdb yet. Returning
    # empty until narrative data is migrated to brain.duckdb.
    ticker = ticker.upper()
    console.print(
        f"[yellow]No analysis run found for {ticker}[/yellow]"
    )
    console.print(
        "[dim]Narrative data not yet available in brain.duckdb. "
        "This command will be re-enabled once analysis outcomes are stored in brain.duckdb.[/dim]"
    )
    raise typer.Exit(code=1)


@knowledge_app.command("learning-summary")
def learning_summary() -> None:
    """Display learning summary from recorded analysis runs.

    Reads check run statistics from brain.duckdb.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        # Count distinct pipeline runs
        total_row = conn.execute(
            "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
            "WHERE is_backtest = FALSE"
        ).fetchone()
        total_runs = total_row[0] if total_row else 0

        if total_runs == 0:
            console.print("[yellow]No analysis runs recorded yet.[/yellow]")
            console.print(
                "[dim]Run 'do-uw run <ticker>' to generate analysis data.[/dim]"
            )
            return

        console.print(f"\n[bold]Learning Summary[/bold] ({total_runs} runs)\n")

        # Top fired signals from brain_signal_runs
        top_fired_rows = conn.execute(
            "SELECT signal_id, "
            "  SUM(CASE WHEN status = 'TRIGGERED' THEN 1 ELSE 0 END) as fired, "
            "  COUNT(*) as total "
            "FROM brain_signal_runs "
            "WHERE is_backtest = FALSE "
            "GROUP BY signal_id "
            "HAVING fired > 0 "
            "ORDER BY fired DESC "
            "LIMIT 10"
        ).fetchall()

        if top_fired_rows:
            table = Table(title="Top 10 Most-Fired Checks")
            table.add_column("Check ID")
            table.add_column("Times Fired", justify="right")
            table.add_column("Fire Rate", justify="right")
            for cid, fired, total in top_fired_rows:
                fire_rate = fired / total if total > 0 else 0.0
                table.add_row(
                    str(cid),
                    str(fired),
                    f"{fire_rate:.1%}",
                )
            console.print(table)

    finally:
        conn.close()


@knowledge_app.command("migrate")
def migrate() -> None:
    """Migrate brain/ JSON files to brain.duckdb.

    Directs the user to use 'do-uw brain build' which is the
    authoritative rebuild command for brain.duckdb.

    Note: This command previously migrated JSON to knowledge.db (SQLite).
    knowledge.db is superseded by brain.duckdb. Use 'do-uw brain build'
    to rebuild brain.duckdb from YAML source files.

    TODO(45): This command stub replaces the knowledge.db migration.
    Legacy KnowledgeStore migration removed in Phase 45.
    """
    console.print(
        "\n[bold]Brain knowledge is now managed via brain.duckdb[/bold]\n"
    )
    console.print(
        "Use the following command to rebuild brain.duckdb from YAML sources:"
    )
    console.print("  [bold]uv run do-uw brain build[/bold]")
    console.print(
        "\n[dim]knowledge.db (SQLite) is superseded by brain.duckdb.[/dim]"
    )


@knowledge_app.command("stats")
def stats() -> None:
    """Show knowledge store statistics from brain.duckdb.

    Displays check counts by lifecycle state and section from
    brain.duckdb (the authoritative check store).
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        # Total active checks
        total_row = conn.execute(
            "SELECT COUNT(DISTINCT signal_id) FROM brain_signals_active"
        ).fetchone()
        total = total_row[0] if total_row else 0

        # Total check run history
        history_row = conn.execute(
            "SELECT COUNT(*) FROM brain_signal_runs WHERE is_backtest = FALSE"
        ).fetchone()
        history = history_row[0] if history_row else 0

        console.print("\n[bold]Knowledge Store Statistics (brain.duckdb)[/bold]\n")
        console.print(f"Total active checks: {total}")
        console.print(f"Total check run records: {history}\n")

        # Checks by lifecycle state
        by_state_rows = conn.execute(
            "SELECT lifecycle_state, COUNT(DISTINCT signal_id) as cnt "
            "FROM brain_signals_current "
            "GROUP BY lifecycle_state "
            "ORDER BY cnt DESC"
        ).fetchall()

        if by_state_rows:
            table = Table(title="Checks by Lifecycle State")
            table.add_column("State")
            table.add_column("Count", justify="right")
            for state, count in by_state_rows:
                table.add_row(str(state), str(count))
            console.print(table)

        # Checks by report section
        by_section_rows = conn.execute(
            "SELECT report_section, COUNT(DISTINCT signal_id) as cnt "
            "FROM brain_signals_active "
            "GROUP BY report_section "
            "ORDER BY cnt DESC"
        ).fetchall()

        if by_section_rows:
            table = Table(title="Active Checks by Report Section")
            table.add_column("Section")
            table.add_column("Count", justify="right")
            for section, count in by_section_rows:
                table.add_row(str(section), str(count))
            console.print(table)

    finally:
        conn.close()


@knowledge_app.command("ingest")
def ingest(
    filepath: Path = typer.Argument(
        help="Path to a .txt or .md file to ingest"
    ),
    doc_type: str = typer.Option(
        "GENERAL",
        "--type",
        "-t",
        help=(
            "Document type: SHORT_SELLER_REPORT, CLAIMS_STUDY, "
            "UNDERWRITER_NOTES, INDUSTRY_ANALYSIS, "
            "REGULATORY_GUIDANCE, GENERAL"
        ),
    ),
) -> None:
    """Ingest an external document into the knowledge store.

    TODO(45): Document ingestion creates incubating checks and notes
    in knowledge.db (SQLite). This workflow is not yet available in
    brain.duckdb. Ingestion is disabled until the brain YAML workflow
    for incubating checks is implemented.
    """
    # TODO(45): ingest writes incubating Check and Note records to knowledge.db.
    # No brain.duckdb equivalent exists yet. Returns empty until brain ingestion
    # workflow is implemented (expected in a future architecture phase).
    console.print(
        "[yellow]Document ingestion is not yet available via brain.duckdb.[/yellow]"
    )
    console.print(
        "[dim]Incubating check creation will be re-enabled once the brain YAML "
        "ingestion workflow is implemented.[/dim]"
    )
    raise typer.Exit(code=1)


@knowledge_app.command("search")
def search(
    query: str = typer.Argument(help="Search query text"),
    limit: int = typer.Option(
        10, "--limit", "-n", help="Maximum results to return"
    ),
) -> None:
    """Search checks in brain.duckdb by name, ID, or section.

    Searches brain_signals_active using ILIKE (case-insensitive pattern
    match) on signal_id, name, and report_section.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT signal_id, name, lifecycle_state, report_section "
            "FROM brain_signals_active "
            "WHERE signal_id ILIKE ? OR name ILIKE ? OR report_section ILIKE ? "
            "ORDER BY signal_id "
            "LIMIT ?",
            [pattern, pattern, pattern, limit],
        ).fetchall()
    finally:
        conn.close()

    console.print(
        f"\n[bold]Search: '{query}'[/bold] (limit={limit})\n"
    )

    if rows:
        table = Table(title=f"Checks ({len(rows)} results)")
        table.add_column("ID", width=30)
        table.add_column("Name", min_width=30)
        table.add_column("State", width=12)
        table.add_column("Section", width=12)
        for signal_id, name, state, section in rows:
            table.add_row(
                str(signal_id),
                str(name or "")[:60],
                str(state or ""),
                str(section or ""),
            )
        console.print(table)
    else:
        console.print("[dim]No matching checks found.[/dim]")

    console.print()

    # TODO(45): note search not yet available in brain.duckdb.
    # Notes are stored in knowledge.db (SQLite). Returns empty until
    # notes are migrated to brain.duckdb.
    console.print(
        "[dim]Note search not available (notes not yet in brain.duckdb).[/dim]"
    )


def _get_check_stats_from_brain(
    signal_id: str | None = None,
    min_runs: int = 1,
) -> list[dict[str, Any]]:
    """Kept for backward compatibility — delegates to cli_knowledge_signals."""
    from do_uw.cli_knowledge_signals import _get_check_stats_from_brain as _impl
    return _impl(signal_id=signal_id, min_runs=min_runs)
