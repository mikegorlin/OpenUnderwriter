# D&O Underwriting System: MCP Servers, Plugins, Libraries & Anti-Context-Rot Setup

**Research Date:** 2026-02-07
**Target Project:** D&O Liability Underwriting Worksheet System (Python 3.12, CLI)
**Predecessor:** Underwriting-2.0 (43,000 lines, 99+ phases, 5 architectural pivots -- failed due to context rot)
**Builds on:** `MCP_AND_PLUGINS_COMPREHENSIVE_RESEARCH.md`, `UNDERWRITING_2_REVIEW.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/STACK.md`, `.planning/research/PITFALLS.md`

---

## TABLE OF CONTENTS

1. [MCP Servers -- Project-Specific Recommendations](#1-mcp-servers)
2. [Claude Code Plugins & Hooks for Code Quality](#2-claude-code-plugins--hooks)
3. [Python Libraries -- What We Need and Why](#3-python-libraries)
4. [Anti-Context-Rot Architecture Patterns](#4-anti-context-rot-architecture)
5. [Complete Installation Script](#5-complete-installation-script)
6. [Sources](#6-sources)

---

## 1. MCP SERVERS

### 1.1 EdgarTools MCP Server -- MUST HAVE

**What it does:** Provides Claude with direct access to SEC EDGAR filings, XBRL financial data, insider trading (Form 4), proxy statements (DEF 14A), and all other SEC form types. Built-in financial statement parsing converts filings to pandas DataFrames. The MCP server exposes 3,450+ lines of API documentation, code examples, and form type reference to Claude.

**Why we need it:** This is the single most important data source for the project. Requirements DATA-01, SECT2, SECT3, SECT4-04, SECT5, and SECT6 all depend on SEC EDGAR data. EdgarTools handles XBRL taxonomy normalization (mapping `us-gaap:Revenues` vs `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` to a common element), built-in rate limiting (respects SEC's 10 req/sec), and financial statement stitching across multiple filings.

**Package:** `edgartools` (pip) -- latest stable: v5.14.0+ (Feb 2026)

**Install:**
```bash
pip install edgartools

# Add as MCP server
claude mcp add edgartools -- python -m edgar.ai

# Or with explicit JSON config:
claude mcp add-json edgartools '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "edgar.ai"],
  "env": {"EDGAR_IDENTITY": "Your Name your.email@example.com"}
}'
```

**Known limitations:**
- Requires `EDGAR_IDENTITY` environment variable (SEC mandates User-Agent identification)
- XBRL parsing handles standard taxonomies well but custom extensions may need manual mapping
- Rate limited to 10 req/sec (this is SEC's limit, not edgartools')
- Very large filings (100+ pages) can be slow to parse
- MCP server is Python-based (uses stdio transport, not HTTP)

**Predecessor lesson:** Underwriting-2.0 used both edgartools AND a separate sec-edgar-mcp package, creating dual data paths. Use edgartools as the SINGLE SEC data interface.

---

### 1.2 Yahoo Finance MCP Server -- MUST HAVE

**What it does:** Provides stock price history, fundamental ratios, company info, analyst recommendations, institutional holders, short interest, options data, earnings dates, and financial statements from Yahoo Finance. Several community implementations exist; the most mature wraps yfinance.

**Why we need it:** Requirements DATA-02, SECT4 (all stock/market subsections), SECT3-05 (peer benchmarking), and SECT7-01 (scoring factors F.2, F.6, F.7, F.8). Stock price data, insider transactions, short interest, and analyst consensus are essential for the market signals section.

**Package:** Multiple implementations available. Recommended: `yahoo-finance-mcp` or `mcp-yfinance`

**Install (Option A -- Alex2Yang97/yahoo-finance-mcp):**
```bash
# Clone and install
git clone https://github.com/Alex2Yang97/yahoo-finance-mcp.git
cd yahoo-finance-mcp
pip install -e .

claude mcp add-json yahoo-finance '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "yahoo_finance_mcp"]
}'
```

**Install (Option B -- use yfinance directly in Python, no MCP):**
```bash
pip install yfinance
# Access via Python code in the main pipeline, not via MCP
# This is the recommended approach for programmatic use
```

**Known limitations:**
- yfinance scrapes Yahoo Finance's undocumented backend -- Yahoo API changes have broken it before (Feb 2025 incident)
- Aggressive rate limiting and potential IP bans with high-volume usage
- No official API support -- no SLA, no guarantees
- Short interest data is delayed (typically 2 weeks behind exchange reports)
- Fundamental data can be incomplete for smaller companies

**Recommendation:** Use yfinance directly as a Python library (not MCP) with a provider abstraction layer, as specified in STACK.md. The MCP server adds overhead without benefit for programmatic pipeline access. Reserve MCP for ad-hoc interactive queries.

---

### 1.3 Firecrawl MCP Server -- MUST HAVE

**What it does:** AI-powered web crawler that converts web content to clean, LLM-ready markdown or JSON. Handles JavaScript-rendered pages, extracts structured data, and supports crawling entire sites or scraping individual URLs.

**Why we need it:** Requirements DATA-03 (litigation fallback to web search), DATA-07 (Glassdoor, news, social media), DATA-10 (web search with validation), SECT5-09 (broader sentiment signals), SECT6 (court records from web). Essential for any data source that is not available via structured API.

**Package:** `firecrawl-mcp` (npm)

**Install:**
```bash
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-YOUR_API_KEY -- npx -y firecrawl-mcp
```

**Available tools:**
- `FIRECRAWL_SCRAPE_EXTRACT_DATA_LLM` -- scrape a publicly accessible URL
- `FIRECRAWL_CRAWL_URLS` -- start a crawl job for a given URL
- `FIRECRAWL_EXTRACT` -- extract structured data from a web page
- `FIRECRAWL_CANCEL_CRAWL_JOB` -- cancel a running crawl
- `FIRECRAWL_CRAWL_JOB_STATUS` -- check crawl progress

**Free tier limits:**
- 10 scrapes per minute
- 10 maps per minute
- 5 searches per minute
- 1 crawl per minute
- No credit card required

**Known limitations:**
- Free tier rate limits may be insufficient for batch processing
- Paid plans start at $16/month
- Cannot access login-protected content
- JavaScript-heavy sites may require Playwright fallback
- API key required (SaaS dependency)

**Alternative (self-hosted, free):** Crawl4AI
```bash
pip install crawl4ai
claude mcp add-json crawl4ai '{"type":"stdio","command":"python","args":["-m","crawl4ai_mcp"]}'
```

---

### 1.4 Tavily Search MCP Server -- MUST HAVE

**What it does:** Optimized search engine for AI agents with strong citation support, domain filtering, and advanced search depth. Returns structured results with relevance scoring. Supports include/exclude domain lists for focused research.

**Why we need it:** Requirements DATA-03 (litigation discovery via web search), DATA-04 (SEC enforcement data discovery), DATA-06 (earnings call transcript discovery), DATA-07 (sentiment and alternative data), DATA-10 (web search with validation). Essential for discovering information not available in structured databases -- news articles, law firm press releases, short seller reports, regulatory announcements.

**Package:** Tavily MCP (HTTP transport, no npm package needed)

**Install:**
```bash
# HTTP transport (recommended -- lightweight, no npm)
claude mcp add --transport http tavily \
  "https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_API_KEY"

# Global scope (available across all projects)
claude mcp add --transport http --scope user tavily \
  "https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_API_KEY"
```

**Configuration for financial research:**
```json
{
  "DEFAULT_PARAMETERS": {
    "include_images": false,
    "max_results": 15,
    "search_depth": "advanced"
  }
}
```

**Domain filtering examples for D&O research:**
- `include_domains: ["sec.gov", "stanford.edu", "courtlistener.com"]` -- for regulatory/litigation
- `include_domains: ["glassdoor.com", "reddit.com"]` -- for sentiment signals
- `include_domains: ["reuters.com", "bloomberg.com", "wsj.com"]` -- for financial news

**Free tier:** 1,000 monthly API credits

**Known limitations:**
- API key required
- 1,000 free credits may be consumed quickly during multi-ticker analysis
- Search depth "advanced" uses more credits but produces better results
- Citation URLs may become stale (news articles get taken down)

---

### 1.5 DuckDB / MotherDuck MCP Server -- MUST HAVE

**What it does:** Connects Claude to DuckDB's analytical SQL engine for local data caching and analysis. Supports local DuckDB files, in-memory databases, S3-hosted databases, and MotherDuck cloud. Executes read and write SQL queries, browses database catalogs, and switches between connections.

**Why we need it:** Requirement ARCH-04 (local cache for SEC filings, market data, analysis results). DuckDB is superior to SQLite for analytical workloads -- it reads Parquet/CSV/JSON natively, integrates with pandas, and handles complex analytical queries efficiently. Perfect for caching SEC filing data, financial metrics, and peer group comparisons across analysis runs.

**Package:** `mcp-server-motherduck` (uvx/pip)

**Install:**
```bash
# Local DuckDB file (recommended for this project)
claude mcp add duckdb -- uvx mcp-server-motherduck \
  --db-path /path/to/project/data.duckdb --read-write

# In-memory (for testing)
claude mcp add duckdb -- uvx mcp-server-motherduck \
  --db-path :memory: --read-write --allow-switch-databases
```

**Known limitations:**
- Runs in read-only mode by default; `--read-write` flag required for data insertion
- Local file locks prevent concurrent access from multiple processes
- DuckDB file format may change between major versions (rare)
- MotherDuck cloud requires separate authentication for remote features

**Alternative: SQLite MCP (lighter weight)**
```bash
claude mcp add sqlite -- npx @modelcontextprotocol/server-sqlite /path/to/cache.db
```

**Recommendation:** Use DuckDB as the primary analytical cache (ARCH-04). DuckDB handles the financial data analysis patterns (aggregations, joins, window functions) much better than SQLite. Use SQLite only if simpler key-value caching is all that is needed.

---

### 1.6 Context7 MCP Server -- MUST HAVE

**What it does:** Dynamically fetches up-to-date, version-specific library documentation and code examples at query time. Instead of Claude relying on training data (which may be outdated), Context7 pulls current docs for pandas, edgartools, python-docx, pydantic, httpx, and any other library.

**Why we need it:** This project depends on ~20 Python libraries, several of which have had major version changes in 2025-2026 (pandas 3.0, edgartools 5.x, pydantic v2). Context7 prevents Claude from using outdated API patterns. Critical for preventing the "hallucinated API" failure mode.

**Package:** `@upstash/context7-mcp` (npm)

**Install:**
```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

**Optional: API key for higher rate limits:**
```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
```
Free API key available at context7.com/dashboard.

**Recent improvements (late 2025):**
- 65% token reduction
- 38% latency reduction
- 30% fewer tool calls required
- Both `searchLibrary` and `getContext` accept query strings
- Automatic pagination and result limit management

**Known limitations:**
- Requires Node.js 18+
- Coverage depends on library maintainers publishing documentation
- Very new or niche libraries may not be indexed
- Free tier has rate limits (API key increases limits)

**Usage tip:** Say "use context7" in prompts when asking about library APIs. Context7 automatically resolves library names and pulls relevant documentation.

---

### 1.7 Sequential Thinking MCP Server -- RECOMMENDED

**What it does:** Provides structured, step-by-step thinking for complex problem-solving. Enables Claude to methodically work through problems, revise approaches, branch into alternative reasoning paths, and maintain context across extended reasoning chains.

**Why we need it:** The 10-factor scoring model (SECT7-01), composite pattern detection (SECT7-02), and allegation theory mapping (SECT7-05) involve complex multi-factor reasoning. When Claude needs to evaluate 359 checks across 6 sections and synthesize them into a coherent risk assessment, structured reasoning helps prevent shortcuts and missed connections.

**Package:** `@modelcontextprotocol/server-sequential-thinking` (npm)

**Install:**
```bash
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

**Known limitations:**
- Adds latency to each reasoning step (each step is a separate tool call)
- Claude already has strong built-in reasoning, especially with extended thinking mode
- Most valuable for architectural decisions and debugging, less for routine coding
- Can consume significant context window if reasoning chains are long

**Recommendation:** Install but use judiciously. Most valuable during the ANALYZE and SCORE stages when Claude is synthesizing findings from multiple sections. Not needed for straightforward data acquisition or rendering code.

---

### 1.8 Memory MCP Servers -- EVALUATE

**What it does:** Provides persistent, searchable memory across Claude Code sessions. Several implementations exist with different approaches: knowledge graphs, vector search, structured key-value storage.

**Why we consider it:** The predecessor's core failure was context rot across 99+ development sessions. Persistent memory could help maintain architectural decisions, module responsibilities, and design rationale across sessions.

**Options (ranked by maturity):**

**Option A: Memory Keeper (mcp-memory-keeper) -- Most Mature**
```bash
pip install mcp-memory-keeper
claude mcp add-json memory-keeper '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "mcp_memory_keeper"]
}'
```
- Context stored in `~/mcp-data/memory-keeper/`
- Preserves work history, decisions, progress
- Maintained on GitHub (mkreyman/mcp-memory-keeper)

**Option B: OpenMemory MCP (by Mem0) -- Best Privacy**
```bash
npx -y openmemory-mcp
```
- Local-first, nothing goes to cloud
- Shared memory layer across MCP-compatible tools
- From Mem0 (established AI memory company)

**Option C: Claude-mem -- Newest, Most Hyped**
```bash
pip install claude-mem
```
- Auto-captures everything Claude does
- AI-compressed context injection
- 1,739 GitHub stars in 24 hours (Feb 2026)
- Very new -- stability unproven

**Known limitations (all options):**
- Memory injection adds tokens to every prompt, reducing working context
- Quality depends on what gets stored vs. what is noise
- Can create false confidence ("I remember this" when memory is stale)
- None are official Anthropic products

**Recommendation:** EVALUATE, do not commit. The CLAUDE.md + state files approach (Section 4 below) is more reliable and battle-tested. Consider Memory Keeper after Phase 1 is complete, if cross-session continuity becomes a measurable problem. Do NOT use memory as a substitute for proper state management and documentation.

---

### 1.9 GitHub MCP Server -- MUST HAVE (if using GitHub)

**What it does:** Full GitHub integration -- issues, pull requests, code review, release management, repository operations directly from Claude.

**Why we need it:** Standard development workflow. Code review, PR creation, issue tracking.

**Install:**
```bash
# HTTP transport (official)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# Then authenticate:
# /mcp -> select GitHub -> follow browser auth flow

# Or install as plugin:
# /plugin install github@claude-plugins-official
```

---

### 1.10 MCP Server Priority Summary

| # | Server | Priority | Primary Requirement | Install Command |
|---|--------|----------|-------------------|-----------------|
| 1 | EdgarTools | MUST HAVE | DATA-01, SECT2-SECT6 | `claude mcp add edgartools -- python -m edgar.ai` |
| 2 | Tavily Search | MUST HAVE | DATA-03/07/10, SECT5-09, SECT6 | `claude mcp add --transport http tavily URL` |
| 3 | Firecrawl | MUST HAVE | DATA-07/10, SECT5-09, SECT6 | `claude mcp add firecrawl -e KEY -- npx -y firecrawl-mcp` |
| 4 | DuckDB | MUST HAVE | ARCH-04 | `claude mcp add duckdb -- uvx mcp-server-motherduck --db-path ./data.duckdb --read-write` |
| 5 | Context7 | MUST HAVE | Dev quality | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |
| 6 | GitHub | MUST HAVE | Dev workflow | `claude mcp add --transport http github URL` |
| 7 | Sequential Thinking | RECOMMENDED | SECT7 scoring | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` |
| 8 | Yahoo Finance MCP | OPTIONAL | DATA-02 (use yfinance directly instead) | See Section 1.2 |
| 9 | Memory Keeper | EVALUATE | Anti-context-rot | See Section 1.8 |
| 10 | Brave Search | NICE TO HAVE | Backup search | `claude mcp add brave-search -e KEY -- npx server-brave-search` |

**Token budget warning:** Each active MCP server adds tool descriptions to every prompt. Research indicates that exceeding ~20K tokens of MCP tools "cripples Claude, leaving only 20K tokens for actual work." With 6-7 active MCP servers, monitor total MCP token overhead via `/cost` and disable unused servers during implementation-heavy sessions.

---

## 2. CLAUDE CODE PLUGINS & HOOKS

### 2.1 Pyright LSP Plugin -- MUST HAVE

**What it does:** After every file edit Claude makes, Pyright analyzes the changes and reports type errors, missing imports, and syntax issues back automatically. Claude sees errors and fixes them in the same turn. Also provides jump-to-definition, find-references, and hover type info.

**Why we need it:** The entire codebase uses Pydantic v2 models with strict typing (ARCH-03). Type errors in the AnalysisState model propagate silently if not caught. Pyright catches them at edit time, preventing the "it type-checks in my head" failure mode.

**Install:**
```bash
pip install pyright
/plugin install pyright-lsp@claude-plugins-official
```

**What Claude gains:**
1. Automatic diagnostics after every edit -- type errors, missing imports, unreachable code
2. Code navigation -- jump to definitions, find references, type info on hover
3. Symbol listing -- understands module structure

---

### 2.2 Ruff Hook (PostToolUse) -- MUST HAVE

**What it does:** Auto-formats and lints every Python file Claude edits, immediately after the edit. Ruff replaces flake8 + black + isort in a single Rust-based tool that runs in milliseconds.

**Why we need it:** Consistent code formatting across 99+ development sessions prevents "style drift" where different sessions produce code with different formatting conventions. Ruff's auto-fix capability catches common bugs (unused imports, bare except, mutable default arguments) before they accumulate.

**Install ruff:**
```bash
pip install ruff  # Or: uv add --dev ruff
```

**Hook script (`.claude/hooks/ruff-format.sh`):**
```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
ruff check --fix --quiet "$FILE_PATH" 2>/dev/null
ruff format --quiet "$FILE_PATH" 2>/dev/null
ISSUES=$(ruff check "$FILE_PATH" 2>/dev/null)
if [ -n "$ISSUES" ]; then
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Ruff found issues:\\n$ISSUES\"}}"
fi
exit 0
```

**Hook configuration in `.claude/settings.json`:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff-format.sh",
            "timeout": 15,
            "statusMessage": "Running ruff..."
          }
        ]
      }
    ]
  }
}
```

---

### 2.3 Test Runner Hook (PostToolUse, async) -- MUST HAVE

**What it does:** After Claude edits a Python file, asynchronously finds and runs the corresponding test file. Reports pass/fail back to Claude without blocking the edit flow.

**Why we need it:** The predecessor had no automated test running. Tests existed but were never executed systematically. Running tests after every edit catches regressions immediately.

**Hook script (`.claude/hooks/run-tests-async.sh`):**
```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
if [[ "$FILE_PATH" == tests/* ]] || [[ "$FILE_PATH" == */tests/* ]]; then
  TEST_FILE="$FILE_PATH"
else
  BASENAME=$(basename "$FILE_PATH" .py)
  TEST_FILE=$(find "$CLAUDE_PROJECT_DIR" -path "*/tests/test_${BASENAME}.py" 2>/dev/null | head -1)
fi
if [ -z "$TEST_FILE" ]; then exit 0; fi
cd "$CLAUDE_PROJECT_DIR"
RESULT=$(uv run pytest "$TEST_FILE" -x --tb=short 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"Tests passed for $TEST_FILE\"}"
else
  echo "{\"systemMessage\": \"Tests FAILED for $TEST_FILE:\\n$RESULT\"}"
fi
```

**Configuration (add to the PostToolUse array above):**
```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
      "async": true,
      "timeout": 120
    }
  ]
}
```

---

### 2.4 Dangerous Command Blocker (PreToolUse) -- MUST HAVE

**What it does:** Blocks destructive bash commands before they execute. Prevents accidental `rm -rf`, `DROP TABLE`, format commands, etc.

**Hook script (`.claude/hooks/block-dangerous.sh`):**
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE 'rm -rf /|DROP DATABASE|DROP TABLE|truncate|format c:|mkfs'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive command blocked by safety hook"}}'
else
  exit 0
fi
```

---

### 2.5 uv Enforcement Hook (PreToolUse) -- RECOMMENDED

**What it does:** Prevents Claude from falling back to `pip install` instead of `uv add`. Enforces the project's dependency management discipline.

**Hook script (`.claude/hooks/enforce-uv.sh`):**
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE '^pip install|^pip3 install|^python -m pip'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use uv add instead of pip install. This project uses uv for dependency management."}}'
else
  exit 0
fi
```

---

### 2.6 Pre-Compact State Capture Hook -- RECOMMENDED

**What it does:** Before Claude compacts context (which loses detail), captures the current state: git branch, last test result, what was being worked on.

**Configuration:**
```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Pre-compact state: branch='$(git -C \"$CLAUDE_PROJECT_DIR\" branch --show-current)', last test='$(cd \"$CLAUDE_PROJECT_DIR\" && uv run pytest --tb=no -q 2>&1 | tail -1)', modified='$(git -C \"$CLAUDE_PROJECT_DIR\" diff --name-only | head -5)''",
            "statusMessage": "Capturing pre-compact state...",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

---

### 2.7 Stop Hook -- Quality Gate Before Claude Finishes -- RECOMMENDED

**What it does:** When Claude thinks it is done, this hook evaluates whether the work is actually complete. Checks for test failures, type errors, and incomplete tasks.

**Configuration:**
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop: $ARGUMENTS. Check if: 1) All requested tasks are complete, 2) Any test failures need addressing, 3) Any type errors were reported by pyright that need fixing. Respond with {\"ok\": true} to allow stopping or {\"ok\": false, \"reason\": \"explanation\"} to continue.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

### 2.8 Complete `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff-format.sh",
            "timeout": 15,
            "statusMessage": "Running ruff..."
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 120
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-uv.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Pre-compact: branch='$(git -C \"$CLAUDE_PROJECT_DIR\" branch --show-current)', tests='$(cd \"$CLAUDE_PROJECT_DIR\" && uv run pytest --tb=no -q 2>&1 | tail -1)''",
            "statusMessage": "Capturing state...",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if work is complete. Any test failures or type errors? Respond {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

### 2.9 Pre-Commit Configuration (`.pre-commit-config.yaml`)

Separate from Claude Code hooks, this runs on `git commit`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
```

**Install:**
```bash
uv add --dev pre-commit
uv run pre-commit install
```

---

## 3. PYTHON LIBRARIES

### 3.1 edgartools -- SEC EDGAR (PRIMARY DATA SOURCE)

**Package:** `edgartools` >= 5.14.0
**Install:** `uv add edgartools`

**Capabilities:**
- All SEC form types: 10-K, 10-Q, 8-K, DEF 14A, Form 4, S-1, S-3, 13F, Exhibit 21, CORRESP, NT forms
- XBRL financial statement parsing to pandas DataFrames
- Built-in taxonomy normalization (handles variant element names)
- Financial statement stitching across multiple filings
- Full-text filing search
- Company facts API (XBRL data for all filers)
- Built-in rate limiting (pyrate_limiter, respects 10 req/sec)
- MCP server (`python -m edgar.ai`)
- Enterprise configuration for custom SEC data sources
- Actively maintained (v5.14.0 as of Feb 2026)

**Limitations:**
- Custom XBRL extensions may need manual mapping
- Historical filings before XBRL adoption (~pre-2009) have limited structured data
- Very large filings (100+ pages) are slow to parse
- Some filing types (Form N-1A, Form S-11) have less mature parsers

**How it maps to our requirements:**
| Requirement | edgartools Feature |
|------------|-------------------|
| DATA-01 | Core filing retrieval |
| SECT2-01/02/03 | 10-K Item 1, business description, segments |
| SECT2-05 | Exhibit 21 subsidiary extraction |
| SECT3-02/03/04 | XBRL financial statements -> DataFrames |
| SECT3-06 | Earnings quality ratios from financial data |
| SECT3-12 | 10-K/A restatements, NT filings, CORRESP letters |
| SECT4-04 | Form 4 insider trading data |
| SECT4-08 | S-3 shelf registrations, offering history |
| SECT5-02/03 | DEF 14A proxy data (officers, directors, compensation) |
| SECT6-03/04 | 10-K Item 3 legal proceedings, risk factor keywords |

---

### 3.2 yfinance -- Market Data (SUPPLEMENTARY)

**Package:** `yfinance` >= 1.1.0
**Install:** `uv add yfinance`

**Capabilities:**
- Historical OHLCV price data (daily and intraday)
- Current quotes and fundamental ratios
- Financial statements (income, balance sheet, cash flow)
- Institutional holders and insider transactions
- Analyst recommendations and price targets
- Short interest data
- Earnings dates and earnings history
- Options data
- Dividend and split history
- Multi-ticker batch downloads

**Limitations (IMPORTANT):**
- **Reliability:** Scrapes Yahoo Finance's undocumented backend. Yahoo API changes have broken it before (Feb 2025). No SLA.
- **Rate limiting:** Aggressive rate limiting and potential IP bans with high-volume usage
- **Data quality:** Incomplete fundamentals for smaller companies; short interest delayed ~2 weeks
- **No official support:** Community-maintained, not Yahoo-backed
- **Legal gray area:** Yahoo's ToS may restrict automated access

**Mitigation strategy (from STACK.md):**
1. Wrap all yfinance calls in a provider abstraction layer
2. Cache aggressively in SQLite/DuckDB -- once fetched, do not re-fetch for configurable TTL
3. Design for swap-out: Financial Modeling Prep, Alpha Vantage, or Polygon.io as alternatives
4. Use yfinance for supplementary data ONLY -- primary financial data comes from edgartools (XBRL)

---

### 3.3 python-docx + docxtpl -- Word Document Generation

**Package:** `python-docx` >= 1.2.0 (Dec 2025), `docxtpl` >= 0.20.x
**Install:** `uv add python-docx docxtpl`

**python-docx capabilities:**
- Create and modify .docx files programmatically
- Paragraphs, headings, tables, images, page breaks, sections
- Font styling, colors, borders, shading
- Headers and footers
- Numbered and bulleted lists
- Table cell merging and formatting
- Image insertion with aspect ratio preservation

**python-docx limitations:**
- No native chart generation (must embed chart images from matplotlib)
- No native Excel data embedding
- Complex layouts (multi-column, text wrapping around images) are difficult
- No track changes support
- Limited form field support

**docxtpl capabilities (python-docx-template):**
- Use a .docx file as a Jinja2 template
- Insert variables, loops, conditionals directly in Word documents
- Dynamic table rows (`{% for item in items %}...{% endfor %}`)
- Custom Jinja2 filters for formatting
- Supports pictures, index tables, headers, footers with variables
- Separates presentation from business logic

**docxtpl limitations:**
- Jinja2 tags must be within the same paragraph run
- Cross-paragraph loops require special syntax (`{%p for ... %}`)
- Complex conditional formatting requires programmatic post-processing
- Template debugging can be difficult (hard to see why a tag did not render)

**Recommended approach for this project:**
1. Create a base Word template (`templates/word/base.docx`) with styles defined visually in Word
2. Use docxtpl for section-level templates with Jinja2 variables
3. Generate charts as PNG images via matplotlib, embed via `InlineImage` in docxtpl
4. Post-process with python-docx for any formatting docxtpl cannot handle

---

### 3.4 Pydantic v2 -- State Management & Validation

**Package:** `pydantic` >= 2.12.5
**Install:** `uv add pydantic pydantic-settings`

**Why Pydantic v2 (not v1):**
- Rust-based core (pydantic-core) -- 5-50x faster validation than v1
- `model_validate_json()` / `model_dump_json()` for direct JSON serialization
- `BaseSettings` for configuration management (API keys, SEC identity, output paths)
- Discriminated unions for handling different check result types
- Strict mode for catching type coercion issues
- The anthropic SDK already depends on pydantic v2

**How it maps to our architecture:**
- `AnalysisState` -- THE single source of truth for entire analysis run (ARCH-03)
- `CompanyIdentity`, `DataGates`, `CheckResult`, `ScoringResult` -- typed submodels
- `PipelineStage` enum -- tracks progress through 7-stage pipeline
- State file validated by Pydantic on every read -- schema drift fails loudly
- Atomic read/write via temp file + rename pattern

**State management pattern:**
```python
class AnalysisState(BaseModel):
    run_id: str
    ticker: str
    current_stage: PipelineStage
    company: CompanyIdentity | None = None
    gates: DataGates = DataGates()
    check_results: list[CheckResult] = []
    scoring: ScoringResult | None = None
    # ... etc
```

---

### 3.5 httpx -- Async HTTP Client

**Package:** `httpx` >= 0.28.1
**Install:** `uv add "httpx[http2]"`

**Why httpx:**
- Both sync and async APIs from a single library
- HTTP/2 support (with `[http2]` extra)
- requests-compatible API
- edgartools uses sync HTTP internally; orchestration layer uses async
- At SEC's 10 req/sec rate limit, raw throughput is irrelevant -- httpx is fine

**Companion: tenacity for retry logic:**
```bash
uv add tenacity
```
- Exponential backoff for SEC rate limits
- Custom stop conditions
- `wait_random_exponential` for the SEC's 10 req/sec ceiling

---

### 3.6 matplotlib + mplfinance -- Financial Charts

**Package:** `matplotlib` >= 3.10.8, `mplfinance` >= 0.12.x
**Install:** `uv add matplotlib mplfinance`

**matplotlib:**
- Generates static charts that embed directly into Word and PDF
- Bar charts, line charts, radar/spider charts for risk profiles
- Event markers on price charts (stock drops, earnings dates)
- High-quality PNG output for document embedding
- The predecessor used matplotlib; chart requirements (VIS-01 through VIS-04) are all achievable

**mplfinance:**
- Built on matplotlib, specifically for financial data visualization
- Candlestick charts, OHLCV, volume bars
- Moving averages, Bollinger bands, RSI
- Custom event markers on price charts

**Why NOT plotly for v1:**
- Interactive charts are irrelevant for Word/PDF output
- matplotlib produces high-quality static images
- plotly can be added for v2 web UI without changing the analysis pipeline

**Chart embedding in Word:**
```python
# Generate chart as PNG
fig, ax = plt.subplots()
# ... build chart ...
fig.savefig("chart.png", dpi=150, bbox_inches='tight')

# Embed in docx via docxtpl
from docxtpl import InlineImage
context = {
    "stock_chart": InlineImage(doc, "chart.png", width=Inches(6))
}
```

---

### 3.7 NLP/Sentiment Libraries -- RECOMMENDATION

**For earnings call analysis (SECT5-04):**

**Option A: Claude API (RECOMMENDED for v1)**
- The anthropic SDK is already a dependency
- Claude handles all NLP tasks: sentiment analysis, hedging language detection, tone analysis, evasion pattern recognition
- No additional model dependencies (no 500MB+ FinBERT/spaCy downloads)
- Better at nuanced financial language understanding than any pre-trained model
- Cost: ~$0.05-0.20 per earnings call transcript analysis

**Option B: FinBERT (EVALUATE for v2)**
- Pre-trained on SEC filings, earnings calls, analyst reports (4.9B tokens)
- 89% accuracy on financial sentiment (vs 76% for standard BERT)
- Available via Hugging Face: `ProsusAI/finbert`
- Softmax output: positive/negative/neutral with confidence
- Requires PyTorch (~2GB install)
- Could reduce Claude API costs for high-volume sentiment classification

**Option C: Loughran-McDonald Word Lists (FREE, LIGHTWEIGHT)**
- Standard financial sentiment dictionaries used in academic research
- Word lists: positive, negative, uncertainty, litigious, strong modal, weak modal
- Zero model dependency -- just word matching against curated lists
- Ideal for SECT5-04(b) hedging language trend analysis
- Available as CSV from nd.edu or as Python package `pysentiment2`

**Recommendation for v1:** Use Claude API for all NLP tasks. It handles earnings call sentiment, hedging language detection, Q&A evasion patterns, and narrative coherence assessment (SECT5-10) better than any specialized model. Add Loughran-McDonald word lists as a lightweight supplement for quantitative hedging language counts. Evaluate FinBERT for v2 if Claude API costs become significant.

---

### 3.8 Full Dependency List

**Core dependencies (`uv add`):**
```
httpx[http2]
edgartools
yfinance
pandas
python-docx
docxtpl
jinja2
weasyprint
beautifulsoup4
lxml
matplotlib
mplfinance
anthropic
aiosqlite
typer
rich
pydantic
pydantic-settings
structlog
tenacity
```

**Dev dependencies (`uv add --dev`):**
```
pytest
pytest-asyncio
pytest-cov
respx
ruff
pyright
pre-commit
```

---

## 4. ANTI-CONTEXT-ROT ARCHITECTURE

### 4.1 What the Predecessor Got Wrong

The Underwriting-2.0 codebase is a case study in context rot. Over 99+ development phases:

1. **3 parallel data acquisition systems** -- each built when the AI lost context about the previous one
2. **4 scoring model definitions** -- in `03_SCORING_ENGINE.md`, `BRAIN/SCORING/SCORING.md`, `config/scoring_weights.json`, and `orchestrator.py` -- with DIFFERENT values
3. **9,445-line monolithic document generator** -- grew through accretion, never decomposed
4. **7+ state files** with no unified management
5. **77 Python files in a flat directory** with no package structure
6. **14 deprecated files** still present and importable
7. **Check count inconsistencies** -- 337, 359, and 425 claimed in different places
8. **Contradictory instructions** -- CLAUDE.md says "use MCP tools" while LESSONS_LEARNED says "subagents can't access MCP"
9. **Phase numbering drift** -- references to Phase 39, Phase 33, Phase 15-03a scattered through code
10. **9 test/debug output directories for a single ticker** (AAPL)

The root cause: **LLM context windows reset between sessions.** Without persistent architectural documentation, each session starts from a blank slate and "discovers" needs that already have implementations.

### 4.2 How to Structure CLAUDE.md

**Principle:** CLAUDE.md is a Project Constitution, not documentation. Short directives plus pointers to where truth lives. Keep it under 300 lines -- as instruction count increases, instruction-following quality decreases uniformly.

**Anti-rot rules for CLAUDE.md:**
1. Only include what Claude cannot infer from code
2. Convert repetitive instructions to hooks instead of CLAUDE.md rules
3. Review and prune every few weeks
4. Use `@` imports to reference detailed docs without embedding them

**Recommended CLAUDE.md structure for this project:**

```markdown
# D&O Underwriting Worksheet System

## Overview
D&O liability underwriting analysis CLI. Ticker in, risk assessment worksheet out.
Python 3.12, uv, 7-stage pipeline (RESOLVE->ACQUIRE->EXTRACT->ANALYZE->SCORE->BENCHMARK->RENDER).

## Critical Rules
- ONE source of truth per concept. Scoring in scoring.json ONLY. Checks in checks.json ONLY.
- No file over 500 lines. Decompose before it reaches 400.
- Stages communicate ONLY through AnalysisState. No cross-stage imports.
- ALL external data acquisition in Stages 1-2 (main context). Stages 3-7 work from local data only.
- Use uv (NOT pip). Use ruff (NOT black/flake8). Use pyright for type checking.

## Commands
- Install: `uv sync`
- Test: `uv run pytest`
- Test one: `uv run pytest tests/test_file.py::test_name -xvs`
- Lint: `uv run ruff check --fix .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright`

## Architecture
See @.planning/research/ARCHITECTURE.md for full pipeline design.
- src/do_underwriting/ -- main package
- src/do_underwriting/stages/ -- one subpackage per pipeline stage
- src/do_underwriting/state/ -- Pydantic state models (THE truth)
- src/do_underwriting/config/ -- JSON configs (scoring, checks, sectors, red flags)
- src/do_underwriting/data_clients/ -- ONE client per external service
- templates/ -- Jinja2 + docx templates (NOT in src/)
- tests/ -- mirrors src/ structure

## Anti-Context-Rot Discipline
1. Search before create -- grep for existing implementations before building new modules
2. Delete old code in the SAME commit as new code. Old code lives in git history, not the codebase.
3. Every 5th session: run vulture, remove dead code, update this file
4. State files, not memory. All intermediate results written to analysis_state.json.
5. Never hardcode scoring weights, check counts, or thresholds in Python. Read from config/*.json.

## Testing
- Every module has a corresponding test file
- Mock all external HTTP calls (use respx)
- Use tmp_path for test outputs -- never the production output directory
- Conventional commits: feat:, fix:, refactor:, test:, docs:
```

### 4.3 The `.claude/rules/` Pattern for Scoped Instructions

Instead of a monolithic CLAUDE.md, use path-scoped rules that only activate when Claude works in specific directories:

**`.claude/rules/scoring.md`:**
```markdown
---
paths:
  - "src/do_underwriting/stages/score/**"
  - "src/do_underwriting/config/scoring.json"
---

# Scoring Rules
- config/scoring.json is THE ONLY place scoring weights are defined
- score/engine.py READS scoring.json. It NEVER defines weights.
- Check count is computed dynamically: len(checks). Never hardcoded.
- Every scoring calculation must cite the specific check_id that contributed points.
```

**`.claude/rules/data-acquisition.md`:**
```markdown
---
paths:
  - "src/do_underwriting/stages/acquire/**"
  - "src/do_underwriting/data_clients/**"
---

# Data Acquisition Rules
- Set EDGAR_IDENTITY before any SEC requests
- Respect SEC 10 req/sec rate limit (edgartools handles this internally)
- Cache all acquired data in DuckDB/SQLite -- never re-download
- Data completeness check after every acquisition: log what was expected vs found
- Every data point must have: source, as-of date, confidence level
```

**`.claude/rules/render.md`:**
```markdown
---
paths:
  - "src/do_underwriting/stages/render/**"
  - "templates/**"
---

# Document Generation Rules
- Render reads from AnalysisState. It NEVER re-derives data.
- No business logic in templates. The most complex template logic: {% if flag.severity == 'critical' %}
- Charts generated as PNG via matplotlib, embedded as InlineImage in docxtpl
- Each section renderer is an independent module under render/sections/ (< 300 lines each)
- The composer.py file assembles render context from state -- it is the ONLY file that touches state data
```

### 4.4 State File Patterns vs Memory

**Pattern: Single state file per analysis run**

The architecture (from ARCHITECTURE.md) uses a single `AnalysisState` Pydantic model serialized as JSON. This directly prevents the predecessor's 7+ state file fragmentation:

```
analysis_runs/
  AAPL_20260207_143022/
    state.json          # THE single source of truth
    cache/              # Raw acquired data
    output/
      report.docx
      report.pdf
      report.md
    logs/
      pipeline.log
```

**Why state files beat memory servers:**
| Concern | State Files | Memory MCP |
|---------|------------|------------|
| Auditability | Read the JSON, see everything | Memory is opaque |
| Reproducibility | Re-run from saved state | Memory varies by session |
| Debugging | Inspect exact state at failure point | Memory may be stale |
| Resume | Load state, skip completed stages | Memory has no "resume" concept |
| Testing | Use fixture state files | Cannot mock memory server |
| Schema validation | Pydantic validates on every load | No schema enforcement |

**When memory IS useful:** Cross-session architectural decisions. "We decided to use DuckDB instead of SQLite for X reason." This belongs in CLAUDE.md or `.planning/` docs, not a memory server. But if you find yourself repeatedly re-explaining architectural context, a memory server may help.

### 4.5 Chunked Processing Strategy

The predecessor failed because it tried to evaluate 359 checks in a single LLM prompt, achieving only 5-10% coverage. The solution:

**Chunk checks into batches of 15-20:**
```
Section 1 (Business):     58 checks -> 3 batches of ~20
Section 2 (Stock):        35 checks -> 2 batches of ~18
Section 3 (Financial):    26 checks -> 2 batches of 13
Section 4 (Litigation):   56 checks -> 3 batches of ~19
Section 5 (Governance):  107 checks -> 6 batches of ~18
Section 6 (Forward Look): 77 checks -> 4 batches of ~19
                          ___
                          359 checks -> 20 batches total
```

**After each batch:**
1. Write results to `state.json` (persist progress)
2. Verify batch coverage: `len(results_this_batch) >= 0.85 * batch_size`
3. If coverage < 85%, retry the batch with explicit "you missed checks X, Y, Z"
4. Log completion: "Batch 3/20 complete: 19/20 checks evaluated"

**After all batches:**
1. Verify total coverage: `len(all_results) >= 0.85 * 359`
2. Identify gaps: which checks have no results?
3. Run targeted retry for gap checks

This is ARCH-06(c) in the requirements.

### 4.6 Session Discipline Protocol

**Start of every session:**
1. Read CLAUDE.md (automatic)
2. Read `.planning/STATE.md` or `analysis_state.json` for current progress
3. Run `git status` and `git log --oneline -5`
4. Identify what was last worked on and what needs to happen next

**During a session:**
1. Use `/compact` proactively at 70% context (do not wait for auto-compact at 75-92%)
2. Use `/clear` between unrelated tasks
3. Never use the final 20% of context for complex multi-file work
4. Use subagents for research tasks (they get their own context window)
5. Use `/cost` regularly to track token usage

**End of every session:**
1. Update `.planning/STATE.md` with what was done and what is next
2. Commit all changes with descriptive message
3. If architectural decisions were made, update CLAUDE.md

**Every 5th session (cleanup session):**
1. Run `vulture` to find dead code
2. Run `ruff check` on entire codebase
3. Run `pyright` on entire codebase
4. Review and prune CLAUDE.md
5. Check for files approaching 500-line limit
6. Verify no concept is defined in more than one place

### 4.7 The Critical 70% Context Threshold

Research shows that when context reaches 70-80%, quality degrades non-linearly. The final 20% of context produces 80% of errors. Practical implications:

1. **Compact at 70%**, not 90%
2. **Split large tasks** across sessions rather than cramming into the end of one
3. **Delegate research** to subagents (they get fresh context)
4. **Keep CLAUDE.md short** -- every line eats working context
5. **Disable unused MCP servers** during implementation-heavy sessions to reduce tool description overhead

### 4.8 Predecessor Failure Prevention Checklist

Every architectural decision maps to a specific predecessor failure:

| # | Predecessor Failure | Prevention | Enforced By |
|---|-------------------|-----------|-------------|
| 1 | 3 data acquisition systems | ONE `data_clients/` layer | Import boundary test |
| 2 | 4 scoring model definitions | `config/scoring.json` ONLY | CI grep test |
| 3 | 9,445-line monolith | 500-line file limit | CI line count check |
| 4 | 7+ state files | Single `state.json` per run | Pydantic schema |
| 5 | 77 files in flat directory | `src/` layout with subpackages | Package structure |
| 6 | Multiple execution paths | ONE pipeline, ONE state file | Architecture rule |
| 7 | Check count inconsistencies | Dynamic `len(checks)`, never hardcoded | CI test |
| 8 | Subagents fabricating data | Hard MCP boundary after Stage 2 | Architecture rule |
| 9 | No dependency management | `uv.lock` committed | CI install from lockfile |
| 10 | Test/production output mixing | `tmp_path` for tests, gitignore for outputs | Pytest configuration |

---

## 5. COMPLETE INSTALLATION SCRIPT

```bash
#!/bin/bash
# D&O Underwriting System -- Claude Code Environment Setup
# Run from the NEW project root (not the research directory)

set -e
echo "=== D&O Underwriting System Setup ==="

# --------------------------------------------------------
# Step 1: Python tooling
# --------------------------------------------------------
echo ""
echo "=== Step 1: Install Python tooling ==="
pip install pyright ruff

# --------------------------------------------------------
# Step 2: MCP Servers
# --------------------------------------------------------
echo ""
echo "=== Step 2: Install MCP Servers ==="

# SEC EDGAR (MUST HAVE)
claude mcp add edgartools -- python -m edgar.ai

# DuckDB local data cache (MUST HAVE)
claude mcp add duckdb -- uvx mcp-server-motherduck \
  --db-path "$(pwd)/data.duckdb" --read-write

# Documentation lookup (MUST HAVE)
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest

# Sequential reasoning (RECOMMENDED)
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# GitHub (MUST HAVE)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# ---- API KEY REQUIRED (uncomment and set keys) ----

# Web scraping (MUST HAVE -- get key at firecrawl.dev/app)
# claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-YOUR_KEY -- npx -y firecrawl-mcp

# Search (MUST HAVE -- get key at tavily.com)
# claude mcp add --transport http tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_KEY"

# Backup search (NICE TO HAVE -- get key at brave.com/search/api)
# claude mcp add brave-search -e BRAVE_API_KEY=YOUR_KEY -- npx -y @modelcontextprotocol/server-brave-search

# --------------------------------------------------------
# Step 3: Hook scripts
# --------------------------------------------------------
echo ""
echo "=== Step 3: Create hook scripts ==="
mkdir -p .claude/hooks

# Ruff auto-format/lint
cat > .claude/hooks/ruff-format.sh << 'EOF'
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
ruff check --fix --quiet "$FILE_PATH" 2>/dev/null
ruff format --quiet "$FILE_PATH" 2>/dev/null
ISSUES=$(ruff check "$FILE_PATH" 2>/dev/null)
if [ -n "$ISSUES" ]; then
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Ruff found issues:\\n$ISSUES\"}}"
fi
exit 0
EOF

# Async test runner
cat > .claude/hooks/run-tests-async.sh << 'EOF'
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
if [[ "$FILE_PATH" == tests/* ]] || [[ "$FILE_PATH" == */tests/* ]]; then
  TEST_FILE="$FILE_PATH"
else
  BASENAME=$(basename "$FILE_PATH" .py)
  TEST_FILE=$(find "$CLAUDE_PROJECT_DIR" -path "*/tests/test_${BASENAME}.py" 2>/dev/null | head -1)
fi
if [ -z "$TEST_FILE" ]; then exit 0; fi
cd "$CLAUDE_PROJECT_DIR"
RESULT=$(uv run pytest "$TEST_FILE" -x --tb=short 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"Tests passed for $TEST_FILE\"}"
else
  echo "{\"systemMessage\": \"Tests FAILED for $TEST_FILE:\\n$RESULT\"}"
fi
EOF

# Block dangerous commands
cat > .claude/hooks/block-dangerous.sh << 'EOF'
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE 'rm -rf /|DROP DATABASE|DROP TABLE|truncate|format c:|mkfs'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive command blocked"}}'
else
  exit 0
fi
EOF

# Enforce uv over pip
cat > .claude/hooks/enforce-uv.sh << 'EOF'
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE '^pip install|^pip3 install|^python -m pip'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Use uv add instead of pip install"}}'
else
  exit 0
fi
EOF

chmod +x .claude/hooks/*.sh

# --------------------------------------------------------
# Step 4: Settings with hooks
# --------------------------------------------------------
echo ""
echo "=== Step 4: Configure hooks ==="
mkdir -p .claude
cat > .claude/settings.json << 'SETTINGS'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff-format.sh",
            "timeout": 15,
            "statusMessage": "Running ruff..."
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 120
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-uv.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Pre-compact: branch='$(git -C \"$CLAUDE_PROJECT_DIR\" branch --show-current)', tests='$(cd \"$CLAUDE_PROJECT_DIR\" && uv run pytest --tb=no -q 2>&1 | tail -1)''",
            "statusMessage": "Capturing state...",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
SETTINGS

# --------------------------------------------------------
# Step 5: Path-scoped rules
# --------------------------------------------------------
echo ""
echo "=== Step 5: Create path-scoped rules ==="
mkdir -p .claude/rules

cat > .claude/rules/python-style.md << 'RULE'
---
paths:
  - "**/*.py"
---

# Python Code Style
- Type hints on all function signatures
- Google-style docstrings for public functions
- No bare `except:` -- catch specific exceptions
- Use pathlib.Path, not os.path
- Use f-strings, not .format() or %
- Imports: stdlib, third-party, local (separated by blank lines)
RULE

cat > .claude/rules/testing.md << 'RULE'
---
paths:
  - "tests/**/*.py"
---

# Testing Conventions
- Use pytest with fixtures in conftest.py
- Mock all external HTTP calls with respx
- Use tmp_path for test outputs -- never production output directory
- Use DuckDB in-memory for test database fixtures
- Test file naming: test_<module>.py
- Run with: `uv run pytest`
RULE

cat > .claude/rules/scoring.md << 'RULE'
---
paths:
  - "src/**/stages/score/**"
  - "src/**/config/scoring.json"
---

# Scoring Rules
- config/scoring.json is THE ONLY place scoring weights are defined
- score/engine.py READS scoring.json. It NEVER defines weights.
- Check count is computed dynamically. Never hardcoded.
- Every scoring calc must cite the specific check_id that contributed points.
RULE

cat > .claude/rules/data-acquisition.md << 'RULE'
---
paths:
  - "src/**/stages/acquire/**"
  - "src/**/data_clients/**"
---

# Data Acquisition Rules
- Set EDGAR_IDENTITY before any SEC requests
- Cache all acquired data -- never re-download within TTL
- Data completeness check after every acquisition
- Every data point: source, as-of date, confidence level
RULE

# --------------------------------------------------------
# Step 6: Custom commands and agents
# --------------------------------------------------------
echo ""
echo "=== Step 6: Custom commands and agents ==="
mkdir -p .claude/commands .claude/agents

cat > .claude/commands/test.md << 'CMD'
Run tests for the specified module. If no argument, run all tests.

Target: $ARGUMENTS

Steps:
1. Find the test file(s) for the given module
2. Run with `uv run pytest -xvs`
3. If tests fail, analyze failures and suggest fixes
CMD

cat > .claude/commands/review.md << 'CMD'
Review code changes in the current branch vs main.

Focus: $ARGUMENTS

Steps:
1. Run `git diff main...HEAD` to see all changes
2. Check: type safety, error handling, test coverage, no file > 500 lines
3. Verify: no hardcoded scoring weights, no cross-stage imports
4. Provide specific improvement suggestions
CMD

cat > .claude/agents/test-runner.md << 'AGENT'
---
name: test-runner
description: Runs and analyzes test results for Python modules
model: haiku
tools:
  - Bash
  - Read
  - Glob
  - Grep
---

You are a test-runner agent for a D&O underwriting analysis system.
When given a module or file path:
1. Find the corresponding test file(s)
2. Run pytest with `uv run pytest -xvs`
3. Analyze any failures
4. Report: PASS/FAIL, number of tests, failure details
AGENT

cat > .claude/agents/reviewer.md << 'AGENT'
---
name: reviewer
description: Reviews code for quality, anti-context-rot, and architecture compliance
model: sonnet
tools:
  - Read
  - Grep
  - Glob
---

You are a code review agent. Check:
1. No file exceeds 500 lines
2. Scoring weights only in config/scoring.json
3. Stages only import from state/, config/, and own subpackage
4. All external data access goes through data_clients/
5. Type hints complete, no bare except, no hardcoded constants
6. Every public function has a test
AGENT

# --------------------------------------------------------
# Step 7: Verify
# --------------------------------------------------------
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Launch Claude Code: claude"
echo "2. Install plugins: /plugin install pyright-lsp@claude-plugins-official"
echo "3. Authenticate GitHub: /mcp -> select GitHub"
echo "4. Set API keys for Tavily/Firecrawl (uncomment in script)"
echo "5. Verify MCP servers: claude mcp list"
echo "6. Bootstrap CLAUDE.md: /init (then customize)"
echo ""
```

---

## 6. SOURCES

### MCP Servers
- [EdgarTools - SEC EDGAR Python Library](https://github.com/dgunning/edgartools)
- [EdgarTools PyPI](https://pypi.org/project/edgartools/)
- [EdgarTools Documentation](https://edgartools.readthedocs.io/)
- [SEC-EDGAR-MCP Server](https://github.com/stefanoamorelli/sec-edgar-mcp)
- [EDGAR MCP (.NET)](https://github.com/leopoldodonnell/edgar-mcp)
- [Yahoo Finance MCP](https://github.com/Alex2Yang97/yahoo-finance-mcp)
- [Yahoo Finance MCP (9nate-drake)](https://github.com/9nate-drake/mcp-yfinance)
- [Firecrawl MCP Server](https://github.com/firecrawl/firecrawl-mcp-server)
- [Firecrawl MCP for Claude Code](https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/claude-code)
- [Tavily MCP Server](https://github.com/tavily-ai/tavily-mcp)
- [Tavily MCP Docs](https://docs.tavily.com/documentation/mcp)
- [MotherDuck DuckDB MCP](https://github.com/motherduckdb/mcp-server-motherduck)
- [MotherDuck MCP Docs](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-workflows/)
- [Context7 MCP (Upstash)](https://github.com/upstash/context7)
- [Context7 Blog](https://upstash.com/blog/new-context7)
- [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
- [Memory Keeper MCP](https://github.com/mkreyman/mcp-memory-keeper)
- [OpenMemory MCP (Mem0)](https://mem0.ai/blog/introducing-openmemory-mcp)
- [MCP Memory Service](https://github.com/doobidoo/mcp-memory-service)

### Claude Code Best Practices
- [Claude Code Best Practices (Official)](https://code.claude.com/docs/en/best-practices)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Claude Code Memory/CLAUDE.md](https://code.claude.com/docs/en/memory)
- [Claude Code Plugins](https://code.claude.com/docs/en/discover-plugins)
- [Beating Context Rot (The New Stack)](https://thenewstack.io/beating-the-rot-and-getting-stuff-done/)
- [Context Rot Explanation (ProductTalk)](https://www.producttalk.org/context-rot/)
- [Claude Skills and CLAUDE.md Guide (Gend)](https://www.gend.co/blog/claude-skills-claude-md-guide)
- [Claude Code Must-Haves Jan 2026 (DEV)](https://dev.to/valgard/claude-code-must-haves-january-2026-kem)
- [Claude Code Hooks for uv Projects](https://pydevtools.com/blog/claude-code-hooks-for-uv/)
- [Claude Code Context Preservation](https://claudefa.st/blog/guide/performance/context-preservation)
- [CLAUDE.md Best Practices (Arize)](https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/)
- [Writing Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Ruff Pre-Commit Configuration](https://github.com/astral-sh/ruff-pre-commit)
- [Python Code Quality Skill (Ruff + Pyright)](https://mcpmarket.com/ko/tools/skills/python-code-quality-with-ruff-pyright)

### Python Libraries
- [edgartools Documentation](https://edgartools.readthedocs.io/)
- [yfinance PyPI](https://pypi.org/project/yfinance/)
- [yfinance Complete Guide (IBKR)](https://www.interactivebrokers.com/campus/ibkr-quant-news/yfinance-library-a-complete-guide/)
- [Why yfinance Gets Blocked (Medium)](https://medium.com/@trading.dude/why-yfinance-keeps-getting-blocked-and-what-to-use-instead-92d84bb2cc01)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [docxtpl Documentation](https://docxtpl.readthedocs.io/)
- [docxtpl Dynamic Word Generation (ML Hive)](https://mlhive.com/2025/12/mastering-dynamic-word-document-generation-python-docxtpl)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic AI CLAUDE.md Example](https://github.com/pydantic/pydantic-ai/blob/main/CLAUDE.md)
- [FinBERT (Hugging Face)](https://huggingface.co/ProsusAI/finbert)
- [FinBERT GitHub](https://github.com/ProsusAI/finBERT)
- [FinBERT-LSTM for Earnings Calls (Springer)](https://link.springer.com/chapter/10.1007/978-981-96-6438-2_24)
- [mplfinance GitHub](https://github.com/matplotlib/mplfinance)
- [Plotly Financial Charts](https://plotly.com/python/financial-charts/)
- [Financial Charts Comparison (Medium)](https://medium.com/@borih.k/battle-royale-comparison-of-7-python-libraries-for-interactive-financial-charts-bbdcc28989bc)

### Architecture and Context Management
- [Context Engineering from Claude (01.me)](https://01.me/en/2025/12/context-engineering-from-claude/)
- [Claude Code End-to-End SDLC Workflow 2026](https://developersvoice.com/blog/ai/claude_code_2026_end_to_end_sdlc/)
- [Persistent Memory Architecture (DEV)](https://dev.to/suede/the-architecture-of-persistent-memory-for-claude-code-17d)
- [Claude Code Tasks (VentureBeat)](https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across/)
- [Claude Code Best Practices Patterns (DeepWiki)](https://deepwiki.com/FlorianBruniaux/claude-code-ultimate-guide/18-best-practices-and-patterns)
- [Agentic Coding Optimization 2026 (AImultiple)](https://aimultiple.com/agentic-coding/)

### Predecessor Analysis
- `/Users/gorlin/projects/research/UNDERWRITING_2_REVIEW.md` -- full codebase review
- `/Users/gorlin/projects/research/.planning/research/PITFALLS.md` -- 10 critical + 8 moderate pitfalls
- `/Users/gorlin/projects/research/.planning/research/ARCHITECTURE.md` -- 7-stage pipeline design
- `/Users/gorlin/projects/research/.planning/research/STACK.md` -- technology stack decisions
- `/Users/gorlin/projects/research/.planning/REQUIREMENTS.md` -- 111 v1 requirements

---

*Research completed 2026-02-07 by Claude Opus 4.6*
