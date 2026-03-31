# Phase 24: Check Calibration & Knowledge Enrichment - Research

**Researched:** 2026-02-11
**Domain:** Check calibration, scoring model validation, knowledge store enrichment, industry playbook validation
**Confidence:** HIGH (based on extensive codebase analysis; this is internal system calibration, not external library research)

## Summary

Phase 24 calibrates the existing 359-check engine against real company output from 10-12 diverse tickers. The codebase already has substantial infrastructure: a check engine with 10 threshold types (309 tiered, 19 info, 10 percentage, etc.), a 10-factor scoring model (F1-F10 totaling 100 risk points), 19 composite patterns, 11 critical red flag gates, and 10 industry playbooks. The validation infrastructure (`angry-dolphin validate run`) already executes multi-ticker batch runs with checkpointing, and ground truth modules exist for 11 tickers.

The key challenge is NOT building new pipeline stages -- it is instrumenting the existing system to observe its behavior across diverse companies, identify anomalies (checks that always/never fire, evidence quality gaps, tier mismatches), fix bugs and thresholds, and enrich the knowledge store with real observations. The `do_uw.knowledge.learning` module already has `record_analysis_run()`, `get_check_effectiveness()`, `find_redundant_pairs()`, and `get_learning_summary()` -- this is the foundation for calibration.

**Primary recommendation:** Build a `do-uw calibrate` CLI command that runs the pipeline on the calibration ticker set, collects per-check firing data via the existing learning infrastructure, computes anomaly metrics, and generates problem-centric Markdown reports. Use the existing `ValidationRunner` pattern for multi-ticker execution, and extend the existing `learning.py` module for the analytical layer.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Dual approach**: Ground truth for top 20 highest-impact checks (auto-ranked by scoring weight x fire rate x severity contribution), reasonableness testing for the remaining 339+
- **10-12 diverse tickers**: AAPL (clean mega), SMCI (distressed tech), XOM (energy stable), MRNA (biotech volatile), NFLX (entertainment growth), plus JPM (financial), PLUG (pre-revenue), HON (industrial conglomerate), COIN (crypto), DIS (media), and 1-2 more for coverage
- **Fix workflow**: Auto-fix obvious bugs (wrong threshold, missing data mapping, check logic errors). Report complex judgment-call issues for manual review. Both happen within this phase.
- **Top 20 checks selected automatically** by impact scoring -- system ranks by (weight x fire rate x severity contribution), not manual selection
- **CLI command + snapshot**: `do-uw calibrate` as a permanent repeatable CLI command. Phase 24 also commits a baseline snapshot to .planning/
- **Problem-centric summary**: Default view shows only anomalies -- checks with 0% or 100% fire rate, LOW evidence quality, tier mismatches vs expectations, contradictions between sections
- **Per-ticker detail in Markdown**: Detailed per-ticker reports in output/calibration/ for drill-down. Summary in .planning/ for project tracking
- **MD-first**: Calibration results validated in Markdown before any visual work
- **Auto-capture + review gate**: System captures all observations as INCUBATING. Surfaces the most interesting for review. Auto-promotes clear patterns after N confirmations across tickers
- **Discover new risk stories**: Validate the existing 17 composite patterns AND discover new ones from co-firing analysis. New patterns go to INCUBATING
- **Redundancy flagged for review**: When checks are identified as redundant (always co-fire), flag for human review -- don't auto-deprecate
- **Scoring weight auto-adjustment within +/-10%**: System can nudge weights within bounds based on calibration evidence. Larger changes require approval
- **Playbooks are CHECK FACTORIES**: Not just display layers -- they generate industry-specific checks that trace back to real claim drivers
- **Claims-driven approach**: Research why claims actually happen in each vertical -- identify metric precursors -- create checks that extract those metrics from filings -- compare to peers -- flag anomalies
- **Industry-specific KPIs extracted from filings**: LLM extraction pulls industry KPIs (same-store sales for retail, book-to-bill for semiconductors, etc.) from 10-K. These become check data points compared to peer benchmarks
- **Deep validation for 4 verticals**: Tech, Healthcare, Energy, Biotech get deep validation (2-3 tickers each, claims research, KPI verification, new check creation)
- **Light validation for remaining 6**: Financial, CPG, Industrials, Media, REITs, Transportation get 1 ticker each with differentiation check. Review needed before deep treatment
- **Always be learning**: Validate existing claim intelligence AND actively research new patterns, theories, regulatory developments. Knowledge store never "complete"
- **Tied to checks**: Every industry insight must trace back to a check

### Claude's Discretion
- Which specific 10-12 tickers beyond the named ones
- Auto-ranking algorithm for top 20 checks
- Threshold for auto-promoting INCUBATING observations
- N value for "confirmed across N tickers" pattern promotion
- Format of CLI `calibrate` command flags and output structure

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

## Standard Stack

### Core (all existing -- no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | existing | CLI `calibrate` command | Already used for `analyze`, `validate`, `knowledge`, `pricing`, `dashboard` |
| rich | existing | Console output, tables, progress | Already used throughout CLI |
| pydantic | v2 | Calibration result models | Project standard for all data models |
| sqlalchemy | 2.0 | Knowledge store operations (notes, checks, playbooks) | Existing knowledge store ORM |

### Supporting (all existing)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `do_uw.validation.runner` | existing | Multi-ticker pipeline execution with checkpointing | Basis for calibration runner |
| `do_uw.knowledge.learning` | existing | `record_analysis_run()`, `find_redundant_pairs()`, `get_learning_summary()` | Core calibration analytics |
| `do_uw.knowledge.store` | existing | Note storage, check queries, playbook queries | Observation storage |
| `do_uw.knowledge.playbooks` | existing | Playbook activation, industry check loading | Playbook validation |

### No New Dependencies
This phase adds NO new external libraries. All calibration tooling is built on existing infrastructure.

## Architecture Patterns

### Recommended Module Structure
```
src/do_uw/
  calibration/                    # NEW module
    __init__.py                   # CalibrationEngine class
    runner.py                     # CalibrationRunner (extends ValidationRunner pattern)
    analyzer.py                   # Check-level analysis (fire rates, evidence quality)
    anomaly_detector.py           # 0%/100% fire rate, tier mismatches, contradictions
    impact_ranker.py              # Auto-rank top 20 checks by weight x fire_rate x severity
    report_generator.py           # Markdown report generation (summary + per-ticker)
    enrichment.py                 # Knowledge store enrichment (observations, patterns)
    playbook_validator.py         # Industry playbook differentiation checks
    weight_adjuster.py            # Scoring weight micro-adjustment within +/-10%
  cli_calibrate.py                # CLI sub-app: angry-dolphin calibrate
```

### Pattern 1: CalibrationRunner (extends ValidationRunner pattern)
**What:** Multi-ticker execution with per-ticker result collection, but instead of just PASS/FAIL, it captures full check-level detail.
**When to use:** The `calibrate run` command.
**Key difference from ValidationRunner:** After pipeline execution, CalibrationRunner loads `state.json` for each completed ticker and extracts the full `state.analysis.check_results` dict. This gives per-check status (TRIGGERED/CLEAR/SKIPPED/INFO), value, threshold_level, evidence, and source for every check across every ticker.

```python
# Source: Existing pattern from do_uw/validation/runner.py
class CalibrationRunner:
    """Run pipeline + collect per-check detail for all tickers."""

    def __init__(self, tickers: list[str], output_dir: Path) -> None:
        self._tickers = tickers
        self._output_dir = output_dir

    def run(self) -> CalibrationReport:
        # Step 1: Run pipeline on all tickers (reuse ValidationRunner or similar)
        # Step 2: Load state.json for each completed ticker
        # Step 3: Extract check_results, scoring, patterns per ticker
        # Step 4: Feed into analyzer for cross-ticker aggregation
        # Step 5: Generate CalibrationReport
        ...
```

### Pattern 2: Impact Ranker for Top 20 Checks
**What:** Automatically rank all 359 checks by `weight x fire_rate x severity_contribution` to identify the top 20 highest-impact checks.
**When to use:** After initial calibration run collects fire rate data.
**Algorithm:**
```python
# For each check:
#   weight = max_points of the factor it maps to (from scoring.json)
#   fire_rate = times_triggered / total_tickers (from calibration run)
#   severity = average threshold_level across firings (red=3, yellow=2, clear=0)
#   impact_score = weight * fire_rate * severity

# The 91 checks without factor mapping (359 - 268 = 91) get impact_score = 0
# and fall into the "remaining 339+" reasonableness bucket.
```

### Pattern 3: Anomaly Detection
**What:** Flag checks that behave unexpectedly across the ticker set.
**Anomaly types:**
1. **0% fire rate** (never fires) -- check may be dead code, data mapping broken, or threshold too strict
2. **100% fire rate** (always fires) -- threshold too permissive, or universally true (ok for some)
3. **LOW evidence quality** -- evidence string is generic ("Qualitative check: value=...") instead of specific
4. **Tier mismatch** -- AAPL (clean mega) expected WIN/WANT but scored WATCH; SMCI (distressed) expected WALK/NO_TOUCH but scored WANT
5. **Section contradiction** -- Section 3 (financial) says distressed but Section 1 (exec summary) says clean
6. **SKIPPED with data available** -- check returns SKIPPED but the data field actually has a value (mapper bug)

### Pattern 4: Knowledge Enrichment Pipeline
**What:** After calibration analysis, automatically create INCUBATING observations in the knowledge store.
**Flow:**
```
calibration_run -> fire_rate_analysis -> co_firing_analysis
                                      -> tier_expectation_check
                                      -> evidence_quality_audit
  |
  v
create_incubating_notes() -- for each anomaly, create a Note with tags
  |
  v
auto_promote_patterns() -- after N tickers confirm a pattern, promote to ACTIVE
```

### Pattern 5: Playbook Differentiation Validation
**What:** For each industry playbook, verify that it produces checks/scores meaningfully different from the generic baseline.
**Test:** Run the same ticker WITH and WITHOUT its playbook. If the output is identical (same checks fire, same scores), the playbook adds no value.
**Deep validation (4 verticals):** TECH (AAPL, SMCI, NVDA), BIOTECH (MRNA), ENERGY (XOM, PLUG), HEALTHCARE -- 2-3 tickers each, verify industry-specific checks fire and produce relevant evidence.

### Anti-Patterns to Avoid
- **Testing in production pipeline:** Calibration MUST NOT modify the production pipeline code. It reads state.json after pipeline runs. Fixes are separate commits.
- **Manual check selection for top 20:** The whole point is automated impact ranking. Don't manually pick the "important" checks.
- **Fixing judgment calls without reporting:** Auto-fix obvious bugs only. Report anything requiring domain judgment for human review.
- **Coupling calibration to rendering:** Calibration validates the intelligence layer (checks, scores, patterns). Rendering is a separate concern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-ticker execution | Custom pipeline loop | `ValidationRunner` pattern | Checkpointing, continue-on-failure, timing already built |
| Fire rate tracking | Manual counting | `do_uw.knowledge.learning.record_analysis_run()` + `get_learning_summary()` | Already computes fire rates, co-firing, Jaccard similarity |
| Redundancy detection | Custom pair analysis | `do_uw.knowledge.learning.find_redundant_pairs()` | Already implements Jaccard similarity with configurable threshold |
| Observation storage | Custom file format | Knowledge store `add_note()` with tags | Notes with FTS5 search already built |
| Playbook loading | Manual JSON parsing | `BackwardCompatLoader` + `playbooks.py` | Already handles all 10 playbooks with SIC/NAICS matching |
| Check config parsing | Custom parser | `execute_checks()` from check_engine.py | Already handles all 10 threshold types |

**Key insight:** The learning.py module is the foundation. It already tracks AnalysisOutcome (ticker, checks_fired, checks_clear, quality_score, tier), computes CheckEffectiveness (fire_rate, co_firing_partners, last_fired), and finds redundant pairs. Phase 24 extends this, not replaces it.

## Common Pitfalls

### Pitfall 1: Check mapper returns None for available data
**What goes wrong:** A check returns SKIPPED because `map_check_data()` returns `{field: None}` even though the data exists in `state.extracted`.
**Why it happens:** The mapper in `check_mappers.py` uses `_safe_sourced()` to unwrap `SourcedValue`. If the field path is wrong (e.g., accessing `extracted.financials.liquidity` but the actual path is `extracted.financials.distress`), the mapper returns None.
**How to avoid:** Cross-reference the SKIPPED checks against actual state.json to see if the data IS present but the mapper missed it.
**Warning signs:** High SKIPPED rate (>30%) for a section indicates systematic mapper issues.

### Pitfall 2: Threshold direction inversion
**What goes wrong:** A check fires RED for a healthy value because the threshold direction is inverted (e.g., `>` instead of `<`).
**Why it happens:** The `_try_numeric_compare()` function in check_engine.py determines direction from threshold text (`>25%` vs `<25%`). If the threshold string is ambiguous, the check may evaluate backwards.
**How to avoid:** For each TRIGGERED check, verify the data value actually warrants triggering. "Value 1.5 exceeds red threshold 1.0" -- is 1.5 actually bad for this metric?
**Warning signs:** AAPL (clean mega-cap) triggering red on financial health checks.

### Pitfall 3: Factor weight distribution mismatch
**What goes wrong:** F10 (Officer Stability, max 2 points) has 102 check mappings while F8 (Financial Distress, max 8 points) only has 2 check mappings.
**Why it happens:** The factor distribution in checks.json: F10=102, F9=28, F7=27, F5=23, F2=23, F3=18, F4=13, F6=12, F1=43, F8=2. The 102 checks mapped to F10 (a 2-point factor!) suggests many checks are incorrectly mapped or the factor model doesn't reflect how checks actually work.
**How to avoid:** Calibration MUST audit factor mapping distribution. Fix misassigned checks.
**Warning signs:** Many checks map to a low-weight factor while few map to high-weight factors.

### Pitfall 4: INFO checks not contributing to scoring
**What goes wrong:** 19 INFO-type checks and 6 pattern-type checks report values but never affect scoring. This is by design for some (informational context) but may indicate missed scoring opportunities.
**Why it happens:** The check engine treats INFO/pattern/search/multi_period/classification types as always-INFO, never TRIGGERED/CLEAR.
**How to avoid:** Review INFO checks to determine if any should have thresholds added.
**Warning signs:** A check reports an obviously concerning value (e.g., "classification: BINARY_EVENT") but has no scoring impact.

### Pitfall 5: Pattern detection threshold too lax
**What goes wrong:** Composite patterns fire for clean companies because the detection threshold is "majority (>50%) of triggers must match" -- and many triggers match on partial data.
**Why it happens:** `detect_all_patterns()` in pattern_detection.py fires when `len(matched_triggers) > total_triggers / 2.0`. For a pattern with 2 triggers, matching 2/2 fires it. But for a pattern with 3 triggers, matching 2/3 fires it too.
**How to avoid:** Check which patterns fire for clean companies (AAPL, PG, KO). These should have few/no patterns detected.
**Warning signs:** Clean mega-caps showing 5+ detected patterns.

### Pitfall 6: Industry playbooks not generating differentiated output
**What goes wrong:** The TECH_SAAS playbook adds 10 industry-specific checks, but they all return SKIPPED because the data isn't populated by the extractor for industry KPIs.
**Why it happens:** Industry checks reference fields like "ASC 606 multi-element revenue recognition risk" which require LLM extraction of specific disclosure language that may not be in the standard extraction pipeline.
**How to avoid:** Verify that at least some industry checks fire for companies in that vertical. If ALL industry checks are SKIPPED, the playbook adds no value.
**Warning signs:** `get_industry_checks()` returns 10 checks but 0 produce meaningful results.

### Pitfall 7: Calibration data staleness
**What goes wrong:** Running calibration against output from a previous validation run that used old extraction logic.
**Why it happens:** The `output/` directory has cached state.json files from earlier phases. If extraction changed, these are stale.
**How to avoid:** The `calibrate run` command should support a `--fresh` flag (like `validate run`) that clears old output before re-running.
**Warning signs:** Checking state.json file dates and finding they predate recent code changes.

## Code Examples

### CLI Command Structure (following existing pattern)
```python
# Source: Pattern from do_uw/cli_validate.py
calibrate_app = typer.Typer(
    name="calibrate",
    help="Check calibration and knowledge enrichment",
)

@calibrate_app.command("run")
def calibrate_run(
    output: Path = typer.Option(Path("output"), "--output", "-o"),
    fresh: bool = typer.Option(False, "--fresh/--no-fresh"),
    top_n: int = typer.Option(20, "--top-n", help="Number of top-impact checks for ground truth"),
    no_llm: bool = typer.Option(False, "--no-llm"),
) -> None:
    """Run calibration across the calibration ticker set."""
    ...

@calibrate_app.command("report")
def calibrate_report(
    output: Path = typer.Option(Path("output"), "--output", "-o"),
    anomalies_only: bool = typer.Option(True, "--anomalies-only/--all"),
) -> None:
    """Generate calibration report from existing run data."""
    ...

@calibrate_app.command("enrich")
def calibrate_enrich(
    output: Path = typer.Option(Path("output"), "--output", "-o"),
    auto_promote: bool = typer.Option(False, "--auto-promote"),
) -> None:
    """Enrich knowledge store with calibration observations."""
    ...
```

### Impact Ranking Algorithm
```python
# Source: Design from CONTEXT.md decisions
def rank_checks_by_impact(
    checks: list[dict[str, Any]],
    scoring_config: dict[str, Any],
    fire_data: dict[str, CheckEffectiveness],
) -> list[tuple[str, float]]:
    """Rank checks by impact = weight x fire_rate x severity_contribution."""
    factor_weights: dict[str, float] = {}
    for key, cfg in scoring_config.get("factors", {}).items():
        factor_id = cfg.get("factor_id", "")
        factor_weights[factor_id] = float(cfg.get("max_points", 0))

    ranked: list[tuple[str, float]] = []
    for check in checks:
        check_id = check.get("id", "")
        factors = check.get("factors", [])
        weight = max((factor_weights.get(f, 0) for f in factors), default=0)
        eff = fire_data.get(check_id)
        fire_rate = eff.fire_rate if eff else 0.0
        # Severity: approximate from threshold type
        threshold = check.get("threshold", {})
        severity = 3.0 if threshold.get("type") == "tiered" else 1.0
        impact = weight * fire_rate * severity
        ranked.append((check_id, impact))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked
```

### Anomaly Detection Output Format
```python
# Source: CONTEXT.md requirement for problem-centric summary
@dataclass
class CalibrationAnomaly:
    """A detected anomaly in check calibration."""
    anomaly_type: str  # "ZERO_FIRE", "ALWAYS_FIRE", "LOW_EVIDENCE", "TIER_MISMATCH", etc.
    check_id: str
    check_name: str
    description: str
    severity: str  # "BUG", "REVIEW", "INFO"
    tickers_affected: list[str]
    suggested_fix: str | None
```

### Markdown Report Structure
```markdown
# Calibration Report - 2026-02-XX

## Anomaly Summary
| Type | Count | Severity |
|------|-------|----------|
| Dead checks (0% fire rate) | 23 | BUG |
| Always-fire (100%) | 5 | REVIEW |
| Low evidence quality | 41 | REVIEW |
| Tier mismatch vs expectation | 3 | REVIEW |
| SKIPPED with available data | 12 | BUG |

## Top 20 Impact Checks (Ground Truth Candidates)
| Rank | Check ID | Factor | Weight | Fire Rate | Impact |
|------|----------|--------|--------|-----------|--------|
| 1 | SECT6.SCA.active | F1 | 20 | 0.22 | 13.2 |
| ... | ... | ... | ... | ... | ... |

## Tier Expectations vs Actual
| Ticker | Expected | Actual | Match |
|--------|----------|--------|-------|
| AAPL | WIN/WANT | ? | ? |
| SMCI | WALK/NO_TOUCH | ? | ? |
| ... | ... | ... | ... |

## Per-Section Anomaly Detail
### Section 3: Financial
- [BUG] FIN.LIQ.position: 0% fire rate -- mapper returns None for current_ratio
- [REVIEW] FIN.DIST.altman: 100% fire rate -- all tickers have Altman Z-Score populated

## Industry Playbook Differentiation
| Playbook | Tickers | Industry Checks Fired | Differentiation |
|----------|---------|----------------------|-----------------|
| TECH_SAAS | AAPL, SMCI, NVDA | 3/10 | PARTIAL |
| BIOTECH_PHARMA | MRNA | 2/10 | PARTIAL |
| ... | ... | ... | ... |
```

### Recording Calibration Observations
```python
# Source: Pattern from do_uw/knowledge/learning.py
from do_uw.knowledge.store import KnowledgeStore

def record_calibration_observation(
    store: KnowledgeStore,
    anomaly: CalibrationAnomaly,
) -> None:
    """Record a calibration observation as INCUBATING note."""
    store.add_note(
        title=f"Calibration: {anomaly.anomaly_type} - {anomaly.check_id}",
        content=json.dumps({
            "anomaly_type": anomaly.anomaly_type,
            "check_id": anomaly.check_id,
            "description": anomaly.description,
            "severity": anomaly.severity,
            "tickers_affected": anomaly.tickers_affected,
            "suggested_fix": anomaly.suggested_fix,
        }),
        tags="calibration,incubating",
        source="calibration_engine",
    )
```

## Existing Infrastructure Map

### What Already Exists (use, don't rebuild)

| Component | Location | What It Does | Phase 24 Usage |
|-----------|----------|-------------|----------------|
| `check_engine.py` | `stages/analyze/` | Executes 359 checks against ExtractedData | Read results from state.json |
| `check_mappers.py` | `stages/analyze/` | Maps check IDs to data fields | Debug SKIPPED checks |
| `check_results.py` | `stages/analyze/` | CheckResult model with status/value/evidence | Core calibration data |
| `pattern_detection.py` | `stages/score/` | Detects 19 composite patterns | Validate pattern firings |
| `factor_scoring.py` | `stages/score/` | Scores 10 factors (F1-F10) | Verify factor distribution |
| `red_flag_gates.py` | `stages/score/` | Evaluates 11 CRF gates | Verify CRF behavior |
| `learning.py` | `knowledge/` | Fire rates, co-firing, redundancy | Core analytics foundation |
| `playbooks.py` | `knowledge/` | 10 industry playbooks | Differentiation validation |
| `ValidationRunner` | `validation/runner.py` | Multi-ticker with checkpointing | Calibration run pattern |
| `validation/config.py` | `validation/` | 24-ticker set with categories | Override with calibration set |
| Ground truth modules | `tests/ground_truth/` | 11 tickers with verified data | Extend for check-level truth |

### What Needs Building

| Component | Purpose | Complexity |
|-----------|---------|------------|
| `calibration/` module | Calibration engine, analyzer, reporter | MEDIUM |
| `cli_calibrate.py` | CLI sub-app | LOW (follows existing pattern) |
| Impact ranking algorithm | Auto-rank top 20 checks | LOW |
| Anomaly detection | 6 anomaly types | MEDIUM |
| Report generator | Markdown summary + per-ticker detail | MEDIUM |
| Enrichment pipeline | INCUBATING observations, auto-promotion | MEDIUM |
| Playbook validator | Differentiation testing | LOW |
| Weight adjuster | +/-10% nudge with evidence | LOW |
| Calibration ticker config | Ticker set with expected tiers | LOW |

## Calibration Ticker Set

### Recommended Set (12 tickers)
Based on CONTEXT.md requirements and existing infrastructure:

| Ticker | Vertical | Archetype | Expected Tier | Playbook | Notes |
|--------|----------|-----------|---------------|----------|-------|
| AAPL | Tech | Clean mega-cap | WIN/WANT | TECH_SAAS | Already has ground truth, output |
| SMCI | Tech | Distressed/known outcome | WALK/NO_TOUCH | TECH_SAAS | Known outcome, ground truth exists |
| XOM | Energy | Stable large-cap | WANT/WRITE | ENERGY_UTILITIES | Ground truth exists |
| MRNA | Biotech | Volatile growth | WRITE/WATCH | BIOTECH_PHARMA | Ground truth exists |
| NFLX | Entertainment | Growth darling | WANT/WRITE | MEDIA_ENTERTAINMENT | Ground truth exists |
| JPM | Financial | Stable large-cap | WANT/WRITE | FINANCIAL_SERVICES | Ground truth exists (jpm.py) |
| PLUG | Energy | Pre-revenue/distressed | WATCH/WALK | ENERGY_UTILITIES | Known outcome, validation set |
| HON | Industrial | Conglomerate | WANT/WRITE | INDUSTRIALS_MFG | Validation set ticker |
| COIN | Crypto/Tech | Volatile/regulatory | WRITE/WATCH | TECH_SAAS | Known outcome, ground truth |
| DIS | Media | Turnaround | WRITE/WATCH | MEDIA_ENTERTAINMENT | Ground truth exists |
| PG | CPG | Stable blue chip | WIN/WANT | CPG_CONSUMER | Ground truth exists |
| NVDA | Tech | High-growth mega | WIN/WANT | TECH_SAAS | Ground truth exists, validation set |

**Deep validation verticals (2-3 tickers each):**
- Tech: AAPL, SMCI, NVDA
- Biotech/Healthcare: MRNA
- Energy: XOM, PLUG
- Financials: JPM

**Light validation (1 ticker each):**
- CPG: PG
- Media: DIS, NFLX (2 tickers available)
- Industrials: HON
- REITs: (not in set -- could add PLD if needed)
- Transportation: (not in set -- could add UNP if needed)

### Existing Output Status
9 of the recommended 12 tickers already have completed pipeline output in `output/`:
AAPL, SMCI, XOM, MRNA, NFLX, COIN, DIS, PG, NVDA (from validation run 2026-02-11).
JPM, PLUG, HON need pipeline runs (already in validation config.py).

## Factor Distribution Analysis

### Current Check-to-Factor Mapping
| Factor | Name | Max Points | Checks Mapped | Checks/Point |
|--------|------|-----------|---------------|--------------|
| F1 | Prior Litigation | 20 | 43 | 2.15 |
| F2 | Stock Decline | 15 | 23 | 1.53 |
| F3 | Restatement/Audit | 12 | 18 | 1.50 |
| F4 | IPO/SPAC/M&A | 10 | 13 | 1.30 |
| F5 | Guidance Misses | 10 | 23 | 2.30 |
| F6 | Short Interest | 8 | 12 | 1.50 |
| F7 | Volatility | 9 | 27 | 3.00 |
| F8 | Financial Distress | 8 | 2 | 0.25 |
| F9 | Governance | 6 | 28 | 4.67 |
| F10 | Officer Stability | 2 | 102 | 51.0 |

**Anomaly:** F10 (Officer Stability, max 2 points) has 102 mapped checks -- 51 checks per scoring point. This almost certainly indicates mass mis-mapping. Many governance and section 5 checks are mapped to F10 that should probably map to F9 or other factors.

**Anomaly:** F8 (Financial Distress, max 8 points) has only 2 mapped checks. The financial section has 32 checks total, but most map to F3 or F7 instead of F8.

These are calibration findings that the phase should validate and fix.

### Unmapped Checks
91 checks (359 - 268 = 91) have no factor mapping. These are either INFO-only checks or checks whose factor field was left empty. Calibration should classify them as either:
- Correctly informational (no scoring impact)
- Missing factor assignment (should score but don't)

## Scoring Model Observations

### 10-Factor Model Summary
- **Total points:** 100 (quality_score = 100 - risk_points)
- **6 tiers:** WIN (86-100), WANT (71-85), WRITE (51-70), WATCH (31-50), WALK (11-30), NO_TOUCH (0-10)
- **11 CRF gates** cap quality score regardless of factor scores
- **19 composite patterns** add modifier points to factors

### Weight Distribution
F1 (20%) + F2 (15%) = 35% of scoring comes from litigation and stock decline. This is appropriate for D&O underwriting (stock drops and lawsuits are the primary claim drivers).

### Pattern Integration
Patterns modify factor scores in place via `_apply_pattern_modifiers()`. After pattern application, factor scores are re-capped at max_points. This means a pattern can push a factor to its ceiling but not beyond.

## Knowledge Store Integration

### Current State
- `knowledge.db` (SQLite): 827KB, contains checks, patterns, red flags, sectors, scoring rules, notes, industry playbooks
- `learning.py`: Infrastructure for recording analysis runs and computing effectiveness
- No analysis runs recorded yet (learning data starts with Phase 24)

### Enrichment Strategy
1. **Record analysis runs:** After each calibration ticker completes, call `record_analysis_run()` with the outcome
2. **Compute effectiveness:** After all tickers complete, call `get_check_effectiveness()` for each check
3. **Find redundant pairs:** Call `find_redundant_pairs(threshold=0.85)` across all runs
4. **Create INCUBATING notes:** For each anomaly, create a tagged note in the knowledge store
5. **Co-firing analysis:** New patterns emerge from checks that frequently co-fire but aren't in any existing composite pattern

### Auto-Promotion Logic
**Recommendation for N value:** N=3 (pattern confirmed across 3 or more tickers = auto-promote from INCUBATING to CANDIDATE). This is conservative given a 12-ticker set. A pattern that appears in 3/12 tickers (25%) is statistically notable.

**Threshold for auto-promoting observations:** Require both:
- Confidence: observation confirmed by 3+ tickers
- Consistency: same direction (all positive or all negative)
- Review gate: auto-promoted items appear in calibration report for human verification

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual check review | Automated calibration with anomaly detection | Phase 24 | Scalable, repeatable quality validation |
| Ground truth for extraction only | Ground truth for checks + scoring + tiers | Phase 24 | End-to-end quality validation |
| Static playbooks | Playbooks as check factories with claims research | Phase 24 | Industry intelligence that actually drives checks |
| One-time scoring weights | Evidence-based weight adjustment within bounds | Phase 24 | Scoring model that learns from data |

## Open Questions

1. **How to handle tickers that need fresh pipeline runs?**
   - What we know: 9/12 tickers have cached output. JPM, PLUG, HON need runs (~35-90 min each).
   - What's unclear: Whether to run fresh for all 12 or use cached where available.
   - Recommendation: Use cached output for initial calibration pass, then `--fresh` re-run for discrepancies.

2. **Industry KPI extraction for playbook validation**
   - What we know: CONTEXT.md says "LLM extraction pulls industry KPIs (same-store sales, book-to-bill, etc.)"
   - What's unclear: The current LLM extractor may not pull these specific KPIs. This may require extraction prompt changes.
   - Recommendation: Validate what the extractor currently pulls for each vertical. If KPIs are missing, that's a finding, not a blocker. New extraction prompts can be added as industry checks.

3. **What constitutes a "claims research" deliverable?**
   - What we know: "Research why claims actually happen in each vertical" is a core requirement.
   - What's unclear: Whether this is automated (web search for claim patterns) or manual research.
   - Recommendation: Start with existing `claim_theories` in playbook data. Validate against known outcomes (SMCI, COIN, PLUG, RIDE, LCID). Add new theories discovered during calibration.

4. **How to structure the baseline snapshot in .planning/?**
   - What we know: CONTEXT.md says "commits a baseline snapshot to .planning/"
   - What's unclear: Exact format and what to include.
   - Recommendation: `.planning/phases/24-check-calibration-knowledge-enrichment/baseline/` containing the calibration summary Markdown, anomaly list, and fire rate table. This becomes the reference point for future calibration runs.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/analyze/check_engine.py` -- Check execution engine (10 threshold types, 359 checks)
- `src/do_uw/stages/analyze/check_mappers.py` -- Data mapping for sections 1-6
- `src/do_uw/stages/score/__init__.py` -- 16-step scoring pipeline
- `src/do_uw/stages/score/pattern_detection.py` -- 19 composite patterns
- `src/do_uw/brain/checks.json` -- 359 check definitions (9,215 lines)
- `src/do_uw/brain/scoring.json` -- 10-factor scoring model (1,382 lines)
- `src/do_uw/brain/patterns.json` -- 19 composite patterns (1,547 lines)
- `src/do_uw/brain/red_flags.json` -- 11 CRF gates
- `src/do_uw/brain/sectors.json` -- Sector baselines
- `src/do_uw/knowledge/learning.py` -- Learning infrastructure (fire rates, co-firing, redundancy)
- `src/do_uw/knowledge/playbooks.py` -- Playbook activation and query
- `src/do_uw/knowledge/playbook_data.py` -- 10 industry playbook definitions
- `src/do_uw/validation/runner.py` -- Multi-ticker validation runner
- `src/do_uw/validation/config.py` -- 24-ticker validation set
- `src/do_uw/cli_validate.py` -- Validate CLI sub-app (pattern for calibrate)
- `tests/ground_truth/` -- 11 ground truth modules

### Secondary (MEDIUM confidence)
- `output/validation_report.json` -- 9-ticker validation run (2026-02-11), all PASS
- Ground truth verification files (11 tickers, varying coverage depth)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all existing libraries, no new dependencies
- Architecture: HIGH -- follows established codebase patterns (CLI sub-apps, ValidationRunner, learning.py)
- Check analysis: HIGH -- based on actual codebase analysis of 359 checks, 10 factors, 19 patterns
- Pitfalls: HIGH -- derived from actual code inspection (mapper null paths, threshold directions, factor mis-mapping)
- Playbook validation: MEDIUM -- playbook data exists but industry KPI extraction is untested
- Knowledge enrichment: MEDIUM -- learning.py infrastructure exists but has never been used with real data

**Research date:** 2026-02-11
**Valid until:** Indefinite (internal codebase analysis, not external library research)
