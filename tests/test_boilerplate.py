"""Tests for boilerplate stripping and token estimation.

Validates that strip_boilerplate removes XBRL tags, exhibit indexes,
signatures, certifications, SEC headers, HTML comments, and
normalizes whitespace -- while preserving substantive content.
"""

from __future__ import annotations

from do_uw.stages.extract.llm.boilerplate import (
    estimate_tokens,
    strip_boilerplate,
)


def test_xbrl_tag_removal() -> None:
    """Inline XBRL tags are removed."""
    text = (
        "Revenue was <ix:nonfraction>1000000</ix:nonfraction> "
        "for the <ix:nonnumeric>fiscal year</ix:nonnumeric>."
    )
    result = strip_boilerplate(text)
    assert "<ix:" not in result
    assert "</ix:" not in result
    assert "1000000" in result
    assert "fiscal year" in result


def test_exhibit_index_removal() -> None:
    """Exhibit index section is removed."""
    text = (
        "Item 15. Exhibits\n\n"
        "EXHIBIT INDEX\n"
        "Exhibit 31.1 - Certification\n"
        "Exhibit 31.2 - Certification\n"
        "Exhibit 32.1 - Certification\n\n"
        "SIGNATURES\nPursuant to the requirements"
    )
    result = strip_boilerplate(text)
    assert "Exhibit 31.1" not in result
    assert "[EXHIBIT INDEX REMOVED]" in result


def test_signature_page_removal() -> None:
    """Signature pages are removed."""
    text = (
        "Some important content.\n\n"
        "SIGNATURES Pursuant to the requirements of "
        "Section 13 or 15(d) of the Securities Exchange "
        "Act of 1934, the registrant has duly caused this "
        "report to be signed on its behalf.\n\n"
        "/s/ John Smith\nCEO"
    )
    result = strip_boilerplate(text)
    assert "/s/ John Smith" not in result
    assert "Some important content." in result
    assert "[SIGNATURES REMOVED]" in result


def test_sec_header_removal() -> None:
    """SEC filing headers are removed."""
    text = (
        "<SEC-HEADER>0001234567-24-000123.hdr.sgml : 20240315\n"
        "ACCESSION NUMBER: 0001234567-24-000123\n"
        "CONFORMED SUBMISSION TYPE: 10-K\n"
        "</SEC-HEADER>\n\n"
        "Business description here."
    )
    result = strip_boilerplate(text)
    assert "CONFORMED SUBMISSION TYPE" not in result
    assert "Business description here." in result


def test_html_comment_removal() -> None:
    """HTML comments are removed."""
    text = (
        "Important text.\n"
        "<!-- This is a comment -->\n"
        "More important text.\n"
        "<!-- Multi\nline\ncomment -->\n"
        "Final text."
    )
    result = strip_boilerplate(text)
    assert "<!--" not in result
    assert "-->" not in result
    assert "Important text." in result
    assert "More important text." in result
    assert "Final text." in result


def test_certification_removal() -> None:
    """Officer certifications are removed."""
    text = (
        "ITEM 9A. Controls and Procedures\n"
        "Our management assessed...\n\n"
        "CERTIFICATION PURSUANT TO RULE 13a-14(a) "
        "OR RULE 15d-14(a)\n"
        "I, John Smith, certify that:\n"
        "1. I have reviewed this annual report\n\n"
        "EXHIBIT 32.1"
    )
    result = strip_boilerplate(text)
    assert "I, John Smith, certify" not in result
    assert "[CERTIFICATION REMOVED]" in result
    assert "Our management assessed" in result


def test_whitespace_normalization() -> None:
    """Excessive whitespace is normalized."""
    text = "Line 1\n\n\n\n\nLine 2\n\n\nLine 3"
    result = strip_boilerplate(text)
    # 3+ newlines -> 2 newlines
    assert "\n\n\n" not in result
    assert "Line 1" in result
    assert "Line 2" in result

    # 3+ spaces -> 1 space
    text2 = "Word1     Word2      Word3"
    result2 = strip_boilerplate(text2)
    assert "     " not in result2
    assert "Word1" in result2
    assert "Word2" in result2


def test_substantive_content_preserved() -> None:
    """Business description, risk factors, and financials survive stripping."""
    text = (
        "Item 1. Business\n\n"
        "We are a technology company.\n\n"
        "Item 1A. Risk Factors\n\n"
        "We face significant risks.\n\n"
        "Item 7. MD&A\n\n"
        "Revenue increased 15% year-over-year.\n\n"
        "Item 8. Financial Statements\n\n"
        "Total revenue: $10,000,000"
    )
    result = strip_boilerplate(text)
    assert "We are a technology company." in result
    assert "We face significant risks." in result
    assert "Revenue increased 15% year-over-year." in result
    assert "Total revenue: $10,000,000" in result


def test_empty_text() -> None:
    """Empty text returns empty string."""
    assert strip_boilerplate("") == ""


def test_no_boilerplate() -> None:
    """Text without boilerplate is returned as-is (trimmed)."""
    text = "Simple clean text with no boilerplate."
    result = strip_boilerplate(text)
    assert result == text


def test_estimate_tokens_basic() -> None:
    """Token estimate returns roughly len/4."""
    text = "a" * 400  # 400 chars = ~100 tokens
    assert estimate_tokens(text) == 100


def test_estimate_tokens_empty() -> None:
    """Empty text estimates zero tokens."""
    assert estimate_tokens("") == 0


def test_estimate_tokens_short() -> None:
    """Short text (< 4 chars) estimates zero tokens."""
    assert estimate_tokens("abc") == 0
