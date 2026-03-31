"""Tests for CompetitiveLandscape Pydantic models.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data
Plan 01: Data model definitions.
"""

from __future__ import annotations

import json

from do_uw.models.competitive_landscape import (
    CompetitiveLandscape,
    MoatDimension,
    PeerRow,
)


class TestPeerRowDefaults:
    """PeerRow() instantiates with empty string defaults."""

    def test_instantiates_with_defaults(self) -> None:
        p = PeerRow()
        assert p.company_name == ""
        assert p.ticker == ""
        assert p.market_cap == ""
        assert p.revenue == ""
        assert p.margin == ""
        assert p.growth_rate == ""
        assert p.rd_spend == ""
        assert p.market_share == ""
        assert p.stock_performance == ""
        assert p.sca_history == ""
        assert p.do_relevance == ""

    def test_construction_with_values(self) -> None:
        p = PeerRow(company_name="Acme", ticker="ACM")
        assert p.company_name == "Acme"
        assert p.ticker == "ACM"
        # Other fields still default
        assert p.market_cap == ""
        assert p.do_relevance == ""


class TestMoatDimensionDefaults:
    """MoatDimension() defaults: present=False, strength="", durability=""."""

    def test_instantiates_with_defaults(self) -> None:
        m = MoatDimension()
        assert m.dimension == ""
        assert m.present is False
        assert m.strength == ""
        assert m.durability == ""
        assert m.evidence == ""
        assert m.do_risk == ""

    def test_construction_with_dimension(self) -> None:
        m = MoatDimension(dimension="Scale")
        assert m.dimension == "Scale"
        assert m.present is False
        assert m.strength == ""
        assert m.durability == ""


class TestCompetitiveLandscapeDefaults:
    """CompetitiveLandscape() instantiates with empty defaults."""

    def test_instantiates_with_defaults(self) -> None:
        cl = CompetitiveLandscape()
        assert cl.peers == []
        assert cl.moat_dimensions == []
        assert cl.competitive_position_narrative == ""
        assert cl.do_commentary == ""


class TestCompetitiveLandscapeSerialization:
    """CompetitiveLandscape with 4 PeerRows serializes to/from JSON."""

    def test_round_trip_json(self) -> None:
        peers = [
            PeerRow(company_name=f"Company {i}", ticker=f"C{i}")
            for i in range(4)
        ]
        cl = CompetitiveLandscape(
            peers=peers,
            moat_dimensions=[
                MoatDimension(dimension="Scale", present=True, strength="Strong"),
            ],
            competitive_position_narrative="Leader in segment",
            do_commentary="Low competitive D&O risk",
        )
        # Serialize to JSON string and back
        json_str = cl.model_dump_json()
        data = json.loads(json_str)
        restored = CompetitiveLandscape.model_validate(data)
        assert len(restored.peers) == 4
        assert restored.peers[0].company_name == "Company 0"
        assert restored.peers[3].ticker == "C3"
        assert len(restored.moat_dimensions) == 1
        assert restored.moat_dimensions[0].dimension == "Scale"
        assert restored.moat_dimensions[0].present is True
        assert restored.moat_dimensions[0].strength == "Strong"
        assert restored.competitive_position_narrative == "Leader in segment"
        assert restored.do_commentary == "Low competitive D&O risk"

    def test_model_dump_dict(self) -> None:
        cl = CompetitiveLandscape(
            peers=[PeerRow(company_name="Test", ticker="TST")],
        )
        d = cl.model_dump()
        assert isinstance(d, dict)
        assert len(d["peers"]) == 1
        assert d["peers"][0]["company_name"] == "Test"


class TestCompetitiveLandscapeJsonSchema:
    """JSON schema generation works for CompetitiveLandscape."""

    def test_json_schema(self) -> None:
        schema = CompetitiveLandscape.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "peers" in schema["properties"]
        assert "moat_dimensions" in schema["properties"]
