"""Tests for named_archetypes.yaml validation and signal integrity.

Validates that the 6 named archetypes load correctly, conform to
PatternDefinition Pydantic schema, and reference real signal IDs
from brain/signals/*.yaml (with future_signal.* exceptions).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from do_uw.brain.brain_schema import PatternDefinition

# Path to the named archetypes YAML
ARCHETYPES_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "do_uw"
    / "brain"
    / "framework"
    / "named_archetypes.yaml"
)

# Brain signals directory
SIGNALS_DIR = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "do_uw"
    / "brain"
    / "signals"
)


def _load_all_signal_ids() -> set[str]:
    """Load all signal IDs from brain/signals/*.yaml files."""
    signal_ids: set[str] = set()
    for yaml_file in SIGNALS_DIR.rglob("*.yaml"):
        try:
            content = yaml.safe_load(yaml_file.read_text())
            if isinstance(content, list):
                for entry in content:
                    if isinstance(entry, dict) and "id" in entry:
                        signal_ids.add(entry["id"])
        except Exception:
            continue
    return signal_ids


@pytest.fixture(scope="module")
def archetypes() -> list[dict]:
    """Load archetypes YAML."""
    raw = yaml.safe_load(ARCHETYPES_PATH.read_text())
    return raw["archetypes"]


@pytest.fixture(scope="module")
def all_signal_ids() -> set[str]:
    """Load all signal IDs from brain signals corpus."""
    return _load_all_signal_ids()


class TestArchetypesLoad:
    """Tests for YAML loading and basic structure."""

    def test_yaml_loads_successfully(self, archetypes: list[dict]) -> None:
        """Archetypes YAML loads without error."""
        assert isinstance(archetypes, list)

    def test_has_6_archetypes(self, archetypes: list[dict]) -> None:
        """YAML defines exactly 6 archetypes."""
        assert len(archetypes) == 6

    def test_unique_ids(self, archetypes: list[dict]) -> None:
        """All archetype IDs are unique."""
        ids = [a["id"] for a in archetypes]
        assert len(ids) == len(set(ids))


class TestArchetypeSchema:
    """Tests for PatternDefinition Pydantic validation."""

    def test_all_validate_against_schema(self, archetypes: list[dict]) -> None:
        """Every archetype validates against PatternDefinition."""
        for arch in archetypes:
            parsed = PatternDefinition.model_validate(arch)
            assert parsed.id == arch["id"]

    def test_all_have_recommendation_floor(
        self, archetypes: list[dict]
    ) -> None:
        """Every archetype has recommendation_floor set."""
        for arch in archetypes:
            assert arch.get("recommendation_floor") is not None, (
                f"{arch['id']} missing recommendation_floor"
            )

    def test_minimum_matches_at_least_3(self, archetypes: list[dict]) -> None:
        """Every archetype has minimum_matches >= 3."""
        for arch in archetypes:
            assert arch["minimum_matches"] >= 3, (
                f"{arch['id']} has minimum_matches={arch['minimum_matches']} (need >= 3)"
            )


class TestArchetypeSignals:
    """Tests for signal ID validity."""

    def test_real_signals_exist_in_corpus(
        self, archetypes: list[dict], all_signal_ids: set[str]
    ) -> None:
        """Non-future_signal signal IDs exist in brain/signals/ YAML."""
        for arch in archetypes:
            for sig_id in arch["required_signals"]:
                if sig_id.startswith("future_signal."):
                    continue
                assert sig_id in all_signal_ids, (
                    f"{arch['id']} references missing signal: {sig_id}"
                )

    def test_ai_mirage_has_future_signals(
        self, archetypes: list[dict]
    ) -> None:
        """AI Mirage archetype has future_signal.* entries."""
        ai_mirage = next(a for a in archetypes if a["id"] == "ai_mirage")
        future_signals = [
            s for s in ai_mirage["required_signals"]
            if s.startswith("future_signal.")
        ]
        assert len(future_signals) >= 3, (
            f"ai_mirage has only {len(future_signals)} future signals (need >= 3)"
        )

    def test_each_archetype_has_required_signals(
        self, archetypes: list[dict]
    ) -> None:
        """Each archetype has at least minimum_matches required_signals."""
        for arch in archetypes:
            assert len(arch["required_signals"]) >= arch["minimum_matches"], (
                f"{arch['id']} has {len(arch['required_signals'])} signals "
                f"but minimum_matches={arch['minimum_matches']}"
            )


class TestArchetypeContent:
    """Tests for archetype content quality."""

    def test_all_have_epistemology(self, archetypes: list[dict]) -> None:
        """Every archetype has an epistemology section."""
        for arch in archetypes:
            assert arch.get("epistemology") is not None, (
                f"{arch['id']} missing epistemology"
            )

    def test_all_have_historical_cases(self, archetypes: list[dict]) -> None:
        """Every archetype has at least 2 historical case references."""
        for arch in archetypes:
            cases = arch.get("historical_cases", [])
            assert len(cases) >= 2, (
                f"{arch['id']} has only {len(cases)} historical cases (need >= 2)"
            )

    def test_expected_archetype_ids(self, archetypes: list[dict]) -> None:
        """All 6 expected archetype IDs are present."""
        expected = {
            "desperate_growth_trap",
            "governance_vacuum",
            "post_spac_hangover",
            "accounting_time_bomb",
            "regulatory_reckoning",
            "ai_mirage",
        }
        actual = {a["id"] for a in archetypes}
        assert actual == expected
