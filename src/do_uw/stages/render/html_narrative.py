"""Narrative text processing utilities for HTML rendering.

Extracted from html_renderer.py (Plan 43-04 500-line split rule).

Contains:
  - _strip_markdown: Jinja2 'strip_md' filter — cleans LLM prompt artifacts
  - _narratize: Jinja2 'narratize' filter — structures paragraphs into segments
  - _extract_lead_phrase: Helper for _narratize
"""

from __future__ import annotations

import re


def _extract_lead_phrase(text: str) -> tuple[str, str]:
    """Extract a short bolded lead phrase from the start of a paragraph.

    Looks for a natural break point (first sentence boundary, first comma
    clause, or first ~8 words) to create a bold topic header. Returns
    (header, remaining_body). If text is very short (<80 chars), returns
    empty header to avoid over-splitting.
    """
    if not text or len(text) < 80:
        return ("", text)

    # Try first sentence (up to first period followed by space+capital)
    m = re.match(r"^(.{20,120}?[.!])\s+([A-Z].+)$", text, re.DOTALL)
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Try first clause at comma/semicolon (if clause is 20-80 chars)
    m = re.match(r"^(.{20,80}?)[,;]\s+(.{40,}.+)$", text, re.DOTALL)
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Fallback: first ~8 words
    words = text.split()
    if len(words) > 10:
        lead = " ".join(words[:8])
        rest = " ".join(words[8:])
        return (lead, rest)

    return ("", text)


def _strip_markdown(text: str) -> str:
    """Strip markdown formatting from text for clean HTML display.

    Jinja2 filter registered as 'strip_md'. Removes LLM prompt headers,
    bold (**text**), italic (*text*), and heading markers (## text) that
    may leak from LLM-generated narrative text into the rendered output.
    """
    if not text:
        return ""
    # Strip LLM prompt headers that leak into rendered output
    # Pattern: "AI Assessment: # COMPANY -- NARRATIVE" etc.
    text = re.sub(
        r"^(?:AI\s+Assessment:\s*)?#\s+.*?(?:Assessment|Analysis|Summary|Overview|Risk|Narrative).*$",
        "", text, count=1, flags=re.MULTILINE | re.IGNORECASE,
    )
    # Strip "# AI_RISK --" style headers
    text = re.sub(r"^#\s+AI_\w+\s*[\u2014\u2013\-].*$", "", text, count=1, flags=re.MULTILINE)
    # Strip "COMPANY NAME — D&O UNDERWRITING NARRATIVE" title lines.
    # Matches company names followed by em/en dash + D&O/underwriting/narrative keywords.
    # Also matches "D&O UNDERWRITING THESIS: COMPANY" and
    # "COMPANY — DIRECTORS & OFFICERS LIABILITY UNDERWRITING NARRATIVE".
    text = re.sub(
        r"^[A-Z][A-Z0-9 &.,]+\s*[\u2014\u2013\-]+\s*"
        r"(?:D&O|D&amp;O|Directors?\s*(?:&|and)\s*Officers?(?:\s+Liability)?)\s+"
        r"(?:UNDERWRITING\s+)?(?:NARRATIVE|THESIS)[^\n]*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE,
    )
    # Strip "D&O UNDERWRITING THESIS: COMPANY" (colon-separated variant)
    text = re.sub(
        r"^D&O\s+UNDERWRITING\s+THESIS\s*:\s*[A-Z][A-Z0-9 &.,]+(?:Inc\.|Corp\.|Ltd\.|LLC|Co\.)?\s*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE,
    )
    # Strip "Litigation Portfolio Assessment COMPANY" or similar domain headers
    # These are LLM-generated section titles that leak into narrative text.
    # Match the header line only (up to first sentence period or end of line).
    text = re.sub(
        r"^(?:Litigation\s+Portfolio\s+Assessment|Financial\s+Health\s+Assessment|"
        r"Market\s+(?:&\s+)?Trading\s+Assessment|Governance\s+(?:&\s+)?Leadership\s+Assessment|"
        r"Governance\s+Assessment|Company\s+Profile\s+Assessment|Scoring\s+(?:&\s+)?Risk\s+Assessment)"
        r"(?:\s+[A-Z][A-Za-z\s,\.]+(?:Inc\.|Corp\.|Ltd\.|LLC|Co\.)?)?\s*",
        "", text, count=1, flags=re.MULTILINE,
    )
    # Remove bold markers: **text** -> text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Remove italic markers: *text* -> text
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Remove markdown headers: ## text -> text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Strip LLM-generated underwriting directives — system must not dictate
    # specific limits, attachment points, or binding decisions.
    # Match "BIND at ... tier with $X-YM limit" and similar prescriptive text.
    text = re.sub(
        r"(?:BIND|Bind)\s+at\s+.*?(?:limit|ceiling|attachment)[^.]*\.",
        "", text, flags=re.IGNORECASE,
    )
    # Strip sentences that prescribe specific dollar limits for underwriting
    text = re.sub(
        r"[^.]*\$\d+[\-\u2013]\$?\d+[MBK]?\s+limit[^.]*\.",
        "", text, flags=re.IGNORECASE,
    )
    return text.strip()


def _narratize(text: str) -> list[dict[str, str]]:
    """Parse narrative text into structured segments with topic headers.

    Jinja2 filter registered as 'narratize'. Splits LLM-generated narrative
    text into bulleted segments. Detects topic headers (e.g., "Financial Health:")
    and markdown bullet points.

    Returns list of {header: str, body: str} dicts. If parsing produces <=1
    segment, returns empty list (caller should fall back to plain paragraph).
    """
    if not text:
        return []

    # Strip markdown formatting first
    cleaned = _strip_markdown(text)
    if not cleaned:
        return []

    segments: list[dict[str, str]] = []

    # Topic header pattern: line starts with capitalized words followed by colon
    _TOPIC_RE = re.compile(r"^[A-Z][A-Za-z&/\s]{1,60}?:\s+")

    # Split on newlines to handle both paragraph and bullet formats
    lines = cleaned.split("\n")

    # Merge lines into logical paragraphs (consecutive non-empty lines)
    # Break on: blank lines, bullet points, and lines starting with topic headers
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        # Detect bullet points (-, *, numbered)
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+[.)]\s+", stripped):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            # Strip the bullet marker
            cleaned_bullet = re.sub(r"^[-*]\s+", "", stripped)
            cleaned_bullet = re.sub(r"^\d+[.)]\s+", "", cleaned_bullet)
            paragraphs.append(cleaned_bullet)
        elif _TOPIC_RE.match(stripped):
            # Line starts with a topic header — treat as new paragraph
            if current:
                paragraphs.append(" ".join(current))
                current = []
            current.append(stripped)
        elif stripped:
            current.append(stripped)
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []
    if current:
        paragraphs.append(" ".join(current))

    # Parse each paragraph for topic headers (e.g., "Financial Health: The company...")
    for para in paragraphs:
        # Match "Topic Header: rest of text" where header is 2-6 capitalized words
        m = re.match(r"^([A-Z][A-Za-z&/\s]{1,60}?):\s+(.+)$", para, re.DOTALL)
        if m:
            header = m.group(1).strip()
            body = m.group(2).strip()
            segments.append({"header": header, "body": body})
        else:
            # No explicit header — extract a short topic from the opening phrase.
            # Strategy: take the first sentence or clause (up to first period or
            # comma that's followed by a longer continuation), cap at ~60 chars.
            header, body = _extract_lead_phrase(para.strip())
            segments.append({"header": header, "body": body})

    # If we only got 1 segment and it's long, try splitting on sentences
    if len(segments) <= 1 and segments and len(segments[0].get("body", "")) > 300:
        text_to_split = segments[0].get("body", "") or segments[0].get("header", "")
        sentence_segments = _split_long_paragraph(text_to_split)
        if len(sentence_segments) > 1:
            return sentence_segments

    # Only return structured segments if we got >1 (otherwise plain paragraph is better)
    if len(segments) <= 1:
        return []

    return segments


def _split_long_paragraph(text: str) -> list[dict[str, str]]:
    """Split a long single paragraph into sentence-based segments.

    Groups 2-3 related sentences together per segment, extracting
    a lead phrase from each group. Only used when a single paragraph
    exceeds 300 characters.
    """
    # Split on sentence boundaries: period/semicolon followed by space+capital
    sentences = re.split(r"(?<=[.;])\s+(?=[A-Z])", text)
    if len(sentences) <= 2:
        return []

    # Group sentences into segments of 2-3 each
    segments: list[dict[str, str]] = []
    i = 0
    while i < len(sentences):
        # Take 2 sentences per segment, or 3 if near the end
        chunk_size = 3 if i + 3 >= len(sentences) and i + 1 < len(sentences) else 2
        chunk = " ".join(sentences[i:i + chunk_size])
        header, body = _extract_lead_phrase(chunk.strip())
        segments.append({"header": header, "body": body})
        i += chunk_size

    return segments if len(segments) > 1 else []


__all__ = ["_extract_lead_phrase", "_narratize", "_strip_markdown"]
