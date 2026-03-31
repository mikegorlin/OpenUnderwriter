"""Brain framework migration: YAML → DuckDB.

Reads framework YAML files (source of truth) and populates DuckDB
tables for runtime query performance. Called by ``brain build``.

Tables populated:
  brain_perils          — 8 D&O claim perils with HAZ code groupings
  brain_causal_chains   — ~18 claim pathways from trigger to loss
  brain_risk_framework  — Layer/pillar/factor dimension definitions

Also tags brain_signals with peril_id and chain_ids columns.
"""

# DEPRECATED: 2026-02-25
# This file is no longer called by brain build. Knowledge is now loaded from
# src/do_uw/brain/signals/**/*.yaml via brain_migrate_yaml.py and brain_migrate.py.
# Do not delete — kept for reference and emergency rollback only.
# See src/do_uw/brain/SCHEMA.md for the current architecture.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb
import yaml

logger = logging.getLogger(__name__)


def _framework_dir() -> Path:
    """Return path to brain/framework/ directory."""
    return Path(__file__).parent.parent / "framework"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from the framework directory."""
    path = _framework_dir() / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------
# Peril migration
# ---------------------------------------------------------------

def migrate_perils(conn: duckdb.DuckDBPyConnection) -> int:
    """Populate brain_perils from perils.yaml.

    Non-destructive: clears and repopulates (YAML is authoritative).

    Returns:
        Number of perils inserted.
    """
    data = _load_yaml("perils.yaml")
    perils = data.get("perils", [])

    conn.execute("DELETE FROM brain_perils")

    count = 0
    for peril in perils:
        conn.execute(
            """INSERT INTO brain_perils (
                peril_id, name, description, haz_codes,
                frequency, severity, typical_settlement_range,
                key_drivers, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                peril["id"],
                peril["name"],
                peril.get("description", ""),
                peril.get("haz_codes", []),
                peril.get("frequency", "unknown"),
                peril.get("severity", "unknown"),
                peril.get("typical_settlement_range", ""),
                peril.get("key_drivers", []),
                data.get("version", 1),
            ],
        )
        count += 1

    logger.info("Migrated %d perils from perils.yaml", count)
    return count


# ---------------------------------------------------------------
# Causal chain migration
# ---------------------------------------------------------------

def migrate_causal_chains(conn: duckdb.DuckDBPyConnection) -> int:
    """Populate brain_causal_chains from causal_chains.yaml.

    Non-destructive: clears and repopulates (YAML is authoritative).

    Returns:
        Number of chains inserted.
    """
    data = _load_yaml("causal_chains.yaml")
    chains = data.get("chains", [])

    conn.execute("DELETE FROM brain_causal_chains")

    count = 0
    for chain in chains:
        conn.execute(
            """INSERT INTO brain_causal_chains (
                chain_id, name, peril_id, description,
                trigger_signals, amplifier_signals,
                mitigator_signals, evidence_signals,
                frequency_factors, severity_factors,
                patterns, red_flags,
                historical_filing_rate, median_severity_usd,
                version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                chain["id"],
                chain["name"],
                chain["peril_id"],
                chain.get("description", ""),
                chain.get("trigger_signals", []),
                chain.get("amplifier_signals", []),
                chain.get("mitigator_signals", []),
                chain.get("evidence_signals", []),
                chain.get("frequency_factors", []),
                chain.get("severity_factors", []),
                chain.get("patterns", []),
                chain.get("red_flags", []),
                chain.get("historical_filing_rate"),
                chain.get("median_severity_usd"),
                data.get("version", 1),
            ],
        )
        count += 1

    logger.info("Migrated %d causal chains from causal_chains.yaml", count)
    return count


# ---------------------------------------------------------------
# Risk framework migration (layers, pillars, factor dimensions)
# ---------------------------------------------------------------

def migrate_risk_framework(conn: duckdb.DuckDBPyConnection) -> int:
    """Populate brain_risk_framework from taxonomy.yaml and risk_model.yaml.

    Returns:
        Number of framework entries inserted.
    """
    taxonomy = _load_yaml("taxonomy.yaml")
    risk_model = _load_yaml("risk_model.yaml")

    conn.execute("DELETE FROM brain_risk_framework")

    count = 0

    # Pillars
    for pillar in taxonomy.get("pillars", []):
        conn.execute(
            """INSERT INTO brain_risk_framework (
                entity_type, entity_id, legacy_id, name,
                description, sort_order, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                "pillar",
                pillar["id"],
                pillar.get("legacy_id"),
                pillar["name"],
                pillar.get("description", ""),
                pillar.get("order"),
                None,
            ],
        )
        count += 1

    # Layers
    for layer in taxonomy.get("layers", []):
        conn.execute(
            """INSERT INTO brain_risk_framework (
                entity_type, entity_id, legacy_id, name,
                description, sort_order, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                "layer",
                layer["id"],
                layer.get("legacy_id"),
                layer["name"],
                layer.get("description", ""),
                None,
                None,
            ],
        )
        count += 1

    # Factor dimensions
    for factor_id, factor_data in risk_model.get("factor_dimensions", {}).items():
        conn.execute(
            """INSERT INTO brain_risk_framework (
                entity_type, entity_id, legacy_id, name,
                description, sort_order, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                "factor_dimension",
                factor_id,
                None,
                factor_data["name"],
                factor_data.get("rationale", ""),
                None,
                json.dumps({"role": factor_data["role"]}),
            ],
        )
        count += 1

    logger.info("Migrated %d risk framework entries", count)
    return count


# ---------------------------------------------------------------
# Check peril tagging
# ---------------------------------------------------------------

def _build_haz_to_peril_map(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Build HAZ-code → peril_id mapping from brain_perils."""
    rows = conn.execute(
        "SELECT peril_id, haz_codes FROM brain_perils"
    ).fetchall()
    mapping: dict[str, str] = {}
    for peril_id, haz_codes in rows:
        if haz_codes:
            for haz in haz_codes:
                mapping[haz] = peril_id
    return mapping


def _build_check_to_chains(conn: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    """Build signal_id → [chain_ids] mapping from brain_causal_chains."""
    rows = conn.execute(
        """SELECT chain_id, trigger_signals, amplifier_signals,
                  mitigator_signals, evidence_signals
           FROM brain_causal_chains"""
    ).fetchall()

    mapping: dict[str, list[str]] = {}
    for chain_id, triggers, amplifiers, mitigators, evidence in rows:
        all_checks: list[str] = []
        for check_list in [triggers, amplifiers, mitigators, evidence]:
            if check_list:
                all_checks.extend(check_list)
        for signal_id in all_checks:
            mapping.setdefault(signal_id, []).append(chain_id)
    return mapping


def tag_checks_with_perils_and_chains(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, int]:
    """Tag brain_signals_active with peril_id and chain_ids.

    Derives peril_id from existing hazard mappings via the
    HAZ-code → peril lookup. Derives chain_ids from causal chain
    membership.

    Returns:
        Dict with counts: tagged_peril, tagged_chains, total_checked.
    """
    haz_to_peril = _build_haz_to_peril_map(conn)
    check_to_chains = _build_check_to_chains(conn)

    # Read all active checks with their hazards
    rows = conn.execute(
        "SELECT signal_id, hazards FROM brain_signals_active"
    ).fetchall()

    stats = {"tagged_peril": 0, "tagged_chains": 0, "total_checked": 0}

    for signal_id, hazards in rows:
        stats["total_checked"] += 1

        # Determine primary peril from hazards
        peril_id = None
        if hazards:
            for haz in hazards:
                if haz in haz_to_peril:
                    peril_id = haz_to_peril[haz]
                    break

        # Get chain IDs
        chain_ids = check_to_chains.get(signal_id, [])

        # Update check (only if we have something to add)
        if peril_id or chain_ids:
            conn.execute(
                """UPDATE brain_signals
                   SET peril_id = ?, chain_ids = ?
                   WHERE signal_id = ? AND (signal_id, version) IN (
                       SELECT signal_id, MAX(version)
                       FROM brain_signals
                       GROUP BY signal_id
                   )""",
                [peril_id, chain_ids if chain_ids else None, signal_id],
            )

            if peril_id:
                stats["tagged_peril"] += 1
            if chain_ids:
                stats["tagged_chains"] += 1

    logger.info(
        "Tagged %d signals with perils, %d with chains (of %d total)",
        stats["tagged_peril"],
        stats["tagged_chains"],
        stats["total_checked"],
    )
    return stats


# ---------------------------------------------------------------
# Full framework build (called by `brain build`)
# ---------------------------------------------------------------

def build_framework(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Run full framework migration: YAML → DuckDB.

    Reads all framework YAML files and populates DuckDB tables.
    This is the authoritative build step — YAML is source of truth.

    Args:
        conn: Active DuckDB connection with brain schema.

    Returns:
        Dict with migration counts.
    """
    from do_uw.brain.brain_schema import create_schema

    create_schema(conn)  # Ensure Phase 42 tables exist

    results: dict[str, Any] = {}

    results["perils"] = migrate_perils(conn)
    results["chains"] = migrate_causal_chains(conn)
    results["framework_entries"] = migrate_risk_framework(conn)
    results["check_tags"] = tag_checks_with_perils_and_chains(conn)

    logger.info("Framework build complete: %s", results)
    return results
