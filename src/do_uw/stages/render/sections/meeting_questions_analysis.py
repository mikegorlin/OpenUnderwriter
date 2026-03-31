"""Meeting prep question generators -- bear cases, peril map, mispricing alerts.

Generates meeting questions from Phase 27 analytical output:
- Bear case scenarios -> FORWARD_INDICATOR questions
- Peril map plaintiff assessments -> CREDIBILITY_TEST questions
- Market intelligence mispricing -> CLARIFICATION questions

SC5: Meeting prep from analysis. Each question traces to a specific
analytical finding (bear case title, plaintiff lens, pricing alert).

Split from meeting_questions.py for 500-line compliance.
"""

from __future__ import annotations

import logging

from do_uw.models.peril import PerilMap
from do_uw.models.state import AnalysisState
from do_uw.stages.render.sections.meeting_questions import MeetingQuestion, _company_name

logger = logging.getLogger(__name__)

_ELEVATED_BANDS = {"MODERATE", "ELEVATED", "HIGH"}


def _deserialize_peril_map(state: AnalysisState) -> PerilMap | None:
    """Deserialize PerilMap from state.analysis.peril_map dict."""
    if state.analysis is None or state.analysis.peril_map is None:
        return None
    try:
        return PerilMap.model_validate(state.analysis.peril_map)
    except Exception:
        logger.debug("Failed to deserialize peril map for meeting questions")
        return None


# ---------------------------------------------------------------------------
# BEAR CASE questions -- from peril map bear case analysis (SC5)
# ---------------------------------------------------------------------------


def generate_bear_case_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Generate meeting questions from bear case scenarios.

    For each bear case rated MODERATE or HIGH exposure, creates a
    FORWARD_INDICATOR question asking how the company plans to address
    the specific scenario. Source traces back to the bear case analysis.
    """
    peril_map = _deserialize_peril_map(state)
    if peril_map is None:
        return []

    name = _company_name(state)
    questions: list[MeetingQuestion] = []
    for bc in peril_map.bear_cases:
        if bc.probability_band not in _ELEVATED_BANDS:
            continue
        questions.append(
            MeetingQuestion(
                question=(
                    f"What is {name}'s plan to address the "
                    f"'{bc.theory}' scenario? {bc.committee_summary}"
                ),
                category="FORWARD_INDICATOR",
                priority=8.5 if bc.probability_band == "HIGH" else 7.5,
                context=(
                    f"Bear case analysis identified a plausible "
                    f"{bc.plaintiff_type} litigation scenario with "
                    f"{bc.probability_band} probability and "
                    f"{bc.severity_estimate} severity."
                ),
                good_answer=(
                    "Company has specific mitigation measures in place "
                    "or the scenario conditions have changed favorably."
                ),
                bad_answer=(
                    "Company is unaware of the risk or has no "
                    "mitigation plan. Scenario conditions persist or worsen."
                ),
                follow_up=(
                    f"Document response for {bc.theory} bear case. "
                    f"If unmitigated, adjust claim probability upward."
                ),
                source_finding=f"Bear Case Analysis: {bc.theory}",
                expected_answer_range=(
                    "Specific mitigation actions or changed circumstances."
                ),
            )
        )
    return questions


# ---------------------------------------------------------------------------
# PERIL MAP questions -- elevated plaintiff lens assessments (SC5)
# ---------------------------------------------------------------------------


def generate_peril_map_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Generate meeting questions from elevated peril map lenses.

    For each PlaintiffAssessment with ELEVATED or higher probability,
    creates a CREDIBILITY_TEST question about plaintiff-specific exposure.
    """
    peril_map = _deserialize_peril_map(state)
    if peril_map is None:
        return []

    name = _company_name(state)
    questions: list[MeetingQuestion] = []
    elevated_bands = {"ELEVATED", "HIGH"}
    for assessment in peril_map.assessments:
        if assessment.probability_band not in elevated_bands:
            continue
        primary_finding = (
            assessment.key_findings[0]
            if assessment.key_findings
            else "elevated risk signals"
        )
        questions.append(
            MeetingQuestion(
                question=(
                    f"How would {name} defend against a "
                    f"{assessment.plaintiff_type} action based on "
                    f"{primary_finding}?"
                ),
                category="CREDIBILITY_TEST",
                priority=8.0 if assessment.probability_band == "HIGH" else 7.0,
                context=(
                    f"Peril map shows {assessment.probability_band} probability "
                    f"for {assessment.plaintiff_type} claims with "
                    f"{assessment.severity_band} severity. "
                    f"{assessment.triggered_signal_count} of "
                    f"{assessment.evaluated_signal_count} evaluated checks triggered."
                ),
                good_answer=(
                    "Company has strong defense posture: forum provisions, "
                    "safe harbor compliance, or factual basis to rebut claims."
                ),
                bad_answer=(
                    "Weak defense posture or no awareness of "
                    f"{assessment.plaintiff_type} exposure."
                ),
                follow_up=(
                    f"Document {assessment.plaintiff_type} defense posture. "
                    f"Review exposure for tower positioning."
                ),
                source_finding=f"Peril Map: {assessment.plaintiff_type} lens",
                expected_answer_range="Defense strategy details and legal counsel assessment.",
            )
        )
    return questions


# ---------------------------------------------------------------------------
# MISPRICING questions -- pricing divergence alerts (SC5)
# ---------------------------------------------------------------------------


def generate_mispricing_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Generate questions from model-vs-market mispricing alerts.

    If market intelligence shows significant pricing divergence,
    creates CLARIFICATION questions to investigate the gap.
    """
    if state.executive_summary is None:
        return []
    mi = state.executive_summary.deal_context.market_intelligence
    if mi is None:
        return []

    questions: list[MeetingQuestion] = []
    if mi.mispricing_alert is not None:
        questions.append(
            MeetingQuestion(
                question=(
                    f"The market appears to be mispricing this risk: "
                    f"{mi.mispricing_alert}. What factors explain "
                    f"the pricing divergence?"
                ),
                category="CLARIFICATION",
                priority=7.5,
                context=(
                    "Significant deviation between market pricing and model "
                    "indication may signal information asymmetry or market "
                    "inefficiency that affects underwriting positioning."
                ),
                good_answer=(
                    "Identifiable factors (loss history, market cycle, "
                    "competition) explain the divergence."
                ),
                bad_answer="No clear explanation for the pricing gap.",
                follow_up=(
                    "Document pricing divergence rationale. Consider "
                    "whether the model or market is better calibrated."
                ),
                source_finding="Pricing Divergence Alert",
                expected_answer_range="Market dynamics or loss development data.",
            )
        )
    if mi.model_vs_market_alert is not None:
        questions.append(
            MeetingQuestion(
                question=(
                    f"Model-indicated pricing diverges from market: "
                    f"{mi.model_vs_market_alert}. What is your view "
                    f"on the appropriate pricing level?"
                ),
                category="CLARIFICATION",
                priority=7.0,
                context=(
                    "Model-vs-market divergence may indicate either model "
                    "calibration issues or market mispricing opportunity."
                ),
                good_answer=(
                    "Clear view on pricing with supporting data points."
                ),
                bad_answer="Unable to articulate pricing rationale.",
                follow_up=(
                    "Compare model output with broker indications. "
                    "Document pricing basis for committee."
                ),
                source_finding="Model vs. Market Pricing Alert",
                expected_answer_range="Pricing rationale with supporting evidence.",
            )
        )
    return questions


__all__ = [
    "generate_bear_case_questions",
    "generate_mispricing_questions",
    "generate_peril_map_questions",
]
