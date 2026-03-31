"""Section completeness gate for rendered worksheet context.

Detects sections with excessive N/A values (>50% by default) and replaces
them with an Insufficient Data banner dict. Templates that guard with
``{% if section_var %}`` will skip rendering for suppressed sections.

The gate runs pre-render on the template context dict. It does NOT raise
exceptions -- it replaces broken sections with banners (GATE-02).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SectionCompleteness:
    """Completeness assessment for a single section."""

    section_name: str
    total_fields: int
    na_fields: int
    na_ratio: float
    suppressed: bool
    reason: str


# ---------------------------------------------------------------------------
# N/A detection
# ---------------------------------------------------------------------------


def _is_na(value: Any) -> bool:
    """Check if a leaf value is effectively N/A.

    - None -> True
    - "" -> True
    - "N/A" (case-insensitive) -> True
    - "Not Available" -> True
    - empty list/dict -> True
    - Everything else -> False
    """
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        if stripped.lower() in {"n/a", "not available"}:
            return True
        return False
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def _count_leaf_values(data: Any) -> tuple[int, int]:
    """Count total leaf values and N/A leaf values in a nested structure.

    Recurses into dicts and lists to find leaf values. Only leaf
    (non-container) values are counted. Keys starting with '_' are skipped
    (internal metadata).

    Returns:
        (total_leaves, na_leaves)
    """
    if isinstance(data, dict):
        total = 0
        na = 0
        for key, val in data.items():
            if isinstance(key, str) and key.startswith("_"):
                continue
            if isinstance(val, dict) and val:
                # Recurse into non-empty nested dicts
                sub_total, sub_na = _count_leaf_values(val)
                total += sub_total
                na += sub_na
            elif isinstance(val, list):
                if not val:
                    # Empty list counts as 1 N/A leaf
                    total += 1
                    na += 1
                else:
                    # Non-empty list is a real value (not N/A)
                    total += 1
            else:
                # Leaf value
                total += 1
                if _is_na(val):
                    na += 1
        return total, na

    # Non-dict at top level: single leaf
    return 1, (1 if _is_na(data) else 0)


# Known worksheet section keys that should be checked for completeness.
# Other dict keys in the context (chart_images, spectrums, crf_bar, etc.)
# are auxiliary data, not user-facing sections.
_KNOWN_SECTION_KEYS: set[str] = {
    "executive_summary",
    "financials",
    "market",
    "governance",
    "litigation",
    "scoring",
    "company",
}


# ---------------------------------------------------------------------------
# SectionCompletenessGate
# ---------------------------------------------------------------------------


class SectionCompletenessGate:
    """Gate that detects sections with too many N/A values.

    Args:
        threshold: N/A ratio above which a section is suppressed.
            Default 0.5 (50%).
        section_keys: Optional set of context keys to check. If None,
            checks all top-level dict-valued keys (useful for tests).
            When called from the renderer, defaults to _KNOWN_SECTION_KEYS.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        section_keys: set[str] | None = None,
    ) -> None:
        self._threshold = threshold
        self._section_keys = section_keys

    def check(self, context: dict[str, Any]) -> list[SectionCompleteness]:
        """Check sections in context for completeness.

        If section_keys is set, only checks those keys. Otherwise checks
        all top-level dict-valued keys. Scalar keys are always skipped.

        Returns:
            List of SectionCompleteness, one per section checked.
        """
        results: list[SectionCompleteness] = []

        for key, value in context.items():
            # Only check dict-valued keys (section contexts)
            if not isinstance(value, dict):
                continue

            # Skip internal/metadata keys
            if key.startswith("_"):
                continue

            # If section_keys filter is set, only check those keys
            if self._section_keys is not None and key not in self._section_keys:
                continue

            total, na = _count_leaf_values(value)
            if total == 0:
                continue

            ratio = na / total
            suppressed = ratio > self._threshold

            reason = ""
            if suppressed:
                reason = (
                    f"Section '{key}' has {na}/{total} fields "
                    f"({ratio:.0%}) with missing data, exceeding "
                    f"the {self._threshold:.0%} threshold"
                )

            results.append(
                SectionCompleteness(
                    section_name=key,
                    total_fields=total,
                    na_fields=na,
                    na_ratio=ratio,
                    suppressed=suppressed,
                    reason=reason,
                )
            )

        return results

    def apply_banners(self, context: dict[str, Any]) -> dict[str, Any]:
        """Replace suppressed sections with Insufficient Data banner dicts.

        For sections exceeding the N/A threshold, replaces the section dict
        with a minimal dict containing banner metadata. Templates guard with
        ``{% if not section._insufficient_data %}`` to skip rendering.

        Args:
            context: Template context dict (modified in-place).

        Returns:
            The same context dict (for chaining).
        """
        completeness = self.check(context)

        for sc in completeness:
            if sc.suppressed:
                logger.warning(
                    "Section '%s' suppressed: %.0f%% N/A (%d/%d fields)",
                    sc.section_name,
                    sc.na_ratio * 100,
                    sc.na_fields,
                    sc.total_fields,
                )
                context[sc.section_name] = {
                    "_insufficient_data": True,
                    "_section_name": sc.section_name,
                    "_na_ratio": sc.na_ratio,
                    "_reason": sc.reason,
                }

        return context


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def check_section_completeness(
    context: dict[str, Any],
    threshold: float = 0.5,
) -> list[SectionCompleteness]:
    """Check section completeness of a template context.

    Args:
        context: Template context dict.
        threshold: N/A ratio threshold (default 0.5).

    Returns:
        List of SectionCompleteness results.
    """
    gate = SectionCompletenessGate(threshold=threshold)
    return gate.check(context)


__all__ = [
    "SectionCompleteness",
    "SectionCompletenessGate",
    "check_section_completeness",
]
