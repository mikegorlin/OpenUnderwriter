"""V3 signal migration: populate group, signal_class, field_path, depends_on, provenance.

Reads section YAMLs, field_registry.yaml, and output_manifest.yaml to compute
v3 fields for all 476 signals. Modifies YAML in-place using ruamel.yaml to
preserve comments and formatting.

Usage:
    uv run python src/do_uw/brain/brain_migrate_v3.py              # execute migration
    uv run python src/do_uw/brain/brain_migrate_v3.py --dry-run    # preview changes
    uv run python src/do_uw/brain/brain_migrate_v3.py --stats      # summary only
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_BRAIN_DIR = Path(__file__).parent
_SIGNALS_DIR = _BRAIN_DIR / "signals"
_SECTIONS_DIR = _BRAIN_DIR / "sections"
_MANIFEST_PATH = _BRAIN_DIR / "output_manifest.yaml"
_REGISTRY_PATH = _BRAIN_DIR / "field_registry.yaml"

# Facet values that don't match section IDs -> remap to correct section
_FACET_REMAP: dict[str, str] = {
    "litigation_exposure": "litigation",
    "news_sentiment": "executive_summary",
}

# Section YAML group IDs that differ from manifest group IDs
# Section YAML uses short names; manifest uses prefixed names
_GROUP_REMAP: dict[str, str] = {
    "prior_litigation": "executive_prior_litigation",
    "executive_profiles": "executive_risk_profiles",
    "tenure_stability": "executive_tenure_stability",
    "mda_analysis": "filing_analysis_mda",
    "risk_factor_analysis": "filing_analysis_risk_factors",
    "filing_patterns": "filing_analysis_patterns",
    "early_warning": "forward_looking_early_warning",
    "event_catalysts": "forward_looking_event_catalysts",
    "macro_risks": "forward_looking_macro_risks",
    "disclosure_quality": "forward_looking_disclosure_quality",
    "narrative_coherence": "forward_looking_narrative_coherence",
}


# ---------------------------------------------------------------
# Lookup builders (pure functions)
# ---------------------------------------------------------------


def build_group_lookup(sections_dir: Path) -> dict[str, str]:
    """Map signal_id -> group_id from section YAML facet signal lists."""
    lookup: dict[str, str] = {}
    for yaml_path in sorted(sections_dir.glob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        for facet in data.get("facets", []):
            group_id = facet["id"]
            for sig_id in facet.get("signals", []):
                lookup[sig_id] = group_id
    return lookup


def build_section_groups(sections_dir: Path) -> dict[str, list[str]]:
    """Map section_id -> list of group_ids from section YAML facets."""
    mapping: dict[str, list[str]] = {}
    for yaml_path in sorted(sections_dir.glob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        section_id = data.get("id", yaml_path.stem)
        mapping[section_id] = [f["id"] for f in data.get("facets", [])]
    return mapping


def build_manifest_groups(manifest_path: Path) -> set[str]:
    """Extract all valid group IDs from the output manifest."""
    data = yaml.safe_load(manifest_path.read_text())
    groups: set[str] = set()
    for section in data.get("sections", []):
        for facet in section.get("facets", []):
            gid = facet.get("id", "")
            if gid:
                groups.add(gid)
    return groups


def build_field_registry(registry_path: Path) -> dict[str, dict[str, Any]]:
    """Load field_registry.yaml as dict of field definitions."""
    data = yaml.safe_load(registry_path.read_text())
    return data.get("fields", {})


def build_signal_index(signals_dir: Path) -> dict[str, dict[str, Any]]:
    """Map signal_id -> raw dict for cross-referencing."""
    index: dict[str, dict[str, Any]] = {}
    for yaml_path in sorted(signals_dir.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "id" in entry:
                    index[entry["id"]] = entry
    return index


# ---------------------------------------------------------------
# Group inference for unmapped signals
# ---------------------------------------------------------------

# Signal ID prefix patterns -> group assignment heuristics
# These map signal ID patterns to groups within each section
_PREFIX_GROUP_MAP: dict[str, str] = {
    # Financial Health
    "FIN.PROFIT.revenue": "annual_comparison",
    "FIN.PROFIT.earnings": "annual_comparison",
    "FIN.PROFIT.margins": "annual_comparison",
    "FIN.PROFIT.segment": "key_metrics",
    "FIN.PROFIT": "key_metrics",
    "FIN.LIQ": "key_metrics",
    "FIN.DEBT": "distress_indicators",
    "FIN.SECTOR": "key_metrics",
    "FIN.ACCT.going_concern": "distress_indicators",
    "FIN.ACCT.restatement": "audit_profile",
    "FIN.ACCT.auditor": "audit_profile",
    "FIN.ACCT.internal_control": "audit_profile",
    "FIN.ACCT": "earnings_quality",
    "FIN.FORENSIC.fis_composite": "forensic_composites",
    "FIN.FORENSIC.dechow": "forensic_composites",
    "FIN.FORENSIC.montier": "forensic_composites",
    "FIN.FORENSIC.enhanced_sloan": "forensic_composites",
    "FIN.FORENSIC.beneish_dechow": "forensic_composites",
    "FIN.FORENSIC.dsri": "forensic_dashboard",
    "FIN.FORENSIC.aqi": "forensic_dashboard",
    "FIN.FORENSIC.tata": "forensic_dashboard",
    "FIN.FORENSIC.m_score": "forensic_dashboard",
    "FIN.FORENSIC.sloan": "forensic_dashboard",
    "FIN.FORENSIC.cash_flow_manipulation": "forensic_dashboard",
    "FIN.FORENSIC.sbc_dilution": "forensic_dashboard",
    "FIN.FORENSIC.non_gaap": "forensic_dashboard",
    "FIN.FORENSIC.goodwill": "forensic_dashboard",
    "FIN.FORENSIC.intangible": "forensic_dashboard",
    "FIN.FORENSIC.off_balance": "forensic_dashboard",
    "FIN.FORENSIC.cash_conversion": "forensic_dashboard",
    "FIN.FORENSIC.working_capital": "forensic_dashboard",
    "FIN.FORENSIC.deferred_revenue": "forensic_dashboard",
    "FIN.FORENSIC.channel_stuffing": "forensic_dashboard",
    "FIN.FORENSIC.margin_compression": "forensic_dashboard",
    "FIN.FORENSIC.ocf_revenue": "forensic_dashboard",
    "FIN.FORENSIC.roic": "forensic_dashboard",
    "FIN.FORENSIC.acquisition_effectiveness": "forensic_dashboard",
    "FIN.FORENSIC.buyback": "forensic_dashboard",
    "FIN.FORENSIC.dividend": "forensic_dashboard",
    "FIN.FORENSIC.interest_coverage": "forensic_dashboard",
    "FIN.FORENSIC.debt_maturity": "forensic_dashboard",
    "FIN.FORENSIC.etr": "forensic_dashboard",
    "FIN.FORENSIC.deferred_tax": "forensic_dashboard",
    "FIN.FORENSIC.pension": "forensic_dashboard",
    "FIN.FORENSIC.serial_acquirer": "forensic_dashboard",
    "FIN.FORENSIC.acquisition_to_revenue": "forensic_dashboard",
    "FIN.FORENSIC.level3": "forensic_dashboard",
    "FIN.FORENSIC.related_party": "forensic_dashboard",
    "FIN.FORENSIC.accrual": "forensic_dashboard",
    "FIN.FORENSIC": "forensic_dashboard",
    "FIN.TEMPORAL": "quarterly_trends",
    "FIN.GUIDE": "key_metrics",
    "FIN.PEER": "peer_matrix",
    "FIN.QUALITY": "earnings_quality",
    # Governance
    "GOV.BOARD.independence": "board_composition",
    "GOV.BOARD.size": "board_composition",
    "GOV.BOARD.tenure": "board_composition",
    "GOV.BOARD.attendance": "board_composition",
    "GOV.BOARD.diversity": "board_composition",
    "GOV.BOARD.expertise": "board_composition",
    "GOV.BOARD.meeting": "board_composition",
    "GOV.BOARD.busy": "board_composition",
    "GOV.BOARD.interlock": "board_composition",
    "GOV.BOARD.refreshment": "board_composition",
    "GOV.BOARD": "board_composition",
    "GOV.EXEC.ceo": "compensation_analysis",
    "GOV.EXEC.cfo": "compensation_analysis",
    "GOV.EXEC": "compensation_analysis",
    "GOV.PAY": "compensation_analysis",
    "GOV.AUDIT": "transparency_disclosure",
    "GOV.RIGHTS": "structural_governance",
    "GOV.EFFECT": "structural_governance",
    "GOV.INSIDER": "ownership_structure",
    "GOV.ACTIVIST": "activist_risk",
    # Litigation
    "LIT.SCA.active": "active_matters",
    "LIT.SCA.exposure": "active_matters",
    "LIT.SCA.policy": "active_matters",
    "LIT.SCA.search": "active_matters",
    "LIT.SCA.historical": "settlement_history",
    "LIT.SCA.prior": "settlement_history",
    "LIT.SCA.settle": "settlement_history",
    "LIT.SCA.dismiss": "settlement_history",
    "LIT.SCA.demand": "settlement_history",
    "LIT.SCA.prefiling": "settlement_history",
    "LIT.SCA": "active_matters",
    "LIT.REG.sec": "sec_enforcement",
    "LIT.REG.wells": "sec_enforcement",
    "LIT.REG.comment": "sec_enforcement",
    "LIT.REG.subpoena": "sec_enforcement",
    "LIT.REG.civil": "sec_enforcement",
    "LIT.REG.consent": "sec_enforcement",
    "LIT.REG.cease": "sec_enforcement",
    "LIT.REG.deferred": "sec_enforcement",
    "LIT.REG.doj": "sec_enforcement",
    "LIT.REG.ftc": "sec_enforcement",
    "LIT.REG.state": "sec_enforcement",
    "LIT.REG.cfpb": "sec_enforcement",
    "LIT.REG": "sec_enforcement",
    "LIT.DEFENSE": "defense_strength",
    "LIT.PATTERN": "industry_patterns",
    "LIT.SECTOR": "industry_patterns",
    "LIT.OTHER.whistleblower": "whistleblower",
    "LIT.OTHER.product": "workforce_product_env",
    "LIT.OTHER.environmental": "workforce_product_env",
    "LIT.OTHER.employment": "workforce_product_env",
    "LIT.OTHER.ip": "workforce_product_env",
    "LIT.OTHER.deriv": "derivative_suits",
    "LIT.OTHER.sol": "sol_analysis",
    "LIT.OTHER.contingent": "contingent_liabilities",
    "LIT.OTHER": "workforce_product_env",
    # Market Activity
    "STOCK.PRICE": "stock_performance",
    "STOCK.PATTERN": "stock_drops",
    "STOCK.SHORT": "short_interest",
    "STOCK.ANALYST": "analyst_consensus",
    "STOCK.LIT": "analyst_consensus",
    "STOCK.INSIDER": "insider_trading",
    "STOCK.TRADE": "insider_trading",
    "STOCK.OWN": "ownership_structure",
    "STOCK.VALUATION": "analyst_consensus",
    # Executive Risk
    "EXEC.PROFILE": "executive_risk_profiles",
    "EXEC.CEO": "executive_risk_profiles",
    "EXEC.CFO": "executive_risk_profiles",
    "EXEC.AGGREGATE": "executive_risk_profiles",
    "EXEC.TENURE": "executive_tenure_stability",
    "EXEC.DEPARTURE": "executive_tenure_stability",
    "EXEC.INSIDER": "executive_insider_trading",
    "EXEC.PRIOR_LIT": "executive_prior_litigation",
    # Business Profile
    "BIZ.CLASS": "risk_classification",
    "BIZ.MODEL.description": "business_description",
    "BIZ.MODEL.revenue_segment": "revenue_segments",
    "BIZ.MODEL.revenue_geo": "geographic_footprint",
    "BIZ.MODEL": "business_description",
    "BIZ.SIZE": "company_profile",
    "BIZ.STRUCT": "business_description",
    "BIZ.COMP": "company_checks",
    "BIZ.DEPEND.customer": "customer_concentration",
    "BIZ.DEPEND.supplier": "supplier_concentration",
    "BIZ.DEPEND": "business_description",
    "BIZ.UNI": "business_description",
    # Forward Looking
    "FWRD.WARN.glassdoor": "forward_looking_early_warning",
    "FWRD.WARN.indeed": "forward_looking_early_warning",
    "FWRD.WARN.blind": "forward_looking_early_warning",
    "FWRD.WARN.app": "forward_looking_early_warning",
    "FWRD.WARN.g2": "forward_looking_early_warning",
    "FWRD.WARN.trustpilot": "forward_looking_early_warning",
    "FWRD.WARN.social": "forward_looking_early_warning",
    "FWRD.WARN.job": "forward_looking_early_warning",
    "FWRD.WARN.linkedin": "forward_looking_early_warning",
    "FWRD.WARN.journalism": "forward_looking_early_warning",
    "FWRD.WARN.ai_revenue": "forward_looking_early_warning",
    "FWRD.WARN.hyperscaler": "forward_looking_early_warning",
    "FWRD.WARN.gpu": "forward_looking_early_warning",
    "FWRD.WARN.data_center": "forward_looking_early_warning",
    "FWRD.WARN": "forward_looking_early_warning",
    "FWRD.GUID": "forward_looking_disclosure_quality",
    "FWRD.FORECAST": "forward_looking_disclosure_quality",
    "FWRD.NARRATIVE": "forward_looking_narrative_coherence",
    "FWRD.DISC": "forward_looking_disclosure_quality",
    "FWRD.SPAC": "forward_looking_event_catalysts",
    "FWRD.MERGER": "forward_looking_event_catalysts",
    "FWRD.MA": "forward_looking_event_catalysts",
    "FWRD.ACQ": "forward_looking_event_catalysts",
    "FWRD.EVENT": "forward_looking_event_catalysts",
    "FWRD.MACRO": "forward_looking_macro_risks",
    # NLP
    "NLP": "nlp_analysis",
    # BASE signals (foundational)
    "BASE.XBRL": "statement_tables",
    "BASE.FILING": "filing_analysis_patterns",
    "BASE.FORENSIC": "forensic_dashboard",
    "BASE.LIT": "active_matters",
    "BASE.NEWS": "key_findings",
    "BASE.STOCK": "stock_performance",
    "BASE.MARKET.stock_price": "stock_performance",
    "BASE.MARKET.institutional": "ownership_structure",
    "BASE.MARKET.insider_trading": "insider_trading",
    "BASE.MARKET": "stock_performance",
    "BASE.PEER": "peer_group",
}


def _infer_group_from_prefix(signal_id: str) -> str:
    """Infer group from signal ID prefix, using longest-match-first."""
    best_match = ""
    best_group = ""
    for prefix, group in _PREFIX_GROUP_MAP.items():
        if signal_id.startswith(prefix) and len(prefix) > len(best_match):
            best_match = prefix
            best_group = group
    return best_group


def resolve_group(
    signal_id: str,
    facet: str,
    explicit_lookup: dict[str, str],
    section_groups: dict[str, list[str]],
    manifest_groups: set[str],
) -> tuple[str, str]:
    """Resolve group for a signal. Returns (group_id, resolution_method).

    Priority:
    1. Explicit section YAML mapping
    2. Prefix-based inference
    3. First group from the signal's facet/section (fallback)
    """
    # 1. Explicit mapping from section YAML (with remap to manifest IDs)
    if signal_id in explicit_lookup:
        group = explicit_lookup[signal_id]
        group = _GROUP_REMAP.get(group, group)
        return group, "explicit"

    # 2. Prefix-based inference
    prefix_group = _infer_group_from_prefix(signal_id)
    prefix_group = _GROUP_REMAP.get(prefix_group, prefix_group)
    if prefix_group and prefix_group in manifest_groups:
        return prefix_group, "prefix"

    # 3. Fallback: use facet value to find section, then use first group
    section_id = _FACET_REMAP.get(facet, facet)
    groups = section_groups.get(section_id, [])
    if groups:
        group = _GROUP_REMAP.get(groups[0], groups[0])
        return group, "facet_fallback"

    # Last resort: use facet value itself if it's a valid manifest group
    remapped = _GROUP_REMAP.get(facet, facet)
    if remapped in manifest_groups:
        return remapped, "facet_direct"

    return "", "unresolved"


# ---------------------------------------------------------------
# Signal class inference
# ---------------------------------------------------------------

# Signals that are composites/convergences -> inference
_INFERENCE_PATTERNS = [
    re.compile(r"^FIN\.FORENSIC\.fis_composite$"),
    re.compile(r"^FIN\.FORENSIC\.dechow_f_score$"),
    re.compile(r"^FIN\.FORENSIC\.montier_c_score$"),
    re.compile(r"^FIN\.FORENSIC\.enhanced_sloan$"),
    re.compile(r"^FIN\.FORENSIC\.beneish_dechow_convergence$"),
    re.compile(r"^FWRD\.DISC\.disclosure_quality_composite$"),
    re.compile(r"^FWRD\.NARRATIVE\.narrative_coherence_composite$"),
]


def infer_signal_class(signal: dict[str, Any]) -> str:
    """Infer signal_class from v2 type, work_type, or existing signal_class fields."""
    sig_id = signal.get("id", "")

    # Already migrated signals: preserve existing signal_class
    if signal.get("signal_class") in ("foundational", "inference"):
        return signal["signal_class"]

    # Foundational signals (v2 type field)
    if signal.get("type") == "foundational":
        return "foundational"

    # Foundational by ID prefix (for idempotent re-runs after type field removed)
    if sig_id.startswith("BASE."):
        return "foundational"

    # Inference signals: work_type=infer OR known composite patterns
    if signal.get("work_type") == "infer":
        return "inference"
    for pat in _INFERENCE_PATTERNS:
        if pat.match(sig_id):
            return "inference"

    return "evaluative"


# ---------------------------------------------------------------
# depends_on and field_path computation
# ---------------------------------------------------------------

# Map field_registry field_key -> foundational signal that provides the data
_FIELD_KEY_TO_FOUNDATIONAL: dict[str, str] = {
    # Financial fields -> XBRL foundational signals
    "current_ratio": "BASE.XBRL.balance_sheet",
    "cash_ratio": "BASE.XBRL.balance_sheet",
    "interest_coverage": "BASE.XBRL.income_statement",
    "cash_burn_months": "BASE.XBRL.cash_flow",
    "restatements": "BASE.XBRL.balance_sheet",
    "board_independence": "BASE.FILING.DEF14A",
    "say_on_pay_pct": "BASE.FILING.DEF14A",
    "filing_13d_count": "BASE.FILING.DEF14A",
    "active_sca_count": "BASE.LIT.scac",
    "contingent_liabilities_total": "BASE.LIT.10k_item3",
    "product_liability_count": "BASE.LIT.10k_item3",
    "decline_from_high": "BASE.STOCK.price_history",
    "short_interest_pct": "BASE.STOCK.price_history",
    "pe_ratio": "BASE.STOCK.price_history",
    "customer_concentration": "BASE.FILING.10K",
    "subsidiary_count": "BASE.FILING.10K",
    "market_cap": "BASE.STOCK.price_history",
    # Forensic fields -> forensic foundational signals
    "forensic_goodwill_to_assets": "BASE.FORENSIC.balance_sheet",
    "forensic_intangible_concentration": "BASE.FORENSIC.balance_sheet",
    "forensic_off_balance_sheet": "BASE.FORENSIC.balance_sheet",
    "forensic_cash_conversion_cycle": "BASE.FORENSIC.balance_sheet",
    "forensic_working_capital_volatility": "BASE.FORENSIC.balance_sheet",
    "forensic_deferred_revenue_divergence": "BASE.FORENSIC.revenue",
    "forensic_channel_stuffing": "BASE.FORENSIC.revenue",
    "forensic_margin_compression": "BASE.FORENSIC.revenue",
    "forensic_ocf_revenue_ratio": "BASE.FORENSIC.revenue",
    "forensic_roic_trend": "BASE.FORENSIC.capital_alloc",
    "forensic_acquisition_effectiveness": "BASE.FORENSIC.capital_alloc",
    "forensic_buyback_timing": "BASE.FORENSIC.capital_alloc",
    "forensic_dividend_sustainability": "BASE.FORENSIC.capital_alloc",
    "forensic_interest_coverage_trend": "BASE.FORENSIC.debt_tax",
    "forensic_debt_maturity_concentration": "BASE.FORENSIC.debt_tax",
    "forensic_etr_anomaly": "BASE.FORENSIC.debt_tax",
    "forensic_deferred_tax_growth": "BASE.FORENSIC.debt_tax",
    "forensic_pension_underfunding": "BASE.FORENSIC.debt_tax",
    "forensic_beneish_dsri": "BASE.FORENSIC.beneish",
    "forensic_beneish_aqi": "BASE.FORENSIC.beneish",
    "forensic_beneish_tata": "BASE.FORENSIC.beneish",
    "forensic_beneish_composite": "BASE.FORENSIC.beneish",
    "forensic_sloan_accruals": "BASE.FORENSIC.earnings",
    "forensic_cash_flow_manipulation": "BASE.FORENSIC.earnings",
    "forensic_sbc_dilution": "BASE.FORENSIC.earnings",
    "forensic_non_gaap_gap": "BASE.FORENSIC.earnings",
    "forensic_serial_acquirer": "BASE.FORENSIC.ma",
    "forensic_goodwill_growth_rate": "BASE.FORENSIC.ma",
    "forensic_acquisition_to_revenue": "BASE.FORENSIC.ma",
}


def compute_depends_on(
    signal: dict[str, Any],
    signal_class: str,
    signal_index: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    """Compute depends_on for a signal."""
    if signal_class == "foundational":
        return []

    field_key = (signal.get("data_strategy") or {}).get("field_key", "")
    if not field_key:
        return []

    foundational_id = _FIELD_KEY_TO_FOUNDATIONAL.get(field_key, "")
    if foundational_id and foundational_id in signal_index:
        return [{"signal": foundational_id, "field": field_key}]

    return []


def compute_field_path(signal: dict[str, Any]) -> str:
    """Compute field_path from data_strategy.field_key (registry key approach)."""
    ds = signal.get("data_strategy") or {}
    return ds.get("field_key", "")


# ---------------------------------------------------------------
# Provenance expansion
# ---------------------------------------------------------------


def expand_provenance(
    signal: dict[str, Any],
    group: str,
) -> dict[str, Any]:
    """Expand provenance block with v3 audit trail fields."""
    prov = dict(signal.get("provenance", {}))

    # data_source from display.source_type
    display = signal.get("display") or {}
    source_type = display.get("source_type", "")
    if not prov.get("data_source"):
        prov["data_source"] = source_type

    # threshold_provenance
    threshold = signal.get("threshold") or {}
    threshold_type = threshold.get("type", "")
    if threshold_type and threshold_type not in ("info", "display"):
        if "threshold_provenance" not in prov:
            prov["threshold_provenance"] = {
                "source": "standard",
                "rationale": "",
            }
    elif "threshold_provenance" not in prov:
        prov["threshold_provenance"] = {
            "source": "unattributed",
            "rationale": "",
        }

    # render_target from group
    if not prov.get("render_target"):
        prov["render_target"] = group

    # formula left empty
    if "formula" not in prov:
        prov["formula"] = ""

    return prov


# ---------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------


def compute_v3_fields(
    signal: dict[str, Any],
    explicit_lookup: dict[str, str],
    section_groups: dict[str, list[str]],
    manifest_groups: set[str],
    signal_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute all v3 fields for a signal. Returns dict of updates."""
    sig_id = signal.get("id", "")
    facet = signal.get("facet", "")

    # group
    group, method = resolve_group(
        sig_id, facet, explicit_lookup, section_groups, manifest_groups
    )

    # signal_class
    signal_class = infer_signal_class(signal)

    # field_path
    field_path = compute_field_path(signal)

    # depends_on
    depends_on = compute_depends_on(signal, signal_class, signal_index)

    # provenance
    provenance = expand_provenance(signal, group)

    return {
        "group": group,
        "signal_class": signal_class,
        "field_path": field_path,
        "depends_on": depends_on,
        "provenance": provenance,
        "schema_version": 3,
        "_group_method": method,  # tracking only, not written to YAML
    }


# ---------------------------------------------------------------
# YAML in-place modification using ruamel.yaml
# ---------------------------------------------------------------


def migrate_yaml_file(
    yaml_path: Path,
    explicit_lookup: dict[str, str],
    section_groups: dict[str, list[str]],
    manifest_groups: set[str],
    signal_index: dict[str, dict[str, Any]],
    dry_run: bool = False,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Migrate all signals in a single YAML file. Returns migration results."""
    from ruamel.yaml import YAML

    rtyaml = YAML(typ="rt")
    rtyaml.preserve_quotes = True
    rtyaml.width = 120

    with open(yaml_path, encoding="utf-8") as f:
        data = rtyaml.load(f)

    if not isinstance(data, list):
        return []

    results = []
    modified = False

    for entry in data:
        if not isinstance(entry, dict) or "id" not in entry:
            continue

        sig_id = entry["id"]
        raw_dict = dict(entry)

        v3 = compute_v3_fields(
            raw_dict, explicit_lookup, section_groups, manifest_groups, signal_index
        )
        method = v3.pop("_group_method")

        result = {
            "id": sig_id,
            "old_facet": raw_dict.get("facet", ""),
            "new_group": v3["group"],
            "group_method": method,
            "old_type": raw_dict.get("type", ""),
            "new_signal_class": v3["signal_class"],
            "field_path": v3["field_path"],
            "depends_on_count": len(v3["depends_on"]),
        }
        results.append(result)

        if verbose:
            print(
                f"  {sig_id}: facet={raw_dict.get('facet', '')!r} -> group={v3['group']!r} "
                f"({method}), type={raw_dict.get('type', '')!r} -> class={v3['signal_class']}, "
                f"field_path={v3['field_path']!r}, depends_on={len(v3['depends_on'])}"
            )

        if not dry_run:
            # Set v3 fields
            entry["group"] = v3["group"]
            entry["signal_class"] = v3["signal_class"]
            entry["field_path"] = v3["field_path"]
            entry["depends_on"] = v3["depends_on"]
            entry["schema_version"] = v3["schema_version"]

            # Update provenance in place
            if "provenance" in entry:
                prov = entry["provenance"]
                for k, val in v3["provenance"].items():
                    if k not in prov or not prov[k]:
                        prov[k] = val
            else:
                entry["provenance"] = v3["provenance"]

            # Remove old fields (replaced by v3 equivalents)
            if "type" in entry:
                del entry["type"]
            if "facet" in entry:
                del entry["facet"]

            modified = True

    if modified and not dry_run:
        with open(yaml_path, "w", encoding="utf-8") as f:
            rtyaml.dump(data, f)

    return results


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------


def run_migration(
    dry_run: bool = False,
    stats_only: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Execute the v3 migration. Returns summary statistics."""
    print("=== Brain Signal V3 Migration ===")
    print(f"Signals dir: {_SIGNALS_DIR}")
    print(f"Sections dir: {_SECTIONS_DIR}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print()

    # Build lookups
    explicit_lookup = build_group_lookup(_SECTIONS_DIR)
    section_groups = build_section_groups(_SECTIONS_DIR)
    manifest_groups = build_manifest_groups(_MANIFEST_PATH)
    signal_index = build_signal_index(_SIGNALS_DIR)

    print(f"Explicit group mappings: {len(explicit_lookup)}")
    print(f"Section groups: {sum(len(g) for g in section_groups.values())}")
    print(f"Manifest groups: {len(manifest_groups)}")
    print(f"Total signals: {len(signal_index)}")
    print()

    all_results: list[dict[str, Any]] = []
    yaml_files = sorted(_SIGNALS_DIR.rglob("*.yaml"))

    for yaml_path in yaml_files:
        rel = yaml_path.relative_to(_SIGNALS_DIR)
        if verbose:
            print(f"Processing: {rel}")
        results = migrate_yaml_file(
            yaml_path,
            explicit_lookup,
            section_groups,
            manifest_groups,
            signal_index,
            dry_run=dry_run,
            verbose=verbose,
        )
        all_results.extend(results)

    # Compute statistics
    total = len(all_results)
    class_counts: dict[str, int] = defaultdict(int)
    method_counts: dict[str, int] = defaultdict(int)
    empty_group = 0
    has_field_path = 0
    has_depends_on = 0

    for r in all_results:
        class_counts[r["new_signal_class"]] += 1
        method_counts[r["group_method"]] += 1
        if not r["new_group"]:
            empty_group += 1
        if r["field_path"]:
            has_field_path += 1
        if r["depends_on_count"] > 0:
            has_depends_on += 1

    # Print summary
    print()
    print("=== Migration Summary ===")
    print(f"Total signals: {total}")
    print()
    print("Signal class distribution:")
    for cls, count in sorted(class_counts.items()):
        print(f"  {cls}: {count}")
    print()
    print("Group resolution methods:")
    for method, count in sorted(method_counts.items()):
        print(f"  {method}: {count}")
    print()
    print(f"Empty group: {empty_group}")
    print(f"Has field_path: {has_field_path}/{total}")
    print(f"Has depends_on: {has_depends_on}/{total}")
    print()

    if empty_group > 0:
        unresolved = [r for r in all_results if not r["new_group"]]
        print("UNRESOLVED signals (no group assigned):")
        for r in unresolved:
            print(f"  {r['id']}: facet={r['old_facet']!r}")

    stats = {
        "total": total,
        "class_counts": dict(class_counts),
        "method_counts": dict(method_counts),
        "empty_group": empty_group,
        "has_field_path": has_field_path,
        "has_depends_on": has_depends_on,
    }

    if dry_run:
        print("DRY RUN complete -- no files modified.")
    else:
        print("MIGRATION COMPLETE -- YAML files updated in place.")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="V3 brain signal migration")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print summary statistics only",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log every signal assignment",
    )
    args = parser.parse_args()

    stats = run_migration(
        dry_run=args.dry_run or args.stats,
        stats_only=args.stats,
        verbose=args.verbose and not args.stats,
    )

    if stats["empty_group"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
