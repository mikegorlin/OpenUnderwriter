"""Display helpers for brain audit CLI output.

Split from cli_brain_health.py for file length compliance (<500 lines).
Contains Rich table/panel display functions for calibration, correlation,
and lifecycle reports.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Calibration report display
# ---------------------------------------------------------------------------


def display_calibration_report(report: object) -> None:
    """Display calibration report with Rich tables and panels."""
    from do_uw.brain.brain_calibration import CalibrationReport

    if not isinstance(report, CalibrationReport):
        console.print("[red]Invalid calibration report.[/red]")
        return

    # Threshold Drift Analysis table
    if report.drift_signals:
        drift_table = Table(
            title="Threshold Drift Analysis", show_header=True,
            header_style="bold", border_style="dim",
            title_style="bold red", padding=(0, 1),
        )
        drift_table.add_column("Signal ID", min_width=25)
        drift_table.add_column("Current", justify="right", width=10)
        drift_table.add_column("Observed", width=20)
        drift_table.add_column("N", justify="right", width=5)
        drift_table.add_column("Conf.", width=8)
        drift_table.add_column("Proposed", justify="right", width=10)

        for d in report.drift_signals:
            obs_str = (
                f"{d.observed_mean:.2f} +/- {d.observed_stdev:.2f}"
                if d.observed_mean is not None and d.observed_stdev is not None
                else "N/A"
            )
            drift_table.add_row(
                f"[red]{d.signal_id}[/red]",
                f"{d.current_threshold:.2f}" if d.current_threshold is not None else "N/A",
                obs_str,
                str(d.n),
                f"[{'green' if d.confidence == 'HIGH' else 'yellow' if d.confidence == 'MEDIUM' else 'dim'}]{d.confidence}[/]",
                f"[bold]{d.proposed_value:.2f}[/bold]" if d.proposed_value is not None else "N/A",
            )
        console.print(drift_table)
    else:
        console.print("[green]No threshold drift detected.[/green]")

    # Fire Rate Alerts table
    if report.fire_rate_alerts:
        alert_table = Table(
            title="Fire Rate Alerts", show_header=True,
            header_style="bold", border_style="dim",
            title_style="bold yellow", padding=(0, 1),
        )
        alert_table.add_column("Signal ID", min_width=25)
        alert_table.add_column("Fire Rate", justify="right", width=10)
        alert_table.add_column("Alert", width=16)
        alert_table.add_column("Recommendation", ratio=1)

        for a in report.fire_rate_alerts:
            alert_style = "red" if a.alert_type == "HIGH_FIRE_RATE" else "yellow"
            alert_table.add_row(
                f"[{alert_style}]{a.signal_id}[/{alert_style}]",
                f"{a.fire_rate:.1%}",
                f"[{alert_style}]{a.alert_type}[/{alert_style}]",
                a.recommendation,
            )
        console.print(alert_table)
    else:
        console.print("[green]No fire rate anomalies detected.[/green]")

    # Insufficient data count
    if report.insufficient_data:
        console.print(
            f"[dim]{len(report.insufficient_data)} signals with insufficient data "
            f"(N<5 runs, skipped for drift analysis)[/dim]"
        )

    # Summary panel
    console.print()
    console.print(
        Panel(
            f"Analyzed [bold]{report.total_signals_analyzed}[/bold] signals, "
            f"[bold]{report.total_with_numeric_values}[/bold] with numeric values, "
            f"[bold]{len(report.drift_signals)}[/bold] drift detected, "
            f"[bold]{len(report.fire_rate_alerts)}[/bold] fire rate alerts, "
            f"[bold]{report.total_proposals_generated}[/bold] proposals generated",
            title="[bold]Calibration Summary[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    if report.total_proposals_generated > 0:
        console.print(
            "[dim]Run 'do-uw brain apply-proposal <id>' to apply a "
            "calibration proposal.[/dim]"
        )


# ---------------------------------------------------------------------------
# Correlation report display
# ---------------------------------------------------------------------------


def display_correlation_report(report: object) -> None:
    """Display co-occurrence analysis with Rich tables."""
    from do_uw.brain.brain_correlation import CorrelationReport

    if not isinstance(report, CorrelationReport):
        console.print("[red]Invalid correlation report.[/red]")
        return

    if report.correlated_pairs:
        pair_table = Table(
            title="Co-occurrence Analysis", show_header=True,
            header_style="bold", border_style="dim",
            title_style="bold", padding=(0, 1),
        )
        pair_table.add_column("Signal A", min_width=20)
        pair_table.add_column("Signal B", min_width=20)
        pair_table.add_column("Co-fire", justify="right", width=8)
        pair_table.add_column("Rate", justify="right", width=8)
        pair_table.add_column("Type", width=20)

        for p in report.correlated_pairs[:20]:
            type_style = "yellow" if p.correlation_type == "potential_redundancy" else "cyan"
            pair_table.add_row(
                p.signal_a, p.signal_b,
                str(p.co_fire_count),
                f"{p.co_fire_rate:.1%}",
                f"[{type_style}]{p.correlation_type}[/{type_style}]",
            )
        console.print(pair_table)
    else:
        console.print("[green]No correlated signal pairs detected.[/green]")

    if report.redundancy_clusters:
        for cluster in report.redundancy_clusters:
            console.print(
                Panel(
                    f"[yellow]{cluster.recommendation}[/yellow]\n"
                    f"Signals: {', '.join(cluster.signal_ids)}",
                    title=f"[bold yellow]Redundancy Cluster: {cluster.prefix}[/bold yellow]",
                    border_style="yellow",
                    padding=(0, 1),
                )
            )

    redundancy_count = sum(
        1 for p in report.correlated_pairs
        if p.correlation_type == "potential_redundancy"
    )
    risk_count = len(report.correlated_pairs) - redundancy_count
    console.print(
        f"[dim]Analyzed {report.total_pairs_analyzed} pairs, "
        f"{report.above_threshold_count} above threshold "
        f"({redundancy_count} redundancy, {risk_count} risk correlation), "
        f"excluded {report.excluded_high_fire_rate} high-fire-rate signals, "
        f"{report.proposals_generated} proposals generated[/dim]"
    )
    if report.proposals_generated > 0:
        console.print(
            "[dim]Run 'do-uw brain apply-proposal <id>' to annotate "
            "signal YAML with correlated_signals.[/dim]"
        )


# ---------------------------------------------------------------------------
# Lifecycle report display
# ---------------------------------------------------------------------------


def display_lifecycle_report(report: object) -> None:
    """Display lifecycle analysis with Rich tables."""
    from do_uw.brain.brain_lifecycle_v2 import LifecycleReport

    if not isinstance(report, LifecycleReport):
        console.print("[red]Invalid lifecycle report.[/red]")
        return

    if report.by_state:
        dist_table = Table(
            title="Signal Lifecycle Analysis", show_header=True,
            header_style="bold", border_style="dim",
            title_style="bold", padding=(0, 1),
        )
        dist_table.add_column("State", width=16)
        dist_table.add_column("Count", justify="right", width=10)

        state_styles = {
            "INCUBATING": "dim", "ACTIVE": "green",
            "MONITORING": "yellow", "DEPRECATED": "red", "ARCHIVED": "dim",
        }
        for state, count in sorted(report.by_state.items()):
            style = state_styles.get(state, "")
            dist_table.add_row(
                f"[{style}]{state}[/{style}]",
                f"[{style}]{count}[/{style}]",
            )
        console.print(dist_table)

    if report.proposals:
        prop_table = Table(
            title="Transition Proposals", show_header=True,
            header_style="bold", border_style="dim",
            title_style="bold yellow", padding=(0, 1),
        )
        prop_table.add_column("Signal ID", min_width=25)
        prop_table.add_column("Current", width=12)
        prop_table.add_column("Proposed", width=12)
        prop_table.add_column("Confidence", width=10)
        prop_table.add_column("Reason", ratio=1)

        for p in report.proposals:
            conf_style = (
                "green" if p.confidence == "HIGH"
                else "yellow" if p.confidence == "MEDIUM"
                else "dim"
            )
            prop_table.add_row(
                p.signal_id,
                p.current_state.value,
                f"[bold]{p.proposed_state.value}[/bold]",
                f"[{conf_style}]{p.confidence}[/{conf_style}]",
                p.reason,
            )
        console.print(prop_table)
    else:
        console.print("[green]No lifecycle transitions proposed.[/green]")

    console.print(
        Panel(
            report.summary,
            title="[bold]Lifecycle Summary[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )
    if report.proposals:
        console.print(
            "[dim]Run 'do-uw brain apply-proposal <id>' to apply "
            "a lifecycle transition.[/dim]"
        )
