# Claude Code: Comprehensive MCP, Plugin, Hook, and Configuration Research

**Research Date:** February 6, 2026
**Target Project:** Data-intensive Python (SEC EDGAR, document generation, financial analysis)

---

## TABLE OF CONTENTS

1. [Part 1: MCP Servers -- Comprehensive Catalog](#part-1-mcp-servers)
2. [Part 2: Claude Code Plugins](#part-2-claude-code-plugins)
3. [Part 3: Claude Code Hooks](#part-3-claude-code-hooks)
4. [Part 4: CLAUDE.md Optimization](#part-4-claudemd-optimization)
5. [Part 5: Other Productivity Enhancements](#part-5-other-productivity-enhancements)
6. [Appendix: Complete Installation Script](#appendix-complete-installation-script)

---

## PART 1: MCP SERVERS

### 1.1 SEC EDGAR / Financial Data MCP Servers

#### EdgarTools MCP Server -- MUST HAVE

The only SEC EDGAR library built from the ground up for AI agents and LLMs. Includes a production-ready MCP server. Supports all SEC form types (10-K, 10-Q, 8-K, 13F, Form 4, DEF 14A, S-1). Parses XBRL financial data, extracts text sections, and converts filings to pandas DataFrames.

**Install:**
```bash
pip install edgartools

claude mcp add edgartools -- python -m edgar.ai
```

Or using `claude mcp add-json`:
```bash
claude mcp add-json edgartools '{"type":"stdio","command":"python","args":["-m","edgar.ai"],"env":{"EDGAR_IDENTITY":"Your Name your.email@example.com"}}'
```

**Status:** Actively maintained on GitHub (dgunning/edgartools). Python-native, works perfectly with Claude Code.

#### SEC-EDGAR-MCP (Alternative) -- NICE TO HAVE

A standalone MCP server for SEC EDGAR data with real-time data streaming via SSE.

**Install:**
```bash
pip install sec-edgar-mcp

claude mcp add-json sec-edgar-mcp '{"type":"stdio","command":"python","args":["-m","sec_edgar_mcp.server"],"env":{"SEC_EDGAR_USER_AGENT":"Your Name (your@email.com)"}}'
```

**Status:** Maintained on GitHub (stefanoamorelli/sec-edgar-mcp, LuisRincon23/SEC-MCP). Good alternative if you want a lighter-weight solution.

---

### 1.2 Code Quality / LSP Servers

#### Pyright LSP Plugin -- MUST HAVE

Not an MCP server but a Claude Code **plugin** that provides real-time Python type checking. After every file edit Claude makes, Pyright analyzes the changes and reports type errors, missing imports, and syntax issues back automatically. Claude sees errors and fixes them in the same turn. Also provides jump-to-definition, find-references, and hover type info.

**Install:**
```bash
# First install pyright
pip install pyright
# Or: npm install -g pyright

# Then install the plugin
/plugin install pyright-lsp@claude-plugins-official
```

**Requires:** `pyright-langserver` binary in PATH.

**Status:** Part of the official Anthropic plugin marketplace. Actively maintained.

#### Ruff (via Hooks, not MCP) -- MUST HAVE

Ruff is best integrated via hooks (see Part 3), not as an MCP server. Claude Code hooks auto-format and lint after every file edit.

**Install ruff:**
```bash
pip install ruff
```

Hook configuration is detailed in Part 3.

---

### 1.3 Testing MCP Servers

There are no widely-adopted dedicated "pytest MCP servers." Testing is best handled through:

1. **Claude Code hooks** (PostToolUse to run pytest after edits -- see Part 3)
2. **Claude's built-in Bash tool** (Claude can run `pytest` directly)
3. **Custom subagents** (a test-runner agent in `.claude/agents/`)

#### Recommended Approach -- MUST HAVE (via hooks + agent)

Create a PostToolUse hook that runs pytest asynchronously after Python file edits, and a custom test-runner subagent. Details in Part 3 and Part 5.

---

### 1.4 Docker / Container MCP

#### Docker MCP Toolkit -- NICE TO HAVE

Connects Claude Code to Docker for isolated execution. Creates secure containerized environments where code runs without risk to the local machine.

**Install:**
```bash
# Install Docker Desktop first, then:
claude mcp add docker -- npx -y @docker/mcp-server
```

The Docker Sandbox feature also supports running Claude Code itself in a containerized dev environment with `--dangerously-skip-permissions` for unattended operation.

**Status:** Maintained by Docker Inc. 200+ pre-built containerized MCP servers available.

#### Development Containers -- NICE TO HAVE

Claude Code has native devcontainer support documented at `code.claude.com/docs/en/devcontainer`. Useful for reproducible environments.

---

### 1.5 Git MCP Servers

#### Official Git MCP Server -- NICE TO HAVE

Provides git operations (diff, log, blame, commit) as MCP tools.

**Install:**
```bash
claude mcp add git -- uvx mcp-server-git --repository /Users/gorlin/projects/research
```

**Status:** Latest version 2026.1.14. Recently patched for security (CVE-2025-68143, CVE-2025-68144, CVE-2025-68145).

**Note:** Claude Code already has excellent built-in git support via its Bash tool. The Git MCP server adds structured access to blame, log parsing, and diff operations but is not strictly necessary. Consider it if you want richer git history context injected into Claude's reasoning.

#### GitHub MCP Server -- MUST HAVE (if using GitHub)

**Install:**
```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
# Then authenticate:
# /mcp -> select GitHub -> follow browser flow
```

Or install as a plugin:
```bash
/plugin install github@claude-plugins-official
```

**Status:** Official, maintained by GitHub/Anthropic.

---

### 1.6 Database MCP Servers

#### DuckDB / MotherDuck MCP -- MUST HAVE (for data-intensive Python)

DuckDB is the best choice for a local analytical data cache in a Python data project. It handles Parquet, CSV, JSON natively, integrates with pandas/polars, and supports analytical SQL.

**Install (local DuckDB file):**
```bash
claude mcp add duckdb -- uvx mcp-server-motherduck --db-path /Users/gorlin/projects/research/data.duckdb --read-write
```

**Install (MotherDuck cloud):**
```bash
claude mcp add motherduck --env motherduck_token=YOUR_TOKEN -- uvx mcp-server-motherduck --db-path md: --read-write
```

**Status:** Maintained by MotherDuck. Actively developed. Supports local files, in-memory databases, S3-hosted databases.

#### SQLite MCP Server -- NICE TO HAVE

Good for simpler key-value or metadata caching.

**Install:**
```bash
claude mcp add sqlite -- npx @modelcontextprotocol/server-sqlite /Users/gorlin/projects/research/cache.db
```

**Status:** Part of the official modelcontextprotocol/servers repo.

#### PostgreSQL MCP Server -- NICE TO HAVE (if using PostgreSQL)

**Install:**
```bash
claude mcp add postgres -- npx -y @bytebase/dbhub --dsn "postgresql://user:pass@localhost:5432/dbname"
```

**Recommendation:** For a local data cache on a Python data project, **DuckDB is the best choice**. It is purpose-built for analytical workloads, reads Parquet/CSV directly, and has excellent Python integration. Use SQLite only for simple metadata. Use PostgreSQL only if you already have one running.

---

### 1.7 Documentation MCP Servers

#### Context7 -- MUST HAVE

Dynamically fetches up-to-date, version-specific library documentation and code examples at query time. Instead of relying on training data, Context7 pulls current docs for pandas, polars, SEC libraries, etc.

**Install:**
```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

**Status:** Maintained by Upstash. Open-source and free. Requires Node.js 18+.

**Usage:** Context7's skill triggers automatically when you ask about libraries. You can also explicitly reference it. Very valuable for ensuring Claude uses current API signatures rather than hallucinated ones.

---

### 1.8 Web Scraping MCP Servers

#### Firecrawl MCP -- MUST HAVE (for SEC/court/news scraping)

AI-powered web crawler that converts web content to clean, LLM-ready markdown or JSON. SaaS model with free tier.

**Install:**
```bash
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-YOUR_API_KEY -- npx -y firecrawl-mcp
```

**Cost:** Free tier available. Paid plans start at $16/month.
**Status:** Official server by Firecrawl. Actively maintained. Works great with Claude Code.

#### Crawl4AI MCP -- NICE TO HAVE (free alternative)

Self-hosted, Python-native web crawler. No API key needed. Uses Playwright under the hood.

**Install:**
```bash
pip install crawl4ai
# Then add as MCP:
claude mcp add-json crawl4ai '{"type":"stdio","command":"python","args":["-m","crawl4ai_mcp"]}'
```

**Cost:** Free (self-hosted). You pay for your own compute and LLM tokens.
**Status:** Maintained on GitHub (sadiuysal/crawl4ai-mcp-server).

**Recommendation:** Use **Firecrawl** for production reliability and ease. Use **Crawl4AI** if you need self-hosted/free or finer control. Both work with Claude Code. For SEC EDGAR specifically, the EdgarTools MCP is better than raw scraping.

---

### 1.9 Search MCP Servers

#### Tavily Search -- MUST HAVE (best for financial/legal research)

Optimized for factual information with strong citation support. Supports domain filtering (include_domains/exclude_domains). 1,000 free monthly credits.

**Install (HTTP transport, recommended):**
```bash
claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_API_KEY
```

**Install (user scope, available across all projects):**
```bash
claude mcp add --transport http -s user tavily https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_API_KEY
```

**Status:** Official Tavily MCP server. Production-ready. Best balance for research workloads.

#### Brave Search -- NICE TO HAVE (generous free tier)

2,000 free queries/month. Good for general web search.

**Install:**
```bash
claude mcp add brave-search -e BRAVE_API_KEY=YOUR_KEY -- npx -y @modelcontextprotocol/server-brave-search
```

**Status:** Part of official modelcontextprotocol/servers. Endorsed by Anthropic.

#### Exa Search -- NICE TO HAVE (best for code/company research)

Neural search engine. Strong for developer-focused queries, company research, and code context retrieval.

**Install (HTTP):**
```bash
claude mcp add --transport http exa https://mcp.exa.ai/mcp?tools=web_search_exa,get_code_context_exa,crawling_exa,company_research_exa
```

Or via plugin:
```bash
/plugin marketplace add exa-labs/exa-mcp-server
/plugin install exa-mcp-server
```

**Status:** Maintained by Exa AI. Requires API key from dashboard.exa.ai.

**Recommendation:** Install **Tavily** as the primary search engine (best for financial/legal research with domain filtering). Add **Brave Search** as a free fallback. Consider **Exa** if you need company research or code context.

---

### 1.10 File Management MCP Servers

#### Filesystem MCP Server -- SKIP

Claude Code already has excellent built-in file operations (Read, Write, Edit, Glob, Grep). The Filesystem MCP server is mainly for Claude Desktop, which lacks these built-in tools.

#### Desktop Commander MCP -- SKIP for Claude Code

Provides terminal commands and file operations. Redundant with Claude Code's built-in capabilities. Mainly useful for Claude Desktop.

---

### 1.11 Monitoring / Observability MCP

#### OpenTelemetry (Built-in) -- MUST HAVE (free, built-in)

Claude Code has native OpenTelemetry support for metrics and events. No MCP server needed.

**Enable:**
```bash
# Set OTel endpoint before launching Claude
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
claude
```

#### Enhanced Telemetry Skill -- NICE TO HAVE

Captures comprehensive observability metrics across Claude Code lifecycle using hooks. Tracks session duration, prompt patterns, tool sequences, context window utilization, and token accumulation. Integrates with Grafana dashboards.

**Status:** Available on mcpmarket.com. Community-maintained.

#### ccusage -- NICE TO HAVE

CLI tool for analyzing Claude Code usage from local JSONL transcript files.

**Install:**
```bash
npx ccusage
```

**Status:** Maintained on GitHub (ryoppippi/ccusage). Good for cost tracking.

---

### 1.12 Thinking / Planning MCP Servers

#### Sequential Thinking MCP -- NICE TO HAVE

Provides structured, step-by-step thinking for complex problem-solving. Enables Claude to methodically work through problems, revise approaches, and maintain context across extended reasoning chains.

**Install:**
```bash
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

**Status:** Part of official modelcontextprotocol/servers repo.

**Note:** Claude already has strong built-in reasoning, especially with extended thinking enabled. This server is most useful for very complex architectural decisions or debugging sessions.

---

### 1.13 Data Analysis MCP

#### ClaudeJupy (Jupyter MCP) -- NICE TO HAVE

ML Jupyter MCP server with execution framework for Claude Code integration. Allows Claude to execute and interact with Jupyter notebooks.

**Install:**
```bash
pip install claudejupy
claude mcp add-json claudejupy '{"type":"stdio","command":"python","args":["-m","claudejupy"]}'
```

**Status:** Maintained on GitHub (mayank-ketkar-sf/ClaudeJupy).

#### MCP Pandas -- NICE TO HAVE

Brings pandas capabilities to the MCP ecosystem through containerized architecture.

**Note:** For most Python data analysis, Claude Code can use pandas/polars directly via its Bash tool. These MCP servers add incremental value for specific workflows.

---

### 1.14 MCP Server Priority Summary

| Server | Priority | Install Command |
|--------|----------|----------------|
| EdgarTools | MUST HAVE | `claude mcp add edgartools -- python -m edgar.ai` |
| Pyright LSP | MUST HAVE | `/plugin install pyright-lsp@claude-plugins-official` |
| DuckDB | MUST HAVE | `claude mcp add duckdb -- uvx mcp-server-motherduck --db-path ./data.duckdb --read-write` |
| Context7 | MUST HAVE | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |
| Tavily Search | MUST HAVE | `claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=KEY` |
| Firecrawl | MUST HAVE | `claude mcp add firecrawl -e FIRECRAWL_API_KEY=KEY -- npx -y firecrawl-mcp` |
| GitHub | MUST HAVE | `claude mcp add --transport http github https://api.githubcopilot.com/mcp/` |
| Brave Search | NICE TO HAVE | `claude mcp add brave-search -e BRAVE_API_KEY=KEY -- npx -y @modelcontextprotocol/server-brave-search` |
| Git | NICE TO HAVE | `claude mcp add git -- uvx mcp-server-git --repository .` |
| Sequential Thinking | NICE TO HAVE | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` |
| SQLite | NICE TO HAVE | `claude mcp add sqlite -- npx @modelcontextprotocol/server-sqlite ./cache.db` |
| Docker | NICE TO HAVE | `claude mcp add docker -- npx -y @docker/mcp-server` |
| Exa Search | NICE TO HAVE | HTTP transport, see above |
| Crawl4AI | NICE TO HAVE | Self-hosted Python, see above |
| Filesystem | SKIP | Redundant with Claude Code built-ins |
| Desktop Commander | SKIP | Redundant with Claude Code built-ins |

---

## PART 2: CLAUDE CODE PLUGINS

### 2.1 Plugin System Overview

Claude Code plugins are shareable packages that bundle slash commands, specialized agents, MCP servers, and hooks into single installable units. Launched October 2025 (public beta). Over 9,000 plugins available as of early 2026.

**Key difference from MCP servers:**
- **MCP servers** provide tools (functions Claude can call) via the Model Context Protocol
- **Plugins** are broader packages that can include MCP servers, slash commands, agents, hooks, and LSP configurations all bundled together

### 2.2 Plugin Management Commands

```bash
# Open interactive plugin manager
/plugin

# Install from official marketplace
/plugin install plugin-name@claude-plugins-official

# Add a third-party marketplace
/plugin marketplace add owner/repo

# Install from third-party marketplace
/plugin install plugin-name@marketplace-name

# Manage plugins
/plugin disable plugin-name@marketplace-name
/plugin enable plugin-name@marketplace-name
/plugin uninstall plugin-name@marketplace-name
/plugin update plugin-name@marketplace-name

# List marketplaces
/plugin marketplace list
```

### 2.3 Must-Have Plugins for Python Development

#### Code Intelligence (LSP)

| Plugin | Language | Binary Required | Priority |
|--------|----------|----------------|----------|
| `pyright-lsp` | Python | `pyright-langserver` | MUST HAVE |
| `typescript-lsp` | TypeScript | `typescript-language-server` | If using TS |

**What Claude gains from pyright-lsp:**
1. **Automatic diagnostics** -- after every file edit, Pyright analyzes changes and reports type errors, missing imports, syntax issues. Claude sees and fixes errors in the same turn.
2. **Code navigation** -- jump to definitions, find references, get type info on hover, list symbols.

Install:
```bash
pip install pyright
/plugin install pyright-lsp@claude-plugins-official
```

#### External Integrations (Official Marketplace)

| Plugin | Purpose | Priority |
|--------|---------|----------|
| `github` | GitHub integration | MUST HAVE |
| `sentry` | Error monitoring | NICE TO HAVE |
| `slack` | Team communication | NICE TO HAVE |
| `notion` | Documentation | NICE TO HAVE |
| `linear` | Project management | NICE TO HAVE |

#### Development Workflow Plugins

| Plugin | Purpose | Priority |
|--------|---------|----------|
| `commit-commands` | Git commit workflows | NICE TO HAVE |
| `pr-review-toolkit` | PR review agents | NICE TO HAVE |
| `plugin-dev` | Create your own plugins | NICE TO HAVE |

### 2.4 Third-Party Marketplaces Worth Adding

```bash
# Official demo marketplace (example plugins)
/plugin marketplace add anthropics/claude-code

# Community LSP marketplace (additional language servers)
/plugin marketplace add Piebald-AI/claude-code-lsps

# Community plugins with 270+ plugins and 739 agent skills
/plugin marketplace add jeremylongshore/claude-code-plugins-plus-skills
```

### 2.5 Recommended Plugin Setup for This Project

```bash
# Step 1: Install pyright binary
pip install pyright

# Step 2: Install the must-have plugins
/plugin install pyright-lsp@claude-plugins-official
/plugin install github@claude-plugins-official

# Step 3: Add community marketplace for additional tools
/plugin marketplace add anthropics/claude-code

# Step 4: Install development workflow plugins
/plugin install commit-commands@anthropics-claude-code
```

---

## PART 3: CLAUDE CODE HOOKS

### 3.1 Hook System Overview

Hooks are shell commands (or LLM prompts) that execute automatically at specific points in Claude Code's lifecycle. They are configured in `.claude/settings.json` (project) or `~/.claude/settings.json` (global).

**Hook Events:**

| Event | When It Fires | Can Block? |
|-------|--------------|------------|
| `SessionStart` | When session begins/resumes | No |
| `UserPromptSubmit` | When you submit a prompt | Yes |
| `PreToolUse` | Before a tool call | Yes |
| `PostToolUse` | After a tool call succeeds | No (feedback only) |
| `PostToolUseFailure` | After a tool call fails | No (feedback only) |
| `PermissionRequest` | When permission dialog appears | Yes |
| `Notification` | When Claude sends a notification | No |
| `SubagentStart` | When a subagent spawns | No |
| `SubagentStop` | When a subagent finishes | Yes |
| `Stop` | When Claude finishes responding | Yes |
| `PreCompact` | Before context compaction | No |
| `SessionEnd` | When session terminates | No |

**Matcher Patterns:** Regex strings that filter when hooks fire.
- For tool events: matches tool name (`Bash`, `Edit`, `Write`, `Edit|Write`)
- For MCP tools: `mcp__servername__toolname` pattern

### 3.2 Recommended Hook Configurations

#### Complete `.claude/settings.json` for Python Data Project

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
            "statusMessage": "Running ruff format and lint..."
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
      }
    ],
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

#### Hook Script: `.claude/hooks/ruff-format.sh`

```bash
#!/bin/bash
# Auto-format and lint Python files after every edit

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Run ruff check with auto-fix, then format
ruff check --fix --quiet "$FILE_PATH" 2>/dev/null
ruff format --quiet "$FILE_PATH" 2>/dev/null

# If ruff found unfixable issues, report them back
ISSUES=$(ruff check "$FILE_PATH" 2>/dev/null)
if [ -n "$ISSUES" ]; then
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Ruff found issues:\\n$ISSUES\"}}"
fi

exit 0
```

#### Hook Script: `.claude/hooks/run-tests-async.sh`

```bash
#!/bin/bash
# Run related tests asynchronously after file edits

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only run tests for Python source/test files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Determine which test file to run
if [[ "$FILE_PATH" == tests/* ]] || [[ "$FILE_PATH" == */tests/* ]]; then
  TEST_FILE="$FILE_PATH"
else
  # Try to find corresponding test file
  BASENAME=$(basename "$FILE_PATH" .py)
  TEST_FILE=$(find . -name "test_${BASENAME}.py" -o -name "${BASENAME}_test.py" 2>/dev/null | head -1)
fi

if [ -z "$TEST_FILE" ]; then
  exit 0
fi

RESULT=$(python -m pytest "$TEST_FILE" -x --tb=short 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"Tests passed for $TEST_FILE\"}"
else
  echo "{\"systemMessage\": \"Tests FAILED for $TEST_FILE:\\n$RESULT\"}"
fi
```

#### Hook Script: `.claude/hooks/block-dangerous.sh`

```bash
#!/bin/bash
# Block dangerous bash commands

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block destructive commands
if echo "$COMMAND" | grep -qE 'rm -rf /|DROP DATABASE|DROP TABLE|truncate|format|mkfs'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive command blocked by safety hook"}}'
else
  exit 0
fi
```

Make all hook scripts executable:
```bash
mkdir -p .claude/hooks
chmod +x .claude/hooks/*.sh
```

### 3.3 Advanced Hook Patterns

#### SessionStart: Auto-load project context

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Current git branch:' $(git branch --show-current) && echo 'Recent commits:' && git log --oneline -5 && echo 'Modified files:' && git diff --name-only"
          }
        ]
      }
    ]
  }
}
```

#### SessionStart: Persist environment variables

```bash
#!/bin/bash
# .claude/hooks/setup-env.sh
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export PYTHONPATH="$PYTHONPATH:./src"' >> "$CLAUDE_ENV_FILE"
  echo 'export EDGAR_IDENTITY="Your Name your@email.com"' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

#### PreCompact: Save important context before compaction

```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Compacting context. Key state: branch='$(git branch --show-current)', last test result='$(python -m pytest --tb=no -q 2>&1 | tail -1)''",
            "statusMessage": "Capturing pre-compact state..."
          }
        ]
      }
    ]
  }
}
```

---

## PART 4: CLAUDE.md OPTIMIZATION

### 4.1 Key Principles

1. **Keep it under 300 lines.** Shorter is better. As instruction count increases, instruction-following quality decreases uniformly.
2. **Only include what Claude cannot infer from code.** If Claude already does something correctly without the instruction, delete it.
3. **Convert repetitive instructions to hooks** instead of CLAUDE.md rules.
4. **Review and prune periodically.** Every few weeks, ask Claude to review and optimize your CLAUDE.md.

### 4.2 Memory Hierarchy

Claude Code uses a 4-level memory hierarchy (highest priority first):

| Level | Location | Purpose | Shared? |
|-------|----------|---------|---------|
| Managed Policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Org-wide | All users |
| Project Memory | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team project rules | Via git |
| Project Rules | `./.claude/rules/*.md` | Modular topic rules | Via git |
| User Memory | `~/.claude/CLAUDE.md` | Personal preferences | Just you |
| Local Project | `./CLAUDE.local.md` | Personal project prefs | Just you (gitignored) |

### 4.3 The `@` Import Syntax

CLAUDE.md files can import other files:

```markdown
See @README.md for project overview and @pyproject.toml for dependencies.

# Workflow
- Git workflow: @docs/git-workflow.md
- API conventions: @docs/api-conventions.md
```

Rules:
- Both relative and absolute paths work
- Relative paths resolve relative to the file containing the import
- Recursive imports allowed (max depth: 5)
- Imports not evaluated inside code blocks
- First-time imports require approval

### 4.4 Per-Directory CLAUDE.md Files

Claude Code reads CLAUDE.md files recursively upward from cwd. It also discovers CLAUDE.md files in subdirectories (loaded lazily when Claude reads files in those subtrees).

Example structure:
```
project/
  CLAUDE.md                    # Main project rules
  CLAUDE.local.md              # Your personal prefs (gitignored)
  .claude/
    CLAUDE.md                  # Alternative main location
    rules/
      code-style.md            # Modular: code style
      testing.md               # Modular: testing rules
      security.md              # Modular: security rules
      api-design.md            # Modular: API conventions
  src/
    CLAUDE.md                  # Rules specific to src/
    edgar/
      CLAUDE.md                # Rules specific to EDGAR code
    reports/
      CLAUDE.md                # Rules specific to report generation
  tests/
    CLAUDE.md                  # Rules specific to tests/
```

### 4.5 Path-Specific Rules (`.claude/rules/`)

Rules files support YAML frontmatter with `paths` to scope rules to specific files:

```markdown
---
paths:
  - "src/edgar/**/*.py"
  - "src/financial/**/*.py"
---

# SEC EDGAR Code Rules

- Always set EDGAR_IDENTITY before making requests
- Use edgartools library for all SEC data access
- Cache filing data in DuckDB, not in memory
- Parse XBRL with edgartools built-in parsers
```

```markdown
---
paths:
  - "tests/**/*.py"
---

# Testing Rules

- Use pytest with fixtures defined in conftest.py
- Mock all external HTTP calls (SEC EDGAR, court APIs)
- Use DuckDB in-memory mode for test database fixtures
- Every new function needs a corresponding test
```

### 4.6 Recommended CLAUDE.md Template for This Project

```markdown
# Project: [Your Project Name]

## Overview
Financial data analysis platform. SEC EDGAR filings, document generation, financial analysis.
Python 3.11+. Uses uv for package management.

## Tech Stack
- Python 3.11+ with uv (NOT pip directly)
- DuckDB for local data cache
- edgartools for SEC EDGAR access
- pandas/polars for data processing
- pytest for testing
- ruff for linting/formatting

## Commands
- Install deps: `uv sync`
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_file.py::test_name -xvs`
- Lint: `uv run ruff check --fix .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright`

## Architecture
- `src/` -- main source code
- `src/edgar/` -- SEC EDGAR data access (@src/edgar/README.md)
- `src/reports/` -- document generation
- `src/analysis/` -- financial analysis
- `tests/` -- pytest tests (mirror src/ structure)
- `data/` -- DuckDB database and cached data

## Code Style
- Type hints on all function signatures
- Google-style docstrings for public functions
- No bare `except:` -- always catch specific exceptions
- Use pathlib.Path, not os.path
- Use f-strings, not .format() or %

## Testing
- Every module in src/ has a corresponding test file in tests/
- Use pytest fixtures for shared setup
- Mock all external HTTP calls
- Use DuckDB in-memory for test fixtures

## Git
- Conventional commits: feat:, fix:, refactor:, test:, docs:
- Always run tests before committing
- PR descriptions must include what changed and why
```

---

## PART 5: OTHER PRODUCTIVITY ENHANCEMENTS

### 5.1 Custom Slash Commands

Custom slash commands are stored as markdown files in `.claude/commands/` (project) or `~/.claude/commands/` (personal).

#### Example: `/test` command

File: `.claude/commands/test.md`
```markdown
Run the test suite for the specified module or file. If no argument given, run all tests.

Test target: $ARGUMENTS

Steps:
1. If a specific file/module is given, find the corresponding test file
2. Run pytest with -xvs flags for verbose output
3. If tests fail, analyze the failure and suggest fixes
4. Report test coverage for the tested module
```

#### Example: `/review` command

File: `.claude/commands/review.md`
```markdown
Review the code changes in the current branch compared to main.

Focus areas: $ARGUMENTS

Steps:
1. Run `git diff main...HEAD` to see all changes
2. For each changed file, check:
   - Type safety (are type hints correct and complete?)
   - Error handling (are exceptions handled properly?)
   - Test coverage (do new functions have tests?)
   - SEC EDGAR compliance (is EDGAR_IDENTITY set?)
3. Provide a summary with specific improvement suggestions
```

#### Example: `/edgar` command

File: `.claude/commands/edgar.md`
```markdown
Fetch and analyze SEC EDGAR filing data.

Query: $ARGUMENTS

Steps:
1. Use the edgartools MCP server to access SEC EDGAR
2. Fetch the requested filing or data
3. Parse relevant financial data into a structured format
4. Store results in the DuckDB cache if appropriate
5. Provide a summary analysis
```

### 5.2 Custom Subagents

Subagents are stored as markdown files in `.claude/agents/`.

#### Test Runner Agent

File: `.claude/agents/test-runner.md`
```yaml
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

You are a test-runner agent for a Python data analysis project.

When given a module or file path:
1. Find the corresponding test file(s)
2. Run pytest with detailed output
3. Analyze any failures
4. Report results concisely

Always use `uv run pytest` to run tests.
Report: PASS/FAIL, number of tests, and any failure details.
```

#### Code Reviewer Agent

File: `.claude/agents/reviewer.md`
```yaml
---
name: reviewer
description: Reviews Python code for quality, type safety, and best practices
model: sonnet
tools:
  - Read
  - Grep
  - Glob
---

You are a code review agent for a Python financial data project.

Review code for:
1. Type hint correctness and completeness
2. Error handling (no bare except, proper exception types)
3. Security (no hardcoded credentials, proper input validation)
4. Performance (efficient pandas/polars operations, proper DuckDB queries)
5. Test coverage (every public function should have tests)

Be specific and actionable in your feedback.
```

#### Research Agent

File: `.claude/agents/researcher.md`
```yaml
---
name: researcher
description: Researches SEC filings, financial data, and regulatory information
model: opus
tools:
  - Read
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---

You are a financial research agent. You help find and analyze:
- SEC EDGAR filings and financial data
- Regulatory requirements and compliance information
- Court filings and legal documents
- Financial analysis methodologies

Always cite your sources. Store findings in structured format.
```

### 5.3 Permission Modes

| Mode | What It Does | When to Use |
|------|-------------|-------------|
| Default | Asks before edits and shell commands | Normal interactive work |
| `acceptEdits` | Auto-approves file edits, asks for shell | Trusted refactoring sessions |
| `bypassPermissions` | No prompts at all | Only in Docker containers |
| Plan mode | Generates plan first, waits for approval | Complex architecture changes |

**Recommended approach:** Use default mode normally. Press **Shift+Tab** to toggle auto-accept for a session when doing trusted refactoring. Never use `bypassPermissions` outside a container.

### 5.4 Model Selection Strategy

| Model | When to Use | Cost |
|-------|------------|------|
| **Sonnet 4.5** (default) | 80% of daily work: feature development, tests, refactoring | Baseline |
| **Opus 4.6** | Complex architecture, multi-file refactors, debugging tangled issues | ~5x Sonnet |
| **Haiku 4.5** | Quick syntax questions, small single-file edits, typo fixes | ~0.3x Sonnet |
| **opusplan** | Hybrid: Opus for planning, Sonnet for execution | Variable |

**Switch models:**
```bash
# In Claude Code, use /model command
/model opus
/model sonnet
/model haiku

# Or set as environment variable
CLAUDE_MODEL=claude-opus-4-6 claude

# Or in settings
# ~/.claude/settings.json: {"model": "claude-sonnet-4-5-20250929"}
```

**Best practice:** Use Sonnet for 80% of work. Reserve Opus for the 20% that truly needs deep reasoning (complex debugging, architecture decisions, large refactors).

### 5.5 Context Management Techniques

1. **Use `/compact` proactively at 70% context.** Don't wait for auto-compact at 75-92%.
2. **Use `/clear` between unrelated tasks.** Every new task should start fresh.
3. **Never use the final 20% of context for complex multi-file tasks.** Quality degrades.
4. **Use subagents for research tasks.** They get their own context window.
5. **Keep CLAUDE.md short.** Long CLAUDE.md files eat into your working context.
6. **Use `/cost` regularly** to track token usage.

**Session hygiene pattern:**
```
Start session -> Work on task -> /compact when complex -> Complete task -> /clear -> Next task
```

### 5.6 Claude-mem (Persistent Memory Plugin)

A new plugin (February 2026, 1,739 GitHub stars in 24 hours) that automatically captures everything Claude does, compresses it with AI, and injects relevant context into future sessions. Achieves approximately 10x token savings through progressive context retrieval.

**Install:**
```bash
pip install claude-mem
```

**Status:** Very new but rapidly adopted. Worth evaluating for long-running projects where session continuity matters.

### 5.7 Essential Daily Commands

| Command | Purpose |
|---------|---------|
| `/init` | Bootstrap CLAUDE.md from codebase |
| `/compact` | Compress context to free space |
| `/clear` | Clear context for new task |
| `/cost` | Check token usage and costs |
| `/model` | Switch between models |
| `/memory` | Edit memory files in your editor |
| `/mcp` | Check MCP server status, authenticate |
| `/plugin` | Manage plugins |
| `/hooks` | View/edit hooks interactively |
| `/agents` | List available subagents |
| `Ctrl+O` | Toggle verbose mode (see hook output, diagnostics) |

### 5.8 Tips from Power Users

1. **Start with `/init`** to bootstrap your CLAUDE.md, then refine it manually.
2. **Use hooks instead of CLAUDE.md rules** for anything that can be automated (formatting, linting, test running).
3. **Create specific slash commands** for your most common workflows (test, review, deploy).
4. **Use subagents for parallel work** -- a skill can launch multiple subagents to gather information from different sources simultaneously.
5. **Install the pyright-lsp plugin immediately** -- it prevents an entire class of type errors from being introduced.
6. **Use DuckDB as your data cache** -- it is analytically fast, reads Parquet/CSV natively, and integrates perfectly with pandas.
7. **Run Claude Code with `--debug`** to see hook execution details when troubleshooting.
8. **Periodically ask Claude to review your CLAUDE.md** -- "Review this CLAUDE.md and suggest improvements."

---

## APPENDIX: COMPLETE INSTALLATION SCRIPT

Run this to set up the full recommended environment:

```bash
#!/bin/bash
# Claude Code Comprehensive Setup for Python Data Project
# Run from project root

echo "=== Step 1: Install Python tooling ==="
pip install pyright ruff edgartools sec-edgar-mcp

echo "=== Step 2: Install MCP Servers ==="

# SEC EDGAR (MUST HAVE)
claude mcp add edgartools -- python -m edgar.ai

# DuckDB local data cache (MUST HAVE)
claude mcp add duckdb -- uvx mcp-server-motherduck --db-path "$(pwd)/data.duckdb" --read-write

# Documentation (MUST HAVE)
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest

# Web scraping (MUST HAVE -- requires API key)
# claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-YOUR_KEY -- npx -y firecrawl-mcp

# Search (MUST HAVE -- requires API key)
# claude mcp add --transport http tavily https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_KEY

# GitHub (MUST HAVE)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# Brave Search (NICE TO HAVE -- requires API key)
# claude mcp add brave-search -e BRAVE_API_KEY=YOUR_KEY -- npx -y @modelcontextprotocol/server-brave-search

# Sequential Thinking (NICE TO HAVE)
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

echo "=== Step 3: Create hook scripts ==="
mkdir -p .claude/hooks

cat > .claude/hooks/ruff-format.sh << 'HOOKEOF'
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
HOOKEOF

cat > .claude/hooks/run-tests-async.sh << 'HOOKEOF'
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi
if [[ "$FILE_PATH" == tests/* ]] || [[ "$FILE_PATH" == */tests/* ]]; then
  TEST_FILE="$FILE_PATH"
else
  BASENAME=$(basename "$FILE_PATH" .py)
  TEST_FILE=$(find . -name "test_${BASENAME}.py" -o -name "${BASENAME}_test.py" 2>/dev/null | head -1)
fi
if [ -z "$TEST_FILE" ]; then exit 0; fi
RESULT=$(python -m pytest "$TEST_FILE" -x --tb=short 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"Tests passed for $TEST_FILE\"}"
else
  echo "{\"systemMessage\": \"Tests FAILED for $TEST_FILE:\\n$RESULT\"}"
fi
HOOKEOF

cat > .claude/hooks/block-dangerous.sh << 'HOOKEOF'
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE 'rm -rf /|DROP DATABASE|DROP TABLE|truncate|format c:|mkfs'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive command blocked by safety hook"}}'
else
  exit 0
fi
HOOKEOF

chmod +x .claude/hooks/*.sh

echo "=== Step 4: Create settings.json with hooks ==="
mkdir -p .claude
cat > .claude/settings.json << 'SETTINGSEOF'
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
      }
    ]
  }
}
SETTINGSEOF

echo "=== Step 5: Create agent definitions ==="
mkdir -p .claude/agents

cat > .claude/agents/test-runner.md << 'AGENTEOF'
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

You are a test-runner agent for a Python data analysis project.
When given a module or file path:
1. Find the corresponding test file(s)
2. Run pytest with `uv run pytest` and detailed output
3. Analyze any failures
4. Report results concisely: PASS/FAIL, number of tests, failure details
AGENTEOF

cat > .claude/agents/reviewer.md << 'AGENTEOF'
---
name: reviewer
description: Reviews Python code for quality, type safety, and best practices
model: sonnet
tools:
  - Read
  - Grep
  - Glob
---

You are a code review agent for a Python financial data project.
Review code for:
1. Type hint correctness and completeness
2. Error handling (no bare except, proper exception types)
3. Security (no hardcoded credentials, proper input validation)
4. Performance (efficient data operations, proper DuckDB queries)
5. Test coverage (every public function should have tests)
Be specific and actionable in your feedback.
AGENTEOF

echo "=== Step 6: Create custom commands ==="
mkdir -p .claude/commands

cat > .claude/commands/test.md << 'CMDEOF'
Run tests for the specified module. If no argument, run all tests.

Target: $ARGUMENTS

Steps:
1. Find the test file(s) for the given module
2. Run with `uv run pytest -xvs`
3. If tests fail, analyze failures and suggest fixes
CMDEOF

cat > .claude/commands/review.md << 'CMDEOF'
Review code changes in the current branch vs main.

Focus: $ARGUMENTS

Steps:
1. Run `git diff main...HEAD` to see all changes
2. Check type safety, error handling, test coverage
3. Provide specific improvement suggestions
CMDEOF

echo "=== Step 7: Create rules directory ==="
mkdir -p .claude/rules

cat > .claude/rules/python-style.md << 'RULEEOF'
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
RULEEOF

cat > .claude/rules/testing.md << 'RULEEOF'
---
paths:
  - "tests/**/*.py"
---

# Testing Conventions

- Use pytest with fixtures in conftest.py
- Mock all external HTTP calls
- Use DuckDB in-memory for test database fixtures
- Test file naming: test_<module>.py
- Use `uv run pytest` to run tests
RULEEOF

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Launch Claude Code: claude"
echo "2. Install plugins: /plugin install pyright-lsp@claude-plugins-official"
echo "3. Authenticate GitHub: /mcp -> select GitHub"
echo "4. Bootstrap CLAUDE.md: /init"
echo "5. Set API keys for Tavily/Firecrawl/Brave (uncomment in script above)"
echo ""
echo "Verify MCP servers: claude mcp list"
```

---

## Sources

### Official Documentation
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Claude Code Memory/CLAUDE.md](https://code.claude.com/docs/en/memory)
- [Claude Code Plugins](https://code.claude.com/docs/en/discover-plugins)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Settings](https://code.claude.com/docs/en/settings)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code Model Configuration](https://code.claude.com/docs/en/model-config)

### MCP Servers
- [EdgarTools - SEC EDGAR Python Library](https://github.com/dgunning/edgartools)
- [SEC-EDGAR-MCP Server](https://github.com/stefanoamorelli/sec-edgar-mcp)
- [MotherDuck DuckDB MCP](https://github.com/motherduckdb/mcp-server-motherduck)
- [Context7 MCP](https://github.com/upstash/context7)
- [Firecrawl MCP](https://github.com/firecrawl/firecrawl-mcp-server)
- [Tavily MCP](https://github.com/tavily-ai/tavily-mcp)
- [Brave Search MCP](https://github.com/modelcontextprotocol/servers)
- [Exa MCP](https://github.com/exa-labs/exa-mcp-server)
- [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
- [mcp-server-git](https://pypi.org/project/mcp-server-git/)
- [Docker MCP Toolkit](https://www.docker.com/blog/add-mcp-servers-to-claude-code-with-mcp-toolkit/)
- [Crawl4AI MCP](https://github.com/sadiuysal/crawl4ai-mcp-server)

### Plugins and Marketplaces
- [Official Anthropic Plugin Marketplace](https://github.com/anthropics/claude-plugins-official)
- [Claude Code LSPs Marketplace](https://github.com/Piebald-AI/claude-code-lsps)
- [Claude Code Plugins Plus Skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)

### Community Guides and References
- [Top 10 MCP Servers for Claude Code 2026](https://apidog.com/blog/top-10-mcp-servers-for-claude-code/)
- [Best MCP Servers 2026 - Builder.io](https://www.builder.io/blog/best-mcp-servers-2026)
- [Claude Code Hooks for uv Projects](https://pydevtools.com/blog/claude-code-hooks-for-uv/)
- [CLAUDE.md Best Practices - Arize](https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/)
- [Writing a Good CLAUDE.md - HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Complete Guide to CLAUDE.md - Builder.io](https://www.builder.io/blog/claude-md-guide)
- [Claude Code Must-Haves January 2026 - DEV Community](https://dev.to/valgard/claude-code-must-haves-january-2026-kem)
- [How I Use Every Claude Code Feature](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)
- [Claude Code Cheatsheet - Shipyard](https://shipyard.build/blog/claude-code-cheat-sheet/)
- [Awesome Claude Code (Community)](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery)
- [Multi-Agent Observability Hooks](https://github.com/disler/claude-code-hooks-multi-agent-observability)
- [ccusage - Usage Analyzer](https://github.com/ryoppippi/ccusage)
- [Claude-mem - Persistent Memory](https://byteiota.com/claude-mem-persistent-memory-for-claude-code/)
- [Ruff Claude Hook](https://github.com/TMYuan/ruff-claude-hook)
