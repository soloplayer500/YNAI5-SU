"""
YNAI5 Task Manager
====================
Local web UI to add/edit/delete tasks with priority levels.
Autonomous agent mode: works through tasks starting with highest priority.

Usage:
    python task-manager.py --ui           (start web UI on localhost:7700)
    python task-manager.py --add          (add task via CLI)
    python task-manager.py --list         (list all tasks)
    python task-manager.py --work         (autonomous: work highest-priority task via Claude API)
    python task-manager.py --complete ID  (mark task complete)
    python task-manager.py --delete ID    (delete task)
"""

import json
import sys
import os
import datetime
import pathlib
import argparse
import uuid

WORKSPACE  = pathlib.Path("C:/Users/shema/OneDrive/Desktop/YNAI5-SU")
TASKS_FILE = WORKSPACE / "tools" / "tasks.json"
TASKS_LOG  = WORKSPACE / "tools" / "tasks.log"

PRIORITIES = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ── Storage ───────────────────────────────────────────────────────────────────

def load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def save_tasks(tasks: list[dict]) -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")


def log(msg: str) -> None:
    TASKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with TASKS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


# ── CLI operations ────────────────────────────────────────────────────────────

def add_task(title: str = None, priority: str = None, notes: str = None) -> dict:
    if not title:
        title    = input("Task title: ").strip()
        priority = input("Priority [critical/high/medium/low] (default: medium): ").strip() or "medium"
        notes    = input("Notes (optional): ").strip()

    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "priority": priority if priority in PRIORITIES else "medium",
        "notes": notes or "",
        "status": "pending",
        "created": datetime.datetime.now().isoformat(),
        "completed": None,
    }
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    log(f"ADD [{task['priority']}] {task['title']} (id={task['id']})")
    print(f"✅ Task added: [{task['id']}] {task['title']}")
    return task


def list_tasks(status_filter: str = None) -> None:
    tasks = load_tasks()
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]

    if not tasks:
        print("No tasks found.")
        return

    sorted_tasks = sorted(tasks, key=lambda t: (PRIORITIES.get(t.get("priority", "medium"), 2), t["created"]))
    print(f"\n{'ID':<10} {'PRIORITY':<10} {'STATUS':<12} {'TITLE'}")
    print("-" * 80)
    for t in sorted_tasks:
        print(f"{t['id']:<10} {t.get('priority','medium'):<10} {t['status']:<12} {t['title'][:50]}")


def complete_task(task_id: str) -> None:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            t["completed"] = datetime.datetime.now().isoformat()
            save_tasks(tasks)
            log(f"COMPLETE {task_id}: {t['title']}")
            print(f"✅ Task {task_id} marked complete.")
            return
    print(f"Task {task_id} not found.")


def delete_task(task_id: str) -> None:
    tasks = load_tasks()
    original = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < original:
        save_tasks(tasks)
        log(f"DELETE {task_id}")
        print(f"🗑 Task {task_id} deleted.")
    else:
        print(f"Task {task_id} not found.")


def work_next_task() -> None:
    """Autonomous mode: take the highest priority pending task and work it via Claude API."""
    tasks = load_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]

    if not pending:
        print("[Task Agent] No pending tasks. Queue is empty.")
        log("WORK: No pending tasks.")
        return

    sorted_pending = sorted(pending, key=lambda t: (PRIORITIES.get(t.get("priority", "medium"), 2), t["created"]))
    task = sorted_pending[0]
    print(f"[Task Agent] Working task: [{task['priority']}] {task['title']}")
    log(f"WORK START: {task['id']} — {task['title']}")

    # Mark as in_progress
    for t in tasks:
        if t["id"] == task["id"]:
            t["status"] = "in_progress"
            t["started"] = datetime.datetime.now().isoformat()
    save_tasks(tasks)

    # Call Claude API to work this task
    try:
        import anthropic
        from dotenv import load_dotenv
        load_dotenv(WORKSPACE / ".env.local")

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        system = (
            "You are an autonomous AI agent for Shami's YNAI5 workspace. "
            "Your job is to complete tasks from the task queue. "
            "Be concise and actionable. Deliver real output, not just plans."
        )
        user_msg = (
            f"Complete this task from my task queue:\n\n"
            f"**Task:** {task['title']}\n"
            f"**Priority:** {task['priority']}\n"
            f"**Notes:** {task.get('notes', 'none')}\n\n"
            f"Workspace: C:/Users/shema/OneDrive/Desktop/YNAI5-SU\n"
            f"Deliver your output directly. Be brief and actionable."
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_msg}],
            system=system,
        )
        result = response.content[0].text

        # Save result
        output_file = WORKSPACE / "tools" / f"task-output-{task['id']}.md"
        output_file.write_text(
            f"# Task Output: {task['title']}\n\n"
            f"**Completed:** {datetime.datetime.now().isoformat()}\n\n"
            f"---\n\n{result}\n",
            encoding="utf-8"
        )

        # Mark complete
        for t in tasks:
            if t["id"] == task["id"]:
                t["status"] = "completed"
                t["completed"] = datetime.datetime.now().isoformat()
                t["output_file"] = str(output_file)
        save_tasks(tasks)
        log(f"WORK DONE: {task['id']} — output saved to {output_file.name}")
        print(f"[Task Agent] ✅ Done. Output saved to tools/task-output-{task['id']}.md")
        print(f"\n--- RESULT ---\n{result[:500]}...")

    except ImportError:
        print("[Task Agent] anthropic not installed. Run: pip install anthropic python-dotenv")
        log("WORK FAIL: anthropic not installed")
    except Exception as e:
        print(f"[Task Agent] Error: {e}")
        log(f"WORK ERROR: {task['id']} — {e}")


# ── Web UI ────────────────────────────────────────────────────────────────────

def start_ui() -> None:
    """Launch a minimal Flask web UI for task management."""
    try:
        from flask import Flask, request, jsonify, render_template_string
    except ImportError:
        print("Flask not installed. Run: pip install flask")
        return

    app = Flask(__name__)

    HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>YNAI5 Task Manager</title>
<style>
  body { font-family: monospace; background: #0f0f0f; color: #e0e0e0; margin: 20px; }
  h1 { color: #00ff88; } h2 { color: #aaa; font-size: 14px; }
  input, select, textarea { background: #1a1a1a; color: #fff; border: 1px solid #333; padding: 6px; width: 300px; }
  button { background: #00ff88; color: #000; border: none; padding: 8px 16px; cursor: pointer; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  th { background: #1a1a1a; color: #00ff88; padding: 8px; text-align: left; }
  td { padding: 8px; border-bottom: 1px solid #222; }
  .critical { color: #ff4444; } .high { color: #ff8800; } .medium { color: #ffff00; } .low { color: #aaa; }
  .pending { color: #aaa; } .in_progress { color: #00ff88; } .completed { color: #555; text-decoration: line-through; }
  .del-btn { background: #ff4444; color: #fff; border: none; padding: 4px 8px; cursor: pointer; }
</style>
</head>
<body>
<h1>YNAI5 Task Manager</h1>
<h2>Add New Task</h2>
<form id="addForm">
  <input type="text" id="title" placeholder="Task title..." required><br><br>
  <select id="priority">
    <option value="critical">Critical</option>
    <option value="high">High</option>
    <option value="medium" selected>Medium</option>
    <option value="low">Low</option>
  </select>
  <input type="text" id="notes" placeholder="Notes (optional)"><br><br>
  <button type="submit">+ Add Task</button>
</form>
<table id="taskTable">
  <thead><tr><th>ID</th><th>Priority</th><th>Status</th><th>Title</th><th>Actions</th></tr></thead>
  <tbody id="taskBody"></tbody>
</table>
<script>
async function loadTasks() {
  const r = await fetch('/tasks'); const tasks = await r.json();
  const body = document.getElementById('taskBody');
  body.innerHTML = '';
  tasks.sort((a,b) => ({'critical':0,'high':1,'medium':2,'low':3}[a.priority]||2) - ({'critical':0,'high':1,'medium':2,'low':3}[b.priority]||2));
  for (const t of tasks) {
    body.innerHTML += `<tr class="${t.status}">
      <td>${t.id}</td>
      <td class="${t.priority}">${t.priority}</td>
      <td>${t.status}</td>
      <td>${t.title}</td>
      <td>
        ${t.status!='completed'?`<button onclick="completeTask('${t.id}')">Done</button>`:''}
        <button class="del-btn" onclick="deleteTask('${t.id}')">Del</button>
      </td></tr>`;
  }
}
document.getElementById('addForm').onsubmit = async (e) => {
  e.preventDefault();
  await fetch('/tasks', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({title: document.getElementById('title').value,
      priority: document.getElementById('priority').value,
      notes: document.getElementById('notes').value})});
  document.getElementById('title').value = '';
  document.getElementById('notes').value = '';
  loadTasks();
};
async function completeTask(id) { await fetch('/tasks/'+id+'/complete', {method:'POST'}); loadTasks(); }
async function deleteTask(id) { await fetch('/tasks/'+id, {method:'DELETE'}); loadTasks(); }
loadTasks();
setInterval(loadTasks, 10000);
</script>
</body>
</html>"""

    @app.route("/")
    def index():
        return render_template_string(HTML)

    @app.route("/tasks", methods=["GET"])
    def get_tasks():
        return jsonify(load_tasks())

    @app.route("/tasks", methods=["POST"])
    def create_task():
        data = request.json
        task = add_task(title=data.get("title"), priority=data.get("priority", "medium"), notes=data.get("notes", ""))
        return jsonify(task), 201

    @app.route("/tasks/<task_id>/complete", methods=["POST"])
    def mark_complete(task_id):
        complete_task(task_id)
        return jsonify({"ok": True})

    @app.route("/tasks/<task_id>", methods=["DELETE"])
    def del_task(task_id):
        delete_task(task_id)
        return jsonify({"ok": True})

    print("[Task Manager] Starting web UI at http://localhost:7700")
    print("[Task Manager] Press Ctrl+C to stop")
    app.run(host="127.0.0.1", port=7700, debug=False)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="YNAI5 Task Manager")
    parser.add_argument("--ui",      action="store_true", help="Start web UI (localhost:7700)")
    parser.add_argument("--add",     action="store_true", help="Add task interactively")
    parser.add_argument("--list",    action="store_true", help="List all tasks")
    parser.add_argument("--work",    action="store_true", help="Work highest-priority task (autonomous)")
    parser.add_argument("--complete",metavar="ID",        help="Mark task complete by ID")
    parser.add_argument("--delete",  metavar="ID",        help="Delete task by ID")
    args = parser.parse_args()

    if args.ui:
        start_ui()
    elif args.add:
        add_task()
    elif args.list:
        list_tasks()
    elif args.work:
        work_next_task()
    elif args.complete:
        complete_task(args.complete)
    elif args.delete:
        delete_task(args.delete)
    else:
        list_tasks()


if __name__ == "__main__":
    main()
