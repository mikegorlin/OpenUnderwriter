"""Boilerplate elimination regression tests.

Catalogs 20+ known boilerplate narrative phrases and provides a utility
function to detect them in rendered output. Every sentence in the worksheet
must contain company-specific data -- generic phrases that could apply to
any company by swapping the name are boilerplate.

Phase 124-02: TDD contract for narrative quality enforcement.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Known boilerplate patterns -- generic phrases that add no information
# ---------------------------------------------------------------------------
BOILERPLATE_PATTERNS: list[str] = [
    # Generic hedging / filler
    r"has experienced a notable",
    r"the company has shown",
    r"demonstrates a commitment to",
    r"is positioned to",
    r"may impact future",
    r"faces potential challenges",
    r"has maintained a strong",
    r"continues to demonstrate",
    r"reflects the company's",
    r"underscores the importance",
    r"it is worth noting",
    r"it should be noted",
    r"given the current landscape",
    r"in the current environment",
    r"going forward(?![\w-])",  # not "going-forward" as adjective
    r"moving forward",
    r"remains to be seen",
    r"time will tell",
    r"has shown a trend",
    r"the company has exhibited",
    # D&O-specific boilerplate
    r"warrants?\s+(?:further\s+)?underwriting\s+attention",
    r"warrants?\s+(?:further\s+)?investigation",
    r"historically correlated with",
    r"moderate risk factors can generate",
    r"contributes? to the overall risk profile",
    r"elevates? D&O exposure$",  # bare "elevates D&O exposure" with no specifics
    r"creates? structural complexity that elevates?",
    r"(?:has|have) governance characteristics that warrant",
]

# Compiled regex for each pattern (case-insensitive)
_COMPILED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (p, re.compile(p, re.IGNORECASE)) for p in BOILERPLATE_PATTERNS
]


def find_boilerplate_matches(text: str, patterns: list[str] | None = None) -> list[str]:
    """Return all boilerplate phrases found in *text*.

    Args:
        text: Narrative or HTML content to scan.
        patterns: Optional override list of regex patterns.
                  Defaults to BOILERPLATE_PATTERNS.

    Returns:
        List of matched phrase strings (the actual text that matched).
    """
    if patterns is None:
        compiled = _COMPILED_PATTERNS
    else:
        compiled = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]

    matches: list[str] = []
    for _raw, rx in compiled:
        for m in rx.finditer(text):
            matches.append(m.group())
    return matches


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBoilerplatePatternCatalog:
    """Verify the boilerplate pattern catalog itself."""

    def test_boilerplate_patterns_defined(self) -> None:
        """At least 20 patterns must be cataloged."""
        assert len(BOILERPLATE_PATTERNS) >= 20, (
            f"Expected 20+ patterns, got {len(BOILERPLATE_PATTERNS)}"
        )

    def test_all_patterns_are_valid_regex(self) -> None:
        """Every pattern must compile without error."""
        for pattern in BOILERPLATE_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None, f"Failed to compile: {pattern}"


class TestFindBoilerplateMatches:
    """Verify the detection utility function."""

    def test_clean_text_passes(self) -> None:
        """Company-specific text should return zero matches."""
        clean = (
            "Apple Inc. reported $394.3B in revenue for FY2024, "
            "a 2.1% YoY increase. Altman Z-Score of 8.42 places "
            "AAPL firmly in the safe zone. CEO Tim Cook has led "
            "the company for 13 years with no material weaknesses "
            "or restatement history."
        )
        matches = find_boilerplate_matches(clean)
        assert matches == [], f"False positives: {matches}"

    def test_generic_text_caught(self) -> None:
        """Text with known boilerplate returns matches."""
        generic = (
            "The company has shown a trend of improvement. "
            "This warrants further underwriting attention. "
            "Going forward, the risk profile may change."
        )
        matches = find_boilerplate_matches(generic)
        assert len(matches) >= 2, f"Expected 2+ matches, got: {matches}"

    def test_single_boilerplate_phrase(self) -> None:
        """A narrative containing 'has experienced a notable decline'."""
        text = "The company has experienced a notable decline in revenue."
        matches = find_boilerplate_matches(text)
        assert any("has experienced a notable" in m for m in matches)

    def test_case_insensitive(self) -> None:
        """Matching is case-insensitive."""
        text = "IT IS WORTH NOTING that metrics have improved."
        matches = find_boilerplate_matches(text)
        assert len(matches) >= 1

    def test_custom_patterns(self) -> None:
        """Custom patterns override the default catalog."""
        text = "The sky is blue and the grass is green."
        matches = find_boilerplate_matches(text, patterns=[r"sky is blue"])
        assert len(matches) == 1

    def test_empty_text(self) -> None:
        """Empty text returns no matches."""
        assert find_boilerplate_matches("") == []


class TestSourceCodeBoilerplateFree:
    """Verify that Python source files generating narratives are boilerplate-free.

    These tests grep the actual source code for hardcoded boilerplate
    phrases that would appear verbatim in rendered output. Lines that
    define patterns (in regex strings or anti-boilerplate directives)
    are excluded -- we only flag boilerplate used as output text.
    """

    def _read_source(self, rel_path: str) -> str:
        """Read a source file relative to project root."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]  # tests/ -> project root
        path = root / "src" / "do_uw" / rel_path
        if not path.exists():
            return ""
        return path.read_text()

    @staticmethod
    def _strip_pattern_definitions(src: str) -> str:
        """Remove lines that define boilerplate patterns or anti-boilerplate directives.

        These are regex strings, NEVER-use instructions, and docstrings that
        reference boilerplate phrases as examples -- they are NOT output text.
        """
        lines = src.split("\n")
        filtered: list[str] = []
        # Markers that indicate a line is a pattern definition or
        # anti-boilerplate instruction, not generated output.
        skip_markers = (
            "NEVER use",
            "re.compile",
            "_BOILERPLATE",
            "BOILERPLATE_PATTERNS",
            "# boilerplate",
            "# Boilerplate",
            "No hedging",
            "No generic",
            "No filler",
            "generic phrases like",
            "generic language",
            "generic boilerplate",
            "omit the sentence",
            "Every sentence MUST",
            "specific dollar amount",
        )
        for line in lines:
            stripped = line.strip()
            # Skip regex pattern definitions (r"..." strings in lists)
            if stripped.startswith(("r\"", "r'", 'r"')):
                continue
            # Skip lines containing anti-boilerplate directive markers
            if any(marker in stripped for marker in skip_markers):
                continue
            filtered.append(line)
        return "\n".join(filtered)

    def test_findings_neg_no_boilerplate(self) -> None:
        """sect1_findings_neg.py must not contain boilerplate phrases."""
        src = self._read_source("stages/render/sections/sect1_findings_neg.py")
        matches = find_boilerplate_matches(src)
        assert matches == [], (
            f"Boilerplate in sect1_findings_neg.py: {matches}"
        )

    def test_findings_pos_no_boilerplate(self) -> None:
        """sect1_findings_pos.py must not contain boilerplate phrases."""
        src = self._read_source("stages/render/sections/sect1_findings_pos.py")
        matches = find_boilerplate_matches(src)
        assert matches == [], (
            f"Boilerplate in sect1_findings_pos.py: {matches}"
        )

    def test_narrative_generator_no_boilerplate(self) -> None:
        """narrative_generator.py must not contain boilerplate in output text.

        Anti-boilerplate LLM directives are excluded -- they are instructions
        not to USE boilerplate, not boilerplate themselves.
        """
        src = self._read_source("stages/benchmark/narrative_generator.py")
        src = self._strip_pattern_definitions(src)
        matches = find_boilerplate_matches(src)
        assert matches == [], (
            f"Boilerplate in narrative_generator.py: {matches}"
        )

    def test_formatters_no_boilerplate(self) -> None:
        """formatters.py must not contain boilerplate in output text.

        The boilerplate detection patterns in _BOILERPLATE_RX are excluded
        since they are regex definitions, not generated output.
        """
        src = self._read_source("stages/render/formatters.py")
        src = self._strip_pattern_definitions(src)
        matches = find_boilerplate_matches(src)
        assert matches == [], (
            f"Boilerplate in formatters.py: {matches}"
        )
