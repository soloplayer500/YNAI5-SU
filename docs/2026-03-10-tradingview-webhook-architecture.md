# TradingView Webhook Architecture — YNAI5-SU
Date: 2026-03-10
Status: PLANNED (not built yet)
Priority: Medium — build after Kraken skill is tested

---

## What TradingView Is (and Isn't)

TradingView is a **charting + alerting platform** — it does NOT have a REST API for reading price data.
It DOES have outbound webhook alerts that fire when Pine Script conditions are met.

### What TradingView can do for YNAI5:
- Send price alerts when RSI, EMA crosses, support/resistance levels are hit
- Fire webhook to your server → trigger Kraken trade or Telegram notification
- Custom Pine Script strategy → backtest → deploy as live alert

### What it cannot do:
- No REST API for Claude to call
- No way to "read" TradingView charts from Python
- All integration is one-way: TradingView pushes → you receive

---

## Architecture Overview

```
TradingView Alert (Pine Script condition)
    │
    ▼ POST webhook
[Your webhook receiver server]  ← Flask/Python on local machine or VPS
    │
    ├── Log to file / YNAI5 workspace
    ├── Send Telegram alert (via bot)
    └── Optional: trigger Kraken trade via kraken.py skill
```

---

## What You Need to Build This

### 1. TradingView Plan
- **Free tier:** NO webhooks — only email/SMS alerts
- **Pro plan:** $14.95/month — unlocks webhook alerts
- **Pro+ / Premium:** Higher alert limits
- **Decision:** Buy Pro if you want to automate. Free = manual only.

### 2. Webhook Receiver (Python Flask)
A simple Python script that listens for POST requests from TradingView.

```python
# webhook-receiver.py (MVP — build when ready)
from flask import Flask, request, jsonify
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

ALERTS_FILE = Path("projects/crypto-monitoring/tradingview-alerts.log")

@app.route("/webhook", methods=["POST"])
def receive_alert():
    data = request.get_json(silent=True) or request.data.decode()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {json.dumps(data)}\n"
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.open("a").write(entry)
    print(f"Alert received: {entry.strip()}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 3. Public URL (TradingView must reach your server)
TradingView webhooks POST to a **public HTTPS URL** — your laptop's localhost won't work directly.

Options:
| Option | Cost | Notes |
|--------|------|-------|
| **ngrok** (free tier) | Free | Temporary public URL for local server. URL changes on restart. OK for testing. |
| **ngrok static domain** | ~$8/mo | Permanent URL on ngrok free plan (1 static domain now free) |
| **VPS (cheapest)** | ~$4–6/mo | Hetzner or Vultr cloud server, permanent IP, full control |
| **Cloudflare Tunnel** | Free | Permanent tunnel from local machine → public URL. Best free option. |

**Recommendation:** Cloudflare Tunnel (free) → runs local Python server → permanent public URL.

### 4. TradingView Alert Setup (Pine Script)
Once webhook receiver is live, in TradingView:

```
Alerts → Create Alert → Condition: [your Pine Script condition]
Notifications tab → Webhook URL: https://your-domain.com/webhook
Message: {"ticker": "{{ticker}}", "price": {{close}}, "signal": "BUY"}
```

TradingView sends the JSON payload to your URL when the condition fires.

---

## Full Build Order (when ready)

1. **Decide**: Buy TradingView Pro ($14.95/mo) → proceed. Otherwise stop.
2. **Set up Cloudflare Tunnel** on your laptop → get permanent public URL
3. **Build `webhook-receiver.py`** (flask, 30 lines) → logs alerts to file
4. **Test** with TradingView → send test webhook → confirm receipt
5. **Extend**: add Telegram bot notification when alert fires
6. **Extend**: connect to Kraken skill for auto-trade execution (optional, advanced)

---

## Telegram Bot Integration (for alerts without TradingView)

Even without TradingView Pro, you can get Telegram alerts from price-alert.py:
- Create Telegram bot via @BotFather (free)
- Get bot token + your chat ID
- Add `send_telegram(message)` function to price-alert.py
- Run price-alert.py on schedule → fires Telegram when threshold crossed

This gives you mobile alerts with NO monthly cost and NO TradingView needed.
Build this FIRST as it's the easier path.

---

## Verdict / Recommended Path

| Priority | Action |
|----------|--------|
| **Now** | Use price-alert.py manually (already built) |
| **Next** | Add Telegram bot to price-alert.py — free, no server needed |
| **Later** | Evaluate TradingView Pro when you want Pine Script chart alerts |
| **Advanced** | Full webhook pipeline when you're ready to semi-automate trades |

---

## Sources
- TradingView webhook docs: https://www.tradingview.com/support/solutions/43000529348
- TradingView plan comparison: https://www.tradingview.com/pricing
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
