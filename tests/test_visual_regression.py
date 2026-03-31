"""Visual regression testing framework for D&O worksheet HTML output.

Captures per-section screenshots of the HTML worksheet and compares
against golden baselines stored in tests/golden/. Uses Playwright for
browser rendering and Pillow for structural image comparison.

Usage:
    # First run: generate golden baselines
    VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py --update-golden -v

    # Subsequent runs: compare against baselines
    VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Section IDs matching the HTML worksheet structure (v8.0)
# Derived from actual HTML output analysis + template section IDs.
# Playwright will skip sections not present in a given output file.
SECTION_IDS = [
    # Zone 0: Identity & Key Stats
    "identity",
    "key-stats",
    # Zone 1: Executive overview
    "scorecard",
    "executive-brief",
    "executive-summary",
    "red-flags",
    # Zone 2: Company profile & dossier
    "company-profile",
    "section-intelligence-dossier",
    # Zone 3: Analytical sections
    "financial-health",
    "market",
    "governance",
    "litigation",
    "ai-risk",
    "section-alternative-data",
    # Zone 4: Scoring & forward-looking
    "scoring",
    "pattern-firing",
    "section-forward-looking",
    "adversarial-critique",
    # Zone 5: Appendices
    "meeting-prep",
    "coverage",
    "decision-record",
    "signal-audit",
    "data-audit",
    "sources",
    "qa-audit",
]

GOLDEN_DIR = Path(__file__).parent / "golden"
# Percentage threshold for pixel diff (0.0 - 1.0). Diffs above this fail.
DIFF_THRESHOLD = 0.10  # 10% tolerance for data changes


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --update-golden CLI flag."""
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Save current screenshots as new golden baselines",
    )


@pytest.fixture()
def update_golden(request: pytest.FixtureRequest) -> bool:
    """Whether to update golden baselines instead of comparing."""
    return bool(request.config.getoption("--update-golden"))


def _find_html_output() -> Path | None:
    """Find the most recent HTML worksheet output."""
    output_root = Path(__file__).parent.parent / "output"
    if not output_root.exists():
        return None
    # Find most recent output directory
    dirs = sorted(output_root.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
    for d in dirs:
        html_files = list(d.glob("*_worksheet.html"))
        if html_files:
            return html_files[0]
    return None


def _compute_pixel_diff(img_a_path: Path, img_b_path: Path) -> float:
    """Compute pixel difference ratio between two images.

    Returns float between 0.0 (identical) and 1.0 (completely different).
    Images are resized to the same dimensions before comparison.
    """
    from PIL import Image
    import numpy as np

    img_a = Image.open(img_a_path).convert("RGB")
    img_b = Image.open(img_b_path).convert("RGB")

    # Resize to common dimensions (use golden as reference)
    if img_a.size != img_b.size:
        img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)

    arr_a = np.array(img_a, dtype=np.float32)
    arr_b = np.array(img_b, dtype=np.float32)

    # Per-pixel absolute difference, normalized to [0, 1]
    diff = np.abs(arr_a - arr_b) / 255.0
    # Mean difference across all pixels and channels
    return float(np.mean(diff))


@pytest.mark.skipif(
    not os.environ.get("VISUAL_REGRESSION"),
    reason="Set VISUAL_REGRESSION=1 to run visual regression tests",
)
class TestVisualRegression:
    """Per-section screenshot comparison against golden baselines."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        """Ensure golden directory exists."""
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    @pytest.mark.parametrize("section_id", SECTION_IDS)
    def test_section_screenshot(
        self,
        section_id: str,
        update_golden: bool,
    ) -> None:
        """Capture and compare a section screenshot against golden baseline."""
        html_path = _find_html_output()
        if html_path is None:
            pytest.skip("No HTML output found in output/ directory")

        ticker = html_path.stem.replace("_worksheet", "")
        golden_path = GOLDEN_DIR / f"{ticker}_{section_id}.png"
        screenshot_path = GOLDEN_DIR / f"{ticker}_{section_id}_current.png"

        # Use Playwright to capture section screenshot
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(f"file://{html_path.resolve()}")
            page.wait_for_load_state("networkidle")

            # Find the section element
            section = page.query_selector(f"section#{section_id}")
            if section is None:
                browser.close()
                pytest.skip(f"Section #{section_id} not found in HTML")

            # Scroll to section and capture
            section.scroll_into_view_if_needed()
            section.screenshot(path=str(screenshot_path))
            browser.close()

        if update_golden or not golden_path.exists():
            # Save as new golden baseline
            screenshot_path.rename(golden_path)
            if update_golden:
                pytest.skip(f"Updated golden baseline: {golden_path.name}")
            else:
                pytest.skip(f"Created initial golden baseline: {golden_path.name}")
            return

        # Compare against golden baseline
        diff_ratio = _compute_pixel_diff(golden_path, screenshot_path)

        # Clean up current screenshot if it passes
        if diff_ratio <= DIFF_THRESHOLD:
            screenshot_path.unlink(missing_ok=True)

        assert diff_ratio <= DIFF_THRESHOLD, (
            f"Visual regression detected for section '{section_id}': "
            f"{diff_ratio:.1%} pixel difference (threshold: {DIFF_THRESHOLD:.0%}). "
            f"Compare: {golden_path} vs {screenshot_path}"
        )


@pytest.mark.skipif(
    not os.environ.get("VISUAL_REGRESSION"),
    reason="Set VISUAL_REGRESSION=1 to run visual regression tests",
)
class TestVisualRegressionFramework:
    """Smoke tests for the visual regression framework itself."""

    def test_golden_dir_exists(self) -> None:
        """Golden directory is present."""
        assert GOLDEN_DIR.exists(), f"Golden directory missing: {GOLDEN_DIR}"

    def test_section_ids_complete(self) -> None:
        """All expected sections are listed (v8.0: 25 sections)."""
        assert len(SECTION_IDS) == 25
        assert "identity" in SECTION_IDS
        assert "scoring" in SECTION_IDS
        assert "coverage" in SECTION_IDS
        # v8.0 additions
        assert "section-intelligence-dossier" in SECTION_IDS
        assert "section-alternative-data" in SECTION_IDS
        assert "section-forward-looking" in SECTION_IDS
        assert "adversarial-critique" in SECTION_IDS
        assert "scorecard" in SECTION_IDS
        assert "pattern-firing" in SECTION_IDS

    def test_diff_threshold_reasonable(self) -> None:
        """Threshold is between 5% and 15%."""
        assert 0.05 <= DIFF_THRESHOLD <= 0.15
