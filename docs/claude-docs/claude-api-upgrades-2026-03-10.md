# Claude API Upgrades — Quick Reference
Source: Email "claude code upgrades" (2026-03-10) — 15 features
Status: Reviewed and categorized for YNAI5-SU integration

---

## Legend
- FREE = applies to Claude Code with no extra cost
- PAID = requires Anthropic API key (separate billing from Claude Code)
- SKIP = researched, not currently relevant

---

## Tier 1 — Paid (API Key Required) — Revisit When Revenue Comes In

| Feature | Key Concept | YNAI5 Use Case | Cost |
|---------|-------------|----------------|------|
| **Prompt Caching** | Cache system prompt → 90% cheaper on repeat calls | Cache CLAUDE.md in skill calls | 0.1x input tokens on hit |
| **Effort Parameter** | `output_config: {effort: "low/medium/high/max"}` | Low for quick lookups, high for trade analysis | Reduces token spend |
| **Adaptive Thinking** | `thinking: {type: "adaptive"}` — Claude decides when to reason | Complex PsycheCore decisions, trade evals | Opus/Sonnet 4.6 only |
| **Token Counting** | `client.messages.count_tokens()` — FREE endpoint | Pre-check cost before big API calls | Free to call |

**When ready:** Add `ANTHROPIC_API_KEY` to `.env.local`, build `/claude-api` skill with caching + effort.

---

## Tier 2 — Remote MCP Servers

| Feature | Key Concept | Status |
|---------|-------------|--------|
| **Remote MCP Servers** | Connect to GitHub, Notion, Slack etc. via MCP protocol | Via API = needs API key. Via Claude Code settings = configure locally. See `docs/2026-03-10-remote-mcp-servers.md` |

---

## Tier 3 — FREE Wins (Claude Code + Prompt Design)

### Reduce Hallucinations
- Tell Claude "if unsure, say I don't know" — drastically reduces false info
- For long docs (20K+ tokens): extract exact quotes FIRST, then analyze
- Ask Claude to cite supporting quotes for every claim — if no quote, remove the claim
- Use chain-of-thought: ask Claude to explain reasoning before final answer
- Restrict to provided documents: "only use information from the provided context, not general knowledge"

**Applied to:** `/research` skill, `/market-check` skill

### Increase Output Consistency
- Specify exact output format with JSON/XML template in the prompt
- Use structured outputs when strict JSON schema compliance is required
- Provide concrete examples of desired output format (not just descriptions)
- Break complex tasks into smaller subtasks — each gets Claude's full attention
- Use system prompt to define role + explicit rules + example scenarios

**Applied to:** All skill SKILL.md files

### Reducing Latency
- Use `claude-haiku-4-5` for speed-critical simple tasks (fastest model)
- Minimize input/output tokens — be concise in prompts
- Ask Claude directly to "be concise" or limit to N sentences/paragraphs
- Set `max_tokens` as hard limit for short-answer tasks
- Enable streaming for real-time output display (`client.messages.stream()`)
- Don't optimize prematurely — get correct output first, then optimize speed

**Applied to:** Prompt design in skills

### How to Implement Tool Use
- Define tools with clear name, description, and JSON input schema
- Tool descriptions are critical — Claude uses them to decide when to call a tool
- Keep tool names short and action-oriented (e.g., `get_price`, `search_web`)
- Use `tool_choice: "auto"` for most cases; `"required"` to force tool use
- Handle tool results by passing them back as `tool_result` content blocks

**Applied to:** Future skill design, social media automation pipeline

### Programmatic Tool Calling
- Requires code execution tool + API key — SKIP for now
- Key insight: Claude writes code to call multiple tools in one shot (no round-trips)
- **Future use**: Social media pipeline — one Claude call generates → schedules → posts

### Context Editing
- Claude Code compacts context automatically when approaching limits
- Can manually trim past messages to preserve token budget
- Keep CLAUDE.md concise — it's loaded every session, counts toward context

**Applied to:** MEMORY.md maintenance strategy — keep under 200 lines

### Context Windows
- Claude models have different context windows (varies by model)
- Thinking tokens count toward context — monitor with token counting
- Practical limit: compress MEMORY.md before it impacts session quality

### Compaction
- Automatic: Claude Code compacts when context fills up
- Manual: Can request compaction mid-session
- Impact: Compacted context loses fine detail — keep critical info in files not chat

**Applied to:** Session protocol — always save to files, not just chat

### Define Success Criteria
- Build evals: define what "correct output" looks like for each skill
- Use LLM-as-judge patterns for subjective quality (content scripts, market analysis)
- **Future**: Build eval suite for PsycheCore reasoning quality

### Evaluation Tool
- Claude Console has a built-in eval runner — test prompts across many variations
- Use for improving research, market-check, and content generation prompts
- **When to use**: After building 5+ skills, run evals to compare prompt versions

---

## Implementation Priority

| Priority | Action | Status |
|----------|--------|--------|
| ✅ Done | Read all 15 docs, categorize | Complete |
| 🔨 Now | Apply Tier 3 strategies to existing skills | This session |
| 🔨 Now | Research + add remote MCP servers to Claude Code | This session |
| ⏸ Later | Build `/claude-api` skill when API key obtained | When revenue allows |
| ⏸ Later | Token counting + prompt caching | Same time as above |

---

## Note on Remote MCP Servers (For Claude Code)
The email URL covered the API-based MCP connector (requires API key).
For Claude Code specifically, MCP servers are added via project settings — NO API key needed.
See `docs/2026-03-10-remote-mcp-servers.md` for the full setup guide.
