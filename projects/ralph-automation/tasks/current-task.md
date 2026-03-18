# Daily Crypto + Stocks Audit Task
_Runs 3x/day: 8AM / 2PM / 9PM AST via GitHub Actions_

---

## Task

You are YNAI5's autonomous market intelligence agent. Run a full crypto + stocks audit and save a structured report.

### Step 1 — Read Context
- Read `projects/crypto-monitoring/watchlist.md` for current holdings and watchlist
- Read `memory/MEMORY.md` for recent learnings and portfolio notes

### Step 2 — Fetch Crypto Prices (CoinGecko free API)
Use `run_bash` to fetch prices for: BTC, ETH, SOL, OPN, XRP, BNB, AVAX, ADA

```bash
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,open-network,ripple,binancecoin,avalanche-2,cardano&vs_currencies=usd&include_24hr_change=true" | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'{k}: ${v[\"usd\"]:,.2f} ({v.get(\"usd_24h_change\",0):.2f}%)') for k,v in data.items()]"
```

### Step 3 — Fetch Stock/Index Prices (Yahoo Finance free endpoint)
Use `run_bash` to fetch: SPY (S&P 500), QQQ (NASDAQ), NVDA, MSFT, META

```bash
for ticker in SPY QQQ NVDA MSFT META; do
  curl -s "https://query1.finance.yahoo.com/v8/finance/chart/$ticker?interval=1d&range=2d" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d['chart']['result'][0]; closes=r['indicators']['quote'][0]['close']; print(f'$ticker: \${closes[-1]:.2f} (prev: \${closes[-2]:.2f})')" 2>/dev/null || echo "$ticker: fetch failed"
done
```

### Step 4 — Get Crypto News Headlines
Use `run_bash` to fetch latest crypto news:

```bash
curl -s "https://cryptopanic.com/api/v1/posts/?auth_token=free&filter=hot&public=true" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for item in d.get('results', [])[:5]:
        print(f\"- {item['title']} [{item['source']['title']}]\")
except: print('News fetch failed')
" || echo "News fetch unavailable"
```

### Step 5 — Generate Report
Save a structured report to `projects/ralph-automation/sessions/YYYY-MM-DD-HHMM-market-audit.md`:

```markdown
# Market Audit — [timestamp]
## Crypto Prices
[prices with 24h change]
## Stock Prices
[stock prices]
## News Headlines
[top 5 headlines]
## OPN Watch (Shami's main hold)
[OPN price vs targets: buy $0.15-0.20, sell $0.45 / $0.60]
## Signal Summary
[1-3 line assessment: anything notable, any price targets hit?]
```

### Step 6 — Also update trade journal
Append a one-line entry to `projects/crypto-monitoring/trade-journal.md`:
```
| [date] | [BTC price] | [notable market event or "quiet"] | [any OPN update] |
```

---
_Last updated: 2026-03-12_
_Schedule: 8AM / 2PM / 9PM AST daily_
