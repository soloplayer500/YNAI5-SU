---
name: script-gen
description: Generate 3 A/B script variations for the same topic with different hooks and angles. Use before recording to pick the strongest version. Use when asked for "script variations", "A/B test scripts", "multiple versions", or "/script-gen".
argument-hint: [topic] [platform: tiktok|youtube|instagram — default: tiktok]
---

Generate 3 A/B script variations for: $ARGUMENTS

## Purpose
Before recording, you want 3 different angles on the same topic. Different hooks = different
audiences. Pick the one that feels most natural to deliver or strongest for today's algorithm.

## YNAI5 Brand Voice — APPLY TO ALL VARIANTS

**Identity:** YNAI = Young Nigga AI. Gen Z AI content — unfiltered, funny, reactive, authentic.
Every variant sounds like your smartest friend texting you about wild AI news. Not a press release.

**Vocabulary:** "bro what", "ngl", "no cap", "fr fr", "lowkey wild", "it's giving", "not even joking",
"they actually just—", "this is so them", "rent free", "ate and left no crumbs", "main character behavior",
"NPC behavior", "sigma move", "based", "[X] era", "[X] core", "the model dropped", "hallucinating again"

**Rules for ALL variants:**
- Short punchy bursts. One idea per line.
- All-caps ONE word per hook for punch
- Hot take is mandatory in every variant — different opinion angle per variant
- CTA = debate-starter or tag prompt. NEVER subscribe ask.
- NEVER: "In today's video", "Let's dive in", "As we know", "This is a game-changer" (unless sarcastic)

## Variation Strategy (all in YNAI5 voice)
- **Variation A — The Reaction:** Pure Gen Z chaos reaction. "Bro they actually just—"
- **Variation B — The Hot Take:** Spicy opinion angle. Designed to get comments and arguments.
- **Variation C — The Explainer:** "here's why this matters fr" — educational but punchy and YNAI5-toned.

## Steps

1. Parse topic and platform from $ARGUMENTS

2. For each variation (A, B, C), generate:
   - Hook (0–3s): Different opening angle for each
   - Body (3–30s): 3–4 sentences, consistent facts but different tone
   - CTA: Tailored to the variation's tone
   - One caption

3. Score each variation (1–10) on:
   - **Hook strength** — does it stop the scroll?
   - **Comment potential** — will people reply?
   - **Shareability** — will people send it?

4. Give a recommendation: which one to use and why

5. Save all 3 to `projects/social-media-automation/scripts/YYYY-MM-DD-[topic-slug]-variants.md`

## Output Format

```markdown
# Script Variants: [TOPIC]
Date: YYYY-MM-DD
Platform: [Platform]

---

## VARIANT A — The Reaction
**Score:** Hook: X/10 | Comments: X/10 | Share: X/10

**HOOK:** [Hook]
**BODY:**
[Line 1]
[Line 2]
[Line 3]
**CTA:** [CTA]
**Caption:** [Caption]

---

## VARIANT B — The Hot Take
**Score:** Hook: X/10 | Comments: X/10 | Share: X/10

**HOOK:** [Hook]
**BODY:**
[Line 1]
[Line 2]
[Line 3]
**CTA:** [CTA]
**Caption:** [Caption]

---

## VARIANT C — The Explainer
**Score:** Hook: X/10 | Comments: X/10 | Share: X/10

**HOOK:** [Hook]
**BODY:**
[Line 1]
[Line 2]
[Line 3]
**CTA:** [CTA]
**Caption:** [Caption]

---

## Recommendation
**Use Variant [X]** — [1-2 sentence reason]
```

After saving, tell the user the file path and recommended variant.
