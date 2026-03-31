# Phase 46: Brain-Driven Gap Search - Research

**Researched:** 2026-02-25
**Domain:** Acquire-stage gap-fill loop — YAML config classification, LLM query generation, budget-gated web search, CheckResult re-evaluation, AcquiredData persistence
**Confidence:** HIGH (codebase directly inspected; no external library research needed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Gap Classification Config**
- Static YAML file: `config/gap_search_buckets.yaml` — each check ID mapped to its bucket (routing-gap, intentionally-unmapped, aspirational)
- Generated as the first task in Phase 46 execution by an agent that reads brain check metadata and auto-classifies; output is reviewable before being checked in
- All three bucket types are eligible for web gap search — routing-gap, intentionally-unmapped, and aspirational checks all receive gap search attempts
- The bucket config also contains per-check `keywords` lists (see Evidence gate below)

**Query Generation**
- Always company-specific — every query includes the company name and ticker; no company-agnostic queries
- Queries are LLM-generated at runtime (two-step: LLM generates the optimized search string, Brave Search executes it)
- Query generation and execution happen at the end of ACQUIRE stage — after all structured acquisition, before passing state to EXTRACT. All web fetching stays in ACQUIRE.

**Evidence Quality Gate**
- Keyword confirmation uses per-check keyword lists defined in `gap_search_buckets.yaml`
- Check with keyword match in search snippet → TRIGGERED, confidence=LOW
- Check with search results but NO keyword match → CLEAR, confidence=LOW (not SKIPPED)
- Source format: `"WEB (gap): {domain}"` e.g. `"WEB (gap): reuters.com"` — domain-level traceability, not full URL

**Search Budget Allocation**
- Priority ordering: check severity from brain metadata — highest-severity eligible checks get searches first
- Budget model: hard stop at 50 total shared budget — gap searches draw from the same 50-search pool as regular acquisition; if only 5 searches remain, gap search gets 5, not 15
- Cache: gap search results use the same TTL as other DuckDB-cached acquired data — a second run of the same ticker within the TTL window skips re-searching already-resolved checks
- Visibility: pipeline log line + QA audit table row showing gap search consumption (e.g., "Gap search: 12/15 budget used, 8 eligible checks unsearched")

### Claude's Discretion
- Exact LLM prompt structure for query generation
- How brain metadata severity scores are normalized for priority ranking (if not already on a standard scale)
- Internal data structure of `gap_search_buckets.yaml` beyond the required fields (bucket, keywords)
- How multi-result Brave snippets are evaluated against the keyword list (any match vs majority)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GAP-01 | System audits all 68 "Data mapping not configured" SKIPPED checks and classifies each into routing-gap, intentionally-unmapped, or aspirational bucket before any gap-search code is written | Triage script reads brain_checks_active, calls `make_skipped` reason check, outputs `gap_search_buckets.yaml`; brain `tier` + `claims_correlation` + `acquisition_tier` fields are the classification signals |
| GAP-02 | System identifies L2/L3 acquisition-tier checks with DATA_UNAVAILABLE status after structured acquisition and generates targeted web search queries from each check's brain metadata (name, required_data) | `acquisition_tier` field present on all 400 YAML checks (L1=363, L3=37, L2=0 today); check_results with `data_status=DATA_UNAVAILABLE` + status=SKIPPED are the target population; LLM prompt uses check `name` + `required_data` |
| GAP-03 | System executes gap-targeted web searches within a hard per-run cap (≤15 searches) that draws from the existing 50-search budget, with L1 checks ineligible for web fallback | `WebSearchClient.budget_remaining` already tracks this; gap searcher reads `budget_remaining`, caps own allocation at `min(budget_remaining, 15)`; L1 filter on `acquisition_tier` field from brain check metadata |
| GAP-04 | System enforces an evidence quality gate: web search results may produce at most LOW-confidence advisory results; a gap-search result can never directly set a check to TRIGGERED status without keyword-presence confirmation | Keywords per-check in `gap_search_buckets.yaml`; evaluator checks any-snippet for keyword match before setting status to TRIGGERED vs CLEAR |
| GAP-05 | System re-evaluates previously SKIPPED checks after gap search, updating CheckResult to TRIGGERED or CLEAR with confidence=LOW and source="WEB (gap)" where web evidence was found | `CheckResult` model accepts `source` and `confidence` fields; update in-place in `AnalysisResults.check_results` dict after gap search phase |
| GAP-06 | Gap search results are persisted to AcquiredData.brain_targeted_search (a Pydantic field on AnalysisState) so results are available across pipeline stages without re-searching | New Pydantic field `brain_targeted_search: dict[str, Any]` added to `AcquiredData` in `models/state.py`; SQLite cache key `gap_search:{ticker}:{check_id}:{query_hash}` with same TTL as other acquired data |
</phase_requirements>

---

## Summary

Phase 46 adds a brain-to-acquire feedback loop that closes the gap between brain check definitions and pipeline execution. After all structured ACQUIRE completes, the 68 checks that end with `data_status_reason = "Data mapping not configured for this check"` are the target population. These checks have no data mapper, so they SKIP without ever attempting retrieval. The phase adds a new Phase E sub-step at the end of ACQUIRE that uses brain check metadata (name, required_data, keywords from YAML config) to generate company-specific web search queries, executes them via the existing `WebSearchClient`, and re-evaluates the check results from SKIPPED to TRIGGERED or CLEAR based on keyword presence in snippets.

The codebase is well-positioned for this. `WebSearchClient` already has pluggable budget tracking and caching. `AcquiredData` is a plain Pydantic model — adding `brain_targeted_search` is one field addition. `CheckResult` already has `source`, `confidence`, and `data_status` fields; updating them post-evaluation is a dict mutation on `AnalysisResults.check_results`. The QA audit template already reads `confidence` and `source` from check dicts. The primary new artefacts are: a YAML triage config (`config/gap_search_buckets.yaml`), a gap searcher module (`stages/acquire/gap_searcher.py`), and LLM query generation logic.

The 68-check target population is identified by `data_status_reason == "Data mapping not configured for this check"` (set in `check_helpers.make_skipped` when `data` dict is empty). This is distinct from checks that have data mappers but the data is absent at runtime — those have reason `"Required data not available from filings"`. Only the "not configured" population is eligible for gap search.

**Primary recommendation:** Build in this order — (1) triage audit script → `gap_search_buckets.yaml`, (2) `AcquiredData.brain_targeted_search` field + cache wiring, (3) gap searcher with budget gating and evidence gate, (4) post-search CheckResult re-evaluator, (5) QA audit visibility row.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic v2 | 2.x | `AcquiredData.brain_targeted_search` field, `GapSearchResult` model | Project-wide model standard |
| duckdb | current | Read brain check metadata + `acquisition_tier` for priority ordering | Already used for brain_checks_active |
| httpx | current | No new HTTP calls needed; search goes through existing `WebSearchClient.search()` | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyYAML / ruamel.yaml | current | Read `gap_search_buckets.yaml` at ACQUIRE time | Config files are YAML (pattern from brain/checks/*.yaml) |
| pathlib | stdlib | File path for `config/gap_search_buckets.yaml` | Standard across project |
| hashlib | stdlib | Cache key hashing for gap search results | Already used in `WebSearchClient._query_hash()` |
| logging | stdlib | Pipeline log visibility for gap search budget | All stages use standard logging |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| YAML for bucket config | JSON (like other configs in `src/do_uw/config/*.json`) | YAML is used for all brain check files — natural fit since this config describes check properties. Either works. |
| Any-snippet keyword match | Majority-snippet match | Any-match is simpler, lower false-negative rate. Majority-match raises bar unnecessarily given snippet truncation to ~150 chars. |

---

## Architecture Patterns

### Recommended Project Structure

The new gap search code belongs entirely in `stages/acquire/`:

```
src/do_uw/
  config/
    gap_search_buckets.yaml       # NEW — check-to-bucket + keywords mapping
  models/
    state.py                      # MODIFY — add brain_targeted_search field to AcquiredData
  stages/acquire/
    gap_searcher.py               # NEW — gap search orchestration module
    gap_query_generator.py        # NEW — LLM query generation (split if gap_searcher hits 300+ lines)
    orchestrator.py               # MODIFY — add Phase E call at end of run()
```

Size discipline: keep `gap_searcher.py` under 300 lines pre-emptively (not 500) since it will be touched frequently during v1.1.

### Pattern 1: Extending the Orchestrator with Phase E

The `AcquisitionOrchestrator.run()` already has labeled phases (A, B, B+, B++, C, D). Phase E belongs after Phase D (gate checking), before returning `acquired`. The pattern is already established in `_run_discovery_hook()` which shows non-blocking post-gate additions:

```python
# Phase E: Brain-driven gap search
logger.info("Phase E: Brain-driven gap search")
_run_gap_search_phase(state, acquired, self._web_search, self._cache)
```

`_run_gap_search_phase` is a module-level function in `gap_searcher.py` that accepts the shared `WebSearchClient` instance (so budget tracking is shared) and the `AnalysisCache` (so results cache under the same TTL policy).

### Pattern 2: gap_search_buckets.yaml Structure

Based on `BrainCheckEntry` schema and locked decisions, the YAML structure is:

```yaml
# config/gap_search_buckets.yaml
# Generated by Phase 46 triage script — do not hand-edit check IDs
# Bucket values: routing-gap | intentionally-unmapped | aspirational
# Keywords: per-check list used by evidence gate (any-snippet match = TRIGGERED)
---
checks:
  - id: LIT.REG.state_ag_action
    bucket: routing-gap
    keywords: [attorney general, state AG, enforcement action, settlement, civil penalty]

  - id: BIZ.COMP.market_position_shift
    bucket: intentionally-unmapped
    keywords: [market share, competitive threat, product recall, disruption]

  - id: EXEC.CHARACTER.personal_conduct
    bucket: aspirational
    keywords: [misconduct, personal lawsuit, fraud, criminal, arrest, ethics violation]
```

The triage script generates all 68 entries. The `bucket` field is informational (all buckets are eligible for gap search per locked decision). The `keywords` field is used by the evidence gate.

### Pattern 3: AcquiredData.brain_targeted_search Field

Add one field to `AcquiredData` in `models/state.py`:

```python
brain_targeted_search: dict[str, Any] = Field(
    default_factory=dict,
    description=(
        "Gap search results keyed by check_id. Each value is a dict with: "
        "query (str), results (list[dict]), keywords_matched (bool), "
        "suggested_status (str: TRIGGERED|CLEAR), confidence (str: LOW)."
    ),
)
```

The field uses `dict[str, Any]` (not a typed model per `AcquiredData` convention — see `blind_spot_results`, `acquisition_metadata` which follow the same pattern). This avoids coupling `AcquiredData` to gap-search-specific Pydantic models.

### Pattern 4: Budget Gating in gap_searcher.py

The `WebSearchClient` is shared with the orchestrator — its `budget_remaining` property reflects all prior searches. Gap search must read this value to compute its own cap:

```python
GAP_SEARCH_MAX = 15  # Maximum gap searches per run

def _run_gap_search_phase(
    state: AnalysisState,
    acquired: AcquiredData,
    web_search: WebSearchClient,
    cache: AnalysisCache | None,
) -> None:
    available = min(web_search.budget_remaining, GAP_SEARCH_MAX)
    if available <= 0:
        logger.info("Gap search: no budget remaining, skipping")
        return

    eligible = _get_eligible_checks(acquired, state)  # sorted by severity
    searched = 0
    for check_id, check_meta in eligible:
        if searched >= available:
            break
        # generate query via LLM, search, evaluate, store
        searched += 1

    logger.info(
        "Gap search: %d/%d budget used, %d eligible checks unsearched",
        searched, available, len(eligible) - searched
    )
```

### Pattern 5: Cache Key for Gap Search Results

Follow the existing `WebSearchClient._query_hash()` pattern. Gap search cache keys:

```
gap_search:{ticker}:{check_id}:{query_hash}
```

TTL: same 30-day TTL (`WEB_SEARCH_TTL = 30 * 24 * 3600`) as other web search results. On cache hit, skip re-searching AND skip re-evaluating the check (result is already in `acquired.brain_targeted_search`). This satisfies GAP-06 requirement that a second run does not fire redundant gap searches.

### Pattern 6: Triage Script (GAP-01 First Task)

The triage script (first task, generates the YAML) must:

1. Load all brain checks from `brain_checks_active` via `BrainDBLoader.load_checks()`
2. Identify the 68 checks with `data_status_reason == "Data mapping not configured"` (proxy: no `data_strategy.field_key` AND no FIELD_FOR_CHECK entry AND no Phase26 prefix mapper — same logic as `gap_detector.py`)
3. For each: classify bucket based on `acquisition_tier`, `required_data`, and check ID prefix:
   - `acquisition_tier == L1` → intentionally-unmapped (L1 checks must come from structured sources, they're in the wrong bucket, but they're ineligible for web search)
   - `required_data` contains only structured sources AND check has no web-fallback path → routing-gap
   - `required_data` contains web-source strings OR check `name` suggests qualitative data → aspirational
4. Auto-populate `keywords` from check `name` and `required_data` fields (tokenize, filter stopwords)
5. Write to `config/gap_search_buckets.yaml` — this file is checked in and reviewed by the user before any gap-search code runs

Note from CONTEXT.md locked decisions: L1 checks are ineligible for web fallback (GAP-03). This means the triage script should mark L1 checks with `bucket: intentionally-unmapped` but the gap searcher should enforce `acquisition_tier != L1` as a hard filter when selecting eligible checks — the YAML classification is informational documentation, the eligibility check in code is the enforcement gate.

### Pattern 7: LLM Query Generation

Two-step flow:
1. LLM generates an optimized search string from check metadata
2. `WebSearchClient.search()` executes it

The LLM call uses the existing `anthropic` SDK (already in project). Prompt structure (Claude's discretion):

```python
QUERY_GEN_PROMPT = """\
Generate a targeted web search query to find public information about {company_name} ({ticker})
related to: {check_name}.

Context: {required_data_summary}

Requirements:
- Include company name and ticker
- Focus on recent news, regulatory actions, or public disclosures
- Return ONLY the search query string, nothing else
- Maximum 12 words"""
```

The LLM call should be a minimal, cheap call (no streaming, low max_tokens ~30). Consider using `claude-haiku-3-5` or the project's default model. If the LLM call fails, fall back to a template-generated query: `'"{company_name}" {check_name_keywords}'`.

### Pattern 8: CheckResult Re-evaluation

After gap search completes, the re-evaluator iterates `acquired.brain_targeted_search` and updates `state.analysis.analysis.check_results`:

```python
def apply_gap_search_results(
    acquired: AcquiredData,
    analysis_results: AnalysisResults,
) -> int:
    """Apply gap search results to SKIPPED CheckResults. Returns count updated."""
    updated = 0
    for check_id, gap_result in acquired.brain_targeted_search.items():
        check_result = analysis_results.check_results.get(check_id)
        if check_result is None:
            continue
        if check_result.get("status") != "SKIPPED":
            continue  # Don't overwrite non-SKIPPED results

        new_status = gap_result["suggested_status"]  # "TRIGGERED" or "CLEAR"
        domain = gap_result.get("domain", "web")
        check_result["status"] = new_status
        check_result["confidence"] = "LOW"
        check_result["source"] = f"WEB (gap): {domain}"
        check_result["data_status"] = "EVALUATED"
        check_result["data_status_reason"] = "Resolved via gap search"
        updated += 1
    return updated
```

**WHERE this runs matters.** The ANALYZE stage runs after ACQUIRE. The gap search results are persisted in `acquired.brain_targeted_search`, available at ANALYZE time. The re-evaluation happens in ANALYZE stage (after `execute_checks()` produces its initial results) because that's when `analysis.check_results` exists. The ACQUIRE stage stores the gap search data; the ANALYZE stage applies it. This keeps the boundary clean.

### Anti-Patterns to Avoid

- **Don't add a new pipeline stage:** The phase explicitly does NOT add a stage. Gap search is a sub-step of ACQUIRE; re-evaluation is a post-step of ANALYZE.
- **Don't run LLM extraction on snippets:** Decision locked. Snippets are too short. Keyword matching only.
- **Don't exceed 50-line functions in new modules:** Follow project convention of single-responsibility functions.
- **Don't call gap search for all 68 checks unconditionally:** Budget gate is mandatory. Priority order ensures highest-value checks get the budget.
- **Don't use `WEB_SEARCH` as source format:** The locked format is `"WEB (gap): {domain}"` — distinct from the existing `WEB_SEARCH` acquisition source.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Search budget tracking | Custom counter in gap_searcher.py | `WebSearchClient.budget_remaining` | Already tracks all prior searches in the shared instance |
| Query result caching | Custom cache layer | `AnalysisCache` via `WebSearchClient.search(query, cache=cache)` | Same TTL, same hit detection, same monthly tracking |
| Check metadata loading | Parse YAML files directly | `BrainDBLoader.load_checks()` | brain_checks_active view already normalizes the 400 checks |
| YAML file loading | Custom YAML parser | PyYAML / standard `yaml.safe_load()` | Project already uses this for brain check YAML files |

---

## Common Pitfalls

### Pitfall 1: Re-evaluation Happens Before ANALYZE Runs

**What goes wrong:** The gap search runs in ACQUIRE. If re-evaluation also runs in ACQUIRE (trying to update check_results before they exist), it will fail silently because `state.analysis` is None at that point.

**Why it happens:** The phase stores gap search results in ACQUIRE (correct) but the re-evaluation call requires `AnalysisResults.check_results` which is populated by ANALYZE.

**How to avoid:** Phase E in ACQUIRE stores results in `AcquiredData.brain_targeted_search` only. A separate post-step in ANALYZE calls `apply_gap_search_results(acquired, analysis)` after `execute_checks()` completes.

**Warning signs:** `state.analysis is None` errors or "attribute 'check_results' does not exist" in acquire logs.

### Pitfall 2: L1 Checks Incorrectly Included in Gap Search

**What goes wrong:** Some L1 checks also end up in the "Data mapping not configured" category because they have data mappers missing (routing gap), not because they should use web fallback. Searching the web for XBRL financial data (e.g., `FIN.LIQ.position`) is meaningless and wastes budget.

**Why it happens:** The triage script classifies by bucket but the gap searcher must enforce the L1 eligibility filter independently.

**How to avoid:** In `_get_eligible_checks()`, filter out any check where `brain_check.acquisition_tier == "L1"`. This is the code-level gate that GAP-03 requires.

**Warning signs:** Gap searches firing for checks with IDs starting `FIN.` (most are L1 XBRL checks).

### Pitfall 3: Keyword List Empty → All Results Match

**What goes wrong:** If `gap_search_buckets.yaml` has an empty `keywords: []` for a check, every search result would default to CLEAR (no keyword match). But the intent is that empty keywords should mean the check is unevaluable.

**How to avoid:** In the evidence gate, if `keywords` list is empty, the result is SKIPPED (unchanged) rather than CLEAR. A check needs keywords to be re-evaluated.

**Warning signs:** Checks with no keywords appearing as CLEAR in QA audit.

### Pitfall 4: Snippet Length Truncation

**What goes wrong:** Brave Search snippets are ~150 chars. Multi-word keywords like "material weakness restatement" may not match if the snippet cuts mid-sentence.

**How to avoid:** Use single-word or two-word keywords in `gap_search_buckets.yaml`. The triage script should prefer short, distinctive terms (e.g., `["restatement", "restate"]` not `["material weakness restatement"]`). Also: check across ALL result snippets for the query, not just the first result.

**Warning signs:** Known-issue checks failing to TRIGGER when news clearly contains the keyword.

### Pitfall 5: LLM Query Generation Cost Per Run

**What goes wrong:** If a fresh analysis (no cache hit) has 15 eligible gap checks, that's 15 LLM calls. With a fast/cheap model this is acceptable (~$0.001 each) but must be accounted for in per-run cost.

**How to avoid:** Cache query strings alongside results. Cache key: `gap_query:{check_id}` so the generated query string survives across runs without re-generating. Alternatively, generate all queries in a single LLM call (one prompt, list of 15 checks, numbered responses). Single-call is cheaper and faster.

**Warning signs:** Cost tracker showing unexpected LLM spend on gap-related calls.

### Pitfall 6: Budget Consumed Before Gap Search Runs

**What goes wrong:** If pre/post blind spot sweeps + news client use all 50 searches, gap search gets 0 budget. The pipeline log must make this visible.

**How to avoid:** Log budget remaining at Phase E start: `"Phase E: Gap search starting with %d/%d budget remaining"`. This surfaces the starvation scenario to the user. The 15-search cap means gap search never takes all the budget, but it can receive nothing if the blind spot sweeps ran wide.

**Warning signs:** Phase E log always showing "0 searches available" — needs blind spot budget tuning.

---

## Code Examples

### Example 1: AcquiredData Field Addition

Source: `src/do_uw/models/state.py` — add after `company_logo_b64`:

```python
brain_targeted_search: dict[str, Any] = Field(
    default_factory=dict,
    description=(
        "Gap search results keyed by check_id. "
        "Populated by Phase E of ACQUIRE for checks with "
        "data_status_reason='Data mapping not configured'. "
        "Format: {check_id: {query, results, keywords_matched, "
        "suggested_status, domain, confidence}}"
    ),
)
```

### Example 2: Triage Script Logic to Identify the 68 SKIPPED Checks

The 68 checks can be identified programmatically without running the full pipeline. They are the checks that will receive `data_status_reason = "Data mapping not configured for this check"` — i.e., checks where `map_check_data()` returns an empty dict. The triage script can replicate this logic:

```python
from do_uw.knowledge.gap_detector import detect_gaps, ACQUIRED_SOURCES, PHASE26_PREFIXES
from do_uw.stages.analyze.check_field_routing import FIELD_FOR_CHECK
from do_uw.brain.brain_loader import BrainDBLoader

loader = BrainDBLoader()
data = loader.load_checks()
checks = data["checks"]

no_routing = []
for check in checks:
    if check.get("execution_mode") != "AUTO":
        continue
    check_id = check.get("id", "")
    ds = check.get("data_strategy", {})
    has_field_key = isinstance(ds, dict) and ds.get("field_key") is not None
    has_legacy = check_id in FIELD_FOR_CHECK
    has_p26 = any(check_id.startswith(p) for p in PHASE26_PREFIXES)
    if not has_field_key and not has_legacy and not has_p26:
        no_routing.append(check)

# no_routing is the population for gap_search_buckets.yaml
```

### Example 3: Gap Searcher Budget Gate

```python
# In stages/acquire/gap_searcher.py
GAP_SEARCH_MAX = 15

def run_gap_search(
    state: AnalysisState,
    acquired: AcquiredData,
    web_search: WebSearchClient,
    cache: AnalysisCache | None,
    buckets: dict[str, dict[str, Any]],
) -> None:
    """Phase E: gap-targeted web searches for SKIPPED checks."""
    available = min(web_search.budget_remaining, GAP_SEARCH_MAX)
    if available <= 0:
        logger.info("Phase E: no search budget available for gap search")
        return

    company_name = _get_company_name(state)
    eligible = _rank_eligible_checks(buckets, available)

    searched = 0
    for check_id, bucket_entry in eligible:
        if searched >= available:
            break

        cache_key = f"gap_search:{state.ticker}:{check_id}"
        cached = cache.get(cache_key) if cache else None
        if cached is not None:
            acquired.brain_targeted_search[check_id] = cached
            continue

        query = _generate_query(check_id, bucket_entry, company_name, state.ticker)
        results = web_search.search(query, cache=cache)
        searched += 1

        keywords = bucket_entry.get("keywords", [])
        keywords_matched, domain = _evaluate_evidence(results, keywords)
        suggested = "TRIGGERED" if keywords_matched else ("CLEAR" if results else None)

        if suggested is None:
            continue  # No results at all — leave as SKIPPED

        gap_result = {
            "query": query,
            "results_count": len(results),
            "keywords_matched": keywords_matched,
            "suggested_status": suggested,
            "domain": domain,
            "confidence": "LOW",
        }
        acquired.brain_targeted_search[check_id] = gap_result
        if cache:
            cache.set(cache_key, gap_result, source="gap_search", ttl=WEB_SEARCH_TTL)

    logger.info(
        "Gap search: %d/%d budget used, %d eligible checks unsearched",
        searched, available, max(0, len(eligible) - searched),
    )
```

### Example 4: Evidence Gate

```python
def _evaluate_evidence(
    results: list[dict[str, str]],
    keywords: list[str],
) -> tuple[bool, str]:
    """Check if any result snippet contains a keyword.

    Returns (keywords_matched: bool, domain: str of first matching result).
    """
    if not keywords or not results:
        return False, ""

    lower_keywords = [k.lower() for k in keywords]
    for result in results:
        snippet = (result.get("snippet") or result.get("description") or "").lower()
        title = (result.get("title") or "").lower()
        text = f"{title} {snippet}"
        if any(kw in text for kw in lower_keywords):
            url = result.get("url", "")
            domain = _extract_domain(url)
            return True, domain

    # Results exist but no keyword match
    return False, ""
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SKIPPED checks silently absent | SKIPPED → gap search → TRIGGERED/CLEAR | Phase 46 | Reduces SKIPPED count from 68 baseline |
| Web search only in blind spot sweeps | Web search also in targeted gap-fill loop | Phase 46 | Different budget allocation bucket |
| CheckResult.confidence not populated | confidence=LOW for WEB (gap) results | Phase 46 | QA audit can display confidence level |

---

## Open Questions

1. **Which LLM to use for query generation?**
   - What we know: Project uses Anthropic Claude API; existing LLM calls in `llm_extraction.py` use the configured model.
   - What's unclear: Whether to use the same expensive model (claude-opus/sonnet) or a cheap model (haiku) for 15 short query-gen calls.
   - Recommendation: Use `claude-haiku-3-5` for query generation (cheap, fast, ~30 token output). Fall back to template query on failure. Add a `_generate_query_template()` fallback so the feature works even without LLM configured.

2. **Re-evaluation timing: ACQUIRE or ANALYZE?**
   - What we know: `AcquiredData.brain_targeted_search` is populated in ACQUIRE. `AnalysisResults.check_results` is populated in ANALYZE.
   - What's unclear: The phase success criteria says "SKIPPED check count is lower after Phase 46" — this means the re-evaluation visible in QA audit must happen before RENDER.
   - Recommendation: Store gap results in ACQUIRE (in `brain_targeted_search`). Apply re-evaluation in ANALYZE (post-`execute_checks()`). The ANALYZE stage already reads `state.acquired_data`, so `acquired_data.brain_targeted_search` is accessible there.

3. **What is the actual count of L1 checks in the 68 SKIPPED population?**
   - What we know: 363 checks are L1, 37 are L3, 0 are L2. The triage script will reveal the exact breakdown.
   - What's unclear: How many of the 68 "no routing" checks are L1 (must remain SKIPPED per GAP-03) vs L2/L3 (eligible for gap search).
   - Recommendation: The triage script is the first task specifically to answer this question before writing any gap-search code.

4. **QA audit "summary row" for gap search consumption: where exactly?**
   - What we know: CONTEXT.md says "pipeline log line + QA audit table row showing gap search consumption".
   - What's unclear: Whether this is a new row at the bottom of the QA table, a separate sub-table, or just a footer count.
   - Recommendation: Add a summary paragraph below the existing QA audit check table: "Gap search consumed N of M available searches; K checks re-evaluated (J TRIGGERED, L CLEAR)." This matches the existing pattern of the `<p class="text-xs text-gray-400 mt-4">Total checks...</p>` footer.

---

## Key Codebase Facts (For Planner Reference)

### The 68 SKIPPED Checks Root Cause

`check_helpers.make_skipped()` sets `data_status_reason = "Data mapping not configured for this check"` when `data` (the output of `map_check_data()`) is an **empty dict** — meaning no mapper exists at all for this check. This is distinct from checks where a mapper exists but returns all-None values (reason: `"Required data not available from filings"`).

The gap-check population is **strictly those with empty mapper output**. The triage script (`gap_detector.py` already implements the same logic to identify these) confirms: checks without `data_strategy.field_key`, without `FIELD_FOR_CHECK` entry, and without Phase 26+ prefix match.

### AcquiredData Convention

All existing fields that store untyped/variable data use `dict[str, Any]`:
- `blind_spot_results: dict[str, Any]`
- `acquisition_metadata: dict[str, Any]`

The new `brain_targeted_search: dict[str, Any]` follows this convention. Do NOT create a `GapSearchResult` Pydantic model and put it in `AcquiredData` — that would break serialization compatibility.

### WebSearchClient Shared Instance

The `AcquisitionOrchestrator` creates ONE `WebSearchClient` instance and passes it to `LitigationClient`, `NewsClient`, and `_run_blind_spot_sweep()`. The shared `_searches_used` counter tracks total searches. Phase E must receive this same instance (not create a new one) so budget tracking is accurate.

### QA Audit Template Bug (Already Noted, Not Phase 46 Scope)

`qa_audit.html.j2` line 37 reads `check.get('filing_ref', '')` but the field is named `source` on `CheckResult`. This bug is in QA-01 (Phase 48 scope). For Phase 46, the `source` field on re-evaluated checks will be correctly set to `"WEB (gap): {domain}"` — it just won't appear in the QA audit until Phase 48 fixes the template. The data will be correct; display is Phase 48.

### Acquisition Tier Distribution in Brain Checks

- `acquisition_tier: L1` — 363 checks (XBRL financial, SEC filings — structured only)
- `acquisition_tier: L3` — 37 checks (market price derived, stock pattern, peer data)
- `acquisition_tier: L2` — 0 checks (no L2 checks defined currently)
- No `acquisition_tier` — 0 checks (all 400 YAML entries have the field)

The 37 L3 checks are primarily in `stock/`, `biz/`, `lit/defense.yaml`, `fwrd/ma.yaml`. These are the most likely gap-search candidates. However, many L3 checks DO have `data_strategy.field_key` mappings — they're not all in the "no routing" population. The triage script will clarify the exact overlap.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection — `src/do_uw/models/state.py`, `stages/acquire/orchestrator.py`, `stages/acquire/clients/web_search.py`, `stages/acquire/__init__.py`, `stages/analyze/check_engine.py`, `stages/analyze/check_helpers.py`, `stages/analyze/check_results.py`, `knowledge/gap_detector.py`, `brain/brain_check_schema.py`, `brain/brain_loader.py`
- Brain YAML files — `brain/checks/**/*.yaml` (all 36 files, 400 entries inspected for `acquisition_tier` distribution)
- Phase context — `.planning/phases/46-brain-driven-gap-search/46-CONTEXT.md`
- Project requirements — `.planning/REQUIREMENTS.md` (GAP-01 through GAP-06)
- Project state — `.planning/STATE.md`

### Secondary (MEDIUM confidence)
- None needed — all findings come from direct codebase inspection.

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, no new dependencies needed
- Architecture: HIGH — inspected all integration points directly in source
- Pitfalls: HIGH — derived from direct code reading of `make_skipped`, `WebSearchClient`, `AcquiredData`

**Research date:** 2026-02-25
**Valid until:** 2026-03-27 (30 days — stable codebase)
