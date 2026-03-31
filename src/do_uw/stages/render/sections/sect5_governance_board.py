"""Section 5 board renderers: composition, quality, ownership, sentiment,
anti-takeover, and executive name validation helpers.

Extracted from sect5_governance.py to satisfy the 500-line limit.
All functions are called from sect5_governance.render_section_5() orchestrator.

Phase 60-02: render_board_quality_metrics receives context dict for
peer benchmark lookups via context["_state"] escape hatch.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import LeadershipForensicProfile, OwnershipAnalysis
from do_uw.stages.render.chart_helpers import embed_chart
from do_uw.stages.render.charts.ownership_chart import create_ownership_chart
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
    set_cell_shading,
)
from do_uw.stages.render.formatters import (
    format_percentage,
    na_if_none,
)
from do_uw.stages.render.peer_context import get_peer_context_line


def render_board_composition(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render full board composition table from DEF 14A data."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Board Composition")

    board_profs = gov.board_forensics
    if not board_profs:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Board composition data not available.")
        return

    headers = [
        "Name", "Tenure", "Independent", "Committees",
        "Other Boards", "Overboarded",
    ]
    rows: list[list[str]] = []
    for d in board_profs:
        name = clean_board_name(sv_str(d.name))
        tenure = (
            f"{d.tenure_years.value:.1f} yrs"
            if d.tenure_years is not None
            else "N/A"
        )
        indep = sv_bool(d.is_independent)
        committees = ", ".join(d.committees) if d.committees else "N/A"
        other = str(len(d.other_boards)) if d.other_boards else "0"
        overboarded = "Yes" if d.is_overboarded else "No"
        rows.append([name, tenure, indep, committees, other, overboarded])

    table: Any = add_styled_table(doc, headers, rows, ds)

    # Highlight overboarded directors (amber)
    for row_idx, d in enumerate(board_profs):
        if d.is_overboarded:
            ob_cell: Any = table.rows[row_idx + 1].cells[5]
            set_cell_shading(ob_cell, "FFF3CD")  # Amber

    # D&O context for classified board
    board = gov.board
    if board.classified_board and board.classified_board.value:
        para = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            "D&O Context: Classified (staggered) board reduces "
            "shareholder ability to replace directors, increasing "
            "Revlon duty scrutiny and derivative suit exposure "
            "in change-of-control situations."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


def render_board_quality_metrics(
    doc: Any,
    gov: GovernanceData,
    context: dict[str, Any] | None = None,
    ds: DesignSystem | None = None,
    **kwargs: Any,
) -> None:
    """Render board quality summary metrics with optional peer context."""
    # Backward compatibility: old callers pass (doc, gov, ds) positionally
    if isinstance(context, DesignSystem):
        ds = context
        context = None
    if ds is None:
        msg = "ds (DesignSystem) is required"
        raise TypeError(msg)

    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Board Quality Metrics")

    board = gov.board
    rows: list[list[str]] = []
    rows.append([
        "Board Size",
        na_if_none(board.size.value if board.size else None),
    ])

    # Independence ratio with optional peer context
    indep_val = format_percentage(
        board.independence_ratio.value * 100
        if board.independence_ratio is not None
        else None
    )
    rows.append(["Independence Ratio", indep_val])

    if board.avg_tenure_years:
        rows.append([
            "Average Tenure",
            f"{board.avg_tenure_years.value:.1f} years",
        ])
    rows.append(["CEO/Chair Duality", sv_bool(board.ceo_chair_duality)])
    rows.append(["Classified Board", sv_bool(board.classified_board)])
    ob_val = board.overboarded_count.value if board.overboarded_count is not None else None
    rows.append(["Overboarded Directors", na_if_none(ob_val)])
    rows.append(["Dual-Class Structure", sv_bool(board.dual_class_structure)])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Governance score peer context (when context available)
    if context is not None:
        # TODO(phase-60): move benchmark to context_builders
        state = context.get("_state")
        bm = state.benchmark if state is not None else None
        gov_line = get_peer_context_line("governance_score", bm)
        if gov_line:
            ctx_para: Any = doc.add_paragraph(style="DOBody")
            ctx_para.add_run(f"Governance Score: {gov_line}")

    # D&O context for duality
    if board.ceo_chair_duality and board.ceo_chair_duality.value:
        para: Any = doc.add_paragraph(style="DOBody")
        run: Any = para.add_run(
            "D&O Context: CEO/Chair duality reduces board independence "
            "in oversight of management, increasing derivative suit risk."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(para, "ELEVATED", ds)


def render_ownership(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render ownership structure with donut chart (VIS-02)."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Ownership Structure")

    ownership = gov.ownership

    # Embed ownership chart
    chart_buf = create_ownership_chart(ownership, ds)
    if chart_buf is not None:
        embed_chart(doc, chart_buf)
        caption: Any = doc.add_paragraph(style="DOCaption")
        caption.add_run(
            "Figure: Ownership breakdown -- "
            "institutional, insider, retail float"
        )
    else:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Ownership chart not available (insufficient data).")

    # Ownership table
    _render_ownership_table(doc, ownership, ds)

    # Activist positions
    if ownership.known_activists:
        para = doc.add_paragraph(style="DOBody")
        activists = [str(a.value) for a in ownership.known_activists]
        para.add_run(f"Known Activist Positions: {', '.join(activists)}")
        context_para: Any = doc.add_paragraph(style="DOBody")
        run: Any = context_para.add_run(
            "D&O Context: Activist investor presence increases proxy "
            "contest and derivative suit risk. May trigger Section 14A "
            "disclosure litigation."
        )
        run.italic = True
        run.font.size = ds.size_small
        add_risk_indicator(context_para, "ELEVATED", ds)


def _render_ownership_table(
    doc: Any, ownership: OwnershipAnalysis, ds: DesignSystem
) -> None:
    """Render ownership breakdown table with top holders."""
    rows: list[list[str]] = []
    if ownership.institutional_pct:
        rows.append([
            "Institutional Ownership",
            format_percentage(ownership.institutional_pct.value),
        ])
    if ownership.insider_pct:
        rows.append([
            "Insider Ownership",
            format_percentage(ownership.insider_pct.value),
        ])
    # Calculate retail float
    inst = ownership.institutional_pct.value if ownership.institutional_pct else 0
    ins = ownership.insider_pct.value if ownership.insider_pct else 0
    if inst > 0 or ins > 0:
        retail = max(0, 100.0 - inst - ins)
        rows.append(["Retail Float", format_percentage(retail)])

    if rows:
        add_styled_table(doc, ["Category", "Percentage"], rows, ds)

    # Top holders -- only show if we have meaningful data (names + pcts)
    if ownership.top_holders:
        holder_rows: list[list[str]] = []
        has_pct_data = False
        for holder in ownership.top_holders[:5]:
            info: Any = holder.value
            name = str(info.get("name", "N/A")) if hasattr(info, "get") else "N/A"
            if name == "N/A":
                continue
            pct: Any = (info.get("pct_out") or info.get("percentage") or info.get("pct")) if hasattr(info, "get") else None
            if pct is not None:
                has_pct_data = True
                pct_str = format_percentage(float(pct))
            else:
                pct_str = ""
            holder_rows.append([name, pct_str])

        if holder_rows:
            if has_pct_data:
                add_styled_table(
                    doc, ["Top Holder", "Ownership %"], holder_rows, ds,
                )
            else:
                # Show just names without the empty % column
                name_rows = [[r[0]] for r in holder_rows]
                add_styled_table(
                    doc, ["Top Institutional Holders"], name_rows, ds,
                )


def render_sentiment(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render sentiment and narrative coherence section.

    Suppresses N/A rows to avoid a table of empty data.
    If all rows would be N/A, hides the entire section (silence = clean).
    """
    sentiment = gov.sentiment
    coherence = gov.narrative_coherence

    # Build rows, filtering out N/A values
    candidates: list[tuple[str, str]] = [
        ("Management Tone", sv_str(sentiment.management_tone_trajectory)),
        ("Hedging Language", sv_str(sentiment.hedging_language_trend)),
        ("CEO/CFO Alignment", sv_str(sentiment.ceo_cfo_divergence)),
        (
            "Q&A Evasion Score",
            format_percentage(
                sentiment.qa_evasion_score.value * 100
                if sentiment.qa_evasion_score is not None
                else None
            ),
        ),
        ("Narrative Coherence", sv_str(coherence.overall_assessment)),
    ]

    rows = [[label, val] for label, val in candidates if val != "N/A"]

    if not rows:
        # No data at all — hide section entirely (silence = clean)
        return

    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Sentiment & Narrative Coherence")

    add_styled_table(doc, ["Signal", "Assessment"], rows, ds)

    # Coherence flags
    if coherence.coherence_flags:
        for flag in coherence.coherence_flags:
            para: Any = doc.add_paragraph(style="DOBody")
            run: Any = para.add_run(
                f"D&O Context: {flag.value} -- Narrative gaps between "
                f"management statements and data increase 10b-5 risk."
            )
            run.italic = True
            run.font.size = ds.size_small
            add_risk_indicator(para, "ELEVATED", ds)


def render_anti_takeover(
    doc: Any, gov: GovernanceData, ds: DesignSystem
) -> None:
    """Render anti-takeover provisions with D&O implications."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Anti-Takeover Provisions")

    board = gov.board
    provisions: list[list[str]] = []

    # Classified board
    if board.classified_board:
        status = "Yes" if board.classified_board.value else "No"
        context = (
            "Limits hostile takeover risk but increases Revlon duty scrutiny"
            if board.classified_board.value
            else "Standard annual elections"
        )
        provisions.append(["Classified Board", status, context])

    # Dual-class structure
    if board.dual_class_structure:
        status = "Yes" if board.dual_class_structure.value else "No"
        context = (
            "Concentrated voting power limits shareholder remedy options"
            if board.dual_class_structure.value
            else "Single class of common stock"
        )
        provisions.append(["Dual-Class Structure", status, context])

    if not provisions:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "Anti-takeover provision data not available. "
            "Review DEF 14A and charter documents for complete analysis."
        )
        return

    add_styled_table(
        doc, ["Provision", "Status", "D&O Implication"], provisions, ds,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def clean_board_name(name: str) -> str:
    """Remove company name artifacts from board member names.

    LLM extraction sometimes includes company name or title suffixes.
    Examples: 'John Smith, Apple Inc.' -> 'John Smith'
              'Jane Doe (Independent)' -> 'Jane Doe'
              'John Doe, CPA' -> 'John Doe, CPA' (keep credential suffixes)
    """
    if not name or name == "N/A":
        return name
    # Remove parenthetical suffixes like (Independent), (Non-Executive)
    name = re.sub(r'\s*\((?:Independent|Non-Independent|Non-Executive|'
                  r'Executive|Director|Chairman|Chair)\)\s*$', '', name,
                  flags=re.IGNORECASE)
    # Remove trailing ", <Company Name> <Corp Suffix>" patterns.
    # Matches: ", Anything Inc.", ", Anything Corp.", ", Anything LLC", etc.
    name = re.sub(
        r',\s+\S.*?\s*(?:Inc\.?|Corp\.?|LLC|Ltd\.?|L\.P\.|N\.A\.|PLC)\s*$',
        '', name, flags=re.IGNORECASE,
    )
    # Also match when the corporate suffix appears without a preceding comma
    # e.g., "John Smith Inc." -- but only at the end, and only if the suffix
    # is preceded by a word that looks like a company name (capitalized)
    name = re.sub(
        r'\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|L\.P\.|PLC)\s*$',
        '', name, flags=re.IGNORECASE,
    )
    return name.strip()


def sv_str(sv: Any) -> str:
    """Extract string from SourcedValue or return N/A."""
    if sv is None:
        return "N/A"
    return str(sv.value)


def sv_bool(sv: Any) -> str:
    """Format a SourcedValue[bool] as Yes/No/N/A."""
    if sv is None:
        return "N/A"
    return "Yes" if sv.value else "No"


# ---------------------------------------------------------------------------
# Executive name validation helpers (used by sect5_governance._render_leadership)
# ---------------------------------------------------------------------------

# Words that never appear in a person's name -- corporate suffixes and industry terms
_REJECT_WORDS = {
    "corporation", "corp", "inc", "ltd", "llc", "llp", "company", "co",
    "group", "holdings", "partners", "plc", "semiconductor", "computer",
    "technology", "technologies", "digital", "systems", "solutions",
    "services", "software", "global", "international", "worldwide",
    "enterprises", "capital", "financial", "industries", "associates",
    "networks", "communications", "electronics", "energy",
    "pharmaceuticals", "therapeutics", "biosciences", "motors", "airlines",
    "entertainment", "media",
}

# Known brands that proxy regex greedily extracts as person names
_KNOWN_BRANDS = {
    "pixar", "disney", "google", "apple", "amazon", "microsoft", "netflix",
    "meta", "tesla", "nvidia", "intel", "oracle", "ibm", "samsung", "sony",
    "qualcomm", "cisco", "adobe", "uber", "lyft", "twitter", "spacex",
    "boeing", "airbus", "orient", "springer",
}


def is_valid_person_name(name: str, company_name: str = "") -> bool:
    """Check if a string looks like a valid person name.

    Rejects single words, corporate/brand names, and matches to the
    subject company name.
    """
    if not name or name == "N/A":
        return False
    parts = name.strip().split()
    if len(parts) < 2:
        return False
    if any(p.lower().rstrip(".,") in _REJECT_WORDS for p in parts):
        return False
    if any(p.lower().rstrip(".,") in _KNOWN_BRANDS for p in parts):
        return False
    if company_name:
        name_lower = name.lower().strip()
        comp_lower = company_name.lower().strip()
        if name_lower == comp_lower or name_lower in comp_lower:
            return False
        if comp_lower in name_lower:
            return False
    return True


def filter_valid_executives(
    executives: list[LeadershipForensicProfile],
    company_name: str = "",
) -> list[LeadershipForensicProfile]:
    """Filter and deduplicate executives, removing garbage extractions."""
    seen_titles: dict[str, LeadershipForensicProfile] = {}
    for ep in executives:
        name = sv_str(ep.name)
        if not is_valid_person_name(name, company_name):
            continue
        title = sv_str(ep.title).lower().strip()
        primary_role = _extract_primary_role(title)
        if primary_role in seen_titles:
            existing_name = sv_str(seen_titles[primary_role].name)
            if len(name) > len(existing_name):
                seen_titles[primary_role] = ep
        else:
            seen_titles[primary_role] = ep
    return list(seen_titles.values())


def _extract_primary_role(title: str) -> str:
    """Extract the primary role from a compound title for deduplication."""
    for role in ("ceo", "cfo", "coo", "cto", "cio", "cmo", "gc", "general counsel"):
        if role in title:
            return role
    return title


def count_shade_factors(exec_prof: LeadershipForensicProfile) -> str:
    """Count and summarize shade factors for an executive."""
    count = len(exec_prof.shade_factors)
    return "None" if count == 0 else f"{count} flag(s)"


__all__ = [
    "clean_board_name",
    "count_shade_factors",
    "filter_valid_executives",
    "is_valid_person_name",
    "render_anti_takeover",
    "render_board_composition",
    "render_board_quality_metrics",
    "render_ownership",
    "render_sentiment",
    "sv_bool",
    "sv_str",
]
