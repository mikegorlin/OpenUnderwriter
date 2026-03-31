"""Tests for Phase 27 peril mapping Pydantic models.

Validates construction, serialization, round-trip, and edge cases
for PerilMap, PlaintiffAssessment, BearCase, and related models.
"""

from __future__ import annotations

import pytest

from do_uw.models.peril import (
    BearCase,
    EvidenceItem,
    PerilMap,
    PerilProbabilityBand,
    PerilSeverityBand,
    PlaintiffAssessment,
    PlaintiffFirmMatch,
)


# -----------------------------------------------------------------------
# PlaintiffAssessment tests
# -----------------------------------------------------------------------


class TestPlaintiffAssessment:
    """Test PlaintiffAssessment construction and serialization."""

    def test_full_modeling_depth(self) -> None:
        """Shareholders assessment with FULL modeling depth."""
        pa = PlaintiffAssessment(
            plaintiff_type="SHAREHOLDERS",
            probability_band=PerilProbabilityBand.ELEVATED,
            severity_band=PerilSeverityBand.SIGNIFICANT,
            triggered_signal_count=8,
            total_signal_count=25,
            evaluated_signal_count=22,
            key_findings=["Stock price decline >30%", "Insider selling cluster"],
            modeling_depth="FULL",
        )
        assert pa.plaintiff_type == "SHAREHOLDERS"
        assert pa.probability_band == "ELEVATED"
        assert pa.severity_band == "SIGNIFICANT"
        assert pa.modeling_depth == "FULL"
        assert pa.triggered_signal_count == 8
        assert pa.evaluated_signal_count == 22

    def test_proportional_modeling_depth(self) -> None:
        """Employees assessment with PROPORTIONAL modeling depth."""
        pa = PlaintiffAssessment(
            plaintiff_type="EMPLOYEES",
            probability_band=PerilProbabilityBand.VERY_LOW,
            severity_band=PerilSeverityBand.NUISANCE,
            triggered_signal_count=0,
            total_signal_count=3,
            evaluated_signal_count=2,
            key_findings=[],
            modeling_depth="PROPORTIONAL",
        )
        assert pa.plaintiff_type == "EMPLOYEES"
        assert pa.probability_band == "VERY_LOW"
        assert pa.modeling_depth == "PROPORTIONAL"
        assert len(pa.key_findings) == 0

    def test_serialization(self) -> None:
        """PlaintiffAssessment serializes to dict and back."""
        pa = PlaintiffAssessment(
            plaintiff_type="REGULATORS",
            probability_band=PerilProbabilityBand.MODERATE,
            severity_band=PerilSeverityBand.MODERATE,
            triggered_signal_count=3,
            total_signal_count=10,
            evaluated_signal_count=8,
            key_findings=["SEC comment letter exchange"],
            modeling_depth="FULL",
        )
        data = pa.model_dump()
        restored = PlaintiffAssessment(**data)
        assert restored.plaintiff_type == pa.plaintiff_type
        assert restored.probability_band == pa.probability_band
        assert restored.key_findings == pa.key_findings


# -----------------------------------------------------------------------
# EvidenceItem tests
# -----------------------------------------------------------------------


class TestEvidenceItem:
    """Test EvidenceItem model."""

    def test_construction(self) -> None:
        ei = EvidenceItem(
            signal_id="FIN.ACCT.restatement",
            description="Financial restatement detected in 10-K",
            source="SEC EDGAR 10-K filing",
            severity="CRITICAL",
            data_status="EVALUATED",
        )
        assert ei.signal_id == "FIN.ACCT.restatement"
        assert ei.data_status == "EVALUATED"


# -----------------------------------------------------------------------
# BearCase tests
# -----------------------------------------------------------------------


class TestBearCase:
    """Test BearCase construction and optional fields."""

    def test_with_defense_assessment(self) -> None:
        """BearCase with company-specific defense."""
        bc = BearCase(
            theory="A_DISCLOSURE",
            plaintiff_type="SHAREHOLDERS",
            committee_summary="Revenue recognition concerns with Q3 restatement. "
            "Multiple insider sales during class period. "
            "Strong potential for 10b-5 claim.",
            evidence_chain=[
                EvidenceItem(
                    signal_id="FIN.ACCT.restatement",
                    description="Q3 restatement",
                    source="10-K",
                    severity="CRITICAL",
                    data_status="EVALUATED",
                ),
            ],
            severity_estimate=PerilSeverityBand.SIGNIFICANT,
            defense_assessment="Motion to dismiss likely on loss causation grounds",
            probability_band=PerilProbabilityBand.ELEVATED,
            supporting_signal_count=5,
        )
        assert bc.defense_assessment is not None
        assert bc.theory == "A_DISCLOSURE"
        assert bc.supporting_signal_count == 5

    def test_without_defense_assessment(self) -> None:
        """BearCase without defense (default None)."""
        bc = BearCase(
            theory="B_GUIDANCE",
            plaintiff_type="SHAREHOLDERS",
            committee_summary="Guidance miss with subsequent stock decline.",
            evidence_chain=[],
            severity_estimate=PerilSeverityBand.MINOR,
            probability_band=PerilProbabilityBand.LOW,
            supporting_signal_count=2,
        )
        assert bc.defense_assessment is None
        assert bc.severity_estimate == "MINOR"


# -----------------------------------------------------------------------
# PlaintiffFirmMatch tests
# -----------------------------------------------------------------------


class TestPlaintiffFirmMatch:
    """Test PlaintiffFirmMatch model."""

    def test_tier_1_match(self) -> None:
        pfm = PlaintiffFirmMatch(
            firm_name="Bernstein Litowitz Berger & Grossmann",
            tier=1,
            severity_multiplier=2.0,
            match_source="securities_class_actions[0].lead_counsel",
        )
        assert pfm.tier == 1
        assert pfm.severity_multiplier == 2.0

    def test_tier_3_default(self) -> None:
        pfm = PlaintiffFirmMatch(
            firm_name="Unknown Regional Firm",
            tier=3,
            severity_multiplier=1.0,
            match_source="derivative_suits[0].lead_counsel",
        )
        assert pfm.tier == 3
        assert pfm.severity_multiplier == 1.0


# -----------------------------------------------------------------------
# PerilMap tests
# -----------------------------------------------------------------------


class TestPerilMap:
    """Test PerilMap root container."""

    def _make_assessment(
        self, plaintiff_type: str, prob: str = "VERY_LOW", sev: str = "NUISANCE"
    ) -> PlaintiffAssessment:
        """Helper to create a PlaintiffAssessment."""
        depth = "FULL" if plaintiff_type in ("SHAREHOLDERS", "REGULATORS") else "PROPORTIONAL"
        return PlaintiffAssessment(
            plaintiff_type=plaintiff_type,
            probability_band=prob,
            severity_band=sev,
            triggered_signal_count=0,
            total_signal_count=5,
            evaluated_signal_count=4,
            key_findings=[],
            modeling_depth=depth,
        )

    def test_seven_assessments(self) -> None:
        """PerilMap holds exactly 7 assessments."""
        lenses = [
            "SHAREHOLDERS", "REGULATORS", "CUSTOMERS",
            "COMPETITORS", "EMPLOYEES", "CREDITORS", "GOVERNMENT",
        ]
        assessments = [self._make_assessment(lens) for lens in lenses]
        pm = PerilMap(
            assessments=assessments,
            overall_peril_rating=PerilProbabilityBand.VERY_LOW,
        )
        assert len(pm.assessments) == 7

    def test_round_trip(self) -> None:
        """PerilMap round-trip: construct -> model_dump -> reconstruct."""
        lenses = [
            "SHAREHOLDERS", "REGULATORS", "CUSTOMERS",
            "COMPETITORS", "EMPLOYEES", "CREDITORS", "GOVERNMENT",
        ]
        assessments = [
            self._make_assessment(
                lenses[i],
                prob=PerilProbabilityBand.MODERATE if i == 0 else PerilProbabilityBand.VERY_LOW,
                sev=PerilSeverityBand.MODERATE if i == 0 else PerilSeverityBand.NUISANCE,
            )
            for i in range(7)
        ]
        pm = PerilMap(
            assessments=assessments,
            bear_cases=[
                BearCase(
                    theory="A_DISCLOSURE",
                    plaintiff_type="SHAREHOLDERS",
                    committee_summary="Test bear case.",
                    evidence_chain=[],
                    severity_estimate=PerilSeverityBand.MODERATE,
                    probability_band=PerilProbabilityBand.MODERATE,
                    supporting_signal_count=3,
                ),
            ],
            plaintiff_firm_matches=[
                PlaintiffFirmMatch(
                    firm_name="Pomerantz",
                    tier=2,
                    severity_multiplier=1.5,
                    match_source="sca[0]",
                ),
            ],
            overall_peril_rating=PerilProbabilityBand.MODERATE,
            coverage_gaps=["FIN.ACCT.restatement: DATA_UNAVAILABLE"],
        )

        data = pm.model_dump()
        restored = PerilMap(**data)

        assert len(restored.assessments) == 7
        assert len(restored.bear_cases) == 1
        assert len(restored.plaintiff_firm_matches) == 1
        assert restored.overall_peril_rating == "MODERATE"
        assert restored.coverage_gaps == pm.coverage_gaps
        assert restored.assessments[0].plaintiff_type == "SHAREHOLDERS"
        assert restored.assessments[0].probability_band == "MODERATE"

    def test_empty_bear_cases(self) -> None:
        """PerilMap with no bear cases (clean company)."""
        lenses = [
            "SHAREHOLDERS", "REGULATORS", "CUSTOMERS",
            "COMPETITORS", "EMPLOYEES", "CREDITORS", "GOVERNMENT",
        ]
        pm = PerilMap(
            assessments=[self._make_assessment(lens) for lens in lenses],
            bear_cases=[],
            overall_peril_rating=PerilProbabilityBand.VERY_LOW,
        )
        assert len(pm.bear_cases) == 0
        assert pm.overall_peril_rating == "VERY_LOW"


# -----------------------------------------------------------------------
# Enum tests
# -----------------------------------------------------------------------


class TestEnums:
    """Test PerilProbabilityBand and PerilSeverityBand enums."""

    def test_probability_band_values(self) -> None:
        assert len(PerilProbabilityBand) == 5
        assert PerilProbabilityBand.VERY_LOW == "VERY_LOW"
        assert PerilProbabilityBand.HIGH == "HIGH"

    def test_severity_band_values(self) -> None:
        assert len(PerilSeverityBand) == 5
        assert PerilSeverityBand.NUISANCE == "NUISANCE"
        assert PerilSeverityBand.SEVERE == "SEVERE"
