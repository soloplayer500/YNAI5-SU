# YNAI5 Auto-Video Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a fully automated daily pipeline that produces a ready-to-upload TikTok MP4 with zero manual steps — trend → script → voice → footage → FFmpeg assembly → Telegram notification.

**Architecture:** Modular Python (stdlib only). Each step is an independent module orchestrated by `run.py`. Future AI video gen (Kling/Higgsfield) slots in by replacing `footage.py` only.

**Tech Stack:** Python 3 stdlib, Brave Search API, Anthropic API (Haiku), ElevenLabs API, Pexels Video API, FFmpeg (subprocess), Telegram Bot API

---

## Task 0: Install FFmpeg

**Files:** none (system install)

**Step 1: Install via winget**
```bash
winget install Gyan.FFmpeg
```

**Step 2: Verify (open new terminal after install)**
```bash
ffmpeg -version
```
Expected: `ffmpeg version 8.x ...`

**Step 3: If PATH not updated, find and note the path**
```bash
where ffmpeg
```
Expected: `C:\Users\shema\AppData\Local\Microsoft\WinGet\Packages\...`

---

## Task 1: Create Pipeline Directory + Shared Config

**Files:**
- Create: `projects/social-media-automation/pipeline/__init__.py`
- Create: `projects/social-media-automation/pipeline/config.py`
- Create: `projects/social-media-automation/output/` (dir)
- Create: `projects/social-media-automation/footage/` (dir)

**Step 1: Create directories**
```bash
mkdir -p projects/social-media-automation/pipeline
mkdir -p projects/social-media-automation/output
mkdir -p projects/social-media-automation/footage
touch projects/social-media-automation/pipeline/__init__.py
```

**Step 2: Create `pipeline/config.py`**

```python
"""
Shared config for YNAI5 auto-video pipeline.
All modules import from here — single source of truth.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PIPELINE_DIR  = Path(__file__).resolve().parent
SMA_DIR       = PIPELINE_DIR.parent   # social-media-automation/
WORKSPACE     = SMA_DIR.parent.parent # YNAI5-SU/
ENV_FILE      = WORKSPACE / ".env.local"

TRENDS_DIR    = SMA_DIR / "trends"
SCRIPTS_DIR   = SMA_DIR / "scripts"
AUDIO_DIR     = SMA_DIR / "audio"
FOOTAGE_DIR   = SMA_DIR / "footage"
OUTPUT_DIR    = SMA_DIR / "output"
ASSETS_DIR    = WORKSPACE / "assets" / "ynai-world" / "brand"

# Ensure output dirs exist
for d in [TRENDS_DIR, SCRIPTS_DIR, AUDIO_DIR, FOOTAGE_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────────────
def _load_env() -> dict:
    if not ENV_FILE.exists():
        print(f"[ERROR] .env.local not found at {ENV_FILE}")
        sys.exit(1)
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

_ENV = _load_env()

def get_key(name: str) -> str:
    val = _ENV.get(name, "")
    if not val:
        print(f"[ERROR] {name} not found in .env.local")
        sys.exit(1)
    return val

BRAVE_API_KEY     = get_key("BRAVE_SEARCH_API_KEY")
ANTHROPIC_API_KEY = get_key("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = get_key("ELEVENLABS_API_KEY")
PEXELS_API_KEY    = get_key("PEXELS_API_KEY")
TELEGRAM_TOKEN    = get_key("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID  = get_key("TELEGRAM_CHAT_ID")

# ── Model / Voice ──────────────────────────────────────────────────────────────
CLAUDE_MODEL      = "claude-haiku-4-5-20251001"
ELEVENLABS_VOICE  = "TX3LPaxmHKxFdv7VOQHJ"   # Liam — Energetic Social Media Creator
ELEVENLABS_MODEL  = "eleven_multilingual_v2"

# ── Video settings ─────────────────────────────────────────────────────────────
VIDEO_WIDTH       = 1080
VIDEO_HEIGHT      = 1920
VIDEO_FPS         = 30
BRAND_COLOR       = "0x1a0a2e"   # dark purple tint
BRAND_TINT_ALPHA  = 0.20
FONT_PATH         = "C:/Windows/Fonts/arialbd.ttf"   # bold Arial, standard on Windows
FONT_SIZE         = 58
FONT_COLOR        = "white"
FONT_SHADOW       = "black"

# ── Helpers ────────────────────────────────────────────────────────────────────
def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:max_len].strip("-")
```

**Step 3: Verify config loads**
```bash
cd C:/Users/shema/OneDrive/Desktop/YNAI5-SU
python -c "from projects.social-media-automation.pipeline import config; print('Keys loaded OK')"
```

Note: use `python -c "import sys; sys.path.insert(0,'.');` if import path issues arise — run scripts directly instead.

**Step 4: Commit**
```bash
git add projects/social-media-automation/pipeline/
git commit -m "feat(pipeline): add directory structure and shared config"
```

---

## Task 2: trend.py — Brave Search → Top Topic

**Files:**
- Create: `projects/social-media-automation/pipeline/trend.py`

**Step 1: Create `pipeline/trend.py`**

```python
"""
trend.py — Finds today's top viral AI topic for TikTok.
Uses Brave Search API (3 queries) → scores virality → returns top pick.
"""

import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# Run standalone or imported
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    BRAVE_API_KEY, TRENDS_DIR, today, slugify
)

BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"

VIRALITY_KEYWORDS = [
    "just announced", "breaking", "shocking", "everyone", "viral",
    "billions", "trillion", "beats", "surpasses", "replaces", "fires",
    "launches", "acquires", "banned", "leaked", "exposed", "partnership",
    "apple", "google", "openai", "anthropic", "meta", "nvidia", "microsoft",
    "chatgpt", "gemini", "claude", "gpt", "siri", "ai model",
]


def _brave_search(query: str) -> list[dict]:
    """Single Brave Search call → list of result dicts"""
    params = urllib.parse.urlencode({
        "q": query,
        "count": 10,
        "search_lang": "en",
        "freshness": "pd",   # past day
    })
    req = urllib.request.Request(
        f"{BRAVE_URL}?{params}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data.get("web", {}).get("results", [])
    except Exception as e:
        print(f"  [trend] Search error for '{query}': {e}")
        return []


def _score_result(result: dict) -> float:
    """Score a search result on virality potential (0–10)"""
    text = (result.get("title", "") + " " + result.get("description", "")).lower()
    score = 0.0
    for kw in VIRALITY_KEYWORDS:
        if kw in text:
            score += 0.5
    # Bonus for big company names (higher shareability)
    big_names = ["apple", "google", "openai", "meta", "nvidia", "microsoft"]
    for name in big_names:
        if name in text:
            score += 0.8
    return min(score, 10.0)


def _extract_hook(title: str, description: str) -> str:
    """Generate a short hook angle from search result"""
    text = title + ". " + description
    # Look for contrast/surprise
    if any(w in text.lower() for w in ["replac", "partner", "beats", "surpass"]):
        return f"Nobody expected this: {title}"
    if any(w in text.lower() for w in ["billion", "trillion", "million"]):
        return f"The money behind this is wild: {title}"
    if any(w in text.lower() for w in ["ban", "expos", "leak"]):
        return f"They tried to hide this: {title}"
    return f"Wait— {title}"


def get_top_trend() -> dict:
    """
    Run 3 Brave searches, score all results, return top pick.
    Returns: {title, hook, source_url, virality, description}
    """
    date_str = datetime.now().strftime("%B %d %Y")
    queries = [
        f"AI news today {date_str}",
        f"trending AI tools viral TikTok {date_str}",
        f"ChatGPT Claude Gemini news this week {date_str}",
    ]

    print("[trend] Running 3 Brave searches in parallel...")
    all_results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(_brave_search, q): q for q in queries}
        for future in futures:
            results = future.result()
            all_results.extend(results)

    if not all_results:
        return {
            "title": "AI is changing everything in 2026",
            "hook": "Wait— AI just did something wild",
            "source_url": "",
            "virality": 5.0,
            "description": "General AI trends topic",
        }

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        url = r.get("url", "")
        if url not in seen:
            seen.add(url)
            unique.append(r)

    # Score and sort
    scored = sorted(unique, key=lambda r: _score_result(r), reverse=True)
    top = scored[0]

    title = top.get("title", "AI News Today")
    description = top.get("description", "")
    hook = _extract_hook(title, description)
    virality = round(_score_result(top), 1)

    result = {
        "title": title,
        "hook": hook,
        "source_url": top.get("url", ""),
        "virality": virality,
        "description": description,
    }

    # Save trends file
    _save_trends_file(result, scored[:5])
    return result


def _save_trends_file(top: dict, all_scored: list) -> None:
    date = today()
    path = TRENDS_DIR / f"{date}-trends.md"
    lines = [
        f"# Trend Check: {date}",
        "Platform: TikTok (auto-generated by pipeline)",
        "",
        "## Top Pick",
        f"**{top['title']}**",
        f"- Hook: {top['hook']}",
        f"- Virality estimate: {top['virality']}/10",
        f"- Source: {top['source_url']}",
        "",
        "## All Candidates (top 5)",
    ]
    for i, r in enumerate(all_scored[:5], 1):
        score = round(_score_result(r), 1)
        lines.append(f"{i}. [{r.get('title','')}]({r.get('url','')}) — {score}/10")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [trend] Saved → {path.name}")


if __name__ == "__main__":
    result = get_top_trend()
    print(f"\n[trend] Top pick: {result['title']}")
    print(f"        Hook: {result['hook']}")
    print(f"        Virality: {result['virality']}/10")
```

**Step 2: Note on imports** — when running from workspace root, Python needs the path. All modules use `sys.path.insert(0, ...)`. For module imports within pipeline, use relative imports when called via `run.py`.

**Step 3: Test trend.py standalone**
```bash
cd C:/Users/shema/OneDrive/Desktop/YNAI5-SU
python projects/social-media-automation/pipeline/trend.py
```
Expected:
```
[trend] Running 3 Brave searches in parallel...
  [trend] Saved → 2026-03-17-trends.md
[trend] Top pick: [some real AI headline]
        Hook: Wait— [headline]
        Virality: X.X/10
```

**Step 4: Commit**
```bash
git add projects/social-media-automation/pipeline/trend.py
git commit -m "feat(pipeline): add trend.py — Brave Search viral topic picker"
```

---

## Task 3: script.py — Anthropic API → YNAI5 Script + Shot List

**Files:**
- Create: `projects/social-media-automation/pipeline/script.py`

**Step 1: Create `pipeline/script.py`**

```python
"""
script.py — Generates YNAI5-voice TikTok script + shot list via Claude Haiku.
Input: topic dict from trend.py
Output: structured script dict + saved .md file
"""

import json
import re
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, SCRIPTS_DIR, today, slugify
)

SYSTEM_PROMPT = """You are the YNAI5 script writer. YNAI5 = Young Nigga AI — Gen Z AI content.
Every script sounds like your smartest friend texting you about wild AI news. Not a press release.

TONE: Chaotic-good. React first, explain second. Hot takes mandatory. Slightly unhinged is good.

USE: "bro what", "wait wait wait", "ngl", "no cap", "fr fr", "lowkey wild", "it's giving"
USE: "they actually just—", "not even joking", "this is so them", "ate and left no crumbs"
USE: "NPC behavior", "sigma move", "based", "unhinged", "the audacity"
USE AI slang: "the model dropped", "hallucinating again", "this AI ate", "context window cracked"

RULES:
- Short punchy bursts. One idea per line.
- All-caps ONE word per hook for emphasis
- Every script must have ONE hot take / exaggeration for humor
- CTA = debate-starter or tag prompt. NEVER "like and subscribe"
- NEVER write: "In today's video", "As we know", "Let's dive in", anything LinkedIn-sounding
- Target duration: 20-30 seconds spoken at normal pace

Return ONLY valid JSON. No markdown, no explanation. Exact format:
{
  "hook": "single punchy hook line starting with Wait— or Bro or POV:",
  "body": ["line 1", "line 2", "line 3", "line 4 hot take"],
  "cta": "debate-starter question or hot take",
  "caption_a": "caption under 150 chars with 3 hashtags",
  "caption_b": "caption under 150 chars with 3 hashtags",
  "hashtags": "#AI #TechNews #AINews #aitools #fyp #foryoupage and 4 topic-specific tags",
  "shots": [
    {"line": "exact spoken words", "text_overlay": "max 6 words", "pexels_term": "2-4 word search", "duration": 2.5},
    {"line": "...", "text_overlay": "...", "pexels_term": "...", "duration": 2.0}
  ]
}
shots array must have one entry per spoken line (hook + each body line + cta = 6-7 shots total).
pexels_term must be a concrete visual search term (e.g. "apple logo close-up", "shocked person phone").
duration is seconds — hook: 2-3s, body lines: 2-3s each, cta: 3s."""


def generate_script(trend: dict) -> dict:
    """
    Call Claude Haiku with YNAI5 brand voice prompt.
    Returns structured script dict.
    """
    user_msg = (
        f"Topic: {trend['title']}\n"
        f"Hook angle: {trend['hook']}\n"
        f"Context: {trend.get('description', '')}\n\n"
        "Write the full YNAI5 TikTok script. Return JSON only."
    )

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )

    print("[script] Calling Claude Haiku...")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            response = json.loads(r.read())
    except Exception as e:
        if hasattr(e, "read"):
            err = json.loads(e.read().decode())
            print(f"  [script] API error: {err}")
        else:
            print(f"  [script] Request failed: {e}")
        raise

    raw = response["content"][0]["text"].strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    script = json.loads(raw)
    script["topic"] = trend["title"]
    script["source_url"] = trend.get("source_url", "")
    script["virality"] = trend.get("virality", 0)

    _save_script_file(script)
    return script


def _save_script_file(script: dict) -> str:
    date = today()
    slug = slugify(script["topic"])
    path = SCRIPTS_DIR / f"{date}-{slug}.md"

    body_text = "\n".join(script.get("body", []))
    shots_table = "\n".join(
        f"| {i+1} | {s['line'][:50]} | {s['text_overlay']} | {s['pexels_term']} | {s['duration']}s |"
        for i, s in enumerate(script.get("shots", []))
    )

    content = f"""# Script: {script['topic']}
Date: {date}
Platform: TikTok
Virality: {script.get('virality', '?')}/10
Source: {script.get('source_url', '')}

---

## HOOK (0–3s)
{script.get('hook', '')}

## BODY
{body_text}

## CTA
{script.get('cta', '')}

---

## Captions
**Option A:** {script.get('caption_a', '')}
**Option B:** {script.get('caption_b', '')}

## Hashtags
{script.get('hashtags', '')}

---

## Shot List
| # | Line | Text Overlay | Pexels Term | Duration |
|---|------|--------------|-------------|----------|
{shots_table}

---
_Auto-generated by pipeline/script.py_
"""
    path.write_text(content, encoding="utf-8")
    print(f"  [script] Saved → {path.name}")
    return str(path)


def get_vo_text(script: dict) -> str:
    """Combine hook + body + cta into single VO string"""
    parts = [script["hook"]] + script.get("body", []) + [script["cta"]]
    return " ".join(parts)


if __name__ == "__main__":
    # Test with a dummy trend
    test_trend = {
        "title": "Apple is using Google Gemini for Siri",
        "hook": "Wait— Apple actually chose GOOGLE??",
        "description": "Apple announced Siri will be powered by Gemini for iOS 26.4",
        "source_url": "https://axios.com",
        "virality": 9.0,
    }
    result = generate_script(test_trend)
    print(f"\n[script] Hook: {result['hook']}")
    print(f"[script] Shots: {len(result['shots'])}")
```

**Step 2: Test script.py standalone**
```bash
python projects/social-media-automation/pipeline/script.py
```
Expected:
```
[script] Calling Claude Haiku...
  [script] Saved → 2026-03-17-apple-is-using-google-ge.md
[script] Hook: Wait— ...
[script] Shots: 6
```

**Step 3: Commit**
```bash
git add projects/social-media-automation/pipeline/script.py
git commit -m "feat(pipeline): add script.py — Claude Haiku YNAI5 script generator"
```

---

## Task 4: voice.py — ElevenLabs → MP3

**Files:**
- Create: `projects/social-media-automation/pipeline/voice.py`

**Step 1: Create `pipeline/voice.py`**

```python
"""
voice.py — ElevenLabs TTS → MP3 voiceover.
Reuses same API pattern as .claude/skills/voice-gen/generate.py.
"""

import json
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE, ELEVENLABS_MODEL,
    AUDIO_DIR, today, slugify
)


def generate_voice(text: str, slug: str) -> Path:
    """Call ElevenLabs TTS, save MP3, return path."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}"
    payload = json.dumps({
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "output_format": "mp3_44100_128",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST"
    )

    print("[voice] Calling ElevenLabs...")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            audio_bytes = r.read()
    except Exception as e:
        if hasattr(e, "read"):
            err = json.loads(e.read().decode())
            print(f"  [voice] API error: {err.get('detail', err)}")
        else:
            print(f"  [voice] Request failed: {e}")
        raise

    out_path = AUDIO_DIR / f"{today()}-{slug}.mp3"
    out_path.write_bytes(audio_bytes)
    print(f"  [voice] Saved → {out_path.name} ({len(audio_bytes)//1024} KB)")
    return out_path


if __name__ == "__main__":
    test_text = (
        "Wait— Apple actually chose GOOGLE?? "
        "Bro they literally just announced Siri is getting powered by Gemini. "
        "Apple. The company that built their whole identity around we protect your privacy. "
        "Just handed your voice assistant to Google. "
        "Ngl this is so them — Siri was so cooked they had zero choice fr fr. "
        "Hot take: Apple just publicly admitted Google won AI. Fight me."
    )
    path = generate_voice(test_text, "test-voice")
    print(f"[voice] Output: {path}")
```

**Step 2: Test voice.py**
```bash
python projects/social-media-automation/pipeline/voice.py
```
Expected: `[voice] Saved → 2026-03-17-test-voice.mp3 (XXX KB)`

**Step 3: Commit**
```bash
git add projects/social-media-automation/pipeline/voice.py
git commit -m "feat(pipeline): add voice.py — ElevenLabs TTS module"
```

---

## Task 5: footage.py — Pexels API → Download Clips

**Files:**
- Create: `projects/social-media-automation/pipeline/footage.py`

**Step 1: Create `pipeline/footage.py`**

```python
"""
footage.py — Downloads stock video clips from Pexels for each shot.
Prefers portrait (vertical) clips. Falls back to landscape with crop.
"""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    PEXELS_API_KEY, FOOTAGE_DIR, today, slugify
)

PEXELS_URL = "https://api.pexels.com/videos/search"


def _search_pexels(query: str, orientation: str = "portrait") -> list[dict]:
    """Search Pexels for videos matching query."""
    params = urllib.parse.urlencode({
        "query": query,
        "per_page": 8,
        "orientation": orientation,
        "size": "medium",
    })
    req = urllib.request.Request(
        f"{PEXELS_URL}?{params}",
        headers={"Authorization": PEXELS_API_KEY}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("videos", [])
    except Exception as e:
        print(f"  [footage] Pexels search error for '{query}': {e}")
        return []


def _best_file(video: dict, target_duration: float) -> str | None:
    """Pick the best quality download URL — prefer HD, close to target duration."""
    files = video.get("video_files", [])
    # Filter for reasonable quality
    hd = [f for f in files if f.get("quality") in ("hd", "sd") and f.get("link")]
    if not hd:
        return None
    # Sort by resolution (width desc)
    hd.sort(key=lambda f: f.get("width", 0), reverse=True)
    return hd[0]["link"]


def _download_clip(url: str, dest: Path) -> bool:
    """Download a video file to dest path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YNAI5-Pipeline/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  [footage] Download failed: {e}")
        return False


def download_footage(shots: list[dict], slug: str) -> list[Path]:
    """
    Download one clip per shot.
    shots: list of {pexels_term, duration, ...}
    Returns: list of local Path objects (same length as shots, None if failed)
    """
    clip_dir = FOOTAGE_DIR / f"{today()}-{slug}"
    clip_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, shot in enumerate(shots):
        term = shot.get("pexels_term", "technology")
        duration = shot.get("duration", 2.5)
        dest = clip_dir / f"shot-{i:02d}.mp4"

        if dest.exists():
            print(f"  [footage] Shot {i} already downloaded, skipping")
            paths.append(dest)
            continue

        print(f"  [footage] Shot {i}: searching '{term}'...")

        # Try portrait first, fall back to landscape
        videos = _search_pexels(term, "portrait")
        if not videos:
            videos = _search_pexels(term, "landscape")
        if not videos:
            videos = _search_pexels("technology abstract", "portrait")  # last resort

        if not videos:
            print(f"  [footage] No results for shot {i}, using placeholder")
            paths.append(None)
            continue

        # Pick first video with a valid HD file
        download_url = None
        for video in videos:
            url = _best_file(video, duration)
            if url:
                download_url = url
                break

        if not download_url:
            print(f"  [footage] No downloadable file for shot {i}")
            paths.append(None)
            continue

        print(f"  [footage] Downloading shot {i}...")
        success = _download_clip(download_url, dest)
        paths.append(dest if success else None)

    downloaded = sum(1 for p in paths if p is not None)
    print(f"[footage] Downloaded {downloaded}/{len(shots)} clips → {clip_dir.name}/")
    return paths


if __name__ == "__main__":
    test_shots = [
        {"pexels_term": "apple logo neon", "duration": 2.5},
        {"pexels_term": "siri voice assistant smartphone", "duration": 3.0},
        {"pexels_term": "google search interface", "duration": 2.0},
        {"pexels_term": "person laughing phone", "duration": 2.5},
    ]
    paths = download_footage(test_shots, "test-footage")
    for i, p in enumerate(paths):
        print(f"  Shot {i}: {p}")
```

**Step 2: Test footage.py**
```bash
python projects/social-media-automation/pipeline/footage.py
```
Expected:
```
  [footage] Shot 0: searching 'apple logo neon'...
  [footage] Downloading shot 0...
  ...
[footage] Downloaded 4/4 clips → 2026-03-17-test-footage/
```

**Step 3: Commit**
```bash
git add projects/social-media-automation/pipeline/footage.py
git commit -m "feat(pipeline): add footage.py — Pexels video downloader"
```

---

## Task 6: assemble.py — FFmpeg → Final MP4

**Files:**
- Create: `projects/social-media-automation/pipeline/assemble.py`

**Step 1: Create `pipeline/assemble.py`**

```python
"""
assemble.py — FFmpeg video assembly.
Takes shots (clips + text) + VO audio → outputs final 9:16 MP4.

Pipeline:
  For each shot: scale/crop to 1080x1920 → add text overlay → apply purple tint
  Then: concat all shots → add YNAI5 outro text card → mux with VO
  Output: output/YYYY-MM-DD-[slug]-final.mp4
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    OUTPUT_DIR, ASSETS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    BRAND_COLOR, BRAND_TINT_ALPHA, FONT_PATH, FONT_SIZE,
    today, slugify
)

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def _run(cmd: list, label: str) -> bool:
    """Run FFmpeg command, return True if success."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  [assemble] {label} failed:\n{result.stderr[-500:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  [assemble] {label} timed out")
        return False
    except Exception as e:
        print(f"  [assemble] {label} error: {e}")
        return False


def _escape_text(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    # Escape single quotes and colons
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    return text


def _process_shot(clip_path: Path | None, text_overlay: str,
                  duration: float, tmp_dir: Path, idx: int) -> Path | None:
    """
    Process a single shot:
    - Scale/crop to 1080x1920
    - Trim to duration
    - Add text overlay (white bold, black shadow)
    - Apply brand tint
    Returns processed clip path or None if failed.
    """
    out = tmp_dir / f"shot_{idx:02d}.mp4"
    escaped = _escape_text(text_overlay)
    tint_alpha = int(BRAND_TINT_ALPHA * 255)
    tint_hex = BRAND_COLOR.replace("0x", "")

    if clip_path and clip_path.exists():
        # Scale to fill 1080x1920 (crop center), trim, add text + tint
        vf = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"drawbox=x=0:y=0:w=iw:h=ih:color={tint_hex}@{BRAND_TINT_ALPHA}:t=fill,"
            f"drawtext=fontfile='{FONT_PATH}':text='{escaped}':"
            f"fontcolor=white:fontsize={FONT_SIZE}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"shadowcolor=black:shadowx=3:shadowy=3:box=1:boxcolor=black@0.4:boxborderw=10"
        )
        cmd = [
            FFMPEG, "-y", "-ss", "0", "-i", str(clip_path),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(VIDEO_FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            str(out)
        ]
    else:
        # No clip — generate black card with text
        vf = (
            f"color=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}:d={duration},"
            f"drawtext=fontfile='{FONT_PATH}':text='{escaped}':"
            f"fontcolor=white:fontsize={FONT_SIZE}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"shadowcolor=black:shadowx=3:shadowy=3"
        )
        cmd = [
            FFMPEG, "-y",
            "-f", "lavfi", "-i", vf,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            str(out)
        ]

    success = _run(cmd, f"shot {idx}")
    return out if success else None


def _make_outro(tmp_dir: Path, duration: float = 1.0) -> Path:
    """Generate 'YNAI5 World' outro text card on black."""
    out = tmp_dir / "outro.mp4"
    text = "YNAI5 WORLD"
    vf = (
        f"color=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}:d={duration},"
        f"drawtext=fontfile='{FONT_PATH}':text='{text}':"
        f"fontcolor=white:fontsize=80:"
        f"x=(w-text_w)/2:y=(h-text_h)/2"
    )
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", vf,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(out)
    ]
    _run(cmd, "outro")
    return out


def _concat_clips(clip_paths: list[Path], tmp_dir: Path) -> Path:
    """Concatenate all processed clips using FFmpeg concat demuxer."""
    list_file = tmp_dir / "concat_list.txt"
    lines = [f"file '{str(p).replace(chr(92), '/')}'\n" for p in clip_paths if p and p.exists()]
    list_file.write_text("".join(lines), encoding="utf-8")

    out = tmp_dir / "concat.mp4"
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(out)
    ]
    _run(cmd, "concat")
    return out


def assemble_video(shots: list[dict], clip_paths: list[Path | None],
                   vo_path: Path, slug: str) -> Path | None:
    """
    Full assembly pipeline.
    shots: list of {text_overlay, duration, ...}
    clip_paths: downloaded footage paths (parallel to shots)
    vo_path: ElevenLabs MP3
    Returns: final MP4 path
    """
    print("[assemble] Starting FFmpeg assembly...")
    out_path = OUTPUT_DIR / f"{today()}-{slug}-final.mp4"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        processed = []

        # Process each shot
        for i, (shot, clip) in enumerate(zip(shots, clip_paths)):
            print(f"  [assemble] Processing shot {i}/{len(shots)}...")
            text = shot.get("text_overlay", "")
            duration = shot.get("duration", 2.5)
            processed_clip = _process_shot(clip, text, duration, tmp_dir, i)
            processed.append(processed_clip)

        # Add outro
        outro = _make_outro(tmp_dir)
        processed.append(outro)

        # Concatenate
        print("  [assemble] Concatenating clips...")
        concat = _concat_clips(processed, tmp_dir)

        if not concat.exists():
            print("[assemble] Concat failed — aborting")
            return None

        # Mux with VO audio
        print("  [assemble] Muxing with voiceover...")
        cmd = [
            FFMPEG, "-y",
            "-i", str(concat),
            "-i", str(vo_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",   # end when shorter stream ends
            "-movflags", "+faststart",
            str(out_path)
        ]
        success = _run(cmd, "final mux")

    if success and out_path.exists():
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"[assemble] Done → {out_path.name} ({size_mb:.1f} MB)")
        return out_path
    else:
        print("[assemble] Final mux failed")
        return None


if __name__ == "__main__":
    # Test with existing files from today's session
    from pathlib import Path as P
    import sys

    test_shots = [
        {"text_overlay": "APPLE CHOSE GOOGLE??", "duration": 2.5, "pexels_term": "apple logo"},
        {"text_overlay": "SIRI → GEMINI", "duration": 3.0, "pexels_term": "smartphone"},
        {"text_overlay": "the audacity fr fr", "duration": 2.5, "pexels_term": "shocked face"},
        {"text_overlay": "Google ATE. no crumbs.", "duration": 2.5, "pexels_term": "google"},
        {"text_overlay": "Fight me.", "duration": 3.0, "pexels_term": "debate"},
    ]

    # Use a real VO if available
    audio_dir = P(__file__).resolve().parents[1] / "audio"
    vo_files = list(audio_dir.glob("*.mp3"))
    if not vo_files:
        print("[test] No VO file found — run voice.py first")
        sys.exit(1)

    vo = vo_files[-1]
    print(f"[test] Using VO: {vo.name}")

    # Use None clips (will generate black cards with text)
    clips = [None] * len(test_shots)
    result = assemble_video(test_shots, clips, vo, "test-assembly")
    if result:
        print(f"[test] Output: {result}")
```

**Step 2: Test assemble.py with text cards only (no footage needed)**
```bash
python projects/social-media-automation/pipeline/assemble.py
```
Expected: `[assemble] Done → 2026-03-17-test-assembly-final.mp4 (X.X MB)`

**Step 3: Check output plays correctly**
Open `projects/social-media-automation/output/2026-03-17-test-assembly-final.mp4` in Windows Media Player or VLC. Should show black cards with white text, VO audio, YNAI5 WORLD outro.

**Step 4: Commit**
```bash
git add projects/social-media-automation/pipeline/assemble.py
git commit -m "feat(pipeline): add assemble.py — FFmpeg video assembler"
```

---

## Task 7: notify.py — Telegram Notification

**Files:**
- Create: `projects/social-media-automation/pipeline/notify.py`

**Step 1: Create `pipeline/notify.py`**

```python
"""
notify.py — Sends Telegram message when video is ready.
Uses existing bot (same as market-report.py pattern).
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from projects.social_media_automation.pipeline.config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
)


def send(message: str) -> bool:
    """Send a Telegram message to personal chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"  [notify] Telegram error: {e}")
        return False


def video_ready(title: str, virality: float, output_path: Path) -> None:
    """Send 'video ready' notification."""
    msg = (
        f"🎬 <b>YNAI5 Video Ready</b>\n\n"
        f"📌 <b>Topic:</b> {title}\n"
        f"🔥 <b>Virality:</b> {virality}/10\n"
        f"📁 <b>File:</b> {output_path.name}\n\n"
        f"⏰ <b>Post tonight 7–9 PM AST</b>\n"
        f"✅ Open TikTok → upload → paste caption B + hashtags"
    )
    success = send(msg)
    print(f"[notify] Telegram {'sent ✓' if success else 'FAILED'}")


def pipeline_error(step: str, error: str) -> None:
    """Send error notification if pipeline fails."""
    msg = (
        f"⚠️ <b>YNAI5 Pipeline Error</b>\n\n"
        f"Step: {step}\n"
        f"Error: {error[:200]}"
    )
    send(msg)


if __name__ == "__main__":
    video_ready(
        "Apple is using Google Gemini for Siri",
        9.0,
        Path("output/2026-03-17-test-final.mp4")
    )
```

**Step 2: Test notify.py**
```bash
python projects/social-media-automation/pipeline/notify.py
```
Expected: Telegram message received on phone + `[notify] Telegram sent ✓`

**Step 3: Commit**
```bash
git add projects/social-media-automation/pipeline/notify.py
git commit -m "feat(pipeline): add notify.py — Telegram video-ready notification"
```

---

## Task 8: run.py — Daily Orchestrator

**Files:**
- Create: `projects/social-media-automation/pipeline/run.py`

**Step 1: Create `pipeline/run.py`**

```python
"""
run.py — YNAI5 Auto-Video Pipeline Orchestrator
Runs daily via Windows Task Scheduler at 10:00 AM.

Chain: trend → script → voice → footage → assemble → notify
Each step is independent — failures are caught and reported via Telegram.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

# Ensure workspace root is on path
WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE))

from projects.social_media_automation.pipeline.config import slugify, today
from projects.social_media_automation.pipeline import notify


def run_pipeline():
    start = datetime.now()
    print(f"\n{'='*60}")
    print(f"YNAI5 Auto-Video Pipeline — {start.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    slug = None
    trend = None
    script = None
    vo_path = None
    clip_paths = None
    output = None

    # ── Step 1: Trend ──────────────────────────────────────────────────────────
    try:
        print("Step 1/6 — Trend Check")
        from projects.social_media_automation.pipeline.trend import get_top_trend
        trend = get_top_trend()
        slug = slugify(trend["title"])
        print(f"  → Topic: {trend['title']}")
        print(f"  → Virality: {trend['virality']}/10\n")
    except Exception as e:
        notify.pipeline_error("trend", str(e))
        print(f"[FATAL] Trend step failed: {e}")
        return

    # ── Step 2: Script ─────────────────────────────────────────────────────────
    try:
        print("Step 2/6 — Script Generation")
        from projects.social_media_automation.pipeline.script import generate_script, get_vo_text
        script = generate_script(trend)
        print(f"  → Hook: {script['hook'][:60]}...")
        print(f"  → Shots: {len(script.get('shots', []))}\n")
    except Exception as e:
        notify.pipeline_error("script", str(e))
        print(f"[FATAL] Script step failed: {e}")
        return

    # ── Step 3: Voice ──────────────────────────────────────────────────────────
    try:
        print("Step 3/6 — Voice Generation")
        from projects.social_media_automation.pipeline.script import get_vo_text
        from projects.social_media_automation.pipeline.voice import generate_voice
        vo_text = get_vo_text(script)
        vo_path = generate_voice(vo_text, slug)
        print(f"  → Audio: {vo_path.name}\n")
    except Exception as e:
        notify.pipeline_error("voice", str(e))
        print(f"[FATAL] Voice step failed: {e}")
        return

    # ── Step 4: Footage ────────────────────────────────────────────────────────
    try:
        print("Step 4/6 — Footage Download")
        from projects.social_media_automation.pipeline.footage import download_footage
        shots = script.get("shots", [])
        clip_paths = download_footage(shots, slug)
        downloaded = sum(1 for p in clip_paths if p is not None)
        print(f"  → {downloaded}/{len(shots)} clips downloaded\n")
    except Exception as e:
        notify.pipeline_error("footage", str(e))
        print(f"[WARN] Footage step failed, continuing with text cards: {e}")
        clip_paths = [None] * len(script.get("shots", []))

    # ── Step 5: Assemble ───────────────────────────────────────────────────────
    try:
        print("Step 5/6 — Video Assembly")
        from projects.social_media_automation.pipeline.assemble import assemble_video
        shots = script.get("shots", [])
        output = assemble_video(shots, clip_paths, vo_path, slug)
        if output:
            print(f"  → Output: {output.name}\n")
        else:
            raise RuntimeError("assemble_video returned None")
    except Exception as e:
        notify.pipeline_error("assemble", str(e))
        print(f"[FATAL] Assembly step failed: {e}")
        traceback.print_exc()
        return

    # ── Step 6: Notify ─────────────────────────────────────────────────────────
    print("Step 6/6 — Sending Telegram Notification")
    notify.video_ready(trend["title"], trend["virality"], output)

    elapsed = (datetime.now() - start).seconds
    print(f"\n{'='*60}")
    print(f"Pipeline complete in {elapsed}s")
    print(f"Output: {output}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_pipeline()
```

**Step 2: Full end-to-end test**
```bash
cd C:/Users/shema/OneDrive/Desktop/YNAI5-SU
python projects/social-media-automation/pipeline/run.py
```

Expected output (10-12 minutes total):
```
============================================================
YNAI5 Auto-Video Pipeline — 2026-03-17 HH:MM
============================================================

Step 1/6 — Trend Check
  [trend] Running 3 Brave searches...
  → Topic: [real headline]
  → Virality: X.X/10

Step 2/6 — Script Generation
  [script] Calling Claude Haiku...
  → Hook: Wait— ...
  → Shots: 6

Step 3/6 — Voice Generation
  [voice] Calling ElevenLabs...
  → Audio: 2026-03-17-[slug].mp3

Step 4/6 — Footage Download
  [footage] Shot 0: searching '...'
  → 6/6 clips downloaded

Step 5/6 — Video Assembly
  [assemble] Processing shot 0/6...
  [assemble] Done → 2026-03-17-[slug]-final.mp4 (X.X MB)

Step 6/6 — Sending Telegram Notification
  [notify] Telegram sent ✓

============================================================
Pipeline complete in XXXs
Output: ...output/2026-03-17-[slug]-final.mp4
============================================================
```

**Step 3: Commit**
```bash
git add projects/social-media-automation/pipeline/run.py
git commit -m "feat(pipeline): add run.py — daily orchestrator, end-to-end pipeline complete"
```

---

## Task 9: Register Task Scheduler

**Files:**
- Create: `projects/social-media-automation/pipeline/run-pipeline.bat`

**Step 1: Create the batch file**

```bat
@echo off
cd /d C:\Users\shema\OneDrive\Desktop\YNAI5-SU
python projects\social-media-automation\pipeline\run.py >> projects\social-media-automation\pipeline\pipeline.log 2>&1
```

**Step 2: Register with Task Scheduler (run in Git Bash or PowerShell)**
```bash
schtasks /create \
  /tn "YNAI5-AutoVideo" \
  /tr "C:\\Users\\shema\\OneDrive\\Desktop\\YNAI5-SU\\projects\\social-media-automation\\pipeline\\run-pipeline.bat" \
  /sc daily \
  /st 10:00 \
  /f
```

**Step 3: Verify task registered**
```bash
schtasks /query /tn "YNAI5-AutoVideo"
```

**Step 4: Test manual trigger**
```bash
schtasks /run /tn "YNAI5-AutoVideo"
```

Then check `pipeline/pipeline.log` for output.

**Step 5: Final commit**
```bash
git add projects/social-media-automation/pipeline/run-pipeline.bat
git commit -m "feat(pipeline): add Task Scheduler bat + register daily 10AM job"
```

---

## Verification Checklist

After all tasks complete:
- [ ] `ffmpeg -version` returns v8.x
- [ ] `python pipeline/run.py` runs end-to-end without errors
- [ ] `output/YYYY-MM-DD-*-final.mp4` exists and plays in VLC
- [ ] MP4 is 9:16 vertical, text overlays readable, VO audio synced
- [ ] Telegram notification received on phone
- [ ] Task Scheduler shows `YNAI5-AutoVideo` in task list
- [ ] `pipeline.log` populated after scheduled run

## Future Swap: Kling/Higgsfield
When AI video gen is purchased:
1. Create `pipeline/kling.py` with same interface as `footage.py`
   - `download_footage(shots, slug) -> list[Path]`
2. In `run.py` Step 4, change one import line:
   ```python
   # from projects.social_media_automation.pipeline.footage import download_footage
   from projects.social_media_automation.pipeline.kling import download_footage
   ```
3. Everything else unchanged.
