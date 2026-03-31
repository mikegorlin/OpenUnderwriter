"""Chain validator: traces every signal's data chain end-to-end.

A complete signal chain has 4 links:
  1. ACQUIRE -- signal has an acquisition source (V2 AcquisitionSpec, tier1, or BASE.* prefix)
  2. EXTRACT -- signal has a field_key (data_strategy.field_key or FIELD_FOR_CHECK entry)
  3. ANALYZE -- signal has evaluation logic (V2 EvaluationSpec or meaningful threshold)
  4. RENDER  -- signal is assigned to a facet in the output manifest

Foundational signals (signal_class='foundational') only require links 1+2; links 3+4 are N/A.
INACTIVE signals (lifecycle_state='INACTIVE') are separated from chain stats.

Phase 77 Plan 01 (original). Phase 81 Plan 01: switched render-link resolution
from section YAML facets (135 signals) to manifest facets (476 signals).
"""

from __future__ import annotations

import enum
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from do_uw.brain.brain_signal_schema import BrainSignalEntry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChainGapType(str, enum.Enum):
    """Categories of broken chain links."""

    NO_ACQUISITION = "NO_ACQUISITION"
    MISSING_FIELD_KEY = "MISSING_FIELD_KEY"
    NO_EVALUATION = "NO_EVALUATION"
    NO_FACET = "NO_FACET"


# ---------------------------------------------------------------------------
# Pydantic report models
# ---------------------------------------------------------------------------


class ChainLink(BaseModel):
    """Status of a single link in the chain."""

    link_type: str = Field(description="acquire, extract, analyze, or render")
    status: str = Field(description="complete, broken, or na")
    detail: str = Field(default="", description="What was found or is missing")


class SignalChainResult(BaseModel):
    """Chain validation result for a single signal."""

    signal_id: str
    signal_name: str
    signal_type: str = Field(description="evaluate or foundational")
    chain_status: str = Field(description="complete, broken, or inactive")
    gaps: list[ChainGapType] = Field(default_factory=list)
    links: list[ChainLink] = Field(default_factory=list)


class GapSummary(BaseModel):
    """Aggregated gap info for one gap type."""

    gap_type: ChainGapType
    signal_ids: list[str] = Field(default_factory=list)
    count: int = 0


class ChainReport(BaseModel):
    """Full chain validation report across all signals."""

    total_signals: int = 0
    chain_complete: int = 0
    chain_broken: int = 0
    inactive_count: int = 0
    results: list[SignalChainResult] = Field(default_factory=list)
    gap_summary: list[GapSummary] = Field(default_factory=list)
    foundational_complete: int = 0
    foundational_broken: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Threshold types that indicate no real evaluation logic (display-only)
_DISPLAY_THRESHOLD_TYPES = frozenset({"display", "info", "info_display"})


def _is_inactive(signal: BrainSignalEntry) -> bool:
    """Detect INACTIVE signals.

    Checks the `lifecycle_state` extra field set on some signals in YAML.
    The field is not in the Pydantic schema but loaded via extra='allow'.
    """
    lifecycle = getattr(signal, "lifecycle_state", None)
    if lifecycle and str(lifecycle).upper() == "INACTIVE":
        return True
    return False


def _has_meaningful_threshold(signal: BrainSignalEntry) -> bool:
    """Check if the signal's legacy threshold contains real evaluation logic."""
    t = signal.threshold
    if t.type in _DISPLAY_THRESHOLD_TYPES:
        return False
    # Has at least one defined level
    return any([t.red, t.yellow, t.clear, t.triggered])


def _build_facet_signal_map(
    manifest: Any,
) -> dict[str, set[str]]:
    """Build {group_id: set(signal_ids)} from manifest groups (or legacy facets).

    In v3 (groups-based manifest), signals self-select into groups via their
    `group` field. Uses collect_signals_by_group for resolution.
    Falls back to legacy facet.signals for backward compat.
    """
    # Check if facets have embedded signal lists (legacy/test manifests)
    has_facet_signals = any(
        facet.signals
        for section in manifest.sections
        for facet in section.facets
    )

    if has_facet_signals:
        # Legacy: read from facet.signals (embedded in manifest)
        result: dict[str, set[str]] = {}
        for section in manifest.sections:
            for facet in section.facets:
                if facet.id not in result:
                    result[facet.id] = set()
                result[facet.id].update(facet.signals)
        return result

    # V3: signals self-select into groups via their `group` field
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import collect_signals_by_group

    sigs = load_signals()["signals"]
    sig_groups = collect_signals_by_group(sigs)

    result = {}
    for section in manifest.sections:
        for group in section.groups:
            result[group.id] = set(sig_groups.get(group.id, []))
    return result


def _find_signal_facets(
    signal_id: str,
    facet_signal_map: dict[str, set[str]],
) -> list[str]:
    """Return list of facet IDs that include this signal."""
    return [fid for fid, sids in facet_signal_map.items() if signal_id in sids]


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def validate_single_chain(
    signal: BrainSignalEntry,
    facet_signal_map: dict[str, set[str]],
    manifest: Any,
    field_routing_keys: set[str],
) -> SignalChainResult:
    """Validate one signal's data chain across 4 links.

    Args:
        signal: The signal to validate.
        facet_signal_map: Pre-computed {facet_id: set(signal_ids)} from manifest.
        manifest: OutputManifest (unused after Phase 81, kept for API compat).
        field_routing_keys: Set of signal IDs that have FIELD_FOR_CHECK entries.

    Returns:
        SignalChainResult with chain_status, gaps, and per-link details.
    """
    # Check for inactive first
    if _is_inactive(signal):
        return SignalChainResult(
            signal_id=signal.id,
            signal_name=signal.name,
            signal_type=signal.signal_class,
            chain_status="inactive",
            gaps=[],
            links=[],
        )

    is_foundational = signal.signal_class == "foundational"
    gaps: list[ChainGapType] = []
    links: list[ChainLink] = []

    # --- Link 1: ACQUIRE ---
    has_acquisition = False
    acquire_detail = ""

    if signal.acquisition and signal.acquisition.sources:
        has_acquisition = True
        acquire_detail = f"V2 acquisition: {len(signal.acquisition.sources)} source(s)"
    elif signal.acquisition_tier and signal.acquisition_tier.lower() in ("tier1", "l1", "t1"):
        has_acquisition = True
        acquire_detail = f"Tier 1 acquisition ({signal.acquisition_tier})"
    elif signal.id.startswith("BASE."):
        has_acquisition = True
        acquire_detail = "BASE.* prefix (implicit Tier 1)"
    elif signal.data_strategy and signal.data_strategy.get("primary_source"):
        has_acquisition = True
        acquire_detail = f"data_strategy.primary_source: {signal.data_strategy['primary_source']}"

    if has_acquisition:
        links.append(ChainLink(link_type="acquire", status="complete", detail=acquire_detail))
    else:
        gaps.append(ChainGapType.NO_ACQUISITION)
        links.append(ChainLink(link_type="acquire", status="broken", detail="No acquisition source found"))

    # --- Link 2: EXTRACT ---
    has_field_key = False
    extract_detail = ""

    if signal.data_strategy and signal.data_strategy.get("field_key"):
        has_field_key = True
        extract_detail = f"field_key: {signal.data_strategy['field_key']}"
    elif signal.id in field_routing_keys:
        has_field_key = True
        extract_detail = f"FIELD_FOR_CHECK entry: {signal.id}"

    if has_field_key:
        links.append(ChainLink(link_type="extract", status="complete", detail=extract_detail))
    else:
        gaps.append(ChainGapType.MISSING_FIELD_KEY)
        links.append(ChainLink(link_type="extract", status="broken", detail="No field_key or FIELD_FOR_CHECK entry"))

    # --- Link 3: ANALYZE (evaluate signals only) ---
    if is_foundational:
        links.append(ChainLink(link_type="analyze", status="na", detail="Foundational signal -- N/A"))
    else:
        has_evaluation = False
        analyze_detail = ""

        if signal.evaluation and signal.evaluation.thresholds:
            has_evaluation = True
            analyze_detail = f"V2 evaluation: {len(signal.evaluation.thresholds)} threshold(s)"
        elif _has_meaningful_threshold(signal):
            has_evaluation = True
            analyze_detail = f"Legacy threshold type={signal.threshold.type}"

        if has_evaluation:
            links.append(ChainLink(link_type="analyze", status="complete", detail=analyze_detail))
        else:
            gaps.append(ChainGapType.NO_EVALUATION)
            links.append(ChainLink(link_type="analyze", status="broken", detail="No evaluation spec or meaningful threshold"))

    # --- Link 4: RENDER (evaluate signals only) ---
    if is_foundational:
        links.append(ChainLink(link_type="render", status="na", detail="Foundational signal -- N/A"))
    else:
        signal_facets = _find_signal_facets(signal.id, facet_signal_map)

        if not signal_facets:
            gaps.append(ChainGapType.NO_FACET)
            links.append(ChainLink(link_type="render", status="broken", detail="Signal not in any manifest facet"))
        else:
            links.append(
                ChainLink(
                    link_type="render",
                    status="complete",
                    detail=f"In manifest facet(s): {signal_facets}",
                )
            )

    chain_status = "complete" if not gaps else "broken"

    return SignalChainResult(
        signal_id=signal.id,
        signal_name=signal.name,
        signal_type=signal.signal_class,
        chain_status=chain_status,
        gaps=gaps,
        links=links,
    )


# ---------------------------------------------------------------------------
# Bulk validation
# ---------------------------------------------------------------------------


def validate_all_chains(
    signals_dir: Path | None = None,
    manifest_path: Path | None = None,
) -> ChainReport:
    """Validate data chains for all brain signals.

    Args:
        signals_dir: Override path to brain/signals/ (for testing).
        manifest_path: Override path to output_manifest.yaml (for testing).

    Returns:
        ChainReport with per-signal results and aggregate statistics.
    """
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import load_manifest
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    # Load signals
    if signals_dir:
        from do_uw.brain.brain_unified_loader import _load_and_validate_signals

        raw_signals, _ = _load_and_validate_signals(signals_dir)
        signal_dicts = raw_signals
    else:
        data = load_signals()
        signal_dicts = data["signals"]

    # Parse into BrainSignalEntry objects
    signals: list[BrainSignalEntry] = []
    for raw in signal_dicts:
        if isinstance(raw, BrainSignalEntry):
            signals.append(raw)
        else:
            signals.append(BrainSignalEntry.model_validate(raw))

    # Load manifest and pre-compute facet signal map
    manifest = load_manifest(manifest_path)
    facet_signal_map = _build_facet_signal_map(manifest)

    # Build field routing keys
    field_routing_keys = set(FIELD_FOR_CHECK.keys())

    # Validate each signal
    results: list[SignalChainResult] = []
    complete = 0
    broken = 0
    inactive = 0
    foundational_complete = 0
    foundational_broken = 0
    gap_groups: dict[ChainGapType, list[str]] = {}

    for signal in signals:
        result = validate_single_chain(signal, facet_signal_map, manifest, field_routing_keys)
        results.append(result)

        if result.chain_status == "inactive":
            inactive += 1
        elif result.chain_status == "complete":
            complete += 1
            if result.signal_type == "foundational":
                foundational_complete += 1
        else:
            broken += 1
            if result.signal_type == "foundational":
                foundational_broken += 1

        for gap in result.gaps:
            if gap not in gap_groups:
                gap_groups[gap] = []
            gap_groups[gap].append(result.signal_id)

    # Build gap summary
    gap_summary = [
        GapSummary(gap_type=gt, signal_ids=sids, count=len(sids))
        for gt, sids in sorted(gap_groups.items(), key=lambda x: -len(x[1]))
    ]

    return ChainReport(
        total_signals=len(results),
        chain_complete=complete,
        chain_broken=broken,
        inactive_count=inactive,
        results=results,
        gap_summary=gap_summary,
        foundational_complete=foundational_complete,
        foundational_broken=foundational_broken,
    )


__all__ = [
    "ChainGapType",
    "ChainLink",
    "ChainReport",
    "GapSummary",
    "SignalChainResult",
    "validate_all_chains",
    "validate_single_chain",
]
