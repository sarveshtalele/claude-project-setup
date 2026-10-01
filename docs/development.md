# Development

## Layout
```
claude-project-setup/                ← marketplace (this repo)
├── .claude-plugin/marketplace.json
├── README.md · CHANGELOG.md
├── docs/                            ← documentation and diagrams (not installed)
├── tools/package.py                 ← release packaging (not installed)
└── plugins/claude-project-setup/    ← the plugin (installed)
    ├── .claude-plugin/plugin.json
    ├── hooks/hooks.json             ← SessionStart hint, UserPromptSubmit approval capture
    ├── skills/                      ← brief · bootstrap (+references) · doctor · integrations
    │                                   create-skill · create-agent · create-plugin
    ├── scripts/                     ← scan_repo · scan_tools · render · scaffold · adopt_scaffold · doctor · hint
    ├── tracker/                     ← state machine engine + its 23 evals
    ├── catalog/integrations.json
    ├── templates/                   ← everything render.py and scaffold.py can write
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

**Suite coverage (33 tests, stdlib only; the tracker's own 23 evals run inside it)**
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
- **Project types and generators:** type detection (6 kinds); a generated skill passes its own 16 evals; a plugin bundle has one tracker copy and passes `claude plugin validate`; bad specs and overwrites are refused; a skill's gate is approved only from the user's message.
- **End-to-end findings (v0.4.2):** no Stop-gate block right after setup; `STATE.md` seeded from the plan; strict needs a real fast test; skill approval message; `/models` keeps `CLAUDE.md` in sync; scan finds pip, test frameworks and CI commands; scaffold adoption into a non-empty project.
- **`doctor`**, and upgrading from the manifest.

## Adding things
| Add | Where | Also update |
|---|---|---|
| Agent template | `templates/agents/<name>.md` | `docs/agents.md`, `references/plan.md` |
| Hook | `templates/hooks/<name>.py` | `LEVELS` / `HOOK_EVENTS` in `render.py`, `selftest.py`, `docs/guardrails.md` |
| MCP server | `catalog/integrations.json` | `docs/integrations.md` |
| Template variable | the template | `references/plan.md` variable table |

## Release
1. Bump `version` in `plugins/claude-project-setup/.claude-plugin/plugin.json` and the README version badge.
2. Add a `## [<version>]` section to `CHANGELOG.md`, then commit.
3. Build the package. The tool refuses a dirty tree, a version mismatch, failing tests or failed validation.

   ```bash
   python3 tools/package.py
   ```

4. Tag and push, then publish the package as a GitHub release.

   ```bash
   git tag -a v<version> -m "v<version>" && git push origin main v<version>
   ```

   ```bash
   gh release create v<version> dist/claude-project-setup-<version>.zip dist/claude-project-setup-<version>.zip.sha256 --title "v<version>" --notes-file <notes>
   ```

## Conventions
- Python 3.9+ standard library only. No third-party dependencies.
- Commits use Conventional Commits, with **no AI attribution trailers**.
- Every bug fix ships with a regression test.
