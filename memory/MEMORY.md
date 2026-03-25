# Memory Index
_Claude auto-updates this file. Keep under 200 lines. Overflow goes to topic files._

Last Updated: 2026-03-22 (Session 13)

---

## Key Learnings
- [2026-03-09] Workspace initialized: YNAI5-SU with full folder architecture, 5 projects, 7 skills
- [2026-03-09] Hardware constraint confirmed: integrated GPU only — NO local video generation. Cloud-only pipeline.
- [2026-03-09] Gemini model naming: use `gemini-flash-latest` (not `gemini-2.0-flash` — quota 0 error)
- [2026-03-09] OPN verdict: 6/10, real project, wrong entry timing at $0.31, watch $0.15–$0.20
- [2026-03-09] Both API keys (ElevenLabs + Gemini) appeared in chat — MUST be regenerated
- [2026-03-10] Claude API upgrades reviewed — 15 docs categorized. Tier 1 (paid, skip) = prompt caching, effort, adaptive thinking. Tier 3 (free) = prompting strategies applied to skills.
- [2026-03-10] MCP servers: two types — Claude Code config (no API key, use `claude mcp add`) vs. API-based connector (needs API key, skip). Gmail + Playwright already connected.
- [2026-03-10] Best candidates to add next: Brave Search MCP (2000 searches/month free) + GitHub MCP (free with token)
- [2026-03-10] Anti-hallucination rules applied to /research and /market-check SKILL.md files
- [2026-03-10] Decision: skip Anthropic API key features for now — not paying extra until revenue starts
- [2026-03-10] Brave Search MCP added to Claude Code — 2000 free searches/month (key in .env.local)
- [2026-03-10] Telegram bot created (ID: 8420532120) — price-alert.py wired for 24/7 Telegram notifications
- [2026-03-10] Windows Task Scheduler activated — YNAI5-CryptoAlert runs 8AM + 10PM daily
- [2026-03-10] Telegram LIVE: personal chat ID 8569520396 (bot: @SoloClaude5_bot) — alerts confirmed working
- [2026-03-10] market-report.py built — CoinGecko + Kraken + Brave News + Gemini AI + Telegram, 3x/day
- [2026-03-10] Task Scheduler: 3 tasks — YNAI5-Report-Morning(8AM), Evening(6PM), Night(9PM)
- [2026-03-10] SECURITY: Regenerate Brave API keys (both) + Telegram bot token — all were shared in chat
- [2026-03-10] BTC market structure explained: reserve asset → institutional flow → amplification effect → capital rotation cycle
- [2026-03-10] Amplification effect: alts move 2–5x BTC % moves (liquidity math — small cap pool vs BTC ocean)
- [2026-03-10] NotebookLM study doc created: docs/2026-03-10-crypto-market-dynamics.txt (10 sections + portfolio applied)
- [2026-03-10] Kimi K2.5 researched — Moonshot AI, open-source, agent swarms (PARL, 100 parallel sub-agents), 256K context, $0.45/M input via OpenRouter. /kimi skill created.
- [2026-03-10] market-report.py v2 — RSI from Kraken OHLC (free), better section order, visual separators
- [2026-03-10] monitor-loop.py created — 15min heartbeat, threshold+big-move alerts, no Docker needed
- [2026-03-10] OpenRouter API key added — OPENROUTER_API_KEY in .env.local. Kimi K2.5 tested LIVE ✅ ($0.0002/call)
- [2026-03-10] API key input method: open Notepad .txt on Desktop, user pastes key there — never in chat
- [2026-03-22] /learn skill created — 6 modes: plan, cheatsheet, quiz, ladder, resources, feynman
- [2026-03-22] /macro-impact skill created — McKinsey macro assessment for portfolio impact analysis
- [2026-03-22] Higgsfield vs Kling verdict: KLING AI WINS — $6.99/mo Standard, 4.4x more videos, mcp-kling Claude Code integration, 1-3 min gen speed
- [2026-03-22] Video gen upgrade: buy Kling AI Standard + add mcp-kling MCP on payday 2026-03-27
- [2026-03-22] BTC symbol bug confirmed FIXED already — XXBT → BTC via KRAKEN_DISPLAY_SYMBOL dict
- [2026-03-22] Anthropic API credits LOW — top up $10 on payday (Telegram bridge + AI analyst breaking)
- [2026-03-22] /stock-analyze skill created — @BetterWaveFinance 9-dimension framework (Business Model, Value Creation, Capital Intensity, Balance Sheet, Management, SBC, Guidance, Optionality, Risks → BUY/HOLD/AVOID)
- [2026-03-22] Block Syndicate Telegram screener LIVE — VIP (-1003689725571) + Free (-1003860200579) channels receiving signals daily at 8AM AST via GitHub Actions
- [2026-03-22] Passive income strategy: Telegram screener channel → Beehiiv newsletter → YouTube Shorts
- [2026-03-22] Distribution: GLOBAL (Reddit + Twitter/X + Discord) — NOT Aruba-local audience
- [2026-03-22] Revenue target: 25–80 paid subscribers @ $9.99 = $250–800 MRR by month 3
- [2026-03-22] Upgrade screenshots batch: slides 1-6 = learning prompts, slides 7-15 = existing finance skills, slide 16 = new McKinsey macro skill
- [2026-03-22] Payday 2026-03-27 12:01 PM AST: Kling $6.99 → Anthropic credits $10 → crypto DCA (in that order)
- [2026-03-22] n8n or Postiz (both free) recommended for cross-platform signal distribution automation

## Preferences Summary
See @memory/preferences.md for full list.
- Tone: professional but friendly, no filler
- Always save to files directly
- MVP first, challenge weak reasoning
- Structured outputs with headings

## Recurring Patterns
See @memory/patterns.md

## Decision Archive Index
See @memory/decisions-log.md

## Topic Files
| File | Contents |
|------|----------|
| preferences.md | All saved preferences with dates |
| patterns.md | Recurring behaviors and workflow insights |
| decisions-log.md | Chronological decision log |

## Skills Available (29 total)
/research, /session-close, /weekly-review, /decision, /remember, /market-check, /project-update, /voice-gen, /prompt-gen, /gemini, /kimi, /email-check, /kraken, /health-check, /docker, /backup
/stock-screen, /dcf-value, /risk-analyze, /earnings-breakdown, /portfolio-strategy, /technical-analysis, /dividend-strategy, /competitive-analysis, /pattern-finder, /stock-analyze (finance suite)
/trend-check, /content-gen, /script-gen, /niche-finder, /video-plan (social media — 2026-03-16)
/crypto-portfolio, /crypto-screen (crypto intelligence — Session 11-12)
/learn, /macro-impact, /stock-analyze (Session 13 — 2026-03-22)

## Session Index
| Date | Focus | File |
|------|-------|------|
| 2026-03-09 | Workspace foundation setup | sessions/2026-03-09-session.md |
| 2026-03-09 | Skills, APIs, OPN research, Gemini sub-agent | sessions/2026-03-09-session-2.md |
| 2026-03-10 | Kraken API skill + price alert system (8 tickers) | sessions/2026-03-10-session-3.md |
| 2026-03-10 | Claude API upgrades — 15 docs reviewed, free wins applied | sessions/2026-03-10-session-4.md |
| 2026-03-10 | Portfolio snapshot, BTC market mechanics, NotebookLM crypto study doc | sessions/2026-03-10-session-5.md |
| 2026-03-18 | GitHub push + cloud sync + Telegram redesign + crypto focus shift | sessions/2026-03-18-session-12.md |
| 2026-03-22 | 16 upgrade screenshots processed, /learn + /macro-impact skills, Kling verdict, passive income strategy | sessions/2026-03-22-session-13.md |

## Docs Added
| Date | Topic | File |
|------|-------|------|
| 2026-03-09 | Workspace index | docs/INDEX.md |
| 2026-03-09 | AI prompt engineering — video/image generation 2026 | docs/2026-03-09-ai-prompt-engineering-video-images.md |
| 2026-03-09 | Google APIs integration — Gemini, YouTube, Gmail free tiers | docs/2026-03-09-google-apis-integration.md |
| 2026-03-10 | All 15 Claude API upgrades — quick reference (free vs paid) | docs/claude-docs/claude-api-upgrades-2026-03-10.md |
| 2026-03-10 | Remote MCP servers setup guide — Brave Search, GitHub | docs/2026-03-10-remote-mcp-servers.md |
| 2026-03-10 | Crypto market dynamics — BTC dominance, amplification effect, portfolio applied | docs/2026-03-10-crypto-market-dynamics.txt |

## Crypto Monitoring
- OPN entry: ~$0.31, alerts at $0.18 (buy) / $0.45 / $0.60 (sell zones)
- March 2027 cliff: 425M OPN tokens unlock — monitor closely
- Price alert script: `python projects/crypto-monitoring/price-alert.py`
- [2026-03-11] Laptop cleaned: WildTangent, ExpressVPN, HP bloatware (7 apps) removed, McAfee uninstalling
- [2026-03-11] Startup cleaned: 4 entries removed (HP launcher, Edge auto-launch, Notion, NordVPN) — only OneDrive remains
- [2026-03-11] Freed ~900MB: temp folder (557MB) + Downloads cleanup (151MB) + npm cache (201MB)
- [2026-03-11] Telegram-Claude bridge LIVE: @SoloClaude5_bot now calls Claude Haiku API. Runs at startup via startup folder bat
- [2026-03-11] Virtual RAM: SET_VIRTUAL_RAM_AS_ADMIN.vbs on Desktop (run as admin, then restart)
- [2026-03-11] ANTHROPIC_API_KEY added to .env.local — bridge uses claude-haiku-4-5-20251001 (~$0.0005/convo)
- [2026-03-11] GitHub Actions workflow created — market-report.py runs 3x/day (8AM/6PM/9PM AST) on GitHub cloud. 7 secrets required. ~180 min/month — within free tier. Task Scheduler can be disabled once confirmed working.
- [2026-03-11] Established YNAI5-KEY-INPUT.txt on Desktop as permanent secure API key input method — Claude reads it, adds to .env.local, then the file is cleared
- [2026-03-12] New MCPs added: context7 (live docs), memory (persistent KV store), sequential-thinking (structured reasoning) — all free, no API key
- [2026-03-12] Ralph Loop installed — autonomous multi-task dev agent. Use `ralph-setup <project>` then `ralph --live` in Git Bash. tmux/--monitor not available on Windows without WSL2
- [2026-03-12] Claude Mem SKIPPED — known win32 bug (worker crashes). Revisit when WSL2 is set up
- [2026-03-12] jq v1.8.1 installed via winget (required by Ralph Loop)
- [2026-03-12] autonomous-agent.py built — direct Anthropic API agent (no CLI needed), runs in GitHub Actions
- [2026-03-12] ralph-automation.yml created — schedules agent Mon/Wed/Fri 10AM AST, commits session outputs to repo
- [2026-03-12] Docker MCP Toolkit confirmed — 100+ servers, free ones: DuckDuckGo, Docker Hub, Puppeteer (needs Docker Desktop open)
- [2026-03-12] Integration audit: 6 MCPs working (Brave, Context7, Memory, SeqThinking, Gmail, Playwright), 12 keys in .env.local
- [2026-03-12] ⚠️ Security: Telegram/Brave/Kimi/ElevenLabs/Gemini keys flagged for regeneration (shared in past sessions)
- [2026-03-12] Session crash recovery LIVE: PreCompact/Stop/SessionStart hooks save backup automatically
- [2026-03-12] /health-check skill: parallel diagnostics (psutil) → logs/ + optional Telegram
- [2026-03-12] /docker skill: Docker on-demand (auto-starts Desktop, no 24/7 daemon)
- [2026-03-12] startup.bat installed: price-alert.py + telegram-claude-bridge.py auto-start at Windows login
- [2026-03-12] Cloud health: system-health.yml runs 9AM AST daily via GitHub Actions (checks CoinGecko/GitHub/Kraken)
- [2026-03-12] fetch + git MCPs added (free, no API key)
- [2026-03-15] All 14 upgrade screenshots processed — 9 finance skills, 3 tools (decision-review.py, task-manager.py, gmail-manager.py), memory system confirmed
- [2026-03-15] Task Scheduler: YNAI5-DecisionReview (daily 9:15AM), YNAI5-GmailTriage (hourly), YNAI5-TaskAgent (hourly), YNAI5-UpgradeWatcher (every 30min)
- [2026-03-15] Screen lock fix: AC sleep=NEVER, DC sleep=30min (was 3min). Sessions survive screen lock.
- [2026-03-16] Social media pipeline skills built: /trend-check, /content-gen, /script-gen, /niche-finder, /video-plan
- [2026-03-16] New output folders: social-media-automation/scripts/, trends/, niche-research/, video-plans/
- [2026-03-16] content-gen upgraded: now includes B-Roll Pexels keywords section in every output
- [2026-03-16] Playbook created: playbooks/tiktok-video-assembly.md — SOP for <15 min/video assembly
- [2026-03-16] Free pipeline LIVE: ElevenLabs VO (10K chars/mo) + Pexels stock footage + CapCut
- [2026-03-16] Video gen verdict: Kling AI wins (MCP server + 66 free credits/day + cheapest API). Buy March 27 at $6.99/mo.
- [2026-03-16] Seedance 2.0 SUSPENDED globally March 15 — Disney C&D, copyright dispute. Avoid entirely.
- [2026-03-16] ACTION: Go to pexels.com/api → free API key → paste in YNAI5-KEY-INPUT.txt → add PEXELS_API_KEY to .env.local
- [2026-03-16] March 27 plan: Kling AI Standard ($6.99) + mcp-kling MCP → fully autonomous video pipeline
- [2026-03-18] GitHub repo LIVE: https://github.com/soloplayer500/YNAI5-SU (public, master branch)
- [2026-03-18] Cloud sync LIVE: GitHub Actions runs portfolio_monitor.py every 30min + morning briefing 9AM AST
- [2026-03-18] 7 GitHub Secrets set automatically via Python + gh CLI (no manual steps needed)
- [2026-03-18] Telegram messages redesigned: card format, 🟢🔴 P&L, ▲▼ 24h — mobile-first
- [2026-03-18] Pinokio YNAI5 Bridge created: C:\pinokio\api\ynai5-bridge\ — starts Telegram bridge as daemon
- [2026-03-18] FOCUS SHIFT: social media pipeline paused (hardware blocker), full focus on crypto/stocks
- [2026-03-18] Brave Search hit 2000/month limit — ration searches, resets monthly
- [2026-03-18] BTC at $71,400 — holding $70K support. BTC dominance 56.65% = risk-off, NOT alt season
- [2026-03-18] Kraken portfolio: mostly dust positions. PENGU $14 (84% of portfolio). All coins underwater.
- [2026-03-18] OPN WARNING: -15.8% today on top of -24.8% from avg buy. Watch $0.22 support.
- [2026-03-18] NEXT WEEK: user gets paid — plan position sizes for BTC DCA + automation tools (Kling $6.99)
- [2026-03-18] BTC symbol bug: shows "BT" instead of "BTC" in portfolio JSON — XXBT asset mapping issue
- [2026-03-18] Claude.ai Projects system prompt ready with real GitHub URLs — user setting up on mobile
- [2026-03-24] Personal Telegram: `📋 PORTFOLIO BRIEF` executive format — no branding, alert-only on >5% moves
- [2026-03-24] Block Syndicate market-report: professional card format — Regime/RSI/Holdings/News/AI Take
- [2026-03-24] market-report.yml trimmed to 9AM + 3PM AST only (was 8AM/6PM/9PM)
- [2026-03-24] FlowStack workspace created — C:\Users\shema\OneDrive\Desktop\FlowStack\ (27 files, git init)
- [2026-03-24] FlowStack = personal finance only (portfolio, savings, investing knowledge, 5 skills)
- [2026-03-24] Payslip reminder scheduled: 2026-03-29 10:00 AM AST (auto-fires Telegram)

## Session Index
| Date | Focus | File |
|------|-------|------|
| 2026-03-09 | Workspace foundation setup | sessions/2026-03-09-session.md |
| 2026-03-09 | Skills, APIs, OPN research, Gemini sub-agent | sessions/2026-03-09-session-2.md |
| 2026-03-10 | Kraken API skill + price alert system (8 tickers) | sessions/2026-03-10-session-3.md |
| 2026-03-10 | Claude API upgrades — 15 docs reviewed, free wins applied | sessions/2026-03-10-session-4.md |
| 2026-03-10 | Portfolio snapshot, BTC market mechanics, NotebookLM crypto study doc | sessions/2026-03-10-session-5.md |
| 2026-03-18 | GitHub push + cloud sync + Telegram redesign + crypto focus shift | sessions/2026-03-18-session-12.md |
| 2026-03-22 | 16 upgrade screenshots, /learn + /macro-impact, Kling verdict, passive income | sessions/2026-03-22-session-13.md |
| 2026-03-24 | Telegram executive briefing, FlowStack workspace, payslip reminder | sessions/2026-03-24-session-14.md |
