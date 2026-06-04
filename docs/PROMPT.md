# Session Workflow

A repeatable pattern for starting and ending every session.
Copy the relevant block into Claude at the start/end of each session.

---

## SESSION START prompt

Paste this at the beginning of each new conversation with Claude:

---
I'm continuing work on my stock-pipeline learning project.
Here's my current context:

**Project:** Stock data pipeline using Polygon.io API
**Location:** ~/projects/stock-pipeline (WSL, Ubuntu 22.04)
**Environment:** conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Learning goal:** CLI/Bash fluency + DS pipeline skills
  toward a lead DS role

**Last session summary:** See docs/SESSION_LOG.md
**Current focus:** [FILL IN — e.g. "Saving data as Parquet"]

Please pick up where we left off. I'll paste my terminal
output as we go.
---

## SESSION END checklist

Before closing each session:

1. `git status` — make sure nothing uncommitted is sitting around
2. `git add` and `git commit` any remaining work
3. `git push` — local and remote should match
4. Update `docs/SESSION_LOG.md`:
   - Fill in what was accomplished
   - Update the "upcoming" section with revised next steps
5. Commit the updated session log:
   `git add docs/SESSION_LOG.md`
   `git commit -m "Update session log after session N"`
   `git push`

## Between sessions

- Your project lives at `~/projects/stock-pipeline`
- Always open via the **Ubuntu app**, not PowerShell
- Always `conda activate stock` before running any Python
- Check `git status` before starting work — clean tree = safe starting point

## When starting a new Claude conversation

Claude loses the chat history when you start a new conversation.
The session start prompt above gives it the context it needs.
The more specific you are about what you're stuck on or trying
to do next, the faster we move.

---
*Refine this workflow as patterns emerge across sessions.*
