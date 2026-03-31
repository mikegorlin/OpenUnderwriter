"""Dossier D&O enrichment engine.

Generates company-specific D&O risk commentary for every dossier table row,
computes concentration risk levels, maps emerging risks to scoring factors,
produces unit economics narrative, and generates the revenue waterfall D&O
insight narrative.

Runs in BENCHMARK stage after scoring is complete. Enrichment reads scoring
data from state.scoring and produces pre-rendered D&O commentary that
templates display as-is.

Phase 118-03: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

import logging

from do_uw.models.dossier import DossierData, UnitEconomicMetric
from do_uw.models.scoring import FactorScore, ScoringResult
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.dossier_enrichment_helpers import (
    CONCENTRATION_IMPLICATION_MAP,
    enrich_concentration_card,
    enrich_generic_card,
    enrich_revenue_quality,
    enrich_revrec_card,
    extract_dollar_amount,
    extract_number,
    extract_percentage,
)

logger = logging.getLogger(__name__)

# Keyword -> scoring factor mapping for emerging risks
_RISK_FACTOR_MAP: dict[str, str] = {
    "regulat": "F.9",
    "sec ": "F.9",
    "compliance": "F.9",
    "litigat": "F.1",
    "lawsuit": "F.1",
    "settlement": "F.1",
    "sca": "F.1",
    "class action": "F.1",
    "financ": "F.3",
    "margin": "F.3",
    "debt": "F.3",
    "liquidity": "F.3",
    "competit": "F.5",
    "market share": "F.5",
    "disrupt": "F.5",
    "governance": "F.7",
    "board": "F.7",
    "insider": "F.8",
    "executive": "F.7",
    "stock": "F.2",
    "share price": "F.2",
    "cyber": "F.9",
    "data breach": "F.9",
    "accounting": "F.4",
    "restat": "F.4",
    "audit": "F.4",
}


def enrich_dossier(state: AnalysisState) -> None:
    """Main entry point: enrich all dossier D&O commentary.

    Calls sub-functions to populate do_risk, risk_level, do_factor,
    core_do_exposure, and waterfall_narrative on state.dossier.

    Safe to call even if scoring is absent (uses generic fallback).
    """
    if state.dossier is None:
        state.dossier = DossierData()

    scoring = state.scoring
    ticker = state.ticker or "Company"

    _enrich_core_do_exposure(state, scoring, ticker)
    _enrich_revenue_card(state, scoring, ticker)
    _enrich_concentration_dimensions(state)
    _enrich_emerging_risks(state)
    _enrich_unit_economics(state, ticker)
    _enrich_waterfall(state, scoring, ticker)
    _enrich_asc_606(state)

    logger.info(
        "Dossier enrichment complete: %d card rows, %d concentration dims, "
        "%d emerging risks, %d ASC 606 elements",
        len(state.dossier.revenue_card),
        len(state.dossier.concentration_dimensions),
        len(state.dossier.emerging_risks),
        len(state.dossier.asc_606_elements),
    )


def _get_top_factor(scoring: ScoringResult | None) -> FactorScore | None:
    """Get the factor with highest points deducted."""
    if scoring is None or not scoring.factor_scores:
        return None
    return max(scoring.factor_scores, key=lambda f: f.points_deducted)


def _get_tier_name(scoring: ScoringResult | None) -> str:
    """Get scoring tier name or fallback."""
    if scoring is not None and scoring.tier is not None:
        return str(scoring.tier.tier.value)
    return "N/A"


def _get_quality_score(scoring: ScoringResult | None) -> str:
    """Get quality score as string."""
    if scoring is not None:
        return f"{scoring.quality_score:.1f}"
    return "N/A"


# -----------------------------------------------------------------------
# Core D&O Exposure
# -----------------------------------------------------------------------
def _enrich_core_do_exposure(
    state: AnalysisState,
    scoring: ScoringResult | None,
    ticker: str,
) -> None:
    """Generate core D&O exposure paragraph from scoring data."""
    if scoring is None:
        state.dossier.core_do_exposure = (
            f"Scoring data not yet available for {ticker}."
        )
        return

    tier = _get_tier_name(scoring)
    score = _get_quality_score(scoring)
    top_factor = _get_top_factor(scoring)

    if top_factor is not None:
        state.dossier.core_do_exposure = (
            f"The core D&O exposure for {ticker} centers on "
            f"{top_factor.factor_name.lower()}. "
            f"Quality score {score} ({tier}), with the heaviest drag from "
            f"{top_factor.factor_name} "
            f"({top_factor.points_deducted:.0f}/{top_factor.max_points} points deducted)."
        )
    else:
        state.dossier.core_do_exposure = (
            f"The core D&O exposure for {ticker} is evaluated at "
            f"{score} ({tier}) with no dominant single factor."
        )


# -----------------------------------------------------------------------
# Revenue Card Enrichment
# -----------------------------------------------------------------------
def _enrich_revenue_card(
    state: AnalysisState,
    scoring: ScoringResult | None,
    ticker: str,
) -> None:
    """Add do_risk + risk_level to each revenue card row."""
    tier = _get_tier_name(scoring)

    for row in state.dossier.revenue_card:
        attr_lower = row.attribute.lower()
        value_lower = row.value.lower()

        if "revenue quality" in attr_lower:
            enrich_revenue_quality(row, value_lower, tier, ticker)
        elif "concentration" in attr_lower:
            enrich_concentration_card(row, value_lower, ticker)
        elif "rev-rec" in attr_lower or "recognition" in attr_lower:
            enrich_revrec_card(row, value_lower, ticker)
        else:
            enrich_generic_card(row, scoring, tier, ticker)


# -----------------------------------------------------------------------
# Concentration Dimensions
# -----------------------------------------------------------------------
def _enrich_concentration_dimensions(state: AnalysisState) -> None:
    """Compute risk levels for concentration dimensions."""
    for dim in state.dossier.concentration_dimensions:
        pct = extract_percentage(dim.metric)
        dim_key = dim.dimension.lower().strip()

        if pct is not None:
            if pct > 30:
                dim.risk_level = "HIGH"
            elif pct > 15:
                dim.risk_level = "MEDIUM"
            else:
                dim.risk_level = "LOW"

        dim.do_implication = CONCENTRATION_IMPLICATION_MAP.get(
            dim_key,
            f"Concentration in {dim.dimension} creates potential "
            f"disclosure obligation under federal securities law",
        )


# -----------------------------------------------------------------------
# Emerging Risks
# -----------------------------------------------------------------------
def _enrich_emerging_risks(state: AnalysisState) -> None:
    """Map each emerging risk to a scoring factor via keyword matching."""
    for risk in state.dossier.emerging_risks:
        risk_lower = risk.risk.lower()

        matched_factor = "F.5"  # default
        for keyword, factor in _RISK_FACTOR_MAP.items():
            if keyword in risk_lower:
                matched_factor = factor
                break

        risk.do_factor = f"Maps to {matched_factor}: {risk.risk}"

        valid_prob = {"high", "medium", "low"}
        valid_impact = {"very high", "high", "medium", "low"}
        if risk.probability.lower() not in valid_prob:
            risk.probability = "Medium"
        if risk.impact.lower() not in valid_impact:
            risk.impact = "Medium"


# -----------------------------------------------------------------------
# Unit Economics
# -----------------------------------------------------------------------
def _enrich_unit_economics(
    state: AnalysisState,
    ticker: str,
) -> None:
    """Add do_risk to each metric and generate the narrative."""
    metrics = state.dossier.unit_economics
    if not metrics:
        return

    most_important: UnitEconomicMetric | None = None
    most_important_reason = ""

    for m in metrics:
        m_lower = m.metric.lower()
        val = extract_number(m.value)

        if "ndr" in m_lower or "net dollar" in m_lower or "retention" in m_lower:
            if val is not None and val < 90:
                m.do_risk = (
                    f"NDR at {m.value} below 100% threshold indicates "
                    f"net contraction risk -- a leading indicator of "
                    f"revenue deceleration and SCA trigger."
                )
                most_important = m
                most_important_reason = (
                    "NDR below 90% signals net revenue contraction "
                    "risk, the strongest leading indicator of an "
                    "earnings miss for SaaS companies"
                )
            else:
                m.do_risk = (
                    f"NDR at {m.value} demonstrates healthy expansion "
                    f"revenue, supporting earnings predictability."
                )
        elif "growth" in m_lower:
            if val is not None and val < 0:
                m.do_risk = (
                    f"Negative growth ({m.value}) creates immediate "
                    f"narrative break risk -- market expects growth "
                    f"companies to maintain trajectory."
                )
                if most_important is None:
                    most_important = m
                    most_important_reason = (
                        "negative growth creates immediate SCA risk "
                        "if previously guided higher"
                    )
            else:
                m.do_risk = (
                    f"Growth at {m.value} vs benchmark {m.benchmark} "
                    f"-- monitor for deceleration risk."
                )
        else:
            m.do_risk = (
                f"{m.metric}: {m.value} (benchmark: {m.benchmark}). Within normal range."
            )

    if most_important is None and metrics:
        most_important = metrics[0]
        most_important_reason = (
            "it is the primary indicator of business model health"
        )

    if most_important is not None:
        state.dossier.unit_economics_narrative = (
            f"The single most important metric for {ticker}'s D&O "
            f"risk is {most_important.metric} at {most_important.value} "
            f"because {most_important_reason}."
        )


# -----------------------------------------------------------------------
# Revenue Waterfall
# -----------------------------------------------------------------------
def _enrich_waterfall(
    state: AnalysisState,
    scoring: ScoringResult | None,
    ticker: str,
) -> None:
    """Generate waterfall_narrative from waterfall_rows + scoring."""
    rows = state.dossier.waterfall_rows
    if not rows:
        state.dossier.waterfall_narrative = ""
        return

    tier = _get_tier_name(scoring)
    expansion_val, new_logo_val, price_val, total_new = 0.0, 0.0, 0.0, 0.0
    row_summaries: list[str] = []

    for row in rows:
        label_lower = row.label.lower()
        val = extract_dollar_amount(row.value)

        if "expansion" in label_lower or "upsell" in label_lower:
            expansion_val = val or 0.0
            total_new += expansion_val
        elif "new logo" in label_lower or "new customer" in label_lower:
            new_logo_val = val or 0.0
            total_new += new_logo_val
        elif "price" in label_lower or "pricing" in label_lower:
            price_val = val or 0.0
            total_new += price_val

        if row.value and row.label:
            row_summaries.append(f"{row.label} ({row.value})")

    parts = _build_waterfall_parts(
        expansion_val, new_logo_val, price_val,
        total_new, row_summaries, ticker,
    )

    if parts:
        narrative = ". ".join(parts) + "."
        if scoring is not None:
            narrative += (
                f" At {tier} tier, monitor for revenue composition "
                f"shifts that could trigger narrative break."
            )
        state.dossier.waterfall_narrative = narrative
    else:
        state.dossier.waterfall_narrative = (
            f"Revenue waterfall for {ticker} contains "
            f"{len(rows)} components. "
            f"Review individual rows for growth composition detail."
        )


def _build_waterfall_parts(
    expansion_val: float,
    new_logo_val: float,
    price_val: float,
    total_new: float,
    row_summaries: list[str],
    ticker: str,
) -> list[str]:
    """Build narrative parts from waterfall component values."""
    parts: list[str] = []

    if total_new > 0:
        components = []
        if expansion_val > 0:
            components.append(f"expansion (${expansion_val:.0f}M)")
        if new_logo_val > 0:
            components.append(f"new logo (${new_logo_val:.0f}M)")
        if price_val > 0:
            components.append(f"price increases (${price_val:.0f}M)")
        if components:
            parts.append(
                f"Net new ARR of ${total_new:.0f}M driven by "
                + " vs ".join(components)
            )

        expansion_pct = (expansion_val / total_new) * 100
        new_logo_pct = (new_logo_val / total_new) * 100
        price_pct = (price_val / total_new) * 100

        if expansion_pct > 60:
            parts.append(
                f"Expansion-heavy growth ({expansion_pct:.0f}% of new ARR) "
                f"creates earnings predictability risk if NDR compresses "
                f"(F.5 narrative break indicator)"
            )
        elif new_logo_pct > 60:
            parts.append(
                "New customer acquisition cost may pressure margins "
                "-- miss guidance if CAC payback extends "
                "(F.3 expense trajectory)"
            )
        if price_pct > 30:
            parts.append(
                f"Price-driven growth ({price_pct:.0f}% of new ARR) "
                f"faces churn risk if competitors undercut -- "
                f"disclosure risk under Item 303 if pricing power wanes"
            )
    elif row_summaries:
        parts.append(
            f"Revenue bridge for {ticker}: "
            + "; ".join(row_summaries[:4])
        )

    return parts


# -----------------------------------------------------------------------
# ASC 606 Enrichment
# -----------------------------------------------------------------------
def _enrich_asc_606(state: AnalysisState) -> None:
    """Add do_risk to each ASC 606 element based on complexity."""
    for el in state.dossier.asc_606_elements:
        complexity_lower = el.complexity.lower()

        if complexity_lower == "high":
            el.do_risk = (
                f"Revenue recognition judgment area ({el.element}) -- "
                f"23% of SCA settlements 2019-2024 involved rev-rec "
                f"allegations. {el.approach} requires consistent "
                f"application and robust documentation."
            )
        elif complexity_lower == "medium":
            el.do_risk = (
                f"Moderate recognition complexity ({el.element}) -- "
                f"requires consistent ASC 606 application. "
                f"Monitor for policy changes or new contract types."
            )
        else:
            el.do_risk = (
                f"Standard recognition with minimal judgment "
                f"({el.element}). Low SCA exposure from this element."
            )
