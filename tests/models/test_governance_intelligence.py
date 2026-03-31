"""Tests for governance intelligence Pydantic models.

Validates PriorCompany, OfficerSCAExposure, OfficerBackground,
ShareholderRightsProvision, ShareholderRightsInventory, PerInsiderActivity.
"""

from __future__ import annotations

import pytest


class TestPriorCompany:
    """PriorCompany model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import PriorCompany

        pc = PriorCompany(
            company_name="Acme Corp",
            role="CFO",
            years="2015-2020",
            start_year=2015,
            end_year=2020,
        )
        assert pc.company_name == "Acme Corp"
        assert pc.role == "CFO"
        assert pc.start_year == 2015
        assert pc.end_year == 2020

    def test_optional_years(self) -> None:
        from do_uw.models.governance_intelligence import PriorCompany

        pc = PriorCompany(company_name="Widgets Inc", role="CEO", years="2018-present")
        assert pc.start_year is None
        assert pc.end_year is None

    def test_defaults(self) -> None:
        from do_uw.models.governance_intelligence import PriorCompany

        pc = PriorCompany()
        assert pc.company_name == ""
        assert pc.role == ""
        assert pc.years == ""
        assert pc.start_year is None
        assert pc.end_year is None


class TestOfficerSCAExposure:
    """OfficerSCAExposure model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import OfficerSCAExposure

        exp = OfficerSCAExposure(
            company_name="Acme Corp",
            case_caption="In re Acme Securities Litigation",
            filing_date="2019-06-15",
            class_period_start="2018-03-15",
            class_period_end="2019-11-30",
            officer_role_at_time="CFO",
            settlement_amount_m=45.0,
        )
        assert exp.company_name == "Acme Corp"
        assert exp.case_caption == "In re Acme Securities Litigation"
        assert exp.settlement_amount_m == 45.0

    def test_optional_settlement(self) -> None:
        from do_uw.models.governance_intelligence import OfficerSCAExposure

        exp = OfficerSCAExposure(
            company_name="Test",
            case_caption="Test v. Test",
        )
        assert exp.settlement_amount_m is None


class TestOfficerBackground:
    """OfficerBackground model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import OfficerBackground

        ob = OfficerBackground(
            name="Jane Doe",
            title="CFO",
            suitability="HIGH",
            suitability_reason="Full bio + litigation search complete",
        )
        assert ob.name == "Jane Doe"
        assert ob.title == "CFO"
        assert ob.is_serial_defendant is False
        assert ob.suitability == "HIGH"
        assert ob.prior_companies == []
        assert ob.sca_exposures == []
        assert ob.personal_litigation == []

    def test_suitability_values(self) -> None:
        from do_uw.models.governance_intelligence import OfficerBackground

        for level in ("HIGH", "MEDIUM", "LOW"):
            ob = OfficerBackground(name="Test", title="CEO", suitability=level)
            assert ob.suitability == level

    def test_serial_defendant_flag(self) -> None:
        from do_uw.models.governance_intelligence import (
            OfficerBackground,
            OfficerSCAExposure,
        )

        ob = OfficerBackground(
            name="Bad Actor",
            title="CEO",
            is_serial_defendant=True,
            sca_exposures=[
                OfficerSCAExposure(
                    company_name="FailCo",
                    case_caption="In re FailCo",
                    class_period_start="2017-01-01",
                    class_period_end="2018-12-31",
                )
            ],
        )
        assert ob.is_serial_defendant is True
        assert len(ob.sca_exposures) == 1


class TestShareholderRightsProvision:
    """ShareholderRightsProvision model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import ShareholderRightsProvision

        p = ShareholderRightsProvision(
            provision_name="Board Classification",
            status="Yes",
            details="Staggered board with 3-year terms",
            defense_strength="Protective",
            do_implication="Staggered terms limit hostile takeover but increase Revlon duty scrutiny",
        )
        assert p.provision_name == "Board Classification"
        assert p.status == "Yes"
        assert p.defense_strength == "Protective"

    def test_defaults(self) -> None:
        from do_uw.models.governance_intelligence import ShareholderRightsProvision

        p = ShareholderRightsProvision()
        assert p.provision_name == ""
        assert p.status == ""
        assert p.details == ""
        assert p.defense_strength == ""
        assert p.do_implication == ""


class TestShareholderRightsInventory:
    """ShareholderRightsInventory model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import (
            ShareholderRightsInventory,
            ShareholderRightsProvision,
        )

        provisions = [
            ShareholderRightsProvision(
                provision_name="Board Classification",
                status="Yes",
                defense_strength="Protective",
                do_implication="test",
            ),
            ShareholderRightsProvision(
                provision_name="Poison Pill",
                status="No",
                defense_strength="Shareholder-Friendly",
                do_implication="test",
            ),
            ShareholderRightsProvision(
                provision_name="Proxy Access",
                status="Yes",
                defense_strength="Shareholder-Friendly",
                do_implication="test",
            ),
        ]
        inv = ShareholderRightsInventory(
            provisions=provisions,
            overall_defense_posture="Moderate",
            protective_count=1,
            shareholder_friendly_count=2,
        )
        assert len(inv.provisions) == 3
        assert inv.overall_defense_posture == "Moderate"
        assert inv.protective_count == 1
        assert inv.shareholder_friendly_count == 2

    def test_defense_posture_values(self) -> None:
        from do_uw.models.governance_intelligence import ShareholderRightsInventory

        for posture in ("Strong", "Moderate", "Weak"):
            inv = ShareholderRightsInventory(overall_defense_posture=posture)
            assert inv.overall_defense_posture == posture

    def test_defaults(self) -> None:
        from do_uw.models.governance_intelligence import ShareholderRightsInventory

        inv = ShareholderRightsInventory()
        assert inv.provisions == []
        assert inv.overall_defense_posture == ""
        assert inv.protective_count == 0
        assert inv.shareholder_friendly_count == 0


class TestPerInsiderActivity:
    """PerInsiderActivity model validation."""

    def test_basic_creation(self) -> None:
        from do_uw.models.governance_intelligence import PerInsiderActivity

        pia = PerInsiderActivity(
            name="John Smith",
            position="CEO",
            total_sold_usd=5_000_000.0,
            total_sold_pct_os=0.15,
            tx_count=12,
            has_10b5_1=True,
            activity_period_start="2025-01-15",
            activity_period_end="2025-12-20",
        )
        assert pia.name == "John Smith"
        assert pia.total_sold_usd == 5_000_000.0
        assert pia.total_sold_pct_os == 0.15
        assert pia.tx_count == 12
        assert pia.has_10b5_1 is True

    def test_optional_pct_os(self) -> None:
        from do_uw.models.governance_intelligence import PerInsiderActivity

        pia = PerInsiderActivity(
            name="Test",
            position="CFO",
            total_sold_usd=1000.0,
            tx_count=1,
            has_10b5_1=False,
            activity_period_start="2025-01-01",
            activity_period_end="2025-06-30",
        )
        assert pia.total_sold_pct_os is None

    def test_defaults(self) -> None:
        from do_uw.models.governance_intelligence import PerInsiderActivity

        pia = PerInsiderActivity()
        assert pia.name == ""
        assert pia.position == ""
        assert pia.total_sold_usd == 0.0
        assert pia.total_sold_pct_os is None
        assert pia.tx_count == 0
        assert pia.has_10b5_1 is False


class TestBoardProfileCumulativeVoting:
    """BoardProfile.cumulative_voting field validation."""

    def test_cumulative_voting_exists(self) -> None:
        from do_uw.models.governance import BoardProfile

        bp = BoardProfile()
        assert hasattr(bp, "cumulative_voting")
        assert bp.cumulative_voting is None

    def test_cumulative_voting_set(self) -> None:
        from do_uw.models.common import Confidence, SourcedValue
        from do_uw.models.governance import BoardProfile
        from datetime import datetime, UTC

        bp = BoardProfile(
            cumulative_voting=SourcedValue(
                value=False,
                source="DEF 14A 2025-04-15",
                confidence=Confidence.HIGH,
                as_of=datetime.now(tz=UTC),
            )
        )
        assert bp.cumulative_voting is not None
        assert bp.cumulative_voting.value is False
