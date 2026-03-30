---
name: niche-finder
description: "BRAINAI5 V3 — Deep autonomous niche research for YouTube/TikTok/Instagram. Triggers cloud GitHub Actions pipeline: 5-layer Brave research → Claude synthesis → Telegram inline gate (YES/NO/PIVOT) → Google Sheets tracking → HTML dashboard. Use when asked to 'find a niche', 'niche research', 'what niche should I pick', or '/niche-finder'."
argument-hint: "[seed keyword, e.g. 'betrayal karma narratives' or 'AI productivity tools']"
---

# BRAINAI5 V3 — Niche Research
Query: $ARGUMENTS

## Architecture
This skill runs cloud-first via GitHub Actions:
- **Phase 1** (`niche-research.yml`): Brave Search × 5 layers → Claude Haiku synthesis → Telegram inline keyboard gate
- **Phase 2** (`niche-approve.yml`): Deep dive → Google Sheets (5 tabs) → HTML dashboard → Telegram report

## Step 1 — Trigger GitHub Actions (Cloud)

Run this to start the full cloud pipeline:

```bash
gh workflow run niche-research.yml \
  --repo soloplayer500/YNAI5-SU \
  -f niche_query="$ARGUMENTS"
```

If `gh` CLI is not available, go to:
**GitHub → Actions → "BRAINAI5 Niche Research" → Run workflow → Enter:** `$ARGUMENTS`

After triggering: **check Telegram** for the summary card with inline YES / NO / PIVOT buttons (arrives within ~3 minutes).

---

## Step 2 — Quick Local Preview (Terminal)

While the cloud job runs, provide a fast local research summary using available tools.

Run 3 web searches:
1. `"$ARGUMENTS" YouTube niche RPM CPM monetization 2025`
2. `top "$ARGUMENTS" YouTube channels subscribers growth 2025`
3. `"$ARGUMENTS" content gap blue ocean underserved niche`

Synthesize into a quick summary table:

| Metric | Value |
|--------|-------|
| Est. CPM Range | $X–$Y |
| Saturation | Blue / Orange / Red |
| Top Creator | Name + subs |
| Best Format | Format type |
| #1 Blue Ocean Gap | Description |

**Accuracy rules:**
- Mark estimates as "estimate" if not from search results
- Never fabricate subscriber counts or revenue figures
- If data is unavailable for a metric, write "unknown"

---

## Step 3 — Gate Response

After the user sees the Telegram card:
- **YES tap** → Phase 2 auto-runs (Google Sheets + HTML dashboard committed to repo)
- **NO tap** → Research discarded
- **PIVOT tap** → Re-run with new query: re-trigger with new `niche_query`
- **TIMEOUT (10 min)** → Manually trigger Phase 2 when ready:
  ```bash
  gh workflow run niche-approve.yml \
    --repo soloplayer500/YNAI5-SU \
    -f niche_slug="[slug-from-phase-1]"
  ```

---

## Step 4 — Results Location

After Phase 2 completes:
- **JSON report**: `projects/niche-research/output/reports/YYYY-MM-DD-[slug].json`
- **HTML dashboard**: `projects/niche-research/output/dashboards/YYYY-MM-DD-[slug].html`
- **Google Sheets**: 5 tabs auto-populated (Niche_Tracker, Creator_Tracker, Format_Performance, Opportunity_Log, Research_Journal)
- **Telegram**: Full deep dive card sent to personal chat

---

## Fallback (No GitHub CLI + No Cloud)

If GitHub Actions is unavailable, do full local research:

1. Run 5 Brave searches (audience, monetization, competitors, formats, gaps)
2. Synthesize into the JSON schema below
3. Save to `projects/niche-research/output/reports/YYYY-MM-DD-[slug].json`
4. Run: `python projects/niche-research/dashboard_gen.py [report-path]`
5. Open the generated HTML dashboard

**JSON schema for local save:**
```json
{
  "niche": "$ARGUMENTS",
  "category": "Tech/AI | Finance | Lifestyle | Gaming | Education | Other",
  "query": "$ARGUMENTS",
  "date": "YYYY-MM-DD",
  "slug": "slug-form",
  "stats": {
    "growth_rate": 14,
    "saturation": "Blue",
    "cpm_low": 8,
    "cpm_high": 14,
    "audience_m": 22,
    "entry_barrier": "Low"
  },
  "creators": [{"name":"...","subs":500000,"growth_rate_12mo":"45%","est_monthly_rev":"3500","platform":"YouTube","format_innovation":"..."}],
  "formats":  [{"name":"...","platform":"YouTube","avg_views":120000,"ctr_pct":8.5,"retention_pct":52,"shares_est":800,"cpm":12.5,"why":"..."}],
  "blue_ocean":[{"name":"...","why":"...","audience_m":8,"entry_barrier":"Low","effort_hours":40,"rpm_est":"10-15"}],
  "summary": "2-3 sentence opportunity summary",
  "notes": ""
}
```
