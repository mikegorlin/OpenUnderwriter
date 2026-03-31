"""Integration tests verifying Phase 74 pipeline wiring.

Confirms that quarterly XBRL extraction, trends, reconciliation,
and ownership analysis are wired into the pipeline extract stage.
"""

from __future__ import annotations

from pathlib import Path

_EXTRACT_INIT = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "stages" / "extract" / "__init__.py"
_INSIDER_TRADING = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "stages" / "extract" / "insider_trading.py"


def test_extract_init_contains_quarterly_xbrl_call() -> None:
    """Extract __init__.py must contain the quarterly XBRL wiring."""
    source = _EXTRACT_INIT.read_text()
    assert "extract_quarterly_xbrl" in source, (
        "extract_quarterly_xbrl not wired in extract __init__.py"
    )


def test_extract_init_contains_trend_call() -> None:
    """Extract __init__.py must contain the trend computation wiring."""
    source = _EXTRACT_INIT.read_text()
    assert "compute_all_trends" in source, (
        "compute_all_trends not wired in extract __init__.py"
    )


def test_extract_init_contains_reconciliation_call() -> None:
    """Extract __init__.py must contain the reconciliation wiring."""
    source = _EXTRACT_INIT.read_text()
    assert "reconcile_quarterly" in source
    assert "cross_validate_yfinance" in source


def test_insider_trading_contains_ownership_call() -> None:
    """insider_trading.py must contain run_ownership_analysis wiring."""
    source = _INSIDER_TRADING.read_text()
    assert "run_ownership_analysis" in source, (
        "run_ownership_analysis not wired in insider_trading.py"
    )


def test_run_ownership_analysis_importable() -> None:
    """run_ownership_analysis must be importable and callable."""
    from do_uw.stages.extract.insider_trading_analysis import (
        run_ownership_analysis,
    )

    assert callable(run_ownership_analysis)


def test_run_ownership_analysis_empty_transactions() -> None:
    """run_ownership_analysis with empty inputs returns empty warnings."""
    from do_uw.models.market_events import InsiderTradingAnalysis
    from do_uw.stages.extract.insider_trading_analysis import (
        run_ownership_analysis,
    )

    analysis = InsiderTradingAnalysis()
    warnings = run_ownership_analysis([], [], analysis)
    assert warnings == []
    assert analysis.ownership_alerts == []
    assert analysis.ownership_trajectories == {}


def test_extract_quarterly_xbrl_empty_facts() -> None:
    """extract_quarterly_xbrl with empty facts returns 0 quarters."""
    from do_uw.stages.extract.xbrl_quarterly import extract_quarterly_xbrl

    result = extract_quarterly_xbrl({}, "0001234567")
    assert len(result.quarters) == 0


def test_compute_all_trends_empty_quarters() -> None:
    """compute_all_trends with empty QuarterlyStatements returns empty dict."""
    from do_uw.models.financials import QuarterlyStatements
    from do_uw.stages.extract.xbrl_trends import compute_all_trends

    qs = QuarterlyStatements(quarters=[], cik="0001234567")
    result = compute_all_trends(qs)
    assert result == {}


def test_reconcile_quarterly_none_xbrl() -> None:
    """reconcile_quarterly with None xbrl returns a ReconciliationReport."""
    from do_uw.stages.extract.xbrl_llm_reconciler import reconcile_quarterly

    report = reconcile_quarterly(None, [])
    assert hasattr(report, "total_comparisons")
    assert report.total_comparisons == 0
