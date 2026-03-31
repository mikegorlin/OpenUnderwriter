"""Tests for XBRL coverage validation and tag discovery.

Tests the validate_coverage() and discover_tags() functions from
xbrl_coverage.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.extract.xbrl_coverage import (
    ConceptResolution,
    CoverageReport,
    discover_tags,
    validate_coverage,
)
from do_uw.stages.extract.xbrl_mapping import XBRLConcept


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_concept(
    canonical_name: str,
    xbrl_tags: list[str],
    statement: str = "income",
    unit: str = "USD",
    expected_sign: str = "any",
) -> XBRLConcept:
    """Build a minimal XBRLConcept for testing."""
    return {
        "canonical_name": canonical_name,
        "xbrl_tags": xbrl_tags,
        "unit": unit,
        "period_type": "duration",
        "statement": statement,
        "description": canonical_name.replace("_", " ").title(),
        "expected_sign": expected_sign,
    }


def _make_facts(*concept_defs: tuple[str, str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Build a synthetic Company Facts API response."""
    us_gaap: dict[str, Any] = {}
    for concept_name, unit, entries in concept_defs:
        us_gaap[concept_name] = {"units": {unit: entries}}
    return {
        "cik": 1234567,
        "entityName": "Test Corp",
        "facts": {"us-gaap": us_gaap},
    }


def _make_entry(val: float, end: str = "2024-12-31", fy: int = 2024) -> dict[str, Any]:
    return {
        "val": val,
        "end": end,
        "fy": fy,
        "fp": "FY",
        "form": "10-K",
        "filed": "2025-02-15",
        "accn": "0001234-24-001",
    }


# ---------------------------------------------------------------------------
# validate_coverage tests
# ---------------------------------------------------------------------------


class TestValidateCoverageBasics:
    """Coverage report has correct total/resolved counts."""

    def test_returns_coverage_report(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "net_income": _make_concept("net_income", ["NetIncomeLoss"], "income"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert isinstance(report, CoverageReport)
        assert report.ticker == "TEST"

    def test_total_and_resolved_counts(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "net_income": _make_concept("net_income", ["NetIncomeLoss"], "income"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert report.total_concepts == 2
        assert report.resolved_concepts == 1

    def test_coverage_pct_computed_correctly(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "net_income": _make_concept("net_income", ["NetIncomeLoss"], "income"),
            "cost_of_revenue": _make_concept("cost_of_revenue", ["CostOfRevenue"], "income"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
            ("NetIncomeLoss", "USD", [_make_entry(20_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        # 2 of 3 concepts resolved = 66.7%
        assert report.coverage_pct == round(2 / 3 * 100, 1)


class TestCoverageByStatement:
    """Coverage breakdown reports per-statement coverage."""

    def test_by_statement_breakdown(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "net_income": _make_concept("net_income", ["NetIncomeLoss"], "income"),
            "total_assets": _make_concept("total_assets", ["Assets"], "balance_sheet"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
            ("Assets", "USD", [_make_entry(500_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert "income" in report.by_statement
        assert "balance_sheet" in report.by_statement
        # income: 1/2 = 50%, balance_sheet: 1/1 = 100%
        assert report.by_statement["income"] == 50.0
        assert report.by_statement["balance_sheet"] == 100.0


class TestCoverageAlerts:
    """Alerts generated when statement coverage < 60%."""

    def test_alert_on_low_coverage(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "net_income": _make_concept("net_income", ["NetIncomeLoss"], "income"),
            "cost_of_revenue": _make_concept("cost_of_revenue", ["CostOfRevenue"], "income"),
            "gross_profit": _make_concept("gross_profit", ["GrossProfit"], "income"),
        }
        # Only 1 of 4 income concepts resolved = 25%
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert len(report.alerts) > 0
        assert any("income" in a.lower() for a in report.alerts)

    def test_no_alert_on_high_coverage(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert len(report.alerts) == 0


class TestConceptResolutionTracking:
    """Each ConceptResolution tracks resolved_tag, tags_tried, value_count."""

    def test_resolution_details(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues", "SalesRevenueNet"], "income"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000), _make_entry(80_000, "2023-12-31", 2023)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        assert len(report.resolutions) == 1
        res = report.resolutions[0]
        assert res.concept_name == "revenue"
        assert res.resolved_tag == "Revenues"
        assert res.tags_tried == 2
        assert res.value_count == 2

    def test_unresolved_concept(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
        }
        facts = _make_facts()  # No data at all
        report = validate_coverage(facts, mapping, "TEST")
        res = report.resolutions[0]
        assert res.resolved_tag is None
        assert res.value_count == 0


class TestCoverageEmptyFacts:
    """Handles empty facts dict gracefully."""

    def test_empty_facts(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
        }
        facts: dict[str, Any] = {"facts": {"us-gaap": {}}}
        report = validate_coverage(facts, mapping, "TEST")
        assert report.total_concepts == 1
        assert report.resolved_concepts == 0
        assert report.coverage_pct == 0.0

    def test_completely_empty_facts(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
        }
        facts: dict[str, Any] = {}
        report = validate_coverage(facts, mapping, "TEST")
        assert report.resolved_concepts == 0


class TestCoverageDerivedExcluded:
    """Derived concepts (statement='derived') excluded from coverage."""

    def test_derived_concepts_excluded(self) -> None:
        mapping = {
            "revenue": _make_concept("revenue", ["Revenues"], "income"),
            "ebitda": _make_concept("ebitda", [], "derived"),
        }
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
        )
        report = validate_coverage(facts, mapping, "TEST")
        # Only 1 non-derived concept
        assert report.total_concepts == 1
        assert report.resolved_concepts == 1
        assert report.coverage_pct == 100.0


# ---------------------------------------------------------------------------
# discover_tags tests
# ---------------------------------------------------------------------------


class TestDiscoverTags:
    """discover_tags returns (tag_name, value_count, latest_value) tuples."""

    def test_returns_tags_sorted_by_count(self) -> None:
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000), _make_entry(80_000, "2023-12-31", 2023)]),
            ("Assets", "USD", [_make_entry(500_000)]),
        )
        tags = discover_tags(facts)
        assert len(tags) == 2
        # Revenues has 2 entries, Assets has 1 -- Revenues first
        assert tags[0][0] == "Revenues"
        assert tags[0][1] == 2
        assert tags[1][0] == "Assets"
        assert tags[1][1] == 1

    def test_latest_value_included(self) -> None:
        facts = _make_facts(
            ("Revenues", "USD", [
                _make_entry(80_000, "2023-12-31", 2023),
                _make_entry(100_000, "2024-12-31", 2024),
            ]),
        )
        tags = discover_tags(facts)
        assert tags[0][2] == 100_000

    def test_filter_by_unit(self) -> None:
        facts = _make_facts(
            ("Revenues", "USD", [_make_entry(100_000)]),
            ("SharesOutstanding", "shares", [_make_entry(1_000_000)]),
        )
        usd_tags = discover_tags(facts, unit_filter="USD")
        assert len(usd_tags) == 1
        assert usd_tags[0][0] == "Revenues"

        shares_tags = discover_tags(facts, unit_filter="shares")
        assert len(shares_tags) == 1
        assert shares_tags[0][0] == "SharesOutstanding"

    def test_empty_facts(self) -> None:
        facts: dict[str, Any] = {"facts": {"us-gaap": {}}}
        tags = discover_tags(facts)
        assert tags == []
