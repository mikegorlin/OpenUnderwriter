# RULE RENUMBERING MAP
## v4.6 â†’ v4.7 ID Conversion Reference
## Date: January 7, 2026

---

## PURPOSE

This document maps old rule IDs (with inconsistent letter suffixes and descriptive names) to new sequential IDs. Use this for backward compatibility when referencing historical documents.

---

## RENUMBERING SUMMARY

| Category | Old Pattern | New Pattern | Count |
|----------|-------------|-------------|-------|
| TRI | 001, 001a, 001b, 002, 003 | 001-005 | 5 |
| NEG | 001, 001a-h | 001-009 | 9 |
| SEC | 001, FIN-001-006, MKT-001, STK-001 | 001-009 | 9 |
| STK | 001, 1D, 5D, 20D, 60D, 90D, 52W, ATR-001, REC-001, PAT-001 | 001-010 | 10 |
| EX | 001, 001a, 002, 003, 003a, 004-008 | 001-010 | 10 |
| ESC | 001-007 | 001-007 | 7 (no change) |

---

## TRIAGE RULES (TRI)

| Old ID | New ID | Rule Name |
|--------|--------|-----------|
| TRI-001 | TRI-001 | Submission Triage Gate |
| TRI-001a | TRI-002 | SCAC Litigation Scan |
| TRI-001b | TRI-003 | Web Litigation Scan |
| TRI-002 | TRI-004 | Route to Full Analysis |
| TRI-003 | TRI-005 | Route to Renewal Module |

---

## NEGATIVE NEWS SWEEP RULES (NEG)

| Old ID | New ID | Rule Name |
|--------|--------|-----------|
| NEG-001 | NEG-001 | Negative Sweep Protocol (master) |
| NEG-001a | NEG-002 | Securities Class Action Search |
| NEG-001b | NEG-003 | Executive Departure Search |
| NEG-001c | NEG-004 | Restatement/Accounting Search |
| NEG-001d | NEG-005 | Investigation/Subpoena Search |
| NEG-001e | NEG-006 | Stock Drop Search |
| NEG-001f | NEG-007 | Guidance Miss Search |
| NEG-001g | NEG-008 | Short Seller Search |
| NEG-001h | NEG-009 | Layoffs/Restructuring Search |

---

## SECTOR CALIBRATION RULES (SEC)

| Old ID | New ID | Rule Name |
|--------|--------|-----------|
| SEC-001 | SEC-001 | Sector Identification |
| SEC-FIN-001 | SEC-002 | EBITDA Calibration |
| SEC-FIN-002 | SEC-003 | Leverage Calibration |
| SEC-FIN-003 | SEC-004 | Cash Runway Calibration |
| SEC-FIN-004 | SEC-005 | Margin Calibration |
| SEC-FIN-005 | SEC-006 | Current Ratio Calibration |
| SEC-FIN-006 | SEC-007 | Interest Coverage Calibration |
| SEC-MKT-001 | SEC-008 | Short Interest Calibration |
| SEC-STK-001 | SEC-009 | Stock Decline Calibration |

---

## STOCK PERFORMANCE RULES (STK)

| Old ID | New ID | Rule Name |
|--------|--------|-----------|
| STK-001 | STK-001 | Stock Performance Module (master) |
| STK-1D | STK-002 | Single-Day Horizon Analysis |
| STK-5D | STK-003 | 5-Day Horizon Analysis |
| STK-20D | STK-004 | 20-Day Horizon Analysis |
| STK-60D | STK-005 | 60-Day Horizon Analysis |
| STK-90D | STK-006 | 90-Day Horizon Analysis |
| STK-52W | STK-007 | 52-Week Horizon Analysis |
| STK-ATR-001 | STK-008 | Attribution Analysis |
| STK-REC-001 | STK-009 | Recency Weighting |
| STK-PAT-001 | STK-010 | Pattern Detection |

---

## EXECUTION RULES (EX)

| Old ID | New ID | Rule Name |
|--------|--------|-----------|
| EX-001 | EX-001 | Start with Triage |
| EX-001a | EX-002 | Sector ID After Triage |
| EX-002 | EX-003 | NEG-001 Before QS |
| EX-003 | EX-004 | Nuclear Triggers First |
| EX-003a | EX-005 | STK-001 During QS |
| EX-004 | EX-006 | Scoring Data with Sources |
| EX-005 | EX-007 | Industry Module Before Output |
| EX-006 | EX-008 | Generate v1.1 with Guidance |
| EX-007 | EX-009 | Recommend Deep-Dives |
| EX-008 | EX-010 | Save State if Lengthy |

---

## QUICK SCREEN RULES (QS) - CONSOLIDATION NOTE

QS-023, QS-029, and QS-032 were consolidated into STK-001 module. 

| Old ID | New Status | Replacement |
|--------|------------|-------------|
| QS-023 | RETIRED | STK-001 through STK-007 |
| QS-029 | RETIRED | STK-001, STK-010 |
| QS-032 | RETIRED | STK-001 (low-price assessment) |

Remaining QS rules (001-022, 024-028, 030-031, 033-043) retain original numbering.

---

## SCORING RULES - CROSS-REFERENCE UPDATES

F.2 rules reference STK outputs:

| Rule | Old Reference | New Reference |
|------|---------------|---------------|
| F2-007 | STK-ATR-001 | STK-008 |
| F2-008 | STK-PAT-001 | STK-010 |

---

## UNCHANGED CATEGORIES

The following categories use clean sequential numbering and require no changes:

- F1-001 through F1-007 (Prior Litigation)
- F2-001 through F2-008 (Stock Decline)
- F3-001 through F3-007 (Restatement/Audit)
- F4-001 through F4-006 (IPO/SPAC/M&A)
- F5-001 through F5-006 (Guidance Misses)
- F6-R01 through F6-X02 (Short Interest - contextual, different pattern intentional)
- F7-H01 through F7-B02 (Insider Trading - contextual, different pattern intentional)
- F8-xxx (Volatility - contextual)
- F9-xxx (Financial Distress - contextual)
- F10-001 through F10-005 (Governance)
- NT-001 through NT-008 (Nuclear Triggers)
- TR-001 through TR-006 (Tier Rules)
- ESC-001 through ESC-007 (Escalation)
- VER-001 (Verification)
- ZER-001 (Zero Score)
- STR-001 through STR-005 (Streamlined Execution)
- IND-001 through IND-004 (Industry Module)
- DDR-001 through DDR-003 (Deep-Dive Recommendation)
- RQS-001 through RQS-020 (Renewal Quick Screen)
- REN-001 through REN-011 (Renewal Module)
- COR-001 through COR-007 (Corridor)
- VR-001 through VR-010 (Validation)
- CR-001 through CR-006 (Citation)
- SV-001 through SV-010 (Severity)
- EW-001 through EW-010 (Event-Window)
- DF-001 through DF-010 (Directional Flags)

---

**END OF RENUMBERING MAP**
