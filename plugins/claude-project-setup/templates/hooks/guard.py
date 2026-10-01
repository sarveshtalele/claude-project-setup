"""PreToolUse guard: deterministic file and shell guardrails.

Write/Edit/MultiEdit/NotebookEdit:
  deny  - path outside the project (temp dir excepted), always-protected path,
          or a glob listed in .claude/protected.txt
  ask   - NEW file whose path is not matched by .claude/write-allow.txt
Bash:
  deny  - destructive / exfiltration patterns, shell writes to protected config
  ask   - dependency installs, git push

Silent exit 0 = no opinion; normal permission rules then apply.
"""
import json
import os
import re
import sys
import tempfile
from fnmatch import fnmatch

ALWAYS_PROTECTED = [  # fnmatch globs on the project-relative POSIX path; "*" crosses "/"
    ".env", ".env.*", "*/.env", "*/.env.*", "*.pem", "*.key", "*secrets/*",
    ".git/*", ".claude/settings.json", ".claude/hooks/*", ".claude/protected.txt",
    ".claude/setup-manifest.json", ".claude/state-machine/.state-machine/*", ".claude/state-machine/tracker/*",
    "package-lock.json", "*/package-lock.json", "pnpm-lock.yaml", "*/pnpm-lock.yaml",
    "yarn.lock", "*/yarn.lock", "poetry.lock", "uv.lock", "Cargo.lock",
]

BASH_DENY = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME|\.\.)(\s|/?$)", "recursive delete of /, ~ or parent dir"),
    (r"\bgit\s+push\b.*(\s--force\b|\s-f\b|--force-with-lease)", "force push"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards work"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean deletes untracked files"),
    (r"(curl|wget)[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b", "piping a download into a shell"),
    (r"\bsudo\b", "sudo"),
    (r"\bchmod\s+-R\s+777\b", "world-writable permissions"),
    (r"--no-verify\b", "skipping git hooks"),
    (r"\b(cat|less|head|tail|grep|sed|awk)\b[^|;&]*\.env\b", "reading .env"),
    (r"\b(npm|pnpm|yarn)\s+publish\b", "publishing a package"),
    (r"(>|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\brm\b)[^|;&]*\.claude/(settings\.json|hooks/|protected\.txt|setup-manifest\.json)",
     "changing guardrail config from the shell"),
    (r"\buser_approved\b", "recording the user's approval yourself (only the user's own message can approve)"),
    (r"(>|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\brm\b)[^|;&]*\.state-machine/", "editing state-machine logs directly"),
]

BASH_ASK = [
    (r"\b(npm|pnpm|yarn|bun)\s+(i|install|add)\b(?!\s*$)", "dependency change (must be in the task spec)"),
    (r"\b(pip|pip3|uv|poetry)\s+(install|add)\b", "dependency change (must be in the task spec)"),
    (r"\bgit\s+push\b", "git push"),
]


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def under(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def globs_from(project, name):
    path = os.path.join(project, ".claude", name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]


def check_write(inp, project):
    raw = inp.get("file_path") or inp.get("notebook_path") or ""
    if not raw:
        return
    path = os.path.realpath(os.path.join(project, raw))
    if not under(path, project):
        if under(path, os.path.realpath(tempfile.gettempdir())):
            return
        decide("deny", f"{raw} is outside the project. Use the project or the temp dir.")
    rel = os.path.relpath(path, project).replace(os.sep, "/")
    for g in ALWAYS_PROTECTED + globs_from(project, "protected.txt"):
        if fnmatch(rel, g):
            decide("deny", f"{rel} is protected ({g}). Ask the user to change it.")
    if os.path.exists(path):
        return
    if not any(fnmatch(rel, g) for g in globs_from(project, "write-allow.txt")):
        decide("ask", f"New file {rel} is outside .claude/write-allow.txt. Confirm the name and location.")


def check_bash(cmd):
    for pat, why in BASH_DENY:
        if re.search(pat, cmd):
            decide("deny", f"Blocked: {why}. Ask the user to run it themselves if intended.")
    for pat, why in BASH_ASK:
        if re.search(pat, cmd):
            decide("ask", f"Needs approval: {why}.")


def main():
    data = json.load(sys.stdin)
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        check_write(inp, project)
    elif tool == "Bash":
        check_bash(inp.get("command", ""))


if __name__ == "__main__":
    main()
