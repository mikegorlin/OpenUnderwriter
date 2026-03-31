"""Section 2 D&O exposure renderers: exposure mapping, extracted/standard exposure.

Extracted from sect2_company_details.py to satisfy the 500-line limit.
All functions are called from sect2_company_details.render_company_details().

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)

# Standard D&O exposure categories for mapping table
_DO_EXPOSURE_TYPES: list[dict[str, str]] = [
    {
        "type": "Securities Litigation",
        "coverage": "Side A/B/C",
        "description": "Shareholder class actions, SEC enforcement",
    },
    {
        "type": "Derivative Actions",
        "coverage": "Side A/B",
        "description": "Breach of fiduciary duty, waste claims",
    },
    {
        "type": "Employment Practices",
        "coverage": "Side B/C (EPLI)",
        "description": "Discrimination, harassment, wrongful termination",
    },
    {
        "type": "Regulatory/Government",
        "coverage": "Side A (primarily)",
        "description": "DOJ, SEC, FTC, state AG investigations",
    },
    {
        "type": "Fiduciary (ERISA)",
        "coverage": "Fiduciary Liability",
        "description": "401(k) plan mismanagement, fee litigation",
    },
]


def render_do_exposure_mapping(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render D&O exposure mapping table."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("D&O Exposure Factors")

    state = context["_state"]

    # Use extracted exposure factors if available AND well-structured
    factors = state.company.do_exposure_factors if state.company else []

    # Only use extracted factors if we have enough quality data:
    # at least 2 factors, each with a 'level' field
    has_quality_factors = (
        len(factors) >= 2
        and all(
            f.value.get("level") is not None
            for f in factors
        )
    )

    if has_quality_factors:
        _render_extracted_exposure(doc, factors, ds)
    else:
        _render_standard_exposure(doc, ds)


def _render_extracted_exposure(
    doc: Any, factors: list[Any], ds: DesignSystem
) -> None:
    """Render exposure from extracted factors as paragraphs with risk level."""
    for sv_factor in factors:
        factor = sv_factor.value
        raw_name = str(factor.get("factor", factor.get("name", "Unknown")))
        name = raw_name.replace("_", " ").title()
        level = str(factor.get("level", "N/A"))
        rationale = str(factor.get("reason", factor.get("rationale", "")))
        coverage = str(factor.get("coverage_part", ""))

        fp: Any = doc.add_paragraph(style="DOBody")
        run: Any = fp.add_run(f"{name}: {level}")
        run.bold = True
        _add_exposure_indicator(fp, level, ds)

        if rationale or coverage:
            detail: Any = doc.add_paragraph(style="DOCaption")
            parts: list[str] = []
            if rationale:
                parts.append(rationale)
            if coverage:
                parts.append(f"Coverage: {coverage}")
            detail.add_run(" | ".join(parts))


def _render_standard_exposure(
    doc: Any, ds: DesignSystem
) -> None:
    """Render standard D&O exposure categories when no extracted data."""
    rows: list[list[str]] = []
    for exp in _DO_EXPOSURE_TYPES:
        rows.append([
            exp["type"],
            "See analysis sections",
            exp["description"],
            exp["coverage"],
        ])

    add_styled_table(
        doc,
        ["Exposure Type", "Risk Level", "Description", "Coverage Part"],
        rows,
        ds,
    )

    note: Any = doc.add_paragraph(style="DOCaption")
    note.add_run(
        "Standard D&O exposure categories shown. "
        "See individual analysis sections for company-specific risk levels."
    )


def _add_exposure_indicator(
    para: Any, level: str, ds: DesignSystem
) -> None:
    """Add risk indicator based on exposure level string."""
    level_map: dict[str, str] = {
        "HIGH": "HIGH", "ELEVATED": "ELEVATED", "MODERATE": "MODERATE",
        "LOW": "MODERATE", "CRITICAL": "CRITICAL",
    }
    risk_level = level_map.get(level.upper(), "NEUTRAL")
    add_risk_indicator(para, risk_level, ds)


__all__ = ["render_do_exposure_mapping"]
