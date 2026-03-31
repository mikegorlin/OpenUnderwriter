"""Pipeline audit tooling to identify unwired checks.

Programmatically audits the data pipeline for all checks by calling
map_signal_data() and examining which checks have mappers, which have
data, and which are completely unwired.

Used by Phase 27 Plan 04 to wire data paths and by the Coverage Gaps
section to report what was not checked.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData

from do_uw.brain.brain_unified_loader import load_config

logger = logging.getLogger(__name__)


def _load_classification() -> dict[str, Any]:
    """Load signal_classification.json for category/plaintiff_lens metadata."""
    return load_config("signal_classification")


def _get_check_category(
    signal_id: str,
    check_config: dict[str, Any],
    classification: dict[str, Any],
) -> str:
    """Resolve the category for a check from config or classification lookup.

    Priority: check_config["category"] > override list > prefix_defaults.
    """
    # Direct config value
    if check_config.get("category"):
        return str(check_config["category"])

    # Override to DECISION_DRIVING
    overrides = classification.get("override_decision_driving", {})
    override_ids = overrides.get("signals", [])
    if signal_id in override_ids:
        return "DECISION_DRIVING"

    # Prefix defaults: try longest prefix first
    prefix_defaults = classification.get("prefix_defaults", {})
    parts = signal_id.split(".")
    for depth in range(len(parts), 0, -1):
        prefix = ".".join(parts[:depth])
        if prefix in prefix_defaults:
            return str(prefix_defaults[prefix].get("category", ""))

    return ""


def _get_plaintiff_lenses(
    signal_id: str,
    check_config: dict[str, Any],
    classification: dict[str, Any],
) -> list[str]:
    """Resolve plaintiff lenses for a check from config or classification."""
    if check_config.get("plaintiff_lenses"):
        return [str(p) for p in check_config["plaintiff_lenses"]]

    lens_defaults = classification.get("plaintiff_lens_defaults", {})
    parts = signal_id.split(".")
    for depth in range(len(parts), 0, -1):
        prefix = ".".join(parts[:depth])
        if prefix in lens_defaults:
            return [str(p) for p in lens_defaults[prefix]]

    return []


def audit_check_pipeline(
    signal_id: str,
    check_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit a single check's data pipeline status.

    Calls map_signal_data() to see if the check has a mapper and whether
    the mapped fields contain actual data.

    Args:
        signal_id: Unique check identifier.
        check_config: Check configuration dict from brain/signals.json.
        extracted: ExtractedData from the EXTRACT stage.
        company: Optional CompanyProfile for company-related checks.
        classification: Pre-loaded classification config (optional, loaded if None).

    Returns:
        Audit result dict with: signal_id, has_mapper, all_values_none,
        mapped_fields, non_none_fields, data_status, check_category,
        plaintiff_lenses.
    """
    from do_uw.stages.analyze.signal_mappers import map_signal_data

    if classification is None:
        classification = _load_classification()

    data = map_signal_data(signal_id, check_config, extracted, company)

    has_mapper = bool(data)
    mapped_fields = list(data.keys())
    non_none_fields = [k for k, v in data.items() if v is not None]
    all_values_none = has_mapper and len(non_none_fields) == 0

    if not has_mapper:
        data_status = "NO_MAPPER"
    elif all_values_none:
        data_status = "ALL_NONE"
    else:
        data_status = "HAS_DATA"

    category = _get_check_category(signal_id, check_config, classification)
    lenses = _get_plaintiff_lenses(signal_id, check_config, classification)

    return {
        "signal_id": signal_id,
        "has_mapper": has_mapper,
        "all_values_none": all_values_none,
        "mapped_fields": mapped_fields,
        "non_none_fields": non_none_fields,
        "data_status": data_status,
        "check_category": category,
        "plaintiff_lenses": lenses,
    }


def audit_all_checks(
    checks: list[dict[str, Any]],
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
) -> dict[str, Any]:
    """Audit all AUTO signals for data pipeline completeness.

    Args:
        checks: List of check config dicts from brain/signals.json.
        extracted: ExtractedData from the EXTRACT stage.
        company: Optional CompanyProfile.

    Returns:
        Summary dict with totals, breakdowns by category/section, and
        per-check audit details.
    """
    classification = _load_classification()

    auto_signals = [
        c for c in checks if c.get("execution_mode") == "AUTO"
    ]

    details: dict[str, dict[str, Any]] = {}
    has_data_count = 0
    no_mapper_count = 0
    all_none_count = 0
    unwired_checks: list[str] = []

    by_category: dict[str, dict[str, int]] = {}
    by_section: dict[str, dict[str, int]] = {}

    for check in auto_signals:
        signal_id = check.get("id", "UNKNOWN")
        audit = audit_check_pipeline(
            signal_id, check, extracted, company, classification,
        )
        details[signal_id] = audit

        # Aggregate counts
        status = audit["data_status"]
        if status == "HAS_DATA":
            has_data_count += 1
        elif status == "NO_MAPPER":
            no_mapper_count += 1
            unwired_checks.append(signal_id)
        elif status == "ALL_NONE":
            all_none_count += 1
            unwired_checks.append(signal_id)

        # By category
        cat = audit["check_category"] or "UNCATEGORIZED"
        if cat not in by_category:
            by_category[cat] = {"total": 0, "has_data": 0, "no_mapper": 0, "all_none": 0}
        by_category[cat]["total"] += 1
        by_category[cat][_status_to_key(status)] += 1

        # By section prefix (first two segments of signal_id)
        parts = signal_id.split(".")
        section_key = ".".join(parts[:2]) if len(parts) >= 2 else signal_id
        if section_key not in by_section:
            by_section[section_key] = {"total": 0, "has_data": 0, "no_mapper": 0, "all_none": 0}
        by_section[section_key]["total"] += 1
        by_section[section_key][_status_to_key(status)] += 1

    total = len(auto_signals)

    return {
        "total_signals": total,
        "has_data": has_data_count,
        "no_mapper": no_mapper_count,
        "all_none": all_none_count,
        "by_category": dict(sorted(by_category.items())),
        "by_section": dict(sorted(by_section.items())),
        "unwired_checks": sorted(unwired_checks),
        "details": details,
    }


def _status_to_key(status: str) -> str:
    """Map audit data_status to dict key for aggregation."""
    if status == "HAS_DATA":
        return "has_data"
    if status == "NO_MAPPER":
        return "no_mapper"
    return "all_none"


def format_audit_report(audit_result: dict[str, Any]) -> str:
    """Produce a human-readable text summary of the pipeline audit.

    Args:
        audit_result: Output from audit_all_checks().

    Returns:
        Multi-line string with totals, category breakdown, and unwired list.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("PIPELINE DATA COVERAGE AUDIT")
    lines.append("=" * 60)
    lines.append("")

    total = audit_result["total_signals"]
    has_data = audit_result["has_data"]
    no_mapper = audit_result["no_mapper"]
    all_none = audit_result["all_none"]

    pct_wired = (has_data / total * 100) if total > 0 else 0
    lines.append(f"Total AUTO signals: {total}")
    lines.append(f"  Has data:   {has_data:>4} ({pct_wired:.0f}%)")
    lines.append(f"  No mapper:  {no_mapper:>4}")
    lines.append(f"  All None:   {all_none:>4}")
    lines.append(f"  Unwired:    {no_mapper + all_none:>4} ({100 - pct_wired:.0f}%)")
    lines.append("")

    # By category
    lines.append("By Category:")
    lines.append(f"  {'Category':<22} {'Total':>6} {'Data':>6} {'NoMap':>6} {'None':>6}")
    lines.append("  " + "-" * 46)
    for cat, counts in audit_result["by_category"].items():
        lines.append(
            f"  {cat:<22} {counts['total']:>6} "
            f"{counts['has_data']:>6} {counts['no_mapper']:>6} "
            f"{counts['all_none']:>6}"
        )
    lines.append("")

    # By section
    lines.append("By Section Prefix:")
    lines.append(f"  {'Section':<22} {'Total':>6} {'Data':>6} {'NoMap':>6} {'None':>6}")
    lines.append("  " + "-" * 46)
    for sec, counts in audit_result["by_section"].items():
        lines.append(
            f"  {sec:<22} {counts['total']:>6} "
            f"{counts['has_data']:>6} {counts['no_mapper']:>6} "
            f"{counts['all_none']:>6}"
        )
    lines.append("")

    # Unwired checks
    unwired = audit_result["unwired_checks"]
    if unwired:
        lines.append(f"Unwired Checks ({len(unwired)}):")
        for cid in unwired:
            detail = audit_result["details"].get(cid, {})
            status = detail.get("data_status", "?")
            cat = detail.get("check_category", "?")
            lines.append(f"  [{status:>9}] {cid} ({cat})")
    else:
        lines.append("All checks have data -- no unwired checks found.")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


__all__ = ["audit_all_checks", "audit_check_pipeline", "format_audit_report"]
