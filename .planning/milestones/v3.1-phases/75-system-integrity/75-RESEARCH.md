# Phase 75: System Integrity -- Manifest, Facets, QA, Learning Loop - Research

**Researched:** 2026-03-07
**Domain:** Brain architecture completeness, data traceability, template validation, semantic QA, closed-loop learning
**Confidence:** HIGH

## Summary

Phase 75 closes four structural gaps in the brain-driven architecture: (1) the Tier 1 data manifest exists as 31 foundational signals in `brain/signals/base/` but is missing Frames API peer benchmarking -- SYS-02 requires adding it; (2) 16 section-level templates exist without facet references -- the template-facet audit needs a CI test and cleanup; (3) no semantic validation exists to verify rendered output matches source data; and (4) the learning loop infrastructure (lifecycle state machine, calibration, fire-rate alerts, feedback processing) is fully built but not wired into automated operation.

The key finding is that most of the code already exists. `brain_lifecycle_v2.py` implements the 5-state lifecycle machine (INCUBATING -> ACTIVE -> MONITORING -> DEPRECATED -> ARCHIVED). `brain_calibration.py` computes threshold drift and fire-rate alerts. `brain_health.py` reports fire-rate distributions. `cli_brain_apply.py` and `cli_feedback_process.py` handle proposal application. The work is primarily about: documenting the manifest, filling the Frames gap, writing CI validation tests, building semantic QA checks, and wiring the existing calibration/lifecycle code into automated triggers rather than CLI-only invocation.

**Primary recommendation:** Focus on validation and integration -- most infrastructure exists. The novel work is semantic QA (comparing rendered HTML values against state data) and auto-triggering calibration/lifecycle proposals after pipeline runs.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SYS-01 | Explicit Tier 1 manifest document | 31 foundational signals exist in `brain/signals/base/`; need formal document + traceability table |
| SYS-02 | Foundational signals cover 100% of Tier 1 | 8-K, Form 4, short interest covered; Frames API missing; need `BASE.PEER.frames` signal |
| SYS-03 | Signal author guide | Document foundational vs evaluative, acquisition blocks, gap_bucket usage |
| SYS-04 | Automated template-to-facet validation CI | 100 facet-referenced templates, 116 actual, 16 orphaned, 0 dangling; audit script proven above |
| SYS-05 | Remove/consolidate orphaned templates | 16 orphaned are section-level wrappers (company.html.j2 etc); most are parent templates, not truly orphaned |
| SYS-06 | Semantic content QA framework | No existing infrastructure; need test that loads state.json + rendered HTML, compares values |
| SYS-07 | Integrate QA into CI | Extend pytest with semantic QA; existing `scripts/qa_compare.py` is manual-only |
| SYS-08 | Closed-loop feedback auto-adjustment | `brain_calibration.py` generates proposals; `cli_feedback_process.py` processes reactions; need auto-trigger after N confirmations |
| SYS-09 | Fire-rate anomaly alerts | `compute_fire_rate_alerts()` exists in brain_calibration.py; need pipeline integration + logging |
| SYS-10 | Signal lifecycle state machine | `brain_lifecycle_v2.py` fully implements 5-state machine with proposal generation; need auto-run after pipeline |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | v2 | All data models, validation reports | Project standard per CLAUDE.md |
| duckdb | latest | Brain signal runs, feedback, proposals, changelog | Existing brain database |
| pyyaml | latest | Brain signal/section YAML loading | Existing brain infrastructure |
| pytest | latest | CI validation tests | Project standard |
| beautifulsoup4 | latest | HTML parsing for semantic QA | Already in project for rendering tests |
| lxml | latest | Fast HTML parsing backend | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich | latest | CLI output for audit/health reports | Already used by brain CLI |
| typer | latest | CLI commands | Already used |

### No New Dependencies Needed
All work uses existing project libraries. No new packages required.

## Architecture Patterns

### Existing Infrastructure Map

```
brain/
  signals/base/           # 6 YAML files, 31 foundational signals (Tier 1 manifest)
  signals/{domain}/        # ~36 YAML files, ~400 evaluative signals
  sections/                # 12 YAML files, each with facets[] listing templates
  brain_lifecycle_v2.py    # 5-state machine: INCUBATING->ACTIVE->MONITORING->DEPRECATED->ARCHIVED
  brain_calibration.py     # Threshold drift + fire-rate alerts + proposal generation
  brain_health.py          # Fire-rate distribution, facet coverage, system metrics
  brain_audit.py           # Staleness, coverage gaps, threshold conflicts, orphans
  brain_effectiveness.py   # Per-signal fire rate computation from brain_signal_runs
  brain_schema.py          # 19 DuckDB tables including brain_feedback, brain_proposals
  config/
    learning_config.json   # co_fire_threshold, min_runs, fire_rate thresholds
```

### Pattern 1: Foundational Signal Declaration
**What:** `type: foundational` signals in `brain/signals/base/` declare Tier 1 data sources
**When to use:** For any data the pipeline ALWAYS acquires regardless of company
**Current state:** 31 signals across 6 files. Missing: Frames API peer benchmarking.
**Gap:** No `BASE.PEER.frames` signal exists. Phase 72 built the Frames client but never declared a foundational signal for it.

### Pattern 2: Proposal-Based Changes
**What:** All threshold/lifecycle changes go through brain_proposals table, reviewed via CLI
**When to use:** Calibration drift, feedback consensus, lifecycle transitions
**Current state:** Fully built. `compute_calibration_report()` generates THRESHOLD_CALIBRATION proposals. `compute_lifecycle_proposals()` generates LIFECYCLE_TRANSITION proposals. `brain apply-proposal` applies them.
**Gap:** These only run when manually invoked via CLI. SYS-08/09/10 require auto-triggering after pipeline runs.

### Pattern 3: Section-Facet-Template Mapping
**What:** `sections/*.yaml` defines facets with `template:` pointing to `.html.j2` files
**Current state:** 100 facet-referenced templates, 116 actual template files, 16 orphans
**Orphan analysis:** The 16 "orphaned" templates are NOT truly orphaned -- they are section-level parent templates (e.g., `sections/company.html.j2`, `sections/governance.html.j2`) that include facet templates via Jinja2 `{% include %}`. They serve as wrapper/layout templates, not facet-level display units.

### Anti-Patterns to Avoid
- **Rewriting existing infrastructure:** The lifecycle, calibration, and fire-rate code is complete. Don't rewrite -- wire it.
- **Making auto-adjustment truly automatic:** User explicitly requires brain changes to be evidence-driven with provenance. Auto-PROPOSE, don't auto-APPLY. The proposal review step must remain.
- **Breaking the CLI-first pattern:** Existing brain management is CLI-driven. Pipeline integration should generate proposals that the CLI then manages, not bypass the CLI.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fire-rate computation | Custom aggregation | `brain_effectiveness.compute_effectiveness()` | Already handles all edge cases |
| Threshold drift detection | Custom statistics | `brain_calibration.compute_threshold_drift()` | Proper sigma-based detection with p90 proposals |
| Lifecycle transitions | Custom state machine | `brain_lifecycle_v2.evaluate_transition()` | Full 5-state machine with locked criteria |
| Feedback processing | Custom aggregation | `knowledge/feedback_process.process_pending_reactions()` | Consensus determination with confidence |
| Template-facet audit | Manual script | `brain_section_schema.load_all_sections()` + glob templates | Schema already parsed |
| HTML value extraction | Regex parsing | BeautifulSoup with CSS selectors | Reliable for semantic QA |

**Key insight:** Phase 75 is an integration and validation phase, not a construction phase. The building blocks exist.

## Common Pitfalls

### Pitfall 1: Misidentifying "Orphaned" Templates
**What goes wrong:** The 16 section-level templates (company.html.j2, governance.html.j2, etc.) appear orphaned because no facet references them, but they are parent templates that INCLUDE facet templates.
**Why it happens:** Facets reference leaf templates; section templates are the structural wrappers.
**How to avoid:** The CI validation test must distinguish between facet-level templates (must be referenced by a facet) and section-level wrapper templates (referenced by the rendering pipeline, not facets). Use naming convention: `sections/{name}.html.j2` = wrapper, `sections/{name}/*.html.j2` = facet.
**Warning signs:** Deleting a "orphaned" template that is actually a wrapper breaks all rendering for that section.

### Pitfall 2: Auto-Apply vs Auto-Propose
**What goes wrong:** SYS-08 says "auto-adjust signal thresholds" which could be interpreted as auto-applying changes. The user has EXPLICITLY stated brain changes must be evidence-driven with full provenance.
**Why it happens:** Convenience vs safety tradeoff.
**How to avoid:** Auto-PROPOSE after N confirmations, with a CLI flag for auto-APPLY in non-interactive mode. Default is proposal generation only.
**Warning signs:** Threshold changes appearing without changelog entries.

### Pitfall 3: Semantic QA False Positives
**What goes wrong:** Rendered values often have formatting (e.g., "$1.2B" vs raw 1200000000) that doesn't match raw state values.
**Why it happens:** Jinja2 filters apply number formatting, abbreviation, currency symbols.
**How to avoid:** Semantic QA must parse formatted values back to numbers (strip $, parse B/M/K suffixes) before comparison. Use tolerance-based matching (within 1% or rounding).
**Warning signs:** Tests that are brittle to formatting changes.

### Pitfall 4: Circular Dependency Between Pipeline and Calibration
**What goes wrong:** If calibration/lifecycle runs inside the pipeline, it could modify signals mid-run.
**Why it happens:** Temptation to "always keep signals fresh."
**How to avoid:** Calibration/lifecycle PROPOSALS are generated post-pipeline as a separate step. Signal definitions are frozen during pipeline execution. Proposals accumulate in DuckDB for later review.
**Warning signs:** Signal definitions changing between ANALYZE start and end.

### Pitfall 5: Form 4 vs insider_trading Naming
**What goes wrong:** SYS-02 says "add Form 4" as foundational but `BASE.MARKET.insider_trading` already covers Form 4 data.
**Why it happens:** The requirement lists data sources; the signal uses a higher-level abstraction.
**How to avoid:** Verify the existing `BASE.MARKET.insider_trading` acquisition block already covers Form 4 XML parsing. It does -- its `fields` include `extracted.market.insider_analysis.transactions`.

## Code Examples

### Template-Facet Validation Test Pattern
```python
# Source: Codebase analysis of brain_section_schema.py + templates structure
import pytest
from pathlib import Path
from do_uw.brain.brain_section_schema import load_all_sections

SECTIONS_DIR = Path("src/do_uw/brain/sections")
TEMPLATES_DIR = Path("src/do_uw/templates/html")

# Section-level wrapper templates (NOT facet-referenced, but required by renderer)
WRAPPER_TEMPLATES = {
    "sections/company.html.j2", "sections/governance.html.j2",
    "sections/litigation.html.j2", "sections/market.html.j2",
    "sections/financial.html.j2", "sections/scoring.html.j2",
    "sections/executive.html.j2", "sections/ai_risk.html.j2",
    "sections/red_flags.html.j2", "sections/identity.html.j2",
    "sections/cover.html.j2", "sections/financial_statements.html.j2",
    "sections/scoring_hazard.html.j2", "sections/scoring_perils.html.j2",
    "sections/scoring_peril_map.html.j2",
}

def test_no_dangling_facet_templates():
    """Every facet template: field points to existing file."""
    sections = load_all_sections(SECTIONS_DIR)
    for section in sections.values():
        for facet in section.facets:
            template_path = TEMPLATES_DIR / facet.template
            assert template_path.exists(), f"Dangling: {facet.id} -> {facet.template}"

def test_no_orphaned_facet_templates():
    """Every non-wrapper template is referenced by at least one facet."""
    sections = load_all_sections(SECTIONS_DIR)
    facet_templates = set()
    for section in sections.values():
        for facet in section.facets:
            facet_templates.add(facet.template)

    for tf in (TEMPLATES_DIR / "sections").rglob("*.html.j2"):
        rel = str(tf.relative_to(TEMPLATES_DIR))
        if rel not in WRAPPER_TEMPLATES:
            assert rel in facet_templates, f"Orphaned: {rel}"
```

### Semantic QA Pattern: Revenue Match
```python
# Source: Project architecture analysis
from bs4 import BeautifulSoup
import json
import re

def _parse_financial_value(text: str) -> float | None:
    """Parse formatted financial value back to number."""
    text = text.strip().replace(",", "").replace("$", "")
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            try:
                return float(text[:-1]) * mult
            except ValueError:
                return None
    try:
        return float(text)
    except ValueError:
        return None

def validate_revenue_matches_xbrl(html_path: str, state_path: str) -> list[str]:
    """Check that revenue in HTML matches XBRL source value."""
    errors = []
    with open(state_path) as f:
        state = json.load(f)
    with open(html_path) as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # Extract XBRL revenue from state
    xbrl_revenue = None
    for stmt in state.get("extracted", {}).get("financials", {}).get("statements", []):
        if stmt.get("statement_type") == "income_statement":
            for item in stmt.get("line_items", []):
                if item.get("concept") == "revenue":
                    xbrl_revenue = item.get("value")
                    break

    if xbrl_revenue is None:
        return []  # No XBRL revenue to validate against

    # Find revenue in HTML (look for labeled value)
    # Tolerance: within 1% for rounding
    # ... implementation specific to template structure
    return errors
```

### Post-Pipeline Calibration Hook
```python
# Source: Codebase analysis of brain_calibration.py + brain_lifecycle_v2.py
def run_post_pipeline_learning(conn, ticker: str, run_id: str) -> dict:
    """Run calibration + lifecycle analysis after pipeline completion.

    Generates proposals only -- never auto-applies.
    """
    from do_uw.brain.brain_calibration import compute_calibration_report
    from do_uw.brain.brain_lifecycle_v2 import compute_lifecycle_proposals

    cal_report = compute_calibration_report(conn)
    lifecycle_report = compute_lifecycle_proposals(conn)

    return {
        "drift_signals": len(cal_report.drift_signals),
        "fire_rate_alerts": len(cal_report.fire_rate_alerts),
        "lifecycle_proposals": len(lifecycle_report.proposals),
        "total_proposals": (
            cal_report.total_proposals_generated +
            len(lifecycle_report.proposals)
        ),
    }
```

## Current State Inventory

### Foundational Signals (31 total across 6 files)

| File | Count | Covers |
|------|-------|--------|
| `base/filings.yaml` | 5 | 10-K, 10-Q, DEF 14A, 8-K, (Form 4 via market) |
| `base/market.yaml` | 3 (4 with insider) | Stock price, institutional ownership, short interest, insider trading |
| `base/xbrl.yaml` | 5 (6 with derived) | Balance sheet, income stmt, cash flow, quarterly, derived metrics |
| `base/forensics.yaml` | 7 (8 with MA) | Balance sheet, revenue, capital alloc, debt/tax, Beneish, earnings, M&A forensics |
| `base/litigation.yaml` | 3 (4 with CL) | SCAC, 10-K Item 3, CourtListener |
| `base/news.yaml` | 3 (4 with company) | Blind spot pre, blind spot post, company news |

**Gap:** Frames API peer benchmarking (Phase 72) has no foundational signal. Need `BASE.PEER.frames`.

### Template-Facet Audit Results

| Metric | Count |
|--------|-------|
| Facet-referenced templates | 100 |
| Actual template files | 116 |
| Orphaned (not in any facet) | 16 |
| Dangling (facet points to missing file) | 0 |

The 16 "orphaned" templates break down as:
- **11 section wrappers:** company, governance, litigation, market, financial, scoring, executive, ai_risk, red_flags, identity, cover -- these are parent layout templates
- **4 scoring variants:** scoring_hazard, scoring_perils, scoring_peril_map, financial_statements -- legacy standalone templates
- **1 facet template:** scoring/nlp_analysis.html.j2 -- potentially truly orphaned, needs investigation

### Learning Loop Infrastructure Status

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Lifecycle state machine | brain_lifecycle_v2.py | 474 | Complete, CLI-only |
| Calibration engine | brain_calibration.py | 597 | Complete, CLI-only |
| Fire-rate alerts | brain_calibration.py | (included) | Complete, CLI-only |
| Health metrics | brain_health.py | 218 | Complete, CLI-only |
| Effectiveness tracking | brain_effectiveness.py | 424 | Complete, pipeline-integrated |
| Structural audit | brain_audit.py | 490 | Complete, CLI-only |
| Feedback processing | cli_feedback_process.py | ~80 | Complete, CLI-only |
| Proposal application | cli_brain_apply.py | 66 | Complete, CLI-only |

**Key gap:** None of these run automatically after pipeline completion. All are CLI-invoked.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/brain/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SYS-01 | Tier 1 manifest document | manual | N/A (documentation) | N/A |
| SYS-02 | Foundational signals cover 100% | unit | `uv run pytest tests/brain/test_foundational_coverage.py -x` | Wave 0 |
| SYS-03 | Signal author guide | manual | N/A (documentation) | N/A |
| SYS-04 | No dangling facet refs | unit | `uv run pytest tests/brain/test_template_facet_audit.py -x` | Wave 0 |
| SYS-05 | No orphaned templates | unit | `uv run pytest tests/brain/test_template_facet_audit.py -x` | Wave 0 |
| SYS-06 | Semantic QA matches source | integration | `uv run pytest tests/stages/render/test_semantic_qa.py -x` | Wave 0 |
| SYS-07 | QA in CI | integration | `uv run pytest tests/stages/render/test_semantic_qa.py -x` | Wave 0 |
| SYS-08 | Feedback auto-propose | unit | `uv run pytest tests/brain/test_auto_calibration.py -x` | Wave 0 |
| SYS-09 | Fire-rate alerts | unit | `uv run pytest tests/brain/test_brain_calibration.py -x` | Exists |
| SYS-10 | Lifecycle state machine | unit | `uv run pytest tests/brain/test_brain_lifecycle_v2.py -x` | Exists |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before verify

### Wave 0 Gaps
- [ ] `tests/brain/test_foundational_coverage.py` -- covers SYS-02
- [ ] `tests/brain/test_template_facet_audit.py` -- covers SYS-04, SYS-05
- [ ] `tests/stages/render/test_semantic_qa.py` -- covers SYS-06, SYS-07
- [ ] `tests/brain/test_auto_calibration.py` -- covers SYS-08 (auto-trigger after pipeline)

## Sources

### Primary (HIGH confidence)
- Codebase analysis of `brain_lifecycle_v2.py` (474 lines) -- full lifecycle state machine
- Codebase analysis of `brain_calibration.py` (597 lines) -- threshold drift + fire-rate alerts
- Codebase analysis of `brain/signals/base/` (6 files, 31 foundational signals) -- Tier 1 manifest
- Codebase analysis of `brain/sections/*.yaml` (12 files) -- facet-template mapping
- Direct template-facet audit via Python (100 facet refs, 116 templates, 16 orphans, 0 dangling)
- REQUIREMENTS-v3.1.md -- SYS-01 through SYS-10 definitions
- CLAUDE.md -- data integrity rules, anti-context-rot, brain change provenance requirements

### Secondary (MEDIUM confidence)
- User MEMORY.md -- brain change provenance requirements ("driven by real evidence, not YAML editing")

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all existing project libraries, no new dependencies
- Architecture: HIGH -- direct codebase analysis of all relevant modules
- Pitfalls: HIGH -- identified from codebase patterns and user preferences (MEMORY.md)

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable internal architecture)
