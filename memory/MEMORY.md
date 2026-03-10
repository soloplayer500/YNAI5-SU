# Memory Index
_Claude auto-updates this file. Keep under 200 lines. Overflow goes to topic files._

Last Updated: 2026-03-10 (Session 4)

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
- [2026-03-10] PENDING: get Chat ID via get_chat_id.py → add TELEGRAM_CHAT_ID to .env.local to activate alerts
- [2026-03-10] SECURITY: Regenerate Brave API keys (both) + Telegram bot token — all were shared in chat

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

## Skills Available (12 total)
/research, /session-close, /weekly-review, /decision, /remember, /market-check, /project-update, /voice-gen, /prompt-gen, /gemini, /email-check, /kraken

## Session Index
| Date | Focus | File |
|------|-------|------|
| 2026-03-09 | Workspace foundation setup | sessions/2026-03-09-session.md |
| 2026-03-09 | Skills, APIs, OPN research, Gemini sub-agent | sessions/2026-03-09-session-2.md |
| 2026-03-10 | Kraken API skill + price alert system (8 tickers) | sessions/2026-03-10-session-3.md |
| 2026-03-10 | Claude API upgrades — 15 docs reviewed, free wins applied | sessions/2026-03-10-session-4.md |

## Docs Added
| Date | Topic | File |
|------|-------|------|
| 2026-03-09 | Workspace index | docs/INDEX.md |
| 2026-03-09 | AI prompt engineering — video/image generation 2026 | docs/2026-03-09-ai-prompt-engineering-video-images.md |
| 2026-03-09 | Google APIs integration — Gemini, YouTube, Gmail free tiers | docs/2026-03-09-google-apis-integration.md |
| 2026-03-10 | All 15 Claude API upgrades — quick reference (free vs paid) | docs/claude-docs/claude-api-upgrades-2026-03-10.md |
| 2026-03-10 | Remote MCP servers setup guide — Brave Search, GitHub | docs/2026-03-10-remote-mcp-servers.md |

## Crypto Monitoring
- OPN entry: ~$0.31, alerts at $0.18 (buy) / $0.45 / $0.60 (sell zones)
- March 2027 cliff: 425M OPN tokens unlock — monitor closely
- Price alert script: `python projects/crypto-monitoring/price-alert.py`
