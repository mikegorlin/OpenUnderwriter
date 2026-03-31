"""Tax indicator extraction from financial data and filing text.

Computes effective tax rate, ETR trend, deferred tax analysis,
tax haven subsidiary exposure, unrecognized tax benefits, and
transfer pricing risk flags.

Covers SECT3-13 (tax indicators) for D&O underwriting.

Usage:
    tax_data, report = extract_tax_indicators(state)
    state.extracted.financials.tax_indicators = tax_data
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_company_facts,
    get_filings,
    now,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)
from do_uw.stages.extract.xbrl_mapping import (
    extract_concept_value,
    get_latest_value,
    get_period_values,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "etr",
    "etr_trend",
    "deferred_tax",
    "tax_havens",
    "utb",
    "transfer_pricing",
]

# US statutory corporate tax rate for comparison.
US_STATUTORY_RATE: float = 0.21

# ETR thresholds for flagging.
ETR_AGGRESSIVE_LOW: float = 0.15
ETR_UNUSUAL_HIGH: float = 0.30


# ---------------------------------------------------------------------------
# Tax haven config loading
# ---------------------------------------------------------------------------


def load_tax_havens(
    path: Path | None = None,
) -> list[dict[str, str]]:
    """Load the tax haven jurisdiction list.

    Args:
        path: Optional override path to tax_havens.json.

    Returns:
        List of jurisdiction dicts with name, country_code, category.
    """
    if path is not None:
        import json
        if not path.exists():
            logger.warning("Tax havens config not found: %s", path)
            return []
        with path.open(encoding="utf-8") as f:
            data_raw: dict[str, Any] = json.load(f)
        jurisdictions = data_raw.get("jurisdictions")
        if not isinstance(jurisdictions, list):
            return []
        return cast(list[dict[str, str]], jurisdictions)

    data = load_config("tax_havens")
    jurisdictions = data.get("jurisdictions")
    if not isinstance(jurisdictions, list):
        return []
    return cast(list[dict[str, str]], jurisdictions)


# ---------------------------------------------------------------------------
# XBRL helpers
# ---------------------------------------------------------------------------


def _get_tax_expense(facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract income tax expense from XBRL."""
    concepts = [
        "IncomeTaxExpenseBenefit",
        "IncomeTaxesPaid",
        "CurrentIncomeTaxExpenseBenefit",
    ]
    for concept in concepts:
        entries = extract_concept_value(facts, concept, "10-K", "USD")
        if entries:
            return entries
    return []


def _get_pretax_income(facts: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract pretax income from XBRL."""
    concepts = [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ]
    for concept in concepts:
        entries = extract_concept_value(facts, concept, "10-K", "USD")
        if entries:
            return entries
    return []


def _compute_etr(
    tax_entries: list[dict[str, Any]],
    pretax_entries: list[dict[str, Any]],
    periods: int = 3,
) -> list[tuple[str, float]]:
    """Compute ETR for each available period.

    Returns list of (period_end_date, etr) tuples.
    """
    tax_by_end: dict[str, float] = {}
    for entry in get_period_values(tax_entries, periods):
        end = str(entry.get("end", ""))
        val = entry.get("val")
        if end and val is not None:
            tax_by_end[end] = float(val)

    pretax_by_end: dict[str, float] = {}
    for entry in get_period_values(pretax_entries, periods):
        end = str(entry.get("end", ""))
        val = entry.get("val")
        if end and val is not None:
            pretax_by_end[end] = float(val)

    results: list[tuple[str, float]] = []
    for end_date in sorted(pretax_by_end):
        pretax = pretax_by_end[end_date]
        tax = tax_by_end.get(end_date)
        if tax is not None and pretax != 0:
            etr = abs(tax / pretax)
            results.append((end_date, round(etr, 4)))

    return results


def _get_deferred_tax(
    facts: dict[str, Any],
) -> tuple[float | None, float | None]:
    """Extract deferred tax assets and liabilities from XBRL.

    Returns:
        Tuple of (assets_net, liabilities_net).
    """
    assets_entry = get_latest_value(
        extract_concept_value(facts, "DeferredTaxAssetsNet", "10-K", "USD")
    )
    liabilities_entry = get_latest_value(
        extract_concept_value(
            facts, "DeferredTaxLiabilitiesNet", "10-K", "USD"
        )
    )

    assets = float(assets_entry["val"]) if assets_entry and "val" in assets_entry else None
    liabilities = (
        float(liabilities_entry["val"])
        if liabilities_entry and "val" in liabilities_entry
        else None
    )
    return assets, liabilities


def _get_unrecognized_tax_benefits(
    facts: dict[str, Any],
) -> float | None:
    """Extract UnrecognizedTaxBenefits from XBRL."""
    entry = get_latest_value(
        extract_concept_value(
            facts, "UnrecognizedTaxBenefits", "10-K", "USD"
        )
    )
    if entry and "val" in entry:
        return float(entry["val"])
    return None


def _cross_reference_tax_havens(
    exhibit_21_text: str,
    havens: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Cross-reference Exhibit 21 subsidiaries against tax haven list.

    Counts each occurrence of a jurisdiction name on separate lines,
    reflecting multiple subsidiaries in the same haven.

    Args:
        exhibit_21_text: Plain text of Exhibit 21 subsidiary listing.
        havens: Tax haven jurisdiction list.

    Returns:
        Dict with keys per category (zero_tax, low_tax, preferential_regime),
        each mapping to list of jurisdiction names found (may have repeats).
    """
    results: dict[str, list[str]] = {
        "zero_tax": [],
        "low_tax": [],
        "preferential_regime": [],
    }

    if not exhibit_21_text.strip():
        return results

    # Process line by line to count subsidiaries per jurisdiction.
    lines = exhibit_21_text.lower().splitlines()
    for line in lines:
        for haven in havens:
            name = haven.get("name", "")
            category = haven.get("category", "")
            if name.lower() in line and category in results:
                results[category].append(name)

    return results


def _assess_transfer_pricing_risk(
    state: AnalysisState,
    etr_trend: str,
) -> bool:
    """Flag transfer pricing risk if international ops + declining ETR."""
    if state.company is None:
        return False

    # Check for international operations.
    geo_footprint = state.company.geographic_footprint
    has_international = len(geo_footprint) > 1

    # Check subsidiary count as secondary signal.
    sub_count_sv = state.company.subsidiary_count
    many_subs = sub_count_sv is not None and sub_count_sv.value > 10

    return (has_international or many_subs) and etr_trend == "declining"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_tax_indicators(
    state: AnalysisState,
) -> tuple[SourcedValue[dict[str, Any]] | None, ExtractionReport]:
    """Extract tax indicators from XBRL and filing data.

    Computes effective tax rate, ETR trend, deferred tax analysis,
    tax haven subsidiary exposure, unrecognized tax benefits, and
    transfer pricing risk.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (SourcedValue wrapping tax dict or None, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "XBRL Company Facts + Exhibit 21"

    facts = get_company_facts(state)
    tax_data: dict[str, Any] = {}

    # 1. Effective Tax Rate.
    tax_entries = _get_tax_expense(facts)
    pretax_entries = _get_pretax_income(facts)
    etr_series = _compute_etr(tax_entries, pretax_entries)

    if etr_series:
        current_etr = etr_series[-1][1]
        tax_data["effective_tax_rate"] = current_etr
        tax_data["etr_periods"] = [
            {"period": p, "etr": e} for p, e in etr_series
        ]
        found.append("etr")

        if current_etr < ETR_AGGRESSIVE_LOW:
            warnings.append(
                f"ETR {current_etr:.1%} below aggressive threshold "
                f"({ETR_AGGRESSIVE_LOW:.0%})"
            )
        elif current_etr > ETR_UNUSUAL_HIGH:
            warnings.append(
                f"ETR {current_etr:.1%} above unusual threshold "
                f"({ETR_UNUSUAL_HIGH:.0%})"
            )
    else:
        tax_data["effective_tax_rate"] = None
        warnings.append("Could not compute ETR: missing tax or pretax data")

    # 2. ETR Trend.
    etr_trend = "unknown"
    if len(etr_series) >= 2:
        recent = etr_series[-1][1]
        prior = etr_series[-2][1]
        if recent < prior - 0.02:
            etr_trend = "declining"
        elif recent > prior + 0.02:
            etr_trend = "increasing"
        else:
            etr_trend = "stable"
        found.append("etr_trend")
    tax_data["etr_trend"] = etr_trend

    # 3. Deferred Tax Analysis.
    dta_net, dtl_net = _get_deferred_tax(facts)
    if dta_net is not None or dtl_net is not None:
        tax_data["deferred_tax_assets_net"] = dta_net
        tax_data["deferred_tax_liabilities_net"] = dtl_net
        tax_data["deferred_tax_net"] = (
            (dta_net or 0) - (dtl_net or 0)
        )
        found.append("deferred_tax")

    # 4. Tax Haven Subsidiaries.
    filings = get_filings(state)
    exhibit_21 = str(filings.get("exhibit_21", ""))
    havens = load_tax_havens()
    haven_results = _cross_reference_tax_havens(exhibit_21, havens)

    total_haven_count = sum(len(v) for v in haven_results.values())
    tax_data["tax_haven_subsidiary_count"] = total_haven_count
    tax_data["tax_haven_details"] = haven_results

    # Estimate haven percentage.
    sub_count_sv = state.company.subsidiary_count if state.company else None
    total_subs = sub_count_sv.value if sub_count_sv else 0
    if total_subs > 0 and total_haven_count > 0:
        haven_pct = round(total_haven_count / total_subs * 100, 1)
        tax_data["tax_haven_pct"] = haven_pct
        if haven_pct > 20:
            warnings.append(
                f"Tax haven exposure: {haven_pct:.1f}% of subsidiaries"
            )
    else:
        tax_data["tax_haven_pct"] = 0.0
    found.append("tax_havens")

    # 5. Unrecognized Tax Benefits.
    utb = _get_unrecognized_tax_benefits(facts)
    if utb is not None:
        tax_data["unrecognized_tax_benefits"] = utb
        found.append("utb")

    # 6. Transfer Pricing Risk.
    tp_risk = _assess_transfer_pricing_risk(state, etr_trend)
    tax_data["transfer_pricing_risk_flag"] = tp_risk
    if tp_risk:
        warnings.append("Transfer pricing risk: international ops + declining ETR")
    found.append("transfer_pricing")

    # Build result.
    result: SourcedValue[dict[str, Any]] | None = None
    if found:
        result = SourcedValue[dict[str, Any]](
            value=tax_data,
            source=source_filing,
            confidence=Confidence.MEDIUM,
            as_of=now(),
        )

    report = create_report(
        extractor_name="tax_indicators",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return result, report
