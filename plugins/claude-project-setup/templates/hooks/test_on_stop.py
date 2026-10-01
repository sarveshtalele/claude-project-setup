"""Stop hook (strict level): if code changed, run the fast test command before the turn ends.

Failure sends Claude back once (stop_hook_active prevents loops) with the last lines of output.
"""
import json
import os
import shlex
import subprocess
import sys

FAST_TEST_CMD = {{FAST_TEST_CMD|json}}
TIMEOUT_S = 300  # ponytail: fixed cap; raise it if your fast suite is slower


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        porcelain = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=project,
                                   capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return
    changed = [l[3:] for l in porcelain.splitlines() if l.strip()]
    if not any(not p.startswith(("docs/", "specs/", ".claude/")) and not p.endswith(".md")
               and p.rsplit("/", 1)[-1] not in (".gitignore", ".mcp.json", ".env.example") for p in changed):
        return
    try:
        r = subprocess.run(shlex.split(FAST_TEST_CMD), cwd=project, capture_output=True, text=True,
                           timeout=TIMEOUT_S, shell=(os.name == "nt"))
    except subprocess.TimeoutExpired:
        print(json.dumps({"decision": "block", "reason": f"Fast tests timed out after {TIMEOUT_S}s: `{FAST_TEST_CMD}`."}))
        return
    except OSError as e:  # command not found: a silent pass would disable the guardrail
        print(json.dumps({"decision": "block", "reason":
              f"Fast tests could not run: `{FAST_TEST_CMD}` ({e.__class__.__name__}: {e}). Tell the user; "
              "the command must work from a plain shell in the project root (e.g. `.venv/bin/python -m pytest` or `uv run pytest`)."}))
        return
    if r.returncode != 0:
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-30:])
        print(json.dumps({"decision": "block", "reason":
              f"Fast tests failed (`{FAST_TEST_CMD}`, exit {r.returncode}). Fix or report before stopping:\n{tail}"}))


if __name__ == "__main__":
    main()
