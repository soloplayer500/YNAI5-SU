# GitHub Actions Setup — YNAI5 Market Reports
_Date: 2026-03-11_

Moves the 3x/day market report from Windows Task Scheduler → GitHub's cloud runners.
Reports fire at 8AM, 6PM, 9PM AST even when the laptop is off.

---

## Cost
$0. GitHub free tier = 2,000 min/month.
Each run takes ~2 min × 3 runs/day × 30 days = 180 min/month. Well within free limits.

---

## Step 1 — Push Repo to GitHub

Open a terminal in the YNAI5-SU folder and run:

```bash
# One-time: create private repo on GitHub first (github.com → New repository → Private → no README)
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/YNAI5-SU.git
git branch -M main
git add .
git commit -m "Add GitHub Actions market report workflow"
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

Note: `.env.local` must be in `.gitignore` (never push API keys to GitHub).

Verify `.gitignore` contains:
```
.env.local
*.env
```

---

## Step 2 — Add GitHub Secrets

Go to: `github.com/YOUR_USERNAME/YNAI5-SU` → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each secret exactly as named below (names are case-sensitive):

| Secret Name | Where to Get It |
|-------------|-----------------|
| `TELEGRAM_BOT_TOKEN` | Your `.env.local` file |
| `TELEGRAM_CHAT_ID` | Your `.env.local` file (your personal chat ID: 8569520396) |
| `COINGECKO_API_KEY` | CoinGecko API dashboard |
| `KRAKEN_API_KEY` | Kraken account → Security → API |
| `KRAKEN_API_SECRET` | Kraken account → Security → API |
| `BRAVE_SEARCH_API_KEY` | Brave Search API dashboard |
| `GEMINI_API_KEY` | Google AI Studio (aistudio.google.com) |

Add them one at a time. Each secret is encrypted and never shown again after saving.

---

## Step 3 — Verify It's Working

1. Go to: `github.com/YOUR_USERNAME/YNAI5-SU` → **Actions** tab
2. You should see "YNAI5 Market Reports" workflow listed
3. To test immediately without waiting for schedule: click the workflow → **Run workflow** → **Run workflow** (manual trigger)
4. Watch the run — green checkmark = success, report sent to Telegram
5. If red X: click the failed job → expand the failing step to read the error log

---

## Step 4 — Disable Windows Task Scheduler

The laptop-based Task Scheduler tasks are no longer needed once GitHub Actions is confirmed working.

1. Press `Win + R` → type `taskschd.msc` → Enter
2. In Task Scheduler Library, find and right-click each of these tasks:
   - `YNAI5-Report-Morning`
   - `YNAI5-Report-Evening`
   - `YNAI5-Report-Night`
3. Click **Disable** on each (don't delete — keep as backup)

The monitor-loop.py (15-min heartbeat) is separate — that still needs to run locally or be replaced by a different cloud solution (not handled by this workflow).

---

## How the Workflow Works

File: `.github/workflows/market-report.yml`

- **Trigger:** 3 cron schedules (12:00, 22:00, 01:00 UTC) + manual dispatch
- **Runner:** GitHub ubuntu-latest (free, ephemeral VM)
- **Steps:**
  1. Checkout the repo
  2. Set up Python 3.11
  3. Install `requests` (safety net — script uses stdlib only)
  4. Write secrets into `.env.local` so the script's `load_env()` function finds them
  5. Run `projects/crypto-monitoring/market-report.py`

The script sends its report directly to your Telegram bot. GitHub just provides the compute.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Workflow not appearing in Actions tab | Confirm `.github/workflows/market-report.yml` is pushed to `main` branch |
| Run succeeds but no Telegram message | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets are correct |
| API errors in logs | Check the relevant secret value — copy from `.env.local` not from memory |
| Schedule not firing | GitHub cron can delay up to 15 min during high load — normal |
| `revolut-config.json` error | That file needs to be committed (contains no secrets, just qty values) |

---

## Files Created
- `.github/workflows/market-report.yml` — the workflow definition
- `docs/2026-03-11-github-actions-setup.md` — this file
