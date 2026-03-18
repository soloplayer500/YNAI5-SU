"""
assemble.py — FFmpeg video assembly.
shots (clips + text overlays) + VO audio -> final 9:16 MP4.
Clip durations are scaled to exactly match VO audio length so audio never cuts early.
"""
import subprocess
import tempfile
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

FFMPEG = config.FFMPEG_PATH
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")


def _get_vo_duration(vo_path: Path) -> float:
    """Use ffprobe to get exact audio duration in seconds."""
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_streams", str(vo_path)],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if "duration" in stream:
                return float(stream["duration"])
    except Exception as e:
        print(f"  [assemble] ffprobe error: {e} — using fallback duration")
    return 30.0  # fallback


def _scale_shot_durations(shots: list, vo_duration: float) -> list:
    """
    Scale shot durations proportionally so total video = VO duration.
    Adds 0.5s tail buffer so last clip doesn't hard-cut on final word.
    """
    target = vo_duration + 0.5
    raw_total = sum(float(s.get("duration", 2.5)) for s in shots)
    scale = target / raw_total if raw_total > 0 else 1.0
    scaled = []
    for s in shots:
        new_s = dict(s)
        new_s["duration"] = round(float(s.get("duration", 2.5)) * scale, 2)
        scaled.append(new_s)
    total = sum(s["duration"] for s in scaled)
    print(f"  [assemble] VO={vo_duration:.1f}s | raw shots={raw_total:.1f}s | scaled={total:.1f}s (x{scale:.2f})")
    return scaled


def _run(cmd: list, label: str) -> bool:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"  [assemble] {label} FAILED:\n{result.stderr[-800:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  [assemble] {label} timed out")
        return False
    except Exception as e:
        print(f"  [assemble] {label} error: {e}")
        return False


def _esc(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")   # replace apostrophe with right single quote
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    # Keep only printable ASCII
    import re
    text = re.sub(r"[^\x20-\x7E]", "", text)
    return text


def _wrap_caption(text: str, max_chars: int = 38) -> str:
    """
    Wrap caption text to max_chars per line using FFmpeg newline syntax.
    Keeps font readable on both phone and desktop.
    FFmpeg drawtext uses literal \\n for newlines in the text string.
    """
    import textwrap
    lines = textwrap.wrap(text, width=max_chars, break_long_words=False)
    # Cap at 3 lines to avoid overflow
    return "\\n".join(lines[:3])


def _font_esc(path: str) -> str:
    """Escape font path for FFmpeg drawtext on Windows (colon after drive letter)."""
    # Replace C: with C\: so FFmpeg doesn't treat it as option separator
    import re
    return re.sub(r"^([A-Za-z]):", r"\1\\:", path.replace("\\", "/"))


def _process_shot(clip_path, text_overlay: str, duration: float,
                  tmp_dir: Path, idx: int, shot: dict = None) -> Path:
    """Scale/crop clip to 1080x1920, trim, add text overlay. Returns processed clip path."""
    out = tmp_dir / f"shot_{idx:02d}.mp4"
    escaped = _esc(text_overlay)
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    FPS = config.VIDEO_FPS
    font = _font_esc(config.FONT_PATH)
    font_size = config.FONT_SIZE
    tint = 0.20  # 20% dark purple overlay

    # Centre card — bold short overlay (max 6 words)
    drawtext = (
        f"drawtext=fontfile='{font}'"
        f":text='{escaped}'"
        f":fontcolor=white:fontsize={font_size}"
        f":x=(w-text_w)/2:y=(h-text_h)/2"
        f":shadowcolor=black:shadowx=3:shadowy=3"
        f":box=1:boxcolor=black@0.45:boxborderw=12"
    )

    # Bottom caption — wrapped spoken line, bold and readable on all screens
    raw_caption = shot.get("line", text_overlay) if isinstance(shot, dict) else text_overlay
    caption_text = _esc(_wrap_caption(raw_caption, max_chars=32))
    caption = (
        f"drawtext=fontfile='{font}'"
        f":text='{caption_text}'"
        f":fontcolor=white:fontsize=46"
        f":x=(w-text_w)/2:y=h-text_h-180"
        f":shadowcolor=black:shadowx=3:shadowy=3"
        f":line_spacing=8"
        f":box=1:boxcolor=black@0.6:boxborderw=14"
    )

    if clip_path and Path(clip_path).exists() and Path(clip_path).stat().st_size > 5000:
        # Scale/crop existing clip + centre overlay + bottom caption
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},"
            f"drawbox=x=0:y=0:w=iw:h=ih:color=0x1a0a2e@{tint}:t=fill,"
            f"{drawtext},"
            f"{caption}"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", "0", "-i", str(clip_path),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            str(out)
        ]
    else:
        # Black text card (no footage) — centre overlay + bottom caption
        cmd = [
            FFMPEG, "-y",
            "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}",
            "-t", str(duration),
            "-vf", f"{drawtext},{caption}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            str(out)
        ]

    _run(cmd, f"shot {idx}")
    return out if out.exists() else None


def _make_outro(tmp_dir: Path) -> Path:
    """1s black card with 'YNAI5 WORLD' text."""
    out = tmp_dir / "outro.mp4"
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    font = _font_esc(config.FONT_PATH)
    drawtext = (
        f"drawtext=fontfile='{font}':text='YNAI5 WORLD'"
        f":fontcolor=white:fontsize=80"
        f":x=(w-text_w)/2:y=(h-text_h)/2"
    )
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={config.VIDEO_FPS}",
        "-t", "1.0",
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(out)
    ]
    _run(cmd, "outro")
    return out


def _concat(clip_paths: list, tmp_dir: Path) -> Path:
    """Concatenate clips using FFmpeg concat demuxer."""
    list_file = tmp_dir / "clips.txt"
    valid = [p for p in clip_paths if p and Path(p).exists()]
    if not valid:
        raise RuntimeError("No valid clips to concat")
    lines = [f"file '{str(p).replace(chr(92), '/')}'\n" for p in valid]
    list_file.write_text("".join(lines), encoding="utf-8")

    out = tmp_dir / "concat.mp4"
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(out)
    ]
    _run(cmd, "concat")
    return out


def assemble_video(shots: list, clip_paths: list, vo_path: Path, slug: str) -> Path:
    """
    Full assembly.
    shots: list of {text_overlay, duration, ...}
    clip_paths: list of Path|None (parallel to shots)
    vo_path: ElevenLabs MP3
    Returns: final MP4 path or None on failure
    """
    print("[assemble] Starting FFmpeg assembly...")
    out_path = config.OUTPUT_DIR / f"{config.today()}-{slug}-final.mp4"

    # Measure VO duration and scale clips to match exactly
    vo_duration = _get_vo_duration(vo_path)
    shots = _scale_shot_durations(shots, vo_duration)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        processed = []

        for i, (shot, clip) in enumerate(zip(shots, clip_paths)):
            print(f"  [assemble] Shot {i+1}/{len(shots)}: {shot.get('text_overlay','')[:30]}")
            text = shot.get("text_overlay", f"Shot {i+1}")
            duration = float(shot.get("duration", 2.5))
            p = _process_shot(clip, text, duration, tmp_dir, i, shot=shot)
            if p:
                processed.append(p)

        # Add outro
        outro = _make_outro(tmp_dir)
        if outro and outro.exists():
            processed.append(outro)

        if not processed:
            print("[assemble] No clips processed — aborting")
            return None

        # Concatenate
        print("  [assemble] Concatenating...")
        concat = _concat(processed, tmp_dir)
        if not concat.exists():
            print("[assemble] Concat failed")
            return None

        # Mux with audio — clips already scaled to VO duration, no -shortest needed
        print("  [assemble] Muxing with VO audio...")
        cmd = [
            FFMPEG, "-y",
            "-i", str(concat),
            "-i", str(vo_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_path)
        ]
        success = _run(cmd, "final mux")

    if out_path.exists() and out_path.stat().st_size > 10000:
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"[assemble] Done -> {out_path.name} ({size_mb:.1f} MB)")
        return out_path
    else:
        print("[assemble] Output not created or too small")
        return None


if __name__ == "__main__":
    # Test with text-card-only mode (no footage needed)
    test_shots = [
        {"text_overlay": "APPLE CHOSE GOOGLE??", "duration": 2.5},
        {"text_overlay": "Siri powered by Gemini fr fr", "duration": 3.0},
        {"text_overlay": "Apple said we protect privacy", "duration": 2.5},
        {"text_overlay": "then handed it to Google lol", "duration": 2.5},
        {"text_overlay": "Siri was cooked fr fr", "duration": 2.0},
        {"text_overlay": "Google ATE no crumbs", "duration": 2.5},
        {"text_overlay": "Fight me.", "duration": 3.0},
    ]

    # Use most recent VO from audio dir
    audio_files = sorted(config.AUDIO_DIR.glob("*.mp3"))
    if not audio_files:
        print("[test] No VO file found in audio/ — run voice.py first")
        sys.exit(1)
    vo = audio_files[-1]
    print(f"[test] Using VO: {vo.name}")

    # Text cards only (no footage)
    clips = [None] * len(test_shots)
    result = assemble_video(test_shots, clips, vo, "test-assembly")
    if result:
        print(f"[test] SUCCESS: {result}")
    else:
        print("[test] FAILED")
