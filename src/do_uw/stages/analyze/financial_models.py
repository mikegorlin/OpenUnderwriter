"""Financial distress models -- Altman Z, Beneish M, Ohlson O, Piotroski F.

Sector-appropriate variants, partial-score handling, trajectory support.
Model formulas (Beneish, Ohlson, Piotroski) are in distress_formulas.py.
Covers SECT3-06 and SECT3-07.
"""

from __future__ import annotations

import logging

from do_uw.models.financials import (
    DistressIndicators,
    DistressResult,
    DistressZone,
    FinancialLineItem,
    FinancialStatements,
)
from do_uw.stages.analyze.financial_formulas import (
    altman_zone_double_prime,
    altman_zone_original,
    compute_m_score,
)
from do_uw.stages.analyze.financial_formulas_distress import (
    compute_f_score,
    compute_o_score,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Sectors routed to Z''-Score (non-manufacturing / financial).
_FINANCIAL_SECTORS: frozenset[str] = frozenset({"FINS", "REIT", "INSUR"})


def derive_total_liabilities(
    inputs: dict[str, float | None],
) -> float | None:
    """Derive total liabilities with a 4-step cascade.

    Priority order:
    1. Direct Liabilities tag value
    2. total_assets - stockholders_equity (basic balance sheet equation)
    3. total_assets - stockholders_equity + minority_interest
       (when SE tag includes noncontrolling interest)
    4. liabilities_and_stockholders_equity - stockholders_equity
       (fallback for companies using only L&SE tag)

    Args:
        inputs: Dict of concept names to values (may contain None).

    Returns:
        Derived total liabilities, or None if no derivation possible.
    """
    # Priority 1: Direct Liabilities tag
    tl = inputs.get("total_liabilities")
    if tl is not None:
        return tl

    ta = inputs.get("total_assets")
    se = inputs.get("stockholders_equity")

    # Priority 2 & 3: TA - SE, with optional minority interest adjustment
    if ta is not None and se is not None:
        mi = inputs.get("minority_interest")
        if mi is not None and mi > 0:
            # SE tag includes NCI -- add minority_interest back
            derived = ta - se + mi
        else:
            derived = ta - se

        # Sanity check: TL > TA indicates negative equity (valid but flag it)
        if derived > ta:
            logger.warning(
                "Derived total_liabilities (%.0f) > total_assets (%.0f) "
                "-- company may have negative equity",
                derived, ta,
            )
        return derived

    # Priority 4: LiabilitiesAndStockholdersEquity - SE
    lse = inputs.get("liabilities_and_stockholders_equity")
    if lse is not None and se is not None:
        return lse - se

    return None


def _find_line_item(
    items: list[FinancialLineItem],
    concept: str,
) -> FinancialLineItem | None:
    """Find a line item by XBRL concept name."""
    for item in items:
        if item.xbrl_concept == concept:
            return item
    return None


def _get_latest_value(item: FinancialLineItem) -> float | None:
    """Get the most recent period value from a line item."""
    if not item.values:
        return None
    sorted_keys = sorted(item.values.keys())
    for key in reversed(sorted_keys):
        sv = item.values.get(key)
        if sv is not None:
            return sv.value
    return None


def _get_prior_value(item: FinancialLineItem) -> float | None:
    """Get the second-most-recent period value from a line item."""
    if not item.values or len(item.values) < 2:
        return None
    sorted_keys = sorted(item.values.keys())
    if len(sorted_keys) < 2:
        return None
    sv = item.values.get(sorted_keys[-2])
    if sv is not None:
        return sv.value
    return None


def _get_value_for_period(
    item: FinancialLineItem, period: str
) -> float | None:
    """Get value for a specific period label."""
    sv = item.values.get(period)
    if sv is not None:
        return sv.value
    return None


def _extract_input(
    statements: FinancialStatements,
    concept: str,
    period: str = "latest",
) -> float | None:
    """Safely extract a financial value by concept name."""
    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = _find_line_item(stmt.line_items, concept)
        if item is None:
            continue
        if period == "prior":
            val = _get_prior_value(item)
        else:
            val = _get_latest_value(item)
        if val is not None:
            return val
    return None


def _collect_all_inputs(
    statements: FinancialStatements,
) -> dict[str, float | None]:
    """Collect all financial inputs needed across all four models."""
    concepts = [
        "total_assets", "total_liabilities", "current_assets",
        "current_liabilities", "retained_earnings", "ebit",
        "revenue", "stockholders_equity", "net_income",
        "operating_cash_flow", "accounts_receivable", "gross_profit",
        "property_plant_equipment", "sga_expense",
        "depreciation_amortization", "long_term_debt",
        "cash_and_equivalents", "shares_outstanding",
        "capital_expenditures", "dividends_paid",
        "cost_of_revenue",
        # Added for total liabilities derivation cascade
        "minority_interest",
        "liabilities_and_stockholders_equity",
    ]
    result: dict[str, float | None] = {}
    for c in concepts:
        result[c] = _extract_input(statements, c, "latest")
    prior_concepts = [
        "total_assets", "total_liabilities", "current_assets",
        "current_liabilities", "revenue", "gross_profit",
        "property_plant_equipment", "sga_expense",
        "depreciation_amortization", "net_income",
        "accounts_receivable", "long_term_debt",
        "shares_outstanding", "cost_of_revenue",
        # Added for total liabilities derivation cascade
        "minority_interest", "stockholders_equity",
        "liabilities_and_stockholders_equity",
    ]
    for c in prior_concepts:
        result[f"{c}_prior"] = _extract_input(statements, c, "prior")

    # Derive total_liabilities using 4-step cascade (handles minority
    # interest, L&SE fallback, and sanity checks)
    derived_tl = derive_total_liabilities(result)
    if derived_tl is not None and result.get("total_liabilities") is None:
        result["total_liabilities"] = derived_tl
        logger.info(
            "Derived total_liabilities = %.0f via cascade",
            derived_tl,
        )

    # Apply same cascade to prior period
    prior_inputs: dict[str, float | None] = {
        "total_liabilities": result.get("total_liabilities_prior"),
        "total_assets": result.get("total_assets_prior"),
        "stockholders_equity": result.get("stockholders_equity_prior"),
        "minority_interest": result.get("minority_interest_prior"),
        "liabilities_and_stockholders_equity": result.get(
            "liabilities_and_stockholders_equity_prior"
        ),
    }
    derived_tl_prior = derive_total_liabilities(prior_inputs)
    if derived_tl_prior is not None and result.get("total_liabilities_prior") is None:
        result["total_liabilities_prior"] = derived_tl_prior

    return result


def _altman_z_original(
    inputs: dict[str, float | None],
    market_cap: float | None,
) -> DistressResult:
    """Compute original 5-factor Altman Z-Score for manufacturing firms.

    Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MktCap/TL)
        + 1.0*(Sales/TA)
    """
    ta = inputs.get("total_assets")
    tl = inputs.get("total_liabilities")
    ca = inputs.get("current_assets")
    cl = inputs.get("current_liabilities")
    re = inputs.get("retained_earnings")
    ebit = inputs.get("ebit")
    sales = inputs.get("revenue")

    missing: list[str] = []
    required = {
        "total_assets": ta, "total_liabilities": tl,
        "current_assets": ca, "current_liabilities": cl,
        "retained_earnings": re, "ebit": ebit,
        "revenue": sales, "market_cap": market_cap,
    }
    for name, val in required.items():
        if val is None:
            missing.append(name)
            logger.warning("Altman Z (original): missing %s", name)

    if ta is None or ta == 0.0:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="original",
        )

    available = sum(1 for v in required.values() if v is not None)
    if available < 5:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="original",
        )

    wc = (ca or 0.0) - (cl or 0.0)
    z = (
        1.2 * (wc / ta)
        + 1.4 * ((re or 0.0) / ta)
        + 3.3 * ((ebit or 0.0) / ta)
        + 0.6 * ((market_cap or 0.0) / tl if tl and tl != 0.0 else 0.0)
        + 1.0 * ((sales or 0.0) / ta)
    )
    z = round(z, 4)

    return DistressResult(
        score=z, zone=altman_zone_original(z),
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="original",
    )


def _altman_z_double_prime(
    inputs: dict[str, float | None],
) -> DistressResult:
    """Compute Altman Z''-Score for non-manufacturing / financial firms.

    Z'' = 6.56*(WC/TA) + 3.26*(RE/TA) + 6.72*(EBIT/TA)
          + 1.05*(BV_Equity/TL)
    """
    ta = inputs.get("total_assets")
    tl = inputs.get("total_liabilities")
    ca = inputs.get("current_assets")
    cl = inputs.get("current_liabilities")
    re = inputs.get("retained_earnings")
    ebit = inputs.get("ebit")
    equity = inputs.get("stockholders_equity")

    missing: list[str] = []
    required = {
        "total_assets": ta, "total_liabilities": tl,
        "current_assets": ca, "current_liabilities": cl,
        "retained_earnings": re, "ebit": ebit,
        "stockholders_equity": equity,
    }
    for name, val in required.items():
        if val is None:
            missing.append(name)
            logger.warning("Altman Z'': missing %s", name)

    if ta is None or ta == 0.0:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="z_double_prime",
        )

    available = sum(1 for v in required.values() if v is not None)
    if available < 4:
        return DistressResult(
            score=None, zone=DistressZone.NOT_APPLICABLE,
            is_partial=True, missing_inputs=missing,
            model_variant="z_double_prime",
        )

    wc = (ca or 0.0) - (cl or 0.0)
    z = (
        6.56 * (wc / ta)
        + 3.26 * ((re or 0.0) / ta)
        + 6.72 * ((ebit or 0.0) / ta)
        + 1.05 * ((equity or 0.0) / tl if tl and tl != 0.0 else 0.0)
    )
    z = round(z, 4)

    return DistressResult(
        score=z, zone=altman_zone_double_prime(z),
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="z_double_prime",
    )


def _early_stage_metrics(
    inputs: dict[str, float | None],
) -> DistressResult:
    """Alternative metrics for pre-revenue / early-stage companies."""
    cash = inputs.get("cash_and_equivalents")
    ocf = inputs.get("operating_cash_flow")
    tl = inputs.get("total_liabilities")

    missing: list[str] = []
    if cash is None:
        missing.append("cash_and_equivalents")
    if ocf is None:
        missing.append("operating_cash_flow")

    burn_rate: float | None = None
    if ocf is not None and ocf < 0:
        burn_rate = round(abs(ocf) / 12.0, 2)

    runway: float | None = None
    if cash is not None and burn_rate is not None and burn_rate > 0:
        runway = round(cash / burn_rate, 1)

    cash_to_debt: float | None = None
    if cash is not None and tl is not None and tl > 0:
        cash_to_debt = round(cash / tl, 4)

    alt: dict[str, float | str] = {}
    if runway is not None:
        alt["cash_runway_months"] = runway
    if burn_rate is not None:
        alt["monthly_burn_rate"] = burn_rate
    if cash_to_debt is not None:
        alt["cash_to_debt_ratio"] = cash_to_debt

    return DistressResult(
        score=None, zone=DistressZone.NOT_APPLICABLE,
        is_partial=bool(missing), missing_inputs=missing,
        model_variant="early_stage",
        trajectory=[alt] if alt else [],
    )


def _compute_z_score(
    inputs: dict[str, float | None],
    sector: str,
    market_cap: float | None,
) -> DistressResult:
    """Route to appropriate Altman Z variant based on sector/revenue."""
    revenue = inputs.get("revenue")
    if revenue is None or revenue == 0.0:
        return _early_stage_metrics(inputs)
    if sector.upper() in _FINANCIAL_SECTORS:
        return _altman_z_double_prime(inputs)
    return _altman_z_original(inputs, market_cap)


def _build_trajectory(
    statements: FinancialStatements,
    model_fn: str,
    sector: str,
    market_cap: float | None,
) -> list[dict[str, float | str]]:
    """Build score trajectory across available periods."""
    periods: list[str] = []
    if statements.balance_sheet is not None:
        periods = list(statements.balance_sheet.periods)
    elif statements.income_statement is not None:
        periods = list(statements.income_statement.periods)

    if len(periods) < 2:
        return []

    trajectory: list[dict[str, float | str]] = []
    for period in periods:
        inputs = _collect_period_inputs(statements, period)
        result: DistressResult | None = None

        if model_fn == "altman":
            revenue = inputs.get("revenue")
            if revenue is None or revenue == 0.0:
                continue
            if sector.upper() in _FINANCIAL_SECTORS:
                result = _altman_z_double_prime(inputs)
            else:
                result = _altman_z_original(inputs, market_cap)

        if result is not None and result.score is not None:
            trajectory.append({
                "period": period,
                "score": result.score,
                "zone": result.zone.value,
            })

    return trajectory


def _collect_period_inputs(
    statements: FinancialStatements,
    period: str,
) -> dict[str, float | None]:
    """Collect financial inputs for a specific period."""
    concepts = [
        "total_assets", "total_liabilities", "current_assets",
        "current_liabilities", "retained_earnings", "ebit",
        "revenue", "stockholders_equity", "net_income",
        "operating_cash_flow", "accounts_receivable", "gross_profit",
        "property_plant_equipment", "sga_expense",
        "depreciation_amortization", "long_term_debt",
        "cash_and_equivalents", "shares_outstanding",
    ]
    result: dict[str, float | None] = {}
    for concept in concepts:
        result[concept] = _get_period_value(statements, concept, period)
    return result


def _get_period_value(
    statements: FinancialStatements,
    concept: str,
    period: str,
) -> float | None:
    """Get a single concept value for a specific period."""
    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = _find_line_item(stmt.line_items, concept)
        if item is not None:
            val = _get_value_for_period(item, period)
            if val is not None:
                return val
    return None


def compute_distress_indicators(
    statements: FinancialStatements,
    sector: str,
    market_cap: float | None = None,
) -> tuple[DistressIndicators, list[ExtractionReport]]:
    """Compute all four financial distress scoring models.

    Routes to sector-appropriate variants for Altman Z-Score.
    Handles missing inputs with partial scores and explicit flags.

    Args:
        statements: Extracted financial statements.
        sector: Company sector code (e.g., "TECH", "FINS").
        market_cap: Market capitalization in USD (for Altman original).

    Returns:
        Tuple of (DistressIndicators, list of ExtractionReports).
    """
    inputs = _collect_all_inputs(statements)
    reports: list[ExtractionReport] = []

    # Model 1: Altman Z-Score (sector-routed).
    z_result = _compute_z_score(inputs, sector, market_cap)
    z_trajectory = _build_trajectory(
        statements, "altman", sector, market_cap
    )
    if z_trajectory and z_result.model_variant != "early_stage":
        z_result.trajectory = z_trajectory

    _log_result("Altman Z-Score", z_result)
    reports.append(_make_model_report("altman_z_score", z_result))

    # Model 2: Beneish M-Score.
    m_result = compute_m_score(inputs)
    _log_result("Beneish M-Score", m_result)
    reports.append(_make_model_report("beneish_m_score", m_result))

    # Model 3: Ohlson O-Score.
    o_result = compute_o_score(inputs)
    _log_result("Ohlson O-Score", o_result)
    reports.append(_make_model_report("ohlson_o_score", o_result))

    # Model 4: Piotroski F-Score.
    f_result = compute_f_score(inputs)
    _log_result("Piotroski F-Score", f_result)
    reports.append(_make_model_report("piotroski_f_score", f_result))

    indicators = DistressIndicators(
        altman_z_score=z_result,
        beneish_m_score=m_result,
        ohlson_o_score=o_result,
        piotroski_f_score=f_result,
    )

    return indicators, reports


def _log_result(name: str, result: DistressResult) -> None:
    """Log distress model result."""
    if result.score is not None:
        logger.info(
            "%s: score=%.4f zone=%s partial=%s variant=%s",
            name, result.score, result.zone.value,
            result.is_partial, result.model_variant,
        )
    else:
        logger.info(
            "%s: score=N/A zone=%s partial=%s variant=%s missing=%s",
            name, result.zone.value, result.is_partial,
            result.model_variant, result.missing_inputs,
        )


def _make_model_report(
    model_name: str,
    result: DistressResult,
) -> ExtractionReport:
    """Create an ExtractionReport for a distress model computation."""
    all_expected = [
        f"{model_name}:score", f"{model_name}:zone",
    ]
    found: list[str] = []
    if result.score is not None:
        found.append(f"{model_name}:score")
    if result.zone != DistressZone.NOT_APPLICABLE:
        found.append(f"{model_name}:zone")

    warnings: list[str] = []
    if result.is_partial:
        warnings.append(
            f"Partial computation: missing {result.missing_inputs}"
        )

    return create_report(
        extractor_name=model_name,
        expected=all_expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
        warnings=warnings,
    )
