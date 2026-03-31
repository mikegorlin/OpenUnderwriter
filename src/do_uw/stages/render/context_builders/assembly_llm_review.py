"""Assembly builder: LLM critical review per section.

Runs AFTER all other builders (html_extras, signals, dossier, uw_analysis)
so it has access to the fully assembled context. Adds an 'llm_insight'
paragraph to each major section that interprets the data through a
D&O underwriting lens.

Registered LAST in assembly_registry.py import order.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import register_builder

logger = logging.getLogger(__name__)

# Sections to review and their data extraction functions
_REVIEW_SECTIONS: list[tuple[str, str, str]] = [
    # (section_id, context_key, display_name)
    ("company", "comp", "Company & Operations"),
    ("market", "market_ext", "Stock & Market"),
    ("financial", "fin", "Financial Health"),
    ("governance", "gov", "Governance & Leadership"),
    ("litigation", "lit_detail", "Litigation & Regulatory"),
    ("scoring", "score_detail", "Scoring & Risk Assessment"),
]


def _extract_section_brief(
    context: dict[str, Any],
    section_id: str,
    ctx_key: str,
) -> dict[str, Any]:
    """Extract a concise data brief from a section's context for LLM review.

    Pulls the most underwriting-relevant fields, keeping under 4000 chars
    to fit in the LLM prompt budget.
    """
    uw = context.get("uw_analysis", {})
    if not isinstance(uw, dict):
        return {}

    section_data = uw.get(ctx_key, {})
    if not isinstance(section_data, dict):
        return {}

    # For each section, extract the most critical fields
    brief: dict[str, Any] = {}

    if section_id == "company":
        for k in ("risk_profile", "revenue_model_type", "risk_classification",
                   "filer_category", "years_public", "disruption_risk",
                   "key_person", "concentration_assessment"):
            if k in section_data:
                brief[k] = section_data[k]

    elif section_id == "market":
        for k in ("price_summary", "drawdown", "short_interest",
                   "insider_summary", "earnings_guidance", "analyst_consensus"):
            if k in section_data:
                brief[k] = section_data[k]
        # Add stock price context
        top_level_mkt = context.get("market", {})
        if isinstance(top_level_mkt, dict):
            for k in ("current_price", "market_cap", "pe_ratio", "52w_range"):
                if k in top_level_mkt:
                    brief[k] = top_level_mkt[k]

    elif section_id == "financial":
        for k in ("distress_indicators", "forensic_dashboard", "earnings_quality",
                   "debt_structure", "liquidity", "goodwill_concentration",
                   "cash_flow_adequacy"):
            if k in section_data:
                brief[k] = section_data[k]

    elif section_id == "governance":
        for k in ("board_composition", "officer_profiles", "compensation",
                   "ownership_structure", "structural_governance"):
            if k in section_data:
                brief[k] = section_data[k]

    elif section_id == "litigation":
        for k in ("sca_profile", "derivative_suits", "defense_strength",
                   "settlement_history", "regulatory_proceedings",
                   "contingent_liabilities", "sol_windows"):
            if k in section_data:
                brief[k] = section_data[k]

    elif section_id == "scoring":
        for k in ("tier_classification", "factor_scores", "claim_probability",
                   "peril_assessment", "hazard_profile"):
            if k in section_data:
                brief[k] = section_data[k]

    # Fallback: if no specific fields matched, grab first few keys
    if not brief and section_data:
        for k in list(section_data.keys())[:8]:
            brief[k] = section_data[k]

    return brief


@register_builder
def _build_llm_section_reviews(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None = None,
) -> None:
    """Add LLM critical review paragraphs to each major section.

    Stores reviews in context['section_reviews'] dict, keyed by section_id.
    Templates pick them up as section_reviews.company, section_reviews.market, etc.
    """
    try:
        from do_uw.stages.render.context_builders.risk_synthesis import (
            synthesize_section_review,
        )
    except ImportError:
        logger.debug("Risk synthesis module not available")
        return

    reviews: dict[str, str] = {}

    for section_id, ctx_key, display_name in _REVIEW_SECTIONS:
        try:
            brief = _extract_section_brief(context, section_id, ctx_key)
            if not brief:
                continue

            review = synthesize_section_review(section_id, brief, state)
            if review:
                reviews[section_id] = review
                logger.debug("LLM review generated for %s", section_id)
        except Exception:
            logger.debug(
                "LLM review failed for %s (non-fatal)", section_id,
                exc_info=True,
            )

    if reviews:
        context["section_reviews"] = reviews
        logger.info("LLM generated %d section reviews", len(reviews))

    # Company profile — full 4-paragraph synthesis (replaces data dump opener)
    try:
        from do_uw.stages.render.context_builders.risk_synthesis import (
            synthesize_company_profile,
        )
        cp = synthesize_company_profile(state)
        if cp:
            context["company_profile"] = cp
            logger.info("LLM synthesized company profile")
    except Exception:
        logger.debug("LLM company profile failed (non-fatal)", exc_info=True)


__all__ = ["_build_llm_section_reviews"]
