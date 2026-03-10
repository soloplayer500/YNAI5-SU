#!/usr/bin/env python3
"""
YNAI5 Market Report Bot
Daily comprehensive briefing: prices + Kraken portfolio + live news + AI analysis

Runs automatically via Windows Task Scheduler (8 AM, 6 PM, 9 PM daily).
Sends to Telegram — works 24/7 without Claude.

Keys read from .env.local:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  COINGECKO_API_KEY, KRAKEN_API_KEY, KRAKEN_API_SECRET
  BRAVE_SEARCH_API_KEY, GEMINI_API_KEY

No pip dependencies — stdlib only.
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
from datetime import datetime
from pathlib import Path

# Force UTF-8 on Windows console (needed for emoji in print statements)
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


# ── Portfolio Config ──────────────────────────────────────────────────────────

# Revolut holdings (no API — hardcoded from known positions, update if changed)
REVOLUT_HOLDINGS = {
    "bitcoin-cash": 0.01896,   # BCH — confirmed
    # BTC and SOL amounts unknown — tracked in Revolut app
}

# Full watchlist: avg_buy used for P&L calculation, alerts for threshold detection
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

# Kraken asset code → CoinGecko ID mapping
KRAKEN_ASSET_MAP = {
    "XXBT": "bitcoin", "XBT": "bitcoin",
    "XETH": "ethereum", "ETH": "ethereum",
    "SOL":  "solana",   "XSOL": "solana",
    "OPN":  "opinion",
    "EIGEN": "eigenlayer",
    "PENGU": "pudgy-penguins",
    "BABY":  "babylon",
    "BCH":   "bitcoin-cash",
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


# ── Kraken Portfolio ──────────────────────────────────────────────────────────

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
    """Convert raw Kraken balances to human-readable portfolio rows."""
    rows = []
    for asset, qty_str in raw_balances.items():
        qty = float(qty_str)
        if qty < 0.000001:
            continue
        coin_id = KRAKEN_ASSET_MAP.get(asset)
        if not coin_id or coin_id not in prices:
            continue
        price = prices[coin_id].get("usd", 0)
        sym = WATCHLIST[coin_id]["symbol"]
        avg = WATCHLIST[coin_id].get("avg_buy")
        pnl_pct = ((price - avg) / avg * 100) if avg else None
        rows.append({
            "symbol": sym,
            "qty": qty,
            "price": price,
            "usd_value": qty * price,
            "pnl_pct": pnl_pct,
        })
    rows.sort(key=lambda x: x["usd_value"], reverse=True)
    return rows


def revolut_portfolio(prices: dict) -> list:
    """Build Revolut rows from hardcoded holdings."""
    rows = []
    for coin_id, qty in REVOLUT_HOLDINGS.items():
        if coin_id not in prices:
            continue
        price = prices[coin_id].get("usd", 0)
        sym = WATCHLIST[coin_id]["symbol"]
        rows.append({
            "symbol": sym,
            "qty": qty,
            "price": price,
            "usd_value": qty * price,
        })
    return rows


# ── Brave News Search ─────────────────────────────────────────────────────────

def fetch_news(query: str = "crypto bitcoin market analysis today", count: int = 4) -> list:
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


# ── Gemini AI Analysis ────────────────────────────────────────────────────────

def gemini_analysis(context: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        )
        prompt = (
            "You are YNAI5, a personal crypto trading assistant for Shami in Aruba.\n\n"
            f"{context}\n\n"
            "Write a short mobile-friendly market briefing (max 160 words total):\n"
            "1. Market vibe — one punchy sentence (what's driving price action today)\n"
            "2. Two bullet points — notable moves or setups in the portfolio\n"
            "3. One action tip — what Shami should watch or do right now\n"
            "4. Final line: Sentiment: 🟢 Bullish / 🔴 Bearish / 🟡 Neutral\n\n"
            "Be direct, reference real prices, speak like a sharp trading friend. No fluff."
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


# ── Telegram Send ─────────────────────────────────────────────────────────────

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Not configured — set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env.local")
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
        print("[TELEGRAM] Report sent ✓")
    except Exception as e:
        print(f"[TELEGRAM] Failed: {e}")


# ── Build Report ──────────────────────────────────────────────────────────────

def build_report(
    now: str,
    session_label: str,
    prices: dict,
    kraken_rows: list,
    revolut_rows: list,
    news: list,
    analysis: str,
) -> str:
    lines = [f"<b>📊 YNAI5 Daily Briefing — {now} ({session_label})</b>", ""]

    # ── Prices ──
    lines.append("💹 <b>PRICES</b>")
    alerts_active = []
    context_prices = []

    for coin_id, cfg in WATCHLIST.items():
        sym = cfg["symbol"]
        data = prices.get(coin_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change", 0.0)

        if price is None:
            lines.append(f"  {sym}: NO DATA")
            continue

        sign = "+" if change >= 0 else ""
        trend = "🟢" if change >= 0 else "🔴"
        move = " ⚡" if abs(change) >= 8 else ""

        avg = cfg.get("avg_buy")
        pnl = ""
        if avg:
            pct = (price - avg) / avg * 100
            pnl = f"  [{'+' if pct >= 0 else ''}{pct:.0f}% vs buy]"

        lines.append(f"  {trend} <b>{sym}</b>: ${price:,.4f}  {sign}{change:.1f}%{move}{pnl}")
        context_prices.append(f"{sym}: ${price:,.4f} ({sign}{change:.1f}% 24h, avg buy: ${avg or 'N/A'})")

        for threshold, direction in cfg["alerts"]:
            if direction == "DOWN" and price <= threshold:
                alerts_active.append(f"⬇️ {sym} @ ${price:,.4f} hit ${threshold} support")
            elif direction == "UP" and price >= threshold:
                alerts_active.append(f"⬆️ {sym} @ ${price:,.4f} hit ${threshold} target")

    lines.append("")

    # ── Portfolio Snapshot ──
    total_usd = 0.0
    if kraken_rows:
        kraken_total = sum(r["usd_value"] for r in kraken_rows)
        total_usd += kraken_total
        lines.append(f"💼 <b>KRAKEN</b>  ~${kraken_total:,.0f} USD")
        for r in kraken_rows:
            pnl_str = ""
            if r.get("pnl_pct") is not None:
                p = r["pnl_pct"]
                pnl_str = f"  [{'+' if p >= 0 else ''}{p:.0f}% P&L]"
            lines.append(
                f"  {r['symbol']}: {r['qty']:.4f} @ ${r['price']:,.2f} = ${r['usd_value']:,.0f}{pnl_str}"
            )
        lines.append("")

    if revolut_rows:
        rev_total = sum(r["usd_value"] for r in revolut_rows)
        total_usd += rev_total
        lines.append(f"📱 <b>REVOLUT</b>  ~${rev_total:,.0f} USD (known positions only)")
        for r in revolut_rows:
            lines.append(
                f"  {r['symbol']}: {r['qty']:.5f} @ ${r['price']:,.2f} = ${r['usd_value']:,.0f}"
            )
        lines.append("  BTC + SOL amounts tracked in app — check manually")
        lines.append("")

    if total_usd > 0:
        lines.append(f"📊 <b>TRACKED TOTAL: ~${total_usd:,.0f} USD</b>")
        lines.append("")

    # ── Active Alerts ──
    if alerts_active:
        lines.append("🚨 <b>ALERTS TRIGGERED</b>")
        for a in alerts_active:
            lines.append(f"  {a}")
        lines.append("")

    # ── News ──
    if news:
        lines.append("📰 <b>MARKET NEWS</b>")
        for item in news:
            title = item["title"][:85]
            age = f" ({item['age']})" if item.get("age") else ""
            lines.append(f"  • {title}{age}")
        lines.append("")

    # ── Gemini AI Analysis ──
    if analysis:
        lines.append("🤖 <b>YNAI5 ANALYSIS</b>")
        lines.append(analysis)
        lines.append("")

    lines.append("— YNAI5 Alert Bot 🤖")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")
    hour = now.hour
    if hour < 12:
        session_label = "Morning ☀️"
    elif hour < 18:
        session_label = "Afternoon 🌤️"
    elif hour < 21:
        session_label = "Evening 🌆"
    else:
        session_label = "Night 🌙"

    print(f"\n{'='*55}")
    print(f"  YNAI5 Market Report — {now_str} ({session_label})")
    print(f"{'='*55}\n")

    print("  [1/4] Fetching prices from CoinGecko...")
    prices = fetch_prices()
    if not prices:
        print("  [ERROR] No price data — aborting.")
        return

    print("  [2/4] Fetching Kraken portfolio...")
    kraken_raw = fetch_kraken_balance()
    kraken_rows = kraken_to_portfolio(kraken_raw, prices) if kraken_raw else []
    revolut_rows = revolut_portfolio(prices)

    print("  [3/4] Fetching crypto news via Brave Search...")
    news = fetch_news("bitcoin ethereum crypto market today analysis")

    print("  [4/4] Generating AI analysis via Gemini...")
    ctx = (
        "Current portfolio prices:\n" + "\n".join(context_prices_list(prices)) + "\n\n"
        "Latest news:\n" + "\n".join(f"- {n['title']}" for n in news)
    )
    analysis = gemini_analysis(ctx)

    report = build_report(now_str, session_label, prices, kraken_rows, revolut_rows, news, analysis)

    # Console preview (strip HTML tags)
    print("\n--- PREVIEW ---")
    print(re.sub(r"<[^>]+>", "", report))
    print("--- END ---\n")

    send_telegram(report)


def context_prices_list(prices: dict) -> list:
    rows = []
    for coin_id, cfg in WATCHLIST.items():
        sym = cfg["symbol"]
        data = prices.get(coin_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change", 0.0)
        avg = cfg.get("avg_buy")
        if price:
            sign = "+" if change >= 0 else ""
            pnl = f", {'+' if avg and price >= avg else ''}{((price-avg)/avg*100):.0f}% vs avg" if avg else ""
            rows.append(f"{sym}: ${price:,.4f} ({sign}{change:.1f}% 24h{pnl})")
    return rows


if __name__ == "__main__":
    main()
