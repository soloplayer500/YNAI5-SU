#!/usr/bin/env python3
"""
Price Alert Checker — YNAI5-SU Crypto Monitoring
Checks current prices vs alert thresholds. Uses CoinGecko free API (no key needed).
Run manually: python price-alert.py
Schedule: Windows Task Scheduler → run daily or on-demand

No external dependencies — stdlib only (urllib, json).
"""

import json
import urllib.request
from datetime import datetime

# ── Alert Config ────────────────────────────────────────────────────────────────
# Format: "coingecko_id": { "symbol": "TICKER", "alerts": [(price, label), ...] }
# alert label: "DOWN" = below threshold, "UP" = above threshold

WATCHLIST = {
    "opinion": {
        "symbol": "OPN",
        "alerts": [
            (0.18,  "DOWN - Accumulation zone reached"),
            (0.45,  "UP   - Recovery signal, re-evaluate"),
            (0.60,  "UP   - Near ATH resistance, consider exit"),
        ],
        "note": "Post-Binance listing. 80% supply unlocked. Watch March 2027 cliff."
    },
    "bitcoin": {
        "symbol": "BTC",
        "alerts": [
            (55000, "DOWN - Major support test"),
            (90000, "UP   - Back at avg buy zone"),
            (110000,"UP   - All-time high territory"),
        ],
        "note": "Kraken + Revolut holding. Avg buy $90,111."
    },
    "ethereum": {
        "symbol": "ETH",
        "alerts": [
            (1500,  "DOWN - Critical support"),
            (3000,  "UP   - Back at avg buy zone"),
            (4000,  "UP   - ATH territory"),
        ],
        "note": "Kraken holding. Avg buy $3,151."
    },
    "solana": {
        "symbol": "SOL",
        "alerts": [
            (60,    "DOWN - Deep support"),
            (120,   "UP   - Recovery level"),
            (200,   "UP   - Bull run territory"),
        ],
        "note": "Kraken + Revolut. Small positions."
    },
    "eigenlayer": {
        "symbol": "EIGEN",
        "alerts": [
            (0.10,  "DOWN - Near zero, review exit"),
            (0.40,  "UP   - Back at avg buy"),
            (1.00,  "UP   - Strong recovery signal"),
        ],
        "note": "Restaking protocol. Avg buy $0.30."
    },
}

# ── CoinGecko API ───────────────────────────────────────────────────────────────

def get_prices(coin_ids: list) -> dict:
    """Fetch current prices from CoinGecko free API. No key required."""
    ids_str = ",".join(coin_ids)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"

    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "YNAI5-PriceAlert/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] CoinGecko API failed: {e}")
        return {}


# ── Alert Logic ─────────────────────────────────────────────────────────────────

def check_alerts(symbol: str, current: float, alerts: list) -> list:
    """Return list of triggered alerts."""
    triggered = []
    for threshold, label in alerts:
        direction = label.split()[0]
        if direction == "DOWN" and current <= threshold:
            triggered.append((threshold, label))
        elif direction == "UP" and current >= threshold:
            triggered.append((threshold, label))
    return triggered


def format_change(change: float) -> str:
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}%"


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"  YNAI5 Price Alert Check — {now}")
    print(f"{'='*60}\n")

    coin_ids = list(WATCHLIST.keys())
    prices = get_prices(coin_ids)

    if not prices:
        print("[ERROR] Could not fetch prices. Check internet connection.")
        return

    alerts_fired = []

    for coin_id, config in WATCHLIST.items():
        symbol = config["symbol"]
        data = prices.get(coin_id, {})
        current = data.get("usd")
        change_24h = data.get("usd_24h_change", 0)

        if current is None:
            print(f"  {symbol:<8} [NO DATA]")
            continue

        # Check for triggered alerts
        triggered = check_alerts(symbol, current, config["alerts"])

        # Status display
        change_str = format_change(change_24h)
        status = "*** ALERT ***" if triggered else "OK"
        print(f"  {symbol:<8} ${current:<12.4f} 24h: {change_str:<10} [{status}]")

        if triggered:
            for threshold, label in triggered:
                print(f"           >> ${threshold} — {label}")
                alerts_fired.append((symbol, current, threshold, label))

        if config.get("note"):
            print(f"           Note: {config['note']}")
        print()

    # Summary
    print(f"{'='*60}")
    if alerts_fired:
        print(f"  ALERTS FIRED: {len(alerts_fired)}")
        for symbol, price, threshold, label in alerts_fired:
            print(f"  {symbol}: ${price:.4f} — {label}")
    else:
        print(f"  No alert thresholds crossed. All tickers within normal range.")
    print(f"{'='*60}\n")

    print("Tip: Run this script anytime for a quick check.")
    print("     To add new tickers, edit the WATCHLIST dict at the top of this file.")
    print("     Schedule: Windows Task Scheduler -> Action -> 'python price-alert.py'\n")


if __name__ == "__main__":
    main()
