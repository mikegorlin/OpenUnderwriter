"""Post-pipeline health check heuristics (Phase 92 -- REND-03/REND-04).

Scans rendered HTML output for data quality issues:
- Raw LLM text leaking through (phrases, markdown formatting)
- Zero placeholder values in non-allowlisted contexts
- Empty/N/A values in percentage or numeric table cells

All issues are warnings -- they never block the pipeline.

Exports:
    HealthIssue, HealthCheckReport, load_health_config,
    detect_llm_markers, detect_zero_placeholders,
    detect_empty_percentages, run_health_checks
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[assignment, misc]
    Tag = None  # type: ignore[assignment, misc]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class HealthIssue:
    """A single health check finding."""

    category: str  # "llm_text", "zero_placeholder", "empty_value"
    severity: str  # "HIGH", "MEDIUM", "LOW"
    location: str  # Approximate location (section ID or context)
    message: str  # Human-readable description
    snippet: str  # The offending text (truncated to ~100 chars)


@dataclass
class HealthCheckReport:
    """Aggregated result of all health check heuristics."""

    issues: list[HealthIssue] = field(default_factory=list)
    llm_text_count: int = 0
    zero_placeholder_count: int = 0
    empty_value_count: int = 0


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "config"
    / "health_check.yaml"
)


@functools.cache
def load_health_config() -> dict[str, Any]:
    """Load health check config from config/health_check.yaml.

    Returns:
        Dict with keys: llm_markers, zero_valid_fields, empty_value_patterns.
        Cached after first call.
    """
    if not _CONFIG_PATH.exists():
        return {
            "llm_markers": [],
            "zero_valid_fields": [],
            "empty_value_patterns": [],
        }
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "llm_markers": data.get("llm_markers", []),
        "zero_valid_fields": data.get("zero_valid_fields", []),
        "empty_value_patterns": data.get("empty_value_patterns", []),
    }


# ---------------------------------------------------------------------------
# LLM marker detection
# ---------------------------------------------------------------------------


def _get_section_id(element: Any) -> str:
    """Walk up the DOM to find the nearest parent section ID."""
    if element is None or Tag is None:
        return "unknown"
    current = element
    while current is not None:
        if isinstance(current, Tag):
            if current.name == "section" and current.get("id"):
                return f"section#{current['id']}"
        current = getattr(current, "parent", None)
    return "unknown"


def detect_llm_markers(html: str, config: dict[str, Any]) -> list[HealthIssue]:
    """Scan rendered HTML for raw LLM text patterns.

    Uses BeautifulSoup to extract visible text from each section,
    then checks against the llm_markers list from config.
    Reports with section ID context for location.

    Args:
        html: The rendered HTML string.
        config: Health check config dict (from load_health_config).

    Returns:
        List of HealthIssue for each LLM marker found.
    """
    markers = config.get("llm_markers", [])
    if not markers:
        return []

    issues: list[HealthIssue] = []

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        # Walk all text nodes
        for text_node in soup.find_all(string=True):
            text = str(text_node).strip()
            if not text:
                continue
            for marker in markers:
                if marker in text:
                    location = _get_section_id(text_node)
                    snippet = text[:100] if len(text) > 100 else text
                    issues.append(
                        HealthIssue(
                            category="llm_text",
                            severity="MEDIUM",
                            location=location,
                            message=f"Raw LLM text detected: '{marker}'",
                            snippet=snippet,
                        )
                    )
    else:
        # Fallback: simple string matching without BeautifulSoup
        for marker in markers:
            if marker in html:
                # Find approximate context
                idx = html.find(marker)
                start = max(0, idx - 20)
                end = min(len(html), idx + len(marker) + 80)
                snippet = html[start:end].strip()
                issues.append(
                    HealthIssue(
                        category="llm_text",
                        severity="MEDIUM",
                        location="unknown",
                        message=f"Raw LLM text detected: '{marker}'",
                        snippet=snippet,
                    )
                )

    return issues


# ---------------------------------------------------------------------------
# Zero placeholder detection
# ---------------------------------------------------------------------------

# Pattern matching zero values in table cells: 0.0, $0, 0.00, $0.0, $0.00
_ZERO_PATTERN = re.compile(
    r"<td[^>]*>\s*\$?\s*0(?:\.0+)?\s*</td>",
    re.IGNORECASE,
)


def detect_zero_placeholders(
    html: str,
    state_dict: dict[str, Any],
    config: dict[str, Any],
) -> list[HealthIssue]:
    """Find 0.0 values in rendered output that aren't in zero_valid_fields.

    Context-aware: checks the surrounding text/field label to determine
    if the zero is in a field that legitimately can be zero.
    Only flags values rendered as "0.0", "$0", "0.00" etc. in table cells.

    Args:
        html: The rendered HTML string.
        state_dict: State dict (currently unused, reserved for future context).
        config: Health check config dict.

    Returns:
        List of HealthIssue for each suspicious zero found.
    """
    allowlist = config.get("zero_valid_fields", [])
    allowlist_lower = [f.lower() for f in allowlist]
    issues: list[HealthIssue] = []

    for match in _ZERO_PATTERN.finditer(html):
        # Get surrounding context to check field label
        start = max(0, match.start() - 200)
        context = html[start : match.end()]

        # Check if any allowlisted field name appears in the surrounding context
        context_lower = context.lower()
        is_allowlisted = any(field in context_lower for field in allowlist_lower)

        if not is_allowlisted:
            # Extract the nearest header/label for location
            th_match = re.search(r"<th[^>]*>([^<]+)</th>", context)
            label = th_match.group(1).strip() if th_match else "unknown field"
            snippet = match.group().strip()

            issues.append(
                HealthIssue(
                    category="zero_placeholder",
                    severity="LOW",
                    location=f"near '{label}'",
                    message=f"Possible zero placeholder value in table cell near '{label}'",
                    snippet=snippet,
                )
            )

    return issues


# ---------------------------------------------------------------------------
# Empty percentage / value detection
# ---------------------------------------------------------------------------

_HEADER_PERCENT_PATTERN = re.compile(
    r"%|percent|rate|ratio|margin|yield|roe|roa|growth",
    re.IGNORECASE,
)


def detect_empty_percentages(
    html: str,
    config: dict[str, Any],
) -> list[HealthIssue]:
    """Find percentage table cells that are empty, N/A, or 'Not Available'.

    Scans <td> elements that should contain numeric values for
    empty_value_patterns from config.

    Args:
        html: The rendered HTML string.
        config: Health check config dict.

    Returns:
        List of HealthIssue for each empty value found in numeric contexts.
    """
    patterns = config.get("empty_value_patterns", [])
    if not patterns:
        return []

    issues: list[HealthIssue] = []

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for table in tables:
            # Get header row to identify numeric columns
            headers: list[str] = []
            thead = table.find("thead")
            if thead and isinstance(thead, Tag):
                for th in thead.find_all("th"):
                    headers.append(th.get_text(strip=True))

            # Check if any header suggests numeric/percentage content
            has_numeric_headers = any(
                _HEADER_PERCENT_PATTERN.search(h) for h in headers
            )

            # Scan all td cells
            tbody = table.find("tbody")
            rows = tbody.find_all("tr") if tbody and isinstance(tbody, Tag) else table.find_all("tr")
            for row in rows:
                if not isinstance(row, Tag):
                    continue
                cells = row.find_all("td")

                # Check if any cell in the row has a percentage-like label
                # (e.g., first cell is "ROE" which is a percentage metric)
                row_texts = [
                    c.get_text(strip=True) for c in cells if isinstance(c, Tag)
                ]
                row_has_numeric_label = any(
                    _HEADER_PERCENT_PATTERN.search(t) for t in row_texts
                )

                for cell_idx, cell in enumerate(cells):
                    if not isinstance(cell, Tag):
                        continue
                    cell_text = cell.get_text(strip=True)

                    # Check if cell content matches an empty value pattern
                    for pattern in patterns:
                        if pattern in cell_text:
                            # Determine if this cell is in a numeric context
                            in_numeric_col = (
                                has_numeric_headers
                                or row_has_numeric_label
                                or (
                                    cell_idx < len(headers)
                                    and _HEADER_PERCENT_PATTERN.search(
                                        headers[cell_idx]
                                    )
                                )
                            )

                            if in_numeric_col:
                                # Get header context for location
                                header_ctx = (
                                    headers[cell_idx]
                                    if cell_idx < len(headers)
                                    else "unknown column"
                                )
                                issues.append(
                                    HealthIssue(
                                        category="empty_value",
                                        severity="LOW",
                                        location=f"column '{header_ctx}'",
                                        message=f"Empty/missing value '{pattern}' in numeric context",
                                        snippet=cell_text[:100],
                                    )
                                )
                            break  # Only report once per cell
    else:
        # Fallback: regex-based detection
        td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
        for td_match in td_pattern.finditer(html):
            cell_text = td_match.group(1).strip()
            for pattern in patterns:
                if pattern in cell_text:
                    start = max(0, td_match.start() - 200)
                    context = html[start : td_match.start()]
                    # Check if there's a percentage-like header nearby
                    if _HEADER_PERCENT_PATTERN.search(context):
                        issues.append(
                            HealthIssue(
                                category="empty_value",
                                severity="LOW",
                                location="unknown",
                                message=f"Empty/missing value '{pattern}' in numeric context",
                                snippet=cell_text[:100],
                            )
                        )
                    break

    return issues


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def run_health_checks(
    html: str,
    state_dict: dict[str, Any],
) -> HealthCheckReport:
    """Run all health check heuristics and aggregate results.

    Args:
        html: The rendered HTML string.
        state_dict: State dict for context-aware checks.

    Returns:
        HealthCheckReport with all issues aggregated.
    """
    config = load_health_config()

    llm_issues = detect_llm_markers(html, config)
    zero_issues = detect_zero_placeholders(html, state_dict, config)
    empty_issues = detect_empty_percentages(html, config)

    all_issues = llm_issues + zero_issues + empty_issues

    return HealthCheckReport(
        issues=all_issues,
        llm_text_count=len(llm_issues),
        zero_placeholder_count=len(zero_issues),
        empty_value_count=len(empty_issues),
    )


__all__ = [
    "HealthCheckReport",
    "HealthIssue",
    "detect_empty_percentages",
    "detect_llm_markers",
    "detect_zero_placeholders",
    "load_health_config",
    "run_health_checks",
]
