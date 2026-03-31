# D&O Underwriting Worksheet System — How It Works

## What This System Does

Given a stock ticker (e.g. `AAPL`), the system runs a 7-stage pipeline and produces a comprehensive D&O liability underwriting worksheet. The primary output is a Word document, with HTML/PDF and Markdown as secondary outputs.

```
angry-dolphin analyze RPM --output output/
```

The pipeline takes ~5-15 minutes depending on data availability and LLM extraction load.

---

## The 7-Stage Pipeline

```
RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER
```

Every stage reads from and writes to a single `AnalysisState` Pydantic model — the only source of truth. State is persisted to `state.json` after each stage for resume support.

### Stage 1: RESOLVE (Ticker → Company Identity)

**Entry:** `stages/resolve/__init__.py` (197 lines)

Takes a ticker string and resolves it to a full company identity:

1. **Ticker → CIK**: Queries SEC's bulk `company_tickers.json` (10K+ filers)
2. **CIK → Full Identity**: SEC Submissions API → legal name, SIC code, exchange, state of incorporation, fiscal year end, FPI status, NAICS code
3. **yfinance Enrichment**: Market cap, employee count (MEDIUM confidence)
4. **Industry Playbook**: Matches SIC/NAICS to a playbook (e.g. `TECH_SAAS`, `BIOTECH_PHARMA`) for industry-specific signal injection

**Output:** `state.company: CompanyProfile` — CIK, legal name, SIC, exchange, market cap, employee count

### Stage 2: ACQUIRE (Gather All Raw Data)

**Entry:** `stages/acquire/orchestrator.py` (656 lines)

Five-phase data acquisition:

**Phase A — Pre-acquisition blind spot sweep** (~20% of search budget)
Runs 5 web searches BEFORE any structured data — catches things APIs miss:
- `"{company}" lawsuit investigation fraud`
- `"{company}" SEC subpoena Wells notice`
- `"{company}" short seller report Hindenburg Muddy Waters Citron`
- `"{company}" restatement whistleblower scandal`
- `"{company}" FDA warning CFPB OSHA`

**Phase B — Structured data acquisition** (4 clients):
1. **SEC Filing Client** — 10-K, 10-Q, DEF 14A, 8-K, Form 4, S-3, SC 13D/G. Also fetches XBRL Company Facts (~4MB structured financial data)
2. **Market Data Client** — yfinance: 1Y/5Y price history, insider transactions, institutional holders, analyst recommendations, sector ETF benchmarks
3. **Litigation Client** — Web search for SCA/enforcement/derivative suits + SEC EDGAR EFTS legal proceedings (10-year lookback)
4. **News Client** — Serper API for sentiment and news searches

**Phase B+ — Supplementals** (non-blocking):
- USPTO AI patent search
- Company favicon for HTML display
- Volume spike event correlation

**Phase C — Post-acquisition blind spot sweep** (remaining search budget)

**Phase D — Gate checking**: Validates hard requirements (annual report, proxy, market data). Retries once if missing.

**Phase E — Brain-driven gap search**: For signals that were previously SKIPPED due to missing data, runs targeted web searches.

**Output:** `state.acquired_data: AcquiredData` — raw filings, market data, litigation data, web search results, blind spot results

### Stage 3: EXTRACT (Parse Raw Data → Structured Facts)

**Entry:** `stages/extract/__init__.py` (384 lines)

13-phase extraction pipeline that transforms raw acquired data into structured Pydantic models:

| Phase | What it extracts | Key output |
|-------|-----------------|------------|
| 0a | Section-split 10-K into Items 1, 1A, 7, 8, etc. | Filing sections |
| 0b | LLM extraction (Claude) — parallel, cached | Structured fields from filings |
| 1 | Company profile from 10-K Item 1 + DEF 14A | Business description, subsidiaries, geographic footprint |
| 2 | Financial statements from XBRL | Income, balance sheet, cash flow (3+ years) |
| 3 | Distress indicators | Altman Z-Score, Beneish M-Score, Piotroski F-Score |
| 4 | Earnings quality | Accruals ratio, OCF/NI, revenue quality |
| 5 | Debt analysis | Liquidity ratios, leverage, debt structure, refinancing risk |
| 6 | Audit risk | Auditor name/tenure, opinion type, going concern, material weaknesses |
| 7 | Tax indicators | Effective rate, deferred tax, uncertain positions, tax havens |
| 8 | Peer group | Same SIC + similar market cap (or CLI override) |
| 9 | Financial narrative | Templated narrative from all financial data |
| 10 | Market extractors | Stock drops, short interest, insider trading, analyst coverage |
| 11 | Governance | Board composition, executives, compensation, ownership, forensics |
| 12 | Litigation | SCAs, SEC enforcement, derivative suits, regulatory proceedings |
| 13 | AI risk | Patents, AI job postings, management rhetoric, competitive positioning |

**Output:** `state.extracted: ExtractedData` — financials, market, governance, litigation, ai_risk, text_signals

### Stage 4: ANALYZE (Evaluate 400 Signals Against Extracted Data)

**Entry:** `stages/analyze/__init__.py` (511 lines)

The brain-driven analytical engine. This is where the 400 signals fire.

**Pre-ANALYZE — Two classification layers:**

- **Layer 1 (Classification)**: Market cap tier × industry sector × years public → base SCA filing rate from `brain/config/classification.json`
- **Layer 2 (Hazard Profile)**: Scores 47 dimensions across 5 domains → Inherent Exposure Score (IES, 0-100)

**Main signal execution:**

For each of the 400 signals:
1. **Data mapping** — routes signal to the right extracted data field by ID prefix (BIZ.*, FIN.*, STOCK.*, LIT.*, GOV.*, etc.)
2. **Content-type dispatch**:
   - `EVALUATIVE_CHECK` (267 signals) → threshold evaluation (numeric, boolean, tiered, temporal)
   - `MANAGEMENT_DISPLAY` (98 signals) → data presence check only, renders in worksheet
   - `INFERENCE_PATTERN` (19 signals) → multi-signal pattern detection
3. **Result** → TRIGGERED, CLEAR, INFO, or SKIPPED (with evidence and traceability)

**Additional analytical engines:**
- **Temporal analysis**: Detects DETERIORATING/IMPROVING/STABLE trends in financial metrics
- **Forensic composites**: Financial Integrity Score (FIS), Revenue Quality Score (RQS), Cash Flow Quality Score (CFQS)
- **Executive forensics**: Person-level risk scoring from board forensic profiles
- **NLP signals**: Readability, tone, risk factor categorization from 10-K text
- **Section density**: Pre-computes NORMAL/ELEVATED/CRITICAL density per section (drives alert banners in rendering)

**Telemetry**: Every signal result is written to `brain.duckdb` → `brain_signal_runs` table for the learning loop.

**Output:** `state.analysis: AnalysisResults` — 400 signal results, patterns detected, temporal signals, forensic composites, executive risk, section densities

### Stage 5: SCORE (10-Factor Risk Scoring)

**Entry:** `stages/score/__init__.py` (469 lines)

17-step scoring pipeline:

**The 10 factors:**

| Factor | Name | Max Points |
|--------|------|------------|
| F1 | Prior Litigation | 20 |
| F2 | Stock Decline | 15 |
| F3 | Restatement / Audit | 15 |
| F4 | IPO / SPAC / M&A | 10 |
| F5 | Guidance Misses | 10 |
| F6 | Short Interest | 10 |
| F7 | Volatility | 8 |
| F8 | Financial Distress | 7 |
| F9 | Governance | 3 |
| F10 | Officer Stability | 2 |

`quality_score = 100 - sum(points_deducted)` → mapped to tier:

| Tier | Score | Action |
|------|-------|--------|
| WIN | 86-100 | Must-have account, compete aggressively |
| WANT | 71-85 | Actively pursue |
| WRITE | 51-70 | Normal terms, conditions possible |
| WATCH | 31-50 | Write carefully, senior review |
| WALK | 11-30 | Excess/Side A only |
| NO_TOUCH | 0-10 | Decline |

**Critical Red Flag (CRF) ceilings** override the score — e.g., active SCA → max 30 (WALK), going concern → max 50 (WATCH).

**Additional scoring outputs:**
- 19 composite pattern detections (e.g. PATTERN.STOCK.EVENT_COLLAPSE)
- IES amplification of behavioral factors
- Risk type classification
- Allegation theory mapping
- DDL-based settlement prediction (median, P25, P75)
- Tower recommendation (attachment point + limits)
- 7-lens peril map

**Output:** `state.scoring: ScoringResult` — quality score, tier, factor breakdown, patterns, allegations, settlement prediction, tower recommendation

### Stage 6: BENCHMARK (Peer Comparison + Executive Summary)

**Entry:** `stages/benchmark/__init__.py` (358 lines)

1. **Peer rankings** — percentile ranks for key metrics against the peer group
2. **Relative position** — BEST_IN_CLASS through WORST_IN_CLASS
3. **Inherent risk baseline** — sector-adjusted filing rate × IES multiplier
4. **Executive summary** — builds the Section 1 snapshot: company identity, tier, key findings, underwriting thesis
5. **Pre-computed narratives** — LLM-generated prose for each section, stored for rendering (avoids re-generation)

**Output:** `state.benchmark`, `state.executive_summary`, `state.analysis.pre_computed_narratives`

### Stage 7: RENDER (Produce Documents)

**Entry:** `stages/render/__init__.py` (369 lines)

Produces all output files:
- `{TICKER}_worksheet.docx` — Word document (primary, always runs)
- `{TICKER}_worksheet.pdf` — PDF via Playwright Chromium (secondary, error-isolated)
- `{TICKER}_worksheet.md` — Markdown (secondary, error-isolated)
- `charts/*.png` — stock, radar, ownership, timeline charts
- `sources/` — all acquired filing texts, search results, manifest
- `state.json` — full analysis state

See `docs/RENDERING_PIPELINE.md` for the full rendering architecture.

---

## The Brain System

The "brain" is the knowledge system that drives analysis. It contains 400 signals organized across 36 YAML files, plus framework data and configuration.

### Signal YAML Files (Source of Truth)

**Location:** `src/do_uw/brain/signals/` — 36 files, ~548KB total

```
signals/
  biz/     — Business profile (BIZ.*)         4 files
  exec/    — Executive activity (EXEC.*)       2 files
  fin/     — Financial (FIN.*)                 5 files
  fwrd/    — Forward-looking (FWRD.*)          6 files
  gov/     — Governance (GOV.*)                7 files
  lit/     — Litigation (LIT.*)                6 files
  nlp/     — NLP analysis (NLP.*)              1 file
  stock/   — Market/trading (STOCK.*)          5 files
```

**Signal ID convention:** `{DOMAIN}.{CATEGORY}.{NAME}` — e.g. `FIN.ACCT.auditor`, `LIT.SCA.active_count`, `GOV.BOARD.independence_ratio`

**Each signal defines:**
- What data it needs (`required_data`, `data_locations`, `data_strategy.field_key`)
- How to evaluate it (`threshold` with type: tiered/boolean/numeric/percentage/temporal)
- What scoring factors it feeds into (`factors: [F1, F3]`)
- Where it appears in the worksheet (`worksheet_section`, `facet`)
- How to display results (`display: {value_format, source_type}`)

### BrainLoader (Unified Runtime Loader)

**File:** `brain/brain_unified_loader.py` (431 lines)

Reads YAML directly at runtime — DuckDB is NOT read for signal definitions. Module-level singleton caching means signals load once per process (~65ms via PyYAML CSafeLoader).

```python
from do_uw.brain.brain_unified_loader import load_signals, load_config
signals = load_signals()          # 400 signals from YAML
scoring = load_config("scoring")  # brain/config/scoring.json
```

### Brain DuckDB (History Only)

**File:** `src/do_uw/brain/brain.duckdb` (~370MB, gitignored)

21 tables. Used for signal run history, effectiveness tracking, feedback, changelog. Written to after every ANALYZE run as telemetry. Read by `brain audit`, `brain stats`, `brain trace`, `brain health` commands. The Phase 57 learning loop (calibration, correlation mining, lifecycle management) queries this data.

### Config JSON Files

**Location:** `src/do_uw/brain/config/` — 28 JSON files

Key configs: `scoring.json` (10-factor rules), `red_flags.json` (CRF gates), `patterns.json` (19 composite patterns), `classification.json` (Layer 1 base rates), `hazard_weights.json` (Layer 2 IES weights), `sectors.json` (sector baselines), `learning_config.json` (Phase 57 calibration thresholds).

---

## Caching

| Cache | File | Technology | Purpose | TTL |
|-------|------|------------|---------|-----|
| Analysis data | `.cache/analysis.db` | SQLite | SEC filings, market data, search results | 7d default (filing-specific overrides) |
| LLM extractions | `.cache/llm_extractions.db` | SQLite | Claude extraction results per filing | Indefinite (cleared with `--fresh`) |
| Brain telemetry | `brain/brain.duckdb` | DuckDB | Signal run history, effectiveness, feedback | Permanent |

---

## Data Source Fallback Chains

| Data Type | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|------------|------------|
| SEC Filings | SEC Submissions API | SEC EDGAR EFTS | Web search |
| Stock Data | yfinance | Yahoo Finance web | Web search |
| Litigation | Web search + EDGAR EFTS | 10-K Item 3 | - |
| News/Sentiment | Serper API | - | - |
| Financial Data | XBRL Company Facts | LLM extraction of 10-K | - |

Every data point carries `source` (filing type + date) and `confidence` (HIGH/MEDIUM/LOW). Missing data is "Not Available" — never guessed.

---

## CLI Commands

```bash
# Main pipeline
angry-dolphin analyze <TICKER> [--fresh] [--no-llm] [--peers AAPL,MSFT] [--search-budget 50]

# Brain management
angry-dolphin brain stats         # Signal counts, coverage, skip rates
angry-dolphin brain audit         # Flag dead/broken signals
angry-dolphin brain audit --calibrate   # + threshold drift + co-occurrence analysis
angry-dolphin brain audit --lifecycle   # + signal lifecycle transitions
angry-dolphin brain trace <SIG_ID>      # Evaluation history for a signal
angry-dolphin brain health        # Anomaly detection on fire rates

# Analyst feedback (drives learning loop)
angry-dolphin feedback            # Record agree/disagree with signal results

# Other
angry-dolphin calibrate           # Scoring calibration
angry-dolphin validate            # QA report on pipeline output
angry-dolphin dashboard           # Metrics dashboard
```

---

## Key Architectural Invariants

1. **Single state model** — `AnalysisState` is the only state representation
2. **Source + confidence on all data** — every `SourcedValue` carries provenance
3. **No hallucination** — missing data = "Not Available", never estimated
4. **No file over 500 lines** — split before it gets there
5. **Single location for logic** — scoring only in `stages/score/`, acquisition only in `stages/acquire/`
6. **Brain changes require provenance** — documented reason, evidence, expected impact
7. **Blind spot detection is first-class** — web search runs before AND after structured acquisition
8. **Graceful degradation** — every supplemental acquisition and analytical engine is wrapped so failures never crash the pipeline
