# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Allowed commands still prompt | Workspace not trusted, so Claude Code ignores `permissions.allow` | Open the folder interactively once with `claude` and accept the trust dialog |
| New hooks, agents or CLAUDE.md not active | They load when a session starts | Start a new session after bootstrap or an upgrade |
| `test_on_stop` blocks with "could not run" | `FAST_TEST_CMD` relies on an activated venv (`python` not on PATH) | Use `.venv/bin/python -m pytest` (Windows: `.venv\Scripts\python`) or `uv run pytest`; `doctor` flags this |
| `render.py` exits 2: missing variables | The plan lacks a variable a template needs | Add it to `vars` (use `n/a` if it doesn't apply) |
| `render.py` exits 2: literal secret | A key is in the `.mcp.json` config | Use `${VAR}` and set the variable in your environment |
| `SKIP CLAUDE.md` | You already have one | Expected. Claude merges the generated version by hand and shows you the diff |
| `KEEP-EDITED` on upgrade | You changed a generated file | Expected. The diff shows what the template changed; merge by hand if you want it |
| Plugin hint appears in a repo you don't want set up | The project isn't set up | Ignore it (about 50 tokens), or disable the plugin for that project in `enabledPlugins` |
| Hooks fail on Windows | `python3` isn't on PATH | Generated hooks use `python` on Windows; set `"python": "python"` in the plan if detection was wrong |
| `render.py` exits 3: "setup plan isn't approved" | First-time setup needs your approval | Reply `approved` to the setup plan, then Claude runs `state_cli.py move bootstrap approve` |
| "Approval not recorded" | Your message had a condition ("but…") or several items are waiting | Reply exactly `approved`, or `approve TASK-007` |
| Setup stopped halfway | Usage limit, `/clear` or a closed session | Start a new session; the start hook names the state, then run `/claude-project-setup:bootstrap` |
| Commits show Claude as co-author | Older setup, or user-level settings | Generated settings set `attribution.commit` and `attribution.pr` to `""`; check `~/.claude/settings.json` |

Still stuck? Run `/claude-project-setup:doctor` and open an issue with its output.
