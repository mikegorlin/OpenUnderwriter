"""Output manifest schema and loader.

Phase 76 Plan 01: Declares the output manifest contract -- a single YAML file
that specifies every section and facet the worksheet must contain, with explicit
ordering and data_type tags.

Phase 84 Plan 01: Evolves from facets-with-signal-lists to group objects where
signals self-select. ManifestGroup replaces ManifestFacet as the primary grouping
unit. Backward-compat: facets auto-populate groups during migration.

The manifest is the authority for output structure across all formats (HTML, Word, PDF).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Default manifest location (relative to this module)
_DEFAULT_MANIFEST_PATH = Path(__file__).parent / "output_manifest.yaml"


class ManifestFacet(BaseModel):
    """An atomic display unit within a manifest section.

    Each facet maps to a template block and carries a data_type tag from
    the data complexity spectrum:
      - extract_display: Pull data, show it (revenue, board size)
      - extract_compute: Pull inputs, apply formula (Altman Z, ratios)
      - extract_infer: Pattern recognition across data points
      - hunt_analyze: Broad search, aggregate, deduplicate, then analyze
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Unique facet ID within its parent section",
    )
    name: str = Field(
        ...,
        description="Display heading for this facet",
    )
    template: str = Field(
        ...,
        description="Template path for rendering this facet",
    )
    data_type: Literal["extract_display", "extract_compute", "extract_infer", "hunt_analyze"] = Field(
        ...,
        description="Data complexity type from the 4-type spectrum",
    )
    render_as: str = Field(
        ...,
        description="Template dispatch type (financial_table, kv_table, scorecard, etc.)",
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Signal IDs this facet displays (informational metadata)",
    )
    requires: list[str] = Field(
        default_factory=list,
        description=(
            "Data field paths required for this facet to render meaningfully "
            "(dot-notation, e.g. 'financials.statements'). Used by "
            "validate_requires_populated for pre-render diagnostics."
        ),
    )


class ManifestGroup(BaseModel):
    """A grouping unit within a manifest section (v3 evolution of ManifestFacet).

    Groups declare layout/rendering metadata. Signals self-select into groups
    via their own `group` field -- the manifest no longer lists signal IDs.

    Six fields: id, name, template, render_as, requires, display_only.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Unique group ID within its parent section",
    )
    name: str = Field(
        ...,
        description="Display heading for this group",
    )
    template: str = Field(
        ...,
        description="Template path for rendering this group",
    )
    render_as: str = Field(
        ...,
        description="Template dispatch type (financial_table, kv_table, scorecard, etc.)",
    )
    requires: list[str] = Field(
        default_factory=list,
        description=(
            "Data field paths required for this group to render meaningfully "
            "(dot-notation, e.g. 'financials.statements')."
        ),
    )
    display_only: bool = Field(
        default=False,
        description=(
            "If true, this group displays computed or extracted data with no "
            "signal governance. Signals evaluate risk FROM this data but do "
            "not govern the display itself."
        ),
    )


class ManifestSection(BaseModel):
    """A section in the output manifest.

    Sections are ordered containers of groups. Sections without groups
    (e.g., identity/cover) render as single template blocks.

    Backward-compat: if `facets` is provided but `groups` is empty,
    groups auto-populates from facets (dropping data_type and signals).
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Unique section identifier",
    )
    name: str = Field(
        ...,
        description="Human-readable section name",
    )
    template: str = Field(
        ...,
        description="Parent wrapper template path",
    )
    render_mode: Literal["required", "optional"] = Field(
        default="required",
        description="Whether section always renders or only when data exists",
    )
    layer: Literal["decision", "analysis", "audit"] = Field(
        default="analysis",
        description="Document tier: decision (top), analysis (middle), audit (collapsed appendix)",
    )
    groups: list[ManifestGroup] = Field(
        default_factory=list,
        description="Ordered list of groups within this section",
    )
    # Deprecated: use groups
    facets: list[ManifestFacet] = Field(
        default_factory=list,
        description="Deprecated -- use groups. Kept for backward-compat migration.",
    )

    @model_validator(mode="after")
    def _auto_populate_groups_from_facets(self) -> "ManifestSection":
        """If groups is empty and facets is non-empty, populate groups from facets."""
        if not self.groups and self.facets:
            self.groups = [
                ManifestGroup(
                    id=f.id,
                    name=f.name,
                    template=f.template,
                    render_as=f.render_as,
                    requires=list(f.requires),
                )
                for f in self.facets
            ]
        return self


class OutputManifest(BaseModel):
    """Top-level output manifest declaring all worksheet content.

    The manifest is versioned and contains an ordered list of sections,
    each with an ordered list of facets. This is the single source of truth
    for what the worksheet contains and in what order.
    """

    model_config = ConfigDict(extra="forbid")

    manifest_version: str = Field(
        ...,
        description="Schema version for the manifest format",
    )
    sections: list[ManifestSection] = Field(
        default_factory=list,
        description="Ordered list of worksheet sections",
    )

    @model_validator(mode="after")
    def _check_duplicates(self) -> "OutputManifest":
        """Reject duplicate section IDs, facet IDs, and group IDs within sections."""
        seen_sections: set[str] = set()
        for section in self.sections:
            if section.id in seen_sections:
                raise ValueError(
                    f"Duplicate section ID: '{section.id}'"
                )
            seen_sections.add(section.id)

            seen_facets: set[str] = set()
            for facet in section.facets:
                if facet.id in seen_facets:
                    raise ValueError(
                        f"Duplicate facet ID '{facet.id}' in section '{section.id}'"
                    )
                seen_facets.add(facet.id)

            seen_groups: set[str] = set()
            for group in section.groups:
                if group.id in seen_groups:
                    raise ValueError(
                        f"Duplicate group ID '{group.id}' in section '{section.id}'"
                    )
                seen_groups.add(group.id)

        return self


def load_manifest(path: Path | None = None) -> OutputManifest:
    """Load and validate the output manifest YAML.

    Args:
        path: Path to the manifest YAML file. Defaults to
              src/do_uw/brain/output_manifest.yaml.

    Returns:
        Validated OutputManifest instance.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    manifest_path = path or _DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"output_manifest.yaml not found at {manifest_path}"
        )
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return OutputManifest.model_validate(raw)


def get_section_order(manifest: OutputManifest) -> list[str]:
    """Return ordered list of section IDs from the manifest."""
    return [s.id for s in manifest.sections]


def get_facet_order(manifest: OutputManifest, section_id: str) -> list[str]:
    """Return ordered list of group/facet IDs for a given section.

    Prefers groups (v3) over facets (legacy). Returns empty list if
    section_id is not found or has no groups/facets.
    """
    for section in manifest.sections:
        if section.id == section_id:
            if section.groups:
                return [g.id for g in section.groups]
            return [f.id for f in section.facets]
    return []


def collect_signals_by_group(signals: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Map group IDs to lists of signal IDs from loaded signals.

    Signals self-select into groups via their `group` field. Signals
    without a group (empty string or missing key) are excluded.
    """
    groups: dict[str, list[str]] = {}
    for sig in signals:
        gid = sig.get("group", "")
        if gid:
            groups.setdefault(gid, []).append(sig["id"])
    return groups


__all__ = [
    "ManifestFacet",
    "ManifestGroup",
    "ManifestSection",
    "OutputManifest",
    "collect_signals_by_group",
    "get_facet_order",
    "get_section_order",
    "load_manifest",
]
