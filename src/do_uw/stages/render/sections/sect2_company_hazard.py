"""Section 2 hazard/classification: classification table, hazard profile,
and D&O-relevant risk factors from Item 1A.

Split from sect2_company.py for the 500-line limit.
Called after sect2_company_details to render analysis-layer data.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import format_currency, format_percentage
from do_uw.stages.render.context_builders.analysis import (
    _score_to_exposure,
)

# ---------------------------------------------------------------------------
# Classification (Layer 1)
# ---------------------------------------------------------------------------


def render_classification(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render classification table: market cap tier, sector, filing rate."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Classification")

    state = context["_state"]
    cls = state.classification
    if cls is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Classification data not available.")
        return

    rows: list[list[str]] = [
        ["Market Cap Tier", cls.market_cap_tier.value],
        ["Sector", f"{cls.sector_name or cls.sector_code} ({cls.sector_code})"],
        ["Years Public", str(cls.years_public) if cls.years_public is not None else "N/A"],
        ["Base Filing Rate", format_percentage(cls.base_filing_rate_pct)],
        [
            "Severity Band",
            f"{format_currency(cls.severity_band_low_m * 1_000_000, compact=True)} -- "
            f"{format_currency(cls.severity_band_high_m * 1_000_000, compact=True)}",
        ],
        ["DDL Exposure Base", format_currency(cls.ddl_exposure_base_m * 1_000_000, compact=True)],
        ["IPO Multiplier", f"{cls.ipo_multiplier:.2f}x"],
        ["Cap Filing Multiplier", f"{cls.cap_filing_multiplier:.2f}x"],
    ]

    add_styled_table(doc, ["Attribute", "Value"], rows, ds)


# ---------------------------------------------------------------------------
# Hazard Profile (Layer 2)
# ---------------------------------------------------------------------------


_CATEGORY_NAMES: dict[str, str] = {
    "H1": "Business & Operating Model",
    "H2": "People & Management",
    "H3": "Financial Structure",
    "H4": "Governance Structure",
    "H5": "Public Company Maturity",
    "H6": "External Environment",
    "H7": "Emerging / Modern Hazards",
}


def render_hazard_profile(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render hazard profile: IES score, top risk dimensions, full table, categories."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Hazard Profile (Inherent Exposure Score)")

    state = context["_state"]
    hp = state.hazard_profile
    if hp is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Hazard profile data not available.")
        return

    ies_label = _score_to_exposure(hp.ies_score)

    # IES summary paragraph
    summary: Any = doc.add_paragraph(style="DOBody")
    run: Any = summary.add_run(
        f"IES: {hp.ies_score:.0f}/100 ({ies_label}) | "
        f"Multiplier: {hp.ies_multiplier:.2f}x | "
        f"Data Coverage: {hp.data_coverage_pct:.0f}%"
    )
    run.bold = True
    # Add risk indicator based on IES label
    _ies_risk_map = {
        "CRITICAL": "CRITICAL", "HIGH": "HIGH", "ELEVATED": "ELEVATED",
        "MODERATE": "MODERATE", "LOW": "MODERATE",
    }
    add_risk_indicator(summary, _ies_risk_map.get(ies_label, "NEUTRAL"), ds)

    if hp.confidence_note:
        note: Any = doc.add_paragraph(style="DOCaption")
        note.add_run(hp.confidence_note)

    # Top risk dimensions (ELEVATED+)
    elevated_levels = {"ELEVATED", "HIGH", "CRITICAL"}
    top_dims = sorted(
        [d for d in hp.dimension_scores if _score_to_exposure(d.normalized_score) in elevated_levels],
        key=lambda d: d.normalized_score,
        reverse=True,
    )

    if top_dims:
        sub_heading: Any = doc.add_paragraph(style="DOHeading3")
        sub_heading.add_run("Top Risk Dimensions (Elevated+)")

        top_rows: list[list[str]] = []
        for dim in top_dims:
            evidence = "; ".join(dim.evidence[:2]) if dim.evidence else ""
            exposure = _score_to_exposure(dim.normalized_score)
            top_rows.append([
                dim.dimension_name,
                f"{dim.normalized_score:.0f}",
                exposure,
                evidence,
            ])

        add_styled_table(
            doc,
            ["Dimension", "Score", "Exposure", "Evidence"],
            top_rows,
            ds,
        )

    # Interaction effects
    all_interactions = hp.named_interactions + hp.dynamic_interactions
    if all_interactions:
        ie_heading: Any = doc.add_paragraph(style="DOHeading3")
        ie_heading.add_run("Interaction Effects")

        for ie in all_interactions:
            ie_para: Any = doc.add_paragraph(style="DOBody")
            ie_run: Any = ie_para.add_run(
                f"{ie.name} ({ie.multiplier:.2f}x): {ie.description}"
            )
            ie_run.bold = True

    # Full dimension table (all dimensions sorted by score descending)
    all_dims = sorted(hp.dimension_scores, key=lambda d: d.normalized_score, reverse=True)
    if all_dims:
        full_heading: Any = doc.add_paragraph(style="DOHeading3")
        full_heading.add_run(f"All Hazard Dimensions ({len(all_dims)} dimensions)")

        full_rows: list[list[str]] = []
        for dim in all_dims:
            evidence = "; ".join(dim.evidence[:1]) if dim.evidence else ""
            exposure = _score_to_exposure(dim.normalized_score)
            cat_name = _CATEGORY_NAMES.get(dim.category.value, dim.category.value)
            full_rows.append([
                dim.dimension_name,
                f"{dim.normalized_score:.0f}",
                exposure,
                cat_name,
                evidence,
            ])

        add_styled_table(
            doc,
            ["Dimension", "Score", "Exposure", "Category", "Evidence"],
            full_rows,
            ds,
        )

    # Category summary
    if hp.category_scores:
        cat_heading: Any = doc.add_paragraph(style="DOHeading3")
        cat_heading.add_run("Category Summary")

        cat_rows: list[list[str]] = []
        for cat_id in ("H1", "H2", "H3", "H4", "H5", "H6", "H7"):
            cat = hp.category_scores.get(cat_id)
            if cat is None:
                continue
            cat_rows.append([
                cat.category_name,
                f"{cat.weight_pct:.1f}%",
                f"{cat.raw_score:.1f}",
                f"{cat.weighted_score:.1f}",
                f"{cat.dimensions_scored}/{cat.dimensions_total}",
                f"{cat.data_coverage_pct:.0f}%",
            ])

        add_styled_table(
            doc,
            ["Category", "Weight", "Score", "Weighted", "Dims Scored", "Coverage"],
            cat_rows,
            ds,
        )


# ---------------------------------------------------------------------------
# Risk Factors (Item 1A)
# ---------------------------------------------------------------------------


def render_risk_factors(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render D&O-relevant risk factors from Item 1A, grouped by category."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Risk Factors (D&O-Relevant)")

    state = context["_state"]
    if state.extracted is None or not state.extracted.risk_factors:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("No D&O-relevant risk factors identified.")
        return

    # Filter to D&O-relevant, new, or unique
    rfs = state.extracted.risk_factors
    filtered = [
        rf for rf in rfs
        if rf.do_relevance in ("HIGH", "MEDIUM")
        or rf.is_new_this_year
        or (rf.category != "OTHER" and rf.severity == "HIGH")
    ]

    if not filtered:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("No D&O-relevant risk factors identified.")
        return

    # Sort by new first, then severity, then category
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    filtered.sort(key=lambda f: (not f.is_new_this_year, severity_order.get(f.severity, 3), f.category))

    # Build table rows
    rows: list[list[str]] = []
    for rf in filtered:
        new_flag = "[NEW] " if rf.is_new_this_year else ""
        passage = rf.source_passage
        rows.append([
            f"{new_flag}{rf.title}",
            rf.category,
            rf.severity,
            rf.do_relevance,
            passage,
        ])

    add_styled_table(
        doc,
        ["Risk Factor", "Category", "Severity", "D&O Relevance", "Source Passage"],
        rows,
        ds,
    )

    # Summary count
    new_count = sum(1 for rf in filtered if rf.is_new_this_year)
    high_count = sum(1 for rf in filtered if rf.severity == "HIGH")
    summary_para: Any = doc.add_paragraph(style="DOCaption")
    summary_para.add_run(
        f"{len(filtered)} D&O-relevant risk factors "
        f"({new_count} new this year, {high_count} high severity)."
    )


__all__ = [
    "render_classification",
    "render_hazard_profile",
    "render_risk_factors",
]
