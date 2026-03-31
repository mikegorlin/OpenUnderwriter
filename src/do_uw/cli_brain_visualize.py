"""brain visualize -- Interactive dependency graph visualization.

Generates a self-contained HTML file with a D3.js force-directed graph
showing all brain signals and their dependency edges. Filterable by
section, signal_class, and group.

Registered via cli_brain.py import.
"""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from do_uw.cli_brain import brain_app

console = Console()

_TEMPLATES_DIR = Path(__file__).resolve().parent / "brain" / "templates"


@brain_app.command("visualize")
def visualize(
    output: str = typer.Option(
        "output/brain_dependency_graph.html",
        "--output",
        "-o",
        help="Output path for the HTML visualization",
    ),
    section: str = typer.Option(
        "",
        "--section",
        "-s",
        help="Filter by report section (company, financial, governance, litigation, market)",
    ),
    signal_type: str = typer.Option(
        "",
        "--type",
        "-t",
        help="Filter by signal_class: foundational, evaluative, inference",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="Auto-open the generated file in default browser",
    ),
) -> None:
    """Generate an interactive D3.js dependency graph of brain signals."""
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.dependency_graph import generate_graph_data

    # Load signals
    signals_data = load_signals()
    signals = signals_data.get("signals", [])

    # Generate graph data
    graph_data = generate_graph_data(
        signals,
        section_filter=section,
        type_filter=signal_type,
    )

    # Render template
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
    )
    template = env.get_template("dependency_graph.html")
    html = template.render(graph_data=json.dumps(graph_data))

    # Write output
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    # Console summary
    stats = graph_data["stats"]
    console.print(f"\n[bold]Brain Dependency Graph[/bold]")
    console.print(f"  Nodes: [bold]{stats['total_nodes']}[/bold]")
    console.print(f"  Edges: [bold]{stats['total_edges']}[/bold]")
    console.print(
        f"  Tiers: foundational={stats['foundational']}, "
        f"evaluative={stats['evaluative']}, "
        f"inference={stats['inference']}"
    )
    if section:
        console.print(f"  Section filter: {section}")
    if signal_type:
        console.print(f"  Type filter: {signal_type}")
    console.print(f"  Output: [green]{out_path}[/green]\n")

    # Open in browser if requested
    if open_browser:
        webbrowser.open(out_path.resolve().as_uri())
