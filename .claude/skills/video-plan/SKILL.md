---
name: video-plan
description: Read a generated script file and produce a full shot-by-shot video production plan — Pexels stock footage search terms, text overlays, timing guide, and YNAI5 brand notes. Use when asked to "plan the video", "video plan", "what footage do I need", or "/video-plan". Bridges the gap between script and CapCut assembly.
argument-hint: [path to script file, e.g. projects/social-media-automation/scripts/2026-03-16-apple-gemini.md]
---

Create a video production plan for: $ARGUMENTS

## Purpose
Turn a Claude-generated script into a shot-by-shot director's breakdown. Every line of the script
gets a visual, a text overlay, a timing window, and a stock footage search term. After this,
assembly in CapCut should take under 15 minutes.

## Steps

1. Read the script file at the path provided in $ARGUMENTS
   - If no path given, check `projects/social-media-automation/scripts/` for the most recent .md file
   - Extract: HOOK, BODY lines, CTA, duration, platform, topic

2. Break the script into individual shots:
   - HOOK = Shot 1 (always)
   - Each sentence in BODY = its own shot
   - CTA = final shot
   - Aim for 1–2 seconds per shot for TikTok Phase 1 (fast cuts = high retention)

3. For each shot, produce:
   - **Line:** Exact words spoken
   - **Visual:** What should be on screen (stock clip, text card, or character image)
   - **Text overlay:** Exact on-screen caption (short, punchy — max 6 words)
   - **Pexels search term:** 2–4 word search query to find matching stock footage
   - **Duration:** Seconds for this shot
   - **YNAI5 note:** Any brand element (logo flash, character reaction, color overlay)

4. Add a Brand Guide section:
   - Intro: YNAI5 logo flash (0.5s) at start
   - Voice: ElevenLabs VO plays throughout (generated separately via /voice-gen)
   - Color overlay: Dark purple/electric blue gradient (YNAI5 brand colors)
   - Outro: "YNAI5 World" text card (1s) at end
   - Font: Bold, white, centered — same every video

5. Add a Pexels Quick-Fetch section:
   - List all unique Pexels search terms in one block
   - User can copy-paste these into pexels.com or the Pexels API returns footage URLs

6. Save plan to `projects/social-media-automation/video-plans/YYYY-MM-DD-[slug]-plan.md`

7. Return full plan in chat

## Output Format

```markdown
# Video Plan: [TOPIC]
Script: [source file path]
Date: YYYY-MM-DD
Platform: TikTok
Total Duration: ~[X] seconds

---

## Shot Breakdown

| # | Line (spoken) | Visual | Text Overlay | Pexels Term | Duration | YNAI5 Note |
|---|--------------|--------|--------------|-------------|----------|------------|
| 0 | — | YNAI5 logo flash | — | — | 0.5s | Logo intro |
| 1 | [HOOK text] | [stock clip / text card] | [overlay text] | [search term] | [Xs] | [note] |
| 2 | [Body line 1] | ... | ... | ... | [Xs] | ... |
[continue for all lines]
| N | [CTA text] | Text card — black bg | [CTA text short] | — | 3s | Outro |
| N+1 | — | YNAI5 World text card | YNAI5 World | — | 1s | Brand outro |

---

## Pexels Quick-Fetch (copy-paste these)
- [search term 1]
- [search term 2]
- [search term 3]
[etc.]

---

## Brand Guide (apply to every video)
- **Intro:** YNAI5 logo flash 0.5s
- **Voice:** ElevenLabs VO (file: audio/[slug].mp3)
- **Color overlay:** Dark purple → electric blue gradient, 30% opacity
- **Font:** Bold white centered, stroke outline
- **Outro:** "YNAI5 World" text card 1s, fade to black

---

## CapCut Assembly Order
1. Import VO file (audio/[slug].mp3)
2. Import stock clips in shot order
3. Trim each clip to target duration
4. Add text overlays per shot table
5. Apply YNAI5 color overlay (add filter layer)
6. Add YNAI5 logo intro (0.5s) + outro (1s)
7. Export 9:16 vertical, 1080p, 30fps
8. Upload to TikTok at 7–9PM AST
```

After saving, tell the user: "Plan saved to video-plans/[filename]. Run `/voice-gen` to generate the VO, then open CapCut and follow the shot breakdown. Assembly should take ~15 minutes."
