#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/gorlin/projects/UW/OpenUnderwriter/src")

from do_uw.validation.qa_content import _check_raw_threshold_evidence
from bs4 import BeautifulSoup

html_path = (
    "/Users/gorlin/projects/UW/OpenUnderwriter/output/AAPL/AAPL_20260402_v0_2_0_worksheet.html"
)
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
checks = _check_raw_threshold_evidence(soup)
for check in checks:
    print(f"Status: {check.status}")
    print(f"Detail: {check.detail}")
    print(f"Value: {check.value}")
    print(f"Category: {check.category}, Name: {check.name}")
    if check.status == "FAIL":
        sys.exit(1)
