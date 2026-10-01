"""Plugin SessionStart hook: one-line hint so Claude routes project descriptions to this plugin.

Silent once the project is set up (.claude/setup-manifest.json exists), so set-up projects pay nothing.
"""
import os

project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
if not os.path.exists(os.path.join(project, ".claude", "setup-manifest.json")):
    brief = os.path.exists(os.path.join(project, "PROJECT-BRIEF.md"))
    print("Claude Project Setup is installed and this project is not set up yet. "
          + ("PROJECT-BRIEF.md exists: when the user wants to start, run the claude-project-setup:bootstrap skill."
             if brief else
             "When the user describes a project to build, or asks to set up / adopt this repo for Claude, "
             "run the claude-project-setup:brief skill first (it drafts PROJECT-BRIEF.md from their description)."))
