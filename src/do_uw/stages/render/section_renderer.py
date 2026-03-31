"""Section-driven rendering orchestrator.

Builds section dispatch context for HTML templates. Uses manifest groups
and signal self-selection (v3 architecture) instead of section YAML.

Phase 84-03: Migrated from brain_section_schema to manifest_schema + signal groups.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_signals
from do_uw.brain.manifest_schema import collect_signals_by_group, load_manifest
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def build_section_context(
    state: AnalysisState | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build section dispatch context for HTML rendering.

    Returns dict with section_context: dict of section_id -> facet data,
    and manifest_sections: ordered list of sections with facets.

    Sources data from manifest groups and signal self-selection (group field).
    The section_context dict preserves the same structure templates expect:
    each entry has "section" and "facets" keys, where facets is a list of
    dicts with id, name, render_as, signals, columns, template.

    Args:
        state: AnalysisState (reserved for future per-signal gating).
        **kwargs: Absorbs deprecated params (e.g., sections_dir) for compat.
    """
    _ = state  # Reserved for future use

    manifest = load_manifest()
    signals_data = load_signals()
    signals_by_group = collect_signals_by_group(signals_data["signals"])

    section_context: dict[str, Any] = {}

    for ms in manifest.sections:
        if not ms.groups:
            continue

        facet_data = []
        for group in ms.groups:
            facet_data.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "render_as": group.render_as,
                    "signals": signals_by_group.get(group.id, []),
                    "columns": [],  # Not used by templates -- safe default
                    "template": group.template,
                }
            )

        section_context[ms.id] = {
            "section": None,  # No SectionSpec object needed anymore
            "facets": facet_data,
        }
        logger.debug(
            "Section '%s' has %d facets for section-driven rendering",
            ms.id,
            len(facet_data),
        )

    # Manifest-driven section list for template loop rendering.
    manifest_sections: list[dict[str, Any]] = []
    for ms in manifest.sections:
        facet_list: list[dict[str, Any]] = []
        for group in ms.groups:
            facet_list.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "template": group.template,
                    "render_as": group.render_as,
                    "signals": signals_by_group.get(group.id, []),
                }
            )
        manifest_sections.append(
            {
                "id": ms.id,
                "name": ms.name,
                "template": ms.template,
                "render_mode": ms.render_mode,
                "layer": ms.layer,
                "facets": facet_list,
            }
        )
    logger.debug(
        "Manifest-driven rendering: %d sections in order",
        len(manifest_sections),
    )

    return {"section_context": section_context, "manifest_sections": manifest_sections}


__all__ = ["build_section_context"]
