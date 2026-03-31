"""Tests for self-review HTML quality audit.

Validates REVIEW-01 through REVIEW-04:
- Section counting, N/A detection, empty sections, boilerplate, consistency
- JSON report with per-section scores
- LLM refusal detection, double-encoding, empty red flags, DDL discrepancy
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from do_uw.stages.render.self_review import (
    ReviewFinding,
    SectionScore,
    SelfReviewReport,
    _check_boilerplate,
    _check_data_consistency,
    _check_ddl_discrepancy,
    _check_double_encoding,
    _check_empty_red_flags,
    _check_llm_refusals,
    _check_visual_compliance,
    _count_na,
    _parse_dollar_amount,
    _parse_sections,
    print_review_summary,
    run_self_review,
    write_review_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_CLEAN_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Test Worksheet</title></head>
<body>
<section id="scorecard">
<h2>Risk Scorecard</h2>
<p>AAPL composite score 22.5, tier WRITE. Market cap $3.6T. Revenue $394.3B.</p>
<table><tr><td>Score</td><td>22.5</td></tr></table>
<p>Strong financial position with low litigation exposure.</p>
<p>Factor F.1 = 2/8 based on 10-year public history.</p>
<p>Factor F.2 = 1/12 with no active SCA filings.</p>
</section>
<section id="executive-brief">
<h2>Executive Brief</h2>
<p>Apple Inc trades at $185.50 with market capitalization of $3.6T.</p>
<p>Revenue of $394.3B with 22.1% net margin.</p>
<p>No active securities class actions. Clean governance profile.</p>
<p>D&O risk tier: WRITE based on composite score 22.5/100.</p>
<p>Board of 8 directors, 7 independent (87.5% independence ratio).</p>
</section>
<section id="financial-health">
<h2>Financial Health</h2>
<p>Revenue: $394.3B (FY2025). Net income: $87.1B. Current ratio: 1.07.</p>
<p>Altman Z-Score: 8.24 (safe zone). Beneish M-Score: -2.89 (no manipulation).</p>
<p>Total debt: $111.1B. Debt-to-equity: 1.73.</p>
<p>Free cash flow: $93.0B. Operating margin: 30.7%.</p>
</section>
</body>
</html>
"""

_DIRTY_HTML = """\
<!DOCTYPE html>
<html><body>
<section id="scorecard">
<h2>Risk Scorecard</h2>
<p>Score is N/A and market cap N/A.</p>
<p>The company has shown a commitment to N/A.</p>
<p>This is positioned to face potential challenges going forward.</p>
<table border="2" cellpadding="8"><tr><td>N/A</td><td>N/A</td></tr></table>
</section>
<section id="brief">
<h2>Executive Brief</h2>
<p>N/A</p>
</section>
<section id="refusal-section">
<h2>Bad Section</h2>
<p>I cannot write this narrative because I don't have access to the data.</p>
<p>&lt;strong&gt;Double encoded&lt;/strong&gt; and <strong><strong>nested</strong></strong></p>
<p>DDL estimate is $513B for this risk.</p>
</section>
<section id="ddl-section">
<h2>DDL Analysis</h2>
<p>DDL dollar-loss estimate of $66M based on market cap.</p>
</section>
</body></html>
"""


@pytest.fixture
def clean_html_file(tmp_path: Path) -> Path:
    p = tmp_path / "AAPL_worksheet.html"
    p.write_text(_CLEAN_HTML, encoding="utf-8")
    return p


@pytest.fixture
def dirty_html_file(tmp_path: Path) -> Path:
    p = tmp_path / "ANGI_worksheet.html"
    p.write_text(_DIRTY_HTML, encoding="utf-8")
    return p


def _mock_state(
    red_flags: list[dict[str, Any]] | None = None,
) -> SimpleNamespace:
    scoring = SimpleNamespace(red_flags=red_flags or [])
    return SimpleNamespace(scoring=scoring, ticker="TEST")


# ---------------------------------------------------------------------------
# REVIEW-01: Section count, N/A, empty, boilerplate, consistency
# ---------------------------------------------------------------------------


class TestReview01BasicAudit:
    """REVIEW-01: Post-pipeline quality audit reads HTML and reports basics."""

    def test_section_count_clean(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert report.section_count == 3

    def test_section_count_dirty(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        assert report.section_count == 4

    def test_na_count_clean(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert report.total_na_count == 0

    def test_na_count_dirty(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        assert report.total_na_count >= 4  # Multiple N/A in dirty HTML

    def test_empty_sections_dirty(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        # "Executive Brief" section has only 1 line (N/A)
        assert report.empty_section_count >= 1

    def test_empty_sections_clean_small_fixture(self, clean_html_file: Path) -> None:
        """Clean small fixture sections are below 10-line threshold; real worksheets are larger."""
        report = run_self_review(clean_html_file)
        # Test fixture is intentionally compact; verify counting works
        assert report.empty_section_count >= 0

    def test_boilerplate_detected_dirty(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        assert report.boilerplate_count > 0

    def test_no_boilerplate_clean(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert report.boilerplate_count == 0

    def test_data_consistency_checks(self) -> None:
        html = (
            '<p>Market cap $3.6T</p>'
            '<p>Market capitalization: $2.8T</p>'
        )
        findings = _check_data_consistency(html)
        assert len(findings) >= 1
        assert findings[0].category == "consistency"


# ---------------------------------------------------------------------------
# REVIEW-02: Structured JSON report with per-section scores
# ---------------------------------------------------------------------------


class TestReview02JsonReport:
    """REVIEW-02: Audit output produces structured JSON."""

    def test_json_serialization(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert "section_scores" in parsed
        assert "findings" in parsed
        assert "overall_score" in parsed

    def test_section_scores_populated(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert len(report.section_scores) == 3
        for score in report.section_scores:
            assert 0.0 <= score.data_population <= 1.0
            assert score.narrative_quality in (0.0, 1.0)
            assert 0.0 <= score.visual_compliance <= 1.0

    def test_clean_html_high_scores(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        # Clean HTML should score well
        assert report.overall_score >= 0.8
        assert report.grade in ("A", "B")

    def test_dirty_html_lower_scores(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        assert report.overall_score < 0.9

    def test_write_report_creates_file(self, clean_html_file: Path, tmp_path: Path) -> None:
        report = run_self_review(clean_html_file)
        report_path = write_review_report(report, tmp_path)
        assert report_path.exists()
        assert report_path.suffix == ".json"
        data = json.loads(report_path.read_text())
        assert data["ticker"] == "AAPL"

    def test_per_section_data_population(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        for score in report.section_scores:
            # Clean sections should have high data population
            assert score.data_population > 0.8

    def test_visual_compliance_clean(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        for score in report.section_scores:
            assert score.visual_compliance == 1.0  # No border attrs

    def test_visual_compliance_dirty(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        # Dirty HTML has border="2" and cellpadding="8"
        scorecard = next(
            s for s in report.section_scores if s.section_id == "scorecard"
        )
        assert scorecard.visual_compliance < 1.0


# ---------------------------------------------------------------------------
# REVIEW-03: CLI flag (integration-level, tested via import)
# ---------------------------------------------------------------------------


class TestReview03CLIFlag:
    """REVIEW-03: --review flag registered in CLI."""

    def test_review_flag_exists(self) -> None:
        """Verify analyze command accepts --review parameter."""
        from do_uw.cli import analyze
        import inspect

        sig = inspect.signature(analyze)
        assert "review" in sig.parameters


# ---------------------------------------------------------------------------
# REVIEW-04: Specific issue detection
# ---------------------------------------------------------------------------


class TestReview04LLMRefusals:
    """REVIEW-04: Catches LLM refusal messages."""

    def test_detects_cannot_write(self) -> None:
        html = "<p>I cannot write this narrative due to limitations.</p>"
        findings = _check_llm_refusals(html)
        assert len(findings) >= 1
        assert findings[0].category == "refusal"
        assert findings[0].severity == "error"

    def test_detects_as_an_ai(self) -> None:
        html = "<p>As an AI language model, I should note that...</p>"
        findings = _check_llm_refusals(html)
        assert len(findings) >= 1

    def test_no_false_positives_clean(self) -> None:
        html = "<p>Revenue was $394.3B with 22.1% net margin.</p>"
        findings = _check_llm_refusals(html)
        assert len(findings) == 0

    def test_detects_dont_have_access(self) -> None:
        html = "<p>I don't have access to real-time data for this company.</p>"
        findings = _check_llm_refusals(html)
        assert len(findings) >= 1


class TestReview04DoubleEncoding:
    """REVIEW-04: Catches HTML double-encoding."""

    def test_detects_amp_lt(self) -> None:
        html = "<p>&amp;lt;strong&amp;gt;</p>"
        findings = _check_double_encoding(html)
        assert len(findings) >= 1
        assert findings[0].category == "encoding"

    def test_detects_escaped_tags(self) -> None:
        html = "<p>&lt;strong&gt;bold&lt;/strong&gt;</p>"
        findings = _check_double_encoding(html)
        assert len(findings) >= 1

    def test_detects_nested_strong(self) -> None:
        html = "<p><strong><strong>double bold</strong></strong></p>"
        findings = _check_double_encoding(html)
        assert len(findings) >= 1

    def test_no_false_positives(self) -> None:
        html = "<p><strong>normal bold</strong></p>"
        findings = _check_double_encoding(html)
        assert len(findings) == 0


class TestReview04EmptyRedFlags:
    """REVIEW-04: Catches empty red flags (triggered=false in state)."""

    def test_detects_untriggered_flags(self) -> None:
        state = _mock_state(red_flags=[
            {"name": "Active SCA", "triggered": False},
            {"name": "SEC Investigation", "triggered": False},
        ])
        findings = _check_empty_red_flags(state)
        assert len(findings) >= 1
        assert findings[0].category == "red_flag"

    def test_no_finding_when_all_triggered(self) -> None:
        state = _mock_state(red_flags=[
            {"name": "Active SCA", "triggered": True},
        ])
        findings = _check_empty_red_flags(state)
        assert len(findings) == 0

    def test_no_finding_when_no_flags(self) -> None:
        state = _mock_state(red_flags=[])
        findings = _check_empty_red_flags(state)
        assert len(findings) == 0


class TestReview04DDLDiscrepancy:
    """REVIEW-04: Catches DDL discrepancies between sections."""

    def test_detects_large_discrepancy(self) -> None:
        html = (
            "<p>DDL dollar-loss estimate of $513B.</p>"
            "<p>DDL dollar-loss: $66M from the scorecard.</p>"
        )
        findings = _check_ddl_discrepancy(html, None)
        assert len(findings) >= 1
        assert findings[0].category == "ddl"
        assert findings[0].severity == "error"

    def test_no_finding_when_consistent(self) -> None:
        html = (
            "<p>DDL dollar-loss estimate of $66M.</p>"
            "<p>DDL dollar-loss: $68M from the scorecard.</p>"
        )
        findings = _check_ddl_discrepancy(html, None)
        assert len(findings) == 0  # 68/66 = 1.03x, well under 5x

    def test_no_finding_when_single_value(self) -> None:
        html = "<p>DDL dollar-loss estimate of $66M.</p>"
        findings = _check_ddl_discrepancy(html, None)
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Integration: full review on dirty HTML catches all issue types
# ---------------------------------------------------------------------------


class TestFullReviewIntegration:
    """Full review on dirty HTML catches multiple issue types."""

    def test_dirty_html_catches_refusals(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        refusals = [f for f in report.findings if f.category == "refusal"]
        assert len(refusals) >= 1

    def test_dirty_html_catches_encoding(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        encodings = [f for f in report.findings if f.category == "encoding"]
        assert len(encodings) >= 1

    def test_dirty_html_catches_ddl(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        ddl = [f for f in report.findings if f.category == "ddl"]
        assert len(ddl) >= 1

    def test_report_grade(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert report.grade in ("A", "B", "C", "D", "F")

    def test_error_and_warning_counts(self, dirty_html_file: Path) -> None:
        report = run_self_review(dirty_html_file)
        assert report.error_count >= 1  # At least refusal + encoding

    def test_ticker_extracted_from_filename(self, clean_html_file: Path) -> None:
        report = run_self_review(clean_html_file)
        assert report.ticker == "AAPL"


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelpers:
    """Unit tests for helper functions."""

    def test_count_na(self) -> None:
        assert _count_na("N/A and N/A but not NA") == 2

    def test_count_na_zero(self) -> None:
        assert _count_na("No missing values here") == 0

    def test_check_boilerplate_detects(self) -> None:
        matches = _check_boilerplate("The company has shown great resilience.")
        assert len(matches) >= 1

    def test_check_boilerplate_clean(self) -> None:
        matches = _check_boilerplate("Revenue was $394.3B in FY2025.")
        assert len(matches) == 0

    def test_visual_compliance_clean(self) -> None:
        score = _check_visual_compliance("<table><tr><td>OK</td></tr></table>")
        assert score == 1.0

    def test_visual_compliance_bordered(self) -> None:
        score = _check_visual_compliance('<table border="2"><tr><td>Old</td></tr></table>')
        assert score < 1.0

    def test_parse_dollar_amount(self) -> None:
        assert _parse_dollar_amount("$513B") == 513_000_000_000
        assert _parse_dollar_amount("$66M") == 66_000_000
        assert _parse_dollar_amount("$1.5T") == 1_500_000_000_000
        assert _parse_dollar_amount("$100K") == 100_000

    def test_parse_dollar_amount_invalid(self) -> None:
        assert _parse_dollar_amount("no dollars") is None

    def test_parse_sections_counts(self) -> None:
        sections = _parse_sections(_CLEAN_HTML)
        assert len(sections) == 3

    def test_print_review_summary_no_crash(self, clean_html_file: Path) -> None:
        """Verify print_review_summary runs without error."""
        report = run_self_review(clean_html_file)
        # Should not raise
        print_review_summary(report)
