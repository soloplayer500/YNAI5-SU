# Research: Kimi AI (Moonshot AI) — Agent Swarms, API, YNAI5 Integration
Date: 2026-03-10
Sources:
- https://build.nvidia.com/moonshotai/kimi-k2.5/modelcard
- https://www.datacamp.com/tutorial/kimi-k2-agent-swarm-guide
- https://www.infoq.com/news/2026/02/kimi-k25-swarm/
- https://openrouter.ai/moonshotai/kimi-k2.5
- https://kimi-k2.ai/api-docs
- https://www.kimi.com/blog/kimi-k2-5
- https://huggingface.co/moonshotai/Kimi-K2.5
- https://www.together.ai/models/kimi-k2-5
- https://venturebeat.com/orchestration/moonshot-ai-debuts-kimi-k2-5-most-powerful-open-source-llm-beating-opus-4-5

---

## Summary
Kimi K2.5 is an open-source multimodal AI model released by Moonshot AI on January 27, 2026. Its standout feature is **Agent Swarm** — a self-directed orchestration system where one model dynamically spins up and coordinates up to 100 parallel sub-agents, achieving 80% runtime reduction vs single-agent execution. The API is fully OpenAI-compatible, making integration into YNAI5 straightforward with minimal code changes.

---

## Key Findings

### 1. Model: Kimi K2.5
- **Released:** January 27, 2026 (Moonshot AI, China)
- **Type:** Open-source, multimodal (text + vision + code)
- **Context window:** 256K tokens (262,144)
- **Max output:** 65,535 tokens
- **Architecture:** Mixture-of-Experts (MoE) — trillion parameters
- **Benchmarks:** Claimed to beat Claude Opus 4.5 on multiple tasks (VentureBeat, 2026)

### 2. Agent Swarm — The Key Feature
The model's headline capability. Built using **PARL (Parallel Agent Reinforcement Learning)**:

- **Orchestrator** controls the swarm — trained via RL
- **Sub-agents** are frozen copies — specialized by task
- **Up to 100 sub-agents** in parallel, **up to 1,500 coordinated steps**
- **80% reduction** in end-to-end runtime vs single agent
- **4.5x wall-clock speedup** on complex research tasks

**How it works:**
1. Orchestrator receives complex task
2. Decomposes it into parallel subtasks
3. Dynamically spawns specialized agents (e.g., "AI Researcher", "Fact Checker", "Physics Expert")
4. Agents execute in parallel, report back to orchestrator
5. Orchestrator synthesizes results

**PARL prevents two failure modes:**
- *Serial collapse*: model ignoring parallel capacity, doing tasks sequentially
- *Spurious parallelism*: spawning many agents without meaningful decomposition

**Proven use cases (from official blog):**
- Researching top YouTube creators across 100 niche domains simultaneously (spawns 100 search agents in parallel)
- Complex office productivity tasks requiring coordinated multi-step tool use
- Visual coding from UI design screenshots
- Multi-source fact verification

### 3. API — OpenAI + Anthropic Compatible
Two endpoints both work:

**Official (Moonshot AI platform):**
```
Base URL: https://platform.moonshot.ai
API Key: from platform.moonshot.ai (register → API Keys)
```

**Third-party aggregator (kimi-k2.ai):**
```
Base URL: https://kimi-k2.ai/api/v1
```

**Via OpenRouter:**
```
Model: moonshotai/kimi-k2.5
Base URL: https://openrouter.ai/api/v1
```

**Authentication options:**
```python
# OpenAI-compatible (Bearer token)
Authorization: Bearer YOUR_KIMI_API_KEY

# Anthropic-compatible (header)
X-API-Key: YOUR_KIMI_API_KEY
```

**Python (drop-in OpenAI replacement):**
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_KIMI_API_KEY",
    base_url="https://platform.moonshot.ai/v1"  # or kimi-k2.ai/api/v1
)

response = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[{"role": "user", "content": "Your task here"}],
    temperature=0.6,
    max_tokens=8192
)
```

**Available models:**
| Model | Context | Best For |
|-------|---------|----------|
| `kimi-k2` | 128K | Fast, general tasks |
| `kimi-k2-0905` | 256K | Long context, detailed analysis |
| `kimi-k2-thinking` | 256K | Deep reasoning, complex problems |
| `kimi-k2.5` | 256K | Multimodal, agent swarms, visual |

### 4. Pricing (as of March 2026)
**Via OpenRouter:**
- Input: **$0.45 / 1M tokens**
- Output: **$2.20 / 1M tokens**

**Via Moonshot official:**
- ~$0.60 / 1M input, ~$2.50 / 1M output (Codecademy source)
- **75% cost reduction** via automatic context caching (costgoat.com)

**vs Gemini Flash (our current sub-agent):**
- Gemini Flash: 1,500 free calls/day → $0 for light use
- Kimi K2.5: No confirmed free tier → **paid from first call**

**Recommendation:** Use Gemini for daily tasks (free). Reserve Kimi for heavy parallel research tasks where swarm capability justifies cost.

### 5. Visual + Code Capabilities
- Understands images, screenshots, diagrams
- Can generate code from UI mockups / screenshots
- Can analyze charts → relevant for crypto chart reading
- "Visual coding" benchmark SOTA as of release (NVIDIA NIM card)

---

## YNAI5 Integration Blueprint

### Where Kimi Fits in Our Stack

| Task | Use | Model |
|------|-----|-------|
| Quick market analysis (daily) | Gemini Flash | Free |
| Deep niche research (100 domains parallel) | Kimi Agent Swarm | Paid |
| Crypto chart reading from screenshot | Kimi K2.5 (vision) | Paid |
| Long doc analysis (256K context) | Kimi K2.5 | Paid |
| Content idea generation (parallel) | Kimi Swarm | Paid |
| TikTok script variants (5 at once) | Kimi Swarm | Paid |

### Proposed `/kimi` Skill
Similar to `/gemini` skill — wraps Kimi API:
```
/kimi [task] [input] [--model k2.5|k2-thinking|k2] [--save]
```

**Skill file:** `.claude/skills/kimi/SKILL.md`
**Key from .env.local:** `KIMI_API_KEY`
**Endpoint:** `https://platform.moonshot.ai/v1`

### Agent Swarm for YNAI5 Use Cases
1. **Niche Research Swarm** — spin 10-20 agents, each researching a different TikTok niche simultaneously
2. **Content Parallel Generation** — 5 agents each write a different TikTok script on same topic → pick best
3. **Crypto Multi-Source Verification** — 3 agents check price + news + sentiment in parallel, synthesize

---

## Limitations / Caveats

- **No confirmed free tier** — need to verify on platform.moonshot.ai after signup
- **China-based company** — API may have latency from Aruba; OpenRouter as proxy reduces this
- **Agent Swarm is not simple API calls** — it's the model's internal orchestration. You can't manually control "spawn 5 agents"; the model decides. You prompt it to use parallel research.
- **kimi-k2.ai** is an unofficial third-party aggregator — use official platform.moonshot.ai or OpenRouter for production

---

## Next Steps / Follow-up
1. **Get Kimi API key** — register at platform.moonshot.ai (check if free credits on signup)
2. **Test via OpenRouter first** — already have OpenRouter access, add OPENROUTER_API_KEY to .env.local
3. **Build `/kimi` skill** — stdlib-only, same pattern as `/gemini`
4. **First use case** — niche research swarm for social media automation (Priority 1)
5. **Chart reading** — pass CoinGecko chart screenshot to Kimi K2.5 vision for technical analysis
