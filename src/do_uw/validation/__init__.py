"""Multi-ticker validation infrastructure.

Provides the ValidationRunner for batch pipeline execution with
checkpointing, continue-on-failure, and comprehensive reporting.
"""

from __future__ import annotations

from do_uw.validation.config import VALIDATION_TICKERS, TickerEntry, get_tickers
from do_uw.validation.cost_report import (
    CostReport,
    CostReportEntry,
    generate_cost_report,
    print_cost_report,
    save_cost_report,
)
from do_uw.validation.report import (
    ReportSummary,
    TickerResult,
    ValidationReport,
    print_report,
    save_report,
)
from do_uw.validation.runner import ValidationRunner

__all__ = [
    "VALIDATION_TICKERS",
    "CostReport",
    "CostReportEntry",
    "ReportSummary",
    "TickerEntry",
    "TickerResult",
    "ValidationReport",
    "ValidationRunner",
    "generate_cost_report",
    "get_tickers",
    "print_cost_report",
    "print_report",
    "save_cost_report",
    "save_report",
]
