"""Tests for sentiment analysis and narrative coherence extractors.

15 tests covering:
- L-M analysis (5): negative text, positive text, empty text,
  trajectory deteriorating, trajectory improving
- Broader signals (3): glassdoor extraction, negative news, no web results
- Coherence (5): insider-vs-confidence misaligned, aligned,
  strategy-vs-results misaligned, all coherent, missing data
- Integration (2): extraction report coverage, pysentiment2 import
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import SentimentProfile
from do_uw.models.market import InsiderTradingProfile, MarketSignals
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.analyze.narrative_coherence import (
    _is_net_income_label,  # pyright: ignore[reportPrivateUsage]
    _is_revenue_label,  # pyright: ignore[reportPrivateUsage]
    assess_narrative_coherence,
)
from do_uw.stages.analyze.sentiment_analysis import (
    analyze_lm_sentiment,
    extract_sentiment,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _sv_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.LOW, as_of=_now()
    )


def _sv_float(val: float) -> SourcedValue[float]:
    return SourcedValue[float](
        value=val, source="test", confidence=Confidence.LOW, as_of=_now()
    )


def _make_state(
    *,
    mda_text: str = "",
    prior_mda: str = "",
    web_results: dict[str, Any] | None = None,
    insider_direction: str | None = None,
    revenue_yoy: float | None = None,
    net_income_yoy: float | None = None,
    glassdoor_rating: float | None = None,
    has_growth_claims: bool = False,
) -> AnalysisState:
    """Build a test AnalysisState with configurable fields."""
    filing_texts: dict[str, Any] = {}
    if mda_text:
        filing_texts["10-K_item7"] = mda_text
    if prior_mda:
        filing_texts["10-K_item7_prior"] = prior_mda

    filings: dict[str, Any] = {"filing_texts": filing_texts}

    acquired = AcquiredData(
        filings=filings,
        web_search_results=web_results or {},
    )

    # Build extracted data if needed.
    extracted: ExtractedData | None = None
    line_items: list[FinancialLineItem] = []

    if revenue_yoy is not None:
        line_items.append(
            FinancialLineItem(
                label="Total Revenue",
                yoy_change=revenue_yoy,
            )
        )

    if net_income_yoy is not None:
        line_items.append(
            FinancialLineItem(
                label="Net Income",
                yoy_change=net_income_yoy,
            )
        )

    has_financials = revenue_yoy is not None or net_income_yoy is not None

    market = MarketSignals()
    if insider_direction is not None:
        market.insider_trading = InsiderTradingProfile(
            net_buying_selling=_sv_str(insider_direction),
        )

    governance = GovernanceData()
    if glassdoor_rating is not None:
        governance.sentiment = SentimentProfile(
            glassdoor_rating=_sv_float(glassdoor_rating),
        )

    if has_financials or insider_direction or glassdoor_rating:
        financials = None
        if has_financials:
            income = FinancialStatement(
                statement_type="income",
                line_items=line_items,
            )
            financials = ExtractedFinancials(
                statements=FinancialStatements(income_statement=income),
            )
        extracted = ExtractedData(
            financials=financials,
            market=market,
            governance=governance,
        )

    return AnalysisState(
        ticker="TEST",
        acquired_data=acquired,
        extracted=extracted,
    )


# ---------------------------------------------------------------------------
# L-M Analysis Tests (5)
# ---------------------------------------------------------------------------


class TestLMAnalysis:
    """Tests for Loughran-McDonald dictionary analysis."""

    def test_negative_text(self) -> None:
        """L-M analysis of negative financial text returns negative polarity."""
        text = (
            "The company faces significant risk of loss, litigation, "
            "decline, weakness, and negative operating conditions. "
            "Losses continue to mount with deteriorating performance."
        )
        mock_lm_obj = MagicMock()
        mock_lm_obj.tokenize.return_value = text.split()
        mock_lm_obj.get_score.return_value = {
            "Positive": 0.01,
            "Negative": 0.15,
            "Polarity": -0.87,
            "Subjectivity": 0.16,
        }
        mock_ps = MagicMock()
        mock_ps.LM.return_value = mock_lm_obj

        with patch.dict(
            "sys.modules", {"pysentiment2": mock_ps},
        ):
            # Re-call with the mocked module.
            result = analyze_lm_sentiment(text)

        assert result["polarity"] < 0
        assert result["negative"] > result["positive"]

    def test_positive_text(self) -> None:
        """L-M analysis of positive financial text returns positive polarity."""
        text = (
            "Strong growth in revenue, improvement in margins, "
            "favorable market conditions, and excellent performance."
        )
        mock_lm_obj = MagicMock()
        mock_lm_obj.tokenize.return_value = text.split()
        mock_lm_obj.get_score.return_value = {
            "Positive": 0.20,
            "Negative": 0.02,
            "Polarity": 0.82,
            "Subjectivity": 0.22,
        }
        mock_ps = MagicMock()
        mock_ps.LM.return_value = mock_lm_obj

        with patch.dict(
            "sys.modules", {"pysentiment2": mock_ps},
        ):
            result = analyze_lm_sentiment(text)

        assert result["polarity"] > 0
        assert result["positive"] > result["negative"]

    def test_empty_text(self) -> None:
        """L-M analysis of empty text returns zeros."""
        result = analyze_lm_sentiment("")
        assert result["polarity"] == 0.0
        assert result["positive"] == 0.0
        assert result["negative"] == 0.0
        assert result["subjectivity"] == 0.0

    def test_trajectory_deteriorating(self) -> None:
        """Sentiment trajectory is DETERIORATING when negativity increases."""
        state = _make_state(
            mda_text="Current year discussion of operations and results.",
            prior_mda="Prior year discussion of operations and results.",
        )

        call_count = 0

        def mock_lm(text: str) -> dict[str, float]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Current: high negativity.
                return {
                    "positive": 0.05, "negative": 0.15,
                    "polarity": -0.5, "subjectivity": 0.2,
                }
            # Prior: low negativity.
            return {
                "positive": 0.08, "negative": 0.05,
                "polarity": 0.2, "subjectivity": 0.13,
            }

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            side_effect=mock_lm,
        ):
            profile, _report = extract_sentiment(state)

        assert profile.management_tone_trajectory is not None
        assert profile.management_tone_trajectory.value == "DETERIORATING"

    def test_trajectory_improving(self) -> None:
        """Sentiment trajectory is IMPROVING when negativity decreases."""
        state = _make_state(
            mda_text="Current year positive performance.",
            prior_mda="Prior year challenging conditions.",
        )

        call_count = 0

        def mock_lm(text: str) -> dict[str, float]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Current: low negativity.
                return {
                    "positive": 0.12, "negative": 0.03,
                    "polarity": 0.6, "subjectivity": 0.15,
                }
            # Prior: high negativity.
            return {
                "positive": 0.04, "negative": 0.14,
                "polarity": -0.5, "subjectivity": 0.18,
            }

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            side_effect=mock_lm,
        ):
            profile, _report = extract_sentiment(state)

        assert profile.management_tone_trajectory is not None
        assert profile.management_tone_trajectory.value == "IMPROVING"


# ---------------------------------------------------------------------------
# Broader Signals Tests (3)
# ---------------------------------------------------------------------------


class TestBroaderSignals:
    """Tests for broader sentiment signal extraction."""

    def test_glassdoor_extraction(self) -> None:
        """Glassdoor rating is extracted from web search results."""
        state = _make_state(
            mda_text="Some MD&A text for analysis.",
            web_results={
                "glassdoor": {
                    "rating": 4.2,
                    "employee_sentiment": "POSITIVE",
                },
            },
        )

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            return_value={
                "positive": 0.1, "negative": 0.05,
                "polarity": 0.3, "subjectivity": 0.15,
            },
        ):
            profile, _report = extract_sentiment(state)

        assert profile.glassdoor_rating is not None
        assert profile.glassdoor_rating.value == pytest.approx(4.2)  # type: ignore[reportUnknownMemberType]
        assert profile.glassdoor_rating.confidence == Confidence.LOW
        assert profile.employee_sentiment is not None
        assert profile.employee_sentiment.value == "POSITIVE"

    def test_negative_news_sentiment(self) -> None:
        """Negative news sentiment is captured from web search."""
        state = _make_state(
            mda_text="Some MD&A text.",
            web_results={
                "news_sentiment": "NEGATIVE",
                "social_media_sentiment": "NEGATIVE",
            },
        )

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            return_value={
                "positive": 0.05, "negative": 0.1,
                "polarity": -0.3, "subjectivity": 0.15,
            },
        ):
            profile, _report = extract_sentiment(state)

        assert profile.news_sentiment is not None
        assert profile.news_sentiment.value == "NEGATIVE"
        assert profile.social_media_sentiment is not None
        assert profile.social_media_sentiment.value == "NEGATIVE"

    def test_no_web_results(self) -> None:
        """Empty web results yield no broader signals."""
        state = _make_state(
            mda_text="Some MD&A text.",
            web_results={},
        )

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            return_value={
                "positive": 0.1, "negative": 0.05,
                "polarity": 0.3, "subjectivity": 0.15,
            },
        ):
            profile, _report = extract_sentiment(state)

        assert profile.glassdoor_rating is None
        assert profile.news_sentiment is None
        assert profile.social_media_sentiment is None
        assert profile.employee_sentiment is None


# ---------------------------------------------------------------------------
# Narrative Coherence Tests (5)
# ---------------------------------------------------------------------------


class TestRevenueLabelMatching:
    """Tests for revenue and net income label matching helpers."""

    def test_exact_revenue_labels(self) -> None:
        assert _is_revenue_label("Total Revenue") is True
        assert _is_revenue_label("Revenue") is True
        assert _is_revenue_label("Net Revenue") is True

    def test_compound_revenue_labels(self) -> None:
        """Labels like Tesla's 'Total revenue / net sales' should match."""
        assert _is_revenue_label("Total revenue / net sales") is True
        assert (
            _is_revenue_label("Total Revenue from Operations") is True
        )
        assert (
            _is_revenue_label("Net revenue from contracts") is True
        )

    def test_non_revenue_labels(self) -> None:
        assert _is_revenue_label("Cost of Revenue") is False
        assert _is_revenue_label("Operating Income") is False
        assert _is_revenue_label("Total Assets") is False

    def test_exact_net_income_labels(self) -> None:
        assert _is_net_income_label("Net Income") is True
        assert _is_net_income_label("Net Income (Loss)") is True

    def test_compound_net_income_labels(self) -> None:
        assert (
            _is_net_income_label("Net income / net loss") is True
        )
        assert (
            _is_net_income_label(
                "Net income attributable to common shareholders"
            )
            is True
        )

    def test_non_net_income_labels(self) -> None:
        assert _is_net_income_label("Gross Income") is False
        assert _is_net_income_label("Operating Income") is False


class TestNarrativeCoherence:
    """Tests for narrative coherence assessment."""

    def test_insider_vs_confidence_misaligned(self) -> None:
        """Positive tone + net insider selling -> MISALIGNED."""
        state = _make_state(
            mda_text="Excellent performance with strong growth.",
            insider_direction="NET_SELLING",
        )

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.15, "negative": 0.02,
                "polarity": 0.75, "subjectivity": 0.17,
            },
        ):
            coherence, _report = assess_narrative_coherence(state)

        assert coherence.insider_vs_confidence is not None
        assert coherence.insider_vs_confidence.value == "MISALIGNED"
        assert coherence.insider_vs_confidence.confidence == Confidence.LOW

    def test_insider_vs_confidence_aligned(self) -> None:
        """Positive tone + net insider buying -> ALIGNED."""
        state = _make_state(
            mda_text="Strong results with positive outlook.",
            insider_direction="NET_BUYING",
        )

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.15, "negative": 0.02,
                "polarity": 0.75, "subjectivity": 0.17,
            },
        ):
            coherence, _report = assess_narrative_coherence(state)

        assert coherence.insider_vs_confidence is not None
        assert coherence.insider_vs_confidence.value == "ALIGNED"

    def test_strategy_vs_results_misaligned(self) -> None:
        """Growth claims + declining revenue -> MISALIGNED."""
        state = _make_state(
            mda_text=(
                "Our revenue growth strategy continues to drive "
                "strong growth across all segments with "
                "expanding market share."
            ),
            revenue_yoy=-15.0,
            has_growth_claims=True,
        )

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.12, "negative": 0.04,
                "polarity": 0.5, "subjectivity": 0.16,
            },
        ):
            coherence, _report = assess_narrative_coherence(state)

        assert coherence.strategy_vs_results is not None
        assert coherence.strategy_vs_results.value == "MISALIGNED"
        assert len(coherence.coherence_flags) >= 1

    def test_strategy_vs_results_compound_label(self) -> None:
        """Compound label like 'Total revenue / net sales' is detected."""
        # Build state manually with compound revenue label.
        filing_texts: dict[str, Any] = {
            "10-K_item7": (
                "Our revenue growth strategy drives strong growth "
                "across all segments with expanding market share."
            ),
        }
        income = FinancialStatement(
            statement_type="income",
            line_items=[
                FinancialLineItem(
                    label="Total revenue / net sales",
                    yoy_change=-20.0,
                ),
            ],
        )
        state = AnalysisState(
            ticker="TEST",
            acquired_data=AcquiredData(
                filings={"filing_texts": filing_texts},
            ),
            extracted=ExtractedData(
                financials=ExtractedFinancials(
                    statements=FinancialStatements(
                        income_statement=income
                    ),
                ),
            ),
        )

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.12, "negative": 0.04,
                "polarity": 0.5, "subjectivity": 0.16,
            },
        ):
            coherence, _report = assess_narrative_coherence(state)

        assert coherence.strategy_vs_results is not None
        assert coherence.strategy_vs_results.value == "MISALIGNED"

    def test_all_coherent(self) -> None:
        """When all signals align, overall is COHERENT."""
        state = _make_state(
            mda_text=(
                "Our revenue growth strategy has delivered results. "
                "We continue to see strong growth in key markets."
            ),
            insider_direction="NET_BUYING",
            revenue_yoy=12.0,
            net_income_yoy=8.0,
            glassdoor_rating=4.5,
            has_growth_claims=True,
        )

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.15, "negative": 0.03,
                "polarity": 0.67, "subjectivity": 0.18,
            },
        ):
            coherence, _report = assess_narrative_coherence(state)

        assert coherence.overall_assessment is not None
        assert coherence.overall_assessment.value == "COHERENT"
        assert len(coherence.coherence_flags) == 0

    def test_missing_data(self) -> None:
        """Missing data -> no checks possible, warning in report."""
        state = AnalysisState(ticker="TEST")

        with patch(
            "do_uw.stages.analyze.narrative_coherence.analyze_lm_sentiment",
            return_value={
                "positive": 0.0, "negative": 0.0,
                "polarity": 0.0, "subjectivity": 0.0,
            },
        ):
            coherence, report = assess_narrative_coherence(state)

        assert coherence.overall_assessment is None
        assert len(report.warnings) > 0
        assert "Insufficient data" in report.warnings[0]


# ---------------------------------------------------------------------------
# Integration Tests (2)
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests for sentiment extraction pipeline."""

    def test_extraction_report_coverage(self) -> None:
        """Extraction report has expected fields and coverage tracking."""
        state = _make_state(
            mda_text="Some text for analysis.",
            web_results={
                "glassdoor": {"rating": 3.5},
                "news_sentiment": "NEUTRAL",
            },
        )

        with patch(
            "do_uw.stages.analyze.sentiment_analysis.analyze_lm_sentiment",
            return_value={
                "positive": 0.08, "negative": 0.06,
                "polarity": 0.14, "subjectivity": 0.14,
            },
        ):
            _profile, report = extract_sentiment(state)

        assert report.extractor_name == "sentiment_analysis"
        assert len(report.expected_fields) == 9
        assert report.coverage_pct >= 0.0
        # Should have at least lm_negative_trend, glassdoor, news.
        assert len(report.found_fields) >= 3

    def test_pysentiment2_import(self) -> None:
        """pysentiment2 can be imported and LM dictionary constructed."""
        import pysentiment2 as ps  # type: ignore[import-untyped]

        lm = ps.LM()
        tokens: list[str] = lm.tokenize(  # type: ignore[reportUnknownMemberType]
            "The company reported strong earnings growth"
        )
        score: dict[str, float] = lm.get_score(tokens)  # type: ignore[reportUnknownMemberType]
        assert "Positive" in score
        assert "Negative" in score
        assert "Polarity" in score
        assert "Subjectivity" in score
