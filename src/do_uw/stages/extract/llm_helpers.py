"""Shared helpers for deserializing LLM extraction results from state.

Pre-deserializes LLM results once at sub-orchestrator level so individual
converter functions receive typed Pydantic models, not raw dicts.
"""

from __future__ import annotations

import logging
from typing import cast

from pydantic import BaseModel as _BaseModel

from do_uw.models.state import AnalysisState
from do_uw.stages.extract.llm.schemas import (
    DEF14AExtraction,
    EightKExtraction,
    TenKExtraction,
)

logger = logging.getLogger(__name__)


def get_llm_eight_k(state: AnalysisState) -> list[EightKExtraction]:
    """Deserialize ALL LLM 8-K extractions from state.

    Unlike 10-K and DEF 14A (single filing per type), multiple 8-Ks
    may exist for a company.  Returns a list of typed extractions.
    """
    if state.acquired_data is None:
        return []
    results: list[EightKExtraction] = []
    for key, data in state.acquired_data.llm_extractions.items():
        if key.startswith("8-K:") and isinstance(data, dict):
            try:
                results.append(EightKExtraction.model_validate(data))
            except Exception:
                logger.warning(
                    "Failed to deserialize 8-K extraction: %s",
                    key,
                    exc_info=True,
                )
    return results


def get_llm_def14a(state: AnalysisState) -> DEF14AExtraction | None:
    """Deserialize LLM DEF 14A extraction from state.

    Searches ``state.acquired_data.llm_extractions`` for a key starting
    with ``"DEF 14A:"`` and returns a validated :class:`DEF14AExtraction`.
    """
    result = _get_llm_extraction(state, "DEF 14A:", DEF14AExtraction)
    if result is None:
        return None
    return cast(DEF14AExtraction, result)


def get_llm_ten_k(state: AnalysisState) -> TenKExtraction | None:
    """Deserialize LLM 10-K extraction from state.

    Tries ``"10-K:"`` first, falls back to ``"20-F:"`` for foreign
    private issuers.  Returns a validated :class:`TenKExtraction`.
    """
    result = _get_llm_extraction(state, "10-K:", TenKExtraction)
    if result is not None:
        return cast(TenKExtraction, result)
    result = _get_llm_extraction(state, "20-F:", TenKExtraction)
    if result is None:
        return None
    return cast(TenKExtraction, result)


def collect_brain_fields(state: AnalysisState) -> dict[str, object]:
    """Merge brain_fields from all LLM extractions into a single dict.

    Each LLM extraction schema has an optional brain_fields dict for
    dynamically requested extraction targets. This function collects
    them all, with later extractions overwriting earlier ones on
    key collision.

    Returns:
        Merged dict of field_key -> extracted value.
    """
    if state.acquired_data is None:
        return {}

    merged: dict[str, object] = {}
    for _key, data in state.acquired_data.llm_extractions.items():
        if isinstance(data, dict):
            brain_fields = data.get("brain_fields")
            if isinstance(brain_fields, dict):
                merged.update(brain_fields)

    if merged:
        logger.info(
            "Collected %d brain_fields from LLM extractions", len(merged),
        )
    return merged


def _get_llm_extraction(
    state: AnalysisState,
    key_prefix: str,
    model_class: type[_BaseModel],
) -> _BaseModel | None:
    """Generic LLM extraction deserializer.

    Looks through ``state.acquired_data.llm_extractions`` for ALL keys
    matching *key_prefix*, selects the most recent by cross-referencing
    filing dates, and returns a validated Pydantic model.
    """
    if state.acquired_data is None:
        return None
    extractions = state.acquired_data.llm_extractions
    if not extractions:
        return None

    # Collect all matching keys
    matching_keys = [k for k in extractions if k.startswith(key_prefix)]
    if not matching_keys:
        return None

    # If only one match, use it directly
    if len(matching_keys) == 1:
        return _try_deserialize(extractions[matching_keys[0]], matching_keys[0], model_class)

    # Multiple matches — pick the most recent by filing date
    # Build accession -> filing_date lookup from filings metadata
    filing_dates = _build_filing_date_lookup(state, key_prefix)

    # Sort matching keys by filing date descending (most recent first)
    def _sort_key(k: str) -> str:
        # Key format: "10-K:0000950170-23-034640"
        accession = k.split(":", 1)[1] if ":" in k else k
        return filing_dates.get(accession, "0000-00-00")

    matching_keys.sort(key=_sort_key, reverse=True)

    # Try each in order (most recent first)
    for key in matching_keys:
        result = _try_deserialize(extractions[key], key, model_class)
        if result is not None:
            return result
    return None


def _try_deserialize(
    data: dict | None,
    key: str,
    model_class: type[_BaseModel],
) -> _BaseModel | None:
    """Try to deserialize a single extraction."""
    if not isinstance(data, dict):
        return None
    try:
        return model_class.model_validate(data)
    except Exception:
        logger.warning(
            "Failed to deserialize LLM extraction for %s",
            key,
            exc_info=True,
        )
        return None


def _build_filing_date_lookup(
    state: AnalysisState,
    key_prefix: str,
) -> dict[str, str]:
    """Build accession_number -> filing_date mapping from filings metadata."""
    lookup: dict[str, str] = {}
    if state.acquired_data is None:
        return lookup

    # Map key_prefix to filing type
    form_type = key_prefix.rstrip(":")  # "10-K:" -> "10-K"
    filings = state.acquired_data.filings
    if not filings:
        return lookup

    filing_list = filings.get(form_type, []) if isinstance(filings, dict) else []
    for f in filing_list:
        if not isinstance(f, dict):
            continue
        acc = f.get("accession") or f.get("accession_number") or ""
        date = f.get("filing_date", "")
        if acc and date:
            lookup[acc] = str(date)

    return lookup
