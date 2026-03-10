---
name: kraken
description: Kraken exchange API — check portfolio balance, live prices, trade history, open orders
allowed-tools: Bash, Read
---

# /kraken Skill

Query your Kraken exchange account and market data.

## Setup Required
Add to `.env.local` (open in Notepad — do NOT paste keys in chat):
```
KRAKEN_API_KEY=your_public_key_here
KRAKEN_API_SECRET=your_private_key_here
```
Get keys at: https://www.kraken.com/u/security/api

**API Key permissions needed:**
- Query Funds (for balance)
- Query Open Orders & Trades (for trade history)
- Do NOT enable "Create & Modify Orders" until ready for auto-trading

## Commands

```bash
# Check portfolio balance (private API)
python .claude/skills/kraken/kraken.py balance

# Live prices — default BTC ETH SOL
python .claude/skills/kraken/kraken.py price

# Live prices — custom pairs
python .claude/skills/kraken/kraken.py price XBTUSD ETHUSD OPNUSD

# Last 10 trades
python .claude/skills/kraken/kraken.py trades

# Last N trades
python .claude/skills/kraken/kraken.py trades 25

# Open orders
python .claude/skills/kraken/kraken.py orders
```

## Kraken Pair Format
- BTC = XBTUSD or XXBTZUSD
- ETH = ETHUSD or XETHZUSD
- SOL = SOLUSD
- OPN = OPNUSD (if listed)

## What This Unlocks
- Real portfolio value from Kraken (not estimates)
- Actual trade execution prices vs. CoinGecko market prices
- Trade history for journal/P&L analysis
- Future: automated order placement (when ready)

## Security
- Keys live in .env.local only — gitignored, never committed
- Private key is never passed through chat
- Skill uses stdlib only — no pip installs
