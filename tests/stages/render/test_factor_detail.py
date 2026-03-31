"""Tests for per-factor scoring detail with collapsible sections.

Validates that factor detail rendering produces correct evidence,
D&O context, and structural elements for both context building and
HTML template output.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.scoring import FactorScore, ScoringResult, TierClassification, Tier
from do_uw.stages.render.sections.sect7_scoring_factors import (
    build_factor_detail_context,
    render_factor_details,
)


def _make_factor(
    factor_id: str = "F.1",
    factor_name: str = "Prior Litigation",
    max_points: int = 20,
    points_deducted: float = 12.0,
    evidence: list[str] | None = None,
    rules_triggered: list[str] | None = None,
    signal_contributions: list[dict[str, Any]] | None = None,
) -> FactorScore:
    """Create a test FactorScore."""
    return FactorScore(
        factor_id=factor_id,
        factor_name=factor_name,
        max_points=max_points,
        points_deducted=points_deducted,
        evidence=evidence or [],
        rules_triggered=rules_triggered or [],
        signal_contributions=signal_contributions or [],
    )


def _make_scoring(factors: list[FactorScore] | None = None) -> ScoringResult:
    """Create a test ScoringResult with given factors."""
    return ScoringResult(
        composite_score=65.0,
        quality_score=65.0,
        total_risk_points=35.0,
        factor_scores=factors or [],
        tier=TierClassification(
            tier=Tier.WRITE, score_range_low=51, score_range_high=70,
        ),
    )


class TestBuildFactorDetailContext:
    """Test build_factor_detail_context()."""

    def test_factor_detail_renders_evidence(self) -> None:
        """Evidence list is joined into evidence string."""
        factors = [_make_factor(
            evidence=["Active SCA: Smith v. RPM filed 2025-03", "Prior SCA settled 2023"],
            points_deducted=12.0,
        )]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        assert len(details) == 1
        assert "Active SCA: Smith v. RPM filed 2025-03" in details[0]["evidence"]
        assert "Prior SCA settled 2023" in details[0]["evidence"]

    def test_factor_detail_renders_do_context(self) -> None:
        """D&O context is extracted from signal contributions."""
        mock_signal_results = {
            "LIT.SCA.ACTIVE": {
                "status": "TRIGGERED",
                "value": 1,
                "threshold_level": "RED",
                "evidence": "Active SCA",
                "source": "SCAC Database",
                "confidence": "HIGH",
                "threshold_context": "",
                "details": {},
                "do_context": "Active securities class action creates direct D&O exposure.",
            }
        }
        factors = [_make_factor(
            signal_contributions=[{"signal_id": "LIT.SCA.ACTIVE", "weight": 0.4}],
            points_deducted=15.0,
        )]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, mock_signal_results)

        assert details[0]["do_context"] == "Active securities class action creates direct D&O exposure."

    def test_factor_detail_collapsible_structure(self) -> None:
        """Factor detail contains structural keys for collapsible rendering."""
        factors = [_make_factor(points_deducted=5.0)]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        detail = details[0]
        assert "factor_id" in detail
        assert "factor_name" in detail
        assert "score" in detail
        assert "evidence" in detail
        assert "do_context" in detail
        assert "sources" in detail
        assert "rules" in detail

    def test_factor_detail_empty_do_context(self) -> None:
        """Empty do_context when no signal contributions have do_context."""
        factors = [_make_factor(
            signal_contributions=[{"signal_id": "MISSING.SIGNAL", "weight": 0.2}],
            points_deducted=5.0,
        )]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        assert details[0]["do_context"] == ""

    def test_all_ten_factors_rendered(self) -> None:
        """All 10 factors appear in output regardless of deductions."""
        factors = [
            _make_factor(factor_id=f"F.{i}", factor_name=f"Factor {i}",
                         max_points=10, points_deducted=float(i))
            for i in range(1, 11)
        ]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        assert len(details) == 10
        ids = [d["factor_id"] for d in details]
        for i in range(1, 11):
            assert f"F.{i}" in ids

    def test_score_format(self) -> None:
        """Score is formatted as 'deducted/max'."""
        factors = [_make_factor(points_deducted=7.5, max_points=15)]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        assert details[0]["score"] == "8/15"  # 7.5 rounds to 8

    def test_rules_triggered_list(self) -> None:
        """Rules triggered are passed through as list."""
        factors = [_make_factor(
            rules_triggered=["F1-001", "F1-003"],
            points_deducted=10.0,
        )]
        scoring = _make_scoring(factors)
        details = build_factor_detail_context(scoring, None)

        assert details[0]["rules"] == ["F1-001", "F1-003"]


class TestRenderFactorDetailsWord:
    """Test render_factor_details() Word output."""

    def test_word_output_creates_heading(self) -> None:
        """Word output creates 'Per-Factor Detail' heading."""
        doc = MagicMock()
        ds = MagicMock()
        ds.size_body = 10
        ds.size_small = 8
        factors = [_make_factor(
            evidence=["Test evidence"],
            points_deducted=5.0,
        )]
        scoring = _make_scoring(factors)

        render_factor_details(doc, scoring, None, ds)

        # First call should be the heading
        heading_call = doc.add_paragraph.call_args_list[0]
        assert heading_call[1].get("style") == "DOHeading3"

    def test_word_output_no_deductions(self) -> None:
        """Word output shows 'No factors' when all deductions are 0."""
        doc = MagicMock()
        ds = MagicMock()
        factors = [_make_factor(points_deducted=0.0)]
        scoring = _make_scoring(factors)

        render_factor_details(doc, scoring, None, ds)

        # Should have heading + one body paragraph
        calls = doc.add_paragraph.call_args_list
        assert len(calls) == 2  # heading + "No factors"


class TestFactorDetailTemplate:
    """Test factor_detail.html.j2 template content."""

    def test_template_contains_collapsible(self) -> None:
        """Template file contains <details and What Was Found."""
        from pathlib import Path
        template = Path("src/do_uw/templates/html/sections/scoring/factor_detail.html.j2")
        content = template.read_text()
        assert "<details" in content
        assert "<summary" in content
        assert "What Was Found" in content
        assert "Underwriting Commentary" in content
        assert "collapsible" in content
