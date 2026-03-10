---
name: research
description: Research a topic using web search, synthesize findings, and save as a dated document. Use when asked to research, look up, investigate, or find information on any topic.
argument-hint: [topic to research]
---

Research the topic: $ARGUMENTS

## Accuracy Rules (Anti-Hallucination)
- Only include facts supported by the search results — cite source URL for every key claim
- If a source contradicts another, note the disagreement — do not pick one without justification
- If information is unavailable or unclear, say so explicitly — never fill gaps with assumptions
- Restrict findings to what was actually found — no general knowledge padding

## Steps

1. Use WebSearch to find current, relevant information on the topic
2. Search at least 2-3 different angles or sources — vary search queries
3. For every key finding, note the source URL it came from
4. Synthesize the findings — identify key themes, facts, and insights
5. Save the research to `docs/YYYY-MM-DD-[topic-slug].md` using today's date
6. Update `docs/INDEX.md` with the new entry (date, topic, file path)
7. Return a concise summary in chat (5 bullet points max) — not a recap of the full doc

## Output File Format
```markdown
# Research: [Topic]
Date: YYYY-MM-DD
Sources: [list URLs used]

## Summary
[2-3 sentence executive summary]

## Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

## Details
[Expanded notes organized by theme]

## Next Steps / Follow-up
[What to research next, or actions to take based on findings]
```

Keep research actionable. End with concrete next steps or implications.
