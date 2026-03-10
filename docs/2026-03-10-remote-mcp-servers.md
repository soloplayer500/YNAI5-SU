# Remote MCP Servers — Research & Setup Guide
Date: 2026-03-10
Status: Researched — ready to add useful servers to Claude Code

---

## Two Types of MCP Integration

| Type | How | Needs API Key? |
|------|-----|----------------|
| **Claude Code MCP** | Add servers to `.claude/settings.json` or system config | NO |
| **API MCP Connector** | Pass `mcp_servers` in Messages API calls | YES (+ beta header) |

**For YNAI5-SU:** We use Claude Code, not the raw API. So we configure MCP servers in Claude Code settings — no extra API key needed.

---

## Already Connected (Working)
| Server | What It Does | Status |
|--------|-------------|--------|
| **Gmail MCP** | Search, read, draft, send emails | ✅ Live — `shemarpantophlet@gmail.com` |
| **Playwright MCP** | Browser automation, screenshots, web interaction | ✅ Live |

---

## High-Value Servers to Add (Free or Minimal Cost)

### 1. Brave Search MCP ⭐ HIGH PRIORITY
- **What**: Web search directly in Claude — more reliable than WebFetch for live data
- **Free tier**: 2,000 searches/month free
- **Get key**: https://api.search.brave.com
- **Install**: `npx @modelcontextprotocol/server-brave-search`
- **Use case**: Market research, news search for content ideas, crypto news

### 2. GitHub MCP ⭐ HIGH PRIORITY
- **What**: Read/write GitHub repos, issues, PRs, commits directly from Claude
- **Cost**: Free (uses your GitHub token)
- **Get key**: GitHub → Settings → Developer Settings → Personal Access Tokens
- **Install**: `npx @modelcontextprotocol/server-github`
- **Use case**: Push workspace to GitHub, manage projects, read code from repos

### 3. Filesystem MCP
- **What**: Enhanced local file access (already partially covered by Claude Code)
- **Cost**: Free, local
- **Install**: `npx @modelcontextprotocol/server-filesystem`
- **Use case**: Read files outside workspace, better file operations

### 4. Fetch MCP
- **What**: HTTP fetch with better content extraction than WebFetch
- **Cost**: Free, local
- **Install**: `npx @modelcontextprotocol/server-fetch`
- **Use case**: Scrape crypto data pages, read APIs without SDK

### 5. SQLite MCP (Future)
- **What**: Query SQLite databases directly
- **Cost**: Free, local
- **Install**: `npx @modelcontextprotocol/server-sqlite`
- **Use case**: When trade journal grows large — structured queries

---

## How to Add MCP Servers to Claude Code

### Method 1: Via Claude Code CLI (Easiest)
```bash
# Add a server
claude mcp add brave-search -e BRAVE_API_KEY=your_key -- npx @modelcontextprotocol/server-brave-search

# Add GitHub
claude mcp add github -e GITHUB_TOKEN=your_token -- npx @modelcontextprotocol/server-github

# List current servers
claude mcp list

# Remove a server
claude mcp remove server-name
```

### Method 2: Manual config edit
File: `C:\Users\shema\.claude\settings.json` (or `claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_key_here"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_token_here"
      }
    }
  }
}
```

---

## API-Based Remote MCP Servers (Requires Anthropic API Key)
When we get the API key, these can be connected via `mcp_servers` parameter:
- Brave Search (remote hosted version)
- Any server with a public HTTPS endpoint
- Uses beta header: `anthropic-beta: mcp-client-2025-11-20`

---

## Recommended Action Plan

| Step | Action | Priority |
|------|--------|----------|
| 1 | Get Brave Search API key (free) → add via `claude mcp add` | High |
| 2 | Get GitHub Personal Access Token → add GitHub MCP | High |
| 3 | Test both servers in Claude Code | Immediate |
| 4 | Add `BRAVE_API_KEY` and `GITHUB_TOKEN` to `.env.local` for reference | After setup |

---

## Resources
- Official MCP servers list: https://github.com/modelcontextprotocol/servers
- Claude Code MCP docs: https://docs.anthropic.com/claude-code/mcp
- Brave Search API: https://api.search.brave.com
- GitHub tokens: https://github.com/settings/tokens
