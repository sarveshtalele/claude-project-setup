---
name: integrations
description: Review, add or remove plugins and MCP servers for this project. Reuses what is installed, suggests what fills a real need, flags overlaps and token cost. Use when the user asks which plugins/MCP to use, wants to add an MCP server or plugin to a project, or asks why sessions are expensive.
argument-hint: "[list | add <capability or name> | remove <name> | audit]"
---

# Integrations

1. Inventory and classify (it records names, scopes, status and token cost only, never secrets):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan_repo.py" . > "${TMPDIR:-/tmp}/cps-scan.json"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan_tools.py" . --scan "${TMPDIR:-/tmp}/cps-scan.json" --needs <capabilities>
   ```
   The capabilities are `ui-testing`, `library-docs`, `github`, `error-monitoring`, `web-research`, `code-review` and `response-style`.
2. Show a table: kind · id · capability · class (REUSE / ADD / SKIP / CONFLICT) · always-on tokens · reason. For CONFLICT, ask which one to keep.
3. Make changes **only through the saved plan**, so the project stays reproducible:
   - Read `.claude/setup-manifest.json` → `plan`, and update its `mcp` / `plugins.enable` lists.
   - Write the plan to `${TMPDIR:-/tmp}/cps-plan.json`, then preview it with `render.py --target . --plan <it> --dry-run`, and apply it after approval.
   - Removing an item: render only adds. Edit `.mcp.json` / `.claude/settings.json` `enabledPlugins` by hand after approval (the guard hook protects settings.json, so ask the user to make that edit, or to run `/permissions`).
4. Installing a new plugin needs its own approval: `claude plugin install <id>`. Never enter API keys or complete OAuth. Tell the user which env var to set (it's listed in `.env.example`) or to run `/mcp`.
5. If the project wasn't set up by this plugin (no manifest), run `/claude-project-setup:bootstrap` instead.
