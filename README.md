# Claude Project Setup

A Claude Code plugin that sets up **any project, new (greenfield) or existing (brownfield)**, from one Markdown brief you edit by hand.
It interviews you about what's missing, shows the complete setup plan, and only after you approve does it generate:

- root and **per-module `CLAUDE.md`** files (large repos load only the module you're working in)
- **project-specific subagents** (explorer, implementer, verifier, reviewer, plus specialists chosen from your brief)
- **guardrail hooks** that enforce rules instead of requesting them (protected paths, ask before any new file, dangerous shell, scope)
- **permissions**, **plugin and MCP server configuration** (reusing what you already have)
- **memory that survives `/clear`, compaction and new sessions** (`docs/STATE.md`, injected automatically)

Version `0.2.1` · Python 3.9+ standard library · macOS, Linux and Windows · 16/16 tests passing · [end-to-end tested on tokentelemetry](docs/E2E-TOKENTELEMETRY.md).

```
/claude-project-setup:brief         create PROJECT-BRIEF.md; you fill it in
/claude-project-setup:bootstrap     scan → interview → setup plan → you approve → generate → verify
/claude-project-setup:doctor        health check (add `upgrade` to update generated files, `--tools` for plugin/MCP cost)
/claude-project-setup:integrations  list / add / remove / audit plugins and MCP servers for this project

# installed into your project by bootstrap (work without the plugin, for the whole team):
/task <title>                       one requirement becomes a one-page task spec with runnable acceptance checks
/checkpoint                         save state to docs/STATE.md before /clear
```

---

## Install

```bash
claude plugin marketplace add sarveshtalele/claude-project-setup
```
```bash
claude plugin install claude-project-setup@claude-project-setup
```
Or try it from a clone without installing:
```bash
git clone https://github.com/sarveshtalele/claude-project-setup.git
```
```bash
claude --plugin-dir ./claude-project-setup/plugins/claude-project-setup
```

**Prerequisites:** Claude Code with plugin support · Python 3.9+ (`python3` on macOS/Linux, `python` on Windows) · git.
**Teammates don't need the plugin.** Everything generated is written into the project's `.claude/` and committed.

> **Workspace trust:** Claude Code ignores a project's `permissions.allow` rules until you accept the trust dialog for that folder. Open it interactively with `claude` once and accept.

---

## Quick start

**New project**
```text
mkdir my-app && cd my-app && claude
> /claude-project-setup:brief          ← then edit PROJECT-BRIEF.md in your editor
> /claude-project-setup:bootstrap
```
**Existing repo**
```text
cd my-repo && claude
> /claude-project-setup:brief          ← optional: goals, protected areas, integrations
> /claude-project-setup:bootstrap
```
Then **start a new session** so the new hooks, agents and CLAUDE.md files load, and begin with `/task <first requirement>`.

---

## How bootstrap works

```
PROJECT-BRIEF.md ─► 1 SCAN ─► 2 TOOLS ─► 3 INTERVIEW ─► 4 PLAN + DRY RUN ─► 5 APPROVE ─► 6 GENERATE ─► 7 VERIFY
                    script     script     ≤2 rounds ×      exact file list    you          render.py    selftest +
                    (0 tokens) (0 tokens) ≤4 questions     agents/hooks/MCP                (no AI)      doctor
```

| Step | What happens | Deterministic? |
|---|---|---|
| 1. Scan | `scan_repo.py` finds manifests, languages, frameworks, scripts, tests, existing `CLAUDE.md`/`AGENTS.md`/`.cursorrules`/`.claude`, module candidates, git. It decides greenfield or brownfield. | yes |
| 2. Tools | `scan_tools.py` runs `claude plugin list --json --available`, `claude plugin details` (token cost) and `claude mcp list`, and reads `.mcp.json`. It sorts each item into REUSE, ADD, SKIP or CONFLICT. Names only, never secrets. | yes |
| 3. Interview | Claude asks only about gaps or conflicts between the brief and the scan: stack, guardrail level, protected areas, modules, agents, integrations, outputs folder. Each question has a recommended default. Answers go into `## Decisions` in the brief. | AI, bounded |
| 4. Plan | Claude writes a plan JSON, and `render.py --dry-run` prints the **exact** files it would create, merge or skip. You see agents, hooks, permissions and plugins/MCP with token cost. | yes (preview) |
| 5. Approve | Nothing has been written or installed until you say so. | you |
| 6. Generate | `render.py` fills templates (it won't run if a variable is missing or a literal secret is present), never overwrites files it didn't create, and union-merges settings, `.mcp.json` and `.gitignore`. Greenfield runs the stack's official scaffold first. | yes |
| 7. Verify | `.claude/hooks/selftest.py` and `doctor.py` must pass; then it offers to commit. | yes |

---

## User stories

### US-1 Start a new project from requirements (greenfield)
*As a developer starting from an empty folder, I want to describe the product in Markdown and get a correct, guarded skeleton, so that I don't hand-write boilerplate or re-explain the project each session.*
- Claude proposes the architecture, an ADR for the stack and a folder tree, then scaffolds with the stack's **official generator** (`npm create vite`, `create-next-app`, `uv init`, …) after you approve.
- `CLAUDE.md` contains only commands that ran successfully. Each numbered requirement becomes a `specs/tasks/TASK-NNN` stub.

**Accept:** nothing is written before approval · every listed command was run · one task stub per requirement.

### US-2 Adopt an existing repo safely (brownfield)
*As a developer joining an existing or legacy repo, I want Claude to understand and guard it without rewriting anything.*
- **No source changes.** Only `CLAUDE.md` files, `docs/`, `specs/`, `.claude/`, `.mcp.json`, `.env.example`, `.gitignore` and the brief are written.
- An existing `CLAUDE.md` is never overwritten: Claude merges the generated version into it by hand and shows you the diff. Existing `settings.json` and `.mcp.json` are union-merged, so your own entries win.
- `ARCHITECTURE.md` describes what *exists*, with path evidence. Problems go to `STATE.md` "Known gaps".

**Accept:** `git diff` touches only the paths above · your existing settings, MCP servers and `.gitignore` lines are preserved (tested).

### US-3 Keep a large repo cheap to work in
- A folder gets a **module `CLAUDE.md`** (≤ 40 lines) if it has its own manifest, more than 150 source files, or a different language from the root. Claude Code loads it only when working there.
- Cross-cutting rules use `.claude/rules/*.md` with `paths:` globs (`testing`, `api`, `ui`), so they load only when matching files are touched.
- Optional `<module>-expert` agents for the biggest modules.

### US-4 Turn a requirement into an approved, verifiable task
```text
> /task add CSV export to the reports page
```
Splits multi-goal requests, asks at most 3 questions, and writes a spec with **Allowed files**, **Non-goals** and **Acceptance as runnable commands**. After you approve, the work runs `implementer` → `verifier` (real output, never "should pass") → `reviewer`.

### US-5 Never lose context between sessions
- **SessionStart hook** (start, resume, `/clear`, compaction) injects `docs/STATE.md` and the git branch and changed files.
- **Stop hook** (standard and strict): if code changed after STATE.md was last updated, Claude is sent back once to update it.
- `/checkpoint` rewrites STATE.md (≤ 60 lines). Protocol: one task per session; checkpoint → `/clear`; after a second compaction, start a new session.

### US-6 Enforce guardrails, not just request them
| You edit | Effect |
|---|---|
| `.claude/protected.txt` | Globs Claude can never write (Write/Edit **and** shell redirection). Secrets, lockfiles, `.git/` and the guardrail files themselves are always protected. |
| `.claude/write-allow.txt` | Where Claude may create **new** files without asking. Any other new file prompts you. |
| `PROJECT-BRIEF.md` → Guardrail level | **light** = guard and context · **standard** = + STATE.md stop gate · **strict** = + tests on Stop + task-scope enforcement |

Always blocked: force-push, `reset --hard`, `git clean -f`, `sudo`, `curl | sh`, `--no-verify`, `npm publish`, reading `.env`, changing `.claude/settings.json`/hooks from the shell. Dependency installs, `git push`, plugin installs and `claude mcp add` always ask.

### US-7 Keep token cost low by default
- Mapping uses scripts, not AI exploration. Search and verification run on **Haiku** agents and implementation on **Sonnet**; planning and review inherit your model.
- Deny rules keep `node_modules/`, build output, lockfiles and coverage out of context. Run outputs go to a folder **outside** the repo.
- Every plugin's always-on token cost is shown before it's enabled. `doctor --tools` reports the total.

### US-8 Check and upgrade a project's setup
`/claude-project-setup:doctor` prints a PASS/WARN/FAIL table covering: git, CLAUDE.md and module sizes, folders that qualify as modules but have no CLAUDE.md, duplicate `AGENTS.md`, STATE.md size and freshness, scripts named in CLAUDE.md that no longer exist, hook self-test, unregistered hooks, secrets in `.mcp.json`, large folders inside the repo, and the setup version.
`doctor upgrade` re-renders from the plan saved in `.claude/setup-manifest.json`. It replaces only generated files you haven't edited (checked by hash); for the others it shows the template diff.

### US-9 Get subagents and hooks tailored to this project
**Agents** (`.claude/agents/`) are filled in with your real commands, paths and risk areas:

| Agent | When | Model |
|---|---|---|
| `explorer` · `implementer` · `verifier` · `reviewer` | always | haiku · sonnet · haiku · inherit |
| `security-reviewer` | brief lists auth, payments, PII, uploads… | inherit |
| `test-writer` | tests missing or thin | sonnet |
| `migration-reviewer` | DB or framework migrations in scope | inherit |
| `ui-verifier` | frontend detected (Playwright screenshots, console errors) | sonnet |
| `<module>-expert` | large modules you choose | sonnet |

**Hooks** (`.claude/hooks/`, registered in `.claude/settings.json`):

| Hook | Event | Level |
|---|---|---|
| `guard.py` | PreToolUse (Write/Edit/Bash) | all |
| `session_context.py` | SessionStart | all |
| `stop_gate.py` | Stop | standard, strict |
| `scope_check.py` | PreToolUse (Write/Edit) | strict |
| `test_on_stop.py` | Stop | strict |
| `format_on_edit.py` | PostToolUse | optional (your formatter, edited file only) |
| `selftest.py` | run by you or by doctor | all |

### US-10 Reuse my plugins and MCP servers, or add new ones
| Class | Meaning | After approval |
|---|---|---|
| **REUSE** | Installed and fits a need | Enabled for this project (`enabledPlugins`) |
| **ADD** | Not installed, fills a need | Each install needs its own yes; MCP servers are written to `.mcp.json` |
| **SKIP** | Installed but not needed here | Left off, with the reason shown |
| **CONFLICT** | Two tools doing one exclusive job (for example two output-style plugins) | You pick one |

- Built-in MCP catalog: `playwright` (UI checks), `context7` (library docs), `github` (PRs and issues; writes ask), `sentry` (errors; sign in via `/mcp`), `firecrawl` (web research; asks). Plugin suggestions come only from your **real** installed or marketplace listings.
- Secrets are always `${ENV_VAR}` references. `render.py` refuses literal keys, and `.env.example` lists the variable names. Claude never enters credentials or completes OAuth for you.

---

## PROJECT-BRIEF.md

```markdown
## Goal · ## Users & key flows · ## Requirements (numbered, one goal each)
## Stack preferences · ## Constraints · ## Risk areas · ## Protected areas
## Guardrail level · ## Tools & integrations · ## Outputs location
## Non-goals · ## Done means · ## Decisions (filled in by the interview)
```
An empty section, or one that says "recommend", becomes an interview question; Claude never assumes silently. The full template, with guidance for each section, is in `plugins/claude-project-setup/templates/PROJECT-BRIEF.md`.

## What gets created in your project

```
your-project/
├── PROJECT-BRIEF.md              ← yours (+ Decisions)
├── CLAUDE.md                     ← root rules, ≤100 lines
├── <module>/CLAUDE.md            ← large/distinct modules only, ≤40 lines
├── .mcp.json · .env.example      ← only if MCP servers were chosen; secrets as ${VAR}
├── docs/  STATE.md · ARCHITECTURE.md · adr/
├── specs/ TASK-TEMPLATE.md · tasks/
└── .claude/
    ├── settings.json             ← permissions (incl. mcp__*), hooks, enabledPlugins
    ├── protected.txt · write-allow.txt
    ├── agents/ · hooks/ · rules/
    ├── skills/ task/ · checkpoint/
    └── setup-manifest.json       ← the plan + file hashes (enables safe upgrades)
```

## Repository layout

```
claude-project-setup/                    ← this repo = plugin marketplace
├── .claude-plugin/marketplace.json
├── README.md
├── docs/ playbook.md · SESSION-AUDIT.md
└── plugins/claude-project-setup/
    ├── .claude-plugin/plugin.json
    ├── skills/      brief · bootstrap (+ references/ interview, greenfield, brownfield, modules, plan) · doctor · integrations
    ├── scripts/     scan_repo.py · scan_tools.py · render.py · doctor.py
    ├── catalog/     integrations.json   (capabilities, MCP servers, known plugins)
    ├── templates/   PROJECT-BRIEF · CLAUDE · CLAUDE.module · docs · specs · settings/base.json
    │                agents/ (9) · hooks/ (7) · rules/ (4) · skills/ (task, checkpoint) · protected.txt · write-allow.txt
    └── tests/       test_scripts.py + fixtures/
```

## Development

```bash
python3 plugins/claude-project-setup/tests/test_scripts.py
```
```bash
claude plugin validate . && claude plugin validate plugins/claude-project-setup
```
The tests cover:
- scans in greenfield and brownfield, including module detection;
- REUSE/ADD/SKIP/CONFLICT sorting;
- rendering at all 3 levels, with each project's own hook self-test passing;
- dry runs writing nothing, and re-runs changing nothing;
- protection of files you edited, and brownfield merges keeping your settings and MCP servers;
- refusal of literal secrets and missing variables;
- doctor, and upgrading from the manifest.

**Not covered by automated tests:** the interactive interview runs inside a live Claude Code session. Try it end to end with `--plugin-dir` on a scratch copy of a repo before relying on it.

## Limits
- A plugin can't ship permissions, so bootstrap writes `.claude/settings.json` into the project (after approval).
- Removing a plugin or MCP server is a manual edit. `render.py` only adds and merges; it never deletes your config.
- Application code is limited to what official scaffold generators produce. CI isn't generated.

Background: [docs/SESSION-AUDIT.md](docs/SESSION-AUDIT.md) lists the 20 findings from a real 6-day, $383 session that this plugin is designed to prevent, and [docs/playbook.md](docs/playbook.md) has the full working method behind it.
