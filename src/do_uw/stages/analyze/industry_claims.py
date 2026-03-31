"""Industry claim pattern extraction (SECT6-10).

Maps company SIC code to industry-specific legal theories from
config/industry_theories.json. Identifies contagion risk from
peer companies and assesses exposure based on business description.

Usage:
    patterns, report = extract_industry_claim_patterns(state)
    state.extracted.litigation.industry_patterns = patterns
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation_details import IndustryClaimPattern
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import sourced_str
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

_CONFIG_FILE = "industry_theories.json"
_SOURCE = "config/industry_theories.json"

EXPECTED_FIELDS: list[str] = [
    "industry_match",
    "theories_mapped",
    "peer_examples",
    "contagion_risks",
    "exposure_assessments",
]


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _load_industry_theories() -> dict[str, Any]:
    """Load industry_theories.json from config directory.

    Returns:
        Parsed JSON dict with 'industry_theories' key.
    """
    return load_config("industry_theories")


def _parse_sic_range(range_str: str) -> tuple[int, int] | None:
    """Parse a SIC range string like '2830-2836' into (start, end).

    Returns None if the format is invalid.
    """
    parts = range_str.split("-")
    if len(parts) != 2:
        return None
    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        return None
    return (start, end)


def find_matching_industries(
    sic_code: int, theories_config: dict[str, Any]
) -> list[tuple[str, dict[str, Any]]]:
    """Find all industry entries whose SIC range contains the given code.

    Args:
        sic_code: Company's SIC code.
        theories_config: The 'industry_theories' dict from config.

    Returns:
        List of (range_key, industry_entry) tuples that match.
    """
    matches: list[tuple[str, dict[str, Any]]] = []
    for range_key, entry in theories_config.items():
        parsed = _parse_sic_range(range_key)
        if parsed is None:
            continue
        start, end = parsed
        if start <= sic_code <= end:
            if isinstance(entry, dict):
                matches.append((range_key, cast(dict[str, Any], entry)))
    return matches


def build_claim_pattern(
    theory: dict[str, Any],
    sic_range: str,
    industry_name: str,
) -> IndustryClaimPattern:
    """Build an IndustryClaimPattern from a theory config entry.

    Args:
        theory: Single theory dict from config (theory, description,
            legal_basis).
        sic_range: SIC range string like '7370-7379'.
        industry_name: Industry display name.

    Returns:
        Populated IndustryClaimPattern.
    """
    theory_name = str(theory.get("theory", "unknown"))
    description = str(theory.get("description", ""))

    pattern = IndustryClaimPattern()
    pattern.legal_theory = sourced_str(
        theory_name, _SOURCE, Confidence.HIGH
    )
    pattern.description = sourced_str(
        f"[{industry_name}] {description}",
        _SOURCE,
        Confidence.HIGH,
    )
    pattern.sic_range = sourced_str(sic_range, _SOURCE, Confidence.HIGH)
    pattern.this_company_exposed = SourcedValue[bool](
        value=True,
        source=_SOURCE,
        confidence=Confidence.MEDIUM,
        as_of=_now(),
    )
    pattern.exposure_rationale = sourced_str(
        f"Company SIC code falls within {industry_name} range ({sic_range})",
        _SOURCE,
        Confidence.MEDIUM,
    )
    # Default contagion risk -- set to True for same-industry patterns.
    pattern.contagion_risk = SourcedValue[bool](
        value=True,
        source=_SOURCE,
        confidence=Confidence.LOW,
        as_of=_now(),
    )
    return pattern


def enrich_with_peer_data(
    patterns: list[IndustryClaimPattern],
    state: AnalysisState,
) -> int:
    """Cross-reference patterns with peer group data if available.

    Adds peer company names as examples. Returns the count of peers
    referenced.

    Args:
        patterns: List of IndustryClaimPattern to enrich.
        state: Analysis state with potential peer group data.

    Returns:
        Number of peer references added.
    """
    peer_count = 0
    if (
        state.extracted is None
        or state.extracted.financials is None
        or state.extracted.financials.peer_group is None
    ):
        return peer_count

    peer_group = state.extracted.financials.peer_group
    peer_names: list[str] = []

    # PeerCompany has plain str fields (name, ticker), not SourcedValue.
    for peer in peer_group.peers:
        if peer.name:
            peer_names.append(peer.name)
        elif peer.ticker:
            peer_names.append(peer.ticker)

    if not peer_names:
        return peer_count

    for pattern in patterns:
        # Add up to 3 peers as examples.
        for name in peer_names[:3]:
            pattern.peer_examples.append(
                sourced_str(
                    name,
                    "peer group analysis",
                    Confidence.LOW,
                )
            )
            peer_count += 1

    return peer_count


def extract_industry_claim_patterns(
    state: AnalysisState,
) -> tuple[list[IndustryClaimPattern], ExtractionReport]:
    """Extract industry claim patterns based on company SIC code.

    Loads industry_theories.json, matches SIC code to industry
    ranges, creates IndustryClaimPattern for each matching theory,
    and enriches with peer company data if available.

    Args:
        state: Analysis state with company identity (SIC code).

    Returns:
        Tuple of (list[IndustryClaimPattern], ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    patterns: list[IndustryClaimPattern] = []

    # --- Get SIC code ---
    sic_code = _get_sic_code(state)
    if sic_code is None:
        warnings.append("No SIC code available for industry matching")
        report = create_report(
            extractor_name="industry_claim_patterns",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=_SOURCE,
            warnings=warnings,
        )
        log_report(report)
        return patterns, report

    # --- Load config ---
    config = _load_industry_theories()
    theories_dict = config.get("industry_theories", {})
    if not theories_dict:
        warnings.append("No industry theories loaded from config")
        report = create_report(
            extractor_name="industry_claim_patterns",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=_SOURCE,
            warnings=warnings,
        )
        log_report(report)
        return patterns, report

    # --- Match SIC to industry ranges ---
    matches = find_matching_industries(
        sic_code, cast(dict[str, Any], theories_dict)
    )
    if matches:
        found.append("industry_match")
    else:
        warnings.append(
            f"SIC code {sic_code} does not match any industry range"
        )

    # --- Build patterns for each matching theory ---
    contagion_count = 0
    for range_key, industry_entry in matches:
        industry_name = str(industry_entry.get("industry", "Unknown"))
        theories_raw = industry_entry.get("theories", [])
        if not isinstance(theories_raw, list):
            continue
        theories = cast(list[Any], theories_raw)
        for theory in theories:
            if not isinstance(theory, dict):
                continue
            pattern = build_claim_pattern(
                cast(dict[str, Any], theory),
                range_key,
                industry_name,
            )
            patterns.append(pattern)
            contagion_count += 1

    if patterns:
        found.append("theories_mapped")
        found.append("contagion_risks")
        found.append("exposure_assessments")

    # --- Enrich with peer data ---
    peer_refs = enrich_with_peer_data(patterns, state)
    if peer_refs > 0:
        found.append("peer_examples")

    logger.info(
        "Industry claims: %d theories matched for SIC %d, "
        "%d peer references",
        len(patterns),
        sic_code,
        peer_refs,
    )

    report = create_report(
        extractor_name="industry_claim_patterns",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=_SOURCE,
        warnings=warnings,
    )
    log_report(report)
    return patterns, report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_sic_code(state: AnalysisState) -> int | None:
    """Extract SIC code from company identity.

    Returns None if not available.
    """
    if state.company is None:
        return None
    sic_sv = state.company.identity.sic_code
    if sic_sv is None:
        return None
    try:
        return int(sic_sv.value)
    except (ValueError, TypeError):
        return None
