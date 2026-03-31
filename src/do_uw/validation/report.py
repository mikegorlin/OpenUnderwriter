"""Validation report data structures and output formatting.

Provides dataclasses for storing per-ticker results and summary
statistics, with both Rich console display and JSON serialization.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class TickerResult:
    """Result of running the pipeline on a single ticker."""

    status: str  # "PASS" or "FAIL"
    duration_seconds: float
    cost_usd: float = 0.0
    error: str | None = None
    failed_stage: str | None = None


@dataclass
class ReportSummary:
    """Aggregate statistics for a validation run."""

    total: int
    passed: int
    failed: int
    total_cost_usd: float
    avg_duration_seconds: float


@dataclass
class ValidationReport:
    """Complete report for a multi-ticker validation run."""

    run_date: str
    results: dict[str, TickerResult] = field(
        default_factory=lambda: dict[str, TickerResult]()
    )
    summary: ReportSummary = field(
        default_factory=lambda: ReportSummary(
            total=0, passed=0, failed=0, total_cost_usd=0.0, avg_duration_seconds=0.0
        )
    )


def compute_summary(results: dict[str, TickerResult]) -> ReportSummary:
    """Compute summary statistics from per-ticker results.

    Args:
        results: Map of ticker -> TickerResult.

    Returns:
        Computed ReportSummary.
    """
    total = len(results)
    passed = sum(1 for r in results.values() if r.status == "PASS")
    failed = total - passed
    total_cost = sum(r.cost_usd for r in results.values())
    durations = [r.duration_seconds for r in results.values()]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    return ReportSummary(
        total=total,
        passed=passed,
        failed=failed,
        total_cost_usd=round(total_cost, 2),
        avg_duration_seconds=round(avg_duration, 1),
    )


def print_report(report: ValidationReport) -> None:
    """Display a validation report as a Rich console table.

    Args:
        report: The validation report to display.
    """
    console = Console()
    table = Table(
        title="Angry Dolphin Validation Report",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Ticker", min_width=6)
    table.add_column("Status", width=6, justify="center")
    table.add_column("Duration", width=10, justify="right")
    table.add_column("Cost", width=8, justify="right")
    table.add_column("Error", min_width=20)

    for ticker, result in sorted(report.results.items()):
        status_style = "green" if result.status == "PASS" else "red"
        dur_str = f"{result.duration_seconds:.1f}s"
        cost_str = f"${result.cost_usd:.2f}"
        error_str = result.error or ""
        # Truncate long errors for table display
        if len(error_str) > 60:
            error_str = error_str[:57] + "..."

        table.add_row(
            ticker,
            f"[{status_style}]{result.status}[/{status_style}]",
            dur_str,
            cost_str,
            error_str,
        )

    console.print(table)

    # Print summary line
    s = report.summary
    console.print(
        f"\n[bold]Summary:[/bold] {s.passed}/{s.total} passed, "
        f"{s.failed} failed, "
        f"${s.total_cost_usd:.2f} total cost, "
        f"{s.avg_duration_seconds:.1f}s avg duration"
    )


def save_report(report: ValidationReport, path: Path) -> None:
    """Serialize a validation report to a JSON file.

    Args:
        report: The validation report to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_report(path: Path) -> ValidationReport:
    """Deserialize a validation report from a JSON file.

    Args:
        path: Path to the JSON report file.

    Returns:
        Deserialized ValidationReport.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file content is invalid.
    """
    if not path.exists():
        msg = f"Report file not found: {path}"
        raise FileNotFoundError(msg)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        results = {
            ticker: TickerResult(**data)
            for ticker, data in raw.get("results", {}).items()
        }
        summary_data = raw.get("summary", {})
        summary = ReportSummary(**summary_data) if summary_data else compute_summary(results)
        return ValidationReport(
            run_date=raw.get("run_date", ""),
            results=results,
            summary=summary,
        )
    except Exception as exc:
        msg = f"Invalid report file {path}: {exc}"
        raise ValueError(msg) from exc
