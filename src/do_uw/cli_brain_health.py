"""Brain health + audit CLI commands. Registered via cli_brain.py."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from do_uw.cli_brain import brain_app

console = Console()


# ---------------------------------------------------------------------------
# brain health
# ---------------------------------------------------------------------------


@brain_app.command("health")
def brain_health() -> None:
    """Show unified brain system health: coverage, fire rates, freshness."""
    from do_uw.brain.brain_health import compute_brain_health
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        console.print(
            "[red]brain.duckdb not found.[/red] "
            "Run 'do-uw brain build' first."
        )
        raise typer.Exit(code=1)

    file_size_mb = db_path.stat().st_size / (1024 * 1024)

    conn = connect_brain_db(db_path)
    try:
        report = compute_brain_health(conn)
    finally:
        conn.close()

    # Header panel
    console.print()
    console.print(
        Panel(
            f"[dim]Database: {db_path} ({file_size_mb:.1f} MB)[/dim]",
            title="[bold]Brain Health Report[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    # Overview table
    overview = Table(
        title="Overview",
        show_header=False,
        border_style="dim",
        title_style="bold",
        padding=(0, 1),
    )
    overview.add_column("Metric", style="bold", width=20)
    overview.add_column("Value", ratio=1)

    # Active signals
    overview.add_row(
        "Active signals",
        f"[bold]{report.total_active_signals}[/bold] "
        f"(of {report.total_all_signals} total)",
    )

    # Facet coverage
    cov_color = (
        "green" if report.facet_coverage_pct >= 90
        else "yellow" if report.facet_coverage_pct >= 70
        else "red"
    )
    overview.add_row(
        "Facet coverage",
        f"[{cov_color}]{report.facet_coverage_pct:.1f}%[/{cov_color}] "
        f"({report.signals_in_facets} in facets, "
        f"{report.signals_not_in_facets} orphaned)",
    )

    # Pipeline runs
    overview.add_row(
        "Pipeline runs",
        f"{report.total_pipeline_runs} "
        f"(+ {report.total_backtest_runs} backtests)",
    )

    # Tickers analyzed
    tickers_str = (
        ", ".join(report.tickers_analyzed)
        if report.tickers_analyzed
        else "[dim]none[/dim]"
    )
    overview.add_row("Tickers analyzed", tickers_str)

    # Data freshness
    freshness_color = "green" if report.data_freshness != "N/A" else "dim"
    overview.add_row(
        "Data freshness",
        f"[{freshness_color}]{report.data_freshness}[/{freshness_color}]",
    )

    # Feedback queue
    fb_color = "yellow" if report.feedback_queue_size > 0 else "dim"
    overview.add_row(
        "Feedback queue",
        f"[{fb_color}]{report.feedback_queue_size} pending[/{fb_color}]",
    )

    console.print(overview)

    # Fire rate distribution table
    total_in_dist = sum(report.fire_rate_distribution.values())
    if total_in_dist > 0:
        dist_table = Table(
            title="Fire Rate Distribution",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold",
            padding=(0, 1),
        )
        dist_table.add_column("Fire Rate", width=16)
        dist_table.add_column("Signals", justify="right", width=10)

        bucket_labels = ["0%", "1-10%", "10-30%", "30-50%", "50-80%", "80-100%"]
        bucket_styles = {
            "0%": "yellow",
            "1-10%": "dim",
            "10-30%": "green",
            "30-50%": "green",
            "50-80%": "dim",
            "80-100%": "red",
        }
        for label in bucket_labels:
            count = report.fire_rate_distribution.get(label, 0)
            display_label = f"0% (never)" if label == "0%" else label
            style = bucket_styles.get(label, "")
            dist_table.add_row(
                f"[{style}]{display_label}[/{style}]",
                f"[{style}]{count}[/{style}]",
            )

        console.print(dist_table)
    else:
        console.print(
            "[dim]No fire rate data available "
            "(run the pipeline to generate signal runs).[/dim]"
        )

    # Top problematic signals
    if report.top_always_fire:
        af_table = Table(
            title="Always-Fire Signals (top 10)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold red",
            padding=(0, 1),
        )
        af_table.add_column("Signal ID", min_width=25)
        af_table.add_column("Fire Rate", justify="right", width=10)
        af_table.add_column("Runs", justify="right", width=8)
        for entry in report.top_always_fire:
            af_table.add_row(
                f"[red]{entry['signal_id']}[/red]",
                f"{entry.get('fire_rate', 1.0):.0%}",
                str(entry.get("run_count", 0)),
            )
        console.print(af_table)

    if report.top_never_fire:
        nf_table = Table(
            title="Never-Fire Signals (top 10)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold yellow",
            padding=(0, 1),
        )
        nf_table.add_column("Signal ID", min_width=25)
        nf_table.add_column("Runs", justify="right", width=8)
        for entry in report.top_never_fire:
            nf_table.add_row(
                f"[yellow]{entry['signal_id']}[/yellow]",
                str(entry.get("run_count", 0)),
            )
        console.print(nf_table)

    if report.top_high_skip:
        hs_table = Table(
            title="High-Skip Signals (top 10)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold yellow",
            padding=(0, 1),
        )
        hs_table.add_column("Signal ID", min_width=25)
        hs_table.add_column("Skip Rate", justify="right", width=10)
        hs_table.add_column("Runs", justify="right", width=8)
        for entry in report.top_high_skip:
            hs_table.add_row(
                f"[yellow]{entry['signal_id']}[/yellow]",
                f"{entry.get('skip_rate', 0):.0%}",
                str(entry.get("run_count", 0)),
            )
        console.print(hs_table)

    if (
        not report.top_always_fire
        and not report.top_never_fire
        and not report.top_high_skip
    ):
        console.print(
            "[dim]No problematic signals detected "
            "(run the pipeline to generate signal runs).[/dim]"
        )

    # do_context coverage (YAML-based, no DuckDB needed)
    try:
        from do_uw.brain.brain_unified_loader import load_signals as _load_all_signals

        all_signals_data = _load_all_signals()
        all_signals_list = all_signals_data.get("signals", [])
        total_signals = len(all_signals_list)
        with_do_context = sum(
            1
            for s in all_signals_list
            if isinstance(s.get("presentation"), dict)
            and s["presentation"].get("do_context")
        )
        pct = (100 * with_do_context / total_signals) if total_signals > 0 else 0
        pct_color = "green" if pct >= 50 else "yellow" if pct >= 10 else "dim"
        console.print(
            f"\n[bold]do_context Coverage:[/bold] "
            f"[{pct_color}]{with_do_context} / {total_signals} signals ({pct:.0f}%)[/{pct_color}]"
        )
    except Exception as exc:
        console.print(f"[dim]do_context coverage check failed: {exc}[/dim]")

    console.print()


# ---------------------------------------------------------------------------
# brain delta
# ---------------------------------------------------------------------------


@brain_app.command("delta")
def brain_delta_cmd(
    ticker: str = typer.Argument(help="Ticker to compare runs for"),
    run1: str = typer.Option("", "--run1", help="Explicit old run ID"),
    run2: str = typer.Option("", "--run2", help="Explicit new run ID"),
    list_runs_flag: bool = typer.Option(
        False, "--list-runs", help="List available runs for this ticker"
    ),
) -> None:
    """Show signal status changes between two runs for a ticker."""
    from do_uw.brain.brain_delta import compute_delta, list_runs
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        console.print(
            "[red]brain.duckdb not found.[/red] "
            "Run the pipeline first."
        )
        raise typer.Exit(code=1)

    ticker_upper = ticker.upper()
    conn = connect_brain_db(db_path)
    try:
        # --list-runs mode: show available runs and exit
        if list_runs_flag:
            runs = list_runs(conn, ticker_upper)
            if not runs:
                console.print(
                    f"[yellow]No runs found for {ticker_upper}.[/yellow]"
                )
                raise typer.Exit(code=1)

            console.print()
            runs_table = Table(
                title=f"Available Runs for {ticker_upper}",
                show_header=True,
                header_style="bold",
                border_style="dim",
                title_style="bold",
                padding=(0, 1),
            )
            runs_table.add_column("Run ID", min_width=20)
            runs_table.add_column("Date", width=22)
            runs_table.add_column("Signals", justify="right", width=10)
            for run in runs:
                runs_table.add_row(
                    run.run_id,
                    run.run_date,
                    str(run.signal_count),
                )
            console.print(runs_table)
            console.print()
            return

        # Delta mode (default)
        report = compute_delta(
            conn,
            ticker_upper,
            run1_id=run1 or None,
            run2_id=run2 or None,
        )
    finally:
        conn.close()

    # Handle errors
    if report.error:
        console.print(f"[red]{report.error}[/red]")
        if "Need at least 2" in report.error:
            console.print(
                f"[dim]Run 'do-uw analyze {ticker_upper}' to create more runs.[/dim]"
            )
        raise typer.Exit(code=1)

    # Header panel
    console.print()
    header_text = (
        f"Old run: [bold]{report.old_run.run_id}[/bold] "
        f"({report.old_run.run_date}) -- "
        f"{report.old_run.signal_count} signals\n"
        f"New run: [bold]{report.new_run.run_id}[/bold] "
        f"({report.new_run.run_date}) -- "
        f"{report.new_run.signal_count} signals"
    )
    console.print(
        Panel(
            header_text,
            title=f"[bold]Signal Delta: {ticker_upper}[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    # Summary line
    total_changes = len(report.changes)
    if total_changes == 0:
        console.print(
            "[green]No signal status changes between runs.[/green]"
        )
        console.print()
        return

    change_color = "yellow" if total_changes < 10 else "red"
    console.print(
        f"[{change_color}]{total_changes} changes detected[/{change_color}] "
        f"({report.unchanged_count} unchanged)"
    )

    # Newly TRIGGERED table
    if report.newly_triggered:
        trig_table = Table(
            title="Newly Triggered (CLEAR/SKIPPED -> TRIGGERED)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold red",
            padding=(0, 1),
        )
        trig_table.add_column("Signal", min_width=30)
        trig_table.add_column("Was", width=12)
        trig_table.add_column("Value", width=20)
        for change in report.newly_triggered:
            trig_table.add_row(
                f"[bold red]{change.signal_id}[/bold red]",
                change.old_status or "(new)",
                change.new_value or "",
            )
        console.print(trig_table)

    # Newly CLEARED table
    if report.newly_cleared:
        clear_table = Table(
            title="Newly Cleared (TRIGGERED/SKIPPED -> CLEAR)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold green",
            padding=(0, 1),
        )
        clear_table.add_column("Signal", min_width=30)
        clear_table.add_column("Was", width=12)
        clear_table.add_column("Value", width=20)
        for change in report.newly_cleared:
            clear_table.add_row(
                f"[green]{change.signal_id}[/green]",
                change.old_status or "(new)",
                change.new_value or "",
            )
        console.print(clear_table)

    # Newly SKIPPED table
    if report.newly_skipped:
        skip_table = Table(
            title="Newly Skipped (-> SKIPPED)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold yellow",
            padding=(0, 1),
        )
        skip_table.add_column("Signal", min_width=30)
        skip_table.add_column("Was", width=12)
        for change in report.newly_skipped:
            skip_table.add_row(
                f"[yellow]{change.signal_id}[/yellow]",
                change.old_status or "(new)",
            )
        console.print(skip_table)

    # Other changes table
    if report.other_changes:
        other_table = Table(
            title="Other Changes",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="dim",
            padding=(0, 1),
        )
        other_table.add_column("Signal", min_width=30)
        other_table.add_column("Was", width=12)
        other_table.add_column("Now", width=12)
        for change in report.other_changes:
            other_table.add_row(
                f"[dim]{change.signal_id}[/dim]",
                change.old_status or "(new)",
                change.new_status or "(removed)",
            )
        console.print(other_table)

    console.print()


# ---------------------------------------------------------------------------
# Severity styling for audit findings
# ---------------------------------------------------------------------------

_AUDIT_SEVERITY_STYLE: dict[str, str] = {
    "HIGH": "bold red",
    "MEDIUM": "yellow",
    "LOW": "dim",
    "INFO": "dim",
}


# ---------------------------------------------------------------------------
# brain audit
# ---------------------------------------------------------------------------


@brain_app.command("audit")
def brain_audit(
    calibrate: bool = typer.Option(
        False, "--calibrate", help="Run statistical threshold calibration",
    ),
    lifecycle: bool = typer.Option(
        False, "--lifecycle", help="Analyze signal lifecycle transitions",
    ),
    html: bool = typer.Option(
        False, "--html", help="Generate institutional-quality HTML provenance report",
    ),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Output path for HTML report (default: output/brain_audit_report.html)",
    ),
) -> None:
    """Audit brain structural health: staleness, coverage, thresholds, orphans."""
    from datetime import UTC, datetime
    from pathlib import Path

    # HTML report mode -- does not require DuckDB
    if html:
        from do_uw.brain.brain_audit import generate_audit_html

        out_path = Path(output) if output else None
        result_path = generate_audit_html(output_path=out_path)
        console.print(
            f"\n[bold green]HTML audit report generated:[/bold green] {result_path}\n"
        )
        return

    from do_uw.brain.brain_audit import compute_brain_audit
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

    db_path = get_brain_db_path()
    if not db_path.exists():
        console.print(
            "[red]brain.duckdb not found.[/red] "
            "Run 'do-uw brain build' first."
        )
        raise typer.Exit(code=1)

    conn = connect_brain_db(db_path)
    try:
        report = compute_brain_audit(conn)

        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        # Header
        console.print()
        console.print(
            Panel(
                f"[dim]{now}[/dim]",
                title="[bold]Brain Audit Report[/bold]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

        # 1. Staleness section
        stale_table = Table(
            title="Signal Staleness",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold",
            padding=(0, 1),
        )
        stale_table.add_column("Category", width=24)
        stale_table.add_column("Signals", justify="right", width=10)

        stale_color = "yellow" if report.never_calibrated > 0 else "dim"
        stale_table.add_row(
            f"[{stale_color}]Never calibrated[/{stale_color}]",
            f"[{stale_color}]{report.never_calibrated}[/{stale_color}]",
        )

        vs_color = "red" if report.very_stale > 0 else "dim"
        stale_table.add_row(
            f"[{vs_color}]> 365 days[/{vs_color}]",
            f"[{vs_color}]{report.very_stale}[/{vs_color}]",
        )

        s_color = "yellow" if report.stale > 0 else "dim"
        stale_table.add_row(
            f"[{s_color}]180-365 days[/{s_color}]",
            f"[{s_color}]{report.stale}[/{s_color}]",
        )

        f_color = "green" if report.fresh > 0 else "dim"
        stale_table.add_row(
            f"[{f_color}]< 180 days (fresh)[/{f_color}]",
            f"[{f_color}]{report.fresh}[/{f_color}]",
        )

        console.print(stale_table)

        # 2. Coverage section
        if report.peril_coverage_available:
            # Show coverage findings
            cov_findings = [f for f in report.findings if f.category == "COVERAGE"]
            if cov_findings:
                cov_table = Table(
                    title="Peril Coverage Gaps",
                    show_header=True,
                    header_style="bold",
                    border_style="dim",
                    title_style="bold",
                    padding=(0, 1),
                )
                cov_table.add_column("Severity", width=10)
                cov_table.add_column("Finding", ratio=1)
                for finding in cov_findings:
                    style = _AUDIT_SEVERITY_STYLE.get(finding.severity, "")
                    cov_table.add_row(
                        f"[{style}]{finding.severity}[/{style}]",
                        finding.message,
                    )
                console.print(cov_table)
            else:
                console.print("[green]Peril coverage: adequate across all perils[/green]")
        else:
            # Peril coverage not available
            cov_msg = next(
                (f for f in report.findings if f.category == "COVERAGE"),
                None,
            )
            if cov_msg:
                console.print(f"[dim]{cov_msg.message}[/dim]")
            else:
                console.print("[dim]Peril coverage: no data[/dim]")

        # 3. Threshold conflicts section
        threshold_findings = [f for f in report.findings if f.category == "THRESHOLD"]
        if threshold_findings:
            th_table = Table(
                title="Threshold Conflicts",
                show_header=True,
                header_style="bold",
                border_style="dim",
                title_style="bold red",
                padding=(0, 1),
            )
            th_table.add_column("Signal ID", min_width=25)
            th_table.add_column("Issue", ratio=1)
            for finding in threshold_findings:
                th_table.add_row(
                    f"[yellow]{finding.signal_id}[/yellow]",
                    finding.message,
                )
            console.print(th_table)
        else:
            console.print("[green]No threshold conflicts detected[/green]")

        # 4. Orphaned signals section
        orphan_findings = [f for f in report.findings if f.category == "ORPHAN"]
        if orphan_findings:
            for finding in orphan_findings:
                console.print(f"[yellow]{finding.message}[/yellow]")
                if finding.detail:
                    console.print(f"[dim]{finding.detail}[/dim]")
        else:
            console.print("[green]All active signals are assigned to facets[/green]")

        # 5. Summary
        console.print()
        summary_style = (
            "green" if "No structural" in report.summary
            else "yellow" if "high" not in report.summary
            else "red"
        )
        console.print(
            Panel(
                f"[{summary_style}]{report.summary}[/{summary_style}]",
                title="[bold]Summary[/bold]",
                border_style="dim",
                padding=(0, 1),
            )
        )

        # 6. Calibration section (--calibrate flag)
        if calibrate:
            from do_uw.brain.brain_calibration import compute_calibration_report

            from do_uw.cli_brain_audit_display import (
                display_calibration_report,
                display_correlation_report,
            )

            console.print()
            cal_report = compute_calibration_report(conn)
            display_calibration_report(cal_report)

            # Correlation analysis (Plan 02 engine)
            from do_uw.brain.brain_correlation import compute_correlation_report

            console.print()
            cor_report = compute_correlation_report(conn)
            display_correlation_report(cor_report)

        # 7. do_context template validation (YAML-based, no DuckDB needed)
        try:
            from do_uw.brain.brain_unified_loader import load_signals as _load_signals_for_audit
            from do_uw.stages.analyze.do_context_engine import validate_do_context_template

            audit_signals_data = _load_signals_for_audit()
            audit_signals_list = audit_signals_data.get("signals", [])
            audit_total = len(audit_signals_list)
            audit_with_do_ctx = 0
            do_ctx_errors: list[tuple[str, str, list[str]]] = []

            for sig_item in audit_signals_list:
                pres = sig_item.get("presentation")
                if not isinstance(pres, dict):
                    continue
                do_ctx = pres.get("do_context", {})
                if not do_ctx:
                    continue
                audit_with_do_ctx += 1
                for status_key, tmpl in do_ctx.items():
                    if not isinstance(tmpl, str):
                        continue
                    issues = validate_do_context_template(tmpl)
                    if issues:
                        do_ctx_errors.append((sig_item.get("id", "?"), status_key, issues))

            if do_ctx_errors:
                err_table = Table(
                    title="do_context Template Errors",
                    show_header=True,
                    header_style="bold",
                    border_style="dim",
                    title_style="bold red",
                    padding=(0, 1),
                )
                err_table.add_column("Signal ID", min_width=25)
                err_table.add_column("Status Key", width=16)
                err_table.add_column("Issues", ratio=1)
                for sig_id, key, issues_list in do_ctx_errors:
                    err_table.add_row(
                        f"[yellow]{sig_id}[/yellow]",
                        key,
                        "; ".join(issues_list),
                    )
                console.print(err_table)
            else:
                console.print("[green]All do_context templates valid[/green]")

            audit_pct = (100 * audit_with_do_ctx / audit_total) if audit_total > 0 else 0
            console.print(
                f"[bold]do_context Coverage:[/bold] "
                f"{audit_with_do_ctx} / {audit_total} signals ({audit_pct:.0f}%)"
            )
        except Exception as exc:
            console.print(f"[dim]do_context audit failed: {exc}[/dim]")

        # 8. Lifecycle section (--lifecycle flag)
        if lifecycle:
            from do_uw.brain.brain_lifecycle_v2 import compute_lifecycle_proposals
            from do_uw.cli_brain_audit_display import display_lifecycle_report

            console.print()
            lc_report = compute_lifecycle_proposals(conn)
            display_lifecycle_report(lc_report)

    finally:
        conn.close()

    console.print()
