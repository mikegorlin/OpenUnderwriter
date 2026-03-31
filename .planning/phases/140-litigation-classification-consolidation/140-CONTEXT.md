# Phase 140: Litigation Classification & Consolidation - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Ensure every litigation entry in the worksheet is classified by legal theory (not data source), deduplicated across all sources, disambiguated by year, and tagged with D&O coverage side. Also filter boilerplate 10-K legal reserves from being misclassified as active cases.

</domain>

<decisions>
## Implementation Decisions

### Classification Architecture
- **D-01:** Unified post-extraction classifier — a NEW module runs AFTER all extractors complete, reclassifying every case uniformly from legal theories + named defendants. Per-extractor classification becomes initial hints only, overwritten by the unified classifier.
- **D-02:** Classifier overwrites existing `CaseDetail.coverage_type` and `CaseDetail.legal_theories` fields. No new fields — the unified classifier IS the source of truth. Per-extractor values are treated as initial hints that get replaced.

### Deduplication
- **D-03:** Universal dedup engine — single dedup algorithm handles ALL case types (SCA, derivative, regulatory, deal litigation). Uses case name similarity + filing year + court as matching signals. Consolidates into one entry with all source references listed.
- **D-04:** Consolidated display uses primary (highest-confidence) case name. Below it, list all source references: "Sources: EFTS/SCAC, 10-K Item 3, Supabase SCA DB". Fields merged with highest-confidence source winning per field.

### Year Disambiguation
- **D-05:** Always append year to every case name: "In re Fastly (2020)", "SEC v. Ripple Labs (2020)". No conditional logic — consistent, unambiguous format for all cases.

### Missing Field Recovery
- **D-06:** Flag missing critical fields (case number, court, class period, named defendants) with data quality annotation. Store case identifiers in a `cases_needing_recovery` list on LitigationLandscape so the ACQUIRE stage can attempt web search recovery on next run. Note: CLAUDE.md prohibits data acquisition outside `stages/acquire/`, so the classifier itself cannot trigger web searches — it only flags and queues for recovery.

### Boilerplate Filtering
- **D-07:** Legal theory match required for classification. A case must match at least one `LegalTheory` enum value. Boilerplate reserves like "routine litigation matters" or "general legal contingencies" won't match any theory and get filtered to a separate "unclassified reserves" bucket — still shown in worksheet but clearly separated from classified cases.

### Folded Todos
- **Litigation extraction misclassifies boilerplate 10-K legal reserves as active cases** — The unified classifier with legal theory match requirement (D-07) directly addresses this. Cases that don't match any legal theory are separated into an unclassified reserves bucket rather than being treated as active classified cases.

### Claude's Discretion
- Exact similarity thresholds for universal dedup (current SCA dedup uses 80% word overlap — may need tuning for other case types)
- How to structure the web search queries for missing field recovery
- Internal module organization (single file vs split by concern)
- Whether to extend existing `deduplicate_cases()` or create new dedup module

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Models
- `src/do_uw/models/litigation.py` — CaseDetail, CoverageType, LegalTheory, EnforcementStage, CaseStatus enums, SECEnforcementPipeline, LitigationLandscape container
- `src/do_uw/models/litigation_details.py` — RegulatoryProceeding, DealLitigation, DefenseAssessment, SOLWindow, ContingentLiability sub-models

### Extraction Pipeline
- `src/do_uw/stages/extract/extract_litigation.py` — Orchestrator that runs all SECT6 sub-area extractors
- `src/do_uw/stages/extract/sca_extractor.py` — SCA extraction + existing `detect_coverage_type()` and `deduplicate_cases()` functions
- `src/do_uw/stages/extract/sca_parsing.py` — SCA case parsing logic
- `src/do_uw/stages/extract/derivative_suits.py` — Derivative suit extraction
- `src/do_uw/stages/extract/deal_litigation.py` — M&A litigation extraction
- `src/do_uw/stages/extract/regulatory_extract.py` — Non-SEC regulatory extraction
- `src/do_uw/stages/extract/llm_litigation.py` — LLM-based case extraction from 10-K/DEF14A

### Rendering
- `src/do_uw/stages/render/context_builders/litigation.py` — Context builder for litigation section
- `src/do_uw/stages/render/context_builders/_litigation_helpers.py` — Display helpers including `COVERAGE_DISPLAY` mapping
- `src/do_uw/stages/render/context_builders/litigation_evaluative.py` — Signal-based evaluative display
- `src/do_uw/stages/render/sections/sect6_litigation.py` — HTML section renderer

### Acquisition
- `src/do_uw/stages/acquire/clients/litigation_client.py` — Primary acquisition (web search, EFTS, SCAC)
- `src/do_uw/stages/acquire/clients/supabase_litigation.py` — Supabase SCA database
- `src/do_uw/stages/acquire/clients/courtlistener_client.py` — CourtListener API

### Brain Signals
- `brain/signals/litigation/` — LIT.DEFENSE.*, LIT.REG.*, LIT.PATTERN.*, LIT.SCA.* signals

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CoverageType` enum (14 values) and `LegalTheory` enum (12 values) — already comprehensive, classification logic maps to these
- `detect_coverage_type()` in `sca_extractor.py` — existing inference logic from allegations to coverage type, can be generalized
- `deduplicate_cases()` in `sca_extractor.py` — 80% word overlap algorithm with filing year gap check, extend for universal use
- `is_case_viable()` — minimum field viability check, use as part of boilerplate filter

### Established Patterns
- All extracted data uses `SourcedValue[T]` with source/confidence/as_of provenance
- Extractors run in dependency order, orchestrated by `extract_litigation.py`
- Fault-isolated: each extractor wrapped in try/except
- Context builder reads from `state.extracted.litigation` — rendering is decoupled from extraction

### Integration Points
- **Unified classifier** inserts AFTER `extract_litigation.py` runs all extractors, BEFORE analyze stage scores signals
- **Universal dedup** runs as part of (or immediately after) the unified classifier
- **Year disambiguation** modifies case_name field during consolidation
- **Missing field recovery** triggers from the classifier when fields are empty — needs access to web search (ACQUIRE boundary concern)
- **Boilerplate filter** runs as first pass in classifier — cases without legal theory match go to separate bucket

</code_context>

<specifics>
## Specific Ideas

- The existing `COVERAGE_DISPLAY` dict in `_litigation_helpers.py` already maps coverage types to human-readable labels — classifier output should use the same enum values
- Supabase dedup currently uses (filing_date, company_name) which is different from SCA word-overlap — universal engine should handle both matching strategies
- Filing year gap check (>1 year apart = distinct) from existing dedup should be preserved in universal engine

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- "Earnings guidance signals conflate analyst consensus with company-issued guidance" — Not litigation-related, belongs in signals/analysis phase

### Other
- Coverage side financial impact estimation (quantifying A vs B vs C exposure in dollars) — future enhancement, separate phase
- Automated case status updates from court docket monitoring — requires new data source integration

</deferred>

---

*Phase: 140-litigation-classification-consolidation*
*Context gathered: 2026-03-28*
