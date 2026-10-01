"""Evals for this skill. Stdlib only. Run: python3 <skill>/evals/run_evals.py

1. Workflow evals, derived from machine.json (if the skill tracks its steps), so they always match the skill:
   steps can't run out of order, review gates need approval, and a full run reaches DONE.
2. Your own cases from evals/evals.json: {"name", "cmd": [...], "expect_exit": 0, "expect_contains": [...]}.
   "{skill}" in a cmd is replaced with this skill's folder; each case runs in a fresh temp project.
"""
import json
import os
import subprocess
import sys
import tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(SKILL, "scripts", "skill_state.py")
failures, passed = [], 0


def run(args, project):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(args, capture_output=True, text=True, env=env, cwd=project)


def check(name, cond, detail=""):
    global passed
    if cond:
        passed += 1
    else:
        failures.append(f"{name}: {detail}")


import re  # noqa: E402

skill_md = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
fm = skill_md.split("\n---", 1)[0]
name = re.search(r"^name:\s*(\S+)", fm, re.M)
desc = re.search(r"^description:\s*(.+)$", fm, re.M)
desc_text = json.loads(desc.group(1)) if desc and desc.group(1).startswith('"') else (desc.group(1) if desc else "")
check("SKILL.md name matches folder", bool(name) and name.group(1) == os.path.basename(SKILL),
      f"name={name.group(1) if name else None}, folder={os.path.basename(SKILL)}")
check("description has 'Use when' and ≤ 1024 chars", "use when" in desc_text.lower() and len(desc_text) <= 1024)
check("SKILL.md under 500 lines", skill_md.count("\n") < 500)

if os.path.exists(STATE):
    machine = json.load(open(os.path.join(SKILL, "machine.json"), encoding="utf-8"))
    steps = machine["steps"]
    with tempfile.TemporaryDirectory() as p:
        st = lambda *a: run([sys.executable, STATE, *a], p)
        check("start", st("start").returncode == 0)
        if len(steps) > 1:
            r = st("begin", steps[1]["id"])
            check("out-of-order step refused", r.returncode == 5, f"exit {r.returncode}")
        for s in steps:
            check(f"begin {s['id']}", st("begin", s["id"]).returncode == 0)
            if s.get("gate"):
                r = st("done", s["id"])
                check(f"gate {s['id']} needs approval", r.returncode == 4, f"exit {r.returncode}")
                check(f"approve {s['id']}", st("approve", "approved (eval)").returncode == 0)
            r = st("done", s["id"])
            check(f"done {s['id']}", r.returncode == 0, r.stderr[-200:])
        r = st("status")
        check("run reaches DONE", '"current_state": "DONE"' in r.stdout, r.stdout[-200:])

cases = json.load(open(os.path.join(SKILL, "evals", "evals.json"), encoding="utf-8")).get("evals", [])
for case in cases:
    with tempfile.TemporaryDirectory() as p:
        cmd = [a.replace("{skill}", SKILL) for a in case["cmd"]]
        r = run([sys.executable if c == "python3" else c for c in cmd], p)
        ok = r.returncode == case.get("expect_exit", 0) and all(x in r.stdout for x in case.get("expect_contains", []))
        check(case["name"], ok, f"exit {r.returncode}: {(r.stdout + r.stderr)[-200:]}")

total = passed + len(failures)
print(f"{passed}/{total} evals passed")
for f in failures:
    print("FAIL:", f, file=sys.stderr)
sys.exit(1 if failures else 0)
