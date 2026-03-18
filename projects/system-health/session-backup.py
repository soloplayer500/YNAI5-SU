"""
YNAI5 Session Backup Engine
============================
Called by Claude Code lifecycle hooks for crash recovery.

Usage:
    python session-backup.py --trigger=compact   (PreCompact hook)
    python session-backup.py --trigger=stop      (Stop hook)
    python session-backup.py --trigger=start     (SessionStart hook)

Reads optional JSON hook data from stdin.
Writes to projects/system-health/backup/
"""

import sys
import json
import argparse
import datetime
import pathlib

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKSPACE = pathlib.Path("C:/Users/shema/OneDrive/Desktop/YNAI5-SU")
BACKUP_DIR = WORKSPACE / "projects" / "system-health" / "backup"
BACKUP_MD  = BACKUP_DIR / "session-backup.md"
BACKUP_JSON = BACKUP_DIR / "session-state.json"
LOG_FILE   = BACKUP_DIR / "backup-log.txt"

TAG = "[YNAI5-Backup]"
BACKUP_MAX_AGE_HOURS = 48


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(message: str) -> None:
    """Append a timestamped line to the backup log."""
    entry = f"[{now_iso()}] {message}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"{TAG} WARNING: Could not write to log: {e}", file=sys.stderr)


def read_stdin_json() -> dict:
    """Read JSON from stdin if available; return empty dict on failure."""
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read().strip()
        if raw:
            return json.loads(raw)
    except (json.JSONDecodeError, Exception):
        pass
    return {}


def backup_age_hours() -> float | None:
    """Return age of existing backup in hours, or None if no backup exists."""
    if not BACKUP_JSON.exists():
        return None
    try:
        with BACKUP_JSON.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ts_str = data.get("timestamp")
        if not ts_str:
            return None
        ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.now() - ts
        return delta.total_seconds() / 3600
    except Exception:
        return None


# ── Core: Save ────────────────────────────────────────────────────────────────

def read_current_priorities() -> str:
    """Read current-priorities.md for context."""
    try:
        p = WORKSPACE / "context" / "current-priorities.md"
        if p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()
            # Return first 20 lines
            return "\n".join(lines[:20])
    except Exception:
        pass
    return "AI Social Media Automation Pipeline (default)"


def read_open_actions() -> str:
    """Read actions/ folder for open TODO items."""
    actions_dir = WORKSPACE / "actions"
    items = []
    try:
        if actions_dir.exists():
            for f in actions_dir.iterdir():
                if f.suffix in (".md", ".txt") and f.stat().st_size > 0:
                    lines = f.read_text(encoding="utf-8").splitlines()
                    items.append(f"[{f.name}] {lines[0][:80] if lines else '(empty)'}")
    except Exception:
        pass
    return "\n".join(items) if items else "No open action files found."


def read_session_state_context() -> str:
    """Read the explicit current-session-state.md if it exists."""
    try:
        p = WORKSPACE / "context" / "current-session-state.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def write_session_state(timestamp: str, trigger: str, resume_prompt: str) -> None:
    """Write context/current-session-state.md so CLAUDE.md can import it."""
    state_file = WORKSPACE / "context" / "current-session-state.md"
    try:
        content = (
            f"# Current Session State\n"
            f"_Auto-updated by session-backup.py at {timestamp} (trigger: {trigger})_\n\n"
            f"## Last Session Context\n\n"
            f"{resume_prompt}\n\n"
            f"## What To Do First\n"
            f"1. Check `actions/` for open TODO items\n"
            f"2. Check `context/current-priorities.md` for top priority\n"
            f"3. Resume from where the last session left off\n"
        )
        state_file.write_text(content, encoding="utf-8")
    except Exception as e:
        log(f"WARNING: Could not write current-session-state.md — {e}")


def save_backup(trigger: str, hook_data: dict) -> None:
    """Write session-backup.md and session-state.json."""
    ensure_backup_dir()
    timestamp = now_iso()

    # ── Gather rich context ───────────────────────────────────────────────────
    priorities = read_current_priorities()
    open_actions = read_open_actions()

    # ── Build resume prompt ───────────────────────────────────────────────────
    resume_prompt = (
        f"Session backup from {timestamp} (trigger: {trigger}).\n"
        f"Workspace: C:/Users/shema/OneDrive/Desktop/YNAI5-SU\n\n"
        f"--- CURRENT PRIORITIES ---\n{priorities}\n\n"
        f"--- OPEN ACTIONS ---\n{open_actions}\n\n"
        f"Run /health-check to verify system. Continue from context/current-session-state.md."
    )

    # ── Write persistent state file ───────────────────────────────────────────
    write_session_state(timestamp, trigger, resume_prompt)

    # ── Build markdown backup ─────────────────────────────────────────────────
    md_lines = [
        "# YNAI5 Session Backup",
        f"",
        f"**Saved:** {timestamp}  ",
        f"**Trigger:** `{trigger}`  ",
        f"**Workspace:** `C:/Users/shema/OneDrive/Desktop/YNAI5-SU`",
        f"",
        "---",
        "",
        "## Resume Prompt",
        "",
        "Copy-paste this into Claude Code to restore context:",
        "",
        "```",
        resume_prompt,
        "```",
        "",
        "---",
        "",
        "## Session State",
        "",
        f"- **Backup trigger:** `{trigger}`",
        f"- **Timestamp:** {timestamp}",
        f"- **Top priority:** AI Social Media Automation Pipeline",
        f"- **Key files:** memory/MEMORY.md, actions/, context/current-priorities.md",
        "",
    ]

    # Attach any hook data Claude Code passed via stdin
    if hook_data:
        md_lines += [
            "## Hook Data (from Claude Code)",
            "",
            "```json",
            json.dumps(hook_data, indent=2),
            "```",
            "",
        ]

    md_lines += [
        "---",
        "",
        "## Quick Recovery Steps",
        "",
        "1. Open Claude Code in `C:/Users/shema/OneDrive/Desktop/YNAI5-SU`",
        "2. Paste the Resume Prompt above",
        "3. Run `/health-check` to verify the workspace",
        "4. Check `actions/` for open TODO items",
        "5. Resume work from `memory/MEMORY.md` session index",
        "",
    ]

    md_content = "\n".join(md_lines)

    # ── Write markdown ────────────────────────────────────────────────────────
    BACKUP_MD.write_text(md_content, encoding="utf-8")

    # ── Write JSON state ──────────────────────────────────────────────────────
    state = {
        "timestamp": timestamp,
        "trigger": trigger,
        "workspace": str(WORKSPACE),
        "top_priority": "AI Social Media Automation Pipeline",
        "resume_prompt": resume_prompt,
        "hook_data": hook_data,
    }
    BACKUP_JSON.write_text(json.dumps(state, indent=2), encoding="utf-8")

    log(f"Backup saved (trigger={trigger}) → {BACKUP_MD.name}, {BACKUP_JSON.name}")
    print(f"{TAG} Saved session state (trigger={trigger})")
    print(f"{TAG} Backup written to: {BACKUP_DIR}")


# ── Core: Load ────────────────────────────────────────────────────────────────

def load_backup() -> None:
    """On session start: surface backup summary if recent enough."""
    ensure_backup_dir()

    age = backup_age_hours()

    if age is None:
        print(f"{TAG} No previous backup found. Starting fresh session.")
        log("SessionStart: no backup found.")
        return

    if age > BACKUP_MAX_AGE_HOURS:
        print(f"{TAG} Backup found but is {age:.1f}h old (> {BACKUP_MAX_AGE_HOURS}h). Skipping.")
        log(f"SessionStart: backup is {age:.1f}h old — skipped (too old).")
        return

    # ── Load and surface the backup ───────────────────────────────────────────
    try:
        with BACKUP_JSON.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        print(f"{TAG} WARNING: Could not read backup JSON: {e}", file=sys.stderr)
        log(f"SessionStart: failed to read backup JSON — {e}")
        return

    trigger   = state.get("trigger", "unknown")
    timestamp = state.get("timestamp", "unknown")
    resume    = state.get("resume_prompt", "")

    print()
    print("=" * 60)
    print(f"{TAG} CRASH RECOVERY — Backup detected ({age:.1f}h ago)")
    print("=" * 60)
    print(f"  Saved:   {timestamp}")
    print(f"  Trigger: {trigger}")
    print()
    print("  Resume Prompt (copy-paste to restore context):")
    print("  " + "-" * 54)
    for line in resume.splitlines():
        print(f"  {line}")
    print("  " + "-" * 54)
    print()
    print(f"  Full backup: {BACKUP_MD}")
    print("=" * 60)
    print()

    log(f"SessionStart: surfaced backup from {timestamp} (trigger={trigger}, age={age:.1f}h).")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="YNAI5 Session Backup Engine")
    parser.add_argument(
        "--trigger",
        required=True,
        choices=["compact", "stop", "start"],
        help="Hook trigger: compact | stop | start",
    )
    args = parser.parse_args()

    hook_data = read_stdin_json()

    if args.trigger in ("compact", "stop"):
        save_backup(trigger=args.trigger, hook_data=hook_data)
    elif args.trigger == "start":
        load_backup()


if __name__ == "__main__":
    main()
