#!/usr/bin/env python
"""
Kraken API Skill — /kraken
Checks portfolio balance, live prices, trade history from Kraken exchange.
Reads KRAKEN_API_KEY and KRAKEN_API_SECRET from .env.local
"""

import sys
import os
import time
import hashlib
import hmac
import base64
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ── Load .env.local ─────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.local")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

# ── Kraken Auth (HMAC-SHA512) ─────────────────────────────────────────────
BASE_URL = "https://api.kraken.com"

def kraken_sign(url_path, data, secret):
    post_data = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + post_data).encode()
    message = url_path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()

def kraken_private(endpoint, api_key, api_secret, extra=None):
    url_path = f"/0/private/{endpoint}"
    nonce = str(int(time.time() * 1000))
    data = {"nonce": nonce}
    if extra:
        data.update(extra)
    headers = {
        "API-Key": api_key,
        "API-Sign": kraken_sign(url_path, data, api_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE_URL + url_path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def kraken_public(endpoint, params=None):
    url = f"{BASE_URL}/0/public/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())

# ── Commands ──────────────────────────────────────────────────────────────
def cmd_balance(api_key, api_secret):
    print("\n[KRAKEN] Account Balance")
    print("-" * 40)
    result = kraken_private("Balance", api_key, api_secret)
    if result.get("error"):
        print("[ERROR]", result["error"])
        return
    balances = result["result"]
    total_shown = 0
    for asset, amount in sorted(balances.items()):
        val = float(amount)
        if val > 0.0001:
            print(f"  {asset:<10} {val:.6f}")
            total_shown += 1
    if total_shown == 0:
        print("  No balances found.")
    print(f"\n  Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def cmd_price(pairs):
    print("\n[KRAKEN] Live Prices")
    print("-" * 40)
    pair_str = ",".join(pairs)
    result = kraken_public("Ticker", {"pair": pair_str})
    if result.get("error"):
        print("[ERROR]", result["error"])
        return
    for pair, data in result["result"].items():
        last = float(data["c"][0])
        high = float(data["h"][1])
        low  = float(data["l"][1])
        vol  = float(data["v"][1])
        print(f"  {pair:<12} Last: ${last:>12,.4f}  H: ${high:,.4f}  L: ${low:,.4f}  Vol: {vol:,.2f}")

def cmd_trades(api_key, api_secret, count=10):
    print(f"\n[KRAKEN] Last {count} Trades")
    print("-" * 40)
    result = kraken_private("TradesHistory", api_key, api_secret)
    if result.get("error"):
        print("[ERROR]", result["error"])
        return
    trades = result["result"].get("trades", {})
    sorted_trades = sorted(trades.items(), key=lambda x: x[1]["time"], reverse=True)[:count]
    for txid, t in sorted_trades:
        dt = datetime.fromtimestamp(t["time"]).strftime("%Y-%m-%d %H:%M")
        side = t["type"].upper()
        pair = t["pair"]
        vol  = float(t["vol"])
        price = float(t["price"])
        cost  = float(t["cost"])
        print(f"  {dt}  {side:<4} {pair:<12}  {vol:.6f} @ ${price:,.4f}  = ${cost:,.2f}")
    if not sorted_trades:
        print("  No trade history found.")

def cmd_open_orders(api_key, api_secret):
    print("\n[KRAKEN] Open Orders")
    print("-" * 40)
    result = kraken_private("OpenOrders", api_key, api_secret)
    if result.get("error"):
        print("[ERROR]", result["error"])
        return
    orders = result["result"].get("open", {})
    if not orders:
        print("  No open orders.")
        return
    for oid, o in orders.items():
        desc = o["descr"]
        print(f"  {oid[:8]}  {desc['order']}  Status: {o['status']}")

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    env = load_env()
    api_key    = env.get("KRAKEN_API_KEY", "")
    api_secret = env.get("KRAKEN_API_SECRET", "")

    args = sys.argv[1:]
    cmd  = args[0] if args else "balance"

    if cmd in ("balance", "bal", "b"):
        if not api_key or not api_secret:
            print("[ERROR] KRAKEN_API_KEY and KRAKEN_API_SECRET not found in .env.local")
            sys.exit(1)
        cmd_balance(api_key, api_secret)

    elif cmd in ("price", "prices", "p"):
        pairs = args[1:] if len(args) > 1 else ["XBTUSD", "ETHUSD", "SOLUSD"]
        cmd_price(pairs)

    elif cmd in ("trades", "history", "t"):
        if not api_key or not api_secret:
            print("[ERROR] KRAKEN_API_KEY and KRAKEN_API_SECRET not found in .env.local")
            sys.exit(1)
        count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
        cmd_trades(api_key, api_secret, count)

    elif cmd in ("orders", "open", "o"):
        if not api_key or not api_secret:
            print("[ERROR] KRAKEN_API_KEY and KRAKEN_API_SECRET not found in .env.local")
            sys.exit(1)
        cmd_open_orders(api_key, api_secret)

    else:
        print("Usage: python kraken.py [balance|price|trades|orders] [args]")
        print("  balance          — show all non-zero balances")
        print("  price [PAIRS]    — live prices (default: BTC ETH SOL)")
        print("  trades [N]       — last N trades (default: 10)")
        print("  orders           — open orders")

if __name__ == "__main__":
    main()
