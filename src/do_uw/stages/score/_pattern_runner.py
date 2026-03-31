"""Pattern runner orchestrator: runs all 4 engines + 6 archetype evaluations.

Orchestrates ConjunctionScan, PeerOutlier, MigrationDrift, and PrecedentMatch
engines sequentially. Evaluates 6 named archetypes from named_archetypes.yaml.
Applies tier floors from fired archetypes. Auto-expands case library when active
SCAC filing is detected.

Called as Step 16 in ScoreStage pipeline, after Step 15.5 severity.
Phase 109-03: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.patterns import PatternEngineResult
from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine
from do_uw.stages.score.migration_drift import MigrationDriftEngine
from do_uw.stages.score.pattern_engine import ArchetypeResult, EngineResult
from do_uw.stages.score.peer_outlier import PeerOutlierEngine
from do_uw.stages.score.precedent_match import PrecedentMatchEngine

__all__ = ["run_pattern_engines"]

logger = logging.getLogger(__name__)

# Path to named archetypes YAML
_ARCHETYPES_PATH = (
    Path(__file__).parent.parent.parent
    / "brain"
    / "framework"
    / "named_archetypes.yaml"
)

# Default auto-cases output directory
_AUTO_CASES_DIR = (
    Path(__file__).parent.parent.parent
    / "brain"
    / "framework"
    / "auto_cases"
)


def run_pattern_engines(
    state: Any,
    signal_results: dict[str, Any],
    hae_result: Any | None = None,
) -> PatternEngineResult | None:
    """Run all 4 pattern engines and 6 archetype evaluations.

    Each engine is run independently. Individual engine failures are caught
    and logged as warnings; remaining engines continue. Returns a
    PatternEngineResult with all results, even if all engines fail.

    Args:
        state: AnalysisState with company, extracted, analysis data.
        signal_results: Signal evaluation results dict.
        hae_result: ScoringLensResult from H/A/E scoring (for tier floors).

    Returns:
        PatternEngineResult, or None on catastrophic failure.
    """
    engine_results: list[EngineResult] = []

    # Instantiate and run all 4 engines
    engines: list[tuple[str, str, Any]] = [
        ("conjunction_scan", "Conjunction Scan", ConjunctionScanEngine),
        ("peer_outlier", "Peer Outlier", PeerOutlierEngine),
        ("migration_drift", "Migration Drift", MigrationDriftEngine),
        ("precedent_match", "Precedent Match", PrecedentMatchEngine),
    ]

    for engine_id, engine_name, engine_cls in engines:
        try:
            engine = engine_cls()
            result = engine.evaluate(signal_results, state=state)
            engine_results.append(result)
        except Exception as exc:
            logger.warning(
                "Pattern engine %s failed: %s",
                engine_id,
                str(exc),
                exc_info=True,
            )
            engine_results.append(
                EngineResult(
                    engine_id=engine_id,
                    engine_name=engine_name,
                    fired=False,
                    confidence=0.0,
                    headline=f"Engine error: {str(exc)[:100]}",
                )
            )

    # Evaluate 6 named archetypes
    archetype_results = _evaluate_archetypes(signal_results)

    # Auto-expand case library if active SCAC filing detected
    try:
        _auto_expand_case_library(state, signal_results)
    except Exception:
        logger.warning(
            "Auto-expansion of case library failed; continuing",
            exc_info=True,
        )

    return PatternEngineResult(
        engine_results=engine_results,
        archetype_results=archetype_results,
        computed_at=datetime.now(timezone.utc),
    )


def _evaluate_archetypes(
    signal_results: dict[str, Any],
) -> list[ArchetypeResult]:
    """Evaluate all 6 named archetypes against signal results.

    Loads archetypes from named_archetypes.yaml. For each archetype,
    checks how many required_signals have status RED or YELLOW.
    Skips future_signal.* IDs (AI Mirage placeholders).

    Returns list of 6 ArchetypeResult (one per archetype).
    """
    archetypes_data = _load_archetypes()
    results: list[ArchetypeResult] = []

    for arch in archetypes_data:
        arch_id = arch.get("id", "unknown")
        arch_name = arch.get("name", "Unknown Archetype")
        required_signals: list[str] = arch.get("required_signals", [])
        minimum_matches: int = arch.get("minimum_matches", 3)
        recommendation_floor: str | None = arch.get("recommendation_floor")
        historical_cases: list[str] = arch.get("historical_cases", [])

        # Filter out future_signal.* IDs
        real_signals = [
            s for s in required_signals if not s.startswith("future_signal.")
        ]

        # Count matched signals (RED or YELLOW)
        matched_ids: list[str] = []
        for sig_id in real_signals:
            sig_data = signal_results.get(sig_id)
            if isinstance(sig_data, dict):
                status = sig_data.get("status", "")
                if status in ("RED", "YELLOW"):
                    matched_ids.append(sig_id)

        matched_count = len(matched_ids)
        required_count = len(real_signals)

        fired = matched_count >= minimum_matches
        confidence = (
            matched_count / required_count if required_count > 0 else 0.0
        )

        results.append(
            ArchetypeResult(
                archetype_id=arch_id,
                archetype_name=arch_name,
                fired=fired,
                signals_matched=matched_count,
                signals_required=required_count,
                matched_signal_ids=matched_ids,
                recommendation_floor=recommendation_floor if fired else None,
                confidence=round(confidence, 4),
                historical_cases=historical_cases,
            )
        )

    # Validate signal IDs at startup (log warnings for unresolvable)
    _validate_archetype_signal_ids(archetypes_data)

    return results


def _load_archetypes() -> list[dict[str, Any]]:
    """Load named archetypes from YAML."""
    if not _ARCHETYPES_PATH.exists():
        logger.warning("Named archetypes YAML not found: %s", _ARCHETYPES_PATH)
        return []

    with open(_ARCHETYPES_PATH) as f:
        data = yaml.safe_load(f)

    if not data or "archetypes" not in data:
        return []

    return data["archetypes"]


def _validate_archetype_signal_ids(
    archetypes_data: list[dict[str, Any]],
) -> None:
    """Log warnings for unresolvable signal IDs in archetypes.

    Checks that each required_signal (excluding future_signal.*) exists
    in the brain signal corpus. Best-effort; does not block execution.
    """
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        signals_data = load_signals()
        known_ids: set[str] = set()
        for sig in signals_data.get("signals", []):
            if isinstance(sig, dict):
                known_ids.add(sig.get("id", ""))

        for arch in archetypes_data:
            arch_id = arch.get("id", "unknown")
            for sig_id in arch.get("required_signals", []):
                if sig_id.startswith("future_signal."):
                    continue
                if sig_id not in known_ids:
                    logger.debug(
                        "Archetype %s: signal %s not found in brain corpus",
                        arch_id,
                        sig_id,
                    )
    except Exception:
        pass  # Non-fatal validation


def _apply_tier_floors(
    hae_result: Any,
    archetype_results: list[ArchetypeResult],
) -> Any:
    """Apply archetype recommendation floors to H/A/E tier.

    For each fired archetype with a recommendation_floor, compares
    HAETier(floor) against hae_result.tier. If floor > current tier,
    tier is raised. Never lowers tier.

    Args:
        hae_result: ScoringLensResult from H/A/E scoring.
        archetype_results: Archetype evaluation results.

    Returns:
        Updated ScoringLensResult (or original if no change).
    """
    from do_uw.stages.score.scoring_lens import HAETier

    current = hae_result
    for arch in archetype_results:
        if not arch.fired or not arch.recommendation_floor:
            continue
        try:
            floor_tier = HAETier(arch.recommendation_floor)
            if floor_tier > current.tier:
                current = current.model_copy(
                    update={
                        "tier": floor_tier,
                        "tier_source": f"pattern_floor:{arch.archetype_id}",
                    }
                )
        except ValueError:
            logger.warning(
                "Invalid tier string in archetype %s floor: %s",
                arch.archetype_id,
                arch.recommendation_floor,
            )

    return current


def _auto_expand_case_library(
    state: Any,
    signal_results: dict[str, Any],
    *,
    auto_cases_dir: Path | None = None,
) -> None:
    """Auto-create case library entry when active SCAC filing detected.

    Checks state.extracted.litigation for active securities class actions.
    If found, builds a signal fingerprint from current signal_results
    and writes a YAML entry to brain/framework/auto_cases/.

    Best-effort operation: failure is logged and ignored.

    Args:
        state: AnalysisState with extracted litigation data.
        signal_results: Current signal results for fingerprinting.
        auto_cases_dir: Override directory for auto-cases (for testing).
    """
    # Check for active SCAC filing
    if not _has_active_scac(state):
        return

    # Build signal fingerprint
    fingerprint: dict[str, str] = {}
    for sig_id, sig_data in signal_results.items():
        if isinstance(sig_data, dict):
            status = sig_data.get("status", "UNKNOWN")
            if status in ("RED", "YELLOW"):
                fingerprint[sig_id] = status
            else:
                fingerprint[sig_id] = "CLEAR"

    if not fingerprint:
        return

    # Extract company info
    ticker = "UNKNOWN"
    company_name = "Unknown Company"
    try:
        if state.company and state.company.identity:
            ticker = state.company.identity.ticker or "UNKNOWN"
            if state.company.identity.legal_name:
                company_name = (
                    state.company.identity.legal_name.value or company_name
                )
    except Exception:
        pass

    # Build case entry
    case_entry = {
        "case_id": f"{ticker}-AUTO-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "company_name": company_name,
        "ticker": ticker,
        "filing_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "claim_type": "SCA",
        "market_cap_at_filing": 0.0,  # Unknown for auto-added
        "sector": "Unknown",
        "signal_profile": fingerprint,
        "outcome": {"status": "ongoing"},
        "signal_profile_confidence": "LOW",
        "notes": (
            "Profile captured post-filing, not at time of filing. "
            "Auto-added by pipeline."
        ),
    }

    # Write to auto_cases directory
    output_dir = auto_cases_dir or _AUTO_CASES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{ticker.lower()}_auto.yaml"

    with open(output_file, "w") as f:
        yaml.safe_dump(case_entry, f, default_flow_style=False, sort_keys=False)

    logger.info(
        "Auto-expanded case library: %s (%d signals profiled)",
        case_entry["case_id"],
        len(fingerprint),
    )


def _has_active_scac(state: Any) -> bool:
    """Check if state has an active SCAC filing."""
    try:
        litigation = state.extracted.litigation
        if litigation is None:
            return False
        scas = getattr(litigation, "securities_class_actions", [])
        for case in scas:
            status = getattr(case, "status", "")
            if isinstance(status, str) and status.lower() not in (
                "dismissed",
                "resolved",
                "settled",
            ):
                return True
    except (AttributeError, TypeError):
        pass
    return False
