#!/usr/bin/env python3
"""
YNAI5 Daily Briefing — Autonomous Morning Planner
==================================================
Runs at 7:00 AM via Windows Task Scheduler (before market reports).

What it does:
  1. Reads workspace state (priorities, open actions, last session)
  2. Fetches market snapshot (BTC/ETH prices + 24h change)
  3. Searches Brave for AI + crypto news overnight
  4. Calls Kimi to generate 3 proactive ideas for the day
  5. Saves briefing → sessions/briefing-YYYY-MM-DD.md
  6. Sends to Telegram as morning message

Run manually: python tools/daily-briefing.py
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

# ── UTF-8 fix ─────────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent


# ── Env ────────────────────────────────────────────────────────────────────────
def load_env() -> dict:
    env = {}
    env_path = ROOT / ".env.local"
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


ENV = load_env()
TELEGRAM_BOT_TOKEN  = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = ENV.get("TELEGRAM_CHAT_ID", "")
OPENROUTER_API_KEY  = ENV.get("OPENROUTER_API_KEY", "")
BRAVE_KEY           = ENV.get("BRAVE_SEARCH_API_KEY", "")
COINGECKO_API_KEY   = ENV.get("COINGECKO_API_KEY", "")
SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ── 1. Read Workspace State ────────────────────────────────────────────────────
def read_priorities() -> str:
    f = ROOT / "context" / "current-priorities.md"
    if f.exists():
        lines = f.read_text(encoding="utf-8").splitlines()
        # Extract top 15 lines of content (skip headers)
        content = [l for l in lines if l.strip() and not l.startswith("_")]
        return "\n".join(content[:15])
    return "No priorities file found."


def read_open_actions() -> list:
    actions_dir = ROOT / "actions"
    items = []
    if not actions_dir.exists():
        return items
    for f in sorted(actions_dir.glob("*.md"))[-5:]:  # last 5 action files
        content = f.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.strip().startswith("- [ ]"):
                items.append(line.strip().lstrip("- [ ]").strip())
    return items[:10]  # max 10 open items


def read_last_session() -> str:
    sessions_dir = ROOT / "sessions"
    if not sessions_dir.exists():
        return ""
    files = sorted(sessions_dir.glob("*.md"))
    # Skip briefing files
    session_files = [f for f in files if "briefing" not in f.name]
    if not session_files:
        return ""
    last = session_files[-1]
    content = last.read_text(encoding="utf-8")
    lines = content.splitlines()
    return "\n".join(lines[:20])  # first 20 lines of last session


# ── 2. Market Snapshot ─────────────────────────────────────────────────────────
def fetch_market_snapshot() -> dict:
    """Quick BTC + ETH + SOL price check from CoinGecko."""
    ids = "bitcoin,ethereum,solana,opinion,bitcoin-cash"
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    )
    headers = {"Accept": "application/json", "User-Agent": "YNAI5-Briefing/1.0"}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[Market] Error: {e}")
        return {}


def fmt_price(price: float) -> str:
    if price >= 1000: return f"${price:,.0f}"
    if price >= 1:    return f"${price:.2f}"
    if price >= 0.01: return f"${price:.4f}"
    return f"${price:.6f}"


def format_market(prices: dict) -> str:
    lines = []
    labels = {
        "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
        "opinion": "OPN", "bitcoin-cash": "BCH"
    }
    for coin_id, sym in labels.items():
        data = prices.get(coin_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change", 0.0)
        if price:
            icon = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            lines.append(f"  {icon} {sym}: {fmt_price(price)} ({sign}{change:.1f}%)")
    return "\n".join(lines) if lines else "  No market data"


# ── 3. Brave News Search ───────────────────────────────────────────────────────
def brave_search(query: str, count: int = 4) -> list:
    if not BRAVE_KEY:
        return []
    try:
        url = (
            f"https://api.search.brave.com/res/v1/news/search"
            f"?q={urllib.parse.quote(query)}&count={count}&freshness=pd"
        )
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_KEY
        })
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
        return [
            {"title": item.get("title", ""), "age": item.get("age", "")}
            for item in data.get("results", [])[:count]
        ]
    except Exception as e:
        print(f"[Brave] {e}")
        return []


def fetch_overnight_news() -> dict:
    """Parallel search: AI news + crypto news overnight."""
    results = {}
    queries = {
        "ai":     "AI artificial intelligence news today 2026",
        "crypto": "bitcoin crypto market overnight news today"
    }
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(brave_search, q): label for label, q in queries.items()}
        for future in as_completed(futures):
            label = futures[future]
            results[label] = future.result()
    return results


# ── 4. Kimi Idea Generator ─────────────────────────────────────────────────────
def kimi_generate_ideas(priorities: str, open_actions: list, market: str, news: dict) -> str:
    """
    Kimi generates 3 proactive ideas for today based on full workspace context.
    This is the 'autonomous planning' intelligence.
    """
    if not OPENROUTER_API_KEY:
        return "[ Kimi unavailable — add OPENROUTER_API_KEY to .env.local ]"

    actions_str = "\n".join(f"- {a}" for a in open_actions) if open_actions else "None"

    ai_news = "\n".join(f"• {n['title']}" for n in news.get("ai", [])[:3])
    crypto_news = "\n".join(f"• {n['title']}" for n in news.get("crypto", [])[:3])

    task = f"""You are YNAI5 — Shami's autonomous AI assistant in Aruba.
Your job: study his workspace and generate 3 proactive ideas he should act on TODAY.

== CURRENT PRIORITIES ==
{priorities}

== OPEN TASKS ==
{actions_str}

== MARKET RIGHT NOW ==
{market}

== OVERNIGHT AI NEWS ==
{ai_news or 'None found'}

== OVERNIGHT CRYPTO NEWS ==
{crypto_news or 'None found'}

Generate exactly 3 proactive, specific ideas. Each idea must:
- Be actionable TODAY (not "eventually" or "someday")
- Connect to his real priorities (revenue, crypto, social media automation)
- Take advantage of something from the news or market if relevant
- Be 1-2 sentences max

Format:
💡 IDEA 1: [title]
[What to do and why it matters today]

💡 IDEA 2: [title]
[What to do and why it matters today]

💡 IDEA 3: [title]
[What to do and why it matters today]

Be a sharp autonomous advisor, not a chatbot. Think ahead of him."""

    payload = json.dumps({
        "model": "moonshotai/kimi-k2.5",
        "messages": [
            {"role": "system", "content": "You are an autonomous AI advisor. Sharp, proactive, no filler."},
            {"role": "user", "content": task}
        ],
        "max_tokens": 500
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ynai5.local",
            "X-Title": "YNAI5"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            result = json.loads(r.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[ Kimi error: {e} ]"


# ── 5. Build Briefing Doc ─────────────────────────────────────────────────────
def build_briefing_md(now: datetime, market: str, news: dict, ideas: str,
                       open_actions: list) -> str:
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M AST")

    ai_news_lines  = "\n".join(f"- {n['title']}" for n in news.get("ai", []))
    cry_news_lines = "\n".join(f"- {n['title']}" for n in news.get("crypto", []))
    actions_lines  = "\n".join(f"- [ ] {a}" for a in open_actions)

    return f"""# YNAI5 Daily Briefing — {date_str}
_Generated at {time_str} by daily-briefing.py_

---

## Market Snapshot
{market}

## Open Actions
{actions_lines or '_None_'}

## Overnight AI News
{ai_news_lines or '_None found_'}

## Overnight Crypto News
{cry_news_lines or '_None found_'}

## Kimi Proactive Ideas
{ideas}

---
_Auto-generated. Review at session start._
"""


# ── 6. Telegram ────────────────────────────────────────────────────────────────
def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Not configured.")
        return
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
        print("[Telegram] ✓ Sent")
    except Exception as e:
        print(f"[Telegram] Failed: {e}")


def build_telegram_message(now: datetime, market: str, open_actions: list,
                             ideas: str, news: dict) -> str:
    date_str = now.strftime("%A, %B %d")
    action_count = len(open_actions)

    # Truncate ideas for Telegram (keep first 2 ideas)
    idea_lines = ideas.split("\n")
    ideas_short = "\n".join(idea_lines[:10])  # ~2 ideas worth

    top_news = []
    for n in (news.get("crypto", []) + news.get("ai", []))[:3]:
        top_news.append(f"• {n['title'][:75]}")

    news_block = "\n".join(top_news) if top_news else "Nothing notable overnight."

    return f"""{SEP}
<b>☀️ YNAI5 BRIEFING — {date_str}</b>
{SEP}

<b>📈 Market</b>
{market}

<b>📰 Overnight</b>
{news_block}

{SEP}
<b>🧠 YNAI5 Ideas for Today</b>

{ideas_short}

{SEP}
<b>📋 Open Actions: {action_count}</b>
{chr(10).join(f'  • {a[:60]}' for a in open_actions[:4]) if open_actions else '  All clear ✅'}

{SEP}
<i>Start Claude → briefing saved in sessions/</i>"""


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    print(f"\n{'━'*50}")
    print(f"  YNAI5 Daily Briefing — {date_str} {now.strftime('%H:%M')}")
    print(f"{'━'*50}\n")

    print("  [1/5] Reading workspace state...")
    priorities   = read_priorities()
    open_actions = read_open_actions()
    last_session = read_last_session()
    print(f"      Open actions: {len(open_actions)}")

    print("  [2/5] Market snapshot...")
    prices  = fetch_market_snapshot()
    market  = format_market(prices)

    print("  [3/5] Brave overnight news (AI + crypto)...")
    news = fetch_overnight_news()
    ai_count    = len(news.get("ai", []))
    crypto_count = len(news.get("crypto", []))
    print(f"      AI: {ai_count} | Crypto: {crypto_count}")

    print("  [4/5] Kimi generating today's ideas...")
    ideas = kimi_generate_ideas(priorities, open_actions, market, news)

    print("  [5/5] Saving briefing + sending Telegram...")
    briefing_md = build_briefing_md(now, market, news, ideas, open_actions)
    briefing_path = ROOT / "sessions" / f"briefing-{date_str}.md"
    briefing_path.write_text(briefing_md, encoding="utf-8")
    print(f"      Saved: {briefing_path.name}")

    tg_message = build_telegram_message(now, market, open_actions, ideas, news)
    send_telegram(tg_message)

    print(f"\n{'━'*50}")
    print("  ✅ Briefing complete")
    print(f"{'━'*50}\n")


if __name__ == "__main__":
    main()
