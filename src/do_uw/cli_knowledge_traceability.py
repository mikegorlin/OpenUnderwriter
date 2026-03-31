"""CLI sub-commands for traceability audit operations.

Provides commands for auditing the 5-link traceability chain
on check results:
- `do-uw knowledge trace audit <ticker>` -- audit traceability completeness

Registered as a Typer sub-app on knowledge_app in cli_knowledge.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from do_uw.stages.analyze.signal_results import SignalResult

traceability_app = typer.Typer(
    name="trace",
    help="Traceability chain audit tools",
    no_args_is_help=True,
)
console = Console()

_TRACE_FIELDS = [
    "trace_data_source",
    "trace_extraction",
    "trace_evaluation",
    "trace_output",
    "trace_scoring",
]

_TRACE_LABELS = {
    "trace_data_source": "DATA_SOURCE",
    "trace_extraction": "EXTRACTION",
    "trace_evaluation": "EVALUATION",
    "trace_output": "OUTPUT",
    "trace_scoring": "SCORING",
}


def _load_signal_results_from_state(
    state_path: Path,
) -> list[SignalResult]:
    """Load SignalResult objects from a state.json file."""
    with open(state_path) as f:
        state_data = json.load(f)

    analysis = state_data.get("analysis")
    if not analysis:
        return []

    raw_results: dict[str, Any] = analysis.get("signal_results", {})
    results: list[SignalResult] = []
    for _signal_id, result_dict in raw_results.items():
        try:
            results.append(SignalResult.model_validate(result_dict))
        except Exception:
            continue
    return results


def _find_state_file(ticker: str) -> Path | None:
    """Find the most recent state.json for a ticker."""
    output_dir = Path("output") / ticker.upper()
    state_path = output_dir / "state.json"
    if state_path.exists():
        return state_path
    return None


def _audit_results(results: list[SignalResult]) -> dict[str, Any]:
    """Compute traceability audit statistics."""
    total = len(results)
    fully_traced = 0
    partially_traced = 0
    no_trace = 0
    gap_counts: dict[str, int] = dict.fromkeys(_TRACE_LABELS.values(), 0)
    gap_examples: dict[str, list[str]] = {label: [] for label in _TRACE_LABELS.values()}

    for r in results:
        gaps = r.traceability_gaps
        if not gaps:
            fully_traced += 1
        elif len(gaps) == 5:
            no_trace += 1
        else:
            partially_traced += 1

        for gap in gaps:
            gap_counts[gap] = gap_counts.get(gap, 0) + 1
            examples = gap_examples.get(gap, [])
            if len(examples) < 3:
                examples.append(r.signal_id)
                gap_examples[gap] = examples

    return {
        "total": total,
        "fully_traced": fully_traced,
        "partially_traced": partially_traced,
        "no_trace": no_trace,
        "gap_counts": gap_counts,
        "gap_examples": gap_examples,
    }


@traceability_app.command("audit")
def traceability_audit(
    ticker: str = typer.Argument(help="Ticker to audit"),
    state_file: Path | None = typer.Option(
        None, "--state", "-s", help="Path to state.json file"
    ),
) -> None:
    """Audit traceability chain completeness for check results.

    Loads the latest analysis state for a ticker (or from a provided
    state file) and reports which check results have complete vs
    incomplete traceability chains.

    Exit code 0 if all complete, exit code 1 if any gaps.
    """
    ticker = ticker.upper()

    # Resolve state file
    if state_file is not None:
        if not state_file.exists():
            console.print(f"[red]State file not found: {state_file}[/red]")
            raise typer.Exit(code=1)
        path = state_file
    else:
        path = _find_state_file(ticker)
        if path is None:
            # Fall back: run checks against brain definitions to audit trace population
            console.print(
                f"[yellow]No state file found for {ticker}.[/yellow]"
            )
            console.print(
                "[dim]Run 'do-uw analyze' first, or use --state <path>.[/dim]"
            )
            console.print(
                "\n[dim]Running trace audit against brain check definitions...[/dim]\n"
            )
            _audit_brain_signals()
            return

    # Load results
    results = _load_signal_results_from_state(path)
    if not results:
        console.print(
            f"[yellow]No check results found in {path}[/yellow]"
        )
        raise typer.Exit(code=1)

    # Audit
    audit = _audit_results(results)
    _display_audit(ticker, audit, source=str(path))

    # Exit code based on completeness
    if audit["fully_traced"] < audit["total"]:
        raise typer.Exit(code=1)


def _audit_brain_signals() -> None:
    """Run trace audit against brain check definitions (no state needed).

    Evaluates all AUTO signals with empty data to verify that the
    check engine populates trace fields from check definitions.
    """
    from do_uw.brain.brain_unified_loader import BrainLoader
    from do_uw.models.state import ExtractedData
    from do_uw.stages.analyze.signal_engine import execute_signals

    loader = BrainLoader()
    brain = loader.load_all()
    raw_checks = brain.checks.get("signals", [])

    # Run with empty extracted data -- all checks will SKIP but trace fields
    # should still be populated from definitions
    extracted = ExtractedData()
    results = execute_signals(raw_checks, extracted)

    audit = _audit_results(results)
    _display_audit("BRAIN_CHECKS", audit, source="brain/signals.json (empty data)")


def _display_audit(
    label: str,
    audit: dict[str, Any],
    source: str = "",
) -> None:
    """Display audit results as Rich tables and panels."""
    total = audit["total"]
    fully = audit["fully_traced"]
    partial = audit["partially_traced"]
    none_ = audit["no_trace"]

    pct = fully / total * 100 if total > 0 else 0
    color = "green" if pct == 100 else "yellow" if pct > 50 else "red"

    summary = (
        f"[bold]Traceability Audit: {label}[/bold]\n"
        f"Source: {source}\n\n"
        f"Total checks: {total}\n"
        f"[{color}]Fully traced: {fully} ({pct:.1f}%)[/{color}]\n"
        f"Partially traced: {partial}\n"
        f"No trace: {none_}"
    )
    console.print(Panel(summary, title="Summary"))

    # Gap breakdown table
    gap_counts = audit["gap_counts"]
    gap_examples = audit["gap_examples"]
    if any(v > 0 for v in gap_counts.values()):
        table = Table(title="Missing Traceability Links")
        table.add_column("Link", min_width=15)
        table.add_column("Missing", justify="right")
        table.add_column("% Missing", justify="right")
        table.add_column("Example Check IDs")
        for link, count in sorted(
            gap_counts.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                pct_missing = count / total * 100 if total > 0 else 0
                examples = gap_examples.get(link, [])
                table.add_row(
                    link,
                    str(count),
                    f"{pct_missing:.1f}%",
                    ", ".join(examples[:3]),
                )
        console.print(table)
    else:
        console.print(
            "[green]All traceability chains complete.[/green]"
        )


__all__ = ["traceability_app"]
