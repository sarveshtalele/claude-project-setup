# {{PROJECT_NAME}}

{{PROJECT_SUMMARY}}

## Stack and commands
- Runtime: {{RUNTIME}}. Package manager: {{PACKAGE_MANAGER}}. Do not add another.
- Install: `{{INSTALL_CMD}}` · Build: `{{BUILD_CMD}}` · Lint/typecheck: `{{LINT_CMD}}`
- Test (full): `{{TEST_CMD}}` · Test (fast, while iterating): `{{FAST_TEST_CMD}}`

## Layout
{{LAYOUT}}
- `docs/STATE.md`: the current state of the project. **Source of truth across sessions.**
- `docs/ARCHITECTURE.md` and `docs/adr/`: how the project is built and why.
- `specs/tasks/`: one file per approved task (template: `specs/TASK-TEMPLATE.md`).
- Run outputs, clones and screenshots go in `{{OUTPUTS_DIR}}` (outside the repo), never in the repo.
- Subfolders with their own `CLAUDE.md` have local rules; they load when you work there.

## Working rules
1. **Plan before code.** For any change touching more than 1 file, run `/task`, show the spec, and wait for an explicit "approved".
2. **Scope is the task file.** Edit only its `Allowed files`. If more is needed, stop and say so.
3. **Verify, don't claim.** "Done" means the acceptance commands ran in this session and passed. Quote their output.
4. **Bugs become tests first.** Reproduce the bug in a test, watch it fail, then fix it.
5. **Ask before creating any new file** outside `.claude/write-allow.txt`, and suggest a name. The hook enforces this.
6. When an architecture decision changes, update this file, `docs/STATE.md` and an ADR **in the same change**.

## Context rules
- One task per session. When a task is done, run `/checkpoint`, then `/clear`.
- `docs/STATE.md` is injected automatically at start and after compaction. Trust it over chat memory.
- Use the `explorer` agent for searches wider than about 3 files.
- Use Grep, Glob and Read with ranges, not `cat`. Bound shell output with `| tail -n 40`.
- Never read `node_modules/`, build output, lockfiles or run outputs into context.

## Agents (`.claude/agents/`)
{{AGENTS_LIST}}

## Guardrails (level: {{GUARDRAIL_LEVEL}}; enforced by `.claude/settings.json` and `.claude/hooks/`)
- Paths in `.claude/protected.txt`, secrets, lockfiles, `.git/` and `.claude/` config are never written.
- No force-push, `reset --hard`, `sudo` or `curl | sh`. Dependency installs and `git push` always ask.
- If a hook blocks you, report the block and ask. Never work around it.
- Commits and PRs carry no AI co-author or attribution lines (`attribution` is off in settings) unless the user asks.
{{MCP_SETUP}}
## Definition of done
Acceptance commands pass · only allowed files changed · `docs/STATE.md` updated · no stray files · reviewer has no P0 findings.
