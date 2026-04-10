#!/usr/bin/env python3
"""
YNAI5-Phase1 Dashboard — FastAPI backend
Serves live system status, heartbeat state, and task queue management.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import uuid
import subprocess
from datetime import datetime, timezone
from pydantic import BaseModel

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

app = FastAPI(title="YNAI5-Phase1 Dashboard", version="1.0.0")

# Serve static assets (v0.3.0 CSS/JS/config)
_DASH_DIR = os.path.dirname(__file__)
app.mount("/assets", StaticFiles(directory=os.path.join(_DASH_DIR, "assets")), name="assets")
app.mount("/config", StaticFiles(directory=os.path.join(_DASH_DIR, "config")), name="config")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEARTBEAT_PATH = "/mnt/gdrive/SYNC/HEARTBEAT.json"
DRIVE_ROOT = "/mnt/gdrive"
GEMINI_LOG = "/ynai5_runtime/logs/gemini_worker.log"
CLAUDE_LOG = "/ynai5_runtime/logs/claude_runner.log"
DASHBOARD_HTML = os.path.join(os.path.dirname(__file__), "index.html")


class TaskRequest(BaseModel):
    command: str
    assigned_to: str  # "claude" | "gemini"
    priority: int = 1
    context: str = ""


def read_heartbeat() -> dict:
    try:
        with open(HEARTBEAT_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Drive not mounted", "status": "offline"}
    except json.JSONDecodeError:
        return {"error": "HEARTBEAT.json corrupted", "status": "error"}


def write_heartbeat(data: dict):
    data["last_update"] = datetime.now(timezone.utc).isoformat()
    tmp = HEARTBEAT_PATH + ".dashboard.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, HEARTBEAT_PATH)


def get_vm_metrics() -> dict:
    if not PSUTIL_OK:
        return {"error": "psutil not installed"}
    import psutil
    try:
        boot_ts = psutil.boot_time()
        uptime_s = int(datetime.now().timestamp() - boot_ts)
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 2),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
            "disk_percent": psutil.disk_usage("/").percent,
            "disk_free_gb": round(psutil.disk_usage("/").free / 1e9, 2),
            "uptime_hours": round(uptime_s / 3600, 1),
        }
    except Exception as e:
        return {"error": str(e)}


def get_service_status(service: str) -> str:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def tail_log(path: str, lines: int = 20) -> list:
    try:
        with open(path) as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:]]
    except FileNotFoundError:
        return [f"Log not found: {path}"]
    except Exception as e:
        return [f"Error reading log: {e}"]


@app.get("/api/status")
def get_status():
    hb = read_heartbeat()
    vm = get_vm_metrics()
    drive_mounted = os.path.exists(DRIVE_ROOT) and bool(os.listdir(DRIVE_ROOT))
    services = {
        "ynai5-drive": get_service_status("ynai5-drive"),
        "ynai5-gemini": get_service_status("ynai5-gemini"),
        "ynai5-claude": get_service_status("ynai5-claude"),
        "ynai5-dashboard": get_service_status("ynai5-dashboard"),
    }
    return {
        "heartbeat": hb,
        "vm": vm,
        "drive_mounted": drive_mounted,
        "services": services,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/task")
def post_task(task: TaskRequest):
    if task.assigned_to not in ("claude", "gemini"):
        raise HTTPException(400, "assigned_to must be 'claude' or 'gemini'")
    if not task.command.strip():
        raise HTTPException(400, "command cannot be empty")

    hb = read_heartbeat()
    if "error" in hb:
        raise HTTPException(503, f"Cannot reach HEARTBEAT: {hb['error']}")

    new_task = {
        "id": str(uuid.uuid4())[:8],
        "type": "manual",
        "command": task.command.strip(),
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "context": task.context,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    hb.setdefault("task_queue", []).append(new_task)
    write_heartbeat(hb)
    return {"status": "queued", "task_id": new_task["id"], "assigned_to": task.assigned_to}


@app.delete("/api/task/{task_id}")
def delete_task(task_id: str):
    hb = read_heartbeat()
    before = len(hb.get("task_queue", []))
    hb["task_queue"] = [t for t in hb.get("task_queue", []) if t["id"] != task_id]
    if len(hb["task_queue"]) == before:
        raise HTTPException(404, f"Task {task_id} not found")
    write_heartbeat(hb)
    return {"status": "deleted", "task_id": task_id}


@app.get("/api/logs/gemini")
def get_gemini_logs(lines: int = 30):
    return {"logs": tail_log(GEMINI_LOG, lines)}


@app.get("/api/logs/claude")
def get_claude_logs(lines: int = 30):
    return {"logs": tail_log(CLAUDE_LOG, lines)}


@app.get("/api/heartbeat")
def get_heartbeat():
    return read_heartbeat()


@app.get("/status.json")
def get_status_compat():
    """Compat endpoint — translates /api/status data to format expected by metrics.js."""
    vm = get_vm_metrics()
    services = {
        "ynai5-drive":      get_service_status("ynai5-drive"),
        "ynai5-gemini":     get_service_status("ynai5-gemini"),
        "ynai5-claude":     get_service_status("ynai5-claude"),
        "ynai5-dashboard":  get_service_status("ynai5-dashboard"),
        "ynai5-chat":       get_service_status("ynai5-chat"),
        "nginx":            get_service_status("nginx"),
    }

    ram_used_mb = int(vm.get("ram_used_gb", 0) * 1024)
    uptime_h = vm.get("uptime_hours", 0)
    uptime_str = f"{int(uptime_h)}h {int((uptime_h % 1) * 60)}m"

    checks = {
        svc: {"status": "ok" if state == "active" else "err", "state": state}
        for svc, state in services.items()
    }

    LOG_MAP = {
        "gemini":    "/ynai5_runtime/logs/gemini_worker.log",
        "claude":    "/ynai5_runtime/logs/claude_runner.log",
        "dashboard": "/ynai5_runtime/logs/dashboard.log",
    }
    service_logs = {k: tail_log(v, 30) for k, v in LOG_MAP.items()}

    hb = read_heartbeat()
    stats = hb.get("stats", {})
    ok_count = sum(1 for c in checks.values() if c["status"] == "ok")

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": "0.3.1",
        "system": {
            "ram_used_mb":   ram_used_mb,
            "cpu_pct":       vm.get("cpu_percent", 0),
            "disk_used_pct": vm.get("disk_percent", 0),
            "uptime":        uptime_str,
        },
        "checks":       checks,
        "summary":      f"{ok_count}/{len(checks)} operational",
        "service_logs": service_logs,
        "billing": {
            "daily_usd":    0.0,
            "gemini_calls": stats.get("gemini_calls", 0),
            "claude_calls": stats.get("claude_calls", 0),
        },
    }


# ── YNAI5Logs — structured event log ──────────────────────────────────────────

YNAI5_LOG_PATH = os.path.expanduser("~/YNAI5_AI_CORE/logs/ynai5logs.json")


def _ynai5log_append(entry: dict):
    try:
        data = json.load(open(YNAI5_LOG_PATH)) if os.path.exists(YNAI5_LOG_PATH) else {"events": []}
    except Exception:
        data = {"events": []}
    data["events"].append(entry)
    data["events"] = data["events"][-200:]
    with open(YNAI5_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)


@app.get("/api/ynai5logs")
def get_ynai5logs(last: int = 50):
    try:
        with open(YNAI5_LOG_PATH) as f:
            data = json.load(f)
        events = data.get("events", [])
        return {"events": events[-last:], "total": len(events)}
    except FileNotFoundError:
        return {"events": [], "total": 0, "note": "No log file yet — will appear after first event"}


@app.post("/api/ynai5logs")
def post_ynai5log(payload: dict):
    entry = {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "component":  payload.get("component", "system"),
        "issue":      payload.get("issue", ""),
        "root_cause": payload.get("root_cause", ""),
        "fix":        payload.get("fix", ""),
    }
    _ynai5log_append(entry)
    return {"status": "logged", "ts": entry["ts"]}


# ── Foundation stubs ───────────────────────────────────────────────────────────

@app.get("/api/usage")
def get_usage():
    """API call tracking — reads from heartbeat stats. Full billing = future feature."""
    hb = read_heartbeat()
    stats = hb.get("stats", {})
    return {
        "gemini_calls":    stats.get("gemini_calls", 0),
        "claude_calls":    stats.get("claude_calls", 0),
        "tasks_completed": stats.get("tasks_completed", 0),
        "note": "Full billing tracking — future feature",
    }


@app.get("/api/agents")
def list_agents():
    """Agent registry — discovers agents from AGENTS.md."""
    agents_path = os.path.expanduser("~/YNAI5_AI_CORE/AGENTS.md")
    try:
        with open(agents_path) as f:
            content = f.read()
        return {"source": "AGENTS.md", "content_length": len(content), "available": True}
    except Exception:
        return {"available": False, "note": "AGENTS.md not found"}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    try:
        with open(DASHBOARD_HTML) as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Dashboard HTML not found</h1><p>Place index.html in /ynai5_runtime/dashboard/</p>"
