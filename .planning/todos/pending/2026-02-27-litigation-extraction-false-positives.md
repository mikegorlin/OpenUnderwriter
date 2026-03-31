---
created: 2026-02-27T21:00:00Z
title: Litigation extraction misclassifies boilerplate 10-K legal reserves as active cases
area: extract
severity: high
files:
  - src/do_uw/stages/extract/ (LLM litigation extraction prompts)
  - src/do_uw/stages/analyze/check_mappers_sections.py (LIT field mapping)
  - src/do_uw/stages/analyze/signal_details.py (LIT detail enrichment)
---

## Problem

The LLM extraction pipeline misclassifies routine 10-K legal reserve disclosures as securities class actions and derivative suits. Confirmed on SNA (Snap-on) which has no meaningful D&O litigation history:

1. **Fake SCA**: "Legal settlement (2025)" extracted from 10-K with allegation "Unspecified legal matter", $22M settlement. This is a standard legal reserve disclosure, not an SCA. No case name, no court, no docket number.
2. **Hollow derivative suit**: Extracted from web search with confidence LOW. No case name, no court, no filing date. Allegation is just "Shareholder derivative action" — a generic label, not a real case.
3. **Cascading false positives**: These hollow records trigger LIT.SCA.demand=1, LIT.SCA.derivative=1, and LIT.PATTERN.sol_windows=9 — all false signals.

Previously documented: the "normal course of business" boilerplate SCA filter exists in check_mappers but the extraction layer is creating the records before that filter can act.

## Solution

### Extraction layer (primary fix)
- LLM litigation prompt should require **named parties, court/jurisdiction, and docket number** for an SCA to be extracted. "Legal settlement" with "Unspecified legal matter" should NOT produce a CaseDetail record.
- Add explicit instruction: "Standard legal reserve disclosures and boilerplate litigation language in Item 3 are NOT securities class actions. Only extract cases with specific named plaintiffs, courts, and case numbers."

### Post-extraction filter (defense in depth)
- Filter hollow CaseDetail records that lack: case_name with actual party names, AND (court OR case_number). Records missing both should be dropped or flagged as LOW confidence boilerplate.
- The existing boilerplate SCA filter in check_mappers catches "normal course of business" text but doesn't catch LLM-generated generic labels like "Unspecified legal matter".

### Validation
- Run on SNA: should produce 0 SCAs, 0 derivative suits
- Run on AAPL: verify real cases (Epic v. Apple etc.) still extracted
- Run on RPM: verify real litigation still captured
