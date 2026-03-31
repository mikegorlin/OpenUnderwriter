"""Tests for unified litigation classifier (Phase 140, LIT-01 through LIT-05).

Covers:
- TestUnifiedClassification (LIT-01): Legal theory detection + classification
- TestUniversalDedup (LIT-02): Cross-list deduplication with source merging
- TestYearDisambiguation (LIT-03): Year suffix on case names
- TestCoverageSideClassification (LIT-04): Coverage type from theories + defendants
- TestMissingFieldRecovery (LIT-05): Missing critical field flagging
- TestBoilerplateFilter (D-07): Boilerplate reserve separation
"""

from __future__ import annotations

from datetime import date, datetime, UTC

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    CoverageType,
    LegalTheory,
    LitigationLandscape,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv(value: str, source: str = "test", confidence: Confidence = Confidence.MEDIUM) -> SourcedValue[str]:
    return SourcedValue[str](value=value, source=source, confidence=confidence, as_of=datetime.now(tz=UTC))


def _sv_date(value: date, source: str = "test", confidence: Confidence = Confidence.MEDIUM) -> SourcedValue[date]:
    return SourcedValue[date](value=value, source=source, confidence=confidence, as_of=datetime.now(tz=UTC))


def _make_case(
    name: str = "Test Case",
    allegations: list[str] | None = None,
    theories: list[str] | None = None,
    defendants: list[str] | None = None,
    filing_date: date | None = None,
    court: str | None = None,
    case_number: str | None = None,
    settlement_amount: float | None = None,
    source: str = "test",
    confidence: Confidence = Confidence.MEDIUM,
) -> CaseDetail:
    case = CaseDetail(
        case_name=_sv(name, source, confidence),
    )
    if allegations:
        case.allegations = [_sv(a, source, confidence) for a in allegations]
    if theories:
        case.legal_theories = [_sv(t, source, confidence) for t in theories]
    if defendants:
        case.named_defendants = [_sv(d, source, confidence) for d in defendants]
    if filing_date:
        case.filing_date = _sv_date(filing_date, source, confidence)
    if court:
        case.court = _sv(court, source, confidence)
    if case_number:
        case.case_number = _sv(case_number, source, confidence)
    if settlement_amount is not None:
        case.settlement_amount = SourcedValue[float](
            value=settlement_amount, source=source, confidence=confidence, as_of=datetime.now(tz=UTC)
        )
    return case


# ---------------------------------------------------------------------------
# LIT-01: Unified Classification
# ---------------------------------------------------------------------------


class TestUnifiedClassification:
    """classify_all_cases sets legal_theories from text evidence."""

    def test_10b5_in_allegations_gets_rule_10b5(self) -> None:
        case = _make_case(
            name="In re Acme Securities Litigation",
            allegations=["Violated Rule 10b-5 of the Securities Exchange Act"],
            defendants=["CEO Smith"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        theory_values = {t.value for t in case.legal_theories}
        assert LegalTheory.RULE_10B5.value in theory_values
        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_A.value

    def test_fiduciary_duty_derivative_gets_derivative_duty(self) -> None:
        case = _make_case(
            name="Smith v. Jones",
            allegations=["breach of fiduciary duty", "derivative action"],
            defendants=["John Jones"],
        )
        landscape = LitigationLandscape(derivative_suits=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        theory_values = {t.value for t in case.legal_theories}
        assert LegalTheory.DERIVATIVE_DUTY.value in theory_values
        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.DERIVATIVE_SIDE_A.value

    def test_fiduciary_duty_no_defendants_gets_side_b(self) -> None:
        case = _make_case(
            name="Smith v. Acme Corp",
            allegations=["breach of fiduciary duty", "derivative"],
        )
        landscape = LitigationLandscape(derivative_suits=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        theory_values = {t.value for t in case.legal_theories}
        assert LegalTheory.DERIVATIVE_DUTY.value in theory_values
        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.DERIVATIVE_SIDE_B.value

    def test_fcpa_gets_sec_enforcement(self) -> None:
        case = _make_case(
            name="SEC v. Acme Corp",
            allegations=["FCPA violations"],
            defendants=["CEO Smith"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        theory_values = {t.value for t in case.legal_theories}
        assert LegalTheory.FCPA.value in theory_values
        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SEC_ENFORCEMENT_A.value

    def test_section_11_gets_side_c(self) -> None:
        case = _make_case(
            name="In re IPO Securities Litigation",
            allegations=["Section 11 of the Securities Act"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_C.value

    def test_section_14a_gets_side_b(self) -> None:
        case = _make_case(
            name="Proxy Statement Litigation",
            allegations=["Section 14(a) proxy fraud"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_B.value

    def test_higher_confidence_preserved(self) -> None:
        """Pitfall 3: Existing HIGH confidence classification not overwritten by MEDIUM."""
        case = _make_case(
            name="In re Test Securities Litigation",
            allegations=["10b-5 fraud"],
        )
        # Pre-set with HIGH confidence classification
        case.legal_theories = [_sv(LegalTheory.RULE_10B5.value, "SCAC", Confidence.HIGH)]
        case.coverage_type = _sv(CoverageType.SCA_SIDE_A.value, "SCAC", Confidence.HIGH)
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        # Should still have the HIGH confidence source
        assert any(t.confidence == Confidence.HIGH for t in case.legal_theories)


# ---------------------------------------------------------------------------
# LIT-02: Universal Dedup
# ---------------------------------------------------------------------------


class TestUniversalDedup:
    """deduplicate_all_cases consolidates similar cases across lists."""

    def test_same_name_same_year_consolidated(self) -> None:
        case1 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2020, 3, 15),
            court="S.D.N.Y.",
            source="EFTS",
        )
        case2 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2020, 6, 1),
            case_number="1:20-cv-1234",
            source="10-K",
        )
        landscape = LitigationLandscape(securities_class_actions=[case1, case2])

        from do_uw.stages.extract.litigation_classifier import deduplicate_all_cases
        deduplicate_all_cases(landscape)

        # Should be consolidated to 1
        total = len(landscape.securities_class_actions) + len(landscape.derivative_suits)
        assert total == 1

    def test_same_name_different_years_kept_separate(self) -> None:
        case1 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2018, 3, 15),
        )
        case2 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2022, 6, 1),
        )
        landscape = LitigationLandscape(securities_class_actions=[case1, case2])

        from do_uw.stages.extract.litigation_classifier import deduplicate_all_cases
        deduplicate_all_cases(landscape)

        total = len(landscape.securities_class_actions) + len(landscape.derivative_suits)
        assert total == 2

    def test_cross_list_dedup(self) -> None:
        """Same case in SCA and derivative lists gets consolidated."""
        case1 = _make_case(
            name="Smith v. Acme Corp Breach of Duty",
            filing_date=date(2021, 5, 1),
            source="EFTS",
        )
        case2 = _make_case(
            name="Smith v. Acme Corp Breach of Duty",
            filing_date=date(2021, 5, 1),
            case_number="1:21-cv-5678",
            source="10-K",
        )
        landscape = LitigationLandscape(
            securities_class_actions=[case1],
            derivative_suits=[case2],
        )

        from do_uw.stages.extract.litigation_classifier import deduplicate_all_cases
        deduplicate_all_cases(landscape)

        total = len(landscape.securities_class_actions) + len(landscape.derivative_suits)
        assert total == 1

    def test_consolidated_entry_merges_sources(self) -> None:
        case1 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2020, 3, 15),
            court="S.D.N.Y.",
            source="EFTS",
            confidence=Confidence.HIGH,
        )
        case2 = _make_case(
            name="In re Acme Corp Securities Litigation",
            filing_date=date(2020, 6, 1),
            case_number="1:20-cv-1234",
            source="10-K",
            confidence=Confidence.MEDIUM,
        )
        landscape = LitigationLandscape(securities_class_actions=[case1, case2])

        from do_uw.stages.extract.litigation_classifier import deduplicate_all_cases
        deduplicate_all_cases(landscape)

        # Consolidated entry should have case_number from case2
        remaining = landscape.securities_class_actions + landscape.derivative_suits
        assert len(remaining) == 1
        assert remaining[0].case_number is not None

    def test_highest_confidence_wins(self) -> None:
        """D-04: Highest-confidence source wins per field."""
        case1 = _make_case(
            name="In re Test Litigation",
            court="N.D. Cal.",
            filing_date=date(2020, 3, 15),
            source="web",
            confidence=Confidence.LOW,
        )
        case2 = _make_case(
            name="In re Test Litigation",
            court="S.D.N.Y.",
            filing_date=date(2020, 6, 1),
            source="EFTS",
            confidence=Confidence.HIGH,
        )
        landscape = LitigationLandscape(securities_class_actions=[case1, case2])

        from do_uw.stages.extract.litigation_classifier import deduplicate_all_cases
        deduplicate_all_cases(landscape)

        remaining = landscape.securities_class_actions + landscape.derivative_suits
        assert len(remaining) == 1
        # HIGH confidence court should win
        assert remaining[0].court is not None
        assert remaining[0].court.confidence == Confidence.HIGH


# ---------------------------------------------------------------------------
# LIT-03: Year Disambiguation
# ---------------------------------------------------------------------------


class TestYearDisambiguation:
    """disambiguate_by_year appends year suffix to case names."""

    def test_year_appended_from_filing_date(self) -> None:
        case = _make_case(
            name="In re Fastly Securities Litigation",
            filing_date=date(2020, 10, 15),
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import disambiguate_by_year
        disambiguate_by_year(landscape)

        assert case.case_name is not None
        assert case.case_name.value == "In re Fastly Securities Litigation (2020)"

    def test_already_suffixed_not_doubled(self) -> None:
        case = _make_case(
            name="In re Fastly (2020)",
            filing_date=date(2020, 10, 15),
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import disambiguate_by_year
        disambiguate_by_year(landscape)

        assert case.case_name is not None
        assert case.case_name.value == "In re Fastly (2020)"

    def test_no_filing_date_no_suffix(self) -> None:
        case = _make_case(name="Unknown Case")
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import disambiguate_by_year
        disambiguate_by_year(landscape)

        assert case.case_name is not None
        assert case.case_name.value == "Unknown Case"


# ---------------------------------------------------------------------------
# LIT-04: Coverage Side Classification
# ---------------------------------------------------------------------------


class TestCoverageSideClassification:
    """Coverage type derived from theories + defendants."""

    def test_10b5_with_defendants_side_a(self) -> None:
        case = _make_case(
            name="Test Case",
            allegations=["Rule 10b-5 fraud"],
            defendants=["CEO John"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_A.value

    def test_section_11_always_side_c(self) -> None:
        case = _make_case(
            name="Test Case",
            allegations=["Section 11 violation"],
            defendants=["CEO John"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_C.value

    def test_derivative_no_defendants_side_b(self) -> None:
        case = _make_case(
            name="Test Derivative",
            allegations=["breach of fiduciary duty", "derivative"],
        )
        landscape = LitigationLandscape(derivative_suits=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.DERIVATIVE_SIDE_B.value

    def test_environmental_regulatory_entity(self) -> None:
        case = _make_case(
            name="EPA v. Acme Corp",
            allegations=["environmental violations", "CERCLA cleanup"],
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.REGULATORY_ENTITY.value


# ---------------------------------------------------------------------------
# LIT-05: Missing Field Recovery
# ---------------------------------------------------------------------------


class TestMissingFieldRecovery:
    """flag_missing_fields populates cases_needing_recovery."""

    def test_missing_court_and_case_number_flagged(self) -> None:
        case = _make_case(
            name="In re Test Litigation",
            filing_date=date(2021, 1, 1),
            # No court, no case_number
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import flag_missing_fields
        flag_missing_fields(landscape)

        assert len(landscape.cases_needing_recovery) >= 1
        recovery = landscape.cases_needing_recovery[0]
        assert "court" in recovery["missing_fields"]
        assert "case_number" in recovery["missing_fields"]

    def test_fully_populated_not_flagged(self) -> None:
        case = _make_case(
            name="In re Complete Case",
            filing_date=date(2021, 1, 1),
            court="S.D.N.Y.",
            case_number="1:21-cv-1234",
            defendants=["CEO"],
        )
        case.class_period_start = _sv_date(date(2020, 1, 1))
        case.class_period_end = _sv_date(date(2021, 1, 1))
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import flag_missing_fields
        flag_missing_fields(landscape)

        assert len(landscape.cases_needing_recovery) == 0


# ---------------------------------------------------------------------------
# D-07: Boilerplate Filter
# ---------------------------------------------------------------------------


class TestBoilerplateFilter:
    """Boilerplate reserves separated from classified cases."""

    def test_routine_litigation_to_unclassified(self) -> None:
        case = _make_case(name="routine litigation matters")
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        assert len(landscape.securities_class_actions) == 0
        assert len(landscape.unclassified_reserves) == 1

    def test_generic_name_with_detail_fields_not_filtered(self) -> None:
        """Pitfall 5: Case with generic name but populated detail fields stays."""
        case = _make_case(
            name="legal proceedings",
            court="S.D.N.Y.",
            filing_date=date(2021, 6, 15),
        )
        landscape = LitigationLandscape(securities_class_actions=[case])

        from do_uw.stages.extract.litigation_classifier import classify_all_cases
        classify_all_cases(landscape)

        # Should NOT be filtered because it has detail fields (court, filing_date)
        assert len(landscape.securities_class_actions) == 1
        assert len(landscape.unclassified_reserves) == 0
