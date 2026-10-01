---
name: checkpoint
description: Save project state to docs/STATE.md so work survives /clear, compaction and new sessions. Use when a task finishes, before /clear, before stopping for the day, or when the user says checkpoint, handoff or save state.
---

# Checkpoint

1. Gather the facts:
   - Run `git status --porcelain` and `git log --oneline -5`.
   - If `.claude/state-machine/state_cli.py` exists, run `python3 .claude/state-machine/state_cli.py status`. The task states there are the truth; use them rather than memory.
2. Rewrite `docs/STATE.md` in place. Overwrite stale lines; don't append. Keep it **under 60 lines**:
   - **Current task:** path and state (from the machine). **Next step:** the single next action (one of the task's legal moves).
   - **Done:** at most 5 recent items, each with the command that verified it.
   - **Open questions** for the user, and **Known gaps** with `path:line` evidence.
   - If architecture changed, add a line under **Architecture**, and an ADR in `docs/adr/` if none exists yet.
3. For each task in `DONE`, set its spec status to `done`. If you need a progress report, run `state_cli.py report <task-id> --out docs/progress/<task-id>.md`, but only if the user wants one.
4. Reply with three lines: what was saved, the next step, and whether `/clear` is safe now. It's safe when nothing important exists only in the chat.
