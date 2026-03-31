"""Section 7 coverage gaps: honest disclosure of unchecked items.

Renders the DATA_UNAVAILABLE and NOT_APPLICABLE check results as an
explicit coverage gaps section. Per user requirement: DATA_UNAVAILABLE
must NEVER masquerade as "N/A" or "No issues found."

Phase 31 enhancement: shows content type labels ([REQUIRED], [EVALUATIVE],
[PATTERN]) and rationale for each gap to help underwriters understand
the significance of missing data.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.stages.render.design_system import DesignSystem

logger = logging.getLogger(__name__)


# Section number -> human-readable name
_SECTION_NAMES: dict[int, str] = {
    1: "Executive Summary & Key Metrics",
    2: "Company Profile & Industry",
    3: "Financial Health",
    4: "Market & Trading",
    5: "Governance & Leadership",
    6: "Litigation & Regulatory",
}

# Content type -> display label mapping
_CONTENT_TYPE_LABELS: dict[str, str] = {
    "MANAGEMENT_DISPLAY": "REQUIRED",
    "EVALUATIVE_CHECK": "EVALUATIVE",
    "INFERENCE_PATTERN": "PATTERN",
}


# ---------------------------------------------------------------------------
# Check metadata cache for gap enrichment
# ---------------------------------------------------------------------------

_CHECK_META_CACHE: dict[str, dict[str, Any]] | None = None


def _load_check_metadata() -> dict[str, dict[str, Any]]:
    """Load check definitions for gap enrichment. Cached."""
    global _CHECK_META_CACHE
    if _CHECK_META_CACHE is not None:
        return _CHECK_META_CACHE
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        checks_data = load_signals()
        _CHECK_META_CACHE = {
            str(c.get("id", "")): c
            for c in checks_data.get("signals", [])
        }
    except Exception:
        logger.debug("Could not load check metadata for gap enrichment")
        _CHECK_META_CACHE = {}
    return _CHECK_META_CACHE


def _get_content_type_label(signal_id: str, meta: dict[str, dict[str, Any]]) -> str:
    """Get the content type label for a check, or empty string if unknown."""
    signal_def = meta.get(signal_id)
    if signal_def is None:
        return ""
    ct = signal_def.get("content_type", "")
    return _CONTENT_TYPE_LABELS.get(ct, "")


def _get_rationale(signal_id: str, meta: dict[str, dict[str, Any]]) -> str:
    """Get the rationale for a check, or empty string if unavailable."""
    signal_def = meta.get(signal_id)
    if signal_def is None:
        return ""
    return str(signal_def.get("rationale", "")) if signal_def.get("rationale") else ""


# ---------------------------------------------------------------------------
# Grouping and rendering
# ---------------------------------------------------------------------------


def _get_signal_results(context: dict[str, Any]) -> dict[str, Any]:
    """Extract signal_results dict from context."""
    # TODO(phase-60): use context["signal_results"] when available
    state = context.get("_state")
    if state is None or state.analysis is None:
        return {}
    return state.analysis.signal_results or {}


class _GapItem:
    """A single coverage gap item with enriched metadata."""

    __slots__ = ("content_type", "desc", "rationale", "reason")

    def __init__(self, desc: str, reason: str, content_type: str = "", rationale: str = "") -> None:
        self.desc = desc
        self.reason = reason
        self.content_type = content_type
        self.rationale = rationale


def _group_by_section(
    results: dict[str, Any],
    status_filter: str,
    meta: dict[str, dict[str, Any]] | None = None,
) -> dict[str, list[_GapItem]]:
    """Group check results by section, filtering by data_status.

    Returns dict of section_label -> list of _GapItem objects.
    When meta is provided, enriches each item with content_type and rationale.
    """
    if meta is None:
        meta = {}

    groups: dict[str, list[_GapItem]] = {}

    for signal_id, result_data in results.items():
        if not isinstance(result_data, dict):
            continue
        data_status = result_data.get("data_status", "EVALUATED")
        if data_status != status_filter:
            continue

        section_num = result_data.get("section", 0)
        section_label = _SECTION_NAMES.get(section_num, f"Section {section_num}")
        reason = result_data.get("data_status_reason", "No reason provided")
        # Skip aspirational checks with no data mappings (not real gaps)
        if "No fields mapped" in reason:
            continue
        signal_name = result_data.get("signal_name", signal_id)

        ct_label = _get_content_type_label(signal_id, meta)
        rationale = _get_rationale(signal_id, meta)

        if section_label not in groups:
            groups[section_label] = []
        groups[section_label].append(
            _GapItem(
                desc=f"{signal_id} ({signal_name})",
                reason=reason,
                content_type=ct_label,
                rationale=rationale,
            )
        )

    return groups


def render_coverage_gaps(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render Coverage Gaps section listing DATA_UNAVAILABLE checks.

    This section provides honest disclosure of what was not checked and why.
    DATA_UNAVAILABLE items are NEVER displayed as "N/A" or "No issues found."

    Phase 31: Shows content type labels and rationale for each gap.
    Phase 60-02: Receives context dict from build_template_context().

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Coverage Gaps -- Data Not Available")

    signal_results = _get_signal_results(context)
    total_signals = len(signal_results)

    # Load enriched metadata (graceful fallback to empty dict)
    meta = _load_check_metadata()

    # Find DATA_UNAVAILABLE checks
    unavailable_groups = _group_by_section(
        signal_results, "DATA_UNAVAILABLE", meta
    )
    unavailable_count = sum(len(v) for v in unavailable_groups.values())

    if unavailable_count == 0 and total_signals > 0:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run(
            "All checks evaluated -- no coverage gaps identified."
        )
    elif total_signals == 0:
        para = doc.add_paragraph(style="DOBody")
        para.add_run(
            "No check results available. Analysis may not have completed."
        )
    else:
        # Intro paragraph
        intro: Any = doc.add_paragraph(style="DOBody")
        intro_run: Any = intro.add_run(
            "The following checks could not be evaluated because required "
            "data was not acquired. These items are NOT cleared -- they "
            "represent gaps in coverage that should be considered in the "
            "underwriting decision."
        )
        intro_run.italic = True

        # Track content type counts for summary
        ct_counts: dict[str, int] = {}

        # Group by section
        for section_label in sorted(unavailable_groups.keys()):
            items = unavailable_groups[section_label]
            sub_heading: Any = doc.add_paragraph(style="DOHeading3")
            sub_heading.add_run(section_label)

            for gap in items:
                # Track content type for summary
                if gap.content_type:
                    ct_counts[gap.content_type] = (
                        ct_counts.get(gap.content_type, 0) + 1
                    )

                item_para: Any = doc.add_paragraph(style="DOBody")
                if gap.content_type:
                    ct_run: Any = item_para.add_run(f"  [{gap.content_type}] ")
                    ct_run.bold = True
                    ct_run.font.size = ds.size_small
                desc_run: Any = item_para.add_run(f"{gap.desc}: {gap.reason}")
                desc_run.font.size = ds.size_small

                # Add rationale line if available
                if gap.rationale:
                    rat_para: Any = doc.add_paragraph(style="DOBody")
                    rat_run: Any = rat_para.add_run(
                        f"    Why this matters: {gap.rationale}"
                    )
                    rat_run.italic = True
                    rat_run.font.size = ds.size_small

        # Content type breakdown summary
        if ct_counts:
            breakdown_parts = []
            for label in ("REQUIRED", "EVALUATIVE", "PATTERN"):
                count = ct_counts.get(label, 0)
                if count > 0:
                    name = {
                        "REQUIRED": "Required items",
                        "EVALUATIVE": "Evaluative checks",
                        "PATTERN": "Patterns",
                    }[label]
                    breakdown_parts.append(f"{name}: {count}")
            if breakdown_parts:
                bd_para: Any = doc.add_paragraph(style="DOBody")
                bd_run: Any = bd_para.add_run(
                    "Gap breakdown: " + " | ".join(breakdown_parts)
                )
                bd_run.font.size = ds.size_small

        # Footer: coverage statistics
        evaluated_count = total_signals - unavailable_count
        coverage_pct = (
            (evaluated_count / total_signals * 100) if total_signals > 0 else 0
        )
        footer: Any = doc.add_paragraph(style="DOBody")
        footer_run: Any = footer.add_run(
            f"Total: {unavailable_count} checks data-unavailable out of "
            f"{total_signals} total checks ({coverage_pct:.0f}% coverage)"
        )
        footer_run.bold = True

    # NOT_APPLICABLE section (brief, with content type prefix)
    not_applicable_groups = _group_by_section(
        signal_results, "NOT_APPLICABLE", meta
    )
    na_count = sum(len(v) for v in not_applicable_groups.values())

    if na_count > 0:
        na_para: Any = doc.add_paragraph(style="DOBody")
        na_items = []
        for items in not_applicable_groups.values():
            for gap in items:
                prefix = f"[{gap.content_type}] " if gap.content_type else ""
                na_items.append(f"{prefix}{gap.desc}")

        # Limit display to first 10 with count
        display_items = na_items[:10]
        suffix = f" (and {na_count - 10} more)" if na_count > 10 else ""
        na_run: Any = na_para.add_run(
            f"Not applicable to this company type ({na_count} checks): "
            + ", ".join(display_items) + suffix
        )
        na_run.font.size = ds.size_small
        na_run.font.color.rgb = ds.color_text_light


__all__ = ["render_coverage_gaps"]
