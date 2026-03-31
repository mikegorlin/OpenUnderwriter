"""Tests for cross-section consistency checker.

Verifies that the ConsistencyChecker detects when the same fact
(revenue, CEO, exchange, market cap) appears with different values
in different sections of the rendered HTML.
"""

from __future__ import annotations

import pytest

from do_uw.validation.consistency_checker import (
    ConsistencyChecker,
    ConsistencyError,
    ConsistencyReport,
    check_cross_section_consistency,
)


# ---------------------------------------------------------------------------
# Helpers: minimal HTML fragments
# ---------------------------------------------------------------------------

def _wrap_html(*sections: str) -> str:
    """Wrap section HTML into a minimal valid page."""
    body = "\n".join(sections)
    return f"<html><body>{body}</body></html>"


def _section(name: str, content: str) -> str:
    return f'<section id="{name}">{content}</section>'


def _kv_row(label: str, value: str) -> str:
    return f"<tr><td>{label}</td><td>{value}</td></tr>"


# ---------------------------------------------------------------------------
# Test 1: Revenue inconsistency detected
# ---------------------------------------------------------------------------

class TestRevenueInconsistency:
    """Revenue $3.05B in one section, $2.98B in another -> 1 inconsistency."""

    def test_different_revenue_values_detected(self) -> None:
        html = _wrap_html(
            _section("key-stats", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("financials", f"<table>{_kv_row('Revenue', '$2.98B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        assert len(report.inconsistencies) >= 1
        rev_issues = [i for i in report.inconsistencies if i.fact_name == "revenue"]
        assert len(rev_issues) >= 1


# ---------------------------------------------------------------------------
# Test 2: CEO consistent -> zero inconsistencies
# ---------------------------------------------------------------------------

class TestCEOConsistent:
    """CEO 'Tim Cook' in both sections -> zero inconsistencies for CEO."""

    def test_same_ceo_no_inconsistency(self) -> None:
        html = _wrap_html(
            _section("executive-summary", "<p>CEO: Tim Cook</p>"),
            _section("governance", "<p>CEO: Tim Cook</p>"),
        )
        canonical = {"ceo_name": "Tim Cook"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        ceo_issues = [i for i in report.inconsistencies if i.fact_name == "ceo_name"]
        assert len(ceo_issues) == 0


# ---------------------------------------------------------------------------
# Test 3: Exchange case-insensitive -> zero inconsistencies
# ---------------------------------------------------------------------------

class TestExchangeCaseInsensitive:
    """NASDAQ vs Nasdaq (case-insensitive) -> zero inconsistencies."""

    def test_case_insensitive_exchange(self) -> None:
        html = _wrap_html(
            _section("cover", f"<table>{_kv_row('Exchange', 'NASDAQ')}</table>"),
            _section("key-stats", f"<table>{_kv_row('Exchange', 'Nasdaq')}</table>"),
        )
        canonical = {"exchange": "NASDAQ"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        exch_issues = [i for i in report.inconsistencies if i.fact_name == "exchange"]
        assert len(exch_issues) == 0


# ---------------------------------------------------------------------------
# Test 4: report_only modes
# ---------------------------------------------------------------------------

class TestReportOnlyMode:
    """report_only=True returns report; report_only=False raises ConsistencyError."""

    def test_report_only_true_no_exception(self) -> None:
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("b", f"<table>{_kv_row('Revenue', '$2.98B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html, report_only=True)
        assert isinstance(report, ConsistencyReport)
        assert len(report.inconsistencies) >= 1

    def test_report_only_false_raises(self) -> None:
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("b", f"<table>{_kv_row('Revenue', '$2.98B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        with pytest.raises(ConsistencyError):
            checker.check(html, report_only=False)

    def test_report_only_false_no_issues_no_exception(self) -> None:
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("b", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html, report_only=False)
        assert len(report.inconsistencies) == 0


# ---------------------------------------------------------------------------
# Test 5: Convenience function works with state dict
# ---------------------------------------------------------------------------

class TestConvenienceFunction:
    """check_cross_section_consistency builds canonical from state and runs."""

    def test_check_cross_section_consistency_returns_report(self) -> None:
        html = _wrap_html(
            _section("key-stats", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
        )
        # Minimal state dict with revenue
        state_dict = {
            "company": {
                "identity": {"legal_name": {"value": "Apple Inc"}},
                "exchange": {"value": "NASDAQ"},
            },
            "extracted": {
                "financials": {
                    "statements": {
                        "income_statement": {
                            "line_items": [
                                {
                                    "label": "Total revenue / net sales",
                                    "values": {"FY2025": {"value": 3050000000}},
                                }
                            ]
                        }
                    }
                }
            },
        }
        report = check_cross_section_consistency(state_dict, html, report_only=True)
        assert isinstance(report, ConsistencyReport)


# ---------------------------------------------------------------------------
# Test: Financial tolerance (within 1%)
# ---------------------------------------------------------------------------

class TestFinancialTolerance:
    """Values within 1% should NOT be flagged as inconsistent."""

    def test_within_tolerance_not_flagged(self) -> None:
        # $3.05B and $3.04B differ by ~0.3% -> consistent
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("b", f"<table>{_kv_row('Revenue', '$3.04B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        rev_issues = [i for i in report.inconsistencies if i.fact_name == "revenue"]
        assert len(rev_issues) == 0

    def test_beyond_tolerance_flagged(self) -> None:
        # $3.05B and $2.98B differ by ~2.3% -> inconsistent
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
            _section("b", f"<table>{_kv_row('Revenue', '$2.98B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        rev_issues = [i for i in report.inconsistencies if i.fact_name == "revenue"]
        assert len(rev_issues) >= 1


# ---------------------------------------------------------------------------
# Test: QA integration
# ---------------------------------------------------------------------------

class TestQAIntegration:
    """Report exposes qa_checks for integration with QA pipeline."""

    def test_report_has_qa_checks(self) -> None:
        html = _wrap_html(
            _section("a", f"<table>{_kv_row('Revenue', '$3.05B')}</table>"),
        )
        canonical = {"revenue": "$3.05B"}
        checker = ConsistencyChecker(canonical_values=canonical)
        report = checker.check(html)
        assert hasattr(report, "qa_checks")
        assert isinstance(report.qa_checks, list)
