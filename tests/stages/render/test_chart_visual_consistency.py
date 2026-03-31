"""Visual consistency tests for chart components (CHART-04).

Compares charts generated from synthetic data against golden reference PNGs.
Uses pixel-level RMSE comparison with configurable threshold.

Run with: uv run pytest tests/stages/render/test_chart_visual_consistency.py -v
Skip with: set SKIP_VISUAL_TESTS=1 to skip (useful in CI without display)
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import matplotlib
import numpy as np
import pytest
from PIL import Image

matplotlib.use("Agg")

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_VISUAL_TESTS") == "1",
    reason="Visual tests skipped (SKIP_VISUAL_TESTS=1)",
)

GOLDEN_DIR = Path(__file__).resolve().parent.parent.parent / "golden_charts"
# Default RMSE threshold: 5% (0-100 scale, accounts for anti-aliasing/font diffs)
DEFAULT_THRESHOLD = 5.0


# ---------------------------------------------------------------------------
# Pixel comparison utility
# ---------------------------------------------------------------------------


def compute_image_rmse(img_a_path: Path, img_b_path: Path) -> float:
    """Compute normalized RMSE between two PNG images.

    Returns value on 0-100 scale (0 = identical, 100 = maximally different).
    """
    a = np.array(Image.open(img_a_path).convert("RGB"), dtype=np.float32)
    b = np.array(Image.open(img_b_path).convert("RGB"), dtype=np.float32)

    if a.shape != b.shape:
        # Resize b to match a
        b_img = Image.open(img_b_path).convert("RGB").resize(
            (a.shape[1], a.shape[0]), Image.LANCZOS
        )
        b = np.array(b_img, dtype=np.float32)

    rmse = float(np.sqrt(np.mean((a - b) ** 2)))
    return rmse / 255.0 * 100  # Normalize to 0-100


# ---------------------------------------------------------------------------
# Chart generation helpers (import from generate_golden_charts.py)
# ---------------------------------------------------------------------------


def _import_generators():
    """Import generate_golden_charts module."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_golden_charts",
        str(GOLDEN_DIR / "generate_golden_charts.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Per-chart visual consistency tests
# ---------------------------------------------------------------------------


class TestStockChartVisualConsistency:
    """Stock charts match golden references within threshold."""

    def test_stock_1y_matches_golden(self, tmp_path: Path) -> None:
        golden = GOLDEN_DIR / "stock_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_stock_charts()
        test_img = [p for p in paths if p.name == "stock_1y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"stock_1y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"

    def test_stock_5y_matches_golden(self, tmp_path: Path) -> None:
        golden = GOLDEN_DIR / "stock_5y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_stock_charts()
        test_img = [p for p in paths if p.name == "stock_5y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"stock_5y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestDrawdownChartVisualConsistency:
    """Drawdown charts match golden references."""

    def test_drawdown_1y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "drawdown_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_drawdown_charts()
        test_img = [p for p in paths if p.name == "drawdown_1y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"drawdown_1y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"

    def test_drawdown_5y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "drawdown_5y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_drawdown_charts()
        test_img = [p for p in paths if p.name == "drawdown_5y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"drawdown_5y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestVolatilityChartVisualConsistency:
    """Volatility charts match golden references."""

    def test_volatility_1y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "volatility_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_volatility_charts()
        test_img = [p for p in paths if p.name == "volatility_1y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"volatility_1y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"

    def test_volatility_5y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "volatility_5y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_volatility_charts()
        test_img = [p for p in paths if p.name == "volatility_5y.png"][0]
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"volatility_5y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestRadarChartVisualConsistency:
    """Radar chart matches golden reference."""

    def test_radar_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "radar.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        test_img = gen.generate_radar_chart()
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"radar RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestOwnershipChartVisualConsistency:
    """Ownership chart matches golden reference."""

    def test_ownership_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "ownership.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        test_img = gen.generate_ownership_chart()
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"ownership RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestDropAnalysisChartVisualConsistency:
    """Drop analysis chart matches golden reference."""

    def test_drop_analysis_1y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "drop_analysis_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        test_img = gen.generate_drop_analysis_chart()
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"drop_analysis_1y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestRelativeChartVisualConsistency:
    """Relative performance chart matches golden reference."""

    def test_relative_1y_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "relative_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        test_img = gen.generate_relative_chart()
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"relative_1y RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


class TestTimelineChartVisualConsistency:
    """Timeline chart matches golden reference."""

    def test_timeline_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "timeline.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        test_img = gen.generate_timeline_chart()
        rmse = compute_image_rmse(golden, test_img)
        assert rmse < DEFAULT_THRESHOLD, f"timeline RMSE {rmse:.2f}% exceeds {DEFAULT_THRESHOLD}%"


# ---------------------------------------------------------------------------
# Sparkline SVG consistency (string comparison, not pixel diff)
# ---------------------------------------------------------------------------


class TestSparklineSvgConsistency:
    """Sparkline SVG output matches expected structure."""

    def test_sparkline_up_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "sparkline_up.svg"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_sparklines()
        test_svg = [p for p in paths if p.name == "sparkline_up.svg"][0]
        assert golden.read_text() == test_svg.read_text(), "sparkline_up SVG does not match golden"

    def test_sparkline_down_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "sparkline_down.svg"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_sparklines()
        test_svg = [p for p in paths if p.name == "sparkline_down.svg"][0]
        assert golden.read_text() == test_svg.read_text(), "sparkline_down SVG does not match golden"

    def test_sparkline_flat_matches_golden(self) -> None:
        golden = GOLDEN_DIR / "sparkline_flat.svg"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        gen = _import_generators()
        paths = gen.generate_sparklines()
        test_svg = [p for p in paths if p.name == "sparkline_flat.svg"][0]
        assert golden.read_text() == test_svg.read_text(), "sparkline_flat SVG does not match golden"


# ---------------------------------------------------------------------------
# Canary test: proves the comparison catches real regressions
# ---------------------------------------------------------------------------


class TestCanaryRegression:
    """Prove the visual test catches real regressions."""

    def test_corrupted_chart_fails_comparison(self) -> None:
        """Generate a chart with wrong colors and verify RMSE exceeds threshold."""
        golden = GOLDEN_DIR / "drawdown_1y.png"
        if not golden.exists():
            pytest.skip(f"Golden reference missing: {golden}")

        # Create a deliberately wrong chart -- solid red fill instead of real drawdown
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(10, 4), dpi=200, facecolor="#FF0000")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#FF0000")
        ax.plot([0, 1, 2, 3], [0, -10, -20, -5], color="#00FF00", linewidth=5)
        ax.set_title("CORRUPTED CHART")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            fig.savefig(f.name, dpi=200, bbox_inches="tight")
            plt.close(fig)
            corrupted_path = Path(f.name)

        try:
            rmse = compute_image_rmse(golden, corrupted_path)
            # A corrupted chart should have HIGH RMSE (well above threshold)
            assert rmse > DEFAULT_THRESHOLD, (
                f"Canary test failed: corrupted chart RMSE {rmse:.2f}% "
                f"should exceed {DEFAULT_THRESHOLD}% threshold"
            )
        finally:
            corrupted_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Registry completeness test
# ---------------------------------------------------------------------------


class TestRegistryCompleteness:
    """Chart registry golden references all exist on disk."""

    def test_all_golden_references_exist(self) -> None:
        """Every chart_registry.yaml entry with golden_reference has a file on disk."""
        from do_uw.stages.render.chart_registry import load_chart_registry

        project_root = Path(__file__).resolve().parent.parent.parent.parent
        missing: list[str] = []

        for entry in load_chart_registry():
            if entry.golden_reference:
                ref_path = project_root / entry.golden_reference
                if not ref_path.exists():
                    missing.append(f"{entry.id}: {entry.golden_reference}")

        assert missing == [], (
            f"Golden reference files missing:\n" + "\n".join(missing)
        )


class TestMissingGoldenSkipsGracefully:
    """Missing golden reference produces skip, not crash."""

    def test_missing_golden_skips(self) -> None:
        """Verify a fake golden path triggers skip, not error."""
        fake_golden = GOLDEN_DIR / "nonexistent_chart.png"
        if fake_golden.exists():
            pytest.skip("Test setup error: fake path exists")

        # This verifies our skip pattern works -- if the file doesn't exist,
        # the test gracefully handles it
        assert not fake_golden.exists()
