"""External environment assessment signal extraction.

Phase 97: Computes 5 ENVR.* signal field values from existing state data:
- regulatory_intensity_score: distinct high-intensity regulators
- geopolitical_risk_score: geographic operations vs sanctioned/high-risk
- esg_gap_score: ESG risk factor vs litigation gap
- cyber_risk_score: cyber risk severity and breach indicators
- macro_sensitivity_score: macroeconomic dimension count
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Known high-intensity regulators for D&O risk assessment
_HIGH_INTENSITY_REGULATORS: tuple[str, ...] = (
    "SEC",
    "FDA",
    "EPA",
    "DOJ",
    "FTC",
    "CFPB",
    "FERC",
    "NRC",
    "OCC",
    "FDIC",
    "FINRA",
)
_STATE_AG_PATTERN = re.compile(r"state\s+attorney|attorney\s+general", re.IGNORECASE)

# OFAC-sanctioned countries (full embargo or comprehensive sanctions)
_SANCTIONED_COUNTRIES: frozenset[str] = frozenset({
    "cuba", "iran", "north korea", "syria", "russia",
    "belarus", "venezuela", "myanmar",
})

# Elevated geopolitical risk countries
_HIGH_RISK_COUNTRIES: frozenset[str] = frozenset({
    "china", "saudi arabia", "turkey", "brazil", "india",
    "south africa", "mexico", "nigeria", "pakistan", "egypt",
})

# ESG-related litigation keywords
_ESG_LITIGATION_KEYWORDS: tuple[str, ...] = (
    "environmental", "climate", "esg", "sustainability",
    "emissions", "discrimination", "diversity", "greenwash",
    "pollution", "toxic",
)

# Breach indicator keywords
_BREACH_KEYWORDS: tuple[str, ...] = (
    "breach", "hack", "data leak", "unauthorized access",
    "cybersecurity incident", "data breach", "ransomware",
    "cyber attack", "compromised",
)

# Macro sensitivity keywords in risk factor titles/passages
_MACRO_KEYWORDS: dict[str, tuple[str, ...]] = {
    "inflation": ("inflation", "inflationary"),
    "recession": ("recession", "economic downturn", "economic slowdown"),
    "commodity": ("commodity", "raw material", "commodity price"),
    "interest_rate": ("interest rate",),
    "exchange_rate": ("exchange rate", "currency", "foreign exchange"),
    "tariff": ("tariff", "trade war", "trade restriction", "import dut"),
}


def extract_environment_signals(state: AnalysisState) -> dict[str, Any]:
    """Extract all 5 ENVR signal field values from state data.

    Returns dict with keys: regulatory_intensity_score,
    geopolitical_risk_score, esg_gap_score, cyber_risk_score,
    macro_sensitivity_score. Plus detail dicts for each.
    """
    result: dict[str, Any] = {}

    result.update(_compute_regulatory_intensity(state))
    result.update(_compute_geopolitical_risk(state))
    result.update(_compute_esg_gap(state))
    result.update(_compute_cyber_risk(state))
    result.update(_compute_macro_sensitivity(state))

    return result


def _compute_regulatory_intensity(state: AnalysisState) -> dict[str, Any]:
    """Count distinct high-intensity regulators from risk factors + LLM."""
    regulators_found: set[str] = set()

    # Scan REGULATORY risk factors for regulator mentions
    risk_factors = getattr(state.extracted, "risk_factors", None) or []
    for rf in risk_factors:
        if rf.category != "REGULATORY":
            continue
        text = (rf.title + " " + rf.source_passage).upper()
        for reg in _HIGH_INTENSITY_REGULATORS:
            if reg in text:
                regulators_found.add(reg)
        if _STATE_AG_PATTERN.search(rf.title + " " + rf.source_passage):
            regulators_found.add("STATE_AG")

    # Parse LLM regulatory_environment text
    llm_reg_env = _get_llm_field(state, "regulatory_environment")
    if llm_reg_env:
        text_upper = llm_reg_env.upper()
        for reg in _HIGH_INTENSITY_REGULATORS:
            if reg in text_upper:
                regulators_found.add(reg)
        if _STATE_AG_PATTERN.search(llm_reg_env):
            regulators_found.add("STATE_AG")

    score = len(regulators_found)
    return {
        "regulatory_intensity_score": score,
        "regulatory_details": {
            "regulators": sorted(regulators_found),
            "count": score,
        },
    }


def _compute_geopolitical_risk(state: AnalysisState) -> dict[str, Any]:
    """Evaluate geographic footprint against sanctioned/high-risk countries."""
    sanctioned_matches: list[str] = []
    high_risk_matches: list[str] = []

    footprint = getattr(state.company, "geographic_footprint", None) or []
    for sv in footprint:
        val = sv.value if hasattr(sv, "value") else sv
        if not isinstance(val, dict):
            continue
        jurisdiction = str(val.get("jurisdiction", "") or val.get("region", ""))
        jur_lower = jurisdiction.lower().strip()

        for sc in _SANCTIONED_COUNTRIES:
            if sc in jur_lower:
                sanctioned_matches.append(jurisdiction)
                break
        else:
            for hr in _HIGH_RISK_COUNTRIES:
                if hr in jur_lower:
                    high_risk_matches.append(jurisdiction)
                    break

    if sanctioned_matches:
        score = 3
    elif len(high_risk_matches) > 3:
        score = 2
    elif high_risk_matches:
        score = 1
    else:
        score = 0

    return {
        "geopolitical_risk_score": score,
        "geopolitical_details": {
            "sanctioned_countries": sanctioned_matches,
            "high_risk_countries": high_risk_matches,
            "score": score,
        },
    }


def _compute_esg_gap(state: AnalysisState) -> dict[str, Any]:
    """Compare ESG risk factors against ESG-related litigation."""
    _risk_factors = getattr(state.extracted, "risk_factors", None) or []
    esg_risk_factors = [
        rf for rf in _risk_factors
        if rf.category == "ESG"
    ]
    esg_high_severity = any(rf.severity == "HIGH" for rf in esg_risk_factors)

    # Check for ESG-related litigation
    esg_litigation_found = False
    lit = getattr(state.extracted, "litigation", None)
    if lit is not None:
        cases = getattr(lit, "securities_class_actions", None) or []
        for case in cases:
            case_name_sv = getattr(case, "case_name", None)
            case_name = ""
            if case_name_sv is not None:
                case_name = str(
                    case_name_sv.value if hasattr(case_name_sv, "value") else case_name_sv
                )
            case_lower = case_name.lower()
            if any(kw in case_lower for kw in _ESG_LITIGATION_KEYWORDS):
                esg_litigation_found = True
                break

    if esg_risk_factors and esg_litigation_found:
        score = 3
    elif esg_high_severity:
        score = 2
    elif esg_risk_factors:
        score = 1
    else:
        score = 0

    return {
        "esg_gap_score": score,
        "esg_gap_details": {
            "esg_risk_factor_count": len(esg_risk_factors),
            "esg_litigation_present": esg_litigation_found,
            "score": score,
        },
    }


def _compute_cyber_risk(state: AnalysisState) -> dict[str, Any]:
    """Evaluate CYBER risk factor presence, severity, and breach indicators."""
    _risk_factors = getattr(state.extracted, "risk_factors", None) or []
    cyber_risk_factors = [
        rf for rf in _risk_factors
        if rf.category == "CYBER"
    ]
    has_high_severity = any(rf.severity == "HIGH" for rf in cyber_risk_factors)

    # Check for breach indicators in text_signals
    breach_detected = False
    text_signals = getattr(state.extracted, "text_signals", None) or {}
    for key, val in text_signals.items():
        if val is None:
            continue
        val_lower = str(val).lower()
        if any(kw in val_lower for kw in _BREACH_KEYWORDS):
            breach_detected = True
            break
        # Also check key names that might indicate breach
        key_lower = key.lower()
        if any(kw.replace(" ", "_") in key_lower for kw in _BREACH_KEYWORDS):
            breach_detected = True
            break

    if breach_detected:
        score = 3
    elif has_high_severity:
        score = 2
    elif cyber_risk_factors:
        score = 1
    else:
        score = 0

    return {
        "cyber_risk_score": score,
        "cyber_risk_details": {
            "cyber_risk_factor_count": len(cyber_risk_factors),
            "has_high_severity": has_high_severity,
            "breach_detected": breach_detected,
            "score": score,
        },
    }


def _compute_macro_sensitivity(state: AnalysisState) -> dict[str, Any]:
    """Count macro risk dimensions from LLM fields + risk factors."""
    dimensions_found: set[str] = set()

    # LLM extraction fields
    interest_rate = _get_llm_field(state, "interest_rate_risk")
    if interest_rate:
        dimensions_found.add("interest_rate")

    currency = _get_llm_field(state, "currency_risk")
    if currency:
        dimensions_found.add("exchange_rate")

    # Scan FINANCIAL risk factors for macro terms
    _risk_factors = getattr(state.extracted, "risk_factors", None) or []
    for rf in _risk_factors:
        if rf.category != "FINANCIAL":
            continue
        text_lower = (rf.title + " " + rf.source_passage).lower()
        for dim_name, keywords in _MACRO_KEYWORDS.items():
            if dim_name in dimensions_found:
                continue
            if any(kw in text_lower for kw in keywords):
                dimensions_found.add(dim_name)

    score = len(dimensions_found)
    return {
        "macro_sensitivity_score": score,
        "macro_sensitivity_details": {
            "dimensions": sorted(dimensions_found),
            "count": score,
        },
    }


def _get_llm_field(state: AnalysisState, field_name: str) -> str | None:
    """Extract a field from the most recent LLM 10-K extraction.

    Searches state.acquired_data.llm_extractions for 10-K entries.
    Returns the raw string value or None.
    """
    llm_extractions = getattr(
        getattr(state, "acquired_data", None), "llm_extractions", None
    )
    if not llm_extractions:
        return None

    for key, data in llm_extractions.items():
        if not key.startswith("10-K:"):
            continue
        if not isinstance(data, dict):
            # Try Pydantic model
            val = getattr(data, field_name, None)
            if val is not None:
                return str(val)
            continue
        val = data.get(field_name)
        if val is not None:
            return str(val)

    return None


__all__ = ["extract_environment_signals"]
