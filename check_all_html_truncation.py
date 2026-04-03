#!/usr/bin/env python3
"""Check all HTML outputs for Jinja truncation artifacts."""

import re
from pathlib import Path

OUTPUT_DIR = Path("output")
ELLIPSIS_PATTERN = re.compile(r"…|\.\.\.")
JINJA_TRUNCATION_PATTERN = re.compile(r"\s*…\s*</")
# Jinja truncation often appears as ellipsis immediately before closing tag
# Extraction truncation appears as ellipsis in middle of text, often with longer surrounding text


def check_html_file(html_path):
    """Return True if Jinja truncation artifacts found."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  ERROR reading {html_path}: {e}")
        return False

    # Find all ellipsis positions
    ellipsis_matches = list(ELLIPSIS_PATTERN.finditer(content))
    if not ellipsis_matches:
        return False

    # Check each ellipsis
    jinja_truncations = []
    extraction_truncations = []

    for match in ellipsis_matches:
        pos = match.start()
        # Get surrounding 200 chars
        start = max(0, pos - 100)
        end = min(len(content), pos + 100)
        context = content[start:end]

        # Check if ellipsis is near closing tag (likely Jinja truncation)
        if re.search(r"…\s*</", context):
            jinja_truncations.append((pos, context))
        else:
            # Check length of preceding text (if short, might be Jinja)
            preceding = content[max(0, pos - 200) : pos]
            # If preceding text is short (<200 chars) and ends with space or punctuation
            # might be Jinja truncation
            if len(preceding) < 200:
                # Check if ellipsis appears after a complete word boundary
                # This is heuristic
                pass
            extraction_truncations.append((pos, context))

    if jinja_truncations:
        print(f"  ⚠️  {len(jinja_truncations)} potential Jinja truncation(s)")
        for pos, ctx in jinja_truncations[:3]:  # show first 3
            print(f"    ...{ctx}...")
        return True
    else:
        if extraction_truncations:
            print(f"  ✓ {len(extraction_truncations)} extraction truncation(s) (acceptable)")
        return False


def main():
    html_files = list(OUTPUT_DIR.glob("**/*.html"))
    print(f"Found {len(html_files)} HTML files in {OUTPUT_DIR}")

    issues = []
    for html_path in sorted(html_files):
        ticker = html_path.parent.name
        print(f"\n{ticker}: {html_path.name}")
        if check_html_file(html_path):
            issues.append(ticker)

    print("\n" + "=" * 60)
    if issues:
        print(f"⚠️  Potential Jinja truncation artifacts found in {len(issues)} tickers:")
        for ticker in issues:
            print(f"  - {ticker}")
        return 1
    else:
        print("✓ No Jinja truncation artifacts found in any HTML files.")
        print("  (Extraction truncations are acceptable LLM word-boundary cuts)")
        return 0


if __name__ == "__main__":
    exit(main())
