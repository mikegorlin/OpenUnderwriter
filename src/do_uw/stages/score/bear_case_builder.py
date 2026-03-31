"""Evidence-gated bear case construction for Phase 27.

Constructs litigation narratives ("how this company gets sued") from
actual analysis findings. Bear cases are ONLY built when an allegation
theory has MODERATE or HIGH exposure in the AllegationMapping -- clean
companies get zero bear cases.

Each bear case includes:
- Committee summary (2-3 structured sentences)
- Evidence chain (ordered EvidenceItem list, highest severity first)
- Defense assessment (ONLY when company-specific defenses exist)

Public API: build_bear_cases(allegation_mapping, signal_results, ...)
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.peril import (
    BearCase,
    EvidenceItem,
    PerilProbabilityBand,
    PerilSeverityBand,
)
from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

# Max evidence items per bear case
_MAX_EVIDENCE_ITEMS = 10

# Severity ordering for sorting (highest first)
_SEVERITY_ORDER: dict[str, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MODERATE": 2,
    "LOW": 3,
}

# Theory-to-factor mapping (mirrors allegation_mapping._THEORY_FACTORS)
_THEORY_FACTORS: dict[str, list[str]] = {
    "A_DISCLOSURE": ["F1", "F3", "F5"],
    "B_GUIDANCE": ["F2", "F5"],
    "C_PRODUCT_OPS": ["F7", "F8"],
    "D_GOVERNANCE": ["F9", "F10"],
    "E_MA": ["F4"],
}

# Theory-to-plaintiff-type mapping
_THEORY_PLAINTIFF: dict[str, str] = {
    "A_DISCLOSURE": "SHAREHOLDERS",
    "B_GUIDANCE": "SHAREHOLDERS",
    "C_PRODUCT_OPS": "REGULATORS",
    "D_GOVERNANCE": "SHAREHOLDERS",
    "E_MA": "SHAREHOLDERS",
}

# Human-readable theory labels
_THEORY_LABELS: dict[str, str] = {
    "A_DISCLOSURE": "securities disclosure fraud",
    "B_GUIDANCE": "guidance manipulation",
    "C_PRODUCT_OPS": "product/operational failure",
    "D_GOVERNANCE": "governance breach",
    "E_MA": "M&A-related",
}

# Exposure level gate: only MODERATE and HIGH produce bear cases
_GATE_LEVELS = frozenset({"MODERATE", "HIGH"})


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def build_bear_cases(
    allegation_mapping: dict[str, Any],
    signal_results: dict[str, Any],
    peril_assessments: list[dict[str, Any]],
    extracted: ExtractedData | None,
    company_name: str,
) -> list[BearCase]:
    """Build evidence-gated bear cases from allegation mapping.

    Args:
        allegation_mapping: AllegationMapping.model_dump() dict.
        signal_results: Dict of signal_id -> check result dict.
        peril_assessments: List of PlaintiffAssessment dicts.
        extracted: Extracted data for defense assessment.
        company_name: Company display name.

    Returns:
        List of BearCase objects. Empty for clean companies.
    """
    theories = allegation_mapping.get("theories", [])
    if not theories:
        return []

    bear_cases: list[BearCase] = []
    for theory_dict in theories:
        exposure_level = theory_dict.get("exposure_level", "LOW")
        if exposure_level not in _GATE_LEVELS:
            continue

        theory_value = theory_dict.get("theory", "")
        bear_case = _construct_bear_case(
            theory_dict,
            signal_results,
            peril_assessments,
            extracted,
            company_name,
        )
        if bear_case is not None:
            bear_cases.append(bear_case)
            logger.info(
                "Bear case constructed: %s (%s exposure)",
                theory_value,
                exposure_level,
            )

    logger.info(
        "Bear case construction: %d cases from %d theories",
        len(bear_cases),
        len(theories),
    )
    return bear_cases


# -----------------------------------------------------------------------
# Construction helpers
# -----------------------------------------------------------------------


def _construct_bear_case(
    theory_dict: dict[str, Any],
    signal_results: dict[str, Any],
    peril_assessments: list[dict[str, Any]],
    extracted: ExtractedData | None,
    company_name: str,
) -> BearCase | None:
    """Construct a single bear case for a theory with sufficient exposure."""
    theory_value = theory_dict.get("theory", "")
    exposure_level = theory_dict.get("exposure_level", "LOW")
    factor_sources = theory_dict.get("factor_sources", [])

    # Get plaintiff type
    plaintiff_type = _THEORY_PLAINTIFF.get(theory_value, "SHAREHOLDERS")

    # Build evidence chain from triggered checks
    evidence_chain = _get_evidence_for_theory(
        theory_value, signal_results, factor_sources,
    )

    # Determine probability and severity bands from peril assessments
    probability_band = _get_band_for_plaintiff(
        plaintiff_type, peril_assessments, "probability_band",
        default=PerilProbabilityBand.MODERATE,
    )
    severity_band = _get_band_for_plaintiff(
        plaintiff_type, peril_assessments, "severity_band",
        default=PerilSeverityBand.MODERATE,
    )

    # Build committee summary
    committee_summary = _build_committee_summary(
        theory_value, evidence_chain, probability_band, severity_band,
        company_name,
    )

    # Assess defenses
    defense = _assess_defense(theory_value, extracted)

    return BearCase(
        theory=theory_value,
        plaintiff_type=plaintiff_type,
        committee_summary=committee_summary,
        evidence_chain=evidence_chain,
        severity_estimate=severity_band,
        defense_assessment=defense,
        probability_band=probability_band,
        supporting_signal_count=len(evidence_chain),
    )


def _get_evidence_for_theory(
    theory_value: str,
    signal_results: dict[str, Any],
    factor_sources: list[str],
) -> list[EvidenceItem]:
    """Filter check results to evidence supporting this theory.

    Includes:
    - Checks whose factors overlap with the theory's factor_sources
    - Checks whose plaintiff_lenses overlap with the theory's primary lens

    Returns EvidenceItem list sorted by severity (highest first), max 10.
    """
    primary_lens = _THEORY_PLAINTIFF.get(theory_value, "SHAREHOLDERS")
    theory_factors = set(
        factor_sources
        or _THEORY_FACTORS.get(theory_value, [])
    )

    evidence: list[EvidenceItem] = []

    for signal_id, signal_data in signal_results.items():
        if not isinstance(signal_data, dict):
            continue

        status = signal_data.get("status", "")
        if status != "TRIGGERED":
            continue

        # Match by factor overlap OR plaintiff lens overlap
        check_factors = set(signal_data.get("factors", []))
        check_lenses = set(signal_data.get("plaintiff_lenses", []))
        factor_match = bool(check_factors & theory_factors)
        lens_match = primary_lens in check_lenses

        if not factor_match and not lens_match:
            continue

        # Determine severity from threshold_level or default
        severity = _infer_severity(signal_data)

        # Use signal_name for human-readable description, NOT raw evidence
        # which contains internal threshold text like "Value 5.0 exceeds red threshold 3.0"
        desc = signal_data.get("signal_name", signal_id)
        evidence.append(EvidenceItem(
            signal_id=signal_id,
            description=desc,
            source=signal_data.get("source", "analysis"),
            severity=severity,
            data_status=signal_data.get("data_status", "EVALUATED"),
        ))

    # Sort by severity (highest first)
    evidence.sort(key=lambda e: _SEVERITY_ORDER.get(e.severity, 99))

    # Cap at max items
    return evidence[:_MAX_EVIDENCE_ITEMS]


def _infer_severity(signal_data: dict[str, Any]) -> str:
    """Infer severity from check data fields."""
    threshold = signal_data.get("threshold_level", "")
    if threshold == "red":
        return "CRITICAL"
    if threshold == "yellow":
        return "HIGH"
    # Fall back to category-based inference
    category = signal_data.get("category", "")
    if category == "DECISION_DRIVING":
        return "MODERATE"
    return "LOW"


def _get_band_for_plaintiff(
    plaintiff_type: str,
    peril_assessments: list[dict[str, Any]],
    band_field: str,
    default: str,
) -> str:
    """Extract probability or severity band for a plaintiff type from assessments."""
    for assessment in peril_assessments:
        if assessment.get("plaintiff_type") == plaintiff_type:
            return assessment.get(band_field, default)
    return default


# -----------------------------------------------------------------------
# Committee summary
# -----------------------------------------------------------------------


def _build_committee_summary(
    theory_value: str,
    evidence_chain: list[EvidenceItem],
    probability_band: str,
    severity_band: str,
    company_name: str,
) -> str:
    """Build 2-3 sentence structured summary for underwriting committee.

    Sentence 1: "[Company] faces [probability_band] exposure to [theory] claims."
    Sentence 2: "Key evidence: [top 2 findings from evidence chain]."
    Sentence 3 (if severity >= MODERATE): "[Severity context]."
    """
    theory_label = _theory_label(theory_value)
    band_display = probability_band.replace("_", " ").lower()

    # Sentence 1
    s1 = f"{company_name} faces {band_display} exposure to {theory_label} claims."

    # Sentence 2: use signal names with severity context
    if evidence_chain:
        top_findings: list[str] = []
        for e in evidence_chain[:2]:
            sev_label = e.severity.lower() if e.severity else "flagged"
            top_findings.append(f"{e.description} ({sev_label})")
        s2 = f"Key risk indicators: {'; '.join(top_findings)}."
    else:
        s2 = "No specific triggered checks currently support this theory."

    # Sentence 3 (severity context, only if MODERATE or above)
    severity_moderate_plus = severity_band in (
        PerilSeverityBand.MODERATE,
        PerilSeverityBand.SIGNIFICANT,
        PerilSeverityBand.SEVERE,
    )
    if severity_moderate_plus:
        severity_display = severity_band.lower()
        s3 = f" Estimated severity is {severity_display}, warranting detailed underwriter review."
        return f"{s1} {s2}{s3}"

    return f"{s1} {s2}"


def _theory_label(theory_value: str) -> str:
    """Map AllegationTheory value to human-readable label."""
    return _THEORY_LABELS.get(theory_value, theory_value.lower().replace("_", " "))


# -----------------------------------------------------------------------
# Defense assessment
# -----------------------------------------------------------------------


def _assess_defense(
    theory_value: str,
    extracted: ExtractedData | None,
) -> str | None:
    """Assess company-specific defenses for a theory.

    Returns defense string ONLY when company-specific provisions exist.
    Returns None for generic defenses or when no defense data available.
    """
    if extracted is None:
        return None

    defenses: list[str] = []

    # Check governance data for charter/bylaw provisions
    gov = extracted.governance
    if gov is not None:
        # Forum selection clause (from board profile or governance score)
        board = gov.board
        if board is not None:
            # Check for classified board (staggered) as anti-takeover defense
            if (
                theory_value == "E_MA"
                and board.ceo_chair_duality is not None
                and board.ceo_chair_duality.value is True
            ):
                defenses.append(
                    "Defense: CEO-Chair duality may complicate "
                    "governance breach claims but strengthens unified decision-making"
                )

        # Check governance score for specific provisions
        gs = gov.governance_score
        if gs is not None and gs.total_score is not None:
            score = gs.total_score.value
            if score >= 80 and theory_value == "D_GOVERNANCE":
                defenses.append(
                    f"Defense: Strong governance score ({score}/100) "
                    f"— governance breach claims face higher evidentiary bar"
                )

    # Section 11 defense: check market data for active offering windows
    if theory_value == "A_DISCLOSURE":
        mkt = extracted.market
        if (
            mkt is not None
            and mkt.capital_markets.active_section_11_windows == 0
        ):
            # No active windows means Section 11 liability period expired
            defenses.append(
                "Defense: No active Section 11 windows "
                "— statute of limitations expired for offering claims"
            )

    # Only return if company-specific defenses found
    if defenses:
        return "; ".join(defenses)
    return None


__all__ = ["build_bear_cases"]
