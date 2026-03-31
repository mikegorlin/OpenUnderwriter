"""Tests for supply chain dependency extraction from 10-K text."""

from __future__ import annotations

import pytest


def test_sole_source_detection() -> None:
    """Detects 'sole source' supplier mentions."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = (
        "We rely on TSMC as our sole source supplier for the manufacture "
        "of our advanced semiconductor chips. If TSMC were unable to meet "
        "our production requirements, we would face significant delays."
    )
    deps = extract_supply_chain(text, "")
    assert len(deps) >= 1
    assert any(d.dependency_type == "sole-source" for d in deps)


def test_single_supplier_detection() -> None:
    """Detects 'single supplier' mentions."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = (
        "Certain critical components are obtained from a single supplier. "
        "We have no alternative sources for these specialized materials."
    )
    deps = extract_supply_chain(text, "")
    assert len(deps) >= 1


def test_key_supplier_detection() -> None:
    """Detects 'key supplier' mentions."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = (
        "We depend on several key suppliers for raw materials used in "
        "our manufacturing processes. Loss of any key supplier could "
        "disrupt our operations."
    )
    deps = extract_supply_chain("", text)
    assert len(deps) >= 1


def test_empty_input_returns_empty() -> None:
    """Empty text inputs return empty list."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    assert extract_supply_chain("", "") == []
    assert extract_supply_chain("", "", company_name="ACME") == []


def test_no_supply_chain_text_returns_empty() -> None:
    """Text without supply chain keywords returns empty."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = "Our company generates revenue from software licensing and consulting services."
    assert extract_supply_chain(text, "") == []


def test_switching_cost_high_for_no_alternative() -> None:
    """'No alternative' language maps to HIGH switching cost."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = (
        "We rely on a sole source supplier for critical components. "
        "There are no alternative sources currently available for these parts."
    )
    deps = extract_supply_chain(text, "")
    assert len(deps) >= 1
    high_cost = [d for d in deps if d.switching_cost == "HIGH"]
    assert len(high_cost) >= 1


def test_do_exposure_populated() -> None:
    """D&O exposure field is populated for detected dependencies."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = "We depend on a single supplier for our key raw materials."
    deps = extract_supply_chain(text, "")
    for d in deps:
        assert d.do_exposure != "", "D&O exposure should be populated"


def test_source_field_set() -> None:
    """Source field tracks which section the dependency was found in."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    deps = extract_supply_chain(
        "We rely on a sole source supplier for components.",
        "",
    )
    if deps:
        assert deps[0].source != ""


def test_multiple_dependencies_found() -> None:
    """Multiple distinct dependency mentions are captured."""
    from do_uw.stages.extract.supply_chain_extract import extract_supply_chain

    text = (
        "We rely on a sole source supplier for silicon wafers. "
        "We also depend on a single supplier for our display panels. "
        "Our key supplier for batteries has limited alternatives."
    )
    deps = extract_supply_chain(text, "")
    assert len(deps) >= 2
