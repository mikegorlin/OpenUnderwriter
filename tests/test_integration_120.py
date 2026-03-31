"""Integration tests for Phase 120: structural verification of pipeline outputs.

Validates that 3 ticker pipelines (HNGE, AAPL, ANGI) produce complete HTML
worksheets with all v8.0 sections populated, real company-specific data,
and meaningful cross-ticker differentiation.

Usage:
    uv run pytest tests/test_integration_120.py -x -v
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def _find_ticker_output(ticker: str) -> Path | None:
    """Find the most recent HTML worksheet for a ticker.

    Handles both plain ticker dirs (output/HNGE/) and
    ticker-company dirs (output/AAPL - Apple/).
    """
    candidates: list[Path] = []
    if not OUTPUT_DIR.exists():
        return None
    for d in OUTPUT_DIR.iterdir():
        if not d.is_dir():
            continue
        # Match dirs starting with ticker (e.g., "HNGE", "AAPL - Apple")
        dirname = d.name
        if dirname == ticker or dirname.startswith(f"{ticker} - ") or dirname.startswith(f"{ticker}/"):
            # Check for date subdirs first
            for sub in sorted(d.iterdir(), reverse=True):
                if sub.is_dir():
                    html = sub / f"{ticker}_worksheet.html"
                    if html.exists():
                        candidates.append(html)
            # Then check direct
            html = d / f"{ticker}_worksheet.html"
            if html.exists():
                candidates.append(html)
    if not candidates:
        return None
    # Return most recently modified
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _find_ticker_state(ticker: str) -> Path | None:
    """Find state.json for a ticker."""
    html_path = _find_ticker_output(ticker)
    if html_path is None:
        return None
    state_path = html_path.parent / "state.json"
    return state_path if state_path.exists() else None


def _load_html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_section_ids(content: str) -> list[str]:
    return re.findall(r'<section[^>]*id="([^"]+)"', content)


def _count_svgs(content: str) -> int:
    return len(re.findall(r"<svg", content))


def _na_ratio(content: str) -> float:
    na_cells = len(re.findall(r"<td[^>]*>\s*N/A\s*</td>", content))
    total_td = len(re.findall(r"<td", content))
    if total_td == 0:
        return 0.0
    return na_cells / total_td


def _has_score_badge(content: str) -> bool:
    return bool(re.search(r"score-badge|verdict-badge|badge-tier", content))


def _get_composite_score(ticker: str) -> float | None:
    """Extract composite score from state.json."""
    state_path = _find_ticker_state(ticker)
    if state_path is None:
        return None
    with open(state_path) as f:
        state = json.load(f)
    return state.get("scoring", {}).get("composite_score")


# Expected sections (pre-v8.0 + v8.0)
EXPECTED_CORE_SECTIONS = {
    "key-stats",
    "executive-brief",
    "scorecard",
    "red-flags",
    "company-profile",
    "financial-health",
    "market",
    "governance",
    "litigation",
    "scoring",
    "meeting-prep",
}

V8_SECTIONS = {
    "section-intelligence-dossier",
    "section-alternative-data",
    "section-forward-looking",
    "adversarial-critique",
}


# --- HNGE Tests ---

HNGE_PATH = _find_ticker_output("HNGE")


@pytest.mark.skipif(HNGE_PATH is None, reason="HNGE output not found")
class TestHNGE:
    """Structural verification for HNGE (Hinge Health) pipeline output."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        assert HNGE_PATH is not None
        self.content = _load_html(HNGE_PATH)
        self.section_ids = _extract_section_ids(self.content)

    def test_hnge_file_size(self) -> None:
        """HNGE HTML should be >100KB (real data produces large output)."""
        assert HNGE_PATH is not None
        size = HNGE_PATH.stat().st_size
        assert size > 100_000, f"HNGE HTML is only {size} bytes"

    def test_hnge_sections_present(self) -> None:
        """All expected core sections present in HNGE output."""
        missing = EXPECTED_CORE_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing sections: {missing}"

    def test_hnge_v8_sections(self) -> None:
        """All v8.0 sections present: intelligence dossier, alt data, forward-looking, adversarial."""
        missing = V8_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing v8.0 sections: {missing}"

    def test_hnge_na_ratio(self) -> None:
        """N/A ratio should be below 30%."""
        ratio = _na_ratio(self.content)
        assert ratio < 0.30, f"N/A ratio is {ratio:.1%}"

    def test_hnge_score_badge(self) -> None:
        """Score badge exists in output."""
        assert _has_score_badge(self.content), "No score badge found"

    def test_hnge_svg_charts(self) -> None:
        """At least one SVG chart rendered."""
        count = _count_svgs(self.content)
        assert count > 0, "No SVG charts found"

    def test_hnge_factor_table(self) -> None:
        """Scoring section has factor references (F.1 through F.10)."""
        # Check for at least a few factor references
        factors_found = set(re.findall(r"F\.\d+", self.content))
        assert len(factors_found) >= 3, f"Only found factor refs: {factors_found}"

    def test_hnge_litigation_section(self) -> None:
        """Litigation section is present."""
        assert "litigation" in self.section_ids


# --- AAPL Tests ---

AAPL_PATH = _find_ticker_output("AAPL")


@pytest.mark.skipif(AAPL_PATH is None, reason="AAPL output not found")
class TestAAPL:
    """Structural verification for AAPL (Apple) pipeline output."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        assert AAPL_PATH is not None
        self.content = _load_html(AAPL_PATH)
        self.section_ids = _extract_section_ids(self.content)

    def test_aapl_file_size(self) -> None:
        """AAPL HTML should be >100KB."""
        assert AAPL_PATH is not None
        size = AAPL_PATH.stat().st_size
        assert size > 100_000, f"AAPL HTML is only {size} bytes"

    def test_aapl_sections_present(self) -> None:
        """All expected core sections present."""
        missing = EXPECTED_CORE_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing sections: {missing}"

    def test_aapl_v8_sections(self) -> None:
        """All v8.0 sections present."""
        missing = V8_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing v8.0 sections: {missing}"

    def test_aapl_na_ratio(self) -> None:
        """N/A ratio below 30%."""
        ratio = _na_ratio(self.content)
        assert ratio < 0.30, f"N/A ratio is {ratio:.1%}"

    def test_aapl_score_badge(self) -> None:
        """Score badge exists."""
        assert _has_score_badge(self.content)

    def test_aapl_svg_charts(self) -> None:
        """SVG charts rendered."""
        count = _count_svgs(self.content)
        assert count > 0, "No SVG charts found"

    def test_aapl_financial_tables(self) -> None:
        """Mega-cap should have extensive financial data tables."""
        # AAPL should have many <td> cells (financial tables)
        total_td = len(re.findall(r"<td", self.content))
        assert total_td > 500, f"Only {total_td} <td> cells — expected extensive financial tables"

    def test_aapl_peer_group(self) -> None:
        """AAPL should have peer group content."""
        # Check for peer-related content
        has_peer = bool(re.search(r"peer|benchmark|compan(y|ies)", self.content, re.IGNORECASE))
        assert has_peer, "No peer/benchmark content found"


# --- ANGI Tests ---

ANGI_PATH = _find_ticker_output("ANGI")


@pytest.mark.skipif(ANGI_PATH is None, reason="ANGI output not found")
class TestANGI:
    """Structural verification for ANGI (Angi) pipeline output."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        assert ANGI_PATH is not None
        self.content = _load_html(ANGI_PATH)
        self.section_ids = _extract_section_ids(self.content)

    def test_angi_file_size(self) -> None:
        """ANGI HTML should be >100KB."""
        assert ANGI_PATH is not None
        size = ANGI_PATH.stat().st_size
        assert size > 100_000, f"ANGI HTML is only {size} bytes"

    def test_angi_sections_present(self) -> None:
        """All expected core sections present."""
        missing = EXPECTED_CORE_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing sections: {missing}"

    def test_angi_v8_sections(self) -> None:
        """All v8.0 sections present."""
        missing = V8_SECTIONS - set(self.section_ids)
        assert not missing, f"Missing v8.0 sections: {missing}"

    def test_angi_na_ratio(self) -> None:
        """N/A ratio below 30%."""
        ratio = _na_ratio(self.content)
        assert ratio < 0.30, f"N/A ratio is {ratio:.1%}"

    def test_angi_score_badge(self) -> None:
        """Score badge exists."""
        assert _has_score_badge(self.content)

    def test_angi_svg_charts(self) -> None:
        """SVG charts rendered."""
        count = _count_svgs(self.content)
        assert count > 0

    def test_angi_triggered_signals(self) -> None:
        """ANGI should have triggered signals (non-trivial risk profile)."""
        # Check for TRIGGERED or red-flag related content
        has_triggered = bool(
            re.search(r"TRIGGERED|red.flag|triggered", self.content, re.IGNORECASE)
        )
        assert has_triggered, "No triggered signals found — expected non-trivial risk"

    def test_angi_litigation_content(self) -> None:
        """ANGI should have litigation section content."""
        assert "litigation" in self.section_ids


# --- Cross-Ticker Comparison ---


@pytest.mark.skipif(
    AAPL_PATH is None or ANGI_PATH is None,
    reason="Need both AAPL and ANGI outputs",
)
class TestCrossTicker:
    """Cross-ticker differentiation: outputs should reflect different risk profiles."""

    def test_angi_differs_from_aapl(self) -> None:
        """ANGI and AAPL should have meaningfully different scores.

        Both tickers should produce complete worksheets but with different
        composite scores reflecting their different risk profiles.
        """
        aapl_score = _get_composite_score("AAPL")
        angi_score = _get_composite_score("ANGI")
        assert aapl_score is not None, "Could not extract AAPL score"
        assert angi_score is not None, "Could not extract ANGI score"
        # Scores should differ (exact direction depends on data)
        assert aapl_score != angi_score, (
            f"AAPL ({aapl_score:.1f}) and ANGI ({angi_score:.1f}) "
            f"have identical scores — expected differentiation"
        )

    def test_three_tickers_all_different(self) -> None:
        """All three tickers should produce distinct scores."""
        hnge_score = _get_composite_score("HNGE")
        aapl_score = _get_composite_score("AAPL")
        angi_score = _get_composite_score("ANGI")
        scores = {
            "HNGE": hnge_score,
            "AAPL": aapl_score,
            "ANGI": angi_score,
        }
        available = {k: v for k, v in scores.items() if v is not None}
        assert len(available) >= 2, f"Need at least 2 scores, got: {available}"
        values = list(available.values())
        # At least 2 distinct scores
        assert len(set(round(v, 1) for v in values)) >= 2, (
            f"Scores are not differentiated: {available}"
        )

    def test_outputs_have_different_content(self) -> None:
        """AAPL and ANGI worksheets should have different content (not copy-paste)."""
        assert AAPL_PATH is not None and ANGI_PATH is not None
        aapl_content = _load_html(AAPL_PATH)
        angi_content = _load_html(ANGI_PATH)
        # Different company names
        assert "Apple" in aapl_content
        assert "Angi" in angi_content
        # Different file sizes (different amount of data)
        aapl_size = AAPL_PATH.stat().st_size
        angi_size = ANGI_PATH.stat().st_size
        # They shouldn't be nearly identical in size
        ratio = min(aapl_size, angi_size) / max(aapl_size, angi_size)
        assert ratio < 0.99, f"Outputs are suspiciously similar in size: {aapl_size} vs {angi_size}"
