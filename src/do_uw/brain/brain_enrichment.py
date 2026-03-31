"""Backward-compat enrichment maps and logic for BrainLoader.

Copies of enrichment constants from brain_build_signals.py and
brain_loader_rows.py. Those files are scheduled for deletion in
Plans 02/03 of Phase 53, so we own these maps here.
"""

from __future__ import annotations

from typing import Any

# work_type -> content_type mapping
_WORK_TYPE_TO_CONTENT_TYPE: dict[str, str] = {
    "extract": "MANAGEMENT_DISPLAY",
    "evaluate": "EVALUATIVE_CHECK",
    "infer": "INFERENCE_PATTERN",
}

# layer -> hazard_or_signal mapping
_LAYER_TO_HAZARD_OR_SIGNAL: dict[str, str] = {
    "hazard": "HAZARD",
    "signal": "SIGNAL",
    "peril_confirming": "PERIL_CONFIRMING",
}

# worksheet_section -> report_section mapping
_WORKSHEET_TO_REPORT_SECTION: dict[str, str] = {
    "company_profile": "company",
    "financial": "financial",
    "governance": "governance",
    "litigation": "litigation",
    "stock_activity": "market",
    "management": "governance",
}

# Legacy report_section names -> section numbers
SECTION_MAP: dict[str, int] = {
    "company": 1,
    "market": 2,
    "financial": 3,
    "financials": 3,
    "governance": 4,
    "litigation": 5,
    "disclosure": 4,
    "forward": 1,
    # New semantic worksheet_section strings
    "company_profile": 1,
    "stock_activity": 2,
    "management": 4,
}


def enrich_signal(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply backward-compat fields to raw YAML signal dict.

    Adds content_type, hazard_or_signal, category, section fields
    that callers expect from the legacy BrainDBLoader output.
    """
    work_type = raw.get("work_type")
    layer = raw.get("layer")
    tier = raw.get("tier")
    worksheet_section = raw.get("worksheet_section")

    raw["content_type"] = _WORK_TYPE_TO_CONTENT_TYPE.get(
        work_type or "", "EVALUATIVE_CHECK"
    )
    raw["hazard_or_signal"] = _LAYER_TO_HAZARD_OR_SIGNAL.get(
        layer or "", "SIGNAL"
    )

    # category: tier-1 extract = CONTEXT_DISPLAY, else DECISION_DRIVING
    if tier == 1 and work_type == "extract":
        raw["category"] = "CONTEXT_DISPLAY"
    else:
        raw["category"] = "DECISION_DRIVING"

    # report_section (string) from worksheet_section mapping
    report_section = _WORKSHEET_TO_REPORT_SECTION.get(
        worksheet_section or "", "company"
    )
    raw["report_section"] = report_section

    # section number from worksheet_section or report_section mapping
    if worksheet_section and worksheet_section in SECTION_MAP:
        raw["section"] = SECTION_MAP[worksheet_section]
    else:
        raw["section"] = SECTION_MAP.get(report_section, 0)

    # execution_mode: all YAML signals are AUTO-evaluated (matches DuckDB convention)
    if "execution_mode" not in raw:
        raw["execution_mode"] = "AUTO"

    return raw
