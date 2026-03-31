"""CLI entry point for Angry Dolphin Underwriting.

Provides the `angry-dolphin analyze <TICKER>` command with Rich-powered
progress display showing all 7 pipeline stages with status and timing.
Also registers the `knowledge` and `pricing` sub-apps.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from do_uw import __version__
from do_uw.cache import AnalysisCache
from do_uw.cli_brain import brain_app
from do_uw.cli_calibrate import calibrate_app
from do_uw.cli_dashboard import dashboard_app
from do_uw.cli_feedback import feedback_app
from do_uw.cli_ingest import ingest_app
from do_uw.cli_knowledge import knowledge_app
from do_uw.cli_pricing import pricing_app
from do_uw.cli_validate import validate_app
from do_uw.models.common import StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState
from do_uw.pipeline import Pipeline

app = typer.Typer(
    name="underwrite",
    help="Angry Dolphin Underwriting -- D&O Liability Worksheet",
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={
        "allow_interspersed_args": False,
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)


@app.callback(invoke_without_command=True)
def _app_init(
    ctx: typer.Context,
    fresh: bool = typer.Option(
        False, "--fresh", help="Delete cache and prior output, run from scratch"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    search_budget: int = typer.Option(
        10, "--search-budget", help="Maximum web searches per analysis"
    ),
    peers: str = typer.Option("", "--peers", help="Comma-separated override peer tickers"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM extraction"),
    review: bool = typer.Option(False, "--review", help="Run self-review audit after pipeline"),
    no_progress: bool = typer.Option(
        False, "--no-progress", help="Disable Rich progress bars (show plain logs)"
    ),
) -> None:  # pyright: ignore[reportUnusedFunction]
    """Load .env and ensure brain.duckdb is initialized before any command."""
    from dotenv import load_dotenv

    load_dotenv()

    # Ensure brain.duckdb is populated from signals.json on first use.
    # BrainDBLoader._get_conn() handles this lazily, but we want it ready
    # before any command runs so all commands (brain status, analyze, etc.)
    # work without manual migration steps.
    _ensure_brain_db()

    # If user ran `underwrite AAPL` with no subcommand, route to analyze.
    # Extra positional args land in ctx.args thanks to allow_extra_args.
    if ctx.invoked_subcommand is None and ctx.args:
        ticker = ctx.args[0]
        ctx.invoke(
            analyze,
            ticker=ticker,
            output=Path("output"),
            fresh=fresh,
            verbose=verbose,
            search_budget=search_budget,
            peers=peers,
            no_llm=no_llm,
            review=review,
            no_progress=no_progress,
        )
    elif ctx.invoked_subcommand is None:
        # No subcommand and no ticker — show help
        import click

        click.echo(ctx.get_help())


def _ensure_brain_db() -> None:
    """Ensure brain.duckdb is populated with schema and checks.

    Checks if brain.duckdb exists and has the brain_signals table with data.
    If empty or missing, runs migration from signals.json automatically.
    This is fast (~1s) and idempotent — safe to call on every CLI invocation.
    """
    import logging

    try:
        from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path

        db_path = get_brain_db_path()
        conn = connect_brain_db(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM brain_signals").fetchone()[0]
            if count == 0:
                raise ValueError("brain_signals table is empty")
        except Exception:
            logging.getLogger(__name__).info("Initializing brain.duckdb from signals.json")
            from do_uw.brain.brain_migrate import migrate_checks_to_brain

            migrate_checks_to_brain(conn=conn)
        finally:
            conn.close()
    except Exception as exc:
        logging.getLogger(__name__).warning("Brain DB auto-init failed (non-fatal): %s", exc)


app.add_typer(brain_app, name="brain")
app.add_typer(calibrate_app, name="calibrate")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(feedback_app, name="feedback")
app.add_typer(ingest_app, name="ingest")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(pricing_app, name="pricing")
app.add_typer(validate_app, name="validate")
console = Console(force_terminal=True)

# Status display symbols
_STATUS_SYMBOLS: dict[str, tuple[str, str]] = {
    "pending": ("...", "dim"),
    "running": (">>>", "yellow"),
    "completed": ("OK", "green"),
    "failed": ("FAIL", "red"),
    "skipped": ("SKIP", "dim"),
}


class RichCallbacks:
    """Pipeline callbacks that update a Rich table display."""

    def __init__(self) -> None:
        self._statuses: dict[str, str] = dict.fromkeys(PIPELINE_STAGES, "pending")
        self._durations: dict[str, float | None] = dict.fromkeys(PIPELINE_STAGES, None)
        self._detail: str = ""

    def on_stage_start(self, stage_name: str, index: int, total: int) -> None:
        """Mark stage as running and display table."""
        _ = (index, total)
        self._statuses[stage_name] = "running"
        self._display()

    def on_stage_complete(
        self,
        stage_name: str,
        index: int,
        total: int,
        duration: float | None,
    ) -> None:
        """Mark stage as completed and display table."""
        _ = (index, total)
        self._statuses[stage_name] = "completed"
        self._durations[stage_name] = duration
        self._detail = ""  # Clear substage detail on stage completion
        self._display()

    def on_stage_skip(self, stage_name: str, index: int, total: int) -> None:
        """Mark stage as skipped."""
        _ = (index, total)
        self._statuses[stage_name] = "skipped"

    def on_stage_fail(self, stage_name: str, index: int, total: int, error: str) -> None:
        """Mark stage as failed and display table."""
        _ = (index, total, error)
        self._statuses[stage_name] = "failed"
        self._detail = ""
        self._display()

    def on_substage_progress(self, message: str) -> None:
        """Update substage detail line and redisplay."""
        self._detail = message
        self._display()

    def _display(self) -> None:
        """Render the pipeline status table."""
        table = Table(
            title="Angry Dolphin Pipeline",
            show_header=True,
            header_style="bold",
        )
        table.add_column("#", width=3, justify="right")
        table.add_column("Stage", min_width=12)
        table.add_column("Status", width=8, justify="center")
        table.add_column("Duration", width=10, justify="right")

        for i, stage_name in enumerate(PIPELINE_STAGES, 1):
            status = self._statuses[stage_name]
            symbol, style = _STATUS_SYMBOLS.get(status, ("?", "dim"))
            duration = self._durations.get(stage_name)
            dur_str = f"{duration:.2f}s" if duration is not None else ""

            table.add_row(
                str(i),
                stage_name.upper(),
                f"[{style}]{symbol}[/{style}]",
                dur_str,
            )

        console.clear()
        console.print(table)
        if self._detail:
            console.print(f"  [dim]\u21b3 {self._detail}[/dim]")


def _sanitize_company_name(name: str) -> str:
    """Sanitize company name for filesystem use."""
    import re

    # Remove SEC-style state suffixes like /DE/, /NY/, /NV/
    clean = re.sub(r"/[A-Z]{2}/$", "", name)
    # Remove trailing Inc, Corp, Ltd suffixes for cleaner folder names
    clean = re.sub(r"\s*(,?\s*Inc\.?|,?\s*Corp\.?|,?\s*Ltd\.?)$", "", clean, flags=re.IGNORECASE)
    # Remove filesystem-unsafe chars
    clean = re.sub(r"[/\\:*?\"<>|]", "", clean)
    clean = clean.strip().rstrip(".")
    return clean[:80]


def _find_company_dir(output: Path, ticker: str) -> Path:
    """Find existing company folder matching ticker, or create ticker-only dir.

    Looks for dirs like 'RPM - RPM International Inc' matching the ticker prefix.
    Falls back to just the ticker name if no existing folder found.
    """
    if output.exists():
        for child in output.iterdir():
            if child.is_dir() and child.name.startswith(f"{ticker} - "):
                return child
            if child.is_dir() and child.name == ticker:
                return child
    return output / ticker


def _rename_to_company_dir(
    output: Path, ticker: str, company_name: str | None, output_dir: Path
) -> Path:
    """After RESOLVE, rename ticker-only folder to include company name.

    output/RPM/2026-03-18/ -> output/RPM - RPM International Inc/2026-03-18/
    """
    if not company_name:
        return output_dir
    clean_name = _sanitize_company_name(company_name)
    target_parent = output / f"{ticker} - {clean_name}"
    current_parent = output_dir.parent

    if current_parent == target_parent:
        return output_dir  # Already named correctly

    if current_parent.name == ticker and current_parent != target_parent:
        # Rename ticker-only dir to include company name
        try:
            current_parent.rename(target_parent)
            return target_parent / output_dir.name
        except OSError:
            return output_dir  # Keep original on rename failure

    return output_dir


def _load_or_create_state(ticker: str, output_dir: Path) -> AnalysisState:
    """Load existing state or create new one."""
    state_path = output_dir / "state.json"
    if state_path.exists():
        try:
            state = Pipeline.load_state(state_path)
            if state.ticker.upper() == ticker.upper():
                console.print(f"[yellow]Resuming analysis for {ticker.upper()}[/yellow]")
                return state
        except (ValueError, FileNotFoundError):
            pass  # Fall through to create new state

    return AnalysisState(ticker=ticker.upper())


@app.command("analyze")
def analyze(
    ticker: str = typer.Argument(help="Ticker or company name (e.g., AAPL, 'Apple Inc')"),
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Output directory for results",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    search_budget: int = typer.Option(
        50,
        "--search-budget",
        help="Maximum web searches per analysis (default 50)",
    ),
    peers: str = typer.Option(
        "",
        "--peers",
        help="Comma-separated override peer tickers (e.g., AAPL,MSFT,GOOG)",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Disable LLM extraction (regex-only mode)",
    ),
    fresh: bool = typer.Option(
        False,
        "--fresh",
        help="Delete cache and prior output, run from scratch",
    ),
    attachment: float | None = typer.Option(
        None,
        "--attachment",
        help="Liberty attachment point in dollars (e.g., 25000000 for $25M)",
    ),
    product: str | None = typer.Option(
        None,
        "--product",
        help="Liberty product type: ABC or SIDE_A",
    ),
    review: bool = typer.Option(
        False,
        "--review",
        help="Run self-review audit after pipeline and produce JSON quality report",
    ),
    no_progress: bool = typer.Option(
        False,
        "--no-progress",
        help="Disable Rich progress bars (show plain logs)",
    ),
) -> None:
    """Analyze a company for D&O underwriting."""
    import sys

    sys.stderr.write(f"ANALYZE ENTER: ticker={ticker}, fresh={fresh}, verbose={verbose}\n")
    sys.stderr.flush()
    import re as _re
    import shutil

    _ = verbose
    # Setup logging
    import logging
    import sys

    # Configure root logger to output to stderr with appropriate level
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("do_uw").info("Starting D&O analysis for %s", ticker)
    logging.getLogger("do_uw").info("no_progress=%s, verbose=%s", no_progress, verbose)
    sys.stderr.write(f"DEBUG: analyze starting for {ticker}\n")
    sys.stderr.flush()

    ticker = ticker.upper()
    # Find existing company folder (TICKER - Company Name) or use ticker-only
    # Single output directory — no dated subdirectories. Each run overwrites.
    company_dir = _find_company_dir(output, ticker)
    output_dir = company_dir

    # Fresh mode: reset pipeline stages but PRESERVE filing cache.
    # SEC filings don't change — re-downloading wastes time and API calls.
    # Only delete the LLM extraction cache (forces re-extraction with new code)
    # and the output directory (forces re-render).
    if fresh:
        # PRESERVE: .cache/analysis.db — filing metadata + XBRL data is expensive to re-fetch
        # This means SEC filings, Company Facts XBRL, yfinance history remain cached.
        console.print("[green]Preserving filing cache (.cache/analysis.db)[/green]")
        # Clear LLM extraction cache — forces re-extraction with latest prompts/code
        llm_cache_path = Path(".cache/llm_extractions.db")
        if llm_cache_path.exists():
            llm_cache_path.unlink()
            console.print("[yellow]Deleted LLM extraction cache (will re-extract)[/yellow]")
        # Clear ticker output directory — forces full re-run of all stages
        if output_dir.exists():
            shutil.rmtree(output_dir)
            console.print(f"[yellow]Deleted output directory: {output_dir}[/yellow]")
        else:
            console.print(f"[yellow]Output directory does not exist: {output_dir}[/yellow]")

    # Parse peer tickers
    peer_list: list[str] | None = None
    if peers.strip():
        peer_list = [t.strip().upper() for t in peers.split(",") if t.strip()]

    console.print(f"\n[bold]Angry Dolphin -- D&O Analysis: {ticker}[/bold]\n")

    # Initialize web search function.
    from do_uw.stages.acquire.clients.serper_client import (
        create_serper_search_fn,
    )

    cli_logger = logging.getLogger("do_uw.cli")
    search_fn, search_status = create_serper_search_fn()
    if search_fn is not None:
        console.print(f"[green]{search_status}[/green]")
    else:
        console.print(f"[bold red]{search_status}[/bold red]")
        cli_logger.warning(
            "SERPER_API_KEY not set -- blind spot detection DISABLED. "
            "Worksheet will include a Data Quality Notice warning. "
            "Set SERPER_API_KEY to enable web-based risk discovery."
        )

    # Initialize cache (ensures database exists)
    cache = AnalysisCache()
    cache_stats = cache.stats()
    console.print(f"[dim]Cache: {cache.db_path} ({cache_stats['valid']} entries)[/dim]\n")

    # Load or create state
    state = _load_or_create_state(ticker, output_dir)

    # Show initial stage statuses
    pending_count = sum(1 for s in state.stages.values() if s.status == StageStatus.PENDING)
    completed_count = sum(1 for s in state.stages.values() if s.status == StageStatus.COMPLETED)
    if completed_count > 0:
        console.print(f"[dim]{completed_count} stages complete, {pending_count} remaining[/dim]\n")

    # Run pipeline
    from do_uw.pipeline import NullCallbacks

    if no_progress:
        callbacks = NullCallbacks()
        progress_fn = None
    else:
        callbacks = RichCallbacks()
        progress_fn = callbacks.on_substage_progress

    pipeline = Pipeline(
        output_dir=output_dir,
        callbacks=callbacks,
        pipeline_config={
            "search_budget": search_budget,
            "search_fn": search_fn,
            "peers": peer_list,
            "no_llm": no_llm,
            "progress_fn": progress_fn,
            "liberty_attachment": attachment,
            "liberty_product": product,
        },
    )

    state = pipeline.run(state)  # Never raises PipelineError anymore

    # Check for failed stages and warn
    failed_stages = [
        (name, result)
        for name, result in state.stages.items()
        if result.status == StageStatus.FAILED
    ]

    # After pipeline, rename folder to include company name if we learned it
    company_name = None
    if state.company and state.company.identity and state.company.identity.legal_name:
        ln = state.company.identity.legal_name
        company_name = ln.value if hasattr(ln, "value") else str(ln)
    output_dir = _rename_to_company_dir(output, ticker, company_name, output_dir)

    if failed_stages:
        console.print()
        for stage_name, result in failed_stages:
            console.print(
                f"[yellow]WARNING: Stage {stage_name} failed: "
                f"{result.error or 'unknown error'}[/yellow]"
            )

    # Check if HTML was produced
    html_files = list(output_dir.glob("*_worksheet.html"))
    if html_files:
        console.print("\n[bold green]Analysis complete![/bold green]")
        if failed_stages:
            console.print(
                f"[dim]({len(failed_stages)} stage(s) had errors -- "
                f"see worksheet audit section)[/dim]"
            )
        console.print(f"[dim]State saved to {output_dir / 'state.json'}[/dim]")

        # Post-pipeline QA verification
        try:
            from do_uw.validation.qa_report import run_qa_verification
            from do_uw.validation.qa_report_generator import print_qa_report

            qa_report = run_qa_verification(state, output_dir)
            print_qa_report(qa_report)
        except Exception:
            console.print("[yellow]QA verification skipped due to error[/yellow]")

        # Post-pipeline signal health summary with anomaly detection
        try:
            from do_uw.validation.health_summary import (
                compute_health_summary,
                print_health_summary,
            )

            health = compute_health_summary(state)
            print_health_summary(health)
        except Exception:
            console.print("[yellow]Health summary skipped due to error[/yellow]")

        # Self-review audit (REVIEW-03: --review flag)
        if review:
            from do_uw.stages.render.self_review import (
                print_review_summary,
                run_self_review,
                write_review_report,
            )

            if html_files:
                review_report = run_self_review(html_files[0], state)
                report_path = write_review_report(review_report, output_dir)
                print_review_summary(review_report)
                console.print(f"[dim]Review report: {report_path}[/dim]")
            else:
                console.print("[yellow]No HTML worksheet found for self-review[/yellow]")
    else:
        console.print("\n[bold red]Pipeline failed -- no HTML output produced[/bold red]")
        raise typer.Exit(code=1)


@app.command("version")
def version() -> None:
    """Show do-uw version."""
    console.print(f"Angry Dolphin Underwriting {__version__}")
