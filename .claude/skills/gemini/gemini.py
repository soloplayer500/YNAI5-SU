#!/usr/bin/env python3
"""
Gemini Sub-Agent — YNAI5-SU
Uses Google Gemini API as a sub-agent for research, analysis, and generation tasks.
Reads GEMINI_API_KEY from .env.local. Zero external dependencies (stdlib only).

Usage:
  python gemini.py --task "summarize" --input "Your text or question here"
  python gemini.py --task "research" --input "What is AI prompt chaining?" --model pro
  python gemini.py --task "analyze" --input "Compare X vs Y" --save
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE       = WORKSPACE_ROOT / ".env.local"
NOTES_DIR      = WORKSPACE_ROOT / "notes"

MODELS = {
    "flash": "gemini-flash-latest",   # always latest stable flash — confirmed working
    "pro":   "gemini-pro-latest",     # latest pro model
}
DEFAULT_MODEL = "flash"

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_api_key() -> str:
    if not ENV_FILE.exists():
        print(f"[ERROR] .env.local not found at: {ENV_FILE}")
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    return key
    print("[ERROR] GEMINI_API_KEY not found in .env.local")
    sys.exit(1)


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:max_len].strip("-")


def call_gemini(api_key: str, model_key: str, task: str, input_text: str) -> str:
    import urllib.request

    model_id = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    url = f"{API_BASE}/{model_id}:generateContent?key={api_key}"

    # Build prompt combining task + input
    prompt = f"Task: {task}\n\n{input_text}" if task.lower() not in input_text.lower() else input_text

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            candidates = data.get("candidates", [])
            if not candidates:
                print("[ERROR] Gemini returned no candidates")
                sys.exit(1)
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
    except Exception as e:
        if hasattr(e, "read"):
            try:
                err = json.loads(e.read().decode())
                msg = err.get("error", {}).get("message", str(e))
                print(f"[ERROR] Gemini API: {msg}")
            except Exception:
                print(f"[ERROR] Request failed: {e}")
        else:
            print(f"[ERROR] Request failed: {e}")
        sys.exit(1)


def save_output(task: str, input_text: str, response: str) -> Path:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(task)
    out_path = NOTES_DIR / f"gemini-{today}-{slug}.md"

    content = f"# Gemini: {task}\n"
    content += f"Date: {today}\n"
    content += f"Model: {MODELS.get(DEFAULT_MODEL)}\n\n"
    content += f"## Input\n{input_text}\n\n"
    content += f"## Response\n{response}\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return out_path


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Gemini sub-agent")
    parser.add_argument("--task",  "-t", required=True,
                        help="Task type (e.g. 'summarize', 'research', 'analyze', 'generate')")
    parser.add_argument("--input", "-i", required=True,
                        help="Input text, question, or content to process")
    parser.add_argument("--model", "-m", choices=["flash", "pro"], default=DEFAULT_MODEL,
                        help="Model: flash (fast, 1500/day) or pro (deep, 100/day)")
    parser.add_argument("--save",  "-s", action="store_true",
                        help="Save output to notes/gemini-YYYY-MM-DD-{task}.md")
    args = parser.parse_args()

    api_key = load_api_key()
    model_name = MODELS[args.model]

    print(f"[gemini] Task    : {args.task}")
    print(f"[gemini] Model   : {model_name}")
    print(f"[gemini] Input   : {args.input[:80]}{'...' if len(args.input) > 80 else ''}")
    print(f"[gemini] Calling API...")

    response = call_gemini(api_key, args.model, args.task, args.input)

    print(f"\n--- Gemini Response ---\n")
    print(response)
    print(f"\n--- End Response ---")

    if args.save:
        out_path = save_output(args.task, args.input, response)
        print(f"\n[SAVED] {out_path}")


if __name__ == "__main__":
    main()
