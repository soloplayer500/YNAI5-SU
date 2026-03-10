#!/usr/bin/env python3
"""
Get Telegram Chat ID — YNAI5-SU Helper
Run this ONCE to find your trading group's Chat ID.

Steps:
1. Add bot to your Telegram trading group
2. Send any message in that group (e.g. "hello")
3. Run this script: python get_chat_id.py
4. Copy the chat_id that appears
5. Add it to .env.local as: TELEGRAM_CHAT_ID=<the_id>

No dependencies — stdlib only.
"""

import json
import urllib.request
from pathlib import Path


def load_env() -> dict:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env.local"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def main():
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")

    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env.local")
        print("        Add it first, then re-run this script.")
        return

    print(f"Using token: {token[:20]}...")
    print("Fetching recent updates from Telegram...\n")

    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        req = urllib.request.Request(url, headers={"User-Agent": "YNAI5/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        return

    if not data.get("ok"):
        print(f"[ERROR] Telegram API error: {data}")
        return

    updates = data.get("result", [])

    if not updates:
        print("No updates found.")
        print("Make sure you:")
        print("  1. Added the bot to your trading group")
        print("  2. Sent at least one message in that group after adding the bot")
        print("  3. Then re-run this script")
        return

    print("Found chats:\n")
    seen = set()
    for update in updates:
        msg = update.get("message") or update.get("channel_post", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "unknown")
        chat_title = chat.get("title") or chat.get("username") or chat.get("first_name", "")

        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            print(f"  Chat ID : {chat_id}")
            print(f"  Type    : {chat_type}")
            print(f"  Name    : {chat_title}")
            print()

    print("─" * 40)
    print("Copy the Chat ID of your trading group.")
    print("Then add to .env.local:")
    print("  TELEGRAM_CHAT_ID=<paste_the_id_here>")
    print()
    print("For groups, the ID is usually a negative number like -1001234567890")


if __name__ == "__main__":
    main()
