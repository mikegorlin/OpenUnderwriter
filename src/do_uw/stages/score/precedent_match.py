"""Precedent Match pattern engine.

Computes weighted Jaccard similarity between the current company's
signal profile and a library of 20 canonical D&O cases. Finds the
most similar historical cases to provide precedent-based risk context.

CRF-related signals receive 3x weighting in similarity computation.
Dismissed cases are included with 0.5x outcome severity weight.
HIGH/MEDIUM/LOW confidence cases get 1.0/0.8/0.6 profile weighting.

Implements PatternEngine Protocol.
Phase 109-02: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.patterns import CaseLibraryEntry
from do_uw.stages.score.pattern_engine import EngineResult

# ---------------------------------------------------------------
# CRF signal IDs (from scoring_model_design.yaml CRF veto catalog)
# ---------------------------------------------------------------
# These signals get 3x weight in Jaccard similarity computation
# because matching on critical risk factors is more meaningful.

_CRF_SIGNAL_IDS: frozenset[str] = frozenset(
    {
        # CRF-FRAUD signals
        "LIT.REG.sec_active",
        "LIT.REG.sec_investigation",
        "LIT.REG.wells_notice",
        # CRF-RESTATEMENT signals
        "FIN.ACCT.restatement",
        "FIN.ACCT.restatement_magnitude",
        # CRF-INSOLVENCY signals
        "FWRD.WARN.zone_of_insolvency",
        "FIN.LIQ.cash_burn",
        "FIN.LIQ.position",
        # CRF-DOJ signals
        "LIT.REG.doj_investigation",
        # CRF-MATERIAL-WEAKNESS signals
        "FIN.ACCT.material_weakness",
        "FIN.ACCT.internal_controls",
        "GOV.EFFECT.material_weakness",
    }
)

# ---------------------------------------------------------------
# Case library path and loader
# ---------------------------------------------------------------

_CASE_LIBRARY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "framework"
    / "case_library.yaml"
)


@functools.lru_cache(maxsize=1)
def _load_case_library_cached() -> tuple[CaseLibraryEntry, ...]:
    """Load case library from YAML. Module-level lazy singleton."""
    if not _CASE_LIBRARY_PATH.exists():
        return ()
    raw = yaml.safe_load(_CASE_LIBRARY_PATH.read_text())
    entries: list[CaseLibraryEntry] = []
    for entry_data in raw.get("cases", []):
        entries.append(CaseLibraryEntry.model_validate(entry_data))
    return tuple(entries)


# ---------------------------------------------------------------
# Weighted Jaccard similarity
# ---------------------------------------------------------------


def _weighted_jaccard(
    a: dict[str, bool],
    b: dict[str, bool],
    weights: dict[str, float],
) -> float:
    """Compute weighted Jaccard similarity between two binary fingerprints.

    weighted_jaccard = sum(w_i * min(a_i, b_i)) / sum(w_i * max(a_i, b_i))
    where a_i, b_i in {0, 1} and w_i is the signal importance weight.

    Guards against division by zero (returns 0.0).
    """
    all_keys = set(a.keys()) | set(b.keys())

    numerator = 0.0
    denominator = 0.0

    for key in all_keys:
        a_val = 1.0 if a.get(key, False) else 0.0
        b_val = 1.0 if b.get(key, False) else 0.0
        w = weights.get(key, 1.0)

        numerator += w * min(a_val, b_val)
        denominator += w * max(a_val, b_val)

    if denominator == 0.0:
        return 0.0

    return numerator / denominator


# ---------------------------------------------------------------
# Confidence and outcome weighting
# ---------------------------------------------------------------

_CONFIDENCE_WEIGHT: dict[str, float] = {
    "HIGH": 1.0,
    "MEDIUM": 0.8,
    "LOW": 0.6,
}

_OUTCOME_SEVERITY: dict[str, float] = {
    "settlement": 1.0,
    "judgment": 1.5,
    "ongoing": 1.0,
    "stayed": 0.8,
    "voluntary_dismissal": 0.5,
    "dismissal": 0.5,  # 0.5x per user decision
}


def _compute_outcome_severity_weight(outcome: dict[str, Any]) -> float:
    """Compute outcome severity weight for a case.

    Large settlements (>$50M) get 1.5x, medium ($5-50M) 1.0x,
    small (<$5M) 0.8x. Dismissals get 0.5x.
    """
    outcome_type = outcome.get("type", "ongoing")
    base = _OUTCOME_SEVERITY.get(outcome_type, 1.0)

    # Adjust for settlement size
    settlement = outcome.get("settlement_amount")
    if outcome_type == "settlement" and settlement is not None:
        if settlement > 50_000_000:
            base = 1.5
        elif settlement < 5_000_000:
            base = 0.8
        # else 1.0 (medium settlement)

    return base


# ---------------------------------------------------------------
# PrecedentMatchEngine
# ---------------------------------------------------------------


class PrecedentMatchEngine:
    """Computes weighted Jaccard similarity against D&O case library.

    Finds historical cases with similar signal profiles to the current
    company, providing precedent-based risk context for underwriters.

    All thresholds are configurable via constructor parameters.
    """

    def __init__(
        self,
        *,
        notable_threshold: float = 0.30,
        strong_threshold: float = 0.50,
        very_strong_threshold: float = 0.70,
        crf_weight: float = 3.0,
        top_k: int = 3,
    ) -> None:
        self._notable_threshold = notable_threshold
        self._strong_threshold = strong_threshold
        self._very_strong_threshold = very_strong_threshold
        self._crf_weight = crf_weight
        self._top_k = top_k

    @property
    def engine_id(self) -> str:
        return "precedent_match"

    @property
    def engine_name(self) -> str:
        return "Precedent Match"

    def _load_case_library(self) -> tuple[CaseLibraryEntry, ...]:
        """Load case library (cached module-level singleton)."""
        return _load_case_library_cached()

    def _build_company_fingerprint(
        self, signal_results: dict[str, Any]
    ) -> dict[str, bool]:
        """Convert signal evaluation results to binary fingerprint.

        Signal is "fired" if status in {RED, YELLOW}.
        CLEAR and SKIPPED are False.
        """
        fingerprint: dict[str, bool] = {}
        for signal_id, result in signal_results.items():
            if isinstance(result, dict):
                status = result.get("status", "")
            else:
                status = getattr(result, "status", "")
            fingerprint[signal_id] = status in ("RED", "YELLOW")
        return fingerprint

    def _build_case_fingerprint(
        self, case: CaseLibraryEntry
    ) -> dict[str, bool]:
        """Convert case signal profile to binary fingerprint.

        RED and YELLOW are True. CLEAR and UNKNOWN are False.
        """
        return {
            sig_id: status in ("RED", "YELLOW")
            for sig_id, status in case.signal_profile.items()
        }

    def _compute_signal_weights(
        self, all_signals: set[str]
    ) -> dict[str, float]:
        """Compute importance weights for signals.

        CRF-related signals get crf_weight (default 3.0x).
        All others get 1.0x.
        """
        return {
            sig_id: self._crf_weight if sig_id in _CRF_SIGNAL_IDS else 1.0
            for sig_id in all_signals
        }

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        state: Any | None = None,
    ) -> EngineResult:
        """Evaluate precedent match against case library.

        Step 1: Load case library. If empty, return NOT_FIRED.
        Step 2: Build company fingerprint from signal_results.
        Step 3: Compute weighted Jaccard for each case.
        Step 4: Apply confidence weighting.
        Step 5: Sort and return top matches.
        """
        base_result = EngineResult(
            engine_id=self.engine_id,
            engine_name=self.engine_name,
        )

        # Step 1: Load case library
        cases = self._load_case_library()
        if not cases:
            return base_result.model_copy(
                update={"headline": "No case library available."}
            )

        # Step 2: Build company fingerprint
        company_fp = self._build_company_fingerprint(signal_results)
        if not any(company_fp.values()):
            return base_result.model_copy(
                update={
                    "headline": "No fired signals to match against case library.",
                    "metadata": {"fired_signal_count": 0},
                }
            )

        # Step 3 & 4: Compute similarities for each case
        matches: list[dict[str, Any]] = []

        for case in cases:
            case_fp = self._build_case_fingerprint(case)

            # Union of all signals for weight computation
            all_signals = set(company_fp.keys()) | set(case_fp.keys())
            weights = self._compute_signal_weights(all_signals)

            # Compute weighted Jaccard
            raw_similarity = _weighted_jaccard(company_fp, case_fp, weights)

            # Apply confidence weighting
            conf_weight = _CONFIDENCE_WEIGHT.get(
                case.signal_profile_confidence, 0.6
            )
            adjusted_similarity = raw_similarity * conf_weight

            # Compute outcome severity weight
            outcome_severity = _compute_outcome_severity_weight(case.outcome)

            # Count overlapping fired signals
            overlapping = [
                sig_id
                for sig_id in all_signals
                if company_fp.get(sig_id, False) and case_fp.get(sig_id, False)
            ]

            matches.append(
                {
                    "case_id": case.case_id,
                    "company_name": case.company_name,
                    "similarity": round(adjusted_similarity, 4),
                    "raw_similarity": round(raw_similarity, 4),
                    "outcome_type": case.outcome.get("type", "unknown"),
                    "outcome_severity_weight": outcome_severity,
                    "settlement_amount": case.outcome.get("settlement_amount"),
                    "claim_type": case.claim_type,
                    "overlapping_signals": len(overlapping),
                    "case_signals": len(case.signal_profile),
                    "confidence_tier": case.signal_profile_confidence,
                    "notes": case.notes[:100] + "..." if len(case.notes) > 100 else case.notes,
                }
            )

        # Step 5: Sort by adjusted similarity descending
        matches.sort(key=lambda m: m["similarity"], reverse=True)

        # Take top K
        top_matches = matches[: self._top_k]

        # Determine if engine fires
        best_similarity = top_matches[0]["similarity"] if top_matches else 0.0
        fired = best_similarity >= self._notable_threshold

        # Build headline
        if fired:
            best = top_matches[0]
            match_strength = "notable"
            if best_similarity >= self._very_strong_threshold:
                match_strength = "very strong"
            elif best_similarity >= self._strong_threshold:
                match_strength = "strong"
            headline = (
                f"Precedent match: {match_strength} similarity to "
                f"{best['company_name']} ({best['case_id']}) at "
                f"{best_similarity:.0%}."
            )
        else:
            headline = (
                f"No notable precedent matches (best: {best_similarity:.0%}, "
                f"threshold: {self._notable_threshold:.0%})."
            )

        return EngineResult(
            engine_id=self.engine_id,
            engine_name=self.engine_name,
            fired=fired,
            confidence=round(min(best_similarity, 1.0), 3),
            headline=headline,
            findings=top_matches,
            metadata={
                "total_cases_compared": len(cases),
                "notable_threshold": self._notable_threshold,
                "strong_threshold": self._strong_threshold,
                "crf_weight": self._crf_weight,
                "company_fired_signals": sum(
                    1 for v in company_fp.values() if v
                ),
            },
        )
