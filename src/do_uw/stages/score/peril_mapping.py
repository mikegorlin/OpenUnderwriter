"""7-lens plaintiff assessment engine for peril mapping.

Aggregates check results by plaintiff lens to build PlaintiffAssessments.
Shareholders/regulators get FULL probabilistic modeling; others get
PROPORTIONAL count-based estimation. Bear cases added by Plan 04.

Public API: build_peril_map(state) -> PerilMap
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.peril import (
    PerilMap,
    PerilProbabilityBand,
    PerilSeverityBand,
    PlaintiffAssessment,
    PlaintiffFirmMatch,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.signal_results import DataStatus, PlaintiffLens, SignalStatus

logger = logging.getLogger(__name__)

_FULL_MODEL_LENSES = frozenset({PlaintiffLens.SHAREHOLDERS, PlaintiffLens.REGULATORS})


_PROB_BAND_ORDER: dict[str, int] = {
    PerilProbabilityBand.VERY_LOW: 0, PerilProbabilityBand.LOW: 1,
    PerilProbabilityBand.MODERATE: 2, PerilProbabilityBand.ELEVATED: 3,
    PerilProbabilityBand.HIGH: 4,
}


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def build_peril_map(state: AnalysisState) -> PerilMap:
    """Build 7-lens peril map from analysis state."""
    signal_results = _get_signal_results(state)
    lens_defaults = _load_lens_defaults()
    firms_config = _load_plaintiff_firms_config()
    claim_probability = _get_claim_probability(state)
    severity_scenarios = _get_severity_scenarios(state)
    allegation_mapping = _get_allegation_mapping(state)

    assessments: list[PlaintiffAssessment] = []
    for lens in PlaintiffLens:
        assessments.append(assess_lens(
            lens, signal_results, lens_defaults,
            claim_probability, severity_scenarios, allegation_mapping,
        ))

    firm_matches = match_plaintiff_firms(state, firms_config)
    overall_rating = _compute_overall_rating(assessments)
    coverage_gaps = _collect_coverage_gaps(signal_results)

    peril_map = PerilMap(
        assessments=assessments,
        bear_cases=[],  # Populated by Plan 04
        plaintiff_firm_matches=firm_matches,
        overall_peril_rating=overall_rating,
        coverage_gaps=coverage_gaps,
    )
    logger.info(
        "Peril map: overall=%s, %d firms, %d gaps",
        overall_rating, len(firm_matches), len(coverage_gaps),
    )
    return peril_map


# -----------------------------------------------------------------------
# Per-lens assessment
# -----------------------------------------------------------------------


def assess_lens(
    lens: PlaintiffLens,
    signal_results: list[dict[str, Any]],
    lens_defaults: dict[str, list[str]],
    claim_probability: dict[str, Any] | None,
    severity_scenarios: dict[str, Any] | None,
    allegation_mapping: dict[str, Any] | None,
) -> PlaintiffAssessment:
    """Assess a single plaintiff lens from check results."""
    is_full = lens in _FULL_MODEL_LENSES
    lens_checks = _filter_checks_by_lens(signal_results, lens, lens_defaults)

    triggered = [c for c in lens_checks if c.get("status") == SignalStatus.TRIGGERED]
    evaluated = [
        c for c in lens_checks
        if c.get("data_status", "EVALUATED") == DataStatus.EVALUATED
        and c.get("status") != SignalStatus.SKIPPED
    ]

    probability_band = _map_to_probability_band(
        len(triggered), len(lens_checks), claim_probability, is_full,
    )
    severity_band = _map_to_severity_band(
        severity_scenarios, triggered, is_full,
    )
    key_findings = _extract_key_findings(triggered, max_findings=5)

    return PlaintiffAssessment(
        plaintiff_type=lens.value,
        probability_band=probability_band,
        severity_band=severity_band,
        triggered_signal_count=len(triggered),
        total_signal_count=len(lens_checks),
        evaluated_signal_count=len(evaluated),
        key_findings=key_findings,
        modeling_depth="FULL" if is_full else "PROPORTIONAL",
    )


# -----------------------------------------------------------------------
# Probability and severity band mapping
# -----------------------------------------------------------------------


def _map_to_probability_band(
    triggered_count: int, total_count: int,
    claim_probability: dict[str, Any] | None, is_full_model: bool,
) -> str:
    """Map to peril probability band (full or proportional)."""
    if is_full_model and claim_probability is not None:
        return _full_model_probability(triggered_count, total_count, claim_probability)
    return _proportional_probability(triggered_count)


def _full_model_probability(
    triggered_count: int, total_count: int, claim_probability: dict[str, Any],
) -> str:
    """Full model: claim probability range + triggered ratio."""
    range_high = claim_probability.get("range_high_pct", 5.0)

    if range_high <= 2.0:
        base_band = PerilProbabilityBand.LOW
    elif range_high <= 5.0:
        base_band = PerilProbabilityBand.MODERATE
    elif range_high <= 10.0:
        base_band = PerilProbabilityBand.ELEVATED
    else:
        base_band = PerilProbabilityBand.HIGH

    if total_count > 0:
        ratio = triggered_count / total_count
        order = _PROB_BAND_ORDER.get(base_band, 0)
        if ratio > 0.5 and order < 4:
            base_band = _band_from_order(order + 1)
        elif ratio == 0 and order > 0:
            base_band = _band_from_order(order - 1)

    return base_band


def _proportional_probability(triggered_count: int) -> str:
    """Count-based: 0=VERY_LOW, 1-2=LOW, 3-5=MODERATE, 6+=ELEVATED."""
    if triggered_count == 0:
        return PerilProbabilityBand.VERY_LOW
    if triggered_count <= 2:
        return PerilProbabilityBand.LOW
    if triggered_count <= 5:
        return PerilProbabilityBand.MODERATE
    return PerilProbabilityBand.ELEVATED


def _map_to_severity_band(
    severity_scenarios: dict[str, Any] | None,
    triggered_checks: list[dict[str, Any]], is_full_model: bool,
) -> str:
    """Map to severity band (full or proportional)."""
    if is_full_model and severity_scenarios is not None:
        return _full_model_severity(severity_scenarios)
    return _proportional_severity(len(triggered_checks))


def _full_model_severity(severity_scenarios: dict[str, Any]) -> str:
    """50th pct settlement: <$5M=NUISANCE, $5-25M=MINOR, $25-100M=MODERATE,
    $100-500M=SIGNIFICANT, $500M+=SEVERE."""
    scenarios = severity_scenarios.get("scenarios", [])
    median_settlement = 0.0
    for s in scenarios:
        if s.get("percentile") == 50 or s.get("label") == "median":
            median_settlement = s.get("settlement_estimate", 0.0)
            break

    if median_settlement < 5_000_000:
        return PerilSeverityBand.NUISANCE
    if median_settlement < 25_000_000:
        return PerilSeverityBand.MINOR
    if median_settlement < 100_000_000:
        return PerilSeverityBand.MODERATE
    if median_settlement < 500_000_000:
        return PerilSeverityBand.SIGNIFICANT
    return PerilSeverityBand.SEVERE


def _proportional_severity(triggered_count: int) -> str:
    """Count-based: 0=NUISANCE, 1-2=MINOR, 3-4=MODERATE, 5+=SIGNIFICANT."""
    if triggered_count == 0:
        return PerilSeverityBand.NUISANCE
    if triggered_count <= 2:
        return PerilSeverityBand.MINOR
    if triggered_count <= 4:
        return PerilSeverityBand.MODERATE
    return PerilSeverityBand.SIGNIFICANT


# -----------------------------------------------------------------------
# Plaintiff firm matching
# -----------------------------------------------------------------------


def match_plaintiff_firms(
    state: AnalysisState, firms_config: dict[str, Any],
) -> list[PlaintiffFirmMatch]:
    """Match plaintiff firms from litigation data against tier config."""
    if state.extracted is None or state.extracted.litigation is None:
        return []

    litigation = state.extracted.litigation
    matches: list[PlaintiffFirmMatch] = []
    seen: set[str] = set()

    for i, case in enumerate(litigation.securities_class_actions):
        if case.lead_counsel is not None and case.lead_counsel.value:
            m = _match_firm_to_tier(case.lead_counsel.value, firms_config)
            if m is not None and m.firm_name not in seen:
                m.match_source = f"securities_class_actions[{i}].lead_counsel"
                matches.append(m)
                seen.add(m.firm_name)

    for i, case in enumerate(litigation.derivative_suits):
        if case.lead_counsel is not None and case.lead_counsel.value:
            m = _match_firm_to_tier(case.lead_counsel.value, firms_config)
            if m is not None and m.firm_name not in seen:
                m.match_source = f"derivative_suits[{i}].lead_counsel"
                matches.append(m)
                seen.add(m.firm_name)

    if matches:
        logger.info(
            "Matched %d plaintiff firms: %s",
            len(matches),
            ", ".join(f"{m.firm_name} (tier {m.tier})" for m in matches),
        )
    return matches


def _match_firm_to_tier(
    counsel_text: str, firms_config: dict[str, Any],
) -> PlaintiffFirmMatch | None:
    """Substring-match counsel against firm tiers (priority: tier 1 > 2)."""
    tiers = firms_config.get("tiers", {})
    counsel_lower = counsel_text.lower()
    for tier_num in ("1", "2"):
        tier_data = tiers.get(tier_num, {})
        for firm in tier_data.get("firms", []):
            if firm.lower() in counsel_lower:
                return PlaintiffFirmMatch(
                    firm_name=firm, tier=int(tier_num),
                    severity_multiplier=tier_data.get("severity_multiplier", 1.0),
                    match_source="",
                )
    return None


# -----------------------------------------------------------------------
# Key findings extraction
# -----------------------------------------------------------------------


def _extract_key_findings(
    triggered_checks: list[dict[str, Any]], max_findings: int = 5,
) -> list[str]:
    """Extract top triggered checks as findings (DECISION_DRIVING first)."""
    sorted_checks = sorted(
        triggered_checks,
        key=lambda c: (
            0 if c.get("category") == "DECISION_DRIVING" else 1,
            c.get("signal_id", ""),
        ),
    )
    findings: list[str] = []
    for check in sorted_checks[:max_findings]:
        name = check.get("signal_name", check.get("signal_id", "unknown"))
        evidence = check.get("evidence", "")
        findings.append(f"{name}: {evidence}" if evidence else name)
    return findings


# -----------------------------------------------------------------------
# State extraction helpers
# -----------------------------------------------------------------------


def _get_signal_results(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract check results as list of dicts from state."""
    if state.analysis is None or not state.analysis.signal_results:
        return []
    return [r for r in state.analysis.signal_results.values() if isinstance(r, dict)]


def _filter_checks_by_lens(
    signal_results: list[dict[str, Any]],
    lens: PlaintiffLens,
    lens_defaults: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Filter checks to those mapped to a specific plaintiff lens."""
    filtered: list[dict[str, Any]] = []
    lens_value = lens.value
    for check in signal_results:
        lenses = check.get("plaintiff_lenses", [])
        if lenses:
            if lens_value in lenses:
                filtered.append(check)
            continue
        signal_id = check.get("signal_id", "")
        if lens_value in _resolve_lens_defaults(signal_id, lens_defaults):
            filtered.append(check)
    return filtered


def _resolve_lens_defaults(
    signal_id: str, lens_defaults: dict[str, list[str]],
) -> list[str]:
    """Resolve lens defaults for signal_id using prefix matching."""
    if signal_id in lens_defaults:
        return lens_defaults[signal_id]
    parts = signal_id.split(".")
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in lens_defaults:
            return lens_defaults[prefix]
    return []


def _load_lens_defaults() -> dict[str, list[str]]:
    """Load plaintiff_lens_defaults from signal_classification.json."""
    config = load_config("signal_classification")
    return config.get("plaintiff_lens_defaults", {})


def _load_plaintiff_firms_config() -> dict[str, Any]:
    """Load plaintiff_firms.json config."""
    config = load_config("plaintiff_firms")
    return config if config else {"tiers": {}}


def _get_claim_probability(state: AnalysisState) -> dict[str, Any] | None:
    """Extract ClaimProbability dict from scoring result."""
    if state.scoring is None or state.scoring.claim_probability is None:
        return None
    return state.scoring.claim_probability.model_dump()


def _get_severity_scenarios(state: AnalysisState) -> dict[str, Any] | None:
    """Extract SeverityScenarios dict from scoring result."""
    if state.scoring is None or state.scoring.severity_scenarios is None:
        return None
    return state.scoring.severity_scenarios.model_dump()


def _get_allegation_mapping(state: AnalysisState) -> dict[str, Any] | None:
    """Extract AllegationMapping dict from scoring result."""
    if state.scoring is None or state.scoring.allegation_mapping is None:
        return None
    return state.scoring.allegation_mapping.model_dump()


def _compute_overall_rating(assessments: list[PlaintiffAssessment]) -> str:
    """Overall peril rating = max probability band across all lenses."""
    max_order = max(
        (_PROB_BAND_ORDER.get(a.probability_band, 0) for a in assessments),
        default=0,
    )
    return _band_from_order(max_order)


def _band_from_order(order: int) -> str:
    """Convert band order back to PerilProbabilityBand string."""
    for band, o in _PROB_BAND_ORDER.items():
        if o == order:
            return band
    return PerilProbabilityBand.VERY_LOW


def _collect_coverage_gaps(signal_results: list[dict[str, Any]]) -> list[str]:
    """Collect check IDs with DATA_UNAVAILABLE for coverage gap reporting."""
    gaps: list[str] = []
    for check in signal_results:
        if check.get("data_status", "EVALUATED") == DataStatus.DATA_UNAVAILABLE:
            cid = check.get("signal_id", "unknown")
            reason = check.get("data_status_reason", "")
            gaps.append(f"{cid}: {reason}" if reason else f"{cid}: DATA_UNAVAILABLE")
    return gaps


__all__ = ["build_peril_map"]
