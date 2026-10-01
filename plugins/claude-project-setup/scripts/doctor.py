"""Setup health check. Prints a PASS/WARN/FAIL table; writes nothing.

Usage: python3 doctor.py [PROJECT] [--tools]   (--tools also inventories plugins/MCP: slower, uses the claude CLI)
Exit 1 if any FAIL.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render import SECRET, version  # noqa: E402
from scan_repo import scan, SKIP_DIRS  # noqa: E402

ROOT_MAX, MODULE_MAX, STATE_MAX, BIG_DIR_MB = 100, 40, 60, 100


def lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def dir_mb(path, cap_mb=2000):
    total = 0
    for dp, dn, fn in os.walk(path):
        for n in fn:
            try:
                total += os.path.getsize(os.path.join(dp, n))
            except OSError:
                pass
        if total > cap_mb * 1e6:
            break  # ponytail: stop counting past the cap; exact size doesn't matter
    return total / 1e6


def git(project, *args):
    try:
        return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None


def check(project, tools=False):
    rows = []
    add = lambda status, name, detail, fix="": rows.append((status, name, detail, fix))
    s = scan(project)
    p = lambda *a: os.path.join(project, *a)

    add("PASS" if s["is_git"] else "FAIL", "git repository", "yes" if s["is_git"] else "not a git repo", "git init && git add -A && git commit")

    if os.path.exists(p("CLAUDE.md")):
        n = len(lines(p("CLAUDE.md")))
        add("PASS" if n <= ROOT_MAX else "WARN", "root CLAUDE.md size", f"{n} lines (max {ROOT_MAX})", "move area rules to .claude/rules/ or module CLAUDE.md")
    else:
        add("FAIL", "root CLAUDE.md", "missing", "run /claude-project-setup:bootstrap")
    for f in s["instruction_files"]:
        if f.endswith("/CLAUDE.md"):
            n = len(lines(p(f)))
            if n > MODULE_MAX:
                add("WARN", f"module {f}", f"{n} lines (max {MODULE_MAX})", "keep only module-local facts")
    if os.path.exists(p("AGENTS.md")) and os.path.exists(p("CLAUDE.md")) and len(lines(p("AGENTS.md"))) > 5:
        add("WARN", "duplicate instructions", "AGENTS.md has content but Claude Code reads only CLAUDE.md when both exist",
            "merge into CLAUDE.md; make AGENTS.md a one-line pointer")
    covered = {f.rsplit("/", 1)[0] for f in s["instruction_files"] if f.endswith("/CLAUDE.md")}
    for m in s["module_candidates"]:
        if m["path"] not in covered:
            add("WARN", f"module {m['path']}", f"{', '.join(m['reasons'])}; no CLAUDE.md", "add one with /claude-project-setup:bootstrap (brownfield)")

    if os.path.exists(p("docs", "STATE.md")):
        n = len(lines(p("docs", "STATE.md")))
        add("PASS" if n <= STATE_MAX else "WARN", "docs/STATE.md size", f"{n} lines (max {STATE_MAX})", "/checkpoint rewrites it compactly")
        last = git(project, "log", "-1", "--format=%ct")
        if last and last.stdout.strip() and os.path.getmtime(p("docs", "STATE.md")) + 60 < int(last.stdout.strip()):
            add("WARN", "docs/STATE.md freshness", "older than the last commit", "run /checkpoint")
    else:
        add("FAIL", "docs/STATE.md", "missing (no cross-session memory)", "create from template / run bootstrap")

    # commands in CLAUDE.md that reference package.json scripts
    if os.path.exists(p("CLAUDE.md")) and os.path.exists(p("package.json")):
        try:
            scripts = set((json.load(open(p("package.json"), encoding="utf-8")).get("scripts") or {}))
        except ValueError:
            scripts = set()
        text = "\n".join(lines(p("CLAUDE.md")))
        used = set(re.findall(r"(?:npm run|pnpm(?: run)?|yarn(?: run)?|bun run)\s+([\w:-]+)", text))
        bad = sorted(u for u in used - scripts if u not in {"install", "add", "i", "dlx", "exec", "test"})
        add("PASS" if not bad else "WARN", "CLAUDE.md commands", "all scripts exist" if not bad else f"unknown scripts: {', '.join(bad)}",
            "fix CLAUDE.md or package.json")

    # hooks
    hooks_dir = p(".claude", "hooks")
    if os.path.exists(p(hooks_dir, "selftest.py")):
        r = subprocess.run([sys.executable, os.path.join(hooks_dir, "selftest.py")], cwd=project,
                           capture_output=True, text=True, timeout=120)
        add("PASS" if r.returncode == 0 else "FAIL", "hook self-test", (r.stdout or r.stderr).strip().splitlines()[-1][:120] if (r.stdout or r.stderr).strip() else "no output",
            "fix the failing hook or re-run render")
    else:
        add("WARN", "hooks", "no .claude/hooks/selftest.py", "run bootstrap to install guardrail hooks")
    try:
        settings = json.load(open(p(".claude", "settings.json"), encoding="utf-8"))
    except (OSError, ValueError):
        settings = None
    if settings is None:
        add("FAIL", ".claude/settings.json", "missing or invalid JSON", "run bootstrap")
    elif os.path.isdir(hooks_dir):
        registered = json.dumps(settings.get("hooks", {}))
        unreg = [h for h in sorted(os.listdir(hooks_dir)) if h.endswith(".py") and h != "selftest.py" and h not in registered]
        add("PASS" if not unreg else "WARN", "hooks registered", "all hook files registered" if not unreg else f"not registered: {', '.join(unreg)}",
            "re-run render.py")

    # MCP secrets
    if os.path.exists(p(".mcp.json")):
        raw = "\n".join(lines(p(".mcp.json")))
        add("FAIL" if SECRET.search(raw) else "PASS", ".mcp.json secrets", "literal secret found" if SECRET.search(raw) else "env references only",
            "replace with ${VAR}, rotate the leaked key")

    # big non-source dirs inside the repo
    for d in sorted(os.listdir(project)):
        full = p(d)
        if os.path.isdir(full) and d not in {".git"} and d not in SKIP_DIRS - {"vendor"}:
            mb = dir_mb(full)
            if mb > BIG_DIR_MB:
                ignored = git(project, "check-ignore", "-q", d)
                add("WARN", f"large folder {d}/", f"{mb:.0f} MB{' (gitignored)' if ignored and ignored.returncode == 0 else ''}",
                    "keep run outputs/clones outside the repo; add a Read deny rule")

    # manifest / upgrades
    try:
        man = json.load(open(p(".claude", "setup-manifest.json"), encoding="utf-8"))
        cur = version()
        add("PASS" if man.get("version") == cur else "WARN", "setup version", f"generated by {man.get('version')}, plugin is {cur}",
            "/claude-project-setup:doctor upgrade")
    except (OSError, ValueError):
        add("WARN", "setup manifest", "none (not set up by this plugin, or manifest deleted)", "run bootstrap")

    if tools:
        from scan_tools import live_inventory
        inv = live_inventory()
        tok = sum(x.get("always_on_tokens") or 0 for x in inv["installed"] if x.get("enabled", True))
        add("PASS" if tok < 3000 else "WARN", "plugin always-on cost", f"~{tok} tokens/session from {len(inv['installed'])} plugin(s)",
            "disable plugins this project doesn't need")
        bad = [m["name"] for m in inv["mcp"] if "connected" not in m["status"].lower()]
        if bad:
            add("WARN", "MCP servers", f"not connected: {', '.join(bad)}", "run /mcp, or remove unused servers")
    return rows


def main(argv):
    project = os.path.realpath(next((a for a in argv if not a.startswith("--")), "."))
    rows = check(project, "--tools" in argv)
    print("| Status | Check | Detail | Fix |\n|---|---|---|---|")
    for st, name, detail, fix in rows:
        print(f"| {st} | {name} | {detail} | {fix if st != 'PASS' else ''} |")
    fails = sum(r[0] == "FAIL" for r in rows)
    print(f"\n{fails} FAIL, {sum(r[0] == 'WARN' for r in rows)} WARN, {sum(r[0] == 'PASS' for r in rows)} PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
