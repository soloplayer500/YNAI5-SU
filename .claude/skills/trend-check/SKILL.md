---
name: trend-check
description: Check current price, news, and market sentiment for a crypto or stock ticker. Saves research to the crypto-monitoring project. Use when asked what's trending in AI/tech, "trend check", "what should I post today", or "/trend-check".
argument-hint: [optional platform focus, e.g. tiktok, youtube — defaults to TikTok]
---

Find today's top trending AI and tech topics for short-form content creation.
Platform focus: $ARGUMENTS (default: TikTok)

## Accuracy Rules
- Only report real news from search results — cite source + date for every topic
- Never invent stories or trends — if nothing strong is found, say so
- Virality scores are estimates based on engagement signals (share potential, controversy, novelty) — label them as estimates

## Steps

1. Use WebSearch with these queries (run all 3):
   - "AI news today [current date]"
   - "trending AI tools viral TikTok [current date]"
   - "ChatGPT Claude Gemini news this week"

2. From results, identify the top 5 topics with the strongest content potential

3. For each topic, score virality (1–10) based on:
   - Novelty (is this new/surprising?)
   - Controversy (does it spark debate?)
   - Relatability (does it affect everyday users?)
   - Shareability (would someone send this to a friend?)

4. For each topic, suggest a TikTok angle (the hook — what makes it funny, relatable, or surprising)

5. Return the ranked list in chat AND save to file

6. Save to `projects/social-media-automation/trends/YYYY-MM-DD-trends.md`

## Output Format (in chat)

```
## Trending AI Topics — [DATE]

| # | Topic | Virality | Angle |
|---|-------|---------|-------|
| 1 | [Topic] | X/10 | [Hook idea — 1 sentence] |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |
| 4 | ... | ... | ... |
| 5 | ... | ... | ... |

**Top Pick:** [Topic #1] — [why it's the strongest today]
**Next Step:** Run `/content-gen [topic]` on your chosen topic
```

## Saved File Format

```markdown
# Trend Check: [DATE]
Platform: TikTok/YouTube/Instagram

## Top 5 Topics

### 1. [Topic Name] — Virality: X/10
- **Source:** [URL] ([date])
- **What happened:** [1-2 sentences]
- **TikTok angle:** [Hook idea]
- **Why it works:** [Novelty / Controversy / Relatability / Shareability]

[repeat for all 5]

## Top Pick
[Topic name] — [reasoning]
```
