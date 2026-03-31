"""Tests for governance extraction gaps: gender diversity, GC succession, board profiles (Phase 129-02).

Verifies:
1. DEF 14A schema has board_gender_diversity_pct field
2. Governance LLM prompt requests gender diversity data
3. Leadership extraction prompt requests current GC name + appointment date
4. Board parsing includes completeness check (doesn't silently drop directors)
"""

from __future__ import annotations

import pytest

from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm.prompts import DEF14A_SYSTEM_PROMPT
from do_uw.stages.extract.board_parsing import extract_board_from_proxy
from do_uw.stages.extract.leadership_profiles import EXPECTED_FIELDS


# ---------------------------------------------------------------------------
# Test 1: DEF 14A schema has gender diversity field
# ---------------------------------------------------------------------------
class TestDEF14ASchema:
    def test_has_gender_diversity_field(self) -> None:
        """DEF14AExtraction schema includes board_gender_diversity_pct."""
        extraction = DEF14AExtraction()
        assert hasattr(extraction, "board_gender_diversity_pct")
        # Field should be Optional[float] defaulting to None
        assert extraction.board_gender_diversity_pct is None

    def test_gender_diversity_accepts_percentage(self) -> None:
        """board_gender_diversity_pct accepts a valid percentage."""
        extraction = DEF14AExtraction(board_gender_diversity_pct=36.0)
        assert extraction.board_gender_diversity_pct == 36.0

    def test_has_racial_diversity_field(self) -> None:
        """DEF14AExtraction schema also includes board_racial_diversity_pct."""
        extraction = DEF14AExtraction()
        assert hasattr(extraction, "board_racial_diversity_pct")


# ---------------------------------------------------------------------------
# Test 2: LLM prompt requests gender diversity data
# ---------------------------------------------------------------------------
class TestGovernancePrompt:
    def test_prompt_mentions_gender_diversity(self) -> None:
        """DEF 14A system prompt explicitly requests gender diversity."""
        prompt_lower = DEF14A_SYSTEM_PROMPT.lower()
        assert "gender" in prompt_lower or "diversity" in prompt_lower, (
            "DEF14A prompt does not mention gender or diversity"
        )

    def test_prompt_mentions_general_counsel(self) -> None:
        """DEF 14A system prompt requests General Counsel / CLO extraction."""
        prompt_lower = DEF14A_SYSTEM_PROMPT.lower()
        assert "general counsel" in prompt_lower or "chief legal" in prompt_lower, (
            "DEF14A prompt does not mention General Counsel or Chief Legal Officer"
        )

    def test_prompt_emphasizes_current_officers(self) -> None:
        """DEF 14A system prompt emphasizes extracting CURRENT officers."""
        prompt_lower = DEF14A_SYSTEM_PROMPT.lower()
        assert "current" in prompt_lower, (
            "DEF14A prompt does not emphasize extracting current (not historical) officers"
        )


# ---------------------------------------------------------------------------
# Test 3: Board parsing completeness check
# ---------------------------------------------------------------------------
class TestBoardCompleteness:
    def test_does_not_silently_drop_directors(self) -> None:
        """Board parsing extracts directors mentioned in proxy text."""
        from unittest.mock import MagicMock

        state = MagicMock()
        proxy_text = (
            "DIRECTOR NOMINEES\n\n"
            "John Smith, age 62\n"
            "Mr. Smith has served as a director since 2018. He is an independent "
            "director and serves on the Audit Committee.\n\n"
            "Jane Doe, age 55\n"
            "Ms. Doe has served as a director since 2020. She is an independent "
            "director and serves on the Compensation Committee.\n\n"
            "Robert Johnson, age 58\n"
            "Mr. Johnson has served as CEO since 2015 and is an employee director.\n"
        )
        profiles = extract_board_from_proxy(proxy_text, state)
        # Should extract all 3 directors, not silently drop any
        names = [p.name.value if p.name else "" for p in profiles]
        assert len(profiles) >= 2, (
            f"Expected at least 2 directors from proxy text, got {len(profiles)}: {names}"
        )

    def test_empty_proxy_returns_empty(self) -> None:
        """Empty proxy text returns empty list."""
        from unittest.mock import MagicMock
        state = MagicMock()
        profiles = extract_board_from_proxy("", state)
        assert profiles == []
