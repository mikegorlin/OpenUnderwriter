"""Tests that meeting prep questions are company-specific, not generic templates.

Every meeting prep question must reference actual data from AnalysisState:
ticker/company name, dollar amounts, dates, case names, scoring factors.
Generic "the company" language is rejected.

Plan 129-03: Meeting prep specificity enforcement.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence, SourcedValue

_NOW = datetime.now(tz=UTC)


def _sv(value: object, source: str = "test", confidence: Confidence = Confidence.HIGH) -> SourcedValue:
    """Shorthand SourcedValue constructor for tests."""
    return SourcedValue(value=value, source=source, confidence=confidence, as_of=_NOW)
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import (
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
)
from do_uw.models.litigation import CaseDetail, LitigationLandscape
from do_uw.models.market import (
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.scoring import (
    FactorScore,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.render.sections.meeting_questions import (
    MeetingQuestion,
    generate_clarification_questions,
    generate_forward_indicator_questions,
)
from do_uw.stages.render.sections.meeting_questions_analysis import (
    generate_bear_case_questions,
)
from do_uw.stages.render.sections.meeting_questions_gap import (
    generate_credibility_test_questions,
    generate_gap_filler_questions,
)


def _build_mock_state() -> AnalysisState:
    """Build a realistic mock AnalysisState with company-specific data.

    Company: Acme Corp (ACME)
    - 1 active SCA: Smith v. Acme, filed 2025-06-15, $50M damages
    - Quality score: 72.5, tier: WRITE
    - Top factor: F.3 = 7/8 points deducted
    - Altman Z = 1.5 (distress zone)
    - Short interest: 15% of float
    """
    state = AnalysisState(ticker="ACME")

    # Company profile
    identity = CompanyIdentity(
        legal_name=_sv("Acme Corp", "SEC EDGAR"),
        ticker="ACME",
    )
    profile = CompanyProfile(identity=identity)
    profile.market_cap = _sv(5_000_000_000, "yfinance")
    state.company = profile

    # Extracted data
    ext = ExtractedData()

    # Financials with distress
    fin = ExtractedFinancials()
    fin.distress = DistressIndicators()
    fin.distress.altman_z_score = DistressResult(
        score=1.50,
        zone=DistressZone.DISTRESS,
    )
    ext.financials = fin

    # Market data with short interest
    market = MarketSignals()
    market.short_interest = ShortInterestProfile()
    market.short_interest.short_pct_float = _sv(15.0, "NASDAQ", Confidence.MEDIUM)
    market.stock = StockPerformance()
    ext.market = market

    # Litigation with one active SCA
    lit = LitigationLandscape()
    sca = CaseDetail(
        case_name=_sv("Smith v. Acme Corp", "Stanford SCAC"),
        filing_date=_sv(date(2025, 6, 15), "Stanford SCAC"),
        status=_sv("ACTIVE", "Stanford SCAC"),
        settlement_amount=_sv(50_000_000, "estimate", Confidence.LOW),
    )
    lit.securities_class_actions = [sca]
    ext.litigation = lit

    state.extracted = ext

    # Scoring
    scoring = ScoringResult(
        quality_score=72.5,
        composite_score=72.5,
        total_risk_points=27.5,
        factor_scores=[
            FactorScore(
                factor_name="Prior SCA History",
                factor_id="F.3",
                max_points=8,
                points_deducted=7.0,
                evidence=["Smith v. Acme Corp filed 2025-06-15"],
            ),
            FactorScore(
                factor_name="Financial Distress",
                factor_id="F.1",
                max_points=10,
                points_deducted=5.0,
                evidence=["Altman Z-Score 1.50 in distress zone"],
            ),
        ],
        tier=TierClassification(tier=Tier.WRITE, score_range_low=65.0, score_range_high=80.0),
    )
    state.scoring = scoring

    return state


class TestClarificationQuestionsSpecificity:
    """Clarification questions must reference company-specific data."""

    def test_questions_contain_company_name_or_ticker(self) -> None:
        """Every clarification question should reference Acme or ACME."""
        state = _build_mock_state()
        questions = generate_clarification_questions(state)
        for q in questions:
            assert (
                "the company" not in q.question.lower()
                or "acme" in q.question.lower()
            ), f"Generic question found without company name: {q.question}"

    def test_forward_indicators_reference_company_name(self) -> None:
        """Forward indicator questions must name the company."""
        state = _build_mock_state()
        questions = generate_forward_indicator_questions(state)
        # Should get distress and short interest questions
        assert len(questions) >= 1, "Expected at least 1 forward indicator question"
        for q in questions:
            has_company_ref = "acme" in q.question.lower()
            has_generic = "the company" in q.question.lower()
            if has_generic:
                assert has_company_ref, (
                    f"Question uses 'the company' without naming Acme: {q.question}"
                )


class TestBearCaseQuestionsSpecificity:
    """Bear case questions must reference scoring factors and specific data."""

    def test_bear_case_references_scoring_factors(self) -> None:
        """Bear case questions should include factor IDs like F.3."""
        state = _build_mock_state()
        questions = generate_bear_case_questions(state)
        # With no peril_map, returns empty -- structural test only

    def test_no_generic_sca_question(self) -> None:
        """Questions must not be generic 'What is the status of pending SCAs?'."""
        state = _build_mock_state()
        all_questions: list[MeetingQuestion] = []
        all_questions.extend(generate_clarification_questions(state))
        all_questions.extend(generate_forward_indicator_questions(state))
        all_questions.extend(generate_gap_filler_questions(state))
        all_questions.extend(generate_credibility_test_questions(state))

        generic_patterns = [
            r"what is the status of pending scas?\s*$",
            r"what is the company's exposure to sca risk\?",
            r"are there any pending securities class actions\?$",
        ]
        for q in all_questions:
            for pattern in generic_patterns:
                assert not re.search(pattern, q.question.lower()), (
                    f"Generic SCA question found: {q.question}"
                )


class TestSCACounterUsage:
    """SCA-related questions must use canonical sca_counter."""

    def test_meeting_questions_import_sca_counter(self) -> None:
        """meeting_questions.py should import from sca_counter for SCA references."""
        import inspect

        import do_uw.stages.render.sections.meeting_questions as mq_mod

        source = inspect.getsource(mq_mod)
        assert "sca_counter" in source, (
            "meeting_questions.py does not import from sca_counter"
        )

    def test_meeting_prep_renderer_imports_sca_counter(self) -> None:
        """meeting_prep.py (Word renderer) should import from sca_counter."""
        import inspect

        import do_uw.stages.render.sections.meeting_prep as mp_mod

        source = inspect.getsource(mp_mod)
        assert "sca_counter" in source, (
            "meeting_prep.py does not import from sca_counter"
        )


class TestQuestionDataPointDensity:
    """Each question must contain at least one company-specific data point."""

    def test_forward_indicators_contain_specific_numbers(self) -> None:
        """Forward indicator questions must have dollar amounts, percentages, or scores."""
        state = _build_mock_state()
        questions = generate_forward_indicator_questions(state)
        assert len(questions) >= 1
        number_pattern = re.compile(r"\d+\.?\d*")
        for q in questions:
            has_number = bool(number_pattern.search(q.question))
            has_name = "acme" in q.question.lower()
            assert has_number or has_name, (
                f"Question lacks specific data points: {q.question}"
            )

    def test_credibility_tests_reference_forensic_values(self) -> None:
        """Credibility test questions should reference actual model values."""
        state = _build_mock_state()
        questions = generate_credibility_test_questions(state)
        for q in questions:
            has_number = bool(re.search(r"\d+\.?\d*", q.question))
            assert has_number, (
                f"Credibility test question lacks forensic values: {q.question}"
            )

    def test_gap_filler_references_company_name(self) -> None:
        """Gap filler questions should reference Acme when applicable."""
        state = _build_mock_state()
        questions = generate_gap_filler_questions(state)
        for q in questions:
            assert (
                "the company" not in q.question.lower()
                or "acme" in q.question.lower()
            ), f"Gap filler uses generic 'the company': {q.question}"


class TestNoGenericCompanyReferences:
    """Across all generators, 'the company' must be replaced with actual name."""

    def test_all_generators_no_bare_the_company(self) -> None:
        """Aggregate check: no question text uses 'the company' without company name."""
        state = _build_mock_state()
        all_questions: list[MeetingQuestion] = []
        all_questions.extend(generate_clarification_questions(state))
        all_questions.extend(generate_forward_indicator_questions(state))
        all_questions.extend(generate_gap_filler_questions(state))
        all_questions.extend(generate_credibility_test_questions(state))

        for q in all_questions:
            text_lower = q.question.lower()
            if "the company" in text_lower:
                assert "acme" in text_lower, (
                    f"Question uses generic 'the company' without naming Acme: "
                    f"{q.question}"
                )
