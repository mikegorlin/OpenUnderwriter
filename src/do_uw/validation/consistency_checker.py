"""Cross-section consistency checker for rendered HTML worksheets.

Compares canonical fact values (revenue, CEO, exchange, market cap)
against all rendered instances in the HTML output to detect contradictions
between sections.

Runs in report-only mode by default (logs warnings). Set report_only=False
to raise ConsistencyError on any inconsistency (GATE-05 promotable).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from do_uw.validation.qa_report import QACheck

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Inconsistency:
    """A single inconsistency: same fact has different values across sections."""

    fact_name: str
    expected: str
    found: dict[str, str] = field(default_factory=dict)
    sections: list[str] = field(default_factory=list)


@dataclass
class ConsistencyReport:
    """Result of a cross-section consistency check."""

    inconsistencies: list[Inconsistency] = field(default_factory=list)
    facts_checked: int = 0
    facts_consistent: int = 0
    report_only: bool = True
    qa_checks: list[QACheck] = field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        return len(self.inconsistencies) == 0


class ConsistencyError(Exception):
    """Raised when inconsistencies found and report_only=False."""

    def __init__(self, report: ConsistencyReport) -> None:
        self.report = report
        details = "; ".join(
            f"{i.fact_name}: expected={i.expected}, found={i.found}"
            for i in report.inconsistencies
        )
        super().__init__(f"Cross-section inconsistencies: {details}")


# ---------------------------------------------------------------------------
# Financial value parsing (reuse from semantic_qa)
# ---------------------------------------------------------------------------

_SUFFIX_MULTIPLIERS: dict[str, float] = {
    "T": 1e12,
    "B": 1e9,
    "M": 1e6,
    "K": 1e3,
}


def _parse_financial_value(text: str) -> float | None:
    """Parse formatted financial string to number.

    Handles: "$1.2B", "$450M", "$12.5K", "$1,234,567", "(1.2B)" for negatives.
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()
    if not cleaned or cleaned in {"N/A", "\u2014", "-", "n/a", "Not Available"}:
        return None

    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1].strip()

    cleaned = cleaned.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None

    suffix = cleaned[-1].upper()
    if suffix in _SUFFIX_MULTIPLIERS:
        num_part = cleaned[:-1].strip()
        try:
            value = float(num_part) * _SUFFIX_MULTIPLIERS[suffix]
            return -value if negative else value
        except ValueError:
            return None

    try:
        value = float(cleaned)
        return -value if negative else value
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Fact extraction patterns
# ---------------------------------------------------------------------------

# Label patterns for each fact type - used to find KV rows in HTML
_FACT_PATTERNS: dict[str, list[str]] = {
    "revenue": [
        r"(?:total\s+)?revenue(?:\s*/\s*net\s+sales)?",
        r"annual\s+revenue",
    ],
    "ceo_name": [
        r"(?:ceo|chief\s+executive\s+officer)",
    ],
    "exchange": [
        r"exchange",
        r"listing",
    ],
    "market_cap": [
        r"market\s+cap(?:italization)?",
    ],
    "net_income": [
        r"net\s+income",
    ],
    "employees": [
        r"employees?(?:\s+count)?",
    ],
    "stock_price": [
        r"(?:stock|share)\s+price",
        r"current\s+price",
    ],
}

# Facts that use financial value comparison (within tolerance)
_FINANCIAL_FACTS = {"revenue", "market_cap", "net_income", "stock_price"}

# Facts that use string comparison (case-insensitive)
_STRING_FACTS = {"ceo_name", "exchange", "employees"}


# ---------------------------------------------------------------------------
# ConsistencyChecker
# ---------------------------------------------------------------------------


class ConsistencyChecker:
    """Compare canonical metric values against rendered HTML instances.

    Args:
        canonical_values: Dict mapping fact names to their canonical string values.
            e.g. {"revenue": "$3.05B", "ceo_name": "Tim Cook", "exchange": "NASDAQ"}
        tolerance: Relative tolerance for financial comparisons (default 0.01 = 1%).
    """

    def __init__(
        self,
        canonical_values: dict[str, str],
        tolerance: float = 0.01,
    ) -> None:
        self._canonical = canonical_values
        self._tolerance = tolerance

    def check(
        self,
        html: str,
        report_only: bool = True,
    ) -> ConsistencyReport:
        """Run consistency check against rendered HTML.

        Args:
            html: Rendered HTML string.
            report_only: If True, return report only. If False, raise
                ConsistencyError on any inconsistency.

        Returns:
            ConsistencyReport with any inconsistencies found.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available - skipping consistency check")
            return ConsistencyReport(report_only=report_only)

        soup = BeautifulSoup(html, "html.parser")
        report = ConsistencyReport(report_only=report_only)

        for fact_name, canonical_str in self._canonical.items():
            if not canonical_str or canonical_str in {"N/A", "None", ""}:
                continue

            patterns = _FACT_PATTERNS.get(fact_name, [])
            if not patterns:
                continue

            report.facts_checked += 1

            # Find all rendered instances of this fact across sections
            found_values = self._extract_fact_instances(soup, fact_name, patterns)

            if not found_values:
                # Fact not found in HTML - not an inconsistency per se
                report.facts_consistent += 1
                continue

            # Compare each found value against canonical
            mismatches: dict[str, str] = {}
            for section_id, found_str in found_values.items():
                if not self._values_match(fact_name, canonical_str, found_str):
                    mismatches[section_id] = found_str

            if mismatches:
                report.inconsistencies.append(
                    Inconsistency(
                        fact_name=fact_name,
                        expected=canonical_str,
                        found=mismatches,
                        sections=list(mismatches.keys()),
                    )
                )
            else:
                report.facts_consistent += 1

        # Build QA checks for pipeline integration
        report.qa_checks = self._build_qa_checks(report)

        # Log warnings
        for inc in report.inconsistencies:
            logger.warning(
                "Consistency: %s mismatch - expected=%s, found=%s",
                inc.fact_name,
                inc.expected,
                inc.found,
            )

        if not report_only and report.inconsistencies:
            raise ConsistencyError(report)

        return report

    def _extract_fact_instances(
        self,
        soup: Any,
        fact_name: str,
        patterns: list[str],
    ) -> dict[str, str]:
        """Find all rendered values for a fact across HTML sections.

        Returns dict mapping section_id -> rendered_value_string.
        """
        found: dict[str, str] = {}

        for section in soup.find_all("section"):
            section_id = section.get("id", "unknown")

            for pattern_str in patterns:
                compiled = re.compile(pattern_str, re.IGNORECASE)

                # Search KV table rows (td label -> td value)
                for tag_name in ["td", "th"]:
                    for el in section.find_all(tag_name):
                        text = el.get_text(strip=True)
                        if compiled.search(text) and len(text) < 80:
                            sibling = el.find_next_sibling("td")
                            if sibling:
                                val = sibling.get_text(strip=True)
                                if val and val not in {"N/A", "\u2014", ""}:
                                    found[section_id] = val
                                    break

                # For ceo_name, also search paragraphs
                if fact_name == "ceo_name":
                    for el in section.find_all(["p", "span", "div"]):
                        text = el.get_text(strip=True)
                        if compiled.search(text):
                            # Extract the value part after the label
                            m = re.search(
                                r"(?:CEO|Chief Executive Officer)[:\s]+(.+?)(?:\.|,|$)",
                                text,
                                re.IGNORECASE,
                            )
                            if m:
                                val = m.group(1).strip()
                                if val and val not in {"N/A", "\u2014", ""}:
                                    found[section_id] = val

        return found

    def _values_match(
        self,
        fact_name: str,
        canonical: str,
        found: str,
    ) -> bool:
        """Compare canonical value against found value.

        Financial values: within tolerance (default 1%).
        String values: case-insensitive comparison.
        """
        if fact_name in _FINANCIAL_FACTS:
            canonical_num = _parse_financial_value(canonical)
            found_num = _parse_financial_value(found)

            if canonical_num is None or found_num is None:
                # Fall back to string comparison
                return canonical.strip().lower() == found.strip().lower()

            if canonical_num == 0:
                return found_num == 0

            pct_diff = abs(found_num - canonical_num) / abs(canonical_num)
            return pct_diff <= self._tolerance

        # String comparison (case-insensitive)
        return canonical.strip().lower() == found.strip().lower()

    @staticmethod
    def _build_qa_checks(report: ConsistencyReport) -> list[QACheck]:
        """Convert report to QACheck list for QA pipeline integration."""
        checks: list[QACheck] = []

        if report.is_consistent:
            checks.append(
                QACheck(
                    category="Consistency",
                    name="Cross-section consistency",
                    status="PASS",
                    detail=f"{report.facts_checked} facts checked, all consistent",
                    value=str(report.facts_checked),
                )
            )
        else:
            facts = ", ".join(i.fact_name for i in report.inconsistencies)
            checks.append(
                QACheck(
                    category="Consistency",
                    name="Cross-section consistency",
                    status="FAIL",
                    detail=f"{len(report.inconsistencies)} inconsistencies: {facts}",
                    value=str(len(report.inconsistencies)),
                )
            )

        return checks


# ---------------------------------------------------------------------------
# Canonical value extraction from state
# ---------------------------------------------------------------------------


def _extract_canonical_from_state(state: dict[str, Any]) -> dict[str, str]:
    """Extract canonical fact values from state dict.

    Builds a dict of fact_name -> formatted string value from the state,
    pulling from the same source-of-truth paths used during rendering.
    """
    canonical: dict[str, str] = {}

    # Revenue
    try:
        inc = (
            state.get("extracted", {})
            .get("financials", {})
            .get("statements", {})
            .get("income_statement", {})
        )
        for item in inc.get("line_items", []):
            label = (item.get("label") or "").lower()
            if "revenue" in label and "cost" not in label:
                values = item.get("values", {})
                fy_keys = sorted(
                    [k for k in values if k.startswith("FY")], reverse=True
                )
                if fy_keys:
                    val = values[fy_keys[0]]
                    if isinstance(val, dict):
                        v = val.get("value")
                    else:
                        v = val
                    if v is not None:
                        canonical["revenue"] = _format_canonical_financial(float(v))
                break
    except (AttributeError, TypeError, KeyError, ValueError):
        pass

    # CEO name
    try:
        gov = state.get("extracted", {}).get("governance", {})
        leadership = gov.get("leadership", {})
        execs = leadership.get("executives", [])
        for ex in execs:
            title = (ex.get("title") or "").lower() if isinstance(ex, dict) else ""
            if "ceo" in title or "chief executive" in title:
                name = ex.get("name", "")
                if name:
                    canonical["ceo_name"] = name
                break
    except (AttributeError, TypeError, KeyError):
        pass

    # Exchange
    try:
        company = state.get("company", {})
        exchange = company.get("exchange", {})
        if isinstance(exchange, dict):
            val = exchange.get("value", "")
        else:
            val = str(exchange) if exchange else ""
        if val:
            canonical["exchange"] = val
    except (AttributeError, TypeError, KeyError):
        pass

    return canonical


def _format_canonical_financial(value: float) -> str:
    """Format a raw number into display format for comparison."""
    abs_val = abs(value)
    negative = value < 0

    if abs_val >= 1e12:
        formatted = f"${abs_val / 1e12:.2f}T"
    elif abs_val >= 1e9:
        formatted = f"${abs_val / 1e9:.2f}B"
    elif abs_val >= 1e6:
        formatted = f"${abs_val / 1e6:.2f}M"
    elif abs_val >= 1e3:
        formatted = f"${abs_val / 1e3:.2f}K"
    else:
        formatted = f"${abs_val:,.2f}"

    return f"({formatted})" if negative else formatted


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def check_cross_section_consistency(
    state: dict[str, Any] | Any,
    html: str,
    report_only: bool = True,
) -> ConsistencyReport:
    """Check cross-section consistency of rendered HTML against state data.

    Builds canonical metrics from state, then runs consistency checker.

    Args:
        state: State dict (or object with __dict__) containing source-of-truth data.
        html: Rendered HTML string.
        report_only: If True (default), return report. If False, raise on inconsistency.

    Returns:
        ConsistencyReport with any inconsistencies found.
    """
    if isinstance(state, dict):
        state_dict = state
    else:
        # Handle AnalysisState objects - convert to dict
        try:
            state_dict = state.model_dump() if hasattr(state, "model_dump") else {}
        except Exception:
            state_dict = {}

    canonical = _extract_canonical_from_state(state_dict)
    checker = ConsistencyChecker(canonical_values=canonical)
    return checker.check(html, report_only=report_only)


__all__ = [
    "ConsistencyChecker",
    "ConsistencyError",
    "ConsistencyReport",
    "Inconsistency",
    "check_cross_section_consistency",
]
