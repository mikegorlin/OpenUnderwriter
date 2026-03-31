"""Narrative YAML configuration loader for 5-layer narrative architecture.

Phase 65-01: NARR-07 -- narrative templates in brain/narratives/ YAML,
not hardcoded strings.

Each section has a YAML file defining:
- verdict: score threshold -> verdict level mapping
- thesis_template: Jinja2-style template string for the thesis sentence
- evidence_keys: list of context keys to pull into evidence grid
- implications_template: D&O implications template string
- deep_context_keys: keys for collapsible deep context
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_NARRATIVES_DIR = Path(__file__).resolve().parent

# All 12 section IDs with YAML configs
SECTION_IDS: list[str] = [
    "executive_summary",
    "business_profile",
    "financial_health",
    "market_activity",
    "governance",
    "litigation",
    "scoring",
    "forward_looking",
    "executive_risk",
    "filing_analysis",
    "red_flags",
    "ai_risk",
]


@lru_cache(maxsize=16)
def load_narrative_config(section_id: str) -> dict[str, Any]:
    """Load narrative YAML configuration for a section.

    Args:
        section_id: Brain section identifier (e.g., "governance", "financial_health").

    Returns:
        Dict with keys: verdict, thesis_template, evidence_keys,
        implications_template, deep_context_keys.

    Raises:
        FileNotFoundError: If no YAML exists for the section_id.
    """
    yaml_path = _NARRATIVES_DIR / f"{section_id}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"No narrative config found for section '{section_id}' at {yaml_path}"
        )
    with open(yaml_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    # Validate required keys
    required = {"verdict", "thesis_template", "evidence_keys", "implications_template", "deep_context_keys"}
    missing = required - set(data.keys())
    if missing:
        logger.warning(
            "Narrative config for '%s' missing keys: %s",
            section_id,
            ", ".join(sorted(missing)),
        )
        # Fill missing with safe defaults
        for key in missing:
            if key.endswith("_keys"):
                data[key] = []
            elif key.endswith("_template"):
                data[key] = ""
            elif key == "verdict":
                data[key] = {"thresholds": {}}

    return data


def load_all_narrative_configs() -> dict[str, dict[str, Any]]:
    """Load narrative configs for all 12 sections.

    Returns:
        Dict keyed by section_id -> narrative config dict.
        Sections with missing YAML files are skipped with a warning.
    """
    configs: dict[str, dict[str, Any]] = {}
    for section_id in SECTION_IDS:
        try:
            configs[section_id] = load_narrative_config(section_id)
        except FileNotFoundError:
            logger.warning("No narrative YAML for section '%s' — skipping", section_id)
    return configs


__all__ = ["SECTION_IDS", "load_all_narrative_configs", "load_narrative_config"]
