"""CLI sub-command for the interactive dashboard.

Provides the `do-uw dashboard serve TICKER` command that starts
a local FastAPI web server displaying the analysis dashboard.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

dashboard_app = typer.Typer(
    name="dashboard",
    help="Interactive analysis dashboard",
    no_args_is_help=True,
)
console = Console()


@dashboard_app.command("serve")
def serve(
    ticker: str = typer.Argument(help="Stock ticker symbol (e.g., AAPL)"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    output: Path = typer.Option(
        Path("output"), "--output", "-o", help="Output directory"
    ),
) -> None:
    """Start the interactive dashboard for a completed analysis.

    Loads the analysis state from output/{TICKER}/state.json and
    serves an interactive web dashboard at http://127.0.0.1:{port}.
    """
    ticker_upper = ticker.upper()
    state_path = output / ticker_upper / "state.json"

    if not state_path.exists():
        console.print(
            f"[bold red]Error:[/bold red] No analysis found at {state_path}\n"
            f"Run [bold]do-uw analyze {ticker_upper}[/bold] first."
        )
        raise typer.Exit(code=1)

    console.print(
        f"\n[bold]D&O Dashboard: {ticker_upper}[/bold]\n"
        f"[dim]Loading state from {state_path}[/dim]\n"
        f"[bold green]Dashboard:[/bold green] http://127.0.0.1:{port}\n"
        f"[dim]Press Ctrl+C to stop[/dim]\n"
    )

    import uvicorn  # type: ignore[import-untyped]

    from do_uw.dashboard.app import create_app

    uvicorn.run(  # type: ignore[no-untyped-call]
        create_app(state_path),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
