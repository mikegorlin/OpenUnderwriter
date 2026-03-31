"""Tests for forward-looking LLM extraction schema.

Validates extraction models instantiate correctly, handle LLM output
quirks via BeforeValidator coercions, and compose properly.
"""

from __future__ import annotations

import pytest

from do_uw.stages.extract.llm.schemas.forward_looking import (
    ExtractedCatalyst,
    ExtractedForwardStatement,
    ExtractedGuidanceChange,
    ForwardLookingExtraction,
)


class TestExtractedForwardStatement:
    """ExtractedForwardStatement model tests."""

    def test_defaults(self) -> None:
        stmt = ExtractedForwardStatement()
        assert stmt.metric == ""
        assert stmt.target_value == ""
        assert stmt.target_numeric_low is None
        assert stmt.target_numeric_high is None
        assert stmt.is_quantitative is False

    def test_fully_populated(self) -> None:
        stmt = ExtractedForwardStatement(
            metric="Revenue",
            target_value="$48-50B for FY2026",
            target_numeric_low=48.0,
            target_numeric_high=50.0,
            timeframe="FY2026",
            context="Management expects revenue growth driven by cloud expansion",
            is_quantitative=True,
            filing_section="MD&A",
        )
        assert stmt.metric == "Revenue"
        assert stmt.target_numeric_low == pytest.approx(48.0)
        assert stmt.target_numeric_high == pytest.approx(50.0)
        assert stmt.is_quantitative is True

    def test_currency_coercion_low(self) -> None:
        """BeforeValidator strips $ and commas from target_numeric_low."""
        stmt = ExtractedForwardStatement(target_numeric_low="$4.50")  # type: ignore[arg-type]
        assert stmt.target_numeric_low == pytest.approx(4.50)

    def test_currency_coercion_high(self) -> None:
        """BeforeValidator strips $ and commas from target_numeric_high."""
        stmt = ExtractedForwardStatement(target_numeric_high="$1,234.56")  # type: ignore[arg-type]
        assert stmt.target_numeric_high == pytest.approx(1234.56)

    def test_currency_coercion_empty_string(self) -> None:
        """Empty string coerces to None."""
        stmt = ExtractedForwardStatement(target_numeric_low="")  # type: ignore[arg-type]
        assert stmt.target_numeric_low is None

    def test_currency_coercion_none(self) -> None:
        """None passes through unchanged."""
        stmt = ExtractedForwardStatement(target_numeric_low=None)
        assert stmt.target_numeric_low is None

    def test_qualitative_statement(self) -> None:
        stmt = ExtractedForwardStatement(
            metric="Market expansion",
            target_value="Expect to enter 3 new international markets",
            is_quantitative=False,
            filing_section="Outlook",
        )
        assert stmt.is_quantitative is False
        assert stmt.target_numeric_low is None


class TestExtractedGuidanceChange:
    """ExtractedGuidanceChange model tests."""

    def test_defaults(self) -> None:
        gc = ExtractedGuidanceChange()
        assert gc.change_type == ""
        assert gc.metric == ""

    def test_guidance_cut(self) -> None:
        gc = ExtractedGuidanceChange(
            change_type="CUT",
            metric="EPS",
            prior_value="$4.50-$4.70",
            new_value="$4.00-$4.20",
            date="2025-10-15",
        )
        assert gc.change_type == "CUT"
        assert gc.prior_value == "$4.50-$4.70"


class TestExtractedCatalyst:
    """ExtractedCatalyst model tests."""

    def test_defaults(self) -> None:
        cat = ExtractedCatalyst()
        assert cat.event == ""
        assert cat.mentioned_in == ""

    def test_populated(self) -> None:
        cat = ExtractedCatalyst(
            event="FDA approval decision for lead drug candidate",
            expected_timing="Q2 2026",
            potential_impact="Stock decline 20-30%, SCA likely if denied",
            mentioned_in="Risk Factors",
        )
        assert "FDA" in cat.event
        assert cat.expected_timing == "Q2 2026"


class TestForwardLookingExtraction:
    """ForwardLookingExtraction model tests."""

    def test_defaults(self) -> None:
        fle = ForwardLookingExtraction()
        assert fle.forward_statements == []
        assert fle.guidance_changes == []
        assert fle.catalyst_events == []
        assert fle.provides_numeric_guidance is False
        assert fle.guidance_summary == ""

    def test_mixed_quantitative_qualitative(self) -> None:
        """Extraction with both quantitative and qualitative statements."""
        fle = ForwardLookingExtraction(
            forward_statements=[
                ExtractedForwardStatement(
                    metric="Revenue",
                    target_value="$48-50B",
                    target_numeric_low=48.0,
                    target_numeric_high=50.0,
                    is_quantitative=True,
                ),
                ExtractedForwardStatement(
                    metric="Market expansion",
                    target_value="Expect significant growth in APAC",
                    is_quantitative=False,
                ),
            ],
            provides_numeric_guidance=True,
            guidance_summary="Company guides revenue $48-50B with APAC expansion plans.",
        )
        assert len(fle.forward_statements) == 2
        quant = [s for s in fle.forward_statements if s.is_quantitative]
        qual = [s for s in fle.forward_statements if not s.is_quantitative]
        assert len(quant) == 1
        assert len(qual) == 1
        assert fle.provides_numeric_guidance is True

    def test_with_guidance_changes(self) -> None:
        fle = ForwardLookingExtraction(
            guidance_changes=[
                ExtractedGuidanceChange(change_type="CUT", metric="EPS"),
                ExtractedGuidanceChange(change_type="REAFFIRM", metric="Revenue"),
            ],
        )
        assert len(fle.guidance_changes) == 2

    def test_with_catalysts(self) -> None:
        fle = ForwardLookingExtraction(
            catalyst_events=[
                ExtractedCatalyst(event="M&A completion", expected_timing="Q1 2026"),
            ],
        )
        assert len(fle.catalyst_events) == 1

    def test_serialization_roundtrip(self) -> None:
        """ForwardLookingExtraction serializes to dict and back."""
        fle = ForwardLookingExtraction(
            forward_statements=[
                ExtractedForwardStatement(
                    metric="EPS",
                    target_numeric_low=4.5,
                    target_numeric_high=4.7,
                ),
            ],
            provides_numeric_guidance=True,
        )
        data = fle.model_dump()
        restored = ForwardLookingExtraction.model_validate(data)
        assert restored.forward_statements[0].metric == "EPS"
        assert restored.forward_statements[0].target_numeric_low == pytest.approx(4.5)
        assert restored.provides_numeric_guidance is True
