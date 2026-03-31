"""Tests for 8-K event converter multi-instance aggregation."""

from __future__ import annotations

from do_uw.models.common import Confidence
from do_uw.stages.extract.eight_k_converter import (
    convert_acquisitions,
    convert_agreements,
    convert_auditor_changes,
    convert_bylaws_changes,
    convert_departures,
    convert_earnings_events,
    convert_ethics_changes,
    convert_impairments,
    convert_restatements,
    convert_restructurings,
    convert_terminations,
)
from do_uw.stages.extract.llm.schemas.eight_k import EightKExtraction


# ------------------------------------------------------------------
# Test helpers
# ------------------------------------------------------------------


def _make_departure_8k(
    name: str = "Jane Doe",
    *,
    title: str | None = None,
    reason: str | None = "resignation",
    successor: str | None = None,
    is_termination: bool | None = False,
    event_date: str | None = "2024-06-15",
) -> EightKExtraction:
    """Create an 8-K extraction with departure fields populated."""
    return EightKExtraction(
        departing_officer=name,
        departing_officer_title=title,
        departure_reason=reason,
        successor=successor,
        is_termination=is_termination,
        event_date=event_date,
    )


def _make_agreement_8k(
    agreement_type: str = "merger",
    *,
    counterparty: str | None = "Acme Corp",
    summary: str | None = "Acquisition of Acme Corp for $1B",
    event_date: str | None = "2024-03-01",
) -> EightKExtraction:
    """Create an 8-K extraction with agreement fields populated."""
    return EightKExtraction(
        agreement_type=agreement_type,
        counterparty=counterparty,
        agreement_summary=summary,
        event_date=event_date,
    )


def _make_restatement_8k(
    periods: list[str] | None = None,
    *,
    reason: str | None = "Revenue recognition error",
    event_date: str | None = "2024-01-15",
) -> EightKExtraction:
    """Create an 8-K extraction with restatement fields populated."""
    return EightKExtraction(
        restatement_periods=periods if periods is not None else ["Q1 2024", "Q2 2024"],
        restatement_reason=reason,
        event_date=event_date,
    )


def _make_earnings_8k(
    revenue: float | None = 10_000_000_000.0,
    eps: float | None = 3.45,
    *,
    guidance_update: str | None = None,
    event_date: str | None = "2024-07-25",
) -> EightKExtraction:
    """Create an 8-K extraction with earnings fields populated."""
    return EightKExtraction(
        revenue=revenue,
        eps=eps,
        guidance_update=guidance_update,
        event_date=event_date,
    )


def _make_acquisition_8k(
    transaction_type: str = "acquisition",
    *,
    target_name: str | None = "TargetCo",
    transaction_value: float | None = 500_000_000.0,
    event_date: str | None = "2024-09-10",
) -> EightKExtraction:
    """Create an 8-K extraction with acquisition fields populated."""
    return EightKExtraction(
        transaction_type=transaction_type,
        target_name=target_name,
        transaction_value=transaction_value,
        event_date=event_date,
    )


# ------------------------------------------------------------------
# Departure tests
# ------------------------------------------------------------------


class TestConvertDepartures:
    """Tests for convert_departures aggregation."""

    def test_convert_departures_multiple(self) -> None:
        """Two 8-Ks with departures -> list of 2 dicts."""
        extractions = [
            _make_departure_8k("Alice Smith", reason="retirement"),
            _make_departure_8k("Bob Jones", reason="resignation"),
        ]
        result = convert_departures(extractions)
        assert len(result) == 2
        assert result[0]["name"] is not None
        assert result[0]["name"].value == "Alice Smith"
        assert result[0]["name"].source == "8-K (LLM)"
        assert result[0]["name"].confidence == Confidence.HIGH
        assert result[1]["name"] is not None
        assert result[1]["name"].value == "Bob Jones"

    def test_convert_departures_empty(self) -> None:
        """Empty list -> empty list."""
        result = convert_departures([])
        assert result == []

    def test_convert_departures_skip_no_officer(self) -> None:
        """8-K without departing_officer is skipped."""
        extractions = [
            EightKExtraction(),  # No departure fields
            _make_departure_8k("Alice Smith"),
        ]
        result = convert_departures(extractions)
        assert len(result) == 1
        assert result[0]["name"] is not None
        assert result[0]["name"].value == "Alice Smith"

    def test_convert_departures_with_title(self) -> None:
        """departing_officer_title populated correctly."""
        ext = _make_departure_8k("Jane Doe", title="Chief Financial Officer")
        result = convert_departures([ext])
        assert len(result) == 1
        title = result[0]["title"]
        assert title is not None
        assert title.value == "Chief Financial Officer"
        assert title.source == "8-K (LLM)"
        assert title.confidence == Confidence.HIGH

    def test_convert_departures_with_termination(self) -> None:
        """is_termination populated as SourcedValue[bool]."""
        ext = _make_departure_8k(
            "John Smith",
            reason="termination",
            is_termination=True,
        )
        result = convert_departures([ext])
        assert len(result) == 1
        term = result[0]["is_termination"]
        assert term is not None
        assert term.value is True
        assert term.source == "8-K (LLM)"

    def test_convert_departures_optional_fields_none(self) -> None:
        """Optional fields are None when not populated."""
        ext = _make_departure_8k(
            "Jane Doe",
            title=None,
            reason=None,
            successor=None,
            is_termination=None,
            event_date=None,
        )
        result = convert_departures([ext])
        assert len(result) == 1
        assert result[0]["title"] is None
        assert result[0]["reason"] is None
        assert result[0]["successor"] is None
        assert result[0]["is_termination"] is None
        assert result[0]["event_date"] is None


# ------------------------------------------------------------------
# Agreement tests
# ------------------------------------------------------------------


class TestConvertAgreements:
    """Tests for convert_agreements aggregation."""

    def test_convert_agreements(self) -> None:
        """Agreement fields mapped correctly."""
        ext = _make_agreement_8k(
            "credit agreement",
            counterparty="Big Bank",
            summary="$2B revolving credit facility",
        )
        result = convert_agreements([ext])
        assert len(result) == 1
        assert result[0]["type"] is not None
        assert result[0]["type"].value == "credit agreement"
        cp = result[0]["counterparty"]
        assert cp is not None
        assert cp.value == "Big Bank"
        assert cp.source == "8-K (LLM)"
        assert cp.confidence == Confidence.HIGH

    def test_convert_agreements_skip_no_type(self) -> None:
        """8-K without agreement_type is skipped."""
        extractions = [EightKExtraction(), _make_agreement_8k()]
        result = convert_agreements(extractions)
        assert len(result) == 1


# ------------------------------------------------------------------
# Acquisition tests
# ------------------------------------------------------------------


class TestConvertAcquisitions:
    """Tests for convert_acquisitions aggregation."""

    def test_convert_acquisitions_with_value(self) -> None:
        """Transaction value as sourced_float."""
        ext = _make_acquisition_8k(
            transaction_value=1_200_000_000.0,
            target_name="WidgetCo",
        )
        result = convert_acquisitions([ext])
        assert len(result) == 1
        val = result[0]["value"]
        assert val is not None
        assert val.value == 1_200_000_000.0
        assert val.source == "8-K (LLM)"
        assert val.confidence == Confidence.HIGH
        target = result[0]["target"]
        assert target is not None
        assert target.value == "WidgetCo"

    def test_convert_acquisitions_no_value(self) -> None:
        """Acquisition without transaction_value has None for value."""
        ext = _make_acquisition_8k(transaction_value=None)
        result = convert_acquisitions([ext])
        assert len(result) == 1
        assert result[0]["value"] is None


# ------------------------------------------------------------------
# Restatement tests
# ------------------------------------------------------------------


class TestConvertRestatements:
    """Tests for convert_restatements aggregation."""

    def test_convert_restatements(self) -> None:
        """Restatement periods as list of sourced_str."""
        ext = _make_restatement_8k(
            periods=["Q1 2024", "Q2 2024", "FY2023"],
            reason="Revenue recognition error",
        )
        result = convert_restatements([ext])
        assert len(result) == 1
        periods = result[0]["periods"]
        assert isinstance(periods, list)
        assert len(periods) == 3
        assert periods[0].value == "Q1 2024"
        assert periods[0].source == "8-K (LLM)"
        assert periods[0].confidence == Confidence.HIGH
        reason = result[0]["reason"]
        assert reason is not None
        assert reason.value == "Revenue recognition error"

    def test_convert_restatements_empty_periods(self) -> None:
        """Empty restatement_periods -> skipped."""
        ext = _make_restatement_8k(periods=[])
        result = convert_restatements([ext])
        assert result == []


# ------------------------------------------------------------------
# Earnings tests
# ------------------------------------------------------------------


class TestConvertEarningsEvents:
    """Tests for convert_earnings_events aggregation."""

    def test_convert_earnings_events(self) -> None:
        """Revenue and EPS as sourced_float."""
        ext = _make_earnings_8k(
            revenue=25_000_000_000.0,
            eps=4.12,
            guidance_update="Raised FY2025 guidance to $100B",
        )
        result = convert_earnings_events([ext])
        assert len(result) == 1
        rev = result[0]["revenue"]
        assert rev is not None
        assert rev.value == 25_000_000_000.0
        assert rev.source == "8-K (LLM)"
        eps = result[0]["eps"]
        assert eps is not None
        assert eps.value == 4.12
        guidance = result[0]["guidance_update"]
        assert guidance is not None
        assert guidance.value == "Raised FY2025 guidance to $100B"

    def test_convert_earnings_events_eps_only(self) -> None:
        """8-K with only EPS (no revenue) is still included."""
        ext = _make_earnings_8k(revenue=None, eps=2.50)
        result = convert_earnings_events([ext])
        assert len(result) == 1
        assert result[0]["revenue"] is None
        assert result[0]["eps"] is not None
        assert result[0]["eps"].value == 2.50

    def test_convert_earnings_skip_no_financials(self) -> None:
        """8-K without revenue or eps is skipped."""
        ext = EightKExtraction(guidance_update="Updated guidance")
        result = convert_earnings_events([ext])
        assert result == []


# ------------------------------------------------------------------
# Mixed event type tests
# ------------------------------------------------------------------


class TestMixedEventTypes:
    """Tests for mixed event types across converter functions."""

    def test_mixed_event_types(self) -> None:
        """List with departure + agreement -> each converter picks its events."""
        departure_8k = _make_departure_8k("CFO Left")
        agreement_8k = _make_agreement_8k("settlement")
        all_8ks = [departure_8k, agreement_8k]

        departures = convert_departures(all_8ks)
        agreements = convert_agreements(all_8ks)

        assert len(departures) == 1
        assert departures[0]["name"] is not None
        assert departures[0]["name"].value == "CFO Left"

        assert len(agreements) == 1
        assert agreements[0]["type"] is not None
        assert agreements[0]["type"].value == "settlement"

    def test_all_converters_empty_input(self) -> None:
        """All converters handle empty list gracefully."""
        assert convert_departures([]) == []
        assert convert_agreements([]) == []
        assert convert_acquisitions([]) == []
        assert convert_restatements([]) == []
        assert convert_earnings_events([]) == []
        assert convert_terminations([]) == []
        assert convert_restructurings([]) == []
        assert convert_impairments([]) == []
        assert convert_auditor_changes([]) == []
        assert convert_bylaws_changes([]) == []
        assert convert_ethics_changes([]) == []


# ------------------------------------------------------------------
# Termination tests (Item 1.02)
# ------------------------------------------------------------------


class TestConvertTerminations:
    """Tests for convert_terminations aggregation."""

    def test_convert_termination(self) -> None:
        ext = EightKExtraction(
            terminated_agreement="Credit Agreement",
            termination_reason="breach",
            termination_counterparty="Big Bank",
            event_date="2024-05-01",
        )
        result = convert_terminations([ext])
        assert len(result) == 1
        assert result[0]["agreement"] is not None
        assert result[0]["agreement"].value == "Credit Agreement"
        assert result[0]["reason"] is not None
        assert result[0]["reason"].value == "breach"

    def test_skip_no_terminated_agreement(self) -> None:
        ext = EightKExtraction()
        result = convert_terminations([ext])
        assert result == []


# ------------------------------------------------------------------
# Restructuring tests (Item 2.05)
# ------------------------------------------------------------------


class TestConvertRestructurings:
    """Tests for convert_restructurings aggregation."""

    def test_convert_restructuring(self) -> None:
        ext = EightKExtraction(
            restructuring_type="layoffs",
            restructuring_charge=50_000_000.0,
            restructuring_description="Reduction of 500 positions",
            event_date="2024-02-28",
        )
        result = convert_restructurings([ext])
        assert len(result) == 1
        assert result[0]["type"] is not None
        assert result[0]["type"].value == "layoffs"
        assert result[0]["charge"] is not None
        assert result[0]["charge"].value == 50_000_000.0

    def test_skip_no_restructuring(self) -> None:
        ext = EightKExtraction()
        result = convert_restructurings([ext])
        assert result == []


# ------------------------------------------------------------------
# Impairment tests (Item 2.06)
# ------------------------------------------------------------------


class TestConvertImpairments:
    """Tests for convert_impairments aggregation."""

    def test_convert_impairment(self) -> None:
        ext = EightKExtraction(
            impairment_type="goodwill",
            impairment_amount=200_000_000.0,
            impairment_description="Goodwill writedown in reporting unit",
            event_date="2024-04-15",
        )
        result = convert_impairments([ext])
        assert len(result) == 1
        assert result[0]["type"] is not None
        assert result[0]["type"].value == "goodwill"
        assert result[0]["amount"] is not None
        assert result[0]["amount"].value == 200_000_000.0

    def test_skip_no_impairment(self) -> None:
        ext = EightKExtraction()
        result = convert_impairments([ext])
        assert result == []


# ------------------------------------------------------------------
# Auditor change tests (Item 4.01)
# ------------------------------------------------------------------


class TestConvertAuditorChanges:
    """Tests for convert_auditor_changes aggregation."""

    def test_convert_auditor_change(self) -> None:
        ext = EightKExtraction(
            former_auditor="Deloitte & Touche LLP",
            new_auditor="Ernst & Young LLP",
            auditor_disagreements=True,
            event_date="2024-06-30",
        )
        result = convert_auditor_changes([ext])
        assert len(result) == 1
        assert result[0]["former_auditor"] is not None
        assert result[0]["former_auditor"].value == "Deloitte & Touche LLP"
        assert result[0]["new_auditor"] is not None
        assert result[0]["new_auditor"].value == "Ernst & Young LLP"
        assert result[0]["disagreements"] is not None
        assert result[0]["disagreements"].value is True

    def test_skip_no_auditor_change(self) -> None:
        ext = EightKExtraction()
        result = convert_auditor_changes([ext])
        assert result == []


# ------------------------------------------------------------------
# Bylaws change tests (Item 5.03)
# ------------------------------------------------------------------


class TestConvertBylawsChanges:
    """Tests for convert_bylaws_changes aggregation."""

    def test_convert_bylaws_change(self) -> None:
        ext = EightKExtraction(
            bylaws_amendment_type="forum selection",
            bylaws_amendment_summary="Adopted Delaware exclusive forum provision",
            event_date="2024-08-01",
        )
        result = convert_bylaws_changes([ext])
        assert len(result) == 1
        assert result[0]["type"] is not None
        assert result[0]["type"].value == "forum selection"

    def test_skip_no_bylaws(self) -> None:
        ext = EightKExtraction()
        result = convert_bylaws_changes([ext])
        assert result == []


# ------------------------------------------------------------------
# Ethics change tests (Item 5.05)
# ------------------------------------------------------------------


class TestConvertEthicsChanges:
    """Tests for convert_ethics_changes aggregation."""

    def test_convert_ethics_waiver(self) -> None:
        ext = EightKExtraction(
            ethics_change_type="waiver",
            ethics_change_person="CEO",
            ethics_change_summary="Waiver of conflict of interest provision",
            event_date="2024-07-15",
        )
        result = convert_ethics_changes([ext])
        assert len(result) == 1
        assert result[0]["type"] is not None
        assert result[0]["type"].value == "waiver"
        assert result[0]["person"] is not None
        assert result[0]["person"].value == "CEO"

    def test_skip_no_ethics_change(self) -> None:
        ext = EightKExtraction()
        result = convert_ethics_changes([ext])
        assert result == []
