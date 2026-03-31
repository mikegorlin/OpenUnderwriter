"""Validation tests for XBRL concept config integrity.

Tests that xbrl_concepts.json is well-formed, has required fields,
and maintains backward compatibility with existing concepts.
"""

from __future__ import annotations

import json
from pathlib import Path

from do_uw.stages.extract.xbrl_mapping import load_xbrl_mapping

# Path to the config file
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "brain" / "config" / "xbrl_concepts.json"

# The original 40 concepts that must remain unchanged
_ORIGINAL_CONCEPTS = {
    "revenue", "cost_of_revenue", "gross_profit", "operating_income",
    "net_income", "eps_basic", "eps_diluted", "total_assets",
    "total_liabilities", "stockholders_equity", "current_assets",
    "current_liabilities", "cash_and_equivalents", "accounts_receivable",
    "inventory", "property_plant_equipment", "goodwill", "intangible_assets",
    "long_term_debt", "short_term_debt", "retained_earnings", "total_debt",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
    "capital_expenditures", "depreciation_amortization", "interest_expense",
    "income_tax_expense", "research_development", "sga_expense", "ebit",
    "shares_outstanding", "dividends_paid", "share_repurchases",
    "accounts_payable", "deferred_revenue", "operating_lease_liabilities",
    "weighted_avg_shares_basic", "weighted_avg_shares_diluted",
    "comprehensive_income", "other_income", "restructuring_charges",
    "impairment_charges", "income_from_operations", "pretax_income",
    "minority_interest", "preferred_dividends", "working_capital", "ebitda",
}

_VALID_SIGNS = {"positive", "negative", "any"}
_VALID_STATEMENTS = {"income", "balance_sheet", "cash_flow", "derived"}
_REQUIRED_FIELDS = {
    "canonical_name", "xbrl_tags", "unit", "period_type",
    "statement", "description", "expected_sign",
}


class TestXbrlConceptsConfigIntegrity:
    """Schema validation for xbrl_concepts.json."""

    def test_config_loads_successfully(self) -> None:
        mapping = load_xbrl_mapping()
        assert len(mapping) >= 110, f"Expected >= 110 concepts, got {len(mapping)}"

    def test_every_concept_has_required_fields(self) -> None:
        mapping = load_xbrl_mapping()
        for name, concept in mapping.items():
            for field in _REQUIRED_FIELDS:
                assert field in concept, (
                    f"Concept '{name}' missing required field '{field}'"
                )

    def test_expected_sign_values_valid(self) -> None:
        mapping = load_xbrl_mapping()
        for name, concept in mapping.items():
            sign = concept["expected_sign"]
            assert sign in _VALID_SIGNS, (
                f"Concept '{name}' has invalid expected_sign '{sign}', "
                f"must be one of {_VALID_SIGNS}"
            )

    def test_all_original_concepts_present(self) -> None:
        mapping = load_xbrl_mapping()
        for name in _ORIGINAL_CONCEPTS:
            assert name in mapping, f"Original concept '{name}' missing from config"

    def test_original_concepts_tags_unchanged(self) -> None:
        """Existing 40 concepts must keep their original xbrl_tags."""
        with _CONFIG_PATH.open() as f:
            raw = json.load(f)

        # Spot-check a few critical concepts
        assert raw["revenue"]["xbrl_tags"][0] == "Revenues"
        assert raw["total_assets"]["xbrl_tags"][0] == "Assets"
        assert raw["net_income"]["xbrl_tags"][0] == "NetIncomeLoss"
        assert raw["operating_cash_flow"]["xbrl_tags"][0] == "NetCashProvidedByUsedInOperatingActivities"

    def test_load_xbrl_mapping_returns_expected_sign(self) -> None:
        mapping = load_xbrl_mapping()
        for name, concept in mapping.items():
            assert "expected_sign" in concept, (
                f"load_xbrl_mapping() result for '{name}' missing expected_sign"
            )

    def test_covers_all_statement_types(self) -> None:
        mapping = load_xbrl_mapping()
        statements_found = set()
        for concept in mapping.values():
            statements_found.add(concept["statement"])
        for stmt in ("income", "balance_sheet", "cash_flow", "derived"):
            assert stmt in statements_found, (
                f"No concepts with statement='{stmt}' found"
            )

    def test_no_duplicate_canonical_names(self) -> None:
        mapping = load_xbrl_mapping()
        names = [c["canonical_name"] for c in mapping.values()]
        assert len(names) == len(set(names)), (
            f"Duplicate canonical_names found: "
            f"{[n for n in names if names.count(n) > 1]}"
        )

    def test_non_derived_concepts_have_tags(self) -> None:
        mapping = load_xbrl_mapping()
        for name, concept in mapping.items():
            if concept["statement"] != "derived":
                assert len(concept["xbrl_tags"]) > 0, (
                    f"Non-derived concept '{name}' has empty xbrl_tags"
                )

    def test_derived_concepts_have_empty_tags(self) -> None:
        mapping = load_xbrl_mapping()
        for name, concept in mapping.items():
            if concept["statement"] == "derived":
                assert concept["xbrl_tags"] == [], (
                    f"Derived concept '{name}' should have empty xbrl_tags"
                )
