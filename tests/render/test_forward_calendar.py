"""Tests for forward calendar context builder.

Verifies that build_forward_calendar() collects dates from multiple
state paths and classifies urgency with color coding.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders._forward_calendar import (
    build_forward_calendar,
)


def _make_mock_state(
    *,
    earnings_date: str | None = None,
    ex_dividend: str | None = None,
    annual_meeting: str | None = None,
    ipo_date: str | None = None,
    fiscal_year_end: str | None = None,
    years_public: int = 20,
) -> MagicMock:
    """Build a mock AnalysisState with calendar and governance data."""
    state = MagicMock()

    # Market data calendar
    calendar: dict[str, Any] = {}
    if earnings_date:
        calendar["Earnings Date"] = [earnings_date]
    if ex_dividend:
        calendar["Ex-Dividend Date"] = ex_dividend

    md: dict[str, Any] = {"calendar": calendar}
    state.acquired_data.market_data = md

    # Governance for annual meeting
    if annual_meeting:
        state.extracted.governance.annual_meeting_date = annual_meeting
    else:
        state.extracted.governance.annual_meeting_date = None

    # Company profile for IPO
    if ipo_date:
        state.extracted.company_profile.ipo_date = ipo_date
    else:
        state.extracted.company_profile.ipo_date = None

    state.extracted.company_profile.years_public = years_public

    # Fiscal year end
    if fiscal_year_end:
        state.company.fiscal_year_end = fiscal_year_end
    else:
        state.company.fiscal_year_end = None

    return state


class TestBuildForwardCalendar:
    """Tests for build_forward_calendar."""

    def test_returns_dict_with_required_keys(self) -> None:
        tomorrow = (date.today() + timedelta(days=10)).isoformat()
        state = _make_mock_state(earnings_date=tomorrow)
        result = build_forward_calendar(state)
        assert isinstance(result, dict)
        assert "calendar_available" in result
        assert "dates" in result
        assert "monitoring_triggers" in result
        assert "date_count" in result

    def test_includes_earnings_date(self) -> None:
        tomorrow = (date.today() + timedelta(days=10)).isoformat()
        state = _make_mock_state(earnings_date=tomorrow)
        result = build_forward_calendar(state)
        assert result["calendar_available"] is True
        events = [d["event"] for d in result["dates"]]
        assert any("Earnings" in e for e in events)

    def test_date_entry_has_required_keys(self) -> None:
        tomorrow = (date.today() + timedelta(days=10)).isoformat()
        state = _make_mock_state(earnings_date=tomorrow)
        result = build_forward_calendar(state)
        required_keys = {
            "date", "event", "source", "urgency",
            "urgency_color", "do_relevance",
        }
        for entry in result["dates"]:
            assert required_keys.issubset(entry.keys()), (
                f"Missing keys: {required_keys - entry.keys()}"
            )

    def test_urgency_within_30d_is_red(self) -> None:
        soon = (date.today() + timedelta(days=5)).isoformat()
        state = _make_mock_state(earnings_date=soon)
        result = build_forward_calendar(state)
        earnings = [d for d in result["dates"] if "Earnings" in d["event"]]
        assert len(earnings) > 0
        assert earnings[0]["urgency"] == "HIGH"
        assert earnings[0]["urgency_color"] == "#DC2626"

    def test_urgency_30_to_90d_is_amber(self) -> None:
        medium = (date.today() + timedelta(days=60)).isoformat()
        state = _make_mock_state(earnings_date=medium)
        result = build_forward_calendar(state)
        earnings = [d for d in result["dates"] if "Earnings" in d["event"]]
        assert len(earnings) > 0
        assert earnings[0]["urgency"] == "MEDIUM"
        assert earnings[0]["urgency_color"] == "#D97706"

    def test_urgency_beyond_90d_is_gray(self) -> None:
        far = (date.today() + timedelta(days=120)).isoformat()
        state = _make_mock_state(earnings_date=far)
        result = build_forward_calendar(state)
        earnings = [d for d in result["dates"] if "Earnings" in d["event"]]
        assert len(earnings) > 0
        assert earnings[0]["urgency"] == "LOW"
        assert earnings[0]["urgency_color"] == "#9CA3AF"

    def test_dates_sorted_chronologically(self) -> None:
        d1 = (date.today() + timedelta(days=60)).isoformat()
        d2 = (date.today() + timedelta(days=10)).isoformat()
        state = _make_mock_state(earnings_date=d1, ex_dividend=d2)
        result = build_forward_calendar(state)
        dates = [d["date"] for d in result["dates"]]
        assert dates == sorted(dates)

    def test_monitoring_triggers_includes_earnings(self) -> None:
        tomorrow = (date.today() + timedelta(days=10)).isoformat()
        state = _make_mock_state(earnings_date=tomorrow)
        result = build_forward_calendar(state)
        trigger_events = [t["event"] for t in result["monitoring_triggers"]]
        assert any("Earnings" in e for e in trigger_events)

    def test_ipo_milestones_for_recent_ipo(self) -> None:
        """Companies public < 5 years should have IPO milestone dates."""
        ipo = (date.today() - timedelta(days=365)).isoformat()
        state = _make_mock_state(ipo_date=ipo, years_public=1)
        result = build_forward_calendar(state)
        events = [d["event"] for d in result["dates"]]
        assert any("IPO" in e or "Lockup" in e for e in events)

    def test_empty_when_no_data(self) -> None:
        state = _make_mock_state()
        result = build_forward_calendar(state)
        assert result["calendar_available"] is False
        assert result["dates"] == []
