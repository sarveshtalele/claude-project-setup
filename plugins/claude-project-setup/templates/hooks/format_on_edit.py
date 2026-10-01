"""PostToolUse (Edit/Write/MultiEdit): run the project's own formatter on the edited file only.

Never blocks. A formatter failure is reported to Claude as a note so it can fix the syntax.
"""
import json
import os
import shlex
import subprocess
import sys
from fnmatch import fnmatch

FORMAT_CMD = {{FORMAT_CMD|json}}      # "{file}" is replaced by the edited path
FORMAT_GLOBS = {{FORMAT_GLOBS|json}}  # only files matching these are formatted


def main():
    data = json.load(sys.stdin)
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    raw = (data.get("tool_input") or {}).get("file_path") or ""
    if not raw:
        return
    path = os.path.realpath(os.path.join(project, raw))
    rel = os.path.relpath(path, project).replace(os.sep, "/")
    if rel.startswith("..") or not any(fnmatch(rel, g) for g in FORMAT_GLOBS):
        return
    args = [a.replace("{file}", path) for a in shlex.split(FORMAT_CMD)]
    try:
        r = subprocess.run(args, cwd=project, capture_output=True, text=True, timeout=60,
                           shell=(os.name == "nt"))
    except Exception as e:  # formatter missing: tell Claude once, don't block
        print(f"format_on_edit: could not run formatter ({e})", file=sys.stderr)
        return
    if r.returncode != 0:
        tail = (r.stderr or r.stdout).strip().splitlines()[-8:]
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Formatter failed on {rel}:\n" + "\n".join(tail),
        }}))


if __name__ == "__main__":
    main()
