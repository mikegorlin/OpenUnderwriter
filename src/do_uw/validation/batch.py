"""Batch API utility for cost-optimized LLM extraction.

NOTE: Batch extraction currently disabled for DeepSeek integration.
Original Anthropic batch API not compatible with DeepSeek.
Kept for reference and future OpenAI batch API integration.

Separate from LLMExtractor by design -- batch mode is an optional
optimization for re-runs, not a replacement for the production code path.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Default LLM model. Override via DO_UW_LLM_MODEL env var.
_DEFAULT_LLM_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")


def _pydantic_to_tool_schema(
    schema_cls: type[BaseModel],
) -> dict[str, Any]:
    """Convert a Pydantic model into an OpenAI tool definition.

    Generates a tool definition dict matching the format that
    instructor uses internally: a single tool named after the schema
    class with its JSON Schema as the input_schema.

    Args:
        schema_cls: Pydantic model class to convert.

    Returns:
        OpenAI tool definition dict with name, description,
        and input_schema.
    """
    json_schema = schema_cls.model_json_schema()
    return {
        "name": schema_cls.__name__,
        "description": (f"Extract structured data matching the {schema_cls.__name__} schema."),
        "input_schema": json_schema,
    }


class BatchExtractor:
    """Batch API client for cost-optimized bulk LLM extraction.

    NOTE: Batch extraction disabled for DeepSeek integration.
    All methods return empty/default values.
    """

    def __init__(
        self,
        model: str = _DEFAULT_LLM_MODEL,
    ) -> None:
        """Initialize the batch extractor.

        Args:
            model: Model identifier for batch requests.
        """
        self._model = model
        logger.warning("Batch extraction disabled for DeepSeek integration")

    @property
    def model(self) -> str:
        """Return the model identifier."""
        return self._model

    def prepare_request(
        self,
        filing_text: str,
        form_type: str,
        accession: str,
        system_prompt: str,
        schema_cls: type[BaseModel],
    ) -> dict[str, Any]:
        """Build a single batch request dict.

        Returns empty dict since batch extraction is disabled.
        """
        logger.warning("Batch extraction disabled for DeepSeek integration")
        return {}

    def submit_batch(self, requests: list[dict[str, Any]]) -> str | None:
        """Submit requests as an OpenAI Batch.

        Returns None since batch extraction is disabled.
        """
        logger.warning("Batch extraction disabled for DeepSeek integration")
        return None

    def poll_batch(
        self,
        batch_id: str,
        poll_interval: float = 60.0,
        max_polls: int = 120,
    ) -> list[dict[str, Any]]:
        """Poll a batch until it reaches a terminal status.

        Returns empty list since batch extraction is disabled.
        """
        logger.warning("Batch extraction disabled for DeepSeek integration")
        return []

    def parse_results(
        self,
        results: list[dict[str, Any]],
        schema_map: dict[str, type[BaseModel]],
    ) -> dict[str, BaseModel | None]:
        """Parse and validate batch results against Pydantic schemas.

        Returns empty dict since batch extraction is disabled.
        """
        logger.warning("Batch extraction disabled for DeepSeek integration")
        return {}
