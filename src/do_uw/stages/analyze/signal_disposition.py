"""Signal disposition tagging for audit trail (Phase 78 — AUDIT-01).

Tags every brain signal with exactly one disposition after pipeline evaluation:
- TRIGGERED: Signal fired (risk detected)
- CLEAN: Signal evaluated, no issue (includes CLEAR and INFO statuses)
- SKIPPED: Signal not evaluated, with categorized reason
- INACTIVE: Signal lifecycle is inactive/deprecated

Zero unaccounted signals: every signal in the brain gets a disposition.

Exports:
    DispositionTag, SkipReason, SignalDisposition, DispositionSummary, build_dispositions
"""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DispositionTag(StrEnum):
    """Disposition outcome for a brain signal."""

    TRIGGERED = "TRIGGERED"
    CLEAN = "CLEAN"
    SKIPPED = "SKIPPED"
    INACTIVE = "INACTIVE"


class SkipReason(StrEnum):
    """Categorized reason for a SKIPPED disposition."""

    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_MAPPER = "NO_MAPPER"
    EXTRACTION_GAP = "EXTRACTION_GAP"
    NOT_AUTO_EVALUATED = "NOT_AUTO_EVALUATED"
    FOUNDATIONAL = "FOUNDATIONAL"
    FEATURE_GATED = "FEATURE_GATED"
    DEFERRED = "DEFERRED"


class SignalDisposition(BaseModel):
    """Disposition record for a single brain signal."""

    model_config = ConfigDict(frozen=False)

    signal_id: str
    signal_name: str
    disposition: DispositionTag
    skip_reason: SkipReason | None = None
    skip_detail: str = ""
    section_prefix: str = ""
    evidence: str = ""


class DispositionSummary(BaseModel):
    """Aggregate disposition summary for all brain signals."""

    model_config = ConfigDict(frozen=False)

    total: int = 0
    triggered_count: int = 0
    clean_count: int = 0
    skipped_count: int = 0
    inactive_count: int = 0
    dispositions: list[SignalDisposition] = Field(default_factory=list)
    by_section: dict[str, dict[str, int]] = Field(default_factory=dict)


def _extract_section_prefix(signal_id: str) -> str:
    """Extract the first segment of a dotted signal ID."""
    parts = signal_id.split(".")
    return parts[0] if parts else ""


def _derive_skip_reason(result: dict[str, Any]) -> tuple[SkipReason, str]:
    """Derive SkipReason from a SKIPPED signal result's data_status."""
    data_status = result.get("data_status", "")
    data_status_reason = result.get("data_status_reason", "")

    if data_status == "DEFERRED":
        return SkipReason.DEFERRED, data_status_reason or "Signal deferred: data source not yet wired"
    if data_status == "DATA_UNAVAILABLE":
        return SkipReason.DATA_UNAVAILABLE, data_status_reason or "Required data not available"
    if data_status == "NOT_APPLICABLE":
        return SkipReason.NOT_APPLICABLE, data_status_reason or "Signal not applicable to this company"

    # Fallback: use data_status_reason to infer
    reason_lower = data_status_reason.lower()
    if "mapper" in reason_lower or "no mapper" in reason_lower:
        return SkipReason.NO_MAPPER, data_status_reason
    if "feature" in reason_lower or "gated" in reason_lower:
        return SkipReason.FEATURE_GATED, data_status_reason

    return SkipReason.DATA_UNAVAILABLE, data_status_reason or "Unknown skip reason"


def _tag_signal(
    signal: dict[str, Any],
    signal_results: dict[str, Any],
) -> SignalDisposition:
    """Produce a disposition for a single brain signal."""
    signal_id = str(signal.get("id", ""))
    signal_name = str(signal.get("name", ""))
    section_prefix = _extract_section_prefix(signal_id)
    lifecycle_state = str(signal.get("lifecycle_state", "active")).lower()

    # Priority 1: Inactive/deprecated signals
    if lifecycle_state in ("inactive", "deprecated"):
        return SignalDisposition(
            signal_id=signal_id,
            signal_name=signal_name,
            disposition=DispositionTag.INACTIVE,
            section_prefix=section_prefix,
        )

    # Priority 2: Signal has an evaluation result
    result = signal_results.get(signal_id)
    if result is not None:
        status = result.get("status", "")
        evidence = result.get("evidence", "")

        if status == "TRIGGERED":
            return SignalDisposition(
                signal_id=signal_id,
                signal_name=signal_name,
                disposition=DispositionTag.TRIGGERED,
                section_prefix=section_prefix,
                evidence=evidence,
            )
        if status in ("CLEAR", "INFO"):
            return SignalDisposition(
                signal_id=signal_id,
                signal_name=signal_name,
                disposition=DispositionTag.CLEAN,
                section_prefix=section_prefix,
            )
        if status == "SKIPPED":
            skip_reason, skip_detail = _derive_skip_reason(result)
            return SignalDisposition(
                signal_id=signal_id,
                signal_name=signal_name,
                disposition=DispositionTag.SKIPPED,
                skip_reason=skip_reason,
                skip_detail=skip_detail,
                section_prefix=section_prefix,
            )

    # Priority 3: No result — classify the gap
    signal_class = str(signal.get("signal_class", "")).lower()
    if signal_class == "foundational":
        return SignalDisposition(
            signal_id=signal_id,
            signal_name=signal_name,
            disposition=DispositionTag.SKIPPED,
            skip_reason=SkipReason.FOUNDATIONAL,
            skip_detail="Foundational signal (not directly evaluated)",
            section_prefix=section_prefix,
        )

    execution_mode = str(signal.get("execution_mode", "AUTO")).upper()
    if execution_mode != "AUTO":
        return SignalDisposition(
            signal_id=signal_id,
            signal_name=signal_name,
            disposition=DispositionTag.SKIPPED,
            skip_reason=SkipReason.NOT_AUTO_EVALUATED,
            skip_detail=f"Execution mode is {execution_mode}, not AUTO",
            section_prefix=section_prefix,
        )

    # AUTO signal with no result = extraction gap
    return SignalDisposition(
        signal_id=signal_id,
        signal_name=signal_name,
        disposition=DispositionTag.SKIPPED,
        skip_reason=SkipReason.EXTRACTION_GAP,
        skip_detail="AUTO signal not evaluated (data extraction gap)",
        section_prefix=section_prefix,
    )


def build_dispositions(
    all_signals: list[dict[str, Any]],
    signal_results: dict[str, Any],
) -> DispositionSummary:
    """Tag every brain signal with a disposition.

    Args:
        all_signals: All signals from brain loader (every signal in the brain).
        signal_results: Evaluated results from state.analysis.signal_results.

    Returns:
        DispositionSummary with per-signal dispositions and aggregate counts.
    """
    dispositions: list[SignalDisposition] = []
    counts = {
        DispositionTag.TRIGGERED: 0,
        DispositionTag.CLEAN: 0,
        DispositionTag.SKIPPED: 0,
        DispositionTag.INACTIVE: 0,
    }
    by_section: dict[str, dict[str, int]] = defaultdict(
        lambda: {"triggered": 0, "clean": 0, "skipped": 0, "inactive": 0}
    )

    for signal in all_signals:
        disp = _tag_signal(signal, signal_results)
        dispositions.append(disp)
        counts[disp.disposition] += 1

        prefix = disp.section_prefix
        if prefix:
            tag_key = disp.disposition.lower()
            by_section[prefix][tag_key] += 1

    return DispositionSummary(
        total=len(dispositions),
        triggered_count=counts[DispositionTag.TRIGGERED],
        clean_count=counts[DispositionTag.CLEAN],
        skipped_count=counts[DispositionTag.SKIPPED],
        inactive_count=counts[DispositionTag.INACTIVE],
        dispositions=dispositions,
        by_section=dict(by_section),
    )


__all__ = [
    "DispositionTag",
    "DispositionSummary",
    "SignalDisposition",
    "SkipReason",
    "build_dispositions",
]
