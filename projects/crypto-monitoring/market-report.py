#!/usr/bin/env python3
"""
YNAI5 Market Report Bot v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends to Telegram 3x/day via Windows Task Scheduler.

Section order:
  Header → Portfolio Total → Market Pulse (w/ RSI) →
  Holdings → Active Alerts → News → YNAI5 AI Take
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keys from .env.local:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  COINGECKO_API_KEY, KRAKEN_API_KEY, KRAKEN_API_SECRET
  BRAVE_SEARCH_API_KEY, GEMINI_API_KEY

No pip installs — stdlib only.
"""

import base64
import hashlib
import hmac
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ── UTF-8 fix for Windows console ────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ── Load .env.local ───────────────────────────────────────────────────────────
def load_env() -> dict:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env.local"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
TELEGRAM_BOT_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = ENV.get("TELEGRAM_CHAT_ID", "")
COINGECKO_API_KEY  = ENV.get("COINGECKO_API_KEY", "")
KRAKEN_API_KEY     = ENV.get("KRAKEN_API_KEY", "")
KRAKEN_API_SECRET  = ENV.get("KRAKEN_API_SECRET", "")
BRAVE_SEARCH_KEY   = ENV.get("BRAVE_SEARCH_API_KEY", "")
GEMINI_API_KEY     = ENV.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = ENV.get("OPENROUTER_API_KEY", "")

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


# ── Portfolio config ──────────────────────────────────────────────────────────
def load_revolut_config() -> dict:
    """Load Revolut holdings from revolut-config.json (browser-scraped or manual)."""
    cfg_path = Path(__file__).resolve().parent / "revolut-config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"holdings": {"bitcoin-cash": {"qty": 0.01896}}}


REVOLUT_CFG = load_revolut_config()

WATCHLIST = {
    "opinion":        {"symbol": "OPN",   "avg_buy": 0.3326, "alerts": [(0.18, "DOWN"), (0.45, "UP"), (0.60, "UP")]},
    "bitcoin":        {"symbol": "BTC",   "avg_buy": 90111,  "alerts": [(55000, "DOWN"), (90000, "UP"), (110000, "UP")]},
    "ethereum":       {"symbol": "ETH",   "avg_buy": 3151,   "alerts": [(1500, "DOWN"), (3000, "UP"), (4000, "UP")]},
    "solana":         {"symbol": "SOL",   "avg_buy": 151,    "alerts": [(60, "DOWN"), (120, "UP"), (200, "UP")]},
    "eigenlayer":     {"symbol": "EIGEN", "avg_buy": 0.30,   "alerts": [(0.10, "DOWN"), (0.40, "UP"), (1.00, "UP")]},
    "pudgy-penguins": {"symbol": "PENGU", "avg_buy": None,   "alerts": [(0.003, "DOWN"), (0.015, "UP"), (0.040, "UP")]},
    "bitcoin-cash":   {"symbol": "BCH",   "avg_buy": None,   "alerts": [(250, "DOWN"), (450, "UP"), (600, "UP")]},
    "babylon":        {"symbol": "BABY",  "avg_buy": 0.028,  "alerts": [(0.008, "DOWN"), (0.025, "UP"), (0.050, "UP")]},
}

# Kraken asset code → CoinGecko ID
KRAKEN_ASSET_MAP = {
    "XXBT": "bitcoin",  "XBT": "bitcoin",
    "XETH": "ethereum", "ETH": "ethereum",
    "SOL":  "solana",   "XSOL": "solana",
    "OPN":  "opinion",
    "EIGEN": "eigenlayer",
    "PENGU": "pudgy-penguins",
    "BABY":  "babylon",
    "BCH":   "bitcoin-cash",
}

# Kraken public OHLC pair codes (for RSI — no API key needed)
KRAKEN_OHLC_PAIRS = {
    "bitcoin":      "XBTUSD",
    "ethereum":     "ETHUSD",
    "solana":       "SOLUSD",
    "bitcoin-cash": "BCHUSD",
}


# ── CoinGecko Prices ──────────────────────────────────────────────────────────
def fetch_prices() -> dict:
    ids = ",".join(WATCHLIST.keys())
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    )
    headers = {"Accept": "application/json", "User-Agent": "YNAI5-Bot/2.0"}
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[CoinGecko] Error: {e}")
        return {}


# ── Kraken OHLC + RSI (public API, no key needed) ────────────────────────────
def fetch_kraken_ohlc(pair: str, interval: int = 60, count: int = 25) -> list:
    """Fetch hourly closing prices from Kraken public OHLC endpoint."""
    try:
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
        req = urllib.request.Request(url, headers={"User-Agent": "YNAI5-Bot/2.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result = data.get("result", {})
        # Result has one key (Kraken pair name) + "last"
        candles = next((v for k, v in result.items() if k != "last"), [])
        # Candle format: [time, open, high, low, close, vwap, volume, count]
        return [float(c[4]) for c in candles[-count:]]
    except Exception as e:
        print(f"[OHLC {pair}] {e}")
        return []


def calculate_rsi(closes: list, period: int = 14):
    """RSI from closing prices. Returns float or None if insufficient data."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains  = [max(0.0, d) for d in deltas[-period:]]
    losses = [abs(min(0.0, d)) for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def rsi_tag(rsi) -> str:
    if rsi is None:
        return ""
    if rsi < 30:
        return f"  🔥RSI {rsi:.0f}"    # oversold
    if rsi < 45:
        return f"  📉RSI {rsi:.0f}"    # bearish lean
    if rsi < 55:
        return f"  RSI {rsi:.0f}"      # neutral
    if rsi < 70:
        return f"  📈RSI {rsi:.0f}"    # bullish lean
    return f"  ❄️RSI {rsi:.0f}"        # overbought


def get_technical_signals() -> dict:
    """Returns {coin_id: rsi_float} for coins with Kraken OHLC data."""
    signals = {}
    for coin_id, pair in KRAKEN_OHLC_PAIRS.items():
        closes = fetch_kraken_ohlc(pair)
        rsi = calculate_rsi(closes)
        if rsi is not None:
            signals[coin_id] = rsi
    return signals


# ── Kraken Private Portfolio ──────────────────────────────────────────────────
def fetch_kraken_balance() -> dict:
    if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
        return {}
    try:
        path = "/0/private/Balance"
        nonce = str(int(time.time() * 1000))
        post_data = f"nonce={nonce}"
        msg = path.encode() + hashlib.sha256((nonce + post_data).encode()).digest()
        mac = hmac.new(base64.b64decode(KRAKEN_API_SECRET), msg, hashlib.sha512)
        sig = base64.b64encode(mac.digest()).decode()
        req = urllib.request.Request(
            f"https://api.kraken.com{path}",
            data=post_data.encode(),
            headers={
                "API-Key": KRAKEN_API_KEY,
                "API-Sign": sig,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data.get("result", {})
    except Exception as e:
        print(f"[Kraken] Error: {e}")
        return {}


def kraken_to_portfolio(raw_balances: dict, prices: dict) -> list:
    rows = []
    for asset, qty_str in raw_balances.items():
        qty = float(qty_str)
        if qty < 0.000001:
            continue
        coin_id = KRAKEN_ASSET_MAP.get(asset)
        if not coin_id or coin_id not in prices:
            continue
        price = prices[coin_id].get("usd", 0)
        sym   = WATCHLIST[coin_id]["symbol"]
        avg   = WATCHLIST[coin_id].get("avg_buy")
        pnl   = ((price - avg) / avg * 100) if avg else None
        rows.append({
            "symbol":    sym,
            "qty":       qty,
            "price":     price,
            "usd_value": qty * price,
            "pnl_pct":   pnl,
        })
    rows.sort(key=lambda x: x["usd_value"], reverse=True)
    return rows


def revolut_portfolio(prices: dict) -> list:
    """Build Revolut rows from revolut-config.json holdings."""
    rows = []
    for coin_id, info in REVOLUT_CFG.get("holdings", {}).items():
        qty = info.get("qty") if isinstance(info, dict) else info
        if not qty or coin_id not in prices:
            continue
        price = prices[coin_id].get("usd", 0)
        sym   = WATCHLIST.get(coin_id, {}).get("symbol", coin_id.upper())
        rows.append({
            "symbol":    sym,
            "qty":       qty,
            "price":     price,
            "usd_value": qty * price,
        })
    return rows


# ── Brave News ────────────────────────────────────────────────────────────────
def fetch_news(query: str = "bitcoin ethereum crypto market today", count: int = 3) -> list:
    if not BRAVE_SEARCH_KEY:
        return []
    try:
        url = (
            f"https://api.search.brave.com/res/v1/news/search"
            f"?q={urllib.parse.quote(query)}&count={count}"
        )
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_SEARCH_KEY,
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return [
            {"title": item.get("title", ""), "age": item.get("age", "")}
            for item in data.get("results", [])[:count]
        ]
    except Exception as e:
        print(f"[Brave News] Error: {e}")
        return []


# ── Gemini Analysis (fallback) ────────────────────────────────────────────────
def gemini_analysis(context: str) -> str:
    """Fallback analysis using Gemini Flash (free). Used if OpenRouter unavailable."""
    if not GEMINI_API_KEY:
        return ""
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        )
        prompt = (
            "You are YNAI5 — Shami's personal AI trading partner in Aruba. "
            "Sharp, direct, no fluff. You know his exact positions.\n\n"
            f"{context}\n\n"
            "Give a punchy mobile-friendly market take (max 130 words):\n"
            "→ Line 1: What's driving price action TODAY (one sharp sentence)\n"
            "→ 2 bullets: positions Shami should focus on right now\n"
            "→ One action line: Watch / Trim / Hold / Buy dip at $X\n"
            "→ Final line: Mood: 🟢 Bullish | 🔴 Bearish | 🟡 Neutral\n\n"
            "Use real numbers. Speak like a sharp friend, not a bot."
        )
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return ""


# ── Kimi Analysis (primary — smarter, parallel) ───────────────────────────────
def _kimi_call(task: str, role_prompt: str) -> str:
    """Single Kimi K2.5 call via OpenRouter. Returns response text."""
    payload = json.dumps({
        "model": "moonshotai/kimi-k2.5",
        "messages": [
            {"role": "system", "content": role_prompt},
            {"role": "user",   "content": task}
        ],
        "max_tokens": 600
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
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    return result["choices"][0]["message"]["content"].strip()


def kimi_analysis(context: str, deep: bool = False) -> str:
    """
    Kimi-powered market analysis.
    deep=False → single sharp take (morning/afternoon)
    deep=True  → 3-perspective swarm consensus (evening — trader, analyst, critic)
    """
    if not OPENROUTER_API_KEY:
        print("[Kimi] No OPENROUTER_API_KEY — falling back to Gemini")
        return gemini_analysis(context)

    base_system = (
        "You are YNAI5 — Shami's personal AI trading partner based in Aruba. "
        "Sharp, direct, mobile-friendly. Max 100 words per response. "
        "Use real prices. Speak like a sharp friend who knows crypto."
    )

    task = (
        f"Current portfolio data:\n{context}\n\n"
        "Give a punchy market take:\n"
        "→ Line 1: What's driving price action TODAY (one sentence, real drivers)\n"
        "→ 2 bullets: which of Shami's positions need attention RIGHT NOW\n"
        "→ Action: Watch / Trim / Hold / Buy dip at $X — be specific\n"
        "→ Mood: 🟢 Bullish | 🔴 Bearish | 🟡 Neutral"
    )

    try:
        if not deep:
            # Single call — fast, cheap (~$0.0002)
            return _kimi_call(task, base_system)

        # Deep mode (evening): 3 roles in parallel → synthesize
        roles = {
            "trader":    base_system + " You are a crypto trader focused on technicals and momentum.",
            "analyst":   base_system + " You are a macro analyst focused on fundamentals and market structure.",
            "contrarian": base_system + " You are a contrarian thinker — challenge the obvious narrative."
        }

        perspectives = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_kimi_call, task, prompt): role
                for role, prompt in roles.items()
            }
            for future in as_completed(futures):
                role = futures[future]
                try:
                    perspectives[role] = future.result()
                except Exception as e:
                    perspectives[role] = f"[error: {e}]"

        print(f"  [Kimi Swarm] 3 perspectives collected → synthesizing")

        synthesis_task = (
            f"3 AI perspectives on this portfolio:\n\n"
            f"TRADER: {perspectives.get('trader', '')}\n\n"
            f"ANALYST: {perspectives.get('analyst', '')}\n\n"
            f"CONTRARIAN: {perspectives.get('contrarian', '')}\n\n"
            "Synthesize into ONE actionable take (max 120 words). "
            "Flag any disagreements. End with overall Mood emoji."
        )
        return _kimi_call(synthesis_task, base_system)

    except Exception as e:
        print(f"[Kimi] Error: {e} — falling back to Gemini")
        return gemini_analysis(context)


# ── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Not configured — set tokens in .env.local")
        return
    try:
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        print("[TELEGRAM] ✓ Sent")
    except Exception as e:
        print(f"[TELEGRAM] Failed: {e}")


# ── Format helpers ────────────────────────────────────────────────────────────
def fmt_price(price: float) -> str:
    if price >= 10000: return f"${price:,.0f}"
    if price >= 1000:  return f"${price:,.0f}"
    if price >= 1:     return f"${price:,.2f}"
    if price >= 0.01:  return f"${price:.4f}"
    return f"${price:.6f}"


def pnl_tag(price: float, avg) -> str:
    if not avg:
        return ""
    pct  = (price - avg) / avg * 100
    sign = "+" if pct >= 0 else ""
    icon = "🟢" if pct >= 5 else ("🔴" if pct <= -5 else "🟡")
    return f"  {icon}{sign}{pct:.0f}%"


# ── Build Report ──────────────────────────────────────────────────────────────
def build_report(
    now_str: str,
    session_label: str,
    prices: dict,
    kraken_rows: list,
    revolut_rows: list,
    signals: dict,
    news: list,
    analysis: str,
) -> str:
    """Professional Block Syndicate briefing card — clean, readable, channel-quality."""

    SEP_BOLD  = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    SEP_LIGHT = "─────────────────────────────"

    lines = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    lines += [
        SEP_BOLD,
        f"📊 <b>BLOCK SYNDICATE</b>  ·  {session_label}",
        f"📅 {now_str} AST",
        SEP_BOLD,
        "",
    ]

    # ── PORTFOLIO TOTAL ───────────────────────────────────────────────────────
    kraken_total  = sum(r["usd_value"] for r in kraken_rows)
    revolut_known = sum(r["usd_value"] for r in revolut_rows)
    grand_total   = kraken_total + revolut_known

    lines += [
        f"💰 <b>PORTFOLIO</b>  ·  <b>${grand_total:,.0f} total</b>",
        f"   Kraken ${kraken_total:,.0f}  ·  Revolut ${revolut_known:,.0f}+",
        "",
    ]

    # ── MARKET REGIME ─────────────────────────────────────────────────────────
    # Use BTC's 24h change and overall green/red ratio to determine regime
    btc_data   = prices.get("bitcoin", {})
    btc_change = btc_data.get("usd_24h_change", 0.0)
    greens     = sum(1 for cid in WATCHLIST if prices.get(cid, {}).get("usd_24h_change", 0) >= 0)
    reds       = len(WATCHLIST) - greens
    green_pct  = greens / max(len(WATCHLIST), 1) * 100

    if green_pct >= 65:
        regime_label = "🟢 <b>RISK-ON</b>  ·  Bulls in control"
    elif green_pct >= 45:
        regime_label = "🟡 <b>NEUTRAL</b>  ·  Mixed signals — wait for direction"
    else:
        regime_label = "🔴 <b>RISK-OFF</b>  ·  Bears leading — preserve capital"

    lines += [
        SEP_LIGHT,
        f"🌡 <b>MARKET REGIME</b>",
        f"   {regime_label}",
        f"   Market: {greens}🟢 {reds}🔴  ·  BTC {'+' if btc_change >= 0 else ''}{btc_change:.1f}% 24h",
        "",
    ]

    # ── MARKET PRICES ─────────────────────────────────────────────────────────
    lines += [
        SEP_LIGHT,
        "💹 <b>MARKET PRICES</b>",
        "",
    ]

    alerts_active = []
    for coin_id, cfg in WATCHLIST.items():
        sym    = cfg["symbol"]
        data   = prices.get(coin_id, {})
        price  = data.get("usd")
        change = data.get("usd_24h_change", 0.0)

        if price is None:
            lines.append(f"   ⚠️ <b>{sym}</b>: no data")
            continue

        sign  = "+" if change >= 0 else ""
        trend = "🟢" if change >= 0 else "🔴"
        arrow = "▲" if change >= 0 else "▼"
        bang  = "  ⚡" if abs(change) >= 8 else ""
        pnl   = pnl_tag(price, cfg.get("avg_buy"))

        # RSI tag
        rsi_val = signals.get(coin_id)
        if rsi_val is not None:
            if rsi_val >= 70:
                rsi_s = f"  · RSI {rsi_val:.0f} ⚠️ OB"
            elif rsi_val <= 30:
                rsi_s = f"  · RSI {rsi_val:.0f} ⚠️ OS"
            else:
                rsi_s = f"  · RSI {rsi_val:.0f}"
        else:
            rsi_s = ""

        lines.append(
            f"   {trend} <b>{sym:<6}</b>  {fmt_price(price):<12}  {arrow}{sign}{change:.1f}%{bang}{pnl}{rsi_s}"
        )

        # Collect threshold alerts
        for threshold, direction in cfg["alerts"]:
            if direction == "DOWN" and price <= threshold:
                alerts_active.append(f"⬇️ <b>{sym}</b> {fmt_price(price)} — hit ${threshold} support")
            elif direction == "UP" and price >= threshold:
                alerts_active.append(f"⬆️ <b>{sym}</b> {fmt_price(price)} — hit ${threshold} target")

    lines.append("")

    # ── MY HOLDINGS ───────────────────────────────────────────────────────────
    if kraken_rows:
        lines += [
            SEP_LIGHT,
            "💼 <b>MY HOLDINGS</b>",
            "",
        ]
        for r in kraken_rows:
            p_val = r.get("pnl_pct")
            ch24  = next(
                (prices.get(cid, {}).get("usd_24h_change", 0)
                 for cid, cfg in WATCHLIST.items() if cfg["symbol"] == r["symbol"]),
                None,
            )

            pnl_dot = "🟢" if (p_val or 0) >= 0 else "🔴"
            pnl_s   = f"{pnl_dot} {'+' if (p_val or 0) >= 0 else ''}{p_val:.0f}% vs entry" if p_val is not None else "⚪ no entry"

            ch_s = ""
            if ch24 is not None:
                arrow = "▲" if ch24 >= 0 else "▼"
                bang  = "  ⚡" if abs(ch24) >= 8 else ""
                ch_s  = f"  ·  {arrow}{abs(ch24):.1f}% today{bang}"

            lines.append(f"   <b>{r['symbol']:<6}</b>  ${r['usd_value']:>7,.0f}  {pnl_s}{ch_s}")

        if revolut_rows:
            lines.append("")
            for r in revolut_rows:
                lines.append(f"   <b>{r['symbol']:<6}</b>  ${r['usd_value']:>7,.0f}  (Revolut)")
            lines.append("   BTC + SOL: check Revolut app 📱")

        lines.append("")

    # ── ACTIVE ALERTS ─────────────────────────────────────────────────────────
    if alerts_active:
        lines += [SEP_LIGHT, "🚨 <b>ALERTS TRIGGERED</b>", ""]
        for a in alerts_active:
            lines.append(f"   {a}")
        lines.append("")

    # ── NEWS ──────────────────────────────────────────────────────────────────
    if news:
        lines += [SEP_LIGHT, "📰 <b>HEADLINES</b>", ""]
        for item in news[:4]:
            title = item["title"][:78]
            age   = f" ({item['age']})" if item.get("age") else ""
            lines.append(f"   • {title}{age}")
        lines.append("")

    # ── AI ANALYST TAKE ───────────────────────────────────────────────────────
    if analysis:
        lines += [SEP_LIGHT, "🤖 <b>YNAI5 ANALYST TAKE</b>", ""]
        # Format as bullet points if not already
        for sentence in analysis.replace("• ", "\n• ").split("\n"):
            s = sentence.strip()
            if not s:
                continue
            if not s.startswith("•") and not s.startswith("▸"):
                s = f"▸ {s}"
            lines.append(f"   {s}")
        lines.append("")

    # ── FOOTER ────────────────────────────────────────────────────────────────
    lines += [
        SEP_BOLD,
        "📌 Free signals  →  @BlockSyndicateFree",
        "💎 VIP setups    →  @BlockSyndicateVip",
        SEP_BOLD,
    ]

    return "\n".join(lines)


# ── Context for Gemini ────────────────────────────────────────────────────────
def build_context(prices: dict, signals: dict, news: list) -> str:
    price_lines = []
    for coin_id, cfg in WATCHLIST.items():
        sym    = cfg["symbol"]
        data   = prices.get(coin_id, {})
        price  = data.get("usd")
        change = data.get("usd_24h_change", 0.0)
        avg    = cfg.get("avg_buy")
        if price:
            sign = "+" if change >= 0 else ""
            pnl  = f", {'+' if avg and price >= avg else ''}{((price-avg)/avg*100):.0f}% vs avg" if avg else ""
            rsi  = signals.get(coin_id)
            rsi_s = f", RSI {rsi:.0f}" if rsi else ""
            price_lines.append(f"{sym}: {fmt_price(price)} ({sign}{change:.1f}% 24h{pnl}{rsi_s})")
    news_lines = [f"- {n['title']}" for n in news]
    return (
        "Current portfolio:\n" + "\n".join(price_lines) +
        ("\n\nLatest news:\n" + "\n".join(news_lines) if news_lines else "")
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")
    h = now.hour
    if h < 12:
        session_label = "Morning ☀️"
    elif h < 18:
        session_label = "Afternoon 🌤️"
    elif h < 21:
        session_label = "Evening 🌆"
    else:
        session_label = "Night 🌙"

    print(f"\n{'━'*52}")
    print(f"  YNAI5 Market Report v2 — {now_str} ({session_label})")
    print(f"{'━'*52}\n")

    print("  [1/5] Prices from CoinGecko...")
    prices = fetch_prices()
    if not prices:
        print("  [ERROR] No price data — aborting.")
        return

    print("  [2/5] Kraken portfolio...")
    kraken_raw   = fetch_kraken_balance()
    kraken_rows  = kraken_to_portfolio(kraken_raw, prices) if kraken_raw else []
    revolut_rows = revolut_portfolio(prices)

    print("  [3/5] Technical signals (Kraken OHLC → RSI)...")
    signals = get_technical_signals()
    for coin_id, rsi in signals.items():
        sym = WATCHLIST.get(coin_id, {}).get("symbol", coin_id)
        print(f"      {sym}: RSI {rsi:.0f}")

    print("  [4/5] News via Brave Search...")
    news = fetch_news("bitcoin ethereum crypto market today analysis")

    # Deep mode = evening report (richer 3-perspective swarm)
    deep_mode = h >= 17
    mode_label = "Kimi Swarm 3x" if deep_mode else "Kimi"
    print(f"  [5/5] {mode_label} AI analysis...")
    ctx      = build_context(prices, signals, news)
    analysis = kimi_analysis(ctx, deep=deep_mode)

    report = build_report(
        now_str, session_label, prices, kraken_rows,
        revolut_rows, signals, news, analysis
    )

    # Console preview (strip HTML tags for readability)
    print("\n" + "━" * 52)
    print(re.sub(r"<[^>]+>", "", report))
    print("━" * 52 + "\n")

    send_telegram(report)


if __name__ == "__main__":
    main()
