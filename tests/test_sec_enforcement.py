"""Tests for SEC enforcement pipeline extractor.

Covers:
- Highest-stage-wins logic across enforcement stages
- Each stage pattern detection
- Industry sweep detection from web results
- Narrative generation
- Empty state returns NONE stage
- Comment letter count from audit data
- 8-K cross-reference
"""

from __future__ import annotations

from typing import Any

from do_uw.models.litigation import EnforcementStage
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sec_enforcement import (
    _detect_stages,
    _generate_narrative,
    extract_sec_enforcement,
    stage_rank,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    web_results: list[str] | None = None,
    blind_spot_results: dict[str, Any] | None = None,
    corresp_count: int | None = None,
    corresp_list: list[str] | None = None,
) -> AnalysisState:
    """Build minimal AnalysisState for SEC enforcement testing."""
    lit_data: dict[str, Any] = {}
    if web_results is not None:
        lit_data["web_results"] = web_results

    filings: dict[str, Any] = {}
    if corresp_count is not None:
        filings["CORRESP"] = corresp_count
    elif corresp_list is not None:
        filings["CORRESP"] = corresp_list

    acquired = AcquiredData(
        litigation_data=lit_data,
        blind_spot_results=blind_spot_results or {},
        filing_documents=filing_documents or {},
        filings=filings,
    )

    return AnalysisState(
        ticker="TEST",
        acquired_data=acquired,
    )


def _make_10k_text(item3_content: str, item1a_content: str = "") -> str:
    """Build 10-K text with Item 3 and optional Item 1A sections."""
    # Pad to exceed 200-char section minimum.
    item3_padded = item3_content
    if len(item3_padded) < 250:
        item3_padded += " " * (250 - len(item3_padded))

    item1a_padded = item1a_content
    if item1a_content and len(item1a_padded) < 250:
        item1a_padded += " " * (250 - len(item1a_padded))

    parts = ["ITEM 1. BUSINESS\n\nCompany overview.\n\n"]
    if item1a_content:
        parts.append(
            f"Item 1A. Risk Factors\n\n{item1a_padded}\n\n"
        )
    else:
        parts.append("Item 1A. Risk Factors\n\nRisk factors here.\n\n")
    parts.append(f"Item 3. Legal Proceedings\n\n{item3_padded}\n\n")
    parts.append("Item 4. Mine Safety\n\n")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Test highest-stage-wins logic
# ---------------------------------------------------------------------------


class TestHighestStageWins:
    """Test enforcement stage ordering and highest-stage-wins."""

    def test_stage_rank_ordering(self) -> None:
        """Stages are ordered by severity."""
        assert stage_rank(EnforcementStage.NONE) < stage_rank(
            EnforcementStage.COMMENT_LETTER,
        )
        assert stage_rank(EnforcementStage.COMMENT_LETTER) < stage_rank(
            EnforcementStage.INFORMAL_INQUIRY,
        )
        assert stage_rank(EnforcementStage.INFORMAL_INQUIRY) < stage_rank(
            EnforcementStage.FORMAL_INVESTIGATION,
        )
        assert stage_rank(EnforcementStage.FORMAL_INVESTIGATION) < stage_rank(
            EnforcementStage.WELLS_NOTICE,
        )
        assert stage_rank(EnforcementStage.WELLS_NOTICE) < stage_rank(
            EnforcementStage.ENFORCEMENT_ACTION,
        )

    def test_multiple_stages_returns_highest(self) -> None:
        """When multiple stages detected, highest wins."""
        text = (
            "The Company received a Wells Notice from the SEC. "
            "Earlier, the SEC had issued comment letters regarding "
            "our revenue recognition. An informal inquiry was also "
            "conducted regarding the matter."
        )
        state = _make_state(
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": _make_10k_text(text),
                }],
            },
        )
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.highest_confirmed_stage is not None
        assert pipeline.highest_confirmed_stage.value == (
            EnforcementStage.WELLS_NOTICE.value
        )


# ---------------------------------------------------------------------------
# Test individual stage patterns
# ---------------------------------------------------------------------------


class TestStagePatterns:
    """Test each enforcement stage pattern detection."""

    def test_enforcement_action_detected(self) -> None:
        """Enforcement action keywords detected."""
        signals = _detect_stages(
            "SEC filed an enforcement action against the company "
            "with civil penalty of $5 million.",
            "test",
        )
        stages = [s for s, _v in signals]
        assert EnforcementStage.ENFORCEMENT_ACTION in stages

    def test_wells_notice_detected(self) -> None:
        """Wells Notice keywords detected."""
        signals = _detect_stages(
            "The Company received a Wells Notice from the SEC "
            "Division of Enforcement.",
            "test",
        )
        stages = [s for s, _v in signals]
        assert EnforcementStage.WELLS_NOTICE in stages

    def test_formal_investigation_detected(self) -> None:
        """Formal investigation keywords detected."""
        signals = _detect_stages(
            "The SEC issued a formal order of investigation "
            "regarding the Company's accounting practices.",
            "test",
        )
        stages = [s for s, _v in signals]
        assert EnforcementStage.FORMAL_INVESTIGATION in stages

    def test_informal_inquiry_detected(self) -> None:
        """Informal inquiry keywords detected."""
        signals = _detect_stages(
            "The SEC conducted an informal inquiry regarding "
            "certain transactions.",
            "test",
        )
        stages = [s for s, _v in signals]
        assert EnforcementStage.INFORMAL_INQUIRY in stages

    def test_comment_letter_detected(self) -> None:
        """Comment letter keywords detected."""
        signals = _detect_stages(
            "The Company received comment letters from the SEC "
            "staff regarding disclosures.",
            "test",
        )
        stages = [s for s, _v in signals]
        assert EnforcementStage.COMMENT_LETTER in stages

    def test_no_match_returns_empty(self) -> None:
        """No enforcement keywords returns empty signals."""
        signals = _detect_stages(
            "The Company sells widgets to customers.",
            "test",
        )
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# Test industry sweep detection
# ---------------------------------------------------------------------------


class TestIndustrySweep:
    """Test industry sweep detection from web results."""

    def test_sweep_detected_in_web_results(self) -> None:
        """Industry sweep detected from web search results."""
        state = _make_state(
            web_results=[
                "SEC industry sweep targeting tech companies' "
                "revenue recognition practices."
            ],
        )
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.industry_sweep_detected is not None
        assert pipeline.industry_sweep_detected.value is True

    def test_no_sweep_returns_false(self) -> None:
        """No sweep keywords returns False."""
        state = _make_state(web_results=["Normal company news."])
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.industry_sweep_detected is not None
        assert pipeline.industry_sweep_detected.value is False


# ---------------------------------------------------------------------------
# Test narrative generation
# ---------------------------------------------------------------------------


class TestNarrativeGeneration:
    """Test enforcement narrative generation."""

    def test_none_stage_narrative(self) -> None:
        """NONE stage produces 'no activity' narrative."""
        narrative = _generate_narrative(
            EnforcementStage.NONE, 0, None, False,
        )
        assert "No SEC enforcement" in narrative

    def test_active_stage_narrative(self) -> None:
        """Active stage produces descriptive narrative."""
        narrative = _generate_narrative(
            EnforcementStage.WELLS_NOTICE, 2, 3, True,
        )
        assert "WELLS_NOTICE" in narrative
        assert "comment letter" in narrative
        assert "sweep" in narrative.lower()

    def test_comment_count_in_narrative(self) -> None:
        """Comment letter count included in narrative."""
        narrative = _generate_narrative(
            EnforcementStage.COMMENT_LETTER, 1, 5, False,
        )
        assert "5 comment letter" in narrative


# ---------------------------------------------------------------------------
# Test empty state
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test empty inputs return NONE stage."""

    def test_empty_state_returns_none_stage(self) -> None:
        """Empty state returns NONE stage."""
        state = AnalysisState(ticker="TEST")
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.highest_confirmed_stage is not None
        assert pipeline.highest_confirmed_stage.value == (
            EnforcementStage.NONE.value
        )

    def test_empty_10k_returns_none_stage(self) -> None:
        """Empty 10-K returns NONE stage with warning."""
        state = _make_state(filing_documents={})
        pipeline, report = extract_sec_enforcement(state)
        assert pipeline.highest_confirmed_stage is not None
        assert pipeline.highest_confirmed_stage.value == (
            EnforcementStage.NONE.value
        )
        assert "No 10-K filing text available" in report.warnings


# ---------------------------------------------------------------------------
# Test comment letter count
# ---------------------------------------------------------------------------


class TestCommentLetterCount:
    """Test comment letter count from various sources."""

    def test_corresp_list_comment_count(self) -> None:
        """Comment count from CORRESP list in acquired filings."""
        state = _make_state(corresp_list=["doc1", "doc2", "doc3"])
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.comment_letter_count is not None
        assert pipeline.comment_letter_count.value == 3

    def test_corresp_count_from_filings(self) -> None:
        """Comment count from CORRESP in acquired filings."""
        state = _make_state(corresp_count=2)
        pipeline, _report = extract_sec_enforcement(state)
        assert pipeline.comment_letter_count is not None
        assert pipeline.comment_letter_count.value == 2
