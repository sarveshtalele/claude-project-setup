# Setup plan JSON (input to render.py)

```json
{
  "mode": "greenfield | brownfield",
  "level": "light | standard | strict",
  "format_on_edit": false,
  "python": "python3",
  "vars": { "PROJECT_NAME": "...", "...": "..." },
  "agents": ["security-reviewer", {"template": "module-expert", "vars": {"AGENT_NAME": "web-expert", "MODULE": "apps/web"}}],
  "modules": [{"path": "apps/web", "vars": {"MODULE_PURPOSE": "...", "MODULE_ENTRY_POINTS": "- `apps/web/src/main.tsx`: bootstrap", "MODULE_TEST_CMD": "...", "MODULE_BUILD_CMD": "...", "MODULE_RULES": "- ..."}}],
  "rules": ["testing", {"template": "api", "vars": {"API_PATHS": ["src/api/**"]}}, {"template": "ui", "vars": {"UI_PATHS": ["src/**/*.tsx"]}}],
  "protected": ["backend/*"],
  "write_allow": ["src/*", "tests/*"],
  "permissions": {"allow": ["Bash(npm test:*)"], "ask": [], "deny": ["Read(./run-outputs/**)"]},
  "plugins": {"enable": ["ponytail@ponytail"], "disable": [], "marketplaces": {}},
  "mcp": ["playwright", "github", {"custom-name": {"command": "npx", "args": ["-y", "pkg"], "env": {"KEY": "${KEY}"}}}],
  "models": {"profile": "balanced", "overrides": {"implementer": {"model": "opus"}}},
  "gitignore": []
}
```
- The 4 core agents (`explorer`, `implementer`, `verifier`, `reviewer`) are always included. `agents` lists the extras: `security-reviewer`, `test-writer`, `migration-reviewer`, `ui-verifier`, `module-expert`.
- Hooks by level: **light** = guard, session_context · **standard** = + stop_gate · **strict** = + scope_check, test_on_stop. `format_on_edit` is separate. `selftest` is always included.
- `mcp` strings are catalog names (`playwright`, `context7`, `github`, `sentry`, `firecrawl`). Custom objects always get an `ask` permission. Any env or header value must be a `${VAR}` reference, or render refuses the plan.
- `models` seeds `.claude/agent-models.json`: `profile` is `economy`, `balanced` (the default) or `quality`, and `overrides` are per agent (globs allowed). If the file already exists, it wins; it belongs to the user. Every generated agent's `model`, `effort`, `maxTurns` and `omitClaudeMd` come from it.
- `plugins.disable` turns off, for this project only, plugins that are enabled at user scope (SKIP or CONFLICT rows the user chose to turn off).
- `docs/STATE.md` and `docs/ARCHITECTURE.md` are **seed files**: they are created only if missing, and never diffed or upgraded afterwards. Their variables are needed only when the file doesn't exist yet.
- `permissions.allow` should include the real test and lint commands, so the user isn't prompted for them.

## Variables (all required by the templates you include; `n/a` is allowed, but never invent values)
| Var | Used by | Source |
|---|---|---|
| `PROJECT_NAME`, `PROJECT_SUMMARY` | CLAUDE.md, ARCHITECTURE.md | brief Goal |
| `RUNTIME`, `PACKAGE_MANAGER` | CLAUDE.md, implementer | scan |
| `INSTALL_CMD`, `BUILD_CMD`, `LINT_CMD`, `TEST_CMD`, `FAST_TEST_CMD` | CLAUDE.md, verifier, implementer, test-writer, test_on_stop | scan scripts, each run once. **`FAST_TEST_CMD` runs inside a hook, from a plain non-interactive shell with no activated venv**, so use `.venv/bin/python -m pytest` (Windows: `.venv\\Scripts\\python`) or `uv run pytest`, never a bare `python`. |
| `LAYOUT` | CLAUDE.md | Markdown bullets, one per important folder |
| `OUTPUTS_DIR` | CLAUDE.md, ui-verifier | brief or interview (outside the repo) |
| `ARCH_OVERVIEW`, `ARCH_COMPONENTS`, `ARCH_EXTERNAL` | ARCHITECTURE.md | `ARCH_COMPONENTS` = table rows `\| name \| path \| responsibility \| talks to \|` |
| `RISK_AREAS` | security-reviewer | brief |
| `TEST_FRAMEWORK`, `TEST_DIRS` | test-writer | scan |
| `MIGRATION_PATHS`, `ROLLBACK_CMD` | migration-reviewer | scan or brief |
| `DEV_CMD`, `DEV_URL` | ui-verifier | scan scripts |
| `FORMAT_CMD` (with `{file}`), `FORMAT_GLOBS` (list) | format_on_edit | repo formatter config, e.g. `npx prettier --write {file}`, `["*.ts","*.tsx"]` |
| `API_PATHS`, `UI_PATHS` (lists) | rules `api` / `ui` (in the rule's own `vars`) | scan |

Computed by render (don't set them): `AGENTS_LIST`, `GUARDRAIL_LEVEL`, `MCP_SETUP`, `MODULE_MAP`, `PROTECTED_LINES`, `WRITE_ALLOW_LINES`.
