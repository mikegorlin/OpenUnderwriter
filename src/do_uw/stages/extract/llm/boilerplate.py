"""Boilerplate stripping for SEC filing text.

Removes low-value content (XBRL tags, exhibit indexes, signatures,
certifications, SEC headers, HTML comments, financial statement tables)
from filing text to reduce token count before LLM extraction.

Financial statement tables (income, balance sheet, cash flow) are
extracted via XBRL and add significant token cost without extraction
value for the LLM (which focuses on text analysis: risk factors,
legal proceedings, business description, governance).
"""

from __future__ import annotations

import re


def strip_boilerplate(text: str) -> str:
    """Remove SEC filing boilerplate that adds no extraction value.

    Strips XBRL inline tags, exhibit indexes, signature pages,
    SEC filing headers, officer certifications, HTML comments,
    financial statement numeric tables, and normalizes whitespace.

    Args:
        text: Raw filing text (HTML already stripped by filing_fetcher).

    Returns:
        Cleaned text with boilerplate removed.
    """
    # 1. Remove inline XBRL tags (<ix:...> and </ix:...>)
    text = re.sub(r"</?ix:[^>]*>", "", text)

    # 2. Remove SEC filing headers (<SEC-HEADER>...</SEC-HEADER>)
    text = re.sub(
        r"<SEC-HEADER>.*?</SEC-HEADER>",
        "",
        text,
        flags=re.DOTALL,
    )

    # 3. Remove HTML comments (<!-- ... -->)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 4. Remove exhibit index section
    text = re.sub(
        r"(?i)EXHIBIT\s+INDEX.*?(?=SIGNATURES|$)",
        "[EXHIBIT INDEX REMOVED]\n",
        text,
        flags=re.DOTALL,
    )

    # 5. Remove signature pages
    text = re.sub(
        r"(?i)SIGNATURES\s+Pursuant\s+to.*$",
        "[SIGNATURES REMOVED]",
        text,
        flags=re.DOTALL,
    )

    # 6. Remove officer certifications (Exhibits 31/32)
    text = re.sub(
        r"(?i)CERTIFICATION\s+PURSUANT\s+TO.*?(?=\n(?:EXHIBIT|ITEM|\Z))",
        "[CERTIFICATION REMOVED]\n",
        text,
        flags=re.DOTALL,
    )

    # 7. Remove dense numeric table rows (3+ consecutive dollar/number columns)
    # These are financial statement line items already extracted via XBRL.
    # Matches rows like: "Total revenue   60,922   26,974   16,675"
    # or: "$ 60,922 $ 26,974 $ 16,675"
    text = _strip_numeric_tables(text)

    # 8. Remove table of contents / page references
    text = re.sub(
        r"(?i)TABLE\s+OF\s+CONTENTS.*?(?=PART\s+I[^IV]|ITEM\s+1[^0-9])",
        "[TABLE OF CONTENTS REMOVED]\n",
        text,
        flags=re.DOTALL,
    )

    # 9. Normalize excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {3,}", " ", text)

    return text.strip()


def _strip_numeric_tables(text: str) -> str:
    """Remove dense numeric table blocks from filing text.

    Identifies blocks of 5+ consecutive lines where each line contains
    mostly numbers/dollar signs (financial statement line items).
    Preserves table headers and isolated numeric references within
    narrative text.

    Args:
        text: Filing text with potential numeric tables.

    Returns:
        Text with numeric table blocks replaced by placeholders.
    """
    lines = text.split("\n")
    result: list[str] = []
    numeric_run: list[int] = []

    for i, line in enumerate(lines):
        if _is_numeric_table_row(line):
            numeric_run.append(i)
        else:
            if len(numeric_run) >= 5:
                # Replace the numeric block with a placeholder
                result.append("[FINANCIAL TABLE REMOVED - SEE XBRL DATA]")
            else:
                # Short run - keep original lines (likely inline refs)
                for idx in numeric_run:
                    result.append(lines[idx])
            numeric_run = []
            result.append(line)

    # Handle trailing numeric run
    if len(numeric_run) >= 5:
        result.append("[FINANCIAL TABLE REMOVED - SEE XBRL DATA]")
    else:
        for idx in numeric_run:
            result.append(lines[idx])

    return "\n".join(result)


def _is_numeric_table_row(line: str) -> bool:
    """Check if a line is a numeric table row (financial statement data).

    A numeric table row has 2+ numeric values (possibly with $, (, ), commas)
    separated by whitespace, and the numeric content dominates the line.

    Args:
        line: Single line of text.

    Returns:
        True if the line appears to be a financial table data row.
    """
    stripped = line.strip()
    if len(stripped) < 10:
        return False

    # Count numeric-like tokens (numbers with optional $, commas, parens)
    tokens = stripped.split()
    numeric_count = 0
    for token in tokens:
        cleaned = token.strip("$(),-\u2014\u2013")
        cleaned = cleaned.replace(",", "")
        if cleaned.replace(".", "").isdigit() and len(cleaned) >= 1:
            numeric_count += 1

    # A row is numeric if it has 2+ numeric tokens AND they make up
    # a significant fraction of the tokens
    if numeric_count >= 2 and len(tokens) > 0:
        ratio = numeric_count / len(tokens)
        return ratio >= 0.3

    return False


def estimate_tokens(text: str) -> int:
    """Estimate token count using character-based heuristic.

    Simple approximation: 1 token ~= 4 characters.
    Used for quick pre-flight checks before API calls.
    For exact counts, use tiktoken or LLM provider's tokenizer.

    Args:
        text: Text to estimate tokens for.

    Returns:
        Estimated number of tokens.
    """
    return len(text) // 4
