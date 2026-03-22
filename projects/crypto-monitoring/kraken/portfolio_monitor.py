#!/usr/bin/env python3
"""
YNAI5 Kraken Portfolio Monitor v1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pulls live Kraken portfolio data (read-only API key).
Outputs kraken_portfolio.json + sends compact Telegram push.
Runs every 30min via GitHub Actions. Also callable locally.

Keys from .env.local (root of YNAI5-SU/):
  KRAKEN_PORTFOLIO_API_KEY, KRAKEN_PORTFOLIO_API_SECRET
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  COINGECKO_API_KEY

Dependencies: krakenex, requests (pip install krakenex requests)
              stdlib: json, time, sys, pathlib, datetime, urllib
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import krakenex
except ImportError:
    print("[ERROR] krakenex not installed. Run: pip install krakenex requests")
    sys.exit(1)

# ── UTF-8 fix for Windows console ─────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).resolve().parent           # kraken/
ENV_PATH    = HERE.parent.parent.parent / ".env.local"  # YNAI5-SU/.env.local
OUTPUT_FILE = HERE / "kraken_portfolio.json"
CACHE_FILE  = HERE / ".cache.json"

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CACHE_TTL   = 300  # 5 minutes


# ── Load .env.local ────────────────────────────────────────────────────────────
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

KRAKEN_API_KEY    = ENV.get("KRAKEN_PORTFOLIO_API_KEY", "")
KRAKEN_API_SECRET = ENV.get("KRAKEN_PORTFOLIO_API_SECRET", "")
TELEGRAM_TOKEN    = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID  = ENV.get("TELEGRAM_CHAT_ID", "")
COINGECKO_KEY     = ENV.get("COINGECKO_API_KEY", "")

if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    print("[ERROR] KRAKEN_PORTFOLIO_API_KEY and KRAKEN_PORTFOLIO_API_SECRET not found in .env.local")
    print(f"        Looked in: {ENV_PATH}")
    sys.exit(1)


# ── Kraken asset code → CoinGecko ID ──────────────────────────────────────────
KRAKEN_ASSET_MAP = {
    "XXBT": "bitcoin",       "XBT": "bitcoin",    "XBTC": "bitcoin",
    "XETH": "ethereum",      "ETH": "ethereum",
    "SOL":  "solana",        "XSOL": "solana",
    "OPN":  "opinion",
    "EIGEN": "eigenlayer",
    "PENGU": "pudgy-penguins",
    "BABY":  "babylon",
    "BCH":   "bitcoin-cash",  "XBCH": "bitcoin-cash",
    "ZUSD": "usd-coin",      "USD": "usd-coin",   # treat as stablecoin
    "USDT": "tether",        "USDC": "usd-coin",
}

# Kraken asset code → clean display symbol (handles double-X prefix like XXBT → BTC)
KRAKEN_DISPLAY_SYMBOL = {
    "XXBT": "BTC", "XBT": "BTC", "XBTC": "BTC",
    "XETH": "ETH",
    "XSOL": "SOL",
    "XBCH": "BCH",
}

# Known avg buy prices (update as positions change)
AVG_BUY = {
    "bitcoin":        90111.0,
    "ethereum":       3151.0,
    "solana":         151.0,
    "opinion":        0.3326,
    "eigenlayer":     0.30,
    "babylon":        0.028,
}

STABLECOINS = {"usd-coin", "tether", "zusd"}


# ── Cache helpers ──────────────────────────────────────────────────────────────
def load_cache() -> dict | None:
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if time.time() - data.get("cached_at", 0) < CACHE_TTL:
                return data.get("portfolio")
    except Exception:
        pass
    return None


def save_cache(portfolio: dict):
    try:
        CACHE_FILE.write_text(
            json.dumps({"cached_at": time.time(), "portfolio": portfolio}, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


# ── Kraken API client ──────────────────────────────────────────────────────────
def _get_api() -> krakenex.API:
    api = krakenex.API()
    api.key    = KRAKEN_API_KEY
    api.secret = KRAKEN_API_SECRET
    return api


def _safe_private(method: str, params: dict = None, retries: int = 2) -> dict:
    """Call Kraken private endpoint with rate-limit retry."""
    api = _get_api()
    for attempt in range(retries):
        try:
            resp = api.query_private(method, params or {})
            errors = resp.get("error", [])
            if errors:
                if any("Too many requests" in e for e in errors):
                    print(f"[Kraken] Rate limited — waiting 3s (attempt {attempt + 1}/{retries})")
                    time.sleep(3)
                    continue
                print(f"[Kraken] API error on {method}: {errors}")
                return {}
            return resp.get("result", {})
        except Exception as e:
            print(f"[Kraken] Exception on {method}: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return {}


def _safe_public(method: str, params: dict = None) -> dict:
    """Call Kraken public endpoint (no auth needed)."""
    api = krakenex.API()
    try:
        resp = api.query_public(method, params or {})
        errors = resp.get("error", [])
        if errors:
            print(f"[Kraken Public] {method} error: {errors}")
            return {}
        return resp.get("result", {})
    except Exception as e:
        print(f"[Kraken Public] Exception on {method}: {e}")
        return {}


# ── CoinGecko prices ───────────────────────────────────────────────────────────
def _fetch_coingecko_prices(coin_ids: list) -> dict:
    """Batch fetch USD prices from CoinGecko."""
    if not coin_ids:
        return {}
    ids_str = ",".join(set(coin_ids))
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"
    )
    headers = {"Accept": "application/json", "User-Agent": "YNAI5-KrakenMonitor/1.0"}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[CoinGecko] Error: {e}")
        return {}


# ── Core functions ─────────────────────────────────────────────────────────────
def get_account_balance(prices: dict = None) -> dict:
    """
    Returns all non-zero Kraken balances with USD values.
    prices: optional pre-fetched CoinGecko price dict (to avoid double-fetching)
    """
    raw = _safe_private("Balance")
    if not raw:
        return {"balances": [], "total_usd": 0.0, "stablecoins_usd": 0.0, "fetched_at": _now()}

    # Filter dust
    holdings = {k: float(v) for k, v in raw.items() if float(v) >= 0.000001}

    # Identify coin IDs needed for pricing
    coin_ids = []
    for asset in holdings:
        cg_id = KRAKEN_ASSET_MAP.get(asset)
        if cg_id:
            coin_ids.append(cg_id)

    if prices is None:
        prices = _fetch_coingecko_prices(coin_ids)

    balances = []
    total_usd = 0.0
    stablecoins_usd = 0.0

    for asset, qty in holdings.items():
        cg_id = KRAKEN_ASSET_MAP.get(asset)
        if not cg_id:
            # Unknown asset — include without USD value
            balances.append({
                "asset": asset, "symbol": asset, "coingecko_id": None,
                "qty": qty, "price_usd": None, "usd_value": 0.0,
                "change_24h_pct": None, "avg_buy": None, "pnl_pct": None,
                "is_stablecoin": False,
            })
            continue

        price_data = prices.get(cg_id, {})
        price_usd  = price_data.get("usd", 0.0)
        change_24h = price_data.get("usd_24h_change")
        usd_value  = qty * price_usd
        avg_buy    = AVG_BUY.get(cg_id)
        is_stable  = cg_id in STABLECOINS

        pnl_pct = None
        if avg_buy and not is_stable:
            pnl_pct = round((price_usd - avg_buy) / avg_buy * 100, 1)

        total_usd += usd_value
        if is_stable:
            stablecoins_usd += usd_value

        balances.append({
            "asset":          asset,
            "symbol":         KRAKEN_DISPLAY_SYMBOL.get(asset, asset.lstrip("X").rstrip("Z") if len(asset) > 3 else asset),
            "coingecko_id":   cg_id,
            "qty":            qty,
            "price_usd":      price_usd,
            "usd_value":      round(usd_value, 2),
            "change_24h_pct": round(change_24h, 2) if change_24h is not None else None,
            "avg_buy":        avg_buy,
            "pnl_pct":        pnl_pct,
            "is_stablecoin":  is_stable,
        })

    # Sort by USD value descending
    balances.sort(key=lambda x: x["usd_value"], reverse=True)

    return {
        "balances":        balances,
        "total_usd":       round(total_usd, 2),
        "stablecoins_usd": round(stablecoins_usd, 2),
        "fetched_at":      _now(),
    }


def get_open_orders() -> list:
    """Returns all active buy/sell orders with details."""
    raw = _safe_private("OpenOrders")
    orders = raw.get("open", {}) if raw else {}
    result = []

    for txid, o in orders.items():
        descr  = o.get("descr", {})
        age_h  = round((time.time() - o.get("opentm", time.time())) / 3600, 1)
        result.append({
            "order_id":      txid,
            "pair":          descr.get("pair", ""),
            "type":          descr.get("type", ""),       # buy / sell
            "order_type":    descr.get("ordertype", ""),  # limit / market
            "price":         float(descr.get("price", 0) or 0),
            "volume":        float(o.get("vol", 0)),
            "volume_filled": float(o.get("vol_exec", 0)),
            "status":        o.get("status", "open"),
            "opened_at":     _ts(o.get("opentm")),
            "age_hours":     age_h,
        })

    result.sort(key=lambda x: x["age_hours"])
    return result


def get_closed_orders(limit: int = 10) -> list:
    """Returns last N closed orders with timestamps."""
    raw = _safe_private("ClosedOrders", {"trades": True, "ofs": 0})
    orders = raw.get("closed", {}) if raw else {}
    result = []

    for txid, o in orders.items():
        descr = o.get("descr", {})
        if o.get("status") not in ("closed", "canceled"):
            continue
        result.append({
            "order_id":       txid,
            "pair":           descr.get("pair", ""),
            "type":           descr.get("type", ""),
            "order_type":     descr.get("ordertype", ""),
            "price_executed": float(o.get("price", 0) or 0),
            "volume":         float(o.get("vol", 0)),
            "volume_filled":  float(o.get("vol_exec", 0)),
            "cost_usd":       float(o.get("cost", 0) or 0),
            "fee_usd":        float(o.get("fee", 0) or 0),
            "status":         o.get("status", ""),
            "closed_at":      _ts(o.get("closetm")),
        })

    result.sort(key=lambda x: x["closed_at"], reverse=True)
    return result[:limit]


def get_ticker_prices(pairs: list) -> dict:
    """Get current bid/ask/last/24h data for trading pairs from Kraken public API."""
    if not pairs:
        return {}
    raw = _safe_public("Ticker", {"pair": ",".join(pairs)})
    result = {}

    for kraken_pair, data in raw.items():
        try:
            result[kraken_pair] = {
                "bid":       float(data["b"][0]),
                "ask":       float(data["a"][0]),
                "last":      float(data["c"][0]),
                "high_24h":  float(data["h"][1]),
                "low_24h":   float(data["l"][1]),
                "volume_24h": float(data["v"][1]),
                "vwap_24h":  float(data["p"][1]),
                "trades_24h": int(data["t"][1]),
            }
        except (KeyError, IndexError, ValueError) as e:
            print(f"[Ticker] Parse error on {kraken_pair}: {e}")

    return result


def get_portfolio_summary(use_cache: bool = True) -> dict:
    """
    Combined overview: balances + open orders + recent trades + ticker prices.
    Writes kraken_portfolio.json and sends Telegram push.
    Returns the full portfolio dict.
    """
    # Check cache first
    if use_cache:
        cached = load_cache()
        if cached:
            print(f"[Cache] Hit — data from {cached.get('fetched_at', '?')} (< 5min old)")
            return cached

    # Fetch prices once, share across balance calls
    print("[2/4] Fetching CoinGecko USD prices...  ", end="", flush=True)
    all_coin_ids = list(KRAKEN_ASSET_MAP.values())
    prices = _fetch_coingecko_prices(all_coin_ids)
    print(f"✓ ({len(prices)} coins)")

    print("[3/4] Fetching Kraken balances...       ", end="", flush=True)
    balance_data = get_account_balance(prices=prices)
    n_assets = len([b for b in balance_data["balances"] if not b["is_stablecoin"]])
    print(f"✓ ({n_assets} assets, total ${balance_data['total_usd']:,.2f})")

    print("[4/4] Fetching orders...                ", end="", flush=True)
    open_orders   = get_open_orders()
    closed_orders = get_closed_orders(limit=10)
    print(f"✓ ({len(open_orders)} open, {len(closed_orders)} recent closed)")

    # Ticker prices for all held pairs
    ticker_pairs = _build_ticker_pairs(balance_data["balances"])
    ticker_data  = get_ticker_prices(ticker_pairs) if ticker_pairs else {}

    portfolio = {
        "generated_at":  _now(),
        "exchange":       "kraken",
        "cache_hit":      False,
        "portfolio": {
            "total_usd":       balance_data["total_usd"],
            "stablecoins_usd": balance_data["stablecoins_usd"],
            "balances":        balance_data["balances"],
            "open_orders":     open_orders,
            "recent_trades":   closed_orders,
            "prices":          ticker_data,
        },
    }

    # Write JSON output
    OUTPUT_FILE.write_text(json.dumps(portfolio, indent=2), encoding="utf-8")
    print(f"\n[Output] Saved → {OUTPUT_FILE}")

    # Cache for subsequent calls
    save_cache(portfolio["portfolio"])

    # Send Telegram push (compact summary)
    _send_telegram_push(portfolio)

    # AI analysis — urgency score + smart alert if significant
    # Import inline to keep krakenex-only installs working without anthropic
    try:
        from ai_analyst import analyze_and_alert
        analyze_and_alert(portfolio, force=False, dry_run=False)
    except ImportError:
        pass  # anthropic not installed — skip AI analysis
    except Exception as e:
        print(f"[AI Analyst] Error: {e} — continuing without analysis")

    return portfolio["portfolio"]


# ── Telegram ───────────────────────────────────────────────────────────────────
ALERT_STATE_FILE = HERE / ".alert-state.json"
BIG_MOVE_THRESHOLD = 5.0   # % 24h change to trigger alert
ALERT_COOLDOWN_H   = 4     # hours before re-alerting same asset


def _load_alert_state() -> dict:
    if ALERT_STATE_FILE.exists():
        try:
            return json.loads(ALERT_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_alert_state(state: dict):
    try:
        ALERT_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def _fmt_price(price: float) -> str:
    if price >= 10000: return f"${price:,.0f}"
    if price >= 100:   return f"${price:,.2f}"
    if price >= 1:     return f"${price:,.3f}"
    if price >= 0.01:  return f"${price:.4f}"
    return f"${price:.6f}"


def _send_telegram_push(portfolio: dict):
    """
    Smart push — only fires on two triggers:
      1. BIG MOVE: any held asset moves >5% in 24h (max 1 alert per asset per 4h)
      2. SCHEDULED: 9AM AST (13:00 UTC) or 3PM AST (19:00 UTC) windows — handled
         by market-report.py. This function handles ALERT mode only.
    Routine 30-min syncs are SILENT (data saved to JSON, no Telegram).
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Not configured — skipping")
        return

    p        = portfolio["portfolio"]
    balances = [b for b in p["balances"] if not b.get("is_stablecoin")]
    now_utc  = datetime.now(timezone.utc)
    state    = _load_alert_state()

    # ── Find big movers not recently alerted ──────────────────────────────────
    big_movers = []
    for b in balances:
        ch24 = b.get("change_24h_pct")
        if ch24 is None or abs(ch24) < BIG_MOVE_THRESHOLD:
            continue
        sym = b.get("symbol", b["asset"])
        key = f"big_move_{sym}"
        last = state.get(key, "")
        if last:
            try:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if (now_utc - last_dt).total_seconds() < ALERT_COOLDOWN_H * 3600:
                    continue  # already alerted recently
            except Exception:
                pass
        big_movers.append(b)

    if not big_movers:
        print("[Telegram] No big moves detected — silent sync")
        return

    # ── Update alert state ───────────────────────────────────────────────────
    ts = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    for b in big_movers:
        sym = b.get("symbol", b["asset"])
        state[f"big_move_{sym}"] = ts
    _save_alert_state(state)

    # ── Build professional ALERT card ────────────────────────────────────────
    time_ast = (now_utc.hour - 4) % 24
    ampm     = "AM" if time_ast < 12 else "PM"
    hour12   = time_ast % 12 or 12
    time_s   = f"{hour12}:{now_utc.strftime('%M')} {ampm} AST"

    SEP_BOLD  = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    SEP_LIGHT = "─────────────────────────────"

    lines = [
        SEP_BOLD,
        f"⚡ <b>PRICE ALERT</b>  ·  {time_s}",
        SEP_BOLD,
        "",
    ]

    for b in big_movers:
        sym   = b.get("symbol", b["asset"])
        price = b.get("current_price") or b["usd_value"] / b["qty"] if b["qty"] > 0 else 0
        ch24  = b.get("change_24h_pct", 0)
        pnl   = b.get("pnl_pct")
        arrow = "▲" if ch24 >= 0 else "▼"
        dot   = "🟢" if ch24 >= 0 else "🔴"

        pnl_s = ""
        if pnl is not None:
            pnl_dot = "🟢" if pnl >= 0 else "🔴"
            pnl_s   = f"  {pnl_dot} {'+' if pnl >= 0 else ''}{pnl:.1f}% vs entry"

        lines.append(
            f"<b>{sym}</b>  {_fmt_price(price)}  {dot} {arrow}{abs(ch24):.1f}% 24h{pnl_s}"
        )

    lines += ["", SEP_LIGHT, ""]

    # Portfolio snapshot
    total = p["total_usd"]
    lines.append(f"💼 <b>PORTFOLIO</b>  ·  <b>${total:,.0f}</b> total")
    lines.append("")
    for b in balances[:6]:
        sym   = b.get("symbol", b["asset"])
        val   = b["usd_value"]
        ch24  = b.get("change_24h_pct")
        pnl   = b.get("pnl_pct")

        pnl_dot = "🟢" if (pnl or 0) >= 0 else "🔴"
        pnl_s   = f"{pnl_dot} {'+' if (pnl or 0) >= 0 else ''}{pnl:.0f}%" if pnl is not None else "⚪"

        if ch24 is not None:
            ch_s = f"{'▲' if ch24 >= 0 else '▼'}{abs(ch24):.1f}%"
            bang = "  ⚡" if abs(ch24) >= BIG_MOVE_THRESHOLD else ""
        else:
            ch_s, bang = "", ""

        lines.append(f"  <b>{sym:<6}</b>  ${val:>6,.0f}  {pnl_s:<10}  {ch_s}{bang}")

    if p.get("stablecoins_usd", 0) > 0:
        lines.append(f"  💵 Stable  ${p['stablecoins_usd']:,.0f}")

    lines += [
        "",
        SEP_BOLD,
        "📌 <b>Free signals</b> → @BlockSyndicateFree",
        "💎 <b>VIP setups</b>  → @BlockSyndicateVip",
    ]

    msg = "\n".join(lines)
    if len(msg) > 4000:
        msg = msg[:3990] + "\n..."

    try:
        payload = json.dumps({
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       msg,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        movers_s = ", ".join(b.get("symbol", b["asset"]) for b in big_movers)
        print(f"[Telegram] ✓ Alert sent — big movers: {movers_s}")
    except Exception as e:
        print(f"[Telegram] Failed: {e}")


# ── Helpers ────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts(unix: float | None) -> str:
    if not unix:
        return ""
    return datetime.fromtimestamp(float(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_ticker_pairs(balances: list) -> list:
    """Build Kraken ticker pair codes from held assets."""
    pairs = []
    asset_to_pair = {
        "XXBT": "XBTUSD", "XBT": "XBTUSD",
        "XETH": "ETHUSD", "ETH": "ETHUSD",
        "SOL":  "SOLUSD",
        "BCH":  "BCHUSD",
        "OPN":  "OPNUSD",
        "EIGEN": "EIGENUSD",
        "PENGU": "PENGUUSD",
        "BABY": "BABYUSD",
    }
    seen = set()
    for b in balances:
        if b.get("is_stablecoin"):
            continue
        pair = asset_to_pair.get(b["asset"])
        if pair and pair not in seen:
            pairs.append(pair)
            seen.add(pair)
    return pairs


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{SEP}")
    print(f"  Kraken Portfolio Monitor v1")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{SEP}")
    print(f"[1/4] Loading credentials from .env.local...  ✓")

    summary = get_portfolio_summary(use_cache=False)

    # Print summary table
    print(f"\n{SEP}")
    print(f"  PORTFOLIO SUMMARY — Kraken")
    print(f"{SEP}")
    print(f"  Total Value:  ${summary['total_usd']:>10,.2f}")
    if summary["stablecoins_usd"] > 0:
        print(f"  Stablecoins:  ${summary['stablecoins_usd']:>10,.2f}")
        print(f"  Net Crypto:   ${summary['total_usd'] - summary['stablecoins_usd']:>10,.2f}")
    print()

    crypto_balances = [b for b in summary["balances"] if not b.get("is_stablecoin")]
    for b in crypto_balances:
        sym   = b.get("symbol", b["asset"])
        qty   = b["qty"]
        val   = b["usd_value"]
        pnl   = b.get("pnl_pct")
        pnl_s = f"  P&L: {'+' if pnl >= 0 else ''}{pnl:.1f}%" if pnl is not None else ""
        print(f"  {sym:<8} {qty:<16.8f}  ${val:>10,.2f}{pnl_s}")

    print()
    open_n = len(summary["open_orders"])
    print(f"  Open Orders:  {open_n}")
    if open_n:
        for o in summary["open_orders"]:
            print(f"    {o['type'].upper()} {o['pair']} @ ${o['price']:,.4f}  (age: {o['age_hours']:.1f}h)")

    print(f"\n  Output: {OUTPUT_FILE.name}")
    print(SEP)


if __name__ == "__main__":
    main()
