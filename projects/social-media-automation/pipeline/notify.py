"""
notify.py — Sends Telegram messages when video is ready or pipeline errors.
Uses existing YNAI5 Telegram bot (same as market-report.py).
"""
import json
import urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config


def send(message: str) -> bool:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": config.TELEGRAM_CHAT_ID,
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
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"  [notify] Telegram error: {e}")
        return False


def video_ready(title: str, virality: float, output_path: Path) -> None:
    msg = (
        f"YNAI5 Video Ready\n\n"
        f"Topic: {title}\n"
        f"Virality: {virality}/10\n"
        f"File: {output_path.name}\n\n"
        f"Post tonight 7-9 PM AST\n"
        f"Open TikTok -> upload -> paste caption B + hashtags"
    )
    ok = send(msg)
    print(f"  [notify] Telegram {'sent OK' if ok else 'FAILED'}")


def pipeline_error(step: str, error: str) -> None:
    msg = f"YNAI5 Pipeline Error\nStep: {step}\nError: {error[:300]}"
    send(msg)


if __name__ == "__main__":
    video_ready(
        "Apple is using Google Gemini for Siri",
        9.0,
        Path("output/2026-03-17-test-final.mp4")
    )
