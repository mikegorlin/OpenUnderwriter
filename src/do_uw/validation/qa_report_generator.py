"""QA report formatting and output generation.

Split from qa_report.py (Phase 45, 500-line rule).

Contains the report printing/formatting function:
- print_qa_report: Rich-formatted QA report table output
"""

from __future__ import annotations

from do_uw.validation.qa_report import QAReport


def print_qa_report(report: QAReport) -> None:
    """Print QA report as a Rich table to console."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Grade color
    grade_color = {
        "PASS": "bold green",
        "WARN": "bold yellow",
        "FAIL": "bold red",
    }.get(report.grade, "bold")

    console.print()
    console.print(
        f"[bold]QA Verification: {report.ticker}[/bold]  "
        f"[{grade_color}]{report.grade}[/{grade_color}]  "
        f"({report.pass_count} pass, {report.warn_count} warn, {report.fail_count} fail)"
    )

    table = Table(show_header=True, header_style="bold", padding=(0, 1))
    table.add_column("", width=4, justify="center")
    table.add_column("Category", width=10)
    table.add_column("Check", width=26)
    table.add_column("Value", width=10, justify="right")
    table.add_column("Detail", min_width=30)

    status_icons = {"PASS": "[green]OK[/green]", "WARN": "[yellow]!![/yellow]", "FAIL": "[red]XX[/red]"}

    for check in report.checks:
        icon = status_icons.get(check.status, "??")
        table.add_row(
            icon,
            check.category,
            check.name,
            check.value,
            check.detail,
        )

    console.print(table)
    console.print()
