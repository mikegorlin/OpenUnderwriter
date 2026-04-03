#!/usr/bin/env python3
"""Run QA verification on existing output."""

import sys
import json
from pathlib import Path

sys.path.insert(0, "src/do_uw")

from do_uw.models.state import AnalysisState
from do_uw.validation.qa_report import run_qa_verification
from do_uw.validation.qa_report_generator import print_qa_report


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_qa.py <output_dir>")
        print("Example: python run_qa.py output/AAPL")
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"Directory {output_dir} does not exist")
        sys.exit(1)

    state_path = output_dir / "state.json"
    if not state_path.exists():
        print(f"state.json not found in {output_dir}")
        sys.exit(1)

    print(f"Loading state from {state_path}")
    with open(state_path, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    state = AnalysisState.model_validate(state_data)

    print(f"Running QA verification for {state.ticker}...")
    qa_report = run_qa_verification(state, output_dir)
    print_qa_report(qa_report)

    # Also check raw threshold evidence count
    raw_check = [c for c in qa_report.checks if c.name == "Raw evidence"]
    if raw_check:
        print(f"\nRaw evidence check: {raw_check[0].status} - {raw_check[0].detail}")
        if raw_check[0].status != "PASS":
            print("  Need to fix remaining raw threshold patterns")

    # Check truncation artifacts
    trunc_check = [c for c in qa_report.checks if c.name == "Truncation artifacts"]
    if trunc_check:
        print(f"\nTruncation artifacts: {trunc_check[0].status} - {trunc_check[0].detail}")
        if trunc_check[0].status != "PASS":
            print("  Need to fix truncation artifacts")


if __name__ == "__main__":
    main()
