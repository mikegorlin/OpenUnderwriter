"""Unit tests for material weakness boilerplate filter.

Tests _is_auditor_methodology_boilerplate() and extract_material_weaknesses()
to verify that standard PCAOB auditor methodology language is filtered out
while genuine material weakness findings are preserved.
"""

from __future__ import annotations

from do_uw.stages.extract.audit_risk_helpers import (
    _is_auditor_methodology_boilerplate,
    extract_material_weaknesses,
)


# ------------------------------------------------------------------
# Unit tests for _is_auditor_methodology_boilerplate
# ------------------------------------------------------------------


class TestIsAuditorMethodologyBoilerplate:
    """Tests for the boilerplate detection function."""

    def test_audit_included_language(self) -> None:
        sentence = (
            "Our audit of internal control over financial reporting included "
            "obtaining an understanding of internal control over financial "
            "reporting, assessing the risk that a material weakness exists"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_assessing_risk_phrase(self) -> None:
        sentence = (
            "The audit procedures included assessing the risk that a "
            "material weakness exists in the company's internal controls"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_testing_and_evaluating_design(self) -> None:
        sentence = (
            "We performed procedures including testing and evaluating "
            "the design and operating effectiveness of internal control "
            "based on the assessed risk"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_definition_of_material_weakness(self) -> None:
        sentence = (
            "A material weakness is a deficiency, or a combination of "
            "deficiencies, in internal control over financial reporting"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_definition_simple(self) -> None:
        sentence = (
            "A material weakness is a deficiency in internal control "
            "over financial reporting"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_responsibility_to_express_opinion(self) -> None:
        sentence = (
            "Our responsibility is to express an opinion on the company's "
            "internal control over financial reporting based on our audit, "
            "including whether any material weakness has been identified"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_pcaob_standards_reference(self) -> None:
        sentence = (
            "We conducted our audit in accordance with the standards of "
            "the Public Company Accounting Oversight Board to determine "
            "whether any material weakness exists"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True

    def test_actual_finding_not_flagged(self) -> None:
        sentence = (
            "We identified a material weakness in the Company's internal "
            "control over financial reporting related to the income tax "
            "provision process"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is False

    def test_management_identified_not_flagged(self) -> None:
        sentence = (
            "Management identified a material weakness in controls over "
            "revenue recognition for contracts with multiple deliverables"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is False

    def test_ineffective_controls_not_flagged(self) -> None:
        sentence = (
            "The Company's internal control over financial reporting was "
            "not effective due to a material weakness in the financial "
            "close process"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is False

    def test_it_general_controls_finding_not_flagged(self) -> None:
        sentence = (
            "A material weakness was identified in IT general controls "
            "over access management and change management"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is False

    def test_remediation_context_not_flagged(self) -> None:
        sentence = (
            "The previously reported material weakness related to "
            "inventory valuation has been remediated"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is False

    def test_case_insensitive(self) -> None:
        sentence = (
            "OUR AUDIT OF INTERNAL CONTROL OVER FINANCIAL REPORTING "
            "INCLUDED OBTAINING AN UNDERSTANDING OF INTERNAL CONTROL "
            "OVER FINANCIAL REPORTING"
        )
        assert _is_auditor_methodology_boilerplate(sentence) is True


# ------------------------------------------------------------------
# Integration tests for extract_material_weaknesses with filter
# ------------------------------------------------------------------


class TestExtractMaterialWeaknessesWithFilter:
    """Tests that extract_material_weaknesses filters boilerplate."""

    def test_pure_boilerplate_returns_empty(self) -> None:
        """Visa-style audit report with NO actual weaknesses."""
        text = (
            "Our audit of internal control over financial reporting included "
            "obtaining an understanding of internal control over financial "
            "reporting, assessing the risk that a material weakness exists, "
            "and testing and evaluating the design and operating effectiveness "
            "of internal control based on the assessed risk. "
            "A material weakness is a deficiency, or a combination of "
            "deficiencies, in internal control over financial reporting, "
            "such that there is a reasonable possibility that a material "
            "misstatement will not be prevented."
        )
        result = extract_material_weaknesses(text)
        assert result == []

    def test_actual_finding_extracted(self) -> None:
        """Real material weakness is extracted."""
        text = (
            "We identified a material weakness in the Company's internal "
            "control over financial reporting related to the revenue "
            "recognition process for multiple-element arrangements."
        )
        result = extract_material_weaknesses(text)
        assert len(result) == 1
        assert "revenue recognition" in result[0]

    def test_mixed_boilerplate_and_findings(self) -> None:
        """Only real findings survive when mixed with boilerplate."""
        text = (
            "Our audit of internal control over financial reporting included "
            "assessing the risk that a material weakness exists. "
            "A material weakness is a deficiency in internal control over "
            "financial reporting. "
            "We identified a material weakness in controls over the "
            "financial close and reporting process."
        )
        result = extract_material_weaknesses(text)
        assert len(result) == 1
        assert "financial close" in result[0]

    def test_no_material_weakness_keyword_returns_empty(self) -> None:
        """No 'material weakness' in text returns empty immediately."""
        text = "The company's internal controls were effective."
        result = extract_material_weaknesses(text)
        assert result == []

    def test_multiple_real_findings(self) -> None:
        """Multiple actual findings are all preserved."""
        text = (
            "Management identified a material weakness in the Company's "
            "IT general controls over access management. "
            "A second material weakness was identified in the Company's "
            "controls over the financial statement close process. "
            "The Company's internal control over financial reporting was "
            "not effective due to a material weakness in tax provision "
            "calculations."
        )
        result = extract_material_weaknesses(text)
        assert len(result) == 3

    def test_cap_at_five(self) -> None:
        """Results capped at 5 even with more findings."""
        sentences = []
        for i in range(7):
            sentences.append(
                f"A material weakness was identified in control area {i}."
            )
        text = " ".join(sentences)
        result = extract_material_weaknesses(text)
        assert len(result) == 5
