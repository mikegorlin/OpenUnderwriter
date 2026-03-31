"""M&A forensic analysis module (FRNSC-08).

Detects serial acquirer patterns from XBRL acquisition data:
- Serial acquirer = acquisitions in 3+ of last 5 years
- Goodwill accumulation rate vs revenue growth
- Total acquisition spend across periods

Acquisition data comes from Phase 67 XBRL concept (acquisitions_net).
Handles None gracefully when concept not yet available.
"""

from __future__ import annotations

import logging

from do_uw.models.financials import FinancialStatements
from do_uw.models.xbrl_forensics import MAForensics
from do_uw.stages.analyze.financial_formulas import safe_ratio
from do_uw.stages.analyze.forensic_helpers import (
    collect_all_period_values,
    extract_input,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)


def compute_ma_forensics(
    statements: FinancialStatements,
) -> tuple[MAForensics, ExtractionReport]:
    """Compute M&A forensic indicators from XBRL data.

    Scans all available periods for acquisition spending to detect
    serial acquirer patterns. Uses goodwill growth vs revenue growth
    to assess acquisition effectiveness.

    Args:
        statements: Extracted financial statements.

    Returns:
        Tuple of (MAForensics, ExtractionReport).
    """
    expected = [
        "is_serial_acquirer",
        "acquisition_years",
        "total_acquisition_spend",
        "goodwill_growth_rate",
        "acquisition_to_revenue",
    ]
    found: list[str] = []
    warnings: list[str] = []

    # Collect acquisition data across all periods
    acq_values = collect_all_period_values(statements, "acquisitions_net")

    # Identify years with acquisition activity
    # Acquisitions are typically negative (cash outflow)
    acquisition_years: list[str] = []
    total_spend = 0.0
    has_any_acquisition = False

    for period, value in acq_values:
        # Acquisitions show as negative in cash flow
        if value != 0.0:
            acquisition_years.append(period)
            total_spend += abs(value)
            has_any_acquisition = True

    # Serial acquirer = acquisitions in 3+ of last 5 years
    is_serial = len(acquisition_years) >= 3

    result = MAForensics(
        is_serial_acquirer=is_serial,
        acquisition_years=acquisition_years,
    )
    found.append("is_serial_acquirer")
    found.append("acquisition_years")

    if has_any_acquisition:
        result.total_acquisition_spend = round(total_spend, 2)
        found.append("total_acquisition_spend")

        # Acquisition to revenue ratio
        revenue = extract_input(statements, "revenue")
        if revenue is not None and revenue > 0:
            result.acquisition_to_revenue = round(total_spend / revenue, 4)
            found.append("acquisition_to_revenue")

    # Goodwill growth rate vs revenue growth
    gw_values = collect_all_period_values(statements, "goodwill")
    rev_values = collect_all_period_values(statements, "revenue")

    if len(gw_values) >= 2 and len(rev_values) >= 2:
        gw_first = gw_values[0][1]
        gw_last = gw_values[-1][1]
        rev_first = rev_values[0][1]
        rev_last = rev_values[-1][1]

        gw_growth = safe_ratio(gw_last - gw_first, abs(gw_first)) if gw_first != 0 else None
        rev_growth = safe_ratio(rev_last - rev_first, abs(rev_first)) if rev_first != 0 else None

        if gw_growth is not None and rev_growth is not None:
            # Ratio > 1.0 means goodwill growing faster than revenue
            growth_ratio = safe_ratio(gw_growth, rev_growth)
            if growth_ratio is not None:
                result.goodwill_growth_rate = round(growth_ratio, 4)
                found.append("goodwill_growth_rate")
                if growth_ratio > 2.0:
                    warnings.append(
                        f"Goodwill growing {growth_ratio:.1f}x faster "
                        "than revenue -- acquisition integration concern"
                    )

    if not acq_values:
        warnings.append(
            "No acquisitions_net data found -- "
            "Phase 67 XBRL concept may not be available"
        )

    report = create_report(
        extractor_name="forensic_ma",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
        warnings=warnings,
    )

    logger.info(
        "M&A forensics: serial=%s years=%s spend=%.0f",
        is_serial,
        acquisition_years,
        total_spend,
    )

    return result, report
