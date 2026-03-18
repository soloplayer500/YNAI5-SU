"""
script.py — Generates YNAI5-voice TikTok script + shot list via Claude Haiku.
Returns structured dict consumed by voice.py, footage.py, assemble.py.
"""
import json
import re
import urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

SYSTEM_PROMPT = """You are the YNAI5 script writer. YNAI5 = Young Nigga AI. Gen Z AI content.
Every script sounds like your smartest, most plugged-in friend breaking down wild AI news.
Not a press release. Not a LinkedIn post. Real talk with real facts.

TONE: Chaotic-good. React first, explain second. Hot takes mandatory. Slightly unhinged is good.
But: every reaction is backed by an actual fact, number, or comparison. No empty vibes.

USE: "bro what", "wait wait wait", "ngl", "no cap", "fr fr", "lowkey wild", "it's giving"
USE: "they actually just", "not even joking", "this is so them", "ate and left no crumbs"
USE: "NPC behavior", "based", "unhinged", "the audacity"

CONTENT RULES — this is what makes viewers STAY and SHARE:
- Hook: 1 punchy line that creates immediate curiosity or shock (all-caps ONE word for emphasis)
- Body lines 1-2: the actual news/fact — what happened, numbers if available
- Body lines 3-4: WHY it matters — real-world impact on the viewer, comparison or context
- Body lines 5-6: hot take + zoom out — what this means for the bigger picture
- Body lines 7-8 (optional): counterpoint or "what they're not telling you" angle
- CTA: debate-starter question OR "what would you do" prompt. NEVER "like and subscribe"

RULES:
- Short punchy bursts. One idea per line. No multi-clause sentences.
- Include at least ONE real stat, number, or named fact per script
- Include at least ONE comparison (vs competitor, vs before, vs expectation)
- Every script must have ONE hot take or exaggeration for humor
- NEVER write: "In today's video", "As we know", "Let's dive in", anything LinkedIn-sounding
- Target duration: 21-30 seconds spoken at natural pace — this is the TikTok completion rate sweet spot
- 4-5 body lines MAXIMUM — short and punchy beats long and detailed every time
- Deliver the key fact + hot take within the first 15 seconds — hook, context, boom

Return ONLY valid JSON, no markdown fences, no explanation:
{
  "hook": "single punchy hook line",
  "body": ["line 1", "line 2", "line 3", "line 4"],
  "cta": "debate-starter question or hot take",
  "caption_a": "caption under 150 chars with 3 hashtags",
  "caption_b": "caption under 150 chars with 3 hashtags",
  "hashtags": "10 hashtags space-separated",
  "shots": [
    {"line": "exact spoken words", "text_overlay": "max 6 words", "pexels_term": "2-4 word search", "duration": 2.5}
  ]
}
shots: one entry per spoken line (hook + each body line + cta).
pexels_term = concrete visual matching what's being said (e.g. "apple logo closeup", "coding screen terminal", "person shocked phone").
duration in seconds (hook 2-3s, body lines 2.5-3.5s each, cta 3-4s).
IMPORTANT: shots array must have exactly one entry per spoken line."""


def generate_script(trend: dict) -> dict:
    user_msg = (
        f"Topic: {trend['title']}\n"
        f"Hook angle: {trend['hook']}\n"
        f"Context: {trend.get('description', '')}\n\n"
        "Write the full YNAI5 TikTok script. Return JSON only."
    )
    payload = json.dumps({
        "model": config.CLAUDE_MODEL,
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": config.ANTHROPIC_API_KEY,
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
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = re.sub(r"^```\s*", "", raw)

    script = json.loads(raw)
    script["topic"] = trend["title"]
    script["source_url"] = trend.get("source_url", "")
    script["virality"] = trend.get("virality", 0)
    _save(script)
    return script


def get_vo_text(script: dict) -> str:
    """Combine hook + body + cta into single VO string."""
    parts = [script["hook"]] + script.get("body", []) + [script["cta"]]
    # Strip emojis for cleaner TTS
    text = " ".join(parts)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()


def _save(script: dict) -> None:
    date = config.today()
    slug = config.slugify(script["topic"])
    path = config.SCRIPTS_DIR / f"{date}-{slug}.md"

    body_text = "\n".join(script.get("body", []))
    shots_rows = "\n".join(
        f"| {i+1} | {s['line'][:50]} | {s['text_overlay']} | {s['pexels_term']} | {s['duration']}s |"
        for i, s in enumerate(script.get("shots", []))
    )

    content = f"""# Script: {script['topic']}
Date: {date}
Platform: TikTok
Virality: {script.get('virality','?')}/10
Source: {script.get('source_url','')}

---

## HOOK
{script.get('hook','')}

## BODY
{body_text}

## CTA
{script.get('cta','')}

---

## Captions
**Option A:** {script.get('caption_a','')}
**Option B:** {script.get('caption_b','')}

## Hashtags
{script.get('hashtags','')}

---

## Shot List
| # | Line | Text Overlay | Pexels Term | Duration |
|---|------|--------------|-------------|----------|
{shots_rows}

---
_Auto-generated by pipeline/script.py_
"""
    path.write_text(content, encoding="utf-8")
    print(f"  [script] Saved -> {path.name}")


if __name__ == "__main__":
    test_trend = {
        "title": "Apple is using Google Gemini for Siri",
        "hook": "Wait— Apple actually chose GOOGLE??",
        "description": "Apple announced Siri will be powered by Gemini for iOS 26.4",
        "source_url": "https://axios.com",
        "virality": 9.0,
    }
    result = generate_script(test_trend)
    print(f"\n[script] Hook: {result['hook']}")
    print(f"[script] Body lines: {len(result.get('body',[]))}")
    print(f"[script] Shots: {len(result.get('shots',[]))}")
    print(f"[script] VO text preview: {get_vo_text(result)[:100]}")
