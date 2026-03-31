"""Meeting prep question generators -- gap filler and credibility tests.

Walks the AnalysisState model to generate priority-ranked questions.
Questions reference ACTUAL extracted data, not boilerplate.

GAP_FILLER: Scan for missing data fields.
CREDIBILITY_TEST: Scan for narrative mismatches and undisclosed patterns.

Split from meeting_questions.py for 500-line compliance.
"""

from __future__ import annotations

from do_uw.models.common import Confidence
from do_uw.models.state import AnalysisState
from do_uw.stages.render.sections.meeting_questions import MeetingQuestion, _company_name


def _gap(
    question: str, priority: float, context: str,
    good: str, bad: str, follow_up: str,
    source: str = "", expected: str = "",
) -> MeetingQuestion:
    """Shorthand constructor for GAP_FILLER questions."""
    return MeetingQuestion(
        question=question, category="GAP_FILLER", priority=priority,
        context=context, good_answer=good, bad_answer=bad,
        follow_up=follow_up, source_finding=source,
        expected_answer_range=expected,
    )


def _cred(
    question: str, priority: float, context: str,
    good: str, bad: str, follow_up: str,
    source: str = "", expected: str = "",
) -> MeetingQuestion:
    """Shorthand constructor for CREDIBILITY_TEST questions."""
    return MeetingQuestion(
        question=question, category="CREDIBILITY_TEST", priority=priority,
        context=context, good_answer=good, bad_answer=bad,
        follow_up=follow_up, source_finding=source,
        expected_answer_range=expected,
    )


# ---------------------------------------------------------------------------
# GAP_FILLER questions -- missing data that SHOULD exist
# ---------------------------------------------------------------------------


def generate_gap_filler_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Scan for None fields that SHOULD have data for D&O analysis."""
    questions: list[MeetingQuestion] = []
    # Company name used in sub-functions via _company_name(state)
    _check_governance_gaps(state, questions)
    _check_financial_gaps(state, questions)
    _check_market_gaps(state, questions)
    _check_litigation_gaps(state, questions)
    _check_ai_risk_gaps(state, questions)
    _check_single_source_data(state, questions)
    return questions


def _check_governance_gaps(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for missing governance data."""
    ext = state.extracted
    if ext is None:
        return
    gov = ext.governance
    if gov is None:
        questions.append(_gap(
            "No governance data was extracted. What is the current board composition?",
            8.0, "Governance quality is a major D&O scoring factor (F9).",
            "Provides proxy statement or board details with independence ratios.",
            "Cannot provide board information.",
            "Request most recent proxy (DEF 14A). Score governance conservatively.",
            "ExtractedData.governance is None",
            "Board size, independence %, committee structure.",
        ))
        return

    if gov.board.independence_ratio is None:
        questions.append(_gap(
            "Board independence ratio could not be determined from proxy filings. "
            "What is the current board composition?",
            7.0, "Board independence affects governance scoring and D&O exposure.",
            "Provides independent/total director count with qualifications.",
            "Board composition is unclear or majority non-independent.",
            "Document board composition manually. Adjust F9 scoring accordingly.",
            "GovernanceData.board.independence_ratio is None",
            "X of Y directors are independent (60-90% typical).",
        ))

    if gov.ownership.institutional_pct is None and gov.ownership.insider_pct is None:
        questions.append(_gap(
            "Ownership structure data was not available. What is the ownership breakdown?",
            6.5, "Ownership concentration affects governance risk and activist exposure.",
            "Provides institutional/insider/retail ownership percentages.",
            "Ownership structure is unclear or highly concentrated.",
            "Request ownership data from broker. Flag concentrated ownership for F9.",
            "OwnershipStructure: institutional_pct and insider_pct both None",
            "Institutional %, insider %, retail % breakdown.",
        ))

    if gov.compensation.ceo_pay_ratio is None and gov.compensation.say_on_pay_support_pct is None:
        questions.append(_gap(
            "CEO compensation data unavailable. What is the current CEO compensation structure?",
            5.5, "Executive compensation drives F9 governance scoring and clawback analysis.",
            "Provides total comp breakdown with performance vs time-based split.",
            "Compensation data is delayed or confidential.",
            "Review latest DEF 14A manually. Flag excessive comp for governance risk.",
            "CompensationFlags: ceo_pay_ratio and say_on_pay both None",
            "CEO pay ratio and say-on-pay vote results.",
        ))


def _check_financial_gaps(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for missing financial data."""
    ext = state.extracted
    if ext is None or ext.financials is None:
        return
    name = _company_name(state)
    fin = ext.financials
    if fin.statements.income_statement is None and fin.statements.balance_sheet is None:
        questions.append(_gap(
            f"{name}'s financial statements could not be extracted. Can you provide recent financials?",
            9.0, "Financial data is required for distress analysis and F1 scoring.",
            "Provides audited financials or confirms 10-K availability.",
            "Financials are delayed or under restatement.",
            "Obtain financials directly. Flag delayed filing as CRF red flag.",
            "FinancialStatements: income_statement and balance_sheet both None",
            "Latest audited financials or 10-Q.",
        ))
    z = fin.distress.altman_z_score
    o = fin.distress.ohlson_o_score
    if z is None and o is None:
        questions.append(_gap(
            f"{name}'s financial distress indicators could not be computed. Is {name} solvent?",
            8.0, "Distress scores (Z-Score, O-Score) drive F1 factor scoring.",
            "Company is investment-grade or has strong cash position.",
            "Going concern issues or covenant violations.",
            "Request credit rating or bank covenant compliance letter.",
            "DistressAnalysis: altman_z_score and ohlson_o_score both None",
            "Credit rating or current ratio > 1.5.",
        ))


def _check_market_gaps(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for missing market data."""
    ext = state.extracted
    if ext is None or ext.market is None:
        return
    name = _company_name(state)
    market = ext.market
    if market.stock.current_price is None and market.stock.high_52w is None:
        questions.append(_gap(
            f"{name}'s stock performance data is unavailable. Is {name} publicly traded?",
            7.5, "Stock performance drives F2 (Stock Decline) and F7 (Volatility).",
            "Stock data is available; acquisition tool had temporary issue.",
            "Company is pre-IPO, recently delisted, or in dark period.",
            "Verify trading status. Adjust scoring assumptions for non-traded entity.",
            "StockData: current_price and high_52w both None",
            "Current stock price and 52-week range.",
        ))


def _check_litigation_gaps(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for missing litigation data."""
    ext = state.extracted
    if ext is None or ext.litigation is None:
        questions.append(_gap(
            "No litigation data was extracted. Are there any pending or historical suits?",
            8.5, "Litigation history drives F3, F4, F5 scoring factors.",
            "No material litigation; confirms clean litigation history.",
            "Pending suits not captured in public records.",
            "Request litigation summary from broker. Run manual court search.",
            "ExtractedData.litigation is None",
            "Complete litigation summary from company counsel.",
        ))


def _check_ai_risk_gaps(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for missing AI risk data."""
    ext = state.extracted
    if ext is None or ext.ai_risk is None:
        return
    ai = ext.ai_risk
    if not ai.sub_dimensions:
        questions.append(_gap(
            "AI risk assessment used generic model without company-specific "
            "sub-dimension scoring. How does AI specifically impact this company?",
            5.0, "Generic AI scoring may understate or overstate actual exposure.",
            "Company provides specific AI impact assessment.",
            "No insight into AI-specific business impact.",
            "Document company-specific AI factors for manual Section 8 adjustment.",
            f"AI model: {ai.industry_model_id}, sub_dimensions: empty",
            "Company-specific AI use cases and risk factors.",
        ))


def _check_single_source_data(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for single-source data needing corroboration."""
    ext = state.extracted
    if ext is None:
        return
    gov = ext.governance
    if gov is not None:
        ind = gov.board.independence_ratio
        if ind is not None and ind.confidence == Confidence.MEDIUM:
            if "proxy" not in ind.source.lower() and "DEF 14A" not in ind.source:
                questions.append(_gap(
                    f"Board independence ratio ({ind.value}) sourced from "
                    f"{ind.source} only. Can you confirm from the latest proxy?",
                    4.5, "Single-source data benefits from cross-validation.",
                    "Confirms value matches proxy filing.",
                    "Value differs from proxy.",
                    "Update with proxy-sourced data. Adjust confidence to HIGH.",
                    f"Board independence: {ind.value} [{ind.source}]",
                    "DEF 14A board composition section.",
                ))


# ---------------------------------------------------------------------------
# CREDIBILITY_TEST questions
# ---------------------------------------------------------------------------


def generate_credibility_test_questions(
    state: AnalysisState,
) -> list[MeetingQuestion]:
    """Scan for narrative coherence mismatches and undisclosed patterns."""
    questions: list[MeetingQuestion] = []
    _check_narrative_coherence(state, questions)
    _check_red_flag_patterns(state, questions)
    _check_ai_disclosure_mismatch(state, questions)
    return questions


def _check_narrative_coherence(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check mismatches between governance narrative and financials."""
    ext = state.extracted
    if ext is None:
        return
    gov = ext.governance
    if gov is not None:
        coherence = gov.narrative_coherence
        if coherence.coherence_flags:
            flag_text = coherence.coherence_flags[0].value
            questions.append(_cred(
                f"Narrative coherence analysis detected gaps: "
                f"{flag_text or 'Governance narrative conflicts with financial reality'}. "
                f"What explains this discrepancy?",
                8.0,
                "Narrative mismatches may indicate management overconfidence or misleading disclosure.",
                "Explains gap with catalysts or timing differences.",
                "Cannot explain the discrepancy or deflects.",
                "Flag for disclosure risk. Consider Theory A (misleading statements) implications.",
                f"Coherence flag: {flag_text}",
                "Specific explanation with supporting evidence.",
            ))
    fin = ext.financials
    if fin is not None and ext.market is not None:
        z_result = fin.distress.altman_z_score
        if z_result is not None and z_result.score is not None and z_result.score < 1.81:
            eg = ext.market.earnings_guidance
            phi = eg.philosophy
            if phi and ("OPTIMISTIC" in phi.upper() or "AGGRESSIVE" in phi.upper()):
                questions.append(_cred(
                    "Company provides optimistic forward guidance despite distress-zone "
                    "financial metrics. What supports the growth projection?",
                    9.0, "Optimistic guidance during distress is a classic Theory A trigger.",
                    "Concrete evidence: signed contracts, backlog, market expansion.",
                    "Vague references to market conditions or management confidence.",
                    "Document guidance vs. reality gap. Flag as potential disclosure risk.",
                    f"Z-Score: {z_result.score:.2f} vs guidance philosophy: {phi}",
                    "Specific revenue pipeline data supporting optimistic guidance.",
                ))
    # Enhanced forensic model credibility tests (SC5)
    _check_forensic_model_specifics(state, questions)


def _check_red_flag_patterns(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for triggered red flags that need credibility testing."""
    scoring = state.scoring
    if scoring is None:
        return
    triggered = [rf for rf in scoring.red_flags if rf.triggered]
    if triggered:
        flag_details = "; ".join(
            f"{rf.flag_name or rf.flag_id}: {rf.evidence[0][:50] if rf.evidence else 'N/A'}"
            for rf in triggered[:3]
        )
        names = ", ".join(rf.flag_name or rf.flag_id for rf in triggered[:3])
        questions.append(_cred(
            f"Critical red flags triggered: {names}. Can you address these specific concerns?",
            9.5, "Red flags impose quality score ceilings and may indicate NO_TOUCH risk.",
            "Provides specific remediation or explains why flags are not material.",
            "Dismisses flags without substantive response.",
            "Red flags stand unless clear evidence of remediation. Document response.",
            f"Triggered CRFs: {flag_details}",
            "Remediation evidence or materiality argument.",
        ))
    patterns = [p for p in scoring.patterns_detected if p.detected]
    if patterns:
        names = ", ".join(p.pattern_name or p.pattern_id for p in patterns[:3])
        details = "; ".join(
            f"{p.pattern_name or p.pattern_id} ({len(p.triggers_matched)} triggers)"
            for p in patterns[:3]
        )
        questions.append(_cred(
            f"Composite risk patterns detected: {names}. "
            f"Are there circumstances that would mitigate these patterns?",
            8.5, "Composite patterns indicate correlated risk factors increasing claim probability.",
            "Points to structural changes that break the pattern.",
            "Patterns are continuing or accelerating.",
            "Document pattern evidence. Adjust tier classification if patterns persist.",
            f"Patterns: {details}",
            "Evidence of structural change since pattern formation.",
        ))


def _check_ai_disclosure_mismatch(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Check for mismatch between AI disclosure sentiment and investment."""
    ext = state.extracted
    if ext is None or ext.ai_risk is None:
        return
    ai = ext.ai_risk
    name = _company_name(state)
    if ai.disclosure_data.sentiment == "OPPORTUNITY" and ai.patent_activity.ai_patent_count == 0:
        questions.append(_cred(
            f"{name} frames AI as an opportunity in filings but has zero AI patent filings. "
            f"Is {name} actually investing in AI capabilities?",
            7.0,
            "Mismatch between AI disclosure (opportunity) and investment (no patents) "
            "may indicate misleading disclosure or unsubstantiated claims.",
            "Company has internal AI initiatives not reflected in patents.",
            "AI claims are aspirational without substantive investment.",
            "Flag disclosure-reality gap for Section 8 narrative.",
            f"AI sentiment: OPPORTUNITY, patents: 0, mentions: {ai.disclosure_data.mention_count}",
            "Specific AI R&D spending or partnership details.",
        ))
    cp = ai.competitive_position
    if (cp.adoption_stance == "LAGGING"
            and ai.disclosure_data.opportunity_mentions > ai.disclosure_data.threat_mentions):
        questions.append(_cred(
            f"{name} emphasizes AI opportunities in disclosures but ranks as LAGGING "
            f"vs peers in AI adoption. What explains this disconnect?",
            6.5,
            "Companies that overstate AI positioning relative to peers may face disclosure-based claims.",
            "Recent AI investments not yet reflected in public data.",
            "No evidence of catch-up investment.",
            "Document peer positioning gap for Section 8.",
            f"Adoption: LAGGING, opportunity mentions: {ai.disclosure_data.opportunity_mentions}, "
            f"peer avg: {cp.peer_avg_mentions:.1f}",
            "Specific AI investment or partnership timeline.",
        ))


def _check_forensic_model_specifics(
    state: AnalysisState, questions: list[MeetingQuestion]
) -> None:
    """Generate credibility tests with specific forensic model values.

    References actual Beneish M-Score, Altman Z-Score values and
    insider trading patterns for maximum question specificity.
    """
    ext = state.extracted
    if ext is None:
        return
    name = _company_name(state)
    fin = ext.financials
    if fin is not None:
        # Beneish M-Score with specific value
        m = fin.distress.beneish_m_score
        if m is not None and m.score is not None and m.score > -1.78:
            questions.append(_cred(
                f"{name}'s Beneish M-Score of {m.score:.2f} suggests possible "
                f"earnings manipulation (threshold: -1.78). How does "
                f"{name}'s management explain the accrual and revenue anomalies?",
                9.0,
                "M-Scores above -1.78 correlate with restatement risk, "
                "a primary SCA catalyst under Theory A (misleading financials).",
                "Specific operational explanations for accrual changes.",
                "Vague or dismissive response about earnings quality.",
                "Flag for enhanced audit scrutiny. Document for F1 factor.",
                f"Beneish M-Score: {m.score:.2f} (zone: {m.zone.value})",
                "Detailed explanation of DSO, accrual ratio, and revenue quality changes.",
            ))
        # Altman Z-Score with specific value (deeper credibility test)
        z = fin.distress.altman_z_score
        if z is not None and z.score is not None and z.zone.value == "grey":
            questions.append(_cred(
                f"{name}'s Altman Z-Score of {z.score:.2f} places {name} "
                f"in the grey zone (1.81-2.99). What specific actions "
                f"are being taken to improve {name}'s financial stability?",
                7.5,
                "Grey zone companies face heightened fiduciary scrutiny "
                "and elevated D&O exposure if conditions deteriorate.",
                "Concrete deleveraging or profitability improvement plan.",
                "No specific plan or reliance on market conditions.",
                "Monitor trajectory quarterly. Flag if Z-Score declines.",
                f"Altman Z-Score: {z.score:.2f} (zone: grey)",
                "Financial improvement roadmap with milestones.",
            ))
    # Insider trading cluster patterns
    market = ext.market if ext else None
    if market is not None and market.insider_analysis:
        insider = market.insider_analysis
        if insider.cluster_events:
            cluster = insider.cluster_events[0]
            exec_count = cluster.insider_count if hasattr(cluster, 'insider_count') else 0
            window_days = cluster.window_days if hasattr(cluster, 'window_days') else 0
            if exec_count >= 2:
                questions.append(_cred(
                    f"{exec_count} executives sold within a "
                    f"{window_days}-day window. What prompted "
                    f"the synchronized selling?",
                    8.5,
                    "Cluster insider selling within a short window "
                    "is a leading indicator of securities class actions.",
                    "Pre-planned 10b5-1 trading plan executions.",
                    "Discretionary sales outside 10b5-1 plans.",
                    "Document trading plan status. Flag for F3 factor.",
                    f"Insider cluster: {exec_count} sellers in {window_days} days",
                    "10b5-1 plan documentation or personal financial reasons.",
                ))


__all__ = [
    "generate_credibility_test_questions",
    "generate_gap_filler_questions",
]
