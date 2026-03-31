"""Section 3 peer group comparison table.

Split from sect3_financial.py for 500-line compliance.
Renders the peer group comparison table with percentile context
for revenue and leverage metrics.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.financials import ExtractedFinancials
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table
from do_uw.stages.render.formatters import format_currency
from do_uw.stages.render.peer_context import get_peer_context_line

# Non-US exchange suffixes to filter from peer group display
_NON_US_SUFFIXES: tuple[str, ...] = (
    ".L", ".F", ".BE", ".DU", ".MU", ".PA", ".AS", ".MI",
    ".MC", ".BR", ".SW", ".TO", ".V", ".AX", ".HK", ".SS",
    ".SZ", ".T", ".TW", ".KS", ".SI", ".JK", ".NS", ".BO",
)


def render_peer_group(
    doc: Any,
    context: dict[str, Any],
    financials: ExtractedFinancials | None,
    ds: DesignSystem,
) -> None:
    """Render peer group comparison table with peer percentile context.

    Filters out non-US exchange listings (e.g. .L London cross-listings)
    and tickers starting with '0' (LSE international listings) that
    are artifacts of the data source, not true peers.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Peer Group Comparison")

    peer_group = financials.peer_group if financials else None
    if peer_group is None or not peer_group.peers:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Peer group data not available.")
        return

    # Filter to US-listed peers only
    valid_peers = [
        p for p in peer_group.peers
        if not p.ticker.endswith(_NON_US_SUFFIXES)
        and not p.ticker.startswith("0")
        and "." not in p.ticker  # catch any other exchange suffixes
    ]

    if not valid_peers:
        body = doc.add_paragraph(style="DOBody")
        body.add_run(
            "Peer group data available but no US-listed peers identified. "
            f"({len(peer_group.peers)} international listing(s) excluded.)"
        )
        return

    rows: list[list[str]] = []
    for peer in valid_peers[:10]:
        mcap = (
            format_currency(peer.market_cap, compact=True)
            if peer.market_cap
            else "N/A"
        )
        rev = (
            format_currency(peer.revenue, compact=True)
            if peer.revenue
            else "N/A"
        )
        rows.append([
            peer.ticker,
            peer.name,
            mcap,
            rev,
            f"{peer.peer_score:.0f}",
        ])

    add_styled_table(
        doc,
        ["Ticker", "Name", "Market Cap", "Revenue", "Score"],
        rows,
        ds,
    )

    # Peer percentile context for revenue and leverage
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    context_parts: list[str] = []
    rev_line = get_peer_context_line("revenue", state.benchmark)
    if rev_line:
        context_parts.append(f"Revenue: {rev_line}")
    lev_line = get_peer_context_line("leverage_debt_ebitda", state.benchmark)
    if lev_line:
        context_parts.append(f"Leverage: {lev_line}")
    if context_parts:
        ctx_para: Any = doc.add_paragraph(style="DOBody")
        ctx_para.add_run(". ".join(context_parts) + ".")

    excluded = len(peer_group.peers) - len(valid_peers)
    method_parts: list[str] = []
    if peer_group.construction_method:
        method_parts.append(f"Method: {peer_group.construction_method}")
    if excluded > 0:
        method_parts.append(
            f"{excluded} non-US listing(s) excluded"
        )
    if method_parts:
        note: Any = doc.add_paragraph(style="DOCaption")
        note.add_run(" | ".join(method_parts))


__all__ = ["render_peer_group"]
