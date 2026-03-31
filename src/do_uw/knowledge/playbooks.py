"""Industry playbook activation and query API.

Provides functions to load pre-defined industry playbooks into the
knowledge store, activate the correct playbook based on SIC/NAICS
codes during RESOLVE stage, and query playbook contents for downstream
stages (checks, questions, scoring adjustments, claim theories).

Usage:
    from do_uw.knowledge.playbooks import activate_playbook, load_playbooks
    from do_uw.knowledge.store import KnowledgeStore

    store = KnowledgeStore()
    load_playbooks(store)
    playbook = activate_playbook("3571", "5112", store)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from do_uw.knowledge.models import Check as CheckORM
from do_uw.knowledge.models import IndustryPlaybook
from do_uw.knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)


def load_playbooks(store: KnowledgeStore) -> int:
    """Load all pre-defined industry playbooks into the knowledge store.

    Idempotent: skips playbooks that already exist (by ID).

    Args:
        store: KnowledgeStore instance to load playbooks into.

    Returns:
        Number of new playbooks inserted (0 if all already exist).
    """
    from do_uw.knowledge.playbook_data import INDUSTRY_PLAYBOOKS

    now = datetime.now(UTC)
    inserted = 0

    with store.get_session() as session:
        for pb_data in INDUSTRY_PLAYBOOKS:
            pb_id = pb_data["id"]
            existing = session.get(IndustryPlaybook, pb_id)
            if existing is not None:
                continue

            pb = IndustryPlaybook(
                id=pb_id,
                name=pb_data["name"],
                description=pb_data.get("description"),
                sic_ranges=pb_data["sic_ranges"],
                naics_prefixes=pb_data["naics_prefixes"],
                check_overrides=pb_data.get("industry_checks"),
                scoring_adjustments=pb_data.get("scoring_adjustments"),
                risk_patterns=pb_data.get("risk_patterns"),
                claim_theories=pb_data.get("claim_theories"),
                meeting_questions=pb_data.get("meeting_questions"),
                status="ACTIVE",
                created_at=now,
                modified_at=now,
            )
            session.add(pb)
            inserted += 1

            # Also insert industry-specific checks as INCUBATING
            _load_playbook_checks(session, pb_data, now)

    logger.info("Loaded %d new playbooks into knowledge store", inserted)
    return inserted


def _load_playbook_checks(
    session: Any,
    pb_data: dict[str, Any],
    now: datetime,
) -> None:
    """Insert industry-specific signals from a playbook as INCUBATING."""
    checks = pb_data.get("industry_checks", [])
    for signal_dict in checks:
        signal_id = signal_dict["id"]
        existing = session.get(CheckORM, signal_id)
        if existing is not None:
            continue

        check = CheckORM(
            id=signal_id,
            name=signal_dict["name"],
            section=signal_dict.get("section", 0),
            pillar=signal_dict.get("pillar", "INGESTED"),
            severity=signal_dict.get("severity"),
            execution_mode=signal_dict.get("execution_mode"),
            status="INCUBATING",
            threshold_type=signal_dict.get("threshold_type"),
            required_data=signal_dict.get("required_data", []),
            data_locations=signal_dict.get("data_locations", []),
            scoring_factor=signal_dict.get("scoring_factor"),
            output_section=signal_dict.get("output_section"),
            origin="PLAYBOOK",
            created_at=now,
            modified_at=now,
            version=1,
            metadata_json=signal_dict.get("metadata_json"),
        )
        session.add(check)


def activate_playbook(
    sic_code: str,
    naics_code: str | None,
    store: KnowledgeStore,
) -> dict[str, Any] | None:
    """Activate the matching industry playbook for a company.

    Tries SIC code first (primary), then falls back to NAICS prefix
    matching if SIC yields no result.

    Args:
        sic_code: Company SIC code from SEC EDGAR.
        naics_code: Optional NAICS code for fallback matching.
        store: KnowledgeStore with loaded playbooks.

    Returns:
        Playbook dict if a match is found, None otherwise.
    """
    # Ensure playbooks are loaded
    load_playbooks(store)

    # Try SIC match first
    result = store.get_playbook_for_sic(sic_code)
    if result is not None:
        logger.info(
            "Activated playbook '%s' for SIC %s",
            result["id"],
            sic_code,
        )
        return result

    # Fallback: NAICS prefix match
    if naics_code:
        result = _match_naics(naics_code, store)
        if result is not None:
            logger.info(
                "Activated playbook '%s' for NAICS %s (fallback)",
                result["id"],
                naics_code,
            )
            return result

    logger.debug("No playbook match for SIC=%s NAICS=%s", sic_code, naics_code)
    return None


def _match_naics(
    naics_code: str,
    store: KnowledgeStore,
) -> dict[str, Any] | None:
    """Match a NAICS code against playbook NAICS prefixes."""
    from do_uw.knowledge.playbook_data import INDUSTRY_PLAYBOOKS

    for pb_data in INDUSTRY_PLAYBOOKS:
        prefixes = pb_data.get("naics_prefixes", [])
        for prefix in prefixes:
            if naics_code.startswith(prefix):
                pb_id = pb_data["id"]
                return store.get_playbook(pb_id)
    return None


def get_industry_signals(
    store: KnowledgeStore,
    playbook_id: str,
) -> list[dict[str, Any]]:
    """Get industry-specific checks for a playbook.

    Returns the check_overrides (industry_checks) stored on the playbook.

    Args:
        store: KnowledgeStore instance.
        playbook_id: Playbook ID (e.g., "TECH_SAAS").

    Returns:
        List of check dicts, empty if playbook not found.
    """
    pb = store.get_playbook(playbook_id)
    if pb is None:
        return []
    overrides = pb.get("check_overrides")
    if isinstance(overrides, list):
        return overrides  # type: ignore[return-value]
    return []


def get_industry_questions(
    store: KnowledgeStore,
    playbook_id: str,
) -> list[str]:
    """Get meeting prep questions for a playbook.

    Args:
        store: KnowledgeStore instance.
        playbook_id: Playbook ID.

    Returns:
        List of question strings, empty if playbook not found.
    """
    pb = store.get_playbook(playbook_id)
    if pb is None:
        return []
    questions = pb.get("meeting_questions")
    if isinstance(questions, list):
        return questions  # type: ignore[return-value]
    return []


def get_scoring_adjustments(
    store: KnowledgeStore,
    playbook_id: str,
) -> dict[str, float]:
    """Get scoring weight adjustments for a playbook.

    Args:
        store: KnowledgeStore instance.
        playbook_id: Playbook ID.

    Returns:
        Dict mapping factor IDs to weight multipliers.
    """
    pb = store.get_playbook(playbook_id)
    if pb is None:
        return {}
    adjustments = pb.get("scoring_adjustments")
    if isinstance(adjustments, dict):
        return adjustments  # type: ignore[return-value]
    return {}


def get_claim_theories(
    store: KnowledgeStore,
    playbook_id: str,
) -> list[str]:
    """Get industry-specific claim theories for a playbook.

    Args:
        store: KnowledgeStore instance.
        playbook_id: Playbook ID.

    Returns:
        List of claim theory description strings.
    """
    pb = store.get_playbook(playbook_id)
    if pb is None:
        return []
    theories = pb.get("claim_theories")
    if isinstance(theories, list):
        return theories  # type: ignore[return-value]
    return []


def get_active_signals_with_industry(
    store: KnowledgeStore,
    playbook_id: str | None,
) -> list[dict[str, Any]]:
    """Get all active checks plus industry-specific checks if playbook active.

    Merges ACTIVE signals from the knowledge store with INCUBATING checks
    that belong to the specified playbook. This provides a combined set
    of checks for the ANALYZE stage.

    Args:
        store: KnowledgeStore instance.
        playbook_id: Active playbook ID, or None for generic checks only.

    Returns:
        Combined list of check dicts (ACTIVE + industry-specific).
    """
    # Get all active checks
    active_checks = store.query_checks(status="ACTIVE", limit=1000)

    if playbook_id is None:
        return active_checks

    # Get industry checks for this playbook
    industry_checks = get_industry_signals(store, playbook_id)

    # Merge without duplicates (by check ID)
    existing_ids = {c["id"] for c in active_checks}
    for ic in industry_checks:
        if ic.get("id") not in existing_ids:
            active_checks.append(ic)

    return active_checks
