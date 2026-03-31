"""Unified BrainLoader: read YAML signals and JSON configs at runtime.

Single loader replacing BrainDBLoader, BrainKnowledgeLoader,
BackwardCompatLoader, and ConfigLoader. Reads brain/signals/ YAML
and brain/config/ JSON directly -- no DuckDB intermediary for
definitions. DuckDB is used only for history data (load_backlog).

Module-level singleton caching: load once on first call, serve from
memory for duration of run. _reset_cache() available for testing.

Usage:
    from do_uw.brain.brain_unified_loader import load_signals, load_config
    signals = load_signals()  # {"signals": [...], "total_signals": 400}
    scoring = load_config("scoring")  # parsed JSON dict

    # Or via class instance (matches BrainDBLoader interface):
    from do_uw.brain.brain_unified_loader import BrainLoader
    loader = BrainLoader()
    brain = loader.load_all()  # BrainConfig
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from do_uw.brain.brain_enrichment import SECTION_MAP, enrich_signal

logger = logging.getLogger(__name__)
_BRAIN_DIR = Path(__file__).parent

# Re-export SECTION_MAP for backward compat (tests import it from here)
__all__ = ["SECTION_MAP"]


class BrainConfig(BaseModel):
    """Container for all validated brain knowledge domains."""

    model_config = ConfigDict(frozen=False)

    checks: dict[str, Any] = Field(default_factory=dict)
    scoring: dict[str, Any] = Field(default_factory=dict)
    patterns: dict[str, Any] = Field(default_factory=dict)
    sectors: dict[str, Any] = Field(default_factory=dict)
    red_flags: dict[str, Any] = Field(default_factory=dict)


# Module-level caches
_signals_cache: dict[str, Any] | None = None
_config_cache: dict[str, dict[str, Any]] = {}
_perils_cache: list[dict[str, Any]] | None = None
_chains_cache: list[dict[str, Any]] | None = None
_taxonomy_cache: dict[str, Any] | None = None


def _reset_cache() -> None:
    """Clear all module-level caches (for testing)."""
    global _signals_cache, _config_cache, _perils_cache, _chains_cache, _taxonomy_cache
    _signals_cache = None
    _config_cache = {}
    _perils_cache = None
    _chains_cache = None
    _taxonomy_cache = None


# ---------------------------------------------------------------
# Signal loading
# ---------------------------------------------------------------


def _load_and_validate_signals(
    signals_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Load signals from YAML, enrich, validate. Returns (signals, skipped_count)."""
    from do_uw.brain.brain_signal_schema import BrainSignalEntry

    if signals_dir is None:
        signals_dir = _BRAIN_DIR / "signals"

    all_raw: list[dict[str, Any]] = []
    for yaml_file in sorted(signals_dir.glob("**/*.yaml")):
        try:
            data = yaml.load(yaml_file.read_text(), Loader=yaml.CSafeLoader)
        except yaml.YAMLError as e:
            logger.warning("Skipping malformed YAML file %s: %s", yaml_file, e)
            continue

        if isinstance(data, list):
            all_raw.extend(data)
        elif isinstance(data, dict) and "signals" in data:
            all_raw.extend(data["signals"])

    # Enrich and validate
    validated: list[dict[str, Any]] = []
    skipped = 0
    for raw in all_raw:
        enriched = enrich_signal(raw)
        try:
            BrainSignalEntry.model_validate(enriched)
            validated.append(enriched)
        except ValidationError as e:
            signal_id = enriched.get("id", "unknown")
            logger.warning(
                "Skipping invalid signal '%s': %s", signal_id, e.errors()[0]["msg"]
            )
            skipped += 1

    return validated, skipped


def _warn_v3_fields(signals: list[dict[str, Any]]) -> None:
    """Log warnings for signals missing v3 fields and auto-infer signal_class.

    This runs post-load to provide migration progress visibility.
    V2 signals get signal_class inferred from existing type/work_type fields.
    """
    import re

    total = len(signals)
    missing_group = 0
    missing_field_path = 0
    has_depends_on = 0
    inferred_count = 0

    for sig in signals:
        sig_id = sig.get("id", "unknown")

        # Auto-infer signal_class from work_type/ID patterns when not explicitly set
        if "signal_class" not in sig or sig.get("signal_class") == "evaluative":
            if sig.get("work_type") == "infer" or (
                re.match(r"COMP\.", sig_id)
                or re.match(r"FIN\.FORENSIC\..*composite", sig_id)
            ):
                sig["signal_class"] = "inference"
                inferred_count += 1

        # Track v3 field coverage
        if not sig.get("group"):
            missing_group += 1
        if not sig.get("field_path"):
            missing_field_path += 1
        if sig.get("depends_on"):
            has_depends_on += 1

    has_group = total - missing_group
    has_field_path = total - missing_field_path

    if inferred_count > 0:
        logger.debug(
            "V3 signal_class inferred for %d signals from v2 type/work_type",
            inferred_count,
        )

    logger.debug(
        "V3 field coverage: %d/%d signals have group, %d/%d have depends_on, "
        "%d/%d have field_path",
        has_group,
        total,
        has_depends_on,
        total,
        has_field_path,
        total,
    )


def load_signals() -> dict[str, Any]:
    """Load all signals from YAML, cached for duration of process.

    Returns dict with "signals" list and "total_signals" count.
    Each signal dict includes backward-compat enrichment fields.
    """
    global _signals_cache
    if _signals_cache is not None:
        return _signals_cache

    signals, skipped = _load_and_validate_signals()

    if skipped > 0:
        logger.warning("Skipped %d invalid signals during YAML load", skipped)

    # V3 field warnings and signal_class inference
    _warn_v3_fields(signals)

    # V3 cycle detection: warn if circular dependencies exist
    from do_uw.brain.dependency_graph import detect_cycles

    cycle_members = detect_cycles(signals)
    if cycle_members:
        logger.warning(
            "Circular dependency detected among signals: %s. "
            "Dependency ordering may be incorrect.",
            " -> ".join(cycle_members),
        )

    result: dict[str, Any] = {
        "signals": signals,
        "total_signals": len(signals),
    }
    _signals_cache = result
    return result


# ---------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------


def load_config(key: str) -> dict[str, Any]:
    """Load a config JSON by key from brain/config/, cached.

    Args:
        key: Config key (e.g. "actuarial", "scoring").

    Returns:
        Parsed config dict. Empty dict + warning if not found.
    """
    if key in _config_cache:
        return _config_cache[key]

    config_dir = _BRAIN_DIR / "config"
    json_path = config_dir / f"{key}.json"
    if not json_path.exists():
        logger.warning("Config '%s' not found at %s", key, json_path)
        return {}

    with open(json_path, encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)

    _config_cache[key] = result
    logger.debug("Loaded config '%s' from %s", key, json_path)
    return result


# ---------------------------------------------------------------
# Convenience methods (delegate to load_config)
# ---------------------------------------------------------------


def load_scoring() -> dict[str, Any]:
    """Load scoring config from brain/config/scoring.json."""
    return load_config("scoring")


def load_patterns() -> dict[str, Any]:
    """Load patterns config from brain/config/patterns.json."""
    return load_config("patterns")


def load_red_flags() -> dict[str, Any]:
    """Load red flags config from brain/config/red_flags.json."""
    return load_config("red_flags")


def load_sectors() -> dict[str, Any]:
    """Load sector baselines from brain/config/sectors.json."""
    return load_config("sectors")


def load_all() -> BrainConfig:
    """Load all brain data as BrainConfig."""
    return BrainConfig(
        checks=load_signals(),
        scoring=load_scoring(),
        patterns=load_patterns(),
        sectors=load_sectors(),
        red_flags=load_red_flags(),
    )


# ---------------------------------------------------------------
# Framework data loaders
# ---------------------------------------------------------------


def load_perils() -> list[dict[str, Any]]:
    """Load perils from brain/framework/perils.yaml."""
    global _perils_cache
    if _perils_cache is not None:
        return _perils_cache

    perils_path = _BRAIN_DIR / "framework" / "perils.yaml"
    if not perils_path.exists():
        logger.warning("perils.yaml not found at %s", perils_path)
        return []

    data = yaml.load(perils_path.read_text(), Loader=yaml.CSafeLoader)
    perils = data.get("perils", []) if isinstance(data, dict) else []

    # Normalize key names for backward compat with DuckDB loader
    result: list[dict[str, Any]] = []
    for p in perils:
        entry = dict(p)
        # Ensure both "id" and "peril_id" are present
        if "id" in entry and "peril_id" not in entry:
            entry["peril_id"] = entry["id"]
        result.append(entry)

    _perils_cache = result
    return result


def load_causal_chains() -> list[dict[str, Any]]:
    """Load causal chains from brain/framework/causal_chains.yaml."""
    global _chains_cache
    if _chains_cache is not None:
        return _chains_cache

    chains_path = _BRAIN_DIR / "framework" / "causal_chains.yaml"
    if not chains_path.exists():
        logger.warning("causal_chains.yaml not found at %s", chains_path)
        return []

    data = yaml.load(chains_path.read_text(), Loader=yaml.CSafeLoader)
    chains = data.get("chains", []) if isinstance(data, dict) else []

    # Normalize key names for backward compat with DuckDB loader
    result: list[dict[str, Any]] = []
    for c in chains:
        entry = dict(c)
        if "id" in entry and "chain_id" not in entry:
            entry["chain_id"] = entry["id"]
        result.append(entry)

    _chains_cache = result
    return result


def load_taxonomy() -> dict[str, Any]:
    """Load taxonomy from brain/framework/taxonomy.yaml.

    Returns dict organized by entity type (pillars, layers, etc.)
    """
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache

    taxonomy_path = _BRAIN_DIR / "framework" / "taxonomy.yaml"
    if not taxonomy_path.exists():
        logger.warning("taxonomy.yaml not found at %s", taxonomy_path)
        return {}

    data = yaml.load(taxonomy_path.read_text(), Loader=yaml.CSafeLoader)
    if not isinstance(data, dict):
        return {}

    # Return the parsed structure directly (pillars, layers, etc.)
    result: dict[str, Any] = {
        k: v for k, v in data.items() if k != "version"
    }

    _taxonomy_cache = result
    return result


# ---------------------------------------------------------------
# History data (DuckDB -- the only method that touches DuckDB)
# ---------------------------------------------------------------


def load_backlog() -> list[dict[str, Any]]:
    """Load brain backlog items from DuckDB (history data).

    This is the ONLY method that reads from DuckDB. Backlog is
    history/planning data, not signal definitions.
    """
    try:
        from do_uw.brain.brain_schema import connect_brain_db

        conn = connect_brain_db()
        try:
            rows = conn.execute(
                """SELECT backlog_id, title, description, rationale,
                          risk_questions, hazards, priority, gap_reference,
                          estimated_effort, status, data_available
                   FROM brain_backlog WHERE status != 'CLOSED'
                   ORDER BY CASE priority WHEN 'CRITICAL' THEN 1
                       WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3
                       WHEN 'LOW' THEN 4 ELSE 5 END, backlog_id"""
            ).fetchall()
            return [
                {
                    "backlog_id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "rationale": r[3],
                    "risk_questions": r[4] or [],
                    "hazards": r[5] or [],
                    "priority": r[6],
                    "gap_reference": r[7],
                    "estimated_effort": r[8],
                    "status": r[9],
                    "data_available": r[10],
                }
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Could not load backlog from DuckDB: %s", e)
        return []


# ---------------------------------------------------------------
# Backward-compat API (matches brain_config_loader signatures)
# ---------------------------------------------------------------


def load_brain_config(
    key: str,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a config by key (backward-compat with brain_config_loader).

    The config_dir parameter is accepted but ignored -- configs are
    always read from brain/config/. This maintains API compatibility
    during migration.
    """
    return load_config(key)


def load_brain_config_or_raise(
    key: str,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a config by key, raising if not found.

    Same as load_brain_config but raises FileNotFoundError
    instead of returning empty dict when key is missing.
    """
    result = load_config(key)
    if not result:
        config_path = _BRAIN_DIR / "config" / f"{key}.json"
        raise FileNotFoundError(
            f"Config '{key}' not found at {config_path}"
        )
    return result


# ---------------------------------------------------------------
# BrainLoader class (thin wrapper for callers expecting class instance)
# ---------------------------------------------------------------


class BrainLoader:
    """Unified brain data loader: YAML signals + JSON configs.

    Thin class wrapper around module-level singleton functions.
    Matches BrainDBLoader interface for drop-in replacement.
    """

    def load_signals(self) -> dict[str, Any]:
        """Load all signals from YAML."""
        return load_signals()

    def load_scoring(self) -> dict[str, Any]:
        """Load scoring config."""
        return load_scoring()

    def load_patterns(self) -> dict[str, Any]:
        """Load patterns config."""
        return load_patterns()

    def load_red_flags(self) -> dict[str, Any]:
        """Load red flags config."""
        return load_red_flags()

    def load_sectors(self) -> dict[str, Any]:
        """Load sector baselines."""
        return load_sectors()

    def load_all(self) -> BrainConfig:
        """Load all brain data as BrainConfig."""
        return load_all()

    def load_taxonomy(self) -> dict[str, Any]:
        """Load taxonomy from framework YAML."""
        return load_taxonomy()

    def load_perils(self) -> list[dict[str, Any]]:
        """Load perils from framework YAML."""
        return load_perils()

    def load_causal_chains(self) -> list[dict[str, Any]]:
        """Load causal chains from framework YAML."""
        return load_causal_chains()

    def load_backlog(self) -> list[dict[str, Any]]:
        """Load backlog from DuckDB."""
        return load_backlog()

    @property
    def source(self) -> str:
        """Return loader source identifier."""
        return "brain_yaml"
