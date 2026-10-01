# Development

## Layout
```
claude-project-setup/                ← marketplace (this repo)
├── .claude-plugin/marketplace.json
├── README.md · CHANGELOG.md
├── docs/                            ← documentation (not installed)
└── plugins/claude-project-setup/    ← the plugin (installed)
    ├── .claude-plugin/plugin.json
    ├── hooks/hooks.json             ← SessionStart hint
    ├── skills/                      ← brief · bootstrap (+references) · doctor · integrations
    ├── scripts/                     ← scan_repo · scan_tools · render · doctor · hint
    ├── catalog/integrations.json
    ├── templates/                   ← everything render.py can write
    └── tests/                       ← test_scripts.py + fixtures/
```

## Test and validate
```bash
python3 plugins/claude-project-setup/tests/test_scripts.py
```
```bash
claude plugin validate . && claude plugin validate plugins/claude-project-setup
```
```bash
claude --plugin-dir ./plugins/claude-project-setup
```

**Suite coverage (24 tests, stdlib only; the tracker's own 23 evals run inside it)**
- **Scans:** greenfield, brownfield, modules, remotes, test folders.
- **Tool classification:** REUSE, ADD, SKIP and CONFLICT.
- **Rendering at all 3 levels:** each generated project's own self-test passes, dry runs write nothing, re-runs are idempotent, and your edits are kept.
- **Brownfield merges:** settings, `.mcp.json` and `.gitignore` keep your entries.
- **Refusals:** literal secrets and missing variables.
- **Level upgrades:** every hook gets registered.
- **Seed files:** never diffed.
- **YAML frontmatter:** generated agent files stay valid.
- **Strict test hook:** never passes silently.
- **Hint hook:** appears only before setup, and resumes an interrupted one.
- **State machines:** render refuses an unapproved setup; approvals come only from your message; a changed plan needs a new approval; the task lifecycle drives scope and DONE; light level has no state machines.
- **Model policy:** profiles and overrides render into agents; `/models apply` keeps prompt edits, and a later upgrade stays UNCHANGED; drift is a WARN; an invalid policy is refused.
- **`doctor`**, and upgrading from the manifest.

## Adding things
| Add | Where | Also update |
|---|---|---|
| Agent template | `templates/agents/<name>.md` | `docs/agents.md`, `references/plan.md` |
| Hook | `templates/hooks/<name>.py` | `LEVELS` / `HOOK_EVENTS` in `render.py`, `selftest.py`, `docs/guardrails.md` |
| MCP server | `catalog/integrations.json` | `docs/integrations.md` |
| Template variable | the template | `references/plan.md` variable table |

## Release
1. Bump `version` in `plugins/claude-project-setup/.claude-plugin/plugin.json`.
2. Add an entry to `CHANGELOG.md`.
3. Make sure the tests and both `claude plugin validate` runs pass.
4. Tag it `v<version>` and push.

## Conventions
- Python 3.9+ standard library only. No third-party dependencies.
- Commits use Conventional Commits, with **no AI attribution trailers**.
- Every bug fix ships with a regression test.
