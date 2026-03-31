"""Tests for LLM narrative generator with caching and fallback.

All LLM calls are mocked -- no real API calls in tests.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.density import DensityLevel, PreComputedNarratives
from do_uw.stages.benchmark.narrative_generator import (
    _cache_key,
    _extract_section_data,
    clear_cache,
    generate_all_narratives,
    generate_executive_thesis,
    generate_meeting_prep_questions,
    generate_section_narrative,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clear_narrative_cache() -> None:
    """Ensure clean cache state for each test."""
    clear_cache()


def _mock_client(text: str = "Test narrative text.") -> MagicMock:
    """Create a mock Anthropic client returning fixed text."""
    client = MagicMock()
    response = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    response.content = [content_block]
    client.messages.create.return_value = response
    return client


def _minimal_state() -> Any:
    """Create a minimal AnalysisState-like object for testing."""
    from do_uw.models.density import SectionDensity
    from do_uw.models.state import AnalysisState

    state = AnalysisState(ticker="TEST")
    # Ensure analysis exists with section_densities
    if state.analysis is None:
        from do_uw.models.state import AnalysisResults

        state.analysis = AnalysisResults()
    state.analysis.section_densities = {
        "company": SectionDensity(level=DensityLevel.CLEAN),
        "financial": SectionDensity(level=DensityLevel.ELEVATED),
        "market": SectionDensity(level=DensityLevel.CLEAN),
        "governance": SectionDensity(level=DensityLevel.CRITICAL),
        "litigation": SectionDensity(level=DensityLevel.CLEAN),
        "scoring": SectionDensity(level=DensityLevel.ELEVATED),
    }
    return state


# ---------------------------------------------------------------------------
# Cache key tests
# ---------------------------------------------------------------------------
class TestCacheKey:
    """Tests for cache key computation."""

    def test_cache_key_deterministic(self) -> None:
        """Same input produces same key."""
        data = {"score": 75, "tier": "WRITE"}
        key1 = _cache_key("scoring", "CLEAN", data)
        key2 = _cache_key("scoring", "CLEAN", data)
        assert key1 == key2

    def test_cache_key_differs_on_density(self) -> None:
        """Different density levels produce different keys."""
        data = {"score": 75}
        key_clean = _cache_key("scoring", "CLEAN", data)
        key_elevated = _cache_key("scoring", "ELEVATED", data)
        assert key_clean != key_elevated

    def test_cache_key_differs_on_section(self) -> None:
        """Different sections produce different keys."""
        data = {"value": 42}
        key_fin = _cache_key("financial", "CLEAN", data)
        key_mkt = _cache_key("market", "CLEAN", data)
        assert key_fin != key_mkt

    def test_cache_key_differs_on_data(self) -> None:
        """Different data produces different keys."""
        key1 = _cache_key("scoring", "CLEAN", {"score": 75})
        key2 = _cache_key("scoring", "CLEAN", {"score": 50})
        assert key1 != key2

    def test_cache_key_length(self) -> None:
        """Cache key is 16 hex chars."""
        key = _cache_key("test", "CLEAN", {})
        assert len(key) == 16
        # All hex chars
        assert all(c in "0123456789abcdef" for c in key)


# ---------------------------------------------------------------------------
# Section narrative tests
# ---------------------------------------------------------------------------
class TestGenerateSectionNarrative:
    """Tests for generate_section_narrative."""

    def test_basic_generation(self) -> None:
        """Generates narrative from LLM response."""
        client = _mock_client("The company shows strong financials.")
        result = generate_section_narrative(
            "financial", {"score": 75}, DensityLevel.CLEAN,
            "Test Corp", client,
        )
        assert "strong financials" in result

    def test_cache_hit_skips_llm(self) -> None:
        """Second call with same data returns cached result."""
        client = _mock_client("First result.")
        data = {"x": 1}
        result1 = generate_section_narrative(
            "test", data, DensityLevel.CLEAN, "Corp", client,
        )
        result2 = generate_section_narrative(
            "test", data, DensityLevel.CLEAN, "Corp", client,
        )
        assert result1 == result2
        # Only one API call (second was cached)
        assert client.messages.create.call_count == 1

    def test_density_controls_max_tokens_clean(self) -> None:
        """CLEAN density uses 600 max_tokens."""
        client = _mock_client("Short narrative.")
        generate_section_narrative(
            "company", {}, DensityLevel.CLEAN, "Corp", client,
        )
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 600

    def test_density_controls_max_tokens_elevated(self) -> None:
        """ELEVATED density uses 900 max_tokens."""
        client = _mock_client("Medium narrative.")
        generate_section_narrative(
            "company", {}, DensityLevel.ELEVATED, "Corp", client,
        )
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 900

    def test_density_controls_max_tokens_critical(self) -> None:
        """CRITICAL density uses 1200 max_tokens."""
        client = _mock_client("Long narrative.")
        generate_section_narrative(
            "company", {}, DensityLevel.CRITICAL, "Corp", client,
        )
        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 1200

    def test_prompt_includes_density_guidance(self) -> None:
        """Prompt includes density-specific length guidance."""
        client = _mock_client("Result.")
        generate_section_narrative(
            "financial", {}, DensityLevel.ELEVATED, "Corp", client,
        )
        call_kwargs = client.messages.create.call_args.kwargs
        prompt = call_kwargs["messages"][0]["content"]
        assert "6-8 sentences" in prompt
        # Section-specific prompts embed density via length guide
        assert "D&O exposure" in prompt or "ELEVATED" in prompt

    def test_raises_without_client(self) -> None:
        """Raises ImportError when no client available."""
        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=None,
        ):
            with pytest.raises(ImportError, match="Anthropic client"):
                generate_section_narrative(
                    "test", {}, DensityLevel.CLEAN, "Corp",
                )


# ---------------------------------------------------------------------------
# Executive thesis tests
# ---------------------------------------------------------------------------
class TestGenerateExecutiveThesis:
    """Tests for executive thesis generation."""

    def test_thesis_generation(self) -> None:
        """Generates executive thesis from LLM response."""
        client = _mock_client("WRITE tier recommendation with moderate risk.")
        result = generate_executive_thesis(
            {"quality_score": 75, "tier": "WRITE"},
            DensityLevel.ELEVATED, "Test Corp", client,
        )
        assert "WRITE" in result

    def test_thesis_tiered_length(self) -> None:
        """CLEAN thesis requests 5-7 sentences."""
        client = _mock_client("Short thesis.")
        generate_executive_thesis(
            {}, DensityLevel.CLEAN, "Corp", client,
        )
        prompt = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "5-7 sentences" in prompt

    def test_thesis_elevated_length(self) -> None:
        """ELEVATED thesis requests 8-10 sentences."""
        client = _mock_client("Longer thesis.")
        generate_executive_thesis(
            {}, DensityLevel.ELEVATED, "Corp", client,
        )
        prompt = client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "8-10 sentences" in prompt


# ---------------------------------------------------------------------------
# Meeting prep questions tests
# ---------------------------------------------------------------------------
class TestGenerateMeetingPrepQuestions:
    """Tests for meeting prep question generation."""

    def test_questions_from_json_array(self) -> None:
        """Parses JSON array response correctly."""
        questions = [
            "What actions has management taken to address the SEC inquiry?",
            "Can you explain the insider selling pattern near the 8-K filing?",
        ]
        client = _mock_client(json.dumps(questions))
        result = generate_meeting_prep_questions(
            {"red_flags": ["SEC inquiry"]},
            DensityLevel.CLEAN, "Corp", client,
        )
        assert len(result) == 2
        assert "SEC inquiry" in result[0]

    def test_questions_capped_at_max(self) -> None:
        """Questions capped at max for density level."""
        many_questions = [f"Question {i}?" for i in range(15)]
        client = _mock_client(json.dumps(many_questions))
        result = generate_meeting_prep_questions(
            {}, DensityLevel.CLEAN, "Corp", client,
        )
        # CLEAN max is 5
        assert len(result) <= 5

    def test_questions_fallback_on_invalid_json(self) -> None:
        """Falls back to line-splitting when JSON parsing fails."""
        raw_text = (
            "1. What drove the revenue decline?\n"
            "2. How will management address the going concern?\n"
            "3. What is the timeline for debt refinancing?"
        )
        client = _mock_client(raw_text)
        result = generate_meeting_prep_questions(
            {}, DensityLevel.CLEAN, "Corp", client,
        )
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# Fallback tests
# ---------------------------------------------------------------------------
class TestNarrativeFallback:
    """Tests for fallback to rule-based narratives when LLM unavailable."""

    def test_narrative_fallback_on_import_error(self) -> None:
        """Falls back to rule-based when anthropic not installed."""
        state = _minimal_state()

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=None,
        ):
            result = generate_all_narratives(state)

        assert isinstance(result, PreComputedNarratives)
        # Executive summary should be None (no rule-based fallback)
        assert result.executive_summary is None
        # Meeting prep should be empty (no fallback)
        assert result.meeting_prep_questions == []

    def test_fallback_does_not_label_ai_assessment(self) -> None:
        """Rule-based fallback narratives lack AI Assessment prefix."""
        state = _minimal_state()

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=None,
        ):
            with patch(
                "do_uw.stages.benchmark.narrative_generator._fallback_narrative",
                return_value="Rule-based governance narrative.",
            ):
                result = generate_all_narratives(state)

        # Check that at least one section has the fallback (non-AI) text
        for section_id in ("company", "governance", "litigation", "scoring"):
            val = getattr(result, section_id, None)
            if val:
                assert not val.startswith("AI Assessment:")


# ---------------------------------------------------------------------------
# generate_all_narratives structure tests
# ---------------------------------------------------------------------------
class TestGenerateAllNarratives:
    """Tests for the main entry point."""

    def test_returns_precomputed_narratives(self) -> None:
        """Returns PreComputedNarratives model."""
        state = _minimal_state()
        client = _mock_client("Section narrative.")

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=client,
        ):
            result = generate_all_narratives(state)

        assert isinstance(result, PreComputedNarratives)

    def test_all_sections_populated(self) -> None:
        """All 7 section fields get populated."""
        state = _minimal_state()
        client = _mock_client("Narrative for section.")

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=client,
        ):
            result = generate_all_narratives(state)

        for section_id in (
            "company", "financial", "market", "governance",
            "litigation", "scoring", "ai_risk",
        ):
            val = getattr(result, section_id)
            assert val is not None, f"{section_id} should be populated"
            assert len(val) > 0, f"{section_id} should not be empty"

    def test_partial_failure_continues(self) -> None:
        """Failure on one section doesn't crash the whole batch."""
        state = _minimal_state()
        call_count = 0

        def side_effect(**kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("LLM API error")
            response = MagicMock()
            content_block = MagicMock()
            content_block.text = f"Narrative {call_count}."
            response.content = [content_block]
            return response

        client = MagicMock()
        client.messages.create.side_effect = side_effect

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=client,
        ):
            result = generate_all_narratives(state)

        # Should still return a result (partial)
        assert isinstance(result, PreComputedNarratives)

    def test_executive_summary_populated(self) -> None:
        """Executive summary thesis is generated."""
        state = _minimal_state()
        client = _mock_client("Thesis text.")

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=client,
        ):
            result = generate_all_narratives(state)

        assert result.executive_summary is not None
        assert len(result.executive_summary) > 0

    def test_meeting_prep_populated(self) -> None:
        """Meeting prep questions are generated."""
        state = _minimal_state()
        questions = ["Q1?", "Q2?", "Q3?"]
        client = _mock_client(json.dumps(questions))

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=client,
        ):
            result = generate_all_narratives(state)

        assert len(result.meeting_prep_questions) > 0


# ---------------------------------------------------------------------------
# Section data extraction tests
# ---------------------------------------------------------------------------
class TestExtractSectionData:
    """Tests for _extract_section_data helper."""

    def test_empty_state_returns_empty_dict(self) -> None:
        """Empty state produces empty section data."""
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        data = _extract_section_data(state, "company")
        assert data == {}

    def test_unknown_section_returns_empty(self) -> None:
        """Unknown section ID returns empty dict."""
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        data = _extract_section_data(state, "unknown_section")
        assert data == {}
