"""Tests for accounting-style number formatters (Plan 40-03).

Verifies format_currency_accounting, format_adaptive, format_yoy_html,
and format_na produce correct HTML output for financial display.
"""

from __future__ import annotations

from do_uw.stages.render.formatters import (
    format_adaptive,
    format_currency_accounting,
    format_na,
    format_yoy_html,
)


class TestFormatCurrencyAccounting:
    """Tests for accounting-style currency formatting."""

    def test_negative_red_parentheses(self) -> None:
        """Negative values show as red parentheses: ($1,234)."""
        result = format_currency_accounting(-1234)
        assert 'text-risk-red' in result
        assert '($1,234)' in result

    def test_positive_no_color(self) -> None:
        """Positive values show as normal currency: $1,234."""
        result = format_currency_accounting(1234)
        assert result == "$1,234"
        assert "text-risk-red" not in result

    def test_compact_large_number(self) -> None:
        """Large numbers in compact mode: $394.3B."""
        result = format_currency_accounting(394_328_000_000, compact=True)
        assert result == "$394.3B"

    def test_compact_negative(self) -> None:
        """Compact negative: ($345.0M)."""
        result = format_currency_accounting(-345_000_000, compact=True)
        assert 'text-risk-red' in result
        assert "($345.0M)" in result

    def test_none_returns_na(self) -> None:
        """None returns gray italic N/A HTML."""
        result = format_currency_accounting(None)
        assert "N/A" in result
        assert "text-gray-400" in result
        assert "italic" in result

    def test_zero(self) -> None:
        """Zero returns $0."""
        result = format_currency_accounting(0)
        assert result == "$0"

    def test_compact_millions(self) -> None:
        """Compact millions: $1.2M."""
        result = format_currency_accounting(1_200_000, compact=True)
        assert result == "$1.2M"


class TestFormatYoyHtml:
    """Tests for YoY change HTML formatting with colored arrows."""

    def test_positive_green_up_arrow(self) -> None:
        """Positive change shows green up-triangle."""
        result = format_yoy_html(12.3)
        assert "&#9650;" in result
        assert "+12.3%" in result
        assert "text-risk-green" in result

    def test_negative_red_down_arrow(self) -> None:
        """Negative change shows red down-triangle."""
        result = format_yoy_html(-5.1)
        assert "&#9660;" in result
        assert "-5.1%" in result
        assert "text-risk-red" in result

    def test_zero_returns_dashes(self) -> None:
        """Zero change returns gray dashes."""
        result = format_yoy_html(0)
        assert "--" in result
        assert "text-gray-400" in result

    def test_none_returns_dashes(self) -> None:
        """None returns gray dashes."""
        result = format_yoy_html(None)
        assert "--" in result
        assert "text-gray-400" in result

    def test_small_positive(self) -> None:
        """Small positive value still gets green arrow."""
        result = format_yoy_html(0.5)
        assert "text-risk-green" in result
        assert "+0.5%" in result


class TestFormatAdaptive:
    """Tests for adaptive precision formatting."""

    def test_ratio(self) -> None:
        """Ratio unit formats as 1.07x."""
        result = format_adaptive(1.07, "ratio")
        assert result == "1.07x"

    def test_percentage(self) -> None:
        """Percentage unit formats as 23.4%."""
        result = format_adaptive(23.4, "pct")
        assert result == "23.4%"

    def test_currency(self) -> None:
        """Currency unit formats via compact accounting."""
        result = format_adaptive(394_328_000_000, "currency")
        assert result == "$394.3B"

    def test_auto_large_number(self) -> None:
        """Auto-detect large numbers as compact currency."""
        result = format_adaptive(1_500_000)
        assert "$" in result
        assert "M" in result

    def test_auto_small_decimal(self) -> None:
        """Auto-detect small decimals as ratio."""
        result = format_adaptive(1.07)
        assert result == "1.07x"

    def test_none_returns_na(self) -> None:
        """None returns gray italic N/A."""
        result = format_adaptive(None)
        assert "N/A" in result
        assert "text-gray-400" in result


class TestFormatNa:
    """Tests for N/A HTML formatting."""

    def test_none_returns_html_na(self) -> None:
        """None returns gray italic N/A HTML span."""
        result = format_na(None)
        assert "N/A" in result
        assert "text-gray-400" in result
        assert "italic" in result

    def test_value_returns_string(self) -> None:
        """Non-None values return str(value)."""
        assert format_na(42) == "42"
        assert format_na("hello") == "hello"

    def test_zero_returns_zero(self) -> None:
        """Zero is not None -- returns '0'."""
        assert format_na(0) == "0"

    def test_empty_string_returns_empty(self) -> None:
        """Empty string is not None -- returns ''."""
        assert format_na("") == ""
