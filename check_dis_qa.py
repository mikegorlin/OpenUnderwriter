#!/usr/bin/env python3
"""Run QA verification on DIS output."""

import json
from pathlib import Path
from do_uw.models.state import AnalysisState
from do_uw.validation.qa_report import run_qa_verification


def main():
    output_dir = Path("output/DIS")
    state_path = output_dir / "state.json"

    print(f"Loading state from {state_path}")
    with open(state_path, "r") as f:
        state_data = json.load(f)

    state = AnalysisState.model_validate(state_data)

    print(f"Running QA verification for {state.ticker}")
    report = run_qa_verification(state, output_dir)

    print(f"QA Report for {report.ticker}:")
    print(f"  PASS: {report.pass_count}")
    print(f"  WARN: {report.warn_count}")
    print(f"  FAIL: {report.fail_count}")

    for check in report.checks:
        if check.status in ("FAIL", "WARN"):
            print(f"  [{check.status}] {check.category}/{check.name}: {check.detail}")
            if check.value:
                print(f"      value: {check.value}")
    print("\nContent category checks:")
    for check in report.checks:
        if check.category == "Content":
            print(f"  [{check.status}] {check.category}/{check.name}: {check.detail}")


if __name__ == "__main__":
    main()
