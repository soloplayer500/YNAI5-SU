# Ralph Automation — Cloud Autonomous Agent

**Status:** 🔨 Building
**Purpose:** Run autonomous Claude coding sessions on a schedule — works with laptop OFF via GitHub Actions

---

## What It Does

`autonomous-agent.py` is a direct Anthropic API agent that:
- Reads a task from `tasks/current-task.md`
- Runs a multi-turn autonomous loop (file read/write, bash execution)
- Saves session output to `sessions/YYYY-MM-DD-HHMM-session.md`
- Sends Telegram notification when done

## Components

| File | Purpose |
|------|---------|
| `autonomous-agent.py` | Main agent script |
| `tasks/current-task.md` | Active task (edit this to set what the agent does) |
| `tasks/example.md` | Example task template |
| `sessions/` | Auto-saved session outputs |

## Usage

### Run Locally
```bash
cd C:\Users\shema\OneDrive\Desktop\YNAI5-SU
python projects/ralph-automation/autonomous-agent.py
# Or with specific task file:
python projects/ralph-automation/autonomous-agent.py projects/ralph-automation/tasks/my-task.md
```

### Run via GitHub Actions
- Push a task to `tasks/current-task.md`
- Workflow runs automatically on schedule (Mon/Wed/Fri 10AM AST)
- Or trigger manually: GitHub → Actions → Ralph Autonomous Agent → Run workflow

## Scheduling

| Mode | Schedule | Requires |
|------|----------|---------|
| GitHub Actions | 3x/week (Mon/Wed/Fri 10AM AST) | ANTHROPIC_API_KEY secret in repo |
| Windows Task Scheduler | On demand / daily | Laptop ON |
| Manual | Any time | Git Bash |

## Required GitHub Secrets
- `ANTHROPIC_API_KEY` — Anthropic API key
- `TELEGRAM_BOT_TOKEN` — (optional) For completion notifications
- `TELEGRAM_CHAT_ID` — (optional) Your Telegram chat ID

## Cost Estimate
- ~$0.01–$0.05 per session (claude-opus-4-6 with adaptive thinking)
- ~$0.10–$0.60/month at 3x/week
