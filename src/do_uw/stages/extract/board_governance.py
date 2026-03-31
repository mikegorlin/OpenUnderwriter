"""Board governance quality extraction from proxy statements.

Extracts board member forensic profiles (SECT5-03) and computes
governance quality score (SECT5-07) from DEF 14A text, yfinance
info, and compensation analysis data.

Usage:
    result, report = extract_board_governance(state)
    state.extracted.governance.board_forensics = result[0]
    state.extracted.governance.governance_score = result[1]
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.board_parsing import extract_board_from_proxy
from do_uw.stages.extract.governance_scoring import (
    compute_governance_score,
    score_overboarding,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_info_dict,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

# Re-export public API so existing callers continue to work.
__all__ = [
    "compute_governance_score",
    "extract_board_governance",
    "load_governance_weights",
    "score_overboarding",
]

logger = logging.getLogger(__name__)

EXPECTED_FIELDS: list[str] = [
    "board_members", "independence", "ceo_chair_duality",
    "committees", "overboarding", "tenure", "governance_score",
]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_governance_weights(
    path: Path | None = None,
) -> tuple[dict[str, float], dict[str, float]]:
    """Load governance scoring weights and thresholds from config."""
    if path is not None:
        import json
        if not path.exists():
            logger.warning("Governance weights config not found: %s", path)
            return _fallback_weights(), _fallback_thresholds()
        with path.open(encoding="utf-8") as f:
            data_raw: dict[str, Any] = json.load(f)
    else:
        data_raw = load_config("governance_weights")
        if not data_raw:
            return _fallback_weights(), _fallback_thresholds()

    w_raw, t_raw = data_raw.get("weights"), data_raw.get("thresholds")
    weights = cast(dict[str, float], w_raw) if isinstance(w_raw, dict) else _fallback_weights()
    thresholds = (
        cast(dict[str, float], t_raw) if isinstance(t_raw, dict)
        else _fallback_thresholds()
    )
    return weights, thresholds


def _fallback_weights() -> dict[str, float]:
    return {
        "independence": 0.20, "ceo_chair": 0.15, "refreshment": 0.10,
        "overboarding": 0.10, "committee_structure": 0.15,
        "say_on_pay": 0.15, "tenure": 0.15,
    }


def _fallback_thresholds() -> dict[str, float]:
    return {
        "independence_high": 0.75, "independence_medium": 0.50,
        "overboarded_boards": 4, "refreshment_new_directors_3yr": 2,
        "tenure_ideal_min": 5, "tenure_ideal_max": 10,
        "tenure_concern_max": 15,
        "say_on_pay_strong": 90.0, "say_on_pay_concern": 70.0,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_board_governance(
    state: AnalysisState,
    compensation: CompensationAnalysis | None = None,
    weights_path: Path | None = None,
) -> tuple[tuple[list[BoardForensicProfile], GovernanceQualityScore], ExtractionReport]:
    """Extract board governance profiles and compute quality score.

    Parses DEF 14A proxy statement for director profiles, then scores
    governance quality across 7 config-driven dimensions.

    Returns:
        Tuple of ((board_profiles, governance_score), ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "DEF 14A proxy statement"
    fallbacks: list[str] = []

    weights, thresholds = load_governance_weights(weights_path)

    proxy_text = get_filing_document_text(state, "DEF 14A")
    if not proxy_text.strip():
        fallbacks.append("No DEF 14A text; using yfinance info fallback")
        source_filing = "yfinance info (no proxy text)"
        proxy_text = ""

    profiles = extract_board_from_proxy(proxy_text, state)
    if profiles:
        found.append("board_members")
    if any(p.is_independent is not None for p in profiles):
        found.append("independence")

    # Search acquired litigation data for each director's name.
    # Reuses the same search function used for executives — searches
    # litigation_data, web_search_results, and blind_spot_results for
    # last-name substring matches.
    _search_director_litigation(profiles, state, found)

    info = get_info_dict(state)
    _enrich_from_info(profiles, info, found)

    if any(len(p.committees) > 0 for p in profiles):
        found.append("committees")
    if any(p.is_overboarded for p in profiles) or profiles:
        found.append("overboarding")
    if any(p.tenure_years is not None for p in profiles):
        found.append("tenure")

    gov_score = compute_governance_score(profiles, compensation, weights, thresholds)
    if gov_score.total_score is not None:
        found.append("governance_score")

    report = create_report(
        extractor_name="board_governance",
        expected=EXPECTED_FIELDS, found=found,
        source_filing=source_filing,
        warnings=warnings, fallbacks_used=fallbacks,
    )
    log_report(report)
    return (profiles, gov_score), report


def _search_director_litigation(
    profiles: list[BoardForensicProfile],
    state: AnalysisState,
    found: list[str],
) -> None:
    """Search acquired litigation data for each director's name.

    Reuses the search_prior_litigation function from leadership_parsing
    which checks litigation_data, web_search_results, and blind_spot_results
    for last-name substring matches.
    """
    from do_uw.stages.extract.leadership_parsing import search_prior_litigation
    from do_uw.models.common import Confidence
    from do_uw.stages.extract.sourced import sourced_str

    total_hits = 0
    for profile in profiles:
        if profile.name is None:
            continue
        name = profile.name.value if hasattr(profile.name, "value") else str(profile.name)
        if not name:
            continue

        hits = search_prior_litigation(name, state)
        for hit in hits:
            profile.prior_litigation.append(
                sourced_str(hit, "director litigation search", Confidence.LOW)
            )
            total_hits += 1

    if total_hits > 0:
        found.append("director_litigation")
        logger.info(
            "Director litigation search: %d hits across %d directors",
            total_hits, len(profiles),
        )


def _enrich_from_info(
    profiles: list[BoardForensicProfile],
    info: dict[str, Any],
    found: list[str],
) -> None:
    """Enrich governance data from yfinance info dict."""
    officers_raw = info.get("companyOfficers", [])
    if not isinstance(officers_raw, list):
        return
    officers = cast(list[dict[str, Any]], officers_raw)
    ceo_name, chair_name = "", ""
    for officer in officers:
        title = str(officer.get("title", "")).lower()
        name = str(officer.get("name", ""))
        if "chief executive" in title or "ceo" in title:
            ceo_name = name
        if "chair" in title:
            chair_name = name
    if ceo_name and chair_name and "ceo_chair_duality" not in found:
        found.append("ceo_chair_duality")
