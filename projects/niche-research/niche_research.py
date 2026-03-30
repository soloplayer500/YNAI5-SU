#!/usr/bin/env python3
"""
BRAINAI5 V3 — Phase 1: Niche Research
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs on GitHub Actions. Uses Brave Search + Claude Haiku.
Sends Telegram summary card with inline YES / NO / PIVOT keyboard.
Polls for callback_query response (10-min window).

Exit codes:
  0 = YES approved → Phase 2 can proceed
  1 = NO / PIVOT / TIMEOUT → stop

Usage:
  NICHE_QUERY="betrayal karma narratives" python niche_research.py
  python niche_research.py "betrayal karma narratives"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ── UTF-8 fix ──────────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Config ─────────────────────────────────────────────────────────────────────
HERE          = Path(__file__).resolve().parent
REPORTS_DIR   = HERE / "output" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

BRAVE_KEY     = os.environ.get("BRAVE_SEARCH_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
NICHE_QUERY   = os.environ.get("NICHE_QUERY", sys.argv[1] if len(sys.argv) > 1 else "")

GATE_TIMEOUT  = int(os.environ.get("GATE_TIMEOUT_SECONDS", "600"))  # 10 min default


# ── Helpers ────────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def log(tag: str, msg: str):
    print(f"[{tag}] {msg}", flush=True)


# ── Brave Search ───────────────────────────────────────────────────────────────
def brave_search(query: str, count: int = 8) -> list[dict]:
    """Returns list of {title, url, desc} snippets from Brave Search."""
    if not BRAVE_KEY:
        log("BRAVE", f"No key — skipping: {query}")
        return []
    url = (
        "https://api.search.brave.com/res/v1/web/search"
        f"?q={urllib.parse.quote(query)}&count={count}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            # Handle gzip if returned
            try:
                import gzip
                data = json.loads(gzip.decompress(raw))
            except Exception:
                data = json.loads(raw)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "desc": r.get("description", ""),
            }
            for r in data.get("web", {}).get("results", [])
        ]
    except Exception as e:
        log("BRAVE", f"Error: {e}")
        return []


# ── Claude Haiku ───────────────────────────────────────────────────────────────
def claude_analyze(prompt: str, max_tokens: int = 2000) -> str:
    if not ANTHROPIC_KEY:
        return "[No ANTHROPIC_API_KEY]"
    payload = json.dumps(
        {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            result = json.loads(resp.read())
        return result["content"][0]["text"]
    except Exception as e:
        return f"[Claude error: {e}]"


# ── Telegram ───────────────────────────────────────────────────────────────────
def tg_request(method: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log("TG", f"{method} error: {e}")
        return {}


def tg_send(text: str):
    tg_request("sendMessage", {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})


def tg_send_gate_card(text: str):
    """Send summary card with inline YES / NO / PIVOT keyboard."""
    result = tg_request(
        "sendMessage",
        {
            "chat_id": TG_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "✅ YES — Deep dive", "callback_data": "YES"},
                        {"text": "❌ NO — Discard", "callback_data": "NO"},
                        {"text": "🔄 PIVOT", "callback_data": "PIVOT"},
                    ]
                ]
            },
        },
    )
    msg_id = result.get("result", {}).get("message_id", "")
    log("TG", f"Gate card sent (msg_id={msg_id})")
    return str(msg_id)


def tg_answer_callback(callback_id: str):
    """Dismiss loading spinner after user taps inline button."""
    tg_request("answerCallbackQuery", {"callback_query_id": callback_id, "text": "✅ Got it!"})


def tg_get_latest_offset() -> int | None:
    """Get update offset so we only see NEW updates after this point."""
    result = tg_request("getUpdates", {"offset": -1, "limit": 1})
    updates = result.get("result", [])
    if updates:
        return updates[-1]["update_id"] + 1
    return None


def tg_poll_gate(timeout_seconds: int = 600) -> str:
    """
    Long-poll for callback_query from the authorized chat.
    Returns: YES | NO | PIVOT | TIMEOUT
    Uses allowed_updates=["callback_query"] to avoid consuming bridge bot messages.
    """
    offset = tg_get_latest_offset()
    log("GATE", f"Polling for inline button tap (offset={offset}, timeout={timeout_seconds}s)...")

    start = time.time()
    while time.time() - start < timeout_seconds:
        params: dict = {
            "timeout": 30,
            "allowed_updates": ["callback_query"],
        }
        if offset is not None:
            params["offset"] = offset

        result = tg_request("getUpdates", params)
        for update in result.get("result", []):
            offset = update["update_id"] + 1
            cb = update.get("callback_query")
            if not cb:
                continue
            from_id = cb.get("from", {}).get("id")
            if str(from_id) != str(TG_CHAT_ID):
                continue  # Not from our authorized user
            response = cb.get("data", "").upper()
            tg_answer_callback(cb["id"])
            log("GATE", f"Response received: {response}")
            return response

    log("GATE", "Timeout — no response")
    return "TIMEOUT"


# ── Research Pipeline ──────────────────────────────────────────────────────────
def run_research(query: str) -> dict:
    log("RESEARCH", f"Starting 5-layer research for: {query}")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Layer 1: Audience intelligence
    log("L1", "Audience demographics...")
    l1 = brave_search(f"{query} YouTube channel viewers audience demographics 2025 2026")

    # Layer 2: Monetization
    log("L2", "Monetization & CPM...")
    l2 = brave_search(f"{query} content creator RPM CPM monetization earnings YouTube TikTok")

    # Layer 3: Competitive landscape
    log("L3", "Top creators & competition...")
    l3 = brave_search(f"top {query} YouTube channels subscribers growth most popular creators")

    # Layer 4: Viral formats
    log("L4", "Viral formats & hooks...")
    l4 = brave_search(f"{query} viral TikTok YouTube Shorts trending format hook 2025")

    # Layer 5: Blue ocean gaps
    log("L5", "Blue ocean gaps...")
    l5 = brave_search(f"{query} content gap underserved niche opportunity missing creators")

    def fmt(results: list[dict]) -> str:
        return "\n".join(f"- {r['title']}: {r['desc']}" for r in results) or "(no results)"

    combined = "\n\n".join(
        [
            f"=== AUDIENCE ===\n{fmt(l1)}",
            f"=== MONETIZATION ===\n{fmt(l2)}",
            f"=== COMPETITORS ===\n{fmt(l3)}",
            f"=== VIRAL FORMATS ===\n{fmt(l4)}",
            f"=== BLUE OCEAN GAPS ===\n{fmt(l5)}",
        ]
    )

    log("CLAUDE", "Synthesizing findings...")
    synthesis_prompt = f"""You are a YouTube/TikTok niche research analyst. Analyze these search results for: "{query}"

{combined}

Return ONLY a valid JSON object — no markdown, no explanation, no code fences:
{{
  "niche": "{query}",
  "category": "<Fantasy/Weapons | Horror/Creepypasta | Animals/Biology | Finance | Tech/AI | Lifestyle | Gaming | Education | Other>",
  "query": "{query}",
  "stats": {{
    "growth_rate": <annual multiplier, number, e.g. 14>,
    "saturation": "<Blue | Orange | Red>",
    "cpm_low": <number>,
    "cpm_high": <number>,
    "audience_m": <monthly viewers in millions, number>,
    "entry_barrier": "<Low | Medium | High>"
  }},
  "creators": [
    {{"name":"...","subs":<number>,"growth_rate_12mo":"e.g. 45%","est_monthly_rev":"e.g. 3500","platform":"YouTube","format_innovation":"..."}}
  ],
  "formats": [
    {{"name":"...","platform":"...","avg_views":<number>,"ctr_pct":<number>,"retention_pct":<number>,"shares_est":<number>,"cpm":<number>,"why":"..."}}
  ],
  "blue_ocean": [
    {{"name":"...","why":"...","audience_m":<number>,"entry_barrier":"<Low|Medium|High>","effort_hours":<number>,"rpm_est":"e.g. 10-15"}}
  ],
  "summary": "2-3 sentence summary of the opportunity",
  "notes": ""
}}
Include 5-10 creators, 4-6 formats, 3-5 blue ocean gaps. Base all numbers on the search results above."""

    raw = claude_analyze(synthesis_prompt)

    # Parse JSON — find first {...} block
    data: dict = {}
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError("No JSON block found in Claude response")
    except Exception as e:
        log("CLAUDE", f"JSON parse error: {e} — using fallback")
        data = {
            "niche": query,
            "category": "Unknown",
            "query": query,
            "stats": {
                "growth_rate": 0,
                "saturation": "Unknown",
                "cpm_low": 0,
                "cpm_high": 0,
                "audience_m": 0,
                "entry_barrier": "Unknown",
            },
            "creators": [],
            "formats": [],
            "blue_ocean": [],
            "summary": raw[:400],
            "notes": "Parse error — raw Claude output in summary field",
        }

    data["date"] = today
    data["slug"] = slugify(query)
    return data


# ── Summary Card ───────────────────────────────────────────────────────────────
def build_summary_card(data: dict) -> str:
    stats = data.get("stats", {})
    sat = stats.get("saturation", "?")
    sat_icon = (
        "\U0001f535" if sat.lower() == "blue"
        else "\U0001f7e0" if sat.lower() == "orange"
        else "\U0001f534"
    )
    creators = data.get("creators", [])
    formats = data.get("formats", [])
    blue_ocean = data.get("blue_ocean", [])
    top_c = creators[0] if creators else {}
    top_f = formats[0] if formats else {}
    top_o = blue_ocean[0] if blue_ocean else {}

    return (
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
        "\U0001f9e0 <b>BRAINAI5 V3 \u2014 RESEARCH COMPLETE</b>\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"<b>NICHE:</b> {data.get('niche', '?')}\n"
        f"<b>CATEGORY:</b> {data.get('category', '?')}\n\n"
        f"\U0001f4ca <b>QUICK STATS:</b>\n"
        f"\u251c\u2500 Growth: <b>{stats.get('growth_rate', '?')}x/yr</b>\n"
        f"\u251c\u2500 Saturation: {sat_icon} <b>{sat} Ocean</b>\n"
        f"\u251c\u2500 CPM/RPM: <b>${stats.get('cpm_low', '?')}\u2013${stats.get('cpm_high', '?')}</b>\n"
        f"\u251c\u2500 Audience: <b>{stats.get('audience_m', '?')}M/mo</b>\n"
        f"\u2514\u2500 Blue Ocean Gaps: <b>{len(blue_ocean)}</b>\n\n"
        f"\U0001f3c6 <b>TOP CREATOR:</b>\n"
        f"\u2514\u2500 {top_c.get('name', 'N/A')} \u2022 {top_c.get('subs', '?')} subs \u2022 ~${top_c.get('est_monthly_rev', '?')}/mo\n\n"
        f"\U0001f3ac <b>WINNING FORMAT:</b>\n"
        f"\u2514\u2500 {top_f.get('name', 'N/A')}: {top_f.get('why', '')[:80]}\n\n"
        f"\U0001f30a <b>BIGGEST GAP:</b>\n"
        f"\u2514\u2500 {top_o.get('name', 'N/A')}: {top_o.get('why', '')[:100]}\n\n"
        f"\U0001f4a1 <b>SUMMARY:</b>\n{data.get('summary', '')}\n\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "<i>Tap a button below to continue:</i>"
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not NICHE_QUERY:
        log("ERROR", "No query — set NICHE_QUERY env var or pass as argument")
        sys.exit(1)

    # 1. Research
    data = run_research(NICHE_QUERY)

    # 2. Save report
    slug = data["slug"]
    today = data["date"]
    report_path = REPORTS_DIR / f"{today}-{slug}.json"
    report_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log("REPORT", f"Saved: {report_path}")

    # 3. Send Telegram gate card
    card = build_summary_card(data)
    tg_send_gate_card(card)

    # 4. Wait for user tap
    response = tg_poll_gate(timeout_seconds=GATE_TIMEOUT)

    if response == "YES":
        tg_send(
            f"\u2705 <b>Approved!</b> Deep dive running for <b>{NICHE_QUERY}</b>...\n\n"
            f"<i>Google Sheets + HTML dashboard being generated now.</i>"
        )
        # Mark approval for Phase 2 workflow to detect
        (REPORTS_DIR / f"{today}-{slug}.approved").write_text("YES", encoding="utf-8")
        log("GATE", f"Approved. Slug: {slug}")
        print(f"APPROVED_SLUG:{slug}", flush=True)
        sys.exit(0)

    elif response == "NO":
        tg_send(f"\u274c Research discarded for: <b>{NICHE_QUERY}</b>")
        report_path.unlink(missing_ok=True)
        log("GATE", "User declined — report deleted")
        sys.exit(1)

    elif response == "PIVOT":
        tg_send(
            f"\U0001f504 Pivot requested.\n\n"
            f"Go to GitHub Actions \u2192 <b>BRAINAI5 Niche Research</b> \u2192 Run workflow\n"
            f"Set <code>niche_query</code> to your new query."
        )
        log("GATE", "User requested pivot")
        sys.exit(1)

    else:  # TIMEOUT
        tg_send(
            f"\u23f3 No response for <b>{NICHE_QUERY}</b>.\n\n"
            f"Report saved. Trigger <b>BRAINAI5 Deep Dive</b> workflow manually when ready:\n"
            f"<code>niche_slug = {slug}</code>"
        )
        log("GATE", "Timeout — report preserved for manual approval")
        sys.exit(1)


if __name__ == "__main__":
    main()
