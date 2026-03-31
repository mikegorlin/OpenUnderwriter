"""Migration of brain/ JSON files to the knowledge store.

Loads all 5 brain JSON files (signals.json, scoring.json, patterns.json,
red_flags.json, sectors.json) and inserts their contents into the
knowledge store with provenance tracking.

Usage:
    from do_uw.knowledge.migrate import migrate_from_json
    from do_uw.knowledge.store import KnowledgeStore

    store = KnowledgeStore(db_path=None)
    result = migrate_from_json(Path("src/do_uw/brain"), store)
    print(f"Migrated {result.checks_migrated} checks")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from do_uw.knowledge.models import (
    Check,
    Pattern,
    RedFlag,
    ScoringRule,
    Sector,
)
from do_uw.knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)


def _empty_str_list() -> list[str]:
    """Return empty list of strings (for pyright strict)."""
    return []


@dataclass
class MigrationResult:
    """Result of a brain/ JSON migration."""

    checks_migrated: int = 0
    patterns_migrated: int = 0
    rules_migrated: int = 0
    flags_migrated: int = 0
    sectors_migrated: int = 0
    errors: list[str] = field(default_factory=_empty_str_list)


def migrate_from_json(
    brain_dir: Path, store: KnowledgeStore
) -> MigrationResult:
    """Migrate all 5 brain/ JSON files into the knowledge store.

    Args:
        brain_dir: Path to the brain/ directory.
        store: KnowledgeStore instance to populate.

    Returns:
        MigrationResult with counts and any errors.
    """
    result = MigrationResult()
    now = datetime.now(UTC)

    # Migrate each file, collecting errors
    _migrate_checks(brain_dir, store, result, now)
    _migrate_scoring(brain_dir, store, result, now)
    _migrate_patterns(brain_dir, store, result, now)
    _migrate_red_flags(brain_dir, store, result, now)
    _migrate_sectors(brain_dir, store, result, now)

    return result


def _load_json(brain_dir: Path, filename: str) -> dict[str, Any]:
    """Load and parse a JSON file from brain/config/ directory."""
    # Config files live in brain/config/ (consolidated in Phase 53)
    path = brain_dir / "config" / filename
    if not path.exists():
        # Fallback to brain/ root for backward compat
        path = brain_dir / filename
    with path.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def _migrate_checks(
    brain_dir: Path,
    store: KnowledgeStore,
    result: MigrationResult,
    now: datetime,
) -> None:
    """Migrate signals.json to the knowledge store."""
    try:
        data = _load_json(brain_dir, "signals.json")
    except Exception as e:
        result.errors.append(f"signals.json load failed: {e}")
        return

    raw_checks = data.get("signals", [])
    if not isinstance(raw_checks, list):
        result.errors.append("signals.json: 'signals' is not a list")
        return

    checks_list = cast(list[Any], raw_checks)
    orm_checks: list[Check] = []

    for raw in checks_list:
        if not isinstance(raw, dict):
            continue
        check = cast(dict[str, Any], raw)
        threshold = check.get("threshold", {})
        threshold_type = None
        threshold_value = None
        if isinstance(threshold, dict):
            threshold_dict = cast(dict[str, Any], threshold)
            threshold_type = str(threshold_dict.get("type", ""))
            # Extract threshold value for numeric thresholds
            val = threshold_dict.get("value")
            if val is not None:
                threshold_value = str(val)
            elif "values" in threshold_dict:
                threshold_value = json.dumps(threshold_dict["values"])

        # Extract scoring factor from check's factors list
        factors_raw = check.get("factors", [])
        scoring_factor = None
        if isinstance(factors_raw, list):
            factors_list = cast(list[Any], factors_raw)
            if len(factors_list) > 0:
                scoring_factor = str(factors_list[0])

        # Extract enriched Phase 31 fields
        content_type = check.get("content_type")
        depth = check.get("depth")
        rationale = check.get("rationale")
        pattern_ref = check.get("pattern_ref")

        # field_key and extraction_path from data_strategy sub-dict
        ds = check.get("data_strategy")
        ds_field_key: str | None = None
        ds_extraction_path: str | None = None
        if isinstance(ds, dict):
            ds_dict = cast(dict[str, Any], ds)
            ds_field_key = ds_dict.get("field_key")
            ds_extraction_path = ds_dict.get("extraction_path")

        orm_checks.append(
            Check(
                id=str(check["id"]),
                name=str(check["name"]),
                section=int(check.get("section", 0)),
                pillar=str(check.get("pillar", "")),
                severity=None,
                execution_mode=check.get("execution_mode"),
                status="ACTIVE",
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                required_data=check.get("required_data", []),
                data_locations=check.get("data_locations", {}),
                scoring_factor=scoring_factor,
                scoring_rule=None,
                output_section=None,
                origin="BRAIN_MIGRATION",
                created_at=now,
                modified_at=now,
                version=1,
                metadata_json=json.dumps(check),
                # Phase 31 enriched fields
                content_type=content_type,
                depth=depth,
                rationale=rationale,
                field_key=ds_field_key,
                extraction_path=ds_extraction_path,
                pattern_ref=pattern_ref,
            )
        )

    if orm_checks:
        result.checks_migrated = store.bulk_insert_checks(orm_checks)

    # Store full signals.json as metadata for backward compat
    store.store_metadata("checks_raw", data)


def _migrate_scoring(
    brain_dir: Path,
    store: KnowledgeStore,
    result: MigrationResult,
    now: datetime,
) -> None:
    """Migrate scoring.json to the knowledge store."""
    try:
        data = _load_json(brain_dir, "scoring.json")
    except Exception as e:
        result.errors.append(f"scoring.json load failed: {e}")
        return

    factors_raw = data.get("factors", {})
    if not isinstance(factors_raw, dict):
        result.errors.append("scoring.json: 'factors' is not a dict")
        return

    factors = cast(dict[str, Any], factors_raw)
    orm_rules: list[ScoringRule] = []

    for factor_key, factor_data in factors.items():
        if not isinstance(factor_data, dict):
            continue
        factor = cast(dict[str, Any], factor_data)
        rules_raw = factor.get("rules", [])
        if not isinstance(rules_raw, list):
            continue
        rules = cast(list[Any], rules_raw)
        for rule_raw in rules:
            if not isinstance(rule_raw, dict):
                continue
            rule = cast(dict[str, Any], rule_raw)
            orm_rules.append(
                ScoringRule(
                    id=str(rule["id"]),
                    factor_id=factor_key,
                    condition=str(rule.get("condition", "")),
                    points=float(rule.get("points", 0)),
                    triggers_crf=rule.get("triggers_crf"),
                    created_at=now,
                )
            )

    if orm_rules:
        result.rules_migrated = store.bulk_insert_scoring_rules(orm_rules)

    # Store full scoring.json as metadata (critical for backward compat)
    store.store_metadata("scoring_raw", data)


def _migrate_patterns(
    brain_dir: Path,
    store: KnowledgeStore,
    result: MigrationResult,
    now: datetime,
) -> None:
    """Migrate patterns.json to the knowledge store."""
    try:
        data = _load_json(brain_dir, "patterns.json")
    except Exception as e:
        result.errors.append(f"patterns.json load failed: {e}")
        return

    raw_patterns = data.get("patterns", [])
    if not isinstance(raw_patterns, list):
        result.errors.append("patterns.json: 'patterns' is not a list")
        return

    patterns_list = cast(list[Any], raw_patterns)
    orm_patterns: list[Pattern] = []

    for raw in patterns_list:
        if not isinstance(raw, dict):
            continue
        p = cast(dict[str, Any], raw)
        severity_mods = p.get("severity_modifiers")
        severity_modifier = None
        if severity_mods is not None:
            severity_modifier = json.dumps(severity_mods)

        orm_patterns.append(
            Pattern(
                id=str(p["id"]),
                name=str(p.get("name", "")),
                category=str(p.get("category", "")),
                description=p.get("description"),
                allegation_types=p.get("allegation_types", []),
                trigger_conditions=p.get("trigger_conditions", []),
                score_impact=p.get("score_impact", {}),
                severity_modifier=severity_modifier,
                status="ACTIVE",
                created_at=now,
                modified_at=now,
            )
        )

    if orm_patterns:
        result.patterns_migrated = store.bulk_insert_patterns(orm_patterns)

    # Store full patterns.json as metadata
    store.store_metadata("patterns_raw", data)


def _migrate_red_flags(
    brain_dir: Path,
    store: KnowledgeStore,
    result: MigrationResult,
    now: datetime,
) -> None:
    """Migrate red_flags.json to the knowledge store."""
    try:
        data = _load_json(brain_dir, "red_flags.json")
    except Exception as e:
        result.errors.append(f"red_flags.json load failed: {e}")
        return

    triggers_raw = data.get("escalation_triggers", [])
    if not isinstance(triggers_raw, list):
        result.errors.append(
            "red_flags.json: 'escalation_triggers' is not a list"
        )
        return

    triggers = cast(list[Any], triggers_raw)
    orm_flags: list[RedFlag] = []

    for raw in triggers:
        if not isinstance(raw, dict):
            continue
        flag = cast(dict[str, Any], raw)
        orm_flags.append(
            RedFlag(
                id=str(flag["id"]),
                name=str(flag.get("name", flag["id"])),
                condition=str(flag.get("condition", "")),
                detection_logic=flag.get("detection_logic"),
                max_tier=str(flag.get("max_tier", "WALK")),
                max_quality_score=float(
                    flag.get("max_quality_score", 30)
                ),
                status="ACTIVE",
                created_at=now,
            )
        )

    if orm_flags:
        result.flags_migrated = store.bulk_insert_red_flags(orm_flags)

    # Store full red_flags.json as metadata
    store.store_metadata("red_flags_raw", data)


def _migrate_sectors(
    brain_dir: Path,
    store: KnowledgeStore,
    result: MigrationResult,
    now: datetime,
) -> None:
    """Migrate sectors.json to the knowledge store."""
    try:
        data = _load_json(brain_dir, "sectors.json")
    except Exception as e:
        result.errors.append(f"sectors.json load failed: {e}")
        return

    orm_sectors: list[Sector] = []
    # Sections with per-sector baselines
    metric_sections = [
        "short_interest",
        "volatility_90d",
        "leverage_debt_ebitda",
        "cash_runway_biotech",
        "guidance_miss_sector_adjustments",
        "insider_trading_sector_context",
        "sector_etfs",
        "dismissal_rates",
        "claim_base_rates",
        "market_cap_filing_multipliers",
    ]

    for section_name in metric_sections:
        section_data = data.get(section_name)
        if section_data is None:
            continue
        if isinstance(section_data, dict):
            section_dict = cast(dict[str, Any], section_data)
            _extract_sector_entries(
                section_dict, section_name, orm_sectors, now
            )

    if orm_sectors:
        result.sectors_migrated = store.bulk_insert_sectors(orm_sectors)

    # Store full sectors.json as metadata
    store.store_metadata("sectors_raw", data)


def _extract_sector_entries(
    section_dict: dict[str, Any],
    metric_name: str,
    orm_sectors: list[Sector],
    now: datetime,
) -> None:
    """Extract sector entries from a section dict."""
    # Skip metadata fields (description, source, etc.)
    skip_keys = {
        "description", "source", "calculation", "note",
        "thresholds",
    }
    for key, value in section_dict.items():
        if key in skip_keys:
            continue
        # Determine baseline value
        baseline = _extract_baseline(value)
        # Store full value as metadata for reconstruction
        metadata = None
        if isinstance(value, dict):
            metadata = json.dumps(value)
        elif isinstance(value, (int, float)):
            metadata = None  # baseline_value is sufficient

        orm_sectors.append(
            Sector(
                sector_code=key,
                metric_name=metric_name,
                baseline_value=baseline,
                metadata_json=metadata,
                created_at=now,
            )
        )


def _extract_baseline(value: Any) -> float:
    """Extract a baseline float value from various formats."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        val_dict = cast(dict[str, Any], value)
        # Try common baseline keys
        for key in ("normal", "typical", "rate", "multiplier"):
            v = val_dict.get(key)
            if isinstance(v, (int, float)):
                return float(v)
        # Fallback: use first numeric value found
        for v in val_dict.values():
            if isinstance(v, (int, float)):
                return float(v)
    return 0.0
