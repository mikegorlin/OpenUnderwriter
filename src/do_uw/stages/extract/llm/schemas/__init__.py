"""LLM extraction schema registry.

Maps SEC form types to their corresponding extraction schema, system
prompt key, and max output tokens. The registry is the single lookup
point used by LLMExtractor to determine how to extract a given filing.

Form 4 is deliberately EXCLUDED -- it is XML-parsed, not LLM-extracted.
"""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel

from do_uw.stages.extract.llm.schemas.capital_filing import (
    CapitalFilingExtraction,
)
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedCompensation,
    ExtractedContingency,
    ExtractedDirector,
    ExtractedLegalProceeding,
    ExtractedPerson,
    ExtractedRiskFactor,
    MoneyAmount,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm.schemas.eight_k import EightKExtraction
from do_uw.stages.extract.llm.schemas.ownership_filing import (
    SC13DExtraction,
    SC13GExtraction,
)
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.llm.schemas.ten_q import TenQExtraction


class SchemaEntry(NamedTuple):
    """Registry entry mapping a form type to extraction configuration."""

    schema: type[BaseModel]
    prompt_key: str
    max_tokens: int


# ---------------------------------------------------------------------------
# Schema Registry
# ---------------------------------------------------------------------------
# Maps SEC form_type strings (as used in ACQUIRE stage) to their
# extraction schema class, system prompt key, and max output tokens.
#
# Form 4 is deliberately excluded -- it uses XML parsing, not LLM extraction.
# ---------------------------------------------------------------------------

SCHEMA_REGISTRY: dict[str, SchemaEntry] = {
    # Annual reports
    "10-K": SchemaEntry(TenKExtraction, "ten_k", 8192),
    "20-F": SchemaEntry(TenKExtraction, "ten_k", 8192),
    # Proxy statements
    "DEF 14A": SchemaEntry(DEF14AExtraction, "def14a", 8192),
    # Quarterly reports
    "10-Q": SchemaEntry(TenQExtraction, "ten_q", 8192),
    "6-K": SchemaEntry(TenQExtraction, "ten_q", 8192),
    # Current reports
    "8-K": SchemaEntry(EightKExtraction, "eight_k", 4096),
    # Ownership filings
    "SC 13D": SchemaEntry(SC13DExtraction, "ownership", 4096),
    "SC 13G": SchemaEntry(SC13GExtraction, "ownership", 4096),
    # Capital market filings
    "S-3": SchemaEntry(CapitalFilingExtraction, "capital", 4096),
    "S-1": SchemaEntry(CapitalFilingExtraction, "capital", 4096),
    "424B": SchemaEntry(CapitalFilingExtraction, "capital", 4096),
}


def get_schema_for_filing(form_type: str) -> SchemaEntry | None:
    """Look up the extraction schema for a given form type.

    Args:
        form_type: SEC form type string (e.g. '10-K', 'DEF 14A').

    Returns:
        SchemaEntry with schema class, prompt key, and max tokens,
        or None if the form type is not supported for LLM extraction
        (e.g. Form 4 which uses XML parsing).
    """
    return SCHEMA_REGISTRY.get(form_type)


__all__ = [
    "SCHEMA_REGISTRY",
    "CapitalFilingExtraction",
    "DEF14AExtraction",
    "EightKExtraction",
    "ExtractedCompensation",
    "ExtractedContingency",
    "ExtractedDirector",
    "ExtractedLegalProceeding",
    "ExtractedPerson",
    "ExtractedRiskFactor",
    "MoneyAmount",
    "SC13DExtraction",
    "SC13GExtraction",
    "SchemaEntry",
    "TenKExtraction",
    "TenQExtraction",
    "get_schema_for_filing",
]
