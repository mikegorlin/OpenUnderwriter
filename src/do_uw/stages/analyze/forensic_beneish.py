"""Beneish M-Score decomposition + multi-period trajectory (FRNSC-05, FRNSC-07).

Decomposes Beneish M-Score into all 8 individual indices:
DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI.

Identifies primary driver (highest weighted contribution) and builds
multi-period trajectory to detect manipulation trend onset.

Uses compute_m_score from financial_formulas.py for actual computation,
then unpacks components for forensic decomposition.
"""

from __future__ import annotations

import logging

from do_uw.models.financials import (
    DistressZone,
    FinancialStatements,
)
from do_uw.models.xbrl_forensics import BeneishDecomposition
from do_uw.stages.analyze.financial_formulas import compute_m_score
from do_uw.stages.analyze.forensic_helpers import (
    collect_all_period_values,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# Beneish 8-variable model coefficients (used for weighted contribution).
_BENEISH_COEFFICIENTS: dict[str, float] = {
    "dsri": 0.920,
    "gmi": 0.528,
    "aqi": 0.404,
    "sgi": 0.892,
    "depi": 0.115,
    "sgai": -0.172,
    "tata": 4.679,
    "lvgi": -0.327,
}

# Index-type components use (value - 1.0) for deviation; TATA uses raw value.
_RATIO_INDICES = {"dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi"}


def _collect_all_inputs(
    statements: FinancialStatements,
) -> dict[str, float | None]:
    """Collect all financial inputs needed for Beneish M-Score.

    Mirrors the pattern from financial_models._collect_all_inputs
    but focused on Beneish-specific concepts.
    """
    concepts_latest = [
        "accounts_receivable", "revenue", "gross_profit",
        "current_assets", "property_plant_equipment", "total_assets",
        "depreciation_amortization", "sga_expense", "net_income",
        "operating_cash_flow", "total_liabilities",
    ]
    concepts_prior = [
        "accounts_receivable", "revenue", "gross_profit",
        "current_assets", "property_plant_equipment", "total_assets",
        "depreciation_amortization", "sga_expense", "total_liabilities",
    ]

    result: dict[str, float | None] = {}
    for c in concepts_latest:
        result[c] = extract_input(statements, c, "latest")
    for c in concepts_prior:
        result[f"{c}_prior"] = extract_input(statements, c, "prior")

    return result


def _identify_primary_driver(
    components: dict[str, float | None],
) -> tuple[str | None, str | None]:
    """Identify which Beneish component contributes most to M-Score.

    For index-type components (DSRI, GMI, etc.), deviation = value - 1.0.
    For TATA, deviation = raw value.
    Weighted contribution = coefficient * deviation.

    Returns:
        Tuple of (primary_driver_name, context_note or None).
    """
    weighted: dict[str, float] = {}
    for name, coeff in _BENEISH_COEFFICIENTS.items():
        val = components.get(name)
        if val is None:
            continue
        if name in _RATIO_INDICES:
            deviation = val - 1.0
        else:
            deviation = val
        weighted[name] = abs(coeff * deviation)

    if not weighted:
        return None, None

    primary = max(weighted, key=lambda k: weighted[k])

    # SGI-driven note per plan spec
    note: str | None = None
    if primary == "sgi":
        note = (
            "High sales growth rate is the primary driver "
            "-- not necessarily manipulation"
        )

    return primary, note


def _build_beneish_trajectory(
    statements: FinancialStatements,
) -> list[dict[str, float | str]]:
    """Build M-Score trajectory across available periods.

    For multi-period trajectory (FRNSC-07), compute Beneish for each
    pair of consecutive periods to detect manipulation trend onset.
    """
    # Get all period labels from statements
    periods: list[str] = []
    if statements.balance_sheet is not None:
        periods = list(statements.balance_sheet.periods)
    elif statements.income_statement is not None:
        periods = list(statements.income_statement.periods)

    if len(periods) < 2:
        return []

    trajectory: list[dict[str, float | str]] = []

    # For each consecutive pair of periods, compute M-Score
    for i in range(1, len(periods)):
        prior_period = periods[i - 1]
        current_period = periods[i]

        # Collect inputs for this period pair
        inputs = _collect_period_pair_inputs(
            statements, current_period, prior_period
        )

        result = compute_m_score(inputs)
        if result.score is not None:
            entry: dict[str, float | str] = {
                "period": current_period,
                "score": result.score,
                "zone": result.zone.value,
            }
            # Add individual components
            for comp_name, comp_val in result.components.items():
                if comp_val is not None:
                    entry[comp_name] = round(comp_val, 4)
            trajectory.append(entry)

    return trajectory


def _get_period_value(
    statements: FinancialStatements,
    concept: str,
    period: str,
) -> float | None:
    """Get a single concept value for a specific period."""
    from do_uw.stages.analyze.forensic_helpers import find_line_item

    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = find_line_item(stmt.line_items, concept)
        if item is not None:
            sv = item.values.get(period)
            if sv is not None:
                return sv.value
    return None


def _collect_period_pair_inputs(
    statements: FinancialStatements,
    current: str,
    prior: str,
) -> dict[str, float | None]:
    """Collect Beneish inputs for a specific period pair."""
    concepts = [
        "accounts_receivable", "revenue", "gross_profit",
        "current_assets", "property_plant_equipment", "total_assets",
        "depreciation_amortization", "sga_expense", "net_income",
        "operating_cash_flow", "total_liabilities",
    ]

    result: dict[str, float | None] = {}
    for c in concepts:
        result[c] = _get_period_value(statements, c, current)
    for c in concepts:
        result[f"{c}_prior"] = _get_period_value(statements, c, prior)

    return result


def _zone_from_distress(zone: DistressZone) -> str:
    """Map DistressZone enum to forensic zone string."""
    if zone == DistressZone.DISTRESS:
        return "manipulation_likely"
    if zone == DistressZone.SAFE:
        return "safe"
    return "insufficient_data"


def compute_beneish_decomposition(
    statements: FinancialStatements,
) -> tuple[BeneishDecomposition, ExtractionReport]:
    """Compute Beneish M-Score decomposition with all 8 indices.

    Runs the standard M-Score computation, then decomposes into
    individual indices with primary driver identification and
    multi-period trajectory.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (BeneishDecomposition, ExtractionReport).
    """
    expected = [
        "composite_score", "dsri", "gmi", "aqi", "sgi",
        "depi", "sgai", "tata", "lvgi", "primary_driver",
        "trajectory",
    ]

    # Collect inputs and compute M-Score
    inputs = _collect_all_inputs(statements)
    result = compute_m_score(inputs)

    if result.score is None:
        report = create_report(
            extractor_name="forensic_beneish",
            expected=expected,
            found=[],
            source_filing="Derived from XBRL financial statements",
        )
        return BeneishDecomposition(), report

    # Extract components from DistressResult
    components = result.components

    # Identify primary driver
    primary_driver, context_note = _identify_primary_driver(components)

    # Build multi-period trajectory (FRNSC-07)
    trajectory = _build_beneish_trajectory(statements)

    decomposition = BeneishDecomposition(
        composite_score=result.score,
        dsri=components.get("dsri"),
        gmi=components.get("gmi"),
        aqi=components.get("aqi"),
        sgi=components.get("sgi"),
        depi=components.get("depi"),
        sgai=components.get("sgai"),
        tata=components.get("tata"),
        lvgi=components.get("lvgi"),
        zone=_zone_from_distress(result.zone),
        primary_driver=primary_driver,
        trajectory=trajectory,
    )

    # Build found list
    found: list[str] = ["composite_score"]
    for name in ["dsri", "gmi", "aqi", "sgi", "depi", "sgai", "tata", "lvgi"]:
        if components.get(name) is not None:
            found.append(name)
    if primary_driver:
        found.append("primary_driver")
    if trajectory:
        found.append("trajectory")

    warnings: list[str] = []
    if result.is_partial:
        warnings.append(
            f"Partial computation: missing {result.missing_inputs}"
        )
    if context_note:
        warnings.append(context_note)

    report = create_report(
        extractor_name="forensic_beneish",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
        warnings=warnings,
    )

    logger.info(
        "Beneish decomposition: score=%.4f zone=%s driver=%s "
        "trajectory=%d periods",
        result.score,
        decomposition.zone,
        primary_driver or "N/A",
        len(trajectory),
    )

    return decomposition, report
