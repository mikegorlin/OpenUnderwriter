"""Tests proving CRF ceiling display values match size-resolved ceilings.

Validates that the HTML context builder reads resolved ceiling values
from ceiling_details (size-adjusted) rather than flat config values.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_scoring_with_ceilings(
    quality_score: float = 65.0,
    ceiling_details: list[dict] | None = None,
    red_flags: list | None = None,
) -> MagicMock:
    """Build a mock scoring object with ceiling details."""
    scoring = MagicMock()
    scoring.quality_score = quality_score
    scoring.composite_score = 80.0
    scoring.total_risk_points = 20.0
    scoring.binding_ceiling_id = "CRF-1" if ceiling_details else None

    # Ceiling details from apply_crf_ceilings
    if ceiling_details:
        details = []
        for cd in ceiling_details:
            detail = MagicMock()
            detail.resolved_ceiling = cd.get("resolved_ceiling")
            detail.ceiling = cd.get("ceiling", cd.get("resolved_ceiling"))
            detail.crf_id = cd.get("crf_id", "CRF-1")
            detail.role = cd.get("role", "primary")
            details.append(detail)
        scoring.ceiling_details = details
    else:
        scoring.ceiling_details = []

    # Red flags
    if red_flags:
        scoring.red_flags = red_flags
    else:
        rf = MagicMock()
        rf.triggered = True
        rf.flag_id = "CRF-1"
        rf.flag_name = "Active SCA"
        rf.ceiling_applied = 60
        rf.max_tier = "WRITE"
        rf.evidence = ["Active SCA: Smith v. Corp"]
        scoring.red_flags = [rf]

    scoring.factor_scores = []
    scoring.patterns_detected = []
    scoring.tier = MagicMock()
    scoring.tier.tier = "WRITE"
    scoring.tier.action = "Review"
    scoring.tier.probability_range = "5-10%"
    scoring.tier.score_range_low = 50
    scoring.tier.score_range_high = 70
    scoring.claim_probability = None
    scoring.severity_scenarios = None
    scoring.tower_recommendation = None
    scoring.risk_type = None
    scoring.calibration_notes = None
    scoring.red_flag_summary = None
    scoring.hae_result = None
    scoring.severity_result = None

    return scoring


class TestCRFCeilingDisplay:
    """Tests for ceiling display consistency."""

    def test_mid_cap_ceiling_displayed(self) -> None:
        """Mid-cap resolved ceiling ($25M -> ceiling 60) should be used in display."""
        from do_uw.stages.render.context_builders.scoring import extract_scoring

        state = MagicMock()
        state.scoring = _make_scoring_with_ceilings(
            quality_score=60.0,
            ceiling_details=[{
                "crf_id": "CRF-1",
                "resolved_ceiling": 60,
                "role": "primary",
            }],
        )
        state.executive_summary = None
        state.extracted = MagicMock()
        state.extracted.financials = None
        state.benchmark = None

        result = extract_scoring(state)
        # The ceiling in red_flags should match the resolved value
        assert len(result.get("red_flags", [])) > 0
        rf = result["red_flags"][0]
        assert rf["ceiling"] == "60"

    def test_large_cap_ceiling_displayed(self) -> None:
        """Large-cap resolved ceiling (ceiling 50) should be used in display."""
        from do_uw.stages.render.context_builders.scoring import extract_scoring

        state = MagicMock()
        state.scoring = _make_scoring_with_ceilings(
            quality_score=50.0,
            ceiling_details=[{
                "crf_id": "CRF-1",
                "resolved_ceiling": 50,
                "role": "primary",
            }],
        )
        state.executive_summary = None
        state.extracted = MagicMock()
        state.extracted.financials = None
        state.benchmark = None

        result = extract_scoring(state)
        assert len(result.get("red_flags", [])) > 0
        rf = result["red_flags"][0]
        assert rf["ceiling"] == "50"

    def test_fallback_to_quality_score_when_no_details(self) -> None:
        """When no ceiling_details, fall back to quality_score."""
        from do_uw.stages.render.context_builders.scoring import extract_scoring

        state = MagicMock()
        state.scoring = _make_scoring_with_ceilings(
            quality_score=72.0,
            ceiling_details=None,
        )
        state.executive_summary = None
        state.extracted = MagicMock()
        state.extracted.financials = None
        state.benchmark = None

        result = extract_scoring(state)
        if result.get("red_flags"):
            rf = result["red_flags"][0]
            assert rf["ceiling"] == "72"
