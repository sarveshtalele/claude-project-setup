"""Generate an Agent Skill or a Claude Code plugin (skill bundle) from a spec. Deterministic; stdlib only.

Usage:
  python3 scaffold.py --spec spec.json --target DIR [--dry-run]

Skill spec:
  {"kind": "skill", "name": "release-notes", "description": "… Use when …", "title": "Release notes",
   "summary": "one paragraph", "path": ".claude/skills/release-notes",       # optional; default .claude/skills/<name>
   "tracker": "auto|on|off",                                                   # auto = on if ≥3 steps or any gate
   "steps": [{"id": "collect", "title": "Collect commits", "do": "what to do", "gate": false}, …]}
Plugin spec:
  {"kind": "plugin", "name": "my-plugin", "description": "…", "author": "Name", "marketplace": true,
   "skills": [<skill spec without path>, …],
   "agents": [{"name": "x", "tier": "scout|builder|judge", "description": "… Use when …",
               "mission": "…", "output": "VERDICT: …"}]}

Never overwrites: any existing target file aborts the run (exit 3). Exit 2 = invalid spec. Nothing is written on error.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
SCAF = os.path.join(PLUGIN, "templates", "scaffold")
TRACKER_FILES = ["_common.py", "init_machine.py", "transition.py", "assert_state.py", "query_state.py",
                 "resume.py", "render_reports.py"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STEP_RE = re.compile(r"^[a-z][a-z0-9_]{0,30}$")
TIERS = {  # balanced-profile defaults (same table as create-agent)
    "scout": {"tools": "Read, Grep, Glob, Bash", "model": "haiku", "turns": 25, "lines": 20},
    "builder": {"tools": "Read, Grep, Glob, Edit, Write, Bash", "model": "sonnet", "turns": 50, "lines": 25},
    "judge": {"tools": "Read, Grep, Glob, Bash", "model": "inherit", "turns": 20, "lines": 15},
}


class SpecError(Exception):
    pass


def read(rel):
    with open(os.path.join(PLUGIN, rel), encoding="utf-8") as f:
        return f.read()


def check_skill(s, where):
    if not NAME_RE.match(s.get("name", "")) or len(s["name"]) > 64:
        raise SpecError(f"{where}.name must be lowercase-hyphenated, ≤ 64 chars")
    d = s.get("description", "")
    if not (40 <= len(d) <= 1024) or "use when" not in d.lower():
        raise SpecError(f"{where}.description must be 40–1024 chars and include 'Use when …'")
    steps = s.get("steps") or []
    if not steps:
        raise SpecError(f"{where}.steps must list at least one step")
    ids = [st.get("id", "") for st in steps]
    bad = [i for i in ids if not STEP_RE.match(i)]
    if bad or len(set(ids)) != len(ids):
        raise SpecError(f"{where}.steps ids must be unique snake_case (bad: {bad or 'duplicates'})")
    if steps[0].get("gate"):
        raise SpecError(f"{where}: the first step can't be a review gate (nothing to review yet)")
    if s.get("tracker", "auto") not in ("auto", "on", "off"):
        raise SpecError(f"{where}.tracker must be auto, on or off")


def tracked(s):
    t = s.get("tracker", "auto")
    return t == "on" or (t == "auto" and (len(s["steps"]) >= 3 or any(st.get("gate") for st in s["steps"])))


def machine_for(s):
    steps = [{"id": st["id"], "title": st["title"], "state": st["id"].upper(), "gate": bool(st.get("gate"))}
             for st in s["steps"]]
    tr, desc = [], {"DONE": "All steps finished."}
    for i, st in enumerate(steps):
        nxt = steps[i + 1]["state"] if i + 1 < len(steps) else "DONE"
        t = {"from": st["state"], "on": f"done_{st['id']}", "to": nxt}
        if st["gate"]:
            t.update(guard="user_approved", guardScope="since_entry")
            tr.append({"from": st["state"], "on": "rework", "to": steps[i - 1]["state"]})
        tr.insert(len(tr) - (1 if st["gate"] else 0), t)
        desc[st["state"]] = st["title"] + (" (review gate: needs the user's approval)" if st["gate"] else "")
    return {"skill": s["name"], "initial": steps[0]["state"], "steps": steps,
            "stateDescriptions": desc, "transitions": tr}


def skill_md(s, has_tracker):
    title = s.get("title") or s["name"].replace("-", " ").capitalize()
    st = 'python3 "${CLAUDE_SKILL_DIR}/scripts/skill_state.py"'
    out = ["---", f"name: {s['name']}", f"description: {json.dumps(s['description'])}", "---", "",
           f"# {title}", "", s.get("summary", "").strip() or "<One paragraph: what this skill produces and for whom.>", "",
           "## Hard rules",
           "- Run the steps in order. Don't skip, merge or reorder them.",
           "- Create or overwrite files only where the user agreed; suggest a name and ask first.",
           "- Never claim a step worked without showing the output that proves it."]
    if has_tracker:
        out += ["- Every step starts with `begin` and ends with `done`. The state machine refuses out-of-order steps "
                "(exit 5) and an unapproved review (exit 4); report it, never work around it.",
                "- At a review gate, show the result and ask the user to reply `approved` or to describe changes. "
                "Never approve on their behalf.",
                "", f"`ST` below means `{st}` (use `python` on Windows).", "",
                "## Start", "`ST start`. If a run is already in progress, `ST status` and continue from its state; "
                "use `ST start --restart` only if the user wants to start over."]
    out += ["", "## Steps"]
    for i, step in enumerate(s["steps"], 1):
        out += ["", f"### {i}. {step['title']}" + (" (review gate)" if step.get("gate") else "")]
        if has_tracker:
            out.append(f"`ST begin {step['id']}`")
        if step.get("gate"):
            out.append(step.get("do") or "Show the result of the previous step and ask: "
                       "**\"Reply `approved` to continue, or tell me what to change.\"** Then stop.")
            if has_tracker:
                out.append(f"After they approve: `ST done {step['id']}`. If they ask for changes: "
                           f"`ST rework {step['id']}`, then redo the previous step.")
        else:
            out.append(step.get("do") or "<What to do in this step, and its expected output.>")
            if has_tracker:
                out.append(f"`ST done {step['id']}`")
    if has_tracker:
        out += ["", "## Finish", "`ST report` writes `progress.md` and `changelog.md` for this run. "
                "Summarise the outputs for the user in at most 5 lines."]
    return "\n".join(out) + "\n"


def skill_files(s, base, tracker_dir):
    """{path: text} for one skill. tracker_dir: where this skill's tracker lives (None = vendored inside)."""
    has_tracker = tracked(s)
    files = {f"{base}/SKILL.md": skill_md(s, has_tracker),
             f"{base}/evals/run_evals.py": read("templates/scaffold/run_evals.py"),
             f"{base}/evals/evals.json": json.dumps({"evals": []}, indent=2) + "\n"}
    if has_tracker:
        files[f"{base}/machine.json"] = json.dumps(machine_for(s), indent=2) + "\n"
        files[f"{base}/scripts/skill_state.py"] = read("templates/scaffold/skill_state.py")
        if tracker_dir is None:
            files.update(tracker_files(f"{base}/tracker"))
    return files


def tracker_files(dest):
    files = {f"{dest}/scripts/{f}": read(f"tracker/scripts/{f}") for f in TRACKER_FILES}
    digest = hashlib.sha256("".join(files[k] for k in sorted(files)).encode()).hexdigest()
    files[f"{dest}/VERSION.json"] = json.dumps({"source": "claude-project-setup/tracker", "sha256": digest}, indent=2) + "\n"
    return files


def agent_file(a, where):
    if not NAME_RE.match(a.get("name", "")):
        raise SpecError(f"{where}.name must be lowercase-hyphenated")
    if a.get("tier") not in TIERS:
        raise SpecError(f"{where}.tier must be one of {', '.join(TIERS)}")
    if "use when" not in a.get("description", "").lower():
        raise SpecError(f"{where}.description must include 'Use when …'")
    t = TIERS[a["tier"]]
    text = read("templates/scaffold/agent.md")
    for k, v in {"AGENT_NAME": a["name"], "AGENT_DESCRIPTION": json.dumps(a["description"]),
                 "AGENT_TOOLS": a.get("tools", t["tools"]), "AGENT_MODEL": t["model"], "AGENT_TURNS": t["turns"],
                 "AGENT_MISSION": a.get("mission", "<one-line mission and its boundary>"),
                 "AGENT_LINES": t["lines"], "AGENT_OUTPUT": a.get("output", "<fixed reply format>")}.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def build(spec):
    kind = spec.get("kind")
    if kind == "skill":
        check_skill(spec, "skill")
        return skill_files(spec, spec.get("path") or f".claude/skills/{spec['name']}", None)
    if kind != "plugin":
        raise SpecError("kind must be 'skill' or 'plugin'")
    if not NAME_RE.match(spec.get("name", "")):
        raise SpecError("plugin.name must be lowercase-hyphenated")
    if len(spec.get("description", "")) < 20:
        raise SpecError("plugin.description is required (≥ 20 chars)")
    root = f"plugins/{spec['name']}" if spec.get("marketplace", True) else "."
    files, skills = {}, spec.get("skills") or []
    for i, s in enumerate(skills):
        check_skill(s, f"skills[{i}]")
        files.update(skill_files(s, f"{root}/skills/{s['name']}", tracker_dir="shared"))
    if any(tracked(s) for s in skills):
        files.update(tracker_files(f"{root}/tracker"))  # one copy shared by every skill in the plugin
    for i, a in enumerate(spec.get("agents") or []):
        files[f"{root}/agents/{a.get('name', '')}.md"] = agent_file(a, f"agents[{i}]")
    author = {"name": spec["author"]} if spec.get("author") else None
    pj = {"name": spec["name"], "version": "0.1.0", "description": spec["description"], **({"author": author} if author else {})}
    files[f"{root}/.claude-plugin/plugin.json"] = json.dumps(pj, indent=2) + "\n"
    if spec.get("marketplace", True):
        files[".claude-plugin/marketplace.json"] = json.dumps({
            "name": spec["name"], "owner": author or {"name": spec["name"]},
            "metadata": {"description": spec["description"]},
            "plugins": [{"name": spec["name"], "source": f"./{root}", "description": spec["description"]}]}, indent=2) + "\n"
        rows = "\n".join(f"| `/{spec['name']}:{s['name']}` | {s['description'].split('. ')[0]} |" for s in skills)
        arows = "\n".join(f"| `{a['name']}` | {a['tier']} | {a['description'].split('. ')[0]} |" for a in spec.get("agents") or [])
        files["README.md"] = (f"# {spec['name']}\n\n{spec['description']}\n\n## Install\n```bash\n"
                              f"claude plugin marketplace add <owner>/{spec['name']}\n```\n```bash\n"
                              f"claude plugin install {spec['name']}@{spec['name']}\n```\n\n## Skills\n| Command | Does |\n|---|---|\n"
                              f"{rows or '| | |'}\n" + (f"\n## Agents\n| Agent | Tier | Does |\n|---|---|---|\n{arows}\n" if arows else "")
                              + f"\n## Development\n```bash\nclaude plugin validate . && claude plugin validate {root}\n```\n"
                              f"Each skill's evals: `python3 {root}/skills/<skill>/evals/run_evals.py`. "
                              "Docs go in `docs/` at the repo root (not installed with the plugin).\n")
        files[".gitignore"] = "__pycache__/\n*.pyc\n.claude/state-machine/.state-machine/*/.lock\n"
    return files


def main(argv):
    flags = {a: argv[i + 1] for i, a in enumerate(argv) if a in ("--spec", "--target") and i + 1 < len(argv)}
    if "--spec" not in flags:
        print(__doc__, file=sys.stderr)
        return 2
    target = os.path.realpath(flags.get("--target", "."))
    try:
        with open(flags["--spec"], encoding="utf-8") as f:
            files = build(json.load(f))
    except (SpecError, ValueError, OSError) as e:
        print(f"SPEC ERROR: {e}", file=sys.stderr)
        return 2
    conflicts = sorted(p for p in files if os.path.exists(os.path.join(target, p)))
    for p in sorted(files):
        print(f"{'EXISTS' if p in conflicts else 'CREATE':<8} {p}")
    if conflicts:
        print(f"\nREFUSED: {len(conflicts)} file(s) already exist; nothing written. Choose another name or path.",
              file=sys.stderr)
        return 3
    if "--dry-run" in argv:
        print(f"\nDRY RUN: {len(files)} file(s) would be created.")
        return 0
    for p, text in files.items():
        path = os.path.join(target, p)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(f"\n{len(files)} file(s) created.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
