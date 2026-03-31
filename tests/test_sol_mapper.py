"""Tests for statute of limitations mapper (SECT6-11).

Tests window computation, open/closed logic, trigger date resolution,
and the main compute_sol_map function.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from unittest.mock import patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import CaseDetail, LitigationLandscape
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.extract.sol_mapper import (
    compute_sol_map,
    compute_window,
    find_trigger_date,
    sort_windows,
)


def _make_state(
    sca_dates: list[str] | None = None,
    sca_class_periods: list[tuple[str, str]] | None = None,
    filing_date: str | None = None,
) -> AnalysisState:
    """Create a state with optional SCA cases and 10-K filing date.

    Args:
        sca_dates: List of SCA complaint filing dates (ISO format).
        sca_class_periods: List of (class_period_start, class_period_end) tuples.
            If provided, must be same length as sca_dates.
        filing_date: 10-K filing date (ISO format).
    """
    state = AnalysisState(ticker="TEST")

    if filing_date:
        state.acquired_data = AcquiredData(
            filing_documents={
                "10-K": [
                    {
                        "accession": "test-10k",
                        "filing_date": filing_date,
                        "form_type": "10-K",
                        "full_text": "Annual report content",
                    }
                ]
            }
        )

    if sca_dates:
        state.extracted = ExtractedData()
        state.extracted.litigation = LitigationLandscape()
        cases: list[CaseDetail] = []
        for i, d in enumerate(sca_dates):
            case = CaseDetail()
            case.filing_date = SourcedValue[date](
                value=date.fromisoformat(d),
                source="test",
                confidence=Confidence.HIGH,
                as_of=datetime.now(tz=UTC),
            )
            if sca_class_periods and i < len(sca_class_periods):
                cp_start, cp_end = sca_class_periods[i]
                case.class_period_start = SourcedValue[date](
                    value=date.fromisoformat(cp_start),
                    source="test",
                    confidence=Confidence.HIGH,
                    as_of=datetime.now(tz=UTC),
                )
                case.class_period_end = SourcedValue[date](
                    value=date.fromisoformat(cp_end),
                    source="test",
                    confidence=Confidence.HIGH,
                    as_of=datetime.now(tz=UTC),
                )
            cases.append(case)
        state.extracted.litigation.securities_class_actions = cases

    return state


_MOCK_CONFIG: dict[str, Any] = {
    "claim_types": {
        "10b-5": {
            "display_name": "Section 10(b) / Rule 10b-5",
            "sol_years": 2,
            "repose_years": 5,
            "sol_trigger": "discovery",
            "repose_trigger": "violation",
        },
        "Section_11": {
            "display_name": "Securities Act Section 11",
            "sol_years": 1,
            "repose_years": 3,
            "sol_trigger": "discovery",
            "repose_trigger": "offering",
        },
    }
}


# ---------------------------------------------------------------------------
# Window computation tests
# ---------------------------------------------------------------------------


class TestComputeWindow:
    """Test SOL and repose window computation."""

    def test_open_window(self) -> None:
        today = date(2024, 6, 1)
        trigger = date(2024, 1, 1)
        window = compute_window(
            "10b-5", 2, 5, trigger, "Test trigger", Confidence.HIGH, today
        )
        assert window.sol_open is True
        assert window.repose_open is True
        assert window.window_open is True
        assert window.sol_expiry is not None
        assert window.repose_expiry is not None

    def test_sol_expired_but_repose_open(self) -> None:
        today = date(2024, 6, 1)
        trigger = date(2021, 1, 1)  # SOL=2yr would expire ~2023
        window = compute_window(
            "10b-5", 2, 5, trigger, "Test", Confidence.HIGH, today
        )
        assert window.sol_open is False
        assert window.repose_open is True
        assert window.window_open is False  # Both must be open.

    def test_both_expired(self) -> None:
        today = date(2024, 6, 1)
        trigger = date(2015, 1, 1)  # Both expired.
        window = compute_window(
            "10b-5", 2, 5, trigger, "Test", Confidence.HIGH, today
        )
        assert window.sol_open is False
        assert window.repose_open is False
        assert window.window_open is False

    def test_repose_constrains_sol(self) -> None:
        """Repose is shorter than SOL -- repose closes first."""
        today = date(2024, 6, 1)
        trigger = date(2022, 1, 1)
        # SOL 5yr, repose 2yr: repose expires first.
        window = compute_window(
            "test", 5, 2, trigger, "Test", Confidence.HIGH, today
        )
        assert window.sol_open is True
        assert window.repose_open is False
        assert window.window_open is False

    def test_expiry_dates_computed(self) -> None:
        trigger = date(2024, 1, 1)
        window = compute_window(
            "10b-5", 2, 5, trigger, "Test", Confidence.HIGH, date(2024, 6, 1)
        )
        expected_sol = trigger + timedelta(days=2 * 365)
        expected_repose = trigger + timedelta(days=5 * 365)
        assert window.sol_expiry == expected_sol
        assert window.repose_expiry == expected_repose


# ---------------------------------------------------------------------------
# Trigger date resolution tests
# ---------------------------------------------------------------------------


class TestFindTriggerDate:
    """Test trigger date resolution from state data."""

    def test_trigger_from_class_period_end_discovery(self) -> None:
        """Discovery trigger uses class_period_end (corrective disclosure)."""
        state = _make_state(
            sca_dates=["2024-06-01"],
            sca_class_periods=[("2023-01-15", "2024-03-15")],
        )
        trigger_date, desc, conf = find_trigger_date(
            "10b-5", state, sol_trigger="discovery",
        )
        assert trigger_date == date(2024, 3, 15)  # class_period_end
        assert "class period end" in desc.lower()
        assert conf == Confidence.HIGH

    def test_trigger_fallback_to_filing_date(self) -> None:
        """When class period dates unavailable, fall back to filing date."""
        state = _make_state(sca_dates=["2024-03-15", "2024-06-01"])
        trigger_date, desc, conf = find_trigger_date(
            "10b-5", state, sol_trigger="discovery",
        )
        assert trigger_date == date(2024, 3, 15)  # earliest filing date
        assert "filing date" in desc.lower()
        assert conf == Confidence.MEDIUM

    def test_proxy_trigger_from_10k(self) -> None:
        state = _make_state(filing_date="2024-02-28")
        trigger_date, desc, conf = find_trigger_date("10b-5", state)
        assert trigger_date == date(2024, 2, 28)
        assert "proxy" in desc.lower()
        assert conf == Confidence.LOW

    def test_no_trigger_available(self) -> None:
        state = AnalysisState(ticker="TEST")
        trigger_date, _desc, _conf = find_trigger_date("10b-5", state)
        assert trigger_date is None


# ---------------------------------------------------------------------------
# Sort tests
# ---------------------------------------------------------------------------


class TestSortWindows:
    """Test window sorting (open first, then by repose date)."""

    def test_open_before_closed(self) -> None:
        from do_uw.models.litigation_details import SOLWindow

        open_w = SOLWindow(
            claim_type="a",
            sol_years=2,
            repose_years=5,
            window_open=True,
            repose_expiry=date(2026, 1, 1),
        )
        closed_w = SOLWindow(
            claim_type="b",
            sol_years=2,
            repose_years=5,
            window_open=False,
            repose_expiry=date(2023, 1, 1),
        )
        result = sort_windows([closed_w, open_w])
        assert result[0].claim_type == "a"
        assert result[1].claim_type == "b"


# ---------------------------------------------------------------------------
# Main function tests
# ---------------------------------------------------------------------------


class TestComputeSolMap:
    """Test the main compute_sol_map function."""

    @patch(
        "do_uw.stages.extract.sol_mapper._load_claim_types",
        return_value=_MOCK_CONFIG,
    )
    def test_with_sca_trigger(self, _mock: Any) -> None:
        state = _make_state(
            sca_dates=["2024-01-15"],
            filing_date="2024-02-28",
        )
        windows, report = compute_sol_map(state)
        # Should have windows for both claim types (SCA-triggered).
        assert len(windows) >= 2
        assert report.coverage_pct > 0

    @patch(
        "do_uw.stages.extract.sol_mapper._load_claim_types",
        return_value=_MOCK_CONFIG,
    )
    def test_with_proxy_trigger_only(self, _mock: Any) -> None:
        state = _make_state(filing_date="2024-02-28")
        windows, _report = compute_sol_map(state)
        # Should still create windows using proxy dates.
        assert len(windows) >= 1

    @patch(
        "do_uw.stages.extract.sol_mapper._load_claim_types",
        return_value=_MOCK_CONFIG,
    )
    def test_no_trigger_no_windows(self, _mock: Any) -> None:
        state = AnalysisState(ticker="TEST")
        windows, _report = compute_sol_map(state)
        assert len(windows) == 0

    @patch(
        "do_uw.stages.extract.sol_mapper._load_claim_types",
        return_value={"claim_types": {}},
    )
    def test_empty_config(self, _mock: Any) -> None:
        state = AnalysisState(ticker="TEST")
        windows, report = compute_sol_map(state)
        assert len(windows) == 0
        assert len(report.warnings) >= 1
