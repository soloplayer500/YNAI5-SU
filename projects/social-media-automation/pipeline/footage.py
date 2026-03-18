"""
footage.py — Downloads stock video clips from Pexels for each shot.
Prefers portrait (9:16) clips. Falls back to landscape (will be cropped by FFmpeg).
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

PEXELS_URL = "https://api.pexels.com/videos/search"


def _search(query: str, orientation: str = "portrait") -> list:
    params = urllib.parse.urlencode({
        "query": query, "per_page": 8,
        "orientation": orientation, "size": "medium",
    })
    req = urllib.request.Request(
        f"{PEXELS_URL}?{params}",
        headers={
            "Authorization": config.PEXELS_API_KEY,
            "User-Agent": "YNAI5-Pipeline/1.0",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("videos", [])
    except Exception as e:
        print(f"  [footage] Pexels search error '{query}': {e}")
        return []


def _best_url(video: dict) -> str:
    """Pick best HD download URL from video dict."""
    files = video.get("video_files", [])
    hd = [f for f in files if f.get("quality") in ("hd", "sd") and f.get("link")]
    if not hd:
        return ""
    hd.sort(key=lambda f: f.get("width", 0), reverse=True)
    return hd[0]["link"]


def _download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YNAI5-Pipeline/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  [footage] Download failed: {e}")
        return False


def download_footage(shots: list, slug: str) -> list:
    """
    Download one clip per shot.
    Returns list of Path objects (None where download failed).
    """
    clip_dir = config.FOOTAGE_DIR / f"{config.today()}-{slug}"
    clip_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, shot in enumerate(shots):
        term = shot.get("pexels_term", "technology abstract")
        dest = clip_dir / f"shot-{i:02d}.mp4"

        if dest.exists() and dest.stat().st_size > 10000:
            print(f"  [footage] Shot {i} cached, skipping")
            paths.append(dest)
            continue

        print(f"  [footage] Shot {i}: searching '{term}'...")

        # Try portrait first, fall back to landscape, then generic fallback
        videos = _search(term, "portrait")
        if not videos:
            videos = _search(term, "landscape")
        if not videos:
            videos = _search("technology abstract", "portrait")

        if not videos:
            print(f"  [footage] No results for shot {i}")
            paths.append(None)
            continue

        # Find first video with a valid URL
        url = ""
        for v in videos:
            url = _best_url(v)
            if url:
                break

        if not url:
            print(f"  [footage] No downloadable file for shot {i}")
            paths.append(None)
            continue

        success = _download(url, dest)
        paths.append(dest if success else None)

    ok = sum(1 for p in paths if p is not None)
    print(f"[footage] Downloaded {ok}/{len(shots)} clips -> {clip_dir.name}/")
    return paths


if __name__ == "__main__":
    test_shots = [
        {"pexels_term": "apple logo neon", "duration": 2.5},
        {"pexels_term": "siri voice assistant smartphone", "duration": 3.0},
        {"pexels_term": "google search interface", "duration": 2.0},
        {"pexels_term": "person laughing phone reaction", "duration": 2.5},
        {"pexels_term": "artificial intelligence data center", "duration": 2.5},
    ]
    paths = download_footage(test_shots, "test-footage")
    for i, p in enumerate(paths):
        size = f"{p.stat().st_size // 1024} KB" if p else "FAILED"
        print(f"  Shot {i}: {p.name if p else 'None'} ({size})")
