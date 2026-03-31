"""Meeting prep question generators -- clarification and forward indicators.

Walks the AnalysisState model to generate priority-ranked questions
for underwriter meetings. Questions reference ACTUAL extracted data.

Categories: CLARIFICATION, FORWARD_INDICATOR.
Split from meeting_prep.py for 500-line compliance.
Gap filler and credibility test generators in meeting_questions_gap.py.
Bear case, peril map, and mispricing generators in meeting_questions_analysis.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.render.sca_counter import count_active_genuine_scas, get_active_genuine_scas


@dataclass
class MeetingQuestion:
    """A single meeting prep question with context and follow-up guidance.

    Each question references actual extracted data via source_finding,
    making questions company-specific rather than boilerplate.
    """

    question: str
    category: str  # CLARIFICATION | FORWARD_INDICATOR | GAP_FILLER | CREDIBILITY_TEST
    priority: float  # Higher = more important (0-10 scale)
    context: str  # Why this matters for D&O
    good_answer: str  # What a reassuring answer looks like
    bad_answer: str  # What a concerning answer looks like
    follow_up: str  # If concerning: next steps / escalation triggers
    source_finding: str = ""  # Specific data point triggering this question
    expected_answer_range: str = ""  # What the answer should look like


def _company_name(state: AnalysisState) -> str:
    """Extract company name from state, falling back to ticker."""
    if state.company and state.company.identity.legal_name:
        return state.company.identity.legal_name.value
    return state.ticker


# ---------------------------------------------------------------------------
# CLARIFICATION questions -- LOW confidence data needing verification
# ---------------------------------------------------------------------------


def generate_clarification_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Scan for LOW confidence data and conflicting sources.

    Generates questions for every data point where confidence is LOW,
    so the underwriter can verify during the meeting.
    """
    questions: list[MeetingQuestion] = []

    if state.company is not None:
        _scan_profile_confidence(state, questions)
    if state.extracted is not None:
        _scan_extracted_confidence(state, questions)

    return questions


def _scan_profile_confidence(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Scan company profile fields for LOW confidence SourcedValues."""
    profile = state.company
    if profile is None:
        return

    _check_sv_field(
        questions,
        sv=profile.market_cap,
        field_label="Market capitalization",
        context="Market cap determines filing rate multipliers and severity ranges.",
        expected_range="Should match latest SEC filing or Bloomberg data.",
    )
    _check_sv_field(
        questions,
        sv=profile.employee_count,
        field_label="Employee count",
        context="Employee count affects employment practices liability exposure.",
        expected_range="Should match latest 10-K or proxy filing.",
    )
    for seg in profile.revenue_segments:
        if seg.confidence == Confidence.LOW:
            val = seg.value
            seg_name = str(val.get("segment", "Unknown"))
            questions.append(
                MeetingQuestion(
                    question=(
                        f"Revenue segment '{seg_name}' data is LOW "
                        f"confidence (source: {seg.source}). Can you "
                        f"confirm the current revenue breakdown "
                        f"by segment?"
                    ),
                    category="CLARIFICATION",
                    priority=6.0,
                    context="Revenue concentration affects disclosure risk under Theory A.",
                    good_answer="Provides audited segment breakdown consistent with 10-K.",
                    bad_answer="Segments have shifted significantly from last filing.",
                    follow_up=(
                        "Request updated segment data. Flag for "
                        "disclosure risk if materially different."
                    ),
                    source_finding=f"Revenue segment '{seg_name}' from {seg.source}",
                    expected_answer_range="Audited segment breakdown within 5% of filing.",
                )
            )


def _scan_extracted_confidence(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Scan extracted data for LOW confidence SourcedValues."""
    ext = state.extracted
    if ext is None:
        return

    gov = ext.governance
    if gov is not None:
        _check_sv_field(
            questions,
            sv=gov.board.independence_ratio,
            field_label="Board independence ratio",
            context="Board independence is a key governance quality indicator for D&O.",
            expected_range="Typically 60-90% for public companies.",
        )
        _check_sv_field(
            questions,
            sv=gov.board.ceo_chair_duality,
            field_label="CEO/Chair duality",
            context="CEO-Chair duality increases governance concentration risk.",
            expected_range="Yes/No with succession plan details.",
        )

    market = ext.market
    if market is not None:
        _check_sv_field(
            questions,
            sv=market.short_interest.short_pct_float,
            field_label="Short interest (% of float)",
            context="Elevated short interest often precedes securities class actions.",
            expected_range="Recent exchange data, updated bi-monthly.",
        )

    # AI risk data
    ai_risk = ext.ai_risk
    name = _company_name(state)
    if ai_risk is not None and ai_risk.narrative_confidence == "LOW":
        questions.append(
            MeetingQuestion(
                question=(
                    f"{name}'s AI risk narrative has LOW confidence "
                    f"(model: {ai_risk.industry_model_id}). "
                    f"How does {name} view AI as impacting "
                    f"its business model?"
                ),
                category="CLARIFICATION",
                priority=5.5,
                context="AI transformation risk drives Section 8 scoring.",
                good_answer="Company has clear AI strategy with board oversight.",
                bad_answer="No AI strategy or dismissive of AI impact.",
                follow_up="Document AI posture for Section 8 assessment.",
                source_finding=(
                    f"AI risk narrative from {ai_risk.industry_model_id} model"
                ),
                expected_answer_range="Concrete AI initiatives or risk mitigation plans.",
            )
        )


def _check_sv_field(
    questions: list[MeetingQuestion],
    sv: SourcedValue[Any] | None,
    field_label: str,
    context: str,
    expected_range: str = "",
) -> None:
    """Add a clarification question if a SourcedValue is LOW confidence."""
    if sv is None or sv.confidence != Confidence.LOW:
        return
    questions.append(
        MeetingQuestion(
            question=(
                f"{field_label} is reported as {sv.value} "
                f"with LOW confidence (source: {sv.source}). "
                f"Can you confirm the current value?"
            ),
            category="CLARIFICATION",
            priority=5.0,
            context=context,
            good_answer=f"Confirms {field_label} with audited/official documentation.",
            bad_answer="Cannot confirm or value differs materially from reported.",
            follow_up=f"Document discrepancy. Adjust {field_label} assumption in scoring.",
            source_finding=f"{field_label}: {sv.value} [{sv.source}, {sv.confidence}]",
            expected_answer_range=expected_range,
        )
    )


# ---------------------------------------------------------------------------
# FORWARD_INDICATOR questions -- upcoming events and deteriorating trends
# ---------------------------------------------------------------------------


def generate_forward_indicator_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Scan for upcoming events and deteriorating trends.

    Questions reference specific extracted data points that signal
    forward-looking D&O risk.
    """
    questions: list[MeetingQuestion] = []

    _check_distress_trends(state, questions)
    _check_short_interest(state, questions)
    _check_sol_windows(state, questions)
    _check_scoring_trajectory(state, questions)
    _check_ai_forward(state, questions)

    return questions


def _check_distress_trends(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for deteriorating distress indicators."""
    ext = state.extracted
    if ext is None or ext.financials is None:
        return
    name = _company_name(state)
    z_result = ext.financials.distress.altman_z_score
    if z_result is not None and z_result.score is not None and z_result.score < 1.81:
        questions.append(
            MeetingQuestion(
                question=(
                    f"{name}'s Altman Z-Score is {z_result.score:.2f}, "
                    f"in the distress zone (below 1.81). What "
                    f"is {name}'s plan to address "
                    f"leverage concerns?"
                ),
                category="FORWARD_INDICATOR",
                priority=9.0,
                context="Distressed companies have 3-5x higher SCA filing rates.",
                good_answer="Company has concrete deleveraging plan with timeline.",
                bad_answer="No clear plan or reliance on future revenue growth to deleverage.",
                follow_up=(
                    "Flag as F1 (Financial Distress) escalation. "
                    "Review debt maturity schedule."
                ),
                source_finding=f"Altman Z-Score: {z_result.score:.2f} (zone: {z_result.zone})",
                expected_answer_range="Debt-to-equity ratio trend and maturity schedule.",
            )
        )


def _check_short_interest(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for elevated short interest."""
    ext = state.extracted
    if ext is None or ext.market is None:
        return
    name = _company_name(state)
    si = ext.market.short_interest.short_pct_float
    if si is not None and si.value > 10.0:
        questions.append(
            MeetingQuestion(
                question=(
                    f"{name}'s short interest is {si.value:.1f}% of float, "
                    f"which is elevated. Are you aware of any "
                    f"active short seller reports or campaigns targeting {name}?"
                ),
                category="FORWARD_INDICATOR",
                priority=8.0,
                context="Short seller reports often precede securities fraud allegations.",
                good_answer=(
                    "Short interest is passive/index-related, no active short campaigns."
                ),
                bad_answer="Active short seller thesis exists or company is unaware.",
                follow_up=(
                    "Search for short seller reports. Review for "
                    "potential Theory A triggers."
                ),
                source_finding=f"Short interest: {si.value:.1f}% of float [{si.source}]",
                expected_answer_range="Short interest context: passive vs active shorts.",
            )
        )


def _check_sol_windows(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for open statute of limitations windows."""
    ext = state.extracted
    if ext is None or ext.litigation is None:
        return
    name = _company_name(state)
    sol_windows = ext.litigation.sol_map
    if sol_windows:
        open_windows = [w for w in sol_windows if w.window_open]
        if open_windows:
            window_details = "; ".join(
                f"{w.claim_type}: {w.trigger_date} to {w.sol_expiry}"
                for w in open_windows[:3]
            )
            questions.append(
                MeetingQuestion(
                    question=(
                        f"{name} has {len(open_windows)} open "
                        f"statute of limitations window(s) for "
                        f"potential securities claims. Are there "
                        f"any pending or threatened suits against {name}?"
                    ),
                    category="FORWARD_INDICATOR",
                    priority=9.5,
                    context="Open SOL windows mean claims can still be filed for past events.",
                    good_answer=(
                        "No threatened litigation; company counsel "
                        "confirms no demand letters."
                    ),
                    bad_answer="Pending demand letters or pre-suit investigation.",
                    follow_up=(
                        "Request copies of any demand letters. "
                        "Adjust claim probability upward."
                    ),
                    source_finding=f"Open SOL windows: {window_details}",
                    expected_answer_range="Litigation counsel confirmation.",
                )
            )


def _check_scoring_trajectory(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for concerning scoring results."""
    scoring = state.scoring
    if scoring is None:
        return
    name = _company_name(state)
    if scoring.quality_score < 50:
        tier_label = scoring.tier.tier if scoring.tier else "N/A"
        factors_str = ", ".join(
            f"{f.factor_id}: {f.points_deducted:.1f}pts" for f in scoring.factor_scores[:3]
        ) if scoring.factor_scores else "N/A"
        questions.append(
            MeetingQuestion(
                question=(
                    f"{name}'s quality score is "
                    f"{scoring.quality_score:.1f}/100 "
                    f"({tier_label} tier). What mitigating "
                    f"factors should we consider for {name}?"
                ),
                category="FORWARD_INDICATOR",
                priority=8.5,
                context="Low quality scores indicate elevated D&O claim probability.",
                good_answer=(
                    "Company can point to recent governance improvements "
                    "or risk reduction."
                ),
                bad_answer="No meaningful mitigation or deteriorating trend.",
                follow_up="Document tier classification rationale. Consider WALK or NO_TOUCH.",
                source_finding=f"Quality: {scoring.quality_score:.1f}/100, Top factors: {factors_str}",
                expected_answer_range="Specific remediation actions with timelines.",
            )
        )


def _check_ai_forward(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for AI forward indicators requiring meeting discussion."""
    ext = state.extracted
    if ext is None or ext.ai_risk is None:
        return
    ai = ext.ai_risk
    name = _company_name(state)
    if ai.overall_score >= 70.0:
        questions.append(
            MeetingQuestion(
                question=(
                    f"{name}'s AI risk score is {ai.overall_score:.0f}/100 "
                    f"(HIGH). What is {name}'s AI strategy "
                    f"and how is the board overseeing AI risks?"
                ),
                category="FORWARD_INDICATOR",
                priority=7.5,
                context="High AI risk scores correlate with competitive displacement claims.",
                good_answer="Board has AI oversight committee; documented strategy.",
                bad_answer="No AI strategy or board-level oversight.",
                follow_up="Document AI governance posture for Section 8.",
                source_finding=(
                    f"AI risk: {ai.overall_score:.0f}/100 "
                    f"({ai.industry_model_id})"
                ),
                expected_answer_range="AI governance framework and investment details.",
            )
        )


__all__ = [
    "MeetingQuestion",
    "generate_clarification_questions",
    "generate_forward_indicator_questions",
]
