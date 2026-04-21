#!/usr/bin/env python3
"""
router.py — YNAI5 Free Model Router v1.0
=========================================
Priority cascade (cheapest first):
  simple  → Ollama → HuggingFace → OpenRouter → Gemini → Claude
  medium  → HuggingFace → OpenRouter → Gemini → Claude
  complex → Gemini → Claude

Usage (module):
  from router import route
  result = route("Your prompt here", complexity="simple")
  # Returns: {"response": str, "model_used": str, "tier": int, "cost_usd": float}

Usage (CLI test):
  python router.py --test

Env vars required (loaded from .env or environment):
  OLLAMA_HOST        (optional, default: http://localhost:11434)
  HF_API_TOKEN       (HuggingFace Inference API — free tier)
  OPENROUTER_API_KEY (OpenRouter — use free community models)
  GEMINI_API_KEY     (Google AI Studio — free 1500 calls/day)
  ANTHROPIC_API_KEY  (Anthropic — paid, last resort only)

Adding a new model:
  1. Implement _try_yourmodel(prompt: str) -> str | None
     - Return the response string on success
     - Return None on ANY failure (exception, timeout, rate limit)
  2. Add it to the relevant tier(s) in ROUTES dict
  3. Add its cost info to MODEL_META
  4. Add required env var to the header above
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Environment ──────────────────────────────────────────────────────────────
# Load from .env if python-dotenv is available, otherwise rely on env
try:
    from dotenv import load_dotenv
    _env = Path("/ynai5_runtime/.env")
    if not _env.exists():
        _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass  # Env vars must be set externally

OLLAMA_HOST       = os.getenv("OLLAMA_HOST", "http://localhost:11434")
HF_API_TOKEN      = os.getenv("HF_API_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Brain State (RYN CORE v3) ─────────────────────────────────────────────────
# Reads ryn/brain/state.json to check which models are available.
# Falls back to True (available) if the state file cannot be read.
_BRAIN_STATE: dict = {}
_state_path = Path(__file__).parent.parent.parent / "ryn" / "brain" / "state.json"
if _state_path.exists():
    try:
        with open(_state_path, encoding="utf-8") as _f:
            _BRAIN_STATE = json.load(_f)
    except Exception:
        pass

def _model_available(name: str) -> bool:
    """Check brain state for model availability. Defaults to True if unknown."""
    return _BRAIN_STATE.get("models", {}).get(name, {}).get("available", True)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_PATH = Path(os.getenv("ROUTER_LOG", "/ynai5_runtime/logs/router.log"))
if not LOG_PATH.parent.exists():
    LOG_PATH = Path(__file__).parent / "router.log"

logging.basicConfig(level=logging.WARNING)
_router_log = logging.getLogger("ynai5.router")

def _log(model: str, complexity: str, tokens: int, cost: float, elapsed: float):
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] complexity={complexity} model={model} cost=${cost:.4f} tokens={tokens} elapsed={elapsed:.2f}s\n"
    try:
        with open(LOG_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass  # Never crash the caller due to log failure
    sys.stdout.buffer.write(f"  -> logged: {entry.strip()}\n".encode("utf-8", errors="replace"))

# ── Model metadata (for cost tracking) ────────────────────────────────────────
MODEL_META = {
    "ollama/phi3:mini":                    {"cost": 0.0,    "tier": 1},
    "huggingface/mistral-7b-instruct":     {"cost": 0.0,    "tier": 2},
    "openrouter/mistral-7b-instruct:free": {"cost": 0.0,    "tier": 3},
    "gemini/gemini-1.5-flash":             {"cost": 0.0,    "tier": 4},
    "claude/claude-haiku-4-5-20251001":    {"cost": 0.0005, "tier": 5},
}

# ── Tier 1: Ollama (local, free) ──────────────────────────────────────────────
def _try_ollama(prompt: str) -> Optional[str]:
    """Attempt local Ollama inference. Returns None if unavailable."""
    if not _model_available("ollama"):
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip() or None
    except Exception:
        return None

# ── Tier 2: HuggingFace Inference API (free) ──────────────────────────────────
def _try_huggingface(prompt: str) -> Optional[str]:
    """HuggingFace Inference API — free tier, no billing needed."""
    if not _model_available("huggingface"):
        return None
    if not HF_API_TOKEN:
        return None
    try:
        import urllib.request
        model = "mistralai/Mistral-7B-Instruct-v0.3"
        payload = json.dumps({
            "inputs": f"[INST] {prompt} [/INST]",
            "parameters": {"max_new_tokens": 512, "temperature": 0.7},
        }).encode()
        req = urllib.request.Request(
            f"https://api-inference.huggingface.co/models/{model}",
            data=payload,
            headers={
                "Authorization": f"Bearer {HF_API_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
                # Strip the prompt echo if present
                if "[/INST]" in text:
                    text = text.split("[/INST]", 1)[-1]
                return text.strip() or None
            return None
    except Exception:
        return None

# ── Tier 3: OpenRouter (free community models) ────────────────────────────────
def _try_openrouter(prompt: str) -> Optional[str]:
    """OpenRouter free tier — mistral-7b-instruct:free (truly $0/call)."""
    if not _model_available("openrouter"):
        return None
    if not OPENROUTER_API_KEY:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
        }).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/soloplayer500/YNAI5-Phase1",
                "X-Title": "YNAI5 Router",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip() or None
            return None
    except Exception:
        return None

# ── Tier 4: Gemini Flash (Google free tier, 1500/day) ─────────────────────────
def _try_gemini(prompt: str) -> Optional[str]:
    """Google Gemini 1.5 Flash — free tier, 1500 requests/day."""
    if not _model_available("gemini"):
        return None
    if not GEMINI_API_KEY:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
        }).encode()
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = " ".join(p.get("text", "") for p in parts).strip()
                return text or None
            return None
    except Exception:
        return None

# ── Tier 5: Claude Haiku (paid — last resort, tracked) ───────────────────────
def _try_claude(prompt: str) -> Optional[str]:
    """Anthropic Claude Haiku — paid fallback. Every call is logged."""
    if not _model_available("claude"):
        return None
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data.get("content", [])
            if content:
                return content[0].get("text", "").strip() or None
            return None
    except Exception:
        return None

# ── Routing Table ─────────────────────────────────────────────────────────────
# simple  = short factual queries, yes/no, quick lookups
# medium  = multi-sentence answers, explanations, summaries
# complex = deep analysis, code generation, market research
ROUTES = {
    "simple":  [_try_ollama,      _try_huggingface, _try_openrouter, _try_gemini, _try_claude],
    "medium":  [_try_huggingface, _try_openrouter,  _try_gemini,     _try_claude],
    "complex": [_try_gemini,      _try_claude],
}

_FUNC_TO_MODEL = {
    _try_ollama:       "ollama/phi3:mini",
    _try_huggingface:  "huggingface/mistral-7b-instruct",
    _try_openrouter:   "openrouter/mistral-7b-instruct:free",
    _try_gemini:       "gemini/gemini-1.5-flash",
    _try_claude:       "claude/claude-haiku-4-5-20251001",
}

# ── Public API ────────────────────────────────────────────────────────────────
def route(prompt: str, complexity: str = "simple") -> dict:
    """
    Route a prompt to the cheapest available model.

    Args:
        prompt:     The text prompt to send to the model.
        complexity: "simple" | "medium" | "complex"

    Returns:
        {
            "response":   str,   # Model's response text
            "model_used": str,   # e.g. "gemini/gemini-1.5-flash"
            "tier":       int,   # 1 (cheapest) to 5 (most expensive)
            "cost_usd":   float, # Estimated cost per call
            "elapsed_s":  float, # Wall-clock seconds
            "complexity": str,   # Echo of input complexity
        }
    """
    if complexity not in ROUTES:
        complexity = "simple"

    cascade = ROUTES[complexity]
    t0 = time.time()

    for fn in cascade:
        model_id = _FUNC_TO_MODEL[fn]
        try:
            response = fn(prompt)
        except Exception:
            response = None

        if response:
            elapsed = round(time.time() - t0, 2)
            meta = MODEL_META.get(model_id, {"cost": 0.0, "tier": 0})
            tokens = len(response.split())  # Rough token estimate
            _log(model_id, complexity, tokens, meta["cost"], elapsed)
            return {
                "response":   response,
                "model_used": model_id,
                "tier":       meta["tier"],
                "cost_usd":   meta["cost"],
                "elapsed_s":  elapsed,
                "complexity": complexity,
            }

    # All tiers exhausted
    elapsed = round(time.time() - t0, 2)
    _log("none/all-failed", complexity, 0, 0.0, elapsed)
    return {
        "response":   "ERROR: All model tiers exhausted. Check env vars and API keys.",
        "model_used": "none",
        "tier":       -1,
        "cost_usd":   0.0,
        "elapsed_s":  elapsed,
        "complexity": complexity,
    }

# ── CLI Test Mode ─────────────────────────────────────────────────────────────
def _run_tests():
    TEST_CASES = [
        ("simple",  "What is 2 + 2?"),
        ("medium",  "Explain what RSI is in 3 sentences for a crypto trader."),
        ("complex", "Analyse BTC market structure. Is now a good time to DCA? Give a 2-paragraph assessment."),
    ]

    def _p(text):
        """Print with UTF-8 encoding, safe on all platforms."""
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))

    _p("=" * 60)
    _p("YNAI5 Router -- Live Test Run")
    _p(f"Log file: {LOG_PATH}")
    _p("=" * 60)

    all_passed = True
    for complexity, prompt in TEST_CASES:
        _p(f"\n[{complexity.upper()}] {prompt[:60]}...")
        result = route(prompt, complexity=complexity)
        model = result["model_used"]
        tier  = result["tier"]
        cost  = result["cost_usd"]
        secs  = result["elapsed_s"]

        if result["tier"] == -1:
            _p(f"  [FAIL] All tiers exhausted")
            _p(f"     {result['response']}")
            all_passed = False
        else:
            _p(f"  [OK] Model: {model} (tier {tier}, ${cost:.4f}, {secs}s)")
            preview = result["response"][:120].replace("\n", " ")
            _p(f"  Response: {preview}...")

    _p("\n" + "=" * 60)
    if all_passed:
        _p("[PASS] ALL TIERS PASSED -- router.py is operational")
    else:
        _p("[WARN] Some tiers failed -- check env vars above")
    _p("=" * 60)

if __name__ == "__main__":
    if "--test" in sys.argv:
        _run_tests()
    else:
        print("Usage: python router.py --test")
        print("       from router import route  (module usage)")
        sys.exit(0)
