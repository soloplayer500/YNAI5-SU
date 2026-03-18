# Design: YNAI5 System Health + Crash Recovery — Method C
_Date: 2026-03-12 | Approved by: Shami_

---

## Problem
1. Claude Code freezes and must be killed via Task Manager — all session context lost on restart
2. Docker MCP requires manual startup — not usable as a skill on demand
3. No automated system health monitoring — can't diagnose why laptop crashes
4. Many tools running but no orchestration — everything starts manually

---

## Solution: Method C — Hybrid Hooks + On-Demand Tools + Cloud Automation

### Architecture Overview
```
YNAI5 System
├── Layer 1: Crash Recovery (Claude Code Hooks)
│   ├── PreCompact hook → saves backup before context compaction
│   ├── Stop hook → saves clean shutdown state
│   └── SessionStart hook → loads backup + surfaces incomplete tasks
│
├── Layer 2: System Health (On-Demand + GitHub Actions)
│   ├── /health-check skill → local psutil diagnostics (when laptop ON)
│   ├── system-health.yml → GitHub Actions cloud health (when laptop OFF)
│   └── health-check.py → core diagnostics engine
│
├── Layer 3: Docker On-Demand Skill
│   ├── /docker skill → auto-starts Docker if needed, then runs command
│   └── docker-start.bat → starts Docker Desktop + waits for ready
│
├── Layer 4: Windows Startup Automation
│   ├── startup.bat → master startup (kills stale procs, starts monitors)
│   └── Shortcut in Windows Startup folder
│
└── Layer 5: New MCPs (free, no API key)
    ├── fetch MCP → web content fetching
    └── git MCP → extended git operations
```

---

## Component Designs

### 1. Crash Recovery Hooks
**Hook config location:** `C:/Users/shema/.claude/settings.json` (global) or `.claude/settings.local.json`

**Three hooks:**
- `PreCompact` — fires before Claude compacts context (50K tokens). Saves: timestamp, active project, last 20 tool calls, open files, incomplete TODOs, last user message
- `Stop` — fires when session ends cleanly. Saves final summary.
- `SessionStart` — fires on every session open. Reads backup, injects summary as context reminder.

**Backup file:** `projects/system-health/backup/session-backup.md`
**Backup script:** `projects/system-health/session-backup.py`

**What the backup contains:**
```markdown
# Session Backup — [timestamp]
## Last Active Project
## Last User Request
## Incomplete Tasks (from TODO log)
## Files Recently Modified
## Decisions Made This Session
## Resume Prompt (copy-paste to restart context)
```

### 2. System Health Agent

**`/health-check` skill** — runs on demand, parallel sub-checks:
- RAM: current usage, top memory hogs, available RAM
- CPU: usage%, throttling check
- Disk: space remaining on C:
- Docker: daemon running? MCP servers active?
- Internet: latency to Cloudflare/Google DNS
- Crash log: Windows Event Log last 24h critical errors
- Python procs: any runaway scripts?
- Startup impact: estimated startup time

**Output:** structured Telegram message + saved to `projects/system-health/logs/YYYY-MM-DD-health.md`

**GitHub Actions cloud version:** `system-health.yml`
- Runs 1x/day at 9AM AST
- Checks: API health (Telegram bot alive, Brave Search, CoinGecko, Kraken), GitHub Actions quota remaining, market-report job status
- Sends Telegram summary even when laptop is OFF

### 3. Docker On-Demand Skill (`/docker`)
**Behavior:**
1. Check if Docker daemon running (`docker ps`)
2. If NOT → start Docker Desktop, wait up to 60s for daemon
3. Execute requested Docker command
4. Return output

**No Docker running 24/7** — called only when needed, preserving RAM

### 4. Windows Startup Automation
**`startup.bat` does:**
1. Kill any hung `claude.exe` / `node.exe` processes from previous crash
2. Run quick health snapshot → save to logs
3. Start `price-alert.py` (crypto monitor)
4. Start `telegram-bridge.py` (Claude Haiku bot)
5. Log startup timestamp
6. Does NOT start Docker (on-demand only)

**Installation:** Shortcut placed in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`

### 5. New Free MCPs
| MCP | Command | Purpose |
|-----|---------|---------|
| fetch | `claude mcp add fetch npx -y @modelcontextprotocol/server-fetch` | Web content fetching without Playwright |
| git | `claude mcp add git uvx mcp-server-git` | Extended git — diff, log, annotate |

---

## Skills Inventory After This Build
| Skill | Type | Status |
|-------|------|--------|
| /research | Web search | ✅ Existing |
| /session-close | Session summary | ✅ Existing |
| /weekly-review | Memory refresh | ✅ Existing |
| /decision | Decision log | ✅ Existing |
| /remember | Save preference | ✅ Existing |
| /market-check | Crypto/stock prices | ✅ Existing |
| /project-update | README status | ✅ Existing |
| /voice-gen | ElevenLabs TTS | ✅ Existing |
| /prompt-gen | AI video/image prompts | ✅ Existing |
| /gemini | Gemini sub-agent | ✅ Existing |
| /kimi | Kimi K2.5 sub-agent | ✅ Existing |
| /email-check | Gmail search | ✅ Existing |
| /kraken | Kraken exchange | ✅ Existing |
| /health-check | System diagnostics | 🔨 NEW |
| /docker | Docker on-demand | 🔨 NEW |
| /backup | Manual session backup | 🔨 NEW |

---

## "Without Laptop" Strategy
| Component | Laptop ON | Laptop OFF |
|-----------|-----------|------------|
| Crash backup hooks | ✅ Active | N/A |
| /health-check skill | ✅ Full diagnostics | ❌ N/A |
| Cloud health check | ✅ Also runs | ✅ GitHub Actions |
| Market reports | ✅ Local + cloud | ✅ GitHub Actions |
| Telegram alerts | ✅ price-alert.py | ✅ GitHub Actions |
| Docker | ✅ On-demand | ❌ Requires local |

---

## Pro Dev Patterns Applied (2026 Best Practices)
- **Hooks as middleware** — inject behavior at lifecycle points, not in main code
- **Narrow-role agents** — each skill does ONE thing, composable
- **Cloud fallback** — critical jobs run on GitHub Actions (laptop-independent)
- **On-demand heavy tools** — Docker, Kimi, Gemini only called when needed
- **Parallel sub-agents** — health-check spawns concurrent checks (RAM, CPU, disk, net)
- **State persistence** — backup → restore pattern for crash resilience

---

## Implementation Order
1. Add fetch + git MCPs (2 commands)
2. Build session-backup.py + configure hooks
3. Build health-check.py + /health-check skill
4. Build /docker skill + docker-start.bat
5. Build startup.bat + install at Windows startup
6. Create GitHub Actions system-health.yml
7. Create system-health project README
8. Update CLAUDE.md + MEMORY.md
9. Commit everything

_Approved: 2026-03-12_
