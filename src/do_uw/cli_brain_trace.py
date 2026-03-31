"""Brain trace, trace-chain, and render-audit CLI commands. Registered via cli_brain.py."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from do_uw.cli_brain import brain_app

logger = logging.getLogger(__name__)
console = Console()

# Lazy-cached group name map from manifest
_CACHED_GROUP_NAMES: dict[str, str] | None = None


def _get_group_name_map() -> dict[str, str]:
    """Build {group_id: group_name} from manifest groups, caching on first call."""
    global _CACHED_GROUP_NAMES
    if _CACHED_GROUP_NAMES is None:
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        _CACHED_GROUP_NAMES = {}
        for section in manifest.sections:
            for group in section.groups:
                _CACHED_GROUP_NAMES[group.id] = group.name
    return _CACHED_GROUP_NAMES

# Prefix -> mapper function name mapping (for blueprint route display)
_PREFIX_TO_MAPPER: dict[str, str] = {
    "BIZ": "_map_company_fields",
    "STOCK": "_map_market_fields",
    "STOCK.OWN": "_gov_fields (ownership)",
    "STOCK.LIT": "_lit_fields (stock litigation)",
    "FIN": "_map_financial_fields",
    "GOV": "_gov_fields",
    "LIT": "_lit_fields",
    "FWRD": "map_fwrd_check",
    "EXEC": "map_phase26_check (executive)",
    "NLP": "map_phase26_check (NLP)",
}

# Required data key -> extractor name
_SOURCE_TO_EXTRACTOR: dict[str, str] = {
    "SEC_10K": "sec_10k_extractor",
    "SEC_10Q": "sec_10q_extractor",
    "SEC_DEF14A": "def14a_extractor (LLM)",
    "SEC_8K": "sec_8k_extractor",
    "MARKET_DATA": "yfinance",
    "INSIDER_DATA": "insider_txn_extractor",
    "SCA_DATA": "stanford_scac",
    "ENFORCEMENT_DATA": "sec_enforcement",
    "WEB": "brave_search",
    "COURTLISTENER": "courtlistener_api",
}

# Stage emoji icons
_STAGE_ICONS = {
    "define": "\U0001f4cb",      # clipboard
    "extract": "\U0001f4e5",     # inbox tray
    "map": "\U0001f500",         # shuffle
    "evaluate": "\u2696\ufe0f",  # scales
    "render": "\U0001f5a8\ufe0f",  # printer
}

# Status emoji
_STATUS_EMOJI = {
    "CLEAR": "\u2705",       # green check
    "INFO": "\u2705",        # green check
    "TRIGGERED": "\u26a0\ufe0f",  # warning
    "SKIPPED": "\u23ed\ufe0f",    # skip
    "UNKNOWN": "\u2753",     # question mark
}

# Threshold level colors
_THRESHOLD_COLORS = {
    "red": "\U0001f534",     # red circle
    "yellow": "\U0001f7e1",  # yellow circle
    "green": "\U0001f7e2",   # green circle
    "clear": "\U0001f7e2",   # green circle
}


def _find_signal_yaml(signal_id: str) -> dict[str, Any] | None:
    """Find a signal definition by ID from brain/signals/**/*.yaml."""
    import yaml

    signals_dir = Path(__file__).parent / "brain" / "signals"
    if not signals_dir.exists():
        return None

    for yaml_path in sorted(signals_dir.rglob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        entries: list[dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict) and "signals" in data:
            entries = data["signals"]
        else:
            continue

        for entry in entries:
            if entry.get("id") == signal_id:
                return entry
    return None


def _infer_mapper(signal_id: str) -> str:
    """Infer the mapper function name from signal ID prefix."""
    prefix2 = ".".join(signal_id.split(".")[:2])
    prefix1 = signal_id.split(".")[0]

    if prefix2 in _PREFIX_TO_MAPPER:
        return _PREFIX_TO_MAPPER[prefix2]
    return _PREFIX_TO_MAPPER.get(prefix1, f"map_signal_data ({prefix1})")


def _infer_extractor(signal_def: dict[str, Any]) -> str:
    """Infer the extractor from required_data or data_strategy."""
    ds = signal_def.get("data_strategy", {})
    primary = ds.get("primary_source", "") if isinstance(ds, dict) else ""
    if primary and primary in _SOURCE_TO_EXTRACTOR:
        return _SOURCE_TO_EXTRACTOR[primary]

    required = signal_def.get("required_data", [])
    if required:
        first = required[0] if isinstance(required, list) else str(required)
        return _SOURCE_TO_EXTRACTOR.get(first, f"extractor({first})")

    return "unknown"


def _format_threshold_bar(threshold: dict[str, Any]) -> str:
    """Format threshold levels as a compact colored bar."""
    parts: list[str] = []
    if threshold.get("red"):
        parts.append(f"{_THRESHOLD_COLORS['red']} {threshold['red']}")
    if threshold.get("yellow"):
        parts.append(f"{_THRESHOLD_COLORS['yellow']} {threshold['yellow']}")
    clear_val = threshold.get("clear", threshold.get("triggered", ""))
    if clear_val:
        parts.append(f"{_THRESHOLD_COLORS['green']} {clear_val}")
    return "  ".join(parts) if parts else "N/A"


def _find_most_recent_output(ticker: str = "") -> Path | None:
    """Find the most recent output directory with a state.json."""
    output_root = Path.cwd() / "output"
    if not output_root.exists():
        return None

    candidates: list[tuple[float, Path]] = []

    if ticker:
        for d in output_root.iterdir():
            if not d.is_dir():
                continue
            name = d.name
            if name == ticker or name.startswith(f"{ticker}-"):
                state_file = d / "state.json"
                if state_file.exists():
                    candidates.append((state_file.stat().st_mtime, state_file))
    else:
        for d in output_root.iterdir():
            if not d.is_dir():
                continue
            state_file = d / "state.json"
            if state_file.exists():
                candidates.append((state_file.stat().st_mtime, state_file))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _load_state(state_path: Path) -> dict[str, Any]:
    """Load state.json and return the parsed dict."""
    return json.loads(state_path.read_text(encoding="utf-8"))


def _get_signal_results(state: dict[str, Any]) -> dict[str, Any]:
    """Extract signal results from state, supporting legacy key names."""
    analysis = state.get("analysis", {})
    for key in ("signal_results", "check_results"):
        candidate = analysis.get(key)
        if candidate:
            return candidate
    return {}


def _build_header_panel(
    signal_id: str,
    signal_def: dict[str, Any],
    facet_id: str,
    facet_name: str,
    mode: str,
    run_info: str = "",
) -> Panel:
    """Build the signal header panel."""
    name = signal_def.get("name", "Unknown")
    lifecycle = signal_def.get("lifecycle_state", "ACTIVE")
    work_type = signal_def.get("work_type", "evaluate")

    title_text = Text()
    title_text.append("\U0001f50d ", style="bold")  # magnifying glass
    title_text.append(signal_id, style="bold cyan")
    title_text.append(f"  {name}", style="bold")

    body_parts: list[str] = []
    body_parts.append(f"\U0001f4c1 {facet_id} ({facet_name})")
    body_parts.append(f"\U0001f527 {work_type}  |  {lifecycle}")
    if run_info:
        body_parts.append(f"\U0001f4ca {run_info}")

    body = "\n".join(body_parts)
    subtitle = f"{mode} mode"

    return Panel(
        body,
        title=title_text,
        subtitle=f"[dim]{subtitle}[/dim]",
        border_style="cyan",
        padding=(0, 1),
    )


def _build_blueprint_table(
    signal_id: str, signal_def: dict[str, Any]
) -> Table:
    """Build the pipeline blueprint table."""
    table = Table(
        title="\U0001f5fa\ufe0f  Pipeline Blueprint",
        show_header=True,
        header_style="bold",
        border_style="dim",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Stage", width=14)
    table.add_column("Route", ratio=1)

    threshold = signal_def.get("threshold", {})
    ds = signal_def.get("data_strategy", {})
    field_key = ds.get("field_key", "N/A") if isinstance(ds, dict) else "N/A"
    required = signal_def.get("required_data", [])
    display = signal_def.get("display", {})
    group = signal_def.get("group", "N/A")
    prefix = signal_id.split(".")[0]

    group_id = signal_def.get("group", "")
    group_names = _get_group_name_map()
    section_name = group_names.get(group_id, prefix)

    # 1. Define
    th_type = threshold.get("type", "N/A")
    th_bar = _format_threshold_bar(threshold)
    define_detail = f"{th_type}: {th_bar}\nfield_key: {field_key}"
    table.add_row("1", f"{_STAGE_ICONS['define']} Define", define_detail)

    # 2. Extract
    extractor = _infer_extractor(signal_def)
    sources = ", ".join(required) if isinstance(required, list) else str(required)
    data_locs = signal_def.get("data_locations", {})
    extract_detail = f"{extractor}\nsources: {sources}"
    if data_locs:
        for src, fields in data_locs.items():
            field_list = ", ".join(fields) if isinstance(fields, list) else str(fields)
            extract_detail += f"\n{src}: {field_list}"
    table.add_row("2", f"{_STAGE_ICONS['extract']} Extract", extract_detail)

    # 3. Map
    mapper = _infer_mapper(signal_id)
    map_detail = f"{mapper}\nfield_key: {field_key}"
    table.add_row("3", f"{_STAGE_ICONS['map']} Map", map_detail)

    # 4. Evaluate
    eval_detail = f"threshold: {th_type}"
    table.add_row("4", f"{_STAGE_ICONS['evaluate']} Evaluate", eval_detail)

    # 5. Render
    vf = display.get("value_format", "N/A")
    st = display.get("source_type", "N/A")
    render_detail = f"{section_name} section\ngroup: {group}  |  format: {vf}  |  source: {st}"
    table.add_row("5", f"{_STAGE_ICONS['render']} Render", render_detail)

    return table


def _build_live_table(
    signal_id: str,
    signal_def: dict[str, Any],
    state: dict[str, Any],
) -> Table:
    """Build the pipeline trace table with live data."""
    results = _get_signal_results(state)
    signal_result = results.get(signal_id)

    table = Table(
        title="\U0001f3af  Pipeline Trace",
        show_header=True,
        header_style="bold",
        border_style="dim",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Stage", width=14)
    table.add_column("Status", width=8, justify="center")
    table.add_column("Detail", ratio=1)

    threshold = signal_def.get("threshold", {})
    ds = signal_def.get("data_strategy", {})
    field_key = ds.get("field_key", "N/A") if isinstance(ds, dict) else "N/A"
    display = signal_def.get("display", {})
    group = signal_def.get("group", "N/A")
    prefix = signal_id.split(".")[0]

    group_id = signal_def.get("group", "")
    group_names = _get_group_name_map()
    section_name = group_names.get(group_id, prefix)

    # 1. Define — always OK (signal exists in YAML)
    th_type = threshold.get("type", "N/A")
    th_bar = _format_threshold_bar(threshold)
    define_detail = f"{th_type}: {th_bar}\nfield_key: {field_key}"
    table.add_row("1", f"{_STAGE_ICONS['define']} Define", "\u2705", define_detail)

    if signal_result:
        status = signal_result.get("status", "UNKNOWN")
        status_emoji = _STATUS_EMOJI.get(status, "\u2753")
        data_status = signal_result.get("data_status", "")

        # 2. Extract
        trace_ext = signal_result.get("trace_extraction", "")
        trace_src = signal_result.get("trace_data_source", "")
        extractor = trace_ext or _infer_extractor(signal_def)
        has_data = data_status not in ("DATA_UNAVAILABLE", "NO_DATA", "")
        ext_status = "\u2705" if has_data else "\u274c"
        ext_detail = extractor
        if trace_src:
            ext_detail += f"\n{trace_src}"
        table.add_row(
            "2", f"{_STAGE_ICONS['extract']} Extract", ext_status, ext_detail
        )

        # 3. Map
        source = signal_result.get("source", "")
        mapped_ok = bool(source)
        map_status = "\u2705" if mapped_ok else "\u274c"
        map_detail = source if source else "no mapped value"
        table.add_row(
            "3", f"{_STAGE_ICONS['map']} Map", map_status, map_detail
        )

        # 4. Evaluate
        value = signal_result.get("value")
        threshold_level = signal_result.get("threshold_level", "")
        evidence = signal_result.get("evidence", "")
        eval_detail_parts: list[str] = [f"{status}"]
        if value is not None:
            eval_detail_parts[0] += f" = {value}"
        if threshold_level:
            level_emoji = _THRESHOLD_COLORS.get(threshold_level, "")
            eval_detail_parts.append(f"{level_emoji} {threshold_level}")
        if evidence:
            short_evidence = evidence[:80] + "..." if len(evidence) > 80 else evidence
            eval_detail_parts.append(short_evidence)
        table.add_row(
            "4",
            f"{_STAGE_ICONS['evaluate']} Evaluate",
            status_emoji,
            "\n".join(eval_detail_parts),
        )

        # 5. Render
        vf = display.get("value_format", "N/A")
        trace_output = signal_result.get("trace_output", "")
        trace_scoring = signal_result.get("trace_scoring", "")
        render_parts = [f"{section_name} section  |  group: {group}  |  format: {vf}"]
        if trace_output:
            render_parts.append(f"output: {trace_output}")
        if trace_scoring:
            render_parts.append(f"scoring: {trace_scoring}")
        render_status = "\u2705" if status != "SKIPPED" else "\u23ed\ufe0f"
        table.add_row(
            "5",
            f"{_STAGE_ICONS['render']} Render",
            render_status,
            "\n".join(render_parts),
        )
    else:
        # Signal not in results
        lifecycle = signal_def.get("lifecycle_state", "")
        reason = (
            "INACTIVE (no extraction path)"
            if lifecycle == "INACTIVE"
            else "not evaluated in this run"
        )
        extractor = _infer_extractor(signal_def)
        table.add_row(
            "2", f"{_STAGE_ICONS['extract']} Extract", "\u2796", f"{extractor}\n{reason}"
        )
        table.add_row("3", f"{_STAGE_ICONS['map']} Map", "\u2796", reason)
        table.add_row("4", f"{_STAGE_ICONS['evaluate']} Evaluate", "\u2796", reason)
        vf = display.get("value_format", "N/A")
        table.add_row(
            "5",
            f"{_STAGE_ICONS['render']} Render",
            "\u2796",
            f"{section_name}  |  group: {group}  |  {vf}",
        )

    return table


@brain_app.command("trace")
def brain_trace(
    signal_id: str = typer.Argument(
        help="Signal ID to trace (e.g., GOV.BOARD.independence)"
    ),
    blueprint: bool = typer.Option(
        False,
        "--blueprint",
        help="Show theoretical route without requiring a run",
    ),
    ticker: str = typer.Option(
        "",
        "--ticker",
        help="Ticker for live mode (defaults to most recent)",
    ),
) -> None:
    """Trace a signal's full pipeline journey (5 stages).

    Default mode shows results from the last completed analysis run.
    Use --blueprint to show the theoretical route from YAML definitions only.
    """
    # 1. Load signal YAML definition
    signal_def = _find_signal_yaml(signal_id)
    if signal_def is None:
        console.print(
            f"[red]Signal '{signal_id}' not found in brain/signals/[/red]"
        )
        raise typer.Exit(code=1)

    # 2. Load group name from manifest
    group_id = signal_def.get("group", "")
    group_name = _get_group_name_map().get(group_id, "")

    if blueprint:
        # Blueprint mode
        header = _build_header_panel(
            signal_id, signal_def, group_id, group_name, "blueprint"
        )
        console.print()
        console.print(header)
        console.print()
        console.print(_build_blueprint_table(signal_id, signal_def))
        console.print()
    else:
        # Live mode — find and load state
        state_path = _find_most_recent_output(ticker)
        if state_path is None:
            console.print(
                "\n[yellow]No analysis run found.[/yellow] "
                "Use --blueprint for theoretical route, or run "
                "'do-uw analyze <TICKER>' first."
            )
            raise typer.Exit(code=1)

        state = _load_state(state_path)
        run_ticker = state.get("ticker", "unknown")
        run_info = f"{run_ticker}  |  {state_path.parent.name}/{state_path.name}"

        header = _build_header_panel(
            signal_id, signal_def, group_id, group_name, "live", run_info
        )
        console.print()
        console.print(header)
        console.print()
        console.print(_build_live_table(signal_id, signal_def, state))
        console.print()


# ---------------------------------------------------------------------------
# render-audit: declared vs rendered signals per facet
# ---------------------------------------------------------------------------


@brain_app.command("render-audit")
def brain_render_audit(
    ticker: str = typer.Argument(help="Ticker to audit"),
) -> None:
    """Show declared vs rendered signals per facet for a completed run.

    Loads facet definitions (declared signals) and compares against the
    signal results from the most recent analysis run for the ticker.
    Reports per-facet coverage and overall statistics.
    """
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.manifest_schema import collect_signals_by_group, load_manifest

    # 1. Find most recent output for the ticker
    state_path = _find_most_recent_output(ticker)
    if state_path is None:
        console.print(
            f"[red]No analysis run found for ticker '{ticker}'.[/red] "
            "Run 'do-uw analyze <TICKER>' first."
        )
        raise typer.Exit(code=1)

    state = _load_state(state_path)
    run_ticker = state.get("ticker", ticker)

    # 2. Load manifest groups and build signal-to-group map
    manifest = load_manifest()
    signals_data = load_signals()
    all_signals = signals_data.get("signals", [])
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]
    sig_groups = collect_signals_by_group(active_signals)

    # 3. Load signal results
    results = _get_signal_results(state)

    # 4. Build audit table
    table = Table(
        title=f"\U0001f4ca  Render Audit: {run_ticker}",
        show_header=True,
        header_style="bold",
        border_style="dim",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("Group", width=26)
    table.add_column("Rendered", width=10, justify="right")
    table.add_column("Skipped", width=10, justify="right")
    table.add_column("Missing", width=10, justify="right")
    table.add_column("Coverage", width=10, justify="right")

    total_declared = 0
    total_rendered = 0
    total_skipped = 0
    total_missing = 0

    for ms in manifest.sections:
        for group in ms.groups:
            if group.id == "red_flags":
                continue

            declared = sig_groups.get(group.id, [])
            if not declared:
                continue

            rendered_count = 0
            skipped_count = 0
            missing_count = 0

            for sig_id in declared:
                result = results.get(sig_id)
                if result is None:
                    missing_count += 1
                elif result.get("status") == "SKIPPED" or result.get("data_status") == "DATA_UNAVAILABLE":
                    skipped_count += 1
                else:
                    rendered_count += 1

            total_declared += len(declared)
            total_rendered += rendered_count
            total_skipped += skipped_count
            total_missing += missing_count

            pct = round(rendered_count / len(declared) * 100) if declared else 0
            pct_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"

            rendered_str = f"[green]{rendered_count}[/green]/{len(declared)}"
            skipped_str = f"[yellow]{skipped_count}[/yellow]" if skipped_count else "[dim]0[/dim]"
            missing_str = f"[red]{missing_count}[/red]" if missing_count else "[dim]0[/dim]"
            pct_str = f"[{pct_color}]{pct}%[/{pct_color}]"

            table.add_row(group.name, rendered_str, skipped_str, missing_str, pct_str)

    # Summary row
    table.add_section()
    overall_pct = round(total_rendered / total_declared * 100) if total_declared > 0 else 0
    overall_color = "green" if overall_pct >= 80 else "yellow" if overall_pct >= 50 else "red"
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold green]{total_rendered}[/bold green]/{total_declared}",
        f"[bold yellow]{total_skipped}[/bold yellow]" if total_skipped else "[dim]0[/dim]",
        f"[bold red]{total_missing}[/bold red]" if total_missing else "[dim]0[/dim]",
        f"[bold {overall_color}]{overall_pct}%[/bold {overall_color}]",
    )

    console.print()
    console.print(f"[dim]State: {state_path.parent.name}/{state_path.name}[/dim]")
    console.print()
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# trace-chain: data chain audit across all signals
# ---------------------------------------------------------------------------

# Abbreviated gap type labels for compact table display
_GAP_ABBREV: dict[str, str] = {
    "NO_ACQUISITION": "NO_ACQ",
    "MISSING_FIELD_KEY": "NO_FK",
    "NO_EVALUATION": "NO_EVAL",
    "NO_FACET": "NO_FAC",
}


@brain_app.command("trace-chain")
def brain_trace_chain(
    signal_id: Optional[str] = typer.Argument(  # noqa: UP007
        None, help="Signal ID for detailed chain view (omit for full audit table)"
    ),
    json_out: Optional[Path] = typer.Option(  # noqa: UP007
        None, "--json", help="Write JSON report to file"
    ),
) -> None:
    """Audit signal data chains: acquire -> extract -> analyze -> render.

    Without arguments: shows summary stats + full signal table with chain status.
    With a signal ID: shows vertical detail for that signal's chain links.
    With --json: writes structured JSON report for CI consumption.
    """
    from do_uw.brain.chain_validator import (
        ChainGapType,
        validate_all_chains,
        validate_single_chain,
    )

    if signal_id is not None:
        # --- Single signal mode ---
        _trace_chain_single(signal_id)
        return

    # --- Full table mode (and/or JSON export) ---
    report = validate_all_chains()

    # Summary panel
    summary_text = (
        f"Total: [bold]{report.total_signals}[/bold] | "
        f"Complete: [bold green]{report.chain_complete}[/bold green] | "
        f"Broken: [bold red]{report.chain_broken}[/bold red] | "
        f"Inactive: [dim]{report.inactive_count}[/dim]\n"
        f"Foundational: {report.foundational_complete} complete, "
        f"{report.foundational_broken} broken"
    )
    console.print()
    console.print(
        Panel(
            summary_text,
            title="[bold]Chain Audit Summary[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    # Gap breakdown table
    if report.gap_summary:
        gap_table = Table(
            title="Gap Breakdown",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold",
            padding=(0, 1),
        )
        gap_table.add_column("Gap Type", min_width=24)
        gap_table.add_column("Signals", justify="right", width=10)
        for gs in report.gap_summary:
            gap_table.add_row(gs.gap_type.value, str(gs.count))
        console.print(gap_table)

    # Full signal table (sorted: broken first, then complete, then inactive)
    sorted_results = sorted(
        report.results,
        key=lambda r: (
            0 if r.chain_status == "broken" else 1 if r.chain_status == "complete" else 2
        ),
    )

    # Main table (active signals only)
    active_results = [r for r in sorted_results if r.chain_status != "inactive"]
    if active_results:
        sig_table = Table(
            title=f"Signal Chains ({len(active_results)} active)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            title_style="bold",
            padding=(0, 1),
        )
        sig_table.add_column("Signal ID", min_width=28)
        sig_table.add_column("Name", min_width=20, max_width=40)
        sig_table.add_column("Status", width=10, justify="center")
        sig_table.add_column("Gaps", min_width=20)

        for r in active_results:
            if r.chain_status == "complete":
                status_str = "[green]OK[/green]"
            else:
                status_str = "[red]BROKEN[/red]"

            gap_strs = [
                _GAP_ABBREV.get(g.value, g.value) for g in r.gaps
            ]
            gaps_display = ", ".join(gap_strs) if gap_strs else ""

            sig_table.add_row(r.signal_id, r.signal_name[:40], status_str, gaps_display)

        console.print(sig_table)

    # Inactive signals (separate dim table)
    inactive_results = [r for r in sorted_results if r.chain_status == "inactive"]
    if inactive_results:
        inactive_table = Table(
            title=f"Inactive Signals ({len(inactive_results)})",
            show_header=True,
            header_style="dim",
            border_style="dim",
            title_style="dim",
            padding=(0, 1),
        )
        inactive_table.add_column("Signal ID", min_width=28, style="dim")
        inactive_table.add_column("Name", min_width=20, style="dim")
        for r in inactive_results:
            inactive_table.add_row(r.signal_id, r.signal_name)
        console.print(inactive_table)

    # JSON export
    if json_out is not None:
        _write_chain_json(report, json_out)

    console.print()


def _trace_chain_single(signal_id: str) -> None:
    """Show vertical chain detail for a single signal."""
    from do_uw.brain.brain_signal_schema import BrainSignalEntry
    from do_uw.brain.brain_unified_loader import load_signals
    from do_uw.brain.chain_validator import _build_facet_signal_map, validate_single_chain
    from do_uw.brain.manifest_schema import load_manifest
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    # Load all signals and find the one we want
    data = load_signals()
    signal_dicts = data["signals"]
    target: BrainSignalEntry | None = None
    for raw in signal_dicts:
        entry = (
            raw if isinstance(raw, BrainSignalEntry)
            else BrainSignalEntry.model_validate(raw)
        )
        if entry.id == signal_id:
            target = entry
            break

    if target is None:
        console.print(f"[red]Signal '{signal_id}' not found in brain/signals/[/red]")
        raise typer.Exit(code=1)

    # Load manifest and build facet signal map
    manifest = load_manifest()
    facet_signal_map = _build_facet_signal_map(manifest)
    field_routing_keys = set(FIELD_FOR_CHECK.keys())

    # Validate
    result = validate_single_chain(target, facet_signal_map, manifest, field_routing_keys)

    # Build vertical panel
    console.print()
    lines: list[str] = [
        f"Signal: [bold cyan]{result.signal_id}[/bold cyan]",
        f"Name: {result.signal_name}",
        f"Type: {result.signal_type}",
    ]
    status_style = (
        "green" if result.chain_status == "complete"
        else "dim" if result.chain_status == "inactive"
        else "red"
    )
    lines.append(f"Status: [{status_style}]{result.chain_status.upper()}[/{status_style}]")
    lines.append("")

    for link in result.links:
        label = link.link_type.upper().ljust(8)
        if link.status == "complete":
            status_mark = "[green]OK[/green]"
        elif link.status == "na":
            status_mark = "[dim]N/A[/dim]"
        else:
            status_mark = "[red]BROKEN[/red]"
        lines.append(f"{label} {status_mark}  {link.detail}")

    if result.gaps:
        lines.append("")
        gap_names = [g.value for g in result.gaps]
        lines.append(f"[red]Gaps: {', '.join(gap_names)}[/red]")

    console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Chain Detail[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )
    )
    console.print()


def _write_chain_json(report: Any, path: Path) -> None:
    """Serialize ChainReport to JSON file."""
    data = report.model_dump()

    # Convert enum values to strings for JSON serialization
    for result in data.get("results", []):
        result["gaps"] = [g if isinstance(g, str) else g.value for g in result.get("gaps", [])]
    for gs in data.get("gap_summary", []):
        gt = gs.get("gap_type")
        if hasattr(gt, "value"):
            gs["gap_type"] = gt.value

    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    console.print(f"Report written to [bold]{path}[/bold]")
