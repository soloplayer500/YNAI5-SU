#!/usr/bin/env python3
"""
rag_indexer.py — YNAI5 Lightweight RAG System
===============================================
Indexes key workspace files into a keyword-searchable JSON index.
No vector DB. No embeddings. Fast + cheap.

Usage:
  python ryn/ryn-core/rag_indexer.py --index           # Build/rebuild full index
  python ryn/ryn-core/rag_indexer.py --query "crypto"  # Test retrieval
  python ryn/ryn-core/rag_indexer.py --query "crypto" --top 3  # Top 3 results

Output:
  ryn/brain/chunks/<name>_<n>.json   — text chunks
  ryn/brain/index/index.json         — keyword index
"""

import os
import re
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent.parent  # YNAI5-SU root
BRAIN     = ROOT / "ryn" / "brain"
CHUNKS_DIR = BRAIN / "chunks"
INDEX_FILE = BRAIN / "index" / "index.json"
STATE_FILE = BRAIN / "state.json"

# ── Scan targets ──────────────────────────────────────────────────────────────
SCAN_TARGETS = [
    ROOT / "CLAUDE.md",
    ROOT / "memory" / "MEMORY.md",
    ROOT / "memory" / "preferences.md",
    ROOT / "memory" / "decisions-log.md",
    ROOT / "context" / "profile.md",
    ROOT / "context" / "current-priorities.md",
    ROOT / "context" / "goals.md",
    ROOT / "docs" / "INDEX.md",
    ROOT / "ryn" / "brain" / "memory.md",
    ROOT / "ryn" / "brain" / "session_state.md",
]

# Glob patterns for extra files
GLOB_PATTERNS = [
    ("projects/*/README.md", ROOT),
    ("docs/*.md", ROOT),
    ("sessions/*.md", ROOT),
    ("playbooks/*.md", ROOT),
]

# ── Stop words ────────────────────────────────────────────────────────────────
STOP_WORDS = {
    "that", "this", "with", "from", "have", "will", "your", "they",
    "them", "been", "were", "would", "could", "should", "there", "their",
    "what", "when", "where", "which", "while", "about", "after", "before",
    "into", "over", "also", "more", "than", "then", "each", "some",
    "only", "both", "here", "just", "like", "very", "even", "back",
    "other", "used", "make", "made", "time", "year", "need", "want",
    "using", "these", "those", "such", "same", "being", "doing",
}

# ── Chunking ──────────────────────────────────────────────────────────────────
MAX_WORDS_PER_CHUNK = 800

def chunk_by_headings(text: str, file_path: str) -> list[dict]:
    """Split text at ## headings, fall back to word-count splits."""
    sections = re.split(r'\n(?=#{1,3} )', text)
    chunks = []
    for section in sections:
        words = section.split()
        if len(words) <= MAX_WORDS_PER_CHUNK:
            if words:
                chunks.append(section.strip())
        else:
            # Sub-split long sections by word count
            while words:
                batch = words[:MAX_WORDS_PER_CHUNK]
                chunks.append(" ".join(batch))
                words = words[MAX_WORDS_PER_CHUNK:]
    return [c for c in chunks if len(c.strip()) > 20]

def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords (>4 chars, not stop words)."""
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b', text.lower())
    seen = set()
    kws = []
    for w in words:
        if w not in STOP_WORDS and w not in seen:
            seen.add(w)
            kws.append(w)
    return kws[:50]  # Cap at 50 keywords per chunk

def make_summary(text: str) -> str:
    """First non-empty line of the chunk (truncated)."""
    for line in text.splitlines():
        line = line.strip().lstrip('#').strip()
        if line:
            return line[:120]
    return text[:120]

# ── Indexer ───────────────────────────────────────────────────────────────────
def collect_files() -> list[Path]:
    """Collect all files to index."""
    files = []
    for p in SCAN_TARGETS:
        if p.exists() and p.is_file():
            files.append(p)

    for pattern, base in GLOB_PATTERNS:
        for p in sorted(base.glob(pattern)):
            if p not in files and p.exists():
                files.append(p)

    return files

def build_index():
    """Scan workspace files, chunk them, build index.json."""
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Clean old chunks
    for old in CHUNKS_DIR.glob("*.json"):
        old.unlink()

    files = collect_files()
    index_entries = []
    total_chunks = 0
    now = datetime.now(timezone.utc).isoformat()

    print(f"Indexing {len(files)} files...")

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  SKIP {file_path.name}: {e}")
            continue

        chunks = chunk_by_headings(text, str(file_path))
        rel = str(file_path.relative_to(ROOT))
        safe_name = re.sub(r'[^\w]', '_', rel)[:60]

        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{safe_name}_{i}"
            keywords = extract_keywords(chunk_text)
            word_count = len(chunk_text.split())

            # Save chunk file
            chunk_data = {
                "chunk_id": chunk_id,
                "file": rel,
                "text": chunk_text,
                "word_count": word_count,
            }
            (CHUNKS_DIR / f"{chunk_id}.json").write_text(
                json.dumps(chunk_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            # Index entry (no text — keeps index small)
            index_entries.append({
                "chunk_id": chunk_id,
                "file": rel,
                "summary": make_summary(chunk_text),
                "keywords": keywords,
                "word_count": word_count,
                "indexed_utc": now,
            })
            total_chunks += 1

        print(f"  {rel}: {len(chunks)} chunk(s)")

    # Write index
    INDEX_FILE.write_text(
        json.dumps(index_entries, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Update state.json
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            state["rag_index_ready"] = True
            state["rag_stats"] = {
                "files_indexed": len(files),
                "total_chunks": total_chunks,
                "built_utc": now,
            }
            state["updated_utc"] = now
            STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"  WARNING: could not update state.json: {e}")

    print(f"\nIndex built: {total_chunks} chunks from {len(files)} files")
    print(f"Index:  {INDEX_FILE}")
    print(f"Chunks: {CHUNKS_DIR}")

# ── Retrieval ─────────────────────────────────────────────────────────────────
def rag_query(query: str, top_k: int = 5) -> list[str]:
    """
    Search index by keyword overlap. Returns top_k chunk texts.
    Pure Python — no dependencies beyond stdlib.
    """
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"No index found. Run: python rag_indexer.py --index")

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    query_kws = set(extract_keywords(query))

    scored = []
    for entry in index:
        entry_kws = set(entry.get("keywords", []))
        score = len(query_kws & entry_kws)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    results = []
    for score, entry in scored[:top_k]:
        chunk_file = CHUNKS_DIR / f"{entry['chunk_id']}.json"
        if chunk_file.exists():
            chunk = json.loads(chunk_file.read_text(encoding="utf-8"))
            results.append(chunk["text"])
    return results

def print_query_results(query: str, top_k: int = 5):
    print(f"\nQuery: '{query}' | top_k={top_k}")
    print("-" * 60)
    results = rag_query(query, top_k)
    if not results:
        print("No results found.")
        return
    for i, text in enumerate(results, 1):
        preview = text[:300].replace("\n", " ")
        print(f"\n[{i}] {preview}...")
    print(f"\n{len(results)} result(s) returned.")

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YNAI5 RAG Indexer")
    parser.add_argument("--index", action="store_true", help="Build/rebuild the RAG index")
    parser.add_argument("--query", type=str, help="Query the RAG index")
    parser.add_argument("--top", type=int, default=5, help="Number of results (default: 5)")
    args = parser.parse_args()

    if args.index:
        build_index()
    elif args.query:
        print_query_results(args.query, top_k=args.top)
    else:
        parser.print_help()
