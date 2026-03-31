"""Tests for 45->36 subsection reorganization.

Validates that signals.json and enrichment_data.py reflect the
36-subsection structure after absorbing/merging subsections.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Valid subsection IDs for the 36-subsection structure
# ---------------------------------------------------------------------------

VALID_SUBSECTION_IDS = {
    "1.1", "1.2", "1.3", "1.4", "1.6", "1.8", "1.9", "1.11",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8",
    "4.1", "4.2", "4.3", "4.4",
    "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7",
}

# IDs that should NOT appear anywhere (absorbed, merged, or removed)
REMOVED_SUBSECTION_IDS = {
    "1.5",   # Geographic Footprint -> absorbed into 1.2 + 1.3
    "1.7",   # Competitive Position -> absorbed into 1.2 + 1.8
    "1.10",  # Company-Specific Risk -> merged into 1.9
    "4.5",   # Activist (old) -> renumbered to 4.4
    "4.6",   # Disclosure Quality (old) -> merged into 4.3
    "4.7",   # Narrative Analysis (old) -> merged into 4.3
    "4.8",   # Whistleblower (old) -> merged into 4.3
    "4.9",   # Media & External (old) -> absorbed into 1.9
    "5.8",   # Litigation Patterns (old) -> merged into 5.7
    "5.9",   # Sector-Specific Lit (old) -> merged into 5.7
}


@pytest.fixture(scope="module")
def checks_data() -> list[dict[str, object]]:
    """Load signals from signals.json."""
    path = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "brain" / "config" / "signals.json"
    with open(path) as f:
        data = json.load(f)
    return data["signals"]  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def sic_gics_mapping() -> dict[str, object]:
    """Load SIC-GICS mapping config."""
    path = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "brain" / "config" / "sic_gics_mapping.json"
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Structural validation tests
# ---------------------------------------------------------------------------


def test_no_removed_subsection_ids(checks_data: list[dict[str, object]]) -> None:
    """No check should reference any removed/absorbed/merged subsection ID."""
    violations: list[tuple[str, list[str]]] = []
    for check in checks_data:
        signal_id = str(check["id"])
        ids = check.get("v6_subsection_ids", [])
        assert isinstance(ids, list)
        bad = set(ids) & REMOVED_SUBSECTION_IDS  # type: ignore[arg-type]
        if bad:
            violations.append((signal_id, sorted(bad)))

    assert violations == [], (
        f"{len(violations)} checks still reference removed IDs:\n"
        + "\n".join(f"  {cid}: {bad}" for cid, bad in violations[:20])
    )


def test_every_check_has_valid_subsection(checks_data: list[dict[str, object]]) -> None:
    """Every check must have at least one valid subsection ID."""
    missing: list[str] = []
    for check in checks_data:
        signal_id = str(check["id"])
        ids = check.get("v6_subsection_ids", [])
        assert isinstance(ids, list)
        valid = [sid for sid in ids if sid in VALID_SUBSECTION_IDS]
        if not valid:
            missing.append(signal_id)

    assert missing == [], (
        f"{len(missing)} checks have no valid subsection ID:\n"
        + "\n".join(f"  {cid}" for cid in missing[:20])
    )


def test_all_subsection_ids_are_valid(checks_data: list[dict[str, object]]) -> None:
    """Every subsection ID on every check must be in the valid set."""
    invalid: list[tuple[str, str]] = []
    for check in checks_data:
        signal_id = str(check["id"])
        for sid in check.get("v6_subsection_ids", []):
            if sid not in VALID_SUBSECTION_IDS:
                invalid.append((signal_id, str(sid)))

    assert invalid == [], (
        f"{len(invalid)} invalid subsection IDs found:\n"
        + "\n".join(f"  {cid}: {sid}" for cid, sid in invalid[:20])
    )


# ---------------------------------------------------------------------------
# Section 4 reorganization tests
# ---------------------------------------------------------------------------


def test_section4_board_checks_map_to_4_1(checks_data: list[dict[str, object]]) -> None:
    """GOV.BOARD checks should map to 4.1 (People Risk)."""
    for check in checks_data:
        signal_id = str(check["id"])
        if signal_id.startswith("GOV.BOARD."):
            ids = check.get("v6_subsection_ids", [])
            assert "4.1" in ids, f"{signal_id} should map to 4.1, got {ids}"


def test_section4_exec_checks_map_to_4_1(checks_data: list[dict[str, object]]) -> None:
    """EXEC.* and GOV.EXEC.* checks should map to 4.1 (People Risk)."""
    prefixes = ("GOV.EXEC.", "EXEC.PROFILE.", "EXEC.TENURE.", "EXEC.DEPARTURE.", "EXEC.PRIOR_LIT.")
    for check in checks_data:
        signal_id = str(check["id"])
        if any(signal_id.startswith(p) for p in prefixes):
            ids = check.get("v6_subsection_ids", [])
            assert "4.1" in ids, f"{signal_id} should map to 4.1, got {ids}"


def test_section4_pay_checks_map_to_4_2(checks_data: list[dict[str, object]]) -> None:
    """GOV.PAY checks should map to 4.2 (Structural Governance)."""
    for check in checks_data:
        signal_id = str(check["id"])
        if signal_id.startswith("GOV.PAY."):
            ids = check.get("v6_subsection_ids", [])
            assert "4.2" in ids, f"{signal_id} should map to 4.2, got {ids}"


def test_section4_rights_checks_map_to_4_2(checks_data: list[dict[str, object]]) -> None:
    """GOV.RIGHTS checks should map to 4.2 (Structural Governance)."""
    for check in checks_data:
        signal_id = str(check["id"])
        if signal_id.startswith("GOV.RIGHTS."):
            ids = check.get("v6_subsection_ids", [])
            assert "4.2" in ids, f"{signal_id} should map to 4.2, got {ids}"


def test_section4_nlp_checks_map_to_4_3(checks_data: list[dict[str, object]]) -> None:
    """NLP.RISK, NLP.MDA, NLP.DISCLOSURE, NLP.FILING, NLP.WHISTLE -> 4.3 (Transparency)."""
    prefixes = ("NLP.RISK.", "NLP.MDA.", "NLP.DISCLOSURE.", "NLP.FILING.", "NLP.WHISTLE.")
    for check in checks_data:
        signal_id = str(check["id"])
        if any(signal_id.startswith(p) for p in prefixes):
            ids = check.get("v6_subsection_ids", [])
            assert "4.3" in ids, f"{signal_id} should map to 4.3, got {ids}"


def test_section4_activist_checks_map_to_4_4(checks_data: list[dict[str, object]]) -> None:
    """GOV.ACTIVIST checks should map to 4.4 (Activist Pressure)."""
    for check in checks_data:
        signal_id = str(check["id"])
        if signal_id.startswith("GOV.ACTIVIST."):
            ids = check.get("v6_subsection_ids", [])
            assert "4.4" in ids, f"{signal_id} should map to 4.4, got {ids}"


# ---------------------------------------------------------------------------
# Merged subsection tests
# ---------------------------------------------------------------------------


def test_merged_litigation_only_5_7(checks_data: list[dict[str, object]]) -> None:
    """LIT.DEFENSE, LIT.PATTERN, LIT.SECTOR all map to 5.7 (merged)."""
    prefixes = ("LIT.DEFENSE.", "LIT.PATTERN.", "LIT.SECTOR.")
    for check in checks_data:
        signal_id = str(check["id"])
        if any(signal_id.startswith(p) for p in prefixes):
            ids = check.get("v6_subsection_ids", [])
            assert "5.7" in ids, f"{signal_id} should map to 5.7, got {ids}"
            # Should NOT have 5.8 or 5.9
            assert "5.8" not in ids, f"{signal_id} should not have 5.8"
            assert "5.9" not in ids, f"{signal_id} should not have 5.9"


def test_disclosure_checks_consolidated_to_4_3(checks_data: list[dict[str, object]]) -> None:
    """FWRD.DISC and FWRD.NARRATIVE checks map to 4.3 (Transparency)."""
    prefixes = ("FWRD.DISC.", "FWRD.NARRATIVE.")
    for check in checks_data:
        signal_id = str(check["id"])
        if any(signal_id.startswith(p) for p in prefixes):
            ids = check.get("v6_subsection_ids", [])
            assert "4.3" in ids, f"{signal_id} should map to 4.3, got {ids}"


# ---------------------------------------------------------------------------
# SIC-GICS mapping tests
# ---------------------------------------------------------------------------


def test_sic_gics_mapping_loads(sic_gics_mapping: dict[str, object]) -> None:
    """SIC-GICS mapping file loads and has expected structure."""
    assert "mappings" in sic_gics_mapping
    mappings = sic_gics_mapping["mappings"]
    assert isinstance(mappings, dict)
    assert len(mappings) >= 30, f"Expected 30+ entries, got {len(mappings)}"


def test_sic_gics_key_entries(sic_gics_mapping: dict[str, object]) -> None:
    """Expected SIC-GICS mappings are present."""
    mappings = sic_gics_mapping["mappings"]
    assert isinstance(mappings, dict)

    expected = {
        "3571": "45202030",  # Electronic Computers -> Tech Hardware
        "7372": "45103010",  # Prepackaged Software -> Application Software
        "3674": "45301020",  # Semiconductors
        "6021": "40101010",  # National Commercial Banks -> Diversified Banks
        "2834": "35201010",  # Pharmaceutical Preparations
        "5912": "30101010",  # Drug Stores -> Drug Retail
        "7371": "45102010",  # Computer Services -> IT Consulting
    }

    for sic, expected_gics in expected.items():
        assert sic in mappings, f"SIC {sic} missing from mapping"
        assert mappings[sic]["gics"] == expected_gics, (
            f"SIC {sic}: expected GICS {expected_gics}, got {mappings[sic]['gics']}"
        )


def test_sic_gics_entry_structure(sic_gics_mapping: dict[str, object]) -> None:
    """Each mapping entry has gics and gics_name fields."""
    mappings = sic_gics_mapping["mappings"]
    assert isinstance(mappings, dict)
    for sic, entry in mappings.items():
        assert isinstance(entry, dict), f"SIC {sic} entry is not a dict"
        assert "gics" in entry, f"SIC {sic} missing gics field"
        assert "gics_name" in entry, f"SIC {sic} missing gics_name field"
        gics = entry["gics"]
        assert isinstance(gics, str), f"SIC {sic} gics is not a string"
        assert len(gics) == 8, f"SIC {sic} gics '{gics}' is not 8 digits"


# ---------------------------------------------------------------------------
# Enrichment data consistency tests
# ---------------------------------------------------------------------------


def test_subdomain_mappings_use_valid_ids() -> None:
    """SUBDOMAIN_TO_RISK_QUESTIONS only references valid subsection IDs."""
    from do_uw.brain.enrichment_data import SUBDOMAIN_TO_RISK_QUESTIONS

    for key, ids in SUBDOMAIN_TO_RISK_QUESTIONS.items():
        for sid in ids:
            assert sid in VALID_SUBSECTION_IDS, (
                f"SUBDOMAIN_TO_RISK_QUESTIONS['{key}'] has invalid ID '{sid}'"
            )


def test_check_to_risk_questions_use_valid_ids() -> None:
    """CHECK_TO_RISK_QUESTIONS only references valid subsection IDs."""
    from do_uw.brain.enrichment_data import CHECK_TO_RISK_QUESTIONS

    for key, ids in CHECK_TO_RISK_QUESTIONS.items():
        for sid in ids:
            assert sid in VALID_SUBSECTION_IDS, (
                f"CHECK_TO_RISK_QUESTIONS['{key}'] has invalid ID '{sid}'"
            )
