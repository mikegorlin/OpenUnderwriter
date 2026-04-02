#!/bin/bash
# OpenCode Setup Script for D&O Underwriting System
# Run this before starting OpenCode in Warp terminal

set -e

echo "=== OpenCode Setup for D&O Underwriting ==="
echo

# Check if we're in the OpenUnderwriter directory
if [ ! -f "opencode.json" ]; then
    echo "Error: Must run from OpenUnderwriter directory"
    echo "Expected: /Users/gorlin/projects/UW/OpenUnderwriter/"
    exit 1
fi

# Source .env file if it exists
if [ -f ".env" ]; then
    echo "Sourcing .env file..."
    # Export all variables from .env file
    set -a
    source .env
    set +a
    echo "  Loaded environment variables from .env"
else
    echo "Warning: No .env file found. Creating from template..."
    cp .env.example .env 2>/dev/null || echo "  No .env.example found either"
fi

# Check required environment variables
echo
echo "Checking environment variables:"
if [ -z "$SUPABASE_URL" ]; then
    echo "  ❌ SUPABASE_URL not set"
else
    echo "  ✅ SUPABASE_URL is set"
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "  ❌ SUPABASE_ANON_KEY not set"
else
    echo "  ✅ SUPABASE_ANON_KEY is set"
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "  ⚠️  SUPABASE_SERVICE_ROLE_KEY not set (optional for writes)"
else
    echo "  ✅ SUPABASE_SERVICE_ROLE_KEY is set"
fi

if [ -z "$MCP_API_KEY" ]; then
    echo "  ⚠️  MCP_API_KEY not set (using 'test-key' as default)"
    export MCP_API_KEY="test-key"
else
    echo "  ✅ MCP_API_KEY is set"
fi

if [ -z "$BRAVE_API_KEY" ]; then
    echo "  ⚠️  BRAVE_API_KEY not set (brave-search MCP disabled)"
else
    echo "  ✅ BRAVE_API_KEY is set"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "  ⚠️  GITHUB_TOKEN not set (github MCP disabled)"
else
    echo "  ✅ GITHUB_TOKEN is set"
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "  ⚠️  DEEPSEEK_API_KEY not set (LLM extraction may fail for OpenCode DeepSeek branch)"
else
    echo "  ✅ DEEPSEEK_API_KEY is set"
fi

echo
echo "=== MCP Server Status ==="
echo

# Check if MCP servers are installed
echo "Checking installed MCP servers:"

if [ -f "node_modules/.bin/edgartools-mcp" ] || [ -f "node_modules/.bin/edgartools" ]; then
    echo "  ✅ edgartools: installed"
else
    echo "  ❌ edgartools: not installed (using Python server)"
fi

if [ -f "node_modules/.bin/brave-search-mcp-server" ]; then
    echo "  ✅ brave-search: installed"
else
    echo "  ❌ brave-search: not installed"
fi

if [ -L "node_modules/.bin/playwright-mcp" ]; then
    if [ -f "node_modules/.bin/playwright-mcp" ]; then
        echo "  ✅ playwright: installed (binary works)"
    else
        echo "  ⚠️  playwright: symlink exists but target missing"
    fi
else
    echo "  ❌ playwright: not installed"
fi

if [ -f "node_modules/.bin/fetch-mcp" ]; then
    echo "  ✅ fetch: installed"
else
    echo "  ❌ fetch: not installed"
fi

if [ -f "node_modules/.bin/github-mcp" ]; then
    echo "  ✅ github: installed"
else
    echo "  ❌ github: not installed"
fi

if [ -f "node_modules/.bin/supabase-mcp-claude" ]; then
    echo "  ✅ supabase: installed (supabase-mcp-claude)"
else
    echo "  ❌ supabase: not installed"
fi

echo
echo "=== Configuration Summary ==="
echo
echo "OpenCode configuration:"
echo "  - Worktree: $(pwd)"
echo "  - Config: opencode.json"
echo "  - MCP Servers configured:"
grep -E '"type"|"enabled"' opencode.json | head -20

echo
echo "=== Next Steps ==="
echo "1. Review the .env file and add missing API keys:"
echo "   - BRAVE_API_KEY: Get from https://brave.com/search/api/"
echo "   - GITHUB_TOKEN: Generate personal access token if needed"
echo "   - EXA_API_KEY: Get from https://exa.ai/ for oh-my-openagent neural search"
echo
echo "2. Start OpenCode in Warp terminal with these environment variables"
echo "   You can source this script: source setup_opencode.sh"
echo
echo "3. Test MCP connectivity in OpenCode:"
echo "   - Run: /mcp list"
echo "   - Check that edgartools, playwright, fetch, supabase are connected"
echo
echo "4. Test the D&O pipeline:"
echo "   - Run: uv run do-uw analyze AAPL  (from main directory)"
echo "   - Or: ./run_aapl.sh  (test script)"
echo
echo "=== Agent Swarm Configuration ==="
echo "oh-my-openagent plugin provides:"
echo "  - Default agent: Sisyphus (orchestrator)"
echo "  - Other agents: Hephaestus, Prometheus, Oracle, Librarian, Explore"
echo "  - GSD enforcement: npx oh-my-opencode run (waits for todo completion)"
echo "  - Parallel background agents with concurrency limits"
echo
echo "=== User Profile ==="
echo "User knowledge transferred to USER_PROFILE.md"
echo "Includes: Mike Gorlin, 25 years underwriting experience, D&O domain knowledge"