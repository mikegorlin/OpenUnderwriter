"""CLI sub-commands for knowledge governance operations.

Provides commands for knowledge governance including:
- `do-uw knowledge govern review` -- review checks by lifecycle state
- `do-uw knowledge govern promote` -- promote/demote check lifecycle
- `do-uw knowledge govern history` -- view check modification history
- `do-uw knowledge govern drift` -- view calibration drift
- `do-uw knowledge govern deprecation-log` -- view deprecated checks

Registered as a Typer sub-app on knowledge_app in cli_knowledge.py.

KnowledgeStore reads removed in Phase 45 -- commands now read from
brain.duckdb where equivalent data exists, or return empty with a
TODO marker where no equivalent exists yet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

governance_app = typer.Typer(
    name="govern",
    help="Knowledge governance: review, promote, history, drift",
    no_args_is_help=True,
)
console = Console()

_VALID_STATUSES = ("INCUBATING", "DEVELOPING", "ACTIVE", "DEPRECATED")


@governance_app.command("review")
def review(
    status: str = typer.Option(
        "INCUBATING",
        "--status",
        "-s",
        help="Filter by status (INCUBATING, DEVELOPING, ACTIVE, DEPRECATED)",
    ),
    limit: int = typer.Option(
        50, "--limit", "-n", help="Maximum checks to display"
    ),
) -> None:
    """Review checks filtered by lifecycle state from brain.duckdb.

    Lists checks matching the specified lifecycle state with signal_id,
    name, section, and content_type columns.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    status_upper = status.upper()
    if status_upper not in _VALID_STATUSES:
        console.print(
            f"[red]Invalid status: {status}[/red]\n"
            f"[dim]Valid: {', '.join(_VALID_STATUSES)}[/dim]"
        )
        raise typer.Exit(code=1)

    # Map old knowledge.db status names to brain.duckdb lifecycle_state names
    state_map = {
        "INCUBATING": "INCUBATING",
        "DEVELOPING": "DEVELOPING",
        "ACTIVE": "ACTIVE",
        "DEPRECATED": "RETIRED",  # brain.duckdb uses RETIRED for deprecated
    }
    brain_state = state_map.get(status_upper, status_upper)

    conn = connect_brain_db()
    try:
        rows = conn.execute(
            "SELECT signal_id, name, lifecycle_state, report_section, content_type "
            "FROM brain_signals_current "
            "WHERE lifecycle_state = ? "
            "ORDER BY signal_id "
            "LIMIT ?",
            [brain_state, limit],
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        console.print(
            f"[dim]No checks found with lifecycle state {brain_state} "
            f"(queried as '{status_upper}' -> '{brain_state}').[/dim]"
        )
        return

    table = Table(
        title=f"Checks -- {status_upper} ({len(rows)} results)"
    )
    table.add_column("Check ID", min_width=30)
    table.add_column("Name", min_width=30)
    table.add_column("State", width=12)
    table.add_column("Section", width=10)
    table.add_column("Content Type", width=18)
    for signal_id, name, state, section, ctype in rows:
        table.add_row(
            str(signal_id),
            str(name or "")[:60],
            str(state or ""),
            str(section or ""),
            str(ctype or ""),
        )
    console.print(table)


@governance_app.command("promote")
def promote(
    signal_id: str = typer.Argument(help="Check ID to transition"),
    to_status: str = typer.Argument(
        help="Target status (INCUBATING, DEVELOPING, ACTIVE, DEPRECATED)"
    ),
    reason: str = typer.Option(
        "", "--reason", "-r", help="Reason for transition (required for DEPRECATED)"
    ),
) -> None:
    """Promote or demote a check to a new lifecycle status.

    Note: Lifecycle transitions are managed via brain YAML files and
    'do-uw brain build'. Direct promotion via CLI is not yet
    supported in brain.duckdb.

    TODO(45): Port to brain.duckdb brain_changelog when brain YAML
    lifecycle management is implemented.
    """
    # TODO(45): promote command requires ORM lifecycle transitions against
    # knowledge.db. No brain.duckdb equivalent exists yet. When brain
    # lifecycle management is implemented, this will write to brain_changelog.
    console.print(
        "[yellow]Check promotion is not yet available via brain.duckdb.[/yellow]"
    )
    console.print(
        "[dim]To change a check's lifecycle state, update the YAML source file "
        "and run 'do-uw brain build' to rebuild brain.duckdb.[/dim]"
    )
    raise typer.Exit(code=1)


@governance_app.command("history")
def history(
    signal_id: str = typer.Argument(help="Check ID to view history for"),
    field_filter: str = typer.Option(
        "", "--field", "-f", help="Filter history by field name (e.g., status)"
    ),
) -> None:
    """View the modification history for a check from brain.duckdb.

    Shows changelog entries from brain_changelog for the specified check.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        # Get check info from brain_signals_current
        signal_row = conn.execute(
            "SELECT signal_id, name, lifecycle_state, version, created_at "
            "FROM brain_signals_current WHERE signal_id = ?",
            [signal_id],
        ).fetchone()

        if signal_row is None:
            console.print(
                f"[red]Check not found in brain.duckdb: {signal_id}[/red]"
            )
            raise typer.Exit(code=1)

        cid, name, state, version, created_at = signal_row

        # Get changelog entries
        changelog_rows = conn.execute(
            "SELECT changelog_id, old_version, new_version, change_type, "
            "  change_description, changed_by, changed_at, change_reason "
            "FROM brain_changelog "
            "WHERE signal_id = ? "
            "ORDER BY changed_at DESC",
            [signal_id],
        ).fetchall()
    finally:
        conn.close()

    # Header
    console.print(f"\n[bold]Check: {name}[/bold]")
    console.print(f"  ID: {cid}")
    console.print(f"  Lifecycle State: {state}")
    console.print(f"  Version: {version}")
    console.print(f"  Created: {created_at}")
    console.print(
        f"  Total changelog entries: {len(changelog_rows)}\n"
    )

    if field_filter:
        changelog_rows = [
            r for r in changelog_rows
            if field_filter.lower() in str(r[3]).lower()
            or field_filter.lower() in str(r[4]).lower()
        ]

    if not changelog_rows:
        console.print("[dim]No history entries found.[/dim]")
        return

    table = Table(title="Modification History (brain_changelog)")
    table.add_column("ID", width=6, justify="right")
    table.add_column("Old Ver", width=7, justify="right")
    table.add_column("New Ver", width=7, justify="right")
    table.add_column("Type", width=12)
    table.add_column("Description", min_width=20)
    table.add_column("Changed By", width=12)
    table.add_column("Date", width=16)
    table.add_column("Reason", min_width=15)
    for row in changelog_rows:
        chg_id, old_ver, new_ver, chg_type, desc, changed_by, chg_at, reason = row
        table.add_row(
            str(chg_id or ""),
            str(old_ver or ""),
            str(new_ver or ""),
            str(chg_type or ""),
            str(desc or "")[:40],
            str(changed_by or ""),
            str(chg_at or "")[:16],
            str(reason or ""),
        )
    console.print(table)


@governance_app.command("drift")
def drift() -> None:
    """Compare scoring config (scoring.json) with brain.duckdb scoring factors.

    For each scoring factor, shows max_points and weight from the
    flat-file config alongside the brain.duckdb values. Flags differences
    as DRIFT.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    scoring_path = Path(__file__).parent / "brain" / "config" / "scoring.json"
    if not scoring_path.exists():
        console.print(
            f"[red]Scoring config not found: {scoring_path}[/red]"
        )
        raise typer.Exit(code=1)

    with open(scoring_path) as f:
        config_data: dict[str, Any] = json.load(f)

    config_factors: dict[str, Any] = config_data.get("factors", {})

    conn = connect_brain_db()
    try:
        # Get scoring factors from brain.duckdb
        factor_rows = conn.execute(
            "SELECT factor_id, name, max_points, weight_pct, rules "
            "FROM brain_scoring_factors_current "
            "ORDER BY factor_id"
        ).fetchall()
    finally:
        conn.close()

    # Aggregate brain.duckdb factors by factor_id
    brain_by_factor: dict[str, dict[str, Any]] = {}
    for factor_id, name, max_points, weight_pct, rules_json in factor_rows:
        fid = str(factor_id)
        brain_by_factor[fid] = {
            "max_points": float(max_points or 0),
            "weight_pct": float(weight_pct or 0),
        }

    table = Table(title="Calibration Drift Report (brain.duckdb vs scoring.json)")
    table.add_column("Factor ID", width=8)
    table.add_column("Name", min_width=20)
    table.add_column("Config Max Pts", width=14, justify="right")
    table.add_column("Brain Max Pts", width=13, justify="right")
    table.add_column("Config Weight%", width=14, justify="right")
    table.add_column("Status", width=8)

    has_drift = False
    for _key, factor_cfg in sorted(config_factors.items()):
        fid = str(factor_cfg.get("factor_id", ""))
        name = str(factor_cfg.get("name", ""))
        cfg_max = float(factor_cfg.get("max_points", 0))
        cfg_weight = float(factor_cfg.get("weight_pct", 0))

        brain_info = brain_by_factor.get(fid, {})
        brain_max = float(brain_info.get("max_points", 0))

        points_match = abs(cfg_max - brain_max) < 0.01
        status = "OK" if points_match else "DRIFT"
        style = "green" if points_match else "yellow bold"

        if not points_match:
            has_drift = True

        table.add_row(
            fid,
            name[:30],
            f"{cfg_max:.0f}",
            f"{brain_max:.0f}" if brain_info else "[dim]--[/dim]",
            f"{cfg_weight:.0f}",
            f"[{style}]{status}[/{style}]",
        )

    console.print(table)

    if has_drift:
        console.print(
            "\n[yellow]Drift detected -- config and brain.duckdb are out of sync.[/yellow]"
        )
    else:
        console.print(
            "\n[green]No drift -- config and brain.duckdb are in sync.[/green]"
        )


@governance_app.command("deprecation-log")
def deprecation_log() -> None:
    """View a log of all retired/deprecated signals from brain.duckdb.

    Shows each retired check from brain_signals_current with its
    lifecycle state and creation date.
    """
    from do_uw.brain.brain_schema import connect_brain_db

    conn = connect_brain_db()
    try:
        rows = conn.execute(
            "SELECT signal_id, name, version, created_at, retired_at, retired_reason "
            "FROM brain_signals_current "
            "WHERE lifecycle_state IN ('RETIRED', 'INACTIVE') "
            "ORDER BY retired_at DESC NULLS LAST, signal_id"
        ).fetchall()

        # Also check changelog for any retirement events
        changelog_rows = conn.execute(
            "SELECT signal_id, changed_at, changed_by, change_reason "
            "FROM brain_changelog "
            "WHERE change_type IN ('RETIRE', 'DEPRECATED', 'INACTIVATE') "
            "ORDER BY changed_at DESC"
        ).fetchall()
    finally:
        conn.close()

    if not rows and not changelog_rows:
        console.print(
            "[dim]No retired/deprecated checks found in brain.duckdb.[/dim]"
        )
        return

    if rows:
        table = Table(
            title=f"Retired/Deprecated Checks ({len(rows)} checks)"
        )
        table.add_column("Check ID", min_width=30)
        table.add_column("Name", min_width=25)
        table.add_column("Version", width=7, justify="right")
        table.add_column("Retired At", width=16)
        table.add_column("Reason", min_width=20)
        for signal_id, name, version, created_at, retired_at, retired_reason in rows:
            table.add_row(
                str(signal_id),
                str(name or "")[:40],
                str(version or ""),
                str(retired_at or "")[:16],
                str(retired_reason or "[dim]none[/dim]"),
            )
        console.print(table)

    if changelog_rows:
        table2 = Table(
            title=f"Retirement Changelog Events ({len(changelog_rows)} entries)"
        )
        table2.add_column("Check ID", min_width=30)
        table2.add_column("Date", width=16)
        table2.add_column("Changed By", width=12)
        table2.add_column("Reason", min_width=20)
        for signal_id, changed_at, changed_by, reason in changelog_rows:
            table2.add_row(
                str(signal_id),
                str(changed_at or "")[:16],
                str(changed_by or ""),
                str(reason or ""),
            )
        console.print(table2)
