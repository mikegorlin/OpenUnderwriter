"""Script to add facet and display fields to all brain signal YAML entries.

Deterministic assignment:
- facet: derived from signal ID prefix (BIZ->business_profile, etc.)
- display.value_format: inferred from threshold.type and signal name
- display.source_type: inferred from required_data/data_locations
- display.threshold_context: left empty (auto-populated at eval time)

Phase 49 Plan 02 Task 1.
"""

from __future__ import annotations

from pathlib import Path

import yaml


# --- Facet assignment by prefix ---
PREFIX_TO_FACET: dict[str, str] = {
    "BIZ": "business_profile",
    "EXEC": "executive_risk",
    "FIN": "financial_health",
    "FWRD": "forward_looking",
    "GOV": "governance",
    "LIT": "litigation",
    "NLP": "filing_analysis",
    "STOCK": "market_activity",
}


def infer_facet(signal_id: str) -> str:
    """Derive facet ID from signal ID prefix."""
    prefix = signal_id.split(".")[0]
    facet = PREFIX_TO_FACET.get(prefix)
    if not facet:
        raise ValueError(f"Unknown prefix for signal {signal_id}: {prefix}")
    return facet


def infer_value_format(signal: dict) -> str:
    """Infer display value_format from threshold type and signal name."""
    threshold = signal.get("threshold", {})
    if not isinstance(threshold, dict):
        return "text"

    threshold_type = threshold.get("type", "")
    signal_id = signal.get("id", "").lower()
    signal_name = signal.get("name", "").lower()

    # Percentage thresholds
    if threshold_type == "percentage":
        return "pct_1dp"

    # Boolean thresholds
    if threshold_type == "boolean":
        return "boolean"

    # Numeric/tiered/value thresholds -- check name context
    if threshold_type in ("tiered", "numeric", "value", "count", "multi_period"):
        # Currency-related
        currency_terms = [
            "revenue", "debt", "compensation", "salary", "pay", "income",
            "asset", "liability", "cash", "equity", "capital", "expense",
            "cost", "profit", "loss", "ebitda", "margin", "valuation",
            "market_cap", "premium", "fee", "bonus", "grant_value",
            "stock_award", "total_comp", "payout",
        ]
        for term in currency_terms:
            if term in signal_id or term in signal_name:
                return "currency"

        # Count-related
        count_terms = [
            "count", "number", "size", "quantity", "total_members",
            "headcount", "departures", "turnover_count",
        ]
        for term in count_terms:
            if term in signal_id or term in signal_name:
                return "count"

        # Percentage-like names with non-percentage threshold
        pct_terms = [
            "ratio", "rate", "pct", "percent", "proportion", "share",
            "concentration", "independence", "dilution", "utilization",
            "volatility", "return", "yield", "beta",
        ]
        for term in pct_terms:
            if term in signal_id or term in signal_name:
                return "pct_1dp"

        # Score-related
        score_terms = ["score", "rating", "index", "z_score", "altman"]
        for term in score_terms:
            if term in signal_id or term in signal_name:
                return "numeric_2dp"

        # Default for tiered/numeric: numeric_2dp
        return "numeric_2dp"

    # Temporal thresholds
    if threshold_type == "temporal":
        return "text"

    # Pattern/classification/display/info
    if threshold_type in ("pattern", "classification", "display", "info"):
        return "text"

    return "text"


def infer_source_type(signal: dict) -> str:
    """Infer display source_type from signal's data sources."""
    required_data = signal.get("required_data", [])
    if not isinstance(required_data, list):
        required_data = []

    data_locations = signal.get("data_locations", {})
    if not isinstance(data_locations, dict):
        data_locations = {}

    data_strategy = signal.get("data_strategy", {})
    if not isinstance(data_strategy, dict):
        data_strategy = {}

    # Combine all source references
    all_sources_str = " ".join(
        [str(r) for r in required_data]
        + list(data_locations.keys())
        + [str(data_strategy.get("primary_source", ""))]
    ).upper()

    # Check in priority order
    if "DEF14A" in all_sources_str or "DEF_14A" in all_sources_str:
        return "SEC_DEF14A"
    if "10-K" in all_sources_str or "10_K" in all_sources_str or "SEC_10K" in all_sources_str:
        return "SEC_10K"
    if "8-K" in all_sources_str or "8_K" in all_sources_str or "SEC_8K" in all_sources_str:
        return "SEC_8K"
    if "10-Q" in all_sources_str or "10_Q" in all_sources_str or "SEC_10Q" in all_sources_str:
        return "SEC_10Q"
    if "STOCK" in all_sources_str or "PRICE" in all_sources_str or "MARKET" in all_sources_str:
        return "MARKET_DATA"
    if "WEB" in all_sources_str or "NEWS" in all_sources_str or "SENTIMENT" in all_sources_str:
        return "WEB"
    if "COURT" in all_sources_str or "LITIGATION" in all_sources_str or "SCAC" in all_sources_str:
        return "COURT_RECORDS"
    if "SEC_ENFORCEMENT" in all_sources_str or "AAER" in all_sources_str:
        return "SEC_ENFORCEMENT"

    return "DERIVED"


def has_complete_display(signal: dict) -> bool:
    """Check if signal already has a complete display spec (don't overwrite)."""
    display = signal.get("display")
    if not isinstance(display, dict):
        return False
    # Complete = has both value_format and source_type set
    return bool(display.get("value_format")) and bool(display.get("source_type"))


def process_yaml_file(filepath: Path) -> tuple[int, int]:
    """Add facet and display to all signals in one YAML file.

    Returns (updated_count, skipped_count).
    """
    text = filepath.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if not isinstance(data, list):
        return (0, 0)

    updated = 0
    skipped = 0

    for signal in data:
        if not isinstance(signal, dict) or "id" not in signal:
            continue

        # Always set facet (overwrite if present since it should be deterministic)
        signal["facet"] = infer_facet(signal["id"])

        # Display: skip if already complete
        if has_complete_display(signal):
            # Still ensure display is present even if already complete
            skipped += 1
        else:
            # Build or merge display
            existing_display = signal.get("display", {})
            if not isinstance(existing_display, dict):
                existing_display = {}

            new_display = {
                "value_format": existing_display.get("value_format") or infer_value_format(signal),
                "source_type": existing_display.get("source_type") or infer_source_type(signal),
                "threshold_context": existing_display.get("threshold_context", ""),
            }
            # Preserve any extra fields (like deprecation_note)
            for k, v in existing_display.items():
                if k not in new_display:
                    new_display[k] = v

            signal["display"] = new_display
            updated += 1

    # Preserve header comments by reading them from original text
    header_lines = []
    for line in text.split("\n"):
        if line.startswith("#"):
            header_lines.append(line)
        else:
            break

    header = "\n".join(header_lines) + "\n\n" if header_lines else ""

    yaml_output = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    filepath.write_text(header + yaml_output, encoding="utf-8")
    return (updated, skipped)


def main() -> None:
    signals_dir = Path("src/do_uw/brain/signals")
    if not signals_dir.exists():
        raise FileNotFoundError(f"Signals directory not found: {signals_dir}")

    total_updated = 0
    total_skipped = 0
    total_files = 0

    for yaml_file in sorted(signals_dir.rglob("*.yaml")):
        updated, skipped = process_yaml_file(yaml_file)
        total_files += 1
        total_updated += updated
        total_skipped += skipped
        print(f"  {yaml_file.relative_to(signals_dir)}: {updated} updated, {skipped} skipped")

    print(f"\nTotal: {total_files} files, {total_updated} signals updated, {total_skipped} skipped (already complete)")

    # Validation pass
    missing_facet = []
    missing_display = []
    for f in sorted(signals_dir.rglob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if isinstance(data, list):
            for s in data:
                if not s.get("facet"):
                    missing_facet.append(s["id"])
                if not s.get("display"):
                    missing_display.append(s["id"])

    print(f"\nValidation: Missing facet: {len(missing_facet)}, Missing display: {len(missing_display)}")
    if missing_facet:
        print(f"  Missing facet: {missing_facet[:10]}")
    if missing_display:
        print(f"  Missing display: {missing_display[:10]}")

    assert len(missing_facet) == 0, f"Some signals missing facet field"
    assert len(missing_display) == 0, f"Some signals missing display field"
    print("\nAll 400 signals have facet and display fields.")


if __name__ == "__main__":
    main()
