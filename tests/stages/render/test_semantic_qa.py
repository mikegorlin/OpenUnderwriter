"""Tests for semantic QA validation module.

Unit tests for financial value parsing and state extraction.
Integration tests against real pipeline output (skip if unavailable).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.stages.render.semantic_qa import (
    _extract_html_board_size,
    _extract_html_revenue,
    _extract_html_score,
    _extract_html_tier,
    _extract_state_board_size,
    _extract_state_overall_score,
    _extract_state_revenue,
    _extract_state_tier,
    _parse_financial_value,
    validate_board_size,
    validate_output,
    validate_overall_score,
    validate_revenue,
    validate_tier,
)

# ---------------------------------------------------------------------------
# Unit tests: _parse_financial_value
# ---------------------------------------------------------------------------


class TestParseFinancialValue:
    """Tests for parsing formatted financial strings back to numbers."""

    def test_parse_billions(self) -> None:
        assert _parse_financial_value("$1.2B") == pytest.approx(1.2e9)

    def test_parse_billions_no_dollar(self) -> None:
        assert _parse_financial_value("1.2B") == pytest.approx(1.2e9)

    def test_parse_millions(self) -> None:
        assert _parse_financial_value("$450M") == pytest.approx(4.5e8)

    def test_parse_millions_decimal(self) -> None:
        assert _parse_financial_value("$450.5M") == pytest.approx(4.505e8)

    def test_parse_thousands(self) -> None:
        assert _parse_financial_value("$12.5K") == pytest.approx(12500)

    def test_parse_trillions(self) -> None:
        assert _parse_financial_value("$1.5T") == pytest.approx(1.5e12)

    def test_parse_plain(self) -> None:
        assert _parse_financial_value("1234567") == pytest.approx(1234567)

    def test_parse_commas(self) -> None:
        assert _parse_financial_value("$1,234,567") == pytest.approx(1234567)

    def test_parse_negative_parens(self) -> None:
        assert _parse_financial_value("($1.2B)") == pytest.approx(-1.2e9)

    def test_parse_negative_parens_millions(self) -> None:
        assert _parse_financial_value("($450M)") == pytest.approx(-4.5e8)

    def test_parse_decimal(self) -> None:
        assert _parse_financial_value("83.80") == pytest.approx(83.80)

    def test_parse_none_on_na(self) -> None:
        assert _parse_financial_value("N/A") is None

    def test_parse_none_on_empty(self) -> None:
        assert _parse_financial_value("") is None

    def test_parse_none_on_dash(self) -> None:
        assert _parse_financial_value("—") is None

    def test_parse_none_on_none(self) -> None:
        assert _parse_financial_value(None) is None  # type: ignore[arg-type]

    def test_parse_none_on_not_available(self) -> None:
        assert _parse_financial_value("Not Available") is None


# ---------------------------------------------------------------------------
# Unit tests: state extraction
# ---------------------------------------------------------------------------


def _mock_state_with_revenue(revenue: float = 7_372_644_000.0) -> dict:
    """Create a mock state dict with revenue data."""
    return {
        "extracted": {
            "financials": {
                "statements": {
                    "income_statement": {
                        "statement_type": "income_statement",
                        "line_items": [
                            {
                                "label": "Total revenue / net sales",
                                "values": {
                                    "FY2025": {
                                        "value": revenue,
                                        "source": "10-K 2025",
                                        "confidence": "HIGH",
                                    },
                                    "FY2024": {
                                        "value": revenue * 0.95,
                                        "source": "10-K 2024",
                                        "confidence": "HIGH",
                                    },
                                },
                            },
                            {
                                "label": "Cost of revenue / COGS",
                                "values": {
                                    "FY2025": {"value": 4_300_000_000.0},
                                },
                            },
                        ],
                    }
                }
            }
        }
    }


def _mock_state_with_board(size: int = 12) -> dict:
    """Create a mock state dict with board data."""
    return {
        "extracted": {
            "governance": {
                "board": {
                    "size": {
                        "value": size,
                        "source": "DEF 14A (LLM)",
                        "confidence": "HIGH",
                    }
                }
            }
        }
    }


def _mock_state_with_score(score: float = 83.8, tier: str = "WANT") -> dict:
    """Create a mock state dict with scoring data."""
    return {
        "scoring": {
            "composite_score": score,
            "quality_score": score,
            "tier": {
                "tier": tier,
                "score_range_low": 71,
                "score_range_high": 85,
            },
        }
    }


class TestExtractStateRevenue:
    """Tests for extracting revenue from state dict."""

    def test_extract_revenue(self) -> None:
        state = _mock_state_with_revenue(7_372_644_000.0)
        vals = _extract_state_revenue(state)
        assert len(vals) == 2
        assert vals[0] == pytest.approx(7_372_644_000.0)

    def test_extract_revenue_missing(self) -> None:
        assert _extract_state_revenue({}) == []

    def test_extract_revenue_no_income_statement(self) -> None:
        state = {"extracted": {"financials": {"statements": {}}}}
        assert _extract_state_revenue(state) == []


class TestExtractStateBoardSize:
    """Tests for extracting board size from state dict."""

    def test_extract_board_size(self) -> None:
        state = _mock_state_with_board(12)
        assert _extract_state_board_size(state) == 12

    def test_extract_board_size_plain_int(self) -> None:
        state = {"extracted": {"governance": {"board": {"size": 10}}}}
        assert _extract_state_board_size(state) == 10

    def test_extract_board_size_missing(self) -> None:
        assert _extract_state_board_size({}) is None


class TestExtractStateScore:
    """Tests for extracting overall score from state dict."""

    def test_extract_overall_score(self) -> None:
        state = _mock_state_with_score(83.8)
        assert _extract_state_overall_score(state) == pytest.approx(83.8)

    def test_extract_score_missing(self) -> None:
        assert _extract_state_overall_score({}) is None


class TestExtractStateTier:
    """Tests for extracting tier from state dict."""

    def test_extract_tier_dict(self) -> None:
        state = _mock_state_with_score(83.8, "WANT")
        assert _extract_state_tier(state) == "WANT"

    def test_extract_tier_string(self) -> None:
        state = {"scoring": {"tier": "WIN"}}
        assert _extract_state_tier(state) == "WIN"

    def test_extract_tier_missing(self) -> None:
        assert _extract_state_tier({}) is None


# ---------------------------------------------------------------------------
# Unit tests: HTML extraction with mock HTML
# ---------------------------------------------------------------------------


def _make_simple_html(
    revenue: str = "$7.3B",
    board_size: str = "12",
    score: float = 83.8,
    tier: str = "WANT",
) -> str:
    """Create minimal HTML mimicking real worksheet structure."""
    return f"""
    <html><body>
    <table>
        <tr><td>Total revenue / net sales</td><td>{revenue}</td></tr>
    </table>
    <table>
        <tr class="bg-bg-alt"><th>Board Size</th><td>{board_size}</td></tr>
    </table>
    <p><strong>composite quality score of {score} and:</strong></p>
    <span class="badge-tier bg-blue-600 text-white tracking-wide">{tier}</span>
    </body></html>
    """


class TestExtractHtmlValues:
    """Tests for extracting values from HTML."""

    def test_extract_html_revenue(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(_make_simple_html(), "lxml")
        assert _extract_html_revenue(soup) == pytest.approx(7.3e9)

    def test_extract_html_board_size(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(_make_simple_html(), "lxml")
        assert _extract_html_board_size(soup) == 12

    def test_extract_html_score(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(_make_simple_html(), "lxml")
        assert _extract_html_score(soup) == pytest.approx(83.8)

    def test_extract_html_tier(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(_make_simple_html(), "lxml")
        assert _extract_html_tier(soup) == "WANT"


# ---------------------------------------------------------------------------
# Unit tests: validate_* functions with mock data
# ---------------------------------------------------------------------------


class TestValidationFunctions:
    """Tests for validation functions using mock state + HTML."""

    def test_revenue_pass(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_revenue(7_300_000_000.0)
        soup = BeautifulSoup(_make_simple_html(revenue="$7.3B"), "lxml")
        passed, msg = validate_revenue(state, soup)
        assert passed
        assert "PASS" in msg

    def test_revenue_skip_when_missing(self) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(_make_simple_html(), "lxml")
        passed, msg = validate_revenue({}, soup)
        assert passed
        assert "SKIP" in msg

    def test_board_size_pass(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_board(12)
        soup = BeautifulSoup(_make_simple_html(board_size="12"), "lxml")
        passed, msg = validate_board_size(state, soup)
        assert passed

    def test_board_size_fail(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_board(12)
        soup = BeautifulSoup(_make_simple_html(board_size="10"), "lxml")
        passed, msg = validate_board_size(state, soup)
        assert not passed
        assert "mismatch" in msg.lower()

    def test_overall_score_pass(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_score(83.8)
        soup = BeautifulSoup(_make_simple_html(score=83.8), "lxml")
        passed, msg = validate_overall_score(state, soup)
        assert passed

    def test_overall_score_within_tolerance(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_score(83.85)
        soup = BeautifulSoup(_make_simple_html(score=83.8), "lxml")
        passed, msg = validate_overall_score(state, soup)
        assert passed  # 0.05 < 0.1 tolerance

    def test_tier_pass(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_score(83.8, "WANT")
        soup = BeautifulSoup(_make_simple_html(tier="WANT"), "lxml")
        passed, msg = validate_tier(state, soup)
        assert passed

    def test_tier_fail(self) -> None:
        from bs4 import BeautifulSoup

        state = _mock_state_with_score(83.8, "WANT")
        soup = BeautifulSoup(_make_simple_html(tier="WIN"), "lxml")
        passed, msg = validate_tier(state, soup)
        assert not passed


# ---------------------------------------------------------------------------
# Integration tests: real pipeline output
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"

# Discover available output directories
_OUTPUT_DIRS = [
    d
    for d in sorted(OUTPUT_DIR.iterdir())
    if d.is_dir()
    and (d / "state.json").exists()
    and list(d.glob("*_worksheet.html"))
]


@pytest.mark.skipif(
    not _OUTPUT_DIRS,
    reason="No pipeline output available for semantic QA integration test",
)
class TestSemanticQAOnRealOutput:
    """Run semantic QA against actual pipeline output."""

    @pytest.fixture(params=[d.name for d in _OUTPUT_DIRS])
    def output_pair(self, request: pytest.FixtureRequest) -> tuple[Path, Path]:
        """Return (state_path, html_path) for a pipeline output directory."""
        output_dir = OUTPUT_DIR / request.param
        state_path = output_dir / "state.json"
        html_files = list(output_dir.glob("*_worksheet.html"))
        return state_path, html_files[0]

    def test_revenue_matches_xbrl(
        self, output_pair: tuple[Path, Path]
    ) -> None:
        state_path, html_path = output_pair
        results = validate_output(state_path, html_path)
        for name, passed, msg in results:
            if name == "revenue":
                assert passed, f"Revenue QA failed for {state_path.parent.name}: {msg}"

    def test_board_size_matches_extraction(
        self, output_pair: tuple[Path, Path]
    ) -> None:
        state_path, html_path = output_pair
        results = validate_output(state_path, html_path)
        for name, passed, msg in results:
            if name == "board_size":
                assert passed, f"Board size QA failed for {state_path.parent.name}: {msg}"

    def test_overall_score_matches_state(
        self, output_pair: tuple[Path, Path]
    ) -> None:
        state_path, html_path = output_pair
        results = validate_output(state_path, html_path)
        for name, passed, msg in results:
            if name == "overall_score":
                assert passed, f"Score QA failed for {state_path.parent.name}: {msg}"

    def test_tier_matches_state(
        self, output_pair: tuple[Path, Path]
    ) -> None:
        state_path, html_path = output_pair
        results = validate_output(state_path, html_path)
        for name, passed, msg in results:
            if name == "tier":
                assert passed, f"Tier QA failed for {state_path.parent.name}: {msg}"

    def test_all_checks_pass(
        self, output_pair: tuple[Path, Path]
    ) -> None:
        state_path, html_path = output_pair
        results = validate_output(state_path, html_path)
        failures = [(n, m) for n, p, m in results if not p]
        assert not failures, (
            f"Semantic QA failures for {state_path.parent.name}: {failures}"
        )
