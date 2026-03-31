"""Enrich brain/signals.json with content_type, depth, and data_strategy metadata.

Standalone script that classifies all 388 checks and writes enriched metadata
back to signals.json. Idempotent -- safe to run multiple times. Never removes
or renames existing fields.

Usage:
    uv run python src/do_uw/scripts/enrich_signals.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Add project src to path so we can import from do_uw
_PROJECT_SRC = str(Path(__file__).parent.parent.parent)
if _PROJECT_SRC not in sys.path:
    sys.path.insert(0, _PROJECT_SRC)

from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK  # noqa: E402

# Path to brain/signals.json relative to this script
CHECKS_JSON = Path(__file__).parent.parent / "brain" / "config" / "signals.json"

# --------------------------------------------------------------------------- #
# Pattern reference mapping for known STOCK.PATTERN checks
# --------------------------------------------------------------------------- #
_KNOWN_PATTERN_REFS: dict[str, str] = {
    "STOCK.PATTERN.event_collapse": "EVENT_COLLAPSE",
    "STOCK.PATTERN.informed_trading": "INFORMED_TRADING",
    "STOCK.PATTERN.cascade": "PRICE_CASCADE",
    "STOCK.PATTERN.death_spiral": "DEATH_SPIRAL",
    "STOCK.PATTERN.short_attack": "SHORT_ATTACK",
    "STOCK.PATTERN.peer_divergence": "PEER_DIVERGENCE",
}

# Data sources that indicate HUNT depth (level 4)
_HUNT_SOURCES = frozenset({"SCAC_SEARCH", "SEC_ENFORCEMENT", "COURTLISTENER"})


def classify_content_type(check: dict) -> str:
    """Classify a check's content type.

    Rules (applied in order):
    1. signal_type == PATTERN -> INFERENCE_PATTERN
    2. CONTEXT_DISPLAY with empty factors -> MANAGEMENT_DISPLAY
    3. CONTEXT_DISPLAY with non-empty factors -> EVALUATIVE_CHECK
    4. DECISION_DRIVING -> EVALUATIVE_CHECK
    5. Default -> EVALUATIVE_CHECK
    """
    if check.get("signal_type") == "PATTERN":
        return "INFERENCE_PATTERN"
    category = check.get("category", "")
    factors = check.get("factors", [])
    if category == "CONTEXT_DISPLAY" and not factors:
        return "MANAGEMENT_DISPLAY"
    if category == "CONTEXT_DISPLAY" and factors:
        return "EVALUATIVE_CHECK"
    if category == "DECISION_DRIVING":
        return "EVALUATIVE_CHECK"
    return "EVALUATIVE_CHECK"


def classify_depth(check: dict) -> int:
    """Classify a check's depth level (1-4).

    Rules (applied in order):
    1. threshold.type in (info, display, classification) AND no factors -> 1 (DISPLAY)
    2. signal_type in (PATTERN, FORENSIC) -> 3 (INFER)
    3. required_data contains SCAC_SEARCH/SEC_ENFORCEMENT/COURTLISTENER -> 4 (HUNT)
    4. threshold.type in (percentage, count, value, boolean) -> 2 (COMPUTE)
    5. threshold.type == temporal -> 3 (INFER)
    6. Default -> 2 (COMPUTE)
    """
    threshold_type = check.get("threshold", {}).get("type", "")
    factors = check.get("factors", [])

    if threshold_type in ("info", "display", "classification") and not factors:
        return 1

    if check.get("signal_type") in ("PATTERN", "FORENSIC"):
        return 3

    required_data = check.get("required_data", [])
    if any(src in _HUNT_SOURCES for src in required_data):
        return 4

    if threshold_type in ("percentage", "count", "value", "boolean"):
        return 2

    if threshold_type == "temporal":
        return 3

    return 2


def migrate_field_key(check: dict) -> None:
    """Set data_strategy.field_key and primary_source from FIELD_FOR_CHECK.

    Initializes data_strategy dict if not present. Only sets field_key
    if the check ID has a mapping in FIELD_FOR_CHECK.
    """
    signal_id = check["id"]
    field = FIELD_FOR_CHECK.get(signal_id)
    if field is None:
        return

    # Ensure data_strategy exists
    if "data_strategy" not in check or check["data_strategy"] is None:
        check["data_strategy"] = {}

    check["data_strategy"]["field_key"] = field

    # Set primary_source from first required_data if available
    required_data = check.get("required_data", [])
    if required_data:
        check["data_strategy"]["primary_source"] = required_data[0]


def set_pattern_ref(check: dict) -> None:
    """Set pattern_ref for INFERENCE_PATTERN checks.

    Uses known mapping for STOCK.PATTERN.* checks. For others,
    derives pattern_ref from the last part of the check ID converted
    to UPPER_SNAKE_CASE.
    """
    if check.get("content_type") != "INFERENCE_PATTERN":
        return

    signal_id = check["id"]

    # Try known mapping first
    if signal_id in _KNOWN_PATTERN_REFS:
        check["pattern_ref"] = _KNOWN_PATTERN_REFS[signal_id]
        return

    # Derive from last part of ID -> UPPER_SNAKE_CASE
    parts = signal_id.split(".")
    last_part = parts[-1] if parts else signal_id
    check["pattern_ref"] = last_part.upper()


def enrich_check(check: dict) -> dict:
    """Apply all enrichment steps to a single check."""
    check["content_type"] = classify_content_type(check)
    check["depth"] = classify_depth(check)
    migrate_field_key(check)
    set_pattern_ref(check)
    return check


def main() -> None:
    """Load, enrich, and write back signals.json."""
    print(f"Loading signals from: {CHECKS_JSON}")
    with open(CHECKS_JSON) as f:
        data = json.load(f)

    checks = data["signals"]
    total = len(checks)
    print(f"Found {total} checks")

    # Enrich each check
    for check in checks:
        enrich_check(check)

    # Update version metadata
    data["version"] = "9.0.0"
    data["schema"] = "BRAIN_CHECKS_V8"

    # Write back
    with open(CHECKS_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Ensure trailing newline
    with open(CHECKS_JSON, "a") as f:
        f.write("\n")

    # Print summary
    ct_counts = Counter(c["content_type"] for c in checks)
    depth_counts = Counter(c["depth"] for c in checks)
    field_key_count = sum(
        1
        for c in checks
        if c.get("data_strategy") and c["data_strategy"].get("field_key")
    )
    pattern_ref_count = sum(1 for c in checks if c.get("pattern_ref"))

    print("\n--- Enrichment Summary ---")
    print(f"Total checks enriched: {total}")
    print("\nContent Type distribution:")
    for ct, count in sorted(ct_counts.items()):
        print(f"  {ct}: {count}")
    print("\nDepth distribution:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Level {depth}: {count}")
    print(f"\nField key coverage: {field_key_count}/{total}")
    print(f"Pattern refs set: {pattern_ref_count}")
    print(f"\nVersion: {data['version']}")
    print(f"Schema: {data['schema']}")
    print(f"\nDone. Wrote enriched checks to: {CHECKS_JSON}")


if __name__ == "__main__":
    main()
