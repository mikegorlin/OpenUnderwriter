"""Supply chain dependency extraction from 10-K text.

Extracts supplier/vendor dependencies from Item 1 (Business) and
Item 1A (Risk Factors) using regex pattern matching. No LLM calls.

Public API:
    extract_supply_chain(item1_text, item1a_text, company_name) -> list[SupplyChainDependency]
"""

from __future__ import annotations

import logging
import re

from do_uw.models.company_intelligence import SupplyChainDependency

logger = logging.getLogger(__name__)

# Patterns that indicate supply chain dependency mentions.
_DEPENDENCY_PATTERNS: list[tuple[str, str]] = [
    (r"sole[\s-]+source", "sole-source"),
    (r"single\s+supplier", "sole-source"),
    (r"single\s+source", "sole-source"),
    (r"principal\s+supplier", "limited-source"),
    (r"key\s+supplier", "limited-source"),
    (r"(?:depend|rely)\s+on\s+[\w\s]*(?:supplier|vendor|manufacturer)", "limited-source"),
    (r"limited[\s-]+source", "limited-source"),
    (r"few\s+suppliers", "limited-source"),
    (r"limited\s+(?:number\s+of\s+)?(?:suppliers|sources|vendors)", "limited-source"),
]

# High switching cost indicators.
_HIGH_SWITCHING_PATTERNS: list[str] = [
    r"no\s+alternative",
    r"no\s+other\s+(?:source|supplier|vendor)",
    r"cannot\s+(?:easily\s+)?(?:replace|substitute)",
    r"limited\s+alternatives",
    r"few\s+alternatives",
    r"difficult\s+to\s+(?:replace|substitute|find)",
    r"long\s+lead\s+time",
    r"qualification\s+process",
]

# Low switching cost indicators.
_LOW_SWITCHING_PATTERNS: list[str] = [
    r"multiple\s+(?:sources|suppliers|vendors)",
    r"readily\s+available",
    r"commodity",
    r"alternative\s+(?:sources|suppliers)",
    r"diversified\s+(?:supply|sourcing)",
]

# Context window size around match.
_CONTEXT_CHARS = 200


def extract_supply_chain(
    item1_text: str,
    item1a_text: str,
    company_name: str = "",
) -> list[SupplyChainDependency]:
    """Extract supply chain dependencies from 10-K text.

    Scans Item 1 (Business) and Item 1A (Risk Factors) for
    supplier/vendor dependency mentions using regex patterns.

    Args:
        item1_text: Item 1 (Business) section text.
        item1a_text: Item 1A (Risk Factors) section text.
        company_name: Company name (for filtering self-references).

    Returns:
        List of SupplyChainDependency models. Empty if no text or
        no dependencies found.
    """
    if not item1_text and not item1a_text:
        return []

    dependencies: list[SupplyChainDependency] = []
    seen_contexts: set[tuple[int, int]] = set()

    # Scan both sections.
    for text, source in [
        (item1_text, "10-K Item 1"),
        (item1a_text, "10-K Item 1A"),
    ]:
        if not text:
            continue
        deps = _scan_text(text, source, company_name, seen_contexts)
        dependencies.extend(deps)

    if dependencies:
        logger.info(
            "Extracted %d supply chain dependencies from 10-K",
            len(dependencies),
        )

    return dependencies


def _scan_text(
    text: str,
    source: str,
    company_name: str,
    seen_contexts: set[tuple[int, int]],
) -> list[SupplyChainDependency]:
    """Scan text for dependency patterns and extract structured data."""
    results: list[SupplyChainDependency] = []

    for pattern, dep_type in _DEPENDENCY_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Extract context window.
            start = max(0, match.start() - _CONTEXT_CHARS)
            end = min(len(text), match.end() + _CONTEXT_CHARS)
            context = text[start:end].strip()

            # Deduplicate by match span overlap.
            # Two matches are duplicates if their spans overlap significantly.
            match_span = (match.start(), match.end())
            is_dup = False
            for seen_start, seen_end in seen_contexts:
                overlap_start = max(match_span[0], seen_start)
                overlap_end = min(match_span[1], seen_end)
                if overlap_end > overlap_start:
                    is_dup = True
                    break
            if is_dup:
                continue
            seen_contexts.add(match_span)

            # Determine switching cost from context.
            switching_cost = _assess_switching_cost(context)

            # Determine concentration level.
            concentration = "HIGH" if dep_type == "sole-source" else "MEDIUM"

            # Build D&O exposure narrative.
            do_exposure = _build_do_exposure(dep_type, switching_cost)

            # Try to extract provider name from context.
            provider = _extract_provider_name(context, company_name)

            results.append(
                SupplyChainDependency(
                    provider=provider,
                    dependency_type=dep_type,
                    concentration=concentration,
                    switching_cost=switching_cost,
                    do_exposure=do_exposure,
                    source=source,
                )
            )

    return results


def _assess_switching_cost(context: str) -> str:
    """Assess switching cost from surrounding text."""
    context_lower = context.lower()

    for pattern in _HIGH_SWITCHING_PATTERNS:
        if re.search(pattern, context_lower):
            return "HIGH"

    for pattern in _LOW_SWITCHING_PATTERNS:
        if re.search(pattern, context_lower):
            return "LOW"

    return "MEDIUM"


def _build_do_exposure(dep_type: str, switching_cost: str) -> str:
    """Build D&O exposure narrative based on dependency characteristics."""
    if dep_type == "sole-source":
        return (
            "Supply disruption creates revenue miss SCA if management "
            "failed to disclose sole-source concentration risk"
        )
    if switching_cost == "HIGH":
        return (
            "High switching costs amplify supply chain risk — "
            "extended disruption creates Section 10b-5 exposure "
            "for failure to disclose dependency"
        )
    return (
        "Supply chain dependency may create D&O exposure if "
        "disruption materially impacts disclosed guidance"
    )


def _extract_provider_name(context: str, company_name: str) -> str:
    """Try to extract a provider/supplier name from context.

    Looks for capitalized proper nouns near dependency keywords.
    Returns empty string if no clear provider name found.
    """
    # Look for capitalized words that could be company names.
    # Pattern: consecutive capitalized words (2+ chars each).
    candidates = re.findall(
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b",
        context,
    )

    company_lower = company_name.lower() if company_name else ""
    for candidate in candidates:
        # Skip the company's own name.
        if company_lower and candidate.lower() in company_lower:
            continue
        # Skip common non-name words.
        if candidate.lower() in {
            "the", "our", "we", "if", "in", "for", "this", "these",
            "item", "risk", "factors", "business", "company",
            "certain", "some", "any", "each", "other", "such",
        }:
            continue
        # Reasonable candidate.
        if len(candidate) >= 3:
            return candidate

    return ""


__all__ = ["extract_supply_chain"]
