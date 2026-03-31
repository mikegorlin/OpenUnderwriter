# Phase 47: Check Data Mapping Completeness - Research

**Researched:** 2026-02-25
**Domain:** Python codebase internal — check routing, DEF 14A LLM extraction, Pydantic model extension, brain YAML authoring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Threshold context display**
- QA audit table: full criterion text (e.g., "red: Prior SEC enforcement action within 5 years")
- HTML worksheet: footnote-style — triggered findings get a reference mark; criterion text collected at section end
- Word doc: inline parenthetical (e.g., "CFO departure (red: executive departure within 6 months of inquiry)") — python-docx footnotes are too complex
- Source of truth: brain YAML `threshold.red` / `threshold.yellow` fields, read at evaluation time and stored on `CheckResult.threshold_context`
- Evaluator populates `threshold_context` when a check triggers; downstream render uses it

**DEF 14A missing field handling**
- Default behavior: populate field with `None` / Not Available — never skip the field entirely
- Downstream check evaluates to SKIPPED (no data) when field is None — this is honest
- Extraction success = non-null value extracted (any value, not a sanity-checked value)
- 80% success rate target applies per field across AAPL, RPM, TSLA
- Extraction method: LLM-assisted extraction (not regex) — proxy formats vary too much
- DEF 14A acquisition: Phase 47 is self-contained — include an explicit acquisition step to fetch DEF 14A filings for AAPL, RPM, TSLA if not cached

**Bucket-a routing fix approach**
- Strategy: audit-first — use Phase 46's bucket classification as the starting task list
- Re-audit required: re-run the Phase 46 gap search tool on the current codebase before beginning routing work; fresh classification supersedes Phase 46's output
- Routing entries live in brain YAML files — each check's YAML gets a `field_for_check` entry, then `brain build` regenerates
- Never add routing entries to `config/` files — brain YAMLs are the canonical check knowledge store

**Regression safety bar**
- Zero tolerance: any new TRIGGERED finding on AAPL compared to baseline = phase failure
- Baseline snapshot: run analysis on AAPL, RPM, TSLA before any Phase 47 changes; record TRIGGERED counts per company
- End-of-phase comparison: post-change counts must not exceed baseline on AAPL
- A new routing entry that causes a check to trigger on AAPL means the mapping is wrong or the threshold needs adjustment — must be fixed before the phase closes
- RPM and TSLA may legitimately gain new triggers from newly-routed data (routing gap fixed → data flows → check evaluates correctly)

### Claude's Discretion
- Exact LLM prompt design for DEF 14A extraction
- How to handle split proxy filings (DEF 14A + DEF 14A/A)
- Order of operations within plans (bucket-a first vs interleaved with bucket-b)
- Exact format of footnote reference marks in HTML (numbers, symbols, etc.)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MAP-01 | System adds FIELD_FOR_CHECK routing entries for all bucket-a checks (~40) where structured field data exists in ExtractedData but routing entry is missing, reducing SKIPPED count | Re-audit shows 17 "Data mapping not configured" checks + 42 checks with routing but None data. Actual bucket-a population confirmed by re-running gap_searcher._load_gap_eligible_checks() |
| MAP-02 | System adds extraction logic for bucket-b checks (~28) where required data exists in source filings but no extractor reads it into ExtractedData | Research confirms 9 checks have no routing (EXEC.PROFILE.*, FIN.QUALITY.*, FWRD.DISC.*, NLP.FILING.*) and 7+ mapper files return `None` as placeholder for unextracted fields |
| MAP-03 | System expands DEF 14A LLM extraction schema (DEF14AExtraction) to include board diversity, director tenure, expertise, and attendance fields; validated against AAPL, RPM, and TSLA | DEF14AExtraction already has `directors` list with `tenure_years`, `qualifications` per director. Missing: board_gender_diversity_pct, board_racial_diversity_pct, board_attendance_pct, board_meetings_count. convert_board_profile() in llm_governance.py is the downstream converter |
| QA-03 | CheckResult model gains a threshold_context field populated from brain check's threshold YAML at evaluation time in _apply_traceability() | CheckResult model is in check_results.py; BrainCheckThreshold schema already has red/yellow/clear string fields; _apply_traceability() in check_engine.py is the right injection point |
</phase_requirements>

---

## Summary

Phase 47 is a pure routing and extraction completeness phase — no new pipeline stages, no new acquisition. The 68 SKIPPED checks observed at runtime on AAPL break into three distinct populations that each need a different fix:

**Population 1 — "Data mapping not configured" (17 checks):** These checks have neither a `FIELD_FOR_CHECK` entry nor a `data_strategy.field_key` in their brain YAML. They return an empty dict from `map_check_data()`, causing `_determine_data_status()` to set `data_status_reason="Data mapping not configured for this check"`. Population: `EXEC.CEO.risk_score`, `EXEC.CFO.risk_score`, `FWRD.NARRATIVE.*` (2), `FWRD.WARN.*` (13 sentiment/ops checks). Fix: add `FIELD_FOR_CHECK` entries in `check_field_routing.py` (or `field_for_check` in brain YAML), or formally classify these as intentionally-unmapped.

**Population 2 — "Required data not available" with existing routing (42 checks):** These checks HAVE routing in `FIELD_FOR_CHECK` and the mappers DO build the result dict, but the target field is set to `None` explicitly in the mapper code (e.g., `result["board_attendance"] = None  # Not yet on BoardProfile`). Fix: either populate the field from DEF 14A extraction (bucket-b extraction work) or accept as intentionally-unmapped.

**Population 3 — "Required data not available" without routing (9 checks):** No `FIELD_FOR_CHECK` entry AND no mapper produces these fields. These are `EXEC.PROFILE.avg_tenure`, `EXEC.PROFILE.board_size`, `EXEC.PROFILE.independent_ratio`, `EXEC.PROFILE.overboarded_directors`, `FIN.QUALITY.deferred_revenue_trend`, `FIN.QUALITY.q4_revenue_concentration`, `FWRD.DISC.sec_comment_letters`, `NLP.FILING.filing_timing_change`, `NLP.FILING.late_filing`.

The DEF 14A extraction work (MAP-03) is the highest-leverage bucket: the `DEF14AExtraction` schema is already capable (it has `directors` with `tenure_years`, `qualifications`, `committees`), but `convert_board_profile()` in `llm_governance.py` doesn't yet map board attendance or expertise into `GovernanceData`, and `DEF14AExtraction` itself is missing `board_gender_diversity_pct`, `board_racial_diversity_pct`, `board_attendance_pct`, and `board_meetings_count` as first-class schema fields.

The `threshold_context` field (QA-03) requires a one-line addition to `CheckResult` in `check_results.py` and a 3-5 line change to `_apply_traceability()` in `check_engine.py` — it must be populated at TRIGGERED time from the brain check's `threshold.red` / `threshold.yellow` text.

**Primary recommendation:** Execute in four plans: (1) re-audit + baseline snapshot, (2) bucket-a routing fixes (FIELD_FOR_CHECK + brain YAML field_for_check entries), (3) DEF 14A schema expansion + extraction population, (4) threshold_context field + regression verification.

---

## Standard Stack

### Core (in-project, no new dependencies)
| Component | Location | Purpose | Pattern |
|-----------|----------|---------|---------|
| `CheckResult` | `src/do_uw/stages/analyze/check_results.py` | Pydantic model for check outcome | Add `threshold_context: str = Field(default="")` |
| `_apply_traceability()` | `src/do_uw/stages/analyze/check_engine.py` | Populates 5 traceability links | Inject threshold_context from `check.get("threshold", {}).get("red"/"yellow")` when TRIGGERED |
| `FIELD_FOR_CHECK` | `src/do_uw/stages/analyze/check_field_routing.py` | check_id → ExtractedData field mapping | Add entries for checks that lack routing |
| `DEF14AExtraction` | `src/do_uw/stages/extract/llm/schemas/def14a.py` | Pydantic schema for proxy LLM extraction | Add `board_gender_diversity_pct`, `board_racial_diversity_pct`, `board_attendance_pct`, `board_meetings_count` |
| `convert_board_profile()` | `src/do_uw/stages/extract/llm_governance.py` | DEF14AExtraction → BoardProfile | Populate `board_attendance` and `board_expertise` in GovernanceData |
| Brain YAML files | `src/do_uw/brain/checks/**/*.yaml` | Per-check metadata store | Add `field_for_check` field; run `brain build` after edits |
| `brain build` | CLI command | Rebuild brain.duckdb from YAML | `uv run do-uw brain build` |

### Supporting
| Component | Location | Purpose |
|-----------|----------|---------|
| `gap_searcher._load_gap_eligible_checks()` | `src/do_uw/stages/acquire/gap_searcher.py` | Re-audit tool: reads gap_bucket from YAML files | Use for re-audit step |
| `map_governance_fields()` | `src/do_uw/stages/analyze/check_mappers_sections.py` | Governance mapper — many `None` placeholders here | These None placeholders are the exact extraction gaps |
| `GovernanceData`, `BoardProfile` | `src/do_uw/models/governance.py` | Domain model holding governance facts | Existing fields `board_attendance`, `board_expertise` missing from `BoardProfile` |
| `AnalysisCache` (SQLite) | `src/do_uw/cache/sqlite_cache.py` | Cache for LLM extraction and web search results | DEF 14A acquisition checks cache before re-fetching |

---

## Architecture Patterns

### Pattern 1: brain YAML field_for_check (Preferred for bucket-a)

The most correct approach for routing-gap checks is to add `field_for_check` directly to the check's brain YAML rather than `FIELD_FOR_CHECK` in `check_field_routing.py`. The `data_strategy.field_key` in the YAML takes priority over `FIELD_FOR_CHECK` (see `narrow_result()` resolution order).

```python
# narrow_result() resolution order in check_field_routing.py:
# 1. data_strategy.field_key from check definition (Phase 31 declarative) — PREFERRED
# 2. Exact check_id match in FIELD_FOR_CHECK (legacy)
# 3. Fallback: return full data dict
```

YAML pattern:
```yaml
- id: GOV.BOARD.attendance
  # ... existing fields ...
  data_strategy:
    field_key: board_attendance    # THIS is the routing entry
    primary_source: SEC_DEF14A
```

After editing brain YAML: `uv run do-uw brain build` regenerates `brain.duckdb`. The checks.json also gets regenerated — both must stay in sync (validated by `_validate_yaml_json_sync()` in `brain_build_checks.py`).

### Pattern 2: FIELD_FOR_CHECK legacy entry (for quick routing without YAML edit)

For checks that already have `data_strategy` in their YAML (many GOV/LIT checks already do), adding an entry to `FIELD_FOR_CHECK` in `check_field_routing.py` is faster but less canonical. Use YAML for canonical fix, `FIELD_FOR_CHECK` as quick validation step.

```python
# In src/do_uw/stages/analyze/check_field_routing.py
FIELD_FOR_CHECK: dict[str, str] = {
    # ... existing entries ...
    # New entries for routing-gap checks:
    "GOV.BOARD.attendance": "board_attendance",
    "GOV.EFFECT.late_filing": "late_filing_flag",
}
```

### Pattern 3: Mapper None → populated field (bucket-b extraction)

The 42 "data available" routing entries have mapper-side None placeholders:
```python
# In check_mappers_sections.py:
result["board_attendance"] = None  # Not yet on BoardProfile
result["board_expertise"] = None  # Not yet on BoardProfile
result["late_filing_flag"] = None  # Not yet extracted
result["nt_filing_flag"] = None  # Not yet extracted
```

The fix for each: populate from DEF14AExtraction via llm_governance conversion. Pattern:
```python
# In llm_governance.convert_board_profile():
# 1. Extract board_attendance_pct from DEF14AExtraction.board_attendance_pct
# 2. Create SourcedValue[float] with Confidence.HIGH
# 3. Store on BoardProfile.board_attendance_pct (new field)

# In check_mappers_sections.map_governance_fields():
# 4. result["board_attendance"] = _safe_sourced(gov.board.board_attendance_pct)
```

### Pattern 4: threshold_context injection in _apply_traceability()

```python
# In check_engine._apply_traceability():
def _apply_traceability(result: CheckResult, check: dict[str, Any], ttype: str) -> CheckResult:
    # ... existing 5-link logic ...

    # QA-03: Populate threshold_context when check triggers
    if result.status == CheckStatus.TRIGGERED:
        threshold = check.get("threshold", {})
        level = result.threshold_level  # "red" or "yellow"
        criterion = threshold.get(level) if level else None
        if criterion:
            result.threshold_context = f"{level}: {criterion}"

    return result
```

The `BrainCheckThreshold.red` and `.yellow` fields in `brain_check_schema.py` are `str | None` — they already hold the human-readable criterion text (e.g., "Average tenure >15 years (entrenchment risk)").

### Pattern 5: DEF14AExtraction schema expansion

New fields to add to `DEF14AExtraction` in `def14a.py`:
```python
# Board diversity (new — not in ExtractedDirector)
board_gender_diversity_pct: float | None = Field(
    default=None,
    description="Percentage of female directors on the board (0-100)",
)
board_racial_diversity_pct: float | None = Field(
    default=None,
    description="Percentage of racially/ethnically diverse directors (0-100)",
)

# Board meeting attendance
board_meetings_held: int | None = Field(
    default=None,
    description="Total board meetings held during the fiscal year",
)
board_attendance_pct: float | None = Field(
    default=None,
    description="Aggregate attendance percentage across all directors (0-100)",
)
directors_below_75_pct_attendance: int | None = Field(
    default=None,
    description="Number of directors who attended less than 75% of meetings",
)
```

Note: `ExtractedDirector` already has `tenure_years`, `qualifications`, `committees`, `other_boards`. The expertise/skills matrix is derivable from director qualifications text. Individual `tenure_years` per director is already available — `convert_board_profile()` already computes `avg_tenure` from this list.

### Pattern 6: Regression baseline snapshot

Before making any routing changes, capture baseline:
```python
# Programmatic baseline approach:
import json
with open("output/AAPL-2026-02-25/state.json") as f:
    state = json.load(f)

baseline = {
    "AAPL": {
        "triggered": len([cr for cr in state["analysis"]["check_results"].values()
                         if cr["status"] == "TRIGGERED"]),
        "skipped": len([cr for cr in state["analysis"]["check_results"].values()
                       if cr["status"] == "SKIPPED"]),
    }
}
# Save as .planning/phases/47-check-data-mapping-completeness/47-baseline.json
```

### Recommended Phase Structure

```
plans/
  47-01-PLAN.md  — Re-audit + baseline snapshot
  47-02-PLAN.md  — bucket-a routing fixes (FIELD_FOR_CHECK + brain YAML data_strategy)
  47-03-PLAN.md  — DEF 14A schema expansion + llm_governance converter update
  47-04-PLAN.md  — threshold_context (QA-03) + final regression verification
```

### Anti-Patterns to Avoid

- **Never add routing to config/ files:** Brain YAML is the canonical store. Any `check_id: {field: value}` entries in `config/` violate the architecture.
- **Never write a new gap_bucket classification from scratch:** The Phase 46 brain YAML `gap_bucket` fields ARE the classification. Re-run `_load_gap_eligible_checks()` to see current state.
- **Never set a TRIGGERED result without a reason:** When routing-gap checks now evaluate (and might trigger on RPM/TSLA), the threshold_context field must be populated — don't add routing without also verifying the threshold criterion is readable.
- **Never populate a field with a value that bypasses the None sentinel:** `map_governance_fields()` explicitly sets `board_attendance = None` to signal DATA_UNAVAILABLE. Once DEF 14A extraction populates this, the None will correctly become non-None only when the proxy discloses attendance data.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gap bucket re-audit | New classifier script | `gap_searcher._load_gap_eligible_checks()` | Already reads brain YAML gap_bucket fields correctly |
| threshold_context text | Custom threshold parser | `check.get("threshold", {}).get("red")` | BrainCheckThreshold.red is already the human-readable string |
| DEF 14A field extraction | Custom regex parser | Extend `DEF14AExtraction` schema + LLM extraction | Proxy formats vary too much; LLM is the locked decision |
| Regression validation | Manual count comparison | JSON snapshot comparison | Programmatic is unambiguous per the specifics in CONTEXT.md |

**Key insight:** Every pattern needed here is an extension of existing machinery, not a new capability. The routing system, LLM extraction, brain YAML, and traceability chain all exist and just need new entries or fields.

---

## Common Pitfalls

### Pitfall 1: Routing gap vs extraction gap confusion
**What goes wrong:** A check has `FIELD_FOR_CHECK` entry AND the mapper sets that field to `None` explicitly — adding another FIELD_FOR_CHECK entry doesn't help.
**Why it happens:** Two different failure modes produce "Required data not available from filings": (a) routing works but data is None in model, (b) routing works but model field doesn't exist on ExtractedData.
**How to avoid:** Before adding a routing entry, check `map_governance_fields()` and `map_litigation_fields()` to verify the target field is populated with data (not just declared `= None`).
**Warning signs:** Check has entry in FIELD_FOR_CHECK but still shows SKIPPED after adding it.

### Pitfall 2: brain build after every YAML change
**What goes wrong:** YAML edited, brain.duckdb not rebuilt, pipeline still uses stale data.
**Why it happens:** The `brain build` step is separate from YAML editing. brain.duckdb is the runtime source; YAML is the source of truth.
**How to avoid:** Always run `uv run do-uw brain build` immediately after any brain YAML change. Verify via `uv run do-uw brain status`.

### Pitfall 3: checks.json / YAML sync violation
**What goes wrong:** `_validate_yaml_json_sync()` throws RuntimeError on `brain build` because checks.json and YAML diverge.
**Why it happens:** checks.json is a derived artifact but must stay in sync. Adding a check to YAML requires checks.json to match.
**How to avoid:** Do not edit checks.json manually. Let `brain build` regenerate it. If divergence exists, run `uv run do-uw brain migrate-yaml` to regenerate YAML from checks.json first.

### Pitfall 4: DEF 14A content variation across proxy filings
**What goes wrong:** `board_attendance_pct` is present in AAPL's proxy but missing in RPM's — 80% success rate fails.
**Why it happens:** Proxy statement format varies significantly. Some companies report aggregate attendance, others per-director, others not at all.
**How to avoid:** The 80% success rate is measured across AAPL, RPM, TSLA — expect some proxies to return None. The field still must be added; it just may be legitimately absent.

### Pitfall 5: EXEC.CEO.risk_score and EXEC.CFO.risk_score cannot be bucket-a fixed
**What goes wrong:** Attempting to add routing for `EXEC.CEO.risk_score` and `EXEC.CFO.risk_score` — these are post-analysis artifacts.
**Why it happens:** The `_map_exec_check()` explicitly comments: "Risk score is a post-analysis artifact computed by executive forensics engine — not available at check evaluation time."
**How to avoid:** Classify these as intentionally-unmapped in their brain YAML and leave SKIPPED. They are not routing gaps — the data doesn't exist at evaluation time by design.

### Pitfall 6: FWRD.WARN.* checks are intentionally-unmapped
**What goes wrong:** Trying to route 13 `FWRD.WARN.*` sentiment checks (Glassdoor, Indeed, Blind, etc.) to ExtractedData fields.
**Why it happens:** Phase 47 scope focuses on structured data sources. These checks require real-time web scraping that isn't in scope.
**How to avoid:** The brain YAML already classifies them as `gap_bucket: intentionally-unmapped`. The re-audit will confirm this. Leave as SKIPPED.

### Pitfall 7: false trigger introduction on AAPL
**What goes wrong:** A newly-routed check (e.g., `GOV.RIGHTS.classified`) now fires TRIGGERED on AAPL because AAPL has a staggered board.
**Why it happens:** Adding routing causes the check to evaluate on real data — if AAPL triggers, it's likely correct (the data was always there, routing just surfaced it). But the baseline comparison will flag it.
**How to avoid:** For AAPL, new TRIGGERED findings after routing must be examined: is AAPL's result correct? If yes, update the baseline; if not, the threshold needs calibration (still a phase failure per the zero-tolerance rule).

---

## Code Examples

### Adding a FIELD_FOR_CHECK entry (bucket-a routing fix)

```python
# Source: src/do_uw/stages/analyze/check_field_routing.py
# Pattern: add to the appropriate section of FIELD_FOR_CHECK dict

# GOV.EFFECT checks (currently None in mapper)
"GOV.EFFECT.late_filing": "late_filing_flag",
"GOV.EFFECT.nt_filing": "nt_filing_flag",
"GOV.EFFECT.auditor_change": "auditor_change_flag",
"GOV.EFFECT.sig_deficiency": "significant_deficiency_flag",

# These already have entries — no change needed
# "GOV.BOARD.attendance": "board_attendance",  # already in FIELD_FOR_CHECK
```

### Populating a None placeholder in the mapper (bucket-b)

```python
# Source: src/do_uw/stages/analyze/check_mappers_sections.py
# Before:
result["board_attendance"] = None  # Not yet on BoardProfile

# After (once DEF14AExtraction.board_attendance_pct flows through convert_board_profile):
result["board_attendance"] = _safe_sourced(gov.board.board_attendance_pct)
```

### Adding threshold_context to CheckResult (QA-03)

```python
# Source: src/do_uw/stages/analyze/check_results.py
# Add after the existing 'confidence' field:
threshold_context: str = Field(
    default="",
    description=(
        "Human-readable threshold criterion from brain YAML that was triggered. "
        "e.g., 'red: Average tenure >15 years (entrenchment risk)'. "
        "Populated by _apply_traceability() when status=TRIGGERED. "
        "Empty for CLEAR/SKIPPED/INFO results."
    ),
)
```

### Injecting threshold_context in _apply_traceability (QA-03)

```python
# Source: src/do_uw/stages/analyze/check_engine.py
# Add to _apply_traceability() after existing link population:
if result.status == CheckStatus.TRIGGERED:
    raw_threshold = check.get("threshold", {})
    threshold = cast(dict[str, Any], raw_threshold) if isinstance(raw_threshold, dict) else {}
    level = result.threshold_level  # "red" or "yellow"
    criterion_text = threshold.get(level) if level else None
    if not criterion_text and threshold.get("triggered"):
        criterion_text = threshold.get("triggered")  # boolean threshold uses "triggered" key
    if criterion_text:
        result.threshold_context = f"{level}: {criterion_text}" if level else criterion_text
```

### DEF14AExtraction new fields

```python
# Source: src/do_uw/stages/extract/llm/schemas/def14a.py
# Add to the Board of Directors section:

board_gender_diversity_pct: float | None = Field(
    default=None,
    description=(
        "Percentage of female/women directors on the board (0-100). "
        "Extract from diversity section or director biography table."
    ),
)
board_racial_diversity_pct: float | None = Field(
    default=None,
    description=(
        "Percentage of racially/ethnically diverse directors (0-100). "
        "Extract from diversity section if disclosed."
    ),
)
board_meetings_held: int | None = Field(
    default=None,
    description="Total number of board meetings held during the fiscal year",
)
board_attendance_pct: float | None = Field(
    default=None,
    description=(
        "Aggregate board meeting attendance percentage (0-100). "
        "Usually disclosed as 'X% of directors attended 75%+ of meetings' "
        "or as a specific aggregate attendance rate."
    ),
)
directors_below_75_pct_attendance: int | None = Field(
    default=None,
    description="Number of directors who attended less than 75% of board meetings",
)
```

### LLM Governance converter additions

```python
# Source: src/do_uw/stages/extract/llm_governance.py
# In convert_board_profile(), after computing overboarded:

board_attendance_pct_sv: SourcedValue[float] | None = None
if extraction.board_attendance_pct is not None:
    if 0.0 <= extraction.board_attendance_pct <= 100.0:
        board_attendance_pct_sv = sourced_float(
            extraction.board_attendance_pct, _LLM_SOURCE, Confidence.HIGH
        )

# Then update the BoardProfile return to include new fields
# (BoardProfile model needs new optional fields added first)
```

---

## Current State of the 68 SKIPPED Checks

Empirically verified from AAPL-2026-02-25/state.json:

```
Status counts: {'CLEAR': 110, 'INFO': 201, 'TRIGGERED': 24, 'SKIPPED': 68}
```

### Population breakdown

**"Data mapping not configured" (17 checks)** — no routing at all:
- `EXEC.CEO.risk_score`, `EXEC.CFO.risk_score` — intentionally-unmapped (post-analysis artifacts)
- `FWRD.NARRATIVE.10k_vs_earnings`, `FWRD.NARRATIVE.investor_vs_sec` — intentionally-unmapped (requires LLM comparison)
- 13x `FWRD.WARN.*` (sentiment: glassdoor, indeed, blind, linkedin, g2, trustpilot, app_ratings, social_sentiment, journalism_activity, nhtsa, cfpb, fda_medwatch) — intentionally-unmapped (external APIs)

**"Required data not available" with FIELD_FOR_CHECK routing (42 checks)** — mapper returns None:
- 9x `GOV.BOARD.*` — board_attendance, diversity, expertise, independence, meetings, overboarding, size, succession, tenure
- 8x `GOV.RIGHTS.*` — action_consent, bylaws, classified, forum_select, proxy_access, special_mtg, supermajority, takeover
- 7x `GOV.PAY.*` — 401k_match, deferred_comp, equity_burn, exec_loans, golden_para, hedging, pension
- 6x `GOV.EFFECT.*` — auditor_change, iss_score, late_filing, nt_filing, proxy_advisory, sig_deficiency
- 4x `FIN.ACCT.*` — auditor_attestation_fail, auditor_disagreement, restatement_auditor_link, restatement_stock_window
- 2x `GOV.INSIDER.*` — plan_adoption, unusual_timing
- 2x `BIZ.*` — BIZ.DEPEND.labor (text signal exists), BIZ.STRUCT.vie_spe (text signal exists)
- 1x `LIT.DEFENSE.*` — forum_selection
- 1x `LIT.PATTERN.*` — peer_contagion
- 1x `LIT.REG.*` — comment_letters
- 1x `LIT.SECTOR.*` — regulatory_databases

**"Required data not available" without any routing (9 checks):**
- 4x `EXEC.PROFILE.*` — avg_tenure, board_size, independent_ratio, overboarded_directors (mapper exists in check_mappers_analytical.py but data is None from GovernanceData)
- 2x `FIN.QUALITY.*` — deferred_revenue_trend, q4_revenue_concentration (Phase 26 quality checks, data not yet computed)
- 1x `FWRD.DISC.*` — sec_comment_letters (LIT data cross-reference possible)
- 2x `NLP.FILING.*` — filing_timing_change, late_filing (NLP engine result not yet mapped)

### Key insight on EXEC.PROFILE checks

The `_map_exec_profile()` function already maps these fields correctly from `gov.board.*` and `gov.leadership.*`. These checks SKIP because `extracted.governance` is None in the AAPL test run, OR the specific sub-fields (like `board.size`) are None on GovernanceData. The fix is to ensure DEF 14A extraction populates these `BoardProfile` fields — not to add new routing.

---

## Open Questions

1. **BIZ.DEPEND.labor routing: text signal exists but check still SKIPS**
   - What we know: `FIELD_FOR_CHECK["BIZ.DEPEND.labor"] = "labor_risk_flag_count"` exists; mapper code sets `result["labor_risk_flag_count"] = _text_signal_count(extracted, "labor_concentration")`
   - What's unclear: Why does AAPL show this as SKIPPED? The text signal count function should return 0 (clear) not None. Possibly `extracted.text_signals` is empty on AAPL run.
   - Recommendation: Verify `extracted.text_signals` content for AAPL in state.json; if empty dict, the NLP stage didn't run — not a routing gap.

2. **FIN.QUALITY.deferred_revenue_trend and q4_revenue_concentration**
   - What we know: These are Phase 26 analytical checks; `_map_quality_check()` in check_mappers_analytical.py handles FIN.QUALITY prefix
   - What's unclear: What specific fields do these need? They likely need multi-period financial data not extracted yet.
   - Recommendation: Examine `_map_quality_check()` implementation to see what data is requested; if the data path is valid but data is genuinely absent, classify as intentionally-unmapped.

3. **NLP.FILING.filing_timing_change and NLP.FILING.late_filing**
   - What we know: `_map_nlp_check()` handles NLP prefix; filing timing analysis requires comparing filing dates across periods
   - What's unclear: Whether the NLP engine produces these specific signals
   - Recommendation: Classify as intentionally-unmapped if NLP engine doesn't produce these; they require dedicated late-filing detection against SEC EDGAR filing dates.

4. **GOV.EFFECT.iss_score and GOV.EFFECT.proxy_advisory**
   - What we know: Both mapper and routing exist; both return None (external services)
   - What's unclear: Are these achievable from public sources?
   - Recommendation: ISS scores are proprietary ($$$). These are correctly intentionally-unmapped; verify brain YAML has `gap_bucket: intentionally-unmapped`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (pyproject.toml [tool.pytest.ini_options]) |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/stages/analyze/ tests/brain/ -q` |
| Full suite command | `uv run pytest tests/ -q` |
| Estimated runtime | ~20s (analyze/brain), ~170s (full) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | FIELD_FOR_CHECK entries for bucket-a checks reduce SKIPPED count | unit | `uv run pytest tests/stages/analyze/test_wiring_fixes.py -x` | ✅ yes — extend existing |
| MAP-01 | No "Data mapping not configured" checks remain unfixed | unit | `uv run pytest tests/stages/analyze/test_data_status.py -x` | ✅ yes — extend |
| MAP-02 | Extraction gaps filled — mapper returns non-None for targeted checks | unit | `uv run pytest tests/stages/analyze/test_declarative_mapper.py -x` | ✅ yes — extend |
| MAP-03 | DEF14AExtraction schema includes diversity/attendance/meetings fields | unit | `uv run pytest tests/stages/extract/ -x` | ✅ yes — new test file needed |
| MAP-03 | convert_board_profile() populates board_attendance_pct from extraction | unit | `uv run pytest tests/stages/extract/ -x` | ❌ Wave 0 gap |
| MAP-03 | 80% of AAPL/RPM/TSLA proxies produce non-None for each new field | integration (manual) | Manual review of state.json after pipeline run | manual-only |
| QA-03 | CheckResult.threshold_context field exists with default="" | unit | `uv run pytest tests/ -k "CheckResult" -x` | ❌ Wave 0 gap |
| QA-03 | _apply_traceability() sets threshold_context when status=TRIGGERED | unit | `uv run pytest tests/stages/analyze/ -k "threshold_context" -x` | ❌ Wave 0 gap |
| QA-03 | TRIGGERED checks have non-empty threshold_context | unit | `uv run pytest tests/stages/analyze/test_false_triggers.py -x` | ✅ yes — extend |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `uv run pytest tests/stages/analyze/ tests/brain/ -q`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green (≤2 pre-existing failures) before verification
- **Estimated feedback latency per task:** ~20 seconds

### Wave 0 Gaps (must be created before implementation)

- [ ] `tests/stages/extract/test_def14a_schema.py` — covers MAP-03 (DEF14AExtraction new fields, convert_board_profile() population)
- [ ] `tests/stages/analyze/test_threshold_context.py` — covers QA-03 (CheckResult.threshold_context field + _apply_traceability() injection)
- [ ] `tests/stages/analyze/test_regression_baseline.py` — covers MAP-01/MAP-02 (baseline snapshot + post-change comparison against AAPL TRIGGERED count)

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection — `src/do_uw/stages/analyze/check_field_routing.py` (FIELD_FOR_CHECK: 247 entries)
- Codebase direct inspection — `src/do_uw/stages/analyze/check_engine.py` (_apply_traceability implementation)
- Codebase direct inspection — `src/do_uw/stages/analyze/check_results.py` (CheckResult Pydantic model)
- Codebase direct inspection — `src/do_uw/stages/analyze/check_mappers_sections.py` (None placeholders in map_governance_fields)
- Codebase direct inspection — `src/do_uw/stages/extract/llm/schemas/def14a.py` (DEF14AExtraction fields)
- Codebase direct inspection — `src/do_uw/stages/extract/llm_governance.py` (convert_board_profile)
- Codebase direct inspection — `src/do_uw/brain/brain_check_schema.py` (BrainCheckThreshold.red/yellow fields)
- Runtime analysis — `output/AAPL-2026-02-25/state.json` (68 SKIPPED checks, exact population breakdown)
- `uv run pytest` — baseline test suite: 3951 passed, 2 pre-existing failures in test_render_coverage.py

### Secondary (MEDIUM confidence)
- Brain YAML files (`src/do_uw/brain/checks/gov/board.yaml`) — confirmed gap_bucket field placement
- Phase 46 CONTEXT.md — confirmed gap_bucket classification approach and field names
- CONTEXT.md Phase 47 — locked decisions (not alternatives)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all components verified by direct codebase inspection
- Architecture patterns: HIGH — all patterns derive from existing code; no new libraries
- Pitfalls: HIGH — confirmed by runtime state.json analysis of actual SKIPPED check population
- Validation architecture: HIGH — test infrastructure exists; 3 new test files needed

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable codebase; no external dependencies)
