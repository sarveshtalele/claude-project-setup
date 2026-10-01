---
name: checkpoint
description: Save project state to docs/STATE.md so work survives /clear, compaction and new sessions. Use when a task finishes, before /clear, before stopping for the day, or when the user says checkpoint, handoff or save state.
---

# Checkpoint

1. Run `git status --porcelain` and `git log --oneline -5`.
2. Rewrite `docs/STATE.md` in place. Overwrite stale lines; don't append. Keep it **under 60 lines**:
   - **Current task:** path and status. **Next step:** the single next action.
   - **Done:** keep at most 5 recent items, each with the command that verified it.
   - **Open questions** for the user, and **Known gaps** with `path:line` evidence.
   - If architecture changed, add a line under **Architecture**, and an ADR in `docs/adr/` if none exists yet.
3. If the task is verified, set its status in `specs/tasks/TASK-NNN-*.md` to `done`.
4. Reply with three lines: what was saved, the next step, and whether `/clear` is safe now (it is safe when nothing important exists only in the chat).
