"""
kimi_swarm.py — YNAI5 Parallel Kimi K2.5 Dispatcher
=====================================================
Patterns:
  swarm()     — fan-out: N tasks run simultaneously, collect all results
  consensus() — same question from multiple role angles, then synthesize
  pipeline()  — Brave search → parallel Kimi analysis in one chain

Usage:
  from tools.kimi_swarm import swarm, consensus, pipeline, save_results
  OR run directly: python tools/kimi_swarm.py
"""

import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime


# ─── ENV ───────────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    env_path = Path(__file__).resolve().parent.parent / ".env.local"
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


# ─── ROLE SYSTEM PROMPTS ───────────────────────────────────────────────────────

ROLES = {
    "analyst":    "You are a sharp research analyst. Be concise, structured, data-driven. Use bullet points.",
    "strategist": "You are a business strategist. Focus on opportunities, risks, and concrete action steps.",
    "critic":     "You are a critical thinker. Challenge assumptions, find weaknesses, identify what is missing.",
    "researcher": "You are a deep researcher. Find facts, patterns, and non-obvious insights others miss.",
    "creator":    "You are a creative content strategist. Think in hooks, viral angles, and audience psychology.",
    "trader":     "You are a crypto trader. Focus on technicals, momentum, risk/reward, and entry/exit logic.",
    "default":    "You are a helpful assistant. Be concise and structured.",
}


# ─── SINGLE CALL ───────────────────────────────────────────────────────────────

def call_kimi(task: str, role: str = "analyst", system: str = None,
               max_tokens: int = 1500, env: dict = None) -> dict:
    """Single Kimi K2.5 call via OpenRouter. Returns result dict."""
    if env is None:
        env = load_env()

    api_key = env.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return {"role": role, "task": task[:80], "result": "ERROR: No OPENROUTER_API_KEY in .env.local", "tokens": 0, "cost": 0.0}

    system_prompt = system or ROLES.get(role, ROLES["default"])

    payload = json.dumps({
        "model": "moonshotai/kimi-k2.5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ],
        "max_tokens": max_tokens
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ynai5.local",
            "X-Title": "YNAI5"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        return {
            "role": role,
            "task": task[:100] + "..." if len(task) > 100 else task,
            "result": content,
            "tokens": usage.get("total_tokens", 0),
            "cost": usage.get("cost", 0.0)
        }
    except Exception as e:
        return {"role": role, "task": task[:80], "result": f"ERROR: {e}", "tokens": 0, "cost": 0.0}


# ─── PATTERN 1: FAN-OUT SWARM ──────────────────────────────────────────────────

def swarm(tasks: list, max_workers: int = 8, env: dict = None) -> list:
    """
    Fan-out: run N tasks simultaneously, return all results.

    tasks: list of strings OR list of (task, role) tuples
    Example:
      swarm(["Research X", "Research Y", "Research Z"])
      swarm([("Analyze BTC", "trader"), ("Analyze ETH", "trader")])
    """
    if env is None:
        env = load_env()

    # Normalize to (task, role) tuples
    normalized = []
    for t in tasks:
        if isinstance(t, tuple) and len(t) == 2:
            normalized.append(t)
        else:
            normalized.append((str(t), "analyst"))

    workers = min(max_workers, len(normalized))
    print(f"\n🐝 Kimi Swarm starting: {len(normalized)} tasks | {workers} parallel workers")
    print("━" * 50)

    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(call_kimi, task, role, env=env): (task, role)
            for task, role in normalized
        }
        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            results.append(r)
            status = "✅" if not r["result"].startswith("ERROR") else "❌"
            print(f"  {status} [{i}/{len(normalized)}] [{r['role']}] {r['task'][:60]}")

    total_cost = sum(r["cost"] for r in results)
    total_tokens = sum(r["tokens"] for r in results)
    print(f"━" * 50)
    print(f"🏁 Done: {total_tokens:,} tokens | ${total_cost:.4f} total cost\n")
    return results


# ─── PATTERN 2: CONSENSUS ──────────────────────────────────────────────────────

def consensus(question: str, roles: list = None, synthesize: bool = True, env: dict = None) -> dict:
    """
    Consensus: same question from multiple role perspectives, then synthesize.

    Example:
      consensus("Should I buy OPN at $0.20?", roles=["trader", "analyst", "critic"])
    """
    if env is None:
        env = load_env()
    if roles is None:
        roles = ["analyst", "strategist", "critic"]

    tasks = [(question, role) for role in roles]
    results = swarm(tasks, env=env)

    synthesis_result = None
    if synthesize:
        perspectives = "\n\n".join([
            f"### {r['role'].upper()}\n{r['result']}"
            for r in results
        ])
        synthesis_task = (
            f'You received these perspectives on: "{question}"\n\n'
            f"{perspectives}\n\n"
            f"Synthesize into ONE clear, actionable answer. Max 5 bullet points. "
            f"Flag disagreements between perspectives if any."
        )
        synthesis_result = call_kimi(synthesis_task, role="analyst", env=env)

    total_cost = sum(r["cost"] for r in results)
    if synthesis_result:
        total_cost += synthesis_result["cost"]

    return {
        "question": question,
        "perspectives": results,
        "synthesis": synthesis_result["result"] if synthesis_result else None,
        "total_cost": total_cost
    }


# ─── PATTERN 3: BRAVE + KIMI PIPELINE ─────────────────────────────────────────

def pipeline(queries: list, analysis_prompt: str, env: dict = None, role: str = "analyst") -> dict:
    """
    Brave → Kimi pipeline:
    1. Run multiple Brave searches simultaneously
    2. Feed all results to Kimi for analysis

    Example:
      pipeline(
        ["AI TikTok trends 2026", "faceless YouTube niches 2026"],
        "Based on these search results, what are the top 5 content niches?"
      )
    """
    if env is None:
        env = load_env()

    brave_key = env.get("BRAVE_SEARCH_API_KEY", "")
    search_results = []

    print(f"\n🔍 Brave search: {len(queries)} queries in parallel")

    def brave_search(query: str) -> list:
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "X-Subscription-Token": brave_key
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            results = data.get("web", {}).get("results", [])
            return [
                f"[{query}] {res.get('title', '')}: {res.get('description', '')}"
                for res in results[:4]
            ]
        except Exception as e:
            return [f"[{query}] Search error: {e}"]

    # Parallel searches
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = {executor.submit(brave_search, q): q for q in queries}
        for future in as_completed(futures):
            search_results.extend(future.result())

    print(f"  ✅ {len(search_results)} results collected → sending to Kimi")

    combined = "\n".join(search_results)
    kimi_task = f"{analysis_prompt}\n\nSearch results:\n{combined}"
    result = call_kimi(kimi_task, role=role, env=env)

    return {
        "queries": queries,
        "search_results": search_results,
        "analysis": result["result"],
        "cost": result["cost"]
    }


# ─── SAVE RESULTS ──────────────────────────────────────────────────────────────

def save_results(results: list, filename: str = None, folder: str = "notes") -> str:
    """Save swarm results to markdown file."""
    if filename is None:
        filename = f"swarm-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

    output_dir = Path(__file__).resolve().parent.parent / folder
    output_dir.mkdir(exist_ok=True)
    path = output_dir / filename

    lines = [f"# Kimi Swarm — {datetime.now().strftime('%Y-%m-%d %H:%M AST')}\n\n"]
    for r in results:
        lines.append(f"## [{r['role'].upper()}]\n")
        lines.append(f"**Task:** {r['task']}\n\n")
        lines.append(r["result"])
        lines.append(f"\n\n_Tokens: {r['tokens']} | Cost: ${r['cost']:.4f}_\n\n---\n\n")

    path.write_text("".join(lines), encoding="utf-8")
    print(f"💾 Saved → {path}")
    return str(path)


# ─── QUICK TEST ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    env = load_env()

    print("=== TEST: Fan-out Swarm (3 tasks) ===")
    results = swarm([
        ("What makes a faceless AI YouTube channel successful in 2026?", "researcher"),
        ("What are the biggest mistakes new TikTok creators make?", "critic"),
        ("What crypto coins show the strongest momentum signals right now?", "trader"),
    ], env=env)

    save_results(results, "swarm-test.md")

    print("\n=== RESULTS PREVIEW ===")
    for r in results:
        print(f"\n[{r['role'].upper()}]")
        print(r["result"][:300] + "..." if len(r["result"]) > 300 else r["result"])
