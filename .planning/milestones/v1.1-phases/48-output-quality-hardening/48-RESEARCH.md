# Phase 48: Output Quality Hardening — Research

**Researched:** 2026-02-26
**Domain:** HTML template rendering, check evaluator value population, brain YAML threshold text, SKIPPED check reduction
**Confidence:** HIGH — all findings verified against source code and actual AAPL state.json

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Source column format:**
- Filing sources: "filing type + date" format — e.g., `10-K 2024-09-28` — plain text, no hyperlinks
- Web sources: "WEB + truncated URL" format — e.g., `WEB (reuters.com/...)` — shows domain for traceability
- SKIPPED rows: leave as "—" (dash) — don't disguise missing data; goal is to reduce SKIPPED, not relabel it
- Always plain text — no hyperlinks in the source cell regardless of URL availability

**Value column content:**
- Numeric checks: raw number, 2 decimal places — e.g., `1.23` for ratios, `12.50` for percentages; units implied by check name
- Boolean/qualitative checks: `True` / `False` — unambiguous, consistent
- Show value even for PASSED checks — reviewers need to verify thresholds weren't just barely missed
- Fix at the evaluator layer — each threshold evaluator type sets `result.value` before returning; not a QA-table-level workaround

**Threshold criterion display:**
- Position: below the finding description as a secondary line
- Style: smaller, muted text — visually secondary, not invisible
- Scope: TRIGGERED findings in the red flags HTML section only — not in the QA audit table
- Backfill required: most checks do not yet have `threshold_context` in brain YAML — this phase must write it for all relevant checks

**SKIPPED reduction strategy:**
- Root cause is unknown — researcher must audit the actual SKIPPED checks on AAPL to categorize (data path gaps vs. brain YAML config gaps vs. legitimately unanswerable)
- Goal: maximize reduction — fix everything that has a fix available, no minimum floor
- Fixes must be general (pipeline-level), not AAPL-specific — improvements apply to all tickers
- Legitimately unanswerable checks stay SKIPPED — never force-pass a check with no data
- Permanently unanswerable checks: flag for deprecation review — add a `deprecation_note` field (or equivalent) to brain YAML and surface the flag in output so future reviews can act on it

### Claude's Discretion
- Exact format for truncating web URLs in the source column (character limit, ellipsis style)
- How to categorize SKIPPED checks during audit (specific categorization taxonomy)
- Brain YAML field name for deprecation flags on unanswerable checks

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QA-01 | QA audit table source column displays the actual filing reference or "WEB (gap)" URL for each evaluated check (fixes template bug: `check.get('filing_ref')` → needs actual date-bearing source) | Filing dates available in `acquired_data.filing_documents`; `_format_trace_source()` provides source type but not date; need `_format_check_source()` helper with filing date lookup |
| QA-02 | QA audit table value column displays the actual datum evaluated for each check (`result.value` is populated for all threshold types, display format must be correct) | Evaluators all set `value=coerce_value(data_value)`; boolean values serialize to `float` via Pydantic coercion (True→1.0, False→0.0); `_group_checks_by_section()` calls `format_adaptive()` on floats showing "1.00" instead of "True" |
| QA-04 | TRIGGERED findings in `red_flags.html.j2` and `qa_audit.html.j2` display the human-readable threshold criterion alongside the finding value | `threshold_context` populated by `_apply_traceability()` after Phase 47; for red flags HTML section: CRF triggers have `condition` text in `red_flags.json`; `extract_scoring()` does not pass it to template |
| QA-05 | Full regression validation on AAPL, RPM, and TSLA confirms: SKIPPED count decreases from baseline 68, TRIGGERED count on AAPL does not increase, output quality approved on human review | AAPL state.json is pre-Phase-47 (no `threshold_context` field); re-run needed; SKIPPED categories: 20 intentionally-unmapped (permanent), 34 DEF14A fixable (Phase 47 schema done), 12 routing-gap (Phase 47 routing done), 2 routing-gap-bucket |
</phase_requirements>

---

## Summary

Phase 48 has four distinct work streams that share the goal of making the HTML worksheet more trustworthy and informative. Each has a specific root cause discovered by inspecting source code and actual AAPL output.

**QA-01 (Source column):** The template uses `check.get('filing_ref')` which IS populated — it's built from `_format_trace_source(trace_data_source)`. The problem is that this function converts source keys like `SEC_10K:balance_sheet` to readable labels like "10-K Balance Sheet" but does NOT include the filing date. The actual filing date is available in `acquired_data.filing_documents[form_type][0]['filing_date']`. Phase 48 must build a date lookup and enrich the source display to produce "10-K 2024-09-28" format.

**QA-02 (Value column):** All threshold evaluators already call `value=coerce_value(data_value)`. The display bug is that boolean check values (`True`/`False`) serialize to `float` (1.0/0.0) via Pydantic v2's `str | float | None` union coercion. The `_group_checks_by_section()` function then calls `format_adaptive(1.0)` → "1.00" instead of "True". The fix is in the formatting layer: detect boolean-origin floats (0.0/1.0 from boolean checks) OR change `coerce_value()` to return `"True"`/`"False"` strings for booleans. The string approach is simpler and cleaner.

**QA-04 (Threshold criterion):** Two separate sub-problems: (a) check-level TRIGGERED findings in the QA audit table — `CheckResult.threshold_context` IS being populated by `_apply_traceability()` after Phase 47, but the `qa_audit.html.j2` template does not render it. (b) CRF-level red flags in `red_flags.html.j2` — these are `RedFlagResult` objects (not `CheckResult`) and use `condition` text from `red_flags.json`. The `extract_scoring()` function builds the template dict but does not pass `condition`. Both templates need updating, and `extract_scoring()` needs to include the `condition` text.

**QA-05 (Regression):** The AAPL state.json is pre-Phase 47 (no `threshold_context` key in serialized check results). A fresh AAPL pipeline run is required to measure the post-Phase-47+48 SKIPPED reduction. Based on Phase 47's population analysis: ~20 intentionally-unmapped checks will remain SKIPPED permanently (Population A), ~34 DEF14A governance checks should now evaluate (Population B, after Phase 47's extraction wiring), ~12 routing-gap checks should now evaluate (Population C+D).

**Primary recommendation:** Implement in four plans: (1) QA-01 source column with filing date lookup, (2) QA-02 boolean value formatting fix, (3) QA-04 threshold criterion rendering in both templates, (4) QA-05 regression run + human review + brain YAML deprecation notes for permanently unanswerable checks.

---

## Standard Stack

### Core

| Component | Purpose | Location |
|-----------|---------|----------|
| `html_checks.py` | `_group_checks_by_section()` — builds check dicts for QA audit template | `src/do_uw/stages/render/html_checks.py` |
| `html_renderer.py` | `build_html_context()` — assembles filing docs, gap_search_summary | `src/do_uw/stages/render/html_renderer.py` |
| `md_renderer_helpers_scoring.py` | `extract_scoring()` — builds red_flags list from `RedFlagResult` | `src/do_uw/stages/render/md_renderer_helpers_scoring.py` |
| `qa_audit.html.j2` | QA audit table template — source + value + status display | `src/do_uw/templates/html/appendices/qa_audit.html.j2` |
| `red_flags.html.j2` | Red flags section template — TRIGGERED finding display | `src/do_uw/templates/html/sections/red_flags.html.j2` |
| `check_helpers.py` | `coerce_value()` — value coercion for CheckResult; target of QA-02 fix | `src/do_uw/stages/analyze/check_helpers.py` |
| `check_engine.py` | `_apply_traceability()` — populates `threshold_context` on TRIGGERED results | `src/do_uw/stages/analyze/check_engine.py` |
| `brain/red_flags.json` | CRF trigger definitions including `condition` text | `src/do_uw/brain/red_flags.json` |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `html_footnotes.py` | `_format_trace_source()` — converts trace_data_source to readable label | Extend for QA-01 date enrichment |
| `formatters_humanize.py` | `format_adaptive()` — numeric formatting called in `_group_checks_by_section()` | Already used; QA-02 adds boolean branch |
| Brain YAML files (`brain/checks/**/*.yaml`) | Source of threshold.red/yellow text populated into `threshold_context` | Audit for deprecation_note additions |

---

## Architecture Patterns

### QA-01: Source Column with Filing Date

The source column currently shows `check.get('filing_ref', '')` from the template. The `filing_ref` key is built in `_group_checks_by_section()` by calling `_format_trace_source(trace_data_source)` which parses `trace_data_source` (e.g., `SEC_10K:balance_sheet`) into a label (e.g., "10-K Balance Sheet") with NO date.

The filing dates ARE in `acquired_data.filing_documents`:
```python
# Structure:
state.acquired_data.filing_documents["10-K"][0]["filing_date"]  # e.g., "2025-10-31"
state.acquired_data.filing_documents["DEF 14A"][0]["filing_date"]  # e.g., "2026-01-08"
```

The source type in `trace_data_source` (SEC_10K, SEC_DEF14A, SEC_10Q, etc.) maps to form type keys in `filing_documents`. The `_SOURCE_LABELS` dict in `html_footnotes.py` already has this mapping:
```python
_SOURCE_LABELS = {
    "SEC_10K": "10-K",
    "SEC_DEF14A": "DEF 14A",
    "SEC_10Q": "10-Q",
    "SEC_8K": "8-K",
    ...
}
```

**Pattern:** Build a `filing_date_lookup` dict from `acquired_data.filing_documents` before calling `_group_checks_by_section()`, pass it to the function, and use it to enrich `filing_ref` with the date. The lookup key is the form type (e.g., `"10-K"` → `"2025-10-31"`). When multiple dates exist (e.g., multiple 10-Qs), use the most recent. The output format is `"10-K 2025-10-31"`.

For web-sourced checks (gap search, `source="WEB (gap)"`): show the source field directly — it already contains "WEB (gap)". For checks where `trace_data_source` is empty or not mappable: fall through to `check.get('source', '—')`.

**Critical path:** `build_html_context()` → `_group_checks_by_section(check_results, filing_date_lookup)` → `filing_ref = _format_check_source(trace_src, source_raw, filing_date_lookup)`. The function signature must remain compatible with its test expectations.

### QA-02: Boolean Value Formatting

**Root cause:** `coerce_value(True)` in `check_helpers.py` returns `True` (Python bool). Pydantic v2's `value: str | float | None` field coerces Python `bool` → `float` at model validation time (since `bool` is a subtype of `int` which is promoted to float in the `str | float | None` union). Result: `CheckResult.value = 1.0` for boolean TRIGGERED, `0.0` for CLEAR.

When `state.json` is deserialized: `json.loads()` converts JSON `1.0` → Python `float(1.0)`. The `_group_checks_by_section()` function then calls `format_adaptive(1.0)` → `"1.00"`.

**Fix option A (recommended):** Modify `coerce_value()` to handle booleans explicitly:
```python
def coerce_value(data_value: Any) -> str | float | None:
    if isinstance(data_value, bool):  # MUST check bool before int/float (bool is int subtype)
        return "True" if data_value else "False"
    if isinstance(data_value, (str, int, float)):
        return data_value
    if data_value is None:
        return None
    return str(data_value)
```
This ensures booleans are stored as string `"True"`/`"False"` in `CheckResult.value`, which serializes correctly as JSON strings and displays correctly in the template.

**Fix option B (alternative):** Modify `_group_checks_by_section()` to detect `raw_val in (0.0, 1.0)` and check if the check's source is a boolean check. This is fragile — a real ratio of 1.0 would incorrectly show "True".

**Option A is strictly correct.** The `bool` check must come before the `(str, int, float)` check because `isinstance(True, int)` returns `True`.

**Note on regression impact:** Changing `coerce_value()` affects all evaluators. Currently 2 checks use boolean thresholds. Verify that numeric checks (e.g., `value=1.0` for a ratio of exactly 1.0) are NOT affected — they would pass `isinstance(1.0, bool)` as False (floats are not bools), so they're safe.

### QA-04: Threshold Criterion Display

**Sub-problem A: QA audit table (`qa_audit.html.j2`)**

After Phase 47, `CheckResult.threshold_context` is populated for TRIGGERED checks by `_apply_traceability()`. The `_group_checks_by_section()` function already passes `threshold_context` indirectly via the `result_data` dict... but it does NOT include `threshold_context` in the grouped check dict. The template cannot access it.

Fix: Add `"threshold_context": result_data.get("threshold_context", "")` to the dict built in `_group_checks_by_section()`. Then update `qa_audit.html.j2` to show it as a secondary line below the finding.

**However:** The CONTEXT.md specifies threshold criterion display "in the red flags HTML section only — NOT in the QA audit table." So the QA audit template change may not be needed per the locked decisions. The QA-04 requirement text says "red_flags.html.j2 and qa_audit.html.j2" but the CONTEXT.md locked scope to red_flags only. Follow the CONTEXT.md locked decisions — skip `qa_audit.html.j2` modification.

**Sub-problem B: Red flags section (`red_flags.html.j2`)**

The `red_flags.html.j2` template is fed by `extract_scoring()` which builds this dict for each triggered CRF flag:
```python
{
    "id": rf.flag_id,
    "name": rf.flag_name or rf.flag_id,
    "description": "; ".join(rf.evidence) if rf.evidence else "",
    "ceiling": str(rf.ceiling_applied) if rf.ceiling_applied else "N/A",
    "max_tier": rf.max_tier or "N/A",
}
```

The `condition` text from `red_flags.json` (e.g., `"Company has pending securities class action lawsuit"`) is the human-readable criterion. It's NOT included in the current dict.

Fix: Load `red_flags.json` in `extract_scoring()` to build a `crf_conditions` lookup dict (`{crf_id: condition_text}`), then add `"threshold_context": crf_conditions.get(rf.flag_id, "")` to the red_flag dict.

The `red_flags.html.j2` template currently uses:
```jinja2
<td class="px-3 py-2 text-xs">{{ flag.get('description', '—') }}</td>
```

Add a secondary line for `threshold_context`:
```jinja2
<td class="px-3 py-2 text-xs">
  {{ flag.get('description', '—') }}
  {% if flag.get('threshold_context') %}
  <br><span class="text-xs text-gray-400">{{ flag.get('threshold_context') }}</span>
  {% endif %}
</td>
```

**Note on `red_flags.json` loading:** `extract_scoring()` in `md_renderer_helpers_scoring.py` already loads `risk_model.yaml` using a similar pattern (try/except import yaml). Use the same pattern for `red_flags.json` via `json.load()` — simpler (no yaml dependency). The brain directory path is `Path(__file__).parent.parent.parent / "brain" / "red_flags.json"`.

### QA-05: SKIPPED Reduction Audit

**Current SKIPPED population (AAPL, pre-Phase-47, 68 total):**

| Category | Count | Examples | Phase 48 Action |
|----------|-------|---------|-----------------|
| Population A: Intentionally unmapped (external APIs, proprietary) | ~20 | FWRD.WARN.* (13 checks), EXEC.CEO/CFO.risk_score, NLP.FILING.* (2), GOV.EFFECT.iss_score/proxy_advisory | Add `deprecation_note` to brain YAML; stays SKIPPED |
| Population B: DEF14A fixable (Phase 47 schema done) | ~34 | GOV.BOARD.attendance/diversity/meetings (3 new fields), GOV.PAY.*/GOV.RIGHTS.*/GOV.EFFECT.*/GOV.INSIDER.* | Verify with fresh pipeline run; should evaluate after Phase 47 |
| Population C: Routing gaps (Phase 47 routing done) | ~12 | BIZ.DEPEND.labor, BIZ.STRUCT.vie_spe, FIN.ACCT.restatement_*, LIT.DEFENSE.forum_selection, LIT.PATTERN.peer_contagion, LIT.SECTOR.regulatory_databases | Verify with fresh pipeline run; should evaluate |
| Population D: FWRD.DISC.sec_comment_letters, FIN.QUALITY.deferred_revenue_trend, FIN.QUALITY.q4_revenue_concentration | ~3 | — | Investigate; may be fixable data path issues |

**Phase 48 SKIPPED work:** After a fresh AAPL run post-Phase-47, measure actual SKIPPED count. If still > 22, audit which checks are still SKIPPING and trace root cause (data unavailable vs. routing error vs. evaluator issue). Fix any remaining fixable ones. Add `deprecation_note` to brain YAML for confirmed-permanent Population A checks.

**Deprecation note field for brain YAML:** Suggested field name: `deprecation_note: str | null` (plain text). This follows the established `provenance:` block pattern in brain YAML. Example:
```yaml
- id: FWRD.WARN.glassdoor_sentiment
  ...
  deprecation_note: "Requires Glassdoor API access — not available via SEC filings or standard web search. Consider reformulating as a disclosure check."
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filing date lookup | Custom date resolver | Index from `acquired_data.filing_documents` | Already structured with `filing_date` field per form type |
| CRF condition text | Duplicate condition in multiple places | Read from `src/do_uw/brain/red_flags.json` | Single source of truth, already has `condition` field |
| Boolean value display | Check-specific formatting | Fix `coerce_value()` once | Propagates to all evaluators automatically |
| Threshold text backfill | New brain YAML field | Read from existing `threshold.red/yellow` text | Phase 47 already wired `_apply_traceability()` to read it |

---

## Common Pitfalls

### Pitfall 1: Filing Date Lookup Key Mismatch

**What goes wrong:** `trace_data_source` uses keys like `SEC_10K`, `SEC_DEF14A`. `filing_documents` uses keys like `"10-K"`, `"DEF 14A"`. The `_SOURCE_LABELS` dict maps between them. If the lookup uses the wrong key format, all source cells show "—".

**How to avoid:** Use `_SOURCE_LABELS` from `html_footnotes.py` to convert `SEC_10K` → `"10-K"` before looking up in `filing_date_lookup`. Or build the lookup indexed by both formats.

**Warning signs:** All source cells show "—" despite filing dates being in state.

### Pitfall 2: Boolean-Before-Int Order in coerce_value()

**What goes wrong:** `isinstance(True, int)` returns `True` in Python (because `bool` is a subclass of `int`). If the bool check comes AFTER the `isinstance(data_value, (str, int, float))` check, booleans still get returned as-is (as Python bools), which Pydantic then coerces to float.

**How to avoid:** Always check `isinstance(data_value, bool)` FIRST before `isinstance(data_value, (str, int, float))`.

### Pitfall 3: QA Audit Template Shows threshold_context Despite CONTEXT.md Scoping

**What goes wrong:** QA-04 requirement text says "red_flags.html.j2 AND qa_audit.html.j2" but the CONTEXT.md locked decisions say "TRIGGERED findings in the red flags HTML section only — not in the QA audit table." The planner should follow the CONTEXT.md locked decision.

**How to avoid:** Add `threshold_context` to the grouped check dict for potential future use, but do NOT render it in `qa_audit.html.j2`. Only render it in `red_flags.html.j2`.

### Pitfall 4: SKIPPED Population B Checks Still SKIP After Phase 47

**What goes wrong:** Phase 47 added extraction schema fields and wired the mapper, but the DEF 14A text may not contain the new fields for all companies. The LLM extraction prompt must be enhanced to look for the new fields. If the LLM doesn't extract them, `DEF14AExtraction.board_attendance_pct` remains `None`, and GOV.BOARD.attendance still SKIPs.

**How to avoid:** After Phase 47's schema additions, re-run AAPL and inspect whether GOV.BOARD.attendance and friends evaluate. If they still SKIP, the issue is the LLM prompt not extracting these fields — the extraction hints may need updating in the brain YAML or LLM prompt.

### Pitfall 5: Stale AAPL State for Regression Testing

**What goes wrong:** The AAPL state.json at `output/AAPL-2026-02-25/state.json` predates Phase 47. Using it for Phase 48 regression testing will show `threshold_context` missing, SKIPPED=68 (not reduced), and no confidence/threshold_context fields on check results. This is not a Phase 48 regression failure — it's a stale state.

**How to avoid:** QA-05 requires a FRESH AAPL pipeline run. The test should run `do-uw run AAPL` and then inspect the fresh output, not the cached state.

---

## Code Examples

### QA-01: Building Filing Date Lookup

```python
# In html_renderer.py build_html_context() — before calling _group_checks_by_section()
def _build_filing_date_lookup(state: AnalysisState) -> dict[str, str]:
    """Build {form_label: filing_date} lookup from acquired filing documents.

    Form labels match _SOURCE_LABELS values: "10-K", "DEF 14A", "10-Q", etc.
    Uses the most recent document for each form type (index [0] is most recent
    as returned by EdgarTools in reverse chronological order).
    """
    lookup: dict[str, str] = {}
    if not state.acquired_data or not state.acquired_data.filing_documents:
        return lookup
    for form_type, docs in state.acquired_data.filing_documents.items():
        if isinstance(docs, list) and docs:
            date = docs[0].get("filing_date", "")
            if date:
                lookup[form_type] = date  # form_type is already "10-K", "DEF 14A", etc.
    return lookup
```

```python
# In html_checks.py _group_checks_by_section() — enrich filing_ref with date
def _format_check_source(
    trace_data_source: str,
    raw_source: str,
    filing_date_lookup: dict[str, str],
) -> str:
    """Format source column for QA audit table.

    Priority:
    1. WEB (gap) sources → show raw_source directly
    2. trace_data_source → parse form type, look up date → "10-K 2024-09-28"
    3. Fallback → raw_source or "—"
    """
    if raw_source and raw_source.startswith("WEB"):
        # Gap search results — show domain truncated
        return raw_source[:40]

    if trace_data_source:
        # Parse first source from trace_data_source (e.g., "SEC_10K:balance_sheet")
        first_chunk = trace_data_source.split(";")[0].strip()
        if ":" in first_chunk:
            src_key = first_chunk.split(":")[0].strip()
        else:
            src_key = first_chunk
        label = _SOURCE_LABELS.get(src_key, "")
        if label and label in filing_date_lookup:
            return f"{label} {filing_date_lookup[label]}"
        elif label:
            return label  # Date not available, show type only

    return raw_source or "—"
```

### QA-02: Fixed coerce_value()

```python
def coerce_value(data_value: Any) -> str | float | None:
    """Coerce a data value to a type CheckResult.value accepts.

    bool MUST be checked before (str, int, float) because bool is a
    subclass of int in Python — isinstance(True, int) == True.
    """
    if isinstance(data_value, bool):  # bool before int — order matters
        return "True" if data_value else "False"
    if isinstance(data_value, (str, int, float)):
        return data_value
    if data_value is None:
        return None
    return str(data_value)
```

### QA-04: extract_scoring() with threshold_context for CRF flags

```python
# In md_renderer_helpers_scoring.py extract_scoring()

def _load_crf_conditions() -> dict[str, str]:
    """Load CRF condition text from red_flags.json for threshold_context display."""
    import json
    from pathlib import Path
    rf_path = Path(__file__).parent.parent.parent / "brain" / "red_flags.json"
    try:
        data = json.loads(rf_path.read_text())
        triggers = data.get("escalation_triggers", [])
        return {
            t["id"]: t.get("condition", "")
            for t in triggers
            if "id" in t
        }
    except Exception:
        return {}

# In extract_scoring(), in the "Red flags" section:
crf_conditions = _load_crf_conditions()
red_flags = [
    {
        "id": rf.flag_id,
        "name": rf.flag_name or rf.flag_id,
        "description": "; ".join(rf.evidence) if rf.evidence else "",
        "ceiling": str(rf.ceiling_applied) if rf.ceiling_applied else "N/A",
        "max_tier": rf.max_tier or "N/A",
        "threshold_context": crf_conditions.get(rf.flag_id, ""),  # NEW
    }
    for rf in sc.red_flags
    if rf.triggered
]
```

### QA-04: Updated red_flags.html.j2 (threshold_context display)

```jinja2
{% for flag in sorted_flags %}
<tr class="bg-red-50">
  <td class="px-3 py-2">{{ traffic_light("TRIGGERED", "TRIGGERED") }}</td>
  <td class="px-3 py-2 font-semibold text-xs">{{ flag.get('name', flag.get('id', '—')) }}</td>
  <td class="px-3 py-2 text-xs">
    {{ flag.get('description', '—') }}
    {% if flag.get('threshold_context') %}
    <br><span class="text-gray-400 text-xs italic">{{ flag.get('threshold_context') }}</span>
    {% endif %}
  </td>
  <td class="px-3 py-2 text-xs text-gray-500">
    {% set ceil = flag.get('ceiling', '') %}
    {{ ('Ceiling: ' ~ ceil) if ceil and ceil != 'N/A' else '—' }}
  </td>
</tr>
{% endfor %}
```

### Brain YAML deprecation_note pattern

```yaml
- id: FWRD.WARN.glassdoor_sentiment
  name: Glassdoor Sentiment Trend
  ...
  deprecation_note: >
    Requires Glassdoor API access not available via SEC filings or standard web search.
    Consider reformulating as a disclosure check: "Does management discuss employee
    satisfaction risks in 10-K risk factors?" (always answerable from filing text).
  gap_bucket: intentionally-unmapped
  ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Source column shows `—` for all non-web checks | Source column shows "10-K Balance Sheet" (from `_format_trace_source()`) | Phase 43 | Partial improvement; date missing |
| `threshold_context` did not exist on CheckResult | `threshold_context: str = Field(default="")` on CheckResult, populated by `_apply_traceability()` | Phase 47 | Wiring exists; templates need updating |
| All check values displayed as raw | `format_adaptive()` applied to floats in `_group_checks_by_section()` | Phase 43 | Boolean coercion bug introduced |

---

## Open Questions

1. **Will Population B checks (GOV.BOARD.*) actually evaluate after a fresh AAPL run?**
   - What we know: Phase 47 wired `convert_board_profile()` and `map_governance_fields()` for board_attendance, board_meetings, board_diversity. The LLM extraction prompt receives the DEF 14A text.
   - What's unclear: Does the LLM extraction actually extract these fields from AAPL's proxy? If not, the extraction schema fields remain None and checks still SKIP.
   - Recommendation: The first task in Phase 48 should be a fresh AAPL run to measure actual post-Phase-47 SKIPPED count before any Phase 48 coding.

2. **Should `threshold_context` be rendered in `qa_audit.html.j2` for TRIGGERED rows?**
   - The CONTEXT.md locked decision says "red flags HTML section only — NOT in the QA audit table."
   - The QA-04 requirement says "red_flags.html.j2 and qa_audit.html.j2."
   - Recommendation: Follow CONTEXT.md (locked decisions override requirement text when they conflict). Add `threshold_context` to the grouped dict for completeness, but do not render it in the QA audit table.

3. **What is the correct URL truncation format for WEB sources?**
   - CONTEXT.md marks this as Claude's discretion.
   - Recommendation: Domain + path truncated to 35 characters. Format: `WEB (domain.com/path...)`. Example: `WEB (reuters.com/tech/apple-...)`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/stages/analyze/ tests/stages/render/ -q` |
| Full suite command | `uv run pytest tests/ -q` |
| Estimated runtime | ~3 minutes (176s observed) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QA-01 | Source column shows "10-K 2024-09-28" format for evaluated checks | unit | `uv run pytest tests/render/test_qa_audit_source.py -x` | Wave 0 gap |
| QA-02 | Boolean check values display as "True"/"False" not "1.00"/"0.00" | unit | `uv run pytest tests/stages/analyze/test_check_evaluators.py -x` | Partial — extend existing |
| QA-04 | red_flags.html.j2 renders threshold_context for triggered CRF flags | unit | `uv run pytest tests/render/test_red_flags_template.py -x` | Wave 0 gap |
| QA-05 | AAPL SKIPPED count < 68 after fresh run; TRIGGERED count = 24 (baseline) | integration | `uv run pytest tests/stages/analyze/test_regression_baseline.py -x` | Exists — update thresholds |

### Nyquist Sampling Rate

- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/stages/analyze/ tests/stages/render/ -q`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green (3967+ pass, 2 pre-existing failures OK) before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** ~30 seconds (targeted test subset)

### Wave 0 Gaps (must be created before implementation)

- [ ] `tests/render/test_qa_audit_source.py` — tests for QA-01 source column format: `_format_check_source()` with filing date lookup, WEB source passthrough, no-date fallback
- [ ] `tests/render/test_red_flags_template.py` — tests for QA-04 `threshold_context` in red_flags dict from `extract_scoring()`, Jinja2 template rendering
- [ ] `tests/stages/analyze/test_coerce_value_boolean.py` — tests for QA-02 bool handling in `coerce_value()`

*(Note: `tests/stages/analyze/test_threshold_context.py` already exists and covers Phase 47 CheckResult field wiring — no change needed)*

---

## Sources

### Primary (HIGH confidence)

- Source code inspection: `src/do_uw/stages/render/html_checks.py` — `_group_checks_by_section()` confirmed
- Source code inspection: `src/do_uw/stages/render/html_footnotes.py` — `_format_trace_source()` and `_SOURCE_LABELS` confirmed
- Source code inspection: `src/do_uw/stages/render/md_renderer_helpers_scoring.py` — `extract_scoring()` red_flags dict structure confirmed
- Source code inspection: `src/do_uw/stages/analyze/check_helpers.py` — `coerce_value()` bool handling gap confirmed
- Source code inspection: `src/do_uw/stages/analyze/check_engine.py` — `_apply_traceability()` threshold_context population confirmed (Phase 47)
- State inspection: `output/AAPL-2026-02-25/state.json` — all 24 TRIGGERED checks confirmed with `threshold_context` key missing (pre-Phase-47 state)
- State inspection: `output/AAPL-2026-02-25/state.json` — GOV.BOARD.ceo_chair value=1.0 (float) confirmed as boolean coercion issue
- Brain data: `src/do_uw/brain/red_flags.json` — `condition` field confirmed on all 17 CRF triggers
- Template inspection: `src/do_uw/templates/html/appendices/qa_audit.html.j2` — `check.get('filing_ref')` confirmed; no threshold_context rendering
- Template inspection: `src/do_uw/templates/html/sections/red_flags.html.j2` — no threshold_context rendering; uses `flag.get('description')` only
- Phase 47 VERIFICATION.md — Population A/B/C/D classification confirmed; 20 intentionally-unmapped, 34 DEF14A fixable, 12 routing-gap
- Test suite: `uv run pytest tests/ -q` — 3967 pass, 2 pre-existing failures confirmed baseline

### Secondary (MEDIUM confidence)

- Phase 47 SUMMARY.md plans 01-04 — confirms Phase 47 scope and what was completed
- Phase 47 CONTEXT.md — confirms QA-03 (threshold_context field) completed in Phase 47

---

## Metadata

**Confidence breakdown:**
- QA-01 source column: HIGH — root cause confirmed in source code; filing dates confirmed in state
- QA-02 boolean values: HIGH — Pydantic coercion behavior confirmed; `coerce_value()` gap confirmed
- QA-04 threshold criterion: HIGH — `extract_scoring()` code confirmed; CRF `condition` text confirmed
- QA-05 SKIPPED audit: MEDIUM — Phase 47 population classifications confirmed; actual post-Phase-47 SKIPPED count unknown until fresh run

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable — no external dependencies; all findings are internal code analysis)
