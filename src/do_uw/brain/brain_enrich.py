"""Brain enrichment: apply risk question, hazard, and framework metadata.

Enriches all brain_signals rows with metadata from enrichment_data.py:
- report_section (from prefix mapping)
- risk_questions (from explicit or subdomain-default mappings)
- hazards (from check-to-hazard mappings)
- risk_framework_layer (inherent_risk, peril_indicator, or risk_modifier)
- characteristic_direction and characteristic_strength

Creates version 2 rows (append-only) and populates brain_changelog.

Also provides remap_to_v6() for upgrading existing databases from Q1-Q25
to v6 subsection IDs (X.Y format). For fresh migrations, enrichment
already uses v6 IDs, so remap_to_v6() is idempotent.
"""

from __future__ import annotations

import re

import duckdb

from do_uw.brain.enrichment_data import (
    CHECK_TO_CHARACTERISTIC,
    CHECK_TO_HAZARDS,
    CHECK_TO_RISK_FRAMEWORK_LAYER,
    CHECK_TO_RISK_QUESTIONS,
    PREFIX_TO_REPORT_SECTION,
    SUBDOMAIN_TO_RISK_QUESTIONS,
)


def _resolve_risk_questions(signal_id: str) -> list[str]:
    """Resolve risk questions for a check via explicit or subdomain default."""
    if signal_id in CHECK_TO_RISK_QUESTIONS:
        return CHECK_TO_RISK_QUESTIONS[signal_id]

    subdomain = ".".join(signal_id.split(".")[:2])
    if subdomain in SUBDOMAIN_TO_RISK_QUESTIONS:
        return SUBDOMAIN_TO_RISK_QUESTIONS[subdomain]

    return []


def _resolve_report_section(signal_id: str) -> str:
    """Resolve report section from prefix."""
    prefix = signal_id.split(".")[0]
    return PREFIX_TO_REPORT_SECTION.get(prefix, "company")


def _resolve_framework_layer(signal_id: str) -> str:
    """Resolve risk framework layer, defaulting to risk_modifier."""
    return CHECK_TO_RISK_FRAMEWORK_LAYER.get(signal_id, "risk_modifier")


def _resolve_hazards(signal_id: str) -> list[str]:
    """Resolve hazard codes for a check."""
    return CHECK_TO_HAZARDS.get(signal_id, [])


def _resolve_characteristic(signal_id: str) -> tuple[str | None, str | None]:
    """Resolve characteristic direction and strength."""
    if signal_id in CHECK_TO_CHARACTERISTIC:
        return CHECK_TO_CHARACTERISTIC[signal_id]
    return (None, None)


def enrich_brain_signals(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Apply enrichment data to brain_signals rows in DuckDB.

    For each check in brain_signals_current, creates a new version row
    with enriched metadata (report_section, risk_questions, hazards,
    risk_framework_layer, characteristic_direction, characteristic_strength).

    Also inserts brain_changelog entries for each enriched check.

    Args:
        conn: Active DuckDB connection with brain schema and v1 data.

    Returns:
        Dict with enrichment counts.
    """
    # Read all current checks (including Wave 1 new columns at positions 34-47)
    rows = conn.execute(
        """SELECT signal_id, version, name, content_type, lifecycle_state,
                  depth, execution_mode, report_section, risk_questions,
                  risk_framework_layer, factors, hazards,
                  characteristic_direction, characteristic_strength,
                  threshold_type, threshold_red, threshold_yellow, threshold_clear,
                  pattern_ref, question, rationale, interpretation,
                  field_key, required_data, data_locations, acquisition_type,
                  extraction_hints,
                  industry_scope, applicable_industries, industry_threshold_overrides,
                  expected_fire_rate, last_calibrated, calibration_notes,
                  pillar, category, signal_type, hazard_or_signal,
                  plaintiff_lenses, claims_correlation, amplifier,
                  amplifier_bonus_points, tier, section_number,
                  sector_adjustments, v6_subsection_ids, data_strategy,
                  threshold_full
           FROM brain_signals_current
           ORDER BY signal_id"""
    ).fetchall()

    # Build enriched version rows
    insert_rows: list[tuple] = []
    changelog_rows: list[tuple] = []
    stats = {
        "enriched": 0,
        "with_questions": 0,
        "with_hazards": 0,
        "with_characteristics": 0,
        "inherent_risk": 0,
        "peril_indicator_layer": 0,
        "risk_modifier": 0,
    }

    for row in rows:
        signal_id = row[0]
        old_version = row[1]
        new_version = old_version + 1

        # Resolve enrichment
        report_section = _resolve_report_section(signal_id)
        risk_questions = _resolve_risk_questions(signal_id)
        risk_framework_layer = _resolve_framework_layer(signal_id)
        hazards_list = _resolve_hazards(signal_id)
        char_direction, char_strength = _resolve_characteristic(signal_id)

        # Track stats
        stats["enriched"] += 1
        if risk_questions:
            stats["with_questions"] += 1
        if hazards_list:
            stats["with_hazards"] += 1
        if char_direction is not None:
            stats["with_characteristics"] += 1
        if risk_framework_layer == "inherent_risk":
            stats["inherent_risk"] += 1
        elif risk_framework_layer == "peril_indicator":
            stats["peril_indicator_layer"] += 1
        else:
            stats["risk_modifier"] += 1

        # Build new version row (copy previous fields, override enrichment fields)
        # Column order matches SELECT: 0-32 original, 33-46 Wave 1 new
        insert_rows.append((
            signal_id,
            new_version,
            row[2],   # name
            row[3],   # content_type
            row[4],   # lifecycle_state
            row[5],   # depth
            row[6],   # execution_mode
            report_section,
            risk_questions,
            risk_framework_layer,
            row[10],  # factors (unchanged)
            hazards_list,
            char_direction,
            char_strength,
            row[14],  # threshold_type
            row[15],  # threshold_red
            row[16],  # threshold_yellow
            row[17],  # threshold_clear
            row[18],  # pattern_ref
            row[19],  # question
            row[20],  # rationale
            row[21],  # interpretation
            row[22],  # field_key
            row[23],  # required_data
            row[24],  # data_locations
            row[25],  # acquisition_type
            row[26],  # extraction_hints (carry forward)
            row[27],  # industry_scope
            row[28],  # applicable_industries
            row[29],  # industry_threshold_overrides
            row[30],  # expected_fire_rate
            row[31],  # last_calibrated
            row[32],  # calibration_notes
            # Wave 1 new columns (carry forward)
            row[33],  # pillar
            row[34],  # category
            row[35],  # signal_type
            row[36],  # hazard_or_signal
            row[37],  # plaintiff_lenses
            row[38],  # claims_correlation
            row[39],  # amplifier
            row[40],  # amplifier_bonus_points
            row[41],  # tier
            row[42],  # section_number
            row[43],  # sector_adjustments
            row[44],  # v6_subsection_ids
            row[45],  # data_strategy
            row[46],  # threshold_full
            "phase_32_enrichment",  # created_by
            "Phase 32 enrichment: added risk questions, hazards, report section, framework layer",
        ))

        # Build fields_changed list
        fields_changed = ["report_section", "risk_questions", "risk_framework_layer"]
        if hazards_list:
            fields_changed.append("hazards")
        if char_direction is not None:
            fields_changed.extend(["characteristic_direction", "characteristic_strength"])

        changelog_rows.append((
            signal_id,
            old_version,
            new_version,
            "MODIFIED",
            "Phase 32 enrichment: added risk questions, hazards, report section, framework layer",
            fields_changed,
            "phase_32_enrichment",
            "Automated enrichment from enrichment_data.py mappings",
            "phase_32_enrichment",
        ))

    # Batch insert new version rows (49 columns)
    conn.executemany(
        """INSERT INTO brain_signals (
            signal_id, version, name, content_type, lifecycle_state,
            depth, execution_mode, report_section, risk_questions,
            risk_framework_layer, factors, hazards,
            characteristic_direction, characteristic_strength,
            threshold_type, threshold_red, threshold_yellow, threshold_clear,
            pattern_ref, question, rationale, interpretation,
            field_key, required_data, data_locations, acquisition_type,
            extraction_hints,
            industry_scope, applicable_industries, industry_threshold_overrides,
            expected_fire_rate, last_calibrated, calibration_notes,
            pillar, category, signal_type, hazard_or_signal,
            plaintiff_lenses, claims_correlation, amplifier,
            amplifier_bonus_points, tier, section_number,
            sector_adjustments, v6_subsection_ids, data_strategy,
            threshold_full,
            created_by, change_description
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?
        )""",
        insert_rows,
    )

    # Batch insert changelog entries
    conn.executemany(
        """INSERT INTO brain_changelog (
            signal_id, old_version, new_version,
            change_type, change_description, fields_changed,
            changed_by, change_reason, triggered_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        changelog_rows,
    )

    return stats


def _has_old_q_ids(risk_questions: list[str]) -> bool:
    """Check if risk_questions list contains old Q1-Q25 identifiers."""
    return any(q.startswith("Q") and q[1:].isdigit() for q in risk_questions)


def _is_v6_format(risk_questions: list[str]) -> bool:
    """Check if all risk_questions use v6 X.Y subsection format."""
    return all(re.match(r"^\d+\.\d+$", q) for q in risk_questions)


def remap_to_v6(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Remap brain_signals from old Q1-Q25 to v6 subsection IDs.

    For each check in brain_signals_current:
    - If risk_questions already use v6 format (X.Y), skip (idempotent)
    - If risk_questions contain old Q-IDs, resolve new v6 IDs from
      enrichment_data.py and create a new version row

    Also inserts brain_changelog entries documenting the transition.

    Args:
        conn: Active DuckDB connection with brain schema and enriched data.

    Returns:
        Dict with remap counts: remapped, already_v6, errors.
    """
    rows = conn.execute(
        """SELECT signal_id, version, name, content_type, lifecycle_state,
                  depth, execution_mode, report_section, risk_questions,
                  risk_framework_layer, factors, hazards,
                  characteristic_direction, characteristic_strength,
                  threshold_type, threshold_red, threshold_yellow, threshold_clear,
                  pattern_ref, question, rationale, interpretation,
                  field_key, required_data, data_locations, acquisition_type,
                  extraction_hints,
                  industry_scope, applicable_industries, industry_threshold_overrides,
                  expected_fire_rate, last_calibrated, calibration_notes,
                  pillar, category, signal_type, hazard_or_signal,
                  plaintiff_lenses, claims_correlation, amplifier,
                  amplifier_bonus_points, tier, section_number,
                  sector_adjustments, v6_subsection_ids, data_strategy,
                  threshold_full
           FROM brain_signals_current
           ORDER BY signal_id"""
    ).fetchall()

    insert_rows: list[tuple] = []
    changelog_rows: list[tuple] = []
    stats = {"remapped": 0, "already_v6": 0, "errors": 0}

    for row in rows:
        signal_id = row[0]
        old_version = row[1]
        current_questions = row[8] or []

        # Check if already v6 format
        if not current_questions or _is_v6_format(current_questions):
            new_questions = _resolve_risk_questions(signal_id)
            new_section = _resolve_report_section(signal_id)
            if new_questions == list(current_questions) and new_section == row[7]:
                stats["already_v6"] += 1
                continue

        new_questions = _resolve_risk_questions(signal_id)
        new_section = _resolve_report_section(signal_id)

        if not new_questions:
            stats["errors"] += 1
            continue

        new_version = old_version + 1

        # Build remap version row (49 columns)
        insert_rows.append((
            signal_id,
            new_version,
            row[2],   # name
            row[3],   # content_type
            row[4],   # lifecycle_state
            row[5],   # depth
            row[6],   # execution_mode
            new_section,
            new_questions,
            row[9],   # risk_framework_layer
            row[10],  # factors
            row[11],  # hazards
            row[12],  # characteristic_direction
            row[13],  # characteristic_strength
            row[14],  # threshold_type
            row[15],  # threshold_red
            row[16],  # threshold_yellow
            row[17],  # threshold_clear
            row[18],  # pattern_ref
            row[19],  # question
            row[20],  # rationale
            row[21],  # interpretation
            row[22],  # field_key
            row[23],  # required_data
            row[24],  # data_locations
            row[25],  # acquisition_type
            row[26],  # extraction_hints
            row[27],  # industry_scope
            row[28],  # applicable_industries
            row[29],  # industry_threshold_overrides
            row[30],  # expected_fire_rate
            row[31],  # last_calibrated
            row[32],  # calibration_notes
            row[33],  # pillar
            row[34],  # category
            row[35],  # signal_type
            row[36],  # hazard_or_signal
            row[37],  # plaintiff_lenses
            row[38],  # claims_correlation
            row[39],  # amplifier
            row[40],  # amplifier_bonus_points
            row[41],  # tier
            row[42],  # section_number
            row[43],  # sector_adjustments
            row[44],  # v6_subsection_ids
            row[45],  # data_strategy
            row[46],  # threshold_full
            "phase_32_v6_remap",
            "Phase 32 v6 remap: risk_questions updated to v6 subsection IDs",
        ))

        old_qs = list(current_questions) if current_questions else []
        changelog_rows.append((
            signal_id,
            old_version,
            new_version,
            "MODIFIED",
            f"Phase 32 v6 remap: risk_questions {old_qs} -> {new_questions}",
            ["risk_questions", "report_section"],
            "phase_32_v6_remap",
            "Taxonomy remap from Q1-Q25 to v6 subsection IDs (QUESTIONS-FINAL.md)",
            "phase_32_v6_remap",
        ))
        stats["remapped"] += 1

    if insert_rows:
        conn.executemany(
            """INSERT INTO brain_signals (
                signal_id, version, name, content_type, lifecycle_state,
                depth, execution_mode, report_section, risk_questions,
                risk_framework_layer, factors, hazards,
                characteristic_direction, characteristic_strength,
                threshold_type, threshold_red, threshold_yellow, threshold_clear,
                pattern_ref, question, rationale, interpretation,
                field_key, required_data, data_locations, acquisition_type,
                extraction_hints,
                industry_scope, applicable_industries, industry_threshold_overrides,
                expected_fire_rate, last_calibrated, calibration_notes,
                pillar, category, signal_type, hazard_or_signal,
                plaintiff_lenses, claims_correlation, amplifier,
                amplifier_bonus_points, tier, section_number,
                sector_adjustments, v6_subsection_ids, data_strategy,
                threshold_full,
                created_by, change_description
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )""",
            insert_rows,
        )

    if changelog_rows:
        conn.executemany(
            """INSERT INTO brain_changelog (
                signal_id, old_version, new_version,
                change_type, change_description, fields_changed,
                changed_by, change_reason, triggered_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            changelog_rows,
        )

    return stats
