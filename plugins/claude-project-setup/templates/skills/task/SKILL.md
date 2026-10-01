---
name: task
description: Turn a request into a one-page, approvable task spec in specs/tasks/, tracked by a task state machine. Use when the user asks for a feature, fix or change touching more than one file, or says plan, spec or new task. Planning only; it writes no code.
argument-hint: <short title of the change>
---

# New task: $ARGUMENTS

`SM` below means `python3 .claude/state-machine/state_cli.py` (use `python` on Windows). If that file doesn't exist (light level), skip every `SM` step.

1. If the request has more than one goal, list them and ask which comes first. **One task covers one goal.**
2. Use the `explorer` agent to find the files involved. Don't read the repo yourself.
3. Ask at most 3 clarifying questions, and only about things that change the plan. Default everything else and state the defaults.
4. Copy `specs/TASK-TEMPLATE.md` to `specs/tasks/TASK-<next number>-<slug>.md`. The file name without `.md` is the **task id**. Fill in:
   - **Allowed files:** exact paths, including new files by name.
   - **Acceptance:** runnable commands only. A bug task must include the test that reproduces it.
   - **Non-goals:** what's out of scope.
5. Run `SM new <task-id>`. The task starts in `PLANNED`.
6. Show the task and end with: **"Reply `approved` (or `approve <task-id>`) to start."** Then stop.
   The approval hook records the user's reply. Never record `user_approved` yourself; it is refused.
7. After they approve:
   - `SM move <task-id> approve`. Exit 4 means no approval was recorded, so ask again.
   - Set the spec's status to approved, and update `Current task` in `docs/STATE.md`.
   - Hand the task to `implementer` with the task id.

Lifecycle: `PLANNED → APPROVED → IN_PROGRESS → VERIFYING → DONE`; `fail` goes from `VERIFYING` back to `IN_PROGRESS`. `SM status <task-id>` shows the legal next steps.
