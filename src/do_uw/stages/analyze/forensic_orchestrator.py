"""XBRL forensic analysis orchestrator (Phase 69).

Runs all forensic modules against XBRL-extracted financial statements
and assembles results into XBRLForensics container.

Extracted from __init__.py to stay under 500-line limit.
"""

from __future__ import annotations

import logging

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def run_xbrl_forensics(state: AnalysisState) -> None:
    """Run all XBRL forensic analysis modules.

    Calls each forensic module with proper error handling:
    - Balance sheet (Plan 01)
    - Revenue quality (Plan 01)
    - Capital allocation (Plan 02, may not exist yet)
    - Debt/tax (Plan 02, may not exist yet)
    - Beneish decomposition (Plan 03)
    - M&A forensics (Plan 03)
    - Earnings quality dashboard (Plan 03)

    Results stored on state.analysis.xbrl_forensics as serialized dict.
    """
    from do_uw.models.xbrl_forensics import XBRLForensics
    from do_uw.stages.analyze.forensic_balance_sheet import (
        compute_balance_sheet_forensics,
    )
    from do_uw.stages.analyze.forensic_beneish import (
        compute_beneish_decomposition,
    )
    from do_uw.stages.analyze.forensic_earnings_dashboard import (
        compute_earnings_dashboard,
    )
    from do_uw.stages.analyze.forensic_ma import compute_ma_forensics
    from do_uw.stages.analyze.forensic_revenue import (
        compute_revenue_forensics,
    )
    from do_uw.stages.extract.validation import merge_reports

    statements = None
    if (
        state.extracted is not None
        and state.extracted.financials is not None
    ):
        statements = state.extracted.financials.statements

    if statements is None:
        logger.warning("XBRL forensics: no financial statements available")
        return

    forensics = XBRLForensics()
    reports = []

    # Balance sheet forensics (Plan 01)
    try:
        bs, bs_report = compute_balance_sheet_forensics(statements)
        forensics.balance_sheet = bs
        reports.append(bs_report)
    except Exception:
        logger.warning("Balance sheet forensics failed", exc_info=True)

    # Revenue forensics (Plan 01)
    try:
        rev, rev_report = compute_revenue_forensics(statements)
        forensics.revenue = rev
        reports.append(rev_report)
    except Exception:
        logger.warning("Revenue forensics failed", exc_info=True)

    # Capital allocation forensics (Plan 02 -- may not exist yet)
    try:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        market_data = None
        if (
            state.extracted is not None
            and state.extracted.market is not None
        ):
            market_data = state.extracted.market.stock
        ca, ca_report = compute_capital_allocation_forensics(
            statements, market_data
        )
        forensics.capital_allocation = ca
        reports.append(ca_report)
    except ImportError:
        logger.info(
            "Capital allocation forensics not yet available (Plan 02)"
        )
    except Exception:
        logger.warning(
            "Capital allocation forensics failed", exc_info=True
        )

    # Debt/tax forensics (Plan 02 -- may not exist yet)
    try:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        dt, dt_report = compute_debt_tax_forensics(statements)
        forensics.debt_tax = dt
        reports.append(dt_report)
    except ImportError:
        logger.info("Debt/tax forensics not yet available (Plan 02)")
    except Exception:
        logger.warning("Debt/tax forensics failed", exc_info=True)

    # Beneish decomposition (Plan 03)
    try:
        bn, bn_report = compute_beneish_decomposition(statements)
        forensics.beneish = bn
        reports.append(bn_report)
    except Exception:
        logger.warning("Beneish decomposition failed", exc_info=True)

    # M&A forensics (Plan 03)
    try:
        ma, ma_report = compute_ma_forensics(statements)
        forensics.ma_forensics = ma
        reports.append(ma_report)
    except Exception:
        logger.warning("M&A forensics failed", exc_info=True)

    # Earnings quality dashboard (Plan 03)
    try:
        eq, eq_report = compute_earnings_dashboard(statements)
        forensics.earnings_quality = eq
        reports.append(eq_report)
    except Exception:
        logger.warning("Earnings dashboard failed", exc_info=True)

    # Store on state
    if state.analysis is not None:
        state.analysis.xbrl_forensics = forensics.model_dump()

    # Merge and log coverage
    if reports:
        merged = merge_reports(reports)
        logger.info(
            "XBRL forensics complete: %.0f%% coverage across %d modules",
            merged.coverage_pct,
            len(reports),
        )
