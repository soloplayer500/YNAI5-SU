# Claude.ai Projects — YNAI5-SU Mobile Cowork Setup

## What This Is

A Claude.ai Project gives you a persistent Claude workspace with full YNAI5-SU context that you access from **any device** — phone, browser, anywhere. When you open this project on mobile and ask "what's my portfolio?" Claude fetches your live data from GitHub automatically.

This is the "cowork" layer — same Claude intelligence, same context, everywhere.

---

## Step 1 — Get Your GitHub Raw URLs

Your portfolio JSON is committed to GitHub every 30 minutes by GitHub Actions. Once your repo is pushed, these URLs give Claude live read access:

```
Portfolio data:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/projects/crypto-monitoring/kraken/kraken_portfolio.json

Memory index:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/memory/MEMORY.md

Preferences:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/memory/preferences.md

Current priorities:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/context/current-priorities.md
```

**Replace `YOUR_USERNAME/YOUR_REPO`** with your actual GitHub repo path.

---

## Step 2 — Create the Claude.ai Project

1. Open **claude.ai** in browser
2. Click **Projects** in the left sidebar
3. Click **+ New Project**
4. Name it: `YNAI5-SU`
5. Click **Set instructions** (or "Project instructions")
6. Paste the system prompt below (after filling in your GitHub URLs)
7. Save

---

## Step 3 — System Prompt to Paste

```
You are Ryn, Shami's personal AI assistant (YNAI5-SU workspace).

ABOUT SHAMI:
- Name: Shami (also Solo) | Location: Aruba (AST, UTC-4)
- AI Systems Builder — systems thinker, MVP first, infrastructure mindset
- Current focus: Crypto portfolio monitoring + social media automation pipeline
- Hardware: HP Laptop 15, 8GB RAM (upgrading to MacBook)

HOLDINGS (Kraken):
BTC (avg buy $90,111), ETH ($3,151), SOL ($151), OPN ($0.33), EIGEN ($0.30), BABY ($0.028)

LIVE PORTFOLIO DATA:
When asked about my portfolio, balances, holdings, P&L, or orders — fetch this URL and read the JSON:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/projects/crypto-monitoring/kraken/kraken_portfolio.json

MEMORY & PREFERENCES:
When asked about my preferences, past decisions, or workspace context:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/memory/MEMORY.md
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/memory/preferences.md

CURRENT PRIORITIES:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/context/current-priorities.md

PREDICTION ACCURACY:
https://raw.githubusercontent.com/soloplayer500/YNAI5-SU/master/projects/crypto-monitoring/kraken/performance.json

RESPONSE STYLE:
- Professional but friendly, no filler, high signal, structured headings
- On mobile: keep responses concise and scannable
- Challenge weak reasoning. MVP first. Actionable steps.
- Crypto analysis: reference actual current data, never invent prices

IMPORTANT: Data in the GitHub URLs is refreshed every 30 minutes by cloud automation. Always fetch fresh before answering portfolio questions.
```

---

## Step 4 — Mobile Access

1. Open the **Claude.ai app** on your phone
2. Tap **Projects** at the bottom
3. Select **YNAI5-SU**
4. Start chatting — you now have full YNAI5-SU context everywhere

### Example mobile queries that work:
- `"What's my portfolio right now?"` → Claude fetches the GitHub URL, parses JSON, shows balances
- `"What are my current priorities?"` → Claude reads current-priorities.md
- `"What have I decided about crypto recently?"` → Claude reads MEMORY.md
- `"Is BTC a good buy right now based on my holdings?"` → Claude combines live data + your avg buy prices

---

## Step 5 — How It Stays Fresh (Automatic)

```
GitHub Actions (every 30min, cloud)
    → runs portfolio_monitor.py
    → commits kraken_portfolio.json to repo
    → raw GitHub URL is always fresh data

Claude.ai Project (mobile)
    → fetches the same raw GitHub URL on demand
    → reads your live portfolio instantly
```

No laptop needed. No manual updates. Just ask.

---

## Cross-Chat Memory (Telegram ↔ Claude Desktop)

Your Telegram conversations with Ryn (via @SoloClaude5_bot) are logged to:
```
projects/crypto-monitoring/telegram-sessions/YYYY-MM-DD.json
```

These get committed to GitHub when the portfolio syncs. On Claude Code desktop:
- Read recent session files to see what was discussed on mobile
- Key decisions get logged to `memory/MEMORY.md`

**To save something important from Telegram directly:**
```
/memory I want to buy more SOL if it drops below $120
```
This appends directly to `memory/MEMORY.md` — synced to GitHub — visible in Claude.ai Project.

---

## What's NOT Possible Yet (Roadmap)

| Feature | Status |
|---------|--------|
| Claude.ai Projects (read GitHub URLs) | ✅ Works now (Pro plan) |
| Telegram `/portfolio` command | ✅ Works (when laptop is on) |
| GitHub Actions auto-sync (no laptop) | ✅ Works 24/7 |
| Claude mobile MCP tool calls | 🔜 On Anthropic roadmap |
| Claude mobile executing trades | 🔜 Phase 10 (after 70% accuracy) |
| Claude.ai seeing Telegram sessions in real-time | 🔜 Would need a webhook bridge |

---

## Troubleshooting

**"I can't fetch the URL"** — The repo `soloplayer500/YNAI5-SU` is private. Go to GitHub → Settings → Change visibility → Make public. Raw GitHub URLs only work on public repos. Claude.ai cannot access private repos.

**"Data is old"** — GitHub Actions runs every 30 min. If the workflow is failing, check the Actions tab on GitHub.

**"Claude doesn't know about my portfolio"** — Make sure you're chatting inside the `YNAI5-SU` Project, not a regular chat.
