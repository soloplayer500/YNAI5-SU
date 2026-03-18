#!/usr/bin/env python3
"""
YNAI5 Morning Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs every morning at 9AM AST via GitHub Actions.
Builds a full AI synthesis from 4 sources:
  1. Kraken portfolio (kraken_portfolio.json — already synced by portfolio_monitor.py)
  2. Brave Search — 3 crypto news headlines
  3. Prediction tracker stats (performance.json)
  4. CoinGecko — top movers last 24h

Sends a concise Telegram morning briefing.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("[ERROR] anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# ── UTF-8 fix ──────────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE             = Path(__file__).resolve().parent          # crypto-monitoring/
ENV_PATH         = HERE.parent.parent / ".env.local"        # YNAI5-SU/.env.local
PORTFOLIO_FILE   = HERE / "kraken" / "kraken_portfolio.json"
PERFORMANCE_FILE = HERE / "kraken" / "performance.json"

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ── Env loading ────────────────────────────────────────────────────────────────
def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
ANTHROPIC_KEY  = ENV.get("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = ENV.get("TELEGRAM_CHAT_ID", "")
COINGECKO_KEY  = ENV.get("COINGECKO_API_KEY", "")
BRAVE_KEY      = ENV.get("BRAVE_SEARCH_API_KEY", "")


# ── Data fetchers ──────────────────────────────────────────────────────────────
def _read_portfolio() -> dict | None:
    if not PORTFOLIO_FILE.exists():
        print(f"[Portfolio] File not found: {PORTFOLIO_FILE}")
        return None
    try:
        return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Portfolio] Read error: {e}")
        return None


def _read_performance() -> dict | None:
    if not PERFORMANCE_FILE.exists():
        return None
    try:
        return json.loads(PERFORMANCE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch_crypto_news() -> list[str]:
    """Fetch top 3 crypto news headlines via Brave Search."""
    if not BRAVE_KEY:
        return ["(Brave Search not configured — no news)"]
    try:
        query = urllib.parse.quote("bitcoin ethereum crypto market today")
        url   = f"https://api.search.brave.com/res/v1/news/search?q={query}&count=3"
        req   = urllib.request.Request(url, headers={
            "Accept":              "application/json",
            "Accept-Encoding":     "gzip",
            "X-Subscription-Token": BRAVE_KEY,
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data    = json.loads(r.read())
        results = data.get("results", [])
        return [r.get("title", "") for r in results[:3] if r.get("title")]
    except Exception as e:
        print(f"[News] Brave error: {e}")
        return ["(News fetch failed)"]


def _fetch_top_movers() -> list[dict]:
    """Get top 3 gainers and top 1 loser from CoinGecko in last 24h."""
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd&order=price_change_percentage_24h_desc"
        "&per_page=20&page=1&sparkline=false&price_change_percentage=24h"
    )
    headers = {"Accept": "application/json", "User-Agent": "YNAI5-MorningBriefing/1.0"}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            coins = json.loads(r.read())
        movers = []
        for c in coins[:3]:
            movers.append({
                "symbol": c.get("symbol", "").upper(),
                "name":   c.get("name", ""),
                "price":  c.get("current_price", 0),
                "change": c.get("price_change_percentage_24h", 0),
            })
        # Add worst performer
        if len(coins) >= 20:
            worst = coins[-1]
            movers.append({
                "symbol": worst.get("symbol", "").upper(),
                "name":   worst.get("name", ""),
                "price":  worst.get("current_price", 0),
                "change": worst.get("price_change_percentage_24h", 0),
                "is_loser": True,
            })
        return movers
    except Exception as e:
        print(f"[CoinGecko] Movers fetch error: {e}")
        return []


# ── Context builders ───────────────────────────────────────────────────────────
def _portfolio_summary_text(portfolio: dict) -> str:
    p = portfolio.get("portfolio", {})
    total = p.get("total_usd", 0)
    balances = [b for b in p.get("balances", []) if not b.get("is_stablecoin")]

    lines = [f"Total USD: ${total:,.2f}"]
    for b in balances[:6]:
        sym  = b.get("symbol", b["asset"])
        val  = b["usd_value"]
        pnl  = b.get("pnl_pct")
        ch24 = b.get("change_24h_pct")
        pnl_s = f" (P&L:{'+' if pnl >= 0 else ''}{pnl:.0f}%)" if pnl is not None else ""
        ch_s  = f" (24h:{'+' if ch24 >= 0 else ''}{ch24:.1f}%)" if ch24 is not None else ""
        lines.append(f"  {sym}: ${val:,.2f}{pnl_s}{ch_s}")

    open_orders = p.get("open_orders", [])
    if open_orders:
        lines.append(f"Open orders: {len(open_orders)}")

    return "\n".join(lines)


def _performance_summary_text(perf: dict | None) -> str:
    if not perf:
        return "No prediction data yet"
    ov = perf.get("overall", {})
    streak = perf.get("streak", {})
    return (
        f"Predictions: {ov.get('correct', 0)}/{ov.get('total', 0)} correct "
        f"({ov.get('accuracy_pct', 0):.1f}%) | "
        f"Streak: {streak.get('current_correct', 0)} correct | "
        f"Pending: {ov.get('pending', 0)}"
    )


def _movers_text(movers: list) -> str:
    if not movers:
        return "Market data unavailable"
    lines = []
    for m in movers:
        sign = "+" if m["change"] >= 0 else ""
        tag  = " 📉 WORST" if m.get("is_loser") else ""
        lines.append(f"  {m['symbol']}: ${m['price']:,.4f} ({sign}{m['change']:.1f}%){tag}")
    return "\n".join(lines)


# ── Claude synthesis ───────────────────────────────────────────────────────────
def _generate_briefing(portfolio_text: str, news: list[str], perf_text: str, movers_text: str) -> str:
    """Call Claude Haiku to synthesize the morning briefing."""
    if not ANTHROPIC_KEY:
        return _fallback_briefing(portfolio_text, news, perf_text)

    today = datetime.now(timezone.utc).strftime("%A %b %d, %Y")
    news_text = "\n".join(f"- {h}" for h in news)

    system_prompt = (
        "You are Ryn, Shami's YNAI5 AI assistant. Generate a concise morning briefing. "
        "Shami is a crypto investor in Aruba. Holdings: BTC, ETH, SOL, OPN, EIGEN, PENGU, BABY. "
        "Be direct, no fluff. High signal. Mobile-friendly (short lines). "
        "Use emojis sparingly but effectively."
    )

    user_prompt = f"""Generate a morning briefing for {today}.

PORTFOLIO:
{portfolio_text}

MARKET MOVERS (24h):
{movers_text}

NEWS:
{news_text}

PREDICTION ACCURACY:
{perf_text}

Format EXACTLY as:
MARKET_MOOD: [1 sentence on overall market sentiment]
PORTFOLIO_STATUS: [1-2 sentences on portfolio state, biggest mover, total value]
OPPORTUNITY: [coin | reason | confidence level]
RISK: [key risk to watch today, 1 sentence]
PREDICTION_SUGGESTION: [TICKER direction timeframe confidence] — e.g. "BTC up 72h 0.65"
BRIEFING_DONE"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        resp   = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        print(f"[Briefing] Claude error: {e}")
        return _fallback_briefing(portfolio_text, news, perf_text)


def _fallback_briefing(portfolio_text: str, news: list, perf_text: str) -> str:
    """Plain text briefing when AI is unavailable."""
    news_text = "\n".join(f"  - {h}" for h in news[:3])
    return (
        f"MARKET_MOOD: AI analysis unavailable — check manually\n"
        f"PORTFOLIO_STATUS: {portfolio_text.splitlines()[0]}\n"
        f"OPPORTUNITY: Manual review required\n"
        f"RISK: N/A\n"
        f"PREDICTION_SUGGESTION: none\n"
        f"NEWS:\n{news_text}\n"
        f"PREDICTION_ACCURACY: {perf_text}\n"
        f"BRIEFING_DONE"
    )


def _parse_briefing(raw: str) -> dict:
    """Parse structured briefing response."""
    fields = {
        "market_mood":           "",
        "portfolio_status":      "",
        "opportunity":           "",
        "risk":                  "",
        "prediction_suggestion": "",
    }
    for line in raw.splitlines():
        line = line.strip()
        for key in fields:
            prefix = key.upper().replace("_", "_") + ":"
            if line.startswith(prefix):
                fields[key] = line.split(":", 1)[1].strip()
    return fields


# ── Telegram sender ────────────────────────────────────────────────────────────
def _format_telegram_briefing(fields: dict, perf: dict | None, news: list) -> str:
    now      = datetime.now(timezone.utc)
    day_name = now.strftime("%a %b %d")

    ov     = (perf or {}).get("overall", {})
    streak = (perf or {}).get("streak", {})
    acc    = f"{ov.get('correct', 0)}/{ov.get('total', 0)} ({ov.get('accuracy_pct', 0):.0f}%)"
    streak_s = f"Streak: {streak.get('current_correct', 0)}✅"

    news_lines = "\n".join(f"  • {h}" for h in news[:3])

    lines = [
        f"🌅 <b>YNAI5 Morning Brief</b> — {day_name}",
        "",
        f"📰 {fields['market_mood']}" if fields['market_mood'] else "",
        f"💼 {fields['portfolio_status']}" if fields['portfolio_status'] else "",
        f"🎯 <b>Opportunity:</b> {fields['opportunity']}" if fields['opportunity'] else "",
        f"⚠️ <b>Risk:</b> {fields['risk']}" if fields['risk'] else "",
    ]

    if fields.get("prediction_suggestion") and fields["prediction_suggestion"].lower() not in ("none", "n/a", ""):
        lines.append(f"📊 <b>Log today:</b> {fields['prediction_suggestion']}")

    if news:
        lines += ["", "📰 <b>News:</b>", news_lines]

    lines += [
        "",
        f"🎲 Accuracy: {acc}  |  {streak_s}",
        "",
        "📱 /portfolio for full view",
    ]

    msg = "\n".join(l for l in lines if l is not None)
    return msg[:4000] + "\n..." if len(msg) > 4000 else msg


def _send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("[Telegram] Not configured — briefing not sent")
        return
    try:
        payload = json.dumps({
            "chat_id":    TELEGRAM_CHAT,
            "text":       message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        print("[Telegram] ✓ Morning briefing sent")
    except Exception as e:
        print(f"[Telegram] Failed: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{SEP}")
    print(f"  YNAI5 Morning Briefing")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{SEP}")

    # 1. Portfolio data
    print("[1/4] Reading portfolio data...", end=" ", flush=True)
    portfolio = _read_portfolio()
    if portfolio:
        total = portfolio.get("portfolio", {}).get("total_usd", 0)
        print(f"✓  (${total:,.2f})")
    else:
        print("⚠  Not found — briefing continues without portfolio data")

    # 2. Performance stats
    perf = _read_performance()
    ov   = (perf or {}).get("overall", {})
    print(f"[2/4] Prediction stats: {ov.get('correct', 0)}/{ov.get('total', 0)} correct")

    # 3. News
    print("[3/4] Fetching crypto news...", end=" ", flush=True)
    news = _fetch_crypto_news()
    print(f"✓  ({len(news)} headlines)")

    # 4. Market movers
    print("[4/4] Fetching market movers...", end=" ", flush=True)
    movers = _fetch_top_movers()
    print(f"✓  ({len(movers)} coins)")

    # Synthesize
    print("\n[AI] Generating briefing synthesis...", end=" ", flush=True)
    portfolio_text = _portfolio_summary_text(portfolio) if portfolio else "Portfolio data unavailable"
    perf_text      = _performance_summary_text(perf)
    movers_text    = _movers_text(movers)
    raw_briefing   = _generate_briefing(portfolio_text, news, perf_text, movers_text)
    fields         = _parse_briefing(raw_briefing)
    print("✓")

    # Format + send
    msg = _format_telegram_briefing(fields, perf, news)
    print(f"\n{SEP}")
    print("  MORNING BRIEFING PREVIEW")
    print(SEP)
    print(msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
    print(SEP)
    _send_telegram(msg)


if __name__ == "__main__":
    main()
