"""Cost report generation for multi-ticker validation runs.

Generates per-company and per-filing-type cost breakdowns from the
ExtractionCache, with Rich table display and JSON serialization.
Provides visibility into where LLM extraction money is spent.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from rich.console import Console
from rich.table import Table

from do_uw.stages.extract.llm.cache import ExtractionCache

logger = logging.getLogger(__name__)


def _empty_str_float_dict() -> dict[str, float]:
    """Return an empty dict[str, float] for dataclass defaults."""
    return {}


def _empty_entry_list() -> list[CostReportEntry]:
    """Return an empty list[CostReportEntry] for dataclass defaults."""
    return []


@dataclass
class CostReportEntry:
    """Cost breakdown for a single company/ticker."""

    ticker: str
    total_cost_usd: float
    duration_seconds: float
    by_filing_type: dict[str, float] = field(
        default_factory=_empty_str_float_dict
    )


@dataclass
class CostReport:
    """Aggregate cost report across all validated companies."""

    entries: list[CostReportEntry] = field(
        default_factory=_empty_entry_list
    )
    grand_total_usd: float = 0.0
    by_filing_type_total: dict[str, float] = field(
        default_factory=_empty_str_float_dict
    )


def _load_ticker_state(
    state_path: Path,
) -> dict[str, Any] | None:
    """Load state.json for a ticker output directory.

    Args:
        state_path: Path to state.json file.

    Returns:
        Parsed JSON dict, or None if unavailable.
    """
    if not state_path.exists():
        return None
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
        result: dict[str, Any] = raw
        return result
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load state %s: %s", state_path, exc)
        return None


def _extract_accessions(
    state: dict[str, Any],
) -> list[str]:
    """Extract accession numbers from state data.

    Looks in acquired_data.filing_documents for accession numbers,
    falling back to filing_metadata if available.

    Args:
        state: Parsed state.json dict.

    Returns:
        List of accession number strings.
    """
    accessions: list[str] = []

    # Try acquired_data.filing_documents path
    acquired: Any = state.get("acquired_data", {})
    if isinstance(acquired, dict):
        acquired_dict = cast(dict[str, Any], acquired)
        filings: Any = acquired_dict.get("filing_documents", {})
        if isinstance(filings, dict):
            filings_dict = cast(dict[str, Any], filings)
            for accession in filings_dict:
                if accession:
                    accessions.append(accession)

        # Also check filing_metadata for accession numbers
        if not accessions:
            metadata: Any = acquired_dict.get(
                "filing_metadata", []
            )
            if isinstance(metadata, list):
                for entry in cast(list[Any], metadata):
                    if isinstance(entry, dict):
                        entry_dict = cast(dict[str, Any], entry)
                        acc: Any = entry_dict.get(
                            "accession_number", ""
                        )
                        if isinstance(acc, str) and acc:
                            accessions.append(acc)

    return accessions


def generate_cost_report(
    output_dir: Path,
    cache: ExtractionCache | None = None,
) -> CostReport:
    """Generate a cost report from validation output directory.

    Scans output_dir for ticker subdirectories containing state.json,
    extracts accession numbers, and queries ExtractionCache for
    per-filing-type cost breakdowns.

    Args:
        output_dir: Root output directory containing ticker subdirs.
        cache: Optional ExtractionCache instance (creates default if None).

    Returns:
        CostReport with per-company and aggregate cost data.
    """
    if cache is None:
        cache = ExtractionCache()

    entries: list[CostReportEntry] = []
    grand_total = 0.0
    agg_by_type: dict[str, float] = {}

    if not output_dir.exists():
        return CostReport()

    # Scan for ticker subdirectories
    for ticker_dir in sorted(output_dir.iterdir()):
        if not ticker_dir.is_dir():
            continue
        # Skip hidden directories and non-ticker entries
        if ticker_dir.name.startswith("."):
            continue

        state_path = ticker_dir / "state.json"
        state = _load_ticker_state(state_path)
        if state is None:
            continue

        ticker = ticker_dir.name.upper()
        accessions = _extract_accessions(state)
        total_cost = cache.get_company_cost(accessions)
        by_type = cache.get_costs_by_filing_type(accessions)

        # Try to get duration from state or checkpoint
        duration = 0.0
        meta: Any = state.get("metadata", {})
        if isinstance(meta, dict):
            meta_dict = cast(dict[str, Any], meta)
            dur_val: Any = meta_dict.get("duration_seconds", 0.0)
            duration = float(dur_val)

        entry = CostReportEntry(
            ticker=ticker,
            total_cost_usd=round(total_cost, 4),
            duration_seconds=round(duration, 1),
            by_filing_type=by_type,
        )
        entries.append(entry)
        grand_total += total_cost

        # Accumulate filing type totals
        for ft, cost in by_type.items():
            agg_by_type[ft] = agg_by_type.get(ft, 0.0) + cost

    return CostReport(
        entries=entries,
        grand_total_usd=round(grand_total, 4),
        by_filing_type_total={
            k: round(v, 4) for k, v in sorted(agg_by_type.items())
        },
    )


def print_cost_report(report: CostReport) -> None:
    """Display a cost report as a Rich console table.

    Shows per-company breakdown with filing type columns and
    a totals footer row.

    Args:
        report: CostReport to display.
    """
    console = Console()

    # Collect all unique filing types across entries
    all_types: set[str] = set()
    for entry in report.entries:
        all_types.update(entry.by_filing_type.keys())
    sorted_types = sorted(all_types)

    table = Table(
        title="Angry Dolphin Cost Report",
        show_header=True,
        header_style="bold",
        show_footer=True,
    )
    table.add_column("#", width=4, justify="right", footer="")
    table.add_column(
        "Ticker", min_width=8, footer="[bold]TOTAL[/bold]"
    )
    table.add_column(
        "Duration",
        width=10,
        justify="right",
        footer="",
    )
    table.add_column(
        "Total Cost",
        width=12,
        justify="right",
        footer=f"[bold]${report.grand_total_usd:.4f}[/bold]",
    )

    # Add columns for each filing type
    for ft in sorted_types:
        ft_total = report.by_filing_type_total.get(ft, 0.0)
        table.add_column(
            ft,
            width=10,
            justify="right",
            footer=f"${ft_total:.4f}",
        )

    for idx, entry in enumerate(report.entries, 1):
        row: list[str] = [
            str(idx),
            entry.ticker,
            f"{entry.duration_seconds:.1f}s",
            f"${entry.total_cost_usd:.4f}",
        ]
        for ft in sorted_types:
            cost = entry.by_filing_type.get(ft, 0.0)
            row.append(f"${cost:.4f}" if cost > 0 else "-")
        table.add_row(*row)

    console.print(table)

    console.print(
        f"\n[bold]Grand Total:[/bold] "
        f"${report.grand_total_usd:.4f} USD "
        f"across {len(report.entries)} companies"
    )


def save_cost_report(report: CostReport, path: Path) -> None:
    """Serialize a cost report to a JSON file.

    Args:
        report: CostReport to serialize.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    path.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def load_cost_report(path: Path) -> CostReport:
    """Deserialize a cost report from a JSON file.

    Args:
        path: Path to the JSON cost report file.

    Returns:
        Deserialized CostReport.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        msg = f"Cost report file not found: {path}"
        raise FileNotFoundError(msg)

    raw: dict[str, Any] = json.loads(
        path.read_text(encoding="utf-8")
    )
    raw_entries: list[dict[str, Any]] = raw.get("entries", [])
    entries = [CostReportEntry(**entry) for entry in raw_entries]
    grand_total: float = raw.get("grand_total_usd", 0.0)
    by_type: dict[str, float] = raw.get("by_filing_type_total", {})
    return CostReport(
        entries=entries,
        grand_total_usd=grand_total,
        by_filing_type_total=by_type,
    )
