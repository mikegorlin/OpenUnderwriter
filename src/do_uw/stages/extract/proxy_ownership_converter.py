"""Proxy ownership converter: DEF14AExtraction -> ownership records.

Maps DEF 14A ownership table fields (top holders, insider ownership %)
into structured SourcedValue records for scoring and rendering.

The top-5 holders list uses a "Name: Percentage" string format from the
LLM extraction. This module parses that into structured dicts.

Public functions:
- convert_top_holders           -> list of holder SourcedValue dicts
- convert_insider_ownership     -> SourcedValue[float] or None
- convert_proxy_ownership_summary -> combined ownership dict
"""

from __future__ import annotations

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
)

_LLM_SOURCE = "DEF 14A (LLM)"


# ------------------------------------------------------------------
# Top holders parsing
# ------------------------------------------------------------------


def convert_top_holders(
    extraction: DEF14AExtraction,
) -> list[SourcedValue[dict[str, str]]]:
    """Parse top-5 holders from proxy ownership table.

    Each entry in ``extraction.top_5_holders`` is expected in the format
    ``"Vanguard Group: 8.2%"``. The colon separates the holder name from
    the ownership percentage string.

    Edge cases:
    - No colon separator: full string used as name, percentage is "N/A"
    - Empty list: returns empty list

    Args:
        extraction: DEF 14A LLM extraction result.

    Returns:
        List of SourcedValue dicts with "name" and "percentage" keys.
    """
    holders: list[SourcedValue[dict[str, str]]] = []
    for entry in extraction.top_5_holders:
        name, percentage = _parse_holder_entry(entry)
        holder_dict: dict[str, str] = {
            "name": name,
            "percentage": percentage,
        }
        sv = SourcedValue[dict[str, str]](
            value=holder_dict,
            source=_LLM_SOURCE,
            confidence=Confidence.HIGH,
            as_of=now(),
        )
        holders.append(sv)
    return holders


def _parse_holder_entry(entry: str) -> tuple[str, str]:
    """Parse a holder entry string into (name, percentage).

    Expected format: "Vanguard Group: 8.2%"
    Fallback: if no colon, use full string as name with "N/A" percentage.
    """
    if ":" in entry:
        parts = entry.split(":", maxsplit=1)
        name = parts[0].strip()
        percentage = parts[1].strip()
        return name, percentage
    return entry.strip(), "N/A"


# ------------------------------------------------------------------
# Insider ownership
# ------------------------------------------------------------------


def convert_insider_ownership(
    extraction: DEF14AExtraction,
) -> SourcedValue[float] | None:
    """Convert officers/directors aggregate ownership percentage.

    Returns a SourcedValue wrapping the insider ownership percentage,
    or None if the field is not populated.

    Args:
        extraction: DEF 14A LLM extraction result.

    Returns:
        SourcedValue[float] with insider %, or None.
    """
    if extraction.officers_directors_ownership_pct is None:
        return None
    return sourced_float(
        extraction.officers_directors_ownership_pct,
        _LLM_SOURCE,
        Confidence.HIGH,
    )


# ------------------------------------------------------------------
# Combined summary
# ------------------------------------------------------------------


def convert_proxy_ownership_summary(
    extraction: DEF14AExtraction,
) -> dict[
    str,
    SourcedValue[float] | list[SourcedValue[dict[str, str]]] | None,
]:
    """Convenience function combining insider ownership and top holders.

    Returns a dict with:
    - "insider_pct": result of convert_insider_ownership
    - "top_holders": result of convert_top_holders

    Args:
        extraction: DEF 14A LLM extraction result.

    Returns:
        Dict with insider_pct and top_holders.
    """
    return {
        "insider_pct": convert_insider_ownership(extraction),
        "top_holders": convert_top_holders(extraction),
    }
