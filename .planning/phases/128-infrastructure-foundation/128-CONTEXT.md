# Phase 128: Infrastructure Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the codebase structurally ready for 10+ new sections in v10.0. Split the oversized assembly module, establish regression reference snapshots, make the pipeline incremental for faster iteration, store raw filings for hallucination detection, cross-validate LLM output against XBRL, and deduplicate the audit appendix.

</domain>

<decisions>
## Implementation Decisions

### Assembly Module Split
- **Domain registry pattern** — each domain registers a builder function; assembly module becomes a thin loop through the registry
- **Merge into existing context_builders/** — move assembly logic for each domain INTO the respective context_builder files (governance.py, market.py, financials.py, etc.). The html_context_assembly.py module dissolves entirely
- New sections in future phases = new context_builder file that registers itself, zero changes to assembly
- Each resulting file must be under 500 lines

### Audit Appendix Cleanup
- **Problem is duplicate info** — same signal/field appears in multiple overlapping audit tables (disposition audit + render audit + unrendered fields)
- **Claude's Discretion** on the exact layout — pick the most space-efficient approach that still proves thoroughness. Could be summary+expandable-detail, single unified table, or section-grouped compact view
- Goal: eliminate redundancy, reduce appendix length significantly while maintaining the "show your work" audit trail

### Regression Reference Snapshots (NOT "golden baselines")
- **Current output is NOT the quality standard** — it's been degrading. The reference is for regression DETECTION, not quality preservation
- **Two layers**: JSON context snapshot (data-level regression) + HTML section hashes (rendering regression)
- When a section hash changes: verify the change was an improvement, not accidental breakage
- **Three tickers**: AAPL + RPM + V — covers mega-cap tech, mid-cap industrial, large-cap financial
- These are reference snapshots, not targets to match

### Incremental Acquisition
- Inventory-based checking: ACQUIRE stage checks state.acquired_data and skips already-fetched data sources
- `--from-stage` and `--rerender` already exist from v9.0 — this adds smarter behavior to the default ACQUIRE path
- Goal: second run of `underwrite AAPL` completes ACQUIRE in <30 seconds

### Raw Filing Storage
- Store raw filing text (10-K, DEF 14A full text) in output/TICKER/sources/ alongside existing output files
- Links to LLM extraction cache via accession number / form type
- Purpose: enable hallucination detection by comparing LLM claims against source text

### Hallucination Cross-Validation
- **Financial numbers: XBRL wins** — when LLM-extracted value differs from XBRL by >2x, auto-correct to XBRL value. Add footnote showing discrepancy was caught. LLM value logged for debugging.
- **Non-financial content: raw filing cross-check** — store raw filing text, check if key claims in LLM output actually appear in the source filing. Flag claims with no source match.
- This is infrastructure for Phase 130 (dual-voice) which will generate more LLM commentary

### Claude's Discretion
- Exact audit appendix layout and grouping approach
- Registry implementation details (decorators vs explicit registration)
- Raw filing text storage format (plain text files vs SQLite)
- Specific hash algorithm for section comparison
- Incremental acquisition cache key design

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Assembly Module
- `src/do_uw/stages/render/html_context_assembly.py` — The 712-line file to dissolve. Contains build_html_context() and helper functions
- `src/do_uw/stages/render/context_builders/` — Existing domain builders (governance.py, market.py, financials.py, etc.) that will absorb assembly logic

### Acquisition Pipeline
- `src/do_uw/stages/acquire/orchestrator.py` — Acquisition orchestrator coordinating 14+ clients. Inventory checking wraps these
- `src/do_uw/stages/acquire/__init__.py` — Stage entry point calling AcquisitionOrchestrator.run()
- `src/do_uw/stages/acquire/clients/` — Individual acquisition clients (sec_client.py, market_client.py, etc.)

### Audit Appendix
- `src/do_uw/stages/render/context_builders/audit.py` — Signal disposition audit context builder
- `src/do_uw/stages/render/context_builders/render_audit.py` — Render completeness audit
- `src/do_uw/stages/render/sections/sect3_audit.py` — Audit section templates

### User Requirements
- `.planning/research/companion-system-features.md` — HNGE comparison identifying the quality gaps this infrastructure enables
- `.planning/research/user-directives-checklist.md` — 200 consolidated directives including visual verification, data integrity, and anti-patterns

### User Feedback
- Memory: `feedback-incremental-acquisition.md` — Detailed incremental acquisition requirements
- Memory: `feedback-raw-data-storage.md` — Raw filing storage rationale and requirements
- Memory: `handoff-v9-audit-fixes.md` — Outstanding bugs and uncommitted fixes context

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context_builders/` directory: 15+ domain-specific builders already exist — assembly logic merges into these
- `AcquisitionOrchestrator`: wraps all client calls — inventory checking can be added as a pre-check in orchestrator.run()
- `AnalysisCache` (SQLite): existing caching infrastructure for LLM extractions — can be extended for raw filing storage
- `self_review.py`: existing self-review module reads rendered HTML — can share section parsing with regression snapshots

### Established Patterns
- Context builders return `dict[str, Any]` consumed by Jinja2 templates
- Acquisition clients have uniform `acquire()` interface via `AcquisitionClient` base
- Filing text already fetched and passed to LLM extraction — storing it is capturing what's already in memory
- XBRL extraction provides ground-truth financial numbers via `state.extracted.xbrl_data`

### Integration Points
- `build_html_context(state)` is called from `html_renderer.py` — the only consumer of the assembly module
- `orchestrator.run(state)` populates `state.acquired_data` — inventory checking happens before client dispatch
- Audit appendix templates in `templates/sections/audit/` — template changes needed alongside context builder changes

</code_context>

<specifics>
## Specific Ideas

- User emphasized: "you get carried away and then don't do the right things" — keep this phase strictly infrastructure, no feature creep
- User emphasized: "make sure all brain functions are still together and intact" — brain signal integrity is non-negotiable throughout
- Regression reference is for detecting CHANGES, not preserving current (subpar) quality — "the old reports were far from great"
- Brain portability principle: brain YAML is source of truth, renderers are dumb consumers — this split must not break that contract

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 128-infrastructure-foundation*
*Context gathered: 2026-03-22*
