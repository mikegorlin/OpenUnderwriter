"""LLM extraction engine for SEC filing data.

Provides LLM-powered structured extraction from complete filing documents
using instructor + Anthropic API with Pydantic schema validation.

Re-exports core components for convenient access:
    LLMExtractor - Main extraction class
    ExtractionCache - SQLite cache for extraction results
    strip_boilerplate - Filing text cleanup
    CostTracker - Per-run cost tracking with budget enforcement
"""

from do_uw.stages.extract.llm.boilerplate import strip_boilerplate
from do_uw.stages.extract.llm.cache import ExtractionCache
from do_uw.stages.extract.llm.cost_tracker import CostTracker
from do_uw.stages.extract.llm.extractor import LLMExtractor

__all__ = [
    "CostTracker",
    "ExtractionCache",
    "LLMExtractor",
    "strip_boilerplate",
]
