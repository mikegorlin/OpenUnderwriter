"""LLM prompt enhancement with brain-driven extraction targets.

When the LLM reads a filing, this module appends targeted extraction
instructions based on what the brain needs. Fields already covered by
the Pydantic schema are excluded to avoid duplication.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from do_uw.stages.extract.llm.schemas import SCHEMA_REGISTRY

if TYPE_CHECKING:
    from do_uw.stages.extract.extraction_manifest import ExtractionManifest

logger = logging.getLogger(__name__)

# Expected types for brain fields (maps extraction_hint expected_type to
# human-readable description for the LLM prompt)
_TYPE_DESCRIPTIONS: dict[str, str] = {
    "numeric": "number",
    "boolean": "true/false",
    "text": "text",
    "list": "list of items",
    "dict": "key-value pairs",
    "percentage": "percentage (0-100)",
    "currency": "amount in USD",
}


def _get_schema_field_names(form_type: str) -> set[str]:
    """Get all field names from the Pydantic schema for a filing type."""
    entry = SCHEMA_REGISTRY.get(form_type)
    if entry is None:
        return set()

    schema_class: type[BaseModel] = entry.schema
    return set(schema_class.model_fields.keys())


def _format_type_hint(hint: dict[str, Any] | None) -> str:
    """Format extraction hint into a type description for the LLM."""
    if not hint:
        return "text"
    expected_type = hint.get("expected_type", "text")
    return _TYPE_DESCRIPTIONS.get(expected_type, expected_type)


def enhance_prompt_with_brain_requirements(
    base_prompt: str,
    filing_type: str,
    manifest: ExtractionManifest,
) -> str:
    """Append brain-driven extraction targets to the LLM system prompt.

    Filters the manifest to requirements matching this filing type,
    excludes fields already covered by the Pydantic schema, and appends
    targeted extraction instructions.

    Args:
        base_prompt: Original system prompt for this filing type.
        filing_type: SEC form type (e.g. "10-K", "DEF 14A").
        manifest: Extraction manifest built from brain checks.

    Returns:
        Enhanced system prompt with brain extraction targets appended.
    """
    requirements = manifest.get_requirements_for_filing_type(filing_type)
    if not requirements:
        return base_prompt

    # Exclude fields already in the schema (no duplication)
    schema_fields = _get_schema_field_names(filing_type)

    # Build extraction target list
    targets: list[str] = []
    for req in requirements:
        # Skip if the field is already a first-class schema field
        if req.field_key in schema_fields:
            continue

        type_desc = _format_type_hint(req.extraction_hint)

        # Build a concise description from check names
        desc = req.signal_names[0] if req.signal_names else req.field_key
        # Truncate long descriptions
        if len(desc) > 80:
            desc = desc[:77] + "..."

        targets.append(f"  - {req.field_key}: {desc} ({type_desc})")

    if not targets:
        return base_prompt

    # Cap at 20 targets to keep prompt manageable
    if len(targets) > 20:
        targets = targets[:20]
        targets.append(f"  ... and {len(requirements) - 20} more fields")

    enhancement = (
        "\n\nADDITIONAL EXTRACTION TARGETS (from underwriting brain):\n"
        "Extract these if found in the document. Report as key-value "
        "pairs in the brain_fields dict. If not found, omit.\n"
        + "\n".join(targets)
    )

    logger.info(
        "Enhanced %s prompt with %d brain extraction targets",
        filing_type,
        len(targets),
    )

    return base_prompt + enhancement


__all__ = ["enhance_prompt_with_brain_requirements"]
