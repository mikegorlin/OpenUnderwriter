"""Tests for 8-K item number classifier and D&O severity tagger."""

from __future__ import annotations

from do_uw.models.market import EightKFiling, EightKItemSummary
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.eight_k_item_classifier import (
    DO_CRITICAL_ITEMS,
    ITEM_CATALOG,
    classify_eight_k_filings,
    get_do_critical_items,
    get_do_severity,
    parse_items_from_text,
)


# ------------------------------------------------------------------
# parse_items_from_text tests
# ------------------------------------------------------------------


class TestParseItemsFromText:
    """Tests for regex-based item extraction from 8-K text."""

    def test_single_item(self) -> None:
        text = "Item 2.02 Results of Operations and Financial Condition"
        items = parse_items_from_text(text)
        assert items == ["2.02"]

    def test_multiple_items(self) -> None:
        text = (
            "Item 2.02 Results of Operations\n"
            "Item 9.01 Financial Statements and Exhibits"
        )
        items = parse_items_from_text(text)
        assert items == ["2.02", "9.01"]

    def test_case_insensitive(self) -> None:
        text = "ITEM 4.02 Non-Reliance on Previously Issued Financials"
        items = parse_items_from_text(text)
        assert items == ["4.02"]

    def test_extra_whitespace(self) -> None:
        text = "Item  5.02 Departure of Officers"
        items = parse_items_from_text(text)
        assert items == ["5.02"]

    def test_deduplication(self) -> None:
        """Same item number appearing multiple times is deduplicated."""
        text = (
            "Item 2.02 Results of Operations\n"
            "Pursuant to Item 2.02, the Company reported...\n"
            "Item 9.01 Financial Statements"
        )
        items = parse_items_from_text(text)
        assert items == ["2.02", "9.01"]

    def test_no_items(self) -> None:
        text = "This is a plain text document with no item numbers."
        items = parse_items_from_text(text)
        assert items == []

    def test_invalid_item_number_filtered(self) -> None:
        """Item numbers not in the catalog are excluded."""
        text = "Item 99.99 Not a Real Item"
        items = parse_items_from_text(text)
        assert items == []

    def test_all_do_critical_items(self) -> None:
        """All D&O-critical items are recognized."""
        text = "\n".join(f"Item {item} test" for item in DO_CRITICAL_ITEMS)
        items = parse_items_from_text(text)
        assert set(items) == DO_CRITICAL_ITEMS

    def test_sorted_output(self) -> None:
        text = "Item 5.02 departure\nItem 2.02 earnings\nItem 1.01 agreement"
        items = parse_items_from_text(text)
        assert items == ["1.01", "2.02", "5.02"]

    def test_restatement_filing(self) -> None:
        """Realistic 8-K text with Item 4.02."""
        text = (
            "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
            "FORM 8-K\n"
            "CURRENT REPORT\n"
            "Item 4.02 Non-Reliance on Previously Issued Financial "
            "Statements or a Related Audit Report or Completed Interim "
            "Review\n\n"
            "On January 15, 2024, management and the Audit Committee "
            "concluded that the previously issued financial statements "
            "for Q1-Q3 2023 should no longer be relied upon.\n\n"
            "Item 9.01 Financial Statements and Exhibits"
        )
        items = parse_items_from_text(text)
        assert "4.02" in items
        assert "9.01" in items


# ------------------------------------------------------------------
# get_do_severity tests
# ------------------------------------------------------------------


class TestGetDoSeverity:
    """Tests for D&O severity classification."""

    def test_critical_severity(self) -> None:
        assert get_do_severity(["4.02"]) == "CRITICAL"
        assert get_do_severity(["4.01"]) == "CRITICAL"
        assert get_do_severity(["1.03"]) == "CRITICAL"
        assert get_do_severity(["3.01"]) == "CRITICAL"

    def test_high_severity(self) -> None:
        assert get_do_severity(["5.02"]) == "HIGH"
        assert get_do_severity(["2.05"]) == "HIGH"
        assert get_do_severity(["2.06"]) == "HIGH"

    def test_medium_severity(self) -> None:
        assert get_do_severity(["1.01"]) == "MEDIUM"
        assert get_do_severity(["2.02"]) == "MEDIUM"

    def test_low_severity(self) -> None:
        assert get_do_severity(["9.01"]) == "LOW"
        assert get_do_severity(["7.01"]) == "LOW"
        assert get_do_severity(["8.01"]) == "LOW"

    def test_highest_wins(self) -> None:
        """Multiple items -> highest severity wins."""
        assert get_do_severity(["9.01", "4.02"]) == "CRITICAL"
        assert get_do_severity(["1.01", "5.02"]) == "HIGH"

    def test_empty_items(self) -> None:
        assert get_do_severity([]) == "LOW"


# ------------------------------------------------------------------
# get_do_critical_items tests
# ------------------------------------------------------------------


class TestGetDoCriticalItems:
    """Tests for D&O-critical item filtering."""

    def test_all_critical(self) -> None:
        result = get_do_critical_items(["4.01", "4.02", "5.02"])
        assert set(result) == {"4.01", "4.02", "5.02"}

    def test_mixed(self) -> None:
        result = get_do_critical_items(["2.02", "4.02", "9.01"])
        assert result == ["4.02"]

    def test_none_critical(self) -> None:
        result = get_do_critical_items(["2.02", "9.01", "7.01"])
        assert result == []

    def test_empty(self) -> None:
        result = get_do_critical_items([])
        assert result == []


# ------------------------------------------------------------------
# classify_eight_k_filings integration tests
# ------------------------------------------------------------------


class TestClassifyEightKFilings:
    """Integration tests for the full classifier pipeline."""

    def _make_state(
        self,
        filing_docs: list[dict[str, str]] | None = None,
        llm_extractions: dict | None = None,
        filings_meta: list[dict] | None = None,
    ) -> AnalysisState:
        """Build a minimal state with 8-K data."""
        acquired = AcquiredData()
        if filing_docs is not None:
            acquired.filing_documents["8-K"] = filing_docs
        if llm_extractions is not None:
            acquired.llm_extractions = llm_extractions
        if filings_meta is not None:
            acquired.filings["8-K"] = filings_meta
        state = AnalysisState(ticker="TEST")
        state.acquired_data = acquired
        return state

    def test_empty_state(self) -> None:
        """No 8-K data -> empty summary."""
        state = self._make_state()
        result = classify_eight_k_filings(state)
        assert result.total_filings == 0
        assert result.filings == []
        assert not result.has_restatement
        assert not result.has_auditor_change

    def test_from_filing_documents(self) -> None:
        """Parse items from raw filing text."""
        doc = {
            "accession": "0001-23-456",
            "filing_date": "2024-01-15",
            "form_type": "8-K",
            "full_text": (
                "Item 4.02 Non-Reliance\n"
                "The Company has determined...\n"
                "Item 9.01 Financial Statements"
            ),
        }
        state = self._make_state(filing_docs=[doc])
        result = classify_eight_k_filings(state)

        assert result.total_filings == 1
        assert result.has_restatement is True
        assert result.do_critical_count == 1
        filing = result.filings[0]
        assert "4.02" in filing.items
        assert "9.01" in filing.items
        assert filing.do_severity == "CRITICAL"
        assert "4.02" in filing.do_critical_items
        assert "4.02" in filing.item_titles
        assert filing.item_titles["4.02"] == "Non-Reliance on Previously Issued Financial Statements"

    def test_from_llm_extractions(self) -> None:
        """Pick up items from LLM extraction results."""
        llm = {
            "8-K:0001-23-789": {
                "items_covered": ["5.02", "9.01"],
                "event_date": "2024-03-01",
                "departing_officer": "CFO Left",
            }
        }
        state = self._make_state(llm_extractions=llm)
        result = classify_eight_k_filings(state)

        assert result.total_filings == 1
        assert result.has_officer_departure is True

    def test_merge_sources(self) -> None:
        """Items from regex and LLM are merged for the same filing."""
        doc = {
            "accession": "0001-23-456",
            "filing_date": "2024-01-15",
            "form_type": "8-K",
            "full_text": "Item 2.02 Results of Operations",
        }
        llm = {
            "8-K:0001-23-456": {
                "items_covered": ["2.02", "9.01"],
                "event_date": "2024-01-15",
            }
        }
        state = self._make_state(filing_docs=[doc], llm_extractions=llm)
        result = classify_eight_k_filings(state)

        assert result.total_filings == 1
        filing = result.filings[0]
        # Should have both items, not duplicates
        assert "2.02" in filing.items
        assert "9.01" in filing.items
        assert len(filing.items) == 2

    def test_item_frequency(self) -> None:
        """item_frequency counts across all filings."""
        docs = [
            {
                "accession": "acc-1",
                "filing_date": "2024-01-01",
                "form_type": "8-K",
                "full_text": "Item 2.02 Results\nItem 9.01 Exhibits",
            },
            {
                "accession": "acc-2",
                "filing_date": "2024-04-01",
                "form_type": "8-K",
                "full_text": "Item 2.02 Results\nItem 5.02 Departure\nItem 9.01 Exhibits",
            },
        ]
        state = self._make_state(filing_docs=docs)
        result = classify_eight_k_filings(state)

        assert result.total_filings == 2
        assert result.item_frequency["2.02"] == 2
        assert result.item_frequency["9.01"] == 2
        assert result.item_frequency["5.02"] == 1

    def test_multiple_do_critical_flags(self) -> None:
        """Multiple D&O-critical items set correct boolean flags."""
        doc = {
            "accession": "acc-1",
            "filing_date": "2024-01-01",
            "form_type": "8-K",
            "full_text": (
                "Item 4.01 Changes in Certifying Accountant\n"
                "Item 4.02 Non-Reliance\n"
                "Item 5.02 Departure\n"
                "Item 2.05 Exit Activities\n"
                "Item 2.06 Material Impairments"
            ),
        }
        state = self._make_state(filing_docs=[doc])
        result = classify_eight_k_filings(state)

        assert result.has_auditor_change is True
        assert result.has_restatement is True
        assert result.has_officer_departure is True
        assert result.has_restructuring is True
        assert result.has_impairment is True

    def test_filings_sorted_by_date_descending(self) -> None:
        """Filings are returned newest first."""
        docs = [
            {
                "accession": "old",
                "filing_date": "2023-01-01",
                "form_type": "8-K",
                "full_text": "Item 2.02 Results",
            },
            {
                "accession": "new",
                "filing_date": "2024-06-01",
                "form_type": "8-K",
                "full_text": "Item 5.02 Departure",
            },
        ]
        state = self._make_state(filing_docs=docs)
        result = classify_eight_k_filings(state)

        assert result.filings[0].accession == "new"
        assert result.filings[1].accession == "old"

    def test_metadata_only_filings(self) -> None:
        """Filings from metadata (no full text) are captured."""
        meta = [
            {
                "accession": "meta-1",
                "filing_date": "2024-02-15",
                "items": ["1.01", "9.01"],
            }
        ]
        state = self._make_state(filings_meta=meta)
        result = classify_eight_k_filings(state)

        assert result.total_filings == 1
        assert "1.01" in result.filings[0].items

    def test_no_acquired_data(self) -> None:
        """State with no acquired_data returns empty summary."""
        state = AnalysisState(ticker="TEST")
        state.acquired_data = None  # type: ignore[assignment]
        result = classify_eight_k_filings(state)
        assert result.total_filings == 0


# ------------------------------------------------------------------
# ITEM_CATALOG completeness tests
# ------------------------------------------------------------------


class TestItemCatalog:
    """Tests for the item catalog constants."""

    def test_all_major_items_present(self) -> None:
        """All standard 8-K items are in the catalog."""
        required = [
            "1.01", "1.02", "1.03", "2.01", "2.02", "2.03", "2.04",
            "2.05", "2.06", "3.01", "3.02", "3.03", "4.01", "4.02",
            "5.01", "5.02", "5.03", "5.04", "5.05", "5.06", "5.07",
            "7.01", "8.01", "9.01",
        ]
        for item in required:
            assert item in ITEM_CATALOG, f"Missing item {item} in ITEM_CATALOG"

    def test_all_critical_items_in_catalog(self) -> None:
        """All D&O-critical items are also in the catalog."""
        for item in DO_CRITICAL_ITEMS:
            assert item in ITEM_CATALOG, f"Critical item {item} not in ITEM_CATALOG"

    def test_critical_items_have_high_or_critical_severity(self) -> None:
        """D&O-critical items should have HIGH or CRITICAL severity."""
        for item in DO_CRITICAL_ITEMS:
            _, severity = ITEM_CATALOG[item]
            assert severity in (
                "HIGH", "CRITICAL"
            ), f"Critical item {item} has unexpected severity: {severity}"
