# Phase 140: Litigation Classification & Consolidation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 140-litigation-classification-consolidation
**Areas discussed:** Classification source, Cross-source dedup, Year disambiguation, Missing field recovery, Consolidated display format, Boilerplate filter criteria, Classification persistence

---

## Classification Source

| Option | Description | Selected |
|--------|-------------|----------|
| Unified post-extraction classifier | New module runs AFTER all extractors, reclassifies every case uniformly from legal theories + named defendants | ✓ |
| Keep per-extractor, add validation pass | Each extractor keeps its classification logic, validation pass cross-checks | |
| You decide | Claude picks best approach | |

**User's choice:** Unified post-extraction classifier
**Notes:** Most architecturally clean — single source of truth for classification

---

## Cross-source Dedup

| Option | Description | Selected |
|--------|-------------|----------|
| Universal dedup engine | Single algorithm handles ALL case types using name similarity + filing year + court | ✓ |
| SCA-only dedup, flag others | Keep existing SCA dedup, flag potential duplicates for other types | |
| You decide | Claude picks based on data patterns | |

**User's choice:** Universal dedup engine

---

## Year Disambiguation

| Option | Description | Selected |
|--------|-------------|----------|
| Always append year | Every case shows year suffix consistently | ✓ |
| Only when ambiguous | Append year only when multiple cases share same company name | |
| You decide | Claude picks clearest approach | |

**User's choice:** Always append year

---

## Missing Field Recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Flag + attempt web recovery | Flag missing fields, trigger targeted web search, tag results LOW confidence | ✓ |
| Flag only, no recovery | Flag with 'Not Available' and annotation, no secondary acquisition | |
| Flag + CourtListener lookup | Flag, then query CourtListener API for federal case details | |

**User's choice:** Flag + attempt web recovery

---

## Consolidated Display Format

| Option | Description | Selected |
|--------|-------------|----------|
| Primary name + sources list | Highest-confidence name as primary, list all source references below | ✓ |
| Primary name + alt names | Highest-confidence name, then 'Also: [alternate names]' | |
| You decide | Claude picks clearest format | |

**User's choice:** Primary name + sources list

---

## Boilerplate Filter Criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Legal theory match required | Must match at least one LegalTheory enum value, unmatched go to 'unclassified reserves' bucket | ✓ |
| Minimum field threshold | Require at least 2 of: case name, number, court, filing date, named defendants | |
| Both combined | Require EITHER legal theory match OR minimum field threshold | |

**User's choice:** Legal theory match required

---

## Classification Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Overwrite existing fields | Unified classifier overwrites CaseDetail.coverage_type and legal_theories | ✓ |
| New fields alongside existing | Add unified_coverage_type and unified_legal_theories, keep originals for audit | |
| You decide | Claude picks based on data model patterns | |

**User's choice:** Overwrite existing fields

---

## Claude's Discretion

- Exact similarity thresholds for universal dedup
- Web search query structure for missing field recovery
- Internal module organization
- Whether to extend existing dedup or create new module

## Deferred Ideas

- Coverage side financial impact estimation (quantifying A vs B vs C exposure in dollars)
- Automated case status updates from court docket monitoring
- "Earnings guidance signals conflate analyst consensus with company-issued guidance" — reviewed but not folded (not litigation-related)
