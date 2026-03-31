# Phase 130: Dual-Voice Intelligence - Research

**Researched:** 2026-03-23
**Domain:** LLM-powered commentary generation, HTML template dual-voice pattern, executive summary overhaul
**Confidence:** HIGH

## Summary

Phase 130 adds a "What Was Said" / "Underwriting Commentary" dual-voice pattern to 8 analytical sections, plus a major executive summary overhaul with recommendation paragraph, 5 key negatives/positives with SCA litigation theory references. All commentary is LLM-generated in the BENCHMARK stage, cached in state, and cross-validated against XBRL data.

The existing codebase provides strong foundations: `narrative_generator.py` already generates per-section LLM narratives in BENCHMARK, `_signal_consumer.py` aggregates signal results per section, `validate_narrative_amounts()` cross-validates dollar amounts, and `_bull_bear.py` already extracts key negatives/positives. The work is primarily: (1) adding a new commentary generation step in BENCHMARK alongside existing narrative generation, (2) adding new Pydantic models for commentary caching, (3) adding dual-voice HTML template blocks, and (4) overhauling the executive brief template.

**Primary recommendation:** Extend `narrative_generator.py` with a `generate_all_commentary()` function that makes one batched LLM call per section (8 calls total) using the same data extraction infrastructure. Store results on a new `state.analysis.pre_computed_commentary` field. Template changes are additive -- existing narratives remain, commentary blocks are new visual elements.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Commentary Source**: LLM with full signal context -- one batched LLM call per section in BENCHMARK stage
- Pass signal results + scoring factors + financials + company data as context
- Brain YAML `do_context` fields inform the LLM prompt (provide the D&O theory framework) but the LLM generates the final company-specific text
- Cached in state (`state.benchmarked.commentary`) -- generate once in BENCHMARK, re-render uses cache
- Only regenerate on `--fresh` or when underlying data changes
- Cross-validate all dollar amounts in commentary against XBRL/state data (leverage Phase 129's `validate_narrative_amounts()`)
- **Visual Presentation**: Bordered boxes -- "What Was Said" in light gray, "Underwriting Commentary" in navy/blue-gray tinted
- Clear headers on each box
- Subtle confidence indicator badge (HIGH/MEDIUM/LOW) based on TRIGGERED vs SKIPPED signal proportion
- **Executive Summary Design**: Recommendation paragraph (tier + probability + severity + defense cost) upfront, then narrative summary (2-3 paragraphs), then key negatives (top 5 with SCA theories), then key positives (top 5 with SCA theories)
- **Section Coverage**: 8 analytical sections get dual-voice (Executive Brief, Litigation, Governance, Financial, Market, Scoring, Company Profile, Meeting Prep). Skip audit appendix and pure-data display sections.

### Claude's Discretion
- Exact LLM prompt engineering for each section's commentary
- How to batch multiple section commentaries into fewer API calls (cost optimization)
- Confidence badge visual design (icon, color, positioning)
- Whether to use existing `_signal_consumer.py` or build a new aggregation layer for commentary context

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VOICE-01 | Every analytical section displays "What Was Said" and "Underwriting Commentary" as visually distinct blocks | Template structure analysis, CSS patterns, section template inventory |
| VOICE-02 | Commentary generated via batched LLM call in BENCHMARK using full signal + scoring + financial context | `narrative_generator.py` extension pattern, data extraction reuse, prompt design |
| VOICE-03 | Commentary cached in state for deterministic re-rendering | New Pydantic model on `AnalysisResults`, serialization pattern |
| VOICE-04 | Commentary cross-validates against XBRL/state data | Existing `validate_narrative_amounts()` reuse |
| EXEC-01 | Executive narrative reads like senior D&O underwriter connecting findings to SCA theories | SCA theory reference framework, prompt engineering |
| EXEC-02 | Key negatives: finding + magnitude + scoring factor ref + litigation theory | Existing `build_negative_narrative()` extension, theory mapping |
| EXEC-03 | Key positives: evidence + quantification + SCA theory defeated | Existing `build_positive_narrative()` extension, defense theory mapping |
| EXEC-04 | Recommendation block: tier + probability + severity + defense cost together | Existing `extract_exec_summary()` already has most fields, template overhaul |
</phase_requirements>

## Standard Stack

No new dependencies. All work uses existing stack.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | existing | LLM API calls for commentary generation | Already used in narrative_generator.py |
| pydantic v2 | existing | State model for commentary caching | Project standard |
| jinja2 | existing | HTML template dual-voice blocks | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| claude-haiku-4-5 | 20251001 | Default LLM model (configurable via DO_UW_LLM_MODEL) | Commentary generation -- same model as existing narratives |

**No new packages needed.**

## Architecture Patterns

### Current Narrative Architecture (What Exists)

```
BENCHMARK stage (stages/benchmark/__init__.py):
  Step 8: _precompute_narratives()
    -> _precompute_legacy_narratives()  -- thesis/risk/claim on state.benchmark
    -> generate_all_narratives()        -- per-section LLM narratives on state.analysis.pre_computed_narratives

Data flow:
  extract_section_data(state, section_id)  -- narrative_data.py dispatches to narrative_data_sections.py
  -> build_section_prompt(section_id, ...)  -- narrative_prompts.py
  -> anthropic_client.messages.create()     -- one call per section (7 sections)
  -> validate_narrative_amounts()           -- cross-validate dollar amounts
  -> stored on PreComputedNarratives model  -- 7 section strings + exec summary + meeting prep
```

### Commentary Generation Architecture (New)

```
BENCHMARK stage:
  Step 8.5: _precompute_commentary() -- NEW, after narratives
    -> generate_all_commentary(state)       -- NEW function in narrative_generator.py (or new commentary_generator.py)
       -> extract_commentary_context(state, section_id)  -- NEW, richer than narrative data
          - includes signal_results by prefix (reuse _signal_consumer.py)
          - includes scoring factor data (reuse _factor_data())
          - includes do_context strings from brain YAML
          - includes existing narrative text for "What Was Said" synthesis
       -> build_commentary_prompt(section_id, ...)  -- NEW prompts in narrative_prompts.py (or commentary_prompts.py)
       -> anthropic_client.messages.create()         -- one call per section (8 sections)
       -> validate_narrative_amounts()               -- reuse existing cross-validator
       -> stored on PreComputedCommentary model      -- NEW Pydantic model

Storage:
  state.analysis.pre_computed_commentary: PreComputedCommentary | None
    - financial: SectionCommentary | None
    - market: SectionCommentary | None
    - governance: SectionCommentary | None
    - litigation: SectionCommentary | None
    - scoring: SectionCommentary | None
    - company: SectionCommentary | None
    - executive_brief: SectionCommentary | None
    - meeting_prep: SectionCommentary | None

SectionCommentary model:
    what_was_said: str          -- factual data summary
    underwriting_commentary: str -- D&O risk interpretation with SCA theory refs
    confidence: str              -- HIGH/MEDIUM/LOW
    hallucination_warnings: list[str]  -- from validate_narrative_amounts()
```

### Template Integration Pattern

Each of the 8 section templates gets a dual-voice block. Pattern:

```html
{# Dual-Voice Commentary Block #}
{% set comm = commentary.get('financial') if commentary else none %}
{% if comm %}
<div class="dual-voice">
  <div class="dual-voice__factual">
    <div class="dual-voice__header">What Was Said</div>
    <div class="dual-voice__body">{{ comm.what_was_said }}</div>
  </div>
  <div class="dual-voice__commentary">
    <div class="dual-voice__header">
      Underwriting Commentary
      <span class="confidence-badge confidence-badge--{{ comm.confidence | lower }}">
        {{ comm.confidence }}
      </span>
    </div>
    <div class="dual-voice__body">{{ comm.underwriting_commentary }}</div>
  </div>
</div>
{% endif %}
```

This block is inserted AFTER the existing narrative architecture (5-layer or SCR fallback) in each section template. It is additive -- existing content remains.

### Executive Summary Overhaul Pattern

The executive brief template (`sections/executive_brief.html.j2`) needs structural changes:

```
Current flow:
  Recommendation block -> Key Negatives/Positives (simple) -> Damage Exposure/Tower -> Claim Scenario -> Coverage

New flow:
  Recommendation paragraph (tier + prob + severity + defense cost)
  -> Narrative summary (2-3 paragraphs, LLM-generated)
  -> Key Negatives (5, each with title + 1-2 para + scoring factor ref + SCA theory)
  -> Key Positives (5, each with title + 1-2 para + evidence + SCA theory defeated)
  -> Damage Exposure/Tower (preserved)
  -> Claim Scenario (preserved)
```

The key change is that negatives/positives become richer: each item gets a named SCA litigation theory mapping.

### Context Builder Integration

Commentary flows through the assembly registry pattern:

```python
# In assembly_html_extras.py or new assembly_commentary.py:
@register_builder
def _build_commentary_context(state, context, chart_dir):
    if state.analysis and state.analysis.pre_computed_commentary:
        commentary = state.analysis.pre_computed_commentary
        context["commentary"] = {
            "financial": _serialize_commentary(commentary.financial),
            "market": _serialize_commentary(commentary.market),
            # ... etc
        }
```

### Recommended File Organization

```
src/do_uw/stages/benchmark/
  commentary_generator.py    # NEW: generate_all_commentary(), per-section generation
  commentary_prompts.py      # NEW: per-section commentary prompt builders
  narrative_generator.py     # UNCHANGED: existing narrative generation
  narrative_prompts.py       # UNCHANGED: existing narrative prompts

src/do_uw/models/
  density.py                 # MODIFIED: add PreComputedCommentary, SectionCommentary models

src/do_uw/stages/render/context_builders/
  assembly_commentary.py     # NEW: @register_builder for commentary context

src/do_uw/templates/html/
  macros/dual_voice.html.j2  # NEW: Jinja2 macro for dual-voice block
  sections/                  # MODIFIED: 8 section templates add dual-voice include
```

### Anti-Patterns to Avoid
- **Putting commentary generation in RENDER stage**: RENDER must be purely formatting. All LLM calls happen in BENCHMARK.
- **Generating commentary and narratives in the same LLM call**: Keep them separate -- different purposes, different prompt engineering, and narrative generation already works. Commentary is additive.
- **Hardcoding SCA theory text in templates**: SCA theory references come from the LLM prompt, informed by brain YAML `do_context` fields. Templates just display what was generated.
- **Re-extracting data already extracted for narratives**: Reuse `extract_section_data()` and `_signal_consumer.py` functions. Add signal aggregation on top, don't rebuild.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dollar amount validation | Custom regex parser | `validate_narrative_amounts()` in narrative_generator.py | Already battle-tested from Phase 129 |
| Signal result aggregation | Raw dict traversal | `get_signals_by_prefix()`, `get_signal_do_context()` from _signal_consumer.py | Typed, cached, handles missing data |
| Section data extraction | New extractors | `extract_section_data()` dispatch in narrative_data.py | Already extracts per-section data for LLM prompts |
| Confidence derivation | New logic | `derive_section_confidence()` from _bull_bear.py | Already computes dominant confidence tier from signals |
| Key findings extraction | New logic for negatives/positives | `_build_bull_items_from_positives()` / `_build_bear_items_from_negatives()` from _bull_bear.py | Already mines state for bull/bear items |
| Finding enrichment | New narrative builder | `build_negative_narrative()` / `build_positive_narrative()` from sect1_findings.py | Already builds title + rich body |

## Common Pitfalls

### Pitfall 1: LLM Cost Explosion
**What goes wrong:** Adding 8 new LLM calls per section doubles the API cost per run.
**Why it happens:** Each section gets a separate commentary call.
**How to avoid:** Use claude-haiku-4-5 (cheapest model, already used for narratives). Keep max_tokens bounded (600-1200 per section based on density tier). Consider combining 2-3 sections per call if cost is excessive. The in-memory cache prevents re-generation within the same run.
**Warning signs:** Run cost exceeding $0.50 total for commentary generation.

### Pitfall 2: Generic Commentary
**What goes wrong:** Commentary reads like it could apply to any company -- violates QUAL-04.
**Why it happens:** Prompt doesn't include enough company-specific context.
**How to avoid:** Pass full signal results (with actual values), scoring factor deductions (with exact points), and brain YAML `do_context` strings as prompt context. The `do_context` fields in brain YAML contain the D&O theory framework -- use them to anchor the LLM's output in specific litigation theories. Example: pass `"FIN.ACCT.quality_indicators do_context: 'Altman Z-Score below 1.81 places company in distress zone, elevating going-concern allegations...'"`.
**Warning signs:** Any sentence that passes the "change the company name" test.

### Pitfall 3: Hallucinated Dollar Amounts in Commentary
**What goes wrong:** LLM fabricates financial figures in commentary text (the $383B hallucination from FIX-01).
**Why it happens:** LLM generates plausible-sounding but incorrect numbers.
**How to avoid:** Apply `validate_narrative_amounts()` to every generated commentary. Log warnings for any divergence >2x from known state values. Include XBRL-reconciled numbers in the prompt context so the LLM has correct figures to reference.
**Warning signs:** Warnings in log from validate_narrative_amounts().

### Pitfall 4: "What Was Said" Duplicating Existing Narratives
**What goes wrong:** The "What Was Said" block repeats the existing SCR/5-layer narrative verbatim, adding bulk without value.
**Why it happens:** Both serve a similar purpose of summarizing section data.
**How to avoid:** "What Was Said" should be a crisp 2-4 sentence factual summary (numbers only, no interpretation). Existing narratives (SCR/5-layer) provide the analytical assessment. The dual-voice block complements existing narratives -- it doesn't replace them. Position the dual-voice block at the TOP of each section, before the detailed data tables.
**Warning signs:** Reader sees the same content twice in different formatting.

### Pitfall 5: Commentary Not Cached Properly
**What goes wrong:** Commentary regenerated on every render, wasting API calls and producing non-deterministic output.
**Why it happens:** State model doesn't persist commentary, or `--fresh` flag not respected.
**How to avoid:** Store on `state.analysis.pre_computed_commentary` (Pydantic model). This automatically serializes to `state.json` cache. On re-render, check if commentary exists and skip generation. Only regenerate when `--fresh` flag is set (which resets all stages).
**Warning signs:** LLM API calls happening during RENDER stage.

### Pitfall 6: Breaking Existing Narrative Architecture
**What goes wrong:** Commentary generation interferes with existing narrative generation (5-layer, SCR, D&O implications).
**Why it happens:** Both share data extraction functions; modifications break the existing pipeline.
**How to avoid:** Commentary is a NEW parallel path. New functions (`generate_all_commentary`, `build_commentary_prompt`), new model (`PreComputedCommentary`), new context key (`commentary`). Do NOT modify existing `generate_all_narratives()`, `build_section_prompt()`, or `PreComputedNarratives`.
**Warning signs:** Existing narrative tests fail.

## Code Examples

### Commentary Pydantic Model (density.py addition)

```python
# Source: Pattern follows PreComputedNarratives in density.py

class SectionCommentary(BaseModel):
    """Dual-voice commentary for a single section."""
    what_was_said: str = Field(
        default="",
        description="Factual data summary -- numbers, dates, names only",
    )
    underwriting_commentary: str = Field(
        default="",
        description="D&O risk interpretation with SCA litigation theory refs",
    )
    confidence: str = Field(
        default="MEDIUM",
        description="HIGH/MEDIUM/LOW based on signal evaluation coverage",
    )
    hallucination_warnings: list[str] = Field(
        default_factory=list,
        description="Warnings from validate_narrative_amounts()",
    )


class PreComputedCommentary(BaseModel):
    """LLM-generated dual-voice commentary pre-computed in BENCHMARK."""
    executive_brief: SectionCommentary | None = None
    financial: SectionCommentary | None = None
    market: SectionCommentary | None = None
    governance: SectionCommentary | None = None
    litigation: SectionCommentary | None = None
    scoring: SectionCommentary | None = None
    company: SectionCommentary | None = None
    meeting_prep: SectionCommentary | None = None
```

### Commentary Prompt Pattern

```python
# Source: Pattern follows narrative_prompts.py SECTION_PROMPT_BUILDERS

COMMENTARY_RULES = (
    "You are writing DUAL-VOICE commentary for a D&O underwriting worksheet section.\n"
    "Return TWO clearly labeled sections:\n"
    "WHAT WAS SAID:\n"
    "[2-4 sentences. ONLY facts: dollar amounts, percentages, dates, names. "
    "No interpretation. No opinion. This is what the filings/data show.]\n\n"
    "UNDERWRITING COMMENTARY:\n"
    "[3-6 sentences. D&O risk interpretation. Reference specific SCA litigation "
    "theories by name (Section 10(b) scienter, loss causation, Section 11 strict "
    "liability, going-concern allegations, broken business narrative, Caremark "
    "duty of oversight, duty of candor). Cite scoring factor references "
    "(e.g., 'F.7 = 5/8'). Explain WHY this matters for D&O claims.]\n\n"
    "Rules:\n"
    "- Every sentence MUST contain company-specific data.\n"
    "- In WHAT WAS SAID: zero interpretation, zero opinion.\n"
    "- In UNDERWRITING COMMENTARY: every claim connects to a named SCA theory.\n"
    "- Reference scoring factors where relevant (F1-F10).\n"
    "- No generic phrases. No hedging. No filler.\n"
)
```

### Signal Context Aggregation for Commentary

```python
# Source: Reuses _signal_consumer.py API

def extract_commentary_context(
    state: AnalysisState, section_id: str,
) -> dict[str, Any]:
    """Extract enriched context for commentary generation.

    Includes everything from extract_section_data() PLUS:
    - Signal results with do_context strings
    - Scoring factor details
    - Section density and confidence
    """
    from do_uw.stages.benchmark.narrative_data import extract_section_data
    from do_uw.stages.render.context_builders._signal_consumer import (
        get_signals_by_prefix, get_signal_do_context,
    )
    from do_uw.stages.render.context_builders._bull_bear import (
        derive_section_confidence,
    )

    # Base data from existing extraction
    data = extract_section_data(state, section_id)

    # Enrich with signal results and do_context
    if state.analysis and state.analysis.signal_results:
        sr = state.analysis.signal_results
        prefix_map = {
            "financial": ["FIN."],
            "market": ["STOCK.", "FWRD."],
            "governance": ["GOV.", "EXEC."],
            "litigation": ["LIT."],
            "scoring": ["BIZ."],
            "company": ["BIZ."],
        }
        prefixes = prefix_map.get(section_id, [])
        triggered = []
        do_contexts = []
        for prefix in prefixes:
            signals = get_signals_by_prefix(sr, prefix)
            for sig in signals:
                if sig.status == "TRIGGERED":
                    triggered.append({
                        "id": sig.signal_id,
                        "value": sig.value,
                        "evidence": sig.evidence[:200],
                        "do_context": sig.do_context[:300],
                        "factors": list(sig.factors),
                    })
                if sig.do_context:
                    do_contexts.append(sig.do_context[:200])
        data["triggered_signals"] = triggered[:10]
        data["do_context_refs"] = do_contexts[:8]

    # Section confidence
    data["section_confidence"] = derive_section_confidence(state, section_id)

    return data
```

### Executive Summary Negative with SCA Theory

```python
# Source: Extension of existing build_negative_narrative() in sect1_findings.py

# SCA theory mapping based on finding characteristics
SCA_THEORY_MAP = {
    "stock_drop": "Section 10(b)/Rule 10b-5: stock decline may constitute corrective disclosure",
    "earnings_miss": "Section 10(b) scienter: management knew or should have known guidance was unachievable",
    "restatement": "Section 10(b) + Section 11: dual exposure from material misstatements",
    "insider_selling": "Scienter inference: insider sales during class period establish motive and opportunity",
    "going_concern": "Going-concern allegations: Z-Score distress zone invites Section 10(b) claims",
    "governance_failure": "Caremark duty of oversight: board failed to implement adequate reporting systems",
    "guidance_miss": "Forward-looking statement liability: PSLRA safe harbor defense weakened by miss",
    "audit_weakness": "SOX Section 302/906 exposure: material weakness in internal controls",
    "regulatory_action": "SEC enforcement: regulatory investigation establishes corrective disclosure timeline",
    "activist_pressure": "Breach of fiduciary duty: activist campaign may trigger derivative claims",
}

SCA_DEFENSE_MAP = {
    "beat_and_raise": "Consistent beat-and-raise pattern removes the #1 allegation vector (forward guidance fraud)",
    "no_sca_history": "Clean litigation history: no prior SCA filing reduces recurrence probability",
    "strong_controls": "Clean SOX assessment: material weakness defense eliminates Section 302 exposure",
    "high_independence": "Strong board independence: reduces Caremark derivative claim viability",
    "low_insider_selling": "Minimal insider sales: undermines scienter motive-and-opportunity inference",
    "stable_auditor": "Long-tenure Big 4 auditor: audit quality defense strengthens 10(b) defense",
    "market_driven_decline": "Stock decline attributable to market/sector: loss causation defense available",
}
```

### CSS for Dual-Voice Blocks

```css
/* Source: New CSS for dual-voice pattern */
.dual-voice {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}
.dual-voice__factual {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 1rem;
}
.dual-voice__commentary {
  background: #1a2744;  /* navy/blue-gray */
  color: #e8edf3;
  border: 1px solid #2a3754;
  border-radius: 6px;
  padding: 1rem;
}
.dual-voice__header {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.dual-voice__factual .dual-voice__header { color: #495057; }
.dual-voice__commentary .dual-voice__header { color: #8fa4c4; }
.confidence-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-weight: 500;
}
.confidence-badge--high { background: #10b981; color: #fff; }
.confidence-badge--medium { background: #f59e0b; color: #000; }
.confidence-badge--low { background: #ef4444; color: #fff; }
```

## SCA Litigation Theory Reference Framework

The LLM prompts must reference these named theories. This list should be included in commentary prompts.

### Plaintiff Theories (Key Negatives Reference)
| Theory | Legal Basis | Trigger Pattern |
|--------|-------------|-----------------|
| Securities fraud | Section 10(b) / Rule 10b-5 | Material misstatement + stock drop |
| Scienter (knowledge) | Tellabs v. Makor | Insider selling during class period, internal docs |
| Loss causation | Dura Pharmaceuticals v. Broudo | Corrective disclosure + economic loss |
| Strict liability (IPO/SPO) | Section 11, Securities Act 1933 | Misstatement in registration statement |
| Forward guidance fraud | PSLRA safe harbor exception | Guidance given with actual knowledge of falsity |
| Going-concern allegations | Section 10(b) | Z-Score distress + failure to disclose |
| Broken business narrative | Section 10(b) | Touted business model fails, stock drops |
| Oversight failure | Caremark / Marchand v. Barnhill | Board failed monitoring of known risk |
| Duty of candor | Fiduciary duty | Directors misled shareholders in proxy |
| Restatement exposure | Section 10(b) + Section 11 | Financial restatement as corrective disclosure |

### Defense Theories (Key Positives Reference)
| Defense | Legal Basis | Evidence Pattern |
|---------|-------------|-----------------|
| PSLRA safe harbor | Private Securities Litigation Reform Act | Forward-looking statement with meaningful cautionary language |
| Loss causation defense | Dura Pharmaceuticals | Decline attributable to market/sector, not company-specific |
| No scienter | Tellabs | No insider selling, no contradicting internal documents |
| Puffery defense | Omnicare v. Laborers | Statements too vague to be actionable |
| Truth-on-the-market | Efficient market theory | Risk already known to market |
| Clean audit trail | SOX 302/906 | No material weakness, clean internal controls |
| Beat-and-raise pattern | Forward guidance credibility | Consistent delivery removes guidance fraud vector |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rule-based narratives only | LLM per-section narratives in BENCHMARK | Phase 35 | Company-specific assessment text |
| Generic D&O implications map | State-aware implication generators | Phase 119 | Context-dependent D&O commentary |
| Single narrative voice | 5-layer narrative (verdict/thesis/evidence/implications/deep context) | Phase 113 | Structured analytical framework |
| No cross-validation | validate_narrative_amounts() | Phase 129 | Anti-hallucination for dollar figures |

**Current LLM calls per run:** ~9 (7 section narratives + 1 exec thesis + 1 meeting prep questions). Phase 130 adds ~8 more (commentary per section), bringing total to ~17.

## Key Implementation Details

### Where Commentary Fits in the BENCHMARK Pipeline

```python
# In stages/benchmark/__init__.py, after Step 8:
# Step 8.5: Pre-compute dual-voice commentary
self._precompute_commentary(state)
```

### Data Available Per Section for Commentary

| Section | Signal Prefixes | Scoring Factors | Key Data Points |
|---------|----------------|-----------------|-----------------|
| Financial | FIN.* | F3 (Financial Health) | Revenue, net income, Altman Z, Beneish M, ratios |
| Market | STOCK.*, FWRD.* | F2 (Stock Drop), F7 (Insider Selling) | Price, drops, insider activity, short interest |
| Governance | GOV.*, EXEC.* | F6 (Governance) | Board size, independence, comp, forensics |
| Litigation | LIT.* | F1 (Litigation), F5 (Regulatory), F9 (Industry) | Active SCAs, settlements, SEC enforcement |
| Scoring | BIZ.* | All F1-F10 | Quality score, tier, red flags, patterns |
| Company | BIZ.* | (profile-level) | MCap, sector, employees, business description |
| Executive Brief | ALL | ALL | Aggregate of all sections + tier + probability |
| Meeting Prep | ALL | Top risk factors | Findings, red flags, SCA count |

### Existing Functions to Reuse

| Function | Location | Reuse For |
|----------|----------|-----------|
| `extract_section_data()` | narrative_data.py | Base data extraction per section |
| `extract_company/financial/market/governance/litigation()` | narrative_data_sections.py | Section-specific data |
| `extract_state_summary()` | narrative_data.py | Exec summary context |
| `get_signals_by_prefix()` | _signal_consumer.py | Signal result aggregation |
| `get_signal_do_context()` | _signal_consumer.py | Brain YAML D&O theory text |
| `derive_section_confidence()` | _bull_bear.py | Confidence badge derivation |
| `validate_narrative_amounts()` | narrative_generator.py | Dollar amount cross-validation |
| `_extract_known_values()` | narrative_generator.py | Known values for validation |
| `build_negative_narrative()` | sect1_findings.py | Enriched negative formatting |
| `build_positive_narrative()` | sect1_findings.py | Enriched positive formatting |

### Template Files Requiring Modification

| Template | Change Type |
|----------|-------------|
| `sections/executive_brief.html.j2` | Major overhaul -- recommendation para, SCA theories in findings |
| `sections/financial.html.j2` | Add dual-voice block before detail tables |
| `sections/market.html.j2` | Add dual-voice block |
| `sections/governance.html.j2` | Add dual-voice block |
| `sections/litigation.html.j2` | Add dual-voice block |
| `sections/scoring.html.j2` | Add dual-voice block |
| `sections/company.html.j2` | Add dual-voice block |
| `macros/` (new file) | Dual-voice Jinja2 macro |
| `styles.css` or `components.css` | Dual-voice CSS |

## Open Questions

1. **Cost optimization: Can multiple sections share one LLM call?**
   - What we know: Current architecture makes 1 call per section. Haiku is cheap (~$0.001/section).
   - What's unclear: Whether a single call with 8 section contexts produces better or worse output.
   - Recommendation: Start with 1 call per section (simpler, more reliable). Optimize to batch later if cost is a concern. At ~$0.008 for 8 Haiku calls, cost is negligible.

2. **Commentary placement: Before or after existing narrative?**
   - What we know: HNGE puts dual-voice at end of each subsection. Our sections have 5-layer narrative at top.
   - What's unclear: Whether dual-voice should precede or follow existing content.
   - Recommendation: Place dual-voice block at TOP of each section, immediately after the section header and before any detail tables. This gives the "executive reader" the summary upfront without scrolling through data. The existing 5-layer narrative can be removed or integrated into the "What Was Said" side in a future phase.

3. **"What Was Said" source: LLM-generated or rule-based?**
   - What we know: User decision says "LLM with full signal context." HNGE's "What Was Said" reads like a human summary.
   - What's unclear: Whether the LLM should generate both voices in one call or two.
   - Recommendation: One LLM call per section that returns BOTH "What Was Said" and "Underwriting Commentary" as structured output. The prompt instructs the LLM to produce both, and we parse the response. This halves the number of API calls vs generating each voice separately.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/ -x -q --timeout=30` |
| Full suite command | `uv run pytest tests/ -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VOICE-01 | Dual-voice blocks in 8 section templates | unit | `uv run pytest tests/stages/render/test_dual_voice_templates.py -x` | Wave 0 |
| VOICE-02 | Commentary LLM generation with signal context | unit | `uv run pytest tests/stages/benchmark/test_commentary_generator.py -x` | Wave 0 |
| VOICE-03 | Commentary cached on state model | unit | `uv run pytest tests/models/test_commentary_model.py -x` | Wave 0 |
| VOICE-04 | Cross-validation of commentary dollar amounts | unit | `uv run pytest tests/stages/benchmark/test_commentary_validation.py -x` | Wave 0 |
| EXEC-01 | Exec summary reads as underwriting assessment | integration | `uv run pytest tests/stages/render/test_exec_summary_overhaul.py -x` | Wave 0 |
| EXEC-02 | Key negatives have SCA theory refs | unit | `uv run pytest tests/stages/render/test_negative_sca_theories.py -x` | Wave 0 |
| EXEC-03 | Key positives have SCA defense refs | unit | `uv run pytest tests/stages/render/test_positive_sca_theories.py -x` | Wave 0 |
| EXEC-04 | Recommendation block has all required fields | unit | `uv run pytest tests/stages/render/test_recommendation_block.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/benchmark/ tests/stages/render/ -x -q --timeout=60`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/benchmark/test_commentary_generator.py` -- covers VOICE-02, VOICE-04
- [ ] `tests/models/test_commentary_model.py` -- covers VOICE-03
- [ ] `tests/stages/render/test_dual_voice_templates.py` -- covers VOICE-01
- [ ] `tests/stages/render/test_exec_summary_overhaul.py` -- covers EXEC-01 through EXEC-04

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/benchmark/narrative_generator.py` -- existing LLM narrative generation pattern
- `src/do_uw/stages/benchmark/narrative_prompts.py` -- existing prompt builder pattern
- `src/do_uw/stages/benchmark/narrative_data_sections.py` -- per-section data extractors
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- signal result typed API
- `src/do_uw/stages/render/context_builders/_bull_bear.py` -- bull/bear case and confidence
- `src/do_uw/stages/render/context_builders/company_exec_summary.py` -- exec summary context
- `src/do_uw/stages/render/context_builders/assembly_registry.py` -- builder registration
- `src/do_uw/stages/render/context_builders/narrative.py` -- 5-layer narrative + SCR + D&O implications
- `src/do_uw/models/density.py` -- PreComputedNarratives model pattern
- `src/do_uw/models/state.py` -- AnalysisResults storage pattern
- `src/do_uw/stages/benchmark/__init__.py` -- BENCHMARK pipeline steps
- `src/do_uw/templates/html/sections/executive_brief.html.j2` -- current exec summary template
- `src/do_uw/templates/html/sections/financial.html.j2` -- section template pattern
- `.planning/research/companion-system-features.md` -- HNGE dual-voice reference

### Secondary (MEDIUM confidence)
- SCA litigation theory framework -- based on standard securities litigation practice (Tellabs, Dura, Omnicare, Caremark, PSLRA)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, extends existing patterns
- Architecture: HIGH -- clear extension of existing narrative_generator.py pattern with new parallel path
- Pitfalls: HIGH -- based on direct observation of existing codebase and known issues (FIX-01 hallucination, QUAL-04 generic text)
- SCA theory framework: MEDIUM -- based on standard D&O underwriting practice, not verified against specific legal references

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain, no fast-moving dependencies)
