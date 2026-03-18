# Kraken Portfolio Monitor

## What It Is
A dedicated read-only Kraken exchange portfolio tracker. Pulls live balances, open/closed orders, and ticker prices. Outputs structured JSON for cloud sync and mobile access via Telegram.

## Problem It Solves
Gives Claude (and Shami on mobile) persistent, cloud-synced access to Kraken portfolio data without depending on the laptop. Foundation for the prediction feedback loop — Claude tracks calls and improves accuracy over time.

## Components

| File | Purpose |
|------|---------|
| `portfolio_monitor.py` | Main script — pulls all Kraken data, writes kraken_portfolio.json, sends Telegram push |
| `prediction_tracker.py` | Logs Claude's market predictions, scores outcomes, tracks accuracy in performance.json |
| `kraken_portfolio.json` | Live portfolio snapshot (auto-committed by GitHub Actions every 30min) |
| `predictions.json` | All logged predictions with outcome status |
| `performance.json` | Accuracy stats by ticker, confidence, timeframe |

## Current Stage
🔨 Building — Phase 1 (portfolio monitor) active. Phase 2 (prediction tracker) next.

## Usage

```bash
# Run portfolio snapshot (requires KRAKEN_PORTFOLIO_API_KEY in .env.local)
python portfolio_monitor.py

# Log a prediction
python prediction_tracker.py --log BTC up 90000 72 0.7 "RSI oversold, holding 200MA"

# Score all due predictions
python prediction_tracker.py --score

# View accuracy stats
python prediction_tracker.py --stats
```

## Required Env Vars
```
KRAKEN_PORTFOLIO_API_KEY=...      # Read-only Kraken API key (separate from market-report.py key)
KRAKEN_PORTFOLIO_API_SECRET=...   # Read-only Kraken API secret
TELEGRAM_BOT_TOKEN=...            # Already in .env.local
TELEGRAM_CHAT_ID=...              # Already in .env.local
COINGECKO_API_KEY=...             # Already in .env.local
```

## Kraken API Permissions Required (read-only key)
- Query Funds (Balance)
- Query Open Orders and Trades
- Query Closed Orders and Trades
- NO trading / withdrawal permissions

## Future Phases
- Phase 2: CEX.IO monitor (`../cex/`)
- Phase 3: Phantom wallet tracker (`../phantom/`)
- Phase 4: Multi-exchange aggregator
