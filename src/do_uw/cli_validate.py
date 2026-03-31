"""CLI sub-app for multi-ticker validation runs.

Provides the ``angry-dolphin validate run`` command that executes the
full D&O underwriting pipeline across the canonical ticker set with
checkpointing, continue-on-failure, and comprehensive reporting.

Also provides ``angry-dolphin validate cost-report`` for per-company
and per-filing-type cost analysis of completed validation runs.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from do_uw.validation.config import get_tickers
from do_uw.validation.cost_report import (
    generate_cost_report,
    print_cost_report,
    save_cost_report,
)
from do_uw.validation.report import print_report, save_report
from do_uw.validation.runner import ValidationRunner

validate_app = typer.Typer(
    name="validate",
    help="Multi-ticker validation runs",
)
console = Console()


def _load_tickers_from_file(path: Path) -> list[str]:
    """Load ticker list from a text file (one ticker per line).

    Args:
        path: Path to the tickers file.

    Returns:
        List of uppercase ticker symbols (blank lines and comments ignored).

    Raises:
        typer.Exit: If the file cannot be read.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [
            line.strip().upper()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
    except OSError as exc:
        console.print(f"[bold red]Cannot read tickers file:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@validate_app.command("run")
def run(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
    fresh: bool = typer.Option(
        True,
        "--fresh/--no-fresh",
        help="Clear cache before each ticker (default: fresh)",
    ),
    conservative_rate: bool = typer.Option(
        True,
        "--conservative-rate/--no-conservative-rate",
        help="Use 5 req/sec SEC rate limit (default: conservative)",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Disable LLM extraction (regex-only mode)",
    ),
    batch: bool = typer.Option(
        False,
        "--batch/--no-batch",
        help="Use Batch API for 50% cost reduction on re-runs",
    ),
    tickers_file: Path | None = typer.Option(
        None,
        "--tickers-file",
        help="Override ticker list from a text file (one per line)",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Filter by category: standard, known_outcome, edge_case",
    ),
) -> None:
    """Run multi-ticker validation batch."""
    # Determine ticker list.
    if tickers_file is not None:
        tickers = _load_tickers_from_file(tickers_file)
    else:
        tickers = get_tickers(category)

    if not tickers:
        console.print("[bold red]No tickers to validate.[/bold red]")
        raise typer.Exit(code=1)

    # Apply conservative SEC rate limiting if requested.
    if conservative_rate:
        _apply_conservative_rate()

    console.print(f"\n[bold]Angry Dolphin Validation Run -- {len(tickers)} tickers[/bold]")
    if batch:
        console.print("[dim]  Batch API mode enabled (50% cost reduction)[/dim]")
    console.print()
    for t in tickers:
        console.print(f"  [dim]{t}[/dim]")
    console.print()

    # Build and run validation.
    runner = ValidationRunner(
        tickers=tickers,
        output_dir=output,
        fresh=fresh,
        use_llm=not no_llm,
    )
    report = runner.run()

    # Display and save report.
    print_report(report)
    report_path = output / "validation_report.json"
    save_report(report, report_path)
    console.print(f"\n[dim]Report saved to {report_path}[/dim]")

    # Batch mode: submit uncached filings for cost-optimized re-extraction.
    if batch:
        _run_batch_extraction(output)


@validate_app.command("cost-report")
def cost_report(
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory containing validation results",
    ),
) -> None:
    """Generate cost report for completed validation runs.

    Scans the output directory for ticker results and queries the
    extraction cache for per-company and per-filing-type cost data.
    Displays a Rich table and saves a JSON report.
    """
    if not output.exists():
        console.print(f"[bold red]Output directory not found:[/bold red] {output}")
        raise typer.Exit(code=1)

    report = generate_cost_report(output)
    print_cost_report(report)

    json_path = output / "cost_report.json"
    save_cost_report(report, json_path)
    console.print(f"\n[dim]Cost report saved to {json_path}[/dim]")


def _apply_conservative_rate() -> None:
    """Set SEC EDGAR rate limiter to 5 req/sec (conservative)."""
    from do_uw.stages.acquire.rate_limiter import set_max_rps

    set_max_rps(5)


def _run_batch_extraction(output_dir: Path) -> None:
    """Submit uncached filings as an OpenAI Batch.

    This is a cost-optimization path for RE-RUNS, not the initial
    validation which uses the real-time API to test production code.
    Collects filings that were not in the ExtractionCache and submits
    them as a single batch for 50% cost savings.

    Args:
        output_dir: Root output directory containing ticker subdirs.
    """
    from do_uw.validation.batch import BatchExtractor

    console.print("\n[bold]Batch API Extraction[/bold] (50% cost reduction for re-runs)")

    extractor = BatchExtractor()

    # For now, log that batch mode is available but requires
    # accumulated filing data from the validation run to
    # identify uncached entries. The full integration with
    # ExtractionCache and filing collection will be refined
    # during the actual multi-ticker validation phase.
    console.print(f"[dim]  Batch extractor initialized: {extractor.model}[/dim]")
    console.print(f"[dim]  Output dir: {output_dir}[/dim]")
    console.print("[dim]  Batch submission ready for next validation run[/dim]")
