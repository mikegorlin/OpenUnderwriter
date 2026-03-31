"""Unit tests for the litigation LLM converter module.

Covers:
- convert_legal_proceedings: CaseDetail mapping, date parsing, theories, coverage
- convert_contingencies: ContingentLiability mapping, amounts, classification
- convert_risk_factors: RiskFactorProfile mapping, do_relevance inference
- convert_forum_provisions: ForumProvisions cross-domain mapping
- _parse_date: valid/invalid date parsing
- _infer_legal_theories: keyword matching, multiple theories
- _meets_minimum_evidence: hollow record filtering
- _is_generic_label: boilerplate case name detection
- _is_borderline_evidence: borderline confidence downgrade
- SNA regression: boilerplate language produces 0 false SCAs
"""

from __future__ import annotations

from datetime import date

from do_uw.models.common import Confidence
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedContingency,
    ExtractedLegalProceeding,
    ExtractedRiskFactor,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.llm_litigation import (
    _GENERIC_LABELS,
    _infer_coverage_type,
    _infer_legal_theories,
    _is_borderline_evidence,
    _is_generic_label,
    _meets_minimum_evidence,
    _parse_date,
    convert_contingencies,
    convert_forum_provisions,
    convert_legal_proceedings,
    convert_risk_factors,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sample_proceeding_sca() -> ExtractedLegalProceeding:
    """Securities class action proceeding."""
    return ExtractedLegalProceeding(
        case_name="In re Acme Corp Securities Litigation",
        court="S.D.N.Y.",
        filing_date="2024-03-15",
        allegations="Alleged violations of Section 10(b) and Rule 10b-5",
        status="ACTIVE",
        settlement_amount=None,
        class_period_start="2023-01-01",
        class_period_end="2024-02-28",
        legal_theories=["10b-5"],
        named_defendants=["John Smith", "Jane Doe"],
        accrued_amount=None,
        source_passage="See Item 3 Legal Proceedings",
    )


def _sample_proceeding_employment() -> ExtractedLegalProceeding:
    """Employment matter proceeding."""
    return ExtractedLegalProceeding(
        case_name="Johnson v. Acme Corp",
        court="N.D. Cal.",
        filing_date="2023-11-20",
        allegations="Employment discrimination under Title VII",
        status="SETTLED",
        settlement_amount=2500000.0,
        class_period_start=None,
        class_period_end=None,
        legal_theories=[],
        named_defendants=[],
        accrued_amount=None,
        source_passage="",
    )


def _sample_contingency_probable() -> ExtractedContingency:
    """Probable contingency with accrued amount."""
    return ExtractedContingency(
        description="Patent infringement litigation reserve",
        classification="probable",
        accrued_amount=15000000.0,
        range_low=None,
        range_high=None,
        source_passage="Note 12: Commitments and Contingencies",
    )


def _sample_contingency_possible() -> ExtractedContingency:
    """Reasonably possible contingency with range."""
    return ExtractedContingency(
        description="Antitrust investigation exposure",
        classification="reasonably_possible",
        accrued_amount=None,
        range_low=5000000.0,
        range_high=25000000.0,
        source_passage="",
    )


def _sample_ten_k() -> TenKExtraction:
    """TenKExtraction with realistic litigation data."""
    return TenKExtraction(
        legal_proceedings=[
            _sample_proceeding_sca(),
            _sample_proceeding_employment(),
        ],
        contingent_liabilities=[
            _sample_contingency_probable(),
            _sample_contingency_possible(),
        ],
        risk_factors=[
            ExtractedRiskFactor(
                title="Securities litigation risk",
                category="LITIGATION",
                severity="HIGH",
                is_new_this_year=True,
                source_passage="We face ongoing securities litigation...",
            ),
            ExtractedRiskFactor(
                title="Cybersecurity and data privacy risk",
                category="CYBER",
                severity="MEDIUM",
                is_new_this_year=False,
                source_passage="We collect and store personal data...",
            ),
            ExtractedRiskFactor(
                title="Supply chain disruption risk",
                category="OPERATIONAL",
                severity="LOW",
                is_new_this_year=False,
                source_passage="Our operations depend on timely supply...",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# convert_legal_proceedings tests
# ---------------------------------------------------------------------------


class TestConvertLegalProceedings:
    """Tests for convert_legal_proceedings."""

    def test_basic_count(self) -> None:
        """2 proceedings produce 2 CaseDetails."""
        ten_k = _sample_ten_k()
        cases = convert_legal_proceedings(ten_k)
        assert len(cases) == 2

    def test_skips_empty_name(self) -> None:
        """Proceeding with empty case_name is skipped."""
        ten_k = TenKExtraction(
            legal_proceedings=[
                ExtractedLegalProceeding(case_name=""),
                _sample_proceeding_sca(),
            ]
        )
        cases = convert_legal_proceedings(ten_k)
        assert len(cases) == 1
        assert cases[0].case_name is not None
        assert cases[0].case_name.value == "In re Acme Corp Securities Litigation"

    def test_sourced_values(self) -> None:
        """Verify source and confidence on key fields."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.case_name is not None
        assert case.case_name.source == "10-K (LLM)"
        assert case.case_name.confidence == Confidence.HIGH

        assert case.court is not None
        assert case.court.source == "10-K (LLM)"
        assert case.court.confidence == Confidence.HIGH

        assert case.status is not None
        assert case.status.source == "10-K (LLM)"

    def test_date_parsing(self) -> None:
        """Filing date 2024-03-15 becomes date(2024, 3, 15)."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.filing_date is not None
        assert case.filing_date.value == date(2024, 3, 15)
        assert case.filing_date.confidence == Confidence.HIGH

    def test_legal_theories(self) -> None:
        """Securities allegations produce RULE_10B5 theory."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        theory_values = [t.value for t in case.legal_theories]
        assert "RULE_10B5" in theory_values

    def test_coverage_type_sca(self) -> None:
        """Securities theories produce SCA_SIDE_C coverage type."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.coverage_type is not None
        assert case.coverage_type.value == "SCA_SIDE_C"

    def test_named_defendants(self) -> None:
        """Named defendants list is converted to SourcedValues."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert len(case.named_defendants) == 2
        names = [d.value for d in case.named_defendants]
        assert "John Smith" in names
        assert "Jane Doe" in names
        assert case.named_defendants[0].source == "10-K (LLM)"

    def test_settlement_amount(self) -> None:
        """Settlement amount is mapped when present."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_employment()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.settlement_amount is not None
        assert case.settlement_amount.value == 2500000.0

    def test_class_period_dates(self) -> None:
        """Class period start/end dates are parsed."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_sca()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.class_period_start is not None
        assert case.class_period_start.value == date(2023, 1, 1)
        assert case.class_period_end is not None
        assert case.class_period_end.value == date(2024, 2, 28)

    def test_employment_coverage_type(self) -> None:
        """Employment discrimination produces EMPLOYMENT_ENTITY."""
        ten_k = TenKExtraction(
            legal_proceedings=[_sample_proceeding_employment()]
        )
        cases = convert_legal_proceedings(ten_k)
        case = cases[0]

        assert case.coverage_type is not None
        assert case.coverage_type.value == "EMPLOYMENT_ENTITY"


# ---------------------------------------------------------------------------
# convert_contingencies tests
# ---------------------------------------------------------------------------


class TestConvertContingencies:
    """Tests for convert_contingencies."""

    def test_basic_count(self) -> None:
        """2 contingencies produce 2 ContingentLiability."""
        ten_k = _sample_ten_k()
        liabilities = convert_contingencies(ten_k)
        assert len(liabilities) == 2

    def test_skips_empty_description(self) -> None:
        """Entry with empty description is skipped."""
        ten_k = TenKExtraction(
            contingent_liabilities=[
                ExtractedContingency(description=""),
                _sample_contingency_probable(),
            ]
        )
        liabilities = convert_contingencies(ten_k)
        assert len(liabilities) == 1

    def test_amounts(self) -> None:
        """Accrued amount, range_low, range_high are mapped."""
        ten_k = TenKExtraction(
            contingent_liabilities=[
                _sample_contingency_probable(),
                _sample_contingency_possible(),
            ]
        )
        liabilities = convert_contingencies(ten_k)

        # Probable has accrued_amount
        prob = liabilities[0]
        assert prob.accrued_amount is not None
        assert prob.accrued_amount.value == 15000000.0
        assert prob.range_low is None
        assert prob.range_high is None

        # Possible has range
        poss = liabilities[1]
        assert poss.accrued_amount is None
        assert poss.range_low is not None
        assert poss.range_low.value == 5000000.0
        assert poss.range_high is not None
        assert poss.range_high.value == 25000000.0

    def test_classification(self) -> None:
        """ASC 450 classification is mapped correctly."""
        ten_k = TenKExtraction(
            contingent_liabilities=[_sample_contingency_probable()]
        )
        liabilities = convert_contingencies(ten_k)
        lib = liabilities[0]

        assert lib.asc_450_classification is not None
        assert lib.asc_450_classification.value == "probable"
        assert lib.asc_450_classification.source == "10-K (LLM)"

    def test_source_note(self) -> None:
        """Source passage is mapped to source_note."""
        ten_k = TenKExtraction(
            contingent_liabilities=[_sample_contingency_probable()]
        )
        liabilities = convert_contingencies(ten_k)
        lib = liabilities[0]

        assert lib.source_note is not None
        assert lib.source_note.value == "Note 12: Commitments and Contingencies"


# ---------------------------------------------------------------------------
# convert_risk_factors tests
# ---------------------------------------------------------------------------


class TestConvertRiskFactors:
    """Tests for convert_risk_factors."""

    def test_basic_count(self) -> None:
        """3 risk factors produce 3 RiskFactorProfile."""
        ten_k = _sample_ten_k()
        profiles = convert_risk_factors(ten_k)
        assert len(profiles) == 3

    def test_do_relevance_inference(self) -> None:
        """LITIGATION->HIGH, CYBER->MEDIUM, OPERATIONAL->LOW."""
        ten_k = _sample_ten_k()
        profiles = convert_risk_factors(ten_k)

        by_category = {p.category: p for p in profiles}
        assert by_category["LITIGATION"].do_relevance == "HIGH"
        assert by_category["CYBER"].do_relevance == "MEDIUM"
        assert by_category["OPERATIONAL"].do_relevance == "LOW"

    def test_skips_empty_title(self) -> None:
        """Risk factor with empty title is skipped."""
        ten_k = TenKExtraction(
            risk_factors=[
                ExtractedRiskFactor(title=""),
                ExtractedRiskFactor(title="Real risk", category="FINANCIAL"),
            ]
        )
        profiles = convert_risk_factors(ten_k)
        assert len(profiles) == 1
        assert profiles[0].title == "Real risk"

    def test_source_set(self) -> None:
        """Source is set to 10-K (LLM)."""
        ten_k = TenKExtraction(
            risk_factors=[
                ExtractedRiskFactor(title="Test risk", category="REGULATORY")
            ]
        )
        profiles = convert_risk_factors(ten_k)
        assert profiles[0].source == "10-K (LLM)"

    def test_is_new_this_year(self) -> None:
        """is_new_this_year is preserved."""
        ten_k = _sample_ten_k()
        profiles = convert_risk_factors(ten_k)
        by_category = {p.category: p for p in profiles}
        assert by_category["LITIGATION"].is_new_this_year is True
        assert by_category["CYBER"].is_new_this_year is False

    def test_regulatory_relevance(self) -> None:
        """REGULATORY category gets HIGH do_relevance."""
        ten_k = TenKExtraction(
            risk_factors=[
                ExtractedRiskFactor(title="Regulatory risk", category="REGULATORY")
            ]
        )
        profiles = convert_risk_factors(ten_k)
        assert profiles[0].do_relevance == "HIGH"


# ---------------------------------------------------------------------------
# convert_forum_provisions tests
# ---------------------------------------------------------------------------


class TestConvertForumProvisions:
    """Tests for convert_forum_provisions."""

    def test_basic_mapping(self) -> None:
        """DEF14A forum fields map to ForumProvisions."""
        proxy = DEF14AExtraction(
            exclusive_forum_provision=True,
            forum_selection_clause="Delaware Court of Chancery",
        )
        fp = convert_forum_provisions(proxy)

        assert fp.has_exclusive_forum is not None
        assert fp.has_exclusive_forum.value is True
        assert fp.has_exclusive_forum.source == "DEF 14A (LLM)"

        assert fp.exclusive_forum_details is not None
        assert fp.exclusive_forum_details.value == "Delaware Court of Chancery"

        assert fp.source_document is not None
        assert fp.source_document.value == "DEF 14A proxy statement"

    def test_none_values(self) -> None:
        """None inputs produce None SourcedValue fields."""
        proxy = DEF14AExtraction(
            exclusive_forum_provision=None,
            forum_selection_clause=None,
        )
        fp = convert_forum_provisions(proxy)

        assert fp.has_exclusive_forum is None
        assert fp.exclusive_forum_details is None
        # source_document is always set
        assert fp.source_document is not None


# ---------------------------------------------------------------------------
# Private helper tests
# ---------------------------------------------------------------------------


class TestParseDate:
    """Tests for _parse_date."""

    def test_valid_date(self) -> None:
        """'2024-03-15' -> date(2024, 3, 15)."""
        result = _parse_date("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_invalid_date(self) -> None:
        """'bad-date' -> None."""
        result = _parse_date("bad-date")
        assert result is None

    def test_none_input(self) -> None:
        """None -> None."""
        result = _parse_date(None)
        assert result is None

    def test_empty_string(self) -> None:
        """'' -> None."""
        result = _parse_date("")
        assert result is None


class TestInferLegalTheories:
    """Tests for _infer_legal_theories."""

    def test_single_theory(self) -> None:
        """Text with '10b-5' produces RULE_10B5."""
        result = _infer_legal_theories("Violations of Rule 10b-5")
        assert "RULE_10B5" in result

    def test_multiple_theories(self) -> None:
        """Text with '10b-5' and 'Section 11' produces 2 theories."""
        text = "Claims under Rule 10b-5 and Section 11 of the Securities Act"
        result = _infer_legal_theories(text)
        assert "RULE_10B5" in result
        assert "SECTION_11" in result
        assert len(result) >= 2

    def test_case_insensitive(self) -> None:
        """Matching is case-insensitive."""
        result = _infer_legal_theories("ERISA claims and FCPA violations")
        assert "ERISA" in result
        assert "FCPA" in result

    def test_empty_text(self) -> None:
        """Empty text returns empty list."""
        result = _infer_legal_theories("")
        assert result == []

    def test_no_match(self) -> None:
        """Text with no matching keywords returns empty list."""
        result = _infer_legal_theories("General business dispute")
        assert result == []


class TestInferCoverageType:
    """Tests for _infer_coverage_type."""

    def test_securities_theory(self) -> None:
        """Securities theory -> SCA_SIDE_C."""
        assert _infer_coverage_type(["RULE_10B5"]) == "SCA_SIDE_C"

    def test_derivative(self) -> None:
        """Derivative duty -> DERIVATIVE_SIDE_A."""
        assert _infer_coverage_type(["DERIVATIVE_DUTY"]) == "DERIVATIVE_SIDE_A"

    def test_erisa(self) -> None:
        """ERISA -> EMPLOYMENT_ENTITY."""
        assert _infer_coverage_type(["ERISA"]) == "EMPLOYMENT_ENTITY"

    def test_product(self) -> None:
        """Product liability -> PRODUCT_ENTITY."""
        assert _infer_coverage_type(["PRODUCT_LIABILITY"]) == "PRODUCT_ENTITY"

    def test_default(self) -> None:
        """Unknown theories -> COMMERCIAL_ENTITY (safe default)."""
        assert _infer_coverage_type(["UNKNOWN"]) == "COMMERCIAL_ENTITY"

    def test_securities_priority(self) -> None:
        """Securities theory takes priority over others."""
        assert (
            _infer_coverage_type(["ERISA", "RULE_10B5"]) == "SCA_SIDE_C"
        )


# ---------------------------------------------------------------------------
# Minimum evidence filter tests
# ---------------------------------------------------------------------------


class TestMeetsMinimumEvidence:
    """Tests for _meets_minimum_evidence."""

    def test_real_case_passes(self) -> None:
        """Proceeding with case_name + court + filing_date passes."""
        proc = ExtractedLegalProceeding(
            case_name="Smith v. Acme Corp",
            court="S.D.N.Y.",
            filing_date="2025-01-15",
        )
        assert _meets_minimum_evidence(proc)

    def test_generic_label_rejected(self) -> None:
        """Generic label 'Various Legal Proceedings' with no specifics fails."""
        proc = ExtractedLegalProceeding(
            case_name="Various Legal Proceedings",
            court=None,
            filing_date=None,
        )
        assert not _meets_minimum_evidence(proc)

    def test_empty_name_rejected(self) -> None:
        """Empty case_name fails."""
        proc = ExtractedLegalProceeding(
            case_name="",
            court="S.D.N.Y.",
            filing_date="2025-01-15",
        )
        assert not _meets_minimum_evidence(proc)

    def test_named_parties_plus_court(self) -> None:
        """Named parties + court (no filing_date) passes."""
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court="D. Del.",
            filing_date=None,
        )
        assert _meets_minimum_evidence(proc)

    def test_named_parties_plus_date(self) -> None:
        """Named parties + filing_date (no court) passes."""
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court=None,
            filing_date="2024-06-01",
        )
        assert _meets_minimum_evidence(proc)

    def test_named_parties_only_fails(self) -> None:
        """Named parties with no court and no filing_date fails.

        This is the borderline case -- _meets_minimum_evidence returns False
        but _is_borderline_evidence returns True (kept at LOW confidence).
        """
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court=None,
            filing_date=None,
        )
        assert not _meets_minimum_evidence(proc)

    def test_whitespace_court_treated_as_missing(self) -> None:
        """Court with only whitespace is treated as missing."""
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court="   ",
            filing_date=None,
        )
        assert not _meets_minimum_evidence(proc)


class TestIsGenericLabel:
    """Tests for _is_generic_label."""

    def test_all_generic_labels(self) -> None:
        """Every label in _GENERIC_LABELS is detected."""
        for label in _GENERIC_LABELS:
            assert _is_generic_label(label), f"Should be generic: {label}"

    def test_case_insensitive(self) -> None:
        """Generic label check is case-insensitive."""
        assert _is_generic_label("Various Legal Proceedings")
        assert _is_generic_label("VARIOUS LEGAL PROCEEDINGS")
        assert _is_generic_label("Legal Matters")

    def test_real_case_not_generic(self) -> None:
        """Real case names are NOT generic."""
        assert not _is_generic_label("Doe v. Smith Corp")
        assert not _is_generic_label("In re Acme Corp Securities Litigation")
        assert not _is_generic_label("SEC v. Johnson")

    def test_whitespace_handling(self) -> None:
        """Whitespace around label is stripped."""
        assert _is_generic_label("  legal proceedings  ")
        assert _is_generic_label("\tlitigation matters\n")


class TestIsBorderlineEvidence:
    """Tests for _is_borderline_evidence."""

    def test_borderline_case(self) -> None:
        """Named parties but no court and no filing_date is borderline."""
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court=None,
            filing_date=None,
        )
        assert _is_borderline_evidence(proc)

    def test_full_evidence_not_borderline(self) -> None:
        """Full evidence (court + date) is NOT borderline."""
        proc = ExtractedLegalProceeding(
            case_name="Doe v. Widget Inc",
            court="S.D.N.Y.",
            filing_date="2025-01-15",
        )
        assert not _is_borderline_evidence(proc)

    def test_generic_label_not_borderline(self) -> None:
        """Generic label is NOT borderline (it's just dropped)."""
        proc = ExtractedLegalProceeding(
            case_name="Various Legal Proceedings",
            court=None,
            filing_date=None,
        )
        assert not _is_borderline_evidence(proc)


# ---------------------------------------------------------------------------
# Minimum evidence integration with convert_legal_proceedings
# ---------------------------------------------------------------------------


class TestConvertLegalProceedingsFiltering:
    """Tests for convert_legal_proceedings with minimum evidence filtering."""

    def test_filters_boilerplate(self) -> None:
        """Boilerplate + empty name filtered; only real case survives."""
        ten_k = TenKExtraction(
            legal_proceedings=[
                # Real case: has named parties + court + date
                ExtractedLegalProceeding(
                    case_name="Smith v. Acme Corp",
                    court="S.D.N.Y.",
                    filing_date="2025-01-15",
                    allegations="Securities fraud",
                ),
                # Boilerplate: generic label, no specifics
                ExtractedLegalProceeding(
                    case_name="Various Legal Proceedings",
                    court=None,
                    filing_date=None,
                ),
                # Empty name
                ExtractedLegalProceeding(
                    case_name="",
                ),
            ]
        )
        cases = convert_legal_proceedings(ten_k)
        assert len(cases) == 1
        assert cases[0].case_name is not None
        assert cases[0].case_name.value == "Smith v. Acme Corp"

    def test_borderline_kept_at_low_confidence(self) -> None:
        """Borderline case (named parties, no court/date) kept at LOW."""
        ten_k = TenKExtraction(
            legal_proceedings=[
                ExtractedLegalProceeding(
                    case_name="Doe v. Widget Inc",
                    court=None,
                    filing_date=None,
                    allegations="General breach claim",
                ),
            ]
        )
        cases = convert_legal_proceedings(ten_k)
        # Borderline case is kept via _is_borderline_evidence path
        assert len(cases) == 1
        case = cases[0]
        assert case.case_name is not None
        assert case.case_name.confidence == Confidence.LOW
        assert case.coverage_type is not None
        assert case.coverage_type.confidence == Confidence.LOW

    def test_sna_regression_no_false_scas(self) -> None:
        """SNA regression: boilerplate 10-K language produces 0 CaseDetails.

        SNA validation audit found false SCAs generated from generic
        10-K legal language like 'routine legal proceedings' and
        'various legal proceedings'. This test ensures those are filtered.
        """
        ten_k = TenKExtraction(
            legal_proceedings=[
                ExtractedLegalProceeding(
                    case_name="Routine Legal Proceedings",
                    court=None,
                    filing_date=None,
                    allegations=None,
                ),
                ExtractedLegalProceeding(
                    case_name="Various Legal Proceedings",
                    court=None,
                    filing_date=None,
                    allegations="The company is subject to various legal proceedings",
                ),
                ExtractedLegalProceeding(
                    case_name="Legal Matters",
                    court=None,
                    filing_date=None,
                    allegations=None,
                ),
                ExtractedLegalProceeding(
                    case_name="Pending Litigation",
                    court=None,
                    filing_date=None,
                    allegations="Normal course of business litigation",
                ),
                ExtractedLegalProceeding(
                    case_name="Ordinary Course Litigation",
                    court=None,
                    filing_date=None,
                    allegations=None,
                ),
            ]
        )
        cases = convert_legal_proceedings(ten_k)
        assert len(cases) == 0, (
            f"Expected 0 CaseDetails from boilerplate, got {len(cases)}: "
            f"{[c.case_name.value for c in cases if c.case_name]}"
        )
