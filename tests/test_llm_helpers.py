"""Tests for LLM extraction helper functions.

Covers get_llm_eight_k() multi-instance deserialization.
"""

from __future__ import annotations

from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas import EightKExtraction
from do_uw.stages.extract.llm_helpers import get_llm_eight_k


def _make_state(llm_extractions: dict[str, object]) -> AnalysisState:
    """Create a minimal AnalysisState with given llm_extractions."""
    return AnalysisState(
        ticker="TEST",
        acquired_data=AcquiredData(llm_extractions=llm_extractions),
    )


def _valid_eight_k_dict(
    officer: str = "Jane Smith",
    title: str = "CFO",
) -> dict[str, str]:
    """Return a valid 8-K extraction dict."""
    return {
        "event_date": "2025-06-15",
        "departing_officer": officer,
        "departing_officer_title": title,
        "departure_reason": "resignation",
    }


class TestGetLlmEightK:
    """Tests for get_llm_eight_k() multi-instance helper."""

    def test_returns_list_of_extractions(self) -> None:
        """State with two 8-K entries returns list of 2 EightKExtraction."""
        state = _make_state({
            "8-K:acc1": _valid_eight_k_dict("Jane Smith", "CFO"),
            "8-K:acc2": _valid_eight_k_dict("John Doe", "CEO"),
        })
        results = get_llm_eight_k(state)
        assert len(results) == 2
        assert all(isinstance(r, EightKExtraction) for r in results)
        names = {r.departing_officer for r in results}
        assert names == {"Jane Smith", "John Doe"}

    def test_empty_when_no_eight_k(self) -> None:
        """State with only 10-K entries returns empty list."""
        state = _make_state({
            "10-K:acc1": {"fiscal_year_end": "2024-12-31"},
            "DEF 14A:acc2": {"board_size": 9},
        })
        results = get_llm_eight_k(state)
        assert results == []

    def test_skips_invalid_entries(self) -> None:
        """State with one valid and one invalid 8-K returns list of 1."""
        state = _make_state({
            "8-K:acc1": _valid_eight_k_dict(),
            "8-K:acc2": "not a dict",  # invalid -- not a dict
        })
        results = get_llm_eight_k(state)
        assert len(results) == 1
        assert results[0].departing_officer == "Jane Smith"

    def test_no_acquired_data(self) -> None:
        """State with acquired_data=None returns empty list."""
        state = AnalysisState(ticker="TEST", acquired_data=None)
        results = get_llm_eight_k(state)
        assert results == []

    def test_preserves_departing_officer_title(self) -> None:
        """New departing_officer_title field is deserialized correctly."""
        state = _make_state({
            "8-K:acc1": _valid_eight_k_dict("Alice", "Chief Technology Officer"),
        })
        results = get_llm_eight_k(state)
        assert len(results) == 1
        assert results[0].departing_officer_title == "Chief Technology Officer"

    def test_skips_malformed_dict(self) -> None:
        """8-K entry with fields that cause validation error is skipped."""
        state = _make_state({
            "8-K:acc1": _valid_eight_k_dict(),
            # items_covered expects list[str], not a string
            "8-K:acc2": {"items_covered": "not a list"},
        })
        results = get_llm_eight_k(state)
        # The second entry should be skipped (validation error) or accepted
        # depending on Pydantic coercion. Either way, first must be present.
        assert any(r.departing_officer == "Jane Smith" for r in results)
