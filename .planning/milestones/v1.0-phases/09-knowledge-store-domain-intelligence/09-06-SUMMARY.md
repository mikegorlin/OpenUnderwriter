---
phase: 09
plan: 06
subsystem: knowledge-store
tags: [playbooks, industry-verticals, sic-mapping, resolve-stage, analyze-stage]
depends_on:
  requires: ["09-01", "09-02", "09-05"]
  provides: ["industry-playbooks", "playbook-activation", "industry-specific-checks"]
  affects: ["10-xx", "11-xx"]
tech_stack:
  added: []
  patterns: ["playbook-activation-pattern", "sic-naics-mapping", "incubating-check-injection"]
key_files:
  created:
    - src/do_uw/knowledge/playbook_data.py
    - src/do_uw/knowledge/playbook_data_extra.py
    - src/do_uw/knowledge/playbooks.py
    - tests/knowledge/test_playbooks.py
  modified:
    - src/do_uw/stages/resolve/__init__.py
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/knowledge/compat_loader.py
    - src/do_uw/knowledge/__init__.py
    - src/do_uw/models/state.py
    - tests/test_resolve.py
decisions:
  - id: "09-06-01"
    decision: "active_playbook_id field on AnalysisState (not generic metadata dict)"
    reason: "Typed field with clear semantics for cross-stage consumption; discoverable by pyright"
  - id: "09-06-02"
    decision: "Split playbook_data.py + playbook_data_extra.py for 500-line compliance"
    reason: "5 playbooks with 10 checks each is too large for a single file"
  - id: "09-06-03"
    decision: "Compact _check() helper function for check dict construction"
    reason: "Reduces boilerplate; each check still has all required fields"
  - id: "09-06-04"
    decision: "load_playbooks called in compat_loader._append_industry_checks"
    reason: "BackwardCompatLoader creates its own in-memory store that needs playbook data loaded"
  - id: "09-06-05"
    decision: "Non-blocking playbook activation with try/except in _activate_industry_playbook"
    reason: "Playbook activation must never break the RESOLVE stage pipeline flow"
metrics:
  duration: "8m 41s"
  completed: "2026-02-09"
  tests_added: 43
  tests_total: 1390
---

# Phase 9 Plan 06: Industry Playbooks Summary

**One-liner:** 5 industry playbooks (Tech/SaaS, Biotech/Pharma, Financial Services, Energy/Utilities, Healthcare) with 50 checks, auto-activated during RESOLVE via SIC/NAICS mapping, injected into ANALYZE via BackwardCompatLoader.

## What Was Built

### Industry Playbook Data (Task 1)

Created comprehensive playbook definitions for 5 high-priority verticals:

| Playbook | SIC Ranges | Checks | Theories | Questions | Scoring Adjustments |
|----------|-----------|--------|----------|-----------|-------------------|
| TECH_SAAS | 3571-3579, 3661-3679, 3812, 7371-7379 | 10 | 4 | 5 | F3: 0.9, F8: 1.2 |
| BIOTECH_PHARMA | 2830-2836, 2860-2869, 3841-3851, 8731-8734 | 10 | 5 | 5 | F1: 1.3, F8: 1.2 |
| FINANCIAL_SERVICES | 6000-6599 | 10 | 5 | 5 | F3: 1.2, F8: 1.1 |
| ENERGY_UTILITIES | 1200-1389, 2900-2999, 4900-4991 | 10 | 5 | 5 | F1: 1.2, F8: 1.3 |
| HEALTHCARE | 8000-8099, 5912, 5047 | 10 | 5 | 5 | F1: 1.3, F8: 1.1 |

Each check includes: id, name, section, pillar, severity, execution_mode, threshold_type, required_data, data_locations, scoring_factor, output_section, and metadata_json with playbook_id.

### Playbook Activation API (Task 1)

- `load_playbooks(store)` -- Idempotent insertion of 5 playbooks + 50 INCUBATING checks
- `activate_playbook(sic, naics, store)` -- SIC primary, NAICS fallback matching
- `get_industry_checks(store, playbook_id)` -- Industry-specific check retrieval
- `get_industry_questions(store, playbook_id)` -- Meeting prep questions
- `get_scoring_adjustments(store, playbook_id)` -- Factor weight multipliers
- `get_claim_theories(store, playbook_id)` -- Industry claim theory descriptions
- `get_active_checks_with_industry(store, playbook_id)` -- Merged ACTIVE + industry checks

### RESOLVE Stage Integration (Task 2)

- After company identity resolution, `_activate_industry_playbook` runs with try/except wrapping
- Extracts SIC/NAICS from CompanyIdentity SourcedValue fields
- Creates in-memory KnowledgeStore, loads playbooks, activates matching playbook
- Stores playbook ID in `state.active_playbook_id`

### ANALYZE Stage Integration (Task 2)

- Reads `state.active_playbook_id` before creating BackwardCompatLoader
- Passes `playbook_id` parameter to BackwardCompatLoader constructor
- BackwardCompatLoader calls `load_playbooks` and `get_industry_checks` when playbook_id is set
- Industry checks are appended to the standard checks list with deduplication by ID

## Decisions Made

1. **active_playbook_id on AnalysisState**: Typed field rather than generic metadata dict. Clear semantics, pyright-discoverable, and Pydantic-serializable.
2. **Split playbook data files**: playbook_data.py (286 lines) + playbook_data_extra.py (193 lines) for 500-line compliance.
3. **Compact _check() helper**: Reduces per-check boilerplate from ~15 lines to 1-3 lines while preserving all required fields.
4. **load_playbooks in compat_loader**: Ensures playbooks exist in the auto-created in-memory store before querying.
5. **Non-blocking activation**: try/except around entire activation function -- logs warning on failure but never breaks pipeline.

## Deviations from Plan

None -- plan executed exactly as written.

## File Sizes

| File | Lines |
|------|-------|
| playbook_data.py | 286 |
| playbook_data_extra.py | 193 |
| playbooks.py | 297 |
| compat_loader.py | 242 |
| resolve/__init__.py | 196 |
| analyze/__init__.py | 111 |
| test_playbooks.py | 292 |

All under 500-line limit.

## Test Coverage

- 39 new playbook tests (data integrity, activation, queries, compat loader integration)
- 4 new resolve stage tests (playbook activation, non-matching SIC, non-blocking behavior)
- Total: 1390 tests passing, 0 regressions

## Next Phase Readiness

Phase 9 complete. All 6 plans executed. The knowledge store now provides:
- SQLAlchemy ORM with lifecycle management (09-01)
- Migration from brain/ JSON with query API (09-02)
- Provenance and traceability (09-03)
- Learning infrastructure and CLI (09-04)
- Stage wiring and document ingestion (09-05)
- Industry playbooks with auto-activation (09-06)
