# Phase 46: Brain-Driven Gap Search - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a brain-to-acquire feedback loop to the pipeline: after all structured ACQUIRE completes, checks that ended up SKIPPED (no structured-source data) get targeted web searches so they can resolve to TRIGGERED or CLEAR instead of silently absent. The 68 SKIPPED checks from v1.0 are the target population.

This phase does NOT change pipeline orchestration structure beyond adding gap search logic at the end of ACQUIRE. It does NOT add a new pipeline stage.

</domain>

<decisions>
## Implementation Decisions

### Gap Classification — Brain YAML Fields (NOT a separate config file)
- Classification is stored as new fields **directly on each check's brain YAML file** in `brain/checks/`: `gap_bucket: routing-gap|intentionally-unmapped|aspirational` and `gap_keywords: [...]`
- This is the ONLY correct location — the brain is the single knowledge store for all per-check metadata; a separate `config/gap_search_buckets.yaml` would duplicate brain knowledge and is explicitly prohibited
- Generated as the **first task in Phase 46 execution** by an agent that reads brain check metadata, auto-classifies, and writes the new fields back to the YAML files; then runs `brain build` to rebuild brain.duckdb
- **All three bucket types are eligible for web gap search** — routing-gap, intentionally-unmapped, and aspirational checks all receive gap search attempts
- The `gap_keywords` field lives on the check YAML — same as all other check metadata

### Query Generation
- Always **company-specific** — every query includes the company name and ticker; no company-agnostic queries
- Queries are **LLM-generated at runtime** (two-step: LLM generates the optimized search string, Brave Search executes it)
- Query generation and execution happen at the **end of ACQUIRE stage** — after all structured acquisition, before passing state to EXTRACT. All web fetching stays in ACQUIRE.

### Evidence Quality Gate
- Keyword confirmation uses **per-check `gap_keywords` lists from brain check YAML files**
- Check with keyword match in search snippet → **TRIGGERED**, confidence=LOW
- Check with search results but NO keyword match → **CLEAR**, confidence=LOW (not SKIPPED)
- Source format: `"WEB (gap): {domain}"` e.g. `"WEB (gap): reuters.com"` — domain-level traceability, not full URL

### Search Budget Allocation
- Priority ordering: **check severity from brain metadata** — highest-severity eligible checks get searches first
- Budget model: **hard stop at 50 total shared budget** — gap searches draw from the same 50-search pool as regular acquisition; if only 5 searches remain, gap search gets 5, not 15
- Cache: gap search results use the **same TTL as other DuckDB-cached acquired data** — a second run of the same ticker within the TTL window skips re-searching already-resolved checks
- Visibility: **pipeline log line + QA audit table row** showing gap search consumption (e.g., "Gap search: 12/15 budget used, 8 eligible checks unsearched")

### Claude's Discretion
- Exact LLM prompt structure for query generation
- How brain metadata severity scores are normalized for priority ranking (if not already on a standard scale)
- Internal structure of the `gap_keywords` list beyond the required fields (bucket, keywords)
- How multi-result Brave snippets are evaluated against the keyword list (any match vs majority)

</decisions>

<specifics>
## Specific Ideas

- The brain check YAML files should have a `gap_keywords` field per eligible check — keyword list is used by the evidence gate to confirm or deny triggered status
- "WEB (gap)" source format with domain (not full URL) balances traceability and cleanliness in the QA audit table
- The QA audit table should show a summary row for gap search budget consumption alongside existing content

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 46-brain-driven-gap-search*
*Context gathered: 2026-02-25*
