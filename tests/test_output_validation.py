"""Process validation harness for generated .docx worksheets.

Reads the final rendered document (not state.json) and validates
that factual claims are correct. Each test class covers one ticker.

Tests are skipped when the .docx file is not present (requires
a prior pipeline run: ``do-uw analyze {TICKER}``).

Tests marked ``xfail`` with ``reason="pre-fix document"`` validate issues
that are confirmed fixed in code (Phase 23) but require document
regeneration (``do-uw analyze {TICKER}``) to clear. They will
automatically start passing once the pipeline is re-run.

All tests are marked with ``@pytest.mark.output_validation`` so they
can be run independently:
    uv run pytest -m output_validation -v
"""

from __future__ import annotations

import re

import pytest

from tests.ground_truth.helpers import (
    find_in_tables,
    find_text_containing,
    load_docx,
    read_docx_tables,
    read_docx_text,
)
from tests.ground_truth.nflx import GROUND_TRUTH as NFLX_TRUTH
from tests.ground_truth.smci import GROUND_TRUTH as SMCI_TRUTH
from tests.ground_truth.xom import GROUND_TRUTH as XOM_TRUTH

pytest.importorskip("docx", reason="python-docx required for output validation")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TICKER_MARKER = pytest.mark.output_validation


def _get_doc(ticker: str):  # type: ignore[no-untyped-def]
    """Load .docx or skip test."""
    doc = load_docx(ticker)
    if doc is None:
        pytest.skip(f"No .docx found for {ticker} (run pipeline first)")
    return doc


def _parse_number_from_cell(cell_text: str) -> int | None:
    """Parse a numeric value from a table cell, stripping formatting."""
    # Remove $, commas, spaces, and other non-digit characters
    cleaned = re.sub(r"[^\d]", "", cell_text)
    if cleaned:
        return int(cleaned)
    return None


# ---------------------------------------------------------------------------
# XOM Output Validation
# ---------------------------------------------------------------------------


@_TICKER_MARKER
class TestXOMOutput:
    """Validate XOM worksheet against known facts."""

    @pytest.mark.xfail(
        reason="Pre-fix doc: employee renders as '62' not 62000",
        strict=False,
    )
    def test_employee_count_reasonable(self) -> None:
        """Employee count should be between 50K-80K for Exxon."""
        doc = _get_doc("XOM")
        tables = read_docx_tables(doc)
        facts = XOM_TRUTH.get("output_facts", {})
        emp_rows = find_in_tables(tables, "employee")
        assert emp_rows, "No 'Employee' row found in any table"
        # Parse number from the value cell (second column typically)
        _, _, row = emp_rows[0]
        assert len(row) >= 2, f"Employee row too short: {row}"
        emp_num = _parse_number_from_cell(row[1])
        assert emp_num is not None, f"Could not parse employee count from: {row[1]}"
        emp_min = facts.get("employee_count_min", 50000)
        emp_max = facts.get("employee_count_max", 80000)
        assert emp_num >= emp_min, (
            f"XOM employees {emp_num:,} < minimum {emp_min:,} "
            f"(cell text: '{row[1]}')"
        )
        assert emp_num <= emp_max, (
            f"XOM employees {emp_num:,} > maximum {emp_max:,} "
            f"(cell text: '{row[1]}')"
        )

    def test_sector_correct(self) -> None:
        """XOM should be classified as Energy sector."""
        doc = _get_doc("XOM")
        text = read_docx_text(doc)
        assert "Energy" in text, "XOM should be classified as Energy sector"
        # Should NOT be misclassified
        facts = XOM_TRUTH.get("output_facts", {})
        for bad_sector in facts.get("sector_not", []):
            # Only flag if the bad sector appears as a classification,
            # not just in body text discussion
            sector_mentions = find_text_containing(doc, bad_sector)
            # Allow mentions in context (e.g. "Technology risks") but
            # the primary sector display should say Energy
            if sector_mentions:
                assert any(
                    "Energy" in m for m in find_text_containing(doc, "Sector")
                ), (
                    f"XOM sector might be misclassified: found '{bad_sector}' "
                    f"mentions without 'Energy' in sector display"
                )

    @pytest.mark.xfail(
        reason="Pre-fix doc: shares outstanding has $ prefix",
        strict=False,
    )
    def test_shares_no_dollar_prefix(self) -> None:
        """Shares Outstanding should NOT have $ prefix (they're counts)."""
        doc = _get_doc("XOM")
        tables = read_docx_tables(doc)
        share_rows = find_in_tables(tables, "shares outstanding")
        for _, _, row in share_rows:
            for cell in row[1:]:
                assert not cell.strip().startswith("$"), (
                    f"Shares Outstanding has $ prefix: '{cell}'"
                )

    def test_auditor_present(self) -> None:
        """PwC should appear as auditor in the worksheet."""
        doc = _get_doc("XOM")
        text = read_docx_text(doc)
        assert any(
            kw in text
            for kw in [
                "PricewaterhouseCoopers",
                "PwC",
                "Pricewaterhouse",
            ]
        ), "XOM auditor (PwC) not found in worksheet"

    def test_company_name_present(self) -> None:
        """Exxon Mobil should appear in the document."""
        doc = _get_doc("XOM")
        text = read_docx_text(doc)
        assert any(
            name in text
            for name in ["Exxon Mobil", "EXXON MOBIL", "ExxonMobil"]
        ), "Company name 'Exxon Mobil' not found in worksheet"

    def test_has_financial_tables(self) -> None:
        """Worksheet should contain financial data tables."""
        doc = _get_doc("XOM")
        tables = read_docx_tables(doc)
        # Should have revenue or total assets somewhere
        revenue_rows = find_in_tables(tables, "revenue")
        asset_rows = find_in_tables(tables, "total assets")
        assert revenue_rows or asset_rows, (
            "No financial data tables found (no 'Revenue' or 'Total Assets' rows)"
        )


# ---------------------------------------------------------------------------
# SMCI Output Validation
# ---------------------------------------------------------------------------


@_TICKER_MARKER
class TestSMCIOutput:
    """Validate SMCI worksheet against known facts."""

    def test_sector_tech(self) -> None:
        """SMCI should be classified as Technology sector."""
        doc = _get_doc("SMCI")
        text = read_docx_text(doc)
        assert "Technology" in text, "SMCI should be classified as Technology sector"

    def test_employee_count_reasonable(self) -> None:
        """Employee count should be between 3K-12K for Super Micro."""
        doc = _get_doc("SMCI")
        tables = read_docx_tables(doc)
        facts = SMCI_TRUTH.get("output_facts", {})
        emp_rows = find_in_tables(tables, "employee")
        assert emp_rows, "No 'Employee' row found in any table"
        _, _, row = emp_rows[0]
        assert len(row) >= 2, f"Employee row too short: {row}"
        emp_num = _parse_number_from_cell(row[1])
        assert emp_num is not None, f"Could not parse employee count from: {row[1]}"
        emp_min = facts.get("employee_count_min", 3000)
        emp_max = facts.get("employee_count_max", 12000)
        assert emp_num >= emp_min, (
            f"SMCI employees {emp_num:,} < minimum {emp_min:,} "
            f"(cell text: '{row[1]}')"
        )
        assert emp_num <= emp_max, (
            f"SMCI employees {emp_num:,} > maximum {emp_max:,} "
            f"(cell text: '{row[1]}')"
        )

    def test_company_name_present(self) -> None:
        """Super Micro Computer should appear in the document."""
        doc = _get_doc("SMCI")
        text = read_docx_text(doc)
        assert any(
            name in text
            for name in ["Super Micro", "SUPER MICRO", "SMCI"]
        ), "Company name 'Super Micro' not found in worksheet"

    def test_has_known_outcome_signals(self) -> None:
        """SMCI worksheet should surface at least some known D&O signals.

        As a known-outcome company with Hindenburg report, EY resignation,
        DOJ investigation, and material weakness, the worksheet should
        contain at least SOME of these signals (depending on data sources).
        """
        doc = _get_doc("SMCI")
        text = read_docx_text(doc)
        facts = SMCI_TRUTH.get("output_facts", {})
        expected_events = facts.get("known_events_expected", [])
        found_events: list[str] = []
        for event in expected_events:
            if event.lower() in text.lower():
                found_events.append(event)
        # At minimum, SOME known outcome signals should be present.
        # Full coverage depends on blind spot detection being wired.
        assert found_events, (
            f"SMCI worksheet contains NONE of the expected known-outcome "
            f"signals: {expected_events}. This indicates blind spot detection "
            f"is not surfacing critical D&O events."
        )

    def test_has_data_quality_notice_or_known_events(self) -> None:
        """SMCI worksheet should have blind spot findings OR data quality notice."""
        doc = _get_doc("SMCI")
        text = read_docx_text(doc)
        has_blind_spot_notice = "blind spot" in text.lower()
        has_data_quality = "data quality" in text.lower()
        has_hindenburg = "hindenburg" in text.lower()
        has_auditor_issue = any(
            kw in text.lower()
            for kw in ["ey resign", "ernst & young resign", "auditor resign"]
        )
        has_doj = "doj" in text.lower()
        has_material_weakness = "material weakness" in text.lower()
        assert (
            has_blind_spot_notice
            or has_data_quality
            or has_hindenburg
            or has_auditor_issue
            or has_doj
            or has_material_weakness
        ), (
            "SMCI worksheet should have either blind spot detection notice, "
            "data quality notice, or findings about Hindenburg/auditor "
            "resignation/DOJ/material weakness"
        )

    def test_has_financial_tables(self) -> None:
        """Worksheet should contain financial data tables."""
        doc = _get_doc("SMCI")
        tables = read_docx_tables(doc)
        revenue_rows = find_in_tables(tables, "revenue")
        asset_rows = find_in_tables(tables, "total assets")
        assert revenue_rows or asset_rows, (
            "No financial data tables found (no 'Revenue' or 'Total Assets' rows)"
        )


# ---------------------------------------------------------------------------
# NFLX Output Validation
# ---------------------------------------------------------------------------


@_TICKER_MARKER
class TestNFLXOutput:
    """Validate NFLX worksheet -- critical for sector classification fix."""

    @pytest.mark.xfail(
        reason="Pre-fix doc: NFLX before SIC 7841->COMM fix",
        strict=False,
    )
    def test_sector_is_communication_services(self) -> None:
        """THE critical test: NFLX must NOT be classified as Industrials."""
        doc = _get_doc("NFLX")
        text = read_docx_text(doc)
        facts = NFLX_TRUTH.get("output_facts", {})
        sector_display = facts.get("sector_display", "Communication Services")
        assert sector_display.lower() in text.lower() or "entertainment" in text.lower(), (
            f"NFLX should show '{sector_display}' or 'Entertainment', not 'Industrials'"
        )
        for forbidden in facts.get("sector_not", []):
            # Allow if the correct sector is also present
            if forbidden.lower() in text.lower():
                assert sector_display.lower() in text.lower(), (
                    f"NFLX shows '{forbidden}' without '{sector_display}'"
                )

    @pytest.mark.xfail(
        reason="Pre-fix doc: NFLX before SIC 7841->COMM fix",
        strict=False,
    )
    def test_not_industrials_in_executive_summary(self) -> None:
        """Executive summary must not describe NFLX as industrials company."""
        doc = _get_doc("NFLX")
        # Find executive summary paragraphs (first section)
        paras = find_text_containing(doc, "mega-cap")
        for p in paras:
            assert "industrials" not in p.lower(), (
                f"Exec summary describes NFLX as industrials: {p[:100]}"
            )

    def test_employee_count_reasonable(self) -> None:
        """Employee count should be between 10K-20K for Netflix."""
        doc = _get_doc("NFLX")
        tables = read_docx_tables(doc)
        facts = NFLX_TRUTH.get("output_facts", {})
        emp_rows = find_in_tables(tables, "employee")
        if emp_rows:
            _, _, row = emp_rows[0]
            if len(row) >= 2:
                num_str = re.sub(r"[^\d]", "", row[1])
                if num_str:
                    emp_num = int(num_str)
                    emp_min = facts.get("employee_count_min", 10000)
                    emp_max = facts.get("employee_count_max", 20000)
                    assert emp_num >= emp_min, (
                        f"NFLX employees {emp_num:,} < minimum {emp_min:,}"
                    )
                    assert emp_num <= emp_max, (
                        f"NFLX employees {emp_num:,} > maximum {emp_max:,}"
                    )

    @pytest.mark.xfail(
        reason="Pre-fix doc: auditor not populated for NFLX",
        strict=False,
    )
    def test_auditor_present(self) -> None:
        """Ernst & Young should appear as auditor in the worksheet."""
        doc = _get_doc("NFLX")
        text = read_docx_text(doc)
        assert any(
            kw in text for kw in ["Ernst & Young", "Ernst", "EY"]
        ), "NFLX auditor (EY) not found in worksheet"

    def test_company_name_present(self) -> None:
        """Netflix should appear in the document."""
        doc = _get_doc("NFLX")
        text = read_docx_text(doc)
        assert any(
            name in text
            for name in ["Netflix", "NETFLIX", "NFLX"]
        ), "Company name 'Netflix' not found in worksheet"

    def test_has_financial_tables(self) -> None:
        """Worksheet should contain financial data tables."""
        doc = _get_doc("NFLX")
        tables = read_docx_tables(doc)
        revenue_rows = find_in_tables(tables, "revenue")
        asset_rows = find_in_tables(tables, "total assets")
        assert revenue_rows or asset_rows, (
            "No financial data tables found (no 'Revenue' or 'Total Assets' rows)"
        )
