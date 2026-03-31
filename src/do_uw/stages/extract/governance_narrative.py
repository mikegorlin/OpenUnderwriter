"""Governance summary narrative generation helpers.

Rule-based governance summary synthesizing 5 key dimensions:
leadership stability, board quality, compensation concerns,
ownership/activist risks, and sentiment/coherence flags.

Split from extract_governance.py to stay under 500-line limit.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)


def generate_governance_summary(gov: GovernanceData) -> SourcedValue[str]:
    """Generate rule-based governance summary from 5 dimensions.

    Synthesizes:
    1. Leadership stability assessment
    2. Board quality highlights
    3. Compensation concerns
    4. Ownership/activist risks
    5. Sentiment/coherence flags

    Returns a SourcedValue[str] with LOW confidence since this is
    derived from other extracted data (not directly from filings).
    """
    parts: list[str] = []

    _add_leadership_summary(parts, gov.leadership)
    _add_board_summary(parts, gov.board_forensics, gov.governance_score)
    _add_compensation_summary(parts, gov.comp_analysis)
    _add_ownership_summary(parts, gov.ownership)
    _add_sentiment_coherence_summary(
        parts, gov.sentiment, gov.narrative_coherence
    )

    narrative = " ".join(parts) if parts else (
        "Insufficient governance data available to generate a "
        "comprehensive assessment."
    )

    return SourcedValue[str](
        value=narrative,
        source="Rule-based synthesis of governance extraction results",
        confidence=Confidence.LOW,
        as_of=datetime.now(tz=UTC),
    )


def _add_leadership_summary(
    parts: list[str], leadership: LeadershipStability
) -> None:
    """Add leadership stability sentence."""
    red_count = len(leadership.red_flags)
    departure_count = len(leadership.departures_18mo)

    if red_count > 0:
        parts.append(
            f"Leadership stability raises {red_count} red flag(s)"
            f" with {departure_count} departure(s) in 18 months."
        )
    elif departure_count > 0:
        parts.append(
            f"Leadership has seen {departure_count} departure(s) "
            f"in the last 18 months but no critical stability flags."
        )
    elif leadership.avg_tenure_years and leadership.avg_tenure_years.value:
        avg = leadership.avg_tenure_years.value
        parts.append(
            f"Leadership team is stable with average tenure of "
            f"{avg:.1f} years."
        )


def _add_board_summary(
    parts: list[str],
    profiles: list[BoardForensicProfile],
    score: GovernanceQualityScore,
) -> None:
    """Add board quality sentence."""
    if score.total_score:
        total = score.total_score.value
        if total >= 70:
            parts.append(
                f"Board governance scores well ({total:.0f}/100)"
                f" across {len(profiles)} directors."
            )
        elif total >= 40:
            parts.append(
                f"Board governance is moderate ({total:.0f}/100)"
                f" with some areas for improvement."
            )
        else:
            parts.append(
                f"Board governance is weak ({total:.0f}/100),"
                f" raising oversight concerns."
            )
    elif profiles:
        overboarded = sum(1 for p in profiles if p.is_overboarded)
        if overboarded > 0:
            parts.append(
                f"{overboarded} of {len(profiles)} directors "
                f"are overboarded (4+ public boards)."
            )


def _add_compensation_summary(
    parts: list[str], comp: CompensationAnalysis
) -> None:
    """Add compensation concern sentence."""
    concerns: list[str] = []

    if comp.say_on_pay_pct:
        if comp.say_on_pay_pct.value < 70.0:
            concerns.append(
                f"low say-on-pay support ({comp.say_on_pay_pct.value:.0f}%)"
            )

    if comp.related_party_transactions:
        concerns.append(
            f"{len(comp.related_party_transactions)} "
            f"related-party transaction(s)"
        )

    if comp.ceo_pay_ratio:
        if comp.ceo_pay_ratio.value > 500:
            concerns.append(
                f"elevated CEO pay ratio ({comp.ceo_pay_ratio.value:.0f}:1)"
            )

    if concerns:
        parts.append(
            "Compensation concerns include: "
            + "; ".join(concerns) + "."
        )


def _add_ownership_summary(
    parts: list[str], ownership: OwnershipAnalysis
) -> None:
    """Add ownership/activist risk sentence."""
    if (
        ownership.activist_risk_assessment
        and ownership.activist_risk_assessment.value
    ):
        risk = ownership.activist_risk_assessment.value
        if risk in ("HIGH", "MEDIUM"):
            activist_names = [
                a.value for a in ownership.known_activists if a.value
            ]
            if activist_names:
                parts.append(
                    f"Activist risk is {risk} with known positions "
                    f"from {', '.join(activist_names[:3])}."
                )
            else:
                parts.append(f"Activist risk is assessed as {risk}.")

    if ownership.has_dual_class and ownership.has_dual_class.value:
        parts.append("Dual-class share structure concentrates voting control.")


def _add_sentiment_coherence_summary(
    parts: list[str],
    sentiment: SentimentProfile,
    coherence: NarrativeCoherence,
) -> None:
    """Add sentiment and coherence flags sentence."""
    flags: list[str] = []

    if (
        sentiment.management_tone_trajectory
        and sentiment.management_tone_trajectory.value == "DETERIORATING"
    ):
        flags.append("deteriorating management tone")

    if (
        sentiment.qa_evasion_score
        and sentiment.qa_evasion_score.value > 0.5
    ):
        flags.append("elevated Q&A evasion")

    if (
        coherence.overall_assessment
        and coherence.overall_assessment.value == "SIGNIFICANT_GAPS"
    ):
        flags.append("significant narrative coherence gaps")

    if flags:
        parts.append("Sentiment signals: " + "; ".join(flags) + ".")
