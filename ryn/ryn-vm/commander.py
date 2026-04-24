#!/usr/bin/env python3
"""
YNAI5 Telegram Commander v2
- Polls Telegram for commands, responds safely
- /snapshot writes local state + delivers via Telegram
- All shell calls have 10s timeout
- Outputs trimmed to safe Telegram lengths
"""
import os, json, time, subprocess
import urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Load .env
_env = Path.home() / "ynai5-agent" / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

BOT_TOKEN        = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID          = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))
ALLOWED_USER_ID  = CHAT_ID
AGENT_DIR        = Path.home() / "ynai5-agent"
AI_CORE_DIR      = Path.home() / "YNAI5_AI_CORE"
CMD_LOG          = AGENT_DIR / "command.log"
HB_LOG           = AGENT_DIR / "heartbeat.log"
OFFSET_FILE      = AGENT_DIR / ".cmd_offset"
SAFE_RESTART     = {"ynai5-dashboard", "ynai5-gemini", "nginx"}
MAX_MSG          = 3900   # Telegram limit 4096; keep margin

# ── Telegram helpers ──────────────────────────────────────────────────────────

def tg_send(chat_id, text):
    """Send message, trim to MAX_MSG, never crash."""
    if len(text) > MAX_MSG:
        text = "...(trimmed)\n" + text[-(MAX_MSG - 20):]
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:
        pass

def get_updates(offset):
    params = {"allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    url = ("https://api.telegram.org/bot" + BOT_TOKEN
           + "/getUpdates?" + urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
            return json.loads(r.read()).get("result", [])
    except Exception:
        return []

def load_offset():
    try:
        return int(OFFSET_FILE.read_text().strip()) if OFFSET_FILE.exists() else 0
    except Exception:
        return 0

def save_offset(o):
    try:
        OFFSET_FILE.write_text(str(o))
    except Exception:
        pass

def log_cmd(uid, cmd, resp):
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with open(CMD_LOG, "a") as f:
            f.write(f"[{ts}] user={uid} cmd={cmd!r} resp={resp[:120]!r}\n")
    except Exception:
        pass

# ── Shell helper (10s timeout, never hangs) ───────────────────────────────────

def sh(args, timeout=10):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"TIMEOUT ({timeout}s)"
    except Exception as e:
        return str(e)

# ── System state builder ──────────────────────────────────────────────────────

def build_system_state():
    """Returns (summary_str, state_dict) with live metrics."""
    ts = datetime.now(timezone.utc).isoformat()
    ts_human = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    ram_raw = sh(["free", "-m"])
    ram_avail, ram_used = "?", "?"
    for line in ram_raw.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()
            ram_used, ram_avail = parts[2], parts[6]

    disk_raw = sh(["df", "-h", "/"]).splitlines()
    disk_used = disk_raw[-1].split()[4] if disk_raw else "?"
    disk_free = disk_raw[-1].split()[3] if disk_raw else "?"
    load = sh(["uptime"]).split("load average:")[-1].strip()

    svc_list = ["ynai5-dashboard", "ynai5-gemini", "ynai5-claude",
                "nginx", "ynai5-heartbeat", "ynai5-commander"]
    svcs = {s: sh(["systemctl", "is-active", s]) for s in svc_list}

    last_hb = "N/A"
    if HB_LOG.exists():
        lines = HB_LOG.read_text().splitlines()
        if lines:
            last_hb = lines[-1]

    state = {
        "timestamp": ts,
        "disk_used_pct": disk_used,
        "disk_free": disk_free,
        "ram_used_mb": ram_used,
        "ram_avail_mb": ram_avail,
        "load": load,
        "services": svcs,
        "last_heartbeat": last_hb,
    }

    svc_lines = "\n".join(
        f"  {s}: {'OK' if v == 'active' else 'DOWN'}"
        for s, v in svcs.items()
    )
    summary = (
        f"YNAI5 STATUS [{ts_human}]\n"
        f"RAM avail: {ram_avail}MB | Disk: {disk_used} ({disk_free} free) | Load: {load}\n\n"
        f"SERVICES:\n{svc_lines}\n\n"
        f"LAST HB:\n{last_hb}"
    )
    return summary, state

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_status():
    summary, _ = build_system_state()
    return summary

def cmd_logs():
    if not HB_LOG.exists():
        return "heartbeat.log not found"
    lines = HB_LOG.read_text().splitlines()
    if not lines:
        return "heartbeat.log is empty"
    return "LAST 20 LINES:\n" + "\n".join(lines[-20:])

def cmd_restart(svc):
    if not svc:
        return "Usage: /restart <service>\nSafe: " + ", ".join(sorted(SAFE_RESTART))
    if svc not in SAFE_RESTART:
        return f"DENIED: '{svc}' not in safe list.\nSafe: {', '.join(sorted(SAFE_RESTART))}"
    try:
        subprocess.run(["sudo", "systemctl", "restart", svc],
                       timeout=15, check=True, capture_output=True)
        time.sleep(3)
        st = sh(["systemctl", "is-active", svc])
        return f"Restarted {svc}\nStatus: {st}"
    except subprocess.TimeoutExpired:
        return f"Restart timed out for {svc}"
    except Exception as e:
        return f"Restart failed for {svc}: {e}"

def cmd_snapshot():
    """Write state files locally and deliver summary via Telegram."""
    ts_commit = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary, state = build_system_state()

    # 1. Write JSON state locally
    snap_file = AGENT_DIR / "snapshot.json"
    try:
        snap_file.write_text(json.dumps(state, indent=2))
    except Exception as e:
        return f"SNAPSHOT FAILED (write): {e}"

    # 2. Write .md files + local git commit in AI_CORE if available
    git_committed = False
    if AI_CORE_DIR.exists() and (AI_CORE_DIR / ".git").exists():
        brain_dir = AI_CORE_DIR / "ryn" / "brain"
        try:
            brain_dir.mkdir(parents=True, exist_ok=True)
            (brain_dir / "system_summary.md").write_text(
                f"# YNAI5 System Summary\n_Snapshot: {ts_commit}_\n\n"
                f"```\n{summary}\n```\n"
            )
            report_file = brain_dir / "last_report.md"
            existing = report_file.read_text() if report_file.exists() else ""
            new_entry = f"## {ts_commit} — SNAPSHOT\n\n{summary}\n\n---\n\n"
            report_file.write_text(new_entry + existing)

            subprocess.run(
                ["git", "-C", str(AI_CORE_DIR), "add",
                 "ryn/brain/system_summary.md", "ryn/brain/last_report.md"],
                timeout=10, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(AI_CORE_DIR), "commit",
                 "-m", f"ryn-snapshot: {ts_commit}", "--allow-empty"],
                timeout=10, capture_output=True
            )
            git_committed = True
        except Exception:
            git_committed = False

    git_note = (
        "Committed to ~/YNAI5_AI_CORE (sync on next Claude Code push from RYN)"
        if git_committed
        else "Written to ~/ynai5-agent/snapshot.json"
    )
    return f"SNAPSHOT [{ts_commit}]\n{git_note}\n\n{summary}"

def handle(text):
    t = text.strip()
    if t == "/status":
        return cmd_status()
    if t == "/logs":
        return cmd_logs()
    if t == "/snapshot":
        return cmd_snapshot()
    if t.startswith("/restart"):
        return cmd_restart(t[8:].strip())
    if t.startswith("/"):
        return "Commands: /status /logs /restart <svc> /snapshot"
    return None   # not a command — ignore silently

# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing in .env")
    offset = load_offset()
    while True:
        try:
            updates = get_updates(offset)
            for upd in updates:
                offset = upd["update_id"] + 1
                save_offset(offset)
                msg = upd.get("message", {})
                if not msg:
                    continue
                uid  = msg.get("from", {}).get("id")
                cid  = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if uid != ALLOWED_USER_ID:
                    continue   # silently reject unknown users
                if not text:
                    continue
                resp = handle(text)
                if resp:
                    tg_send(cid, resp)
                    log_cmd(uid, text, resp)
        except Exception:
            pass
        time.sleep(5)

if __name__ == "__main__":
    main()
