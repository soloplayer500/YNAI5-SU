"""
YNAI5 Future Upgrades Scanner
==============================
Runs at SessionStart. Scans Desktop/Future Upgrades/ for image files.
If found: writes actions/pending-upgrades.md as a flag.
Claude Code reads this at session start and auto-processes all upgrade images.

Usage:
    python upgrades-scanner.py  (called by SessionStart hook)
"""

import sys
import os
import pathlib
import datetime

WORKSPACE   = pathlib.Path("C:/Users/shema/OneDrive/Desktop/YNAI5-SU")
UPGRADES_DIR = pathlib.Path("C:/Users/shema/OneDrive/Desktop/Future Upgrades")
ACTIONS_DIR  = WORKSPACE / "actions"
FLAG_FILE    = ACTIONS_DIR / "pending-upgrades.md"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def find_upgrade_images() -> list[pathlib.Path]:
    if not UPGRADES_DIR.exists():
        return []
    return [
        f for f in sorted(UPGRADES_DIR.iterdir())
        if f.suffix.lower() in IMAGE_EXTS
    ]


def write_flag(images: list[pathlib.Path]) -> None:
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Pending Upgrades",
        f"_Detected at {now} by upgrades-scanner.py_",
        "",
        f"**{len(images)} upgrade image(s) waiting in:**",
        f"`{UPGRADES_DIR}`",
        "",
        "## Images to Process",
        "",
    ]
    for img in images:
        lines.append(f"- `{img.name}`")
    lines += [
        "",
        "## Instructions for Claude",
        "",
        "1. Read each image above using the Read tool",
        "2. Understand what upgrade/feature each image describes",
        "3. Implement it immediately in the relevant skill/file/system",
        "4. After implementing ALL images, delete them from the folder",
        "5. Delete or clear this file when done",
        "",
        "> Auto-generated. Claude processes this at session start.",
    ]
    FLAG_FILE.write_text("\n".join(lines), encoding="utf-8")


def clear_flag() -> None:
    if FLAG_FILE.exists():
        FLAG_FILE.unlink()


def main() -> None:
    images = find_upgrade_images()

    if not images:
        # No upgrades — clear any stale flag
        clear_flag()
        print("[YNAI5-Upgrades] No upgrade images found. Folder is clear.")
        return

    write_flag(images)
    print(f"[YNAI5-Upgrades] {len(images)} upgrade image(s) detected!")
    print(f"[YNAI5-Upgrades] Flag written to: {FLAG_FILE}")
    print(f"[YNAI5-Upgrades] Claude will process these at session start.")
    for img in images:
        print(f"  - {img.name}")


if __name__ == "__main__":
    main()
