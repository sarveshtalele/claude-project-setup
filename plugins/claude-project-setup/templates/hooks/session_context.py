"""SessionStart hook (startup | resume | clear | compact).

Prints docs/STATE.md plus git branch and dirty files. SessionStart stdout is
added to Claude's context, so project state survives /clear and compaction
without depending on the conversation.
"""
import json
import os
import subprocess
import sys

MAX_LINES = 80  # ponytail: hard cap; STATE.md is meant to stay under 60 lines


def git(*args, cwd):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def main():
    try:
        source = json.load(sys.stdin).get("source", "")
    except Exception:
        source = ""
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    out = [f"## Session context ({source or 'start'})"]

    state = os.path.join(project, "docs", "STATE.md")
    if os.path.exists(state):
        with open(state, encoding="utf-8") as f:
            lines = f.read().splitlines()
        out.append("### docs/STATE.md")
        out += lines[:MAX_LINES]
        if len(lines) > MAX_LINES:
            out.append(f"... ({len(lines) - MAX_LINES} lines cut: STATE.md is too long, trim it)")
    else:
        out.append("No docs/STATE.md yet. Create it from the template before starting work.")

    branch = git("branch", "--show-current", cwd=project)
    if branch:
        dirty = git("status", "--porcelain", cwd=project).splitlines()
        out.append(f"### git: branch `{branch}`, {len(dirty)} changed file(s)")
        out += dirty[:15]
    else:
        out.append("### git: NOT a git repository. Run `git init` before editing code.")

    if source == "compact":
        out.append("Context was just compacted. Trust STATE.md and the task file over the summary.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
