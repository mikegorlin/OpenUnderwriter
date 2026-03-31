"""Tests for false SCA classification filtering across all 3 layers.

Validates that boilerplate 10-K litigation language does NOT trigger
CRF-1 (Active SCA) red flag, while real SCAs with specifics DO trigger.
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.signal_mappers_ext import _is_boilerplate_litigation


# ---------------------------------------------------------------------------
# Layer 2: Boilerplate pattern matching (_is_boilerplate_litigation)
# ---------------------------------------------------------------------------


class TestBoilerplatePatterns:
    """Tests for _is_boilerplate_litigation() pattern matching."""

    def test_boilerplate_ordinary_course(self) -> None:
        """Classic boilerplate: 'ordinary course of business'."""
        text = "Company is subject to various legal proceedings in the ordinary course of business"
        assert _is_boilerplate_litigation(text.upper())

    def test_boilerplate_party_to_legal_matters(self) -> None:
        """Boilerplate variant: 'party to legal matters arising'."""
        text = "Company is party to legal matters arising in the ordinary course"
        assert _is_boilerplate_litigation(text.upper())

    def test_boilerplate_involved_in_certain_legal(self) -> None:
        """Boilerplate variant: 'involved in certain legal proceedings'."""
        text = "involved in certain legal proceedings and claims"
        assert _is_boilerplate_litigation(text.upper())

    def test_boilerplate_subject_to_various_legal(self) -> None:
        """Boilerplate: 'subject to various legal proceedings'."""
        text = "The Company is subject to various legal proceedings"
        assert _is_boilerplate_litigation(text.upper())

    def test_boilerplate_normal_course(self) -> None:
        """Boilerplate: 'normal course of business'."""
        text = "Litigation arising in the normal course of business"
        assert _is_boilerplate_litigation(text.upper())

    def test_boilerplate_subject_to_claims(self) -> None:
        """Boilerplate: 'subject to claims'."""
        text = "The company is subject to claims and lawsuits"
        assert _is_boilerplate_litigation(text.upper())

    def test_real_sca_not_boilerplate(self) -> None:
        """Real SCA with named plaintiff is NOT boilerplate."""
        text = "Smith v. Company Inc., Case No. 1:24-cv-01234, S.D.N.Y."
        assert not _is_boilerplate_litigation(text.upper())

    def test_real_sca_in_re_not_boilerplate(self) -> None:
        """Real SCA 'In re' case is NOT boilerplate."""
        text = "In re Acme Corp Securities Litigation"
        assert not _is_boilerplate_litigation(text.upper())


# ---------------------------------------------------------------------------
# Layer 3: Case specificity gate
# ---------------------------------------------------------------------------


class TestCaseSpecificityGate:
    """Tests for _has_case_specificity() check."""

    def test_case_with_named_plaintiff_passes(self) -> None:
        """Case with ' v. ' in name has specificity."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity

        case = _make_mock_case(case_name="Smith v. Acme Corp")
        assert _has_case_specificity(case)

    def test_case_with_court_passes(self) -> None:
        """Case with court info has specificity."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity

        case = _make_mock_case(court="S.D.N.Y.")
        assert _has_case_specificity(case)

    def test_case_with_case_number_passes(self) -> None:
        """Case with case number pattern has specificity."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity

        case = _make_mock_case(case_number="1:24-cv-01234")
        assert _has_case_specificity(case)

    def test_case_with_filing_date_passes(self) -> None:
        """Case with specific filing date has specificity."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity
        from datetime import date

        case = _make_mock_case(filing_date=date(2024, 3, 15))
        assert _has_case_specificity(case)

    def test_case_with_no_specifics_fails(self) -> None:
        """Case lacking ALL specifics fails gate."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity

        case = _make_mock_case(
            case_name="Various legal proceedings in the ordinary course"
        )
        assert not _has_case_specificity(case)

    def test_case_with_only_generic_name_fails(self) -> None:
        """Case with only generic name (no v., no court, no date) fails."""
        from do_uw.stages.score.red_flag_gates import _has_case_specificity

        case = _make_mock_case(case_name="General litigation matters")
        assert not _has_case_specificity(case)


# ---------------------------------------------------------------------------
# Integration: CRF-1 with boilerplate filtering
# ---------------------------------------------------------------------------


class TestCRF1Integration:
    """Tests that CRF-1 handles boilerplate vs real SCAs correctly."""

    def test_crf1_not_triggered_boilerplate_only(self) -> None:
        """CRF-1 does NOT trigger when only boilerplate SCAs exist."""
        from do_uw.stages.score.red_flag_gates import _check_active_sca

        extracted = _make_extracted_with_scas([
            _make_mock_case(
                case_name="Various legal proceedings in the normal course of business",
                status="ACTIVE",
            ),
        ])
        fired, evidence = _check_active_sca(extracted)
        assert not fired, f"CRF-1 should not fire on boilerplate, got: {evidence}"

    def test_crf1_triggered_real_sca(self) -> None:
        """CRF-1 DOES trigger when real SCA exists alongside boilerplate."""
        from do_uw.stages.score.red_flag_gates import _check_active_sca

        extracted = _make_extracted_with_scas([
            _make_mock_case(
                case_name="Various legal proceedings in the normal course of business",
                status="ACTIVE",
            ),
            _make_mock_case(
                case_name="Smith v. Acme Corp Securities Litigation",
                status="ACTIVE",
                court="S.D.N.Y.",
                case_number="1:24-cv-01234",
                has_securities_theories=True,
            ),
        ])
        fired, evidence = _check_active_sca(extracted)
        assert fired, "CRF-1 should fire on real SCA"

    def test_crf1_unverified_sca_gets_caveat(self) -> None:
        """Unverified SCA (no corroboration) gets '(unverified)' in evidence."""
        from do_uw.stages.score.red_flag_gates import _check_active_sca

        extracted = _make_extracted_with_scas([
            _make_mock_case(
                case_name="Jones v. Acme Corp",
                status="ACTIVE",
                has_securities_theories=True,
                corroborated=False,
            ),
        ])
        fired, evidence = _check_active_sca(extracted)
        assert fired, "CRF-1 should fire on unverified SCA"
        assert any("unverified" in e.lower() for e in evidence), (
            f"Evidence should note 'unverified': {evidence}"
        )


# ---------------------------------------------------------------------------
# Helper: build mock case objects
# ---------------------------------------------------------------------------


class _MockSourcedValue:
    """Minimal SourcedValue mock for testing."""

    def __init__(self, value: object) -> None:
        self.value = value


class _MockCase:
    """Minimal CaseDetail mock for testing."""

    def __init__(
        self,
        case_name: str | None = None,
        status: str | None = None,
        court: str | None = None,
        case_number: str | None = None,
        filing_date: object = None,
        coverage_type: str | None = None,
        legal_theories: list[str] | None = None,
        allegations: list[str] | None = None,
        corroborated: bool | None = None,
    ) -> None:
        self.case_name = _MockSourcedValue(case_name) if case_name else None
        self.status = _MockSourcedValue(status) if status else None
        self.court = _MockSourcedValue(court) if court else None
        self.case_number = _MockSourcedValue(case_number) if case_number else None
        self.filing_date = _MockSourcedValue(filing_date) if filing_date else None
        self.coverage_type = _MockSourcedValue(coverage_type) if coverage_type else None
        self.legal_theories = (
            [_MockSourcedValue(t) for t in legal_theories]
            if legal_theories
            else []
        )
        self.allegations = (
            [_MockSourcedValue(a) for a in allegations]
            if allegations
            else []
        )
        self.corroborated = corroborated


def _make_mock_case(
    case_name: str | None = None,
    status: str | None = None,
    court: str | None = None,
    case_number: str | None = None,
    filing_date: object = None,
    has_securities_theories: bool = False,
    corroborated: bool | None = None,
) -> _MockCase:
    """Build a mock case with optional fields."""
    theories = None
    if has_securities_theories:
        theories = ["RULE_10B5", "SECURITIES_FRAUD"]
    return _MockCase(
        case_name=case_name,
        status=status,
        court=court,
        case_number=case_number,
        filing_date=filing_date,
        legal_theories=theories,
        corroborated=corroborated,
    )


class _MockLitigation:
    """Minimal mock for ExtractedData.litigation."""

    def __init__(self, scas: list[_MockCase]) -> None:
        self.securities_class_actions = scas


def _make_extracted_with_scas(cases: list[_MockCase]) -> object:
    """Build a minimal ExtractedData-like object with SCAs."""

    class _MockExtracted:
        def __init__(self, lit: _MockLitigation) -> None:
            self.litigation = lit

    return _MockExtracted(_MockLitigation(cases))
