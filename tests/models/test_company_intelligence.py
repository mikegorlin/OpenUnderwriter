"""Tests for company intelligence Pydantic models.

Validates ConcentrationDimension, SupplyChainDependency, PeerSCARecord,
SectorDOConcern models plus RiskFactorProfile backward compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_concentration_dimension_validates() -> None:
    """ConcentrationDimension validates with all fields."""
    from do_uw.models.company_intelligence import ConcentrationDimension

    dim = ConcentrationDimension(
        dimension="Customer",
        level="HIGH",
        key_data="Top customer = 15% revenue",
        do_implication="Revenue concentration creates 10b-5 exposure if key customer loss concealed",
        source="10-K Item 1A",
    )
    assert dim.dimension == "Customer"
    assert dim.level == "HIGH"
    assert dim.key_data == "Top customer = 15% revenue"
    assert dim.do_implication != ""
    assert dim.source == "10-K Item 1A"


def test_concentration_dimension_defaults() -> None:
    """ConcentrationDimension has sensible defaults."""
    from do_uw.models.company_intelligence import ConcentrationDimension

    dim = ConcentrationDimension(dimension="Geographic")
    assert dim.level == "MEDIUM"
    assert dim.key_data == ""
    assert dim.do_implication == ""
    assert dim.source == ""


def test_supply_chain_dependency_validates() -> None:
    """SupplyChainDependency validates with all fields."""
    from do_uw.models.company_intelligence import SupplyChainDependency

    dep = SupplyChainDependency(
        provider="TSMC",
        dependency_type="sole-source",
        concentration="HIGH",
        switching_cost="HIGH",
        do_exposure="Supply disruption creates revenue miss SCA",
        source="10-K Item 1",
    )
    assert dep.provider == "TSMC"
    assert dep.dependency_type == "sole-source"
    assert dep.concentration == "HIGH"
    assert dep.switching_cost == "HIGH"
    assert dep.do_exposure != ""


def test_supply_chain_dependency_defaults() -> None:
    """SupplyChainDependency has sensible defaults."""
    from do_uw.models.company_intelligence import SupplyChainDependency

    dep = SupplyChainDependency()
    assert dep.provider == ""
    assert dep.dependency_type == ""
    assert dep.concentration == "MEDIUM"
    assert dep.switching_cost == "MEDIUM"
    assert dep.do_exposure == ""


def test_peer_sca_record_validates() -> None:
    """PeerSCARecord validates with all fields."""
    from do_uw.models.company_intelligence import PeerSCARecord

    rec = PeerSCARecord(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        case_caption="In re Microsoft Securities Litigation",
        filing_date="2024-01-15",
        status="active",
        settlement_amount_m=150.0,
        allegation_type="accounting",
    )
    assert rec.ticker == "MSFT"
    assert rec.company_name == "Microsoft Corporation"
    assert rec.status == "active"
    assert rec.settlement_amount_m == 150.0


def test_peer_sca_record_optional_settlement() -> None:
    """PeerSCARecord allows None settlement."""
    from do_uw.models.company_intelligence import PeerSCARecord

    rec = PeerSCARecord(
        ticker="AAPL",
        filing_date="2024-06-01",
        status="dismissed",
    )
    assert rec.settlement_amount_m is None
    assert rec.allegation_type == ""


def test_sector_do_concern_validates() -> None:
    """SectorDOConcern validates with all fields."""
    from do_uw.models.company_intelligence import SectorDOConcern

    concern = SectorDOConcern(
        concern="Interchange litigation risk",
        sector_relevance="HIGH",
        company_exposure="MEDIUM",
        do_implication="MDL interchange fee litigation creates ongoing D&O exposure",
    )
    assert concern.concern == "Interchange litigation risk"
    assert concern.sector_relevance == "HIGH"
    assert concern.do_implication != ""


def test_sector_do_concern_defaults() -> None:
    """SectorDOConcern has sensible defaults."""
    from do_uw.models.company_intelligence import SectorDOConcern

    concern = SectorDOConcern()
    assert concern.concern == ""
    assert concern.sector_relevance == "MEDIUM"
    assert concern.company_exposure == "MEDIUM"
    assert concern.do_implication == ""


def test_risk_factor_profile_backward_compatible() -> None:
    """RiskFactorProfile new fields have defaults (backward compat)."""
    from do_uw.models.state import RiskFactorProfile

    # Create WITHOUT new fields -- should still work
    profile = RiskFactorProfile(
        title="Litigation risk",
        category="LITIGATION",
        severity="HIGH",
    )
    assert profile.classification == "STANDARD"
    assert profile.do_implication == ""
    # Existing fields unchanged
    assert profile.title == "Litigation risk"
    assert profile.category == "LITIGATION"
    assert profile.severity == "HIGH"


def test_risk_factor_profile_new_fields() -> None:
    """RiskFactorProfile accepts new classification and do_implication."""
    from do_uw.models.state import RiskFactorProfile

    profile = RiskFactorProfile(
        title="Novel AI risk",
        category="AI",
        severity="HIGH",
        is_new_this_year=True,
        classification="NOVEL",
        do_implication="AI liability creates novel SCA theory",
    )
    assert profile.classification == "NOVEL"
    assert profile.do_implication == "AI liability creates novel SCA theory"


def test_sector_do_concerns_json_loads() -> None:
    """sector_do_concerns.json loads and has required structure."""
    config_path = Path(__file__).parent.parent.parent / "config" / "sector_do_concerns.json"
    assert config_path.exists(), f"Config file not found: {config_path}"

    with open(config_path) as f:
        data = json.load(f)

    assert "sectors" in data
    assert len(data["sectors"]) >= 8, f"Expected 8+ sectors, got {len(data['sectors'])}"

    for sector in data["sectors"]:
        assert "name" in sector
        assert "sic_ranges" in sector
        assert "concerns" in sector
        assert len(sector["concerns"]) >= 3, f"Sector {sector['name']} needs 3+ concerns"

        for concern in sector["concerns"]:
            assert "concern" in concern
            assert "relevance" in concern
            assert "do_implication" in concern
            assert concern["do_implication"] != "", f"Empty do_implication in {sector['name']}"


def test_sector_do_concerns_technology_coverage() -> None:
    """sector_do_concerns.json covers Technology sector with SIC 7372."""
    config_path = Path(__file__).parent.parent.parent / "config" / "sector_do_concerns.json"
    with open(config_path) as f:
        data = json.load(f)

    tech_sector = None
    for sector in data["sectors"]:
        for sic_range in sector["sic_ranges"]:
            if sic_range[0] <= 7372 <= sic_range[1]:
                tech_sector = sector
                break
    assert tech_sector is not None, "No sector covers SIC 7372 (Technology)"


def test_sector_do_concerns_chemicals_coverage() -> None:
    """sector_do_concerns.json covers a sector including SIC 2851 (Chemicals)."""
    config_path = Path(__file__).parent.parent.parent / "config" / "sector_do_concerns.json"
    with open(config_path) as f:
        data = json.load(f)

    found = False
    for sector in data["sectors"]:
        for sic_range in sector["sic_ranges"]:
            if sic_range[0] <= 2851 <= sic_range[1]:
                found = True
                break
    assert found, "No sector covers SIC 2851 (Chemicals)"


def test_all_models_importable() -> None:
    """All 4 models can be imported from company_intelligence."""
    from do_uw.models.company_intelligence import (
        ConcentrationDimension,
        PeerSCARecord,
        SectorDOConcern,
        SupplyChainDependency,
    )

    assert ConcentrationDimension is not None
    assert SupplyChainDependency is not None
    assert PeerSCARecord is not None
    assert SectorDOConcern is not None
