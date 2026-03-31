"""Signal result model and aggregation helpers for the ANALYZE stage.

Provides:
- SignalStatus: Three-state evaluation enum plus INFO for informational signals
- SignalCategory, PlaintiffLens, SignalType, HazardOrSignal: Classification enums
- SignalResult: Pydantic model capturing evaluation outcome with provenance
- aggregate_results: Summarize a list of SignalResults into counts
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataStatus(StrEnum):
    """Data pipeline status for a signal.

    Three-state data provenance tracking -- distinguishes "we evaluated and
    found something" from "we couldn't evaluate" from "signal doesn't apply."

    EVALUATED: Data acquired, signal ran, result produced.
    DATA_UNAVAILABLE: Signal exists but required data was not acquired.
    NOT_APPLICABLE: Signal genuinely doesn't apply to this company type.
    """

    EVALUATED = "EVALUATED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SignalStatus(StrEnum):
    """Evaluation outcome for a single signal.

    Three-state evaluation (TRIGGERED/CLEAR/SKIPPED) plus INFO for
    informational-only signals that report values without pass/fail.

    TRIGGERED: Threshold breached -- risk signal detected
    CLEAR: Threshold not breached -- no issue
    SKIPPED: Required data unavailable -- cannot evaluate
    INFO: Informational value reported (no pass/fail threshold)
    """

    TRIGGERED = "TRIGGERED"
    CLEAR = "CLEAR"
    SKIPPED = "SKIPPED"
    INFO = "INFO"


class SignalCategory(StrEnum):
    """Classification category for a signal's role in underwriting.

    Controlled vocabulary -- every signal must have exactly one category.

    DECISION_DRIVING: Changes tier assignment, triggers CRF, or materially
        affects the underwriting decision. These are SCORED (factors non-empty).
    CONTEXT_DISPLAY: Useful information always displayed but NOT scored.
        Provides context for the underwriter without influencing factors.
    FUTURE_RESEARCH: Valuable signals blocked by data source constraints.
        Stubbed for implementation when data becomes available.
    """

    DECISION_DRIVING = "DECISION_DRIVING"
    CONTEXT_DISPLAY = "CONTEXT_DISPLAY"
    FUTURE_RESEARCH = "FUTURE_RESEARCH"


class PlaintiffLens(StrEnum):
    """Plaintiff perspective that a signal evaluates risk for.

    Faceted classification dimension -- each signal maps to one or more
    lenses representing "who sues" analysis.
    """

    SHAREHOLDERS = "SHAREHOLDERS"
    REGULATORS = "REGULATORS"
    CUSTOMERS = "CUSTOMERS"
    COMPETITORS = "COMPETITORS"
    EMPLOYEES = "EMPLOYEES"
    CREDITORS = "CREDITORS"
    GOVERNMENT = "GOVERNMENT"


class SignalType(StrEnum):
    """Type of signal detected.

    Faceted classification dimension -- independent of category and lens.

    LEVEL: Point-in-time financial metric (e.g., current ratio)
    DELTA: Change-based measurement (e.g., stock price decline)
    PATTERN: Multi-signal behavioral pattern
    FORENSIC: Accounting manipulation detection model
    NLP: Natural language processing signal
    STRUCTURAL: Persistent company characteristic
    EVENT: Discrete occurrence (lawsuit filed, enforcement action)
    """

    LEVEL = "LEVEL"
    DELTA = "DELTA"
    PATTERN = "PATTERN"
    FORENSIC = "FORENSIC"
    NLP = "NLP"
    STRUCTURAL = "STRUCTURAL"
    EVENT = "EVENT"


class HazardOrSignal(StrEnum):
    """Whether the signal measures a persistent condition or transient evidence.

    HAZARD: Persistent structural condition (what IS the company).
    SIGNAL: Transient behavioral evidence (what the company is DOING).
    PERIL_CONFIRMING: Lawsuit or enforcement already filed.
    """

    HAZARD = "HAZARD"
    SIGNAL = "SIGNAL"
    PERIL_CONFIRMING = "PERIL_CONFIRMING"


class SignalResult(BaseModel):
    """Result of evaluating a single signal against extracted data.

    Every signal produces exactly one SignalResult. The engine never
    silently drops signals -- if data is missing, status is SKIPPED.
    """

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(description="Unique signal identifier (e.g., 'FIN.LIQ.position')")
    signal_name: str = Field(description="Human-readable signal name")
    status: SignalStatus = Field(description="Evaluation outcome")
    value: str | float | None = Field(
        default=None,
        description="The data value that was evaluated (for evidence trail)",
    )
    threshold_level: str = Field(
        default="",
        description="Which threshold was hit: 'red', 'yellow', 'clear', or '' for non-tiered",
    )
    evidence: str = Field(
        default="",
        description="Human-readable explanation of the evaluation result",
    )
    source: str = Field(
        default="",
        description="Data source that provided the evaluated value",
    )
    confidence: str = Field(
        default="MEDIUM",
        description=(
            "Confidence level for this signal result: "
            "HIGH (audited/official), MEDIUM (unaudited/estimated), "
            "LOW (web-derived/gap search). "
            "Set to LOW by gap search re-evaluator for WEB (gap) sourced results."
        ),
    )
    threshold_context: str = Field(
        default="",
        description=(
            "Human-readable threshold criterion from brain YAML that was triggered. "
            "Format: '{level}: {criterion text}', e.g. 'red: Average tenure >15 years (entrenchment risk)'. "
            "Populated by _apply_traceability() when status=TRIGGERED. "
            "Empty for CLEAR, SKIPPED, and INFO results."
        ),
    )
    factors: list[str] = Field(
        default_factory=lambda: [],
        description="Scoring factors this signal maps to (e.g., ['F1', 'F2'])",
    )
    section: int = Field(
        default=0,
        description="Worksheet section this signal belongs to (1-6)",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured evaluation data for composites to read. "
            "Contains rich data computed during evaluation that would "
            "otherwise be discarded after threshold comparison. "
            "Example: stock drop events with date, drop_pct, trigger info."
        ),
    )
    do_context: str = Field(
        default="",
        description=(
            "Rendered D&O commentary string from brain YAML do_context template. "
            "Populated by do_context_engine after signal evaluation in ANALYZE. "
            "Consumed as-is by context builders -- no evaluative logic downstream."
        ),
    )
    needs_calibration: bool = Field(
        default=False,
        description="Whether threshold values are configurable (per SECT7-11)",
    )
    annotations: list[str] = Field(
        default_factory=list,
        description=(
            "Contextual validation annotations added post-ANALYZE. "
            "Provide explanatory context for triggered signals "
            "that may be false positives given company state. "
            "NEVER used to suppress -- only to inform the underwriter."
        ),
    )

    # Phase 27 data pipeline status fields -- backward-compatible defaults
    data_status: str = Field(
        default="EVALUATED",
        description="Data pipeline status: EVALUATED, DATA_UNAVAILABLE, NOT_APPLICABLE",
    )
    data_status_reason: str = Field(
        default="",
        description="Why data is unavailable or not applicable",
    )

    # Phase 35 content_type propagation -- enables display dispatch in RENDER
    content_type: str = Field(
        default="EVALUATIVE_CHECK",
        description="Content type: EVALUATIVE_CHECK, MANAGEMENT_DISPLAY, or INFERENCE_PATTERN",
    )

    # Phase 26 classification fields -- all optional with backward-compatible defaults
    category: str = Field(
        default="",
        description="Signal category: DECISION_DRIVING, CONTEXT_DISPLAY, or FUTURE_RESEARCH",
    )
    plaintiff_lenses: list[str] = Field(
        default_factory=lambda: [],
        description="Plaintiff perspectives: SHAREHOLDERS, REGULATORS, CUSTOMERS, etc.",
    )
    signal_type: str = Field(
        default="",
        description="Signal type: LEVEL, DELTA, PATTERN, FORENSIC, NLP, STRUCTURAL, EVENT",
    )
    hazard_or_signal: str = Field(
        default="",
        description="HAZARD (persistent condition), SIGNAL (transient evidence), PERIL_CONFIRMING",
    )
    temporal_classification: str = Field(
        default="",
        description="For temporal signals: IMPROVING, STABLE, DETERIORATING, CRITICAL",
    )

    # Phase 30 traceability chain (5 links)
    trace_data_source: str = Field(
        default="",
        description="Link 1: Where data came from (e.g., 'SEC_10K:item_7_mda')",
    )
    trace_extraction: str = Field(
        default="",
        description="Link 2: Which extraction produced the value (e.g., 'xbrl_extractor')",
    )
    trace_evaluation: str = Field(
        default="",
        description="Link 3: Evaluation method (e.g., 'tiered_threshold:red>25%')",
    )
    trace_output: str = Field(
        default="",
        description="Link 4: Where result appears in worksheet (e.g., 'SECT3:financial_health')",
    )
    trace_scoring: str = Field(
        default="",
        description="Link 5: How result affects score (e.g., 'F1:-3.5pts')",
    )

    @property
    def traceability_complete(self) -> bool:
        """Whether all 5 traceability links are populated."""
        return all([
            self.trace_data_source,
            self.trace_extraction,
            self.trace_evaluation,
            self.trace_output,
            self.trace_scoring,
        ])

    @property
    def traceability_gaps(self) -> list[str]:
        """Return names of missing traceability links."""
        gaps = []
        for field_name in [
            "trace_data_source",
            "trace_extraction",
            "trace_evaluation",
            "trace_output",
            "trace_scoring",
        ]:
            if not getattr(self, field_name):
                gaps.append(field_name.replace("trace_", "").upper())
        return gaps


def aggregate_results(results: list[SignalResult]) -> dict[str, int]:
    """Summarize a list of SignalResults into counts by status.

    Returns:
        Dict with keys: executed, passed (CLEAR), failed (TRIGGERED),
        skipped (SKIPPED), info (INFO).
    """
    passed = 0
    failed = 0
    skipped = 0
    info = 0

    for r in results:
        if r.status == SignalStatus.CLEAR:
            passed += 1
        elif r.status == SignalStatus.TRIGGERED:
            failed += 1
        elif r.status == SignalStatus.SKIPPED:
            skipped += 1
        elif r.status == SignalStatus.INFO:
            info += 1

    return {
        "executed": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "info": info,
    }


__all__ = [
    "SignalCategory",
    "DataStatus",
    "HazardOrSignal",
    "PlaintiffLens",
    "SignalResult",
    "SignalStatus",
    "SignalType",
    "aggregate_results",
]
