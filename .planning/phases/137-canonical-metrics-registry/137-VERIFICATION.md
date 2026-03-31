---
phase: 137-canonical-metrics-registry
verified: 2026-03-27T21:30:00Z
status: gaps_found
score: 7/8 must-haves verified
gaps:
  - truth: "company_profile reads exchange, employees from canonical (in HTML render path)"
    status: partial
    reason: "extract_company() is called from build_template_context() (md_renderer) WITHOUT canonical. context['company'] in the HTML render path is populated via legacy extraction. The canonical=None kwarg exists on extract_company() and works when called directly, but the assembly pipeline never passes _canonical_obj to it."
    artifacts:
      - path: "src/do_uw/stages/render/context_builders/company_profile.py"
        issue: "canonical kwarg present but never invoked with canonical in HTML assembly path"
      - path: "src/do_uw/stages/render/context_builders/assembly_dossier.py"
        issue: "Does not call extract_company with canonical=context.get('_canonical_obj')"
    missing:
      - "assembly_dossier.py (or assembly_html_extras.py) must re-call extract_company with canonical and overwrite context['company'], OR md_renderer.build_template_context must be refactored to accept canonical"
  - truth: "company_exec_summary reads exchange, market_cap, revenue from canonical (in HTML render path)"
    status: partial
    reason: "Same root cause as company_profile. extract_exec_summary() is called from build_template_context() (md_renderer) without canonical. context['executive_summary'] in HTML is set before canonical is computed."
    artifacts:
      - path: "src/do_uw/stages/render/context_builders/company_exec_summary.py"
        issue: "canonical kwarg present but never invoked with canonical in HTML assembly path"
    missing:
      - "assembly_dossier.py must re-call build_company_exec_summary with canonical=context.get('_canonical_obj') and overwrite context['executive_summary'], similar to how key_stats and scorecard are handled"
---

# Phase 137: Canonical Metrics Registry Verification Report

**Phase Goal:** Every metric that appears in more than one section (revenue, market cap, CEO, exchange, growth rates) is computed exactly once from the highest-confidence source and consumed everywhere
**Verified:** 2026-03-27T21:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | build_canonical_metrics(state) returns CanonicalMetrics with all 8 core metric types populated for valid state | ✓ VERIFIED | 24/24 tests pass; AAPL state produces revenue.raw > 0, source="xbrl:10-K:FY2024" |
| 2 | Every MetricValue carries non-empty source, confidence, and as_of when populated | ✓ VERIFIED | test_every_populated_metric_has_source passes; resolver pattern enforced in all 22 resolvers |
| 3 | XBRL data is preferred over yfinance when both present | ✓ VERIFIED | resolve_revenue returns source="xbrl:10-K:FY2024", confidence="HIGH"; yfinance is explicit else-branch |
| 4 | Missing data produces MetricValue(raw=None, formatted='N/A', source='none', confidence='LOW') | ✓ VERIFIED | test_empty_state_no_crash passes; empty AnalysisState(ticker='TEST') returns all N/A defaults |
| 5 | build_html_context() computes canonical once at top and stores in context['_canonical'] | ✓ VERIFIED | assembly_registry.py lines 91-104; spot-check confirms _canonical and _canonical_obj in ctx |
| 6 | key_stats_context reads revenue, market_cap, employees, exchange from canonical | ✓ VERIFIED | Lines 80-186 of key_stats_context.py; test_key_stats_uses_canonical_revenue passes |
| 7 | beta_report reads revenue, market_cap, stock_price, employees from canonical | ✓ VERIFIED | Lines 142-180 of beta_report.py; assembly_beta_report.py passes _canonical_obj at line 28 |
| 8 | company_profile reads exchange, employees from canonical (HTML render path) | ✗ FAILED | canonical kwarg exists in extract_company() but build_template_context() calls it without canonical — context["company"] is set before canonical is computed |
| 9 | company_exec_summary reads exchange, market_cap, revenue from canonical (HTML render path) | ✗ FAILED | Same root cause — extract_exec_summary() called from md_renderer without canonical |
| 10 | scorecard_context reads market_cap, revenue from canonical | ✓ VERIFIED | assembly_dossier.py line 264-265 passes canonical; _build_metrics_strip uses canonical at lines 816-843 |
| 11 | All 5 migrated builders still work when canonical is None (backward compat) | ✓ VERIFIED | test_key_stats_context_with_canonical_none, test_extract_company_backward_compat, test_extract_exec_summary_backward_compat all pass |

**Score:** 9/11 truths verified (7/8 must-have truths verified — company_profile and exec_summary are partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/canonical_metrics.py` | MetricValue, CanonicalMetrics, build_canonical_metrics | ✓ VERIFIED | 194 lines; class MetricValue (frozen), class CanonicalMetrics (frozen), def build_canonical_metrics |
| `src/do_uw/stages/render/_canonical_resolvers.py` | Identity, market, scoring resolvers + shared helpers | ✓ VERIFIED | 367 lines; resolve_exchange, resolve_employees, resolve_market_cap, resolve_ceo_name, etc. |
| `src/do_uw/stages/render/_canonical_resolvers_fin.py` | Financial statement resolvers (income, balance sheet) | ✓ VERIFIED | 228 lines; resolve_revenue, resolve_net_income, resolve_total_assets, resolve_total_debt |
| `tests/test_canonical_metrics.py` | Unit + integration tests against real state.json | ✓ VERIFIED | 341 lines; 24 tests, all passing (14 Plan 01 + 10 Plan 02) |
| `src/do_uw/stages/render/context_builders/assembly_registry.py` | Canonical computation at top of build_html_context | ✓ VERIFIED | Lines 91-104; try/except block computes canonical, stores _canonical and _canonical_obj |
| `src/do_uw/stages/render/context_builders/key_stats_context.py` | Migrated builder reading from canonical | ✓ VERIFIED | canonical kwarg at line 62; reads market_cap, employees, revenue, exchange from canonical |
| `src/do_uw/stages/render/context_builders/beta_report.py` | Migrated builder reading from canonical | ✓ VERIFIED | canonical kwarg at line 100; reads stock_price, employees, 52w high/low, revenue, market_cap |
| `src/do_uw/stages/render/context_builders/company_profile.py` | Migrated builder reading from canonical | ⚠️ PARTIAL | canonical kwarg at line 54; reads exchange (line 101), employees (lines 311-312) — BUT never receives canonical in HTML assembly path |
| `src/do_uw/stages/render/context_builders/scorecard_context.py` | Migrated builder reading from canonical | ✓ VERIFIED | canonical kwarg at line 79; _build_metrics_strip uses canonical for market_cap, revenue, employees |
| `src/do_uw/stages/render/context_builders/company_exec_summary.py` | Migrated builder reading from canonical | ⚠️ PARTIAL | canonical kwarg at line 181; reads exchange, market_cap, revenue, employees (lines 237-241) — BUT never receives canonical in HTML assembly path |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `assembly_registry.py` | `canonical_metrics.py` | `build_canonical_metrics` at line 95 | ✓ WIRED | `from do_uw.stages.render.canonical_metrics import build_canonical_metrics` inside build_html_context |
| `assembly_registry.py` | context dict | `context["_canonical_obj"] = canonical` at line 104 | ✓ WIRED | Object stored for builder consumption |
| `key_stats_context.py` | `canonical_metrics.py` | canonical parameter on build_key_stats_context | ✓ WIRED | Pattern `canonical.*CanonicalMetrics` present in docstring; canonical.revenue.raw used at line 140 |
| `assembly_dossier.py` | `key_stats_context.py` | `canonical=context.get("_canonical_obj")` at line 254 | ✓ WIRED | Canonical flows through to key_stats builder |
| `assembly_dossier.py` | `scorecard_context.py` | `canonical=context.get("_canonical_obj")` at line 265 | ✓ WIRED | Canonical flows through to scorecard builder |
| `assembly_beta_report.py` | `beta_report.py` | `canonical=context.get("_canonical_obj")` at line 28 | ✓ WIRED | Canonical flows through to beta_report builder |
| `assembly_dossier.py` | `company_profile.py` | canonical param | ✗ NOT_WIRED | `extract_company` is called only from md_renderer `build_template_context()` without canonical. assembly_dossier never overwrites context["company"] |
| `assembly_dossier.py` | `company_exec_summary.py` | canonical param | ✗ NOT_WIRED | `extract_exec_summary` is called only from md_renderer `build_template_context()` without canonical |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `canonical_metrics.py` | revenue.raw | `_xbrl_line_item(state, "income_statement", ...)` | Yes — AAPL state.json: revenue.source="xbrl:10-K:FY2024" | ✓ FLOWING |
| `key_stats_context.py` | revenue_raw | `canonical.revenue.raw` (when canonical available) | Yes — test_key_stats_uses_canonical_revenue passes | ✓ FLOWING |
| `beta_report.py` | rev | `canonical.revenue.raw` at line 166 | Yes — wired through assembly_beta_report | ✓ FLOWING |
| `company_profile.py` | exchange | `canonical.exchange.formatted` at line 102 | Hollow in HTML path — context["company"] is populated before canonical exists | ✗ HOLLOW_PROP |
| `scorecard_context.py` | metrics_strip.market_cap | `canonical.market_cap.formatted` at line 817 | Yes — wired through assembly_dossier | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Empty state produces N/A defaults | `build_canonical_metrics(AnalysisState(ticker='TEST'))` | revenue: raw=None formatted='N/A' source='none' confidence='LOW' as_of='' | ✓ PASS |
| assembly_registry wires canonical into context | `ctx = build_html_context(AnalysisState(ticker='TEST')); '_canonical' in ctx` | True; canonical keys: company_name, ticker, exchange, sic_code, sic_description | ✓ PASS |
| 24 canonical tests pass | `uv run pytest tests/test_canonical_metrics.py -x -v` | 24 passed in 8.32s | ✓ PASS |
| Module imports cleanly | Python import of MetricValue, CanonicalMetrics, build_canonical_metrics | "imports OK" | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| METR-01 | 137-01 | CanonicalMetricsRegistry computes each metric exactly once with XBRL-first source priority | ✓ SATISFIED | 22 resolvers, each called exactly once in build_canonical_metrics(); XBRL paths yield source="xbrl:10-K:FY*" confidence="HIGH"; yfinance is explicit else-branch |
| METR-02 | 137-01, 137-02 | Revenue, net income, market cap, stock price, employees, exchange name, CEO name, and growth rates computed once and consumed by all sections | ⚠️ PARTIAL | Computed once in build_canonical_metrics. Consumed by key_stats, scorecard, beta_report. NOT consumed by context["company"] or context["executive_summary"] in HTML path — those use legacy extraction. REQUIREMENTS.md shows as checked [x] but the consumption gap exists. |
| METR-03 | 137-01 | Every metric carries source, as-of date, and confidence level | ✓ SATISFIED | MetricValue has source, as_of, confidence fields; all 22 resolvers set these explicitly; test_every_populated_metric_has_source passes |
| METR-04 | 137-02 | Context builders import from canonical registry instead of independently navigating state | ⚠️ PARTIAL | 3 of 5 builders (key_stats, scorecard, beta_report) fully wired in HTML path. company_profile and company_exec_summary have the canonical parameter but it is never invoked in the HTML assembly path. REQUIREMENTS.md shows as checked [x] but 2 builders are unwired. |

**Note:** REQUIREMENTS.md traceability table shows METR-01 and METR-03 as "Pending" and METR-02 and METR-04 as "Complete" — these statuses are inconsistent with actual implementation. METR-01 and METR-03 are functionally complete. METR-02 and METR-04 are marked complete but have a partial gap in company_profile/exec_summary wiring.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/stages/render/context_builders/company_profile.py` | 54 | `canonical: Any | None = None` — parameter accepted but canonical never passed in HTML path | ⚠️ Warning | context["company"].exchange and .employees are still sourced from legacy extraction in HTML worksheets |
| `src/do_uw/stages/render/context_builders/company_exec_summary.py` | 181 | `canonical: Any | None = None` — parameter accepted but canonical never passed in HTML path | ⚠️ Warning | context["executive_summary"] snapshot values (exchange, market_cap, revenue) may differ from canonical values in other sections |

No stub patterns, TODO comments, empty returns, or hardcoded empty data found in Phase 137 files.

### Human Verification Required

#### 1. Cross-Section Consistency Check

**Test:** Run `underwrite AAPL` (or any ticker with known revenue), open the HTML worksheet, compare: revenue shown in Key Stats vs revenue shown in Company Profile header vs revenue in Scorecard metrics strip.
**Expected:** All three show identical value and formatting (e.g., "$391.0B" everywhere, not "$391.0B" in key_stats but "$390.8B" in company profile).
**Why human:** The gap is that company_profile reads from legacy extraction while key_stats reads from canonical — they may produce the same value for most companies (both use XBRL), but a discrepancy would only be visible in the rendered HTML output.

### Gaps Summary

**Root Cause:** Both gaps share a single root cause — `build_template_context()` in `md_renderer.py` is called first (before canonical is computed) and sets `context["company"]` and `context["executive_summary"]` via `extract_company()` and `extract_exec_summary()` without canonical. The assembly then computes canonical and passes it to subsequent builders (key_stats, scorecard, beta_report) but does not re-invoke the company/exec_summary builders.

**Impact Assessment:** The primary sections consuming cross-section metrics — Key Stats, Scorecard, and Beta Report — ARE wired through canonical. The Company Profile section and Executive Summary snapshot values use legacy extraction. For the goal of "metrics computed exactly once from highest-confidence source and consumed everywhere," this is a structural gap in 2 of the 5 target builders' actual consumption in the render pipeline, even though the code to consume canonical is written and tested.

**Fix Pattern:** In `assembly_dossier.py` (or a new assembly step), add canonical-aware calls that overwrite `context["company"]` and `context["executive_summary"]` after canonical is computed, mirroring the existing pattern for key_stats and scorecard (lines 249-269).

---

_Verified: 2026-03-27T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
