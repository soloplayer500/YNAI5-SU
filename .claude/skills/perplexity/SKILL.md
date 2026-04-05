---
name: perplexity
description: Use Perplexity Pro as a sub-agent for real-time web research, deep analysis, or fact-checking. Returns cited answers with sources. Best for current events, market news, technical lookups that need live web data.
argument-hint: [task] [query] [--save]
---

Use Perplexity Pro API as a research sub-agent.

## Usage
`/perplexity [task] [query] [--model sonar|sonar-pro] [--save]`

- Default model: `sonar-pro` (best reasoning + citations)
- `--save` saves result to `docs/YYYY-MM-DD-perplexity-[topic].md`

## Step 1: Check API Key

Read `.env.local` and check if `PERPLEXITY_API_KEY` is set (non-empty).

If empty:
```
Perplexity API key not configured.
To add it:
1. Go to perplexity.ai/settings/api → copy key
2. Open YNAI5-KEY-INPUT.txt on Desktop → paste in SLOT_3
3. Tell me "perplexity key ready"
```
Stop here if no key.

## Step 2: Call Perplexity API

Use the Perplexity API via direct HTTP POST. The API is OpenAI-compatible:

```
POST https://api.perplexity.ai/chat/completions
Authorization: Bearer {PERPLEXITY_API_KEY}
Content-Type: application/json

{
  "model": "sonar-pro",
  "messages": [{"role": "user", "content": "{query}"}],
  "return_citations": true,
  "search_recency_filter": "week"
}
```

Use the WebFetch tool to make this request, or dispatch via Bash with curl.

## Step 3: Format Output

```markdown
## Perplexity Research: [topic]
*Model: sonar-pro | Date: YYYY-MM-DD*

[answer text]

### Sources
1. [source title](url) — excerpt
2. [source title](url) — excerpt
```

## Step 4: Save (if --save)

Save to `docs/YYYY-MM-DD-perplexity-[topic-slug].md`
Update `docs/INDEX.md` with the new entry.

## Models
| Model | Best For |
|-------|----------|
| `sonar` | Fast answers, basic research |
| `sonar-pro` | Deep analysis, complex questions, better citations |

## Example Uses
- `/perplexity research "latest BTC regulatory news this week"` — crypto news
- `/perplexity research "Perplexity API pricing and rate limits" --save` — tech research
- `/perplexity research "top TikTok AI content trends April 2026"` — trend research
