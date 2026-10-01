"""UserPromptSubmit hook: record `user_approved` from the user's own message.

A short message such as "approved", "approve TASK-007", "go ahead" or "lgtm" (no "but", "not",
"change"…) approves the one machine waiting for approval. Claude itself can't record
`user_approved` (state_cli refuses it, and guard.py blocks it from the shell), so approvals
come from the user's own words. Never blocks the prompt.

--plugin: run from the plugin before setup (bootstrap machine only); silent once the project is set up.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_state_cli(project, plugin_mode):
    candidates = [os.path.join(HERE, "..", "state-machine", "state_cli.py")]  # plugin templates/ or project .claude/
    if not plugin_mode:
        candidates.insert(0, os.path.join(project, ".claude", "state-machine", "state_cli.py"))
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        return None
    spec = importlib.util.spec_from_file_location("state_cli", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod if mod.TRACKER else None


def main():
    plugin_mode = "--plugin" in sys.argv
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    if plugin_mode and os.path.exists(os.path.join(project, ".claude", "setup-manifest.json")):
        return  # the project's own copy of this hook takes over after setup
    if not os.path.isdir(os.path.join(project, ".claude", "state-machine", ".state-machine")):
        return
    cli = load_state_cli(project, plugin_mode)
    if cli is None:
        return
    msg = cli.capture_approval(project, data.get("prompt", ""),
                               only=(lambda m: m == "bootstrap") if plugin_mode else None)
    if msg:
        print(msg)


if __name__ == "__main__":
    main()
