# Phase 121: Scoring Calibration - Research

**Researched:** 2026-03-21
**Domain:** CRF ceiling calibration, tier classification, weighted CRF compounding
**Confidence:** HIGH

## Summary

The core problem is well-characterized: AAPL (composite 88.8, $3.6T mega-cap, 1 SCA) and ANGI (composite 84.5, $326M micro-cap, 17 CRFs triggered) both land in WALK tier because CRF ceilings are flat -- CRF-1 (active SCA) caps at 30 regardless of company size/severity, and CRF-13 (Altman distress) caps at 25 regardless of distress severity. The fix requires making CRF ceilings context-sensitive (size x severity matrix) and introducing weighted compounding for multiple CRFs.

The existing architecture is well-suited for this change. CRF ceilings are already config-driven (`scoring.json`), ceiling application is a single function (`apply_crf_ceilings()`), and tier classification is a pure config lookup (`classify_tier()`). The main implementation work is: (1) extending the CRF ceiling config schema to support size/severity conditioning, (2) rewriting `apply_crf_ceilings()` to use weighted compounding instead of "lowest wins", and (3) building a calibration harness to run 6+ tickers and compare score distributions before/after.

**Primary recommendation:** Extend `scoring.json` CRF ceiling entries with a `size_severity_matrix` field, add a new `apply_weighted_crf_ceilings()` function alongside the existing one (keep the old function for regression comparison), and build a `scripts/calibration_baseline.py` script for multi-ticker comparison.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **CRF ceilings are size x severity matrix**: Mega-cap (>$100B) + 1 SCA = ceiling ~70 (WANT range); Micro-cap (<$2B) + 1 SCA = ceiling ~30 (WALK range); Any size + restatement + SCA = ceiling ~30 (WALK). Specific matrix values are starting points.
- **Distress ceiling depends on distress severity**: Altman <1.0 with negative equity = ceiling 20; Altman 1.0-1.8 (gray zone) = ceiling 40; Going concern opinion = ceiling 15
- **Multiple CRFs use weighted compounding**: Each CRF has a severity weight, sum of weights maps to final ceiling. More triggered CRFs = lower ceiling. Not just "most severe wins."
- **Keep 6 tiers**: WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH
- **Tier boundary adjustment deferred** until distribution analysis across 6+ tickers
- **6 ticker calibration set**: HNGE, AAPL, ANGI + 3 Claude-selected for diversity
- **Success criteria**: User assigns expected tier per ticker (expert judgment), AND distribution uses 3+ distinct tiers. If conflict, user judgment wins.
- **DDL discrepancy fix** (FIX-02) included

### Claude's Discretion
- Exact CRF severity weights for the weighted compound model
- Which 3 additional tickers to select for diversity
- Implementation approach for size-conditioned ceilings (config-driven vs code-driven)
- Tier boundary adjustment values (if distribution analysis reveals clustering)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCORE-01 | CRF ceiling values conditioned on company size/financial health | Size-severity matrix in scoring.json, market_cap lookup in apply_weighted_crf_ceilings() |
| SCORE-02 | Multi-ticker baseline captured (5+ tickers) before and after calibration | Calibration script with JSON baseline snapshots, 6-ticker set |
| SCORE-03 | AAPL and ANGI produce visibly different tiers | AAPL ceiling ~70 (WANT) vs ANGI ceiling ~25 (WALK) from size-conditioned CRF-1 |
| SCORE-04 | Tier distribution across test tickers uses full spectrum, not compressed into WALK/WATCH | Distribution analysis after calibration, boundary adjustment if needed |
| FIX-02 | DDL narrative estimate consistent with scorecard DDL | Single DDL source: use settlement_prediction DDL from scoring stage, not rough estimate in sect1_findings_data |
</phase_requirements>

## Standard Stack

This phase modifies existing Python modules and JSON config. No new packages required.

### Core (Existing)
| Module | Purpose | Why |
|--------|---------|-----|
| `brain/config/scoring.json` | CRF ceilings, tier boundaries, factor weights | Single authoritative config source |
| `stages/score/red_flag_gates.py` | CRF evaluation + ceiling application | `apply_crf_ceilings()` is the modification target |
| `stages/score/tier_classification.py` | Tier from quality score | Pure config lookup, may need boundary changes |
| `stages/score/__init__.py` | 18-step scoring orchestration | Calls apply_crf_ceilings at Step 6 |

### Supporting (Existing)
| Module | Purpose | Relevance |
|--------|---------|-----------|
| `stages/score/red_flag_gates_enhanced.py` | CRF-12 through CRF-17 evaluation | CRF-13 (Altman) needs severity-graduated ceiling |
| `stages/score/settlement_prediction.py` | DDL-based settlement model | Source of authoritative DDL for FIX-02 |
| `stages/render/context_builders/ddl_context.py` | Render-time DDL calculation | Second DDL source causing FIX-02 discrepancy |
| `stages/render/sections/sect1_findings_data.py` | Narrative DDL estimate | Third DDL source (rough estimate), causes FIX-02 |

### New (To Create)
| Module | Purpose | Why |
|--------|---------|-----|
| `scripts/calibration_baseline.py` | Multi-ticker score comparison | SCORE-02 requires before/after baselines |

## Architecture Patterns

### Current Scoring Flow (18 Steps)
```
Step 1: evaluate_red_flag_gates() -> list[RedFlagResult]
Step 2: score_all_factors() -> list[FactorScore]
Steps 3-4: Patterns + modifiers
Step 5: composite = 100 - sum(factor_points)
Step 6: quality_score = apply_crf_ceilings(composite, red_flags) ← MODIFICATION TARGET
Step 7: tier = classify_tier(quality_score, tier_config) ← MAY NEED BOUNDARY CHANGES
Steps 8-18: Risk type, allegations, probability, severity, etc.
```

### Current Problem Diagnosis
From actual state.json data:

| Ticker | Composite | Quality (after CRF) | Tier | Binding CRF | CRFs Triggered | Market Cap |
|--------|-----------|---------------------|------|-------------|----------------|------------|
| AAPL | 88.8 | 30.0 | WALK | CRF-1 | 1 (active SCA) | $3.6T |
| ANGI | 84.5 | 25.0 | WALK | CRF-13 | 17 (all of them) | $326M |

Both are WALK despite AAPL having one routine SCA and ANGI having 17 CRFs triggered. CRF-1 caps AAPL at 30 and CRF-13 caps ANGI at 25 -- only a 5-point difference.

### Pattern 1: Size-Severity CRF Ceiling Matrix
**What:** Each CRF ceiling is a function of `(company_size, trigger_severity)` instead of a flat number.
**When to use:** CRF-1 (Active SCA), CRF-8 (catastrophic decline), CRF-13 (Altman distress) -- any CRF where the same trigger has different underwriting implications based on company profile.

**Config schema extension in scoring.json:**
```json
{
  "trigger": "Active securities class action",
  "id": "CRF-001",
  "max_tier": "WALK",
  "max_quality_score": 30,
  "size_severity_matrix": {
    "mega_cap": {"threshold_usd": 100e9, "ceiling": 70, "max_tier": "WRITE"},
    "large_cap": {"threshold_usd": 10e9, "ceiling": 55, "max_tier": "WRITE"},
    "mid_cap": {"threshold_usd": 2e9, "ceiling": 40, "max_tier": "WATCH"},
    "small_cap": {"threshold_usd": 500e6, "ceiling": 30, "max_tier": "WALK"},
    "micro_cap": {"threshold_usd": 0, "ceiling": 25, "max_tier": "WALK"}
  }
}
```

**Code pattern:**
```python
def _resolve_crf_ceiling(
    crf_entry: dict[str, Any],
    market_cap: float | None,
) -> tuple[int, str]:
    """Resolve CRF ceiling using size-severity matrix if available.

    Falls back to flat max_quality_score if no matrix defined or no market cap.
    """
    matrix = crf_entry.get("size_severity_matrix")
    if matrix is None or market_cap is None:
        return int(crf_entry.get("max_quality_score", 100)), str(crf_entry.get("max_tier", ""))

    # Walk tiers from largest to smallest
    for tier_name in ("mega_cap", "large_cap", "mid_cap", "small_cap", "micro_cap"):
        tier = matrix.get(tier_name)
        if tier is None:
            continue
        if market_cap >= float(tier["threshold_usd"]):
            return int(tier["ceiling"]), str(tier.get("max_tier", ""))

    # Fallback to flat ceiling
    return int(crf_entry.get("max_quality_score", 100)), str(crf_entry.get("max_tier", ""))
```

### Pattern 2: Weighted CRF Compounding
**What:** Instead of `min(all_triggered_ceilings)`, compute a weighted aggregate that decreases as more CRFs fire.
**When to use:** When multiple CRFs are triggered (ANGI case: 17 CRFs).

**Algorithm:**
```
1. Each CRF has a severity_weight (0.0-1.0)
2. For each triggered CRF, look up its size-conditioned ceiling
3. Sort triggered CRFs by ceiling ascending (most severe first)
4. Primary ceiling = lowest triggered ceiling
5. Each additional CRF compounds: reduction = severity_weight * compounding_factor
6. Final ceiling = primary_ceiling * (1 - sum(additional_reductions))
7. Floor: never below 5 (always allow NO_TOUCH distinction)
```

**Example (ANGI with 17 CRFs):**
- CRF-13 (Altman distress, micro-cap): ceiling 20 (primary)
- CRF-1 (active SCA, micro-cap): weight 0.3 -> additional -6 points
- CRF-8 (catastrophic decline): weight 0.2 -> additional -4
- ... remaining CRFs compound further
- Final ceiling: ~10 (NO_TOUCH territory)

**Example (AAPL with 1 CRF):**
- CRF-1 (active SCA, mega-cap): ceiling 70 (primary)
- No additional CRFs -> no compounding
- Final ceiling: 70 (WANT territory)

### Pattern 3: Distress-Graduated CRF-13
**What:** CRF-13 ceiling varies by Altman Z-Score severity, not binary.
**Config:**
```json
{
  "id": "CRF-013",
  "trigger": "Distress Zone (Altman Z < 1.81)",
  "distress_graduation": {
    "going_concern": {"ceiling": 15, "max_tier": "NO_TOUCH"},
    "severe": {"z_max": 1.0, "negative_equity": true, "ceiling": 20, "max_tier": "WALK"},
    "distress": {"z_max": 1.81, "ceiling": 40, "max_tier": "WATCH"},
    "gray": {"z_max": 2.99, "ceiling": 55, "max_tier": "WRITE"}
  }
}
```

### Pattern 4: FIX-02 DDL Consistency
**What:** The DDL discrepancy comes from three independent DDL calculations:
1. **Score stage** (`settlement_prediction.py`): `compute_ddl()` = market_cap * max_drop_magnitude (used in scorecard)
2. **Render-time** (`ddl_context.py`): Volume-weighted DDL = shares_traded * avg_overpayment (more accurate, used in HTML)
3. **Narrative estimate** (`sect1_findings_data.py`): `ddl_estimate()` = market_cap * decline_pct (rough, used in text)

**Fix:** Make the narrative use the same DDL source as the scorecard. The `settlement_prediction` DDL is stored in `state.analysis.settlement_prediction.ddl_amount`. The narrative builder should read this value instead of computing its own.

### Anti-Patterns to Avoid
- **Hardcoding ceiling values in Python**: All ceiling values MUST remain in `scoring.json` config. Python code reads config, never defines ceilings.
- **Breaking the existing scoring pipeline**: Keep the current `apply_crf_ceilings()` function signature. The new weighted version should be called from the same Step 6 location.
- **Forgetting to update both ceiling systems**: `scoring.json` has `critical_red_flag_ceilings` AND `red_flags.json` has `escalation_triggers` with `max_quality_score`. Both need consistent values, or one should reference the other.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-ticker comparison | Custom diff scripts | JSON baseline snapshots + `diff` | Reproducible, storable, version-controlled |
| Market cap tier lookup | Inline conditionals | Config-driven tier lookup (scoring.json already has `market_cap_multipliers.tiers`) | Consistent with existing patterns |
| Altman Z-Score extraction | Re-parse financials | `_check_altman_distress()` already extracts Z-Score | DRY -- enhance existing, don't duplicate |

## Common Pitfalls

### Pitfall 1: CRF ID Normalization
**What goes wrong:** CRF IDs are inconsistent between `red_flags.json` (CRF-01) and `scoring.json` (CRF-001). The `_normalize_crf_id()` function strips leading zeros.
**How to avoid:** Always use `_normalize_crf_id()` when comparing CRF IDs across configs. Test with both formats.

### Pitfall 2: Dual Ceiling Sources
**What goes wrong:** `scoring.json.critical_red_flag_ceilings` and `red_flags.json.escalation_triggers` BOTH define ceiling values. `evaluate_red_flag_gates()` checks both (line 84-93) with `scoring.json` taking priority.
**How to avoid:** Update `scoring.json` as the primary source. Keep `red_flags.json` values as fallbacks but document that `scoring.json` overrides.

### Pitfall 3: Market Cap Not Available
**What goes wrong:** `state.company.market_cap` could be None for some companies. Size-conditioned ceilings need a fallback.
**How to avoid:** When market_cap is None, fall back to the flat (most conservative) ceiling. Log a warning.

### Pitfall 4: ANGI's 17 CRFs Are Mostly False Positives
**What goes wrong:** ANGI triggers ALL 17 CRFs including CRF-1 through CRF-11 AND CRF-12 through CRF-17. Many of these are likely false positives from LLM extraction issues. Weighted compounding would over-penalize.
**How to avoid:** The weighted compounding model must be robust to false positive CRFs. CRFs with lower severity_weight (0.05) contribute minimal additional reduction. Also: review ANGI's CRF evidence during calibration -- if CRF-1 fires on a non-securities case, that's a separate bug.

### Pitfall 5: DDL Calculation Divergence
**What goes wrong:** Three independent DDL calculations (score stage, render-time, narrative) use different methodologies and produce wildly different numbers (e.g., $513B vs $66B).
**Root cause:** `settlement_prediction.compute_ddl()` uses `market_cap * max_drop_magnitude`, while `ddl_context._calc_window()` uses `total_vol * (price_drop / 2)` (volume-weighted). These are fundamentally different models.
**How to avoid:** For FIX-02, the narrative should reference the same DDL that the scorecard displays. Store the DDL value computed during scoring on `state.scoring` or `state.analysis.settlement_prediction`, and have the narrative builder read that value.

## Code Examples

### Modifying apply_crf_ceilings for weighted compounding
```python
def apply_weighted_crf_ceilings(
    composite_score: float,
    red_flag_results: list[RedFlagResult],
    scoring_config: dict[str, Any],
    market_cap: float | None,
) -> tuple[float, str | None, list[dict[str, Any]]]:
    """Apply size-conditioned, weighted-compound CRF ceilings.

    Returns:
        (quality_score, binding_ceiling_id, ceiling_details)
    """
    ceilings_cfg = scoring_config.get("critical_red_flag_ceilings", {}).get("ceilings", [])
    ceiling_lookup = {_normalize_crf_id(str(c.get("id", ""))): c for c in ceilings_cfg}

    triggered: list[tuple[str, int, float]] = []  # (crf_id, ceiling, weight)
    for result in red_flag_results:
        if not result.triggered or result.flag_id is None:
            continue
        cfg = ceiling_lookup.get(result.flag_id, {})
        ceiling, _tier = _resolve_crf_ceiling(cfg, market_cap)
        weight = float(cfg.get("severity_weight", 0.15))
        triggered.append((result.flag_id, ceiling, weight))

    if not triggered:
        return composite_score, None, []

    # Sort by ceiling ascending (most severe first)
    triggered.sort(key=lambda t: t[1])

    # Primary ceiling from most severe CRF
    primary_id, primary_ceiling, _ = triggered[0]

    # Compound additional CRFs
    compounding_factor = 0.5  # each additional CRF's weight is halved
    total_reduction = 0.0
    for _id, _ceil, weight in triggered[1:]:
        total_reduction += weight * compounding_factor

    # Apply compounding (floor at 5)
    final_ceiling = max(5, primary_ceiling * (1.0 - total_reduction))
    quality_score = min(composite_score, final_ceiling)

    return quality_score, primary_id, [...]
```

### FIX-02: Single DDL source for narrative
```python
def ddl_estimate(state: AnalysisState, decline_pct: float | None = None) -> float | None:
    """Get DDL from scoring stage settlement prediction (authoritative source).

    Falls back to rough estimate only when scoring result unavailable.
    """
    # Preferred: use scoring stage DDL
    if state.scoring is not None and state.scoring.severity_scenarios is not None:
        scenarios = state.scoring.severity_scenarios.scenarios
        if scenarios:
            # Use median scenario DDL
            ddl_amount = scenarios[1].ddl_amount if len(scenarios) > 1 else scenarios[0].ddl_amount
            if ddl_amount and ddl_amount > 0:
                return ddl_amount / 1e9  # Convert to billions

    # Also check analysis.settlement_prediction
    if state.analysis is not None:
        sp = getattr(state.analysis, "settlement_prediction", None)
        if isinstance(sp, dict) and sp.get("ddl_amount", 0) > 0:
            return sp["ddl_amount"] / 1e9

    # Fallback: rough estimate (original logic)
    mc = market_cap_billions(state)
    if mc is None:
        return None
    pct = decline_pct if decline_pct is not None else stock_decline_pct(state)
    if pct is None:
        return None
    return abs(mc * pct / 100)
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Flat CRF ceiling (30 for any SCA) | Size x severity matrix | AAPL goes from WALK to WANT/WRITE |
| "Most severe wins" ceiling | Weighted compounding | Multiple CRFs compound realistically |
| Binary Altman distress (fire/don't) | Graduated severity tiers | Gray zone vs distress vs going concern differentiated |
| Three independent DDL calculations | Single authoritative DDL from scoring | Scorecard and narrative agree |

## Calibration Ticker Selection

### Fixed Set (User Decision)
1. **HNGE** (Hinge Health) -- Recent IPO, health tech
2. **AAPL** (Apple) -- Mega-cap, 1 routine SCA, healthy financials
3. **ANGI** (Angi) -- Distressed micro-cap, 73.7% stock decline, multiple CRFs

### Recommended Additional 3 (Claude's Discretion)
4. **RPM** (RPM International) -- Mid-cap industrials, already has pipeline output, tests mid-range
5. **V** (Visa) -- Large-cap financial services, complex litigation (interchange MDL), tests non-SCA CRFs
6. **EXPONENT** (Exponent) -- Small-cap consulting, low-risk profile, should score WIN/WANT

Rationale: These 6 span mega/large/mid/small/micro caps, 5 sectors, and expected tiers from WIN to NO_TOUCH. RPM, V, and EXPONENT already have pipeline outputs in the `output/` directory, reducing calibration run time.

## Open Questions

1. **How to handle ANGI's likely false-positive CRFs?**
   - What we know: ANGI triggers 17/17 CRFs, many probably false positives from LLM extraction
   - What's unclear: Which are genuine vs false positives
   - Recommendation: During calibration, manually inspect ANGI CRF evidence. Fix false positive triggers as side-fixes, but design the weighted model to be robust even with noisy inputs.

2. **Should size-conditioned ceilings apply to ALL CRFs or only selected ones?**
   - What we know: User specified size conditioning for SCA (CRF-1) and distress (CRF-13)
   - What's unclear: Whether CRF-2 (Wells Notice), CRF-3 (DOJ), etc. should also vary by size
   - Recommendation: Apply size conditioning to CRF-1, CRF-8 (catastrophic decline), CRF-13. Keep flat ceilings for CRF-2, CRF-3, CRF-4, CRF-5 (these are categorical risks where size matters less).

3. **Tier boundary adjustment timing**
   - What we know: User deferred boundary adjustment until distribution is visible
   - What's unclear: Whether calibration will require boundary changes
   - Recommendation: Run calibration with current boundaries first, report distribution, then adjust only if scores cluster in 1-2 tiers.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via `uv run pytest`) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/stages/score/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCORE-01 | Size-conditioned CRF ceilings | unit | `uv run pytest tests/stages/score/test_crf_calibration.py::test_size_conditioned_ceilings -x` | Wave 0 |
| SCORE-02 | Multi-ticker baseline capture | integration | `uv run pytest tests/stages/score/test_crf_calibration.py::test_baseline_capture -x` | Wave 0 |
| SCORE-03 | AAPL vs ANGI different tiers | integration | `uv run pytest tests/stages/score/test_crf_calibration.py::test_aapl_angi_differentiation -x` | Wave 0 |
| SCORE-04 | Distribution uses 3+ tiers | integration | `uv run pytest tests/stages/score/test_crf_calibration.py::test_tier_distribution -x` | Wave 0 |
| FIX-02 | DDL consistency | unit | `uv run pytest tests/stages/score/test_crf_calibration.py::test_ddl_consistency -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/score/ -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/score/test_crf_calibration.py` -- covers SCORE-01 through SCORE-04, FIX-02
- [ ] `tests/stages/score/test_weighted_compounding.py` -- covers weighted CRF algorithm edge cases
- [ ] Framework install: None needed -- pytest already configured

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/config/scoring.json` -- current CRF ceilings, tier boundaries (read directly)
- `src/do_uw/stages/score/red_flag_gates.py` -- current ceiling application logic (read directly)
- `src/do_uw/stages/score/__init__.py` -- full scoring pipeline (read directly)
- `output/AAPL - Apple/2026-03-21/state.json` -- actual AAPL scoring output (read directly)
- `output/ANGI - Angi/2026-03-21/state.json` -- actual ANGI scoring output (read directly)

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/render/context_builders/ddl_context.py` -- render-time DDL calculation
- `src/do_uw/stages/score/settlement_prediction.py` -- score-time DDL calculation
- `src/do_uw/stages/score/severity_scoring.py` -- v7.0 severity model

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all modifications are to existing, well-understood modules
- Architecture: HIGH -- clear diagnosis from actual state.json, straightforward config extension
- Pitfalls: HIGH -- CRF normalization, dual config sources, false positive CRFs all observed in code
- Calibration approach: MEDIUM -- specific ceiling values will need tuning during implementation

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable -- this is internal scoring calibration, no external dependencies)
