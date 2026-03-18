---
name: crypto-screen
description: Goldman Sachs-style crypto screener — find top momentum coins, trending assets, and high-probability setups using live data from CoinGecko, Brave Search, and Kraken OHLC. Outputs ranked table with entry/target/stop.
argument-hint: "[risk: low|medium|high] [focus: momentum|undervalued|breakout|news] [budget: $amount]"
allowed-tools: Bash, Read, Write, WebSearch
---

# /crypto-screen Skill

Screen the crypto market for the best current opportunities. Returns a ranked table of top 5 coins with technical + fundamental reasoning.

## Inputs

- `risk`: low (BTC/ETH/SOL only) | medium (top 50 alts) | high (small caps, meme coins)
- `focus`: momentum (price/volume leaders) | undervalued (down + strong fundamentals) | breakout (near resistance) | news (catalyst-driven)
- `budget`: optional budget amount for position sizing

## Steps

### Step 1 — Market Overview

Search for current crypto market conditions:

```
WebSearch: "top crypto gainers today 2026" site:coingecko.com OR coinmarketcap.com
WebSearch: "crypto market sentiment today {current_date}"
WebSearch: "bitcoin dominance BTC.D chart today"
```

Note: BTC dominance trend (rising = risk-off, alt season ending; falling = alt season, opportunities elsewhere)

### Step 2 — Top Movers from CoinGecko

Use Brave Search to get current top gainers/losers:
```
WebSearch: "coingecko top gainers 24h today"
WebSearch: "highest volume crypto coins today"
```

### Step 3 — Technical Check for Candidates

For each candidate coin (max 5), search for:
```
WebSearch: "{COIN} price analysis RSI support resistance 2026"
WebSearch: "{COIN} news today 2026"
```

Look for:
- RSI < 35 = oversold opportunity
- RSI > 65 = momentum play (but watch for overbought)
- Price near key support = low-risk entry
- Volume spike > 2x average = breakout signal
- Recent news catalyst = news play

### Step 4 — Holdings Context

Read `projects/crypto-monitoring/kraken/kraken_portfolio.json` (if exists).
Flag if any top picks are already held — avoid doubling down into existing losing positions.

### Step 5 — Rank and Output

Produce a ranked table (best opportunity first):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YNAI5 Crypto Screener — {date}  |  Focus: {focus}  |  Risk: {risk}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RANK  COIN   PRICE      SIGNAL              ENTRY       TARGET      STOP    SCORE
  ────  ─────  ─────────  ──────────────────  ─────────   ─────────   ──────  ─────
  #1    BTC    $83,000    RSI 38 oversold     $82,000     $95,000     $77,000  8/10
  #2    SOL    $138       Volume spike +180%  $135        $160        $125     7/10
  #3    EIGEN  $0.38      Near key support    $0.36       $0.55       $0.30    6/10
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BEST PICK: BTC — oversold on HTF, BTC dominance holding, macro improving
  AVOID: Meme coins (high risk, no fundamentals right now)
  MARKET MOOD: Cautious — wait for BTC to reclaim $85K before aggressive alts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 6 — Save Output

Save to: `projects/crypto-monitoring/research/{YYYY-MM-DD}-crypto-screen.md`

Include full research notes, sources, and reasoning.

## Scoring Criteria (1-10)

| Factor | Weight |
|--------|--------|
| Technical setup (RSI, support/resistance) | 30% |
| Volume and momentum | 25% |
| Risk/reward ratio | 20% |
| Fundamental catalyst | 15% |
| Market structure alignment | 10% |

## Anti-Hallucination Rules

- ONLY cite prices from actual search results — never invent price data
- If a price can't be confirmed from search, say "price unconfirmed"
- Clearly label all entries as estimates, not guaranteed setups
- Include "Data may be delayed" disclaimer
