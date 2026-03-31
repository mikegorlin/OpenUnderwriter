# OpenCode MCP Configuration for D&O Underwriting Worksheet

This document describes how to configure Model Context Protocol (MCP) servers for use with OpenCode in the `do-uw` project. MCP servers provide external tools to the AI agent (e.g., SEC EDGAR access, web search, browser automation).

## Separation Strategy: Git Worktrees

To prevent contamination between Claude Desktop and OpenCode environments, we use **git worktrees**:

- **Main directory** (`/Users/gorlin/projects/UW/do-uw/`): Claude Desktop workspace (main branch)
- **OpenCode worktree** (`/Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do/`): OpenCode workspace (opencode-do branch)

### Key Benefits:
- **Complete file separation**: Each workspace has its own working directory
- **Shared git history**: Both worktrees share the same `.git` repository
- **Branch isolation**: Main directory on `main` branch, OpenCode on `opencode-do` branch
- **Easy synchronization**: Merge changes between branches as needed
- **No configuration conflicts**: Separate `.mcp.json` (Claude) vs `opencode.json` (OpenCode)

### Workflow for Transferring Developments:
1. **Claude develops on main branch** → commits to main
2. **Merge main → opencode-do** to bring changes to OpenCode side:
   ```bash
   cd .opencode/worktrees/opencode-do
   git fetch origin
   git merge main
   ```
3. **OpenCode develops on opencode-do branch** → commits to opencode-do
4. **Selective merging** of OpenCode improvements back to main if desired

### Creating the Worktree (Already Done):
```bash
# From main project directory
git worktree add .opencode/worktrees/opencode-do opencode-do
```

## Current Status

### Core MCP Servers (Configured in opencode.json)

| MCP Server | Status | Type | Notes |
|------------|--------|------|-------|
| `edgartools` | ✅ Working | Local | SEC EDGAR filings and XBRL data. Path: `../../../.venv/bin/python -m edgar.ai.mcp.server` |
| `context7` | ✅ Configured | Remote | Documentation search at `https://mcp.context7.com/mcp`. Free tier available. |

### oh-my-openagent Plugin MCPs (Built-in)

| MCP Server | Status | Type | Notes |
|------------|--------|------|-------|
| **Exa** | ⚠️ Needs API key | Built-in | Neural web search. Requires `EXA_API_KEY` environment variable. |
| **Context7** | ✅ Available | Built-in | Same as above, via plugin integration. |
| **Grep.app** | ✅ Available | Built-in | GitHub code search via Vercel proxy. |

### MCPs from CLAUDE.md (Not Yet Configured)

| MCP Server | Status | Type | Notes |
|------------|--------|------|-------|
| `brave-search` | ❌ Not configured | Unknown | Web search with news filtering (2,000 free/month) |
| `playwright` | ❌ Not configured | Unknown | Browser automation for scraping dynamic sites |
| `fetch` | ❌ Not configured | Unknown | Simple URL content extraction |
| `duckdb` | ❌ Not configured | Unknown | Analytical data cache |
| `github` | ❌ Not configured | Unknown | Development workflow |
| `nano-banana` | ❌ Not configured | Local | Gemini image generation (requires GEMINI_API_KEY) |

## Configuration File

MCP servers are configured in `opencode.json`. The file includes:

- `edgartools`: Local Python server using the `edgar` library
- `context7`: Remote server at `https://mcp.context7.com/mcp`
- Placeholders for other MCP servers (disabled by default)

## Setup Instructions

### 1. Install Dependencies

Ensure the project's Python environment has the required MCP packages:

```bash
cd /Users/gorlin/projects/UW/do-uw
uv add mcp  # Already in pyproject.toml
uv sync
```

### 2. oh-my-openagent Plugin Installation

The plugin is already installed globally via OpenCode plugin system. It provides:

- **Built-in MCPs**: Exa (web search), Context7 (docs), Grep.app (GitHub search)
- **Agent orchestration**: Multi-model coordination (Claude, GPT, Gemini, etc.)
- **LSP/AST tools**: Advanced code analysis capabilities
- **Parallel background agents**: Concurrent task execution

**Plugin configuration** (`.opencode/oh-my-opencode.json`):
```json
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",
  "new_task_system_enabled": true,
  "default_run_agent": "sisyphus"
}
```

**To update the plugin:**
```bash
npx oh-my-opencode@latest
```

### 3. Getting Shit Done (GSD) Integration

The oh-my-openagent plugin provides **built-in GSD (Getting Shit Done) functionality** through its disciplined agent system:

#### **Sisyphus Agent - The Discipline Agent**
- **Default agent**: Configured as `"default_run_agent": "sisyphus"`
- **GSD enforcement**: Waits until all todos are completed or cancelled before exiting
- **Multi-model orchestration**: Can coordinate Claude, GPT, Gemini, and other models
- **Background task management**: Parallel execution with completion tracking

#### **Using GSD Mode**
Instead of launching OpenCode normally, use:
```bash
cd /Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do
npx oh-my-opencode run "Your task description here"
```

**Key GSD Features:**
- **Todo completion enforcement**: Agent won't exit until all `todowrite` tasks are completed
- **Session persistence**: Can resume work with `--session-id`
- **Progress tracking**: Background tasks monitored until idle
- **Structured output**: Optional `--json` flag for programmatic use

#### **Example GSD Workflows**
```bash
# Basic GSD task (uses Sisyphus agent by default)
npx oh-my-opencode run "Fix the bug in src/do_uw/stages/acquire/orchestrator.py"

# With specific model
npx oh-my-opencode run --model anthropic/claude-sonnet-4 "Implement new feature"

# Resume previous session
npx oh-my-opencode run --session-id ses_abc123 "Continue from where we left off"

# With completion hook
npx oh-my-opencode run --on-complete "notify-send 'Task completed'" "Analyze AAPL ticker"
```

#### **Configuration**
The GSD system is enabled via:
- `"new_task_system_enabled": true` - Enables todo tracking and enforcement
- `"default_run_agent": "sisyphus"` - Uses the disciplined Sisyphus agent
- Protected tools include `todowrite` and `todoread` for task management

#### **Available Agents**
- **Sisyphus**: Discipline agent for GSD (default)
- **Hephaestus**: Craftsmanship-focused agent
- **Prometheus**: Innovation/exploration agent  
- **Atlas**: Heavy-lifting/refactoring agent

### 4. Agent Swarm (Parallel Execution)

oh-my-openagent includes a sophisticated **agent swarm system** that allows parallel execution of multiple specialized agents. This is built into the Sisyphus agent and can be configured for optimal performance.

#### **Built-in Agent Types**
- **Sisyphus**: Main orchestrator (uses `claude-opus-4-6` / `kimi-k2.5` / `glm-5`)
- **Hephaestus**: Autonomous deep worker (uses `gpt-5.4`) - "The Legitimate Craftsman"
- **Prometheus**: Strategic planner (interview mode, detailed planning)
- **Oracle**: Architecture/debugging specialist  
- **Librarian**: Documentation/code search agent
- **Explore**: Fast codebase grep/pattern discovery
- **Multimodal Looker**: Image/visual analysis

#### **Swarm Orchestration**
Sisyphus can delegate tasks to other agents using `call_omo_agent()`:
```javascript
// Example from refactoring template
call_omo_agent(
  description="Explore codebase patterns",
  subagent_type="explore", 
  run_in_background=true,
  prompt="Search for relevant patterns and implementations"
)
```

#### **Background Task Configuration**
The plugin supports concurrent execution with configurable limits (set in `.opencode/oh-my-opencode.json`):
- `defaultConcurrency`: Maximum parallel background tasks (default: 5)
- `providerConcurrency`: Limits per API provider (Anthropic, OpenAI, Google, etc.)
- `modelConcurrency`: Limits per specific model
- `maxDepth`: Maximum delegation nesting depth
- `maxDescendants`: Maximum total descendant tasks

#### **Swarm Workflow Example**
1. **Sisyphus receives task** and analyzes requirements
2. **Launches parallel exploration agents** (Explore, Librarian) for context gathering
3. **Delegates specialized work** to Hephaestus (deep implementation), Oracle (architecture), etc.
4. **Monitors completion** of all background tasks
5. **Integrates results** and delivers final output

#### **Automatic Parallelization**
For complex tasks like refactoring, the system automatically:
- Launches 5+ explore agents simultaneously to map codebase
- Runs test analysis in parallel with code discovery  
- Delegates independent subtasks to appropriate agents
- Uses dependency graphs to identify parallel execution waves

#### **Manual Agent Invocation**
You can also manually invoke specific agents:
```bash
# Run Hephaestus for deep implementation work
npx oh-my-opencode run --agent hephaestus "Implement feature X"

# Run Prometheus for planning
npx oh-my-opencode run --agent prometheus "Plan the architecture for Y"

# Run Explore for codebase analysis  
npx oh-my-opencode run --agent explore "Find all uses of API Z"
```

### 5. Environment Variables

Create or update `.env` file with necessary API keys:

```bash
# SEC EDGAR identity (required for edgartools)
EDGAR_IDENTITY="do-uw/0.1.0 (contact@example.com)"

# Context7 API key (optional, for higher rate limits)
CONTEXT7_API_KEY="your_key_here"

# Gemini API key for nano-banana image generation
GEMINI_API_KEY="your_key_here"

# Exa API key for neural web search (oh-my-openagent plugin)
EXA_API_KEY="your_key_here"

# Context7 API key for higher rate limits (optional)
CONTEXT7_API_KEY="your_key_here"

# Other API keys as needed
SERPER_API_KEY="your_key_here"  # For web search fallback
ANTHROPIC_API_KEY="your_key_here"  # For LLM extraction
SUPABASE_ANON_KEY="your_key_here"  # For litigation database
```

### 6. Test MCP Servers

#### Test edgartools locally:

```bash
# Kill any existing edgartools MCP server
pkill -f "edgar.ai.mcp.server"

# Start the server in background
EDGAR_IDENTITY="do-uw/0.1.0 (contact@example.com)" \
  .venv/bin/python -m edgar.ai.mcp.server &

# Check OpenCode MCP status
opencode mcp list

# Kill the background server
kill %1
```

#### Test context7 (remote):

```bash
opencode mcp list  # Should show context7 status
```

### 7. Using OpenCode with the Worktree

**OpenCode should be launched from the worktree directory:**

```bash
cd /Users/gorlin/projects/UW/do-uw/.opencode/worktrees/opencode-do
# Launch OpenCode from here (in Warp terminal with OpenCode plugin)
```

**Verify MCP servers are connected:**
- After starting OpenCode, check available tools
- The oh-my-openagent plugin MCPs should be automatically available
- edgartools MCP server starts on-demand when tools are invoked

### 8. Testing MCP Connectivity

To test edgartools MCP server manually:

## MCP Server Details

### edgartools (Local)
- **Purpose**: SEC EDGAR filing retrieval and XBRL data extraction
- **Command**: `../../../.venv/bin/python -m edgar.ai.mcp.server` (relative from worktree to main `.venv`)
- **Requirements**: `mcp` Python package, `edgartools>=5.14.1`
- **Environment**: `EDGAR_IDENTITY="do-uw/0.1.0 (contact@example.com)"` (set in opencode.json)
- **Environment**: `EDGAR_IDENTITY` must be set per SEC requirements
- **Source**: Part of the `edgartools` Python library

### context7 (Remote)
- **Purpose**: Search through documentation and code examples
- **URL**: `https://mcp.context7.com/mcp`
- **Requirements**: Optional API key for higher rate limits
- **Free Tier**: Available without API key (limited requests)

### MCP Server Status

The following MCP servers referenced in CLAUDE.md are not yet configured for OpenCode. Additional servers (Exa, Grep.app) are provided by the oh-my-openagent plugin:

1. **brave-search**: Web search with news/domain filtering (2,000 free/month)
   - Need to find MCP server implementation (npm package or remote server)
   - Potential alternatives: Serper.dev MCP, Exa semantic search MCP

2. **playwright**: Browser automation for scraping dynamic sites
   - May be available as `@modelcontextprotocol/server-playwright` npm package
   - Requires Playwright installation and browser binaries

3. **fetch**: Simple URL content extraction
   - May be available as `@modelcontextprotocol/server-fetch` npm package
   - Simple HTTP client for fetching web content

4. **duckdb**: Analytical data cache
   - May be available as `@modelcontextprotocol/server-duckdb` npm package
   - SQL query execution on DuckDB databases

5. **github**: Development workflow
   - May be available as `@modelcontextprotocol/server-github` npm package
   - GitHub API access for repository operations

6. **nano-banana**: Gemini image generation
   - Available as `nano-banana-mcp` npm package
   - Requires `GEMINI_API_KEY` environment variable
### Plugin Integration (oh-my-openagent)

The **oh-my-openagent** plugin (formerly oh-my-opencode) provides additional MCP servers and enhanced tooling for OpenCode.

#### Installation

```bash
opencode plugin oh-my-openagent -g
```

Add to your `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["oh-my-openagent"],
  ...
}
```

#### Built-in MCP Servers

The plugin includes these MCP servers by default:

1. **Exa** (`exa`) - Neural web search (requires API key)
2. **Context7** (`context7`) - Documentation search (already configured separately)
3. **Grep.app** (`gh_grep`) - GitHub code search via Vercel's Grep

These servers are enabled automatically when the plugin loads. They may not appear in `opencode mcp list` as they are managed dynamically by the plugin.

#### Plugin CLI

The plugin provides a CLI for management:

```bash
npx oh-my-opencode mcp oauth status  # Check OAuth token status
npx oh-my-opencode doctor            # Diagnostic checks
```

#### Configuration

Create a separate configuration file `.opencode/oh-my-opencode.json` for plugin-specific settings (disabled MCPs, agent configurations, etc.). See plugin schema for details.

#### Benefits

- Parallel background agents
- Pre-built LSP/AST tools
- Enhanced MCP integration with skill-based on-demand servers

## Finding MCP Server Implementations

To locate MCP server packages:

```bash
# Search npm for MCP servers
npm search mcp-server
npm search @modelcontextprotocol

# Check Model Context Protocol GitHub organization
# https://github.com/modelcontextprotocol

# Common package naming pattern:
# @modelcontextprotocol/server-{name}
```

## Integration with do-uw Pipeline

The `do-uw` pipeline uses MCP tools primarily in the ACQUIRE stage:

- **SEC EDGAR data**: Uses direct `httpx` calls (not MCP dependent)
- **Web search**: Uses pluggable `search_fn` injected by orchestrator
- **Browser automation**: May use Playwright for court record scraping
- **Documentation**: Context7 for library documentation lookup

Note: The pipeline can run without MCP servers using fallback HTTP clients and local data sources.

## Troubleshooting

### "MCP error -32000: Connection closed"
- The MCP server failed to start or crashed
- Check server logs for errors
- Verify Python dependencies are installed

### "No MCP servers configured"
- OpenCode cannot read `opencode.json`
- Ensure file is in project root with valid JSON
- Run `opencode mcp list` to verify

### Server starts but tools not available
- OpenCode may need restart after configuration changes
- Exit OpenCode (`Ctrl+D`) and restart
- Check `opencode mcp list` shows server as connected

## Next Steps

1. **Identify missing MCP server implementations**
   - Search npm registry for available packages
   - Check Model Context Protocol GitHub organization
   - Consider alternative providers (Serper, Exa, etc.)

2. **Configure essential MCP servers**
   - brave-search (web search for blind spot detection)
   - playwright (court record scraping)
   - fetch (simple URL fetching)

3. **Update pipeline to use MCP tools**
   - Modify ACQUIRE stage to use MCP-injected functions
   - Ensure graceful fallback when MCP servers unavailable

4. **Document usage examples**
   - Example prompts for using each MCP tool
   - Integration testing with the pipeline

## References

- [OpenCode MCP Documentation](https://opencode.ai/docs/mcp-servers)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [edgartools MCP Server](https://github.com/dgunning/edgartools)
- [Context7 MCP](https://context7.com/mcp)