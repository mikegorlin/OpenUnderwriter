# Phase 121: Scoring Calibration - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Recalibrate CRF ceilings and tier thresholds so that companies with fundamentally different risk profiles produce meaningfully different tiers. AAPL (healthy mega-cap with 1 routine SCA) and ANGI (distressed micro-cap with 73.7% decline) must NOT both be WALK.

</domain>

<decisions>
## Implementation Decisions

### CRF Ceiling Logic
- **Combine company size AND severity** — ceiling is a matrix, not a single number
  - Mega-cap (>$100B) + 1 SCA = ceiling ~70 (WANT range)
  - Micro-cap (<$2B) + 1 SCA = ceiling ~30 (WALK range)
  - Any size + restatement + SCA = ceiling ~30 (WALK)
  - Specific matrix values TBD during calibration — these are starting points
- **Distress ceiling depends on distress severity**
  - Altman < 1.0 with negative equity = ceiling 20
  - Altman 1.0-1.8 (gray zone) = ceiling 40
  - Going concern opinion = ceiling 15
- **Multiple CRFs use weighted compounding** — each CRF has a severity weight, sum of weights maps to final ceiling. More triggered CRFs = lower ceiling. Not just "most severe wins."

### Tier Boundaries
- **Keep 6 tiers**: WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH — each maps to specific underwriting action (tower position, coverage type, attachment point)
- **Current ranges may need adjustment** but decision deferred until we see the score distribution across 6+ tickers
- **Run distribution analysis first**, then adjust boundaries based on where scores cluster

### Calibration Methodology
- **6 ticker calibration set**: HNGE, AAPL, ANGI + 3 Claude-selected for maximum diversity (different sectors, market caps, risk profiles)
- **Success criteria**: User assigns expected tier per ticker (expert judgment), AND distribution uses 3+ distinct tiers. If they conflict, user judgment wins.
- **Multi-ticker baseline**: capture before AND after for every calibration change
- **DDL discrepancy fix** (FIX-02) included — scorecard DDL must match narrative DDL

### Claude's Discretion
- Exact CRF severity weights for the weighted compound model
- Which 3 additional tickers to select for diversity
- Implementation approach for size-conditioned ceilings (config-driven vs code-driven)
- Tier boundary adjustment values (if distribution analysis reveals clustering)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scoring Architecture
- `src/do_uw/brain/config/scoring.json` — CRF ceiling definitions, tier boundaries, factor weights
- `src/do_uw/stages/score/red_flag_gates.py` — CRF evaluation + ceiling application logic
- `src/do_uw/stages/score/tier_classification.py` — Tier classification from quality score
- `src/do_uw/stages/score/__init__.py` — Score orchestration (step ordering, ceiling application)

### Scoring Models
- `src/do_uw/stages/score/severity_model.py` — FlaggedItem creation from CRF results
- `src/do_uw/stages/score/hae_crf.py` — Phase 26 CRF gates (CRF-12 through CRF-17)
- `src/do_uw/stages/score/severity_scoring.py` — Settlement/DDL calculations

### Data Sources
- `src/do_uw/stages/render/sections/sect1_findings_data.py` — DDL estimate function (needs fix)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scoring.json` CRF config: already has per-CRF `max_quality_score` — can extend with size/severity conditioning
- `apply_crf_ceilings()` in `red_flag_gates.py`: already iterates CRFs and finds lowest ceiling — can be extended with weighting
- `classify_tier()` in `tier_classification.py`: reads tier boundaries from config — boundary changes are config-only

### Established Patterns
- CRF gates return `RedFlagResult` with `triggered`, `ceiling_applied`, `evidence`
- Scoring config is JSON-driven — no hardcoded values in Python
- Tier classification is pure config lookup — no scoring logic in the classifier

### Integration Points
- `__init__.py` Step 1 calls `evaluate_red_flag_gates()` → Step 3 calls `apply_crf_ceilings()` → Step 5 calls `classify_tier()`
- DDL estimate in `sect1_findings_data.py` needs to match scorecard DDL from `ddl_context.py`

</code_context>

<specifics>
## Specific Ideas

- Tiers are underwriting action prescriptions: WIN = primary full tower, WANT = primary/low excess, WRITE = mid-excess with conditions, WATCH = high excess restricted, WALK = Side A only high attachment, NO_TOUCH = decline
- The philosophy is about tower position and coverage type, not just binary accept/decline
- A $3.6T company with 1 routine SCA should still be writable (WRITE or better), not WALK

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 121-scoring-calibration*
*Context gathered: 2026-03-21*
