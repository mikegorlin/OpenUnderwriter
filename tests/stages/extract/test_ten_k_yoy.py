"""Tests for 10-K year-over-year comparison logic."""

from __future__ import annotations

import pytest

from do_uw.models.state import AnalysisState, AcquiredData
from do_uw.models.ten_k_comparison import TenKYoYComparison
from do_uw.stages.extract.ten_k_yoy import (
    _compare_risk_factors,
    _compare_controls,
    _compare_legal_proceedings,
    _content_words,
    _detect_reorganizations,
    _normalize_title,
    compute_yoy_comparison,
)


# ---------------------------------------------------------------------------
# Risk factor matching tests
# ---------------------------------------------------------------------------


class TestRiskFactorMatching:
    """Test fuzzy title matching and change classification."""

    def test_exact_match_unchanged(self) -> None:
        current = [{"title": "Cybersecurity Risk", "category": "CYBER", "severity": "HIGH"}]
        prior = [{"title": "Cybersecurity Risk", "category": "CYBER", "severity": "HIGH"}]
        changes = _compare_risk_factors(current, prior)
        assert len(changes) == 1
        assert changes[0].change_type == "UNCHANGED"

    def test_fuzzy_match_escalated(self) -> None:
        current = [{"title": "Cybersecurity and Data Privacy Risks", "category": "CYBER", "severity": "HIGH"}]
        prior = [{"title": "Cybersecurity and Data Privacy Risk", "category": "CYBER", "severity": "MEDIUM"}]
        changes = _compare_risk_factors(current, prior)
        assert len(changes) == 1
        assert changes[0].change_type == "ESCALATED"
        assert changes[0].prior_severity == "MEDIUM"
        assert changes[0].current_severity == "HIGH"

    def test_new_risk_factor(self) -> None:
        current = [
            {"title": "AI Regulation Risk", "category": "REGULATORY", "severity": "MEDIUM"},
            {"title": "Cyber Risk", "category": "CYBER", "severity": "HIGH"},
        ]
        prior = [{"title": "Cyber Risk", "category": "CYBER", "severity": "HIGH"}]
        changes = _compare_risk_factors(current, prior)
        new = [c for c in changes if c.change_type == "NEW"]
        assert len(new) == 1
        assert new[0].title == "AI Regulation Risk"

    def test_removed_risk_factor(self) -> None:
        current = [{"title": "Cyber Risk", "category": "CYBER", "severity": "HIGH"}]
        prior = [
            {"title": "Cyber Risk", "category": "CYBER", "severity": "HIGH"},
            {"title": "COVID-19 Impact", "category": "OPERATIONAL", "severity": "MEDIUM"},
        ]
        changes = _compare_risk_factors(current, prior)
        removed = [c for c in changes if c.change_type == "REMOVED"]
        assert len(removed) == 1
        assert removed[0].title == "COVID-19 Impact"

    def test_de_escalated(self) -> None:
        current = [{"title": "Litigation Risk", "category": "LITIGATION", "severity": "LOW"}]
        prior = [{"title": "Litigation Risk", "category": "LITIGATION", "severity": "HIGH"}]
        changes = _compare_risk_factors(current, prior)
        assert len(changes) == 1
        assert changes[0].change_type == "DE_ESCALATED"

    def test_no_match_different_titles(self) -> None:
        current = [{"title": "Brand New Risk Alpha", "category": "OTHER", "severity": "MEDIUM"}]
        prior = [{"title": "Completely Different Risk Beta", "category": "OTHER", "severity": "MEDIUM"}]
        changes = _compare_risk_factors(current, prior)
        new = [c for c in changes if c.change_type == "NEW"]
        removed = [c for c in changes if c.change_type == "REMOVED"]
        assert len(new) == 1
        assert len(removed) == 1

    def test_empty_lists(self) -> None:
        assert _compare_risk_factors([], []) == []
        changes = _compare_risk_factors(
            [{"title": "X", "category": "OTHER", "severity": "LOW"}], [],
        )
        assert len(changes) == 1
        assert changes[0].change_type == "NEW"


# ---------------------------------------------------------------------------
# Reorganization detection tests
# ---------------------------------------------------------------------------


class TestReorganizationDetection:
    """Test detection of reorganized/consolidated risk factors."""

    def test_consolidation_detected(self) -> None:
        """Two removed items consolidated into one new item — Apple-style scenario."""
        current = [
            {"title": "Antitrust investigations and Digital Markets Act compliance", "category": "REGULATORY", "severity": "HIGH"},
        ]
        prior = [
            {"title": "Digital Markets Act compliance and EU regulatory fines", "category": "REGULATORY", "severity": "HIGH"},
            {"title": "Antitrust and regulatory litigation", "category": "REGULATORY", "severity": "HIGH"},
        ]
        changes = _compare_risk_factors(current, prior)
        changes = _detect_reorganizations(changes)

        reorg = [c for c in changes if c.change_type == "REORGANIZED"]
        consolidated = [c for c in changes if c.change_type == "CONSOLIDATED_INTO"]
        new = [c for c in changes if c.change_type == "NEW"]

        # The new item should match one of the removed items as REORGANIZED
        assert len(reorg) == 1
        assert reorg[0].prior_title is not None
        # At most one CONSOLIDATED_INTO (the best match)
        assert len(consolidated) == 1
        # The remaining unmatched removed item stays REMOVED
        assert len(new) == 0

    def test_no_reorganization_for_truly_different(self) -> None:
        """Truly different titles should remain NEW/REMOVED."""
        changes = _compare_risk_factors(
            [{"title": "Artificial Intelligence Governance Risk", "category": "AI", "severity": "MEDIUM"}],
            [{"title": "COVID-19 Pandemic Impact", "category": "OPERATIONAL", "severity": "MEDIUM"}],
        )
        changes = _detect_reorganizations(changes)

        new = [c for c in changes if c.change_type == "NEW"]
        removed = [c for c in changes if c.change_type == "REMOVED"]
        reorg = [c for c in changes if c.change_type == "REORGANIZED"]

        assert len(new) == 1
        assert len(removed) == 1
        assert len(reorg) == 0

    def test_word_overlap_threshold(self) -> None:
        """Items sharing 3+ content words should be detected as reorganized."""
        changes = _compare_risk_factors(
            [{"title": "Supply chain disruption and logistics risks", "category": "OPERATIONAL", "severity": "HIGH"}],
            [{"title": "Risks from supply chain disruption", "category": "OPERATIONAL", "severity": "MEDIUM"}],
        )
        changes = _detect_reorganizations(changes)

        # These share "supply", "chain", "disruption" (3+ words) — should match
        reorg = [c for c in changes if c.change_type == "REORGANIZED"]
        assert len(reorg) == 1

    def test_content_words_strips_stop_words(self) -> None:
        """Content words function should exclude common stop words."""
        words = _content_words("The risks of and to our operations in the market")
        assert "the" not in words
        assert "of" not in words
        assert "and" not in words
        assert "to" not in words
        assert "our" not in words
        assert "in" not in words
        assert "risks" in words
        assert "operations" in words
        assert "market" in words

    def test_empty_changes_no_crash(self) -> None:
        """Empty list should pass through without error."""
        assert _detect_reorganizations([]) == []

    def test_no_new_or_removed(self) -> None:
        """Changes with only UNCHANGED/ESCALATED should pass through."""
        from do_uw.models.ten_k_comparison import RiskFactorChange
        changes = [
            RiskFactorChange(
                title="Cyber Risk", category="CYBER",
                change_type="ESCALATED", current_severity="HIGH",
                prior_severity="MEDIUM", summary="Severity increased",
            ),
        ]
        result = _detect_reorganizations(changes)
        assert len(result) == 1
        assert result[0].change_type == "ESCALATED"

    def test_multiple_reorganizations(self) -> None:
        """Multiple NEW/REMOVED pairs should each be detected independently.

        Titles must be different enough to fail SequenceMatcher fuzzy match
        (<0.6 ratio) but share enough content words for reorganization detection.
        """
        current = [
            {"title": "Regulatory compliance with data privacy laws globally", "category": "REGULATORY", "severity": "HIGH"},
            {"title": "Workforce talent acquisition and employee retention challenges", "category": "OPERATIONAL", "severity": "MEDIUM"},
        ]
        prior = [
            {"title": "Global data protection and privacy regulatory frameworks", "category": "REGULATORY", "severity": "HIGH"},
            {"title": "Employee turnover retention and talent management risks", "category": "OPERATIONAL", "severity": "MEDIUM"},
        ]
        changes = _compare_risk_factors(current, prior)
        changes = _detect_reorganizations(changes)

        reorg = [c for c in changes if c.change_type == "REORGANIZED"]
        new = [c for c in changes if c.change_type == "NEW"]
        removed = [c for c in changes if c.change_type == "REMOVED"]

        # Both pairs should be detected as reorganized
        assert len(reorg) == 2
        assert len(new) == 0
        assert len(removed) == 0

    def test_reorganized_count_in_full_comparison(self) -> None:
        """Integration: reorganized_risk_count populated in full comparison."""
        state = AnalysisState(ticker="TEST")
        state.acquired_data = AcquiredData(
            filing_documents={"10-K": [
                {"accession": "acc1", "filing_date": "2025-03-01", "form_type": "10-K", "full_text": ""},
                {"accession": "acc2", "filing_date": "2024-03-01", "form_type": "10-K", "full_text": ""},
            ]},
            llm_extractions={
                "10-K:acc1": {
                    "period_of_report": "2024-12-31",
                    "risk_factors": [
                        {"title": "Privacy and data protection compliance", "category": "REGULATORY", "severity": "HIGH"},
                        {"title": "Truly new AI risk factor", "category": "AI", "severity": "MEDIUM"},
                    ],
                },
                "10-K:acc2": {
                    "period_of_report": "2023-12-31",
                    "risk_factors": [
                        {"title": "Data protection and privacy regulations", "category": "REGULATORY", "severity": "HIGH"},
                        {"title": "Old pandemic risk no longer relevant", "category": "OPERATIONAL", "severity": "LOW"},
                    ],
                },
            },
        )
        result = compute_yoy_comparison(state)
        assert result is not None
        assert result.reorganized_risk_count == 1
        assert result.new_risk_count == 1  # "Truly new AI risk factor"
        assert result.removed_risk_count == 1  # "Old pandemic risk"


# ---------------------------------------------------------------------------
# Controls comparison tests
# ---------------------------------------------------------------------------


class TestControlsComparison:
    def test_material_weakness_appeared(self) -> None:
        changed, mw = _compare_controls(
            {"has_material_weakness": True},
            {"has_material_weakness": False},
        )
        assert changed is True
        assert mw == "APPEARED"

    def test_material_weakness_remediated(self) -> None:
        changed, mw = _compare_controls(
            {"has_material_weakness": False},
            {"has_material_weakness": True},
        )
        assert changed is True
        assert mw == "REMEDIATED"

    def test_no_change(self) -> None:
        changed, mw = _compare_controls(
            {"has_material_weakness": False},
            {"has_material_weakness": False},
        )
        assert changed is False
        assert mw is None


# ---------------------------------------------------------------------------
# Legal proceedings tests
# ---------------------------------------------------------------------------


class TestLegalProceedings:
    def test_net_new(self) -> None:
        delta = _compare_legal_proceedings(
            {"legal_proceedings": [{"case_name": "A"}, {"case_name": "B"}]},
            {"legal_proceedings": [{"case_name": "A"}]},
        )
        assert delta == 1

    def test_net_resolved(self) -> None:
        delta = _compare_legal_proceedings(
            {"legal_proceedings": []},
            {"legal_proceedings": [{"case_name": "A"}]},
        )
        assert delta == -1


# ---------------------------------------------------------------------------
# Integration: compute_yoy_comparison
# ---------------------------------------------------------------------------


class TestComputeYoY:
    def test_returns_none_with_no_data(self) -> None:
        state = AnalysisState(ticker="TEST")
        assert compute_yoy_comparison(state) is None

    def test_returns_none_with_one_extraction(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.acquired_data = AcquiredData(
            filing_documents={"10-K": [
                {"accession": "acc1", "filing_date": "2025-03-01", "form_type": "10-K", "full_text": ""},
            ]},
            llm_extractions={
                "10-K:acc1": {"period_of_report": "2024-12-31", "risk_factors": []},
            },
        )
        assert compute_yoy_comparison(state) is None

    def test_full_comparison(self) -> None:
        state = AnalysisState(ticker="TEST")
        state.acquired_data = AcquiredData(
            filing_documents={"10-K": [
                {"accession": "acc1", "filing_date": "2025-03-01", "form_type": "10-K", "full_text": ""},
                {"accession": "acc2", "filing_date": "2024-03-01", "form_type": "10-K", "full_text": ""},
            ]},
            llm_extractions={
                "10-K:acc1": {
                    "period_of_report": "2024-12-31",
                    "risk_factors": [
                        {"title": "Cyber Risk", "category": "CYBER", "severity": "HIGH"},
                        {"title": "New AI Risk", "category": "AI", "severity": "MEDIUM"},
                    ],
                    "has_material_weakness": True,
                    "legal_proceedings": [{"case_name": "A"}, {"case_name": "B"}],
                    "key_financial_concerns": ["Rising costs"],
                },
                "10-K:acc2": {
                    "period_of_report": "2023-12-31",
                    "risk_factors": [
                        {"title": "Cyber Risk", "category": "CYBER", "severity": "MEDIUM"},
                    ],
                    "has_material_weakness": False,
                    "legal_proceedings": [{"case_name": "A"}],
                    "key_financial_concerns": [],
                },
            },
        )
        result = compute_yoy_comparison(state)
        assert result is not None
        assert result.current_year == "FY2024"
        assert result.prior_year == "FY2023"
        assert result.new_risk_count == 1  # New AI Risk
        assert result.escalated_risk_count == 1  # Cyber: MEDIUM -> HIGH
        assert result.material_weakness_change == "APPEARED"
        assert result.legal_proceedings_delta == 1
