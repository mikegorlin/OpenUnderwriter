# Phase 28: Presentation Layer & Context-Through-Comparison - Research

**Researched:** 2026-02-12
**Domain:** Document rendering presentation layer (Layer 5), context-through-comparison enrichment, issue-driven density, underwriter education
**Confidence:** HIGH (codebase investigation, no external library research needed -- this phase is about restructuring existing rendering code, not adding new dependencies)

## Summary

Phase 28 implements Layer 5 of the five-layer analysis architecture defined in the Phase 24 unified framework. The key insight from the user's MEMORY.md is that this phase should be **empirical, not framework-driven** -- "run tickers, fix what's wrong" rather than a big redesign. The original roadmap describes 6 success criteria focused on context-through-comparison, issue-driven density, four-tier display, underwriter education, meeting prep from analysis, and structured peer comparison.

The current rendering pipeline is substantial: 14,638 lines across 41 Python files in `stages/render/`, producing Word (primary), Markdown, and PDF output. All 8 sections render, meeting prep generates signal-driven questions, and Phase 27 added peril mapping, bear cases, coverage gaps, and mispricing alerts. The architecture is modular: `word_renderer.py` orchestrates, each section has its own renderer, `design_system.py` holds visual constants, `docx_helpers.py` provides table/styling primitives, and `formatters.py` handles number formatting.

**Primary recommendation:** Implement the six success criteria as incremental improvements to the existing rendering pipeline. Each criterion is a well-scoped enhancement that can be validated by running tickers and examining output. Avoid architectural rewrites -- the current section-renderer pattern works well.

## User Intent (from MEMORY.md)

### Critical Context
The user explicitly stated: "Phase 28 as originally written (framework-driven presentation redesign) should be replaced with empirical 'run tickers, fix what's wrong' approach." This means:

1. **No big redesign** -- improve what exists, don't rebuild
2. **Empirical validation** -- run AAPL, TSLA, XOM, SMCI, JPM and inspect output
3. **Fix visible problems** -- if a metric lacks peer context, add it; if clean sections are too verbose, trim them
4. **Phase 24 concepts as guide, not spec** -- the unified framework defines WHAT to achieve (context-through-comparison, issue-driven density, etc.) but not HOW to implement every detail
5. **Phase 28+ becomes user-driven** -- this phase should produce the best possible output, then the user takes over iteration

## Current Rendering Architecture

### File Structure (41 files, 14,638 lines)
```
src/do_uw/stages/render/
  __init__.py              # RenderStage orchestrator (Word + MD + PDF)
  word_renderer.py         # Word doc assembly (section loop, styles, TOC)
  design_system.py         # DesignSystem dataclass (colors, fonts, sizes)
  docx_helpers.py          # Table, shading, borders, risk indicators
  formatters.py            # Currency, percentage, date, citation formatting
  chart_helpers.py         # Chart embedding utilities
  md_narrative.py          # Narrative text generators (financial, market)
  md_narrative_helpers.py  # Sub-narrative generators
  md_narrative_sections.py # Company, governance, litigation, scoring narratives
  md_renderer.py           # Markdown output (Jinja2 templates)
  md_renderer_helpers.py   # Markdown extraction helpers
  md_renderer_helpers_ext.py  # Extended helpers
  md_renderer_helpers_scoring.py  # Scoring helpers
  pdf_renderer.py          # PDF output (WeasyPrint)
  charts/
    stock_charts.py        # 1-year and 5-year stock price charts
    timeline_chart.py      # Litigation timeline
    ownership_chart.py     # Ownership breakdown pie chart
    radar_chart.py         # 10-factor risk radar chart
  sections/
    sect1_executive.py     # Executive summary (538 lines -- OVER LIMIT)
    sect1_findings.py      # Key findings narrative builders
    sect1_helpers.py       # Thesis, risk, claim narrative helpers
    sect2_company.py       # Company profile orchestrator
    sect2_company_details.py  # Company detail tables (525 lines -- OVER LIMIT)
    sect3_financial.py     # Financial health (463 lines)
    sect3_tables.py        # Financial statement tables (461 lines)
    sect3_audit.py         # Audit risk assessment (485 lines)
    sect4_market.py        # Market & trading (434 lines)
    sect4_market_events.py # Stock drops, adverse events (498 lines)
    sect5_governance.py    # Governance & leadership (668 lines -- OVER LIMIT)
    sect5_governance_comp.py  # Compensation detail tables
    sect6_litigation.py    # Litigation & regulatory (475 lines)
    sect6_defense.py       # Defense assessment
    sect6_timeline.py      # Litigation timeline
    sect7_scoring.py       # Scoring synthesis orchestrator (460 lines)
    sect7_scoring_detail.py  # Factor detail, patterns, allegations
    sect7_peril_map.py     # Peril heat map, bear cases, settlement (460 lines)
    sect7_coverage_gaps.py # DATA_UNAVAILABLE disclosure (152 lines)
    sect8_ai_risk.py       # AI transformation risk (465 lines)
    meeting_prep.py        # Meeting prep appendix orchestrator
    meeting_questions.py   # Clarification + forward indicator generators
    meeting_questions_gap.py  # Gap filler + credibility test generators
```

### Files Exceeding 500-Line Limit (MUST FIX)
| File | Lines | Action Needed |
|------|-------|---------------|
| `sect1_executive.py` | 538 | Split formatting helpers into separate file |
| `sect2_company_details.py` | 525 | Extract sub-tables into helper module |
| `sect5_governance.py` | 668 | Split into governance + board forensics modules |

### Current Section Renderers
All 8 sections + meeting prep appendix render. Each follows the pattern:
```python
def render_section_N(doc: Any, state: AnalysisState, ds: DesignSystem) -> None:
```

### Existing Peer Comparison Infrastructure
The BENCHMARK stage already computes peer rankings:
- `MetricBenchmark` model: company_value, percentile_rank, peer_count, baseline_value
- `BenchmarkResult`: peer_group_tickers, peer_rankings (7 metrics), peer_quality_scores
- `percentile_engine.py`: percentile_rank() and ratio_to_baseline() functions
- 7 benchmarked metrics: market_cap, revenue, volatility_90d, short_interest_pct, leverage_debt_ebitda, quality_score, governance_score
- Peer group data: PeerCompany list with ticker, name, market_cap, revenue, peer_score

**Gap:** The benchmark data EXISTS in state but is NOT surfaced in most section renderers. Section 3 shows a basic peer group table. Section 1 shows market cap decile. But individual metrics (leverage, short interest, volatility, governance score) are NOT shown with their peer percentile or "compared to what?" context.

### Current Meeting Prep System
Questions are generated from actual analysis data (not templates):
- 4 categories: CLARIFICATION, FORWARD_INDICATOR, GAP_FILLER, CREDIBILITY_TEST
- Scans AnalysisState for LOW confidence data, distress trends, open SOL windows, elevated scores
- Each question has: source finding reference, D&O context, good/bad answers, follow-up
- **Gap:** Questions are partially signal-driven but not fully connected to bear cases or peril map findings

### Narrative Engine
The `md_narrative*.py` files generate analyst-quality interpretive text:
- Financial narrative: cites specific dollar amounts, margins, distress scores
- Market narrative: stock performance, insider trading, short interest
- Governance narrative: board composition, compensation, ownership
- Litigation narrative: case history, regulatory pipeline
- Scoring narrative: tier classification, factor breakdown
- **Gap:** Narratives do not include "compared to what?" context (peer percentiles, industry comparisons)

## Success Criteria Analysis

### SC1: Context-Through-Comparison
**What it means:** Every metric in the worksheet includes peer comparison, percentile ranking, and "compared to what?" framing.

**Current state:** Market cap decile exists in Section 1. Peer group table in Section 3. BenchmarkResult has percentile data for 7 metrics. But individual metrics (leverage ratio, short interest, volatility, board independence, CEO comp) are presented as raw numbers without peer context.

**What needs to change:**
- Surface BenchmarkResult percentile data in each section renderer
- Format pattern: "Debt/EBITDA: 4.2x (92nd percentile vs. peers; median 2.8x)"
- Add a `format_with_peer_context()` helper to formatters.py
- For each metric that has a BenchmarkResult entry, append the percentile and peer comparison
- Named peers: include the actual ticker names in comparison context where available
- Where peer data is unavailable: use sector baseline with "vs. sector baseline" label

**Implementation approach:** Create a `peer_context.py` utility module that takes metric_name + BenchmarkResult and returns a formatted context string. Each section renderer calls this for relevant metrics. No architectural change needed -- just enriching what's already rendered.

### SC2: Issue-Driven Density
**What it means:** Clean companies get concise worksheets; problematic companies get detailed forensic breakdowns. Silence means clean.

**Current state:** Some sections already implement this pattern:
- Bear cases: gated on MODERATE/HIGH exposure only (Phase 27)
- Coverage gaps: only renders non-empty lists
- Red flag gates: triggered vs. not-triggered display
- **But:** Several sections render full detail regardless of findings:
  - Financial distress always shows all 4 models even when all are in SAFE zone
  - Governance always renders full board/compensation tables even when clean
  - Litigation always renders empty sections ("No securities class actions identified")

**What needs to change:**
- Add conditional rendering logic: if section is "clean," render 1-2 sentence summary
- Pattern: "Financial Integrity: No concerns identified. All distress models in safe zone. Earnings quality metrics within normal ranges."
- Keep full detail available for problematic companies
- Key sections to make issue-driven: distress indicators, earnings quality, insider trading, short interest, governance quality, litigation, regulatory pipeline

**Implementation approach:** Each section renderer gets a `_is_section_clean()` helper that checks whether any signals are elevated. If clean, render a compact summary. If not clean, render the full detail. This is a per-section change, not architectural.

### SC3: Four-Tier Display
**What it means:** Every piece of information tagged and displayed in its proper tier: Customary (always present baseline), Objective Risk (scored signals), Relative Risk (peer-benchmarked), Subjective Modifier (underwriter questions).

**Current state:** Information is organized by worksheet section (1-8), not by tier. The four-tier concept from Phase 24 is a conceptual overlay, not a structural reorganization. Most sections already mix these tiers -- Section 3 shows customary financials alongside objective distress signals alongside relative peer comparison.

**What needs to change:**
- Within each section, visually distinguish tiers using existing design system:
  - Customary: standard body text with DOBody style
  - Objective Risk: highlighted rows/callouts with risk indicators
  - Relative Risk: peer comparison context (from SC1)
  - Subjective: question prompts linking to meeting prep
- Add visual tier labels or callouts, not restructure sections
- This is a presentation enhancement, not a data reorganization

**Implementation approach:** Add tier-aware rendering helpers:
- `render_customary_block()`: standard display with context
- `render_objective_signal()`: highlighted callout with risk level + evidence
- `render_relative_comparison()`: metric + percentile + named peers
- `render_subjective_prompt()`: question with link to meeting prep appendix
Each section renderer uses appropriate helpers based on content type.

### SC4: Underwriter Education (What IS / What COULD BE / What to ASK)
**What it means:** Level 1 (facts), Level 2 (scenarios with peer examples), Level 3 (targeted meeting prep).

**Current state:**
- Level 1 (What IS): Well-implemented. Sections 2-6 present factual data with source citations.
- Level 2 (What COULD BE): Partially implemented. Bear cases (Phase 27) provide scenario analysis. Claim probability with industry base rate provides probabilistic context. But individual sections don't include "companies like this get sued at X% rate" context.
- Level 3 (What to ASK): Implemented in meeting prep appendix. Questions reference actual findings. But questions are disconnected from the section where the finding appears.

**What needs to change:**
- Level 2: Add scenario context to individual sections. For elevated signals, include industry claims context: "Companies with DSO increasing 3+ quarters experience SCA filings at 2.3x the base rate."
- Level 3: In each section, when a signal is elevated, add a cross-reference to the relevant meeting prep question: "See Meeting Prep Q3: DSO trend clarification"
- Connect bear cases to the sections that generated their evidence

**Implementation approach:** Enrich section narratives with Level 2 context (scenario/probability text when signals are elevated). Add meeting prep cross-references as footnotes or callout boxes within sections.

### SC5: Meeting Prep from Analysis
**What it means:** Questions generated from actual elevated signals, not generic templates. Every question traces to a specific finding.

**Current state:** Mostly implemented. The 4 question generators walk AnalysisState and reference specific data points. Source findings are tracked. **Gap:** Questions from credibility tests and gap fillers are somewhat generic. Bear case scenarios (Phase 27) don't generate corresponding meeting prep questions. Peril map probability bands don't generate questions.

**What needs to change:**
- Add question generators for: bear case scenarios (ask about the scenario), elevated peril map lenses (ask about plaintiff-specific exposure), mispricing alerts (ask about pricing rationale)
- Improve credibility test specificity: reference actual forensic model results, not generic patterns
- Ensure every ELEVATED or higher peril lens generates at least one meeting prep question

**Implementation approach:** Add new generator functions in meeting_questions.py or meeting_questions_gap.py. Wire bear case data and peril map assessments into question generation.

### SC6: Structured Peer Comparison
**What it means:** Named peers with specific shared/differing characteristics, not just percentile ranks.

**Current state:** Peer group data exists in PeerCompany model (ticker, name, market_cap, revenue, peer_score). Section 3 renders a basic peer table. BenchmarkResult has peer_group_tickers. **Gap:** No section shows "shared characteristics" or "differing characteristics" between the subject company and its peers. Peers are listed as a table, not analyzed comparatively.

**What needs to change:**
- Add a structured peer comparison section (could be in Section 2 or Section 7)
- For each named peer, show: what they share (sector, market cap tier, business model) and how they differ (litigation history, governance quality, financial health)
- Include peer SCA history: "4 of 6 peers have faced SCA in the past 5 years"
- Show peer quality scores alongside the subject company's score

**Implementation approach:** Create a `peer_comparison.py` section renderer that takes PeerCompany + BenchmarkResult data and renders a comparative analysis. Include a narrative: "Among [company]'s closest peers, [PEER1] and [PEER2] share [characteristics]. [PEER3] differs in [ways]. Peer SCA history: [X of Y] filed in past 5 years."

## Architecture Patterns

### Pattern 1: Conditional Density Rendering
**What:** Each section checks signal elevation before deciding render depth.
**When to use:** Every section renderer.
**Example:**
```python
def _render_distress_panel(doc, financials, ds, benchmark_result):
    if _all_distress_safe(financials):
        # Issue-driven: clean companies get one-liner
        body = doc.add_paragraph(style="DOBody")
        body.add_run(
            "Financial Integrity: No concerns identified. "
            "All distress models in safe zone."
        )
        return
    # Problematic: render full detail panel
    _render_full_distress_panel(doc, financials, ds, benchmark_result)
```

### Pattern 2: Context-Through-Comparison Enrichment
**What:** Appending peer context to existing metric renders.
**When to use:** Any metric that has a corresponding MetricBenchmark entry.
**Example:**
```python
def format_metric_with_context(
    label: str,
    value: str,
    benchmark: MetricBenchmark | None,
    named_peers: list[str] | None = None,
) -> str:
    """Format a metric value with peer context."""
    if benchmark is None or benchmark.percentile_rank is None:
        return f"{label}: {value}"
    pctile = benchmark.percentile_rank
    ordinal = f"{pctile:.0f}th percentile"
    base = f"{label}: {value} ({ordinal} vs. peers"
    if benchmark.baseline_value is not None:
        base += f"; baseline {benchmark.baseline_value:.1f}"
    if named_peers:
        base += f" [{', '.join(named_peers[:3])}]"
    base += ")"
    return base
```

### Pattern 3: Meeting Prep Cross-Reference
**What:** Linking elevated signals in sections to meeting prep questions.
**When to use:** When rendering an elevated signal that has a corresponding question.
**Example:**
```python
def _add_meeting_prep_ref(doc, ds, question_number: int):
    """Add a cross-reference to a meeting prep question."""
    ref = doc.add_paragraph(style="DOCaption")
    run = ref.add_run(f"See Meeting Prep Q{question_number}")
    run.font.color.rgb = ds.color_accent
    run.italic = True
```

### Anti-Patterns to Avoid
- **Full section rewrite:** The existing renderers work. Enhance them, don't rewrite.
- **New state model fields for presentation:** All data needed already exists in AnalysisState. Presentation changes should not modify the data model.
- **Tier restructuring at the section level:** Keep the 8-section structure. The four-tier display is a visual overlay within sections, not a section reorganization.
- **Markdown/PDF parity changes in this phase:** Focus on Word (primary output). Markdown and PDF will inherit improvements through shared narrative generators but don't need parallel presentation changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Percentile computation | Custom stat functions | Existing `percentile_engine.py` | Already tested, handles ties and higher/lower-is-better |
| Risk color coding | Per-section color logic | Existing `design_system.py` and `get_risk_color()` | Centralized, consistent |
| Table styling | Custom XML manipulation per section | Existing `add_styled_table()` and `add_data_table()` | Navy headers, alternating rows, consistent fonts |
| Source citation | Ad-hoc string formatting | Existing `format_citation()` and `format_source_trail()` | Consistent citation format |
| Compact numbers | Per-section format logic | Existing `format_currency(compact=True)` and `format_compact()` | Handles B/M/K with sign |

## Common Pitfalls

### Pitfall 1: Scope Creep into Data Layer
**What goes wrong:** Presentation changes lead to adding new data acquisition, extraction, or scoring logic.
**Why it happens:** Finding gaps where "compared to what?" context requires data that doesn't exist.
**How to avoid:** If benchmark data for a metric doesn't exist, render without context and note the gap. Don't add new ACQUIRE/EXTRACT/SCORE logic in a presentation phase.
**Warning signs:** Modifying files in `stages/acquire/`, `stages/extract/`, `stages/score/`, or `stages/benchmark/` core logic.

### Pitfall 2: Over-Engineering Tier Classification
**What goes wrong:** Building a complex tier-tagging system that requires classifying every data point as Customary/Objective/Relative/Subjective.
**Why it happens:** Taking the Phase 24 four-tier concept too literally as a data model change.
**How to avoid:** The four tiers are a RENDERING concern. Use helper functions that render content appropriately based on its nature. No need for a `tier` field on every data model.
**Warning signs:** Adding `tier: Literal["customary", "objective", "relative", "subjective"]` fields to Pydantic models.

### Pitfall 3: Breaking Clean Company Output
**What goes wrong:** Issue-driven density logic breaks rendering for clean companies, producing empty or confusing sections.
**Why it happens:** Overly aggressive suppression of "clean" data. Underwriters still need to see the baseline.
**How to avoid:** "Clean" means CONCISE, not ABSENT. Every section still gets at least a summary paragraph. The Customary tier data always renders. Only Objective Risk detail is suppressed when clean.
**Warning signs:** Sections rendering as just a heading with no content.

### Pitfall 4: 500-Line Violations
**What goes wrong:** Adding context-through-comparison enrichment to already-large section renderers pushes them over the 500-line limit.
**Why it happens:** Each section needs both clean and detailed paths, plus peer context formatting.
**How to avoid:** Extract shared utilities (peer context formatting, issue-driven gating) into separate helper modules. Three files already exceed the limit and must be split FIRST.
**Warning signs:** Any render file approaching 450 lines.

### Pitfall 5: Losing Existing Test Coverage
**What goes wrong:** Modifying section renderers breaks existing render tests.
**Why it happens:** Tests assert specific text or table structure that changes with new context.
**How to avoid:** Run existing tests frequently. Update test assertions to accommodate new context strings. Add new tests for new behavior (context-through-comparison, issue-driven gating).
**Warning signs:** Test failures in `test_render_sections_*.py`.

## Code Examples

### Existing Pattern: Section Renderer
```python
# Source: src/do_uw/stages/render/sections/sect3_financial.py
def render_section_3(doc, state, ds):
    _render_heading(doc, ds)
    _render_narrative(doc, state, ds)
    render_financial_tables(doc, state, ds)
    financials = state.extracted.financials if state.extracted else None
    _render_distress_panel(doc, financials, ds)
    _render_earnings_quality(doc, financials, ds)
    _render_audit_delegation(doc, state, ds)
    _render_peer_group(doc, financials, ds)
```

### Existing Pattern: Peer Metric Extraction
```python
# Source: src/do_uw/stages/benchmark/peer_metrics.py
METRIC_REGISTRY = [
    MetricDef("market_cap", "peer_company", True, "SECT2"),
    MetricDef("revenue", "peer_company", True, "SECT2"),
    MetricDef("volatility_90d", "sector_baseline", False, "SECT4", "volatility_90d"),
    MetricDef("short_interest_pct", "sector_baseline", False, "SECT4", "short_interest"),
    MetricDef("leverage_debt_ebitda", "sector_baseline", False, "SECT3", "leverage_debt_ebitda"),
    MetricDef("quality_score", "risk_score", True, "SECT7"),
    MetricDef("governance_score", "risk_score", True, "SECT5"),
]
```

### Existing Pattern: Risk Indicator
```python
# Source: src/do_uw/stages/render/docx_helpers.py
def add_risk_indicator(paragraph, level, ds):
    color_hex = get_risk_color(level)
    run = paragraph.add_run(f" [{level.upper()}]")
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(...)
```

### Phase 24 Four-Tier Display Spec
```
Customary:      Always displayed. Context not score. "$80B market cap, #72 US, #8 in sector"
Objective Risk: Issue-driven. "Beneish M-Score = -1.42 (LIKELY MANIPULATOR)" OR "No concerns"
Relative Risk:  Peer-benchmarked. "Leverage 4.2x vs peer median 2.8x (92nd percentile)"
Subjective:     Questions. "Ask about the 15% DSO increase in Q3" -> Meeting Prep Q3
```

## Implementation Priority Order

Based on the user's empirical approach and what will produce the most visible improvement:

1. **Fix 500-line violations** (prerequisite): Split 3 over-limit files before any other changes
2. **Context-through-comparison** (SC1, SC6): Highest-impact visual improvement -- every metric gets peer context
3. **Issue-driven density** (SC2): Makes clean companies readable, problematic companies focused
4. **Meeting prep from analysis** (SC5): Wire bear cases + peril map to question generators
5. **Underwriter education** (SC4): Add Level 2 scenario context to elevated signals
6. **Four-tier display** (SC3): Visual tier labels/grouping within sections (lightest touch)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw metric display | Partial peer context (market cap decile only) | Phase 7 (Benchmark) | Metrics shown without "compared to what?" context |
| Fixed-length sections | Fixed-length sections | Phase 8 (initial render) | Clean and problematic companies get same detail level |
| Generic meeting questions | Signal-driven questions | Phase 8 (meeting prep) | Questions reference actual findings but not bear cases |
| No bear cases | Evidence-gated bear cases | Phase 27 | Clean companies get 0 bear cases, problematic get 5-6 |
| No coverage gaps | Three-state data status + gaps section | Phase 27 | Honest disclosure of unchecked items |

## Open Questions

1. **Markdown/PDF update scope**
   - What we know: Word is primary output. Markdown uses Jinja2 templates + shared narrative generators. PDF uses WeasyPrint.
   - What's unclear: Should Markdown/PDF get the same context-through-comparison enrichment? The shared narrative generators will propagate some changes, but table structure changes won't.
   - Recommendation: Focus on Word. Let Markdown inherit what it can through shared narratives. PDF can be updated in a future user-driven iteration.

2. **Peer data availability**
   - What we know: 7 metrics have percentile benchmarks. Peer companies have ticker/name/market_cap/revenue.
   - What's unclear: How much richer peer data is available for "shared/differing characteristics" analysis? Would need SCA history per peer, governance scores per peer, etc.
   - Recommendation: Use what's available. Peer quality scores exist in BenchmarkResult.peer_quality_scores. For SCA history, reference whether the peer is in Stanford SCAC (from litigation extraction). Don't add new acquisition for peer data.

3. **Empirical validation tickers**
   - What we know: User expects running actual tickers (AAPL, TSLA, XOM, SMCI, JPM mentioned in Phase 27 context).
   - What's unclear: Whether to include validation runs as explicit plan tasks or leave for user post-phase.
   - Recommendation: Include at least one "run tickers and validate output" task per plan to catch rendering issues empirically.

## Sources

### Primary (HIGH confidence)
- Codebase investigation: all 41 render stage files read and analyzed
- Phase 24 unified framework: `24-UNIFIED-FRAMEWORK.md` (user-approved, Layer 5 specification)
- Phase 27 verification: `27-VERIFICATION.md` (confirms peril map, bear cases, coverage gaps complete)
- User MEMORY.md: explicit "empirical, not framework-driven" directive

### Secondary (MEDIUM confidence)
- Phase 27 context: `27-CONTEXT.md` (decisions affecting rendering: bear case gating, coverage gaps last)
- BenchmarkResult model: `models/scoring.py` lines 291-311

## Metadata

**Confidence breakdown:**
- Current architecture understanding: HIGH -- all files read and analyzed
- Success criteria interpretation: HIGH -- roadmap + Phase 24 framework + user MEMORY.md provide clear guidance
- Implementation approach: HIGH -- incremental improvements to well-understood code
- Pitfall identification: HIGH -- based on actual codebase constraints (500-line limits, existing tests)

**Research date:** 2026-02-12
**Valid until:** Indefinite (codebase-specific research, not time-sensitive library versioning)
