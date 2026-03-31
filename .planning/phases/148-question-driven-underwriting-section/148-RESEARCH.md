# Phase 148: Question-Driven Underwriting Section - Research

**Researched:** 2026-03-28
**Domain:** D&O underwriting question framework / auto-answerers / Supabase SCA integration
**Confidence:** HIGH

## Summary

Phase 148 completes the Underwriting Decision Framework section that was scaffolded in Phase 145. The pre-work established the YAML question schema (55 questions across 8 domains), the loader, template, and 8 initial answerers in `uw_questions.py`. The remaining work is implementing dedicated answerers for the other 47 questions, integrating Supabase SCA scenario questions inline, adding domain/section-level verdict roll-ups, and print CSS.

The pipeline data is rich enough to answer most questions. ORCL state.json shows 576 signal results (49 triggered, 392 clean, 158 skipped), 10 factor scores, risk card with scenario benchmarks, filing history, repeat filer detail, and 9 screening questions. The `uw_analysis.py` context builder already provides `ctx` with: `executive_summary`, `financials`, `governance`, `litigation`, `scoring`, `market`, `triggered_checks`, `enhanced_drop_events`, `forensic_composites`, `nlp_dashboard`, `settlement`, `peril`, `exec_risk`, `temporal`, `investigative`, plus raw `_state` access.

**Primary recommendation:** Organize answerers into domain-specific files (one per domain, ~7 functions each) under a new `answerers/` subpackage within context_builders. Each question gets a dedicated function. Supabase SCA questions are generated dynamically from `risk_card.scenario_benchmarks` and `risk_card.filing_history` and slotted into matching domains with an "SCA Data" badge.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Partial answers with inline flags -- answer with whatever structured data is available, mark missing pieces as "Needs Review" with specific filing references inline. Never punt entirely when partial data exists.
- **D-02:** LLM extraction for specific gaps -- use LLM against filing text for questions where data exists in narrative but isn't structurally extracted. Priority gaps: risk factors (BIZ-06, 10-K Item 1A), M&A activity (BIZ-05, 8-K/proxy), customer concentration (10-K Item 1/7), regulatory/compliance risks (OPS-01+, 10-K Item 1/1A).
- **D-03:** Always render the section regardless of answer rate -- low answer rates show "Needs Review" items which is useful information. No minimum threshold.
- **D-04:** SCA-derived questions integrate inline by domain -- slot into matching domains (SCA settlement -> Litigation, SCA filing frequency -> Litigation, SCA peer comparison -> Market, trigger patterns -> Market/Operational). Display with a "SCA Data" source badge to distinguish from brain-sourced questions.
- **D-05:** All four SCA scenario types generate questions: filing frequency & recidivism, settlement ranges & severity, peer SCA comparison, trigger pattern matching.
- **D-06:** All 8 domains built in parallel -- broad coverage across all domains simultaneously rather than sequential by priority.
- **D-07:** Dedicated answerer per question -- every question gets its own answerer function. Fully explicit, no ambiguity about which logic handles which question. Move away from generic category fallbacks in screening_answers.
- **D-08:** Keep current verdict dots (14px circles, green +/red -/gray =/amber ?) -- compact and scannable, matches CIQ aesthetic.
- **D-09:** Domain-level AND section-level verdict badges -- each domain header shows net assessment (Favorable/Unfavorable/Mixed) based on upgrade vs downgrade counts. Section header shows overall assessment. Maximum signal density.
- **D-10:** Print optimization required -- add @media print rules for completeness bars, small text, verdict dots, and domain groupings. These elements need explicit print treatment.

### Claude's Discretion
- LLM prompt design for filing text extraction (risk factors, M&A, concentration, regulatory)
- How to structure the per-question answerer files (one file per domain vs one file per question)
- Specific @media print CSS rules
- SCA question YAML schema details (question_id format, data_sources, answer_template)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QFW-01 | Define underwriting question framework in brain/questions/ as YAML files organized by domain | DONE in pre-work: 8 YAML files, 55 questions, loader in `__init__.py` |
| QFW-02 | Each question YAML specifies: question_id, text, weight, domain, data_sources, upgrade/downgrade criteria, why_it_matters, answer_template | DONE in pre-work: all fields present in YAML schema |
| QFW-03 | Expand auto-answer engine from 11 answerers to full coverage -- deep cross-referencing, actual numbers not vague assessments | 47 new answerers needed. Data paths mapped below per question. |
| QFW-04 | Supabase scenario-specific questions merge with brain domain questions -- company's scenario history determines which SCA questions appear | Risk card has `scenario_benchmarks`, `screening_questions`, `filing_history`, `repeat_filer_detail`. SCA questions generated from these 4 sources and slotted into domains. |
| QFW-05 | Section template renders questions grouped by domain, sorted by weight; summary bar shows answered/concerns/favorable/needs review | Template exists. Need domain-level verdict badges (D-09) and print CSS (D-10). |
| QFW-06 | "Needs Review" questions show exactly where to find the data -- specific filing references | `_suggest_filing_reference()` exists. Needs expansion for all data_sources patterns. |
| QFW-07 | Section positioned after Scoring, before Meeting Prep in the report | DONE in pre-work: wired into uw_analysis.html.j2 with nav button. |
</phase_requirements>

## Architecture Patterns

### Recommended File Structure

```
src/do_uw/stages/render/context_builders/
  answerers/                     # NEW subpackage
    __init__.py                  # Re-exports answer registry
    company.py                   # BIZ-01 through BIZ-06 (6 functions)
    financial.py                 # FIN-01 through FIN-08 (8 functions)
    governance.py                # GOV-01 through GOV-08 (8 functions)
    market.py                    # MKT-01 through MKT-07 (7 functions)
    litigation.py                # LIT-01 through LIT-07 (7 functions)
    operational.py               # OPS-01 through OPS-07 (7 functions)
    program.py                   # PRG-01 through PRG-05 (5 functions)
    decision.py                  # UW-01 through UW-07 (7 functions)
    sca_questions.py             # Dynamic SCA question generator
    _helpers.py                  # Shared utilities (safe_float, formatting, etc.)
  uw_questions.py                # MODIFIED: imports from answerers/ instead of inline
  screening_answers.py           # KEPT for risk card screening (separate from UW framework)
```

**Rationale for one-file-per-domain:** 55 answerers in one file would hit 500+ lines. One-per-question (55 files) is too granular. Domain files average ~200 lines each, stay under the 500-line limit, and group related data access patterns.

### Pattern: Answerer Function Signature

All answerer functions follow this signature (already established by pre-work):

```python
def _answer_biz_02(
    q: dict[str, Any],        # Question dict from YAML
    state: AnalysisState,      # Full pipeline state
    ctx: dict[str, Any],       # Render context (has executive_summary, financials, etc.)
) -> dict[str, Any]:
    """BIZ-02: Revenue concentration."""
    # ... access state and ctx ...
    return {
        "answer": "Revenue of $52.9B (FY2024). Enterprise software 78%, cloud 22%.",
        "evidence": ["Revenue: $52.9B", "Growth: 6.0% YoY", "Cloud revenue: $11.6B"],
        "verdict": "UPGRADE",     # UPGRADE | DOWNGRADE | NEUTRAL | NO_DATA
        "confidence": "HIGH",     # HIGH | MEDIUM | LOW
        "data_found": True,
    }
```

### Pattern: Registry in answerers/__init__.py

```python
# Central registry mapping question_id -> answerer function
ANSWERER_REGISTRY: dict[str, AnswererFunc] = {}

def register(*question_ids: str):
    """Decorator to register an answerer for one or more question IDs."""
    def wrapper(fn):
        for qid in question_ids:
            ANSWERER_REGISTRY[qid] = fn
        return fn
    return wrapper
```

Each domain file uses `@register("BIZ-02")` to self-register. The `uw_questions.py` builder imports `ANSWERER_REGISTRY` and uses it instead of the inline `_domain_answerers` dict.

### Pattern: SCA Question Generation (QFW-04)

SCA questions are generated dynamically, not from static YAML:

```python
def generate_sca_questions(state: AnalysisState) -> list[dict[str, Any]]:
    """Generate scenario-specific questions from Supabase risk card data.

    Returns question dicts matching the brain question schema but with
    source="SCA Data" badge and domain assignments for inline slotting.
    """
    lit_data = getattr(state.acquired_data, "litigation_data", None) or {}
    risk_card = lit_data.get("risk_card", {}) if isinstance(lit_data, dict) else {}

    questions = []
    # 1. Filing frequency & recidivism -> Litigation domain
    # 2. Settlement ranges & severity -> Litigation domain
    # 3. Peer SCA comparison -> Market domain
    # 4. Trigger pattern matching -> Market/Operational domain
    return questions
```

SCA questions use question_ids like `SCA-LIT-01`, `SCA-MKT-01` to avoid collision with brain question IDs. They carry `source: "SCA Data"` for the template badge.

### Pattern: Domain Verdict Roll-up (D-09)

```python
# In uw_questions.py, per domain:
net = domain_upgrades - domain_downgrades
if net > 0:
    domain_verdict = "FAVORABLE"
elif net < 0:
    domain_verdict = "UNFAVORABLE"
else:
    domain_verdict = "MIXED"

# In section header:
section_verdict = "FAVORABLE" if total_upgrades > total_downgrades else (
    "UNFAVORABLE" if total_downgrades > total_upgrades else "MIXED"
)
```

### Anti-Patterns to Avoid
- **Category fallback answerers** (D-07 explicitly bans this): every question gets a dedicated function, not a generic "financial" fallback
- **Vague assessments**: "Beneish inconclusive" is explicitly called out as failure -- always include the actual M-Score number
- **NO_DATA when partial data exists** (D-01): if any relevant data exists, answer with what you have and flag the gap

## Question-to-Data Mapping (All 55 Questions)

### Domain 1: Company & Business Model (6 questions)

| ID | Question | Data Source in State/Context | Pre-work |
|----|----------|----------------------------|----------|
| BIZ-01 | What does company do? | `ctx.executive_summary`, `yfinance.info.sector/industry`, `state.company.identity.sic_code` | DONE |
| BIZ-02 | Revenue concentration? | `ctx.financials` (revenue), `state.extracted.financials.statements` (segments), `yfinance.info.totalRevenue` | NEW |
| BIZ-03 | How long public, market cap? | `yfinance.info.marketCap`, `ctx.executive_summary.market_cap` | DONE |
| BIZ-04 | Employees, operations? | `yfinance.info.fullTimeEmployees`, `state.company.identity.headquarters` | NEW |
| BIZ-05 | Pending M&A? | `ctx.ma_profile`, signal_results with `MA.*` prefix, `state.extracted.governance` (8-K) | NEW - LLM extraction candidate |
| BIZ-06 | Key risk factors? | `state.extracted.risk_factors`, signal_results | NEW - LLM extraction candidate |

### Domain 2: Financial Health (8 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| FIN-01 | Profitable? | `ctx.financials`, `yfinance.info.revenueGrowth/ebitdaMargins`, `ctx.executive_summary.revenue` | DONE |
| FIN-02 | Balance sheet? | `ctx.financials`, `yfinance.info.debtToEquity/currentRatio` | DONE |
| FIN-03 | Beneish/Altman/forensics? | `ctx.financials.beneish_*`, `ctx.financials.altman_*`, `ctx.forensic_composites` | NEW |
| FIN-04 | Restatements? | signal_results `DISC.CTRL.*`, `state.extracted.financials.audit` | NEW |
| FIN-05 | Auditor, MW? | `ctx.financials.auditor_name`, `ctx.financials.audit_alerts`, signal_results `material_weakness` | NEW (overlap with screening ACCT-01/02) |
| FIN-06 | Cash flow? | `state.extracted.financials.statements` (OCF, FCF), `yfinance.info.operatingCashflow/freeCashflow` | NEW |
| FIN-07 | Revenue recognition? | `yfinance.info.industry`, signal_results `rev_rec_*` | NEW (overlap with screening ACCT-05) |
| FIN-08 | GAAP vs non-GAAP? | signal_results `earnings_quality_*`, `ctx.financials.beneish_*` | NEW (overlap with screening ACCT-03) |

### Domain 3: Governance & People (8 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| GOV-01 | Board independence? | `ctx.governance.board_size/independence_pct/ceo_duality` | DONE |
| GOV-02 | CEO/director sued? | signal_results `exec_litigation_*`, `ctx.litigation`, `ctx.exec_risk` | NEW |
| GOV-03 | Comp alignment? | `state.extracted.governance.compensation`, `ctx.governance.ceo_comp/say_on_pay` | NEW |
| GOV-04 | Related party txns? | signal_results `related_party_*`, `state.extracted.governance` | NEW |
| GOV-05 | Director tenure/changes? | `state.extracted.governance.board.directors` (tenure field) | NEW |
| GOV-06 | D&O experience? | `state.extracted.governance.board.directors` (qualifications) | NEW |
| GOV-07 | Character/integrity? | signal_results `exec_risk_*`, `ctx.exec_risk` | NEW |
| GOV-08 | Dual-class/controlled? | signal_results `controlled_company`, `state.extracted.governance.ownership` | NEW |

### Domain 4: Stock & Market (7 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| MKT-01 | Stock drops >15%? | `ctx.enhanced_drop_events`, `yfinance.info.52wHigh/Low` | DONE |
| MKT-02 | Short interest? | `yfinance.info.shortPercentOfFloat/shortRatio` | NEW (overlap with screening UNIV-02) |
| MKT-03 | DDL exposure? | `yfinance.info.marketCap`, `ctx.settlement` | NEW (overlap with screening UNIV-04) |
| MKT-04 | Insider trading? | `state.acquired_data.market_data.insider_transactions`, signal_results `insider_*` | NEW (overlap with screening INSIDER-01) |
| MKT-05 | Institutional holders? | `state.acquired_data.market_data.institutional_holders` | NEW |
| MKT-06 | Near highs or lows? | `yfinance.info.fiftyTwoWeekHigh/Low/currentPrice` | NEW |
| MKT-07 | Equity/debt issuance? | signal_results `offering_*`, `state.extracted.sec_filings` | NEW |

### Domain 5: Litigation & Claims (7 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| LIT-01 | SCA history? | `ctx.litigation.risk_card_*`, `ctx.litigation.cases` | DONE |
| LIT-02 | Active lawsuits? | `ctx.litigation.cases` (filter active), `state.extracted.litigation` | NEW |
| LIT-03 | Settlement history? | `ctx.litigation.risk_card_filing_history`, `ctx.litigation.risk_card_repeat_filer` | NEW |
| LIT-04 | SEC enforcement? | signal_results `sec_enforcement_*`, `state.acquired_data.regulatory_data` | NEW |
| LIT-05 | Litigation theories? | `ctx.peril`, `state.scoring.allegation_mapping` | NEW |
| LIT-06 | Non-SCA lawsuits? | signal_results `regulatory_*`, `state.acquired_data.web_search_results` | NEW |
| LIT-07 | SOL window? | `ctx.temporal`, `ctx.enhanced_drop_events` | NEW |

### Domain 6: Operational & Emerging (7 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| OPS-01 | Cybersecurity? | signal_results `cyber_*`, `state.extracted.risk_factors` | NEW - LLM extraction candidate |
| OPS-02 | Regulatory changes? | signal_results `regulatory_*`, `state.extracted.risk_factors` | NEW - LLM extraction candidate |
| OPS-03 | ESG/climate? | signal_results `esg_*`, `state.alt_data` | NEW |
| OPS-04 | Customer/supplier concentration? | `state.extracted.financials.statements` (segments), signal_results `concentration_*` | NEW - LLM extraction candidate |
| OPS-05 | Tariff/geopolitical? | signal_results `tariff_*`, `state.alt_data` | NEW |
| OPS-06 | High-frequency sector? | `state.company.identity.sic_code`, risk_card `scenario_benchmarks` | NEW |
| OPS-07 | Forward events? | `state.forward_looking`, `state.analysis.temporal_signals` | NEW |

### Domain 7: Program & Pricing (5 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| PRG-01 | Tower adequacy? | `state.scoring.tower_recommendation`, `yfinance.info.marketCap` | NEW |
| PRG-02 | Claims history? | `ctx.litigation.risk_card_filing_history`, `state.scoring.claim_probability` | NEW |
| PRG-03 | Peer pricing? | `state.benchmark`, `state.scoring.actuarial_pricing` | NEW |
| PRG-04 | Retention level? | `state.scoring.tower_recommendation`, `yfinance.info.marketCap` | NEW |
| PRG-05 | Coverage gaps? | `state.scoring.allegation_mapping` (theories that need exclusion) | NEW |

### Domain 8: Underwriting Decision (7 questions)

| ID | Question | Data Source | Pre-work |
|----|----------|-------------|----------|
| UW-01 | Risk tier? | `ctx.scoring.risk_tier/total_score` | DONE |
| UW-02 | Top 3 reasons to write? | `state.scoring.factor_scores` (lowest deductions = strengths), signal_results (CLEAN) | NEW |
| UW-03 | Top 3 reasons NOT to write? | `state.scoring.red_flags`, `state.scoring.factor_scores` (highest deductions) | NEW |
| UW-04 | Required conditions? | `state.scoring.allegation_mapping`, `state.scoring.red_flags` | NEW |
| UW-05 | Right price? | `state.scoring.actuarial_pricing`, `state.scoring.severity_scenarios` | NEW |
| UW-06 | Decline triggers? | `state.scoring.red_flags`, `state.scoring.ceiling_details` | NEW |
| UW-07 | Follow-up needed? | `state.analysis.disposition_summary` (SKIPPED signals), low confidence data | NEW |

## LLM Extraction Strategy (D-02)

Four questions need LLM extraction from filing text already in state:

| Question | Filing | Section | What to Extract |
|----------|--------|---------|-----------------|
| BIZ-05 | 8-K, proxy | Item 1.01 | M&A announcements, merger agreements, deal terms |
| BIZ-06 | 10-K | Item 1A | Top 5 risk factors by D&O relevance, novel disclosures |
| OPS-01 | 10-K | Item 1/1A | Cybersecurity program description, breach history, data types held |
| OPS-04 | 10-K | Item 1/7 | Customer concentration %, top customers, single-source suppliers |

**Implementation:** Use the existing `instructor`-based extraction pattern from `stages/extract/llm/extractor.py`. Create targeted Pydantic schemas for each extraction. Cache results in `state.acquired_data.llm_extractions` (already exists). Cost: ~$0.02/question at Haiku pricing, total ~$0.08 per analysis run.

**LLM extraction is optional** -- if filing text isn't available, the answerer returns partial answer from other sources with "Needs Review" flag for the LLM-dependent portion.

## SCA Question Integration Architecture (QFW-04, D-04, D-05)

### Data Available from Risk Card

From ORCL state.json inspection:

```python
risk_card = {
    "filing_history": [...],           # 5 filings for ORCL
    "repeat_filer_detail": {
        "recency_tier": ...,
        "filer_category": ...,
        "company_settlement_rate_pct": ...,
        "total_settlement_exposure_m": ...
    },
    "scenario_benchmarks": [{          # 1 scenario for ORCL: accounting_fraud
        "scenario": "accounting_fraud",
        "settle_p25_m": 3.5,
        "settle_p75_m": 32.73,
        "settle_p90_m": 114.06,
        "n_settlements": 1199,
        "settle_mean_m": 69.8,
        "total_filings": 2402,
        "settle_median_m": 10.0,
        "avg_stock_drop_pct": 20.5,
        "dismissal_rate_pct": 44.5,
        "sec_inv_severity_multiplier": 11.7,
        "restatement_severity_multiplier": 3.2,
    }],
    "company_profile": {
        "scenario_history": ["accounting_fraud"],
        "composite_risk_score": ...,
        "risk_score_components": {...},
        ...
    },
    "screening_questions": [...]       # 9 pre-built screening questions
}
```

### Four SCA Question Types -> Domain Mapping

| SCA Type | Generated Questions | Target Domain | Data Source |
|----------|-------------------|---------------|-------------|
| Filing frequency & recidivism | "Company has N SCA filings; filer category is X. How does this compare to {sector} peers?" | Litigation | `repeat_filer_detail`, `filing_history` |
| Settlement ranges & severity | "For {scenario} cases, median settlement is ${X}M (P90: ${Y}M). What's the company's exposure?" | Litigation | `scenario_benchmarks` |
| Peer SCA comparison | "Sector has {X} annual filings. This company's rate is {Y}x the peer average." | Market | `scenario_benchmarks.total_filings`, sector data |
| Trigger pattern matching | "Company matches {scenario} pattern: avg stock drop {X}%, dismissal rate {Y}%." | Market/Operational | `scenario_benchmarks.*_multiplier` |

### SCA Question Schema

```yaml
# Generated dynamically, not stored in YAML
question_id: SCA-LIT-01
text: "What's the company's SCA filing frequency and recidivism category?"
weight: 9
source: "SCA Data"              # Distinguishes from brain questions
domain: litigation_claims        # Slotted into matching domain
data_sources: [supabase_sca]
answer_template: "{filer_category} filer — {n_filings} filings..."
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Financial formatting | Custom number formatters | Existing `_fmt_currency()` and `_fmt_pct()` from `screening_answers.py` | Already handles B/M/T abbreviations correctly |
| Safe value extraction | Bare `float()` calls | `safe_float()` from `stages/render/formatters.py` | CLAUDE.md non-negotiable: LLM data contains "N/A", "13.2%" that crash bare float() |
| SourcedValue unwrapping | Manual `.value` checks | Existing `_sv()` helper from `screening_answers.py` | Handles both SourcedValue objects and raw values |
| LLM extraction | New extraction pipeline | Existing `instructor` + Pydantic schema pattern from `stages/extract/llm/` | Already has caching, cost tracking, retry logic |
| Filing reference suggestions | Per-question hardcoded refs | Existing `_suggest_filing_reference()` in `uw_questions.py` | Already maps data_sources to filing types |

## Common Pitfalls

### Pitfall 1: Vague Assessments Without Numbers
**What goes wrong:** Answerer returns "Beneish inconclusive" instead of "Beneish M-Score: -2.31 (safe zone, threshold: -1.78)"
**Why it happens:** Easy to check presence/absence without formatting the actual value
**How to avoid:** Every answerer must include the raw number in the answer string. Success criteria explicitly calls this out.
**Warning signs:** `answer` field that could apply to any company if you swap the name

### Pitfall 2: NO_DATA When Partial Data Exists (D-01)
**What goes wrong:** A question about "revenue concentration" returns NO_DATA because segment data is missing, even though total revenue is available
**Why it happens:** Checking for the ideal data path and giving up when it's not there
**How to avoid:** Each answerer should check 2-3 fallback paths. Return partial answer with inline "Needs Review" for the missing piece.
**Warning signs:** High NO_DATA rate on questions where some data clearly exists

### Pitfall 3: File Size Explosion
**What goes wrong:** `uw_questions.py` grows past 500 lines as all 55 answerers get added inline
**Why it happens:** Taking the path of least resistance
**How to avoid:** Answerers subpackage with domain files from the start (architecture section above)
**Warning signs:** Any single file approaching 400 lines

### Pitfall 4: Duplicate Logic with screening_answers.py
**What goes wrong:** New answerers duplicate logic from the 11 existing screening answerers (UNIV-01/02/03/04, ACCT-01-05, INSIDER-01/02)
**Why it happens:** The brain framework questions (MKT-02, FIN-05, FIN-07, FIN-08, MKT-04) overlap with screening questions
**How to avoid:** For overlapping questions, extract shared logic into `answerers/_helpers.py`. The new dedicated answerers can call helper functions. Don't duplicate the analysis logic.
**Warning signs:** Copy-pasted code blocks between answerers/ and screening_answers.py

### Pitfall 5: SCA Questions Absent for Non-SCA Companies
**What goes wrong:** Companies with no SCA history show zero SCA questions, losing the "clean record" upgrade signal
**Why it happens:** Only generating SCA questions when `scenario_history` is non-empty
**How to avoid:** Always generate at least the filing frequency question (SCA-LIT-01). For companies with no filings, it answers "FIRST_TIME filer -- no SCA history" which is an UPGRADE verdict.
**Warning signs:** SCA question count is 0 for companies that DO have Supabase data

### Pitfall 6: Context Ordering -- uw_questions Runs Before Extended Contexts
**What goes wrong:** Answerers reference `ctx.peril` or `ctx.settlement` which haven't been built yet
**Why it happens:** In `uw_analysis.py`, `build_uw_questions_context` is called at line 213, but peril/settlement/exec_risk are built at lines 218-222
**How to avoid:** Move `build_uw_questions_context` call AFTER all extended contexts are built (after line 228). This is a one-line change in uw_analysis.py.
**Warning signs:** Answerers return NO_DATA for questions where the data exists but ctx key is missing

## Code Examples

### Example: Dedicated Answerer with Multiple Fallbacks

```python
# answerers/financial.py
from do_uw.stages.render.context_builders.answerers import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    safe_float_extract, fmt_currency, fmt_pct, sv,
)

@register("FIN-03")
def _answer_fin_03(q, state, ctx):
    """FIN-03: Earnings quality red flags (Beneish, Altman, forensics)."""
    fin = ctx.get("financials", {})
    forensic = ctx.get("forensic_composites", {})

    evidence = []
    verdict_signals = []

    # Beneish M-Score
    beneish = fin.get("beneish_score")
    beneish_level = fin.get("beneish_level", "")
    if beneish is not None:
        evidence.append(f"Beneish M-Score: {beneish}")
        if "manipulator" in str(beneish_level).lower():
            verdict_signals.append("DOWNGRADE")
        elif "safe" in str(beneish_level).lower() or "unlikely" in str(beneish_level).lower():
            verdict_signals.append("UPGRADE")

    # Altman Z-Score
    altman = fin.get("altman_z_score")
    altman_zone = fin.get("altman_zone", "")
    if altman is not None:
        evidence.append(f"Altman Z-Score: {altman} ({altman_zone})")
        if "distress" in str(altman_zone).lower():
            verdict_signals.append("DOWNGRADE")
        elif "safe" in str(altman_zone).lower():
            verdict_signals.append("UPGRADE")

    # Forensic composites
    if isinstance(forensic, dict) and forensic.get("flags"):
        n_flags = len(forensic["flags"])
        evidence.append(f"Forensic flags: {n_flags}")
        if n_flags >= 3:
            verdict_signals.append("DOWNGRADE")

    if not evidence:
        return {"verdict": "NO_DATA", "data_found": False}

    # Determine overall verdict
    if "DOWNGRADE" in verdict_signals:
        verdict = "DOWNGRADE"
    elif verdict_signals and all(v == "UPGRADE" for v in verdict_signals):
        verdict = "UPGRADE"
    else:
        verdict = "NEUTRAL"

    # Build answer with ACTUAL NUMBERS
    parts = []
    if beneish is not None:
        parts.append(f"Beneish M-Score: {beneish} ({beneish_level})")
    if altman is not None:
        parts.append(f"Altman Z-Score: {altman} ({altman_zone})")
    answer = ". ".join(parts) + "."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH" if beneish is not None and altman is not None else "MEDIUM",
        "data_found": True,
    }
```

### Example: SCA Question Generator

```python
# answerers/sca_questions.py
def generate_sca_questions(state):
    """Generate SCA-derived questions from risk card data."""
    lit_data = getattr(state.acquired_data, "litigation_data", None) or {}
    risk_card = lit_data.get("risk_card", {}) if isinstance(lit_data, dict) else {}
    if not risk_card:
        return []

    questions = []
    repeat = risk_card.get("repeat_filer_detail", {})
    history = risk_card.get("filing_history", [])
    benchmarks = risk_card.get("scenario_benchmarks", [])
    profile = risk_card.get("company_profile", {})

    # Type 1: Filing frequency & recidivism -> Litigation
    questions.append({
        "question_id": "SCA-LIT-01",
        "text": "What is the company's SCA filing frequency and recidivism category?",
        "weight": 9,
        "source": "SCA Data",
        "domain": "litigation_claims",
        "data_sources": ["supabase_sca"],
        "_risk_card": risk_card,  # Pass data for answerer
    })

    # Type 2: Settlement severity per scenario -> Litigation
    for bench in benchmarks:
        scenario = bench.get("scenario", "unknown")
        questions.append({
            "question_id": f"SCA-LIT-{scenario[:8].upper()}",
            "text": f"What are the settlement benchmarks for {scenario.replace('_', ' ')} scenarios?",
            "weight": 9,
            "source": "SCA Data",
            "domain": "litigation_claims",
            "data_sources": ["supabase_sca"],
            "_benchmark": bench,
        })

    # Type 3: Peer comparison -> Market
    # Type 4: Trigger patterns -> Operational
    # ... similar pattern ...

    return questions
```

### Example: Template Additions for Domain Verdict Badge (D-09)

```html
{# Domain header with verdict badge #}
<div style="display:flex;justify-content:space-between;...">
  <div>
    <span style="font-size:9pt;font-weight:700;color:#1F3A5C">{{ domain.domain_label }}</span>
    <span style="font-size:7pt;color:#6B7280;margin-left:6px">{{ domain.answered_count }}/{{ domain.total_count }}</span>
  </div>
  <div style="display:flex;gap:4px;align-items:center">
    {# NEW: Domain verdict badge #}
    <span style="padding:1px 5px;border-radius:6px;font-size:6pt;font-weight:700;
      background:{% if domain.verdict == 'FAVORABLE' %}#065F46{% elif domain.verdict == 'UNFAVORABLE' %}#991B1B{% else %}#374151{% endif %};
      color:white">{{ domain.verdict }}</span>
    {# ... existing completeness bar ... #}
  </div>
</div>
```

### Example: Print CSS (D-10)

```css
@media print {
  #uw-decision-framework {
    page-break-before: always;
  }
  #uw-decision-framework .domain-group {
    page-break-inside: avoid;
  }
  /* Verdict dots print as filled circles */
  #uw-decision-framework [style*="border-radius:7px"] {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  /* Completeness bars */
  #uw-decision-framework [style*="background:#059669"],
  #uw-decision-framework [style*="background:#D97706"],
  #uw-decision-framework [style*="background:#DC2626"] {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2+ |
| Config file | `pyproject.toml` (testpaths = ["tests"]) |
| Quick run command | `uv run pytest tests/render/test_uw_questions.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QFW-01 | YAML files load all 8 domains, 55 questions | unit | `uv run pytest tests/brain/test_questions.py -x` | Wave 0 |
| QFW-02 | Each question has required schema fields | unit | `uv run pytest tests/brain/test_questions.py::test_question_schema -x` | Wave 0 |
| QFW-03 | All 55 questions have dedicated answerers | unit | `uv run pytest tests/render/test_uw_questions.py::test_all_questions_have_answerers -x` | Wave 0 |
| QFW-03 | Answerers produce answers with numbers (not vague) | integration | `uv run pytest tests/render/test_uw_questions.py::test_answer_quality -x` | Wave 0 |
| QFW-04 | SCA questions generated and slotted into domains | unit | `uv run pytest tests/render/test_sca_questions.py -x` | Wave 0 |
| QFW-05 | Domain and section verdict badges computed | unit | `uv run pytest tests/render/test_uw_questions.py::test_verdict_rollups -x` | Wave 0 |
| QFW-06 | Needs Review shows filing references | unit | `uv run pytest tests/render/test_uw_questions.py::test_filing_references -x` | Wave 0 |
| QFW-07 | Section positioned correctly in rendered HTML | integration | `uv run pytest tests/render/test_uw_questions.py::test_section_position -x` | Wave 0 |

### Wave 0 Gaps
- [ ] `tests/brain/test_questions.py` -- YAML schema validation, all domains load, question count
- [ ] `tests/render/test_uw_questions.py` -- answerer registry completeness, answer quality checks, verdict roll-ups, filing refs
- [ ] `tests/render/test_sca_questions.py` -- SCA question generation, domain slotting, badge display

## Open Questions

1. **Context ordering in uw_analysis.py**
   - What we know: `build_uw_questions_context` is called at line 213, before `peril`, `settlement`, `exec_risk`, `temporal` are built (lines 216-222)
   - What's unclear: Whether moving it after line 228 causes any circular dependency
   - Recommendation: Move it after line 228 -- no circular dependency likely since uw_questions reads ctx but doesn't write back into it for other builders

2. **Screening_answers.py coexistence**
   - What we know: `screening_answers.py` has 11 answerers used for risk card screening questions in the litigation section
   - What's unclear: Whether the new UW framework answerers should completely replace screening_answers or coexist
   - Recommendation: Coexist. Risk card screening questions are a separate feature in the litigation section. The UW framework has its own answerers. Shared helpers go in `answerers/_helpers.py`.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `uw_questions.py` (541 lines), `screening_answers.py` (737 lines), all 8 YAML files
- ORCL `state.json` -- verified data availability for all question data paths
- `uw_analysis.py` -- context builder integration, data flow, ordering

### Secondary (MEDIUM confidence)
- `_hydrate_risk_card()` in `litigation.py` -- Supabase risk card structure
- `assembly_registry.py` -- screening question auto-answer flow

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing patterns
- Architecture: HIGH -- answerers subpackage pattern is clear, data paths verified
- Pitfalls: HIGH -- context ordering issue verified by reading code, data availability verified against real state.json

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- internal project, no external dependency changes)
