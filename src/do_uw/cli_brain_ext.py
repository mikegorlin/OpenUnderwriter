"""Extended brain CLI: changelog, backlog, export-docs, backtest, stats, export/import."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from do_uw.cli_brain import _PRIORITY_STYLE, _style_for, brain_app, console

# 4. brain changelog


@brain_app.command("changelog")
def changelog(
    check: str = typer.Option(
        None,
        "--check",
        "-c",
        help="Filter to a specific check ID",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-n",
        help="Maximum entries to display",
    ),
) -> None:
    """Show recent changelog entries from brain_changelog."""
    from do_uw.brain.brain_writer import BrainWriter

    writer = BrainWriter()
    try:
        entries = writer.get_changelog(signal_id=check, limit=limit)
    finally:
        writer.close()

    if not entries:
        if check:
            console.print(
                f"[dim]No changelog entries for check '{check}'.[/dim]"
            )
        else:
            console.print("[dim]No changelog entries found.[/dim]")
        return

    console.print(
        f"\n[bold]Brain Changelog[/bold] ({len(entries)} entries"
        + (f", check={check}" if check else "")
        + ")\n"
    )

    table = Table()
    table.add_column("ID", width=5, justify="right")
    table.add_column("Check ID", min_width=20)
    table.add_column("Type", width=10)
    table.add_column("Description", min_width=30)
    table.add_column("Changed By", width=15)
    table.add_column("Timestamp", width=20)

    for entry in entries:
        table.add_row(
            str(entry.get("changelog_id", "")),
            str(entry.get("signal_id", "")),
            str(entry.get("change_type", "")),
            str(entry.get("change_description", ""))[:60],
            str(entry.get("changed_by", "")),
            str(entry.get("changed_at", ""))[:19],
        )

    console.print(table)


# 5. brain backlog


@brain_app.command("backlog")
def backlog() -> None:
    """Show open backlog items sorted by priority."""
    from do_uw.brain.brain_unified_loader import load_backlog

    items = load_backlog()

    if not items:
        console.print("[dim]No open backlog items.[/dim]")
        return

    console.print(
        f"\n[bold]Brain Backlog[/bold] ({len(items)} open items)\n"
    )

    table = Table()
    table.add_column("ID", min_width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Priority", width=10)
    table.add_column("Status", width=10)
    table.add_column("Effort", width=8)
    table.add_column("Risk Questions", min_width=15)

    for item in items:
        priority = item.get("priority", "MEDIUM")
        style = _style_for(_PRIORITY_STYLE, priority)
        rqs = item.get("risk_questions", [])
        rq_str = ", ".join(str(r) for r in rqs) if rqs else "-"

        table.add_row(
            str(item.get("backlog_id", "")),
            str(item.get("title", ""))[:50],
            f"[{style}]{priority}[/{style}]",
            str(item.get("status", "")),
            str(item.get("estimated_effort", "-")),
            rq_str[:30],
        )

    console.print(table)


# 6. brain export-docs


@brain_app.command("export-docs")
def export_docs(
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: print to stdout)",
    ),
) -> None:
    """Export active brain checks to readable Markdown document."""
    from do_uw.brain.brain_unified_loader import load_signals

    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    if not signals:
        console.print("[yellow]No active checks found.[/yellow]")
        return

    # Organize by report_section (enriched field from YAML)
    sections: dict[str, list[dict[str, Any]]] = {}
    for sig in signals:
        section = sig.get("report_section", "unknown")
        threshold = sig.get("threshold", {})
        entry: dict[str, Any] = {
            "signal_id": sig.get("id", sig.get("signal_id", "")),
            "name": sig.get("name", ""),
            "content_type": sig.get("content_type", ""),
            "report_section": section,
            "risk_questions": sig.get("risk_questions", []),
            "question": sig.get("name", ""),
            "threshold_type": threshold.get("type", "") if isinstance(threshold, dict) else "",
            "threshold_red": threshold.get("red", "") if isinstance(threshold, dict) else "",
            "threshold_yellow": threshold.get("yellow", "") if isinstance(threshold, dict) else "",
            "threshold_clear": threshold.get("clear", "") if isinstance(threshold, dict) else "",
        }
        sections.setdefault(section, []).append(entry)

    # Build Markdown
    lines: list[str] = [
        "# Brain Check Definitions",
        "",
        f"**Total active checks:** {len(signals)}",
        f"**Sections:** {', '.join(sorted(sections.keys()))}",
        "",
    ]

    for section_name in sorted(sections.keys()):
        checks = sections[section_name]
        lines.append(f"## {section_name.upper()} ({len(checks)} checks)")
        lines.append("")

        for check in checks:
            lines.append(f"### {check['signal_id']}")
            lines.append(f"**{check['name']}**")
            lines.append("")
            if check["question"]:
                lines.append(f"- **Question:** {check['question']}")
            lines.append(f"- **Content type:** {check['content_type']}")

            rqs = check["risk_questions"]
            if rqs:
                lines.append(f"- **Risk questions:** {', '.join(str(r) for r in rqs)}")

            # Thresholds
            if check["threshold_red"] or check["threshold_yellow"] or check["threshold_clear"]:
                lines.append(f"- **Threshold type:** {check['threshold_type']}")
                if check["threshold_red"]:
                    lines.append(f"  - RED: {check['threshold_red']}")
                if check["threshold_yellow"]:
                    lines.append(f"  - YELLOW: {check['threshold_yellow']}")
                if check["threshold_clear"]:
                    lines.append(f"  - CLEAR: {check['threshold_clear']}")

            lines.append("")

    md_text = "\n".join(lines)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_text, encoding="utf-8")
        console.print(f"[green]Exported {len(signals)} checks to {output}[/green]")
    else:
        console.print(md_text)


# 7. brain backtest


@brain_app.command("backtest")
def backtest(
    state_path: Path = typer.Argument(
        help="Path to a historical state.json file (e.g., output/AAPL/state.json)",
    ),
    record: bool = typer.Option(
        True,
        "--record/--no-record",
        help="Store results in brain_signal_runs (default: True)",
    ),
    compare: bool = typer.Option(
        False,
        "--compare",
        help="Compare with previous backtest of same state (if exists)",
    ),
) -> None:
    """Run current checks against a historical state file."""
    from do_uw.knowledge.backtest import run_backtest

    if not state_path.exists():
        console.print(f"[red]State file not found: {state_path}[/red]")
        raise typer.Exit(code=1)

    console.print(
        f"\n[bold]Backtesting[/bold] against {state_path}...\n"
    )

    try:
        result = run_backtest(state_path, record=record)
    except Exception as exc:
        console.print(f"[red]Backtest failed: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold]Backtest Result: {result.ticker}[/bold]")
    console.print(f"State path: {result.state_path}")
    if result.state_date:
        console.print(f"State date: {result.state_date}")
    console.print()

    table = Table(title="Check Results Summary")
    table.add_column("Status", min_width=12)
    table.add_column("Count", justify="right")
    table.add_row("Executed", str(result.checks_executed))
    table.add_row("[red]Triggered[/red]", str(result.triggered))
    table.add_row("[green]Clear[/green]", str(result.clear))
    table.add_row("[yellow]Skipped[/yellow]", str(result.skipped))
    table.add_row("[dim]Info[/dim]", str(result.info))
    console.print(table)

    if record:
        console.print(
            f"\n[dim]Results recorded to brain_signal_runs "
            f"(run_id: backtest_{result.ticker}_*)[/dim]"
        )
    else:
        console.print("\n[dim]Results NOT recorded (--no-record).[/dim]")


# 8. brain stats (quick table count summary)


@brain_app.command("stats")
def stats() -> None:
    """Quick summary: YAML signal count + DuckDB history table counts."""
    from do_uw.brain.brain_unified_loader import load_signals

    # YAML definitions
    signals_data = load_signals()
    total_signals = signals_data.get("total_signals", 0)

    console.print(f"\n[bold]Brain Stats[/bold]\n")
    console.print(f"  Signals (from YAML): [bold]{total_signals}[/bold]\n")

    # DuckDB history tables
    try:
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        db_path = get_brain_db_path()
        if not db_path.exists():
            console.print("[dim]brain.duckdb not found -- history stats unavailable.[/dim]")
            return

        file_mb = db_path.stat().st_size / (1024 * 1024)
        console.print(f"[dim]History DB: {db_path} ({file_mb:.1f} MB)[/dim]\n")

        conn = connect_brain_db(db_path)
        try:
            table = Table(title="History Table Counts")
            table.add_column("Table", min_width=28)
            table.add_column("Rows", justify="right")

            history_tables = [
                ("brain_signal_runs", "brain_signal_runs"),
                ("brain_effectiveness", "brain_effectiveness"),
                ("brain_backlog", "brain_backlog"),
                ("brain_changelog", "brain_changelog"),
                ("brain_feedback", "brain_feedback"),
                ("brain_proposals", "brain_proposals"),
            ]
            for label, tname in history_tables:
                try:
                    count = conn.execute(
                        f"SELECT COUNT(*) FROM {tname}"  # noqa: S608
                    ).fetchone()[0]
                    table.add_row(label, f"{count:,}")
                except Exception:
                    table.add_row(label, "[dim]-[/dim]")
            console.print(table)

            # brain_meta entries
            try:
                meta_rows = conn.execute(
                    "SELECT meta_key, meta_value FROM brain_meta ORDER BY meta_key"
                ).fetchall()
                if meta_rows:
                    console.print()
                    mt = Table(title="Brain Metadata")
                    mt.add_column("Key")
                    mt.add_column("Value")
                    for k, v in meta_rows:
                        mt.add_row(k, v)
                    console.print(mt)
            except Exception:
                pass
        finally:
            conn.close()
    except Exception:
        console.print("[dim]DuckDB history not available.[/dim]")


# 9. brain export-all (DuckDB → JSON directory)


@brain_app.command("export-all")
def export_all(
    output_dir: Path = typer.Argument(
        help="Directory to write JSON files (signals.json, scoring.json, etc.)",
    ),
) -> None:
    """Export all brain data to JSON files (from YAML/JSON source)."""
    import json as json_mod
    import shutil

    from do_uw.brain.brain_unified_loader import (
        BrainLoader,
        load_signals,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    loader = BrainLoader()

    # 1. Signals
    signals_data = load_signals()
    signals = signals_data.get("signals", [])
    (output_dir / "signals.json").write_text(
        json_mod.dumps({
            "$schema": "BRAIN_CHECKS_EXPORT",
            "version": "exported",
            "description": "Exported from brain YAML",
            "total_signals": len(signals),
            "signals": signals,
        }, indent=2),
        encoding="utf-8",
    )
    console.print(f"  signals.json: {len(signals)} signals")

    # 2. Scoring
    scoring = loader.load_scoring()
    (output_dir / "scoring.json").write_text(
        json_mod.dumps(scoring, indent=2), encoding="utf-8"
    )
    console.print(f"  scoring.json: {len(scoring.get('factors', {}))} factors")

    # 3. Patterns
    patterns = loader.load_patterns()
    (output_dir / "patterns.json").write_text(
        json_mod.dumps(patterns, indent=2), encoding="utf-8"
    )
    console.print(f"  patterns.json: {patterns.get('total_patterns', 0)} patterns")

    # 4. Red flags
    red_flags = loader.load_red_flags()
    (output_dir / "red_flags.json").write_text(
        json_mod.dumps(red_flags, indent=2), encoding="utf-8"
    )
    console.print(
        f"  red_flags.json: {len(red_flags.get('escalation_triggers', []))} triggers"
    )

    # 5. Sectors
    sectors = loader.load_sectors()
    (output_dir / "sectors.json").write_text(
        json_mod.dumps(sectors, indent=2), encoding="utf-8"
    )
    console.print(f"  sectors.json: {len(sectors)} metrics")

    # 6. Config files (copy from brain/config/)
    brain_config_dir = Path(__file__).parent / "brain" / "config"
    if brain_config_dir.exists():
        export_config_dir = output_dir / "config"
        export_config_dir.mkdir(exist_ok=True)
        config_count = 0
        for json_file in sorted(brain_config_dir.glob("*.json")):
            if json_file.name != "signals.json":  # already exported above
                shutil.copy2(json_file, export_config_dir / json_file.name)
                config_count += 1
        console.print(f"  config/: {config_count} files")

    console.print(f"\n[green]Exported brain to {output_dir}[/green]")


# 10. brain import-json (JSON directory → DuckDB)


@brain_app.command("import-json")
def import_json(
    input_dir: Path = typer.Argument(
        help="Directory containing JSON files to import into brain.duckdb",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force full reimport (destructive: clears existing data first)",
    ),
) -> None:
    """Import JSON files into brain.duckdb (deprecated for definitions).

    Signal definitions are now sourced from YAML directly at runtime.
    This command still works for populating DuckDB history/legacy tables,
    but is no longer needed for normal operation.
    """
    console.print(
        "[yellow]Note: Signal definitions are now read from YAML at runtime.[/yellow]\n"
        "[yellow]This command populates DuckDB tables for backward compatibility only.[/yellow]\n"
    )

    from do_uw.brain.brain_migrate import migrate_checks_to_brain
    from do_uw.brain.brain_schema import connect_brain_db
    from do_uw.brain.legacy.brain_migrate_config import migrate_configs, populate_brain_meta
    from do_uw.brain.legacy.brain_migrate_scoring import migrate_all_scoring

    conn = connect_brain_db()
    try:
        # Checks
        checks_path = input_dir / "signals.json"
        if checks_path.exists():
            result = migrate_checks_to_brain(
                conn=conn, checks_path=checks_path, force_clean=force,
            )
            console.print(f"  checks: {result['signals']} active")
        else:
            console.print("  [dim]signals.json not found, skipping[/dim]")

        # Scoring + patterns + red flags + sectors
        migrate_all_scoring(conn=conn)
        console.print("  scoring, patterns, red flags, sectors: imported")

        # Config files
        config_dir = input_dir / "config"
        if config_dir.exists():
            n = migrate_configs(conn=conn, config_dir=config_dir)
            console.print(f"  config: {n} entries")
        else:
            console.print("  [dim]config/ not found, skipping[/dim]")

        populate_brain_meta(conn)
    finally:
        conn.close()

    console.print(f"\n[green]Imported brain from {input_dir}[/green]")


# 11. brain coverage-gaps (alias for explore coverage --section/level filters)


@brain_app.command("coverage-gaps")
def coverage_gaps(
    section: str = typer.Option("", "--section", "-s", help="Filter subsection names"),
    level: str = typer.Option("", "--level", "-l", help="GAP, THIN, ADEQUATE, STRONG"),
) -> None:
    """Show coverage matrix gaps. Alias for 'brain explore coverage'."""
    from do_uw.cli_brain_explore import coverage as _explore_coverage

    _explore_coverage(section=section)
