# RYN — Systems Map

_What runs where. One page. No fluff._

Last Updated: 2026-04-24

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1 — LOCAL (RYN / HP Laptop 15 / Aruba)                │
│  Role: Execution relay, NOT a runtime host                   │
│                                                              │
│  • Claude Code         ← primary AI driver                  │
│  • ryn/brain/ state    ← read/write local brain             │
│  • Git repo            ← source of truth                     │
│  • .env.local          ← secrets (gitignored)                │
│  • RAG index           ← 674 chunks, 50 files                │
└─────────────────────────────────────────────────────────────┘
           │ git push / ssh / gh workflow run
           ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 2 — CLOUD (GitHub + GCP VM)                            │
│                                                              │
│  GitHub Actions (scheduled + manual):                        │
│  • daily-tasks.yml             ✅ LIVE 9AM + 3PM AST         │
│  • vm-sync.yml                 ✅ LIVE on push               │
│  • system-health.yml           ✅ LIVE 9AM AST               │
│  • ynai5-vm-health.yml         ✅ LIVE                       │
│  • health-monitor-deploy.yml   ✅ LIVE                       │
│  • drive-heartbeat.yml         ✅ LIVE                       │
│  • screener-bot.yml            ⏸ PAUSED (2026-04-16)         │
│  • market-report.yml           ⏸ PAUSED (2026-03-29)         │
│  • morning-briefing.yml        ⏸ PAUSED (2026-03-29)         │
│  • portfolio-sync.yml          ⏸ PAUSED (2026-03-29)         │
│  • niche-research.yml          status unclear                │
│  • niche-approve.yml           status unclear                │
│  • ralph-automation.yml        Mon/Wed/Fri 10AM AST          │
│                                                              │
│  VM (34.45.31.188, GCP e2-micro, Ubuntu 24):                 │
│  • ynai5-dashboard (FastAPI :8000)    ✅ active              │
│  • ynai5-gemini    (worker)           ✅ active              │
│  • ynai5-claude    (runner)           ✅ active              │
│  • ynai5-drive     (rclone mount)     ✅ active              │
│  • ynai5-monitor   (crypto alerts)    ✅ active              │
│  • ynai5-heartbeat (60s loop)         ✅ active              │
│  • ynai5-commander (Telegram CLI)     ✅ active (v2)         │
│  • nginx           (reverse proxy)    ✅ active              │
│  • n8n             (port 5678)        ⚠ UNUSED              │
│  • Ollama          (phi3:mini)        ⏸ disabled (RAM)      │
└─────────────────────────────────────────────────────────────┘
           ▲                          ▲
           │ heartbeat alerts         │ /status /logs /restart
           │                          │
┌─────────────────────────────────────────────────────────────┐
│  TIER 3 — CONTROL (Telegram + External APIs)                 │
│                                                              │
│  • @SoloClaude5_bot (user 8569520396)                        │
│    - Heartbeat alerts: RAM/disk/load/log-size/service-down   │
│    - Commander: /status, /logs, /restart <svc>, /snapshot    │
│                                                              │
│  • @BlockSyndicate_bot (free channel -1003860200579)         │
│  • @BlockSyndicatevip_bot (VIP channel -1003689725571)       │
│                                                              │
│  External:                                                   │
│  • Kraken API (trading + portfolio)                          │
│  • CoinGecko (prices, free tier)                             │
│  • Gemini API (1500/day free)                                │
│  • Anthropic API (~$10/mo, Claude Haiku)                     │
│  • OpenRouter (Kimi K2, ~$0.0002/call)                       │
│  • ElevenLabs (TTS, 10K chars/mo free)                       │
│  • Brave Search (2000/mo free)                               │
│  • Pexels (free stock footage)                               │
│  • Kling AI (paused — payday gate)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
User intent
  → Claude Code (Tier 1)
  → reads ryn/brain/state.json + priority_stack.md
  → routes via ryn/runtime/task_router.py:
       • SSH → VM (Tier 2)
       • local → Python script
       • GitHub → gh workflow run
       • skill → Claude executes
       • telegram → user sends to bot (Tier 3)
```

---

## Alert Conditions (VM Heartbeat)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Service down | `systemctl is-active != active` | Telegram alert, auto-restart attempt |
| RAM critical | < 100MB free | Telegram alert |
| CPU load spike | 1-min avg > 2.0 | Telegram alert |
| Log oversized | any log > 20MB | Telegram alert |
| Disk > 90% | df percentage | Telegram alert |

All alerts dedupe via `alert.state` file — fire once on breach, once on recovery.

---

## Repo Structure (Stable)

```
YNAI5-SU/
├── CLAUDE.md                           master config
├── ryn/
│   ├── brain/       ← state + priorities + memory (committed .md, gitignored runtime)
│   ├── framework/   ← think.md, build.md, context.md, skills.md, memory.md
│   ├── runtime/     ← scheduler.py, task_router.py, heartbeat_actions.py, telegram_tasks.py
│   ├── profit/      ← income_map.md, trading_system.md, monetization_ideas.md
│   ├── ryn-core/    ← rag_indexer.py
│   ├── ryn-vm/      ← commander.py (reference copy of VM deployment)
│   ├── ryn-local/   ← [empty placeholder — candidate for deletion]
│   └── legacy/      ← [empty placeholder — candidate for deletion]
├── projects/        ← passive-income, crypto-monitoring, vm-dashboard, niche-research, ralph-automation, etc.
├── .claude/
│   ├── skills/      ← 30+ custom Claude skills
│   ├── settings.json
│   └── rules/       ← decisions, projects, sessions rules
├── .github/workflows/  ← 13 GitHub Actions (6 live, 4 paused, 3 unclear)
├── context/         ← profile.md, current-priorities.md, goals.md
├── memory/          ← MEMORY.md, preferences.md, patterns.md, decisions-log.md
├── docs/            ← claude-docs + research + knowledge graphs
├── sessions/        ← 7 session summaries
├── actions/         ← 2 active items (next-session-startup, passive-income-week1)
├── archive/         ← archived stale files
└── playbooks/       ← SOP playbooks
```

---

## Known Weak Points

1. **n8n unused** — installed on VM, consuming RAM, zero value being captured
2. **4 revenue workflows paused** — screener, market-report, morning-briefing, portfolio-sync
3. **Gumroad missing** — no payment gate → no paid conversions possible
4. **Kraken dust positions** — 4–5 tokens under $5 each, add noise, consider sweep
5. **RAM swap engaged on VM** — 778MB swap used of 1GB, stable but tight
6. **No Fiverr listings** — ready-to-sell scripts have no marketplace presence

---

## Maintenance Triggers

- **New doc added →** run `python ryn/ryn-core/rag_indexer.py --index`
- **VM alert fires →** check Telegram, run `/status`, run `/logs`
- **Disk > 80% on VM →** run log cleanup, check snap revisions
- **Session ends →** run `/session-close`, push to GitHub
