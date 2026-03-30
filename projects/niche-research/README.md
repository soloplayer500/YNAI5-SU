# Niche Research Agent — BRAINAI5 V3

## What It Is
Autonomous niche research system. Runs fully on GitHub Actions (no laptop needed).
Research → Telegram summary → inline YES/NO gate → deep dive → Sheets + HTML dashboard.

## Components
| File | Purpose |
|------|---------|
| niche_research.py | Phase 1: Brave research + Telegram summary + inline keyboard gate |
| niche_deepdive.py | Phase 2: Deep dive + Sheets update + HTML dashboard |
| dashboard_gen.py | HTML dashboard generator (Chart.js, stdlib only) |
| sheets_updater.py | Google Sheets 5-tab auto-updater (gspread) |

## Current Stage
🔨 Building

## Trigger Options
1. GitHub Actions UI → "BRAINAI5 Niche Research" → input: niche_query
2. Bridge bot (when laptop on): /niche [query]
3. Oracle Cloud (future): 24/7 Telegram command trigger

## Flow
```
GitHub Actions → niche_research.py
  → 5x Brave Search (audience, monetization, competitors, formats, gaps)
  → Claude Haiku synthesis → JSON report
  → Telegram inline keyboard (YES / NO / PIVOT)
  → [YES] → niche_deepdive.py → Sheets + HTML dashboard → Telegram confirmation
```

## Output
- `output/reports/YYYY-MM-DD-slug.json` — structured research data
- `output/dashboards/YYYY-MM-DD-slug.html` — Chart.js dashboard (committed to repo)
- Google Sheets — 5 auto-populated tabs
