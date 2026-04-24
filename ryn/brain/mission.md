# RYN — Mission

_The north star. Read this first, every session._

Last Updated: 2026-04-24

---

## What RYN Is

RYN is the personal AI operating system of **Shami (Solo)** — a solo systems builder in Aruba turning scattered AI infrastructure into a lean revenue-capable OS.

- **Local brain:** HP Laptop 15 (8GB RAM, Ryzen 5 5500U) — Claude Code interface
- **Cloud spine:** GCP e2-micro VM (34.45.31.188) — 7 active services
- **Control plane:** Telegram (@SoloClaude5_bot) — `/status`, `/logs`, `/restart`, `/snapshot`
- **Source of truth:** GitHub repo `soloplayer500/YNAI5-SU`
- **Execution:** Claude Code (primary) + Gemini/Kimi (secondary) + GitHub Actions (scheduled)

---

## Why It Exists

To generate **sovereign revenue** through AI-powered automation — trading intelligence, content, and paid signals — while running lean enough to survive on limited hardware and a limited budget.

---

## What It Does

| Layer | Function |
|-------|----------|
| **Trading intelligence** | Kraken portfolio monitor, daily /crypto-screen, prediction accuracy tracking |
| **Paid signals** | Block Syndicate Telegram channel (VIP + free tiers) |
| **Content automation** | Scripts, voice, video pipeline (paused — hardware gate) |
| **VM control plane** | Heartbeat, commander, systemd services, log rotation |
| **Knowledge layer** | RAG index (674 chunks, 50 files) + 30+ custom Claude skills |

---

## Operating Principles

1. **MVP first.** Ship working > ship elegant.
2. **Reuse > rebuild.** 90% of what's needed already exists.
3. **Revenue before polish.** No new infrastructure until $100 first revenue milestone.
4. **Protect capital.** Don't blow up the Kraken account.
5. **Memory over recall.** Write strategic findings to `ryn/brain/`.
6. **Simplify ruthlessly.** If a folder has a .gitkeep and nothing else, question why it exists.
7. **One source of truth per fact.** Duplicate docs cause drift — consolidate.

---

## Current Priority (2026-04-24)

**#1 — Activate Block Syndicate Telegram screener as paid product.**

The bot is built. The channels exist. The workflows are paused. The missing piece is Gumroad + distribution. First $10 within 7 days unlocks everything else.

See: `ryn/brain/priority_stack.md` for full stack.

---

## Non-Negotiables

- Never commit API keys (`.env.local` is gitignored)
- Never run 24/7 daemons on laptop (moved to VM)
- Never expand infrastructure before current systems generate revenue
- Never ignore `/status` alerts from VM heartbeat

---

## For Future AI Sessions

If you're a new session reading this:

1. Read `ryn/brain/systems_map.md` to understand what runs where
2. Read `ryn/brain/priority_stack.md` to know what's urgent
3. Read `ryn/brain/next_actions.md` to know what to do first
4. Read `ryn/brain/last_report.md` for the last major event
5. Execute. Don't re-plan what's already planned.
