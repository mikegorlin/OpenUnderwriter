"""Tests for defense assessment extractor (SECT6-09).

Tests forum provision detection, PSLRA classification, prior
dismissals, overall strength, and the main extractor function.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import CaseDetail, LitigationLandscape
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.analyze.defense_assessment import (
    check_prior_dismissals,
    classify_pslra_usage,
    compute_defense_strength,
    extract_defense_assessment,
    parse_forum_provisions,
)


def _make_state(
    proxy_text: str = "",
    text_10k: str = "",
) -> AnalysisState:
    """Create an AnalysisState with filing documents pre-loaded."""
    state = AnalysisState(ticker="TEST")
    docs: dict[str, list[dict[str, str]]] = {}
    if proxy_text:
        docs["DEF 14A"] = [
            {
                "accession": "test-proxy",
                "filing_date": "2024-01-01",
                "form_type": "DEF 14A",
                "full_text": proxy_text,
            }
        ]
    if text_10k:
        docs["10-K"] = [
            {
                "accession": "test-10k",
                "filing_date": "2024-01-01",
                "form_type": "10-K",
                "full_text": text_10k,
            }
        ]
    state.acquired_data = AcquiredData(filing_documents=docs)
    return state


# ---------------------------------------------------------------------------
# Forum provision tests
# ---------------------------------------------------------------------------


class TestForumProvisions:
    """Test forum provision detection from DEF 14A text."""

    def test_federal_forum_detected(self) -> None:
        text = (
            "The Securities Act provides that any claim arising under "
            "the Securities Act shall be brought in a United States "
            "federal district court."
        )
        result = parse_forum_provisions(text)
        assert result.has_federal_forum is not None
        assert result.has_federal_forum.value is True
        assert result.federal_forum_details is not None

    def test_exclusive_forum_detected(self) -> None:
        text = (
            "Our bylaws provide an exclusive forum selection "
            "clause requiring claims to be brought in the "
            "Court of Chancery of Delaware."
        )
        result = parse_forum_provisions(text)
        assert result.has_exclusive_forum is not None
        assert result.has_exclusive_forum.value is True
        assert result.exclusive_forum_details is not None

    def test_no_provisions_found(self) -> None:
        text = "This proxy statement contains standard disclosures."
        result = parse_forum_provisions(text)
        assert result.has_federal_forum is not None
        assert result.has_federal_forum.value is False
        assert result.has_exclusive_forum is not None
        assert result.has_exclusive_forum.value is False

    def test_empty_text_returns_defaults(self) -> None:
        result = parse_forum_provisions("")
        assert result.has_federal_forum is not None
        assert result.has_federal_forum.value is False


# ---------------------------------------------------------------------------
# PSLRA classification tests
# ---------------------------------------------------------------------------


class TestPSLRAClassification:
    """Test PSLRA safe harbor usage classification."""

    def test_strong_classification(self) -> None:
        text = (
            "Pursuant to the Private Securities Litigation Reform Act "
            "of 1995, the following statements are forward-looking. "
            "Risks include market conditions, may not achieve targets, "
            "could differ materially, uncertainties include regulatory "
            "changes, subject to risks, and no assurance of success."
        )
        assert classify_pslra_usage(text) == "STRONG"

    def test_moderate_classification(self) -> None:
        text = (
            "As required by the PSLRA, we note that these statements "
            "are forward-looking and may differ from actual results."
        )
        assert classify_pslra_usage(text) == "MODERATE"

    def test_weak_classification(self) -> None:
        text = (
            "This document contains forward-looking statements."
        )
        assert classify_pslra_usage(text) == "WEAK"

    def test_none_classification(self) -> None:
        text = "This is a standard annual report with financial data."
        assert classify_pslra_usage(text) == "NONE"


# ---------------------------------------------------------------------------
# Prior dismissals tests
# ---------------------------------------------------------------------------


class TestPriorDismissals:
    """Test prior dismissal detection in Item 3 text."""

    def test_dismissal_found(self) -> None:
        text = "The case was dismissed by the court on March 15, 2024."
        has, count = check_prior_dismissals(text)
        assert has is True
        assert count == 1

    def test_motion_to_dismiss_granted(self) -> None:
        text = "The court motion to dismiss granted the defendants' request."
        has, count = check_prior_dismissals(text)
        assert has is True
        assert count >= 1

    def test_judgment_in_favor(self) -> None:
        text = "Judgment in favor of the Company was entered."
        has, _count = check_prior_dismissals(text)
        assert has is True

    def test_no_dismissals(self) -> None:
        text = "The case remains pending before the court."
        has, count = check_prior_dismissals(text)
        assert has is False
        assert count == 0


# ---------------------------------------------------------------------------
# Defense strength tests
# ---------------------------------------------------------------------------


class TestDefenseStrength:
    """Test overall defense strength computation."""

    def test_strong_defense(self) -> None:
        result = compute_defense_strength(
            has_federal_forum=True,
            has_exclusive_forum=True,
            pslra_usage="STRONG",
            has_prior_dismissals=True,
        )
        assert result == "STRONG"

    def test_weak_defense(self) -> None:
        result = compute_defense_strength(
            has_federal_forum=False,
            has_exclusive_forum=False,
            pslra_usage="NONE",
            has_prior_dismissals=False,
        )
        assert result == "WEAK"

    def test_moderate_defense(self) -> None:
        result = compute_defense_strength(
            has_federal_forum=True,
            has_exclusive_forum=False,
            pslra_usage="MODERATE",
            has_prior_dismissals=False,
        )
        assert result == "MODERATE"


# ---------------------------------------------------------------------------
# Main extractor tests
# ---------------------------------------------------------------------------


class TestExtractDefenseAssessment:
    """Test the main extract_defense_assessment function."""

    def test_full_extraction_with_filings(self) -> None:
        proxy = (
            "The charter provides a federal forum "
            "for Securities Act claims in United States "
            "federal district court."
        )
        ten_k = (
            "The Private Securities Litigation Reform Act of 1995 "
            "provides a safe harbor for forward-looking statements. "
            "Risks include that results may not meet expectations. "
            "We cannot guarantee results could differ materially. "
            "Uncertainties include market, no assurance of continued growth. "
            "Item 3. Legal Proceedings\n"
            "The case was dismissed by the court.\n"
            "Item 4. Mine Safety\n"
        )
        state = _make_state(proxy_text=proxy, text_10k=ten_k)
        assessment, report = extract_defense_assessment(state)

        assert assessment.forum_provisions.has_federal_forum is not None
        assert assessment.forum_provisions.has_federal_forum.value is True
        assert assessment.pslra_safe_harbor_usage is not None
        assert assessment.pslra_safe_harbor_usage.value in (
            "STRONG",
            "MODERATE",
        )
        assert assessment.overall_defense_strength is not None
        assert assessment.defense_narrative is not None
        assert report.coverage_pct >= 70.0

    def test_empty_filings_returns_defaults(self) -> None:
        state = _make_state()
        assessment, report = extract_defense_assessment(state)

        assert assessment.overall_defense_strength is not None
        assert assessment.overall_defense_strength.value == "WEAK"
        assert len(report.warnings) >= 1

    def test_judge_track_record_from_cases(self) -> None:
        state = _make_state(text_10k="Some generic 10-K text. " * 100)
        state.extracted = ExtractedData()
        state.extracted.litigation = LitigationLandscape()
        state.extracted.litigation.securities_class_actions = [
            CaseDetail(
                judge=SourcedValue[str](
                    value="Judge Smith",
                    source="court records",
                    confidence=Confidence.MEDIUM,
                    as_of=datetime.now(tz=UTC),
                )
            )
        ]
        assessment, _report = extract_defense_assessment(state)
        assert assessment.judge_track_record is not None
        assert "Smith" in assessment.judge_track_record.value
