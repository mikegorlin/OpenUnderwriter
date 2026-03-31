"""Extended feedback CLI: process reactions and show proposal details.

Provides commands for batch-processing feedback reactions into calibration
proposals and viewing proposal details:
- ``do-uw feedback process`` -- aggregate pending reactions into proposals
- ``do-uw feedback show <id>`` -- show full detail for a specific proposal

Registered on feedback_app from cli_feedback.py via import at module bottom.
"""

from __future__ import annotations

import json

import typer
from rich.panel import Panel
from rich.table import Table

from do_uw.cli_feedback import console, feedback_app


# ---------------------------------------------------------------------------
# Subcommand: process (batch-process reactions into proposals)
# ---------------------------------------------------------------------------


@feedback_app.command("process")
def feedback_process(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show full detail for each proposal (drill-down)",
    ),
) -> None:
    """Batch-process pending reactions into calibration proposals.

    Aggregates all PENDING reactions by signal, determines consensus
    (AGREE/DISAGREE/ADJUST/CONFLICTED), and generates calibration
    proposals with confidence scores and impact projections.
    """
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.feedback_process import process_pending_reactions

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        aggregated, proposals = process_pending_reactions(conn)

        if not aggregated:
            console.print(
                "[dim]No pending reactions to process. "
                "Use 'do-uw feedback capture <TICKER>' to record reactions first.[/dim]"
            )
            return

        # Aggregation summary table
        agg_table = Table(title="Reaction Aggregation Summary")
        agg_table.add_column("Signal ID", min_width=25)
        agg_table.add_column("Reactions", width=10, justify="right")
        agg_table.add_column("A/D/S", width=10, justify="center")
        agg_table.add_column("Consensus", width=12)
        agg_table.add_column("Confidence", width=12)
        agg_table.add_column("Proposal?", width=10, justify="center")

        for agg in aggregated:
            consensus_styled = agg.consensus
            if agg.consensus == "AGREE":
                consensus_styled = "[green]AGREE[/green]"
            elif agg.consensus == "DISAGREE":
                consensus_styled = "[red]DISAGREE[/red]"
            elif agg.consensus == "ADJUST":
                consensus_styled = "[yellow]ADJUST[/yellow]"
            elif agg.consensus == "CONFLICTED":
                consensus_styled = "[bold yellow]CONFLICTED[/bold yellow]"

            has_proposal = agg.consensus != "AGREE"

            agg_table.add_row(
                agg.signal_id,
                str(agg.total_reactions),
                f"{agg.agree_count}/{agg.disagree_count}/{agg.adjust_count}",
                consensus_styled,
                agg.confidence,
                "[green]Yes[/green]" if has_proposal else "[dim]No[/dim]",
            )

        console.print(agg_table)

        # Proposals table
        if proposals:
            console.print()
            prop_table = Table(title="Generated Proposals")
            prop_table.add_column("ID", width=5, justify="right")
            prop_table.add_column("Signal ID", min_width=25)
            prop_table.add_column("Type", width=18)
            prop_table.add_column("Confidence", width=12)
            prop_table.add_column("Fire Rate", width=12)
            prop_table.add_column("Affected", width=10)
            prop_table.add_column("Status", width=12)

            for p in proposals:
                backtest = p.backtest_results or {}
                fire_rate = backtest.get("fire_rate", {})
                score_impact = backtest.get("score_impact", {})
                confidence = backtest.get("confidence", "")

                fire_rate_str = (
                    fire_rate.get("description", "N/A")
                    if isinstance(fire_rate, dict)
                    else "N/A"
                )
                affected = (
                    score_impact.get("affected_tickers", 0)
                    if isinstance(score_impact, dict)
                    else 0
                )

                status_styled = p.status
                if p.status == "CONFLICTED":
                    status_styled = "[bold yellow]CONFLICTED[/bold yellow]"
                elif p.status == "PENDING":
                    status_styled = "[green]PENDING[/green]"

                prop_table.add_row(
                    str(p.proposal_id or ""),
                    p.signal_id or "",
                    p.proposal_type,
                    confidence,
                    fire_rate_str[:20],
                    str(affected),
                    status_styled,
                )

            console.print(prop_table)

            # Verbose: drill-down for each proposal
            if verbose:
                console.print()
                for p in proposals:
                    _print_proposal_detail(p)

        # Summary
        n_agree = sum(1 for a in aggregated if a.consensus == "AGREE")
        n_proposals = len(proposals)
        n_conflicted = sum(1 for p in proposals if p.status == "CONFLICTED")
        n_reactions = sum(a.total_reactions for a in aggregated)

        console.print(
            f"\n[bold]{n_reactions} reactions processed across "
            f"{len(aggregated)} signals:[/bold]"
        )
        console.print(f"  {n_agree} signal(s) confirmed working (AGREE)")
        console.print(f"  {n_proposals} proposal(s) generated")
        if n_conflicted > 0:
            console.print(
                f"  [yellow]{n_conflicted} proposal(s) CONFLICTED "
                f"-- manual review needed[/yellow]"
            )
        if n_proposals > 0:
            console.print(
                "\n[dim]Run 'do-uw brain apply-proposal <id>' to apply a proposal.[/dim]"
            )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subcommand: show (proposal detail)
# ---------------------------------------------------------------------------


@feedback_app.command("show")
def feedback_show(
    proposal_id: int = typer.Argument(help="Proposal ID to show details for"),
) -> None:
    """Show detailed information for a specific proposal."""
    from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path
    from do_uw.knowledge.calibrate_impact import get_proposals_by_ids

    db_path = get_brain_db_path()
    conn = connect_brain_db(db_path)
    create_schema(conn)

    try:
        proposals = get_proposals_by_ids(conn, [proposal_id])

        if not proposals:
            console.print(f"[red]Proposal {proposal_id} not found.[/red]")
            raise typer.Exit(code=1)

        _print_proposal_detail(proposals[0])

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _print_proposal_detail(p: "ProposalRecord") -> None:
    """Print detailed proposal information in a Rich panel."""
    from do_uw.knowledge.feedback_models import ProposalRecord as _PR  # noqa: F811

    backtest = p.backtest_results or {}
    fire_rate = backtest.get("fire_rate", {})
    score_impact = backtest.get("score_impact", {})
    reaction_counts = backtest.get("reaction_counts", {})

    detail = (
        f"[bold]Proposal {p.proposal_id}: {p.signal_id}[/bold]\n"
        f"Type: {p.proposal_type}\n"
        f"Status: {p.status}\n"
        f"Source: {p.source_type} ({p.source_ref or 'N/A'})\n"
        f"Confidence: {backtest.get('confidence', 'N/A')}\n"
        f"Reactions: {reaction_counts.get('agree', 0)} agree, "
        f"{reaction_counts.get('disagree', 0)} disagree, "
        f"{reaction_counts.get('adjust', 0)} adjust "
        f"({reaction_counts.get('total', 0)} total)\n"
        f"Fire Rate: {fire_rate.get('description', 'N/A') if isinstance(fire_rate, dict) else 'N/A'}\n"
        f"Score Impact: {score_impact.get('description', 'N/A') if isinstance(score_impact, dict) else 'N/A'}\n"
        f"Changes: {json.dumps(p.proposed_changes, indent=2) if p.proposed_changes else 'None'}\n"
        f"Rationale: {p.rationale}"
    )
    console.print(Panel(detail, title=f"Proposal {p.proposal_id}"))
