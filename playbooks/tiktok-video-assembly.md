# Playbook: TikTok Video Assembly — YNAI5 World
_Repeatable SOP. Follow this every time. Target: under 15 minutes per video._

Last Updated: 2026-03-16
Version: 1.0 (Phase 1 — Stock Footage + ElevenLabs VO)

---

## Prerequisites (do once, reuse forever)
- [ ] CapCut Desktop installed (free)
- [ ] YNAI5 logo file saved: `assets/ynai-world/brand/logo.png`
- [ ] YNAI5 brand colors saved in CapCut as a preset: dark purple `#1a0a2e` + electric blue `#00d4ff`
- [ ] ElevenLabs voice selected and saved (same voice EVERY video for brand consistency)
- [ ] Pexels account created → free API key → added to `.env.local` as `PEXELS_API_KEY`

---

## Step 0 — Generate Your Assets (Claude does this)

Before touching CapCut, run these 3 commands in order:

```
1. /trend-check                              → pick today's top topic
2. /content-gen [topic] tiktok              → script saved to scripts/
3. /video-plan [path to script file]        → shot breakdown + Pexels terms saved to video-plans/
4. /voice-gen [paste HOOK + BODY + CTA text] → VO saved to audio/
```

When done, you have:
- ✅ Script file: `scripts/YYYY-MM-DD-[slug].md`
- ✅ Video plan: `video-plans/YYYY-MM-DD-[slug]-plan.md`
- ✅ VO audio: `audio/YYYY-MM-DD-[slug].mp3`
- ✅ Pexels search terms (in video plan)

---

## Step 1 — Download Stock Footage (3 min)

1. Open the video plan file: `video-plans/YYYY-MM-DD-[slug]-plan.md`
2. Copy the **Pexels Quick-Fetch** list of search terms
3. Go to [pexels.com/videos](https://pexels.com/videos)
4. Search each term → download the best 5–10 second clip (HD, no watermark)
5. Save all clips to a folder: `Desktop/[topic]-clips/`

**Pro tip:** Download 2 options per shot in case one doesn't fit timing.

---

## Step 2 — CapCut Setup (1 min)

1. Open CapCut Desktop → New Project → 9:16 vertical (1080 × 1920)
2. Set timeline to 30fps
3. Import all assets at once:
   - All stock clips from `Desktop/[topic]-clips/`
   - VO file from `audio/YYYY-MM-DD-[slug].mp3`
   - YNAI5 logo from `assets/ynai-world/brand/logo.png`

---

## Step 3 — Build the Timeline (6 min)

Follow the **Shot Breakdown table** in your video plan exactly.

### Timeline order:
```
[0] YNAI5 logo flash (0.5s)
[1] HOOK shot — strongest visual, first text overlay
[2] Body shot 1
[3] Body shot 2
[4] Body shot 3
[5] Body shot 4 (if applicable)
[6] CTA shot — text card on black or dark background
[7] YNAI5 World outro text card (1s)
```

### For each shot:
1. Drag stock clip to timeline → trim to target duration from video plan
2. Add **text overlay** — exact wording from video plan Shot Breakdown table
   - Font: Bold, white, centered
   - Add black stroke/shadow for readability
   - Size: Large enough to read on mobile
3. Layer the VO audio across the entire timeline (don't trim it — it drives pacing)

---

## Step 4 — Brand Elements (2 min)

1. **Intro:** Add YNAI5 logo image at frame 0 → set duration to 0.5s → add "pop" scale animation
2. **Color overlay:** Add an Adjustment Layer over the full timeline
   - Tint toward dark purple (`#1a0a2e`) at 15–20% opacity — gives cohesive brand feel
3. **Outro:** Add a text card at end — white text "YNAI5 World" on black background, 1 second
4. **Music (optional):** Add a trending TikTok audio at 20–30% volume under the VO
   - Audio style suggestion is in your script file

---

## Step 5 — Review & Export (2 min)

**Quick review checklist:**
- [ ] Hook lands in first 3 seconds — strong enough to stop scroll?
- [ ] VO is clear and audible (not drowned by music)
- [ ] All text overlays readable on mobile (preview on phone if possible)
- [ ] YNAI5 logo appears at start
- [ ] "YNAI5 World" outro at end
- [ ] Total duration: 15–40 seconds for TikTok Phase 1

**Export settings:**
- Resolution: 1080 × 1920 (9:16)
- Format: MP4
- Quality: High (recommended)
- Frame rate: 30fps

---

## Step 6 — Upload to TikTok (1 min)

1. Post between **7–9 PM AST** (peak engagement window)
2. Use **Caption Option B** from your script file (highest hook density)
3. Paste all 10 **hashtags** from your script file
4. Add 1 trending audio if you didn't bake it in during editing
5. Schedule or post immediately

---

## Step 7 — Track Performance (30 sec)

Update `projects/social-media-automation/content-tracker.md`:
- Move video from "In Production" → "Published"
- Log: date, topic, TikTok URL, initial views (check after 24h)

---

## Phase 2 Upgrade (After March 27 — Kling AI Added)

Replace Steps 1–2 with:
```
Claude calls mcp-kling → AI video generated → auto-downloaded
```
CapCut assembly remains but stock footage step is eliminated.
Target: under 5 minutes per video end-to-end.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| VO too fast / slow for clips | Adjust clip durations to match VO pacing — VO is the anchor |
| Stock clip doesn't match shot | Search Pexels alternative terms from video plan |
| Text hard to read | Add black background box behind text, reduce opacity to 80% |
| Video too long | Cut 1 body line — TikTok Phase 1 sweet spot is 18–25 seconds |
| Low views after 24h | Check hook — first 3 seconds must be stronger. Run /script-gen for next video |

---
_This playbook is for Phase 1. Update when Kling AI API is connected (March 27)._
