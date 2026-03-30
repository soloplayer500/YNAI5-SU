#!/usr/bin/env python3
"""
BRAINAI5 V3 — Phase 2: Deep Dive Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs after user approves Phase 1. Called by niche-approve.yml.

Steps:
  1. Find JSON report for slug
  2. Update Google Sheets (5 tabs)
  3. Generate HTML dashboard
  4. Send full Telegram report

Usage:
  NICHE_SLUG=betrayal-karma-narratives python niche_deepdive.py
  python niche_deepdive.py betrayal-karma-narratives
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── UTF-8 fix ──────────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Config ─────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).resolve().parent
REPORTS_DIR = HERE / "output" / "reports"
DASH_DIR    = HERE / "output" / "dashboards"

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
NICHE_SLUG = os.environ.get("NICHE_SLUG", sys.argv[1] if len(sys.argv) > 1 else "")


# ── Helpers ────────────────────────────────────────────────────────────────────
def log(tag: str, msg: str):
    print(f"[{tag}] {msg}", flush=True)


def tg_send(text: str):
    if not TG_TOKEN:
        return
    payload = json.dumps(
        {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        log("TG", f"Error: {e}")


def find_report(slug: str) -> Path:
    """Find most recent .json report matching slug (not .approved marker)."""
    matches = sorted(
        [p for p in REPORTS_DIR.glob(f"*-{slug}.json") if not p.name.endswith(".approved")],
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(f"No report found for slug: {slug}")
    return matches[0]


def run_sub(script: Path, *args: str) -> tuple[int, str]:
    """Run a Python subscript, return (returncode, combined output)."""
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    combined = (result.stdout + result.stderr).strip()
    return result.returncode, combined


# ── Telegram full report ───────────────────────────────────────────────────────
def build_full_report(data: dict, sheets_ok: bool) -> str:
    stats     = data.get("stats", {})
    creators  = data.get("creators", [])[:3]
    formats   = data.get("formats", [])[:3]
    bo        = data.get("blue_ocean", [])[:3]
    niche     = data.get("niche", "?")
    slug      = data.get("slug", "?")
    today     = data.get("date", "?")

    creator_lines = "\n".join(
        f"  \u2514 {c.get('name','?')} \u2014 {c.get('subs','?')} subs \u2022 ${c.get('est_monthly_rev','?')}/mo"
        for c in creators
    ) or "  (none)"

    format_lines = "\n".join(
        f"  \u2514 {f.get('name','?')} ({f.get('platform','?')}): avg {f.get('avg_views','?')} views"
        for f in formats
    ) or "  (none)"

    opp_lines = "\n".join(
        f"  \u2514 {o.get('name','?')}: RPM ${o.get('rpm_est','?')} | {o.get('effort_hours','?')}h | {o.get('entry_barrier','?')}"
        for o in bo
    ) or "  (none)"

    sheets_status = "\u2705 5 tabs updated" if sheets_ok else "\u26a0\ufe0f Sheets skipped/error"
    dash_path = f"{today}-{slug}.html"

    return (
        "\U0001f4c8 <b>DEEP DIVE COMPLETE</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f3c6 <b>NICHE:</b> {niche}\n"
        f"\u251c\u2500 Growth: <b>{stats.get('growth_rate','?')}x/yr</b>\n"
        f"\u251c\u2500 Saturation: <b>{stats.get('saturation','?')} Ocean</b>\n"
        f"\u2514\u2500 RPM Range: <b>${stats.get('cpm_low','?')}\u2013${stats.get('cpm_high','?')}</b>\n\n"
        f"\U0001f465 <b>TOP CREATORS:</b>\n{creator_lines}\n\n"
        f"\U0001f3ac <b>WINNING FORMATS:</b>\n{format_lines}\n\n"
        f"\U0001f30a <b>BLUE OCEAN GAPS:</b>\n{opp_lines}\n\n"
        f"\U0001f4ca <b>Google Sheets:</b> {sheets_status}\n"
        f"\U0001f5a5\ufe0f <b>Dashboard:</b> \u2705 <code>output/dashboards/{dash_path}</code>\n\n"
        f"\U0001f4a1 <b>Summary:</b> {data.get('summary','')[:200]}\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "<i>BRAINAI5 V3 \u2014 Research complete \u2705</i>"
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not NICHE_SLUG:
        log("ERROR", "No slug — set NICHE_SLUG env var or pass as argument")
        sys.exit(1)

    log("DEEPDIVE", f"Starting Phase 2 for slug: {NICHE_SLUG}")
    tg_send(f"\U0001f50d <b>Deep dive starting for:</b> <b>{NICHE_SLUG}</b>...")

    # 1. Load report
    try:
        report_path = find_report(NICHE_SLUG)
    except FileNotFoundError as e:
        msg = f"\u274c Deep dive failed: {e}"
        log("ERROR", str(e))
        tg_send(msg)
        sys.exit(1)

    log("DEEPDIVE", f"Report: {report_path}")
    data = json.loads(report_path.read_text(encoding="utf-8"))

    # 2. Update Google Sheets
    log("SHEETS", "Updating...")
    sheets_rc, sheets_out = run_sub(HERE / "sheets_updater.py", str(report_path))
    print(sheets_out)
    sheets_ok = sheets_rc == 0
    if not sheets_ok:
        log("SHEETS", f"Warning (rc={sheets_rc}) — continuing")

    # 3. Generate HTML dashboard
    log("DASHBOARD", "Generating...")
    dash_rc, dash_out = run_sub(HERE / "dashboard_gen.py", str(report_path))
    print(dash_out)
    if dash_rc != 0:
        log("DASHBOARD", f"Warning (rc={dash_rc})")

    # 4. Send Telegram full report
    report_text = build_full_report(data, sheets_ok)
    tg_send(report_text)

    log("DEEPDIVE", "Done \u2705")


if __name__ == "__main__":
    main()
