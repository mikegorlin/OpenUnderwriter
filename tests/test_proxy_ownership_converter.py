"""Tests for proxy ownership converter (DEF 14A ownership table parsing)."""

from __future__ import annotations

from do_uw.models.common import Confidence
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.proxy_ownership_converter import (
    convert_insider_ownership,
    convert_proxy_ownership_summary,
    convert_top_holders,
)


# ------------------------------------------------------------------
# Test helpers
# ------------------------------------------------------------------


def _make_proxy(
    *,
    insider_pct: float | None = 21.3,
    holders: list[str] | None = None,
) -> DEF14AExtraction:
    """Create a DEF14AExtraction with ownership data."""
    return DEF14AExtraction(
        officers_directors_ownership_pct=insider_pct,
        top_5_holders=holders
        if holders is not None
        else [
            "Elon Musk: 21.3%",
            "Vanguard Group: 6.1%",
            "BlackRock: 4.8%",
        ],
    )


# ------------------------------------------------------------------
# Top holders tests
# ------------------------------------------------------------------


class TestConvertTopHolders:
    """Tests for convert_top_holders parsing."""

    def test_convert_top_holders(self) -> None:
        """3 holders -> 3 SourcedValue dicts with name and percentage."""
        ext = _make_proxy()
        result = convert_top_holders(ext)
        assert len(result) == 3

        assert result[0].value == {"name": "Elon Musk", "percentage": "21.3%"}
        assert result[0].source == "DEF 14A (LLM)"
        assert result[0].confidence == Confidence.HIGH

        assert result[1].value == {"name": "Vanguard Group", "percentage": "6.1%"}
        assert result[2].value == {"name": "BlackRock", "percentage": "4.8%"}

    def test_convert_top_holders_empty(self) -> None:
        """Empty list -> empty list."""
        ext = _make_proxy(holders=[])
        result = convert_top_holders(ext)
        assert result == []

    def test_convert_top_holders_no_colon(self) -> None:
        """'Elon Musk 21%' -> name is full string, percentage is N/A."""
        ext = _make_proxy(holders=["Elon Musk 21%"])
        result = convert_top_holders(ext)
        assert len(result) == 1
        assert result[0].value["name"] == "Elon Musk 21%"
        assert result[0].value["percentage"] == "N/A"

    def test_convert_top_holders_multiple_colons(self) -> None:
        """Entry with multiple colons splits on the first one."""
        ext = _make_proxy(holders=["LLC: Sub: 5.0%"])
        result = convert_top_holders(ext)
        assert len(result) == 1
        assert result[0].value["name"] == "LLC"
        assert result[0].value["percentage"] == "Sub: 5.0%"


# ------------------------------------------------------------------
# Insider ownership tests
# ------------------------------------------------------------------


class TestConvertInsiderOwnership:
    """Tests for convert_insider_ownership."""

    def test_convert_insider_ownership(self) -> None:
        """21.3 -> SourcedValue(21.3) with DEF 14A (LLM) source."""
        ext = _make_proxy(insider_pct=21.3)
        result = convert_insider_ownership(ext)
        assert result is not None
        assert result.value == 21.3
        assert result.source == "DEF 14A (LLM)"
        assert result.confidence == Confidence.HIGH

    def test_convert_insider_ownership_none(self) -> None:
        """None -> None."""
        ext = _make_proxy(insider_pct=None)
        result = convert_insider_ownership(ext)
        assert result is None


# ------------------------------------------------------------------
# Summary tests
# ------------------------------------------------------------------


class TestConvertProxyOwnershipSummary:
    """Tests for convert_proxy_ownership_summary."""

    def test_convert_proxy_ownership_summary(self) -> None:
        """Returns both fields populated."""
        ext = _make_proxy()
        result = convert_proxy_ownership_summary(ext)

        insider = result["insider_pct"]
        assert insider is not None
        assert not isinstance(insider, list)
        assert insider.value == 21.3
        assert insider.source == "DEF 14A (LLM)"

        holders = result["top_holders"]
        assert isinstance(holders, list)
        assert len(holders) == 3

    def test_convert_proxy_ownership_summary_partial(self) -> None:
        """Only insider_pct, no top_5_holders."""
        ext = _make_proxy(insider_pct=15.0, holders=[])
        result = convert_proxy_ownership_summary(ext)

        insider = result["insider_pct"]
        assert insider is not None
        assert not isinstance(insider, list)
        assert insider.value == 15.0

        holders = result["top_holders"]
        assert isinstance(holders, list)
        assert holders == []

    def test_convert_proxy_ownership_summary_no_insider(self) -> None:
        """No insider_pct, but has top_5_holders."""
        ext = _make_proxy(
            insider_pct=None,
            holders=["Vanguard Group: 8.2%"],
        )
        result = convert_proxy_ownership_summary(ext)
        assert result["insider_pct"] is None
        holders = result["top_holders"]
        assert isinstance(holders, list)
        assert len(holders) == 1
