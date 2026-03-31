"""Script to create/update facet definition YAML files.

Reads all signal YAMLs to collect signal IDs grouped by facet field,
then creates/updates facet definition files with complete signals lists.

Phase 49 Plan 02 Task 2.
"""

from __future__ import annotations

from pathlib import Path

import yaml


# Facet definitions (id, name, display_type, display_config)
FACET_DEFS: list[dict] = [
    {
        "id": "business_profile",
        "name": "Business Profile",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Business Indicator",
            "col_value": "Value",
        },
    },
    {
        "id": "executive_risk",
        "name": "Executive Risk",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Executive Indicator",
            "col_value": "Assessment",
        },
    },
    {
        "id": "financial_health",
        "name": "Financial Health",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Financial Metric",
            "col_value": "Value",
        },
    },
    {
        "id": "forward_looking",
        "name": "Forward-Looking Indicators",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Forward Indicator",
            "col_value": "Assessment",
        },
    },
    {
        "id": "governance",
        "name": "Governance Assessment",
        "display_type": "scorecard_table",
        "display_config": {
            "col_signal": "Governance Factor",
            "col_value": "Assessment",
            "col_source": "Source",
            "show_deprecation_note": True,
        },
    },
    {
        "id": "litigation",
        "name": "Litigation & Regulatory",
        "display_type": "flag_list",
        "display_config": {
            "col_signal": "Litigation Factor",
            "col_value": "Assessment",
        },
    },
    {
        "id": "market_activity",
        "name": "Market Activity",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Market Indicator",
            "col_value": "Value",
        },
    },
    {
        "id": "filing_analysis",
        "name": "Filing Analysis",
        "display_type": "metric_table",
        "display_config": {
            "col_signal": "Filing Indicator",
            "col_value": "Assessment",
        },
    },
]


def collect_signals_by_facet(signals_dir: Path) -> dict[str, list[str]]:
    """Read all signal YAMLs and group signal IDs by their facet field."""
    facet_signals: dict[str, list[str]] = {}

    for f in sorted(signals_dir.rglob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if not isinstance(data, list):
            continue
        for sig in data:
            if not isinstance(sig, dict) or "id" not in sig:
                continue
            facet_id = sig.get("facet", "")
            if not facet_id:
                print(f"  WARNING: Signal {sig['id']} has no facet field!")
                continue
            if facet_id not in facet_signals:
                facet_signals[facet_id] = []
            facet_signals[facet_id].append(sig["id"])

    # Sort each list alphabetically for deterministic ordering
    for facet_id in facet_signals:
        facet_signals[facet_id].sort()

    return facet_signals


def create_facet_yaml(facet_def: dict, signal_ids: list[str], facets_dir: Path) -> None:
    """Create or update a facet definition YAML file."""
    facet_id = facet_def["id"]
    filepath = facets_dir / f"{facet_id}.yaml"

    facet_data = {
        "id": facet_def["id"],
        "name": facet_def["name"],
        "display_type": facet_def["display_type"],
        "signals": signal_ids,
        "display_config": facet_def["display_config"],
    }

    yaml_output = yaml.dump(
        facet_data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    # Add a header comment
    header = (
        f"# {facet_def['name']} Facet -- composed display unit for {facet_id} signals\n"
        f"# display_type: {facet_def['display_type']}\n"
        f"# Signal count: {len(signal_ids)}\n"
        f"#\n"
        f"# Phase 49 Plan 02: Created programmatically from signal facet assignments.\n\n"
    )

    filepath.write_text(header + yaml_output, encoding="utf-8")
    action = "Updated" if filepath.exists() else "Created"
    print(f"  {action}: {filepath.name} ({len(signal_ids)} signals)")


def main() -> None:
    signals_dir = Path("src/do_uw/brain/signals")
    facets_dir = Path("src/do_uw/brain/sections")

    if not signals_dir.exists():
        raise FileNotFoundError(f"Signals directory not found: {signals_dir}")

    facets_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Collect signals by facet
    print("Collecting signals by facet...")
    facet_signals = collect_signals_by_facet(signals_dir)
    print(f"  Found {len(facet_signals)} facets: {sorted(facet_signals.keys())}")
    for fid, sids in sorted(facet_signals.items()):
        print(f"    {fid}: {len(sids)} signals")

    # Step 2: Create/update facet definition files
    print("\nCreating facet definition files...")
    for facet_def in FACET_DEFS:
        facet_id = facet_def["id"]
        signal_ids = facet_signals.get(facet_id, [])
        create_facet_yaml(facet_def, signal_ids, facets_dir)

    # Step 3: Keep red_flags.yaml as-is (don't overwrite)
    red_flags_path = facets_dir / "red_flags.yaml"
    if red_flags_path.exists():
        print(f"\n  Kept: red_flags.yaml (cross-cutting, signals list stays empty)")
    else:
        print(f"\n  WARNING: red_flags.yaml not found!")

    # Step 4: Cross-validation
    print("\nCross-validation...")
    all_signal_ids: set[str] = set()
    for f in sorted(signals_dir.rglob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if isinstance(data, list):
            for s in data:
                if isinstance(s, dict) and "id" in s:
                    all_signal_ids.add(s["id"])

    facet_signal_ids: set[str] = set()
    facet_count = 0
    for f in sorted(facets_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        facet_count += 1
        for sid in data.get("signals", []):
            if sid in facet_signal_ids:
                print(f"  ERROR: Duplicate signal {sid} across facets!")
            facet_signal_ids.add(sid)

    missing = all_signal_ids - facet_signal_ids
    extra = facet_signal_ids - all_signal_ids

    print(f"  Facets: {facet_count}")
    print(f"  Signals in facets: {len(facet_signal_ids)}")
    print(f"  Total signals: {len(all_signal_ids)}")
    print(f"  Missing from facets: {len(missing)}")
    print(f"  Unknown in facets: {len(extra)}")

    if missing:
        print(f"  Missing: {sorted(missing)[:10]}")
    if extra:
        print(f"  Extra: {sorted(extra)[:10]}")

    assert len(missing) == 0, f"Missing signals from facets: {sorted(missing)[:10]}"
    assert len(extra) == 0, f"Unknown signals in facets: {sorted(extra)[:10]}"
    assert facet_signal_ids == all_signal_ids, "Facet signals don't match actual signals"

    print("\nAll facet definitions valid. Every signal appears in exactly one facet.")


if __name__ == "__main__":
    main()
