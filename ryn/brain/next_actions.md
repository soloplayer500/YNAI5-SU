# RYN — Next Actions

_Single ranked queue. Top item = do first._

Last Updated: 2026-04-24

---

## Queue (ranked by ROI × Speed)

### 🟢 READY TO EXECUTE — This Week

| # | Action | Time | Revenue Impact |
|---|--------|------|----------------|
| 1 | **Unpause `screener-bot.yml`** → restore cron `0 12 * * *` (8AM AST) | 5 min | Daily signals restart → subscriber magnet |
| 2 | **Unpause `morning-briefing.yml`** → restore cron `0 13 * * *` (9AM AST) | 5 min | Daily portfolio intel resumes |
| 3 | **Unpause `portfolio-sync.yml`** → restore cron `0 13 * * *` (9AM AST) | 5 min | Kraken state stays fresh for trading decisions |
| 4 | **Set up Gumroad product** — "Block Syndicate Daily Signals" $9.99/mo | 10 min (USER) | ENABLES first paid conversion |
| 5 | **Draft 5 Reddit signal posts** (Claude generates) for r/CryptoCurrency, r/SatoshiStreetBets | 30 min | Drive traffic to free channel |
| 6 | **Draft 3 X/Twitter threads** about daily signals | 20 min | Audience growth |
| 7 | **Create Fiverr gig #1**: "Custom Telegram price alert bot" $75–150 | 45 min | Alternate revenue stream |

### 🟡 NEXT (Week 2)

| # | Action | Time | Why |
|---|--------|------|-----|
| 8 | **Wire n8n on VM** — connect Gemini worker + Claude runner | 2 hrs | Unlock visual orchestration for complex workflows |
| 9 | **Create Fiverr gig #2**: GitHub Actions automation setup $50–100 | 45 min | More orders |
| 10 | **Create Fiverr gig #3**: Crypto portfolio monitor + Telegram report $100–200 | 45 min | Higher ticket |
| 11 | **Sweep Kraken dust** — sell tokens under $5, redeploy to BTC | 15 min | Clean portfolio |

### 🔵 LATER (Week 3+)

| # | Action | Condition |
|---|--------|-----------|
| 12 | Enable Ollama + wire phi3 into chat_server.py | After VM upgrade to e2-small |
| 13 | VM upgrade e2-micro → e2-small ($13/mo) | After first $100 revenue |
| 14 | Launch Beehiiv newsletter | After 100 Telegram subs |
| 15 | Package GitHub template product ($29–99) | After screener stable 30 days |
| 16 | Build signals API (FastAPI) | After 70% prediction accuracy |

### ⏸ PAUSED (Hardware / Capital Gate)

- Video pipeline (Kling AI + Sora) — resume when hardware upgraded
- Suno / Distrokid YouTube music — low ROI right now
- Open WebUI full setup — not needed until VM upgrade
- Any new infrastructure builds

---

## Exact Next Step (Right Now)

**Unpause 3 GitHub workflows (15 min total).**

Files to edit:
- `.github/workflows/screener-bot.yml`
- `.github/workflows/morning-briefing.yml`
- `.github/workflows/portfolio-sync.yml`

Change `on:` block from:
```yaml
on:
  workflow_dispatch:
```
To:
```yaml
on:
  schedule:
    - cron: '0 12 * * *'   # or '0 13 * * *' for morning briefing / portfolio
  workflow_dispatch:
```

Then: `git add .github/workflows/ && git commit -m "chore: unpause revenue workflows" && git push`

Verify at: https://github.com/soloplayer500/YNAI5-SU/actions

---

## Don't Do These (Time Wasters Right Now)

- Rebuilding working systems
- Building new infrastructure before $100 revenue
- Polishing folder aesthetics
- Adding new skills before existing ones generate revenue
- Trading on low-conviction setups (<65% confidence)
- Averaging down more than once on losing positions
