"""Plugin SessionStart hook: route Claude to this plugin, and resume an interrupted setup.

Silent once the project is set up (.claude/setup-manifest.json exists), so set-up projects pay nothing.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def bootstrap_status():
    path = os.path.join(HERE, "..", "templates", "state-machine", "state_cli.py")
    try:
        spec = importlib.util.spec_from_file_location("state_cli", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.status(project, "bootstrap")
    except Exception:
        return None


if not os.path.exists(os.path.join(project, ".claude", "setup-manifest.json")):
    st = bootstrap_status()
    if st:
        print(f"Claude Project Setup was interrupted at state {st['state']} ({st['description'].rstrip('.')}). "
              "Resume with the claude-project-setup:bootstrap skill; it continues from this state.")
    elif os.path.exists(os.path.join(project, "PROJECT-BRIEF.md")):
        print("Claude Project Setup is installed and PROJECT-BRIEF.md exists: when the user wants to start, "
              "run the claude-project-setup:bootstrap skill.")
    else:
        print("Claude Project Setup is installed and this project is not set up yet. When the user describes "
              "a project to build, or asks to set up / adopt this repo for Claude, run the "
              "claude-project-setup:brief skill first (it drafts PROJECT-BRIEF.md from their description).")
