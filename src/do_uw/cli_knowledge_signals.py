"""CLI sub-commands for knowledge check analytics.

Split from cli_knowledge.py (Phase 45, 500-line rule).

Provides commands for check run statistics:
- `do-uw knowledge check-stats` -- per-check fire/skip rates
- `do-uw knowledge dead-checks` -- never-fire check detection

Reads from brain.duckdb (brain_signal_runs table).
KnowledgeStore reads removed in Phase 45.

Registered as commands within knowledge_app in cli_knowledge.py.
"""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

checks_console = Console()


def _get_check_stats_from_brain(
    signal_id: str | None = None,
    min_runs: int = 1,
) -> list[dict[str, Any]]:
    """Compute check fire/skip rates from brain.duckdb brain_signal_runs.

    Args:
        signal_id: Optional filter to a single check ID.
        min_runs: Minimum total runs to include a check.

    Returns:
        List of dicts with keys: signal_id, total_runs, fired,
        clear, skipped, info, fire_rate, skip_rate.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        if signal_id is not None:
            rows = conn.execute(
                "SELECT signal_id, status, COUNT(*) as cnt "
                "FROM brain_signal_runs "
                "WHERE is_backtest = FALSE AND signal_id = ? "
                "GROUP BY signal_id, status "
                "ORDER BY signal_id, status",
                [signal_id],
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT signal_id, status, COUNT(*) as cnt "
                "FROM brain_signal_runs "
                "WHERE is_backtest = FALSE "
                "GROUP BY signal_id, status "
                "ORDER BY signal_id, status"
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # Aggregate per signal_id
    agg: dict[str, dict[str, int]] = {}
    for cid, status, cnt in rows:
        if cid not in agg:
            agg[cid] = {
                "fired": 0,
                "clear": 0,
                "skipped": 0,
                "info": 0,
            }
        status_key = status.lower()
        if status_key == "triggered":
            agg[cid]["fired"] += cnt
        elif status_key in agg[cid]:
            agg[cid][status_key] += cnt

    results: list[dict[str, Any]] = []
    for cid, counts in sorted(agg.items()):
        total = (
            counts["fired"]
            + counts["clear"]
            + counts["skipped"]
            + counts["info"]
        )
        if total < min_runs:
            continue
        results.append({
            "signal_id": cid,
            "total_runs": total,
            "fired": counts["fired"],
            "clear": counts["clear"],
            "skipped": counts["skipped"],
            "info": counts["info"],
            "fire_rate": counts["fired"] / total if total else 0.0,
            "skip_rate": counts["skipped"] / total if total else 0.0,
        })
    return results


def check_stats(
    signal_id: str = typer.Option(
        None, "--check", "-c", help="Filter to a single check ID"
    ),
    min_runs: int = typer.Option(
        1, "--min-runs", help="Minimum runs to include"
    ),
    sort_by: str = typer.Option(
        "fire_rate",
        "--sort",
        help="Sort column: fire_rate, skip_rate, total_runs, signal_id",
    ),
) -> None:
    """Show fire rates, skip rates, and anomalies across pipeline runs.

    Displays per-check statistics computed from the brain_signal_runs
    table in brain.duckdb. Use --sort to order by different columns.
    """
    stats_list = _get_check_stats_from_brain(
        signal_id=signal_id, min_runs=min_runs
    )

    if not stats_list:
        checks_console.print(
            "[yellow]No check run data found.[/yellow]"
        )
        checks_console.print(
            "[dim]Run the pipeline to generate feedback data.[/dim]"
        )
        return

    # Sort
    reverse = sort_by != "signal_id"
    stats_list.sort(
        key=lambda s: s.get(sort_by, 0), reverse=reverse
    )

    checks_console.print(
        f"\n[bold]Check Stats[/bold] "
        f"({len(stats_list)} checks, min_runs={min_runs})\n"
    )

    table = Table()
    table.add_column("Check ID", min_width=20)
    table.add_column("Runs", justify="right")
    table.add_column("Fired", justify="right")
    table.add_column("Clear", justify="right")
    table.add_column("Skipped", justify="right")
    table.add_column("Info", justify="right")
    table.add_column("Fire Rate", justify="right")
    table.add_column("Skip Rate", justify="right")
    for s in stats_list:
        fire_style = (
            "red" if s["fire_rate"] > 0.5
            else "yellow" if s["fire_rate"] > 0
            else "dim"
        )
        skip_style = "yellow" if s["skip_rate"] > 0.5 else ""
        table.add_row(
            s["signal_id"],
            str(s["total_runs"]),
            str(s["fired"]),
            str(s["clear"]),
            str(s["skipped"]),
            str(s["info"]),
            f"[{fire_style}]{s['fire_rate']:.1%}[/{fire_style}]",
            f"[{skip_style}]{s['skip_rate']:.1%}[/{skip_style}]"
            if skip_style
            else f"{s['skip_rate']:.1%}",
        )
    checks_console.print(table)


def dead_checks(
    min_runs: int = typer.Option(
        3, "--min-runs", help="Minimum runs to consider"
    ),
) -> None:
    """Show checks that never fire (deprecation candidates).

    Lists checks evaluated across multiple pipeline runs but
    with a fire rate of 0%. These may need threshold recalibration
    or deprecation from the active check set.
    """
    all_stats = _get_check_stats_from_brain(min_runs=min_runs)
    dead = [s for s in all_stats if s["fire_rate"] == 0.0]

    if not dead:
        checks_console.print(
            "[green]No dead checks found "
            f"(min_runs={min_runs}).[/green]"
        )
        return

    checks_console.print(
        f"\n[bold]Dead Checks[/bold] "
        f"({len(dead)} checks, min_runs={min_runs})\n"
    )

    table = Table()
    table.add_column("Check ID", min_width=20)
    table.add_column("Runs", justify="right")
    table.add_column("Clear", justify="right")
    table.add_column("Skipped", justify="right")
    table.add_column("Info", justify="right")
    table.add_column("Skip Rate", justify="right")
    for s in dead:
        table.add_row(
            s["signal_id"],
            str(s["total_runs"]),
            str(s["clear"]),
            str(s["skipped"]),
            str(s["info"]),
            f"{s['skip_rate']:.1%}",
        )
    checks_console.print(table)
