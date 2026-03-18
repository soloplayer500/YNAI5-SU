"""
YNAI5 Decision Accountability System
======================================
Manages decisions.csv — logs decisions with 30-day review dates.
Checks daily if any decisions are due for review and flags them.

Usage:
    python decision-review.py --check          (daily cron — check for reviews due)
    python decision-review.py --add            (add a new decision interactively)
    python decision-review.py --list           (list all decisions)
    python decision-review.py --list-due       (list only REVIEW DUE)
"""

import csv
import sys
import json
import datetime
import pathlib
import argparse
import os

WORKSPACE    = pathlib.Path("C:/Users/shema/OneDrive/Desktop/YNAI5-SU")
DECISIONS_CSV = WORKSPACE / "memory" / "decisions.csv"
LOG_FILE     = WORKSPACE / "memory" / "decision-review.log"
ACTIONS_DIR  = WORKSPACE / "actions"
REVIEW_FLAG  = ACTIONS_DIR / "decisions-due-for-review.md"

CSV_FIELDS = ["date", "decision", "reasoning", "expected_outcome", "review_date", "status", "actual_outcome"]


def ensure_csv() -> None:
    DECISIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not DECISIONS_CSV.exists():
        with DECISIONS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def read_decisions() -> list[dict]:
    ensure_csv()
    with DECISIONS_CSV.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_decisions(rows: list[dict]) -> None:
    with DECISIONS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def check_reviews() -> None:
    """Check for decisions past their review date. Flag them in actions/."""
    rows = read_decisions()
    today = datetime.date.today()
    due = []

    updated = []
    for row in rows:
        if row.get("status") in ("REVIEW DUE", "closed"):
            updated.append(row)
            continue
        try:
            review_date = datetime.date.fromisoformat(row["review_date"])
            if review_date <= today:
                row["status"] = "REVIEW DUE"
                due.append(row)
        except (ValueError, KeyError):
            pass
        updated.append(row)

    write_decisions(updated)

    if due:
        ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Decisions Due for Review",
            f"_Generated {today.isoformat()} — {len(due)} decision(s) need review_",
            "",
            "Review each decision below. Update actual_outcome in `memory/decisions.csv`.",
            "",
        ]
        for d in due:
            lines += [
                f"## {d['date']} — {d['decision'][:80]}",
                f"- **Reasoning:** {d['reasoning']}",
                f"- **Expected outcome:** {d['expected_outcome']}",
                f"- **Review date:** {d['review_date']}",
                f"- **Status:** {d['status']}",
                "",
            ]
        REVIEW_FLAG.write_text("\n".join(lines), encoding="utf-8")
        print(f"[Decision Review] {len(due)} decision(s) due for review!")
        print(f"[Decision Review] Flag written to: {REVIEW_FLAG}")
        log(f"CHECK: {len(due)} decisions marked REVIEW DUE")
    else:
        # Clear stale flag
        if REVIEW_FLAG.exists():
            REVIEW_FLAG.unlink()
        print(f"[Decision Review] No decisions due for review today ({today.isoformat()})")
        log(f"CHECK: No decisions due ({today.isoformat()})")


def add_decision() -> None:
    """Interactively add a new decision to decisions.csv."""
    print("\n=== Add New Decision ===")
    decision     = input("Decision (what was decided): ").strip()
    reasoning    = input("Reasoning (why this option): ").strip()
    expected     = input("Expected outcome: ").strip()
    days         = input("Review in how many days? [30]: ").strip() or "30"

    today        = datetime.date.today()
    review_date  = today + datetime.timedelta(days=int(days))

    row = {
        "date": today.isoformat(),
        "decision": decision,
        "reasoning": reasoning,
        "expected_outcome": expected,
        "review_date": review_date.isoformat(),
        "status": "active",
        "actual_outcome": "",
    }

    rows = read_decisions()
    rows.append(row)
    write_decisions(rows)
    print(f"\n✅ Decision logged. Review due: {review_date.isoformat()}")
    log(f"ADD: '{decision[:60]}' — review due {review_date.isoformat()}")


def list_decisions(due_only: bool = False) -> None:
    rows = read_decisions()
    if due_only:
        rows = [r for r in rows if r.get("status") == "REVIEW DUE"]

    if not rows:
        print("No decisions found.")
        return

    print(f"\n{'DATE':<12} {'STATUS':<12} {'DECISION':<60} {'REVIEW DATE'}")
    print("-" * 100)
    for r in rows:
        print(f"{r.get('date',''):<12} {r.get('status','active'):<12} {r.get('decision','')[:58]:<60} {r.get('review_date','')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="YNAI5 Decision Accountability System")
    parser.add_argument("--check",    action="store_true", help="Check for review due decisions")
    parser.add_argument("--add",      action="store_true", help="Add a new decision")
    parser.add_argument("--list",     action="store_true", help="List all decisions")
    parser.add_argument("--list-due", action="store_true", help="List only REVIEW DUE decisions")
    args = parser.parse_args()

    ensure_csv()

    if args.check:
        check_reviews()
    elif args.add:
        add_decision()
    elif args.list:
        list_decisions(due_only=False)
    elif getattr(args, "list_due"):
        list_decisions(due_only=True)
    else:
        check_reviews()  # default


if __name__ == "__main__":
    main()
