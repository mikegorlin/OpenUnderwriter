"""Extraction manifest: derive field requirements from brain checks.

Builds a structured manifest of what the EXTRACT stage needs to produce
to satisfy all brain checks. Constructed at EXTRACT start, consumed by
LLM prompt enhancer and sub-orchestrators, produces an actionable gap
report at EXTRACT end.

The manifest serves all 4 data complexity layers:
  1. DISPLAY (depth 1) -- extract & show
  2. COMPUTE (depth 2) -- extract inputs, apply formula
  3. INFER  (depth 3) -- multi-signal synthesis
  4. HUNT   (depth 4) -- broad search + aggregate
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Source types that require broad web search (depth 4 / HUNT)
_BROAD_SEARCH_SOURCES = frozenset({
    "WEB_SEARCH", "NEWS_SEARCH", "COURTLISTENER",
})

# Map source types to suggested extraction actions
_SOURCE_SUGGESTIONS: dict[str, str] = {
    "SEC_10K": "Enhance LLM prompt for 10-K",
    "SEC_20F": "Enhance LLM prompt for 20-F",
    "SEC_DEF14A": "Enhance LLM prompt for DEF 14A",
    "SEC_8K": "Enhance LLM prompt for 8-K",
    "SEC_10Q": "Enhance LLM prompt for 10-Q",
    "MARKET_PRICE": "Add to yfinance/stock extraction",
    "MARKET_DATA": "Add to market data extraction",
    "XBRL": "Add to XBRL financial extraction",
    "YFINANCE": "Add to yfinance extraction",
    "WEB_SEARCH": "Add web search extractor",
    "NEWS_SEARCH": "Add news search extractor",
    "COURTLISTENER": "Add CourtListener search",
    "SCAC": "Add SCAC database lookup",
}

# Map brain source types to LLM filing types
SOURCE_TO_FILING_TYPE: dict[str, list[str]] = {
    "SEC_10K": ["10-K", "20-F"],
    "SEC_20F": ["10-K", "20-F"],
    "SEC_DEF14A": ["DEF 14A"],
    "SEC_8K": ["8-K"],
    "SEC_10Q": ["10-Q", "6-K"],
}


@dataclass
class FieldRequirement:
    """A single field the brain needs extracted."""

    field_key: str
    primary_source: str
    signal_ids: list[str] = field(default_factory=list)
    signal_names: list[str] = field(default_factory=list)
    depth: int = 2
    content_type: str = "EVALUATIVE_CHECK"
    extraction_hint: dict[str, Any] | None = None
    is_multi_signal: bool = False
    acquisition_type: str = "structured"  # "structured" or "broad_search"

    @property
    def suggested_action(self) -> str:
        """Suggest how to extract this field."""
        return _SOURCE_SUGGESTIONS.get(
            self.primary_source, f"Add extractor for {self.primary_source}"
        )


@dataclass
class ExtractionGap:
    """A field that was required but not extracted."""

    field_key: str
    source: str
    signal_ids: list[str]
    signal_names: list[str]
    depth: int
    suggested_action: str
    is_multi_signal: bool = False
    acquisition_type: str = "structured"


@dataclass
class ExtractionGapReport:
    """Summary of extraction coverage vs brain requirements."""

    total_requirements: int
    fulfilled: int
    gaps: list[ExtractionGap]

    @property
    def coverage_pct(self) -> float:
        """Percentage of requirements fulfilled."""
        if self.total_requirements == 0:
            return 100.0
        return self.fulfilled / self.total_requirements * 100.0


class ExtractionManifest:
    """Requirements manifest built from brain check definitions.

    Groups all brain checks by their data_strategy.primary_source and
    field_key, deduplicates, and provides source-level filtering,
    fulfillment tracking, and gap reporting.
    """

    def __init__(self) -> None:
        self._requirements: dict[str, FieldRequirement] = {}
        self._fulfilled: set[str] = set()

    @classmethod
    def from_brain_signals(cls, checks: list[dict[str, Any]]) -> ExtractionManifest:
        """Build manifest from enriched check definitions.

        Only processes AUTO-mode checks that have data_strategy with
        both field_key and primary_source defined.
        """
        manifest = cls()
        for check in checks:
            if check.get("execution_mode") != "AUTO":
                continue

            data_strategy = check.get("data_strategy")
            if not isinstance(data_strategy, dict):
                continue

            field_key = data_strategy.get("field_key")
            primary_source = data_strategy.get("primary_source")
            if not field_key or not primary_source:
                continue

            signal_id = check.get("id", "")
            signal_name = check.get("name", signal_id)
            depth = check.get("depth", 2)
            content_type = check.get("content_type", "EVALUATIVE_CHECK")

            # Parse extraction hints
            hint = check.get("extraction_hints") or check.get(
                "_brain_extraction_hints"
            )
            if isinstance(hint, str):
                import json
                try:
                    hint = json.loads(hint)
                except (json.JSONDecodeError, ValueError):
                    hint = None

            is_multi_signal = content_type == "INFERENCE_PATTERN"
            is_hunt = primary_source in _BROAD_SEARCH_SOURCES or depth == 4
            acq_type = "broad_search" if is_hunt else "structured"

            if field_key in manifest._requirements:
                # Merge into existing requirement
                req = manifest._requirements[field_key]
                if signal_id not in req.signal_ids:
                    req.signal_ids.append(signal_id)
                    req.signal_names.append(signal_name)
                # Promote to multi-signal if any check is inference
                if is_multi_signal:
                    req.is_multi_signal = True
                if is_hunt:
                    req.acquisition_type = "broad_search"
                # Keep the shallowest depth (highest priority)
                if depth < req.depth:
                    req.depth = depth
                # Merge hints
                if hint and not req.extraction_hint:
                    req.extraction_hint = hint
            else:
                manifest._requirements[field_key] = FieldRequirement(
                    field_key=field_key,
                    primary_source=primary_source,
                    signal_ids=[signal_id],
                    signal_names=[signal_name],
                    depth=depth,
                    content_type=content_type,
                    extraction_hint=hint if isinstance(hint, dict) else None,
                    is_multi_signal=is_multi_signal,
                    acquisition_type=acq_type,
                )

        logger.info(
            "ExtractionManifest: %d unique field requirements from %d signals",
            len(manifest._requirements),
            sum(len(r.signal_ids) for r in manifest._requirements.values()),
        )
        return manifest

    @property
    def requirements(self) -> dict[str, FieldRequirement]:
        """All field requirements keyed by field_key."""
        return self._requirements

    def get_requirements_for_source(
        self, source: str,
    ) -> list[FieldRequirement]:
        """Filter requirements to a single source type."""
        return [
            r for r in self._requirements.values()
            if r.primary_source == source
        ]

    def get_requirements_for_filing_type(
        self, filing_type: str,
    ) -> list[FieldRequirement]:
        """Filter requirements to those extractable from a filing type.

        Maps filing types (10-K, DEF 14A) back to brain source types
        (SEC_10K, SEC_DEF14A) and returns matching requirements.
        """
        # Find which brain sources map to this filing type
        matching_sources: set[str] = set()
        for source, filing_types in SOURCE_TO_FILING_TYPE.items():
            if filing_type in filing_types:
                matching_sources.add(source)

        return [
            r for r in self._requirements.values()
            if r.primary_source in matching_sources
        ]

    def mark_fulfilled(self, field_key: str) -> None:
        """Record that a field was successfully extracted."""
        self._fulfilled.add(field_key)

    def mark_fulfilled_batch(self, field_keys: set[str]) -> None:
        """Record multiple fields as extracted."""
        self._fulfilled.update(field_keys)

    def get_gap_report(self) -> ExtractionGapReport:
        """Produce actionable gap report showing what's missing."""
        gaps: list[ExtractionGap] = []
        for field_key, req in sorted(self._requirements.items()):
            if field_key not in self._fulfilled:
                gaps.append(ExtractionGap(
                    field_key=field_key,
                    source=req.primary_source,
                    signal_ids=req.signal_ids,
                    signal_names=req.signal_names,
                    depth=req.depth,
                    suggested_action=req.suggested_action,
                    is_multi_signal=req.is_multi_signal,
                    acquisition_type=req.acquisition_type,
                ))

        return ExtractionGapReport(
            total_requirements=len(self._requirements),
            fulfilled=len(self._fulfilled & set(self._requirements.keys())),
            gaps=gaps,
        )


def build_extraction_manifest() -> ExtractionManifest:
    """Build manifest from brain.duckdb checks.

    Convenience function that loads signals via BrainLoader and
    constructs the manifest. Gracefully returns empty manifest if
    brain is unavailable.
    """
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        result = load_signals()
        checks: list[dict[str, Any]] = result.get("signals", [])

        return ExtractionManifest.from_brain_signals(checks)
    except Exception:
        logger.warning(
            "Failed to build extraction manifest from brain; "
            "returning empty manifest",
            exc_info=True,
        )
        return ExtractionManifest()


__all__ = [
    "SOURCE_TO_FILING_TYPE",
    "ExtractionGap",
    "ExtractionGapReport",
    "ExtractionManifest",
    "FieldRequirement",
    "build_extraction_manifest",
]
