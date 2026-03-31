"""Filing section parsing utilities for EXTRACT stage.

Extracts named sections (Item 1, Item 7, Item 9A, etc.) from full
10-K/20-F filing text. This logic lives in EXTRACT (not ACQUIRE)
because section parsing is interpretation of raw document content.

Moved from acquire/clients/filing_text.py in Phase 4 refactor.
"""

from __future__ import annotations

import re

# Max characters to store per section (prevents memory bloat on huge filings).
MAX_SECTION_CHARS = 50_000

# Section definitions: (key_name, start_patterns, end_patterns).
# Each start/end is a list of regex patterns tried in order.
SECTION_DEFS: list[tuple[str, list[str], list[str]]] = [
    (
        "item1",
        [
            r"(?i)\bitem\s+1[\.\s:]+business\b",
            r"(?i)\bitem\s+1\b(?!\s*[0-9a-z])",
        ],
        [
            r"(?i)\bitem\s+1a[\.\s:]+risk\s+factors\b",
            r"(?i)\bitem\s+1a\b",
            r"(?i)\bitem\s+2\b",
        ],
    ),
    (
        "item1a",
        [
            r"(?i)\bitem\s+1a[\.\s:]+risk\s+factors\b",
            r"(?i)\bitem\s+1a\b",
        ],
        [
            r"(?i)\bitem\s+1b\b",
            r"(?i)\bitem\s+2\b",
        ],
    ),
    (
        "item3",
        [
            r"(?i)\bitem\s+3[\.\s:]+legal\s+proceedings\b",
            r"(?i)\bitem\s+3\b(?!\s*[0-9a-z])",
        ],
        [
            r"(?i)\bitem\s+3a\b",
            r"(?i)\bitem\s+4\b",
        ],
    ),
    (
        "item7",
        [
            r"(?i)\bitem\s+7[\.\s:]+"
            r"management.s\s+discussion\s+and\s+analysis\b",
            r"(?i)\bitem\s+7\b(?!\s*[0-9a-z])",
        ],
        [
            r"(?i)\bitem\s+7a[\.\s:]+quantitative\b",
            r"(?i)\bitem\s+7a\b",
            r"(?i)\bitem\s+8\b",
        ],
    ),
    (
        "item8",
        [
            r"(?i)\bitem\s+8[\.\s:]+financial\s+statements\b",
            r"(?i)\bitem\s+8\b(?!\s*[0-9a-z])",
        ],
        [
            r"(?i)\bitem\s+9[\.\s:]+changes\s+in\b",
            r"(?i)\bitem\s+9\b(?!\s*[0-9a-z])",
            r"(?i)\bitem\s+9a\b",
        ],
    ),
    (
        "item9a",
        [
            r"(?i)\bitem\s+9a[\.\s:]+controls\s+and\s+procedures\b",
            r"(?i)\bitem\s+9a\b",
        ],
        [
            r"(?i)\bitem\s+9b\b",
            r"(?i)\bitem\s+10\b",
        ],
    ),
]


def extract_section(
    text: str,
    start_patterns: list[str],
    end_patterns: list[str],
) -> str:
    """Extract a section from filing text between start and end markers.

    Tries each start pattern until one matches, then each end pattern.
    Returns the text between the best start and end matches.

    Args:
        text: Full filing plain text.
        start_patterns: Regex patterns for section start (tried in order).
        end_patterns: Regex patterns for section end (tried in order).

    Returns:
        Extracted section text (truncated to MAX_SECTION_CHARS),
        or empty string if section not found.
    """
    # Find the LAST occurrence of start pattern (10-K table of contents
    # often lists items early, actual content is later).
    start_pos = -1
    for pattern in start_patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            # Use the last match (skip table of contents references).
            start_pos = matches[-1].end()
            break

    if start_pos < 0:
        return ""

    # Find the FIRST occurrence of end pattern after start.
    end_pos = len(text)
    for pattern in end_patterns:
        match = re.search(pattern, text[start_pos:])
        if match:
            candidate = start_pos + match.start()
            if candidate < end_pos:
                end_pos = candidate
            break

    section = text[start_pos:end_pos].strip()

    # Truncate to prevent memory bloat.
    if len(section) > MAX_SECTION_CHARS:
        section = section[:MAX_SECTION_CHARS]

    # Skip if too short (likely a false positive from table of contents).
    if len(section) < 200:
        return ""

    return section


def extract_10k_sections(full_text: str) -> dict[str, str]:
    """Extract all standard 10-K sections from full filing text.

    Runs extract_section() for each entry in SECTION_DEFS and
    returns a dict with both prefixed and short alias keys.

    Args:
        full_text: Full 10-K/20-F plain text.

    Returns:
        Dict with keys like '10-K_item1', 'item1', '10-K_item7', etc.
        Empty sections are omitted.
    """
    sections: dict[str, str] = {}

    for section_name, start_markers, end_markers in SECTION_DEFS:
        extracted = extract_section(full_text, start_markers, end_markers)
        if extracted:
            sections[f"10-K_{section_name}"] = extracted
            # Add short alias for convenience.
            sections[section_name] = extracted

    return sections
