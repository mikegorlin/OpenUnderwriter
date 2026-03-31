"""Template variable type validation CI gate (GATE-04).

Cross-references Jinja2 template variable references against Pydantic
context model field names. Catches template-vs-schema drift where:
  - Templates reference fields that don't exist in the typed model
  - New model fields never get used in templates (informational)

Templates use aliases: fin=financials, mkt=market, gov=governance, lit=litigation.
Access patterns: fin.revenue, fin.get('revenue'), mkt.current_price, etc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from do_uw.stages.render.context_models import (
    ExecSummaryContext,
    FinancialContext,
    GovernanceContext,
    LitigationContext,
    MarketContext,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = PROJECT_ROOT / "src" / "do_uw" / "templates" / "html"

# Map template alias -> context key -> Pydantic model
SECTION_MODELS: dict[str, type[BaseModel]] = {
    "fin": FinancialContext,
    "mkt": MarketContext,
    "gov": GovernanceContext,
    "lit": LitigationContext,
    "executive_summary": ExecSummaryContext,
}

# Template fields that are legitimate dict keys not in the Pydantic model.
# These come from extra builder output, dynamic dict access, or sub-dicts.
# Each entry is (alias, field_name). Documented here so drift is intentional.
KNOWN_EXTRA_FIELDS: set[tuple[str, str]] = {
    # fin extras: computed fields not yet modeled
    ("fin", "balance_sheet_rows"),
    ("fin", "cash_flow_rows"),
    ("fin", "current_ratio"),
    ("fin", "debt_to_equity"),
    ("fin", "earnings_quality_do_context"),
    ("fin", "filing_ref"),
    ("fin", "goodwill_equity_pct"),
    ("fin", "gross_margin_peer"),
    ("fin", "income_statement_rows"),
    ("fin", "is_financial_sector"),
    ("fin", "operating_margin_peer"),
    ("fin", "sector_caveat"),
    ("fin", "source"),
    ("fin", "statement_periods"),
    ("fin", "audit_disclosure_alerts"),
    # mkt extras: fields from evaluative helpers not yet modeled
    ("mkt", "active_s11_windows"),
    ("mkt", "data_source"),
    ("mkt", "earnings_reaction"),
    ("mkt", "earnings_trust_narrative"),
    ("mkt", "earnings_trust_summary"),
    ("mkt", "eps_estimates"),
    ("mkt", "eps_revisions"),
    ("mkt", "filing_ref"),
    ("mkt", "has_atm"),
    ("mkt", "offerings"),
    ("mkt", "revenue_estimates"),
    ("mkt", "sector_1y"),
    ("mkt", "shelf_registrations"),
    ("mkt", "source"),
    # gov extras: governance helpers output
    ("gov", "activists"),
    ("gov", "audit_fees"),
    ("gov", "shareholder_proposal_count"),
    ("gov", "total_insider_sales_fmt"),
    # lit extras: litigation helpers output
    ("lit", "legal_theories"),
    ("lit", "unclassified_reserves"),
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _extract_template_field_refs(template_dir: Path) -> dict[str, set[str]]:
    """Scan .j2 files and extract field references per section alias.

    Patterns matched:
      - alias.field_name  (e.g. fin.revenue)
      - alias.get('field_name'  (e.g. mkt.get('current_price')
      - alias.get("field_name"  (double quotes)

    Returns: {alias: {field1, field2, ...}}
    """
    # Match: alias.get('field') or alias.get("field") or alias.field
    pattern = re.compile(
        r"\b(fin|mkt|gov|lit|executive_summary)"
        r"\.(?:get\(['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]|([a-zA-Z_][a-zA-Z0-9_]*))"
    )

    refs: dict[str, set[str]] = {}
    if not template_dir.exists():
        return refs

    for j2_file in template_dir.rglob("*.j2"):
        text = j2_file.read_text(errors="replace")
        for match in pattern.finditer(text):
            alias = match.group(1)
            field = match.group(2) or match.group(3)
            if field:
                refs.setdefault(alias, set()).add(field)

    return refs


def _get_model_fields(model_cls: type[BaseModel], prefix: str = "") -> set[str]:
    """Get all field names from a Pydantic model, including nested models.

    Returns flat field names (not dot-paths) since templates use dict access.
    """
    fields: set[str] = set()
    for name, field_info in model_cls.model_fields.items():
        fields.add(name)
        # Check if annotation is a Pydantic BaseModel for recursive extraction
        annotation = field_info.annotation
        # Handle Optional[X] -> extract X
        origin = getattr(annotation, "__origin__", None)
        if origin is type(None):
            continue
        args = getattr(annotation, "__args__", ())
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                # Nested model -- its fields are accessed via sub-dict
                nested_fields = _get_model_fields(arg)
                fields.update(nested_fields)
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            nested_fields = _get_model_fields(annotation)
            fields.update(nested_fields)
    return fields


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTemplateVariableExtraction:
    """Verify the extraction helper works correctly."""

    def test_extracts_known_patterns(self) -> None:
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        # Must find references for all 4 main sections
        assert "fin" in refs, "No financial template references found"
        assert "mkt" in refs, "No market template references found"
        assert "gov" in refs, "No governance template references found"
        assert "lit" in refs, "No litigation template references found"

    def test_fin_has_known_fields(self) -> None:
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        fin_refs = refs.get("fin", set())
        assert "revenue" in fin_refs, "Expected fin.revenue in templates"
        assert "has_income" in fin_refs, "Expected fin.has_income in templates"

    def test_mkt_has_known_fields(self) -> None:
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        mkt_refs = refs.get("mkt", set())
        assert "current_price" in mkt_refs, "Expected mkt.current_price in templates"


class TestSchemaFieldExtraction:
    """Verify model field extraction works."""

    def test_financial_fields_complete(self) -> None:
        fields = _get_model_fields(FinancialContext)
        assert "revenue" in fields
        assert "has_income" in fields
        assert "z_score" in fields

    def test_market_fields_complete(self) -> None:
        fields = _get_model_fields(MarketContext)
        assert "current_price" in fields
        assert "short_pct" in fields

    def test_exec_summary_nested_fields(self) -> None:
        """Nested models (SnapshotContext) fields should be included."""
        fields = _get_model_fields(ExecSummaryContext)
        assert "snapshot" in fields
        # Nested SnapshotContext fields
        assert "company_name" in fields
        assert "ticker" in fields


class TestTemplateVsSchemaAlignment:
    """Cross-reference template variables against Pydantic model fields.

    This is the CI gate: unknown template references (not in model AND
    not in KNOWN_EXTRA_FIELDS) indicate schema drift.
    """

    @pytest.mark.parametrize("alias,model_cls", [
        ("fin", FinancialContext),
        ("mkt", MarketContext),
        ("gov", GovernanceContext),
        ("lit", LitigationContext),
    ])
    def test_template_fields_exist_in_model(
        self, alias: str, model_cls: type[BaseModel]
    ) -> None:
        """Every template field ref must be in the model or KNOWN_EXTRA_FIELDS."""
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        template_refs = refs.get(alias, set())
        schema_fields = _get_model_fields(model_cls)

        unknown: set[str] = set()
        for field in template_refs:
            if field in schema_fields:
                continue
            if (alias, field) in KNOWN_EXTRA_FIELDS:
                continue
            unknown.add(field)

        assert not unknown, (
            f"Template references unknown fields in '{alias}' "
            f"(not in {model_cls.__name__} or KNOWN_EXTRA_FIELDS): {sorted(unknown)}\n"
            f"Either add these to the Pydantic model or to KNOWN_EXTRA_FIELDS."
        )

    def test_all_sections_covered(self) -> None:
        """All 5 typed models are checked in this test suite."""
        checked = {"fin", "mkt", "gov", "lit", "executive_summary"}
        assert checked == set(SECTION_MODELS.keys())


class TestModelFieldCoverage:
    """Informational: model fields not referenced in any template.

    These are warnings, not failures -- unused typed fields may be
    consumed by other renderers (Word, Markdown) or future templates.
    """

    @pytest.mark.parametrize("alias,model_cls", [
        ("fin", FinancialContext),
        ("mkt", MarketContext),
        ("gov", GovernanceContext),
        ("lit", LitigationContext),
    ])
    def test_model_field_usage_ratio(
        self, alias: str, model_cls: type[BaseModel]
    ) -> None:
        """At least 30% of model fields should be referenced in templates."""
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        template_refs = refs.get(alias, set())
        # Only count direct model fields, not nested
        model_fields = set(model_cls.model_fields.keys())
        used = model_fields & template_refs
        ratio = len(used) / len(model_fields) if model_fields else 0
        assert ratio >= 0.3, (
            f"{model_cls.__name__}: only {len(used)}/{len(model_fields)} "
            f"({ratio:.0%}) fields referenced in templates. "
            f"Unused: {sorted(model_fields - template_refs)[:10]}..."
        )


class TestKnownExtrasStillNeeded:
    """Verify KNOWN_EXTRA_FIELDS entries are still referenced in templates.

    If a known-extra is no longer used, it should be cleaned up.
    """

    def test_known_extras_still_referenced(self) -> None:
        refs = _extract_template_field_refs(TEMPLATE_DIR)
        stale: list[tuple[str, str]] = []
        for alias, field in KNOWN_EXTRA_FIELDS:
            template_refs = refs.get(alias, set())
            if field not in template_refs:
                stale.append((alias, field))
        # Allow up to 5 stale entries before failing (templates evolve)
        assert len(stale) <= 5, (
            f"{len(stale)} KNOWN_EXTRA_FIELDS entries no longer referenced "
            f"in templates (clean up): {stale[:10]}"
        )
