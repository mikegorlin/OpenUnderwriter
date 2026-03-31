"""CLI sub-commands for document ingestion.

Provides commands for analyzing external documents for D&O intelligence:
- ``do-uw ingest file <path>`` -- analyze a local document
- ``do-uw ingest url <url>`` -- fetch and analyze a URL

Registered as a Typer sub-app in cli.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

ingest_app = typer.Typer(
    name="ingest",
    help="Document ingestion: analyze external documents for D&O intelligence",
    no_args_is_help=True,
)
console = Console()

# File extensions that are likely to contain readable text
_KNOWN_TEXT_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf", ".csv", ".json"}


def _display_impact_report(
    report: Any,  # IngestionImpactReport
    result: Any,  # DocumentIngestionResult
) -> None:
    """Display the ingestion impact report using Rich formatting."""
    console.print()
    console.print(
        f"[bold]Document Ingestion Report[/bold]: {report.document_name}"
    )
    console.print(f"[dim]Type: {report.document_type}[/dim]")
    console.print(f"[dim]Confidence: {result.confidence}[/dim]")
    console.print()

    # Company affected
    if result.company_ticker:
        console.print(
            f"[bold]Company:[/bold] {result.company_ticker} "
            f"(scope: {result.industry_scope})"
        )

    # Event summary
    console.print(f"\n[bold]Event:[/bold] {result.event_type}")
    console.print(result.event_summary)

    # D&O implications
    if result.do_implications:
        console.print(f"\n[bold]D&O Implications ({len(result.do_implications)}):[/bold]")
        for impl in result.do_implications:
            console.print(f"  [yellow]*[/yellow] {impl}")

    # Affected checks
    if result.affected_checks:
        console.print()
        table = Table(title="Affected Existing Checks")
        table.add_column("Check ID", min_width=20)
        for signal_id in result.affected_checks:
            table.add_row(signal_id)
        console.print(table)

    # Gap analysis
    if result.gap_analysis.strip():
        console.print("\n[bold]Gap Analysis:[/bold]")
        console.print(f"  {result.gap_analysis}")

    # Proposed new checks
    if result.proposed_new_checks:
        console.print()
        table = Table(title="Proposed New Checks")
        table.add_column("Check ID", min_width=20)
        table.add_column("Name", min_width=25)
        table.add_column("Threshold (Red)", min_width=20)
        for proposal in result.proposed_new_checks:
            table.add_row(
                proposal.signal_id,
                proposal.name,
                proposal.threshold_red or "-",
            )
        console.print(table)

    # Summary line
    console.print()
    console.print(
        f"[bold]Summary:[/bold] "
        f"{report.checks_affected} checks affected, "
        f"{report.gaps_found} gap(s) found, "
        f"{report.proposals_generated} proposal(s) generated"
    )


# ---------------------------------------------------------------------------
# ingest file
# ---------------------------------------------------------------------------


@ingest_app.command("file")
def ingest_file(
    path: Path = typer.Argument(
        help="Path to the document file to ingest",
    ),
    doc_type: str = typer.Option(
        "GENERAL",
        "--type",
        "-t",
        help="Document type: GENERAL, SHORT_SELLER_REPORT, CLAIMS_STUDY, etc.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply/--no-apply",
        help="Store proposals in the brain (default: dry-run)",
    ),
) -> None:
    """Analyze a local document for D&O underwriting intelligence."""
    from do_uw.knowledge.ingestion_llm import (
        extract_document_intelligence,
        generate_impact_report,
        store_proposals,
    )

    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(code=1)

    # Warn on unusual extensions
    if path.suffix.lower() not in _KNOWN_TEXT_EXTENSIONS:
        console.print(
            f"[yellow]Warning: extension '{path.suffix}' is unusual. "
            f"Attempting to read as text.[/yellow]"
        )

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        console.print(
            f"[red]Cannot read file as UTF-8 text: {path}[/red]"
        )
        raise typer.Exit(code=1)

    if not text.strip():
        console.print("[yellow]File is empty.[/yellow]")
        raise typer.Exit(code=1)

    console.print(
        f"[dim]Analyzing {path.name} ({len(text):,} chars)...[/dim]"
    )

    result = extract_document_intelligence(text, doc_type)
    report = generate_impact_report(result, path.name, doc_type)

    _display_impact_report(report, result)

    if apply:
        _apply_proposals(result, path.name, store_proposals)
    else:
        if result.proposed_new_checks:
            console.print(
                "\n[dim]Run with --apply to store proposals in the brain[/dim]"
            )


# ---------------------------------------------------------------------------
# ingest url
# ---------------------------------------------------------------------------


@ingest_app.command("url")
def ingest_url(
    url: str = typer.Argument(
        help="URL to fetch and analyze for D&O intelligence",
    ),
    doc_type: str = typer.Option(
        "GENERAL",
        "--type",
        "-t",
        help="Document type: GENERAL, SHORT_SELLER_REPORT, CLAIMS_STUDY, etc.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply/--no-apply",
        help="Store proposals in the brain (default: dry-run)",
    ),
) -> None:
    """Fetch a URL and analyze its content for D&O underwriting intelligence."""
    import httpx

    from do_uw.knowledge.ingestion_llm import (
        extract_document_intelligence,
        fetch_url_content,
        generate_impact_report,
        store_proposals,
    )

    console.print(f"[dim]Fetching {url}...[/dim]")

    try:
        text = fetch_url_content(url)
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to fetch URL: {exc}[/red]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Error fetching URL: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if not text.strip():
        console.print("[yellow]URL returned empty content.[/yellow]")
        raise typer.Exit(code=1)

    # Extract a display name from the URL
    from urllib.parse import urlparse

    parsed = urlparse(url)
    doc_name = parsed.path.split("/")[-1] or parsed.netloc

    console.print(
        f"[dim]Analyzing content from {doc_name} ({len(text):,} chars)...[/dim]"
    )

    result = extract_document_intelligence(text, doc_type)
    report = generate_impact_report(result, doc_name, doc_type)

    _display_impact_report(report, result)

    if apply:
        _apply_proposals(result, doc_name, store_proposals)
    else:
        if result.proposed_new_checks:
            console.print(
                "\n[dim]Run with --apply to store proposals in the brain[/dim]"
            )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _apply_proposals(
    result: Any,
    doc_name: str,
    store_proposals_fn: Any,
) -> None:
    """Store proposals in the brain via BrainWriter."""
    from do_uw.brain.brain_writer import BrainWriter

    writer = BrainWriter()
    try:
        count = store_proposals_fn(writer, result, doc_name)
        console.print(
            f"\n[green]Stored {count} proposal(s) in brain "
            f"(INCUBATING status)[/green]"
        )
    except Exception as exc:
        console.print(f"[red]Failed to store proposals: {exc}[/red]")
    finally:
        writer.close()
