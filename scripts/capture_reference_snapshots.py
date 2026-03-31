"""Capture reference snapshots for regression detection.

Usage: uv run python scripts/capture_reference_snapshots.py [--tickers AAPL,RPM,V] [--output-dir .planning/baselines]

For each ticker:
1. Load state.json from output/TICKER/
2. Build HTML context via build_html_context(state)
3. Save context keys + types as JSON snapshot (not full values -- too large)
4. Render HTML and compute per-section SHA256 hashes
5. Save section hashes as JSON
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_TICKERS = ["AAPL", "RPM", "V"]
DEFAULT_OUTPUT_DIR = ".planning/baselines"


def load_state(ticker: str) -> Any:
    """Load state.json for a ticker from output directory.

    Checks both output/TICKER/state.json and output/TICKER/<date>/state.json
    (most recent date subfolder first).
    """
    from do_uw.models.state import AnalysisState

    base = Path(f"output/{ticker}")
    # Direct path
    state_path = base / "state.json"
    if state_path.exists():
        return AnalysisState.model_validate_json(state_path.read_text())
    # Check date subfolders (most recent first)
    if base.exists():
        date_dirs = sorted(
            [d for d in base.iterdir() if d.is_dir() and (d / "state.json").exists()],
            key=lambda d: d.name,
            reverse=True,
        )
        if date_dirs:
            state_path = date_dirs[0] / "state.json"
            return AnalysisState.model_validate_json(state_path.read_text())
    raise FileNotFoundError(f"No state.json for {ticker} in {base} or date subfolders")


def capture_context_snapshot(state: Any) -> dict[str, Any]:
    """Capture context keys, types, and sample values."""
    from do_uw.stages.render.context_builders.assembly_registry import (
        build_html_context,
    )

    context = build_html_context(state)
    snapshot: dict[str, Any] = {}
    for key, value in sorted(context.items()):
        entry: dict[str, Any] = {"type": type(value).__name__}
        if isinstance(value, dict):
            entry["key_count"] = len(value)
            entry["keys"] = sorted(value.keys())[:20]
        elif isinstance(value, list):
            entry["length"] = len(value)
        elif isinstance(value, (str, int, float, bool)):
            entry["value"] = (
                value if isinstance(value, (int, float, bool)) else value[:100]
            )
        snapshot[key] = entry
    return snapshot


def _find_file(ticker: str, filename: str) -> Path | None:
    """Find a file in output/TICKER/ or output/TICKER/<date>/."""
    base = Path(f"output/{ticker}")
    direct = base / filename
    if direct.exists():
        return direct
    if base.exists():
        date_dirs = sorted(
            [d for d in base.iterdir() if d.is_dir() and (d / filename).exists()],
            key=lambda d: d.name,
            reverse=True,
        )
        if date_dirs:
            return date_dirs[0] / filename
    return None


def compute_section_hashes(ticker: str) -> dict[str, str]:
    """Compute SHA256 hashes for each HTML section."""
    html_path = _find_file(ticker, f"{ticker}_worksheet.html")
    if html_path is None:
        return {}
    html = html_path.read_text()
    sections: dict[str, str] = {}
    # Pattern 1: section tags with id
    for match in re.finditer(
        r'<section[^>]*id="([^"]+)"[^>]*>(.*?)</section>', html, re.DOTALL
    ):
        section_id = match.group(1)
        content = match.group(2).strip()
        sections[section_id] = hashlib.sha256(content.encode()).hexdigest()[:16]
    # Pattern 2: div.worksheet-section with data-section attribute
    for match in re.finditer(
        r'<div[^>]*data-section="([^"]+)"[^>]*>(.*?)</div>\s*(?=<div[^>]*data-section|$)',
        html,
        re.DOTALL,
    ):
        section_id = match.group(1)
        content = match.group(2).strip()
        if section_id not in sections:
            sections[section_id] = hashlib.sha256(content.encode()).hexdigest()[:16]
    return sections


def capture_snapshot(ticker: str, output_dir: Path) -> dict[str, Any]:
    """Capture full snapshot for one ticker."""
    output_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(ticker)
    context_snap = capture_context_snapshot(state)
    section_hashes = compute_section_hashes(ticker)
    snapshot = {
        "ticker": ticker,
        "context_keys": context_snap,
        "section_hashes": section_hashes,
        "context_key_count": len(context_snap),
        "section_count": len(section_hashes),
    }
    snap_path = output_dir / f"{ticker}_reference.json"
    snap_path.write_text(json.dumps(snapshot, indent=2, default=str))
    return snapshot


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Capture reference snapshots")
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    tickers = [t.strip() for t in args.tickers.split(",")]
    output_dir = Path(args.output_dir)
    for ticker in tickers:
        try:
            snap = capture_snapshot(ticker, output_dir)
            print(
                f"{ticker}: {snap['context_key_count']} context keys, "
                f"{snap['section_count']} section hashes"
            )
        except Exception as e:
            print(f"{ticker}: FAILED - {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
