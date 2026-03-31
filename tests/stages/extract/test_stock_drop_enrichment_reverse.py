"""Tests for corrective disclosure reverse lookup in stock_drop_enrichment.

Verifies:
- _find_8k_after_drop finds filings 1-14 days AFTER a drop
- Only D&O-relevant 8-K items (2.02, 4.02, 5.02, 2.06) qualify
- enrich_drops_with_reverse_lookup sets corrective disclosure fields
- Web search fallback when no 8-K found
- Already-explained drops are skipped
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import StockDropEvent
from do_uw.stages.extract.stock_drop_enrichment import (
    D_AND_O_RELEVANT_8K_ITEMS,
    _find_8k_after_drop,
    _search_web_for_disclosure,
    enrich_drops_with_reverse_lookup,
)

AS_OF = datetime(2026, 3, 9, tzinfo=UTC)


def _make_drop(
    date_str: str,
    trigger_event: str | None = None,
) -> StockDropEvent:
    """Create a StockDropEvent for testing."""
    te = None
    if trigger_event:
        te = SourcedValue(
            value=trigger_event, source="test", confidence=Confidence.HIGH, as_of=AS_OF,
        )
    return StockDropEvent(
        date=SourcedValue(value=date_str, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        drop_pct=SourcedValue(value=-10.0, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        trigger_event=te,
    )


def _make_8k_doc(
    filing_date: str,
    items: list[str] | None = None,
    accession: str = "0001234-26-000001",
    full_text: str = "",
) -> dict:
    """Create a synthetic 8-K document."""
    doc: dict = {
        "filing_date": filing_date,
        "accession": accession,
        "full_text": full_text,
    }
    if items is not None:
        doc["items"] = items
    return doc


class TestFind8kAfterDrop:
    """Tests for _find_8k_after_drop."""

    def test_finds_filing_5_days_after(self) -> None:
        """Filing 5 days after drop is found with lag=5."""
        docs = [
            _make_8k_doc("2026-01-06", items=["2.02"]),  # 5 days after
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 1
        assert result[0][1] == 5  # lag_days

    def test_ignores_same_day(self) -> None:
        """Filing on same day as drop is excluded (lag=0)."""
        docs = [
            _make_8k_doc("2026-01-01", items=["2.02"]),  # same day
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 0

    def test_ignores_before_drop(self) -> None:
        """Filing before drop is excluded."""
        docs = [
            _make_8k_doc("2025-12-31", items=["2.02"]),  # before drop
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 0

    def test_ignores_beyond_window(self) -> None:
        """Filing 15+ days after is excluded (outside default 14-day window)."""
        docs = [
            _make_8k_doc("2026-01-16", items=["2.02"]),  # 15 days
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 0

    def test_sorted_by_lag_ascending(self) -> None:
        """Multiple matches are sorted by lag (closest first)."""
        docs = [
            _make_8k_doc("2026-01-10", items=["2.02"]),  # 9 days
            _make_8k_doc("2026-01-03", items=["4.02"]),  # 2 days
            _make_8k_doc("2026-01-07", items=["5.02"]),  # 6 days
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 3
        assert result[0][1] == 2
        assert result[1][1] == 6
        assert result[2][1] == 9

    def test_filters_routine_items(self) -> None:
        """8.01 and 9.01 items are filtered out (not D&O-relevant)."""
        docs = [
            _make_8k_doc("2026-01-05", items=["8.01"]),  # routine
            _make_8k_doc("2026-01-05", items=["9.01"]),  # exhibits only
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 0

    def test_accepts_relevant_items(self) -> None:
        """All D&O-relevant items are accepted."""
        for item in ["2.02", "4.02", "5.02", "2.06"]:
            docs = [_make_8k_doc("2026-01-05", items=[item])]
            result = _find_8k_after_drop(docs, "2026-01-01")
            assert len(result) == 1, f"Item {item} should be accepted"

    def test_boundary_day_14(self) -> None:
        """Filing exactly 14 days after is included."""
        docs = [
            _make_8k_doc("2026-01-15", items=["2.02"]),  # 14 days
        ]
        result = _find_8k_after_drop(docs, "2026-01-01")
        assert len(result) == 1
        assert result[0][1] == 14


class TestSearchWebForDisclosure:
    """Tests for _search_web_for_disclosure."""

    def test_finds_article_after_drop(self) -> None:
        """Web article published days after drop is found."""
        web_results = [
            {
                "title": "Acme Corp announces earnings revision",
                "url": "https://news.example.com/acme",
                "date": "2026-01-05",
                "snippet": "Acme Corp reported lower than expected results",
            },
        ]
        result = _search_web_for_disclosure(web_results, "Acme Corp", "2026-01-01")
        assert result is not None
        assert result["url"] == "https://news.example.com/acme"

    def test_ignores_article_before_drop(self) -> None:
        """Article published before drop is not a corrective disclosure."""
        web_results = [
            {
                "title": "Acme Corp quarterly results",
                "url": "https://news.example.com/acme",
                "date": "2025-12-25",
                "snippet": "Acme Corp results were mixed",
            },
        ]
        result = _search_web_for_disclosure(web_results, "Acme Corp", "2026-01-01")
        assert result is None

    def test_requires_company_name_match(self) -> None:
        """Article must mention company name."""
        web_results = [
            {
                "title": "Some unrelated news",
                "url": "https://news.example.com/other",
                "date": "2026-01-05",
                "snippet": "Unrelated company had earnings issues",
            },
        ]
        result = _search_web_for_disclosure(web_results, "Acme Corp", "2026-01-01")
        assert result is None


class TestEnrichDropsWithReverseLookup:
    """Tests for enrich_drops_with_reverse_lookup."""

    def test_sets_corrective_disclosure_from_8k(self) -> None:
        """Corrective disclosure from 8-K sets type, lag, and url."""
        drop = _make_drop("2026-01-01")
        docs = [_make_8k_doc("2026-01-05", items=["2.02"], accession="000123")]
        result = enrich_drops_with_reverse_lookup([drop], docs, [], "Acme Corp")
        assert result[0].corrective_disclosure_type == "8-K"
        assert result[0].corrective_disclosure_lag_days == 4
        assert result[0].corrective_disclosure_url != ""

    def test_skips_explained_drops(self) -> None:
        """Drops that already have a trigger_event are skipped."""
        drop = _make_drop("2026-01-01", trigger_event="earnings_miss")
        docs = [_make_8k_doc("2026-01-05", items=["2.02"])]
        result = enrich_drops_with_reverse_lookup([drop], docs, [], "Acme Corp")
        assert result[0].corrective_disclosure_type == ""  # unchanged

    def test_web_fallback_when_no_8k(self) -> None:
        """Falls back to web search when no 8-K found after drop."""
        drop = _make_drop("2026-01-01")
        web_results = [
            {
                "title": "Acme Corp announces restatement",
                "url": "https://news.example.com/acme-restatement",
                "date": "2026-01-05",
                "snippet": "Acme Corp announced a financial restatement today",
            },
        ]
        result = enrich_drops_with_reverse_lookup([drop], [], web_results, "Acme Corp")
        assert result[0].corrective_disclosure_type == "news"
        assert result[0].corrective_disclosure_url == "https://news.example.com/acme-restatement"

    def test_no_disclosure_found(self) -> None:
        """When neither 8-K nor web results match, fields stay empty."""
        drop = _make_drop("2026-01-01")
        result = enrich_drops_with_reverse_lookup([drop], [], [], "Acme Corp")
        assert result[0].corrective_disclosure_type == ""
        assert result[0].corrective_disclosure_lag_days is None
