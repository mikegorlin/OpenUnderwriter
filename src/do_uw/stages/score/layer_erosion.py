"""Layer erosion probability computation (Phase 108).

Computes the probability that a settlement reaches a given layer
attachment point using a log-normal distribution fitted to historical
settlement data. Handles ABC, Side A excess of ABC, and Side A only
tower structures. DIC probability is signal-driven.

Uses math.erfc for CDF computation (no scipy dependency):
  Phi(x) = 0.5 * erfc(-x / sqrt(2))
  LogNormal_CDF(x, mu, sigma) = Phi((ln(x) - mu) / sigma)
  P(S > x) = 1 - LogNormal_CDF(x, mu, sigma)

Distribution parameters are allegation-type-specific:
  - Restatement: sigma ~1.0 (high dispersion)
  - Guidance miss: sigma ~0.6 (low dispersion)
  - Default: sigma ~0.8 (typical case)
"""

from __future__ import annotations

import logging
import math
from typing import Any

from do_uw.models.severity import LayerErosionResult

__all__ = [
    "compute_dic_probability",
    "compute_layer_erosion",
    "compute_side_a_erosion",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Dispersion parameters by allegation type
# ---------------------------------------------------------------

_SIGMA_BY_ALLEGATION: dict[str, float] = {
    "financial_restatement": 1.0,
    "insider_trading": 0.9,
    "regulatory_action": 0.85,
    "guidance_miss": 0.6,
    "guidance_miss_only": 0.6,
    "merger_objection": 0.5,
    "section_11_ipo": 0.7,
}
_DEFAULT_SIGMA = 0.8

# ---------------------------------------------------------------
# DIC signal configuration
# ---------------------------------------------------------------

_GOING_CONCERN_SIGNALS = frozenset({
    "FIN.HEALTH.going_concern",
    "FIN.HEALTH.going_concern_opinion",
})
_ALTMAN_DISTRESS_SIGNALS = frozenset({
    "FIN.HEALTH.altman_z_distress",
    "FIN.HEALTH.z_score",
})
_CASH_RUNWAY_SIGNALS = frozenset({
    "FIN.HEALTH.cash_runway_short",
    "FIN.HEALTH.liquidity_crisis",
})
_LEVERAGE_SIGNALS = frozenset({
    "FIN.HEALTH.high_leverage",
    "FIN.HEALTH.debt_maturity_wall",
})

_DIC_MAX = 0.8


# ---------------------------------------------------------------
# Log-normal CDF helpers (no scipy needed)
# ---------------------------------------------------------------


def _standard_normal_cdf(x: float) -> float:
    """Compute Phi(x) = CDF of standard normal distribution.

    Uses math.erfc: Phi(x) = 0.5 * erfc(-x / sqrt(2)).
    """
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _lognormal_survival(x: float, mu: float, sigma: float) -> float:
    """Compute P(X > x) for X ~ LogNormal(mu, sigma).

    LogNormal_CDF(x) = Phi((ln(x) - mu) / sigma)
    P(X > x) = 1 - LogNormal_CDF(x)

    Args:
        x: Value to compute survival probability for (must be > 0).
        mu: Log-scale location parameter (ln of median).
        sigma: Log-scale dispersion parameter.

    Returns:
        P(X > x), survival probability.
    """
    if x <= 0:
        return 1.0
    if sigma <= 0:
        return 0.0

    z = (math.log(x) - mu) / sigma
    return 1.0 - _standard_normal_cdf(z)


# ---------------------------------------------------------------
# Layer erosion computation
# ---------------------------------------------------------------


def compute_layer_erosion(
    median_settlement: float,
    sigma: float,
    attachment: float,
    limit: float,
    product: str = "ABC",
) -> LayerErosionResult:
    """Compute layer erosion probability from log-normal distribution.

    P(settlement > attachment) tells us how likely a claim is to
    reach Liberty's layer. liberty_severity is how much of Liberty's
    layer would be consumed.

    Args:
        median_settlement: Median estimated settlement (USD).
        sigma: Log-scale dispersion parameter.
        attachment: Layer attachment point (USD).
        limit: Layer limit (USD).
        product: Product type ("ABC" or "SIDE_A").

    Returns:
        LayerErosionResult with penetration probability and severity.
    """
    # mu = ln(median_settlement) since median of LogNormal(mu, sigma) = exp(mu)
    if median_settlement <= 0:
        return LayerErosionResult(
            attachment=attachment,
            limit=limit,
            product=product,
            penetration_probability=0.0,
            liberty_severity=0.0,
            effective_expected_loss=0.0,
        )

    mu = math.log(median_settlement)

    # P(settlement > attachment)
    penetration_prob = _lognormal_survival(attachment, mu, sigma)

    # Liberty severity: max(0, median_settlement - attachment), capped by limit
    liberty_severity = max(0.0, median_settlement - attachment)
    liberty_severity = min(liberty_severity, limit)

    # Effective expected loss = P_erosion * liberty_severity
    # (Note: P_claim is applied externally in SeverityResult)
    effective_el = penetration_prob * liberty_severity

    return LayerErosionResult(
        attachment=attachment,
        limit=limit,
        product=product,
        penetration_probability=round(penetration_prob, 4),
        liberty_severity=round(liberty_severity, 2),
        effective_expected_loss=round(effective_el, 2),
    )


def compute_side_a_erosion(
    median_settlement: float,
    sigma: float,
    attachment: float,
    limit: float,
    abc_tower_top: float,
    product: str = "SIDE_A",
) -> LayerErosionResult:
    """Compute Side A layer erosion with tower-aware attachment.

    Side A excess of ABC: effective attachment = abc_tower_top + attachment.
    This is essentially catastrophe-only exposure because the entire ABC
    tower must be exhausted first.

    Args:
        median_settlement: Median estimated settlement (USD).
        sigma: Log-scale dispersion parameter.
        attachment: Side A attachment above ABC tower (USD).
        limit: Side A layer limit (USD).
        abc_tower_top: Top of ABC tower (USD).
        product: Product type (default "SIDE_A").

    Returns:
        LayerErosionResult with effective attachment.
    """
    effective_attachment = abc_tower_top + attachment

    return compute_layer_erosion(
        median_settlement=median_settlement,
        sigma=sigma,
        attachment=effective_attachment,
        limit=limit,
        product=product,
    )


# ---------------------------------------------------------------
# DIC probability
# ---------------------------------------------------------------


def _is_signal_triggered(signal_results: dict[str, Any], signal_id: str) -> bool:
    """Check if a signal is in a triggered state."""
    result = signal_results.get(signal_id)
    if result is None:
        return False
    if isinstance(result, dict):
        if result.get("triggered") is True or result.get("fired") is True:
            return True
        status = str(result.get("status", "")).upper()
        if status in ("TRIGGERED", "FIRED", "FLAGGED", "RED", "YELLOW", "CRITICAL", "STRONG", "HIGH"):
            return True
    if hasattr(result, "status"):
        status_val = str(getattr(result, "status", "")).upper()
        if status_val in ("TRIGGERED", "FIRED", "FLAGGED", "RED", "YELLOW", "CRITICAL", "STRONG", "HIGH"):
            return True
    return False


def compute_dic_probability(signal_results: dict[str, Any]) -> float:
    """Estimate DIC (Difference-in-Conditions) trigger probability.

    DIC triggers when entity coverage is unavailable (bankruptcy,
    coverage dispute). Probability driven by financial distress signals.

    Signal-driven scoring:
      - Going concern: 0.5 base
      - Altman Z-score distress: 0.3 base
      - Cash runway < 12mo: 0.2 base
      - High leverage / debt maturity: 0.1 base
    Additive combination, capped at 0.8.

    Args:
        signal_results: Signal evaluation results dict.

    Returns:
        DIC probability (0.0 to 0.8).
    """
    prob = 0.0

    # Going concern
    for sig_id in _GOING_CONCERN_SIGNALS:
        if _is_signal_triggered(signal_results, sig_id):
            prob += 0.5
            break

    # Altman Z-score distress
    for sig_id in _ALTMAN_DISTRESS_SIGNALS:
        if _is_signal_triggered(signal_results, sig_id):
            prob += 0.3
            break

    # Cash runway
    for sig_id in _CASH_RUNWAY_SIGNALS:
        if _is_signal_triggered(signal_results, sig_id):
            prob += 0.2
            break

    # Leverage / debt maturity
    for sig_id in _LEVERAGE_SIGNALS:
        if _is_signal_triggered(signal_results, sig_id):
            prob += 0.1
            break

    return min(prob, _DIC_MAX)


def get_sigma_for_allegation(allegation_type: str) -> float:
    """Get log-normal dispersion parameter for allegation type.

    Args:
        allegation_type: Allegation type key.

    Returns:
        Sigma value for log-normal distribution.
    """
    return _SIGMA_BY_ALLEGATION.get(allegation_type, _DEFAULT_SIGMA)
