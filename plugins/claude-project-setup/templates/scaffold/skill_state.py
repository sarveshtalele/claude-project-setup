"""Step tracking for this skill: each run is a state machine, so steps can't run out of order or skip a review.

Usage (from the project you're working in; `python` on Windows):
  python3 <skill>/scripts/skill_state.py start [--restart]     # new run (machine: skill-<name>)
  python3 <skill>/scripts/skill_state.py begin <step>          # exit 5 if it isn't this step's turn
  python3 <skill>/scripts/skill_state.py done <step>           # finish a step (exit 4 at a review gate without approval)
  python3 <skill>/scripts/skill_state.py rework <gate-step>    # reviewer asked for changes: back to the previous step
  python3 <skill>/scripts/skill_state.py approve "<user's exact words>"   # only when no approval hook is installed
  python3 <skill>/scripts/skill_state.py status | report

State lives in <project>/.claude/state-machine/.state-machine/skill-<name>/events.jsonl (the source of truth).
"""
import json
import os
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER = next((p for p in (os.path.join(SKILL, "tracker", "scripts"),
                            os.path.join(SKILL, "..", "..", "tracker", "scripts")) if os.path.isdir(p)), None)
DEF = os.path.join(SKILL, "machine.json")
APPROVAL = "user_approved"


def project():
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def tracker(script, *args):
    r = subprocess.run([sys.executable, os.path.join(TRACKER, script), *args,
                        "--state-dir", os.path.join(project(), ".claude", "state-machine")],
                       capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip(), file=sys.stderr)
    return r.returncode


def main(argv):
    if TRACKER is None:
        print(json.dumps({"error": "tracker not found (expected tracker/ in the skill or the plugin root)"}), file=sys.stderr)
        return 1
    with open(DEF, encoding="utf-8") as f:
        machine = json.load(f)
    mid = f"skill-{machine['skill']}"
    state_of = {s["id"]: s["state"] for s in machine["steps"]}
    cmd, rest = (argv[0], argv[1:]) if argv else ("status", [])
    if cmd == "start":
        return tracker("init_machine.py", "--id", mid, "--definition", DEF, *(["--force"] if "--restart" in rest else []))
    if cmd in ("begin", "done", "rework") and len(rest) == 1:
        if rest[0] not in state_of:
            print(json.dumps({"error": "unknown step", "step": rest[0], "steps": list(state_of)}), file=sys.stderr)
            return 1
        st = state_of[rest[0]]
        if cmd == "begin":
            return tracker("assert_state.py", "--id", mid, "--in", st)
        t = next((t for t in machine["transitions"] if t["from"] == st
                  and t["on"] == (f"done_{rest[0]}" if cmd == "done" else "rework")), None)
        if t is None:
            print(json.dumps({"error": f"step '{rest[0]}' has no '{cmd}' transition"}), file=sys.stderr)
            return 3
        return tracker("transition.py", "--id", mid, "--on", t["on"], "--to", t["to"])
    if cmd == "approve" and rest:
        if os.path.exists(os.path.join(project(), ".claude", "hooks", "approval_capture.py")):
            print(json.dumps({"error": "refused: this project records approvals from the user's own message. "
                                       "Ask the user to reply 'approved'."}), file=sys.stderr)
            return 6
        return tracker("transition.py", "--id", mid, "--on", APPROVAL,
                       "--data", json.dumps({"source": "skill_state approve", "text": rest[0][:120]}))
    if cmd == "status":
        return tracker("query_state.py", "--id", mid)
    if cmd == "report":
        return tracker("render_reports.py", "--id", mid)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
