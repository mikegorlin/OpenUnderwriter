"""8-K event converter extensions: additional Item converters.

Split from eight_k_converter.py for 500-line compliance.

Covers Items not in the original converter:
- Item 1.02: Termination of Material Definitive Agreement
- Item 2.05: Costs Associated with Exit/Disposal Activities
- Item 2.06: Material Impairments
- Item 4.01: Changes in Certifying Accountant
- Item 5.03: Amendments to Articles/Bylaws
- Item 5.05: Code of Ethics Changes/Waivers

Public functions:
- convert_terminations     -> list of termination dicts (Item 1.02)
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


def _sourced_bool(value: bool) -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with 8-K LLM source and HIGH confidence."""
    return SourcedValue[bool](
        value=value,
        source=_LLM_SOURCE,
        confidence=Confidence.HIGH,
        as_of=now(),
    )


# Type aliases for record dicts.
TerminationRecord = dict[str, SourcedValue[str] | None]
RestructuringRecord = dict[str, SourcedValue[str] | SourcedValue[float] | None]
ImpairmentRecord = dict[str, SourcedValue[str] | SourcedValue[float] | None]
AuditorChangeRecord = dict[str, SourcedValue[str] | SourcedValue[bool] | None]
BylawsRecord = dict[str, SourcedValue[str] | None]
EthicsChangeRecord = dict[str, SourcedValue[str] | None]


# ------------------------------------------------------------------
# Agreement termination events (Item 1.02)
# ------------------------------------------------------------------


def convert_terminations(
    extractions: list[EightKExtraction],
) -> list[TerminationRecord]:
    """Aggregate agreement termination events across multiple 8-K filings.

    Includes 8-Ks where ``terminated_agreement`` is not None.
    """
    results: list[TerminationRecord] = []
    for ext in extractions:
        if ext.terminated_agreement is None:
            continue
        record: TerminationRecord = {
            "agreement": sourced_str(
                ext.terminated_agreement, _LLM_SOURCE, Confidence.HIGH
            ),
            "reason": (
                sourced_str(ext.termination_reason, _LLM_SOURCE, Confidence.HIGH)
                if ext.termination_reason is not None
                else None
            ),
            "counterparty": (
                sourced_str(
                    ext.termination_counterparty, _LLM_SOURCE, Confidence.HIGH
                )
                if ext.termination_counterparty is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results


# ------------------------------------------------------------------
# Restructuring events (Item 2.05)
# ------------------------------------------------------------------


def convert_restructurings(
    extractions: list[EightKExtraction],
) -> list[RestructuringRecord]:
    """Aggregate restructuring/exit cost events across multiple 8-K filings.

    Includes 8-Ks where ``restructuring_type`` is not None.
    """
    results: list[RestructuringRecord] = []
    for ext in extractions:
        if ext.restructuring_type is None:
            continue
        record: RestructuringRecord = {
            "type": sourced_str(
                ext.restructuring_type, _LLM_SOURCE, Confidence.HIGH
            ),
            "charge": (
                sourced_float(ext.restructuring_charge, _LLM_SOURCE, Confidence.HIGH)
                if ext.restructuring_charge is not None
                else None
            ),
            "description": (
                sourced_str(
                    ext.restructuring_description, _LLM_SOURCE, Confidence.HIGH
                )
                if ext.restructuring_description is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results


# ------------------------------------------------------------------
# Impairment events (Item 2.06)
# ------------------------------------------------------------------


def convert_impairments(
    extractions: list[EightKExtraction],
) -> list[ImpairmentRecord]:
    """Aggregate material impairment events across multiple 8-K filings.

    Includes 8-Ks where ``impairment_type`` is not None.
    """
    results: list[ImpairmentRecord] = []
    for ext in extractions:
        if ext.impairment_type is None:
            continue
        record: ImpairmentRecord = {
            "type": sourced_str(
                ext.impairment_type, _LLM_SOURCE, Confidence.HIGH
            ),
            "amount": (
                sourced_float(ext.impairment_amount, _LLM_SOURCE, Confidence.HIGH)
                if ext.impairment_amount is not None
                else None
            ),
            "description": (
                sourced_str(
                    ext.impairment_description, _LLM_SOURCE, Confidence.HIGH
                )
                if ext.impairment_description is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results


# ------------------------------------------------------------------
# Auditor change events (Item 4.01)
# ------------------------------------------------------------------


def convert_auditor_changes(
    extractions: list[EightKExtraction],
) -> list[AuditorChangeRecord]:
    """Aggregate auditor change events across multiple 8-K filings.

    Includes 8-Ks where ``former_auditor`` or ``new_auditor`` is not None.
    """
    results: list[AuditorChangeRecord] = []
    for ext in extractions:
        if ext.former_auditor is None and ext.new_auditor is None:
            continue
        record: AuditorChangeRecord = {
            "former_auditor": (
                sourced_str(ext.former_auditor, _LLM_SOURCE, Confidence.HIGH)
                if ext.former_auditor is not None
                else None
            ),
            "new_auditor": (
                sourced_str(ext.new_auditor, _LLM_SOURCE, Confidence.HIGH)
                if ext.new_auditor is not None
                else None
            ),
            "disagreements": (
                _sourced_bool(ext.auditor_disagreements)
                if ext.auditor_disagreements is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results


# ------------------------------------------------------------------
# Bylaws amendment events (Item 5.03)
# ------------------------------------------------------------------


def convert_bylaws_changes(
    extractions: list[EightKExtraction],
) -> list[BylawsRecord]:
    """Aggregate bylaws/articles amendment events across multiple 8-K filings.

    Includes 8-Ks where ``bylaws_amendment_type`` is not None.
    """
    results: list[BylawsRecord] = []
    for ext in extractions:
        if ext.bylaws_amendment_type is None:
            continue
        record: BylawsRecord = {
            "type": sourced_str(
                ext.bylaws_amendment_type, _LLM_SOURCE, Confidence.HIGH
            ),
            "summary": (
                sourced_str(
                    ext.bylaws_amendment_summary, _LLM_SOURCE, Confidence.HIGH
                )
                if ext.bylaws_amendment_summary is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results


# ------------------------------------------------------------------
# Ethics code change events (Item 5.05)
# ------------------------------------------------------------------


def convert_ethics_changes(
    extractions: list[EightKExtraction],
) -> list[EthicsChangeRecord]:
    """Aggregate code of ethics changes/waivers across multiple 8-K filings.

    Includes 8-Ks where ``ethics_change_type`` is not None.
    """
    results: list[EthicsChangeRecord] = []
    for ext in extractions:
        if ext.ethics_change_type is None:
            continue
        record: EthicsChangeRecord = {
            "type": sourced_str(
                ext.ethics_change_type, _LLM_SOURCE, Confidence.HIGH
            ),
            "person": (
                sourced_str(ext.ethics_change_person, _LLM_SOURCE, Confidence.HIGH)
                if ext.ethics_change_person is not None
                else None
            ),
            "summary": (
                sourced_str(ext.ethics_change_summary, _LLM_SOURCE, Confidence.HIGH)
                if ext.ethics_change_summary is not None
                else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date is not None
                else None
            ),
        }
        results.append(record)
    return results
