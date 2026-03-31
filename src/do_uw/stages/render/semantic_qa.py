"""Semantic QA: validates rendered HTML output against source state data.

Parses HTML with BeautifulSoup and compares key values (revenue, board size,
overall score) back to state.json to catch template bugs, formatting errors,
or data path breakage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Financial value parsing
# ---------------------------------------------------------------------------

_SUFFIX_MULTIPLIERS: dict[str, float] = {
    "T": 1e12,
    "B": 1e9,
    "M": 1e6,
    "K": 1e3,
}


def _parse_financial_value(text: str) -> float | None:
    """Parse formatted financial string back to a number.

    Handles: "$1.2B", "$450M", "$12.5K", "$1,234,567", "(1.2B)" for negatives,
    plain numbers, and percentage values like "83.80".
    Returns None if unparsable.
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()
    if not cleaned or cleaned in {"N/A", "—", "-", "n/a", "Not Available"}:
        return None

    # Detect negative values in parens: ($1.2B) -> negative
    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1].strip()

    # Remove currency symbols and whitespace
    cleaned = cleaned.replace("$", "").replace(",", "").strip()

    if not cleaned:
        return None

    # Check for suffix multiplier (B, M, K, T)
    suffix = cleaned[-1].upper()
    if suffix in _SUFFIX_MULTIPLIERS:
        num_part = cleaned[:-1].strip()
        try:
            value = float(num_part) * _SUFFIX_MULTIPLIERS[suffix]
            return -value if negative else value
        except ValueError:
            return None

    # Plain number
    try:
        value = float(cleaned)
        return -value if negative else value
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# State data extraction
# ---------------------------------------------------------------------------


def _extract_state_revenue(state_data: dict) -> list[float]:
    """Extract all FY revenue values from state dict.

    Path: extracted.financials.statements.income_statement.line_items ->
    find label matching 'revenue' -> all FY values (most recent first).

    Returns list of values so validation can check if HTML matches any period.
    """
    results: list[float] = []
    try:
        inc = (
            state_data.get("extracted", {})
            .get("financials", {})
            .get("statements", {})
            .get("income_statement", {})
        )
        line_items = inc.get("line_items", [])
        for item in line_items:
            label = (item.get("label") or "").lower()
            if "revenue" in label and "cost" not in label:
                values = item.get("values", {})
                fy_keys = sorted(
                    [k for k in values if k.startswith("FY")], reverse=True
                )
                for k in fy_keys:
                    val = values[k]
                    if isinstance(val, dict):
                        v = val.get("value")
                    else:
                        v = val
                    if v is not None:
                        results.append(float(v))
                break
    except (AttributeError, TypeError, KeyError):
        pass
    return results


def _extract_state_board_size(state_data: dict) -> int | None:
    """Extract board size from state dict.

    Path: extracted.governance.board.size (SourcedValue with .value).
    """
    try:
        board = (
            state_data.get("extracted", {})
            .get("governance", {})
            .get("board", {})
        )
        size = board.get("size")
        if isinstance(size, dict):
            val = size.get("value")
            return int(val) if val is not None else None
        if isinstance(size, (int, float)) and size is not None:
            return int(size)
    except (AttributeError, TypeError, KeyError):
        pass
    return None


def _extract_state_overall_score(state_data: dict) -> float | None:
    """Extract composite/overall score from state dict.

    Path: scoring.composite_score (preferred) or scoring.quality_score.
    """
    try:
        scoring = state_data.get("scoring", {})
        score = scoring.get("composite_score")
        if score is not None:
            return float(score)
        score = scoring.get("quality_score")
        if score is not None:
            return float(score)
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    return None


def _extract_state_tier(state_data: dict) -> str | None:
    """Extract tier label from state dict.

    Path: scoring.tier.tier (nested dict).
    """
    try:
        tier = state_data.get("scoring", {}).get("tier", {})
        if isinstance(tier, dict):
            return tier.get("tier")
        if isinstance(tier, str):
            return tier
    except (AttributeError, TypeError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# HTML value extraction
# ---------------------------------------------------------------------------


def _extract_html_value(
    soup: BeautifulSoup,
    label_pattern: str,
    section_hint: str | None = None,
) -> str | None:
    """Find a value in HTML by locating a label and extracting the adjacent value.

    Searches for label_pattern (regex) in td/dt/th elements, then returns
    the text of the adjacent td/dd element. If section_hint is provided,
    limits search to elements within that section class/id.
    """
    pattern = re.compile(label_pattern, re.IGNORECASE)

    # Optionally scope to section
    context = soup
    if section_hint:
        section = soup.find(class_=section_hint) or soup.find(id=section_hint)
        if section:
            context = section

    # Search td -> next td (KV table pattern)
    for tag_name in ["td", "th", "dt"]:
        for el in context.find_all(tag_name):
            text = el.get_text(strip=True)
            if pattern.search(text) and len(text) < 80:
                sibling_tags = {"td": "td", "th": "td", "dt": "dd"}
                sibling = el.find_next_sibling(sibling_tags.get(tag_name, "td"))
                if sibling:
                    val = sibling.get_text(strip=True)
                    if val and val not in {"N/A", "—"}:
                        return val

    return None


def _extract_html_score(soup: BeautifulSoup) -> float | None:
    """Extract the composite/quality score from HTML.

    Strategy 1: Narrative text ("composite quality score of 83.8")
    Strategy 2: Signal debug table row with "quality_score" label (5-6 cells)
    Avoids small KV rows labeled "Quality Score" which show different metrics.
    """
    # Strategy 1: Narrative text (most reliable)
    for el in soup.find_all(["strong", "p", "li"]):
        text = el.get_text(strip=True)
        m = re.search(
            r"composite\s+(?:quality\s+)?score\s+of\s+(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if m:
            return float(m.group(1))

    # Strategy 2: Signal debug table row "quality_score" or "composite_score"
    for td in soup.find_all("td"):
        text = td.get_text(strip=True)
        if text in ("quality_score", "composite_score"):
            sibling = td.find_next_sibling("td")
            if sibling:
                parsed = _parse_financial_value(sibling.get_text(strip=True))
                if parsed is not None and 0 < parsed <= 100:
                    return parsed

    return None


def _extract_html_tier(soup: BeautifulSoup) -> str | None:
    """Extract tier label from HTML badge or narrative text."""
    valid_tiers = {"WIN", "WANT", "WATCH", "WALK", "WITHDRAW"}

    # Strategy 1: Badge element
    for el in soup.find_all(class_=re.compile(r"badge-tier")):
        text = el.get_text(strip=True).upper()
        if text in valid_tiers:
            return text

    # Strategy 2: Narrative text mentioning tier
    tier_pattern = re.compile(
        r"\b(WIN|WANT|WATCH|WALK|WITHDRAW)\s+(?:TIER|tier)\b"
    )
    for el in soup.find_all(["p", "li", "strong", "td"]):
        text = el.get_text(strip=True)
        m = tier_pattern.search(text)
        if m:
            return m.group(1).upper()

    return None


def _extract_html_board_size(soup: BeautifulSoup) -> int | None:
    """Extract board size from HTML.

    Looks for 'Board Size' label in th/td elements within small KV rows
    (2-3 cells) to avoid signal debug table matches (6+ cells).
    """
    pattern = re.compile(r"^board\s*size$", re.IGNORECASE)
    # Check th/td KV rows first
    for el in soup.find_all(["th", "td"]):
        text = el.get_text(strip=True)
        if pattern.match(text):
            row = el.parent
            if row and row.name == "tr":
                all_cells = row.find_all(["td", "th"])
                # Prefer small KV rows (display tables, not debug tables)
                if len(all_cells) <= 4:
                    sibling = el.find_next_sibling("td")
                    if sibling:
                        val_text = sibling.get_text(strip=True)
                        try:
                            return int(float(val_text))
                        except (ValueError, TypeError):
                            pass
    # Also check span-based key stats layout (Board Size in span + adjacent value)
    for el in soup.find_all("span"):
        text = el.get_text(strip=True)
        if pattern.match(text):
            # Look for a sibling or nearby element with the numeric value
            parent = el.parent
            if parent:
                full_text = parent.get_text(strip=True)
                m = re.search(r"(\d+)", full_text.replace(text, "", 1))
                if m:
                    return int(m.group(1))
    return None


def _extract_html_revenue(soup: BeautifulSoup) -> float | None:
    """Extract revenue from HTML financial tables.

    Looks for 'Total revenue / net sales' first (specific), then 'Revenue'
    in financial statement tables.
    """
    # Try specific label first
    for label_pat in [
        r"^total\s+revenue\s*/\s*net\s+sales$",
        r"^revenue$",
    ]:
        val = _extract_html_value(soup, label_pat)
        if val:
            parsed = _parse_financial_value(val)
            if parsed and parsed > 1000:  # Revenue should be > $1K
                return parsed
    return None


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------


def validate_revenue(
    state_data: dict, soup: BeautifulSoup
) -> tuple[bool, str]:
    """Compare state revenue vs HTML revenue within 5% tolerance.

    HTML may show any FY period's revenue (most recent or prior year).
    Checks if the HTML value matches ANY FY revenue in state data.
    Uses 5% tolerance to account for display rounding ($7.4B vs $7,372,644,000).
    """
    state_vals = _extract_state_revenue(state_data)
    if not state_vals:
        return True, "SKIP: No revenue in state data"

    html_val = _extract_html_revenue(soup)
    if html_val is None:
        return False, f"FAIL: Revenue in state ({state_vals[0]:,.0f}) but not found in HTML"

    # Check if HTML value matches any FY revenue within tolerance
    for state_val in state_vals:
        if state_val == 0:
            if html_val == 0:
                return True, "PASS: Revenue matches (both zero)"
            continue

        pct_diff = abs(html_val - state_val) / abs(state_val)
        if pct_diff <= 0.05:
            return True, f"PASS: Revenue matches (state={state_val:,.0f}, html={html_val:,.0f}, diff={pct_diff:.2%})"

    return False, f"FAIL: Revenue mismatch (state values={[f'{v:,.0f}' for v in state_vals]}, html={html_val:,.0f})"


def validate_board_size(
    state_data: dict, soup: BeautifulSoup
) -> tuple[bool, str]:
    """Compare state board size vs HTML board size. Exact match."""
    state_val = _extract_state_board_size(state_data)
    if state_val is None:
        return True, "SKIP: No board size in state data"

    html_val = _extract_html_board_size(soup)
    if html_val is None:
        return False, f"FAIL: Board size in state ({state_val}) but not found in HTML"

    if html_val == state_val:
        return True, f"PASS: Board size matches ({state_val})"
    return False, f"FAIL: Board size mismatch (state={state_val}, html={html_val})"


def validate_overall_score(
    state_data: dict, soup: BeautifulSoup
) -> tuple[bool, str]:
    """Compare state overall score vs HTML score. 1.0 tolerance (HTML may round)."""
    state_val = _extract_state_overall_score(state_data)
    if state_val is None:
        return True, "SKIP: No overall score in state data"

    html_val = _extract_html_score(soup)
    if html_val is None:
        return True, f"SKIP: Score in state ({state_val}) but not rendered in HTML (pre-v3.0 template)"

    if abs(html_val - state_val) <= 1.0:
        return True, f"PASS: Score matches (state={state_val}, html={html_val})"
    return False, f"FAIL: Score mismatch (state={state_val}, html={html_val})"


def validate_tier(
    state_data: dict, soup: BeautifulSoup
) -> tuple[bool, str]:
    """Compare state tier vs HTML tier badge. Exact match."""
    state_val = _extract_state_tier(state_data)
    if state_val is None:
        return True, "SKIP: No tier in state data"

    html_val = _extract_html_tier(soup)
    if html_val is None:
        return True, f"SKIP: Tier in state ({state_val}) but not rendered in HTML (pre-v3.0 template)"

    if html_val.upper() == state_val.upper():
        return True, f"PASS: Tier matches ({state_val})"
    return False, f"FAIL: Tier mismatch (state={state_val}, html={html_val})"


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------


def validate_output(
    state_path: Path, html_path: Path
) -> list[tuple[str, bool, str]]:
    """Run all semantic QA validations on a state.json + HTML pair.

    Returns list of (check_name, passed, message).
    Skips checks where source data is unavailable.
    """
    with open(state_path) as f:
        state_data = json.load(f)

    with open(html_path) as f:
        soup = BeautifulSoup(f, "lxml")

    results: list[tuple[str, bool, str]] = []

    checks = [
        ("revenue", validate_revenue),
        ("board_size", validate_board_size),
        ("overall_score", validate_overall_score),
        ("tier", validate_tier),
    ]

    for name, fn in checks:
        passed, msg = fn(state_data, soup)
        results.append((name, passed, msg))

    return results
