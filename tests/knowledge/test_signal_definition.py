"""Tests for SignalDefinition Pydantic model and enrichment types.

Validates backward compatibility with existing signals.json, enum values,
sub-model creation, round-trip serialization, and extra field preservation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.knowledge.signal_definition import (
    SignalDefinition,
    ContentType,
    DataStrategy,
    DepthLevel,
    EvaluationCriteria,
    PresentationHint,
)

# Sample check dict copied from the first check in signals.json
SAMPLE_CHECK: dict[str, Any] = {
    "id": "BIZ.CLASS.primary",
    "name": "Primary D&O Risk Classification",
    "section": 1,
    "pillar": "P1_WHAT_WRONG",
    "factors": [],
    "required_data": ["SEC_10K"],
    "data_locations": {"SEC_10K": ["item_1_business", "item_7_mda"]},
    "threshold": {
        "type": "classification",
        "values": [
            "BINARY_EVENT",
            "GROWTH_DARLING",
            "GUIDANCE_DEPENDENT",
            "REGULATORY_SENSITIVE",
            "TRANSFORMATION",
            "STABLE_MATURE",
            "DISTRESSED",
        ],
    },
    "execution_mode": "AUTO",
    "claims_correlation": 1.0,
    "tier": 1,
    "category": "CONTEXT_DISPLAY",
    "signal_type": "STRUCTURAL",
    "hazard_or_signal": "HAZARD",
    "plaintiff_lenses": ["SHAREHOLDERS"],
}


class TestContentType:
    """Tests for ContentType enum."""

    def test_enum_values(self) -> None:
        assert ContentType.MANAGEMENT_DISPLAY == "MANAGEMENT_DISPLAY"
        assert ContentType.EVALUATIVE_CHECK == "EVALUATIVE_CHECK"
        assert ContentType.INFERENCE_PATTERN == "INFERENCE_PATTERN"

    def test_enum_count(self) -> None:
        assert len(ContentType) == 3

    def test_str_enum(self) -> None:
        """ContentType is a StrEnum, so it behaves like a string."""
        ct = ContentType.MANAGEMENT_DISPLAY
        assert isinstance(ct, str)
        assert ct == "MANAGEMENT_DISPLAY"


class TestDepthLevel:
    """Tests for DepthLevel IntEnum."""

    def test_range_1_to_4(self) -> None:
        assert DepthLevel.DISPLAY == 1
        assert DepthLevel.COMPUTE == 2
        assert DepthLevel.INFER == 3
        assert DepthLevel.HUNT == 4

    def test_enum_count(self) -> None:
        assert len(DepthLevel) == 4

    def test_int_enum(self) -> None:
        """DepthLevel is an IntEnum, so it behaves like an int."""
        d = DepthLevel.HUNT
        assert isinstance(d, int)
        assert d == 4

    def test_comparison(self) -> None:
        """DepthLevel values are comparable as integers."""
        assert DepthLevel.DISPLAY < DepthLevel.COMPUTE
        assert DepthLevel.COMPUTE < DepthLevel.INFER
        assert DepthLevel.INFER < DepthLevel.HUNT


class TestDataStrategy:
    """Tests for DataStrategy sub-model."""

    def test_minimal(self) -> None:
        ds = DataStrategy(primary_source="SEC_10K")
        assert ds.primary_source == "SEC_10K"
        assert ds.extraction_path is None
        assert ds.field_key is None
        assert ds.fallback_sources == []
        assert ds.computation is None

    def test_with_field_key_and_extraction_path(self) -> None:
        ds = DataStrategy(
            primary_source="SEC_10K",
            extraction_path="financials.liquidity.current_ratio",
            field_key="current_ratio",
            fallback_sources=["SEC_10Q"],
        )
        assert ds.extraction_path == "financials.liquidity.current_ratio"
        assert ds.field_key == "current_ratio"
        assert ds.fallback_sources == ["SEC_10Q"]

    def test_with_computation(self) -> None:
        ds = DataStrategy(
            primary_source="SEC_10K",
            computation="_compute_ceo_cfo_selling_pct",
        )
        assert ds.computation == "_compute_ceo_cfo_selling_pct"


class TestEvaluationCriteria:
    """Tests for EvaluationCriteria sub-model."""

    def test_minimal(self) -> None:
        ec = EvaluationCriteria(type="boolean")
        assert ec.type == "boolean"
        assert ec.metric is None
        assert ec.direction is None
        assert ec.thresholds is None

    def test_tiered_thresholds(self) -> None:
        ec = EvaluationCriteria(
            type="tiered",
            metric="current_ratio",
            direction="lower_is_worse",
            thresholds={"red": "<0.5", "yellow": "0.5-1.0", "clear": ">1.0"},
        )
        assert ec.type == "tiered"
        assert ec.metric == "current_ratio"
        assert ec.direction == "lower_is_worse"
        assert ec.thresholds is not None
        assert ec.thresholds["red"] == "<0.5"


class TestPresentationHint:
    """Tests for PresentationHint sub-model."""

    def test_minimal(self) -> None:
        ph = PresentationHint()
        assert ph.display_format is None
        assert ph.worksheet_label is None
        assert ph.section_placement is None

    def test_full(self) -> None:
        ph = PresentationHint(
            display_format="ratio",
            worksheet_label="Current Ratio",
            section_placement="Financial Health",
        )
        assert ph.display_format == "ratio"
        assert ph.worksheet_label == "Current Ratio"


class TestSignalDefinition:
    """Tests for SignalDefinition model."""

    def test_existing_check_validates_with_defaults(self) -> None:
        """An existing check dict validates with all enrichment defaults applied."""
        cd = SignalDefinition.model_validate(SAMPLE_CHECK)
        assert cd.id == "BIZ.CLASS.primary"
        assert cd.name == "Primary D&O Risk Classification"
        assert cd.section == 1
        assert cd.pillar == "P1_WHAT_WRONG"
        assert cd.execution_mode == "AUTO"
        assert cd.claims_correlation == 1.0
        assert cd.tier == 1
        assert cd.category == "CONTEXT_DISPLAY"
        assert cd.signal_type == "STRUCTURAL"
        assert cd.hazard_or_signal == "HAZARD"
        assert cd.plaintiff_lenses == ["SHAREHOLDERS"]
        # Enrichment defaults
        assert cd.content_type == ContentType.EVALUATIVE_CHECK
        assert cd.depth == DepthLevel.COMPUTE
        assert cd.rationale is None
        assert cd.data_strategy is None
        assert cd.evaluation_criteria is None
        assert cd.presentation is None
        assert cd.pattern_ref is None

    def test_from_signal_dict(self) -> None:
        """from_signal_dict class method works."""
        cd = SignalDefinition.from_signal_dict(SAMPLE_CHECK)
        assert cd.id == "BIZ.CLASS.primary"
        assert cd.content_type == ContentType.EVALUATIVE_CHECK

    def test_to_signal_dict(self) -> None:
        """to_signal_dict excludes None values."""
        cd = SignalDefinition.from_signal_dict(SAMPLE_CHECK)
        d = cd.to_signal_dict()
        assert d["id"] == "BIZ.CLASS.primary"
        assert "rationale" not in d  # None fields excluded
        assert "data_strategy" not in d
        assert "content_type" in d  # Has a default value, not None

    def test_round_trip_preserves_fields(self) -> None:
        """from_signal_dict -> to_signal_dict preserves original fields."""
        cd = SignalDefinition.from_signal_dict(SAMPLE_CHECK)
        d = cd.to_signal_dict()
        # All original fields preserved
        for key in SAMPLE_CHECK:
            assert key in d, f"Original field {key!r} missing after round-trip"
            assert d[key] == SAMPLE_CHECK[key], (
                f"Field {key!r} changed: {SAMPLE_CHECK[key]!r} -> {d[key]!r}"
            )

    def test_extra_fields_preserved(self) -> None:
        """Extra fields not in the model schema are preserved (extra='allow')."""
        check_with_extras = {
            **SAMPLE_CHECK,
            "amplifier": True,
            "amplifier_bonus_points": 2,
            "sector_adjustments": {"BIOT": {"yellow": "15-25%", "red": ">25%"}},
        }
        cd = SignalDefinition.model_validate(check_with_extras)
        d = cd.to_signal_dict()
        assert d["amplifier"] is True
        assert d["amplifier_bonus_points"] == 2
        assert d["sector_adjustments"] == {"BIOT": {"yellow": "15-25%", "red": ">25%"}}

    def test_enriched_check_validates(self) -> None:
        """A fully enriched check dict validates successfully."""
        enriched = {
            **SAMPLE_CHECK,
            "content_type": "MANAGEMENT_DISPLAY",
            "depth": 1,
            "rationale": "Establishes risk archetype for the insured entity",
            "data_strategy": {
                "primary_source": "SEC_10K",
                "extraction_path": "company.risk_classification",
                "field_key": "risk_class",
            },
            "evaluation_criteria": {
                "type": "classification",
                "metric": "risk_class",
                "direction": "presence_is_bad",
            },
            "presentation": {
                "display_format": "narrative",
                "worksheet_label": "Primary Risk Classification",
                "section_placement": "Business Overview",
            },
            "pattern_ref": None,
        }
        cd = SignalDefinition.model_validate(enriched)
        assert cd.content_type == ContentType.MANAGEMENT_DISPLAY
        assert cd.depth == DepthLevel.DISPLAY
        assert cd.rationale == "Establishes risk archetype for the insured entity"
        assert cd.data_strategy is not None
        assert cd.data_strategy.primary_source == "SEC_10K"
        assert cd.data_strategy.field_key == "risk_class"
        assert cd.evaluation_criteria is not None
        assert cd.evaluation_criteria.type == "classification"
        assert cd.presentation is not None
        assert cd.presentation.display_format == "narrative"

    def test_all_400_checks_validate(self) -> None:
        """All 400 signals from brain/signals.json validate through SignalDefinition."""
        checks_path = Path("src/do_uw/brain/config/signals.json")
        with open(checks_path) as f:
            data = json.load(f)

        checks = data["signals"]
        assert len(checks) == 400, f"Expected 400 checks, got {len(checks)}"

        errors: list[str] = []
        for i, signal_dict in enumerate(checks):
            try:
                cd = SignalDefinition.model_validate(signal_dict)
                assert cd.id == signal_dict["id"]
            except Exception as exc:
                errors.append(f"Check {i} ({signal_dict.get('id', '?')}): {exc}")

        assert not errors, (
            f"{len(errors)} checks failed validation:\n"
            + "\n".join(errors[:10])
        )

    def test_minimal_check(self) -> None:
        """A check with only required fields validates."""
        minimal = {
            "id": "TEST.minimal",
            "name": "Minimal Test Check",
            "section": 1,
            "pillar": "P1_WHAT_WRONG",
        }
        cd = SignalDefinition.model_validate(minimal)
        assert cd.id == "TEST.minimal"
        assert cd.factors == []
        assert cd.required_data == []
        assert cd.content_type == ContentType.EVALUATIVE_CHECK
        assert cd.depth == DepthLevel.COMPUTE

    def test_content_type_from_string(self) -> None:
        """ContentType can be set from a string value."""
        check = {**SAMPLE_CHECK, "content_type": "MANAGEMENT_DISPLAY"}
        cd = SignalDefinition.model_validate(check)
        assert cd.content_type == ContentType.MANAGEMENT_DISPLAY

    def test_depth_from_int(self) -> None:
        """DepthLevel can be set from an integer."""
        check = {**SAMPLE_CHECK, "depth": 4}
        cd = SignalDefinition.model_validate(check)
        assert cd.depth == DepthLevel.HUNT
