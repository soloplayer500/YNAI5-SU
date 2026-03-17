"""
run.py — YNAI5 Auto-Video Pipeline Orchestrator.
Runs daily via Windows Task Scheduler at 10:00 AM.
Chain: trend -> script -> voice -> footage -> assemble -> notify
"""
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
import notify


def run():
    start = datetime.now()
    print(f"\n{'='*55}")
    print(f"YNAI5 Auto-Video Pipeline -- {start.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    slug = trend = script = vo_path = clip_paths = output = None

    # Step 1: Trend
    try:
        print("Step 1/6 -- Trend Check")
        from trend import get_top_trend
        trend = get_top_trend()
        slug = config.slugify(trend["title"])
        print(f"  Topic: {trend['title']}")
        print(f"  Virality: {trend['virality']}/10\n")
    except Exception as e:
        notify.pipeline_error("trend", str(e))
        print(f"[FATAL] Trend failed: {e}")
        return

    # Step 2: Script
    try:
        print("Step 2/6 -- Script Generation")
        from script import generate_script, get_vo_text
        script = generate_script(trend)
        print(f"  Hook: {script['hook'][:60]}")
        print(f"  Shots: {len(script.get('shots', []))}\n")
    except Exception as e:
        notify.pipeline_error("script", str(e))
        print(f"[FATAL] Script failed: {e}")
        return

    # Step 3: Voice
    try:
        print("Step 3/6 -- Voice Generation")
        from script import get_vo_text
        from voice import generate_voice
        vo_path = generate_voice(get_vo_text(script), slug)
        print(f"  Audio: {vo_path.name}\n")
    except Exception as e:
        notify.pipeline_error("voice", str(e))
        print(f"[FATAL] Voice failed: {e}")
        return

    # Step 4: Footage (non-fatal — falls back to text cards)
    try:
        print("Step 4/6 -- Footage Download")
        from footage import download_footage
        shots = script.get("shots", [])
        clip_paths = download_footage(shots, slug)
        ok = sum(1 for p in clip_paths if p is not None)
        print(f"  {ok}/{len(shots)} clips downloaded\n")
    except Exception as e:
        print(f"[WARN] Footage failed (using text cards): {e}")
        clip_paths = [None] * len(script.get("shots", []))

    # Step 5: Assemble
    try:
        print("Step 5/6 -- Video Assembly")
        from assemble import assemble_video
        shots = script.get("shots", [])
        output = assemble_video(shots, clip_paths, vo_path, slug)
        if not output:
            raise RuntimeError("assemble_video returned None")
        print(f"  Output: {output.name}\n")
    except Exception as e:
        notify.pipeline_error("assemble", str(e))
        print(f"[FATAL] Assembly failed: {e}")
        traceback.print_exc()
        return

    # Step 6: Notify
    print("Step 6/6 -- Telegram Notification")
    notify.video_ready(trend["title"], trend["virality"], output)

    elapsed = (datetime.now() - start).seconds
    print(f"\n{'='*55}")
    print(f"Pipeline complete in {elapsed}s")
    print(f"Output: {output}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
