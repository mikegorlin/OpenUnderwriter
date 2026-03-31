# Phase 134: Company Intelligence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 134-company-intelligence
**Areas discussed:** Risk Factor Review, Sector & Competitive Landscape, Concentration Assessment, Regulatory Environment
**Mode:** Auto (all areas selected, recommended defaults chosen)

---

## Risk Factor Review (COMP-01, COMP-02)

| Option | Description | Selected |
|--------|-------------|----------|
| LLM classification from 10-K Item 1A | Extract and classify each risk factor as Standard/Novel/Elevated | ✓ |
| Pattern-matching classification | Use regex/keyword matching for factor classification | |
| Manual classification | Require human input for each factor | |

**Auto-selected:** LLM classification — 10-K raw text is already stored (Phase 128), LLM extraction is the established pattern, and classification requires contextual understanding that regex can't provide.

## Sector & Competitive Landscape (COMP-03, COMP-04, COMP-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Extend existing peer group + Supabase SCA | Reuse peer_group.py, add SCA history per peer from Supabase | ✓ |
| Build new peer construction from scratch | New peer identification system | |
| Manual peer selection | User specifies peers per run | |

**Auto-selected:** Extend existing — peer_group.py already does 5-signal composite scoring, Supabase SCA integration exists. Adding SCA history per peer is incremental.

## Concentration Assessment (COMP-06, COMP-07)

| Option | Description | Selected |
|--------|-------------|----------|
| 4-dimension LLM extraction from 10-K | Extract customer/geo/product/channel from Item 1/1A + XBRL segments | ✓ |
| XBRL-only segment analysis | Use only structured XBRL data | |
| Web search enrichment | Supplement with web data | |

**Auto-selected:** LLM extraction — XBRL has geographic/product segments but not customer names or supply chain details. 10-K text has all of it. Web search is deferred (data acquisition boundary).

## Regulatory Environment (COMP-08)

| Option | Description | Selected |
|--------|-------------|----------|
| Extend existing regulatory_extract.py | Add per-regulator table display to existing extraction | ✓ |
| New regulatory monitoring system | Build comprehensive regulatory tracking | |

**Auto-selected:** Extend existing — regulatory_extract.py already covers 12 agencies. The gap is display format, not extraction.

## Claude's Discretion

- Template layout choices within beta_report
- LLM prompt engineering for risk factor classification
- Concentration threshold calibration
- Sub-section ordering

## Deferred Ideas

- Litigation extraction false positives (Phase 129 scope)
- Executive brief overhaul (Phase 136 scope)
- Volume spike correlation (Phase 133 shipped)
