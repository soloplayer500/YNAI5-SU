#!/usr/bin/env python3
"""
RYN Telegram Tasks — Send commands and messages to VM via Telegram bot.
Wraps the Telegram Bot API for sending manual commands or alerts from RYN.

All commands go through @SoloClaude5_bot → ynai5-commander on VM.
Only CHAT_ID 8569520396 commands are accepted by commander.

Usage:
    python ryn/runtime/telegram_tasks.py --status
    python ryn/runtime/telegram_tasks.py --snapshot
    python ryn/runtime/telegram_tasks.py --logs
    python ryn/runtime/telegram_tasks.py --restart ynai5-dashboard
    python ryn/runtime/telegram_tasks.py --send "custom message"
    python ryn/runtime/telegram_tasks.py --test
"""
import os, sys, json, time
import urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
_env = Path.home() / "ynai5-agent" / ".env"
if not _env.exists():
    _env = Path(__file__).parent.parent.parent / ".env.local"

if _env.exists():
    for line in _env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_raw_chat = os.environ.get("TELEGRAM_CHAT_ID", "8569520396")
try:
    CHAT_ID = int(_raw_chat)
except (ValueError, TypeError):
    # .env.local has non-numeric value (e.g. bot username) — fall back to default
    CHAT_ID = 8569520396
MAX_WAIT  = 30  # seconds to wait for command response

SAFE_SERVICES = {"ynai5-dashboard", "ynai5-gemini", "nginx"}

# ── Telegram API helpers ──────────────────────────────────────────────────────

def tg_send(text: str) -> bool:
    """Send a message to the personal chat."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"SEND ERROR: {e}")
        return False

def tg_get_updates(offset: int = 0) -> list:
    params = {"allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    url = (f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?"
           + urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
            return json.loads(r.read()).get("result", [])
    except Exception:
        return []

def send_command_wait_reply(cmd: str, wait: int = MAX_WAIT) -> str:
    """
    Send a bot command and poll for the commander's reply.
    Returns the reply text or a timeout message.
    """
    if not BOT_TOKEN:
        return "ERROR: TELEGRAM_BOT_TOKEN not set"

    # Get current update offset before sending
    updates = tg_get_updates()
    offset  = (updates[-1]["update_id"] + 1) if updates else 0

    # Send the command
    print(f"→ Sending: {cmd}")
    tg_send(cmd)

    # Poll for reply
    deadline = time.time() + wait
    while time.time() < deadline:
        time.sleep(2)
        updates = tg_get_updates(offset)
        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message", {})
            if (msg.get("chat", {}).get("id") == CHAT_ID
                    and msg.get("from", {}).get("id") != CHAT_ID):
                # Message from bot (not from self)
                return msg.get("text", "")
    return f"(no reply within {wait}s)"

def ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_status():
    reply = send_command_wait_reply("/status")
    print(f"\n=== VM STATUS [{ts()}] ===\n{reply}")

def cmd_logs():
    reply = send_command_wait_reply("/logs")
    print(f"\n=== VM LOGS [{ts()}] ===\n{reply}")

def cmd_snapshot():
    print("Triggering /snapshot — this may take 10–15s...")
    reply = send_command_wait_reply("/snapshot", wait=30)
    print(f"\n=== SNAPSHOT [{ts()}] ===\n{reply}")

def cmd_restart(service: str):
    if service not in SAFE_SERVICES:
        print(f"ERROR: '{service}' not in safe list: {', '.join(sorted(SAFE_SERVICES))}")
        sys.exit(1)
    reply = send_command_wait_reply(f"/restart {service}")
    print(f"\n=== RESTART {service} [{ts()}] ===\n{reply}")

def cmd_send(text: str):
    ok = tg_send(text)
    print(f"Message {'sent' if ok else 'FAILED'}: {text[:80]}")

def cmd_test():
    print("=== Telegram Bot Health Test ===")
    if not BOT_TOKEN:
        print("FAIL: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    # Verify bot is reachable
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
            info = json.loads(r.read())
            bot = info.get("result", {})
            print(f"Bot: @{bot.get('username')} (id={bot.get('id')}) — REACHABLE ✓")
    except Exception as e:
        print(f"Bot UNREACHABLE: {e}")
        sys.exit(1)

    # Test /status command
    print("Sending /status command...")
    reply = send_command_wait_reply("/status", wait=20)
    if "YNAI5" in reply or "RAM" in reply:
        print(f"Commander responding ✓\n{reply[:300]}")
    else:
        print(f"Commander response unexpected: {reply[:200]}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    if "--status"   in args: cmd_status()
    elif "--logs"   in args: cmd_logs()
    elif "--snapshot" in args: cmd_snapshot()
    elif "--test"   in args: cmd_test()
    elif "--restart" in args:
        idx = args.index("--restart")
        svc = args[idx + 1] if idx + 1 < len(args) else None
        if not svc:
            print("Usage: --restart <service>")
            sys.exit(1)
        cmd_restart(svc)
    elif "--send" in args:
        idx = args.index("--send")
        msg = args[idx + 1] if idx + 1 < len(args) else None
        if not msg:
            print("Usage: --send 'message'")
            sys.exit(1)
        cmd_send(msg)
    else:
        print(f"Unknown args: {args}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
