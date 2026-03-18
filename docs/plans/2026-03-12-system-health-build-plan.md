# YNAI5 System Health + Crash Recovery — Build Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a crash-resilient, auto-recovering YNAI5 workspace with session backup hooks, system health monitoring, Docker on-demand skill, and Windows auto-start — all orchestrated via Method C (lightweight hooks + cloud fallback, no 24/7 Docker daemon).

**Architecture:** Claude Code hooks (PreCompact/Stop/SessionStart) save and restore session state automatically. A psutil-based health agent runs diagnostics on demand and via GitHub Actions. Docker is started only when explicitly requested via `/docker` skill. A single startup.bat automates everything on Windows boot.

**Tech Stack:** Python 3, psutil, requests, Claude Code hooks (JSON config), Windows Task Scheduler / Startup folder, GitHub Actions, Telegram Bot API, Anthropic API (claude-haiku-4-5)

---

## Task 0: Add Free MCPs (fetch + git)

**Files:**
- Modify: `C:/Users/shema/.claude/settings.json` (via CLI commands only)

**Step 1: Add fetch MCP**

```bash
claude mcp add fetch --scope user -- npx -y @modelcontextprotocol/server-fetch
```
Expected: "MCP server 'fetch' added successfully"

**Step 2: Add git MCP**

```bash
pip install mcp-server-git -q
claude mcp add git --scope user -- uvx mcp-server-git
```
Expected: "MCP server 'git' added successfully"

**Step 3: Verify both are listed**

```bash
claude mcp list
```
Expected output includes: `fetch`, `git` in the list

**Step 4: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add -A
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat: add fetch + git MCPs (free, no API key)"
```

---

## Task 1: Install psutil Dependency

**Step 1: Install required Python packages**

```bash
pip install psutil requests -q
```
Expected: Successfully installed (or already satisfied)

**Step 2: Verify**

```bash
python -c "import psutil; print('psutil OK:', psutil.__version__)"
python -c "import requests; print('requests OK:', requests.__version__)"
```
Expected: both print version numbers

---

## Task 2: Build session-backup.py (Core Crash Recovery Engine)

**Files:**
- Create: `projects/system-health/session-backup.py`

**Step 1: Create the backup script**

```python
#!/usr/bin/env python3
"""
YNAI5 Session Backup Engine
============================
Called by Claude Code hooks: PreCompact, Stop, SessionStart
Saves/loads session state to survive crashes and context compaction.

Usage:
    python session-backup.py --trigger=compact   # PreCompact hook
    python session-backup.py --trigger=stop      # Stop hook
    python session-backup.py --trigger=start     # SessionStart hook
"""

import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent  # YNAI5-SU root
BACKUP_DIR = Path(__file__).parent / "backup"
BACKUP_FILE = BACKUP_DIR / "session-backup.md"
BACKUP_JSON = BACKUP_DIR / "session-state.json"
LOG_FILE = BACKUP_DIR / "backup-log.txt"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    """Append to backup log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def read_stdin_context() -> dict:
    """Read JSON context passed by Claude Code via stdin (if any)."""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read(4096)
            if raw.strip():
                return json.loads(raw)
    except Exception:
        pass
    return {}


def save_backup(trigger: str, ctx: dict):
    """Save current session state to backup file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Build state dict
    state = {
        "timestamp": ts,
        "trigger": trigger,
        "session_id": ctx.get("session_id", "unknown"),
        "workspace": str(WORKSPACE),
    }

    # Save JSON state
    with open(BACKUP_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # Build human-readable backup markdown
    md = f"""# YNAI5 Session Backup
_Saved: {ts} | Trigger: {trigger}_

---

## Resume Prompt
Copy-paste this at the start of your next session to restore context:

```
I'm Shami (Solo). We were working in YNAI5-SU workspace.
Last backup: {ts} (trigger: {trigger})
Workspace: C:/Users/shema/OneDrive/Desktop/YNAI5-SU
Top priority: AI Social Media Automation Pipeline
Check: projects/system-health/backup/session-backup.md for full state.
What were we working on? Check memory/MEMORY.md and actions/ folder.
```

## Last Known State
- Backup time: {ts}
- Trigger: {trigger}
- Session ID: {state.get('session_id', 'unknown')}

## Quick Links
- [MEMORY.md](../../memory/MEMORY.md)
- [current-priorities.md](../../context/current-priorities.md)
- [actions/](../../actions/)
- [projects/README.md](../../projects/README.md)

## What to Check on Resume
1. Look at `actions/` folder for open TODOs
2. Check `sessions/` for last session summary
3. Check `projects/ralph-automation/sessions/` for agent outputs
4. Run `/health-check` to verify system state
"""

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    log(f"Backup saved (trigger={trigger})")
    print(f"[YNAI5-Backup] Saved session state → {BACKUP_FILE}")


def load_backup():
    """Print backup reminder to stdout (injected as SessionStart context)."""
    if not BACKUP_FILE.exists():
        print("[YNAI5-Backup] No previous backup found — fresh session.")
        return

    # Check if backup is recent (within 48h)
    mtime = BACKUP_FILE.stat().st_mtime
    age_hours = (datetime.now().timestamp() - mtime) / 3600

    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if age_hours < 48:
        print(f"[YNAI5-Backup] Found recent backup ({age_hours:.1f}h ago). Surfacing context...")
        # Print a compact summary to inject into session context
        lines = content.split("\n")
        summary_lines = [l for l in lines if l.startswith("- ") or l.startswith("##")][:20]
        print("\n".join(summary_lines))
    else:
        print(f"[YNAI5-Backup] Old backup found ({age_hours:.0f}h ago) — skipping auto-inject.")

    log(f"SessionStart: loaded backup (age={age_hours:.1f}h)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", choices=["compact", "stop", "start"], required=True)
    args = parser.parse_args()

    ctx = read_stdin_context()

    if args.trigger in ("compact", "stop"):
        save_backup(args.trigger, ctx)
    elif args.trigger == "start":
        load_backup()


if __name__ == "__main__":
    main()
```

**Step 2: Smoke test — save**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/session-backup.py" --trigger=compact
```
Expected: `[YNAI5-Backup] Saved session state → ...session-backup.md`

**Step 3: Smoke test — load**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/session-backup.py" --trigger=start
```
Expected: prints backup summary lines

**Step 4: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add projects/system-health/session-backup.py
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat(system-health): session backup engine for crash recovery"
```

---

## Task 3: Configure Claude Code Hooks

**Files:**
- Modify: `C:/Users/shema/.claude/settings.json`

**Step 1: Read current settings.json**

```bash
cat "C:/Users/shema/.claude/settings.json"
```

**Step 2: Add hooks block to settings.json**

The hooks key must be added at the top level of the JSON. Use Python to safely merge:

```python
import json
from pathlib import Path

settings_path = Path(r"C:/Users/shema/.claude/settings.json")
backup_script = r"C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/session-backup.py"

with open(settings_path, "r") as f:
    settings = json.load(f)

settings["hooks"] = {
    "PreCompact": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f'python "{backup_script}" --trigger=compact'
                }
            ]
        }
    ],
    "Stop": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f'python "{backup_script}" --trigger=stop'
                }
            ]
        }
    ],
    "SessionStart": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f'python "{backup_script}" --trigger=start'
                }
            ]
        }
    ]
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("Hooks written to settings.json")
print(json.dumps(settings.get("hooks"), indent=2))
```

Save the above as a temp script and run it:
```bash
python -c "<above code as one-liner or temp file>"
```

**Step 3: Verify hooks appear in settings**

```bash
python -c "import json; s=json.load(open(r'C:/Users/shema/.claude/settings.json')); print(list(s.get('hooks',{}).keys()))"
```
Expected: `['PreCompact', 'Stop', 'SessionStart']`

**Step 4: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add -A
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat(system-health): Claude Code crash recovery hooks configured"
```

---

## Task 4: Build health-check.py (System Diagnostics Engine)

**Files:**
- Create: `projects/system-health/health-check.py`

**Step 1: Create the script**

```python
#!/usr/bin/env python3
"""
YNAI5 System Health Check
==========================
Runs parallel diagnostics and outputs a Telegram-ready report.
Called by /health-check skill.

Usage:
    python health-check.py             # full check, print + save
    python health-check.py --telegram  # also send to Telegram
    python health-check.py --quick     # RAM + disk only
"""

import os
import sys
import json
import time
import socket
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Run: pip install psutil")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None

# ─── Config ───────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent.parent
LOGS_DIR = Path(__file__).parent / "logs"
ENV_FILE = WORKSPACE / ".env.local"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load .env.local
env_vars = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip().strip('"').strip("'")

TELEGRAM_TOKEN = env_vars.get("TELEGRAM_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
TELEGRAM_CHAT_ID = env_vars.get("TELEGRAM_CHAT_ID", os.environ.get("TELEGRAM_CHAT_ID", "8569520396"))


# ─── Check Functions (run in parallel) ────────────────────────────────────────

def check_ram() -> dict:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    top_procs = sorted(psutil.process_iter(['pid', 'name', 'memory_percent']),
                       key=lambda p: p.info.get('memory_percent', 0) or 0,
                       reverse=True)[:5]
    top = [(p.info['name'], round(p.info.get('memory_percent', 0), 1)) for p in top_procs]
    return {
        "total_gb": round(mem.total / 1e9, 1),
        "used_gb": round(mem.used / 1e9, 1),
        "available_gb": round(mem.available / 1e9, 1),
        "percent": mem.percent,
        "swap_percent": swap.percent,
        "top_procs": top,
        "status": "⚠️ HIGH" if mem.percent > 80 else "✅ OK"
    }


def check_cpu() -> dict:
    cpu = psutil.cpu_percent(interval=1)
    freq = psutil.cpu_freq()
    return {
        "percent": cpu,
        "freq_mhz": round(freq.current) if freq else "N/A",
        "cores": psutil.cpu_count(),
        "status": "⚠️ HIGH" if cpu > 85 else "✅ OK"
    }


def check_disk() -> dict:
    disk = psutil.disk_usage("C:/")
    return {
        "total_gb": round(disk.total / 1e9, 1),
        "used_gb": round(disk.used / 1e9, 1),
        "free_gb": round(disk.free / 1e9, 1),
        "percent": disk.percent,
        "status": "⚠️ LOW" if disk.percent > 85 else "✅ OK"
    }


def check_internet() -> dict:
    targets = [("1.1.1.1", "Cloudflare"), ("8.8.8.8", "Google")]
    results = []
    for ip, name in targets:
        try:
            start = time.time()
            sock = socket.create_connection((ip, 53), timeout=3)
            sock.close()
            ms = round((time.time() - start) * 1000)
            results.append(f"{name}: {ms}ms")
        except Exception:
            results.append(f"{name}: ❌ unreachable")
    return {
        "checks": results,
        "status": "✅ OK" if all("unreachable" not in r for r in results) else "⚠️ ISSUES"
    }


def check_docker() -> dict:
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return {"running": True, "containers": len(lines) - 1, "status": "✅ Running"}
        else:
            return {"running": False, "status": "⚪ Not running (OK — on-demand only)"}
    except Exception as e:
        return {"running": False, "status": f"⚪ Not running ({str(e)[:40)}}"}


def check_python_procs() -> dict:
    procs = [p for p in psutil.process_iter(['pid', 'name', 'cmdline'])
             if 'python' in (p.info.get('name') or '').lower()]
    proc_list = []
    for p in procs:
        try:
            cmd = " ".join(p.info.get('cmdline') or [])[:60]
            proc_list.append(f"PID {p.info['pid']}: {cmd}")
        except Exception:
            pass
    return {
        "count": len(proc_list),
        "procs": proc_list[:5],
        "status": "⚠️ MANY" if len(proc_list) > 6 else "✅ OK"
    }


def check_startup_apps() -> dict:
    """Count startup entries in common Windows startup locations."""
    startup_count = 0
    try:
        result = subprocess.run(
            ["reg", "query", r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            entries = [l for l in result.stdout.splitlines() if l.strip() and "REG_" in l]
            startup_count = len(entries)
    except Exception:
        pass
    return {
        "startup_count": startup_count,
        "status": "✅ OK" if startup_count < 5 else "⚠️ MANY"
    }


# ─── Report Builder ────────────────────────────────────────────────────────────

def build_report(results: dict) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M AST")
    r = results

    lines = [
        f"🖥️ *YNAI5 System Health* — {ts}",
        "",
        f"💾 RAM: {r['ram']['used_gb']}GB / {r['ram']['total_gb']}GB ({r['ram']['percent']}%) {r['ram']['status']}",
        f"   Swap: {r['ram']['swap_percent']}% | Avail: {r['ram']['available_gb']}GB",
        f"   Top: {', '.join(f\"{n}({p}%)\" for n, p in r['ram']['top_procs'][:3])}",
        "",
        f"⚡ CPU: {r['cpu']['percent']}% @ {r['cpu']['freq_mhz']}MHz ({r['cpu']['cores']} cores) {r['cpu']['status']}",
        "",
        f"💿 Disk C: {r['disk']['free_gb']}GB free / {r['disk']['total_gb']}GB ({r['disk']['percent']}%) {r['disk']['status']}",
        "",
        f"🌐 Internet: {' | '.join(r['internet']['checks'])} {r['internet']['status']}",
        "",
        f"🐋 Docker: {r['docker']['status']}",
        f"🐍 Python procs: {r['python']['count']} running {r['python']['status']}",
        f"🚀 Startup apps: {r['startup']['startup_count']} entries {r['startup']['status']}",
        "",
    ]

    # Recommendations
    recs = []
    if r['ram']['percent'] > 80:
        recs.append("⚠️ RAM high — close Chrome tabs, restart Claude Code")
    if r['disk']['percent'] > 85:
        recs.append("⚠️ Disk low — run cleanup (temp files, Downloads)")
    if r['ram']['swap_percent'] > 50:
        recs.append("⚠️ Swap heavy — RAM pressure causing slowdowns/crashes")
    if r['python']['count'] > 6:
        recs.append("⚠️ Many Python procs — check for runaway scripts")

    if recs:
        lines.append("📋 *Recommendations:*")
        lines.extend(recs)
    else:
        lines.append("✅ System looks healthy")

    return "\n".join(lines)


def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not requests:
        print("[Telegram] Skipped — no token or requests not installed")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        if resp.status_code == 200:
            print("[Telegram] Health report sent ✅")
        else:
            print(f"[Telegram] Failed: {resp.status_code}")
    except Exception as e:
        print(f"[Telegram] Error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--telegram", action="store_true", help="Send to Telegram")
    parser.add_argument("--quick", action="store_true", help="RAM + disk only")
    args = parser.parse_args()

    print("🔍 Running YNAI5 system health check...")

    checks = {
        "ram": check_ram,
        "cpu": check_cpu,
        "disk": check_disk,
        "internet": check_internet,
        "docker": check_docker,
        "python": check_python_procs,
        "startup": check_startup_apps,
    }

    if args.quick:
        checks = {"ram": check_ram, "disk": check_disk, "internet": check_internet}

    results = {}
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        future_map = {executor.submit(fn): name for name, fn in checks.items()}
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {"status": f"❌ Error: {e}"}

    report = build_report(results)
    print("\n" + report)

    # Save to log
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-health.md"
    log_file.write_text(f"```\n{report}\n```\n", encoding="utf-8")
    print(f"\n[Saved] {log_file}")

    if args.telegram:
        send_telegram(report)


if __name__ == "__main__":
    main()
```

**Step 2: Fix the f-string syntax issue (line with `}}`) — run as-is after writing, Python will raise syntax error if any. If so, fix the `check_docker` return line:**

```python
# Change this line in check_docker:
return {"running": False, "status": f"⚪ Not running ({str(e)[:40]})"}
```

**Step 3: Smoke test**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/health-check.py"
```
Expected: Prints RAM/CPU/disk/internet/docker report, saves to logs/

**Step 4: Test Telegram send**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/health-check.py" --telegram
```
Expected: Report printed + `[Telegram] Health report sent ✅`

**Step 5: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add projects/system-health/health-check.py
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat(system-health): parallel health check engine with Telegram output"
```

---

## Task 5: Create /health-check Skill

**Files:**
- Create: `.claude/skills/health-check/SKILL.md`

**Step 1: Create skill**

```markdown
---
name: health-check
description: Run YNAI5 system health diagnostics — RAM, CPU, disk, internet, Docker, Python procs. Sends Telegram report. Use when system feels slow, before heavy tasks, or any time.
triggers:
  - /health-check
  - /health
---

# Health Check Skill

## What I Do
Run parallel system diagnostics and give you a full health report.

## Usage
- `/health-check` — full report (print + save log)
- `/health-check --telegram` — full report + send to Telegram
- `/health-check --quick` — fast check (RAM + disk + internet only)

## Steps

1. Run the health check script:
```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/health-check.py" [args]
```

2. Read the output and summarize key findings

3. If RAM > 80% or swap > 50%, immediately give optimization actions:
   - "Close these apps to free RAM: [list top memory hogs]"
   - "Run this to kill runaway procs: taskkill /F /PID [pid]"

4. If --telegram flag used or user says "send to telegram", add --telegram

5. Save findings are auto-saved to `projects/system-health/logs/`

## Output Format
Always present results as:
- 🔴 CRITICAL items first (if any)
- ⚠️ Warnings second
- ✅ All-clear last
- Actionable recommendations always included
```

**Step 2: Verify skill is recognized**

```bash
ls "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/.claude/skills/"
```
Expected: `health-check` folder in the list

**Step 3: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add .claude/skills/health-check/
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat: /health-check skill — system diagnostics on demand"
```

---

## Task 6: Build Docker On-Demand Skill

**Files:**
- Create: `projects/system-health/docker-manager.py`
- Create: `.claude/skills/docker/SKILL.md`

**Step 1: Create docker-manager.py**

```python
#!/usr/bin/env python3
"""
YNAI5 Docker Manager
=====================
Ensures Docker Desktop is running before executing Docker commands.
Called by /docker skill.

Usage:
    python docker-manager.py status
    python docker-manager.py start
    python docker-manager.py ps
    python docker-manager.py "run hello-world"
"""

import sys
import subprocess
import time
import os
from pathlib import Path

DOCKER_DESKTOP_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
MAX_WAIT = 60  # seconds to wait for Docker to be ready


def is_docker_running() -> bool:
    """Check if Docker daemon is accessible."""
    result = subprocess.run(
        ["docker", "ps"],
        capture_output=True, text=True, timeout=5
    )
    return result.returncode == 0


def start_docker() -> bool:
    """Start Docker Desktop and wait for daemon to be ready."""
    if is_docker_running():
        return True

    print("[Docker] Starting Docker Desktop...")
    if not Path(DOCKER_DESKTOP_PATH).exists():
        print(f"[Docker] ERROR: Docker Desktop not found at {DOCKER_DESKTOP_PATH}")
        return False

    os.startfile(DOCKER_DESKTOP_PATH)

    print(f"[Docker] Waiting for daemon (up to {MAX_WAIT}s)...")
    for i in range(MAX_WAIT):
        time.sleep(1)
        if is_docker_running():
            print(f"[Docker] ✅ Ready in {i+1}s")
            return True
        if i % 10 == 9:
            print(f"[Docker] Still waiting... ({i+1}s)")

    print("[Docker] ❌ Timed out waiting for Docker")
    return False


def run_docker_command(cmd: str) -> int:
    """Ensure Docker is running, then execute a docker command."""
    if not is_docker_running():
        if not start_docker():
            return 1

    full_cmd = ["docker"] + cmd.split()
    print(f"[Docker] Running: docker {cmd}")
    result = subprocess.run(full_cmd)
    return result.returncode


def main():
    if len(sys.argv) < 2:
        print("Usage: python docker-manager.py <command>")
        print("  status  — check if Docker is running")
        print("  start   — start Docker Desktop")
        print("  <cmd>   — run a docker command (auto-starts if needed)")
        sys.exit(1)

    action = sys.argv[1]

    if action == "status":
        running = is_docker_running()
        print(f"[Docker] {'✅ Running' if running else '⚪ Not running'}")

    elif action == "start":
        success = start_docker()
        sys.exit(0 if success else 1)

    else:
        # Treat everything as a docker subcommand
        cmd = " ".join(sys.argv[1:])
        rc = run_docker_command(cmd)
        sys.exit(rc)


if __name__ == "__main__":
    main()
```

**Step 2: Create /docker skill**

```markdown
---
name: docker
description: Run Docker commands on demand. Automatically starts Docker Desktop if not running. No manual startup needed.
triggers:
  - /docker
---

# Docker On-Demand Skill

## What I Do
Run Docker commands — auto-starting Docker Desktop if it's closed.
No need to manually open Docker before asking me.

## Usage
- `/docker status` — is Docker running?
- `/docker start` — start Docker Desktop
- `/docker ps` — list running containers
- `/docker [any docker command]` — runs it (starts Docker first if needed)

## Steps

1. Parse the user's request to extract the Docker command they want

2. Run via docker-manager.py:
```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/docker-manager.py" [command]
```

3. If Docker needs to start: inform user "Starting Docker Desktop, this takes ~30s..."

4. After command completes: show output and ask if they need anything else with Docker

## Important Notes
- Docker Desktop takes 30-60s to start — be patient, tell user what's happening
- On 8GB RAM: avoid running many containers simultaneously
- Docker MCP Toolkit: once Docker is running, all 100+ MCP servers are available via the Docker Desktop extension
```

**Step 3: Smoke test**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/docker-manager.py" status
```
Expected: `[Docker] ⚪ Not running` or `[Docker] ✅ Running`

**Step 4: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add projects/system-health/docker-manager.py .claude/skills/docker/
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat: /docker on-demand skill + docker-manager.py (auto-starts Docker Desktop)"
```

---

## Task 7: Build Windows Startup Automation

**Files:**
- Create: `projects/system-health/startup.bat`
- Create: `projects/system-health/install-startup.py` (installs the shortcut)

**Step 1: Create startup.bat**

```bat
@echo off
REM ═══════════════════════════════════════════════
REM YNAI5 Startup Automation
REM Runs automatically when Windows starts
REM ═══════════════════════════════════════════════

SET WORKSPACE=C:\Users\shema\OneDrive\Desktop\YNAI5-SU
SET LOG=%WORKSPACE%\projects\system-health\logs\startup-log.txt

echo [%DATE% %TIME%] YNAI5 Startup triggered >> "%LOG%"
echo Starting YNAI5 automation...

REM ─── Wait for desktop to fully load ───────────────
timeout /t 15 /nobreak >nul

REM ─── Quick health snapshot ────────────────────────
echo [%DATE% %TIME%] Running health snapshot... >> "%LOG%"
python "%WORKSPACE%\projects\system-health\health-check.py" --quick >> "%LOG%" 2>&1

REM ─── Start Crypto Price Alert Monitor ─────────────
echo [%DATE% %TIME%] Starting price-alert.py... >> "%LOG%"
start /MIN "YNAI5-PriceAlert" python "%WORKSPACE%\projects\crypto-monitoring\price-alert.py"

REM ─── Start Telegram-Claude Bridge ─────────────────
echo [%DATE% %TIME%] Starting telegram-bridge.py... >> "%LOG%"
start /MIN "YNAI5-TelegramBridge" python "%WORKSPACE%\projects\personal-ai-infrastructure\telegram-bridge.py"

REM ─── Done ─────────────────────────────────────────
echo [%DATE% %TIME%] YNAI5 startup complete. >> "%LOG%"
echo YNAI5 monitors started. Check Telegram.
```

**Step 2: Create install-startup.py**

```python
#!/usr/bin/env python3
"""
Install YNAI5 startup.bat as a Windows Startup shortcut.
Run once. Creates shortcut in Windows Startup folder.
"""

import os
import sys
from pathlib import Path

def install():
    bat_path = Path(r"C:\Users\shema\OneDrive\Desktop\YNAI5-SU\projects\system-health\startup.bat")
    startup_folder = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_folder / "YNAI5-Startup.bat"

    if not bat_path.exists():
        print(f"ERROR: startup.bat not found at {bat_path}")
        sys.exit(1)

    # On Windows, simplest approach: copy the bat directly to startup folder
    import shutil
    shutil.copy2(bat_path, shortcut_path)
    print(f"✅ Installed: {shortcut_path}")
    print("YNAI5 startup automation will now run on every Windows login.")
    print(f"To remove: delete {shortcut_path}")

if __name__ == "__main__":
    install()
```

**Step 3: Smoke test startup.bat (manually run it)**

```bash
"C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/startup.bat"
```
Expected: Health snapshot runs, price-alert and telegram-bridge start minimized

**Step 4: Install at Windows startup**

```bash
python "C:/Users/shema/OneDrive/Desktop/YNAI5-SU/projects/system-health/install-startup.py"
```
Expected: `✅ Installed: C:\Users\shema\AppData\Roaming\...\Startup\YNAI5-Startup.bat`

**Step 5: Commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add projects/system-health/
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat(system-health): Windows startup automation + install script"
```

---

## Task 8: GitHub Actions Cloud Health Check

**Files:**
- Create: `.github/workflows/system-health.yml`

**Step 1: Create the workflow**

```yaml
# .github/workflows/system-health.yml
name: YNAI5 Cloud Health Check

on:
  schedule:
    - cron: "0 13 * * *"   # 9AM AST (UTC-4) = 13:00 UTC
  workflow_dispatch:         # Manual trigger

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run cloud health check
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          COINGECKO_API_KEY: ${{ secrets.COINGECKO_API_KEY }}
          BRAVE_API_KEY: ${{ secrets.BRAVE_API_KEY }}
        run: python projects/system-health/cloud-health.py
```

**Step 2: Create cloud-health.py**

```python
#!/usr/bin/env python3
"""
YNAI5 Cloud Health Check
=========================
Runs on GitHub Actions (laptop OFF).
Checks API health and sends Telegram report.
"""

import os
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8569520396")

def check_api(name: str, url: str, headers: dict = None, timeout: int = 8) -> dict:
    try:
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        return {"name": name, "status": resp.status_code, "ok": resp.status_code < 400}
    except Exception as e:
        return {"name": name, "status": 0, "ok": False, "error": str(e)[:50]}

def run_checks() -> list:
    checks = [
        ("CoinGecko", "https://api.coingecko.com/api/v3/ping", None),
        ("Telegram API", f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe",
         None) if TELEGRAM_TOKEN else None,
        ("GitHub API", "https://api.github.com", None),
        ("Kraken", "https://api.kraken.com/0/public/SystemStatus", None),
        ("Anthropic", "https://api.anthropic.com", {"x-api-key": os.environ.get("ANTHROPIC_API_KEY", "")}),
    ]
    checks = [c for c in checks if c is not None]

    results = []
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        futures = {executor.submit(check_api, *c): c[0] for c in checks}
        for future in as_completed(futures):
            results.append(future.result())
    return results

def send_telegram(message: str):
    if not TELEGRAM_TOKEN:
        print("No Telegram token — skipping")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"
    }, timeout=10)

def main():
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    results = run_checks()

    lines = [f"☁️ *YNAI5 Cloud Health* — {ts}", ""]
    all_ok = True
    for r in sorted(results, key=lambda x: x['name']):
        icon = "✅" if r['ok'] else "❌"
        if not r['ok']:
            all_ok = False
        lines.append(f"{icon} {r['name']}: HTTP {r.get('status', '?')}")

    lines.append("")
    lines.append("✅ All APIs healthy" if all_ok else "⚠️ Some APIs unreachable — check logs")
    lines.append("_(laptop may be OFF — GitHub Actions report)_")

    report = "\n".join(lines)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
```

**Step 3: Push and verify GitHub Actions runs**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add .github/workflows/system-health.yml projects/system-health/cloud-health.py
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat(system-health): GitHub Actions cloud health check + Telegram alert"
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" push
```

---

## Task 9: Create System Health Project README + Update CLAUDE.md

**Files:**
- Create: `projects/system-health/README.md`
- Modify: `projects/README.md` (add system-health row)
- Modify: `CLAUDE.md` (add /health-check + /docker to Skills, update tree)
- Modify: `memory/MEMORY.md` (add session 9 summary)

**Step 1: Create README**

```markdown
# System Health — YNAI5

**Status:** 🔨 Building → ✅ Active
**Purpose:** Crash recovery, system diagnostics, Docker on-demand, Windows auto-start

## Components

| File | Purpose |
|------|---------|
| session-backup.py | Crash recovery engine (called by hooks) |
| health-check.py | Local system diagnostics (RAM/CPU/disk/internet) |
| cloud-health.py | API health checker (runs on GitHub Actions) |
| docker-manager.py | Docker on-demand manager |
| startup.bat | Windows startup automation |
| install-startup.py | One-time startup installer |
| backup/ | Session state backups |
| logs/ | Health check logs |

## Skills Added
- `/health-check` — run system diagnostics anytime
- `/docker [cmd]` — run Docker commands (auto-starts if needed)

## Hooks Configured
- `PreCompact` → session-backup.py --trigger=compact
- `Stop` → session-backup.py --trigger=stop
- `SessionStart` → session-backup.py --trigger=start

## GitHub Actions
- `system-health.yml` — runs 9AM AST daily, sends Telegram cloud health report

## Quick Commands
```bash
# Manual health check
python projects/system-health/health-check.py --telegram

# Manual backup
python projects/system-health/session-backup.py --trigger=compact

# Docker status
python projects/system-health/docker-manager.py status
```
```

**Step 2: Update projects/README.md** — add row:
```
| System Health | ✅ Active | High | [system-health/](system-health/) |
```

**Step 3: Update CLAUDE.md Skills section** — add:
```
- `/health-check` — system diagnostics (RAM/CPU/disk/internet/Docker) → system-health/logs/
- `/docker [command]` — Docker on-demand (auto-starts Docker Desktop if needed)
```

**Step 4: Update CLAUDE.md workspace tree** — add `system-health/` under `projects/`

**Step 5: Update MEMORY.md** with session 9 summary

**Step 6: Final commit**

```bash
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" add -A
git -C "C:/Users/shema/OneDrive/Desktop/YNAI5-SU" commit -m "feat: system-health project complete — crash recovery + health monitoring + Docker on-demand + Windows auto-start"
```

---

## Final Verification Checklist

- [ ] `claude mcp list` shows `fetch` and `git`
- [ ] `python session-backup.py --trigger=compact` → creates backup/session-backup.md
- [ ] `python session-backup.py --trigger=start` → reads and prints backup
- [ ] Claude settings.json has PreCompact, Stop, SessionStart hooks
- [ ] `python health-check.py` → prints full report, saves to logs/
- [ ] `python health-check.py --telegram` → Telegram message received
- [ ] `python docker-manager.py status` → prints Docker state
- [ ] startup.bat runs without errors
- [ ] YNAI5-Startup.bat exists in Windows Startup folder
- [ ] `.github/workflows/system-health.yml` exists and pushed
- [ ] `/health-check` skill exists in .claude/skills/
- [ ] `/docker` skill exists in .claude/skills/
- [ ] CLAUDE.md updated with new skills
- [ ] MEMORY.md updated

---

_Plan written: 2026-03-12 | Execution method: Subagent-Driven_
