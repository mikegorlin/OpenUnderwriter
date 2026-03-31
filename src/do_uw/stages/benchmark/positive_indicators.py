"""Positive indicator catalog and check functions for SECT1-04.

Defines the catalog of positive conditions checked against state data
for the key positives selection in the executive summary. Each indicator
has a module-level check function (not a lambda) for pyright strict.

Split from key_findings.py to stay under 500-line limit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from do_uw.models.state import AnalysisState

# -----------------------------------------------------------------------
# Positive indicator dataclass
# -----------------------------------------------------------------------


@dataclass
class PositiveIndicator:
    """A positive condition to check against state data."""

    condition: str
    evidence_template: str
    section_origin: str
    theory_mapping: str
    check_fn: Callable[[AnalysisState], bool]
    scoring_relevance: float


# -----------------------------------------------------------------------
# Individual check functions (module-level, not lambdas)
# -----------------------------------------------------------------------


def check_no_active_sca(state: AnalysisState) -> bool:
    """No active securities class action litigation."""
    if (
        state.extracted
        and state.extracted.litigation
        and state.extracted.litigation.securities_class_actions
    ):
        return False
    return True


def check_clean_audit(state: AnalysisState) -> bool:
    """Clean audit opinion with no material weaknesses or restatements."""
    if not state.extracted or not state.extracted.financials:
        return False
    audit = state.extracted.financials.audit
    if audit.material_weaknesses:
        return False
    if audit.restatements:
        return False
    if audit.opinion_type and "adverse" in (
        audit.opinion_type.value or ""
    ).lower():
        return False
    return True


def check_low_short_interest(state: AnalysisState) -> bool:
    """Short interest below 5% of float."""
    if (
        state.extracted
        and state.extracted.market
        and state.extracted.market.short_interest
        and state.extracted.market.short_interest.short_pct_float
    ):
        return (
            state.extracted.market.short_interest.short_pct_float.value
            < 5.0
        )
    return False


def check_strong_governance(state: AnalysisState) -> bool:
    """Governance quality score above 70."""
    if (
        state.extracted
        and state.extracted.governance
        and state.extracted.governance.governance_score
        and state.extracted.governance.governance_score.total_score
    ):
        return (
            state.extracted.governance.governance_score.total_score.value
            > 70.0
        )
    return False


def check_stable_leadership(state: AnalysisState) -> bool:
    """No C-suite departures in last 18 months."""
    if (
        state.extracted
        and state.extracted.governance
        and state.extracted.governance.leadership
    ):
        return (
            len(state.extracted.governance.leadership.departures_18mo) == 0
        )
    return False


def check_no_distress(state: AnalysisState) -> bool:
    """No distress zone indicators in financial health."""
    if not state.extracted or not state.extracted.financials:
        return False
    distress = state.extracted.financials.distress
    for model in [
        distress.altman_z_score,
        distress.ohlson_o_score,
    ]:
        if model is not None and model.zone == "distress":
            return False
    return True


def check_low_volatility(state: AnalysisState) -> bool:
    """90-day volatility below sector typical threshold."""
    if (
        state.extracted
        and state.extracted.market
        and state.extracted.market.stock
        and state.extracted.market.stock.volatility_90d
    ):
        return state.extracted.market.stock.volatility_90d.value < 3.0
    return False


def check_independent_board(state: AnalysisState) -> bool:
    """Board has >75% independent directors."""
    if (
        state.extracted
        and state.extracted.governance
        and state.extracted.governance.board
        and state.extracted.governance.board.independence_ratio
    ):
        return (
            state.extracted.governance.board.independence_ratio.value > 0.75
        )
    return False


def check_no_sec_enforcement(state: AnalysisState) -> bool:
    """No active SEC enforcement pipeline activity."""
    if not state.extracted or not state.extracted.litigation:
        return True
    enf = state.extracted.litigation.sec_enforcement
    if enf.highest_confirmed_stage is not None:
        stage = enf.highest_confirmed_stage.value.upper()
        if stage not in ("NONE", ""):
            return False
    if enf.pipeline_position is not None:
        pos = enf.pipeline_position.value.upper()
        if pos not in ("NONE", ""):
            return False
    return True


def check_forum_selection(state: AnalysisState) -> bool:
    """Company has forum selection provision in charter."""
    if not state.extracted or not state.extracted.litigation:
        return False
    defense = state.extracted.litigation.defense
    fp = defense.forum_provisions
    if fp.has_federal_forum and fp.has_federal_forum.value:
        return True
    if fp.has_exclusive_forum and fp.has_exclusive_forum.value:
        return True
    return False


def check_positive_fcf(state: AnalysisState) -> bool:
    """Positive free cash flow from most recent period."""
    if not state.extracted or not state.extracted.financials:
        return False
    cf = state.extracted.financials.statements.cash_flow
    if cf is None:
        return False
    for item in cf.line_items:
        label_lower = item.label.lower()
        if "operating" in label_lower or "free cash" in label_lower:
            for period in cf.periods:
                val = item.values.get(period)
                if val is not None and val.value > 0:
                    return True
    return False


# -----------------------------------------------------------------------
# Indicator catalog builder
# -----------------------------------------------------------------------


def build_positive_indicators() -> list[PositiveIndicator]:
    """Build the positive indicator catalog with function references.

    Returns list of 11 positive indicators covering SECT2-SECT7 domains.
    Each uses a module-level check function (not lambda) for pyright.
    """
    return [
        PositiveIndicator(
            condition="no_active_sca",
            evidence_template=(
                "No active securities class action litigation"
            ),
            section_origin="SECT6",
            theory_mapping="D_GOVERNANCE (strong defense posture)",
            check_fn=check_no_active_sca,
            scoring_relevance=10.0,
        ),
        PositiveIndicator(
            condition="clean_audit",
            evidence_template=(
                "Clean audit opinion with no material weaknesses "
                "or restatements"
            ),
            section_origin="SECT3",
            theory_mapping="A_DISCLOSURE (clean disclosure history)",
            check_fn=check_clean_audit,
            scoring_relevance=8.0,
        ),
        PositiveIndicator(
            condition="no_sec_enforcement",
            evidence_template=(
                "No active SEC enforcement pipeline activity or "
                "open investigations"
            ),
            section_origin="SECT6",
            theory_mapping="A_DISCLOSURE (clean regulatory record)",
            check_fn=check_no_sec_enforcement,
            scoring_relevance=8.5,
        ),
        PositiveIndicator(
            condition="strong_governance",
            evidence_template=(
                "Governance quality score above 70, indicating strong "
                "board oversight"
            ),
            section_origin="SECT5",
            theory_mapping="D_GOVERNANCE (strong governance)",
            check_fn=check_strong_governance,
            scoring_relevance=7.5,
        ),
        PositiveIndicator(
            condition="no_distress",
            evidence_template=(
                "No financial distress indicators (Altman Z-Score "
                "and Ohlson O-Score in safe zones)"
            ),
            section_origin="SECT3",
            theory_mapping="A_DISCLOSURE (financial health)",
            check_fn=check_no_distress,
            scoring_relevance=7.0,
        ),
        PositiveIndicator(
            condition="stable_leadership",
            evidence_template=(
                "No C-suite departures in last 18 months, indicating "
                "organizational stability"
            ),
            section_origin="SECT5",
            theory_mapping="D_GOVERNANCE (stable management)",
            check_fn=check_stable_leadership,
            scoring_relevance=6.5,
        ),
        PositiveIndicator(
            condition="low_short_interest",
            evidence_template=(
                "Short interest below 5% of float, indicating low "
                "market skepticism"
            ),
            section_origin="SECT4",
            theory_mapping="B_GUIDANCE (market confidence)",
            check_fn=check_low_short_interest,
            scoring_relevance=6.0,
        ),
        PositiveIndicator(
            condition="independent_board",
            evidence_template=(
                "Board independence ratio above 75%, exceeding "
                "governance best practices"
            ),
            section_origin="SECT5",
            theory_mapping="D_GOVERNANCE (board independence)",
            check_fn=check_independent_board,
            scoring_relevance=6.0,
        ),
        PositiveIndicator(
            condition="forum_selection",
            evidence_template=(
                "Forum selection provision in charter, limiting "
                "multi-jurisdictional exposure"
            ),
            section_origin="SECT6",
            theory_mapping="D_GOVERNANCE (defense provisions)",
            check_fn=check_forum_selection,
            scoring_relevance=5.5,
        ),
        PositiveIndicator(
            condition="positive_fcf",
            evidence_template=(
                "Positive free cash flow from most recent period, "
                "indicating operational strength"
            ),
            section_origin="SECT3",
            theory_mapping="A_DISCLOSURE (cash generation)",
            check_fn=check_positive_fcf,
            scoring_relevance=5.5,
        ),
        PositiveIndicator(
            condition="low_volatility",
            evidence_template=(
                "90-day volatility below sector typical threshold, "
                "indicating stable price action"
            ),
            section_origin="SECT4",
            theory_mapping="B_GUIDANCE (price stability)",
            check_fn=check_low_volatility,
            scoring_relevance=5.0,
        ),
    ]


# Module-level constant built once
POSITIVE_INDICATORS: list[PositiveIndicator] = build_positive_indicators()


__all__ = [
    "POSITIVE_INDICATORS",
    "PositiveIndicator",
    "build_positive_indicators",
]
