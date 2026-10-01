# Command reference

## Plugin skills (need the plugin)
| Command | Does | Auto-triggers on |
|---|---|---|
| `/claude-project-setup:brief [description]` | Drafts `PROJECT-BRIEF.md` from your description, then hands off to bootstrap | "I want to build…", "set up this repo for Claude" |
| `/claude-project-setup:bootstrap [brief path]` | Scan → interview → plan → generate → verify | "bootstrap", "set up this project" |
| `/claude-project-setup:doctor [upgrade] [--tools]` | Health table; `upgrade` refreshes generated files | "health check", "audit setup" |
| `/claude-project-setup:integrations [list\|add\|remove\|audit]` | Plugins and MCP servers for this project | "which MCP should I use" |

## Project skills (installed into `.claude/skills/`; work without the plugin)
| Command | Does |
|---|---|
| `/task <title>` | One-page task spec with allowed files and runnable acceptance checks; waits for approval |
| `/checkpoint` | Rewrites `docs/STATE.md` (≤ 60 lines); tells you whether `/clear` is safe |

## Scripts (run from the project root)
```bash
python3 .claude/hooks/selftest.py
```
```bash
python3 <plugin>/scripts/doctor.py . --tools
```
```bash
python3 <plugin>/scripts/render.py --target . --dry-run
```
`<plugin>` is the installed plugin folder (shown by `claude plugin list --json` as `installPath`), or `plugins/claude-project-setup` in a clone. Use `python` instead of `python3` on Windows.
