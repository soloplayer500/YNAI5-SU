---
name: md-update
description: Review and update key markdown files (CLAUDE.md, current-priorities.md, MEMORY.md, projects/README.md, context/goals.md) with session learnings. Shows each proposed change and asks confirmation before writing. Can also merge recent sessions into MEMORY.md.
argument-hint: [optional: "all" to check all files, "memory" to focus on MEMORY.md, "priorities" to focus on current-priorities.md, or a specific filename]
---

Review key markdown files for staleness and propose updates. For each file, show what changed and ask confirmation before saving.

## Step 1: Determine Scope

If $ARGUMENTS is empty or "all" → check ALL files below.
If $ARGUMENTS is "memory" → only check memory/MEMORY.md.
If $ARGUMENTS is "priorities" → only check context/current-priorities.md.
If $ARGUMENTS is a filename → check that specific file.

## Step 2: Files to Check

For each file in scope:

### `context/current-priorities.md`
- Read the file. Compare against what happened in this session.
- Is Top Priority still accurate? Has anything been completed or shifted?
- Are payday/deadline dates still future? (if past, remove or update)
- Propose specific line-by-line edits. Show the BEFORE and AFTER for each change.
- Ask: "Update current-priorities.md with these changes? (y/n)"

### `memory/MEMORY.md`
- Read the file. Count lines — warn if approaching 200.
- What key learnings from THIS session aren't in MEMORY.md yet?
- Are any Session Index entries missing?
- Are any "Skills Available" entries missing?
- Propose additions. Show exactly what would be appended or updated.
- Ask: "Add these entries to MEMORY.md? (y/n)"
- If user said "yes": also ask "Merge recent session files into MEMORY.md? Show list of sessions/YYYY-MM-DD-session.md files not yet summarized. (y/n)"

### `CLAUDE.md`
- Read the file. Check the Workspace Map tree.
- Are there new folders/projects not shown in the tree?
- Are there new skills not listed in the Skills section?
- Is the workspace path still correct (YNAI5-SU vs YNAI5-Phase1)?
- Propose specific additions. Show what lines would change.
- Ask: "Update CLAUDE.md with these changes? (y/n)"

### `projects/README.md`
- Read the file. Check the Active Projects table.
- Are any project statuses stale (e.g., 🔨 Building but actually completed)?
- Are any new projects missing from the table?
- Propose row updates. Show the BEFORE and AFTER rows.
- Ask: "Update projects/README.md? (y/n)"

### `context/goals.md`
- Read the file. Check Q1/Q2/Q3/Q4 milestones.
- Are any milestones now completed that aren't checked off?
- Are any milestones now irrelevant (crossed off mentally but still listed)?
- Propose updates. Ask: "Update goals.md? (y/n)"

### `memory/preferences.md`
- Read the file. Were any new preferences discovered in this session that aren't listed?
- Only propose if genuinely new preferences were found.

## Step 3: Session Merge (optional)

If user confirmed MEMORY.md updates, offer:

"Want to add recent session summaries to MEMORY.md? Here are sessions not yet indexed:"
[list sessions/*.md files where date > last session in MEMORY.md Session Index]

For each selected session, extract key learnings and append to MEMORY.md Key Learnings section, then add to Session Index.

Ask confirmation before each file write.

## Step 4: Summary

After all updates, output:
```
Files updated: [list]
Files skipped: [list]
MEMORY.md line count: [N]/200
Next /md-update recommended: [suggest timeframe based on activity]
```

## Rules
- NEVER write to a file without explicit "y" confirmation from user
- Show BEFORE and AFTER for every proposed change
- If nothing needs updating in a file, say "✓ [filename] looks current — no updates needed"
- Focus on what changed THIS session vs what's already captured
- Do not add filler or reformat files — only add genuinely new/changed content
