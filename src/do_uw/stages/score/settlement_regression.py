"""Settlement regression model using published coefficients (Phase 108).

Predicts settlement amount from a 12-feature log-linear regression
model using published Cornerstone/NERA coefficient estimates. No model
fitting required -- the published research fitted on thousands of cases.

log10(settlement) = intercept + sum(coefficient_i * feature_i)

Features include market cap, stock decline, allegation type, jurisdiction,
lead plaintiff type, case characteristics, and sector. Each feature has
a published coefficient estimate from severity_model_design.yaml.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "build_feature_vector",
    "infer_primary_allegation_type",
    "predict_all_allegation_types",
    "predict_settlement_regression",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Coefficient loading
# ---------------------------------------------------------------

_DESIGN_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "framework"
    / "severity_model_design.yaml"
)
_coefficients_cache: dict[str, float] | None = None

# Published intercept derived from Cornerstone baseline:
# Median SCA settlement ~$5M for typical case features.
# Typical case: $1B market_cap (log10=9), 20% decline, guidance_miss,
# 365-day class period (log10=2.56), 2 defendants.
# Contributions: 9*0.40 + 0.20*0.30 + 2.56*0.15 + 2*0.05 = 4.14
# Target: log10(5_000_000) = 6.70 -> intercept = 6.70 - 4.14 = 2.56
_DEFAULT_INTERCEPT = 2.56


def _load_regression_coefficients() -> dict[str, float]:
    """Load regression coefficient estimates from design YAML.

    Returns dict mapping feature_name -> coefficient estimate.
    Cached as module singleton.
    """
    global _coefficients_cache
    if _coefficients_cache is not None:
        return _coefficients_cache

    with open(_DESIGN_YAML_PATH) as f:
        design = yaml.safe_load(f)

    features_list = design.get("settlement_regression", {}).get("features", [])
    coefficients: dict[str, float] = {}

    for feature in features_list:
        name = feature.get("name", "")
        estimate = feature.get("coefficient_estimate", 0)

        # Handle string estimates like "+0.25" or "varies by category"
        if isinstance(estimate, str):
            try:
                estimate = float(estimate.replace("+", ""))
            except ValueError:
                # "varies by category" or similar -- skip, handled by categoricals
                continue
        coefficients[name] = float(estimate)

    _coefficients_cache = coefficients
    return _coefficients_cache


# ---------------------------------------------------------------
# Feature names for categorical encoding
# ---------------------------------------------------------------

_ALLEGATION_TYPES = [
    "financial_restatement",
    "insider_trading",
    "regulatory_action",
    "offering_securities",
    "merger_objection",
]
# baseline: guidance_miss (encoded as all zeros)

_ALLEGATION_COEFFICIENTS: dict[str, float] = {
    "financial_restatement": 0.30,
    "insider_trading": 0.20,
    "regulatory_action": 0.15,
    "offering_securities": 0.10,
    "merger_objection": -0.30,
}

_SECTOR_COEFFICIENTS: dict[str, float] = {
    "technology": 0.10,
    "healthcare": 0.10,
    "utilities": -0.05,
    "consumer_staples": -0.05,
}

# Signal IDs that indicate specific allegation types
_RESTATEMENT_SIGNALS = frozenset({
    "FIN.ACCT.restatement",
    "FIN.ACCT.restatement_magnitude",
    "FIN.ACCT.restatement_pattern",
    "FIN.ACCT.earnings_manipulation",
})
_INSIDER_SIGNALS = frozenset({
    "GOV.INSIDER.cluster_sales",
    "GOV.INSIDER.unusual_timing",
    "EXEC.INSIDER.cluster_selling",
})
_REGULATORY_SIGNALS = frozenset({
    "LIT.REG.sec_active",
    "LIT.REG.sec_investigation",
    "LIT.REG.doj_investigation",
    "LIT.REG.wells_notice",
})
_MERGER_SIGNALS = frozenset({
    "LIT.SCA.merger_obj",
    "FWRD.EVENT.ma_closing",
})


# ---------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------


def predict_settlement_regression(features: dict[str, float]) -> float:
    """Predict settlement amount from feature vector.

    Uses log-linear model: log10(settlement) = intercept + sum(coeff * feature).

    Args:
        features: Dict of feature_name -> value. Continuous features should
            be pre-transformed (log10 for market_cap, class_period_length).
            Categorical features should be 0/1 encoded.

    Returns:
        Predicted settlement amount in USD.
    """
    coefficients = _load_regression_coefficients()

    log_settlement = _DEFAULT_INTERCEPT

    # Market cap (strongest predictor)
    log_settlement += coefficients.get("market_cap_at_filing", 0.40) * features.get(
        "market_cap_at_filing", 0.0
    )

    # Stock decline
    log_settlement += coefficients.get("max_stock_decline_pct", 0.30) * features.get(
        "max_stock_decline_pct", 0.0
    )

    # Allegation type categoricals
    for atype in _ALLEGATION_TYPES:
        feat_key = f"allegation_type_{atype}"
        if features.get(feat_key, 0) > 0:
            log_settlement += _ALLEGATION_COEFFICIENTS.get(atype, 0.0)

    # Jurisdiction
    if features.get("jurisdiction_sdny", 0) > 0 or features.get("jurisdiction_ndcal", 0) > 0:
        log_settlement += 0.10

    # Lead plaintiff type
    if features.get("lead_plaintiff_institutional", 0) > 0:
        log_settlement += coefficients.get("lead_plaintiff_type", 0.15)

    # Class period length (log-transformed)
    log_settlement += coefficients.get("class_period_length_days", 0.15) * features.get(
        "class_period_length_days", 0.0
    )

    # Binary features
    if features.get("restatement_present", 0) > 0:
        log_settlement += float(coefficients.get("restatement_present", 0.25))

    if features.get("sec_investigation_present", 0) > 0:
        log_settlement += float(coefficients.get("sec_investigation_present", 0.20))

    # Named defendants
    log_settlement += coefficients.get("number_of_named_defendants", 0.05) * features.get(
        "number_of_named_defendants", 0.0
    )

    # Sector
    for sector, coeff in _SECTOR_COEFFICIENTS.items():
        if features.get(f"sector_{sector}", 0) > 0:
            log_settlement += coeff

    # Prior litigation
    if features.get("prior_securities_litigation", 0) > 0:
        log_settlement += float(coefficients.get("prior_securities_litigation", 0.10))

    # Auditor change
    if features.get("auditor_change", 0) > 0:
        log_settlement += float(coefficients.get("auditor_change", 0.10))

    return math.pow(10, log_settlement)


def build_feature_vector(
    state: Any,
    allegation_type: str,
) -> dict[str, float]:
    """Extract 12 regression features from AnalysisState.

    Log-transforms market_cap and class_period_length. Encodes
    categoricals as 0/1. Uses case_characteristics for binary features.

    Args:
        state: AnalysisState with company, extracted, analysis data.
        allegation_type: Primary allegation type for categorical encoding.

    Returns:
        Dict of feature_name -> float value.
    """
    from do_uw.stages.score.case_characteristics import detect_case_characteristics

    features: dict[str, float] = {}

    # Market cap (log-transformed)
    market_cap = 0.0
    if state.company is not None and state.company.market_cap is not None:
        market_cap = float(state.company.market_cap.value)
    features["market_cap_at_filing"] = math.log10(max(market_cap, 1.0))

    # Stock decline (max drop from extracted data)
    max_drop = 0.0
    if state.extracted is not None and state.extracted.market is not None:
        stock_drops = getattr(state.extracted.market, "stock_drops", None)
        if stock_drops is not None:
            for drop in getattr(stock_drops, "single_day_drops", []):
                pct = getattr(drop, "drop_pct", None)
                if pct is not None:
                    val = float(pct.value) if hasattr(pct, "value") else float(pct)
                    if abs(val) > abs(max_drop):
                        max_drop = abs(val) / 100.0 if abs(val) > 1 else abs(val)
    features["max_stock_decline_pct"] = max_drop

    # Allegation type (one-hot)
    for atype in _ALLEGATION_TYPES:
        features[f"allegation_type_{atype}"] = 1.0 if allegation_type == atype else 0.0

    # Jurisdiction (default: other_federal)
    features["jurisdiction_sdny"] = 0.0
    features["jurisdiction_ndcal"] = 0.0

    # Lead plaintiff type (default: individual)
    features["lead_plaintiff_institutional"] = 0.0

    # Class period length (log-transformed, default 365 days)
    features["class_period_length_days"] = math.log10(365)

    # Binary features from case characteristics
    case_chars = detect_case_characteristics(state)
    features["restatement_present"] = 1.0 if case_chars.get("restatement") else 0.0
    features["sec_investigation_present"] = 1.0 if case_chars.get("sec_investigation") else 0.0

    # Named defendants (default 3)
    features["number_of_named_defendants"] = 3.0

    # Sector encoding
    sector = ""
    if state.company is not None:
        identity = state.company.identity
        sector_val = getattr(identity, "sector", None)
        if sector_val is not None:
            sector = (sector_val.value if hasattr(sector_val, "value") else str(sector_val)).lower()
    for sec_key in _SECTOR_COEFFICIENTS:
        features[f"sector_{sec_key}"] = 1.0 if sec_key in sector else 0.0

    # Prior litigation
    features["prior_securities_litigation"] = 0.0

    # Auditor change
    features["auditor_change"] = 0.0
    if case_chars.get("officer_termination"):
        # Proxy: governance changes may co-occur with auditor changes
        pass

    return features


def infer_primary_allegation_type(
    signal_results: dict[str, Any],
    case_chars: dict[str, Any] | None = None,
) -> str:
    """Infer the most likely allegation type from signal results.

    Priority: restatement > regulatory > insider_trading > guidance_miss.

    Args:
        signal_results: Signal evaluation results dict.
        case_chars: Case characteristics dict (optional).

    Returns:
        Allegation type string.
    """
    if case_chars is None:
        case_chars = {}

    def _is_triggered(signal_id: str) -> bool:
        result = signal_results.get(signal_id)
        if result is None:
            return False
        if isinstance(result, dict):
            status = str(result.get("status", "")).upper()
            return status in ("TRIGGERED", "FIRED", "FLAGGED", "RED", "YELLOW", "CRITICAL", "STRONG")
        return False

    # Check restatement signals
    if case_chars.get("restatement") or any(_is_triggered(s) for s in _RESTATEMENT_SIGNALS):
        return "financial_restatement"

    # Check regulatory signals
    if case_chars.get("sec_investigation") or any(_is_triggered(s) for s in _REGULATORY_SIGNALS):
        return "regulatory_action"

    # Check insider trading signals
    if case_chars.get("insider_selling") or any(_is_triggered(s) for s in _INSIDER_SIGNALS):
        return "insider_trading"

    # Check merger signals
    if any(_is_triggered(s) for s in _MERGER_SIGNALS):
        return "merger_objection"

    # Default
    return "guidance_miss"


def predict_all_allegation_types(
    state: Any,
    signal_results: dict[str, Any],
) -> list[tuple[str, float]]:
    """Compute settlement estimates for all plausible allegation types.

    Args:
        state: AnalysisState with company and extracted data.
        signal_results: Signal evaluation results.

    Returns:
        List of (allegation_type, settlement_estimate) sorted by estimate desc.
    """
    all_types = [
        "financial_restatement",
        "insider_trading",
        "regulatory_action",
        "guidance_miss",
        "merger_objection",
        "section_11_ipo",
    ]

    results: list[tuple[str, float]] = []
    for atype in all_types:
        features = build_feature_vector(state, atype)
        settlement = predict_settlement_regression(features)
        results.append((atype, settlement))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
