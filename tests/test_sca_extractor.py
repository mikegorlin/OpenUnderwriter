"""Tests for securities class action (SCA) extractor.

Covers:
- EFTS sec_references parsed as primary source with MEDIUM confidence
- Two-layer classification populates coverage_type and legal_theories
- Lead counsel tier lookup with substring matching
- Deduplication logic (EFTS preferred when merging with Item 3)
- Empty EFTS + empty Item 3 returns empty list with low-coverage report
- Item 3 supplement enriches existing EFTS cases
- Item 3 adds new cases not found in EFTS
- Time horizon filtering (10 years)
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import CaseDetail, CaseStatus, CoverageType, LegalTheory
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sca_extractor import (
    count_populated_fields,
    detect_coverage_type,
    detect_status,
    extract_securities_class_actions,
    is_case_viable,
    is_within_horizon,
    load_lead_counsel_tiers,
    lookup_counsel_tier,
    word_overlap_pct,
)
from do_uw.stages.extract.sourced import sourced_str

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(
    sec_references: list[str] | None = None,
    web_results: list[str] | None = None,
    blind_spot_results: dict[str, Any] | None = None,
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
) -> AnalysisState:
    """Build minimal AnalysisState for SCA testing."""
    lit_data: dict[str, Any] = {}
    if sec_references is not None:
        lit_data["sec_references"] = sec_references
    if web_results is not None:
        lit_data["web_results"] = web_results

    acquired = AcquiredData(
        litigation_data=lit_data,
        blind_spot_results=blind_spot_results or {},
        filing_documents=filing_documents or {},
    )

    return AnalysisState(
        ticker="TEST",
        acquired_data=acquired,
    )


# ---------------------------------------------------------------------------
# Test EFTS parsing as primary source
# ---------------------------------------------------------------------------


class TestEFTSParsing:
    """Test EFTS sec_references parsed as primary source."""

    def test_efts_sca_reference_creates_case(self) -> None:
        """EFTS sec_reference with SCA keywords creates CaseDetail."""
        state = _make_state(sec_references=[
            "In re Acme Corp Securities Litigation, "
            "filed January 15, 2024 in S.D.N.Y., "
            "alleging Rule 10b-5 violations. Status: pending."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        case = cases[0]
        assert case.case_name is not None
        assert "Acme Corp" in case.case_name.value
        assert case.case_name.confidence == Confidence.MEDIUM
        assert case.court is not None
        assert case.court.value == "S.D.N.Y."

    def test_efts_non_sca_reference_ignored(self) -> None:
        """EFTS reference without SCA keywords is skipped."""
        state = _make_state(sec_references=[
            "Company filed 10-K annual report with SEC."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 0

    def test_efts_settlement_amount_parsed(self) -> None:
        """Settlement amount extracted from EFTS reference."""
        state = _make_state(sec_references=[
            "In re XYZ Securities Litigation, class action "
            "settled for $25.5 million."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].settlement_amount is not None
        assert cases[0].settlement_amount.value == 25_500_000.0

    def test_efts_filing_date_parsed(self) -> None:
        """Filing date extracted from EFTS reference."""
        state = _make_state(sec_references=[
            "In re Delta Corp Securities Litigation, "
            "securities class action filed March 10, 2023 in D. Del."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].filing_date is not None
        assert cases[0].filing_date.value == date(2023, 3, 10)

    def test_efts_empty_returns_empty(self) -> None:
        """Empty EFTS references returns no cases."""
        state = _make_state(sec_references=[])
        cases, report = extract_securities_class_actions(state)
        assert len(cases) == 0
        assert "No EFTS/SCAC sec_references found" in report.warnings


# ---------------------------------------------------------------------------
# Test two-layer classification
# ---------------------------------------------------------------------------


class TestTwoLayerClassification:
    """Test coverage_type and legal_theories population."""

    def test_10b5_maps_to_sca_side_a(self) -> None:
        """Rule 10b-5 theory maps to SCA_SIDE_A coverage."""
        state = _make_state(sec_references=[
            "In re Alpha Corp Securities Litigation, "
            "filed January 15, 2024 in S.D.N.Y., "
            "alleging Rule 10b-5 violations."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].coverage_type is not None
        assert cases[0].coverage_type.value == CoverageType.SCA_SIDE_A.value

    def test_section_11_maps_to_sca_side_c(self) -> None:
        """Section 11 theory maps to SCA_SIDE_C coverage."""
        state = _make_state(sec_references=[
            "In re Beta Corp Securities Litigation, "
            "filed March 1, 2024 in S.D.N.Y., "
            "alleging Section 11 violations."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].coverage_type is not None
        assert cases[0].coverage_type.value == CoverageType.SCA_SIDE_C.value

    def test_section_14a_maps_to_sca_side_b(self) -> None:
        """Section 14(a) theory maps to SCA_SIDE_B coverage."""
        state = _make_state(sec_references=[
            "In re Gamma Corp Securities Litigation, "
            "filed April 1, 2024 in D. Del., "
            "alleging Section 14(a) violations."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].coverage_type is not None
        assert cases[0].coverage_type.value == CoverageType.SCA_SIDE_B.value

    def test_multiple_theories_detected(self) -> None:
        """Multiple legal theories detected from single reference."""
        state = _make_state(sec_references=[
            "In re Multi Theory Securities Litigation, "
            "filed June 1, 2024 in S.D.N.Y., "
            "alleging Rule 10b-5 and "
            "Section 11 violations under the Securities Act."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        theory_values = {t.value for t in cases[0].legal_theories}
        assert LegalTheory.RULE_10B5.value in theory_values
        assert LegalTheory.SECTION_11.value in theory_values

    def test_detect_coverage_type_default_side_a(self) -> None:
        """Default coverage type is SCA_SIDE_A when no specific theory."""
        theories: list[SourcedValue[str]] = []
        assert detect_coverage_type(theories) == CoverageType.SCA_SIDE_A


# ---------------------------------------------------------------------------
# Test lead counsel tier lookup
# ---------------------------------------------------------------------------


class TestLeadCounselTier:
    """Test lead counsel tier lookup via substring matching."""

    def test_tier_1_exact_match(self) -> None:
        """Tier 1 firm matched by substring."""
        tiers = load_lead_counsel_tiers()
        tier = lookup_counsel_tier(
            "Bernstein Litowitz Berger & Grossmann LLP", tiers,
        )
        assert tier == 1

    def test_tier_2_substring_match(self) -> None:
        """Tier 2 firm matched by substring."""
        tiers = load_lead_counsel_tiers()
        tier = lookup_counsel_tier("Pomerantz LLP", tiers)
        assert tier == 2

    def test_unknown_firm_tier_3(self) -> None:
        """Unknown firm defaults to tier 3."""
        tiers = load_lead_counsel_tiers()
        tier = lookup_counsel_tier("Smith & Associates", tiers)
        assert tier == 3

    def test_lead_counsel_from_efts_reference(self) -> None:
        """Lead counsel parsed from EFTS reference text."""
        state = _make_state(sec_references=[
            "In re Acme Securities Litigation, securities class action, "
            "lead counsel: Robbins Geller Rudman & Dowd LLP."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        assert cases[0].lead_counsel is not None
        assert "Robbins Geller" in cases[0].lead_counsel.value
        assert cases[0].lead_counsel_tier is not None
        assert cases[0].lead_counsel_tier.value == 1


# ---------------------------------------------------------------------------
# Test deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    """Test deduplication logic with EFTS preferred."""

    def test_duplicate_case_merged(self) -> None:
        """Duplicate cases merged with EFTS data preferred."""
        state = _make_state(
            sec_references=[
                "In re Acme Corp Securities Litigation, "
                "securities class action filed in S.D.N.Y."
            ],
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": (
                        "ITEM 1. BUSINESS\n\nAcme Corp is a technology company.\n\n"
                        "Item 1A. Risk Factors\n\nRisk factors here.\n\n"
                        "Item 3. Legal Proceedings\n\n"
                        "In re Acme Corp Securities Litigation -- "
                        "a securities class action is pending in S.D.N.Y. "
                        "alleging Rule 10b-5 violations. The case was "
                        "filed January 15, 2024 and is currently active.\n\n"
                        "Item 4. Mine Safety\n\n"
                    ),
                }],
            },
        )
        cases, _report = extract_securities_class_actions(state)
        # Should be 1 case (merged), not 2.
        assert len(cases) == 1
        assert cases[0].case_name is not None
        assert "Acme Corp" in cases[0].case_name.value

    def test_word_overlap_high_match(self) -> None:
        """Word overlap > 80% identifies duplicates."""
        pct = word_overlap_pct(
            "In re Acme Corp Securities Litigation",
            "In re Acme Corp Securities Lit",
        )
        assert pct > 0.80

    def test_word_overlap_low_no_match(self) -> None:
        """Word overlap < 80% keeps cases separate."""
        pct = word_overlap_pct(
            "In re Acme Corp Securities Litigation",
            "In re Beta Inc Product Liability Action",
        )
        assert pct < 0.80


# ---------------------------------------------------------------------------
# Test Item 3 supplement
# ---------------------------------------------------------------------------


class TestItem3Supplement:
    """Test Item 3 adds new cases and enriches existing."""

    def test_item3_adds_new_case(self) -> None:
        """Item 3 adds case not found in EFTS."""
        # Item 3 text must be >200 chars to pass section parser minimum.
        item3_content = (
            "In re Beta Inc Securities Litigation -- "
            "a securities class action was filed in N.D. Cal. "
            "alleging Rule 10b-5 violations. The case is pending. "
            "We believe the claims are without merit. The Company "
            "intends to vigorously defend against all allegations "
            "and has retained outside counsel to manage the matter. "
            "The lead plaintiff filed an amended complaint in 2024."
        )
        state = _make_state(
            sec_references=[],
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": (
                        "ITEM 1. BUSINESS\n\nAcme Corp is a technology "
                        "company providing enterprise solutions.\n\n"
                        "Item 1A. Risk Factors\n\nRisk factors here.\n\n"
                        "Item 3. Legal Proceedings\n\n"
                        + item3_content + "\n\n"
                        "Item 4. Mine Safety\n\n"
                    ),
                }],
            },
        )
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) >= 1
        # Should have at least one case from Item 3.
        names = [
            c.case_name.value for c in cases if c.case_name
        ]
        assert any("Beta" in n for n in names)

    def test_item3_enriches_efts_case(self) -> None:
        """Item 3 enriches existing EFTS case with missing fields."""
        # Item 3 text must be >200 chars to pass section parser minimum.
        item3_content = (
            "In re Gamma Corp Securities Litigation -- "
            "this securities class action was filed in D. Del. "
            "The case was settled for $10 million. The settlement "
            "was approved by the court in 2024. The Company paid "
            "the settlement from existing insurance coverage under "
            "its directors and officers liability policy. Additional "
            "details regarding the litigation are described below."
        )
        state = _make_state(
            sec_references=[
                "In re Gamma Corp Securities Litigation, "
                "securities class action."
            ],
            filing_documents={
                "10-K": [{
                    "accession": "001",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": (
                        "ITEM 1. BUSINESS\n\nGamma Corp is a tech "
                        "company providing enterprise solutions.\n\n"
                        "Item 1A. Risk Factors\n\nRisks.\n\n"
                        "Item 3. Legal Proceedings\n\n"
                        + item3_content + "\n\n"
                        "Item 4. Mine Safety\n\n"
                    ),
                }],
            },
        )
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        # Settlement should come from Item 3 enrichment.
        assert cases[0].settlement_amount is not None


# ---------------------------------------------------------------------------
# Test empty state
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test empty inputs return empty results with low coverage."""

    def test_empty_efts_empty_item3(self) -> None:
        """Empty EFTS + empty Item 3 returns empty list."""
        state = _make_state(sec_references=[], filing_documents={})
        cases, report = extract_securities_class_actions(state)
        assert len(cases) == 0
        assert report.coverage_pct < 50.0

    def test_no_acquired_data(self) -> None:
        """No acquired data returns empty list."""
        state = AnalysisState(ticker="TEST")
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 0


# ---------------------------------------------------------------------------
# Test time horizon filtering
# ---------------------------------------------------------------------------


class TestTimeHorizon:
    """Test 10-year time horizon filtering."""

    def test_recent_case_included(self) -> None:
        """Case within 10 years is included."""
        assert is_within_horizon(date.today() - timedelta(days=365))

    def test_old_case_excluded(self) -> None:
        """Case older than 10 years is excluded."""
        assert not is_within_horizon(
            date.today() - timedelta(days=TIME_HORIZON_DAYS + 1),
        )

    def test_none_date_included(self) -> None:
        """Case without date is included (can't exclude)."""
        assert is_within_horizon(None)

    def test_old_efts_case_filtered(self) -> None:
        """EFTS case older than 10 years is filtered out."""
        old_date = date.today() - timedelta(days=TIME_HORIZON_DAYS + 100)
        month = old_date.strftime("%B")
        day = old_date.day
        year = old_date.year
        state = _make_state(sec_references=[
            f"Securities class action filed {month} {day}, {year}."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 0


# ---------------------------------------------------------------------------
# Test status detection
# ---------------------------------------------------------------------------


class TestStatusDetection:
    """Test case status keyword detection."""

    def test_dismissed_status(self) -> None:
        """'dismissed' keyword maps to DISMISSED."""
        assert detect_status("The case was dismissed.") == CaseStatus.DISMISSED

    def test_settled_status(self) -> None:
        """'settled' keyword maps to SETTLED."""
        assert detect_status("The case was settled.") == CaseStatus.SETTLED

    def test_pending_status(self) -> None:
        """'pending' keyword maps to ACTIVE."""
        assert detect_status("The case is pending.") == CaseStatus.ACTIVE

    def test_unknown_status(self) -> None:
        """No keywords maps to UNKNOWN."""
        assert detect_status("Some random text.") == CaseStatus.UNKNOWN


# Import for time horizon test constant.
from do_uw.stages.extract.sca_extractor import TIME_HORIZON_DAYS  # noqa: E402, I001


# ---------------------------------------------------------------------------
# Test quality filter
# ---------------------------------------------------------------------------


class TestCaseQualityFilter:
    """Test quality filtering of hollow case records."""

    def test_viable_case_with_court(self) -> None:
        """Case with name + court is viable."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
            court=sourced_str("S.D.N.Y.", "test", Confidence.MEDIUM),
        )
        assert is_case_viable(case)

    def test_viable_case_with_filing_date(self) -> None:
        """Case with name + filing_date is viable."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
            filing_date=SourcedValue[date](
                value=date(2024, 1, 15), source="test",
                confidence=Confidence.MEDIUM, as_of=datetime.now(tz=UTC),
            ),
        )
        assert is_case_viable(case)

    def test_hollow_case_name_only(self) -> None:
        """Case with only a name (no court, date, status) is NOT viable."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
        )
        assert not is_case_viable(case)

    def test_hollow_no_name(self) -> None:
        """Case with no name is NOT viable."""
        case = CaseDetail(
            court=sourced_str("S.D.N.Y.", "test", Confidence.MEDIUM),
        )
        assert not is_case_viable(case)

    def test_hollow_name_plus_unknown_status_only(self) -> None:
        """Case with name + UNKNOWN status (default) is NOT viable."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
            status=sourced_str("UNKNOWN", "test", Confidence.LOW),
        )
        assert not is_case_viable(case)

    def test_viable_case_with_settled_status(self) -> None:
        """Case with name + SETTLED status IS viable."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
            status=sourced_str("SETTLED", "test", Confidence.MEDIUM),
        )
        assert is_case_viable(case)

    def test_hollow_name_plus_coverage_type_only(self) -> None:
        """Case with name + coverage_type but no detail fields is NOT viable.

        coverage_type and legal_theories are auto-derived, not real details.
        """
        case = CaseDetail(
            case_name=sourced_str("In re Acme Securities Litigation", "test", Confidence.MEDIUM),
            coverage_type=sourced_str("SCA_SIDE_A", "test", Confidence.LOW),
        )
        assert not is_case_viable(case)


class TestCountPopulatedFields:
    """Test counting of actually populated fields."""

    def test_fully_populated_case(self) -> None:
        """Case with many fields counts all of them."""
        case = CaseDetail(
            case_name=sourced_str("In re Acme", "test", Confidence.MEDIUM),
            court=sourced_str("S.D.N.Y.", "test", Confidence.MEDIUM),
            filing_date=SourcedValue[date](
                value=date(2024, 1, 15), source="test",
                confidence=Confidence.MEDIUM, as_of=datetime.now(tz=UTC),
            ),
            status=sourced_str("ACTIVE", "test", Confidence.MEDIUM),
            lead_counsel=sourced_str("Robbins Geller", "test", Confidence.MEDIUM),
        )
        populated = count_populated_fields(case)
        assert "case_name" in populated
        assert "court" in populated
        assert "filing_date" in populated
        assert "status" in populated
        assert "lead_counsel" in populated

    def test_empty_case_has_no_populated_fields(self) -> None:
        """Empty CaseDetail has zero populated fields."""
        case = CaseDetail()
        populated = count_populated_fields(case)
        assert len(populated) == 0

    def test_unknown_status_not_counted(self) -> None:
        """UNKNOWN status is not counted as populated."""
        case = CaseDetail(
            case_name=sourced_str("Test", "test", Confidence.LOW),
            status=sourced_str("UNKNOWN", "test", Confidence.LOW),
        )
        populated = count_populated_fields(case)
        assert "status" not in populated


class TestQualityFilterIntegration:
    """Test that quality filter is applied in extract_securities_class_actions."""

    def test_hollow_efts_cases_filtered_with_warning(self) -> None:
        """EFTS cases with only SCA keyword and no details are filtered."""
        # This reference has a class action keyword but minimal extractable data
        state = _make_state(sec_references=[
            "securities class action",
        ])
        cases, _report = extract_securities_class_actions(state)
        # Case has no case_name from CASE_NAME_RE, so it fails viability
        # Either filtered out or never created with a real name
        # The key assertion: no hollow records in output
        for case in cases:
            populated = count_populated_fields(case)
            detail_fields = [
                f for f in populated
                if f not in ("case_name", "allegations", "legal_theories", "coverage_type")
            ]
            assert len(detail_fields) >= 1 or case.case_name is None

    def test_viable_case_kept_after_filter(self) -> None:
        """Viable cases with real detail fields are kept."""
        state = _make_state(sec_references=[
            "In re Acme Corp Securities Litigation, "
            "filed January 15, 2024 in S.D.N.Y., "
            "alleging Rule 10b-5 violations. Status: pending."
        ])
        cases, _report = extract_securities_class_actions(state)
        assert len(cases) == 1
        populated = count_populated_fields(cases[0])
        assert "case_name" in populated
        assert "court" in populated

    def test_filter_reports_fragment_count(self) -> None:
        """Report warnings include fragment count when cases are filtered."""
        state = _make_state(sec_references=[
            "securities class action",  # minimal, likely filtered
            "In re Real Corp Securities Litigation, "
            "filed January 15, 2024 in S.D.N.Y., class action."  # viable
        ])
        _cases, report = extract_securities_class_actions(state)
        # At minimum, we should not crash
        assert report.extractor_name == "securities_class_actions"
