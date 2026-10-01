---
name: task
description: Turn a request into a one-page, approvable task spec in specs/tasks/. Use when the user asks for a feature, fix or change touching more than one file, or says plan, spec or new task. Planning only; it writes no code.
argument-hint: <short title of the change>
---

# New task: $ARGUMENTS

1. If the request contains more than one goal, list them and ask which one comes first. **One task covers one goal.**
2. Use the `explorer` agent to find the files involved. Don't read the repo yourself.
3. Ask at most 3 clarifying questions, and only about things that change the plan. Default everything else and state the defaults.
4. Copy `specs/TASK-TEMPLATE.md` to `specs/tasks/TASK-<next number>-<slug>.md` and fill it in:
   - **Allowed files:** list exact paths, including new files by name.
   - **Acceptance:** runnable commands only. A bug task must include the test that reproduces it.
   - **Non-goals:** state what is out of scope.
5. Show the task and stop. Write `approved` only after the user explicitly approves.
6. On approval: set the status to approved, update `Current task` in docs/STATE.md, then hand the task to `implementer`.
