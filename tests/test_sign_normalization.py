"""Tests for XBRL sign normalization.

Tests that normalize_sign() corrects wrong-sign values based on expected_sign
config, and that sign normalization is integrated into financial statement
extraction.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.xbrl_mapping import normalize_sign


# ---------------------------------------------------------------------------
# Unit tests for normalize_sign
# ---------------------------------------------------------------------------


class TestNormalizeSignPositive:
    """Test expected_sign='positive' normalization."""

    def test_positive_flips_negative_to_positive(self) -> None:
        value, changed = normalize_sign(-500.0, "positive", "revenue")
        assert value == 500.0
        assert changed is True

    def test_positive_keeps_positive_unchanged(self) -> None:
        value, changed = normalize_sign(500.0, "positive", "revenue")
        assert value == 500.0
        assert changed is False


class TestNormalizeSignNegative:
    """Test expected_sign='negative' normalization."""

    def test_negative_flips_positive_to_negative(self) -> None:
        value, changed = normalize_sign(500.0, "negative", "cost_of_revenue")
        assert value == -500.0
        assert changed is True

    def test_negative_keeps_negative_unchanged(self) -> None:
        value, changed = normalize_sign(-500.0, "negative", "cost_of_revenue")
        assert value == -500.0
        assert changed is False


class TestNormalizeSignAny:
    """Test expected_sign='any' -- no normalization."""

    def test_any_keeps_negative(self) -> None:
        value, changed = normalize_sign(-500.0, "any", "net_income")
        assert value == -500.0
        assert changed is False

    def test_any_keeps_positive(self) -> None:
        value, changed = normalize_sign(500.0, "any", "net_income")
        assert value == 500.0
        assert changed is False


class TestNormalizeSignZero:
    """Zero values always return (0, False) regardless of expected_sign."""

    def test_zero_positive(self) -> None:
        value, changed = normalize_sign(0.0, "positive", "revenue")
        assert value == 0.0
        assert changed is False

    def test_zero_negative(self) -> None:
        value, changed = normalize_sign(0.0, "negative", "cost_of_revenue")
        assert value == 0.0
        assert changed is False

    def test_zero_any(self) -> None:
        value, changed = normalize_sign(0.0, "any", "net_income")
        assert value == 0.0
        assert changed is False


class TestNormalizeSignLogging:
    """Normalization events are logged at INFO level."""

    def test_normalization_logged(self, caplog: Any) -> None:
        with caplog.at_level(logging.INFO, logger="do_uw.stages.extract.xbrl_mapping"):
            normalize_sign(-500.0, "positive", "revenue")

        assert any(
            "Sign normalization" in record.message and "revenue" in record.message
            for record in caplog.records
        ), f"Expected sign normalization log for 'revenue', got: {[r.message for r in caplog.records]}"

    def test_no_change_not_logged(self, caplog: Any) -> None:
        with caplog.at_level(logging.INFO, logger="do_uw.stages.extract.xbrl_mapping"):
            normalize_sign(500.0, "positive", "revenue")

        assert not any(
            "Sign normalization" in record.message
            for record in caplog.records
        ), "Should not log when no normalization needed"


# ---------------------------------------------------------------------------
# Integration: sign normalization in financial_statements extraction
# ---------------------------------------------------------------------------


def _make_entry(
    val: float,
    end: str,
    fy: int,
    form: str = "10-K",
    filed: str = "2025-02-15",
    fp: str = "FY",
    accn: str = "0001234-24-001",
) -> dict[str, Any]:
    """Build a single XBRL fact entry."""
    return {
        "val": val,
        "end": end,
        "fy": fy,
        "fp": fp,
        "form": form,
        "filed": filed,
        "accn": accn,
    }


def _make_company_facts(
    *concept_defs: tuple[str, str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build a synthetic Company Facts API response."""
    us_gaap: dict[str, Any] = {}
    for concept_name, unit, entries in concept_defs:
        us_gaap[concept_name] = {"units": {unit: entries}}
    return {
        "cik": 1234567,
        "entityName": "Test Corp",
        "facts": {"us-gaap": us_gaap},
    }


def _make_state(facts: dict[str, Any]) -> AnalysisState:
    """Build a minimal AnalysisState with Company Facts data."""
    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(
            identity=CompanyIdentity(
                ticker="TEST",
                cik=SourcedValue[str](
                    value="0001234567",
                    source="SEC EDGAR",
                    confidence=Confidence.HIGH,
                    as_of=datetime(2024, 1, 1, tzinfo=UTC),
                ),
            )
        ),
        acquired_data=AcquiredData(
            filings={"company_facts": facts},
        ),
    )


class TestSignNormalizationIntegration:
    """Sign normalization applied during financial statement extraction."""

    def test_negative_revenue_corrected_in_extraction(self) -> None:
        """Revenue reported as negative should be flipped to positive."""
        from do_uw.stages.extract.financial_statements import (
            extract_financial_statements,
        )

        # Revenue is expected_sign=positive. Report it as negative.
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(-100_000_000, "2024-12-31", 2024),
                _make_entry(-80_000_000, "2023-12-31", 2023),
            ]),
        )
        state = _make_state(facts)
        statements, reports = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None

        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert len(revenue_items) == 1

        sv = revenue_items[0].values.get("FY2024")
        assert sv is not None
        # Should have been flipped to positive.
        assert sv.value == 100_000_000

        # Normalization should be noted in warnings.
        income_report = reports[0]
        assert any(
            "normalization" in w.lower() or "sign" in w.lower()
            for w in income_report.warnings
        ), f"Expected normalization warning, got: {income_report.warnings}"
