# OpenCode User Profile: Mike Gorlin

## Role & Experience
- **Head of underwriting** at GorlinBase MGA (Managing General Agent)
- **25 years** of commercial underwriting experience
- Technically hands-on: builds his own tools, skills, and systems
- Uses Claude Code, Claude Desktop, Obsidian, Supabase, GitHub (mikegorlin)

## Working Style
- Direct and concise communication preferred
- Types fast with typos (don't correct spelling)
- Don't ask for confirmation on low-risk, reversible things
- Short answers ("yes", "do it", "got it") = trust the direction
- No summarizing what just happened
- No repeating back what was said
- Lead with action, not explanation

## Key Systems
- **GitHub**: mikegorlin
- **Obsidian Vault**: GorlinVaultRemote (synced across devices)
- **Open Brain**: Supabase-based thought capture (MCP tools: capture_thought, search_thoughts)
- **Underwriting bench**: ~/projects/UW/OpenUnderwriter (angry-dolphin CLI — `analyze <TICKER>`)
- **MCP integrations**: Supabase, Open Brain

## D&O Underwriting Domain Knowledge
- **Project**: D&O Liability Underwriting System (Angry Dolphin Underwriting)
- **Input**: Stock ticker
- **Output**: Comprehensive risk assessment worksheet (HTML/Word/PDF)
- **Pipeline**: 7-stage pipeline: RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER
- **Data sources**: 100% publicly available data — SEC EDGAR filings, court records, governance data, financial metrics, news, web sources
- **Brain framework**: 400-check YAML brain framework for D&O risk signals
- **Scoring**: 10-factor scoring, red flags, peril-organized scoring
- **Benchmarking**: Industry peer comparisons

## Critical Project Rules (from CLAUDE.md)
1. **Brain Source of Truth**: YAML files are ONLY source of truth for brain signals, sections, configuration
2. **Narrative Quality**: Every sentence must contain company-specific data (dollar amounts, percentages, dates, names)
3. **Data Integrity**: Every data point MUST have `source` and `confidence` fields
4. **Data Source Priority**: XBRL/SEC filings ALWAYS primary, yfinance is FALLBACK
5. **IPO-Specific Treatment**: Mandatory for companies public < 5 years
6. **Root-Cause Problem Solving**: A patch is NEVER a solution
7. **Visual Quality**: NEVER make things look worse — match references pixel-for-pixel
8. **Self-Verification**: NEVER show output without verifying first
9. **Pipeline Execution Discipline**: Monitor pipeline to completion

## MCP Servers Configured
- `edgartools`: SEC EDGAR filings, XBRL data
- `context7`: Up-to-date library documentation
- `playwright`: Browser automation for scraping
- `fetch`: Simple URL content extraction
- `supabase`: GorlinBase D&O underwriting database
- `brave-search`: Web search (disabled - needs API key)
- `github`: Dev workflow (disabled - needs token)

## Supabase Database (GorlinBase)
- **URL**: https://jfqenpobwadlhuvseiax.supabase.co
- **Tables**: 4,275 accounts, 3,454 programs, pricing data, underwriting notes
- **Use case**: D&O pricing and underwriting database for GorlinBase MGA

## Project Architecture
- **Single source of truth**: `AnalysisState` Pydantic model
- **Cache**: DuckDB at `.cache/analysis.duckdb`
- **Config**: JSON files in `config/` (scoring weights, thresholds, patterns)
- **Knowledge**: Migrated from predecessor BRAIN/ directory
- **Testing**: 5,000+ tests, visual regression, performance budget

## Current Phase
- **Card Catalog Design System v4** (active as of 2026-03-29)
- 62 cards across 13 sections, modular card system
- Operating dashboard: `scripts/build_ops_dashboard.py` → `output/OPS_DASHBOARD.html`
- Card pipeline: Designed → Data Hooked & Verified → LLM Synthesis → QA Tested
- Status: Card frames applied to all 12 sections, internal card redesign in progress