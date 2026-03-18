#!/usr/bin/env python3
"""
YNAI5 Autonomous Agent
======================
Cloud-compatible autonomous coding agent using Anthropic API directly.
No Claude Code CLI required — runs in GitHub Actions or locally.

Usage:
    python autonomous-agent.py                          # uses tasks/current-task.md
    python autonomous-agent.py tasks/my-task.md        # specific task file
    python autonomous-agent.py --task "Do X, Y, Z"    # inline task
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

import anthropic

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent.parent  # YNAI5-SU root
MODEL = "claude-opus-4-6"
MAX_ITERATIONS = 15
SESSIONS_DIR = Path(__file__).parent / "sessions"
TASKS_DIR = Path(__file__).parent / "tasks"


# ─────────────────────────────────────────────
# Tool Definitions
# ─────────────────────────────────────────────
TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the YNAI5-SU workspace. Path is relative to workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to workspace root (e.g. 'projects/crypto-monitoring/watchlist.md')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file in the YNAI5-SU workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to workspace root"
                },
                "content": {
                    "type": "string",
                    "description": "Full file content to write"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory of the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to workspace root. Default: '' (root)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob pattern (e.g. '*.md', '*.py')"
                }
            },
            "required": []
        }
    },
    {
        "name": "run_bash",
        "description": "Run a bash/shell command. Use for git, python scripts, file operations, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (relative to workspace root). Default: workspace root"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds. Default: 30"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "append_file",
        "description": "Append content to the end of an existing file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "content": {"type": "string", "description": "Content to append"}
            },
            "required": ["path", "content"]
        }
    }
]


# ─────────────────────────────────────────────
# Tool Execution
# ─────────────────────────────────────────────
def execute_tool(name: str, input_data: dict) -> str:
    """Execute a tool call and return string result."""
    try:
        if name == "read_file":
            file_path = WORKSPACE / input_data["path"]
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                # Truncate very large files
                if len(content) > 50000:
                    content = content[:50000] + "\n\n[... truncated at 50K chars ...]"
                return content
            return f"Error: File not found: {input_data['path']}"

        elif name == "write_file":
            file_path = WORKSPACE / input_data["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(input_data["content"], encoding="utf-8")
            return f"✅ Written: {input_data['path']} ({len(input_data['content'])} chars)"

        elif name == "append_file":
            file_path = WORKSPACE / input_data["path"]
            if not file_path.exists():
                return f"Error: File not found: {input_data['path']}"
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(input_data["content"])
            return f"✅ Appended to: {input_data['path']}"

        elif name == "list_files":
            dir_path = WORKSPACE / input_data.get("path", "")
            if not dir_path.exists():
                return f"Error: Directory not found: {input_data.get('path', '')}"
            pattern = input_data.get("pattern", "*")
            files = sorted(dir_path.glob(pattern))
            return "\n".join(str(f.relative_to(WORKSPACE)) for f in files[:100])

        elif name == "run_bash":
            cwd = WORKSPACE / input_data.get("cwd", "")
            timeout = input_data.get("timeout", 30)
            result = subprocess.run(
                input_data["command"],
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=timeout
            )
            output = result.stdout.strip()
            if result.returncode != 0 and result.stderr:
                output += f"\nSTDERR: {result.stderr.strip()}"
            return output or "(no output)"

        return f"Unknown tool: {name}"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {input_data.get('timeout', 30)}s"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


# ─────────────────────────────────────────────
# Agent Loop
# ─────────────────────────────────────────────
def run_agent(task: str) -> list[str]:
    """Run the autonomous agent loop. Returns list of text outputs."""
    client = anthropic.Anthropic()

    system = f"""You are YNAI5 Autonomous Agent — a coding and task agent running in the YNAI5-SU workspace.

Workspace: {WORKSPACE}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M AST')}

You can read files, write files, list directories, append to files, and run bash commands.
You have full access to the YNAI5-SU project workspace.

Instructions:
- Complete the task step by step
- Use tools to explore the workspace before making changes
- Save all outputs to files (never just respond in text)
- Be specific and actionable
- When done, summarize exactly what you did and what files were created/modified"""

    messages = [{"role": "user", "content": f"Complete this task:\n\n{task}"}]
    session_log = []

    print(f"\n🤖 Agent starting — model: {MODEL}")
    print(f"📋 Task preview: {task[:150]}...\n")

    for iteration in range(MAX_ITERATIONS):
        print(f"── Iteration {iteration + 1}/{MAX_ITERATIONS} ──")

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system,
            tools=TOOLS,
            messages=messages
        )

        # Collect text output
        text_parts = [b.text for b in response.content if b.type == "text"]
        if text_parts:
            combined = "\n".join(text_parts)
            session_log.append(f"**[Iteration {iteration + 1}]**\n{combined}")
            print(combined)

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        # Done
        if response.stop_reason == "end_turn":
            print("\n✅ Agent completed task")
            break

        # Execute tools
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    args_preview = json.dumps(block.input)[:100]
                    print(f"  🔧 {block.name}({args_preview})")
                    result = execute_tool(block.name, block.input)
                    result_preview = result[:200].replace('\n', ' ')
                    print(f"     → {result_preview}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return session_log


# ─────────────────────────────────────────────
# Telegram Notification
# ─────────────────────────────────────────────
def send_telegram(message: str):
    """Send Telegram notification (silent if tokens not configured)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    import urllib.request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram notify failed: {e}")


# ─────────────────────────────────────────────
# Load Task
# ─────────────────────────────────────────────
def load_task(args: list[str]) -> str:
    """Load task from args, file, or default."""
    # --task "inline task string"
    if "--task" in args:
        idx = args.index("--task")
        return args[idx + 1]

    # Positional arg = task file path
    file_candidates = [a for a in args if not a.startswith("--")]
    if file_candidates:
        path = Path(file_candidates[0])
        if path.exists():
            return path.read_text(encoding="utf-8")
        # Try relative to tasks dir
        path = TASKS_DIR / file_candidates[0]
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Task file not found: {file_candidates[0]}")

    # Default: tasks/current-task.md
    default = TASKS_DIR / "current-task.md"
    if default.exists():
        return default.read_text(encoding="utf-8")

    raise FileNotFoundError(
        "No task found. Create tasks/current-task.md or pass --task 'description'"
    )


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    SESSIONS_DIR.mkdir(exist_ok=True)

    print("=" * 50)
    print("  YNAI5 Autonomous Agent")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M AST')}")
    print("=" * 50)

    try:
        task = load_task(sys.argv[1:])

        session_log = run_agent(task)

        # Save session
        output_path = SESSIONS_DIR / f"{ts}-session.md"
        output_content = f"""# Autonomous Session — {ts}

## Task
{task}

## Session Log
{chr(10).join(session_log)}

---
_Generated by YNAI5 Autonomous Agent_
"""
        output_path.write_text(output_content, encoding="utf-8")
        print(f"\n📄 Session saved: {output_path.relative_to(WORKSPACE)}")

        # Telegram
        send_telegram(
            f"✅ <b>YNAI5 Agent Done</b>\n"
            f"Session: {ts}\n"
            f"Task: {task[:100]}...\n"
            f"Output: projects/ralph-automation/sessions/{ts}-session.md"
        )

    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nCreate a task file:")
        print(f"  {TASKS_DIR / 'current-task.md'}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Agent interrupted by user")
        sys.exit(0)

    except Exception as e:
        error_msg = f"Agent error: {type(e).__name__}: {e}"
        print(f"\n❌ {error_msg}")
        send_telegram(f"❌ <b>YNAI5 Agent Error</b>\n{error_msg}")
        sys.exit(1)
