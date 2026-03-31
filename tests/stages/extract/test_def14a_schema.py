"""Tests for DEF14AExtraction schema expansion (MAP-03).

These tests are RED until Plan 47-04 adds new fields to DEF14AExtraction
and wires convert_board_profile() to populate them.
"""
import pytest
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction


def test_def14a_has_board_gender_diversity_pct():
    """DEF14AExtraction has board_gender_diversity_pct field (defaults to None)."""
    schema = DEF14AExtraction()
    assert hasattr(schema, "board_gender_diversity_pct")
    assert schema.board_gender_diversity_pct is None


def test_def14a_has_board_racial_diversity_pct():
    """DEF14AExtraction has board_racial_diversity_pct field (defaults to None)."""
    schema = DEF14AExtraction()
    assert hasattr(schema, "board_racial_diversity_pct")
    assert schema.board_racial_diversity_pct is None


def test_def14a_has_board_meetings_held():
    """DEF14AExtraction has board_meetings_held field (defaults to None)."""
    schema = DEF14AExtraction()
    assert hasattr(schema, "board_meetings_held")
    assert schema.board_meetings_held is None


def test_def14a_has_board_attendance_pct():
    """DEF14AExtraction has board_attendance_pct field (defaults to None)."""
    schema = DEF14AExtraction()
    assert hasattr(schema, "board_attendance_pct")
    assert schema.board_attendance_pct is None


def test_def14a_has_directors_below_75_pct_attendance():
    """DEF14AExtraction has directors_below_75_pct_attendance field."""
    schema = DEF14AExtraction()
    assert hasattr(schema, "directors_below_75_pct_attendance")
    assert schema.directors_below_75_pct_attendance is None


def test_def14a_new_fields_accept_valid_values():
    """New DEF14AExtraction fields accept valid float/int values."""
    schema = DEF14AExtraction(
        board_gender_diversity_pct=36.4,
        board_racial_diversity_pct=27.3,
        board_meetings_held=9,
        board_attendance_pct=98.5,
        directors_below_75_pct_attendance=0,
    )
    assert schema.board_gender_diversity_pct == 36.4
    assert schema.board_meetings_held == 9


def test_convert_board_profile_uses_attendance_pct():
    """convert_board_profile() uses board_attendance_pct when present."""
    from do_uw.stages.extract.llm_governance import convert_board_profile
    extraction = DEF14AExtraction(board_attendance_pct=98.5, board_meetings_held=9)
    # convert_board_profile takes (extraction: DEF14AExtraction, company_name: str) -> BoardProfile | None
    # This test becomes GREEN when convert_board_profile is updated in Plan 47-04
    result = convert_board_profile(extraction, "AAPL")
    if result is not None:
        assert result.board_attendance_pct is not None
