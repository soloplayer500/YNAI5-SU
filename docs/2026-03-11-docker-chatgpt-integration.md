# Docker + ChatGPT Pro Integration Strategy
Date: 2026-03-11
Topics: Docker containerization for YNAI5 automation | ChatGPT Pro API integration

---

## TOPIC 1: Docker for YNAI5 Automation

### Overview
Docker lets you run Python services (Telegram bot, price alert monitor, market reporter, content scheduler) as isolated, auto-restarting containers managed by a single `docker-compose.yml`. The system becomes "always alive" — containers restart on crash, run on boot, and communicate internally without exposing ports to the internet.

---

### Hardware Feasibility Assessment
**Machine:** HP Laptop 15, AMD Ryzen 5 5500U, 8GB RAM, Windows 11, integrated GPU only

| Factor | Status | Notes |
|--------|--------|-------|
| RAM | Tight but workable | Docker Desktop WSL2 backend uses ~600MB idle. 4 lightweight Python containers = ~200–400MB total. Total overhead stays under 1.5GB if containers are slim. |
| CPU | Fine | Ryzen 5 5500U handles Python containers easily. No GPU needed. |
| Storage | Fine | Python Alpine images = 50–150MB each. Total stack < 1GB. |
| Network | Fine | All containers use internal Docker network + outbound API calls. |

**RAM Budget (conservative):**
```
Windows 11 + background apps:     ~4.0 GB
Docker Desktop WSL2 backend:       ~0.6 GB
4 Python containers combined:      ~0.4 GB
Browser / Claude Code open:        ~1.5 GB
Headroom buffer:                   ~1.5 GB
TOTAL:                             ~8.0 GB ✅ (tight but feasible)
```

**Key constraint:** Set Docker Desktop WSL2 memory limit to 1.5GB in `.wslconfig` to prevent Docker from consuming all RAM.

---

### Docker Desktop for Windows — Setup

**Installation path:** Docker Desktop → WSL2 backend (NOT Hyper-V) — better performance on Windows 11.

**WSL2 memory limit (critical for 8GB machine):**
Create `C:\Users\shema\.wslconfig`:
```ini
[wsl2]
memory=1536MB
processors=2
swap=0
```

**Docker Desktop settings to tune:**
- Resources → Advanced → Memory: 1536MB
- Enable "Start Docker Desktop on login" for always-on containers
- Use WSL2-based engine (default on Windows 11)

---

### Recommended Container Architecture

#### Container 1: `market-report` (Priority: HIGH)
**What it does:** Runs `market-report.py` on schedule (8AM, 6PM, 9PM AST). Replaces Windows Task Scheduler.
**Base image:** `python:3.11-alpine`
**RAM:** ~80–100MB
**Dependencies:** requests, ccxt, python-telegram-bot, google-generativeai
**Schedule:** Cron job inside container OR use a cron sidecar

#### Container 2: `monitor-loop` (Priority: HIGH)
**What it does:** Runs `monitor-loop.py` — 15-minute heartbeat, threshold alerts, big move detection.
**Base image:** `python:3.11-alpine`
**RAM:** ~60–80MB
**Key property:** `restart: always` — recovers from crashes without Windows Task Scheduler

#### Container 3: `telegram-bridge` (Priority: MEDIUM)
**What it does:** Runs the Telegram-Claude bridge bot (@SoloClaude5_bot). Handles incoming Telegram messages, routes to Claude Haiku (or GPT-4o with /gpt command — see Topic 2).
**Base image:** `python:3.11-alpine`
**RAM:** ~80–100MB
**Key property:** Long-polling Telegram API — must stay alive 24/7.

#### Container 4: `content-scheduler` (Priority: LOW — future)
**What it does:** Manages content idea queue, triggers prompt generation, logs to content-tracker.
**Base image:** `python:3.11-alpine`
**RAM:** ~50–70MB
**Status:** Build when content pipeline is active.

---

### Inter-Container Communication

**Method 1: Shared volumes (simplest — recommended for YNAI5)**
Mount a shared folder that all containers can read/write:
```yaml
volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      device: C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/crypto-monitoring/logs
      o: bind
```
Use case: `monitor-loop` writes alerts to a JSON file → `telegram-bridge` reads it and fires Telegram message.

**Method 2: Docker internal networking (for direct HTTP calls)**
All containers on the same `docker-compose` network can call each other by container name:
```
http://monitor-loop:8080/status
http://market-report:8080/trigger
```
Expose a tiny Flask health endpoint if needed. Not required for MVP.

**Method 3: Redis as message queue (overkill for now)**
`redis:alpine` image (~30MB) as a pub/sub broker. Skip unless traffic becomes complex.

**Recommendation:** Start with shared volumes (zero complexity). Add Redis only if containers need real-time signaling.

---

### Docker Compose — Full YNAI5 Stack

Save as `C:\Users\shema\OneDrive\Desktop\YNAI5-SU\docker-compose.yml`:

```yaml
version: "3.9"

services:

  market-report:
    build: ./projects/crypto-monitoring
    container_name: ynai5-market-report
    restart: unless-stopped
    env_file:
      - .env.local
    volumes:
      - ./projects/crypto-monitoring/logs:/app/logs
    command: python market-report-scheduler.py
    mem_limit: 150m
    cpus: 0.5

  monitor-loop:
    build: ./projects/crypto-monitoring
    container_name: ynai5-monitor-loop
    restart: always
    env_file:
      - .env.local
    volumes:
      - ./projects/crypto-monitoring/logs:/app/logs
    command: python monitor-loop.py
    mem_limit: 120m
    cpus: 0.5

  telegram-bridge:
    build: ./projects/crypto-monitoring
    container_name: ynai5-telegram-bridge
    restart: always
    env_file:
      - .env.local
    volumes:
      - ./projects/crypto-monitoring/logs:/app/logs
    command: python telegram-bridge.py
    mem_limit: 150m
    cpus: 0.5

networks:
  default:
    name: ynai5-network
```

**One command to start everything:**
```bash
docker compose up -d
```

**Check status:**
```bash
docker compose ps
docker compose logs -f telegram-bridge
```

**Stop everything:**
```bash
docker compose down
```

---

### Dockerfile Template for Python Services

Place in `projects/crypto-monitoring/Dockerfile`:
```dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "monitor-loop.py"]
```

**Alpine vs slim:** Use `python:3.11-alpine` (50MB) over `python:3.11-slim` (130MB) for tightest RAM footprint.

---

### Market Report Scheduler in Docker

Current setup uses Windows Task Scheduler (3 tasks at 8AM, 6PM, 9PM). Docker replacement options:

**Option A: APScheduler inside Python script (recommended)**
```python
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

scheduler = BlockingScheduler(timezone=pytz.timezone('America/Aruba'))
scheduler.add_job(run_report, 'cron', hour=8, minute=0)
scheduler.add_job(run_report, 'cron', hour=18, minute=0)
scheduler.add_job(run_report, 'cron', hour=21, minute=0)
scheduler.start()
```
The container runs this script as its main process. Docker's `restart: always` handles crashes.

**Option B: Cron inside container**
Add cron to Alpine image and use a `crontab` file. More complex, same result.

**Recommendation:** APScheduler (Option A) — pure Python, simpler, easier to debug.

---

### Docker vs Windows Task Scheduler — Verdict

| Feature | Windows Task Scheduler | Docker |
|---------|----------------------|--------|
| Auto-restart on crash | No | Yes (restart: always) |
| Isolated environment | No (uses system Python) | Yes |
| Multi-service management | Manual (3+ tasks) | One command |
| Logs centralized | Scattered files | `docker logs` or volume |
| Boot persistence | Yes (Task Scheduler) | Yes (Docker Desktop auto-start) |
| RAM overhead | Zero | ~600MB (WSL2 backend) |
| Complexity | Low | Medium |

**Verdict:** Docker wins for always-on reliability, but costs 600MB RAM on boot. Given 8GB machine, this is acceptable. Recommend migrating monitor-loop and telegram-bridge to Docker first (they must stay alive 24/7). Keep market-report in Task Scheduler until Docker setup is stable.

---

### Migration Roadmap

**Phase 1 (Now — 1 day):** Docker Desktop installed, WSL2 memory capped at 1.5GB, Dockerfile for crypto-monitoring written.

**Phase 2 (This week):** Migrate monitor-loop + telegram-bridge to Docker. Keep Task Scheduler for market-report as backup. Test `docker compose up -d` restart behavior.

**Phase 3 (When content pipeline active):** Add content-scheduler container. Full YNAI5 ecosystem running as Docker stack.

---
---

## TOPIC 2: ChatGPT Pro Integration

### Context
Shami has an active **ChatGPT Pro subscription** ($200/month). This is separate from the OpenAI API. The goal is to understand what Pro unlocks for automation and how GPT-4o fits into the YNAI5 multi-AI stack.

---

### ChatGPT Pro Subscription vs OpenAI API — Key Distinction

| Aspect | ChatGPT Pro ($200/mo) | OpenAI API (separate billing) |
|--------|----------------------|-------------------------------|
| Access | UI at chat.openai.com | REST API calls from code |
| Models | GPT-4o, o1, o3, Sora (web UI) | GPT-4o, GPT-4o-mini, o1, o3 (via API) |
| Cost model | Flat $200/month, unlimited in UI | Pay-per-token (no subscription required) |
| Automation | No — web UI only | Yes — full programmatic access |
| Sora | Yes — unlimited in Pro UI | Separate API credits (pay-per-second) |
| Sharing with bots | No — Pro is for your personal account | Yes — API key powers bots and scripts |

**Critical point:** ChatGPT Pro does NOT give you free API access. You need a separate OpenAI API account with billing enabled to make API calls. However, creating an API account is free — you only pay for what you use.

---

### GPT-4o API Pricing (as of knowledge cutoff, ~mid-2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|-----------------------|------------------------|-------|
| GPT-4o | $5.00 | $15.00 | Full model, multimodal |
| GPT-4o (cached input) | $2.50 | $15.00 | 50% discount on repeated context |
| GPT-4o-mini | $0.15 | $0.60 | Cheapest, good for high-volume |
| o1 | $15.00 | $60.00 | Reasoning model, expensive |
| o3-mini | $1.10 | $4.40 | Balanced reasoning |

**YNAI5 cost estimate for Telegram bot (GPT-4o-mini):**
- Average conversation: ~500 input tokens + 300 output tokens = 800 tokens total
- Cost per conversation: ~$0.000075 per message (GPT-4o-mini)
- 100 conversations/day = ~$0.0075/day = ~$0.23/month
- Effectively free for personal use.

**YNAI5 cost estimate for Telegram bot (GPT-4o full):**
- Same volume: ~$0.015/day = ~$0.45/month. Still trivial.

**Recommendation:** Use GPT-4o-mini for Telegram bot routing (cost ~zero), reserve GPT-4o full for tasks requiring vision, nuanced reasoning, or long context.

---

### Sora API — Current Status

Based on existing workspace research (2026-03-09):
- **Sora API is live** — endpoint: `POST https://api.openai.com/v1/videos/generations`
- **Models:** `sora-2` (fast) | `sora-2-pro` (high quality)
- **Access:** Requires OpenAI API key + API credits — SEPARATE from Pro subscription
- **Cost:** ~$0.01–$0.03/second of video generated → 8-sec clip ≈ $0.08–$0.24
- **ChatGPT Pro UI:** Unlimited Sora generations free within Pro subscription (manual only)
- **Automation verdict:** Must use API key + credits for automated `/sora-gen` skill. Pro sub doesn't help here.

**Best path:** Use Pro UI for manual Sora batches now. Build `/sora-gen` API skill when content pipeline is active and you want full automation.

---

### What ChatGPT Pro Uniquely Offers vs Claude

| Feature | ChatGPT Pro | Claude (Sonnet 4.6) |
|---------|-------------|---------------------|
| Sora video generation (free in UI) | YES | No native video |
| DALL-E image generation | YES (unlimited in UI) | No native images |
| GPT-4o reasoning | YES | Claude Sonnet 4.6 comparable |
| Code Interpreter (data analysis) | YES | Limited |
| Advanced Voice Mode | YES | No voice mode |
| o1/o3 reasoning models | YES (in UI) | No o-series |
| Long context (200K+) | Comparable | 200K tokens |
| MCP tool access | YES (Jan 2026) | YES (already using) |
| API for automation | SEPARATE billing | SEPARATE billing |

**Verdict:** Pro subscription is most valuable for Sora and DALL-E (free unlimited image/video in UI). For text tasks, Claude + Haiku covers everything at lower cost.

---

### Multi-AI Telegram Bot — /claude and /gpt Commands

**Concept:** Single Telegram bot (@SoloClaude5_bot) routes to different AI backends based on command prefix.

**Architecture:**
```
User → Telegram message
         │
         ▼
   telegram-bridge.py
         │
    ┌────┴────┐
    │ route   │
    └────┬────┘
         │
   /claude → Claude Haiku API (claude-haiku-4-5)
   /gpt    → GPT-4o-mini API (OpenAI API key)
   /gemini → Gemini Flash API (Google API key)
   /kimi   → Kimi K2.5 API (OpenRouter key)
   [none]  → default to Claude Haiku
```

**Implementation pattern:**

```python
async def handle_message(update, context):
    text = update.message.text.strip()

    if text.startswith('/gpt '):
        prompt = text[5:]
        response = call_openai(prompt)
    elif text.startswith('/gemini '):
        prompt = text[8:]
        response = call_gemini(prompt)
    elif text.startswith('/kimi '):
        prompt = text[6:]
        response = call_kimi(prompt)
    elif text.startswith('/claude ') or not text.startswith('/'):
        prompt = text.replace('/claude ', '', 1)
        response = call_claude(prompt)
    else:
        response = "Commands: /claude /gpt /gemini /kimi"

    await update.message.reply_text(response)
```

**Required env vars in .env.local:**
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=...
```

**Cost per command (approximate):**
- `/claude` (Haiku): ~$0.0005/message
- `/gpt` (4o-mini): ~$0.00008/message
- `/gemini` (Flash): ~$0.000075/message (or free tier)
- `/kimi` (K2.5): ~$0.0002/message

All effectively free at personal usage volume.

---

### OpenAI API Setup (if not already done)

1. Go to `platform.openai.com` → create account (separate from ChatGPT Pro login, or link same email)
2. Add billing: Settings → Billing → Add payment method
3. Generate API key: API Keys → Create new secret key
4. Add to `.env.local` as `OPENAI_API_KEY=sk-...`
5. Set usage limit: $5–10/month hard cap to prevent surprises

**Note:** OpenAI API and ChatGPT Pro are billed separately. Pro is $200/month flat. API is pay-per-token.

---

### Integration Priority Matrix

| Integration | Value | Effort | Priority |
|-------------|-------|--------|----------|
| GPT-4o-mini in Telegram bot (/gpt) | High | Low | DO NOW |
| Sora via Pro UI (manual) | High | Zero | Already possible |
| OpenAI MCP server for Claude | Medium | Low | Nice-to-have |
| /sora-gen automated skill | High | Medium | Build with content pipeline |
| o1/o3 for deep research | Medium | Low | Add to /gpt routing |
| DALL-E for image generation | Medium | Low | Add later |

---

### Recommended Action Sequence

**Immediate (today):**
1. Get OpenAI API key at `platform.openai.com/api-keys`
2. Add `OPENAI_API_KEY` to `.env.local`
3. Upgrade telegram-bridge.py to support `/gpt` + `/claude` routing
4. Set $10/month API spending cap

**This week:**
5. Set up Docker Desktop with WSL2 memory limit
6. Containerize monitor-loop + telegram-bridge
7. Test `docker compose up -d` — verify restart-on-crash behavior

**When content pipeline active:**
8. Build `/sora-gen` skill for automated video generation
9. Add content-scheduler Docker container
10. Add DALL-E image generation endpoint

---

## Combined Architecture Vision

```
YNAI5 Docker Stack (docker-compose.yml)
├── ynai5-telegram-bridge    ← routes /claude, /gpt, /gemini, /kimi
├── ynai5-monitor-loop       ← 15min crypto heartbeat, threshold alerts
├── ynai5-market-report      ← 8AM/6PM/9PM scheduled AI reports
└── ynai5-content-scheduler  ← (future) content idea queue

All containers:
- Share ./logs volume for cross-container data
- Read from .env.local for API keys
- restart: always (survive crashes + reboots)
- Total RAM: ~400MB combined
```

---

## Summary — Top Action Items

### Docker (do first):
1. Install Docker Desktop, set WSL2 memory limit to 1536MB in `.wslconfig`
2. Write `Dockerfile` in `projects/crypto-monitoring/` using `python:3.11-alpine`
3. Write `docker-compose.yml` at workspace root with monitor-loop + telegram-bridge services
4. Migrate monitor-loop to Docker (most critical — must stay alive 24/7)
5. Test restart behavior: `docker compose down && docker compose up -d`

### ChatGPT Pro / OpenAI API (do in parallel):
1. Get OpenAI API key — `platform.openai.com/api-keys`
2. Add to `.env.local` as `OPENAI_API_KEY`, set $10/month hard cap
3. Add `/gpt` command routing to telegram-bridge.py (30-min task)
4. Continue using ChatGPT Pro UI for free Sora video batches
5. Plan `/sora-gen` skill for when content pipeline is built
