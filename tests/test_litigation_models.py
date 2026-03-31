"""Tests for litigation models, config files, and filing section parsing.

Covers:
- LitigationLandscape instantiation with defaults
- CaseDetail two-layer classification
- SECEnforcementPipeline pipeline stages
- All litigation_details.py sub-models
- JSON serialization round-trip
- Config file loading (lead_counsel_tiers, claim_types, industry_theories)
- Item 3 and Item 1A section extraction from filing_sections.py
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    CaseStatus,
    CoverageType,
    EnforcementStage,
    LegalTheory,
    LitigationLandscape,
    SECEnforcement,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import (
    ContingentLiability,
    DealLitigation,
    DefenseAssessment,
    ForumProvisions,
    IndustryClaimPattern,
    LitigationTimelineEvent,
    RegulatoryProceeding,
    SOLWindow,
    WhistleblowerIndicator,
    WorkforceProductEnvironmental,
)
from do_uw.stages.extract.filing_sections import extract_10k_sections

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONFIG_DIR = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
NOW = datetime.now(tz=UTC)


def _sv(value: object, source: str = "test") -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue(
        value=str(value), source=source, confidence=Confidence.LOW, as_of=NOW
    )


def _sv_int(value: int, source: str = "test") -> SourcedValue[int]:
    """Create a test SourcedValue[int]."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.LOW, as_of=NOW
    )


def _sv_float(value: float, source: str = "test") -> SourcedValue[float]:
    """Create a test SourcedValue[float]."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.LOW, as_of=NOW
    )


def _sv_bool(value: bool, source: str = "test") -> SourcedValue[bool]:
    """Create a test SourcedValue[bool]."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.LOW, as_of=NOW
    )


def _sv_date(value: date, source: str = "test") -> SourcedValue[date]:
    """Create a test SourcedValue[date]."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.LOW, as_of=NOW
    )


# ---------------------------------------------------------------------------
# LitigationLandscape instantiation
# ---------------------------------------------------------------------------


class TestLitigationLandscapeDefaults:
    """Test LitigationLandscape instantiates with all defaults."""

    def test_default_instantiation(self) -> None:
        ll = LitigationLandscape()
        assert ll.securities_class_actions == []
        assert ll.derivative_suits == []
        assert ll.regulatory_proceedings == []
        assert ll.deal_litigation == []
        assert ll.industry_patterns == []
        assert ll.sol_map == []
        assert ll.contingent_liabilities == []
        assert ll.whistleblower_indicators == []
        assert ll.litigation_timeline_events == []
        assert ll.defense_assessment is None
        assert ll.total_litigation_reserve is None
        assert ll.litigation_summary is None
        assert ll.active_matter_count is None
        assert ll.historical_matter_count is None

    def test_sec_enforcement_default(self) -> None:
        ll = LitigationLandscape()
        assert isinstance(ll.sec_enforcement, SECEnforcementPipeline)
        assert ll.sec_enforcement.pipeline_position is None
        assert ll.sec_enforcement.actions == []

    def test_defense_default(self) -> None:
        ll = LitigationLandscape()
        assert isinstance(ll.defense, DefenseAssessment)
        assert isinstance(ll.defense.forum_provisions, ForumProvisions)

    def test_workforce_default(self) -> None:
        ll = LitigationLandscape()
        assert isinstance(
            ll.workforce_product_environmental, WorkforceProductEnvironmental
        )
        assert ll.workforce_product_environmental.employment_matters == []


# ---------------------------------------------------------------------------
# CaseDetail two-layer classification
# ---------------------------------------------------------------------------


class TestCaseDetailClassification:
    """Test CaseDetail with coverage_type and legal_theories."""

    def test_two_layer_classification(self) -> None:
        case = CaseDetail(
            case_name=_sv("In re Acme Corp Securities Lit."),
            coverage_type=_sv(CoverageType.SCA_SIDE_A),
            legal_theories=[
                _sv(LegalTheory.RULE_10B5),
                _sv(LegalTheory.SECTION_11),
            ],
            lead_counsel_tier=_sv_int(1),
            lead_plaintiff_type=_sv("institutional"),
            class_period_days=365,
            judge=_sv("Judge Smith"),
        )
        assert case.coverage_type is not None
        assert case.coverage_type.value == CoverageType.SCA_SIDE_A
        assert len(case.legal_theories) == 2
        assert case.legal_theories[0].value == LegalTheory.RULE_10B5
        assert case.lead_counsel_tier is not None
        assert case.lead_counsel_tier.value == 1
        assert case.class_period_days == 365

    def test_backward_compat_fields(self) -> None:
        case = CaseDetail(
            case_name=_sv("Test"),
            status=_sv(CaseStatus.ACTIVE),
            allegations=[_sv("10b-5")],
        )
        assert case.status is not None
        assert case.status.value == CaseStatus.ACTIVE
        assert len(case.allegations) == 1


# ---------------------------------------------------------------------------
# SECEnforcementPipeline
# ---------------------------------------------------------------------------


class TestSECEnforcementPipeline:
    """Test SECEnforcementPipeline with pipeline stages."""

    def test_pipeline_stages(self) -> None:
        pipe = SECEnforcementPipeline(
            highest_confirmed_stage=_sv(EnforcementStage.WELLS_NOTICE),
            pipeline_signals=[
                _sv("Wells notice disclosed in 10-K"),
                _sv("Comment letters on revenue recognition"),
            ],
            comment_letter_count=_sv_int(3),
            comment_letter_topics=[_sv("revenue"), _sv("goodwill")],
            industry_sweep_detected=_sv_bool(False),
        )
        assert pipe.highest_confirmed_stage is not None
        assert pipe.highest_confirmed_stage.value == EnforcementStage.WELLS_NOTICE
        assert len(pipe.pipeline_signals) == 2
        assert pipe.comment_letter_count is not None
        assert pipe.comment_letter_count.value == 3

    def test_backward_compat_alias(self) -> None:
        assert SECEnforcement is SECEnforcementPipeline

    def test_backward_compat_fields(self) -> None:
        pipe = SECEnforcementPipeline(
            pipeline_position=_sv("INVESTIGATION"),
            aaer_count=_sv_int(2),
        )
        assert pipe.pipeline_position is not None
        assert pipe.pipeline_position.value == "INVESTIGATION"


# ---------------------------------------------------------------------------
# Litigation details sub-models
# ---------------------------------------------------------------------------


class TestLitigationDetailModels:
    """Test all litigation_details.py sub-models instantiate cleanly."""

    def test_regulatory_proceeding(self) -> None:
        rp = RegulatoryProceeding(
            agency=_sv("DOJ"),
            proceeding_type=_sv("investigation"),
            status=_sv("active"),
            penalties=_sv_float(5_000_000.0),
        )
        assert rp.agency is not None
        assert rp.agency.value == "DOJ"

    def test_deal_litigation(self) -> None:
        dl = DealLitigation(
            deal_name=_sv("Acme-Widget Merger"),
            litigation_type=_sv("merger_objection"),
            filing_date=_sv_date(date(2025, 6, 15)),
        )
        assert dl.deal_name is not None
        assert dl.deal_name.value == "Acme-Widget Merger"

    def test_workforce_product_environmental(self) -> None:
        wpe = WorkforceProductEnvironmental(
            employment_matters=[_sv("Age discrimination suit")],
            product_recalls=[_sv("Widget recall Q3 2025")],
            cybersecurity_incidents=[_sv("Data breach Jan 2025")],
        )
        assert len(wpe.employment_matters) == 1
        assert len(wpe.product_recalls) == 1
        assert len(wpe.cybersecurity_incidents) == 1

    def test_forum_provisions(self) -> None:
        fp = ForumProvisions(
            has_federal_forum=_sv_bool(True),
            has_exclusive_forum=_sv_bool(True),
            source_document=_sv("Certificate of Incorporation"),
        )
        assert fp.has_federal_forum is not None
        assert fp.has_federal_forum.value is True

    def test_defense_assessment(self) -> None:
        da = DefenseAssessment(
            pslra_safe_harbor_usage=_sv("STRONG"),
            overall_defense_strength=_sv("MODERATE"),
        )
        assert da.pslra_safe_harbor_usage is not None
        assert da.overall_defense_strength is not None
        assert isinstance(da.forum_provisions, ForumProvisions)

    def test_industry_claim_pattern(self) -> None:
        icp = IndustryClaimPattern(
            legal_theory=_sv(LegalTheory.RULE_10B5),
            sic_range=_sv("7370-7379"),
            this_company_exposed=_sv_bool(True),
            contagion_risk=_sv_bool(True),
        )
        assert icp.this_company_exposed is not None
        assert icp.this_company_exposed.value is True

    def test_sol_window(self) -> None:
        sol = SOLWindow(
            claim_type="10b-5",
            trigger_date=date(2024, 1, 15),
            sol_years=2,
            repose_years=5,
            sol_expiry=date(2026, 1, 15),
            repose_expiry=date(2029, 1, 15),
            sol_open=True,
            repose_open=True,
            window_open=True,
        )
        assert sol.claim_type == "10b-5"
        assert sol.sol_years == 2
        assert sol.repose_years == 5

    def test_contingent_liability(self) -> None:
        cl = ContingentLiability(
            description=_sv("Patent infringement claim"),
            asc_450_classification=_sv("reasonably_possible"),
            range_low=_sv_float(10_000_000.0),
            range_high=_sv_float(50_000_000.0),
        )
        assert cl.asc_450_classification is not None
        assert cl.asc_450_classification.value == "reasonably_possible"

    def test_whistleblower_indicator(self) -> None:
        wi = WhistleblowerIndicator(
            indicator_type=_sv("sec_whistleblower"),
            significance=_sv("HIGH"),
            date_identified=_sv_date(date(2025, 3, 1)),
        )
        assert wi.indicator_type is not None
        assert wi.indicator_type.value == "sec_whistleblower"

    def test_litigation_timeline_event(self) -> None:
        lte = LitigationTimelineEvent(
            event_date=date(2025, 1, 10),
            event_type=_sv("case_filing"),
            severity=_sv("HIGH"),
            related_case=_sv("In re Acme Corp"),
        )
        assert lte.event_date == date(2025, 1, 10)
        assert lte.event_type is not None
        assert lte.event_type.value == "case_filing"


# ---------------------------------------------------------------------------
# StrEnum values
# ---------------------------------------------------------------------------


class TestStrEnums:
    """Test StrEnum types for string compatibility."""

    def test_coverage_type_values(self) -> None:
        assert CoverageType.SCA_SIDE_A == "SCA_SIDE_A"
        assert len(CoverageType) == 10

    def test_legal_theory_values(self) -> None:
        assert LegalTheory.RULE_10B5 == "RULE_10B5"
        assert len(LegalTheory) == 12

    def test_enforcement_stage_values(self) -> None:
        assert EnforcementStage.NONE == "NONE"
        assert EnforcementStage.ENFORCEMENT_ACTION == "ENFORCEMENT_ACTION"
        assert len(EnforcementStage) == 6

    def test_case_status_values(self) -> None:
        assert CaseStatus.ACTIVE == "ACTIVE"
        assert len(CaseStatus) == 5


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------


class TestSerialization:
    """Test LitigationLandscape JSON serialization round-trip."""

    def test_serialize_deserialize(self) -> None:
        ll = LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("Test Case"),
                    coverage_type=_sv(CoverageType.SCA_SIDE_A),
                ),
            ],
            active_matter_count=_sv_int(5),
            litigation_summary=_sv("Summary text"),
        )
        json_str = ll.model_dump_json()
        restored = LitigationLandscape.model_validate_json(json_str)
        assert len(restored.securities_class_actions) == 1
        assert restored.active_matter_count is not None
        assert restored.active_matter_count.value == 5
        assert restored.litigation_summary is not None
        assert restored.litigation_summary.value == "Summary text"

    def test_full_model_dump(self) -> None:
        ll = LitigationLandscape()
        data = ll.model_dump()
        assert "sec_enforcement" in data
        assert "defense" in data
        assert "workforce_product_environmental" in data
        assert "sol_map" in data


# ---------------------------------------------------------------------------
# Config file loading
# ---------------------------------------------------------------------------


class TestConfigFiles:
    """Test config JSON files load and have correct structure."""

    def test_lead_counsel_tiers_loads(self) -> None:
        path = CONFIG_DIR / "lead_counsel_tiers.json"
        assert path.exists(), f"Missing: {path}"
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "tier_1" in data
        assert "tier_2" in data
        assert "tier_3_default" in data
        assert "match_strategy" in data
        assert len(data["tier_1"]) >= 5
        assert len(data["tier_2"]) >= 5
        assert data["match_strategy"] == "substring"

    def test_claim_types_loads(self) -> None:
        path = CONFIG_DIR / "claim_types.json"
        assert path.exists(), f"Missing: {path}"
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "claim_types" in data
        ct = data["claim_types"]
        assert "10b-5" in ct
        assert "Section_11" in ct
        assert "derivative" in ct
        assert "FCPA" in ct
        # Validate structure
        for key, val in ct.items():
            assert "display_name" in val, f"{key} missing display_name"
            assert "sol_years" in val, f"{key} missing sol_years"
            assert "repose_years" in val, f"{key} missing repose_years"
            assert "sol_trigger" in val, f"{key} missing sol_trigger"
            assert "repose_trigger" in val, f"{key} missing repose_trigger"
            assert "coverage_type" in val, f"{key} missing coverage_type"

    def test_industry_theories_loads(self) -> None:
        path = CONFIG_DIR / "industry_theories.json"
        assert path.exists(), f"Missing: {path}"
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "industry_theories" in data
        theories = data["industry_theories"]
        assert len(theories) >= 8
        # Validate structure of each entry
        for sic_range, entry in theories.items():
            assert "-" in sic_range, f"SIC range {sic_range} missing dash"
            assert "industry" in entry, f"{sic_range} missing industry"
            assert "theories" in entry, f"{sic_range} missing theories"
            for theory in entry["theories"]:
                assert "theory" in theory
                assert "description" in theory
                assert "legal_basis" in theory


# ---------------------------------------------------------------------------
# Filing section extraction: Item 3 and Item 1A
# ---------------------------------------------------------------------------


# Synthetic 10-K text for testing section extraction.
SAMPLE_10K_TEXT = """
TABLE OF CONTENTS

Item 1. Business
Item 1A. Risk Factors
Item 1B. Unresolved Staff Comments
Item 2. Properties
Item 3. Legal Proceedings
Item 4. Mine Safety Disclosures
Item 5. Market for Registrant's Common Equity
Item 6. [Reserved]
Item 7. Management's Discussion and Analysis

PART I

Item 1. Business

""" + ("Acme Corporation is a leading provider of widgets. " * 30) + """

Item 1A. Risk Factors

""" + (
    "We face risks related to market conditions, "
    "competition, and regulatory changes. "
) * 30 + """

Item 1B. Unresolved Staff Comments

None.

Item 2. Properties

We own facilities in Delaware and California.

Item 3. Legal Proceedings

""" + (
    "The Company is currently a defendant in several securities class "
    "action lawsuits alleging violations of Sections 10(b) and 20(a) "
    "of the Securities Exchange Act of 1934. The complaints allege that "
    "the Company made materially false and misleading statements regarding "
    "its business prospects and financial condition. "
) * 10 + """

Item 4. Mine Safety Disclosures

Not applicable.

Item 7. Management's Discussion and Analysis of Financial Condition

""" + ("Revenue increased 15% year over year driven by widget sales growth. " * 30) + """

Item 7A. Quantitative and Qualitative Disclosures About Market Risk

Interest rate risk is minimal.

Item 9A. Controls and Procedures

Management assessed the effectiveness of internal controls.

Item 9B. Other Information

None.

Item 10. Directors, Executive Officers and Corporate Governance
"""


class TestFilingSectionExtraction:
    """Test Item 3 and Item 1A extraction from filing text."""

    def test_item3_extraction(self) -> None:
        sections = extract_10k_sections(SAMPLE_10K_TEXT)
        assert "item3" in sections, f"item3 not found. Keys: {list(sections.keys())}"
        assert "10-K_item3" in sections
        assert "securities class action" in sections["item3"].lower()

    def test_item1a_extraction(self) -> None:
        sections = extract_10k_sections(SAMPLE_10K_TEXT)
        assert "item1a" in sections, f"item1a not found. Keys: {list(sections.keys())}"
        assert "10-K_item1a" in sections
        assert "risk" in sections["item1a"].lower()

    def test_existing_sections_still_work(self) -> None:
        """Regression: Existing item1, item7, item9a still parse."""
        sections = extract_10k_sections(SAMPLE_10K_TEXT)
        assert "item1" in sections
        assert "item7" in sections
        # item9a text may be too short (< 200 chars) to extract
        # so we don't assert it -- just confirm no crash

    def test_item3_does_not_include_item4(self) -> None:
        sections = extract_10k_sections(SAMPLE_10K_TEXT)
        if "item3" in sections:
            assert "mine safety" not in sections["item3"].lower()

    def test_item1a_does_not_include_item1b(self) -> None:
        sections = extract_10k_sections(SAMPLE_10K_TEXT)
        if "item1a" in sections:
            assert "unresolved staff comments" not in sections["item1a"].lower()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case tests for model robustness."""

    @pytest.mark.parametrize(
        "status",
        [CaseStatus.ACTIVE, CaseStatus.SETTLED, CaseStatus.DISMISSED],
    )
    def test_case_status_in_case_detail(self, status: CaseStatus) -> None:
        case = CaseDetail(status=_sv(status))
        assert case.status is not None
        assert case.status.value == status

    def test_empty_litigation_landscape_json(self) -> None:
        ll = LitigationLandscape()
        data = json.loads(ll.model_dump_json())
        assert isinstance(data, dict)
        assert data["securities_class_actions"] == []
        assert data["active_matter_count"] is None
