"""Tests for SectionCommentary and PreComputedCommentary Pydantic models.

Covers VOICE-03: Commentary cached on state model with serialization.
"""

from __future__ import annotations

import json

import pytest


def test_section_commentary_creation():
    """SectionCommentary can be created with all fields."""
    from do_uw.models.density import SectionCommentary

    sc = SectionCommentary(
        what_was_said="Revenue was $10B, up 15% YoY.",
        underwriting_commentary="This growth reduces going-concern risk under Section 10(b).",
        confidence="HIGH",
        hallucination_warnings=["Some warning"],
    )
    assert sc.what_was_said == "Revenue was $10B, up 15% YoY."
    assert sc.underwriting_commentary.startswith("This growth")
    assert sc.confidence == "HIGH"
    assert len(sc.hallucination_warnings) == 1


def test_section_commentary_defaults():
    """SectionCommentary has sensible defaults for all fields."""
    from do_uw.models.density import SectionCommentary

    sc = SectionCommentary()
    assert sc.what_was_said == ""
    assert sc.underwriting_commentary == ""
    assert sc.confidence == "MEDIUM"
    assert sc.hallucination_warnings == []


def test_precomputed_commentary_creation():
    """PreComputedCommentary has 8 optional section fields."""
    from do_uw.models.density import PreComputedCommentary, SectionCommentary

    pcc = PreComputedCommentary(
        financial=SectionCommentary(what_was_said="Financial data."),
        market=SectionCommentary(what_was_said="Market data."),
    )
    assert pcc.financial is not None
    assert pcc.financial.what_was_said == "Financial data."
    assert pcc.market is not None
    assert pcc.governance is None
    assert pcc.litigation is None
    assert pcc.scoring is None
    assert pcc.company is None
    assert pcc.executive_brief is None
    assert pcc.meeting_prep is None


def test_precomputed_commentary_all_none_by_default():
    """PreComputedCommentary fields default to None."""
    from do_uw.models.density import PreComputedCommentary

    pcc = PreComputedCommentary()
    for field_name in [
        "executive_brief", "financial", "market", "governance",
        "litigation", "scoring", "company", "meeting_prep",
    ]:
        assert getattr(pcc, field_name) is None


def test_precomputed_commentary_json_roundtrip():
    """PreComputedCommentary round-trips through JSON (model_dump/model_validate)."""
    from do_uw.models.density import PreComputedCommentary, SectionCommentary

    original = PreComputedCommentary(
        financial=SectionCommentary(
            what_was_said="Revenue $5B.",
            underwriting_commentary="Low risk.",
            confidence="HIGH",
            hallucination_warnings=["warn1"],
        ),
        litigation=SectionCommentary(
            what_was_said="No active SCAs.",
            underwriting_commentary="Clean litigation history.",
            confidence="HIGH",
        ),
    )
    dumped = original.model_dump()
    json_str = json.dumps(dumped)
    loaded = json.loads(json_str)
    restored = PreComputedCommentary.model_validate(loaded)

    assert restored.financial is not None
    assert restored.financial.what_was_said == "Revenue $5B."
    assert restored.financial.hallucination_warnings == ["warn1"]
    assert restored.litigation is not None
    assert restored.litigation.confidence == "HIGH"
    assert restored.governance is None


def test_section_commentary_json_roundtrip():
    """SectionCommentary individually round-trips."""
    from do_uw.models.density import SectionCommentary

    sc = SectionCommentary(
        what_was_said="Test data.",
        underwriting_commentary="Test commentary.",
        confidence="LOW",
        hallucination_warnings=["w1", "w2"],
    )
    restored = SectionCommentary.model_validate(sc.model_dump())
    assert restored.confidence == "LOW"
    assert len(restored.hallucination_warnings) == 2
