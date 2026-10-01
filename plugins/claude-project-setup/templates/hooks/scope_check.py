"""PreToolUse (strict level): while a task is active, deny edits outside its Allowed files.

The active task is the `specs/tasks/TASK-*.md` path on a docs/STATE.md line whose
status says "approved" or "in progress". Allowed files are the backticked globs
under that task's "## Allowed files" heading. No active task means no opinion.
"""
import json
import os
import re
import sys
from fnmatch import fnmatch

ALWAYS_OK = ["docs/*", "specs/*", "PROJECT-BRIEF.md", "CLAUDE.md", "*/CLAUDE.md"]
TASK_RE = re.compile(r"(specs/tasks/TASK-[\w.-]+\.md)`?\s*[:\-–]\s*.*\b(approved|in progress)\b", re.I)


def active_task(project):
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
    task = active_task(project)
    if not raw or not task or not os.path.exists(os.path.join(project, task)):
        return
    rel = os.path.relpath(os.path.realpath(os.path.join(project, raw)), project).replace(os.sep, "/")
    if rel.startswith(".."):
        return  # outside project: guard.py decides
    globs = allowed_globs(os.path.join(project, task))
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
