"""XBRL concept mapping and resolution.

Maps canonical financial concept names (e.g., "revenue") to actual XBRL
taxonomy tags using a JSON mapping table. Handles the fact that companies
use different XBRL tags for the same concept.

Usage:
    mapping = load_xbrl_mapping()
    facts = sec_client.acquire_company_facts(cik)
    entries = resolve_concept(facts, mapping, "revenue")
    latest = get_latest_value(entries) if entries else None
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypedDict

from do_uw.brain.brain_unified_loader import load_config

logger = logging.getLogger(__name__)


class XBRLConcept(TypedDict):
    """Schema for a single XBRL concept mapping entry."""

    canonical_name: str
    xbrl_tags: list[str]
    unit: str
    period_type: str  # "instant" or "duration"
    statement: str
    description: str
    expected_sign: str  # "positive", "negative", or "any"


def load_xbrl_mapping(
    path: Path | None = None,
) -> dict[str, XBRLConcept]:
    """Load and parse the XBRL concept mapping table.

    Args:
        path: Optional path to xbrl_concepts.json. Defaults to
            src/do_uw/config/xbrl_concepts.json.

    Returns:
        Dict mapping canonical concept names to XBRLConcept entries.

    Raises:
        FileNotFoundError: If mapping file does not exist.
    """
    if path is not None:
        import json
        if not path.exists():
            msg = f"XBRL mapping file not found: {path}"
            raise FileNotFoundError(msg)
        with path.open(encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
    else:
        raw = load_config("xbrl_concepts")
        if not raw:
            msg = "XBRL mapping not found in brain config or config/xbrl_concepts.json"
            raise FileNotFoundError(msg)

    mapping: dict[str, XBRLConcept] = {}
    for key, entry in raw.items():
        concept: XBRLConcept = {
            "canonical_name": str(entry.get("canonical_name", key)),
            "xbrl_tags": list(entry.get("xbrl_tags", [])),
            "unit": str(entry.get("unit", "USD")),
            "period_type": str(entry.get("period_type", "duration")),
            "statement": str(entry.get("statement", "")),
            "description": str(entry.get("description", "")),
            "expected_sign": str(entry.get("expected_sign", "any")),
        }
        mapping[key] = concept

    logger.debug("Loaded %d XBRL concept mappings", len(mapping))
    return mapping


def normalize_sign(
    value: float,
    expected_sign: str,
    concept_name: str,
) -> tuple[float, bool]:
    """Normalize a value's sign based on expected_sign convention.

    Corrects the ~12% of XBRL filings that report values with incorrect
    signs (e.g., negative revenue, positive cost of revenue).

    Args:
        value: Raw numeric value from XBRL.
        expected_sign: One of ``"positive"``, ``"negative"``, or ``"any"``.
        concept_name: Canonical concept name for logging.

    Returns:
        Tuple of (normalized_value, was_changed). ``was_changed`` is True
        only when the sign was actually flipped.
    """
    if value == 0.0:
        return (0.0, False)

    if expected_sign == "positive" and value < 0:
        logger.info(
            "Sign normalization: %s value %.2f flipped to %.2f (expected positive)",
            concept_name,
            value,
            abs(value),
        )
        return (abs(value), True)

    if expected_sign == "negative" and value > 0:
        logger.info(
            "Sign normalization: %s value %.2f flipped to %.2f (expected negative)",
            concept_name,
            value,
            -abs(value),
        )
        return (-abs(value), True)

    return (value, False)


def extract_concept_value(
    facts: dict[str, Any],
    concept: str,
    form_type: str = "10-K",
    unit: str = "USD",
) -> list[dict[str, Any]]:
    """Extract values for a specific XBRL concept from Company Facts.

    Filters by form type and deduplicates by end+fy+fp combination,
    preferring the most recently filed entry.

    Args:
        facts: Full companyfacts API response.
        concept: US GAAP concept name (e.g., "Revenues").
        form_type: Filter to specific form type (default "10-K").
        unit: Unit of measure ("USD", "shares", "pure").

    Returns:
        List of fact entries sorted by end date, deduplicated.
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    concept_data = us_gaap.get(concept, {})
    units = concept_data.get("units", {})
    entries: list[dict[str, Any]] = units.get(unit, [])

    # Filter by form type.
    filtered = [e for e in entries if e.get("form") == form_type]

    # Deduplicate by end+fy+fp, preferring most recently filed.
    seen: set[str] = set()
    deduplicated: list[dict[str, Any]] = []
    for entry in sorted(
        filtered, key=lambda e: str(e.get("filed", "")), reverse=True
    ):
        key = (
            f"{entry.get('end', '')}_{entry.get('fy', '')}"
            f"_{entry.get('fp', '')}"
        )
        if key not in seen:
            seen.add(key)
            deduplicated.append(entry)

    return sorted(deduplicated, key=lambda e: str(e.get("end", "")))


def resolve_concept(
    facts: dict[str, Any],
    mapping: dict[str, XBRLConcept],
    concept_name: str,
    form_type: str = "10-K",
) -> list[dict[str, Any]] | None:
    """Resolve a canonical concept name to XBRL data.

    Tries each tag in the mapping's priority list until data is found.
    Falls back to 10-Q annual entries (fp="FY") when 10-K has no data
    for a concept — some companies (e.g., Apple for Goodwill) stop
    tagging certain concepts in 10-K filings but continue in 10-Q.
    Logs which tag matched for traceability.

    Args:
        facts: Full companyfacts API response.
        mapping: Loaded XBRL concept mapping table.
        concept_name: Canonical name (e.g., "revenue", "net_income").
        form_type: Filing type to filter by (default "10-K").

    Returns:
        List of fact entries if found, None if no tags matched.
    """
    concept_config = mapping.get(concept_name)
    if concept_config is None:
        logger.warning("No mapping found for concept: %s", concept_name)
        return None

    unit = concept_config["unit"]
    best_results: list[dict[str, Any]] | None = None
    best_tag: str = ""
    best_max_end: str = ""

    for tag in concept_config["xbrl_tags"]:
        results = extract_concept_value(facts, tag, form_type, unit)
        if results:
            max_end = max(str(e.get("end", "")) for e in results)
            if best_results is None or max_end > best_max_end:
                best_results = results
                best_tag = tag
                best_max_end = max_end

    # Check if 10-K data is stale (latest entry > 3 years old).
    # Some companies (e.g., Apple for Goodwill) stop tagging certain
    # concepts in 10-K but continue in 10-Q.
    tenk_is_stale = False
    if best_results is not None and form_type == "10-K":
        from datetime import UTC, datetime as _dt

        try:
            latest_dt = _dt.strptime(best_max_end, "%Y-%m-%d").replace(tzinfo=UTC)
            age_days = (_dt.now(tz=UTC) - latest_dt).days
            tenk_is_stale = age_days > 3 * 365
        except ValueError:
            pass

    if best_results is not None and not tenk_is_stale:
        logger.debug(
            "Resolved '%s' via XBRL tag '%s' (%d entries, latest %s)",
            concept_name,
            best_tag,
            len(best_results),
            best_max_end,
        )
        return best_results

    # Fallback: try 10-Q entries when 10-K data is missing or stale.
    # Extract annual-equivalent entries (one per fiscal year from quarterly).
    if form_type == "10-K":
        for tag in concept_config["xbrl_tags"]:
            q_results = extract_concept_value(facts, tag, "10-Q", unit)
            if q_results:
                annual_results = _extract_annual_from_quarterly(q_results)
                if annual_results:
                    max_end = max(str(e.get("end", "")) for e in annual_results)
                    if best_results is None or max_end > best_max_end:
                        best_results = annual_results
                        best_tag = tag
                        best_max_end = max_end

        if best_results is not None:
            logger.info(
                "Resolved '%s' via 10-Q fallback tag '%s' "
                "(%d entries, latest %s)",
                concept_name,
                best_tag,
                len(best_results),
                best_max_end,
            )
            return best_results

    logger.debug(
        "No data found for concept '%s' (tried %d tags)",
        concept_name,
        len(concept_config["xbrl_tags"]),
    )
    return None


def _extract_annual_from_quarterly(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract annual-equivalent entries from 10-Q data.

    For each fiscal year, selects the latest quarter entry (by end date)
    to represent the annual balance sheet snapshot. This handles companies
    that report certain concepts only in 10-Q filings.

    Args:
        entries: 10-Q fact entries sorted by end date.

    Returns:
        List of annual-equivalent entries, one per fiscal year.
    """
    # Group by fiscal year, keep latest entry per year
    by_fy: dict[int, dict[str, Any]] = {}
    for entry in entries:
        fy = entry.get("fy")
        if fy is None or not isinstance(fy, int):
            continue
        existing = by_fy.get(fy)
        if existing is None or str(entry.get("end", "")) > str(existing.get("end", "")):
            by_fy[fy] = entry

    return sorted(by_fy.values(), key=lambda e: str(e.get("end", "")))


def get_latest_value(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Get the most recent entry from a list of fact entries.

    Args:
        entries: List of fact entries sorted by end date.

    Returns:
        Most recent entry (last by end date), or None if empty.
    """
    if not entries:
        return None
    return entries[-1]


def get_period_values(
    entries: list[dict[str, Any]],
    periods: int = 3,
) -> list[dict[str, Any]]:
    """Get the N most recent annual period entries.

    Args:
        entries: List of fact entries sorted by end date.
        periods: Number of most recent periods to return (default 3).

    Returns:
        Up to N most recent entries (by end date).
    """
    if not entries:
        return []
    return entries[-periods:]
