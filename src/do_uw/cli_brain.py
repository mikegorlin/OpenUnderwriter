"""CLI sub-commands for brain knowledge system operations.

Provides commands for brain management including:
- ``do-uw brain status`` -- brain summary (YAML definitions + DuckDB history)
- ``do-uw brain gaps`` -- pipeline gap detection
- ``do-uw brain effectiveness`` -- check effectiveness metrics
- ``do-uw brain changelog`` -- recent changelog entries
- ``do-uw brain backlog`` -- open backlog items
- ``do-uw brain export-docs`` -- export brain to Markdown
- ``do-uw brain backtest`` -- run checks against historical state

Signal definitions read from YAML (via BrainLoader).
DuckDB used for history tables only (signal_runs, effectiveness, feedback, changelog).

Registered as a Typer sub-app in cli.py.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

brain_app = typer.Typer(
    name="brain",
    help="Brain knowledge system: status, gaps, effectiveness, changelog, backlog, export, backtest",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# Severity style helpers
# ---------------------------------------------------------------------------

_SEVERITY_STYLE: dict[str, str] = {
    "CRITICAL": "bold red",
    "HIGH": "bold red",
    "WARNING": "yellow",
    "MEDIUM": "",
    "INFO": "dim",
    "LOW": "dim",
}

_PRIORITY_STYLE: dict[str, str] = {
    "CRITICAL": "bold red",
    "HIGH": "yellow",
    "MEDIUM": "",
    "LOW": "dim",
}


def _style_for(mapping: dict[str, str], key: str) -> str:
    return mapping.get(key, "")


# ---------------------------------------------------------------------------
# 1. brain status
# ---------------------------------------------------------------------------


@brain_app.command("status")
def status() -> None:
    """Show brain summary: YAML signal definitions + DuckDB history counts."""
    from collections import Counter

    from do_uw.brain.brain_unified_loader import (
        BrainLoader,
        load_signals,
        load_taxonomy,
    )

    loader = BrainLoader()

    console.print("\n[bold]Brain Status[/bold]")
    console.print("[dim]Source: brain/signals/ YAML + brain/config/ JSON[/dim]\n")

    # Signal definitions from YAML
    signals_data = load_signals()
    signals = signals_data.get("signals", [])
    total_active = len(signals)
    console.print(f"Total signals: [bold]{total_active}[/bold] (from YAML)")

    # V2 migration progress
    v2_count = sum(1 for sig in signals if sig.get("schema_version", 1) >= 2)
    if total_active > 0:
        v2_pct = v2_count * 100 // total_active
        console.print(
            f"  V2 signals: [bold]{v2_count}[/bold]/{total_active} ({v2_pct}%)"
        )

    # Field registry count
    try:
        from do_uw.brain.field_registry import load_field_registry

        registry = load_field_registry()
        console.print(
            f"  Field registry: [bold]{len(registry.fields)}[/bold] fields mapped"
        )
    except Exception:
        console.print("  [dim]Field registry not available[/dim]")

    # Shadow evaluation summary
    try:
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        shadow_db_path = get_brain_db_path()
        if shadow_db_path.exists():
            shadow_conn = connect_brain_db(shadow_db_path)
            try:
                # Check if table exists
                tables = shadow_conn.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_name = 'brain_shadow_evaluations'"
                ).fetchall()
                if tables:
                    row = shadow_conn.execute(
                        "SELECT COUNT(*) AS total, "
                        "SUM(CASE WHEN is_match THEN 1 ELSE 0 END) AS match_count, "
                        "SUM(CASE WHEN NOT is_match THEN 1 ELSE 0 END) AS mismatch_count "
                        "FROM brain_shadow_evaluations"
                    ).fetchone()
                    if row and row[0] > 0:
                        total, match_count, mismatch_count = row[0], row[1], row[2]
                        match_style = "green" if mismatch_count == 0 else "yellow"
                        console.print(
                            f"\n  Shadow evaluations: [bold]{total}[/bold] "
                            f"([{match_style}]match: {match_count}[/{match_style}], "
                            f"mismatch: {mismatch_count})"
                        )
                        # Show top discrepant signals if any mismatches
                        if mismatch_count > 0:
                            discrepancies = shadow_conn.execute(
                                "SELECT signal_id, COUNT(*) AS cnt "
                                "FROM brain_shadow_evaluations "
                                "WHERE NOT is_match "
                                "GROUP BY signal_id "
                                "ORDER BY cnt DESC LIMIT 5"
                            ).fetchall()
                            if discrepancies:
                                console.print("  [yellow]Top discrepant signals:[/yellow]")
                                for sig_id, cnt in discrepancies:
                                    console.print(f"    - {sig_id}: {cnt} mismatches")
                    else:
                        console.print("\n  [dim]Shadow evaluations: 0 (no runs yet)[/dim]")
            finally:
                shadow_conn.close()
    except Exception:
        pass  # Shadow table may not exist yet

    # By content_type (enriched field)
    ct_counter: Counter[str] = Counter()
    for sig in signals:
        ct_counter[sig.get("content_type", "unknown")] += 1
    if ct_counter:
        table = Table(title="Signals by Content Type")
        table.add_column("Content Type")
        table.add_column("Count", justify="right")
        for ctype, count in sorted(ct_counter.items()):
            table.add_row(ctype, str(count))
        console.print(table)

    # By report_section (enriched field)
    rs_counter: Counter[str] = Counter()
    for sig in signals:
        rs_counter[sig.get("report_section", "unknown")] += 1
    if rs_counter:
        table = Table(title="Signals by Report Section")
        table.add_column("Report Section")
        table.add_column("Count", justify="right")
        for section, count in sorted(rs_counter.items()):
            table.add_row(section, str(count))
        console.print(table)

    # Taxonomy from YAML
    taxonomy = load_taxonomy()
    if taxonomy:
        table = Table(title="Taxonomy Entities (from YAML)")
        table.add_column("Entity Type")
        table.add_column("Count", justify="right")
        for etype, entries in sorted(taxonomy.items()):
            if isinstance(entries, list):
                table.add_row(etype, str(len(entries)))
        console.print(table)

    # Backlog from DuckDB (history data)
    backlog = loader.load_backlog()
    console.print(f"\nOpen backlog items: [bold]{len(backlog)}[/bold]")

    # DuckDB history counts (if available)
    try:
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        db_path = get_brain_db_path()
        if db_path.exists():
            file_size_mb = db_path.stat().st_size / (1024 * 1024)
            console.print(f"\n[dim]History DB: {db_path} ({file_size_mb:.1f} MB)[/dim]")

            conn = connect_brain_db(db_path)
            try:
                run_count = conn.execute(
                    "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
                    "WHERE is_backtest = FALSE"
                ).fetchone()[0]
                backtest_count = conn.execute(
                    "SELECT COUNT(DISTINCT run_id) FROM brain_signal_runs "
                    "WHERE is_backtest = TRUE"
                ).fetchone()[0]
                console.print(
                    f"Pipeline runs recorded: {run_count} "
                    f"(+ {backtest_count} backtests)"
                )
            finally:
                conn.close()
    except Exception:
        console.print("[dim]DuckDB history not available.[/dim]")


# ---------------------------------------------------------------------------
# 2. brain gaps
# ---------------------------------------------------------------------------


@brain_app.command("gaps")
def gaps(
    severity: str = typer.Option(
        "ALL",
        "--severity",
        "-s",
        help="Filter by severity: CRITICAL, WARNING, INFO, ALL",
    ),
    gap_type: str = typer.Option(
        "",
        "--type",
        "-t",
        help="Filter by gap type: SOURCE_NOT_ACQUIRED, NO_FIELD_ROUTING, NO_MAPPER_HANDLER",
    ),
) -> None:
    """Run pipeline gap detection and display Rich-formatted report."""
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.knowledge.gap_detector import detect_gaps
    from do_uw.knowledge.requirements import build_manifest

    checks_data = load_signals()
    checks = checks_data.get("signals", [])

    manifest = build_manifest(checks)
    report = detect_gaps(checks, manifest)

    console.print("\n[bold]Pipeline Gap Report[/bold]")
    console.print(
        f"Total AUTO signals: {report.total_signals} | "
        f"Fully supported: [green]{report.fully_supported}[/green] | "
        f"Gaps: {len(report.gaps)}"
    )

    # Severity summary
    if report.by_severity:
        for sev in ("CRITICAL", "WARNING", "INFO"):
            count = report.by_severity.get(sev, 0)
            style = _style_for(_SEVERITY_STYLE, sev)
            if count > 0:
                console.print(f"  [{style}]{sev}: {count}[/{style}]")

    # Type summary
    if report.by_type:
        console.print()
        for gtype, count in sorted(report.by_type.items()):
            console.print(f"  {gtype}: {count}")

    # Filter gaps
    filtered = report.gaps
    if severity.upper() != "ALL":
        filtered = [g for g in filtered if g.severity == severity.upper()]
    if gap_type:
        filtered = [g for g in filtered if g.gap_type == gap_type.upper()]

    if filtered:
        console.print()
        table = Table(title=f"Gaps ({len(filtered)} shown)")
        table.add_column("Severity", width=10)
        table.add_column("Type", width=22)
        table.add_column("Check ID", min_width=25)
        table.add_column("Detail", min_width=30)
        for g in filtered:
            style = _style_for(_SEVERITY_STYLE, g.severity)
            table.add_row(
                f"[{style}]{g.severity}[/{style}]",
                g.gap_type,
                g.signal_id,
                g.detail[:80],
            )
        console.print(table)
    elif severity.upper() != "ALL" or gap_type:
        console.print("\n[dim]No gaps match the given filters.[/dim]")


# ---------------------------------------------------------------------------
# 3. brain effectiveness
# ---------------------------------------------------------------------------


@brain_app.command("effectiveness")
def effectiveness(
    min_runs: int = typer.Option(
        1,
        "--min-runs",
        help="Minimum runs for a check to be included",
    ),
) -> None:
    """Show check effectiveness metrics: always-fire, never-fire, high-skip."""
    from do_uw.brain.brain_effectiveness import compute_effectiveness
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        console.print(
            "[yellow]brain.duckdb not found. Run the pipeline first.[/yellow]"
        )
        raise typer.Exit(code=1)

    conn = connect_brain_db(db_path)
    try:
        report = compute_effectiveness(conn, min_runs=min_runs)
    finally:
        conn.close()

    console.print("\n[bold]Check Effectiveness Report[/bold]")
    console.print(
        f"Checks analyzed: {report.total_signals_analyzed} | "
        f"Pipeline runs: {report.total_runs}"
    )
    console.print(f"[dim]{report.confidence_note}[/dim]\n")

    # Always-fire checks (red)
    if report.always_fire:
        table = Table(title="Always-Fire Checks (too sensitive?)")
        table.add_column("Check ID", min_width=25)
        table.add_column("Fire Rate", justify="right")
        table.add_column("Runs", justify="right")
        for entry in report.always_fire:
            table.add_row(
                f"[red]{entry['signal_id']}[/red]",
                f"{entry.get('fire_rate', 1.0):.0%}",
                str(entry.get("run_count", 0)),
            )
        console.print(table)
    else:
        console.print("[dim]No always-fire checks.[/dim]")

    # Never-fire checks (yellow)
    if report.never_fire:
        table = Table(title="Never-Fire Checks (miscalibrated?)")
        table.add_column("Check ID", min_width=25)
        table.add_column("Runs", justify="right")
        for entry in report.never_fire:
            table.add_row(
                f"[yellow]{entry['signal_id']}[/yellow]",
                str(entry.get("run_count", 0)),
            )
        console.print(table)
    else:
        console.print("[dim]No never-fire checks.[/dim]")

    # High-skip checks (yellow)
    if report.high_skip:
        table = Table(title="High-Skip Checks (data gap?)")
        table.add_column("Check ID", min_width=25)
        table.add_column("Skip Rate", justify="right")
        table.add_column("Runs", justify="right")
        for entry in report.high_skip:
            table.add_row(
                f"[yellow]{entry['signal_id']}[/yellow]",
                f"{entry.get('skip_rate', 0):.0%}",
                str(entry.get("run_count", 0)),
            )
        console.print(table)
    else:
        console.print("[dim]No high-skip checks.[/dim]")

    # Consistent checks (green)
    if report.consistent:
        table = Table(title="Consistent Checks (reliable)")
        table.add_column("Check ID", min_width=25)
        table.add_column("Fire Rate", justify="right")
        for entry in report.consistent:
            table.add_row(
                f"[green]{entry['signal_id']}[/green]",
                f"{entry.get('fire_rate', 0):.0%}",
            )
        console.print(table)
    else:
        console.print("[dim]No consistent checks (need more runs).[/dim]")


# ---------------------------------------------------------------------------
# 4. brain build
# ---------------------------------------------------------------------------


@brain_app.command("build")
def build() -> None:
    """Validate YAML signals and export signals.json.

    Reads all signals/**/*.yaml, validates via BrainSignalEntry schema,
    runs cross-reference integrity checks, and exports signals.json.

    No DuckDB definition table writes -- YAML is read directly at runtime.
    DuckDB is used for history data only (signal_runs, effectiveness, etc.)
    """
    from do_uw.brain.brain_build_signals import build_checks_from_yaml

    results = build_checks_from_yaml()

    errors = results.get("errors", [])
    unlinked = results.get("unlinked", 0)
    coverage = results.get("coverage", {})

    console.print("\n[bold]Brain Build Complete[/bold]\n")
    console.print(
        f"  Validated {results['signals']} signals "
        f"({unlinked} unlinked) from {results['yaml_files']} YAML files"
    )

    if errors:
        console.print(f"  [yellow]Errors: {len(errors)}[/yellow]")
        for err in errors:
            console.print(f"    [yellow]- {err}[/yellow]")
    else:
        console.print("  [green]No validation errors[/green]")

    if coverage:
        console.print(f"\n  Coverage ({len(coverage)} prefix families):")
        for prefix, count in sorted(coverage.items()):
            console.print(f"    {prefix}: {count} signals")

    v2_count = results.get("v2_signals", 0)
    if v2_count > 0:
        console.print(f"\n  V2 signals validated: [bold]{v2_count}[/bold]")

    console.print("\n  [dim]Exported: brain/config/signals.json[/dim]")


# ---------------------------------------------------------------------------
# Explore sub-app (Phase 42: human query interface for risk framework)
# ---------------------------------------------------------------------------
from do_uw.cli_brain_explore import explore_app as _explore_app  # noqa: E402

brain_app.add_typer(_explore_app, name="explore")

# ---------------------------------------------------------------------------
# Extended commands (changelog, backlog, export-docs, backtest)
# registered via cli_brain_ext.py import
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Live learning commands (add, provenance) registered via cli_brain_add.py import
# ---------------------------------------------------------------------------
import do_uw.cli_brain_add as _cli_brain_add  # noqa: F401, E402
import do_uw.cli_brain_ext as _cli_brain_ext  # noqa: F401, E402

# ---------------------------------------------------------------------------
# YAML commands (validate, unlinked) registered via cli_brain_yaml.py import
# ---------------------------------------------------------------------------
import do_uw.cli_brain_yaml as _cli_brain_yaml  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Trace command (pipeline journey for a single signal)
# registered via cli_brain_trace.py import
# ---------------------------------------------------------------------------
import do_uw.cli_brain_trace as _cli_brain_trace  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Health + audit commands registered via cli_brain_health.py import
# ---------------------------------------------------------------------------
import do_uw.cli_brain_health as _cli_brain_health  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Apply-proposal command (YAML write-back) registered via cli_brain_apply.py
# ---------------------------------------------------------------------------
import do_uw.cli_brain_apply as _cli_brain_apply  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Visualize command (interactive dependency graph)
# registered via cli_brain_visualize.py import
# ---------------------------------------------------------------------------
import do_uw.cli_brain_visualize as _cli_brain_visualize  # noqa: F401, E402
