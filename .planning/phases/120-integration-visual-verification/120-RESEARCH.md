# Phase 120: Integration + Visual Verification - Research

**Researched:** 2026-03-20
**Domain:** End-to-end integration testing, visual verification, CI gate design
**Confidence:** HIGH

## Summary

Phase 120 is a pure verification phase -- no new features. The goal is to validate the complete v8.0 Intelligence Dossier by running the pipeline on 3 tickers (HNGE, AAPL, ANGI), visually verifying output against the HNGE gold standard PDF, confirming all existing analytical capabilities are preserved, meeting performance budgets, and adding a CI gate for do_context coverage.

The project already has substantial test infrastructure: 7,627 tests, visual regression framework (Playwright screenshots), performance budget tests, cross-ticker QA comparison script, do_context CI gate for hardcoded commentary, and render path coverage tests. This phase extends that infrastructure with: (1) full pipeline runs on 3 tickers, (2) section-by-section content verification, (3) a new do_context coverage CI gate, and (4) updated visual regression baselines for new v8.0 sections.

**Primary recommendation:** Structure this as sequential waves -- pipeline runs first, then automated structural verification, then visual review, then CI gate. The pipeline runs are the long pole (~20-25 min each with --fresh); everything else builds on their output.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Test tickers:** HNGE (gold standard), AAPL (clean mega-cap), ANGI (complex WALK-tier)
- All 3 pipeline runs automated within phase execution using `underwrite TICKER --fresh`
- Verification bar is **content correctness and completeness**, not pixel-perfect visual matching
- **do_context coverage target: 100%** -- every evaluative column must trace to a brain signal do_context block
- CI gate is **two-layer**: pytest assertion for pass/fail + standalone script for detailed investigation
- **Both automated and visual** verification for existing analytics
- All existing sections equally important -- no prioritization
- Performance budget: HTML render <10s, full pipeline <25min
- New v8.0 sections (Intelligence Dossier, Forward-Looking Risk, Alt Data, Stock Catalysts) get full visual review
- ANGI should look markedly different from AAPL -- if similar, something is wrong
- Section density should vary naturally

### Claude's Discretion
- Order of pipeline runs (HNGE first recommended as baseline)
- Exact HTML structural assertions (selectors, elements)
- How to report visual review findings
- Standalone do_context coverage script implementation details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

This phase validates ALL v8.0 requirements. No individual requirement IDs are assigned because this is an integration verification phase. The phase's 5 success criteria map to the requirement categories:

| Success Criterion | Validates | Research Support |
|---|---|---|
| SC-1: Full pipeline runs on 3 tickers with all sections populated | ALL req categories (DOSSIER, STOCK, FORWARD, SCORE, TRIGGER, ALTDATA, COMMENT) | Pipeline run infrastructure, output directory structure, section inventory from manifest |
| SC-2: Section-by-section gold standard comparison | QUAL-01 through QUAL-07 (narrative quality cross-cutting) | HNGE gold standard PDF at `Feedme/HNGE - D&O Analysis - 2026-03-18.pdf`, 29 pages |
| SC-3: Existing capabilities preserved | Preservation of pre-v8.0 analytics (forensics, scoring, governance, litigation) | Visual regression framework, qa_compare.py, existing section IDs in HTML |
| SC-4: Performance budget met | Non-functional requirements | Performance budget test framework already exists |
| SC-5: CI gate for do_context coverage | INFRA-01 through INFRA-05, COMMENT-01 through COMMENT-06 | Signal consumer pattern, do_context engine, existing CI gate infrastructure |
</phase_requirements>

## Standard Stack

No new libraries needed. This phase uses existing project infrastructure exclusively.

### Core (Already in Project)
| Tool | Purpose | Location |
|------|---------|----------|
| pytest | Test framework for CI gates | `uv run pytest` |
| Playwright | Visual regression screenshots | `tests/test_visual_regression.py` |
| Pillow + numpy | Pixel diff comparison | `_compute_pixel_diff()` in visual regression |
| qa_compare.py | Cross-ticker feature parity | `scripts/qa_compare.py` |
| brain YAML loader | Signal do_context coverage scan | `do_uw.brain.brain_unified_loader.load_signals()` |

### CLI Commands
```bash
# Pipeline runs (--fresh forces full acquisition)
underwrite HNGE --fresh
underwrite AAPL --fresh
underwrite ANGI --fresh

# Performance budget tests
PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py -v

# Visual regression (generate new baselines)
VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py --update-golden -v

# Cross-ticker QA
uv run python scripts/qa_compare.py --reference HNGE

# Full test suite
uv run pytest
```

## Architecture Patterns

### Current HTML Section ID Inventory (from AAPL output)

These are the actual `<section>` IDs rendered in the HTML worksheet. The visual regression test only checks 13 of these -- needs updating for v8.0 sections.

```
Existing (pre-v8.0):
  scorecard, executive-brief, red-flags, company-profile,
  financial-health, market, governance, litigation, ai-risk,
  scoring, pattern-firing, meeting-prep, coverage,
  decision-record, signal-audit, data-audit

New v8.0 sections:
  section-intelligence-dossier    (Phase 118)
  section-alternative-data        (Phase 119)
  section-forward-looking         (Phase 117)
  adversarial-critique            (Phase 110)
```

### Output Manifest Section Inventory

The output manifest (`src/do_uw/brain/output_manifest.yaml`) defines 16 top-level sections with ~120 groups total. Key sections for verification:

| Manifest Section | HTML ID | Groups | v8.0 New? |
|---|---|---|---|
| identity | identity | 0 | No |
| executive_summary | executive-summary | 7 | No |
| red_flags | red-flags | 1 | No |
| business_profile | company-profile | 17 | No |
| intelligence_dossier | section-intelligence-dossier | 9 | YES |
| alternative_data | section-alternative-data | 4 | YES |
| financial_health | financial-health | 17 | No |
| market_activity | market | 13 | No (but STOCK-01..06 added groups) |
| governance | governance | 14 | No |
| litigation | litigation | 11 | No |
| ai_risk | ai-risk | 5 | No |
| scoring | scoring | 20 | No (but SCORE-01..05 added groups) |
| forward_looking | section-forward-looking | 11 | YES |
| adversarial_critique | adversarial-critique | 4 | Yes (Phase 110) |
| meeting_prep | meeting-prep | 0 | No |
| sources | sources | 0 | No |
| qa_audit | qa-audit | 0 | No |
| coverage | coverage | 0 | No |

### Gold Standard PDF Structure (HNGE, 29 pages)

From the HNGE gold standard PDF (pages 1-3 examined):
1. **Header/Snapshot** -- Company profile table (Market Cap, Revenue, Employees, Public Since, HQ, Sector, ETF), Risk Tier badge, Nuclear Triggers status
2. **Executive Summary** -- Key Positives (5 items with bold leads, dollar amounts, source citations), Key Negatives (5 items with yellow dot indicators, factor references like "F4-003 = 8/10"), Recommendation Summary paragraph
3. **Quantitative Risk Assessment** -- Score narrative, 10-factor scoring table (Factor/Score/Max/Key Driver), Nuclear Triggers, Modifiers, 18-Month Litigation Probability, Expected Severity
4. **Deal Context** -- Transaction Context, Management Meeting notes

Key quality markers from gold standard:
- Every key positive/negative has bold lead, specific numbers, source citation
- Factor references embedded in findings (e.g., "F.1 = 0/20", "F4-003 = 8/10")
- Recommendation paragraph is company-specific with factor references
- Scoring table has "Key Driver" column with concise evidence

### do_context Coverage Architecture

The do_context system has three layers:

1. **Brain YAML signals** -- 562+ signals in `brain/signals/*.yaml`, each with optional `presentation.do_context` block containing template variants (TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR)
2. **do_context engine** (`stages/analyze/do_context_engine.py`) -- Evaluates templates against signal results at ANALYZE time, stores rendered string on `signal_result.do_context`
3. **Context builders** -- Consume `do_context` via `get_signal_do_context(signal_results, SIGNAL_ID)` or `safe_get_result(signal_results, SIGNAL_ID).do_context` pattern

For the CI gate, "evaluative columns" means any table column labeled "D&O Risk", "D&O Implication", "Assessment", "D&O Relevance", or "Underwriting Commentary" in the rendered HTML. Each such column must be populated by a brain signal's do_context, not hardcoded Python/Jinja2.

**Current do_context coverage stats** (from brain health CLI):
- The `cli_brain_health.py` already counts signals with `presentation.do_context` -- all 563 signals were populated with do_context templates in Phase 116-01.
- The gap is: not all evaluative columns in templates necessarily consume a signal's do_context. Some may still use hardcoded text or be empty.

### Pattern: Two-Layer CI Gate

The CONTEXT.md specifies a two-layer approach:

**Layer 1: pytest assertion** (fast, CI-friendly)
```python
def test_do_context_evaluative_coverage():
    """Every evaluative column in templates traces to a do_context signal."""
    # Scan Jinja2 templates for evaluative column headers
    # For each, verify it references a do_context variable
    # Assert coverage_pct >= 100
```

**Layer 2: standalone script** (detailed investigation)
```python
# scripts/do_context_coverage.py
# Produces detailed report:
# - Which templates have evaluative columns
# - Which columns are covered (trace to signal ID)
# - Which columns are missing coverage
# - Coverage percentage
```

### Pipeline Run Timing Considerations

Each `underwrite TICKER --fresh` run takes 15-25 minutes. Three runs = 45-75 minutes total. These CANNOT be parallelized (concurrent pipeline runs cause SQLite cache contention -- see MEMORY.md "Concurrent pipeline runs forbidden").

Recommended order:
1. HNGE first (gold standard baseline)
2. AAPL second (clean ticker, validates normal path)
3. ANGI third (complex ticker, validates edge cases)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Section presence detection | Custom HTML parser | regex on section IDs (existing qa_compare.py pattern) | Simple, proven, already in codebase |
| Visual screenshot comparison | Custom diff tool | Existing Playwright + Pillow framework | Already handles screenshots, diff thresholds |
| Performance measurement | Custom timing | Existing test_performance_budget.py framework | Already has budgets, load from state.json |
| Cross-ticker comparison | Custom comparison | Existing qa_compare.py + extensions | Already profiles outputs, just needs v8.0 sections |
| do_context YAML scanning | Custom YAML parser | `brain_unified_loader.load_signals()` | Already loads and caches all signals |

## Common Pitfalls

### Pitfall 1: Stale Output Directories
**What goes wrong:** Running `underwrite HNGE --fresh` creates a new output directory (e.g., `output/HNGE-2026-03-20/`) but the visual regression framework and qa_compare.py look for the most recent output. If old outputs exist, tests may pick up stale data.
**How to avoid:** Always verify the output directory timestamp after each pipeline run. Consider clearing old outputs for the 3 test tickers before running.

### Pitfall 2: Visual Regression Section IDs Out of Date
**What goes wrong:** The `SECTION_IDS` list in `test_visual_regression.py` only has 13 entries (identity, executive-summary, red-flags, financial-health, market, governance, litigation, ai-risk, scoring, meeting-prep, sources, qa-audit, coverage). It's missing: scorecard, executive-brief, company-profile, section-intelligence-dossier, section-alternative-data, section-forward-looking, adversarial-critique, decision-record, signal-audit, data-audit, pattern-firing.
**How to avoid:** Update SECTION_IDS to match actual rendered section IDs from the HTML output.

### Pitfall 3: Concurrent Pipeline Runs
**What goes wrong:** SQLite cache contention causes disk I/O errors when multiple pipeline runs execute simultaneously.
**How to avoid:** Run pipeline sequentially. Never parallelize `underwrite` commands.

### Pitfall 4: do_context Coverage False Positives
**What goes wrong:** Some evaluative columns use column headers like "D&O Risk" but are display_only groups where the content is a do_context variable reference. Others might use hardcoded labels that look like evaluative content but are actually just column headers.
**How to avoid:** The CI gate should trace from evaluative column headers in templates to the Jinja2 variable that populates the cell, then verify that variable originates from a `do_context` signal result. Distinguish between "column header text" (allowed) and "cell content text" (must come from do_context).

### Pitfall 5: HNGE Pipeline May Differ from Gold Standard
**What goes wrong:** The gold standard PDF was generated on 2026-03-18. Running `underwrite HNGE --fresh` on 2026-03-20 may acquire different data (stock prices moved, new filings, etc.). The comparison should focus on structural completeness and quality, not exact data matching.
**How to avoid:** Compare SECTIONS and QUALITY patterns, not exact values. Verify the same sections exist, scoring factors are present, narratives reference company-specific data with the right pattern (bold leads, factor refs, source citations).

### Pitfall 6: Missing `key-stats` and `executive-brief` Sections
**What goes wrong:** The HTML output has both `key-stats` and `executive-brief` sections (rendered via `sections/key_stats.html.j2` and `sections/executive_brief.html.j2`) but these are NOT in the output manifest -- they're injected separately. Don't expect manifest-driven discovery to find all sections.
**How to avoid:** Use both manifest scanning AND actual HTML output scanning to build complete section inventory.

## Code Examples

### Pattern: Structural HTML Verification (from qa_compare.py)
```python
# Source: scripts/qa_compare.py
section_ids = re.findall(r'<section[^>]*id="([^"]+)"', content)
svg_count = len(re.findall(r"<svg", content))
score_badges = len(re.findall(r"score-badge|verdict-badge|badge-tier", content))
collapsibles = len(re.findall(r"<details|collapsible", content))
na_ratio = na_cells / max(total_td, 1)
```

### Pattern: Signal do_context Access (from _signal_consumer.py)
```python
# Source: src/do_uw/stages/render/context_builders/_signal_consumer.py
def get_signal_do_context(signal_results: dict[str, Any], signal_id: str) -> str:
    raw = signal_results.get(signal_id)
    if raw is None or not isinstance(raw, dict):
        return ""
    return raw.get("do_context", "")
```

### Pattern: do_context YAML Coverage Check (from cli_brain_health.py)
```python
# Source: src/do_uw/cli_brain_health.py (lines 223-243)
all_signals_data = load_signals()
all_signals_list = all_signals_data.get("signals", [])
total_signals = len(all_signals_list)
with_do_context = sum(
    1 for s in all_signals_list
    if isinstance(s.get("presentation"), dict)
    and s["presentation"].get("do_context")
)
pct = (100 * with_do_context / total_signals) if total_signals > 0 else 0
```

### Pattern: Evaluative Column Detection in Templates
```python
# Scan Jinja2 templates for evaluative column headers
EVALUATIVE_HEADERS = [
    "D&O Risk", "D&O Implication", "D&O Relevance",
    "Assessment", "Underwriting Commentary",
    "D&O Litigation Exposure", "D&O Factor",
]
# For each template with these headers, verify the cell content
# references a do_context variable (e.g., {{ row.do_risk }})
```

### Pattern: Performance Budget Test (from test_performance_budget.py)
```python
# Source: tests/test_performance_budget.py
HTML_RENDER_BUDGET = 10.0  # seconds
PDF_RENDER_BUDGET = 30.0
PIPELINE_TOTAL_BUDGET = 1500.0  # 25 minutes

start = time.perf_counter()
render_html_pdf(state, output_path)
duration = time.perf_counter() - start
assert duration < HTML_RENDER_BUDGET
```

## State of the Art

| Aspect | Current State | Phase 120 Target |
|--------|--------------|-----------------|
| Visual regression section IDs | 13 sections | All rendered sections (~20) |
| do_context CI gate | Checks hardcoded commentary prevention | NEW: evaluative column traceability |
| Cross-ticker QA | Profile-based comparison (qa_compare.py) | Extended with v8.0 section checks |
| Pipeline runs | Manual, ad-hoc | 3 automated runs with structured verification |
| Gold standard comparison | No formal process | Section-by-section content review against PDF |

## Open Questions

1. **How to verify QUAL-01 through QUAL-07 programmatically?**
   - What we know: QUAL requirements demand company-specific narratives with dollar amounts, factor references, source citations. The gold standard PDF shows the pattern.
   - What's unclear: How much can be automated vs requires human visual review? Regex can check for factor ref patterns (e.g., `F\.\d+ = \d+/\d+`) and dollar amounts (`\$[\d,.]+[BMK]?`) but quality assessment may need visual review.
   - Recommendation: Automated checks for structural patterns (factor refs present, dollar amounts present, source citations present) + visual review for narrative quality.

2. **Exact scope of "evaluative columns" for do_context CI gate**
   - What we know: Tables with "D&O Risk", "Assessment", etc. columns should be populated by do_context. Phase 116-01 populated all 563 signals with do_context templates.
   - What's unclear: Is the CI gate checking that every template RENDERS a do_context value, or that every signal HAS a do_context template? The CONTEXT.md says "every evaluative column traceable to a brain signal do_context block."
   - Recommendation: Scan templates for evaluative column headers, verify each column's cell content references a `do_context` or `do_risk` variable, trace those variables back through context builders to signal IDs.

3. **HNGE output may not exist yet**
   - What we know: No HNGE output directory found in `output/`. AAPL output exists from a prior run.
   - What's unclear: Whether Phase 120 should generate HNGE output for the first time or if a pre-existing run exists elsewhere.
   - Recommendation: Phase 120 generates fresh output for all 3 tickers. HNGE output creation is part of the phase, not a prerequisite.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/brain/test_do_context_ci_gate.py tests/test_ci_render_paths.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Criterion | Behavior | Test Type | Automated Command | File Exists? |
|-----------|----------|-----------|-------------------|-------------|
| SC-1 | Pipeline runs produce complete output | integration (pipeline) | `underwrite HNGE --fresh` (manual trigger) | N/A - pipeline command |
| SC-2 | Gold standard section comparison | visual + automated | `uv run pytest tests/test_integration_120.py -x` | Wave 0 |
| SC-3 | Existing capabilities preserved | structural + visual | `uv run python scripts/qa_compare.py --reference HNGE` | Exists (needs v8.0 extension) |
| SC-4 | Performance budget | timing | `PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py -x` | Exists |
| SC-5 | do_context coverage CI gate | static analysis | `uv run pytest tests/test_do_context_evaluative_coverage.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/test_do_context_ci_gate.py tests/test_ci_render_paths.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green + all 3 pipeline outputs verified

### Wave 0 Gaps
- [ ] `tests/test_do_context_evaluative_coverage.py` -- NEW: CI gate for evaluative column traceability
- [ ] `scripts/do_context_coverage.py` -- NEW: standalone detailed coverage report script
- [ ] `tests/test_visual_regression.py` -- UPDATE: SECTION_IDS needs v8.0 sections added
- [ ] `scripts/qa_compare.py` -- UPDATE: needs v8.0 section checks (intelligence_dossier, alt_data, forward_looking)

## Sources

### Primary (HIGH confidence)
- `output/AAPL/AAPL_worksheet.html` -- actual rendered section IDs extracted
- `src/do_uw/brain/output_manifest.yaml` -- complete section/group inventory (770 lines)
- `tests/test_visual_regression.py` -- existing framework code
- `tests/test_performance_budget.py` -- existing performance test code
- `tests/brain/test_do_context_ci_gate.py` -- existing CI gate patterns
- `tests/test_ci_render_paths.py` -- existing render path coverage
- `scripts/qa_compare.py` -- existing QA comparison tool
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` -- signal consumer API
- `Feedme/HNGE - D&O Analysis - 2026-03-18.pdf` -- gold standard reference (29 pages)

### Secondary (MEDIUM confidence)
- `src/do_uw/cli_brain_health.py` -- do_context coverage counting pattern (lines 223-243)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools already exist in project, no new dependencies
- Architecture: HIGH -- section IDs verified from actual HTML output, manifest structure documented
- Pitfalls: HIGH -- based on direct codebase analysis (stale SECTION_IDS list, concurrent run prohibition)
- CI gate design: MEDIUM -- evaluative column traceability concept clear but exact scope of "evaluative column" needs definition during implementation

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable -- verification phase, no external dependencies)
