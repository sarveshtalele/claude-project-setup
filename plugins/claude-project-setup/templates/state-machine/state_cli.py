"""State machines for this project: the setup (bootstrap) machine and one machine per task.

Usage (from the project root; use `python` on Windows):
  python3 .claude/state-machine/state_cli.py new <id> [--kind task|bootstrap]
  python3 .claude/state-machine/state_cli.py move <id> <event>       # applies the one transition for <event>
  python3 .claude/state-machine/state_cli.py record <id> <event>     # records an event (never user_approved)
  python3 .claude/state-machine/state_cli.py status [<id>]
  python3 .claude/state-machine/state_cli.py active                  # tasks being worked on
  python3 .claude/state-machine/state_cli.py report <id> [--out progress.md]

The event log (.state-machine/<id>/events.jsonl) is the source of truth.
`user_approved` is recorded ONLY by the approval hook, from the user's own message.
Exit codes follow the tracker: 1 bad input · 2 locked · 3 illegal · 4 guard unmet · 6 refused.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKER = next((p for p in (os.path.join(HERE, "tracker", "scripts"),
                            os.path.join(HERE, "..", "..", "tracker", "scripts"))
                if os.path.isdir(p)), None)
DEFS = {"task": os.path.join(HERE, "task.json"), "bootstrap": os.path.join(HERE, "bootstrap.json")}
WORK_STATES = ("APPROVED", "IN_PROGRESS", "VERIFYING")
APPROVAL_GUARD = "user_approved"
APPROVE_RE = re.compile(r"^\s*(approved?|i approve|lgtm|go ahead|proceed|ship it|looks good)\b[\s.!,:-]*"
                        r"((?:TASK-[\w.-]+|setup|plan)\b[\s.!]*)?$", re.I)
NEGATION = re.compile(r"\b(not|don'?t|but|except|change|wait|hold|no)\b", re.I)

if TRACKER:
    sys.path.insert(0, TRACKER)
    import _common as c  # noqa: E402


def state_root(project):
    return os.path.join(project, ".claude", "state-machine")


def _tracker(script, *args, project):
    r = subprocess.run([sys.executable, os.path.join(TRACKER, script), *args, "--state-dir", state_root(project)],
                       capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _load(project, mid):
    d = c.state_dir(__import__("pathlib").Path(state_root(project)), mid)
    if not (d / "machine.json").exists():
        return None, None
    machine = c.load_json(d / "machine.json")
    return machine, c.read_events(d / "events.jsonl")


def machines(project):
    base = os.path.join(state_root(project), ".state-machine")
    return sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n))) if os.path.isdir(base) else []


def status(project, mid):
    machine, events = _load(project, mid)
    if machine is None:
        return None
    cur = c.replay_state(machine, events)
    legal = [{"on": t["on"], "to": t["to"], "guard": t.get("guard"),
              "guard_satisfied": c.guard_satisfied(t, events)} for t in machine["transitions"] if t["from"] == cur]
    return {"id": mid, "state": cur, "description": machine.get("stateDescriptions", {}).get(cur, ""), "legal": legal}


def awaiting_approval(project):
    out = []
    for mid in machines(project):
        s = status(project, mid)
        if s and any(t["guard"] == APPROVAL_GUARD and not t["guard_satisfied"] for t in s["legal"]):
            out.append(mid)
    return out


def active_tasks(project):
    return [m for m in machines(project) if m != "bootstrap" and (status(project, m) or {}).get("state") in WORK_STATES]


def capture_approval(project, prompt, only=None):
    """Called by the UserPromptSubmit hook. Returns a context message, or '' if nothing applied."""
    text = (prompt or "").strip()
    if not text or len(text) > 80 or not APPROVE_RE.match(text) or NEGATION.search(text):
        return ""
    waiting = [m for m in awaiting_approval(project) if only is None or only(m)]
    named = re.search(r"TASK-[\w.-]+", text, re.I)
    if named:
        waiting = [m for m in waiting if m.lower().startswith(named.group(0).lower().rstrip(".!"))]
    if not waiting:
        return ""
    if len(waiting) > 1:
        return ("Approval not recorded: several items await approval (" + ", ".join(waiting)
                + "). Ask the user to say e.g. 'approve " + waiting[-1] + "'.")
    mid = waiting[0]
    code, _, err = _tracker("transition.py", "--id", mid, "--on", APPROVAL_GUARD,
                            "--data", json.dumps({"source": "user-prompt", "text": text[:80]}), project=project)
    return (f"Recorded the user's approval for `{mid}` from their message. You may now run: "
            f"state_cli.py move {mid} approve" if code == 0 else f"Could not record approval for {mid}: {err[:200]}")


def main(argv):
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if TRACKER is None:
        print(json.dumps({"error": "tracker scripts not found next to state_cli.py"}), file=sys.stderr)
        return 1
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "new" and rest:
        kind = rest[rest.index("--kind") + 1] if "--kind" in rest else ("bootstrap" if rest[0] == "bootstrap" else "task")
        code, out, err = _tracker("init_machine.py", "--id", rest[0], "--definition", DEFS[kind], project=project)
    elif cmd == "move" and len(rest) == 2:
        s = status(project, rest[0])
        if s is None:
            print(json.dumps({"error": "unknown machine", "id": rest[0]}), file=sys.stderr)
            return 1
        targets = sorted({t["to"] for t in s["legal"] if t["on"] == rest[1]})
        if len(targets) != 1:
            print(json.dumps({"error": "illegal transition", "id": rest[0], "state": s["state"], "on": rest[1],
                              "legal": [t["on"] for t in s["legal"]]}), file=sys.stderr)
            return 3
        code, out, err = _tracker("transition.py", "--id", rest[0], "--on", rest[1], "--to", targets[0], project=project)
    elif cmd == "record" and len(rest) >= 2:
        if rest[1] == APPROVAL_GUARD:
            print(json.dumps({"error": "refused: user_approved is recorded only from the user's own message "
                                       "(approval hook). Ask the user to reply 'approved'."}), file=sys.stderr)
            return 6
        code, out, err = _tracker("transition.py", "--id", rest[0], "--on", rest[1], *rest[2:], project=project)
    elif cmd == "status":
        ids = rest[:1] or machines(project)
        print(json.dumps([status(project, m) for m in ids], indent=2))
        return 0
    elif cmd == "active":
        print(json.dumps(active_tasks(project)))
        return 0
    elif cmd == "report" and rest:
        args = ["--id", rest[0]]
        if "--out" in rest:
            args += ["--progress-out", rest[rest.index("--out") + 1],
                     "--changelog-out", os.path.join(state_root(project), ".state-machine", rest[0], "changelog.md")]
        code, out, err = _tracker("render_reports.py", *args, project=project)
    else:
        print(__doc__)
        return 1
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
