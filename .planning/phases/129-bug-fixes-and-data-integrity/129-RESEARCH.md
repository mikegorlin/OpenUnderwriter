# Phase 129: Bug Fixes and Data Integrity - Research

**Researched:** 2026-03-22
**Domain:** Data quality bugs, extraction correctness, render consistency
**Confidence:** HIGH

## Summary

Phase 129 addresses five known data quality bugs that produce incorrect or inconsistent output in the worksheet. The bugs span the full pipeline: LLM hallucination in narrative generation (FIX-01), extraction gaps in governance data (FIX-02), generic LLM-generated meeting prep questions (FIX-03), inconsistent SCA count computation across 6+ render locations (FIX-04), and stale CRF insolvency triggers with inconsistent ceiling display (FIX-05).

Phase 128 just delivered the XBRL/LLM cross-validation infrastructure (`xbrl_llm_reconciler.py`) and raw filing storage -- these are direct prerequisites for FIX-01. The SCA count inconsistency (FIX-04) is the most architecturally impactful fix, requiring extraction of a shared counting function from 13+ call sites that each implement slightly different filter logic. The CRF insolvency suppression (FIX-05) already has partial fixes in 3 locations but the logic is duplicated rather than centralized.

**Primary recommendation:** Centralize SCA counting and CRF insolvency suppression into single canonical functions first (FIX-04/FIX-05), then fix extraction and generation bugs (FIX-01/FIX-02/FIX-03) which are more localized changes.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FIX-01 | Eliminate $383B services revenue hallucination and DOJ_FCPA misclassification | XBRL cross-validation from Phase 128; narrative generator passes LLM-extracted data without validation; DOJ_FCPA in `_is_regulatory_not_sca` already filters FCPA but web search results bypass the SCA filter |
| FIX-02 | Fix extraction gaps: gender diversity, Wanda Austin board profile, Kate Adams to Jennifer Newstead GC succession | `llm_governance.py` extracts `board_gender_diversity_pct` from DEF 14A LLM schema; `board_parsing.py` and `leadership_profiles.py` handle board/exec extraction; likely stale LLM cache or extraction prompt gaps |
| FIX-03 | Company-specific meeting prep questions tied to actual risk findings | 6 question generators exist across 3 files (`meeting_questions.py`, `meeting_questions_analysis.py`, `meeting_questions_gap.py`); all walk `AnalysisState` for data-driven questions, but LLM-generated meeting prep in benchmark stage produces generic templates |
| FIX-04 | SCA count consistency across executive brief, monitoring triggers, and meeting prep | 13+ call sites import `_is_regulatory_not_sca` but apply different status filters: some use `("ACTIVE", "PENDING")`, some `"ACTIVE"` only, some `("ACTIVE", "PENDING", "N/A")`, some also include `status=None` |
| FIX-05 | Suppress stale CRF insolvency trigger; consistent CRF ceiling values | Insolvency suppression duplicated in 3 locations (`crf_bar_context.py`, `assembly_registry.py`, `sect1_executive_tables.py`); ceiling sync exists in `__init__.py` Step 6.5 but renderers may still read flat values from state |
</phase_requirements>

## Architecture Patterns

### Bug Location Map

```
FIX-01: $383B hallucination + DOJ_FCPA misclassification
  src/do_uw/stages/benchmark/narrative_generator.py    -- LLM generates narratives without XBRL cross-check
  src/do_uw/stages/benchmark/narrative_data_sections.py -- extracts data for LLM prompts (may pass bad data)
  src/do_uw/stages/extract/xbrl_llm_reconciler.py      -- Phase 128: already reconciles, need to APPLY it
  src/do_uw/stages/extract/sec_enforcement.py           -- DOJ_FCPA classification from web search

FIX-02: Gender diversity + Wanda Austin + GC succession
  src/do_uw/stages/extract/llm_governance.py           -- LLM governance extraction
  src/do_uw/stages/extract/llm/schemas/def14a.py       -- DEF 14A schema (has board_gender_diversity_pct)
  src/do_uw/stages/extract/board_parsing.py            -- Board member extraction
  src/do_uw/stages/extract/leadership_profiles.py      -- Leadership profile extraction

FIX-03: Generic meeting prep questions
  src/do_uw/stages/render/sections/meeting_prep.py     -- Word doc renderer (calls generators)
  src/do_uw/stages/render/sections/meeting_questions.py          -- Clarification + forward indicators
  src/do_uw/stages/render/sections/meeting_questions_analysis.py -- Bear case + peril + mispricing
  src/do_uw/stages/render/sections/meeting_questions_gap.py      -- Credibility + gap fillers
  src/do_uw/stages/benchmark/narrative_generator.py    -- LLM narrative (may duplicate meeting prep)

FIX-04: SCA count inconsistency (13+ call sites)
  src/do_uw/stages/score/red_flag_gates.py             -- _is_regulatory_not_sca (canonical filter)
  src/do_uw/stages/render/sections/sect1_findings_data.py        -- ("ACTIVE", "PENDING"), requires status!=None
  src/do_uw/stages/render/context_builders/_narrative_generators.py -- "ACTIVE" only
  src/do_uw/stages/render/context_builders/monitoring_context.py   -- ("ACTIVE","PENDING","N/A") + status=None
  src/do_uw/stages/render/context_builders/key_stats_context.py    -- all SCAs (no status filter)
  src/do_uw/stages/render/context_builders/litigation.py           -- ("ACTIVE","PENDING","N/A")
  src/do_uw/stages/render/context_builders/_key_stats_helpers.py   -- 2 call sites
  src/do_uw/stages/render/context_builders/_litigation_helpers.py  -- per-case filter
  src/do_uw/stages/render/context_builders/ddl_context.py          -- exclusion filter
  src/do_uw/stages/render/sections/sect6_litigation.py             -- active+pending filter
  src/do_uw/stages/render/md_narrative_sections.py                 -- "ACTIVE" only
  src/do_uw/stages/analyze/section_assessments.py                  -- analysis-stage count
  src/do_uw/stages/score/factor_data.py                            -- scoring-stage count
  src/do_uw/stages/score/pattern_fields.py                         -- pattern detection count

FIX-05: Stale CRF insolvency + ceiling display
  src/do_uw/stages/render/context_builders/crf_bar_context.py      -- insolvency suppression (inline)
  src/do_uw/stages/render/context_builders/assembly_registry.py    -- _should_suppress_insolvency_crf
  src/do_uw/stages/render/sections/sect1_executive_tables.py       -- _should_suppress_insolvency_crf_flag
  src/do_uw/stages/score/__init__.py                               -- Step 6.5 ceiling sync
  src/do_uw/stages/score/red_flag_gates.py                         -- apply_crf_ceilings + _resolve_crf_ceiling
```

### Pattern 1: Centralized SCA Count Function (FIX-04 Fix Strategy)

**What:** Extract a single `count_active_genuine_scas(state) -> int` function that all 13+ call sites use.

**When to use:** Whenever any code needs to know how many active genuine SCAs exist.

**Design:**
```python
# src/do_uw/stages/render/sca_counter.py (or similar shared location)
def count_active_genuine_scas(state: AnalysisState) -> int:
    """Single source of truth for active genuine SCA count.

    Criteria:
    - status in ("ACTIVE", "PENDING") or status is None/N/A (unknown = assume active)
    - NOT filtered by _is_regulatory_not_sca (not a genuine securities case)
    """
    ...

def get_active_genuine_scas(state: AnalysisState) -> list[SecuritiesClassAction]:
    """Return the filtered list of active genuine SCAs."""
    ...
```

**Key decision:** Whether `status=None` and `status="N/A"` cases should be counted as active. Current code disagrees -- `monitoring_context.py` includes them, `sect1_findings_data.py` excludes them. The conservative D&O underwriting answer is: **include them** (unknown status = assume active, per data integrity principle of not assuming "no data" = "no issue").

### Pattern 2: Centralized Insolvency Suppression (FIX-05 Fix Strategy)

**What:** Single `should_suppress_insolvency(state) -> bool` function replacing 3 inline implementations.

**Currently duplicated in:**
1. `crf_bar_context.py` lines 54-61 -- inline check with `_get_distress_metrics`
2. `assembly_registry.py` lines 57-79 -- `_should_suppress_insolvency_crf` with text matching
3. `sect1_executive_tables.py` line 363 -- imports `_should_suppress_insolvency_crf_flag`

**Fix:** Consolidate into one location (likely `stages/score/red_flag_gates.py` alongside CRF logic), import everywhere.

### Pattern 3: Cross-Validation Gate for LLM Narratives (FIX-01 Fix Strategy)

**What:** After LLM generates a narrative, cross-validate any dollar amounts it mentions against XBRL/state data before storing.

**Current flow:**
```
narrative_data_sections.py extracts data -> narrative_prompts.py builds prompt
-> narrative_generator.py calls LLM -> result stored on state
```

**Fix points:**
1. Ensure `narrative_data_sections.py` passes XBRL-reconciled values (not raw LLM-extracted)
2. Post-generation: scan narrative text for dollar amounts, cross-validate against state
3. Flag or strip hallucinated figures

### Anti-Patterns to Avoid
- **Fixing symptoms not root causes:** The SCA count bug exists because 13 files each compute the count independently. Patching each one separately will lead to future drift. Must centralize.
- **Duplicating suppression logic:** CRF insolvency suppression is already duplicated 3 ways. Adding a 4th fix point would make it worse.
- **Testing only AAPL:** Some bugs may be AAPL-specific (GC succession, Wanda Austin). But SCA count and CRF insolvency bugs affect all tickers. Test with multiple tickers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SCA filtering | Inline filter logic per call site | Single `get_active_genuine_scas()` function | 13+ locations already diverged; any inline fix will drift again |
| Insolvency check | Per-renderer suppression code | Single `should_suppress_insolvency()` | Already duplicated 3 ways with subtle differences |
| Dollar amount validation | Manual regex in narratives | Extend `xbrl_llm_reconciler.py` post-validation | Phase 128 already built the reconciliation infrastructure |

## Common Pitfalls

### Pitfall 1: SCA Status Filter Disagreement
**What goes wrong:** Different files count different sets of SCAs because they disagree on whether `status=None`, `status="N/A"`, and `status="PENDING"` should be included.
**Why it happens:** Each developer independently decided what "active" means when writing their render path.
**How to avoid:** Define canonical filter criteria ONCE. Current analysis of the 6 variants:
- `("ACTIVE", "PENDING")` + requires status != None -- `sect1_findings_data.py`
- `"ACTIVE"` only -- `_narrative_generators.py`, `md_narrative_sections.py`
- `("ACTIVE", "PENDING", "N/A")` + includes status=None -- `monitoring_context.py`
- All SCAs (no status filter, only `_is_regulatory_not_sca`) -- `key_stats_context.py`
**Recommendation:** Use `("ACTIVE", "PENDING")` + include `status=None/N/A` as active (conservative underwriting principle). This matches `monitoring_context.py` behavior.

### Pitfall 2: LLM Cache Staleness for FIX-02
**What goes wrong:** Re-running the pipeline with `--fresh` may still use cached LLM extraction results.
**Why it happens:** LLM extraction cache (`stages/extract/llm/cache.py`) is separate from pipeline stage cache. `--fresh` resets stage status but may not invalidate LLM cache.
**How to avoid:** For extraction prompt changes (gender diversity, GC succession), verify that LLM cache keys include the prompt text hash so changed prompts invalidate the cache.

### Pitfall 3: CRF Ceiling Display vs Applied Value
**What goes wrong:** Renderers display `ceiling_applied` from `RedFlagResult`, which may be the flat value from `red_flags.json` rather than the size-resolved value from `apply_crf_ceilings`.
**Why it happens:** `evaluate_red_flag_gates` sets `ceiling_applied` from flat config. Step 6.5 in `__init__.py` syncs resolved values back, but only if `ceiling_details` is populated. Edge cases where sync fails = stale display.
**How to avoid:** Verify the Step 6.5 sync path is robust. Add a test that resolved ceiling matches displayed ceiling for a triggered CRF.

### Pitfall 4: DOJ_FCPA Misclassification Source
**What goes wrong:** A web search result about DOJ/FCPA gets placed into `securities_class_actions` list by the LLM extractor, then `_is_regulatory_not_sca` should catch it via the `FCPA` entry in `_NON_SECURITIES_THEORIES`.
**Root cause investigation needed:** Either (a) the web search result bypasses the SCA filter entirely, (b) the `_has_securities_indicators` function has a false positive, or (c) the data enters via a different path than `securities_class_actions`. The fix must trace the exact data flow for the AAPL DOJ_FCPA entry.

### Pitfall 5: Meeting Prep vs Benchmark Narrative
**What goes wrong:** Meeting prep questions may be generated both by the rule-based generators in `render/sections/meeting_questions*.py` AND by the LLM narrative in `benchmark/narrative_generator.py`. If the LLM path produces generic output and overrides the data-driven path, questions become generic.
**How to avoid:** Clarify which path produces the meeting prep content. The rule-based generators walk AnalysisState and produce data-driven questions. If an LLM narrative also generates a "meeting prep" section, it needs the same company-specific context injection.

## Code Examples

### Current SCA Count Locations (showing divergent filter logic)

```python
# sect1_findings_data.py -- requires status not None, uses ("ACTIVE", "PENDING")
counts["sca"] = sum(
    1 for sca in scas
    if getattr(sca, "status", None) is not None
    and str(safe_sv(sca, "status") or "").upper() in ("ACTIVE", "PENDING")
    and not _is_regulatory_not_sca(sca)
)

# _narrative_generators.py -- "ACTIVE" only
active_scas = [
    c for c in sca
    if getattr(c, "status", None) is not None
    and str(_sv(getattr(c, "status", ""))).upper() == "ACTIVE"
    and not _is_regulatory_not_sca(c)
]

# monitoring_context.py -- includes "N/A" and status=None
active_genuine = [
    s for s in genuine
    if (getattr(s, "status", None) and
        str(s.status.value if hasattr(s.status, "value") else s.status).upper()
        in ("ACTIVE", "PENDING", "N/A"))
    or not getattr(s, "status", None)
]

# key_stats_context.py -- no status filter at all, only regulatory filter
r["sca_count"] = str(len([s for s in all_scas if not _is_regulatory_not_sca(s)]))
```

### Recommended Canonical SCA Counter

```python
# New shared function in a common location
def get_active_genuine_scas(state: AnalysisState) -> list:
    """Canonical active genuine SCA list -- single source of truth.

    Active = status in (ACTIVE, PENDING, N/A, None) -- conservative: unknown = active
    Genuine = passes _is_regulatory_not_sca filter
    """
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    ext = state.extracted
    if not ext or not ext.litigation:
        return []
    scas = getattr(ext.litigation, "securities_class_actions", None) or []

    _ACTIVE_STATUSES = {"ACTIVE", "PENDING", "N/A"}
    result = []
    for sca in scas:
        if _is_regulatory_not_sca(sca):
            continue
        status = getattr(sca, "status", None)
        if status is None:
            result.append(sca)  # Unknown = assume active
            continue
        status_str = (status.value if hasattr(status, "value") else str(status)).upper()
        if status_str in _ACTIVE_STATUSES or not status_str:
            result.append(sca)
    return result
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via `uv run pytest`) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/ -x -q --timeout=30` |
| Full suite command | `uv run pytest tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | No $383B hallucination in narrative; no DOJ_FCPA misclassification | unit+integration | `uv run pytest tests/render/ tests/stages/ -k "hallucin or fcpa or narrative_valid" -x` | Likely partial |
| FIX-02 | Gender diversity extracted; current GC correct; all board members present | unit | `uv run pytest tests/extract/ -k "gender or governance or board" -x` | Likely partial |
| FIX-03 | Meeting prep questions contain company-specific data | unit | `uv run pytest tests/render/ -k "meeting" -x` | Likely exists |
| FIX-04 | SCA count identical across all render paths | unit | `uv run pytest tests/ -k "sca_count or sca_consist" -x` | Wave 0 needed |
| FIX-05 | CRF insolvency suppressed for healthy companies; ceiling consistent | unit | `uv run pytest tests/ -k "crf or insolvency or ceiling" -x` | Likely partial |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q --timeout=30 -k "sca or crf or meeting or narrative or governance"`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** Full suite green + `underwrite AAPL --fresh` visual verification

### Wave 0 Gaps
- [ ] `tests/render/test_sca_count_consistency.py` -- verifies all SCA count paths produce identical results
- [ ] `tests/render/test_crf_insolvency_suppression.py` -- verifies insolvency CRF suppressed for Altman Z > 3.0
- [ ] `tests/render/test_crf_ceiling_display.py` -- verifies displayed ceiling matches resolved ceiling

## Open Questions

1. **Where does the $383B figure originate?**
   - What we know: It appears in the LLM-generated company narrative. Narrative generator calls Claude Haiku with extracted data.
   - What's unclear: Does the hallucination originate in the LLM prompt data (bad extraction) or in the LLM output (hallucination despite correct data)?
   - Recommendation: Run AAPL pipeline, inspect `narrative_data_sections.py` output for the company section. If data is correct, the fix is post-generation validation. If data is wrong, the fix is in extraction.

2. **What is the DOJ_FCPA misclassification path?**
   - What we know: `_NON_SECURITIES_THEORIES` includes "FCPA" and `_is_regulatory_not_sca` should filter it.
   - What's unclear: Whether the DOJ_FCPA entry enters via `securities_class_actions` (where the filter would catch it) or via a different state path (where no filter runs).
   - Recommendation: Grep AAPL state.json for "FCPA" to find the exact data path.

3. **Is meeting prep LLM-generated or rule-based?**
   - What we know: Two paths exist -- rule-based generators in `meeting_questions*.py` walk AnalysisState; LLM narrative in `narrative_generator.py` may also produce meeting prep content.
   - What's unclear: Which path produces the output the user sees as "generic SCA templates."
   - Recommendation: Check Word renderer (`meeting_prep.py` line 80 -- `state = context["_state"]`) to confirm it uses rule-based generators, then check HTML template for meeting prep section to see if it uses LLM narrative instead.

4. **Does `--fresh` invalidate LLM extraction cache?**
   - What we know: `--fresh` resets stage status. LLM cache in `stages/extract/llm/cache.py` is separate.
   - What's unclear: Whether changed prompts automatically invalidate cached extractions.
   - Recommendation: Check cache key computation in `llm/cache.py` -- if prompt hash is part of the key, prompt changes auto-invalidate.

## Sources

### Primary (HIGH confidence)
- Direct code inspection of 20+ source files in `src/do_uw/stages/` (all findings verified by reading actual code)
- `_is_regulatory_not_sca` filter logic in `red_flag_gates.py` lines 411-490
- SCA status filter variants across 6+ render locations (exact line numbers documented above)
- CRF insolvency suppression in 3 locations: `crf_bar_context.py:54-61`, `assembly_registry.py:57-79`, `sect1_executive_tables.py:363`
- Phase 128 `xbrl_llm_reconciler.py` cross-validation infrastructure

### Secondary (MEDIUM confidence)
- Bug descriptions from phase context (user-reported bugs, not independently verified against current code output)

## Metadata

**Confidence breakdown:**
- SCA count inconsistency (FIX-04): HIGH -- directly observed 4+ divergent filter implementations in code
- CRF insolvency/ceiling (FIX-05): HIGH -- traced 3 suppression locations and ceiling sync path
- LLM hallucination (FIX-01): MEDIUM -- know the narrative generation path but haven't traced exact $383B origin
- Extraction gaps (FIX-02): MEDIUM -- know the extraction code paths but root cause needs pipeline run
- Meeting prep genericity (FIX-03): MEDIUM -- know both generation paths but unclear which produces the user-reported generic output

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable -- bugs are in existing code, not moving targets)
