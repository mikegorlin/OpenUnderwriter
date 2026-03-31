"""Post-render HTML sanitization safety net.

This module provides a single-pass sanitizer that runs AFTER all Jinja2
template rendering is complete. It catches markdown artifacts, raw Python
serialization, system jargon, and debug strings that leaked through existing
pre-render filters.

This is a SAFETY NET, not a replacement for proper template filters. Every
substitution is logged so that upstream fixes can be applied to prevent
the leak in the first place.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import ClassVar

logger = logging.getLogger(__name__)

# Known internal codes from qa_content.py — these should never appear in output
_KNOWN_CODES = {
    "DATA_UNAVAILABLE", "NOT_AUTO_EVALUATED", "MANUAL_ONLY",
    "FALLBACK_ONLY", "SECTOR_CONDITIONAL", "SEC_FORM4",
    "SEC_ENFORCEMENT", "MARKET_SHORT", "SEC_FRAMES",
    "REFERENCE_DATA", "SEC_S1", "SEC_S3", "SEC_13DG",
    "INSIDER_TRADES", "SEC_8K", "SCAC_SEARCH", "SEC_DEF14A",
    "MARKET_PRICE", "SEC_10K", "NET_SELLING", "A_DISCLOSURE",
}


@dataclass
class SanitizationEntry:
    """A single substitution made by the sanitizer."""

    category: str  # markdown | python_serial | jargon | debug
    pattern_name: str
    matched_text: str
    replacement: str
    line_context: str  # ~40 chars surrounding the match


@dataclass
class SanitizationLog:
    """Collects all substitutions from a sanitize() pass."""

    entries: list[SanitizationEntry] = field(default_factory=list)

    @property
    def total_substitutions(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        """Human-readable summary of all substitutions."""
        if not self.entries:
            return "No sanitization needed."
        lines = [f"Sanitizer made {self.total_substitutions} substitution(s):"]
        by_cat: dict[str, int] = {}
        for e in self.entries:
            by_cat[e.category] = by_cat.get(e.category, 0) + 1
        for cat, count in sorted(by_cat.items()):
            lines.append(f"  {cat}: {count}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Markdown patterns
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_MD_ITALIC_RE = re.compile(r"(?<![a-zA-Z])\*([^*]+?)\*(?![a-zA-Z])")
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_MD_HR_RE = re.compile(r"^(?:---+|\*\*\*+)$")
_MD_BACKTICK_RE = re.compile(r"`([^`]+)`")

# Python serialization patterns
_PY_LIST_SINGLE_RE = re.compile(r"\['([^']*)'(?:,\s*'([^']*)')*\]")
_PY_LIST_DOUBLE_RE = re.compile(r'\["([^"]*)"(?:,\s*"([^"]*)")*\]')
_PY_DICT_SINGLE_RE = re.compile(r"\{(?:'[^']*'\s*:\s*'[^']*'(?:,\s*'[^']*'\s*:\s*'[^']*')*)\}")
_PY_DICT_DOUBLE_RE = re.compile(r'\{(?:"[^"]*"\s*:\s*"[^"]*"(?:,\s*"[^"]*"\s*:\s*"[^"]*")*)\}')
# Trailing list serialization artifacts (",  at end of question/sentence)
_PY_TRAILING_COMMA_QUOTE_RE = re.compile(r'[?!.]\s*",?\s*$')

# NaN/nan in formatted output (e.g., "+nan%", "nan%", "$nan")
_PY_NAN_RE = re.compile(r"(?<![a-zA-Z])[+\-$]?nan%?(?![a-zA-Z])", re.IGNORECASE)

_PY_NONE_STANDALONE_RE = re.compile(r"^None$")
_PY_TRUE_STANDALONE_RE = re.compile(r"^True$")
_PY_FALSE_STANDALONE_RE = re.compile(r"^False$")

# SourcedValue repr patterns (Phase 140 QA: these leak into board forensics, officer profiles)
_PY_SOURCED_VALUE_RE = re.compile(
    r"value='[^']*'\s+source='[^']*'\s+confidence=<[^>]+>"
    r"(?:\s+as_of=datetime\.datetime\([^)]*\))?"
    r"(?:\s+retrieved_at=datetime\.datetime\([^)]*\))?",
)
_PY_DATETIME_RE = re.compile(
    r"datetime\.datetime\(\d{4},\s*\d{1,2},\s*\d{1,2}"
    r"(?:,\s*\d{1,2})*"
    r"(?:,\s*tzinfo=datetime\.timezone\.\w+)?\)",
)
_PY_CONFIDENCE_ENUM_RE = re.compile(
    r"(?:<\s*)?Confidence\.\w+(?::\s*'?\w+'?)?\s*(?:>)?",
)

# Jargon patterns
_JARGON_FACTOR_CODE_RE = re.compile(r"F\.?\d{1,2}\s*=\s*[\d.]+/\d+\s*")
# Handle nested parens like (threshold: Average tenure >15 years (entrenchment risk))
_JARGON_THRESHOLD_RE = re.compile(r"\s*\(threshold:[^)]*(?:\([^)]*\)[^)]*)*\)")
_JARGON_SIGNALS_TRIGGERED_RE = re.compile(
    r"\d+\s+(?:brain\s+)?signals?\(?s?\)?\s+triggered(?:\s+in\s+this\s+category)?"
)
_JARGON_TRIGGERED_PREFIX_RE = re.compile(r"triggered\s+[^—]+—\s*")
_JARGON_COVERAGE_RE = re.compile(r"coverage=\d+%")
_JARGON_EVAL_METHOD_RE = re.compile(r"evaluation_method:\s*\S+")
_JARGON_SCHEMA_VERSION_RE = re.compile(r"schema_version:\s*\S+")
# Orphaned closing paren after a number, left behind by nested-threshold stripping
# e.g., "Tenure at 17.92) signals" -> "Tenure at 17.9 years signals"
_JARGON_ORPHAN_PAREN_RE = re.compile(r"(\bat\s+)(\d+(?:\.\d+)?)\s*\)\s*")

# Enum value patterns (STRONG_BUY, NET_SELLING, HIGH_SCIENTER etc.)
_ENUM_SCREAMING_RE = re.compile(r"\b([A-Z]+_[A-Z_]+)\b")
# Map of known enum values to human-readable text
_ENUM_DISPLAY_MAP: dict[str, str] = {
    "STRONG_BUY": "Strong Buy",
    "STRONG_SELL": "Strong Sell",
    "NET_SELLING": "Net Selling",
    "NET_BUYING": "Net Buying",
    "NET_SELLER": "Net Seller",
    "NET_BUYER": "Net Buyer",
    "HIGH_SCIENTER": "High Scienter Risk",
    "LOW_SCIENTER": "Low Scienter Risk",
    "A_DISCLOSURE": "Disclosure",
    "E_MA": "M&A",
}

# Source label patterns that reveal AI pipeline internals
_SOURCE_LLM_RE = re.compile(r"\b10-K\s*\(LLM\)\b")
_SOURCE_INTERNAL_RE = re.compile(r"\b(?:LLM extraction|LLM_EXTRACTION|llm_extraction)\b")

# D&O boilerplate patterns (baked in state.json from enrichment stage)
_DOC_STANDARD_EXPOSURE_RE = re.compile(
    r"(?:presents|standard)\s+(?:standard\s+)?D&amp;O\s+exposure(?:\s+monitoring)?\.?",
    re.IGNORECASE,
)
_DOC_RELATIVE_THRESHOLD_RE = re.compile(
    r"[Bb]elow-average\s+\w+\s+risk\s+relative\s+to\s+scoring\s+thresholds?",
)
_DOC_REVIEW_DISCLOSURE_RE = re.compile(
    r"8-K material event\s*—?\s*review for disclosure implications",
)

# Debug patterns
_DEBUG_CLASS_RE = re.compile(r"<class\s+'[^']*'>")
_DEBUG_MODULE_RE = re.compile(r"<module\s+'[^']*'>")
_DEBUG_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\).*", re.DOTALL)


def _extract_list_items(text: str) -> str:
    """Convert a Python list repr string to comma-separated items."""
    # Remove brackets
    inner = text[1:-1]
    # Split on comma, strip quotes and whitespace
    items = []
    for item in inner.split(","):
        item = item.strip().strip("'\"")
        if item:
            items.append(item)
    return ", ".join(items)


# Tags whose text content should never be modified
_SKIP_TAGS = frozenset({"script", "style", "code", "pre"})

# Regex to match HTML tags (including self-closing, comments, doctype)
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)

# Regex to match skip-tag blocks: <script>...</script>, <style>...</style>, etc.
_SKIP_BLOCK_RES = {
    tag: re.compile(
        rf"<{tag}[\s>].*?</{tag}>", re.DOTALL | re.IGNORECASE
    )
    for tag in _SKIP_TAGS
}

# Regex to match data-raw="true" blocks
_DATA_RAW_RE = re.compile(
    r'<[^>]+data-raw\s*=\s*["\']true["\'][^>]*>.*?</[^>]+>',
    re.DOTALL | re.IGNORECASE,
)


def _find_text_spans(html: str) -> list[tuple[int, int, str]]:
    """Find all text node positions in HTML, skipping protected regions.

    Uses regex-based approach rather than HTMLParser to avoid issues with
    malformed HTML or HTML entities like &lt; being decoded to < and
    breaking tag detection.

    Returns list of (start, end, text) tuples.
    """
    # Build a set of protected ranges (byte positions to skip)
    protected: list[tuple[int, int]] = []

    # Mark skip-tag blocks as protected
    for tag_re in _SKIP_BLOCK_RES.values():
        for m in tag_re.finditer(html):
            protected.append((m.start(), m.end()))

    # Mark data-raw blocks as protected
    for m in _DATA_RAW_RE.finditer(html):
        protected.append((m.start(), m.end()))

    # Sort protected ranges
    protected.sort()

    def _is_protected(pos: int) -> bool:
        for ps, pe in protected:
            if ps <= pos < pe:
                return True
            if ps > pos:
                break
        return False

    # Find all text between tags
    spans: list[tuple[int, int, str]] = []
    last_end = 0
    for m in _HTML_TAG_RE.finditer(html):
        tag_start = m.start()
        if tag_start > last_end:
            text = html[last_end:tag_start]
            if text.strip() and not _is_protected(last_end):
                spans.append((last_end, tag_start, text))
        last_end = m.end()

    # Text after last tag
    if last_end < len(html):
        text = html[last_end:]
        if text.strip() and not _is_protected(last_end):
            spans.append((last_end, len(html), text))

    return spans


class OutputSanitizer:
    """Post-render HTML sanitizer.

    Walks text nodes in rendered HTML and applies pattern-based substitutions
    for markdown artifacts, Python serialization, system jargon, and debug
    strings. Skips script, style, code, and pre tags. Skips elements with
    data-raw="true" attribute.

    Every substitution is logged to SanitizationLog for upstream fix evidence.
    """

    # Pattern categories applied in order (most specific first)
    CATEGORIES: ClassVar[list[str]] = ["debug", "python_serial", "jargon", "markdown"]

    @classmethod
    def from_defaults(cls) -> OutputSanitizer:
        """Create sanitizer with standard configuration."""
        return cls()

    def sanitize(self, html: str) -> tuple[str, SanitizationLog]:
        """Sanitize rendered HTML, returning cleaned HTML and substitution log."""
        log = SanitizationLog()

        if not html:
            return "", log

        # Pre-pass: remove debug patterns that look like HTML tags
        # (e.g., <class 'module.Class'>, <module 'name'>) — these are
        # consumed by the HTML tag regex and never appear as text nodes.
        html = self._pre_pass_debug_tags(html, log)

        # Find text nodes using regex-based approach (avoids HTMLParser
        # issues with &lt; being decoded and breaking tag detection)
        text_spans = _find_text_spans(html)

        # Process text spans in reverse order so positions remain valid
        result = html
        for start, end, original_text in reversed(text_spans):
            cleaned = self._sanitize_text(original_text, log)
            if cleaned != original_text:
                result = result[:start] + cleaned + result[end:]

        if log.total_substitutions > 0:
            logger.warning(
                "OutputSanitizer made %d substitution(s) — "
                "investigate upstream to prevent leakage",
                log.total_substitutions,
            )
            logger.info(log.summary())

        return result, log

    def _pre_pass_debug_tags(self, html: str, log: SanitizationLog) -> str:
        """Remove debug patterns that resemble HTML tags before text extraction.

        Patterns like <class 'module.Class'> and <module 'name'> are consumed
        by the HTML tag regex and never appear as text nodes, so they must be
        handled in a pre-pass.
        """
        result = html
        for pattern, name in [
            (_DEBUG_CLASS_RE, "class_repr"),
            (_DEBUG_MODULE_RE, "module_repr"),
        ]:
            for match in pattern.finditer(result):
                self._log_entry(log, "debug", name, match.group(), "", match.group())
            result = pattern.sub("", result)
        return result

    def _sanitize_text(self, text: str, log: SanitizationLog) -> str:
        """Apply all pattern categories to a single text node."""
        result = text

        for category in self.CATEGORIES:
            handler = getattr(self, f"_apply_{category}", None)
            if handler:
                result = handler(result, text, log)

        return result

    def _log_entry(
        self,
        log: SanitizationLog,
        category: str,
        pattern_name: str,
        matched: str,
        replacement: str,
        original_text: str,
    ) -> None:
        """Record a substitution in the log."""
        # Extract ~40 chars of context around the match
        idx = original_text.find(matched)
        if idx >= 0:
            ctx_start = max(0, idx - 20)
            ctx_end = min(len(original_text), idx + len(matched) + 20)
            context = original_text[ctx_start:ctx_end]
        else:
            context = original_text[:40]

        log.entries.append(
            SanitizationEntry(
                category=category,
                pattern_name=pattern_name,
                matched_text=matched,
                replacement=replacement,
                line_context=context,
            )
        )

    # ------------------------------------------------------------------
    # Category: debug
    # ------------------------------------------------------------------
    def _apply_debug(
        self, text: str, original: str, log: SanitizationLog
    ) -> str:
        result = text

        # Note: class_repr and module_repr are handled in _pre_pass_debug_tags
        # because they look like HTML tags and are consumed by the tag regex.
        match = _DEBUG_TRACEBACK_RE.search(result)
        if match:
            self._log_entry(log, "debug", "traceback", match.group(), "", original)
            result = _DEBUG_TRACEBACK_RE.sub("", result)

        return result

    # ------------------------------------------------------------------
    # Category: python_serial
    # ------------------------------------------------------------------
    def _apply_python_serial(
        self, text: str, original: str, log: SanitizationLog
    ) -> str:
        result = text

        # Python lists
        for pattern, name in [
            (_PY_LIST_SINGLE_RE, "list_single_quote"),
            (_PY_LIST_DOUBLE_RE, "list_double_quote"),
        ]:
            match = pattern.search(result)
            if match:
                items = _extract_list_items(match.group())
                self._log_entry(
                    log, "python_serial", name, match.group(), items, original
                )
                result = result[: match.start()] + items + result[match.end() :]

        # Python dicts
        for pattern, name in [
            (_PY_DICT_SINGLE_RE, "dict_single_quote"),
            (_PY_DICT_DOUBLE_RE, "dict_double_quote"),
        ]:
            match = pattern.search(result)
            if match:
                self._log_entry(
                    log, "python_serial", name, match.group(), "", original
                )
                result = pattern.sub("", result)

        # SourcedValue repr strings (value='...' source='...' confidence=<...>)
        for match in _PY_SOURCED_VALUE_RE.finditer(result):
            # Extract just the value= portion
            val_match = re.search(r"value='([^']*)'", match.group())
            replacement = val_match.group(1) if val_match else ""
            self._log_entry(
                log, "python_serial", "sourced_value_repr",
                match.group()[:60], replacement, original,
            )
        result = _PY_SOURCED_VALUE_RE.sub(
            lambda m: re.search(r"value='([^']*)'", m.group()).group(1)
            if re.search(r"value='([^']*)'", m.group()) else "",
            result,
        )

        # datetime.datetime() objects
        for match in _PY_DATETIME_RE.finditer(result):
            self._log_entry(
                log, "python_serial", "datetime_repr",
                match.group()[:40], "", original,
            )
        result = _PY_DATETIME_RE.sub("", result)

        # Confidence enum references (Confidence.HIGH, <Confidence.LOW: 'LOW'>)
        for match in _PY_CONFIDENCE_ENUM_RE.finditer(result):
            self._log_entry(
                log, "python_serial", "confidence_enum",
                match.group(), "", original,
            )
        result = _PY_CONFIDENCE_ENUM_RE.sub("", result)

        # NaN in formatted output (+nan%, $nan, nan)
        nan_match = _PY_NAN_RE.search(result)
        if nan_match:
            self._log_entry(
                log, "python_serial", "nan_value",
                nan_match.group(), "N/A", original,
            )
            result = _PY_NAN_RE.sub("N/A", result)

        # Trailing list serialization artifacts: question?", -> question?
        trail_match = _PY_TRAILING_COMMA_QUOTE_RE.search(result)
        if trail_match:
            # Strip the trailing ", leaving just the punctuation
            cleaned = re.sub(r'([?!.])\s*",?\s*$', r'\1', result)
            if cleaned != result:
                self._log_entry(
                    log, "python_serial", "trailing_comma_quote",
                    result[-10:], cleaned[-10:], original,
                )
                result = cleaned

        # Standalone None/True/False
        stripped = result.strip()
        if _PY_NONE_STANDALONE_RE.match(stripped):
            self._log_entry(log, "python_serial", "none_standalone", "None", "N/A", original)
            result = result.replace("None", "N/A", 1)
        elif _PY_TRUE_STANDALONE_RE.match(stripped):
            self._log_entry(log, "python_serial", "true_standalone", "True", "Yes", original)
            result = result.replace("True", "Yes", 1)
        elif _PY_FALSE_STANDALONE_RE.match(stripped):
            self._log_entry(log, "python_serial", "false_standalone", "False", "No", original)
            result = result.replace("False", "No", 1)

        return result

    # ------------------------------------------------------------------
    # Category: jargon
    # ------------------------------------------------------------------
    def _apply_jargon(
        self, text: str, original: str, log: SanitizationLog
    ) -> str:
        result = text

        # Known internal codes -> N/A
        for code in _KNOWN_CODES:
            if code in result:
                # Only replace if it appears as a standalone word/token
                code_re = re.compile(rf"\b{re.escape(code)}\b")
                if code_re.search(result):
                    self._log_entry(log, "jargon", f"known_code_{code}", code, "N/A", original)
                    result = code_re.sub("N/A", result)

        # Factor codes: F.7 = 5/8
        match = _JARGON_FACTOR_CODE_RE.search(result)
        if match:
            self._log_entry(log, "jargon", "factor_code", match.group(), "", original)
            result = _JARGON_FACTOR_CODE_RE.sub("", result)

        # Threshold context: (threshold: ...) — supports nested parens
        match = _JARGON_THRESHOLD_RE.search(result)
        if match:
            self._log_entry(log, "jargon", "threshold_context", match.group(), "", original)
            result = _JARGON_THRESHOLD_RE.sub("", result)

        # Orphaned closing paren after number: "at 17.92) signals" -> "at 17.9 years signals"
        match = _JARGON_ORPHAN_PAREN_RE.search(result)
        if match:
            # Round to 1 decimal and append " years" for readability
            try:
                val = round(float(match.group(2)), 1)
                replacement = f"{match.group(1)}{val} years "
            except ValueError:
                replacement = f"{match.group(1)}{match.group(2)} "
            self._log_entry(
                log, "jargon", "orphan_paren", match.group(), replacement, original,
            )
            result = _JARGON_ORPHAN_PAREN_RE.sub(replacement, result)

        # N signals triggered
        match = _JARGON_SIGNALS_TRIGGERED_RE.search(result)
        if match:
            self._log_entry(log, "jargon", "signals_triggered", match.group(), "", original)
            result = _JARGON_SIGNALS_TRIGGERED_RE.sub("", result)

        # triggered SIGNAL_NAME (FN) --
        match = _JARGON_TRIGGERED_PREFIX_RE.search(result)
        if match:
            self._log_entry(log, "jargon", "triggered_prefix", match.group(), "", original)
            result = _JARGON_TRIGGERED_PREFIX_RE.sub("", result)

        # coverage=100%
        match = _JARGON_COVERAGE_RE.search(result)
        if match:
            self._log_entry(log, "jargon", "coverage_display", match.group(), "", original)
            result = _JARGON_COVERAGE_RE.sub("", result)

        # evaluation_method: / schema_version:
        for pattern, name in [
            (_JARGON_EVAL_METHOD_RE, "evaluation_method"),
            (_JARGON_SCHEMA_VERSION_RE, "schema_version"),
        ]:
            match = pattern.search(result)
            if match:
                self._log_entry(log, "jargon", name, match.group(), "", original)
                result = pattern.sub("", result)

        # Screaming enum values (STRONG_BUY -> Strong Buy, etc.)
        for match in _ENUM_SCREAMING_RE.finditer(result):
            enum_val = match.group(1)
            if enum_val in _ENUM_DISPLAY_MAP:
                human = _ENUM_DISPLAY_MAP[enum_val]
                self._log_entry(
                    log, "jargon", "enum_value", enum_val, human, original,
                )
                result = result.replace(enum_val, human, 1)

        # Source labels that reveal AI pipeline ("10-K (LLM)" -> "10-K Filing")
        match = _SOURCE_LLM_RE.search(result)
        if match:
            self._log_entry(
                log, "jargon", "source_llm_label", match.group(), "10-K Filing", original,
            )
            result = _SOURCE_LLM_RE.sub("10-K Filing", result)

        match = _SOURCE_INTERNAL_RE.search(result)
        if match:
            self._log_entry(
                log, "jargon", "source_internal_label", match.group(), "", original,
            )
            result = _SOURCE_INTERNAL_RE.sub("", result)

        # D&O boilerplate baked in state.json from enrichment stage
        for pattern, name, replacement in [
            (_DOC_STANDARD_EXPOSURE_RE, "standard_do_exposure", ""),
            (_DOC_RELATIVE_THRESHOLD_RE, "relative_threshold", "Within normal parameters."),
            (_DOC_REVIEW_DISCLOSURE_RE, "review_disclosure", "Material event filed"),
        ]:
            match = pattern.search(result)
            if match:
                self._log_entry(
                    log, "jargon", name, match.group(), replacement, original,
                )
                result = pattern.sub(replacement, result)

        return result

    # ------------------------------------------------------------------
    # Category: markdown
    # ------------------------------------------------------------------
    def _apply_markdown(
        self, text: str, original: str, log: SanitizationLog
    ) -> str:
        result = text

        # Bold: **text** -> text
        for match in _MD_BOLD_RE.finditer(result):
            self._log_entry(
                log, "markdown", "bold", match.group(), match.group(1), original
            )
        result = _MD_BOLD_RE.sub(r"\1", result)

        # Italic: *text* -> text (but not contractions)
        for match in _MD_ITALIC_RE.finditer(result):
            self._log_entry(
                log, "markdown", "italic", match.group(), match.group(1), original
            )
        result = _MD_ITALIC_RE.sub(r"\1", result)

        # Heading markers: ### text -> text
        match = _MD_HEADING_RE.search(result)
        if match:
            self._log_entry(log, "markdown", "heading", match.group(), "", original)
            result = _MD_HEADING_RE.sub("", result)

        # Horizontal rules: --- or ***
        if _MD_HR_RE.match(result.strip()):
            self._log_entry(log, "markdown", "horizontal_rule", result.strip(), "", original)
            result = ""

        # Backtick code: `text` -> text
        for match in _MD_BACKTICK_RE.finditer(result):
            self._log_entry(
                log, "markdown", "backtick", match.group(), match.group(1), original
            )
        result = _MD_BACKTICK_RE.sub(r"\1", result)

        return result


__all__ = ["OutputSanitizer", "SanitizationEntry", "SanitizationLog"]
