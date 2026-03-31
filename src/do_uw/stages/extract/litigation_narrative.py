"""Litigation summary narrative, timeline events, and matter counting.

Split from extract_litigation.py for 500-line compliance.  Provides
rule-based litigation summary synthesis, chronological timeline
construction from case dates, and active/historical matter counts.

All functions are public (no underscore prefix) because they are
called from extract_litigation.py's run_litigation_extractors().
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import (
    DealLitigation,
    LitigationTimelineEvent,
    RegulatoryProceeding,
)

# ------------------------------------------------------------------
# Litigation summary generation
# ------------------------------------------------------------------


def generate_litigation_summary(
    landscape: LitigationLandscape,
) -> SourcedValue[str]:
    """Generate rule-based litigation summary from 5 dimensions.

    Synthesizes:
    1. Active matters count and severity
    2. Historical litigation pattern
    3. Regulatory pipeline position
    4. Defense posture
    5. Emerging exposure (industry patterns + SOL windows)

    Returns a SourcedValue[str] with LOW confidence since this is
    derived from other extracted data (not directly from filings).
    """
    parts: list[str] = []

    _add_active_matters_summary(parts, landscape)
    _add_historical_pattern_summary(parts, landscape)
    _add_regulatory_pipeline_summary(parts, landscape)
    _add_defense_summary(parts, landscape)
    _add_emerging_exposure_summary(parts, landscape)

    narrative = " ".join(parts) if parts else (
        "Insufficient litigation data available to generate a "
        "comprehensive assessment."
    )

    return SourcedValue[str](
        value=narrative,
        source="Rule-based synthesis of litigation extraction results",
        confidence=Confidence.LOW,
        as_of=datetime.now(tz=UTC),
    )


def _add_active_matters_summary(
    parts: list[str], landscape: LitigationLandscape
) -> None:
    """Add active matters count and type sentence."""
    active_scas = sum(
        1 for c in landscape.securities_class_actions
        if c.status and c.status.value == "ACTIVE"
    )
    active_derivs = sum(
        1 for c in landscape.derivative_suits
        if c.status and c.status.value == "ACTIVE"
    )
    active_reg = _count_active_regulatory(landscape)

    matter_parts: list[str] = []
    if active_scas > 0:
        matter_parts.append(f"{active_scas} securities class action(s)")
    if active_derivs > 0:
        matter_parts.append(f"{active_derivs} derivative suit(s)")
    if active_reg > 0:
        matter_parts.append(f"{active_reg} regulatory proceeding(s)")

    if matter_parts:
        parts.append(
            f"Active litigation includes {', '.join(matter_parts)}."
        )
    else:
        parts.append("No active litigation matters identified.")


def _add_historical_pattern_summary(
    parts: list[str], landscape: LitigationLandscape
) -> None:
    """Add historical litigation pattern sentence."""
    total_cases = (
        len(landscape.securities_class_actions)
        + len(landscape.derivative_suits)
    )
    settled = sum(
        1 for c in landscape.securities_class_actions
        if c.status and c.status.value == "SETTLED"
    ) + sum(
        1 for c in landscape.derivative_suits
        if c.status and c.status.value == "SETTLED"
    )

    if total_cases > 0:
        parts.append(
            f"Historical litigation activity shows {total_cases} "
            f"case(s) with {settled} settlement(s)."
        )


def _add_regulatory_pipeline_summary(
    parts: list[str], landscape: LitigationLandscape
) -> None:
    """Add regulatory pipeline position sentence."""
    enf = landscape.sec_enforcement
    stage = "NONE"
    if enf.highest_confirmed_stage and enf.highest_confirmed_stage.value:
        stage = enf.highest_confirmed_stage.value
    elif enf.pipeline_position and enf.pipeline_position.value:
        stage = enf.pipeline_position.value

    sweep = "not detected"
    if enf.industry_sweep_detected and enf.industry_sweep_detected.value:
        sweep = "detected"

    parts.append(
        f"SEC enforcement pipeline position: {stage}. "
        f"Industry sweep {sweep}."
    )


def _add_defense_summary(
    parts: list[str], landscape: LitigationLandscape
) -> None:
    """Add defense posture sentence."""
    defense = landscape.defense
    strength = "UNKNOWN"
    if (
        defense.overall_defense_strength
        and defense.overall_defense_strength.value
    ):
        strength = defense.overall_defense_strength.value

    detail_parts: list[str] = []
    if (
        defense.forum_provisions.has_federal_forum
        and defense.forum_provisions.has_federal_forum.value
    ):
        detail_parts.append("federal forum provision")
    if (
        defense.pslra_safe_harbor_usage
        and defense.pslra_safe_harbor_usage.value
    ):
        detail_parts.append(
            f"PSLRA safe harbor ({defense.pslra_safe_harbor_usage.value})"
        )

    detail = f" with {', '.join(detail_parts)}" if detail_parts else ""
    parts.append(f"Defense strength assessed as {strength}{detail}.")


def _add_emerging_exposure_summary(
    parts: list[str], landscape: LitigationLandscape
) -> None:
    """Add emerging exposure sentence."""
    exposed_patterns = [
        p for p in landscape.industry_patterns
        if p.this_company_exposed and p.this_company_exposed.value
    ]
    open_windows = sum(1 for w in landscape.sol_map if w.window_open)

    if exposed_patterns:
        theories = [
            p.legal_theory.value
            for p in exposed_patterns
            if p.legal_theory and p.legal_theory.value
        ]
        theory_str = ", ".join(theories[:3]) if theories else "various"
        parts.append(
            f"Industry claim patterns suggest exposure to {theory_str}."
        )

    if open_windows > 0:
        parts.append(f"{open_windows} open SOL window(s).")


# ------------------------------------------------------------------
# Timeline event construction
# ------------------------------------------------------------------


def build_timeline_events(
    landscape: LitigationLandscape,
) -> list[LitigationTimelineEvent]:
    """Build chronological timeline from all extracted litigation data.

    Collects events from SCAs, settlements, SEC enforcement, and
    regulatory proceedings. Sorted by date descending (most recent
    first).
    """
    events: list[LitigationTimelineEvent] = []

    _collect_sca_events(events, landscape.securities_class_actions)
    _collect_enforcement_events(events, landscape.sec_enforcement)
    _collect_regulatory_events(events, landscape)
    _collect_deal_events(events, landscape.deal_litigation)

    # Sort by date descending, None dates last
    events.sort(
        key=lambda e: e.event_date or date.min,
        reverse=True,
    )
    return events


def _make_event_sourced(
    value: str, source: str,
) -> SourcedValue[str]:
    """Create a MEDIUM-confidence SourcedValue for timeline events."""
    return SourcedValue[str](
        value=value,
        source=source,
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def _collect_sca_events(
    events: list[LitigationTimelineEvent],
    cases: list[CaseDetail],
) -> None:
    """Collect SCA filing and settlement events."""
    for case in cases:
        if case.filing_date and case.filing_date.value:
            name = (
                case.case_name.value if case.case_name else "Unknown SCA"
            )
            events.append(LitigationTimelineEvent(
                event_date=case.filing_date.value,
                event_type=_make_event_sourced("case_filing", "SCA"),
                description=_make_event_sourced(
                    f"SCA filed: {name}", "SCA extractor",
                ),
            ))

        if (
            case.settlement_amount
            and case.settlement_amount.value
            and case.status
            and case.status.value == "SETTLED"
        ):
            name = (
                case.case_name.value if case.case_name else "Unknown SCA"
            )
            settle_date = (
                case.filing_date.value if case.filing_date else None
            )
            events.append(LitigationTimelineEvent(
                event_date=settle_date,
                event_type=_make_event_sourced("settlement", "SCA"),
                description=_make_event_sourced(
                    f"Settlement: {name} "
                    f"(${case.settlement_amount.value:,.0f})",
                    "SCA extractor",
                ),
            ))


def _collect_enforcement_events(
    events: list[LitigationTimelineEvent],
    enforcement: SECEnforcementPipeline,
) -> None:
    """Collect SEC enforcement action events."""
    for action in enforcement.actions:
        if not action.value:
            continue
        action_dict = action.value
        action_date_str = action_dict.get("date")
        event_date: date | None = None
        if action_date_str:
            try:
                event_date = date.fromisoformat(action_date_str)
            except ValueError:
                pass

        desc = action_dict.get("description", "SEC enforcement action")
        events.append(LitigationTimelineEvent(
            event_date=event_date,
            event_type=_make_event_sourced(
                "enforcement_action", "SEC enforcement",
            ),
            description=_make_event_sourced(desc, "SEC enforcement"),
        ))


def _collect_regulatory_events(
    events: list[LitigationTimelineEvent],
    landscape: LitigationLandscape,
) -> None:
    """Collect regulatory proceeding events.

    Handles RegulatoryProceeding objects stored at runtime despite
    the Phase 3 field type being list[SourcedValue[dict[str, str]]].
    Uses cast() to satisfy pyright while handling both types.
    """
    for proc_raw in landscape.regulatory_proceedings:
        event_date: date | None = None
        desc = "Regulatory proceeding"

        # At runtime, proc is RegulatoryProceeding (Phase 5 extractor)
        proc = cast(Any, proc_raw)
        if isinstance(proc, RegulatoryProceeding):
            if proc.date_initiated and proc.date_initiated.value:
                event_date = proc.date_initiated.value
            if proc.description and proc.description.value:
                desc = proc.description.value
        elif hasattr(proc, "value") and hasattr(proc.value, "get"):
            date_str = proc.value.get("date")
            if date_str:
                try:
                    event_date = date.fromisoformat(str(date_str))
                except ValueError:
                    pass
            desc = str(proc.value.get("description", desc))

        events.append(LitigationTimelineEvent(
            event_date=event_date,
            event_type=_make_event_sourced("regulatory", "Regulatory"),
            description=_make_event_sourced(desc, "Regulatory extractor"),
        ))


def _collect_deal_events(
    events: list[LitigationTimelineEvent],
    deals: list[DealLitigation],
) -> None:
    """Collect deal litigation events."""
    for deal in deals:
        if deal.filing_date and deal.filing_date.value:
            name = deal.deal_name.value if deal.deal_name else "Deal"
            events.append(LitigationTimelineEvent(
                event_date=deal.filing_date.value,
                event_type=_make_event_sourced(
                    "case_filing", "Deal litigation",
                ),
                description=_make_event_sourced(
                    f"Deal litigation filed: {name}",
                    "Deal litigation extractor",
                ),
            ))


# ------------------------------------------------------------------
# Matter counting
# ------------------------------------------------------------------


def count_active_matters(
    landscape: LitigationLandscape,
) -> SourcedValue[int]:
    """Count currently active litigation matters across all categories."""
    count = 0
    count += sum(
        1 for c in landscape.securities_class_actions
        if c.status and c.status.value == "ACTIVE"
    )
    count += sum(
        1 for c in landscape.derivative_suits
        if c.status and c.status.value == "ACTIVE"
    )
    count += _count_active_regulatory(landscape)

    return SourcedValue[int](
        value=count,
        source="Aggregated from all SECT6 extractor results",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def count_historical_matters(
    landscape: LitigationLandscape,
) -> SourcedValue[int]:
    """Count historical (resolved) litigation matters."""
    count = 0
    count += sum(
        1 for c in landscape.securities_class_actions
        if c.status and c.status.value in ("SETTLED", "DISMISSED")
    )
    count += sum(
        1 for c in landscape.derivative_suits
        if c.status and c.status.value in ("SETTLED", "DISMISSED")
    )

    return SourcedValue[int](
        value=count,
        source="Aggregated from all SECT6 extractor results",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def _count_active_regulatory(landscape: LitigationLandscape) -> int:
    """Count active regulatory proceedings (handles both model types)."""
    count = 0
    for proc_raw in landscape.regulatory_proceedings:
        proc = cast(Any, proc_raw)
        if isinstance(proc, RegulatoryProceeding):
            if proc.status and proc.status.value:
                if proc.status.value.upper() in ("ACTIVE", "INVESTIGATION"):
                    count += 1
        elif hasattr(proc, "value") and hasattr(proc.value, "get"):
            status = str(proc.value.get("status", ""))
            if status.upper() in ("ACTIVE", "INVESTIGATION"):
                count += 1
    return count
