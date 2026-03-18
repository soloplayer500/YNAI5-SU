# Research: Video Generation Tools for Autonomous Claude Pipeline
Date: 2026-03-16
Sources: See bottom of file

---

## Summary
Kling AI is the clear winner for an autonomous Claude → video pipeline. It is the only tool with:
- A working MCP server (mcp-kling, 13+ tools)
- A free tier (66 credits/day — ~6 videos/day free)
- Best price:quality ratio (~$0.029/sec via fal.ai)

**Seedance 2.0: AVOID.** Global launch suspended March 15, 2026 (Disney cease-and-desist + copyright disputes). No reliable API.

---

## Full Comparison Table

| Tool | Price/Free Tier | API | MCP | Quality | Autonomous? |
|---|---|---|---|---|---|
| **Kling AI** | 66 free credits/day. $6.99–$180/mo paid. API: ~$0.029/sec (fal.ai) | YES | YES — mcp-kling (github.com/199-mcp/mcp-kling) | High — 4K Kling 3.0 | ✅ FULL — Claude triggers, downloads, chains commands |
| **Runway Gen-4** | $12/mo entry. API: $0.05/sec Turbo, $0.12/sec Gen-4 | YES | YES — official (mcp.runway.team, runwayml/runway-api-mcp-server) | Very High | ✅ FULL — official MCP, most stable |
| **Sora 2** | No free tier. $20/mo min. API: $0.10–$0.50/sec | YES | NO | Very High | Partial — API yes, no MCP |
| **Hailuo 2.3** | $9.99/mo. API: ~$0.045/sec (fal.ai) | YES | NO | High | Partial — API yes, no MCP |
| **Veo 2** | No free tier. API: $0.35–$0.75/sec | YES | NO | Extremely High | Partial — Gemini API only |
| **Seedance 2.0** | ~$9.60/mo consumer. Global API: BLOCKED | BLOCKED | NO | Extremely High | ❌ — suspended globally |

---

## Recommendation: Kling AI

**Buy March 27: Kling AI Standard ($6.99/mo) or Pro ($66/mo)**

### Why:
1. **MCP server confirmed** — mcp-kling connects Claude directly to Kling. Generate, extend, download from a single Claude prompt.
2. **Free tier is unbeatable** — 66 credits/day before paying anything. Build + test entire pipeline for free.
3. **Cheapest per clip** — 30-second TikTok costs ~$0.87 via API. Sora: $3.00. Veo: $10.50–$22.50.
4. **Seedance is legally dead for now** — don't build on it.
5. **Cloud-only** — 8GB RAM laptop just runs the Claude Code process. No local compute.

### Setup on March 27:
1. Subscribe at klingai.com → get API key from developer portal
2. `claude mcp add mcp-kling` (via npm/config)
3. Pipeline: `/trend-check` → `/content-gen` → Claude calls mcp-kling → video auto-generated → upload

### Backup: Runway Gen-4 Turbo ($12/mo)
If quality > cost is the priority, Runway has the most professional MCP implementation. $0.05/sec Turbo makes 30s shorts = $1.50/clip.

---

## Real-World Case Study: AI Agent Running YouTube Channel (6 Weeks)

**Source:** DEV Community — physician-engineer, Jan 2026

Results after 6 weeks, fully autonomous:
- 52 videos published
- 30,000+ views
- 4–5% like rate (industry avg: 1–2%)
- Only 29 subscribers (sub conversion was the weak point — fixed with better CTAs)

**Architecture:**
- **Agent 1 ("Midnight"):** Research → script → video render → TTS → upload → analytics → memory update. Runs at 2AM.
- **Agent 2 ("Dusk"):** Cross-platform distribution (X, blog, promotion)
- **Memory file** = core innovation — agent accumulates learnings about what formats/lengths/topics perform best. Self-improves between sessions.

**Key learning:** 30-second videos with 85% retention outperformed 60-second videos with 50% retention. The agent discovered this on its own and adapted.

**How this maps to YNAI5:**
- Ralph Automation is already the "Midnight" equivalent
- Add Kling MCP → give Claude video generation capability
- Add TikTok MCP (github.com/Seym0n/tiktok-mcp) → live trend data + upload
- Add YouTube API → auto-publish to YT Shorts
- Result: fully autonomous pipeline matching or exceeding this case study

---

## TikTok MCP Server
- **Repo:** github.com/Seym0n/tiktok-mcp
- **What it does:** Claude can pull live TikTok trend data directly in real time
- **Free** — add to Claude Code MCP config
- **Adds to pipeline:** Real-time trend discovery without manual `/trend-check` runs

---

## Sources
- [I Let AI Agents Run My YouTube Channel for 6 Weeks](https://dev.to/wcamon/i-let-ai-agents-run-my-youtube-channel-for-6-weeks-heres-what-actually-happened-21b1)
- [mcp-kling — First MCP Server for Kling AI](https://github.com/199-mcp/mcp-kling)
- [Claude-klingAI MCP Server](https://github.com/revathi-prasad/Claude-klingAI)
- [Official Runway MCP Server](https://docs.runway.team/api/runway-mcp-server)
- [Runway MCP GitHub](https://github.com/runwayml/runway-api-mcp-server)
- [Kling AI Pricing 2026](https://aitoolanalysis.com/kling-ai-pricing/)
- [Sora 2 API Pricing 2026](https://www.aifreeapi.com/en/posts/sora-2-api-pricing-quotas)
- [ByteDance Pauses Seedance 2.0 — TechCrunch](https://techcrunch.com/2026/03/15/bytedance-reportedly-pauses-global-launch-of-its-seedance-2-0-video-generator/)
- [Seedance 2.0 Suspended — The Information](https://www.theinformation.com/articles/bytedance-suspends-launch-video-ai-model-copyright-disputes-hollywood)
- [AI Video API Pricing 2026 Comparison](https://devtk.ai/en/blog/ai-video-generation-pricing-2026/)
- [TikTok MCP Server](https://github.com/Seym0n/tiktok-mcp)
- [Unlocking Kling AI in Claude via MCP](https://skywork.ai/skypage/en/unlocking-kling-ai-boris-djordjevic-mcp-server/1979080592369242112)
