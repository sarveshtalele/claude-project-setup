"""Apply .claude/agent-models.json to the frontmatter of .claude/agents/*.md. Deterministic; stdlib only.

Usage (project root; `python` on Windows):
  python3 .claude/scripts/apply_models.py            # apply the policy (rewrites only the managed keys)
  python3 .claude/scripts/apply_models.py --check    # report agents that differ from the policy; writes nothing
  python3 .claude/scripts/apply_models.py --list     # table of the effective settings per agent

Managed keys: model, effort, maxTurns, omitClaudeMd (+ tools / disallowedTools when the policy sets them).
Everything else in an agent file is left untouched, so hand edits to prompts survive.
Exit: 0 ok · 2 invalid policy (nothing written).
"""
import json
import os
import re
import sys
from fnmatch import fnmatch

MODELS = {"haiku", "sonnet", "opus", "fable", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
KEYS = ["model", "effort", "maxTurns", "omitClaudeMd", "tools", "disallowedTools"]


class PolicyError(Exception):
    pass


def validate(policy):
    profiles = policy.get("profiles") or {}
    if policy.get("profile") not in profiles:
        raise PolicyError(f"profile '{policy.get('profile')}' not in profiles {sorted(profiles)}")
    for where, table in [*((f"profiles.{p}", t) for p, t in profiles.items()), ("overrides", policy.get("overrides") or {})]:
        for agent, s in table.items():
            for k, v in s.items():
                if k not in KEYS:
                    raise PolicyError(f"{where}.{agent}: unknown key '{k}' (allowed: {', '.join(KEYS)})")
            m = s.get("model")
            if m is not None and m not in MODELS and not re.fullmatch(r"claude-[a-z0-9.-]+", str(m)):
                raise PolicyError(f"{where}.{agent}.model '{m}' (use {', '.join(sorted(MODELS))} or a claude-* model id)")
            if s.get("effort") not in (None, *EFFORTS):
                raise PolicyError(f"{where}.{agent}.effort '{s['effort']}' (use {', '.join(sorted(EFFORTS))} or null)")
            if "maxTurns" in s and not (isinstance(s["maxTurns"], int) and 1 <= s["maxTurns"] <= 500):
                raise PolicyError(f"{where}.{agent}.maxTurns must be an integer 1-500")
            if "omitClaudeMd" in s and not isinstance(s["omitClaudeMd"], bool):
                raise PolicyError(f"{where}.{agent}.omitClaudeMd must be true or false")
    ladder = (policy.get("escalation") or {}).get("ladder", [])
    if any(m not in MODELS - {"inherit"} for m in ladder):
        raise PolicyError("escalation.ladder may only contain haiku, sonnet, opus, fable")


def _lookup(table, agent):
    if agent in table:
        return table[agent]
    return next((v for k, v in table.items() if fnmatch(agent, k)), None)


def settings_for(policy, agent):
    """Effective settings for an agent: profile entry, then overrides (both may use globs). None = unmanaged."""
    base = _lookup(policy["profiles"][policy["profile"]], agent)
    over = _lookup(policy.get("overrides") or {}, agent)
    if base is None and over is None:
        return None
    return {**(base or {}), **(over or {})}


def _fm_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def apply_to_text(text, settings):
    """Set managed frontmatter keys; a None value removes the key. Returns the new text."""
    if not text.startswith("---\n") or settings is None:
        return text
    end = text.find("\n---", 4)
    managed = [k for k in KEYS if k in settings]
    # canonical form: unmanaged lines keep their order, managed keys follow in KEYS order, so the
    # same policy always yields the same bytes whatever the file's history (keeps upgrades UNCHANGED)
    keep = [l for l in text[4:end].split("\n")
            if not (re.match(r"^([A-Za-z][\w-]*):", l) and re.match(r"^([A-Za-z][\w-]*):", l).group(1) in managed)]
    keep += [f"{k}: {_fm_value(settings[k])}" for k in managed if settings[k] is not None]
    return "---\n" + "\n".join(keep) + text[end:]


def sync_claude_md(project, policy, rows):
    """Keep the Agents list and profile name in CLAUDE.md in step with the policy."""
    path = os.path.join(project, "CLAUDE.md")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(r"\(profile `[\w-]+`\)", f"(profile `{policy['profile']}`)", text)
    for name, s in rows:
        if s and s.get("model"):
            new = re.sub(rf"^(- `{re.escape(name)}` )\([^)]*\)", rf"\g<1>({s['model']})", new, flags=re.M)
    if new != text:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)


def agent_name(text, fallback):
    m = re.search(r"^name:\s*\"?([^\"\n]+)\"?$", text.split("\n---", 1)[0], re.M)
    return m.group(1).strip() if m else fallback


def main(argv):
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        with open(os.path.join(project, ".claude", "agent-models.json"), encoding="utf-8") as f:
            policy = json.load(f)
        validate(policy)
    except (OSError, ValueError, PolicyError) as e:
        print(f"POLICY ERROR: {e}", file=sys.stderr)
        return 2
    adir = os.path.join(project, ".claude", "agents")
    rows, drift, changed = [], [], []
    for fn in sorted(f for f in os.listdir(adir) if f.endswith(".md")) if os.path.isdir(adir) else []:
        path = os.path.join(adir, fn)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        name = agent_name(text, fn[:-3])
        s = settings_for(policy, name)
        rows.append((name, s))
        new = apply_to_text(text, s)
        if new != text:
            drift.append(name)
            if "--check" not in argv and "--list" not in argv:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                changed.append(name)
    if "--list" in argv:
        print(f"profile: {policy['profile']}\n\n| Agent | model | effort | maxTurns | omitClaudeMd |\n|---|---|---|---|---|")
        for name, s in rows:
            s = s or {}
            print(f"| {name} | {s.get('model', '(file)')} | {s.get('effort') or '(session)'} | "
                  f"{s.get('maxTurns', '(file)')} | {s.get('omitClaudeMd', '(file)')} |")
        return 0
    if "--check" in argv:
        print(json.dumps({"profile": policy["profile"], "differs_from_policy": drift,
                          "unmanaged": [n for n, s in rows if s is None]}))
        return 0
    sync_claude_md(project, policy, rows)
    print(json.dumps({"profile": policy["profile"], "updated": changed,
                      "unchanged": [n for n, _ in rows if n not in changed]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
