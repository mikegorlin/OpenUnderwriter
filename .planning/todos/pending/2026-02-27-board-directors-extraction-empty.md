---
created: 2026-02-27T21:30:00Z
title: Board directors array empty despite metadata being correct
area: extract
severity: high
files:
  - src/do_uw/stages/extract/board_governance.py
  - src/do_uw/stages/extract/board_parsing.py
---

## Problem

SNA validation audit: board metadata is correct (size=10, independence_ratio=0.9, CEO/Chair duality detected) but the `directors` array is EMPTY — zero individual director records extracted.

For a D&O worksheet, named board members are essential. An underwriter needs to see who's on the board, their independence status, committee assignments, tenure, and qualifications.

## Expected

Snap-on has ~10 directors including:
- Nicholas T. Pinchuk (Chairman/CEO, insider)
- 9 independent directors (per DEF 14A)

All should be extracted with names, independence status, committee memberships, and qualifications from the DEF 14A.

## Likely Cause

DEF 14A parsing populates board aggregate stats but fails to extract individual director records. The LLM extraction prompt may not be targeting the director table/bios in the proxy statement.
