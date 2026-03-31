"""Footnote registry for HTML data tracing (Plan 43-04).

FootnoteRegistry pre-collects all data source citations from AnalysisState
before template rendering, assigns sequential footnote numbers (1-based),
and deduplicates identical sources.

The registry is passed to Jinja2 templates via build_html_context() as
context['footnote_registry'] and context['all_sources'].

Inline usage in templates:
    <sup class="fn-ref"><a href="#fn-{{ fn_num }}">{{ fn_num }}</a></sup>

Sources appendix anchor targets:
    <li id="fn-{{ num }}">{{ source_text }}</li>
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


class FootnoteRegistry:
    """Pre-collected source citations for footnote rendering.

    Assigned sequential numbers (1-based) in order of first registration.
    Identical source strings receive the same number (deduplication).

    Usage:
        reg = FootnoteRegistry()
        fn = reg.register("10-K (SEC EDGAR), filed 2024-02-23")  # -> 1
        fn = reg.register("10-K (SEC EDGAR), filed 2024-02-23")  # -> 1 (deduplicated)
        fn = reg.register("DEF 14A (SEC EDGAR), filed 2024-03-15")  # -> 2
        pairs = reg.all_sources  # -> [(1, "10-K..."), (2, "DEF 14A...")]
    """

    def __init__(self) -> None:
        self._sources: list[str] = []
        self._index: dict[str, int] = {}

    def register(self, source_text: str) -> int:
        """Register a source, return its footnote number (1-based).

        Idempotent — registering the same source twice returns the same number.
        Returns 0 for empty/None source_text (no footnote rendered).
        """
        if not source_text or not source_text.strip():
            return 0
        text = source_text.strip()
        if text in self._index:
            return self._index[text]
        self._sources.append(text)
        num = len(self._sources)
        self._index[text] = num
        return num

    def get(self, source_text: str) -> int:
        """Get footnote number for an already-registered source, 0 if not found.

        Returns 0 for empty/None source_text (safe: no superscript rendered).
        """
        if not source_text:
            return 0
        return self._index.get(source_text.strip(), 0)

    @property
    def all_sources(self) -> list[tuple[int, str]]:
        """Return list of (number, source_text) for Sources appendix rendering."""
        return [(i, _humanize_source_text(s)) for i, s in enumerate(self._sources, 1)]

    def __len__(self) -> int:
        return len(self._sources)


def _humanize_source_text(text: str) -> str:
    """Replace SCREAMING_SNAKE prefixes in source text with readable labels.

    'SEC_FORM4 Ceo Transactions' -> 'Form 4 Ceo Transactions'
    """
    import re
    from do_uw.stages.render.formatters_humanize import _SOURCE_LABELS as _HUMANIZE_LABELS
    def _replace(m: re.Match[str]) -> str:
        return _HUMANIZE_LABELS.get(m.group(0), m.group(0).replace("_", " ").title())
    return re.sub(r"[A-Z][A-Z0-9_]{2,}[A-Z0-9]", _replace, text)


# ---------------------------------------------------------------------------
# Source label mapping (shared with html_renderer._format_filing_ref)
# ---------------------------------------------------------------------------

_SOURCE_LABELS: dict[str, str] = {
    "SEC_10K": "10-K",
    "SEC_DEF14A": "DEF 14A",
    "SEC_10Q": "10-Q",
    "SEC_8K": "8-K",
    "SCAC_SEARCH": "SCAC Search",
    "MARKET_PRICE": "Market Data",
    "XBRL": "XBRL",
    "WEB_SEARCH": "Web Search",
    "YFINANCE": "yFinance",
}


def _format_trace_source(trace_data_source: str) -> str:
    """Parse trace_data_source into readable filing reference for footnotes.

    Input examples:
        "SEC_10K:item_3_legal_proceedings; SCAC_SEARCH:search_results"
        "SEC_DEF14A:executive_compensation"
    Output:
        "10-K Item 3 Legal Proceedings, SCAC Search Results"
    """
    if not trace_data_source:
        return ""
    parts = []
    for chunk in trace_data_source.split(";"):
        chunk = chunk.strip()
        if ":" in chunk:
            src, section = chunk.split(":", 1)
            label = _SOURCE_LABELS.get(src.strip(), src.strip())
            section = section.strip().replace("_", " ").title()
            parts.append(f"{label} {section}" if section else label)
        elif chunk:
            parts.append(chunk)
    return ", ".join(parts[:3])


def build_footnote_registry(state: AnalysisState) -> FootnoteRegistry:
    """Pre-collect all data source citations from AnalysisState.

    Walks:
      - acquired_data.filing_documents (form_type + filing_date)
      - analysis.signal_results (trace_data_source field)

    Returns a populated FootnoteRegistry ready for template use.
    Sources are registered in a deterministic order so footnote numbers
    are stable across renders for the same state.
    """
    reg = FootnoteRegistry()

    # Register filing document sources (most authoritative, registered first)
    if state.acquired_data and state.acquired_data.filing_documents:
        for form_type, docs in state.acquired_data.filing_documents.items():
            if isinstance(docs, list):
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    date = doc.get("filing_date", "")
                    if date:
                        # Map internal form_type key to display label
                        label = _SOURCE_LABELS.get(form_type, form_type)
                        reg.register(f"{label} (SEC EDGAR), filed {date}")
                    elif doc.get("accession_number"):
                        # Fallback: use accession number if no date
                        label = _SOURCE_LABELS.get(form_type, form_type)
                        reg.register(f"{label} (SEC EDGAR)")

    # Register check result data sources
    if state.analysis and state.analysis.signal_results:
        for _signal_id, result in state.analysis.signal_results.items():
            if not isinstance(result, dict):
                continue
            trace_src = result.get("trace_data_source", "")
            if trace_src:
                src = _format_trace_source(str(trace_src))
                if src:
                    reg.register(src)

    logger.debug(
        "FootnoteRegistry: %d unique sources collected from state", len(reg)
    )
    return reg


__all__ = ["FootnoteRegistry", "build_footnote_registry"]
