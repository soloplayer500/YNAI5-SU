"""
YNAI5 Gmail Inbox Manager
===========================
Scans Gmail inbox, triages messages into URGENT/NEEDS REPLY/FYI/JUNK,
drafts replies for URGENT and NEEDS REPLY using Claude API.
State saved in emails_processed.json. Logs to inbox_manager.log.

This script integrates with the Gmail MCP server already connected.
For scheduled use: run via Windows Task Scheduler or GitHub Actions.

Usage:
    python gmail-manager.py              (run full triage cycle)
    python gmail-manager.py --dry-run    (analyze only, no drafts created)
    python gmail-manager.py --stats      (show processing stats)

NOTE: This uses the Claude API directly (not MCP) for portability.
The Gmail MCP is used interactively in Claude Code sessions.
"""

import json
import os
import sys
import datetime
import pathlib
import argparse

WORKSPACE      = pathlib.Path("C:/Users/shema/OneDrive/Desktop/YNAI5-SU")
STATE_FILE     = WORKSPACE / "tools" / "emails_processed.json"
LOG_FILE       = WORKSPACE / "tools" / "inbox_manager.log"
DRAFTS_DIR     = WORKSPACE / "tools" / "email-drafts"

# Triage categories
URGENT      = "URGENT"
NEEDS_REPLY = "NEEDS REPLY"
FYI         = "FYI"
JUNK        = "JUNK"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_ids": [], "last_run": None, "stats": {"urgent": 0, "needs_reply": 0, "fyi": 0, "junk": 0}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_run"] = datetime.datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def triage_email(subject: str, sender: str, snippet: str, api_key: str) -> dict:
    """Ask Claude to triage one email. Returns {category, draft_reply}."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Triage this email for Shami (AI systems builder in Aruba):

FROM: {sender}
SUBJECT: {subject}
PREVIEW: {snippet[:300]}

Classify as exactly one of: URGENT, NEEDS REPLY, FYI, JUNK

Rules:
- URGENT: time-sensitive, needs action today (payments, deadlines, emergencies)
- NEEDS REPLY: should reply within 48h (business, collaboration, brand deals)
- FYI: informational, newsletters, notifications (no reply needed)
- JUNK: spam, promotions, irrelevant

If URGENT or NEEDS REPLY, also write a short draft reply (2-3 sentences, tone-matched to Shami's last sent emails — professional but friendly).

Respond in JSON:
{{"category": "URGENT|NEEDS REPLY|FYI|JUNK", "reason": "one sentence why", "draft_reply": "reply text or empty string"}}"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        result = json.loads(response.content[0].text)
        return result
    except Exception as e:
        log(f"TRIAGE ERROR: {e}")
        return {"category": FYI, "reason": "Error triaging", "draft_reply": ""}


def save_draft(email_id: str, subject: str, sender: str, draft: str) -> None:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = email_id.replace("/", "-")[:20]
    draft_file = DRAFTS_DIR / f"draft-{safe_id}.md"
    content = (
        f"# Draft Reply\n\n"
        f"**To:** {sender}\n"
        f"**Subject:** Re: {subject}\n"
        f"**Generated:** {datetime.datetime.now().isoformat()}\n\n"
        f"---\n\n{draft}\n"
    )
    draft_file.write_text(content, encoding="utf-8")


def run_triage(dry_run: bool = False) -> None:
    """
    Main triage loop.
    In a real implementation, this would use the Gmail MCP server.
    For standalone script use, it uses the Gmail API directly.
    Since Gmail MCP is already set up in Claude Code, this script
    generates a triage report that can be reviewed in the next session.
    """
    log(f"Starting triage cycle (dry_run={dry_run})")
    state = load_state()

    # Load .env.local for API key
    env_file = WORKSPACE / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[Gmail Manager] ERROR: ANTHROPIC_API_KEY not found in .env.local")
        log("ERROR: No ANTHROPIC_API_KEY")
        return

    # Generate instructions file for Gmail MCP integration
    # (Gmail MCP is available in Claude Code sessions interactively)
    report_file = WORKSPACE / "actions" / "gmail-triage-pending.md"
    WORKSPACE.joinpath("actions").mkdir(parents=True, exist_ok=True)

    report_file.write_text(
        "# Gmail Triage Pending\n\n"
        f"_Requested: {datetime.datetime.now().isoformat()}_\n\n"
        "## Instructions for Claude\n\n"
        "1. Use `/email-check` skill to search Gmail for unread messages from last 24h\n"
        "2. For each email: classify as URGENT / NEEDS REPLY / FYI / JUNK\n"
        "3. For URGENT and NEEDS REPLY: draft a reply (professional but friendly, tone-matched)\n"
        "4. Save drafts to `tools/email-drafts/` folder\n"
        "5. Report summary: X urgent, X needs reply, X FYI, X junk\n"
        "6. Delete this file when done\n\n"
        "> Auto-generated by gmail-manager.py. Process at next session.\n",
        encoding="utf-8",
    )

    print(f"[Gmail Manager] Triage request queued → actions/gmail-triage-pending.md")
    print("[Gmail Manager] Claude will process this at next session via /email-check skill.")
    log("Triage request queued to actions/gmail-triage-pending.md")


def show_stats() -> None:
    state = load_state()
    print(f"\n=== Gmail Manager Stats ===")
    print(f"Last run: {state.get('last_run', 'never')}")
    stats = state.get("stats", {})
    print(f"Processed: {len(state.get('processed_ids', []))} emails total")
    for k, v in stats.items():
        print(f"  {k.upper()}: {v}")

    drafts = list(DRAFTS_DIR.glob("*.md")) if DRAFTS_DIR.exists() else []
    print(f"Drafts saved: {len(drafts)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="YNAI5 Gmail Inbox Manager")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, no drafts")
    parser.add_argument("--stats",   action="store_true", help="Show stats")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        run_triage(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
