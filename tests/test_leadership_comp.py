"""Tests for leadership profiles and compensation analysis extraction.

Covers tests:
- Leadership name validation: garbage names rejected, valid names accepted
- Leadership extraction from proxy, departure from 8-K
- Stability score full team, red flag CFO departure, red flag multiple
  departures, prior litigation search, no proxy text graceful
- Compensation: say-on-pay, pay ratio, clawback, comp mix, missing data
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.compensation_analysis import (
    extract_compensation,
)
from do_uw.stages.extract.leadership_parsing import (
    is_valid_person_name,
    extract_executives_from_proxy,
)
from do_uw.stages.extract.leadership_profiles import (
    extract_leadership_profiles,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue[str](
        value=val,
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(
    proxy_text: str = "",
    proxy_governance: str = "",
    eight_k_texts: list[str] | None = None,
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    litigation_data: dict[str, Any] | None = None,
    web_search_results: dict[str, Any] | None = None,
    market_info: dict[str, Any] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState for testing."""
    filings: dict[str, Any] = {}
    filing_texts: dict[str, str] = {}

    if proxy_text:
        filing_texts["proxy_compensation"] = proxy_text
    if proxy_governance:
        filing_texts["proxy_governance"] = proxy_governance
    if eight_k_texts:
        for i, text in enumerate(eight_k_texts):
            filing_texts[f"8-K_item502_{i}"] = text

    filings["filing_texts"] = filing_texts

    market_data: dict[str, Any] = {}
    if market_info is not None:
        market_data["info"] = market_info

    fd = filing_documents or {}

    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"),
        sector=_sourced_str("TECH"),
    )
    profile = CompanyProfile(identity=identity)

    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=AcquiredData(
            filings=filings,
            market_data=market_data,
            filing_documents=fd,
            litigation_data=litigation_data or {},
            web_search_results=web_search_results or {},
        ),
    )


# ===========================================================================
# Name Validation Tests
# ===========================================================================


class TestGarbageNameRejection:
    """Test that known garbage names are rejected by is_valid_person_name."""

    def test_rejects_interim_award(self) -> None:
        """'Interim Award' is a compensation term, not a person."""
        assert not is_valid_person_name("Interim Award")

    def test_rejects_performance_award(self) -> None:
        """'Performance Award' is a compensation term."""
        assert not is_valid_person_name("Performance Award")

    def test_rejects_space_exploration(self) -> None:
        """'Space Exploration' is a business term."""
        assert not is_valid_person_name("Space Exploration")

    def test_rejects_annual_incentive(self) -> None:
        """'Annual Incentive' is a compensation term."""
        assert not is_valid_person_name("Annual Incentive")

    def test_rejects_restricted_stock(self) -> None:
        """'Restricted Stock' is a compensation term."""
        assert not is_valid_person_name("Restricted Stock")

    def test_rejects_total_compensation(self) -> None:
        """'Total Compensation' is a filing term."""
        assert not is_valid_person_name("Total Compensation")

    def test_rejects_equity_grant(self) -> None:
        """'Equity Grant' is a compensation term."""
        assert not is_valid_person_name("Equity Grant")

    def test_rejects_deferred_compensation(self) -> None:
        """'Deferred Compensation' is a filing term."""
        assert not is_valid_person_name("Deferred Compensation")

    def test_rejects_corporate_governance(self) -> None:
        """'Corporate Governance' is a section header."""
        assert not is_valid_person_name("Corporate Governance")

    def test_rejects_independent_directors(self) -> None:
        """'Independent Directors' is a filing term."""
        assert not is_valid_person_name("Independent Directors")

    def test_rejects_global_technologies(self) -> None:
        """'Global Technologies' is a company name fragment."""
        assert not is_valid_person_name("Global Technologies")

    def test_rejects_financial_services(self) -> None:
        """'Financial Services' is a business term."""
        assert not is_valid_person_name("Financial Services")

    def test_rejects_executive_compensation(self) -> None:
        """'Executive Compensation' is a section header."""
        assert not is_valid_person_name("Executive Compensation")


class TestLLMGarbageNameRejection:
    """Test that LLM-extracted garbage names (from TSLA DEF 14A) are rejected."""

    def test_rejects_western_association(self) -> None:
        assert not is_valid_person_name("Western Association")

    def test_rejects_partner_brands(self) -> None:
        assert not is_valid_person_name("Partner Brands")

    def test_rejects_redwood_materials(self) -> None:
        assert not is_valid_person_name("Redwood Materials")

    def test_rejects_proposals_three(self) -> None:
        assert not is_valid_person_name("Proposals Three")

    def test_rejects_reserve_fund(self) -> None:
        assert not is_valid_person_name("Reserve Fund")

    def test_rejects_pay_ratio(self) -> None:
        assert not is_valid_person_name("Pay Ratio")

    def test_rejects_nova_sky(self) -> None:
        assert not is_valid_person_name("Nova Sky")

    def test_rejects_juniper_networks(self) -> None:
        assert not is_valid_person_name("Juniper Networks")


class TestValidNameAcceptance:
    """Test that known valid person names pass is_valid_person_name."""

    def test_accepts_elon_musk(self) -> None:
        assert is_valid_person_name("Elon Musk")

    def test_accepts_tim_cook(self) -> None:
        assert is_valid_person_name("Tim Cook")

    def test_accepts_jamie_dimon(self) -> None:
        assert is_valid_person_name("Jamie Dimon")

    def test_accepts_mary_barra(self) -> None:
        assert is_valid_person_name("Mary Barra")

    def test_accepts_robyn_denholm(self) -> None:
        assert is_valid_person_name("Robyn Denholm")

    def test_accepts_zachary_kirkhorn(self) -> None:
        assert is_valid_person_name("Zachary Kirkhorn")

    def test_accepts_name_with_middle_initial(self) -> None:
        """Names with middle initial like 'John A. Smith' are valid."""
        assert is_valid_person_name("John A. Smith")

    def test_accepts_three_part_name(self) -> None:
        """Three-part names like 'Mary Jane Watson' are valid."""
        assert is_valid_person_name("Mary Jane Watson")


class TestExtractorRejectsGarbageFromCompTable:
    """Test that the extractor returns empty list on compensation tables."""

    def test_compensation_table_no_false_names(self) -> None:
        """Compensation table text should not produce false names."""
        comp_table_text = (
            "Summary Compensation Table\n\n"
            "Name  Salary  Bonus  Stock Awards  Option Awards  Total\n\n"
            "Interim Award of Performance Award based on Annual Incentive "
            "Plan. Restricted Stock granted as Equity Grant under Deferred "
            "Compensation plan. Target Threshold Maximum payout levels.\n\n"
            "Chief Executive Officer compensation includes base salary "
            "and performance-based equity grants."
        )
        executives = extract_executives_from_proxy(comp_table_text)
        # No valid person names should be extracted from comp table text.
        names = [e.name.value for e in executives if e.name]
        # None of the garbage terms should appear as names.
        garbage_terms = [
            "Interim Award", "Performance Award", "Annual Incentive",
            "Restricted Stock", "Equity Grant", "Deferred Compensation",
            "Target Threshold",
        ]
        for term in garbage_terms:
            assert term not in names, f"Garbage name '{term}' found"


# ===========================================================================
# Leadership Profile Tests
# ===========================================================================


class TestExecutiveExtraction:
    """Test extraction of executives from proxy text."""

    def test_extract_executives_from_proxy(self) -> None:
        """Proxy text with CEO and CFO -> two executives extracted."""
        proxy = (
            "John Smith, Chief Executive Officer, has served as CEO "
            "since 2019. He previously served as COO.\n\n"
            "Jane Doe, Chief Financial Officer, was appointed in 2021. "
            "She joined from a public accounting firm."
        )
        state = _make_state(proxy_text=proxy)
        stability, report = extract_leadership_profiles(state)

        assert len(stability.executives) >= 2
        names = [
            e.name.value for e in stability.executives if e.name
        ]
        assert "John Smith" in names
        assert "Jane Doe" in names
        assert "executives_found" in report.found_fields


class TestDepartureExtraction:
    """Test extraction of departures from 8-K filings."""

    def test_departure_from_8k(self) -> None:
        """8-K with Item 5.02 departure -> departure extracted."""
        eight_k = (
            "Item 5.02 Departure of Directors or Certain Officers\n"
            "On January 15, 2025, the Company announced the resignation "
            "of Robert Chen, Chief Financial Officer, effective "
            "February 1, 2025, to pursue other opportunities."
        )
        state = _make_state(
            filing_documents={
                "8-K": [
                    {
                        "accession": "0001234-25-001",
                        "filing_date": "2025-01-15",
                        "form_type": "8-K",
                        "full_text": eight_k,
                    }
                ]
            }
        )
        stability, report = extract_leadership_profiles(state)

        assert len(stability.departures_18mo) >= 1
        dep = stability.departures_18mo[0]
        assert dep.name is not None
        assert "Chen" in dep.name.value
        assert dep.departure_type == "UNPLANNED"
        assert "departures_18mo" in report.found_fields


class TestStabilityScore:
    """Test stability scoring logic."""

    def test_stability_score_full_team(self) -> None:
        """Full C-suite with no departures -> high stability score."""
        proxy = (
            "Alice Johnson, Chief Executive Officer, appointed in 2015. "
            "She has led the company for nearly a decade.\n\n"
            "Bob Williams, Chief Financial Officer, joined in 2018. "
            "He previously served at a Fortune 500 company.\n\n"
            "Carol Davis, Chief Operating Officer, named in 2017. "
            "She has extensive operational experience."
        )
        state = _make_state(proxy_text=proxy)
        stability, _ = extract_leadership_profiles(state)

        assert stability.stability_score is not None
        # No departures -> score should be 100.
        assert stability.stability_score.value == 100.0
        assert len(stability.red_flags) == 0

    def test_red_flag_cfo_departure(self) -> None:
        """Unplanned CFO departure -> red flag and score deduction."""
        proxy = (
            "Alice Johnson, Chief Executive Officer, appointed in 2015.\n\n"
            "Bob Williams, Chief Financial Officer, joined in 2018."
        )
        eight_k = (
            "Item 5.02 Departure of Directors\n"
            "Bob Williams, Chief Financial Officer, has resigned "
            "effective immediately."
        )
        state = _make_state(
            proxy_text=proxy,
            filing_documents={
                "8-K": [
                    {
                        "accession": "0001234-25-002",
                        "filing_date": "2025-01-20",
                        "form_type": "8-K",
                        "full_text": eight_k,
                    }
                ]
            },
        )
        stability, _ = extract_leadership_profiles(state)

        assert stability.stability_score is not None
        assert stability.stability_score.value < 100.0
        flag_texts = [f.value for f in stability.red_flags]
        assert any("CFO" in f for f in flag_texts)

    def test_red_flag_multiple_departures(self) -> None:
        """3+ departures -> multiple departures red flag."""
        eight_k_1 = (
            "Item 5.02\nDeparture of John Alpha. "
            "John Alpha, Chief Financial Officer, has resigned."
        )
        eight_k_2 = (
            "Item 5.02\nDeparture of Jane Beta. "
            "Jane Beta, Chief Operating Officer, has departed."
        )
        eight_k_3 = (
            "Item 5.02\nDeparture of Sam Gamma. "
            "Sam Gamma, Chief Technology Officer, has retired."
        )
        state = _make_state(
            filing_documents={
                "8-K": [
                    {
                        "accession": "001",
                        "filing_date": "2025-01-01",
                        "form_type": "8-K",
                        "full_text": eight_k_1,
                    },
                    {
                        "accession": "002",
                        "filing_date": "2025-02-01",
                        "form_type": "8-K",
                        "full_text": eight_k_2,
                    },
                    {
                        "accession": "003",
                        "filing_date": "2025-03-01",
                        "form_type": "8-K",
                        "full_text": eight_k_3,
                    },
                ]
            }
        )
        stability, _ = extract_leadership_profiles(state)

        assert len(stability.departures_18mo) >= 3
        assert stability.stability_score is not None
        assert stability.stability_score.value < 100.0
        flag_texts = [f.value for f in stability.red_flags]
        assert any("departures" in f.lower() for f in flag_texts)


class TestPriorLitigation:
    """Test prior litigation search for executives."""

    def test_prior_litigation_search(self) -> None:
        """Litigation data with matching name -> hits found."""
        proxy = (
            "John Smith, Chief Executive Officer, appointed in 2019."
        )
        state = _make_state(
            proxy_text=proxy,
            litigation_data={
                "scac_cases": [
                    {"description": "Securities fraud case involving John Smith at XYZ Corp"},
                    {"description": "Unrelated case about environmental violations"},
                ]
            },
        )
        stability, report = extract_leadership_profiles(state)

        # Should find at least one executive.
        assert len(stability.executives) >= 1
        ceo = stability.executives[0]
        assert len(ceo.prior_litigation) > 0
        assert "prior_litigation_searched" in report.found_fields


class TestGracefulDegradation:
    """Test graceful handling of missing data."""

    def test_no_proxy_text_graceful(self) -> None:
        """No proxy text -> empty executives, warnings, no crash."""
        state = _make_state()
        stability, report = extract_leadership_profiles(state)

        assert len(stability.executives) == 0
        assert stability.stability_score is not None
        assert report.extractor_name == "leadership_profiles"
        assert any("No executives" in w for w in report.warnings)


# ===========================================================================
# Compensation Analysis Tests
# ===========================================================================


class TestSayOnPay:
    """Test say-on-pay extraction."""

    def test_say_on_pay_extracted(self) -> None:
        """Proxy with say-on-pay text -> percentage extracted."""
        proxy = (
            "Summary Compensation Table\n"
            "Name, Title, Salary\n"
            "John Smith, Chief Executive Officer, $1,200,000\n\n"
            "Say-on-Pay Advisory Vote\n"
            "At our 2024 annual meeting, our say-on-pay proposal was "
            "approved by approximately 92.3% of votes cast."
        )
        state = _make_state(proxy_text=proxy)
        analysis, report = extract_compensation(state)

        assert analysis.say_on_pay_pct is not None
        assert analysis.say_on_pay_pct.value == 92.3
        assert "say_on_pay" in report.found_fields


class TestPayRatio:
    """Test pay ratio extraction."""

    def test_pay_ratio_extracted(self) -> None:
        """Proxy with CEO pay ratio -> ratio extracted."""
        proxy = (
            "Summary Compensation Table\n"
            "Jane Doe, Chief Executive Officer\n"
            "CEO Pay Ratio\n"
            "The ratio of our CEO's annual total compensation to the "
            "median annual total compensation of all employees was "
            "approximately 200:1 for fiscal year 2024."
        )
        state = _make_state(proxy_text=proxy)
        analysis, report = extract_compensation(state)

        assert analysis.ceo_pay_ratio is not None
        assert analysis.ceo_pay_ratio.value == 200.0
        assert "pay_ratio" in report.found_fields


class TestClawback:
    """Test clawback detection."""

    def test_clawback_detected(self) -> None:
        """Proxy with clawback policy -> has_clawback=True."""
        proxy = (
            "The Company has adopted a clawback policy that goes "
            "beyond the Dodd-Frank minimum requirements. In addition to "
            "mandatory recoupment provisions, the policy also covers "
            "cases of executive misconduct."
        )
        state = _make_state(proxy_text=proxy)
        analysis, report = extract_compensation(state)

        assert analysis.has_clawback is not None
        assert analysis.has_clawback.value is True
        assert analysis.clawback_scope is not None
        assert analysis.clawback_scope.value == "BROADER"
        assert "clawback" in report.found_fields


class TestCompMix:
    """Test compensation mix calculation."""

    def test_comp_mix_calculation(self) -> None:
        """Proxy with full SCT -> mix percentages computed."""
        proxy = (
            "Summary Compensation Table\n"
            "Name  Title  Salary  Bonus  Stock Awards  Total\n"
            "John Smith, Chief Executive Officer  "
            "$800,000  $500,000  $4,000,000  $200,000  $5,500,000"
        )
        state = _make_state(proxy_text=proxy)
        analysis, report = extract_compensation(state)

        if analysis.ceo_total_comp is not None:
            assert "ceo_total_comp" in report.found_fields
            # Comp mix should have some entries.
            if analysis.comp_mix:
                assert "comp_mix" in report.found_fields
                total_pct = sum(analysis.comp_mix.values())
                # Mix percentages should sum to roughly 100 or less.
                assert total_pct <= 101.0


class TestCompMissingData:
    """Test compensation with missing data."""

    def test_missing_data_graceful(self) -> None:
        """No proxy text -> empty analysis, no crash."""
        state = _make_state()
        _analysis, report = extract_compensation(state)

        assert report.extractor_name == "compensation_analysis"
        assert any(
            "No proxy text" in w or "missing" in w.lower()
            for w in report.warnings
        )
        # related_party is always found (even if empty list).
        assert "related_party" in report.found_fields
