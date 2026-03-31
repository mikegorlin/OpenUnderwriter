"""Tests for forward short-seller monitoring context builder.

Verifies short-seller report detection with firm+company co-occurrence
and short interest conviction label derivation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders._forward_short_sellers import (
    build_short_seller_alerts,
    derive_short_conviction,
)


def _make_state_with_search(
    search_results: dict[str, Any] | None = None,
    blind_spot_results: dict[str, Any] | None = None,
    ticker: str = "TEST",
    company_name: str = "Test Corp",
) -> MagicMock:
    """Build mock state with web search results."""
    state = MagicMock()
    state.company.ticker = ticker
    state.company.company_name = company_name

    ad = MagicMock()
    ad.web_search_results = search_results or {}
    ad.blind_spot_results = blind_spot_results or {}
    state.acquired_data = ad

    return state


def _make_state_with_short_interest(
    shares_short: int | None = None,
    shares_short_prior: int | None = None,
    trend_6m: str | None = None,
    short_pct_float: float | None = None,
    days_to_cover: float | None = None,
) -> MagicMock:
    """Build mock state with short interest data."""
    state = MagicMock()

    si = MagicMock()

    def _make_sv(val: Any) -> MagicMock | None:
        if val is None:
            return None
        sv = MagicMock()
        sv.value = val
        return sv

    si.shares_short = _make_sv(shares_short)
    si.shares_short_prior = _make_sv(shares_short_prior)
    si.trend_6m = _make_sv(trend_6m)
    si.short_pct_float = _make_sv(short_pct_float)
    si.days_to_cover = _make_sv(days_to_cover)

    state.extracted.market.short_interest = si
    return state


class TestBuildShortSellerAlerts:
    """Tests for build_short_seller_alerts."""

    def test_returns_dict_with_required_keys(self) -> None:
        state = _make_state_with_search()
        result = build_short_seller_alerts(state)
        assert "alerts_available" in result
        assert "reports" in result
        assert "report_count" in result
        assert "firms_checked" in result

    def test_checks_five_named_firms(self) -> None:
        state = _make_state_with_search()
        result = build_short_seller_alerts(state)
        assert len(result["firms_checked"]) == 5
        firms = result["firms_checked"]
        assert "Citron Research" in firms
        assert "Hindenburg Research" in firms
        assert "Spruce Point Capital" in firms
        assert "Muddy Waters Research" in firms
        assert "Kerrisdale Capital" in firms

    def test_detects_report_with_co_occurrence(self) -> None:
        """Report detected when firm name AND company ticker co-occur."""
        state = _make_state_with_search(
            ticker="ACME",
            company_name="Acme Corp",
            blind_spot_results={
                "query_1": {
                    "results": [
                        {
                            "title": "Hindenburg Research short report on ACME",
                            "snippet": "Hindenburg Research published a short report targeting ACME stock",
                            "url": "https://example.com/report",
                        }
                    ]
                }
            },
        )
        result = build_short_seller_alerts(state)
        assert result["alerts_available"] is True
        assert result["report_count"] >= 1
        assert any(r["firm"] == "Hindenburg Research" for r in result["reports"])

    def test_requires_co_occurrence_no_false_positive(self) -> None:
        """Firm name without company name/ticker should NOT match."""
        state = _make_state_with_search(
            ticker="ACME",
            company_name="Acme Corp",
            blind_spot_results={
                "query_1": {
                    "results": [
                        {
                            "title": "Hindenburg Research report on OTHER company",
                            "snippet": "Hindenburg Research targets OTHER Corp in new short report",
                            "url": "https://example.com/report",
                        }
                    ]
                }
            },
        )
        result = build_short_seller_alerts(state)
        assert result["alerts_available"] is False
        assert result["report_count"] == 0

    def test_no_alerts_when_empty_data(self) -> None:
        state = _make_state_with_search()
        result = build_short_seller_alerts(state)
        assert result["alerts_available"] is False
        assert result["reports"] == []

    def test_report_entry_has_required_keys(self) -> None:
        state = _make_state_with_search(
            ticker="TEST",
            blind_spot_results={
                "q": {
                    "results": [
                        {
                            "title": "Citron Research short report on TEST",
                            "snippet": "Citron Research targets TEST stock short",
                            "url": "https://example.com",
                        }
                    ]
                }
            },
        )
        result = build_short_seller_alerts(state)
        if result["reports"]:
            report = result["reports"][0]
            assert "firm" in report
            assert "title" in report
            assert "url" in report


class TestDeriveShortConviction:
    """Tests for derive_short_conviction."""

    def test_rising_when_shares_increase_over_10pct(self) -> None:
        state = _make_state_with_short_interest(
            shares_short=1150000, shares_short_prior=1000000
        )
        result = derive_short_conviction(state)
        assert result["conviction"] == "Rising"
        assert result["conviction_color"] == "#DC2626"

    def test_declining_when_shares_decrease_over_10pct(self) -> None:
        state = _make_state_with_short_interest(
            shares_short=800000, shares_short_prior=1000000
        )
        result = derive_short_conviction(state)
        assert result["conviction"] == "Declining"
        assert result["conviction_color"] == "#16A34A"

    def test_stable_when_change_within_10pct(self) -> None:
        state = _make_state_with_short_interest(
            shares_short=1050000, shares_short_prior=1000000
        )
        result = derive_short_conviction(state)
        assert result["conviction"] == "Stable"
        assert result["conviction_color"] == "#D97706"

    def test_fallback_to_trend_6m_rising(self) -> None:
        state = _make_state_with_short_interest(trend_6m="UP")
        result = derive_short_conviction(state)
        assert result["conviction"] == "Rising"

    def test_fallback_to_trend_6m_declining(self) -> None:
        state = _make_state_with_short_interest(trend_6m="DECLINING")
        result = derive_short_conviction(state)
        assert result["conviction"] == "Declining"

    def test_stable_when_no_data(self) -> None:
        state = _make_state_with_short_interest()
        result = derive_short_conviction(state)
        assert result["conviction"] == "Stable"

    def test_conviction_has_rationale(self) -> None:
        state = _make_state_with_short_interest(
            shares_short=1200000, shares_short_prior=1000000
        )
        result = derive_short_conviction(state)
        assert "conviction_rationale" in result
        assert len(result["conviction_rationale"]) > 0
