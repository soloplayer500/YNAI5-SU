# CapCut API Research + Telegram Bridge /gpt Plan
_Date: 2026-03-11 | Research Agent Output_

---

## TASK A: CapCut API — Verdict

### Does CapCut Have a Public API?

**Verdict: NO public API exists. CapCut is a closed consumer app.**

As of mid-2025 (latest confirmed knowledge):
- CapCut has **no published developer API**, no API keys, no docs, no webhook system
- ByteDance (CapCut's parent) has not announced any developer program for CapCut
- There is no MCP server for CapCut — no community-built one either
- CapCut operates entirely as a GUI app (mobile + desktop) — no programmatic trigger points
- Some "CapCut API" references online are scrapers or reverse-engineered workarounds — unstable, against ToS, and break on updates
- TikTok's own API (separate product) covers analytics/posting to TikTok — NOT video editing

**Summary:** CapCut cannot be integrated into an automated pipeline. It is not automation-friendly by design.

---

## CapCut Alternatives for Automated Video Pipeline

### Option 1: FFmpeg (RECOMMENDED for YNAI5)

**What it is:** Open-source CLI video/audio processing tool. Free, runs locally, no API needed.

**What it can do:**
- Concatenate clips together (assemble a video from parts)
- Add audio tracks (voiceover, background music)
- Add subtitles from .srt files
- Trim, cut, resize, reformat video
- Add fade in/out, transitions (basic)
- Convert formats (mp4, webm, etc.)
- Burn in text overlays (via drawtext filter)
- Add watermarks / logo overlays
- Control bitrate and quality for upload targets
- Output TikTok-ready vertical video (1080x1920)

**Limitations:**
- No AI-powered scene detection or style transfer
- No template system (you build templates manually via shell scripts)
- Text overlays are functional but basic (not CapCut quality animated captions)

**Best for YNAI5:** Assembling AI-generated clips + voiceover + music into a final video. Core workhorse of the pipeline.

**Install:** Already available via `winget install Gyan.FFmpeg` or download ffmpeg.exe

---

### Option 2: Remotion (React-Based Programmatic Video)

**What it is:** JavaScript/React framework — you code your video like a webpage, it renders to MP4.

**What it can do:**
- Full programmatic video generation from code/data
- Dynamic text, images, animations driven by JSON/API data
- Templated videos (change data → new video automatically)
- Integrates with React components
- Can render on a server (GitHub Actions, VPS)

**Limitations:**
- Requires Node.js + React knowledge
- Rendering is CPU-heavy (slow on 8GB RAM laptop — use cloud render)
- Not free for commercial use above 30-day trial (Remotion Player is free, Lambda render has cost)
- Learning curve if unfamiliar with React

**Best for YNAI5:** Data-driven videos (crypto price updates, news summaries with dynamic text). Overkill for basic content.

---

### Option 3: MoviePy (Python Video Editing Library)

**What it is:** Python library wrapping FFmpeg with a clean programmatic API.

**What it can do:**
- Clip assembly, concatenation
- Add audio (voiceover + background music with volume mixing)
- Text overlays with font/color/position control
- Fade/transition effects
- ImageSequenceClip (turn images into video for AI image pipelines)
- Fully scriptable from Python — integrates with existing YNAI5 Python scripts

**Limitations:**
- Slower than raw FFmpeg for large files
- Limited advanced effects (no motion graphics)
- Still requires FFmpeg installed

**Best for YNAI5:** Best Python-native option. Integrates cleanly with existing .py scripts. Text overlays, audio mixing, and clip assembly covered.

**Install:** `pip install moviepy`

---

### Option 4: Canva API (Free Tier Available)

**What it is:** Canva has a public API (Connect API) for design generation.

**What it can do:**
- Generate designs programmatically from templates
- Export as PNG/PDF
- Limited video template support (not full video editing)

**Best for YNAI5:** Thumbnails and static graphics — not video editing.

---

### Option 5: RunwayML API (Paid, Not Recommended Now)

**What it is:** AI video generation and editing API.

**What it can do:**
- Gen-3 Alpha video generation from text/image
- Video-to-video style transfer
- Inpainting, outpainting

**Limitations:**
- Paid API — $0.05+/second of video generated
- Budget-sensitive for YNAI5 at current stage

**Best for YNAI5:** Worth revisiting after first revenue. Not now.

---

## Recommended Video Stack for YNAI5 Pipeline (2026)

```
AI Image/Video Generation  →  Sora / Kling / Seedance (cloud)
           ↓
   Audio Generation        →  ElevenLabs TTS / RVC voice (local)
           ↓
   Music/BGM               →  Suno AI (export MP3)
           ↓
   Assembly + Mix          →  MoviePy (Python) or FFmpeg (CLI)
           ↓
   Captions (optional)     →  Whisper (transcribe) → .srt → FFmpeg burn-in
           ↓
   Upload                  →  YouTube Data API v3 / TikTok Upload API
```

FFmpeg + MoviePy replace CapCut in this pipeline. Total cost: $0.

---

## TASK B: Telegram Bridge — /gpt Command Plan

### Current Bridge Structure (telegram-claude-bridge.py)

File: `projects/personal-ai-infrastructure/telegram-claude-bridge.py`

**Key components:**
- Reads `.env.local` via `load_dotenv()` at line 14-15
- Auth: `ALLOWED_CHAT_ID` check on every handler
- `conversation_history` dict — keyed by `chat_id`, capped at `MAX_HISTORY = 20`
- `handle_message()` — catches all plain text (non-command), sends to Claude Haiku
- Registered handlers: `/start`, `/clear`, `/status` + plain text fallback

**Current flow:**
```
User sends message → handle_message() → Claude Haiku → reply
User sends /start → clear history, welcome
User sends /clear → clear history
User sends /status → show model + history count
```

---

### Code Plan: Adding /gpt + /claude Commands

**No changes to existing logic.** Only additions.

---

#### Step 1: Load OpenAI API Key

At the top of the file, after existing env vars (after line 19):

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

Add to the validation check (update line 21-22):

```python
if not TELEGRAM_BOT_TOKEN or not ANTHROPIC_API_KEY:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or ANTHROPIC_API_KEY in .env.local")
# Note: OPENAI_API_KEY is optional — /gpt command will warn if missing
```

---

#### Step 2: Add OpenAI HTTP Call Function

Add a new async function (after the existing `client = Anthropic(...)` line):

```python
import httpx  # add to top-level imports

async def call_gpt(messages: list) -> str:
    """Call GPT-4o-mini via OpenAI API."""
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set in .env.local"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "max_tokens": 1024
    }
    async with httpx.AsyncClient() as http:
        r = await http.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

**Why httpx instead of openai library:** Avoids a new pip install. `httpx` is likely already available (used by python-telegram-bot internally). Alternatively, `pip install openai` and use the official client — either works.

---

#### Step 3: Add gpt_command Handler

New handler function:

```python
async def gpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    user_message = " ".join(context.args) if context.args else ""
    if not user_message:
        await update.message.reply_text("Usage: /gpt [your message]")
        return
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    conversation_history[chat_id].append({"role": "user", "content": user_message})
    if len(conversation_history[chat_id]) > MAX_HISTORY:
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY:]
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        reply = await call_gpt(conversation_history[chat_id])
        conversation_history[chat_id].append({"role": "assistant", "content": reply})
        # Chunk if >4096 chars (same pattern as handle_message)
        if len(reply) <= 4096:
            await update.message.reply_text(f"[GPT-4o-mini]\n{reply}")
        else:
            # use same chunking logic as handle_message
            ...
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        await update.message.reply_text(f"GPT Error: {str(e)[:200]}")
```

---

#### Step 4: Add claude_command Handler (Explicit /claude Prefix)

New handler — mirrors handle_message but with explicit command syntax:

```python
async def claude_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    user_message = " ".join(context.args) if context.args else ""
    if not user_message:
        await update.message.reply_text("Usage: /claude [your message]")
        return
    # Same logic as handle_message() — routes to Claude Haiku
    # Copy handle_message body, replace user_message source
    ...
```

---

#### Step 5: Register New Handlers in main()

Update `main()` to register both new commands:

```python
def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("gpt", gpt_command))       # NEW
    app.add_handler(CommandHandler("claude", claude_command)) # NEW
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("YNAI5 Telegram-Claude Bridge starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
```

**Order matters:** CommandHandlers must be registered before the fallback MessageHandler. This is already the case in the current code — the new handlers go between /status and the MessageHandler line.

---

#### Step 6: Update /status to Show Both Models

Update the `status` handler reply:

```python
await update.message.reply_text(
    f"Bridge: ONLINE\n"
    f"Default: claude-haiku-4-5\n"
    f"/claude: claude-haiku-4-5\n"
    f"/gpt: gpt-4o-mini\n"
    f"History: {h} msgs"
)
```

---

### Conversation History Sharing Decision

**Option A: Shared history (current design)** — `/gpt` and `/claude` both read from the same `conversation_history[chat_id]`. Cross-model context. Simpler.

**Option B: Separate histories per model** — `claude_history[chat_id]` and `gpt_history[chat_id]`. Each model only sees its own prior replies.

**Recommendation: Option A (shared)** — keeps the current architecture intact, lets you reference a prior Claude answer when asking GPT. Easiest to implement. Can split later if needed.

---

### .env.local Change Required

Add one line:
```
OPENAI_API_KEY=sk-...
```

Use the Notepad method (preference saved 2026-03-10): open Notepad .txt on Desktop, paste key there, copy into .env.local manually.

---

### pip Install Required

If using `httpx` approach (already likely installed):
```
pip install httpx
```

If using official OpenAI library instead:
```
pip install openai
```

Both work. `httpx` keeps dependencies minimal.

---

## Summary

### CapCut Verdict
No API exists. Not automatable. Replace with:
- **MoviePy** (Python) — primary assembly tool, integrates with existing scripts
- **FFmpeg** (CLI) — underlying engine, subtitle burn-in, format conversion
- Both are free, local, and fit the 8GB RAM constraint

### Telegram Bridge /gpt Plan
4 code additions to `telegram-claude-bridge.py`:
1. Load `OPENAI_API_KEY` from `.env.local`
2. Add `call_gpt()` async function using `httpx` + OpenAI REST endpoint
3. Add `gpt_command()` handler for `/gpt [message]`
4. Add `claude_command()` handler for explicit `/claude [message]`
5. Register both in `main()` before the fallback MessageHandler
6. Update `/status` reply to show both models

Default behavior (plain text → Claude Haiku) unchanged. Shared conversation history. Restart bridge after changes.
