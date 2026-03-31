# Underwriting 2.0 Codebase Review

## Comprehensive Analysis of the D&O Insurance Underwriting System

**Review Date:** 2026-02-06
**Codebase Location:** `/Users/gorlin/Desktop/Underwriting-2.0/`
**Version Claimed:** v6.1 (with v7 architecture planned/partially implemented)
**Total Files:** ~200+ (excluding caches)
**Total Python Code:** ~43,000 lines across 80 Python files in `tools/`

---

## 1. WHAT WAS BUILT

### 1.1 System Purpose

An AI-powered D&O (Directors & Officers) insurance underwriting analysis system. Given a company ticker, it acquires financial data from multiple sources, runs ~359 checks across 6 analysis sections, calculates a risk score on a 100-point scale, assigns a tier (WIN/WANT/WRITE/WATCH/WALK/NO TOUCH), and generates Word documents (referral worksheet and diagnostic report) for insurance underwriters.

### 1.2 Architecture Overview

The system has 4 conceptual layers:

```
BRAIN (Knowledge Layer)
  - 359 checks in 6 sections (JSON + CSV + Markdown)
  - 10-factor scoring model
  - 17 composite patterns
  - Sector baselines and adjustments

DATA ACQUISITION (Data Layer)
  - SEC EDGAR via MCP + EdgarTools
  - yfinance for stock/market data
  - Alpha Vantage (backup)
  - Brave Search for web/news/litigation
  - CourtListener for federal court data

ANALYSIS ENGINE (Agent Layer)
  - 9-agent pipeline (DATA -> 6 SECTION -> SCORING -> OUTPUT)
  - Check execution framework
  - Validation gates between stages
  - Schema validation for agent handoffs

OUTPUT RENDERER (Presentation Layer)
  - generate_referral.py (9,445 lines - monolithic)
  - REFERRAL.docx (polished worksheet)
  - DIAGNOSTIC.docx (internal, flags-first)
  - MEETING_PREP.docx (planned in v7)
  - Narrative generation module
  - Chart generation (TradingView/Plotly/matplotlib)
```

### 1.3 Module Inventory

| Module | Location | Lines | Purpose |
|--------|----------|-------|---------|
| orchestrator.py | tools/ | 1,620 | Pipeline coordinator, Anthropic SDK integration |
| generate_referral.py | tools/ | 9,445 | Word document generator (monolithic) |
| check_executor.py | tools/ | 4,115 | Individual check execution with state tracking |
| build_check_manifest.py | tools/ | 1,099 | Check manifest builder |
| build_analysis_json.py | tools/ | 1,065 | Analysis JSON assembler |
| stock_patterns.py | tools/ | 1,031 | 6 composite stock pattern detection |
| sec_data_acquisition.py | tools/ | 965 | SEC filing acquisition (DEPRECATED) |
| schema_validator.py | tools/ | ~400 | JSON schema validation |
| pipeline_validator.py | tools/ | ~400 | Stage-aware pipeline validation |
| stock_narrative.py | tools/ | 587 | Stock performance narrative |
| scienter_analysis.py | tools/ | 545 | Insider trading scienter analysis |
| pricing.py | tools/ | ~400 | D&O pricing model |
| learning_tracker.py | tools/ | ~400 | Continuous learning system |
| brain_advisor.py | tools/ | ~400 | Real-time brain improvement suggestions |
| narrative/ | tools/narrative/ | ~600 | Executive summary + prose generation |
| data_acquisition/ | tools/data_acquisition/ | ~1,500 | Unified data acquisition (v2) |

### 1.4 Data Sources

| Source | Integration Method | Status |
|--------|-------------------|--------|
| SEC EDGAR | MCP server (sec-edgar-mcp) + EdgarTools | Working, primary |
| yfinance | MCP server (yfmcp) + direct library | Working, primary |
| Alpha Vantage | MCP server (mcp-remote) | Working, backup |
| Brave Search | MCP server (@anthropic-ai/brave-search-mcp-server) | Configured |
| CourtListener | MCP server (mcp-remote to localhost) | Requires separate server |
| Polygon.io/Massive | MCP server (mcp-massive) | "EVALUATION ONLY" - 5 req/min |

### 1.5 Knowledge Assets (SYSTEM/ directory)

| File | Size | Purpose |
|------|------|---------|
| 00_MASTER_PROMPT.md | 16KB | Underwriter mindset |
| 00_PROJECT_INSTRUCTIONS.md | 40KB | Execution sequence |
| 03_SCORING_ENGINE.md | 56KB | Scoring model (legacy) |
| 05_OUTPUT_DIAGNOSTIC.md | 70KB | Diagnostic template |
| 07_LEARNING_ENGINE.md | 40KB | Sector baselines |
| 08_MULTI_AGENT_ARCHITECTURE.md | 33KB | Pipeline spec |
| BRAIN/BRAIN.md | 117KB | AUTHORITATIVE knowledge |
| BRAIN/checks.json | 198KB | 359 checks (machine-readable) |
| BRAIN/PATTERNS.md | 32KB | 17 composite patterns |
| 9 Agent Prompts | 15-62KB each | Section-specific prompts |
| 6 Section Check Files | 70-110KB each | Detailed checks (CHECKS/) |

---

## 2. WHAT WORKS

### 2.1 Domain Knowledge is Excellent

The underwriting knowledge captured in this system is genuinely impressive. The 359 checks across 6 sections represent deep D&O expertise:

- **Section 1 (Business):** 58 checks including 7 D&O risk type classifications (BINARY_EVENT, GROWTH_DARLING, etc.) with litigation rate data
- **Section 2 (Stock):** 35 checks including 6 composite patterns (EVENT_COLLAPSE, INFORMED_TRADING, etc.)
- **Section 3 (Financial):** 26 checks including CFRA earnings quality framework
- **Section 4 (Litigation):** 56 checks with Stanford SCAC integration
- **Section 5 (Governance):** 107 checks including ISS-style governance scoring
- **Section 6 (Forward Look):** 77 checks including narrative coherence analysis

The sector baselines (`config/sector_baselines.json`) and scoring weights (`config/scoring_weights.json`) show real actuarial thinking with empirical foundations cited (NERA 2024, Cornerstone 2024).

### 2.2 The Scoring Model is Well-Designed

The 10-factor scoring model with "Quality Score = 100 - Risk Points" is intuitively correct:

- Factor weights are empirically justified (F.1 Prior Litigation at 20 points has 3-5x litigation lift)
- The insider trading amplifier on F.2 is sophisticated -- treating insider selling as a scienter evidence multiplier rather than a standalone factor
- Critical Red Flag ceilings (CRF-001 through CRF-011) that cap the quality score regardless of other factors
- W-series tier boundaries with pricing multipliers and tower position guidance

### 2.3 The Brain Architecture is Sound

The `SYSTEM/BRAIN/` restructure (v7) shows mature thinking:

- Clean separation: RULES (how to behave) vs CHECKS (what to verify) vs SCORING (the math) vs PATTERNS (what to recognize)
- Machine-readable `checks.json` with 359 checks, data source mappings, and thresholds
- CSV-based check registry split into manageable chunks (001-100, 101-200, 201-300, 301-359)
- The EXTENDING.md guides for adding checks/patterns/sectors

### 2.4 Data Acquisition Design

The MCP integration is well-thought-out:

- 6 MCP servers configured in `.mcp.json` with clear hierarchy (primary/backup/evaluation)
- Data freshness rules (stock: 1hr, 10-K: 90 days, litigation: 1 day)
- Validation gates that BLOCK analysis if critical data is missing
- Identity resolution before data acquisition (resolves ticker to CIK, sector)

### 2.5 The LESSONS_LEARNED.md is Valuable

This document is remarkably honest about what failed and why. It identifies 5 major architectural pivots, documents specific failure patterns (Silent Data Loss, Schema Drift, Implicit Assumptions in Prose), and provides concrete rebuild requirements. This kind of meta-learning document is rare and valuable.

### 2.6 Real Output Was Generated

The OUTPUTS/ directory contains analysis for ~25 companies (AAPL, AMZN, BA, CAT, CRM, CVX, DIS, GOOGL, GS, HD, JNJ, JPM, META, MSFT, NFLX, NVDA, PFE, SMCI, TSLA, UNH, WMT, XOM). The AAPL scoring result shows a well-structured JSON with detailed escalation triggers, evidence citations, and nuanced analysis (correctly identifying DOJ civil antitrust lawsuit as NOT a criminal investigation).

### 2.7 The Anti-Context-Rot Architecture

`SYSTEM/ANTI_CONTEXT_ROT.md` shows deep understanding of the core problem and proposes 7 good principles:
1. Explicit checklists, not implicit memory
2. Data-before-analysis gates
3. Chunked processing with verification
4. State files, not memory
5. Verification checkpoints
6. Re-anchoring instructions
7. Explicit "no shortcut" rules

---

## 3. WHAT IS BROKEN OR PROBLEMATIC

### 3.1 The Monolithic generate_referral.py (CRITICAL)

At 9,445 lines and 408KB, this is the most problematic file in the codebase. It:

- Hardcodes ALL document generation logic (styles, formatting, content, layout)
- Has grown through accretion rather than design
- Mixes concerns: data extraction, formatting, styling, narrative generation, chart embedding, field tracking
- Contains deprecated code paths (Phase 39 CheckExecutor references alongside agent-based checks)
- Is fragile -- any change risks breaking the entire document generation pipeline

This was explicitly identified in LESSONS_LEARNED.md as a problem: "270KB generate_referral.py hardcodes all document logic."

### 3.2 Subagents Cannot Access MCP Tools (FUNDAMENTAL LIMITATION)

The entire multi-agent architecture was designed around parallel execution of 6 section agents, but:

- **Background subagents CANNOT access MCP tools** (confirmed bug in Claude Code as of Feb 2026)
- **Foreground subagents block the main conversation**
- This means the parallel execution benefit is either non-functional or requires all data to be pre-acquired

The TECHNICAL_CONSTRAINTS.md documents this clearly, but the orchestrator.py still contains code that would attempt to use MCP tools from subagents.

### 3.3 Dual/Triple Data Acquisition Paths

There are at least 3 generations of data acquisition code:

1. **Original (DEPRECATED):** `sec_data_acquisition.py`, `market_data_acquisition.py`, `search_data_acquisition.py`, `full_data_acquisition.py`
2. **v2 (tools/data_acquisition/):** `orchestrator.py`, `acquirers/sec_acquirer.py`, `acquirers/market_acquirer.py`, etc.
3. **MCP-based:** Direct MCP tool calls from main conversation

All three generations still exist in the codebase. The deprecated files have deprecation headers but are still imported by `full_data_acquisition.py`. The v2 orchestrator imports from acquirers that may or may not work.

### 3.4 Check Count Inconsistencies

Different parts of the system claim different check counts:
- CLAUDE.md: "~425 deep checks" (v6.0), "337 total" (in orchestrator validation)
- BRAIN README: "359 CHECKS in 4 CSV files"
- checks.json: 359 checks (confirmed by "id" count)
- Orchestrator validate_check_results(): expects 337, uses 320 as threshold
- /uw:analyze command: "ALL 359 checks", expects 300 minimum
- ANTI_CONTEXT_ROT.md: references "359 checks" consistently

The orchestrator hardcodes `expected_checks=320` and `total=337` while the actual check count is 359. This means the validation thresholds are miscalibrated.

### 3.5 Scoring Model Inconsistencies Across Files

The 10-factor model has different factor definitions depending on which file you read:

**In orchestrator.py (lines 806-815):**
- F.5 = Guidance Misses (max 8)
- F.6 = Short Interest (max 8)
- F.7 = Insider Trading (max 8)
- F.8 = Volatility (max 7)
- F.9 = Financial Distress (max 6)
- F.10 = Governance (max 3)

**In BRAIN/SCORING/SCORING.md:**
- F.5 = Guidance Misses (max 10)
- F.6 = Short Interest (max 8)
- F.7 = Volatility (max 9)
- F.8 = Financial Distress (max 8)
- F.9 = Governance (max 6)
- F.10 = Officer Stability (max 2)

**In config/scoring_weights.json:**
- F.4 = IPO/SPAC/M&A (max 10)
- F.5 = Guidance Misses (max 10) -- but named "F5_guidance_misses"
- F.7 = "F7_insider_trading" (max 9) -- called "Insider Trading" not "Volatility"
- F.8 = Volatility (max 8)
- F.9 = Financial Distress (max 6)
- F.10 = Governance (max 2)

The SCORING.md says F.7 is "Volatility" but the config JSON names it "insider_trading". The orchestrator says F.7 is "Insider Trading" (max 8) but SCORING.md says "Volatility" (max 9). This is a significant source of confusion.

### 3.6 Directory Name Bugs

Two directories in the project root are literally named `--diagnostic-only` and `--output-dir`:
```
drwxr-xr-x  10 gorlin  staff  320 Feb  2 15:09 --diagnostic-only
drwxr-xr-x   6 gorlin  staff  192 Feb  2 18:01 --output-dir
```
These were clearly created when CLI flags were passed incorrectly (e.g., `python orchestrator.py AAPL --output-dir` created a directory named `--output-dir` instead of using it as a flag). This indicates the argument parsing had bugs that created garbage output directories.

### 3.7 Excessive AAPL Test Outputs

The OUTPUTS/AAPL_2026-02-02/ directory contains 91 files, including ~30+ DIAGNOSTIC files generated within minutes of each other (1112, 1118, 1121, 1124, 1128, 1130, 1133...). This suggests extensive trial-and-error debugging rather than systematic testing. There are also multiple test directories:
- AAPL_test_complete
- AAPL_test_complete2
- AAPL_final_test
- AAPL_final_complete
- AAPL_complete_test
- AAPL_test_full
- AAPL_FULL_PHASE39
- AAPL_TEST_PHASE39
- AAPL_REAL_TEST

This is 9 test/debugging directories for a single ticker.

---

## 4. EVIDENCE OF CONTEXT ROT

### 4.1 Multiple Generations of the Same System Coexisting

This is the strongest evidence of context rot. The codebase contains:

1. **Three data acquisition systems:** Original standalone scripts, v2 `data_acquisition/` package, and MCP-based acquisition
2. **Two check execution systems:** CheckExecutor (deprecated Phase 39) and agent-based evaluation
3. **Multiple scoring definitions:** `03_SCORING_ENGINE.md` (56KB, legacy), `BRAIN/SCORING/SCORING.md` (authoritative), `config/scoring_weights.json` (programmatic), and inline in `orchestrator.py`
4. **Two output template systems:** `04_OUTPUT_WORKSHEET.md` / `05_OUTPUT_DIAGNOSTIC.md` (original) and `WORKSHEET_SPECIFICATION.md` (v7)
5. **Two check registries:** `config/check_registry.json` (old) and `BRAIN/checks.json` (new)

Each generation was built when the AI lost context about the previous one, creating parallel systems that partially overlap but are not fully compatible.

### 4.2 The v6.0/v6.1/v7 Version Confusion

The system simultaneously claims to be:
- v6.1 (CLAUDE.md, README.md, orchestrator.py header)
- v7 (BRAIN/ structure, ANTI_CONTEXT_ROT.md, /uw:analyze command, ARCHITECTURE_V7.md)
- Has LESSONS_LEARNED.md planning for v7.0 rebuild

The v7 architecture was designed but only partially implemented. BRAIN/ has v7 structure but the orchestrator still runs v6.1 logic. The `/uw:analyze` command references v7 with "No Blind Spots" but the actual execution path still goes through v6.1 orchestrator.

### 4.3 Abandoned Feature Indicators

Several files were clearly started and abandoned mid-development:

- **tools/calibration_tracker.py** (580 lines): Continuous calibration system, never connected to main pipeline
- **tools/brain_advisor.py** (~400 lines): Real-time improvement suggestions, never integrated
- **tools/learning_tracker.py** (~400 lines): Learning from analysis outcomes, `learning_log.json` has only a skeleton
- **tools/price_analysis.py** / **tools/pricing.py**: Two separate pricing modules that overlap
- **tools/meeting_prep_generator.py**: Referenced but only partially integrated into generate_referral.py
- **LEARNING_AND_CALIBRATION_SYSTEMS.md** (68KB): Massive research document about calibration systems that was never implemented
- **RESEARCH_AI_DOCUMENT_ANALYSIS_PATTERNS.md** (29KB): Research document that informed design but sits as dead weight

### 4.4 Phase Numbering Drift

References to "Phase 39", "Phase 33", "Phase 15-03a", "Phase 13.3 audit" appear throughout the code. The comment in generate_referral.py references "Phase 15-03a" critical field validation alongside "Phase 39" deprecated code. This phase numbering is evidence of an AI agent that tracked progress through numbered phases but lost continuity between them.

### 4.5 Contradictory Instructions

- CLAUDE.md says "Use MCP tools first" but LESSONS_LEARNED says "Subagents via Task tool cannot access MCP tools"
- The orchestrator still has CheckExecutor import logic with 6 levels of try/except fallback despite it being "deprecated"
- README says "parallel execution (3x faster)" but TECHNICAL_CONSTRAINTS says parallel subagents cannot access MCP
- The /uw:analyze command says to spawn Task agents but also says "CRITICAL: You are a Task-spawned subagent. You CANNOT access MCP tools"

### 4.6 Repeated Import Safety Patterns

Nearly every tool file has this pattern:
```python
try:
    from module import Class
    MODULE_AVAILABLE = True
except ImportError:
    try:
        from tools.module import Class
        MODULE_AVAILABLE = True
    except ImportError:
        MODULE_AVAILABLE = False
        print("Warning: module not available")
```

The orchestrator.py has 7 such blocks (lines 43-129). This defensive import pattern exists because the code was written across multiple sessions where the import context changed.

---

## 5. ARCHITECTURE ISSUES

### 5.1 No Single Execution Path

The system has multiple ways to run an analysis:
1. `python tools/orchestrator.py TICKER` (SDK mode with Anthropic API)
2. `python tools/orchestrator.py TICKER --manual` (prompt generation mode)
3. `/uw:analyze TICKER` (Claude Code slash command)
4. Interactive: "Analyze TICKER" in Claude conversation
5. `python -m tools.data_acquisition.orchestrator TICKER` (data only)
6. `python tools/full_data_acquisition.py TICKER` (deprecated data only)

These paths do not converge on a single execution flow. The orchestrator's SDK mode runs agents via Anthropic API, while the /uw:analyze command spawns them as Claude Code Tasks. Different paths produce different results.

### 5.2 State Management is Fragmented

State lives in:
- `AGENT_OUTPUTS/state.json` (pipeline state)
- `analysis.json` (final output)
- `master_data_manifest.json` (data acquisition state)
- `gate_validation_report.json` (gate state)
- `check_tracker.json` (check execution state -- v7)
- `check_progress.json` (referenced in ANTI_CONTEXT_ROT.md but may not exist)
- Individual `section{N}_findings.json` files

There is no unified state management. Each component writes its own state file.

### 5.3 The `tools/` Directory is Flat and Overloaded

80 Python files in a flat directory with no subpackaging beyond `narrative/` and `data_acquisition/`. This includes:
- Core pipeline code (orchestrator, generate_referral)
- Data acquisition (5+ deprecated files + new package)
- Validation (4+ validators)
- Testing (8+ test files)
- Analysis helpers (stock_patterns, scienter_analysis, financial_helpers)
- QA tools (qa_suite, qa_batch_tester, run_qa_suite)
- Management tools (check_manager, manifest_generator)
- Learning/calibration (learning_tracker, calibration_tracker, brain_advisor)
- Schema utilities (schema_validator, schema_transformer)
- Samples and examples

### 5.4 No Dependency Management

`requirements.txt` is minimal:
```
python-docx
yfinance
pandas
matplotlib
beautifulsoup4
requests
anthropic
edgartools
jsonschema
referencing
tqdm
```

No version pinning, no separation between core and optional dependencies, no dev dependencies.

---

## 6. DATA SOURCES ANALYSIS

### 6.1 SEC EDGAR (Primary -- Works Well)

Two integration paths:
1. **MCP sec-edgar server:** Uses `sec-edgar-mcp` package, provides structured access to 10-K, 10-Q, 8-K, DEF 14A, Form 4, financial statements
2. **EdgarTools library:** Direct Python access, used as fallback

The SEC data acquisition is the most mature part of the system. The MCP server handles rate limiting and provides full content.

### 6.2 yfinance (Primary Market Data -- Works Well)

Provides: 5-year price history, current quotes, fundamentals, institutional holders, analyst recommendations. No API key needed.

The `stock_narrative.py` module calculates volatility metrics (beta, annual vol, max drawdown, Sharpe ratio) directly from yfinance data.

### 6.3 Alpha Vantage (Backup -- Limited)

Free tier: 25 requests/day, 5 requests/min. Used for technical indicators and features yfinance does not provide. Limited by rate constraints.

### 6.4 Brave Search (Web/News -- Configured)

Free tier: 2,000 requests/month. Used for litigation searches (Stanford SCAC), news, regulatory actions. Integration quality depends on search result parsing.

### 6.5 CourtListener (Federal Courts -- Requires Setup)

Requires running a separate MCP server locally (`python -m app` on localhost:8000). Free tier: 100/day unauthenticated. Not integrated into the automated pipeline.

### 6.6 Polygon.io/Massive (EVALUATION ONLY)

Explicitly marked as not for production use (5 requests/minute). Should probably be removed from configuration.

---

## 7. OUTPUT QUALITY ANALYSIS

### 7.1 Referral Document (WORKSHEET)

The REFERRAL.docx is the polished, client-facing document. Based on the Liberty Mutual referral template. At ~217KB per document, it is comprehensive. The generate_referral.py includes:

- Executive summary with verdict-first structure
- Company snapshot with D&O risk classification
- Stock performance with chart generation
- Financial analysis with CFRA earnings quality
- Litigation history with Stanford SCAC search results
- Governance analysis with ISS-style scoring
- Forward look with prospective triggers
- 10-factor scoring breakdown
- Recommendation with tier assignment

### 7.2 Diagnostic Document (FLAGS-FIRST)

The DIAGNOSTIC.docx is the internal working document. Organized by flags/concerns first, then detailed analysis. Should contain ALL 359 check results but this is where the "check_results[]" pipeline often fails.

### 7.3 Known Output Problems

From LESSONS_LEARNED.md:
- "REFERRAL worked (99.5% pass), DIAGNOSTIC broken (empty)" -- dual code paths
- "54% data loss" on critical fields (Forward Look at 80% loss rate)
- generate_referral.py tracks N/A rate -- high N/A rates indicate data not flowing through
- Section 6 (Forward Look) consistently had the worst data population

### 7.4 The Narrative Quality Module

The `tools/narrative/` module includes quality checks that scan for robotic language, verify D&O context is present, and score narrative quality 0-100. This is a good quality control mechanism.

---

## 8. PATTERNS TO AVOID IN REBUILD

### 8.1 DO NOT: Let the Document Generator Become the System

`generate_referral.py` at 9,445 lines is the single biggest technical debt item. The document template, styling, content extraction, narrative generation, and formatting are all in one file. In a rebuild: separate template definition, data extraction, formatting, and rendering.

### 8.2 DO NOT: Build Parallel Systems Instead of Fixing One

The codebase has 3 data acquisition systems, 2 check execution systems, 3 scoring definition locations, and 2 check registries. Each was built when the previous one "didn't work" but the previous one was never removed. In a rebuild: one system, one source of truth, deprecate aggressively.

### 8.3 DO NOT: Use Implicit Check Execution

Asking an LLM to "evaluate all 359 checks" in a single prompt produces 5-10% coverage. The v7 architecture correctly identifies this: chunk into batches of 20, verify after each batch, persist state.

### 8.4 DO NOT: Ignore the MCP Subagent Limitation

The fundamental constraint -- background subagents cannot access MCP tools -- must be designed around, not ignored. All MCP-dependent data acquisition must happen in the main conversation before spawning subagents.

### 8.5 DO NOT: Allow Multiple Sources of Truth for Scoring

Having the scoring model defined in 4 different files (03_SCORING_ENGINE.md, BRAIN/SCORING/SCORING.md, config/scoring_weights.json, orchestrator.py) with DIFFERENT values is a recipe for bugs. One file should be authoritative and all others should read from it.

### 8.6 DO NOT: Store Test Outputs in the Same Directory as Production

9 test/debug directories for AAPL, plus stress test directories, plus batch test directories -- all mixed in with actual analysis outputs. Test outputs should be in a separate directory.

---

## 9. PATTERNS TO CARRY FORWARD

### 9.1 The Domain Knowledge Structure

The 359 checks across 6 sections, with sector-specific suffixes (-BIOT, -TECH, -FINS), value dimensions (LEVEL, TREND, PEER, TIMING, COHERENCE), and composite patterns represent months of insurance underwriting expertise. This is the most valuable asset.

### 9.2 The 10-Factor Scoring Model

The factor weights, empirical foundations, insider trading amplifier, and critical red flag ceilings are well-calibrated. The tier boundaries with pricing multipliers and tower position guidance are production-ready.

### 9.3 The MCP Tool Integration Pattern

Using MCP servers for data acquisition with a clear priority hierarchy (SEC EDGAR primary, yfinance for market, web search as last resort) is the right approach.

### 9.4 The Gate-Based Validation

The concept of blocking gates (GATE_1 through GATE_6) that prevent analysis from starting without complete data is essential. This should be carried forward and strengthened.

### 9.5 The Anti-Context-Rot Principles

The 7 principles in ANTI_CONTEXT_ROT.md are correct:
1. Explicit checklists, not implicit memory
2. Data-before-analysis gates
3. Chunked processing with verification
4. State files, not memory
5. Verification checkpoints
6. Re-anchoring instructions
7. Explicit "no shortcut" rules

### 9.6 The LESSONS_LEARNED.md

The meta-learning document itself is a pattern to carry forward. It honestly documents what went wrong and why.

### 9.7 The checks.json Machine-Readable Format

The v7 `BRAIN/checks.json` with 359 checks, data source mappings, thresholds, and sector adjustments in a structured JSON format is the right approach for machine execution.

---

## 10. SPECIFIC FILE-BY-FILE RECOMMENDATIONS

### Files to Keep (Carry Forward)

| File | Reason |
|------|--------|
| `SYSTEM/BRAIN/checks.json` | 359 checks, machine-readable, authoritative |
| `SYSTEM/BRAIN/SCORING/SCORING.md` | Authoritative scoring model |
| `SYSTEM/BRAIN/PATTERNS.md` | 17 composite patterns |
| `SYSTEM/BRAIN/RULES/*.md` | Behavioral guidance |
| `SYSTEM/BRAIN/CHECKS/*.csv` | Check definitions |
| `config/scoring_weights.json` | Programmatic scoring (AFTER fixing inconsistencies) |
| `config/tier_boundaries.json` | Tier definitions |
| `config/sector_baselines.json` | Sector context |
| `config/critical_red_flags.json` | Escalation triggers |
| `.mcp.json` | MCP server configuration |
| `tools/narrative/` | Narrative quality module |
| `tools/stock_patterns.py` | Pattern detection logic |
| `tools/scienter_analysis.py` | Scienter analysis |
| `tools/pricing.py` | Pricing model |
| `LESSONS_LEARNED.md` | Meta-learning |
| `.planning/TECHNICAL_CONSTRAINTS.md` | Platform limitations |
| `.planning/ARCHITECTURE_V7.md` | Design reference |
| `SYSTEM/ANTI_CONTEXT_ROT.md` | Architecture principles |

### Files to Delete (Dead Weight)

| File | Reason |
|------|--------|
| `tools/sec_data_acquisition.py` | Deprecated, replaced by data_acquisition/ |
| `tools/market_data_acquisition.py` | Deprecated, replaced by data_acquisition/ |
| `tools/search_data_acquisition.py` | Deprecated, replaced by data_acquisition/ |
| `tools/full_data_acquisition.py` | Deprecated, replaced by data_acquisition/ |
| `tools/data_acquisition_gate.py` | Deprecated, replaced by data_acquisition/validation_gate.py |
| `tools/test_acquisition_gate.py` | Tests deprecated module |
| `tools/test_cat.py` | Ticker-specific test (deprecated) |
| `tools/test_smci.py` | Ticker-specific test (deprecated) |
| `tools/test_meta.py` | Ticker-specific test (deprecated) |
| `tools/qa_batch_tester.py` | Deprecated |
| `tools/run_qa_suite.py` | Deprecated |
| `--diagnostic-only/` | Garbage directory from CLI bug |
| `--output-dir/` | Garbage directory from CLI bug |
| `LEARNING_AND_CALIBRATION_SYSTEMS.md` | 68KB research doc, never implemented |
| `RESEARCH_AI_DOCUMENT_ANALYSIS_PATTERNS.md` | 29KB research doc, informational only |
| `SYSTEM/03_SCORING_ENGINE.md` | Legacy, superseded by BRAIN/SCORING/SCORING.md |
| `.claude/commands/uw/analyze-e2e.md` | Deprecated command |
| All `OUTPUTS/*_test*` directories | Test debris |
| All `OUTPUTS/STRESS_TEST_*` directories | Test debris |

### Files to Rewrite

| File | Reason |
|------|--------|
| `tools/generate_referral.py` | Must be decomposed: template engine + template definitions + data extraction |
| `tools/orchestrator.py` | Needs cleanup: remove deprecated CheckExecutor code, fix check count, fix scoring model references |
| `CLAUDE.md` | Update to reflect actual v7 state, remove contradictory MCP instructions |
| `README.md` | Consolidate version claims, remove outdated quick-start paths |

---

## 11. QUANTITATIVE SUMMARY

| Metric | Value |
|--------|-------|
| Total Python files (tools/) | 80 |
| Total Python lines (tools/) | 43,254 |
| Largest single file | generate_referral.py (9,445 lines, 408KB) |
| Deprecated files still present | 14 |
| Check count (actual) | 359 |
| Check count (claimed in different places) | 337, 359, 425 |
| Scoring model definitions | 4 locations (inconsistent) |
| Data acquisition systems | 3 generations |
| Agent prompts | 9 + 2 MCP acquisition docs |
| MCP servers configured | 6 |
| Companies analyzed (OUTPUTS/) | ~25 unique tickers |
| Test/debug output directories | ~15 |
| Markdown documentation files (SYSTEM/) | 20+ |
| Total SYSTEM/ knowledge | ~1.5MB of domain expertise |
| Total project size (excluding venv/git) | ~50MB |

---

## 12. CONCLUSION

### What This System Actually Is

This is a knowledge framework masquerading as a software system. The true value is in the 359 checks, the scoring model, the sector baselines, the composite patterns, and the domain expertise encoded in the BRAIN/ directory. The Python code is the scaffolding that tries to operationalize this knowledge through Claude, with varying degrees of success.

### The Core Problem

The system was built iteratively by an AI that lost context repeatedly (hence "Underwriting 2.0" with 5 major architectural pivots across 99+ phases). Each session produced new code without fully understanding or cleaning up the previous session's code. The result is a codebase with excellent domain knowledge but fragmented execution paths, duplicated systems, and contradictory configurations.

### The Path Forward

1. **Treat the BRAIN/ directory as the primary asset** -- the knowledge is production-ready
2. **Build a clean execution layer from scratch** -- do not try to fix the existing Python code
3. **One source of truth for everything** -- one scoring model file, one check registry, one data acquisition path, one document template system
4. **Design around the MCP limitation** -- all data acquisition in main conversation, subagents work from pre-acquired data files
5. **Decompose generate_referral.py** -- template engine + templates + data extraction as separate concerns
6. **Delete deprecated code aggressively** -- 14 deprecated files are noise
7. **Separate test outputs from production** -- clean the OUTPUTS/ directory

The domain knowledge in this system would take weeks to recreate from scratch. The Python code could be rewritten in days. Prioritize preserving the former while replacing the latter.

---

*Review completed 2026-02-06 by Claude Opus 4.6*
