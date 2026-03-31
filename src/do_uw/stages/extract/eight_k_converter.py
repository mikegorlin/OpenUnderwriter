"""8-K event converter: EightKExtraction list -> aggregated event records.

Maps flat LLM-extracted 8-K fields into structured event records for the
scoring engine and worksheet renderer. 8-K is unique among SEC filings:
companies file many per year, each covering different events. The converter
must aggregate across ALL 8-K extractions.

Each function takes ``list[EightKExtraction]`` and returns aggregated
records for a specific event type. Events without relevant fields are
silently skipped (not errors -- most 8-Ks only cover one event type).

Public functions:
- convert_departures       -> list of departure dicts (Item 5.02)
- convert_agreements       -> list of agreement dicts (Item 1.01)
- convert_terminations     -> list of termination dicts (Item 1.02)
- convert_acquisitions     -> list of acquisition dicts (Item 2.01)
- convert_restatements     -> list of restatement dicts (Item 4.02)
- convert_earnings_events  -> list of earnings event dicts (Item 2.02)
- convert_restructurings   -> list of restructuring dicts (Item 2.05)
- convert_impairments      -> list of impairment dicts (Item 2.06)
- convert_auditor_changes  -> list of auditor change dicts (Item 4.01)
- convert_bylaws_changes   -> list of bylaws amendment dicts (Item 5.03)
- convert_ethics_changes   -> list of ethics code change dicts (Item 5.05)
"""

from __future__ import annotations

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.llm.schemas.eight_k import EightKExtraction
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
    sourced_str,
)

_LLM_SOURCE = "8-K (LLM)"


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _sourced_bool(value: bool) -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with 8-K LLM source and HIGH confidence."""
    return SourcedValue[bool](
        value=value,
        source=_LLM_SOURCE,
        confidence=Confidence.HIGH,
        as_of=now(),
    )


# Type alias for departure record.
DepartureRecord = dict[
    str,
    SourcedValue[str] | SourcedValue[bool] | None,
]

# Type alias for agreement record.
AgreementRecord = dict[
    str,
    SourcedValue[str] | SourcedValue[float] | None,
]

# Type alias for acquisition record.
AcquisitionRecord = dict[
    str,
    SourcedValue[str] | SourcedValue[float] | None,
]

# Type alias for restatement record.
RestatementRecord = dict[
    str,
    SourcedValue[str] | list[SourcedValue[str]] | None,
]

# Type alias for earnings event record.
EarningsRecord = dict[
    str,
    SourcedValue[str] | SourcedValue[float] | None,
]

# Re-export extended converters for backward compatibility.
# The actual implementations live in eight_k_converter_ext.py (500-line split).
from do_uw.stages.extract.eight_k_converter_ext import (  # noqa: E402, F401
    AuditorChangeRecord,
    BylawsRecord,
    EthicsChangeRecord,
    ImpairmentRecord,
    RestructuringRecord,
    TerminationRecord,
    convert_auditor_changes,
    convert_bylaws_changes,
    convert_ethics_changes,
    convert_impairments,
    convert_restructurings,
    convert_terminations,
)


# ------------------------------------------------------------------
# Departure events (Item 5.02)
# ------------------------------------------------------------------


def convert_departures(
    extractions: list[EightKExtraction],
) -> list[DepartureRecord]:
    """Aggregate executive departure events across multiple 8-K filings.

    Iterates all extractions and includes those where ``departing_officer``
    is not None. Each departure is captured as a dict of SourcedValues.

    Args:
        extractions: All 8-K LLM extraction results for a company.

    Returns:
        List of departure record dicts, one per departure event.
    """
    departures: list[DepartureRecord] = []
    for ext in extractions:
        if ext.departing_officer is None:
            continue
        record: DepartureRecord = {
            "name": sourced_str(ext.departing_officer, _LLM_SOURCE, Confidence.HIGH),
            "title": (
                sourced_str(ext.departing_officer_title, _LLM_SOURCE, Confidence.HIGH)
                if ext.departing_officer_title is not None
                else None
            ),
            "reason": (
                sourced_str(ext.departure_reason, _LLM_SOURCE, Confidence.HIGH)
                if ext.departure_reason is not None
                else None
            ),
            "successor": (
                sourced_str(ext.successor, _LLM_SOURCE, Confidence.HIGH)
                if ext.successor is not None
                else None
            ),
            "is_termination": (
                _sourced_bool(ext.is_termination)
                if ext.is_termination is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        departures.append(record)
    return departures


# ------------------------------------------------------------------
# Material agreement events (Item 1.01)
# ------------------------------------------------------------------


def convert_agreements(
    extractions: list[EightKExtraction],
) -> list[AgreementRecord]:
    """Aggregate material agreement events across multiple 8-K filings.

    Includes 8-Ks where ``agreement_type`` is not None.

    Args:
        extractions: All 8-K LLM extraction results for a company.

    Returns:
        List of agreement record dicts.
    """
    agreements: list[AgreementRecord] = []
    for ext in extractions:
        if ext.agreement_type is None:
            continue
        record: AgreementRecord = {
            "type": sourced_str(ext.agreement_type, _LLM_SOURCE, Confidence.HIGH),
            "counterparty": (
                sourced_str(ext.counterparty, _LLM_SOURCE, Confidence.HIGH)
                if ext.counterparty is not None
                else None
            ),
            "summary": (
                sourced_str(ext.agreement_summary, _LLM_SOURCE, Confidence.HIGH)
                if ext.agreement_summary is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        agreements.append(record)
    return agreements


# ------------------------------------------------------------------
# Acquisition/disposition events (Item 2.01)
# ------------------------------------------------------------------


def convert_acquisitions(
    extractions: list[EightKExtraction],
) -> list[AcquisitionRecord]:
    """Aggregate acquisition/disposition events across multiple 8-K filings.

    Includes 8-Ks where ``transaction_type`` is not None.

    Args:
        extractions: All 8-K LLM extraction results for a company.

    Returns:
        List of acquisition record dicts.
    """
    acquisitions: list[AcquisitionRecord] = []
    for ext in extractions:
        if ext.transaction_type is None:
            continue
        record: AcquisitionRecord = {
            "type": sourced_str(ext.transaction_type, _LLM_SOURCE, Confidence.HIGH),
            "target": (
                sourced_str(ext.target_name, _LLM_SOURCE, Confidence.HIGH)
                if ext.target_name is not None
                else None
            ),
            "value": (
                sourced_float(ext.transaction_value, _LLM_SOURCE, Confidence.HIGH)
                if ext.transaction_value is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        acquisitions.append(record)
    return acquisitions


# ------------------------------------------------------------------
# Restatement events (Item 4.02)
# ------------------------------------------------------------------


def convert_restatements(
    extractions: list[EightKExtraction],
) -> list[RestatementRecord]:
    """Aggregate restatement/non-reliance events across multiple 8-K filings.

    Includes 8-Ks with non-empty ``restatement_periods``.

    Args:
        extractions: All 8-K LLM extraction results for a company.

    Returns:
        List of restatement record dicts.
    """
    restatements: list[RestatementRecord] = []
    for ext in extractions:
        if not ext.restatement_periods:
            continue
        record: RestatementRecord = {
            "periods": [
                sourced_str(p, _LLM_SOURCE, Confidence.HIGH)
                for p in ext.restatement_periods
            ],
            "reason": (
                sourced_str(ext.restatement_reason, _LLM_SOURCE, Confidence.HIGH)
                if ext.restatement_reason is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        restatements.append(record)
    return restatements


# ------------------------------------------------------------------
# Earnings/financial events (Item 2.02)
# ------------------------------------------------------------------


def convert_earnings_events(
    extractions: list[EightKExtraction],
) -> list[EarningsRecord]:
    """Aggregate earnings/financial events across multiple 8-K filings.

    Includes 8-Ks where ``revenue`` or ``eps`` is not None.

    Args:
        extractions: All 8-K LLM extraction results for a company.

    Returns:
        List of earnings event record dicts.
    """
    events: list[EarningsRecord] = []
    for ext in extractions:
        if ext.revenue is None and ext.eps is None:
            continue
        record: EarningsRecord = {
            "revenue": (
                sourced_float(ext.revenue, _LLM_SOURCE, Confidence.HIGH)
                if ext.revenue is not None
                else None
            ),
            "eps": (
                sourced_float(ext.eps, _LLM_SOURCE, Confidence.HIGH)
                if ext.eps is not None
                else None
            ),
            "guidance_update": (
                sourced_str(ext.guidance_update, _LLM_SOURCE, Confidence.HIGH)
                if ext.guidance_update is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        events.append(record)
    return events
