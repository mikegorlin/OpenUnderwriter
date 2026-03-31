"""Validation wrapper for typed context models.

Provides _validate_context() which validates raw builder dicts against
Pydantic models and falls back to untyped dicts on any error. This
ensures the render pipeline never breaks during typed model migration.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def _validate_context(
    model_cls: type[BaseModel],
    raw: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Validate raw context dict against typed model.

    Returns model_dump() on success, raw dict on failure.
    Never breaks the pipeline.

    Args:
        model_cls: The Pydantic model class to validate against.
        raw: The raw dict from the context builder.
        section_name: Name of the section (for logging).

    Returns:
        A dict -- either from model_dump() (validated) or the original
        raw dict (fallback on validation error).
    """
    if not raw:
        return raw
    try:
        typed = model_cls.model_validate(raw)
        return typed.model_dump()
    except ValidationError as e:
        logger.warning(
            "Typed validation failed for %s (%d errors), using untyped fallback",
            section_name,
            e.error_count(),
        )
        return raw
