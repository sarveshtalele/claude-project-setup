---
name: doctor
description: Audit this project's Claude Code setup (CLAUDE.md sizes, missing modules, STATE.md freshness, hooks, secrets in .mcp.json, large folders, plugin/MCP cost) and optionally upgrade generated agents/hooks to the plugin's latest templates. Use when the user says doctor, health check, audit setup, or upgrade setup.
argument-hint: "[upgrade] [--tools]"
---

# Doctor

## Report (default)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" . $ARGUMENTS
```
Pass `--tools` when the user asks about plugins, MCP or token cost (it's slower). Show the table as printed, then list **at most 5** fixes, FAIL rows first. Don't apply fixes without asking.

## Upgrade (`$ARGUMENTS` contains `upgrade`)
1. Preview it. The script re-renders from the plan saved in `.claude/setup-manifest.json`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" --target . --dry-run
   ```
   - `UPGRADE`: a generated file you never edited; it is safe to replace.
   - `KEEP-EDITED`: you edited it; the template diff is shown, and it won't be replaced.
   - `MERGE`: settings, `.mcp.json` or `.gitignore` gain only missing entries.
2. Ask for approval, then run it without `--dry-run`, then run `python3 .claude/hooks/selftest.py`.
3. For each KEEP-EDITED file, offer to merge the template change by hand with Edit, and show the diff.
