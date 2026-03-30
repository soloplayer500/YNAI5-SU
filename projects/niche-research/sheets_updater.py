#!/usr/bin/env python3
"""
BRAINAI5 V3 — Google Sheets Auto-Updater
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requires: pip install gspread google-auth

Env vars:
  GOOGLE_SHEETS_ID             — Sheet ID (from URL)
  GOOGLE_SERVICE_ACCOUNT_JSON  — Full JSON of service account key (GitHub Secret)

Fallback (local): credentials/service-account.json

5 tabs managed:
  Niche_Tracker     — one row per niche researched
  Creator_Tracker   — top creators per niche
  Format_Performance — winning formats
  Opportunity_Log   — blue ocean gaps
  Research_Journal  — full research log

Usage:
  python sheets_updater.py output/reports/2026-03-29-betrayal-karma.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("[SHEETS] ERROR: Run: pip install gspread google-auth")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────────
HERE      = Path(__file__).resolve().parent
SHEETS_ID = os.environ.get("GOOGLE_SHEETS_ID", "")
SA_JSON   = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_HEADERS: dict[str, list[str]] = {
    "Niche_Tracker": [
        "Date", "Niche", "Category", "Growth_Rate", "Saturation",
        "CPM_Low", "CPM_High", "Audience_M", "Blue_Ocean_Count",
        "Entry_Barrier", "Action",
    ],
    "Creator_Tracker": [
        "Date", "Niche", "Creator", "Platform",
        "Subs", "Growth_12mo", "Est_Rev_Mo", "Format_Innovation",
    ],
    "Format_Performance": [
        "Date", "Niche", "Format", "Platform",
        "Avg_Views", "CTR_Pct", "Retention_Pct", "Shares_Est", "CPM",
    ],
    "Opportunity_Log": [
        "Date", "Niche", "Opportunity", "Why",
        "Audience_M", "Barrier", "Effort_h", "RPM_Est", "Status",
    ],
    "Research_Journal": [
        "Date", "Niche", "Query", "Summary", "Decision", "Notes",
    ],
}


# ── Auth ───────────────────────────────────────────────────────────────────────
def get_client() -> gspread.Client:
    if SA_JSON:
        # GitHub Actions: secret is the raw JSON string
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(SA_JSON)
            tmp = f.name
        try:
            creds = Credentials.from_service_account_file(tmp, scopes=SCOPES)
        finally:
            Path(tmp).unlink(missing_ok=True)
    else:
        # Local dev: credentials/service-account.json
        creds_file = HERE / "credentials" / "service-account.json"
        if not creds_file.exists():
            print(f"[SHEETS] ERROR: No credentials found at {creds_file}")
            print("[SHEETS] Set GOOGLE_SERVICE_ACCOUNT_JSON env var or place service-account.json")
            sys.exit(1)
        creds = Credentials.from_service_account_file(str(creds_file), scopes=SCOPES)

    return gspread.authorize(creds)


# ── Tab management ─────────────────────────────────────────────────────────────
def ensure_tabs(sheet: gspread.Spreadsheet) -> dict[str, gspread.Worksheet]:
    """Create any missing tabs with headers. Returns {tab_name: worksheet}."""
    existing = {ws.title: ws for ws in sheet.worksheets()}
    tabs: dict[str, gspread.Worksheet] = {}

    for tab_name, headers in TAB_HEADERS.items():
        if tab_name not in existing:
            ws = sheet.add_worksheet(title=tab_name, rows=2000, cols=len(headers))
            ws.append_row(headers)
            print(f"[SHEETS] Created tab: {tab_name}", flush=True)
            tabs[tab_name] = ws
        else:
            tabs[tab_name] = existing[tab_name]

    return tabs


# ── Main update ────────────────────────────────────────────────────────────────
def update(data: dict):
    if not SHEETS_ID:
        print("[SHEETS] No GOOGLE_SHEETS_ID — skipping Sheets update")
        return

    client = get_client()
    sheet = client.open_by_key(SHEETS_ID)
    tabs = ensure_tabs(sheet)

    today = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    niche = data.get("niche", "?")
    stats = data.get("stats", {})

    # 1. Niche_Tracker — one overview row
    tabs["Niche_Tracker"].append_row([
        today,
        niche,
        data.get("category", ""),
        stats.get("growth_rate", ""),
        stats.get("saturation", ""),
        stats.get("cpm_low", ""),
        stats.get("cpm_high", ""),
        stats.get("audience_m", ""),
        len(data.get("blue_ocean", [])),
        stats.get("entry_barrier", ""),
        "YES — deep dive approved",
    ])
    print("[SHEETS] Niche_Tracker: row added", flush=True)

    # 2. Creator_Tracker — one row per creator
    for c in data.get("creators", []):
        tabs["Creator_Tracker"].append_row([
            today,
            niche,
            c.get("name", ""),
            c.get("platform", "YouTube"),
            c.get("subs", ""),
            c.get("growth_rate_12mo", ""),
            c.get("est_monthly_rev", ""),
            c.get("format_innovation", "")[:100],
        ])
    print(f"[SHEETS] Creator_Tracker: {len(data.get('creators', []))} rows added", flush=True)

    # 3. Format_Performance — one row per format
    for f in data.get("formats", []):
        tabs["Format_Performance"].append_row([
            today,
            niche,
            f.get("name", ""),
            f.get("platform", ""),
            f.get("avg_views", ""),
            f.get("ctr_pct", ""),
            f.get("retention_pct", ""),
            f.get("shares_est", ""),
            f.get("cpm", ""),
        ])
    print(f"[SHEETS] Format_Performance: {len(data.get('formats', []))} rows added", flush=True)

    # 4. Opportunity_Log — one row per blue ocean gap
    for o in data.get("blue_ocean", []):
        tabs["Opportunity_Log"].append_row([
            today,
            niche,
            o.get("name", ""),
            o.get("why", "")[:300],
            o.get("audience_m", ""),
            o.get("entry_barrier", ""),
            o.get("effort_hours", ""),
            o.get("rpm_est", ""),
            "Open",
        ])
    print(f"[SHEETS] Opportunity_Log: {len(data.get('blue_ocean', []))} rows added", flush=True)

    # 5. Research_Journal — one summary row
    tabs["Research_Journal"].append_row([
        today,
        niche,
        data.get("query", ""),
        data.get("summary", "")[:500],
        "YES — deep dive approved",
        data.get("notes", ""),
    ])
    print("[SHEETS] Research_Journal: row added", flush=True)
    print(f"[SHEETS] All 5 tabs updated for niche: {niche}", flush=True)


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sheets_updater.py <path-to-report.json>")
        sys.exit(1)
    report_file = Path(sys.argv[1])
    if not report_file.exists():
        print(f"ERROR: File not found: {report_file}")
        sys.exit(1)
    report_data = json.loads(report_file.read_text(encoding="utf-8"))
    update(report_data)
