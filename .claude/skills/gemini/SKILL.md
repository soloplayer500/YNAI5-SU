---
name: gemini
description: Use Google Gemini as a sub-agent for research, analysis, summarization,
             script generation, or second-opinion tasks. Flash model for speed (1500/day free),
             Pro model for deep analysis (100/day free). Reads key from .env.local.
argument-hint: "[task description] [input text or question] [optional: --model pro] [optional: --save]"
allowed-tools: Bash, Read
---

# Gemini Sub-Agent Skill

Call Google Gemini (Flash or Pro) as a sub-agent for tasks that benefit from a second AI perspective,
large context processing, or multimodal analysis.

## When to Use
- Second-opinion on scripts, research, or creative decisions
- Analyzing large amounts of text (Gemini has 1M token context)
- Quick research queries where you want another model's perspective
- Comparing or evaluating content at scale

## How to Invoke

When called with `/gemini [task] [input]`, run:

```bash
python ".claude/skills/gemini/gemini.py" --task "$TASK" --input "$INPUT"
```

Extract task and input from `$ARGUMENTS`. If the user provides `--model pro`, pass that flag.
If the user asks to save the output, add `--save`.

## Model Selection

| Model | Flag | Requests/Day | Best For |
|-------|------|-------------|----------|
| Gemini 2.0 Flash | `--model flash` (default) | 1,500 | Quick tasks, scripting, analysis |
| Gemini 2.5 Pro | `--model pro` | 100 | Deep research, complex analysis |

## Example Calls

**Quick research:**
```bash
python ".claude/skills/gemini/gemini.py" --task "research" --input "What are the top TikTok niches in March 2026?"
```

**Script second opinion:**
```bash
python ".claude/skills/gemini/gemini.py" --task "improve" --input "Here is my TikTok script: [script]" --save
```

**Deep analysis with Pro:**
```bash
python ".claude/skills/gemini/gemini.py" --task "analyze tokenomics" --input "OPN token: 1B supply, 200M circulating, $61M MC, $320M FDV..." --model pro
```

## Output
- Always prints to terminal
- Use `--save` to write to `notes/gemini-YYYY-MM-DD-{task}.md`

## Free Tier Limits
- Flash: 15 RPM, 1,500 RPD — covers all daily use comfortably
- Pro: 5 RPM, 100 RPD — use for important tasks only
- Check usage: https://aistudio.google.com/app/usage
