# Kling AI Prompting Guide — mcp-kling Reference
_Compiled: 2026-03-29 | Source: mcp-kling tool schema + best practices_

---

## Key Finding: Plain Text, NOT JSON

Kling MCP takes **plain text prompts** as a string parameter. All other settings are **separate named params**. Do NOT embed settings inside the prompt text itself.

---

## `generate_video` Full Parameter Schema

| Param | Type | Required | Options | Default | Notes |
|-------|------|----------|---------|---------|-------|
| `prompt` | string | ✅ | — | — | Plain text, max 2500 chars |
| `negative_prompt` | string | ❌ | — | — | What to avoid, max 2500 chars |
| `model_name` | enum | ❌ | kling-v1, kling-v1.5, kling-v1.6, **kling-v2-master** | kling-v2-master | Always use v2-master for best quality |
| `duration` | enum | ❌ | "5", "10" | "5" | Use "10" for TikTok/Shorts content |
| `aspect_ratio` | enum | ❌ | "16:9", **"9:16"**, "1:1" | "16:9" | **Use 9:16 for ALL TikTok + YouTube Shorts** |
| `mode` | enum | ❌ | standard, **professional** | standard | Use professional for YNAI5 content |
| `cfg_scale` | float | ❌ | 0–1 | 0.5 | 0=more creative, 1=more literal |
| `camera_control` | object | ❌ | See below | — | V2 models only |

---

## Camera Control Options

```json
{
  "type": "forward_up",         // dramatic low-angle push forward — BEST for cinematic reveals
  "type": "down_back",          // pull back and descend — good for world reveals
  "type": "right_turn_forward", // sweeping right pan — good for panoramic shots
  "type": "left_turn_forward",  // sweeping left pan
  "type": "simple",             // manual config — full control
  "config": {
    "horizontal": 0,   // -10 to 10 (left/right)
    "vertical": 0,     // -10 to 10 (down/up)
    "zoom": -3,        // -10 to 10 (zoom out/in) — negative = pull back
    "pan": 0,          // -10 to 10 (rotate left/right)
    "tilt": 0,         // -10 to 10 (tilt up/down)
    "roll": 0          // -10 to 10 (barrel roll)
  }
}
```

---

## Best Practices

### Prompt Structure (use this order)
```
[Subject description] + [Action/state] + [Environment] + [Lighting] + [Camera movement] + [Visual style]
```

**Example:**
> "A fire elemental warrior in obsidian armor, standing motionless as lava veins pulse across the chest piece, set in a collapsed volcanic crater at dusk, dramatic god-ray lighting from below, camera drifts slowly upward from ground level, dark fantasy cinematic style, hyper-detailed, 4K"

### Prompt Length
- **Sweet spot: 100–300 words** — diminishing returns after ~500 words
- Longer ≠ better. Be specific, not verbose.
- Stack adjectives for subjects (fire, molten, obsidian, ancient) — Kling responds well

### cfg_scale by Content Type
| Content | cfg_scale | Reason |
|---------|-----------|--------|
| Fantasy / cinematic | 0.3–0.4 | More creative freedom → better atmosphere |
| Realistic / product | 0.7–0.9 | Stick close to prompt |
| YNAI5 brainrot | 0.2–0.3 | Max creative = more unexpected visual hooks |

### Standard Negative Prompt (YNAI5 default)
```
text, watermark, blurry, low quality, cartoon, 2D animation, ugly, deformed, oversaturated, noise
```

### YNAI5 Fantasy Niche — Default Settings
```
model_name: kling-v2-master
aspect_ratio: 9:16
duration: 10
mode: professional
cfg_scale: 0.4
camera_control: { type: "forward_up" }
negative_prompt: "text, watermark, blurry, low quality, cartoon, 2D animation, ugly, deformed"
```

### YNAI5 Brainrot Niche — Default Settings
```
model_name: kling-v2-master
aspect_ratio: 9:16
duration: 5
mode: standard
cfg_scale: 0.2
camera_control: { type: "simple", config: { zoom: 2, horizontal: 1 } }
```

### YNAI5 AI News Niche — Default Settings
```
model_name: kling-v2-master
aspect_ratio: 9:16
duration: 5
mode: standard
cfg_scale: 0.5
camera_control: { type: "right_turn_forward" }
```

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Putting JSON config inside prompt text | Use separate MCP params |
| Using 16:9 for TikTok/Shorts | Always use 9:16 |
| Forgetting negative_prompt | Always add — prevents watermarks/text appearing |
| cfg_scale too high for fantasy | Keep 0.3–0.5, not 0.8+ |
| Prompt > 1000 words | Cut to 200–300 — more specific, less bloat |
| Using kling-v1 for main content | Always v2-master unless testing credits |
| Not polling check_video_status | Generation takes 1–3 min — must poll to get URL |

---

## Workflow Template (copy-paste)

```python
# Step 1: Generate
result = mcp__mcp-kling__generate_video(
    prompt="[Your prompt here]",
    negative_prompt="text, watermark, blurry, low quality, cartoon, 2D animation",
    model_name="kling-v2-master",
    aspect_ratio="9:16",
    duration="10",
    mode="professional",
    cfg_scale=0.4,
    camera_control={"type": "forward_up"}
)
task_id = result.task_id

# Step 2: Poll until done (check every 30s)
status = mcp__mcp-kling__check_video_status(task_id=task_id)
# status.status: "submitted" | "processing" | "succeed" | "failed"
# status.task_result.videos[0].url  ← download URL when succeed
```

---

## Important: Web App Credits ≠ API Credits

The **$6.99/mo Standard plan** gives credits to the **web app** (klingai.com).
The **MCP/API** uses a **separate developer credit pool** — must be topped up at the Kling Developer Console.

**Fix:** Go to Kling Developer Console → top up API credits separately.
Until then: MCP video generation will return `Account balance not enough`.

## Valid Model Names (confirmed from API)
- `kling-v1` ✅
- `kling-v1.5` ✅
- `kling-v2-master` ✅
- `kling-v1.6` ❌ (invalid — not a real model name despite appearing in docs)

## camera_control Restriction
- Only works with: `kling-v1`, `standard` mode, `5s` duration
- Does NOT work with v2-master or professional mode

---

_Auto-generated reference. Update after each Kling session with new findings._
