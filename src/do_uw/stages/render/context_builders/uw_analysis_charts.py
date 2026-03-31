"""Stock chart and earnings beat/miss builders for the UW Analysis.

The combo chart and 5yr strip delegate to generate_all_charts.py.
Earnings beat circles remain as inline SVG here.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState

try:
    import matplotlib.dates as mdates  # noqa: F401
except ImportError:
    mdates = None  # type: ignore[assignment]
from do_uw.stages.render.formatters import safe_float

# Ensure scripts/ is importable for chart functions
# uw_analysis_charts.py → context_builders/ → render/ → stages/ → do_uw/ → src/ → project_root/
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[5] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

logger = logging.getLogger(__name__)


def build_earnings_beat_circles(state: AnalysisState) -> tuple[str, str]:
    """Build SVG row of up to 8 compact earnings beat/miss circles + summary.

    Returns (svg_html, summary_text) where summary is like "4 of 4 beats".
    Green = beat, red = miss, gray = not yet reported.
    Oldest on left, newest on right.  Circles are 8px diameter, 2px gap.
    """
    try:
        md = state.acquired_data.market_data if state.acquired_data else None
        if not md:
            return ("", "")
        ed = md.get("earnings_dates", {}) if isinstance(md, dict) else getattr(md, "earnings_dates", {}) or {}
        if not isinstance(ed, dict):
            return ("", "")
        reported, estimates = ed.get("Reported EPS", []), ed.get("EPS Estimate", [])
        surprises, dates = ed.get("Surprise(%)", []), ed.get("Earnings Date", [])
        if not estimates:
            return ("", "")
        n = min(8, len(estimates))
        items = []
        for i in range(n):
            items.append({
                "rep": reported[i] if i < len(reported) else None,
                "surp": surprises[i] if i < len(surprises) else None,
                "date": dates[i] if i < len(dates) else None,
            })
        items.reverse()
        # Compact circles: r=4 (8px diameter), 10px spacing (8px circle + 2px gap)
        spacing = 10
        r = 4
        cy = r
        w = n * spacing - 2  # subtract last gap
        h = r * 2
        p = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
        beats, misses, reported_count = 0, 0, 0
        for idx, it in enumerate(items):
            cx = idx * spacing + r
            if it["rep"] is None:
                p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#D1D5DB" opacity="0.5"/>')
            else:
                reported_count += 1
                s = safe_float(it["surp"], 0.0)
                if s >= 0:
                    fill = "#16A34A"
                    beats += 1
                else:
                    fill = "#DC2626"
                    misses += 1
                p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')
        p.append("</svg>")
        # Build summary text
        if reported_count > 0:
            if beats >= misses:
                summary = f"{beats} of {reported_count} quarters beat"
            else:
                summary = f"{misses} of {reported_count} quarters negative"
        else:
            summary = ""
        return ("".join(p), summary)
    except Exception:
        logger.debug("Failed to build earnings beat circles", exc_info=True)
        return ("", "")


def _quarter_label(dt: Any) -> str:
    """Convert date to quarter label like 'Q3 24'."""
    if dt is None:
        return ""
    try:
        if isinstance(dt, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    d = datetime.strptime(dt.split(" ")[0], fmt)
                    return f"Q{(d.month - 1) // 3 + 1} {d.strftime('%y')}"
                except ValueError:
                    continue
        if hasattr(dt, "month") and hasattr(dt, "year"):
            return f"Q{(dt.month - 1) // 3 + 1} {str(dt.year)[-2:]}"
        if isinstance(dt, (int, float)):
            d = datetime.fromtimestamp(dt)
            return f"Q{(d.month - 1) // 3 + 1} {d.strftime('%y')}"
    except Exception:
        pass
    return ""


def _overlay_class_periods(fig: Any, state: AnalysisState) -> None:
    """Shade active SCA class periods on the price chart (first axes).

    Draws a semi-transparent purple band over the class period with a label.
    This shows the underwriter exactly which price movement is already
    covered by the active claim — reducing go-forward liability exposure.
    """
    try:
        if not state.acquired_data or not state.acquired_data.litigation_data:
            return
        lit_data = state.acquired_data.litigation_data
        cases: list[dict[str, Any]] = []
        if isinstance(lit_data, dict):
            cases = lit_data.get("supabase_cases", [])
        else:
            cases = getattr(lit_data, "supabase_cases", []) or []

        active_statuses = {"ACTIVE", "PENDING", "OPEN", "FILED", "ONGOING"}
        active_cases = [
            c for c in cases
            if isinstance(c, dict)
            and str(c.get("case_status", "")).upper() in active_statuses
            and c.get("class_period_start")
            and c.get("class_period_end")
        ]

        if not active_cases:
            return

        ax = fig.axes[0]  # Price panel is always first

        for c in active_cases:
            cp_start = datetime.strptime(str(c["class_period_start"])[:10], "%Y-%m-%d")
            cp_end = datetime.strptime(str(c["class_period_end"])[:10], "%Y-%m-%d")

            ax.axvspan(
                cp_start, cp_end,
                alpha=0.15, color="#7C3AED", zorder=1,
                label=None,
            )
            # Add label at top of shaded region
            mid = cp_start + (cp_end - cp_start) / 2
            ymax = ax.get_ylim()[1]
            ax.text(
                mid, ymax * 0.97,
                f"CLASS PERIOD\n{c['class_period_start']} → {c['class_period_end']}",
                ha="center", va="top",
                fontsize=7, fontweight="bold", color="#7C3AED",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white",
                      "edgecolor": "#7C3AED", "alpha": 0.9},
                zorder=10,
            )
    except Exception:
        logger.warning("Failed to overlay class periods", exc_info=True)


def build_stock_chart_svg(state: AnalysisState) -> str:
    """Build the Navy Professional combo chart (Basic D&O Chart 1) as <img> tag.

    Uses the same chart_1_combo function from generate_all_charts.py.
    Three panels: price + DDL + volume with all overlays.
    """
    try:
        import base64
        import io
        import sys
        from pathlib import Path

        # Import chart_1_combo from the scripts module
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        scripts_dir = project_root / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        from generate_all_charts import chart_1_combo

        md = state.acquired_data.market_data if state.acquired_data else None
        if not md:
            return ""
        if not isinstance(md, dict):
            md = md.model_dump() if hasattr(md, "model_dump") else {}

        # Set global ticker for the chart function
        import generate_all_charts
        generate_all_charts.ticker = state.ticker or "Company"

        state_dict = state.model_dump() if hasattr(state, "model_dump") else {}
        fig, err = chart_1_combo(state_dict, md)
        if fig is None:
            logger.warning("Combo chart returned None: %s", err)
            return ""

        # Overlay active claim class periods as shaded regions
        _overlay_class_periods(fig, state)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.15, facecolor="white")
        import matplotlib.pyplot as plt
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;border-radius:12px;border:1px solid #E5E7EB;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.08);" '
            f'alt="D&O Combo Chart"/>'
        )
    except Exception:
        logger.warning("Failed to build combo chart", exc_info=True)
        return ""


def build_stock_chart_5y(state: AnalysisState) -> str:
    """Build compact 5-year Bloomberg Orange strip chart as <img> tag."""
    try:
        import base64
        import io
        import sys
        from pathlib import Path

        project_root = Path(__file__).resolve().parent.parent.parent.parent
        scripts_dir = project_root / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        from generate_all_charts import chart_3_perf_5y

        md = state.acquired_data.market_data if state.acquired_data else None
        if not md:
            return ""
        if not isinstance(md, dict):
            md = md.model_dump() if hasattr(md, "model_dump") else {}

        import generate_all_charts
        generate_all_charts.ticker = state.ticker or "Company"

        state_dict = state.model_dump() if hasattr(state, "model_dump") else {}
        fig, err = chart_3_perf_5y(state_dict, md)
        if fig is None:
            return ""

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1, facecolor="#1A1A2E")
        import matplotlib.pyplot as plt
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;border-radius:8px;'
            f'box-shadow:0 2px 6px rgba(0,0,0,0.15);" '
            f'alt="5-Year Performance"/>'
        )
    except Exception:
        logger.warning("Failed to build 5-year chart", exc_info=True)
        return ""
