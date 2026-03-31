"""Brain migration: signals.json → domain YAML files (unified 3-axis schema).

Reads signals.json, patterns.json, red_flags.json, and causal_chains.yaml,
then writes domain YAML files under src/do_uw/brain/signals/ using the
unified schema defined in SCHEMA.md (Phase 44, Plan 02).

Usage:
    uv run python src/do_uw/brain/brain_migrate_yaml.py
"""

from __future__ import annotations

import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

_BRAIN_DIR = Path(__file__).parent
_CHECKS_JSON = _BRAIN_DIR / "signals.json"
_PATTERNS_JSON = _BRAIN_DIR / "patterns.json"
_RED_FLAGS_JSON = _BRAIN_DIR / "red_flags.json"
_CAUSAL_CHAINS_YAML = _BRAIN_DIR / "framework" / "causal_chains.yaml"
_OUTPUT_DIR = _BRAIN_DIR / "signals"

# Section int (1–7) → semantic string (SCHEMA.md §10)
_SECTION_MAP: dict[int, str] = {
    1: "company_profile", 2: "governance", 3: "management",
    4: "financial", 5: "litigation", 6: "stock_activity", 7: "forward_looking",
}

_CONTENT_TYPE_MAP = {
    "MANAGEMENT_DISPLAY": "extract",
    "EVALUATIVE_CHECK": "evaluate",
    "INFERENCE_PATTERN": "infer",
}

_LAYER_MAP = {
    "HAZARD": "hazard", "SIGNAL": "signal", "PERIL_CONFIRMING": "peril_confirming",
}

_DISPLAY_WHEN_DEFAULT = {"extract": "always", "evaluate": "has_data", "infer": "fired"}

_PREFIX_SECTION_FALLBACK = {
    "BIZ": "company_profile", "FIN": "financial", "GOV": "governance",
    "EXEC": "management", "LIT": "litigation", "STOCK": "stock_activity",
    "FWRD": "forward_looking", "NLP": "governance",
}

_CHECK_ID_RE = re.compile(
    r"\b(?:BIZ|FIN|GOV|EXEC|LIT|STOCK|FWRD|NLP)\.[A-Z0-9]+\.[a-z_]+\b"
)


def load_sources() -> tuple[list[dict], list[dict], list[dict], dict]:
    """Load signals.json, patterns.json, red_flags.json, causal_chains.yaml."""
    with open(_CHECKS_JSON) as f:
        checks = json.load(f)["signals"]
    with open(_PATTERNS_JSON) as f:
        patterns = json.load(f).get("patterns", [])
    with open(_RED_FLAGS_JSON) as f:
        rf_triggers = json.load(f).get("escalation_triggers", [])
    with open(_CAUSAL_CHAINS_YAML) as f:
        causal_chains = yaml.safe_load(f)
    return checks, patterns, rf_triggers, causal_chains


def build_chain_roles_index(causal_chains: dict) -> dict[str, dict[str, str]]:
    """Return {signal_id: {chain_id: role}} for all cross-referenced checks."""
    index: dict[str, dict[str, str]] = defaultdict(dict)
    role_fields = [
        ("trigger_signals", "trigger"), ("amplifier_signals", "amplifier"),
        ("mitigator_signals", "mitigator"), ("evidence_signals", "evidence"),
    ]
    for chain in causal_chains.get("chains", []):
        chain_id: str = chain["id"]
        for field, role in role_fields:
            for signal_id in chain.get(field, []):
                index[signal_id][chain_id] = role
    return dict(index)


def build_red_flag_index(rf_triggers: list[dict]) -> set[str]:
    """Return set of check IDs that map to critical red flag conditions.

    Combines: (1) explicit check IDs in detection_logic fields, and
    (2) semantic mapping from CRF names to evaluating check IDs.
    """
    red_flag_ids: set[str] = set()
    for trigger in rf_triggers:
        detection = trigger.get("detection_logic", "") or ""
        red_flag_ids.update(_CHECK_ID_RE.findall(detection))

    # Semantic mapping: CRF name → primary check IDs that evaluate the condition
    crf_to_checks = {
        "Active Securities Class Action": ["LIT.SCA.active", "LIT.SCA.search"],
        "Wells Notice Disclosed": ["LIT.REG.wells_notice"],
        "DOJ Criminal Investigation": ["LIT.REG.doj_investigation"],
        "Going Concern Opinion": ["FIN.ACCT.going_concern"],
        "Restatement in Past 12 Months": ["FIN.ACCT.restatement", "FIN.ACCT.restatement_magnitude"],
        "Short Seller Report": ["STOCK.SHORT.report"],
        "Catastrophic Stock Drop": ["STOCK.PRICE.recent_drop_alert"],
        "Recent Drop - 7 Day": ["STOCK.PRICE.recent_drop_alert"],
        "Recent Drop - 30 Day": ["STOCK.PRICE.recent_drop_alert"],
        "Recent Drop - 90 Day": ["STOCK.PRICE.returns_multi_horizon"],
        "Active DOJ Criminal Investigation": ["LIT.REG.doj_investigation"],
        "Caremark Claim Survived Dismissal": ["LIT.OTHER.whistleblower"],
    }
    for trigger in rf_triggers:
        for signal_id in crf_to_checks.get(trigger.get("name", ""), []):
            red_flag_ids.add(signal_id)

    return red_flag_ids


def map_content_type_to_work_type(content_type: str) -> str:
    """Map content_type enum to work_type enum."""
    return _CONTENT_TYPE_MAP.get(content_type, "evaluate")


def derive_acquisition_tier(required_data: list[str]) -> str:
    """Derive acquisition tier from required_data values. Highest-cost wins."""
    tier = "L1"
    for source in required_data:
        su = source.upper()
        if any(su.startswith(p) for p in (
            "BIZ.", "FIN.", "GOV.", "EXEC.", "LIT.", "STOCK.", "FWRD.", "NLP.", "PATTERN."
        )):
            return "L4"
        if any(su.startswith(p) for p in (
            "MARKET_", "NEWS", "COURT", "WEB", "BRAVE", "PLAYWRIGHT",
            "SEC_PROXY", "YAHOO", "GLASSDOOR", "TWITTER", "REDDIT",
            "EDGAR_FULL_TEXT",
        )):
            return "L3"
        if su.startswith("ITEM"):
            tier = "L2"
    return tier


def map_hazard_or_signal_to_layer(hazard_or_signal: str) -> str:
    """Map hazard_or_signal string to layer enum value."""
    return _LAYER_MAP.get((hazard_or_signal or "").upper(), "signal")


def derive_worksheet_section(section_int: int, signal_id: str) -> str:
    """Map section int (1–7) to semantic string; fallback to prefix heuristic."""
    if section_int in _SECTION_MAP:
        return _SECTION_MAP[section_int]
    prefix = signal_id.split(".")[0]
    return _PREFIX_SECTION_FALLBACK.get(prefix, "company_profile")


def migrate_single_check(
    check: dict,
    chain_roles_index: dict[str, dict[str, str]],
    red_flag_ids: set[str],
) -> dict:
    """Transform one signals.json entry to unified YAML dict.

    Adds: work_type, layer, acquisition_tier, worksheet_section, display_when,
          chain_roles, peril_ids (empty), unlinked, provenance.
    Removes deprecated fields: pillar, category, signal_type, hazard_or_signal,
          content_type, section.
    Keeps: id, name, factors, required_data, data_locations, threshold,
           execution_mode, claims_correlation, tier, depth, pattern_ref,
           plaintiff_lenses, v6_subsection_ids, amplifier, amplifier_bonus_points,
           sector_adjustments, extraction_hints, data_strategy.
    """
    signal_id: str = check["id"]
    work_type = map_content_type_to_work_type(check.get("content_type", "EVALUATIVE_CHECK"))
    layer = map_hazard_or_signal_to_layer(check.get("hazard_or_signal", "SIGNAL"))
    chain_roles: _FlowMapping = _FlowMapping(chain_roles_index.get(signal_id, {}))
    unlinked = len(chain_roles) == 0
    required_data: list[str] = check.get("required_data", [])
    acquisition_tier = derive_acquisition_tier(required_data)
    worksheet_section = derive_worksheet_section(check.get("section", 1), signal_id)
    display_when = _DISPLAY_WHEN_DEFAULT[work_type]

    out: dict[str, Any] = {"id": signal_id, "name": check["name"], "work_type": work_type,
                           "layer": layer}

    factors = check.get("factors", [])
    if factors:
        out["factors"] = factors

    out["peril_ids"] = []
    out["chain_roles"] = chain_roles
    out["unlinked"] = unlinked
    out["acquisition_tier"] = acquisition_tier

    if required_data:
        out["required_data"] = required_data

    # Preserved optional fields — only include when present/non-null
    _copy_if_present(out, check, "data_locations")
    _copy_if_present(out, check, "threshold")

    execution_mode = check.get("execution_mode")
    if execution_mode and execution_mode != "AUTO":
        out["execution_mode"] = execution_mode

    _copy_if_not_none(out, check, "claims_correlation")
    _copy_if_not_none(out, check, "tier")
    _copy_if_not_none(out, check, "depth")
    _copy_if_present(out, check, "pattern_ref")

    plaintiff_lenses = check.get("plaintiff_lenses", [])
    if plaintiff_lenses:
        out["plaintiff_lenses"] = plaintiff_lenses

    v6 = check.get("v6_subsection_ids", [])
    if v6:
        out["v6_subsection_ids"] = v6

    _copy_if_present(out, check, "amplifier")
    _copy_if_not_none(out, check, "amplifier_bonus_points")
    _copy_if_present(out, check, "sector_adjustments")
    _copy_if_present(out, check, "extraction_hints")
    _copy_if_present(out, check, "data_strategy")

    out["worksheet_section"] = worksheet_section
    out["display_when"] = display_when

    if signal_id in red_flag_ids:
        out["critical_red_flag"] = True

    out["provenance"] = _FlowMapping({
        "origin": "migrated_from_json",
        "confidence": "inherited",
        "last_validated": None,
        "source_url": None,
        "source_date": None,
        "source_author": None,
        "added_by": None,
    })
    return out


def _copy_if_present(out: dict, src: dict, key: str) -> None:
    val = src.get(key)
    if val:
        out[key] = val


def _copy_if_not_none(out: dict, src: dict, key: str) -> None:
    val = src.get(key)
    if val is not None:
        out[key] = val


def assign_domain_file(signal_id: str) -> str:
    """Return relative YAML path within checks/ for the given check ID.

    All domains use subdirectory structure to stay within the 500-line limit.
    Sub-prefixes that would exceed ~12 checks are split further.
    """
    parts = signal_id.split(".")
    prefix = parts[0]
    sub = parts[1] if len(parts) >= 2 else ""

    if prefix == "GOV":
        gov_map = {"BOARD": "gov/board.yaml", "AUDIT": "gov/audit.yaml",
                   "EXEC": "gov/exec_comp.yaml", "ACTIVIST": "gov/activist.yaml",
                   "PAY": "gov/pay.yaml", "RIGHTS": "gov/rights.yaml",
                   "EFFECT": "gov/effect.yaml", "INSIDER": "gov/insider.yaml"}
        return gov_map.get(sub, "gov/effect.yaml")

    if prefix == "FWRD":
        if sub == "WARN":
            name3 = parts[2] if len(parts) >= 3 else ""
            _sentiment = {"glassdoor_sentiment", "indeed_reviews", "blind_posts",
                          "app_ratings", "g2_reviews", "trustpilot_trend",
                          "social_sentiment", "job_posting_patterns",
                          "linkedin_headcount", "linkedin_departures", "journalism_activity"}
            _tech = {"ai_revenue_concentration", "hyperscaler_dependency",
                     "gpu_allocation", "data_center_risk"}
            if name3 in _sentiment:
                return "fwrd/warn_sentiment.yaml"
            if name3 in _tech:
                return "fwrd/warn_tech.yaml"
            return "fwrd/warn_ops.yaml"
        fwrd_map = {"GUID": "fwrd/guidance.yaml", "FORECAST": "fwrd/guidance.yaml",
                    "NARRATIVE": "fwrd/guidance.yaml", "DISC": "fwrd/guidance.yaml",
                    "SPAC": "fwrd/spac.yaml", "MERGER": "fwrd/spac.yaml",
                    "MA": "fwrd/ma.yaml", "ACQ": "fwrd/ma.yaml", "EVENT": "fwrd/ma.yaml",
                    "MACRO": "fwrd/transform.yaml"}
        return fwrd_map.get(sub, "fwrd/transform.yaml")

    if prefix == "BIZ":
        biz_map = {"CLASS": "biz/core.yaml", "MODEL": "biz/model.yaml",
                   "SIZE": "biz/core.yaml", "STRUCT": "biz/core.yaml",
                   "COMP": "biz/competitive.yaml", "DEPEND": "biz/dependencies.yaml",
                   "UNI": "biz/dependencies.yaml"}
        return biz_map.get(sub, "biz/core.yaml")

    if prefix == "FIN":
        fin_map = {"ACCT": "fin/accounting.yaml", "FORENSIC": "fin/forensic.yaml",
                   "QUALITY": "fin/forensic.yaml", "PROFIT": "fin/income.yaml",
                   "GUIDE": "fin/income.yaml", "DEBT": "fin/balance.yaml",
                   "LIQ": "fin/balance.yaml", "SECTOR": "fin/balance.yaml",
                   "TEMPORAL": "fin/temporal.yaml"}
        return fin_map.get(sub, "fin/income.yaml")

    if prefix == "LIT":
        if sub == "SCA":
            n3 = parts[2] if len(parts) >= 3 else ""
            _hist = {"historical", "prior_settle", "prior_dismiss", "settle_amount",
                     "settle_date", "dismiss_basis", "demand", "search", "prefiling"}
            return "lit/sca_history.yaml" if n3 in _hist else "lit/sca.yaml"
        if sub == "REG":
            n3 = parts[2] if len(parts) >= 3 else ""
            _sec = {"sec_active", "sec_investigation", "sec_severity", "wells_notice",
                    "comment_letters", "subpoena", "civil_penalty", "consent_order",
                    "cease_desist", "deferred_pros"}
            return "lit/reg_sec.yaml" if n3 in _sec else "lit/reg_agency.yaml"
        lit_map = {"OTHER": "lit/other.yaml", "DEFENSE": "lit/defense.yaml",
                   "PATTERN": "lit/defense.yaml", "SECTOR": "lit/defense.yaml"}
        return lit_map.get(sub, "lit/other.yaml")

    if prefix == "STOCK":
        stock_map = {"PRICE": "stock/price.yaml", "PATTERN": "stock/pattern.yaml",
                     "SHORT": "stock/short.yaml", "ANALYST": "stock/short.yaml",
                     "LIT": "stock/short.yaml", "INSIDER": "stock/insider.yaml",
                     "TRADE": "stock/insider.yaml", "OWN": "stock/ownership.yaml",
                     "VALUATION": "stock/ownership.yaml"}
        return stock_map.get(sub, "stock/price.yaml")

    if prefix == "EXEC":
        exec_map = {"PROFILE": "exec/profile.yaml", "TENURE": "exec/profile.yaml",
                    "CEO": "exec/profile.yaml", "CFO": "exec/profile.yaml",
                    "AGGREGATE": "exec/profile.yaml", "DEPARTURE": "exec/activity.yaml",
                    "INSIDER": "exec/activity.yaml", "PRIOR_LIT": "exec/activity.yaml"}
        return exec_map.get(sub, "exec/profile.yaml")

    if prefix == "NLP":
        return "nlp/nlp.yaml"

    return "biz/core.yaml"


class _FlowMapping(dict):
    """Dict subclass that signals YAML dumper to use flow style."""


class _CompactDumper(yaml.Dumper):
    """Custom YAML dumper: flow style for short lists and _FlowMapping dicts."""

    def represent_sequence(self, tag: str, sequence: list, flow_style: bool = False) -> yaml.Node:  # type: ignore[override]
        # Use flow style for short, simple (non-dict) lists
        if all(isinstance(item, (str, int, float, bool)) for item in sequence) and len(sequence) <= 5:
            flow_style = True
        return super().represent_sequence(tag, sequence, flow_style=flow_style)

    def represent_none(self, data: None) -> yaml.Node:  # type: ignore[override]
        return self.represent_scalar("tag:yaml.org,2002:null", "null")

    def represent_flow_mapping(self, data: _FlowMapping) -> yaml.Node:
        return self.represent_mapping("tag:yaml.org,2002:map", dict(data), flow_style=True)


_CompactDumper.add_representer(type(None), _CompactDumper.represent_none)
_CompactDumper.add_representer(
    list,
    lambda dumper, data: dumper.represent_sequence("tag:yaml.org,2002:seq", data),
)
_CompactDumper.add_representer(_FlowMapping, _CompactDumper.represent_flow_mapping)


def write_domain_yaml_files(grouped: dict[str, list[dict]], output_dir: Path) -> None:
    """Write each domain's checks to YAML file; create subdirs as needed."""
    for rel_path, checks_list in sorted(grouped.items()):
        out_file = output_dir / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Generated by brain_migrate_yaml.py — DO NOT EDIT"
            f" — source: signals.json\n"
            f"# Domain: {rel_path}  |  Count: {len(checks_list)}\n\n"
        )
        lines: list[str] = []
        for check in checks_list:
            chunk = yaml.dump(
                [check], Dumper=_CompactDumper, default_flow_style=False,
                allow_unicode=True, sort_keys=False, width=120,
            )
            lines.append(chunk.rstrip())
            lines.append("")
        out_file.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"  Wrote {len(checks_list):3d} checks → {rel_path}")


def verify_output(output_dir: Path, original_count: int) -> None:
    """Count total checks in YAML files and assert equals original_count."""
    total = 0
    oversized: list[tuple[str, int]] = []
    for yaml_path_str in sorted(glob.glob(str(output_dir / "**" / "*.yaml"), recursive=True)):
        yaml_path = Path(yaml_path_str)
        line_count = len(yaml_path.read_text().splitlines())
        if line_count > 490:
            oversized.append((str(yaml_path.relative_to(output_dir)), line_count))
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            total += len(data)
        elif isinstance(data, dict) and "signals" in data:
            total += len(data["signals"])

    print(f"\nVerification: {total} checks in YAML, {original_count} in signals.json")
    if total == original_count:
        print("CHECK COUNT MATCH: OK")
    else:
        print(f"MISMATCH: {total} != {original_count} — check migration logic")
        sys.exit(1)

    if oversized:
        print("\nWARNING: Files exceeding 490 lines:")
        for name, count in oversized:
            print(f"  {name}: {count} lines — consider splitting by sub-prefix")
    else:
        print("LINE LENGTH CHECK: All files within 500-line limit")


def clean_output_dir(output_dir: Path) -> None:
    """Remove all existing YAML files from output_dir before fresh migration."""
    import shutil
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Cleaned output directory: {output_dir}")


def main() -> None:
    """Orchestrate: clean → load → build indexes → migrate → group → write → verify."""
    print("=== Brain YAML Migration ===")
    print(f"Source: {_CHECKS_JSON}")
    print(f"Output: {_OUTPUT_DIR}\n")

    # Clean output directory for idempotent re-runs
    clean_output_dir(_OUTPUT_DIR)

    checks, patterns, rf_triggers, causal_chains = load_sources()
    print(f"Loaded: {len(checks)} checks, {len(patterns)} patterns, "
          f"{len(rf_triggers)} red flag triggers, "
          f"{len(causal_chains.get('chains', []))} causal chains")

    chain_roles_index = build_chain_roles_index(causal_chains)
    red_flag_ids = build_red_flag_index(rf_triggers)
    print(f"Indexes: {len(chain_roles_index)} chain-linked checks, "
          f"{len(red_flag_ids)} red flag check IDs\n")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for check in checks:
        migrated = migrate_single_check(check, chain_roles_index, red_flag_ids)
        grouped[assign_domain_file(check["id"])].append(migrated)

    unlinked = sum(1 for c in checks if c["id"] not in chain_roles_index)
    print(f"Migration: {len(checks) - unlinked} linked, {unlinked} unlinked, "
          f"{len(grouped)} target files\n")

    write_domain_yaml_files(dict(grouped), _OUTPUT_DIR)
    verify_output(_OUTPUT_DIR, len(checks))


if __name__ == "__main__":
    main()
