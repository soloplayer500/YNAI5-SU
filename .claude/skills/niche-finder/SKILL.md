---
name: niche-finder
description: Deep niche research for YouTube/TikTok/Instagram content strategy. Returns ranked table of sub-niches with RPM, competition, automation score, and first-mover potential. Use when asked to "find a niche", "niche research", "what niche should I pick", or "/niche-finder".
argument-hint: [seed keyword or broad category, e.g. "AI tools" or "crypto education"]
---

Deep niche research for: $ARGUMENTS

## Research Goal
Find the 10 best content sub-niches within the seed topic. Rank them by revenue potential
and automation feasibility — not just view counts. The goal is monetizable, automatable content.

## Accuracy Rules
- Base RPM estimates on real advertiser data where available — otherwise mark as "estimate"
- Competition level must come from search results (YouTube search volume, TikTok saturation) — not assumptions
- Cite at least one source per sub-niche
- If data is unavailable for a metric, mark as "unknown" — never fabricate numbers

## Steps

1. Use WebSearch with 3 queries:
   - "[seed] YouTube niche RPM 2025 2026"
   - "[seed] TikTok creator fund earnings sub-niche"
   - "best [seed] content niche low competition high revenue"

2. Identify 10 distinct sub-niches within the seed topic

3. For each sub-niche, research and score:
   - **RPM estimate** ($X–$Y per 1000 views) — based on advertiser category
   - **Competition level** (Low / Medium / High) — based on search saturation
   - **Automation score** (1–10) — how much can AI handle? (10 = fully automatable)
   - **First-mover potential** (High / Medium / Low) — is this under-served?
   - **Monetization path** — how does money actually come in?

4. Rank by a composite score: (RPM × 0.4) + (Automation × 0.3) + (First-mover × 0.3)

5. Save to `projects/social-media-automation/niche-research/YYYY-MM-DD-[seed-slug].md`

6. Return ranked table + top 3 recommendations in chat

## Output Format (in chat)

```
## Niche Research: [SEED] — [DATE]

| Rank | Sub-Niche | RPM Est. | Competition | Automation | First-Mover | Score |
|------|-----------|----------|-------------|------------|-------------|-------|
| 1    | [name]    | $X–$Y    | Low/Med/High | X/10      | High/Med/Low | X.X  |
[... 10 rows total]

## Top 3 Picks

### #1 — [Sub-Niche Name]
- **Why:** [2 sentences — RPM + automation + gap in market]
- **Content format:** [what works here — shorts, long-form, tutorials, reactions]
- **Monetization:** [AdSense + sponsorships + affiliate / etc.]

### #2 — ...
### #3 — ...

**Recommendation:** [Which one to pursue and why, given YNAI5 constraints: 8GB RAM laptop, cloud-only video, Phase 1 = TikTok]
```

## Saved File Format
Full research notes per sub-niche with sources, reasoning, and action plan.
