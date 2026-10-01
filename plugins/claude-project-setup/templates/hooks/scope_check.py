"""PreToolUse (strict level): while a task is active, deny edits outside its Allowed files.

Active tasks come from the task state machines (.claude/state-machine): any task in
APPROVED / IN_PROGRESS / VERIFYING, whose spec is specs/tasks/<task-id>.md. Projects set up
without state machines fall back to the docs/STATE.md line "specs/tasks/TASK-…md: in progress".
Allowed files are the backticked globs under the task's "## Allowed files" heading.
No active task means no opinion.
"""
import importlib.util
import json
import os
import re
import sys
from fnmatch import fnmatch

ALWAYS_OK = ["docs/*", "specs/*", "PROJECT-BRIEF.md", "CLAUDE.md", "*/CLAUDE.md"]
TASK_RE = re.compile(r"(specs/tasks/TASK-[\w.-]+\.md)`?\s*[:\-–]\s*.*\b(approved|in progress)\b", re.I)


def active_tasks(project):
    cli = os.path.join(project, ".claude", "state-machine", "state_cli.py")
    if os.path.exists(cli):
        spec = importlib.util.spec_from_file_location("state_cli", cli)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return [f"specs/tasks/{m}.md" for m in mod.active_tasks(project)]
    legacy = active_task_from_state(project)
    return [legacy] if legacy else []


def active_task_from_state(project):
    state = os.path.join(project, "docs", "STATE.md")
    if not os.path.exists(state):
        return None
    with open(state, encoding="utf-8") as f:
        for line in f:
            m = TASK_RE.search(line)
            if m:
                return m.group(1)
    return None


def allowed_globs(task_path):
    globs, inside = [], False
    with open(task_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                inside = line.strip().lower() == "## allowed files"
                continue
            if inside:
                globs += re.findall(r"`([^`]+)`", line)
    return globs


def main():
    data = json.load(sys.stdin)
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    raw = (data.get("tool_input") or {}).get("file_path") or ""
    tasks = [t for t in active_tasks(project) if os.path.exists(os.path.join(project, t))]
    if not raw or not tasks:
        return
    rel = os.path.relpath(os.path.realpath(os.path.join(project, raw)), project).replace(os.sep, "/")
    if rel.startswith(".."):
        return  # outside project: guard.py decides
    globs = [g for t in tasks for g in allowed_globs(os.path.join(project, t))]
    task = ", ".join(tasks)
    if any(fnmatch(rel, g) for g in ALWAYS_OK + globs):
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"{rel} is not in the Allowed files of {task}. "
                                    "Stop and ask the user to widen the task, or file a new one.",
    }}))


if __name__ == "__main__":
    main()
