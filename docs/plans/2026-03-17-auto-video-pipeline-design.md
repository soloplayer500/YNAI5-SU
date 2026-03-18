# Design: YNAI5 Auto-Video Pipeline
Date: 2026-03-17
Status: Approved — building now

---

## Context
Current video production requires manually triggering each Claude skill (trend-check, content-gen, voice-gen) and then manually downloading Pexels footage + assembling in CapCut. Goal: eliminate all manual steps except the final TikTok upload. Claude makes all creative decisions. User gets a Telegram ping when the video is ready.

## Architecture: Modular Pipeline (Option B)

```
projects/social-media-automation/pipeline/
├── run.py          ← orchestrator — runs daily via Task Scheduler
├── trend.py        ← Brave Search → picks #1 viral AI topic
├── script.py       ← Anthropic API → YNAI5-voice script + shot list
├── voice.py        ← ElevenLabs API → MP3 voiceover
├── footage.py      ← Pexels API → downloads best clip per shot
├── assemble.py     ← FFmpeg → final 9:16 MP4 with text, tint, logo, outro
└── notify.py       ← Telegram → "🎬 Ready: [title] — upload tonight 7PM"
```

## Daily Flow
```
10:00 AM  Task Scheduler → python pipeline/run.py
          trend.py   → saves trends/YYYY-MM-DD-trends.md
          script.py  → saves scripts/YYYY-MM-DD-[slug].md
          voice.py   → saves audio/YYYY-MM-DD-[slug].mp3
          footage.py → saves footage/YYYY-MM-DD-[slug]/*.mp4
          assemble.py→ saves output/YYYY-MM-DD-[slug]-final.mp4
          notify.py  → Telegram ping with title + upload reminder
```

## Module Specs

### trend.py
- Queries Brave Search API (3 queries: AI news today, trending AI TikTok, ChatGPT/Claude/Gemini news)
- Scores virality (novelty, controversy, relatability, shareability)
- Returns top topic title + hook angle + source URL
- Saves full trends file

### script.py
- Calls Anthropic API (claude-haiku-4-5 for cost) with YNAI5 brand voice system prompt
- Input: topic + hook from trend.py
- Output: HOOK / BODY lines / CTA / captions / hashtags / shot list with Pexels terms
- Parses output into structured dict for downstream modules

### voice.py
- Calls ElevenLabs API (Liam voice — social media creator)
- Input: HOOK + BODY + CTA text from script.py
- Output: MP3 in audio/

### footage.py
- Calls Pexels Video API for each shot's search term
- Downloads best result (portrait/vertical preferred, 5–15s clips)
- Falls back to landscape if no vertical found
- Saves to footage/YYYY-MM-DD-[slug]/shot-N.mp4

### assemble.py
- Uses FFmpeg subprocess (no pip install needed)
- Per shot: trim clip to target duration, overlay text (white bold + black outline)
- Full video: YNAI5 logo flash (0.5s) → shots → outro text card (1s)
- Color grade: dark purple tint overlay at 20% opacity
- Mux with VO audio
- Output: output/YYYY-MM-DD-[slug]-final.mp4 (9:16, 1080p, 30fps)

### notify.py
- Sends Telegram message to personal chat (existing bot)
- Message includes: title, virality score, output file path, upload reminder

## Future Upgrade Path
When Kling/Higgsfield API is added:
- Replace `footage.py` with `kling.py` or `higgsfield.py`
- `assemble.py` receives AI-generated clips instead of Pexels downloads
- All other modules unchanged
- Swap decision: pick whichever tool has best quality/price/API at that time

## Hardware Constraints
- AMD Ryzen 5 5500U, 8GB RAM — FFmpeg runs fine for simple cuts
- stdlib only (no pip) — matches existing market-report.py pattern
- MacBook Neo (future) → move to cloud generation, GitHub Actions orchestration

## Keys Required (all already in .env.local)
- BRAVE_SEARCH_API_KEY
- ANTHROPIC_API_KEY
- ELEVENLABS_API_KEY
- PEXELS_API_KEY
- TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID

## Success Criteria
- Daily MP4 drops in output/ folder
- Telegram notification received by 10:15 AM
- Video quality: watchable, text readable, VO synced
- Zero manual steps before upload
