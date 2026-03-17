"""
Shared config for YNAI5 auto-video pipeline.
All modules import from here: import sys; sys.path.insert(0, str(Path(__file__).resolve().parent)); import config
"""
import os, re, sys
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PIPELINE_DIR  = Path(__file__).resolve().parent
SMA_DIR       = PIPELINE_DIR.parent
WORKSPACE     = SMA_DIR.parent.parent
ENV_FILE      = WORKSPACE / ".env.local"

TRENDS_DIR    = SMA_DIR / "trends"
SCRIPTS_DIR   = SMA_DIR / "scripts"
AUDIO_DIR     = SMA_DIR / "audio"
FOOTAGE_DIR   = SMA_DIR / "footage"
OUTPUT_DIR    = SMA_DIR / "output"
ASSETS_DIR    = WORKSPACE / "assets" / "ynai-world" / "brand"

for d in [TRENDS_DIR, SCRIPTS_DIR, AUDIO_DIR, FOOTAGE_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────────────────────
def _load_env() -> dict:
    if not ENV_FILE.exists():
        print(f"[ERROR] .env.local not found at {ENV_FILE}"); sys.exit(1)
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
        print(f"[ERROR] {name} not found in .env.local"); sys.exit(1)
    return val

BRAVE_API_KEY      = get_key("BRAVE_SEARCH_API_KEY")
ANTHROPIC_API_KEY  = get_key("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = get_key("ELEVENLABS_API_KEY")
PEXELS_API_KEY     = get_key("PEXELS_API_KEY")
TELEGRAM_TOKEN     = get_key("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = get_key("TELEGRAM_CHAT_ID")

# ── Model / Voice ──────────────────────────────────────────────────────────────
CLAUDE_MODEL      = "claude-haiku-4-5-20251001"
ELEVENLABS_VOICE  = "TX3LPaxmHKxFdv7VOQHJ"   # Liam — Energetic Social Media Creator
ELEVENLABS_MODEL  = "eleven_multilingual_v2"

# ── Video settings ─────────────────────────────────────────────────────────────
VIDEO_WIDTH   = 1080
VIDEO_HEIGHT  = 1920
VIDEO_FPS     = 30
BRAND_TINT_ALPHA = 0.20
FONT_SIZE     = 58
FONT_COLOR    = "white"
FFMPEG_PATH   = r"C:/Users/shema/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/ffmpeg.exe"
FONT_PATH     = "C:/Windows/Fonts/arialbd.ttf"

# ── Helpers ────────────────────────────────────────────────────────────────────
def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:max_len].strip("-")
