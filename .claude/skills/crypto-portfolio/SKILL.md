---
name: crypto-portfolio
description: Read Kraken portfolio snapshot, display balances/orders/P&L. Optionally log a prediction or view accuracy stats.
argument-hint: "[--predict TICKER DIRECTION TARGET HOURS CONFIDENCE 'REASONING'] [--stats] [--list]"
allowed-tools: Read, Bash
---

# /crypto-portfolio Skill

Display the current Kraken portfolio from cached JSON. Optionally log a new prediction or check accuracy stats.

## Arguments

- No args → display full portfolio summary
- `--predict BTC up 90000 72 0.7 "RSI oversold, holding 200MA"` → log a new prediction
- `--stats` → show prediction accuracy breakdown
- `--list` → list all predictions
- `--list pending` → list pending predictions only

## Steps

### Default (no args) — Show Portfolio

1. Read `projects/crypto-monitoring/kraken/kraken_portfolio.json`
2. If file doesn't exist: print "Portfolio data not available — run portfolio_monitor.py or wait for GitHub Actions sync (every 30min)"
3. Display:
   - Total USD value
   - Each balance: symbol, qty, USD value, P&L %, 24h change
   - Open orders (if any)
   - Most recent trade
   - Data age (generated_at timestamp)
4. If data is older than 35 minutes, show a warning: ⚠️ Data is Xmin old

### --predict TICKER DIRECTION TARGET HOURS CONFIDENCE "REASONING"

```bash
python projects/crypto-monitoring/kraken/prediction_tracker.py \
  --log {TICKER} {DIRECTION} {TARGET} {HOURS} {CONFIDENCE} "{REASONING}"
```

Show the returned prediction ID and confirmation.

### --stats

```bash
python projects/crypto-monitoring/kraken/prediction_tracker.py --stats
```

Display the accuracy breakdown from performance.json.

### --list [STATUS]

```bash
python projects/crypto-monitoring/kraken/prediction_tracker.py --list [STATUS]
```

Display all (or filtered) predictions.

## Output Format

Portfolio display example:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KRAKEN PORTFOLIO  |  $1,423.50 total
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BTC      0.000234      $19.63   [-7%]
  ETH      0.012400      $31.00   [-41%]  +1.2% 24h
  SOL      0.450000      $62.10   [-60%]
  ...

  Open orders: 0
  Last trade: BUY ETH @ $1,800  2026-03-15

  ⏱ Data: 2026-03-18 14:30 UTC (3min ago)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
