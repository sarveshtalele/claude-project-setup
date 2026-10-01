"""Stop hook: refuse to end a turn that changed code but left docs/STATE.md stale.

Forces a checkpoint, so the next session or compaction starts from accurate state.
Uses stop_hook_active to block at most once per turn (no infinite loop).
"""
import json
import os
import subprocess
import sys


NOT_CODE = (".gitignore", ".mcp.json", ".env.example")


def is_setup_or_docs(path):
    """Docs, specs, Markdown and Claude setup files don't count as code changes."""
    return (path.startswith(("docs/", "specs/", ".claude/")) or path.endswith(".md")
            or path.rsplit("/", 1)[-1] in NOT_CODE)


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        porcelain = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=project,
                                   capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return
    changed = [l[3:].strip().strip('"') for l in porcelain.splitlines() if l.strip()]
    code = [p for p in changed if not is_setup_or_docs(p)]
    if not code:
        return
    state = os.path.join(project, "docs", "STATE.md")
    state_mtime = os.path.getmtime(state) if os.path.exists(state) else 0
    newest = max((os.path.getmtime(os.path.join(project, p)) for p in code
                  if os.path.isfile(os.path.join(project, p))), default=0)
    if newest > state_mtime:
        print(json.dumps({"decision": "block", "reason":
              "Code changed after docs/STATE.md was last updated. Update 'Current task', "
              "'Next step' and 'Known gaps' in docs/STATE.md (keep it under 60 lines), then stop."}))


if __name__ == "__main__":
    main()
