---
name: kimi
description: Use Kimi K2.5 (Moonshot AI) as a sub-agent for parallel research, agent swarm tasks, chart/image analysis, and long-context processing. Best for tasks where parallel execution matters. Reads KIMI_API_KEY from .env.local.
usage: /kimi [task] [input] [--model k2.5|k2-thinking|k2] [--save]
examples:
  - /kimi research "top 20 TikTok niches for faceless AI content 2026"
  - /kimi analyze "what does this crypto chart pattern suggest?" --model k2.5
  - /kimi generate "write 5 different TikTok hook scripts about AI news" --save
  - /kimi summarize "long document text here" --model k2-thinking
---

# Kimi Sub-Agent Skill

## When to Use Kimi (vs Gemini)

| Use Kimi | Use Gemini |
|----------|------------|
| Parallel/swarm research tasks | Quick daily analysis (free) |
| 100+ domain niche research | Simple Q&A, market commentary |
| Image/chart visual analysis | News summarization |
| Long doc > 32K tokens | Routine portfolio briefings |
| "Research X across many angles simultaneously" | Single-question tasks |

**Gemini Flash = free (1500/day). Kimi = paid. Default to Gemini unless swarm/vision needed.**

## Accuracy Rules (Anti-Hallucination)
- Only report what the model actually returns — never pad with assumptions
- If Kimi returns uncertain output, say so explicitly
- For financial analysis: always note this is AI analysis, not financial advice
- If API errors occur: report the error, do not fabricate a response

## Steps

### 1. Parse the Request
- Extract: task description, input text/data, model preference (default: kimi-k2.5), save flag
- Identify if this is a swarm-style task (research across many domains → tell Kimi to use parallel research)

### 2. Load API Key
Read `KIMI_API_KEY` from `.env.local` in the workspace root (`C:\Users\shema\OneDrive\Desktop\YNAI5-SU\.env.local`).

If key is missing → tell user: "Add KIMI_API_KEY=your_key to .env.local. Get a DIRECT API key from platform.moonshot.ai → API Keys section. OpenClaw integration tokens do NOT work for direct API calls."

### 3. Build the Prompt
Construct a context-aware prompt:
```
You are a specialist AI assistant working for Shami (Solo) in Aruba.
Context: Personal AI infrastructure builder, crypto monitoring, social media automation.
Goal: Revenue generation through AI-powered content automation.

Task: [user task]
Input: [user input]

[If swarm task]: Use parallel research — explore multiple angles simultaneously.
Be direct, structured, actionable. No filler.
```

### 4. Call Kimi API

**Model selection:**
- Default: `kimi-k2.5` (multimodal, agent swarm, 256K context)
- Reasoning tasks: `kimi-k2-thinking` (deep analysis, slower)
- Fast tasks: `kimi-k2` (128K context, cheaper)

**API endpoint (official):**
```python
import urllib.request, json
from pathlib import Path

def load_env():
    env = {}
    for line in Path(".env.local").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env

def call_kimi(task, model="kimi-k2.5"):
    env = load_env()
    api_key = env.get("KIMI_API_KEY", "")
    if not api_key:
        return "ERROR: KIMI_API_KEY not found in .env.local"

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": task}],
        "temperature": 0.6,
        "max_tokens": 8192
    }).encode()

    req = urllib.request.Request(
        "https://api.moonshot.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
    return result["choices"][0]["message"]["content"].strip()
```

**Fallback (OpenRouter):** If official endpoint fails, use:
```
Base URL: https://openrouter.ai/api/v1
Model: moonshotai/kimi-k2.5
Key: OPENROUTER_API_KEY from .env.local
```

### 5. Process Output
- Display the response clearly in chat
- For swarm/research tasks: structure into sections with headings
- For analysis tasks: include actionable recommendation at end

### 6. Save (if --save flag or significant output)
Save to appropriate project folder:
- Research output → `docs/YYYY-MM-DD-kimi-[topic].md`
- Content output → `projects/social-media-automation/content-tracker.md`
- Analysis → relevant project research folder

Update `docs/INDEX.md` if saved to docs/.

### 7. Report Back
Confirm in chat:
- Model used
- Tokens consumed (if available from response)
- File saved (if applicable)
- Key insight or result summary

## Agent Swarm Prompting Tips

To trigger Kimi's parallel agent mode, phrase prompts like:
```
"Research [topic] across 10 different angles simultaneously and synthesize findings."
"Analyze [X] from multiple expert perspectives in parallel: technical, financial, market, risk."
"Generate 5 different versions of [content] simultaneously, then rank them."
```

The model internally decides how to decompose and parallelize — you cannot manually control sub-agent count, but framing the task as parallel accelerates it.

## Cost Awareness
- ~$0.45/M input + $2.20/M output (OpenRouter pricing)
- A typical 2K token request + 2K response ≈ $0.006 (less than 1 cent)
- 100 swarm-style requests/day ≈ $0.60/day — use selectively
- **Always check: could Gemini Flash (free) handle this?** Only use Kimi when swarm/vision/long-context matters

## Error Handling
- 401 Unauthorized → check KIMI_API_KEY in .env.local
- 429 Rate limit → wait 60 seconds, retry once
- 503 → API down, fall back to Gemini for the task
- Timeout → increase to 120s for swarm tasks (they run longer)
