"""Post-pipeline automated health summary with anomaly detection.

Computes signal counts (evaluated, TRIGGERED, CLEAR, SKIPPED, INFO),
groups by signal prefix section, and runs heuristic anomaly rules to
flag suspicious patterns.

Called after every `do-uw analyze` run, alongside the existing QA report.
Provides Rich-formatted CLI output only (not in HTML worksheet).
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anomaly detection thresholds (module-level constants per CLAUDE.md)
# ---------------------------------------------------------------------------

MAX_SKIPPED_THRESHOLD = 45
"""Maximum number of SKIPPED signals before warning. Consistent with
test_brain_contract.py MAX_ALLOWED_SKIPPED."""


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class AnomalyWarning(BaseModel):
    """A single anomaly warning from heuristic detection."""

    level: str = Field(description="WARNING or INFO")
    message: str = Field(description="Short summary of the anomaly")
    detail: str = Field(description="Detailed explanation")


class HealthSummary(BaseModel):
    """Aggregated signal health metrics and anomaly warnings."""

    total_signals: int = Field(default=0, description="Total signals in results")
    evaluated: int = Field(
        default=0, description="Evaluated signals (TRIGGERED + CLEAR + INFO)"
    )
    triggered: int = Field(default=0, description="Signals that hit thresholds")
    clear: int = Field(default=0, description="Signals that passed clean")
    skipped: int = Field(default=0, description="Signals with missing data")
    info: int = Field(default=0, description="Informational signals")
    anomalies: list[AnomalyWarning] = Field(
        default_factory=list, description="Detected anomalies"
    )
    by_section: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Counts by signal prefix section (e.g., BIZ, FIN, GOV)",
    )


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def _get_signal_results_from_state(state: Any) -> dict[str, Any]:
    """Extract signal results from state, supporting both Pydantic and dict.

    Uses the same backward-compat pattern as cli_brain_trace.py:
    checks both signal_results and the legacy check_results key.
    """
    # Handle Pydantic AnalysisState
    if hasattr(state, "analysis"):
        analysis = state.analysis
        if analysis is None:
            return {}
        if hasattr(analysis, "signal_results"):
            results = analysis.signal_results
            if results:
                return results
        # Legacy backward-compat key (Phase 49 rename)
        if hasattr(analysis, "model_dump"):
            dumped = analysis.model_dump()
            for key in ("signal_results", "check_results"):
                if dumped.get(key):
                    return dumped[key]
        return {}

    # Handle dict-based state (e.g., loaded from JSON)
    if isinstance(state, dict):
        analysis = state.get("analysis", {})
        if isinstance(analysis, dict):
            for key in ("signal_results", "check_results"):
                candidate = analysis.get(key)
                if candidate:
                    return candidate
    return {}


def _extract_prefix(signal_id: str) -> str:
    """Extract the top-level prefix from a signal ID.

    Examples:
        'FIN.LIQ.position' -> 'FIN'
        'STOCK.PRICE.single_day_events' -> 'STOCK'
        'GOV.BOARD.independence' -> 'GOV'
    """
    parts = signal_id.split(".")
    return parts[0] if parts else "UNKNOWN"


def compute_health_summary(state: Any) -> HealthSummary:
    """Compute signal health summary from pipeline state.

    Counts signals by status, groups by prefix section, and runs
    heuristic anomaly detection rules.

    Args:
        state: AnalysisState (Pydantic) or dict from state.json.

    Returns:
        HealthSummary with counts and anomaly warnings.
    """
    results = _get_signal_results_from_state(state)

    if not results:
        return HealthSummary(
            anomalies=[
                AnomalyWarning(
                    level="INFO",
                    message="No signal results available",
                    detail="Pipeline may have failed before ANALYZE stage completed.",
                )
            ]
        )

    # Count by status
    triggered = 0
    clear = 0
    skipped = 0
    info = 0

    # Group by section prefix
    sections: dict[str, dict[str, int]] = {}

    for signal_id, result in results.items():
        status = _get_status(result)
        prefix = _extract_prefix(signal_id)

        if prefix not in sections:
            sections[prefix] = {"triggered": 0, "clear": 0, "skipped": 0, "info": 0}

        if status == "TRIGGERED":
            triggered += 1
            sections[prefix]["triggered"] += 1
        elif status == "CLEAR":
            clear += 1
            sections[prefix]["clear"] += 1
        elif status == "SKIPPED":
            skipped += 1
            sections[prefix]["skipped"] += 1
        elif status == "INFO":
            info += 1
            sections[prefix]["info"] += 1

    total = len(results)
    evaluated = triggered + clear + info

    # Run anomaly detection
    anomalies: list[AnomalyWarning] = []

    anomaly = _check_zero_triggered_with_litigation(state, triggered)
    if anomaly is not None:
        anomalies.append(anomaly)

    anomaly = _check_high_skipped(skipped)
    if anomaly is not None:
        anomalies.append(anomaly)

    for prefix, counts in sections.items():
        anomaly = _check_section_all_skipped(prefix, counts)
        if anomaly is not None:
            anomalies.append(anomaly)

    return HealthSummary(
        total_signals=total,
        evaluated=evaluated,
        triggered=triggered,
        clear=clear,
        skipped=skipped,
        info=info,
        anomalies=anomalies,
        by_section=dict(sorted(sections.items())),
    )


def _get_status(result: Any) -> str:
    """Extract status string from a result (dict or Pydantic)."""
    if isinstance(result, dict):
        return str(result.get("status", ""))
    if hasattr(result, "status"):
        return str(result.status)
    return ""


# ---------------------------------------------------------------------------
# Anomaly detection rules (heuristic, NOT ML)
# ---------------------------------------------------------------------------


def _check_zero_triggered_with_litigation(
    state: Any,
    triggered_count: int,
) -> AnomalyWarning | None:
    """Flag when 0 signals triggered but litigation data is present.

    If the company has active securities class actions, derivative suits,
    or SEC enforcement activity but zero signals fired, something may
    be wrong with the evaluation pipeline.
    """
    if triggered_count > 0:
        return None

    # Check for litigation data
    lit_count = _count_litigation_items(state)
    if lit_count == 0:
        return None

    return AnomalyWarning(
        level="WARNING",
        message="0 signals TRIGGERED but litigation data is present",
        detail=(
            f"{lit_count} litigation item(s) found (securities class actions, "
            f"derivative suits, or SEC enforcement) but no signals fired. "
            f"Check data mapping or threshold calibration."
        ),
    )


def _count_litigation_items(state: Any) -> int:
    """Count litigation items from extracted data."""
    count = 0

    # Handle Pydantic AnalysisState
    if hasattr(state, "extracted"):
        extracted = state.extracted
        if extracted is None:
            return 0
        lit = getattr(extracted, "litigation", None)
        if lit is None:
            return 0
        if hasattr(lit, "securities_class_actions"):
            count += len(lit.securities_class_actions)
        if hasattr(lit, "derivative_suits"):
            count += len(lit.derivative_suits)
        if hasattr(lit, "sec_enforcement"):
            enforcement = lit.sec_enforcement
            if hasattr(enforcement, "current_stage"):
                stage = enforcement.current_stage
                stage_val = stage.value if hasattr(stage, "value") else str(stage)
                if stage_val and stage_val != "NONE":
                    count += 1
        return count

    # Handle dict-based state
    if isinstance(state, dict):
        extracted = state.get("extracted", {})
        if isinstance(extracted, dict):
            lit = extracted.get("litigation", {})
            if isinstance(lit, dict):
                count += len(lit.get("securities_class_actions", []))
                count += len(lit.get("derivative_suits", []))
                enforcement = lit.get("sec_enforcement", {})
                if isinstance(enforcement, dict):
                    stage = enforcement.get("current_stage", "NONE")
                    if stage and stage != "NONE":
                        count += 1
    return count


def _check_high_skipped(skipped_count: int) -> AnomalyWarning | None:
    """Flag when SKIPPED count exceeds threshold.

    A high SKIPPED count suggests data acquisition or extraction issues.
    """
    if skipped_count <= MAX_SKIPPED_THRESHOLD:
        return None

    return AnomalyWarning(
        level="WARNING",
        message=f"SKIPPED count ({skipped_count}) exceeds threshold ({MAX_SKIPPED_THRESHOLD})",
        detail=(
            f"{skipped_count} signals skipped due to missing data. "
            f"Threshold is {MAX_SKIPPED_THRESHOLD}. "
            f"Check data acquisition (ACQUIRE stage) or extraction (EXTRACT stage) "
            f"for failures."
        ),
    )


def _check_section_all_skipped(
    prefix: str,
    counts: dict[str, int],
) -> AnomalyWarning | None:
    """Flag when ALL signals in a section are SKIPPED.

    If every signal in a prefix section (e.g., GOV, FIN, LIT) is SKIPPED,
    data for that entire domain was likely unavailable.
    """
    total = sum(counts.values())
    if total == 0:
        return None

    if counts.get("skipped", 0) == total:
        return AnomalyWarning(
            level="WARNING",
            message=f"All {total} signals in {prefix}.* section are SKIPPED",
            detail=(
                f"Every signal in the {prefix} section has status SKIPPED. "
                f"This means no data was available for any {prefix} signal. "
                f"Check whether {prefix}-related data sources were acquired."
            ),
        )
    return None


# ---------------------------------------------------------------------------
# Rich CLI output
# ---------------------------------------------------------------------------


def print_health_summary(health: HealthSummary) -> None:
    """Print health summary as Rich-formatted CLI output.

    Uses Rich Panel and Table for structured display with color coding:
    - green: CLEAR
    - yellow: TRIGGERED
    - red: WARNING anomalies
    - dim: INFO
    """
    console = Console()

    # Main counts table
    counts_table = Table(
        show_header=True,
        header_style="bold",
        padding=(0, 1),
        expand=False,
    )
    counts_table.add_column("Status", width=12)
    counts_table.add_column("Count", width=8, justify="right")

    counts_table.add_row("Evaluated", str(health.evaluated))
    counts_table.add_row(
        "[yellow]TRIGGERED[/yellow]",
        f"[yellow]{health.triggered}[/yellow]",
    )
    counts_table.add_row(
        "[green]CLEAR[/green]",
        f"[green]{health.clear}[/green]",
    )
    counts_table.add_row(
        "[dim]INFO[/dim]",
        f"[dim]{health.info}[/dim]",
    )
    counts_table.add_row(
        "[red]SKIPPED[/red]" if health.skipped > MAX_SKIPPED_THRESHOLD else "SKIPPED",
        (
            f"[red]{health.skipped}[/red]"
            if health.skipped > MAX_SKIPPED_THRESHOLD
            else str(health.skipped)
        ),
    )

    console.print()
    console.print(
        Panel(counts_table, title="Signal Health Summary", border_style="blue")
    )

    # By-section breakdown
    if health.by_section:
        section_table = Table(
            show_header=True,
            header_style="bold",
            padding=(0, 1),
            expand=False,
        )
        section_table.add_column("Section", width=10)
        section_table.add_column("Triggered", width=10, justify="right")
        section_table.add_column("Clear", width=8, justify="right")
        section_table.add_column("Info", width=8, justify="right")
        section_table.add_column("Skipped", width=8, justify="right")

        for prefix, counts in health.by_section.items():
            t = counts.get("triggered", 0)
            c = counts.get("clear", 0)
            i = counts.get("info", 0)
            s = counts.get("skipped", 0)

            # Highlight all-skipped sections
            all_skipped = s == (t + c + i + s) and s > 0
            prefix_style = "[red]" if all_skipped else ""
            prefix_end = "[/red]" if all_skipped else ""

            section_table.add_row(
                f"{prefix_style}{prefix}{prefix_end}",
                f"[yellow]{t}[/yellow]" if t > 0 else str(t),
                f"[green]{c}[/green]" if c > 0 else str(c),
                f"[dim]{i}[/dim]" if i > 0 else str(i),
                f"[red]{s}[/red]" if all_skipped else str(s),
            )

        console.print(
            Panel(section_table, title="By Section", border_style="dim")
        )

    # Anomalies
    warn_count = sum(1 for a in health.anomalies if a.level == "WARNING")
    info_count = sum(1 for a in health.anomalies if a.level == "INFO")

    if health.anomalies:
        anomaly_lines: list[str] = []
        for anomaly in health.anomalies:
            if anomaly.level == "WARNING":
                anomaly_lines.append(
                    f"  [bold red]WARNING:[/bold red] {anomaly.message}"
                )
                anomaly_lines.append(f"    [dim]{anomaly.detail}[/dim]")
            else:
                anomaly_lines.append(
                    f"  [dim]INFO:[/dim] {anomaly.message}"
                )
                anomaly_lines.append(f"    [dim]{anomaly.detail}[/dim]")

        title = f"Anomalies ({warn_count} warning{'s' if warn_count != 1 else ''}, {info_count} info)"
        border = "red" if warn_count > 0 else "yellow"
        console.print(
            Panel(
                "\n".join(anomaly_lines),
                title=title,
                border_style=border,
            )
        )
    else:
        console.print(
            "[green]  No anomalies detected[/green]"
        )

    console.print()


__all__ = [
    "AnomalyWarning",
    "HealthSummary",
    "compute_health_summary",
    "print_health_summary",
]
