#!/usr/bin/env python3
"""Run QA verification on CAT and SMCI outputs."""

import json
from pathlib import Path
from do_uw.models.state import AnalysisState
from do_uw.validation.qa_report import run_qa_verification


def run_qa(ticker):
    output_dir = Path(f"output/{ticker}")
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

    # Print content checks
    print("\nContent category checks:")
    for check in report.checks:
        if check.category == "Content":
            print(f"  [{check.status}] {check.category}/{check.name}: {check.detail}")

    return report


def main():
    print("=" * 60)
    print("CAT QA Verification")
    print("=" * 60)
    cat_report = run_qa("CAT")

    print("\n" + "=" * 60)
    print("SMCI QA Verification")
    print("=" * 60)
    smci_report = run_qa("SMCI")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(
        f"CAT: PASS={cat_report.pass_count}, WARN={cat_report.warn_count}, FAIL={cat_report.fail_count}"
    )
    print(
        f"SMCI: PASS={smci_report.pass_count}, WARN={smci_report.warn_count}, FAIL={smci_report.fail_count}"
    )


if __name__ == "__main__":
    main()
