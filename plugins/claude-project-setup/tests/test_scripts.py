"""Plugin test suite (stdlib only). Run: python3 plugins/claude-project-setup/tests/test_scripts.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
FIX = os.path.join(HERE, "fixtures")
PY = sys.executable
results = []


def sh(args, cwd=None, inp=None, env=None):
    return subprocess.run(args, cwd=cwd, input=inp, capture_output=True, text=True, env=env)


def script(name, *args, cwd=None):
    return sh([PY, os.path.join(SCRIPTS, name), *args], cwd=cwd)


def test(fn):
    try:
        fn()
        results.append(("PASS", fn.__name__, ""))
    except AssertionError as e:
        results.append(("FAIL", fn.__name__, str(e)[:400]))
    return fn


def touch(root, rel, text="x\n"):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def plan(level="strict", **over):
    with open(os.path.join(FIX, "plan-strict.json"), encoding="utf-8") as f:
        p = json.load(f)
    p["level"] = level
    p.update(over)
    path = os.path.join(tempfile.mkdtemp(), "plan.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f)
    return path


def fresh_repo():
    t = tempfile.mkdtemp()
    sh(["git", "init", "-q"], cwd=t)
    return t


@test
def scan_greenfield_empty():
    d = json.loads(script("scan_repo.py", tempfile.mkdtemp()).stdout)
    assert d["mode"] == "greenfield" and d["source_files"] == 0, d


@test
def scan_brownfield_modules_and_frameworks():
    t = fresh_repo()
    touch(t, "package.json", json.dumps({"dependencies": {"react": "1"}, "scripts": {"test": "vitest"}}))
    touch(t, "package-lock.json", "{}")
    touch(t, "AGENTS.md", "rules")
    touch(t, "backend/pyproject.toml", "[project]\ndependencies=['fastapi']\n")
    for i in range(160):
        touch(t, f"web/src/c{i}.tsx", "export {}")
    for i in range(12):
        touch(t, f"backend/app/m{i}.py", "x=1")
    touch(t, "node_modules/x/index.js", "ignored")
    d = json.loads(script("scan_repo.py", t).stdout)
    assert d["mode"] == "brownfield" and d["has_frontend"], d
    assert {"react", "fastapi"} <= set(d["frameworks"]), d["frameworks"]
    assert d["package_managers"] == ["npm"], d["package_managers"]
    mods = {m["path"]: m["reasons"] for m in d["module_candidates"]}
    assert "backend" in mods and "own manifest" in mods["backend"], mods
    assert "web" in mods, mods
    assert "AGENTS.md" in d["instruction_files"], d["instruction_files"]
    assert not any("node_modules" in f for f in d["top_level"]), d["top_level"]


@test
def tools_classify_reuse_add_skip_conflict():
    inv = {"cli": True, "mcp": [{"name": "github", "status": "✓ Connected", "source": "cli"},
                                {"name": "weird", "status": "✗ Failed", "source": "cli"}],
           "installed": [{"id": "ponytail@ponytail", "enabled": True, "always_on_tokens": 676},
                         {"id": "terse@x", "enabled": True, "description": "terse output style", "always_on_tokens": 300},
                         {"id": "misc@x", "enabled": True, "description": "something else", "always_on_tokens": 50}],
           "available": []}
    fx = os.path.join(tempfile.mkdtemp(), "inv.json")
    json.dump(inv, open(fx, "w"))
    scan = os.path.join(tempfile.mkdtemp(), "scan.json")
    json.dump({"has_frontend": True, "manifests": [{"path": "package.json"}], "git_remote_host": "github.com", "frameworks": []}, open(scan, "w"))
    d = json.loads(script("scan_tools.py", tempfile.mkdtemp(), "--fixture", fx, "--scan", scan).stdout)
    cls = {r["id"]: r["cls"] for r in d["items"]}
    assert cls["github"] == "REUSE", cls
    assert cls["playwright"] == "ADD" and cls["context7"] == "ADD", cls
    assert cls["ponytail@ponytail"] == "CONFLICT" and cls["terse@x"] == "CONFLICT", cls
    assert cls["misc@x"] == "SKIP" and cls["weird"] == "SKIP", cls
    assert d["total_always_on_tokens"] == 1026, d["total_always_on_tokens"]


CLI = os.path.join(HERE, "..", "templates", "state-machine", "state_cli.py")
HOOK = os.path.join(HERE, "..", "templates", "hooks", "approval_capture.py")


def sm(t, *args):
    return sh([PY, CLI, *args], cwd=t, env=dict(os.environ, CLAUDE_PROJECT_DIR=t, PYTHONDONTWRITEBYTECODE="1"))


def say(t, prompt, *flags):  # the user typing a message (UserPromptSubmit hook)
    return sh([PY, HOOK, *flags], cwd=t, inp=json.dumps({"prompt": prompt}),
              env=dict(os.environ, CLAUDE_PROJECT_DIR=t, PYTHONDONTWRITEBYTECODE="1")).stdout


def approve_setup(t):
    if sm(t, "status", "bootstrap").stdout.strip() not in ("[]", "[\n  null\n]"):
        return
    sm(t, "new", "bootstrap")
    for e in ("brief_written", "answers_recorded", "plan_previewed"):
        sm(t, "move", "bootstrap", e)
    say(t, "approved", "--plugin")
    assert sm(t, "move", "bootstrap", "approve").returncode == 0


def render(t, p, *extra, approve=True):
    if approve and "--dry-run" not in extra and "--show" not in extra:
        approve_setup(t)
    return script("render.py", "--target", t, "--plan", p, *extra)


@test
def render_every_level_passes_selftest():
    for level in ("light", "standard", "strict"):
        t = fresh_repo()
        r = render(t, plan(level))
        assert r.returncode == 0, r.stderr
        st = sh([PY, ".claude/hooks/selftest.py"], cwd=t)
        assert st.returncode == 0 and st.stdout.startswith("OK"), (level, st.stdout, st.stderr)
        hooks = set(os.listdir(os.path.join(t, ".claude", "hooks")))
        assert ("scope_check.py" in hooks) == (level == "strict"), (level, hooks)
        assert ("stop_gate.py" in hooks) == (level != "light"), (level, hooks)
        leftovers = sh(["grep", "-rl", "{{", "."], cwd=t).stdout.replace("./.git", "").strip()
        assert not [l for l in leftovers.splitlines() if not l.startswith(".git")], leftovers


@test
def render_dry_run_writes_nothing():
    t = fresh_repo()
    r = render(t, plan(), "--dry-run")
    assert r.returncode == 0 and "DRY RUN" in r.stdout, r.stdout
    assert sorted(os.listdir(t)) == [".git"], os.listdir(t)


@test
def render_is_idempotent_and_respects_edits():
    t = fresh_repo()
    p = plan()
    render(t, p)
    again = render(t, p).stdout
    assert "CREATE" not in again and "MERGE" not in again and "UPGRADE" not in again, again
    with open(os.path.join(t, ".claude/agents/reviewer.md"), "a") as f:
        f.write("# mine\n")
    out = render(t, p).stdout
    assert "KEEP-EDITED  .claude/agents/reviewer.md" in out, out
    assert open(os.path.join(t, ".claude/agents/reviewer.md")).read().endswith("# mine\n")


@test
def render_brownfield_skips_and_merges():
    t = fresh_repo()
    touch(t, "CLAUDE.md", "# my rules\n")
    touch(t, ".claude/settings.json", json.dumps({"model": "opus", "permissions": {"allow": ["Bash(make:*)"]},
                                                   "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}}))
    touch(t, ".mcp.json", json.dumps({"mcpServers": {"github": {"command": "my-own-github"}}}))
    touch(t, ".gitignore", "node_modules/\n")
    out = render(t, plan()).stdout
    assert "SKIP         CLAUDE.md" in out, out
    assert open(os.path.join(t, "CLAUDE.md")).read() == "# my rules\n"
    s = json.load(open(os.path.join(t, ".claude/settings.json")))
    assert s["model"] == "opus" and "Bash(make:*)" in s["permissions"]["allow"], s
    stop_cmds = [h["command"] for g in s["hooks"]["Stop"] for h in g["hooks"]]
    assert "echo mine" in stop_cmds and any("stop_gate.py" in c for c in stop_cmds), stop_cmds
    m = json.load(open(os.path.join(t, ".mcp.json")))
    assert m["mcpServers"]["github"] == {"command": "my-own-github"} and "playwright" in m["mcpServers"], m
    gi = open(os.path.join(t, ".gitignore")).read()
    assert gi.startswith("node_modules/\n") and ".env" in gi, gi
    shown = render(t, plan(), "--show", "CLAUDE.md")
    assert shown.returncode == 0 and "# demo-app" in shown.stdout


@test
def render_refuses_bad_plans_without_writing():
    t = fresh_repo()
    bad_secret = plan(mcp=[{"x": {"command": "npx", "env": {"API_KEY": "sk-abcdefghijklmnopqrstuv"}}}])
    bad_literal = plan(mcp=[{"x": {"command": "npx", "env": {"API_KEY": "plainvalue"}}}])
    with open(plan()) as f:
        p = json.load(f)
    del p["vars"]["TEST_CMD"]
    bad_var = os.path.join(tempfile.mkdtemp(), "p.json")
    json.dump(p, open(bad_var, "w"))
    for b, msg in ((bad_secret, "literal secret"), (bad_literal, "env var"), (bad_var, "TEST_CMD")):
        r = render(t, b)
        assert r.returncode == 2 and msg in r.stderr, (msg, r.stderr)
    assert sorted(os.listdir(t)) == [".git"] or sorted(os.listdir(t)) == [".claude", ".git"], os.listdir(t)
    assert not os.path.exists(os.path.join(t, "CLAUDE.md"))


@test
def doctor_clean_after_render_and_flags_problems():
    t = fresh_repo()
    for i in range(40):  # TypeScript project: .claude/'s Python tooling must not look like a module
        touch(t, f"src/c{i}.ts", "export {}")
    render(t, plan())
    r = script("doctor.py", t)
    assert r.returncode == 0 and "0 FAIL" in r.stdout and "module .claude" not in r.stdout, r.stdout
    u = tempfile.mkdtemp()
    touch(u, "CLAUDE.md", "\n".join(["x"] * 150))
    touch(u, "AGENTS.md", "\n".join(["y"] * 20))
    r = script("doctor.py", u)
    assert r.returncode == 1, r.stdout
    for needle in ("not a git repo", "150 lines", "duplicate instructions", "docs/STATE.md"):
        assert needle in r.stdout, (needle, r.stdout)


@test
def scan_remote_host_and_test_dirs():  # E2E-1, E2E-2
    t = fresh_repo()
    touch(t, "docs/superpowers/specs/design.md", "x")
    touch(t, "tests/test_a.py", "def test_a(): pass")
    for remote, host in (("/some/local/path", None), ("https://github.com/a/b.git", "github.com"),
                         ("git@github.com:a/b.git", "github.com"), ("ssh://git@gitlab.com/a/b", "gitlab.com")):
        sh(["git", "remote", "remove", "origin"], cwd=t)
        sh(["git", "remote", "add", "origin", remote], cwd=t)
        d = json.loads(script("scan_repo.py", t).stdout)
        assert d["git_remote_host"] == host, (remote, d["git_remote_host"])
    assert d["test_dirs"] == ["tests"], d["test_dirs"]


@test
def level_upgrade_registers_every_new_hook():  # E2E-5
    t = fresh_repo()
    render(t, plan("standard"))
    render(t, plan("strict"))
    s = json.load(open(os.path.join(t, ".claude/settings.json")))
    cmds = [h["command"] for ev in s["hooks"].values() for g in ev for h in g["hooks"]]
    for hook in ("guard", "session_context", "stop_gate", "scope_check", "test_on_stop"):
        assert sum(hook + ".py" in c for c in cmds) == 1, (hook, cmds)
    r = script("doctor.py", t)
    assert "hooks registered | all hook files registered" in r.stdout, r.stdout


@test
def seed_files_are_never_diffed_and_skip_needs_no_vars():  # E2E-4, E2E-6
    t = fresh_repo()
    render(t, plan())
    with open(os.path.join(t, "docs/STATE.md"), "w") as f:
        f.write("# my state\n")
    out = render(t, plan()).stdout
    assert "KEEP-SEED    docs/STATE.md" in out and "KEEP-EDITED  docs/STATE.md" not in out, out
    u = fresh_repo()
    touch(u, "docs/ARCHITECTURE.md", "# theirs\n")
    with open(plan()) as f:
        p = json.load(f)
    for k in ("ARCH_OVERVIEW", "ARCH_COMPONENTS", "ARCH_EXTERNAL"):
        del p["vars"][k]
    pp = os.path.join(tempfile.mkdtemp(), "p.json")
    json.dump(p, open(pp, "w"))
    r = render(u, pp)
    assert r.returncode == 0, r.stderr
    assert open(os.path.join(u, "docs/ARCHITECTURE.md")).read() == "# theirs\n"


@test
def plugins_can_be_disabled_per_project():  # E2E-3
    t = fresh_repo()
    render(t, plan(plugins={"enable": ["a@m"], "disable": ["ponytail@ponytail"]}))
    s = json.load(open(os.path.join(t, ".claude/settings.json")))
    assert s["enabledPlugins"] == {"ponytail@ponytail": False, "a@m": True}, s["enabledPlugins"]


@test
def strict_test_hook_never_passes_silently():  # E2E-8
    t = fresh_repo()
    render(t, plan("strict", vars={**json.load(open(plan()))["vars"], "FAST_TEST_CMD": "definitely-not-a-cmd -q"}))
    touch(t, "src/a.py", "x=1")
    r = sh([PY, ".claude/hooks/test_on_stop.py"], cwd=t, inp="{}")
    assert '"block"' in r.stdout and "could not run" in r.stdout, r.stdout + r.stderr
    d = script("doctor.py", t)
    assert "FAIL | test_on_stop command" in d.stdout, d.stdout


@test
def agent_frontmatter_stays_valid_yaml():  # E2E-9
    t = fresh_repo()
    v = json.load(open(plan()))["vars"]
    render(t, plan(vars={**v, "RISK_AREAS": "auth: OAuth tokens #1, payments"}))
    fm = open(os.path.join(t, ".claude/agents/security-reviewer.md")).read().split("\n---", 1)[0]
    line = next(l for l in fm.splitlines() if l.startswith("description:"))
    assert line.startswith('description: "') and json.loads(line[len("description: "):]).count("auth: OAuth") == 1, line
    assert "auth: OAuth tokens #1" in open(os.path.join(t, "CLAUDE.md")).read()
    for f in os.listdir(os.path.join(t, ".claude/agents")):  # every agent: frontmatter lines are key: value
        head = open(os.path.join(t, ".claude/agents", f)).read().split("\n---", 1)[0].splitlines()[1:]
        for l in head:
            k, _, val = l.partition(": ")
            assert k and (": " not in val or val.startswith('"')), (f, l)


@test
def plugin_hint_only_before_setup():
    t = fresh_repo()
    env = dict(os.environ, CLAUDE_PROJECT_DIR=t)
    run = lambda: subprocess.run([PY, os.path.join(SCRIPTS, "hint.py")], capture_output=True, text=True, env=env).stdout
    assert "claude-project-setup:brief" in run()
    touch(t, "PROJECT-BRIEF.md", "# b")
    assert "claude-project-setup:bootstrap" in run()
    render(t, plan())
    assert run() == "", run()


@test
def tracker_evals_pass():
    r = sh([PY, os.path.join(HERE, "..", "tracker", "scripts", "run_evals.py")],
           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert r.returncode == 0 and "23/23" in r.stdout, r.stdout + r.stderr


@test
def setup_refused_until_user_approves_plan():
    t = fresh_repo()
    r = render(t, plan(), approve=False)
    assert r.returncode == 3 and "isn't approved" in r.stderr, r.stderr
    sm(t, "new", "bootstrap")
    for e in ("brief_written", "answers_recorded", "plan_previewed"):
        sm(t, "move", "bootstrap", e)
    assert sm(t, "record", "bootstrap", "user_approved").returncode == 6      # Claude can't self-approve
    assert sm(t, "move", "bootstrap", "approve").returncode == 4              # no approval yet
    for prompt in ("approved but use strict", "what does approved mean here?", "yes", "don't approve yet"):
        assert say(t, prompt, "--plugin") == "", prompt
    r = render(t, plan(), approve=False)
    assert r.returncode == 3 and not os.path.exists(os.path.join(t, "CLAUDE.md")), r.stderr
    assert "Recorded" in say(t, "approved", "--plugin")
    sm(t, "move", "bootstrap", "plan_changed")                                # plan edited after approval
    assert sm(t, "move", "bootstrap", "approve").returncode == 4, "old approval must not cover a changed plan"
    say(t, "Approved.", "--plugin")
    assert sm(t, "move", "bootstrap", "approve").returncode == 0
    assert render(t, plan(), approve=False).returncode == 0
    st = json.loads(sm(t, "status", "bootstrap").stdout)[0]["state"]
    assert st == "GENERATED", st


@test
def task_lifecycle_drives_scope_and_done():
    t = fresh_repo()
    render(t, plan("strict"))
    cli = [PY, ".claude/state-machine/state_cli.py"]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=t, PYTHONDONTWRITEBYTECODE="1")
    run = lambda *a: sh(cli + list(a), cwd=t, env=env)
    hook = lambda name, payload: sh([PY, f".claude/hooks/{name}.py"], cwd=t, inp=json.dumps(payload), env=env).stdout
    scope = lambda f: (json.loads(hook("scope_check", {"tool_name": "Edit", "tool_input": {"file_path": f}}) or "{}")
                       .get("hookSpecificOutput", {}).get("permissionDecision", "allow"))
    touch(t, "specs/tasks/TASK-001-csv.md", "# T\n## Allowed files\n- `src/csv.ts`\n## Rollback\nx\n")
    assert run("new", "TASK-001-csv").returncode == 0
    assert scope("src/other.ts") == "allow", "PLANNED task must not restrict edits yet"
    assert run("move", "TASK-001-csv", "start").returncode == 3
    assert "Recorded" in hook("approval_capture", {"prompt": "approve TASK-001"})
    for e in ("approve", "start"):
        assert run("move", "TASK-001-csv", e).returncode == 0, e
    assert scope("src/csv.ts") == "allow" and scope("src/other.ts") == "deny"
    assert json.loads(run("active").stdout) == ["TASK-001-csv"]
    run("move", "TASK-001-csv", "submit")
    assert run("move", "TASK-001-csv", "pass").returncode == 4, "DONE needs verify_passed"
    run("record", "TASK-001-csv", "verify_passed")
    assert run("move", "TASK-001-csv", "pass").returncode == 0
    assert scope("src/other.ts") == "allow" and json.loads(run("active").stdout) == []
    st = sh([PY, ".claude/hooks/selftest.py"], cwd=t, env=env)
    assert st.returncode == 0 and "approval_capture" in st.stdout, st.stdout + st.stderr


@test
def light_level_has_no_state_machines():
    t = fresh_repo()
    render(t, plan("light"))
    assert not os.path.exists(os.path.join(t, ".claude/state-machine/state_cli.py"))
    s = json.load(open(os.path.join(t, ".claude/settings.json")))
    assert "UserPromptSubmit" not in s["hooks"], s["hooks"].keys()


def frontmatter_of(path):
    head = open(path).read().split("\n---", 1)[0].splitlines()[1:]
    return dict(l.split(": ", 1) for l in head if ": " in l)


@test
def render_applies_model_policy():
    t = fresh_repo()
    render(t, plan("standard"))
    ex = frontmatter_of(os.path.join(t, ".claude/agents/explorer.md"))
    assert ex["model"] == "haiku" and "effort" not in ex and ex["maxTurns"] == "25" and ex["omitClaudeMd"] == "true", ex
    rv = frontmatter_of(os.path.join(t, ".claude/agents/reviewer.md"))
    assert rv["model"] == "inherit" and rv["effort"] == "high", rv
    me = frontmatter_of(os.path.join(t, ".claude/agents/api-expert.md"))
    assert me["model"] == "sonnet" and me["effort"] == "medium", me              # *-expert glob
    cm = open(os.path.join(t, "CLAUDE.md")).read()
    assert "haiku → sonnet → opus" in cm and "agent-models.json" in cm and "`explorer` (haiku)" in cm
    assert json.load(open(os.path.join(t, ".claude/agent-models.json")))["profile"] == "balanced"
    u = fresh_repo()
    render(u, plan("standard", models={"profile": "economy", "overrides": {"implementer": {"model": "opus"}}}))
    assert frontmatter_of(os.path.join(u, ".claude/agents/reviewer.md"))["model"] == "sonnet"
    assert frontmatter_of(os.path.join(u, ".claude/agents/implementer.md"))["model"] == "opus"


@test
def models_apply_keeps_prompts_and_upgrades_cooperate():
    t = fresh_repo()
    p = plan("standard")
    render(t, p)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=t, PYTHONDONTWRITEBYTECODE="1")
    apply = lambda *a: sh([PY, ".claude/scripts/apply_models.py", *a], cwd=t, env=env)
    impl = os.path.join(t, ".claude/agents/implementer.md")
    with open(impl, "a") as f:
        f.write("\nHouse rule: prefer small commits.\n")                       # user's own prompt edit
    pol_path = os.path.join(t, ".claude/agent-models.json")
    pol = json.load(open(pol_path))
    pol["profile"] = "quality"
    pol["overrides"] = {"implementer": {"model": "opus", "effort": "max"}}
    json.dump(pol, open(pol_path, "w"), indent=2)
    r = apply()
    assert r.returncode == 0 and "implementer" in json.loads(r.stdout)["updated"], r.stdout + r.stderr
    fm = frontmatter_of(impl)
    assert fm["model"] == "opus" and fm["effort"] == "max", fm
    assert "House rule: prefer small commits." in open(impl).read()
    assert frontmatter_of(os.path.join(t, ".claude/agents/explorer.md"))["model"] == "sonnet"   # quality profile
    assert json.loads(apply("--check").stdout)["differs_from_policy"] == []
    out = render(t, p).stdout                                                     # plugin upgrade after /models
    agent_lines = [l for l in out.splitlines() if ".claude/agents/" in l]
    assert all(l.startswith("UNCHANGED") or l.startswith("KEEP-EDITED  .claude/agents/implementer.md")
               for l in agent_lines), agent_lines
    assert "KEEP-SEED    .claude/agent-models.json" in out, out
    assert json.load(open(pol_path))["profile"] == "quality", "render must never overwrite the user's policy"


@test
def model_drift_warns_and_bad_policy_fails():
    t = fresh_repo()
    render(t, plan("standard"))
    env = dict(os.environ, CLAUDE_PROJECT_DIR=t, PYTHONDONTWRITEBYTECODE="1")
    ex = os.path.join(t, ".claude/agents/explorer.md")
    edited = open(ex).read().replace("model: haiku", "model: opus")              # hand edit
    open(ex, "w").write(edited)
    d = script("doctor.py", t).stdout
    assert "WARN | agent models" in d and "explorer" in d and "0 FAIL" in d, d
    pol_path = os.path.join(t, ".claude/agent-models.json")
    pol = json.load(open(pol_path))
    pol["overrides"] = {"explorer": {"model": "gpt-4", "effort": "ultra"}}
    json.dump(pol, open(pol_path, "w"))
    before = open(ex).read()
    r = sh([PY, ".claude/scripts/apply_models.py"], cwd=t, env=env)
    assert r.returncode == 2 and "gpt-4" in r.stderr and open(ex).read() == before, r.stderr
    assert "FAIL | agent model policy" in script("doctor.py", t).stdout
    u = fresh_repo()
    r = render(u, plan("standard", models={"profile": "turbo"}))
    assert r.returncode == 2 and "turbo" in r.stderr, r.stderr


@test
def upgrade_from_manifest_without_plan():
    t = fresh_repo()
    render(t, plan())
    r = script("render.py", "--target", t)
    assert r.returncode == 0 and "UNCHANGED" in r.stdout, r.stdout + r.stderr


for status, name, msg in results:
    print(f"{status} {name}" + (f"\n     {msg}" if msg else ""))
fails = sum(r[0] == "FAIL" for r in results)
print(f"\n{len(results) - fails}/{len(results)} passed")
sys.exit(1 if fails else 0)
