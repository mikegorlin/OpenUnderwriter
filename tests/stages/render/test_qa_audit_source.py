"""Wave 0 tests for QA-01: QA audit table source column format.

Tests for _format_signal_source() function to be added to html_signals.py.
These tests FAIL before Plan 02 implements the function.
"""
import pytest
from do_uw.stages.render.html_signals import _format_signal_source


FILING_DATE_LOOKUP = {"10-K": "2024-09-28", "DEF 14A": "2026-01-08", "10-Q": "2024-06-29"}


def test_sec_10k_source_shows_date():
    """Filing source includes form type and date."""
    result = _format_signal_source("SEC_10K:balance_sheet", "", FILING_DATE_LOOKUP)
    assert result == "10-K 2024-09-28"


def test_sec_def14a_source_shows_date():
    result = _format_signal_source("SEC_DEF14A:board_members", "", FILING_DATE_LOOKUP)
    assert result == "DEF 14A 2026-01-08"


def test_web_source_passthrough():
    """WEB (gap) sources show truncated domain."""
    result = _format_signal_source("", "WEB (gap) https://reuters.com/tech/apple-lawsuit-very-long-path", FILING_DATE_LOOKUP)
    assert result.startswith("WEB (reuters.com")
    assert len(result) <= 45


def test_no_trace_no_source_shows_dash():
    result = _format_signal_source("", "", FILING_DATE_LOOKUP)
    assert result == "—"


def test_source_type_without_date_shows_label_only():
    """If date not available for form type, show form type label without date."""
    result = _format_signal_source("SEC_8K:event", "", {})
    assert result == "8-K"


def test_multi_source_uses_first():
    """When trace_data_source has multiple sources separated by ';', use the first."""
    result = _format_signal_source("SEC_10K:risk_factors; SEC_DEF14A:board", "", FILING_DATE_LOOKUP)
    assert result == "10-K 2024-09-28"
