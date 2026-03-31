"""Brain explore CLI: risk framework queries with Rich output.

Sub-app registered on ``brain_app`` in cli_brain.py.
"""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

explore_app = typer.Typer(
    name="explore",
    help="Explore the D&O risk framework: perils, chains, coverage, effectiveness.",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COVERAGE_STYLE: dict[str, str] = {
    "GAP": "bold red",
    "THIN": "yellow",
    "ADEQUATE": "",
    "STRONG": "green",
}

_SIGNAL_STYLE: dict[str, str] = {
    "ALWAYS_FIRES": "bold red",
    "NEVER_FIRES": "yellow",
    "GOOD_DISCRIMINATION": "green",
    "MODERATE": "",
    "INSUFFICIENT_DATA": "dim",
}


def _get_conn() -> Any:
    """Get a DuckDB connection to brain.duckdb, or exit."""
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        console.print(
            "[yellow]brain.duckdb not found. Run the pipeline first.[/yellow]"
        )
        raise typer.Exit(code=1)
    return connect_brain_db(db_path)


def _style(mapping: dict[str, str], key: str) -> str:
    return mapping.get(key, "")


# ---------------------------------------------------------------------------
# 1. explore framework — overview of the risk model
# ---------------------------------------------------------------------------


@explore_app.command("framework")
def framework() -> None:
    """Show the risk model: layers, pillars, factor dimensions."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT entity_type, entity_id, legacy_id, name, description,
                      sort_order
               FROM brain_risk_framework
               ORDER BY entity_type, sort_order, entity_id"""
        ).fetchall()

        if not rows:
            console.print(
                "[yellow]No framework data. Run 'do-uw brain build'.[/yellow]"
            )
            return

        # Group by entity_type
        groups: dict[str, list[tuple[Any, ...]]] = {}
        for r in rows:
            groups.setdefault(r[0], []).append(r)

        console.print("\n[bold]D&O Underwriting Risk Framework[/bold]\n")

        # Pillars
        if "pillar" in groups:
            table = Table(title="Pillars (Underwriting Questions)")
            table.add_column("#", width=3, justify="right")
            table.add_column("ID", width=12)
            table.add_column("Legacy", width=16)
            table.add_column("Name", min_width=22)
            table.add_column("Description", min_width=30)
            for r in groups["pillar"]:
                table.add_row(
                    str(r[5] or ""),
                    r[1],
                    r[2] or "-",
                    r[3],
                    (r[4] or "")[:60],
                )
            console.print(table)

        # Layers
        if "layer" in groups:
            table = Table(title="Risk Framework Layers")
            table.add_column("ID", width=18)
            table.add_column("Legacy", width=20)
            table.add_column("Name", min_width=18)
            table.add_column("Description", min_width=35)
            for r in groups["layer"]:
                table.add_row(r[1], r[2] or "-", r[3], (r[4] or "")[:60])
            console.print(table)

        # Factor dimensions
        if "factor_dimension" in groups:
            table = Table(title="Factor Dimensions (NERA LEAD)")
            table.add_column("ID", width=5)
            table.add_column("Name", min_width=25)
            table.add_column("Description", min_width=40)
            for r in groups["factor_dimension"]:
                table.add_row(r[1], r[3], (r[4] or "")[:60])
            console.print(table)

        # Perils summary
        peril_rows = conn.execute(
            """SELECT peril_id, name, frequency, severity,
                      len(haz_codes) as haz_count
               FROM brain_perils ORDER BY peril_id"""
        ).fetchall()
        if peril_rows:
            table = Table(title="D&O Claim Perils")
            table.add_column("Peril", width=20)
            table.add_column("Name", min_width=22)
            table.add_column("Frequency", width=14)
            table.add_column("Severity", width=16)
            table.add_column("HAZ Codes", justify="right", width=10)
            for r in peril_rows:
                table.add_row(r[0], r[1], r[2], r[3], str(r[4]))
            console.print(table)

        # Chain count
        chain_count = conn.execute(
            "SELECT COUNT(*) FROM brain_causal_chains"
        ).fetchone()[0]
        console.print(
            f"\nCausal chains defined: [bold]{chain_count}[/bold]"
        )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. explore checks — filter by peril, layer, or pillar
# ---------------------------------------------------------------------------


@explore_app.command("signals")
def checks(
    peril: str = typer.Option("", "--peril", "-p", help="Filter by peril_id"),
    layer: str = typer.Option("", "--layer", "-l", help="Filter by risk_framework_layer"),
    pillar: str = typer.Option("", "--pillar", help="Filter by pillar"),
    limit: int = typer.Option(50, "--limit", "-n", help="Max rows"),
) -> None:
    """List active checks filtered by peril, layer, or pillar."""
    conn = _get_conn()
    try:
        conditions: list[str] = []
        if peril:
            conditions.append(f"peril_id = '{peril.upper()}'")
        if layer:
            conditions.append(f"risk_framework_layer = '{layer}'")
        if pillar:
            conditions.append(f"pillar = '{pillar.upper()}'")

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""SELECT signal_id, name, risk_framework_layer, pillar,
                           peril_id, content_type
                    FROM brain_signals_active{where}
                    ORDER BY signal_id LIMIT {limit}"""

        rows = conn.execute(query).fetchall()

        title_parts = ["Active Checks"]
        if peril:
            title_parts.append(f"peril={peril.upper()}")
        if layer:
            title_parts.append(f"layer={layer}")
        if pillar:
            title_parts.append(f"pillar={pillar.upper()}")

        console.print(f"\n[bold]{' | '.join(title_parts)}[/bold]")
        console.print(f"[dim]Showing {len(rows)} checks[/dim]\n")

        if not rows:
            console.print("[dim]No checks match the given filters.[/dim]")
            return

        table = Table()
        table.add_column("Check ID", min_width=28)
        table.add_column("Name", min_width=25)
        table.add_column("Layer", width=16)
        table.add_column("Pillar", width=12)
        table.add_column("Peril", width=18)
        table.add_column("Type", width=18)

        for r in rows:
            table.add_row(
                r[0],
                (r[1] or "")[:30],
                r[2] or "-",
                r[3] or "-",
                r[4] or "-",
                r[5] or "-",
            )
        console.print(table)

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. explore chain — single chain detail
# ---------------------------------------------------------------------------


@explore_app.command("chain")
def chain(
    chain_id: str = typer.Argument(help="Chain ID (e.g., stock_drop_to_sca)"),
) -> None:
    """Show full detail for a single causal chain."""
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT chain_id, name, peril_id, description,
                      trigger_signals, amplifier_signals,
                      mitigator_signals, evidence_signals,
                      frequency_factors, severity_factors,
                      patterns, red_flags,
                      historical_filing_rate, median_severity_usd
               FROM brain_causal_chains WHERE chain_id = ?""",
            [chain_id],
        ).fetchone()

        if not row:
            console.print(f"[red]Chain '{chain_id}' not found.[/red]")
            # List available chains
            available = conn.execute(
                "SELECT chain_id, name FROM brain_causal_chains ORDER BY chain_id"
            ).fetchall()
            if available:
                console.print("\n[dim]Available chains:[/dim]")
                for cid, cname in available:
                    console.print(f"  {cid} — {cname}")
            raise typer.Exit(code=1)

        console.print()
        console.print(Panel(
            f"[bold]{row[1]}[/bold]\n\n"
            f"Peril: [cyan]{row[2]}[/cyan]\n\n"
            f"{(row[3] or '').strip()}",
            title=f"Chain: {row[0]}",
        ))

        # Check lists
        check_roles = [
            ("Trigger Checks", row[4], "red"),
            ("Amplifier Checks", row[5], "yellow"),
            ("Mitigator Checks", row[6], "green"),
            ("Evidence Checks", row[7], "cyan"),
        ]
        for label, check_list, color in check_roles:
            if check_list:
                console.print(f"\n[bold]{label}[/bold] ({len(check_list)}):")
                for cid in check_list:
                    console.print(f"  [{color}]{cid}[/{color}]")

        # Factor/pattern/flag references
        if row[8]:
            console.print(f"\nFrequency factors: {', '.join(row[8])}")
        if row[9]:
            console.print(f"Severity factors:  {', '.join(row[9])}")
        if row[10]:
            console.print(f"Patterns:          {', '.join(row[10])}")
        if row[11]:
            console.print(f"Red flags:         {', '.join(row[11])}")

        # Actuarial data
        if row[12] is not None:
            console.print(f"\nHistorical filing rate: {row[12]:.0%}")
        if row[13] is not None:
            console.print(f"Median severity:       ${row[13]:,.0f}")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. explore chains — list chains, optionally filter by peril
# ---------------------------------------------------------------------------


@explore_app.command("chains")
def chains(
    peril: str = typer.Option("", "--peril", "-p", help="Filter by peril_id"),
) -> None:
    """List all causal chains, optionally filtered by peril."""
    conn = _get_conn()
    try:
        query = """SELECT chain_id, name, peril_id,
                          list_length(trigger_signals) as triggers,
                          list_length(amplifier_signals) as amplifiers,
                          list_length(mitigator_signals) as mitigators,
                          list_length(evidence_signals) as evidence,
                          historical_filing_rate, median_severity_usd
                   FROM brain_causal_chains"""
        if peril:
            query += f" WHERE peril_id = '{peril.upper()}'"
        query += " ORDER BY peril_id, chain_id"

        rows = conn.execute(query).fetchall()

        title = "Causal Chains"
        if peril:
            title += f" (peril={peril.upper()})"
        console.print(f"\n[bold]{title}[/bold] — {len(rows)} chains\n")

        if not rows:
            console.print("[dim]No chains found.[/dim]")
            return

        table = Table()
        table.add_column("Chain ID", min_width=24)
        table.add_column("Name", min_width=28)
        table.add_column("Peril", width=18)
        table.add_column("Trig", justify="right", width=5)
        table.add_column("Amp", justify="right", width=5)
        table.add_column("Mit", justify="right", width=5)
        table.add_column("Evid", justify="right", width=5)
        table.add_column("File Rate", justify="right", width=10)
        table.add_column("Median $", justify="right", width=12)

        for r in rows:
            rate = f"{r[7]:.0%}" if r[7] is not None else "-"
            sev = f"${r[8]:,.0f}" if r[8] is not None else "-"
            table.add_row(
                r[0], r[1][:32], r[2],
                str(r[3] or 0), str(r[4] or 0),
                str(r[5] or 0), str(r[6] or 0),
                rate, sev,
            )
        console.print(table)

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. explore coverage — full coverage matrix
# ---------------------------------------------------------------------------


@explore_app.command("coverage")
def coverage(
    section: str = typer.Option(
        "", "--section", "-s",
        help="Filter subsection names containing this string",
    ),
) -> None:
    """Show the full coverage matrix: subsections x perils."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT subsection_id, subsection_name, peril_id, peril_name,
                      total_signals, evaluative_signals, pattern_signals,
                      coverage_level
               FROM brain_coverage_matrix
               ORDER BY coverage_level, subsection_id, peril_id"""
        ).fetchall()

        if not rows:
            console.print(
                "[yellow]No coverage data. Run 'do-uw brain build'.[/yellow]"
            )
            return

        if section:
            section_lower = section.lower()
            rows = [r for r in rows
                    if section_lower in (r[1] or "").lower()
                    or section_lower in (r[0] or "").lower()]

        console.print(
            f"\n[bold]Coverage Matrix[/bold] — {len(rows)} cells\n"
        )

        # Summary
        levels: dict[str, int] = {}
        for r in rows:
            levels[r[7]] = levels.get(r[7], 0) + 1
        for lv in ("GAP", "THIN", "ADEQUATE", "STRONG"):
            ct = levels.get(lv, 0)
            if ct:
                s = _style(_COVERAGE_STYLE, lv)
                console.print(f"  [{s}]{lv}: {ct}[/{s}]")
        console.print()

        table = Table()
        table.add_column("Subsection", min_width=22)
        table.add_column("Peril", min_width=18)
        table.add_column("Level", width=10)
        table.add_column("Total", justify="right", width=6)
        table.add_column("Eval", justify="right", width=6)
        table.add_column("Pattern", justify="right", width=8)

        for r in rows:
            s = _style(_COVERAGE_STYLE, r[7])
            table.add_row(
                (r[1] or "")[:28],
                (r[3] or "")[:22],
                f"[{s}]{r[7]}[/{s}]",
                str(r[4]), str(r[5]), str(r[6]),
            )
        console.print(table)

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. explore effectiveness — check discrimination power
# ---------------------------------------------------------------------------


@explore_app.command("effectiveness")
def effectiveness(
    min_runs: int = typer.Option(
        5, "--min-runs", "-m",
        help="Minimum pipeline runs to include a check",
    ),
) -> None:
    """Show check effectiveness: fire rates and signal quality."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT signal_id, total_runs, fire_count, clear_count,
                      skip_count, fire_rate, signal_quality
               FROM brain_signal_effectiveness
               WHERE total_runs >= ?
               ORDER BY signal_quality, fire_rate DESC""",
            [min_runs],
        ).fetchall()

        console.print(
            f"\n[bold]Check Effectiveness[/bold] "
            f"(min {min_runs} runs) — {len(rows)} checks\n"
        )

        if not rows:
            console.print("[dim]No checks meet the minimum run threshold.[/dim]")
            return

        # Summary by signal quality
        quality_counts: dict[str, int] = {}
        for r in rows:
            quality_counts[r[6]] = quality_counts.get(r[6], 0) + 1
        for q in ("ALWAYS_FIRES", "NEVER_FIRES", "GOOD_DISCRIMINATION",
                   "MODERATE", "INSUFFICIENT_DATA"):
            ct = quality_counts.get(q, 0)
            if ct:
                s = _style(_SIGNAL_STYLE, q)
                console.print(f"  [{s}]{q}: {ct}[/{s}]")
        console.print()

        table = Table()
        table.add_column("Check ID", min_width=28)
        table.add_column("Runs", justify="right", width=6)
        table.add_column("Fires", justify="right", width=6)
        table.add_column("Clear", justify="right", width=6)
        table.add_column("Skip", justify="right", width=6)
        table.add_column("Fire Rate", justify="right", width=10)
        table.add_column("Signal Quality", width=20)

        for r in rows:
            s = _style(_SIGNAL_STYLE, r[6])
            rate = f"{r[5]:.0%}" if r[5] is not None else "-"
            table.add_row(
                r[0], str(r[1]), str(r[2]), str(r[3]), str(r[4]),
                rate, f"[{s}]{r[6]}[/{s}]",
            )
        console.print(table)

    finally:
        conn.close()
