"""Quick screen: nuclear triggers, trigger matrix, prospective checks.

Scans signal results for RED/YELLOW evaluative flags, runs 5 nuclear trigger
checks, and computes 5 prospective assessments. Phase 117-03.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.forward_looking import (
    NuclearTriggerCheck,
    ProspectiveCheck,
    QuickScreenResult,
    TriggerMatrixRow,
)
from do_uw.models.state import AnalysisState

_nuclear_config_cache: dict[str, Any] | None = None


def _load_nuclear_config() -> dict[str, Any]:
    """Load nuclear trigger definitions from brain YAML."""
    global _nuclear_config_cache
    if _nuclear_config_cache is not None:
        return _nuclear_config_cache
    config_path = (
        Path(__file__).parent.parent.parent / "brain" / "config" / "nuclear_triggers.yaml"
    )
    with open(config_path) as f:
        _nuclear_config_cache = yaml.safe_load(f)
    return _nuclear_config_cache


def _sv_val(sourced: object) -> Any:
    """Extract .value from SourcedValue, or return the raw value."""
    if hasattr(sourced, "value"):
        return sourced.value
    return sourced



def check_nuclear_triggers(state: AnalysisState) -> list[NuclearTriggerCheck]:
    """Verify 5 nuclear triggers with positive evidence against state data."""
    config = _load_nuclear_config()
    trigger_defs = config.get("nuclear_triggers", [])
    checks: list[NuclearTriggerCheck] = []

    for tdef in trigger_defs:
        trigger_id = tdef["id"]
        name = tdef["name"]
        source = tdef.get("data_source", "")
        check_type = tdef.get("check_type", "")
        evidence_fired = tdef.get("evidence_template_fired", "Trigger fired")
        evidence_clean = tdef.get("evidence_template_clean", "Clean")

        fired, evidence = _evaluate_nuclear(
            trigger_id, check_type, state, evidence_fired, evidence_clean
        )

        checks.append(
            NuclearTriggerCheck(
                trigger_id=trigger_id,
                name=name,
                fired=fired,
                evidence=evidence,
                source=source,
            )
        )

    return checks


def _evaluate_nuclear(
    trigger_id: str,
    check_type: str,
    state: AnalysisState,
    evidence_fired: str,
    evidence_clean: str,
) -> tuple[bool, str]:
    """Evaluate a single nuclear trigger. Returns (fired, evidence)."""
    if trigger_id == "NUC-01":
        return _check_active_sca(state, evidence_fired, evidence_clean)
    if trigger_id == "NUC-02":
        return _check_sec_enforcement(state, evidence_fired, evidence_clean)
    if trigger_id == "NUC-03":
        return _check_restatement(state, evidence_fired, evidence_clean)
    if trigger_id == "NUC-04":
        return _check_departure(state, evidence_fired, evidence_clean)
    if trigger_id == "NUC-05":
        return _check_going_concern(state, evidence_fired, evidence_clean)
    return (False, evidence_clean)


def _check_active_sca(
    state: AnalysisState, tmpl_fired: str, tmpl_clean: str
) -> tuple[bool, str]:
    if state.extracted and state.extracted.litigation:
        scas = state.extracted.litigation.securities_class_actions
        if scas:
            names = []
            for c in scas[:3]:
                cn = c.case_name
                if cn is not None:
                    names.append(str(_sv_val(cn)))
            detail = ", ".join(names) if names else "active SCA"
            return (True, tmpl_fired.replace("{case_details}", detail))
    return (False, tmpl_clean)


def _check_sec_enforcement(
    state: AnalysisState, tmpl_fired: str, tmpl_clean: str
) -> tuple[bool, str]:
    if state.extracted and state.extracted.litigation:
        sec = state.extracted.litigation.sec_enforcement
        if sec and sec.actions:
            detail = f"{len(sec.actions)} action(s)"
            return (True, tmpl_fired.replace("{action_details}", detail))
    return (False, tmpl_clean)


def _check_restatement(
    state: AnalysisState, tmpl_fired: str, tmpl_clean: str
) -> tuple[bool, str]:
    """NUC-03: Financial Restatement.

    Fires only on POSITIVE evidence of actual restatement or material weakness.
    Does NOT fire on Beneish M-Score or other accounting quality signals alone —
    those are risk indicators, not confirmed restatements. Mirrors CRF-5 logic.
    """
    if not state.extracted or not state.extracted.financials:
        return (False, tmpl_clean)
    audit = state.extracted.financials.audit

    # 1. Check for actual restatements (same logic as CRF-5 _check_recent_restatement)
    if audit and audit.restatements:
        for rst in audit.restatements:
            rst_dict = rst.value
            rst_date = rst_dict.get("date", "")
            desc = rst_dict.get("description", rst_dict.get("reason", "Restatement disclosed"))
            detail = f"{desc} ({rst_date})" if rst_date else str(desc)
            return (True, tmpl_fired.replace("{restatement_details}", detail))

    # 2. Check for material weaknesses in internal controls
    if audit and hasattr(audit, "material_weaknesses"):
        mws = audit.material_weaknesses
        if isinstance(mws, list) and mws:
            return (True, tmpl_fired.replace("{restatement_details}", "Material weakness identified"))

    return (False, tmpl_clean)


def _check_departure(
    state: AnalysisState, tmpl_fired: str, tmpl_clean: str
) -> tuple[bool, str]:
    if state.extracted and state.extracted.governance:
        gov = state.extracted.governance
        # Check executive departures if available
        if hasattr(gov, "executive_departures"):
            deps = gov.executive_departures
            if isinstance(deps, list) and deps:
                return (True, tmpl_fired.replace("{executive_name}", "Executive").replace(
                    "{date}", "").replace("{circumstances}", "Departure under pressure"))
    return (False, tmpl_clean)


def _check_going_concern(
    state: AnalysisState, tmpl_fired: str, tmpl_clean: str
) -> tuple[bool, str]:
    if state.extracted and state.extracted.financials:
        audit = state.extracted.financials.audit
        gc = audit.going_concern if audit else None
        if gc is not None:
            gc_val = _sv_val(gc)
            if gc_val:
                source = gc.source if hasattr(gc, "source") else ""
                evidence = tmpl_fired.replace("{auditor}", source).replace("{date}", "")
                return (True, evidence)
    return (False, tmpl_clean)


# Trigger matrix signal-to-section mapping
_PREFIX_TO_SECTION: dict[str, str] = {
    "SCAC": "Litigation",
    "LITIG": "Litigation",
    "SCA": "Litigation",
    "FIN": "Financial",
    "DIST": "Financial",
    "EARN": "Financial",
    "GOV": "Governance",
    "BOARD": "Governance",
    "MKT": "Market",
    "STOCK": "Market",
    "FWRD": "Forward-Looking",
    "REG": "Regulatory",
    "SEC": "Regulatory",
    "AI": "AI/Technology",
}

_SECTION_ANCHORS: dict[str, str] = {
    "Litigation": "#section-litigation",
    "Financial": "#section-financial",
    "Governance": "#section-governance",
    "Market": "#section-market",
    "Forward-Looking": "#section-forward-looking",
    "Regulatory": "#section-regulatory",
    "AI/Technology": "#section-ai-risk",
    "Other": "#section-summary",
}

# Content types that belong in trigger matrix (evaluative, not display)
_EVALUATIVE_TYPES = {"EVALUATIVE_CHECK", "EVALUATIVE_METRIC", "INFERENCE"}


def _signal_to_section(signal_id: str) -> str:
    """Map a signal ID to its worksheet section."""
    prefix = signal_id.split(".")[0] if "." in signal_id else signal_id
    return _PREFIX_TO_SECTION.get(prefix, "Other")


def build_trigger_matrix(signal_results: dict[str, Any]) -> list[TriggerMatrixRow]:
    """Aggregate RED/YELLOW evaluative signals into trigger matrix.

    Filters to evaluative/inference signals, groups by section, limits to
    top 3 per section, sorts RED before YELLOW.
    """
    # Collect qualifying rows
    section_rows: dict[str, list[TriggerMatrixRow]] = defaultdict(list)

    for signal_id, raw in signal_results.items():
        if not isinstance(raw, dict):
            continue

        status = raw.get("status", "")
        if status != "TRIGGERED":
            continue

        threshold_level = raw.get("threshold_level", "")
        if threshold_level not in ("red", "yellow"):
            continue

        content_type = raw.get("content_type", "")
        if content_type not in _EVALUATIVE_TYPES:
            continue

        section = _signal_to_section(signal_id)
        flag = "RED" if threshold_level == "red" else "YELLOW"
        anchor = _SECTION_ANCHORS.get(section, "#section-summary")

        row = TriggerMatrixRow(
            signal_id=signal_id,
            signal_name=raw.get("signal_name", signal_id),
            flag_level=flag,
            section=section,
            section_anchor=anchor,
            do_context=raw.get("do_context", ""),
        )
        section_rows[section].append(row)

    # Sort each section: RED first, then by signal_id; limit to top 3
    all_rows: list[TriggerMatrixRow] = []
    for section in sorted(section_rows.keys()):
        rows = sorted(
            section_rows[section],
            key=lambda r: (0 if r.flag_level == "RED" else 1, r.signal_id),
        )
        all_rows.extend(rows[:3])

    # Final sort: RED first, then YELLOW, then signal_id
    all_rows.sort(key=lambda r: (0 if r.flag_level == "RED" else 1, r.signal_id))
    return all_rows



def compute_prospective_checks(state: AnalysisState) -> list[ProspectiveCheck]:
    """Compute 5 forward-looking prospective checks with traffic light status."""
    return [
        _check_earnings_expectations(state),
        _check_major_deal(state),
        _check_regulatory_decision(state),
        _check_competitive_disruption(state),
        _check_macro_headwinds(state),
    ]


def _check_earnings_expectations(state: AnalysisState) -> ProspectiveCheck:
    finding = ""
    status = "UNKNOWN"
    source = ""
    if state.extracted and state.extracted.market:
        eg = state.extracted.market.earnings_guidance
        if eg and hasattr(eg, "quarters") and eg.quarters:
            recent_misses = sum(
                1 for q in eg.quarters[-4:]
                if hasattr(q, "result") and str(getattr(q, "result", "")) == "MISS"
            )
            if recent_misses >= 2:
                status = "RED"
                finding = f"{recent_misses} misses in last 4 quarters"
            elif recent_misses == 1:
                status = "YELLOW"
                finding = f"{recent_misses} miss in last 4 quarters"
            else:
                status = "GREEN"
                finding = "Meeting or beating expectations"
            source = "yfinance earnings data"
    return ProspectiveCheck(
        check_name="Earnings Expectations",
        finding=finding,
        status=status,
        source=source,
    )


def _check_major_deal(state: AnalysisState) -> ProspectiveCheck:
    finding = ""
    status = "UNKNOWN"
    if state.forward_looking and state.forward_looking.catalysts:
        deal_cats = [c for c in state.forward_looking.catalysts if "M&A" in c.event or "acquisition" in c.event.lower()]
        if deal_cats:
            status = "YELLOW"
            finding = f"{len(deal_cats)} pending deal catalyst(s)"
        else:
            status = "GREEN"
            finding = "No major pending deals identified"
    return ProspectiveCheck(
        check_name="Major Contract/Deal",
        finding=finding,
        status=status,
        source="10-K/8-K extraction",
    )


def _check_regulatory_decision(state: AnalysisState) -> ProspectiveCheck:
    finding = ""
    status = "UNKNOWN"
    if state.acquired_data and state.acquired_data.regulatory_data:
        reg = state.acquired_data.regulatory_data
        if isinstance(reg, dict) and reg:
            status = "YELLOW"
            finding = "Regulatory data present -- review pending decisions"
        else:
            status = "GREEN"
            finding = "No pending regulatory decisions"
    return ProspectiveCheck(
        check_name="Regulatory Decision",
        finding=finding,
        status=status,
        source="Regulatory data",
    )


def _check_competitive_disruption(state: AnalysisState) -> ProspectiveCheck:
    return ProspectiveCheck(
        check_name="Competitive Disruption",
        finding="",
        status="UNKNOWN",
        source="Sector classification",
    )


def _check_macro_headwinds(state: AnalysisState) -> ProspectiveCheck:
    finding = ""
    status = "UNKNOWN"
    if state.acquired_data and state.acquired_data.blind_spot_results:
        bsr = state.acquired_data.blind_spot_results
        if isinstance(bsr, dict) and bsr:
            status = "YELLOW"
            finding = "Blind spot search identified macro concerns"
        else:
            status = "GREEN"
            finding = "No significant macro headwinds detected"
    return ProspectiveCheck(
        check_name="Macro Headwinds",
        finding=finding,
        status=status,
        source="Web search blind spots",
    )



def build_quick_screen(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> QuickScreenResult:
    """Assemble all quick screen components into QuickScreenResult."""
    trigger_matrix = build_trigger_matrix(signal_results)
    nuclear_triggers = check_nuclear_triggers(state)
    prospective_checks = compute_prospective_checks(state)

    return QuickScreenResult(
        trigger_matrix=trigger_matrix,
        nuclear_triggers=nuclear_triggers,
        nuclear_fired_count=sum(1 for nt in nuclear_triggers if nt.fired),
        prospective_checks=prospective_checks,
        red_count=sum(1 for r in trigger_matrix if r.flag_level == "RED"),
        yellow_count=sum(1 for r in trigger_matrix if r.flag_level == "YELLOW"),
    )


__all__ = [
    "build_quick_screen",
    "build_trigger_matrix",
    "check_nuclear_triggers",
    "compute_prospective_checks",
]
