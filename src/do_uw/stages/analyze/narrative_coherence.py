"""Narrative coherence assessment (SECT5-10).

Rule-based (not LLM) checks for alignment between management claims
and observable data. Identifies gaps across four dimensions:
- Strategy vs results
- Insider behavior vs stated confidence
- Filing tone vs financial trajectory
- Employee sentiment vs management messaging

Each check produces a SourcedValue[str] with LOW confidence and
"AI Assessment" label per DATA-14.

Usage:
    coherence, report = assess_narrative_coherence(state)
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import NarrativeCoherence
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.sentiment_analysis import (
    analyze_lm_sentiment,
    get_mda_text,
)
from do_uw.stages.extract.sourced import (
    now,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

COHERENCE_EXPECTED: list[str] = [
    "strategy_vs_results",
    "insider_vs_confidence",
    "tone_vs_financials",
    "employee_vs_management",
    "overall_assessment",
]


# ---------------------------------------------------------------------------
# Coherence check helpers
# ---------------------------------------------------------------------------


def _check_strategy_vs_results(
    state: AnalysisState,
) -> SourcedValue[str] | None:
    """Check if growth claims align with revenue trends.

    Growth claims in MD&A + declining revenue -> MISALIGNED.
    """
    mda_text = get_mda_text(state)
    if not mda_text:
        return None

    # Check for growth language.
    mda_lower = mda_text.lower()
    growth_phrases = [
        "revenue growth",
        "growing revenue",
        "strong growth",
        "growth strategy",
        "accelerating growth",
        "expanding market",
    ]
    has_growth_claims = any(p in mda_lower for p in growth_phrases)

    if not has_growth_claims:
        return SourcedValue[str](
            value="ALIGNED",
            source="AI Assessment: 10-K MD&A vs financials",
            confidence=Confidence.LOW,
            as_of=now(),
        )

    # Check revenue trend from financials.
    revenue_declining = _is_revenue_declining(state)
    if revenue_declining is None:
        return None

    alignment = "MISALIGNED" if revenue_declining else "ALIGNED"
    return SourcedValue[str](
        value=alignment,
        source="AI Assessment: 10-K MD&A vs financials",
        confidence=Confidence.LOW,
        as_of=now(),
    )


def _is_revenue_declining(state: AnalysisState) -> bool | None:
    """Check if revenue is declining year-over-year."""
    if state.extracted is None or state.extracted.financials is None:
        return None
    stmts = state.extracted.financials.statements
    if stmts.income_statement is None:
        return None

    for item in stmts.income_statement.line_items:
        if _is_revenue_label(item.label):
            if item.yoy_change is not None:
                return item.yoy_change < 0.0
    return None


def _is_revenue_label(label: str) -> bool:
    """Check if a financial line item label represents revenue.

    Uses substring matching to handle variations like
    "Total revenue / net sales", "Revenue from contracts", etc.
    """
    lower = label.lower()
    # Exact matches for common labels.
    if lower in ("total revenue", "revenue", "net revenue"):
        return True
    # Substring matches for compound labels.
    return lower.startswith("total revenue") or lower.startswith(
        "net revenue"
    )


def _is_net_income_label(label: str) -> bool:
    """Check if a financial line item label represents net income.

    Uses substring matching to handle variations like
    "Net income attributable to...", "Net income / net loss", etc.
    """
    lower = label.lower()
    if lower in ("net income", "net income (loss)"):
        return True
    return lower.startswith("net income")


def _check_insider_vs_confidence(
    state: AnalysisState,
) -> SourcedValue[str] | None:
    """Check if insider trading aligns with management confidence.

    Management optimism + net insider selling -> MISALIGNED.
    """
    mda_text = get_mda_text(state)
    if not mda_text:
        return None

    lm_score = analyze_lm_sentiment(mda_text)
    is_positive_tone = lm_score.get("polarity", 0.0) > 0.0

    # Check insider trading direction.
    insider_direction = _get_insider_direction(state)
    if insider_direction is None:
        return None

    is_net_selling = insider_direction == "NET_SELLING"

    if is_positive_tone and is_net_selling:
        alignment = "MISALIGNED"
    else:
        alignment = "ALIGNED"

    return SourcedValue[str](
        value=alignment,
        source="AI Assessment: L-M tone vs Form 4 insider trading",
        confidence=Confidence.LOW,
        as_of=now(),
    )


def _get_insider_direction(state: AnalysisState) -> str | None:
    """Get net insider buying/selling direction from extracted data."""
    if state.extracted is None or state.extracted.market is None:
        return None

    direction_sv = state.extracted.market.insider_trading.net_buying_selling
    if direction_sv is not None:
        return direction_sv.value
    return None


def _check_tone_vs_financials(
    state: AnalysisState,
    lm_polarity: float,
) -> SourcedValue[str] | None:
    """Check if L-M tone matches financial trajectory.

    Positive L-M polarity + deteriorating financials -> MISALIGNED.
    """
    if state.extracted is None or state.extracted.financials is None:
        return None

    is_positive = lm_polarity > 0.0

    deteriorating = _are_financials_deteriorating(state)
    if deteriorating is None:
        return None

    if is_positive and deteriorating:
        alignment = "MISALIGNED"
    else:
        alignment = "ALIGNED"

    return SourcedValue[str](
        value=alignment,
        source="AI Assessment: L-M tone vs financial trajectory",
        confidence=Confidence.LOW,
        as_of=now(),
    )


def _are_financials_deteriorating(state: AnalysisState) -> bool | None:
    """Check if financials show deteriorating trend.

    Uses revenue decline + profitability decline as indicators.
    """
    if state.extracted is None or state.extracted.financials is None:
        return None

    stmts = state.extracted.financials.statements
    if stmts.income_statement is None:
        return None

    signals: list[bool] = []
    for item in stmts.income_statement.line_items:
        if _is_revenue_label(item.label):
            if item.yoy_change is not None:
                signals.append(item.yoy_change < 0.0)
        elif _is_net_income_label(item.label):
            if item.yoy_change is not None:
                signals.append(item.yoy_change < -10.0)

    if not signals:
        return None

    # Deteriorating if majority of signals are negative.
    return sum(signals) > len(signals) / 2


def _check_employee_vs_management(
    state: AnalysisState,
    glassdoor_rating: SourcedValue[float] | None,
    lm_polarity: float,
) -> SourcedValue[str] | None:
    """Check if employee sentiment aligns with management messaging.

    Declining Glassdoor (< 3.0) + positive messaging -> MISALIGNED.
    """
    if glassdoor_rating is None:
        return None

    is_negative_employee = glassdoor_rating.value < 3.0
    is_positive_mgmt = lm_polarity > 0.0

    if is_negative_employee and is_positive_mgmt:
        alignment = "MISALIGNED"
    else:
        alignment = "ALIGNED"

    return SourcedValue[str](
        value=alignment,
        source="AI Assessment: Glassdoor vs L-M management tone",
        confidence=Confidence.LOW,
        as_of=now(),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def assess_narrative_coherence(
    state: AnalysisState,
) -> tuple[NarrativeCoherence, ExtractionReport]:
    """Assess cross-source narrative coherence (rule-based, not LLM).

    Identifies gaps between management narrative and observable data
    across four dimensions: strategy vs results, insider behavior vs
    stated confidence, tone vs financials, and employee sentiment
    vs management messaging.

    Each check produces a SourcedValue[str] with LOW confidence and
    "AI Assessment" label per DATA-14.

    Args:
        state: AnalysisState with extracted data populated.

    Returns:
        Tuple of (NarrativeCoherence, ExtractionReport).
    """
    coherence = NarrativeCoherence()
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "Cross-source AI assessment"

    # Get L-M polarity for reuse across checks.
    mda_text = get_mda_text(state)
    lm_score = analyze_lm_sentiment(mda_text)
    lm_polarity = lm_score.get("polarity", 0.0)

    # Get Glassdoor rating for employee check.
    glassdoor_rating: SourcedValue[float] | None = None
    if state.extracted and state.extracted.governance:
        glassdoor_rating = (
            state.extracted.governance.sentiment.glassdoor_rating
        )

    # 1. Strategy vs results.
    strategy_check = _check_strategy_vs_results(state)
    if strategy_check is not None:
        coherence.strategy_vs_results = strategy_check
        found.append("strategy_vs_results")
        if strategy_check.value == "MISALIGNED":
            coherence.coherence_flags.append(
                sourced_str(
                    "Growth claims contradict declining revenue",
                    "AI Assessment: MD&A vs financials",
                    Confidence.LOW,
                )
            )

    # 2. Insider vs confidence.
    insider_check = _check_insider_vs_confidence(state)
    if insider_check is not None:
        coherence.insider_vs_confidence = insider_check
        found.append("insider_vs_confidence")
        if insider_check.value == "MISALIGNED":
            coherence.coherence_flags.append(
                sourced_str(
                    "Management optimism contradicts net insider selling",
                    "AI Assessment: L-M tone vs Form 4",
                    Confidence.LOW,
                )
            )

    # 3. Tone vs financials.
    tone_check = _check_tone_vs_financials(state, lm_polarity)
    if tone_check is not None:
        coherence.tone_vs_financials = tone_check
        found.append("tone_vs_financials")
        if tone_check.value == "MISALIGNED":
            coherence.coherence_flags.append(
                sourced_str(
                    "Positive filing tone contradicts deteriorating financials",
                    "AI Assessment: L-M polarity vs financial trends",
                    Confidence.LOW,
                )
            )

    # 4. Employee vs management.
    employee_check = _check_employee_vs_management(
        state,
        glassdoor_rating,
        lm_polarity,
    )
    if employee_check is not None:
        coherence.employee_vs_management = employee_check
        found.append("employee_vs_management")
        if employee_check.value == "MISALIGNED":
            coherence.coherence_flags.append(
                sourced_str(
                    "Negative employee sentiment contradicts "
                    "positive management tone",
                    "AI Assessment: Glassdoor vs L-M tone",
                    Confidence.LOW,
                )
            )

    # 5. Overall assessment.
    misaligned_count = len(coherence.coherence_flags)
    if found:
        if misaligned_count == 0:
            overall = "COHERENT"
        elif misaligned_count <= 1:
            overall = "MINOR_GAPS"
        else:
            overall = "SIGNIFICANT_GAPS"

        coherence.overall_assessment = sourced_str(
            overall,
            f"AI Assessment: {misaligned_count} coherence gaps "
            f"from {len(found)} checks",
            Confidence.LOW,
        )
        found.append("overall_assessment")
    else:
        warnings.append(
            "Insufficient data for narrative coherence assessment"
        )

    report = create_report(
        extractor_name="narrative_coherence",
        expected=COHERENCE_EXPECTED,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return coherence, report
