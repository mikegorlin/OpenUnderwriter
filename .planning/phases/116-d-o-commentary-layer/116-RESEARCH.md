# Phase 116: D&O Commentary Layer - Research

**Researched:** 2026-03-18
**Domain:** Brain YAML do_context authoring, migration of hardcoded D&O commentary, section narratives, scoring detail expansion
**Confidence:** HIGH

## Summary

Phase 116 transforms the worksheet from a data display tool into a D&O risk intelligence document. The infrastructure is fully in place from Phase 115: do_context engine (`do_context_engine.py`), signal consumer pattern (`_signal_consumer.py` / `_signal_fallback.py`), and template variable system with `SafeFormatDict`. The remaining work is: (1) authoring do_context templates for all 563 signals (only 3 YAML files currently have them), (2) migrating 5 hardcoded Python functions + 1 Jinja2 template to consume signal do_context, (3) adding D&O columns to evaluative tables, (4) generating LLM-powered section-opening narratives stored on `state.pre_computed_narratives`, (5) building per-factor scoring detail with "Why TIER" explanations, and (6) promoting CI gate from WARN to FAIL.

The largest single task is LLM batch generation of do_context for 563 signals across 90+ YAML files. This is a mechanical but high-volume operation -- each signal needs TRIGGERED_RED, TRIGGERED_YELLOW, and CLEAR templates referencing the signal's `factors`, `peril_ids`, and D&O litigation theory. The existing 3 files (accounting.yaml, forensic.yaml, forensic_xbrl.yaml) serve as exemplars.

**Primary recommendation:** Execute in the CONTEXT.md-defined wave order: batch generate do_context first (establishes content), then migrate Python functions (delete hardcoded commentary), then wire D&O columns to tables, then narratives + scoring detail, then CI gate promotion.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Evaluative tables only** -- Tables presenting risk-relevant data get D&O columns: forensic indicators, governance metrics, litigation cases, scoring factors, market events, risk flags. Raw financial statements, peer comparison raw data, filing history, and officer/director raw listings do NOT get D&O columns
- **Empty cell fallback** -- If no signal do_context exists for a row, leave the D&O column blank. No filler commentary
- **All 562 signals get do_context** -- LLM batch generation produces TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR templates for every signal. Human spot-checks ~20-30 key signals. `brain health` validates template syntax
- **LLM batch process** -- Read all signal YAMLs, LLM generates per-status D&O commentary templates, write back to YAML files, run `brain health` validation, spot-check key signals
- **Quality bar** -- Every template must contain company-specific placeholder variables ({value}, {score}, {zone}, etc.) and reference the specific D&O litigation theory or risk vector
- **Expandable per-factor detail** -- Each factor (F.1-F.10) gets collapsible section with "What Was Found" + "Underwriting Commentary"
- **"Why TIER, not ADJACENT_TIER"** -- Algorithmic from factor scores, no LLM
- **LLM-generated section narratives in ANALYZE stage** -- All 6 major sections (Financial Health, Market Events, Governance Posture, Litigation Context, Scoring/Tier, Company Profile)
- **Migrate ALL 5 Python functions + Jinja2 template**: sect3_audit._add_audit_do_context, sect4_market_events._departure_do_context, sect5_governance._add_leadership_do_context, sect6_litigation._add_sca_do_context, sect7_scoring_detail._add_pattern_do_context, distress_indicators.html.j2 inline conditionals
- **Delete Python functions after migration** with golden snapshot parity tests
- **Promote CI gate WARN to FAIL** -- WARN_PYTHON_FILES and WARN_TEMPLATE_FILES become empty. Clean slate
- **Wave ordering**: (1) LLM batch do_context, (2) Migrate 5 functions, (3) Wire D&O columns, (4) Narratives, (5) Scoring detail + tier explanation, (6) CI gate promotion

### Claude's Discretion
- Exact LLM prompt design for batch do_context generation
- Which tables qualify as "evaluative" vs "raw data"
- Exact collapsible section implementation for factor detail
- Narrative prompt engineering for section openers
- Order of signal YAML file processing
- Handling signals with no meaningful D&O relevance

### Deferred Ideas (OUT OF SCOPE)
- Interactive `brain preview-do-context SIGNAL_ID` command
- do_context coverage threshold in CI (e.g., "must be >90%")
- Sector-specific do_context variants
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COMMENT-01 | Every data table has optional "D&O Risk" / "Assessment" column populated by signal do_context | Evaluative table identification (Architecture section), do_context consumer pattern from Phase 115, add_styled_table column extension |
| COMMENT-02 | Each scoring factor (F.1-F.10) has "What Was Found" + "Underwriting Commentary" | FactorScore model fields (evidence, rules_triggered, signal_contributions), SignalResult.do_context for commentary |
| COMMENT-03 | Each forensic indicator has D&O Commentary | Already partially done in distress_indicators.html.j2 (z_do_context, beneish_do_context, etc.) -- extend pattern to all forensic signals |
| COMMENT-04 | Financial Health opens with narrative paragraph | PreComputedNarratives.financial field exists, existing financial_narrative() in md_narrative.py as pattern |
| COMMENT-05 | Governance section opens with narrative | PreComputedNarratives.governance field exists, existing governance_narrative() in md_narrative_sections.py as pattern |
| COMMENT-06 | Litigation section narrative with sector comparison and SCA probability | PreComputedNarratives.litigation field exists, existing litigation_narrative() as pattern |
| SCORE-01 | Scoring detail: each factor expanded with "What Was Found" + "Underwriting Commentary" | Current sect7_scoring_detail.py has factor detail table -- expand with collapsible per-factor sections |
| SCORE-04 | "Why [TIER], not [ADJACENT_TIER]" narrative | Tier boundaries in scoring.json (WIN 86-100, WANT 71-85, WRITE 51-70, WATCH 31-50, WALK 11-30, NO_TOUCH 0-10), factor scores provide counterfactual analysis |
</phase_requirements>

## Architecture Patterns

### Existing Infrastructure (Phase 115 -- consume, don't rebuild)

```
Brain YAML (do_context templates)
    |
    v
do_context_engine.py (ANALYZE stage)
  - _select_template(): TRIGGERED_RED > TRIGGERED > DEFAULT
  - render_do_context(): SafeFormatDict template eval
  - apply_do_context(): orchestrates selection + rendering
    |
    v
SignalResult.do_context (string on result)
    |
    v
_signal_consumer.py (RENDER stage)
  - SignalResultView.do_context field
  - get_signal_do_context() accessor
    |
    v
_signal_fallback.py
  - safe_get_result() -> SignalResultView with .do_context
    |
    v
Context Builders / Section Renderers
  - Consume do_context strings as-is (no interpretation)
```

### Signal YAML do_context Format (Established Pattern)

```yaml
presentation:
  do_context:
    TRIGGERED_RED: >-
      Score of {value}/9 signals weak fundamentals -- companies
      scoring 0-3 historically experience higher stock volatility and
      increased exposure to shareholder derivative suits alleging
      mismanagement.
    TRIGGERED_YELLOW: >-
      Score of {value}/9 indicates moderate financial strength.
      Mid-range scores suggest mixed signals.
    CLEAR: >-
      Score of {value}/9 indicates strong fundamentals across
      profitability, leverage, and efficiency. Strong financial health
      correlates with lower D&O claim frequency.
```

**Template variables:** `{value}`, `{score}`, `{zone}`, `{threshold}`, `{threshold_level}`, `{evidence}`, `{source}`, `{confidence}`, `{company}`, `{ticker}`, `{details_*}` (flattened nested dict keys).

### Consumer Pattern (Established)

```python
# From financials_evaluative.py -- the canonical pattern
z_signal = safe_get_result(signal_results, "FIN.ACCT.quality_indicators")
result["z_do_context"] = z_signal.do_context if z_signal and z_signal.do_context else ""
```

### Section Narrative Storage

The `PreComputedNarratives` model on `AnalysisState.pre_computed_narratives` already has fields for all 6 sections:
- `financial: str | None`
- `market: str | None` (currently unused -- will be "Market Events")
- `governance: str | None`
- `litigation: str | None`
- `scoring: str | None` (currently unused -- will include tier explanation)
- `company: str | None`

Narratives are pre-computed in BENCHMARK stage (or can be added to ANALYZE). Renderers consume strings as-is from `state.pre_computed_narratives.financial`, etc.

### Scoring Factor Detail Structure

Current `FactorScore` model provides:
- `factor_name`, `factor_id` (F.1-F.10)
- `max_points`, `points_deducted`
- `evidence: list[str]` -- text evidence supporting deduction
- `rules_triggered: list[str]` -- rule IDs (e.g., F1-001)
- `sub_components: dict[str, float]` -- score breakdown
- `signal_contributions: list[dict[str, Any]]` -- signals with weights and severity

This provides everything needed for "What Was Found" without new data collection. "Underwriting Commentary" comes from signal do_context.

### Tier Boundaries (for "Why TIER" Algorithm)

| Tier | Min | Max | Probability |
|------|-----|-----|-------------|
| WIN | 86 | 100 | <2% |
| WANT | 71 | 85 | 2-5% |
| WRITE | 51 | 70 | 5-10% |
| WATCH | 31 | 50 | 10-15% |
| WALK | 11 | 30 | 15-20% |
| NO_TOUCH | 0 | 10 | >20% |

**Counterfactual algorithm:**
1. Get current score and tier
2. Get adjacent tier (above and below)
3. For each factor with points_deducted > 0: compute "if this factor were 0, what tier?"
4. For the tier above: identify which factor(s) would need to improve to reach it
5. Render: "Score of X places RPM in WRITE tier (51-70). If F.7 Insider Trading (5/8) had scored 0, total would be X+5 = Y, still WRITE. The heaviest drag is F.1 Litigation History (12/20), which alone accounts for N% of deductions."

### Migration Targets -- Detailed Analysis

Each hardcoded function and the patterns they use:

| File | Function | What It Hardcodes | Replacement Signal |
|------|----------|-------------------|-------------------|
| sect3_audit.py | `_add_audit_do_context()` | Material weaknesses, restatements, going concern, CAMs, tenure D&O text | Audit signals: FIN.ACCT.* audit-related signals |
| sect4_market_events.py | `_departure_do_context()` | 3-line departure type to D&O string mapping | EXEC.PROFILE.departure or GOV.* departure signals |
| sect5_governance.py | `_add_leadership_do_context()` | Prior litigation history D&O context per executive | EXEC.PROFILE.prior_litigation signals |
| sect6_litigation.py | `_add_sca_do_context()` | Active SCA count, settlement history, lead counsel tier D&O text | LIT.SCA.* signals |
| sect7_scoring_detail.py | `_add_pattern_do_context()` | HIGH/SEVERE pattern D&O text | Pattern signal do_context |
| distress_indicators.html.j2 | Inline Jinja2 conditionals | Zone-based D&O relevance text per model | Already partially replaced -- extend to use `{{ z_do_context }}` etc. |

### Evaluative vs Raw Data Tables

**Evaluative (GET D&O column):**
- Distress model indicators (Altman, Beneish, Ohlson, Piotroski)
- Forensic accounting indicators (DSO, Sloan, accruals, revenue quality)
- Audit risk assessment table
- Stock drop events table
- Insider cluster events table
- Executive departures table
- SCA cases table
- SEC enforcement actions table
- Board quality metrics table
- Governance red flags
- Scoring factor detail table
- Pattern detection results table
- Allegation theory mapping

**Raw Data (NO D&O column):**
- Income statement, balance sheet, cash flow statement
- Peer financial comparison raw numbers
- Filing history table
- Officer/director raw listing
- Institutional holders raw listing
- Revenue segment raw data
- Debt maturity schedule (raw numbers)
- Capital markets offerings table (has some D&O already -- Section 11 text)

### Collapsible Section Pattern

The project already has collapsible sections (VIS-04 from CIQ-style layout). Use the same `<details>/<summary>` pattern:

```html
<details class="collapsible my-3">
  <summary>F.1 — Litigation History (12/20)</summary>
  <div class="collapsible-content">
    <h4>What Was Found</h4>
    <p>{{ factor.evidence | join('; ') }}</p>
    <p><em>Sources: {{ factor.sources }}</em></p>
    <h4>Underwriting Commentary</h4>
    <p>{{ factor.do_context }}</p>
  </div>
</details>
```

For the Word renderer (docx), simulate collapsibility with indented sub-sections under each factor heading.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template variable substitution | Custom string replacement | `do_context_engine.render_do_context()` with `SafeFormatDict` | Already handles missing variables, nested details, formatting edge cases |
| Signal result access | Direct dict key access | `safe_get_result(signal_results, SIGNAL_ID).do_context` | Null-safe, returns `SignalUnavailable` sentinel, typed view |
| Narrative pre-computation storage | New state field | `state.pre_computed_narratives` (`PreComputedNarratives` model) | Already has fields for all 6 sections, populated in BENCHMARK |
| Tier boundary lookup | Hardcoded score ranges | `scoring.json["tiers"]` config file | Single source of truth, already used by `tier_classification.py` |
| Template validation | Manual checking | `validate_do_context_template()` from do_context_engine.py | Checks balanced braces, valid variable names, details_* pattern |
| D&O evaluative language scanning | Manual grep | `test_do_context_ci_gate.py` scanner functions | AST-based Python scanning, Jinja2 content extraction, 13 D&O patterns |

## Common Pitfalls

### Pitfall 1: YAML Multi-Line String Formatting
**What goes wrong:** YAML multi-line strings with `>-` (folded block scalar, strip trailing newlines) vs `|` (literal block scalar) behave differently. Template variables `{value}` inside YAML can conflict with YAML flow mapping syntax.
**Why it happens:** YAML interprets `{` as flow mapping start in certain contexts.
**How to avoid:** Always use `>-` (folded, strip) for do_context templates. Quote or escape any `{variable}` that appears at the start of a YAML value. The existing 3 files all use `>-` successfully.
**Warning signs:** `brain health` validation fails with YAML parse errors after batch generation.

### Pitfall 2: LLM Batch Generation Quality
**What goes wrong:** LLM generates generic boilerplate ("This signal indicates elevated risk") that violates QUAL-04.
**Why it happens:** Without sufficient context about the signal's specific D&O relevance, the LLM defaults to vague language.
**How to avoid:** Include in the LLM prompt: signal name, signal description, `factors` list (F.1-F.10 IDs), `peril_ids`, threshold values, and the specific D&O litigation theory each factor maps to. Require `{value}`, `{company}`, or `{evidence}` in every template. Spot-check the 20-30 highest-impact signals (those with factors F.1-F.4, which carry the most weight).
**Warning signs:** Templates that don't reference any placeholder variables. Templates that could apply to any company by changing the name.

### Pitfall 3: Migration Parity Loss
**What goes wrong:** After deleting hardcoded Python functions, the rendered output loses D&O commentary that was present before.
**Why it happens:** Signal do_context may not fire for all the same conditions the Python function handled.
**How to avoid:** Before migration, capture golden snapshots of current output for 2+ companies (one clean, one problematic). After migration, diff output section-by-section. The Phase 115 pattern (`test_do_context_golden.py`) establishes this workflow.
**Warning signs:** Visual regression test diff > threshold. Sections that had D&O commentary now show blank cells.

### Pitfall 4: Empty do_context for SKIPPED Signals
**What goes wrong:** Many signals return SKIPPED status when data is unavailable. The do_context engine correctly returns "" for SKIPPED. But evaluative table rows backed by SKIPPED signals show blank D&O columns even though the user expects commentary.
**Why it happens:** `_select_template()` returns "" for SKIPPED status by design.
**How to avoid:** This is correct behavior per CONTEXT.md ("empty cells are honest representation"). Do NOT add fallback commentary for SKIPPED signals. The blank cell tells the underwriter "we couldn't evaluate this."
**Warning signs:** Urge to add "Data unavailable" placeholder text -- resist this.

### Pitfall 5: Narrative Generation Context Starvation
**What goes wrong:** LLM section narratives come out generic because the prompt doesn't include enough analytical context.
**Why it happens:** QUAL-03 violation -- prompts omit scoring results, signal evaluations, or company specifics.
**How to avoid:** Pass to the LLM prompt: (a) all signal results for the section's domain, (b) factor scores and deductions, (c) tier classification, (d) company name/ticker/sector, (e) specific dollar amounts and dates from extracted data. The existing `financial_narrative()` in md_narrative.py shows the level of specificity required.
**Warning signs:** Narrative sentences that could apply to any company by changing the name.

### Pitfall 6: CI Gate False Positives After Migration
**What goes wrong:** After deleting hardcoded functions, the CI gate FAIL scan finds D&O language in log messages, docstrings, or test assertions in the same files.
**Why it happens:** The AST scanner extracts ALL string literals, including docstrings and logging.
**How to avoid:** The scanner already uses AST parsing which captures string literals in code. After migration, verify the WARN files have zero hits by running `pytest tests/brain/test_do_context_ci_gate.py -v`. If legitimate non-commentary strings trigger false positives, update the scanner's exclusion logic.
**Warning signs:** CI gate fails on docstrings or test fixture text.

### Pitfall 7: 500-Line File Limit Violation
**What goes wrong:** Adding D&O columns, collapsible sections, and narrative consumption to existing section renderers pushes them past 500 lines.
**Why it happens:** Each section file is already 400-500 lines. Adding new rendering code without splitting will exceed the limit.
**How to avoid:** Plan for splits proactively. The established pattern is `sect5_governance.py` + `sect5_governance_board.py` + `sect5_governance_comp.py`. Create new sub-modules like `sect7_scoring_factors.py` for per-factor detail.
**Warning signs:** Files approaching 450 lines before the new code is added.

## Code Examples

### Batch do_context Generation -- Signal Processing Pattern

```python
# Read signal YAML, generate do_context, write back
import yaml
from pathlib import Path

def generate_do_context_for_signal(signal: dict) -> dict[str, str]:
    """Generate do_context templates for a single signal.

    Returns dict with TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR keys.
    """
    signal_id = signal["id"]
    factors = signal.get("factors", [])
    peril_ids = signal.get("peril_ids", [])
    name = signal["name"]
    threshold = signal.get("threshold", {})

    # Build LLM prompt with full context
    prompt = f"""Generate D&O underwriting commentary templates for brain signal:

Signal: {signal_id} - {name}
Factors: {factors}  (scoring factors this signal maps to)
Peril IDs: {peril_ids}
Threshold Red: {threshold.get('red', 'N/A')}
Threshold Yellow: {threshold.get('yellow', 'N/A')}

Generate 3 templates (TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR).
Each MUST:
- Use {{value}}, {{company}}, {{evidence}} variables
- Reference the specific D&O litigation theory
- Be 1-2 sentences, company-specific when rendered
"""
    # LLM call here, parse response into dict
    return {"TRIGGERED_RED": "...", "TRIGGERED_YELLOW": "...", "CLEAR": "..."}
```

### Adding D&O Column to Evaluative Table

```python
# Pattern for adding D&O column to existing tables
from do_uw.stages.render.context_builders._signal_fallback import safe_get_result

def _render_table_with_do_context(
    doc, signal_results, rows_with_signal_ids, ds
):
    headers = ["Indicator", "Value", "Zone", "D&O Risk"]
    rows = []
    for indicator_name, value, zone, signal_id in rows_with_signal_ids:
        sig = safe_get_result(signal_results, signal_id)
        do_ctx = sig.do_context if sig and sig.do_context else ""
        rows.append([indicator_name, value, zone, do_ctx])
    add_styled_table(doc, headers, rows, ds)
```

### "Why TIER" Algorithm

```python
def generate_tier_explanation(scoring: ScoringResult, tier_config: list) -> str:
    """Generate 'Why TIER, not ADJACENT_TIER' narrative."""
    score = scoring.quality_score
    tier = scoring.tier_classification.tier

    # Find adjacent tiers
    current_idx = [t["tier"] for t in tier_config].index(tier.value)
    above = tier_config[current_idx - 1] if current_idx > 0 else None
    below = tier_config[current_idx + 1] if current_idx < len(tier_config) - 1 else None

    parts = [f"Quality score of {score:.1f} places the company in {tier.value} "
             f"tier ({scoring.tier_classification.score_range_low}-"
             f"{scoring.tier_classification.score_range_high})."]

    # Top contributing factors
    active = sorted(scoring.factor_scores,
                    key=lambda f: f.points_deducted, reverse=True)
    if active and active[0].points_deducted > 0:
        top = active[0]
        parts.append(f"Heaviest drag: {top.factor_id} {top.factor_name} "
                     f"({top.points_deducted:.0f}/{top.max_points}).")

    # Counterfactual for tier above
    if above:
        gap = above["min_score"] - score
        parts.append(f"To reach {above['tier']}, score would need "
                     f"+{gap:.1f} points.")
        # Which factor, if zeroed, gets closest?
        for f in active:
            if f.points_deducted > 0:
                hypothetical = score + f.points_deducted
                if hypothetical >= above["min_score"]:
                    parts.append(f"If {f.factor_id} were clean, score "
                                 f"would be {hypothetical:.1f} ({above['tier']}).")
                    break

    return " ".join(parts)
```

### Migration Pattern (Delete Hardcoded, Use Signal do_context)

```python
# BEFORE (hardcoded in sect3_audit.py)
def _add_audit_do_context(doc, audit, ds):
    if audit.material_weaknesses:
        fp = doc.add_paragraph(style="DOBody")
        fp.add_run("Material Weaknesses: ... primary D&O risk signal ...")

# AFTER (signal do_context)
def _render_audit_do_annotations(doc, signal_results, ds):
    # Material weakness signal
    mw_sig = safe_get_result(signal_results, "FIN.ACCT.material_weakness")
    if mw_sig and mw_sig.do_context:
        fp = doc.add_paragraph(style="DOBody")
        run = fp.add_run(mw_sig.do_context)
        run.italic = True
        run.font.size = ds.size_small
        if mw_sig.threshold_level == "red":
            add_risk_indicator(fp, "HIGH", ds)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| D&O commentary in Python functions | Brain YAML do_context templates | Phase 115 (v8.0) | Commentary portable, auditable, signal-driven |
| Hardcoded Jinja2 conditionals | `{{ do_context }}` pass-through | Phase 115 established pattern | Zero business logic in templates |
| Narratives generated at render time | Pre-computed in ANALYZE/BENCHMARK | PreComputedNarratives model exists | Deterministic, auditable, cached |
| Generic factor tables | Expandable per-factor detail | Phase 116 new | Underwriter sees evidence + interpretation |

## Open Questions

1. **Signal-to-Migration-Target Mapping**
   - What we know: 5 Python functions contain hardcoded D&O commentary. Each function handles specific conditions (e.g., material weaknesses, going concern, cluster selling).
   - What's unclear: The exact signal IDs that map to each condition. Some conditions (e.g., "material weakness count > 0") may not have a dedicated brain signal yet.
   - Recommendation: During batch generation, ensure every condition handled by the 5 functions has a corresponding signal with do_context. If a signal doesn't exist, the do_context on a related signal should cover the case. Map this explicitly before migration starts.

2. **LLM Narrative Generation Placement**
   - What we know: CONTEXT.md says "LLM-generated in ANALYZE stage." PreComputedNarratives is populated in BENCHMARK stage currently.
   - What's unclear: Whether to add narrative generation to ANALYZE or BENCHMARK (or both).
   - Recommendation: Add to BENCHMARK stage (which runs after ANALYZE and SCORE), since narratives need scoring results and tier classification. The model field `pre_computed_narratives` already lives on AnalysisState and is populated in BENCHMARK.

3. **HTML vs Word Renderer Parity**
   - What we know: Both HTML and Word renderers exist. HTML uses Jinja2 templates. Word uses python-docx directly.
   - What's unclear: Whether Phase 116 needs to update both renderers for every change.
   - Recommendation: Both renderers must be updated. The HTML path is the primary output the user reviews. Word renderer must show equivalent content.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/brain/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMMENT-01 | D&O columns in evaluative tables | integration | `uv run pytest tests/render/ -k "do_context or do_column" -x` | Wave 0 |
| COMMENT-02 | Scoring factor "What Found" + "Commentary" | integration | `uv run pytest tests/render/test_sect7* -x` | Extend existing |
| COMMENT-03 | Forensic indicator D&O commentary | integration | `uv run pytest tests/render/test_financials* -k forensic -x` | Extend existing |
| COMMENT-04 | Financial Health narrative | unit | `uv run pytest tests/render/test_narrative* -k financial -x` | Extend existing |
| COMMENT-05 | Governance narrative | unit | `uv run pytest tests/render/test_narrative* -k governance -x` | Extend existing |
| COMMENT-06 | Litigation narrative | unit | `uv run pytest tests/render/test_narrative* -k litigation -x` | Extend existing |
| SCORE-01 | Per-factor detail expansion | integration | `uv run pytest tests/render/test_sect7* -x` | Extend existing |
| SCORE-04 | "Why TIER" narrative | unit | `uv run pytest tests/score/test_tier* -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/ tests/render/ -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/brain/test_do_context_batch.py` -- validates batch-generated templates pass `validate_do_context_template()`
- [ ] `tests/score/test_tier_explanation.py` -- tests "Why TIER" algorithm
- [ ] `tests/render/test_do_context_golden.py` -- golden snapshot parity for migration (may extend existing)
- [ ] Migration parity assertions: before/after output diff for RPM (problematic) and V (clean)

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/analyze/do_context_engine.py` -- Template engine, variable reference, SafeFormatDict
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- SignalResultView.do_context consumer pattern
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` -- Reference consumer implementation
- `src/do_uw/stages/render/sections/sect3_audit.py` -- Migration target: _add_audit_do_context() (lines 189-253)
- `src/do_uw/stages/render/sections/sect4_market_events.py` -- Migration target: _departure_do_context() (lines 409-415)
- `src/do_uw/stages/render/sections/sect5_governance.py` -- Migration target: _add_leadership_do_context() (lines 419-436)
- `src/do_uw/stages/render/sections/sect6_litigation.py` -- Migration target: _add_sca_do_context() (lines 259-323)
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` -- Migration target: _add_pattern_do_context() (lines 182-197)
- `src/do_uw/templates/html/sections/financial/distress_indicators.html.j2` -- Migration target: inline Jinja2 conditionals
- `tests/brain/test_do_context_ci_gate.py` -- CI gate: WARN_PYTHON_FILES, WARN_TEMPLATE_FILES to promote
- `src/do_uw/brain/brain_signal_schema.py` -- PresentationSpec.do_context schema (line 472)
- `src/do_uw/models/density.py` -- PreComputedNarratives model (line 74)
- `src/do_uw/brain/config/scoring.json` -- Tier boundaries (WIN 86-100 through NO_TOUCH 0-10)
- `src/do_uw/brain/signals/fin/forensic.yaml` -- Exemplar do_context templates (Piotroski)

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/render/md_narrative.py` -- Existing narrative generation patterns
- `src/do_uw/stages/render/md_narrative_sections.py` -- Existing governance/litigation/scoring narrative generators

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all infrastructure exists from Phase 115, no new libraries needed
- Architecture: HIGH -- consumer pattern established, migration targets identified with line numbers
- Pitfalls: HIGH -- based on direct code inspection of 6 migration targets and template engine

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable internal architecture, no external dependencies)
