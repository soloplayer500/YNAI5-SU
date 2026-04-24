# Local Machine Role — RYN
_Defines what runs locally vs on VM vs via repo._

Last Updated: 2026-04-24

---

## Device Identity

**RYN** = HP Laptop 15 (AMD Ryzen 5 5500U, 8GB RAM, Aruba/AST)
- Execution relay — Claude Code interface
- NOT a runtime host
- NOT a 24/7 server

---

## What Runs Locally

| Component | Status | Notes |
|-----------|--------|-------|
| Claude Code | ACTIVE | Primary AI execution engine |
| ryn/brain/ | READ/WRITE | Local brain state (gitignored runtime, md committed) |
| ryn/ryn-core/rag_indexer.py | ON DEMAND | Rebuild index when new docs added |
| Git repo (YNAI5-SU) | ACTIVE | Source of truth — push to GitHub |
| .env.local | ACTIVE | Local API keys (never committed) |

---

## What Runs on VM (24/7)

| Component | Path | Role |
|-----------|------|------|
| ynai5-dashboard | FastAPI :8000 | API + web UI |
| ynai5-gemini | /ynai5_runtime/scripts/ | Gemini worker |
| ynai5-claude | /ynai5_runtime/scripts/ | Claude runner |
| ynai5-drive | rclone | Google Drive mount |
| ynai5-monitor | /ynai5_runtime/scripts/ | Crypto alerts |
| nginx | :80/:443 | Reverse proxy |
| **ynai5-heartbeat** | ~/ynai5-agent/ | 60s system monitoring |
| **ynai5-commander** | ~/ynai5-agent/ | Telegram command handler |

---

## What Runs via GitHub Repo

| Workflow | File | Trigger |
|----------|------|---------|
| VM auto-deploy | vm-sync.yml | Push to master |
| Morning briefing | market-report.yml | 9AM + 3PM AST cron |
| Portfolio monitor | portfolio-monitor.yml | Every 30min |
| System health | system-health.yml | Daily 9AM AST |

---

## Interaction Model

```
User → Telegram bot → ynai5-commander (VM) → shell/systemd
User → Claude Code (RYN) → SSH → VM
User → Claude Code (RYN) → git push → GitHub Actions → VM
Claude Code (RYN) → reads ryn/brain/ → informed decisions
```

---

## Local Constraints

- 8GB RAM — no local AI servers, no Docker daemons
- No ComfyUI running unless explicitly needed (closes after use)
- No price-alert.py or telegram-claude-bridge.py loops (moved to VM)
- No heavy cron jobs locally — use GitHub Actions instead
- No storing runtime state locally (goes to ryn/brain/ gitignored OR VM logs)

---

## Local Start Checklist (each session)

1. Claude Code opens → reads CLAUDE.md → checks current-priorities.md
2. RAG index valid? → if stale: `python ryn/ryn-core/rag_indexer.py --index`
3. Pull latest: `git pull origin master`
4. Check brain: `cat ryn/brain/state.json` for known VM state
5. SSH to VM if needed (key at ~/.ssh/google_compute_engine)

---

## Files NEVER run locally

- Any 24/7 monitoring loops
- Any Telegram bot polling loops
- Any database servers
- Any video generation (cloud-only via Kling API or Sora)
