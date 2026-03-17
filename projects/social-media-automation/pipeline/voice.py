"""
voice.py — ElevenLabs TTS -> MP3 voiceover.
Voice: Liam (TX3LPaxmHKxFdv7VOQHJ) — Energetic Social Media Creator.
Free tier works with this voice ID (premade voices in account library).
"""
import json
import urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def generate_voice(text: str, slug: str) -> Path:
    """Call ElevenLabs TTS, save MP3, return path."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE}"
    payload = json.dumps({
        "text": text,
        "model_id": config.ELEVENLABS_MODEL,
        "output_format": "mp3_44100_128",
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={
            "xi-api-key": config.ELEVENLABS_API_KEY,
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
            try:
                err = json.loads(e.read().decode())
                print(f"  [voice] API error: {err.get('detail', err)}")
            except Exception:
                pass
        raise

    out_path = config.AUDIO_DIR / f"{config.today()}-{slug}.mp3"
    out_path.write_bytes(audio_bytes)
    size_kb = len(audio_bytes) // 1024
    print(f"  [voice] Saved -> {out_path.name} ({size_kb} KB)")
    return out_path


if __name__ == "__main__":
    test_text = (
        "wait APPLE just chose GOOGLE to run Siri?? "
        "like bro what is even happening right now "
        "they literally just announced Siri is getting powered by Gemini. "
        "Apple. The company that built their whole identity around privacy. "
        "Just handed your voice assistant to Google. "
        "Ngl Siri was so cooked they had zero choice fr fr. "
        "Hot take: Apple just publicly admitted Google won AI. Fight me."
    )
    path = generate_voice(test_text, "pipeline-voice-test")
    print(f"[voice] Output: {path}")
