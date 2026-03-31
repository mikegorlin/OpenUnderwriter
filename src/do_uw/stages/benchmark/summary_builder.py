"""Executive summary builder -- orchestrates SECT1 population.

Builds the complete ExecutiveSummary from state data by calling
the key findings ranker, thesis generator, and snapshot builder.
This is the final analytical step before document rendering.

After this runs, state.executive_summary contains all SECT1 data:
- SECT1-01: CompanySnapshot
- SECT1-02: InherentRiskBaseline (passed in)
- SECT1-03: Key negatives (top 5)
- SECT1-04: Key positives (top 5)
- SECT1-05/06: On ScoringResult (not duplicated)
- SECT1-07: DealContext (placeholder)
- Thesis: Underwriting thesis narrative
"""

from __future__ import annotations

import logging

from do_uw.models.executive_summary import (
    CompanySnapshot,
    DealContext,
    ExecutiveSummary,
    InherentRiskBaseline,
    KeyFindings,
    UnderwritingThesis,
)
from do_uw.models.scoring import FactorScore, ScoringResult, Tier
from do_uw.models.scoring_output import RiskType
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.key_findings import (
    select_key_negatives,
    select_key_positives,
)
from do_uw.stages.benchmark.thesis_templates import generate_thesis

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------


def _get_top_factor(scoring: ScoringResult | None) -> FactorScore | None:
    """Get the factor with the highest points deducted.

    Returns None if no scoring data or no factor has any deduction.
    """
    if scoring is None or not scoring.factor_scores:
        return None
    top = max(scoring.factor_scores, key=lambda f: f.points_deducted)
    if top.points_deducted <= 0:
        return None
    return top


def _build_snapshot(state: AnalysisState) -> CompanySnapshot:
    """Build SECT1-01 CompanySnapshot from available state data.

    Extracts company identity, market cap, revenue, employees,
    industry, SIC code, and exchange from state.company and
    state.extracted.financials.
    """
    ticker = state.ticker
    company_name = ""
    market_cap = None
    employee_count = None
    industry = ""
    sic_code = ""
    exchange = ""

    if state.company is not None:
        if state.company.identity.legal_name is not None:
            company_name = state.company.identity.legal_name.value
        market_cap = state.company.market_cap
        employee_count = state.company.employee_count
        # Fallback: yfinance employee count from market extraction
        if employee_count is None and state.extracted and state.extracted.market:
            yf_emp = state.extracted.market.stock.employee_count_yf
            if yf_emp is not None:
                employee_count = yf_emp
        if state.company.identity.sic_code is not None:
            sic_code = state.company.identity.sic_code.value
        if state.company.identity.exchange is not None:
            exchange = state.company.identity.exchange.value
        if state.company.industry_classification is not None:
            industry = state.company.industry_classification.value
        elif state.company.identity.sector is not None:
            industry = state.company.identity.sector.value

    # Try to get revenue from extracted financials (most recent period first)
    revenue = None
    if (
        state.extracted
        and state.extracted.financials
        and state.extracted.financials.statements.income_statement
    ):
        stmt = state.extracted.financials.statements.income_statement
        for item in stmt.line_items:
            if "revenue" in item.label.lower():
                # Use dict order (most recent first) to match financials.py
                for val in item.values.values():
                    if val is not None:
                        revenue = val
                        break
                break

    return CompanySnapshot(
        ticker=ticker,
        company_name=company_name,
        market_cap=market_cap,
        revenue=revenue,
        employee_count=employee_count,
        industry=industry,
        sic_code=sic_code,
        exchange=exchange,
    )


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name, falling back to ticker."""
    if (
        state.company is not None
        and state.company.identity.legal_name is not None
    ):
        return state.company.identity.legal_name.value
    return state.ticker


def _get_risk_type(scoring: ScoringResult | None) -> RiskType:
    """Extract risk type, defaulting to STABLE_MATURE."""
    if scoring and scoring.risk_type:
        return scoring.risk_type.primary
    return RiskType.STABLE_MATURE


def _get_quality_score(scoring: ScoringResult | None) -> float:
    """Extract quality score, defaulting to 100."""
    if scoring:
        return scoring.quality_score
    return 100.0


def _get_tier(scoring: ScoringResult | None) -> Tier:
    """Extract tier, defaulting to WRITE."""
    if scoring and scoring.tier:
        return scoring.tier.tier
    return Tier.WRITE


# -----------------------------------------------------------------------
# Public interface
# -----------------------------------------------------------------------


def build_executive_summary(
    state: AnalysisState,
    inherent_risk: InherentRiskBaseline,
) -> ExecutiveSummary:
    """Build complete ExecutiveSummary from state data.

    Reads from:
    - state.company (SECT1-01 snapshot)
    - state.scoring (SECT1-03/04 findings, thesis input)
    - state.scoring.risk_type (thesis input)
    - state.scoring.red_flag_summary (key negatives source)
    - state.scoring.factor_scores (key findings source)
    - state.scoring.allegation_mapping (theory mapping)
    - inherent_risk (passed in, already computed)

    Args:
        state: Full analysis state after SCORE stage.
        inherent_risk: Pre-computed inherent risk baseline.

    Returns:
        Populated ExecutiveSummary with all SECT1 fields.
    """
    scoring = state.scoring

    # SECT1-01: CompanySnapshot
    snapshot = _build_snapshot(state)

    # SECT1-02: InherentRiskBaseline (passed in)
    # Already computed in BenchmarkStage step 4.

    # SECT1-03: Key Negatives
    negatives = select_key_negatives(
        scoring.red_flag_summary if scoring else None,
        scoring.factor_scores if scoring else [],
        scoring.patterns_detected if scoring else [],
        scoring.allegation_mapping if scoring else None,
    )

    # SECT1-04: Key Positives
    positives = select_key_positives(
        state,
        scoring.factor_scores if scoring else [],
    )

    key_findings = KeyFindings(
        negatives=negatives,
        positives=positives,
    )

    # Thesis narrative
    thesis: UnderwritingThesis = generate_thesis(
        risk_type=_get_risk_type(scoring),
        quality_score=_get_quality_score(scoring),
        tier=_get_tier(scoring),
        top_factor=_get_top_factor(scoring),
        allegation_mapping=(
            scoring.allegation_mapping if scoring else None
        ),
        inherent_risk=inherent_risk,
        company_name=_get_company_name(state),
    )

    # SECT1-07: Deal Context (always placeholder in ticker-only mode)
    deal_context = DealContext()

    n_neg = len(negatives)
    n_pos = len(positives)
    logger.info(
        "Executive summary built: %d negatives, %d positives, "
        "risk_type=%s, thesis=%d chars",
        n_neg,
        n_pos,
        _get_risk_type(scoring).value,
        len(thesis.narrative),
    )

    return ExecutiveSummary(
        snapshot=snapshot,
        inherent_risk=inherent_risk,
        key_findings=key_findings,
        thesis=thesis,
        deal_context=deal_context,
    )


__all__ = ["build_executive_summary"]
